"""
Generates paper5/tables.html. Table I (positioning vs prior work / centralized
threat-intel platforms) is qualitative and hand-authored. Table II (results
summary) is generated from federation_results.json so every number is real.
Render to PNG with render.py (Chrome headless), captions added by LaTeX.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
F = json.loads((ROOT / "federation_results.json").read_text())

al = F["aggregate_anchor_latency_ms"]
prop = F["cross_node_propagation"]
dd = F["dedup_and_consensus"]
res = F["compromised_node_resilience"]
thr = F["concurrent_node_throughput"]
meta = F["meta"]

seq_rps = F["sequential_baseline_throughput"]["throughput_rps"]

# --- Table II rows: (metric, value) all read from real JSON ---
results_rows = [
    ("Simulated honeypot nodes", f"{meta['n_nodes']}"),
    ("IOCs observed per node", f"{meta['iocs_per_node']}"),
    ("Total anchored events", f"{F['total_anchored_txs']:,}"),
    ("Configured overlap fraction", f"{meta['overlap_fraction_config']*100:.0f}%"),
    ("Mean / median / p95 anchor latency", f"{al['mean_ms']:.2f} / {al['median_ms']:.2f} / {al['p95_ms']:.2f} ms"),
    ("Cross-node propagation trials", f"{prop['trials']}"),
    ("Propagation observed success rate", f"{prop['observed_success_rate_pct']:.0f}%"),
    ("Mean / p95 propagation latency", f"{prop['latency_ms']['mean_ms']:.2f} / {prop['latency_ms']['p95_ms']:.2f} ms"),
    ("Local IOCs reconstructed from chain", f"{dd['total_reconstructed_from_chain']} / {dd['total_local_iocs']} ({dd['recall_pct']:.0f}%)"),
    ("Ground-truth shared IOCs", f"{dd['ground_truth_shared_iocs']}"),
    ("Corroborated by 2+ nodes", f"{dd['corroborated_by_2plus_nodes']}"),
    ("Corroboration precision / recall", f"{dd['corroboration_precision_pct']:.0f}% / {dd['corroboration_recall_pct']:.0f}%"),
    ("Compromised-node tamper detected", "yes" if res["tamper_detected_via_shared_ledger"] else "no"),
    ("Concurrent nodes / events attempted", f"{thr['nodes']} / {thr['attempted']}"),
    ("Concurrent aggregate throughput", f"{thr['aggregate_throughput_rps']:.2f} events/s"),
    ("Single-writer baseline (this harness)", f"{seq_rps:.2f} events/s"),
]

# --- Table I: positioning (qualitative) ---
Y = '<span class="y">&#9679;</span>'
N = '<span class="n">&#9675;</span>'
compare_header = ["System / class", "No trusted<br>coordinator", "New node bootstraps<br>from chain alone", "Measured cross-node<br>corroboration", "Compromised-node<br>detection via peers"]
compare_rows = [
    ["MISP federated instances [1], [4]<br><span class='sub'>(configured sync relationships)</span>", N, N, N, N],
    ["STIX/TAXII hub-and-collection [2], [3]<br><span class='sub'>(client-server feeds)</span>", N, N, N, N],
    ["Blockchain CTI sharing with<br>on-chain policy / reputation [6]-[10]<br><span class='sub'>(contract-mediated trust logic)</span>", Y, N, N, N],
    ["Blockchain-coordinated honeypots [12]<br><span class='sub'>(trust arbitration between sensors)</span>", Y, N, N, N],
    ["<b>This work</b><br><span class='sub'>(hash-only passive bulletin board)</span>", Y, Y, Y, Y],
]


def table_html(headers, rows, tid, first_left=True):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = []
        for j, c in enumerate(r):
            cls = "left" if (j == 0 and first_left) else "ctr"
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
  table{{border-collapse:collapse;font-size:13.5px;background:#fff}}
  th,td{{padding:8px 12px;border-bottom:1px solid #d8d7d0}}
  thead th{{border-bottom:2px solid #0b0b0b;text-align:center;font-weight:700;vertical-align:bottom}}
  th.left{{text-align:left}}
  td.left{{text-align:left}} td.ctr{{text-align:center}}
  td.val,th.val{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  tbody tr:last-child td{{border-bottom:2px solid #0b0b0b}}
  .y{{color:#1baf7a;font-size:15px}} .n{{color:#c9c7c0;font-size:15px}}
  .sub{{color:#77756f;font-size:11px;font-weight:400}}
  #t_compare tbody tr:last-child{{background:#eef4fc}}
</style></head><body>
<div class="wrap">{table_html(compare_header, compare_rows, "t_compare")}</div>
<hr>
<div class="wrap">{kv_table(results_rows, "t_results")}</div>
</body></html>"""

(ROOT / "tables.html").write_text(HTML)
print("Wrote", ROOT / "tables.html")
