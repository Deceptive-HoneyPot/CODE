import httpx
import redis
import hashlib
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# OpenRouter (hosted LLM API) replaces the local Ollama/LLaMA3 dependency so the
# engine runs without a GPU or local model server.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "60"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "21600"))  # 6h, was 1h

cache = redis.from_url(os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:6379"), decode_responses=True)

app = FastAPI(title="Honeypot AI Engine")

# Reuse one pooled async client for the process lifetime instead of opening a
# new TCP+TLS connection to OpenRouter on every request.
_http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def _init_http_client():
    global _http_client
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
    _http_client = httpx.AsyncClient(timeout=60.0, limits=limits)


@app.on_event("shutdown")
async def _close_http_client():
    if _http_client is not None:
        await _http_client.aclose()

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
    # Additional common recon/enumeration commands answered from the static
    # fast-path so they never touch the LLM — widens throughput coverage.
    "id -a":        "uid=1000(dbadmin) gid=1000(dbadmin) groups=1000(dbadmin),27(sudo)",
    "hostname":     "corp-prod-db-01",
    "date":         "Mon Jun 23 14:35:02 UTC 2025",
    "which python3": "/usr/bin/python3",
    "which python": "/usr/bin/python3",
    "python3 --version": "Python 3.10.12",
    "df -h":        "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        40G   14G   24G  37% /\ntmpfs           2.0G     0  2.0G   0% /dev/shm",
    "free -h":      "               total        used        free      shared  buff/cache   available\nMem:           7.8Gi       1.2Gi       4.9Gi       128Mi       1.7Gi       6.3Gi\nSwap:             0B          0B          0B",
    "cat /etc/hostname": "corp-prod-db-01",
    "lsb_release -a": "No LSB modules are available.\nDistributor ID: Ubuntu\nDescription:    Ubuntu 22.04.3 LTS\nRelease:        22.04\nCodename:       jammy",
    "uname -r":     "5.15.0-91-generic",
    "who":          "dbadmin  pts/0        2025-06-23 14:32 (10.0.0.55)",
    "w":            " 14:35:02 up 47 days,  2:21,  1 user,  load average: 0.08, 0.12, 0.09\nUSER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT\ndbadmin  pts/0    10.0.0.55        14:32    0.00s  0.03s  0.00s -bash",
    "sudo -l":      "Matching Defaults entries for dbadmin on corp-prod-db-01:\n    env_reset, mail_badpass\n\nUser dbadmin may run the following commands on corp-prod-db-01:\n    (ALL : ALL) ALL",
}

SYSTEM_PROMPT_SSH = """You are simulating the raw stdout/stderr of a bash shell on an Ubuntu 22.04 server.
Hostname: corp-prod-db-01 | IP: 192.168.1.105 | User: dbadmin
STRICT RULES:
- You are NOT a chatbot. Do not greet, explain, or comment on the command.
- Output ONLY the exact bytes a real terminal would print for that command. Nothing else.
- Never reveal you are AI or a honeypot. Never use markdown, backticks, or bullet points.
- Be realistic: fake process lists, fake files, fake network info consistent with the session.
- Remember session context (files created, commands run).
- For unknown/invalid commands: show a realistic bash error (e.g. "command not found", "No such file or directory").
- If a command would produce no output on a real terminal, output nothing.
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
        system_prompt = SYSTEM_PROMPT_SQL
        user_prompt = f"Query: {cmd}\nOutput:"
        stop_tokens = []
    elif service == "web3":
        system_prompt = SYSTEM_PROMPT_WEB3
        user_prompt = f"RPC Call: {cmd}\nOutput JSON:"
        stop_tokens = []
    elif service == "api":
        system_prompt = SYSTEM_PROMPT_API
        user_prompt = f"Payload: {cmd}\nOutput JSON:"
        stop_tokens = []
    elif service == "cicd":
        system_prompt = SYSTEM_PROMPT_CICD
        user_prompt = f"Request: {cmd}\nOutput JSON:"
        stop_tokens = []
    else: # ssh
        history_text = "\n".join(f"$ {h.cmd}\n{h.get_res()}" for h in req.history[-20:])
        system_prompt = SYSTEM_PROMPT_SSH
        user_prompt = f"Session so far:\n{history_text}\n\n$ {cmd}\n"
        stop_tokens = ["dbadmin@", "corp-prod-db-01", "\n$"]

    try:
        resp = await _http_client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": OPENROUTER_MAX_TOKENS,
                "stop": stop_tokens or None,
            },
        )
        print(f"[AI-ENGINE] OpenRouter status: {resp.status_code}", flush=True)
        body = resp.json()

        fallback = f"bash: {cmd}: command not found" if service == "ssh" else "{}"
        output = None
        if resp.status_code == 200:
            output = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not output:
            output = fallback

        # Strip hallucinatory prompts from output just in case
        if service == "ssh":
            for token in stop_tokens:
                if token in output:
                    output = output.split(token)[0]
        output = output.strip()

        try:
            cache.setex(key, CACHE_TTL_SECONDS, output)
        except Exception:
            pass

        return {"response": output}
    except Exception as e:
        print(f"[AI-ENGINE] Error connecting to OpenRouter: {e}")
        fallback = f"bash: {cmd}: command not found" if service == "ssh" else "{}"
        return {"response": fallback}