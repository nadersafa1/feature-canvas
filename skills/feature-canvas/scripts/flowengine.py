"""Lane-based flow diagrams: every card, arrow segment and label is its own placed element.

A spec is {"eyebrow", "title", "lead", "lanes": [{"tag", "title", "nodes", "edges"}], "footer"?}.
node: (id, row, col, kind, title, refs?)  kind: step | decision | system | push | end | state
edge: (from, to) | (from, to, label) | (from, to, label, dashed)
"""
from common import E, page, round20

LINE = "var(--muted)"
FLOW_W = 1640


class Flow:
    def __init__(self, card_w=240, card_h=96, pitch_x=304, pitch_y=184, x0=64):
        self.cw, self.ch, self.px, self.py, self.x0 = card_w, card_h, pitch_x, pitch_y, x0
        self.marker = 0
        self.bg, self.arrows, self.cards, self.labels = [], [], [], []
        self.nodes = {}

    def place(self, nid, lane_top, row, col, kind):
        cx = self.x0 + col * self.px + self.cw // 2
        cy = lane_top + 72 + row * self.py + self.ch // 2
        h = self.ch + 16 if kind == "decision" else self.ch - 16 if kind == "end" else self.ch
        self.nodes[nid] = {"cx": cx, "cy": cy, "w": self.cw, "h": h, "kind": kind}

    def seg(self, x1, y1, x2, y2, head, dashed=False):
        dash = " stroke-dasharray: 6 6;" if dashed else ""
        common = f"position: absolute; overflow: visible; fill: none; stroke: {LINE}; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;{dash}"
        defs, mk = "", ""
        if head:
            self.marker += 1
            mid = f"dc-arrow-head-filled-{self.marker}"
            defs = f'<defs><marker id="{mid}" orient="auto" markerWidth="5" markerHeight="5" refX="2" refY="2" overflow="visible"><path d="M0 0 L4 2 L0 4 Z" fill="{LINE}" stroke="none" style="stroke: none; fill: {LINE}; fill: context-stroke"></path></marker></defs>'
            mk = f' marker-end="url(#{mid})"'
        h = 4 if head else 0
        if y1 == y2:
            n = max(1, abs(x2 - x1))
            d = f"M 0 4 L {n - h} 4" if x2 > x1 else f"M {n} 4 L {h} 4"
            box = f'width="{n}" height="8" viewBox="0 0 {n} 8"'
            pos = f"left: {min(x1, x2)}px; top: {y1 - 4}px; width: {n}px; height: 8px;"
        else:
            n = max(1, abs(y2 - y1))
            d = f"M 4 0 L 4 {n - h}" if y2 > y1 else f"M 4 {n} L 4 {h}"
            box = f'width="8" height="{n}" viewBox="0 0 8 {n}"'
            pos = f"left: {x1 - 4}px; top: {min(y1, y2)}px; width: 8px; height: {n}px;"
        self.arrows.append(f'<svg {box} preserveAspectRatio="none" aria-hidden="true" style="{pos} {common}">{defs}<path d="{d}"{mk}></path></svg>')

    def path(self, pts, dashed=False):
        for k in range(len(pts) - 1):
            last = k == len(pts) - 2
            (x1, y1), (x2, y2) = pts[k], pts[k + 1]
            if last:  # stop 1px short of the target edge
                if y1 == y2:
                    x2 = x2 - 1 if x2 > x1 else x2 + 1
                else:
                    y2 = y2 - 1 if y2 > y1 else y2 + 1
            self.seg(x1, y1, x2, y2, last, dashed)

    def side_label(self, x, y, text):
        self.labels.append(f'<div style="position: absolute; left: {x}px; top: {y}px; font-size: 13px; line-height: 16px; font-weight: 600; color: var(--ink-2);">{E(text)}</div>')

    def centre_label(self, x, y, text):
        w = max(28, 8 * len(text) + 8)
        self.labels.append(f'<div style="position: absolute; left: {x - w // 2}px; top: {y}px; width: {w}px; text-align: center; font-size: 13px; line-height: 16px; font-weight: 600; color: var(--ink-2);">{E(text)}</div>')

    def edge(self, a, b, text=None, dashed=False):
        s, t = self.nodes[a], self.nodes[b]
        sl, sr, st, sb = s["cx"] - s["w"] // 2, s["cx"] + s["w"] // 2, s["cy"] - s["h"] // 2, s["cy"] + s["h"] // 2
        tl, tr, tt, tb = t["cx"] - t["w"] // 2, t["cx"] + t["w"] // 2, t["cy"] - t["h"] // 2, t["cy"] + t["h"] // 2
        if s["cy"] == t["cy"]:
            pts = [(sr, s["cy"]), (tl, t["cy"])] if t["cx"] > s["cx"] else [(sl, s["cy"]), (tr, t["cy"])]
            self.path(pts, dashed)
            if text:
                self.centre_label((pts[0][0] + pts[1][0]) // 2, s["cy"] - 28, text)
        elif s["cx"] == t["cx"]:
            pts = [(s["cx"], sb), (t["cx"], tt)] if t["cy"] > s["cy"] else [(s["cx"], st), (t["cx"], tb)]
            self.path(pts, dashed)
            if text:
                self.side_label(s["cx"] + 12, (pts[0][1] + pts[1][1]) // 2 - 8, text)
        elif t["cy"] > s["cy"]:
            ymid = s["cy"] + self.py // 2
            self.path([(s["cx"], sb), (s["cx"], ymid), (t["cx"], ymid), (t["cx"], tt)], dashed)
            if text:
                self.side_label(s["cx"] + 12, (sb + ymid) // 2 - 8, text)
        else:  # target above: along the source's row, then up into the target's bottom
            x_edge = sr if t["cx"] > s["cx"] else sl
            self.path([(x_edge, s["cy"]), (t["cx"], s["cy"]), (t["cx"], tb)], dashed)
            if text:
                self.centre_label((x_edge + t["cx"]) // 2, s["cy"] - 28, text)

    def card(self, nid, title, refs=""):
        n = self.nodes[nid]
        left, top = n["cx"] - n["w"] // 2, n["cy"] - n["h"] // 2
        refs_html = f'<br><span style="font-size: 12px; font-weight: 600; color: var(--muted);">{E(refs)}</span>' if refs else ""
        base = f"position: absolute; left: {left}px; top: {top}px; width: {n['w']}px; height: {n['h']}px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 14px; line-height: 18px; color: var(--ink);"
        kind = n["kind"]
        body = f"<span>{E(title)}{refs_html}</span>"
        if kind == "decision":
            style = base + " padding: 10px 46px; background: color-mix(in srgb,var(--warning) 20%,var(--surface)); clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); font-weight: 600; font-size: 13px; line-height: 16px;"
            body = E(title)
        elif kind == "end":
            style = base + f" padding: 8px 16px; background: var(--primary); color: var(--on-primary); border-radius: 32px; font-weight: 700;"
        elif kind == "system":
            style = base + " padding: 10px 14px; border: 2px dashed var(--muted); font-style: italic;"
        elif kind == "push":
            style = base + f" padding: 10px 14px; background: color-mix(in srgb,var(--feature) 12%,var(--surface)); border: 1px solid color-mix(in srgb,var(--feature) 40%,var(--surface));"
        elif kind == "state":
            style = base + f" padding: 10px 14px; background: var(--surface); border: 2px solid var(--ink); border-radius: 48px; font-weight: 700;"
        elif kind == "step":
            style = base + " padding: 10px 14px; background: var(--surface); border: 1px solid var(--line);"
            body = f"<span><b>{E(title)}</b>{refs_html}</span>"
        else:
            raise ValueError(f"unknown node kind {kind!r} on {nid}")
        self.cards.append(f'<div style="{style}">{body}</div>')

    def lane(self, top, height, title, tag):
        self.bg.append(f'<div style="position: absolute; left: 32px; top: {top}px; width: {FLOW_W - 64}px; height: {height}px; background: var(--soft); border: 1px solid var(--line);"></div>')
        self.labels.append(f'<div style="position: absolute; left: 48px; top: {top + 16}px; display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 700;"><span class="chip chip-ink">{E(tag)}</span><span>{E(title)}</span></div>')


def legend_html(top, items):
    swatch = {
        "step": "background: var(--surface); border: 1px solid var(--line);",
        "decision": "background: color-mix(in srgb,var(--warning) 20%,var(--surface)); clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%);",
        "system": "border: 2px dashed var(--muted);",
        "push": f"background: color-mix(in srgb,var(--feature) 12%,var(--surface)); border: 1px solid color-mix(in srgb,var(--feature) 40%,var(--surface));",
        "end": f"background: var(--primary); border-radius: 10px;",
        "state": f"background: var(--surface); border: 2px solid var(--ink); border-radius: 10px;",
    }
    spans = "".join(
        f'<span style="display: inline-flex; align-items: center; gap: 8px; font-size: 13px;"><span style="width: 26px; height: 18px; box-sizing: border-box; {swatch[k]}"></span>{E(t)}</span>'
        for k, t in items
    )
    return f'<div style="position: absolute; left: 64px; top: {top}px; display: flex; gap: 24px; flex-wrap: wrap; align-items: center;">{spans}</div>'


def render(spec, flow, legend, **flow_kw):
    """Returns (html, height) for one flow board."""
    f = Flow(**flow_kw)
    hdr = f"""<div style="position: absolute; left: 64px; top: 64px; width: 1340px; display: flex; flex-direction: column; gap: 10px;">
  <div class="eyebrow">{E(flow['eyebrow'])}</div>
  <h1 class="serif" style="font-size: 48px; line-height: 1.05;">{E(flow['title'])}</h1>
  <p style="font-size: 17px; line-height: 1.5; color: var(--ink-2); max-width: 1180px;">{E(flow['lead'])}</p>
</div>"""
    y = 300
    for ln in flow["lanes"]:
        rows = 1 + max(n[1] for n in ln["nodes"])
        height = 72 + rows * f.py - (f.py - f.ch) + 56
        f.lane(y, height, ln["title"], ln["tag"])
        for nid, row, col, kind, *_ in ln["nodes"]:
            f.place(nid, y, row, col, kind)
        for nid, row, col, kind, title, *refs in ln["nodes"]:
            f.card(nid, title, refs[0] if refs else "")
        for e in ln["edges"]:
            a, b, *rest = e
            f.edge(a, b, rest[0] if rest else None, len(rest) > 1 and rest[1])
        y += height + 32
    footer = ""
    total = y
    if flow.get("footer"):
        footer = f'<div style="position: absolute; left: 64px; top: {y}px; width: 1500px; font-size: 13px; line-height: 1.5; color: var(--muted);">{E(flow["footer"])}</div>'
        total += 40
    inner = "".join(f.bg) + "".join(f.arrows) + "".join(f.cards) + "".join(f.labels) + hdr + legend_html(232, legend) + footer
    h = round20(total)
    return page(spec, flow["title"], FLOW_W, h, inner, root_style="display: block; padding: 0;"), h
