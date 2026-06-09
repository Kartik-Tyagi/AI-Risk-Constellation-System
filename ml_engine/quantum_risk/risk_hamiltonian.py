"""
Risk Hamiltonian Construction for Quantum-Inspired Risk Optimization
Defines various Hamiltonian formulations for different risk optimization problems.
"""

import numpy as np
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class RiskHamiltonian:
    """
    Constructs Hamiltonians for various risk optimization problems.
    """
    
    def __init__(self, num_assets: int):
        """
        Initialize Risk Hamiltonian builder.
        
        Args:
            num_assets: Number of assets in the problem
        """
        self.num_assets = num_assets
        self.dim = 2 ** num_assets
    
    def portfolio_variance_hamiltonian(self, covariance: np.ndarray, 
                                      penalty: float = 1.0) -> np.ndarray:
        """
        Construct Hamiltonian for portfolio variance minimization.
        
        Args:
            covariance: Covariance matrix of asset returns
            penalty: Penalty for empty portfolio
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                variance = weights @ covariance @ weights
                H[i, i] = variance
            else:
                H[i, i] = penalty
        
        return H
    
    def mean_variance_hamiltonian(self, returns: np.ndarray, 
                                 covariance: np.ndarray,
                                 risk_aversion: float = 1.0,
                                 penalty: float = 1.0) -> np.ndarray:
        """
        Construct mean-variance optimization Hamiltonian.
        Objective: risk_aversion * variance - expected_return
        
        Args:
            returns: Expected returns for each asset
            covariance: Covariance matrix
            risk_aversion: Risk aversion parameter
            penalty: Penalty for empty portfolio
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                
                portfolio_return = np.dot(weights, returns)
                portfolio_variance = weights @ covariance @ weights
                
                # Objective: minimize risk - return
                H[i, i] = risk_aversion * portfolio_variance - portfolio_return
            else:
                H[i, i] = penalty
        
        return H
    
    def concentration_risk_hamiltonian(self, max_weight: float = 0.2,
                                      penalty: float = 10.0) -> np.ndarray:
        """
        Construct Hamiltonian penalizing concentration risk.
        
        Args:
            max_weight: Maximum allowed weight per asset
            penalty: Penalty multiplier for violations
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                
                # Penalize weights exceeding max_weight
                violations = np.maximum(0, weights - max_weight)
                concentration_penalty = penalty * np.sum(violations ** 2)
                
                H[i, i] = concentration_penalty
            else:
                H[i, i] = penalty
        
        return H
    
    def correlation_penalty_hamiltonian(self, correlation: np.ndarray,
                                       penalty_weight: float = 1.0) -> np.ndarray:
        """
        Construct Hamiltonian penalizing high correlations.
        Encourages diversification by penalizing correlated assets.
        
        Args:
            correlation: Correlation matrix
            penalty_weight: Weight for correlation penalty
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                
                # Calculate weighted correlation
                weighted_corr = 0
                for j in range(self.num_assets):
                    for k in range(j + 1, self.num_assets):
                        weighted_corr += weights[j] * weights[k] * abs(correlation[j, k])
                
                H[i, i] = penalty_weight * weighted_corr
            else:
                H[i, i] = penalty_weight
        
        return H
    
    def liquidity_risk_hamiltonian(self, liquidity_scores: np.ndarray,
                                  penalty_weight: float = 1.0) -> np.ndarray:
        """
        Construct Hamiltonian for liquidity risk.
        Lower liquidity scores = higher penalty.
        
        Args:
            liquidity_scores: Liquidity score for each asset (0-1)
            penalty_weight: Weight for liquidity penalty
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                
                # Penalize illiquid assets
                illiquidity_penalty = np.sum(weights * (1 - liquidity_scores))
                H[i, i] = penalty_weight * illiquidity_penalty
            else:
                H[i, i] = penalty_weight
        
        return H
    
    def combined_risk_hamiltonian(self, 
                                 returns: np.ndarray,
                                 covariance: np.ndarray,
                                 correlation: np.ndarray,
                                 liquidity_scores: np.ndarray,
                                 weights_dict: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Construct combined Hamiltonian with multiple risk factors.
        
        Args:
            returns: Expected returns
            covariance: Covariance matrix
            correlation: Correlation matrix
            liquidity_scores: Liquidity scores
            weights_dict: Dictionary of weights for each component
                - 'variance': Weight for variance term
                - 'return': Weight for return term
                - 'concentration': Weight for concentration penalty
                - 'correlation': Weight for correlation penalty
                - 'liquidity': Weight for liquidity penalty
                
        Returns:
            Combined Hamiltonian matrix
        """
        if weights_dict is None:
            weights_dict = {
                'variance': 1.0,
                'return': 1.0,
                'concentration': 0.5,
                'correlation': 0.3,
                'liquidity': 0.2
            }
        
        # Construct individual Hamiltonians
        H_variance = self.portfolio_variance_hamiltonian(covariance)
        H_return = self._return_hamiltonian(returns)
        H_concentration = self.concentration_risk_hamiltonian()
        H_correlation = self.correlation_penalty_hamiltonian(correlation)
        H_liquidity = self.liquidity_risk_hamiltonian(liquidity_scores)
        
        # Combine with weights
        H_combined = (
            weights_dict['variance'] * H_variance -
            weights_dict['return'] * H_return +
            weights_dict['concentration'] * H_concentration +
            weights_dict['correlation'] * H_correlation +
            weights_dict['liquidity'] * H_liquidity
        )
        
        logger.info(f"Constructed combined Hamiltonian with {len(weights_dict)} components")
        
        return H_combined
    
    def _return_hamiltonian(self, returns: np.ndarray) -> np.ndarray:
        """
        Construct Hamiltonian for expected returns (to be maximized).
        
        Args:
            returns: Expected returns for each asset
            
        Returns:
            Hamiltonian matrix
        """
        H = np.zeros((self.dim, self.dim))
        
        for i in range(self.dim):
            weights = self._bitstring_to_weights(i)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                portfolio_return = np.dot(weights, returns)
                H[i, i] = portfolio_return
            else:
                H[i, i] = 0
        
        return H
    
    def _bitstring_to_weights(self, index: int) -> np.ndarray:
        """
        Convert integer index to binary weights array.
        
        Args:
            index: Integer index
            
        Returns:
            Binary weights array
        """
        bitstring = format(index, f'0{self.num_assets}b')
        return np.array([int(b) for b in bitstring], dtype=float)
    
    def tune_parameters(self, returns: np.ndarray, covariance: np.ndarray,
                       target_return: Optional[float] = None,
                       target_risk: Optional[float] = None) -> Dict[str, float]:
        """
        Automatically tune Hamiltonian parameters based on targets.
        
        Args:
            returns: Expected returns
            covariance: Covariance matrix
            target_return: Target portfolio return
            target_risk: Target portfolio risk (std dev)
            
        Returns:
            Dictionary of tuned parameters
        """
        # Calculate market statistics
        avg_return = np.mean(returns)
        avg_risk = np.mean(np.sqrt(np.diag(covariance)))
        
        # Set defaults if not provided
        if target_return is None:
            target_return = float(avg_return * 1.2)  # 20% above average
        
        if target_risk is None:
            target_risk = float(avg_risk * 0.8)  # 20% below average
        
        # Calculate risk aversion parameter
        risk_aversion = float(target_return / (target_risk ** 2)) if target_risk > 0 else 1.0
        
        params = {
            'risk_aversion': risk_aversion,
            'concentration_penalty': 0.5,
            'correlation_penalty': 0.3,
            'liquidity_penalty': 0.2,
            'target_return': target_return,
            'target_risk': target_risk
        }
        
        logger.info(f"Tuned parameters: risk_aversion={risk_aversion:.4f}")
        
        return params


if __name__ == '__main__':
    # Example usage
    np.random.seed(42)
    
    num_assets = 4
    returns = np.array([0.08, 0.12, 0.10, 0.15])
    
    # Generate covariance matrix
    A = np.random.randn(num_assets, num_assets)
    covariance = A @ A.T / num_assets
    
    # Generate correlation matrix
    std_devs = np.sqrt(np.diag(covariance))
    correlation = covariance / np.outer(std_devs, std_devs)
    
    # Liquidity scores
    liquidity_scores = np.array([0.9, 0.7, 0.8, 0.6])
    
    # Build Hamiltonian
    hamiltonian_builder = RiskHamiltonian(num_assets)
    
    # Mean-variance Hamiltonian
    H_mv = hamiltonian_builder.mean_variance_hamiltonian(returns, covariance, risk_aversion=1.0)
    print(f"Mean-Variance Hamiltonian shape: {H_mv.shape}")
    print(f"Diagonal values (first 5): {np.diag(H_mv)[:5]}")
    
    # Combined Hamiltonian
    H_combined = hamiltonian_builder.combined_risk_hamiltonian(
        returns, covariance, correlation, liquidity_scores
    )
    print(f"\nCombined Hamiltonian shape: {H_combined.shape}")
    print(f"Diagonal values (first 5): {np.diag(H_combined)[:5]}")
    
    # Tune parameters
    params = hamiltonian_builder.tune_parameters(returns, covariance)
    print(f"\nTuned parameters: {params}")

# Made with Bob
