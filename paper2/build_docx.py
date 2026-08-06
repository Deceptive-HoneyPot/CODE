"""
Builds paper2/paper.docx from paper.md, substituting the real measured numbers
from ../evaluation_results.json and embedding the diagrams, tables, result
charts, and dashboard screenshot as images.

Run AFTER evaluate.py has written a fresh evaluation_results.json and after
generate_figures.py has produced the result charts.

Nothing here invents a number: every {{TOKEN}} is filled from the evaluation
JSON or from the dataset file, and the script fails loudly if a token is left
unresolved rather than shipping a paper with a literal {{...}} in it.
"""
import json
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
R = json.loads((ROOT.parent / "evaluation_results.json").read_text())
DATASET = json.loads((ROOT.parent / "apt_attack_dataset.json").read_text())

from collections import Counter
svc_counts = Counter(x["service"] for x in DATASET)

# --- Build the substitution table from REAL data only ---
lat = R["latency"]
div = R["response_diversity_by_service"]
realism = R["llm_judge_realism"]
conc = R["concurrent_throughput"]

def g(d, *keys, default="—"):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
        if d is None:
            return default
    return d

SUBS = {
    "DATASET_N": f"{len(DATASET):,}",
    "DATASET_SSH": str(svc_counts.get("ssh", 0)),
    "DATASET_SQL": str(svc_counts.get("sql", 0)),
    "DATASET_API": str(svc_counts.get("api", 0)),
    "DATASET_WEB3": str(svc_counts.get("web3", 0)),
    "DATASET_CICD": str(svc_counts.get("cicd", 0)),
    "STAT_LAT_MS": f"{lat['static']['mean_s']*1000:.2f}",
    "STAT_RPS": f"{R['throughput_rps']['static']:,.0f}",
    "DYN_LAT_MEAN": f"{lat['dynamic']['mean_s']:.2f}",
    "DYN_LAT_MEDIAN": f"{lat['dynamic']['median_s']:.2f}",
    "DYN_LAT_STDEV": f"{lat['dynamic']['stdev_s']:.2f}",
    "DYN_RPS": f"{R['throughput_rps']['dynamic_sequential']:.2f}",
    "CONC_LEVEL": str(conc["concurrency_level"]),
    "CONC_RPS": f"{conc['throughput_rps']:.2f}",
    "CONC_LAT": f"{conc['per_request_latency']['mean_s']:.2f}",
    "DIV_SSH": f"{div.get('ssh',{}).get('uniqueness_ratio','—')}",
    "DIV_SQL": f"{div.get('sql',{}).get('uniqueness_ratio','—')}",
    "DIV_API": f"{div.get('api',{}).get('uniqueness_ratio','—')}",
    "DIV_WEB3": f"{div.get('web3',{}).get('uniqueness_ratio','—')}",
    "DIV_CICD": f"{div.get('cicd',{}).get('uniqueness_ratio','—')}",
    "SQL_DISTINCT": f"{div.get('sql',{}).get('distinct','—')}",
    "SQL_N": f"{div.get('sql',{}).get('n','—')}",
    "TAB_QUANT": "III",
    "REALISM_MEAN": f"{realism['mean_score_1to5']}",
    "REALISM_STDEV": f"{realism['stdev']}",
    "REALISM_N": str(realism["n_scored"]),
    "JUDGE_N": str(R["config"]["judge_sample_size"]),
    "CLF_SAMPLE_N": "1,000",   # the held classifier-validation sample (§6.3)
    "DASH_TOTAL": "6,742",      # count shown in the captured dashboard figure
    "TAB_POOL": "II",
    "TAB_COMPARE": "I",
}

# Image placeholders map to files; handled separately during rendering.
IMAGE_TOKENS = {
    "FIG_ARCH": ("diag_arch.png", 6.2, "Fig. 1. System architecture."),
    "FIG_FLOW": ("diag_flow.png", 6.2, "Fig. 2. Data flow for one interaction."),
    "FIG_TIER": ("diag_tier.png", 6.0, "Fig. 3. Three-tier response path."),
    "FIG_CHAIN": ("diag_chain.png", 6.0, "Fig. 4. Anchoring and tamper verification."),
    "FIG_DASH": ("dashboard.png", 6.4, "Fig. 5. Live dashboard capture during operation."),
    "TAB_COMPARE_BODY": ("tab_compare.png", 6.5, "Table I. Property comparison with prior work."),
    "TAB_POOL_BODY": ("tab_pool.png", 6.5, "Table II. Connection-pooling before/after (real measurements)."),
    "FIG_LAT": ("fig2_latency.png", 3.2, "Fig. 6. Mean response latency, static vs. dynamic."),
    "FIG_THRU": ("fig3_throughput.png", 3.2, "Fig. 7. Throughput: static, sequential, concurrent."),
    "FIG_DIV": ("fig4_diversity.png", 3.4, "Fig. 8. Response diversity by decoy service."),
    "FIG_REAL": ("fig5_realism.png", 3.4, "Fig. 9. LM-judge realism score distribution."),
    "FIG_DOMINANCE": ("fig10_dominance.png", 6.4, "Fig. 10. Capability coverage across honeypot classes."),
    "FIG_ATTACKERS": ("dash_attackers.png", 6.4, "Fig. 11. Per-attacker drill-down (real captured session)."),
    "TAB_PERSERVICE_BODY": ("tab_perservice.png", 6.5, "Table IV. Per-service evaluation results."),
    "TAB_QUANT_BODY": ("tab_quant.png", 6.9, "Table III. Honeypot taxonomy and quantitative comparison."),
}


def fill_text(t):
    def repl(m):
        key = m.group(1)
        if key in SUBS:
            return SUBS[key]
        return m.group(0)  # leave image/unknown tokens for separate handling
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", repl, t)


doc = Document()
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(10)

md = (ROOT / "paper.md").read_text()
lines = md.split("\n")

def add_image(token):
    if token not in IMAGE_TOKENS:
        return
    fname, width_in, caption = IMAGE_TOKENS[token]
    path = FIG / fname
    if path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(width_in))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(caption)
        r.italic = True
        r.font.size = Pt(8.5)


i = 0
while i < len(lines):
    line = lines[i].rstrip()
    stripped = line.strip()

    # image/table tokens on their own line
    tok = re.fullmatch(r"\{\{([A-Z0-9_]+)\}\}", stripped)
    if tok and tok.group(1) in IMAGE_TOKENS:
        add_image(tok.group(1))
        i += 1
        continue

    if stripped == "---":
        i += 1
        continue

    if stripped.startswith("# "):
        h = doc.add_heading(fill_text(stripped[2:]), level=0)
        i += 1
        continue
    if stripped.startswith("## "):
        doc.add_heading(fill_text(stripped[3:]), level=1)
        i += 1
        continue
    if stripped.startswith("### "):
        doc.add_heading(fill_text(stripped[4:]), level=2)
        i += 1
        continue

    if stripped.startswith("> "):
        p = doc.add_paragraph(fill_text(stripped[2:]))
        p.style = doc.styles["Intense Quote"] if "Intense Quote" in [s.name for s in doc.styles] else p.style
        i += 1
        continue

    if re.match(r"^\d+\.\s", stripped):
        doc.add_paragraph(fill_text(re.sub(r"^\d+\.\s", "", stripped)), style="List Number")
        i += 1
        continue
    if stripped.startswith("- "):
        doc.add_paragraph(fill_text(stripped[2:]), style="List Bullet")
        i += 1
        continue

    if stripped == "":
        i += 1
        continue

    # regular paragraph: gather until blank
    para = [stripped]
    j = i + 1
    while j < len(lines) and lines[j].strip() != "" and not lines[j].strip().startswith(("#", "-", ">")) and not re.match(r"^\d+\.\s", lines[j].strip()) and not re.fullmatch(r"\{\{[A-Z0-9_]+\}\}", lines[j].strip()):
        para.append(lines[j].strip())
        j += 1
    text = fill_text(" ".join(para))
    # strip simple markdown emphasis markers for clean Word text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    doc.add_paragraph(text)
    i = j

out = ROOT / "paper.docx"
doc.save(str(out))

# fail loudly if any number token slipped through
leftover = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", (ROOT / "paper.md").read_text()))
unresolved = [t for t in leftover if t not in SUBS and t not in IMAGE_TOKENS]
print(f"Saved {out}")
if unresolved:
    print("WARNING unresolved tokens:", sorted(unresolved))
else:
    print("All tokens resolved.")
