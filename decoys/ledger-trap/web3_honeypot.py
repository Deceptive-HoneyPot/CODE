from fastapi import FastAPI, Request
import aiohttp, os, random
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")

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

async def get_ai_response(method, params):
    import json
    try:
        cmd = json.dumps({"method": method, "params": params})
        payload = {"command": cmd, "history": [], "service": "web3"}
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{AI_ENGINE_URL}/api/response", json=payload, timeout=120.0) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Try to parse the response as JSON, else return it as a string
                    ai_text = data.get("response", "{}")
                    try:
                        return json.loads(ai_text)
                    except:
                        return {"result": ai_text}
    except Exception as e:
        print(f"[WEB3] AI Engine error: {e}")
    return {"error": {"code": -32601, "message": "Method not found"}}

@app.post("/")
async def rpc(request: Request):
    body = await request.json()
    ip = request.client.host
    method = body.get("method", "")
    params = body.get("params", [])
    await log_it(ip, body)

    fake_responses = {
        "eth_getBalance":        {"result": "0x56BC75E2D63100000"},  # 100 ETH in Wei
        "eth_blockNumber":       {"result": "0x112A880"},
        "net_version":           {"result": "1"},
        "eth_accounts":          {"result": ["0xFakeWallet123456789ABCDEF"]},
    }
    
    if method in fake_responses:
        resp = fake_responses[method]
    else:
        # Send everything else to AI
        resp = await get_ai_response(method, params)
        
    return {**resp, "id": body.get("id", 1), "jsonrpc": "2.0"}