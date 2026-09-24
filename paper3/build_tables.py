"""
Generates paper3/tables.html. Table I (positioning vs prior work) is qualitative
and hand-authored from the verified RELATED_WORK_NOTES.md. Table II (results
summary) is generated from ../blockchain_results.json so every number is real.
Render to PNG with render.py (Chrome headless), captions added by LaTeX.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
B = json.loads((ROOT.parent / "blockchain_results.json").read_text())

al = B["anchor_latency_ms"]; bl = B["baseline_hash_latency_ms"]
vl = B["verification_latency_ms"]; gas = B["gas"]; suc = B["anchored_success"]
thr = B["throughput_rps"]; tam = B["tamper_detection"]; oc = B["onchain_retrievability"]

# --- Table II rows: (metric, value) all read from real JSON ---
results_rows = [
    ("Events anchored", f"{suc['anchored_ok']:,} / {suc['attempted']:,} ({suc['success_rate_pct']:.0f}%)"),
    ("On-chain transactions mined", f"{B['onchain_txs_mined']:,}"),
    ("Mean anchoring latency", f"{al['mean_ms']:.2f} ms"),
    ("Median / p95 / p99 anchoring latency", f"{al['median_ms']:.2f} / {al['p95_ms']:.2f} / {al['p99_ms']:.2f} ms"),
    ("Baseline SHA-256 hashing (no chain)", f"{bl['mean_ms']:.4f} ms"),
    ("Anchoring overhead (chain write)", f"{B['anchoring_overhead_ms']:.2f} ms"),
    ("Mean gas per anchor", f"{gas['mean_gas']:,.0f} gas ({gas['min_gas']:,}–{gas['max_gas']:,})"),
    ("Cost per anchor", f"{gas['mean_cost_eth']:.2e} ETH"),
    ("Sequential throughput", f"{thr['sequential_anchored']:.2f} events/s"),
    (f"Concurrent throughput (n={thr['concurrency_level']})", f"{thr['concurrent_anchored']:.2f} events/s"),
    ("Verification latency", f"{vl['mean_ms']:.4f} ms/record"),
    ("Tamper-detection rate", f"{tam['detected']:,} / {tam['trials']:,} ({tam['detection_rate_pct']:.0f}%)"),
    ("False positives", f"{tam['false_positives']}"),
    ("Digest recoverable on-chain", "yes" if oc["found_on_chain"] else "no"),
]

# --- Table I: positioning (qualitative, from verified notes) ---
Y = '<span class="y">●</span>'   # filled = yes
N = '<span class="n">○</span>'   # open = no
compare_header = ["System / class", "Anchors integrity", "Threat model:<br>capturing host compromised", "Measured tamper<br>detection", "Live honeypot<br>integration"]
compare_rows = [
    ["Distributed / adaptive honeypots on blockchain<br><span class='sub'>(coordination &amp; IoT trust)</span>", Y, N, N, Y],
    ["BlockTrail; permissioned audit-log infrastructures<br><span class='sub'>(enterprise audit trails)</span>", Y, N, N, N],
    ["Immutable-log / LogStamping anchoring services<br><span class='sub'>(general log integrity)</span>", Y, N, N, N],
    ["Local hash-chained honeypot logs<br><span class='sub'>(hash on same host)</span>", N, N, N, Y],
    ["<b>This work</b><br><span class='sub'>(tamper-evident honeypot evidence)</span>", Y, Y, Y, Y],
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
  table{{border-collapse:collapse;font-size:14px;background:#fff}}
  th,td{{padding:8px 13px;border-bottom:1px solid #d8d7d0}}
  thead th{{border-bottom:2px solid #0b0b0b;text-align:center;font-weight:700;vertical-align:bottom}}
  th.left{{text-align:left}}
  td.left{{text-align:left}} td.ctr{{text-align:center}}
  td.val,th.val{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  tbody tr:last-child td{{border-bottom:2px solid #0b0b0b}}
  .y{{color:#1baf7a;font-size:15px}} .n{{color:#c9c7c0;font-size:15px}}
  .sub{{color:#77756f;font-size:11.5px;font-weight:400}}
  #t_compare tbody tr:last-child{{background:#eef4fc}}
</style></head><body>
<div class="wrap">{table_html(compare_header, compare_rows, "t_compare")}</div>
<hr>
<div class="wrap">{kv_table(results_rows, "t_results")}</div>
</body></html>"""

(ROOT / "tables.html").write_text(HTML)
print("Wrote", ROOT / "tables.html")
