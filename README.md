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
| `apt_attack_dataset.json` | 100-payload synthetic adversary dataset (20 per service) used for evaluation |
| `evaluate.py` | Evaluation harness: latency/throughput, response diversity, LLM-judge realism scoring |
| `generate_dataset.py` | Regenerates `apt_attack_dataset.json` |

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

## Evaluation

`evaluate.py` measures the system against a static-honeypot baseline using
four independent, reproducible metrics instead of a single unexplained
score:

1. **Sequential latency / throughput** — static fast-path vs. LLM-backed
   path, one request at a time, N trials each, mean/median/stdev reported.
2. **Concurrent throughput** — `CONCURRENCY_LEVEL` simultaneous requests
   fired at once (default 10), measuring sustained req/s under concurrent
   attacker sessions rather than one-at-a-time latency.
3. **Response diversity** — fraction of distinct outputs across the 100-item
   APT dataset, as a proxy for resistance to signature-based fingerprinting.
4. **LLM-judge realism score** — a second, independent LLM call rates each
   response 1-5 on how convincingly it imitates a real system. This is an
   automated proxy metric, not a human-subject study — see `evaluate.py`
   and the paper's Limitations section for the exact prompt and caveats.

See `BENCHMARK_REPORT.md` for a documented latency/throughput optimization
pass (connection pooling, tuned generation length, widened static
dictionary) with real before/after numbers — a ~3x latency improvement at
a small, honestly-reported realism-score cost.

```bash
set -a; source .env; set +a
.venv-ai/bin/python evaluate.py
```

Results are written to `evaluation_results.json`.

## Security note

This project intentionally builds attacker-facing deception infrastructure
(fake credential capture, fake secrets, permissive fake shells). It is
designed for isolated research/lab use only — do not expose these services
to the public internet without understanding the legal and operational
implications for your environment.

## License

See `LICENSE`.
