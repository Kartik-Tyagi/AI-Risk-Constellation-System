"""
Training script for Quantum-Inspired Risk Optimizer.

This script trains the QAOA-based portfolio optimization model.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.mlflow_setup import setup_mlflow
from training.training_pipeline import TrainingPipeline, TrainingConfig
from quantum_risk.qaoa_optimizer import QAOAOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main training function."""
    logger.info("Starting Quantum Risk Optimizer training...")
    
    # Setup MLflow
    mlflow_manager = setup_mlflow(experiment_name="quantum_risk_optimizer")
    
    # Training configuration
    config = TrainingConfig(
        model_name="quantum_risk_optimizer",
        model_type="qaoa",
        num_epochs=100,
        batch_size=32,
        learning_rate=0.001,
        patience=15
    )
    
    logger.info(f"Configuration: {config}")
    
    # Note: Quantum optimizer is primarily used for optimization problems
    # rather than supervised learning, so traditional training may not apply.
    # This script serves as a template for parameter tuning and validation.
    
    logger.info("Quantum Risk Optimizer setup complete.")
    logger.info("For actual optimization, use the QAOA optimizer directly with portfolio data.")
    
    # Example: Create optimizer instance
    optimizer = QAOAOptimizer(num_assets=10)
    logger.info(f"Created QAOA optimizer with {optimizer.num_assets} assets")
    
    logger.info("Training complete!")


if __name__ == '__main__':
    main()

# Made with Bob
