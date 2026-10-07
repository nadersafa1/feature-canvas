"""Check a canvas: the spec's cross-references, then every board's markup.

usage: python3 check.py WORK_DIR            spec + every board in root/project
       python3 check.py WORK_DIR --spec     spec only (before any board exists)
       python3 check.py WORK_DIR FILE...    spec + just these boards (after drawing one)
Exit code 1 on any error. Warnings never fail the run.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

from common import all_stories, helmet, load_spec, project_dir, screen_file

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "stop"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
REF = re.compile(r"\b([A-Z]{1,3}\d{1,3}(?:\.\d{1,3})?)\b")
SIZES = {"S", "M", "L"}
KINDS = {"web", "phone"}
STATUSES = {"agreed", "assumed", "open"}


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errs = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))
        names = dict(attrs)
        if tag in ("div", "span") and ("onclick" in names or names.get("role") == "button"):
            self.errs.append(f"<{tag}> used as a button at {self.getpos()}: use <button>")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            return
        if tag in [t for t, _ in self.stack]:
            while self.stack[-1][0] != tag:
                t, pos = self.stack.pop()
                self.errs.append(f"unclosed <{t}> opened at {pos}")
            self.stack.pop()
        else:
            self.errs.append(f"stray </{tag}> at {self.getpos()}")


def check_spec(spec):
    errs, warns = [], []
    surfaces = {s["id"]: s for s in spec.get("SURFACES", [])}
    roles = {r["id"] for r in spec.get("ROLES", [])}
    for s in spec.get("SURFACES", []):
        if s.get("kind") not in KINDS:
            errs.append(f"surface {s['id']}: kind must be one of {sorted(KINDS)}")
    for r in spec.get("ROLES", []):
        for x in r.get("surfaces", []):
            if x not in surfaces:
                errs.append(f"role {r['id']}: unknown surface {x}")
    stories = all_stories(spec)
    story_ids = [s["id"] for s in stories]
    stage_ids = [s["id"] for s in spec.get("STAGES", [])]
    screen_ids = [sc["id"] for sc in spec.get("SCREENS", [])]
    decision_ns = [d["n"] for d in spec.get("DECISIONS", [])]
    for label, ids in (("story", story_ids), ("stage", stage_ids), ("screen", screen_ids), ("decision", decision_ns)):
        dup = sorted({str(i) for i in ids if ids.count(i) > 1})
        if dup:
            errs.append(f"duplicate {label} ids: {', '.join(dup)}")
    for st in spec.get("STAGES", []):
        for dep in st.get("after", []):
            if dep not in stage_ids:
                errs.append(f"stage {st['id']}: needs unknown stage {dep}")
        if not st["stories"]:
            errs.append(f"stage {st['id']} has no stories")
    for s in stories:
        if s["size"] not in SIZES:
            errs.append(f"story {s['id']}: size must be S, M or L")
        if s["as"] not in roles:
            warns.append(f"story {s['id']}: 'as' is not a role id ({s['as']}); it prints as written")
        for x in s["surfaces"]:
            if x not in surfaces:
                errs.append(f"story {s['id']}: unknown surface {x}")
        for n in s.get("decisions", []):
            if n not in decision_ns:
                errs.append(f"story {s['id']}: unknown decision #{n}")
        if not s.get("accept"):
            errs.append(f"story {s['id']}: no acceptance points")
    covered = set()
    for sc in spec.get("SCREENS", []):
        if sc["surface"] not in surfaces:
            errs.append(f"screen {sc['id']}: unknown surface {sc['surface']}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", sc["slug"]):
            errs.append(f"screen {sc['id']}: slug must be letters, digits and dashes")
        for x in sc["stories"]:
            if x not in story_ids:
                errs.append(f"screen {sc['id']}: unknown story {x}")
            covered.add(x)
    later = {s["id"] for st in spec.get("STAGES", []) if st.get("later") for s in st["stories"]}
    for s in stories:
        if s["id"] not in covered and s["id"] not in later and s.get("screen", True):
            errs.append(f"story {s['id']} is on no screen (add it to a screen, or set 'screen': False if it has no UI)")
    known = set(story_ids) | set(screen_ids) | set(stage_ids) | {f["id"] for f in spec.get("FLOWS", [])}
    for f in spec.get("FLOWS", []):
        if f["role"] not in roles:
            errs.append(f"flow {f['id']}: unknown role {f['role']}")
        for lane in f["lanes"]:
            errs += check_lane(f"flow {f['id']}", lane, known)
    for lane in spec.get("LIFECYCLES", {}).get("lanes", []):
        errs += check_lane("lifecycle", lane, None)
    for j in spec.get("JOURNEYS", []):
        if j["role"] not in roles:
            errs.append(f"journey {j['title']!r}: unknown role {j['role']}")
        for _, ref in j["steps"]:
            for token in REF.findall(ref or ""):
                if token not in known:
                    errs.append(f"journey {j['title']!r}: unknown ref {token}")
    for group, rows in spec.get("PERMISSIONS", []):
        for action, cells in rows:
            for rid in cells:
                if rid not in roles:
                    errs.append(f"permissions {action!r}: unknown role {rid}")
    for d in spec.get("DECISIONS", []):
        if d["status"] not in STATUSES:
            errs.append(f"decision #{d['n']}: status must be one of {sorted(STATUSES)}")
    n_open = sum(d["status"] == "open" for d in spec.get("DECISIONS", []))
    if n_open:
        warns.append(f"{n_open} decisions are still open")
    return errs, warns


def check_lane(where, lane, known):
    errs, ids = [], set()
    cells = set()
    for node in lane["nodes"]:
        nid, row, col, kind, title, *refs = node
        if nid in ids:
            errs.append(f"{where} lane {lane['tag']}: duplicate node {nid}")
        ids.add(nid)
        if (row, col) in cells:
            errs.append(f"{where} lane {lane['tag']}: two nodes at row {row}, col {col}")
        cells.add((row, col))
        if col > 4:
            errs.append(f"{where} lane {lane['tag']}: node {nid} at col {col}; a lane has columns 0-4")
        if known is not None and refs:
            for token in REF.findall(refs[0]):
                if token not in known:
                    errs.append(f"{where} node {nid}: unknown ref {token}")
    for e in lane["edges"]:
        for end in e[:2]:
            if end not in ids:
                errs.append(f"{where} lane {lane['tag']}: edge to unknown node {end}")
    return errs


def check_board(path, spec):
    s = open(path, encoding="utf-8").read()
    errs = []
    if '<script src="./support.js"></script>' not in s:
        errs.append("missing the support.js head line")
    kit = helmet(spec).rsplit("</style>", 1)[0]
    if kit not in s or not re.search(r"</style>\s*</helmet>", s) or (s.count("</style>") > 1 and "/* board-local */" not in s):
        errs.append("helmet differs from helmet.html: build boards with scripts/board.py (board-local CSS may follow the kit inside the same <style>)" if "<helmet>" in s else "missing <helmet>")
    m = re.search(r"<script type=\"text/x-dc\" data-dc-script data-props='([^']*)'", s)
    if not m:
        errs.append("missing the data-dc-script block with single-quoted data-props")
    else:
        try:
            pv = json.loads(m.group(1))["$preview"]
            root = re.search(r'<div class="board[^"]*" style="width: (\d+)px; height: (\d+)px', s)
            if not root:
                errs.append('board root must start <div class="board" style="width: Wpx; height: Hpx; ...')
            elif (int(root.group(1)), int(root.group(2))) != (pv["width"], pv["height"]):
                errs.append(f"$preview {pv['width']}x{pv['height']} != board root {root.group(1)}x{root.group(2)}")
        except (ValueError, KeyError) as e:
            errs.append(f"data-props is not valid JSON with $preview: {e}")
    body = s.split("<x-dc>", 1)[-1].split("</x-dc>", 1)[0]
    found = EMOJI.search(body)
    if found:
        errs.append(f"emoji used as an icon: {found.group(0)}")
    for bad in ("innerHTML", "appendChild", "<iframe", "<object", "<embed"):
        if bad in s:
            errs.append(f"not allowed on a board: {bad}")
    parser = Tags()
    parser.feed(body)
    errs += parser.errs + [f"unclosed <{t}> opened at {pos}" for t, pos in parser.stack]
    text = re.sub(r"<[^>]+>", " ", body)
    for word, instead in spec.get("VOCABULARY", {}).get("never", {}).items():
        if re.search(rf"\b{re.escape(word)}\b", text, re.I):
            errs.append(f"uses {word!r}: {instead}")
    return errs


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    spec = load_spec(argv[1])
    errs, warns = check_spec(spec)
    for w in warns:
        print("WARN", w)
    print(("OK   spec" if not errs else "ERR  spec"))
    for e in errs:
        print("    -", e)
    bad = bool(errs)
    if argv[2:] == ["--spec"]:
        sys.exit(1 if bad else 0)
    proj = project_dir(spec)
    files = argv[2:]
    if not files and os.path.isdir(proj):
        files = sorted(os.path.join(proj, f) for f in os.listdir(proj) if f.endswith(".dc.html"))
    for f in files:
        e = check_board(f, spec)
        print(("OK   " if not e else "ERR  ") + os.path.basename(f))
        for x in e[:15]:
            print("    -", x)
        bad |= bool(e)
    if not argv[2:]:
        missing = [screen_file(sc) for sc in spec.get("SCREENS", []) if not os.path.exists(os.path.join(proj, screen_file(sc)))]
        if missing:
            print("ERR  wireframes not drawn yet: " + ", ".join(missing))
            bad = True
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv)
