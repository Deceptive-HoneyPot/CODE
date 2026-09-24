"""
Builds paper.tex from paper_src.tex by substituting every @@TOKEN@@ with a
value computed from fingerprint_results.json, then compiles with tectonic.
    /usr/bin/python3 build_latex.py
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
F = json.loads((ROOT / "fingerprint_results.json").read_text())
meta, e1, e2, e3, e4 = F["meta"], F["e1_conformance"], F["e2_timing"], F["e3_corpus"], F["e4_mitigation"]


def f0(x): return f"{x:,.0f}"
def f1(x): return f"{x:.1f}"
def f2(x): return f"{x:.2f}"
def pct(x): return f"{100*x:.1f}".rstrip("0").rstrip(".")


def esc(t):
    return (t.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
             .replace("#", r"\#").replace("{", r"\{").replace("}", r"\}").replace("$", r"\$").replace("~", r"\textasciitilde{}").replace("^", r"\^{}"))


def short(v, n=30):
    """Compact, human-readable form of a probe observation for the table."""
    s = str(v).replace("\n", " / ")
    s = re.sub(r"keys=\['error', 'id', 'jsonrpc'\] error.code=(-?\d+)", r"error \1", s)
    s = s.replace("keys=['id', 'jsonrpc', 'result']", "result, no error")
    s = re.sub(r"http=(\d+) str:.*", r"HTTP \1", s)
    s = re.sub(r"http=(\d+) list\[(\d+)\]", r"HTTP \1, \2 results", s)
    s = re.sub(r"http=(\d+) Server=(\S+) X-Jenkins=(\S+) X-Hudson=\S+",
               lambda m: f"HTTP {m.group(1)}, {m.group(2)}" + ("" if m.group(3) == "-" else ", X-Jenkins"), s)
    s = re.sub(r"http=(\d+) Server=(\S+)", r"HTTP \1, \2", s)
    s = re.sub(r"http=(\d+) ct=application/json keys=\[([^\]]*)\]", lambda m: "JSON keys " + m.group(2).replace("'", ""), s)
    s = re.sub(r"http=(\d+) *$", r"HTTP \1", s)
    s = s.replace("Ganache/v7.9.2/EthereumJS TestRPC/v7.9.2/ethereum-js", "Ganache/v7.9.2/...")
    s = s.replace("chacha20-poly1305@openssh.com", "chacha20-poly1305")
    s = re.sub(r"^(0x[0-9A-Fa-f]+) then \1$", "constant", s)
    s = s.replace("cat: /etc/nosuchfile: No such file or directory", "cat: ...: No such file or directory")
    s = s.replace("bash: hostname; uname -n: command not found", "command not found")
    s = re.sub(r"^([0-9a-f]{12}) / \1$", "same name twice", s)
    if s == "":
        s = "(empty)"
    return esc(s if len(s) <= n else s[:n - 1] + "…")


# E1 table rows grouped by service
PROBE_LABEL = {
    "protocol banner": "Version banner", "host-key type offered": "Host-key type", "cipher negotiated (same client)": "Cipher negotiated",
    "random credentials accepted": "Random credentials accepted", "exec request honored": "\\texttt{exec} request honored",
    "shell arithmetic $((7*6))": "\\texttt{echo \\$((7*6))}", "missing-file error format": "\\texttt{cat} missing file",
    "unknown command error format": "Unknown command", "pwd after cd /tmp": "\\texttt{cd /tmp; pwd}",
    "hostname vs uname -n consistency": "\\texttt{hostname; uname -n}", "echo of quoted string": "\\texttt{echo 'a  b'}",
    "web3_clientVersion": "\\texttt{web3\\_clientVersion}", "eth_chainId": "\\texttt{eth\\_chainId}",
    "unknown method -> error code": "Unknown method", "malformed JSON body": "Malformed body",
    "string id echoed as string": "String id echoed", "batch request (array)": "Batch request",
    "eth_getBalance without params": "\\texttt{eth\\_getBalance}, no params", "eth_blockNumber monotonic (two calls)": "\\texttt{eth\\_blockNumber} twice",
    "eth_getBlockByNumber latest -> field count": "\\texttt{eth\\_getBlockByNumber}",
    "GET / -> status, Server, X-Jenkins": "\\texttt{GET /}", "GET /api/json -> status, content-type, top-level keys": "\\texttt{GET /api/json}",
    "GET /nonexistent -> status, Server": "\\texttt{GET} unknown path", "GET /login -> status": "\\texttt{GET /login}",
    "HEAD / -> status": "\\texttt{HEAD /}", "GET /robots.txt -> status": "\\texttt{GET /robots.txt}",
    "POST /job/build/api/json -> status": "\\texttt{POST} build trigger", "GET /api/json?depth=0 -> repeated call identical?": "\\texttt{GET /api/json} repeated",
}
VALUE_FIX = {
    "SSH-2.0-AsyncSSH_2.23.1": "AsyncSSH 2.23.1", "SSH-2.0-OpenSSH_10.3": "OpenSSH 10.3",
    "cat: /etc/nosuchfile: No such file or directory": "No such file or directory",
    "frobnicate: command not foun": "``command not foun'' (truncated)", "-bash: frobnicate: command not found": "``-bash: \\ldots: command not found''",
    "bash: hostname; uname -n: command not found": "command not found", "50c6c971be27\n50c6c971be27": "same name twice",
    "": "(empty)", "True": "yes", "False": "no",
    "http=200 ct=application/json keys=['_class', 'assignedLabels', 'description', 'jobs', 'mode', 'nodeDescription']": "JSON keys \\_class, assignedLabels, \\ldots",
    "http=200 ct=application/json keys=['result']": "JSON key result only",
}


def cell(v):
    s = str(v)
    if s in VALUE_FIX:
        return VALUE_FIX[s]
    return short(s, 40)


svc_name = {"ssh": "SSH", "rpc": "JSON-RPC", "ci": "CI/HTTP"}
e1_rows, e1_counts = [], {}
for r in e1:
    e1_counts.setdefault(r["service"], [0, 0]); e1_counts[r["service"]][1] += 1
    e1_counts[r["service"]][0] += int(r["distinguishing"])
for svc in ("ssh", "rpc", "ci"):
    e1_rows.append(r"\midrule" if svc != "ssh" else "")
    e1_rows.append(r"\multicolumn{4}{@{}l}{\textit{%s} (%d of %d probes distinguish)} \\" % (svc_name[svc], *e1_counts[svc]))
    for r in e1:
        if r["service"] != svc:
            continue
        e1_rows.append(f"{PROBE_LABEL.get(r['probe'], esc(r['probe']))} & {cell(r['decoy'])} & {cell(r['real'])} & {'yes' if r['distinguishing'] else 'no'} \\\\")
e1_total = sum(v[0] for v in e1_counts.values()); e1_n = sum(v[1] for v in e1_counts.values())

# E2 table rows
label = {("ssh", "auth"): ("SSH", "connect + authenticate"), ("ssh", "static"): ("SSH", "recon command (static)"),
         ("ssh", "cache"): ("SSH", "repeated command (cache)"), ("ssh", "llm"): ("SSH", "novel command (LLM)"),
         ("ssh", "session5"): ("SSH", "5-command recon session"),
         ("rpc", "static"): ("JSON-RPC", "known method (static)"), ("rpc", "cache"): ("JSON-RPC", "repeated call (cache)"),
         ("rpc", "llm"): ("JSON-RPC", "novel call (LLM)"),
         ("ci", "unknown_path_static"): ("CI/HTTP", "unknown path (404)"), ("ci", "api_json_llm"): ("CI/HTTP", "GET /api/json (cache)"),
         ("ci", "build_post_llm"): ("CI/HTTP", "POST build (LLM)")}
e2_rows = []
order = [("ssh", "auth"), ("ssh", "static"), ("ssh", "cache"), ("ssh", "llm"), ("ssh", "session5"),
         ("rpc", "static"), ("rpc", "cache"), ("rpc", "llm"), ("ci", "unknown_path_static"), ("ci", "api_json_llm"), ("ci", "build_post_llm")]
for svc, k in order:
    v = e2[svc][k]; d, r = v["decoy"], v["real"]
    e2_rows.append(f"{label[(svc,k)][0]} & {label[(svc,k)][1]} & {d['median']:,.1f} & {d['p95']:,.0f} & {r['median']:.1f} & {r['p95']:.1f} & {v['auc']:.3f} \\\\")

def g(svc, k, side, stat): return e2[svc][k][side][stat]

# E3 rows
svc_label = {"ssh": "SSH shell", "sql": "SQL gateway", "api": "AI API", "web3": "JSON-RPC", "cicd": "CI server"}
ref_med = {"ssh": e2["ssh"]["llm"]["real"]["median"], "web3": e2["rpc"]["llm"]["real"]["median"],
           "cicd": e2["ci"]["build_post_llm"]["real"]["median"]}
e3_rows, meds = [], []
for svc in ("ssh", "sql", "api", "web3", "cicd"):
    tiers = e3["by_service"].get(svc, {})
    n = sum(t["count"] for t in tiers.values())
    llm = tiers.get("llm", {}); L = llm.get("latency_ms", {})
    meds.append(L.get("median", 0))
    rm = f"{ref_med[svc]:.1f}" if svc in ref_med else "--"
    e3_rows.append(f"{svc_label[svc]} & {n} & {llm.get('count', 0)} ({100*llm.get('count', 0)/n:.0f}\\%) & {L.get('median', 0):,.0f} & {L.get('p95', 0):,.0f} & {L.get('max', 0):,.0f} & {rm} \\\\")
fp = e3["first_pass"]; sp = e3["second_pass_sample"]

SUBS = {
    "TRIALS": str(meta["trials"]), "RUNTIME_MIN": f0(meta["runtime_s"] / 60),
    "REAL_SSH": esc(meta.get("real_ssh", "")), "DECOY_SSH": esc(meta.get("decoy_ssh", "")),
    "REAL_RPC": esc(meta.get("real_rpc", "")), "REAL_CI": esc(f"Jenkins {meta.get('real_ci_version','')} ({meta.get('real_ci_server','')})"),
    "E1_ROWS": "\n".join(e1_rows), "E1_TOTAL": str(e1_total), "E1_N": str(e1_n),
    "E1_SSH": f"{e1_counts['ssh'][0]}/{e1_counts['ssh'][1]}", "E1_RPC": f"{e1_counts['rpc'][0]}/{e1_counts['rpc'][1]}", "E1_CI": f"{e1_counts['ci'][0]}/{e1_counts['ci'][1]}",
    "E2_ROWS": "\n".join(e2_rows),
    "SSH_STATIC_D": f1(g("ssh", "static", "decoy", "median")), "SSH_STATIC_R": f1(g("ssh", "static", "real", "median")),
    "SSH_STATIC_AUC": f"{e2['ssh']['static']['auc']:.3f}", "SSH_STATIC_ACC": f"{100*e2['ssh']['static']['threshold']['accuracy']:.0f}",
    "SSH_LLM_D": f0(g("ssh", "llm", "decoy", "median")), "SSH_LLM_D_P95": f0(g("ssh", "llm", "decoy", "p95")), "SSH_LLM_D_MIN": f0(g("ssh", "llm", "decoy", "min")),
    "SSH_LLM_R": f1(g("ssh", "llm", "real", "median")), "SSH_LLM_AUC": f"{e2['ssh']['llm']['auc']:.3f}",
    "SSH_CACHE_D": f1(g("ssh", "cache", "decoy", "median")), "SSH_CACHE_R": f1(g("ssh", "cache", "real", "median")), "SSH_CACHE_AUC": f"{e2['ssh']['cache']['auc']:.3f}",
    "SSH_AUTH_D": f0(g("ssh", "auth", "decoy", "median")), "SSH_AUTH_R": f0(g("ssh", "auth", "real", "median")), "SSH_AUTH_AUC": f"{e2['ssh']['auth']['auc']:.3f}",
    "SSH_SESS_D": f0(g("ssh", "session5", "decoy", "median")), "SSH_SESS_R": f0(g("ssh", "session5", "real", "median")), "SSH_SESS_AUC": f"{e2['ssh']['session5']['auc']:.3f}",
    "RPC_STATIC_D": f1(g("rpc", "static", "decoy", "median")), "RPC_STATIC_R": f1(g("rpc", "static", "real", "median")), "RPC_STATIC_AUC": f"{e2['rpc']['static']['auc']:.3f}",
    "RPC_LLM_D": f0(g("rpc", "llm", "decoy", "median")), "RPC_LLM_R": f1(g("rpc", "llm", "real", "median")), "RPC_LLM_AUC": f"{e2['rpc']['llm']['auc']:.3f}",
    "RPC_CACHE_D": f1(g("rpc", "cache", "decoy", "median")), "RPC_CACHE_AUC": f"{e2['rpc']['cache']['auc']:.3f}",
    "CI_404_D": f1(g("ci", "unknown_path_static", "decoy", "median")), "CI_404_R": f1(g("ci", "unknown_path_static", "real", "median")), "CI_404_AUC": f"{e2['ci']['unknown_path_static']['auc']:.3f}",
    "CI_API_D": f0(g("ci", "api_json_llm", "decoy", "median")), "CI_API_R": f1(g("ci", "api_json_llm", "real", "median")), "CI_API_AUC": f"{e2['ci']['api_json_llm']['auc']:.3f}",
    "CI_BUILD_D": f0(g("ci", "build_post_llm", "decoy", "median")), "CI_BUILD_R": f1(g("ci", "build_post_llm", "real", "median")), "CI_BUILD_AUC": f"{e2['ci']['build_post_llm']['auc']:.3f}",
    "SSH_REPEAT_D": f0(e2["ssh"]["repeat_same_session"]["decoy"]["median"]),
    "SSH_AUTH_ACC": f"{100*e2['ssh']['auth']['threshold']['accuracy']:.0f}",
    "SSH_STATIC_RATIO": f0(g("ssh", "static", "decoy", "median") / g("ssh", "static", "real", "median")),
    "E3_N": f0(e3["n"]), "E3_FAILED": str(e3["failed"]), "E3_WALL_MIN": f1(e3["wall_s"] / 60), "E3_CONC": str(e3["concurrency"]),
    "E3_STATIC_PCT": pct(fp["static"]["share"]), "E3_CACHE_PCT": pct(fp["cache"]["share"]), "E3_LLM_PCT": pct(fp["llm"]["share"]),
    "E3_STATIC_N": f0(fp["static"]["count"]), "E3_LLM_N": f0(fp["llm"]["count"]),
    "E3_LLM_MED": f0(fp["llm"]["latency_ms"].get("median", 0)), "E3_LLM_P95": f0(fp["llm"]["latency_ms"].get("p95", 0)), "E3_LLM_MAX": f0(fp["llm"]["latency_ms"].get("max", 0)),
    "E3_STATIC_MED": f1(fp["static"]["latency_ms"].get("median", 0)) if fp["static"]["count"] else "--",
    "E3_ROWS": "\n".join(e3_rows), "E3_MED_LO": f0(min(meds)), "E3_MED_HI": f0(max(meds)),
    "E3_SP_CACHE_PCT": pct(sp["cache"]["share"]), "E3_SP_CACHE_MED": f1(sp["cache"]["latency_ms"].get("median", 0)), "E3_SP_CACHE_P95": f1(sp["cache"]["latency_ms"].get("p95", 0)),
    "E4_CORPUS": f0(e4["corpus"]), "E4_DISTINCT_EXACT": f0(e4["distinct_exact_keys"]), "E4_DISTINCT_NORM": f0(e4["distinct_normalized_keys"]),
    "E4_TEST": f0(e4["split_test"]), "E4_EXACT_HITS": str(e4["exact_key_hits"]), "E4_NORM_HITS": str(e4["normalized_key_hits"]),
    "E4_EXACT_PCT": pct(e4["exact_hit_rate"]), "E4_NORM_PCT": pct(e4["normalized_hit_rate"]),
    "E4_ROWS": "\n".join(f"{svc_label.get(s, s)} & {v['test']} & {v['normalized_hits']} & {100*v['normalized_hits']/max(v['test'],1):.1f}\\% \\\\" for s, v in e4["by_service"].items()),
}


def bibliography():
    items = []
    for ln in (ROOT / "references.md").read_text().splitlines():
        m = re.match(r"^\[(\d+)\]\s*(.+)$", ln.strip())
        if not m:
            continue
        body = m.group(2).strip(); url = None
        u = re.search(r"\[Online\]\.\s*Available:\s*(\S+)", body)
        if u:
            url = u.group(1); body = body[:u.start()].rstrip()
        body = re.sub(r"\*(.+?)\*", lambda mm: "\x01" + mm.group(1) + "\x02", body)
        body = body.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
        body = body.replace("\x01", r"\emph{").replace("\x02", "}")
        body = re.sub(r'"([^"]*)"', lambda mm: "``" + mm.group(1) + "''", body)
        body = body.rstrip(". ") + "."
        if url:
            body += " [Online]. Available: \\url{" + url + "}"
        items.append(f"\\bibitem{{ref{m.group(1)}}} {body}")
    return "\n".join(items)


def build():
    src = (ROOT / "paper_src.tex").read_text()
    SUBS["BIBLIOGRAPHY"] = bibliography()
    missing = sorted(set(re.findall(r"@@([A-Z0-9_]+)@@", src)) - set(SUBS))
    if missing:
        raise SystemExit(f"missing tokens: {missing}")
    (ROOT / "paper.tex").write_text(re.sub(r"@@([A-Z0-9_]+)@@", lambda m: SUBS[m.group(1)], src))
    print("Wrote paper.tex")
    if shutil.which("tectonic"):
        r = subprocess.run(["tectonic", "paper.tex"], cwd=ROOT, capture_output=True, text=True)
        print(r.stderr[-1500:]); print("tectonic exit", r.returncode)


if __name__ == "__main__":
    build()
