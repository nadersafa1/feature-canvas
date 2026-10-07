"""Build every generated board, the canvas index, the static bundle and STORIES.md from spec.py.

usage: python3 build.py WORK_DIR

Writes into WORK_DIR:
  root/project/*.dc.html   generated boards (cover, overview, flows, roadmap, stages); wireframes are never touched
  root/project/canvas.json the Design-canvas index: pages, rows, titles, sizes (wireframes included once they exist)
  helmet.html              the exact <helmet> every wireframe board must carry
  bundle.html              one static page with every board, for viewing anywhere and measuring heights
  STORIES.md               stages, stories, acceptance and decisions as Markdown, for the build that follows
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

from common import (
    CHECK_SVG, E, all_stories, fitted_heights, header, helmet, lines, load_spec, page,
    project_dir, role, round20, screen_file, stage_points, surface, surface_chip, write_board,
)
from common import restyle
from flowengine import render as render_flow

COL = "flex-direction: column; gap: 28px; padding: 48px;"
W = 1640


def article(word):
    return "an" if word[:1].lower() in "aeiou" else "a"


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "", text.title())[:24] or "Board"


def decision_status_counts(spec):
    counts = {"agreed": 0, "assumed": 0, "open": 0}
    for d in spec.get("DECISIONS", []):
        counts[d["status"]] += 1
    return counts


# ── Overview ─────────────────────────────────────────────────────────────────

def cover(spec):
    c = spec["CANVAS"]
    stories = all_stories(spec)
    counts = decision_status_counts(spec)
    stats = [
        (len(spec["STAGES"]), "stages"), (len(stories), "user stories"), (len(spec.get("SCREENS", [])), "screens"),
        (len(spec.get("FLOWS", [])), "user flows"), (len(spec.get("DECISIONS", [])), "decisions"),
    ]
    stat_html = "".join(f'<div><div class="serif tnum" style="font-size: 56px; line-height: 1;">{n}</div><div class="muted" style="font-size: 14px; margin-top: 6px;">{E(t)}</div></div>' for n, t in stats)
    open_line = (f'<span class="chip chip-bad">{counts["open"]} open decisions</span>' if counts["open"]
                 else '<span class="chip chip-ok">No open decisions</span>')
    people = "".join(
        f"""<div class="card" style="padding: 18px; display: flex; flex-direction: column; gap: 8px;">
  <div style="display: flex; align-items: center; gap: 10px;"><span class="av">{E(''.join(p[0] for p in r['persona'].split()[:2]))}</span><div><div class="b" style="font-size: 16px;">{E(r['persona'])}</div><div class="muted" style="font-size: 13px;">{E(r['name'])}</div></div></div>
  <p style="font-size: 13.5px; line-height: 1.5; color: var(--ink-2);">{E(r['does'])}</p>
  <div style="display: flex; gap: 4px; flex-wrap: wrap;">{''.join(surface_chip(spec, s) for s in r['surfaces'])}</div>
</div>""" for r in spec["ROLES"])
    pages = "".join(
        f'<li style="display: flex; gap: 12px; font-size: 14px; line-height: 1.5;"><span class="chip chip-ink" style="flex: none;">{E(name)}</span><span>{E(what)}</span></li>'
        for name, what in canvas_page_guide(spec))
    inner = header(f"{c['product']} · {c['feature']}", c["title"], E(c["lead"]), 72, 1100) + f"""
<section style="display: flex; gap: 72px; align-items: flex-end;">{stat_html}<div style="flex-grow: 1;"></div>{open_line}</section>
<div class="hr"></div>
<section style="display: flex; flex-direction: column; gap: 14px;"><div class="eyebrow">Who it is for · the sample world, now = {E(c['now'])}</div>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px;">{people}</div></section>
<section class="card" style="padding: 24px; display: flex; flex-direction: column; gap: 12px;"><div class="eyebrow">How to read this canvas</div><ul style="display: flex; flex-direction: column; gap: 10px;">{pages}</ul>
<p class="help">Every step in a flow names its screen and story (W01 · {E(first_story_id(spec))}); every wireframe lists its stories; every story card lists its decisions (#n).</p></section>"""
    role_rows = -(-len(spec["ROLES"]) // 4)
    h = 48 + 330 + 28 + 120 + 28 + 1 + 28 + 30 + role_rows * 200 + 28 + 110 + 36 * len(canvas_page_guide(spec)) + 48
    return "Main.dc.html", "Cover", inner, h


def first_story_id(spec):
    stories = all_stories(spec)
    return stories[0]["id"] if stories else "A1.1"


def canvas_page_guide(spec):
    guide = [("Overview", "The model, who can do what, journeys, states and every decision taken.")]
    if spec.get("FLOWS"):
        guide.append(("User flows", "One board per role: each lane is a job they do, step by step."))
    for name, ids in surface_pages(spec):
        guide.append((name, f"Annotated wireframes: {ids[0]}–{ids[-1]}." if len(ids) > 1 else f"Annotated wireframe {ids[0]}."))
    guide.append(("User stories", "The roadmap, then one board per stage with its stories and acceptance points."))
    return guide


def surface_pages(spec):
    """[(page name, [screen ids])] in first-seen order."""
    pages = {}
    for sc in spec.get("SCREENS", []):
        pages.setdefault(surface(spec, sc["surface"])["page"], []).append(sc["id"])
    return list(pages.items())


def model(spec):
    cards = "".join(
        f"""<article class="card" style="padding: 22px; display: flex; flex-direction: column; gap: 12px;">
  <h2 class="serif" style="font-size: 30px; line-height: 1.1;">{E(e['name'])}</h2>
  <p style="font-size: 15px; line-height: 1.5; color: var(--ink-2);">{E(e['what'])}</p>
  <ul style="display: flex; flex-direction: column; gap: 8px;">{''.join(f'<li style="display: flex; gap: 8px; font-size: 13.5px; line-height: 1.45;">{CHECK_SVG}<span>{E(x)}</span></li>' for x in e.get('facts', []))}</ul>
  {''.join(f'<div style="display: flex; gap: 8px; font-size: 13.5px; font-weight: 600;"><span class="muted">→</span><span>{E(x)}</span></div>' for x in e.get('links', []))}
</article>""" for e in spec["ENTITIES"])
    inner = header("Overview · Model", spec["CANVAS"].get("model_title", "How it is built"), E(spec["CANVAS"].get("model_lead", "The records the feature adds, what each one means, and how they connect.")), 52) + \
        f'<section style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; align-items: start;">{cards}</section>'
    rows = [spec["ENTITIES"][i:i + 3] for i in range(0, len(spec["ENTITIES"]), 3)]
    grid = sum(max(140 + 26 * lines(e["what"], 46) + sum(22 * lines(x, 44) + 8 for x in e.get("facts", [])) + 26 * len(e.get("links", [])) for e in r) for r in rows) + 24 * (len(rows) - 1)
    return "O1-Model.dc.html", "Model", inner, 48 + 200 + 28 + grid + 48


def permissions(spec):
    roles = spec["ROLES"]
    head = "".join(f'<th style="width: {int(900 / len(roles))}px;">{E(r["name"])}</th>' for r in roles)
    body, n_rows = [], 0
    for group, rows in spec["PERMISSIONS"]:
        body.append(f'<tr><td colspan="{len(roles) + 1}" class="b" style="background: var(--soft); font-size: 12px; letter-spacing: .06em; text-transform: uppercase;">{E(group)}</td></tr>')
        n_rows += 1
        for action, cells in rows:
            tds = "".join(perm_cell(cells.get(r["id"], "—")) for r in roles)
            body.append(f"<tr><td>{E(action)}</td>{tds}</tr>")
            n_rows += 1
    inner = header("Overview · Permissions", "Who can do what", "Every action the feature adds, by role. A dash means never; anything else names the limit.", 52) + \
        f'<div class="card"><table><thead><tr><th>Action</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    return "O2-Permissions.dc.html", "Who can do what", inner, 48 + 200 + 28 + 40 + n_rows * 44 + 48


def perm_cell(value):
    if value == "Yes":
        return '<td><span class="chip chip-ok">Yes</span></td>'
    if value in ("—", "No", ""):
        return '<td class="muted">—</td>'
    return f'<td style="font-size: 12.5px;">{E(value)}</td>'


def journeys(spec):
    out = []
    for j in spec["JOURNEYS"]:
        r = role(spec, j["role"])
        steps = []
        for k, (text, ref) in enumerate(j["steps"]):
            if k:
                steps.append('<span class="muted" style="font-size: 18px; align-self: center;">→</span>')
            ref_html = f'<span class="muted" style="font-size: 11px; font-weight: 600;">{E(ref)}</span>' if ref else ""
            steps.append(f'<div class="card" style="padding: 10px 12px; display: flex; flex-direction: column; gap: 4px; max-width: 220px;"><span style="font-size: 13.5px; font-weight: 600; line-height: 1.35;">{E(text)}</span>{ref_html}</div>')
        out.append(f"""<section style="display: flex; flex-direction: column; gap: 10px;">
  <div style="display: flex; align-items: center; gap: 10px;"><span class="chip chip-ink">{E(r['name'])}</span><span class="b" style="font-size: 17px;">{E(j['title'])}</span><span class="muted" style="font-size: 13px;">{E(r['persona'])}</span></div>
  <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: stretch;">{''.join(steps)}</div>
</section>""")
    inner = header("Overview · Journeys", "Journeys", "The main path each person takes, end to end. The flows page breaks every one of them into steps and decisions.", 52) + "".join(out)
    h = 48 + 200 + sum(28 + 40 + 90 * max(1, -(-len(j["steps"]) // 6)) for j in spec["JOURNEYS"]) + 48
    return "O3-Journeys.dc.html", "Journeys", inner, h


def decisions(spec):
    groups = [
        ("agreed", "Agreed", "chip chip-ink", "Settled with the product owner."),
        ("assumed", "Assumed", "chip chip-feat", "Calls taken while writing this canvas; each stands unless overridden."),
        ("open", "Open", "chip chip-bad", "Still to decide. Stories that depend on these are not ready to build."),
    ]
    cols = []
    for status, title, cls, lead in groups:
        items = [d for d in spec.get("DECISIONS", []) if d["status"] == status]
        lis = "".join(
            f'<li style="display: flex; gap: 8px; font-size: 13.5px; line-height: 1.5;"><span class="{cls} tnum" style="flex: none;">#{d["n"]}</span><span><b>{E(d["topic"])}.</b> {E(d["text"])}</span></li>'
            for d in sorted(items, key=lambda d: d["n"])) or '<li class="muted" style="font-size: 13.5px;">None.</li>'
        cols.append(f'<div class="card" style="padding: 20px; display: flex; flex-direction: column; gap: 10px;"><div class="eyebrow">{title} · {len(items)}</div><p class="help">{lead}</p><ul style="display: flex; flex-direction: column; gap: 10px;">{lis}</ul></div>')
    counts = decision_status_counts(spec)
    lead = f"{counts['agreed']} agreed, {counts['assumed']} assumed, {counts['open']} open. Stories and wireframes cite these as #n."
    inner = header("Overview · Decisions", "Decisions log", E(lead), 52) + \
        f'<section style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; align-items: start;">{"".join(cols)}</section>'
    tallest = max((sum(22 * lines(d["topic"] + d["text"], 52) + 10 for d in spec.get("DECISIONS", []) if d["status"] == s) for s, *_ in groups), default=0)
    return "O5-Decisions.dc.html", "Decisions log", inner, 48 + 200 + 28 + 110 + tallest + 48


# ── Stories ──────────────────────────────────────────────────────────────────

def story_card_h(s):
    sentence = f"As a {s['as']}, I want {s['want']}, so that {s['so']}."
    h = 18 + 22 + 10 + 22 * lines(s["title"], 44) + 10 + 21 * lines(sentence, 60)
    if s.get("accept"):
        h += 10 + sum(19 * lines(b, 58) + 6 for b in s["accept"])
    return h + 20


def story_card(spec, s):
    who = role(spec, s["as"])["name"].lower() if any(r["id"] == s["as"] for r in spec["ROLES"]) else s["as"]
    chips = "".join(surface_chip(spec, x) for x in s["surfaces"])
    dec = "".join(f'<span class="chip chip-muted tnum">#{n}</span>' for n in s.get("decisions", []))
    accept = "".join(f'<li style="display: flex; gap: 8px; font-size: 12.5px; line-height: 1.45;">{CHECK_SVG}<span>{E(b)}</span></li>' for b in s.get("accept", []))
    return f"""<article class="card" style="padding: 18px 18px 16px; display: flex; flex-direction: column; gap: 10px;">
  <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;"><span class="chip chip-ink">{E(s['id'])}</span><span class="chip chip-muted" title="Relative effort">{s['size']}</span>{dec}<span style="flex-grow: 1;"></span>{chips}</div>
  <h3 style="font-size: 17px; line-height: 1.25; font-weight: 700;">{E(s['title'])}</h3>
  <p style="font-size: 13.5px; line-height: 1.5; color: var(--ink-2);">As {article(who)} <b>{E(who)}</b>, I want {E(s['want'])}, so that {E(s['so'])}.</p>
  {f'<ul style="display: flex; flex-direction: column; gap: 6px;">{accept}</ul>' if accept else ''}
</article>"""


def screens_for_stage(spec, stage):
    ids = {s["id"] for s in stage["stories"]}
    return [sc["id"] for sc in spec.get("SCREENS", []) if ids & set(sc["stories"])]


def stage_board(spec, index, stage):
    stories = stage["stories"]
    building = [s for s in spec["STAGES"] if not s.get("later")]
    order = f"Build order {building.index(stage) + 1} of {len(building)}" if not stage.get("later") else "Parking lot"
    after = ", ".join(stage.get("after", [])) or "Nothing. Ships on its own."
    screens = " · ".join(screens_for_stage(spec, stage)) or "None yet"
    head = f"""<header style="display: flex; gap: 40px; align-items: flex-start;">
  <div style="flex-grow: 1; display: flex; flex-direction: column; gap: 12px;">
    <div class="eyebrow">User stories · {order}</div>
    <h1 class="serif" style="font-size: 52px; line-height: 1.05;">{E(stage['id'])} · {E(stage['name'])}</h1>
    <p style="font-size: 18px; line-height: 1.5; color: var(--ink-2); max-width: 960px;">{E(stage['tagline'])}</p>
  </div>
  <aside class="card" style="width: 460px; flex: none; padding: 18px 20px; display: flex; flex-direction: column; gap: 12px;">
    <div><div class="eyebrow">What it gives</div><p style="font-size: 14px; line-height: 1.45; margin-top: 4px;">{E(stage['gets'])}</p></div>
    <div class="hr"></div>
    <div><div class="eyebrow">Needs first</div><p style="font-size: 14px; margin-top: 4px;">{E(after)}</p></div>
    <div class="hr"></div>
    <div><div class="eyebrow">Screens</div><p style="font-size: 14px; margin-top: 4px;">{E(screens)}</p></div>
    <div class="hr"></div>
    <div style="display: flex; gap: 28px; align-items: baseline;">
      <div><span class="serif tnum" style="font-size: 30px;">{len(stories)}</span> <span class="muted" style="font-size: 13px;">stories</span></div>
      <div><span class="serif tnum" style="font-size: 30px;">{stage_points(stage)}</span> <span class="muted" style="font-size: 13px;">effort points (S 1 · M 2 · L 3)</span></div>
    </div>
  </aside>
</header>"""
    grid = '<section style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; align-items: start;">' + "".join(story_card(spec, s) for s in stories) + "</section>"
    foot = '<div class="muted" style="font-size: 13px;">Surfaces: ' + " ".join(surface_chip(spec, s["id"]) for s in spec["SURFACES"]) + " · Stories are in build order. #n = decision number in the Decisions log.</div>"
    rows = [stories[k:k + 3] for k in range(0, len(stories), 3)]
    grid_h = sum(max(story_card_h(s) for s in r) for r in rows) + 20 * (len(rows) - 1) if rows else 0
    aside_h = 36 + 72 + 3 + 20 + 22 * lines(stage["gets"], 48) + 20 + 22 * lines(after, 50) + 20 + 22 * lines(screens, 50) + 40
    h = 48 + max(230, aside_h) + 28 + grid_h + 28 + 30 + 48
    return f"US{index}-{stage['id']}.dc.html", f"{stage['id']} · {stage['name']}", head + grid + foot, h


def roadmap(spec):
    stages = spec["STAGES"]
    by_id = {s["id"]: s for s in stages}
    depth = {}

    def d(sid):
        if sid not in depth:
            depth[sid] = 0 if not by_id[sid].get("after") else 1 + max(d(x) for x in by_id[sid]["after"])
        return depth[sid]

    tracks = []
    for s in stages:
        t = "Later" if s.get("later") else s.get("track", "Main")
        if t not in tracks:
            tracks.append(t)
    if "Later" in tracks:
        tracks.remove("Later")
        tracks.append("Later")
    bw, bh, px, py, top = 250, 140, 330, 200, 40
    taken, pos = set(), {}
    for s in stages:
        row = tracks.index("Later" if s.get("later") else s.get("track", "Main"))
        col = d(s["id"])
        while (row, col) in taken:
            col += 1
        taken.add((row, col))
        pos[s["id"]] = (col * px, top + row * py)
    building = [s for s in stages if not s.get("later")]
    boxes, lines_ = [], []
    for s in stages:
        x, y = pos[s["id"]]
        later = s.get("later")
        bg, border = ("transparent", "2px dashed var(--muted)") if later else ("var(--surface)", "1px solid var(--line)")
        mk = "" if later else f'<span class="mk" style="background: var(--primary); color: var(--on-primary); box-shadow: none; width: 24px; height: 24px; font-size: 12px;">{building.index(s) + 1}</span>'
        boxes.append(f"""<div style="position: absolute; left: {x}px; top: {y}px; width: {bw}px; height: {bh}px; box-sizing: border-box; padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; background: {bg}; border: {border};">
  <div style="display: flex; align-items: center; gap: 8px;">{mk}<span class="b" style="font-size: 15px;">{E(s['id'])}</span><span style="flex-grow: 1;"></span><span class="chip">{len(s['stories'])} stories · {stage_points(s)} pts</span></div>
  <div style="font-size: 16px; font-weight: 700; line-height: 1.25;">{E(s['name'])}</div>
  <div style="font-size: 12px; line-height: 1.4; color: var(--muted);">{E(s['tagline'])}</div>
</div>""")
        for dep in s.get("after", []):
            lines_.append(route(pos[dep], pos[s["id"]], bw, bh))
    track_labels = "".join(
        f'<div class="eyebrow" style="position: absolute; left: 0; top: {top + i * py - 26}px;">{E(t)}</div>' for i, t in enumerate(tracks))
    gw = max(x for x, _ in pos.values()) + bw
    gh = top + len(tracks) * py
    graph = f'<div style="position: relative; width: {gw}px; height: {gh}px; flex: none;">{track_labels}{"".join(lines_)}{"".join(boxes)}</div>'
    ms = ""
    if spec.get("MILESTONES"):
        ms = '<section style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px;">' + "".join(
            f"""<div class="card" style="padding: 18px; display: flex; flex-direction: column; gap: 8px;">
  <div style="display: flex; align-items: center; gap: 8px;"><span class="eyebrow">Milestone {i}</span><span style="flex-grow: 1;"></span><span class="chip chip-ink">{E(' + '.join(m['stages']))}</span></div>
  <div class="serif" style="font-size: 24px; line-height: 1.1;">{E(m['name'])}</div>
  <p style="font-size: 14px; line-height: 1.5; color: var(--ink-2);">{E(m['what'])}</p>
</div>""" for i, m in enumerate(spec["MILESTONES"], start=1)) + "</section>"
    rows = "".join(
        f'<tr><td class="tnum b">{building.index(s) + 1 if not s.get("later") else "—"}</td><td class="b">{E(s["id"])}</td><td>{E(s["name"])}</td><td class="tnum">{len(s["stories"])}</td><td class="tnum">{stage_points(s)}</td><td>{"".join(surface_chip(spec, x) for x in stage_surfaces(s))}</td><td>{E(", ".join(s.get("after", [])) or "—")}</td></tr>'
        for s in stages)
    n = sum(len(s["stories"]) for s in building)
    p = sum(stage_points(s) for s in building)
    table = f"""<div class="card"><table>
<thead><tr><th style="width: 60px;">Order</th><th style="width: 70px;">Stage</th><th>Name</th><th style="width: 80px;">Stories</th><th style="width: 90px;">Effort pts</th><th style="width: 340px;">Surfaces</th><th style="width: 220px;">Needs first</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="muted" style="padding: 12px 10px; font-size: 13px;"><b class="tnum" style="color: var(--ink);">{n} stories · {p} effort points</b> before the parking lot. Effort is relative (S 1, M 2, L 3): compare stages with it, never estimate time with it. Each stage ships on its own.</div></div>"""
    legend = f'<div style="display: flex; gap: 22px; flex-wrap: wrap; font-size: 13px;"><span style="display: inline-flex; align-items: center; gap: 8px;"><span class="mk" style="background: var(--primary); color: var(--on-primary); box-shadow: none;">1</span>Recommended build order</span><span style="display: inline-flex; align-items: center; gap: 8px;"><span style="width: 18px; height: 14px; border: 2px dashed var(--muted);"></span>Parking lot</span><span class="muted">Arrows: a stage needs the one it comes from.</span></div>'
    lead = spec["CANVAS"].get("roadmap_lead", "Every stage is deployable on its own. Rows are tracks; a stage sits to the right of everything it needs.")
    inner = header("User stories · Roadmap", "Build order and dependencies", E(lead), 56, 1100) + legend + graph + ms + table
    h = 48 + 210 + 28 + 24 + 28 + gh + (28 + 170 if ms else 0) + 28 + 40 + 44 * len(stages) + 50 + 48
    return "US0-Roadmap.dc.html", "Roadmap", inner, h


def stage_surfaces(stage):
    seen = []
    for s in stage["stories"]:
        for x in s["surfaces"]:
            if x not in seen:
                seen.append(x)
    return seen


def hline(x1, x2, y, color="var(--muted)"):
    return f'<div style="position: absolute; left: {min(x1, x2)}px; top: {y - 1}px; width: {abs(x2 - x1) + 2}px; height: 2px; background: {color};"></div>'


def vline(x, y1, y2, color="var(--muted)"):
    return f'<div style="position: absolute; left: {x - 1}px; top: {min(y1, y2)}px; width: 2px; height: {abs(y2 - y1) + 2}px; background: {color};"></div>'


def head_right(x, y):
    return f'<div style="position: absolute; left: {x - 9}px; top: {y - 6}px; width: 0; height: 0; border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-left: 9px solid var(--muted);"></div>'


def route(a, b, bw, bh):
    """Arrow from stage box a to stage box b, kept in the gutters between boxes."""
    (ax, ay), (bx, by) = a, b
    acy, bcy = ay + bh // 2, by + bh // 2
    if ay == by and bx - ax <= 330:
        return hline(ax + bw, bx - 2, acy) + head_right(bx, bcy)
    gx = bx - 40
    gy = ay + bh + 30 if by >= ay else ay - 30
    start_x = ax + bw // 2 + 30
    return (vline(start_x, ay + bh if by >= ay else ay, gy) + hline(start_x, gx, gy) + vline(gx, gy, bcy)
            + hline(gx, bx - 2, bcy) + head_right(bx, bcy))


# ── Layout, bundle and Markdown ─────────────────────────────────────────────

def board_size(path):
    s = open(path, encoding="utf-8").read()
    m = re.search(r'"\$preview":\{"width":(\d+),"height":(\d+)\}', s)
    return int(m.group(1)), int(m.group(2))


def layout(spec, titles):
    """Pages and rows for canvas.json: [(page id, page name, [(row title, [file names])])]."""
    proj = project_dir(spec)
    exists = lambda f: os.path.exists(os.path.join(proj, f))  # noqa: E731
    pages = []
    ov1 = [f for f in ("Main.dc.html", "O1-Model.dc.html", "O2-Permissions.dc.html") if exists(f)]
    ov2 = [f for f in ("O3-Journeys.dc.html", "O5-Decisions.dc.html", "O4-Lifecycles.dc.html") if exists(f)]
    pages.append(("overview", "Overview & model", [r for r in (("Overview", ov1), ("Journeys, states and decisions", ov2)) if r[1]]))
    flows = [flow_file(spec, f) for f in spec.get("FLOWS", [])]
    if flows:
        pages.append(("flows", "User flows", [(f"Flows {i + 1}–{min(i + 3, len(flows))}", flows[i:i + 3]) for i in range(0, len(flows), 3)]))
    rows_spec = spec.get("SCREEN_ROWS", {})
    for k, (page_name, ids) in enumerate(surface_pages(spec)):
        by_id = {sc["id"]: sc for sc in spec["SCREENS"]}
        kind = surface(spec, by_id[ids[0]]["surface"])["kind"]
        if page_name in rows_spec:
            rows = [(t, [screen_file(by_id[i]) for i in r]) for t, r in rows_spec[page_name]]
        else:
            per = 4 if kind == "web" else 6
            rows = [(f"{ids[i]}–{ids[min(i + per, len(ids)) - 1]}", [screen_file(by_id[x]) for x in ids[i:i + per]]) for i in range(0, len(ids), per)]
        rows = [(t, [f for f in r if exists(f)]) for t, r in rows]
        rows = [r for r in rows if r[1]]
        if rows:
            pages.append((f"screens{k + 1}", page_name, rows))
    st = ["US0-Roadmap.dc.html"] + [f"US{i}-{s['id']}.dc.html" for i, s in enumerate(spec["STAGES"], start=1)]
    pages.append(("stories", "User stories", [(f"Stories {i // 4 + 1}", st[i:i + 4]) for i in range(0, len(st), 4)]))
    return pages


def write_canvas_json(spec, pages, titles):
    proj = project_dir(spec)
    boards, order, notes = {}, [], {}
    for pid, _, rows in pages:
        y = 300
        for ri, (title, names) in enumerate(rows):
            x, row_h = 0, 0
            for n in names:
                w, h = board_size(os.path.join(proj, n))
                boards[n] = {"x": x, "y": y, "w": w, "h": h, "title": titles.get(n, n[:-8]), "page": pid}
                order.append(n)
                x += w + 80
                row_h = max(row_h, h)
            notes[f"{pid}-t{ri}"] = {"x": 0, "y": y - 280, "text": title, "kind": "title1", "maxW": min(8000, x - 80), "page": pid}
            y += row_h + 120 + 280
    path = os.path.join(proj, "canvas.json")
    created = {"v": 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if os.path.exists(path):  # keep the original creation stamp across rebuilds
        created = json.load(open(path, encoding="utf-8")).get("createdOnFiles", created)
    idx = {
        "v": 3, "createdOnFiles": created, "title": spec["CANVAS"]["title"],
        "launch": {"view": "canvas", "page": "overview"},
        "pages": [{"id": pid, "name": name} for pid, name, _ in pages],
        "boards": boards, "order": order, "notes": notes, "designSystems": [],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    return idx


def write_bundle(spec, pages, titles):
    proj = project_dir(spec)
    items = []
    for pid, pname, rows in pages:
        for row_title, names in rows:
            for n in names:
                s = open(os.path.join(proj, n), encoding="utf-8").read()
                hel = re.search(r"<helmet>(.*?)</helmet>", s, re.S).group(1)
                board = s.split("</helmet>", 1)[1].rsplit("</x-dc>", 1)[0]
                w, h = board_size(os.path.join(proj, n))
                doc = f'<!doctype html><html><head><meta charset="utf-8">{hel}</head><body>{board}</body></html>'
                items.append({"file": n, "title": titles.get(n, n), "page": pname, "row": row_title, "w": w, "h": h, "doc": doc})
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bundle_template.html"), encoding="utf-8").read()
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    out = tpl.replace("__TITLE__", E(spec["CANVAS"]["title"])).replace("__DATA__", data)
    with open(os.path.join(spec["_dir"], "bundle.html"), "w", encoding="utf-8") as f:
        f.write(out)


def write_markdown(spec):
    c = spec["CANVAS"]
    out = [f"# {c['title']}", "", c["lead"], "", f"Sample world: see WORLD.md. Now = {c['now']}.", ""]
    out += ["## Decisions", ""]
    for d in sorted(spec.get("DECISIONS", []), key=lambda d: d["n"]):
        out.append(f"- **#{d['n']} {d['topic']}** ({d['status']}). {d['text']}")
    screens = spec.get("SCREENS", [])
    for st in spec["STAGES"]:
        out += ["", f"## {st['id']} · {st['name']}{' (parking lot)' if st.get('later') else ''}", "", f"{st['tagline']}", "",
                f"- Gives: {st['gets']}", f"- Needs first: {', '.join(st.get('after', [])) or 'nothing'}",
                f"- Screens: {', '.join(screens_for_stage(spec, st)) or 'none'}", ""]
        for s in st["stories"]:
            who = role(spec, s["as"])["name"].lower() if any(r["id"] == s["as"] for r in spec["ROLES"]) else s["as"]
            dec = f" · decisions {', '.join('#' + str(n) for n in s['decisions'])}" if s.get("decisions") else ""
            out += [f"### {s['id']} {s['title']} ({s['size']} · {', '.join(surface(spec, x)['name'] for x in s['surfaces'])}{dec})", "",
                    f"As {article(who)} {who}, I want {s['want']}, so that {s['so']}.", ""]
            out += [f"- [ ] {a}" for a in s.get("accept", [])] + [""]
    if screens:
        out += ["## Screens", ""] + [f"- **{sc['id']} {sc['title']}** ({surface(spec, sc['surface'])['name']}; {', '.join(sc['stories'])}). {sc['brief']}" for sc in screens]
    with open(os.path.join(spec["_dir"], "STORIES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip() + "\n")


def flow_file(spec, flow):
    return f"{flow['id']}-{slug(role(spec, flow['role'])['name'])}.dc.html"


def main(work_dir):
    spec = load_spec(work_dir)
    fitted = fitted_heights(spec)
    titles = {}

    def emit(name, title, inner, est_h, root_style=COL):
        h = fitted.get(name[:-8]) or round20(est_h)
        write_board(spec, name, page(spec, title, W, h, inner, root_style=root_style))
        titles[name] = title

    for fn in (cover, model, permissions, journeys, decisions):
        key = {"model": "ENTITIES", "permissions": "PERMISSIONS", "journeys": "JOURNEYS"}.get(fn.__name__)
        if key and not spec.get(key):
            continue
        emit(*fn(spec))
    if spec.get("LIFECYCLES"):
        lc = {"eyebrow": "Overview · States", "title": "States and who moves them", **spec["LIFECYCLES"]}
        html_, _ = render_flow(spec, lc, [("state", "State (what it means)"), ("step", "Arrow label = who or what moves it")],
                               card_w=220, card_h=80, pitch_x=320, pitch_y=150)
        write_board(spec, "O4-Lifecycles.dc.html", html_)
        titles["O4-Lifecycles.dc.html"] = "States and who moves them"
    for flow in spec.get("FLOWS", []):
        r = role(spec, flow["role"])
        f = {"eyebrow": f"User flow · {r['name']} · {', '.join(surface(spec, s)['name'] for s in r['surfaces'])}", **flow}
        html_, _ = render_flow(spec, f, [("step", "Step (screen · story)"), ("decision", "Decision"), ("system", f"{spec['CANVAS']['product']} does it"), ("push", "Notification"), ("end", "Outcome")])
        name = flow_file(spec, flow)
        write_board(spec, name, html_)
        titles[name] = f"{flow['id']} · {r['name']}"
    emit(*roadmap(spec))
    for i, st in enumerate(spec["STAGES"], start=1):
        emit(*stage_board(spec, i, st))
    restyled = []
    for sc in spec.get("SCREENS", []):
        titles[screen_file(sc)] = f"{sc['id']} · {sc['title']}"
        path = os.path.join(project_dir(spec), screen_file(sc))
        if os.path.exists(path) and restyle(spec, path):
            restyled.append(sc["id"])

    with open(os.path.join(spec["_dir"], "helmet.html"), "w", encoding="utf-8") as f:
        f.write(helmet(spec) + "\n")
    pages = layout(spec, titles)
    idx = write_canvas_json(spec, pages, titles)
    write_bundle(spec, pages, titles)
    write_markdown(spec)
    missing = [screen_file(sc) for sc in spec.get("SCREENS", []) if not os.path.exists(os.path.join(project_dir(spec), screen_file(sc)))]
    print(f"{len(idx['boards'])} boards on {len(idx['pages'])} pages · bundle.html · STORIES.md · helmet.html")
    if restyled:
        print("kit refreshed on drawn wireframes: " + ", ".join(restyled))
    if missing:
        print(f"{len(missing)} wireframes still to draw: " + ", ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
