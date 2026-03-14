"""
Vision Module for GMI Resonant Field Framework.

Implements the multiscale visual field per the mathematical specification:

    V(x, n) ∈ ℝ^(H×W×88)
    
Where:
- x ∈ Ω_vis ⊂ ℝ² is spatial coordinate
- n ∈ {0, ..., 87} is octave/scale index

This is the visual analogue of the resonant field, carrying both space and scale.

Modules:
- visual_field: Core visual field representation
- scene_binding: Scene coherence functional
- visual_dynamics: Visual field dynamics
- visual_projections: Eye and display operators

This module is part of the constitutive extension to the GM-OS canon.
"""

from gmos.agents.gmi.vision.visual_field import VisualFieldBlock
from gmos.agents.gmi.vision.scene_binding import SceneBindingFunctional
from gmos.agents.gmi.vision.visual_dynamics import VisualDriftOperator
from gmos.agents.gmi.vision.visual_projections import (
    EyeOperator,
    ImageryOperator,
    VisualEgressOperator
)

__all__ = [
    'VisualFieldBlock',
    'SceneBindingFunctional', 
    'VisualDriftOperator',
    'EyeOperator',
    'ImageryOperator',
    'VisualEgressOperator',
]
