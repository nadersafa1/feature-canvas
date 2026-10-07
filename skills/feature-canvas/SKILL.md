---
name: feature-canvas
description: Map a new product feature onto a design canvas of decisions, user flows, annotated wireframes and staged user stories, all rendered from one spec. Use when the user wants to plan, spec or design a feature before building it, or asks for its flows, wireframes or user stories.
---

# Feature canvas

A **canvas** is a set of **boards** on five kinds of page:

- **Overview:** a cover, the model, who can do what, journeys, states and the decisions log.
- **User flows:** one board per role.
- **Wireframes:** one page of annotated wireframes per surface, such as web or phone.
- **User stories:** a roadmap, then one board per stage.

Every board points at the others:
- a flow step names its screen and story (`W01 · B1.2`);
- a wireframe lists its stories;
- a story cites the decisions behind it (`#3`).

That web of references is what makes the canvas easy to build from.

`spec.py` in the work folder is the **single source**. The scripts render every board from it except the wireframes, which are drawn by hand. Never hand-edit a generated board: the next build overwrites it.

The scripts are in this skill's `scripts/` folder; call them by absolute path from the skill's base directory. They need only python3 and its standard library. `DIR` is the work folder.

## Steps

1. **Workspace.** Make `DIR` (a scratchpad folder unless the user names one). Copy `assets/example/spec.py` and `assets/example/WORLD.md` into it as the shape to replace, and read [SPEC.md](SPEC.md).
   *Done when* `DIR` holds both files.

2. **Decide.** If the feature extends an existing product, read its code and docs first. Then the decisions name what already exists, using the words on its screens. Interview the user one question at a time, starting with the questions that change the stage list. Record every answer as a numbered **decision**:
   - `agreed` when the user chose it;
   - `assumed` when they said "you decide": take the call and give your reason;
   - `open` while it is unanswered.

   *Done when* every role, surface, record type and stage has a name, and nothing open would change a stage.

3. **Brand.** The canvas wears the product's own look; it has no house style. Run `python3 scripts/brand.py <repo root>`. It reads the project's CSS variables (following `var()` chains and the import cascade), its Tailwind and theme files, and the fonts it loads. It then prints a proposed `BRAND` with the file each value came from.
   - Paste the proposal into `BRAND`.
   - Open two or three of the files it cites, plus the product's button, card and navigation components. Correct any token that disagrees with what users see.
   - Choose `mode` with the user when the product has both light and dark.
   - With no product yet, ask for a primary colour and a font, or keep the defaults and say so.

   *Done when* every `BRAND` value has a named source, or the user agreed to the default.

4. **Sample world.** Write `WORLD.md` as one concrete fictional world that every board uses:
   - a fixed "now";
   - a named person for every role;
   - real-looking records, with numbers that add up;
   - a short "use / never" vocabulary list.

   Copy the vocabulary into `VOCABULARY` in the spec, and each surface's navigation into its `nav`. *Done when* every screen you plan could be filled from the world without inventing anything new.

5. **Spec.** Fill `spec.py` from the decisions and the world.
   *Done when* `python3 scripts/check.py DIR --spec` reports `OK spec`. That check also proves every story is on a screen and every reference resolves.

6. **Build.** Run `python3 scripts/build.py DIR`. It writes:
   - the generated boards and `canvas.json`;
   - `helmet.html`;
   - `bundle.html`, a static viewer of every board;
   - `STORIES.md`, the stories as a backlog.

   *Done when* it prints the board count. It may also list the wireframes still to draw.

7. **Wireframes.** Draw every screen in `SCREENS` by [WIREFRAMES.md](WIREFRAMES.md). When the harness has parallel subagents, give each one a surface and the brief's absolute path. Afterwards:
   - merge every reported **World addition** into `WORLD.md`;
   - settle every reported **Conflict** in the world, the spec or a board.

   *Done when* `python3 scripts/check.py DIR` passes with nothing "not drawn yet", and no reported item is left unsettled.

8. **Fit.** Run `build.py` again. Open `bundle.html` in a browser, visit every page, then press **Board heights** and pass the JSON to `python3 scripts/fit.py DIR '<json>'`. Build once more.
   *Done when* Board heights shows `{}`, or you had no browser; say so in the report.

9. **Publish** by [PUBLISH.md](PUBLISH.md).
   *Done when* the user has a link, or the files if publishing isn't possible.

10. **Report.** Give the link, then the counts of stages, stories, screens and decisions. List every `assumed` decision so the user can overturn it, and every `open` one.

## Revising

A changed decision, story, flow or brand means: edit `spec.py`, then build, check and republish. A build re-applies `BRAND` to drawn wireframes too. For a changed screen, edit its wireframe file and run `check.py` on it.

When the user overturns an assumed decision, set it to `agreed` with the new text. Fix every story and wireframe that cites it before you rebuild.
