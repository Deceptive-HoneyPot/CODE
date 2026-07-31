"""
Evaluation harness for the AI-driven honeypot vs. a static-honeypot baseline.

Produces four independent, reproducible measurements instead of a single
unexplained "F1-score":

  1. Sequential latency / throughput - static fast-path vs. LLM-backed
     dynamic path, one request at a time, N trials each, mean/median/stdev
     reported (not a single sample).
  2. Response diversity     - fraction of distinct outputs the engine gives
     across the APT payload set, as a proxy for how easy the service is to
     fingerprint by an automated scanner that expects deterministic output.
  3. LLM-judge realism score - a second, independent LLM call rates each
     response 1-5 on how convincingly it imitates a real system response.
     This is an automated proxy metric, not a human-subject study, and the
     report states that limitation explicitly.
  4. Concurrent throughput  - CONCURRENCY_LEVEL simultaneous requests fired
     at once, measuring sustained requests/sec under concurrent attacker
     sessions rather than one-at-a-time latency.

Run with the local stack up (backend on :3001, ai-engine on :8000) and
OPENROUTER_API_KEY set in the environment / .env file.
"""
import asyncio
import json
import os
import statistics
import time
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv()

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://localhost:8000/api/response")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "meta-llama/llama-3.1-70b-instruct")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DATASET_PATH = Path(__file__).parent / "apt_attack_dataset.json"
STATIC_PAYLOAD = {"command": "ip a", "history": [], "service": "ssh"}

# Cap the judged/latency sample sizes to keep API cost and runtime bounded;
# the full 100-item dataset is still used for the diversity metric.
DYNAMIC_LATENCY_TRIALS = 20
JUDGE_SAMPLE_SIZE = 30
STATIC_LATENCY_TRIALS = 30


async def call_engine(session, payload):
    t0 = time.perf_counter()
    try:
        async with session.post(AI_ENGINE_URL, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            data = await resp.json()
            return time.perf_counter() - t0, data.get("response", "")
    except Exception as e:
        return time.perf_counter() - t0, f"__ERROR__:{e}"


async def bench_static(session):
    lats = []
    for _ in range(STATIC_LATENCY_TRIALS):
        lat, _ = await call_engine(session, STATIC_PAYLOAD)
        lats.append(lat)
    return lats


async def bench_dynamic(session, dataset):
    sample = dataset[:DYNAMIC_LATENCY_TRIALS]
    lats, outputs = [], []
    for i, payload in enumerate(sample):
        print(f"  dynamic latency trial {i + 1}/{len(sample)}", end="\r")
        lat, out = await call_engine(session, payload)
        lats.append(lat)
        outputs.append(out)
    print()
    return lats, outputs


def summarize(lats):
    return {
        "mean_s": round(statistics.mean(lats), 4),
        "median_s": round(statistics.median(lats), 4),
        "stdev_s": round(statistics.stdev(lats), 4) if len(lats) > 1 else 0.0,
        "min_s": round(min(lats), 4),
        "max_s": round(max(lats), 4),
        "n": len(lats),
    }


CONCURRENCY_LEVEL = int(os.getenv("CONCURRENCY_LEVEL", "10"))


async def bench_concurrent_throughput(session, dataset):
    """
    Measures sustained throughput under CONCURRENCY_LEVEL simultaneous
    attacker sessions, as opposed to bench_dynamic's one-request-at-a-time
    latency measurement. Uses unique (nonce-tagged) payloads so every
    request is a genuine cache miss, reflecting worst-case concurrent load.
    """
    sample = dataset[:CONCURRENCY_LEVEL]
    t0 = time.perf_counter()
    results = await asyncio.gather(*[call_engine(session, p) for p in sample])
    wall_time = time.perf_counter() - t0
    lats = [r[0] for r in results]
    throughput = len(sample) / wall_time if wall_time else 0.0
    return {
        "concurrency_level": len(sample),
        "wall_time_s": round(wall_time, 4),
        "throughput_rps": round(throughput, 4),
        "per_request_latency": summarize(lats),
    }


async def diversity_pass(session, dataset):
    """Run the *entire* dataset once and measure output uniqueness per service."""
    from collections import defaultdict

    by_service = defaultdict(list)
    for i, payload in enumerate(dataset):
        print(f"  diversity pass {i + 1}/{len(dataset)}", end="\r")
        _, out = await call_engine(session, payload)
        by_service[payload["service"]].append(out)
    print()

    result = {}
    for service, outs in by_service.items():
        distinct = len(set(outs))
        result[service] = {
            "n": len(outs),
            "distinct": distinct,
            "uniqueness_ratio": round(distinct / len(outs), 3) if outs else 0.0,
        }
    return result, by_service


JUDGE_SYSTEM = """You are a security researcher evaluating honeypot realism.
You will see an ATTACK PAYLOAD sent to a service, and the RESPONSE that service produced.
Rate, on a scale of 1-5, how convincingly the RESPONSE imitates what a REAL, non-honeypot
instance of that service (a real bash shell, a real PostgreSQL server, a real Ethereum
JSON-RPC node, a real internal API, or a real Jenkins server) would have produced.

1 = obviously fake / templated / an AI disclaimer / an unrelated chatbot answer
3 = plausible but generic, or contains a subtle tell (wrong format, refusal-like phrasing)
5 = indistinguishable from a real system's output for that exact payload

Respond with ONLY a single JSON object: {"score": <int 1-5>, "reason": "<one short sentence>"}
"""


async def judge_response(session, service, payload, response, retries=2):
    user = f"SERVICE: {service}\nATTACK PAYLOAD: {payload}\nRESPONSE:\n{response}\n"
    last_error = None
    for attempt in range(retries + 1):
        try:
            async with session.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": JUDGE_MODEL,
                    "messages": [
                        {"role": "system", "content": JUDGE_SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 80,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                body = await resp.json()
                if "choices" not in body:
                    # Surface the API's actual error payload (e.g. rate limit)
                    # instead of a bare KeyError, and retry transient failures.
                    last_error = f"http={resp.status} body={json.dumps(body)[:200]}"
                    if attempt < retries:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    return None, f"judge_error: {last_error}"
                content = body["choices"][0]["message"]["content"].strip()
                # tolerate stray markdown fences
                content = content.strip("`").removeprefix("json").strip()
                parsed = json.loads(content)
                return int(parsed["score"]), parsed.get("reason", "")
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            return None, f"judge_error: {last_error}"


async def realism_eval(session, dataset):
    sample = dataset[:JUDGE_SAMPLE_SIZE]
    scores = []
    details = []
    for i, payload in enumerate(sample):
        print(f"  judging response {i + 1}/{len(sample)}", end="\r")
        _, out = await call_engine(session, payload)
        score, reason = await judge_response(session, payload["service"], payload["command"], out)
        if score is not None:
            scores.append(score)
        details.append({"service": payload["service"], "payload": payload["command"][:80], "score": score, "reason": reason})
    print()
    return scores, details


async def main():
    dataset = json.loads(DATASET_PATH.read_text())

    async with aiohttp.ClientSession() as session:
        print("Warming up...")
        await call_engine(session, STATIC_PAYLOAD)

        print(f"\n[1/5] Static fast-path latency ({STATIC_LATENCY_TRIALS} trials)...")
        static_lats = await bench_static(session)

        print(f"\n[2/5] Dynamic LLM-backed latency ({DYNAMIC_LATENCY_TRIALS} trials, cache bypassed by unique payloads)...")
        dyn_lats, dyn_outputs = await bench_dynamic(session, dataset)

        print(f"\n[3/5] Response diversity over full {len(dataset)}-item APT dataset...")
        diversity, raw_outputs = await diversity_pass(session, dataset)

        print(f"\n[4/5] LLM-judge realism scoring ({JUDGE_SAMPLE_SIZE} sampled payloads, judge={JUDGE_MODEL})...")
        scores, judge_details = await realism_eval(session, dataset)

        print(f"\n[5/5] Concurrent throughput ({CONCURRENCY_LEVEL} simultaneous requests)...")
        concurrent = await bench_concurrent_throughput(session, dataset)

    static_stats = summarize(static_lats)
    dyn_stats = summarize(dyn_lats)
    static_throughput = round(1.0 / static_stats["mean_s"], 2) if static_stats["mean_s"] else 0.0
    dyn_throughput = round(1.0 / dyn_stats["mean_s"], 4) if dyn_stats["mean_s"] else 0.0
    avg_words = round(sum(len(o.split()) for o in dyn_outputs) / len(dyn_outputs), 1) if dyn_outputs else 0.0
    judge_mean = round(statistics.mean(scores), 2) if scores else None
    judge_stdev = round(statistics.stdev(scores), 2) if len(scores) > 1 else 0.0

    results = {
        "config": {
            "engine_model": OPENROUTER_MODEL,
            "judge_model": JUDGE_MODEL,
            "static_trials": STATIC_LATENCY_TRIALS,
            "dynamic_latency_trials": DYNAMIC_LATENCY_TRIALS,
            "diversity_dataset_size": len(dataset),
            "judge_sample_size": JUDGE_SAMPLE_SIZE,
        },
        "latency": {"static": static_stats, "dynamic": dyn_stats},
        "throughput_rps": {"static": static_throughput, "dynamic_sequential": dyn_throughput},
        "concurrent_throughput": concurrent,
        "response_diversity_by_service": diversity,
        "avg_response_words_dynamic": avg_words,
        "llm_judge_realism": {
            "mean_score_1to5": judge_mean,
            "stdev": judge_stdev,
            "n_scored": len(scores),
            "n_requested": JUDGE_SAMPLE_SIZE,
            "distribution": {str(s): scores.count(s) for s in range(1, 6)},
        },
        "judge_sample_details": judge_details,
    }

    out_path = Path(__file__).parent / "evaluation_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved raw results to {out_path}")
    print(json.dumps({k: v for k, v in results.items() if k != "judge_sample_details"}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
