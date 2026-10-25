"""
Unit tests for the Decoy Service Health & Availability Monitor.
"""
import pytest
from unittest.mock import patch, MagicMock
from tools.decoy_health_monitor import probe_service, monitor_all, DEFAULT_TARGETS


class TestDecoyHealthMonitor:
    def test_default_targets_structure(self):
        assert len(DEFAULT_TARGETS) >= 5
        names = {t["name"] for t in DEFAULT_TARGETS}
        assert "shadow-shell" in names
        assert "oracle-ai" in names
        assert "vault-sql" in names
        assert "ledger-trap" in names
        assert "forge-ci" in names

    @patch("socket.socket")
    def test_probe_service_success(self, mock_socket_class):
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        target = {"name": "shadow-shell", "protocol": "SSH", "host": "127.0.0.1", "port": 2222}
        result = probe_service(target, timeout=1.0)

        assert result["reachable"] is True
        assert result["name"] == "shadow-shell"
        assert result["latency_ms"] is not None
        assert result["error"] is None
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    def test_probe_service_connection_refused(self, mock_socket_class):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_sock

        target = {"name": "vault-sql", "protocol": "PostgreSQL", "host": "127.0.0.1", "port": 5433}
        result = probe_service(target, timeout=1.0)

        assert result["reachable"] is False
        assert "Connection Refused" in result["error"]

    @patch("tools.decoy_health_monitor.probe_service")
    def test_monitor_all_aggregation(self, mock_probe):
        mock_probe.side_effect = [
            {"name": "s1", "reachable": True, "latency_ms": 1.5, "protocol": "SSH", "endpoint": "127.0.0.1:2222"},
            {"name": "s2", "reachable": False, "error": "Offline", "protocol": "HTTP", "endpoint": "127.0.0.1:8080"},
        ]
        targets = [
            {"name": "s1", "protocol": "SSH", "host": "127.0.0.1", "port": 2222},
            {"name": "s2", "protocol": "HTTP", "host": "127.0.0.1", "port": 8080},
        ]
        report = monitor_all(targets)
        assert report["total_services"] == 2
        assert report["online_services"] == 1
        assert report["healthy_percentage"] == 50.0
