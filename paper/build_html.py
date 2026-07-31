"""
Builds paper/paper.html: a self-contained, IEEE-conference-styled two-column
HTML document with all figures embedded as base64 data URIs, from the
template in paper_template.html and the PNGs in figures/.
"""
from pathlib import Path

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"

template = (ROOT / "paper_template.html").read_text()

for name in ["fig1_latency", "fig2_throughput", "fig3_diversity", "fig4_realism", "fig5_decoy_pooling", "dashboard_screenshot"]:
    b64 = (FIG_DIR / f"{name}.b64").read_text().strip()
    placeholder = f"{{{{{name}}}}}"
    if placeholder not in template:
        raise SystemExit(f"Missing placeholder {placeholder} in template")
    template = template.replace(placeholder, b64)

out_path = ROOT / "paper.html"
out_path.write_text(template)
print(f"Wrote {out_path} ({len(template):,} bytes)")
