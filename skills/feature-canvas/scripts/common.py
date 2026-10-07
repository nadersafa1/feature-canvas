"""Shared helpers: loading the spec, the brand-filled kit, and the board page shell."""
import html
import json
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape

DEFAULT_BRAND = {
    "ink": "#0E2F3E",      # text, dark fills, the Web surface
    "accent": "#C4D433",   # primary buttons, outcomes, live chips; must carry ink text
    "feature": "#7A45E6",  # the one colour that marks the new feature on existing screens
    "ground": "#E9E7E0",   # the canvas behind every board
    "serif": "Hedvig Letters Serif",
    "sans": "Inter",
}

SIZE_PTS = {"S": 1, "M": 2, "L": 3}


def mix(hex_a, hex_b, t):
    """Blend hex_a towards hex_b by t (0..1)."""
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def brand_tokens(spec):
    b = {**DEFAULT_BRAND, **spec.get("BRAND", {})}
    b["accent_soft"] = mix(b["accent"], "#FFFFFF", 0.82)
    b["accent_line"] = mix(b["accent"], "#FFFFFF", 0.45)
    b["accent_ink"] = mix(b["accent"], "#000000", 0.6)
    b["feature_soft"] = mix(b["feature"], "#FFFFFF", 0.88)
    b["feature_line"] = mix(b["feature"], "#FFFFFF", 0.6)
    b["feature_ink"] = mix(b["feature"], "#000000", 0.4)
    return b


def load_spec(work_dir):
    path = os.path.join(work_dir, "spec.py")
    data = runpy.run_path(path)
    spec = {k: v for k, v in data.items() if k.isupper()}
    spec["_dir"] = os.path.abspath(work_dir)
    spec["_brand"] = brand_tokens(spec)
    return spec


def helmet(spec):
    """The exact <helmet> every board carries: fonts plus the brand-filled kit."""
    b = spec["_brand"]
    css = open(os.path.join(HERE, "kit.css"), encoding="utf-8").read()
    for key, value in b.items():
        css = css.replace(f"@@{key}@@", value)
    fam = lambda name, spec_: name.replace(" ", "+") + spec_  # noqa: E731
    fonts = (
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family='
        + fam(b["serif"], "")
        + "&amp;family="
        + fam(b["sans"], ":wght@400;500;600;700")
        + '&amp;display=swap">'
    )
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
  <p style="font-size: 18px; line-height: 1.5; color: #33454E; max-width: {lead_w}px;">{lead}</p>
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
