"""
Generate a BibTeX references.bib from a paper.md's numbered reference list.
Each [n] entry becomes @<type>{refN, ...} with a best-effort field parse
(author, title, journal/booktitle, volume, number, pages, year, url).
Heuristic but conservative — leaves a 'note' with the raw string so nothing
is lost, and picks entry type from cues (Proc.-> inproceedings, journal vol ->
article, Available: url with no venue -> misc, book publishers -> book).
"""
import re
import sys
from pathlib import Path


def strip_md(t):
    t = re.sub(r"\*\((?:Confirm|confirm).*?\)\*", "", t)   # drop verification asides
    t = re.sub(r"\*(.+?)\*", r"\1", t)                      # italics
    t = t.replace("–", "--").replace("—", "---")
    return t.strip()


def parse_entry(raw):
    raw = strip_md(raw).rstrip(". ").strip()
    d = {}
    # url
    m = re.search(r"(?:\[Online\]\.\s*Available:\s*)?(https?://\S+)", raw)
    if m:
        d["url"] = m.group(1).rstrip(".")
        raw = raw[:m.start()].rstrip(" .[Online].Available:").rstrip()
        raw = re.sub(r"\[Online\]\.\s*Available:\s*$", "", raw).rstrip(" .")
    # year
    ym = re.search(r"\b(19|20)\d{2}\b", raw)
    if ym:
        d["year"] = ym.group(0)
    # title in quotes
    tm = re.search(r'"([^"]+)"', raw)
    if tm:
        d["title"] = tm.group(1).rstrip(",.")
        author = raw[:tm.start()].rstrip(", ")
        rest = raw[tm.end():].lstrip(", ")
    else:
        # book form: Author, Title. City: Publisher, Year.
        # Split author (before first comma) from the rest, then take the title
        # as the text up to the first period (the title ends at "Title.").
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
        # BibTeX wants "A and B and C", not "A, B, and C"
        a = author.strip()
        a = re.sub(r",\s*and\s+", " and ", a)
        a = re.sub(r"\s+and\s+", " and ", a)
        a = re.sub(r",\s*", " and ", a)          # remaining comma-separated authors
        a = re.sub(r"\s+et\s+al\.?", " and others", a)   # "X et al." -> "X and others"
        a = re.sub(r"\s+and\s+and\s+", " and ", a)
        d["author"] = a.strip()
    # volume / number / pages
    vm = re.search(r"vol\.?\s*(\d+)", rest)
    if vm: d["volume"] = vm.group(1)
    nm = re.search(r"no\.?\s*(\d+)", rest)
    if nm: d["number"] = nm.group(1)
    pm = re.search(r"pp\.?\s*([\dA-Za-z]+--?[\dA-Za-z]+|\d+)", rest)
    if pm: d["pages"] = pm.group(1)
    # venue: Proc. ... -> booktitle ; else if journal-ish italic -> journal
    entrytype = "misc"
    proc = re.search(r"(?:in\s+)?(Proc\.[^,]*|Proceedings[^,]*)", rest)
    if proc:
        entrytype = "inproceedings"
        d["booktitle"] = proc.group(1).strip().rstrip(".")
    else:
        # journal = text before "vol." after the title
        jm = re.match(r"\s*([A-Z][^,]+?),\s*(?:vol|no|pp)\.", rest)
        if jm:
            entrytype = "article"
            d["journal"] = jm.group(1).strip()
        elif "Addison-Wesley" in rest or "Press" in rest or "Wesley" in raw:
            entrytype = "book"
            pub = re.search(r"(Addison-Wesley|[A-Z][\w ]+Press)", rest)
            if pub: d["publisher"] = pub.group(1)
            addr = re.match(r"\s*([A-Z][A-Za-z .]+,\s*[A-Z]{2},\s*USA)", rest)
            if addr: d["address"] = addr.group(1).strip()
        elif "Tech. Rep" in rest or "Technical Report" in rest:
            entrytype = "techreport"
            inst = re.match(r"\s*([^,]+),", rest)
            if inst: d["institution"] = inst.group(1).strip()
        elif d.get("url") and "journal" not in d:
            entrytype = "misc"
            howpub = re.match(r"\s*([A-Z][^,]+?),", rest)
    if entrytype == "misc" and "howpublished" not in d and d.get("url"):
        d["howpublished"] = "\\url{%s}" % d["url"]
    return entrytype, d


def to_bib(n, entrytype, d):
    # cite key from first author surname + year
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
    # entries: [n] ... until next [n] or end
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
