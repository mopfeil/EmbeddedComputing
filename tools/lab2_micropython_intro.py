"""MicroPython introduction for lab task 2 (ET1 robot, H-bridge).

A 30-45 minute introduction to MicroPython for students without Python
knowledge: every language concept is shown with a piece of the ET1 robot
(LED, button, H-bridge) from Lab/2-programming/python/main.py, without giving
away the solutions of the TODOs. Editable PPTX built with python-pptx, with
speaker notes. All code on the slides was run in MicroPython 1.29 (RPI_PICO)
in Wokwi; the outputs and error texts shown are the real ones.

    make lab2-intro    (= python tools/lab2_micropython_intro.py [out.pptx])
"""
import re
import sys
import pathlib

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGO = ROOT / "figures" / "lab2" / "rwu_logo.png"
OUT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "pdf" / "EmbeddedComputing_Lab_2_MicroPython_Intro.pptx")

# ---- RWU colours (preamble.tex) ---------------------------------------------
VIOLET = RGBColor(0x66, 0x38, 0xB6)
VIOLET_DARK = RGBColor(0x3A, 0x1F, 0x6E)
VIOLET_LIGHT = RGBColor(0x9B, 0x7D, 0xD4)
VIOLET_TINT = RGBColor(0xF3, 0xEF, 0xFA)
CYAN = RGBColor(0x00, 0xA9, 0xCE)
CYAN_DARK = RGBColor(0x00, 0x7C, 0x99)
CYAN_TINT = RGBColor(0xE3, 0xF5, 0xFB)
TEXT = RGBColor(0x26, 0x24, 0x33)
GRAY = RGBColor(0x6E, 0x6B, 0x7B)
LIGHTGRAY = RGBColor(0xD9, 0xD6, 0xE0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xC6, 0x28, 0x28)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
ORANGE = RGBColor(0xB5, 0x48, 0x0F)

FONT = "Calibri"
MONO = "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = 13.333, 7.5
LAYOUT_TITLE_ONLY = prs.slide_layouts[5]
LAYOUT_BLANK = prs.slide_layouts[6]
slide_no = 0


# ---- basic helpers ------------------------------------------------------------
def rgb_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def no_line(shape):
    shape.line.fill.background()


def text(slide, x, y, w, h, content, size=16, color=TEXT, bold=False, italic=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, margin=0.0, space_after=0,
         name=None):
    """content: str (lines split at \\n) or list of paragraphs; a paragraph is a str
    or a list of runs (str or (str, dict))."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    m = Inches(margin)
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = m
    paras = content.split("\n") if isinstance(content, str) else content
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        runs = [para] if isinstance(para, (str, tuple)) else para
        for r in runs:
            s, opt = (r, {}) if isinstance(r, str) else r
            run = p.add_run()
            run.text = s
            f = run.font
            f.name = opt.get("font", font)
            f.size = Pt(opt.get("size", size))
            f.bold = opt.get("bold", bold)
            f.italic = opt.get("italic", italic)
            f.color.rgb = opt.get("color", color)
    return tb


def bullets(slide, x, y, w, h, items, size=18, color=TEXT, space_after=8):
    """items: list of str or run lists; an item starting with '  ' is a sub-item."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        level = 0
        if isinstance(item, str) and item.startswith("  "):
            level, item = 1, item.strip()
        runs = [item] if isinstance(item, str) else item
        for r in runs:
            s, opt = (r, {}) if isinstance(r, str) else r
            run = p.add_run()
            run.text = s
            run.font.name = opt.get("font", FONT)
            run.font.size = Pt(opt.get("size", size - 2 * level))
            run.font.bold = opt.get("bold", False)
            run.font.color.rgb = opt.get("color", color)
        p.space_after = Pt(space_after)
        pPr = p._p.get_or_add_pPr()
        indent = 0.28 + 0.3 * level
        pPr.set("marL", str(Inches(indent)))
        pPr.set("indent", str(-Inches(0.24)))
        buClr = pPr.makeelement(qn("a:buClr"), {})
        clr = buClr.makeelement(qn("a:srgbClr"), {"val": "00A9CE" if level == 0 else "9B7DD4"})
        buClr.append(clr)
        pPr.append(buClr)
        buFont = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
        pPr.append(buFont)
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•" if level == 0 else "–"})
        pPr.append(bu)
    return tb


def box(slide, x, y, w, h, fill=VIOLET_TINT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.08, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    if fill is None:
        s.fill.background()
    else:
        rgb_fill(s, fill)
    if line is None:
        no_line(s)
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.25)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    s.text_frame.text = ""
    return s


def shape_text(s, content, size=16, color=TEXT, bold=False, align=PP_ALIGN.CENTER,
               font=FONT, anchor=MSO_ANCHOR.MIDDLE):
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    oval = s.auto_shape_type == MSO_SHAPE.OVAL
    tf.margin_left = tf.margin_right = Inches(0 if oval else 0.08)
    tf.margin_top = tf.margin_bottom = Inches(0 if oval else 0.04)
    if oval:
        tf.word_wrap = False
        if len(content) >= 2 and content.isdigit():
            size = size * 0.8
    lines = content.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.bold = bold
        r.font.name = font


def line(slide, x1, y1, x2, y2, color=GRAY, width=1.5, arrow=False, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        d = ln.makeelement(qn("a:prstDash"), {"val": "dash"})
        ln.append(d)
    if arrow:
        tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
        ln.append(tail)
    return c


def polyline(slide, pts, color=VIOLET, width=2.25):
    """open polyline through pts (inches)"""
    emu = [(int(Inches(px)), int(Inches(py))) for px, py in pts]
    fb = slide.shapes.build_freeform(emu[0][0], emu[0][1], scale=1.0)
    fb.add_line_segments(emu[1:], close=False)
    s = fb.convert_to_shape()
    s.fill.background()
    s.line.color.rgb = color
    s.line.width = Pt(width)
    s.shadow.inherit = False
    return s


# ---- syntax-highlighted code ----------------------------------------------------
KEYWORDS = {"def", "return", "if", "elif", "else", "while", "for", "in", "import", "from",
            "global", "True", "False", "None", "and", "or", "not", "break", "pass", "try",
            "except", "as", "continue"}
BUILTINS = {"print", "range", "int", "abs", "min", "max", "len", "type", "str", "float",
            "list", "help", "dir"}
TOKEN = re.compile(r'(?P<comment>#.*)|(?P<string>f?"[^"]*"|f?\'[^\']*\')|'
                   r'(?P<number>\b\d+(?:\.\d+)?\b)|(?P<name>[A-Za-z_]\w*)|(?P<other>.)')


def code_runs(src_line, lang="py"):
    """returns [(text, color, bold, italic)]"""
    if lang == "c":
        body, _, comment = src_line.partition("//")
        runs = [(body, TEXT, False, False)]
        if comment:
            runs.append(("//" + comment, GRAY, False, True))
        return runs
    if src_line.startswith("→"):                     # REPL output / serial output line
        return [(src_line[1:].lstrip(), CYAN_DARK, False, False)]
    if src_line.startswith("!"):                     # error output
        return [(src_line[1:].lstrip(), RED, False, False)]
    runs = []
    rest = src_line
    if rest.startswith(">>> "):
        runs.append((">>> ", GRAY, False, False))
        rest = rest[4:]
    for m in TOKEN.finditer(rest):
        kind, s = m.lastgroup, m.group()
        if kind == "comment":
            runs.append((s, GRAY, False, True))
        elif kind == "string":
            runs.append((s, GREEN, False, False))
        elif kind == "number":
            runs.append((s, ORANGE, False, False))
        elif kind == "name" and s in KEYWORDS:
            runs.append((s, VIOLET, True, False))
        elif kind == "name" and s in BUILTINS:
            runs.append((s, CYAN_DARK, False, False))
        else:
            runs.append((s, TEXT, False, False))
    merged = []
    for r in runs:                                   # merge equal-style neighbours
        if merged and merged[-1][1:] == r[1:]:
            merged[-1] = (merged[-1][0] + r[0],) + r[1:]
        else:
            merged.append(r)
    return merged


def code(slide, x, y, w, h, src, size=15, fill=VIOLET_TINT, highlight=None, title=None, lang="py"):
    """highlight: set of 1-based line numbers drawn on a cyan tint. The font size shrinks
    until every line fits (checked with a 0.6 em wide monospace font, the widest common one)."""
    bg = box(slide, x, y, w, h, fill=fill, radius=0.04, name="code background")
    lines = src.strip("\n").split("\n")
    pad = 0.18
    avail_h = h - 2 * pad - (0.3 if title else 0)
    longest = max(len(l.lstrip("→!")) for l in lines)
    while size > 11 and (longest * size * 0.6 / 72 > w - 2 * pad or len(lines) * size * 1.18 / 72 > avail_h):
        size -= 0.5
    if longest * size * 0.6 / 72 > w - 2 * pad or len(lines) * size * 1.18 / 72 > avail_h:
        print(f"WARNING slide {slide_no}: code does not fit: {lines[0][:30]}")
    top = y + pad
    if title:
        text(slide, x + pad, y + 0.1, w - 2 * pad, 0.3, title, size=11, color=GRAY, bold=True)
        top += 0.3
    lh = size * 1.18 / 72                         # line height in inches
    for n in (highlight or ()):
        hb = box(slide, x + 0.06, top + (n - 1) * lh - 0.01, w - 0.12, lh + 0.02, fill=CYAN_TINT,
                 shape=MSO_SHAPE.RECTANGLE, name="highlight")
    tb = slide.shapes.add_textbox(Inches(x + pad), Inches(top), Inches(w - 2 * pad),
                                  Inches(h - (top - y) - pad / 2))
    tb.name = "code"
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        for s, color, bold, italic in code_runs(ln, lang) or [(" ", TEXT, False, False)]:
            r = p.add_run()
            r.text = s
            r.font.name = MONO
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.bold = bold
            r.font.italic = italic
    # exact line height so that highlight bars line up
    for p in tf.paragraphs:
        pPr = p._p.get_or_add_pPr()
        lnSpc = pPr.makeelement(qn("a:lnSpc"), {})
        spcPts = lnSpc.makeelement(qn("a:spcPts"), {"val": str(int(size * 1.18 * 100))})
        lnSpc.append(spcPts)
        pPr.insert(0, lnSpc)
    return bg


# ---- slide frames --------------------------------------------------------------
def footer(slide, dark=False):
    c = VIOLET_LIGHT if dark else GRAY
    text(slide, 0.6, SH - 0.45, 8, 0.3, "Embedded Computing · Lab 2 · MicroPython in 45 minutes",
         size=10, color=c, name="footer")
    text(slide, SW - 1.6, SH - 0.45, 1.0, 0.3, str(slide_no), size=10, color=c,
         align=PP_ALIGN.RIGHT, name="slide number")


def content_slide(title, num=None, notes=""):
    """light slide; num = concept number shown in a cyan circle before the title"""
    global slide_no
    slide_no += 1
    s = prs.slides.add_slide(LAYOUT_TITLE_ONLY)
    tx = 0.6
    if num is not None:
        c = box(s, 0.6, 0.47, 0.62, 0.62, fill=CYAN, shape=MSO_SHAPE.OVAL, name="concept number")
        shape_text(c, str(num), size=20, color=WHITE, bold=True)
        tx = 1.4
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(tx), Inches(0.35), Inches(SW - tx - 0.6), Inches(0.85)
    tf = t.text_frame
    tf.margin_left = tf.margin_right = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = title
    r.font.size = Pt(34)
    r.font.bold = True
    r.font.name = FONT
    r.font.color.rgb = VIOLET
    footer(s)
    if notes:
        s.notes_slide.notes_text_frame.text = notes.strip()
    return s


def dark_slide(notes=""):
    global slide_no
    slide_no += 1
    s = prs.slides.add_slide(LAYOUT_BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = VIOLET_DARK
    if notes:
        s.notes_slide.notes_text_frame.text = notes.strip()
    return s


def section(title, subtitle, items, notes=""):
    s = dark_slide(notes)
    text(s, 0.9, 2.2, 8, 1.0, title, size=44, bold=True, color=WHITE)
    text(s, 0.9, 3.25, 8, 0.6, subtitle, size=20, color=RGBColor(0x99, 0xDD, 0xFD))
    # concept list on the right
    y = 1.9
    for num, label in items:
        c = box(s, 9.0, y, 0.5, 0.5, fill=CYAN, shape=MSO_SHAPE.OVAL)
        shape_text(c, str(num), size=15, color=WHITE, bold=True)
        text(s, 9.7, y, 3.2, 0.5, label, size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.72
    footer(s, dark=True)
    return s


def card(slide, x, y, w, h, head, body, fill=VIOLET_TINT, head_color=VIOLET, size=15,
         icon=None):
    box(slide, x, y, w, h, fill=fill, radius=0.06, name="card")
    tx = x + 0.25
    if icon:
        c = box(slide, x + 0.22, y + 0.22, 0.5, 0.5, fill=head_color, shape=MSO_SHAPE.OVAL)
        shape_text(c, icon, size=15, color=WHITE, bold=True)
        text(slide, x + 0.85, y + 0.22, w - 1.05, 0.5, head, size=18, bold=True,
             color=head_color, anchor=MSO_ANCHOR.MIDDLE)
    else:
        text(slide, tx, y + 0.2, w - 0.5, 0.45, head, size=18, bold=True, color=head_color)
    body_y = y + (0.9 if icon else 0.7)
    if isinstance(body, list):
        text(slide, tx, body_y, w - 0.5, h - (body_y - y) - 0.15, body, size=size, space_after=4)
    else:
        text(slide, tx, body_y, w - 0.5, h - (body_y - y) - 0.15, body, size=size)


def table(slide, x, y, w, rows, col_w, size=14, row_h=0.42, header_fill=VIOLET, mono_cols=()):
    nr, nc = len(rows), len(rows[0])
    gt = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    tbl = gt.table
    # plain style: no banding from the default table style
    tblPr = tbl._tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = header_fill
            else:
                cell.fill.fore_color.rgb = VIOLET_TINT if i % 2 == 0 else WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = val
            r.font.size = Pt(size)
            r.font.name = MONO if (j in mono_cols and i > 0) else FONT
            r.font.bold = i == 0
            r.font.color.rgb = WHITE if i == 0 else TEXT
    return gt


# =================================================================================
# 1  Title
# =================================================================================
s = dark_slide(notes="""
Goal of these 30-45 minutes: you can read main.py of lab task 2 and write the missing
functions yourself. No Python knowledge is assumed. Every concept comes with a piece of the
ET1 robot: the LED, the button and the H-bridge that drives the two motors.

All code on the slides was run in MicroPython 1.29 on the simulated Pico in Wokwi;
the outputs and error messages shown are the real ones.
""")
logo_card = box(s, 0.9, 0.8, 3.3, 1.05, fill=WHITE, radius=0.12)
s.shapes.add_picture(str(LOGO), Inches(1.1), Inches(0.98), height=Inches(0.7))
text(s, 0.9, 2.45, 9.5, 1.2, "MicroPython in 45 Minutes", size=54, bold=True, color=WHITE)
text(s, 0.9, 3.55, 9.5, 0.8, "Python concepts explained with the H-bridge of the ET1 robot",
     size=24, color=RGBColor(0x99, 0xDD, 0xFD))
text(s, 0.9, 4.6, 9, 0.5, "Embedded Computing · Master · Introduction to lab task 2",
     size=16, color=VIOLET_LIGHT)
# little robot motif: two wheels + body
body = box(s, 10.2, 2.3, 1.9, 2.4, fill=VIOLET, radius=0.18)
for wx in (9.85, 11.95):
    w_ = box(s, wx, 2.8, 0.5, 1.4, fill=CYAN, radius=0.3)
fwd = box(s, 11.05, 2.45, 0.2, 0.9, fill=WHITE, radius=0.4)
c = box(s, 10.55, 3.7, 1.2, 0.55, fill=VIOLET_DARK, radius=0.3)
shape_text(c, "ET1", size=16, color=WHITE, bold=True)
text(s, 9.6, 4.95, 3.2, 0.4, ">>> motor(LEFT, 50)", size=16, color=RGBColor(0x99, 0xDD, 0xFD),
     font=MONO, align=PP_ALIGN.CENTER)

# =================================================================================
# 2  Plan
# =================================================================================
s = content_slide("What you can do after this introduction", notes="""
Three outcomes. First: read main.py, the frame of the lab task: what is given, where the TODOs are.
Second: write the functions with the TODOs yourself: motor(), button_clicked() and the driving
sequences. Third: find your own mistakes, because Python tells you exactly where it stopped.

Timing: about 10 minutes for the basics (how the code gets onto the Pico, variables, objects),
15 minutes for control flow and functions, 10 minutes for timing, output and errors,
then a tour of main.py.
""")
card(s, 0.6, 1.6, 3.85, 2.9, "Read main.py", "Find the wiring, the H-bridge pins and the TODOs. Know which part is given and which part is yours.", icon="1")
card(s, 4.74, 1.6, 3.85, 2.9, "Write the TODOs", "motor(), button_clicked(), task3(), ramp(), wait_ms(): every concept you need is on one of the next slides.", icon="2")
card(s, 8.88, 1.6, 3.85, 2.9, "Find your mistakes", "Read a traceback, try a line in the REPL, print values. Change, build, run again.", icon="3")
# timeline
steps = [("Basics", "workflow, variables,\nnumbers, objects", 10), ("Control flow", "if, while, for,\nfunctions, global", 15),
         ("On the Pico", "timing, print,\nerrors, REPL", 10), ("Tour", "main.py,\nyour tasks", 5)]
x = 0.6
for i, (h, d, m) in enumerate(steps):
    w_ = 12.13 * m / 40
    b = box(s, x, 5.0, w_ - 0.08, 0.5, fill=VIOLET if i % 2 == 0 else CYAN, radius=0.2)
    shape_text(b, f"{h} · {m} min", size=14, color=WHITE, bold=True)
    text(s, x, 5.58, w_ - 0.1, 0.7, d, size=12, color=GRAY, align=PP_ALIGN.CENTER)
    x += w_

# =================================================================================
# 3  Python vs C first look
# =================================================================================
s = content_slide("The same blink program in C and in MicroPython", notes="""
Most of you know C. Put the two programs side by side: they do the same thing, LED on GP7 on
and off every half second.

Differences you see at once: no main(), no setup()/loop() - the file is simply executed from top
to bottom. No semicolons, no braces: the colon starts a block and the indentation shows what
belongs to it. No type names: led is just a name for a Pin object. # starts a comment.

The important difference you do not see: C is compiled to machine code on your PC.
MicroPython is an interpreter that runs ON the Pico and executes main.py line by line.
That makes it slower, but you can type commands into the running Pico (REPL, later).
""")
code(s, 0.6, 1.55, 5.9, 4.2, """#include <Arduino.h>

void setup() {
    pinMode(7, OUTPUT);       // red LED
}

void loop() {
    digitalWrite(7, HIGH);    // LED on
    delay(500);
    digitalWrite(7, LOW);     // LED off
    delay(500);
}""", size=15, title="C (Arduino-Pico core)", fill=RGBColor(0xF2, 0xF2, 0xF4), lang="c")
code(s, 6.83, 1.55, 5.9, 4.2, """from machine import Pin
import time

led = Pin(7, Pin.OUT)      # red LED

while True:
    led.value(1)           # LED on
    time.sleep_ms(500)
    led.value(0)           # LED off
    time.sleep_ms(500)""", size=15, title="MicroPython - main.py")
for i, (h, d) in enumerate([("No main()", "the file runs from top to bottom"),
                            ("No ; and { }", "colon + indentation make a block"),
                            ("No types", "led is a name for a Pin object"),
                            ("Interpreted", "MicroPython runs on the Pico itself")]):
    x = 0.6 + i * 3.07
    text(s, x, 6.0, 2.95, 0.35, h, size=16, bold=True, color=VIOLET)
    text(s, x, 6.35, 2.95, 0.5, d, size=13, color=GRAY)

# =================================================================================
# 4  Workflow
# =================================================================================
s = content_slide("How main.py gets onto the simulated Pico", notes="""
In the lab you work in VS Code with the Wokwi extension. Wokwi loads one firmware file.
The script make_uf2.py packs two things into it: the MicroPython interpreter (downloaded once)
and a small file system that holds your main.py. After reset MicroPython starts main.py.

Build task "Python: build main.uf2", then F1 > Wokwi: Start Simulator. print() output appears
in the serial monitor.

Faster: while the simulation runs, the task "Python: run main.py in the running simulation"
sends main.py via mpremote without a rebuild.
""")
flow = [("main.py", "your code", VIOLET), ("make_uf2.py", "Build Task", CYAN_DARK),
        ("build/main.uf2", "MicroPython +\nfile system", VIOLET), ("Wokwi", "Start Simulator", CYAN_DARK),
        ("Serial monitor", "print() output,\nREPL >>>", VIOLET)]
bw, gap = 2.05, 0.47
for i, (h, d, col) in enumerate(flow):
    x = 0.6 + i * (bw + gap)
    b = box(s, x, 1.9, bw, 1.25, fill=col, radius=0.12)
    shape_text(b, h, size=17, color=WHITE, bold=True)
    text(s, x, 3.25, bw, 0.7, d, size=14, color=GRAY, align=PP_ALIGN.CENTER)
    if i < len(flow) - 1:
        line(s, x + bw + 0.05, 2.525, x + bw + gap - 0.05, 2.525, color=GRAY, width=2, arrow=True)
# shortcut path
line(s, 0.6 + bw / 2, 4.05, 0.6 + bw / 2, 4.45, color=CYAN, width=2)
line(s, 0.6 + bw / 2, 4.45, 0.6 + 3 * (bw + gap) + bw / 2, 4.45, color=CYAN, width=2, dash=True)
line(s, 0.6 + 3 * (bw + gap) + bw / 2, 4.45, 0.6 + 3 * (bw + gap) + bw / 2, 4.0, color=CYAN, width=2, arrow=True)
text(s, 2.2, 4.55, 7.4, 0.4, "shortcut while it runs: task “run main.py in the running simulation” (mpremote)",
     size=13, color=CYAN_DARK, align=PP_ALIGN.CENTER)
card(s, 0.6, 5.15, 5.95, 1.6, "After each change", "Build again, then restart the simulator. Your program starts from the top.", size=15)
card(s, 6.78, 5.15, 5.95, 1.6, "Where do I see something?", "print() and error messages: serial monitor (USB). The robot: ET1 display.", size=15)

# =================================================================================
# 5  H-bridge
# =================================================================================
s = content_slide("The hardware we program: two motors behind an H-bridge", notes="""
The example for the whole introduction. An H-bridge has four switches around the motor.
IN1 and IN2 choose which motor terminal goes to +V and which to ground.
IN1=1, IN2=0: current flows from A to B, the wheel turns forward. 0 1: the other way round,
backward. 0 0: both terminals on ground, the motor is short-circuited and brakes.

ENA decides HOW LONG per PWM period the bridge is switched on: that is the speed.
The right motor is the same with IN3, IN4 and ENB.

In Python you will set exactly these three signals per motor: two digital outputs and one
PWM output. Below 12 % duty cycle the motor does not turn (friction) - you will see that on the display.
""")
# drawing: +V rail, GND rail, two half bridges
X0, X1 = 0.9, 5.4
YT, YB = 1.75, 5.75
line(s, X0, YT, X1, YT, color=TEXT, width=2.5)
line(s, X0, YB, X1, YB, color=TEXT, width=2.5)
text(s, X0 - 0.1, YT - 0.42, 1.0, 0.35, "+V", size=14, bold=True)
text(s, X0 - 0.1, YB + 0.05, 1.0, 0.35, "GND", size=14, bold=True)
xa, xb = 1.7, 4.6
ym = (YT + YB) / 2
for xc, top_on, bot_on, top_l, bot_l in ((xa, True, False, "S1", "S2"), (xb, False, True, "S3", "S4")):
    line(s, xc, YT, xc, YT + 0.45, color=TEXT, width=2)
    sw1 = box(s, xc - 0.32, YT + 0.45, 0.64, 0.8, fill=CYAN if top_on else WHITE, line=TEXT, radius=0.1)
    shape_text(sw1, top_l, size=13, bold=True, color=WHITE if top_on else TEXT)
    line(s, xc, YT + 1.25, xc, YB - 1.25, color=TEXT, width=2)
    sw2 = box(s, xc - 0.32, YB - 1.25, 0.64, 0.8, fill=CYAN if bot_on else WHITE, line=TEXT, radius=0.1)
    shape_text(sw2, bot_l, size=13, bold=True, color=WHITE if bot_on else TEXT)
    line(s, xc, YB - 0.45, xc, YB, color=TEXT, width=2)
line(s, xa, ym, 2.65, ym, color=TEXT, width=2)
line(s, 3.65, ym, xb, ym, color=TEXT, width=2)
m = box(s, 2.65, ym - 0.5, 1.0, 1.0, fill=VIOLET, shape=MSO_SHAPE.OVAL)
shape_text(m, "M", size=22, color=WHITE, bold=True)
text(s, xa - 0.55, ym - 0.4, 0.5, 0.35, "A", size=14, bold=True, color=VIOLET)
text(s, xb + 0.12, ym - 0.4, 0.5, 0.35, "B", size=14, bold=True, color=VIOLET)
# current arrow
line(s, 2.05, ym - 0.75, 4.2, ym - 0.75, color=RED, width=2.5, arrow=True)
text(s, 2.05, ym - 1.15, 2.2, 0.35, "current: forward", size=12, color=RED, align=PP_ALIGN.CENTER)
text(s, 0.9, 6.15, 4.6, 0.45, "IN1 = 1, IN2 = 0: S1 and S4 closed", size=13, color=GRAY)
# truth table + pins
table(s, 6.3, 1.65, 6.4, [["IN1", "IN2", "ENA (PWM)", "Left wheel"],
                          ["1", "0", "duty 0 … 100 %", "forward"],
                          ["0", "1", "duty 0 … 100 %", "backward"],
                          ["0", "0", "any", "brake"]],
      [0.8, 0.8, 2.2, 2.6], size=15, row_h=0.45)
table(s, 6.3, 3.85, 6.4, [["Pico pin", "Signal", "In main.py"],
                          ["GP18 / 17 / 16", "ENA / IN1 / IN2", "ena, in1, in2"],
                          ["GP19 / 20 / 21", "ENB / IN3 / IN4", "enb, in3, in4"],
                          ["GP7 · GP5", "LED · START button", "led, button"]],
      [2.0, 2.3, 2.1], size=14, row_h=0.42, header_fill=CYAN_DARK, mono_cols=(2,))
text(s, 6.3, 5.75, 6.4, 0.8, [[("Up to 12 % duty cycle the motor does not turn. ", {}),
                               ("Top speed 0.25 m/s, wheels 14 cm apart.", {"color": GRAY})]], size=14)

# =================================================================================
# Section: basics
# =================================================================================
section("Part 1: Basics", "Statements, values and objects", [(1, "Blocks and indentation"), (2, "Variables and types"),
        (3, "Numbers and arithmetic"), (4, "Objects and methods"), (5, "Tuples, several values at once")],
        notes="Part 1: what a Python statement looks like, which values there are and how we talk to the hardware through objects.")

# =================================================================================
# 6  Indentation
# =================================================================================
s = content_slide("Indentation is part of the syntax", 1, notes="""
The most important rule for C programmers. In C the braces define a block and the indentation is
only for the reader. In Python the indentation IS the block. A line that ends with a colon
(if, while, for, def) opens a block; all following lines that are indented further belong to it.
The block ends with the first line that is indented less.

Convention: 4 spaces per level; VS Code does it for you with Tab. Never mix tabs and spaces.

Error on the right: the line after if is not indented. MicroPython says only "SyntaxError: invalid
syntax" (CPython on the PC says "expected an indented block"). Too much indentation gives
"IndentationError: unexpected indent".
""")
code(s, 0.6, 1.55, 6.7, 3.6, """while True:                # colon: block starts
    if button.value() == 0: # 4 spaces: in while
        led.value(1)        # 8 spaces: in if
    else:
        led.value(0)
    time.sleep_ms(1)        # 4 again: in while
print("never reached")      # 0: after the loop""", size=15, highlight={2, 3})
card(s, 7.6, 1.55, 5.13, 1.7, "Rules", ["Line ends with : → a block follows", "Same indentation = same block", "4 spaces per level, no tabs"], size=15)
code(s, 7.6, 3.5, 5.13, 1.65, """if button.value() == 0:
led.value(1)
!SyntaxError: invalid syntax""", size=15, fill=RGBColor(0xFB, 0xEE, 0xEE), title="forgotten indentation")
text(s, 0.6, 5.45, 12.1, 0.9, [[("# ", {"color": GRAY, "font": MONO}),
                                ("starts a comment up to the end of the line. ", {}),
                                ('"""text"""', {"font": MONO, "color": GREEN}),
                                (" under a def is a docstring: the description of a function, as in main.py.", {})]], size=16)

# =================================================================================
# 7  Variables and types
# =================================================================================
s = content_slide("Variables are names for values", 2, notes="""
A variable is created by the first assignment, there is no declaration. The name points to a value,
and the value knows its type. type() shows it.

The same name can later point to a value of another type; that is allowed, but rarely a good idea.

Conventions you see in main.py: names in CAPITALS are constants (TASK, LEFT, RIGHT). Python does
not enforce that - it is a promise to the reader. Names with lower case and underscores:
button_clicked, wait_ms.

None means "no value yet". True and False start with a capital letter.
""")
table(s, 0.6, 1.6, 7.2, [["Type", "Example from ET1", "Meaning"],
                         ["int", "TASK = 2", "whole number, any size"],
                         ["float", "trim = 0.9", "number with fraction"],
                         ["bool", "running = False", "True or False"],
                         ["str", 'name = "left"', 'text in "…" or \'…\''],
                         ["NoneType", "last = None", "no value (yet)"]],
      [1.4, 2.9, 2.9], size=15, row_h=0.5, mono_cols=(0, 1))
code(s, 8.1, 1.6, 4.63, 3.0, """>>> trim = 0.9
>>> type(trim)
→<class 'float'>
>>> trim = "weak"     # allowed
>>> type(trim)
→<class 'str'>""", size=15, title="REPL")
card(s, 8.1, 4.85, 4.63, 1.75, "Naming", ["CAPITALS: constants (TASK, LEFT)", "lower_case: variables, functions"], size=15)
text(s, 0.6, 4.85, 7.2, 1.6, [[("No declaration, no type name: ", {"bold": True, "color": VIOLET}),
                               ("the first assignment creates the variable. The value has a type, the name has none.", {})],
                              [("= ", {"font": MONO, "bold": True}), ("assigns, ", {}), ("== ", {"font": MONO, "bold": True}),
                               ("compares - as in C.", {})]], size=17, space_after=8)

# =================================================================================
# 8  Numbers
# =================================================================================
s = content_slide("Numbers: from percent to PWM duty cycle", 3, notes="""
The motor driver gets the speed in percent, the PWM wants a 16-bit value 0 ... 65535.
So you have to calculate - and watch the types.

/ always gives a float, even 7 / 2 = 3.5 and 4 / 2 = 2.0. // is integer division, rounding down
(also for negative numbers: -7 // 2 = -4, in C it would be -3). % is the remainder.
int() cuts off the fraction. abs(), min(), max() are built in.

The trap: duty_u16() accepts only an int. A float gives the error on the right. This is the
most frequent error in task 1. A value above 65535 does not give an error: the duty cycle is
simply 100 %.
""")
code(s, 0.6, 1.55, 5.6, 4.6, """>>> 7 / 2
→3.5
>>> 7 // 2          # integer division
→3
>>> 7 % 2           # remainder
→1
>>> -7 // 2         # rounds down!
→-4
>>> abs(-40), min(150, 100)
→(40, 100)
>>> 2 ** 16 - 1     # power
→65535""", size=15, title="REPL")
# duty scale graphic
text(s, 6.55, 1.6, 6.2, 0.4, "PWM duty cycle: duty_u16(0 … 65535)", size=17, bold=True, color=VIOLET)
bx, bw_ = 6.55, 6.15
box(s, bx, 2.15, bw_, 0.42, fill=LIGHTGRAY, radius=0.3)
box(s, bx, 2.15, bw_ * 0.5, 0.42, fill=CYAN, radius=0.3)
for frac, lab in ((0, "0"), (0.5, "32767"), (1.0, "65535")):
    text(s, bx + bw_ * frac - 0.6, 2.62, 1.2, 0.3, lab, size=12, color=GRAY, align=PP_ALIGN.CENTER, font=MONO)
for frac, lab in ((0, "0 %"), (0.5, "50 %"), (1.0, "100 %")):
    text(s, bx + bw_ * frac - 0.6, 2.9, 1.2, 0.3, lab, size=12, color=GRAY, align=PP_ALIGN.CENTER)
code(s, 6.55, 3.45, 6.18, 1.35, """>>> 65535 * 50 // 100
→32767
>>> ena.duty_u16(32767)        # 50 %""", size=15)
code(s, 6.55, 5.0, 6.18, 1.15, """>>> ena.duty_u16(65535 * 50 / 100)
!TypeError: can't convert float to int""", size=15, fill=RGBColor(0xFB, 0xEE, 0xEE))
text(s, 0.6, 6.3, 12.1, 0.5, [[("/ gives a float, always. ", {"bold": True, "color": VIOLET}),
                               ("Use // or int() where a whole number is needed.", {})]], size=16)

# =================================================================================
# 9  Objects
# =================================================================================
s = content_slide("Objects: the hardware as Pin and PWM", 4, notes="""
MicroPython wraps every piece of hardware in an object. Pin(7, Pin.OUT) creates an object that
stands for GPIO 7, configured as output. led is the name we give it.

A method is a function that belongs to an object, called with a dot: led.value(1).
Without an argument value() reads the pin. Pin.OUT, Pin.IN, Pin.PULL_UP are constants of the class Pin.

PWM(Pin(18), freq=1000, duty_u16=0): freq= and duty_u16= are keyword arguments. You name the
parameter, so the order does not matter. This is exactly the line from main.py for the ENA pin.

dir(led) lists everything an object can do - useful in the REPL.
""")
code(s, 0.6, 1.55, 7.0, 3.2, """from machine import Pin, PWM

led    = Pin(7, Pin.OUT)              # output
button = Pin(5, Pin.IN, Pin.PULL_UP)  # input, pull-up
ena    = PWM(Pin(18), freq=1000, duty_u16=0)

led.value(1)          # method call: set the pin
led.off()             # same as led.value(0)
button.value()        # read: 1 = released, 0 = pressed
ena.duty_u16(16384)   # 25 % duty cycle""", size=15, highlight={5})
# object diagram
o = box(s, 8.0, 1.55, 4.73, 1.55, fill=VIOLET, radius=0.1)
shape_text(o, "led\nPin object for GP7", size=17, color=WHITE, bold=True)
for i, mth in enumerate(["value()", "value(1)", "on()", "off()", "toggle()"]):
    col = i % 3
    row = i // 3
    mb = box(s, 8.0 + col * 1.6, 3.3 + row * 0.6, 1.5, 0.48, fill=CYAN_TINT, radius=0.2)
    shape_text(mb, mth, size=14, font=MONO, color=CYAN_DARK)
text(s, 8.0, 4.5, 4.73, 0.4, "methods: called with a dot, led.on()", size=13, color=GRAY)
table(s, 0.6, 5.05, 12.13, [["Word", "Meaning", "Example"],
                            ["class", "the blueprint", "Pin, PWM"],
                            ["object", "one thing made from it", "led, ena"],
                            ["keyword argument", "argument given by name", "freq=1000"]],
      [2.6, 4.5, 5.03], size=14, row_h=0.36, mono_cols=(2,))

# =================================================================================
# 10  PWM
# =================================================================================
s = content_slide("PWM: the speed is the share of on-time", notes="""
The PWM output switches ENA on and off 1000 times per second (freq=1000). What counts is the duty
cycle: the share of each 1 ms period in which the signal is high. The motor is too slow to follow
the single pulses and turns as if it got the average voltage.

The rp2 port measures the duty cycle in 16 bits: 0 is always off, 65535 always on.
Below about 12 % the ET1 motor does not move: friction. You will see that on the display (L and R
show the wheel speeds).
""")
waves = [(0.25, "duty_u16(16384)", "25 %"), (0.5, "duty_u16(32767)", "50 %"), (0.8, "duty_u16(52428)", "80 %")]
for i, (d, call, pct) in enumerate(waves):
    y0 = 1.75 + i * 1.45
    hi, lo = y0, y0 + 0.75
    x = 4.2
    per = 2.1
    pts = [(x, lo)]
    for k in range(4):
        xs = x + k * per
        pts += [(xs, lo), (xs, hi), (xs + per * d, hi), (xs + per * d, lo)]
    pts.append((x + 4 * per, lo))
    polyline(s, pts, color=VIOLET if i != 1 else CYAN_DARK, width=2.5)
    text(s, 0.6, y0 + 0.05, 1.3, 0.65, pct, size=30, bold=True, color=VIOLET if i != 1 else CYAN_DARK)
    text(s, 1.85, y0 + 0.2, 2.3, 0.4, call, size=14, font=MONO, color=TEXT)
text(s, 4.2, 6.05, 2.1, 0.35, "← 1 ms →", size=12, color=GRAY, align=PP_ALIGN.CENTER)
text(s, 8.5, 6.05, 4.2, 0.5, "ena = PWM(Pin(18), freq=1000)", size=14, font=MONO, color=GRAY, align=PP_ALIGN.RIGHT)

# =================================================================================
# 11  Tuples
# =================================================================================
s = content_slide("Tuples: several values at once", 5, notes="""
A comma makes a tuple: (18, 17, 16) is one value that holds three. The parentheses are optional.

Unpacking: on the left of = you can write several names, then each gets one element. main.py uses
that for LEFT, RIGHT = 0, 1 and for the two direction pins. a, b = b, a swaps two values without
a temporary variable.

A function can return a tuple and the caller unpacks it: so a function can give back several
values. Think about it for the motor driver: which three objects belong to one side?
""")
code(s, 0.6, 1.55, 6.3, 2.35, """LEFT, RIGHT = 0, 1        # from main.py
in1, in2 = Pin(17, Pin.OUT), Pin(16, Pin.OUT)

pins = (18, 17, 16)        # one tuple
en, a, b = pins            # en=18, a=17, b=16
a, b = b, a                # swap""", size=15, highlight={1, 2})
code(s, 7.2, 1.55, 5.53, 2.35, """def minmax(x, y):
    return min(x, y), max(x, y)

lo, hi = minmax(70, 20)
print(lo, hi)
→20 70""", size=15, title="return several values")
card(s, 0.6, 4.2, 3.85, 2.4, "Tuple ( )", "fixed: you cannot change an element after creation. Good for pin groups.", icon="( )")
card(s, 4.74, 4.2, 3.85, 2.4, "Unpacking", "the number of names on the left must match the number of values.", icon="=")
card(s, 8.88, 4.2, 3.85, 2.4, "Indexing", ["pins[0] → 18", "pins[-1] → 16 (from the end)"], icon="[i]")

# =================================================================================
# Section: control flow
# =================================================================================
section("Part 2: Control flow", "Decisions, loops, functions", [(6, "if / elif / else"), (7, "while loops"),
        (8, "for and range()"), (9, "Functions"), (10, "global: state between calls"), (11, "Lists and dicts")],
        notes="Part 2: everything you need for the logic of the tasks: decisions, loops, functions and state.")

# =================================================================================
# 12  if
# =================================================================================
s = content_slide("if / elif / else: deciding the direction", 6, notes="""
The H-bridge needs a decision: which direction does a given speed mean? if, elif (else if) and else
work as in C, but without parentheses around the condition and with colon + indentation.

Comparisons are the same as in C. Logic is written as words: and, or, not instead of &&, ||, !.
Python allows chained comparisons: -100 <= speed <= 100 means speed >= -100 and speed <= 100.

Here we only print the direction. In task 1 you set the two direction pins instead -
use the truth table from the H-bridge slide.
""")
code(s, 0.6, 1.55, 6.3, 3.4, """speed = -40

if speed > 0:
    print("forward")
elif speed < 0:
    print("backward")
else:
    print("brake")
→backward""", size=16)
table(s, 7.2, 1.55, 5.53, [["Python", "C"], ["if x > 0:", "if (x > 0) {"], ["elif x < 0:", "} else if (x < 0) {"],
                           ["a and b", "a && b"], ["a or b", "a || b"], ["not a", "!a"]],
      [2.6, 2.93], size=15, row_h=0.45, mono_cols=(0, 1))
code(s, 0.6, 5.2, 12.13, 1.2, """>>> -100 <= speed <= 100        # chained comparison
→True""", size=16)

# =================================================================================
# 13  while
# =================================================================================
s = content_slide("while: the endless main loop", 7, notes="""
while repeats its block as long as the condition is true. while True: runs forever - every
microcontroller program has such a loop; in main.py it is at the very end.

break leaves the loop at once, continue jumps to the next round. The example on the left waits
for the button and counts the milliseconds: a typical polling loop.

The diagram on the right is the end of main.py: depending on TASK, the loop calls task2(),
task3() or task4() again and again, with 1 ms pause. So each task function is called very often
- remember that when you write button_clicked().

Ctrl-C in the serial monitor stops a running loop: KeyboardInterrupt.
""")
code(s, 0.6, 1.55, 6.3, 3.5, """count = 0
while True:
    if button.value() == 0:  # pressed?
        break                # leave loop
    count += 1               # count = count + 1
    time.sleep_ms(1)

print("waited", count, "ms")""", size=15, highlight={4})
# flow of main loop
fx = 7.6
nodes = [("stop()\nprint(\"ET1 ready\")", VIOLET), ("TASK == 2? → task2()\nTASK == 3? → task3()\nTASK == 4? → task4()", CYAN_DARK),
         ("time.sleep_ms(1)", VIOLET)]
ys = [1.55, 2.75, 4.35]
hs = [0.85, 1.25, 0.6]
for (lab, col), y, h in zip(nodes, ys, hs):
    b = box(s, fx, y, 4.4, h, fill=col, radius=0.1)
    shape_text(b, lab, size=14, color=WHITE, bold=True, font=MONO)
line(s, fx + 2.2, 2.4, fx + 2.2, 2.75, color=GRAY, width=2, arrow=True)
line(s, fx + 2.2, 4.0, fx + 2.2, 4.35, color=GRAY, width=2, arrow=True)
line(s, fx + 4.4, 4.65, fx + 4.85, 4.65, color=CYAN, width=2)
line(s, fx + 4.85, 4.65, fx + 4.85, 3.37, color=CYAN, width=2)
line(s, fx + 4.85, 3.37, fx + 4.42, 3.37, color=CYAN, width=2, arrow=True)
text(s, fx, 5.1, 5.1, 0.4, "end of main.py: while True", size=13, color=GRAY)
text(s, 0.6, 5.4, 12.1, 1.0, [[("break ", {"font": MONO, "bold": True, "color": VIOLET}), ("leaves the loop, ", {}),
                               ("continue ", {"font": MONO, "bold": True, "color": VIOLET}), ("starts the next round. ", {}),
                               ("x += 1 ", {"font": MONO, "bold": True}), ("exists, ", {}), ("x++ ", {"font": MONO, "bold": True}),
                               ("does not.", {})]], size=17)

# =================================================================================
# 14  for / range
# =================================================================================
s = content_slide("for and range(): counting in steps", 8, notes="""
for runs once for each element of a sequence. range(start, stop, step) produces whole numbers
from start up to - but NOT including - stop. That is the classic trap: range(5) is 0 to 4.

With a negative step range counts down; stop is again not included.
list(range(...)) shows the numbers in the REPL.

For task 4 you need a speed ramp. Think about which start, stop and step give you the
numbers from the task sheet - and check them in the REPL before you drive.
""")
code(s, 0.6, 1.55, 6.0, 2.6, """for duty in range(0, 101, 25):
    print(duty, "%")
→0 %
→25 %
→50 %
→75 %
→100 %""", size=16)
table(s, 6.9, 1.55, 5.83, [["Call", "Numbers"], ["range(5)", "0 1 2 3 4"], ["range(2, 10, 2)", "2 4 6 8"],
                           ["range(5, 0, -1)", "5 4 3 2 1"], ["range(0, 101, 25)", "0 25 50 75 100"]],
      [2.9, 2.93], size=16, row_h=0.5, mono_cols=(0, 1))
# number line visual
text(s, 0.6, 4.55, 12.1, 0.4, "range(start, stop, step): stop is never part of it", size=18, bold=True, color=VIOLET)
for i in range(11):
    x = 0.9 + i * 1.12
    inside = 2 <= i < 10 and i % 2 == 0
    c = box(s, x, 5.15, 0.7, 0.7, fill=CYAN if inside else (RED if i == 10 else LIGHTGRAY), shape=MSO_SHAPE.OVAL)
    shape_text(c, str(i), size=16, color=WHITE if (inside or i == 10) else TEXT, bold=inside)
text(s, 0.6, 6.0, 12.1, 0.5, [[("range(2, 10, 2)", {"font": MONO}), (": 2, 4, 6, 8 - the 10 (red) is the stop value and is left out.", {"color": GRAY})]], size=14)

# =================================================================================
# 15  Functions
# =================================================================================
s = content_slide("Functions: def, parameters, return", 9, notes="""
def defines a function. Parameters have no types. return gives a value back; without return a
function returns None. The docstring directly below def describes what the function does - main.py
uses it for every TODO function, read them.

Default values: ms=200 makes the parameter optional. Keyword arguments: blink(2, ms=100).

The example measures time with ticks_ms and ticks_diff - more on that in part 3.
blink(3) takes 6 x 200 ms = 1200 ms; the simulation printed exactly 1200.

In main.py the functions are given with their name, parameters and docstring; you fill in the body.
""")
code(s, 0.6, 1.55, 7.1, 4.1, """def blink(times, ms=200):
    \"\"\"Blinks the LED, returns the time in ms.\"\"\"
    start = time.ticks_ms()
    for i in range(times):
        led.on()
        time.sleep_ms(ms)
        led.off()
        time.sleep_ms(ms)
    return time.ticks_diff(time.ticks_ms(), start)

print(blink(3), blink(2, ms=100))
→1200 400""", size=15, highlight={1, 9})
for i, (h, d, ic) in enumerate([("def name(params):", "parameters without types; ms=200 is a default", "def"),
                                ("return value", "ends the function; no return gives None", "ret"),
                                ("blink(2, ms=100)", "arguments by position or by name", "( )")]):
    y = 1.55 + i * 1.4
    box(s, 8.0, y, 4.73, 1.22, fill=VIOLET_TINT, radius=0.08)
    c = box(s, 8.2, y + 0.3, 0.62, 0.62, fill=VIOLET, shape=MSO_SHAPE.OVAL)
    shape_text(c, ic, size=12, color=WHITE, bold=True)
    text(s, 9.0, y + 0.15, 3.6, 0.4, h, size=15, bold=True, font=MONO, color=VIOLET)
    text(s, 9.0, y + 0.55, 3.6, 0.6, d, size=14, color=TEXT)
text(s, 0.6, 5.95, 12.1, 0.6, [[("In main.py ", {"bold": True, "color": VIOLET}),
                                ("name, parameters and docstring of each function are given. You write the body, replacing ", {}),
                                ("pass", {"font": MONO, "color": VIOLET, "bold": True}), (".", {})]], size=16)

# =================================================================================
# 16  global
# =================================================================================
s = content_slide("global: a function that remembers something", 10, notes="""
button_clicked() must remember the previous state of the button between two calls. A local
variable is gone after return. So the state has to live outside the function, at module level.

Reading a global variable in a function works without anything. But as soon as a function
ASSIGNS to a name, Python treats that name as local for the whole function. clicks = clicks + 1
then reads a local clicks that does not exist yet: NameError (MicroPython; on the PC it is called
UnboundLocalError).

global clicks tells Python: assignments in this function go to the module variable.
You need this for task 2a (previous state) and 2b (time of the last accepted change).
""")
# scope diagram
outer = box(s, 0.6, 1.55, 5.6, 4.9, fill=CYAN_TINT, radius=0.05)
text(s, 0.85, 1.7, 5.2, 0.4, "module (global): lives as long as the program", size=15, bold=True, color=CYAN_DARK)
text(s, 0.85, 2.15, 5.2, 0.4, "clicks = 0      led      button      TASK", size=15, font=MONO)
inner = box(s, 1.0, 2.85, 4.8, 3.3, fill=WHITE, line=VIOLET_LIGHT, radius=0.05)
text(s, 1.2, 3.0, 4.4, 0.4, "function count(): local names", size=15, bold=True, color=VIOLET)
text(s, 1.2, 3.45, 3.2, 2.6, ["created at each call,", "gone after return", "", "global clicks → this", "function may change", "the outer clicks"],
     size=15, color=TEXT)
line(s, 4.6, 4.75, 4.6, 2.55, color=VIOLET, width=2.25, arrow=True)
code(s, 6.5, 1.55, 6.23, 2.3, """clicks = 0

def count_wrong():
    clicks = clicks + 1
!NameError: local variable referenced before assignment""", size=13, fill=RGBColor(0xFB, 0xEE, 0xEE), title="without global")
code(s, 6.5, 4.05, 6.23, 2.4, """clicks = 0

def count():
    global clicks
    clicks = clicks + 1

count(); count(); print(clicks)
→2""", size=15, highlight={4}, title="with global")

# =================================================================================
# 17  Lists and dicts
# =================================================================================
s = content_slide("Lists and dicts: collections of values", 11, notes="""
A list [ ] is like a tuple, but it can change: append, change elements. A dict { } maps keys
to values - like a small lookup table. The key can be a number: names[RIGHT] with RIGHT = 1.

Lists, tuples and dicts can hold any values - also Pin and PWM objects. That is one way to
choose the pins of one side in the motor driver; an if/else is another. Both are fine.

Index errors and key errors stop the program with a traceback; the message names the bad key.
""")
code(s, 0.6, 1.55, 6.0, 3.5, """speeds = [10, 50, 80]
speeds.append(100)
print(speeds[0], speeds[-1], len(speeds))
→10 100 4

for s in speeds:
    print(s, "%")""", size=16, title="list [ ]")
code(s, 6.9, 1.55, 5.83, 3.5, """LEFT, RIGHT = 0, 1
names = {LEFT: "left", RIGHT: "right"}

print(names[RIGHT])
→right
names[2]
!KeyError: 2""", size=16, title="dict { key: value }")
table(s, 0.6, 5.3, 12.13, [["", "tuple ( )", "list [ ]", "dict { }"],
                           ["access", "t[0]", "l[0]", "d[key]"],
                           ["change", "no", "l.append(x), l[0] = x", "d[key] = x"]],
      [2.0, 2.8, 3.9, 3.43], size=15, row_h=0.42, mono_cols=(1, 2, 3))

# =================================================================================
# Section: on the Pico
# =================================================================================
section("Part 3: On the Pico", "Time, output, errors", [(12, "Timing without blocking"), (13, "print and f-strings"),
        (14, "Reading error messages"), (15, "The REPL")],
        notes="Part 3: what is special on the microcontroller - time, output, and how to find errors.")

# =================================================================================
# 18  Timing
# =================================================================================
s = content_slide("Time: sleep_ms() blocks, ticks_ms() does not", 12, notes="""
time.sleep_ms(500) stops the program for 500 ms: during that time nothing else happens, a button
press is simply missed. That is fine for a blinking LED, but not for an emergency stop (task 5).

The alternative: a loop that runs every millisecond, asks the clock with ticks_ms() and only acts
when enough time has passed. In between it can check the button.

Always compute time differences with ticks_diff(new, old), never with a minus sign: the ms counter
wraps around (after about 12 days on the Pico), ticks_diff handles that.

The printing in this loop happens on EVERY ms while the button is held - that is why task 2 asks
for edge detection: react only to the change from released to pressed.
""")
# timeline graphic
tx0, tx1 = 0.9, 6.3
for row, (lab, y) in enumerate((("sleep_ms(500)", 2.0), ("loop every 1 ms", 3.4))):
    text(s, 0.6, y - 0.55, 5.8, 0.4, lab, size=15, bold=True, font=MONO, color=VIOLET)
    line(s, tx0, y + 0.35, tx1, y + 0.35, color=GRAY, width=1.25, arrow=True)
    if row == 0:
        b = box(s, tx0, y, (tx1 - tx0) * 0.85, 0.35, fill=VIOLET_LIGHT, radius=0.2)
        shape_text(b, "blocked: nothing else runs", size=12, color=WHITE, bold=True)
    else:
        for k in range(40):
            x = tx0 + k * (tx1 - tx0 - 0.3) / 40
            line(s, x, y + 0.05, x, y + 0.35, color=CYAN, width=1.25)
# button press marker
px = tx0 + (tx1 - tx0) * 0.4
for y, ok in ((2.0, False), (3.4, True)):
    c = box(s, px - 0.22, y + 0.5, 0.44, 0.44, fill=GREEN if ok else RED, shape=MSO_SHAPE.OVAL)
    shape_text(c, "✓" if ok else "✗", size=14, color=WHITE, bold=True)
    text(s, px + 0.3, y + 0.52, 3.0, 0.4, "press seen at once" if ok else "press missed", size=13, color=GREEN if ok else RED)
code(s, 6.75, 1.45, 5.98, 3.45, """last = time.ticks_ms()
while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, last) >= 500:
        last = now
        led.value(not led.value())   # toggle
    if button.value() == 0:
        print("pressed")   # every ms while held!
    time.sleep_ms(1)""", size=14, highlight={4})
table(s, 0.6, 5.15, 12.13, [["Function", "What it does"], ["time.sleep_ms(ms)", "waits, blocks everything"],
                            ["time.ticks_ms()", "ms counter since start (wraps around)"],
                            ["time.ticks_diff(new, old)", "new - old in ms, correct across the wrap"]],
      [3.6, 8.53], size=14, row_h=0.36, mono_cols=(0,))

# =================================================================================
# 19  print
# =================================================================================
s = content_slide("print() and f-strings: see what your program does", 13, notes="""
print() is your most important debugging tool. It takes any number of arguments and separates them
with a space; numbers are converted automatically.

f-strings: an f before the quote, and every {expression} in the string is replaced by its value.
After a colon comes the format, like printf: {x:.2f} = two digits after the point.

Text and numbers cannot be joined with +: "a" + 5 is a TypeError. Use str(5), a comma in print,
or an f-string.

Task 3 asks you to print how long the sequence took: ticks_diff + an f-string.
""")
code(s, 0.6, 1.55, 6.4, 4.5, """print("LED on")
→LED on
print("task", TASK)            # comma: space
→task 2
elapsed = 20004
print(f"took {elapsed} ms")    # f-string
→took 20004 ms
print(f"X = {0.4567:.2f} m")   # 2 decimals
→X = 0.46 m
print("a" + str(5))
→a5""", size=15, highlight={7})
card(s, 7.3, 1.55, 5.43, 2.0, "f\"… {expression} …\"", "Every { } is replaced by the value of the expression. {x:.2f} formats like printf(\"%.2f\").", size=15)
code(s, 7.3, 3.8, 5.43, 1.45, """print("a" + 5)
!TypeError: unsupported types for
!__add__: 'str', 'int'""", size=15, fill=RGBColor(0xFB, 0xEE, 0xEE))
text(s, 7.3, 5.45, 5.43, 1.0, "Text + number does not work. Use a comma, str() or an f-string.", size=15, color=TEXT)

# =================================================================================
# 20  Errors
# =================================================================================
s = content_slide("Reading an error message", 14, notes="""
When MicroPython stops with an error, it prints a traceback in the serial monitor. Read it from
the BOTTOM: the last line says what went wrong, the line above it where: file, line number and
function. Here: line 68 in set_speed, a float was passed to duty_u16. Line 70 is the call that led there.

After the error the program has stopped and you see the REPL prompt >>>. The motors keep their
last state!

The table lists the errors you will most likely meet in the lab, with the exact MicroPython texts.
""")
code(s, 0.6, 1.55, 6.6, 2.9, """Traceback (most recent call last):
  File "main.py", line 70, in <module>
  File "main.py", line 68, in set_speed
!TypeError: can't convert float to int
MicroPython v1.29.0 on 2026-08-24; Raspberry Pi Pico
Type "help()" for more information.
>>>""", size=14, highlight={3, 4}, title="serial monitor")
c1 = box(s, 7.5, 1.55, 0.5, 0.5, fill=RED, shape=MSO_SHAPE.OVAL)
shape_text(c1, "1", size=15, color=WHITE, bold=True)
text(s, 8.15, 1.55, 4.6, 0.5, [[("Last line: what. ", {"bold": True}), ("The type of the error and a message.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE)
c2 = box(s, 7.5, 2.3, 0.5, 0.5, fill=VIOLET, shape=MSO_SHAPE.OVAL)
shape_text(c2, "2", size=15, color=WHITE, bold=True)
text(s, 8.15, 2.3, 4.6, 0.5, [[("Line above: where. ", {"bold": True}), ("File, line, function.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE)
c3 = box(s, 7.5, 3.05, 0.5, 0.5, fill=CYAN_DARK, shape=MSO_SHAPE.OVAL)
shape_text(c3, "3", size=15, color=WHITE, bold=True)
text(s, 8.15, 3.05, 4.6, 0.9, [[(">>> means: ", {"bold": True}), ("your program has stopped. The motors keep running!", {})]], size=15)
table(s, 0.6, 4.7, 12.13, [["Error (MicroPython text)", "Typical cause"],
                           ["SyntaxError: invalid syntax", "missing colon, missing indentation, = instead of =="],
                           ["NameError: name 'Led' isn't defined", "typo; Python is case-sensitive"],
                           ["AttributeError: 'Pin' object has no attribute 'valu'", "typo in a method name"],
                           ["TypeError: can't convert float to int", "result of / passed to duty_u16()"]],
      [6.3, 5.83], size=13, row_h=0.34, mono_cols=(0,))

# =================================================================================
# 21  REPL
# =================================================================================
s = content_slide("The REPL: try one line on the running Pico", 15, notes="""
REPL = Read, Eval, Print, Loop. When main.py has ended or you press Ctrl-C in the serial monitor,
MicroPython shows >>> and you can type Python directly on the (simulated) Pico. Every expression
prints its value.

This is the fastest way to test hardware: switch the LED, read the button, set a duty cycle and
watch the ET1 display. Once your motor() function exists you can call motor(LEFT, 50) by hand -
the names of main.py are still there after Ctrl-C.

Ctrl-D does a soft reset and runs main.py again. help() and dir(obj) show what is available.
""")
code(s, 0.6, 1.55, 6.6, 4.4, """>>> led.value(1)              # red LED on
>>> button.value()
→1
>>> ena.duty_u16(32767)        # 50 % on ENA
>>> in1.value(1); in2.value(0)
>>> dir(led)
→['__class__', 'value', … 'on', 'toggle']
>>> int(65535 * 0.12)        # 12 % dead zone
→7864""", size=15, title="serial monitor after Ctrl-C")
table(s, 7.5, 1.55, 5.23, [["Key", "Effect"], ["Ctrl-C", "stop main.py → >>>"], ["Ctrl-D", "soft reset, main.py runs again"],
                           ["↑", "previous line"], ["Tab", "complete a name"]],
      [1.4, 3.83], size=15, row_h=0.48)
card(s, 7.5, 4.2, 5.23, 1.75, "Test before you write", "Every line that works in the REPL can go into main.py unchanged.", size=15)

# =================================================================================
# 22  MicroPython vs Python
# =================================================================================
s = content_slide("MicroPython is Python - on 264 KB of RAM", notes="""
MicroPython implements the Python 3 language (sys.version says 3.4 plus many later features such as
f-strings) for microcontrollers. The language is the same; what is different is the environment.

machine is the hardware module: Pin, PWM, ADC, I2C, SPI, UART, Timer. time has extra functions
ticks_ms, ticks_diff, sleep_ms.

Only a small standard library: no numpy, no pandas. Speed: an interpreter is roughly 10 to 100
times slower than C - for a robot that reacts in milliseconds that is plenty, for a 100 kHz control
loop it is not (see chapter Programming). Memory is managed by a garbage collector: after start
about 220 KB are free on the Pico.
""")
items = [("machine", "Pin, PWM, ADC, I2C, SPI, UART, Timer: the hardware as objects", VIOLET),
         ("time", "sleep_ms(), ticks_ms(), ticks_diff(): extra functions for µCs", CYAN_DARK),
         ("small library", "no numpy, no pandas; what exists: math, random, struct, json …", VIOLET),
         ("slower than C", "interpreter: roughly 10 … 100 × slower; ms reaction is fine", CYAN_DARK),
         ("garbage collector", "memory is freed automatically; ~220 KB free after start", VIOLET),
         ("same language", "if, for, def, lists, dicts, f-strings: as in Python on the PC", CYAN_DARK)]
for i, (h, d, col) in enumerate(items):
    cx = 0.6 + (i % 3) * 4.14
    cy = 1.6 + (i // 3) * 2.45
    box(s, cx, cy, 3.95, 2.2, fill=VIOLET_TINT, radius=0.06)
    c = box(s, cx + 0.25, cy + 0.25, 0.55, 0.55, fill=col, shape=MSO_SHAPE.OVAL)
    shape_text(c, str(i + 1), size=15, color=WHITE, bold=True)
    text(s, cx + 0.95, cy + 0.25, 2.85, 0.55, h, size=18, bold=True, color=col, anchor=MSO_ANCHOR.MIDDLE)
    text(s, cx + 0.25, cy + 1.0, 3.5, 1.1, d, size=15)
text(s, 0.6, 6.5, 12.1, 0.4, "Measured in Wokwi: MicroPython v1.29.0, gc.mem_free() = 226 720 bytes after start", size=12, color=GRAY)

# =================================================================================
# 23  Cheat sheet
# =================================================================================
s = content_slide("Cheat sheet: C → MicroPython", notes="""
One table to keep open during the lab. Everything on it appeared on the slides before.
""")
table(s, 0.6, 1.5, 12.13, [["", "C", "MicroPython"],
                           ["block", "if (x > 0) { … }", "if x > 0:  + indentation"],
                           ["variable", "int speed = 50;", "speed = 50"],
                           ["logic", "&&   ||   !", "and   or   not"],
                           ["division", "7 / 2 → 3", "7 // 2 → 3,   7 / 2 → 3.5"],
                           ["loop", "for (i = 0; i < 5; i++)", "for i in range(5):"],
                           ["function", "int f(int a) { return a; }", "def f(a):  return a"],
                           ["global state", "static int last;", "last = 0  +  global last"],
                           ["output", 'printf("%d ms\\n", t);', 'print(f"{t} ms")'],
                           ["GPIO", "digitalWrite(7, HIGH);", "led.value(1)"],
                           ["PWM", "analogWrite(18, 128);", "ena.duty_u16(32767)"],
                           ["wait", "delay(500);", "time.sleep_ms(500)"]],
      [2.2, 4.8, 5.13], size=15, row_h=0.43, mono_cols=(1, 2))

# =================================================================================
# 24  Tour of main.py
# =================================================================================
s = content_slide("Tour of main.py: what is given, what is yours", notes="""
main.py from top to bottom. Given: imports, TASK, the pin objects (exactly the lines from the
objects slide), LEFT/RIGHT and button_down(). Then the task functions with docstrings and numbered
TODO comments - that is your part. At the end the main loop, also given.

Order of work: task 1 (motor) is tested in tasks 3 and 4. Start with task 2 to get used to the
workflow, then 1 and 3, then 4 and finally 5 (emergency stop), which changes 3 and 4.

Concept numbers on the right (the cyan circles on the slides): which concepts you need for which task.
""")
blocks = [("import time · from machine import Pin, PWM · TASK = 2", "given", LIGHTGRAY, TEXT, 0.5),
          ("led, button, ena, in1 … in4 · LEFT, RIGHT · button_down()", "given", LIGHTGRAY, TEXT, 0.5),
          ("Task 1  motor(side, speed), stop()", "TODO 1a-d", VIOLET, WHITE, 0.55),
          ("Task 2  button_clicked(), task2()", "TODO 2a-c", VIOLET, WHITE, 0.55),
          ("Task 5  wait_ms(ms)", "TODO 5a-b", VIOLET, WHITE, 0.55),
          ("Task 3  task3()", "TODO 3", VIOLET, WHITE, 0.55),
          ("Task 4  ramp(direction), task4()", "TODO 4a-c", VIOLET, WHITE, 0.55),
          ("stop() · print(\"ET1 ready\") · while True: run task TASK", "given", LIGHTGRAY, TEXT, 0.5)]
y = 1.5
for lab, tag, fill, fc, h in blocks:
    b = box(s, 0.6, y, 7.3, h, fill=fill, radius=0.12)
    shape_text(b, lab, size=13 if fill != VIOLET else 15, color=fc, bold=fill == VIOLET, align=PP_ALIGN.LEFT, font=MONO if fill != VIOLET else FONT)
    text(s, 8.0, y, 1.3, h, tag, size=13, color=GRAY if fill != VIOLET else VIOLET, bold=fill == VIOLET, anchor=MSO_ANCHOR.MIDDLE)
    y += h + 0.1
table(s, 9.45, 1.5, 3.28, [["Task", "Concepts"], ["1", "3, 4, 5, 6, 11"], ["2", "6, 10, 12"], ["3", "9, 12, 13"],
                           ["4", "3, 8, 9"], ["5", "7, 9, 12"]],
      [0.9, 2.38], size=15, row_h=0.5)
text(s, 9.45, 4.65, 3.28, 1.2, "Set TASK at the top to the task you are working on.", size=14, color=GRAY)

# =================================================================================
# 25  Your turn
# =================================================================================
s = dark_slide(notes="""
Start with task 2: it needs only the button and the LED and gets you used to build, start, read
the serial monitor. Then the motor driver. Test it in the REPL with motor(LEFT, 50) and watch L
on the display before you write the sequences.

How to check each task is in the task sheet ("Done when" boxes) and in README.md.
""")
text(s, 0.9, 0.8, 11, 1.0, "Your turn", size=48, bold=True, color=WHITE)
text(s, 0.9, 1.75, 11, 0.6, "Lab/2-programming/python/main.py · task sheet: Lab_2_Programming.pdf", size=18,
     color=RGBColor(0x99, 0xDD, 0xFD), font=MONO)
steps = [("2", "Button + LED", "edge detection,\n30 ms debounce"), ("1", "motor()", "test in the REPL:\nmotor(LEFT, 50)"),
         ("3", "Turning", "two circles,\n20 s"), ("4", "Ramp + trim", "D ends at 0.00"), ("5", "Emergency stop", "a click stops ET1")]
for i, (n, h, d) in enumerate(steps):
    x = 0.9 + i * 2.38
    c = box(s, x, 2.9, 0.75, 0.75, fill=CYAN, shape=MSO_SHAPE.OVAL)
    shape_text(c, n, size=22, color=WHITE, bold=True)
    text(s, x, 3.85, 2.2, 0.45, h, size=19, bold=True, color=WHITE)
    text(s, x, 4.3, 2.2, 0.9, d, size=15, color=VIOLET_LIGHT)
    if i < len(steps) - 1:
        line(s, x + 0.85, 3.275, x + 2.3, 3.275, color=VIOLET_LIGHT, width=1.5, arrow=True)
tips = [("Small steps:", " build and run after every few lines."), ("print() everything", " you are not sure about."),
        ("Read the traceback", " from the bottom up.")]
text(s, 0.9, 5.55, 11.5, 1.0, [[(a, {"bold": True, "color": WHITE}), (b, {"color": RGBColor(0x99, 0xDD, 0xFD)})] for a, b in tips],
     size=16, space_after=2)
footer(s, dark=True)

prs.save(OUT)
print("wrote", OUT, "slides:", slide_no)
