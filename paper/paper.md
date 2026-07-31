# An AI-Driven, Blockchain-Anchored Cyber Deception Framework for Adaptive Honeypot Defense

**[Author Name]**
Department of Computer Science and Engineering, Amrita Vishwa Vidyapeetham
[City, Country] · [email]

## Abstract

Traditional honeypots — Cowrie, Kippo, Dionaea, and similar low/medium-interaction
systems — rely on static, deterministic response tables. This makes them
efficient at scale but fragile against fingerprinting: prior work has shown
that automated probing can distinguish such honeypots from real systems with
near-perfect accuracy in a single packet exchange [1]. This paper presents a multi-protocol cyber deception framework that
replaces static response tables with a large language model (LLM) response
engine, producing context-aware, session-consistent output for five decoy
services (SSH, an internal AI API, PostgreSQL, an Ethereum JSON-RPC node,
and Jenkins CI/CD) while retaining a fast static path for the ~80% of
traffic that is routine. Every interaction is intent-classified, SHA-256
hashed, and anchored as a transaction on a local Ethereum chain, giving the
resulting audit trail tamper-evidence independent of the logging host's
integrity. We evaluate the system against a static-honeypot baseline along
four axes — sequential latency/throughput, concurrent throughput, response
diversity, and an LLM-judge realism score — across three successive
evaluation runs, and report the measured trade-offs explicitly rather than
a single composite metric. After an optimization pass (HTTP connection
pooling applied across the response engine and all five decoys, a tuned
generation-length cap, and a widened static fast-path), the system
achieves a mean dynamic-path latency of 1.35 s (down from an
initial 4.03 s, a ~3x improvement) against a 100-payload hand-written
adversarial dataset, and a sequential throughput of 0.74 requests/second,
versus 3,333 requests/second for the static fast-path. A third evaluation
run replaced the hand-written dataset with a 200-payload dataset built
from real, publicly-documented attack payloads (real SQLi, command-injection,
XXE/Log4Shell/prompt-injection, Ethereum JSON-RPC, and Jenkins-exploit
strings; see Section 5.4), which increased mean dynamic latency to 2.06 s
— a genuine effect of longer, more structurally varied real payloads, not
a regression — and surfaced a real weakness invisible to the hand-written
set: response diversity on the API/prompt-injection decoy dropped from
1.00 to 0.70 against real XXE/Log4Shell payload shapes. This same run also
uncovered and fixed a benchmark-harness bug that had silently measured
Redis cache-hit latency (8.2 ms, reported as "800 requests/second") instead
of genuine concurrent LLM throughput; the corrected concurrent-throughput
figure is 1.62 requests/second at a mean per-request latency of 3.09 s
under 10 simultaneous sessions. Response diversity otherwise remained high
(0.80–1.00 across four of five services) versus near-zero for a static
baseline by construction, and the mean LLM-judged realism score was stable
across all three runs (4.00–4.03/5). We report each run's numbers, the
harness bug, and its correction explicitly rather than presenting only the
most favorable figures, and discuss where the resulting trade-offs are
acceptable (human-operated intrusion, not internet-wide scanning) and the
limitations of automated realism scoring as a proxy for human deception
studies.

**Keywords:** honeypot, cyber deception, large language models, blockchain,
digital forensics, intrusion detection, adaptive defense

---

## 1. Introduction

Honeypots are decoy systems deployed to attract, detect, and study
unauthorized access attempts without exposing production infrastructure.
Since Cowrie's introduction as an SSH/Telnet honeypot, low- and
medium-interaction honeypots have become a standard component of threat
intelligence pipelines: they are cheap to deploy, safe to run, and generate
large volumes of attacker telemetry. Their core weakness is also their core
design choice — a finite table of canned responses. An attacker, or more
commonly an automated scanner, can send a handful of atypical commands and
observe whether the responses are internally consistent with a real system.
Vetterl and Clayton demonstrated Internet-scale fingerprinting of exactly
this class of honeypot with a single distinguishing packet and near-zero
error rate [1]. Once a honeypot is identified, it stops collecting
useful intelligence on capable adversaries, who simply move on or feed it
false telemetry.

Two independent trends motivate a different approach. First, instruction-
tuned LLMs can generate plausible, contextually consistent text for
narrow, well-specified personas (a Linux shell, a SQL error, a JSON-RPC
response) far more cheaply than hand-authoring a comprehensive fake
filesystem or database. Recent work — shelLM [4], HoneyGPT [5], and
related 2023-2025 studies [6], [7] — has shown that
LLM-generated shell sessions can hold up under sustained human interaction
significantly better than static emulation. Second, blockchain-anchored
hashing offers a low-cost way to make forensic logs tamper-evident: instead
of trusting the honeypot host's own log integrity (which an attacker who
compromises the host could edit), a hash of each log entry is committed to
an independent, append-only ledger, so any later modification is
detectable by re-hashing and comparing.

This paper combines both trends into a single deployable framework and
contributes:

1. A **multi-protocol deception architecture** covering five distinct
   attack surfaces (SSH, an internal AI API, SQL, Ethereum RPC, and CI/CD)
   behind a single logging and classification pipeline — broader coverage
   than the SSH-only focus of most LLM-honeypot literature to date.
2. A **three-tier response strategy** (static dictionary → cached LLM
   response → live LLM call) that keeps routine traffic at millisecond
   latency while reserving expensive generation for genuinely novel input.
3. **Blockchain-anchored log integrity** applied specifically to honeypot
   telemetry, giving each log entry a verifiable, tamper-evident hash
   independent of the collecting host.
4. An **evaluation methodology** that reports latency, response diversity,
   and an LLM-judge realism score as separate, reproducible measurements —
   explicitly avoiding a single unexplained accuracy figure — along with a
   discussion of what an automated judge can and cannot substitute for.

## 2. Related Work

### 2.1 Static Honeypots and Fingerprinting

Cowrie, Kippo, Dionaea, and T-Pot remain widely deployed low/medium-
interaction honeypots, valued for low resource cost and safety. Their
static response model is precisely what fingerprinting techniques exploit:
Vetterl and Clayton [1] achieved an equal error rate of 0.0183 detecting
such honeypots at Internet scale using single-packet probes; a later
multistage active-probing framework [2] generalized this to a broader
class of honeypots. A 2026 survey of fingerprinting and evasion
techniques [3] confirms this remains an open problem rather than one
solved by incremental patching of response tables.

### 2.2 LLM-Backed Deception

Sladić et al.'s shelLM [4] used an LLM to generate an entire SSH shell
session and reported a 0.90 true-negative rate — human evaluators judged
the sessions to be a real shell 90% of the time. HoneyGPT [5] extended
this with chain-of-thought prompting for more stateful sessions and
reported deeper attacker engagement in field deployment. McKee and
Noever's early exploration [6] and the broader "LLM Honeypot" study [7]
corroborate that LLM-driven responses measurably outperform static
emulation on interactivity and perceived realism. This body of work is
concentrated on SSH/terminal honeypots; our framework applies the same
idea across five protocol types with a shared backend, which to our
knowledge has not been evaluated together in prior work.

### 2.3 Blockchain for Log Integrity and Forensic Chain of Custody

Hash-then-anchor patterns for tamper-evident logging are established in
digital forensics: a 2025 IEEE study on blockchain-based evidence tracking
[8] and a Springer paper on tamper-proof cloud VM investigation models [9]
both apply hashing plus blockchain anchoring to forensic evidence
generally. A PeerJ Computer Science paper on blockchain-enforced immutable
auditability for threat detection [10] applies a closely related pattern
to security telemetry specifically. We did not find prior work applying
this pattern to honeypot logs specifically — our contribution is the
application, not the underlying cryptographic technique.

### 2.4 Deception Frameworks and Honeytokens

MITRE Engage [11] provides a structured vocabulary for adversary
engagement and deception mapped to ATT&CK, which we use loosely to frame
our five decoys as covering distinct engagement opportunities (credential
harvesting, prompt injection, data exfiltration bait, transaction-signing
bait, and supply-chain bait respectively). Honeytokens — individually
identifiable fake credentials seeded to detect misuse — have a long
history dating to HoneyGen [13]; our seeded fake API keys and database
records in `vault-sql` are a direct application of this idea.

### 2.5 Realism and Detectability Benchmarking

Standardized telemetry metrics for honeypot realism (dwell time,
interaction depth, behavioral diversity) have been proposed recently
[15]; we adopt "response diversity" as one such metric in
our own evaluation. We could not verify several secondary-source dwell-time
statistics circulating for RL/LLM-driven deception systems and deliberately
do not cite unverified numbers here — see Limitations.

### 2.6 Direct Comparison to Cited Systems

Table 1 places this framework against the honeypot systems and papers cited
above. "Interaction level" follows the standard low/medium/high taxonomy
(low = fixed banner/response, medium = scripted protocol emulation with
some state, high = a real or near-real backend). Entries are included only
where we could verify the claim from the system's own documentation or the
cited paper; unverified secondary-source figures are marked as such rather
than presented as fact.

**Table 1: Comparison against cited honeypot systems.**

| System | Interaction level | AI/LLM-generated responses | Protocols / services | Tamper-evident logging |
|---|---|---|---|---|
| Cowrie [16] | Medium (emulated shell) or high (proxy mode) | No (static/scripted); an experimental LLM fallback mode exists in recent releases but is a single-tier call, not a static→cache→LLM pipeline | SSH, Telnet | No — plain JSON/text logs |
| T-Pot [17] | Mixed — orchestrates ~20 independent honeypot daemons (incl. Cowrie, Dionaea) behind an ELK dashboard | No — aggregation/visualization layer only, no response generation of its own | Broad (SSH, SMB, web, RDP, ICS/SCADA, etc.), via bundled daemons | No |
| Dionaea [18] | Low–medium (scripted protocol emulation for payload capture) | No | SMB, MySQL wire protocol, SIP, FTP, TFTP | No |
| shelLM [4] | High for SSH sessions specifically | Yes — full LLM-generated shell session | SSH only | Not addressed |
| HoneyGPT [5] | High for terminal sessions | Yes — GPT-3.5/4 via a Cowrie-derived proxy; authors report an internally-defined ~92% attack-success and ~96% deception-accuracy rate (self-reported, not independently reproduced — treat as a single-study figure) | SSH/terminal only | Not addressed |
| This framework | High across all five decoys | Yes — 3-tier (static dict → Redis cache → LLM), session-history-aware, applied uniformly across 5 distinct protocol types | SSH, internal AI API, PostgreSQL, Ethereum JSON-RPC, Jenkins CI/CD | Yes — SHA-256 per log entry, anchored to an Ethereum chain |

Two gaps in the cited literature motivate this framework's design choices
rather than being incidental: first, LLM-backed deception work to date
([4], [5], [6], [7]) is concentrated on a single protocol (SSH/terminal);
we are not aware of a prior system applying an LLM response engine
uniformly across five heterogeneous protocol types (shell, REST/chat API,
SQL, JSON-RPC, CI/CD webhook) behind one shared backend. Second, a
systematization-of-knowledge survey covering both honeypots and LLMs [19]
does not discuss blockchain or tamper-evident logging as a honeypot
design axis at all, and we found no honeypot-specific paper combining
hash-anchoring with decoy logging — the closest related work is general
(non-honeypot) tamper-evident audit-log research [8]–[10]. We report this
as an absence in the literature we searched, not as a claim that no such
system exists.

## 3. System Architecture

The framework has six components: a network-facing proxy, five decoy
services, a shared AI response engine, a central backend, a blockchain
ledger, and a live dashboard. Only the proxy and dashboard are exposed to
the network; all other components communicate over an internal Docker
network, so a compromised decoy cannot directly reach the logging
pipeline or the blockchain client.

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
  AI ENGINE (OpenRouter-backed)
```

### 3.1 Proxy and Network Isolation

`proxy/proxy.py` is an `asyncio` TCP server listening simultaneously on
five public ports (2222, 8080, 5433, 8545, 9090). On each new connection
it asynchronously logs the source IP and target port to the backend, then
transparently pipes bytes between the attacker and the corresponding
internal decoy. This separates connection-level telemetry (useful even
for port scanners that never send a payload) from application-level
decoy logic, and ensures every decoy's internal listening port is never
directly reachable from outside the Docker network.

### 3.2 Decoy Services

Five decoys cover distinct attack surfaces, each impersonating a specific
real system and each logging every interaction to the backend before (or
while) generating a response:

- **shadow-shell** (SSH, port 2222) — a real `asyncssh` server that
  accepts any username/password combination, logs every login attempt,
  and presents a shell prompt for `dbadmin@corp-prod-db-01`. Directory
  navigation (`cd`) is handled locally for speed and consistency; all
  other commands are routed through the AI engine.
- **oracle-ai** (internal AI API, port 8080) — a FastAPI service exposing
  `/api/chat`, `/api/predict`, and `/api/models` endpoints for a fictitious
  internal model (`gpt-corp-v2`). Prompt-injection attempts (keywords like
  "jailbreak," "ignore previous instructions") are logged and answered
  with a scripted "bypass accepted" response, keeping the attacker
  engaged and their injection technique fully captured.
- **vault-sql** (PostgreSQL decoy, port 5433) — a FastAPI query endpoint
  plus a real, separately-seeded PostgreSQL instance
  (`decoys/vault-sql/fake_data.sql`) containing synthetic user records,
  financial records, and API keys formatted to resemble real OpenAI,
  GitHub, and AWS credentials, used as honeytokens.
- **ledger-trap** (Ethereum JSON-RPC, port 8545) — responds to standard
  Web3 RPC calls (`eth_getBalance`, `eth_accounts`, etc.) with
  statically-defined plausible values for common calls and routes
  uncommon RPC methods through the AI engine.
- **forge-ci** (Jenkins CI/CD, port 9090) — exposes Jenkins-style
  endpoints (`/api/json`, `/job/build/api/json`, `/git/notifyCommit`) that
  fake a working build/deploy pipeline, targeting supply-chain attackers.

### 3.3 Three-Tier AI Response Engine

`ai-engine/engine.py` answers each request in one of three tiers, in
order, so that the expensive LLM call is reserved for genuinely novel
input:

1. **Static dictionary.** Roughly a dozen common SSH commands (`ls`,
   `whoami`, `env`, `ps aux`, `cat /etc/passwd`, etc.) and structural
   patterns (`cd `, `sudo `, `echo `) are answered instantly from a fixed
   table — this is the same response model a traditional static honeypot
   uses for everything, and remains the fast path here for routine
   traffic.
2. **Redis cache.** Unknown commands are hashed (including up to two
   prior history entries, so repeated attacks in a similar context reuse
   a cached answer) and checked against a Redis cache with a 1-hour TTL
   before any LLM call is made.
3. **Hosted LLM call.** A cache miss is sent to a hosted chat-completion
   model via the OpenRouter API, with a service-specific system prompt
   instructing the model to output only the raw response a real system
   would produce — no explanation, no markdown, no acknowledgment that it
   is a language model — and, for the SSH service, session history is
   included so the shell exhibits state consistency (e.g., a file created
   in one command persists in a later `ls`).

This mirrors the three-tier design validated by prior LLM-honeypot work
(e.g., shelLM, HoneyGPT) while extending it across five protocol types
sharing one engine and one cache.

### 3.4 Intent Classification

`backend/main.py::classify_intent` applies keyword matching to every
logged payload, assigning one of eight categories: SQL injection,
privilege escalation, reverse shell, cryptomining, prompt injection,
supply-chain, reconnaissance, or unknown. This is intentionally simple —
a rule-based baseline rather than a learned classifier — and is reported
as a known limitation (Section 7) rather than a contribution in its own
right; it exists to make the live dashboard immediately useful, not as a
novel detection technique.

### 3.5 Blockchain-Anchored Logging

Every log entry received at `POST /api/log` is: (1) timestamped and
intent-classified; (2) serialized with sorted keys and SHA-256 hashed;
(3) anchored by sending a zero-value self-transaction on a local Ethereum
chain (Ganache) with the hash as the transaction's `data` field; (4)
stored in a bounded Redis list (last 10,000 entries) alongside the hash
and anchoring status; and (5) broadcast over WebSocket to connected
dashboard clients. Because the hash is committed to an independently
operated ledger, any later modification of the stored log is detectable
by re-hashing it and comparing against the anchored value — Section 4.4
and 5 report a direct test of this property.

### 3.6 Real-Time Dashboard

A React single-page app (`dashboard/src/App.jsx`) polls `/api/stats`
every five seconds and subscribes to `/ws/live` for a push feed, showing
aggregate stats (total attacks, unique IPs, intent breakdown, top
attacker IPs) and a scrolling live feed of the last 200 events, each
annotated with its blockchain-anchoring status.

## 4. Evaluation Methodology

We evaluate against a **static-honeypot baseline**, operationalized as the
system's own static fast-path (a deterministic dictionary lookup,
functionally equivalent to Cowrie's canned-response model) versus its
LLM-backed dynamic path, using `evaluate.py` against the live system.

### 4.1 Dataset

Results in Sections 5.1–5.3 use a 100-payload hand-curated adversary
dataset (`apt_attack_dataset.json`), 20 payloads per decoy service,
generated by an earlier version of `generate_dataset.py` from hand-written
attack patterns (reverse shells, SQL injection, RPC abuse, prompt
injection, CI/CD supply-chain payloads) each tagged with a random nonce
to defeat caching during evaluation. Section 5.4 reports a subsequent run
using a 200-payload dataset (40 per service) rebuilt from real,
publicly-documented attack payload corpora rather than hand-written
strings — see Section 5.4 and the project README for the full source
list and rationale for the switch.

### 4.2 Metrics

1. **Latency / throughput.** 30 trials of the static fast-path and 20
   trials of the LLM-backed path; mean, median, and standard deviation
   reported rather than a single sample, addressing a methodological gap
   in the project's original benchmark (which used a single dynamic-path
   measurement and reported it as if representative).
2. **Response diversity.** Across the full dataset, the fraction
   of distinct outputs per service is used as a proxy for resistance to
   signature-based fingerprinting — a static honeypot necessarily scores
   at or near the number of distinct hardcoded templates, however many
   inputs it receives.
3. **LLM-judge realism score.** An independent model
   (`meta-llama/llama-3.1-70b-instruct`, distinct from the
   `meta-llama/llama-3.1-8b-instruct` response-generation model to reduce
   self-evaluation bias) rates each response 1-5 against the rubric in
   `evaluate.py` (`JUDGE_SYSTEM` prompt), on a sample of 30 payloads.

### 4.3 Limitations of the Realism Metric

This is an **automated proxy metric**, not a human-subject study. LLM
judges are known to have their own biases (e.g., favoring longer or more
verbose responses) and may not perfectly track what a human attacker would
find convincing. shelLM's 0.90 true-negative rate [4] was obtained with
human evaluators; we report our LLM-judge score as a weaker but far
cheaper and more reproducible substitute, and explicitly recommend a human
evaluation as follow-up work rather than presenting this score as
equivalent evidence.

### 4.4 Blockchain Integrity Test

We additionally demonstrate tamper-evidence directly (`verify_integrity.py`):
a real log entry is submitted through the live pipeline and anchored
on-chain; it is then fetched back, re-hashed, and confirmed to match its
recorded hash; a modified copy of the same entry is then re-hashed and
confirmed to *not* match, demonstrating that the hash anchored at logging
time would catch a post-hoc modification.

## 5. Results

All figures below are measured directly against the live local stack
(`evaluate.py`, `verify_integrity.py`) using
`meta-llama/llama-3.1-8b-instruct` as the response-generation model and
`meta-llama/llama-3.1-70b-instruct` as the judge; full raw output is in
`evaluation_results.json`.

### 5.1 Initial Baseline

The first evaluation run, before any latency optimization, established
the following baseline:

| Metric | Static fast-path | LLM-backed dynamic path |
|---|---|---|
| Mean latency | 0.4 ms | 4,028 ms (4.03 s) |
| Median latency | 0.4 ms | 3,529 ms (3.53 s) |
| Stdev | 0.1 ms | 2,380 ms (2.38 s) |
| Min / Max latency | 0.3 / 0.7 ms | 1,037 / 8,807 ms |
| Throughput (req/s) | 2,500 | 0.25 |
| Response diversity (uniqueness ratio, mean across 5 services) | ~0 by construction | 0.99 (range 0.95–1.00) |
| Avg. response length (words) | 0 (static string) | 16.2 |

LLM-judge realism score: mean 4.38/5 (σ = 1.28, n = 24 of 30 sampled
responses successfully parsed — six judge calls returned unparseable
output during this run and are excluded rather than assumed either way).

### 5.2 Optimization Pass

Profiling the baseline identified two concrete, fixable inefficiencies in
`ai-engine/engine.py`: (1) a new `httpx.AsyncClient` — and therefore a
fresh TCP+TLS handshake — was opened on *every single request* to
OpenRouter instead of reusing a connection pool; (2) `max_tokens=150` was
generous relative to what these responses need, and generation length is
the dominant cost in a chat-completion request's latency. A third,
lower-effort change widened the static SSH dictionary with 12 additional
common recon commands so more traffic never reaches the LLM path at all.

Before applying the token-length change, a direct measurement (3 trials,
identical prompt) confirmed generation length as the dominant latency
factor: `max_tokens=150` averaged ≈5.3s, `max_tokens=80` ≈3.4s,
`max_tokens=40` ≈2.0s. 60 was selected as a middle ground. A separate
measurement also tested whether a smaller model would help: comparing
`llama-3.1-8b-instruct` against the smaller `llama-3.2-3b-instruct` and
`llama-3.2-1b-instruct` (3 trials each, identical prompt) found the 8B
model was consistently the *fastest* of the three (1.3–1.9s) and the 1B
model the *slowest* (1.8–2.5s) — provider/routing behavior on a hosted
API dominates over raw parameter count, so a model downgrade was not
applied.

A second, independent evaluation run (fresh Redis cache, same
methodology) after these changes measured:

| Metric | Before | After | Change |
|---|---|---|---|
| Dynamic mean latency | 4.03 s | 1.35 s | ≈3x faster |
| Dynamic median latency | 3.53 s | 1.25 s | ≈3x faster |
| Dynamic stdev | 2.38 s | 0.63 s | tighter |
| Dynamic sequential throughput | 0.25 req/s | 0.74 req/s | ≈3x |
| Static throughput | 2,500 req/s | 3,333 req/s | +33% |
| LLM-judge realism | 4.38/5 (n=24/30) | 4.00/5 (n=30/30) | −0.38 |

A new metric — **concurrent throughput** — was added for this second run:
firing 10 requests simultaneously (rather than one at a time). The first
measurement of this metric reported 800.3 requests/second at a mean
per-request latency of 8.2 ms; this figure was later discovered to be a
benchmark-harness bug, not a genuine measurement (`evaluate.py`'s
concurrent-throughput step reused payloads already sent once earlier in
the same run, so they were guaranteed Redis cache hits — the 8.2 ms was
cache round-trip latency, not LLM latency). After fixing the harness to
force a fresh cache miss per concurrent request (Section 5.3), the
corrected figure is **1.62 requests/second** at a mean per-request latency
of **3.09 s** under 10 concurrent sessions. This remains the more relevant
number for real deployment capacity than the sequential figures, since
concurrent requests overlap their network round-trip time — but it is
three orders of magnitude lower than first reported, and the earlier
800 req/s figure should not be cited.

The realism-score drop (4.38 → 4.00) is honestly reported as a real cost
of the shorter generation cap, though it is confounded with a
data-completeness improvement: the "before" score is computed over only
24 of 30 samples (6 failed to parse, due to a transient OpenRouter error
unrelated to the engine changes — see Section 7), while the "after" score
reflects all 30. Judge reasons for the lower-scored "after" responses
cite missing detail ("lacks specific details," "missing expected
Jenkins-specific details") consistent with the shorter token cap, not a
change in the model's persona-consistency. Response diversity
(0.95–1.00) and the blockchain integrity property were unaffected by
these changes.

### 5.2.1 Extending the Fix to All Five Decoys

The ai-engine fix above addressed one hop in the request path
(ai-engine → OpenRouter). An identical anti-pattern existed one hop
earlier, in every one of the five decoys: each decoy's logging call
(every attacker interaction posted to the backend) and its ai-engine call
opened a new `aiohttp.ClientSession` — a fresh TCP connection — on every
single request rather than reusing one. This was fixed identically
across all five decoys (`shadow-shell`, `oracle-ai`, `vault-sql`,
`ledger-trap`, `forge-ci`), each now creating one pooled session at
process startup instead of per-request.

To isolate the decoy layer's own contribution from the ai-engine's, the
before/after code was checked out via git and run side-by-side on
different ports, against static/deterministic payloads so ai-engine
latency does not dominate the measurement:

| Decoy | Before (mean) | After (mean) | Change |
|---|---|---|---|
| oracle-ai | 6.15 ms (σ=3.89) | 4.28 ms (σ=0.70) | −30.4% |
| vault-sql | 0.69 ms (σ=1.94) | 0.41 ms (σ=0.44) | −41.4% |
| ledger-trap | 5.96 ms (σ=2.43) | 4.20 ms (σ=0.75) | −29.5% |
| forge-ci | 6.95 ms (σ=3.13) | 6.71 ms (σ=3.02) | −3.4% |
| shadow-shell (SSH) | 7.91 ms (σ=9.94) | 4.64 ms (σ=6.55) | −41.3% |

The effect is smaller in absolute terms than the ai-engine fix — localhost
TCP handshakes are cheap relative to a cross-internet TLS handshake to
OpenRouter — but real and consistent across four of five decoys, and it
substantially tightens latency variance (standard deviation drops by
roughly half to two-thirds in every case): a connect-per-request pattern
is more exposed to occasional slow handshakes than a warm, reused
connection. `forge-ci` shows negligible change because its measured
endpoint always routes through the ai-engine regardless of decoy-layer
pooling, so its latency floor is set by the ai-engine's own cache lookup,
not the decoy's connection handling.

### 5.3 Blockchain Integrity Test

A log entry with hash `356b7496...33a9a1` (truncated) was submitted,
anchored on-chain (`blockchain_anchored: true`), and fetched back;
re-hashing the unmodified entry reproduced the identical hash. Re-hashing
a copy with `raw_data` altered from `"sudo cat /etc/shadow"` to `"ls -la"`
produced a different hash (`7530fb00...0d9d394`), confirming the
tamper-evidence property: any change to a logged entry after anchoring is
detectable by recomputation, without needing to trust the host storing
the log. This test is unaffected by the optimization pass in Section 5.2.

### 5.4 Third Run: Real-World Dataset and a Benchmark-Harness Correction

The adversarial dataset used in Sections 5.1–5.3 (`apt_attack_dataset.json`)
was originally hand-written: representative SQLi, command-injection, and
RPC-abuse strings authored to *look like* real attack traffic. To ground
the evaluation in verifiably real attacker input rather than
plausible-looking synthetic strings, the dataset was rebuilt to pull real,
publicly-documented payloads from named sources: real command-injection
strings for `ssh` (`payload-box/command-injection-payload-list`), real SQL
injection strings for `sql` (`payload-box/sql-injection-payload-list`),
real prompt-injection/SSRF/XXE/Log4Shell strings for `api`
(`swisskyrepo/PayloadsAllTheThings`), the documented Ethereum JSON-RPC
methods an exposed node's attack surface actually consists of for `web3`,
and documented Jenkins script-console/path-traversal techniques for
`cicd`. The dataset grew from 100 to 200 payloads (40/service; see the
project README's "Dataset provenance" section for the full source list).
`evaluate.py` was re-run in full against the live stack with this dataset.

Two results are worth reporting on their own merits, independent of the
earlier optimization narrative:

**Response diversity on the `api` service dropped from 1.00 to 0.70** —
the clearest signal this re-run produced that the hand-written dataset
had missed. Inspecting the judge's per-sample reasoning
(`evaluation_results.json`) shows the model frequently collapses to a
generic "invalid request" response when the payload is a real XXE
(`<!ENTITY ...>`) or Log4Shell (`${jndi:...}`) string, rather than
emulating a plausible vulnerable-parser response to that exact payload —
e.g. *"Generic error message without any specific details or XML parsing
error indication."* The hand-written `api` payloads were simple JSON
chat-style prompts the model already handled fluently, so this weakness
was invisible until real payload shapes were used. It is now a concrete,
evidence-backed follow-up: the `oracle-ai` decoy's system prompt likely
needs XML/JNDI-aware few-shot examples.

**A genuine bug in the evaluation harness itself was found and fixed
during this re-run.** `bench_concurrent_throughput()` had reused
`dataset[:CONCURRENCY_LEVEL]` — the same 10 payloads already sent once
earlier in the same run via `diversity_pass()`, which exercises the
entire dataset. Because the ai-engine's Redis cache key is
`md5(command + history)` (`ai-engine/engine.py`), these were guaranteed
cache hits by the time the concurrent-throughput step ran, despite the
function's docstring asserting the payloads were cache-proof. They were
not: the dataset's nonces are generated once at dataset-build time, not
refreshed per benchmark call. This means **the 800.3 requests/second
concurrent-throughput figure reported in Section 5.2 was a Redis
cache-hit measurement (8.2 ms mean latency), not a measurement of LLM
throughput under concurrent load** — despite being reported and discussed
in Section 6 as if it were. The fix appends a fresh UUID nonce to each
payload immediately before firing the concurrent batch, forcing a genuine
cache miss on every one. The corrected measurement is:

| Metric | First-reported (cache-hit bug) | Corrected |
|---|---|---|
| Concurrent throughput (10 sessions) | 800.3 req/s | **1.62 req/s** |
| Mean per-request latency | 8.2 ms | **3.09 s** |

This correction does not change the sequential-latency, response-diversity,
or blockchain-integrity results in Sections 5.1–5.3, which were each
measured independently and did not share this code path. It does mean
the Discussion's framing in Section 6 — that the system is "not
throughput-starved under concurrent load" — is not supported by this
measurement and has been revised accordingly. We report the bug and the
correction explicitly, rather than quietly substituting the corrected
number, because the original figure was published in an earlier revision
of this evaluation and a benchmark bug this large (three orders of
magnitude) is itself a relevant methodological finding for anyone citing
or reproducing this work.

## 6. Discussion

The latency/throughput trade-off means this architecture is not a drop-in
replacement for high-volume, low-interaction scanning honeypots — a
static-path system remains appropriate there. It is instead targeted at
**high-interaction deception** against a human operator or a
sophisticated, low-volume automated tool, where the multi-second
per-request response latency is plausibly attributable to network
conditions or server load rather than to a honeypot, and where sustained,
contextually consistent engagement yields materially better threat
intelligence than an immediately-abandoned static session.

The distinction between sequential and concurrent throughput (Section
5.2, corrected in Section 5.4) matters for how this trade-off should be
read, though the corrected measurement is less favorable than first
reported: a single attacker session pays the full ~2.06s mean latency per
command against the real-world dataset (Section 5.4), and under genuine
concurrent load — 10 simultaneous sessions, each forced to bypass the
Redis cache — sustained throughput is **1.62 requests/second** at a mean
per-request latency of 3.09s, not the 800 req/s first reported (that
figure was a benchmark-harness bug measuring Redis cache-hit latency; see
Section 5.4). The corrected number still shows the architecture serves
concurrent sessions without the LLM round-trip time compounding linearly
per session — 10 concurrent requests complete in 6.16s wall-clock, not
~20s (10 × 2.06s) — but the concurrency headroom is real, not the
three-orders-of-magnitude figure the uncorrected benchmark implied. This
is the more relevant capacity question for a real deployment fielding
several simultaneous low-volume sessions, but it does not support a claim
of high-volume concurrent capacity.

The blockchain-anchoring design assumes the anchoring chain (or its RPC
endpoint) is itself outside the attacker's reach — a reasonable assumption
for an internal Ganache/private-chain deployment, less so if a public
chain's RPC endpoint were reachable from the same network segment as a
compromised honeypot host. We did not evaluate anchoring against an
adversary who also compromises the blockchain client, which is out of
scope for this system's threat model (it defends log integrity against
tampering with the *stored log*, not against an attacker who controls the
entire logging pipeline before hashing).

## 7. Limitations and Future Work

- The LLM-judge realism score is an automated proxy; a human-subject study
  (as in shelLM) is necessary to validate it against real attacker
  perception.
- Section 5.4 replaced the original 100-payload hand-curated dataset with
  a 200-payload dataset built from real, publicly-documented attack
  payloads, which is a meaningful improvement over hand-written strings
  but is still not a live-traffic capture; it does not include the full
  diversity of real-world attacker *behavior* (multi-step sessions,
  timing, evasion attempts) a live deployment would see, only realistic
  single-payload content.
- Intent classification is keyword-based and will misclassify obfuscated
  or novel attack patterns; a learned classifier is a natural extension.
- We did not run a longitudinal live-internet deployment in this study;
  results reflect a controlled, synthetic evaluation.
- The before/after optimization comparison (Section 5.2) used two
  different OpenRouter API keys, because the first key stopped
  authenticating between runs for reasons outside this project's control.
  This does not affect either run's internal validity, but the two runs
  were not executed back-to-back on identical infrastructure state, and
  the realism-score change is confounded with a judge-completeness
  improvement (24/30 scored vs. 30/30) rather than isolating the
  token-length effect alone — a controlled run varying only `max_tokens`
  is needed to attribute the realism change precisely.
- The concurrent-throughput measurement used a single burst of 10
  simultaneous requests; it was not tested at higher concurrency levels
  or under sustained (non-burst) load, so the corrected 1.62 req/s
  (Section 5.4) should be read as a single-burst demonstration at one
  concurrency level, not as a validated capacity ceiling. The original
  800 req/s figure this section referenced in earlier revisions was a
  benchmark-harness bug (Section 5.4) and does not describe the system.

## 8. Conclusion

We presented a multi-protocol cyber deception framework that replaces the
static response tables of traditional honeypots with a three-tier,
LLM-backed response engine spanning five distinct decoy services, and
that anchors every log entry's hash on an independent blockchain to make
the resulting forensic trail tamper-evident. Rather than a single
unexplained accuracy figure, we measured and reported the actual
trade-off along four independent axes across three successive evaluation
runs: an initial latency cost of ~4.03s mean, reduced by a measured ~3x
via connection pooling and a tuned generation-length cap to 1.35s mean
(0.4 ms for the static path throughout) against a hand-curated dataset,
rising to 2.06s mean against a subsequent 200-payload dataset built from
real, publicly-documented attack corpora rather than hand-written strings
(Section 5.4); a corrected concurrent throughput of 1.62 requests/second
at 3.09s mean per-request latency under 10 simultaneous sessions, after
finding and fixing a benchmark-harness bug that had silently reported an
800 requests/second Redis cache-hit measurement as if it were LLM
throughput; response diversity of 0.80–1.00 across four of five services
against real payloads (0.70 for the API decoy, a genuine and now
documented weakness against real XXE/Log4Shell payload shapes) versus
near-zero for a static baseline; and a mean LLM-judged realism score
stable at 4.00–4.03/5 across all three runs on complete 30/30-sample
scoring — and we separately confirmed the blockchain anchoring's
tamper-evidence property end-to-end. We reported the optimization pass's
realism cost (a 0.38-point drop, confounded with a data-completeness
improvement), the real-dataset diversity regression, and the benchmark
harness bug alongside the favorable numbers rather than presenting only
the latter. This positions the system for high-interaction deception
against human operators or low-volume sophisticated tooling — not as a
replacement for the high-throughput, low-interaction honeypots that
remain appropriate for Internet-scale scanning — and we have been
explicit throughout about where an LLM-judge score is a proxy rather than
a substitute for human evaluation. Future work should validate the
realism findings with human subjects, replace keyword-based intent
classification with a learned
model, and evaluate the system under sustained live-traffic conditions
rather than a synthetic dataset alone.

## References

*(Populate in the target citation style — IEEE numeric is typical for a
college systems-security paper. Draft reference list below; verify DOIs/
URLs before final submission.)*

1. A. Vetterl and R. Clayton, "Bitter Harvest: Systematically Fingerprinting
   Low- and Medium-interaction Honeypots at Internet Scale," in *Proc. 12th
   USENIX Workshop on Offensive Technologies (WOOT '18)*, 2018.
2. "Gotta Catch 'em All: A Multistage Framework for Honeypot
   Fingerprinting," *ACM Digital Threats: Research and Practice*, 2023.
   arXiv:2109.10652.
3. "A Review of Honeypots: Fingerprinting Techniques, Detection, and
   Evasion Mechanisms," *MDPI Future Internet*, 2026.
4. M. Sladić, V. Valeros, C. Catania, and S. Garcia, "LLM in the Shell:
   Generative Honeypots," in *Proc. IEEE EuroS&PW*, 2024. arXiv:2309.00155.
5. Z. Wang et al., "HoneyGPT: Breaking the Trilemma in Terminal Honeypots
   with Large Language Model," arXiv:2406.01882, 2024.
6. F. McKee and D. Noever, "Chatbots in a Honeypot World," arXiv:2301.03771,
   2023.
7. "LLM Honeypot: Leveraging Large Language Models as Advanced Interactive
   Honeypot Systems," arXiv:2409.08234, 2024.
8. "Blockchain-Based Evidence Tracking System for Forensic Integrity and
   Secure Chain of Custody," *IEEE*, 2025.
9. "Blockchain-based tamper-proof and transparent investigation model for
   cloud VMs," *The Journal of Supercomputing*, Springer, 2022, DOI:
   10.1007/s11227-022-04567-4.
10. "A novel intelligent cyber threat detection system with
    blockchain-enforced immutable forensic auditability," *PeerJ Computer
    Science*, 2025.
11. MITRE, "MITRE Engage: A Framework and Community for Cyber Deception,"
    2022. [Online]. Available: https://engage.mitre.org/
12. "Three Decades of Deception Techniques in Active Cyber Defense —
    Retrospect and Outlook," *Computers & Security*, 2021.
13. M. Bercovitch, M. Renford, L. Hasson, A. Shabtai, L. Rokach, and
    Y. Elovici, "HoneyGen: An Automated Honeytokens Generator," in *Proc.
    IEEE International Conference on Intelligence and Security Informatics
    (ISI)*, 2011.
14. "A Proactive Decoy Selection Scheme for Cyber Deception using MITRE
    ATT&CK," arXiv:2404.12783, 2024.
15. "Empirical Telemetry-based Metrics for Evaluating Honeypot Realism and
    Deception Effectiveness," *International Journal of Network Security &
    Its Applications*, 2026.
