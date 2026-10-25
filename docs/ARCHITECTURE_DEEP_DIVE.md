# Technical Architecture & Cyber Deception Engine Deep Dive

## 1. Executive Summary & Problem Formulation
Traditional low/medium-interaction honeypots (e.g., Cowrie, Kippo, Dionaea) suffer from deterministic behavior. Automated port scanners and adversary reconnaissance scripts can fingerprint and unmask static honeypots within a single TCP packet exchange through timing anomalies, invariant response banners, or missing command implementations.

This framework introduces a **hybrid 3-tier deception architecture** paired with **blockchain-anchored tamper-evident forensics** to achieve high realism at scale without introducing unbounded LLM inference latency.

---

## 2. The 3-Tier Dynamic Response Engine

```
                     Incoming Attacker Query / Command
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │ Tier 1: Static Fast-Path    │  < 0.5 ms
                      │ (Deterministic Dict Lookup) │  (Routine Linux / API commands)
                      └──────────────┬──────────────┘
                                     │ (Cache Miss)
                                     ▼
                      ┌─────────────────────────────┐
                      │ Tier 2: Redis In-Memory     │  ~ 1 - 2 ms
                      │ (SHA-256 Keyed Context)     │  (Session-Consistent Responses)
                      └──────────────┬──────────────┘
                                     │ (Cache Miss)
                                     ▼
                      ┌─────────────────────────────┐
                      │ Tier 3: Hosted LLM Engine   │  ~ 450 - 900 ms
                      │ (OpenRouter / LLaMA-3.1-8B) │  (Complex / Obfuscated Payloads)
                      └─────────────────────────────┘
```

### Response Tier Mechanics:
1. **Tier 1 (Static Fast-Path):** Over 80% of automated adversary probes involve standard reconnaissance (`ls`, `whoami`, `id`, `uname -a`, `netstat`). These are serviced directly from memory in $< 0.5\text{ ms}$, preventing LLM API quota exhaustion.
2. **Tier 2 (Context-Aware Cache):** Identical commands within a specific decoy protocol reuse cached responses with a 6-hour TTL (`CACHE_TTL_SECONDS = 21600`), ensuring session consistency and sub-2ms response times.
3. **Tier 3 (LLM Deception Fallback):** Novel, obfuscated, or custom commands fall back to an instruction-tuned LLM conditioned with specialized system prompts to emulate authentic Ubuntu/PostgreSQL/Ethereum nodes.

---

## 3. Cryptographic Proof of Integrity (Blockchain Commitment)

### Threat Model:
An advanced adversary gaining root access to the logging server or network infrastructure may attempt to erase command history, manipulate timestamps, or forge benign activity records to obstruct forensic investigations.

### Tamper-Evident Anchoring Protocol:
1. **Canonicalization:** Captured raw telemetry $E = \{\text{timestamp}, \text{service}, \text{ip}, \text{payload}\}$ is serialized into deterministic canonical JSON:
   $$\text{canonical\_bytes}(E) = \text{JSON}_{\text{sorted\_keys}}(E)$$
2. **Cryptographic Digest:**
   $$H(E) = \text{SHA-256}(\text{canonical\_bytes}(E))$$
3. **On-Chain Commitment:**
   The hex digest $H(E)$ is embedded into the `data` field of an Ethereum transaction directed to the contract account on Ganache/Ethereum:
   $$\text{tx} = \{\text{from}: A_{\text{miner}}, \text{to}: A_{\text{miner}}, \text{value}: 0, \text{data}: 0x || H(E)\}$$
4. **Third-Party Verification:**
   Any downstream auditor can recompute $H(E_{\text{audit}})$ and confirm its inclusion in an immutable Ethereum block. Any modification to a single character yields an invalid hash verification alert.

---

## 4. Multi-Protocol Decoy Surface

| Decoy Service | Internal Container | Public Port | Protocol Emulated | Target Vulnerability / Threat |
|---|---|---|---|---|
| **shadow-shell** | `decoys/shadow-shell` | `2222` | SSH v2 (asyncssh) | Credential stuffing, interactive shell RCE, sudoers privilege escalation |
| **vault-sql** | `decoys/vault-sql` | `5433` | PostgreSQL Wire | SQL injection, schema enumeration, financial data exfiltration |
| **oracle-ai** | `decoys/oracle-ai` | `8080` | REST API | Indirect prompt injection, jailbreaks, system prompt extraction |
| **ledger-trap** | `decoys/ledger-trap` | `8545` | Ethereum JSON-RPC | Unauthorized account unlocking, balance draining, contract theft |
| **forge-ci** | `decoys/forge-ci` | `9090` | Jenkins CI/CD | Pipeline script console RCE, cryptomining malware staging |
