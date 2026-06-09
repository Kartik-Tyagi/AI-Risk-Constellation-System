"""
Unit tests for inference pipeline components.

Tests inference engine, risk calculator, cache manager, and performance monitor.
"""

import unittest
import time
import tempfile
from pathlib import Path
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.inference_engine import InferenceEngine, ModelCache, ModelMetadata
from inference.risk_calculator import RiskCalculator, RiskAssessmentResult
from inference.cache_manager import CacheManager, CacheConfig
from inference.performance_monitor import PerformanceMonitor, InferenceMetrics


class TestModelCache(unittest.TestCase):
    """Test ModelCache functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = ModelCache(max_size=3, device='cpu')
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertEqual(self.cache.max_size, 3)
        self.assertEqual(self.cache.device, 'cpu')
        self.assertEqual(len(self.cache.cache), 0)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 0)
        self.assertEqual(stats['max_size'], 3)
        self.assertEqual(stats['device'], 'cpu')
    
    def test_cache_clear(self):
        """Test cache clearing."""
        self.cache.clear()
        self.assertEqual(len(self.cache.cache), 0)


class TestInferenceEngine(unittest.TestCase):
    """Test InferenceEngine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = InferenceEngine(batch_size=32, device='cpu')
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        self.assertEqual(self.engine.device, 'cpu')
        self.assertEqual(self.engine.batch_size, 32)
        self.assertIsNotNone(self.engine.model_cache)
    
    def test_get_stats(self):
        """Test engine statistics."""
        stats = self.engine.get_stats()
        self.assertIn('device', stats)
        self.assertIn('batch_size', stats)
        self.assertIn('cache', stats)
        self.assertEqual(stats['device'], 'cpu')
        self.assertEqual(stats['batch_size'], 32)


class TestRiskAssessmentResult(unittest.TestCase):
    """Test RiskAssessmentResult dataclass."""
    
    def test_result_creation(self):
        """Test result creation."""
        result = RiskAssessmentResult(
            entity_id='TEST_001',
            timestamp=time.time(),
            overall_risk_score=0.75
        )
        
        self.assertEqual(result.entity_id, 'TEST_001')
        self.assertEqual(result.overall_risk_score, 0.75)
        self.assertIsNone(result.quantum_optimization_score)
    
    def test_result_to_dict(self):
        """Test result conversion to dictionary."""
        result = RiskAssessmentResult(
            entity_id='TEST_001',
            timestamp=time.time(),
            overall_risk_score=0.75,
            quantum_optimization_score=0.8,
            confidence=0.9
        )
        
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['entity_id'], 'TEST_001')
        self.assertEqual(result_dict['overall_risk_score'], 0.75)
        self.assertEqual(result_dict['quantum_optimization_score'], 0.8)
        self.assertEqual(result_dict['confidence'], 0.9)
    
    def test_result_with_dna(self):
        """Test result with Risk DNA."""
        dna_vector = np.random.randn(256)
        
        result = RiskAssessmentResult(
            entity_id='TEST_001',
            timestamp=time.time(),
            overall_risk_score=0.75,
            risk_dna_vector=dna_vector,
            similar_entities=['TEST_002', 'TEST_003']
        )
        
        self.assertIsNotNone(result.risk_dna_vector)
        self.assertEqual(len(result.similar_entities), 2)
        
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict['risk_dna_vector'], list)
        self.assertEqual(len(result_dict['risk_dna_vector']), 256)


class TestRiskCalculator(unittest.TestCase):
    """Test RiskCalculator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        engine = InferenceEngine(device='cpu')
        self.calculator = RiskCalculator(engine)
    
    def test_calculator_initialization(self):
        """Test calculator initialization."""
        self.assertIsNotNone(self.calculator.engine)
        self.assertEqual(self.calculator.max_workers, 4)
        self.assertIn('quantum', self.calculator.weights)
        self.assertIn('graph', self.calculator.weights)
        self.assertIn('temporal', self.calculator.weights)
        self.assertIn('cascade', self.calculator.weights)
    
    def test_weight_normalization(self):
        """Test weight normalization."""
        total_weight = sum(self.calculator.weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=6)
    
    def test_calculate_risk_basic(self):
        """Test basic risk calculation."""
        features = {
            'portfolio': {'total_value': 1000000, 'volatility': 0.15},
            'historical': {'volatility_30d': 0.12},
            'counterparty': {'num_counterparties': 25}
        }
        
        result = self.calculator.calculate_risk('TEST_001', features)
        
        self.assertIsInstance(result, RiskAssessmentResult)
        self.assertEqual(result.entity_id, 'TEST_001')
        self.assertGreaterEqual(result.overall_risk_score, 0.0)
        self.assertLessEqual(result.overall_risk_score, 1.0)
        self.assertGreater(result.computation_time_ms, 0)
    
    def test_calculate_risk_with_all_features(self):
        """Test risk calculation with all features."""
        features = {
            'portfolio': {'total_value': 1000000, 'volatility': 0.15, 'concentration': 0.5},
            'historical': {'volatility_30d': 0.12, 'trend': 0.5},
            'counterparty': {'num_counterparties': 25, 'avg_exposure': 50000},
            'market': {'vix_level': 20, 'market_stress': 0.3}
        }
        
        graph_data = {
            'num_connections': 30,
            'avg_counterparty_risk': 0.4,
            'centrality': 0.6
        }
        
        temporal_data = {
            'historical_volatility': 0.15,
            'trend': 0.3
        }
        
        result = self.calculator.calculate_risk('TEST_001', features, graph_data, temporal_data)
        
        self.assertIsNotNone(result.quantum_optimization_score)
        self.assertIsNotNone(result.graph_propagation_score)
        self.assertIsNotNone(result.temporal_risk_score)
        self.assertIsNotNone(result.cascade_probability)
        self.assertIsNotNone(result.risk_dna_vector)
        if result.risk_dna_vector is not None:
            self.assertEqual(len(result.risk_dna_vector), 256)
    
    def test_risk_dna_generation(self):
        """Test Risk DNA generation."""
        features = {
            'portfolio': {'total_value': 1000000},
            'historical': {'volatility_30d': 0.12},
            'counterparty': {'num_counterparties': 25}
        }
        
        dna = self.calculator._generate_risk_dna('TEST_001', features)
        
        self.assertEqual(len(dna), 256)
        self.assertIsInstance(dna, np.ndarray)
        # Check normalization
        norm = np.linalg.norm(dna)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_batch_risk_calculation(self):
        """Test batch risk calculation."""
        entities = [
            ('TEST_001', {'portfolio': {'total_value': 1000000}}),
            ('TEST_002', {'portfolio': {'total_value': 2000000}}),
            ('TEST_003', {'portfolio': {'total_value': 3000000}})
        ]
        
        results = self.calculator.calculate_batch_risk(entities)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, RiskAssessmentResult)
            self.assertGreaterEqual(result.overall_risk_score, 0.0)
            self.assertLessEqual(result.overall_risk_score, 1.0)


class TestCacheManager(unittest.TestCase):
    """Test CacheManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        config = CacheConfig(host='localhost', port=6379, db=15)  # Use test DB
        self.cache = CacheManager(config)
        
        if self.cache.enabled:
            self.cache.invalidate_all()
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertIsNotNone(self.cache.config)
        self.assertEqual(self.cache.config.host, 'localhost')
        self.assertEqual(self.cache.config.port, 6379)
    
    def test_key_generation(self):
        """Test cache key generation."""
        key1 = self.cache._generate_key('TEST_001')
        key2 = self.cache._generate_key('TEST_001', 'hash123')
        
        self.assertIn('TEST_001', key1)
        self.assertIn('TEST_001', key2)
        self.assertIn('hash123', key2)
    
    def test_feature_hashing(self):
        """Test feature hashing."""
        features1 = {'a': 1, 'b': 2}
        features2 = {'b': 2, 'a': 1}  # Same features, different order
        
        hash1 = self.cache._hash_features(features1)
        hash2 = self.cache._hash_features(features2)
        
        self.assertEqual(hash1, hash2)  # Should be same due to sorting
    
    @unittest.skipIf(not CacheManager(CacheConfig()).enabled, "Redis not available")
    def test_set_and_get(self):
        """Test cache set and get operations."""
        result = {
            'entity_id': 'TEST_001',
            'risk_score': 0.75,
            'timestamp': time.time()
        }
        
        self.cache.set('TEST_001', result, ttl=60)
        cached = self.cache.get('TEST_001')
        
        self.assertIsNotNone(cached)
        if cached is not None:
            self.assertEqual(cached['entity_id'], 'TEST_001')
            self.assertEqual(cached['risk_score'], 0.75)
    
    @unittest.skipIf(not CacheManager(CacheConfig()).enabled, "Redis not available")
    def test_cache_expiration(self):
        """Test cache TTL."""
        result = {'entity_id': 'TEST_001', 'risk_score': 0.75}
        
        self.cache.set('TEST_001', result, ttl=1)
        
        # Should exist immediately
        cached = self.cache.get('TEST_001')
        self.assertIsNotNone(cached)
        
        # Wait for expiration
        time.sleep(2)
        cached = self.cache.get('TEST_001')
        self.assertIsNone(cached)
    
    @unittest.skipIf(not CacheManager(CacheConfig()).enabled, "Redis not available")
    def test_cache_deletion(self):
        """Test cache deletion."""
        result = {'entity_id': 'TEST_001', 'risk_score': 0.75}
        
        self.cache.set('TEST_001', result)
        self.cache.delete('TEST_001')
        
        cached = self.cache.get('TEST_001')
        self.assertIsNone(cached)
    
    @unittest.skipIf(not CacheManager(CacheConfig()).enabled, "Redis not available")
    def test_batch_operations(self):
        """Test batch cache operations."""
        results = {
            'TEST_001': {'risk_score': 0.75},
            'TEST_002': {'risk_score': 0.80},
            'TEST_003': {'risk_score': 0.65}
        }
        
        self.cache.batch_set(results, ttl=60)
        
        cached_results = self.cache.batch_get(['TEST_001', 'TEST_002', 'TEST_003'])
        
        self.assertEqual(len(cached_results), 3)
        self.assertIsNotNone(cached_results['TEST_001'])
        self.assertIsNotNone(cached_results['TEST_002'])
        self.assertIsNotNone(cached_results['TEST_003'])
    
    def tearDown(self):
        """Clean up after tests."""
        if self.cache.enabled:
            self.cache.invalidate_all()
            self.cache.close()


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(window_size=100)
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertEqual(self.monitor.window_size, 100)
        self.assertEqual(len(self.monitor.metrics), 0)
        self.assertEqual(self.monitor.total_requests, 0)
    
    def test_record_inference(self):
        """Test recording inference metrics."""
        self.monitor.record_inference(
            entity_id='TEST_001',
            latency_ms=50.0,
            model_count=4,
            cache_hit=False,
            success=True
        )
        
        self.assertEqual(len(self.monitor.metrics), 1)
        self.assertEqual(self.monitor.total_requests, 1)
        self.assertEqual(self.monitor.total_successes, 1)
        self.assertEqual(self.monitor.total_cache_misses, 1)
    
    def test_latency_stats(self):
        """Test latency statistics."""
        # Record some metrics
        for i in range(10):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0 + i * 10,
                model_count=4,
                cache_hit=False,
                success=True
            )
        
        stats = self.monitor.get_latency_stats()
        
        self.assertIn('mean', stats)
        self.assertIn('median', stats)
        self.assertIn('p95', stats)
        self.assertIn('p99', stats)
        self.assertGreater(stats['mean'], 0)
    
    def test_throughput_stats(self):
        """Test throughput statistics."""
        for i in range(10):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=False,
                success=True
            )
            time.sleep(0.01)
        
        stats = self.monitor.get_throughput()
        
        self.assertIn('total_requests', stats)
        self.assertIn('requests_per_second_overall', stats)
        self.assertEqual(stats['total_requests'], 10)
        self.assertGreater(stats['requests_per_second_overall'], 0)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        # Record mix of cache hits and misses
        for i in range(10):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=(i % 2 == 0),
                success=True
            )
        
        stats = self.monitor.get_cache_stats()
        
        self.assertEqual(stats['total_hits'], 5)
        self.assertEqual(stats['total_misses'], 5)
        self.assertAlmostEqual(stats['hit_rate'], 0.5)
    
    def test_error_stats(self):
        """Test error statistics."""
        # Record mix of successes and failures
        for i in range(10):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=False,
                success=(i % 3 != 0),
                error='Test error' if i % 3 == 0 else None
            )
        
        stats = self.monitor.get_error_stats()
        
        self.assertGreater(stats['total_failures'], 0)
        self.assertGreater(stats['total_successes'], 0)
        self.assertIn('error_rate', stats)
        self.assertIn('Test error', stats['error_types'])
    
    def test_performance_targets(self):
        """Test performance target checking."""
        # Record some fast inferences
        for i in range(10):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=False,
                success=True
            )
        
        targets = self.monitor.check_performance_targets(
            target_latency_ms=100.0,
            target_throughput=1.0,
            target_success_rate=0.95
        )
        
        self.assertIn('latency_target_met', targets)
        self.assertIn('throughput_target_met', targets)
        self.assertIn('success_rate_target_met', targets)
        self.assertTrue(targets['latency_target_met'])
        self.assertTrue(targets['success_rate_target_met'])
    
    def test_reset(self):
        """Test monitor reset."""
        # Record some metrics
        for i in range(5):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=False,
                success=True
            )
        
        self.assertEqual(len(self.monitor.metrics), 5)
        
        # Reset
        self.monitor.reset()
        
        self.assertEqual(len(self.monitor.metrics), 0)
        self.assertEqual(self.monitor.total_requests, 0)
    
    def test_export_metrics(self):
        """Test metrics export."""
        for i in range(5):
            self.monitor.record_inference(
                entity_id=f'TEST_{i:03d}',
                latency_ms=50.0,
                model_count=4,
                cache_hit=False,
                success=True
            )
        
        exported = self.monitor.export_metrics()
        
        self.assertEqual(len(exported), 5)
        self.assertIsInstance(exported[0], dict)
        self.assertIn('entity_id', exported[0])
        self.assertIn('latency_ms', exported[0])


if __name__ == '__main__':
    unittest.main()

# Made with Bob
