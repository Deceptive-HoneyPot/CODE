"""
Unit tests for the Honeypot Operator & Telemetry CLI tool.
"""
import pytest
from unittest.mock import patch, MagicMock
from tools.honeypot_cli import cmd_status, cmd_logs, cmd_verify, cmd_simulate


class TestHoneypotCLI:
    @patch("tools.honeypot_cli.get_json")
    def test_cmd_status_online(self, mock_get_json, capsys):
        mock_get_json.side_effect = [
            {"status": "ok", "redis": True, "blockchain": True},
            {"total": 42, "lifetime_total": 105, "top_ips": [("198.51.100.1", 10)]},
        ]
        args = MagicMock(backend="http://localhost:3001")
        cmd_status(args)

        captured = capsys.readouterr().out
        assert "ONLINE" in captured
        assert "CONNECTED [OK]" in captured
        assert "Total Events Captured : 42" in captured

    @patch("tools.honeypot_cli.get_json")
    def test_cmd_logs_table(self, mock_get_json, capsys):
        mock_get_json.return_value = [
            {
                "timestamp": "2026-10-25T12:00:00",
                "service": "shadow-shell",
                "intent": "privilege_escalation",
                "attacker_ip": "10.0.0.1",
                "blockchain_anchored": True,
            }
        ]
        args = MagicMock(backend="http://localhost:3001", limit=10, filter_intent=None)
        cmd_logs(args)

        captured = capsys.readouterr().out
        assert "shadow-shell" in captured
        assert "privilege_escalation" in captured
        assert "YES [ETH]" in captured

    @patch("tools.honeypot_cli.post_json")
    @patch("tools.honeypot_cli.get_json")
    def test_cmd_verify_audit(self, mock_get_json, mock_post_json, capsys):
        mock_get_json.return_value = [{"service": "oracle-ai", "digest": "abc"}]
        mock_post_json.return_value = {"match": True}

        args = MagicMock(backend="http://localhost:3001", limit=10)
        cmd_verify(args)

        captured = capsys.readouterr().out
        assert "Verified Intact: 1" in captured
