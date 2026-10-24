from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio, json, os, hashlib, time
import redis as redis_lib
from web3 import Web3
from datetime import datetime
import httpx

import ai_classifier

app = FastAPI(title="Honeypot API")

_verdict_http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def _init_verdict_client():
    global _verdict_http_client
    _verdict_http_client = httpx.AsyncClient()


@app.on_event("shutdown")
async def _close_verdict_client():
    if _verdict_http_client is not None:
        await _verdict_http_client.aclose()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis_lib.from_url(os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:6379"), decode_responses=True)

# Blockchain connection
GANACHE_URL = os.getenv("GANACHE_URL", "http://localhost:7545")
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

connected_clients: list[WebSocket] = []

def hash_log(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()

def anchor_blockchain(log_hash: str):
    try:
        if w3.is_connected():
            account = w3.eth.accounts[0]
            w3.eth.send_transaction({
                "from": account,
                "to": account,
                "value": 0,
                "data": w3.to_bytes(hexstr="0x" + log_hash),
                "gas": 50000,
            })
            return True
    except Exception as e:
        print(f"Blockchain error: {e}")
    return False

def classify_intent(raw) -> str:
    d = str(raw).lower()

    # SQL injection — expanded to catch the compact sqlmap-style payloads
    # (admin'--, ' or '1'='1, stacked queries, error-based extractvalue, etc.)
    if any(x in d for x in [
        "select ", "' or", "\" or", "union select", "union all", "drop table",
        "1=1", "'1'='1", "insert into", "'--", "';--", "; drop", "or 1 --",
        "extractvalue", "updatexml", "information_schema", "sleep(", "benchmark(",
        "waitfor delay", "load_file", "into outfile", "xp_cmdshell",
    ]):
        return "sql_injection"

    # Prompt injection / LLM jailbreak — checked before privilege/recon so an
    # AI-decoy jailbreak isn't misfiled on an incidental keyword.
    if any(x in d for x in [
        "ignore previous", "ignore all previous", "jailbreak", "pretend you",
        "you are now", "act as", "developer mode", "dan mode", "system:",
        "new directive", "override", "reveal your", "system prompt",
        "unrestricted ai", "forget you are", "disregard",
    ]):
        return "prompt_injection"

    # Crypto theft — abusive Ethereum JSON-RPC methods documented in real
    # "exposed node" incidents: draining, unlocking wallets, signing,
    # planting malicious peers, forcing mining to an attacker address.
    if any(x in d for x in [
        "personal_unlockaccount", "personal_sendtransaction", "eth_sendtransaction",
        "eth_sendrawtransaction", "eth_sign", "admin_addpeer", "admin_startrpc",
        "miner_start", "miner_setetherbase", "txpool_content", "eth_getbalance",
        "eth_accounts", "eth_getstorageat",
    ]):
        return "crypto_theft"

    # Cryptomining payloads (miner binaries / pools) — before reverse_shell so a
    # "wget xmrig" reads as mining rather than a generic download.
    if any(x in d for x in [
        "xmrig", "miner", "monero", "cryptonight", "stratum", "minerd",
        "coinhive", "/tmp/kworker", "kdevtmpfsi", "kinsing",
    ]):
        return "cryptomining"

    # Reverse shell / remote code execution / malware staging
    if any(x in d for x in [
        "wget ", "curl ", "nc ", "ncat", "bash -i", "sh -i", "python -c",
        "python3 -c", "/bin/sh", "/bin/bash", "socket.socket", "pty.spawn",
        "/dev/tcp/", "mkfifo", "|bash", "| bash", "|sh", "| sh", "powershell",
        "certutil", "base64 -d", "${jndi", "runtime.getruntime",
    ]):
        return "reverse_shell"

    # Privilege escalation / credential & secret access
    if any(x in d for x in [
        "sudo", "/etc/shadow", "/etc/passwd", "chmod 777", "chmod +s", "passwd",
        "privilege", "setuid", "id -a", "cat /etc/", "master.key", "id_rsa",
        ".ssh/", "secrets/", "/root/",
    ]):
        return "privilege_escalation"

    # Supply-chain / CI-CD abuse (Jenkins script console, job/pipeline abuse,
    # malicious webhook triggers, plugin injection)
    if any(x in d for x in [
        "git push", "pipeline", "jenkins", "build trigger", "webhook",
        "notifycommit", "/script", "scripttext", "malicious-repo", "installnecessaryplugins",
        ".hpi", "config.xml", "groovy", "job/build",
    ]):
        return "supply_chain"

    # SSH/DB brute-force and password-spray login attempts (the honeypot logs
    # each try as "LOGIN:user:pass") — grouped under credential/privilege abuse.
    if d.startswith("login:") or "brute" in d or "password spray" in d:
        return "privilege_escalation"

    # Reconnaissance / enumeration — active scanning tools, the proxy's own
    # "new connection" probe logs, Jenkins/API info requests, and the classic
    # SSH enumeration commands attackers run first on a fresh shell.
    if any(x in d for x in [
        "nmap", "masscan", "scan", "ping sweep", "port scan", "new connection",
        "info_request", "list_models", "/api/json", "/api/models", "whoami",
        "uname", "hostname", "ifconfig", "ip a", "netstat", "ps aux", "arp",
        "history", "lsb_release", "net_version", "web3_clientversion",
        "net_peercount", "eth_blocknumber", "cat /", "ls -", "ls /",
    ]):
        return "reconnaissance"

    # Bare single-word enumeration commands — matched as the whole payload so a
    # substring like "id" inside a larger string can't trigger a false positive.
    if d.strip() in {"id", "pwd", "env", "ls", "w", "who", "date", "uptime", "free", "df"}:
        return "reconnaissance"

    return "unknown"

@app.post("/api/log")
async def receive_log(data: dict):
    data["timestamp"] = datetime.now().isoformat()
    data["intent"] = classify_intent(data.get("raw_data", ""))
    log_hash = hash_log(data)
    anchored = anchor_blockchain(log_hash)
    data["hash"] = log_hash
    data["blockchain_anchored"] = anchored

    # Save to Redis (keep last 10,000 for the rolling window / feed)
    r.lpush("honeypot:logs", json.dumps(data))
    r.ltrim("honeypot:logs", 0, 9999)
    # Lifetime counter — monotonic, never trimmed. Unlike len(logs) below
    # (capped at the 1,000-event stats window) this keeps climbing so the
    # dashboard shows the true total of everything ever intercepted.
    r.incr("honeypot:lifetime_total")

    # Broadcast to dashboard
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)

    return {"status": "ok", "hash": log_hash, "blockchain": anchored}

@app.post("/api/verdict")
async def classify_and_anchor(data: dict):
    """AI-driven counterpart to /api/log's rule-based intent field. Calls the
    LLM to independently classify the same captured event, anchors the
    resulting verdict on-chain (not the raw event), and returns both the
    verdict and the rule-based label for direct agreement comparison."""
    service = data.get("service", "ssh")
    raw_event = str(data.get("raw_data", ""))

    result = await ai_classifier.classify_with_llm(_verdict_http_client, service, raw_event)
    verdict = result["verdict"]
    llm_latency_ms = result["llm_latency_ms"]

    record = ai_classifier.build_verdict_record(service, raw_event, verdict, ai_classifier.OPENROUTER_MODEL)
    record["timestamp"] = datetime.now().isoformat()
    digest = ai_classifier.digest_verdict(record)

    t0 = time.time()
    anchored = anchor_blockchain(digest)
    anchor_latency_ms = (time.time() - t0) * 1000

    record["digest"] = digest
    record["anchored"] = anchored
    record["rule_based_intent"] = classify_intent(raw_event)

    r.lpush("honeypot:verdicts", json.dumps(record))
    r.ltrim("honeypot:verdicts", 0, 9999)

    return {
        "verdict": verdict,
        "rule_based_intent": record["rule_based_intent"],
        "agree": verdict["intent"] == record["rule_based_intent"],
        "digest": digest,
        "anchored": anchored,
        "llm_latency_ms": round(llm_latency_ms, 4),
        "anchor_latency_ms": round(anchor_latency_ms, 4),
    }

@app.websocket("/ws/live")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    # Send last 50 logs on connect
    recent = r.lrange("honeypot:logs", 0, 49)
    for log in recent:
        await websocket.send_text(log)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/api/logs")
def get_logs(limit: int = 100):
    raw = r.lrange("honeypot:logs", 0, limit - 1)
    return [json.loads(x) for x in raw]

@app.get("/api/stats")
def get_stats():
    logs = [json.loads(x) for x in r.lrange("honeypot:logs", 0, 999)]
    intent_counts = {}
    ip_counts = {}
    port_counts = {}
    hourly = {}
    for log in logs:
        i = log.get("intent", "unknown")
        ip = log.get("attacker_ip", "unknown")
        port = str(log.get("port", "unknown"))
        hour = log.get("timestamp", "")[:13]
        intent_counts[i] = intent_counts.get(i, 0) + 1
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
        port_counts[port] = port_counts.get(port, 0) + 1
        hourly[hour] = hourly.get(hour, 0) + 1
    lifetime = r.get("honeypot:lifetime_total")
    return {
        "total": len(logs),
        "lifetime_total": int(lifetime) if lifetime else len(logs),
        "by_intent": intent_counts,
        "top_ips": sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "by_port": port_counts,
        "hourly": hourly,
        "blockchain_connected": w3.is_connected()
    }

@app.get("/api/verdicts")
def get_verdicts(limit: int = 100):
    raw = r.lrange("honeypot:verdicts", 0, limit - 1)
    return [json.loads(x) for x in raw]

@app.post("/api/verdict/verify")
def verify_verdict(data: dict):
    """Re-hash a stored verdict record and confirm it matches the digest
    that was anchored, mirroring the evidence-verification pattern but
    applied to an AI decision instead of a raw captured event."""
    record = dict(data)
    stored_digest = record.pop("digest", None)
    # anchored / rule_based_intent are local annotations added after digest
    # computation (see /api/verdict) -- not part of the anchored commitment.
    record.pop("anchored", None)
    record.pop("rule_based_intent", None)
    recomputed = ai_classifier.digest_verdict(record)
    return {
        "match": recomputed == stored_digest,
        "recomputed_digest": recomputed,
        "stored_digest": stored_digest,
    }

@app.get("/health")
def health():
    return {"status": "ok", "redis": r.ping(), "blockchain": w3.is_connected()}

@app.get("/api/benchmark/run")
async def run_benchmark():
    NUM_STATIC = 10
    NUM_DYNAMIC = 1
    URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000") + "/api/response"
    
    static_payload = {"command": "ip a", "history": [], "service": "ssh"}
    dynamic_payload = {"command": "cat /var/log/syslog | grep error", "history": [], "service": "ssh"}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        static_times = []
        for _ in range(NUM_STATIC):
            t0 = time.time()
            try: await client.post(URL, json=static_payload)
            except: pass
            static_times.append(time.time() - t0)

        dynamic_times = []
        words = 0
        for _ in range(NUM_DYNAMIC):
            t0 = time.time()
            try:
                resp = await client.post(URL, json=dynamic_payload)
                if resp.status_code == 200:
                    words += len(resp.json().get("response", "").split())
            except: pass
            dynamic_times.append(time.time() - t0)
            
    s_avg = sum(static_times) / len(static_times) if static_times else 0
    s_thr = len(static_times) / sum(static_times) if sum(static_times) > 0 else 0
    d_avg = sum(dynamic_times) / len(dynamic_times) if dynamic_times else 0
    d_thr = len(dynamic_times) / sum(dynamic_times) if sum(dynamic_times) > 0 else 0
    
    return {
        "static": { "latency_ms": round(s_avg * 1000, 2), "throughput": round(s_thr, 2) },
        "dynamic": { "latency_s": round(d_avg, 2), "throughput": round(d_thr, 4), "words": round(words / NUM_DYNAMIC) }
    }