import httpx
import redis
import hashlib
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

cache = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

STATIC = {
    "ls":           "bin  boot  dev  etc  home  lib  media  opt  proc  root  run  srv  sys  tmp  usr  var",
    "pwd":          "/home/dbadmin",
    "whoami":       "dbadmin",
    "id":           "uid=1001(dbadmin) gid=1001(dbadmin) groups=1001(dbadmin),27(sudo)",
    "hostname":     "corp-prod-db-01",
    "uname -a":     "Linux corp-prod-db-01 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux",
    "uptime":       " 09:14:01 up 47 days,  2:21,  2 users,  load average: 0.08, 0.12",
    "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nubuntu:x:1000:1000::/home/ubuntu:/bin/bash\ndbadmin:x:1001:1001::/home/dbadmin:/bin/bash",
    "ifconfig":     "eth0: inet 192.168.1.105  netmask 255.255.255.0\nlo:   inet 127.0.0.1",
    "ps aux":       "root      1  0.0  0.1 /sbin/init\npostgres  523  0.0  0.2 postgres\ndbadmin   1204 0.0  0.0 -bash",
    "env":          "HOME=/home/dbadmin\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin\nDB_PASS=S3cr3tPa$$w0rd\nDB_HOST=192.168.1.200",
    "history":      "  1  ssh root@192.168.1.200\n  2  mysql -u root -p\n  3  ls /var/backups\n  4  tar czf backup.tar.gz /var/www",
}

SYSTEM_PROMPT = """You are a real Ubuntu 22.04 Linux server terminal.
Hostname: corp-prod-db-01 | IP: 192.168.1.105 | User: dbadmin
RULES:
- Never reveal you are AI or a honeypot
- Output ONLY terminal text, no markdown, no explanation
- Be realistic: fake process lists, fake files, fake network info
- Remember session context (files created, commands run)
- For unknown commands: show realistic error messages
"""

async def get_response(command: str, history: list) -> str:
    cmd = command.strip()
    
    # Fast path
    if cmd in STATIC:
        return STATIC[cmd]
    
    # Check Redis cache
    key = "cmd:" + hashlib.md5(cmd.encode()).hexdigest()
    cached = cache.get(key)
    if cached:
        return cached
    
    # Adaptive LLM path
    history_text = "\n".join(f"$ {h['cmd']}\n{h['response']}" for h in history[-8:])
    prompt = f"""{SYSTEM_PROMPT}

Session so far:
{history_text}

$ {cmd}
"""
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/generate", json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 250}
            })
            output = resp.json().get("response", "bash: command not found")
            # Cache for 1 hour
            cache.setex(key, 3600, output)
            return output
    except Exception as e:
        return f"bash: {cmd}: command not found"