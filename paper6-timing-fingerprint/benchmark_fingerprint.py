"""
Attacker-side fingerprintability benchmark for the multi-protocol LLM honeypot.

Every number in fingerprint_results.json is measured live against
  decoys (via the proxy): SSH :2222, JSON-RPC :8545, CI/HTTP :9090
  real counterparts:      OpenSSH :2200, Ganache :7545, Jenkins :8090
  ai-engine directly:     :8000 (tier exposure over the attack corpus)
  Redis (compose container, via docker exec) to classify cache hits

Run with /usr/bin/python3 after the stack and the three real services are up
(see README.md).

E1  Protocol conformance: deterministic probes whose observable answer differs
    between decoy and real service (static fingerprints).
E2  Timing: response-latency distributions per tier (static / cache / LLM) on
    the decoys versus the same probes on the real services; AUC of a
    single-observation latency classifier; sessions of k commands.
E3  Tier exposure: the 2,500-payload attack corpus replayed through the
    response engine; which tier answered and how long it took.
E4  Mitigation analysis: normalized cache keys (cross-payload reuse), and
    the residual exposure after pre-warming.
"""
import asyncio
import concurrent.futures as cf
import hashlib
import json
import math
import random
import re
import statistics
import time
from pathlib import Path

import subprocess

import asyncssh
import requests

ROOT = Path(__file__).parent
CORPUS = ROOT.parent / "apt_attack_dataset.json"
OUT = ROOT / "fingerprint_results.json"

DECOY_SSH, REAL_SSH = 2222, 2200
DECOY_RPC, REAL_RPC = "http://127.0.0.1:8545", "http://127.0.0.1:7545"
DECOY_CI, REAL_CI = "http://127.0.0.1:9090", "http://127.0.0.1:8090"
ENGINE = "http://127.0.0.1:8000/api/response"
TRIALS = 30
CORPUS_CONCURRENCY = 8

STATIC_SSH = ['ls', 'whoami', 'uname -a', 'id', 'pwd', 'clear', 'ip a', 'netstat -tulpn', 'arp -a',
              'cat /etc/passwd', 'cat /etc/os-release', 'history', 'uptime', 'ifconfig', 'ps aux', 'env',
              'id -a', 'hostname', 'date', 'which python3', 'which python', 'python3 --version', 'df -h',
              'free -h', 'cat /etc/hostname', 'lsb_release -a', 'uname -r', 'who', 'w', 'sudo -l']


def stats(xs):
    if not xs:
        return {}
    s = sorted(xs); n = len(s)
    sd = statistics.stdev(s) if n > 1 else 0.0
    return {"n": n, "mean": round(statistics.mean(s), 3), "median": round(statistics.median(s), 3),
            "p5": round(s[max(0, int(0.05 * n) - 1)], 3), "p95": round(s[min(n - 1, int(math.ceil(0.95 * n)) - 1)], 3),
            "min": round(s[0], 3), "max": round(s[-1], 3), "stdev": round(sd, 3)}


def auc(pos, neg):
    """P(decoy latency > real latency), i.e. AUC of a threshold detector."""
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > r else 0.5 if p == r else 0.0 for p in pos for r in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def best_threshold(pos, neg):
    """Single-threshold accuracy (decoy if latency > t or < t, whichever is better)."""
    vals = sorted(set(pos + neg)); best = (0.0, None, None)
    for t in vals:
        for direction in ("gt", "lt"):
            tp = sum((p > t) if direction == "gt" else (p < t) for p in pos)
            tn = sum((r <= t) if direction == "gt" else (r >= t) for r in neg)
            acc = (tp + tn) / (len(pos) + len(neg))
            if acc > best[0]:
                best = (acc, t, direction)
    return {"accuracy": round(best[0], 4), "threshold_ms": round(best[1], 3) if best[1] is not None else None,
            "decoy_if": best[2]}


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------
class Shell:
    def __init__(self, port, user, pw, prompt_re, prompt_line, setup=None):
        self.port, self.user, self.pw, self.prompt_re, self.setup = port, user, pw, prompt_re, setup
        self.prompt_line = prompt_line
        self.info = {}

    async def __aenter__(self):
        t0 = time.perf_counter()
        self.conn = await asyncssh.connect("127.0.0.1", port=self.port, username=self.user, password=self.pw,
                                           known_hosts=None)
        self.info["auth_ms"] = (time.perf_counter() - t0) * 1000
        self.info["banner"] = self.conn.get_extra_info("server_version")
        self.proc = await self.conn.create_process(term_type="xterm")
        await self._until(rx=r"[$#>] $")   # default prompt, before any PS1 setup
        if self.setup:
            self.proc.stdin.write(self.setup + "\n"); await self._until()
        return self

    async def _until(self, timeout=90, rx=None):
        rx = rx or self.prompt_re
        buf = ""; t = time.perf_counter()
        while time.perf_counter() - t < timeout:
            try:
                buf += await asyncio.wait_for(self.proc.stdout.read(65536), timeout=0.2)
            except asyncio.TimeoutError:
                pass
            if re.search(rx, re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", buf)):
                return buf
        return buf

    async def cmd(self, c):
        t = time.perf_counter()
        self.proc.stdin.write(c + "\n")
        out = await self._until()
        ms = (time.perf_counter() - t) * 1000
        out = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", out)
        out = out.replace("\r", "")
        lines = out.split("\n")[1:]  # drop the echoed command
        lines = [ln for ln in lines if not re.search(self.prompt_line, ln)]
        return ms, "\n".join(lines).strip()

    async def __aexit__(self, *a):
        self.conn.close()


def decoy_shell():
    return Shell(DECOY_SSH, "root", "toor", r"dbadmin@corp-prod-db-01:[^\n]*\$ $", r"^dbadmin@corp-prod-db-01:.*\$ ?$")


def real_shell():
    return Shell(REAL_SSH, "dbadmin", "dbadmin123", r"PROMPT> $", r"^PROMPT> ?$", setup="PS1='PROMPT> '")


async def ssh_algorithms(port):
    """Server algorithm lists as seen by a client during KEX."""
    conn = await asyncssh.connect("127.0.0.1", port=port, username="dbadmin", password="dbadmin123",
                                  known_hosts=None) if port == REAL_SSH else \
        await asyncssh.connect("127.0.0.1", port=port, username="root", password="x", known_hosts=None)
    hk = getattr(conn, "_server_host_key", None)
    info = {"server_version": conn.get_extra_info("server_version"),
            "host_key_alg": hk.algorithm if hk is not None else None,
            "cipher": conn.get_extra_info("send_cipher"), "mac": conn.get_extra_info("send_mac")}
    conn.close()
    return {k: (v.decode() if isinstance(v, bytes) else v) for k, v in info.items()}


async def ssh_accepts_any_credentials(port):
    try:
        conn = await asyncssh.connect("127.0.0.1", port=port, username="nosuchuser%08x" % random.getrandbits(32),
                                      password="%016x" % random.getrandbits(64), known_hosts=None)
        conn.close(); return True
    except asyncssh.PermissionDenied:
        return False
    except Exception as e:
        return f"error: {type(e).__name__}"


async def ssh_exec_channel(port, user, pw):
    """Does the server honour an exec request (ssh host cmd) rather than only a shell?"""
    try:
        conn = await asyncssh.connect("127.0.0.1", port=port, username=user, password=pw, known_hosts=None)
        r = await asyncio.wait_for(conn.run("echo EXEC_OK", check=False), timeout=20)
        conn.close()
        return {"supported": "EXEC_OK" in (r.stdout or ""), "stdout": (r.stdout or "")[:80], "exit_status": r.exit_status}
    except Exception as e:
        return {"supported": False, "error": type(e).__name__}


# ---------------------------------------------------------------------------
# E1  conformance
# ---------------------------------------------------------------------------
async def e1_conformance():
    rows = []

    # --- SSH
    d_alg, r_alg = await ssh_algorithms(DECOY_SSH), await ssh_algorithms(REAL_SSH)
    rows.append({"service": "ssh", "probe": "protocol banner", "decoy": d_alg["server_version"], "real": r_alg["server_version"]})
    rows.append({"service": "ssh", "probe": "host-key type offered", "decoy": d_alg["host_key_alg"], "real": r_alg["host_key_alg"]})
    rows.append({"service": "ssh", "probe": "cipher negotiated (same client)", "decoy": d_alg["cipher"], "real": r_alg["cipher"]})
    rows.append({"service": "ssh", "probe": "random credentials accepted", "decoy": await ssh_accepts_any_credentials(DECOY_SSH), "real": await ssh_accepts_any_credentials(REAL_SSH)})
    rows.append({"service": "ssh", "probe": "exec request honored", "decoy": (await ssh_exec_channel(DECOY_SSH, "root", "x"))["supported"], "real": (await ssh_exec_channel(REAL_SSH, "dbadmin", "dbadmin123"))["supported"]})
    probes = [("shell arithmetic $((7*6))", "echo $((7*6))"), ("missing-file error format", "cat /etc/nosuchfile"),
              ("unknown command error format", "frobnicate --version"), ("pwd after cd /tmp", "cd /tmp; pwd"),
              ("hostname vs uname -n consistency", "hostname; uname -n"), ("echo of quoted string", "echo 'a  b'")]
    async with decoy_shell() as d, real_shell() as r:
        for name, c in probes:
            _, do = await d.cmd(c); _, ro = await r.cmd(c)
            rows.append({"service": "ssh", "probe": name, "decoy": do[:120], "real": ro[:120]})

    # --- JSON-RPC
    def rpc(url, body, raw=False):
        try:
            resp = requests.post(url, data=body if raw else json.dumps(body), headers={"content-type": "application/json"}, timeout=60)
            try:
                return resp.status_code, resp.json()
            except ValueError:
                return resp.status_code, resp.text[:120]
        except Exception as e:
            return None, type(e).__name__

    def shape(x):
        if isinstance(x, dict):
            keys = sorted(x.keys())
            err = x.get("error")
            return f"keys={keys}" + (f" error.code={err.get('code') if isinstance(err, dict) else err}" if err is not None else "")
        return f"{type(x).__name__}:{str(x)[:60]}"

    rpc_probes = [
        ("web3_clientVersion", {"jsonrpc": "2.0", "method": "web3_clientVersion", "params": [], "id": 1}, lambda s, j: str(j.get("result") if isinstance(j, dict) else j)[:60]),
        ("eth_chainId", {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}, lambda s, j: str(j.get("result") if isinstance(j, dict) else j)[:40]),
        ("unknown method -> error code", {"jsonrpc": "2.0", "method": "eth_noSuchMethod", "params": [], "id": 1}, lambda s, j: shape(j)),
        ("malformed JSON body", "{not json", lambda s, j: f"http={s} " + shape(j)),
        ("string id echoed as string", {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": "abc"}, lambda s, j: repr(j.get("id")) if isinstance(j, dict) else shape(j)),
        ("batch request (array)", [{"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}, {"jsonrpc": "2.0", "method": "net_version", "params": [], "id": 2}], lambda s, j: f"http={s} " + ("list[%d]" % len(j) if isinstance(j, list) else shape(j))),
        ("eth_getBalance without params", {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [], "id": 1}, lambda s, j: shape(j)),
        ("eth_blockNumber monotonic (two calls)", None, None),
        ("eth_getBlockByNumber latest -> field count", {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}, lambda s, j: (f"{len(j['result'])} fields" if isinstance(j, dict) and isinstance(j.get("result"), dict) else shape(j))),
    ]
    for name, body, view in rpc_probes:
        if body is None:
            def mono(url):
                a = rpc(url, {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1})[1]
                b = rpc(url, {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1})[1]
                ra, rb = (a.get("result"), b.get("result")) if isinstance(a, dict) and isinstance(b, dict) else (None, None)
                if ra is None or rb is None:
                    return "no result"
                return "advances" if int(rb, 16) > int(ra, 16) else "constant"
            rows.append({"service": "rpc", "probe": name, "decoy": mono(DECOY_RPC), "real": mono(REAL_RPC)})
            continue
        raw = isinstance(body, str)
        sd, jd = rpc(DECOY_RPC, body, raw); sr, jr = rpc(REAL_RPC, body, raw)
        rows.append({"service": "rpc", "probe": name, "decoy": view(sd, jd), "real": view(sr, jr)})

    # --- CI / HTTP
    def http(url, method="GET", path="/", data=None):
        try:
            r = requests.request(method, url + path, data=data, timeout=60, allow_redirects=False)
            return r
        except Exception as e:
            return None

    def hdr(r, names):
        if r is None:
            return "no response"
        return f"http={r.status_code} " + " ".join(f"{n}={r.headers.get(n, '-')}" for n in names)

    ci_probes = [
        ("GET / -> status, Server, X-Jenkins", "GET", "/", None, lambda r: hdr(r, ["Server", "X-Jenkins", "X-Hudson"])),
        ("GET /api/json -> status, content-type, top-level keys", "GET", "/api/json", None,
         lambda r: "no response" if r is None else f"http={r.status_code} ct={r.headers.get('content-type','-').split(';')[0]} keys=" + (str(sorted(r.json().keys())[:6]) if r.headers.get('content-type','').startswith('application/json') else "n/a")),
        ("GET /nonexistent -> status, Server", "GET", "/nonexistent-%08x" % random.getrandbits(32), None, lambda r: hdr(r, ["Server"])),
        ("GET /login -> status", "GET", "/login", None, lambda r: hdr(r, ["Server"])),
        ("HEAD / -> status", "HEAD", "/", None, lambda r: hdr(r, ["Server"])),
        ("GET /robots.txt -> status", "GET", "/robots.txt", None, lambda r: hdr(r, [])),
        ("POST /job/build/api/json -> status", "POST", "/job/build/api/json", "{}", lambda r: hdr(r, ["Server"])),
        ("GET /api/json?depth=0 -> repeated call identical?", None, None, None, None),
    ]
    for name, m, p, data, view in ci_probes:
        if m is None:
            def twice(url):
                a = http(url, "GET", "/api/json"); b = http(url, "GET", "/api/json")
                if a is None or b is None:
                    return "no response"
                return "identical" if a.text == b.text else f"differs ({len(a.text)} vs {len(b.text)} bytes)"
            rows.append({"service": "ci", "probe": name, "decoy": twice(DECOY_CI), "real": twice(REAL_CI)})
            continue
        rows.append({"service": "ci", "probe": name, "decoy": view(http(DECOY_CI, m, p, data)), "real": view(http(REAL_CI, m, p, data))})

    for r in rows:
        r["distinguishing"] = str(r["decoy"]) != str(r["real"])
        print(f"  E1 {r['service']:4s} {r['probe'][:44]:44s} decoy={str(r['decoy'])[:40]!r:44s} real={str(r['real'])[:40]!r} {'DIFF' if r['distinguishing'] else 'same'}")
    return rows


# ---------------------------------------------------------------------------
# E2  timing
# ---------------------------------------------------------------------------
async def e2_timing_ssh():
    out = {}
    # SSH: auth, static tier, cache tier, LLM tier vs real
    d_auth, r_auth = [], []
    d_static, r_static, d_cache, r_cache, d_llm, r_llm = [], [], [], [], [], []
    d_session, r_session = [], []  # 5-command recon session wall time
    recon = ["whoami", "id", "uname -a", "cat /etc/passwd", "ps aux"]
    d_repeat_same_session = []
    for i in range(TRIALS):
        novel = f"cat /var/log/app-{random.getrandbits(32):08x}.log"
        static_cmd = random.choice(STATIC_SSH)
        async with decoy_shell() as d:
            d_auth.append(d.info["auth_ms"])
            ms, _ = await d.cmd(static_cmd); d_static.append(ms)
            ms, _ = await d.cmd(novel); d_llm.append(ms)
            ms, _ = await d.cmd(novel); d_repeat_same_session.append(ms)   # key includes history: not a hit
            t = time.perf_counter()
            for c in recon:
                await d.cmd(c)
            d_session.append((time.perf_counter() - t) * 1000)
        async with decoy_shell() as d2:   # fresh session, same history -> Redis hit
            await d2.cmd(static_cmd)
            ms, _ = await d2.cmd(novel); d_cache.append(ms)
        async with real_shell() as r:
            r_auth.append(r.info["auth_ms"])
            ms, _ = await r.cmd(static_cmd); r_static.append(ms)
            ms, _ = await r.cmd(novel); r_llm.append(ms)
            t = time.perf_counter()
            for c in recon:
                await r.cmd(c)
            r_session.append((time.perf_counter() - t) * 1000)
        async with real_shell() as r2:
            await r2.cmd(static_cmd)
            ms, _ = await r2.cmd(novel); r_cache.append(ms)
        print(f"  E2 ssh trial {i}: static {d_static[-1]:.1f}/{r_static[-1]:.1f}  llm {d_llm[-1]:.0f}/{r_llm[-1]:.1f}  cache {d_cache[-1]:.1f}/{r_cache[-1]:.1f}  same-session repeat {d_repeat_same_session[-1]:.0f}  auth {d_auth[-1]:.0f}/{r_auth[-1]:.0f}")
    out["ssh"] = {}
    for name, dv, rv in (("auth", d_auth, r_auth), ("static", d_static, r_static), ("cache", d_cache, r_cache),
                         ("llm", d_llm, r_llm), ("session5", d_session, r_session)):
        out["ssh"][name] = {"decoy": stats(dv), "real": stats(rv), "auc": auc(dv, rv), "threshold": best_threshold(dv, rv)}
    out["ssh"]["repeat_same_session"] = {"decoy": stats(d_repeat_same_session),
                                         "note": "same command repeated in the same session; cache key includes history so this is a model call"}

    return out["ssh"]


async def e2_timing():
    out = {}
    out["ssh"] = await e2_timing_ssh()
    # JSON-RPC
    def rpc_ms(url, body):
        t = time.perf_counter(); requests.post(url, json=body, timeout=60); return (time.perf_counter() - t) * 1000
    ds, rs, dl, rl, dc, rc = [], [], [], [], [], []
    for i in range(TRIALS):
        static_body = {"jsonrpc": "2.0", "method": random.choice(["eth_blockNumber", "net_version", "eth_accounts"]), "params": [], "id": 1}
        novel_body = {"jsonrpc": "2.0", "method": "eth_getStorageAt", "params": ["0x%040x" % random.getrandbits(160), "0x0", "latest"], "id": 1}
        ds.append(rpc_ms(DECOY_RPC, static_body)); rs.append(rpc_ms(REAL_RPC, static_body))
        dl.append(rpc_ms(DECOY_RPC, novel_body)); rl.append(rpc_ms(REAL_RPC, novel_body))
        dc.append(rpc_ms(DECOY_RPC, novel_body)); rc.append(rpc_ms(REAL_RPC, novel_body))
    out["rpc"] = {n: {"decoy": stats(a), "real": stats(b), "auc": auc(a, b), "threshold": best_threshold(a, b)}
                  for n, a, b in (("static", ds, rs), ("llm", dl, rl), ("cache", dc, rc))}
    print(f"  E2 rpc static {statistics.mean(ds):.1f}/{statistics.mean(rs):.1f} llm {statistics.mean(dl):.0f}/{statistics.mean(rl):.1f} cache {statistics.mean(dc):.1f}/{statistics.mean(rc):.1f}")

    # CI / HTTP
    def http_ms(url, method, path, data=None):
        t = time.perf_counter(); requests.request(method, url + path, data=data, timeout=60, allow_redirects=False); return (time.perf_counter() - t) * 1000
    di, ri, dp, rp, dn, rn = [], [], [], [], [], []
    for i in range(TRIALS):
        di.append(http_ms(DECOY_CI, "GET", "/api/json")); ri.append(http_ms(REAL_CI, "GET", "/api/json"))
        body = json.dumps({"parameter": [{"name": "BRANCH", "value": "feat-%08x" % random.getrandbits(32)}]})
        dp.append(http_ms(DECOY_CI, "POST", "/job/build/api/json", body)); rp.append(http_ms(REAL_CI, "POST", "/job/build/api/json", body))
        dn.append(http_ms(DECOY_CI, "GET", "/static-%08x" % random.getrandbits(32))); rn.append(http_ms(REAL_CI, "GET", "/static-%08x" % random.getrandbits(32)))
    out["ci"] = {n: {"decoy": stats(a), "real": stats(b), "auc": auc(a, b), "threshold": best_threshold(a, b)}
                 for n, a, b in (("api_json_llm", di, ri), ("build_post_llm", dp, rp), ("unknown_path_static", dn, rn))}
    print(f"  E2 ci api/json {statistics.mean(di):.0f}/{statistics.mean(ri):.1f} build {statistics.mean(dp):.0f}/{statistics.mean(rp):.1f} 404 {statistics.mean(dn):.1f}/{statistics.mean(rn):.1f}")
    return out


# ---------------------------------------------------------------------------
# E3  tier exposure over the corpus
# ---------------------------------------------------------------------------
def engine_static_match(service, cmd):
    if service != "ssh":
        return False
    c = cmd.strip()
    return c in STATIC_SSH or c.startswith(("sudo ", "cd ", "mkdir ", "touch ", "rm ", "export ", "echo "))


def cache_key(service, cmd):
    return f"{service}:" + hashlib.md5(cmd.strip().encode()).hexdigest()


DOCKER = "/Applications/Docker.app/Contents/Resources/bin/docker"


def engine_cache_keys():
    """Snapshot of the engine's Redis keys (the compose instance, not the host one)."""
    out = subprocess.run([DOCKER, "exec", "code-redis-1", "redis-cli", "--scan"], capture_output=True, text=True, check=True).stdout
    return set(out.split())


def e3_corpus():
    corpus = json.loads(CORPUS.read_text())
    sess = requests.Session()
    keys = engine_cache_keys()

    def one(item):
        svc, cmd = item["service"], item["command"]
        tier = "static" if engine_static_match(svc, cmd) else ("cache" if cache_key(svc, cmd) in keys else "llm")
        t = time.perf_counter()
        try:
            resp = sess.post(ENGINE, json={"command": cmd, "history": [], "service": svc}, timeout=120)
            ok = resp.status_code == 200
        except Exception:
            ok = False
        return svc, tier, (time.perf_counter() - t) * 1000, ok

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=CORPUS_CONCURRENCY) as ex:
        res = list(ex.map(one, corpus))
    wall = time.perf_counter() - t0
    by = {}
    for svc, tier, ms, ok in res:
        by.setdefault(svc, {}).setdefault(tier, []).append(ms)
    summary = {svc: {tier: {"count": len(v), "latency_ms": stats(v)} for tier, v in tiers.items()} for svc, tiers in by.items()}
    overall = {}
    for tier in ("static", "cache", "llm"):
        v = [ms for svc, t, ms, ok in res if t == tier]
        overall[tier] = {"count": len(v), "share": round(len(v) / len(res), 4), "latency_ms": stats(v)}
    failed = sum(1 for x in res if not x[3])
    print(f"  E3 first pass: {overall} failed={failed} wall={wall:.0f}s")

    # second pass on a sample: every payload is now a cache hit (exact key)
    sample = random.Random(7).sample(corpus, 300)
    keys.clear(); keys.update(engine_cache_keys())
    res2 = []
    with cf.ThreadPoolExecutor(max_workers=CORPUS_CONCURRENCY) as ex:
        res2 = list(ex.map(one, sample))
    second = {}
    for tier in ("static", "cache", "llm"):
        v = [ms for svc, t, ms, ok in res2 if t == tier]
        second[tier] = {"count": len(v), "share": round(len(v) / len(res2), 4), "latency_ms": stats(v)}
    print(f"  E3 second pass (300): {second}")
    return {"n": len(res), "failed": failed, "wall_s": round(wall, 1), "concurrency": CORPUS_CONCURRENCY,
            "first_pass": overall, "by_service": summary, "second_pass_sample": second}


# ---------------------------------------------------------------------------
# E4  mitigation analysis: normalized cache keys
# ---------------------------------------------------------------------------
NONCE = re.compile(r"\s*(#[0-9a-f]{8}|/\*[0-9a-f]{8}\*/)\s*$")


def normalize(cmd):
    c = NONCE.sub("", cmd)
    c = re.sub(r"\s+", " ", c.strip())
    c = re.sub(r"0x[0-9a-fA-F]{8,}", "0xHEX", c)
    c = re.sub(r"\b\d{4,}\b", "N", c)
    return c


def e4_mitigation():
    corpus = json.loads(CORPUS.read_text())
    rng = random.Random(11)
    idx = list(range(len(corpus))); rng.shuffle(idx)
    half = len(idx) // 2
    warm, test = [corpus[i] for i in idx[:half]], [corpus[i] for i in idx[half:]]
    exact_warm = {cache_key(x["service"], x["command"]) for x in warm}
    norm_warm = {(x["service"], normalize(x["command"])) for x in warm}
    exact_hits = sum(1 for x in test if cache_key(x["service"], x["command"]) in exact_warm)
    norm_hits = sum(1 for x in test if (x["service"], normalize(x["command"])) in norm_warm)
    distinct_exact = len({cache_key(x["service"], x["command"]) for x in corpus})
    distinct_norm = len({(x["service"], normalize(x["command"])) for x in corpus})
    by_svc = {}
    for svc in sorted({x["service"] for x in corpus}):
        tw = {normalize(x["command"]) for x in warm if x["service"] == svc}
        tt = [x for x in test if x["service"] == svc]
        by_svc[svc] = {"test": len(tt), "normalized_hits": sum(1 for x in tt if normalize(x["command"]) in tw)}
    res = {"corpus": len(corpus), "distinct_exact_keys": distinct_exact, "distinct_normalized_keys": distinct_norm,
           "split_warm": len(warm), "split_test": len(test), "exact_key_hits": exact_hits,
           "normalized_key_hits": norm_hits, "exact_hit_rate": round(exact_hits / len(test), 4),
           "normalized_hit_rate": round(norm_hits / len(test), 4), "by_service": by_svc}
    print(f"  E4 {res}")
    return res


def main():
    t0 = time.perf_counter()
    random.seed(3)
    print("[E1] conformance"); e1 = asyncio.run(e1_conformance())
    print("[E2] timing");      e2 = asyncio.run(e2_timing())
    print("[E4] mitigation");  e4 = e4_mitigation()
    print("[E3] corpus");      e3 = e3_corpus()
    banner = {}
    try:
        banner["real_ssh"] = e1[0]["real"]; banner["decoy_ssh"] = e1[0]["decoy"]
    except Exception:
        pass
    results = {"meta": {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "trials": TRIALS,
                        "runtime_s": round(time.perf_counter() - t0, 1),
                        "real_rpc": requests.post(REAL_RPC, json={"jsonrpc": "2.0", "method": "web3_clientVersion", "params": [], "id": 1}).json().get("result"),
                        "real_ci_server": requests.get(REAL_CI + "/", allow_redirects=False).headers.get("Server"),
                        "real_ci_version": requests.get(REAL_CI + "/", allow_redirects=False).headers.get("X-Jenkins"),
                        **banner},
               "e1_conformance": e1, "e2_timing": e2, "e3_corpus": e3, "e4_mitigation": e4}
    OUT.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUT} ({results['meta']['runtime_s']} s)")


def rerun_ssh_timing():
    """Re-measure the SSH block of E2 and merge it into an existing results file."""
    F = json.loads(OUT.read_text())
    async def only_ssh():
        global TRIALS
        res = await e2_timing_ssh()
        return res
    F["e2_timing"]["ssh"] = asyncio.run(only_ssh())
    F["meta"]["ssh_timing_rerun"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    OUT.write_text(json.dumps(F, indent=2))
    print("merged SSH timing into", OUT)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--ssh-timing":
        rerun_ssh_timing()
    else:
        main()
