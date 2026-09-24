"""
Builds paper3-journal/paper.tex — an extended IEEEtran JOURNAL-format (single
column) paper on the blockchain-anchored tamper-evident audit trail, with
every number substituted from the REAL ../blockchain_results.json produced by
benchmark_blockchain.py. This is the extended ~15-page journal version of the
7-page paper3/ conference paper: same measured data, substantially expanded
prose (deeper related work, full canonicalization/API description, a tamper
taxonomy, a projected public/permissioned cost model, and a future-work
section).

Reuses the proven paper2/paper3 build conventions (token protection, LaTeX
escaping, IEEE floats, manual thebibliography). Compile with tectonic or on
Overleaf.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
B = json.loads((ROOT.parent / "blockchain_results.json").read_text())

al = B["anchor_latency_ms"]
bl = B["baseline_hash_latency_ms"]
vl = B["verification_latency_ms"]
gas = B["gas"]
suc = B["anchored_success"]
thr = B["throughput_rps"]
tam = B["tamper_detection"]
oc = B["onchain_retrievability"]
meta = B["meta"]

verify_ratio = round(al["mean_ms"] / vl["mean_ms"]) if vl["mean_ms"] else 0
_gv = re.search(r"v([0-9.]+)", meta["ganache_client"])
ganache_ver = _gv.group(1) if _gv else "dev"

SUBS = {
    # anchor latency
    "ANCHOR_N": f"{al['n']:,}",
    "ANCHOR_MEAN": f"{al['mean_ms']:.2f}",
    "ANCHOR_MEDIAN": f"{al['median_ms']:.2f}",
    "ANCHOR_STDEV": f"{al['stdev_ms']:.2f}",
    "ANCHOR_P95": f"{al['p95_ms']:.2f}",
    "ANCHOR_P99": f"{al['p99_ms']:.2f}",
    "ANCHOR_MIN": f"{al['min_ms']:.2f}",
    "ANCHOR_MAX": f"{al['max_ms']:.2f}",
    # baseline hashing
    "BASE_N": f"{bl['n']:,}",
    "BASE_MEAN": f"{bl['mean_ms']:.4f}",
    "OVERHEAD_MS": f"{B['anchoring_overhead_ms']:.2f}",
    # verification
    "VERIFY_MEAN": f"{vl['mean_ms']:.4f}",
    "VERIFY_MEDIAN": f"{vl['median_ms']:.4f}",
    "VERIFY_RATIO": f"{verify_ratio:,}",
    # gas
    "GAS_MEAN": f"{gas['mean_gas']:,.0f}",
    "GAS_MIN": f"{gas['min_gas']:,}",
    "GAS_MAX": f"{gas['max_gas']:,}",
    "GAS_COST_ETH": f"{gas['mean_cost_eth']:.2e}".replace("e-0", "e-").replace("e+0", "e+"),
    # success / throughput
    "ANCHOR_OK": f"{suc['anchored_ok']:,}",
    "ANCHOR_RATE": f"{suc['success_rate_pct']:.0f}",
    "TX_MINED": f"{B['onchain_txs_mined']:,}",
    "SEQ_RPS": f"{thr['sequential_anchored']:.2f}",
    "CONC_RPS": f"{thr['concurrent_anchored']:.2f}",
    "CONC_LEVEL": f"{thr['concurrency_level']}",
    # tamper
    "TAMPER_TRIALS": f"{tam['trials']:,}",
    "TAMPER_DETECTED": f"{tam['detected']:,}",
    "TAMPER_RATE": f"{tam['detection_rate_pct']:.0f}",
    "TAMPER_FP": f"{tam['false_positives']}",
    # onchain / meta
    "ONCHAIN_FOUND": "yes" if oc["found_on_chain"] else "no",
    "CHAIN_ID": f"{meta['chain_id']}",
    "GANACHE_VER": ganache_ver,
    # table cross-refs (Roman numerals matching captions)
    "TAB_COMPARE": "I",
    "TAB_RESULTS": "II",
}

# token -> (file, float_env, caption, label)
IMG = {
    "FIG_PIPELINE": ("diag_pipeline.png", "figure*",
        "The tamper-evident anchoring pipeline. A captured interaction is canonically serialized and hashed by the internal collector (off the exposed decoy host); the digest is anchored on-chain; verification later re-hashes the stored record and compares it against the on-chain commitment.",
        "fig:pipeline"),
    "FIG_CHAIN": ("diag_threat.png", "figure",
        "The evidence-integrity threat. The attacker owns the decoy and can edit its local log, but the anchored digest lies on a ledger outside the compromise boundary, so any edit is detectable.",
        "fig:threat"),
    "FIG_LATENCY": ("fig_latency.png", "figure",
        "Anchoring cost decomposed: on-chain anchoring versus isolated SHA-256 hashing (log scale). The integrity guarantee is dominated by the on-chain commitment, not the cryptography.",
        "fig:latency"),
    "FIG_GAS": ("fig_gas.png", "figure",
        "Measured gas per anchor read from real transaction receipts, against the 21,000-gas Ethereum base-transaction floor.",
        "fig:gas"),
    "FIG_TAMPER": ("fig_tamper.png", "figure",
        "Tamper-detection outcome over all trials: every single-field modification was detected, with no false positives.",
        "fig:tamper"),
    # tables rendered as images, captioned as tables (caption above)
    "TAB_COMPARE_BODY": ("tab_compare.png", "table*",
        "How this work is positioned against prior blockchain-logging and blockchain-honeypot systems. The distinguishing axis is the evidence-integrity threat model, in which the capturing host is itself compromised.",
        "tab:compare"),
    "TAB_RESULTS_BODY": ("tab_results.png", "table",
        "Summary of measured results against the live stack.",
        "tab:results"),
}


def esc(t):
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("$", r"\$"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        t = t.replace(a, b)
    reps = {"—": "---", "–": "--", "“": "``", "”": "''", "‘": "`", "’": "'",
            "×": r"$\times$", "→": r"$\rightarrow$", "≈": r"$\approx$",
            "≥": r"$\geq$", "≤": r"$\leq$", "±": r"$\pm$", "§": r"Sec.~",
            "…": r"\ldots{}", "•": r"$\bullet$", "≠": r"$\neq$",
            "′": r"$'$"}
    for a, b in reps.items():
        t = t.replace(a, b)
    return t


def convert(t):
    order = list(SUBS.keys())
    def prot(m):
        k = m.group(1)
        if k in SUBS:
            return "\x00%d\x00" % order.index(k)
        return m.group(0)
    t = re.sub(r"\{\{([A-Z0-9_]+)\}\}", prot, t)
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"\*(.+?)\*", r"\\emph{\1}", t)
    t = re.sub(r"`(.+?)`", r"\\texttt{\1}", t)
    def restore(m):
        return SUBS[order[int(m.group(1))]]
    t = re.sub(r"\x00(\d+)\x00", restore, t)
    return t


def emit_float(token):
    fname, env, cap, label = IMG[token]
    is_table = token.startswith("TAB_")
    # IEEEtran's journal option is still two-column (the standard IEEE
    # Transactions layout), same as conference mode, so wide tables/figures
    # still need the starred (double-column-spanning) float environments.
    star = env.endswith("*")
    width = r"\textwidth" if star else r"\columnwidth"
    cap = convert(cap)
    if is_table:
        table_env = "table*" if star else "table"
        return (f"\\begin{{{table_env}}}[!t]\n\\centering\n"
                f"\\caption{{{cap}}}\n\\label{{{label}}}\n"
                f"\\includegraphics[width={width}]{{figures/{fname}}}\n"
                f"\\end{{{table_env}}}\n")
    return (f"\\begin{{{env}}}[!t]\n\\centering\n"
            f"\\includegraphics[width={width}]{{figures/{fname}}}\n"
            f"\\caption{{{cap}}}\n\\label{{{label}}}\n"
            f"\\end{{{env}}}\n")


HEADER = r"""\documentclass[journal]{IEEEtran}
\IEEEoverridecommandlockouts
\usepackage{times}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage[hyphens]{url}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
\begin{document}

\title{A Blockchain-Anchored Tamper-Evident Audit Trail for Honeypot Forensics}

\author{Sisir~Reddy~Nellore, Radhika~G, Pranav~Sharma~Chouduru, and Surya~Tejeswar~Reddy~Nagireddy%
\thanks{The authors are with the Department of Computer Science and
Engineering, Amrita School of Computing, Coimbatore, Amrita Vishwa
Vidyapeetham, India. E-mail: cb.sc.u4cse23129@cb.students.amrita.edu,
g\_radhika@cb.amrita.edu, cb.sc.u4cse23611@cb.students.amrita.edu,
cb.sc.u4cse23127@cb.students.amrita.edu}}

\markboth{Preprint, Project Journal Submission, August~2026}%
{Nellore \MakeLowercase{\textit{et al.}}: A Blockchain-Anchored Tamper-Evident Audit Trail for Honeypot Forensics}

\maketitle
"""

FOOTER = "\n\\end{document}\n"


def build():
    md = (ROOT / "paper.md").read_text()
    lines = md.split("\n")
    out = [HEADER]

    i = 0
    while i < len(lines) and lines[i].strip() != "## Abstract":
        i += 1
    i += 1

    abs_lines = []
    while i < len(lines) and not lines[i].strip().startswith("**Index Terms") \
            and not lines[i].strip().startswith("## "):
        if lines[i].strip() and lines[i].strip() != "---":
            abs_lines.append(lines[i].strip())
        i += 1
    out.append("\n\\begin{abstract}\n" + convert(" ".join(abs_lines)) + "\n\\end{abstract}\n")

    if i < len(lines) and lines[i].strip().startswith("**Index Terms"):
        kw_lines = [lines[i].strip()]
        i += 1
        while i < len(lines) and lines[i].strip() != "" and lines[i].strip() != "---" \
                and not lines[i].strip().startswith("## "):
            kw_lines.append(lines[i].strip())
            i += 1
        idx = " ".join(kw_lines)
        idx = re.sub(r"\*\*Index Terms\*\*\s*[—-]*\s*", "", idx)
        out.append("\n\\begin{IEEEkeywords}\n" + convert(idx) + "\n\\end{IEEEkeywords}\n")

    def flush_para(buf):
        if buf:
            out.append("\n" + convert(" ".join(buf)) + "\n")

    para = []
    while i < len(lines):
        s = lines[i].strip()

        m = re.fullmatch(r"\{\{([A-Z0-9_]+)\}\}", s)
        if m and m.group(1) in IMG:
            flush_para(para); para = []
            out.append("\n" + emit_float(m.group(1)))
            i += 1; continue

        if s == "" or s == "---":
            flush_para(para); para = []; i += 1; continue

        if s.startswith("## "):
            flush_para(para); para = []
            title = re.sub(r"^\d+\.\s*", "", s[3:])
            if title.strip().lower() == "references":
                out.append("\n% ==== References ====\n")
                i += 1
                refs = []
                while i < len(lines):
                    if lines[i].strip():
                        refs.append(lines[i].strip())
                    i += 1
                out.append(emit_bibliography(refs))
                break
            out.append("\n\\section{" + convert(title) + "}\n")
            i += 1; continue

        if s.startswith("### "):
            flush_para(para); para = []
            sub = re.sub(r"^\d+\.\d+\s*", "", s[4:])
            out.append("\n\\subsection{" + convert(sub) + "}\n")
            i += 1; continue

        if re.match(r"^\d+\.\s", s) or s.startswith("- "):
            flush_para(para); para = []
            ordered = bool(re.match(r"^\d+\.\s", s))
            env = "enumerate" if ordered else "itemize"
            items = []
            def _is_item(x):
                return bool(re.match(r"^\d+\.\s", x)) or x.startswith("- ")
            while i < len(lines):
                ls = lines[i].strip()
                if _is_item(ls):
                    body = re.sub(r'^\d+\.\s', '', ls) if re.match(r"^\d+\.\s", ls) else ls[2:]
                    items.append(convert(body))
                    i += 1
                elif ls == "":
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and _is_item(lines[j].strip()):
                        i = j
                    else:
                        i += 1
                        break
                elif ls.startswith(("#", ">")) or re.fullmatch(r"\{\{[A-Z0-9_]+\}\}", ls):
                    break
                elif items:
                    items[-1] += " " + convert(ls)
                    i += 1
                else:
                    break
            out.append("\n\\begin{" + env + "}\n")
            for it in items:
                out.append("\\item " + it + "\n")
            out.append("\\end{" + env + "}\n")
            continue

        para.append(s)
        i += 1

    flush_para(para)
    out.append(FOOTER)
    (ROOT / "paper.tex").write_text("".join(out))
    print("Wrote", ROOT / "paper.tex")


def _ref_to_latex(body):
    body = re.sub(r"\*\(.*?\)\*", "", body).strip()
    url = None
    m = re.search(r"\[Online\]\.\s*Available:\s*(\S+)", body)
    if m:
        url = m.group(1)
        body = body[:m.start()].rstrip()
    else:
        m = re.search(r"(https?://\S+)", body)
        if m:
            url = m.group(1)
            body = body[:m.start()].rstrip()
    body = body.rstrip(". ").strip()
    body = re.sub(r"\*(.+?)\*", lambda m: "\x01" + m.group(1) + "\x01", body)
    body = esc(body)
    body = body.replace("\x01", "")
    out = body
    if not out.endswith("."):
        out += "."
    if url:
        out += " [Online]. Available: \\url{" + url + "}"
    return out


def emit_bibliography(ref_lines):
    entries = []
    cur = None
    for ln in ref_lines:
        s = ln.strip()
        if not s or s.startswith(">"):
            continue
        if re.match(r"^\[\d+\]", s):
            if cur is not None:
                entries.append(cur)
            cur = re.sub(r"^\[\d+\]\s*", "", s)
        elif cur is not None:
            cur += " " + s
    if cur is not None:
        entries.append(cur)
    tex = ["\n\\begin{thebibliography}{00}\n"]
    for idx, e in enumerate(entries, 1):
        tex.append("\\bibitem{ref%d} %s\n" % (idx, _ref_to_latex(e)))
    tex.append("\\end{thebibliography}\n")
    return "".join(tex)


if __name__ == "__main__":
    build()
