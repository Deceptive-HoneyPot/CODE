"""
Demonstrates the tamper-evidence property claimed for the blockchain-anchored
logging pipeline: re-hash a stored log entry and compare against its recorded
hash (the same hash that was anchored on-chain in backend/main.py::anchor_blockchain).
A mismatch proves the entry was altered after logging.
"""
import hashlib
import json
import sys

import requests

BACKEND_URL = "http://localhost:3001"


def hash_log(data: dict) -> str:
    # Must exactly mirror backend/main.py::hash_log for the comparison to be valid.
    fields = {k: v for k, v in data.items() if k not in ("hash", "blockchain_anchored")}
    serialized = json.dumps(fields, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def main():
    logs = requests.get(f"{BACKEND_URL}/api/logs?limit=1").json()
    if not logs:
        print("No logs found — POST to /api/log first.")
        sys.exit(1)

    original = logs[0]
    recorded_hash = original["hash"]
    print("Fetched log entry:", json.dumps(original, indent=2))

    recomputed = hash_log(original)
    print(f"\nRecorded hash:   {recorded_hash}")
    print(f"Recomputed hash: {recomputed}")
    print("Untampered match:", recomputed == recorded_hash)

    tampered = dict(original)
    tampered["raw_data"] = "ls -la"
    tampered_hash = hash_log(tampered)
    print(f"\nTampered hash:   {tampered_hash}")
    print("Tamper detected (hash mismatch vs. on-chain-anchored hash):",
          tampered_hash != recorded_hash)


if __name__ == "__main__":
    main()
