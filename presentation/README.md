# Project presentation (presentation/)

A 48-slide deck covering the whole project: problem, architecture, every
component, the evidence pipeline, the threat model, all measured results, the
limitations, and the two research papers.

| File | What it is |
|------|-----------|
| **`PROJECT_PRESENTATION.pptx`** | The deck. Open in PowerPoint, Keynote or Google Slides. 16:9, fully editable — all text is real text, all tables are native tables. |
| `PROJECT_PRESENTATION.pdf` | Same deck exported to PDF, for presenting without PowerPoint. |
| `build_ppt.py` | Generates the `.pptx`. |

## Structure

| Slides | Section |
|--------|---------|
| 1–2 | Title, agenda |
| 3–5 | The problem: why static honeypots stop working; objectives |
| 6–9 | Architecture: end-to-end diagram, request lifecycle, deployment topology |
| 10–16 | The five decoys: port routing, then one slide each |
| 17–19 | Tiered response engine and prompting |
| 20–22 | Evidence pipeline: five steps on `POST /api/log`, intent classification |
| 23–26 | Blockchain: anchoring pipeline, threat model, verification procedure |
| 27–29 | Dashboard and a worked end-to-end attack example |
| 30–40 | Evaluation: methodology, dataset, latency, throughput, diversity, realism, blockchain benchmark, optimisation pass, prior work |
| 41–46 | Limitations, research output, tech stack, reproduction steps, future work |
| 47–48 | Conclusion, Q&A |

## Every number is read from the real result files

`build_ppt.py` reads `../evaluation_results.json`, `../blockchain_results.json`
and `../apt_attack_dataset.json` at build time — the same sources the papers
use. Nothing is hand-typed, so re-running the benchmarks and rebuilding the
deck refreshes it consistently with `paper2/` and `paper3/`.

Diagrams and charts are reused from `../paper2/figures/` and
`../paper3/figures/`, so the deck and the papers show the same visuals.

## Rebuilding

Needs `python-pptx` and `Pillow` (Pillow is used only to read image dimensions
for aspect-ratio-correct placement):

```
python3 -m venv .venv-ppt
.venv-ppt/bin/pip install python-pptx Pillow
.venv-ppt/bin/python build_ppt.py        # -> PROJECT_PRESENTATION.pptx
```

To refresh the PDF export as well (macOS, via Keynote):

```
osascript -e 'tell application "Keynote"
  set d to open POSIX file "'$PWD'/PROJECT_PRESENTATION.pptx"
  export d to POSIX file "'$PWD'/PROJECT_PRESENTATION.pdf" as PDF
  close d saving no
  quit saving no
end tell'
```

## Notes for editing

- Fonts are Arial throughout (and Courier New for the command strings on the
  reproduction slide), so the deck renders the same on macOS, Windows and
  Google Slides without substitution.
- Bullet blocks are laid out by estimated wrapped-line height in
  `bullets()`. If you lengthen a bullet a long way past its current text,
  re-render and check it still clears the block below.
- Section-divider slides and the title/closing slides are the only dark ones;
  everything else is light so the white-background diagrams sit flush.
