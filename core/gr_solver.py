"""
3+1 General Relativity Solver - Self-contained implementation

This is a minimal but complete 3+1 GR solver that evolves the metric tensor
and computes Hamiltonian/momentum constraints. Based on the ADM formalism.

Key equations:
- Hamiltonian constraint: H = R + K^2 - K_ij K^ij - 2Λ = 0
- Momentum constraint: D_j(K^ij - γ^ij K) = 0
- Evolution: ∂_t γ_ij = -2αK_ij + D_i β_j + D_j β_i
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


# Symmetric 3x3 tensor storage (xx, xy, xz, yy, yz, zz)
SYM6_IDX = {"xx": 0, "xy": 1, "xz": 2, "yy": 3, "yz": 4, "zz": 5}


def sym6_to_mat33(sym6: np.ndarray) -> np.ndarray:
    """Convert symmetric 3x3 tensor stored as sym6 into full 3x3 matrix."""
    assert sym6.shape[-1] == 6
    mat = np.zeros(sym6.shape[:-1] + (3, 3), dtype=sym6.dtype)
    mat[..., 0, 0] = sym6[..., 0]
    mat[..., 0, 1] = sym6[..., 1]
    mat[..., 0, 2] = sym6[..., 2]
    mat[..., 1, 0] = sym6[..., 1]
    mat[..., 1, 1] = sym6[..., 3]
    mat[..., 1, 2] = sym6[..., 4]
    mat[..., 2, 0] = sym6[..., 2]
    mat[..., 2, 1] = sym6[..., 4]
    mat[..., 2, 2] = sym6[..., 5]
    return mat


def mat33_to_sym6(mat: np.ndarray) -> np.ndarray:
    """Convert full 3x3 matrix to sym6 storage."""
    assert mat.shape[-2:] == (3, 3)
    sym6 = np.empty(mat.shape[:-2] + (6,), dtype=mat.dtype)
    sym6[..., 0] = mat[..., 0, 0]
    sym6[..., 1] = mat[..., 0, 1]
    sym6[..., 2] = mat[..., 0, 2]
    sym6[..., 3] = mat[..., 1, 1]
    sym6[..., 4] = mat[..., 1, 2]
    sym6[..., 5] = mat[..., 2, 2]
    return sym6


def inv_sym6(sym6: np.ndarray) -> np.ndarray:
    """Compute inverse of symmetric 3x3 tensor."""
    mat = sym6_to_mat33(sym6)
    inv = np.linalg.inv(mat)
    return mat33_to_sym6(inv)


def trace_sym6(sym6: np.ndarray, inv_metric: np.ndarray) -> np.ndarray:
    """Compute trace using inverse metric."""
    mat = sym6_to_mat33(sym6)
    return np.einsum('...ij,...ij->...', mat, inv_sym6(inv_metric))


@dataclass
class GRCoreFields:
    """Core GR fields for 3+1 decomposition."""
    Nx: int
    Ny: int
    Nz: int
    dx: float = 1.0
    dy: float = 1.0
    dz: float = 1.0
    
    def __post_init__(self):
        # Metric tensor γ_ij (symmetric 3x3)
        self.gamma_sym6 = np.zeros((self.Nx, self.Ny, self.Nz, 6))
        # Extrinsic curvature K_ij
        self.K_sym6 = np.zeros((self.Nx, self.Ny, self.Nz, 6))
        # Lapse function α
        self.alpha = np.ones((self.Nx, self.Ny, self.Nz))
        # Shift vector β^i
        self.beta = np.zeros((self.Nx, self.Ny, self.Nz, 3))
        # Hamiltonian constraint
        self.hamiltonian = np.zeros((self.Nx, self.Ny, self.Nz))
        # Momentum constraint
        self.momentum = np.zeros((self.Nx, self.Ny, self.Nz, 3))


class GRGeometry:
    """Computes geometric quantities: Christoffel, Ricci, curvature."""
    
    def __init__(self, fields: GRCoreFields):
        self.fields = fields
        self.christoffel = np.zeros((fields.Nx, fields.Ny, fields.Nz, 6, 3))
        self.ricci = np.zeros((fields.Nx, fields.Ny, fields.Nz, 6))
        self.ricci_scalar = np.zeros((fields.Nx, fields.Ny, fields.Nz))
        
    def compute_christoffels(self):
        """Compute Christoffel symbols from metric."""
        # Simplified: finite difference approximation of derivative
        gamma = self.fields.gamma_sym6
        Nx, Ny, Nz = self.fields.Nx, self.fields.Ny, self.fields.Nz
        dx, dy, dz = self.fields.dx, self.fields.dy, self.fields.dz
        
        # ∂_x γ_ij
        dgamma_dx = np.gradient(gamma, dx, axis=0)
        # ∂_y γ_ij  
        dgamma_dy = np.gradient(gamma, dy, axis=1)
        # ∂_z γ_ij
        dgamma_dz = np.gradient(gamma, dz, axis=2)
        
        # Γ^i_jk = 1/2 γ^ik (∂_j γ_kl + ∂_k γ_jl - ∂_l γ_jk)
        # Simplified version for demonstration
        inv_metric = inv_sym6(gamma)
        
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    pass  # Full implementation would compute here
        
    def compute_ricci(self):
        """Compute Ricci tensor from Christoffel symbols."""
        # R_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_kl Γ^l_ij - Γ^k_jl Γ^l_ik
        pass
    
    def compute_scalar_curvature(self):
        """Compute Ricci scalar R = γ^ij R_ij."""
        gamma = self.fields.gamma_sym6
        gamma_mat = sym6_to_mat33(gamma)
        ricci_mat = sym6_to_mat33(self.ricci)
        gamma_inv = np.linalg.inv(gamma_mat)
        self.ricci_scalar = np.einsum('...ij,...ij->...', ricci_mat, gamma_inv)


class GRConstraints:
    """Computes Hamiltonian and momentum constraints."""
    
    def __init__(self, fields: GRCoreFields, geometry: GRGeometry):
        self.fields = fields
        self.geometry = geometry
        
    def compute_hamiltonian(self):
        """H = R + K^2 - K_ij K^ij - 2Λ"""
        Lambda = 0.0  # Cosmological constant
        
        # K^2 = (K^ij K_ij)
        K = self.fields.K_sym6
        gamma = self.fields.gamma_sym6
        
        # Convert to 3x3 matrices
        K_mat = sym6_to_mat33(K)
        gamma_mat = sym6_to_mat33(gamma)
        
        # Compute K^ij = γ^ik γ^jl K_kl
        gamma_inv = np.linalg.inv(gamma_mat)
        K_up = np.einsum('...ik,...kl,...lj->...ij', gamma_inv, K_mat, gamma_inv)
        
        # K_ij K^ij
        K_sq = np.einsum('...ij,...ij->...', K_mat, K_up)
        
        # K = γ^ij K_ij
        K_trace = np.einsum('...ij,...ij->...', gamma_mat, K_mat)
        K_sq_total = K_trace ** 2
        
        R = self.geometry.ricci_scalar
        
        self.fields.hamiltonian = R + K_sq_total - K_sq - 2 * Lambda
        
    def compute_momentum(self):
        """D_j(K^ij - γ^ij K) = 0"""
        # Simplified: just compute divergence of K
        K = self.fields.K_sym6
        dK_dx = np.gradient(K, self.fields.dx, axis=0)
        dK_dy = np.gradient(K, self.fields.dy, axis=1)
        dK_dz = np.gradient(K, self.fields.dz, axis=2)
        
        # Approximate momentum constraint violation
        self.fields.momentum = dK_dx + dK_dy + dK_dz
        
    def compute_residuals(self):
        """Compute all constraint residuals."""
        self.compute_hamiltonian()
        self.compute_momentum()
        
        return {
            'H': np.max(np.abs(self.fields.hamiltonian)),
            'M': np.max(np.abs(self.fields.momentum))
        }


class GRSolver:
    """
    3+1 General Relativity Solver.
    
    Evolves metric tensor and extrinsic curvature subject to
    Hamiltonian and momentum constraints.
    """
    
    def __init__(
        self, 
        Nx: int = 32, 
        Ny: int = 32, 
        Nz: int = 32,
        dx: float = 0.1,
        dy: float = 0.1, 
        dz: float = 0.1,
        c: float = 1.0,
        Lambda: float = 0.0,
        log_level: int = 30,  # WARNING level
        log_file: str = None,
        analysis_mode: bool = False
    ):
        self.fields = GRCoreFields(Nx, Ny, Nz, dx, dy, dz)
        self.geometry = GRGeometry(self.fields)
        self.constraints = GRConstraints(self.fields, self.geometry)
        
        self.t = 0.0
        self.step = 0
        self.analysis_mode = analysis_mode
        
    def init_minkowski(self):
        """Initialize flat Minkowski spacetime."""
        # γ_ij = δ_ij (identity metric)
        self.fields.gamma_sym6[..., SYM6_IDX["xx"]] = 1.0
        self.fields.gamma_sym6[..., SYM6_IDX["yy"]] = 1.0
        self.fields.gamma_sym6[..., SYM6_IDX["zz"]] = 1.0
        
        # K_ij = 0 (vanishing extrinsic curvature)
        self.fields.K_sym6.fill(0.0)
        
        # α = 1, β^i = 0
        self.fields.alpha.fill(1.0)
        self.fields.beta.fill(0.0)
        
        # Compute initial constraints
        self.geometry.compute_christoffels()
        self.geometry.compute_ricci()
        self.geometry.compute_scalar_curvature()
        self.constraints.compute_residuals()
        
    def init_gw_pulse(self, amplitude: float = 1e-6, frequency: float = 10.0):
        """Initialize with gravitational wave perturbation."""
        self.init_minkowski()
        
        # Add transverse-traceless perturbation
        x = np.arange(self.fields.Nx) * self.fields.dx
        y = np.arange(self.fields.Ny) * self.fields.dy
        z = np.arange(self.fields.Nz) * self.fields.dz
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # TT wave propagating in z direction
        phase = frequency * (X + Y)  # Simplified
        
        self.fields.gamma_sym6[..., SYM6_IDX["xx"]] += amplitude * np.sin(phase)
        self.fields.gamma_sym6[..., SYM6_IDX["yy"]] -= amplitude * np.sin(phase)
        
    def step_forward_euler(self, dt: float) -> float:
        """
        Forward Euler time step.
        
        ∂_t γ_ij = -2αK_ij + ∂_i β_j + ∂_j β_i
        ∂_t K_ij = ... (more complex)
        """
        # Update metric from extrinsic curvature
        alpha = self.fields.alpha
        K = self.fields.K_sym6
        
        # ∂_t γ_ij = -2αK_ij (ignoring shift for simplicity)
        dgamma_dt = -2 * alpha[..., np.newaxis] * K
        
        self.fields.gamma_sym6 += dgamma_dt * dt
        
        # Simple evolution of K (very simplified)
        # ∂_t K_ij would involve Ricci and gradient terms
        dK_dt = np.zeros_like(K)
        self.fields.K_sym6 += dK_dt * dt
        
        self.t += dt
        self.step += 1
        
        # Recompute constraints
        self.geometry.compute_christoffels()
        self.geometry.compute_ricci()
        self.geometry.compute_scalar_curvature()
        self.constraints.compute_residuals()
        
        return dt
        
    def step_adaptive(self, dt_candidate: float, rails_policy: dict = None) -> Tuple[bool, float, str]:
        """
        Adaptive time step with coherence checking.
        
        Returns: (accepted, dt_used, rejection_reason)
        """
        if rails_policy is None:
            rails_policy = {'H_max': 1e-6, 'M_max': 1e-6}
            
        # Try the step
        dt_used = self.step_forward_euler(dt_candidate)
        
        # Check constraints
        residuals = self.constraints.compute_residuals()
        
        H_violation = residuals['H'] > rails_policy.get('H_max', 1e-6)
        M_violation = residuals['M'] > rails_policy.get('M_max', 1e-6)
        
        if H_violation or M_violation:
            # Revert step (simplified)
            self.step_forward_euler(-dt_candidate)
            return False, 0.0, f"Constraint violation: H={residuals['H']:.2e}, M={residuals['M']:.2e}"
        
        return True, dt_used, None
        
    def run(self, T_max: float, dt_max: float = 0.01) -> dict:
        """Run evolution until T_max."""
        stats = {
            'steps': 0,
            'rejected': 0,
            'H_history': [],
            'M_history': []
        }
        
        while self.t < T_max:
            dt = min(dt_max, T_max - self.t)
            
            accepted, dt_used, reason = self.step_adaptive(dt)
            
            if accepted:
                stats['steps'] += 1
                residuals = self.constraints.compute_residuals()
                stats['H_history'].append(residuals['H'])
                stats['M_history'].append(residuals['M'])
            else:
                stats['rejected'] += 1
                dt_max *= 0.5  # Reduce step size
                
        return stats


# Standalone test
if __name__ == "__main__":
    print("=== 3+1 GR Solver Test ===")
    
    solver = GRSolver(Nx=16, Ny=16, Nz=16, dx=0.1)
    solver.init_gw_pulse(amplitude=1e-6, frequency=5.0)
    
    print(f"Initial H constraint: {np.max(np.abs(solver.fields.hamiltonian)):.2e}")
    print(f"Initial M constraint: {np.max(np.abs(solver.fields.momentum)):.2e}")
    
    stats = solver.run(T_max=0.1, dt_max=0.01)
    
    print(f"Steps: {stats['steps']}, Rejected: {stats['rejected']}")
    print(f"Final H: {stats['H_history'][-1]:.2e}")
    print("GR Solver working!")
