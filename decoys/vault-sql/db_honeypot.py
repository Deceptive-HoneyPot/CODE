from fastapi import FastAPI, Request
import aiohttp, os
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")

async def log_it(ip, query):
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json={
                "attacker_ip": ip, "port": 5433,
                "service": "SQL-DB",
                "raw_data": query,
                "timestamp": datetime.now().isoformat()
            })
    except:
        pass

async def get_ai_response(query):
    import json
    try:
        payload = {"command": query, "history": [], "service": "sql"}
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{AI_ENGINE_URL}/api/response", json=payload, timeout=120.0) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "ERROR: relation does not exist")
    except Exception as e:
        print(f"[SQL] AI Engine error: {e}")
    return "ERROR: syntax error at or near end of line"

@app.post("/query")
async def run_query(request: Request):
    body = await request.json()
    ip = request.client.host
    query = body.get("query", "")
    await log_it(ip, query)
    
    # Generate realistic response using AI Engine
    ai_resp = await get_ai_response(query)
    return {"rows": [{"ai_response": ai_resp}], "count": 1}

@app.get("/health")
def health():
    return {"status": "ok"}