# Team 58 — Redesigned Project Presentation

`PPT.tex` → `PPT.pdf` (33 slides, 16:9).

## Build

```bash
tectonic PPT.tex        # what was used here
# or
pdflatex PPT.tex && pdflatex PPT.tex
```

No external image files — every diagram and chart is TikZ/pgfplots inside the `.tex`.

## What changed vs. the old 24-slide deck

| | Old | New |
|---|---|---|
| Scope | Module 1 only (deception engine) | All four measured modules |
| Slides | 24 | 33 |
| Architecture | plain node sketch | layered TikZ with trust zones, ports, tier latencies, request/telemetry paths |
| New diagrams | — | request lifecycle (10 steps), 3-tier engine, anchoring pipeline |
| New content | — | roadmap, implementation stack, Module 2/3/4 results, project-status chart, conclusion |
| Teaching aids | — | `TAKEAWAY` box on every result slide |
| Margins | cramped, several overfull slides | 0.85 cm symmetric margins, auto-wrapping title band, zero overfull warnings |

All logic, claims and figures from the original deck are preserved. The new numbers
come from the project's own measurement files:

- `blockchain_results.json` → Module 2
- `ai_verdict_results.json` → Module 3
- `paper5-federated-intel/federation_results.json` → Module 4

## Slide map

| # | Slide | # | Slide |
|---|---|---|---|
| 1 | Title | 18 | Runs 3–4 real payloads |
| 2 | Roadmap | 19 | Diversity by service |
| 3 | Problem statement | 20 | Benchmark-harness bug |
| 4 | Objectives | 21 | Realism distribution |
| 5 | Research gaps | 22 | API decoy realism failure |
| 6 | Comparison table | 23 | **Module 2** — audit trail |
| 7 | **System architecture** | 24 | **Module 3** — LLM vs rules |
| 8 | **Life of one request** | 25 | Module 3 — why it matters |
| 9 | Five decoys | 26 | **Module 4** — federated intel |
| 10 | Three-tier engine | 27 | **Project status — 70%** |
| 11 | Blockchain logging | 28 | Discussion |
| 12 | Implementation stack | 29 | Limitations & future work |
| 13 | Evaluation methodology | 30 | Conclusion |
| 14 | Run 1 baseline | 31–32 | References |
| 15 | Run 2 optimisation | 33 | Thank you |
| 16 | Latency before/after | | |
| 17 | Decoy pooling | | |

## Presenting it (≈15 min)

Slide 8 is the anchor of the talk. If a teacher only follows one slide, make it that
one: steps 1–5 are "does the attacker believe us", steps 6–10 are "can we prove what
they did". Every later result slide belongs to one of those two halves — say which
one before you read the numbers.

Three questions to expect, with the slide that answers them:

- *"Isn't 1.35 s too slow for a honeypot?"* → slide 28. Yes for scanning honeypots;
  we say so. This targets a human operator, where server-load latency is plausible.
- *"Why is the LLM worse than keyword rules?"* → slide 25. The errors cluster in the
  expensive categories, and that gap is the argument for anchoring verdicts.
- *"Why is a bug on a slide?"* → slide 20. A cached benchmark measured Redis, not the
  LLM. Reporting it is the methodological contribution.

## Adjusting margins

One place, in the preamble:

```latex
\setbeamersize{text margin left=0.85cm, text margin right=0.85cm}
```

Change both values and the matching `0.85cm` in the `frametitle` and `footline`
templates so the title band and footer stay aligned with the body text.
