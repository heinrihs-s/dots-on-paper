---
name: dots on paper
description: A tactile ink companion on cool paper.
colors:
  ground: "#dfe9e3"
  ink: "#1d2925"
  secondary: "#4c6056"
  line: "#b9cac0"
  paper: "#f2f3ed"
  white: "#fafbf7"
  action-hover: "#40544a"
rounded:
  toggle: "5px"
  field: "6px"
  circle: "50%"
  character-picker: "12px"
  character-picker-mobile: "10px"
spacing:
  compact: "8px"
  control: "12px"
  rhythm: "16px"
typography:
  display:
    fontFamily: "Figtree, sans-serif"
    fontSize: "80px"
    fontWeight: 650
  body:
    fontFamily: "Figtree, sans-serif"
    fontSize: "16px"
    fontWeight: 400
  label:
    fontFamily: "Figtree, sans-serif"
    fontSize: "12px"
    fontWeight: 400
  character-label:
    fontFamily: "Figtree, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  character-label-mobile:
    fontFamily: "Figtree, sans-serif"
    fontSize: "11px"
    fontWeight: 400
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "12px 20px"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
  transport-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.circle}"
    width: "38px"
    height: "38px"
  toggle-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.toggle}"
    padding: "7px 12px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "12px 15px"
---

# Design System: dots on paper

## Overview

**Creative North Star: "The Paper Companion"**

A quiet mineral-green studio surrounds a physical charcoal display and a cool sheet of paper. Rounded Figtree lettering and a gray plush character give the work warmth; restrained controls let that material presence carry the identity.

Depth belongs to tangible objects: a softly lit bezel, paper fibers, a contact shadow, and the plush body. The surrounding interface stays light, open, and precise. This system is extracted from the standalone demo and does not prescribe the existing TRMNL dashboard.

**Key Characteristics:**

- Mineral-green ground with charcoal lettering.
- Tactile grayscale character and cool paper.
- Open layouts with fine separators.
- Small, clearly selected controls.

## Colors

The palette is restrained and botanical, with material neutrals carrying most of the contrast. The frontmatter records the normative values.

### Primary

- **Charcoal Ink:** lettering, primary actions, selected toggles, and transport controls.
- **Mineral Green:** the continuous studio ground surrounding the work.

### Neutral

- **Secondary Green:** supportive copy, timestamps, and inactive controls.
- **Fine Green Line:** separators, range tracks, and input borders.
- **Cool Paper:** the display surface.
- **Soft White:** input surfaces and reversed control text.
- **Hover Charcoal:** the lighter primary-action hover state.

**The Material Contrast Rule.** Keep dark control states legible against the pale studio ground; reserve textured light surfaces for the physical display and character scene.

## Typography

Figtree is self-hosted as a variable TrueType face, with a sans-serif fallback. Its rounded forms link the friendly character to a precise interface.

The interface uses regular body text and compact labels, with a heavier wordmark. Canvas lettering is specified in source pixels and scales with the entire drawing; its display token must not be copied as an unscaled browser heading. The studio headline is semibold, the response slightly heavier, and supporting copy quieter.

**The Single Voice Rule.** Use Figtree throughout the interface and canvas; create hierarchy through scale and weight.

## Layout

Center the work within a constrained stage and keep supporting controls aligned beneath it. The 4:3 drawing preserves its proportions at every width. Fine horizontal separators establish control bands without enclosing them in cards.

Below the mobile breakpoint, transport and format controls remain together while the scrubber receives a full row. Secondary tools wrap, and the answer field stacks above its submit action. Spacious margins belong to the studio, while control spacing stays compact. The actual breakpoints and widths are recorded in the sidecar.

## Elevation & Depth

The page interface is flat. Depth comes from the canvas hardware's subtle diagonal rim lighting and soft ambient shadow, with a faint contact shadow grounding the plush character. Paper fibers remain stable while the character moves; texture never becomes an animated overlay. Hardware shadow measurements use canvas source pixels.

**The Tangible Depth Rule.** Use shadows to explain a physical object's contact and lighting; keep interface controls flat.

## Shapes

Circular transport buttons echo the dot character. Selected toggles and fields have gently curved corners; thin separators stay straight. The hardware uses a much larger rounded silhouette, while the paper opening is almost square. Preserve these different material roles instead of applying one radius to everything.

## Components

### Buttons and transport

Primary actions use charcoal fill and soft white text, with the recorded hover charcoal. Pause/play has a circular filled treatment; replay is an open circular control. Text actions use an inline SVG arrow and gain an underline on hover. Keyboard focus is a charcoal outline (2px) offset from the element (5px).

### Segmented controls

Format and material choices share a compact, flat toggle language. Inactive labels are secondary green; the selected state uses charcoal and soft white. Selection is also exposed through `aria-pressed`.

### Input and scrubber

The answer input uses soft white, a fine green border, and the field radius. Its action sits alongside on desktop and below on mobile. The scrubber uses a fine track and a small charcoal circular thumb, accompanied by tabular timestamp numerals.

### Paper companion

Four generated gray plush bodies retain the reference characters' silhouettes: Artist wears a beret, Curious has raised white eye globes, Bookish is a rounded triangle with round wire glasses, and Cool is a heart with sunglasses. Canvas-drawn eyes blink, glance, and wink independently; glasses, sunglasses, and smiles use the same charcoal stroke language. Curious bobs more eagerly; Bookish moves more gently. A restrained smile accompanies the reply. These gestures belong to the character rather than the surrounding interface. Detailed timing and reduced-motion behavior live in the surface brief and sidecar.

### Character picker

A row of four small portrait buttons appears immediately below the stage. Each portrait uses the same generated body and canvas-drawn face as the animated character. The selected portrait has a pale green fill and a stronger label, with `aria-pressed` identifying selection. Desktop choices place the name beside the portrait; mobile choices place it beneath. Keep one selected character at a time and preserve the reply, view, and playback position while switching.

### Calendar Chaos example

The optional `calendar-chaos` preset is ordinary reply data: a short introduction, three bullet points, and a closing aside. A small companion avatar identifies the sender above a single left-aligned reading column. Paragraphs, bullets, numbered lists, and headings use the same renderer for every answer. Long replies scale down to a readable minimum, then end in a visible ellipsis with a continuation notice. The full text stays available in the editor and accessible description. Cool is the initial protagonist; the answer frame is initially paused. Switching dots preserves the reply and playback position.

### Conversation example

The `wife-noo` preset supplies timed assistant and user messages to a reusable conversation renderer. A draft status appears with the first assistant message, the user's “NOO” uses a compact right-aligned chat bubble, and a final assistant message confirms that nothing was sent. Extra reply/demo footer labels are omitted for the requested clean composition. These are scripted messages; the animation performs no messaging action. Example choices sit beneath the transport controls. Edited replies can be saved as the actual current studio or native-screen PNG.

## Do's and Don'ts

### Do:

- **Do** keep the paper, plush, and hardware materially distinct.
- **Do** preserve clear selected states and visible keyboard focus.
- **Do** keep canvas lettering proportional to its drawing.
- **Do** accommodate the full permitted reply through wrapping and adaptive type sizing.

### Don't:

- **Don't** animate the paper's fiber texture.
- **Don't** give flat interface controls the hardware's ambient shadow.
- **Don't** reuse this demo's visual rules as a mandate for the existing dashboard.
