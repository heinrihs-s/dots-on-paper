"""Native Pillow rendering for monochrome and 16-tone e-paper displays.

The renderer consumes the same state as the event API. It does not invent an
answer or fetch a remote image; every frame can be rendered entirely offline.
"""

from __future__ import annotations

from functools import lru_cache
from dataclasses import dataclass
from io import BytesIO
import math
import os
from pathlib import Path
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFont, ImageOps


PAPER = 255
INK = 24
SECONDARY = 85
CHARACTERS = {
    "artist": ("beret-dot.png", .102, .121),
    "curious": ("curious-dot.png", .14, -.15),
    "bookish": ("bookish-dot.png", .12, .10),
    "cool": ("cool-dot.png", .12, .08),
}
STATUSES = {"idle", "thinking", "answer", "error"}


@lru_cache(maxsize=1)
def _asset_directory() -> Path:
    override = os.environ.get("DOTS_ASSET_DIR")
    candidates = ([Path(override)] if override else []) + [
        Path(__file__).resolve().parent / "assets",
        Path(__file__).resolve().parents[2] / "assets",
    ]
    for candidate in candidates:
        if (candidate / "Figtree.ttf").is_file():
            return candidate
    raise RuntimeError("Dots assets are missing. Install the package with its assets.")


@lru_cache(maxsize=4)
def _source_image(character: str) -> tuple[Image.Image, Image.Image]:
    with Image.open(_asset_directory() / CHARACTERS[character][0]) as source:
        rgba = source.convert("RGBA")
    return ImageOps.grayscale(rgba), rgba.getchannel("A")


@lru_cache(maxsize=48)
def _font(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(_asset_directory() / "Figtree.ttf"), size)
    try:
        axes = font.get_variation_axes()
        font.set_variation_by_axes([
            weight if axis["name"] == b"Weight" else axis["default"]
            for axis in axes
        ])
    except (AttributeError, OSError):
        # A static replacement font remains usable without variable-font APIs.
        pass
    return font


def _clean(value: object, fallback: str = "") -> str:
    if not isinstance(value, str):
        return fallback
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    return "".join(
        character for character in value
        if character == "\n" or not unicodedata.category(character).startswith("C")
    ).strip()


def _advance(font: ImageFont.FreeTypeFont, value: str) -> float:
    return font.getlength(value)


def _ellipsize(value: str, font: ImageFont.FreeTypeFont, width: int) -> str:
    suffix = "…"
    if _advance(font, suffix) > width:
        return ""
    value = value.rstrip()
    while value and _advance(font, value + suffix) > width:
        value = value[:-1].rstrip()
    return value + suffix


def _wrap(value: str, font: ImageFont.FreeTypeFont, width: int, limit: int) -> tuple[list[str], bool]:
    """Wrap by font metrics and stop promptly once the panel is full.

    Overlong words are split at character boundaries. Input length is not used
    to pick a tiny font, and no state field is changed when text is clipped.
    """
    lines: list[str] = []
    line = ""
    paragraphs = value.split("\n")
    for paragraph_index, paragraph in enumerate(paragraphs):
        words = re.findall(r"\S+", paragraph)
        for word in words:
            proposed = (line + " " + word).strip()
            if _advance(font, proposed) <= width:
                line = proposed
                continue
            if line:
                lines.append(line)
                line = ""
                if len(lines) >= limit:
                    return lines, True
            for character in word:
                if line and _advance(font, line + character) > width:
                    lines.append(line)
                    line = ""
                    if len(lines) >= limit:
                        return lines, True
                line += character
        if line or not words:
            lines.append(line)
            line = ""
        if len(lines) >= limit:
            more = paragraph_index < len(paragraphs) - 1
            return lines, more
    return lines, False


def _text_block(
    canvas: Image.Image, value: str, box: tuple[int, int, int, int],
    preferred: int, minimum: int, weight: int = 600, centered: bool = False,
    color: int = INK,
) -> bool:
    """Draw readable text, returning whether a visible ellipsis was required."""
    x, y, width, height = box
    if width <= 0 or height <= 0 or not value:
        return False
    preferred = max(minimum, preferred)
    candidates = list(range(preferred, minimum - 1, -max(1, (preferred - minimum) // 5)))
    if candidates[-1] != minimum:
        candidates.append(minimum)
    for size in candidates:
        font = _font(size, weight)
        leading = max(size + 2, round(size * 1.24))
        line_limit = max(1, height // leading)
        lines, clipped = _wrap(value, font, width, line_limit)
        if not clipped or size == minimum:
            break
    if clipped:
        lines[-1] = _ellipsize(lines[-1], font, width)
    draw = ImageDraw.Draw(canvas)
    total_height = len(lines) * leading
    if centered:
        y += max(0, (height - total_height) // 2)
    for line in lines:
        left = x + (width - _advance(font, line)) / 2 if centered else x
        draw.text((round(left), y), line, font=font, fill=color, anchor="lt")
        y += leading
    return clipped


@dataclass(frozen=True)
class ReplyBlock:
    """An ordinary reply paragraph or list item, independent of its subject."""

    text: str
    marker: str = ""


@dataclass(frozen=True)
class ReplyLine:
    text: str
    x: int
    y: int
    marker: str = ""


@dataclass(frozen=True)
class ReplyLayout:
    lines: tuple[ReplyLine, ...]
    font_size: int
    leading: int
    clipped: bool


@dataclass(frozen=True)
class ConversationMessage:
    """A display turn supplied by its caller, with no inferred action."""

    role: str
    content: str
    meta: str = ""


def _conversation_messages(state: dict) -> tuple[ConversationMessage, ...]:
    values = state.get("messages")
    if not isinstance(values, list):
        return ()
    messages = []
    for value in values:
        if not isinstance(value, dict) or value.get("role") not in ("assistant", "user"):
            continue
        content = _clean(value.get("content"))
        if content:
            messages.append(ConversationMessage(value["role"], content, _clean(value.get("meta"))))
    return tuple(messages)


def _conversation_mode(state: dict) -> bool:
    # Existing offline callers supplied structured turns before the bridge
    # exposed a preference. Keep those images compatible when mode is absent.
    return state.get("mode", "full_conversation" if state.get("messages") else "last_reply") == "full_conversation"


def _parse_reply(value: str) -> tuple[ReplyBlock, ...]:
    """Keep Markdown paragraphs and lists without requiring a special schema.

    A dot's own words remain the content. Soft line breaks join the preceding
    paragraph or item; empty lines create paragraph spacing. The renderer does
    not infer reminders, dates, punchlines, or any other domain-specific field.
    """
    blocks: list[ReplyBlock] = []
    paragraph: list[str] = []
    continuing_item = False

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(ReplyBlock(" ".join(paragraph)))
            paragraph.clear()

    for line in value.splitlines():
        line = line.strip()
        if not line:
            flush_paragraph()
            continuing_item = False
            continue
        match = re.match(r"^(?:([-*•])|(\d+[.)]))\s+(.+)$", line)
        # Bold Markdown is useful to the source assistant, but literal stars
        # are distracting on a compact display. Keep the words themselves.
        plain = line.replace("**", "")
        if match:
            flush_paragraph()
            marker = "•" if match.group(1) else match.group(2)
            blocks.append(ReplyBlock(match.group(3).replace("**", ""), marker))
            continuing_item = True
        elif continuing_item:
            previous = blocks[-1]
            blocks[-1] = ReplyBlock(previous.text + " " + plain, previous.marker)
        else:
            paragraph.append(plain)
    flush_paragraph()
    return tuple(blocks)


def _reply_at_size(blocks: tuple[ReplyBlock, ...], size: int, width: int, height: int) -> ReplyLayout:
    font = _font(size, 500)
    leading = max(size + 2, round(size * 1.34))
    lines: list[ReplyLine] = []
    y = 0
    clipped = False
    previous: ReplyBlock | None = None
    for block in blocks:
        if previous is not None:
            if previous.marker and block.marker:
                y += round(size * .22)
            elif previous.marker:
                y += round(size * .62)
            else:
                y += round(size * .50)
        limit = (height - y) // leading
        if limit < 1:
            clipped = True
            break
        marker = block.marker
        if marker and marker != "•" and _advance(font, marker) > width * .28:
            marker = _ellipsize(marker, font, round(width * .28))
        marker_width = _advance(font, marker) if marker and marker != "•" else size * .35
        indent = max(round(size * .74), round(marker_width + size * .34)) if block.marker else 0
        indent = min(indent, round(width * .44))
        wrapped, clipped = _wrap(block.text, font, width - indent, limit)
        for index, text in enumerate(wrapped):
            lines.append(ReplyLine(text, indent, y, marker if index == 0 else ""))
            y += leading
        previous = block
        if clipped:
            break
    if clipped and lines:
        last = lines[-1]
        lines[-1] = ReplyLine(_ellipsize(last.text, font, width - last.x), last.x, last.y, last.marker)
    return ReplyLayout(tuple(lines), size, leading, clipped)


def _reply_layout(value: str, width: int, height: int, preferred: int, minimum: int) -> ReplyLayout:
    blocks = _parse_reply(value)
    preferred = max(minimum, preferred)
    candidates = list(range(preferred, minimum - 1, -max(1, (preferred - minimum) // 5)))
    if candidates[-1] != minimum:
        candidates.append(minimum)
    for size in candidates:
        layout = _reply_at_size(blocks, size, width, height)
        if not layout.clipped or size == minimum:
            return layout
    raise AssertionError("Reply size candidates must include the minimum")


def _reply_text(canvas: Image.Image, value: str, box: tuple[int, int, int, int], preferred: int, minimum: int) -> ReplyLayout:
    x, y, width, height = box
    layout = _reply_layout(value, width, height, preferred, minimum)
    font = _font(layout.font_size, 500)
    draw = ImageDraw.Draw(canvas)
    for line in layout.lines:
        if line.marker == "•":
            radius = max(1, layout.font_size * .058)
            _circle(draw, x + layout.font_size * .14, y + line.y + layout.font_size * .38, radius, INK)
        elif line.marker:
            draw.text((x, y + line.y), line.marker, font=font, fill=INK, anchor="lt")
        draw.text((x + line.x, y + line.y), line.text, font=font, fill=INK, anchor="lt")
    return layout


def _circle(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, fill: int) -> None:
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def _mascot(canvas: Image.Image, character: str, box: tuple[int, int, int, int], status: str, frame: int, monochrome: bool = False) -> None:
    x, y, width, height = box
    size = max(16, min(width, height))
    x += (width - size) // 2
    y += (height - size) // 2
    # Render expressions at twice the native size on small panels, then reduce.
    scale = 2 if size <= 800 else 1
    side = size * scale
    layer = Image.new("L", (side, side), PAPER)
    grayscale, alpha = _source_image(character)
    layer.paste(
        grayscale.resize((side, side), Image.Resampling.LANCZOS), (0, 0),
        alpha.resize((side, side), Image.Resampling.LANCZOS),
    )
    draw = ImageDraw.Draw(layer)
    unit = side / 760
    _, eye_x, eye_y = CHARACTERS[character]
    cx, cy = side / 2, side / 2
    eye_y = cy + eye_y * side
    gaze_x = math.sin(frame * 1.1) * 12 * unit if status == "thinking" else 0
    gaze_y = -11 * unit if status == "thinking" else (6 * unit if status == "idle" else 0)
    openness = .14 if status == "idle" else (.14 if status == "thinking" and frame % 8 == 6 else 1)
    stroke = max(scale, round(6 * unit))
    if character == "cool":
        draw.line((cx - eye_x * side + 52 * unit, eye_y, cx + eye_x * side - 52 * unit, eye_y), fill=INK, width=stroke)
        for direction in (-1, 1):
            ex = cx + direction * eye_x * side
            draw.ellipse((ex - 58 * unit, eye_y - 53 * unit, ex + 58 * unit, eye_y + 53 * unit), fill=INK)
            draw.line((ex - 23 * unit, eye_y - 20 * unit, ex - 6 * unit, eye_y - 29 * unit), fill=102, width=max(scale, round(3 * unit)))
    else:
        for direction in (-1, 1):
            ex = cx + direction * eye_x * side + gaze_x
            ew = (28 if character == "curious" else 13) * unit
            eye_openness = openness
            if status == "answer":
                if character == "curious" and frame == 5:
                    eye_openness = .14
                elif character in {"artist", "bookish"} and direction == 1 and frame in (4, 5):
                    eye_openness = .14
            eh = max(3 * unit, (38 if character == "curious" else 28) * eye_openness * unit)
            draw.ellipse((ex - ew, eye_y + gaze_y - eh, ex + ew, eye_y + gaze_y + eh), fill=INK)
        if character == "bookish":
            for direction in (-1, 1):
                ex = cx + direction * eye_x * side
                radius = 55 * unit
                draw.ellipse((ex - radius, eye_y - radius, ex + radius, eye_y + radius), outline=INK, width=stroke)
            draw.arc((cx - 37 * unit, eye_y - 18 * unit, cx + 37 * unit, eye_y + 10 * unit), 195, 345, fill=INK, width=stroke)
    mouth_y = cy + side * .17 if character == "curious" else eye_y + 53 * unit
    if status == "answer":
        radius = 18 * unit
        mouth_x = cx + (7 * unit if character == "cool" else 0)
        draw.arc((mouth_x - radius, mouth_y - radius, mouth_x + radius, mouth_y + radius), 23, 157, fill=INK, width=max(scale, round(5 * unit)))
    elif status == "error":
        draw.line((cx - 13 * unit, mouth_y, cx + 13 * unit, mouth_y), fill=INK, width=max(scale, round(4 * unit)))
    if status == "thinking":
        for index in range(3):
            radius = (5 + (2 if frame % 3 == index else 0)) * unit
            _circle(draw, side * .83 + index * 24 * unit, side * .27 - index * 9 * unit, radius, INK)
    if scale != 1:
        layer = layer.resize((size, size), Image.Resampling.LANCZOS)
    if monochrome:
        # Dither the plush texture locally. Keeping the surrounding paper and
        # typography out of error diffusion makes small labels much clearer.
        layer = layer.convert("1", dither=Image.Dither.FLOYDSTEINBERG).convert("L")
    bob = 0
    if status == "thinking":
        bob = round(math.sin(frame * math.pi / 2) * max(1, size * .008))
    elif status == "answer" and 0 < frame < 11:
        # A single quiet acknowledgment, with identical settled endpoints.
        # The response typography never moves or waits for the performance.
        amplitude = max(1, size * (.006 if character == "bookish" else .009))
        bob = -round(math.sin(frame * math.pi / 11) * amplitude)
    canvas.paste(layer, (x, y + bob))


def _mark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    radius = max(1, size / 9)
    for px, py in ((0, .5), (.5, 0), (.5, 1), (1, .5)):
        _circle(draw, x + size * px, y + size * py, radius, INK)


def _status_label(status: str) -> str:
    return {"idle": "Waiting", "thinking": "Thinking", "answer": "Answer", "error": "Needs attention"}[status]


def _display_text(state: dict, status: str) -> str:
    actual = _clean(state.get("text"))
    messages = _conversation_messages(state) if status == "answer" else ()
    if messages and _conversation_mode(state):
        name = _clean(state.get("dot_name"), "Dot") or "Dot"
        return "\n\n".join(
            f"{'You' if message.role == 'user' else name}: {message.content}"
            for message in messages[-6:]
        )
    if actual:
        return actual
    if messages:
        return next((message.content for message in reversed(messages) if message.role == "assistant"), "Your dot replied without text.")
    return {
        "idle": "Waiting for your dot.",
        "thinking": "Your dot is thinking.",
        "answer": "Your dot replied without text.",
        "error": "Your dot needs attention.",
    }[status]


def _compact(canvas: Image.Image, state: dict, character: str, status: str, frame: int, monochrome: bool = False) -> None:
    width, height = canvas.size
    margin = max(5, round(min(width, height) * .055))
    name = _clean(state.get("dot_name"), character.title()) or character.title()
    title = _clean(state.get("title"))
    mascot_size = min(height - 2 * margin, round(width * .34))
    _mascot(canvas, character, (margin, margin, mascot_size, height - 2 * margin), status, frame, monochrome)
    left = mascot_size + 2 * margin
    measure = width - left - margin
    label_size = max(10, min(22, round(height * .10)))
    label_height = round(label_size * 1.3)
    _text_block(canvas, name, (left, margin, measure, label_height), label_size, label_size, 700)
    content_y = margin + label_height + max(3, round(height * .04))
    if title and height >= 180:
        title_size = max(12, min(24, round(height * .10)))
        title_height = round(title_size * 1.25)
        _text_block(canvas, title, (left, content_y, measure, title_height), title_size, title_size, 600)
        content_y += title_height + margin
    preferred = max(12, min(40, round(height * .16)))
    minimum = max(12, min(24, round(height * .12)))
    messages = _conversation_messages(state) if status == "answer" and _conversation_mode(state) else ()
    if messages:
        # A shelf tag cannot fit a thread. Keep the latest answer readable and
        # show its preceding user turn in a separate, visibly clipped strip.
        latest = next((message for message in reversed(messages) if message.role == "assistant"), messages[-1])
        preceding = messages[-1] if messages[-1].role == "user" else (messages[-2] if len(messages) > 1 and messages[-2].role == "user" else None)
        if preceding and height - margin - content_y >= minimum * 3:
            size = max(10, min(14, round(height * .075)))
            padding = max(3, size // 3)
            bubble_height = size + padding * 2
            draw = ImageDraw.Draw(canvas)
            draw.rounded_rectangle((left, content_y, left + measure, content_y + bubble_height), radius=3, fill=INK)
            text = "You: " + preceding.content.replace("\n", " ")
            font = _font(size, 650)
            if _advance(font, text) > measure - padding * 2:
                text = _ellipsize(text, font, measure - padding * 2)
            draw.text((left + padding, content_y + padding), text, font=font, fill=PAPER, anchor="lt")
            content_y += bubble_height + padding
        _text_block(canvas, latest.content, (left, content_y, measure, height - margin - content_y), preferred, minimum)
    else:
        _text_block(canvas, _display_text(state, status), (left, content_y, measure, height - margin - content_y), preferred, minimum)


def _tiny(canvas: Image.Image, state: dict, character: str, status: str, frame: int, monochrome: bool = False) -> None:
    width, height = canvas.size
    margin = 4
    size = min(width - margin * 2, max(20, height // 2))
    _mascot(canvas, character, ((width - size) // 2, 0, size, size), status, frame, monochrome)
    # On the smallest tags the latest assistant reply takes precedence over
    # history; source state still retains the selected conversation mode.
    _text_block(canvas, _display_text({**state, "mode": "last_reply"}, status), (margin, size, width - margin * 2, height - size - margin), 12, 10, centered=True)


def _reply(canvas: Image.Image, state: dict, character: str, frame: int, monochrome: bool = False) -> None:
    """A sender and an ordinary reading column, for every real answer."""
    width, height = canvas.size
    short_side = min(width, height)
    margin = max(12, round(short_side * .066))
    avatar_size = max(24, round(min(width * .115, height * .15)))
    avatar_top = round(height * .155)
    column_left = margin + avatar_size + max(6, round(short_side * .030))
    column_width = width - column_left - margin
    name_y = round(height * .20)
    name_size = max(13, min(44, round(short_side * .0314)))
    name_height = round(name_size * 1.3)
    name = _clean(state.get("dot_name"), character.title()) or character.title()
    _mascot(canvas, character, (margin, avatar_top, avatar_size, avatar_size), "answer", frame, monochrome)
    _text_block(canvas, name, (column_left, name_y, column_width, name_height), name_size, name_size, 700)
    title = _clean(state.get("title"))
    if title:
        title_size = max(11, min(24, round(short_side * .0171)))
        title_y = name_y + name_height + max(4, round(short_side * .009))
        _text_block(canvas, title, (column_left, title_y, column_width, round(title_size * 1.3)), title_size, title_size, 500, color=SECONDARY)
    body_y = name_y + max(name_height + 12, round(short_side * .098))
    body_height = height - margin - body_y
    preferred = max(16, min(64, round(short_side * .0456)))
    minimum = max(14, min(42, round(short_side * .030)))
    _reply_text(canvas, _display_text(state, "answer"), (column_left, body_y, column_width, body_height), preferred, minimum)


def _conversation(canvas: Image.Image, state: dict, character: str, frame: int, monochrome: bool = False) -> None:
    """Retain actual turns, with a dark right-aligned user reply on paper.

    This is an optional renderer input, not a messaging transport. Small panels
    use the ordinary compact text representation; roomy panels keep speaker
    identity and turn boundaries visible. Excess content is visibly clipped.
    """
    width, height = canvas.size
    short_side = min(width, height)
    margin = max(12, round(short_side * .066))
    avatar_size = max(24, round(min(width * .115, height * .15)))
    column_left = margin + avatar_size + max(6, round(short_side * .030))
    column_width = width - column_left - margin
    name_y = round(height * .20)
    name_size = max(13, min(44, round(short_side * .0314)))
    name_height = round(name_size * 1.3)
    name = _clean(state.get("dot_name"), character.title()) or character.title()
    _mascot(canvas, character, (margin, round(height * .155), avatar_size, avatar_size), "answer", frame, monochrome)
    _text_block(canvas, name, (column_left, name_y, column_width, name_height), name_size, name_size, 700)
    label_size = max(11, min(24, round(short_side * .022)))
    title_y = name_y + name_height + max(4, round(short_side * .009))
    _text_block(canvas, _clean(state.get("title")) or "Conversation", (column_left, title_y, column_width, round(label_size * 1.3)), label_size, label_size, 500, color=SECONDARY)
    body_y = name_y + max(name_height + 12, round(short_side * .098))
    body_height = height - margin - body_y
    messages = _conversation_messages(state)
    omitted = len(messages) > 6
    messages = messages[-6:]
    if omitted:
        _text_block(canvas, "Earlier messages omitted", (column_left, body_y, column_width, label_size * 2), label_size, label_size, 500, color=SECONDARY)
        body_y += label_size * 2
        body_height -= label_size * 2

    preferred = max(16, min(58, round(short_side * .043)))
    minimum = max(14, min(38, round(short_side * .029)))
    for size in range(preferred, minimum - 1, -1):
        font = _font(size, 500)
        leading = round(size * 1.30)
        small = max(10, round(size * .54))
        small_height = round(small * 1.4)
        padding = max(8, round(size * .54))
        gap = max(8, round(size * .74))
        rows = []
        for index, message in enumerate(messages):
            user = message.role == "user"
            measure = round(column_width * .64) - 2 * padding if user else column_width
            lines, clipped = _wrap(message.content.replace("**", ""), _font(size, 650 if user else 500), measure, 64)
            overhead = (small_height + 2 * padding if user else (small_height if index else 0))
            overhead += small_height + round(size * .25) if message.meta else 0
            rows.append([message, lines, clipped, measure, overhead])
        total = sum(len(row[1]) * leading + row[4] for row in rows) + gap * max(0, len(rows) - 1)
        if total <= body_height or size == minimum:
            break
    # Give every visible turn a line before spending spare room on longer
    # paragraphs. Clip the longest paragraphs first, preserving later replies.
    while total > body_height and any(len(row[1]) > 1 for row in rows):
        row = max(rows, key=lambda item: len(item[1]))
        row[1].pop()
        row[2] = True
        total -= leading
    draw = ImageDraw.Draw(canvas)
    y = body_y
    for index, (message, lines, clipped, measure, overhead) in enumerate(rows):
        if clipped:
            lines[-1] = _ellipsize(lines[-1], _font(size, 650 if message.role == "user" else 500), measure)
        user = message.role == "user"
        row_height = len(lines) * leading + overhead
        if y + row_height > height - margin:
            break
        left = column_left
        color = INK
        if user:
            text_width = max(_advance(_font(size, 650), line) for line in lines)
            text_width = max(text_width, _advance(_font(small, 650), "You"))
            bubble_width = min(round(column_width * .64), round(text_width + 2 * padding))
            left = width - margin - bubble_width
            draw.rounded_rectangle((left, y, width - margin, y + row_height), radius=max(6, round(size * .40)), fill=INK)
            left += padding
            text_y = y + padding
            color = PAPER
            draw.text((left, text_y), "You", font=_font(small, 650), fill=color, anchor="lt")
            text_y += small_height
        else:
            text_y = y
            if index:
                _text_block(canvas, name, (left, text_y, column_width, small_height), small, small, 650, color=SECONDARY)
                text_y += small_height
        for line in lines:
            draw.text((left, text_y), line, font=_font(size, 650 if user else 500), fill=color, anchor="lt")
            text_y += leading
        if message.meta:
            text_y += round(size * .25)
            _text_block(canvas, message.meta, (left, text_y, measure, small_height), small, small, 500, color=color if user else SECONDARY)
        y += row_height + gap


def _hero(canvas: Image.Image, state: dict, character: str, status: str, frame: int, monochrome: bool = False) -> None:
    width, height = canvas.size
    margin = max(12, round(min(width, height) * .064))
    draw = ImageDraw.Draw(canvas)
    header_size = max(14, min(44, round(min(width, height) * .031)))
    mark_size = max(12, round(header_size * .8))
    _mark(draw, margin, margin + (header_size - mark_size) // 2, mark_size)
    draw.text((margin + mark_size + round(header_size * .45), margin), "dots", font=_font(header_size, 700), fill=INK, anchor="lt")
    name = _clean(state.get("dot_name"), character.title()) or character.title()
    name_size = max(12, round(header_size * .72))
    name_width = max(36, width // 2 - margin)
    name = _ellipsize(name, _font(name_size, 500), name_width) if _advance(_font(name_size, 500), name) > name_width else name
    draw.text((width - margin, margin + header_size // 5), name, font=_font(name_size, 500), fill=INK, anchor="rt")
    top = margin + header_size + margin // 2
    footer_size = max(10, min(24, round(min(width, height) * .017)))
    footer_y = height - margin - footer_size
    content_bottom = footer_y - margin // 2
    available = content_bottom - top
    title = _clean(state.get("title"))
    text = _display_text(state, status)
    # The dot keeps the original quiet central composition; a long response
    # receives more paper instead of making its type progressively unreadable.
    long_answer = len(text) > 180
    mascot_size = round(min(width * .62, available * (.40 if long_answer else .58)))
    mascot_size = max(36, mascot_size)
    _mascot(canvas, character, ((width - mascot_size) // 2, top, mascot_size, mascot_size), status, frame, monochrome)
    text_y = top + mascot_size + max(6, margin // 3)
    if title:
        title_size = max(14, min(38, round(min(width, height) * .030)))
        title_height = round(title_size * 1.3)
        _text_block(canvas, title, (margin, text_y, width - margin * 2, title_height), title_size, title_size, 600, centered=True, color=SECONDARY)
        text_y += title_height + max(6, margin // 3)
    preferred = max(18, min(91, round(min(width, height) * .065)))
    minimum = max(16, min(40, round(min(width, height) * .037)))
    _text_block(canvas, text, (margin, text_y, width - margin * 2, content_bottom - text_y), preferred, minimum, centered=True)
    draw.line((margin, footer_y - footer_size // 2, width - margin, footer_y - footer_size // 2), fill=204, width=max(1, width // 1000))
    draw.text((margin, footer_y), _status_label(status), font=_font(footer_size, 500), fill=SECONDARY, anchor="lt")
    for index in range(3):
        radius = max(1, footer_size / 6)
        fill = INK if (frame % 3 == index and status == "thinking") or status == "answer" else 153
        _circle(draw, width - margin - (2 - index) * footer_size, footer_y + footer_size * .45, radius, fill)


def render_image(state: dict, width: int, height: int, levels: int = 16, format: str = "PNG", frame: int = 0) -> bytes:
    """Render an actual dot event as PNG or BMP at the device's native size.

    Supported dimensions are 64–2400 pixels in each direction. ``levels=2``
    produces a one-bit image with Floyd–Steinberg texture; ``levels=16`` uses
    exact, evenly spaced gray values. Unknown characters fall back to Artist;
    unknown statuses fall back to idle. Answer frames 1–10 make a small nod or
    wink; frames 0 and 11 are settled. Full text stays in the caller's API.
    """
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 64 <= value <= 2400 for value in (width, height)):
        raise ValueError("width and height must be integers between 64 and 2400")
    if width * height > 8_000_000:
        raise ValueError("image exceeds the pixel budget")
    if isinstance(levels, bool) or not isinstance(levels, int) or levels not in (2, 16):
        raise ValueError("levels must be 2 or 16")
    if not isinstance(format, str) or format.upper() not in {"PNG", "BMP"}:
        raise ValueError("format must be PNG or BMP")
    if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
        raise ValueError("frame must be a nonnegative integer")
    character = state.get("character", "artist")
    if not isinstance(character, str) or character not in CHARACTERS:
        character = "artist"
    status = state.get("status", "idle")
    if not isinstance(status, str) or status not in STATUSES:
        status = "idle"
    canvas = Image.new("L", (width, height), PAPER)
    if width < 180:
        _tiny(canvas, state, character, status, frame, levels == 2)
    elif height <= 180 or width / height >= 1.85:
        _compact(canvas, state, character, status, frame, levels == 2)
    elif status == "answer" and _conversation_mode(state) and _conversation_messages(state) and min(width, height) < 300:
        _compact(canvas, state, character, status, frame, levels == 2)
    elif status == "answer" and _conversation_mode(state) and _conversation_messages(state):
        _conversation(canvas, state, character, frame, levels == 2)
    elif status == "answer":
        _reply(canvas, state, character, frame, levels == 2)
    else:
        _hero(canvas, state, character, status, frame, levels == 2)
    if levels == 2:
        canvas = canvas.convert("1", dither=Image.Dither.NONE)
    else:
        canvas = canvas.point([round(value / 17) * 17 for value in range(256)])
    output = BytesIO()
    canvas.save(output, format=format.upper())
    return output.getvalue()
