# AI Honeypot vs. Static Honeypot — Evaluation Report

## Overview

This report compares the system's static fast-path response (functionally
equivalent to a deterministic, Cowrie-style honeypot) against its
LLM-backed dynamic response path (OpenRouter, model
`meta-llama/llama-3.1-8b-instruct`), using the methodology and code in
`evaluate.py`. All numbers below are measured directly against the live
local stack, not estimated.

Unlike the earlier version of this report, no single "accuracy" or "F1"
figure is reported for realism — there is no ground-truth classifier for
"is this a convincing honeypot response," so a supervised metric like F1
does not apply here. Instead, three separate, reproducible measurements
are reported, each with its own methodology and limitations stated
explicitly.

## 1. Latency and Throughput

| Metric | Static fast-path (n=30) | Dynamic LLM path (n=20) |
|---|---|---|
| Mean latency | 0.4 ms | 4.03 s |
| Median latency | 0.4 ms | 3.53 s |
| Std. deviation | 0.1 ms | 2.38 s |
| Min / Max | 0.3 / 0.7 ms | 1.04 / 8.81 s |
| Throughput | 2,500 req/s | 0.25 req/s |

The dynamic path is roughly **10,000x slower** and has substantially
higher variance (min 1.04s, max 8.81s) than the deterministic fast-path,
reflecting real network + inference latency to a hosted LLM rather than a
local model call. This is a real cost, not a rounding error, and any
claim about this architecture must state it plainly: it is unsuitable for
high-volume, low-interaction scanning traffic, and appropriate only where
sustained engagement with a smaller number of sessions is the goal.

## 2. Response Diversity (Fingerprinting-Resistance Proxy)

Measured across the full 100-item `apt_attack_dataset.json` (20 payloads
per decoy service, each with a unique nonce to defeat caching):

| Service | Distinct / Total | Uniqueness ratio |
|---|---|---|
| web3 | 20 / 20 | 1.00 |
| cicd | 20 / 20 | 1.00 |
| sql | 20 / 20 | 1.00 |
| ssh | 19 / 20 | 0.95 |
| api | 20 / 20 | 1.00 |

A static, dictionary-based honeypot returns the same fixed template for
any unrecognized input; its uniqueness ratio over a set of *novel*
payloads is at or near 0 by construction. The measured ratios above
(0.95–1.00) indicate the LLM-backed path produces a distinct response for
almost every unique payload, which is the property that defeats
single-packet / signature-based fingerprinting approaches such as those
described by Vetterl and Clayton (2018). This is a proxy metric for
fingerprinting resistance, not a direct test against a real fingerprinting
tool — see the paper's Limitations section.

Average dynamic response length: **16.2 words** (vs. 0 — a fixed string —
for the static path).

## 3. LLM-Judge Realism Score

A second, independent model (`meta-llama/llama-3.1-70b-instruct`, distinct
from the response-generating model to reduce self-evaluation bias) scored
30 sampled responses 1–5 against the rubric in `evaluate.py`
(`JUDGE_SYSTEM` prompt): "how convincingly does this response imitate a
real, non-honeypot instance of this service for this exact payload."

| | |
|---|---|
| Mean score | **4.38 / 5** |
| Std. deviation | 1.28 |
| Scored | 24 / 30 requested |
| Score distribution | 1: 2 · 2: 1 · 3: 1 · 4: 2 · 5: 18 |

Six of the 30 judge calls (20%) returned a response the harness could not
parse as the requested JSON object and are excluded rather than silently
counted as failures or successes — this is a real limitation of using an
LLM as a structured-output judge and is reported here rather than hidden.
The scored distribution is bimodal-leaning-high: most responses (18/24)
were rated maximally convincing, with a smaller cluster of low scores
concentrated in cases where the engine produced an overly generic or
too-informative error message (see `evaluation_results.json` →
`judge_sample_details` for every individual score and the judge's stated
reason).

**This is an automated proxy metric, not a human-subject study.** LLM
judges have known biases (e.g., verbosity preference) and may not track
what a human attacker would find convincing. Prior work using human
evaluators (Sladić et al., 2024, shelLM) reported a 0.90 true-negative
rate under direct human interaction; that remains the stronger form of
evidence and is recommended as follow-up work rather than assumed
equivalent to the score reported here.

## Configuration

- Engine model: `meta-llama/llama-3.1-8b-instruct` (via OpenRouter)
- Judge model: `meta-llama/llama-3.1-70b-instruct` (via OpenRouter)
- Dataset: `apt_attack_dataset.json` (100 payloads, 5 services × 20 each)
- Full raw results (including every judged sample): `evaluation_results.json`
- Reproduce with: `set -a; source .env; set +a; .venv-ai/bin/python evaluate.py`

## Conclusion

The dynamic, LLM-backed response path trades roughly four orders of
magnitude in latency for a measurable, reproducible increase in response
diversity (0.95–1.00 uniqueness vs. ~0 for a static baseline) and a judged
realism score of 4.38/5 on the payloads it was successfully scored on.
This supports using the architecture for **high-interaction deception**
against a human operator or low-volume sophisticated tooling, not as a
replacement for high-throughput, low-interaction scanning honeypots, where
a static fast-path (retained in this system for ~80% of routine commands)
remains the appropriate choice.
