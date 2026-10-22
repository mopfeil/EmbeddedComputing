#!/usr/bin/env python3
"""Convert the slides PDF into a PPTX with one full-page image per slide.

Usage: pdf2pptx.py input.pdf output.pptx [dpi]

Needs pdftoppm (poppler-utils) and python-pptx; the Makefile runs it from
the venv in ~/.local/share/lecture-tools/venv.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dpi = sys.argv[3] if len(sys.argv) > 3 else "200"

info = subprocess.run(["pdfinfo", src], capture_output=True, text=True, check=True).stdout
w_pt, h_pt = map(float, re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info).groups())

prs = Presentation()
prs.slide_width = Emu(round(w_pt * 12700))
prs.slide_height = Emu(round(h_pt * 12700))
blank = prs.slide_layouts[6]

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["pdftoppm", "-r", dpi, "-png", src, f"{tmp}/p"], check=True)
    for png in sorted(Path(tmp).glob("p-*.png"), key=lambda p: int(p.stem.split("-")[1])):
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(str(png), 0, 0, prs.slide_width, prs.slide_height)

prs.save(dst)
print(f"{dst}: {len(prs.slides)} slides")
