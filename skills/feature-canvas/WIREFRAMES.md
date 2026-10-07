# Drawing wireframe boards

A wireframe board is one screen of the feature, drawn in a device frame, beside a **notes** column that explains it. Red numbered **markers** on the screen match numbered points in the notes. Draw each board by hand from its `SCREENS` brief.

This page is the whole brief for a drawing subagent. Pass it:
- the absolute path of this file;
- `DIR`;
- the screen ids it owns.

Paths below that don't start with `DIR` are relative to this skill's folder.

## Read first

1. `DIR/WORLD.md`, the sample world. It is the truth. See "The world wins" below.
2. `DIR/spec.py`: your screens' briefs, the stories and decisions they cite, and the surface's `nav`.
3. The exemplar for the frame, for structure only: [`assets/exemplars/phone.dc.html`](assets/exemplars/phone.dc.html) (800 × 1020) or [`assets/exemplars/web.dc.html`](assets/exemplars/web.dc.html) (1640 × 980). Its content is an illustration from the example canvas, not a fact of your world.

## Making the file

Never hand-write the shell or the helmet. For each screen:

1. Write the **body** to `DIR/work/<id>.body.html`: the device frame, then `<aside class="notes">`. That is everything inside the board root. Write it in one write call per board; large outputs fail.
2. Board-local CSS, if any, goes in `DIR/work/<id>.css`.
3. Wrap it:

   ```bash
   python3 scripts/board.py DIR <id>-<slug>.dc.html <width> <height> DIR/work/<id>.body.html [DIR/work/<id>.css]
   ```

4. Check it:

   ```bash
   python3 scripts/check.py DIR DIR/root/project/<id>-<slug>.dc.html
   ```

   Fix every error before you start the next board.

Sizes: phone boards are 800 wide, web boards 1640 wide. Use the spec's `"h"` when it gives one; otherwise phone boards are 1020 tall and web boards 980. A longer screen grows in steps of 80 px and is never clipped.

## Frames

- **Phone:** `.phone` (410 wide) > `.n` (390 inner) > `.inset` (status-bar space), then `.hdr`, then `main.scroll`, then `.cta` or `.tabbar`.
- **Web:** `.browser` (1250 wide) > `.urlbar` > `.app` > `nav.sidebar` + `.main`. Inside `.main` are `header.top` and `main`. The URL shows `[web domain]/real/path`.
- **Navigation:** draw the surface's `nav` from the spec, with the screen's own area active. If the surface has no `nav`, stop and report it rather than inventing one.
- **Dialogs and sheets:** draw them inside the frame:
  1. a `.scrim` over the screen;
  2. then a `.dialog` (web) or `.sheet` (phone), positioned absolutely.

  Markers sit above the scrim. Text under the scrim is exempt from the contrast rule; text in the dialog is not.

## Notes column

Use `<aside class="notes">`, with these parts in order:
1. an eyebrow (`Web · Front desk`);
2. an `h1` naming the screen;
3. a one-sentence lead naming who is doing what, and when if it isn't "now";
4. an `.hr` divider;
5. an `ol` of 3–7 points, each `<li><span class="mk">n</span><div><b>Short claim.</b> Why, in a sentence or two, citing #decisions.</div></li>`;
6. a second `.hr`;
7. a **Stories** eyebrow with one `.chip` per story id;
8. a **Next** eyebrow with `→ <next screen id and title>`. On the last screen of a flow, use `→ End of the flow`.

Each point justifies a choice the screen makes; never narrate what is visible. Place marker `n` on the screen at the exact element:
- `<span class="mk mka">n</span>` inside a `.rel` wrapper;
- or an inline `<span class="mk">n</span>` beside a label.

## The world wins

- Every name, time, amount and count comes from WORLD.md. No lorem ipsum.
- The brief names the state to show, such as a full class, an open dialog or a conflict. Find a moment in the world where that state is true. A screen may show a moment other than "now" (later that day, or the morning of the class); its lead must say when.
- If no moment in the world holds the state, **don't edit WORLD.md**: parallel drawers would overwrite each other. Pick the smallest fact that fits the world, use it, and list it under **World additions** in your report.

## Rules

- Use real controls:
  - `<button>`, `<a href="#">`, `<input>` with a `<label>`;
  - `aria-label` on icon-only buttons;
  - never a `div` or `span` acting as a button.
- On the phone, every tappable element is at least 44 px tall. Use `.btn`, `.btn-sm`, `.pill` (`.pill-on` when selected) or `.ib`. `.chip` is a label, never a control.
- Icons are inline stroke SVG using `class="i"` or `class="ic"`. Never emoji.
- Text contrast is at least 4.5:1. Muted text is `#4A5C66`, never lighter.
- Use the `feature` colour (`.chip-feat`, `.feat-rail`) only where the new feature appears inside an existing screen.
- Static markup only: no script-built UI, `<iframe>`, `<object>` or `<embed>`.

## Report

- **Boards:** for each one, the file name, its final size, and every choice the brief didn't settle (one line each).
- **World additions:** every fact you had to add, so the orchestrator can merge them into WORLD.md.
- **Conflicts:** anything in the world, the stories or the decisions that disagrees with itself. The product owner reads these.
