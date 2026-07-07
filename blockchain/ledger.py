from web3 import Web3
import hashlib
import json
from datetime import datetime
import redis

# Connect to Ganache local blockchain
w3 = Web3(Web3.HTTPProvider("http://localhost:7545"))
cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Your deployed contract address (set after running deploy.py)
CONTRACT_ADDRESS = ""  # Fill after deployment
CONTRACT_ABI = []      # Fill after deployment

class BlockchainLedger:
    def __init__(self):
        if not w3.is_connected():
            raise Exception("Cannot connect to Ganache blockchain!")
        
        # Use the first Ganache account as the signer
        self.account = w3.eth.accounts[0]
        self.log_queue = []
        print(f"[LEDGER] Connected to blockchain. Account: {self.account}")

    def hash_log_entry(self, log_data: dict) -> str:
        """Create SHA-256 hash of a log entry"""
        # Sort keys for deterministic hashing
        serialized = json.dumps(log_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def anchor_to_blockchain(self, log_data: dict) -> str:
        """Hash the log and write the hash to the blockchain"""
        log_hash = self.hash_log_entry(log_data)
        
        try:
            # Send a simple ETH transaction where data = our log hash
            # This permanently records the hash on-chain
            tx_hash = w3.eth.send_transaction({
                "from": self.account,
                "to": self.account,      # Send to self (just to record data)
                "value": 0,
                "data": w3.to_bytes(hexstr="0x" + log_hash),
                "gas": 50000,
            })
            
            # Also store in Redis for fast retrieval by dashboard
            cache.lpush("honeypot:logs", json.dumps({
                **log_data,
                "hash": log_hash,
                "tx_hash": tx_hash.hex(),
                "blockchain_anchored": True,
                "anchored_at": datetime.now().isoformat()
            }))
            # Keep only last 10,000 logs in Redis
            cache.ltrim("honeypot:logs", 0, 9999)
            
            print(f"[LEDGER] Log anchored. Hash: {log_hash[:16]}... TX: {tx_hash.hex()[:16]}...")
            return log_hash
            
        except Exception as e:
            print(f"[LEDGER] Blockchain error: {e}")
            # Even if blockchain fails, save to Redis
            cache.lpush("honeypot:logs", json.dumps({
                **log_data,
                "hash": log_hash,
                "blockchain_anchored": False
            }))
            return log_hash

    def verify_log_integrity(self, log_data: dict, expected_hash: str) -> bool:
        """Verify a log hasn't been tampered with"""
        computed = self.hash_log_entry(log_data)
        return computed == expected_hash

    def get_recent_logs(self, count=100) -> list:
        """Get recent logs from Redis cache"""
        raw_logs = cache.lrange("honeypot:logs", 0, count - 1)
        return [json.loads(log) for log in raw_logs]

ledger = BlockchainLedger()