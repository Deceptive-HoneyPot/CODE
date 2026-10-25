"""
Shared pytest fixtures and mock environments for the Cyber Deception Framework test suite.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root, backend, and ai-engine to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
AI_ENGINE_DIR = os.path.join(BASE_DIR, "ai-engine")

for d in [BASE_DIR, BACKEND_DIR, AI_ENGINE_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Mock web3 if not installed in the current environment
try:
    import web3
except ImportError:
    mock_web3_module = MagicMock()
    mock_w3_class = MagicMock()
    mock_web3_module.Web3 = mock_w3_class
    sys.modules["web3"] = mock_web3_module


@pytest.fixture
def mock_redis():
    """Mock Redis client simulating key-value storage and list operations."""
    store = {}
    lists = {}

    m = MagicMock()

    def get(key):
        return store.get(key)

    def set_val(key, val, ex=None):
        store[key] = str(val)
        return True

    def lpush(key, *values):
        if key not in lists:
            lists[key] = []
        for v in values:
            lists[key].insert(0, str(v))
        return len(lists[key])

    def lrange(key, start, end):
        lst = lists.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start : end + 1]

    def ltrim(key, start, end):
        if key in lists:
            if end == -1:
                lists[key] = lists[key][start:]
            else:
                lists[key] = lists[key][start : end + 1]
        return True

    def incr(key):
        val = int(store.get(key, 0)) + 1
        store[key] = str(val)
        return val

    def ping():
        return True

    m.get.side_effect = get
    m.set.side_effect = set_val
    m.lpush.side_effect = lpush
    m.lrange.side_effect = lrange
    m.ltrim.side_effect = ltrim
    m.incr.side_effect = incr
    m.ping.side_effect = ping
    m._store = store
    m._lists = lists
    return m


@pytest.fixture
def mock_w3_instance():
    """Mock Web3 instance simulating Ethereum transaction anchoring."""
    w3 = MagicMock()
    w3.is_connected.return_value = True
    w3.eth.accounts = ["0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"]

    tx_hashes = []

    def send_tx(tx_data):
        tx_hash = "0x" + "a1b2c3d4e5" * 6 + "deadbeef"
        tx_hashes.append((tx_data, tx_hash))
        return tx_hash

    w3.eth.send_transaction.side_effect = send_tx
    w3.to_bytes.side_effect = lambda hexstr: bytes.fromhex(hexstr.replace("0x", ""))
    w3._tx_hashes = tx_hashes
    return w3
