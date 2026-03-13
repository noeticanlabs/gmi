"""
Curvature Field for Memory Scarring.

Per spec: Memory Curvature C(x) represents the geometric deformation
of the PhaseLoom when the organism experiences negative outcomes.
When an action fails or harms the organism, that event physically
deforms the landscape, creating a "hill" that repels future
gradient flow from making that same choice.

Mathematical Form:
    C(x) ← C(x) + ΔC · exp(-|x - x_failure|² / σ²)

Extended Potential with Curvature:
    V_ext[θ; s] = ∫_M (κ/2|∇θ|² + W(θ) + θ·Ξ(s) + λ_C θ·C) dx
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


@dataclass
class CurvatureParameters:
    """
    Parameters governing curvature field behavior.
    """
    # Curvature coupling constant λ_C
    lambda_c: float = 1.0
    
    # Scar spread σ (width of the Gaussian)
    scar_spread: float = 0.1
    
    # Maximum curvature value
    max_curvature: float = 10.0
    
    # Curvature decay rate (scars heal over time)
    decay_rate: float = 0.01
    
    # Minimum curvature threshold (below this, no avoidance)
    avoidance_threshold: float = 0.5


class CurvatureField:
    """
    Manages the curvature field C(x) for memory scarring.
    
    The curvature field represents the geometric deformation
    of the PhaseLoom caused by traumatic experiences.
    """
    
    def __init__(
        self,
        dimensions: int = 1,
        resolution: int = 100,
        bounds: Tuple[float, float] = (0.0, 1.0),
        params: Optional[CurvatureParameters] = None,
    ):
        """
        Initialize the curvature field.
        
        Args:
            dimensions: Number of spatial dimensions
            resolution: Grid resolution per dimension
            bounds: (min, max) bounds for each dimension
            params: Curvature parameters
        """
        self.dimensions = dimensions
        self.resolution = resolution
        self.bounds = bounds
        self.params = params or CurvatureParameters()
        
        # Initialize curvature field C(x)
        self.C = np.zeros((resolution,) * dimensions)
        
        # Create coordinate grid
        self._create_coordinates()
        
        # Track scar positions
        self.scar_positions: List[float] = []
        self.scar_magnitudes: List[float] = []
    
    def _create_coordinates(self):
        """Create the coordinate grid."""
        if self.dimensions == 1:
            self.coordinates = np.linspace(self.bounds[0], self.bounds[1], self.resolution)
        elif self.dimensions == 2:
            x = np.linspace(self.bounds[0], self.bounds[1], self.resolution)
            y = np.linspace(self.bounds[0], self.bounds[1], self.resolution)
            self.coordinates = np.meshgrid(x, y, indexing='ij')
        else:
            # Higher dimensions - use simple array
            self.coordinates = np.linspace(self.bounds[0], self.bounds[1], self.resolution)
    
    def add_scar(
        self,
        position: float,
        magnitude: float,
        spread: Optional[float] = None
    ) -> float:
        """
        Add a curvature scar at the given position.
        
        Math: C(x) ← C(x) + ΔC · exp(-|x - pos|² / σ²)
        
        Args:
            position: The semantic coordinate of the scar
            magnitude: The curvature increment ΔC
            spread: Optional override for scar spread σ
            
        Returns:
            The actual magnitude added (may be clamped)
        """
        spread = spread or self.params.scar_spread
        
        # Clamp magnitude
        magnitude = min(magnitude, self.params.max_curvature)
        
        if self.dimensions == 1:
            # 1D Gaussian bump
            x = self.coordinates
            scar = magnitude * np.exp(-((x - position) ** 2) / (2 * spread ** 2))
            self.C += scar
        else:
            # Multi-dimensional (use first dimension for simplicity)
            x = self.coordinates[0] if isinstance(self.coordinates, tuple) else self.coordinates
            scar = magnitude * np.exp(-((x - position) ** 2) / (2 * spread ** 2))
            self.C += scar
        
        # Track scar
        self.scar_positions.append(position)
        self.scar_magnitudes.append(magnitude)
        
        return magnitude
    
    def get_curvature(self, position: float) -> float:
        """
        Get curvature at a specific position.
        
        Args:
            position: The position to query
            
        Returns:
            Curvature value at that position
        """
        if self.dimensions == 1:
            # Interpolate from grid
            idx = int((position - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * (self.resolution - 1))
            idx = max(0, min(self.resolution - 1, idx))
            return self.C[idx]
        else:
            # For multi-D, use first coordinate
            x = self.coordinates[0] if isinstance(self.coordinates, tuple) else self.coordinates
            idx = int((position - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * (self.resolution - 1))
            idx = max(0, min(self.resolution - 1, idx))
            return self.C[idx, idx] if self.C.ndim > 1 else self.C[idx]
    
    def compute_curvature_gradient(self, position: float) -> float:
        """
        Compute the gradient of curvature at a position.
        
        This determines the "push" direction when gradient flow hits the scar.
        
        Args:
            position: The position to query
            
        Returns:
            Curvature gradient (derivative)
        """
        if self.dimensions == 1:
            # Numerical gradient
            idx = int((position - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * (self.resolution - 1))
            idx = max(1, min(self.resolution - 2, idx))
            
            # Central difference
            grad = (self.C[idx + 1] - self.C[idx - 1]) / (2 * (self.bounds[1] - self.bounds[0]) / self.resolution)
            return grad
        return 0.0
    
    def should_avoid(self, position: float) -> bool:
        """
        Check if a position should be avoided due to scarring.
        
        Args:
            position: The position to check
            
        Returns:
            True if curvature exceeds avoidance threshold
        """
        curvature = self.get_curvature(position)
        return curvature > self.params.avoidance_threshold
    
    def compute_gradient_penalty(
        self,
        theta: np.ndarray
    ) -> float:
        """
        Compute the curvature penalty term: λ_C ∫ θ·C dx
        
        This is the energy cost of having field values in high-curvature regions.
        
        Args:
            theta: The field state
            
        Returns:
            Curvature penalty value
        """
        # Simple dot product approximation
        if theta.shape != self.C.shape:
            # Resize theta to match C
            theta_resized = np.interp(
                np.linspace(0, 1, self.resolution),
                np.linspace(0, 1, len(theta)),
                theta
            )
        else:
            theta_resized = theta
        
        # Compute λ_C * θ · C
        penalty = self.params.lambda_c * np.sum(theta_resized * self.C)
        
        return penalty
    
    def compute_extended_potential(
        self,
        theta: np.ndarray,
        kappa: float = 1.0,
        external_force: float = 0.0
    ) -> float:
        """
        Compute the extended potential with curvature.
        
        V_ext = ∫ (κ/2|∇θ|² + θ·Ξ(s) + λ_C θ·C) dx
        
        Args:
            theta: Field state
            kappa: Diffusion coefficient
            external_force: External forcing term
            
        Returns:
            Total extended potential
        """
        # Gradient energy term
        if self.dimensions == 1:
            grad_energy = kappa * 0.5 * np.sum(np.gradient(theta) ** 2)
        else:
            grad_energy = kappa * 0.5 * np.sum(np.gradient(theta) ** 2)
        
        # External forcing term
        external_term = np.sum(theta * external_force)
        
        # Curvature penalty term
        curvature_penalty = self.compute_gradient_penalty(theta)
        
        return grad_energy + external_term + curvature_penalty
    
    def decay_scars(self, dt: float = 1.0):
        """
        Apply decay to curvature field (scars heal over time).
        
        Args:
            dt: Time step
        """
        decay = np.exp(-self.params.decay_rate * dt)
        self.C *= decay
        
        # Clean up small values
        self.C[np.abs(self.C) < 0.01] = 0.0
    
    def get_scar_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current scarring.
        
        Returns:
            Dictionary with scar statistics
        """
        non_zero = np.count_nonzero(self.C)
        max_curvature = np.max(self.C)
        total_curvature = np.sum(self.C)
        
        return {
            "scar_count": non_zero,
            "max_curvature": float(max_curvature),
            "total_curvature": float(total_curvature),
            "scar_positions": self.scar_positions[-5:] if len(self.scar_positions) > 5 else self.scar_positions,
        }
    
    def visualize(self) -> str:
        """
        Get a text visualization of the curvature field.
        
        Returns:
            ASCII art representation
        """
        if self.dimensions != 1:
            return "Visualization only supported for 1D fields"
        
        # Discretize for visualization
        resolution = min(50, self.resolution)
        indices = np.linspace(0, self.resolution - 1, resolution, dtype=int)
        values = self.C[indices]
        
        # Normalize to 0-20 for display
        if np.max(values) > 0:
            values = values / np.max(values) * 20
        else:
            values = np.zeros_like(values)
        
        lines = []
        for v in values:
            bar = "█" * int(v)
            lines.append(f"|{bar}")
        
        return "\n".join(lines)


class CurvatureField2D(CurvatureField):
    """
    2D curvature field for more complex semantic spaces.
    """
    
    def __init__(self, resolution: int = 50, bounds: Tuple[float, float] = (0.0, 1.0)):
        super().__init__(dimensions=2, resolution=resolution, bounds=bounds)
    
    def add_scar_2d(
        self,
        x: float,
        y: float,
        magnitude: float,
        spread: Optional[float] = None
    ):
        """Add a 2D Gaussian scar."""
        spread = spread or self.params.scar_spread
        
        X, Y = self.coordinates
        scar = magnitude * np.exp(-((X - x)**2 + (Y - y)**2) / (2 * spread**2))
        self.C += scar
        
        self.scar_positions.append((x, y))
        self.scar_magnitudes.append(magnitude)
    
    def get_curvature_2d(self, x: float, y: float) -> float:
        """Get curvature at 2D position."""
        idx_x = int((x - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * (self.resolution - 1))
        idx_y = int((y - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * (self.resolution - 1))
        idx_x = max(0, min(self.resolution - 1, idx_x))
        idx_y = max(0, min(self.resolution - 1, idx_y))
        
        return self.C[idx_x, idx_y]


# === Exports ===

__all__ = [
    "CurvatureParameters",
    "CurvatureField",
    "CurvatureField2D",
]
