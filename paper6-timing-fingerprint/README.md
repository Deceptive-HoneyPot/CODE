# paper6 — Attacker-side fingerprinting of the LLM honeypot (RMK SMART 2026)

Target venue: RMK SMART 2026 (IEEE Madras Section technical co-sponsor,
Xplore-bound). Format: standard IEEE conference template, two-column,
**max 6 pages**, no headers/footers. Submission deadline 3 Oct 2026 (CMT).

Concept: measure how a remote attacker can tell the platform's decoys from
the real services they imitate (OpenSSH, Ethereum JSON-RPC via Ganache,
Jenkins) by protocol conformance and by response timing per engine tier,
then quantify how much real attack traffic reaches the slow LLM tier and
how little a cache can hide.

## Reproduce

    # honeypot stack
    cd ..; docker compose up -d redis postgres ganache backend ai-engine proxy \
        shadow-shell oracle-ai vault-sql ledger-trap forge-ci
    # reference services
    docker run -d --name real-openssh -p 2200:2222 -e PASSWORD_ACCESS=true \
        -e USER_NAME=dbadmin -e USER_PASSWORD=dbadmin123 lscr.io/linuxserver/openssh-server:latest
    docker run -d --name real-jenkins -p 8090:8080 \
        -e JAVA_OPTS="-Djenkins.install.runSetupWizard=false" jenkins/jenkins:lts-jdk17
    docker exec code-redis-1 redis-cli flushall          # cold cache
    cd paper6-timing-fingerprint
    /usr/bin/python3 -u benchmark_fingerprint.py         # ~30 min, real OpenRouter calls
    /usr/bin/python3 generate_figures.py
    /usr/bin/python3 render.py                           # diagram (Chrome + magick)
    /usr/bin/python3 build_latex.py                      # paper_src.tex + JSON -> paper.pdf
    /usr/bin/python3 build_docx.py

Note: a Homebrew Redis on the host shadows 127.0.0.1:6379; the harness reads
the engine's cache through `docker exec code-redis-1 redis-cli`.
`paper_src.tex` is the manuscript source; every `@@TOKEN@@` is filled from
`fingerprint_results.json`.
