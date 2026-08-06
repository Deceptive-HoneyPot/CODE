"""
Builds paper2/paper.tex — an official IEEEtran (IEEE conference) LaTeX source
from paper.md, with real numbers substituted from ../evaluation_results.json
and figures/tables emitted as proper IEEE floats (figure / figure* for
single- vs double-column). Compile on Overleaf with the IEEEtran class.

Output conventions match IEEE Xplore papers:
  - \\documentclass[conference]{IEEEtran}
  - Roman-numeral sections via \\section (automatic)
  - Abstract + \\IEEEkeywords
  - \\caption gives "Fig. N" / "TABLE N" automatically
  - Wide items use figure*/table* (span both columns)
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
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
    "DIV_SSH": f"{div.get('ssh',{}).get('uniqueness_ratio','')}", "DIV_SQL": f"{div.get('sql',{}).get('uniqueness_ratio','')}",
    "DIV_API": f"{div.get('api',{}).get('uniqueness_ratio','')}", "DIV_WEB3": f"{div.get('web3',{}).get('uniqueness_ratio','')}",
    "DIV_CICD": f"{div.get('cicd',{}).get('uniqueness_ratio','')}",
    "SQL_DISTINCT": f"{div.get('sql',{}).get('distinct','')}", "SQL_N": f"{div.get('sql',{}).get('n','')}",
    "REALISM_MEAN": f"{realism['mean_score_1to5']}", "REALISM_STDEV": f"{realism['stdev']}",
    "REALISM_N": str(realism['n_scored']), "JUDGE_N": str(R['config']['judge_sample_size']),
    "CLF_SAMPLE_N": "1{,}000", "DASH_TOTAL": "6{,}742",
    # Table cross-refs: literal Roman numerals matching the caption text
    # (captions are authored as "Table I/II/III", so refer to them by name).
    "TAB_POOL": "II", "TAB_COMPARE": "I", "TAB_QUANT": "III",
}

# token -> (file, float_env, caption, label)
IMG = {
    "FIG_ARCH":  ("diag_arch.png",  "figure*", "System architecture. Only the proxy and dashboard are on the public boundary; the five decoys, response engine, collector, datastore, and blockchain node communicate solely on the isolated internal network.", "fig:arch"),
    "FIG_FLOW":  ("diag_flow.png",  "figure*", "Data flow for one interaction: the proxy logs the connection before any decoy responds; the collector classifies, hashes, anchors on-chain, and streams to the dashboard.", "fig:flow"),
    "FIG_TIER":  ("diag_tier.png",  "figure",  "Three-tier response path. Routine requests are answered from the static table or cache in sub-millisecond time; only novel requests reach the language model.", "fig:tier"),
    "FIG_CHAIN": ("diag_chain.png", "figure",  "Anchoring and tamper verification. A record's SHA-256 digest is committed on-chain; re-hashing and comparison later detects any modification.", "fig:chain"),
    "FIG_DASH":  ("dashboard.png",  "figure*", "Live dashboard capture during operation, showing intent breakdown, per-service exposure, and anchoring status.", "fig:dash"),
    "FIG_ATTACKERS": ("dash_attackers.png", "figure*", "Per-attacker drill-down: services touched, severity rating, intent mix, and a timeline of the real payloads sent (a genuine captured session).", "fig:attackers"),
    "FIG_LAT":   ("fig2_latency.png", "figure", "Mean response latency, static vs.\\ dynamic path (log scale).", "fig:lat"),
    "FIG_THRU":  ("fig3_throughput.png", "figure", "Throughput: static, sequential, and concurrent (log scale).", "fig:thru"),
    "FIG_DIV":   ("fig4_diversity.png", "figure", "Response diversity (uniqueness ratio) by decoy service.", "fig:div"),
    "FIG_REAL":  ("fig5_realism.png", "figure", "LM-judge realism score distribution.", "fig:real"),
    "FIG_DOMINANCE": ("fig10_dominance.png", "figure*", "Capability coverage across honeypot classes. Our system is the only design scoring highly on every dimension at once.", "fig:dominance"),
    # table images rendered as figures for fidelity; captioned as tables
    "TAB_PERSERVICE_BODY": ("tab_perservice.png", "figure*", "\\textsc{Table IV.} Per-service evaluation results on the 2,500-payload corpus.", "tab:perservice"),
    "TAB_QUANT_BODY":  ("tab_quant.png",  "figure*", "\\textsc{Table III.} Honeypot taxonomy and quantitative comparison, using each system's own published figures.", "tab:quant"),
    "TAB_COMPARE_BODY":("tab_compare.png","figure*", "\\textsc{Table I.} Property comparison with prior categories of work.", "tab:compare"),
    "TAB_POOL_BODY":   ("tab_pool.png",   "figure",  "\\textsc{Table II.} Connection-pooling before/after (real measurements).", "tab:pool"),
}


def esc(t):
    """Escape LaTeX special chars in body prose (not in math/commands)."""
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("$", r"\$"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        t = t.replace(a, b)
    # smart punctuation / unicode common in the source
    reps = {"—": "---", "–": "--", "“": "``", "”": "''", "‘": "`", "’": "'",
            "×": r"$\times$", "→": r"$\rightarrow$", "≈": r"$\approx$",
            "≥": r"$\geq$", "≤": r"$\leq$", "±": r"$\pm$", "§": r"Sec.~",
            "…": r"\ldots{}", "•": r"$\bullet$"}
    for a, b in reps.items():
        t = t.replace(a, b)
    return t


def convert(t):
    """Full markdown->LaTeX for a run of prose, in the correct order:
    1) protect {{TOKEN}} substitutions behind unescapable sentinels
    2) escape LaTeX special chars in the remaining prose
    3) apply markdown emphasis (re-injecting \textbf etc.)
    4) restore the protected substitutions (which may themselves be LaTeX)
    """
    # 1) protect subs — use a sentinel with NO special chars and no letters
    #    that esc() touches. Digits + control char are safe.
    order = list(SUBS.keys())
    def prot(m):
        k = m.group(1)
        if k in SUBS:
            return "\x00%d\x00" % order.index(k)
        return m.group(0)
    t = re.sub(r"\{\{([A-Z0-9_]+)\}\}", prot, t)
    # 2) escape
    t = esc(t)
    # 3) markdown emphasis
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"\*(.+?)\*", r"\\emph{\1}", t)
    t = re.sub(r"`(.+?)`", r"\\texttt{\1}", t)
    # 4) restore subs (esc() leaves \x00 digits \x00 intact — digits/NUL aren't escaped)
    def restore(m):
        return SUBS[order[int(m.group(1))]]
    t = re.sub(r"\x00(\d+)\x00", restore, t)
    return t


def emit_float(token):
    fname, env, cap, label = IMG[token]
    is_table = token.startswith("TAB_")
    star = env.endswith("*")
    width = r"\textwidth" if star else r"\columnwidth"
    if is_table:
        # Real IEEE table float: caption ABOVE, numbered "TABLE N" automatically,
        # so the caption text must NOT itself say "Table III." (that produced the
        # "\textsc{Table III.}" duplication the reviewer flagged). The table body
        # is a rendered image, scaled to the float width.
        table_env = "table*" if star else "table"
        cap_clean = re.sub(r"\\textsc\{Table\s+[IVX]+\.\}\s*", "", cap).strip()
        return (f"\\begin{{{table_env}}}[!t]\n\\centering\n"
                f"\\caption{{{cap_clean}}}\n\\label{{{label}}}\n"
                f"\\includegraphics[width={width}]{{figures/{fname}}}\n"
                f"\\end{{{table_env}}}\n")
    # Figure float: caption BELOW.
    return (f"\\begin{{{env}}}[!t]\n\\centering\n"
            f"\\includegraphics[width={width}]{{figures/{fname}}}\n"
            f"\\caption{{{cap}}}\n\\label{{{label}}}\n"
            f"\\end{{{env}}}\n")


HEADER = r"""\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
% IEEE requires Times. The classic \usepackage{times} sets Times New Roman for
% the text (and the matching math), is what the official IEEE templates use,
% and — unlike newtxmath — does not clash with amssymb. This is the explicit
% fix for the "Latin Modern default" font issue.
\usepackage{times}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage[hyphens]{url}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
\begin{document}

\title{A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging}

\author{
\IEEEauthorblockN{Radhika G\textsuperscript{1}, Sisir Reddy Nellore\textsuperscript{2}, Pranav Sharma Chouduru\textsuperscript{3}, Surya Tejeswar Reddy Nagireddy\textsuperscript{4},\\ Guru Sai Prasad Reddy Bompalli\textsuperscript{5}, Vishnu Sathwick Rajala\textsuperscript{6}}
\IEEEauthorblockA{\textit{Department of Computer Science and Engineering}\\
\textit{Amrita School of Computing, Coimbatore}\\
\textit{Amrita Vishwa Vidyapeetham, India}\\
g\_radhika@cb.amrita.edu\textsuperscript{1}, cb.sc.u4cse23129@cb.students.amrita.edu\textsuperscript{2},\\
cb.sc.u4cse23611@cb.students.amrita.edu\textsuperscript{3}, cb.sc.u4cse23127@cb.students.amrita.edu\textsuperscript{4},\\
cb.sc.u4cse23111@cb.students.amrita.edu\textsuperscript{5}, cb.sc.u4cse23644@cb.students.amrita.edu\textsuperscript{6}}
}

\maketitle
"""

FOOTER = r"""
\end{document}
"""


def build():
    md = (ROOT / "paper.md").read_text()
    lines = md.split("\n")
    out = [HEADER]

    # locate abstract + index terms + body start
    i = 0
    # skip title/author (handled in HEADER) up to first "## Abstract"
    while i < len(lines) and lines[i].strip() != "## Abstract":
        i += 1
    i += 1  # past "## Abstract"

    # gather abstract until "**Index Terms**" or next "##"
    abs_lines = []
    while i < len(lines) and not lines[i].strip().startswith("**Index Terms") \
            and not lines[i].strip().startswith("## "):
        if lines[i].strip() and lines[i].strip() != "---":
            abs_lines.append(lines[i].strip())
        i += 1
    abstract = " ".join(abs_lines)
    abstract = convert(abstract)
    out.append("\n\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n")

    # index terms
    if i < len(lines) and lines[i].strip().startswith("**Index Terms"):
        # Index Terms may wrap across several source lines; gather them all
        # until a blank line so no fragment leaks out as a stray paragraph.
        kw_lines = [lines[i].strip()]
        i += 1
        while i < len(lines) and lines[i].strip() != "" and lines[i].strip() != "---" \
                and not lines[i].strip().startswith("## "):
            kw_lines.append(lines[i].strip())
            i += 1
        idx = " ".join(kw_lines)
        idx = re.sub(r"\*\*Index Terms\*\*\s*[—-]*\s*", "", idx)
        idx = convert(idx)
        out.append("\n\\begin{IEEEkeywords}\n" + idx + "\n\\end{IEEEkeywords}\n")

    # walk the rest of the body
    def flush_para(buf):
        if not buf:
            return
        txt = " ".join(buf)
        txt = convert(txt)
        out.append("\n" + txt + "\n")

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
            title = re.sub(r"^\d+\.\s*", "", s[3:])  # strip "1." — IEEEtran auto-numbers
            title = convert(title)
            # skip Abstract (already done) and References (handled specially)
            if title.strip().lower() == "references":
                out.append("\n% ==== References ====\n")
                # emit remaining reference lines as a manual thebibliography
                i += 1
                refs = []
                while i < len(lines):
                    rs = lines[i].rstrip()
                    if rs.strip():
                        refs.append(rs.strip())
                    i += 1
                out.append(emit_bibliography(refs))
                break
            out.append("\n\\section{" + title + "}\n")
            i += 1; continue

        if s.startswith("### "):
            flush_para(para); para = []
            sub = re.sub(r"^\d+\.\d+\s*", "", s[4:])
            sub = convert(sub)
            out.append("\n\\subsection{" + sub + "}\n")
            i += 1; continue

        if s.startswith("> "):
            flush_para(para); para = []
            q = convert(s[2:])
            out.append("\n\\textit{" + q + "}\n")
            i += 1; continue

        if re.match(r"^\d+\.\s", s) or s.startswith("- "):
            flush_para(para); para = []
            ordered = bool(re.match(r"^\d+\.\s", s))
            env = "enumerate" if ordered else "itemize"
            items = []
            # Gather ALL items of this one list into a single environment.
            # Markdown separates items with blank lines, so a blank line does
            # NOT end the list — we look ahead past blank lines and only stop
            # when the next real content is not another list item (or is a
            # heading/float token). Continuation (wrapped) lines are appended
            # to the current \item.
            def _is_item(x):
                return bool(re.match(r"^\d+\.\s", x)) or x.startswith("- ")

            while i < len(lines):
                ls = lines[i].strip()
                if _is_item(ls):
                    body = re.sub(r'^\d+\.\s', '', ls) if re.match(r"^\d+\.\s", ls) else ls[2:]
                    items.append(convert(body))
                    i += 1
                elif ls == "":
                    # peek: is the next non-blank line still a list item?
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and _is_item(lines[j].strip()):
                        i = j  # skip the blank(s), continue the same list
                    else:
                        i += 1
                        break  # list truly ends
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
    """Convert one complete reference string (markdown) to a LaTeX bibitem body.
    Handles emphasis, drops parenthetical *(...)* asides, and wraps any URL in
    \\url{} without letting esc() mangle the URL's characters."""
    # Drop italic parenthetical guidance asides like *(Confirm ...)*
    body = re.sub(r"\*\(.*?\)\*", "", body).strip()
    # Pull out an "[Online]. Available: URL" tail (or a bare trailing URL) so we
    # can protect the URL from LaTeX escaping.
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
    # markdown emphasis -> LaTeX, then escape the remaining prose safely
    # (protect emphasis by converting to sentinels first)
    body = re.sub(r"\*(.+?)\*", lambda m: "\x01" + m.group(1) + "\x01", body)
    body = esc(body)
    body = body.replace("\x01", "").replace("\x01", "")  # emphasis flattened; titles already in quotes
    out = body
    if not out.endswith("."):
        out += "."
    if url:
        out += " [Online]. Available: \\url{" + url + "}"
    return out


def emit_bibliography(ref_lines):
    """Assemble a proper thebibliography from the markdown reference block.
    Continuation lines (a reference wrapped across several source lines) are
    joined back into one entry; the leading '>' verification note is dropped."""
    # Join wrapped lines: a new entry begins with "[n]"; everything else is a
    # continuation of the current entry. Lines starting with '>' are the note.
    entries = []
    cur = None
    for ln in ref_lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith(">"):
            continue  # verification note — omit from the compiled paper
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
