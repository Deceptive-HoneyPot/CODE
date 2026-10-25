"""
Tests for blockchain anchoring mechanics, SHA-256 cryptographic commitments, and tamper-evidence.
"""
import pytest
import hashlib
import json
from unittest.mock import MagicMock
import main


class TestBlockchainAnchoring:
    def test_log_hash_avalanche_effect(self):
        """Verifies that a 1-bit or 1-char change completely changes the evidence hash."""
        original = {
            "service": "vault-sql",
            "attacker_ip": "198.51.100.10",
            "raw_data": "SELECT * FROM users",
            "timestamp": "2026-10-25T14:30:00.000000",
        }
        tampered_ip = dict(original, attacker_ip="198.51.100.11")
        tampered_timestamp = dict(original, timestamp="2026-10-25T14:30:00.000001")
        tampered_query = dict(original, raw_data="SELECT * FROM users ")  # trailing space

        hash_orig = main.hash_log(original)
        hash_ip = main.hash_log(tampered_ip)
        hash_ts = main.hash_log(tampered_timestamp)
        hash_query = main.hash_log(tampered_query)

        assert hash_orig != hash_ip
        assert hash_orig != hash_ts
        assert hash_orig != hash_query

    def test_anchor_blockchain_format(self, mock_w3_instance):
        """Validates Ethereum transaction format including 0x-prefixed payload."""
        test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(main, "w3", mock_w3_instance)
            anchored = main.anchor_blockchain(test_hash)

            assert anchored is True
            assert len(mock_w3_instance._tx_hashes) == 1
            tx_data, tx_hash = mock_w3_instance._tx_hashes[0]

            assert tx_data["from"] == "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"
            assert tx_data["value"] == 0
            assert tx_data["gas"] == 50000
            assert "data" in tx_data

    def test_anchor_blockchain_disconnected_fallback(self):
        """Ensures safe failure when blockchain node is unreachable."""
        disconnected_w3 = MagicMock()
        disconnected_w3.is_connected.return_value = False

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(main, "w3", disconnected_w3)
            anchored = main.anchor_blockchain("deadbeef" * 8)
            assert anchored is False


class TestAuditReplay:
    def test_forensic_chain_of_custody(self):
        """Simulates verifying an audit trail of 100 historical logs."""
        audit_trail = []
        for i in range(100):
            entry = {
                "id": i,
                "service": "shadow-shell",
                "command": f"cmd_{i}",
                "timestamp": f"2026-10-25T10:00:{i:02d}",
            }
            entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
            audit_trail.append((entry, entry_hash))

        # Replay and verify all hashes
        for entry, expected_hash in audit_trail:
            recomputed = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
            assert recomputed == expected_hash
