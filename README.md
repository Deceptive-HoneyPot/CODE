# AI-Driven Cyber Deception & Attack Detection Framework

A research-oriented honeypot platform that combines **LLM-generated deception**,
**multi-protocol decoy services**, and **blockchain-anchored, tamper-evident
logging** to detect and study attacker behavior in real time.

Public-facing decoy services impersonate a corporate SSH server, an internal
AI API, a PostgreSQL database, an Ethereum JSON-RPC node, and a Jenkins
CI/CD server. Every interaction is logged, classified by attack intent,
SHA-256 hashed, anchored on a local Ethereum chain, and streamed live to a
React dashboard over WebSocket.

> Originally built with a locally-hosted Ollama/LLaMA3 model; this version
> uses a hosted LLM via the [OpenRouter](https://openrouter.ai) API so the
> stack runs without a GPU or local model server.

## Architecture

```
INTERNET / ATTACKER
        |
        v
  +-------------+     logs every connection
  |    PROXY    |----------------------------+
  | (port guard)|                            |
  +-------------+                            v
        |                            +---------------+
  routes to 5 decoys:                |    BACKEND    |
        |                            |   (FastAPI)   |
  +-----+----------------------+     | classify/hash |
  | shadow-shell  (SSH)        |     +------+--------+
  | oracle-ai     (AI API)     |            |
  | vault-sql     (PostgreSQL) |     +------+-------+------------+
  | ledger-trap   (Ethereum)   |     |              |            |
  | forge-ci      (Jenkins)    |  REDIS         GANACHE      DASHBOARD
  +-----+----------------------+  (store)   (blockchain)   (React/WS)
        |
        v
  AI ENGINE (OpenRouter-backed) -- generates dynamic, context-aware
  responses for any command/query/payload the static fast-path doesn't
  already know how to answer.
```

Only the **proxy** and **dashboard** are exposed publicly; every decoy
and the backend communicate over an internal Docker network.

## Components

| Path | Role |
|---|---|
| `proxy/` | asyncio TCP proxy; logs every connection, forwards to the matching decoy |
| `decoys/shadow-shell/` | Fake SSH server (`asyncssh`), accepts any credentials, AI-backed shell |
| `decoys/oracle-ai/` | Fake internal AI API; detects and "falls for" prompt-injection attempts |
| `decoys/vault-sql/` | Fake PostgreSQL query endpoint + a real seeded Postgres instance with honeypot data |
| `decoys/ledger-trap/` | Fake Ethereum JSON-RPC node |
| `decoys/forge-ci/` | Fake Jenkins CI/CD server |
| `ai-engine/` | 3-tier response engine: static dict -> Redis cache -> OpenRouter LLM call |
| `backend/` | Central API: intent classification, SHA-256 hashing, blockchain anchoring, Redis storage, WebSocket broadcast |
| `dashboard/` | React live-attack dashboard |
| `apt_attack_dataset.json` | 1,328-payload real-world adversary dataset used for evaluation |
| `evaluate.py` | Evaluation harness: latency/throughput, response diversity, LLM-judge realism scoring |
| `generate_dataset.py` | Rebuilds `apt_attack_dataset.json` from real public payload corpora (see below) |

## Running locally without Docker

Requires Python 3.11+, Redis, and (optionally) Node for `npx ganache`.

```bash
brew install redis
redis-server &

npx ganache --chain.chainId 1337 --wallet.totalAccounts 5 \
  --wallet.defaultBalance 1000 --server.port 7545 &

python3 -m venv .venv-backend && source .venv-backend/bin/activate
pip install -r backend/requirements.txt
deactivate

python3 -m venv .venv-ai && source .venv-ai/bin/activate
pip install -r ai-engine/requirements.txt
deactivate

cp .env.example .env   # add your OPENROUTER_API_KEY

set -a; source .env; set +a
REDIS_HOST=localhost GANACHE_URL=http://localhost:7545 \
  .venv-backend/bin/uvicorn main:app --app-dir backend --port 3001 &
REDIS_HOST=localhost \
  .venv-ai/bin/uvicorn engine:app --app-dir ai-engine --port 8000 &
```

Then run individual decoys the same way (each has its own `requirements.txt`
via its Dockerfile), or use `docker-compose up` for the full stack.

## Running with Docker

```bash
cp .env.example .env   # add your OPENROUTER_API_KEY
docker compose up --build
```

Dashboard: http://localhost:3000 · Backend API: http://localhost:3001

## Deploying to capture live internet traffic

Everything above runs the stack locally, with no real attacker traffic —
the "live attack feed" stays empty until something actually connects to
one of the exposed decoy ports. Capturing genuine live attacks (the
organic complement to the real-world *payload* dataset above) requires
exposing the proxy's ports to the public internet from a real host with a
public IP. **This is a real security-relevant action with consequences —
do it deliberately, not as a default:**

- **Use a disposable cloud VM, not a home network or work machine.**
  Internet-facing honeypot ports draw scanning and exploitation traffic
  within minutes of going live; isolate it from anything else you run.
- **Only the `proxy` and `dashboard` containers should ever be
  internet-facing** (see docker-compose.yml) — never expose the
  `backend`, `redis`, `postgres`, or `ganache` ports directly.
- **Put the dashboard behind auth or a private network (e.g. a VPN/SSH
  tunnel or a firewalled admin IP allowlist)** before exposing the decoy
  ports — the dashboard itself has no login, and while it only *displays*
  attacker telemetry, that telemetry can include attacker IPs and raw
  payloads you may not want publicly browsable.
- **Set real budget/rate limits on your OpenRouter API key.** Every
  unrecognized command an attacker sends triggers a real, billed LLM
  call; a scripted scanner hitting an exposed decoy can generate sustained
  API cost with no cap unless you set one on the OpenRouter dashboard.
- **Check your cloud provider's and hosting country's policy on running
  honeypots/deception infrastructure** before exposing anything —
  some providers restrict or prohibit it in their acceptable-use policy.
- Typical flow: provision a VM, install Docker, clone this repo, `cp
  .env.example .env` with your own `OPENROUTER_API_KEY`, open only the
  proxy's five ports (2222, 8080, 5433, 8545, 9090) plus the dashboard
  port behind your chosen access control, then `docker compose up -d`.

This step was intentionally **not** performed as part of building this
project's dataset/dashboard work — it's a deployment decision for
whoever operates the resulting instance, not something to do
automatically from a development environment.

## Evaluation

`evaluate.py` measures the system against a static-honeypot baseline using
four independent, reproducible metrics instead of a single unexplained
score:

1. **Sequential latency / throughput** — static fast-path vs. LLM-backed
   path, one request at a time, N trials each, mean/median/stdev reported.
2. **Concurrent throughput** — `CONCURRENCY_LEVEL` simultaneous requests
   fired at once (default 10), measuring sustained req/s under concurrent
   attacker sessions rather than one-at-a-time latency.
3. **Response diversity** — fraction of distinct outputs across the
   1,328-item APT dataset, as a proxy for resistance to signature-based
   fingerprinting.
4. **LLM-judge realism score** — a second, independent LLM call rates each
   response 1-5 on how convincingly it imitates a real system. This is an
   automated proxy metric, not a human-subject study — see `evaluate.py`
   and the paper's Limitations section for the exact prompt and caveats.

### Dataset provenance

`apt_attack_dataset.json` is built by `generate_dataset.py` by downloading
real, publicly documented attack payloads (not hand-written or model-generated):

| Service | Count | Real source |
|---|---|---|
| `ssh` | 500 | [`danielmiessler/SecLists`](https://github.com/danielmiessler/SecLists) `Fuzzing/command-injection-commix.txt` (8,956 unique real strings from the commix exploitation tool) + [`payload-box/command-injection-payload-list`](https://github.com/payload-box/command-injection-payload-list) |
| `sql` | 500 | SecLists `Fuzzing/Databases/SQLi/` — Generic-SQLi, quick-SQLi, SQLi-Polyglots, and `sqlmap`-derived risk-classified boolean/error/time-based payloads (474 unique real strings from the sqlmap exploitation tool) + [`payload-box/sql-injection-payload-list`](https://github.com/payload-box/sql-injection-payload-list) |
| `api` | 300 | [`swisskyrepo/PayloadsAllTheThings`](https://github.com/swisskyrepo/PayloadsAllTheThings) (Prompt Injection, SSRF, XXE, Log4Shell sections) + SecLists `Fuzzing/XXE-Fuzzing.txt` |
| `web3` | 18 | Real Ethereum JSON-RPC method names (`eth_sendRawTransaction`, `personal_unlockAccount`, `admin_addPeer`, etc.) — for an exposed RPC node the method call itself *is* the documented attack, per the public Ethereum JSON-RPC spec. Capped at 18 deliberately: no larger real corpus of "web3 attack payloads" exists |
| `cicd` | 10 | Real Jenkins remote-API endpoints and exploitation techniques from Jenkins Security Advisories (script-console RCE, job path traversal, pipeline `sh`-step abuse). Capped at 10 for the same reason as `web3` |

**1,328 total real payloads.** `web3` and `cicd` are intentionally not
scaled to match `ssh`/`sql`/`api`: their real attack surface is a small,
finite set of documented API methods/endpoints, not an open space of
injection strings, so padding them to a uniform count would mean
fabricating payloads rather than using more real data.

Each dataset entry keeps a `"source": "real-world-payload-corpus"` field for
provenance. Fetched payloads are cached in `real_data_cache/` so
`generate_dataset.py` still works offline after the first run.

Regenerate it with:

```bash
pip install requests
python3 generate_dataset.py
```

See `BENCHMARK_REPORT.md` for a documented latency/throughput optimization
pass (connection pooling, tuned generation length, widened static
dictionary) with real before/after numbers — a ~3x latency improvement at
a small, honestly-reported realism-score cost.

```bash
set -a; source .env; set +a
.venv-ai/bin/python evaluate.py
```

Results are written to `evaluation_results.json`.

## Testing & Quality Assurance

A comprehensive automated test suite covers the FastAPI backend, AI classifier, decoy service protocols, and cryptographic blockchain commitments.

Run all tests:
```bash
python tests/run_all_tests.py
```

## Security Operations & Forensic Tools

The repository includes dedicated command-line utilities in `tools/` for security operations centers (SOC) and threat intelligence analysts:

1. **Forensic Evidence & STIX 2.1 Exporter (`tools/forensic_exporter.py`):**
   Extracts intercepted attack events and generates OASIS STIX 2.1 bundles, MISP threat packages, CSV telemetry, and cryptographic chain-of-custody audit reports.
   ```bash
   python tools/forensic_exporter.py --format all --output-dir forensics_export
   ```

2. **Operator Administration CLI (`tools/honeypot_cli.py`):**
   Command-line control interface for checking service connectivity, streaming live logs, auditing blockchain digests, and injecting simulated attack campaigns.
   ```bash
   python tools/honeypot_cli.py status
   python tools/honeypot_cli.py logs --limit 20
   python tools/honeypot_cli.py verify-chain
   ```

3. **Decoy Service Health Monitor (`tools/decoy_health_monitor.py`):**
   Automated synthetic TCP health probe measuring socket availability and latency across all 5 decoy service ports.
   ```bash
   python tools/decoy_health_monitor.py
   ```

4. **Multi-Stage Adversary Simulator (`tools/adversary_simulator.py`):**
   Simulates realistic APT attack campaigns (APT29, FIN7, Web3 node draining, LLM prompt-injection jailbreaks) to evaluate deception fidelity.
   ```bash
   python tools/adversary_simulator.py --campaign APT29
   ```

5. **Performance & Latency Profiler (`tools/performance_profiler.py`):**
   Profiles response time percentiles (p50, p95, p99) across the 3-tier pipeline (static fast-path vs Redis cache vs LLM inference).
   ```bash
   python tools/performance_profiler.py --iterations 50
   ```

## Documentation & Architecture

- [Architecture Deep Dive](docs/ARCHITECTURE_DEEP_DIVE.md) — Comprehensive technical breakdown of the 3-tier response pipeline, SHA-256 blockchain anchoring, and multi-protocol decoy surface.
- [API Reference](docs/API_REFERENCE.md) — Complete endpoint schema specifications for REST and WebSocket interfaces.

## Security note

This project intentionally builds attacker-facing deception infrastructure
(fake credential capture, fake secrets, permissive fake shells). It is
designed for isolated research/lab use only — do not expose these services
to the public internet without understanding the legal and operational
implications for your environment.

## License

See `LICENSE`.
