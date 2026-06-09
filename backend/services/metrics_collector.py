"""
Metrics Collector
Collects application metrics for monitoring
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Single request metric"""
    timestamp: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    client_id: Optional[str] = None


@dataclass
class DatabaseMetric:
    """Database query metric"""
    timestamp: str
    query_type: str
    duration_ms: float
    rows_affected: int
    success: bool


@dataclass
class MLInferenceMetric:
    """ML inference metric"""
    timestamp: str
    model_name: str
    duration_ms: float
    input_size: int
    success: bool


class MetricsCollector:
    """Collects and aggregates application metrics"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        
        # Request metrics
        self.request_metrics: deque = deque(maxlen=max_history)
        self.request_count = 0
        self.request_errors = 0
        
        # Database metrics
        self.db_metrics: deque = deque(maxlen=max_history)
        self.db_query_count = 0
        self.db_errors = 0
        
        # ML inference metrics
        self.ml_metrics: deque = deque(maxlen=max_history)
        self.ml_inference_count = 0
        self.ml_errors = 0
        
        # Endpoint statistics
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'count': 0,
                'errors': 0,
                'total_duration': 0.0,
                'durations': deque(maxlen=1000)
            }
        )
    
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_id: Optional[str] = None
    ):
        """
        Record API request metric
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            client_id: Optional client identifier
        """
        metric = RequestMetric(
            timestamp=datetime.now().isoformat(),
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_id=client_id
        )
        
        self.request_metrics.append(metric)
        self.request_count += 1
        
        if status_code >= 400:
            self.request_errors += 1
        
        # Update endpoint statistics
        endpoint_key = f"{method} {path}"
        stats = self.endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_duration'] += duration_ms
        stats['durations'].append(duration_ms)
        
        if status_code >= 400:
            stats['errors'] += 1
    
    def record_database_query(
        self,
        query_type: str,
        duration_ms: float,
        rows_affected: int = 0,
        success: bool = True
    ):
        """
        Record database query metric
        
        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
            success: Whether query succeeded
        """
        metric = DatabaseMetric(
            timestamp=datetime.now().isoformat(),
            query_type=query_type,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            success=success
        )
        
        self.db_metrics.append(metric)
        self.db_query_count += 1
        
        if not success:
            self.db_errors += 1
    
    def record_ml_inference(
        self,
        model_name: str,
        duration_ms: float,
        input_size: int = 0,
        success: bool = True
    ):
        """
        Record ML inference metric
        
        Args:
            model_name: Name of ML model
            duration_ms: Inference duration in milliseconds
            input_size: Size of input data
            success: Whether inference succeeded
        """
        metric = MLInferenceMetric(
            timestamp=datetime.now().isoformat(),
            model_name=model_name,
            duration_ms=duration_ms,
            input_size=input_size,
            success=success
        )
        
        self.ml_metrics.append(metric)
        self.ml_inference_count += 1
        
        if not success:
            self.ml_errors += 1
    
    def get_request_metrics(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Get request metrics for time period
        
        Args:
            minutes: Time period in minutes
            
        Returns:
            Request metrics summary
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.request_metrics
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'period_minutes': minutes,
                'total_requests': 0,
                'error_rate': 0.0,
                'avg_duration_ms': 0.0
            }
        
        durations = [m.duration_ms for m in recent_metrics]
        errors = sum(1 for m in recent_metrics if m.status_code >= 400)
        
        return {
            'period_minutes': minutes,
            'total_requests': len(recent_metrics),
            'successful_requests': len(recent_metrics) - errors,
            'failed_requests': errors,
            'error_rate': (errors / len(recent_metrics)) * 100,
            'avg_duration_ms': statistics.mean(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'p50_duration_ms': statistics.median(durations),
            'p95_duration_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
            'p99_duration_ms': statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else max(durations)
        }
    
    def get_database_metrics(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Get database metrics for time period
        
        Args:
            minutes: Time period in minutes
            
        Returns:
            Database metrics summary
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.db_metrics
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'period_minutes': minutes,
                'total_queries': 0,
                'error_rate': 0.0,
                'avg_duration_ms': 0.0
            }
        
        durations = [m.duration_ms for m in recent_metrics]
        errors = sum(1 for m in recent_metrics if not m.success)
        
        # Query type breakdown
        query_types = defaultdict(int)
        for m in recent_metrics:
            query_types[m.query_type] += 1
        
        return {
            'period_minutes': minutes,
            'total_queries': len(recent_metrics),
            'successful_queries': len(recent_metrics) - errors,
            'failed_queries': errors,
            'error_rate': (errors / len(recent_metrics)) * 100,
            'avg_duration_ms': statistics.mean(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'query_types': dict(query_types)
        }
    
    def get_ml_metrics(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Get ML inference metrics for time period
        
        Args:
            minutes: Time period in minutes
            
        Returns:
            ML metrics summary
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            m for m in self.ml_metrics
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'period_minutes': minutes,
                'total_inferences': 0,
                'error_rate': 0.0,
                'avg_duration_ms': 0.0
            }
        
        durations = [m.duration_ms for m in recent_metrics]
        errors = sum(1 for m in recent_metrics if not m.success)
        
        # Model breakdown
        model_stats = defaultdict(lambda: {'count': 0, 'errors': 0})
        for m in recent_metrics:
            model_stats[m.model_name]['count'] += 1
            if not m.success:
                model_stats[m.model_name]['errors'] += 1
        
        return {
            'period_minutes': minutes,
            'total_inferences': len(recent_metrics),
            'successful_inferences': len(recent_metrics) - errors,
            'failed_inferences': errors,
            'error_rate': (errors / len(recent_metrics)) * 100,
            'avg_duration_ms': statistics.mean(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'model_stats': dict(model_stats)
        }
    
    def get_endpoint_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all endpoints
        
        Returns:
            Endpoint statistics
        """
        endpoint_data = {}
        
        for endpoint, stats in self.endpoint_stats.items():
            if stats['count'] > 0:
                durations = list(stats['durations'])
                endpoint_data[endpoint] = {
                    'count': stats['count'],
                    'errors': stats['errors'],
                    'error_rate': (stats['errors'] / stats['count']) * 100,
                    'avg_duration_ms': stats['total_duration'] / stats['count'],
                    'min_duration_ms': min(durations) if durations else 0,
                    'max_duration_ms': max(durations) if durations else 0
                }
        
        return endpoint_data
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall metrics summary
        
        Returns:
            Complete metrics summary
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'requests': {
                'total': self.request_count,
                'errors': self.request_errors,
                'error_rate': (self.request_errors / self.request_count * 100) if self.request_count > 0 else 0,
                'recent': self.get_request_metrics(60)
            },
            'database': {
                'total_queries': self.db_query_count,
                'errors': self.db_errors,
                'error_rate': (self.db_errors / self.db_query_count * 100) if self.db_query_count > 0 else 0,
                'recent': self.get_database_metrics(60)
            },
            'ml_inference': {
                'total_inferences': self.ml_inference_count,
                'errors': self.ml_errors,
                'error_rate': (self.ml_errors / self.ml_inference_count * 100) if self.ml_inference_count > 0 else 0,
                'recent': self.get_ml_metrics(60)
            },
            'endpoints': self.get_endpoint_statistics()
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.request_metrics.clear()
        self.db_metrics.clear()
        self.ml_metrics.clear()
        self.endpoint_stats.clear()
        
        self.request_count = 0
        self.request_errors = 0
        self.db_query_count = 0
        self.db_errors = 0
        self.ml_inference_count = 0
        self.ml_errors = 0
        
        logger.info("Metrics reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance"""
    return metrics_collector

# Made with Bob
