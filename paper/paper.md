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
three axes — latency/throughput, response diversity across a 100-payload
adversarial dataset, and an LLM-judge realism score — and report the
measured trade-off explicitly rather than a single composite metric. Our
results show a static fast-path throughput of 2,500 requests/second versus
0.25 requests/second for the LLM-backed path (a ~10,000x difference), a
response-diversity (uniqueness) ratio of 0.95–1.00 across all five decoy
services versus near-zero for a static baseline by construction, and a
mean LLM-judged realism score of 4.38/5 (σ = 1.28, n = 24 of 30 sampled
responses successfully scored) at a mean latency cost of roughly 4.0
seconds versus 0.4 milliseconds for the static path. We discuss where
this trade-off is acceptable (human-operated intrusion, not internet-wide
scanning) and the limitations of automated realism scoring as a proxy for
human deception studies.

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

A 100-payload synthetic adversary dataset (`apt_attack_dataset.json`), 20
payloads per decoy service, generated by `generate_dataset.py` from
hand-curated attack patterns (reverse shells, SQL injection, RPC abuse,
prompt injection, CI/CD supply-chain payloads) each tagged with a random
nonce to defeat caching during evaluation.

### 4.2 Metrics

1. **Latency / throughput.** 30 trials of the static fast-path and 20
   trials of the LLM-backed path; mean, median, and standard deviation
   reported rather than a single sample, addressing a methodological gap
   in the project's original benchmark (which used a single dynamic-path
   measurement and reported it as if representative).
2. **Response diversity.** Across the full 100-item dataset, the fraction
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

| Metric | Static fast-path | LLM-backed dynamic path |
|---|---|---|
| Mean latency | 0.4 ms | 4,028 ms (4.03 s) |
| Median latency | 0.4 ms | 3,529 ms (3.53 s) |
| Stdev | 0.1 ms | 2,380 ms (2.38 s) |
| Min / Max latency | 0.3 / 0.7 ms | 1,037 / 8,807 ms |
| Throughput (req/s) | 2,500 | 0.25 |
| Response diversity (uniqueness ratio, mean across 5 services) | ~0 by construction | 0.99 (range 0.95–1.00) |
| Avg. response length (words) | 0 (static string) | 16.2 |

**Response diversity by service:** web3 1.00, cicd 1.00, sql 1.00, ssh
0.95, api 1.00 (each n = 20 unique payloads).

**LLM-judge realism score:** mean **4.38 / 5** (σ = 1.28, n = 24 of 30
sampled responses successfully parsed as judge output — six calls
returned unparseable judge output and are excluded rather than assumed
either way). Score distribution: 1→2, 2→1, 3→1, 4→2, 5→18. The
low-scoring cases clustered around CI/CD payloads where the engine
returned an overly generic response rather than one tailored to the
specific attack (e.g., a path-traversal `job_name` payload), and one
web3 payload (`personal_unlockAccount`) where the returned result value
did not match the expected format for that RPC method — both are
concrete, fixable prompt-engineering gaps rather than fundamental
limitations of the approach.

**Blockchain integrity test:** a log entry with hash
`356b7496...33a9a1` (truncated) was submitted, anchored on-chain
(`blockchain_anchored: true`), and fetched back; re-hashing the
unmodified entry reproduced the identical hash. Re-hashing a copy with
`raw_data` altered from `"sudo cat /etc/shadow"` to `"ls -la"` produced a
different hash (`7530fb00...0d9d394`), confirming the tamper-evidence
property: any change to a logged entry after anchoring is detectable by
recomputation, without needing to trust the host storing the log.

## 6. Discussion

The latency/throughput trade-off means this architecture is not a drop-in
replacement for high-volume, low-interaction scanning honeypots — a
static-path system remains appropriate there. It is instead targeted at
**high-interaction deception** against a human operator or a
sophisticated, low-volume automated tool, where the multi-second response
latency is plausibly attributable to network conditions or server load
rather than to a honeypot, and where sustained, contextually consistent
engagement yields materially better threat intelligence than an
immediately-abandoned static session.

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
- The 100-payload dataset is synthetic and hand-curated; it does not
  capture the full diversity of real-world attacker behavior a live
  deployment would see.
- Intent classification is keyword-based and will misclassify obfuscated
  or novel attack patterns; a learned classifier is a natural extension.
- We did not run a longitudinal live-internet deployment in this study;
  results reflect a controlled, synthetic evaluation.

## 8. Conclusion

We presented a multi-protocol cyber deception framework that replaces the
static response tables of traditional honeypots with a three-tier,
LLM-backed response engine spanning five distinct decoy services, and
that anchors every log entry's hash on an independent blockchain to make
the resulting forensic trail tamper-evident. Rather than a single
unexplained accuracy figure, we measured and reported the actual
trade-off along three independent axes: a ~10,000x latency cost (0.4 ms
vs. 4.03 s mean) in exchange for near-total response diversity (0.95–1.00
uniqueness vs. near-zero for a static baseline) and a mean LLM-judged
realism score of 4.38/5, and we separately confirmed the blockchain
anchoring's tamper-evidence property end-to-end. This positions the
system for high-interaction deception against human operators or
low-volume sophisticated tooling — not as a replacement for the
high-throughput, low-interaction honeypots that remain appropriate for
Internet-scale scanning — and we have been explicit throughout about
where an LLM-judge score is a proxy rather than a substitute for human
evaluation. Future work should validate the realism findings with human
subjects, replace keyword-based intent classification with a learned
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
