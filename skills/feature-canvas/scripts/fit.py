"""Set board heights to what bundle.html measured, so no board is clipped or padded with empty space.

usage: python3 fit.py WORK_DIR '{"US2-A1": 1712, "W04-Schedule": 1190}'

Generated boards keep their fitted height in heights.json (build.py reads it on every rebuild);
drawn wireframes are edited in place. Heights round up to the next 20 px.
"""
import json
import os
import re
import sys

from common import project_dir, load_spec, round20

GENERATED = re.compile(r"^(Main|O\d-|US\d+-)")


def main(work_dir, measured_json):
    spec = load_spec(work_dir)
    measured = json.loads(measured_json)
    store_path = os.path.join(spec["_dir"], "heights.json")
    store = json.load(open(store_path, encoding="utf-8")) if os.path.exists(store_path) else {}
    for stem, content in measured.items():
        h = round20(int(content))
        path = os.path.join(project_dir(spec), stem + ".dc.html")
        s = open(path, encoding="utf-8").read()
        s, n1 = re.subn(r'(<div class="board[^"]*" style="width: \d+px; height: )\d+(px;)', rf"\g<1>{h}\2", s, count=1)
        s, n2 = re.subn(r'("\$preview":\{"width":\d+,"height":)\d+', rf"\g<1>{h}", s, count=1)
        if n1 != 1 or n2 != 1:
            sys.exit(f"{stem}: could not find the board root and $preview to resize")
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        if GENERATED.match(stem):
            store[stem] = h
        print(f"{stem} -> {h}")
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=1, sort_keys=True)
    print("Run build.py again so canvas.json and bundle.html pick up the new sizes.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
