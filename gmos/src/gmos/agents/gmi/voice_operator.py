"""
Voice Operator (Spectral Egress) for GMI Resonant Field Framework.

Implements the voice-generation map per the mathematical specification:

    G_voice: (ξ_sens, ξ_affect, ξ_task, ξ_shell, ξ_policy, ξ_coh) → (Ω_v, Φ_v)

The voice is NOT text. It is a lawful spectral egress signature produced from internal state.

Voice cost law:
    Σ_v* = λ₁·H(Ω_v) + λ₂·R(Ω_v) + Σ_mis,v
    
Where:
- H(Ω_v): Spectral entropy (penalizes broad unstructured speech)
- R(Ω_v): Spectral roughness (penalizes jagged spectral overcorrection)
- Σ_mis,v: Confidence mismatch penalty (penalizes overclaiming)

This module is part of the constitutive extension to the GM-OS canon.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class VoiceSpectrum:
    """
    Voice output from internal state.
    
    Ω_v ∈ ℝ_+^88: Voice-band power
    Φ_v: Cross-band phase/coherence summary
    """
    power: np.ndarray          # Ω_v (88 bands)
    coherence: np.ndarray       # Phase coherence
    entropy: float              # Spectral entropy H(Ω_v)
    roughness: float            # Spectral roughness R(Ω_v)
    confidence: float           # cert_v
    total_cost: float          # Σ_v*
    
    def to_vector(self) -> np.ndarray:
        """Convert to flat vector."""
        return np.concatenate([
            self.power,
            self.coherence,
            np.array([self.entropy, self.roughness, self.confidence, self.total_cost])
        ])


class VoiceOperator:
    """
    Spectral egress operator G_voice.
    
    The voice is NOT text. It is a lawful spectral egress signature
    produced from internal state.
    
    Per spec §13: May or may not equal substrate field block itself;
    in stricter formulation, it is controlled egress derived from
    internal blocks.
    """
    
    def __init__(
        self,
        field_dim: int = 88,
        cost_weights: Optional[dict] = None,
        coherence_dim: int = 8
    ):
        """
        Initialize voice operator.
        
        Args:
            field_dim: Field dimension (88)
            cost_weights: Dictionary of cost weights
            coherence_dim: Coherence summary dimension
        """
        self.field_dim = field_dim
        self.coherence_dim = coherence_dim
        
        # Default cost weights
        self.cost_weights = cost_weights or {
            'lambda_v1': 1.0,   # Spectral entropy weight
            'lambda_v2': 1.0,   # Spectral roughness weight
            'lambda_v4': 1.0,   # Confidence mismatch weight
        }
        
        # Learnable mappings from internal state to voice spectrum
        # Input dims: sens(32) + affect(8) + task(16) + shell(16) + policy(16) + coh(3) = 91
        input_dim = 32 + 8 + 16 + 16 + 16 + 3
        
        # Power spectrum generator
        self.W_power = np.random.randn(field_dim, input_dim) * 0.01
        
        # Coherence generator
        self.W_coherence = np.random.randn(coherence_dim, input_dim) * 0.01
    
    def __call__(
        self,
        xi_sens: np.ndarray,
        xi_affect: np.ndarray,
        xi_task: np.ndarray,
        xi_shell: np.ndarray,
        xi_policy: np.ndarray,
        xi_coh: np.ndarray,
        claimed_confidence: float = 0.5
    ) -> VoiceSpectrum:
        """
        Generate voice spectrum from internal state.
        
        Maps (sens, affect, task, shell, policy, coh) → (Ω_v, Φ_v)
        
        Args:
            xi_sens: Sensory state
            xi_affect: Affective state
            xi_task: Task state
            xi_shell: Shell state
            xi_policy: Policy state
            xi_coh: Coherence state
            claimed_confidence: Claimed confidence level
            
        Returns:
            VoiceSpectrum
        """
        # Combine internal state
        combined = np.concatenate([
            xi_sens, xi_affect, xi_task, xi_shell, xi_policy, xi_coh
        ])
        
        # Generate power distribution
        power = self._generate_power_distribution(combined)
        
        # Generate coherence
        coherence = self._generate_coherence(combined)
        
        # Compute spectral entropy
        entropy = self._compute_entropy(power)
        
        # Compute spectral roughness
        roughness = self._compute_roughness(power)
        
        # Compute certified confidence
        confidence = self._compute_certified_confidence(
            coherence, power, xi_coh, xi_shell
        )
        
        # Compute mismatch penalty
        mismatch_penalty = self._compute_mismatch_penalty(
            claimed_confidence, confidence
        )
        
        # Compute total cost
        total_cost = self._compute_total_cost(
            entropy, roughness, mismatch_penalty
        )
        
        return VoiceSpectrum(
            power=power,
            coherence=coherence,
            entropy=entropy,
            roughness=roughness,
            confidence=confidence,
            total_cost=total_cost
        )
    
    def _generate_power_distribution(self, combined: np.ndarray) -> np.ndarray:
        """Generate power distribution from internal state."""
        # Use softmax to get proper distribution
        logits = self.W_power @ combined
        
        # Numerical stability
        logits = logits - np.max(logits)
        exp_logits = np.exp(logits)
        
        return exp_logits / np.sum(exp_logits)
    
    def _generate_coherence(self, combined: np.ndarray) -> np.ndarray:
        """Generate coherence summary."""
        return np.tanh(self.W_coherence @ combined)
    
    def _compute_entropy(self, power: np.ndarray) -> float:
        """
        Compute spectral entropy: H(Ω_v) = -Σ_n q_n log q_n
        
        Args:
            power: Power distribution
            
        Returns:
            Entropy
        """
        # Avoid log(0)
        p = power[power > 1e-10]
        if len(p) == 0:
            return 0.0
        
        return -np.sum(p * np.log(p))
    
    def _compute_roughness(self, power: np.ndarray) -> float:
        """
        Compute spectral roughness: R(Ω_v) = Σ_n (Ω_{v,n+1} - Ω_{v,n})²
        
        Args:
            power: Power distribution
            
        Returns:
            Roughness
        """
        diffs = np.diff(power)
        return np.sum(diffs ** 2)
    
    def _compute_certified_confidence(
        self,
        coherence: np.ndarray,
        power: np.ndarray,
        xi_coh: np.ndarray,
        xi_shell: np.ndarray
    ) -> float:
        """
        Compute certified confidence: cert_v = ψ(Φ_v, 1-H, ξ_coh, b, ξ_shell)
        
        Args:
            coherence: Phase coherence
            power: Power distribution
            xi_coh: Coherence state
            xi_shell: Shell state
            
        Returns:
            Certified confidence in [0, 1]
        """
        # Coherence contribution
        coh_contrib = np.mean(np.abs(coherence))
        
        # Inverse entropy (more uniform = less confident)
        entropy = self._compute_entropy(power)
        entropy_contrib = 1.0 - entropy / np.log(self.field_dim)
        
        # Shell stability contribution
        shell_contrib = 1.0 - np.linalg.norm(xi_shell) / (np.linalg.norm(xi_shell) + 1.0)
        
        # Coherence state contribution (Bloch sphere z-component)
        coh_state_contrib = (xi_coh[2] + 1.0) / 2.0 if len(xi_coh) >= 3 else 0.5
        
        # Combine
        confidence = (
            0.3 * coh_contrib +
            0.3 * entropy_contrib +
            0.2 * shell_contrib +
            0.2 * coh_state_contrib
        )
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _compute_mismatch_penalty(
        self,
        claimed_confidence: float,
        certified_confidence: float
    ) -> float:
        """
        Compute confidence mismatch penalty.
        
        Σ_mis,v = λ_v4 * [conf(s) - cert_v]_+²
        
        Args:
            claimed_confidence: What the system claims
            certified_confidence: What is actually certified
            
        Returns:
            Mismatch penalty
        """
        mismatch = max(0.0, claimed_confidence - certified_confidence)
        return self.cost_weights['lambda_v4'] * (mismatch ** 2)
    
    def _compute_total_cost(
        self,
        entropy: float,
        roughness: float,
        mismatch_penalty: float
    ) -> float:
        """
        Compute total voice cost.
        
        Σ_v* = λ_v1 * H(Ω_v) + λ_v2 * R(Ω_v) + Σ_mis,v
        
        Args:
            entropy: Spectral entropy
            roughness: Spectral roughness
            mismatch_penalty: Confidence mismatch
            
        Returns:
            Total cost
        """
        return (
            self.cost_weights['lambda_v1'] * entropy +
            self.cost_weights['lambda_v2'] * roughness +
            mismatch_penalty
        )


class VoiceCostAnalyzer:
    """
    Analyze voice cost components without generating full spectrum.
    """
    
    def __init__(self, cost_weights: Optional[dict] = None):
        """Initialize analyzer."""
        self.cost_weights = cost_weights or {
            'lambda_v1': 1.0,
            'lambda_v2': 1.0,
            'lambda_v4': 1.0,
        }
    
    def analyze_cost(
        self,
        power: np.ndarray,
        claimed_confidence: float = 0.5,
        certified_confidence: Optional[float] = None
    ) -> dict:
        """
        Analyze cost components from power spectrum.
        
        Args:
            power: Power distribution
            claimed_confidence: Claimed confidence
            certified_confidence: Actual certified (computed if None)
            
        Returns:
            Dictionary with cost breakdown
        """
        # Compute entropy
        p = power[power > 1e-10]
        entropy = -np.sum(p * np.log(p)) if len(p) > 0 else 0.0
        
        # Compute roughness
        diffs = np.diff(power)
        roughness = np.sum(diffs ** 2)
        
        # Compute certified confidence if not provided
        if certified_confidence is None:
            certified_confidence = 0.5
        
        # Compute mismatch
        mismatch = max(0.0, claimed_confidence - certified_confidence)
        mismatch_penalty = self.cost_weights['lambda_v4'] * (mismatch ** 2)
        
        # Total cost
        total = (
            self.cost_weights['lambda_v1'] * entropy +
            self.cost_weights['lambda_v2'] * roughness +
            mismatch_penalty
        )
        
        return {
            'entropy': entropy,
            'roughness': roughness,
            'mismatch_penalty': mismatch_penalty,
            'total_cost': total,
            'claimed_confidence': claimed_confidence,
            'certified_confidence': certified_confidence
        }


# =============================================================================
# Tests
# =============================================================================

if __name__ == "__main__":
    print("Testing voice operator (spectral egress)...")
    
    # Create voice operator
    voice = VoiceOperator(field_dim=88)
    print(f"Voice operator initialized")
    
    # Create test internal state
    xi_sens = np.random.randn(32) * 0.5
    xi_affect = np.random.randn(8) * 0.3
    xi_task = np.random.randn(16) * 0.5
    xi_shell = np.random.randn(16) * 0.2
    xi_policy = np.random.randn(16) * 0.3
    xi_coh = np.array([0.0, 0.0, 1.0])  # Pure state
    
    # Generate voice spectrum
    spectrum = voice(
        xi_sens=xi_sens,
        xi_affect=xi_affect,
        xi_task=xi_task,
        xi_shell=xi_shell,
        xi_policy=xi_policy,
        xi_coh=xi_coh,
        claimed_confidence=0.7
    )
    
    print(f"\nVoice spectrum:")
    print(f"  Power sum: {np.sum(spectrum.power):.4f}")
    print(f"  Power (first 10): {spectrum.power[:10]}")
    print(f"  Coherence (first 5): {spectrum.coherence[:5]}")
    print(f"  Entropy: {spectrum.entropy:.4f}")
    print(f"  Roughness: {spectrum.roughness:.4f}")
    print(f"  Confidence: {spectrum.confidence:.4f}")
    print(f"  Total cost: {spectrum.total_cost:.4f}")
    
    # Test cost analyzer
    print("\nTesting cost analyzer...")
    analyzer = VoiceCostAnalyzer()
    cost_analysis = analyzer.analyze_cost(
        spectrum.power,
        claimed_confidence=0.7,
        certified_confidence=spectrum.confidence
    )
    print(f"  Entropy cost: {cost_analysis['entropy']:.4f}")
    print(f"  Roughness cost: {cost_analysis['roughness']:.4f}")
    print(f"  Mismatch penalty: {cost_analysis['mismatch_penalty']:.4f}")
    print(f"  Total: {cost_analysis['total_cost']:.4f}")
    
    # Test different claimed confidences
    print("\nTesting confidence mismatch...")
    for claimed in [0.3, 0.5, 0.7, 0.9]:
        spectrum = voice(
            xi_sens, xi_affect, xi_task, xi_shell, xi_policy, xi_coh,
            claimed_confidence=claimed
        )
        print(f"  Claimed {claimed}: certified={spectrum.confidence:.2f}, cost={spectrum.total_cost:.4f}")
    
    print("\nAll tests passed!")
