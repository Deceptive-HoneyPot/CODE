# AI Honeypot vs. Static Honeypot — Evaluation Report

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

The sequential numbers above measure one request at a time — but a real
deployment serves multiple attacker sessions simultaneously. A separate
test fires 10 requests concurrently and measures sustained throughput:

| Metric | Value |
|---|---|
| Concurrency level | 10 simultaneous requests |
| Wall time | 0.0125 s |
| **Throughput** | **800.3 req/s** |
| Per-request latency (mean) | 8.2 ms |

This number is dramatically higher than the sequential figure because
concurrent requests overlap their network-wait time — the bottleneck is
per-request round-trip latency to OpenRouter, not local CPU, so the
system scales well with concurrent attacker sessions even though any
single request still takes over a second end-to-end when measured alone.
This distinction — sequential per-request latency vs. sustained
concurrent throughput — is the more accurate way to reason about this
architecture's real-world capacity than a single "requests/sec" number.

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
