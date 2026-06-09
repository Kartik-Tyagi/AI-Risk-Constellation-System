"""
End-to-End Training Pipeline for AI Risk Constellation System.

This module provides a complete training pipeline with data loading,
preprocessing, training, validation, and model registration.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
import numpy as np

from .mlflow_setup import MLflowManager, setup_mlflow

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for training pipeline."""
    # Model parameters
    model_name: str
    model_type: str
    
    # Training parameters
    batch_size: int = 32
    num_epochs: int = 100
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    
    # Data parameters
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15
    
    # Device
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Early stopping
    patience: int = 10
    min_delta: float = 0.001
    
    # Checkpointing
    save_best_only: bool = True
    checkpoint_dir: Optional[str] = None
    
    # MLflow
    experiment_name: str = "risk_constellation"
    run_name: Optional[str] = None


class TrainingPipeline:
    """
    End-to-end training pipeline with MLflow integration.
    
    Handles data loading, model training, validation, and model registration.
    """
    
    def __init__(self, config: TrainingConfig, mlflow_manager: Optional[MLflowManager] = None):
        """
        Initialize training pipeline.
        
        Args:
            config: Training configuration
            mlflow_manager: MLflow manager (creates new if None)
        """
        self.config = config
        self.mlflow = mlflow_manager or setup_mlflow(config.experiment_name)
        
        # Setup checkpoint directory
        if config.checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent.parent.parent / "checkpoints" / config.model_name
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            self.config.checkpoint_dir = str(checkpoint_dir)
        
        # Training state
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.criterion: Optional[nn.Module] = None
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        
        logger.info(f"Initialized training pipeline for {config.model_name}")
    
    def prepare_data(self, dataset: Dataset) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Split dataset and create data loaders.
        
        Args:
            dataset: Full dataset
            
        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        # Calculate split sizes
        total_size = len(dataset)
        train_size = int(total_size * self.config.train_split)
        val_size = int(total_size * self.config.val_split)
        test_size = total_size - train_size - val_size
        
        # Split dataset
        train_dataset, val_dataset, test_dataset = random_split(
            dataset,
            [train_size, val_size, test_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )
        
        logger.info(f"Data split - Train: {train_size}, Val: {val_size}, Test: {test_size}")
        
        return train_loader, val_loader, test_loader
    
    def setup_training(self, model: nn.Module, criterion: nn.Module):
        """
        Setup model, optimizer, and loss function.
        
        Args:
            model: Model to train
            criterion: Loss function
        """
        self.model = model.to(self.config.device)
        self.criterion = criterion
        
        # Setup optimizer
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        logger.info(msg=f"Setup training on device: {self.config.device}")
    
    def train_epoch(self, train_loader: DataLoader) -> Dict[str, float]:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            
        Returns:
            Dictionary of training metrics
        """
        if self.model is None or self.optimizer is None or self.criterion is None:
            raise ValueError("Model, optimizer, and criterion must be set up before training")
        
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            if isinstance(batch, (list, tuple)):
                batch = [b.to(self.config.device) if isinstance(b, torch.Tensor) else b for b in batch]
            else:
                batch = batch.to(self.config.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            
            # Handle different batch formats
            if isinstance(batch, (list, tuple)) and len(batch) == 2:
                inputs, targets = batch
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
            else:
                # For unsupervised or custom formats
                outputs = self.model(batch)
                loss = self.criterion(outputs, batch)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        return {'train_loss': avg_loss}
    
    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """
        Validate the model.
        
        Args:
            val_loader: Validation data loader
            
        Returns:
            Dictionary of validation metrics
        """
        if self.model is None or self.criterion is None:
            raise ValueError("Model and criterion must be set up before validation")
        
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in val_loader:
                # Move batch to device
                if isinstance(batch, (list, tuple)):
                    batch = [b.to(self.config.device) if isinstance(b, torch.Tensor) else b for b in batch]
                else:
                    batch = batch.to(self.config.device)
                
                # Forward pass
                if isinstance(batch, (list, tuple)) and len(batch) == 2:
                    inputs, targets = batch
                    outputs = self.model(inputs)
                    loss = self.criterion(outputs, targets)
                else:
                    outputs = self.model(batch)
                    loss = self.criterion(outputs, batch)
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        return {'val_loss': avg_loss}
    
    def check_early_stopping(self, val_loss: float) -> bool:
        """
        Check if training should stop early.
        
        Args:
            val_loss: Current validation loss
            
        Returns:
            True if should stop, False otherwise
        """
        if val_loss < self.best_val_loss - self.config.min_delta:
            self.best_val_loss = val_loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            if self.patience_counter >= self.config.patience:
                logger.info(f"Early stopping triggered after {self.patience_counter} epochs")
                return True
            return False
    
    def save_checkpoint(self, epoch: int, metrics: Dict[str, float], is_best: bool = False):
        """
        Save model checkpoint.
        
        Args:
            epoch: Current epoch
            metrics: Current metrics
            is_best: Whether this is the best model so far
        """
        if self.model is None or self.optimizer is None or self.config.checkpoint_dir is None:
            raise ValueError("Model, optimizer, and checkpoint_dir must be set up")
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metrics': metrics,
            'config': self.config
        }
        
        # Save checkpoint
        checkpoint_path = Path(self.config.checkpoint_dir) / f"checkpoint_epoch_{epoch}.pt"
        torch.save(checkpoint, checkpoint_path)
        
        # Save best model
        if is_best:
            best_path = Path(self.config.checkpoint_dir) / "best_model.pt"
            torch.save(checkpoint, best_path)
            logger.info(f"Saved best model at epoch {epoch}")
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, Any]:
        """
        Run full training loop.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            
        Returns:
            Training results dictionary
        """
        logger.info(f"Starting training for {self.config.num_epochs} epochs")
        
        # Start MLflow run
        with self.mlflow.start_run(run_name=self.config.run_name):
            # Log configuration
            self.mlflow.log_params({
                'model_name': self.config.model_name,
                'model_type': self.config.model_type,
                'batch_size': self.config.batch_size,
                'learning_rate': self.config.learning_rate,
                'num_epochs': self.config.num_epochs,
                'device': self.config.device
            })
            
            start_time = time.time()
            epoch = 0
            
            for epoch in range(self.config.num_epochs):
                epoch_start = time.time()
                
                # Train
                train_metrics = self.train_epoch(train_loader)
                
                # Validate
                val_metrics = self.validate(val_loader)
                
                # Combine metrics
                metrics = {**train_metrics, **val_metrics}
                metrics['epoch_time'] = time.time() - epoch_start
                
                # Log to MLflow
                self.mlflow.log_metrics(metrics, step=epoch)
                
                # Log progress
                logger.info(
                    f"Epoch {epoch+1}/{self.config.num_epochs} - "
                    f"Train Loss: {train_metrics['train_loss']:.4f}, "
                    f"Val Loss: {val_metrics['val_loss']:.4f}"
                )
                
                # Check if best model
                is_best = val_metrics['val_loss'] < self.best_val_loss
                
                # Save checkpoint
                if not self.config.save_best_only or is_best:
                    self.save_checkpoint(epoch, metrics, is_best)
                
                # Early stopping
                if self.check_early_stopping(val_metrics['val_loss']):
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
            
            total_time = time.time() - start_time
            
            # Log final metrics
            self.mlflow.log_metrics({
                'total_training_time': total_time,
                'best_val_loss': self.best_val_loss
            })
            
            # Log best model
            if self.config.checkpoint_dir is None:
                raise ValueError("Checkpoint directory not set")
            
            best_model_path = Path(self.config.checkpoint_dir) / "best_model.pt"
            if best_model_path.exists():
                self.mlflow.log_model(
                    self.model,
                    artifact_path="model",
                    registered_model_name=self.config.model_name
                )
            
            results = {
                'best_val_loss': self.best_val_loss,
                'total_time': total_time,
                'num_epochs_trained': (epoch + 1) if 'epoch' in locals() else 0
            }
            
            logger.info(f"Training complete. Best val loss: {self.best_val_loss:.4f}")
            
            return results
    
    def evaluate(self, test_loader: DataLoader) -> Dict[str, float]:
        """
        Evaluate model on test set.
        
        Args:
            test_loader: Test data loader
            
        Returns:
            Test metrics
        """
        if self.model is None or self.criterion is None:
            raise ValueError("Model and criterion must be set up before evaluation")
        
        logger.info("Evaluating on test set...")
        
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in test_loader:
                if isinstance(batch, (list, tuple)):
                    batch = [b.to(self.config.device) if isinstance(b, torch.Tensor) else b for b in batch]
                else:
                    batch = batch.to(self.config.device)
                
                if isinstance(batch, (list, tuple)) and len(batch) == 2:
                    inputs, targets = batch
                    outputs = self.model(inputs)
                    loss = self.criterion(outputs, targets)
                else:
                    outputs = self.model(batch)
                    loss = self.criterion(outputs, batch)
                
                total_loss += loss.item()
                num_batches += 1
        
        test_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        logger.info(f"Test Loss: {test_loss:.4f}")
        
        return {'test_loss': test_loss}


if __name__ == '__main__':
    # Example usage
    print("Training Pipeline Module")
    
    # Create dummy config
    config = TrainingConfig(
        model_name="test_model",
        model_type="gat",
        num_epochs=10,
        batch_size=32
    )
    
    print(f"Config: {config}")
    print(f"Device: {config.device}")

# Made with Bob
