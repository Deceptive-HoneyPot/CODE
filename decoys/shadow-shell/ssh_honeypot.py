import asyncio
import asyncssh
import os
import sys
import aiohttp
import json
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

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
    STATIC = {
        # Basic navigation
        "ls":               "bin  boot  dev  etc  home  lib  media  opt  proc  root  run  srv  sys  tmp  usr  var",
        "ls -la":           "total 68\ndrwxr-xr-x 18 root    root    4096 Jun 10 09:01 .\ndrwxr-xr-x 18 root    root    4096 Jun 10 09:01 ..\ndrwxr-xr-x  2 root    root    4096 Jun 10 09:01 bin\ndrwxr-xr-x  3 root    root    4096 Jun 10 09:01 etc\ndrwxr-xr-x  3 dbadmin dbadmin 4096 Jun 20 14:12 home\ndrwxrwxrwt  8 root    root    4096 Jun 23 08:55 tmp",
        "pwd":              "/home/dbadmin",
        "whoami":           "dbadmin",
        "id":               "uid=1001(dbadmin) gid=1001(dbadmin) groups=1001(dbadmin),27(sudo)",
        "hostname":         "corp-prod-db-01",
        "uname -a":         "Linux corp-prod-db-01 5.15.0-91-generic #101-Ubuntu SMP Thu Jan 11 14:29:40 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux",
        "uptime":           " 14:32:10 up 47 days,  2:21,  2 users,  load average: 0.08, 0.12, 0.09",
        "date":             "Mon Jun 23 14:32:10 UTC 2025",

        # User / credential info (juicy bait for attackers)
        "cat /etc/passwd":  "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\ndbadmin:x:1001:1001:DB Admin:/home/dbadmin:/bin/bash\npostgres:x:1002:1002:PostgreSQL:/var/lib/postgresql:/bin/bash",
        "cat /etc/shadow":  "cat: /etc/shadow: Permission denied",
        "cat /etc/hosts":   "127.0.0.1   localhost\n127.0.1.1   corp-prod-db-01\n192.168.1.200  db-primary.corp.internal\n192.168.1.201  db-replica.corp.internal",
        "cat /etc/os-release": 'NAME="Ubuntu"\nVERSION="22.04.3 LTS (Jammy Jellyfish)"\nID=ubuntu\nPRETTY_NAME="Ubuntu 22.04.3 LTS"',

        # Environment (fake credentials as bait)
        "env":              "HOME=/home/dbadmin\nUSER=dbadmin\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin\nDB_PASS=Sup3rS3cr3t!\nDB_HOST=192.168.1.200\nDB_PORT=5432\nDB_NAME=corporate_db\nAWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "printenv":         "HOME=/home/dbadmin\nUSER=dbadmin\nDB_PASS=Sup3rS3cr3t!\nDB_HOST=192.168.1.200\nAWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",

        # Process / system info
        "ps aux":           "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1 169936  8120 ?        Ss   Jun10   0:08 /sbin/init\npostgres   523  0.0  0.2 213456 18024 ?        Ss   Jun10   2:14 /usr/lib/postgresql/15/bin/postgres\ndbadmin   1204  0.0  0.0  21360  5432 pts/0    Ss   14:30   0:00 -bash\ndbadmin   1337  0.0  0.0  13228  1024 pts/0    R+   14:32   0:00 ps aux",
        "ps -ef":           "UID        PID  PPID  C STIME TTY          TIME CMD\nroot         1     0  0 Jun10 ?        00:00:08 /sbin/init\npostgres   523     1  0 Jun10 ?        00:02:14 postgres: 15/main\ndbadmin   1204  1203  0 14:30 pts/0    00:00:00 -bash",
        "top":              "top - 14:32:10 up 47 days,  2:21,  2 users,  load average: 0.08, 0.12, 0.09\nTasks:  87 total,   1 running,  86 sleeping,   0 stopped\n%Cpu(s):  0.3 us,  0.1 sy,  0.0 ni, 99.5 id\nMiB Mem :   7854.2 total,   4210.3 free,   1823.1 used\n\nPID    USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND\n  523  postgres  20   0  213456  18024  14320 S   0.3   0.2   2:14.33 postgres",

        # Network info
        "ifconfig":         "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 192.168.1.105  netmask 255.255.255.0  broadcast 192.168.1.255\n        inet6 fe80::42:acff:fe11:2  prefixlen 64\nlo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n        inet 127.0.0.1  netmask 255.0.0.0",
        "ip a":             "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n    inet 127.0.0.1/8 scope host lo\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500\n    inet 192.168.1.105/24 brd 192.168.1.255 scope global eth0",
        "netstat -an":      "Active Internet connections (servers and established)\nProto Recv-Q Send-Q Local Address     Foreign Address   State\ntcp        0      0 0.0.0.0:22        0.0.0.0:*         LISTEN\ntcp        0      0 0.0.0.0:5432      0.0.0.0:*         LISTEN\ntcp        0      0 192.168.1.105:22  192.168.1.50:41832 ESTABLISHED",
        "netstat -tulpn":   "Proto Recv-Q Send-Q Local Address   Foreign Address  State       PID/Program\ntcp        0      0 0.0.0.0:22      0.0.0.0:*        LISTEN      855/sshd\ntcp        0      0 0.0.0.0:5432    0.0.0.0:*        LISTEN      523/postgres",
        "ss -tulpn":        "Netid State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port\ntcp   LISTEN 0      128         0.0.0.0:22         0.0.0.0:*    users:((\"sshd\",pid=855,fd=3))\ntcp   LISTEN 0      128         0.0.0.0:5432       0.0.0.0:*    users:((\"postgres\",pid=523,fd=5))",

        # File system snooping
        "ls /etc":          "apt  bash.bashrc  cron.d  crontab  environment  fstab  group  hosts  hostname  motd  passwd  profile  resolv.conf  shadow  ssh  sudoers",
        "ls /home":         "dbadmin  ubuntu",
        "ls /home/dbadmin": ".bash_history  .bashrc  .profile  .ssh  backups  db_scripts",
        "ls /tmp":          "tmp_backup_20250620.tar.gz  .X11-unix",
        "ls /var":          "backups  cache  lib  log  mail  opt  run  spool  tmp  www",
        "ls /var/log":      "auth.log  dpkg.log  kern.log  postgresql  syslog  ufw.log",
        "ls /root":         "ls: cannot open directory '/root': Permission denied",

        # Privilege escalation attempts
        "sudo su":          "[sudo] password for dbadmin: \nSorry, try again.\n[sudo] password for dbadmin: \nSorry, try again.\nsudo: 3 incorrect password attempts",
        "sudo -l":          "Matching Defaults entries for dbadmin on corp-prod-db-01:\n    env_reset, mail_badpass\nUser dbadmin may run the following commands:\n    (ALL) /usr/bin/pg_dump\n    (ALL) /usr/bin/pg_restore",
        "su root":          "Password: \nsu: Authentication failure",
        "sudo cat /etc/shadow": "[sudo] password for dbadmin: \nroot:$6$rounds=4096$fakeHash$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:19700:0:99999:7:::\ndbadmin:$6$rounds=4096$fakeHash$BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB:19700:0:99999:7:::",

        # History (leave breadcrumbs)
        "history":          "    1  ssh root@192.168.1.200\n    2  mysql -u root -p\n    3  ls /var/backups\n    4  cat /etc/passwd\n    5  pg_dump -U postgres corporate_db > backup.sql\n    6  tar czf /tmp/backup.tar.gz backup.sql\n    7  aws s3 cp /tmp/backup.tar.gz s3://corp-backups/\n    8  history",
        "cat ~/.bash_history": "ssh root@192.168.1.200\nmysql -u root -p\npg_dump -U postgres corporate_db\nwget http://internal-tools.corp/deploy.sh\nbash deploy.sh\napt-get install nmap\nnmap -sV 192.168.1.0/24",

        # Common recon
        "w":                " 14:32:10 up 47 days,  2:21,  2 users,  load average: 0.08\nUSER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT\ndbadmin  pts/0    10.0.0.55        14:30    0.00s  0.04s  0.00s -bash\nubuntu   pts/1    10.0.0.12        09:14    5:18m  0.02s  0.02s -bash",
        "last":             "dbadmin  pts/0        10.0.0.55        Mon Jun 23 14:30   still logged in\nubuntu   pts/1        10.0.0.12        Mon Jun 23 09:14   still logged in\ndbadmin  pts/0        10.0.0.55        Sun Jun 22 18:42 - 20:10  (01:28)",
        "who":              "dbadmin pts/0        2025-06-23 14:30 (10.0.0.55)\nubuntu  pts/1        2025-06-23 09:14 (10.0.0.12)",
        "df -h":            "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        50G   18G   30G  38% /\ntmpfs           3.9G     0  3.9G   0% /dev/shm\n/dev/sda2       200G   87G  103G  46% /var/lib/postgresql",
        "free -h":          "               total        used        free      shared\nMem:           7.7Gi       1.8Gi       4.1Gi        12Mi\nSwap:          2.0Gi          0B       2.0Gi",
        "crontab -l":       "# m h dom mon dow command\n*/5 * * * * /home/dbadmin/db_scripts/backup.sh\n0 2 * * * /home/dbadmin/db_scripts/cleanup.sh >> /var/log/cleanup.log 2>&1",
    }
    cmd = command.strip()
    if cmd in STATIC:
        return STATIC[cmd]
    
    try:
        history_text = "\n".join(f"$ {h['cmd']}\n{h['res']}" for h in history[-6:])
        prompt = f"""You are a real Ubuntu 22.04 server terminal. Output ONLY terminal text.
Hostname: corp-prod-db-01 | User: dbadmin
Never say you are AI. Be realistic.

{history_text}
$ {cmd}
"""
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{OLLAMA_HOST}/api/generate", json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 200}
            })
            return resp.json().get("response", f"bash: {cmd}: command not found")
    except:
        return f"bash: {cmd}: command not found"

class HoneypotSession(asyncssh.SSHServerSession):
    def __init__(self, peer_addr):
        self.peer_addr = peer_addr
        self.history = []
        self.buffer = ""

    def shell_requested(self):
        return True

    def connection_made(self, chan):
        self._chan = chan
        chan.write("\r\nWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n")
        chan.write(f"Last login: Mon Jun 23 14:32:10 2025 from 10.0.0.55\r\n")
        chan.write("dbadmin@corp-prod-db-01:~$ ")

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
        
        response = await get_ai_response(command, self.history)
        self.history.append({"cmd": command, "res": response})
        
        await send_log(self.peer_addr, command, response)
        
        self._chan.write(f"\r\n{response}\r\ndbadmin@corp-prod-db-01:~$ ")

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