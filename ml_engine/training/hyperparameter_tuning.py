"""
Hyperparameter Tuning for AI Risk Constellation System.

This module provides grid search and random search capabilities
with cross-validation for hyperparameter optimization.
"""

import logging
import itertools
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, SubsetRandomSampler

from .training_pipeline import TrainingPipeline, TrainingConfig
from .mlflow_setup import MLflowManager

logger = logging.getLogger(__name__)


@dataclass
class HyperparameterSpace:
    """Definition of hyperparameter search space."""
    learning_rate: List[float]
    batch_size: List[int]
    weight_decay: List[float]
    num_epochs: List[int]
    
    def to_dict(self) -> Dict[str, List[Any]]:
        """Convert to dictionary."""
        return {
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'weight_decay': self.weight_decay,
            'num_epochs': self.num_epochs
        }


class GridSearch:
    """
    Grid search for hyperparameter tuning.
    
    Exhaustively searches all combinations of hyperparameters.
    """
    
    def __init__(self, param_space: HyperparameterSpace, 
                 n_folds: int = 5,
                 mlflow_manager: Optional[MLflowManager] = None):
        """
        Initialize grid search.
        
        Args:
            param_space: Hyperparameter search space
            n_folds: Number of cross-validation folds
            mlflow_manager: MLflow manager for logging
        """
        self.param_space = param_space
        self.n_folds = n_folds
        self.mlflow = mlflow_manager
        
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score = float('inf')
        self.results: List[Dict[str, Any]] = []
    
    def _generate_param_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all parameter combinations.
        
        Returns:
            List of parameter dictionaries
        """
        param_dict = self.param_space.to_dict()
        keys = param_dict.keys()
        values = param_dict.values()
        
        combinations = []
        for combination in itertools.product(*values):
            param_combo = dict(zip(keys, combination))
            combinations.append(param_combo)
        
        logger.info(f"Generated {len(combinations)} parameter combinations")
        return combinations
    
    def _cross_validate(self, 
                       model_fn: Callable,
                       criterion: nn.Module,
                       dataset: Any,
                       params: Dict[str, Any]) -> float:
        """
        Perform k-fold cross-validation.
        
        Args:
            model_fn: Function that creates a model
            criterion: Loss function
            dataset: Full dataset
            params: Hyperparameters to test
            
        Returns:
            Average validation loss across folds
        """
        dataset_size = len(dataset)
        indices = list(range(dataset_size))
        np.random.shuffle(indices)
        
        fold_size = dataset_size // self.n_folds
        fold_scores = []
        
        for fold in range(self.n_folds):
            # Split indices
            val_start = fold * fold_size
            val_end = (fold + 1) * fold_size if fold < self.n_folds - 1 else dataset_size
            
            val_indices = indices[val_start:val_end]
            train_indices = indices[:val_start] + indices[val_end:]
            
            # Create samplers
            train_sampler = SubsetRandomSampler(train_indices)
            val_sampler = SubsetRandomSampler(val_indices)
            
            # Create data loaders
            train_loader = DataLoader(
                dataset,
                batch_size=params['batch_size'],
                sampler=train_sampler
            )
            
            val_loader = DataLoader(
                dataset,
                batch_size=params['batch_size'],
                sampler=val_sampler
            )
            
            # Create model and training config
            model = model_fn()
            config = TrainingConfig(
                model_name=f"cv_fold_{fold}",
                model_type="grid_search",
                batch_size=params['batch_size'],
                learning_rate=params['learning_rate'],
                weight_decay=params['weight_decay'],
                num_epochs=params['num_epochs'],
                patience=5  # Reduced for CV
            )
            
            # Train
            pipeline = TrainingPipeline(config, self.mlflow)
            pipeline.setup_training(model, criterion)
            results = pipeline.train(train_loader, val_loader)
            
            fold_scores.append(results['best_val_loss'])
            
            logger.info(f"Fold {fold+1}/{self.n_folds} - Val Loss: {results['best_val_loss']:.4f}")
        
        avg_score = np.mean(fold_scores)
        std_score = np.std(fold_scores)
        
        logger.info(f"CV Score: {avg_score:.4f} ± {std_score:.4f}")
        
        return float(avg_score)
    
    def search(self,
              model_fn: Callable,
              criterion: nn.Module,
              dataset: Any) -> Dict[str, Any]:
        """
        Perform grid search.
        
        Args:
            model_fn: Function that creates a model
            criterion: Loss function
            dataset: Full dataset
            
        Returns:
            Best parameters found
        """
        logger.info("Starting grid search...")
        
        param_combinations = self._generate_param_combinations()
        
        for idx, params in enumerate(param_combinations):
            logger.info(f"\nTesting combination {idx+1}/{len(param_combinations)}: {params}")
            
            # Cross-validate
            score = self._cross_validate(model_fn, criterion, dataset, params)
            
            # Store results
            result = {
                'params': params,
                'score': score
            }
            self.results.append(result)
            
            # Update best
            if score < self.best_score:
                self.best_score = score
                self.best_params = params
                logger.info(f"New best score: {score:.4f}")
        
        logger.info(f"\nGrid search complete. Best params: {self.best_params}")
        logger.info(f"Best score: {self.best_score:.4f}")
        
        if self.best_params is None:
            raise ValueError("No valid parameters found during grid search")
        
        return self.best_params
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all search results."""
        return sorted(self.results, key=lambda x: x['score'])


class RandomSearch:
    """
    Random search for hyperparameter tuning.
    
    Randomly samples from hyperparameter space.
    """
    
    def __init__(self, param_space: HyperparameterSpace,
                 n_iter: int = 20,
                 n_folds: int = 5,
                 mlflow_manager: Optional[MLflowManager] = None):
        """
        Initialize random search.
        
        Args:
            param_space: Hyperparameter search space
            n_iter: Number of random samples
            n_folds: Number of cross-validation folds
            mlflow_manager: MLflow manager for logging
        """
        self.param_space = param_space
        self.n_iter = n_iter
        self.n_folds = n_folds
        self.mlflow = mlflow_manager
        
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score = float('inf')
        self.results: List[Dict[str, Any]] = []
    
    def _sample_params(self) -> Dict[str, Any]:
        """
        Sample random parameters.
        
        Returns:
            Random parameter dictionary
        """
        param_dict = self.param_space.to_dict()
        
        sampled = {}
        for key, values in param_dict.items():
            sampled[key] = np.random.choice(values)
        
        return sampled
    
    def _cross_validate(self,
                       model_fn: Callable,
                       criterion: nn.Module,
                       dataset: Any,
                       params: Dict[str, Any]) -> float:
        """
        Perform k-fold cross-validation.
        
        Args:
            model_fn: Function that creates a model
            criterion: Loss function
            dataset: Full dataset
            params: Hyperparameters to test
            
        Returns:
            Average validation loss across folds
        """
        dataset_size = len(dataset)
        indices = list(range(dataset_size))
        np.random.shuffle(indices)
        
        fold_size = dataset_size // self.n_folds
        fold_scores = []
        
        for fold in range(self.n_folds):
            val_start = fold * fold_size
            val_end = (fold + 1) * fold_size if fold < self.n_folds - 1 else dataset_size
            
            val_indices = indices[val_start:val_end]
            train_indices = indices[:val_start] + indices[val_end:]
            
            train_sampler = SubsetRandomSampler(train_indices)
            val_sampler = SubsetRandomSampler(val_indices)
            
            train_loader = DataLoader(
                dataset,
                batch_size=params['batch_size'],
                sampler=train_sampler
            )
            
            val_loader = DataLoader(
                dataset,
                batch_size=params['batch_size'],
                sampler=val_sampler
            )
            
            model = model_fn()
            config = TrainingConfig(
                model_name=f"cv_fold_{fold}",
                model_type="random_search",
                batch_size=params['batch_size'],
                learning_rate=params['learning_rate'],
                weight_decay=params['weight_decay'],
                num_epochs=params['num_epochs'],
                patience=5
            )
            
            pipeline = TrainingPipeline(config, self.mlflow)
            pipeline.setup_training(model, criterion)
            results = pipeline.train(train_loader, val_loader)
            
            fold_scores.append(results['best_val_loss'])
        
        avg_score = np.mean(fold_scores)
        return float(avg_score)
    
    def search(self,
              model_fn: Callable,
              criterion: nn.Module,
              dataset: Any) -> Dict[str, Any]:
        """
        Perform random search.
        
        Args:
            model_fn: Function that creates a model
            criterion: Loss function
            dataset: Full dataset
            
        Returns:
            Best parameters found
        """
        logger.info(f"Starting random search with {self.n_iter} iterations...")
        
        for iteration in range(self.n_iter):
            # Sample parameters
            params = self._sample_params()
            
            logger.info(f"\nIteration {iteration+1}/{self.n_iter}: {params}")
            
            # Cross-validate
            score = self._cross_validate(model_fn, criterion, dataset, params)
            
            # Store results
            result = {
                'params': params,
                'score': score
            }
            self.results.append(result)
            
            # Update best
            if score < self.best_score:
                self.best_score = score
                self.best_params = params
                logger.info(f"New best score: {score:.4f}")
        
        logger.info(f"\nRandom search complete. Best params: {self.best_params}")
        logger.info(f"Best score: {self.best_score:.4f}")
        
        if self.best_params is None:
            raise ValueError("No valid parameters found during random search")
        
        return self.best_params
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all search results."""
        return sorted(self.results, key=lambda x: x['score'])


if __name__ == '__main__':
    # Example usage
    print("Hyperparameter Tuning Module")
    
    # Define search space
    param_space = HyperparameterSpace(
        learning_rate=[0.001, 0.0001],
        batch_size=[16, 32],
        weight_decay=[0.0001, 0.00001],
        num_epochs=[50, 100]
    )
    
    print(f"Parameter space: {param_space.to_dict()}")
    
    # Grid search would test 2*2*2*2 = 16 combinations
    # Random search would test n_iter random samples

# Made with Bob
