"""
Full Dynamics Integration for GMI Resonant Field Framework.

This module integrates all components of the resonant field framework:

- 12-block state decomposition
- 88-octave resonant field
- Reserve-coupled viscosity
- Triad resonance
- Ear operator (sensory ingress)
- Voice operator (spectral egress)
- Visual field
- Scene binding

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any

from gmos.agents.gmi.twelve_block_state import TwelveBlockState, create_initial_state
from gmos.agents.gmi.resonant_field import ResonantFieldBlock, ActionForcingOperator
from gmos.agents.gmi.viscosity_law import ReserveCoupledViscosity
from gmos.agents.gmi.triad_resonance import TriadResonanceOperator
from gmos.agents.gmi.ear_operator import EarOperator, ContextModulationOperator
from gmos.agents.gmi.voice_operator import VoiceOperator
from gmos.agents.gmi.vision.visual_field import VisualFieldBlock
from gmos.agents.gmi.vision.scene_binding import SceneBindingFunctional
from gmos.agents.gmi.vision.visual_dynamics import VisualDriftOperator, VisualCrossScaleResonance
from gmos.agents.gmi.vision.visual_projections import EyeOperator, ImageryOperator, VisualEgressOperator


@dataclass
class DynamicsConfig:
    """Configuration for the full dynamics system."""
    # Field dimensions
    field_dim: int = 88
    
    # Visual dimensions
    visual_height: int = 32
    visual_width: int = 32
    
    # Viscosity
    nu_0: float = 0.1
    nu_1: float = 1.0
    kappa: float = 10.0
    b_floor: float = 1.0
    
    # Resonance
    triad_delta_R: float = 1.0
    
    # Sensory
    sensory_dim: int = 32
    
    # Decay rates
    gamma_sens: float = 0.1
    gamma_affect: float = 0.1


class FullDynamicsSystem:
    """
    Complete dynamics system integrating all framework components.
    
    This is the main integration point for:
    - 12-block state
    - Resonant field dynamics
    - Sensory ingress (ears)
    - Spectral egress (voice)
    - Visual field (eyes)
    - Scene binding
    """
    
    def __init__(self, config: Optional[DynamicsConfig] = None):
        """
        Initialize the full dynamics system.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or DynamicsConfig()
        
        # Initialize components
        self._init_field_components()
        self._init_sensory_components()
        self._init_visual_components()
    
    def _init_field_components(self):
        """Initialize resonant field components."""
        # Resonant field block
        self.field_block = ResonantFieldBlock(k0=1.0)
        
        # Viscosity law
        self.viscosity = ReserveCoupledViscosity(
            nu_0=self.config.nu_0,
            nu_1=self.config.nu_1,
            kappa=self.config.kappa,
            b_floor=self.config.b_floor
        )
        
        # Triad resonance
        self.triad_resonance = TriadResonanceOperator(
            k=self.field_block.k,
            delta_R=self.config.triad_delta_R
        )
        
        # Action forcing
        self.action_forcing = ActionForcingOperator(
            action_dim=16,
            field_dim=self.config.field_dim,
            spectral_focus="mid"
        )
    
    def _init_sensory_components(self):
        """Initialize sensory (ear/voice) components."""
        # Ear operator (sensory ingress)
        self.ear = EarOperator(
            field_dim=self.config.field_dim,
            sensory_dim=self.config.sensory_dim,
            projection_type="learned",
            decay_rate=self.config.gamma_sens
        )
        
        # Context modulation
        self.context = ContextModulationOperator(
            task_dim=16,
            shell_dim=16,
            policy_dim=16,
            sensory_dim=self.config.sensory_dim
        )
        
        # Voice operator (spectral egress)
        self.voice = VoiceOperator(
            field_dim=self.config.field_dim
        )
    
    def _init_visual_components(self):
        """Initialize visual components."""
        # Visual field
        self.visual_field = VisualFieldBlock(
            height=self.config.visual_height,
            width=self.config.visual_width
        )
        
        # Scene binding
        self.scene_binding = SceneBindingFunctional()
        
        # Visual drift
        self.visual_drift = VisualDriftOperator(
            field_height=self.config.visual_height,
            field_width=self.config.visual_width,
            num_octaves=self.config.field_dim
        )
        
        # Visual resonance
        self.visual_resonance = VisualCrossScaleResonance(
            num_octaves=self.config.field_dim
        )
        
        # Eye operator
        self.eye = EyeOperator(
            field_height=self.config.visual_height,
            field_width=self.config.visual_width,
            num_octaves=self.config.field_dim,
            sensory_dim=self.config.sensory_dim
        )
        
        # Imagery operator
        self.imagery = ImageryOperator(
            field_height=self.config.visual_height,
            field_width=self.config.visual_width,
            num_octaves=self.config.field_dim
        )
        
        # Visual egress
        self.visual_egress = VisualEgressOperator(
            field_height=self.config.visual_height,
            field_width=self.config.visual_width,
            num_octaves=self.config.field_dim
        )
    
    def compute_drift(
        self,
        state: TwelveBlockState,
        dt: float = 0.01
    ) -> Dict[str, np.ndarray]:
        """
        Compute the full drift for all components.
        
        Args:
            state: Current 12-block state
            dt: Time step
            
        Returns:
            Dictionary of drift components
        """
        # Get viscosity
        nu = self.viscosity(state.b)
        
        # =========================================
        # Resonant field dynamics
        # =========================================
        
        # Dissipation
        dissipation = self.field_block.compute_dissipation(state.xi_Phi, nu)
        
        # Resonance
        resonance = self.triad_resonance(state.xi_Phi, state.xi_coh)
        
        # Action forcing
        forcing = self.action_forcing(state.xi_action)
        
        # Field drift
        field_drift = dissipation + resonance + forcing
        
        # =========================================
        # Sensory dynamics (ears)
        # =========================================
        
        # Context modulation
        ctx = self.context(state.xi_task, state.xi_shell, state.xi_policy)
        
        # Ear projection with decay
        ear_input = self.ear(state.xi_Phi)
        sensory_drift = ear_input - self.config.gamma_sens * state.xi_sens + ctx
        
        # =========================================
        # Affective dynamics
        # =========================================
        
        # Affect receives from sensory and task (use dot products for dimension matching)
        affect_drift = (
            0.5 * np.dot(state.xi_sens, state.xi_sens) * np.ones_like(state.xi_affect) / len(state.xi_affect) +
            0.5 * np.dot(state.xi_task, state.xi_task) * np.ones_like(state.xi_affect) / len(state.xi_affect) -
            self.config.gamma_affect * state.xi_affect
        )
        
        # =========================================
        # Visual field dynamics
        # =========================================
        
        # Visual viscosity
        nu_vis = nu * 0.5  # Visual may have different viscosity
        
        # External forcing (would come from world in practice)
        # For now, assume zero
        visual_external = np.zeros((
            self.config.visual_height,
            self.config.visual_width,
            self.config.field_dim
        ))
        
        # Internal imagery
        visual_internal = self.imagery(
            state.xi_mem,
            state.xi_task,
            state.xi_affect,
            state.xi_policy,
            state.xi_coh
        )
        
        # Visual resonance
        visual_resonance = self.visual_resonance(
            self.visual_field.V,
            state.xi_coh
        )
        
        # Visual drift
        visual_drift = self.visual_drift.compute_drift(
            V=self.visual_field.V,
            nu_vis=nu_vis,
            resonance=visual_resonance,
            external_forcing=visual_external,
            internal_forcing=visual_internal
        )
        
        return {
            'xi_Phi': field_drift,
            'xi_sens': sensory_drift,
            'xi_affect': affect_drift,
            'visual_field': visual_drift,
        }
    
    def step(
        self,
        state: TwelveBlockState,
        dt: float = 0.01
    ) -> TwelveBlockState:
        """
        Perform one integration step.
        
        Args:
            state: Current state
            dt: Time step
            
        Returns:
            Updated state
        """
        # Compute drift
        drift = self.compute_drift(state, dt)
        
        # Create new state
        new_state = state.copy()
        
        # Update fields (simple forward Euler) with clamping
        new_state.xi_Phi += dt * drift['xi_Phi']
        new_state.xi_Phi = np.clip(new_state.xi_Phi, -10.0, 10.0)
        new_state.xi_sens += dt * drift['xi_sens']
        new_state.xi_affect += dt * drift['xi_affect']
        
        # Update visual field with clamping to prevent overflow
        self.visual_field.V += dt * drift['visual_field']
        self.visual_field.V = np.clip(self.visual_field.V, -10.0, 10.0)
        
        # Budget spend (simplified)
        # In practice, this would be computed from all expenditures
        energy_Phi = state.compute_field_energy()
        field_cost = energy_Phi * dt
        new_state.b = max(0.0, state.b - field_cost)
        
        # Clamp values
        new_state.xi_Phi = np.clip(new_state.xi_Phi, -10.0, 10.0)
        new_state.xi_sens = np.clip(new_state.xi_sens, -5.0, 5.0)
        new_state.xi_affect = np.clip(new_state.xi_affect, -5.0, 5.0)
        
        return new_state
    
    def generate_voice(
        self,
        state: TwelveBlockState,
        claimed_confidence: float = 0.5
    ):
        """
        Generate voice output.
        
        Args:
            state: Current state
            claimed_confidence: Claimed confidence level
            
        Returns:
            VoiceSpectrum
        """
        return self.voice(
            xi_sens=state.xi_sens,
            xi_affect=state.xi_affect,
            xi_task=state.xi_task,
            xi_shell=state.xi_shell,
            xi_policy=state.xi_policy,
            xi_coh=state.xi_coh,
            claimed_confidence=claimed_confidence
        )
    
    def project_visual_to_sensory(self, state: TwelveBlockState) -> np.ndarray:
        """
        Project visual field to sensory.
        
        Args:
            state: Current state
            
        Returns:
            Visual sensory projection
        """
        return self.eye(self.visual_field.V)
    
    def get_visual_scene_binding_energy(self) -> float:
        """
        Get current scene binding energy.
        
        Returns:
            Scene binding energy
        """
        return self.scene_binding.compute_smoothness(self.visual_field.V)


# =============================================================================
# Factory function
# =============================================================================

def create_dynamics_system(
    field_dim: int = 88,
    visual_size: int = 32,
    sensory_dim: int = 32
) -> FullDynamicsSystem:
    """
    Create a configured dynamics system.
    
    Args:
        field_dim: Field dimension (88)
        visual_size: Visual field size (height=width)
        sensory_dim: Sensory dimension
        
    Returns:
        Configured FullDynamicsSystem
    """
    config = DynamicsConfig(
        field_dim=field_dim,
        visual_height=visual_size,
        visual_width=visual_size,
        sensory_dim=sensory_dim
    )
    
    return FullDynamicsSystem(config)


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing full dynamics system...")
    
    # Create system
    system = create_dynamics_system()
    print("System created")
    
    # Create initial state
    state = create_initial_state(budget=10.0)
    print(f"Initial budget: {state.b}")
    print(f"Initial field energy: {state.compute_field_energy():.4f}")
    
    # Run a few steps
    print("\nRunning dynamics steps...")
    for i in range(5):
        state = system.step(state, dt=0.1)
        field_energy = state.compute_field_energy()
        print(f"  Step {i+1}: b={state.b:.3f}, E_Phi={field_energy:.4f}")
    
    # Generate voice
    print("\nGenerating voice...")
    voice = system.generate_voice(state, claimed_confidence=0.7)
    print(f"  Entropy: {voice.entropy:.4f}")
    print(f"  Roughness: {voice.roughness:.4f}")
    print(f"  Confidence: {voice.confidence:.4f}")
    print(f"  Cost: {voice.total_cost:.4f}")
    
    # Visual projections
    print("\nVisual projections...")
    visual_sens = system.project_visual_to_sensory(state)
    print(f"  Visual sensory projection shape: {visual_sens.shape}")
    
    scene_energy = system.get_visual_scene_binding_energy()
    print(f"  Scene binding energy: {scene_energy:.4f}")
    
    print("\nAll tests passed!")
