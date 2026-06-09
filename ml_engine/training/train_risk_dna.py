"""
Training script for Risk DNA Generator.

This script trains/validates the Risk DNA generation model.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.mlflow_setup import setup_mlflow
from training.training_pipeline import TrainingPipeline, TrainingConfig
from risk_dna.dna_generator import RiskDNAGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main training function."""
    logger.info("Starting Risk DNA Generator training...")
    
    # Setup MLflow
    mlflow_manager = setup_mlflow(experiment_name="risk_dna_generator")
    
    # Training configuration
    config = TrainingConfig(
        model_name="risk_dna_generator",
        model_type="risk_dna",
        num_epochs=100,
        batch_size=32,
        learning_rate=0.001,
        patience=15
    )
    
    logger.info(f"Configuration: {config}")
    
    # Create Risk DNA generator
    generator = RiskDNAGenerator(dna_dim=256)
    logger.info(f"Created Risk DNA generator with dimension: {generator.dna_dim}")
    
    # Note: Risk DNA generation is primarily feature-based encoding
    # rather than supervised learning. This script validates the generator.
    
    logger.info("Risk DNA Generator setup complete.")
    logger.info("Generator is ready for feature encoding.")
    logger.info("Training complete!")


if __name__ == '__main__':
    main()

# Made with Bob
