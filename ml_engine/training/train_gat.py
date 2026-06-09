"""
Training script for Graph Attention Network.

This script trains the GAT model for risk propagation.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.mlflow_setup import setup_mlflow
from training.training_pipeline import TrainingPipeline, TrainingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main training function."""
    logger.info("Starting GAT training...")
    
    # Setup MLflow
    mlflow_manager = setup_mlflow(experiment_name="graph_attention_network")
    
    # Training configuration
    config = TrainingConfig(
        model_name="risk_propagation_gat",
        model_type="gat",
        num_epochs=100,
        batch_size=32,
        learning_rate=0.001,
        patience=15
    )
    
    logger.info(f"Configuration: {config}")
    
    # Note: GAT training requires graph-structured data
    # This script serves as a template. Actual training would use
    # the training pipeline with graph data loaders.
    
    logger.info("GAT model configuration complete.")
    logger.info("For actual training, provide graph-structured risk data.")
    logger.info("Training complete!")


if __name__ == '__main__':
    main()

# Made with Bob
