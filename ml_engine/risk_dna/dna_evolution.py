"""
Risk DNA Evolution Tracker
Tracks and analyzes how Risk DNA changes over time.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .dna_generator import RiskDNA
from .dna_comparator import DNAComparator

logger = logging.getLogger(__name__)


class DNAEvolutionTracker:
    """
    Tracks Risk DNA changes over time for entities.
    """
    
    def __init__(self, window_size: int = 30):
        """
        Initialize evolution tracker.
        
        Args:
            window_size: Time window for tracking (in days)
        """
        self.window_size = window_size
        self.history: Dict[str, List[RiskDNA]] = defaultdict(list)
        self.comparator = DNAComparator(metric='cosine')
        
        logger.info(f"Initialized DNAEvolutionTracker with window_size={window_size}")
    
    def add_dna(self, dna: RiskDNA):
        """
        Add DNA to tracking history.
        
        Args:
            dna: Risk DNA to add
        """
        self.history[dna.entity_id].append(dna)
        
        # Keep only recent history
        cutoff_date = datetime.now() - timedelta(days=self.window_size)
        self.history[dna.entity_id] = [
            d for d in self.history[dna.entity_id]
            if d.timestamp >= cutoff_date
        ]
    
    def get_evolution_rate(self, entity_id: str) -> float:
        """
        Compute rate of DNA evolution.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Evolution rate (average change per day)
        """
        if entity_id not in self.history or len(self.history[entity_id]) < 2:
            return 0.0
        
        dnas = sorted(self.history[entity_id], key=lambda x: x.timestamp)
        
        # Compute pairwise changes
        changes = []
        for i in range(len(dnas) - 1):
            similarity = self.comparator.compare(dnas[i], dnas[i+1])
            change = 1 - similarity  # Convert similarity to change
            
            # Normalize by time difference
            time_diff = (dnas[i+1].timestamp - dnas[i].timestamp).days
            if time_diff > 0:
                changes.append(change / time_diff)
        
        # Average evolution rate
        return float(np.mean(changes)) if changes else 0.0
    
    def detect_mutations(self, entity_id: str, threshold: float = 0.3) -> List[Dict]:
        """
        Detect significant DNA mutations.
        
        Args:
            entity_id: Entity identifier
            threshold: Mutation detection threshold
            
        Returns:
            List of mutation events
        """
        if entity_id not in self.history or len(self.history[entity_id]) < 2:
            return []
        
        dnas = sorted(self.history[entity_id], key=lambda x: x.timestamp)
        mutations = []
        
        for i in range(len(dnas) - 1):
            similarity = self.comparator.compare(dnas[i], dnas[i+1])
            change = 1 - similarity
            
            if change > threshold:
                # Identify which components changed most
                component_changes = self._compute_component_changes(
                    dnas[i], dnas[i+1]
                )
                
                mutations.append({
                    'timestamp': dnas[i+1].timestamp,
                    'change_magnitude': float(change),
                    'component_changes': component_changes,
                    'before_signature': dnas[i].signature,
                    'after_signature': dnas[i+1].signature
                })
        
        return mutations
    
    def _compute_component_changes(self, dna1: RiskDNA, dna2: RiskDNA) -> Dict[str, float]:
        """Compute changes in DNA components."""
        changes = {}
        
        for key in dna1.components.keys():
            val1 = dna1.components.get(key, 0)
            val2 = dna2.components.get(key, 0)
            
            if val1 != 0:
                change = abs(val2 - val1) / abs(val1)
            else:
                change = abs(val2)
            
            changes[key] = float(change)
        
        return changes
    
    def get_evolution_trajectory(self, entity_id: str) -> np.ndarray:
        """
        Get DNA evolution trajectory over time.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Array of DNA vectors over time [time_steps, dna_dim]
        """
        if entity_id not in self.history:
            return np.array([])
        
        dnas = sorted(self.history[entity_id], key=lambda x: x.timestamp)
        trajectory = np.array([dna.dna_vector for dna in dnas])
        
        return trajectory
    
    def predict_next_dna(self, entity_id: str) -> Optional[np.ndarray]:
        """
        Predict next DNA state using linear extrapolation.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Predicted DNA vector
        """
        trajectory = self.get_evolution_trajectory(entity_id)
        
        if len(trajectory) < 2:
            return None
        
        # Simple linear extrapolation
        if len(trajectory) >= 3:
            # Use last 3 points for better prediction
            recent = trajectory[-3:]
            # Fit linear trend
            trend = recent[-1] - recent[0]
            prediction = trajectory[-1] + trend / 2
        else:
            # Use last 2 points
            trend = trajectory[-1] - trajectory[-2]
            prediction = trajectory[-1] + trend
        
        return prediction


class DNAMutationAnalyzer:
    """
    Analyzes patterns in DNA mutations.
    """
    
    def __init__(self):
        """Initialize mutation analyzer."""
        self.mutation_patterns: Dict[str, List[Dict]] = defaultdict(list)
        logger.info("Initialized DNAMutationAnalyzer")
    
    def add_mutation(self, entity_id: str, mutation: Dict):
        """
        Add mutation to analysis.
        
        Args:
            entity_id: Entity identifier
            mutation: Mutation event dictionary
        """
        self.mutation_patterns[entity_id].append(mutation)
    
    def identify_common_patterns(self, min_occurrences: int = 3) -> List[Dict]:
        """
        Identify common mutation patterns across entities.
        
        Args:
            min_occurrences: Minimum occurrences to be considered common
            
        Returns:
            List of common patterns
        """
        # Collect all component changes
        all_changes = []
        for mutations in self.mutation_patterns.values():
            for mutation in mutations:
                all_changes.append(mutation['component_changes'])
        
        if not all_changes:
            return []
        
        # Find common patterns (simplified)
        # Group by dominant component
        pattern_counts = defaultdict(int)
        
        for changes in all_changes:
            # Find component with largest change
            dominant = max(changes.items(), key=lambda x: x[1])
            pattern_counts[dominant[0]] += 1
        
        # Filter by minimum occurrences
        common_patterns = [
            {'component': comp, 'occurrences': count}
            for comp, count in pattern_counts.items()
            if count >= min_occurrences
        ]
        
        return common_patterns
    
    def get_mutation_frequency(self, entity_id: str) -> float:
        """
        Get mutation frequency for entity.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Mutations per day
        """
        if entity_id not in self.mutation_patterns:
            return 0.0
        
        mutations = self.mutation_patterns[entity_id]
        if len(mutations) < 2:
            return 0.0
        
        # Compute time span
        timestamps = [m['timestamp'] for m in mutations]
        time_span = (max(timestamps) - min(timestamps)).days
        
        if time_span == 0:
            return 0.0
        
        return len(mutations) / time_span
    
    def predict_next_mutation(self, entity_id: str) -> Optional[Dict]:
        """
        Predict when next mutation might occur.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Prediction dictionary
        """
        if entity_id not in self.mutation_patterns or len(self.mutation_patterns[entity_id]) < 2:
            return None
        
        mutations = sorted(self.mutation_patterns[entity_id], key=lambda x: x['timestamp'])
        
        # Compute average time between mutations
        time_diffs = []
        for i in range(len(mutations) - 1):
            diff = (mutations[i+1]['timestamp'] - mutations[i]['timestamp']).days
            time_diffs.append(diff)
        
        avg_interval = float(np.mean(time_diffs))
        std_interval = float(np.std(time_diffs))
        
        # Predict next mutation time
        last_mutation = mutations[-1]['timestamp']
        predicted_time = last_mutation + timedelta(days=avg_interval)
        
        return {
            'predicted_time': predicted_time,
            'confidence_interval': (avg_interval - std_interval, avg_interval + std_interval),
            'based_on_mutations': len(mutations)
        }


class DNAEvolutionPredictor:
    """
    Predicts future DNA evolution using time series models.
    """
    
    def __init__(self, prediction_horizon: int = 7):
        """
        Initialize evolution predictor.
        
        Args:
            prediction_horizon: Days ahead to predict
        """
        self.prediction_horizon = prediction_horizon
        logger.info(f"Initialized DNAEvolutionPredictor with horizon={prediction_horizon}")
    
    def predict(self, trajectory: np.ndarray) -> np.ndarray:
        """
        Predict future DNA states.
        
        Args:
            trajectory: Historical DNA trajectory [time_steps, dna_dim]
            
        Returns:
            Predicted trajectory [prediction_horizon, dna_dim]
        """
        if len(trajectory) < 3:
            # Not enough history, return last state
            return np.tile(trajectory[-1], (self.prediction_horizon, 1))
        
        # Use autoregressive prediction
        predictions = []
        current = trajectory[-1].copy()
        
        # Compute trend from recent history
        recent_trend = trajectory[-1] - trajectory[-3]
        trend_per_step = recent_trend / 2
        
        for _ in range(self.prediction_horizon):
            # Add trend with decay
            decay = 0.9 ** len(predictions)
            next_state = current + trend_per_step * decay
            predictions.append(next_state)
            current = next_state
        
        return np.array(predictions)
    
    def predict_with_confidence(self, trajectory: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with confidence intervals.
        
        Args:
            trajectory: Historical DNA trajectory
            
        Returns:
            Tuple of (predictions, confidence_intervals)
        """
        predictions = self.predict(trajectory)
        
        # Estimate confidence based on historical volatility
        if len(trajectory) >= 3:
            changes = np.diff(trajectory, axis=0)
            volatility = np.std(changes, axis=0)
        else:
            volatility = np.ones(trajectory.shape[1]) * 0.1
        
        # Confidence intervals (95%)
        confidence = 1.96 * volatility
        
        return predictions, confidence


if __name__ == '__main__':
    # Example usage
    print("Risk DNA Evolution Module")
    
    from dna_generator import RiskDNAGenerator
    
    # Create generator
    generator = RiskDNAGenerator(dna_dim=256)
    
    # Generate DNA sequence
    tracker = DNAEvolutionTracker(window_size=30)
    
    for i in range(10):
        features = {
            'portfolio': {'total_value': 1000000 * (1 + i * 0.1)},
            'historical': {'volatility_30d': 0.15 + i * 0.01},
            'counterparty': {'num_counterparties': 10 + i},
            'market': {'vix_level': 15 + i * 0.5}
        }
        
        dna = generator.generate('ENTITY_001', features)
        dna.timestamp = datetime.now() - timedelta(days=10-i)
        tracker.add_dna(dna)
    
    # Analyze evolution
    evolution_rate = tracker.get_evolution_rate('ENTITY_001')
    print(f"Evolution rate: {evolution_rate:.4f}")
    
    mutations = tracker.detect_mutations('ENTITY_001', threshold=0.2)
    print(f"Detected {len(mutations)} mutations")
    
    # Predict next DNA
    prediction = tracker.predict_next_dna('ENTITY_001')
    if prediction is not None:
        print(f"Predicted next DNA shape: {prediction.shape}")

# Made with Bob
