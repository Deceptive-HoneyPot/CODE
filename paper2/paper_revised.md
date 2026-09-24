# A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging

**Revised manuscript — camera-ready revision responding to reviewer comments**

**Radhika G¹, Sisir Reddy Nellore², Pranav Sharma Chouduru³, Surya Tejeswar Reddy Nagireddy⁴, Guru Sai Prasad Reddy Bompalli⁵, Vishnu Sathwick Rajala⁶**

Department of Computer Science and Engineering
Amrita School of Computing, Coimbatore
Amrita Vishwa Vidyapeetham, India

g_radhika@cb.amrita.edu¹, cb.sc.u4cse23129@cb.students.amrita.edu², cb.sc.u4cse23611@cb.students.amrita.edu³, cb.sc.u4cse23127@cb.students.amrita.edu⁴, cb.sc.u4cse23111@cb.students.amrita.edu⁵, cb.sc.u4cse23644@cb.students.amrita.edu⁶

---

## Abstract

Low- and medium-interaction honeypots remain a cost-effective source of attacker telemetry, but their reliance on fixed response tables makes them straightforward to fingerprint. A scanner that sends a handful of atypical requests can observe that the replies are drawn from a finite, deterministic set and disengage. We present a multi-protocol deception framework that replaces the fixed response table with a language-model (LM) response engine serving five heterogeneous decoys: an interactive SSH shell, a PostgreSQL query endpoint, an internal AI/chat API, an Ethereum JSON-RPC node, and a Jenkins continuous-integration server, all behind a single connection-logging proxy. A three-tier response path answers routine traffic from a static fast-path and a cache in sub-millisecond time and escalates only novel requests to the LM. Every interaction is intent-classified by a transparent rule set, hashed with SHA-256, and anchored as a transaction on a local Ethereum chain, yielding a tamper-evident audit trail whose integrity does not depend on the logging host. We evaluate the system against a static-response baseline using a corpus of 2,500 real, publicly documented attack payloads spanning all five services. The dynamic path answers with a mean latency of 2.33 s against 0.8 ms static-path latency, sustains 1.61 requests/s under 10 concurrent sessions, and produces high output diversity for all five services (uniqueness ratio 0.64 to 0.992) against the near-zero diversity of a static table. The mean LM-judge realism score is 4.37/5. This revision adds four analyses absent from the original manuscript: a layered treatment of fingerprinting resistance that identifies a timing side-channel our own latency data exposes and that response diversity does not address; a security analysis of the risks a generative response layer introduces, including cache-miss cost exhaustion and injection into the operator console; a parametric cost model grounded in measured token counts; and a concurrency-scaling analysis showing the system saturates at an effective parallelism of 3.5 because of the hosted inference provider rather than the framework. We report the per-service realism disparity, the limits of an automated realism proxy, and a specified protocol for the human-subject study that a stronger claim would require.

**Index Terms** — honeypot, cyber deception, large language models, blockchain, digital forensics, intrusion detection.

---

## 1. Introduction

A honeypot is a decoy system deployed with no legitimate purpose, so that any interaction with it is by definition suspicious. Because they generate high-signal telemetry at low operational risk, honeypots are a standard component of threat-intelligence and early-warning pipelines. The dominant low- and medium-interaction designs, exemplified by SSH/Telnet decoys that emulate a shell without booting a real operating system, achieve their low cost precisely by not being real. They answer from a hand-written table of canned responses. This is also their central weakness. An automated scanner that issues even a few commands outside the table observes responses that are missing, inconsistent, or identical across supposedly distinct hosts, and concludes it is talking to a decoy. Vetterl and Clayton [5] showed that such fingerprinting can be performed at Internet scale with a single packet, at an equal-error rate of 0.0183, identifying 7,605 honeypot instances across nine implementations in the wild.

The problem is structural rather than a matter of writing a larger table. Any finite, static response set is enumerable, and an adversary who enumerates it can distinguish the decoy from a genuine service. What is needed is a response mechanism that is generative rather than tabular, one that can produce a plausible, context-consistent reply to a request never seen before.

Modern language models are a natural fit for this role. An instruction-tuned model, prompted to emulate the raw output stream of a specific service, can synthesise responses to arbitrary inputs while maintaining session consistency. This capability introduces two engineering tensions that a deployable system must resolve. First, an LM call costs on the order of seconds, whereas a real service answers routine requests in microseconds. A design in which every request goes to the model is both slow and expensive, and its latency profile is itself a fingerprinting signal. Second, an LM occasionally breaks character, emitting a refusal, a disclaimer, or an explanatory aside that no real service would produce. This is a deception-fatal tell rather than a minor stylistic flaw.

A second, orthogonal concern is the integrity of the collected evidence. A honeypot log that is only a file on the collecting host is only as trustworthy as that host. If the honeypot is compromised, which is a real risk since its entire purpose is to be attacked, the attacker can edit or delete the very records of the intrusion. For telemetry that is to be used as forensic evidence, the audit trail needs an integrity guarantee that survives compromise of the logging system itself.

This paper describes a framework that addresses both concerns together and reports an evaluation of the result. Our contributions are:

1. **A multi-protocol, LM-backed deception layer** covering five distinct modern attack surfaces (SSH, SQL, an internal AI API, an Ethereum RPC node, and a CI/CD server) behind one logging proxy, with a three-tier response path that keeps routine traffic fast while reserving generative responses for novel inputs.

2. **Blockchain-anchored forensic logging**, in which every interaction is hashed and the hash is committed on-chain, giving each record tamper-evidence independent of the honeypot host, verifiable after the fact by any party.

3. **A four-axis evaluation against a static baseline** on a corpus of real, publicly documented attack payloads, measuring latency and throughput, concurrent throughput, per-service response diversity, and an LM-judge realism score.

4. **A layered analysis of fingerprinting resistance** (Section 7) that separates transport-level, timing-level, content-level, and semantic-level detection, and that identifies a timing side-channel arising directly from the tiered design. Response diversity, the metric most generative-honeypot papers report, addresses only one of these four layers.

5. **A security analysis of the generative response layer itself** (Section 8), covering prompt injection against the decoy, cost-exhaustion through forced cache misses, injection into the operator console, and the distinction between record integrity and record truth.

6. **A parametric cost model** (Section 9) grounded in measured output-token counts, expressing operating cost as a function of the fast-path hit rate rather than assuming one.

The remainder of the paper is organised as follows. Section 2 reviews related work. Section 3 states the threat model and design goals. Section 4 describes the architecture and Section 5 the evaluation method. Section 6 reports the measured results, including the concurrency-scaling analysis. Sections 7, 8, and 9 present the fingerprinting, security, and cost analyses. Section 10 compares the framework with prior systems, Section 11 documents the engineering gaps resolved during construction, and Section 12 sets out the validation work required to support stronger claims. Sections 13 and 14 discuss limitations and conclude.

---

## 2. Related Work

We organise prior work into four strands: classical honeypots and their detectability, LLM-backed deception, secure and blockchain-anchored logging, and the broader deception and evaluation literature.

### 2.1 Classical honeypots and fingerprinting

Honeypots have been a standard sensor since Spitzner's foundational treatment [1] and Provos's Honeyd virtual-honeypot framework [2]. The widely deployed low- and medium-interaction systems, the Cowrie SSH/Telnet honeypot [3] and the malware-capturing Dionaea [4], emulate services from fixed response logic. This makes them cheap and safe but also enumerable. Vetterl and Clayton [5] made this concrete at scale. Exploiting the fact that such honeypots reuse off-the-shelf protocol libraries whose behaviour deviates subtly from the real service, they fingerprinted low- and medium-interaction honeypots with a single packet at an equal-error rate of 0.0183, locating 7,605 instances across nine honeypot implementations on the Internet, of which the Cowrie and Kippo SSH family formed the largest group. This structural weakness is the core problem a generative response mechanism is meant to solve. We return to it in Section 7, where we argue that the attack Vetterl and Clayton describe operates at a layer that generative response synthesis does not defend.

### 2.2 LLM-backed generative honeypots

Replacing the fixed table with a language model was proposed conceptually by McKee and Noever [10], who showed ChatGPT imitating Linux, Mac, and Windows terminal commands. The ShelLM system of Sladić et al. [11] was the first integrated generative SSH honeypot and remains the strongest published realism result. In a human-subject study of 226 commands it reached 0.92 accuracy and a 0.90 true-negative rate. Subsequent systems refined the architecture. HoneyGPT [12] added a dedicated prompt-management component to track session state and framed its design as resolving a three-way tension between flexibility, depth of interaction, and deception quality. HoneyLLM [13] added a filter and router front end and reported a mean 1.88 s per command against a 0.138 s Cowrie baseline. A systematisation by Bridges et al. [15] catalogues sixteen such systems and distils a canonical architecture consisting of a filter and router, a deterministic cached responder, a prompt and state manager, and an LLM engine. Our tiered design independently mirrors this structure.

Two limitations recur across this literature and directly motivate our work. First, realism is fragile. Weber et al. [14] found in a human study that only 52% of GPT-3.5 honeypot responses were convincing, with compound commands the main failure mode. We echo this caution in our own AI-API result. Second, every system in this line targets a single surface, a Linux shell, and none anchors its logs for integrity. We extend the generative approach to five heterogeneous protocols and add tamper-evident logging, while engaging the same three open problems the literature identifies: latency and cost, session consistency, and character stability.

### 2.3 Secure and blockchain-anchored logging

The integrity of security logs is a long-studied problem. Schneier and Kelsey [17] introduced secure audit logs resistant to tampering by an attacker who compromises the logging host, and Ma and Tsudik [18] advanced forward-secure sequential aggregate authentication for the same threat. More recently, distributed ledgers have been used to anchor log integrity. Instead of placing the full data on-chain, only a short hash of each record is written to the ledger, so that any subsequent edit is caught by recomputing the hash and comparing it against the committed value, as in the blockchain-enabled audit logs of Sutton and Samavi [21], building on the integrity guarantees of the Bitcoin [19] and Ethereum [20] ledgers. We apply this well-established pattern specifically to honeypot telemetry, a setting where the logging host is by design the thing being attacked, so that the evidentiary value of the logs does not rest on the integrity of the collecting host. To our knowledge this coupling of a generative multi-protocol honeypot with on-chain log anchoring has not previously been reported.

### 2.4 Deception frameworks, honeytokens, and evaluation

Beyond service emulation, a broad literature places decoys throughout an environment. The survey of deception techniques by Han et al. [6] frames the design space, Bowen et al. [7] embed beacons in decoy documents to bait insiders, and the honeywords of Juels and Rivest [8] plant decoy passwords to detect credential theft. Recent surveys track the field's evolution toward honeypot performance [9]. Our contribution is complementary and narrower: a self-contained multi-protocol decoy cluster with a generative response layer and integrity-anchored logging.

On evaluation, human-subject detectability studies remain the gold standard [11], [14] but are costly. Automated proxies, output diversity and increasingly the use of a second model as a judge under the LLM-as-judge paradigm [22], are cheaper but imperfect. We adopt both diversity and an LM judge and are explicit in Section 5.4 that the judge is a proxy, reporting where it is unreliable rather than treating its score as ground truth. Automated downstream analysis of the resulting telemetry, for example mapping captured commands to MITRE ATT&CK [23] tactics as LogPrécis [16] does at over 90% accuracy, is a natural consumer of the intent-classified, integrity-anchored logs our framework produces.

---

## 3. Threat Model and Design Goals

### 3.1 Adversary model

We consider two adversary classes, following the distinction the recent literature draws [15]. The first is the automated scanner: a high-rate, non-interactive bot that probes exposed services, issues a small set of stereotyped requests, and moves on. Such scanners dominate real honeypot traffic, and field studies report that the overwhelming majority of honeypot activity is automated scanning rather than hands-on-keyboard interaction [15]. They fingerprint by looking for deterministic, enumerable, or internally inconsistent responses [5]. The second is the interactive intruder: a human, or a human-directed agent, who has reached a shell or service and explores it at human speed, issuing novel, context-dependent commands.

The two classes stress different properties. The scanner stresses breadth, consistency, and latency uniformity. The intruder stresses the ability to answer genuinely novel input in character. In this revision we add a third class, discussed in Section 7: the **adaptive fingerprinter**, an adversary who knows the general architecture of a tiered generative honeypot and probes specifically for its seams, most obviously the latency discontinuity between the static fast-path and the model path.

We further assume the honeypot host itself may be compromised. Its entire purpose is to be attacked, so an adversary who gains sufficient access could attempt to alter or delete the records of the intrusion. The integrity mechanism must therefore not rely on trusting the collecting host. We treat the blockchain node as an append-only integrity anchor and assume standard cryptographic hardness of SHA-256 and of the underlying ledger. We do not claim confidentiality of the logged data, only tamper-evidence.

### 3.2 Design goals

- **G1 — Non-enumerable responses.** Output must not collapse to a small deterministic set an automated probe can cluster. Addresses the scanner; evaluated as response diversity, Section 6.3.
- **G2 — Novel-input handling.** The system must answer requests never seen before with plausible, context-consistent output. Addresses the intruder; evaluated as realism, Section 6.4.
- **G3 — Latency compatible with a real service.** Routine traffic must be answered fast enough that timing is not itself a tell. Section 6.1, revisited critically in Section 7.2.
- **G4 — Multi-protocol coverage.** A single framework should span several distinct modern attack surfaces rather than one. Section 4.2.
- **G5 — Host-independent log integrity.** Every record must be verifiable as untampered even if the honeypot host is compromised. Section 6.5.
- **G6 — Actionable, auditable classification.** Captured interactions should be labelled by attack intent using an explainable mechanism suitable for forensic use. Section 4.4.

Section 13 revisits where these goals are met and where they are met only partially.

---

## 4. System Architecture

The framework is a set of containerised services on an isolated bridge network. Only two components are reachable from outside: the connection proxy that fronts the decoys, and the monitoring dashboard. The decoys, the response engine, the datastore, and the blockchain node communicate only on the internal network, so an attacker interacting with a decoy cannot reach the control plane directly.

### 4.1 Connection proxy and network isolation

A single asynchronous proxy listens on the five public decoy ports and transparently forwards each connection to the corresponding internal decoy. It records every inbound connection, source address and target port, before any decoy responds, so that even a bare port scan that never completes a protocol handshake is captured. Separating the public-listening concern from the decoy logic keeps the decoys off the public interface and gives a single choke point for connection-level telemetry.

### 4.2 Decoy services

Five decoys cover distinct, currently relevant attack surfaces.

- **SSH shell (port 2222).** A real SSH server that accepts any credentials and presents an interactive shell identifying itself as a corporate Ubuntu database host. Login attempts and every subsequent command are logged; command output is produced by the tiered response path.
- **PostgreSQL endpoint (port 5433).** Accepts SQL queries and returns plausible tabular results or realistic error text, baiting SQL injection.
- **Internal AI API (port 8080).** An internal chat and prediction service, a target for prompt injection and jailbreak attempts.
- **Ethereum JSON-RPC node (port 8545).** Responds to the JSON-RPC methods attackers invoke against exposed nodes to enumerate and drain wallets.
- **Jenkins CI/CD server (port 9090).** Exposes build- and script-oriented endpoints representing the documented Jenkins attack surface.

Each decoy forwards a normalised record of every interaction to the central collector.

### 4.3 Three-tier response path

Generating every response with the LM would be slow, costly, and, because of the uniform multi-second latency, itself detectable. The response engine therefore uses three tiers, escalating only when necessary.

1. **Static fast-path.** The most common enumeration commands, for example directory listing, identity, and network-configuration queries on the SSH decoy, are answered from a fixed table in sub-millisecond time. This intercepts the bulk of routine traffic without an LM call. The realism cost is low, because these commands genuinely have stable, well-known outputs on a real host.

2. **Response cache.** Previously seen requests, keyed on the request and recent session context, are served from an in-memory cache, so a repeated probe does not incur a second LM call.

3. **Language-model synthesis.** Only novel requests reach the LM, which is prompted with a service-specific system persona instructing it to emit solely the raw output stream of the emulated service, with no explanation, no markdown, and no acknowledgement that it is a model, together with recent session history for consistency. The model used in our deployment is an instruction-tuned Llama-3.1-8B served through a hosted inference API, so the framework requires no local GPU.

This structure bounds the expected per-request cost. The fast-path and cache absorb routine load at near-zero latency, and only the genuinely novel tail pays the LM latency. Sections 7.2 and 8.2 examine two consequences of this design that the original manuscript did not address: the latency discontinuity is a fingerprinting surface, and the cache is a cost-control mechanism an adversary can deliberately defeat.

### 4.4 Intent classification

Every interaction is labelled with an attack-intent category by a transparent, rule-based classifier operating on the raw request text. The categories are SQL injection, prompt injection, crypto theft (abusive Ethereum RPC methods such as wallet unlock or transfer), cryptomining, reverse shell and RCE, privilege escalation (including brute-force login attempts and credential or secret access), supply-chain and CI/CD abuse, and reconnaissance (scanning, service enumeration, and the standard first-contact commands on a fresh shell). Anything unmatched is labelled unknown.

The classifier is intentionally rule-based rather than learned. The rules are auditable, need no training data, add no latency, and their decisions are explainable, properties we consider more valuable for a forensic sensor than the marginal coverage a learned model might add. The language model performs response synthesis, not classification; classification is a separate, deterministic stage. Section 12.2 specifies the precision and recall study needed to validate the rule set, which the present evaluation does not provide.

### 4.5 Blockchain-anchored logging

When a record reaches the collector it is intent-classified, serialised deterministically and hashed with SHA-256, and anchored by sending a transaction carrying that hash to a local Ethereum chain. The full record is retained in the datastore; only the digest is placed on-chain.

The integrity guarantee follows directly. To check a record later, one re-hashes it and compares against the value committed on-chain. Any post-hoc alteration of the stored record, by an attacker who has compromised the honeypot or by anyone else, changes its hash and is therefore detectable, because the on-chain digest cannot be silently rewritten. Integrity does not depend on trusting the logging host. Section 8.5 draws the distinction, important for forensic use, between proving a record has not been altered and proving that its contents are true.

### 4.6 Real-time dashboard

A web dashboard consumes the collector's live event stream and aggregate statistics. It presents intercepted-attack counts, per-intent and per-service breakdowns, ranked source addresses with a per-actor threat profile, and a searchable live feed in which each event exposes its payload, the decoy's response, its SHA-256 digest, and its on-chain anchoring status. Section 8.3 treats the dashboard as an attack surface in its own right, since it renders attacker-influenced text.

---

## 5. Evaluation Methodology

Our evaluation compares the LM-backed dynamic path against a static-response baseline and characterises the system along four independent axes. We report each axis separately rather than collapsing them into a single composite score, because the axes trade against one another and the trade-offs are the point.

### 5.1 Dataset

The evaluation corpus consists of 2,500 attack payloads drawn from public, permissively licensed security-research corpora and from documented real-world attack shapes, partitioned by target service: 1,862 SSH, 474 SQL, 136 API, 18 Web3, and 10 CI/CD. The SSH, SQL, and API partitions draw on large public payload lists, the SecLists collection [24] and PayloadsAllTheThings [25], covering command injection, SQL injection, and prompt injection, XXE, and SSRF strings. The Web3 and CI/CD partitions are deliberately smaller because their real attack surface is a small, finite set of RPC methods and exploit endpoints rather than an open space of injection strings.

Every entry retains a provenance field recording the corpus it came from. No payload is model-generated or hand-invented. Each service's payload count is capped at the number of distinct real payloads genuinely available for that service, so the corpus contains no duplicated or padded entries.

### 5.2 Attack-scenario coverage and its limits

Reviewers asked for a wider range of real-world attack scenarios. We address this in two parts: what the corpus does cover, and what it does not.

Table I maps the corpus partitions onto the adversary behaviours they represent and the corresponding MITRE ATT&CK [23] techniques. The payloads are real strings observed or catalogued in the wild, so the corpus covers the *content* of a broad range of contemporary attacks against these five surfaces.

**TABLE I. Corpus coverage by adversary behaviour.**

| Partition | n | Adversary behaviour represented | ATT&CK technique |
|---|---|---|---|
| SSH | 1,862 | Command injection, shell enumeration, reverse-shell staging, credential access, cryptomining installation | T1059.004, T1082, T1071, T1552 |
| SQL | 474 | SQL injection, schema enumeration, authentication bypass, data exfiltration via query | T1190, T1213 |
| API | 136 | Prompt injection, jailbreak, XXE, SSRF against an internal model-serving endpoint | T1190, T1552.001 |
| Web3 | 18 | Wallet enumeration, unauthorised account unlock and transfer against an exposed JSON-RPC node | T1190, T1657 |
| CI/CD | 10 | Build-system abuse, script-console RCE, credential harvesting from a CI server | T1195, T1059 |

The limitation is that the corpus is composed of **single-request payloads evaluated independently**. A real intrusion is a sequence: reconnaissance, then access, then escalation, then action on objectives, with each step conditioned on the output of the last. Our evaluation therefore measures the system's response to the individual constituents of real attacks, not its coherence across a multi-stage campaign. Session consistency, whether the decoy's account of the filesystem in step seven contradicts what it said in step two, is not measured by any metric we report. This is a substantive gap, and Section 12.3 specifies the multi-stage scenario evaluation that would close it. We prefer to state the gap plainly rather than describe the corpus in terms that imply campaign-level coverage it does not have.

### 5.3 Metrics

**Latency and sequential throughput.** We measure per-request latency for the static fast-path and for the dynamic LM path separately, over repeated trials, reporting mean, median, and standard deviation rather than a single sample. Sequential throughput is the reciprocal of mean latency.

**Concurrent throughput.** Because real attackers arrive concurrently, we fire ten requests simultaneously and measure sustained throughput and per-request latency under that load. To avoid inadvertently measuring cache-hit latency, each concurrent request carries a fresh nonce guaranteeing a cache miss and a genuine LM call.

**Response diversity.** For each service we run its entire payload partition through the engine and compute the uniqueness ratio, distinct outputs divided by total outputs. This is a proxy for one specific kind of fingerprintability. A static table tends toward a low ratio, since many payloads collapse to the same canned reply, whereas a generative engine that answers each payload differently tends toward 1.0. Section 7 sets out precisely which fingerprinting attacks this metric does and does not speak to.

**LM-judge realism.** A second, independent model, an instruction-tuned Llama-3.1-70B, is shown each attack payload and the decoy's response and asked to rate on a scale of 1 to 5 how convincingly the response imitates a real instance of that service, with 1 denoting an obvious tell such as a template, a refusal, or an AI disclaimer, and 5 denoting output indistinguishable from the real service. We sample 30 payloads for judging.

### 5.4 Limitations of the realism metric

The LM judge is an automated proxy, not a human-subject detectability study, and we treat its output accordingly. A model judge can be miscalibrated, can reward superficially plausible but subtly wrong output, and shares blind spots with the model it judges. Its sample size here, 30 responses, is small enough that the mean carries wide uncertainty. We therefore use the judge to locate gross realism failures and per-service disparities, not to certify indistinguishability, and we report its score distribution rather than only its mean. Section 12.1 specifies the human-subject protocol required for a stronger claim.

### 5.5 Blockchain integrity test

Independently of the realism evaluation, we verify the tamper-evidence claim directly. We fetch a stored record, recompute its SHA-256 digest, and confirm it matches the value anchored on-chain. We then modify a field of the record, re-hash, and confirm the digest no longer matches, demonstrating that alteration is detectable.

---

## 6. Results

All figures below are produced directly from the evaluation harness's output on a single run against the 2,500-payload corpus, using an instruction-tuned Llama-3.1-8B response engine and a Llama-3.1-70B judge.

### 6.1 Latency and throughput

The static fast-path answers in a mean of 0.8 ms (median 0.8 ms, standard deviation 0.3 ms, n = 30). The dynamic LM path answers in a mean of 2.33 s (median 1.73 s, standard deviation 1.40 s, range 1.15 s to 5.92 s, n = 20). The two paths are roughly four orders of magnitude apart. This gap is the explicit justification for the tiered design: routing routine traffic to the fast-path is what makes an LM-backed honeypot viable at all. Sequential dynamic throughput is 0.43 requests/s; the static path sustains on the order of 1,250 requests/s. The dynamic latency is dominated by the round trip to the hosted inference API rather than by local computation.

The same gap is a liability as well as an asset, and Section 7.2 quantifies it as a detection channel.

### 6.2 Concurrent throughput and scaling behaviour

Under ten simultaneous sessions, the system sustains 1.61 requests/s at a mean per-request latency of 2.19 s, completing the ten-request burst in 6.21 s wall time.

The original manuscript reported these numbers without analysing them. Doing so yields a result that speaks directly to the scalability question reviewers raised. Sequential throughput is 0.43 requests/s. Ideal linear scaling at concurrency 10 would give 4.29 requests/s. The measured 1.61 requests/s is a speedup of 3.76, a parallel efficiency of 0.376. Applying Little's Law to the measured figures, the mean number of requests in flight is 1.61 × 2.19 = 3.53, not 10.

Two things follow. First, the system saturates at an effective parallelism of roughly 3.5 concurrent model calls, well below the offered concurrency of 10. Second, and diagnostically more useful, mean per-request latency under load (2.19 s) is slightly *lower* than sequential mean latency (2.33 s), a ratio of 0.94. If requests were queueing inside our framework, latency would inflate with concurrency. It does not. The bottleneck is therefore upstream admission control at the hosted inference provider, which appears to admit approximately 3.5 of our requests concurrently, rather than any queue in the decoys, the proxy, or the response engine.

This distinction matters for deployment. The framework's own concurrency ceiling has not been reached at c = 10, so the ceiling we measured is a property of the inference provider and the account tier, not of the architecture. An operator who needs higher concurrent capacity should expect to obtain it by raising the provider's rate limit, by distributing calls across providers, or by self-hosting the model, rather than by re-engineering the framework.

We state clearly what this analysis is and is not. It is a valid inference from measurements at two concurrency levels, c = 1 and c = 10. It is not a scaling curve. We did not measure c = 25, 50, or 100, nor sustained rather than burst load, and we therefore make no claim about behaviour at those levels. Section 12.4 specifies the load-sweep experiment required.

### 6.3 Response diversity

Response diversity separates the generative engine sharply from a static baseline. All five services exhibit high output uniqueness on the 2,500-payload corpus: SQL 0.992 (470 distinct outputs across 474 payloads), Web3 0.944, SSH 0.903, CI/CD 0.900, and the AI-API decoy 0.640, which is the lowest but still far from the near-zero value a deterministic table would produce. A static response table would by construction collapse many distinct payloads onto the same canned reply and score near zero here.

The AI-API decoy's lower figure is the one soft spot. A meaningful minority of its responses to structurally similar payloads, for example XXE and XML probes and SSRF probes, converge on near-identical generic error text, which the realism analysis in Section 6.4 corroborates.

### 6.4 LM-judge realism

The mean LM-judge realism score is 4.37/5 (standard deviation 1.45, n = 30). The distribution is strongly bimodal: 25 responses rated 5, one rated 2, four rated 1, and none rated 3 or 4. This shape is consistent with a system that is usually in character but occasionally lapses completely, rather than one that is uniformly mediocre.

Inspecting the low-scoring cases, they are concentrated on, but not exclusive to, the AI-API decoy. The majority of low ratings fall on API responses to structured payloads, generic error text that does not acknowledge the specific XML or SSRF probe. The remainder fall on a small number of SSH responses that were templated or fell back to a bare "command not found" where a real shell would have said more.

We report these cases rather than smoothing them into the mean. The generative approach is convincing for the shell, database, RPC, and CI/CD decoys, while the AI-API decoy trails the other four on both metrics and is the clearest candidate for further work.

Table II consolidates the per-service picture. The disparity is consistent across both independent metrics: the structured-protocol decoys score 0.90 to 0.99 on diversity and highly on judged realism, while the AI-API decoy sits at 0.64 and draws most of the low ratings. That two metrics, one an automatic count of distinct outputs and the other an independent model's judgement, agree on which service is weakest is itself evidence that the finding is real rather than an artefact of either measure.

**TABLE II. Per-service results.**

| Service | Payloads | Distinct outputs | Uniqueness ratio | Judged realism |
|---|---|---|---|---|
| SQL | 474 | 470 | 0.992 | High |
| Web3 | 18 | 17 | 0.944 | High |
| SSH | 1,862 | 1,681 | 0.903 | High, with a small templated minority |
| CI/CD | 10 | 9 | 0.900 | High |
| AI-API | 136 | 87 | 0.640 | Lowest; source of most low ratings |

Sample sizes for judged realism are small and unevenly distributed across services. We do not report per-service realism means, because at this sample size they would not be meaningful.

### 6.5 Blockchain integrity

The integrity test behaves as designed. For an untampered record, the recomputed SHA-256 digest matches the anchored value exactly. After a single field of the record is altered, the recomputed digest diverges from the anchored value, so the tampering is detected. This confirms that the audit trail's integrity is verifiable independently of the logging host. An attacker who compromises the honeypot and edits a stored record cannot make the edited record's hash match what was already committed on-chain.

---

## 7. Resistance to Fingerprinting: A Layered Analysis

Reviewers asked whether response diversity holds up against sophisticated fingerprinting. It does not, on its own, and the honest answer requires separating fingerprinting into layers. Generative honeypot papers, ours included in its original form, tend to report a content-diversity metric and leave the impression that it addresses detection generally. It addresses one layer of four.

### 7.1 Layer 1: transport and protocol implementation

The attack of Vetterl and Clayton [5] does not look at response content at all. It exploits the fact that honeypots implement protocols using off-the-shelf libraries whose behaviour deviates from the reference implementation in ways the honeypot author never considered: option ordering in the SSH key-exchange, error behaviour on malformed packets, TCP window and timing characteristics, banner-string details. A single packet suffices.

**Response diversity provides no defence at this layer.** Our SSH decoy is a real SSH server, which helps at the key-exchange level, but our SQL, API, Web3, and CI/CD decoys are application-layer emulations behind HTTP, and none has been audited for protocol-implementation fidelity against the genuine PostgreSQL wire protocol, a real Geth JSON-RPC endpoint, or a real Jenkins instance. An adversary running the Vetterl and Clayton methodology against our deployment would very plausibly succeed, and nothing in our evaluation would have caught it. We regard this as the most significant unaddressed detection risk in the system, and note it is equally unaddressed by every generative honeypot in the literature we surveyed, none of which reports a transport-layer fidelity result.

### 7.2 Layer 2: timing

The tiered design creates a timing signature that our own measurements quantify precisely. The static fast-path answers in 0.8 ms with a standard deviation of 0.3 ms. The model path answers in 2.33 s with a standard deviation of 1.40 s. These distributions do not overlap. They are separated by roughly three and a half orders of magnitude, and the gap is far larger than the variance of either.

An adversary needs no sophistication to exploit this. Sending two commands, one common (`whoami`) and one arbitrary (a random string), and comparing the response times yields a ratio near 3,000 on our system. No real service exhibits that ratio between two commands of comparable output size, because on a real host both are answered by the same code path. **A single pair of probes is sufficient to detect the tiered architecture with high confidence.**

This is a direct and, we think, important consequence of the design choice the paper advocates. The tiering that makes an LM-backed honeypot economically viable is also the clearest fingerprinting surface it presents. We did not identify this in the original manuscript, and it qualifies the claim in design goal G3: routine traffic is answered fast enough that *absolute* latency is not a tell, but the *relative* latency between tiers is a stronger tell than slow responses would have been.

Three mitigations are available and none is free. Adding artificial delay to fast-path responses to match the model path forfeits the throughput advantage that motivated tiering. Adding calibrated jitter so the two distributions overlap partially reduces but does not eliminate the signal, since a few dozen probes recover the bimodality. Pre-generating and caching responses for the plausible novel space ahead of time shrinks the model path but cannot cover an open input space. A quantified evaluation of the jitter option, measuring the number of probes needed to distinguish tiers as a function of injected jitter, is the natural follow-on experiment and is specified in Section 12.5.

### 7.3 Layer 3: content and response-set enumeration

This is the layer our uniqueness-ratio metric addresses, and here the results are genuinely strong. Against an adversary who probes with many distinct payloads and clusters the responses, a static table collapses to a small number of equivalence classes and is trivially identified. Our engine returns 470 distinct outputs for 474 SQL payloads, so no useful clustering exists.

Two qualifications apply. First, uniqueness is necessary but not sufficient. Output that is unique but wrong scores well on this metric and poorly with a human, which is exactly the AI-API decoy's profile at 0.64 diversity and the majority of the low realism ratings. Second, **the cache reintroduces determinism at this layer.** An adversary who sends the same payload twice receives a byte-identical response from the cache on the second request, and receives it in cache-hit rather than model time. Repeating a probe a handful of times reveals both the caching behaviour and, through the timing shift, the tier boundary. Our diversity measurement used distinct payloads throughout and therefore never exercised this path. This is an evaluation blind spot, not merely a system limitation.

### 7.4 Layer 4: semantic and cross-session consistency

The most demanding fingerprinting attack is a human intruder checking whether the decoy's account of itself is internally coherent: whether a file written in one command is present in the next listing, whether the process table is consistent with the uptime, whether the database schema returned by two different queries agrees. Our session-history prompting gives the model recent context, but nothing enforces consistency, and no metric we report measures it.

This layer is where the multi-stage scenario evaluation of Section 12.3 would produce its most valuable results, and it is where we expect the system to be weakest against a determined human adversary.

### 7.5 Summary

**TABLE III. Fingerprinting layers and coverage.**

| Layer | Attack | Our defence | Evaluated? |
|---|---|---|---|
| 1. Transport | Protocol-library deviation [5] | None specific | No |
| 2. Timing | Tier-boundary latency ratio | None currently | Quantified here; not mitigated |
| 3. Content | Response-set enumeration | Generative synthesis, 0.64 to 0.99 uniqueness | Yes |
| 4. Semantic | Cross-command consistency | Session-history prompting | No |

Stating this honestly weakens the paper's headline claim and strengthens its usefulness. A reader deploying this framework should understand that high response diversity buys resistance to one specific and common class of automated fingerprinting, and that two other layers remain open.

---

## 8. Security Analysis of the Generative Response Layer

Introducing a language model into the response path creates risks that a static honeypot does not have. Reviewers asked for these to be identified. We group them by what the adversary gains.

### 8.1 Prompt injection against the decoy

Attacker input is passed directly into the model's context. An adversary who suspects a generative honeypot can attempt to override the system persona: instructing the model to ignore prior instructions, to state what it is, or to output its own system prompt. Success is deception-fatal, since it converts a suspicion into a confirmation.

Our AI-API decoy is the acute case, because it *advertises* itself as a model-serving endpoint, so prompt-injection payloads arrive as legitimate-looking traffic and the persona boundary is the only thing separating a convincing emulation from a genuine disclosure. Our corpus contains 136 API payloads including prompt-injection and jailbreak strings, and the decoy's low realism scores indicate it handled many of them by falling back to generic error text. Falling back to a generic error is a poor deception but a safe failure. We did not systematically measure persona-escape rate, that is, the fraction of injection payloads that caused the model to break character explicitly. This is a specific and easily run experiment that we should have included, and it is specified in Section 12.6.

Mitigations we apply are output filtering for known break-character markers, and keeping no secret in the system prompt whose disclosure would matter. The second is the more robust: the prompt should be written on the assumption that an adversary will eventually read it.

### 8.2 Cost exhaustion through forced cache misses

The tiered design controls cost by absorbing repeated traffic in the cache. An adversary who appends a unique nonce to every request defeats the cache entirely and forces a model call per request, converting the honeypot into a metered expense under adversary control.

We know this attack works because our own benchmark harness performs it. The nonce technique described in Section 5.3, introduced to obtain honest concurrency measurements, is precisely the cost-exhaustion attack. An adversary sending requests at the system's saturated capacity of roughly 1.6 requests/s sustains approximately 138,000 model calls per day. Section 9 puts a figure on what that costs.

This is a denial-of-wallet rather than a denial-of-service condition, and the standard mitigations apply: a per-source and global rate limit on escalation to the model tier, a daily spend cap after which the system degrades to static responses, and anomaly detection on the cache-miss ratio, since a legitimate scanner produces many cache hits while this attack produces none. A sustained cache-miss ratio near 1.0 from a single source is a strong signal of a deliberate adversary and is worth surfacing on the dashboard as a threat indicator in its own right. None of these controls is implemented in the current build.

### 8.3 Injection into the operator console

The dashboard renders attacker-supplied payloads and model-generated responses. Both are adversary-influenced text displayed in a privileged operator context. If rendering is not correctly escaped, an attacker can achieve stored cross-site scripting against the defender's own console, which inverts the deception entirely: the decoy becomes the delivery vehicle for an attack on the operator.

The model path makes this worse rather than better, because the response is not drawn from a set the developer wrote and reviewed. It is generated at request time and can contain arbitrary markup. Treating model output as untrusted input to the dashboard, with strict escaping and a content-security policy, is a requirement rather than a hardening measure. We flag this as a design obligation for anyone deploying a generative honeypot with a live operator view.

### 8.4 Generation of genuinely harmful content

Asked to emulate a compromised host, a model may produce functional exploit code, working command sequences, or plausible credentials. Two risks follow. The decoy may supply an attacker with material of real operational value, and the operator may mistake fabricated content for captured intelligence. The second is the more insidious: a hallucinated internal hostname or credential in the log looks exactly like a real one, and downstream analysis has no way to tell them apart.

The mitigation is provenance. Every record should carry a field recording which tier produced the response, so that model-generated content is distinguishable from static content at analysis time and never enters threat intelligence as though it were observed rather than synthesised. Our records identify the responding service but do not currently record the tier. Adding this field is a small change with a large effect on the evidential quality of the archive, and we recommend it.

### 8.5 Integrity is not veracity

The blockchain anchor proves that a record has not been altered since it was committed. It does not prove that the record's contents are true. This distinction is easy to blur in a paper that discusses forensic evidence and cryptographic commitment in the same breath, and it matters in a system where part of every record is machine-generated fiction.

Stated precisely, our anchoring establishes that the payload the attacker sent and the response the decoy returned were recorded as shown at the time of capture and have not been modified since. It establishes nothing about whether the response described a real system state, because the response was synthesised. For evidentiary use, the attacker's input is the probative part of the record, and its integrity is exactly what the anchoring protects. The synthesised response is context. Section 8.4's provenance field is what allows a court or an analyst to keep the two apart.

---

## 9. Cost Analysis

Reviewers asked for more discussion of cost. The relevant quantity is cost per unit of collected telemetry, and it depends on one parameter we did not measure.

### 9.1 Cost model

Let *h* be the fraction of requests absorbed by the static fast-path and the cache, so that (1 − *h*) reach the model. Let *c* be the price per model call. Cost per 1,000 intercepted interactions is

> Cost = 1,000 × (1 − *h*) × *c*

The measured inputs are as follows. Mean dynamic response length is 13.8 words, roughly 19 output tokens. Input consists of the service persona and recent session history, which in our deployment is on the order of a few hundred tokens. A single call is therefore small by contemporary standards, on the order of a few hundred input tokens and twenty output tokens. At commodity hosted pricing for an 8B-class instruction model, per-call cost is a small fraction of a US cent, and the dominant cost term at realistic volumes is not inference but the operator's time.

### 9.2 The parameter we did not measure

We do not report a value for *h*. The original manuscript asserted that approximately 80% of traffic is routine. That figure was not measured by our harness and we withdraw it. Our evaluation drove the system with 2,500 distinct payloads specifically to force model calls, so it establishes an upper bound on model usage rather than a representative hit rate. A deployment facing real Internet background traffic, which is dominated by repeated scanner probes, would see *h* far higher, but we have not measured it and will not estimate it.

Instrumenting the tier counters and reporting *h* from a period of live exposure is straightforward and is the single highest-value measurement missing from the cost picture. It is specified in Section 12.7.

### 9.3 Cost under adversarial conditions

The benign case is not the binding constraint. Section 8.2 established that an adversary can force *h* to zero. At the measured saturated throughput of 1.6 requests/s, sustained for 24 hours, an adversary generates approximately 138,000 model calls. This is the number that determines the operating budget of an exposed deployment, and it is entirely under adversary control unless a spend cap is enforced.

The practical consequence is that a generative honeypot must be deployed with a hard cost ceiling and a defined degradation mode. The degradation is not a failure state. Falling back to static responses under attack yields a honeypot no worse than a conventional one, while capping the loss. We regard this as a necessary architectural feature rather than an operational detail, and its absence from the current build is a limitation.

### 9.4 Cost comparison with the alternatives

A static honeypot has effectively zero marginal response cost and the fingerprintability described in Section 2.1. A high-interaction honeypot running real services has no inference cost but substantial hosting cost, plus the operational risk of exposing genuinely exploitable software. The generative approach sits between them: marginal cost per novel interaction, negligible cost per routine interaction, and no exploitable real service. The blockchain component adds negligible cost in our development-chain deployment, though a public-chain deployment would require batching commitments through a Merkle root rather than anchoring each record individually.

---

## 10. Comparison with Prior Systems

We compare our framework with the most directly relevant published honeypot systems on two levels: the numbers each system reported in its own paper, and the structural properties that distinguish the approaches.

A critical caveat governs the quantitative comparison. Each prior figure is reproduced exactly as published, and the systems were measured under different conditions, with different metrics, on different hardware and models. **We do not claim a controlled head-to-head.** That would require re-implementing and re-benchmarking every baseline on one testbed, which we did not do. What the numbers support is a like-for-like reading of the specific quantities defined the same way across systems, most usefully per-request latency and the presence or absence of an integrity guarantee.

### 10.1 The core trade-off every LLM honeypot faces

The published literature converges on one dominant finding: LLM-backed honeypots buy realism at the cost of latency, and the two pull against each other. A benchmarking study of generative SSH honeypots reports that small models answer in under half a second but hallucinate at rates above 20%, while mid-size models that achieve good fidelity incur three- to four-second response times, and even the largest models settle around a two-second delay that the authors judge too long to be considered realistic [15]. HoneyLLM reports a mean of 1.88 s per command against 0.138 s for the static Cowrie baseline it compares to [13].

This is precisely the trade-off our tiered design targets. Rather than pay the LLM latency on every request, we pay it only on the novel tail. Our fast-path answers routine enumeration in 0.8 ms, three to four orders of magnitude below any of the generative systems above and comparable to a static honeypot, while our dynamic path's 2.33 s mean sits in the same band as the published mid-size-model figures. We do not beat the generative systems on raw novel-request latency, and no system using a comparable hosted model could. Our architecture avoids paying that latency on routine traffic, subject to the timing-fingerprint cost quantified in Section 7.2.

### 10.2 Realism relative to the state of the art

The strongest published realism result is ShelLM's. In a human-subject study, twelve security researchers judged 226 commands and the system reached an overall accuracy of 0.92 and a true-negative rate of 0.90 [11]. This is a human-subject result and is a stronger form of evidence than our automated LLM-judge score.

Our comparable figure is a mean LM-judge realism of 4.37/5, with 25 of 30 sampled responses rated 5/5. We do not claim parity with ShelLM's human study on the strength of an automated judge, for the reasons given in Sections 5.4 and 12.1. Two narrower points are defensible: our best-performing decoys reach output-diversity levels consistent with strong realism, and we do so across five protocols rather than one. ShelLM, HoneyLLM, and the McKee and Noever chatbot honeypot are all single-surface, and none anchors its logs for integrity.

### 10.3 What a controlled comparison would require

Reviewers asked for comparative evaluation against other modern honeypots. We agree this is the right next step and set out what it demands, since the phrase covers a wide range of study designs.

A defensible controlled comparison requires deploying Cowrie as the static baseline and at least one open generative honeypot, ShelLM being the obvious choice as its code is public, on the same host as our SSH decoy; driving all three with the identical payload corpus; and measuring latency, diversity, and realism with the same instruments on the same day. This is a substantial engineering effort, on the order of several weeks, dominated by making three heterogeneous systems accept the same driver and emit comparable logs. It is the most valuable single experiment remaining and would convert Section 10's published-numbers comparison into a measured one. We note it is restricted to the SSH surface, since no prior system implements the other four.

### 10.4 Structural comparison

**TABLE IV. Structural comparison.**

| System | Surfaces | Response mechanism | Routine latency | Log integrity |
|---|---|---|---|---|
| Cowrie / Kippo [3] | 1 (SSH) | Static table | Microseconds | None |
| ShelLM [11] | 1 (shell) | Generative | Seconds | None |
| HoneyLLM [13] | 1 (shell) | Generative + filter | 1.88 s mean | None |
| HoneyGPT [12] | 1 (shell) | Generative + state mgr | Seconds | None |
| Blockchain audit logs [21] | n/a | n/a | n/a | On-chain |
| **This work** | **5** | **Tiered: static, cache, generative** | **0.8 ms** | **On-chain per record** |

Classical static honeypots achieve microsecond latency precisely because they never generate, the same property that let a single-packet probe fingerprint them at scale. The single-surface LLM honeypots share our generative advantage but on one protocol only, and none addresses log integrity. Blockchain secure-logging systems provide integrity but are not deception sensors. To our knowledge the combination we report, a five-surface generative deception layer whose every record is tamper-evident through on-chain anchoring, with a tiered path that keeps routine latency at static-honeypot levels, is not present in any single prior system.

We are careful about the word that describes this. The framework does not dominate prior systems on any individual metric. It occupies a combination of properties no prior system occupies, at the cost of the timing signature Section 7.2 identifies.

---

## 11. Engineering Gaps Identified and Resolved

A working deception sensor is a set of defects discovered and fixed during construction and measurement. We document three concrete gaps because two of them are the kind of error that silently corrupts an evaluation if left unstated.

### 11.1 Language-model latency made the naive design non-viable

Our first end-to-end build routed essentially every SSH command to the language model, giving a mean dynamic-path latency of about 4.0 s with a long tail. We measured the two dominant costs rather than guessing. The engine opened a fresh TCP and TLS connection to the hosted inference API on every request, and the generation-length cap was far larger than the short outputs a shell or error message needs.

We introduced the three-tier response path, replaced the per-request connection with a single pooled client reused for the process lifetime, and reduced the generation-length cap to a value measured to preserve realistic multi-line output. These changes reduced mean dynamic-path latency from approximately 4.0 s to approximately 1.35 s on the same payload set, measured across two independent runs. We also tested whether swapping in a smaller model would help and found it did not: on the hosted API, provider routing dominated raw parameter count.

The same per-request-connection anti-pattern existed one hop earlier in all five decoys, each of which opened a new HTTP session for every log write and every engine call. Applying the identical pooling fix reduced decoy-layer latency by roughly 30% to 41% for four of the five services and, as importantly, tightened variance by half to two-thirds. A warm reused connection is far less exposed to an occasional slow handshake than a fresh one.

**TABLE V. Connection-pooling effect, measured before and after.**

| Decoy | Endpoint | Before (mean) | After (mean) | Change |
|---|---|---|---|---|
| oracle-ai | `GET /api/models` | 6.15 ms (σ 3.89) | 4.28 ms (σ 0.70) | −30.4% |
| vault-sql | `GET /health` | 0.69 ms (σ 1.94) | 0.41 ms (σ 0.44) | −41.4% |
| ledger-trap | `POST /` (`eth_accounts`) | 5.96 ms (σ 2.43) | 4.20 ms (σ 0.75) | −29.5% |
| forge-ci | `GET /api/json` | 6.95 ms (σ 3.13) | 6.71 ms (σ 3.02) | −3.4% |
| shadow-shell | SSH `whoami` | 7.91 ms (σ 9.94) | 4.64 ms (σ 6.55) | −41.3% |

The `forge-ci` endpoint shows almost no change because it routes through the engine regardless of decoy-layer pooling; its floor is set by the cache lookup.

We note that the 1.35 s figure and the 2.33 s figure reported in Section 6.1 come from different runs against different corpora, the latter being the full 2,500-payload evaluation with a higher proportion of long-output payloads. They are not directly comparable, and we report both rather than presenting the more favourable one.

### 11.2 The benchmark harness was measuring the cache, not the model

An early version of our evaluation harness reported concurrent throughput on the order of hundreds of requests per second. This was a measurement artefact. The concurrent-throughput test reused payloads already sent during the diversity pass, so every concurrent request was a cache hit returning in milliseconds. The harness was faithfully measuring cache-hit latency and mislabelling it as language-model throughput.

This is a dangerous class of error precisely because it produces a flattering number. Left unexamined it would have overstated concurrent capacity by two to three orders of magnitude. We appended a fresh unique nonce to each concurrent request, guaranteeing a cache miss and a genuine model call. The corrected figure in Section 6.2 is far lower.

We keep this episode in the paper deliberately. Silently benchmarking a cache instead of the system under test is a common and easily missed evaluation mistake. The same nonce technique, as Section 8.2 notes, is also an attack.

### 11.3 The intent classifier left most traffic unlabelled

Under realistic mixed traffic, an early version of the rule-based classifier labelled roughly three-quarters of all events as unknown. Inspection showed the rules were too narrow rather than the traffic unclassifiable. They missed the connection-probe records the proxy emits, standard first-contact shell enumeration, the abusive Ethereum RPC methods used to drain wallets, brute-force login attempts, and compact injection strings that did not match the original keyword shapes.

A sensor whose dominant output category is unknown provides little actionable intelligence. The gap was in the labelling, not the data. We expanded the rule set along the categories the traffic actually contained, adding a dedicated crypto-theft category for wallet-draining RPC methods, broadening reconnaissance to include connection probes and shell enumeration, folding brute-force logins into privilege escalation, and widening the injection and remote-execution patterns. Re-running the expanded classifier over a held sample of 1,000 real captured payloads reduced the unknown fraction from roughly 75% to effectively zero, distributing events across eight categories.

We are careful about what this shows. It demonstrates coverage, that the rules fire on the traffic, and not correctness, that they fire on the *right* traffic. Coverage without a ground-truth comparison cannot distinguish a well-tuned rule set from an over-broad one. Section 12.2 specifies the validation study.

---

## 12. Validation Roadmap

Several reviewer comments ask for evidence the present evaluation does not contain. Rather than qualify each claim in place, we set out here exactly what each outstanding question requires, so that the boundary between what we measured and what remains open is unambiguous.

### 12.1 Human-subject realism study

The LM judge locates gross failures. It cannot certify indistinguishability. A defensible claim requires security practitioners interacting with both the decoys and matched real services under blinded conditions and attempting to tell them apart.

The protocol we propose follows ShelLM's [11] in structure. Recruit at least twenty participants with professional security experience. Each is given interactive sessions against a randomised mix of real services and decoys across all five protocols, with the assignment concealed. Participants issue commands freely for a fixed budget of interactions and, after each session, judge whether the endpoint was real and state their confidence. The outcome measure is detection rate with confidence intervals, reported per protocol rather than pooled, since our own data predicts the AI-API decoy will differ sharply from the other four. Twenty participants across five protocols is the minimum for per-protocol resolution; ShelLM used twelve for a single protocol.

### 12.2 Intent-classifier precision and recall

Section 11.3 reports coverage. Validation requires ground truth. The study: draw a stratified random sample of at least 500 captured payloads across all eight categories and both high- and low-frequency rules; have two annotators independently label each with the correct intent, blind to the classifier's output; measure inter-annotator agreement and adjudicate disagreements; then report per-category precision, recall, and F1 against the adjudicated labels. This will identify over-broad rules, which coverage measurement cannot, and gives the auditability claim in Section 4.4 quantitative support.

### 12.3 Multi-stage attack scenarios

Section 5.2 established that our corpus is single-request. The scenario evaluation requires constructing at least ten multi-stage attack chains, each a realistic ordered sequence of eight to fifteen interactions drawn from a documented intrusion pattern, for example initial SSH access, then enumeration, then credential access, then lateral-movement attempts against the SQL and CI endpoints. Each chain is replayed against the framework as a single session.

The metric of interest is not diversity but **consistency**: whether the decoy's later responses contradict its earlier ones. Scoring requires manual review or a judge model given the full session transcript rather than isolated pairs. This experiment addresses fingerprinting layer 4 and would produce, we expect, the least flattering results of anything proposed here, which is why it matters.

### 12.4 Load sweep

Section 6.2 measured two concurrency levels and inferred saturation at an effective parallelism of 3.5. A scaling curve requires sweeping concurrency across at least c ∈ {1, 5, 10, 25, 50, 100}, measuring throughput and latency at each point under both burst and sustained load, and repeating the sweep with the inference provider's rate limit raised to separate framework limits from provider limits. Our environment permits this experiment; it was not run.

### 12.5 Timing-mitigation evaluation

Section 7.2 quantified the timing side-channel but did not mitigate it. The experiment: implement calibrated jitter on the fast-path, then measure the number of probe pairs an adversary needs to distinguish the two tiers at a given confidence, as a function of injected jitter and of the throughput sacrificed. This turns a qualitative mitigation discussion into a defensible trade-off curve.

### 12.6 Persona-escape rate

Section 8.1 identified prompt injection against the decoy as an unmeasured risk. The experiment is simple: run the 136 API prompt-injection payloads plus a set of injection strings targeted at the other four decoys, and have an independent judge classify each response as in-character, generic-fallback, or explicit break-character. The break-character rate per service is the metric. We regard this as the single cheapest missing experiment on this list.

### 12.7 Fast-path hit rate under live traffic

Section 9.2 withdrew the unmeasured 80% figure. Obtaining a real value requires instrumenting the tier counters and exposing the deployment to live Internet background traffic for a defined period, then reporting *h* with its variance across days. This is the parameter that determines whether the cost model in Section 9.1 evaluates to negligible or significant.

---

## 13. Discussion and Limitations

**Where the trade-off is favourable.** The system's cost model suits its threat model. The metered, multi-second model path is spent only on novel requests, which are exactly the inputs a static table cannot handle and which a human intruder generates at human speed. For interactive intrusion, second-scale latency on novel commands is within the range of a real congested server. For high-rate scanning, the fast-path and cache carry the load.

**Where it is weakest.** Three weaknesses stand out, in order of severity.

The timing side-channel of Section 7.2 is the most serious, because it is cheap to exploit, our own data quantifies it, and it follows from the architecture rather than from an implementation flaw. Any tiered generative honeypot has this property.

The AI-API decoy lags the other four on diversity and draws most of the low realism ratings. The likely cause is prompt design: emulating an internal AI API is under-constrained compared with emulating a shell or a SQL engine, whose output formats are rigid, so the model more often falls back on generic error text. This points at a concrete fix, a tightly specified output contract for that decoy, rather than a limitation of the approach.

Transport-layer fidelity (Section 7.1) is unaudited across four of five decoys, and is the layer at which the best-documented honeypot fingerprinting attack in the literature operates.

**Honesty of the reported numbers.** We report the corrected concurrent-throughput figure, the per-service realism disparity, and the withdrawal of the unmeasured fast-path hit rate rather than the aggregate alone. A composite realism headline would obscure which decoy is weak. A single omitted benchmark bug would have inflated concurrent throughput by orders of magnitude. For a system whose purpose is trustworthy evidence collection, transparent reporting is part of the contribution.

**Threats to validity.** The realism metric is an automated proxy on a sample of 30. The evaluation is a single run on one response model and one judge model. The diversity metric rewards uniqueness, which is necessary but not sufficient for realism, since unique-but-wrong output scores well on diversity and poorly with the judge, which is exactly the AI-API decoy's profile. The blockchain evaluation runs on a development chain that mines instantly, so it demonstrates the anchoring pipeline and the tamper-detection property but not public-chain confirmation latency or cost.

---

## 14. Conclusion

We presented a multi-protocol cyber-deception framework that couples a tiered, language-model-backed response engine with blockchain-anchored forensic logging across five heterogeneous decoys. The tiered design answers common traffic at static-honeypot speed, 0.8 ms, and calls the model only for the novel tail at 2.33 s. On-chain anchoring makes the audit trail tamper-evident independently of the logging host, which we verify directly. On a corpus of 2,500 real attack payloads the system delivers response uniqueness between 0.64 and 0.992 across five decoys and a mean judged realism of 4.37/5.

This revision adds four analyses the original lacked. Fingerprinting resistance separates into four layers, and response diversity, the metric this literature reports, addresses one of them; our own latency measurements expose a timing side-channel that a single pair of probes can exploit. The generative response layer introduces security risks a static honeypot does not have, of which forced cache-miss cost exhaustion and injection into the operator console are the most actionable. Operating cost is a function of a fast-path hit rate we did not measure, and we withdraw the estimate the original manuscript made. Concurrency scaling saturates at an effective parallelism of 3.5, and the measurements locate that ceiling at the inference provider rather than in the framework.

The most important limitation remains that realism is measured by proxy. Section 12 sets out seven specific experiments, in order of value, that would convert the present evidence into stronger claims. We report the per-service disparity, the architectural side-channel, and the withdrawn estimate alongside the favourable numbers because a system built to produce trustworthy evidence should be described the same way.

---

## References

[1] L. Spitzner, *Honeypots: Tracking Hackers.* Boston, MA, USA: Addison-Wesley, 2002.

[2] N. Provos, "A virtual honeypot framework," in *Proc. 13th USENIX Security Symp.*, 2004.

[3] M. Oosterhof, "Cowrie SSH/Telnet honeypot," 2015. [Online]. Available: https://github.com/cowrie/cowrie

[4] The Honeynet Project, "Dionaea: a malware-capturing honeypot," 2016. [Online]. Available: https://github.com/DinoTools/dionaea

[5] A. Vetterl and R. Clayton, "Bitter Harvest: Systematically fingerprinting low- and medium-interaction honeypots at Internet scale," in *Proc. 12th USENIX Workshop on Offensive Technologies (WOOT)*, 2018.

[6] X. Han, N. Kheir, and D. Balzarotti, "Deception techniques in computer security: A research perspective," *ACM Comput. Surveys*, vol. 51, no. 4, pp. 1–36, 2018.

[7] B. M. Bowen, S. Hershkop, A. D. Keromytis, and S. J. Stolfo, "Baiting inside attackers using decoy documents," in *Proc. Int. Conf. Security and Privacy in Communication Systems (SecureComm)*, 2009.

[8] A. Juels and R. L. Rivest, "Honeywords: Making password-cracking detectable," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2013.

[9] A. Javadpour, F. Ja'fari, T. Taleb, M. Shojafar, and C. Benzaïd, "A comprehensive survey on cyber deception techniques to improve honeypot performance," *Computers & Security*, vol. 140, 2024, Art. no. 103792.

[10] F. McKee and D. Noever, "Chatbots in a honeypot world," *arXiv:2301.03771*, 2023.

[11] M. Sladić, V. Valeros, C. Catania, and S. Garcia, "LLM in the Shell: Generative honeypots," in *Proc. IEEE European Symp. Security and Privacy Workshops (EuroS&PW)*, 2024, doi: 10.1109/EuroSPW61312.2024.00054.

[12] Z. Wang et al., "HoneyGPT: Breaking the trilemma in terminal honeypots with large language model," *arXiv:2406.01882*, 2024.

[13] W. Fan, Z. Yang, Y. Liu, L. Qin, and J. Liu, "HoneyLLM: A large language model-powered medium-interaction honeypot," in *Proc. Int. Conf. Information and Communications Security (ICICS)*, 2024, pp. 253–272.

[14] Weber et al., "Don't Stop Believin': A unified evaluation approach for LLM honeypots," in *Proc. IEEE Conf.*, 2024.

[15] R. A. Bridges et al., "SoK: Honeypots & LLMs, more than the sum of their parts?," *arXiv:2510.25939*, 2025.

[16] M. Boffa, G. Milan, L. Vassio, I. Drago, M. Mellia, and Z. Ben Houidi, "LogPrécis: Unleashing language models for automated malicious log analysis," *Computers & Security*, vol. 141, 2024.

[17] B. Schneier and J. Kelsey, "Secure audit logs to support computer forensics," *ACM Trans. Inf. Syst. Secur.*, vol. 2, no. 2, pp. 159–176, 1999.

[18] D. Ma and G. Tsudik, "A new approach to secure logging," *ACM Trans. Storage*, vol. 5, no. 1, pp. 1–21, 2009.

[19] S. Nakamoto, "Bitcoin: A peer-to-peer electronic cash system," 2008. [Online]. Available: https://bitcoin.org/bitcoin.pdf

[20] G. Wood, "Ethereum: A secure decentralised generalised transaction ledger," *Ethereum Project Yellow Paper*, 2014.

[21] A. Sutton and R. Samavi, "Blockchain enabled privacy audit logs," in *Proc. Int. Semantic Web Conf. (ISWC)*, 2017.

[22] L. Zheng et al., "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2023.

[23] MITRE, "MITRE ATT&CK: Adversarial tactics, techniques, and common knowledge," 2015. [Online]. Available: https://attack.mitre.org

[24] D. Miessler and J. Haddix, "SecLists: A collection of security testing lists," 2012. [Online]. Available: https://github.com/danielmiessler/SecLists

[25] Swisskyrepo, "PayloadsAllTheThings: A list of useful payloads and bypasses for web application security," 2016. [Online]. Available: https://github.com/swisskyrepo/PayloadsAllTheThings
