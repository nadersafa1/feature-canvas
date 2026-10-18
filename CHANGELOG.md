# Changelog

## 1.1.1

- The static `bundle.html` stores the kit's `<helmet>` once instead of once per board, so a canvas is about 60% smaller. The boards render the same.
- The README says where the plugin works and what it reads, writes and sends.
- CI validates the plugin and builds the worked example on every push.
- A listing icon for the plugin directory, with its editable SVG source in the docs folder.

## 1.1.0

- Boards take on the product's look. `brand.py` proposes `BRAND` from the repo's CSS variables, Tailwind `@theme`, JS/TS theme files and loaded fonts, with light and dark detection.
- Wireframes may not hard-code colours; `check.py` enforces it, and `build.py` re-themes drawn boards on every build.

## 1.0.0

- First release: plan a feature as a design canvas of decisions, user flows, annotated wireframes and staged user stories, rendered from one `spec.py`.
