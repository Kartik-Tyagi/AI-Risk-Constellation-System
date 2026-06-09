"""
Graph Neural Networks Module
Implements GAT-based models for risk propagation and network analysis.
"""

from .gat_model import GATConv, GAT, MultiHeadGATLayer
from .risk_propagation_gat import RiskPropagationGAT
from .graph_builder import RiskGraphBuilder, DynamicGraphBuilder
from .training_loop import GATTrainer, RiskPropagationTrainer, create_data_loaders
from .temporal_gnn import TemporalGNN, TemporalGRUGNN, TemporalGATLayer, AttentionTemporalAggregator
from .risk_cascade_predictor import (
    CascadeDetector, RiskCascadePredictor, TemporalPatternRecognizer, MultiStepCascadePredictor
)
from .temporal_data_loader import (
    TemporalGraphDataset, TemporalDataLoader, MissingDataHandler, TemporalAugmenter,
    create_temporal_dataloaders
)

__all__ = [
    # GAT models
    'GATConv',
    'GAT',
    'MultiHeadGATLayer',
    'RiskPropagationGAT',
    # Graph builders
    'RiskGraphBuilder',
    'DynamicGraphBuilder',
    # Training
    'GATTrainer',
    'RiskPropagationTrainer',
    'create_data_loaders',
    # Temporal GNN
    'TemporalGNN',
    'TemporalGRUGNN',
    'TemporalGATLayer',
    'AttentionTemporalAggregator',
    # Cascade prediction
    'CascadeDetector',
    'RiskCascadePredictor',
    'TemporalPatternRecognizer',
    'MultiStepCascadePredictor',
    # Data loading
    'TemporalGraphDataset',
    'TemporalDataLoader',
    'MissingDataHandler',
    'TemporalAugmenter',
    'create_temporal_dataloaders'
]

# Made with Bob
