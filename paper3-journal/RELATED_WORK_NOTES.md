# Verified related-work numbers for paper3 (tamper-evident audit trail)

Every citation below was checked against a real source via web search. Confirm
exact author/venue/year on Xplore/DOI before final submission.

## Directly comparable systems

- **BlockTrail** — Ahmad, Saad, Al Ghamdi, Nyang, Mohaisen, *IEEE Systems
  Journal*, 2022 (accepted 2021, doc 9528166). Secure/transparent
  blockchain-driven audit trails; fragments the chain into codependent
  hierarchies to cut space-time complexity and raise throughput; prototyped on
  PBFT. Motivation quote: audit-trail entities have "weak trust boundaries."
  URL: https://ieeexplore.ieee.org/document/9528166/

- **BlockTrail (multichain)** — Ahmad et al., IEEE conf, 2019 (doc 8761448).
  Scalable multichain audit trails.

- **Immutable Log Storage as a Service on Private and Public Blockchains** —
  arXiv:2009.07834. Hybrid on/off-chain; batches log hashes; targets both
  Ethereum (public) and private chains. Reports minimal per-batch overhead;
  block-confirmation latency dominates on public Ethereum (~seconds).
  URL: https://arxiv.org/abs/2009.07834

- **BCALS: Blockchain-based secure log management for cloud** — researchgate
  350947485. Permissioned-chain log management.

- **A secure and auditable logging infrastructure based on a permissioned
  blockchain** — *Computers & Security* (Elsevier), S0167404818313907.
  Hyperledger-style permissioned audit logging.

- **LogStamping** — arXiv:2505.17236. Blockchain-based log auditing for
  large-scale systems; hash-anchoring approach.

- **Framework for Blockchain-Based Access Logs and Tamper-Proof Audit Trails**
  — *IEEE Access*, vol. 7, pp. 115384–115393 (from search). Immutable
  access-event logs on-chain.

## Blockchain + honeypot (the intersection this paper sits in)

- **Next Generation Dynamic Distributed Honeypots System Based on Blockchain**
  — researchgate 372724368. Blockchain for distributed honeypot coordination.

- **Blockchain Meets Adaptive Honeypots: A Trust-Aware Approach to Next-Gen IoT
  Security** — arXiv:2504.16226. Trust-aware adaptive honeypots + blockchain.

- **Strategic Deployment of Honeypots in Blockchain-based IoT Systems** —
  researchgate 382410694.

- **Blockchain-enabled dynamic honeypot conversion for resource-efficient IoT
  security** — ScienceDirect S2214212625001462.

  NOTE: Most honeypot+blockchain work uses blockchain to COORDINATE distributed
  honeypots or for IoT trust — NOT to make the honeypot's own captured evidence
  tamper-evident against an attacker who has already compromised the decoy.
  That evidence-integrity threat model is this paper's gap/contribution.

## Verified gas grounding (makes our 21,488–21,512 measurement defensible)

- Base Ethereum tx = **21,000 gas** (fixed). Input data ~16 gas/byte
  (non-zero), 4 gas/byte (zero). LOG opcode base = 375 gas + 375/topic + 8
  gas/byte of data. ERC-20 transfer+log ~40k–60k gas.
  Sources: web3.university, bitquery gas analysis, Ethereum yellow paper.
  => Our measured mean 21,510 gas = 21,000 base + SHA-256 data bytes. Exactly
     as expected for a minimal-payload anchor tx. Real and defensible.

## Framing contrast for our Results/Comparison

- Public-Ethereum logging systems are bottlenecked by ~12–16 s block
  confirmation; they batch to amortize. Our Ganache (dev/PoA-style instant
  mining) anchors in ~10.8 ms/event because there is no public-consensus wait —
  we MUST state this honestly: our latency reflects a local/permissioned
  Ethereum, not public mainnet. The contribution is the pipeline + threat model
  + 100% tamper detection, not "faster than mainnet."
