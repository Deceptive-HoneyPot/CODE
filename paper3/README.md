# Paper 3 — Blockchain-Anchored Tamper-Evident Audit Trail (paper3/)

A second, **distinct** research paper focused on the **blockchain / security**
side of the project: making honeypot evidence tamper-evident against an attacker
who has compromised the decoy itself. It shares no prose with paper2 (measured
6-gram overlap ≈ 1%, all of it the author list + shared citations).

**Every number in this paper is measured**, not simulated. They come from
`../blockchain_results.json`, produced by running `../benchmark_blockchain.py`
against the live stack (Ganache + FastAPI backend + Redis).

## The files you care about

| File | What it is |
|------|-----------|
| **`paper.pdf`** | The compiled IEEE conference paper (7 pages). Open / print / submit. |
| `paper.tex` | IEEEtran LaTeX source (edit on Overleaf, recompile). |
| `paper.md` | Markdown source of truth for the text. |
| `figures/` | All charts, diagrams, and tables (PNG) referenced by the paper. |
| `RELATED_WORK_NOTES.md` | Verified sources + exact figures for every citation. |

## The real results (from the live benchmark)

| Metric | Value |
|--------|-------|
| Events anchored | 300 / 300 (100%) |
| Mean anchoring latency | 10.79 ms |
| Baseline SHA-256 hashing | 0.0063 ms |
| Anchoring overhead (chain write) | 10.79 ms |
| Gas per anchor | 21,511 (21,488–21,512) — matches the 21,000-gas base-tx floor |
| Sequential / concurrent throughput | 92.65 / 148.96 events/s |
| Verification latency | 0.0046 ms/record |
| **Tamper detection** | **500 / 500 (100%), 0 false positives** |
| Digest recoverable on-chain | yes (read straight from tx input data) |

## Regenerate everything (if you re-run the benchmark)

Bring the stack up first (Docker must be running):

```
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
cd ..                                   # CODE/
docker compose up -d ganache redis backend
/usr/bin/python3 benchmark_blockchain.py     # -> blockchain_results.json  (REAL numbers)
```

Then rebuild the paper artifacts:

```
cd paper3
/usr/bin/python3 generate_figures.py    # result charts  (needs /usr/bin/python3 — has matplotlib)
/usr/bin/python3 build_tables.py        # tables.html from real JSON
/usr/bin/python3 render.py              # diagrams + tables -> PNG (Chrome headless + magick trim)
/usr/bin/python3 build_latex.py         # -> paper.tex
tectonic paper.tex                      # -> paper.pdf   (or upload paper.tex + figures/ to Overleaf)
```

Nothing is hand-typed: the figures, tables, and every in-text number are read
from `blockchain_results.json`, so re-running the benchmark and these scripts
refreshes the entire paper consistently.

## Before you submit (checklist)

1. **References** — the list uses real, well-known works. A few entries are
   marked *(Confirm ...)* in `paper.md`; verify their exact
   authors/venue/year/pages against IEEE Xplore / the DOI and remove the note.
2. **Threat-model framing is honest** — the paper explicitly states that the
   ledger is a **development chain (Ganache) that mines instantly**, so the
   10.79 ms latency contains no public-network confirmation wait. Keep that
   framing; it is what makes the numbers defensible. The contribution is the
   pipeline + threat model + 100% tamper detection, which transfer unchanged to
   a batched public/permissioned deployment.
3. **Page length** — 7 pages, within typical IEEE conference limits. If a venue
   caps at 6, the easiest cut is to merge Sections 7.2 and 7.3.
