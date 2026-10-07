# Publishing the canvas

Use the first of these routes that your environment supports.

## 1. A Design canvas artifact (claude.ai)

Use this route when the Artifact tool offers a **Design** (canvas) type: a quickstart with intent `design` lists it. On that type, the boards are artboards you can pan, zoom, comment on and share, with one page per canvas page.

1. Create the canvas once. Publish with that type's `type_url` and `title` set to `CANVAS.title`, and set `auto_open` to `"after_first_write"` when that option is offered.
2. Publish in two calls, with `url` set to the new canvas and `root` set to `DIR/root`:
   1. The first call publishes the index and the cover:
      - `file_path`: the absolute path of `DIR/root/project/canvas.json`;
      - `files`: `{"project/Main.dc.html": "project/Main.dc.html"}`.
   2. The second call publishes every other board in `canvas.json`'s `order`:
      - `file_path`: one of those boards;
      - `files`: the rest, mapped the same way.
3. The boards bring their own kit (`helmet.html`). Don't install a design system unless the user asks for one.
4. To update the canvas later, send only the boards that changed. Send `canvas.json` as well only when boards were added, removed or resized. Before changing an index someone else may have edited, read it with the Artifact `read` action.

The Design type's own instructions travel with it. Follow them wherever they differ from this page about calls and file shapes.

## 2. A plain HTML artifact

`DIR/bundle.html` is self-contained: every board, page tabs, zoom, and click to open a board full size. Publish it as an HTML page, following the harness's page rules. It must stay under 16 MB, which about 400 boards fit in.

## 3. Files only

Hand the user `bundle.html`, which opens in any browser, and `STORIES.md`. Mention that `DIR/root/project/` can be uploaded to a Design canvas later as it is.

In every route, offer to copy `STORIES.md` and the decisions into the user's repo or issue tracker. That backlog is what the implementation starts from.
