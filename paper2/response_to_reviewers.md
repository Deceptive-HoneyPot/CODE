# Response to Reviewers

**Paper:** A Multi-Protocol Cyber-Deception Framework Combining Language-Model Response Synthesis with Blockchain-Anchored Forensic Logging

**Venue:** I-SMAC 2026

---

We thank both reviewers for their careful reading. The comments identified two weaknesses we had not seen: that our diversity metric addresses only one layer of fingerprinting, and that the generative response layer introduces security risks a static honeypot does not have. Addressing these produced what we believe are the two strongest additions to the paper.

We have been deliberate about one thing throughout. Several comments ask for measurements we could not complete before the camera-ready deadline. We have not manufactured results for these. Where a comment required new experimental data, we have either derived what our existing measurements genuinely support, or specified the experiment precisely in a new Section 12 (Validation Roadmap) and stated plainly that it remains outstanding. We would rather submit a paper whose boundary between measured and unmeasured is unambiguous.

A summary of changes precedes the point-by-point response.

---

## Summary of changes

**New sections**
- Section 7, Resistance to Fingerprinting: A Layered Analysis (addresses R2.3)
- Section 8, Security Analysis of the Generative Response Layer (addresses R2.6)
- Section 9, Cost Analysis (addresses R1.8)
- Section 12, Validation Roadmap (addresses R1.5, R2.2, R2.4, and the unmeasured parts of R1.3 and R1.6)

**Substantially revised**
- Section 5.2, new subsection on attack-scenario coverage with an ATT&CK mapping table and an explicit statement of the single-request limitation (R1.3)
- Section 6.2, new scaling analysis of the concurrency data (R1.6, R2.5)
- Section 10.3, specification of what a controlled comparison requires (R2.2)
- Section 11.3, coverage and correctness distinguished for the intent classifier (R2.4)
- Section 13, limitations reordered by severity

**Corrections made during revision**
- Withdrew the claim that approximately 80% of traffic is routine. This figure was not measured by our harness. Cost is now expressed as a function of the hit rate (Section 9.1) rather than assuming a value.
- Corrected the Vetterl and Clayton figure. The published result is 7,605 instances across nine honeypot implementations; our original text attributed 2,844 to Cowrie and Kippo without noting it was a subset.
- Noted that the 1.35 s optimisation figure and the 2.33 s evaluation figure come from different runs against different corpora and are not directly comparable (Section 11.1). The original manuscript presented both without this qualification.

---

# Reviewer 1

### R1.1 — "The design of the proposed approach is technically sound and LM-based deception is well incorporated into it."

We thank the reviewer. No change required.

### R1.2 — "The multi-protocol system is novel and relevant to the practical setting."

We thank the reviewer. Section 10.4 now states the novelty claim more precisely: the framework does not dominate prior systems on any individual metric, but occupies a combination of properties no prior system occupies.

### R1.3 — "More real-world attack scenarios need to be considered in the evaluation."

**Partially addressed; the remainder is specified as future work.**

We have separated what our corpus does cover from what it does not, in a new Section 5.2.

Our 2,500 payloads are real strings drawn from SecLists and PayloadsAllTheThings, not synthesised, so the corpus already covers the *content* of a broad range of contemporary attacks. Table I now maps each partition onto the adversary behaviour it represents and the corresponding MITRE ATT&CK technique, making that coverage explicit rather than implied.

The reviewer's comment also exposes a limitation we had not stated. Every payload is evaluated as an **independent single request**. A real intrusion is a conditioned sequence, and our evaluation therefore measures the system's response to the constituents of real attacks rather than its coherence across a campaign. Session consistency is not measured by any metric we report. We now say this plainly in Section 5.2 rather than describing the corpus in terms that imply campaign-level coverage.

Section 12.3 specifies the multi-stage evaluation that would close the gap: at least ten ordered attack chains of eight to fifteen interactions each, replayed as single sessions, scored on whether later responses contradict earlier ones. We expect this to produce the least flattering results of any experiment we have proposed, which is why we have specified it rather than omitted it.

### R1.4 — "The time delay of the LM response needs optimization."

**Addressed. Optimisation work was already performed and is now reported more prominently, with the trade-off it creates.**

Section 11.1 documents a measured threefold reduction in mean dynamic-path latency, from approximately 4.0 s to approximately 1.35 s, achieved by three changes: introducing the three-tier response path so routine traffic never reaches the model, replacing per-request TCP and TLS connections with a pooled client, and reducing the generation-length cap to a measured value. Table V reports the per-decoy effect of applying the same pooling fix across all five decoys, giving 30% to 41% latency reductions and a halving to two-thirds reduction in variance.

We also tested whether a smaller model would help. It did not, because provider routing dominated parameter count on the hosted API. We report this because it is a negative result others would otherwise repeat.

The reviewer's comment prompted us to examine what the optimisation costs, and this produced the paper's most significant new finding. The tiered design that delivers the speedup creates a **latency discontinuity of roughly three and a half orders of magnitude** between the fast-path (0.8 ms, σ 0.3 ms) and the model path (2.33 s, σ 1.40 s). These distributions do not overlap. A new Section 7.2 shows that a single pair of probes, one common command and one arbitrary string, distinguishes the tiers with high confidence. Optimising latency by tiering therefore trades a slow-response tell for a stronger relative-timing tell. We now state this as a qualification on design goal G3 and specify the jitter-mitigation experiment in Section 12.5.

We are also now explicit that the 1.35 s and 2.33 s figures come from different runs on different corpora and are not directly comparable.

### R1.5 — "The realism measure needs to be validated by human experts."

**Not addressed by new data. We agree, and have specified the study rather than substituting a weaker proxy.**

We agree without reservation. Sections 5.4 and 13 already stated that the LM judge is a proxy; the revision strengthens this by reporting that our judged sample is only n = 30 with a strongly bimodal distribution, so the mean carries wide uncertainty. We have removed any phrasing that could read as a claim of indistinguishability.

Section 12.1 now specifies the study in full: at least twenty participants with professional security experience, interactive sessions against a blinded randomised mix of real services and decoys across all five protocols, free-form command issuing to a fixed budget, and detection rate with confidence intervals as the outcome, reported **per protocol rather than pooled**. Per-protocol reporting matters because our own data predicts the AI-API decoy will differ sharply from the other four, and a pooled figure would conceal exactly the disparity we consider important.

For calibration, ShelLM [11] used twelve participants for a single protocol; twenty across five is the minimum for per-protocol resolution.

We could not recruit and run this study within the revision window. Rather than report a strengthened automated proxy as though it answered the comment, we have stated that the human-subject claim is not yet supported and made the required work concrete.

### R1.6 — "Scalability with respect to a larger number of sessions needs investigation."

**Partially addressed with new analysis of existing data; the load sweep is specified as future work.**

The original manuscript reported the concurrency measurements without analysing them. Doing so, in a rewritten Section 6.2, yields a result that directly answers part of the reviewer's question.

Sequential throughput is 0.43 requests/s. Ideal linear scaling at concurrency 10 would give 4.29 requests/s. Measured throughput is 1.61 requests/s, a speedup of 3.76 and a parallel efficiency of 0.376. Applying Little's Law, mean requests in flight is 1.61 × 2.19 = 3.53, not 10. The system therefore saturates at an effective parallelism of roughly 3.5.

The diagnostically useful part is *where* the ceiling sits. Mean per-request latency under load (2.19 s) is slightly **lower** than sequential latency (2.33 s). If requests were queueing inside our framework, latency would inflate with concurrency; it does not. The bottleneck is upstream admission control at the hosted inference provider, not any queue in the decoys, proxy, or response engine. An operator needing more concurrent capacity should raise the provider rate limit, distribute across providers, or self-host, rather than re-engineer the framework.

We are explicit about the limits of this inference. It is valid reasoning from two concurrency levels, c = 1 and c = 10. It is not a scaling curve. Section 12.4 specifies the sweep required: c ∈ {1, 5, 10, 25, 50, 100}, under both burst and sustained load, repeated with the provider rate limit raised in order to separate framework limits from provider limits. Our environment permits this experiment; it was not run before the deadline.

### R1.7 — "Performance of AI-API decoy needs further improvement."

**Diagnosis addressed; the improvement is specified but not yet measured.**

We agree this is the system's clearest weakness and have kept it prominent rather than averaging it away. The AI-API decoy scores 0.640 uniqueness against 0.900 to 0.992 for the other four, and draws the majority of low realism ratings.

The revision states the diagnosis more precisely. Emulating an internal AI API is **under-constrained** relative to emulating a shell or SQL engine, whose output grammars are rigid and well known. The model consequently falls back on generic error text that does not engage the specific payload, which is why structurally similar XXE and SSRF probes converge on near-identical output. The two independent metrics agreeing on which service is weakest is itself evidence the finding is real rather than an artefact of either measure.

This points at a concrete fix rather than a limitation of the approach: a tightly specified output contract for that decoy, with a schema-driven non-generative fallback for structured payloads, so the model is constrained in the same way the SQL decoy's error grammar constrains it.

We have not implemented and re-evaluated this fix, and we do not claim an improvement we have not measured. Section 8.1 adds a related point the reviewer's comment led us to: the AI-API decoy is also the acute case for prompt injection against the decoy itself, since injection payloads arrive there as legitimate-looking traffic. Section 12.6 specifies a persona-escape-rate experiment, which we identify as the cheapest missing measurement in the paper.

### R1.8 — "The costs involved need more discussion."

**Addressed with a new Section 9, and a correction.**

Section 9 gives a parametric cost model grounded in measured quantities. Mean dynamic response length is 13.8 words, roughly 19 output tokens; input is the service persona plus recent session history, on the order of a few hundred tokens. Cost per 1,000 intercepted interactions is 1,000 × (1 − *h*) × *c*, where *h* is the fast-path and cache hit rate and *c* the per-call price.

Working through this produced a correction. The original manuscript asserted that approximately 80% of traffic is routine. **That figure was not measured by our harness and we have withdrawn it.** Our evaluation drove the system with 2,500 distinct payloads specifically to force model calls, so it bounds model usage from above rather than establishing a representative hit rate. Section 9.2 states this and Section 12.7 specifies the live-traffic instrumentation needed to obtain a real value. We would rather present cost as a function of an honest unknown than as a point estimate resting on an unmeasured assumption.

Section 9.3 addresses the case that actually binds. Section 8.2 establishes that an adversary can force *h* to zero by appending a nonce to every request, defeating the cache. At the measured saturated throughput this yields roughly 138,000 model calls per day, entirely under adversary control. A generative honeypot therefore requires a hard spend cap and a defined degradation mode, falling back to static responses under attack. We argue this is an architectural requirement rather than an operational detail, and note its absence from the current build.

Section 9.4 compares the cost profile against static and high-interaction honeypots, and notes that a public-chain deployment would need Merkle-root batching rather than per-record anchoring.

---

# Reviewer 2

### R2.1 — "The three-level response system represents a good compromise between speed and realism."

We thank the reviewer. Section 7.2 now qualifies this: the compromise is favourable on speed and realism, and unfavourable on timing-based detectability. We think stating both sides strengthens the design's presentation.

### R2.2 — "Comparative evaluation of the framework against other modern honeypots is suggested."

**Partially addressed; a controlled comparison is specified but not run.**

Section 10 compares against Cowrie, ShelLM, HoneyLLM, HoneyGPT, and blockchain audit-logging systems on two levels: published numbers and structural properties. Table IV gives the structural comparison across surfaces, response mechanism, routine latency, and log integrity.

We have strengthened the caveat governing the quantitative comparison. Each prior figure is reproduced as published, from systems measured under different conditions with different metrics on different hardware and models. **This is not a controlled head-to-head and we do not present it as one.**

New Section 10.3 sets out what a defensible controlled comparison requires, since the phrase covers a wide range of designs: deploying Cowrie as the static baseline and ShelLM as the generative baseline, its code being public, on the same host as our SSH decoy; driving all three with the identical corpus; and measuring latency, diversity, and realism with the same instruments on the same day. The effort is on the order of several weeks, dominated by making three heterogeneous systems accept one driver and emit comparable logs. It would also be restricted to the SSH surface, since no prior system implements the other four. We identify it as the most valuable single experiment remaining.

### R2.3 — "Diversity of responses needs to be evaluated against sophisticated fingerprinting attacks."

**Addressed by a new Section 7. This comment produced the most substantial change in the revision.**

The reviewer is right, and following the point through led us to conclude that our diversity metric addresses **one of four** fingerprinting layers. Generative honeypot papers, ours included in its original form, tend to report a content-diversity figure and leave the impression it addresses detection generally. Section 7 separates the layers.

**Layer 1, transport and protocol implementation.** The Vetterl and Clayton attack [5] does not examine response content at all. It exploits deviations in off-the-shelf protocol libraries: key-exchange option ordering, malformed-packet behaviour, banner details. Response diversity provides no defence here. Our SSH decoy is a real SSH server, but the SQL, API, Web3, and CI/CD decoys are application-layer emulations that have not been audited for wire-protocol fidelity. We now state that an adversary running this methodology against our deployment would plausibly succeed and that nothing in our evaluation would have caught it. We also note this is equally unaddressed by every generative honeypot we surveyed.

**Layer 2, timing.** Quantified in Section 7.2 and discussed under R1.4 above. A single probe pair distinguishes the tiers.

**Layer 3, content.** This is what uniqueness ratio measures, and the results are genuinely strong: 470 distinct outputs across 474 SQL payloads leaves no useful clustering. Two qualifications now appear. Uniqueness is necessary but not sufficient, since unique-but-wrong output scores well here and poorly with a judge, which is the AI-API profile. And **the cache reintroduces determinism at this layer**: an adversary repeating a payload receives a byte-identical response in cache-hit time, revealing both the caching and the tier boundary. Our diversity measurement used distinct payloads throughout and therefore never exercised this path. We identify this as an evaluation blind spot, not only a system limitation.

**Layer 4, semantic consistency.** Unmeasured; addressed by the scenario evaluation in Section 12.3.

Table III summarises coverage across the four layers. This weakens the paper's headline claim and we think it improves the paper. A reader deploying the framework should understand that response diversity buys resistance to one common class of automated fingerprinting and that two other layers remain open.

### R2.4 — "Rule-based approach for classification of intents needs further validation."

**Partially addressed; a correction, and the validation study specified.**

The reviewer's comment identified a real overstatement. Section 11.3 reported that expanding the rule set reduced the unknown fraction from roughly 75% to effectively zero across 1,000 captured payloads. We have added an explicit statement of what this does and does not show: it demonstrates **coverage**, that the rules fire on the traffic, not **correctness**, that they fire on the right traffic. Coverage without ground truth cannot distinguish a well-tuned rule set from an over-broad one, and the original manuscript did not make that distinction.

Section 12.2 specifies the validation study: a stratified random sample of at least 500 captured payloads across all eight categories and both high- and low-frequency rules; two annotators labelling independently and blind to classifier output; inter-annotator agreement measured and disagreements adjudicated; per-category precision, recall, and F1 reported against the adjudicated labels. This would identify over-broad rules, which coverage measurement cannot, and would give the auditability argument in Section 4.4 quantitative support rather than a design rationale alone.

### R2.5 — "The latency and throughput need to be measured in different load conditions."

**Partially addressed by the analysis under R1.6; the load sweep is specified as future work.**

Please see R1.6 above, which covers the same ground. In brief: Section 6.2 now analyses the c = 1 and c = 10 measurements to establish an effective parallelism of 3.5 and to locate the bottleneck at the inference provider rather than the framework, using the observation that per-request latency does not inflate under load. Section 12.4 specifies the full sweep, c ∈ {1, 5, 10, 25, 50, 100} under burst and sustained load with the provider rate limit varied.

We should note directly that our own benchmark report already flagged this gap, recording that the concurrency test "has not been tested at higher concurrency levels or under sustained (non-burst) load." The reviewer has correctly identified a limitation we were aware of and had not surfaced in the paper. It is now stated in Section 6.2 rather than left in an internal document.

### R2.6 — "Security concerns of LM responses need to be identified."

**Addressed by a new Section 8.**

This comment identified a genuine gap. Section 8 now analyses five risks that a generative response layer introduces and a static honeypot does not have.

**Prompt injection against the decoy (8.1).** Attacker input enters the model's context directly, so an adversary can attempt to override the persona and induce the model to disclose what it is. Success converts suspicion into confirmation. The AI-API decoy is the acute case because it advertises itself as a model endpoint. Mitigations applied are output filtering for break-character markers and, more robustly, writing the system prompt on the assumption an adversary will eventually read it. Persona-escape rate is unmeasured; Section 12.6 specifies the experiment.

**Cost exhaustion through forced cache misses (8.2).** An adversary appending a nonce to every request defeats the cache and forces a model call per request. We know the attack works because our own benchmark harness performs it: the nonce technique introduced for honest measurement is precisely this attack. Mitigations are per-source and global escalation rate limits, a daily spend cap with static-response degradation, and anomaly detection on cache-miss ratio, since a sustained miss ratio near 1.0 from one source is itself a strong threat indicator worth surfacing. None is implemented in the current build.

**Injection into the operator console (8.3).** The dashboard renders attacker payloads and model output, both adversary-influenced text in a privileged context. The model path worsens this, because responses are generated at request time rather than drawn from a developer-reviewed set and may contain arbitrary markup. Treating model output as untrusted input to the dashboard, with strict escaping and a content-security policy, is a requirement rather than a hardening measure.

**Generation of genuinely harmful content (8.4).** The model may emit functional exploit code or plausible credentials, supplying an attacker with material of value, and the operator may mistake fabricated content for captured intelligence. A hallucinated internal hostname in the log is indistinguishable from a real one. The mitigation is a provenance field recording which tier produced each response, so synthesised content never enters threat intelligence as though observed. Our records do not currently carry this field and we recommend adding it.

**Integrity is not veracity (8.5).** The anchor proves a record has not been altered, not that its contents are true. In a system where part of every record is machine-generated, this distinction matters. The attacker's input is the probative part of the record and is exactly what anchoring protects; the synthesised response is context. The provenance field of 8.4 is what allows an analyst to keep them apart. We consider this an important clarification for a paper that discusses forensic evidence and cryptographic commitment together.

### R2.7 — "In general, the proposed framework looks promising, but further validation will enhance its contribution."

We agree, and have organised the outstanding validation into a single Section 12 so that the boundary between measured and unmeasured is unambiguous rather than distributed across the text. The seven items, in the order we judge most valuable:

1. Human-subject realism study (12.1) — the strongest available evidence, and the one the paper most needs
2. Controlled comparison against Cowrie and ShelLM (12.3, Section 10.3)
3. Multi-stage attack-scenario consistency evaluation (12.3)
4. Persona-escape-rate measurement (12.6) — cheapest of the set
5. Intent-classifier precision and recall (12.2)
6. Concurrency sweep under burst and sustained load (12.4)
7. Fast-path hit rate under live traffic (12.7)

Items 4, 5, 6, and 7 are runnable in our existing environment. Items 1, 2, and 3 require recruitment or substantial engineering.

---

## Closing note

Two comments, R1.4 on latency optimisation and R2.3 on sophisticated fingerprinting, together produced the finding we consider the revision's most useful contribution: the tiering that makes an LM-backed honeypot economically viable is simultaneously its clearest detection surface, and our own measurements quantify the channel precisely. We would not have identified this without the reviews and are grateful for them.

We have also used the revision to correct three things the reviews did not raise: an unmeasured traffic-composition figure, a misattributed count in a cited result, and two latency figures from different runs presented without qualification. We would rather correct these ourselves than have them found later.
