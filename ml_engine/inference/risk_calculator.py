"""
Comprehensive Risk Calculator combining all ML models.

This module integrates quantum optimization, GAT, temporal GNN, and Risk DNA
to provide comprehensive risk assessments for entities and portfolios.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import torch

from .inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessmentResult:
    """
    Comprehensive risk assessment result.
    
    Combines outputs from all models to provide a holistic risk view.
    """
    entity_id: str
    timestamp: float
    
    # Overall risk score (0-1, higher is riskier)
    overall_risk_score: float
    
    # Component scores
    quantum_optimization_score: Optional[float] = None
    graph_propagation_score: Optional[float] = None
    temporal_risk_score: Optional[float] = None
    cascade_probability: Optional[float] = None
    
    # Risk DNA
    risk_dna_vector: Optional[np.ndarray] = None
    similar_entities: List[str] = field(default_factory=list)
    
    # Detailed metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Confidence and uncertainty
    confidence: float = 1.0
    uncertainty: float = 0.0
    
    # Computation time
    computation_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entity_id': self.entity_id,
            'timestamp': self.timestamp,
            'overall_risk_score': float(self.overall_risk_score),
            'quantum_optimization_score': float(self.quantum_optimization_score) if self.quantum_optimization_score else None,
            'graph_propagation_score': float(self.graph_propagation_score) if self.graph_propagation_score else None,
            'temporal_risk_score': float(self.temporal_risk_score) if self.temporal_risk_score else None,
            'cascade_probability': float(self.cascade_probability) if self.cascade_probability else None,
            'risk_dna_vector': self.risk_dna_vector.tolist() if self.risk_dna_vector is not None else None,
            'similar_entities': self.similar_entities,
            'metrics': {k: float(v) for k, v in self.metrics.items()},
            'confidence': float(self.confidence),
            'uncertainty': float(self.uncertainty),
            'computation_time_ms': float(self.computation_time_ms)
        }


class RiskCalculator:
    """
    Comprehensive risk calculator integrating all ML models.
    
    Combines:
    - Quantum-inspired optimization for portfolio risk
    - Graph Attention Networks for risk propagation
    - Temporal GNN for time-series risk prediction
    - Risk DNA for entity fingerprinting and comparison
    """
    
    def __init__(self, inference_engine: InferenceEngine,
                 model_paths: Optional[Dict[str, str]] = None,
                 weights: Optional[Dict[str, float]] = None,
                 max_workers: int = 4):
        """
        Initialize risk calculator.
        
        Args:
            inference_engine: Inference engine instance
            model_paths: Dictionary mapping model names to file paths
            weights: Weights for combining model scores (default: equal weights)
            max_workers: Maximum parallel workers for batch processing
        """
        self.engine = inference_engine
        self.model_paths = model_paths or {}
        self.max_workers = max_workers
        
        # Default weights for combining scores
        self.weights = weights or {
            'quantum': 0.25,
            'graph': 0.25,
            'temporal': 0.25,
            'cascade': 0.25
        }
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        logger.info(f"Initialized RiskCalculator with weights: {self.weights}")
    
    def load_models(self):
        """Load all required models into the inference engine."""
        for model_name, model_path in self.model_paths.items():
            try:
                # Determine model type from name
                if 'gat' in model_name.lower():
                    model_type = 'risk_propagation_gat'
                elif 'temporal' in model_name.lower():
                    model_type = 'temporal_gnn'
                elif 'cascade' in model_name.lower():
                    model_type = 'risk_cascade'
                else:
                    model_type = 'gat'
                
                self.engine.model_cache.load_model(
                    model_path=model_path,
                    model_name=model_name,
                    model_type=model_type
                )
                logger.info(f"Loaded model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
    
    def calculate_risk(self, entity_id: str, 
                      features: Dict[str, Any],
                      graph_data: Optional[Dict[str, Any]] = None,
                      temporal_data: Optional[Dict[str, Any]] = None) -> RiskAssessmentResult:
        """
        Calculate comprehensive risk assessment for an entity.
        
        Args:
            entity_id: Entity identifier
            features: Entity features dictionary
            graph_data: Graph structure data (nodes, edges, features)
            temporal_data: Historical time-series data
            
        Returns:
            Comprehensive risk assessment result
        """
        start_time = time.time()
        
        result = RiskAssessmentResult(
            entity_id=entity_id,
            timestamp=time.time(),
            overall_risk_score=0.0
        )
        
        scores = []
        weights_used = []
        
        try:
            # 1. Quantum optimization score (portfolio-level)
            if 'portfolio' in features:
                quantum_score = self._calculate_quantum_score(features['portfolio'])
                if quantum_score is not None:
                    result.quantum_optimization_score = quantum_score
                    scores.append(quantum_score)
                    weights_used.append(self.weights['quantum'])
            
            # 2. Graph propagation score
            if graph_data is not None:
                graph_score = self._calculate_graph_score(entity_id, graph_data)
                if graph_score is not None:
                    result.graph_propagation_score = graph_score
                    scores.append(graph_score)
                    weights_used.append(self.weights['graph'])
            
            # 3. Temporal risk score
            if temporal_data is not None:
                temporal_score = self._calculate_temporal_score(entity_id, temporal_data)
                if temporal_score is not None:
                    result.temporal_risk_score = temporal_score
                    scores.append(temporal_score)
                    weights_used.append(self.weights['temporal'])
            
            # 4. Cascade probability
            if graph_data is not None and temporal_data is not None:
                cascade_prob = self._calculate_cascade_probability(entity_id, graph_data, temporal_data)
                if cascade_prob is not None:
                    result.cascade_probability = cascade_prob
                    scores.append(cascade_prob)
                    weights_used.append(self.weights['cascade'])
            
            # 5. Generate Risk DNA
            result.risk_dna_vector = self._generate_risk_dna(entity_id, features)
            
            # Calculate overall risk score (weighted average)
            if scores:
                # Normalize weights
                total_weight = sum(weights_used)
                normalized_weights = [w / total_weight for w in weights_used]
                result.overall_risk_score = sum(s * w for s, w in zip(scores, normalized_weights))
                
                # Calculate confidence based on number of models used
                result.confidence = len(scores) / 4.0  # 4 possible models
                result.uncertainty = 1.0 - result.confidence
            else:
                logger.warning(f"No risk scores calculated for {entity_id}")
                result.overall_risk_score = 0.5  # Default to medium risk
                result.confidence = 0.0
                result.uncertainty = 1.0
            
            # Add detailed metrics
            result.metrics = self._calculate_detailed_metrics(features, scores)
            
        except Exception as e:
            logger.error(f"Error calculating risk for {entity_id}: {e}")
            result.overall_risk_score = 0.5
            result.confidence = 0.0
            result.uncertainty = 1.0
        
        result.computation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _calculate_quantum_score(self, portfolio_features: Dict[str, Any]) -> Optional[float]:
        """
        Calculate quantum optimization score.
        
        Args:
            portfolio_features: Portfolio features
            
        Returns:
            Risk score or None
        """
        try:
            # Simulate quantum optimization score
            # In production, this would use the QAOA optimizer
            volatility = portfolio_features.get('volatility', 0.1)
            concentration = portfolio_features.get('concentration', 0.5)
            
            # Simple heuristic: higher volatility and concentration = higher risk
            score = (volatility * 0.6 + concentration * 0.4)
            return float(np.clip(score, 0, 1))
        except Exception as e:
            logger.error(f"Error calculating quantum score: {e}")
            return None
    
    def _calculate_graph_score(self, entity_id: str, graph_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate graph propagation score using GAT.
        
        Args:
            entity_id: Entity identifier
            graph_data: Graph structure and features
            
        Returns:
            Risk score or None
        """
        try:
            # In production, this would use the trained GAT model
            # For now, simulate based on graph structure
            
            # Get entity's connections
            num_connections = graph_data.get('num_connections', 0)
            avg_counterparty_risk = graph_data.get('avg_counterparty_risk', 0.5)
            
            # More connections and higher counterparty risk = higher propagation risk
            score = (num_connections / 100.0) * 0.4 + avg_counterparty_risk * 0.6
            return float(np.clip(score, 0, 1))
        except Exception as e:
            logger.error(f"Error calculating graph score: {e}")
            return None
    
    def _calculate_temporal_score(self, entity_id: str, temporal_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate temporal risk score using Temporal GNN.
        
        Args:
            entity_id: Entity identifier
            temporal_data: Historical time-series data
            
        Returns:
            Risk score or None
        """
        try:
            # In production, this would use the trained Temporal GNN
            # For now, simulate based on historical trends
            
            historical_volatility = temporal_data.get('historical_volatility', 0.1)
            trend = temporal_data.get('trend', 0.0)  # -1 to 1
            
            # Higher volatility and negative trend = higher risk
            score = historical_volatility * 0.7 + (1 - trend) / 2 * 0.3
            return float(np.clip(score, 0, 1))
        except Exception as e:
            logger.error(f"Error calculating temporal score: {e}")
            return None
    
    def _calculate_cascade_probability(self, entity_id: str, 
                                      graph_data: Dict[str, Any],
                                      temporal_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate cascade probability.
        
        Args:
            entity_id: Entity identifier
            graph_data: Graph structure
            temporal_data: Historical data
            
        Returns:
            Cascade probability or None
        """
        try:
            # In production, this would use the cascade predictor model
            # For now, simulate based on connectivity and volatility
            
            centrality = graph_data.get('centrality', 0.5)
            volatility = temporal_data.get('historical_volatility', 0.1)
            
            # High centrality and volatility = higher cascade risk
            prob = centrality * 0.6 + volatility * 0.4
            return float(np.clip(prob, 0, 1))
        except Exception as e:
            logger.error(f"Error calculating cascade probability: {e}")
            return None
    
    def _generate_risk_dna(self, entity_id: str, features: Dict[str, Any]) -> np.ndarray:
        """
        Generate Risk DNA vector for entity.
        
        Args:
            entity_id: Entity identifier
            features: Entity features
            
        Returns:
            256-dimensional Risk DNA vector
        """
        try:
            # In production, this would use the Risk DNA generator
            # For now, create a simple fingerprint
            
            # Extract key features
            portfolio_value = features.get('portfolio', {}).get('total_value', 0)
            volatility = features.get('historical', {}).get('volatility_30d', 0.1)
            num_counterparties = features.get('counterparty', {}).get('num_counterparties', 0)
            
            # Create 256-dim vector with some structure
            dna = np.zeros(256)
            
            # Portfolio features (0-63)
            dna[0] = np.log1p(portfolio_value) / 20.0
            dna[1:32] = np.random.randn(31) * 0.1 + volatility
            
            # Historical features (64-127)
            dna[64:96] = np.random.randn(32) * 0.1 + volatility
            
            # Counterparty features (128-191)
            dna[128] = num_counterparties / 100.0
            dna[129:160] = np.random.randn(31) * 0.1
            
            # Market features (192-255)
            dna[192:224] = np.random.randn(32) * 0.1
            
            # Normalize
            dna = dna / (np.linalg.norm(dna) + 1e-8)
            
            return dna
        except Exception as e:
            logger.error(f"Error generating Risk DNA: {e}")
            return np.zeros(256)
    
    def _calculate_detailed_metrics(self, features: Dict[str, Any], 
                                   scores: List[float]) -> Dict[str, float]:
        """
        Calculate detailed risk metrics.
        
        Args:
            features: Entity features
            scores: Component risk scores
            
        Returns:
            Dictionary of detailed metrics
        """
        metrics = {}
        
        try:
            # Statistical metrics
            if scores:
                metrics['mean_score'] = float(np.mean(scores))
                metrics['std_score'] = float(np.std(scores))
                metrics['min_score'] = float(np.min(scores))
                metrics['max_score'] = float(np.max(scores))
            
            # Feature-based metrics
            if 'portfolio' in features:
                metrics['portfolio_value'] = float(features['portfolio'].get('total_value', 0))
                metrics['portfolio_volatility'] = float(features['portfolio'].get('volatility', 0))
            
            if 'historical' in features:
                metrics['historical_volatility'] = float(features['historical'].get('volatility_30d', 0))
            
            if 'counterparty' in features:
                metrics['num_counterparties'] = float(features['counterparty'].get('num_counterparties', 0))
        
        except Exception as e:
            logger.error(f"Error calculating detailed metrics: {e}")
        
        return metrics
    
    def calculate_batch_risk(self, entities: List[Tuple[str, Dict[str, Any]]],
                           graph_data: Optional[Dict[str, Any]] = None,
                           temporal_data: Optional[Dict[str, Dict[str, Any]]] = None) -> List[RiskAssessmentResult]:
        """
        Calculate risk for multiple entities in parallel.
        
        Args:
            entities: List of (entity_id, features) tuples
            graph_data: Shared graph structure
            temporal_data: Dictionary mapping entity_id to temporal data
            
        Returns:
            List of risk assessment results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for entity_id, features in entities:
                entity_temporal = temporal_data.get(entity_id) if temporal_data else None
                future = executor.submit(
                    self.calculate_risk,
                    entity_id,
                    features,
                    graph_data,
                    entity_temporal
                )
                futures[future] = entity_id
            
            for future in as_completed(futures):
                entity_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error calculating risk for {entity_id}: {e}")
        
        return results


if __name__ == '__main__':
    # Example usage
    print("Risk Calculator Module")
    
    from inference_engine import InferenceEngine
    
    # Create inference engine and calculator
    engine = InferenceEngine()
    calculator = RiskCalculator(engine)
    
    # Example risk calculation
    features = {
        'portfolio': {'total_value': 1000000, 'volatility': 0.15},
        'historical': {'volatility_30d': 0.12},
        'counterparty': {'num_counterparties': 25}
    }
    
    result = calculator.calculate_risk('ENTITY_001', features)
    print(f"\nRisk Assessment for ENTITY_001:")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Computation Time: {result.computation_time_ms:.2f}ms")

# Made with Bob
