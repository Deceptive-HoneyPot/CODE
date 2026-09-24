# Paper 4 — When AI Verdicts Need Audit Trails (paper4-ai-verdict/)

**Authors: Radhika G, Uma Jothi, Radhika N.**

A **new, distinct** research paper — not a rewrite of paper3/paper3-journal.
Where paper3 anchors raw honeypot *evidence* against an attacker who has
compromised the decoy, this paper anchors an **LLM's classification verdict**
about that evidence, and asks a sharper, more uncomfortable question: how
accurate is that verdict in the first place, and what happens when it's
wrong?

## The concept

We built a second, independent intent classifier into the live honeypot
stack — an LLM (Llama-3.1-8B-Instruct via OpenRouter) that labels every
captured attacker event, running *alongside* the deployment's existing
deterministic keyword-rule classifier, not replacing it. Every LLM verdict
(intent, severity score, rationale) is canonically hashed and anchored
on-chain, exactly so that whatever the model concluded — right or wrong —
cannot be silently edited after the fact by an attacker, or by an operator
tempted to quietly fix an embarrassing mistake.

**The honest, measured result:** on 121 hand-labeled attacker payloads
spanning all 9 intent categories, the LLM classifier is *less* accurate
(50.4%) than the simple rule-based classifier it was meant to complement
(85.1%), and its errors cluster hard in the categories that matter most —
prompt injection, crypto theft, and (most strikingly) benign/harmless
traffic, where it correctly recognized 0 of 13 harmless payloads.

## New code (not reused from paper3)

| File | What it is |
|------|-----------|
| `../backend/ai_classifier.py` | New module: calls the LLM, builds/hashes the verdict record. |
| `../backend/main.py` | New endpoints: `POST /api/verdict` (classify + anchor), `GET /api/verdicts`, `POST /api/verdict/verify`. |
| `../benchmark_ai_verdicts.py` | New live benchmark: 121 labeled payloads, real LLM calls, real anchoring, tamper trials, on-chain retrievability. |
| `../ai_verdict_results.json` | Real output of that benchmark — the single source of truth for every number in this paper. |

## The files you care about

| File | What it is |
|------|-----------|
| **`paper.pdf`** | The compiled IEEE Access-styled journal paper (16 pages, two-column, DOI/publication-date banner header + CC-BY footer). |
| `paper.docx` / `paper_ieee.docx` | Word versions. |
| `paper.tex` | IEEEtran (`journal` class, styled to match the IEEE Access visual identity) LaTeX source. |
| `paper.md` | Markdown source of truth for the text. |
| `figures/` | All-new charts and diagrams — none shared with paper3/paper3-journal. |
| `diagrams.html` | Source for the dual-classification pipeline and verdict-record diagrams (new, not paper3's pipeline/threat diagrams). |

## The real results (from the live benchmark)

| Metric | Value |
|--------|-------|
| Labeled payloads | 121 (9 intent categories, 12–15 each) |
| Rule-based classifier accuracy | 85.1% |
| LLM classifier accuracy | **50.4%** |
| LLM &harr; rule-based agreement | 56.2% |
| Worst LLM category | Prompt injection: 8% (vs. 100% rule-based) |
| Benign/unknown traffic recognized by LLM | **0 / 13** |
| Mean LLM inference latency | 1,669 ms |
| Mean on-chain anchor latency | 24.8 ms |
| Verdicts anchored | 121 / 121 (100%) |
| Verdict tamper detection | 40 / 40 (100%), 0 false positives |
| Verdict digest recoverable on-chain | yes |

## Regenerate everything (if you re-run the benchmark)

Bring the stack up first (Docker must be running), and the backend needs
`OPENROUTER_API_KEY` (already wired into `docker-compose.yml`):

```
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
cd ..                                   # CODE/
docker compose build backend            # picks up ai_classifier.py + new endpoints
docker compose up -d ganache redis backend
/usr/bin/python3 benchmark_ai_verdicts.py    # -> ai_verdict_results.json  (REAL numbers, real LLM calls)
```

Then rebuild the paper artifacts:

```
cd paper4-ai-verdict
/usr/bin/python3 generate_figures.py    # accuracy/confusion/latency/tamper/per-category charts
/usr/bin/python3 build_tables.py        # tables.html from real JSON
/usr/bin/python3 render.py              # diagrams + tables -> PNG (Chrome headless + magick trim)
/usr/bin/python3 build_latex.py         # -> paper.tex
tectonic paper.tex                      # -> paper.pdf
/usr/bin/python3 build_docx.py          # -> paper.docx, paper_ieee.docx
```

Nothing is hand-typed: every figure, table, and in-text number is read from
`ai_verdict_results.json`, so re-running the benchmark (which makes real
LLM calls — expect some run-to-run variance) and these scripts refreshes
the entire paper consistently.

## Before you submit (checklist)

1. **References** — several entries in `paper.md` are marked
   *(Confirm ...)*; verify exact venue/year/pages against ACL Anthology /
   IEEE Xplore / arXiv before submission.
2. **Sample size** — 121 payloads (12–15 per category) supports the
   aggregate and per-category comparisons in the paper but is not large
   enough for finer sub-category claims; Section 8 (Limitations) states
   this explicitly.
3. **Single model, single prompt** — deliberately unoptimized (Section 3.4),
   to keep the baseline honest. Don't read the accuracy numbers as a ceiling
   for what an LLM classifier could achieve with tuning.
4. **Page length** — 16 pages, IEEE Access two-column style (DOI header,
   publication-date banner, CC-BY license footer). Well within typical
   journal limits.
5. **DOI placeholder** — the header shows a placeholder DOI
   (`10.1109/ACCESS.2026.PROJECT.JOURNAL`) since this is a preprint; replace
   with the real assigned DOI upon acceptance, in `build_latex.py`'s
   `HEADER` block.
