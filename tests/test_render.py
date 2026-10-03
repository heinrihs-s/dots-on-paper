"""Tests for the physical display renderer, independent of the web preview."""

from io import BytesIO
from pathlib import Path
import sys
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dots_on_paper.render import _parse_reply, _reply_layout, render_image


class RendererTests(unittest.TestCase):
    def state(self, **changes):
        state = {
            "status": "answer", "character": "artist", "dot_name": "My dot",
            "title": "A little answer", "text": "Good ideas deserve a little paper.",
            "revision": 1, "event_id": "answer-1", "updated_at": "2026-10-03T10:00:00Z",
        }
        state.update(changes)
        return state

    def decode(self, output):
        image = Image.open(BytesIO(output))
        image.load()
        return image

    def test_native_png_is_exact_16_tone_grayscale(self):
        output = render_image(self.state(), 1872, 1404)
        image = self.decode(output)
        self.assertEqual(output[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(image.size, (1872, 1404))
        self.assertEqual(image.mode, "L")
        self.assertEqual(set(image.tobytes()), set(range(0, 256, 17)))

    def test_monochrome_has_only_two_values_and_bmp_is_supported(self):
        for format in ("PNG", "BMP"):
            with self.subTest(format=format):
                image = self.decode(render_image(self.state(), 296, 128, levels=2, format=format))
                self.assertEqual(image.format, format)
                self.assertEqual(image.size, (296, 128))
                self.assertEqual(image.mode, "1")
                self.assertEqual(set(image.convert("L").tobytes()), {0, 255})

    def test_all_characters_on_portrait_and_small_landscape(self):
        distinct = set()
        for character in ("artist", "curious", "bookish", "cool"):
            for width, height in ((296, 128), (600, 800)):
                with self.subTest(character=character, dimensions=(width, height)):
                    output = render_image(self.state(character=character), width, height)
                    self.assertEqual(self.decode(output).size, (width, height))
                    distinct.add(output)
        self.assertEqual(len(distinct), 8)

    def test_long_unicode_is_clipped_without_changing_real_state(self):
        value = ("Īsts ziņojums — café 日本語 مرحبا 👋\n" * 400) + "last line"
        state = self.state(text=value)
        for dimensions in ((296, 128), (800, 600), (600, 800), (64, 64)):
            with self.subTest(dimensions=dimensions):
                image = self.decode(render_image(state, *dimensions))
                self.assertEqual(image.size, dimensions)
        self.assertEqual(state["text"], value)

    def test_invalid_state_fields_fall_back_safely(self):
        invalid = self.state(character=[], status={})
        expected = self.state(character="artist", status="idle")
        self.assertEqual(render_image(invalid, 296, 128), render_image(expected, 296, 128))

    def test_state_and_frame_change_the_expression(self):
        outputs = [render_image(self.state(status=status), 800, 600) for status in ("idle", "thinking", "answer", "error")]
        self.assertEqual(len(set(outputs)), 4)
        for character in ("artist", "curious", "bookish", "cool"):
            with self.subTest(character=character):
                state = self.state(character=character, status="thinking")
                self.assertNotEqual(render_image(state, 296, 128, frame=0), render_image(state, 296, 128, frame=1))

    def test_answer_arrival_animates_only_the_mascot_and_settles(self):
        text = "This actual reply stays readable while your dot acknowledges it."
        for character in ("artist", "curious", "bookish", "cool"):
            for dimensions in ((296, 128), (600, 800)):
                with self.subTest(character=character, dimensions=dimensions):
                    state = self.state(character=character, text=text)
                    start = self.decode(render_image(state, *dimensions, levels=2, frame=0))
                    moving = self.decode(render_image(state, *dimensions, levels=2, frame=5))
                    settled = self.decode(render_image(state, *dimensions, levels=2, frame=11))
                    self.assertNotEqual(start.tobytes(), moving.tobytes())
                    self.assertEqual(start.tobytes(), settled.tobytes())
                    width, height = dimensions
                    # The reply occupies the right side on a small landscape
                    # panel and the lower reading area on a portrait panel.
                    text_box = (120, 0, width, height) if height == 128 else (0, round(height * .6), width, height - 50)
                    self.assertEqual(start.crop(text_box).tobytes(), moving.crop(text_box).tobytes())
                    self.assertEqual(state["text"], text)

    def test_arguments_are_validated(self):
        cases = [
            {"width": 63}, {"height": 2401}, {"width": 128.5}, {"width": True},
            {"levels": 3}, {"levels": True}, {"levels": 16.0}, {"format": "JPEG"}, {"format": None},
            {"frame": -1}, {"frame": 1.5}, {"frame": True}, {"state": []},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                args = {"state": self.state(), "width": 296, "height": 128}
                args.update(changes)
                with self.assertRaises(ValueError):
                    render_image(**args)

    def test_empty_idle_uses_truthful_waiting_copy(self):
        self.assertEqual(
            render_image({"status": "idle"}, 296, 128),
            render_image({"status": "idle", "text": "Waiting for your dot."}, 296, 128),
        )

    def test_answer_text_changes_pixels_without_requiring_a_browser(self):
        one = render_image(self.state(text="First real answer."), 296, 128)
        two = render_image(self.state(text="A different real answer."), 296, 128)
        self.assertNotEqual(one, two)

    def test_reply_parser_preserves_paragraphs_bullets_and_numbered_lists(self):
        text = (
            "Here are your reminders:\n\n"
            "- **Tonight:** Date with Paula.\n"
            "* Tomorrow morning: Breakfast with Amy.\n"
            "• Lunch: With your wife.\n\n"
            "Your calendar needs a lawyer.\n\n"
            "1. Check the dates.\n2) Leave time to travel."
        )
        blocks = _parse_reply(text)
        self.assertEqual([block.marker for block in blocks], ["", "•", "•", "•", "", "1.", "2)"])
        self.assertEqual(blocks[1].text, "Tonight: Date with Paula.")
        self.assertEqual(blocks[4].text, "Your calendar needs a lawyer.")
        self.assertNotIn("**", " ".join(block.text for block in blocks))

    def test_reply_parser_accepts_unrelated_content_and_soft_line_breaks(self):
        blocks = _parse_reply(
            "The build finished.\nAll checks passed.\n\n"
            "- Update the configuration\n  before restarting the service.\n\n"
            "You can deploy whenever you are ready."
        )
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].text, "The build finished. All checks passed.")
        self.assertEqual(blocks[1].text, "Update the configuration before restarting the service.")
        self.assertEqual(blocks[2].marker, "")

    def test_wrapped_list_lines_keep_a_hanging_indent(self):
        layout = _reply_layout(
            "A response:\n\n- This item is deliberately long enough to wrap across several lines.\n\nA closing paragraph.",
            width=250, height=700, preferred=30, minimum=30,
        )
        bullet_index = next(index for index, line in enumerate(layout.lines) if line.marker == "•")
        indent = layout.lines[bullet_index].x
        self.assertGreater(indent, 0)
        self.assertEqual(layout.lines[bullet_index + 1].x, indent)
        self.assertEqual(layout.lines[bullet_index + 1].marker, "")
        self.assertEqual(layout.lines[-1].x, 0)
        self.assertFalse(layout.clipped)

    def test_long_reply_uses_a_visible_ellipsis_at_a_readable_minimum(self):
        layout = _reply_layout(
            "Introduction.\n\n- " + "A long real reply " * 200 + "\n\nClosing.",
            width=340, height=180, preferred=40, minimum=24,
        )
        self.assertTrue(layout.clipped)
        self.assertEqual(layout.font_size, 24)
        self.assertTrue(layout.lines[-1].text.endswith("…"))
        self.assertLessEqual(layout.lines[-1].y + layout.leading, 180)

    def test_native_reply_has_room_for_the_ordinary_reminder_response(self):
        text = (
            "Here are your reminders:\n\n"
            "- Tonight: Date with Paula.\n"
            "- Tomorrow morning: Breakfast with Amy.\n"
            "- Lunch: With your wife.\n\n"
            "Your calendar needs a lawyer."
        )
        layout = _reply_layout(text, width=1435, height=894, preferred=64, minimum=42)
        self.assertFalse(layout.clipped)
        self.assertEqual(layout.font_size, 64)
        self.assertEqual(len(layout.lines), 5)
        self.assertEqual([line.marker for line in layout.lines], ["", "•", "•", "•", ""])

    def test_native_answer_frames_keep_the_sender_and_whole_reply_still(self):
        state = self.state(
            character="cool", dot_name="Codex dot", title="",
            text="Here are your reminders:\n\n- Tonight: Date with Paula.\n- Lunch: With your wife.\n\nYour calendar needs a lawyer.",
        )
        start = self.decode(render_image(state, 1872, 1404, frame=0))
        moving = self.decode(render_image(state, 1872, 1404, frame=5))
        settled = self.decode(render_image(state, 1872, 1404, frame=11))
        self.assertNotEqual(start.tobytes(), moving.tobytes())
        self.assertEqual(start.tobytes(), settled.tobytes())
        self.assertEqual(start.crop((346, 0, 1872, 1404)).tobytes(), moving.crop((346, 0, 1872, 1404)).tobytes())


if __name__ == "__main__":
    unittest.main()
