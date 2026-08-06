"""
Builds paper2/paper_ieee.docx — an IEEE-conference-styled two-column Word
document from paper.md, with the same real-number substitution and image
embedding as build_docx.py.

IEEE styling applied (best-effort within python-docx):
  - US Letter, ~0.75in margins
  - Two balanced columns for body text
  - Times New Roman, 10pt body
  - Centered bold title (~18pt); centered author block
  - Centered SMALL-CAPS numbered section headings; italic subsections
  - Abstract in bold-italic-lead, justified
  - Figures/tables placed inline; wide items scaled to column or page width

python-docx cannot perfectly reproduce the official IEEEtran template
(true column-spanning floats, exact heading kerning). For a pixel-perfect
IEEE PDF, the accompanying LaTeX path (IEEEtran on Overleaf) remains the
canonical route; this .docx is the editable, close-in-Word approximation.
"""
import json
import re
from collections import Counter
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
R = json.loads((ROOT.parent / "evaluation_results.json").read_text())
DATASET = json.loads((ROOT.parent / "apt_attack_dataset.json").read_text())
svc = Counter(x["service"] for x in DATASET)

lat, div = R["latency"], R["response_diversity_by_service"]
realism, conc = R["llm_judge_realism"], R["concurrent_throughput"]

SUBS = {
    "DATASET_N": f"{len(DATASET):,}", "DATASET_SSH": str(svc.get('ssh',0)),
    "DATASET_SQL": str(svc.get('sql',0)), "DATASET_API": str(svc.get('api',0)),
    "DATASET_WEB3": str(svc.get('web3',0)), "DATASET_CICD": str(svc.get('cicd',0)),
    "STAT_LAT_MS": f"{lat['static']['mean_s']*1000:.2f}",
    "STAT_RPS": f"{R['throughput_rps']['static']:,.0f}",
    "DYN_LAT_MEAN": f"{lat['dynamic']['mean_s']:.2f}", "DYN_LAT_MEDIAN": f"{lat['dynamic']['median_s']:.2f}",
    "DYN_LAT_STDEV": f"{lat['dynamic']['stdev_s']:.2f}", "DYN_RPS": f"{R['throughput_rps']['dynamic_sequential']:.2f}",
    "CONC_LEVEL": str(conc['concurrency_level']), "CONC_RPS": f"{conc['throughput_rps']:.2f}",
    "CONC_LAT": f"{conc['per_request_latency']['mean_s']:.2f}",
    "DIV_SSH": f"{div.get('ssh',{}).get('uniqueness_ratio','—')}", "DIV_SQL": f"{div.get('sql',{}).get('uniqueness_ratio','—')}",
    "DIV_API": f"{div.get('api',{}).get('uniqueness_ratio','—')}", "DIV_WEB3": f"{div.get('web3',{}).get('uniqueness_ratio','—')}",
    "DIV_CICD": f"{div.get('cicd',{}).get('uniqueness_ratio','—')}",
    "SQL_DISTINCT": f"{div.get('sql',{}).get('distinct','—')}", "SQL_N": f"{div.get('sql',{}).get('n','—')}",
    "REALISM_MEAN": f"{realism['mean_score_1to5']}", "REALISM_STDEV": f"{realism['stdev']}",
    "REALISM_N": str(realism['n_scored']), "JUDGE_N": str(R['config']['judge_sample_size']),
    "CLF_SAMPLE_N": "1,000", "DASH_TOTAL": "6,742",
    "TAB_POOL": "II", "TAB_COMPARE": "I", "TAB_QUANT": "III",
}

# Wide items span BOTH columns → placed in a single-column band. Narrow charts
# sit inline in the two-column flow.
FULLWIDTH = {
    "FIG_ARCH": ("diag_arch.png", 6.9, "Fig. 1. System architecture."),
    "FIG_FLOW": ("diag_flow.png", 6.9, "Fig. 2. Data flow for one interaction."),
    "FIG_DASH": ("dashboard.png", 6.9, "Fig. 5. Live dashboard capture during operation."),
    "FIG_ATTACKERS": ("dash_attackers.png", 6.9, "Fig. 11. Per-attacker drill-down (real captured session)."),
    "FIG_DOMINANCE": ("fig10_dominance.png", 6.9, "Fig. 10. Capability coverage across honeypot classes."),
    "TAB_PERSERVICE_BODY": ("tab_perservice.png", 6.9, "TABLE IV. Per-service evaluation results."),
    "TAB_QUANT_BODY": ("tab_quant.png", 6.9, "TABLE III. Honeypot taxonomy and quantitative comparison."),
    "TAB_COMPARE_BODY": ("tab_compare.png", 6.9, "TABLE I. Property comparison with prior work."),
}
INLINE_IMG = {
    "FIG_TIER": ("diag_tier.png", 3.3, "Fig. 3. Three-tier response path."),
    "FIG_CHAIN": ("diag_chain.png", 3.3, "Fig. 4. Anchoring and tamper verification."),
    "TAB_POOL_BODY": ("tab_pool.png", 3.3, "TABLE II. Connection-pooling before/after."),
    "FIG_LAT": ("fig2_latency.png", 3.3, "Fig. 6. Mean response latency."),
    "FIG_THRU": ("fig3_throughput.png", 3.3, "Fig. 7. Throughput comparison."),
    "FIG_DIV": ("fig4_diversity.png", 3.3, "Fig. 8. Response diversity by service."),
    "FIG_REAL": ("fig5_realism.png", 3.3, "Fig. 9. LM-judge realism distribution."),
}
ALL_IMG = {**FULLWIDTH, **INLINE_IMG}


def fill(t):
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}",
                  lambda m: SUBS.get(m.group(1), m.group(0)), t)


def strip_md(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    t = re.sub(r"`(.+?)`", r"\1", t)
    return t


def set_cols(section, num):
    cols = section._sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols'); section._sectPr.append(cols)
    cols.set(qn('w:num'), str(num))
    cols.set(qn('w:space'), '360')  # ~0.25in gutter


doc = Document()
# base style
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(10)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.0

sec = doc.sections[0]
sec.page_height = Inches(11); sec.page_width = Inches(8.5)
sec.top_margin = Inches(0.75); sec.bottom_margin = Inches(0.75)
sec.left_margin = Inches(0.72); sec.right_margin = Inches(0.72)

md = (ROOT / "paper.md").read_text()
lines = md.split("\n")

# --- Title block: single column at top ---
def add_title_block():
    # find title (# ...) and author lines
    i = 0
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    title = fill(lines[i][2:].strip())
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title); r.bold = True; r.font.size = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    # author block (next non-empty lines until ---)
    j = i + 1
    authors = []
    while j < len(lines) and lines[j].strip() != "---":
        if lines[j].strip():
            authors.append(lines[j].strip())
        j += 1
    for a in authors:
        ap = doc.add_paragraph(); ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ar = ap.add_run(strip_md(a)); ar.font.size = Pt(10.5)
    return j  # index of the --- after author block


start = add_title_block()

# add a continuous section break → switch to two columns for the body
new_sec = doc.add_section(WD_SECTION.CONTINUOUS)
new_sec.top_margin = Inches(0.75); new_sec.bottom_margin = Inches(0.75)
new_sec.left_margin = Inches(0.72); new_sec.right_margin = Inches(0.72)
set_cols(new_sec, 2)

body_col_state = 2  # track current column mode


def ensure_cols(n):
    """Switch column mode by adding a continuous section break if needed."""
    global body_col_state
    if body_col_state == n:
        return
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    s.top_margin = Inches(0.75); s.bottom_margin = Inches(0.75)
    s.left_margin = Inches(0.72); s.right_margin = Inches(0.72)
    set_cols(s, n)
    body_col_state = n


def add_heading(text, level):
    ensure_cols(2)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(3)
    if level == 1:  # section: centered small caps
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(fill(text).upper()); r.bold = True; r.font.size = Pt(10)
    else:  # subsection: italic, left
        r = p.add_run(fill(text)); r.italic = True; r.bold = True; r.font.size = Pt(10)


def add_para(text, justify=True, first=False):
    ensure_cols(2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Inches(0 if first else 0.14)
    p.paragraph_format.space_after = Pt(2)
    p.add_run(strip_md(fill(text)))


def add_inline_image(token):
    ensure_cols(2)
    fname, w, cap = INLINE_IMG[token]
    path = FIG / fname
    if not path.exists(): return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(min(w, 3.3)))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = c.add_run(cap); cr.font.size = Pt(8.5)


def add_fullwidth_image(token):
    ensure_cols(1)  # span both columns
    fname, w, cap = FULLWIDTH[token]
    path = FIG / fname
    if not path.exists(): return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(min(w, 6.9)))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = c.add_run(cap); cr.font.size = Pt(8.5)


# --- walk body from `start` ---
i = start
while i < len(lines):
    s = lines[i].strip()

    m = re.fullmatch(r"\{\{([A-Z0-9_]+)\}\}", s)
    if m and m.group(1) in FULLWIDTH:
        add_fullwidth_image(m.group(1)); i += 1; continue
    if m and m.group(1) in INLINE_IMG:
        add_inline_image(m.group(1)); i += 1; continue

    if s == "---" or s == "":
        i += 1; continue

    if s.startswith("## "):
        add_heading(s[3:], 1); i += 1; continue
    if s.startswith("### "):
        add_heading(s[4:], 2); i += 1; continue
    if s.startswith("# "):  # already used title
        i += 1; continue

    if s.startswith("> "):
        add_para(s[2:], justify=True); i += 1; continue
    if re.match(r"^\d+\.\s", s):
        add_para(re.sub(r"^\d+\.\s", "", s), justify=True); i += 1; continue
    if s.startswith("- "):
        add_para("• " + s[2:], justify=False); i += 1; continue

    # gather paragraph
    para = [s]; j = i + 1
    while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("#", "-", ">")) \
            and not re.match(r"^\d+\.\s", lines[j].strip()) \
            and not re.fullmatch(r"\{\{[A-Z0-9_]+\}\}", lines[j].strip()):
        para.append(lines[j].strip()); j += 1
    add_para(" ".join(para), justify=True, first=(s.lower().startswith("abstract") or para[0][:2].isupper()))
    i = j

out = ROOT / "paper_ieee.docx"
doc.save(str(out))
leftover = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", (ROOT / "paper.md").read_text()))
unresolved = [t for t in leftover if t not in SUBS and t not in ALL_IMG]
print(f"Saved {out}")
print("All tokens resolved." if not unresolved else f"WARNING unresolved: {sorted(unresolved)}")
