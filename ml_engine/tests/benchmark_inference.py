"""
Benchmark script for inference pipeline performance testing.

Tests inference latency, throughput, and scalability to ensure
the system meets real-time requirements (1K-10K calculations/second).
"""

import logging
import time
import argparse
from typing import List, Dict, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.inference_engine import InferenceEngine, ModelCache
from inference.risk_calculator import RiskCalculator
from inference.cache_manager import CacheManager, CacheConfig
from inference.performance_monitor import PerformanceMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_data(num_entities: int) -> List[tuple[str, Dict[str, Any]]]:
    """
    Generate synthetic test data for benchmarking.
    
    Args:
        num_entities: Number of entities to generate
        
    Returns:
        List of (entity_id, features) tuples
    """
    entities = []
    
    for i in range(num_entities):
        entity_id = f"BENCH_ENTITY_{i:06d}"
        
        features = {
            'portfolio': {
                'total_value': np.random.uniform(100000, 10000000),
                'volatility': np.random.uniform(0.05, 0.30),
                'concentration': np.random.uniform(0.1, 0.8)
            },
            'historical': {
                'volatility_30d': np.random.uniform(0.05, 0.25),
                'trend': np.random.uniform(-1, 1)
            },
            'counterparty': {
                'num_counterparties': np.random.randint(5, 100),
                'avg_exposure': np.random.uniform(10000, 1000000)
            },
            'market': {
                'vix_level': np.random.uniform(10, 40),
                'market_stress': np.random.uniform(0, 1)
            }
        }
        
        entities.append((entity_id, features))
    
    return entities


def benchmark_single_threaded(calculator: RiskCalculator, 
                              entities: List[tuple[str, Dict[str, Any]]],
                              monitor: PerformanceMonitor) -> Dict[str, Any]:
    """
    Benchmark single-threaded inference.
    
    Args:
        calculator: Risk calculator instance
        entities: Test entities
        monitor: Performance monitor
        
    Returns:
        Benchmark results
    """
    logger.info(f"Running single-threaded benchmark with {len(entities)} entities...")
    
    start_time = time.time()
    
    for entity_id, features in entities:
        inference_start = time.time()
        
        try:
            result = calculator.calculate_risk(entity_id, features)
            latency_ms = (time.time() - inference_start) * 1000
            
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=4,  # Assuming all 4 models used
                cache_hit=False,
                success=True
            )
        except Exception as e:
            latency_ms = (time.time() - inference_start) * 1000
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=0,
                cache_hit=False,
                success=False,
                error=str(e)
            )
    
    total_time = time.time() - start_time
    throughput = len(entities) / total_time
    
    return {
        'mode': 'single_threaded',
        'total_time': total_time,
        'throughput': throughput,
        'num_entities': len(entities)
    }


def benchmark_multi_threaded(calculator: RiskCalculator,
                            entities: List[tuple[str, Dict[str, Any]]],
                            monitor: PerformanceMonitor,
                            num_workers: int = 4) -> Dict[str, Any]:
    """
    Benchmark multi-threaded inference.
    
    Args:
        calculator: Risk calculator instance
        entities: Test entities
        monitor: Performance monitor
        num_workers: Number of worker threads
        
    Returns:
        Benchmark results
    """
    logger.info(f"Running multi-threaded benchmark with {num_workers} workers and {len(entities)} entities...")
    
    start_time = time.time()
    
    def process_entity(entity_data):
        entity_id, features = entity_data
        inference_start = time.time()
        
        try:
            result = calculator.calculate_risk(entity_id, features)
            latency_ms = (time.time() - inference_start) * 1000
            
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=4,
                cache_hit=False,
                success=True
            )
            return True
        except Exception as e:
            latency_ms = (time.time() - inference_start) * 1000
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=0,
                cache_hit=False,
                success=False,
                error=str(e)
            )
            return False
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_entity, entity) for entity in entities]
        
        for future in as_completed(futures):
            future.result()
    
    total_time = time.time() - start_time
    throughput = len(entities) / total_time
    
    return {
        'mode': 'multi_threaded',
        'num_workers': num_workers,
        'total_time': total_time,
        'throughput': throughput,
        'num_entities': len(entities)
    }


def benchmark_with_cache(calculator: RiskCalculator,
                        cache_manager: CacheManager,
                        entities: List[tuple[str, Dict[str, Any]]],
                        monitor: PerformanceMonitor) -> Dict[str, Any]:
    """
    Benchmark inference with caching.
    
    Args:
        calculator: Risk calculator instance
        cache_manager: Cache manager instance
        entities: Test entities
        monitor: Performance monitor
        
    Returns:
        Benchmark results
    """
    logger.info(f"Running cache benchmark with {len(entities)} entities...")
    
    # First pass: populate cache
    logger.info("Populating cache...")
    for entity_id, features in entities:
        result = calculator.calculate_risk(entity_id, features)
        cache_manager.set(entity_id, result.to_dict(), features)
    
    # Second pass: test cache hits
    logger.info("Testing cache performance...")
    start_time = time.time()
    cache_hits = 0
    
    for entity_id, features in entities:
        inference_start = time.time()
        
        # Try cache first
        cached = cache_manager.get(entity_id, features)
        
        if cached:
            cache_hits += 1
            latency_ms = (time.time() - inference_start) * 1000
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=0,
                cache_hit=True,
                success=True
            )
        else:
            result = calculator.calculate_risk(entity_id, features)
            latency_ms = (time.time() - inference_start) * 1000
            monitor.record_inference(
                entity_id=entity_id,
                latency_ms=latency_ms,
                model_count=4,
                cache_hit=False,
                success=True
            )
    
    total_time = time.time() - start_time
    throughput = len(entities) / total_time
    hit_rate = cache_hits / len(entities)
    
    return {
        'mode': 'with_cache',
        'total_time': total_time,
        'throughput': throughput,
        'num_entities': len(entities),
        'cache_hits': cache_hits,
        'hit_rate': hit_rate
    }


def run_scalability_test(calculator: RiskCalculator,
                        monitor: PerformanceMonitor,
                        sizes: List[int] = [100, 500, 1000, 5000, 10000]) -> List[Dict[str, Any]]:
    """
    Test scalability with increasing load.
    
    Args:
        calculator: Risk calculator instance
        monitor: Performance monitor
        sizes: List of entity counts to test
        
    Returns:
        List of scalability results
    """
    logger.info("Running scalability test...")
    results = []
    
    for size in sizes:
        logger.info(f"Testing with {size} entities...")
        monitor.reset()
        
        entities = generate_test_data(size)
        
        start_time = time.time()
        for entity_id, features in entities:
            calculator.calculate_risk(entity_id, features)
        total_time = time.time() - start_time
        
        throughput = size / total_time
        latency_stats = monitor.get_latency_stats()
        
        results.append({
            'num_entities': size,
            'total_time': total_time,
            'throughput': throughput,
            'mean_latency': latency_stats['mean'],
            'p95_latency': latency_stats['p95'],
            'p99_latency': latency_stats['p99']
        })
        
        logger.info(f"  Throughput: {throughput:.2f} req/s")
        logger.info(f"  P95 Latency: {latency_stats['p95']:.2f} ms")
    
    return results


def print_benchmark_results(results: List[Dict[str, Any]]):
    """
    Print formatted benchmark results.
    
    Args:
        results: List of benchmark results
    """
    print("\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\nMode: {result['mode']}")
        print(f"  Entities:   {result['num_entities']}")
        print(f"  Total Time: {result['total_time']:.2f} seconds")
        print(f"  Throughput: {result['throughput']:.2f} requests/second")
        
        if 'num_workers' in result:
            print(f"  Workers:    {result['num_workers']}")
        
        if 'hit_rate' in result:
            print(f"  Cache Hits: {result['cache_hits']}")
            print(f"  Hit Rate:   {result['hit_rate']*100:.1f}%")
    
    print("="*80 + "\n")


def print_scalability_results(results: List[Dict[str, Any]]):
    """
    Print formatted scalability results.
    
    Args:
        results: List of scalability results
    """
    print("\n" + "="*80)
    print("SCALABILITY TEST RESULTS")
    print("="*80)
    print(f"\n{'Entities':<12} {'Time (s)':<12} {'Throughput':<15} {'P95 (ms)':<12} {'P99 (ms)':<12}")
    print("-"*80)
    
    for result in results:
        print(f"{result['num_entities']:<12} "
              f"{result['total_time']:<12.2f} "
              f"{result['throughput']:<15.2f} "
              f"{result['p95_latency']:<12.2f} "
              f"{result['p99_latency']:<12.2f}")
    
    print("="*80 + "\n")


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description='Benchmark inference pipeline')
    parser.add_argument('--entities', type=int, default=1000,
                       help='Number of entities to test')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of worker threads')
    parser.add_argument('--cache', action='store_true',
                       help='Enable cache benchmarking')
    parser.add_argument('--scalability', action='store_true',
                       help='Run scalability test')
    
    args = parser.parse_args()
    
    # Initialize components
    logger.info("Initializing inference pipeline...")
    engine = InferenceEngine(batch_size=32)
    calculator = RiskCalculator(engine, max_workers=args.workers)
    monitor = PerformanceMonitor(window_size=10000)
    
    # Generate test data
    entities = generate_test_data(args.entities)
    
    benchmark_results = []
    
    # Run single-threaded benchmark
    monitor.reset()
    result = benchmark_single_threaded(calculator, entities, monitor)
    benchmark_results.append(result)
    monitor.print_summary()
    
    # Run multi-threaded benchmark
    monitor.reset()
    result = benchmark_multi_threaded(calculator, entities, monitor, args.workers)
    benchmark_results.append(result)
    monitor.print_summary()
    
    # Run cache benchmark if enabled
    if args.cache:
        cache_config = CacheConfig(host='localhost', port=6379)
        cache_manager = CacheManager(cache_config)
        
        if cache_manager.enabled:
            monitor.reset()
            result = benchmark_with_cache(calculator, cache_manager, entities, monitor)
            benchmark_results.append(result)
            monitor.print_summary()
            cache_manager.close()
        else:
            logger.warning("Cache not available, skipping cache benchmark")
    
    # Print benchmark results
    print_benchmark_results(benchmark_results)
    
    # Run scalability test if enabled
    if args.scalability:
        monitor.reset()
        scalability_results = run_scalability_test(calculator, monitor)
        print_scalability_results(scalability_results)
    
    # Check performance targets
    print("\nPerformance Target Check:")
    targets = monitor.check_performance_targets(
        target_latency_ms=100.0,
        target_throughput=1000.0,
        target_success_rate=0.99
    )
    
    target_values = targets['targets']  # type: ignore
    actual_values = targets['actual']  # type: ignore
    
    print(f"  Target Throughput: {target_values['throughput_rps']:.0f} req/s")
    print(f"  Actual Throughput: {actual_values['throughput_rps']:.2f} req/s")
    print(f"  Target Met: {'✓' if targets['throughput_target_met'] else '✗'}")
    print()
    print(f"  Target P95 Latency: {target_values['latency_ms']:.0f} ms")
    print(f"  Actual P95 Latency: {actual_values['latency_p95_ms']:.2f} ms")
    print(f"  Target Met: {'✓' if targets['latency_target_met'] else '✗'}")
    print()
    print(f"  All Targets Met: {'✓' if targets['all_targets_met'] else '✗'}")


if __name__ == '__main__':
    main()

# Made with Bob
