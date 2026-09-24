"""
Generate a BibTeX references.bib from paper5's paper.md numbered reference
list. Self-contained parser for this paper's reference section.
"""
import re
import sys
from pathlib import Path


def strip_md(t):
    t = re.sub(r"\*\((?:Confirm|confirm).*?\)\*", "", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    t = t.replace("–", "--").replace("—", "---")
    return t.strip()


def parse_entry(raw):
    raw = strip_md(raw).rstrip(". ").strip()
    d = {}
    m = re.search(r"(?:\[Online\]\.\s*Available:\s*)?(https?://\S+)", raw)
    if m:
        d["url"] = m.group(1).rstrip(".")
        raw = raw[:m.start()].rstrip(" .[Online].Available:").rstrip()
        raw = re.sub(r"\[Online\]\.\s*Available:\s*$", "", raw).rstrip(" .")
    ym = re.search(r"\b(19|20)\d{2}\b", raw)
    if ym:
        d["year"] = ym.group(0)
    tm = re.search(r'"([^"]+)"', raw)
    if tm:
        d["title"] = tm.group(1).rstrip(",.")
        author = raw[:tm.start()].rstrip(", ")
        rest = raw[tm.end():].lstrip(", ")
    else:
        fc = raw.find(",")
        author = raw[:fc] if fc != -1 else ""
        tail = raw[fc + 1:] if fc != -1 else raw
        tm2 = re.match(r"\s*(.+?)\.\s", tail)
        if tm2:
            d["title"] = tm2.group(1).strip()
            rest = tail[tm2.end():]
        else:
            d["title"] = tail.strip()
            rest = tail
    if author:
        a = author.strip()
        a = re.sub(r",\s*and\s+", " and ", a)
        a = re.sub(r"\s+and\s+", " and ", a)
        a = re.sub(r",\s*", " and ", a)
        a = re.sub(r"\s+et\s+al\.?", " and others", a)
        a = re.sub(r"\s+and\s+and\s+", " and ", a)
        d["author"] = a.strip()
    vm = re.search(r"vol\.?\s*(\d+)", rest)
    if vm: d["volume"] = vm.group(1)
    nm = re.search(r"no\.?\s*(\d+)", rest)
    if nm: d["number"] = nm.group(1)
    pm = re.search(r"pp\.?\s*([\dA-Za-z]+--?[\dA-Za-z]+|\d+)", rest)
    if pm: d["pages"] = pm.group(1)
    entrytype = "misc"
    proc = re.search(r"(?:in\s+)?(Proc\.[^,]*|Proceedings[^,]*)", rest)
    if proc:
        entrytype = "inproceedings"
        d["booktitle"] = proc.group(1).strip().rstrip(".")
    else:
        jm = re.match(r"\s*([A-Z][^,]+?),\s*(?:vol|no|pp)\.", rest)
        if jm:
            entrytype = "article"
            d["journal"] = jm.group(1).strip()
        elif "Standard" in rest:
            entrytype = "misc"
    if entrytype == "misc" and "howpublished" not in d and d.get("url"):
        d["howpublished"] = "\\url{%s}" % d["url"]
    return entrytype, d


def to_bib(n, entrytype, d):
    au = d.get("author", "anon")
    surname = re.sub(r"[^A-Za-z]", "", au.split(",")[0].split(" and ")[0].split()[-1] if au.split() else "anon")
    key = f"ref{n}_{surname.lower()}{d.get('year','')}"
    lines = [f"@{entrytype}{{{key},"]
    order = ["author", "title", "journal", "booktitle", "publisher", "address",
             "institution", "volume", "number", "pages", "year", "howpublished", "url", "note"]
    for f in order:
        if f in d and d[f]:
            lines.append(f"  {f} = {{{d[f]}}},")
    lines.append("}")
    return key, "\n".join(lines)


def build(md_path, out_path):
    t = Path(md_path).read_text()
    ref_block = t[t.index("## References"):]
    raws = re.findall(r"^\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", ref_block, re.S | re.M)
    bibs, keys = [], {}
    for n, raw in raws:
        raw = " ".join(l.strip() for l in raw.splitlines() if l.strip() and not l.strip().startswith(">"))
        etype, d = parse_entry(raw)
        key, bib = to_bib(int(n), etype, d)
        keys[n] = key
        bibs.append(bib)
    Path(out_path).write_text("\n\n".join(bibs) + "\n")
    print(f"Wrote {out_path}  ({len(bibs)} entries)")
    return keys


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
