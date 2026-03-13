# Memory Curvature / Scarring Implementation Plan

## Overview

This plan implements the "Trauma" mechanism - the ability for the organism to learn from negative experiences through memory curvature.

**Core Concept**: When an action fails or harms the organism, that event permanently deforms the PhaseLoom geometric landscape, creating a "hill" (curvature increase) that repels future gradient flow from making the same choice.

## Mathematical Framework

### Curvature Field Update

When the organism receives negative feedback (damage, failure):

```
C(x) ← C(x) + ΔC • exp(-|x - x_failure|² / σ²)
```

Where:
- `C(x)` = Curvature at semantic coordinate x
- `x_failure` = The semantic coordinate of the failed action
- `ΔC` = Curvature increment (damage magnitude)
- `σ` = Spatial spread of the scar

### Extended Potential with Curvature

```
V_ext[θ; s] = ∫_M (κ/2|∇θ|² + W(θ) + θ·Ξ(s) + λ_C θ·C) dx
```

The curvature term `λ_C θ·C` creates a repulsive potential barrier.

### Gradient Flow with Curvature

```
∂_t θ = -∇V_ext + N_K(θ)
       = κΔθ - W'(θ) - Ξ(s) - λ_C C + N_K(θ)
```

The curvature `C` acts as a "force field" pushing the gradient away from dangerous regions.

---

## Implementation Tasks

### Task 1: CurvatureField Class

**Location**: `gmos/src/gmos/sensory/curvature.py` (NEW FILE)

```python
class CurvatureField:
    """Manages the curvature field C(x) for memory scarring."""
    
    def __init__(self, dimensions: int, resolution: int):
        self.C = np.zeros((resolution,) * dimensions)
        self.coordinates = ...  # Semantic coordinate grid
        
    def add_scar(self, position: float, magnitude: float, spread: float):
        """Add a curvature scar at position with given magnitude and spread."""
        # Gaussian bump: ΔC * exp(-|x-pos|²/σ²)
        
    def get_curvature(self, position: float) -> float:
        """Get curvature at a specific position."""
        
    def compute_gradient_penalty(self, theta: np.ndarray) -> float:
        """Compute λ_C ∫ θ·C dx - the curvature penalty term."""
```

### Task 2: TraumaMemory Class

**Location**: `gmos/src/gmos/sensory/trauma.py` (NEW FILE)

```python
class TraumaMemory:
    """Manages traumatic memories that create lasting scars."""
    
    def __init__(self, curvature_field: CurvatureField):
        self.curvature = curvature_field
        self.trauma_log = []
        
    def process_failure(
        self, 
        action: str, 
        damage: float, 
        semantic_position: float
    ):
        """Process a failed action and create a scar."""
        # 1. Log the trauma
        # 2. Add curvature to field
        # 3. Compute scar properties
        
    def should_avoid(self, action: str, semantic_position: float) -> bool:
        """Check if an action should be avoided based on scarring."""
        # Check if curvature at position exceeds threshold
```

### Task 3: Integrate with WorldWeld

**Location**: Update `gmos/tests/sensory/test_world_weld.py`

Add:
- Poison environment (negative feedback)
- Trauma processing after damage
- Avoidance behavior demonstration

---

## Mermaid: Trauma Processing Flow

```mermaid
flowchart TD
    A[Action Executed] --> B[Environment Response]
    B --> C{Damage > 0?}
    C -->|Yes| D[Process Trauma]
    C -->|No| E[Normal Replenishment]
    
    D --> F[Log Trauma Event]
    F --> G[Calculate Scar: ΔC · exp(-|x-x failure|²/σ²)]
    G --> H[Update Curvature Field C(x)]
    H --> I[Next Tick: Gradient hits curvature hill]
    I --> J[Organism routes around danger]
    
    E --> K[Standard Budget Update]
```

---

## Test Scenario: The Poison Test

1. **Setup**: Organism in environment with a "poison" node
2. **First encounter**: Organism tries to eat from poison node
3. **Feedback**: Negative - takes damage, no replenishment
4. **Scarring**: Curvature field updated at poison semantic coordinate
5. **Second encounter**: Organism approaches poison node
6. **Result**: Gradient hits curvature hill, organism routes around

---

## Files to Create

1. `gmos/src/gmos/sensory/curvature.py` - Curvature field management
2. `gmos/src/gmos/sensory/trauma.py` - Trauma processing and memory
3. Update `gmos/src/gmos/sensory/__init__.py` - Export new modules
4. Add trauma tests to `gmos/tests/sensory/test_world_weld.py`

---

## Success Criteria

1. ✅ Curvature field can store multiple scars
2. ✅ Scars create repulsive potential barriers
3. ✅ Organism avoids previously harmful actions
4. ✅ Test demonstrates "touch hot stove, learn to avoid"
