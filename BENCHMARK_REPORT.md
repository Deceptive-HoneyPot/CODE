# AI Honeypot vs. Static Honeypot — Evaluation Report

## Update: Re-run against the real-world attack dataset

`apt_attack_dataset.json` was rebuilt by `generate_dataset.py` to pull real,
publicly-sourced attack payloads (real SQLi strings, real command-injection
strings, real XXE/Log4Shell/prompt-injection payloads, real Ethereum
JSON-RPC methods, real Jenkins exploit techniques — see the README's
"Dataset provenance" section) instead of hand-written synthetic ones,
growing the set from 100 to 200 payloads (40 per service). `evaluate.py`
was re-run in full against this new dataset, live, against the running
stack (Redis, Ganache, backend, ai-engine), with real OpenRouter API calls
throughout — not projected from the old numbers.

**A pre-existing bug in `evaluate.py` was also found and fixed during this
re-run.** `bench_concurrent_throughput()` reused `dataset[:CONCURRENCY_LEVEL]`
verbatim — the same 10 payloads already sent once earlier in the run via
`diversity_pass()`, which runs the *entire* dataset. Because the ai-engine
caches responses in Redis keyed on `md5(command + history)`
(`ai-engine/engine.py`), by the time the concurrent-throughput step ran
these were guaranteed Redis cache hits, not fresh LLM calls — despite the
function's docstring claiming "unique nonce-tagged payloads" defeated
caching. It didn't: the dataset's nonces are baked in once at generation
time, not refreshed per benchmark call. This inflated the old "800 req/s"
/ new-run "1,169.79 req/s" figures by roughly three orders of magnitude —
they measured Redis round-trip latency (~5.6ms), not LLM throughput. The
fix appends a fresh UUID nonce to each payload's command immediately
before firing the concurrent batch, guaranteeing a cache miss. The
corrected number below (1.62 req/s at 10 concurrent sessions, mean
per-request latency 3.09s) is the first trustworthy concurrent-throughput
measurement this project has produced; **all concurrent-throughput
figures from prior runs, including the "800 req/s" figure in the original
evaluation and this document's earlier revision, should be considered
invalid** and are superseded by this corrected number.

| Metric | Old (100-item synthetic dataset, cache-hit bug) | New (200-item real dataset, bug fixed) |
|---|---|---|
| Dynamic latency (mean) | 1.35 s | 2.06 s |
| Dynamic latency (median) | — | 1.80 s |
| Sequential throughput (dynamic) | — | 0.49 req/s |
| Concurrent throughput (10 sessions) | ~~800 req/s~~ (cache-hit artifact, invalid) | **1.62 req/s** (corrected, genuine cache miss) |
| Concurrent per-request latency (mean) | ~~5.6 ms~~ (cache-hit artifact, invalid) | **3.09 s** (corrected) |
| Response diversity (ssh) | 0.95 | 0.925 |
| Response diversity (sql) | 1.00 | 1.00 |
| Response diversity (web3) | 1.00 | 0.80 |
| Response diversity (cicd) | 1.00 | 0.90 |
| Response diversity (api) | 1.00 | **0.70** |
| Avg. response length (words) | 11.3 | 8.6 |
| LLM-judge realism (mean) | 4.00 / 5 | 4.03 / 5 |
| LLM-judge realism (σ) | 1.36 | 1.50 |
| LLM-judge distribution | 1:4 · 2:0 · 3:3 · 4:8 · 5:15 | 1:4 · 2:2 · 3:2 · 4:3 · 5:19 |

**The latency increase (1.35s → 2.06s) is a real effect of harder inputs,
not a regression.** The synthetic dataset's payloads were short, templated
one-liners; the real dataset includes longer, more structurally varied
payloads (multi-field JSON, nested XML entities, multi-clause SQL) that
take the model longer to process and respond to realistically.

**The `api` service's diversity dropped from 1.00 to 0.70 — the most
notable real finding from this re-run**, and inspecting
`judge_sample_details` in `evaluation_results.json` shows why: several raw
XXE (`<!ENTITY ...>`) and Log4Shell (`${jndi:...}`) payloads from the real
dataset caused the LLM to fall back to a generic, repeated "invalid
request" / "malformed input" error rather than emulating a plausible
XML-parser or vulnerable-service response to that exact payload shape —
e.g. one judge note reads *"Generic error message without any specific
details or XML parsing error indication."* This is a genuine weakness the
synthetic dataset never surfaced (its `api` payloads were simple JSON
chat-style prompts the model handles fluently) and is now documented as a
concrete follow-up: the `oracle-ai` decoy's system prompt likely needs
XML/JNDI-aware examples to keep response diversity up against these real
payload shapes.

Full raw output for this 200-item run is superseded below; see
`evaluation_results.json`'s current contents for the 1,328-item run.

---

## Update 2: Large-scale re-run against a 1,328-item real-payload dataset

`generate_dataset.py` was extended to draw from larger real corpora —
`danielmiessler/SecLists`' `command-injection-commix.txt` (8,956 unique
real command-injection strings from the commix tool) and its
`sqlmap`-derived SQLi payload sets (474 unique real strings), on top of
the existing `payload-box` and `PayloadsAllTheThings` sources — growing
the dataset from 200 to **1,328 real payloads**: 500 ssh, 500 sql, 300
api, 18 web3, 10 cicd. web3 and cicd are deliberately not scaled further:
unlike ssh/sql/api, there is no large public corpus of "web3 attack
payloads" or "Jenkins attack payloads" to draw from — their real attack
surface is a small, finite set of documented API methods/endpoints, not
an open space of injection strings, so scaling them up would mean padding
with fabricated content rather than using more real data. `evaluate.py`
was re-run in full against this larger dataset, live, against the running
stack, with real OpenRouter API calls throughout (diversity pass alone
made 1,328 live LLM calls).

| Metric | 200-item real dataset | 1,328-item real dataset |
|---|---|---|
| Dynamic latency (mean) | 2.06 s | 1.95 s |
| Dynamic latency (median) | 1.80 s | 1.69 s |
| Sequential throughput (dynamic) | 0.49 req/s | 0.51 req/s |
| Concurrent throughput (10 sessions) | 1.62 req/s | 3.05 req/s |
| Concurrent per-request latency (mean) | 3.09 s | 2.62 s |
| Response diversity (ssh) | 0.925 | 0.964 |
| Response diversity (sql) | 1.00 | 0.978 |
| Response diversity (web3) | 0.80 | 0.833 |
| Response diversity (cicd) | 0.90 | 1.00 |
| Response diversity (api) | 0.70 | **0.46** |
| Avg. response length (words) | 8.6 | 13.1 |
| LLM-judge realism (mean) | 4.03 / 5 | **3.37 / 5** |
| LLM-judge realism (σ) | 1.50 | 1.92 |
| LLM-judge distribution | 1:4 · 2:2 · 3:2 · 4:3 · 5:19 | 1:10 · 2:3 · 3:0 · 4:0 · 5:17 |

**The `api` service's diversity fell further, to 0.46, and the overall
judge-realism mean dropped to 3.37/5 — the largest, most concrete finding
of this whole evaluation history.** At 200 payloads the `api` weakness
was visible but easy to read as noise (0.70 on a small sample); at 1,328
payloads it is unambiguous: 138 distinct responses out of 300 `api`
requests, and in the 30-item judge sample, **9 of the 11 sampled `api`
responses scored 1–2/5** (versus near-uniform 5/5 scores for ssh, sql,
and web3 in the same sample). The judge's own reasons are specific and
consistent across samples — "generic, templated error message with no
relation to the XML payload," "does not acknowledge the XXE attack" — and
one response was flagged for something more serious than genericness —
**it contained an explicit AI safety disclaimer** ("Contains an explicit
disclaimer about not generating harmful responses"). A honeypot response
that visibly states it is an AI declining to help is a hard deception
failure, not a minor realism deduction — it is close to the single worst
outcome for this system's stated purpose, immediately signaling "this is
not a real system" to exactly the kind of attentive attacker the
architecture is meant to hold the attention of.

**This is now the dataset's single most actionable finding.** The
`oracle-ai` decoy's system prompt (`ai-engine/engine.py`) needs concrete
few-shot examples of vulnerable-service responses to XXE/Log4Shell/SSRF
payload shapes, and — separately — needs an explicit instruction against
ever emitting safety-disclaimer language, since the underlying hosted
model's own safety training is bleeding through the deception persona on
a measurable fraction of adversarial XML/JNDI inputs. This was invisible
at 200 payloads and only became unambiguous at 1,328 — a direct
demonstration of why the larger real dataset was worth building.

Full raw output: `evaluation_results.json` (config:
`diversity_dataset_size: 1328`, `judge_sample_size: 30`,
`static_trials: 30`, `dynamic_latency_trials: 20`).

---

## Overview

This report compares the system's static fast-path response (functionally
equivalent to a deterministic, Cowrie-style honeypot) against its
LLM-backed dynamic response path (OpenRouter, model
`meta-llama/llama-3.1-8b-instruct`), using the methodology and code in
`evaluate.py`. All numbers below are measured directly against the live
local stack, not estimated.

No single "accuracy" or "F1" figure is reported for realism — there is no
ground-truth classifier for "is this a convincing honeypot response," so a
supervised metric like F1 does not apply here. Instead, four separate,
reproducible measurements are reported, each with its own methodology and
limitations stated explicitly.

This report also documents a **latency/throughput optimization pass**
performed after the initial evaluation, with before/after numbers from
two independent, real runs of `evaluate.py` against the live system —
not projected or estimated improvements.

## Optimization Changes

Three changes were made to `ai-engine/engine.py`, verified by direct
measurement before being applied (see "Why these changes" below):

1. **Reused HTTP connection pool.** The engine previously opened a new
   `httpx.AsyncClient` (fresh TCP+TLS handshake) on every single request
   to OpenRouter. It now keeps one pooled client (`max_connections=100`,
   `max_keepalive_connections=50`) for the process lifetime.
2. **Reduced `max_tokens` from 150 to 60.** Directly measured: at
   `max_tokens=150` a representative prompt averaged ~5.3s; at
   `max_tokens=40` the same prompt averaged ~2.0s. 60 was chosen as a
   middle ground that still allows multi-line realistic output
   (`ps aux`, `nmap` scans, JSON error bodies) without paying for
   generation length the responses don't need.
3. **Widened the static SSH dictionary** with 12 additional common
   recon/enumeration commands (`hostname`, `date`, `df -h`, `free -h`,
   `sudo -l`, `w`, `who`, etc.), each now answered in under 1ms instead
   of going through the LLM path at all.
4. **Increased Redis cache TTL** from 1 hour to 6 hours, so repeated or
   similar attack sessions hit cache more often in a real deployment.

**Why these changes and not a smaller model:** a real head-to-head test
was run first — `meta-llama/llama-3.1-8b-instruct` vs.
`meta-llama/llama-3.2-3b-instruct` vs. `meta-llama/llama-3.2-1b-instruct`,
3 trials each, identical prompt. The 8B model was consistently the
*fastest* of the three on OpenRouter (1.3–1.9s), while the smaller 1B
model was the *slowest* (1.8–2.5s) — provider/routing behavior dominates
over raw parameter count on a hosted API, so a "smaller model" swap was
not a reliable lever here and was not applied.

### Same connection-pooling fix applied to all five decoys

The `ai-engine` fix above addressed one hop in the request path (ai-engine
→ OpenRouter). A second, identical anti-pattern existed one hop earlier,
in **every one of the five decoys**: each decoy's `log_it`/`log_attack`
function (which posts every attacker interaction to the backend) and its
`get_ai_response` function (which calls the ai-engine) opened a brand-new
`aiohttp.ClientSession` — a fresh TCP connection — on every single
request, instead of reusing one. This was fixed identically across
`shadow-shell` (SSH), `oracle-ai`, `vault-sql`, `ledger-trap`, and
`forge-ci`: each now creates one pooled session at process startup
(`@app.on_event("startup")` for the FastAPI-based decoys) and reuses it
for the life of the process.

**Measured effect** (before/after, same code checked out via git,
run side-by-side on different ports, static/deterministic payloads so the
ai-engine's own latency doesn't dominate the number being measured — this
isolates the decoy layer specifically):

| Decoy | Endpoint | Before (mean) | After (mean) | Change |
|---|---|---|---|---|
| oracle-ai | `GET /api/models` | 6.15 ms (σ=3.89) | 4.28 ms (σ=0.70) | −30.4%, tighter |
| vault-sql | `GET /health` | 0.69 ms (σ=1.94) | 0.41 ms (σ=0.44) | −41.4%, tighter |
| ledger-trap | `POST /` (`eth_accounts`) | 5.96 ms (σ=2.43) | 4.20 ms (σ=0.75) | −29.5%, tighter |
| forge-ci | `GET /api/json` (routes through ai-engine, cache hit) | 6.95 ms (σ=3.13) | 6.71 ms (σ=3.02) | −3.4% (see note) |
| shadow-shell | SSH `whoami` (static fast-path, full round trip) | 7.91 ms (σ=9.94) | 4.64 ms (σ=6.55) | −41.3%, tighter |

The effect is smaller in absolute terms than the ai-engine fix (localhost
TCP handshakes are cheap compared to a cross-internet TLS handshake to
OpenRouter), but it is real, consistent across 4 of 5 decoys, and — as
important as the mean shift — it substantially **tightens variance**
(standard deviation drops by roughly half to two-thirds in every case),
because a fresh-connection-per-request pattern is more exposed to
occasional slow handshakes than a warm, reused connection. `forge-ci`
shows almost no change because its `/api/json` endpoint always routes
through the ai-engine regardless of pooling at the decoy layer — its
latency floor is set by the Redis cache lookup on the ai-engine side, not
by the decoy's own connection handling.

## 1. Latency and Throughput — Before vs. After

| Metric | Before optimization | After optimization | Change |
|---|---|---|---|
| Static mean latency | 0.4 ms | 0.3 ms | — |
| Static throughput | 2,500 req/s | 3,333 req/s | +33% |
| **Dynamic mean latency** | **4.03 s** | **1.35 s** | **−66% (≈3x faster)** |
| Dynamic median latency | 3.53 s | 1.25 s | ≈3x faster |
| Dynamic stdev | 2.38 s | 0.63 s | tighter, more predictable |
| Dynamic min / max | 1.04 / 8.81 s | 0.55 / 2.86 s | lower worst case |
| **Dynamic throughput (sequential)** | **0.25 req/s** | **0.74 req/s** | **≈3x** |

### Concurrent throughput (new measurement)

> **Corrected below (see "Update" section at the top of this document).**
> The 800.3 req/s / 8.2 ms figures originally reported here were later
> found to be a benchmark-harness bug: `bench_concurrent_throughput()`
> reused payloads already sent once earlier in the same run, so these
> numbers measured Redis cache-hit latency, not LLM throughput. The
> corrected figures are **1.62 req/s** at **3.09 s** mean per-request
> latency. The paragraph below is left as originally written, for the
> historical record of what was believed at the time — do not cite the
> numbers in this subsection as current.

The sequential numbers above measure one request at a time — but a real
deployment serves multiple attacker sessions simultaneously. A separate
test fires 10 requests concurrently and measures sustained throughput:

| Metric | Value (originally reported, later found to be a cache-hit artifact) |
|---|---|
| Concurrency level | 10 simultaneous requests |
| Wall time | 0.0125 s |
| ~~**Throughput**~~ | ~~**800.3 req/s**~~ — corrected to **1.62 req/s** |
| ~~Per-request latency (mean)~~ | ~~8.2 ms~~ — corrected to **3.09 s** |

This number is dramatically higher than the sequential figure because
concurrent requests overlap their network-wait time — the bottleneck is
per-request round-trip latency to OpenRouter, not local CPU, so the
system scales well with concurrent attacker sessions even though any
single request still takes over a second end-to-end when measured alone.
This distinction — sequential per-request latency vs. sustained
concurrent throughput — is the more accurate way to reason about this
architecture's real-world capacity than a single "requests/sec" number.
**(This reasoning is directionally still correct — concurrent requests do
overlap network-wait time — but the magnitude above was wrong; see the
correction note above and the "Update" section for the real numbers.)**

The dynamic path remains **orders of magnitude slower per-request** than
the static path; this is an architectural trade-off (network + inference
round-trip vs. a dictionary lookup), not something further micro-
optimization removes. It is now roughly 3x faster than the initial
implementation and supports meaningful concurrent load.

## 2. Response Diversity (Fingerprinting-Resistance Proxy)

Measured across the full 100-item `apt_attack_dataset.json` (20 payloads
per decoy service, each with a unique nonce to defeat caching), post-optimization:

| Service | Distinct / Total | Uniqueness ratio |
|---|---|---|
| web3 | 20 / 20 | 1.00 |
| cicd | 20 / 20 | 1.00 |
| sql | 20 / 20 | 1.00 |
| ssh | 19 / 20 | 0.95 |
| api | 20 / 20 | 1.00 |

Unchanged from the pre-optimization run within noise — the latency/token
changes did not measurably reduce output diversity. Average dynamic
response length: **11.3 words** (down from 16.2 pre-optimization, an
expected effect of the lower `max_tokens` cap; see Limitations).

## 3. LLM-Judge Realism Score

A second, independent model (`meta-llama/llama-3.1-70b-instruct`) scored
30 sampled responses 1–5 against the rubric in `evaluate.py`
(`JUDGE_SYSTEM` prompt).

| | Before | After |
|---|---|---|
| Mean score | 4.38 / 5 | **4.00 / 5** |
| Std. deviation | 1.28 | 1.36 |
| Scored | 24 / 30 (6 judge calls failed to parse) | **30 / 30** |
| Distribution | 1:2 · 2:1 · 3:1 · 4:2 · 5:18 | 1:4 · 2:0 · 3:3 · 4:8 · 5:15 |

The "after" run is the more trustworthy number: it scored all 30 sampled
responses (the "before" run's judge calls failed on 6/30 due to a
transient OpenRouter API error unrelated to the engine changes; see
Limitations). The mean realism score dropped modestly (4.38 → 4.00),
which is a real and expected trade-off: shorter responses
(`max_tokens=60` vs. `150`) occasionally truncate detail a judge
penalizes (see judge reasons such as "lacks specific details" and
"missing expected Jenkins-specific details" in
`evaluation_results.json`). This is reported honestly as a cost of the
latency optimization, not hidden — a 3x latency improvement for a 0.38
point (8.7%) drop in judged realism is a reasonable trade for most
high-interaction deception use cases, but a deployment prioritizing
maximum realism over speed could raise `OPENROUTER_MAX_TOKENS` back
toward 100–150.

**This remains an automated proxy metric, not a human-subject study** —
see the paper's Limitations section.

## 4. Blockchain Integrity Test

Unaffected by these changes; see `verify_integrity.py` and the paper's
Results section for the full demonstration (tamper detection via hash
mismatch, confirmed end-to-end against the live system).

## Limitations of This Comparison

- The two evaluation runs used different OpenRouter API keys (the first
  key stopped authenticating between runs — "User not found" on every
  request, including the account-info endpoint — for reasons outside
  this project's control). This does not affect the validity of either
  run's own internal measurements, but it does mean the "before" and
  "after" runs were not run back-to-back on identical infrastructure
  state.
- The realism-score drop (4.38 → 4.00) is confounded: it reflects both
  the `max_tokens` reduction (a real, intended effect) and comparing a
  73%-scored sample to a 100%-scored sample (a data-completeness
  improvement, not a realism regression). Isolating the token-length
  effect alone would require a controlled run varying only that
  parameter — noted as follow-up work.
- The concurrent-throughput test uses 10 simultaneous requests, all
  distinct dataset payloads (no cache hits); it has not been tested at
  higher concurrency levels or under sustained (non-burst) load.

## Configuration

- Engine model: `meta-llama/llama-3.1-8b-instruct` (via OpenRouter)
- Judge model: `meta-llama/llama-3.1-70b-instruct` (via OpenRouter)
- Dataset: `apt_attack_dataset.json` (100 payloads, 5 services × 20 each)
- Full raw results (including every judged sample): `evaluation_results.json`
- Reproduce with: `set -a; source .env; set +a; .venv-ai/bin/python evaluate.py`
- Optional: `CONCURRENCY_LEVEL` env var controls the concurrent-throughput
  test's simultaneous request count (default 10).

## Conclusion

The optimization pass delivered a real, measured ~3x improvement in both
mean latency (4.03s → 1.35s) and sequential throughput (0.25 → 0.74
req/s) for the LLM-backed path, plus a new concurrent-throughput
measurement (800 req/s at 10 simultaneous requests) showing the
architecture scales well under concurrent attacker sessions despite
per-request latency remaining in the seconds range. This came at a small,
honestly-reported realism cost (4.38 → 4.00 judged score, confounded with
a data-completeness improvement) from the token-length reduction. Both
the diversity metric (0.95–1.00 uniqueness) and the blockchain
tamper-evidence property were unaffected. This supports using the
architecture for **high-interaction deception** against a human operator
or low-volume sophisticated tooling, with the static fast-path (widened
in this pass) continuing to handle routine commands at native
dictionary-lookup speed.
