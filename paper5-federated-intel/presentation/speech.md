# ICOIICS 2026 talk script: Hub-less Cross-Honeypot Threat Intelligence

**Paper ID:** ICOIICS_245
**Deck:** `ICOIICS_245_presentation.pptx` (9 slides, this script is also in each slide's speaker notes)
**Target length:** about 6 minutes at a steady pace (~140 words/min). To get closer to 5 minutes, skip the lines marked *(optional)*.

| Speaker | Slides | Part | Approx. time |
|---|---|---|---|
| **Speaker 1: Suhas Reddy Annem** | 1 to 4 | Problem and design | ~2 min 55 s |
| **Speaker 2: Sisir Reddy Nellore** | 5 to 9 | Results and close | ~3 min |

Lines in quote blocks are what you say. Notes in *italics* are cues and are not spoken.

---

## Slide 1: Title
**Speaker 1 (Suhas)** · ~25 s

> Good morning, everyone. I'm Suhas Reddy Annem, and this is Sisir Reddy Nellore. This work was done with our faculty advisor, Radhika G, at Amrita Vishwa Vidyapeetham, Coimbatore.
>
> Our paper is "Hub-less Cross-Honeypot Threat Intelligence." In the next five minutes we'll show how honeypots run by different organizations can share threat intelligence without a central server, and what that costs when you actually measure it.

*Change "morning" to "afternoon" if needed.*

---

## Slide 2: One central hub correlates everything
**Speaker 1 (Suhas)** · ~40 s

> A honeypot is a decoy that is built to be attacked. But attack campaigns hit many targets, so any one honeypot only sees a slice. The usual fix is a central threat-intelligence platform, such as MISP. Every sensor reports to one server, and that server does the correlation.
>
> That server creates three problems. Everyone has to trust it not to lose, change or hide data. When it goes down, correlation stops. And it is an attractive target: compromise that one host and the whole sensor network goes blind. That's awkward for honeypots, which exist to attract attackers in the first place. *(optional)*

---

## Slide 3: Our design: a ledger of tagged hashes, no hub
**Speaker 1 (Suhas)** · ~50 s

> So we asked: what happens if we remove the hub completely?
>
> On the left is the usual model. On the right is ours. Each honeypot hashes the indicator of compromise it sees, for example the attacker's address and payload. It then writes a small tag to a shared, append-only ledger: its node ID and that hash. That's all. No raw data goes on the chain. There's no smart contract and no registry, and the nodes never talk to each other.
>
> Anyone reading the ledger can build the observer map: for each hash, which nodes reported it. If at least *k* nodes saw the same hash, it is corroborated, which is evidence of one campaign across organizations. A node that joins later, like P4 here, rebuilds the same view from the ledger history alone.

*Point at the left half, then the right half, then P4.*

---

## Slide 4: Commit–reveal stops copied corroboration
**Speaker 1 (Suhas)** · ~45 s

> There's an obvious attack on this. We call it the echo attack. An adversary reads the ledger and re-posts every hash under its own identity, so everything looks like it was seen twice. In our tests, that made 100 percent of single-node hashes look corroborated.
>
> Our fix is commit–reveal. First, a node commits a salted hash, which reveals nothing. Later, it reveals the salt and the hash. A reader counts that node only if its commitment came *before* anyone revealed that hash. The echo node only learns the hash from a reveal, so it is always too late to commit.
>
> Now Sisir will take you through the results.

*Hand over to Sisir.*

---

## Slide 5: Throughput: ledger 255 vs. hub 1,737 events/s
**Speaker 2 (Sisir)** · ~45 s

> Thanks, Suhas. Every number we report is measured, not simulated. We ran a live Ethereum-compatible chain, Ganache, with up to 16 concurrent writer nodes, five repetitions each, and 95 percent confidence intervals. We built a centralized hub in the same test harness, so the comparison is fair.
>
> The ledger, in green, levels off near 255 events per second from eight writers onward, because the chain orders transactions one at a time. The hub, in red, reaches about 1,737, which is 6.8 times faster. Median latency stays around 12 milliseconds, but the tail grows once the chain is saturated. *(optional)* That gap is the measured price of removing the trusted middleman.

---

## Slide 6: Cost matches the calldata model to the unit
**Speaker 2 (Sisir)** · ~35 s

> Cost is very predictable. Each anchored indicator costs 22,120 gas, and that matches the Ethereum calldata formula exactly.
>
> If a node batches 64 hashes under one Merkle root, the cost per indicator falls to 337 gas, as the chart shows. A brand-new node rebuilds the full picture at about 3 milliseconds per block. That cost is linear in history length, with an R-squared of 0.998. *(optional)*

---

## Slide 7: No single keying function fits every campaign
**Speaker 2 (Sisir)** · ~40 s

> Accuracy is where design choices matter. Real campaigns don't send identical indicators to every target. Tokens and source addresses change.
>
> Hashing the exact record is always correct, but it finds only 27.5 percent of campaigns. Stripping out tokens and IPs, the template key, merges unrelated attacks and drops to an F1 of 0.15. The best was the /24 network prefix plus the template: 100 percent precision, 81 percent recall, and an F1 of 0.89.
>
> The point is that the ledger doesn't fix the key. Nodes can choose it, or anchor under several. *(optional)*

---

## Slide 8: Adversaries: what the scheme catches
**Speaker 2 (Sisir)** · ~35 s

> On security, three results. Commit–reveal took the echo attack from 100 percent to zero, for twice the gas, and every genuinely shared hash was still corroborated.
>
> For Sybil attacks, fake hashes pass only if the attacker controls at least *k* identities. So this belongs on a permissioned chain, where identities are controlled.
>
> And when we edited records in a node's local log after anchoring, we caught 500 out of 500, with zero false alarms on 500 untouched records.

---

## Slide 9: Takeaways
**Speaker 2 (Sisir)** · ~35 s

> To sum up: a ledger that carries only tagged hashes can replace the correlation hub for honeypots that don't trust each other. The costs are measurable and predictable. Accuracy depends on the keying function, and commit–reveal is needed against echo attacks.
>
> Our limits: the local chain has no consensus delay, so a real deployment will be slower. The campaign data is synthetic, and Sybil resistance needs controlled identity.
>
> Thank you. We're happy to take questions.

---

## Q&A preparation (not part of the 5 minutes)

Short answers either speaker can give. All of them come from the paper.

**Why not just use MISP federation?**
MISP instances sync pairwise between administered servers, and a new participant has to be admitted before it receives anything. In our scheme there is no server to be introduced to: every node writes to one ledger and any reader reads it.

**Ganache isn't a real network. Do the results hold?**
Some do and some don't. Gas costs, the batching law, bootstrap cost per block, the accuracy trade-off, the Sybil bound and the commit–reveal argument don't depend on block production, so they transfer unchanged. Throughput and latency don't transfer: on a real chain you add seconds of consensus delay. We say this explicitly in the paper.

**Isn't paying gas for every indicator expensive?**
At 64-way batching it is 337 gas per indicator, about 1.6% of a plain transfer. The trade-off is that indicators wait until a batch fills. Whether the fee level is acceptable depends on the chain, which is a deployment decision. We expect a consortium chain.

**Why is the hub so much faster?**
The hub stores records in memory and pays nothing per record. The chain includes transactions one at a time, so it saturates at a single ordering point, and extra writers just queue.

**What about an honest node that sees an attack late, after the hash was revealed?**
Time is split into epochs. A late observation is committed in the next epoch, so corroboration is delayed by at most one epoch, not lost. We did not measure the recall cost of a given epoch length; that is future work.

**What if a node is compromised before it anchors and posts a false hash?**
That is out of scope. The ledger records what a node committed to, not whether it was true.

**Can someone recover the indicator from its hash?**
Only hashes go on chain. For low-entropy values like an IP address, someone could hash guesses and confirm a match, so the hash hides content from a casual reader but not from a determined one. We don't claim confidentiality in the paper.
