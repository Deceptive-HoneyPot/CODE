# Paper 3 — Extended Journal Version (paper3-journal/)

The full-length, **15-page IEEE journal-format** version of `../paper3/`'s
blockchain-anchored tamper-evident audit trail paper. Same live-measured
data, same threat model, same authors — expanded from the 7-page conference
treatment into a longer paper with deeper related work, a formal
canonicalization/verification algorithm, a five-strategy tamper taxonomy, a
projected public/permissioned deployment cost model, a legal/evidentiary
discussion, and a reproducibility statement.

## The files you care about

| File | What it is |
|------|-----------|
| **`paper.pdf`** | The compiled IEEE Transactions-style journal paper (15 pages, two-column). Open / print / submit. |
| `paper.docx` / `paper_ieee.docx` | Word versions of the same paper. |
| `paper.tex` | IEEEtran (`journal` class) LaTeX source — edit on Overleaf, recompile. |
| `paper.md` | Markdown source of truth for the text. |
| `figures/` | Charts, diagrams, and tables (PNG) referenced by the paper. |
| `RELATED_WORK_NOTES.md` | Verified sources + exact figures for every citation. |

## How this differs from `../paper3/`

- **Document class**: `\documentclass[journal]{IEEEtran}` (IEEE Transactions
  style, with running head / markboth) instead of `[conference]`. Both are
  two-column; the journal class uses roman-numeral section numbering and a
  journal-style title block with footnote author affiliation.
- **Length**: ~15 pages vs. 7, via genuinely expanded content — not padding.
  New material includes: an illustrative rollback-attack scenario in the
  introduction; a Merkle-tree / authenticated-data-structure related-work
  subsection; a per-decoy breakdown of what each of the five honeypots
  contributes as an evidence source; a formal Anchor/Verify algorithm
  statement; a five-case tampering taxonomy; a comparison-against-related-work
  results subsection; a projected cost model for public (Ethereum mainnet)
  and permissioned (Hyperledger/Quorum-style) deployment; a legal/evidentiary
  considerations discussion; expanded limitations and future work; and a
  reproducibility statement.
- **Data**: both papers read every number from the same
  `../blockchain_results.json`. Re-running the benchmark updates both.

## The real results (from the live benchmark)

Regenerated fresh for this build by running the benchmark against the live
stack (Ganache + FastAPI backend + Redis) — see `../blockchain_results.json`.

| Metric | Value |
|--------|-------|
| Events anchored | 300 / 300 (100%) |
| Mean anchoring latency | ~10.86 ms |
| Baseline SHA-256 hashing | ~0.0070 ms |
| Gas per anchor | ~21,510 (matches the 21,000-gas base-tx floor) |
| Sequential / concurrent throughput | ~92.08 / ~141.21 events/s |
| Verification latency | ~0.0080 ms/record |
| **Tamper detection** | **500 / 500 (100%), 0 false positives** |
| Digest recoverable on-chain | yes |

## Regenerate everything (if you re-run the benchmark)

Bring the stack up first (Docker must be running):

```
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
cd ..                                   # CODE/
docker compose up -d ganache redis backend
/usr/bin/python3 benchmark_blockchain.py     # -> ../blockchain_results.json  (REAL numbers)
```

Then rebuild this paper's artifacts:

```
cd paper3-journal
/usr/bin/python3 generate_figures.py    # result charts  (needs /usr/bin/python3 — has matplotlib)
/usr/bin/python3 build_tables.py        # tables.html from real JSON
/usr/bin/python3 render.py              # diagrams + tables -> PNG (Chrome headless + magick trim)
/usr/bin/python3 build_latex.py         # -> paper.tex  (journal-format build script, NOT paper3's)
tectonic paper.tex                      # -> paper.pdf   (or upload paper.tex + figures/ to Overleaf)
/usr/bin/python3 build_docx.py          # -> paper.docx, paper_ieee.docx
```

Nothing is hand-typed: the figures, tables, and every in-text number are read
from `../blockchain_results.json`, so re-running the benchmark and these
scripts refreshes the entire paper consistently. Note `build_latex.py` here
is a **separate script** from `../paper3/build_latex.py` — it emits the
`journal`-class document and the expanded content, and uses `table*`/`figure*`
(double-column-spanning floats) correctly for two-column journal mode, which
matters because IEEEtran's `journal` option is still two-column, not
single-column.

## Before you submit (checklist)

1. **References** — a few entries in `paper.md` are marked *(Confirm ...)*;
   verify their exact authors/venue/year/pages against IEEE Xplore / the DOI
   and remove the note.
2. **Threat-model framing is honest** — the paper explicitly states the
   ledger is a development chain (Ganache) that mines instantly, and gives a
   projected (not measured) cost model for public/permissioned deployment in
   Section 7.2. Keep that framing.
3. **Page length** — 15 pages. If a venue caps lower, the Reproducibility
   Statement, Acknowledgment, and Section 7.5 (legal/evidentiary discussion)
   are the easiest sections to trim or move to supplementary material.
