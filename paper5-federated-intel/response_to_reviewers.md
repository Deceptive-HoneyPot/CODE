# Response to Reviewers — ICOIICS_245

**Title:** Hub-less Cross-Honeypot Threat Intelligence: Federated IOC Corroboration on a Shared Ledger
**Authors:** Suhas Reddy Annem, Sisir Reddy Nellore, Radhika G

We thank both reviewers for the detailed and constructive comments. Every point
has been addressed in the camera-ready manuscript; section references below are
to the revised paper. No measured value was changed — all numbers continue to
come from the single benchmark run reported in the submitted version.

---

## Reviewer 1

**1. Describe how the five campaign variation modes are generated and associated with ground-truth campaign identities.**

Section V-B now specifies the generator formally. A campaign is defined as a
tuple (template, /24 prefix, session token, host octet, target set, variation
mode), with the target set and mode drawn uniformly. The five modes — *fixed*,
*token*, *ip*, *token+ip* and *net* — are each defined by exactly which
components are re-drawn per target. Every record carries the identifier of the
campaign that produced it, noise records carry ⊥, and the text states explicitly
that these labels are the ground truth used for scoring and are never visible to
the reconstruction, which observes only anchored digests.

**2. Explain how late observations are handled operationally when commit–reveal validation rejects them.**

Section IV-C now states the operational handling: an observation arriving after
the reveal phase is not discarded, but held by the node and committed in the
following epoch, where it corroborates with any node that observed the same
digest in that window. The consequence for readers is also given — a reader
requiring corroboration inside one epoch counts such observers separately, while
a reader that unions per-epoch observer sets counts them together at the cost of
admitting a cross-boundary echo.

**3. Replace informal expressions such as "how much of the hub's function survives" with formal academic wording.**

The flagged sentence now reads: "This paper determines which functions of a
centralized aggregator can be preserved when the aggregator is replaced by a
shared append-only ledger…". The manuscript was re-read in full and comparable
informalities were removed throughout, including the two expressions noted by
Reviewer 2 in comment 6.

**4. Clarify the epoch-based deployment workflow and identify where epoch boundaries affect corroboration results.**

Section IV-C now describes the workflow explicitly: time is divided into epochs
of fixed length Δ; within an epoch each node commits every digest observed since
its last commit; commitments close at the boundary, after which reveals are
anchored; and validation is evaluated per epoch. The effect on results is stated
directly — corroboration of a campaign straddling a boundary is delayed by at
most one epoch under the union rule and lost under the strict rule, making Δ the
parameter that trades detection latency against echo resistance. The text notes
that Section VI-E measures the strict rule within a single epoch, the
conservative case.

**5. Standardize figure captions, capitalization, spacing and naming conventions.**

All fourteen captions were brought to one scheme: an experiment tag where
applicable ("E1 and E7:", "E4:"), a descriptive sentence, and terminal
punctuation; multi-experiment tags now use "and" rather than a slash. Naming was
unified across the manuscript (hub-less, commit–reveal, keying function, observer
map), numeric formatting was made consistent (thin spaces before units, thousands
separators), and the algorithm captions were converted to a single verb-phrase
form.

---

## Reviewer 2

**1. The E4 campaign dataset is entirely synthetic, with only 16 campaigns and five variation modes, so the reported corroboration accuracy may not represent real-world attack diversity.**

Agreed, and now stated as a limitation under "Synthetic corroboration workload"
(Section VII-E). The text explains why the dataset is generated — campaign labels
are required for precision and recall and captured honeypot traffic does not
carry them — and states that the absolute figures characterize this workload
rather than a deployment. What the experiment establishes is the mechanism and
its ordering: an exact-match key corroborates no campaign that varies per target,
and each relaxation recovers some campaigns while merging some unrelated ones.
That ordering follows from the definitions of the keys and modes rather than from
the sample size.

**2. The choice of normalization rules and their sensitivity to unseen IOC variations is not evaluated beyond the synthetic workload.**

Addressed under "Sensitivity of the keying functions" (Section VII-E). The keys
were fixed before the datasets were generated, but their normalization rules
match the structure of the generated variation, so the measured accuracy is
stated as an upper bound on what those rules achieve against unseen variation
such as encoded payloads, padded commands or per-target reordering. The text
states that the keys were neither tuned nor evaluated outside the five modes and
that a deployment should measure its own key against its own traffic.

**3. The Sybil evaluation uses only 30 fabricated digests and three controlled identities, which provides limited evidence for behavior under larger-scale or adaptive identity attacks.**

Addressed under "Scale of the adversarial evaluation" (Section VII-E). The text
explains that the Sybil result verifies the arithmetic of the corroboration
predicate — c identities satisfy C_k exactly when c ≥ k, which holds for any c —
so a larger trial would add only the cost of acquiring identities on a particular
chain, a property of that chain's admission policy rather than of the scheme. It
also states plainly that neither adversary is adaptive: no attacker is modeled
that observes the corroboration output and adjusts its anchoring, or that times
reveals to exploit epoch boundaries, and these are identified as the natural next
experiments.

**4. The 255 events/s throughput and latency results come from Ganache with transactions mined immediately in separate blocks, so real consensus, propagation, block-time and network effects are not experimentally measured.**

Agreed, and now stated under "Absence of real consensus" (Section VII-E). The
text states that the saturation point, the millisecond-scale latencies and the
propagation figure contain no block time, no consensus round, no gossip
propagation and no fork or reorganization behavior, and that they characterize
the anchoring and reconstruction software rather than a distributed deployment.
Section VII-A separately lists which results are independent of block production
— the gas model, the batching law and proof sizes, the linear bootstrap cost, the
accuracy ordering, the Sybil bound and the commit–reveal argument — and states
explicitly that the throughput and latency figures are not among them.

**5. The commit–reveal mechanism rejects honest late observers after the first reveal, but its effect on campaign recall across different epoch lengths is acknowledged as unmeasured.**

Retained as an explicit limitation and made more precise. Section IV-C now gives
the operational handling (the observation is carried into the next epoch) and
Section VII-C states that the resulting recall cost depends on campaign duration
relative to Δ and is not measured in this work. This is listed among the open
items rather than claimed as resolved.

**6. The English language should be revised (for example "the quality of the corroboration signal is set by", "worst on both axes").**

Both flagged expressions were rewritten. The first now reads that the corroboration
signal depends on the keying function; the second now states that the template key
"attains the lowest precision and the lowest recall of the four". The full
manuscript was re-read for comparable phrasing and for consistency of tense,
terminology and register.

---

## Summary of changes

| Item | Location in revised paper |
|---|---|
| Campaign/variation-mode generator, ground-truth labels | Section V-B |
| Epoch workflow, late-observation handling | Section IV-C |
| Formal wording, language revision | Throughout (Sections I, VI-D) |
| Caption, naming and numeric-format standardization | All figures and tables |
| Synthetic workload limitation | Section VII-E |
| Keying-function sensitivity | Section VII-E |
| Adversarial evaluation scale, non-adaptive adversaries | Section VII-E |
| Absence of real consensus | Sections VII-A, VII-E |
| Commit–reveal recall cost unmeasured | Sections IV-C, VII-C |

The paper remains within 8 pages in the IEEE conference template.
