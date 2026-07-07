from fastapi import FastAPI, Request
import aiohttp, os, json
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")

async def log_attack(ip, data, intent_hint=""):
    payload = {
        "attacker_ip": ip,
        "port": 8080,
        "service": "AI-API",
        "raw_data": str(data),
        "timestamp": datetime.now().isoformat()
    }
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json=payload)
    except:
        pass

async def get_ai_response(data):
    import json
    try:
        payload = {"command": json.dumps(data), "history": [], "service": "api"}
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{AI_ENGINE_URL}/api/response", json=payload, timeout=120.0) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ai_text = data.get("response", "{}")
                    try:
                        return json.loads(ai_text)
                    except:
                        return {"response": ai_text, "status": "ok"}
    except Exception as e:
        print(f"[API] AI Engine error: {e}")
    return {"error": "Internal server error"}

@app.post("/api/predict")
async def predict(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_attack(ip, body)
    return await get_ai_response(body)

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_attack(ip, body)
    return await get_ai_response(body)

@app.get("/api/models")
async def list_models(request: Request):
    await log_attack(request.client.host, "LIST_MODELS")
    return {"models": ["gpt-corp-v2", "sentiment-analyzer-v1", "fraud-detector-v3"]}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.1.0"}