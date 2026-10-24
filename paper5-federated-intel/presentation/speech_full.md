# ICOIICS 2026 talk script (full 25-slide version)

**Paper:** Hub-less Cross-Honeypot Threat Intelligence: Federated IOC Corroboration on a Shared Ledger (ICOIICS_245)
**Deck:** `ICOIICS_245_full_deck.pptx`. This script is also in each slide's speaker notes.
**Full length:** about 12 minutes at a steady pace (~140 words/min).

| Speaker | Slides | Part | Approx. time |
|---|---|---|---|
| **Speaker 1: Sisir Reddy Nellore** | 1 to 15 | Background, the problem, prior work, what makes us unique, how the design works | ~7 min 30 s |
| **Speaker 2: Suhas Reddy Annem** | 16 to 25 | Keying functions, attacks and the fix, results, conclusion | ~5 min 00 s |

**If your slot is only 5 to 6 minutes:** hide the slides marked **[SKIP IF SHORT]** in PowerPoint (right-click the slide thumbnail, then *Hide Slide*) and skip their lines. That leaves 14 slides and about 7 minutes. To get under 6, also drop the second paragraph on slides 6, 18, 20 and 24.

Lines in quote blocks are what you say. Notes in *italics* are cues and are not spoken.

---

## Slide 1: Title
**Speaker 1 (Sisir)** · ~25 s

> Good morning, everyone. I'm Sisir Reddy Nellore, and this is Suhas Reddy Annem. This work was done with our faculty advisor, Radhika G, at Amrita Vishwa Vidyapeetham, Coimbatore.
>
> Our paper is "Hub-less Cross-Honeypot Threat Intelligence." In simple words, it asks how security sensors owned by different organizations can share what they see about attacks, without all of them trusting one central server.

*Change "morning" to "afternoon" if needed.*

---

## Slide 2: Today's talk  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~20 s

> Here's the plan. I'll start with some background, then explain the problem we're solving, what earlier work has done, what makes our approach different, and how our design works. After that, Suhas will show how we handle varied attacks and cheating, and walk you through the results.

---

## Slide 3: What is a honeypot?  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~30 s

> First, what is a honeypot? It's a decoy computer. It looks like a real server, but it has no real users, so anyone who connects to it is almost certainly an attacker.
>
> The honeypot quietly records everything: where the attacker came from, what commands they typed, and what files they tried to download. That record is valuable evidence.

---

## Slide 4: What is an indicator of compromise?  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~35 s

> Each piece of that evidence is called an indicator of compromise, or IOC. It might be the attacker's IP address, the command they ran, or a session token their tool uses.
>
> Here's the key idea for this talk. If two honeypots in two different organizations see the same indicator, it is very likely the same attack campaign. Confirming an attack from more than one independent source is called corroboration.

---

## Slide 5: Each honeypot sees only one slice
**Speaker 1 (Sisir)** · ~30 s

> Why does that matter? Because attacks are rarely aimed at just one target. Botnets and mass scanners hit everyone they can reach.
>
> Each organization sees only its own piece. Organization A doesn't know that B and C are seeing the same thing. The full picture appears only when you combine their views.

---

## Slide 6: Today's fix: send everything to one hub
**Speaker 1 (Sisir)** · ~40 s

> Today, the standard way to combine views is a central hub: a threat-intelligence platform such as MISP, using the STIX and TAXII standards. Every sensor sends its data to one server, and that server does the matching.
>
> It works, but it creates three problems. Everyone has to trust the hub not to lose, change or hide their data. If the hub goes down, correlation stops. And it's a single, attractive target. For honeypots that's especially awkward: the decoys are meant to be attacked, but the hub is exposed to the same attackers.

---

## Slide 7: The problem we solve
**Speaker 1 (Sisir)** · ~35 s

> So here is the problem we solve: can honeypots run by organizations that don't trust each other spot shared attacks, without any central server?
>
> We set four requirements. There is no trusted middleman. A new honeypot can join at any time and catch up on its own. Fake or copied reports must not count as evidence. And the costs must be measured, not assumed.

---

## Slide 8: What others have built  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~40 s

> Others have worked on this. On the left are the central and federated platforms. MISP can federate, but its servers sync in pairs and new members have to be admitted. STIX and TAXII define a common data format and a client–server transport.
>
> On the right are blockchain-based designs: TRADE, TrustShare, the framework by Dunnett and colleagues, BFLS, and the trust-aware honeypot ledger by Otoum and colleagues. They all use a blockchain, but they also put a lot of logic on it.

---

## Slide 9: Where prior work falls short  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~35 s

> That is where they fall short for our problem. First, smart contracts for reputation, access and membership are extra code that everyone has to trust, and they make it hard to tell what the blockchain itself contributes.
>
> Second, joining usually needs permission or configuration. Third, the designs we compared against don't report measured fees, speed limits, or what happens when a participant cheats.

---

## Slide 10: Side-by-side with prior work
**Speaker 1 (Sisir)** · ~30 s

> This table, from our paper, puts it side by side. Central platforms need a trusted coordinator. Blockchain designs remove the coordinator, but they rely on on-chain logic, none of them lets a new node build its view from the ledger alone, and none reports measured attacks and costs.
>
> Ours is the only row that ticks all three, with no on-chain logic at all.

*Point at the highlighted last row.*

---

## Slide 11: What makes our paper unique
**Speaker 1 (Sisir)** · ~40 s

> So what makes this paper unique? One: we put nothing on the chain except fingerprints. No contracts, no registry, and no messages between nodes.
>
> Two: any newcomer rebuilds the full picture from the ledger history alone. Three: we define a new cheating attack, the echo attack, and block it with commit–reveal. And four: every number is measured on a live chain with up to 16 nodes, against a real centralized hub, and our cost formulas match the measurements exactly.

---

## Slide 12: Our idea: a shared notice board
**Speaker 1 (Sisir)** · ~35 s

> Here's the core idea as an analogy. Picture a public notice board that nobody owns and nothing can be erased from. Each honeypot pins up a fingerprint of what it saw, signed with its own name.
>
> If the same fingerprint shows up from several different honeypots, like the three highlighted here, that's a corroborated campaign. Let me show you how it works.

---

## Slide 13: Key tool: the hash, a data fingerprint  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~35 s

> The fingerprint is a hash, computed with SHA-256. You feed in any text, like this attack command, and you get back a fixed-length code.
>
> Three properties matter. The same input always gives the same hash, so two honeypots that see the same thing produce the same code. Change one character and the hash is completely different. And the hash doesn't show the original text, so we never put raw attack data on the ledger.

---

## Slide 14: Hub vs. our hub-less design
**Speaker 1 (Sisir)** · ~40 s

> Here are the two models side by side. On the left is the usual hub: raw data flows in, and the hub is the single point of trust and failure.
>
> On the right is our design. Each honeypot posts a small tag, its node ID plus the hash, to a shared, append-only ledger. There's no smart contract and no owner. Anyone reading the ledger can work out, for each hash, which nodes saw it. And P4, a node that joins later, rebuilds the same view from history.

*Point at the left half, then the right half, then P4.*

*Short version (slide 15 hidden): finish here with the handover line from the end of slide 15.*

---

## Slide 15: How it works, step by step  [SKIP IF SHORT]
**Speaker 1 (Sisir)** · ~35 s

> Step by step: a honeypot observes an attack. It normalizes the record, keeping only the fields that define "the same" indicator. It hashes that. It posts the tag, its ID plus the hash, to the ledger. Then any reader counts: if k or more different nodes posted the same hash, it is corroborated.
>
> Notice that no node ever talks to another. The ledger is the only thing they share.
>
> Now Suhas will take you through how we make this work against real, messy attacks, and what we measured.

*Hand over to Suhas.*

---

## Slide 16: Choosing what counts as "the same" IOC  [SKIP IF SHORT]
**Speaker 2 (Suhas)** · ~45 s

> Thanks, Sisir. Step two, normalizing, turns out to matter a lot. Real attackers change small details for each target: a session token here, a source IP there. So what counts as the same indicator? We tested four options, called keying functions.
>
> Hash the exact record and you're never wrong, but you miss varied attacks. Hash only the command, and common commands from unrelated attackers collide. Blank out tokens and IPs, which is the template, and you merge different campaigns that use the same tool. Or combine the attacker's /24 network with the template. We'll see the numbers shortly.

---

## Slide 17: A new threat: the echo attack  [SKIP IF SHORT]
**Speaker 2 (Suhas)** · ~35 s

> Now, a threat we identified. Because the board is public, a cheater can simply read it and re-post every fingerprint under its own name. Suddenly everything looks like it was seen by two honeypots.
>
> We call this the echo attack. In our test, it falsely corroborated all 120 single-node reports in about one second.

---

## Slide 18: Our fix: commit, then reveal
**Speaker 2 (Suhas)** · ~45 s

*Short version (slides 16 and 17 hidden): Suhas starts here with "Thanks, Sisir."*

> Our fix works like a sealed-bid auction. First, each node commits: it posts a salted hash that reveals nothing. Later, it reveals the salt and the hash. A reader counts a node only if its commitment came before anyone revealed that hash.
>
> The echo node only learns a hash from someone else's reveal, so it is always too late. The cost is two transactions per indicator instead of one. Honest nodes that see an attack late simply commit it in the next round, which we call an epoch.

---

## Slide 19: How we tested it  [SKIP IF SHORT]
**Speaker 2 (Suhas)** · ~35 s

> How did we test it? On a live Ethereum-compatible chain, Ganache, with 1 to 16 honeypot nodes writing at the same time, five repetitions each, and 95 percent confidence intervals. We also built a real centralized hub in the same test harness, so the comparison is fair.
>
> Eight experiments cover scaling, cost, bootstrap, accuracy, attacks, tamper detection, the hub baseline and propagation. One run of about three minutes produced every number in the paper.

---

## Slide 20: Throughput: ledger 255 vs. hub 1,737 events/s
**Speaker 2 (Suhas)** · ~40 s

> First, speed. The ledger, in green, levels off at about 255 events per second from eight writers onward, because the chain processes transactions one at a time. The hub, in red, reaches 1,737, which is 6.8 times faster.
>
> We report this openly: it is the measured price of removing the trusted middleman. Median latency stays around 12 milliseconds, but the slowest one percent grows to about a second once the chain is full.

---

## Slide 21: Cost matches the calldata model to the unit  [SKIP IF SHORT]
**Speaker 2 (Suhas)** · ~35 s

> Next, cost. Each indicator costs 22,120 gas, which is exactly what the Ethereum fee formula predicts. Batching 64 hashes under one Merkle root brings it down to 337 gas per indicator.
>
> And a new node catches up at about 3 milliseconds per block, growing in a straight line with the length of the history.

---

## Slide 22: No single keying function fits every campaign
**Speaker 2 (Suhas)** · ~45 s

> Accuracy depends on the keying function. Exact hashing is always correct, but it finds only 27.5 percent of campaigns that vary per target. The template key merges unrelated attacks and scores lowest, with an F1 of 0.15. The best was the /24 network plus template: 100 percent precision, 81 percent recall, and an F1 of 0.89.
>
> The lesson is that the ledger doesn't lock you into one key. Nodes can pick the one that suits their traffic, or post under several.

---

## Slide 23: Adversaries: what the scheme catches
**Speaker 2 (Suhas)** · ~40 s

> On security, commit–reveal cut the echo attack from 100 percent to zero, at twice the gas, and every genuinely shared hash was still corroborated.
>
> In a Sybil attack, one attacker creates many fake identities. Fake reports pass only if the attacker controls at least k identities, so this belongs on a permissioned chain. And when we edited records in a node's local log after posting, we caught 500 out of 500, with zero false alarms on 500 untouched records.

---

## Slide 24: What we showed
**Speaker 2 (Suhas)** · ~45 s

> To sum up: a ledger that carries only fingerprints can replace the central hub for honeypots that don't trust each other. Compared with prior work, we use no on-chain logic, newcomers need no permission to catch up, we defend against copied reports, and every cost is measured.
>
> Our limits: the test chain has no consensus delay, so real deployments will be slower. The accuracy data is synthetic, and Sybil resistance needs controlled identities. Next, we want to test on a real consortium chain, tune the epoch length, and use captured attack traffic.

---

## Slide 25: Thank you
**Speaker 2 (Suhas)** · ~10 s

> Thank you for listening. We're happy to take your questions.

---

## Q&A preparation (not part of the talk)

Short answers either speaker can give. All of them come from the paper.

**Do you outperform the other systems?**
Not on raw speed, and we don't claim to. A central hub is faster (6.8× in our own measurement). Our contribution is that we remove the trusted coordinator with zero on-chain logic, let a newcomer bootstrap from the ledger alone, defend against the echo attack, and measure all of it. The prior designs in our comparison table don't report measured cost or attack results.

**Why not just use MISP federation?**
MISP instances sync pairwise between administered servers, and a new participant has to be admitted before it receives anything. In our scheme there is no server to be introduced to: every node writes to one ledger and any reader reads it.

**Ganache isn't a real network. Do the results hold?**
Some do and some don't. Gas costs, the batching law, bootstrap cost per block, the accuracy trade-off, the Sybil bound and the commit–reveal argument don't depend on block production, so they transfer unchanged. Throughput and latency don't transfer: on a real chain you add seconds of consensus delay.

**Isn't paying gas for every indicator expensive?**
At 64-way batching it is 337 gas per indicator, about 1.6% of a plain transfer. The trade-off is that indicators wait until a batch fills. Whether the fee level is acceptable depends on the chain; we expect a consortium chain.

**What about an honest node that sees an attack late, after the hash was revealed?**
Time is split into epochs. A late observation is committed in the next epoch, so corroboration is delayed by at most one epoch, not lost. We did not measure the recall cost of a given epoch length; that is future work.

**What if a node is compromised before it posts, and posts a false hash?**
That is out of scope. The ledger records what a node committed to, not whether it was true.

**Can someone recover the indicator from its hash?**
Only hashes go on chain. For low-entropy values like an IP address, someone could hash guesses and confirm a match, so the hash hides content from a casual reader but not from a determined one. We don't claim confidentiality in the paper.
