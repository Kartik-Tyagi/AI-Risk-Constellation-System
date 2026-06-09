"""
Unit Tests for Temporal Graph Neural Networks
Tests temporal GNN, cascade predictor, and data loader.
"""

import unittest
import torch
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_networks.temporal_gnn import (
    TemporalGATLayer, TemporalGNN, TemporalGRUGNN, AttentionTemporalAggregator
)
from graph_networks.risk_cascade_predictor import (
    CascadeDetector, RiskCascadePredictor, TemporalPatternRecognizer,
    MultiStepCascadePredictor
)
from graph_networks.temporal_data_loader import (
    TemporalGraphDataset, TemporalDataLoader, MissingDataHandler,
    TemporalAugmenter
)

try:
    from torch_geometric.data import Data
except ImportError:
    Data = None


class TestTemporalGATLayer(unittest.TestCase):
    """Test Temporal GAT Layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.layer = TemporalGATLayer(
                in_channels=10,
                out_channels=16,
                heads=4
            )
    
    def test_initialization(self):
        """Test layer initialization."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        self.assertIsNotNone(self.layer.gat)
        self.assertIsNotNone(self.layer.lstm)
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 20
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, 40))
        
        output, hidden = self.layer(x, edge_index)
        
        self.assertEqual(output.shape[0], num_nodes)
        self.assertIsNotNone(hidden)


class TestTemporalGNN(unittest.TestCase):
    """Test Temporal GNN model."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.model = TemporalGNN(
                node_feature_dim=10,
                edge_feature_dim=5,
                hidden_dim=32,
                output_dim=16,
                num_layers=2,
                heads=4,
                prediction_horizon=5
            )
    
    def test_initialization(self):
        """Test model initialization."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        self.assertEqual(self.model.num_layers, 2)
        self.assertEqual(self.model.prediction_horizon, 5)
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_time_steps = 10
        
        x_sequence = [torch.randn(num_nodes, 10) for _ in range(num_time_steps)]
        edge_index_sequence = [torch.randint(0, num_nodes, (2, 50)) for _ in range(num_time_steps)]
        
        predictions, hidden_states = self.model(x_sequence, edge_index_sequence)
        
        self.assertEqual(predictions.shape[0], num_nodes)
        self.assertEqual(predictions.shape[1], 5)  # prediction_horizon
        self.assertEqual(len(hidden_states), 2)  # num_layers
    
    def test_predict_future(self):
        """Test future prediction."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_time_steps = 10
        
        x_sequence = [torch.randn(num_nodes, 10) for _ in range(num_time_steps)]
        edge_index_sequence = [torch.randint(0, num_nodes, (2, 50)) for _ in range(num_time_steps)]
        
        predictions = self.model.predict_future(x_sequence, edge_index_sequence, num_future_steps=3)
        
        self.assertEqual(predictions.shape, (num_nodes, 3))


class TestTemporalGRUGNN(unittest.TestCase):
    """Test Temporal GRU-GNN model."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.model = TemporalGRUGNN(
                node_feature_dim=10,
                hidden_dim=32,
                output_dim=16,
                num_layers=2,
                heads=4
            )
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_time_steps = 10
        
        x_sequence = [torch.randn(num_nodes, 10) for _ in range(num_time_steps)]
        edge_index_sequence = [torch.randint(0, num_nodes, (2, 50)) for _ in range(num_time_steps)]
        
        output = self.model(x_sequence, edge_index_sequence)
        
        self.assertEqual(output.shape, (num_nodes, 16))


class TestCascadeDetector(unittest.TestCase):
    """Test Cascade Detector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = CascadeDetector(
            feature_dim=20,
            hidden_dim=64,
            threshold=0.7
        )
    
    def test_forward_pass(self):
        """Test forward pass."""
        x = torch.randn(50, 20)
        
        cascade_prob, severity = self.detector(x)
        
        self.assertEqual(cascade_prob.shape, (50, 1))
        self.assertEqual(severity.shape, (50, 1))
        
        # Check probability range
        self.assertTrue(torch.all(cascade_prob >= 0))
        self.assertTrue(torch.all(cascade_prob <= 1))
    
    def test_detect_cascades(self):
        """Test cascade detection."""
        x = torch.randn(50, 20)
        
        cascade_mask, probs, severities = self.detector.detect_cascades(x)
        
        self.assertEqual(cascade_mask.shape, (50, 1))
        # Mask should be binary
        self.assertTrue(torch.all((cascade_mask == 0) | (cascade_mask == 1)))


class TestRiskCascadePredictor(unittest.TestCase):
    """Test Risk Cascade Predictor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.predictor = RiskCascadePredictor(
            node_feature_dim=20,
            temporal_feature_dim=15,
            hidden_dim=64,
            num_cascade_steps=5
        )
    
    def test_forward_pass(self):
        """Test forward pass."""
        num_nodes = 50
        seq_len = 10
        
        node_features = torch.randn(num_nodes, 20)
        temporal_features = torch.randn(num_nodes, seq_len, 15)
        edge_index = torch.randint(0, num_nodes, (2, 100))
        
        cascade_preds, confidence = self.predictor(
            node_features, temporal_features, edge_index
        )
        
        self.assertEqual(len(cascade_preds), 5)
        for pred in cascade_preds:
            self.assertEqual(pred.shape, (num_nodes, 1))
        
        self.assertEqual(confidence.shape, (num_nodes, 1))
    
    def test_predict_with_intervals(self):
        """Test prediction with confidence intervals."""
        num_nodes = 50
        seq_len = 10
        
        node_features = torch.randn(num_nodes, 20)
        temporal_features = torch.randn(num_nodes, seq_len, 15)
        edge_index = torch.randint(0, num_nodes, (2, 100))
        
        intervals = self.predictor.predict_with_intervals(
            node_features, temporal_features, edge_index, num_samples=10
        )
        
        self.assertIn('mean', intervals)
        self.assertIn('std', intervals)
        self.assertIn('lower', intervals)
        self.assertIn('upper', intervals)
        
        # Check shapes
        self.assertEqual(intervals['mean'].shape[0], 5)  # num_cascade_steps
        self.assertEqual(intervals['mean'].shape[1], num_nodes)


class TestTemporalPatternRecognizer(unittest.TestCase):
    """Test Temporal Pattern Recognizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recognizer = TemporalPatternRecognizer(
            feature_dim=20,
            pattern_dim=64,
            num_patterns=10
        )
    
    def test_forward_pass(self):
        """Test forward pass."""
        x = torch.randn(32, 20)
        
        pattern_probs, embeddings = self.recognizer(x)
        
        self.assertEqual(pattern_probs.shape, (32, 10))
        self.assertEqual(embeddings.shape, (32, 64))
        
        # Check probabilities sum to 1
        prob_sums = torch.sum(pattern_probs, dim=1)
        self.assertTrue(torch.allclose(prob_sums, torch.ones(32), atol=1e-5))
    
    def test_pattern_similarity(self):
        """Test pattern similarity computation."""
        x = torch.randn(32, 20)
        
        similarity = self.recognizer.get_pattern_similarity(x)
        
        self.assertEqual(similarity.shape, (32, 10))
        # Similarity should be in [-1, 1] for cosine similarity
        self.assertTrue(torch.all(similarity >= -1))
        self.assertTrue(torch.all(similarity <= 1))


class TestMultiStepCascadePredictor(unittest.TestCase):
    """Test Multi-Step Cascade Predictor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.predictor = MultiStepCascadePredictor(
            feature_dim=20,
            hidden_dim=64,
            max_steps=10
        )
    
    def test_forward_pass(self):
        """Test forward pass."""
        batch_size = 16
        seq_len = 10
        
        x = torch.randn(batch_size, seq_len, 20)
        
        predictions = self.predictor(x, num_steps=5)
        
        self.assertEqual(predictions.shape, (batch_size, 5, 1))
        
        # Check probability range
        self.assertTrue(torch.all(predictions >= 0))
        self.assertTrue(torch.all(predictions <= 1))


class TestTemporalGraphDataset(unittest.TestCase):
    """Test Temporal Graph Dataset."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.dataset = TemporalGraphDataset(
            data_dir=self.temp_dir,
            sequence_length=10,
            prediction_horizon=5
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test dataset initialization."""
        self.assertEqual(self.dataset.sequence_length, 10)
        self.assertEqual(self.dataset.prediction_horizon, 5)
    
    def test_length(self):
        """Test dataset length."""
        # Initially empty
        self.assertEqual(len(self.dataset), 0)


class TestMissingDataHandler(unittest.TestCase):
    """Test Missing Data Handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = MissingDataHandler(strategy='interpolate')
    
    def test_interpolate_strategy(self):
        """Test interpolation strategy."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        # Create sequence with missing data
        sequence = [
            Data(x=torch.randn(10, 5), edge_index=torch.randint(0, 10, (2, 20))),
            None,  # Missing
            Data(x=torch.randn(10, 5), edge_index=torch.randint(0, 10, (2, 20)))
        ]
        
        processed = self.handler.handle_missing_nodes(sequence)
        
        # Should have same length
        self.assertEqual(len(processed), 3)
        # Middle element should be filled
        self.assertIsNotNone(processed[1])
    
    def test_forward_fill_strategy(self):
        """Test forward fill strategy."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        handler = MissingDataHandler(strategy='forward_fill')
        
        sequence = [
            Data(x=torch.randn(10, 5), edge_index=torch.randint(0, 10, (2, 20))),
            None,
            None
        ]
        
        processed = handler.handle_missing_nodes(sequence)
        
        self.assertEqual(len(processed), 3)
        # Should forward fill from first element
        self.assertIsNotNone(processed[1])
        self.assertIsNotNone(processed[2])


class TestTemporalAugmenter(unittest.TestCase):
    """Test Temporal Augmenter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.augmenter = TemporalAugmenter(
            noise_level=0.01,
            time_warp_prob=0.1,
            node_dropout_prob=0.05
        )
    
    def test_augmentation(self):
        """Test data augmentation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        sequence = [
            Data(x=torch.randn(10, 5), edge_index=torch.randint(0, 10, (2, 20)))
            for _ in range(10)
        ]
        
        augmented = self.augmenter.augment(sequence)
        
        # Should return a sequence
        self.assertIsInstance(augmented, list)
        self.assertGreater(len(augmented), 0)


class TestAttentionTemporalAggregator(unittest.TestCase):
    """Test Attention Temporal Aggregator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = AttentionTemporalAggregator(feature_dim=64)
    
    def test_forward_pass(self):
        """Test forward pass."""
        num_nodes = 50
        time_steps = 10
        features = 64
        
        temporal_features = torch.randn(num_nodes, time_steps, features)
        
        aggregated = self.aggregator(temporal_features)
        
        self.assertEqual(aggregated.shape, (num_nodes, features))


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalGATLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalGNN))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalGRUGNN))
    suite.addTests(loader.loadTestsFromTestCase(TestCascadeDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskCascadePredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalPatternRecognizer))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiStepCascadePredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalGraphDataset))
    suite.addTests(loader.loadTestsFromTestCase(TestMissingDataHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestTemporalAugmenter))
    suite.addTests(loader.loadTestsFromTestCase(TestAttentionTemporalAggregator))
    
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
