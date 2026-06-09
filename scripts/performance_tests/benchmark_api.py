"""
API benchmark — measures latency for each endpoint individually with
a warm-up pass followed by N timed iterations. Reports p50/p95/p99/max.

Usage:
  python scripts/performance_tests/benchmark_api.py
  python scripts/performance_tests/benchmark_api.py --base-url http://localhost:8000 --iterations 50
"""

import argparse
import time
import statistics
import sys
import json
from urllib import request, error as urllib_error

DEFAULT_BASE_URL = "http://localhost:8000"
WARMUP = 3
ITERATIONS = 30

GET_ENDPOINTS = [
    ("GET", "/health",                        None),
    ("GET", "/api/v1/risk/summary",           None),
    ("GET", "/api/v1/risk/metrics",           None),
    ("GET", "/api/v1/portfolios/",            None),
    ("GET", "/api/v1/graph/constellation",    None),
    ("GET", "/api/v1/risk/dna/bench-entity",  None),
    ("GET", "/api/v1/risk/history/bench-entity", None),
    ("GET", "/api/v1/risk/alerts/bench-entity",  None),
    ("POST", "/api/v1/risk/analyze/bench-portfolio", None),
]

POST_PAYLOAD = json.dumps({
    "entity_ids": ["bench-001", "bench-002", "bench-003"]
}).encode()


def timed_request(method: str, url: str, payload=None) -> float:
    """Returns response time in ms, or -1 on error."""
    try:
        data = payload if method == "POST" else None
        req = request.Request(url, data=data, method=method,
                               headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        with request.urlopen(req, timeout=15) as resp:
            _ = resp.read()
        return (time.perf_counter() - t0) * 1000
    except urllib_error.HTTPError as e:
        if e.code < 500:
            # 4xx is still a valid (fast) response
            return (time.perf_counter() - t0) * 1000 if 't0' in dir() else -1
        return -1
    except Exception:
        return -1


def benchmark_endpoint(method: str, url: str, payload=None, warmup: int = WARMUP, iterations: int = ITERATIONS):
    # Warm-up
    for _ in range(warmup):
        timed_request(method, url, payload)

    times = []
    for _ in range(iterations):
        t = timed_request(method, url, payload)
        if t >= 0:
            times.append(t)

    return times


def main():
    parser = argparse.ArgumentParser(description="API benchmark")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    args = parser.parse_args()

    print(f"\nAPI Benchmark — {args.iterations} iterations per endpoint (warmup={WARMUP})")
    print(f"Target: {args.base_url}\n")
    print(f"  {'Method':<6} {'Endpoint':<45} {'p50':>7} {'p95':>7} {'p99':>7} {'max':>7} {'ok':>4}")
    print(f"  {'-' * 85}")

    all_pass = True
    SLA_P95_MS = 500  # 500ms p95 SLA

    for method, path, payload in GET_ENDPOINTS:
        url = f"{args.base_url}{path}"
        times = benchmark_endpoint(method, url, payload, iterations=args.iterations)

        if not times:
            print(f"  {method:<6} {path:<45} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'N/A':>7} {'ERR':>4}")
            all_pass = False
            continue

        p50 = statistics.median(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        p99 = sorted(times)[int(len(times) * 0.99)]
        mx  = max(times)
        ok_count = len(times)

        sla = "PASS" if p95 <= SLA_P95_MS else "FAIL"
        if sla == "FAIL":
            all_pass = False

        print(f"  {method:<6} {path:<45} {p50:>6.0f}ms {p95:>6.0f}ms {p99:>6.0f}ms {mx:>6.0f}ms {ok_count:>4}")

    print(f"\n  SLA: p95 ≤ {SLA_P95_MS}ms per endpoint")
    if all_pass:
        print("  PASS: All endpoints within SLA.\n")
    else:
        print("  FAIL: One or more endpoints exceeded SLA.\n")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
