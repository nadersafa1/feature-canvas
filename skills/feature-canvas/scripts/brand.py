"""Propose BRAND from a project's own UI: its CSS variables, Tailwind config, theme files and fonts.

usage: python3 brand.py REPO_DIR [--mode light|dark]

Prints a ready-to-paste BRAND dict for spec.py, with the file each value came from, and every
candidate it saw so a wrong guess is easy to correct. It is a heuristic: read the sources it names,
compare with a real screen when you can, and fix any token before you build.
"""
import json
import os
import re
import sys

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".expo", ".turbo", "coverage", "ios", "android",
             "Pods", ".venv", "venv", "__pycache__", "vendor", "out", ".output", "storybook-static", "worktrees"}
CSS_EXT = (".css", ".scss", ".sass", ".less", ".pcss")
CODE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json")
THEME_FILE = re.compile(r"(theme|colou?rs?|tokens?|palette|brand|tailwind\.config|design)", re.I)

# Token → CSS custom property names, most specific first (shadcn, Tailwind v4 @theme, common names).
CSS_NAMES = {
    "background": ["background", "color-background", "bg", "app-bg", "background-color"],
    "surface": ["card", "color-card", "surface", "color-surface", "popover", "panel"],
    "text": ["foreground", "color-foreground", "text", "text-primary", "ink", "color-text"],
    "muted": ["muted-foreground", "color-muted-foreground", "text-muted", "text-secondary", "muted"],
    "border": ["border", "color-border", "input", "border-color"],
    "primary": ["primary", "color-primary", "brand", "brand-primary", "accent"],
    "on_primary": ["primary-foreground", "color-primary-foreground", "on-primary"],
    "success": ["success", "color-success", "positive"],
    "warning": ["warning", "color-warning", "caution"],
    "danger": ["destructive", "color-destructive", "danger", "error", "color-error"],
    "radius": ["radius", "radius-md", "border-radius"],
    "font_sans": ["font-sans", "font-body", "default-font-family", "font-family-sans"],
    "font_display": ["font-display", "font-heading", "font-serif", "font-title"],
}
# Token → keys in JS/TS theme objects (React Native themes, Tailwind colors, design-token files).
CODE_NAMES = {
    "background": ["background", "bg", "appBackground", "screen"],
    "surface": ["card", "surface", "cardBackground", "paper"],
    "text": ["text", "foreground", "ink", "textPrimary", "label"],
    "muted": ["textMuted", "mutedText", "muted", "textSecondary", "secondaryText", "subtle"],
    "border": ["border", "separator", "divider", "outline"],
    "primary": ["primary", "tint", "brand", "accent"],
    "on_primary": ["onPrimary", "primaryForeground", "onAccent", "primaryText"],
    "success": ["success", "positive"],
    "warning": ["warning", "caution"],
    "danger": ["danger", "error", "destructive"],
}
COLOUR = r"(#[0-9A-Fa-f]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\)|oklab\([^)]*\))"


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            yield os.path.join(base, f)


def rel(root, path):
    return os.path.relpath(path, root)


def css_blocks(text):
    """(selector, body) for every innermost block, with comments removed."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for m in re.finditer(r"([^{}]*)\{([^{}]*)\}", text):
        yield re.split(r"[;}]", m.group(1))[-1].strip(), m.group(2)


GLOBAL_SELECTOR = re.compile(r":root|^html\b|[\s,]html\b|^body\b|@theme|\.dark\b|\.light\b|data-theme|data-mode|:host", re.I)


def scheme(selector):
    """Which colour scheme a global block serves: light, dark, both (names both) or generic."""
    sel = selector.lower()
    dark, light = "dark" in sel, "light" in sel
    if dark and light:
        return "both"
    return "dark" if dark else "light" if light else "generic"


def read_css(root):
    """Every custom property declared in a global block, as (name, value, source, order, scheme),
    plus each file's @imports and whether a generic block declares itself dark."""
    defs, imports, base_is_dark = [], {}, False
    for path in walk(root):
        if not path.endswith(CSS_EXT):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        source = rel(root, path)
        imports[source] = {os.path.basename(x) for x in re.findall(r"@import\s+(?:url\()?['\"]([^'\"]+)['\"]", text)}
        for order, (selector, body) in enumerate(css_blocks(text)):
            if not GLOBAL_SELECTOR.search(selector):
                continue  # a component's own variables, not the product's tokens
            sch = scheme(selector)
            if sch == "generic" and re.search(r"color-scheme\s*:\s*dark", body):
                base_is_dark = True
            for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", body):
                defs.append((name, value.strip(), source, order, sch))
    return defs, imports, base_is_dark


def table_for(mode, defs, imports):
    """{name: (value, source)} as the cascade would leave it in this mode."""
    best = {}
    for d in defs:
        name, _, source, order, sch = d
        if sch not in ("generic", "both", mode):
            continue
        if name not in best or beats(d, best[name], imports):
            best[name] = d
    return {name: (d[1], d[2]) for name, d in best.items()}


def beats(a, b, imports):
    """An importing file beats what it imports; in one file, mode-specific beats generic, then later
    beats earlier; between unrelated files, mode-specific beats generic and the first one stays."""
    specific = lambda d: d[4] != "generic"  # noqa: E731
    if os.path.basename(b[2]) in imports.get(a[2], set()):
        return True
    if os.path.basename(a[2]) in imports.get(b[2], set()):
        return False
    if a[2] == b[2]:
        return (specific(a), a[3]) > (specific(b), b[3])
    return specific(a) and not specific(b)


def resolve(name, table, depth=0):
    """Follow var(--x) chains, including fallbacks, inside one scheme's table."""
    if name not in table or depth > 12:
        return None, None
    value, source = table[name]
    m = re.fullmatch(r"var\(\s*--([\w-]+)\s*(?:,\s*(.+))?\)", value)
    if m:
        inner, src = resolve(m.group(1), table, depth + 1)
        if inner is None and m.group(2):
            return m.group(2).strip(), source
        return inner, src
    return value, source


def hsl_triplet(value):
    """shadcn v3 stores colours as bare 'H S% L%' triplets."""
    if re.fullmatch(r"-?[\d.]+\s+[\d.]+%\s+[\d.]+%(\s*/\s*[\d.]+%?)?", value):
        return f"hsl({value})"
    return value


def from_css(table):
    out = {}
    for token, names in CSS_NAMES.items():
        for n in names:
            value, source = resolve(n, table)
            if value and "var(" not in value:
                if token.startswith("font"):
                    value = first_font(value)
                elif token != "radius":
                    value = hsl_triplet(value)
                if value:
                    out[token] = {"value": value, "from": f"{source} (--{n})"}
                    break
    return out


def first_font(stack):
    name = stack.split(",")[0].strip().strip("'\"")
    generic = {"sans-serif", "serif", "system-ui", "monospace", "ui-sans-serif", "ui-serif", "-apple-system", "inherit"}
    return None if name in generic or name.startswith("var(") else name.replace(" Variable", "")


def from_code(root, mode):
    """Colour keys in theme-like JS/TS files. A `light:`/`dark:` key before a value scopes it."""
    out, seen = {}, {}
    for path in walk(root):
        if not path.endswith(CODE_EXT) or not THEME_FILE.search(os.path.basename(path)) or path.endswith("package.json"):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if len(text) > 400_000:
            continue
        for m in re.finditer(r"([A-Za-z_][\w]*)\s*:\s*['\"]" + COLOUR + r"['\"]", text):
            before = text[:m.start()]
            scope = "dark" if before.rfind("dark") > before.rfind("light") else "light"
            if "light" not in before and "dark" not in before:
                scope = "base"
            seen.setdefault(m.group(1), []).append((m.group(2), scope, rel(root, path)))
    for token, keys in CODE_NAMES.items():
        for k in keys:
            for value, scope, source in seen.get(k, []):
                if scope in (mode, "base"):
                    out[token] = {"value": value, "from": f"{source} ({k})"}
                    break
            if token in out:
                break
    return out, {k: v[:3] for k, v in seen.items()}


def fonts(root):
    """Font families the project loads: @fontsource, Google Fonts links, expo-google-fonts, fontFamily."""
    found = []

    def add(name, source):
        name = name.replace(" Variable", "").strip()
        if name and name not in [f["name"] for f in found]:
            found.append({"name": name, "from": source})

    for path in walk(root):
        base = os.path.basename(path)
        if not (path.endswith(CSS_EXT + CODE_EXT + (".html",)) or base == "package.json"):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in re.finditer(r"@fontsource(?:-variable)?/([a-z0-9-]+)", text):
            add(m.group(1).replace("-", " ").title(), rel(root, path))
        for m in re.finditer(r"@expo-google-fonts/([a-z0-9-]+)", text):
            if m.group(1) != "dev":
                add(m.group(1).replace("-", " ").title(), rel(root, path))
        for m in re.finditer(r"fonts\.googleapis\.com/css2?\?([^\"')\s]+)", text):
            for fam in re.findall(r"family=([^:&;]+)", m.group(1)):
                add(fam.replace("+", " "), rel(root, path))
    return found


def lightness(colour):
    """0 (black) to 1 (white) for hex, rgb() and oklch() values; None when it can't tell."""
    c = colour.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})([0-9a-f]{2})?", c)
    if m:
        h = m.group(1) if len(m.group(1)) == 6 else "".join(ch * 2 for ch in m.group(1))
        rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    elif c.startswith("rgb"):
        rgb = [float(x) / 255 for x in re.findall(r"[\d.]+", c)[:3]]
    elif c.startswith("oklch") or c.startswith("oklab"):
        first = re.findall(r"[\d.]+%?", c)[0]
        return float(first[:-1]) / 100 if first.endswith("%") else float(first)
    else:
        return None
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    root = os.path.abspath(argv[1])
    defs, imports, base_is_dark = read_css(root)
    has = lambda sch: any(d[4] == sch for d in defs)  # noqa: E731
    default_mode = "dark" if base_is_dark and has("light") else "light"
    if not has("light") and not has("dark") and not has("both"):
        bg = from_css(table_for("light", defs, imports)).get("background")
        level = lightness(bg["value"]) if bg else None
        default_mode = "dark" if level is not None and level < 0.2 else "light"
    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else default_mode
    tokens = from_css(table_for(mode, defs, imports))
    code_tokens, code_seen = from_code(root, mode)
    for k, v in code_tokens.items():
        tokens.setdefault(k, v)
    families = fonts(root)
    if "font_sans" not in tokens and families:
        tokens["font_sans"] = {"value": families[0]["name"], "from": families[0]["from"]}
    if "font_display" not in tokens:
        serif = [f for f in families if re.search(r"serif|display|slab|playfair|fraunces|lora|merriweather", f["name"], re.I)
                 and "Sans" not in f["name"]]
        if serif:
            tokens["font_display"] = {"value": serif[0]["name"], "from": serif[0]["from"]}
    brand = {"mode": mode, **{k: v["value"] for k, v in tokens.items()}}
    missing = [k for k in ("background", "surface", "text", "muted", "border", "primary", "on_primary") if k not in tokens]
    print("# Proposed BRAND for spec.py (mode:", mode + ";", "the product's default is", default_mode + ")")
    print("BRAND = " + json.dumps(brand, indent=4, ensure_ascii=False))
    print("\n# Where each value came from")
    for k, v in tokens.items():
        print(f"#   {k:<13} {v['value']:<28} {v['from']}")
    if missing:
        print("# Not found (the kit default stays):", ", ".join(missing))
    print("# Fonts the project loads:", ", ".join(f["name"] for f in families) or "none found")
    other = "dark" if mode == "light" else "light"
    if has(other) or (other == "dark" and base_is_dark):
        print(f"# The project also has a {other} scheme: run with --mode {other} to see it.")
    if not tokens:
        print("# Nothing found. Theme-like code keys seen:", json.dumps(dict(list(code_seen.items())[:20])))


if __name__ == "__main__":
    main(sys.argv)
