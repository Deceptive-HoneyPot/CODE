# Paper deliverables (paper2/)

This folder contains the research paper in multiple formats, all generated
from the same source (`paper.md`) with real numbers from
`../evaluation_results.json` (the 2,500-payload evaluation run).

## The files you care about

| File | What it is | Use it for |
|------|-----------|-----------|
| **`paper.pdf`** | Compiled IEEE conference PDF | **This is the real IEEE paper.** Open/print/submit. |
| `paper.tex` | IEEEtran LaTeX source | Edit on Overleaf, then recompile to PDF |
| `paper.docx` | Word doc (simple styling) | Editing in Word |
| `paper_ieee.docx` | Word doc (IEEE-styled two-column) | Editing in Word, closer to IEEE look |
| `paper.md` | Markdown source of truth | Where the text lives |
| `figures/` | All diagrams, charts, tables (PNG) | Referenced by the paper |

## How to edit and re-compile the IEEE PDF (Overleaf — free, no install)

The `paper.pdf` here was compiled locally. To edit it and get IEEE format:

1. Go to <https://www.overleaf.com> and create a free account.
2. **New Project → Upload Project**, and upload:
   - `paper.tex`
   - the entire `figures/` folder (keep the folder name `figures`)
3. In Overleaf, set the compiler to **pdfLaTeX** (Menu → Compiler), then click
   **Recompile**. You'll get the IEEE two-column PDF.
4. Overleaf already includes the `IEEEtran` class — nothing else to install.

## Before you submit (checklist)

1. **Author block** — in `paper.tex`, replace `Author Name`, `Department
   Name`, `University Name`, `City, Country`, `author@email.com` with the real
   details. (Same placeholders exist at the top of `paper.md`.)
2. **References** — the reference list uses real, well-known works, but you
   must confirm each citation's exact authors/title/venue/year against the
   original source. A couple of entries are marked "confirm exact authors" —
   resolve those. Remove the verification note.
3. **Citation markers** — the body refers to works as `[4]`, `[5]`, `[6a]`,
   etc. Make sure every marker matches the final numbered reference list after
   you finalise it.
4. **Page length** — the compiled PDF is ~14 pages because it embeds 15
   figures/tables at full size and includes a full literature survey. IEEE
   conference limits are usually 6–8 pages. To fit, in order of easiest cut:
   (a) reduce oversized full-width figures (the dashboard/attacker screenshots
   and the three tables are the biggest space users — shrink or move two to an
   appendix); (b) merge the three "Gap" subsections in Section VII into one
   tighter subsection; (c) condense the per-service prose now that Table IV
   carries the numbers. The *content* is complete and defensible; the trimming
   is purely a layout exercise for a specific venue's limit.

5. **Verify the newly-added references [12]–[16], [18], [21].** These came from
   the literature review and are real, but confirm exact authors/venue/year —
   a few (HoneyLLM [13], Weber [14]) are marked "confirm" in the reference list
   because their published bibliographic details should be checked against the
   source before submission.

## Regenerating everything (if the evaluation is re-run)

From the `CODE/` directory, after a fresh `evaluate.py` run:

```
python3 paper2/generate_figures.py     # result charts from evaluation_results.json
python3 paper2/build_latex.py          # -> paper.tex
python3 paper2/build_docx.py           # -> paper.docx
python3 paper2/build_ieee_docx.py      # -> paper_ieee.docx
cd paper2 && tectonic paper.tex        # -> paper.pdf  (or use Overleaf)
```

Every number in the outputs is read from `evaluation_results.json` and the
dataset file — nothing is hand-typed, so re-running the evaluation and these
scripts refreshes the whole paper consistently.
