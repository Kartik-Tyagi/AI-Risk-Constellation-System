"""
Unit Tests for Graph Attention Network Modules
Tests GAT model, risk propagation, graph builder, and training loop.
"""

import unittest
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_networks.gat_model import (
    GATConv, GAT, MultiHeadGATLayer
)
from graph_networks.risk_propagation_gat import (
    RiskPropagationGAT
)
from graph_networks.graph_builder import (
    RiskGraphBuilder, DynamicGraphBuilder
)
from graph_networks.training_loop import (
    GATTrainer, RiskPropagationTrainer, create_data_loaders
)

try:
    from torch_geometric.data import Data
except ImportError:
    Data = None


class TestGATConv(unittest.TestCase):
    """Test GAT convolution layer implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.in_channels = 10
        self.out_channels = 16
        self.num_heads = 4
        
        if Data is not None:
            self.layer = GATConv(
                self.in_channels,
                self.out_channels,
                heads=self.num_heads
            )
    
    def test_initialization(self):
        """Test layer initialization."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        self.assertEqual(self.layer.in_channels, self.in_channels)
        self.assertEqual(self.layer.out_channels, self.out_channels)
        self.assertEqual(self.layer.num_heads, self.num_heads)
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        # Create dummy data
        num_nodes = 20
        num_edges = 50
        
        x = torch.randn(num_nodes, self.in_channels)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        # Forward pass
        output = self.layer(x, edge_index)
        
        # Check output shape
        expected_shape = (num_nodes, self.out_channels * self.num_heads)
        self.assertEqual(output.shape, expected_shape)
    
    def test_attention_weights(self):
        """Test attention weight computation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 10
        num_edges = 20
        
        x = torch.randn(num_nodes, self.in_channels)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        # Forward pass with attention return
        output, attention = self.layer(x, edge_index, return_attention=True)
        
        # Check attention shape
        self.assertEqual(attention.shape[0], num_edges)
        self.assertEqual(attention.shape[1], self.num_heads)
        
        # Check attention values are in [0, 1]
        self.assertTrue(torch.all(attention >= 0))
        self.assertTrue(torch.all(attention <= 1))


class TestGAT(unittest.TestCase):
    """Test multi-layer GAT model."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.model = GAT(
                in_channels=10,
                hidden_channels=32,
                out_channels=1,
                heads=4,
                num_layers=2
            )
    
    def test_initialization(self):
        """Test model initialization."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        self.assertEqual(len(self.model.gat_layers), 2)
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_edges = 80
        
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        output = self.model(x, edge_index)
        
        # Check output shape
        self.assertEqual(output.shape, (num_nodes, 1))
    
    def test_with_edge_features(self):
        """Test forward pass with edge features."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_edges = 80
        
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        edge_attr = torch.randn(num_edges, 5)
        
        output = self.model(x, edge_index, edge_attr)
        
        self.assertEqual(output.shape, (num_nodes, 1))
    
    def test_dropout(self):
        """Test dropout during training."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_edges = 80
        
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        # Training mode
        self.model.train()
        output1 = self.model(x, edge_index)
        output2 = self.model(x, edge_index)
        
        # Outputs should be different due to dropout
        self.assertFalse(torch.allclose(output1, output2))
        
        # Eval mode
        self.model.eval()
        output3 = self.model(x, edge_index)
        output4 = self.model(x, edge_index)
        
        # Outputs should be same in eval mode
        self.assertTrue(torch.allclose(output3, output4))


class TestRiskPropagationGAT(unittest.TestCase):
    """Test risk propagation GAT model."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.model = RiskPropagationGAT(
                node_feature_dim=10,
                edge_feature_dim=5,
                hidden_dim=32,
                heads=4,
                num_layers=2
            )
    
    def test_forward_pass(self):
        """Test forward pass."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 30
        num_edges = 80
        
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        risk_scores, cascade_probs = self.model(x, edge_index)
        
        # Check output shapes
        self.assertEqual(risk_scores.shape, (num_nodes, 1))
        self.assertEqual(cascade_probs.shape, (num_nodes, 1))
        
        # Check value ranges
        self.assertTrue(torch.all(risk_scores >= 0))
        self.assertTrue(torch.all(cascade_probs >= 0))
        self.assertTrue(torch.all(cascade_probs <= 1))
    
    def test_propagate_risk(self):
        """Test risk propagation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        num_nodes = 20
        num_edges = 40
        
        x = torch.randn(num_nodes, 10)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        
        # Initial risk scores
        initial_risks = torch.rand(num_nodes, 1)
        
        # Propagate risk
        propagated_risks = self.model.propagate_risk(
            x, edge_index, initial_risks, num_steps=3
        )
        
        self.assertEqual(propagated_risks.shape, (num_nodes, 1))


class TestGraphBuilder(unittest.TestCase):
    """Test graph builder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = RiskGraphBuilder()
        
        # Create sample data
        self.nodes_df = pd.DataFrame({
            'counterparty_id': [f'CP{i:04d}' for i in range(10)],
            'credit_score': np.random.uniform(50, 100, 10),
            'total_exposure': np.random.lognormal(15, 1, 10),
            'leverage_ratio': np.random.uniform(1, 5, 10),
            'liquidity_ratio': np.random.uniform(0.1, 0.5, 10),
            'systemic_importance': np.random.uniform(0, 100, 10)
        })
        
        self.edges_df = pd.DataFrame({
            'counterparty_1': [f'CP{i:04d}' for i in np.random.randint(0, 10, 20)],
            'counterparty_2': [f'CP{i:04d}' for i in np.random.randint(0, 10, 20)],
            'exposure_amount': np.random.lognormal(14, 1, 20),
            'strength': np.random.uniform(0, 1, 20),
            'correlation': np.random.uniform(-0.3, 0.8, 20)
        })
    
    def test_build_graph(self):
        """Test graph building."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        data = self.builder.build_from_dataframes(
            self.nodes_df, self.edges_df
        )
        
        # Check data structure
        self.assertEqual(data.num_nodes, 10)
        self.assertIsNotNone(data.x)
        self.assertIsNotNone(data.edge_index)
        self.assertIsNotNone(data.edge_attr)
    
    def test_node_features(self):
        """Test node feature extraction."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        data = self.builder.build_from_dataframes(
            self.nodes_df, self.edges_df
        )
        
        # Check feature shape
        self.assertEqual(data.x.shape[0], 10)
        self.assertEqual(data.x.shape[1], 5)  # 5 features
    
    def test_edge_features(self):
        """Test edge feature extraction."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        data = self.builder.build_from_dataframes(
            self.nodes_df, self.edges_df
        )
        
        # Check edge features
        self.assertIsNotNone(data.edge_attr)
        self.assertEqual(data.edge_attr.shape[1], 3)  # 3 features
    
    def test_node_mapping(self):
        """Test node ID to index mapping."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        data = self.builder.build_from_dataframes(
            self.nodes_df, self.edges_df
        )
        
        # Check mapping
        self.assertEqual(len(self.builder.node_id_to_idx), 10)
        self.assertEqual(len(self.builder.idx_to_node_id), 10)
    
    def test_subgraph_creation(self):
        """Test subgraph creation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        data = self.builder.build_from_dataframes(
            self.nodes_df, self.edges_df
        )
        
        # Create subgraph with first 5 nodes
        subgraph = self.builder.create_subgraph(data, [0, 1, 2, 3, 4])
        
        self.assertEqual(subgraph.num_nodes, 5)
        self.assertLessEqual(subgraph.edge_index.shape[1], data.edge_index.shape[1])


class TestDynamicGraphBuilder(unittest.TestCase):
    """Test dynamic graph builder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = DynamicGraphBuilder(time_window=30)
        
        # Create temporal data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        self.nodes_df = pd.DataFrame({
            'counterparty_id': [f'CP{i:04d}' for i in range(10)],
            'credit_score': np.random.uniform(50, 100, 10)
        })
        
        self.edges_df = pd.DataFrame({
            'counterparty_1': [f'CP{i:04d}' for i in np.random.randint(0, 10, 100)],
            'counterparty_2': [f'CP{i:04d}' for i in np.random.randint(0, 10, 100)],
            'exposure_amount': np.random.lognormal(14, 1, 100),
            'date': dates
        })
    
    def test_temporal_snapshots(self):
        """Test temporal snapshot creation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        snapshots = self.builder.build_temporal_snapshots(
            self.nodes_df, self.edges_df, num_snapshots=5
        )
        
        # Check number of snapshots
        self.assertGreater(len(snapshots), 0)
        self.assertLessEqual(len(snapshots), 5)
        
        # Check each snapshot
        for snapshot in snapshots:
            self.assertIsNotNone(snapshot.x)
            self.assertIsNotNone(snapshot.edge_index)


class TestGATTrainer(unittest.TestCase):
    """Test GAT trainer."""
    
    def setUp(self):
        """Set up test fixtures."""
        if Data is not None:
            self.model = GAT(
                in_channels=10,
                hidden_channels=16,
                out_channels=1,
                heads=2,
                num_layers=2
            )
            
            # Create temporary checkpoint directory
            self.temp_dir = tempfile.mkdtemp()
            
            self.trainer = GATTrainer(
                model=self.model,
                device='cpu',
                learning_rate=0.01,
                patience=5,
                checkpoint_dir=self.temp_dir
            )
    
    def tearDown(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test trainer initialization."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        self.assertIsNotNone(self.trainer.optimizer)
        self.assertEqual(self.trainer.device, 'cpu')
    
    def test_checkpoint_save_load(self):
        """Test checkpoint saving and loading."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        # Save checkpoint
        self.trainer.save_checkpoint('test_checkpoint.pt', epoch=0, val_loss=0.5)
        
        # Modify model
        for param in self.model.parameters():
            param.data.fill_(0.0)
        
        # Load checkpoint
        self.trainer.load_checkpoint('test_checkpoint.pt')
        
        # Check model was restored
        has_nonzero = False
        for param in self.model.parameters():
            if torch.any(param.data != 0.0):
                has_nonzero = True
                break
        
        self.assertTrue(has_nonzero)


class TestDataLoaders(unittest.TestCase):
    """Test data loader creation."""
    
    def test_create_data_loaders(self):
        """Test data loader creation."""
        if Data is None:
            self.skipTest("PyTorch Geometric not installed")
        
        # Create dummy data
        data_list = []
        for _ in range(50):
            x = torch.randn(20, 10)
            edge_index = torch.randint(0, 20, (2, 40))
            y = torch.randn(20, 1)
            data_list.append(Data(x=x, edge_index=edge_index, y=y))
        
        # Create loaders
        train_loader, val_loader, test_loader = create_data_loaders(
            data_list, train_ratio=0.7, val_ratio=0.15, batch_size=8
        )
        
        # Check loaders
        self.assertGreater(len(train_loader), 0)
        self.assertGreater(len(val_loader), 0)
        self.assertGreater(len(test_loader), 0)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGATConv))
    suite.addTests(loader.loadTestsFromTestCase(TestGAT))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskPropagationGAT))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicGraphBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestGATTrainer))
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoaders))
    
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
