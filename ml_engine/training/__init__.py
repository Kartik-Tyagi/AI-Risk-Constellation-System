"""
Training Pipeline and MLOps Module for AI Risk Constellation System.

This module provides comprehensive training infrastructure including:
- MLflow integration for experiment tracking
- End-to-end training pipeline
- Hyperparameter tuning (grid search and random search)
- Model evaluation and backtesting
- Training scripts for all models
"""

from .mlflow_setup import MLflowManager, MLflowConfig, setup_mlflow
from .training_pipeline import TrainingPipeline, TrainingConfig
from .hyperparameter_tuning import (
    HyperparameterSpace,
    GridSearch,
    RandomSearch
)
from .model_evaluation import (
    ModelEvaluator,
    BacktestFramework,
    EvaluationMetrics
)

__all__ = [
    # MLflow
    'MLflowManager',
    'MLflowConfig',
    'setup_mlflow',
    
    # Training Pipeline
    'TrainingPipeline',
    'TrainingConfig',
    
    # Hyperparameter Tuning
    'HyperparameterSpace',
    'GridSearch',
    'RandomSearch',
    
    # Evaluation
    'ModelEvaluator',
    'BacktestFramework',
    'EvaluationMetrics',
]

# Made with Bob
