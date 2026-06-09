"""
Risk DNA Generator
Creates unique risk fingerprints for entities, portfolios, and transactions.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RiskDNA:
    """
    Risk DNA structure representing a unique risk fingerprint.
    """
    entity_id: str
    dna_vector: np.ndarray
    timestamp: datetime
    components: Dict[str, float]
    signature: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'entity_id': self.entity_id,
            'dna_vector': self.dna_vector.tolist(),
            'timestamp': self.timestamp.isoformat(),
            'components': self.components,
            'signature': self.signature,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RiskDNA':
        """Create from dictionary."""
        return cls(
            entity_id=data['entity_id'],
            dna_vector=np.array(data['dna_vector']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            components=data['components'],
            signature=data['signature'],
            metadata=data['metadata']
        )


class RiskDNAGenerator:
    """
    Generates Risk DNA fingerprints from various risk features.
    """
    
    def __init__(self, dna_dim: int = 256, use_neural_encoder: bool = True):
        """
        Initialize Risk DNA generator.
        
        Args:
            dna_dim: Dimension of DNA vector
            use_neural_encoder: Whether to use neural network for encoding
        """
        self.dna_dim = dna_dim
        self.use_neural_encoder = use_neural_encoder
        
        if use_neural_encoder:
            self.encoder = self._build_encoder()
        
        logger.info(f"Initialized RiskDNAGenerator with dim={dna_dim}")
    
    def _build_encoder(self) -> nn.Module:
        """Build neural encoder for DNA generation."""
        return nn.Sequential(
            nn.Linear(100, 512),  # Assume max 100 input features
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, self.dna_dim),
            nn.Tanh()  # Normalize to [-1, 1]
        )
    
    def generate(self, entity_id: str, features: Dict[str, Any],
                metadata: Optional[Dict] = None) -> RiskDNA:
        """
        Generate Risk DNA for an entity.
        
        Args:
            entity_id: Unique entity identifier
            features: Dictionary of risk features
            metadata: Additional metadata
            
        Returns:
            RiskDNA object
        """
        # Extract feature components
        portfolio_features = self._extract_portfolio_features(features)
        historical_features = self._extract_historical_features(features)
        counterparty_features = self._extract_counterparty_features(features)
        market_features = self._extract_market_features(features)
        
        # Combine all features
        combined_features = np.concatenate([
            portfolio_features,
            historical_features,
            counterparty_features,
            market_features
        ])
        
        # Generate DNA vector
        if self.use_neural_encoder:
            # Pad or truncate to 100 features
            if len(combined_features) < 100:
                combined_features = np.pad(
                    combined_features,
                    (0, 100 - len(combined_features)),
                    mode='constant'
                )
            else:
                combined_features = combined_features[:100]
            
            # Encode with neural network
            with torch.no_grad():
                features_tensor = torch.tensor(combined_features, dtype=torch.float32).unsqueeze(0)
                dna_vector = self.encoder(features_tensor).squeeze(0).numpy()
        else:
            # Use dimensionality reduction
            dna_vector = self._reduce_dimensions(combined_features, self.dna_dim)
        
        # Compute components
        components = {
            'portfolio_weight': float(np.linalg.norm(portfolio_features)),
            'historical_weight': float(np.linalg.norm(historical_features)),
            'counterparty_weight': float(np.linalg.norm(counterparty_features)),
            'market_weight': float(np.linalg.norm(market_features))
        }
        
        # Generate signature
        signature = self._generate_signature(dna_vector)
        
        # Create Risk DNA
        risk_dna = RiskDNA(
            entity_id=entity_id,
            dna_vector=dna_vector,
            timestamp=datetime.now(),
            components=components,
            signature=signature,
            metadata=metadata or {}
        )
        
        return risk_dna
    
    def _extract_portfolio_features(self, features: Dict) -> np.ndarray:
        """Extract portfolio composition features."""
        portfolio_data = features.get('portfolio', {})
        
        feature_list = [
            portfolio_data.get('total_value', 0.0),
            portfolio_data.get('num_positions', 0),
            portfolio_data.get('concentration_hhi', 0.0),
            portfolio_data.get('sector_diversity', 0.0),
            portfolio_data.get('avg_position_size', 0.0),
            portfolio_data.get('leverage_ratio', 0.0),
            portfolio_data.get('liquidity_ratio', 0.0),
            portfolio_data.get('var_95', 0.0),
            portfolio_data.get('cvar_95', 0.0),
            portfolio_data.get('sharpe_ratio', 0.0)
        ]
        
        return np.array(feature_list, dtype=np.float32)
    
    def _extract_historical_features(self, features: Dict) -> np.ndarray:
        """Extract historical risk event features."""
        historical_data = features.get('historical', {})
        
        feature_list = [
            historical_data.get('num_risk_events', 0),
            historical_data.get('avg_loss_per_event', 0.0),
            historical_data.get('max_drawdown', 0.0),
            historical_data.get('recovery_time_avg', 0.0),
            historical_data.get('volatility_30d', 0.0),
            historical_data.get('volatility_90d', 0.0),
            historical_data.get('correlation_to_market', 0.0),
            historical_data.get('beta', 0.0),
            historical_data.get('tracking_error', 0.0),
            historical_data.get('information_ratio', 0.0)
        ]
        
        return np.array(feature_list, dtype=np.float32)
    
    def _extract_counterparty_features(self, features: Dict) -> np.ndarray:
        """Extract counterparty relationship features."""
        counterparty_data = features.get('counterparty', {})
        
        feature_list = [
            counterparty_data.get('num_counterparties', 0),
            counterparty_data.get('avg_credit_score', 0.0),
            counterparty_data.get('total_exposure', 0.0),
            counterparty_data.get('max_single_exposure', 0.0),
            counterparty_data.get('network_centrality', 0.0),
            counterparty_data.get('clustering_coefficient', 0.0),
            counterparty_data.get('systemic_importance', 0.0),
            counterparty_data.get('contagion_risk', 0.0),
            counterparty_data.get('default_correlation', 0.0),
            counterparty_data.get('recovery_rate', 0.0)
        ]
        
        return np.array(feature_list, dtype=np.float32)
    
    def _extract_market_features(self, features: Dict) -> np.ndarray:
        """Extract market condition features."""
        market_data = features.get('market', {})
        
        feature_list = [
            market_data.get('vix_level', 0.0),
            market_data.get('market_return', 0.0),
            market_data.get('interest_rate', 0.0),
            market_data.get('credit_spread', 0.0),
            market_data.get('liquidity_index', 0.0),
            market_data.get('sentiment_score', 0.0),
            market_data.get('volatility_regime', 0.0),
            market_data.get('correlation_regime', 0.0),
            market_data.get('stress_indicator', 0.0),
            market_data.get('macro_factor', 0.0)
        ]
        
        return np.array(feature_list, dtype=np.float32)
    
    def _reduce_dimensions(self, features: np.ndarray, target_dim: int) -> np.ndarray:
        """Reduce feature dimensions using PCA-like approach."""
        if len(features) <= target_dim:
            # Pad if needed
            return np.pad(features, (0, target_dim - len(features)), mode='constant')
        else:
            # Simple binning for dimension reduction
            bin_size = len(features) // target_dim
            reduced = np.array([
                np.mean(features[i*bin_size:(i+1)*bin_size])
                for i in range(target_dim)
            ])
            return reduced
    
    def _generate_signature(self, dna_vector: np.ndarray) -> str:
        """Generate unique signature hash for DNA vector."""
        # Convert to bytes and hash
        vector_bytes = dna_vector.tobytes()
        signature = hashlib.sha256(vector_bytes).hexdigest()[:16]
        return signature
    
    def batch_generate(self, entities: List[Tuple[str, Dict]]) -> List[RiskDNA]:
        """
        Generate Risk DNA for multiple entities.
        
        Args:
            entities: List of (entity_id, features) tuples
            
        Returns:
            List of RiskDNA objects
        """
        dna_list = []
        for entity_id, features in entities:
            dna = self.generate(entity_id, features)
            dna_list.append(dna)
        
        logger.info(f"Generated {len(dna_list)} Risk DNAs")
        return dna_list


class PortfolioRiskDNA(RiskDNAGenerator):
    """
    Specialized DNA generator for portfolios.
    """
    
    def __init__(self, dna_dim: int = 256):
        super().__init__(dna_dim, use_neural_encoder=True)
    
    def generate_from_holdings(self, portfolio_id: str,
                               holdings: List[Dict],
                               market_data: Dict) -> RiskDNA:
        """
        Generate Risk DNA from portfolio holdings.
        
        Args:
            portfolio_id: Portfolio identifier
            holdings: List of holdings with positions
            market_data: Current market data
            
        Returns:
            RiskDNA for portfolio
        """
        # Aggregate portfolio features
        total_value = sum(h.get('value', 0) for h in holdings)
        num_positions = len(holdings)
        
        # Compute concentration (HHI)
        weights = [h.get('value', 0) / total_value for h in holdings if total_value > 0]
        hhi = sum(w**2 for w in weights) if weights else 0
        
        # Compute sector diversity
        sectors = set(h.get('sector', 'unknown') for h in holdings)
        sector_diversity = len(sectors) / max(num_positions, 1)
        
        features = {
            'portfolio': {
                'total_value': total_value,
                'num_positions': num_positions,
                'concentration_hhi': hhi,
                'sector_diversity': sector_diversity,
                'avg_position_size': total_value / max(num_positions, 1)
            },
            'market': market_data,
            'historical': {},
            'counterparty': {}
        }
        
        return self.generate(portfolio_id, features)


class TransactionRiskDNA(RiskDNAGenerator):
    """
    Specialized DNA generator for transactions.
    """
    
    def __init__(self, dna_dim: int = 128):
        super().__init__(dna_dim, use_neural_encoder=True)
    
    def generate_from_transaction(self, transaction_id: str,
                                  transaction_data: Dict) -> RiskDNA:
        """
        Generate Risk DNA from transaction data.
        
        Args:
            transaction_id: Transaction identifier
            transaction_data: Transaction details
            
        Returns:
            RiskDNA for transaction
        """
        features = {
            'portfolio': {
                'total_value': transaction_data.get('amount', 0),
                'num_positions': 1,
                'leverage_ratio': transaction_data.get('leverage', 1.0)
            },
            'counterparty': {
                'num_counterparties': 2,  # Buyer and seller
                'total_exposure': transaction_data.get('amount', 0)
            },
            'market': transaction_data.get('market_conditions', {}),
            'historical': {}
        }
        
        metadata = {
            'transaction_type': transaction_data.get('type'),
            'asset_class': transaction_data.get('asset_class'),
            'timestamp': transaction_data.get('timestamp')
        }
        
        return self.generate(transaction_id, features, metadata)


if __name__ == '__main__':
    # Example usage
    print("Risk DNA Generator Module")
    
    # Create generator
    generator = RiskDNAGenerator(dna_dim=256)
    
    # Sample features
    features = {
        'portfolio': {
            'total_value': 1000000,
            'num_positions': 50,
            'concentration_hhi': 0.15,
            'var_95': 50000
        },
        'historical': {
            'num_risk_events': 3,
            'max_drawdown': 0.15,
            'volatility_30d': 0.20
        },
        'counterparty': {
            'num_counterparties': 10,
            'avg_credit_score': 750,
            'network_centrality': 0.6
        },
        'market': {
            'vix_level': 18.5,
            'market_return': 0.08,
            'interest_rate': 0.045
        }
    }
    
    # Generate DNA
    dna = generator.generate('ENTITY_001', features)
    
    print(f"Generated Risk DNA:")
    print(f"  Entity ID: {dna.entity_id}")
    print(f"  DNA Vector Shape: {dna.dna_vector.shape}")
    print(f"  Signature: {dna.signature}")
    print(f"  Components: {dna.components}")

# Made with Bob
