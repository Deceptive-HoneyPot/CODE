from fastapi import FastAPI, Request
import aiohttp, os
from datetime import datetime

app = FastAPI()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")

async def log_it(ip, data):
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json={
                "attacker_ip": ip, "port": 9090,
                "service": "CI-CD",
                "raw_data": str(data),
                "timestamp": datetime.now().isoformat()
            })
    except:
        pass

@app.post("/job/build/api/json")
async def trigger_build(request: Request):
    body = await request.body()
    ip = request.client.host
    await log_it(ip, body.decode())
    return {"result": "SUCCESS", "build_number": 247, "url": "http://jenkins.corp/job/build/247/"}

@app.get("/api/json")
async def jenkins_info(request: Request):
    await log_it(request.client.host, "INFO_REQUEST")
    return {"mode": "NORMAL", "nodeDescription": "Jenkins 2.387.3", "numExecutors": 4}

@app.post("/git/notifyCommit")
async def git_hook(request: Request):
    body = await request.json()
    ip = request.client.host
    await log_it(ip, body)
    return {"triggered": True, "jobs": ["build-main", "deploy-prod"]}