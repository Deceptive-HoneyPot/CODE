"""
Generates paper4-ai-verdict/tables.html from ../ai_verdict_results.json.
Every number is real, read directly from the benchmark output. Render to
PNG with render.py (Chrome headless), captions added by LaTeX.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
D = json.loads((ROOT.parent / "ai_verdict_results.json").read_text())
S = D["summary"]
T = D["tamper_detection"]
OC = D["onchain_retrievability"]

# --- Table I: headline results summary ---
results_rows = [
    ("Labeled payloads", f"{S['n_payloads']}"),
    ("Rule-based classifier accuracy", f"{S['rule_based_accuracy_pct']:.1f}%"),
    ("LLM classifier accuracy", f"{S['llm_accuracy_pct']:.1f}%"),
    ("LLM &harr; rule-based agreement", f"{S['llm_rule_agreement_pct']:.1f}%"),
    ("Verdicts anchored on-chain", f"{S['anchored_ok']} / {S['n_payloads']} ({S['anchored_rate_pct']:.0f}%)"),
    ("Mean LLM inference latency", f"{S['llm_latency_ms']['mean_ms']:,.1f} ms"),
    ("Median LLM inference latency", f"{S['llm_latency_ms']['median_ms']:,.1f} ms"),
    ("Mean on-chain anchor latency", f"{S['anchor_latency_ms']['mean_ms']:.2f} ms"),
    ("Verdict tamper-detection rate", f"{T['detected']} / {T['trials']} ({T['detection_rate_pct']:.0f}%)"),
    ("Verdict false positives", f"{T['false_positives']}"),
    ("Verdict digest recoverable on-chain", "yes" if OC["found_on_chain"] else "no"),
]

# --- Table II: per-category accuracy, rule-based vs LLM ---
categories = ["reconnaissance", "privilege_escalation", "sql_injection", "reverse_shell",
              "cryptomining", "crypto_theft", "prompt_injection", "supply_chain", "unknown"]
label_map = {
    "reconnaissance": "Reconnaissance", "privilege_escalation": "Privilege escalation",
    "sql_injection": "SQL injection", "reverse_shell": "Reverse shell",
    "cryptomining": "Cryptomining", "crypto_theft": "Crypto theft",
    "prompt_injection": "Prompt injection", "supply_chain": "Supply chain", "unknown": "Unknown / benign",
}
llm_by_cat = {c: [0, 0] for c in categories}
rule_by_cat = {c: [0, 0] for c in categories}
for r in D["raw_results"]:
    gt = r["ground_truth"]
    if gt not in llm_by_cat:
        continue
    llm_by_cat[gt][1] += 1
    rule_by_cat[gt][1] += 1
    if r["llm_correct"]:
        llm_by_cat[gt][0] += 1
    if r["rule_based_correct"]:
        rule_by_cat[gt][0] += 1

category_header = ["Intent category", "n", "Rule-based acc.", "LLM acc.", "Gap"]
category_rows = []
for c in categories:
    n = llm_by_cat[c][1]
    rp = 100 * rule_by_cat[c][0] / n if n else 0
    lp = 100 * llm_by_cat[c][0] / n if n else 0
    gap = rp - lp
    gap_str = f"+{gap:.0f} pts" if gap > 0 else (f"{gap:.0f} pts" if gap < 0 else "0 pts")
    category_rows.append([label_map[c], str(n), f"{rp:.0f}%", f"{lp:.0f}%", gap_str])


def table_html(headers, rows, tid, num_cols_from=1):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = []
        for j, c in enumerate(r):
            cls = "left" if j == 0 else "ctr"
            tds.append(f'<td class="{cls}">{c}</td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f'<table id="{tid}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


def kv_table(rows, tid):
    trs = []
    for k, v in rows:
        trs.append(f'<tr><td class="left">{k}</td><td class="val">{v}</td></tr>')
    head = '<thead><tr><th class="left">Metric</th><th class="val">Measured value</th></tr></thead>'
    return f'<table id="{tid}">{head}<tbody>{"".join(trs)}</tbody></table>'


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  body{{margin:0;background:#fff;font-family:-apple-system,"Helvetica Neue",Arial,sans-serif;color:#111}}
  .wrap{{padding:20px 24px;display:inline-block}}
  table{{border-collapse:collapse;font-size:14px;background:#fff}}
  th,td{{padding:8px 13px;border-bottom:1px solid #d8d7d0}}
  thead th{{border-bottom:2px solid #0b0b0b;text-align:center;font-weight:700;vertical-align:bottom}}
  th.left{{text-align:left}}
  td.left{{text-align:left}} td.ctr{{text-align:center;font-variant-numeric:tabular-nums}}
  td.val,th.val{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  tbody tr:last-child td{{border-bottom:2px solid #0b0b0b}}
</style></head><body>
<div class="wrap">{kv_table(results_rows, "t_results")}</div>
<hr>
<div class="wrap">{table_html(category_header, category_rows, "t_category")}</div>
</body></html>"""

(ROOT / "tables.html").write_text(HTML)
print("Wrote", ROOT / "tables.html")
