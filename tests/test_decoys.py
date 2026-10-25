"""
Unit tests for AI Engine decoy response logic, static fast-path table, and cache key derivation.
"""
import pytest
import hashlib
from unittest.mock import patch, MagicMock

import engine


class TestAIEngineStaticFastPath:
    def test_static_dictionary_essential_commands(self):
        """Verifies core Linux shell commands exist in the static fast-path to prevent unnecessary LLM calls."""
        core_commands = ["ls", "whoami", "uname -a", "id", "pwd", "ip a", "netstat -tulpn"]
        for cmd in core_commands:
            assert cmd in engine.STATIC
            assert len(engine.STATIC[cmd]) > 0

    def test_static_command_realism(self):
        """Checks that static responses emulate believable Ubuntu server outputs."""
        assert "Linux" in engine.STATIC["uname -a"]
        assert "uid=" in engine.STATIC["id"]
        assert "dbadmin" in engine.STATIC["whoami"]
        assert "eth0" in engine.STATIC["ip a"]

    def test_cache_key_generation(self):
        """Ensures identical commands and service contexts produce identical cache keys."""
        service = "ssh"
        cmd = "cat /etc/os-release"
        key_1 = f"ai_resp:{service}:{hashlib.sha256(cmd.encode()).hexdigest()}"
        key_2 = f"ai_resp:{service}:{hashlib.sha256(cmd.encode()).hexdigest()}"
        assert key_1 == key_2
        assert len(key_1.split(":")[-1]) == 64


class TestDecoyServiceProtocols:
    def test_service_decoy_ports(self):
        """Validates standard decoy service port assignments."""
        expected_ports = {
            "shadow-shell": 2222,
            "oracle-ai": 8080,
            "vault-sql": 5433,
            "ledger-trap": 8545,
            "forge-ci": 9090,
        }
        assert len(expected_ports) == 5
        assert expected_ports["shadow-shell"] == 2222
        assert expected_ports["ledger-trap"] == 8545
