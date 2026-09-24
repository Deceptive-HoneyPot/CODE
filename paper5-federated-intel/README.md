# paper5 — Hub-less Cross-Honeypot Threat Intelligence (revision 2)

Revised after the first-round rejection ("needs substantial revision in
technical writing; lacks scientific merit"). The submitted version is kept
in `submitted_v1/`.

Build (all numbers come from one benchmark run; nothing is hand-typed):

    # dedicated chain with enough accounts for 16 writers + adversaries
    docker run -d --name ganache-bench -p 7545:7545 trufflesuite/ganache:latest \
        --chain.chainId 1337 --wallet.totalAccounts 24 --wallet.defaultBalance 1000 \
        --server.port 7545 --wallet.deterministic
    /usr/bin/python3 benchmark_federation.py     # ~3 min -> federation_results.json
    /usr/bin/python3 generate_figures.py         # figures/fig_*.png
    /usr/bin/python3 render.py                   # figures/diag_hubcompare.png (Chrome + magick)
    /usr/bin/python3 build_latex.py              # paper_src.tex + JSON -> paper.tex -> paper.pdf (tectonic)
    /usr/bin/python3 build_docx.py               # paper.tex -> paper.docx, paper_ieee.docx

`paper_src.tex` is the manuscript source; every `@@TOKEN@@` is filled from
`federation_results.json` by `build_latex.py`. Edit prose there, not in paper.tex.
