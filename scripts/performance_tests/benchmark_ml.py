"""
ML engine benchmark — measures inference time for GAT forward pass,
risk propagation, and QAOA optimizer sampling.
Runs purely in-process (no HTTP); requires ml_engine dependencies.

Usage:
  python scripts/performance_tests/benchmark_ml.py
  python scripts/performance_tests/benchmark_ml.py --iterations 50 --nodes 100
"""

import argparse
import sys
import time
import statistics
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ml_engine"))


def _bench(fn, iterations: int, label: str):
    """Time `fn()` for `iterations` runs, print stats."""
    times = []
    # Warm-up
    for _ in range(3):
        try:
            fn()
        except Exception:
            pass
    # Timed
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            fn()
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
        except Exception:
            pass

    if not times:
        print(f"  {label:<50} ERROR (no successful runs)")
        return

    p50 = statistics.median(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    mx = max(times)
    print(f"  {label:<50} p50={p50:>7.1f}ms  p95={p95:>7.1f}ms  max={mx:>7.1f}ms")


def main():
    parser = argparse.ArgumentParser(description="ML engine benchmark")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--nodes", type=int, default=50,
                        help="Number of graph nodes to use in GAT benchmarks")
    args = parser.parse_args()

    print(f"\nML Engine Benchmark — {args.iterations} iterations, {args.nodes} nodes")
    print(f"{'=' * 75}")

    # ── GAT forward pass ────────────────────────────────────────────────────
    print("\n  Graph Attention Network (GAT):")
    try:
        import torch
        try:
            from graph_networks.gat_model import GAT
            model = GAT(in_channels=10, hidden_channels=32, out_channels=1, heads=4, num_layers=2)
            model.eval()
            n, e = args.nodes, args.nodes * 3
            x = torch.randn(n, 10)
            edge_index = torch.randint(0, n, (2, e))

            def gat_forward():
                with torch.no_grad():
                    return model(x, edge_index)

            _bench(gat_forward, args.iterations, f"GAT forward ({n} nodes, {e} edges)")
        except ImportError as ex:
            print(f"  Skipped GAT: {ex}")
    except ImportError:
        print("  Skipped GAT: torch not available")

    # ── RiskPropagationGAT ───────────────────────────────────────────────────
    print("\n  Risk Propagation GAT:")
    try:
        import torch
        try:
            from graph_networks.risk_propagation_gat import RiskPropagationGAT
            rp_model = RiskPropagationGAT(
                node_feature_dim=10, edge_feature_dim=5, hidden_dim=32, heads=4, num_layers=2
            )
            rp_model.eval()
            n, e = args.nodes, args.nodes * 3
            x = torch.randn(n, 10)
            edge_index = torch.randint(0, n, (2, e))

            def rp_forward():
                with torch.no_grad():
                    return rp_model(x, edge_index)

            _bench(rp_forward, args.iterations, f"RiskPropagationGAT forward ({n} nodes)")
        except ImportError as ex:
            print(f"  Skipped RiskPropagationGAT: {ex}")
    except ImportError:
        print("  Skipped RiskPropagationGAT: torch not available")

    # ── QAOA optimizer ───────────────────────────────────────────────────────
    print("\n  QAOA Optimizer:")
    try:
        from quantum_risk.qaoa_optimizer import QAOAOptimizer
        import numpy as np

        def qaoa_sample():
            opt = QAOAOptimizer(num_assets=8, num_layers=2)
            weights = np.random.dirichlet(np.ones(8))
            returns = np.random.normal(0.1, 0.2, 8)
            cov = np.eye(8) * 0.04
            return opt.optimize_portfolio(weights, returns, cov)

        _bench(qaoa_sample, min(args.iterations, 10), "QAOA portfolio optimize (8 assets)")
    except ImportError as ex:
        print(f"  Skipped QAOA: {ex}")
    except Exception as ex:
        print(f"  QAOA error: {ex}")

    # ── RiskCalculator ───────────────────────────────────────────────────────
    print("\n  Risk Calculator:")
    try:
        from risk_models.risk_calculator import RiskCalculator
        import numpy as np

        calc = RiskCalculator()

        def calc_risk():
            returns = np.random.normal(0.001, 0.02, (252, 10))
            return calc.calculate_portfolio_risk(returns)

        _bench(calc_risk, args.iterations, "RiskCalculator.calculate_portfolio_risk (252d, 10 assets)")
    except ImportError as ex:
        print(f"  Skipped RiskCalculator: {ex}")
    except Exception as ex:
        print(f"  RiskCalculator error: {ex}")

    print(f"\n{'=' * 75}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
