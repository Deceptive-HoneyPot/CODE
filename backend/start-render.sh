#!/bin/sh
# Start Ganache on localhost, wait until it answers, then run the API.
# The chain is in memory: it resets when the service restarts or redeploys.
set -e

ganache --chain.chainId 1337 --wallet.totalAccounts 5 --wallet.defaultBalance 1000 \
    --server.host 127.0.0.1 --server.port 7545 --logging.quiet &

python3 - <<'EOF'
import time, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:7545",
    data=b'{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}',
    headers={"Content-Type": "application/json"},
)
for _ in range(60):
    try:
        urllib.request.urlopen(req, timeout=2)
        print("[start] ganache ready")
        break
    except Exception:
        time.sleep(1)
else:
    print("[start] ganache not ready after 60s; starting API anyway")
EOF

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-3001}"
