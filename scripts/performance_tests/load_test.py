"""
Load test for the AI Risk Constellation System API.
Uses concurrent threads to simulate multiple users hitting key endpoints simultaneously.
Measures: response time, error rate, and throughput.

Usage:
  python scripts/performance_tests/load_test.py
  python scripts/performance_tests/load_test.py --base-url http://localhost:8000 --users 20 --duration 30
"""

import argparse
import threading
import time
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from urllib import request, error as urllib_error

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_USERS = 10
DEFAULT_DURATION = 20  # seconds

ENDPOINTS = [
    "/health",
    "/api/v1/risk/summary",
    "/api/v1/risk/metrics",
    "/api/v1/portfolios/",
    "/api/v1/graph/constellation",
]


# ── Worker ─────────────────────────────────────────────────────────────────────

results_lock = threading.Lock()
results: dict[str, list] = defaultdict(list)
errors: dict[str, int] = defaultdict(int)
stop_event = threading.Event()


def worker(base_url: str, user_id: int):
    """Continuously hit endpoints until stop_event is set."""
    import random
    while not stop_event.is_set():
        endpoint = random.choice(ENDPOINTS)
        url = f"{base_url}{endpoint}"
        t0 = time.perf_counter()
        try:
            req = request.Request(url, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
            elapsed = (time.perf_counter() - t0) * 1000  # ms
            with results_lock:
                results[endpoint].append(elapsed)
        except urllib_error.HTTPError as e:
            elapsed = (time.perf_counter() - t0) * 1000
            with results_lock:
                if e.code >= 500:
                    errors[endpoint] += 1
                else:
                    results[endpoint].append(elapsed)  # 4xx still counts as a response
        except Exception:
            with results_lock:
                errors[endpoint] += 1


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(duration: float):
    print(f"\n{'=' * 70}")
    print(f"  Load Test Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {duration:.1f}s")
    print(f"{'=' * 70}")
    print(f"  {'Endpoint':<40} {'Reqs':>5} {'Err':>4} {'p50':>7} {'p95':>7} {'p99':>7}")
    print(f"  {'-' * 66}")

    total_reqs = 0
    total_errors = 0
    all_times = []

    for ep in ENDPOINTS:
        times = results.get(ep, [])
        errs = errors.get(ep, 0)
        total_reqs += len(times)
        total_errors += errs
        all_times.extend(times)

        if times:
            p50 = statistics.median(times)
            p95 = sorted(times)[int(len(times) * 0.95)]
            p99 = sorted(times)[int(len(times) * 0.99)]
        else:
            p50 = p95 = p99 = 0.0

        print(f"  {ep:<40} {len(times):>5} {errs:>4} {p50:>6.0f}ms {p95:>6.0f}ms {p99:>6.0f}ms")

    print(f"  {'-' * 66}")
    throughput = total_reqs / duration if duration > 0 else 0
    error_rate = total_errors / (total_reqs + total_errors) * 100 if (total_reqs + total_errors) > 0 else 0
    overall_p50 = statistics.median(all_times) if all_times else 0
    overall_p95 = sorted(all_times)[int(len(all_times) * 0.95)] if all_times else 0

    print(f"\n  Total requests : {total_reqs}")
    print(f"  Total errors   : {total_errors}")
    print(f"  Error rate     : {error_rate:.1f}%")
    print(f"  Throughput     : {throughput:.1f} req/s")
    print(f"  Overall p50    : {overall_p50:.0f}ms")
    print(f"  Overall p95    : {overall_p95:.0f}ms")
    print(f"{'=' * 70}\n")

    # Pass/fail thresholds
    passed = True
    if error_rate > 5:
        print(f"  FAIL: error rate {error_rate:.1f}% exceeds 5% threshold")
        passed = False
    if overall_p95 > 2000:
        print(f"  FAIL: p95 latency {overall_p95:.0f}ms exceeds 2000ms threshold")
        passed = False
    if total_reqs == 0:
        print("  FAIL: No requests completed (is the server running?)")
        passed = False

    if passed:
        print("  PASS: All performance thresholds met.")
    return passed


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Load test for AI Risk API")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--users", type=int, default=DEFAULT_USERS)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    args = parser.parse_args()

    print(f"\nStarting load test: {args.users} concurrent users for {args.duration}s")
    print(f"Target: {args.base_url}")

    threads = [
        threading.Thread(target=worker, args=(args.base_url, i), daemon=True)
        for i in range(args.users)
    ]
    for t in threads:
        t.start()

    time.sleep(args.duration)
    stop_event.set()
    for t in threads:
        t.join(timeout=3)

    passed = print_report(args.duration)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
