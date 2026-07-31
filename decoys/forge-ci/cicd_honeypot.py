from fastapi import FastAPI, Request
import aiohttp, os, json
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")

# Reused connection pool instead of opening a new TCP connection on every
# logged request and every AI-engine call.
_session: aiohttp.ClientSession | None = None


@app.on_event("startup")
async def _init_session():
    global _session
    _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))


@app.on_event("shutdown")
async def _close_session():
    if _session is not None:
        await _session.close()


async def log_it(ip, data):
    try:
        await _session.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip, "port": 9090,
            "service": "CI-CD",
            "raw_data": str(data),
            "timestamp": datetime.now().isoformat()
        })
    except Exception:
        pass

async def get_ai_response(req_path, body_data):
    try:
        cmd = f"Endpoint: {req_path}\nData: {body_data}"
        payload = {"command": cmd, "history": [], "service": "cicd"}
        async with _session.post(f"{AI_ENGINE_URL}/api/response", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                ai_text = data.get("response", "{}")
                try:
                    return json.loads(ai_text)
                except Exception:
                    return {"result": ai_text}
    except Exception as e:
        print(f"[CICD] AI Engine error: {e}")
    return {"error": "Service unavailable"}

@app.post("/job/build/api/json")
async def trigger_build(request: Request):
    body = await request.body()
    ip = request.client.host
    await log_it(ip, body.decode())
    return await get_ai_response("/job/build/api/json", body.decode())

@app.get("/api/json")
async def jenkins_info(request: Request):
    await log_it(request.client.host, "INFO_REQUEST")
    return await get_ai_response("/api/json", "")

@app.post("/git/notifyCommit")
async def git_hook(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_it(ip, body)
    return await get_ai_response("/git/notifyCommit", json.dumps(body))