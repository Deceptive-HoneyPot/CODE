"""
Unit tests for the Adversary Campaign Simulator.
"""
import pytest
from unittest.mock import patch
from tools.adversary_simulator import CAMPAIGN_PROFILES, execute_step, run_campaign


class TestAdversarySimulator:
    def test_campaign_profiles_exist(self):
        assert "APT29" in CAMPAIGN_PROFILES
        assert "FIN7" in CAMPAIGN_PROFILES
        assert "CRYPTO_DRAINER" in CAMPAIGN_PROFILES
        assert "LLM_JAILBREAK" in CAMPAIGN_PROFILES

        for name, profile in CAMPAIGN_PROFILES.items():
            assert "name" in profile
            assert "steps" in profile
            assert len(profile["steps"]) > 0

    @patch("tools.adversary_simulator.execute_step")
    def test_run_campaign_mocked(self, mock_exec):
        mock_exec.return_value = {"status": "ok", "hash": "abcdef123456", "blockchain": True}
        res = run_campaign("http://localhost:3001", "FIN7", delay=0)

        assert res["profile"] == "FIN7"
        assert res["total_steps"] == len(CAMPAIGN_PROFILES["FIN7"]["steps"])
        assert len(res["results"]) == len(CAMPAIGN_PROFILES["FIN7"]["steps"])
        assert mock_exec.call_count == len(CAMPAIGN_PROFILES["FIN7"]["steps"])
