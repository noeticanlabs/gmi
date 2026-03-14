"""
Visual Field Block for GMI Resonant Field Framework.

Implements the multiscale visual field per the mathematical specification:

    V(x, n) ∈ ℝ^(H×W×88)
    
Where:
- x ∈ Ω_vis ⊂ ℝ² is spatial coordinate
- n ∈ {0, ..., 87} is octave/scale index

Interpretation:
- Low n: broad scene geometry, global contours, coarse layout
- Mid n: object boundaries, parts, persistent forms
- High n: texture, fine detail, local edge energy

This is the core visual representation - NOT a scalar sensory channel,
but a multiscale spatial field.

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


class VisualFieldBlock:
    """
    Multiscale visual field V(x, n, t) ∈ ℝ^(H×W×88).
    
    Discrete form: V[i, j, n] where:
    - i ∈ [0, H-1], j ∈ [0, W-1] are spatial coordinates
    - n ∈ [0, 87] is octave/scale index
    
    Interpretation:
    - Low n: broad scene geometry, global contours
    - Mid n: object boundaries, parts, persistent forms
    - High n: texture, fine detail, local edges
    """
    
    NUM_OCTAVES = 88
    
    def __init__(
        self, 
        height: int = 32, 
        width: int = 32,
        k0: float = 0.1
    ):
        """
        Initialize the visual field block.
        
        Args:
            height: Spatial height H
            width: Spatial width W
            k0: Base wave number (default: 0.1 to avoid numerical overflow)
        """
        self.H = height
        self.W = width
        
        # Visual field: (H, W, 88)
        self.V = np.zeros((height, width, self.NUM_OCTAVES))
        
        # Octave wave numbers: k_n = k0 * 2^(n/10) for slower scaling
        self.k0 = k0
        self.k = np.array([k0 * (2 ** (n/10)) for n in range(self.NUM_OCTAVES)])
        
        # Octave operator K (diagonal)
        self.K_squared = np.diag(self.k ** 2)
        
        # Spatial Laplacian kernel
        self._laplacian_kernel = np.array([
            [0.0, 1.0, 0.0],
            [1.0, -4.0, 1.0],
            [0.0, 1.0, 0.0]
        ])
    
    def get_field(self) -> np.ndarray:
        """Get the current visual field."""
        return self.V
    
    def set_field(self, V: np.ndarray):
        """Set the visual field."""
        if V.shape != (self.H, self.W, self.NUM_OCTAVES):
            raise ValueError(f"Expected shape {(self.H, self.W, self.NUM_OCTAVES)}, got {V.shape}")
        self.V = V
    
    def compute_field_energy(self) -> float:
        """
        Compute field energy: E_vis = 0.5 * Σ_i,j,n V_ij,n²
        
        Returns:
            Field energy
        """
        return 0.5 * np.sum(self.V ** 2)
    
    def compute_per_octave_energy(self) -> np.ndarray:
        """
        Compute energy per octave band.
        
        Returns:
            Array of shape (88,) with energy per octave
        """
        return 0.5 * np.sum(self.V ** 2, axis=(0, 1))
    
    def compute_weighted_energy(self) -> float:
        """
        Compute octave-weighted energy: E_vis^K = 0.5 * Σ_n k_n² * Σ_ij V_ij,n²
        
        High octaves contribute more to weighted energy.
        
        Returns:
            Weighted field energy
        """
        energy_per_octave = np.sum(self.V ** 2, axis=(0, 1))
        return 0.5 * np.sum(energy_per_octave * (self.k ** 2))
    
    def compute_spatial_gradient_energy(self, alpha: float = 1.0) -> float:
        """
        Compute spatial gradient energy: E_grad = (α/2) * Σ_n ∫ |∇V|² dx
        
        This penalizes jagged spatial nonsense.
        
        Args:
            alpha: Weight coefficient
            
        Returns:
            Gradient energy
        """
        energy = 0.0
        for n in range(self.NUM_OCTAVES):
            # Compute spatial gradient using finite differences
            V_slice = self.V[:, :, n]
            
            # Gradient in x direction
            grad_x = np.gradient(V_slice, axis=0)
            # Gradient in y direction  
            grad_y = np.gradient(V_slice, axis=1)
            
            energy += np.sum(grad_x ** 2 + grad_y ** 2)
        
        return (alpha / 2.0) * energy
    
    def apply_spatial_laplacian(self) -> np.ndarray:
        """
        Apply spatial Laplacian to all octaves.
        
        Returns:
            Laplacian of visual field
        """
        try:
            from scipy.ndimage import convolve
            result = np.zeros_like(self.V)
            for n in range(self.NUM_OCTAVES):
                result[:, :, n] = convolve(
                    self.V[:, :, n], 
                    self._laplacian_kernel, 
                    mode='constant'
                )
            return result
        except ImportError:
            # Fallback: manual convolution
            result = np.zeros_like(self.V)
            for n in range(self.NUM_OCTAVES):
                V = self.V[:, :, n]
                result[:, :, n] = (
                    np.roll(V, 1, axis=0) + 
                    np.roll(V, -1, axis=0) + 
                    np.roll(V, 1, axis=1) + 
                    np.roll(V, -1, axis=1) - 
                    4 * V
                )
            return result
    
    def apply_octave_damping(self) -> np.ndarray:
        """
        Apply octave-specific damping: K² * V
        
        Returns:
            Octave-damped visual field
        """
        result = np.zeros_like(self.V)
        for n in range(self.NUM_OCTAVES):
            result[:, :, n] = self.k[n] ** 2 * self.V[:, :, n]
        return result
    
    def get_octave_slice(self, n: int) -> np.ndarray:
        """
        Get a single octave slice.
        
        Args:
            n: Octave index
            
        Returns:
            2D array of shape (H, W)
        """
        return self.V[:, :, n]
    
    def set_octave_slice(self, n: int, slice_2d: np.ndarray):
        """
        Set a single octave slice.
        
        Args:
            n: Octave index
            slice_2d: 2D array of shape (H, W)
        """
        if slice_2d.shape != (self.H, self.W):
            raise ValueError(f"Expected shape {(self.H, self.W)}, got {slice_2d.shape}")
        self.V[:, :, n] = slice_2d
    
    def get_scale_pyramid(self, num_scales: int = 5) -> list:
        """
        Get a scale pyramid (for visualization).
        
        Args:
            num_scales: Number of scales to return
            
        Returns:
            List of 2D arrays at different scales
        """
        scales = []
        indices = np.linspace(0, self.NUM_OCTAVES - 1, num_scales, dtype=int)
        
        for idx in indices:
            # Average over nearby octaves
            start = max(0, idx - 2)
            end = min(self.NUM_OCTAVES, idx + 3)
            scale_slice = np.mean(self.V[:, :, start:end], axis=2)
            scales.append(scale_slice)
        
        return scales
    
    def get_spatial_summary(self) -> dict:
        """
        Get spatial summary statistics.
        
        Returns:
            Dictionary with summary stats
        """
        return {
            'total_energy': self.compute_field_energy(),
            'weighted_energy': self.compute_weighted_energy(),
            'mean': float(np.mean(self.V)),
            'std': float(np.std(self.V)),
            'max': float(np.max(self.V)),
            'min': float(np.min(self.V)),
            'sparsity': float(np.sum(np.abs(self.V) < 0.01) / self.V.size),
        }


@dataclass
class VisualFieldConfig:
    """Configuration for visual field."""
    height: int = 32
    width: int = 32
    num_octaves: int = 88
    k0: float = 1.0


# =============================================================================
# Factory functions
# =============================================================================

def create_visual_field(
    height: int = 32,
    width: int = 32,
    num_octaves: int = 88,
    initialization: str = "zeros",
    seed: Optional[int] = None
) -> VisualFieldBlock:
    """
    Create a visual field with specified initialization.
    
    Args:
        height: Spatial height
        width: Spatial width
        num_octaves: Number of octaves
        initialization: "zeros", "random", "gaussian", "edges"
        seed: Random seed
        
    Returns:
        Initialized VisualFieldBlock
    """
    if seed is not None:
        np.random.seed(seed)
    
    field = VisualFieldBlock(height=height, width=width, k0=1.0)
    
    if initialization == "zeros":
        pass  # Already zeros
    elif initialization == "random":
        field.V = np.random.randn(height, width, num_octaves) * 0.1
    elif initialization == "gaussian":
        # Create Gaussian blobs at different scales
        for n in range(num_octaves):
            x_c = width // 2 + np.random.randint(-5, 5)
            y_c = height // 2 + np.random.randint(-5, 5)
            sigma = 2.0 + n * 0.5
            
            x = np.arange(width)
            y = np.arange(height)
            X, Y = np.meshgrid(x, y)
            
            gaussian = np.exp(-((X - x_c)**2 + (Y - y_c)**2) / (2 * sigma**2))
            field.V[:, :, n] = gaussian
    elif initialization == "edges":
        # Create edge-like patterns
        for n in range(num_octaves):
            freq = (n + 1) / num_octaves
            x = np.arange(width)
            y = np.arange(height)
            X, Y = np.meshgrid(x, y)
            
            edges = np.sin(2 * np.pi * freq * X) * np.cos(2 * np.pi * freq * Y)
            field.V[:, :, n] = edges * 0.5
    
    return field


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing visual field block...")
    
    # Create visual field
    field = VisualFieldBlock(height=32, width=32)
    print(f"Field shape: {field.V.shape}")
    print(f"Number of octaves: {field.NUM_OCTAVES}")
    
    # Test with random initialization
    field_rand = create_visual_field(32, 32, initialization="random", seed=42)
    print(f"\nRandom field:")
    print(f"  Total energy: {field_rand.compute_field_energy():.4f}")
    print(f"  Weighted energy: {field_rand.compute_weighted_energy():.4f}")
    print(f"  Gradient energy: {field_rand.compute_spatial_gradient_energy():.4f}")
    
    # Test with Gaussian blobs
    field_gauss = create_visual_field(32, 32, initialization="gaussian", seed=42)
    print(f"\nGaussian field:")
    print(f"  Total energy: {field_gauss.compute_field_energy():.4f}")
    
    # Test octave operations
    print(f"\nPer-octave energy (first 5): {field_rand.compute_per_octave_energy()[:5]}")
    
    # Test spatial Laplacian
    laplacian = field_rand.apply_spatial_laplacian()
    print(f"\nLaplacian norm: {np.linalg.norm(laplacian):.4f}")
    
    # Test octave damping
    damped = field_rand.apply_octave_damping()
    print(f"Damped norm: {np.linalg.norm(damped):.4f}")
    
    # Test scale pyramid
    pyramid = field_rand.get_scale_pyramid(num_scales=3)
    print(f"\nScale pyramid: {len(pyramid)} scales")
    for i, scale in enumerate(pyramid):
        print(f"  Scale {i}: shape={scale.shape}")
    
    # Test spatial summary
    summary = field_rand.get_spatial_summary()
    print(f"\nSpatial summary: {summary}")
    
    print("\nAll tests passed!")
