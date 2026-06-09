"""
Performance Monitor for Inference Pipeline.

This module tracks inference latency, throughput, and other performance metrics
to ensure the system meets real-time requirements.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import statistics
import threading

logger = logging.getLogger(__name__)


@dataclass
class InferenceMetrics:
    """Metrics for a single inference operation."""
    entity_id: str
    timestamp: float
    latency_ms: float
    model_count: int
    cache_hit: bool
    success: bool
    error: Optional[str] = None


class PerformanceMonitor:
    """
    Monitor and track inference performance metrics.
    
    Tracks latency, throughput, cache hit rates, and error rates
    with configurable time windows for statistics.
    """
    
    def __init__(self, window_size: int = 1000, time_window_seconds: int = 60):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of recent metrics to keep
            time_window_seconds: Time window for rate calculations
        """
        self.window_size = window_size
        self.time_window_seconds = time_window_seconds
        
        # Metrics storage
        self.metrics: deque[InferenceMetrics] = deque(maxlen=window_size)
        self.lock = threading.Lock()
        
        # Counters
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0
        
        # Timing
        self.start_time = time.time()
        
        logger.info(f"Initialized PerformanceMonitor (window_size={window_size}, time_window={time_window_seconds}s)")
    
    def record_inference(self, entity_id: str, latency_ms: float,
                        model_count: int, cache_hit: bool,
                        success: bool, error: Optional[str] = None):
        """
        Record an inference operation.
        
        Args:
            entity_id: Entity identifier
            latency_ms: Inference latency in milliseconds
            model_count: Number of models used
            cache_hit: Whether result was from cache
            success: Whether inference succeeded
            error: Error message if failed
        """
        with self.lock:
            metric = InferenceMetrics(
                entity_id=entity_id,
                timestamp=time.time(),
                latency_ms=latency_ms,
                model_count=model_count,
                cache_hit=cache_hit,
                success=success,
                error=error
            )
            
            self.metrics.append(metric)
            
            # Update counters
            self.total_requests += 1
            if success:
                self.total_successes += 1
            else:
                self.total_failures += 1
            
            if cache_hit:
                self.total_cache_hits += 1
            else:
                self.total_cache_misses += 1
    
    def get_latency_stats(self) -> Dict[str, float]:
        """
        Get latency statistics.
        
        Returns:
            Dictionary of latency statistics
        """
        with self.lock:
            if not self.metrics:
                return {
                    'mean': 0.0,
                    'median': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'std': 0.0
                }
            
            latencies = [m.latency_ms for m in self.metrics if m.success]
            
            if not latencies:
                return {
                    'mean': 0.0,
                    'median': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'std': 0.0
                }
            
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            
            return {
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'p50': sorted_latencies[int(n * 0.50)],
                'p95': sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0],
                'p99': sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0],
                'min': min(latencies),
                'max': max(latencies),
                'std': statistics.stdev(latencies) if len(latencies) > 1 else 0.0
            }
    
    def get_throughput(self) -> Dict[str, float]:
        """
        Get throughput statistics.
        
        Returns:
            Dictionary of throughput statistics
        """
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            
            # Calculate requests in time window
            cutoff_time = current_time - self.time_window_seconds
            recent_requests = sum(1 for m in self.metrics if m.timestamp >= cutoff_time)
            
            return {
                'total_requests': self.total_requests,
                'requests_per_second_overall': self.total_requests / elapsed_time if elapsed_time > 0 else 0.0,
                'requests_per_second_recent': recent_requests / self.time_window_seconds,
                'elapsed_time_seconds': elapsed_time
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        with self.lock:
            total_cache_requests = self.total_cache_hits + self.total_cache_misses
            hit_rate = self.total_cache_hits / total_cache_requests if total_cache_requests > 0 else 0.0
            
            return {
                'total_hits': self.total_cache_hits,
                'total_misses': self.total_cache_misses,
                'hit_rate': hit_rate,
                'miss_rate': 1.0 - hit_rate
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary of error statistics
        """
        with self.lock:
            error_rate = self.total_failures / self.total_requests if self.total_requests > 0 else 0.0
            success_rate = self.total_successes / self.total_requests if self.total_requests > 0 else 0.0
            
            # Count error types
            error_types: Dict[str, int] = {}
            for m in self.metrics:
                if not m.success and m.error:
                    error_types[m.error] = error_types.get(m.error, 0) + 1
            
            return {
                'total_successes': self.total_successes,
                'total_failures': self.total_failures,
                'success_rate': success_rate,
                'error_rate': error_rate,
                'error_types': error_types
            }
    
    def get_model_usage_stats(self) -> Dict[str, Any]:
        """
        Get model usage statistics.
        
        Returns:
            Dictionary of model usage statistics
        """
        with self.lock:
            if not self.metrics:
                return {
                    'avg_models_per_request': 0.0,
                    'model_count_distribution': {}
                }
            
            model_counts = [m.model_count for m in self.metrics]
            
            # Count distribution
            distribution: Dict[int, int] = {}
            for count in model_counts:
                distribution[count] = distribution.get(count, 0) + 1
            
            return {
                'avg_models_per_request': statistics.mean(model_counts),
                'model_count_distribution': distribution
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary of all performance metrics
        """
        return {
            'latency': self.get_latency_stats(),
            'throughput': self.get_throughput(),
            'cache': self.get_cache_stats(),
            'errors': self.get_error_stats(),
            'models': self.get_model_usage_stats(),
            'window_size': self.window_size,
            'metrics_count': len(self.metrics)
        }
    
    def print_summary(self):
        """Print performance summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        print("\nLatency Statistics:")
        latency = summary['latency']
        print(f"  Mean:   {latency['mean']:.2f} ms")
        print(f"  Median: {latency['median']:.2f} ms")
        print(f"  P95:    {latency['p95']:.2f} ms")
        print(f"  P99:    {latency['p99']:.2f} ms")
        print(f"  Min:    {latency['min']:.2f} ms")
        print(f"  Max:    {latency['max']:.2f} ms")
        
        print("\nThroughput:")
        throughput = summary['throughput']
        print(f"  Total Requests: {throughput['total_requests']}")
        print(f"  Overall:        {throughput['requests_per_second_overall']:.2f} req/s")
        print(f"  Recent:         {throughput['requests_per_second_recent']:.2f} req/s")
        
        print("\nCache Performance:")
        cache = summary['cache']
        print(f"  Hit Rate:  {cache['hit_rate']*100:.1f}%")
        print(f"  Hits:      {cache['total_hits']}")
        print(f"  Misses:    {cache['total_misses']}")
        
        print("\nError Statistics:")
        errors = summary['errors']
        print(f"  Success Rate: {errors['success_rate']*100:.1f}%")
        print(f"  Error Rate:   {errors['error_rate']*100:.1f}%")
        print(f"  Successes:    {errors['total_successes']}")
        print(f"  Failures:     {errors['total_failures']}")
        
        print("\nModel Usage:")
        models = summary['models']
        print(f"  Avg Models/Request: {models['avg_models_per_request']:.2f}")
        
        print("="*60 + "\n")
    
    def check_performance_targets(self, target_latency_ms: float = 100.0,
                                 target_throughput: float = 1000.0,
                                 target_success_rate: float = 0.99) -> Dict[str, Any]:
        """
        Check if performance meets targets.
        
        Args:
            target_latency_ms: Target P95 latency in milliseconds
            target_throughput: Target throughput in requests/second
            target_success_rate: Target success rate (0-1)
            
        Returns:
            Dictionary of target checks with nested target and actual values
        """
        summary = self.get_summary()
        
        latency_ok = summary['latency']['p95'] <= target_latency_ms
        throughput_ok = summary['throughput']['requests_per_second_recent'] >= target_throughput
        success_ok = summary['errors']['success_rate'] >= target_success_rate
        
        return {
            'latency_target_met': latency_ok,
            'throughput_target_met': throughput_ok,
            'success_rate_target_met': success_ok,
            'all_targets_met': latency_ok and throughput_ok and success_ok,
            'targets': {
                'latency_ms': target_latency_ms,
                'throughput_rps': target_throughput,
                'success_rate': target_success_rate
            },
            'actual': {
                'latency_p95_ms': summary['latency']['p95'],
                'throughput_rps': summary['throughput']['requests_per_second_recent'],
                'success_rate': summary['errors']['success_rate']
            }
        }
    
    def reset(self):
        """Reset all metrics and counters."""
        with self.lock:
            self.metrics.clear()
            self.total_requests = 0
            self.total_successes = 0
            self.total_failures = 0
            self.total_cache_hits = 0
            self.total_cache_misses = 0
            self.start_time = time.time()
            logger.info("Reset performance metrics")
    
    def export_metrics(self) -> List[Dict[str, Any]]:
        """
        Export all metrics as list of dictionaries.
        
        Returns:
            List of metric dictionaries
        """
        with self.lock:
            return [
                {
                    'entity_id': m.entity_id,
                    'timestamp': m.timestamp,
                    'latency_ms': m.latency_ms,
                    'model_count': m.model_count,
                    'cache_hit': m.cache_hit,
                    'success': m.success,
                    'error': m.error
                }
                for m in self.metrics
            ]


if __name__ == '__main__':
    # Example usage
    print("Performance Monitor Module")
    
    # Create monitor
    monitor = PerformanceMonitor(window_size=100)
    
    # Simulate some inferences
    import random
    
    for i in range(50):
        entity_id = f"ENTITY_{i:03d}"
        latency = random.uniform(10, 150)
        model_count = random.randint(1, 4)
        cache_hit = random.random() < 0.3
        success = random.random() < 0.95
        
        monitor.record_inference(
            entity_id=entity_id,
            latency_ms=latency,
            model_count=model_count,
            cache_hit=cache_hit,
            success=success,
            error="Test error" if not success else None
        )
        
        time.sleep(0.01)  # Simulate time between requests
    
    # Print summary
    monitor.print_summary()
    
    # Check targets
    targets = monitor.check_performance_targets(
        target_latency_ms=100.0,
        target_throughput=10.0,
        target_success_rate=0.90
    )
    
    print("\nTarget Check:")
    print(f"All targets met: {targets['all_targets_met']}")
    print(f"Latency target met: {targets['latency_target_met']}")
    print(f"Throughput target met: {targets['throughput_target_met']}")
    print(f"Success rate target met: {targets['success_rate_target_met']}")

# Made with Bob
