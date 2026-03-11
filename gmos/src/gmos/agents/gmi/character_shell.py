"""
Character Shell - Threshold Modulation Field for GMI.

This module provides the character shell χ that modulates how the GMI organism
responds within the lawful epistemic space. It is NOT a belief system - it is
a lawful parameterization of response style.

Key principles:
- χ may modulate thresholds within the lawful set, but may NOT override legality
- Character is defined by parameters in [0,1]
- Character induces a modulation map: M_χ: Θ_0 → Θ_χ

The character shell ties into epistemic shell v1-v4:
- v1: χ_humility modulates collapse resistance
- v2: χ_laziness/discipline modulate representative persistence
- v3: χ_curiosity/patience modulate EVI threshold
- v4: χ_restraint/humility modulate corroboration demand
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np


# ============================================================================
# Character State Definition
# ============================================================================

@dataclass
class CharacterState:
    """
    Character shell state - threshold modulation parameters.
    
    χ = (χ_courage, χ_discipline, χ_patience, χ_curiosity, 
          χ_restraint, χ_persistence, χ_laziness, χ_humility) ∈ [0,1]^m
    
    These are control coefficients that modulate thresholds inside the lawful 
    epistemic space.
    """
    
    # Core χ parameters (control coefficients in [0,1])
    chi_courage: float = 0.5       # Tolerance for acting under ambiguity
    chi_discipline: float = 0.5     # Pointer preservation, bookkeeping rigor
    chi_patience: float = 0.5      # Tolerance for delay in learning
    chi_curiosity: float = 0.5     # Willingness to pay for evidence
    chi_restraint: float = 0.5     # Corroboration demand before acting
    chi_persistence: float = 0.5   # Resistance to giving up during repair
    chi_laziness: float = 0.3      # Preference for cheap representatives
    chi_humility: float = 0.5      # Resistance to premature fiber collapse
    
    # Bounded reservoirs (for dynamics)
    pressure: float = 0.0           # Accumulated pressure from constraints
    shock_level: float = 0.0        # Model-falsification shock
    
    # Drift parameters (how character evolves)
    adaptation_rate: float = 0.05   # Rate of character drift under experience
    
    # Clamping utilities
    _chi_min: float = 0.0
    _chi_max: float = 1.0
    
    def __post_init__(self):
        """Clamp all χ parameters to [0, 1]."""
        self.chi_courage = self._clamp(self.chi_courage)
        self.chi_discipline = self._clamp(self.chi_discipline)
        self.chi_patience = self._clamp(self.chi_patience)
        self.chi_curiosity = self._clamp(self.chi_curiosity)
        self.chi_restraint = self._clamp(self.chi_restraint)
        self.chi_persistence = self._clamp(self.chi_persistence)
        self.chi_laziness = self._clamp(self.chi_laziness)
        self.chi_humility = self._clamp(self.chi_humility)
        self.pressure = max(0.0, self.pressure)
        self.shock_level = max(0.0, self.shock_level)
        self.adaptation_rate = max(0.0, min(1.0, self.adaptation_rate))
    
    def _clamp(self, value: float) -> float:
        return max(self._chi_min, min(self._chi_max, value))
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'chi_courage': self.chi_courage,
            'chi_discipline': self.chi_discipline,
            'chi_patience': self.chi_patience,
            'chi_curiosity': self.chi_curiosity,
            'chi_restraint': self.chi_restraint,
            'chi_persistence': self.chi_persistence,
            'chi_laziness': self.chi_laziness,
            'chi_humility': self.chi_humility,
            'pressure': self.pressure,
            'shock_level': self.shock_level,
            'adaptation_rate': self.adaptation_rate,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CharacterState':
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def create_scientist(cls) -> 'CharacterState':
        """Create a scientist profile: careful, thorough, humble."""
        return cls(
            chi_courage=0.3,
            chi_discipline=0.8,
            chi_patience=0.8,
            chi_curiosity=0.6,
            chi_restraint=0.7,
            chi_persistence=0.7,
            chi_laziness=0.2,
            chi_humility=0.8,
        )
    
    @classmethod
    def create_warrior(cls) -> 'CharacterState':
        """Create a warrior profile: bold, fast, decisive."""
        return cls(
            chi_courage=0.9,
            chi_discipline=0.6,
            chi_patience=0.3,
            chi_curiosity=0.4,
            chi_restraint=0.3,
            chi_persistence=0.6,
            chi_laziness=0.3,
            chi_humility=0.4,
        )
    
    @classmethod
    def create_explorer(cls) -> 'CharacterState':
        """Create an explorer profile: curious, bold, experimental."""
        return cls(
            chi_courage=0.7,
            chi_discipline=0.4,
            chi_patience=0.5,
            chi_curiosity=0.9,
            chi_restraint=0.3,
            chi_persistence=0.5,
            chi_laziness=0.4,
            chi_humility=0.5,
        )
    
    @classmethod
    def create_diplomat(cls) -> 'CharacterState':
        """Create a diplomat profile: balanced, cautious, verification-focused."""
        return cls(
            chi_courage=0.5,
            chi_discipline=0.7,
            chi_patience=0.6,
            chi_curiosity=0.5,
            chi_restraint=0.8,
            chi_persistence=0.6,
            chi_laziness=0.3,
            chi_humility=0.7,
        )


# ============================================================================
# Threshold Modulation
# ============================================================================

@dataclass
class EpistemicThresholds:
    """
    Base epistemic thresholds (before character modulation).
    
    These are the "neutral" values that character will modulate.
    """
    # v1 thresholds
    tau_frag: float = 0.5           # Fragility threshold
    lambda_collapse: float = 0.5     # Collapse penalty weight
    
    # v2 thresholds
    tau_refresh: float = 0.5         # Representative refresh threshold
    lambda_overreach: float = 0.5    # Overreach penalty weight
    
    # v3 thresholds
    tau_epistemic: float = 0.5       # EVI threshold
    beta_delay: float = 0.3          # Delay cost weight
    lambda_mania: float = 0.3        # Mania penalty weight
    
    # v4 thresholds
    tau_corr: float = 0.6            # Corroboration threshold
    lambda_shock: float = 0.4       # Shock penalty weight


@dataclass
class ModulatedThresholds:
    """
    Character-modulated epistemic thresholds.
    
    Θ_χ = M_χ(Θ_0)
    """
    # v1
    lambda_collapse: float
    tau_frag: float
    
    # v2
    tau_refresh: float
    lambda_overreach: float
    
    # v3
    tau_epistemic: float
    beta_delay: float
    lambda_mania: float
    
    # v4
    tau_corr: float
    lambda_shock: float


def compute_modulated_thresholds(
    base: EpistemicThresholds,
    chi: CharacterState,
) -> ModulatedThresholds:
    """
    Apply character modulation to epistemic thresholds.
    
    Θ_χ = M_χ(Θ_0)
    
    Args:
        base: Base epistemic thresholds (Θ_0)
        chi: Character state (χ)
        
    Returns:
        Modulated thresholds (Θ_χ)
    """
    
    # v1: Humility modulates collapse resistance
    # Higher humility = keep alternatives alive longer = higher collapse penalty
    collapse_weight = base.lambda_collapse * (1 + 0.5 * chi.chi_humility)
    
    # v1: Courage modulates ambiguity tolerance
    # Higher courage = tolerate more fragility
    frag_threshold = base.tau_frag + (
        0.3 * chi.chi_courage - 0.2 * chi.chi_restraint
    )
    
    # v2: Laziness modulates representative persistence
    # Higher laziness = continue using current representative longer = HIGHER threshold
    # Higher discipline = refresh sooner = LOWER threshold
    refresh_threshold = base.tau_refresh * (
        1 + 0.5 * chi.chi_laziness - 0.4 * chi.chi_discipline
    )
    
    # v2: Discipline guards against overreach
    # Higher discipline = pay more for confusing representative with truth
    overreach_weight = base.lambda_overreach * (
        1 + 0.5 * chi.chi_discipline + 0.3 * chi.chi_humility
    )
    
    # v3: Curiosity modulates EVI threshold
    # Higher curiosity = ask more often = LOWER threshold
    epi_threshold = base.tau_epistemic * (
        1 - 0.5 * chi.chi_curiosity + 0.3 * chi.chi_laziness
    )
    
    # v3: Patience modulates delay cost
    # Higher patience = willing to wait = lower delay pain
    delay_weight = base.beta_delay * (
        1 + 0.3 * chi.chi_courage + 0.2 * chi.chi_laziness
        - 0.5 * chi.chi_patience
    )
    
    # v3: Restraint vs persistence modulates mania
    # Higher restraint = less mania, higher persistence = risk of compulsive looping
    mania_weight = base.lambda_mania * (
        1 + 0.5 * chi.chi_restraint - 0.4 * chi.chi_persistence
    )
    
    # v4: Restraint/humility demand corroboration
    # Higher restraint = want more corroboration
    corr_threshold = base.tau_corr * (
        1 + 0.5 * chi.chi_restraint + 0.3 * chi.chi_humility
        - 0.3 * chi.chi_courage
    )
    
    # v4: Courage/patience soften shock
    # Higher courage/patience = less affected by model falsification
    shock_weight = base.lambda_shock * (
        1 - 0.4 * chi.chi_courage - 0.4 * chi.chi_patience
        + 0.3 * chi.chi_laziness
    )
    
    return ModulatedThresholds(
        lambda_collapse=collapse_weight,
        tau_frag=frag_threshold,
        tau_refresh=refresh_threshold,
        lambda_overreach=overreach_weight,
        tau_epistemic=epi_threshold,
        beta_delay=delay_weight,
        lambda_mania=mania_weight,
        tau_corr=corr_threshold,
        lambda_shock=shock_weight,
    )


# ============================================================================
# Character Dynamics (Drift Under Experience)
# ============================================================================

def update_character(
    current: CharacterState,
    action_taken: bool,
    action_successful: bool,
    action_value: float,
    pressure_input: float,
    shock_received: bool,
) -> CharacterState:
    """
    Update character state based on experiences.
    
    Character drifts slowly under repeated experiences:
    - Successful high-pressure actions → increase courage
    - Repeated lazy refusals → increase laziness temporarily
    - Model falsification shock → increase humility
    - Failed repairs → increase patience
    
    Args:
        current: Current character state
        action_taken: Whether an action was committed
        action_successful: Whether the action succeeded
        action_value: Net value of the action (V_before - V_after)
        pressure_input: Pressure from constraints at this step
        shock_received: Whether a model falsification shock occurred
        
    Returns:
        Updated character state
    """
    
    rate = current.adaptation_rate
    
    # Pressure dynamics
    new_pressure = (1 - 0.1) * current.pressure + pressure_input
    new_pressure = min(1.0, new_pressure)
    
    # Shock decay
    new_shock = max(0.0, current.shock_level - rate * 0.1)
    if shock_received:
        new_shock = min(1.0, new_shock + 0.2)
    
    # Courage: success under pressure increases, failure decreases
    if action_taken and action_successful and pressure_input > 0.3:
        courage_delta = rate * 0.1
    elif action_taken and not action_successful:
        courage_delta = -rate * 0.05
    else:
        courage_delta = 0.0
    new_courage = current.chi_courage + courage_delta
    
    # Humility: shock increases, recovery decreases
    if shock_received:
        humility_delta = rate * 0.2
    else:
        humility_delta = -rate * 0.02
    new_humility = current.chi_humility + humility_delta
    
    # Laziness: lazy refusal increases, successful action decreases
    if not action_taken and action_value > 0:
        laziness_delta = rate * 0.1
    elif action_taken and action_successful:
        laziness_delta = -rate * 0.02
    else:
        laziness_delta = 0.0
    new_laziness = current.chi_laziness + laziness_delta
    
    # Patience: failed repair increases, successful action decreases
    if not action_successful and action_taken:
        patience_delta = rate * 0.05
    elif action_successful:
        patience_delta = -rate * 0.02
    else:
        patience_delta = 0.0
    new_patience = current.chi_patience + patience_delta
    
    # Create new state with clamped values
    return CharacterState(
        chi_courage=current._clamp(new_courage),
        chi_discipline=current.chi_discipline,  # Discipline is stable
        chi_patience=current._clamp(new_patience),
        chi_curiosity=current.chi_curiosity,    # Curiosity is stable
        chi_restraint=current.chi_restraint,    # Restraint is stable
        chi_persistence=current.chi_persistence,  # Persistence is stable
        chi_laziness=current._clamp(new_laziness),
        chi_humility=current._clamp(new_humility),
        pressure=new_pressure,
        shock_level=new_shock,
        adaptation_rate=current.adaptation_rate,
    )


# ============================================================================
# Character Non-Override Constraint
# ============================================================================

def is_action_allowed(
    legal_check_passed: bool,
    message: str = "",
) -> Tuple[bool, str]:
    """
    Character may bias lawful selection, but may NOT make an unlawful act lawful.
    
    This is the fundamental constraint: χ does NOT override hard lawful constraints.
    
    Args:
        legal_check_passed: Whether the action passes hard legal constraints
        message: Additional context
        
    Returns:
        Tuple of (allowed, reason)
    """
    if not legal_check_passed:
        return False, f"violates hard lawful constraints: {message}"
    return True, "allowed by character-modulated thresholds"


# ============================================================================
# Integration with GMI Tension Law
# ============================================================================

def apply_character_to_tension_weights(
    base_weights: 'TensionWeights',
    chi: CharacterState,
    modulated: ModulatedThresholds,
) -> 'TensionWeights':
    """
    Apply character-modulated thresholds to tension weights.
    
    This integrates character into the GMI tension law computation.
    
    Args:
        base_weights: Base tension weights
        chi: Character state
        modulated: Character-modulated thresholds
        
    Returns:
        Modified weights reflecting character modulation
    """
    # Create a copy with modified weights
    from dataclasses import replace
    
    # Map modulated thresholds to weights
    # Note: This assumes TensionWeights has corresponding fields
    # We'll handle this based on actual tension_law.py structure
    
    return base_weights  # Placeholder - actual integration depends on tension_law.py


# ============================================================================
# Utility Functions
# ============================================================================

def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def interpolate_character(
    c1: CharacterState,
    c2: CharacterState,
    t: float,
) -> CharacterState:
    """
    Interpolate between two character states.
    
    Useful for smooth transitions between character profiles.
    
    Args:
        c1: First character state
        c2: Second character state
        t: Interpolation factor in [0, 1]
        
    Returns:
        Interpolated character state
    """
    t = clamp(t, 0.0, 1.0)
    inv_t = 1.0 - t
    
    return CharacterState(
        chi_courage=inv_t * c1.chi_courage + t * c2.chi_courage,
        chi_discipline=inv_t * c1.chi_discipline + t * c2.chi_discipline,
        chi_patience=inv_t * c1.chi_patience + t * c2.chi_patience,
        chi_curiosity=inv_t * c1.chi_curiosity + t * c2.chi_curiosity,
        chi_restraint=inv_t * c1.chi_restraint + t * c2.chi_restraint,
        chi_persistence=inv_t * c1.chi_persistence + t * c2.chi_persistence,
        chi_laziness=inv_t * c1.chi_laziness + t * c2.chi_laziness,
        chi_humility=inv_t * c1.chi_humility + t * c2.chi_humility,
        pressure=inv_t * c1.pressure + t * c2.pressure,
        shock_level=inv_t * c1.shock_level + t * c2.shock_level,
        adaptation_rate=c1.adaptation_rate,  # Keep adaptation rate
    )


def character_summary(chi: CharacterState) -> dict:
    """Get a summary of character state."""
    return {
        'courage': chi.chi_courage,
        'discipline': chi.chi_discipline,
        'patience': chi.chi_patience,
        'curiosity': chi.chi_curiosity,
        'restraint': chi.chi_restraint,
        'persistence': chi.chi_persistence,
        'laziness': chi.chi_laziness,
        'humility': chi.chi_humility,
        'pressure': chi.pressure,
        'shock': chi.shock_level,
    }
