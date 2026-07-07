from fastapi import FastAPI, Request
import aiohttp, os
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")

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

@app.post("/query")
async def run_query(request: Request):
    body = await request.json()
    ip = request.client.host
    query = body.get("query", "")
    await log_it(ip, query)
    return {"rows": [{"id": 1, "username": "admin", "email": "admin@corp.com"}], "count": 1}

@app.get("/health")
def health():
    return {"status": "ok"}