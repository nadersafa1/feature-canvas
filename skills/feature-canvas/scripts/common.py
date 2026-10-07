"""Shared helpers: loading the spec, the brand-filled kit, and the board page shell."""
import html
import json
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

# Screen tokens: what the product looks like inside the device frames. brand.py proposes them from
# the project's own CSS variables, Tailwind config, theme files and font imports.
SCREEN_DEFAULTS = {
    "mode": "light",
    "background": "#F5F6F2",
    "surface": "#FFFFFF",
    "text": "#0E2F3E",
    "muted": "#4A5C66",
    "border": "#D5DBE0",
    "primary": "#C4D433",
    "on_primary": "#0E2F3E",
    "feature": "#7A45E6",
    "success": "#6B8E23",
    "warning": "#E8A33A",
    "danger": "#D93A3A",
    "radius": "0px",
    "radius_phone": "14px",
    "font_sans": "Inter",
    "font_display": "",
}

# Canvas tokens: the paper around the screens (notes, flows, roadmap). On a light product they
# follow the product's text, muted and border colours; on a dark one they stay a light paper.
CANVAS_DEFAULTS = {
    "canvas_ground": "#E9E7E0",
    "canvas_ink": "#0E2F3E",
    "canvas_muted": "#4A5C66",
    "canvas_line": "#D6DBD7",
    "marker": "#C8361A",
}

LEGACY_KEYS = {"ink": "text", "accent": "primary", "serif": "font_display", "sans": "font_sans", "ground": "canvas_ground"}

SIZE_PTS = {"S": 1, "M": 2, "L": 3}


def brand_tokens(spec):
    given = {LEGACY_KEYS.get(k, k): v for k, v in spec.get("BRAND", {}).items()}
    b = {**SCREEN_DEFAULTS, **CANVAS_DEFAULTS, **given}
    if b["mode"] == "light":
        for key, src in (("canvas_ink", "text"), ("canvas_muted", "muted"), ("canvas_line", "border")):
            if key not in given:
                b[key] = b[src]
    for key in ("font_sans", "font_display"):
        b[key] = b[key].replace(" Variable", "").strip().strip("'\"")
    b["font_display"] = b["font_display"] or b["font_sans"]
    return b


def font_stack(name, fallback):
    return f"'{name}', {fallback}"


def css_vars(b):
    """The :root block that feeds kit.css. Text on tinted fills is mixed towards black on light
    surfaces and towards white on dark ones, so status chips stay readable in either mode."""
    on_dark = b["mode"] == "dark"
    tone = lambda var, light_pct=55, dark_pct=45: (  # noqa: E731
        f"color-mix(in srgb,var({var}) {dark_pct}%,#fff)" if on_dark else f"color-mix(in srgb,var({var}) {light_pct}%,#000)")
    light_tone = lambda var, pct=55: f"color-mix(in srgb,var({var}) {pct}%,#000)"  # noqa: E731
    root = {
        "--font-sans": font_stack(b["font_sans"], "system-ui, -apple-system, sans-serif"),
        "--font-display": font_stack(b["font_display"], "Georgia, serif" if b["font_display"] != b["font_sans"] else "system-ui, sans-serif"),
        "--primary": b["primary"], "--on-primary": b["on_primary"], "--feature": b["feature"],
        "--success": b["success"], "--warning": b["warning"], "--danger": b["danger"], "--marker": b["marker"],
        "--primary-text": light_tone("--primary", 45), "--feature-text": light_tone("--feature", 60),
        "--success-text": light_tone("--success", 55), "--warning-text": light_tone("--warning", 45),
        "--danger-text": light_tone("--danger", 60),
        "--ground": b["canvas_ground"], "--surface": "#FFFFFF", "--ink": b["canvas_ink"],
        "--ink-2": "color-mix(in srgb,var(--ink) 85%,var(--ground))", "--muted": b["canvas_muted"],
        "--line": b["canvas_line"], "--line-soft": "color-mix(in srgb,var(--line) 60%,#fff)",
        "--soft": "color-mix(in srgb,var(--ink) 5%,#fff)", "--soft-2": "color-mix(in srgb,var(--ink) 11%,#fff)",
        "--radius": "0px",
        "--s-background": b["background"], "--s-surface": b["surface"], "--s-text": b["text"],
        "--s-text-2": "color-mix(in srgb,var(--s-text) 85%,var(--s-surface))", "--s-muted": b["muted"],
        "--s-border": b["border"], "--s-border-soft": "color-mix(in srgb,var(--s-border) 60%,var(--s-surface))",
        "--s-soft": "color-mix(in srgb,var(--s-text) 5%,var(--s-surface))",
        "--s-soft-2": "color-mix(in srgb,var(--s-text) 11%,var(--s-surface))",
        "--s-radius": b["radius"], "--s-radius-phone": b["radius_phone"],
        "--s-primary-text": tone("--primary", 45, 70), "--s-feature-text": tone("--feature", 60, 55),
        "--s-success-text": tone("--success", 55, 60), "--s-warning-text": tone("--warning", 45, 70),
        "--s-danger-text": tone("--danger", 60, 55),
    }
    return ":root{" + ";".join(f"{k}:{v}" for k, v in root.items()) + "}\n"


def load_spec(work_dir):
    path = os.path.join(work_dir, "spec.py")
    data = runpy.run_path(path)
    spec = {k: v for k, v in data.items() if k.isupper()}
    spec["_dir"] = os.path.abspath(work_dir)
    spec["_brand"] = brand_tokens(spec)
    return spec


def helmet(spec):
    """The exact <helmet> every board carries: the product's fonts, its tokens, then the kit."""
    b = spec["_brand"]
    css = css_vars(b) + open(os.path.join(HERE, "kit.css"), encoding="utf-8").read()
    families = [b["font_sans"] + ":wght@400;500;600;700"]
    if b["font_display"] != b["font_sans"]:
        families.append(b["font_display"])
    query = "&amp;".join("family=" + f.replace(" ", "+") for f in families)
    fonts = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{query}&amp;display=swap">'
    return f"<helmet>\n{fonts}\n<style>\n{css}</style>\n</helmet>"


LOCAL_CSS = "/* board-local */"


def with_local_css(hel, css):
    """The kit helmet with a board's own rules appended after the marker, inside the same <style>."""
    if not css.strip():
        return hel
    return hel.replace("</style>\n</helmet>", f"{LOCAL_CSS}\n{css.strip()}\n</style>\n</helmet>")


def restyle(spec, path):
    """Swap a drawn board's helmet for the current kit, keeping its board-local CSS. Returns True if changed."""
    s = open(path, encoding="utf-8").read()
    start, end = s.find("<helmet>"), s.find("</helmet>")
    if start < 0 or end < 0:
        return False
    old = s[start:end + len("</helmet>")]
    local = old.split(LOCAL_CSS, 1)[1].rsplit("</style>", 1)[0] if LOCAL_CSS in old else ""
    new = with_local_css(helmet(spec), local)
    if new == old:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(s[:start] + new + s[end + len("</helmet>"):])
    return True


def page(spec, title, w, h, inner, root_style="", extra_css=""):
    hel = with_local_css(helmet(spec), extra_css)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{E(title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
{hel}
<div class="board" style="width: {w}px; height: {h}px; {root_style}">
{inner}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
"""


def project_dir(spec):
    return os.path.join(spec["_dir"], "root", "project")


def write_board(spec, name, content):
    out = project_dir(spec)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        f.write(content)


def fitted_heights(spec):
    path = os.path.join(spec["_dir"], "heights.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def round20(n):
    return int(-(-n // 20) * 20)


def header(eyebrow, title, lead, size=52, lead_w=960):
    return f"""<header style="display: flex; flex-direction: column; gap: 12px;">
  <div class="eyebrow">{E(eyebrow)}</div>
  <h1 class="serif" style="font-size: {size}px; line-height: 1.05;">{E(title)}</h1>
  <p style="font-size: 18px; line-height: 1.5; color: var(--ink-2); max-width: {lead_w}px;">{lead}</p>
</header>"""


def surface_chip(spec, surface_id):
    s = surface(spec, surface_id)
    return f'<span class="chip"><span class="dot" style="background: {s["color"]};"></span>{E(s["name"])}</span>'


def surface(spec, surface_id):
    for s in spec["SURFACES"]:
        if s["id"] == surface_id:
            return s
    raise KeyError(f"unknown surface {surface_id!r}")


def role(spec, role_id):
    for r in spec["ROLES"]:
        if r["id"] == role_id:
            return r
    raise KeyError(f"unknown role {role_id!r}")


def screen_file(screen):
    return f"{screen['id']}-{screen['slug']}.dc.html"


def all_stories(spec):
    return [s for st in spec["STAGES"] for s in st["stories"]]


def stage_points(stage):
    return sum(SIZE_PTS[s["size"]] for s in stage["stories"])


def lines(text, per_line):
    return max(1, -(-len(text) // per_line))


CHECK_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="flex: none; margin-top: 2px;" aria-hidden="true"><path d="M20 6L9 17l-5-5"></path></svg>'
