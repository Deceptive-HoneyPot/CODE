from fastapi import FastAPI, Request
import aiohttp, os, random
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")

async def log_it(ip, data):
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json={
                "attacker_ip": ip, "port": 8545,
                "service": "Web3-Node",
                "raw_data": str(data),
                "timestamp": datetime.now().isoformat()
            })
    except:
        pass

@app.post("/")
async def rpc(request: Request):
    body = await request.json()
    ip = request.client.host
    method = body.get("method", "")
    await log_it(ip, body)

    fake_responses = {
        "eth_getBalance":        {"result": "0x56BC75E2D63100000"},  # 100 ETH in Wei
        "eth_blockNumber":       {"result": "0x112A880"},
        "eth_sendRawTransaction":{"result": "0x" + "a" * 64},
        "net_version":           {"result": "1"},
        "eth_accounts":          {"result": ["0xFakeWallet123456789ABCDEF"]},
    }
    resp = fake_responses.get(method, {"result": None})
    return {**resp, "id": body.get("id", 1), "jsonrpc": "2.0"}