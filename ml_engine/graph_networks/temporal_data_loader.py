"""
Temporal Data Loader
Handles loading and batching of time-series graph data.
"""

import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data, Batch
from typing import List, Tuple, Optional, Dict, Callable
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class TemporalGraphDataset:
    """
    Dataset for temporal graph sequences.
    """
    
    def __init__(self, data_dir: str, sequence_length: int = 10,
                 prediction_horizon: int = 5, stride: int = 1):
        """
        Initialize temporal graph dataset.
        
        Args:
            data_dir: Directory containing graph data
            sequence_length: Length of input sequences
            prediction_horizon: Number of steps to predict
            stride: Stride for sliding window
        """
        self.data_dir = Path(data_dir)
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.stride = stride
        
        self.sequences = []
        self.targets = []
        
        logger.info(f"Initialized TemporalGraphDataset from {data_dir}")
    
    def load_from_snapshots(self, snapshot_files: List[str]):
        """
        Load data from graph snapshot files.
        
        Args:
            snapshot_files: List of snapshot file paths
        """
        # Load all snapshots
        snapshots = []
        for file_path in snapshot_files:
            snapshot = torch.load(file_path)
            snapshots.append(snapshot)
        
        # Create sequences with sliding window
        for i in range(0, len(snapshots) - self.sequence_length - self.prediction_horizon + 1, self.stride):
            sequence = snapshots[i:i + self.sequence_length]
            target = snapshots[i + self.sequence_length:i + self.sequence_length + self.prediction_horizon]
            
            self.sequences.append(sequence)
            self.targets.append(target)
        
        logger.info(f"Loaded {len(self.sequences)} sequences from {len(snapshot_files)} snapshots")
    
    def __len__(self) -> int:
        """Return number of sequences."""
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple[List[Data], List[Data]]:
        """
        Get sequence and target.
        
        Args:
            idx: Sequence index
            
        Returns:
            Tuple of (input_sequence, target_sequence)
        """
        return self.sequences[idx], self.targets[idx]


class TemporalBatchSampler:
    """
    Sampler for creating temporal batches.
    """
    
    def __init__(self, dataset: TemporalGraphDataset, batch_size: int = 32,
                 shuffle: bool = True):
        """
        Initialize batch sampler.
        
        Args:
            dataset: Temporal graph dataset
            batch_size: Batch size
            shuffle: Whether to shuffle data
        """
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        self.indices = list(range(len(dataset)))
    
    def __iter__(self):
        """Iterate over batches."""
        if self.shuffle:
            np.random.shuffle(self.indices)
        
        for i in range(0, len(self.indices), self.batch_size):
            batch_indices = self.indices[i:i + self.batch_size]
            yield batch_indices
    
    def __len__(self) -> int:
        """Return number of batches."""
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size


class TemporalDataLoader:
    """
    Data loader for temporal graph sequences.
    """
    
    def __init__(self, dataset: TemporalGraphDataset, batch_size: int = 32,
                 shuffle: bool = True, num_workers: int = 0):
        """
        Initialize data loader.
        
        Args:
            dataset: Temporal graph dataset
            batch_size: Batch size
            shuffle: Whether to shuffle
            num_workers: Number of worker processes
        """
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_workers = num_workers
        
        self.sampler = TemporalBatchSampler(dataset, batch_size, shuffle)
    
    def __iter__(self):
        """Iterate over batches."""
        for batch_indices in self.sampler:
            # Collect sequences for this batch
            batch_sequences = []
            batch_targets = []
            
            for idx in batch_indices:
                seq, target = self.dataset[idx]
                batch_sequences.append(seq)
                batch_targets.append(target)
            
            yield self._collate_fn(batch_sequences, batch_targets)
    
    def __len__(self) -> int:
        """Return number of batches."""
        return len(self.sampler)
    
    def _collate_fn(self, sequences: List[List[Data]], 
                    targets: List[List[Data]]) -> Tuple[List[Data], List[Data]]:
        """
        Collate function for batching.
        
        Args:
            sequences: List of input sequences
            targets: List of target sequences
            
        Returns:
            Tuple of (batched_sequences, batched_targets)
        """
        # For temporal data, we keep sequences separate but batch graphs at each time step
        batch_size = len(sequences)
        seq_length = len(sequences[0])
        
        batched_sequences = []
        for t in range(seq_length):
            # Collect all graphs at time t
            graphs_at_t = [sequences[i][t] for i in range(batch_size)]
            # Batch them
            batched_graph = Batch.from_data_list(graphs_at_t)
            batched_sequences.append(batched_graph)
        
        # Same for targets
        target_length = len(targets[0])
        batched_targets = []
        for t in range(target_length):
            graphs_at_t = [targets[i][t] for i in range(batch_size)]
            batched_graph = Batch.from_data_list(graphs_at_t)
            batched_targets.append(batched_graph)
        
        return batched_sequences, batched_targets


class MissingDataHandler:
    """
    Handles missing data in temporal graph sequences.
    """
    
    def __init__(self, strategy: str = 'interpolate'):
        """
        Initialize missing data handler.
        
        Args:
            strategy: Strategy for handling missing data
                     ('interpolate', 'forward_fill', 'zero', 'mean')
        """
        self.strategy = strategy
        logger.info(f"Initialized MissingDataHandler with strategy: {strategy}")
    
    def handle_missing_nodes(self, graph_sequence: List[Data]) -> List[Data]:
        """
        Handle missing nodes in graph sequence.
        
        Args:
            graph_sequence: List of graph snapshots
            
        Returns:
            Processed graph sequence
        """
        if self.strategy == 'interpolate':
            return self._interpolate_missing(graph_sequence)
        elif self.strategy == 'forward_fill':
            return self._forward_fill(graph_sequence)
        elif self.strategy == 'zero':
            return self._fill_zero(graph_sequence)
        elif self.strategy == 'mean':
            return self._fill_mean(graph_sequence)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _interpolate_missing(self, graph_sequence: List[Data]) -> List[Data]:
        """Linear interpolation for missing values."""
        processed = []
        
        for i, graph in enumerate(graph_sequence):
            if graph is None or graph.x is None:
                # Interpolate between previous and next
                if i > 0 and i < len(graph_sequence) - 1:
                    prev_graph = graph_sequence[i - 1]
                    next_graph = graph_sequence[i + 1]
                    
                    if prev_graph is not None and next_graph is not None:
                        # Linear interpolation
                        interpolated_x = (prev_graph.x + next_graph.x) / 2
                        graph = Data(x=interpolated_x, edge_index=prev_graph.edge_index)
                
                processed.append(graph)
            else:
                processed.append(graph)
        
        return processed
    
    def _forward_fill(self, graph_sequence: List[Data]) -> List[Data]:
        """Forward fill missing values."""
        processed = []
        last_valid = None
        
        for graph in graph_sequence:
            if graph is None or graph.x is None:
                if last_valid is not None:
                    processed.append(last_valid)
                else:
                    processed.append(graph)
            else:
                processed.append(graph)
                last_valid = graph
        
        return processed
    
    def _fill_zero(self, graph_sequence: List[Data]) -> List[Data]:
        """Fill missing values with zeros."""
        processed = []
        
        for graph in graph_sequence:
            if graph is None or graph.x is None:
                # Create zero-filled graph
                if len(processed) > 0:
                    ref_graph = processed[-1]
                    zero_x = torch.zeros_like(ref_graph.x)
                    graph = Data(x=zero_x, edge_index=ref_graph.edge_index)
            
            processed.append(graph)
        
        return processed
    
    def _fill_mean(self, graph_sequence: List[Data]) -> List[Data]:
        """Fill missing values with mean."""
        # Compute mean features
        valid_features = []
        for graph in graph_sequence:
            if graph is not None and graph.x is not None:
                valid_features.append(graph.x)
        
        if len(valid_features) == 0:
            return graph_sequence
        
        mean_features = torch.stack(valid_features).mean(dim=0)
        
        # Fill missing
        processed = []
        for graph in graph_sequence:
            if graph is None or graph.x is None:
                if len(processed) > 0:
                    ref_graph = processed[-1]
                    graph = Data(x=mean_features, edge_index=ref_graph.edge_index)
            
            processed.append(graph)
        
        return processed


class TemporalAugmenter:
    """
    Data augmentation for temporal graphs.
    """
    
    def __init__(self, noise_level: float = 0.01, 
                 time_warp_prob: float = 0.1,
                 node_dropout_prob: float = 0.05):
        """
        Initialize augmenter.
        
        Args:
            noise_level: Gaussian noise level
            time_warp_prob: Probability of time warping
            node_dropout_prob: Probability of node dropout
        """
        self.noise_level = noise_level
        self.time_warp_prob = time_warp_prob
        self.node_dropout_prob = node_dropout_prob
    
    def augment(self, graph_sequence: List[Data]) -> List[Data]:
        """
        Apply augmentation to graph sequence.
        
        Args:
            graph_sequence: Input sequence
            
        Returns:
            Augmented sequence
        """
        augmented = []
        
        for graph in graph_sequence:
            # Add Gaussian noise
            if np.random.random() < 0.5:
                noise = torch.randn_like(graph.x) * self.noise_level
                graph.x = graph.x + noise
            
            # Node dropout
            if np.random.random() < self.node_dropout_prob:
                num_nodes = graph.x.shape[0]
                keep_mask = torch.rand(num_nodes) > self.node_dropout_prob
                graph.x = graph.x * keep_mask.unsqueeze(1)
            
            augmented.append(graph)
        
        # Time warping
        if np.random.random() < self.time_warp_prob:
            augmented = self._time_warp(augmented)
        
        return augmented
    
    def _time_warp(self, sequence: List[Data]) -> List[Data]:
        """
        Apply time warping augmentation.
        
        Args:
            sequence: Input sequence
            
        Returns:
            Warped sequence
        """
        # Simple time warping: randomly speed up or slow down
        warp_factor = np.random.uniform(0.8, 1.2)
        
        if warp_factor < 1.0:
            # Speed up: skip some frames
            indices = np.linspace(0, len(sequence) - 1, 
                                 int(len(sequence) * warp_factor)).astype(int)
            warped = [sequence[i] for i in indices]
        else:
            # Slow down: interpolate frames
            warped = sequence.copy()
            # Simple duplication for now
            for i in range(len(sequence) - 1):
                if np.random.random() < (warp_factor - 1.0):
                    warped.insert(i * 2 + 1, sequence[i])
        
        return warped


def create_temporal_dataloaders(data_dir: str, 
                                sequence_length: int = 10,
                                prediction_horizon: int = 5,
                                batch_size: int = 32,
                                train_ratio: float = 0.7,
                                val_ratio: float = 0.15) -> Tuple[TemporalDataLoader, TemporalDataLoader, TemporalDataLoader]:
    """
    Create train/val/test temporal data loaders.
    
    Args:
        data_dir: Data directory
        sequence_length: Input sequence length
        prediction_horizon: Prediction horizon
        batch_size: Batch size
        train_ratio: Training data ratio
        val_ratio: Validation data ratio
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    # Create dataset
    dataset = TemporalGraphDataset(
        data_dir=data_dir,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon
    )
    
    # Load snapshot files
    data_path = Path(data_dir)
    snapshot_files = sorted(data_path.glob('snapshot_*.pt'))
    dataset.load_from_snapshots([str(f) for f in snapshot_files])
    
    # Split dataset
    n = len(dataset)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    
    train_dataset = TemporalGraphDataset(data_dir, sequence_length, prediction_horizon)
    train_dataset.sequences = dataset.sequences[:n_train]
    train_dataset.targets = dataset.targets[:n_train]
    
    val_dataset = TemporalGraphDataset(data_dir, sequence_length, prediction_horizon)
    val_dataset.sequences = dataset.sequences[n_train:n_train + n_val]
    val_dataset.targets = dataset.targets[n_train:n_train + n_val]
    
    test_dataset = TemporalGraphDataset(data_dir, sequence_length, prediction_horizon)
    test_dataset.sequences = dataset.sequences[n_train + n_val:]
    test_dataset.targets = dataset.targets[n_train + n_val:]
    
    # Create loaders
    train_loader = TemporalDataLoader(train_dataset, batch_size, shuffle=True)
    val_loader = TemporalDataLoader(val_dataset, batch_size, shuffle=False)
    test_loader = TemporalDataLoader(test_dataset, batch_size, shuffle=False)
    
    logger.info(f"Created dataloaders: train={len(train_dataset)}, val={len(val_dataset)}, test={len(test_dataset)}")
    
    return train_loader, val_loader, test_loader


if __name__ == '__main__':
    # Example usage
    print("Temporal Data Loader Module")
    
    # Create dummy dataset
    dataset = TemporalGraphDataset(
        data_dir='./data/temporal_graphs',
        sequence_length=10,
        prediction_horizon=5
    )
    
    print(f"Dataset initialized with sequence_length={dataset.sequence_length}")
    print(f"Prediction horizon: {dataset.prediction_horizon}")

# Made with Bob
