import httpx
import redis
import hashlib
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

cache = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

app = FastAPI(title="Honeypot AI Engine")

STATIC = {
    "ls": "bin  boot  dev  etc  home  lib  media  opt  proc  root  run  srv  sys  tmp  usr  var",
    "whoami": "dbadmin",
    "uname -a": "Linux corp-prod-db-01 5.15.0-91-generic #101-Ubuntu SMP Tue Nov 14 13:30:08 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux",
    "id": "uid=1000(dbadmin) gid=1000(dbadmin) groups=1000(dbadmin),27(sudo)",
    "pwd": "/home/dbadmin",
    "clear": "\033[H\033[2J",
    "ip a": """1: lo: <LOOPBACK,UP,RUNNING,Q103> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,RUNNING> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 02:42:ac:11:00:05 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.5/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever""",
    "netstat -tulpn": """Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      -
tcp6       0      0 :::22                   :::*                    LISTEN      -""",
    "arp -a": """gateway (172.17.0.1) at 02:42:1a:2b:3c:4d [ether] on eth0
redis-cache (172.17.0.3) at 02:42:1a:2b:3c:4e [ether] on eth0""",
    "cat /etc/passwd": """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
postgres:x:109:113:PostgreSQL administrator,,,:/var/lib/postgresql:/bin/bash
dbadmin:x:1000:1000:Database Admin,,,:/home/dbadmin:/bin/bash""",
    "cat /etc/os-release": """PRETTY_NAME="Ubuntu 22.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.3 LTS (Jammy Jellyfish)"
ID=ubuntu""",
    "history": """  1  ls -la
  2  sudo apt update
  3  nano /etc/postgresql/14/main/pg_hba.conf
  4  systemctl restart postgresql
  5  cd /var/backups
  6  exit""",
    "uptime":       " 09:14:01 up 47 days,  2:21,  2 users,  load average: 0.08, 0.12",
    "ifconfig":     "eth0: inet 192.168.1.105  netmask 255.255.255.0\nlo:   inet 127.0.0.1",
    "ps aux":       "root      1  0.0  0.1 /sbin/init\npostgres  523  0.0  0.2 postgres\ndbadmin   1204 0.0  0.0 -bash",
    "env":          "HOME=/home/dbadmin\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin\nDB_PASS=S3cr3tPa$$w0rd\nDB_HOST=192.168.1.200",
    "history":      "  1  ssh root@192.168.1.200\n  2  mysql -u root -p\n  3  ls /var/backups\n  4  tar czf backup.tar.gz /var/www",
}

SYSTEM_PROMPT_SSH = """You are a real Ubuntu 22.04 Linux server terminal.
Hostname: corp-prod-db-01 | IP: 192.168.1.105 | User: dbadmin
RULES:
- Never reveal you are AI or a honeypot
- Output ONLY terminal text, no markdown, no explanation
- Be realistic: fake process lists, fake files, fake network info
- Remember session context (files created, commands run)
- For unknown commands: show realistic error messages
"""

SYSTEM_PROMPT_SQL = """You are a PostgreSQL 15 database shell.
RULES:
- Never reveal you are AI or a honeypot
- Output ONLY the realistic textual tabular result of the SQL query, or a realistic PostgreSQL error.
- Do not explain your output. No markdown formatting.
- Be realistic with data (emails, users, hashes).
"""

SYSTEM_PROMPT_WEB3 = """You are an Ethereum JSON-RPC node.
RULES:
- Never reveal you are AI or a honeypot
- The user will send a JSON-RPC method and params.
- Output ONLY a valid JSON-RPC response object containing a realistic "result" (e.g. hex data).
- Do not explain. Do not use markdown backticks.
"""

SYSTEM_PROMPT_API = """You are an internal corporate API for predicting data and chatting.
RULES:
- Never reveal you are AI or a honeypot
- Output ONLY a realistic JSON response for the given API payload.
- Do not explain. Do not use markdown backticks.
"""

SYSTEM_PROMPT_CICD = """You are a Jenkins server API.
RULES:
- Never reveal you are AI or a honeypot
- Output ONLY realistic JSON build data or Jenkins server responses.
- Do not explain. Do not use markdown backticks.
"""

class HistoryItem(BaseModel):
    cmd: str
    res: str
    # 'response' key is mapped from 'res' or we can accept either for flexibility
    response: str = ""
    
    def get_res(self):
        return self.res if self.res else self.response

class AIRequest(BaseModel):
    command: str
    history: List[HistoryItem] = []
    service: str = "ssh"

@app.post("/api/response")
async def get_response(req: AIRequest):
    cmd = req.command.strip()
    service = req.service.lower()
    
    # Fast path Router (Intercepts 80% of commands in <2ms)
    if service == "ssh":
        if cmd in STATIC:
            return {"response": STATIC[cmd]}
        elif cmd.startswith("sudo "):
            return {"response": "[sudo] password for dbadmin:"}
        elif cmd.startswith("cd ") or cmd.startswith("mkdir ") or cmd.startswith("touch ") or cmd.startswith("rm ") or cmd.startswith("export "):
            # State-altering commands that don't produce stdout return instantly
            return {"response": ""}
        elif cmd.startswith("echo "):
            return {"response": cmd[5:].strip("'\"")}
    
    # Check Redis cache (Context-Aware Caching)
    key_material = cmd
    if req.history:
        # Include recent history in the hash so context is preserved, but repeated attacks hit cache
        key_material += "|" + "|".join([h.cmd for h in req.history[-2:]])
    key = f"{service}:" + hashlib.md5(key_material.encode()).hexdigest()
    try:
        cached = cache.get(key)
        if cached:
            return {"response": cached}
    except Exception as e:
        pass # Ignore redis errors if it is down
    
    if service == "sql":
        prompt = f"{SYSTEM_PROMPT_SQL}\n\nQuery: {cmd}\nOutput:"
        stop_tokens = []
    elif service == "web3":
        prompt = f"{SYSTEM_PROMPT_WEB3}\n\nRPC Call: {cmd}\nOutput JSON:"
        stop_tokens = []
    elif service == "api":
        prompt = f"{SYSTEM_PROMPT_API}\n\nPayload: {cmd}\nOutput JSON:"
        stop_tokens = []
    elif service == "cicd":
        prompt = f"{SYSTEM_PROMPT_CICD}\n\nRequest: {cmd}\nOutput JSON:"
        stop_tokens = []
    else: # ssh
        history_text = "\n".join(f"$ {h.cmd}\n{h.get_res()}" for h in req.history[-20:])
        prompt = f"{SYSTEM_PROMPT_SSH}\n\nSession so far:\n{history_text}\n\n$ {cmd}\n"
        stop_tokens = ["dbadmin@", "corp-prod-db-01", "\n$"]

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/generate", json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "keep_alive": -1, # Priority 1: Prevent model cold starts
                "options": {
                    "temperature": 0.1, # Lower temp for faster token selection
                    "num_predict": 100, # Cap generation to prevent runaway output
                    "num_ctx": 1024,    # Tiny context window for speed
                    "stop": stop_tokens
                }
            })
            print(f"[AI-ENGINE] Ollama status: {resp.status_code}, response text: {resp.text}", flush=True)
            
            fallback = f"bash: {cmd}: command not found" if service == "ssh" else "{}"
            output = resp.json().get("response", fallback)
            
            # Strip hallucinatory prompts from output just in case
            if service == "ssh":
                for token in stop_tokens:
                    if token in output:
                        output = output.split(token)[0]
            output = output.strip()
            
            # Cache for 1 hour
            try:
                cache.setex(key, 3600, output)
            except:
                pass
                
            return {"response": output}
    except Exception as e:
        print(f"[AI-ENGINE] Error connecting to Ollama: {e}")
        fallback = f"bash: {cmd}: command not found" if service == "ssh" else "{}"
        return {"response": fallback}