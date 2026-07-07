from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio, json, os, hashlib
import redis as redis_lib
from web3 import Web3
from datetime import datetime

app = FastAPI(title="Honeypot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis_lib.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

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

def classify_intent(raw: str) -> str:
    d = raw.lower()
    if any(x in d for x in ["select ", "' or", "union ", "drop table", "1=1", "insert into"]):
        return "sql_injection"
    if any(x in d for x in ["sudo", "/etc/shadow", "chmod 777", "passwd", "privilege"]):
        return "privilege_escalation"
    if any(x in d for x in ["wget ", "curl ", "nc ", "bash -i", "python -c", "/bin/sh"]):
        return "reverse_shell"
    if any(x in d for x in ["xmrig", "miner", "monero", "cryptonight", "stratum"]):
        return "cryptomining"
    if any(x in d for x in ["ignore previous", "jailbreak", "pretend you", "you are now", "act as"]):
        return "prompt_injection"
    if any(x in d for x in ["git push", "pipeline", "jenkins", "build trigger", "webhook"]):
        return "supply_chain"
    if any(x in d for x in ["nmap", "masscan", "scan", "ping sweep", "port scan"]):
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

    # Save to Redis (keep last 10,000)
    r.lpush("honeypot:logs", json.dumps(data))
    r.ltrim("honeypot:logs", 0, 9999)

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
    return {
        "total": len(logs),
        "by_intent": intent_counts,
        "top_ips": sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "by_port": port_counts,
        "hourly": hourly,
        "blockchain_connected": w3.is_connected()
    }

@app.get("/health")
def health():
    return {"status": "ok", "redis": r.ping(), "blockchain": w3.is_connected()}