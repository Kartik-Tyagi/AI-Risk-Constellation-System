"""
QAOA-Style Quantum-Inspired Optimizer for Portfolio Risk Optimization
Implements a quantum-inspired annealing simulation for portfolio optimization.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAOAOptimizer:
    """
    Quantum Approximate Optimization Algorithm (QAOA) inspired optimizer.
    Uses variational quantum eigensolver approach for portfolio risk optimization.
    """
    
    def __init__(self, num_assets: int, p_layers: int = 3, seed: Optional[int] = None):
        """
        Initialize QAOA optimizer.
        
        Args:
            num_assets: Number of assets in portfolio
            p_layers: Number of QAOA layers (depth)
            seed: Random seed for reproducibility
        """
        self.num_assets = num_assets
        self.p_layers = p_layers
        self.seed = seed
        
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize parameters (gamma and beta for each layer)
        self.params = self._initialize_parameters()
        
        logger.info(f"Initialized QAOA optimizer with {num_assets} assets and {p_layers} layers")
    
    def _initialize_parameters(self) -> np.ndarray:
        """Initialize QAOA parameters randomly."""
        # 2 parameters per layer (gamma and beta)
        return np.random.uniform(0, 2*np.pi, 2 * self.p_layers)
    
    def _apply_mixer_hamiltonian(self, state: np.ndarray, beta: float) -> np.ndarray:
        """
        Apply mixer Hamiltonian (X rotations).
        
        Args:
            state: Current quantum state
            beta: Rotation angle
            
        Returns:
            Updated state after mixer
        """
        # Simulate X rotation on each qubit
        rotation_matrix = np.cos(beta) * np.eye(len(state)) + \
                         1j * np.sin(beta) * self._pauli_x_matrix(len(state))
        return rotation_matrix @ state
    
    def _pauli_x_matrix(self, dim: int) -> np.ndarray:
        """Generate Pauli X matrix for given dimension."""
        # Simplified Pauli X for simulation
        matrix = np.zeros((dim, dim), dtype=complex)
        for i in range(dim):
            j = (i + 1) % dim
            matrix[i, j] = 1
            matrix[j, i] = 1
        return matrix
    
    def _apply_problem_hamiltonian(self, state: np.ndarray, gamma: float, 
                                   hamiltonian_matrix: np.ndarray) -> np.ndarray:
        """
        Apply problem Hamiltonian (Z rotations based on cost function).
        
        Args:
            state: Current quantum state
            gamma: Rotation angle
            hamiltonian_matrix: Problem Hamiltonian matrix
            
        Returns:
            Updated state after problem Hamiltonian
        """
        # Apply phase based on Hamiltonian
        phase_matrix = np.exp(-1j * gamma * hamiltonian_matrix)
        return phase_matrix @ state
    
    def _measure_expectation(self, state: np.ndarray, 
                            hamiltonian_matrix: np.ndarray) -> float:
        """
        Measure expectation value of Hamiltonian.
        
        Args:
            state: Quantum state
            hamiltonian_matrix: Hamiltonian matrix
            
        Returns:
            Expectation value
        """
        return float(np.real(np.conj(state) @ hamiltonian_matrix @ state))
    
    def _qaoa_circuit(self, params: np.ndarray, 
                     hamiltonian_matrix: np.ndarray) -> float:
        """
        Execute QAOA circuit and return expectation value.
        
        Args:
            params: QAOA parameters [gamma_1, beta_1, ..., gamma_p, beta_p]
            hamiltonian_matrix: Problem Hamiltonian
            
        Returns:
            Expectation value (cost)
        """
        # Initialize state in equal superposition
        dim = 2 ** self.num_assets
        state = np.ones(dim, dtype=complex) / np.sqrt(dim)
        
        # Apply QAOA layers
        for layer in range(self.p_layers):
            gamma = params[2 * layer]
            beta = params[2 * layer + 1]
            
            # Apply problem Hamiltonian
            state = self._apply_problem_hamiltonian(state, gamma, hamiltonian_matrix)
            
            # Apply mixer Hamiltonian
            state = self._apply_mixer_hamiltonian(state, beta)
        
        # Measure expectation
        return self._measure_expectation(state, hamiltonian_matrix)
    
    def optimize(self, hamiltonian_matrix: np.ndarray, 
                max_iter: int = 100) -> Tuple[np.ndarray, float]:
        """
        Optimize QAOA parameters to minimize expectation value.
        
        Args:
            hamiltonian_matrix: Problem Hamiltonian matrix
            max_iter: Maximum optimization iterations
            
        Returns:
            Tuple of (optimal_params, optimal_value)
        """
        logger.info("Starting QAOA optimization...")
        
        # Objective function
        def objective(params):
            return self._qaoa_circuit(params, hamiltonian_matrix)
        
        # Optimize using classical optimizer
        result = minimize(
            objective,
            self.params,
            method='COBYLA',
            options={'maxiter': max_iter}
        )
        
        self.params = result.x
        optimal_value = result.fun
        
        logger.info(f"Optimization complete. Optimal value: {optimal_value:.6f}")
        
        return self.params, optimal_value
    
    def sample_solution(self, params: np.ndarray, 
                       hamiltonian_matrix: np.ndarray,
                       num_samples: int = 1000) -> Dict[str, float]:
        """
        Sample solutions from optimized QAOA circuit.
        
        Args:
            params: Optimized QAOA parameters
            hamiltonian_matrix: Problem Hamiltonian
            num_samples: Number of samples to draw
            
        Returns:
            Dictionary of bitstrings and their probabilities
        """
        # Execute circuit to get final state
        dim = 2 ** self.num_assets
        state = np.ones(dim, dtype=complex) / np.sqrt(dim)
        
        for layer in range(self.p_layers):
            gamma = params[2 * layer]
            beta = params[2 * layer + 1]
            state = self._apply_problem_hamiltonian(state, gamma, hamiltonian_matrix)
            state = self._apply_mixer_hamiltonian(state, beta)
        
        # Calculate probabilities — normalise to guard against floating-point drift
        probabilities = np.abs(state) ** 2
        probabilities = probabilities / probabilities.sum()

        # Sample bitstrings
        samples = np.random.choice(dim, size=num_samples, p=probabilities)
        
        # Count occurrences
        unique, counts = np.unique(samples, return_counts=True)
        
        # Convert to bitstrings
        results = {}
        for idx, count in zip(unique, counts):
            bitstring = format(idx, f'0{self.num_assets}b')
            results[bitstring] = count / num_samples
        
        return results
    
    def decode_solution(self, bitstring: str) -> np.ndarray:
        """
        Decode bitstring to portfolio weights.
        
        Args:
            bitstring: Binary string representing solution
            
        Returns:
            Portfolio weights array
        """
        # Convert bitstring to weights (1 = include, 0 = exclude)
        weights = np.array([int(b) for b in bitstring], dtype=float)
        
        # Normalize to sum to 1
        if weights.sum() > 0:
            weights = weights / weights.sum()
        
        return weights


class PortfolioQAOAOptimizer:
    """
    Portfolio-specific QAOA optimizer that constructs appropriate Hamiltonians.
    """
    
    def __init__(self, returns: np.ndarray, covariance: np.ndarray, 
                 risk_aversion: float = 1.0, p_layers: int = 3):
        """
        Initialize portfolio QAOA optimizer.
        
        Args:
            returns: Expected returns for each asset
            covariance: Covariance matrix of returns
            risk_aversion: Risk aversion parameter (higher = more risk averse)
            p_layers: Number of QAOA layers
        """
        self.returns = returns
        self.covariance = covariance
        self.risk_aversion = risk_aversion
        self.num_assets = len(returns)
        
        self.qaoa = QAOAOptimizer(self.num_assets, p_layers)
        
        logger.info(f"Initialized Portfolio QAOA optimizer for {self.num_assets} assets")
    
    def _construct_hamiltonian(self) -> np.ndarray:
        """
        Construct portfolio optimization Hamiltonian.
        Minimizes: risk_aversion * variance - expected_return
        
        Returns:
            Hamiltonian matrix
        """
        dim = 2 ** self.num_assets
        H = np.zeros((dim, dim))
        
        # Iterate over all possible portfolio configurations
        for i in range(dim):
            # Convert index to bitstring (portfolio allocation)
            bitstring = format(i, f'0{self.num_assets}b')
            weights = np.array([int(b) for b in bitstring], dtype=float)
            
            if weights.sum() > 0:
                weights = weights / weights.sum()
                
                # Calculate portfolio return
                portfolio_return = np.dot(weights, self.returns)
                
                # Calculate portfolio variance
                portfolio_variance = weights @ self.covariance @ weights
                
                # Objective: minimize risk - return
                H[i, i] = self.risk_aversion * portfolio_variance - portfolio_return
            else:
                # Penalize empty portfolio
                H[i, i] = 1e6
        
        return H
    
    def optimize_portfolio(self, max_iter: int = 100, 
                          num_samples: int = 1000) -> Dict:
        """
        Optimize portfolio using QAOA.
        
        Args:
            max_iter: Maximum optimization iterations
            num_samples: Number of solution samples
            
        Returns:
            Dictionary with optimization results
        """
        logger.info("Constructing portfolio Hamiltonian...")
        hamiltonian = self._construct_hamiltonian()
        
        logger.info("Optimizing QAOA parameters...")
        optimal_params, optimal_value = self.qaoa.optimize(hamiltonian, max_iter)
        
        logger.info("Sampling solutions...")
        solutions = self.qaoa.sample_solution(optimal_params, hamiltonian, num_samples)
        
        # Get best solution
        best_bitstring = max(solutions.keys(), key=lambda k: solutions[k])
        best_weights = self.qaoa.decode_solution(best_bitstring)
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(best_weights, self.returns)
        portfolio_variance = best_weights @ self.covariance @ best_weights
        portfolio_std = np.sqrt(portfolio_variance)
        sharpe_ratio = portfolio_return / portfolio_std if portfolio_std > 0 else 0
        
        results = {
            'optimal_weights': best_weights,
            'portfolio_return': portfolio_return,
            'portfolio_std': portfolio_std,
            'portfolio_variance': portfolio_variance,
            'sharpe_ratio': sharpe_ratio,
            'optimal_value': optimal_value,
            'qaoa_params': optimal_params,
            'solution_distribution': solutions,
            'best_bitstring': best_bitstring
        }
        
        logger.info(f"Optimization complete:")
        logger.info(f"  Expected Return: {portfolio_return:.4f}")
        logger.info(f"  Risk (Std Dev): {portfolio_std:.4f}")
        logger.info(f"  Sharpe Ratio: {sharpe_ratio:.4f}")
        
        return results


if __name__ == '__main__':
    # Example usage
    np.random.seed(42)
    
    # Generate sample data
    num_assets = 5
    returns = np.random.uniform(0.05, 0.15, num_assets)
    
    # Generate covariance matrix
    A = np.random.randn(num_assets, num_assets)
    covariance = A @ A.T / num_assets
    
    # Optimize portfolio
    optimizer = PortfolioQAOAOptimizer(
        returns=returns,
        covariance=covariance,
        risk_aversion=1.0,
        p_layers=2
    )
    
    results = optimizer.optimize_portfolio(max_iter=50, num_samples=500)
    
    print("\nOptimal Portfolio Weights:")
    for i, weight in enumerate(results['optimal_weights']):
        print(f"  Asset {i}: {weight:.4f}")

# Made with Bob
