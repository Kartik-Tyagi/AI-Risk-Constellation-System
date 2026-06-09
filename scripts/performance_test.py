"""
Performance Testing Suite
Load testing, stress testing, performance benchmarks, and bottleneck identification
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available - some tests will be limited")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests not available - API tests disabled")


class PerformanceMetrics:
    """
    Container for performance metrics
    """
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0
    
    def add_response_time(self, time_ms: float):
        """Add response time measurement"""
        self.response_times.append(time_ms)
    
    def add_error(self, error: str):
        """Add error"""
        self.errors.append(error)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics"""
        if not self.response_times:
            return {
                'count': 0,
                'errors': len(self.errors),
                'error_rate': 1.0
            }
        
        sorted_times = sorted(self.response_times)
        count = len(sorted_times)
        
        return {
            'count': count,
            'mean': statistics.mean(sorted_times),
            'median': statistics.median(sorted_times),
            'min': min(sorted_times),
            'max': max(sorted_times),
            'stdev': statistics.stdev(sorted_times) if count > 1 else 0,
            'p50': sorted_times[int(count * 0.50)],
            'p90': sorted_times[int(count * 0.90)],
            'p95': sorted_times[int(count * 0.95)],
            'p99': sorted_times[int(count * 0.99)] if count >= 100 else sorted_times[-1],
            'errors': len(self.errors),
            'error_rate': len(self.errors) / (count + len(self.errors)),
            'throughput': count / (self.end_time - self.start_time) if self.end_time else 0
        }


class LoadTester:
    """
    Load testing for API endpoints
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.metrics = PerformanceMetrics()
    
    def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        num_requests: int = 100,
        concurrent: int = 10
    ) -> Dict[str, Any]:
        """
        Test API endpoint with load
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request data
            num_requests: Total number of requests
            concurrent: Number of concurrent requests
        
        Returns:
            Performance metrics
        """
        if not REQUESTS_AVAILABLE:
            print("Requests library not available")
            return {}
        
        url = f"{self.base_url}{endpoint}"
        self.metrics = PerformanceMetrics()
        self.metrics.start_time = time.time()
        
        def make_request():
            try:
                start = time.time()
                
                if method == "GET":
                    response = requests.get(url, timeout=30)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, json=data, timeout=30)
                else:
                    response = requests.delete(url, timeout=30)
                
                elapsed = (time.time() - start) * 1000  # Convert to ms
                
                if response.status_code >= 400:
                    self.metrics.add_error(f"HTTP {response.status_code}")
                else:
                    self.metrics.add_response_time(elapsed)
                    
            except Exception as e:
                self.metrics.add_error(str(e))
        
        # Execute requests with thread pool
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in futures:
                future.result()
        
        self.metrics.end_time = time.time()
        
        return self.metrics.get_statistics()
    
    def stress_test(
        self,
        endpoint: str,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10,
        max_concurrent: int = 100
    ) -> Dict[str, Any]:
        """
        Stress test endpoint with increasing load
        
        Args:
            endpoint: API endpoint path
            duration_seconds: Test duration
            ramp_up_seconds: Ramp-up period
            max_concurrent: Maximum concurrent requests
        
        Returns:
            Performance metrics over time
        """
        if not REQUESTS_AVAILABLE:
            print("Requests library not available")
            return {}
        
        url = f"{self.base_url}{endpoint}"
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            elapsed = time.time() - start_time
            
            # Calculate current concurrency (ramp up)
            if elapsed < ramp_up_seconds:
                concurrent = int((elapsed / ramp_up_seconds) * max_concurrent)
            else:
                concurrent = max_concurrent
            
            concurrent = max(1, concurrent)
            
            # Run batch of requests
            metrics = PerformanceMetrics()
            metrics.start_time = time.time()
            
            def make_request():
                try:
                    start = time.time()
                    response = requests.get(url, timeout=30)
                    elapsed_ms = (time.time() - start) * 1000
                    
                    if response.status_code >= 400:
                        metrics.add_error(f"HTTP {response.status_code}")
                    else:
                        metrics.add_response_time(elapsed_ms)
                except Exception as e:
                    metrics.add_error(str(e))
            
            with ThreadPoolExecutor(max_workers=concurrent) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent)]
                for future in futures:
                    future.result()
            
            metrics.end_time = time.time()
            stats = metrics.get_statistics()
            stats['timestamp'] = elapsed
            stats['concurrent'] = concurrent
            results.append(stats)
            
            time.sleep(1)  # 1 second between batches
        
        return {
            'duration': duration_seconds,
            'max_concurrent': max_concurrent,
            'samples': results
        }


class MLBenchmark:
    """
    ML inference performance benchmarks
    """
    
    def __init__(self):
        self.results = {}
    
    def benchmark_inference(
        self,
        model_func: Callable,
        input_data: Any,
        num_iterations: int = 1000,
        warmup: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark ML inference performance
        
        Args:
            model_func: Model inference function
            input_data: Input data
            num_iterations: Number of iterations
            warmup: Warmup iterations
        
        Returns:
            Performance metrics
        """
        # Warmup
        for _ in range(warmup):
            model_func(input_data)
        
        # Benchmark
        times = []
        for _ in range(num_iterations):
            start = time.time()
            model_func(input_data)
            times.append((time.time() - start) * 1000)  # ms
        
        return {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'throughput': 1000 / statistics.mean(times)  # inferences per second
        }
    
    def benchmark_batch_inference(
        self,
        model_func: Callable,
        batch_sizes: List[int],
        input_shape: tuple,
        num_iterations: int = 100
    ) -> Dict[int, Dict[str, float]]:
        """
        Benchmark batch inference with different batch sizes
        
        Args:
            model_func: Model inference function
            batch_sizes: List of batch sizes to test
            input_shape: Shape of single input
            num_iterations: Number of iterations per batch size
        
        Returns:
            Performance metrics for each batch size
        """
        if not NUMPY_AVAILABLE:
            print("NumPy not available")
            return {}
        
        results = {}
        
        for batch_size in batch_sizes:
            # Create batch input
            batch_input = np.random.randn(batch_size, *input_shape).astype(np.float32)
            
            # Benchmark
            metrics = self.benchmark_inference(model_func, batch_input, num_iterations)
            metrics['batch_size'] = batch_size
            metrics['throughput_per_sample'] = metrics['throughput'] * batch_size
            
            results[batch_size] = metrics
        
        return results


class DatabaseBenchmark:
    """
    Database query performance benchmarks
    """
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.results = {}
    
    def benchmark_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        num_iterations: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark database query
        
        Args:
            query: SQL query
            params: Query parameters
            num_iterations: Number of iterations
        
        Returns:
            Performance metrics
        """
        times = []
        
        for _ in range(num_iterations):
            start = time.time()
            
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                cursor.fetchall()
                cursor.close()
                
                times.append((time.time() - start) * 1000)  # ms
            except Exception as e:
                print(f"Query error: {e}")
        
        if not times:
            return {}
        
        return {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_index_usage(
        self,
        queries: List[tuple]
    ) -> Dict[str, Any]:
        """
        Benchmark queries with and without indexes
        
        Args:
            queries: List of (query, params) tuples
        
        Returns:
            Comparison results
        """
        results = []
        
        for query, params in queries:
            # Get execution plan
            explain_query = f"EXPLAIN ANALYZE {query}"
            
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(explain_query, params)
                else:
                    cursor.execute(explain_query)
                
                plan = cursor.fetchall()
                cursor.close()
                
                results.append({
                    'query': query[:100],  # Truncate for readability
                    'plan': str(plan)
                })
            except Exception as e:
                print(f"Explain error: {e}")
        
        return {'queries': results}


class BottleneckIdentifier:
    """
    Identify performance bottlenecks
    """
    
    def __init__(self):
        self.bottlenecks = []
    
    def analyze_metrics(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze metrics to identify bottlenecks
        
        Args:
            metrics: Performance metrics
        
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        # Check response time
        if 'mean' in metrics and metrics['mean'] > 1000:  # > 1 second
            bottlenecks.append({
                'type': 'slow_response',
                'severity': 'high',
                'metric': 'mean_response_time',
                'value': metrics['mean'],
                'threshold': 1000,
                'recommendation': 'Optimize query or add caching'
            })
        
        # Check error rate
        if 'error_rate' in metrics and metrics['error_rate'] > 0.01:  # > 1%
            bottlenecks.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'metric': 'error_rate',
                'value': metrics['error_rate'],
                'threshold': 0.01,
                'recommendation': 'Investigate errors and add error handling'
            })
        
        # Check p99 latency
        if 'p99' in metrics and metrics['p99'] > 5000:  # > 5 seconds
            bottlenecks.append({
                'type': 'high_tail_latency',
                'severity': 'medium',
                'metric': 'p99_latency',
                'value': metrics['p99'],
                'threshold': 5000,
                'recommendation': 'Optimize slow queries or add timeouts'
            })
        
        # Check throughput
        if 'throughput' in metrics and metrics['throughput'] < 10:  # < 10 req/s
            bottlenecks.append({
                'type': 'low_throughput',
                'severity': 'medium',
                'metric': 'throughput',
                'value': metrics['throughput'],
                'threshold': 10,
                'recommendation': 'Scale horizontally or optimize processing'
            })
        
        return bottlenecks
    
    def generate_report(self, all_metrics: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate bottleneck report
        
        Args:
            all_metrics: Dictionary of all performance metrics
        
        Returns:
            Report string
        """
        report = ["=" * 80]
        report.append("PERFORMANCE BOTTLENECK REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")
        
        all_bottlenecks = []
        
        for test_name, metrics in all_metrics.items():
            bottlenecks = self.analyze_metrics(metrics)
            
            if bottlenecks:
                report.append(f"\n{test_name}:")
                report.append("-" * 40)
                
                for bottleneck in bottlenecks:
                    all_bottlenecks.append(bottleneck)
                    report.append(f"  [{bottleneck['severity'].upper()}] {bottleneck['type']}")
                    report.append(f"    Metric: {bottleneck['metric']}")
                    report.append(f"    Value: {bottleneck['value']:.2f}")
                    report.append(f"    Threshold: {bottleneck['threshold']}")
                    report.append(f"    Recommendation: {bottleneck['recommendation']}")
                    report.append("")
        
        # Summary
        report.append("\n" + "=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        report.append(f"Total bottlenecks found: {len(all_bottlenecks)}")
        
        severity_counts = {}
        for b in all_bottlenecks:
            severity_counts[b['severity']] = severity_counts.get(b['severity'], 0) + 1
        
        for severity, count in severity_counts.items():
            report.append(f"  {severity.upper()}: {count}")
        
        return "\n".join(report)


def run_all_tests():
    """
    Run all performance tests
    """
    print("=" * 80)
    print("PERFORMANCE TEST SUITE")
    print("=" * 80)
    print()
    
    results = {}
    
    # API Load Tests
    if REQUESTS_AVAILABLE:
        print("Running API load tests...")
        tester = LoadTester()
        
        # Test health endpoint
        print("  - Testing /health endpoint...")
        results['health_endpoint'] = tester.test_endpoint(
            "/health",
            num_requests=100,
            concurrent=10
        )
        print(f"    Mean: {results['health_endpoint'].get('mean', 0):.2f}ms")
        print(f"    P95: {results['health_endpoint'].get('p95', 0):.2f}ms")
        print()
    
    # ML Benchmarks
    print("Running ML inference benchmarks...")
    ml_bench = MLBenchmark()
    
    # Simple inference test
    def dummy_model(x):
        if NUMPY_AVAILABLE:
            return np.sum(x)
        return sum(x) if isinstance(x, list) else x
    
    test_input = np.random.randn(10) if NUMPY_AVAILABLE else [1.0] * 10
    results['ml_inference'] = ml_bench.benchmark_inference(
        dummy_model,
        test_input,
        num_iterations=1000
    )
    print(f"  Mean inference time: {results['ml_inference']['mean_time']:.2f}ms")
    print(f"  Throughput: {results['ml_inference']['throughput']:.2f} inferences/sec")
    print()
    
    # Bottleneck Analysis
    print("Analyzing bottlenecks...")
    identifier = BottleneckIdentifier()
    report = identifier.generate_report(results)
    print(report)
    print()
    
    # Save results
    output_file = "performance_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)
    
    print(f"Results saved to {output_file}")
    print()
    print("=" * 80)
    print("PERFORMANCE TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

# Made with Bob
