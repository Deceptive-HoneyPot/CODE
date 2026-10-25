"""
Unit tests for the Performance & Latency Distribution Profiler.
"""
import pytest
from tools.performance_profiler import calculate_metrics, simulate_tier_benchmark


class TestPerformanceProfiler:
    def test_calculate_metrics_empty(self):
        m = calculate_metrics([])
        assert m["count"] == 0
        assert m["mean_ms"] == 0.0

    def test_calculate_metrics_values(self):
        samples = [10.0, 20.0, 30.0, 40.0, 50.0]
        m = calculate_metrics(samples)
        assert m["count"] == 5
        assert m["mean_ms"] == 30.0
        assert m["min_ms"] == 10.0
        assert m["max_ms"] == 50.0
        assert m["p50_ms"] == 30.0

    def test_simulate_tier_benchmark(self):
        report = simulate_tier_benchmark(iterations=30)
        assert "static_tier" in report
        assert "cache_tier" in report
        assert "llm_tier" in report

        # Verify static is faster than cache, and cache is faster than LLM
        assert report["static_tier"]["mean_ms"] < report["cache_tier"]["mean_ms"]
        assert report["cache_tier"]["mean_ms"] < report["llm_tier"]["mean_ms"]
