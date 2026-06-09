"""
Model Evaluation and Backtesting Framework for AI Risk Constellation System.

This module provides comprehensive evaluation metrics and backtesting
capabilities for risk prediction models.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""
    # Loss metrics
    mse: float
    mae: float
    rmse: float
    
    # Classification metrics (if applicable)
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Risk-specific metrics
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    hit_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        result = {
            'mse': self.mse,
            'mae': self.mae,
            'rmse': self.rmse
        }
        
        if self.accuracy is not None:
            result['accuracy'] = self.accuracy
        if self.precision is not None:
            result['precision'] = self.precision
        if self.recall is not None:
            result['recall'] = self.recall
        if self.f1_score is not None:
            result['f1_score'] = self.f1_score
        if self.sharpe_ratio is not None:
            result['sharpe_ratio'] = self.sharpe_ratio
        if self.max_drawdown is not None:
            result['max_drawdown'] = self.max_drawdown
        if self.hit_rate is not None:
            result['hit_rate'] = self.hit_rate
        
        return result


class ModelEvaluator:
    """
    Comprehensive model evaluation framework.
    
    Provides various metrics and visualization tools for model assessment.
    """
    
    def __init__(self, model: nn.Module, device: str = 'cpu'):
        """
        Initialize evaluator.
        
        Args:
            model: Model to evaluate
            device: Device to use for evaluation
        """
        self.model = model.to(device)
        self.device = device
        self.model.eval()
    
    def evaluate(self, data_loader: DataLoader, 
                criterion: Optional[nn.Module] = None) -> EvaluationMetrics:
        """
        Evaluate model on a dataset.
        
        Args:
            data_loader: Data loader for evaluation
            criterion: Loss function (optional)
            
        Returns:
            Evaluation metrics
        """
        all_predictions = []
        all_targets = []
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in data_loader:
                # Handle different batch formats
                if isinstance(batch, (list, tuple)) and len(batch) == 2:
                    inputs, targets = batch
                    inputs = inputs.to(self.device)
                    targets = targets.to(self.device)
                    
                    outputs = self.model(inputs)
                    
                    if criterion:
                        loss = criterion(outputs, targets)
                        total_loss += loss.item()
                    
                    all_predictions.append(outputs.cpu().numpy())
                    all_targets.append(targets.cpu().numpy())
                    num_batches += 1
        
        # Concatenate all predictions and targets
        predictions = np.concatenate(all_predictions, axis=0)
        targets = np.concatenate(all_targets, axis=0)
        
        # Calculate metrics
        mse = float(np.mean((predictions - targets) ** 2))
        mae = float(np.mean(np.abs(predictions - targets)))
        rmse = float(np.sqrt(mse))
        
        metrics = EvaluationMetrics(
            mse=mse,
            mae=mae,
            rmse=rmse
        )
        
        # Calculate classification metrics if binary
        if predictions.shape[-1] == 1 or len(predictions.shape) == 1:
            # Binary classification
            pred_binary = (predictions > 0.5).astype(int)
            target_binary = (targets > 0.5).astype(int)
            
            metrics.accuracy = float(np.mean(pred_binary == target_binary))
            
            # Precision, recall, F1
            tp = np.sum((pred_binary == 1) & (target_binary == 1))
            fp = np.sum((pred_binary == 1) & (target_binary == 0))
            fn = np.sum((pred_binary == 0) & (target_binary == 1))
            
            metrics.precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            metrics.recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            
            if metrics.precision + metrics.recall > 0:
                metrics.f1_score = float(
                    2 * (metrics.precision * metrics.recall) / 
                    (metrics.precision + metrics.recall)
                )
            else:
                metrics.f1_score = 0.0
        
        logger.info(f"Evaluation complete - MSE: {mse:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
        
        return metrics
    
    def calculate_risk_metrics(self, predictions: np.ndarray, 
                              targets: np.ndarray,
                              returns: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Calculate risk-specific metrics.
        
        Args:
            predictions: Model predictions
            targets: True values
            returns: Asset returns (optional)
            
        Returns:
            Dictionary of risk metrics
        """
        metrics = {}
        
        # Hit rate (percentage of correct direction predictions)
        if len(predictions) > 1:
            pred_direction = np.sign(np.diff(predictions.flatten()))
            target_direction = np.sign(np.diff(targets.flatten()))
            hit_rate = np.mean(pred_direction == target_direction)
            metrics['hit_rate'] = float(hit_rate)
        
        # If returns are provided, calculate Sharpe ratio and max drawdown
        if returns is not None:
            # Sharpe ratio
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
                metrics['sharpe_ratio'] = float(sharpe)
            
            # Maximum drawdown
            cumulative = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = cumulative - running_max
            max_dd = np.min(drawdown)
            metrics['max_drawdown'] = float(max_dd)
        
        return metrics
    
    def plot_predictions(self, predictions: np.ndarray, targets: np.ndarray,
                        save_path: Optional[str] = None):
        """
        Plot predictions vs targets.
        
        Args:
            predictions: Model predictions
            targets: True values
            save_path: Path to save plot
        """
        plt.figure(figsize=(12, 6))
        
        # Flatten if needed
        pred_flat = predictions.flatten()
        target_flat = targets.flatten()
        
        # Plot
        plt.subplot(1, 2, 1)
        plt.scatter(target_flat, pred_flat, alpha=0.5)
        plt.plot([target_flat.min(), target_flat.max()], 
                [target_flat.min(), target_flat.max()], 
                'r--', lw=2)
        plt.xlabel('True Values')
        plt.ylabel('Predictions')
        plt.title('Predictions vs True Values')
        plt.grid(True)
        
        # Residuals
        plt.subplot(1, 2, 2)
        residuals = pred_flat - target_flat
        plt.hist(residuals, bins=50, edgecolor='black')
        plt.xlabel('Residuals')
        plt.ylabel('Frequency')
        plt.title('Residual Distribution')
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_time_series(self, predictions: np.ndarray, targets: np.ndarray,
                        save_path: Optional[str] = None):
        """
        Plot time series predictions.
        
        Args:
            predictions: Model predictions
            targets: True values
            save_path: Path to save plot
        """
        plt.figure(figsize=(14, 6))
        
        pred_flat = predictions.flatten()
        target_flat = targets.flatten()
        
        plt.plot(target_flat, label='True Values', linewidth=2)
        plt.plot(pred_flat, label='Predictions', linewidth=2, alpha=0.7)
        plt.xlabel('Time Step')
        plt.ylabel('Value')
        plt.title('Time Series Predictions')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved time series plot to {save_path}")
        else:
            plt.show()
        
        plt.close()


class BacktestFramework:
    """
    Backtesting framework for risk models.
    
    Simulates model performance on historical data.
    """
    
    def __init__(self, model: nn.Module, device: str = 'cpu'):
        """
        Initialize backtest framework.
        
        Args:
            model: Model to backtest
            device: Device to use
        """
        self.model = model.to(device)
        self.device = device
        self.model.eval()
    
    def run_backtest(self, data_loader: DataLoader,
                    initial_capital: float = 100000.0) -> Dict[str, Any]:
        """
        Run backtest simulation.
        
        Args:
            data_loader: Historical data
            initial_capital: Starting capital
            
        Returns:
            Backtest results
        """
        logger.info("Running backtest...")
        
        portfolio_values = [initial_capital]
        predictions_list = []
        targets_list = []
        
        with torch.no_grad():
            for batch in data_loader:
                if isinstance(batch, (list, tuple)) and len(batch) == 2:
                    inputs, targets = batch
                    inputs = inputs.to(self.device)
                    
                    # Get predictions
                    predictions = self.model(inputs)
                    
                    predictions_list.append(predictions.cpu().numpy())
                    targets_list.append(targets.numpy())
        
        # Concatenate results
        all_predictions = np.concatenate(predictions_list, axis=0)
        all_targets = np.concatenate(targets_list, axis=0)
        
        # Simulate trading based on predictions
        # Simple strategy: go long if prediction > threshold
        threshold = 0.5
        returns = []
        
        for i in range(len(all_predictions) - 1):
            pred = all_predictions[i].flatten()[0]
            actual_return = all_targets[i+1].flatten()[0] - all_targets[i].flatten()[0]
            
            # Position based on prediction
            if pred > threshold:
                position = 1.0  # Long
            else:
                position = 0.0  # No position
            
            # Calculate return
            period_return = position * actual_return
            returns.append(period_return)
            
            # Update portfolio value
            new_value = portfolio_values[-1] * (1 + period_return)
            portfolio_values.append(new_value)
        
        returns = np.array(returns)
        
        # Calculate metrics
        total_return = (portfolio_values[-1] - initial_capital) / initial_capital
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        
        # Maximum drawdown
        portfolio_array = np.array(portfolio_values)
        running_max = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        results = {
            'initial_capital': initial_capital,
            'final_value': portfolio_values[-1],
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'num_trades': len(returns),
            'portfolio_values': portfolio_values,
            'returns': returns.tolist()
        }
        
        logger.info(f"Backtest complete - Total Return: {total_return*100:.2f}%, "
                   f"Sharpe: {sharpe_ratio:.2f}, Max DD: {max_drawdown*100:.2f}%")
        
        return results
    
    def plot_backtest_results(self, results: Dict[str, Any],
                             save_path: Optional[str] = None):
        """
        Plot backtest results.
        
        Args:
            results: Backtest results
            save_path: Path to save plot
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Portfolio value over time
        axes[0].plot(results['portfolio_values'], linewidth=2)
        axes[0].axhline(y=results['initial_capital'], color='r', linestyle='--', 
                       label='Initial Capital')
        axes[0].set_xlabel('Time Step')
        axes[0].set_ylabel('Portfolio Value ($)')
        axes[0].set_title('Portfolio Value Over Time')
        axes[0].legend()
        axes[0].grid(True)
        
        # Returns distribution
        axes[1].hist(results['returns'], bins=50, edgecolor='black')
        axes[1].axvline(x=0, color='r', linestyle='--', linewidth=2)
        axes[1].set_xlabel('Return')
        axes[1].set_ylabel('Frequency')
        axes[1].set_title('Return Distribution')
        axes[1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved backtest plot to {save_path}")
        else:
            plt.show()
        
        plt.close()


if __name__ == '__main__':
    # Example usage
    print("Model Evaluation Module")
    
    # Create dummy data
    predictions = np.random.randn(100, 1)
    targets = predictions + np.random.randn(100, 1) * 0.1
    
    # Calculate metrics
    mse = np.mean((predictions - targets) ** 2)
    mae = np.mean(np.abs(predictions - targets))
    rmse = np.sqrt(mse)
    
    print(f"MSE: {mse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")

# Made with Bob
