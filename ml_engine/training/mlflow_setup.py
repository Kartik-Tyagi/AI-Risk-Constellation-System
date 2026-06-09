"""
MLflow Setup and Configuration for AI Risk Constellation System.

This module initializes MLflow for experiment tracking and model management.
Uses local file-based tracking for deployment without external dependencies.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class MLflowConfig:
    """Configuration for MLflow setup."""
    
    def __init__(self, 
                 tracking_uri: Optional[str] = None,
                 experiment_name: str = "risk_constellation",
                 artifact_location: Optional[str] = None):
        """
        Initialize MLflow configuration.
        
        Args:
            tracking_uri: URI for MLflow tracking server (default: local file)
            experiment_name: Name of the experiment
            artifact_location: Location to store artifacts
        """
        # Default to SQLite-based tracking (file store is deprecated in newer MLflow)
        if tracking_uri is None:
            mlruns_dir = Path(__file__).parent.parent.parent / "mlruns"
            mlruns_dir.mkdir(exist_ok=True)
            tracking_uri = f"sqlite:///{mlruns_dir.absolute()}/mlflow.db"
        
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        
        # Default artifact location
        if artifact_location is None:
            artifacts_dir = Path(__file__).parent.parent.parent / "mlartifacts"
            artifacts_dir.mkdir(exist_ok=True)
            artifact_location = str(artifacts_dir.absolute())
        
        self.artifact_location = artifact_location


class MLflowManager:
    """
    Manager for MLflow experiment tracking and model registry.
    
    Provides utilities for logging metrics, parameters, models, and artifacts.
    """
    
    def __init__(self, config: Optional[MLflowConfig] = None):
        """
        Initialize MLflow manager.
        
        Args:
            config: MLflow configuration (uses defaults if None)
        """
        self.config = config or MLflowConfig()
        self.client: Optional[MlflowClient] = None
        self.experiment_id: Optional[str] = None
        
        self._setup_mlflow()
    
    def _setup_mlflow(self):
        """Set up MLflow tracking and experiment."""
        try:
            # Set tracking URI
            mlflow.set_tracking_uri(self.config.tracking_uri)
            logger.info(f"MLflow tracking URI: {self.config.tracking_uri}")
            
            # Initialize client
            self.client = MlflowClient()
            
            # Create or get experiment
            try:
                if self.client is None:
                    raise ValueError("MLflow client not initialized")
                
                experiment = self.client.get_experiment_by_name(self.config.experiment_name)
                if experiment is None:
                    self.experiment_id = self.client.create_experiment(
                        name=self.config.experiment_name,
                        artifact_location=self.config.artifact_location
                    )
                    logger.info(f"Created experiment: {self.config.experiment_name}")
                else:
                    self.experiment_id = experiment.experiment_id
                    logger.info(f"Using existing experiment: {self.config.experiment_name}")
            except Exception as e:
                logger.error(f"Error setting up experiment: {e}")
                raise
            
            # Set experiment
            mlflow.set_experiment(self.config.experiment_name)
            
        except Exception as e:
            logger.error(f"Failed to setup MLflow: {e}")
            raise
    
    def start_run(self, run_name: Optional[str] = None, 
                  tags: Optional[Dict[str, str]] = None) -> mlflow.ActiveRun:
        """
        Start a new MLflow run.
        
        Args:
            run_name: Name for the run
            tags: Tags to add to the run
            
        Returns:
            Active MLflow run
        """
        return mlflow.start_run(run_name=run_name, tags=tags)
    
    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters to current run.
        
        Args:
            params: Dictionary of parameters
        """
        try:
            mlflow.log_params(params)
        except Exception as e:
            logger.error(f"Error logging params: {e}")
    
    def log_param(self, key: str, value: Any):
        """
        Log a single parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        try:
            mlflow.log_param(key, value)
        except Exception as e:
            logger.error(f"Error logging param {key}: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics to current run.
        
        Args:
            metrics: Dictionary of metrics
            step: Step number for the metrics
        """
        try:
            mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def log_metric(self, key: str, value: float, step: Optional[int] = None):
        """
        Log a single metric.
        
        Args:
            key: Metric name
            value: Metric value
            step: Step number
        """
        try:
            mlflow.log_metric(key, value, step=step)
        except Exception as e:
            logger.error(f"Error logging metric {key}: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """
        Log an artifact file.
        
        Args:
            local_path: Path to local file
            artifact_path: Path within artifact store
        """
        try:
            mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.error(f"Error logging artifact: {e}")
    
    def log_model(self, model: Any, artifact_path: str, 
                  registered_model_name: Optional[str] = None,
                  **kwargs):
        """
        Log a PyTorch model.
        
        Args:
            model: Model to log
            artifact_path: Path within artifact store
            registered_model_name: Name for model registry
            **kwargs: Additional arguments for mlflow.pytorch.log_model
        """
        try:
            import mlflow.pytorch
            mlflow.pytorch.log_model(
                model,
                artifact_path,
                registered_model_name=registered_model_name,
                **kwargs
            )
            logger.info(f"Logged model to {artifact_path}")
        except Exception as e:
            logger.error(f"Error logging model: {e}")
    
    def register_model(self, model_uri: str, name: str) -> Any:
        """
        Register a model in the model registry.
        
        Args:
            model_uri: URI of the model
            name: Name for the registered model
            
        Returns:
            Registered model version
        """
        try:
            result = mlflow.register_model(model_uri, name)
            logger.info(f"Registered model {name} version {result.version}")
            return result
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            return None
    
    def load_model(self, model_uri: str) -> Any:
        """
        Load a model from MLflow.
        
        Args:
            model_uri: URI of the model
            
        Returns:
            Loaded model
        """
        try:
            import mlflow.pytorch
            model = mlflow.pytorch.load_model(model_uri)
            logger.info(f"Loaded model from {model_uri}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def get_experiment_runs(self, max_results: int = 100) -> list:
        """
        Get runs for the current experiment.
        
        Args:
            max_results: Maximum number of runs to return
            
        Returns:
            List of runs
        """
        try:
            if self.experiment_id and self.client:
                runs = self.client.search_runs(
                    experiment_ids=[self.experiment_id],
                    max_results=max_results
                )
                return runs
            return []
        except Exception as e:
            logger.error(f"Error getting runs: {e}")
            return []
    
    def get_best_run(self, metric_name: str, ascending: bool = False) -> Optional[Any]:
        """
        Get the best run based on a metric.
        
        Args:
            metric_name: Name of the metric to optimize
            ascending: If True, lower is better
            
        Returns:
            Best run or None
        """
        try:
            runs = self.get_experiment_runs()
            if not runs:
                return None
            
            # Sort by metric
            sorted_runs = sorted(
                runs,
                key=lambda r: r.data.metrics.get(metric_name, float('inf') if not ascending else float('-inf')),
                reverse=not ascending
            )
            
            return sorted_runs[0] if sorted_runs else None
        except Exception as e:
            logger.error(f"Error getting best run: {e}")
            return None
    
    def end_run(self):
        """End the current MLflow run."""
        try:
            mlflow.end_run()
        except Exception as e:
            logger.error(f"Error ending run: {e}")
    
    def get_tracking_uri(self) -> str:
        """Get the MLflow tracking URI."""
        return self.config.tracking_uri
    
    def get_experiment_id(self) -> Optional[str]:
        """Get the current experiment ID."""
        return self.experiment_id


def setup_mlflow(experiment_name: str = "risk_constellation",
                tracking_uri: Optional[str] = None) -> MLflowManager:
    """
    Convenience function to set up MLflow.
    
    Args:
        experiment_name: Name of the experiment
        tracking_uri: URI for tracking server
        
    Returns:
        Configured MLflow manager
    """
    config = MLflowConfig(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name
    )
    return MLflowManager(config)


if __name__ == '__main__':
    # Example usage
    print("MLflow Setup Module")
    
    # Initialize MLflow
    manager = setup_mlflow()
    
    print(f"Tracking URI: {manager.get_tracking_uri()}")
    print(f"Experiment ID: {manager.get_experiment_id()}")
    
    # Example run
    with manager.start_run(run_name="test_run"):
        manager.log_params({
            'learning_rate': 0.001,
            'batch_size': 32
        })
        
        manager.log_metrics({
            'loss': 0.5,
            'accuracy': 0.85
        })
        
        print("Logged test run")
    
    print("MLflow setup complete")

# Made with Bob
