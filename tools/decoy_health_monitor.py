"""
Decoy Service Health & Port Availability Telemetry Monitor
Performs automated synthetic TCP handshake probes across all 5 honeypot decoys,
measuring connection latency, socket responsiveness, and service availability.
"""
import os
import sys
import time
import socket
import json
import argparse
from typing import Dict, Any, List


DEFAULT_TARGETS = [
    {"name": "shadow-shell", "protocol": "SSH", "host": "127.0.0.1", "port": 2222, "critical": True},
    {"name": "oracle-ai", "protocol": "HTTP", "host": "127.0.0.1", "port": 8080, "critical": True},
    {"name": "vault-sql", "protocol": "PostgreSQL", "host": "127.0.0.1", "port": 5433, "critical": True},
    {"name": "ledger-trap", "protocol": "JSON-RPC", "host": "127.0.0.1", "port": 8545, "critical": True},
    {"name": "forge-ci", "protocol": "HTTP", "host": "127.0.0.1", "port": 9090, "critical": True},
    {"name": "fastapi-backend", "protocol": "HTTP", "host": "127.0.0.1", "port": 3001, "critical": True},
]


def probe_service(target: Dict[str, Any], timeout: float = 2.0) -> Dict[str, Any]:
    """Performs a TCP connection probe and returns connection latency and status."""
    host = target["host"]
    port = target["port"]
    t0 = time.perf_counter()

    result = {
        "name": target["name"],
        "protocol": target["protocol"],
        "endpoint": f"{host}:{port}",
        "reachable": False,
        "latency_ms": None,
        "error": None,
    }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        result["reachable"] = True
        result["latency_ms"] = round(elapsed_ms, 2)
        sock.close()
    except socket.timeout:
        result["error"] = "Connection Timed Out"
    except ConnectionRefusedError:
        result["error"] = "Connection Refused (Service Offline)"
    except Exception as e:
        result["error"] = str(e)

    return result


def monitor_all(targets: List[Dict[str, Any]] = None, timeout: float = 2.0) -> Dict[str, Any]:
    if targets is None:
        targets = DEFAULT_TARGETS

    probes = []
    online_count = 0
    total_count = len(targets)

    for tgt in targets:
        p = probe_service(tgt, timeout=timeout)
        if p["reachable"]:
            online_count += 1
        probes.append(p)

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_services": total_count,
        "online_services": online_count,
        "healthy_percentage": round((online_count / total_count) * 100, 1) if total_count > 0 else 0,
        "services": probes,
    }


def print_status_table(report: Dict[str, Any]):
    print("=" * 75)
    print("DECOY SERVICE HEALTH & NETWORK RESPONSIVENESS REPORT")
    print(f"Timestamp: {report['timestamp']} | Health: {report['online_services']}/{report['total_services']} Online ({report['healthy_percentage']}%)")
    print("=" * 75)
    print(f"{'SERVICE':<18} {'PROTOCOL':<12} {'ENDPOINT':<20} {'STATUS':<12} {'LATENCY'}")
    print("-" * 75)

    for s in report["services"]:
        name = s["name"]
        proto = s["protocol"]
        endpoint = s["endpoint"]
        status = "ONLINE [OK]" if s["reachable"] else "OFFLINE"
        latency = f"{s['latency_ms']} ms" if s["reachable"] else (s.get("error") or "Unreachable")
        print(f"{name:<18} {proto:<12} {endpoint:<20} {status:<12} {latency}")

    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Honeypot Decoy Service Health Monitor")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    parser.add_argument("--timeout", type=float, default=2.0, help="Socket timeout seconds")
    args = parser.parse_args()

    report = monitor_all(timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_status_table(report)


if __name__ == "__main__":
    main()
