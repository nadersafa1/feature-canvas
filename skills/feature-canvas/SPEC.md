# spec.py: the single source

`spec.py` holds plain Python data in UPPER_CASE names, and nothing else. [`assets/example/spec.py`](assets/example/spec.py) is a complete worked example; copy its shape. Fields marked *optional* can be left out, and their board is then skipped.

## Ids

| Kind | Format | Example |
|---|---|---|
| Stage | letter + number | `B2` |
| Story | stage id `.` number | `B2.3` |
| Screen | surface letter + 2 digits | `W01` (web), `M04` (mobile) |
| Flow | `F` + number | `F1` |
| Decision | integer, cited as `#n` | `#3` |

Prose refs such as `"W01 · B1.2"` in flow nodes and journeys are checked: every id-shaped token must exist.

## CANVAS

`title`, `product`, `feature`, `lead` (one or two sentences for the cover), `now` (the sample world's clock). *Optional:* `model_title`, `model_lead`, `roadmap_lead`.

## BRAND *(optional)*

Overrides the default kit: `ink` (text and dark fills), `accent` (buttons and outcomes; must carry ink text), `feature` (the one colour that marks the new feature on existing screens), `ground`, `serif`, `sans` (Google Fonts family names). Soft and darker tints are derived.

## SURFACES

Where the feature lives: `{"id", "name", "kind": "web" | "phone", "color", "page", "nav"}`. `page` is the wireframe page's name; surfaces sharing a `page` share the page. `nav` lists the navigation items wireframes draw: the tab bar on a phone, the sidebar items on the web (an item ending in `/` is a sidebar heading). Copy the real product's navigation when it exists.

## ROLES

`{"id", "name", "persona", "surfaces": [surface ids], "does"}`. `persona` is the named person from WORLD.md; `does` is one sentence.

## ENTITIES *(optional)*

`{"name", "what", "facts": [..], "links": [..]}`: the records the feature adds. These render the Model board.

## PERMISSIONS *(optional)*

`[(group, [(action, {role id: cell})])]`. A cell is `"Yes"`, a limit in words (`"Own classes"`), or omitted for never.

## JOURNEYS *(optional)*

`{"role", "title", "steps": [(text, ref or None)]}`: the end-to-end path per role, six steps or so.

## LIFECYCLES *(optional)*

`{"lead", "lanes": [lane]}`, using `state` nodes. Arrow labels say who or what moves the record.

## FLOWS

`{"id", "role", "title", "lead", "lanes": [lane]}`, normally one flow per role. A **lane** is one job:

```python
{"tag": "B2", "title": "Book a place",
 "nodes": [(id, row, col, kind, title, refs?)],   # col 0–4, row 0–2; one node per cell
 "edges": [(from, to), (from, to, "label"), (from, to, "label", True)]}  # True = dashed
```

| kind | means |
|---|---|
| `step` | a person acts on a screen; refs `"W01 · B1.2"` |
| `decision` | a yes/no fork; label the outgoing edges |
| `system` | the product does it on its own |
| `push` | a notification |
| `end` | the outcome |
| `state` | lifecycles only |

Keep the main path on row 0, left to right, and put exceptions on row 1 under the decision that leads to them.

## SCREENS

`{"id", "slug", "title", "surface", "stories": [story ids], "brief"}`. The **brief** is the wireframe's whole spec: say which screen and state is shown, what sample data from WORLD.md appears on it, and which dialog or edge case is open. *Optional:* `"h"`, a height in px when the screen is long. Every story must be on at least one screen, unless its stage is `later` or the story sets `"screen": False` (a push, or a job with no UI).

## SCREEN_ROWS *(optional)*

`{page name: [(row title, [screen ids])]}`: groups a wireframe page into titled rows. Without it, rows are cut by count.

## STAGES

Stages are in build order. Each stage is deployable on its own.

```python
{"id": "B2", "name": "Members book", "track": "Members", "after": ["B1"],
 "tagline": "...", "gets": "what the user gets when it ships", "later": False,
 "stories": [story]}
```

`track` is the roadmap row and `after` lists what the stage needs first. `later: True` puts the stage in the parking lot.

A **story**:

```python
{"id": "B2.2", "size": "S" | "M" | "L", "surfaces": [surface ids], "title": "Book a place",
 "as": role id, "want": "to book a place in one tap", "so": "I'm sure I'm in",
 "accept": ["checkable acceptance points"], "decisions": [1, 3]}
```

Sizes are relative effort (S 1, M 2, L 3). `accept` points must be checkable by a tester, not aspirations.

## MILESTONES *(optional)*

`{"name", "stages": [ids], "what"}`: what a user can do once those stages ship.

## DECISIONS

`{"n", "topic", "status": "agreed" | "assumed" | "open", "text"}`. One decision per call; the text states the rule, not the discussion.

## VOCABULARY

`{"use": [words], "never": {"word": "say X instead"}}`. `check.py` fails any board that uses a `never` word.
