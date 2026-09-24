"""
Builds paper.docx (single column) and paper_ieee.docx (two column) from the
generated paper.tex. paper.tex/paper.pdf remain canonical; the .docx files
are editable approximations: equations and algorithms are rendered as text,
tables as Word tables, figures embedded from figures/.

    /usr/bin/python3 build_docx.py     (after build_latex.py)
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).parent
TEX = (ROOT / "paper.tex").read_text()

MATH = {r"\ge": "≥", r"\le": "≤", r"\ne": "≠", r"\in": "∈", r"\cup": "∪", r"\wedge": "∧", r"\Leftrightarrow": "⇔",
        r"\gets": "←", r"\to": "→", r"\times": "×", r"\pm": "±", r"\cdot": "·", r"\emptyset": "∅",
        r"\lceil": "⌈", r"\rceil": "⌉", r"\langle": "⟨", r"\rangle": "⟩", r"\|": "‖", r"\min": "min",
        r"\mathcal{L}": "L", r"\Ledger": "L", r"\Obs": "Ω", r"\Omega": "Ω", r"\kappa": "κ", r"\tau": "τ",
        r"\rho": "ρ", r"\alpha": "α", r"\beta": "β", r"\sigma": "σ", r"\sqrt": "√", r"\bullet": "●",
        r"\mu": "μ", r"\mathcal{P}": "P", r"\mathcal{R}": "R", r"\dots": "…", r"\,": " ", r"\;": " ", r"\quad": "  ",
        r"\qquad": "    ", r"\textbf": "", r"\textit": "", r"\emph": "", r"\mathrm": "", r"\mathit": "", r"\text": "",
        r"\big": "", r"\left": "", r"\right": "", r"\log_2": "log2", r"\{": "{", r"\}": "}", r"\%": "%", r"\&": "&",
        r"\_": "_", r"\#": "#", r"\shortstack": "", r"\ldots": "…"}


def detex(s: str) -> str:
    s = re.sub(r"~?\\cite\{([^}]*)\}", lambda m: "[" + ", ".join(k.replace("ref", "") for k in m.group(1).split(",")) + "]", s)
    s = re.sub(r"(~?)\\ref\{([^}]*)\}", lambda m: (" " if m.group(1) else "") + REFS.get(m.group(2), "?"), s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\(texttt|textbf|textit|emph|mathrm|mathit|text|url|textsuperscript)\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\(texttt|textbf|textit|emph|mathrm|mathit|text|url)\{([^{}]*)\}", r"\2", s)
    for k in sorted(MATH, key=len, reverse=True):
        s = s.replace(k, MATH[k])
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"\\[ ,;:!]", " ", s)            # \  \, \; spacing escapes
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)     # escaped specials
    s = s.replace("$", "").replace("--", "–").replace("~", " ").replace("\\\\", " ")
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"[ \t]+", " ", s).strip()


_SCRIPT_RE = re.compile(r"([\^_])\{([^}]*)\}|([\^_])([A-Za-z0-9]+|\*)")


def _script_parts(text):
    """Yield (text, kind) where kind is None / 'sup' / 'sub', so that
    x^2 and P_i become real Word super/subscripts instead of literal ^ and _."""
    out, pos = [], 0
    for m in _SCRIPT_RE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], None))
        mark = m.group(1) or m.group(3)
        body = m.group(2) if m.group(2) is not None else m.group(4)
        out.append((body, "sup" if mark == "^" else "sub"))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], None))
    return out or [(text, None)]


def _caption(src):
    """Body of \\caption{...} with brace matching (captions contain math braces)."""
    m = re.search(r"\\caption\{", src)
    i = m.end(); depth = 1; out = []
    while i < len(src) and depth:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(src[i]); i += 1
    return "".join(out)

# numbering for \ref
REFS = {}
for i, m in enumerate(re.finditer(r"\\section\{([^}]*)\}\s*\\label\{([^}]*)\}", TEX), 1):
    pass
sec_no = 0; sub_no = 0; fig_no = 0; tab_no = 0; alg_no = 0; eq_no = 0
roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
for m in re.finditer(r"\\(section|subsection)\{([^}]*)\}(?:\s*\\label\{([^}]*)\})?|\\begin\{(figure\*?|table\*?|algorithm)\}.*?\\label\{([^}]*)\}|\\begin\{equation\}.*?\\label\{([^}]*)\}", TEX, re.S):
    if m.group(1) == "section":
        sec_no += 1; sub_no = 0
        if m.group(3): REFS[m.group(3)] = roman[sec_no - 1]
    elif m.group(1) == "subsection":
        sub_no += 1
        if m.group(3): REFS[m.group(3)] = f"{roman[sec_no-1]}-{chr(64+sub_no)}"
    elif m.group(4):
        kind = m.group(4).rstrip("*")
        if kind == "figure": fig_no += 1; REFS[m.group(5)] = str(fig_no)
        elif kind == "table": tab_no += 1; REFS[m.group(5)] = roman[tab_no - 1]
        else: alg_no += 1; REFS[m.group(5)] = str(alg_no)
    elif m.group(6):
        eq_no += 1; REFS[m.group(6)] = str(eq_no)


def set_cols(section, num):
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols"); section._sectPr.append(cols)
    cols.set(qn("w:num"), str(num)); cols.set(qn("w:space"), "360")


def build(ieee: bool):
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(10)
    st.paragraph_format.space_after = Pt(0)
    sec = doc.sections[0]
    sec.page_height = Inches(11); sec.page_width = Inches(8.5)
    for a in ("top_margin", "bottom_margin"): setattr(sec, a, Inches(0.75))
    for a in ("left_margin", "right_margin"): setattr(sec, a, Inches(0.72))
    col = {"n": 1}
    _num = {"sec": 0, "sub": 0}

    def ensure_cols(n):
        if not ieee or col["n"] == n:
            return
        s = doc.add_section(WD_SECTION.CONTINUOUS)
        s.top_margin = s.bottom_margin = Inches(0.75); s.left_margin = s.right_margin = Inches(0.72)
        set_cols(s, n); col["n"] = n

    def para(text, size=10, bold=False, italic=False, align=None, indent=True, mono=False):
        p = doc.add_paragraph()
        p.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
        if indent and align is None: p.paragraph_format.first_line_indent = Inches(0.14)
        p.paragraph_format.space_after = Pt(2)
        # Split on ^token / _token so they can be set as real super/subscripts.
        for part, kind in _script_parts(text):
            r = p.add_run(part)
            r.bold = bold; r.italic = italic; r.font.size = Pt(size)
            if kind == "sup":
                r.font.superscript = True
            elif kind == "sub":
                r.font.subscript = True
            if mono:
                r.font.name = "Courier New"
        return p

    # title / authors
    title = detex(re.search(r"\\title\{(.*?)\}\s*\n", TEX, re.S).group(1))
    para(title, 18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    auth = re.search(r"\\author\{(.*?)\n\}\n", TEX, re.S).group(1)

    def _blocks(src):
        """Yield the body of each \\IEEEauthorblockN/A{...} with brace matching,
        so nested braces (e.g. \\textsuperscript{1}) do not truncate the block."""
        for m in re.finditer(r"\\IEEEauthorblock[NA]\{", src):
            i = m.end(); depth = 1
            while i < len(src) and depth:
                if src[i] == "{":
                    depth += 1
                elif src[i] == "}":
                    depth -= 1
                i += 1
            yield src[m.end():i-1]

    for ln in _blocks(auth):
        for sub in ln.split("\\\\"):
            if not sub.strip():
                continue
            # keep \textsuperscript{n} as a real superscript on names/emails
            pieces = re.split(r"\\textsuperscript\{([^}]*)\}", sub)
            pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pp.paragraph_format.space_after = Pt(2)
            for idx, piece in enumerate(pieces):
                txt = detex(piece) if idx % 2 == 0 else piece.strip()
                if not txt:
                    continue
                r = pp.add_run(txt); r.font.size = Pt(10.5)
                if idx % 2:
                    r.font.superscript = True
    if ieee:
        ensure_cols(2)

    body = TEX[TEX.index(r"\maketitle") + len(r"\maketitle"):TEX.index(r"\end{document}")]
    pos = 0
    env_re = re.compile(r"\\begin\{(abstract|IEEEkeywords|enumerate|itemize|figure\*?|table\*?|algorithm|equation|thebibliography)\}(.*?)\\end\{\1\}", re.S)

    def emit_text(chunk):
        for blk in re.split(r"\n\s*\n", chunk):
            blk = blk.strip()
            if not blk:
                continue
            m = re.match(r"\\section\{(.*?)\}", blk)
            if m:
                ensure_cols(2)
                _num["sec"] += 1; _num["sub"] = 0
                _title = detex(m.group(1))
                if ieee:
                    _title = f"{roman[_num['sec']-1]}. {_title.upper()}"
                p = para(_title, 10 if ieee else 11, bold=True,
                         align=WD_ALIGN_PARAGRAPH.CENTER if ieee else WD_ALIGN_PARAGRAPH.LEFT,
                         indent=False)
                p.paragraph_format.space_before = Pt(6)
                rest = blk[m.end():].strip()
                if rest: emit_text(rest)
                continue
            m = re.match(r"\\subsection\{(.*?)\}", blk)
            if m:
                ensure_cols(2)
                _num["sub"] += 1
                _st = detex(m.group(1))
                if ieee:
                    _st = f"{chr(64 + _num['sub'])}. {_st}"
                p = para(_st, 10, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False)
                p.paragraph_format.space_before = Pt(4)
                rest = blk[m.end():].strip()
                if rest: emit_text(rest)
                continue
            ensure_cols(2)
            para(detex(blk))

    for m in env_re.finditer(body):
        emit_text(body[pos:m.start()])
        env, inner = m.group(1), m.group(2)
        pos = m.end()
        if env == "abstract":
            p = para("Abstract—" + detex(inner), 9, bold=True, indent=False)
        elif env == "IEEEkeywords":
            para("Index Terms—" + detex(inner), 9, bold=True, indent=False)
        elif env in ("enumerate", "itemize"):
            for i, it in enumerate(re.split(r"\\item\s", inner)[1:], 1):
                para(("%d) " % i if env == "enumerate" else "• ") + detex(it), indent=False)
        elif env == "equation":
            lab = re.search(r"\\label\{([^}]*)\}", inner)
            txt = detex(inner) + ("    (%s)" % REFS[lab.group(1)] if lab else "")
            para(txt, 10, align=WD_ALIGN_PARAGRAPH.CENTER)
        elif env.startswith("figure"):
            wide = env.endswith("*")
            img = re.search(r"\\includegraphics\[[^\]]*\]\{([^}]*)\}", inner).group(1)
            cap = detex(_caption(inner))
            lab = re.search(r"\\label\{([^}]*)\}", inner).group(1)
            ensure_cols(1 if (wide and ieee) else col["n"])
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(ROOT / img), width=Inches(6.9 if wide else 3.3))
            para(f"Fig. {REFS[lab]}. {cap}", 8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
            if span_page and ieee: ensure_cols(2)
        elif env.startswith("table"):
            wide = env.endswith("*")
            cap = detex(_caption(inner))
            lab = re.search(r"\\label\{([^}]*)\}", inner).group(1)
            # Body of the tabular, skipping its column specification (which may
            # itself contain braces, e.g. {@{}lp{0.62\columnwidth}@{}}).
            tb = re.search(r"\\begin\{tabular\}", inner)
            i = tb.end()
            while i < len(inner) and inner[i] in " \n":
                i += 1
            assert inner[i] == "{"
            depth = 0
            while i < len(inner):                       # skip the colspec group
                if inner[i] == "{":
                    depth += 1
                elif inner[i] == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            tab = inner[i:inner.index(r"\end{tabular}", i)]

            def _cells(line):
                """Split a tabular row on unescaped &, expanding \multicolumn."""
                parts, buf, depth = [], "", 0
                k = 0
                while k < len(line):
                    ch = line[k]
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                    if ch == "&" and depth == 0 and (k == 0 or line[k-1] != "\\"):
                        parts.append(buf); buf = ""
                    else:
                        buf += ch
                    k += 1
                parts.append(buf)
                out = []
                for part in parts:
                    part = re.sub(r"\\shortstack\{(.*?)\}", lambda m: m.group(1).replace("\\\\", " "), part, flags=re.S)
                    m = re.match(r"\s*\\multicolumn\{(\d+)\}\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\{(.*)\}\s*$",
                                 part, re.S)
                    if m:
                        span = int(m.group(1))
                        out.append(detex(m.group(2)))
                        out.extend([""] * (span - 1))    # keep column alignment
                    else:
                        out.append(detex(part))
                return out

            def _split_rows(src):
                """Split on \\\\ that are at brace depth 0, so \\shortstack{a\\\\b}
                inside a header cell does not create a spurious row."""
                out, buf, depth = [], "", 0
                k = 0
                while k < len(src):
                    ch = src[k]
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                    if ch == "\\" and k + 1 < len(src) and src[k+1] == "\\" and depth == 0:
                        out.append(buf); buf = ""; k += 2; continue
                    buf += ch; k += 1
                out.append(buf)
                return out

            rows = []
            for ln in _split_rows(tab):
                ln = re.sub(r"\\(?:toprule|midrule|bottomrule)\b", "", ln)
                ln = re.sub(r"\\cmidrule(?:\([^)]*\))?\{[^}]*\}", "", ln)
                ln = ln.strip()
                if not ln or ln.startswith("%"):
                    continue
                cells = _cells(ln)
                if any(c.strip() for c in cells):
                    rows.append(cells)

            # Merge a header that LaTeX wrote as stacked \shortstack-style lines:
            # if a row has the same cell count and the previous row's trailing
            # cells are empty, LaTeX layout handled it; Word does not need it.
            # A table with many columns cannot fit a 3.3in text column in Word;
            # lay it across the full page width as IEEE does with table*.
            ncol_probe = max(len(r) for r in rows)
            widest_row = max(sum(len(v) for v in r) for r in rows)
            span_page = wide or ncol_probe >= 6 or widest_row > 46
            ensure_cols(1 if (span_page and ieee) else col["n"])
            para(f"TABLE {REFS[lab]}. {cap}", 8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
            ncol = max(len(r) for r in rows)
            t = doc.add_table(rows=len(rows), cols=ncol)
            t.style = "Table Grid"
            t.autofit = True
            t.allow_autofit = True
            # width proportional to the longest cell in each column
            widths = []
            for j in range(ncol):
                vals = [r[j] for r in rows if j < len(r)]
                longest = max((len(v) for v in vals), default=1)
                # a single unbreakable token must fit, else Word wraps and clips
                token = max((max((len(w) for w in v.split()), default=1) for v in vals), default=1)
                longest = int(max(longest, token * 1.6) * 1.15) + 2
                widths.append(max(longest, 3))
            total = sum(widths)
            avail = Inches(6.8 if (span_page and ieee) else 3.3)
            for i, r in enumerate(rows):
                for j in range(ncol):
                    c = t.cell(i, j)
                    val = r[j] if j < len(r) else ""
                    # keep "119.2 ± 8.0" on one line: non-breaking spaces
                    val = re.sub(r"(\d)\s*\u00b1\s*(\d)", "\\1\u00a0\u00b1\u00a0\\2", val)
                    c.text = val
                    c.width = Inches(avail.inches * widths[j] / total)
                    for pp in c.paragraphs:
                        pp.paragraph_format.space_before = Pt(0)
                        pp.paragraph_format.space_after = Pt(0)
                        for rr in pp.runs:
                            rr.font.size = Pt(7)
                            if i == 0:
                                rr.bold = True
            # A row whose content sits entirely in the first cell is a spanning
            # sub-heading (e.g. "(a) Sybil: ..."); merge it so the text is not
            # squeezed into one narrow column.
            for i, r in enumerate(rows):
                filled = [j for j, v in enumerate(r) if v.strip()]
                if len(filled) == 1 and filled[0] == 0 and ncol > 1:
                    try:
                        merged = t.cell(i, 0).merge(t.cell(i, ncol - 1))
                        # a merge concatenates each source cell's paragraph;
                        # drop the empty ones so the row is a single tight line
                        keep = False
                        for pp in list(merged.paragraphs):
                            if pp.text.strip() and not keep:
                                keep = True
                            else:
                                pp._element.getparent().remove(pp._element)
                    except Exception:
                        pass

            # never let Word clip a row
            for row in t.rows:
                trPr = row._tr.get_or_add_trPr()
                for h in trPr.findall(qn("w:trHeight")):
                    trPr.remove(h)
            doc.add_paragraph()
            if span_page and ieee: ensure_cols(2)
        elif env == "algorithm":
            cap = detex(re.search(r"\\caption\{(.*?)\}\n", inner, re.S).group(1))
            lab = re.search(r"\\label\{([^}]*)\}", inner).group(1)
            ensure_cols(2)
            para(f"Algorithm {REFS[lab]} {cap}", 9, bold=True, indent=False)
            code = re.search(r"\\begin\{algorithmic\}(?:\[\d\])?(.*?)\\end\{algorithmic\}", inner, re.S).group(1)
            depth = 0; n = 0
            for ln in code.strip().splitlines():
                ln = ln.strip()
                if not ln: continue
                if re.match(r"\\(EndFor|EndIf)", ln): depth -= 1; continue
                if ln.startswith("\\ElsIf"): depth -= 1
                n += 1
                txt = re.sub(r"\\(State|For|If|ElsIf|Return)", lambda mm: {"State": "", "For": "for ", "If": "if ", "ElsIf": "else if ", "Return": "return "}[mm.group(1)], ln)
                para(f"{n:2d}: " + "    " * max(depth, 0) + detex(txt), 8.5, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, mono=True)
                if re.match(r"\\(For|If|ElsIf)", ln): depth += 1
            doc.add_paragraph()
        elif env == "thebibliography":
            ensure_cols(2)
            para("REFERENCES" if ieee else "References", 10, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER if ieee else WD_ALIGN_PARAGRAPH.LEFT)
            for i, it in enumerate(re.split(r"\\bibitem\{[^}]*\}", inner)[1:], 1):
                para(f"[{i}] " + detex(it), 8.5, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT)
    emit_text(body[pos:])
    out = ROOT / ("paper_ieee.docx" if ieee else "paper.docx")
    doc.save(str(out)); print("Saved", out)


if __name__ == "__main__":
    build(False); build(True)
