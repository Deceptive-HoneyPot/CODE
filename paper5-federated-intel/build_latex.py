"""
Builds paper.tex from paper_src.tex by substituting every @@TOKEN@@ with a
value computed from federation_results.json (output of
benchmark_federation.py). Then compiles with tectonic if available.

    /usr/bin/python3 build_latex.py
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
F = json.loads((ROOT / "federation_results.json").read_text())
meta = F["meta"]
e1 = {r["N"]: r for r in F["e1_scaling"]}
hub = {int(k): v for k, v in F["e7_hub"]["sweep"].items()}
out = F["e7_hub"]["outage"]
enc = F["e2_gas"]["encoding"]
bat = {b["B"]: b for b in F["e2_gas"]["batching"]}
boot = F["e3_bootstrap"]
acc = F["e4_accuracy"]
adv = F["e5_adversary"]
tam = F["e6_tamper"]
prop = F["e8_propagation"]
cr = adv["echo_commit_reveal"]
plain = adv["echo_plain"]

ganache_ver = re.search(r"v([0-9.]+)", meta["ganache_client"]).group(1)


def f0(x): return f"{x:,.0f}"
def f1(x): return f"{x:.1f}"
def f2(x): return f"{x:.2f}"
def pct(x): return f"{100*x:.1f}".rstrip("0").rstrip(".")


gas_ascii = enc["ascii"]["gas_measured"]["mean"]
gas_bin = enc["binary"]["gas_measured"]["mean"]
gas_cr = cr["gas_per_ioc_total"]

scaling_rows = []
for N in meta["n_sweep"]:
    r, h = e1[N], hub[N]
    L = r["latency_ms"]
    scaling_rows.append(
        f"{N} & {r['throughput_mean']:.1f} $\\pm$ {r['throughput_ci95']:.1f} & {L['median']:.2f} & "
        f"{L['p95']:.1f} & {L['p99']:.0f} & {L['max']:.0f} & "
        f"{h['throughput_mean']:.0f} $\\pm$ {h['throughput_ci95']:.0f} & {h['latency_ms']['median']:.2f} \\\\")

acc_rows = []
names = {"exact": r"$\kappa_{\mathrm{exact}}$", "payload": r"$\kappa_{\mathrm{payload}}$",
         "template": r"$\kappa_{\mathrm{tmpl}}$", "net24+template": r"$\kappa_{\mathrm{net}}$"}
for k in ("exact", "payload", "template", "net24+template"):
    s = acc["summary"][k]
    acc_rows.append(
        f"{names[k]} & {s['precision']:.3f} $\\pm$ {s['precision_ci95']:.3f} & "
        f"{s['recall']:.3f} $\\pm$ {s['recall_ci95']:.3f} & {s['f1']:.3f} $\\pm$ {s['f1_ci95']:.3f} & "
        f"{s['tp']}/{s['fp']}/{s['fn']} \\\\")

syb_rows = [f"{r['identities']} & & {r['corroborated_k2']} & {r['corroborated_k3']} & {r['corroborated_k4']} \\\\"
            for r in adv["sybil"]]

per_kind = ", ".join(f"{v['detected']}/{v['trials']}" for v in tam["per_kind"].values())

SUBS = {
    "GANACHE_VER": ganache_ver, "CHAIN_ID": str(meta["chain_id"]), "ACCOUNTS": str(meta["accounts"]),
    "RUNTIME_S": f0(meta["total_runtime_s"]), "BLOCKS": f0(meta["blocks_produced"]),
    "REPS": str(meta["reps"]), "EV_PER_NODE": str(meta["events_per_node_sweep"]),
    "RPC_MEAN": f2(meta["rpc_floor_ms"]["mean"]), "RPC_P95": f2(meta["rpc_floor_ms"]["p95"]),
    "E1_TOTAL": f0(sum(r["ok"] for r in e1.values())),
    "THR_1": f0(e1[1]["throughput_mean"]), "THR_2": f0(e1[2]["throughput_mean"]), "THR_4": f0(e1[4]["throughput_mean"]),
    "THR_16": f0(e1[16]["throughput_mean"]),
    "MED_1": f2(e1[1]["latency_ms"]["median"]), "MED_16": f2(e1[16]["latency_ms"]["median"]),
    "MEAN_1": f2(e1[1]["latency_ms"]["mean"]),
    "P99_8": f0(e1[8]["latency_ms"]["p99"]), "P99_16": f0(e1[16]["latency_ms"]["p99"]),
    "MAX_16": f0(e1[16]["latency_ms"]["max"]),
    "HUB_THR_1": f0(hub[1]["throughput_mean"]), "HUB_THR_16": f0(hub[16]["throughput_mean"]),
    "HUB_MED_1": f2(hub[1]["latency_ms"]["median"]), "HUB_MED_16": f2(hub[16]["latency_ms"]["median"]),
    "HUB_RATIO": f1(hub[16]["throughput_mean"] / e1[16]["throughput_mean"]),
    "OUT_ACC": str(out["accepted_before_outage"]), "OUT_ATT": str(out["attempted"]),
    "OUT_REJ": str(out["rejected_during_outage"]),
    "GAS_ASCII": f0(gas_ascii), "GAS_BIN": f0(gas_bin),
    "GAS_ASCII_MODEL": f0(enc["ascii"]["gas_model"]["mean"]), "GAS_BIN_MODEL": f0(enc["binary"]["gas_model"]["mean"]),
    "GAS_ASCII_CALLDATA": f0(gas_ascii - 21000),
    "GAS_SAVE_PCT": f1(100 * (gas_ascii - gas_bin) / gas_ascii),
    "GAS_B1": f0(bat[1]["gas_per_ioc"]), "GAS_B8": f0(bat[8]["gas_per_ioc"]), "GAS_B64": f0(bat[64]["gas_per_ioc"]),
    "GAS_B8_TX": f0(bat[8]["gas_per_tx"]["mean"]), "GAS_B64_TX": f0(bat[64]["gas_per_tx"]["mean"]),
    "GAS_BATCH_TX": f0(sum(b["gas_per_tx"]["mean"] for b in bat.values()) / len(bat)),
    "GAS_B64_PCT": f1(100 * bat[64]["gas_per_ioc"] / 21000),
    "LAT_B1": f2(bat[1]["latency_per_ioc_ms"]), "LAT_B64": f2(bat[64]["latency_per_ioc_ms"]),
    "PROOFS_TOTAL": f0(sum(b["proofs_total"] for b in bat.values())),
    "BATCH_TRIALS": str(bat[1]["trials"]),
    "BOOT_SLOPE": f2(boot["fit"]["ms_per_block"]), "BOOT_R2": f"{boot['fit']['r2']:.3f}",
    "BOOT_HMAX": f0(boot["rows"][-1]["H"]), "BOOT_TMAX": f1(boot["rows"][-1]["seconds_mean"]),
    "ACC_NODES": str(acc["nodes"]), "ACC_IOCS": str(acc["iocs_per_node"]), "ACC_CAMPS": str(acc["campaigns"]),
    "ACC_TOTAL_ANCHORS": f0(sum(r["anchored"] for k in acc["per_rep"] for r in acc["per_rep"][k])),
    "REC_EXACT_PCT": pct(acc["summary"]["exact"]["recall"]),
    "REC_PAYLOAD_PCT": pct(acc["summary"]["payload"]["recall"]),
    "PREC_PAYLOAD_PCT": pct(acc["summary"]["payload"]["precision"]),
    "PREC_NET_PCT": pct(acc["summary"]["net24+template"]["precision"]),
    "REC_NET_PCT": pct(acc["summary"]["net24+template"]["recall"]),
    "F1_TEMPLATE": f2(acc["summary"]["template"]["f1"]), "F1_NET": f2(acc["summary"]["net24+template"]["f1"]),
    "SYB_F": str(adv["sybil"][0]["fabricated"]),
    "ECHO_SINGLES": str(plain["honest_single_node_digests"]), "ECHO_PLAIN_FP": str(plain["falsely_corroborated"]),
    "ECHO_PLAIN_PCT": pct(plain["false_corroboration_rate"]), "ECHO_COST_S": f2(plain["echo_cost_s"]),
    "CR_SHARED": str(cr["shared_digests"]), "CR_SINGLES": str(cr["honest_single_node_digests"]),
    "CR_REJECTED": str(cr["echo_reveals_rejected"]), "ECHO_CR_FP": str(cr["falsely_corroborated"]),
    "ECHO_CR_PCT": pct(cr["false_corroboration_rate"]),
    "GAS_CR": f0(gas_cr), "GAS_CR_C": f0(cr["gas_commit"]["mean"]), "GAS_CR_R": f0(cr["gas_reveal"]["mean"]),
    "CR_GAS_MULT": f1(gas_cr / gas_ascii),
    "CR_LAT_C": f1(cr["latency_commit_ms"]["mean"]), "CR_LAT_R": f1(cr["latency_reveal_ms"]["mean"]),
    "TAMPER_N": str(tam["trials"]), "TAMPER_DET": str(tam["detected"]), "TAMPER_FP": str(tam["controls_flagged"]),
    "TAMPER_PER_KIND": per_kind, "TAMPER_US": f1(tam["check_time_us"]["mean"]),
    "PROP_N": str(prop["trials"]), "PROP_MEAN": f2(prop["latency_ms"]["mean"]), "PROP_P95": f2(prop["latency_ms"]["p95"]),
    "SCALING_ROWS": "\n".join(scaling_rows), "ACC_ROWS": "\n".join(acc_rows), "SYB_ROWS": "\n".join(syb_rows),
}


def esc_ref(t):
    t = t.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
    t = t.replace("–", "--").replace("—", "---").replace("’", "'")
    return t


def bibliography():
    """Numbered reference list from references.md (IEEE style, one per line)."""
    items = []
    for ln in (ROOT / "references.md").read_text().splitlines():
        m = re.match(r"^\[(\d+)\]\s*(.+)$", ln.strip())
        if not m:
            continue
        body = m.group(2).strip()
        url = None
        u = re.search(r"\[Online\]\.\s*Available:\s*(\S+)", body)
        if u:
            url = u.group(1); body = body[:u.start()].rstrip()
        body = re.sub(r"\*(.+?)\*", lambda mm: "\x01" + mm.group(1) + "\x01", body)
        body = esc_ref(body).replace("\x01", "\\emph{", 1)
        while "\x01" in body:
            body = body.replace("\x01", "}", 1).replace("\x01", "\\emph{", 1)
        body = re.sub(r'"([^"]*)"', lambda mm: "``" + mm.group(1) + "''", body)
        body = body.rstrip(". ") + "."
        if url:
            body += " [Online]. Available: \\url{" + url + "}"
        items.append(f"\\bibitem{{ref{m.group(1)}}} {body}")
    return "\n".join(items)


def build():
    src = (ROOT / "paper_src.tex").read_text()
    SUBS["BIBLIOGRAPHY"] = bibliography()
    tex = re.sub(r"@@([A-Z0-9_]+)@@", lambda m: SUBS[m.group(1)], src)
    (ROOT / "paper.tex").write_text(tex)
    print("Wrote paper.tex")
    if shutil.which("tectonic"):
        r = subprocess.run(["tectonic", "paper.tex"], cwd=ROOT, capture_output=True, text=True)
        print(r.stdout[-1500:], r.stderr[-3000:])
        print("tectonic exit", r.returncode)


if __name__ == "__main__":
    build()
