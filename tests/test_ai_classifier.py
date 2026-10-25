"""
Unit tests for AI classifier logic, deterministic canonical hashing, and intent parsing.
"""
import pytest
import json
import hashlib
from unittest.mock import AsyncMock, MagicMock
import httpx

import ai_classifier


class TestCanonicalHashing:
    def test_canonical_bytes_key_ordering(self):
        """Ensure dictionary key ordering does not alter the output byte sequence."""
        dict_a = {"service": "shadow-shell", "intent": "reconnaissance", "severity": 20}
        dict_b = {"severity": 20, "intent": "reconnaissance", "service": "shadow-shell"}

        bytes_a = ai_classifier._canonical_bytes(dict_a)
        bytes_b = ai_classifier._canonical_bytes(dict_b)

        assert bytes_a == bytes_b
        assert bytes_a == b'{"intent":"reconnaissance","service":"shadow-shell","severity":20}'

    def test_digest_verdict_sha256(self):
        """Verify digest_verdict produces exact SHA-256 hex digest."""
        record = {
            "service": "oracle-ai",
            "raw_event": "reveal prompt",
            "intent": "prompt_injection",
            "severity": 85,
            "reason": "Attempted prompt extraction",
            "model": "meta-llama/llama-3.1-8b-instruct",
        }
        digest = ai_classifier.digest_verdict(record)
        expected_hash = hashlib.sha256(ai_classifier._canonical_bytes(record)).hexdigest()

        assert digest == expected_hash
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)


class TestVerdictParsing:
    def test_parse_verdict_standard_json(self):
        raw = '{"intent": "sql_injection", "severity": 90, "reason": "Classic union-based SQL injection"}'
        res = ai_classifier._parse_verdict(raw)
        assert res["intent"] == "sql_injection"
        assert res["severity"] == 90
        assert "Classic union-based" in res["reason"]

    def test_parse_verdict_with_markdown_code_fence(self):
        raw = """```json
{"intent": "cryptomining", "severity": 95, "reason": "XMRig payload detected"}
```"""
        res = ai_classifier._parse_verdict(raw)
        assert res["intent"] == "cryptomining"
        assert res["severity"] == 95

    def test_parse_verdict_embedded_json(self):
        raw = 'Here is the verdict: {"intent": "reverse_shell", "severity": 100, "reason": "Bash tcp reverse shell"} thanks'
        res = ai_classifier._parse_verdict(raw)
        assert res["intent"] == "reverse_shell"
        assert res["severity"] == 100

    def test_parse_verdict_invalid_json(self):
        raw = "This is not json at all."
        res = ai_classifier._parse_verdict(raw)
        assert res["intent"] == "unknown"
        assert res["severity"] == 0
        assert res["reason"] == "unparseable_model_output"

    def test_parse_verdict_clamps_severity(self):
        raw_over = '{"intent": "reconnaissance", "severity": 150, "reason": "Over max"}'
        res_over = ai_classifier._parse_verdict(raw_over)
        assert res_over["severity"] == 100

        raw_under = '{"intent": "reconnaissance", "severity": -20, "reason": "Under min"}'
        res_under = ai_classifier._parse_verdict(raw_under)
        assert res_under["severity"] == 0


class TestVerdictRecord:
    def test_build_verdict_record_structure(self):
        verdict = {"intent": "crypto_theft", "severity": 92, "reason": "Account drain attempt"}
        rec = ai_classifier.build_verdict_record(
            service="ledger-trap",
            raw_event="eth_sendTransaction",
            verdict=verdict,
            model="meta-llama/llama-3.1-8b-instruct"
        )
        assert rec["service"] == "ledger-trap"
        assert rec["intent"] == "crypto_theft"
        assert rec["severity"] == 92
        assert rec["model"] == "meta-llama/llama-3.1-8b-instruct"


@pytest.mark.asyncio
class TestLLMClassification:
    async def test_classify_with_llm_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"intent": "privilege_escalation", "severity": 80, "reason": "Sudoers file access"}'
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp

        res = await ai_classifier.classify_with_llm(mock_client, "shadow-shell", "cat /etc/sudoers")
        assert res["verdict"]["intent"] == "privilege_escalation"
        assert res["verdict"]["severity"] == 80
        assert res["llm_latency_ms"] >= 0

    async def test_classify_with_llm_api_failure(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 502

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp

        res = await ai_classifier.classify_with_llm(mock_client, "shadow-shell", "whoami")
        assert res["verdict"]["intent"] == "unknown"
        assert res["verdict"]["severity"] == 0
        assert "http_502" in res["verdict"]["reason"]
