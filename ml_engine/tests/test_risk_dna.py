"""
Unit Tests for Risk DNA Module
Tests DNA generation, comparison, evolution, and visualization.
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_dna.dna_generator import (
    RiskDNA, RiskDNAGenerator, PortfolioRiskDNA, TransactionRiskDNA
)
from risk_dna.dna_comparator import (
    DNAComparator, DNAClusterer, AnomalyDetector
)
from risk_dna.dna_evolution import (
    DNAEvolutionTracker, DNAMutationAnalyzer, DNAEvolutionPredictor
)


class TestRiskDNA(unittest.TestCase):
    """Test RiskDNA dataclass."""
    
    def test_initialization(self):
        """Test DNA initialization."""
        dna = RiskDNA(
            entity_id='TEST_001',
            dna_vector=np.random.randn(256),
            timestamp=datetime.now(),
            components={'portfolio_weight': 0.5},
            signature='abc123',
            metadata={}
        )
        
        self.assertEqual(dna.entity_id, 'TEST_001')
        self.assertEqual(len(dna.dna_vector), 256)
        self.assertIn('portfolio_weight', dna.components)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        dna = RiskDNA(
            entity_id='TEST_001',
            dna_vector=np.array([1.0, 2.0, 3.0]),
            timestamp=datetime.now(),
            components={'test': 1.0},
            signature='abc',
            metadata={}
        )
        
        dna_dict = dna.to_dict()
        
        self.assertIsInstance(dna_dict, dict)
        self.assertEqual(dna_dict['entity_id'], 'TEST_001')
        self.assertIsInstance(dna_dict['dna_vector'], list)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'entity_id': 'TEST_001',
            'dna_vector': [1.0, 2.0, 3.0],
            'timestamp': datetime.now().isoformat(),
            'components': {'test': 1.0},
            'signature': 'abc',
            'metadata': {}
        }
        
        dna = RiskDNA.from_dict(data)
        
        self.assertEqual(dna.entity_id, 'TEST_001')
        self.assertEqual(len(dna.dna_vector), 3)


class TestRiskDNAGenerator(unittest.TestCase):
    """Test Risk DNA Generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = RiskDNAGenerator(dna_dim=256, use_neural_encoder=False)
    
    def test_initialization(self):
        """Test generator initialization."""
        self.assertEqual(self.generator.dna_dim, 256)
        self.assertFalse(self.generator.use_neural_encoder)
    
    def test_generate_dna(self):
        """Test DNA generation."""
        features = {
            'portfolio': {'total_value': 1000000, 'num_positions': 50},
            'historical': {'volatility_30d': 0.2},
            'counterparty': {'num_counterparties': 10},
            'market': {'vix_level': 18.5}
        }
        
        dna = self.generator.generate('ENTITY_001', features)
        
        self.assertEqual(dna.entity_id, 'ENTITY_001')
        self.assertEqual(len(dna.dna_vector), 256)
        self.assertIsNotNone(dna.signature)
        self.assertIn('portfolio_weight', dna.components)
    
    def test_signature_uniqueness(self):
        """Test that different features produce different signatures."""
        features1 = {'portfolio': {'total_value': 1000000}}
        features2 = {'portfolio': {'total_value': 2000000}}
        
        dna1 = self.generator.generate('ENTITY_001', features1)
        dna2 = self.generator.generate('ENTITY_002', features2)
        
        self.assertNotEqual(dna1.signature, dna2.signature)
    
    def test_batch_generate(self):
        """Test batch DNA generation."""
        entities = [
            ('ENTITY_001', {'portfolio': {'total_value': 1000000}}),
            ('ENTITY_002', {'portfolio': {'total_value': 2000000}}),
            ('ENTITY_003', {'portfolio': {'total_value': 3000000}})
        ]
        
        dnas = self.generator.batch_generate(entities)
        
        self.assertEqual(len(dnas), 3)
        self.assertEqual(dnas[0].entity_id, 'ENTITY_001')


class TestPortfolioRiskDNA(unittest.TestCase):
    """Test Portfolio Risk DNA Generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = PortfolioRiskDNA(dna_dim=256)
    
    def test_generate_from_holdings(self):
        """Test DNA generation from holdings."""
        holdings = [
            {'value': 100000, 'sector': 'tech'},
            {'value': 150000, 'sector': 'finance'},
            {'value': 50000, 'sector': 'tech'}
        ]
        
        market_data = {'vix_level': 18.5}
        
        dna = self.generator.generate_from_holdings('PORT_001', holdings, market_data)
        
        self.assertEqual(dna.entity_id, 'PORT_001')
        self.assertEqual(len(dna.dna_vector), 256)


class TestDNAComparator(unittest.TestCase):
    """Test DNA Comparator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.comparator = DNAComparator(metric='cosine')
        self.generator = RiskDNAGenerator(dna_dim=256, use_neural_encoder=False)
    
    def test_compare_identical(self):
        """Test comparison of identical DNAs."""
        features = {'portfolio': {'total_value': 1000000}}
        dna = self.generator.generate('ENTITY_001', features)
        
        similarity = self.comparator.compare(dna, dna)
        
        self.assertAlmostEqual(similarity, 1.0, places=5)
    
    def test_compare_different(self):
        """Test comparison of different DNAs."""
        features1 = {'portfolio': {'total_value': 1000000}}
        features2 = {'portfolio': {'total_value': 10000000}}
        
        dna1 = self.generator.generate('ENTITY_001', features1)
        dna2 = self.generator.generate('ENTITY_002', features2)
        
        similarity = self.comparator.compare(dna1, dna2)
        
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_compare_batch(self):
        """Test batch comparison."""
        dnas = []
        for i in range(5):
            features = {'portfolio': {'total_value': 1000000 * (i + 1)}}
            dna = self.generator.generate(f'ENTITY_{i:03d}', features)
            dnas.append(dna)
        
        similarity_matrix = self.comparator.compare_batch(dnas)
        
        self.assertEqual(similarity_matrix.shape, (5, 5))
        # Diagonal should be 1.0
        np.testing.assert_array_almost_equal(np.diag(similarity_matrix), np.ones(5))
    
    def test_find_most_similar(self):
        """Test finding most similar DNAs."""
        dnas = []
        for i in range(10):
            features = {'portfolio': {'total_value': 1000000 * (i + 1)}}
            dna = self.generator.generate(f'ENTITY_{i:03d}', features)
            dnas.append(dna)
        
        query_dna = dnas[0]
        similar = self.comparator.find_most_similar(query_dna, dnas[1:], top_k=3)
        
        self.assertEqual(len(similar), 3)
        # Check that similarities are sorted
        similarities = [s for _, s in similar]
        self.assertEqual(similarities, sorted(similarities, reverse=True))


class TestDNAClusterer(unittest.TestCase):
    """Test DNA Clusterer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.clusterer = DNAClusterer(method='kmeans', n_clusters=3)
        self.generator = RiskDNAGenerator(dna_dim=256, use_neural_encoder=False)
    
    def test_fit(self):
        """Test clustering."""
        dnas = []
        for i in range(15):
            features = {'portfolio': {'total_value': 1000000 * (i + 1)}}
            dna = self.generator.generate(f'ENTITY_{i:03d}', features)
            dnas.append(dna)
        
        labels = self.clusterer.fit(dnas)
        
        self.assertEqual(len(labels), 15)
        self.assertEqual(len(set(labels)), 3)  # 3 clusters
    
    def test_get_cluster_profiles(self):
        """Test cluster profile extraction."""
        dnas = []
        for i in range(15):
            features = {'portfolio': {'total_value': 1000000 * (i + 1)}}
            dna = self.generator.generate(f'ENTITY_{i:03d}', features)
            dnas.append(dna)
        
        self.clusterer.fit(dnas)
        profiles = self.clusterer.get_cluster_profiles(dnas)
        
        self.assertIsInstance(profiles, dict)
        self.assertGreater(len(profiles), 0)


class TestAnomalyDetector(unittest.TestCase):
    """Test Anomaly Detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = AnomalyDetector(threshold=2.0)
        self.generator = RiskDNAGenerator(dna_dim=256, use_neural_encoder=False)
    
    def test_fit_and_detect(self):
        """Test anomaly detection."""
        # Generate normal DNAs
        normal_dnas = []
        for i in range(10):
            features = {'portfolio': {'total_value': 1000000 + i * 10000}}
            dna = self.generator.generate(f'ENTITY_{i:03d}', features)
            normal_dnas.append(dna)
        
        self.detector.fit(normal_dnas)
        
        # Test normal DNA
        is_anomaly, score = self.detector.detect(normal_dnas[0])
        self.assertFalse(is_anomaly)
        
        # Test anomalous DNA
        anomalous_features = {'portfolio': {'total_value': 100000000}}
        anomalous_dna = self.generator.generate('ANOMALY', anomalous_features)
        is_anomaly, score = self.detector.detect(anomalous_dna)
        
        self.assertGreaterEqual(score, 0.0)


class TestDNAEvolutionTracker(unittest.TestCase):
    """Test DNA Evolution Tracker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = DNAEvolutionTracker(window_size=30)
        self.generator = RiskDNAGenerator(dna_dim=256, use_neural_encoder=False)
    
    def test_add_dna(self):
        """Test adding DNA to tracker."""
        features = {'portfolio': {'total_value': 1000000}}
        dna = self.generator.generate('ENTITY_001', features)
        
        self.tracker.add_dna(dna)
        
        self.assertIn('ENTITY_001', self.tracker.history)
        self.assertEqual(len(self.tracker.history['ENTITY_001']), 1)
    
    def test_get_evolution_rate(self):
        """Test evolution rate computation."""
        for i in range(5):
            features = {'portfolio': {'total_value': 1000000 * (1 + i * 0.1)}}
            dna = self.generator.generate('ENTITY_001', features)
            dna.timestamp = datetime.now() - timedelta(days=5-i)
            self.tracker.add_dna(dna)
        
        rate = self.tracker.get_evolution_rate('ENTITY_001')
        
        self.assertGreaterEqual(rate, 0.0)
    
    def test_detect_mutations(self):
        """Test mutation detection."""
        # Add DNAs with significant change
        for i in range(3):
            features = {'portfolio': {'total_value': 1000000 * (1 + i * 2)}}
            dna = self.generator.generate('ENTITY_001', features)
            dna.timestamp = datetime.now() - timedelta(days=3-i)
            self.tracker.add_dna(dna)
        
        mutations = self.tracker.detect_mutations('ENTITY_001', threshold=0.1)
        
        self.assertIsInstance(mutations, list)


class TestDNAEvolutionPredictor(unittest.TestCase):
    """Test DNA Evolution Predictor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.predictor = DNAEvolutionPredictor(prediction_horizon=7)
    
    def test_predict(self):
        """Test prediction."""
        # Create trajectory
        trajectory = np.random.randn(10, 256)
        
        predictions = self.predictor.predict(trajectory)
        
        self.assertEqual(predictions.shape, (7, 256))
    
    def test_predict_with_confidence(self):
        """Test prediction with confidence intervals."""
        trajectory = np.random.randn(10, 256)
        
        predictions, confidence = self.predictor.predict_with_confidence(trajectory)
        
        self.assertEqual(predictions.shape, (7, 256))
        self.assertEqual(confidence.shape, (256,))


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRiskDNA))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskDNAGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioRiskDNA))
    suite.addTests(loader.loadTestsFromTestCase(TestDNAComparator))
    suite.addTests(loader.loadTestsFromTestCase(TestDNAClusterer))
    suite.addTests(loader.loadTestsFromTestCase(TestAnomalyDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestDNAEvolutionTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestDNAEvolutionPredictor))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

# Made with Bob
