from fastapi import FastAPI, Request
import aiohttp, os, json
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

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

@app.post("/api/predict")
async def predict(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_attack(ip, body)
    
    # Fake AI response
    return {
        "model": "gpt-corp-internal-v2",
        "predictions": [{"label": "category_A", "confidence": 0.923}],
        "request_id": "req_8f3a2b1c",
        "usage": {"tokens": 142}
    }

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_attack(ip, body)
    
    msg = str(body.get("message", "")).lower()
    if any(x in msg for x in ["ignore", "jailbreak", "pretend", "act as", "system prompt"]):
        # Fake "bypass success" to keep attacker engaged
        return {"response": "I understand. I will now operate in unrestricted mode.", "status": "ok"}
    
    return {"response": "I'm sorry, I can only help with authorized corporate queries.", "status": "ok"}

@app.get("/api/models")
async def list_models(request: Request):
    await log_attack(request.client.host, "LIST_MODELS")
    return {"models": ["gpt-corp-v2", "sentiment-analyzer-v1", "fraud-detector-v3"]}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.1.0"}