# ISAMC 2026 — Speaker Guide

Deck: `ISAMC_Presentation.pptx` (26 slides, ~15 min). Every slide's notes are also inside the .pptx (Presenter View).

Timing guide: slides 1–7 ≈ 4 min · 8–15 ≈ 5 min · 16–21 ≈ 4 min · 22–25 ≈ 2 min · Q&A.

---

## Slide 1 — A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging

Good morning everyone. I am Sisir Reddy Nellore from Amrita Vishwa Vidyapeetham, Coimbatore, and I will present our paper
"A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging".

In one sentence: we built a honeypot — a fake server that exists only to be attacked — where an AI language model writes the replies
so it looks real, and where every attack record is fingerprinted onto a blockchain so nobody, not even an attacker who breaks into the honeypot,
can change the evidence without being caught.

The talk is about 15 minutes: the problem, our design, how we tested it, what worked, and — honestly — what did not.

**Terms on this slide**

• Cyber deception: Defensive technique: plant fake systems/data so attackers waste time on decoys and reveal themselves.
• Language model (LM/LLM): An AI model (like ChatGPT / Llama) that generates text. We use it to generate fake server output.
• Forensic logging: Recording attack evidence in a way that can later be used to investigate or prove what happened.
• Blockchain-anchored: A short fingerprint (hash) of each record is written onto a blockchain, which cannot be rewritten.


## Slide 2 — What this talk covers

Here is the roadmap. I will start with why existing honeypots fail, then our two-part idea, then walk through the architecture piece by piece.
After that, the evaluation on 2,500 real attack strings, and I will spend real time on the honest findings — including one decoy that
underperforms and three bugs we caught in our own benchmark — because for a system whose job is trustworthy evidence, transparent reporting is part of the contribution.


## Slide 3 — First, what is a honeypot?

Before the problem, one minute on what a honeypot is, for anyone outside security.
A honeypot is a decoy server deployed on purpose. It has no legitimate users, so any connection to it is suspicious by definition.
It silently records everything the attacker does, so defenders learn who is attacking and how.

The popular low-cost honeypots — Cowrie, Kippo — do not run a real operating system. They fake it using a lookup table:
if the attacker types "ls" reply with this string, if "whoami" reply "root". That is cheap and safe.
But the table is finite. Type something not in the table and the honeypot answers wrongly, or not at all. That is the crack we are going to widen on the next slide.

**Terms on this slide**

• Low / medium-interaction honeypot: Emulates a service with scripted logic instead of running the real thing. Cheap and safe but shallow.
• High-interaction honeypot: A real full OS used as bait. Very realistic but expensive and dangerous if the attacker escapes.
• SSH: Secure Shell — the remote command-line login used to administer Linux servers; the most-attacked service on the Internet.
• Telemetry: The data/records collected by a sensor — here, attacker connections, commands and payloads.


## Slide 4 — Problem 1 — Static honeypots are easy to unmask

Problem one. Because the answer table is finite, an automated scanner only needs to send a handful of odd requests and observe that
the replies are drawn from a fixed set — or are identical across supposedly different hosts. It then concludes "decoy" and disengages.
This is not a matter of writing a bigger table: any finite static set can be enumerated.

This was demonstrated at Internet scale by Vetterl and Clayton in 2018: with a single packet they fingerprinted these honeypots
with an equal-error rate of 0.0183 and located 2,844 real Cowrie and Kippo instances in the wild.

So the requirement is a reply mechanism that is generative rather than tabular — something that can invent a plausible, consistent reply to a never-seen request.

**Terms on this slide**

• Fingerprinting: Identifying what software a remote machine runs from tiny behavioural quirks in its replies.
• Equal-error rate (EER): The error rate at the point where false positives equal false negatives; 0.0183 means ~1.8% error — a very accurate detector.
• Deterministic: Same input always gives exactly the same output — a tell-tale sign of a scripted decoy.
• Enumerable: Can be fully listed out. A finite table of answers can be discovered by trying inputs.


## Slide 5 — Problem 2 — The evidence lives on the machine being attacked

Problem two is separate and, we argue, equally important. A honeypot log that is just a file on the honeypot is only as trustworthy as that machine.
But the honeypot's entire job is to get attacked, so we must assume a capable attacker can compromise it — and then edit or delete the records of their own intrusion.

If we want to use that telemetry as evidence — in an incident report, or in court — the audit trail needs an integrity guarantee that holds
even when the logging machine itself is compromised. Note we ask for tamper-EVIDENCE, not tamper-proofing: we cannot stop an attacker from editing a file,
but we can make sure the edit is always detectable.

**Terms on this slide**

• Audit trail: The chronological record of events, kept for later review.
• Tamper-evident vs tamper-proof: Tamper-proof = cannot be changed. Tamper-evident = can be changed, but any change is detectable. We guarantee the latter.
• Compromised host: A machine the attacker has gained control of.


## Slide 6 — Our idea — fix both problems in one framework

Our idea addresses both problems together.
For realism, we replace the fixed table with a language model that is prompted to behave like the service — a shell, a database, and so on.
It can answer any request and keep the session consistent, so there is no finite set to enumerate. But — and this matters — we do not send every request to the model,
because that would be slow and expensive. We use a tiered path: static table first, cache second, model only for genuinely new input.

For integrity, every interaction is hashed with SHA-256 and the hash is written as a transaction on an Ethereum blockchain.
Later, anyone can re-hash the stored record and compare. If even one character was changed, the hash differs and the tampering is exposed.

The paper's three contributions are: the multi-protocol LM-backed deception layer, the blockchain-anchored logging, and an honest four-axis evaluation on real attack data.

**Terms on this slide**

• SHA-256: A cryptographic hash function: turns any data into a fixed 256-bit fingerprint. Changing one byte of input gives a completely different fingerprint, and it is infeasible to find two inputs with the same fingerprint.
• Ethereum: A public blockchain platform. We run a local (private) Ethereum node; we only store hashes on it, never the raw logs.
• Transaction (tx): A record written onto the blockchain; once mined into a block it is practically immutable.
• Multi-protocol: Covers several different network services / attack surfaces, not just SSH.


## Slide 7 — Threat model and design goals

We designed against two adversaries. The automated scanner is a bot: fast, non-interactive, sends a few standard probes and leaves. Field studies show the
overwhelming majority of honeypot traffic is this kind. It fingerprints by looking for deterministic or inconsistent replies. The interactive intruder is a human
who has reached a shell and explores at human speed with novel commands. The scanner stresses breadth and timing; the intruder stresses novel-input handling.
We additionally assume the honeypot host may be compromised, so integrity cannot rely on trusting it.

From that we derived six goals, G1 to G6, and — importantly — each maps to a specific measurement later in the talk, so you can check whether we met them.
We claim tamper-evidence, not confidentiality: we assume SHA-256 and the ledger are cryptographically sound.

**Terms on this slide**

• Threat model: A precise statement of what the attacker can do and what we assume; every security design must state one.
• Latency uniformity: If every reply takes exactly the same suspicious multi-second delay, timing alone reveals a decoy.


## Slide 8 — Part 2

Now the architecture. I will show the big picture first, then zoom into each component.


## Slide 9 — Architecture at a glance

This is Figure 1 from the paper. Everything runs as containers on an isolated bridge network.
Only two components are reachable from outside: the connection proxy, which fronts the decoys, and the monitoring dashboard.
The attacker connects to the proxy; the proxy forwards to the right decoy. The decoy asks the tiered response engine for a reply, which goes to the
hosted LM API only for novel requests. Every interaction is posted to the collector, which classifies intent, computes the SHA-256 hash, stores the full record in Redis,
anchors the hash on the Ethereum chain, and streams the event live to the dashboard.
Because decoys, engine, datastore and chain are internal-only, an attacker inside a decoy cannot reach the control plane.

**Terms on this slide**

• Containerised / bridge network: Each component runs in its own Docker container; a bridge network is a private virtual network between them.
• Proxy: A relay that accepts the connection and forwards it — here it also logs every connection before anything else happens.
• Redis: A fast in-memory key-value datastore; holds the full records and the response cache.
• Control plane: The management components (collector, datastore, chain) as opposed to the attacker-facing decoys.


## Slide 10 — The connection proxy and one interaction's journey

This is Figure 2 — the sequence for one interaction. A single asynchronous proxy listens on the five public ports and forwards each connection to the matching decoy.
The key design decision: it logs the source address and port before any decoy replies. So even a bare port scan that never completes a protocol handshake is captured.
It also gives us one choke point for connection telemetry and keeps the decoys off the public interface.
After the decoy replies, the collector does its five steps: classify the intent, hash, store, anchor the hash on-chain, and push the event to the live dashboard.

**Terms on this slide**

• Asynchronous: Handles many connections at once without blocking on any single one.
• Port: A numbered door on a server; each service listens on one (e.g. SSH on 22, PostgreSQL on 5432).
• Handshake: The initial exchange that sets up a protocol session. Scanners often connect and leave without completing it.


## Slide 11 — Five decoys — five modern attack surfaces

The five decoys were chosen to cover distinct, currently relevant attack surfaces.
The SSH shell is a real SSH server that accepts any credentials and presents a shell claiming to be a corporate Ubuntu database host.
PostgreSQL accepts SQL and returns plausible tables or realistic errors — bait for SQL injection.
The "internal AI API" is a chat/prediction service — bait for prompt injection and jailbreak attempts; this is a very new attack surface.
The Ethereum JSON-RPC node answers the exact methods attackers use to find and drain wallets on exposed nodes.
And Jenkins exposes the build/script endpoints that make up its documented attack surface.
Every prior generative honeypot in the literature — ShelLM, HoneyLLM, HoneyGPT — covers only a Linux shell.

**Terms on this slide**

• SQL injection: Inserting malicious SQL into an input so the database executes the attacker's query.
• Prompt injection / jailbreak: Crafting text to make an AI model ignore its instructions or reveal hidden data.
• XXE / SSRF: XML External Entity and Server-Side Request Forgery — web attacks that make a server read files or contact internal URLs.
• JSON-RPC: A simple remote-procedure-call protocol over JSON; Ethereum nodes expose it (methods like eth_accounts, personal_unlockAccount).
• CI/CD (Jenkins): Continuous Integration / Delivery — servers that build and deploy code; compromising one lets attackers poison the software supply chain.
• RCE / reverse shell: Remote Code Execution; a reverse shell is a connection from the victim back to the attacker giving them a command line.
• Privilege escalation: Going from a low-privilege account to admin/root.


## Slide 12 — The three-tier response path

This is the heart of the realism-versus-cost trade-off. An LM call takes seconds; a real service answers routine commands in microseconds.
If every request went to the model, the honeypot would be slow, expensive, AND the uniform multi-second delay would itself be a fingerprint.

So the engine escalates only when necessary. Tier one: the most common enumeration commands — directory listing, identity, network config — come from a fixed table
in under a millisecond. The realism cost is low because those commands genuinely have stable outputs. Tier two: an in-memory cache keyed on request plus recent session context,
so a repeated probe is free. Tier three: only truly novel requests reach the model — an instruction-tuned Llama-3.1-8B behind a hosted inference API, so no local GPU is needed.
The system prompt tells it to emit only the raw output stream of the service: no explanation, no markdown, never admit it is a model. Recent session history is included for consistency.

This mirrors the canonical architecture that Bridges et al.'s 2025 systematisation distilled from sixteen LLM honeypots — we arrived at it independently.

**Terms on this slide**

• Llama-3.1-8B: Meta's open-weight language model with 8 billion parameters; 'instruction-tuned' means trained to follow instructions.
• Hosted inference API: The model runs on a cloud provider; we call it over the network instead of running it on our own GPU.
• System persona / system prompt: Hidden instructions telling the model what role to play.
• Cache miss / hit: Miss = not found in cache, must compute; hit = found, return instantly.
• Breaking character: When the LM outputs a refusal or 'As an AI model…' — a deception-fatal tell.


## Slide 13 — Intent classification — labelling what the attacker wants

Every captured interaction is labelled with an attack intent from eight categories: SQL injection, prompt injection, crypto theft — the wallet-draining RPC methods — cryptomining,
reverse shell / remote code execution, privilege escalation including brute-force logins, supply-chain / CI-CD abuse, and reconnaissance. Anything unmatched is 'unknown'.

We deliberately used a rule-based classifier rather than a trained model. For a forensic sensor, we value that every decision is explainable and auditable — you can point
to the rule that fired — and that it adds no latency and needs no training data. We consider that worth more than the marginal recall a learned model might add.
Important distinction: the LM writes replies; it does not classify. Classification is deterministic.

**Terms on this slide**

• Cryptomining: Hijacking a machine's CPU to mine cryptocurrency for the attacker.
• Reconnaissance: Scanning, service enumeration, and the first commands an intruder runs to look around.
• Auditable / explainable: A human can inspect and justify why a label was assigned — essential if the label appears in an investigation.
• Recall: Fraction of true cases the classifier catches.


## Slide 14 — Blockchain-anchored logging — making the evidence tamper-evident

Here is the integrity mechanism, Figure 4. When a record reaches the collector, it is serialised in a deterministic way — same record, same bytes every time — hashed with SHA-256,
and the 32-byte digest is sent as a transaction to a local Ethereum chain. The full record stays in our datastore; only the digest goes on-chain.

Verification is trivial and can be done by any party at any time: fetch the stored record, re-hash it, compare with the committed value. If they match, the record is intact.
If an attacker who compromised the honeypot edited even one field, the hash changes and no longer matches — and they cannot fix that, because the on-chain digest cannot be rewritten.
This is a well-established pattern from blockchain audit-log research; our contribution is applying it to honeypot telemetry, where the logging host is by design the thing under attack,
and coupling it with a generative multi-protocol honeypot — which, to our knowledge, has not been reported before.

**Terms on this slide**

• Digest: Another word for the hash output — the fixed-size fingerprint.
• Deterministic serialisation: Converting the record to bytes in a fixed order so identical records always hash identically.
• Immutable / append-only: Blocks can only be added to a blockchain, never edited; rewriting history would require re-mining every later block.
• Local Ethereum chain: A private Ethereum node (Ganache-style) under our control, used as an integrity anchor; the same design works on a public chain.


## Slide 15 — Real-time operator dashboard

The dashboard is the operator's window into the sensor. It shows intercepted-attack counts, unique attacker IPs, per-intent and per-service breakdowns, and — for each event —
the payload, the decoy's response, its SHA-256 digest and whether it is anchored on-chain. There is also a per-attacker drill-down that reconstructs which services an address touched,
a severity-weighted threat rating, its intent mix, and a timeline of the actual payloads it sent. The paper's Figure 5 shows this over 6,742 intercepted events, and this is also the
surface we use for the live integrity demonstration.

**Terms on this slide**

• Threat rating: A score combining how many and how severe the attacker's intents are.


## Slide 16 — Part 3

Now the evaluation. One methodological point up front: we report four axes separately rather than a single composite score, because they pull against each other and the trade-offs are the point.


## Slide 17 — Evaluation methodology

The corpus is 2,500 attack payloads from public, permissively licensed security corpora — SecLists and PayloadsAllTheThings — plus documented real-world attack shapes.
Every entry keeps a provenance field. Nothing is model-generated or hand-invented, and there is no padding: each service is capped at the number of distinct real payloads available,
which is why Web3 and CI/CD are small — their real attack surface is a small finite set of RPC methods and exploit endpoints, not an open space of injection strings.

Four axes. Latency and sequential throughput, static versus LM path. Concurrent throughput with ten simultaneous sessions, where each request carries a unique nonce to force a cache miss —
I will come back to why that matters. Response diversity: the uniqueness ratio, distinct outputs over total, which directly measures how clusterable the replies are. And realism,
judged by an independent, larger model — Llama-3.1-70B — on a one-to-five scale, with one meaning an obvious tell.
Separately, we test the tamper-evidence claim directly. And we are explicit that the LM judge is a proxy, not a human study — I will return to that.

**Terms on this slide**

• SecLists / PayloadsAllTheThings: Two widely used open-source collections of real attack strings used by penetration testers.
• Provenance: Where each payload came from — recorded so the dataset is auditable.
• Nonce: A 'number used once' appended to a request so it is guaranteed unique.
• Uniqueness ratio: distinct replies / total replies. 1.0 = every reply different; 0 = all identical.
• LLM-as-judge: Using a second AI model to grade another model's output — cheap but imperfect (Zheng et al., NeurIPS 2023).
• Standard deviation: How spread out the measurements are.


## Slide 18 — Result 1 — Latency and throughput

Result one. The static fast-path answers in a mean of 0.80 milliseconds — around 1,250 requests per second. The dynamic LM path answers in a mean of 2.33 seconds, median 1.73,
standard deviation 1.40 — so roughly four orders of magnitude apart. Note the charts are on a log scale.
This gap is exactly why the tiered design exists: routing routine traffic to the fast-path is what makes an LM honeypot viable at all.

Under ten simultaneous sessions — with cache misses forced — the system sustains 1.61 requests per second at 2.19 seconds mean latency.
The dynamic latency is dominated by the network round-trip to the hosted model, not our code.
For the interactive-intruder threat model, second-scale latency on a genuinely novel command is within the range of a real congested server. For high-rate scanning, the fast-path and cache carry the load.

**Terms on this slide**

• Log scale: Each axis step is 10×; used because the values differ by thousands of times.
• Median vs mean: Median is the middle value — less affected by a few very slow outliers.
• req/s: Requests per second.


## Slide 19 — Result 2 — Diversity and realism

Result two, goals G1 and G2. On diversity, all five decoys score high: SQL 0.992 — 470 distinct outputs for 474 injection payloads — Web3 0.944, SSH 0.903, CI/CD 0.9, and AI-API 0.64.
A static table would by construction collapse many payloads onto the same canned reply and score near zero. So an automated scanner cannot cluster our output into a small deterministic set.

On realism, the mean judge score is 4.37 out of 5, with 25 of the 30 samples rated a full 5. But look at the distribution, not just the mean: it is bimodal.
Most replies are clearly realistic, a few are clearly unconvincing, almost nothing in between — the signature of a system that is usually in character but occasionally lapses.
When we inspected the low scores, most were AI-API responses to structured payloads — generic error text that did not engage with the specific XML or SSRF probe —
and a few were SSH replies that were templated or fell back to a bare "command not found". We report those rather than smoothing them into the average.

**Terms on this slide**

• Bimodal: A distribution with two peaks — here, a cluster at 5 and a small cluster at 1.
• Templated reply: A generic canned-looking answer — exactly what the LM was supposed to avoid.


## Slide 20 — The honest per-service picture

This table consolidates the per-service picture, and it is the slide I most want you to remember, because it is where we resist the temptation to hide behind an average.
The structured-protocol decoys — SQL, Web3, SSH, CI/CD — score 0.90 to 0.99 on diversity and 4.71 to 5.00 on judged realism. The AI-API decoy sits at 0.64 and 1.00.
The disparity is stark and, crucially, consistent across two independent metrics: one is an automatic count of distinct outputs, the other is a separate model's judgement.
That they agree so closely on which service is weakest tells us the finding is real, not an artefact of either measure.

Our explanation: SQL and JSON-RPC have rigid, well-known output formats, so the model has very little room to break character. An "internal AI API" is under-constrained,
so the model more often falls back on generic error text. That points at a concrete fix — a much tighter output contract for that decoy — rather than a flaw in the approach.
Also note the caveat: per-service judge samples are small; they show the direction and size of the disparity, not precise point estimates.

**Terms on this slide**

• Output contract: A strict specification of exactly what format the reply must take.
• Point estimate: A single number; with n = 3 the number is indicative, not precise.


## Slide 21 — Result 3 — Blockchain integrity test

Result three is the integrity claim, tested directly rather than argued. We fetch a stored record, recompute its SHA-256 digest, and confirm it matches the anchored value exactly.
Then we modify a single field of the record, re-hash, and confirm the digest no longer matches. The tampering is detected.

This confirms goal G5: an attacker who compromises the honeypot and edits a stored record cannot make the new hash match what is already on the chain.
The evidence can be verified by anyone, later, without trusting our machine. In the live demo on the dashboard we show exactly this: an event's digest and its on-chain status.


## Slide 22 — Three engineering gaps we found — and fixed — during construction

Section 7 of the paper documents three concrete defects we hit, because a working sensor is not only a design — it is a set of bugs found and fixed.

Gap one: our first build sent essentially every SSH command to the model, giving about 4 seconds mean latency — slow, and a fingerprintable timing signature.
We measured the causes: a fresh TCP plus TLS connection on every request, and a generation-length cap far larger than a shell output needs. The fix was the tiered path,
a single pooled client, and a measured cap: 4.0 down to about 1.35 seconds, roughly threefold, across two independent runs. Applying the same pooling fix in all five decoys
cut their latency 30 to 41 percent and halved the variance. Interestingly, swapping in a smaller model did not help — on the hosted API, provider routing dominated parameter count.

Gap two is the important one for anyone who benchmarks. An early harness reported hundreds of requests per second concurrent throughput. It was measuring the cache: the concurrent test reused
payloads already sent during the diversity pass, so every request was a Redis hit. We fixed it with a per-request nonce. The honest number, 1.61 requests per second, is two to three orders
of magnitude lower. We kept this in the paper because it is a common, flattering, easily missed mistake.

Gap three: the first classifier labelled about three-quarters of traffic as unknown — not because the traffic was unclassifiable, but because the rules were too narrow.
Expanding them brought unknown from 75 percent to effectively zero on a held-out sample of 1,000 real payloads.

**Terms on this slide**

• TCP + TLS handshake: Setting up a new encrypted network connection costs several round-trips; reusing one pooled connection avoids that on every request.
• Generation-length cap (max tokens): The maximum number of words the model may produce; larger caps mean longer generation time.
• Connection pooling: Keeping one warm connection open and reusing it.
• Held-out sample: Data not used while designing the rules, so the test is fair.


## Slide 23 — How we compare with prior systems

How does this sit against prior work? Figure 11 scores three classes of system on five capabilities.
Static honeypots like Cowrie lead only on routine latency — and that is the same property that let a single packet fingerprint them.
Single-surface LLM honeypots — ShelLM, HoneyLLM, HoneyGPT — share our generative advantage, but on one protocol, and none addresses log integrity.
Blockchain secure-logging systems give integrity but are not deception sensors. Ours is the only design scoring highly on every dimension at once.
That is the sense in which we "dominate": not by beating any system on its own best metric, but by being the only one that is simultaneously multi-protocol, generative, fast on routine traffic, and integrity-anchored.

Two honest caveats. First, the numbers in our comparison table are each system's own published figures under different conditions — we did not re-benchmark them on one testbed,
so this is not a controlled head-to-head. Second, ShelLM's 0.92 accuracy comes from a human-subject study, which is stronger evidence than our LM judge; we explicitly do not claim parity.
What we do claim: our best decoys reach diversity and realism at least in ShelLM's range, across five protocols instead of one.

**Terms on this slide**

• ShelLM (Sladić et al. 2024): First integrated generative SSH honeypot; strongest published human-study realism result.
• HoneyLLM (Fan et al. 2024): LLM honeypot with a filter/router front end; 1.88 s per command vs 0.138 s for Cowrie.
• HoneyGPT (Wang et al. 2024): Adds a prompt-management component to track session state.
• SoK (Bridges et al. 2025): Systematisation of sixteen LLM honeypots; distils the canonical architecture our design mirrors.


## Slide 24 — Limitations and future work

Limitations, stated plainly. The most important one: realism is measured by proxy. An LM judge can only flag gross failures; it can be miscalibrated and share blind spots with the model it judges.
A defensible claim of indistinguishability needs a human-subject study — practitioners interacting with matched real and decoy sessions under blinded conditions — and designing and running that is our primary future work.
The evaluation is a single run on one response model and one judge. Diversity rewards uniqueness, which is necessary but not sufficient — unique-but-wrong output would score well on diversity and badly with the judge,
which is exactly the AI-API decoy's profile; that is why we read the two together.

Next steps beyond the human study: redesign the AI-API decoy with a tight output contract or a non-generative fallback; compare models to map the realism-latency-cost frontier;
measure the classifier's precision and recall; and feed the intent-labelled, integrity-anchored logs into MITRE ATT&CK mapping as a downstream consumer.

**Terms on this slide**

• Threats to validity: Standard research term for reasons the results might not generalise.
• Blinded study: Participants do not know which session is real and which is the decoy.
• Precision: Of the items labelled X, how many really are X. Recall: of all real X, how many were labelled X.
• MITRE ATT&CK: An industry-standard catalogue of attacker tactics and techniques.


## Slide 25 — Conclusion — what to take away

To conclude. We presented a multi-protocol cyber-deception framework coupling a tiered, LM-backed response engine with blockchain-anchored logging across five decoys.
Generative replies make the honeypot non-enumerable. The tiered path keeps routine traffic at static-honeypot speed and pays the LM cost only on the novel tail.
On-chain anchoring makes the audit trail tamper-evident independent of the logging host, and we verified that directly.
On 2,500 real payloads we get high diversity across all five decoys and strong judged realism, with the AI-API decoy the one service that measurably underperforms — and the priority for refinement.
And by documenting the engineering gaps, a benchmark correction, and the per-service disparity alongside the favourable numbers, we aimed to give an honest account of what an LM-plus-blockchain deception sensor does and does not yet achieve.


## Slide 26 — Thank you — questions?

Thank you. I am happy to take questions.

LIKELY QUESTIONS & SHORT ANSWERS
• "Why not a human study?" — Cost and time; it is our stated primary future work. The LM judge is used only to find gross failures and per-service disparities, never to certify indistinguishability.
• "Isn't 2.33 s a giveaway?" — For routine commands (~80% of traffic) we answer in 0.8 ms. Novel commands from a human intruder at human speed see 2 s, which is within the range of a congested real server. Published LLM honeypots sit at 1.88–4 s per command on EVERY request.
• "Why Ethereum / why blockchain instead of a signed log or write-once storage?" — Any append-only anchor works; a ledger gives a third-party-verifiable, host-independent commitment with existing tooling. We store only 32-byte digests, so cost and privacy are minimal. (Do not claim confidentiality — we claim tamper-evidence only.)
• "What if the LM breaks character?" — The persona prompt forbids explanations/markdown/AI disclaimers; the judge rubric scores a refusal as 1, and our low-score cases are mostly generic errors, not disclaimers. Character stability is an open problem across this literature.
• "Why rules instead of ML for classification?" — Auditability, explainability, zero latency, no training data; we plan a precision/recall study and a comparison with a learned classifier.
• "Can the attacker DoS you by forcing LM calls?" — The cache and fast-path absorb repeats; only novel input costs an LM call. Rate-limiting the LM tier is straightforward and part of deployment hardening.
• "Cost?" — Hosted 8B model, no local GPU; only the novel tail is metered.


---

# Consolidated glossary (alphabetical)

- **Asynchronous** — Handles many connections at once without blocking on any single one.
- **Audit trail** — The chronological record of events, kept for later review.
- **Auditable / explainable** — A human can inspect and justify why a label was assigned — essential if the label appears in an investigation.
- **Bimodal** — A distribution with two peaks — here, a cluster at 5 and a small cluster at 1.
- **Blinded study** — Participants do not know which session is real and which is the decoy.
- **Blockchain-anchored** — A short fingerprint (hash) of each record is written onto a blockchain, which cannot be rewritten.
- **Breaking character** — When the LM outputs a refusal or 'As an AI model…' — a deception-fatal tell.
- **Cache miss / hit** — Miss = not found in cache, must compute; hit = found, return instantly.
- **CI/CD (Jenkins)** — Continuous Integration / Delivery — servers that build and deploy code; compromising one lets attackers poison the software supply chain.
- **Compromised host** — A machine the attacker has gained control of.
- **Connection pooling** — Keeping one warm connection open and reusing it.
- **Containerised / bridge network** — Each component runs in its own Docker container; a bridge network is a private virtual network between them.
- **Control plane** — The management components (collector, datastore, chain) as opposed to the attacker-facing decoys.
- **Cryptomining** — Hijacking a machine's CPU to mine cryptocurrency for the attacker.
- **Cyber deception** — Defensive technique: plant fake systems/data so attackers waste time on decoys and reveal themselves.
- **Deterministic** — Same input always gives exactly the same output — a tell-tale sign of a scripted decoy.
- **Deterministic serialisation** — Converting the record to bytes in a fixed order so identical records always hash identically.
- **Digest** — Another word for the hash output — the fixed-size fingerprint.
- **Enumerable** — Can be fully listed out. A finite table of answers can be discovered by trying inputs.
- **Equal-error rate (EER)** — The error rate at the point where false positives equal false negatives; 0.0183 means ~1.8% error — a very accurate detector.
- **Ethereum** — A public blockchain platform. We run a local (private) Ethereum node; we only store hashes on it, never the raw logs.
- **Fingerprinting** — Identifying what software a remote machine runs from tiny behavioural quirks in its replies.
- **Forensic logging** — Recording attack evidence in a way that can later be used to investigate or prove what happened.
- **Generation-length cap (max tokens)** — The maximum number of words the model may produce; larger caps mean longer generation time.
- **Handshake** — The initial exchange that sets up a protocol session. Scanners often connect and leave without completing it.
- **Held-out sample** — Data not used while designing the rules, so the test is fair.
- **High-interaction honeypot** — A real full OS used as bait. Very realistic but expensive and dangerous if the attacker escapes.
- **HoneyGPT (Wang et al. 2024)** — Adds a prompt-management component to track session state.
- **HoneyLLM (Fan et al. 2024)** — LLM honeypot with a filter/router front end; 1.88 s per command vs 0.138 s for Cowrie.
- **Hosted inference API** — The model runs on a cloud provider; we call it over the network instead of running it on our own GPU.
- **Immutable / append-only** — Blocks can only be added to a blockchain, never edited; rewriting history would require re-mining every later block.
- **JSON-RPC** — A simple remote-procedure-call protocol over JSON; Ethereum nodes expose it (methods like eth_accounts, personal_unlockAccount).
- **Language model (LM/LLM)** — An AI model (like ChatGPT / Llama) that generates text. We use it to generate fake server output.
- **Latency uniformity** — If every reply takes exactly the same suspicious multi-second delay, timing alone reveals a decoy.
- **Llama-3.1-8B** — Meta's open-weight language model with 8 billion parameters; 'instruction-tuned' means trained to follow instructions.
- **LLM-as-judge** — Using a second AI model to grade another model's output — cheap but imperfect (Zheng et al., NeurIPS 2023).
- **Local Ethereum chain** — A private Ethereum node (Ganache-style) under our control, used as an integrity anchor; the same design works on a public chain.
- **Log scale** — Each axis step is 10×; used because the values differ by thousands of times.
- **Low / medium-interaction honeypot** — Emulates a service with scripted logic instead of running the real thing. Cheap and safe but shallow.
- **Median vs mean** — Median is the middle value — less affected by a few very slow outliers.
- **MITRE ATT&CK** — An industry-standard catalogue of attacker tactics and techniques.
- **Multi-protocol** — Covers several different network services / attack surfaces, not just SSH.
- **Nonce** — A 'number used once' appended to a request so it is guaranteed unique.
- **Output contract** — A strict specification of exactly what format the reply must take.
- **Point estimate** — A single number; with n = 3 the number is indicative, not precise.
- **Port** — A numbered door on a server; each service listens on one (e.g. SSH on 22, PostgreSQL on 5432).
- **Precision** — Of the items labelled X, how many really are X. Recall: of all real X, how many were labelled X.
- **Privilege escalation** — Going from a low-privilege account to admin/root.
- **Prompt injection / jailbreak** — Crafting text to make an AI model ignore its instructions or reveal hidden data.
- **Provenance** — Where each payload came from — recorded so the dataset is auditable.
- **Proxy** — A relay that accepts the connection and forwards it — here it also logs every connection before anything else happens.
- **RCE / reverse shell** — Remote Code Execution; a reverse shell is a connection from the victim back to the attacker giving them a command line.
- **Recall** — Fraction of true cases the classifier catches.
- **Reconnaissance** — Scanning, service enumeration, and the first commands an intruder runs to look around.
- **Redis** — A fast in-memory key-value datastore; holds the full records and the response cache.
- **req/s** — Requests per second.
- **SecLists / PayloadsAllTheThings** — Two widely used open-source collections of real attack strings used by penetration testers.
- **SHA-256** — A cryptographic hash function: turns any data into a fixed 256-bit fingerprint. Changing one byte of input gives a completely different fingerprint, and it is infeasible to find two inputs with the same fingerprint.
- **ShelLM (Sladić et al. 2024)** — First integrated generative SSH honeypot; strongest published human-study realism result.
- **SoK (Bridges et al. 2025)** — Systematisation of sixteen LLM honeypots; distils the canonical architecture our design mirrors.
- **SQL injection** — Inserting malicious SQL into an input so the database executes the attacker's query.
- **SSH** — Secure Shell — the remote command-line login used to administer Linux servers; the most-attacked service on the Internet.
- **Standard deviation** — How spread out the measurements are.
- **System persona / system prompt** — Hidden instructions telling the model what role to play.
- **Tamper-evident vs tamper-proof** — Tamper-proof = cannot be changed. Tamper-evident = can be changed, but any change is detectable. We guarantee the latter.
- **TCP + TLS handshake** — Setting up a new encrypted network connection costs several round-trips; reusing one pooled connection avoids that on every request.
- **Telemetry** — The data/records collected by a sensor — here, attacker connections, commands and payloads.
- **Templated reply** — A generic canned-looking answer — exactly what the LM was supposed to avoid.
- **Threat model** — A precise statement of what the attacker can do and what we assume; every security design must state one.
- **Threat rating** — A score combining how many and how severe the attacker's intents are.
- **Threats to validity** — Standard research term for reasons the results might not generalise.
- **Transaction (tx)** — A record written onto the blockchain; once mined into a block it is practically immutable.
- **Uniqueness ratio** — distinct replies / total replies. 1.0 = every reply different; 0 = all identical.
- **XXE / SSRF** — XML External Entity and Server-Side Request Forgery — web attacks that make a server read files or contact internal URLs.


---

# Numbers to have at your fingertips

| Quantity | Value |
|---|---|
| Corpus | 2,500 real payloads: 1,862 SSH · 474 SQL · 136 API · 18 Web3 · 10 CI/CD |
| Static fast-path latency | 0.80 ms mean (~1,250 req/s) |
| Dynamic (LM) latency | 2.33 s mean · 1.73 s median · σ 1.40 s · 0.43 req/s |
| Concurrent (10 sessions, cache-miss forced) | 1.61 req/s · 2.19 s mean |
| Diversity (uniqueness ratio) | SQL 0.992 · Web3 0.944 · SSH 0.903 · CI/CD 0.900 · AI-API 0.64 |
| LM-judge realism | 4.37/5 mean · σ 1.45 · n = 30 · 25/30 rated 5 |
| Per-service realism | SQL 5.00 (n=3) · SSH 4.71 (n=24) · AI-API 1.00 (n=3) |
| Gap 1 fix | ~4.0 s → ~1.35 s (≈3×); decoy pooling −30–41 %, variance halved |
| Gap 2 fix | hundreds req/s (cache artefact) → 1.61 req/s (real) |
| Gap 3 fix | unknown 75 % → ~0 % on 1,000 held-out payloads |
| Response model / judge | Llama-3.1-8B (hosted API) / Llama-3.1-70B |
| Prior art | Vetterl & Clayton: 1 packet, EER 0.0183, 2,844 Cowrie/Kippo · ShelLM 0.92 acc (human, 226 cmds) · HoneyLLM 1.88 s/cmd vs Cowrie 0.138 s |
| Dashboard capture | 6,742 intercepted events (Fig. 5) |
