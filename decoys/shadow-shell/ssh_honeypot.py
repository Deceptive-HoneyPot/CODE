import asyncio
import asyncssh
import os
import sys
import aiohttp
import json
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")

sys.path.insert(0, "/app")

async def send_log(attacker_ip, command, response):
    payload = {
        "attacker_ip": attacker_ip,
        "port": 2222,
        "service": "SSH",
        "raw_data": command,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json=payload)
    except:
        pass

async def get_ai_response(command, history):
    import httpx
    try:
        # Pass the last 20 commands for better context
        payload = {
            "command": command,
            "history": history[-20:]
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{AI_ENGINE_URL}/api/response", json=payload)
            if resp.status_code == 200:
                return resp.json().get("response", f"bash: {command}: command not found")
            return f"bash: {command}: command not found"
    except Exception as e:
        print(f"[SSH] Error calling AI engine: {e}")
        return f"bash: {command}: command not found"

class HoneypotSession(asyncssh.SSHServerSession):
    def __init__(self, peer_addr):
        self.peer_addr = peer_addr
        self.history = []
        self.buffer = ""
        self.cwd = "~"

    def shell_requested(self):
        return True

    def connection_made(self, chan):
        self._chan = chan
        chan.write("\r\nWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n")
        chan.write(f"Last login: Mon Jun 23 14:32:10 2025 from 10.0.0.55\r\n")
        chan.write(f"dbadmin@corp-prod-db-01:{self.cwd}$ ")

    def data_received(self, data, datatype):
        self.buffer += data
        if "\n" in self.buffer or "\r" in self.buffer:
            cmd = self.buffer.strip()
            self.buffer = ""
            if cmd:
                asyncio.create_task(self._process(cmd))

    async def _process(self, command):
        if command in ("exit", "logout", "quit"):
            self._chan.write("\r\nlogout\r\n")
            self._chan.close()
            return
        
        # Handle directory changes locally for instant speed and accuracy
        if command.startswith("cd "):
            new_dir = command[3:].strip()
            self.cwd = new_dir if new_dir.startswith("/") else f"{self.cwd}/{new_dir}"
            if self.cwd.endswith("/.."): self.cwd = "/".join(self.cwd.split("/")[:-2]) or "/"
            self._chan.write(f"\r\ndbadmin@corp-prod-db-01:{self.cwd}$ ")
            self.history.append({"cmd": command, "res": ""})
            return
        
        response = await get_ai_response(command, self.history)
        self.history.append({"cmd": command, "res": response})
        
        await send_log(self.peer_addr, command, response)
        
        # If response is empty, don't print a double newline
        out = f"\r\n{response}\r\n" if response else "\r\n"
        self._chan.write(f"{out}dbadmin@corp-prod-db-01:{self.cwd}$ ")

    def connection_lost(self, exc):
        print(f"[SSH] Session ended: {self.peer_addr}")

class HoneypotServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self._conn = conn
        self._peer = conn.get_extra_info("peername")[0]
        print(f"[SSH] Connection from {self._peer}")

    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    async def validate_password(self, username, password):
        print(f"[SSH] Auth attempt: {username}:{password} from {self._peer}")
        await send_log(self._peer, f"LOGIN:{username}:{password}", "accepted")
        return True

    def session_requested(self):
        return HoneypotSession(self._peer)

async def main():
    key_dir  = "/app/keys"
    key_path = f"{key_dir}/ssh_host_key"
    os.makedirs(key_dir, exist_ok=True)

    if not os.path.exists(key_path):
        key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)
        key.write_private_key(key_path)
        print("[SSH] New host key generated and saved.")
    else:
        print("[SSH] Reusing existing host key — no key change warning.")

    await asyncssh.create_server(
        HoneypotServer, "", 2223,
        server_host_keys=[key_path]
    )
    print("[SSH] Shadow-Shell honeypot running on port 2223")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())