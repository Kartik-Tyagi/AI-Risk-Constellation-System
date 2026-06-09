"""
Stress test — ramps up concurrent users until the API degrades or errors spike.
Reports the maximum sustainable load and the breaking point.

Usage:
  python scripts/performance_tests/stress_test.py
  python scripts/performance_tests/stress_test.py --base-url http://localhost:8000 --max-users 50 --step 5
"""

import argparse
import threading
import time
import statistics
import sys
from collections import defaultdict
from urllib import request, error as urllib_error

DEFAULT_BASE_URL = "http://localhost:8000"
PROBE_ENDPOINT = "/api/v1/risk/summary"
STEP_DURATION = 10   # seconds per load step
MAX_USERS = 50
STEP = 5


results_lock = threading.Lock()
step_results: list[float] = []
step_errors: list[int] = []
stop_event = threading.Event()


def worker(base_url: str):
    url = f"{base_url}{PROBE_ENDPOINT}"
    while not stop_event.is_set():
        t0 = time.perf_counter()
        try:
            req = request.Request(url, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                _ = resp.read()
            elapsed = (time.perf_counter() - t0) * 1000
            with results_lock:
                step_results.append(elapsed)
        except urllib_error.HTTPError as e:
            if e.code >= 500:
                with results_lock:
                    step_errors.append(1)
        except Exception:
            with results_lock:
                step_errors.append(1)


def run_step(base_url: str, num_users: int) -> dict:
    global step_results, step_errors
    stop_event.clear()
    with results_lock:
        step_results.clear()
        step_errors.clear()

    threads = [
        threading.Thread(target=worker, args=(base_url,), daemon=True)
        for _ in range(num_users)
    ]
    for t in threads:
        t.start()
    time.sleep(STEP_DURATION)
    stop_event.set()
    for t in threads:
        t.join(timeout=2)

    with results_lock:
        times = list(step_results)
        errors = len(step_errors)

    if not times:
        return {"users": num_users, "reqs": 0, "errors": errors, "p50": 0, "p95": 0, "error_rate": 100.0}

    p50 = statistics.median(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    total = len(times) + errors
    error_rate = errors / total * 100 if total > 0 else 0
    throughput = len(times) / STEP_DURATION

    return {
        "users": num_users,
        "reqs": len(times),
        "errors": errors,
        "p50": p50,
        "p95": p95,
        "error_rate": error_rate,
        "throughput": throughput,
    }


def main():
    parser = argparse.ArgumentParser(description="Stress test for AI Risk API")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--max-users", type=int, default=MAX_USERS)
    parser.add_argument("--step", type=int, default=STEP)
    args = parser.parse_args()

    print(f"\nStress test: ramping 1→{args.max_users} users (step={args.step})")
    print(f"Target: {args.base_url}{PROBE_ENDPOINT}")
    print(f"\n  {'Users':>5} {'Reqs':>6} {'Err':>4} {'p50':>7} {'p95':>7} {'RPS':>6} {'Status'}")
    print(f"  {'-' * 55}")

    breaking_point = None
    last_good = 0

    for num_users in range(args.step, args.max_users + 1, args.step):
        result = run_step(args.base_url, num_users)
        status = "OK"
        if result["error_rate"] > 5 or result["p95"] > 3000:
            status = "DEGRADED"
            if breaking_point is None:
                breaking_point = num_users
        elif result["reqs"] == 0:
            status = "FAILED"
            if breaking_point is None:
                breaking_point = num_users
        else:
            last_good = num_users

        print(f"  {result['users']:>5} {result['reqs']:>6} {result['errors']:>4} "
              f"{result['p50']:>6.0f}ms {result['p95']:>6.0f}ms "
              f"{result.get('throughput', 0):>5.1f} {status}")

        if result["error_rate"] > 30:
            print("\n  Error rate exceeded 30% — stopping ramp.")
            break

    print(f"\n  Maximum sustainable load : {last_good} concurrent users")
    if breaking_point:
        print(f"  Breaking point           : {breaking_point} concurrent users")
    else:
        print(f"  No breaking point reached within {args.max_users} users")

    sys.exit(0)


if __name__ == "__main__":
    main()
