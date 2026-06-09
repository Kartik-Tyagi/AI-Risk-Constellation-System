"""
Training Script for Temporal Graph Neural Networks
Trains temporal GNN models for risk cascade prediction.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import sys
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_networks.temporal_gnn import TemporalGNN, TemporalGRUGNN
from graph_networks.risk_cascade_predictor import RiskCascadePredictor
from graph_networks.temporal_data_loader import (
    create_temporal_dataloaders, MissingDataHandler, TemporalAugmenter
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemporalGNNTrainer:
    """
    Trainer for Temporal GNN models.
    """
    
    def __init__(self, model: nn.Module, device: str = 'cpu',
                 learning_rate: float = 0.001, weight_decay: float = 1e-5):
        """
        Initialize trainer.
        
        Args:
            model: Temporal GNN model
            device: Device to train on
            learning_rate: Learning rate
            weight_decay: Weight decay
        """
        self.model = model.to(device)
        self.device = device
        
        self.optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5
        )
        
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_mae': [],
            'val_mae': []
        }
        
        self.best_val_loss = float('inf')
        self.best_epoch = 0
        
        logger.info(f"Initialized TemporalGNNTrainer on {device}")
    
    def train_epoch(self, train_loader) -> Dict[str, float]:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            
        Returns:
            Dictionary of metrics
        """
        self.model.train()
        total_loss = 0.0
        total_mae = 0.0
        num_batches = 0
        
        for batch_sequences, batch_targets in train_loader:
            # Move to device
            x_sequence = [x.to(self.device) for x in batch_sequences]
            edge_index_sequence = [x.edge_index.to(self.device) for x in batch_sequences]
            
            # Extract node features
            x_features = [x.x for x in x_sequence]
            
            # Forward pass
            self.optimizer.zero_grad()
            predictions, _ = self.model(x_features, edge_index_sequence)
            
            # Compute loss
            target_features = torch.stack([t.x for t in batch_targets], dim=1)
            loss = nn.functional.mse_loss(predictions, target_features)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            # Metrics
            total_loss += loss.item()
            mae = torch.mean(torch.abs(predictions - target_features))
            total_mae += mae.item()
            num_batches += 1
        
        return {
            'loss': total_loss / num_batches,
            'mae': total_mae / num_batches
        }
    
    @torch.no_grad()
    def validate(self, val_loader) -> Dict[str, float]:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
            
        Returns:
            Dictionary of metrics
        """
        self.model.eval()
        total_loss = 0.0
        total_mae = 0.0
        num_batches = 0
        
        for batch_sequences, batch_targets in val_loader:
            x_sequence = [x.to(self.device) for x in batch_sequences]
            edge_index_sequence = [x.edge_index.to(self.device) for x in batch_sequences]
            
            x_features = [x.x for x in x_sequence]
            
            predictions, _ = self.model(x_features, edge_index_sequence)
            
            target_features = torch.stack([t.x for t in batch_targets], dim=1)
            loss = nn.functional.mse_loss(predictions, target_features)
            
            total_loss += loss.item()
            mae = torch.mean(torch.abs(predictions - target_features))
            total_mae += mae.item()
            num_batches += 1
        
        return {
            'loss': total_loss / num_batches,
            'mae': total_mae / num_batches
        }
    
    def fit(self, train_loader, val_loader, num_epochs: int = 100,
            checkpoint_dir: str = 'checkpoints') -> Dict:
        """
        Train model.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of epochs
            checkpoint_dir: Directory to save checkpoints
            
        Returns:
            Training history
        """
        checkpoint_path = Path(checkpoint_dir)
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting training for {num_epochs} epochs")
        
        for epoch in range(num_epochs):
            # Train
            train_metrics = self.train_epoch(train_loader)
            
            # Validate
            val_metrics = self.validate(val_loader)
            
            # Update history
            self.history['train_loss'].append(train_metrics['loss'])
            self.history['val_loss'].append(val_metrics['loss'])
            self.history['train_mae'].append(train_metrics['mae'])
            self.history['val_mae'].append(val_metrics['mae'])
            
            # Learning rate scheduling
            self.scheduler.step(val_metrics['loss'])
            
            # Logging
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{num_epochs}: "
                    f"train_loss={train_metrics['loss']:.4f}, "
                    f"val_loss={val_metrics['loss']:.4f}, "
                    f"train_mae={train_metrics['mae']:.4f}, "
                    f"val_mae={val_metrics['mae']:.4f}"
                )
            
            # Save best model
            if val_metrics['loss'] < self.best_val_loss:
                self.best_val_loss = val_metrics['loss']
                self.best_epoch = epoch
                
                checkpoint = {
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_metrics['loss'],
                    'history': self.history
                }
                
                torch.save(checkpoint, checkpoint_path / 'best_model.pt')
                logger.info(f"Saved best model at epoch {epoch+1}")
        
        logger.info(f"Training complete. Best epoch: {self.best_epoch+1}")
        
        return self.history
    
    def save_history(self, filepath: str):
        """Save training history to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=2)
        logger.info(f"Saved training history to {filepath}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train Temporal GNN')
    
    parser.add_argument('--data_dir', type=str, required=True,
                       help='Directory containing temporal graph data')
    parser.add_argument('--model_type', type=str, default='temporal_gnn',
                       choices=['temporal_gnn', 'temporal_gru_gnn', 'cascade_predictor'],
                       help='Type of model to train')
    parser.add_argument('--node_feature_dim', type=int, default=20,
                       help='Node feature dimension')
    parser.add_argument('--edge_feature_dim', type=int, default=5,
                       help='Edge feature dimension')
    parser.add_argument('--hidden_dim', type=int, default=128,
                       help='Hidden dimension')
    parser.add_argument('--output_dim', type=int, default=64,
                       help='Output dimension')
    parser.add_argument('--num_layers', type=int, default=3,
                       help='Number of layers')
    parser.add_argument('--heads', type=int, default=4,
                       help='Number of attention heads')
    parser.add_argument('--sequence_length', type=int, default=10,
                       help='Input sequence length')
    parser.add_argument('--prediction_horizon', type=int, default=5,
                       help='Prediction horizon')
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--num_epochs', type=int, default=100,
                       help='Number of epochs')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                       help='Learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-5,
                       help='Weight decay')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='Device to train on')
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                       help='Checkpoint directory')
    parser.add_argument('--augment', action='store_true',
                       help='Use data augmentation')
    parser.add_argument('--handle_missing', action='store_true',
                       help='Handle missing data')
    
    return parser.parse_args()


def create_model(args):
    """Create model based on arguments."""
    if args.model_type == 'temporal_gnn':
        model = TemporalGNN(
            node_feature_dim=args.node_feature_dim,
            edge_feature_dim=args.edge_feature_dim,
            hidden_dim=args.hidden_dim,
            output_dim=args.output_dim,
            num_layers=args.num_layers,
            heads=args.heads,
            prediction_horizon=args.prediction_horizon
        )
    elif args.model_type == 'temporal_gru_gnn':
        model = TemporalGRUGNN(
            node_feature_dim=args.node_feature_dim,
            hidden_dim=args.hidden_dim,
            output_dim=args.output_dim,
            num_layers=args.num_layers,
            heads=args.heads
        )
    elif args.model_type == 'cascade_predictor':
        model = RiskCascadePredictor(
            node_feature_dim=args.node_feature_dim,
            temporal_feature_dim=args.hidden_dim,
            hidden_dim=args.hidden_dim,
            num_cascade_steps=args.prediction_horizon
        )
    else:
        raise ValueError(f"Unknown model type: {args.model_type}")
    
    return model


def main():
    """Main training function."""
    args = parse_args()
    
    logger.info("="*70)
    logger.info("Temporal GNN Training")
    logger.info("="*70)
    logger.info(f"Model type: {args.model_type}")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Device: {args.device}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Sequence length: {args.sequence_length}")
    logger.info(f"Prediction horizon: {args.prediction_horizon}")
    logger.info("="*70)
    
    # Create data loaders
    logger.info("Creating data loaders...")
    train_loader, val_loader, test_loader = create_temporal_dataloaders(
        data_dir=args.data_dir,
        sequence_length=args.sequence_length,
        prediction_horizon=args.prediction_horizon,
        batch_size=args.batch_size
    )

    if len(train_loader.dataset) == 0:
        logger.warning(
            f"No temporal graph snapshots found in '{args.data_dir}'. "
            "Training requires pre-processed 'snapshot_*.pt' files. "
            "Skipping Temporal GNN training."
        )
        return

    # Create model
    logger.info("Creating model...")
    model = create_model(args)
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    
    # Create trainer
    trainer = TemporalGNNTrainer(
        model=model,
        device=args.device,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay
    )
    
    # Train
    logger.info("Starting training...")
    history = trainer.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=args.num_epochs,
        checkpoint_dir=args.checkpoint_dir
    )
    
    # Save history
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    history_file = Path(args.checkpoint_dir) / f'history_{timestamp}.json'
    trainer.save_history(str(history_file))
    
    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_metrics = trainer.validate(test_loader)
    logger.info(f"Test loss: {test_metrics['loss']:.4f}")
    logger.info(f"Test MAE: {test_metrics['mae']:.4f}")
    
    logger.info("Training complete!")


if __name__ == '__main__':
    main()

# Made with Bob
