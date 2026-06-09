"""
Risk Cascade Predictor
Detects and predicts systemic risk cascades in financial networks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CascadeDetector(nn.Module):
    """
    Detects risk cascades in temporal graph sequences.
    """
    
    def __init__(self, feature_dim: int, hidden_dim: int = 64,
                 threshold: float = 0.7):
        """
        Initialize cascade detector.
        
        Args:
            feature_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            threshold: Cascade detection threshold
        """
        super(CascadeDetector, self).__init__()
        
        self.threshold = threshold
        
        # Feature extraction
        self.feature_extractor = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        # Cascade probability head
        self.cascade_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        # Severity estimation head
        self.severity_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, feature_dim]
            
        Returns:
            Tuple of (cascade_probability, severity_score)
        """
        features = self.feature_extractor(x)
        
        cascade_prob = self.cascade_head(features)
        severity = self.severity_head(features)
        
        return cascade_prob, severity
    
    def detect_cascades(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Detect cascades and return affected nodes.
        
        Args:
            x: Node features
            
        Returns:
            Tuple of (cascade_mask, probabilities, severities)
        """
        cascade_prob, severity = self.forward(x)
        
        # Binary mask for cascade detection
        cascade_mask = (cascade_prob > self.threshold).float()
        
        return cascade_mask, cascade_prob, severity


class RiskCascadePredictor(nn.Module):
    """
    Predicts risk cascade propagation patterns over time.
    """
    
    def __init__(self, node_feature_dim: int, temporal_feature_dim: int,
                 hidden_dim: int = 128, num_cascade_steps: int = 5,
                 dropout: float = 0.3):
        """
        Initialize risk cascade predictor.
        
        Args:
            node_feature_dim: Node feature dimension
            temporal_feature_dim: Temporal feature dimension
            hidden_dim: Hidden dimension
            num_cascade_steps: Number of cascade steps to predict
            dropout: Dropout probability
        """
        super(RiskCascadePredictor, self).__init__()
        
        self.num_cascade_steps = num_cascade_steps
        
        # Node encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Temporal encoder
        self.temporal_encoder = nn.LSTM(
            temporal_feature_dim,
            hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=dropout
        )
        
        # Cascade propagation network
        self.propagation_net = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, hidden_dim)
            ) for _ in range(num_cascade_steps)
        ])
        
        # Output heads for each cascade step
        self.output_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
                nn.Sigmoid()
            ) for _ in range(num_cascade_steps)
        ])
        
        # Confidence estimator
        self.confidence_net = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        logger.info(f"Initialized RiskCascadePredictor with {num_cascade_steps} cascade steps")
    
    def forward(self, node_features: torch.Tensor,
                temporal_features: torch.Tensor,
                edge_index: torch.Tensor) -> Tuple[List[torch.Tensor], torch.Tensor]:
        """
        Predict cascade propagation.
        
        Args:
            node_features: Node features [num_nodes, node_feature_dim]
            temporal_features: Temporal features [num_nodes, seq_len, temporal_feature_dim]
            edge_index: Edge indices [2, num_edges]
            
        Returns:
            Tuple of (cascade_predictions, confidence_scores)
        """
        # Encode nodes
        node_embed = self.node_encoder(node_features)
        
        # Encode temporal patterns
        temporal_embed, _ = self.temporal_encoder(temporal_features)
        temporal_embed = temporal_embed[:, -1, :]  # Use last time step
        
        # Combine node and temporal embeddings
        combined = torch.cat([node_embed, temporal_embed], dim=1)
        
        # Predict cascade for each step
        cascade_predictions = []
        current_state = combined
        
        for step in range(self.num_cascade_steps):
            # Propagate through network
            current_state = self.propagation_net[step](current_state)
            
            # Predict cascade probability
            cascade_prob = self.output_heads[step](current_state)
            cascade_predictions.append(cascade_prob)
        
        # Estimate confidence
        confidence = self.confidence_net(current_state)
        
        return cascade_predictions, confidence
    
    def predict_with_intervals(self, node_features: torch.Tensor,
                               temporal_features: torch.Tensor,
                               edge_index: torch.Tensor,
                               num_samples: int = 100) -> Dict[str, torch.Tensor]:
        """
        Predict with confidence intervals using Monte Carlo dropout.
        
        Args:
            node_features: Node features
            temporal_features: Temporal features
            edge_index: Edge indices
            num_samples: Number of MC samples
            
        Returns:
            Dictionary with mean, lower, upper predictions
        """
        self.train()  # Enable dropout
        
        all_predictions = []
        
        with torch.no_grad():
            for _ in range(num_samples):
                predictions, _ = self.forward(
                    node_features, temporal_features, edge_index
                )
                # Stack predictions: [num_cascade_steps, num_nodes, 1]
                predictions = torch.stack(predictions, dim=0)
                all_predictions.append(predictions)
        
        # Stack all samples: [num_samples, num_cascade_steps, num_nodes, 1]
        all_predictions = torch.stack(all_predictions, dim=0)
        
        # Compute statistics
        mean_pred = torch.mean(all_predictions, dim=0)
        std_pred = torch.std(all_predictions, dim=0)
        
        # 95% confidence intervals
        lower_bound = mean_pred - 1.96 * std_pred
        upper_bound = mean_pred + 1.96 * std_pred
        
        return {
            'mean': mean_pred,
            'std': std_pred,
            'lower': lower_bound,
            'upper': upper_bound
        }


class TemporalPatternRecognizer(nn.Module):
    """
    Recognizes temporal patterns that precede risk cascades.
    """
    
    def __init__(self, feature_dim: int, pattern_dim: int = 64,
                 num_patterns: int = 10):
        """
        Initialize pattern recognizer.
        
        Args:
            feature_dim: Input feature dimension
            pattern_dim: Pattern embedding dimension
            num_patterns: Number of pattern prototypes
        """
        super(TemporalPatternRecognizer, self).__init__()
        
        self.num_patterns = num_patterns
        
        # Pattern encoder
        self.encoder = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, pattern_dim)
        )
        
        # Pattern prototypes (learnable)
        self.pattern_prototypes = nn.Parameter(
            torch.randn(num_patterns, pattern_dim)
        )
        
        # Pattern classifier
        self.classifier = nn.Sequential(
            nn.Linear(pattern_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_patterns),
            nn.Softmax(dim=1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recognize patterns.
        
        Args:
            x: Input features [batch_size, feature_dim]
            
        Returns:
            Tuple of (pattern_probabilities, pattern_embeddings)
        """
        # Encode input
        embeddings = self.encoder(x)
        
        # Classify pattern
        pattern_probs = self.classifier(embeddings)
        
        return pattern_probs, embeddings
    
    def get_pattern_similarity(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute similarity to each pattern prototype.
        
        Args:
            x: Input features
            
        Returns:
            Similarity scores [batch_size, num_patterns]
        """
        embeddings = self.encoder(x)
        
        # Compute cosine similarity to prototypes
        embeddings_norm = F.normalize(embeddings, p=2, dim=1)
        prototypes_norm = F.normalize(self.pattern_prototypes, p=2, dim=1)
        
        similarity = torch.mm(embeddings_norm, prototypes_norm.t())
        
        return similarity


class MultiStepCascadePredictor(nn.Module):
    """
    Multi-step ahead cascade predictor with attention mechanism.
    """
    
    def __init__(self, feature_dim: int, hidden_dim: int = 128,
                 max_steps: int = 10, dropout: float = 0.3):
        """
        Initialize multi-step predictor.
        
        Args:
            feature_dim: Feature dimension
            hidden_dim: Hidden dimension
            max_steps: Maximum prediction steps
            dropout: Dropout probability
        """
        super(MultiStepCascadePredictor, self).__init__()
        
        self.max_steps = max_steps
        
        # Encoder
        self.encoder = nn.GRU(
            feature_dim,
            hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=dropout
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            hidden_dim,
            num_heads=4,
            dropout=dropout,
            batch_first=True
        )
        
        # Decoder for each step
        self.decoder = nn.GRU(
            hidden_dim,
            hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=dropout
        )
        
        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor, num_steps: Optional[int] = None) -> torch.Tensor:
        """
        Predict multiple steps ahead.
        
        Args:
            x: Input sequence [batch_size, seq_len, feature_dim]
            num_steps: Number of steps to predict (default: max_steps)
            
        Returns:
            Predictions [batch_size, num_steps, 1]
        """
        if num_steps is None:
            num_steps = self.max_steps
        
        # Encode input sequence
        encoded, hidden = self.encoder(x)
        
        # Apply attention
        attended, _ = self.attention(encoded, encoded, encoded)
        
        # Decode for multiple steps
        predictions = []
        decoder_input = attended[:, -1:, :]  # Last time step
        
        for _ in range(num_steps):
            decoder_output, hidden = self.decoder(decoder_input, hidden)
            pred = self.output_proj(decoder_output)
            predictions.append(pred)
            
            # Use prediction as next input
            decoder_input = decoder_output
        
        # Stack predictions
        predictions = torch.cat(predictions, dim=1)
        
        return predictions


if __name__ == '__main__':
    # Example usage
    print("Risk Cascade Predictor Module")
    
    # Create dummy data
    num_nodes = 50
    node_feature_dim = 20
    temporal_feature_dim = 15
    seq_len = 10
    
    node_features = torch.randn(num_nodes, node_feature_dim)
    temporal_features = torch.randn(num_nodes, seq_len, temporal_feature_dim)
    edge_index = torch.randint(0, num_nodes, (2, 100))
    
    # Create predictor
    predictor = RiskCascadePredictor(
        node_feature_dim=node_feature_dim,
        temporal_feature_dim=temporal_feature_dim,
        hidden_dim=64,
        num_cascade_steps=5
    )
    
    # Predict cascades
    cascade_preds, confidence = predictor(node_features, temporal_features, edge_index)
    
    print(f"Number of cascade steps: {len(cascade_preds)}")
    print(f"Cascade prediction shape: {cascade_preds[0].shape}")
    print(f"Confidence shape: {confidence.shape}")
    
    # Predict with intervals
    intervals = predictor.predict_with_intervals(
        node_features, temporal_features, edge_index, num_samples=50
    )
    print(f"Mean prediction shape: {intervals['mean'].shape}")

# Made with Bob
