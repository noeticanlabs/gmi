import numpy as np

class MemoryManifold:
    """
    The geometric memory of the GMI engine.
    Instead of updating weights, it warps the local metric by adding
    curvature 'scars' at coordinates where the ledger rejected a trajectory.
    """
    def __init__(self, lambda_c=5.0):
        self.scars = []        # List of tuples: (coordinate_array, penalty_height)
        self.lambda_c = lambda_c  # How severely a scar warps the space

    def write_scar(self, x: np.ndarray, penalty=1.0):
        """Places a localized curvature spike at the rejected coordinate."""
        self.scars.append((np.array(x), penalty))

    def read_curvature(self, x: np.ndarray) -> float:
        """
        Evaluates the total curvature C(x) from all scars.
        Uses a Gaussian distribution so the penalty is highest exactly at the 
        scar, but creates a 'steep hill' in the surrounding semantic neighborhood.
        """
        if not self.scars:
            return 0.0
            
        c_val = 0.0
        for scar_x, height in self.scars:
            # Gaussian bump: height * exp(-distance^2 / width)
            dist_sq = np.sum((x - scar_x)**2)
            c_val += height * np.exp(-dist_sq / 2.0)
            
        return self.lambda_c * c_val
    
    def clear(self):
        """Clear all scars (for testing)"""
        self.scars = []
