"""
Quantum Utility Functions for Risk Optimization
Provides Pauli matrices, state preparation, and quantum circuit utilities.
"""

import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PauliMatrices:
    """Pauli matrix operations for quantum simulations."""
    
    @staticmethod
    def pauli_x(n_qubits: int = 1) -> np.ndarray:
        """
        Generate Pauli X matrix.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            Pauli X matrix
        """
        if n_qubits == 1:
            return np.array([[0, 1], [1, 0]], dtype=complex)
        else:
            # Tensor product for multiple qubits
            X = PauliMatrices.pauli_x(1)
            result = X
            for _ in range(n_qubits - 1):
                result = np.kron(result, X)
            return result
    
    @staticmethod
    def pauli_y(n_qubits: int = 1) -> np.ndarray:
        """
        Generate Pauli Y matrix.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            Pauli Y matrix
        """
        if n_qubits == 1:
            return np.array([[0, -1j], [1j, 0]], dtype=complex)
        else:
            Y = PauliMatrices.pauli_y(1)
            result = Y
            for _ in range(n_qubits - 1):
                result = np.kron(result, Y)
            return result
    
    @staticmethod
    def pauli_z(n_qubits: int = 1) -> np.ndarray:
        """
        Generate Pauli Z matrix.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            Pauli Z matrix
        """
        if n_qubits == 1:
            return np.array([[1, 0], [0, -1]], dtype=complex)
        else:
            Z = PauliMatrices.pauli_z(1)
            result = Z
            for _ in range(n_qubits - 1):
                result = np.kron(result, Z)
            return result
    
    @staticmethod
    def identity(n_qubits: int = 1) -> np.ndarray:
        """
        Generate identity matrix.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            Identity matrix
        """
        dim = 2 ** n_qubits
        return np.eye(dim, dtype=complex)


class StatePreparation:
    """Quantum state preparation utilities."""
    
    @staticmethod
    def uniform_superposition(n_qubits: int) -> np.ndarray:
        """
        Create uniform superposition state |+⟩^⊗n.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            State vector in uniform superposition
        """
        dim = 2 ** n_qubits
        return np.ones(dim, dtype=complex) / np.sqrt(dim)
    
    @staticmethod
    def computational_basis(n_qubits: int, state: int) -> np.ndarray:
        """
        Create computational basis state |state⟩.
        
        Args:
            n_qubits: Number of qubits
            state: Integer representing the basis state
            
        Returns:
            State vector
        """
        dim = 2 ** n_qubits
        vec = np.zeros(dim, dtype=complex)
        vec[state] = 1.0
        return vec
    
    @staticmethod
    def random_state(n_qubits: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Create random quantum state (Haar random).
        
        Args:
            n_qubits: Number of qubits
            seed: Random seed
            
        Returns:
            Random state vector
        """
        if seed is not None:
            np.random.seed(seed)
        
        dim = 2 ** n_qubits
        
        # Generate random complex vector
        real_part = np.random.randn(dim)
        imag_part = np.random.randn(dim)
        state = real_part + 1j * imag_part
        
        # Normalize
        state = state / np.linalg.norm(state)
        
        return state
    
    @staticmethod
    def ghz_state(n_qubits: int) -> np.ndarray:
        """
        Create GHZ (Greenberger-Horne-Zeilinger) state.
        |GHZ⟩ = (|00...0⟩ + |11...1⟩) / √2
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            GHZ state vector
        """
        dim = 2 ** n_qubits
        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0 / np.sqrt(2)  # |00...0⟩
        state[-1] = 1.0 / np.sqrt(2)  # |11...1⟩
        return state


class QuantumGates:
    """Common quantum gate operations."""
    
    @staticmethod
    def hadamard(n_qubits: int = 1) -> np.ndarray:
        """
        Generate Hadamard gate.
        
        Args:
            n_qubits: Number of qubits
            
        Returns:
            Hadamard matrix
        """
        if n_qubits == 1:
            return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        else:
            H = QuantumGates.hadamard(1)
            result = H
            for _ in range(n_qubits - 1):
                result = np.kron(result, H)
            return result
    
    @staticmethod
    def rotation_x(theta: float) -> np.ndarray:
        """
        Generate X rotation gate.
        
        Args:
            theta: Rotation angle
            
        Returns:
            Rotation matrix
        """
        return np.array([
            [np.cos(theta/2), -1j * np.sin(theta/2)],
            [-1j * np.sin(theta/2), np.cos(theta/2)]
        ], dtype=complex)
    
    @staticmethod
    def rotation_y(theta: float) -> np.ndarray:
        """
        Generate Y rotation gate.
        
        Args:
            theta: Rotation angle
            
        Returns:
            Rotation matrix
        """
        return np.array([
            [np.cos(theta/2), -np.sin(theta/2)],
            [np.sin(theta/2), np.cos(theta/2)]
        ], dtype=complex)
    
    @staticmethod
    def rotation_z(theta: float) -> np.ndarray:
        """
        Generate Z rotation gate.
        
        Args:
            theta: Rotation angle
            
        Returns:
            Rotation matrix
        """
        return np.array([
            [np.exp(-1j * theta/2), 0],
            [0, np.exp(1j * theta/2)]
        ], dtype=complex)
    
    @staticmethod
    def phase_gate(phi: float) -> np.ndarray:
        """
        Generate phase gate.
        
        Args:
            phi: Phase angle
            
        Returns:
            Phase gate matrix
        """
        return np.array([
            [1, 0],
            [0, np.exp(1j * phi)]
        ], dtype=complex)


class QuantumMeasurement:
    """Quantum measurement utilities."""
    
    @staticmethod
    def measure_probabilities(state: np.ndarray) -> np.ndarray:
        """
        Calculate measurement probabilities from state.
        
        Args:
            state: Quantum state vector
            
        Returns:
            Probability distribution
        """
        return np.abs(state) ** 2
    
    @staticmethod
    def sample_measurements(state: np.ndarray, num_shots: int = 1000,
                          seed: Optional[int] = None) -> np.ndarray:
        """
        Sample measurement outcomes.
        
        Args:
            state: Quantum state vector
            num_shots: Number of measurements
            seed: Random seed
            
        Returns:
            Array of measurement outcomes
        """
        if seed is not None:
            np.random.seed(seed)
        
        probabilities = QuantumMeasurement.measure_probabilities(state)
        outcomes = np.random.choice(len(state), size=num_shots, p=probabilities)
        
        return outcomes
    
    @staticmethod
    def expectation_value(state: np.ndarray, operator: np.ndarray) -> float:
        """
        Calculate expectation value ⟨ψ|O|ψ⟩.
        
        Args:
            state: Quantum state vector
            operator: Observable operator
            
        Returns:
            Expectation value
        """
        return float(np.real(np.conj(state) @ operator @ state))
    
    @staticmethod
    def fidelity(state1: np.ndarray, state2: np.ndarray) -> float:
        """
        Calculate fidelity between two states.
        F = |⟨ψ₁|ψ₂⟩|²
        
        Args:
            state1: First state vector
            state2: Second state vector
            
        Returns:
            Fidelity (0 to 1)
        """
        overlap = np.abs(np.vdot(state1, state2))
        return float(overlap ** 2)


class QuantumCircuitSimulator:
    """Simple quantum circuit simulator."""
    
    def __init__(self, n_qubits: int):
        """
        Initialize simulator.
        
        Args:
            n_qubits: Number of qubits
        """
        self.n_qubits = n_qubits
        self.state = StatePreparation.computational_basis(n_qubits, 0)
        self.gates_applied = []
    
    def reset(self):
        """Reset to |0⟩^⊗n state."""
        self.state = StatePreparation.computational_basis(self.n_qubits, 0)
        self.gates_applied = []
    
    def apply_gate(self, gate: np.ndarray, name: str = "Gate"):
        """
        Apply gate to current state.
        
        Args:
            gate: Gate matrix
            name: Gate name for logging
        """
        self.state = gate @ self.state
        self.gates_applied.append(name)
    
    def apply_hadamard(self):
        """Apply Hadamard to all qubits."""
        H = QuantumGates.hadamard(self.n_qubits)
        self.apply_gate(H, "Hadamard")
    
    def apply_rotation_z(self, theta: float):
        """
        Apply Z rotation to all qubits.
        
        Args:
            theta: Rotation angle
        """
        Rz = QuantumGates.rotation_z(theta)
        # Apply to all qubits
        gate = Rz
        for _ in range(self.n_qubits - 1):
            gate = np.kron(gate, Rz)
        self.apply_gate(gate, f"Rz({theta:.3f})")
    
    def measure(self, num_shots: int = 1000) -> dict:
        """
        Measure all qubits.
        
        Args:
            num_shots: Number of measurements
            
        Returns:
            Dictionary of measurement counts
        """
        outcomes = QuantumMeasurement.sample_measurements(self.state, num_shots)
        
        # Count outcomes
        unique, counts = np.unique(outcomes, return_counts=True)
        
        # Convert to bitstrings
        results = {}
        for outcome, count in zip(unique, counts):
            bitstring = format(outcome, f'0{self.n_qubits}b')
            results[bitstring] = int(count)
        
        return results
    
    def get_statevector(self) -> np.ndarray:
        """Get current state vector."""
        return self.state.copy()


if __name__ == '__main__':
    # Example usage
    print("Quantum Utilities Demo\n")
    
    # Pauli matrices
    print("Pauli X matrix:")
    print(PauliMatrices.pauli_x())
    
    # State preparation
    print("\nUniform superposition (2 qubits):")
    state = StatePreparation.uniform_superposition(2)
    print(state)
    
    # Circuit simulation
    print("\nCircuit Simulation:")
    sim = QuantumCircuitSimulator(3)
    sim.apply_hadamard()
    sim.apply_rotation_z(np.pi / 4)
    
    measurements = sim.measure(num_shots=1000)
    print("Measurement results:")
    for bitstring, count in sorted(measurements.items()):
        print(f"  |{bitstring}⟩: {count} times ({count/10:.1f}%)")

# Made with Bob
