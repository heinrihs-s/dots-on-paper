# Calendar Chaos provenance

These eight PNGs are deterministic renders of the separate Calendar Chaos example in `dots-demo/demo.js`, composed for the user's fictional social-post request on 3 October 2026.

- `calendar-chaos-poster-<character>.png`: 1600×1200 studio canvas at nine seconds.
- `calendar-chaos-screen-1872x1404-<character>.png`: 1872×1404 native screen canvas at nine seconds.
- Characters: Artist, Curious, Bookish, and Cool. Cool is the share URL's initial character.

The plush bodies come from the existing generated `assets/beret-dot.png`, `curious-dot.png`, `bookish-dot.png`, and `cool-dot.png`. Their exact generation prompts are saved in adjacent `.prompt.md` files. All eyes, eyewear, facial expressions, hardware, paper fibers, lettering, calendar layout, and compositing are authored by canvas. Figtree uses the included SIL Open Font License. No new image generation was used for this example.

Each PNG embeds its render provenance and the corresponding plush source prompt in text metadata. Metadata insertion preserves the rendered pixels.

The fictional reminders are “Date with Paula tonight.”, “Breakfast with Amy tomorrow.”, and “Lunch with my wife.” The dot's fictional reply is “Your calendar needs a lawyer.” No actual calendar, person, or dot supplied these events.

Reproduce using `node dots-demo/tools/export-calendar.mjs` while the local preview server is running. That harness verifies original defaults, the example's first frame, all four character selections, the prepared download links, custom reply behavior, screen-reader copy, and mobile overflow. Desktop/mobile inspection captures are saved under `.impeccable/review/calendar-chaos-*.png`.

The implementation pass inspected studio and mobile output. The independent scoped finish review passed: the poster and native screen are readable, the composition is eye-catching, and the punchline lands without adding visual clutter.
