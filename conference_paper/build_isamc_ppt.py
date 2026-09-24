#!/usr/bin/env python3
"""Build the ISAMC conference talk deck from conference_paper/Paper.pdf content.

Every number is taken verbatim from the accepted paper. Figures are the
paper's own figures (paper2/figures). Every slide has speaker notes: a plain-
English script first, then a "Terms" block explaining the technical words.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

CODE = "/Users/sisirreddy/project_phase/CODE"
FIG = os.path.join(CODE, "paper2", "figures")
OUT = os.path.join(CODE, "conference_paper", "ISAMC_Presentation.pptx")

# ---------------------------------------------------------------- palette
NAVY = RGBColor(0x0F, 0x2A, 0x4A)
TEAL = RGBColor(0x0E, 0x8A, 0x7B)
ORANGE = RGBColor(0xD9, 0x62, 0x2B)
RED = RGBColor(0xB8, 0x3A, 0x2E)
INK = RGBColor(0x1F, 0x29, 0x33)
MUTED = RGBColor(0x5F, 0x6B, 0x7A)
LIGHT = RGBColor(0xF3, 0xF5, 0xF8)
LINE = RGBColor(0xD5, 0xDB, 0xE3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]

TOTAL = 24  # updated at the end for footer numbering
slide_no = [0]


# ---------------------------------------------------------------- helpers
def _run(p, text, size, bold=False, color=INK, italic=False, font=FONT):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    r.font.color.rgb = color
    return r


def textbox(slide, x, y, w, h, text="", size=18, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, font=FONT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    _run(p, text, size, bold, color, italic, font)
    return tb


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    return s


def bullets(slide, x, y, w, h, items, size=18, color=INK, gap=6):
    """items: list of str or (str, level) or (str, level, bold)."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    first = True
    for it in items:
        if isinstance(it, str):
            txt, lvl, bold = it, 0, False
        elif len(it) == 2:
            txt, lvl = it
            bold = False
        else:
            txt, lvl, bold = it
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        p.level = lvl
        marker = "•  " if lvl == 0 else "–  "
        sz = size if lvl == 0 else size - 2
        if lvl:
            p.left_indent = Inches(0.35)
        _run(p, marker + txt, sz, bold, color if lvl == 0 else MUTED)
    return tb


def picture(slide, path, x, y, max_w, max_h, align="center"):
    """Place image fitted inside the box, keeping aspect ratio."""
    im = Image.open(path)
    iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    if align == "center":
        x = x + (max_w - w) // 2
    y = y + (max_h - h) // 2
    return slide.shapes.add_picture(path, x, y, w, h)


def stat_card(slide, x, y, w, h, number, label, accent=TEAL):
    rect(slide, x, y, w, h, LIGHT)
    rect(slide, x, y, Inches(0.08), h, accent)
    textbox(slide, x + Inches(0.2), y + Inches(0.1), w - Inches(0.3), Inches(0.75),
            number, size=30, bold=True, color=accent)
    textbox(slide, x + Inches(0.2), y + Inches(0.8), w - Inches(0.3), h - Inches(0.85),
            label, size=13, color=INK)


def notes(slide, script, terms=None):
    txt = "SCRIPT\n" + script.strip()
    if terms:
        txt += "\n\nTERMS TO EXPLAIN IF ASKED\n" + "\n".join(
            f"• {k}: {v}" for k, v in terms)
    slide.notes_slide.notes_text_frame.text = txt


def base_slide(title, kicker=None):
    """Content slide with title band and footer."""
    slide_no[0] += 1
    s = prs.slides.add_slide(BLANK)
    # title band
    rect(s, 0, 0, W, Inches(1.05), NAVY)
    rect(s, 0, Inches(1.05), W, Inches(0.06), TEAL)
    textbox(s, Inches(0.5), Inches(0.14), Inches(12.3), Inches(0.8), title,
            size=30, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if kicker:
        textbox(s, Inches(0.5), Inches(1.18), Inches(12.3), Inches(0.45), kicker,
                size=15, color=MUTED, italic=True)
    # footer
    rect(s, 0, H - Inches(0.4), W, Inches(0.4), LIGHT)
    textbox(s, Inches(0.5), H - Inches(0.38), Inches(9), Inches(0.35),
            "ISAMC 2026  ·  Multi-Protocol Cyber-Deception Framework  ·  Amrita Vishwa Vidyapeetham",
            size=10, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, W - Inches(1.6), H - Inches(0.38), Inches(1.1), Inches(0.35),
            f"{slide_no[0]}", size=10, color=MUTED, align=PP_ALIGN.RIGHT,
            anchor=MSO_ANCHOR.MIDDLE)
    return s


def section_slide(number, title, subtitle):
    slide_no[0] += 1
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, H, NAVY)
    rect(s, Inches(0.8), Inches(3.05), Inches(1.2), Inches(0.08), TEAL)
    textbox(s, Inches(0.8), Inches(1.9), Inches(11), Inches(1), number,
            size=22, color=TEAL, bold=True)
    textbox(s, Inches(0.8), Inches(3.25), Inches(11.5), Inches(1.2), title,
            size=40, bold=True, color=WHITE)
    textbox(s, Inches(0.8), Inches(4.45), Inches(11.5), Inches(1.2), subtitle,
            size=18, color=RGBColor(0xC9, 0xD4, 0xE0))
    return s


CY = Inches(1.35)             # content top (no kicker)
CYK = Inches(1.7)             # content top (with kicker)
CH = H - Inches(0.5) - CY     # content height


# ================================================================ SLIDE 1
slide_no[0] += 1
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, NAVY)
rect(s, 0, Inches(5.3), W, Inches(0.06), TEAL)
textbox(s, Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.5),
        "ISAMC 2026  ·  Conference Presentation", size=16, color=TEAL, bold=True)
textbox(s, Inches(0.8), Inches(1.4), Inches(11.7), Inches(2.6),
        "A Multi-Protocol Cyber-Deception Framework Combining Language-Model "
        "Response Synthesis with Blockchain-Anchored Forensic Logging",
        size=34, bold=True, color=WHITE)
textbox(s, Inches(0.8), Inches(4.05), Inches(11.7), Inches(0.5),
        "A honeypot that talks back like a real server — and whose evidence cannot be silently edited.",
        size=18, color=RGBColor(0xC9, 0xD4, 0xE0), italic=True)
textbox(s, Inches(0.8), Inches(5.55), Inches(11.7), Inches(0.9),
        "Radhika G,  Sisir Reddy Nellore,  Pranav Sharma Chouduru,  Surya Tejeswar Reddy Nagireddy,\n"
        "Guru Sai Prasad Reddy Bompalli,  Vishnu Sathwick Rajala",
        size=15, color=WHITE)
textbox(s, Inches(0.8), Inches(6.45), Inches(11.7), Inches(0.6),
        "Department of Computer Science and Engineering  ·  Amrita School of Computing, Coimbatore  ·  "
        "Amrita Vishwa Vidyapeetham, India", size=13, color=RGBColor(0xC9, 0xD4, 0xE0))
notes(s, """
Good morning everyone. I am Sisir Reddy Nellore from Amrita Vishwa Vidyapeetham, Coimbatore, and I will present our paper
"A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging".

In one sentence: we built a honeypot — a fake server that exists only to be attacked — where an AI language model writes the replies
so it looks real, and where every attack record is fingerprinted onto a blockchain so nobody, not even an attacker who breaks into the honeypot,
can change the evidence without being caught.

The talk is about 15 minutes: the problem, our design, how we tested it, what worked, and — honestly — what did not.
""", [
    ("Cyber deception", "Defensive technique: plant fake systems/data so attackers waste time on decoys and reveal themselves."),
    ("Language model (LM/LLM)", "An AI model (like ChatGPT / Llama) that generates text. We use it to generate fake server output."),
    ("Forensic logging", "Recording attack evidence in a way that can later be used to investigate or prove what happened."),
    ("Blockchain-anchored", "A short fingerprint (hash) of each record is written onto a blockchain, which cannot be rewritten."),
])

# ================================================================ SLIDE 2 — roadmap
s = base_slide("What this talk covers")
items = [
    ("1", "The problem", "Honeypots are easy to unmask, and their logs are easy to tamper with"),
    ("2", "Our idea", "Let a language model write replies; anchor every record's hash on a blockchain"),
    ("3", "The system", "Five decoys · three-tier response path · intent classifier · on-chain logging · dashboard"),
    ("4", "Evaluation", "2,500 real attack payloads · latency, throughput, diversity, realism · tamper test"),
    ("5", "Honest findings", "Where it works, where it is weak (AI-API decoy), and 3 engineering bugs we fixed"),
    ("6", "Comparison & future", "Versus Cowrie, ShelLM, HoneyLLM · limitations · next steps"),
]
y = CY + Inches(0.1)
for n, t, d in items:
    rect(s, Inches(0.6), y, Inches(0.7), Inches(0.7), TEAL, shape=MSO_SHAPE.OVAL)
    textbox(s, Inches(0.6), y, Inches(0.7), Inches(0.7), n, size=20, bold=True,
            color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(1.5), y - Inches(0.05), Inches(3.2), Inches(0.8), t, size=22, bold=True,
            color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(4.7), y - Inches(0.05), Inches(8.2), Inches(0.8), d, size=17,
            color=INK, anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.9)
notes(s, """
Here is the roadmap. I will start with why existing honeypots fail, then our two-part idea, then walk through the architecture piece by piece.
After that, the evaluation on 2,500 real attack strings, and I will spend real time on the honest findings — including one decoy that
underperforms and three bugs we caught in our own benchmark — because for a system whose job is trustworthy evidence, transparent reporting is part of the contribution.
""")

# ================================================================ SLIDE 3 — what is a honeypot
s = base_slide("First, what is a honeypot?", "The plain-English version")
rect(s, Inches(0.6), CYK, Inches(6.0), Inches(4.9), LIGHT)
textbox(s, Inches(0.85), CYK + Inches(0.15), Inches(5.6), Inches(0.5),
        "Think of a decoy house", size=20, bold=True, color=NAVY)
bullets(s, Inches(0.85), CYK + Inches(0.7), Inches(5.6), Inches(4.1), [
    "A fake server put on the network on purpose",
    "It has no real users — so anyone who touches it is, by definition, suspicious",
    "Every command the attacker types is recorded",
    "Defenders learn: who is attacking, what tools they use, what they want",
    "Cheap, low risk, high-signal — a standard sensor in security teams",
], size=17)
rect(s, Inches(6.9), CYK, Inches(5.85), Inches(4.9), WHITE, line=LINE)
textbox(s, Inches(7.15), CYK + Inches(0.15), Inches(5.4), Inches(0.5),
        "How today's cheap honeypots work", size=20, bold=True, color=NAVY)
bullets(s, Inches(7.15), CYK + Inches(0.7), Inches(5.4), Inches(4.1), [
    "They do NOT run a real operating system (too risky, too costly)",
    "They pretend, using a hand-written table of canned answers:",
    ("attacker types  ls   →  reply: \"file1  file2\"", 1),
    ("attacker types  whoami  →  reply: \"root\"", 1),
    "Examples: Cowrie, Kippo (SSH), Dionaea (malware capture)",
    "Anything NOT in the table → wrong, missing, or identical reply",
], size=17)
notes(s, """
Before the problem, one minute on what a honeypot is, for anyone outside security.
A honeypot is a decoy server deployed on purpose. It has no legitimate users, so any connection to it is suspicious by definition.
It silently records everything the attacker does, so defenders learn who is attacking and how.

The popular low-cost honeypots — Cowrie, Kippo — do not run a real operating system. They fake it using a lookup table:
if the attacker types "ls" reply with this string, if "whoami" reply "root". That is cheap and safe.
But the table is finite. Type something not in the table and the honeypot answers wrongly, or not at all. That is the crack we are going to widen on the next slide.
""", [
    ("Low / medium-interaction honeypot", "Emulates a service with scripted logic instead of running the real thing. Cheap and safe but shallow."),
    ("High-interaction honeypot", "A real full OS used as bait. Very realistic but expensive and dangerous if the attacker escapes."),
    ("SSH", "Secure Shell — the remote command-line login used to administer Linux servers; the most-attacked service on the Internet."),
    ("Telemetry", "The data/records collected by a sensor — here, attacker connections, commands and payloads."),
])

# ================================================================ SLIDE 4 — problem 1
s = base_slide("Problem 1 — Static honeypots are easy to unmask", "A finite answer table can always be enumerated")
bullets(s, Inches(0.6), CYK, Inches(6.6), Inches(3.4), [
    "A scanner sends a few unusual commands and watches the replies",
    "Replies come from a finite, deterministic set → identical across 'different' hosts",
    "Conclusion in seconds: \"this is a decoy\" → the attacker leaves",
    "Bigger tables do not help — any static set is still enumerable",
    ("This is a structural flaw, not a tuning problem", 0, True),
], size=18)
stat_card(s, Inches(7.6), CYK, Inches(5.1), Inches(1.5), "1 packet",
          "Vetterl & Clayton (USENIX WOOT 2018) fingerprinted low/medium-interaction honeypots with a single packet", ORANGE)
stat_card(s, Inches(7.6), CYK + Inches(1.7), Inches(5.1), Inches(1.5), "2,844",
          "real Cowrie / Kippo honeypots identified on the public Internet", ORANGE)
stat_card(s, Inches(7.6), CYK + Inches(3.4), Inches(5.1), Inches(1.5), "EER 0.0183",
          "Equal-error rate — the detector was wrong less than 2% of the time", ORANGE)
rect(s, Inches(0.6), CYK + Inches(3.6), Inches(6.6), Inches(1.3), NAVY)
textbox(s, Inches(0.85), CYK + Inches(3.7), Inches(6.2), Inches(1.1),
        "What is needed: a GENERATIVE reply mechanism — one that can produce a plausible, "
        "in-character answer to a request it has never seen before.",
        size=16, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
notes(s, """
Problem one. Because the answer table is finite, an automated scanner only needs to send a handful of odd requests and observe that
the replies are drawn from a fixed set — or are identical across supposedly different hosts. It then concludes "decoy" and disengages.
This is not a matter of writing a bigger table: any finite static set can be enumerated.

This was demonstrated at Internet scale by Vetterl and Clayton in 2018: with a single packet they fingerprinted these honeypots
with an equal-error rate of 0.0183 and located 2,844 real Cowrie and Kippo instances in the wild.

So the requirement is a reply mechanism that is generative rather than tabular — something that can invent a plausible, consistent reply to a never-seen request.
""", [
    ("Fingerprinting", "Identifying what software a remote machine runs from tiny behavioural quirks in its replies."),
    ("Equal-error rate (EER)", "The error rate at the point where false positives equal false negatives; 0.0183 means ~1.8% error — a very accurate detector."),
    ("Deterministic", "Same input always gives exactly the same output — a tell-tale sign of a scripted decoy."),
    ("Enumerable", "Can be fully listed out. A finite table of answers can be discovered by trying inputs."),
])

# ================================================================ SLIDE 5 — problem 2
s = base_slide("Problem 2 — The evidence lives on the machine being attacked", "A log file is only as trustworthy as the host that holds it")
rect(s, Inches(0.6), CYK, Inches(12.1), Inches(1.9), LIGHT)
steps = ["Attacker breaks into the honeypot", "Finds the log file of their own intrusion",
         "Edits or deletes the records", "Investigator sees nothing — or a false story"]
x = Inches(0.8)
for i, t in enumerate(steps):
    col = RED if i == 3 else NAVY
    rect(s, x, CYK + Inches(0.35), Inches(2.6), Inches(1.2), col, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    textbox(s, x + Inches(0.1), CYK + Inches(0.35), Inches(2.4), Inches(1.2), t, size=15,
            color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        textbox(s, x + Inches(2.6), CYK + Inches(0.35), Inches(0.4), Inches(1.2), "→", size=26,
                color=MUTED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    x += Inches(3.0)
bullets(s, Inches(0.6), CYK + Inches(2.2), Inches(12.1), Inches(2.9), [
    "A honeypot's whole purpose is to be attacked — so we must assume it CAN be compromised",
    "If the only copy of the audit trail is on that host, the attacker can rewrite history",
    "For logs to count as forensic evidence they need an integrity guarantee that survives compromise of the logger itself",
    ("Requirement: tamper-EVIDENCE that does not depend on trusting the honeypot host", 0, True),
], size=18)
notes(s, """
Problem two is separate and, we argue, equally important. A honeypot log that is just a file on the honeypot is only as trustworthy as that machine.
But the honeypot's entire job is to get attacked, so we must assume a capable attacker can compromise it — and then edit or delete the records of their own intrusion.

If we want to use that telemetry as evidence — in an incident report, or in court — the audit trail needs an integrity guarantee that holds
even when the logging machine itself is compromised. Note we ask for tamper-EVIDENCE, not tamper-proofing: we cannot stop an attacker from editing a file,
but we can make sure the edit is always detectable.
""", [
    ("Audit trail", "The chronological record of events, kept for later review."),
    ("Tamper-evident vs tamper-proof", "Tamper-proof = cannot be changed. Tamper-evident = can be changed, but any change is detectable. We guarantee the latter."),
    ("Compromised host", "A machine the attacker has gained control of."),
])

# ================================================================ SLIDE 6 — our idea
s = base_slide("Our idea — fix both problems in one framework")
rect(s, Inches(0.6), CY + Inches(0.1), Inches(5.9), Inches(2.45), LIGHT)
rect(s, Inches(0.6), CY + Inches(0.1), Inches(0.1), Inches(2.45), TEAL)
textbox(s, Inches(0.9), CY + Inches(0.2), Inches(5.5), Inches(0.5), "Realism → a language model writes the replies",
        size=19, bold=True, color=NAVY)
bullets(s, Inches(0.9), CY + Inches(0.7), Inches(5.5), Inches(1.8), [
    "Replace the fixed table with an LM that emulates the service",
    "Answers any request, keeps session context, no finite set to enumerate",
    "Tiered: fast table → cache → LM only for novel input",
], size=15)
rect(s, Inches(6.8), CY + Inches(0.1), Inches(5.9), Inches(2.45), LIGHT)
rect(s, Inches(6.8), CY + Inches(0.1), Inches(0.1), Inches(2.45), ORANGE)
textbox(s, Inches(7.1), CY + Inches(0.2), Inches(5.5), Inches(0.5), "Integrity → hash every record onto a blockchain",
        size=19, bold=True, color=NAVY)
bullets(s, Inches(7.1), CY + Inches(0.7), Inches(5.5), Inches(1.8), [
    "Each interaction → SHA-256 digest → transaction on an Ethereum chain",
    "Later: re-hash the stored record, compare with the on-chain value",
    "Any edit changes the hash → tampering is detected",
], size=15)
textbox(s, Inches(0.6), CY + Inches(2.75), Inches(12), Inches(0.5), "Three contributions of the paper",
        size=20, bold=True, color=NAVY)
contrib = [
    ("C1", "Multi-protocol LM-backed deception layer", "5 decoys (SSH, SQL, AI API, Ethereum RPC, CI/CD) behind one proxy, with a three-tier response path"),
    ("C2", "Blockchain-anchored forensic logging", "Every record hashed and committed on-chain — tamper-evidence independent of the honeypot host"),
    ("C3", "Four-axis honest evaluation", "2,500 real payloads · latency / concurrency / diversity / realism · failure modes reported explicitly"),
]
y = CY + Inches(3.3)
for tag, t, d in contrib:
    rect(s, Inches(0.6), y, Inches(0.9), Inches(0.62), NAVY)
    textbox(s, Inches(0.6), y, Inches(0.9), Inches(0.62), tag, size=17, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(1.65), y - Inches(0.03), Inches(4.2), Inches(0.68), t, size=15, bold=True, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(5.9), y - Inches(0.03), Inches(6.9), Inches(0.68), d, size=13, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.75)
notes(s, """
Our idea addresses both problems together.
For realism, we replace the fixed table with a language model that is prompted to behave like the service — a shell, a database, and so on.
It can answer any request and keep the session consistent, so there is no finite set to enumerate. But — and this matters — we do not send every request to the model,
because that would be slow and expensive. We use a tiered path: static table first, cache second, model only for genuinely new input.

For integrity, every interaction is hashed with SHA-256 and the hash is written as a transaction on an Ethereum blockchain.
Later, anyone can re-hash the stored record and compare. If even one character was changed, the hash differs and the tampering is exposed.

The paper's three contributions are: the multi-protocol LM-backed deception layer, the blockchain-anchored logging, and an honest four-axis evaluation on real attack data.
""", [
    ("SHA-256", "A cryptographic hash function: turns any data into a fixed 256-bit fingerprint. Changing one byte of input gives a completely different fingerprint, and it is infeasible to find two inputs with the same fingerprint."),
    ("Ethereum", "A public blockchain platform. We run a local (private) Ethereum node; we only store hashes on it, never the raw logs."),
    ("Transaction (tx)", "A record written onto the blockchain; once mined into a block it is practically immutable."),
    ("Multi-protocol", "Covers several different network services / attack surfaces, not just SSH."),
])

# ================================================================ SLIDE 7 — threat model & goals
s = base_slide("Threat model and design goals", "Who are we fooling, and what must the system guarantee?")
rect(s, Inches(0.6), CYK, Inches(5.6), Inches(4.9), LIGHT)
textbox(s, Inches(0.85), CYK + Inches(0.15), Inches(5.2), Inches(0.5), "Two kinds of adversary", size=19, bold=True, color=NAVY)
bullets(s, Inches(0.85), CYK + Inches(0.7), Inches(5.2), Inches(4.1), [
    ("Automated scanner", 0, True),
    ("High-rate bot, stereotyped requests, moves on fast", 1),
    ("Detects decoys via deterministic / inconsistent replies", 1),
    ("Stresses: breadth, consistency, latency uniformity", 1),
    ("Interactive intruder", 0, True),
    ("Human at a shell, exploring at human speed", 1),
    ("Issues novel, context-dependent commands", 1),
    ("Stresses: in-character answers to unseen input", 1),
    ("Plus: the honeypot host itself may be compromised", 0, True),
], size=17, gap=5)
rect(s, Inches(6.5), CYK, Inches(6.2), Inches(4.9), WHITE, line=LINE)
textbox(s, Inches(6.75), CYK + Inches(0.15), Inches(5.8), Inches(0.5), "Six design goals (each is measured later)", size=19, bold=True, color=NAVY)
goals = [
    ("G1", "Non-enumerable responses", "→ diversity"),
    ("G2", "Handle never-seen input in character", "→ realism"),
    ("G3", "Latency like a real service", "→ latency"),
    ("G4", "Cover multiple protocols", "→ 5 decoys"),
    ("G5", "Host-independent log integrity", "→ tamper test"),
    ("G6", "Explainable attack-intent labels", "→ classifier"),
]
y = CYK + Inches(0.75)
for g, t, m in goals:
    rect(s, Inches(6.75), y, Inches(0.6), Inches(0.5), TEAL)
    textbox(s, Inches(6.75), y, Inches(0.6), Inches(0.5), g, size=13, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(7.45), y, Inches(3.6), Inches(0.5), t, size=14, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(11.0), y, Inches(1.6), Inches(0.5), m, size=13, color=TEAL, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.65)
notes(s, """
We designed against two adversaries. The automated scanner is a bot: fast, non-interactive, sends a few standard probes and leaves. Field studies show the
overwhelming majority of honeypot traffic is this kind. It fingerprints by looking for deterministic or inconsistent replies. The interactive intruder is a human
who has reached a shell and explores at human speed with novel commands. The scanner stresses breadth and timing; the intruder stresses novel-input handling.
We additionally assume the honeypot host may be compromised, so integrity cannot rely on trusting it.

From that we derived six goals, G1 to G6, and — importantly — each maps to a specific measurement later in the talk, so you can check whether we met them.
We claim tamper-evidence, not confidentiality: we assume SHA-256 and the ledger are cryptographically sound.
""", [
    ("Threat model", "A precise statement of what the attacker can do and what we assume; every security design must state one."),
    ("Latency uniformity", "If every reply takes exactly the same suspicious multi-second delay, timing alone reveals a decoy."),
])

# ================================================================ SECTION — architecture
section_slide("Part 2", "System architecture", "Five decoys · one proxy · a tiered response engine · a collector that classifies, hashes and anchors")
notes(prs.slides[-1], "Now the architecture. I will show the big picture first, then zoom into each component.")

# ================================================================ SLIDE 9 — architecture figure
s = base_slide("Architecture at a glance", "Only the proxy and the dashboard face the outside; everything else lives on an isolated internal network")
picture(s, os.path.join(FIG, "diag_arch.png"), Inches(0.5), CYK, Inches(8.0), Inches(4.9))
bullets(s, Inches(8.7), CYK, Inches(4.2), Inches(4.9), [
    ("Public boundary", 0, True),
    ("Connection proxy — the single entry point", 1),
    ("Dashboard — operator's view", 1),
    ("Isolated internal network", 0, True),
    ("5 decoy services", 1),
    ("Tiered response engine (static · cache · LM)", 1),
    ("Collector: classify → hash → store → anchor → stream", 1),
    ("Redis datastore + local Ethereum chain", 1),
    ("Attacker can never reach the control plane directly", 0, True),
], size=15, gap=3)
notes(s, """
This is Figure 1 from the paper. Everything runs as containers on an isolated bridge network.
Only two components are reachable from outside: the connection proxy, which fronts the decoys, and the monitoring dashboard.
The attacker connects to the proxy; the proxy forwards to the right decoy. The decoy asks the tiered response engine for a reply, which goes to the
hosted LM API only for novel requests. Every interaction is posted to the collector, which classifies intent, computes the SHA-256 hash, stores the full record in Redis,
anchors the hash on the Ethereum chain, and streams the event live to the dashboard.
Because decoys, engine, datastore and chain are internal-only, an attacker inside a decoy cannot reach the control plane.
""", [
    ("Containerised / bridge network", "Each component runs in its own Docker container; a bridge network is a private virtual network between them."),
    ("Proxy", "A relay that accepts the connection and forwards it — here it also logs every connection before anything else happens."),
    ("Redis", "A fast in-memory key-value datastore; holds the full records and the response cache."),
    ("Control plane", "The management components (collector, datastore, chain) as opposed to the attacker-facing decoys."),
])

# ================================================================ SLIDE 10 — proxy + data flow
s = base_slide("The connection proxy and one interaction's journey", "Log first, respond second — even a bare port scan is captured")
picture(s, os.path.join(FIG, "diag_flow.png"), Inches(0.5), CYK, Inches(12.3), Inches(2.6))
bullets(s, Inches(0.6), CYK + Inches(2.8), Inches(12.1), Inches(2.3), [
    "One asynchronous proxy listens on all five public ports and forwards each connection to the right internal decoy",
    "Records source address + target port BEFORE any decoy responds → a scan that never completes a handshake is still logged",
    "Single choke point for connection-level telemetry; decoys stay off the public interface",
    "Then: decoy → tiered engine → reply; collector → classify → SHA-256 → store → anchor on-chain → stream to dashboard",
], size=16)
notes(s, """
This is Figure 2 — the sequence for one interaction. A single asynchronous proxy listens on the five public ports and forwards each connection to the matching decoy.
The key design decision: it logs the source address and port before any decoy replies. So even a bare port scan that never completes a protocol handshake is captured.
It also gives us one choke point for connection telemetry and keeps the decoys off the public interface.
After the decoy replies, the collector does its five steps: classify the intent, hash, store, anchor the hash on-chain, and push the event to the live dashboard.
""", [
    ("Asynchronous", "Handles many connections at once without blocking on any single one."),
    ("Port", "A numbered door on a server; each service listens on one (e.g. SSH on 22, PostgreSQL on 5432)."),
    ("Handshake", "The initial exchange that sets up a protocol session. Scanners often connect and leave without completing it."),
])

# ================================================================ SLIDE 11 — five decoys
s = base_slide("Five decoys — five modern attack surfaces", "Prior LLM honeypots cover one surface (a Linux shell); we cover five")
hdr = ["Decoy", "Port", "What it pretends to be", "What it baits"]
rows = [
    ("SSH shell", "2222", "Corporate Ubuntu database host; accepts any password; interactive shell", "Brute-force logins, recon, reverse shells, priv-esc"),
    ("PostgreSQL", "5433", "SQL endpoint returning plausible tables or realistic errors", "SQL injection"),
    ("Internal AI API", "8080", "'Internal' chat / prediction service", "Prompt injection, jailbreaks, XXE / SSRF probes"),
    ("Ethereum JSON-RPC", "8545", "Exposed blockchain node", "Wallet enumeration & draining (crypto theft)"),
    ("Jenkins CI/CD", "9090", "Build server with script endpoints", "Supply-chain / CI-CD abuse, RCE"),
]
colw = [Inches(2.2), Inches(0.9), Inches(5.0), Inches(4.0)]
x0, y = Inches(0.6), CYK
x = x0
for i, h in enumerate(hdr):
    rect(s, x, y, colw[i], Inches(0.5), NAVY)
    textbox(s, x + Inches(0.08), y, colw[i] - Inches(0.1), Inches(0.5), h, size=14, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    x += colw[i]
y += Inches(0.5)
for r_i, row in enumerate(rows):
    x = x0
    for i, c in enumerate(row):
        rect(s, x, y, colw[i], Inches(0.78), LIGHT if r_i % 2 == 0 else WHITE, line=LINE)
        textbox(s, x + Inches(0.08), y, colw[i] - Inches(0.1), Inches(0.78), c, size=13,
                bold=(i == 0), color=NAVY if i == 0 else INK, anchor=MSO_ANCHOR.MIDDLE)
        x += colw[i]
    y += Inches(0.78)
textbox(s, Inches(0.6), y + Inches(0.1), Inches(12.1), Inches(0.5),
        "Each decoy forwards a normalised record of every interaction to the central collector.",
        size=14, color=MUTED, italic=True)
notes(s, """
The five decoys were chosen to cover distinct, currently relevant attack surfaces.
The SSH shell is a real SSH server that accepts any credentials and presents a shell claiming to be a corporate Ubuntu database host.
PostgreSQL accepts SQL and returns plausible tables or realistic errors — bait for SQL injection.
The "internal AI API" is a chat/prediction service — bait for prompt injection and jailbreak attempts; this is a very new attack surface.
The Ethereum JSON-RPC node answers the exact methods attackers use to find and drain wallets on exposed nodes.
And Jenkins exposes the build/script endpoints that make up its documented attack surface.
Every prior generative honeypot in the literature — ShelLM, HoneyLLM, HoneyGPT — covers only a Linux shell.
""", [
    ("SQL injection", "Inserting malicious SQL into an input so the database executes the attacker's query."),
    ("Prompt injection / jailbreak", "Crafting text to make an AI model ignore its instructions or reveal hidden data."),
    ("XXE / SSRF", "XML External Entity and Server-Side Request Forgery — web attacks that make a server read files or contact internal URLs."),
    ("JSON-RPC", "A simple remote-procedure-call protocol over JSON; Ethereum nodes expose it (methods like eth_accounts, personal_unlockAccount)."),
    ("CI/CD (Jenkins)", "Continuous Integration / Delivery — servers that build and deploy code; compromising one lets attackers poison the software supply chain."),
    ("RCE / reverse shell", "Remote Code Execution; a reverse shell is a connection from the victim back to the attacker giving them a command line."),
    ("Privilege escalation", "Going from a low-privilege account to admin/root."),
])

# ================================================================ SLIDE 12 — three-tier path
s = base_slide("The three-tier response path", "Why not send every request to the AI? Because seconds of delay is itself a tell — and it costs money")
picture(s, os.path.join(FIG, "diag_tier.png"), Inches(0.5), CYK, Inches(12.3), Inches(2.3))
tiers = [
    ("Tier 1 · Static fast-path", "< 1 ms", "Common enumeration commands (ls, whoami, ifconfig…) from a fixed table. Low realism cost — these really do have stable outputs on a real host.", TEAL),
    ("Tier 2 · Response cache", "~1 ms", "Seen this request (plus recent context) before? Serve from in-memory cache — a repeated probe never pays for a second LM call.", TEAL),
    ("Tier 3 · LM synthesis", "seconds", "Only novel requests. Llama-3.1-8B via hosted API, service-specific persona: 'emit ONLY the raw output stream — no explanation, no markdown'. Session history for consistency.", ORANGE),
]
x = Inches(0.6)
for t, lat, d, col in tiers:
    rect(s, x, CYK + Inches(2.45), Inches(3.95), Inches(2.55), LIGHT)
    rect(s, x, CYK + Inches(2.45), Inches(3.95), Inches(0.08), col)
    textbox(s, x + Inches(0.15), CYK + Inches(2.55), Inches(2.6), Inches(0.45), t, size=15, bold=True, color=NAVY)
    textbox(s, x + Inches(2.75), CYK + Inches(2.55), Inches(1.1), Inches(0.45), lat, size=15, bold=True, color=col, align=PP_ALIGN.RIGHT)
    textbox(s, x + Inches(0.15), CYK + Inches(3.0), Inches(3.65), Inches(2.0), d, size=13, color=INK)
    x += Inches(4.1)
notes(s, """
This is the heart of the realism-versus-cost trade-off. An LM call takes seconds; a real service answers routine commands in microseconds.
If every request went to the model, the honeypot would be slow, expensive, AND the uniform multi-second delay would itself be a fingerprint.

So the engine escalates only when necessary. Tier one: the most common enumeration commands — directory listing, identity, network config — come from a fixed table
in under a millisecond. The realism cost is low because those commands genuinely have stable outputs. Tier two: an in-memory cache keyed on request plus recent session context,
so a repeated probe is free. Tier three: only truly novel requests reach the model — an instruction-tuned Llama-3.1-8B behind a hosted inference API, so no local GPU is needed.
The system prompt tells it to emit only the raw output stream of the service: no explanation, no markdown, never admit it is a model. Recent session history is included for consistency.

This mirrors the canonical architecture that Bridges et al.'s 2025 systematisation distilled from sixteen LLM honeypots — we arrived at it independently.
""", [
    ("Llama-3.1-8B", "Meta's open-weight language model with 8 billion parameters; 'instruction-tuned' means trained to follow instructions."),
    ("Hosted inference API", "The model runs on a cloud provider; we call it over the network instead of running it on our own GPU."),
    ("System persona / system prompt", "Hidden instructions telling the model what role to play."),
    ("Cache miss / hit", "Miss = not found in cache, must compute; hit = found, return instantly."),
    ("Breaking character", "When the LM outputs a refusal or 'As an AI model…' — a deception-fatal tell."),
])

# ================================================================ SLIDE 13 — intent classification
s = base_slide("Intent classification — labelling what the attacker wants", "Rule-based on purpose: auditable, zero latency, no training data")
cats = [("SQL injection", RED), ("Prompt injection", ORANGE), ("Crypto theft", ORANGE), ("Cryptomining", MUTED),
        ("Reverse shell / RCE", RED), ("Privilege escalation", RED), ("Supply-chain / CI-CD", ORANGE), ("Reconnaissance", TEAL)]
x, y = Inches(0.6), CYK
for i, (c, col) in enumerate(cats):
    rect(s, x, y, Inches(2.9), Inches(0.7), col, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    textbox(s, x, y, Inches(2.9), Inches(0.7), c, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    x += Inches(3.05)
    if i == 3:
        x = Inches(0.6)
        y += Inches(0.85)
bullets(s, Inches(0.6), CYK + Inches(1.9), Inches(12.1), Inches(3.2), [
    "Every interaction gets ONE of eight categories (else 'unknown'), from transparent rules on the raw request text",
    "Why rules and not machine learning? Rules are auditable, explainable, need no labelled dataset, and add zero latency — the right trade for a forensic sensor",
    "The language model does response SYNTHESIS only — classification is a separate, deterministic stage",
    "Fun fact for later: our first rule set left ~75% of traffic 'unknown'. We fixed it (Gap 3).",
], size=18, gap=10)
notes(s, """
Every captured interaction is labelled with an attack intent from eight categories: SQL injection, prompt injection, crypto theft — the wallet-draining RPC methods — cryptomining,
reverse shell / remote code execution, privilege escalation including brute-force logins, supply-chain / CI-CD abuse, and reconnaissance. Anything unmatched is 'unknown'.

We deliberately used a rule-based classifier rather than a trained model. For a forensic sensor, we value that every decision is explainable and auditable — you can point
to the rule that fired — and that it adds no latency and needs no training data. We consider that worth more than the marginal recall a learned model might add.
Important distinction: the LM writes replies; it does not classify. Classification is deterministic.
""", [
    ("Cryptomining", "Hijacking a machine's CPU to mine cryptocurrency for the attacker."),
    ("Reconnaissance", "Scanning, service enumeration, and the first commands an intruder runs to look around."),
    ("Auditable / explainable", "A human can inspect and justify why a label was assigned — essential if the label appears in an investigation."),
    ("Recall", "Fraction of true cases the classifier catches."),
])

# ================================================================ SLIDE 14 — blockchain anchoring
s = base_slide("Blockchain-anchored logging — making the evidence tamper-evident", "Only a 32-byte fingerprint goes on-chain; the full record stays in the datastore")
picture(s, os.path.join(FIG, "diag_chain.png"), Inches(0.5), CYK, Inches(7.4), Inches(2.7))
rect(s, Inches(0.6), CYK + Inches(2.85), Inches(7.3), Inches(2.05), NAVY)
textbox(s, Inches(0.85), CYK + Inches(2.95), Inches(6.8), Inches(1.85),
        "Why it holds: the on-chain digest cannot be silently rewritten. Any edit to the stored record changes its "
        "SHA-256, so the mismatch is detectable by anyone — integrity no longer depends on trusting the honeypot host.",
        size=16, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
bullets(s, Inches(8.2), CYK, Inches(4.6), Inches(4.9), [
    ("At log time", 0, True),
    ("Serialise the record deterministically", 1),
    ("Compute the SHA-256 digest (32 bytes)", 1),
    ("Send a transaction carrying the digest to a local Ethereum chain", 1),
    ("Full record stays in the datastore", 1),
    ("At verification — any time, by anyone", 0, True),
    ("Fetch the stored record, re-hash it", 1),
    ("Compare with the on-chain digest", 1),
    ("Equal → intact.   Different → tampered.", 1, True),
], size=16, gap=5)
notes(s, """
Here is the integrity mechanism, Figure 4. When a record reaches the collector, it is serialised in a deterministic way — same record, same bytes every time — hashed with SHA-256,
and the 32-byte digest is sent as a transaction to a local Ethereum chain. The full record stays in our datastore; only the digest goes on-chain.

Verification is trivial and can be done by any party at any time: fetch the stored record, re-hash it, compare with the committed value. If they match, the record is intact.
If an attacker who compromised the honeypot edited even one field, the hash changes and no longer matches — and they cannot fix that, because the on-chain digest cannot be rewritten.
This is a well-established pattern from blockchain audit-log research; our contribution is applying it to honeypot telemetry, where the logging host is by design the thing under attack,
and coupling it with a generative multi-protocol honeypot — which, to our knowledge, has not been reported before.
""", [
    ("Digest", "Another word for the hash output — the fixed-size fingerprint."),
    ("Deterministic serialisation", "Converting the record to bytes in a fixed order so identical records always hash identically."),
    ("Immutable / append-only", "Blocks can only be added to a blockchain, never edited; rewriting history would require re-mining every later block."),
    ("Local Ethereum chain", "A private Ethereum node (Ganache-style) under our control, used as an integrity anchor; the same design works on a public chain."),
])

# ================================================================ SLIDE 15 — dashboard
s = base_slide("Real-time operator dashboard", "Live capture during operation — intent breakdown, per-service exposure, top attackers, anchoring status")
picture(s, os.path.join(FIG, "dashboard.png"), Inches(0.5), CYK, Inches(8.6), Inches(4.9))
bullets(s, Inches(9.3), CYK, Inches(3.6), Inches(4.9), [
    "Attacks intercepted, unique attacker IPs, services under attack",
    "% of evidence anchored on-chain",
    "Attack-intent breakdown across the 8 categories",
    "Per-attacker drill-down: services touched, severity-weighted threat rating, intent mix, timeline of real payloads",
    "Searchable live feed: payload, decoy reply, SHA-256 digest, on-chain status per event",
], size=15, gap=6)
notes(s, """
The dashboard is the operator's window into the sensor. It shows intercepted-attack counts, unique attacker IPs, per-intent and per-service breakdowns, and — for each event —
the payload, the decoy's response, its SHA-256 digest and whether it is anchored on-chain. There is also a per-attacker drill-down that reconstructs which services an address touched,
a severity-weighted threat rating, its intent mix, and a timeline of the actual payloads it sent. The paper's Figure 5 shows this over 6,742 intercepted events, and this is also the
surface we use for the live integrity demonstration.
""", [
    ("Threat rating", "A score combining how many and how severe the attacker's intents are."),
])

# ================================================================ SECTION — evaluation
section_slide("Part 3", "Evaluation", "Four independent axes on 2,500 real attack payloads — reported separately, because they trade against each other")
notes(prs.slides[-1], "Now the evaluation. One methodological point up front: we report four axes separately rather than a single composite score, because they pull against each other and the trade-offs are the point.")

# ================================================================ SLIDE 17 — methodology
s = base_slide("Evaluation methodology", "Real payloads only — nothing model-generated, nothing hand-invented")
stat_card(s, Inches(0.6), CYK, Inches(2.9), Inches(1.5), "2,500", "unique real attack payloads from SecLists & PayloadsAllTheThings, each with a provenance field")
stat_card(s, Inches(3.7), CYK, Inches(2.9), Inches(1.5), "5 partitions", "1,862 SSH · 474 SQL · 136 API · 18 Web3 · 10 CI/CD (capped at real payloads available)")
stat_card(s, Inches(6.8), CYK, Inches(2.9), Inches(1.5), "8B → 70B", "Llama-3.1-8B generates replies; an independent Llama-3.1-70B judges realism", ORANGE)
stat_card(s, Inches(9.9), CYK, Inches(2.8), Inches(1.5), "vs static", "baseline: a fixed response table (Cowrie-style)", ORANGE)
axes = [
    ("Axis 1 · Latency & sequential throughput", "Per-request latency of static path vs LM path over repeated trials — mean, median, std-dev. Throughput = 1 / mean latency."),
    ("Axis 2 · Concurrent throughput", "10 simultaneous sessions. Each request carries a fresh nonce → guaranteed cache miss → real LM call (see Gap 2!)."),
    ("Axis 3 · Response diversity", "Uniqueness ratio = distinct outputs ÷ total outputs, per service. Direct proxy for fingerprintability. Static table → ~0; generative → ~1."),
    ("Axis 4 · LM-judge realism", "Llama-3.1-70B rates each (payload, reply) pair 1–5: 1 = obvious tell (template / refusal / AI disclaimer), 5 = indistinguishable. n = 30 sampled."),
    ("+ Blockchain integrity test", "Fetch record → re-hash → matches on-chain. Modify one field → re-hash → must NOT match."),
]
y = CYK + Inches(1.7)
for t, d in axes:
    rect(s, Inches(0.6), y, Inches(12.1), Inches(0.62), LIGHT)
    textbox(s, Inches(0.75), y, Inches(3.9), Inches(0.62), t, size=13, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(4.7), y, Inches(7.9), Inches(0.62), d, size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(0.67)
notes(s, """
The corpus is 2,500 attack payloads from public, permissively licensed security corpora — SecLists and PayloadsAllTheThings — plus documented real-world attack shapes.
Every entry keeps a provenance field. Nothing is model-generated or hand-invented, and there is no padding: each service is capped at the number of distinct real payloads available,
which is why Web3 and CI/CD are small — their real attack surface is a small finite set of RPC methods and exploit endpoints, not an open space of injection strings.

Four axes. Latency and sequential throughput, static versus LM path. Concurrent throughput with ten simultaneous sessions, where each request carries a unique nonce to force a cache miss —
I will come back to why that matters. Response diversity: the uniqueness ratio, distinct outputs over total, which directly measures how clusterable the replies are. And realism,
judged by an independent, larger model — Llama-3.1-70B — on a one-to-five scale, with one meaning an obvious tell.
Separately, we test the tamper-evidence claim directly. And we are explicit that the LM judge is a proxy, not a human study — I will return to that.
""", [
    ("SecLists / PayloadsAllTheThings", "Two widely used open-source collections of real attack strings used by penetration testers."),
    ("Provenance", "Where each payload came from — recorded so the dataset is auditable."),
    ("Nonce", "A 'number used once' appended to a request so it is guaranteed unique."),
    ("Uniqueness ratio", "distinct replies / total replies. 1.0 = every reply different; 0 = all identical."),
    ("LLM-as-judge", "Using a second AI model to grade another model's output — cheap but imperfect (Zheng et al., NeurIPS 2023)."),
    ("Standard deviation", "How spread out the measurements are."),
])

# ================================================================ SLIDE 18 — latency + throughput
s = base_slide("Result 1 — Latency and throughput", "Four orders of magnitude between the tiers — this gap IS the justification for the tiered design")
picture(s, os.path.join(FIG, "fig2_latency.png"), Inches(0.5), CYK, Inches(4.4), Inches(3.05))
picture(s, os.path.join(FIG, "fig3_throughput.png"), Inches(5.0), CYK, Inches(4.4), Inches(3.05))
stat_card(s, Inches(9.7), CYK, Inches(3.0), Inches(1.45), "0.80 ms", "static fast-path mean latency (~1,250 req/s)", TEAL)
stat_card(s, Inches(9.7), CYK + Inches(1.6), Inches(3.0), Inches(1.45), "2.33 s", "dynamic LM path mean (median 1.73 s, σ 1.40 s) → 0.43 req/s", ORANGE)
bullets(s, Inches(0.6), CYK + Inches(3.25), Inches(12.1), Inches(1.9), [
    "Under 10 concurrent sessions (cache misses forced): 1.61 req/s sustained, 2.19 s mean per-request latency",
    "Dynamic latency is dominated by the round-trip to the hosted inference API, not local computation",
    "Routine traffic (~80%) never pays the LM cost — it is answered at static-honeypot speed",
], size=16)
notes(s, """
Result one. The static fast-path answers in a mean of 0.80 milliseconds — around 1,250 requests per second. The dynamic LM path answers in a mean of 2.33 seconds, median 1.73,
standard deviation 1.40 — so roughly four orders of magnitude apart. Note the charts are on a log scale.
This gap is exactly why the tiered design exists: routing routine traffic to the fast-path is what makes an LM honeypot viable at all.

Under ten simultaneous sessions — with cache misses forced — the system sustains 1.61 requests per second at 2.19 seconds mean latency.
The dynamic latency is dominated by the network round-trip to the hosted model, not our code.
For the interactive-intruder threat model, second-scale latency on a genuinely novel command is within the range of a real congested server. For high-rate scanning, the fast-path and cache carry the load.
""", [
    ("Log scale", "Each axis step is 10×; used because the values differ by thousands of times."),
    ("Median vs mean", "Median is the middle value — less affected by a few very slow outliers."),
    ("req/s", "Requests per second."),
])

# ================================================================ SLIDE 19 — diversity + realism
s = base_slide("Result 2 — Diversity and realism", "Can an attacker cluster our replies into a small set? And do they look real?")
picture(s, os.path.join(FIG, "fig4_diversity.png"), Inches(0.5), CYK, Inches(4.6), Inches(3.2))
picture(s, os.path.join(FIG, "fig5_realism.png"), Inches(5.2), CYK, Inches(4.6), Inches(3.2))
stat_card(s, Inches(10.0), CYK, Inches(2.7), Inches(1.5), "0.64 – 0.992", "uniqueness ratio across all five decoys (static table → ~0)", TEAL)
stat_card(s, Inches(10.0), CYK + Inches(1.65), Inches(2.7), Inches(1.5), "4.37 / 5", "mean LM-judge realism (σ 1.45, n = 30); 25 of 30 rated a full 5", TEAL)
bullets(s, Inches(0.6), CYK + Inches(3.4), Inches(12.1), Inches(1.8), [
    "Diversity: SQL 0.992 · Web3 0.944 · SSH 0.903 · CI/CD 0.900 · AI-API 0.64 — all far from the near-zero of a static table",
    "Realism distribution is bimodal: mostly 'clearly realistic', a few 'clearly unconvincing', almost none in between — usually in character, occasionally lapses",
    "The low ratings concentrate on the AI-API decoy (generic error text for XML/SSRF probes) plus a few over-terse SSH 'command not found' replies",
], size=15)
notes(s, """
Result two, goals G1 and G2. On diversity, all five decoys score high: SQL 0.992 — 470 distinct outputs for 474 injection payloads — Web3 0.944, SSH 0.903, CI/CD 0.9, and AI-API 0.64.
A static table would by construction collapse many payloads onto the same canned reply and score near zero. So an automated scanner cannot cluster our output into a small deterministic set.

On realism, the mean judge score is 4.37 out of 5, with 25 of the 30 samples rated a full 5. But look at the distribution, not just the mean: it is bimodal.
Most replies are clearly realistic, a few are clearly unconvincing, almost nothing in between — the signature of a system that is usually in character but occasionally lapses.
When we inspected the low scores, most were AI-API responses to structured payloads — generic error text that did not engage with the specific XML or SSRF probe —
and a few were SSH replies that were templated or fell back to a bare "command not found". We report those rather than smoothing them into the average.
""", [
    ("Bimodal", "A distribution with two peaks — here, a cluster at 5 and a small cluster at 1."),
    ("Templated reply", "A generic canned-looking answer — exactly what the LM was supposed to avoid."),
])

# ================================================================ SLIDE 20 — per-service honesty
s = base_slide("The honest per-service picture", "Two independent metrics agree on which decoy is weakest — that agreement is itself evidence the finding is real")
picture(s, os.path.join(FIG, "tab_perservice.png"), Inches(0.5), CYK, Inches(12.3), Inches(2.6))
rect(s, Inches(0.6), CYK + Inches(2.8), Inches(5.9), Inches(2.3), LIGHT)
rect(s, Inches(0.6), CYK + Inches(2.8), Inches(0.1), Inches(2.3), TEAL)
textbox(s, Inches(0.9), CYK + Inches(2.9), Inches(5.5), Inches(0.45), "Structured-protocol decoys: strong", size=17, bold=True, color=NAVY)
bullets(s, Inches(0.9), CYK + Inches(3.35), Inches(5.5), Inches(1.7), [
    "SQL, Web3, SSH, CI/CD: diversity 0.90–0.99, realism 4.71–5.00",
    "Rigid output grammars (SQL errors, JSON-RPC schema) leave the LM little room to break character",
], size=14)
rect(s, Inches(6.8), CYK + Inches(2.8), Inches(5.9), Inches(2.3), LIGHT)
rect(s, Inches(6.8), CYK + Inches(2.8), Inches(0.1), Inches(2.3), RED)
textbox(s, Inches(7.1), CYK + Inches(2.9), Inches(5.5), Inches(0.45), "AI-API decoy: the one soft spot", size=17, bold=True, color=RED)
bullets(s, Inches(7.1), CYK + Inches(3.35), Inches(5.5), Inches(1.7), [
    "Diversity 0.64, judged realism 1.00 (n = 3)",
    "Likely cause: an 'internal AI API' is under-constrained → model falls back to generic error text",
    "Concrete fix: a tightly specified output contract for that decoy",
], size=14)
notes(s, """
This table consolidates the per-service picture, and it is the slide I most want you to remember, because it is where we resist the temptation to hide behind an average.
The structured-protocol decoys — SQL, Web3, SSH, CI/CD — score 0.90 to 0.99 on diversity and 4.71 to 5.00 on judged realism. The AI-API decoy sits at 0.64 and 1.00.
The disparity is stark and, crucially, consistent across two independent metrics: one is an automatic count of distinct outputs, the other is a separate model's judgement.
That they agree so closely on which service is weakest tells us the finding is real, not an artefact of either measure.

Our explanation: SQL and JSON-RPC have rigid, well-known output formats, so the model has very little room to break character. An "internal AI API" is under-constrained,
so the model more often falls back on generic error text. That points at a concrete fix — a much tighter output contract for that decoy — rather than a flaw in the approach.
Also note the caveat: per-service judge samples are small; they show the direction and size of the disparity, not precise point estimates.
""", [
    ("Output contract", "A strict specification of exactly what format the reply must take."),
    ("Point estimate", "A single number; with n = 3 the number is indicative, not precise."),
])

# ================================================================ SLIDE 21 — integrity test
s = base_slide("Result 3 — Blockchain integrity test", "Goal G5: does tampering get detected? Yes — directly verified")
rect(s, Inches(0.6), CYK, Inches(5.9), Inches(2.3), LIGHT)
rect(s, Inches(0.6), CYK, Inches(0.1), Inches(2.3), TEAL)
textbox(s, Inches(0.9), CYK + Inches(0.15), Inches(5.5), Inches(0.5), "Untampered record", size=18, bold=True, color=TEAL)
bullets(s, Inches(0.9), CYK + Inches(0.65), Inches(5.5), Inches(1.6), [
    "Fetch stored record → recompute SHA-256",
    "Digest matches the anchored on-chain value exactly ✔",
], size=15)
rect(s, Inches(6.8), CYK, Inches(5.9), Inches(2.3), LIGHT)
rect(s, Inches(6.8), CYK, Inches(0.1), Inches(2.3), RED)
textbox(s, Inches(7.1), CYK + Inches(0.15), Inches(5.5), Inches(0.5), "After altering ONE field", size=18, bold=True, color=RED)
bullets(s, Inches(7.1), CYK + Inches(0.65), Inches(5.5), Inches(1.6), [
    "Re-hash the modified record",
    "Digest diverges from the on-chain value → tampering detected ✔",
], size=15)
rect(s, Inches(0.6), CYK + Inches(2.55), Inches(12.1), Inches(2.5), NAVY)
textbox(s, Inches(0.9), CYK + Inches(2.65), Inches(11.5), Inches(2.3),
        "What this proves: an attacker who compromises the honeypot and edits a stored record cannot make the edited record's hash "
        "match what was already committed on-chain. The audit trail's integrity is verifiable independently of the logging host — "
        "by any party, at any later time.",
        size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
notes(s, """
Result three is the integrity claim, tested directly rather than argued. We fetch a stored record, recompute its SHA-256 digest, and confirm it matches the anchored value exactly.
Then we modify a single field of the record, re-hash, and confirm the digest no longer matches. The tampering is detected.

This confirms goal G5: an attacker who compromises the honeypot and edits a stored record cannot make the new hash match what is already on the chain.
The evidence can be verified by anyone, later, without trusting our machine. In the live demo on the dashboard we show exactly this: an event's digest and its on-chain status.
""")

# ================================================================ SLIDE 22 — engineering gaps
s = base_slide("Three engineering gaps we found — and fixed — during construction", "Reported deliberately: two of them are exactly the kind of error that silently corrupts an evaluation")
gaps = [
    ("Gap 1 · LM latency made the naïve design non-viable",
     "Every SSH command went to the model → ~4.0 s mean.",
     "Measured, not guessed: fresh TCP+TLS connection per request; oversized generation cap.",
     "Tiered path + one pooled client + tuned cap → ~1.35 s (≈3× faster). Pooling across all 5 decoys cut latency 30–41% and halved variance. A smaller model did NOT help — provider routing dominated.", TEAL),
    ("Gap 2 · The benchmark was measuring the cache, not the model",
     "Concurrent throughput looked like hundreds of req/s.",
     "Reused payloads from the diversity pass → every 'concurrent' request was a Redis cache hit.",
     "Append a fresh nonce per request → forced cache miss. Honest figure: 1.61 req/s — 2–3 orders of magnitude lower. Kept in the paper on purpose.", ORANGE),
    ("Gap 3 · The intent classifier left ~75% of traffic 'unknown'",
     "Sensor output dominated by 'unknown' = no actionable intelligence.",
     "Rules too narrow: missed proxy probes, first-contact shell enumeration, wallet-draining RPC, brute-force logins, compact injections.",
     "Added crypto-theft category, broadened recon & priv-esc, widened injection/RCE patterns → unknown 75% → ~0% on 1,000 held-out real payloads.", RED),
]
y = CYK
for t, gap, diag, fix, col in gaps:
    rect(s, Inches(0.6), y, Inches(12.1), Inches(1.6), LIGHT)
    rect(s, Inches(0.6), y, Inches(0.1), Inches(1.6), col)
    textbox(s, Inches(0.85), y + Inches(0.05), Inches(11.7), Inches(0.4), t, size=15, bold=True, color=NAVY)
    textbox(s, Inches(0.85), y + Inches(0.45), Inches(3.5), Inches(1.1), "The gap: " + gap, size=12, color=INK)
    textbox(s, Inches(4.4), y + Inches(0.45), Inches(3.6), Inches(1.1), "Diagnosis: " + diag, size=12, color=INK)
    textbox(s, Inches(8.05), y + Inches(0.45), Inches(4.55), Inches(1.1), "Fix: " + fix, size=12, color=INK)
    y += Inches(1.7)
notes(s, """
Section 7 of the paper documents three concrete defects we hit, because a working sensor is not only a design — it is a set of bugs found and fixed.

Gap one: our first build sent essentially every SSH command to the model, giving about 4 seconds mean latency — slow, and a fingerprintable timing signature.
We measured the causes: a fresh TCP plus TLS connection on every request, and a generation-length cap far larger than a shell output needs. The fix was the tiered path,
a single pooled client, and a measured cap: 4.0 down to about 1.35 seconds, roughly threefold, across two independent runs. Applying the same pooling fix in all five decoys
cut their latency 30 to 41 percent and halved the variance. Interestingly, swapping in a smaller model did not help — on the hosted API, provider routing dominated parameter count.

Gap two is the important one for anyone who benchmarks. An early harness reported hundreds of requests per second concurrent throughput. It was measuring the cache: the concurrent test reused
payloads already sent during the diversity pass, so every request was a Redis hit. We fixed it with a per-request nonce. The honest number, 1.61 requests per second, is two to three orders
of magnitude lower. We kept this in the paper because it is a common, flattering, easily missed mistake.

Gap three: the first classifier labelled about three-quarters of traffic as unknown — not because the traffic was unclassifiable, but because the rules were too narrow.
Expanding them brought unknown from 75 percent to effectively zero on a held-out sample of 1,000 real payloads.
""", [
    ("TCP + TLS handshake", "Setting up a new encrypted network connection costs several round-trips; reusing one pooled connection avoids that on every request."),
    ("Generation-length cap (max tokens)", "The maximum number of words the model may produce; larger caps mean longer generation time."),
    ("Connection pooling", "Keeping one warm connection open and reusing it."),
    ("Held-out sample", "Data not used while designing the rules, so the test is fair."),
])

# ================================================================ SLIDE 23 — comparison
s = base_slide("How we compare with prior systems", "No single prior system is multi-protocol, generative, fast on routine traffic AND integrity-anchored")
picture(s, os.path.join(FIG, "fig10_dominance.png"), Inches(0.5), CYK, Inches(7.2), Inches(3.1))
bullets(s, Inches(7.9), CYK, Inches(4.9), Inches(3.2), [
    ("Static (Cowrie/Kippo): ~0.14 s/cmd but fingerprinted in one packet; no integrity", 0),
    ("Single-surface LLM (ShelLM, HoneyLLM, HoneyGPT): generative, but SSH only; HoneyLLM 1.88 s/cmd; none anchors logs", 0),
    ("Blockchain audit logs: integrity, but not a deception sensor at all", 0),
    ("This work: 5 surfaces · 0.8 ms routine / 2.33 s novel · tamper-evident", 0, True),
], size=14, gap=4)
rect(s, Inches(0.6), CYK + Inches(3.3), Inches(12.1), Inches(1.75), LIGHT)
bullets(s, Inches(0.8), CYK + Inches(3.4), Inches(11.8), Inches(1.6), [
    "Caveat we state explicitly: prior figures are reproduced as published — different hardware, metrics, models. This is NOT a controlled head-to-head.",
    "ShelLM's 0.92 accuracy is a HUMAN-subject result (12 researchers, 226 commands) — stronger evidence than our automated judge; we do not claim parity",
    "We do not beat generative systems on raw novel-request latency; we are the design that avoids paying it on the ~80% of routine traffic",
], size=14, gap=4)
notes(s, """
How does this sit against prior work? Figure 11 scores three classes of system on five capabilities.
Static honeypots like Cowrie lead only on routine latency — and that is the same property that let a single packet fingerprint them.
Single-surface LLM honeypots — ShelLM, HoneyLLM, HoneyGPT — share our generative advantage, but on one protocol, and none addresses log integrity.
Blockchain secure-logging systems give integrity but are not deception sensors. Ours is the only design scoring highly on every dimension at once.
That is the sense in which we "dominate": not by beating any system on its own best metric, but by being the only one that is simultaneously multi-protocol, generative, fast on routine traffic, and integrity-anchored.

Two honest caveats. First, the numbers in our comparison table are each system's own published figures under different conditions — we did not re-benchmark them on one testbed,
so this is not a controlled head-to-head. Second, ShelLM's 0.92 accuracy comes from a human-subject study, which is stronger evidence than our LM judge; we explicitly do not claim parity.
What we do claim: our best decoys reach diversity and realism at least in ShelLM's range, across five protocols instead of one.
""", [
    ("ShelLM (Sladić et al. 2024)", "First integrated generative SSH honeypot; strongest published human-study realism result."),
    ("HoneyLLM (Fan et al. 2024)", "LLM honeypot with a filter/router front end; 1.88 s per command vs 0.138 s for Cowrie."),
    ("HoneyGPT (Wang et al. 2024)", "Adds a prompt-management component to track session state."),
    ("SoK (Bridges et al. 2025)", "Systematisation of sixteen LLM honeypots; distils the canonical architecture our design mirrors."),
])

# ================================================================ SLIDE 24 — limitations & future
s = base_slide("Limitations and future work", "What we cannot yet claim, and what we will do next")
rect(s, Inches(0.6), CYK, Inches(5.9), Inches(4.9), LIGHT)
rect(s, Inches(0.6), CYK, Inches(0.1), Inches(4.9), RED)
textbox(s, Inches(0.9), CYK + Inches(0.15), Inches(5.5), Inches(0.5), "Limitations (threats to validity)", size=19, bold=True, color=NAVY)
bullets(s, Inches(0.9), CYK + Inches(0.7), Inches(5.5), Inches(4.1), [
    "Realism is measured by PROXY — an LM judge can be miscalibrated, reward plausible-but-wrong output, share blind spots with the judged model",
    "Single run, one response model, one judge model",
    "Diversity rewards uniqueness — necessary but not sufficient (unique-but-wrong scores well); so we read diversity and realism together",
    "Rule-based classifier is coverage-limited by construction",
    "Per-service judge samples are small (n = 3 for SQL and API)",
], size=15, gap=6)
rect(s, Inches(6.8), CYK, Inches(5.9), Inches(4.9), LIGHT)
rect(s, Inches(6.8), CYK, Inches(0.1), Inches(4.9), TEAL)
textbox(s, Inches(7.1), CYK + Inches(0.15), Inches(5.5), Inches(0.5), "Future work", size=19, bold=True, color=NAVY)
bullets(s, Inches(7.1), CYK + Inches(0.7), Inches(5.5), Inches(4.1), [
    ("Human-subject detectability study — the primary next step", 0, True),
    ("Security practitioners, matched real vs decoy sessions, blinded, detection-rate outcome", 1),
    "Redesign the AI-API decoy: tightly constrained prompt, or a non-generative fallback for structured payloads; re-evaluate",
    "Compare response models to quantify the realism / latency / cost frontier",
    "Measure classifier precision & recall on labelled traffic; test whether a learned classifier adds coverage without losing explainability",
    "Downstream: map intent-labelled logs to MITRE ATT&CK tactics",
], size=15, gap=6)
notes(s, """
Limitations, stated plainly. The most important one: realism is measured by proxy. An LM judge can only flag gross failures; it can be miscalibrated and share blind spots with the model it judges.
A defensible claim of indistinguishability needs a human-subject study — practitioners interacting with matched real and decoy sessions under blinded conditions — and designing and running that is our primary future work.
The evaluation is a single run on one response model and one judge. Diversity rewards uniqueness, which is necessary but not sufficient — unique-but-wrong output would score well on diversity and badly with the judge,
which is exactly the AI-API decoy's profile; that is why we read the two together.

Next steps beyond the human study: redesign the AI-API decoy with a tight output contract or a non-generative fallback; compare models to map the realism-latency-cost frontier;
measure the classifier's precision and recall; and feed the intent-labelled, integrity-anchored logs into MITRE ATT&CK mapping as a downstream consumer.
""", [
    ("Threats to validity", "Standard research term for reasons the results might not generalise."),
    ("Blinded study", "Participants do not know which session is real and which is the decoy."),
    ("Precision", "Of the items labelled X, how many really are X. Recall: of all real X, how many were labelled X."),
    ("MITRE ATT&CK", "An industry-standard catalogue of attacker tactics and techniques."),
])

# ================================================================ SLIDE 25 — conclusion
s = base_slide("Conclusion — what to take away")
take = [
    ("Generative, not tabular", "A language model behind five decoys yields non-enumerable, in-character replies (diversity 0.64–0.99, judged realism 4.37/5)", TEAL),
    ("Tiered, so it is fast", "Routine traffic at 0.8 ms — static-honeypot speed; only the novel tail pays 2.33 s", TEAL),
    ("Tamper-evident evidence", "Every record hashed and anchored on-chain; alteration detected without trusting the honeypot host", TEAL),
    ("Honest about the weak spot", "The AI-API decoy underperforms on both metrics — reported, diagnosed, and the priority for future work", ORANGE),
    ("Honest about the process", "A benchmark bug that inflated throughput 100–1000× and a classifier that missed 75% of traffic — found, fixed, documented", ORANGE),
]
y = CY + Inches(0.1)
for t, d, col in take:
    rect(s, Inches(0.6), y, Inches(0.12), Inches(0.85), col)
    textbox(s, Inches(0.95), y - Inches(0.03), Inches(3.9), Inches(0.9), t, size=19, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, Inches(4.9), y - Inches(0.03), Inches(7.9), Inches(0.9), d, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    y += Inches(1.0)
textbox(s, Inches(0.6), y + Inches(0.05), Inches(12.1), Inches(0.6),
        "For a system whose entire purpose is trustworthy evidence collection, transparent reporting is part of the contribution.",
        size=16, color=MUTED, italic=True)
notes(s, """
To conclude. We presented a multi-protocol cyber-deception framework coupling a tiered, LM-backed response engine with blockchain-anchored logging across five decoys.
Generative replies make the honeypot non-enumerable. The tiered path keeps routine traffic at static-honeypot speed and pays the LM cost only on the novel tail.
On-chain anchoring makes the audit trail tamper-evident independent of the logging host, and we verified that directly.
On 2,500 real payloads we get high diversity across all five decoys and strong judged realism, with the AI-API decoy the one service that measurably underperforms — and the priority for refinement.
And by documenting the engineering gaps, a benchmark correction, and the per-service disparity alongside the favourable numbers, we aimed to give an honest account of what an LM-plus-blockchain deception sensor does and does not yet achieve.
""")

# ================================================================ SLIDE 26 — thank you
slide_no[0] += 1
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, NAVY)
rect(s, Inches(0.8), Inches(3.35), Inches(1.2), Inches(0.08), TEAL)
textbox(s, Inches(0.8), Inches(2.2), Inches(11.5), Inches(1.1), "Thank you — questions?", size=44, bold=True, color=WHITE)
textbox(s, Inches(0.8), Inches(3.6), Inches(11.5), Inches(1.2),
        "A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging",
        size=16, color=RGBColor(0xC9, 0xD4, 0xE0), italic=True)
textbox(s, Inches(0.8), Inches(4.9), Inches(11.5), Inches(1.4),
        "Radhika G  ·  Sisir Reddy Nellore  ·  Pranav Sharma Chouduru  ·  Surya Tejeswar Reddy Nagireddy  ·  "
        "Guru Sai Prasad Reddy Bompalli  ·  Vishnu Sathwick Rajala\n"
        "Amrita School of Computing, Coimbatore  ·  Amrita Vishwa Vidyapeetham, India\n"
        "g_radhika@cb.amrita.edu  ·  cb.sc.u4cse23129@cb.students.amrita.edu",
        size=14, color=WHITE)
notes(s, """
Thank you. I am happy to take questions.

LIKELY QUESTIONS & SHORT ANSWERS
• "Why not a human study?" — Cost and time; it is our stated primary future work. The LM judge is used only to find gross failures and per-service disparities, never to certify indistinguishability.
• "Isn't 2.33 s a giveaway?" — For routine commands (~80% of traffic) we answer in 0.8 ms. Novel commands from a human intruder at human speed see 2 s, which is within the range of a congested real server. Published LLM honeypots sit at 1.88–4 s per command on EVERY request.
• "Why Ethereum / why blockchain instead of a signed log or write-once storage?" — Any append-only anchor works; a ledger gives a third-party-verifiable, host-independent commitment with existing tooling. We store only 32-byte digests, so cost and privacy are minimal. (Do not claim confidentiality — we claim tamper-evidence only.)
• "What if the LM breaks character?" — The persona prompt forbids explanations/markdown/AI disclaimers; the judge rubric scores a refusal as 1, and our low-score cases are mostly generic errors, not disclaimers. Character stability is an open problem across this literature.
• "Why rules instead of ML for classification?" — Auditability, explainability, zero latency, no training data; we plan a precision/recall study and a comparison with a learned classifier.
• "Can the attacker DoS you by forcing LM calls?" — The cache and fast-path absorb repeats; only novel input costs an LM call. Rate-limiting the LM tier is straightforward and part of deployment hardening.
• "Cost?" — Hosted 8B model, no local GPU; only the novel tail is metered.
""")

TOTAL = slide_no[0]
prs.save(OUT)
print("saved", OUT, "slides:", TOTAL)
