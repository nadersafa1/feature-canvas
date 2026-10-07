"""Wrap a drawn board body in the board shell and the exact helmet, so nothing is pasted by hand.

usage: python3 board.py DIR FILE WIDTH HEIGHT BODY_FILE [CSS_FILE]

FILE is the board's name in root/project (W03-Groups.dc.html). BODY_FILE holds everything that goes
inside the board root: the device frame and the notes aside. CSS_FILE, optional, holds board-local rules.
"""
import os
import sys

from common import load_spec, page, write_board


def main(argv):
    if len(argv) not in (6, 7):
        sys.exit(__doc__)
    spec = load_spec(argv[1])
    name, w, h = argv[2], int(argv[3]), int(argv[4])
    body = open(argv[5], encoding="utf-8").read()
    css = open(argv[6], encoding="utf-8").read() if len(argv) == 7 else ""
    title = name[: -len(".dc.html")].replace("-", " ", 1)
    write_board(spec, name, page(spec, title, w, h, body, extra_css=css))
    print(os.path.join("root", "project", name), f"{w}x{h}")


if __name__ == "__main__":
    main(sys.argv)
