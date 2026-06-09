"""
Training Loop for Graph Attention Networks
Handles training, validation, and model checkpointing.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import Data, DataLoader
from torch_geometric.loader import NeighborLoader
from typing import Dict, List, Optional, Tuple, Callable
import numpy as np
import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class GATTrainer:
    """
    Trainer for Graph Attention Network models.
    """
    
    def __init__(self,
                 model: nn.Module,
                 device: str = 'cpu',
                 learning_rate: float = 0.001,
                 weight_decay: float = 1e-5,
                 patience: int = 10,
                 checkpoint_dir: str = 'checkpoints'):
        """
        Initialize trainer.
        
        Args:
            model: GAT model to train
            device: Device to train on ('cpu' or 'cuda')
            learning_rate: Learning rate for optimizer
            weight_decay: L2 regularization weight
            patience: Early stopping patience
            checkpoint_dir: Directory to save checkpoints
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.patience = patience
        
        # Create checkpoint directory
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_metrics': [],
            'val_metrics': []
        }
        
        # Best model tracking
        self.best_val_loss = float('inf')
        self.best_epoch = 0
        self.epochs_without_improvement = 0
        
        logger.info(f"Initialized GATTrainer on {device}")
    
    def train_epoch(self,
                   train_loader: DataLoader,
                   loss_fn: Callable,
                   metric_fns: Optional[Dict[str, Callable]] = None) -> Tuple[float, Dict]:
        """
        Train for one epoch.
        
        Args:
            train_loader: DataLoader for training data
            loss_fn: Loss function
            metric_fns: Dictionary of metric functions
            
        Returns:
            Tuple of (average_loss, metrics_dict)
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        # Initialize metrics
        if metric_fns is None:
            metric_fns = {}
        metrics = {name: 0.0 for name in metric_fns.keys()}
        
        for batch in train_loader:
            batch = batch.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            output = self.model(batch.x, batch.edge_index, batch.edge_attr)
            
            # Compute loss
            if hasattr(batch, 'y'):
                loss = loss_fn(output, batch.y)
            else:
                # Self-supervised or reconstruction loss
                loss = loss_fn(output, batch.x)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Accumulate loss
            total_loss += loss.item()
            num_batches += 1
            
            # Compute metrics
            with torch.no_grad():
                for name, metric_fn in metric_fns.items():
                    if hasattr(batch, 'y'):
                        metric_value = metric_fn(output, batch.y)
                    else:
                        metric_value = metric_fn(output, batch.x)
                    metrics[name] += metric_value
        
        # Average metrics
        avg_loss = total_loss / num_batches
        avg_metrics = {name: value / num_batches for name, value in metrics.items()}
        
        return avg_loss, avg_metrics
    
    @torch.no_grad()
    def validate(self,
                val_loader: DataLoader,
                loss_fn: Callable,
                metric_fns: Optional[Dict[str, Callable]] = None) -> Tuple[float, Dict]:
        """
        Validate model.
        
        Args:
            val_loader: DataLoader for validation data
            loss_fn: Loss function
            metric_fns: Dictionary of metric functions
            
        Returns:
            Tuple of (average_loss, metrics_dict)
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        # Initialize metrics
        if metric_fns is None:
            metric_fns = {}
        metrics = {name: 0.0 for name in metric_fns.keys()}
        
        for batch in val_loader:
            batch = batch.to(self.device)
            
            # Forward pass
            output = self.model(batch.x, batch.edge_index, batch.edge_attr)
            
            # Compute loss
            if hasattr(batch, 'y'):
                loss = loss_fn(output, batch.y)
            else:
                loss = loss_fn(output, batch.x)
            
            total_loss += loss.item()
            num_batches += 1
            
            # Compute metrics
            for name, metric_fn in metric_fns.items():
                if hasattr(batch, 'y'):
                    metric_value = metric_fn(output, batch.y)
                else:
                    metric_value = metric_fn(output, batch.x)
                metrics[name] += metric_value
        
        # Average metrics
        avg_loss = total_loss / num_batches
        avg_metrics = {name: value / num_batches for name, value in metrics.items()}
        
        return avg_loss, avg_metrics
    
    def fit(self,
            train_loader: DataLoader,
            val_loader: DataLoader,
            loss_fn: Callable,
            num_epochs: int = 100,
            metric_fns: Optional[Dict[str, Callable]] = None,
            verbose: bool = True) -> Dict:
        """
        Train model for multiple epochs.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            loss_fn: Loss function
            num_epochs: Number of epochs to train
            metric_fns: Dictionary of metric functions
            verbose: Whether to print progress
            
        Returns:
            Training history dictionary
        """
        logger.info(f"Starting training for {num_epochs} epochs")
        
        for epoch in range(num_epochs):
            # Train
            train_loss, train_metrics = self.train_epoch(
                train_loader, loss_fn, metric_fns
            )
            
            # Validate
            val_loss, val_metrics = self.validate(
                val_loader, loss_fn, metric_fns
            )
            
            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_metrics'].append(train_metrics)
            self.history['val_metrics'].append(val_metrics)
            
            # Check for improvement
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_epoch = epoch
                self.epochs_without_improvement = 0
                
                # Save best model
                self.save_checkpoint('best_model.pt', epoch, val_loss)
                
                if verbose:
                    logger.info(f"Epoch {epoch+1}: New best model (val_loss={val_loss:.4f})")
            else:
                self.epochs_without_improvement += 1
            
            # Print progress
            if verbose and (epoch + 1) % 10 == 0:
                metrics_str = ', '.join([f"{k}={v:.4f}" for k, v in train_metrics.items()])
                val_metrics_str = ', '.join([f"{k}={v:.4f}" for k, v in val_metrics.items()])
                
                logger.info(
                    f"Epoch {epoch+1}/{num_epochs}: "
                    f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}"
                )
                if metrics_str:
                    logger.info(f"  Train metrics: {metrics_str}")
                if val_metrics_str:
                    logger.info(f"  Val metrics: {val_metrics_str}")
            
            # Early stopping
            if self.epochs_without_improvement >= self.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Load best model
        self.load_checkpoint('best_model.pt')
        
        logger.info(f"Training complete. Best epoch: {self.best_epoch+1}")
        
        return self.history
    
    def save_checkpoint(self, filename: str, epoch: int, val_loss: float):
        """
        Save model checkpoint.
        
        Args:
            filename: Checkpoint filename
            epoch: Current epoch
            val_loss: Validation loss
        """
        checkpoint_path = self.checkpoint_dir / filename
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'history': self.history,
            'best_val_loss': self.best_val_loss,
            'best_epoch': self.best_epoch
        }
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint to {checkpoint_path}")
    
    def load_checkpoint(self, filename: str):
        """
        Load model checkpoint.
        
        Args:
            filename: Checkpoint filename
        """
        checkpoint_path = self.checkpoint_dir / filename
        
        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint {checkpoint_path} not found")
            return
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        self.best_val_loss = checkpoint['best_val_loss']
        self.best_epoch = checkpoint['best_epoch']
        
        logger.info(f"Loaded checkpoint from {checkpoint_path}")
    
    def save_history(self, filename: str = 'training_history.json'):
        """
        Save training history to JSON.
        
        Args:
            filename: Output filename
        """
        history_path = self.checkpoint_dir / filename
        
        # Convert numpy arrays to lists for JSON serialization
        history_json = {}
        for key, value in self.history.items():
            if isinstance(value, list):
                history_json[key] = [
                    {k: float(v) for k, v in item.items()} if isinstance(item, dict) else float(item)
                    for item in value
                ]
            else:
                history_json[key] = value
        
        with open(history_path, 'w') as f:
            json.dump(history_json, f, indent=2)
        
        logger.info(f"Saved training history to {history_path}")


class RiskPropagationTrainer(GATTrainer):
    """
    Specialized trainer for risk propagation models.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def train_epoch(self,
                   train_loader: DataLoader,
                   loss_fn: Optional[Callable] = None,
                   metric_fns: Optional[Dict[str, Callable]] = None) -> Tuple[float, Dict]:
        """
        Train epoch with risk-specific loss.
        
        Args:
            train_loader: Training data loader
            loss_fn: Loss function (uses default if None)
            metric_fns: Metric functions
            
        Returns:
            Tuple of (loss, metrics)
        """
        # Default risk propagation loss
        if loss_fn is None:
            loss_fn = self._risk_propagation_loss
        
        # Default metrics
        if metric_fns is None:
            metric_fns = {
                'mae': self._mean_absolute_error,
                'cascade_accuracy': self._cascade_accuracy
            }
        
        return super().train_epoch(train_loader, loss_fn, metric_fns)
    
    def _risk_propagation_loss(self, output: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Combined loss for risk propagation.
        
        Args:
            output: Model output (risk_scores, cascade_probs)
            target: Target values
            
        Returns:
            Combined loss
        """
        risk_scores, cascade_probs = output
        target_risks, target_cascades = target
        
        # Risk score loss (MSE)
        risk_loss = nn.functional.mse_loss(risk_scores, target_risks)
        
        # Cascade probability loss (BCE)
        cascade_loss = nn.functional.binary_cross_entropy(
            cascade_probs, target_cascades
        )
        
        # Combined loss
        total_loss = risk_loss + 0.5 * cascade_loss
        
        return total_loss
    
    def _mean_absolute_error(self, output: torch.Tensor, target: torch.Tensor) -> float:
        """
        Compute MAE for risk scores.
        
        Args:
            output: Model output
            target: Target values
            
        Returns:
            MAE value
        """
        risk_scores, _ = output
        target_risks, _ = target
        
        mae = torch.mean(torch.abs(risk_scores - target_risks))
        return mae.item()
    
    def _cascade_accuracy(self, output: torch.Tensor, target: torch.Tensor) -> float:
        """
        Compute accuracy for cascade prediction.
        
        Args:
            output: Model output
            target: Target values
            
        Returns:
            Accuracy value
        """
        _, cascade_probs = output
        _, target_cascades = target
        
        predictions = (cascade_probs > 0.5).float()
        accuracy = torch.mean((predictions == target_cascades).float())
        
        return accuracy.item()


def create_data_loaders(data_list: List[Data],
                       train_ratio: float = 0.7,
                       val_ratio: float = 0.15,
                       batch_size: int = 32,
                       shuffle: bool = True) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create train/val/test data loaders.
    
    Args:
        data_list: List of graph Data objects
        train_ratio: Ratio of training data
        val_ratio: Ratio of validation data
        batch_size: Batch size
        shuffle: Whether to shuffle data
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    # Split data
    n = len(data_list)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    
    if shuffle:
        indices = np.random.permutation(n)
        data_list = [data_list[i] for i in indices]
    
    train_data = data_list[:n_train]
    val_data = data_list[n_train:n_train + n_val]
    test_data = data_list[n_train + n_val:]
    
    # Create loaders
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=shuffle)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    
    logger.info(f"Created data loaders: train={len(train_data)}, val={len(val_data)}, test={len(test_data)}")
    
    return train_loader, val_loader, test_loader


if __name__ == '__main__':
    # Example usage
    from .gat_model import GAT
    
    # Create dummy model
    model = GAT(
        in_channels=10,
        hidden_channels=32,
        out_channels=1,
        heads=4,
        num_layers=2
    )
    
    # Create trainer
    trainer = GATTrainer(
        model=model,
        device='cpu',
        learning_rate=0.001,
        patience=10
    )
    
    print("Trainer initialized successfully")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters())}")

# Made with Bob
