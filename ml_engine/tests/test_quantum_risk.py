"""
Unit tests for Quantum-Inspired Risk Optimization module.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from quantum_risk.qaoa_optimizer import QAOAOptimizer, PortfolioQAOAOptimizer
from quantum_risk.risk_hamiltonian import RiskHamiltonian
from quantum_risk.quantum_utils import (
    PauliMatrices, StatePreparation, QuantumGates,
    QuantumMeasurement, QuantumCircuitSimulator
)


class TestQAOAOptimizer:
    """Test QAOA optimizer functionality."""
    
    def test_initialization(self):
        """Test QAOA optimizer initialization."""
        optimizer = QAOAOptimizer(num_assets=4, p_layers=2, seed=42)
        
        assert optimizer.num_assets == 4
        assert optimizer.p_layers == 2
        assert len(optimizer.params) == 4  # 2 params per layer
    
    def test_parameter_initialization(self):
        """Test parameter initialization is within valid range."""
        optimizer = QAOAOptimizer(num_assets=3, p_layers=3, seed=42)
        
        # Parameters should be between 0 and 2π
        assert np.all(optimizer.params >= 0)
        assert np.all(optimizer.params <= 2 * np.pi)
    
    def test_pauli_x_matrix(self):
        """Test Pauli X matrix generation."""
        optimizer = QAOAOptimizer(num_assets=2, p_layers=1)
        
        X = optimizer._pauli_x_matrix(4)
        
        assert X.shape == (4, 4)
        assert np.allclose(X, X.conj().T)  # Should be Hermitian
    
    def test_measure_expectation(self):
        """Test expectation value measurement."""
        optimizer = QAOAOptimizer(num_assets=2, p_layers=1)
        
        # Simple state and Hamiltonian
        state = np.array([1, 0, 0, 0], dtype=complex)
        H = np.diag([1, 2, 3, 4])
        
        expectation = optimizer._measure_expectation(state, H)
        
        assert np.isclose(expectation, 1.0)
    
    def test_decode_solution(self):
        """Test bitstring to weights decoding."""
        optimizer = QAOAOptimizer(num_assets=4, p_layers=1)
        
        bitstring = "1010"
        weights = optimizer.decode_solution(bitstring)
        
        assert len(weights) == 4
        assert np.isclose(weights.sum(), 1.0)
        assert weights[0] > 0 and weights[2] > 0
        assert weights[1] == 0 and weights[3] == 0


class TestPortfolioQAOAOptimizer:
    """Test portfolio-specific QAOA optimizer."""
    
    def test_initialization(self):
        """Test portfolio optimizer initialization."""
        returns = np.array([0.08, 0.12, 0.10])
        cov = np.eye(3) * 0.01
        
        optimizer = PortfolioQAOAOptimizer(returns, cov, risk_aversion=1.0)
        
        assert optimizer.num_assets == 3
        assert np.array_equal(optimizer.returns, returns)
    
    def test_hamiltonian_construction(self):
        """Test Hamiltonian construction."""
        returns = np.array([0.08, 0.12])
        cov = np.eye(2) * 0.01
        
        optimizer = PortfolioQAOAOptimizer(returns, cov)
        H = optimizer._construct_hamiltonian()
        
        assert H.shape == (4, 4)  # 2^2 states
        assert np.allclose(H, H.conj().T)  # Should be Hermitian
    
    def test_optimize_portfolio_shape(self):
        """Test portfolio optimization returns correct shapes."""
        np.random.seed(42)
        returns = np.array([0.08, 0.12, 0.10])
        cov = np.eye(3) * 0.01
        
        optimizer = PortfolioQAOAOptimizer(returns, cov, p_layers=1)
        results = optimizer.optimize_portfolio(max_iter=10, num_samples=100)
        
        assert 'optimal_weights' in results
        assert len(results['optimal_weights']) == 3
        assert 'portfolio_return' in results
        assert 'portfolio_std' in results
        assert 'sharpe_ratio' in results


class TestRiskHamiltonian:
    """Test Risk Hamiltonian construction."""
    
    def test_initialization(self):
        """Test Hamiltonian builder initialization."""
        builder = RiskHamiltonian(num_assets=3)
        
        assert builder.num_assets == 3
        assert builder.dim == 8  # 2^3
    
    def test_portfolio_variance_hamiltonian(self):
        """Test variance Hamiltonian construction."""
        builder = RiskHamiltonian(num_assets=2)
        cov = np.array([[0.01, 0.005], [0.005, 0.02]])
        
        H = builder.portfolio_variance_hamiltonian(cov)
        
        assert H.shape == (4, 4)
        assert np.all(np.diag(H) >= 0)  # Variance is non-negative
    
    def test_mean_variance_hamiltonian(self):
        """Test mean-variance Hamiltonian."""
        builder = RiskHamiltonian(num_assets=2)
        returns = np.array([0.08, 0.12])
        cov = np.eye(2) * 0.01
        
        H = builder.mean_variance_hamiltonian(returns, cov, risk_aversion=1.0)
        
        assert H.shape == (4, 4)
        assert np.allclose(H, H.conj().T)
    
    def test_concentration_risk_hamiltonian(self):
        """Test concentration risk Hamiltonian."""
        builder = RiskHamiltonian(num_assets=3)
        
        H = builder.concentration_risk_hamiltonian(max_weight=0.5)
        
        assert H.shape == (8, 8)
        assert np.all(np.diag(H) >= 0)
    
    def test_combined_hamiltonian(self):
        """Test combined Hamiltonian with multiple factors."""
        builder = RiskHamiltonian(num_assets=2)
        returns = np.array([0.08, 0.12])
        cov = np.eye(2) * 0.01
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        liquidity = np.array([0.9, 0.8])
        
        H = builder.combined_risk_hamiltonian(returns, cov, corr, liquidity)
        
        assert H.shape == (4, 4)
        assert np.allclose(H, H.conj().T)
    
    def test_tune_parameters(self):
        """Test parameter tuning."""
        builder = RiskHamiltonian(num_assets=3)
        returns = np.array([0.08, 0.10, 0.12])
        cov = np.eye(3) * 0.01
        
        params = builder.tune_parameters(returns, cov)
        
        assert 'risk_aversion' in params
        assert 'target_return' in params
        assert 'target_risk' in params
        assert params['risk_aversion'] > 0


class TestPauliMatrices:
    """Test Pauli matrix operations."""
    
    def test_pauli_x(self):
        """Test Pauli X matrix."""
        X = PauliMatrices.pauli_x()
        
        expected = np.array([[0, 1], [1, 0]])
        assert np.array_equal(X, expected)
    
    def test_pauli_y(self):
        """Test Pauli Y matrix."""
        Y = PauliMatrices.pauli_y()
        
        assert Y.shape == (2, 2)
        assert np.allclose(Y @ Y, np.eye(2))  # Y^2 = I
    
    def test_pauli_z(self):
        """Test Pauli Z matrix."""
        Z = PauliMatrices.pauli_z()
        
        expected = np.array([[1, 0], [0, -1]])
        assert np.array_equal(Z, expected)
    
    def test_identity(self):
        """Test identity matrix."""
        I = PauliMatrices.identity(n_qubits=2)
        
        assert I.shape == (4, 4)
        assert np.array_equal(I, np.eye(4))


class TestStatePreparation:
    """Test quantum state preparation."""
    
    def test_uniform_superposition(self):
        """Test uniform superposition state."""
        state = StatePreparation.uniform_superposition(n_qubits=2)
        
        assert len(state) == 4
        assert np.isclose(np.linalg.norm(state), 1.0)
        assert np.allclose(np.abs(state), 0.5)  # Equal amplitudes
    
    def test_computational_basis(self):
        """Test computational basis state."""
        state = StatePreparation.computational_basis(n_qubits=2, state=2)
        
        assert len(state) == 4
        assert state[2] == 1.0
        assert np.sum(np.abs(state)) == 1.0
    
    def test_random_state_normalized(self):
        """Test random state is normalized."""
        state = StatePreparation.random_state(n_qubits=3, seed=42)
        
        assert len(state) == 8
        assert np.isclose(np.linalg.norm(state), 1.0)
    
    def test_ghz_state(self):
        """Test GHZ state."""
        state = StatePreparation.ghz_state(n_qubits=2)
        
        assert len(state) == 4
        assert np.isclose(np.abs(state[0]), 1/np.sqrt(2))
        assert np.isclose(np.abs(state[3]), 1/np.sqrt(2))
        assert np.isclose(state[1], 0)
        assert np.isclose(state[2], 0)


class TestQuantumGates:
    """Test quantum gate operations."""
    
    def test_hadamard(self):
        """Test Hadamard gate."""
        H = QuantumGates.hadamard()
        
        assert H.shape == (2, 2)
        # H^2 = I
        assert np.allclose(H @ H, np.eye(2))
    
    def test_rotation_x(self):
        """Test X rotation gate."""
        Rx = QuantumGates.rotation_x(np.pi)
        
        assert Rx.shape == (2, 2)
        # Rx(π) ≈ -iX
        X = PauliMatrices.pauli_x()
        assert np.allclose(Rx, -1j * X, atol=1e-10)
    
    def test_rotation_z(self):
        """Test Z rotation gate."""
        Rz = QuantumGates.rotation_z(np.pi/2)
        
        assert Rz.shape == (2, 2)
        assert np.allclose(Rz @ Rz.conj().T, np.eye(2))  # Unitary
    
    def test_phase_gate(self):
        """Test phase gate."""
        P = QuantumGates.phase_gate(np.pi/4)
        
        assert P.shape == (2, 2)
        assert P[0, 0] == 1
        assert np.isclose(np.abs(P[1, 1]), 1)


class TestQuantumMeasurement:
    """Test quantum measurement utilities."""
    
    def test_measure_probabilities(self):
        """Test probability calculation."""
        state = np.array([1, 0, 0, 0], dtype=complex)
        probs = QuantumMeasurement.measure_probabilities(state)
        
        assert len(probs) == 4
        assert np.isclose(probs[0], 1.0)
        assert np.isclose(probs.sum(), 1.0)
    
    def test_sample_measurements(self):
        """Test measurement sampling."""
        state = StatePreparation.uniform_superposition(2)
        outcomes = QuantumMeasurement.sample_measurements(state, num_shots=1000, seed=42)
        
        assert len(outcomes) == 1000
        assert np.all(outcomes >= 0) and np.all(outcomes < 4)
    
    def test_expectation_value(self):
        """Test expectation value calculation."""
        state = np.array([1, 0], dtype=complex)
        Z = PauliMatrices.pauli_z()
        
        exp_val = QuantumMeasurement.expectation_value(state, Z)
        
        assert np.isclose(exp_val, 1.0)
    
    def test_fidelity(self):
        """Test fidelity calculation."""
        state1 = np.array([1, 0], dtype=complex)
        state2 = np.array([1, 0], dtype=complex)
        
        fid = QuantumMeasurement.fidelity(state1, state2)
        
        assert np.isclose(fid, 1.0)
    
    def test_fidelity_orthogonal(self):
        """Test fidelity of orthogonal states."""
        state1 = np.array([1, 0], dtype=complex)
        state2 = np.array([0, 1], dtype=complex)
        
        fid = QuantumMeasurement.fidelity(state1, state2)
        
        assert np.isclose(fid, 0.0)


class TestQuantumCircuitSimulator:
    """Test quantum circuit simulator."""
    
    def test_initialization(self):
        """Test simulator initialization."""
        sim = QuantumCircuitSimulator(n_qubits=2)
        
        assert sim.n_qubits == 2
        assert len(sim.state) == 4
        assert sim.state[0] == 1.0  # Starts in |00⟩
    
    def test_reset(self):
        """Test circuit reset."""
        sim = QuantumCircuitSimulator(n_qubits=2)
        sim.apply_hadamard()
        sim.reset()
        
        assert sim.state[0] == 1.0
        assert len(sim.gates_applied) == 0
    
    def test_apply_hadamard(self):
        """Test Hadamard application."""
        sim = QuantumCircuitSimulator(n_qubits=1)
        sim.apply_hadamard()
        
        # After H on |0⟩, should be in |+⟩
        assert np.isclose(np.abs(sim.state[0]), 1/np.sqrt(2))
        assert np.isclose(np.abs(sim.state[1]), 1/np.sqrt(2))
    
    def test_measure(self):
        """Test measurement."""
        sim = QuantumCircuitSimulator(n_qubits=2)
        sim.apply_hadamard()
        
        results = sim.measure(num_shots=1000)
        
        assert isinstance(results, dict)
        assert sum(results.values()) == 1000
        # Should have roughly equal distribution
        assert len(results) > 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

# Made with Bob
