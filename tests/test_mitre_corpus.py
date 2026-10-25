"""
Unit tests for the MITRE ATT&CK Corpus dataset structure and schema validation.
"""
import pytest
import os
import json


@pytest.fixture
def corpus_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, "data", "mitre_attack_corpus.json")
    assert os.path.exists(corpus_path), f"Corpus file missing at {corpus_path}"
    with open(corpus_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestMITRECorpus:
    def test_corpus_non_empty(self, corpus_data):
        assert isinstance(corpus_data, list)
        assert len(corpus_data) >= 10

    def test_entry_required_fields(self, corpus_data):
        required_fields = {
            "id",
            "technique_id",
            "technique_name",
            "tactic_id",
            "tactic_name",
            "target_service",
            "severity_score",
            "payload",
            "intent_label",
        }
        valid_services = {"shadow-shell", "vault-sql", "oracle-ai", "ledger-trap", "forge-ci"}

        for entry in corpus_data:
            assert required_fields.issubset(entry.keys())
            assert entry["id"].startswith("ATTACK-")
            assert entry["technique_id"].startswith("T")
            assert entry["tactic_id"].startswith("TA")
            assert entry["target_service"] in valid_services
            assert 0 <= entry["severity_score"] <= 100
            assert len(entry["payload"]) > 0
