"""
LLM-driven attacker-intent classifier and on-chain verdict anchor.

Distinct from classify_intent() in main.py, which is a fixed keyword-rule
classifier. This module asks a live LLM (via OpenRouter, same provider the
ai-engine decoy responses already use) to independently label the same
captured event, and returns a structured verdict: an intent category, a
0-100 severity score, and a one-line rationale. The verdict is anchored
on-chain the same way an evidence hash is anchored in main.py, so the
AI's decision -- not just the raw event -- becomes tamper-evident: an
attacker (or anyone downstream) cannot alter what the model concluded
after the fact without the change being detectable against the chain.

This file has no import-time dependency on main.py so it can be benchmarked
standalone (see ../benchmark_ai_verdicts.py).
"""
import hashlib
import json
import os
import time

import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

INTENT_CATEGORIES = [
    "reconnaissance",
    "privilege_escalation",
    "sql_injection",
    "reverse_shell",
    "cryptomining",
    "crypto_theft",
    "prompt_injection",
    "supply_chain",
    "unknown",
]

VERDICT_SYSTEM_PROMPT = f"""You are a security analyst classifying a single captured honeypot event.
Choose exactly one intent category from this fixed list: {", ".join(INTENT_CATEGORIES)}.
Also assign a severity score from 0 to 100 (0 = harmless noise, 100 = active high-impact compromise).
Respond with ONLY a compact JSON object on one line, no markdown, no explanation outside the JSON:
{{"intent": "<one category>", "severity": <integer 0-100>, "reason": "<max 12 words>"}}
"""


def _canonical_bytes(record: dict) -> bytes:
    """Deterministic byte encoding: sorted keys, fixed separators. Mirrors
    the canonicalization discipline used for evidence hashing elsewhere in
    the pipeline, applied here to the verdict record instead of the raw
    event, so a verdict can be independently re-hashed and compared against
    its on-chain commitment."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()


def digest_verdict(verdict_record: dict) -> str:
    return hashlib.sha256(_canonical_bytes(verdict_record)).hexdigest()


def _fallback_verdict(reason: str) -> dict:
    return {"intent": "unknown", "severity": 0, "reason": reason}


def _parse_verdict(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    # Models occasionally wrap JSON in a code fence despite instructions; strip it.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    try:
        obj = json.loads(raw_text)
    except json.JSONDecodeError:
        start, end = raw_text.find("{"), raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return _fallback_verdict("unparseable_model_output")
        try:
            obj = json.loads(raw_text[start:end + 1])
        except json.JSONDecodeError:
            return _fallback_verdict("unparseable_model_output")

    intent = str(obj.get("intent", "unknown")).strip().lower()
    if intent not in INTENT_CATEGORIES:
        intent = "unknown"
    try:
        severity = int(obj.get("severity", 0))
    except (TypeError, ValueError):
        severity = 0
    severity = max(0, min(100, severity))
    reason = str(obj.get("reason", ""))[:200]
    return {"intent": intent, "severity": severity, "reason": reason}


async def classify_with_llm(client: httpx.AsyncClient, service: str, raw_event: str) -> dict:
    """Calls the LLM once for a single event and returns a verdict dict plus
    timing. Raises no exception on API failure -- returns a fallback verdict
    so a benchmark loop can keep running and record the failure as a data
    point rather than aborting."""
    t0 = time.perf_counter()
    user_prompt = f"Service: {service}\nCaptured event: {raw_event}\nJSON verdict:"
    try:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": VERDICT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 80,
            },
            timeout=30.0,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if resp.status_code != 200:
            verdict = _fallback_verdict(f"http_{resp.status_code}")
        else:
            body = resp.json()
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            verdict = _parse_verdict(content)
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        verdict = _fallback_verdict(f"error:{type(e).__name__}")

    return {"verdict": verdict, "llm_latency_ms": elapsed_ms}


def build_verdict_record(service: str, raw_event: str, verdict: dict, model: str) -> dict:
    """The record that gets canonicalized, hashed, and anchored -- the
    'decision', not the raw captured payload. Keeping this separate from the
    evidence-hash record in main.py is deliberate: a verdict is an AI
    inference, not an attacker-supplied fact, and anchoring it lets a third
    party later prove what the model concluded at classification time,
    independent of whatever the raw log later shows or is claimed to show."""
    return {
        "service": service,
        "raw_event": raw_event,
        "intent": verdict["intent"],
        "severity": verdict["severity"],
        "reason": verdict["reason"],
        "model": model,
    }
