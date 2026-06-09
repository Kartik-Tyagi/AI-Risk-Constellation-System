"""
Inference Engine for Real-Time Risk Calculations.

This module provides the core inference engine that loads and manages trained models,
optimizes batch inference, and provides GPU acceleration when available.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from collections import OrderedDict
import threading

import torch
import torch.nn as nn
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a loaded model."""
    model_name: str
    model_type: str
    version: str
    input_shape: tuple
    output_shape: tuple
    device: str
    loaded_at: float
    last_used: float
    use_count: int = 0


class ModelCache:
    """
    LRU cache for loaded models with automatic eviction.
    
    Manages model loading, caching, and eviction to optimize memory usage
    while maintaining fast inference times.
    """
    
    def __init__(self, max_size: int = 10, device: Optional[str] = None):
        """
        Initialize model cache.
        
        Args:
            max_size: Maximum number of models to cache
            device: Device to load models on ('cpu', 'cuda', or None for auto)
        """
        self.max_size = max_size
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.cache: OrderedDict[str, tuple[nn.Module, ModelMetadata]] = OrderedDict()
        self.lock = threading.Lock()
        
        logger.info(f"Initialized ModelCache with max_size={max_size}, device={self.device}")
    
    def load_model(self, model_path: Union[str, Path], model_name: str,
                   model_type: str, version: str = "1.0") -> nn.Module:
        """
        Load a model from disk or retrieve from cache.
        
        Args:
            model_path: Path to model file
            model_name: Name identifier for the model
            model_type: Type of model (e.g., 'gat', 'temporal_gnn', 'risk_dna')
            version: Model version
            
        Returns:
            Loaded model
        """
        with self.lock:
            # Check if model is in cache
            if model_name in self.cache:
                model, metadata = self.cache[model_name]
                # Move to end (most recently used)
                self.cache.move_to_end(model_name)
                metadata.last_used = time.time()
                metadata.use_count += 1
                logger.debug(f"Retrieved {model_name} from cache (use_count={metadata.use_count})")
                return model
            
            # Load model from disk
            logger.info(f"Loading model {model_name} from {model_path}")
            start_time = time.time()
            
            try:
                # Load model state dict
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # Extract model if it's wrapped in a checkpoint
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                    model_config = checkpoint.get('model_config', {})
                else:
                    state_dict = checkpoint
                    model_config = {}
                
                # Create model instance based on type
                model = self._create_model_instance(model_type, model_config)
                model.load_state_dict(state_dict)
                model.to(self.device)
                model.eval()
                
                # Create metadata
                metadata = ModelMetadata(
                    model_name=model_name,
                    model_type=model_type,
                    version=version,
                    input_shape=model_config.get('input_shape', ()),
                    output_shape=model_config.get('output_shape', ()),
                    device=self.device,
                    loaded_at=time.time(),
                    last_used=time.time(),
                    use_count=1
                )
                
                # Add to cache
                self._add_to_cache(model_name, model, metadata)
                
                load_time = time.time() - start_time
                logger.info(f"Loaded {model_name} in {load_time:.3f}s")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise
    
    def _create_model_instance(self, model_type: str, config: Dict[str, Any]) -> nn.Module:
        """
        Create a model instance based on type and config.
        
        Args:
            model_type: Type of model
            config: Model configuration
            
        Returns:
            Model instance
        """
        # Import models dynamically to avoid circular imports
        if model_type == 'gat':
            from ml_engine.graph_networks.gat_model import GAT
            return GAT(**config)
        elif model_type == 'risk_propagation_gat':
            from ml_engine.graph_networks.risk_propagation_gat import RiskPropagationGAT
            return RiskPropagationGAT(**config)
        elif model_type == 'temporal_gnn':
            from ml_engine.graph_networks.temporal_gnn import TemporalGNN
            return TemporalGNN(**config)
        elif model_type == 'risk_cascade':
            from ml_engine.graph_networks.risk_cascade_predictor import RiskCascadePredictor
            return RiskCascadePredictor(**config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _add_to_cache(self, model_name: str, model: nn.Module, metadata: ModelMetadata):
        """
        Add model to cache with LRU eviction.
        
        Args:
            model_name: Model identifier
            model: Model instance
            metadata: Model metadata
        """
        # Evict least recently used model if cache is full
        if len(self.cache) >= self.max_size:
            evicted_name, (evicted_model, evicted_metadata) = self.cache.popitem(last=False)
            logger.info(f"Evicted {evicted_name} from cache (use_count={evicted_metadata.use_count})")
            # Free GPU memory
            del evicted_model
            if self.device == 'cuda':
                torch.cuda.empty_cache()
        
        self.cache[model_name] = (model, metadata)
        logger.debug(f"Added {model_name} to cache (size={len(self.cache)}/{self.max_size})")
    
    def get_model(self, model_name: str) -> Optional[nn.Module]:
        """
        Get a model from cache without loading.
        
        Args:
            model_name: Model identifier
            
        Returns:
            Model if in cache, None otherwise
        """
        with self.lock:
            if model_name in self.cache:
                model, metadata = self.cache[model_name]
                self.cache.move_to_end(model_name)
                metadata.last_used = time.time()
                metadata.use_count += 1
                return model
            return None
    
    def clear(self):
        """Clear all models from cache."""
        with self.lock:
            self.cache.clear()
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            logger.info("Cleared model cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        with self.lock:
            stats = {
                'size': len(self.cache),
                'max_size': self.max_size,
                'device': self.device,
                'models': {}
            }
            
            for name, (_, metadata) in self.cache.items():
                stats['models'][name] = {
                    'type': metadata.model_type,
                    'version': metadata.version,
                    'use_count': metadata.use_count,
                    'loaded_at': metadata.loaded_at,
                    'last_used': metadata.last_used
                }
            
            return stats


class InferenceEngine:
    """
    Main inference engine for real-time risk calculations.
    
    Provides optimized batch inference with model caching and GPU acceleration.
    """
    
    def __init__(self, model_cache: Optional[ModelCache] = None,
                 batch_size: int = 32, device: Optional[str] = None):
        """
        Initialize inference engine.
        
        Args:
            model_cache: Model cache instance (creates new if None)
            batch_size: Default batch size for inference
            device: Device to use ('cpu', 'cuda', or None for auto)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_cache = model_cache or ModelCache(device=self.device)
        self.batch_size = batch_size
        
        logger.info(f"Initialized InferenceEngine with device={self.device}, batch_size={batch_size}")
    
    @torch.no_grad()
    def predict(self, model_name: str, inputs: Union[torch.Tensor, Dict[str, torch.Tensor]],
                batch_size: Optional[int] = None) -> torch.Tensor:
        """
        Run inference on inputs.
        
        Args:
            model_name: Name of model to use
            inputs: Input tensor or dictionary of tensors
            batch_size: Batch size for inference (uses default if None)
            
        Returns:
            Model predictions
        """
        model = self.model_cache.get_model(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found in cache. Load it first.")
        
        model.eval()
        batch_size = batch_size or self.batch_size
        
        # Handle different input types
        if isinstance(inputs, dict):
            # Move all tensors to device
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                     for k, v in inputs.items()}
            return model(**inputs)
        else:
            inputs = inputs.to(self.device)
            
            # Batch processing for large inputs
            if len(inputs) > batch_size:
                return self._batch_predict(model, inputs, batch_size)
            else:
                return model(inputs)
    
    def _batch_predict(self, model: nn.Module, inputs: torch.Tensor,
                      batch_size: int) -> torch.Tensor:
        """
        Process inputs in batches.
        
        Args:
            model: Model to use
            inputs: Input tensor
            batch_size: Batch size
            
        Returns:
            Concatenated predictions
        """
        predictions = []
        
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            pred = model(batch)
            predictions.append(pred)
        
        return torch.cat(predictions, dim=0)
    
    @torch.no_grad()
    def predict_batch(self, model_name: str, 
                     batch_inputs: List[Union[torch.Tensor, Dict[str, torch.Tensor]]]) -> List[torch.Tensor]:
        """
        Run inference on multiple inputs in parallel.
        
        Args:
            model_name: Name of model to use
            batch_inputs: List of inputs
            
        Returns:
            List of predictions
        """
        model = self.model_cache.get_model(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not found in cache. Load it first.")
        
        model.eval()
        predictions = []
        
        for inputs in batch_inputs:
            if isinstance(inputs, dict):
                inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                         for k, v in inputs.items()}
                pred = model(**inputs)
            else:
                inputs = inputs.to(self.device)
                pred = model(inputs)
            predictions.append(pred)
        
        return predictions
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a loaded model.
        
        Args:
            model_name: Model identifier
            
        Returns:
            Model information dictionary or None
        """
        if model_name in self.model_cache.cache:
            _, metadata = self.model_cache.cache[model_name]
            return {
                'name': metadata.model_name,
                'type': metadata.model_type,
                'version': metadata.version,
                'device': metadata.device,
                'use_count': metadata.use_count,
                'loaded_at': metadata.loaded_at,
                'last_used': metadata.last_used
            }
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get engine statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'device': self.device,
            'batch_size': self.batch_size,
            'cache': self.model_cache.get_stats()
        }


if __name__ == '__main__':
    # Example usage
    print("Inference Engine Module")
    
    # Create inference engine
    engine = InferenceEngine(batch_size=32)
    
    print(f"Device: {engine.device}")
    print(f"Batch size: {engine.batch_size}")
    print(f"Cache stats: {engine.get_stats()}")

# Made with Bob
