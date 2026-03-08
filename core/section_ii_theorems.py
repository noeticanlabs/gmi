"""
Section II Theorem Implementations for the GMI Universal Cognition Engine.

This module provides formal theorem implementations corresponding to
Section II — Discrete Governance and the Oplax Ledger from the canonical document.

Reference: docs/section_ii_discrete_governance.md

Tag Legend:
- [AXIOM] Foundational definitions and assumptions
- [POLICY] Governing laws and dynamics
- [PROVED] Theorems with implementation verification
- [LEMMA-NEEDED] Items requiring additional proof work
- [CONTRACT] Interface contract requirements
- [DEFINITION] Formal definitions
- [ORDER] Ordering relations
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Callable, Protocol
from abc import ABC, abstractmethod
import hashlib


# =============================================================================
# Section II Theorem Protocols
# =============================================================================

class Theorem(ABC):
    """Base class for Section II theorems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Theorem name."""
        pass
    
    @property
    @abstractmethod
    def section_ref(self) -> str:
        """Section reference (e.g., '§2.3')."""
        pass
    
    @property
    @abstractmethod
    def tag(self) -> str:
        """Tag: PROVED, LEMMA-NEEDED, etc."""
        pass
    
    @property
    @abstractmethod
    def statement(self) -> str:
        """Mathematical statement."""
        pass


# =============================================================================
# PDES Projection — Definition
# =============================================================================

@dataclass
class PDESProjection(Theorem):
    """
    PDES Projection — Definition §2.1
    
    # [POLICY]
    
    There exists a many-to-one projection Π: X → Y from microscopic lawful
    paths to observable records, with hidden fiber F_R.
    
    Reference: docs/section_ii_discrete_governance.md §2.1
    """
    name: str = "PDES Projection"
    section_ref: str = "§2.1"
    tag: str = "POLICY"
    statement: str = "Π: X → Y many-to-one with fiber F_R"
    
    def project(self, trajectory: np.ndarray, record_type: str = "discrete") -> np.ndarray:
        """
        Project continuous trajectory to discrete record.
        
        Args:
            trajectory: Full microscopic path
            record_type: Type of projection
            
        Returns:
            Coarse-grained observable record
        """
        # Simplified: just sample at discrete intervals
        return trajectory[::max(1, len(trajectory) // 10)]


# =============================================================================
# Canonical Envelope — Definition
# =============================================================================

@dataclass
class CanonicalEnvelope(Theorem):
    """
    Canonical Envelope — Definition §2.2
    
    # [DEFINITION]
    
    The verifiable discrete thermodynamic cost of record R is the canonical envelope:
        Ŵ(R) = sup{ξ ∈ F_R} W(ξ)
    
    Reference: docs/section_ii_discrete_governance.md §2.2
    """
    name: str = "Canonical Envelope"
    section_ref: str = "§2.2"
    tag: str = "DEFINITION"
    statement: str = "Ŵ(R) = sup{ξ ∈ F_R} W(ξ)"
    
    def compute_envelope(
        self,
        work_values: np.ndarray
    ) -> float:
        """
        Compute canonical envelope as supremum of work values.
        
        Args:
            work_values: Array of work values from hidden fiber
            
        Returns:
            Supremum (safe upper bound)
        """
        return float(np.max(work_values))


# =============================================================================
# Oplax Subadditivity — Theorem 6.1
# =============================================================================

@dataclass
class OplaxSubadditivityTheorem(Theorem):
    """
    Oplax Subadditivity — Theorem 6.1 / §2.3
    
    # [PROVED]
    
    If microscopic work is additive, then the macroscopic envelope obeys:
        Ŵ(R₂ ⊙ R₁) ≤ Ŵ(R₁) + Ŵ(R₂)
    
    Reference: docs/section_ii_discrete_governance.md §2.3
    """
    name: str = "Oplax Subadditivity"
    section_ref: str = "§2.3"
    tag: str = "PROVED"
    statement: str = "Ŵ(R₂ ⊙ R₁) ≤ Ŵ(R₁) + Ŵ(R₂)"
    
    def verify_subadditivity(
        self,
        envelope_R1: float,
        envelope_R2: float,
        envelope_composite: float,
        tolerance: float = 1e-10
    ) -> Tuple[bool, str]:
        """
        Verify oplax subadditivity.
        
        Args:
            envelope_R1: Envelope for R1
            envelope_R2: Envelope for R2
            envelope_composite: Envelope for composite R2 ⊙ R1
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, message)
        """
        if envelope_composite <= envelope_R1 + envelope_R2 + tolerance:
            return True, f"Oplax verified: {envelope_composite} ≤ {envelope_R1} + {envelope_R2}"
        else:
            return False, f"Oplax violated: {envelope_composite} > {envelope_R1} + {envelope_R2}"


# =============================================================================
# Coh Discrete Object — Definition
# =============================================================================

@dataclass
class CohDiscreteObject(Theorem):
    """
    Coh Discrete Object — Definition §3
    
    # [DEFINITION]
    
    A discrete governed system is a 5-tuple:
        S = (X, V, Spend, Defect, RV)
    
    Reference: docs/section_ii_discrete_governance.md §3
    """
    name: str = "Coh Discrete Object"
    section_ref: str = "§3"
    tag: str = "DEFINITION"
    statement: str = "S = (X, V, Spend, Defect, RV)"
    
    # Default values for the discrete object
    state_space_dim: int = 1
    
    def create_discrete_system(
        self,
        violation_fn: Callable[[np.ndarray], float],
        spend_fn: Callable[[dict], float],
        defect_fn: Callable[[dict], float],
        verifier_fn: Callable
    ) -> dict:
        """
        Create a Coh discrete object.
        
        Args:
            violation_fn: V: X → ℝ≥0
            spend_fn: Spend: R → ℝ≥0
            defect_fn: Defect: R → ℝ≥0
            verifier_fn: RV predicate
            
        Returns:
            Discrete governed system dictionary
        """
        return {
            "X": np.zeros(self.state_space_dim),
            "V": violation_fn,
            "Spend": spend_fn,
            "Defect": defect_fn,
            "RV": verifier_fn
        }


# =============================================================================
# Discrete Descent Law — Axiom/Contract
# =============================================================================

@dataclass
class DiscreteDescentLaw(Theorem):
    """
    Discrete Descent Law — §4
    
    # [AXIOM] / [CONTRACT]
    
    A transition x →r x' is accepted only if:
        V(x') + Spend(r) ≤ V(x) + Defect(r)
    
    Reference: docs/section_ii_discrete_governance.md §4
    """
    name: str = "Discrete Descent Law"
    section_ref: str = "§4"
    tag: str = "AXIOM"
    statement: str = "V(x') + Spend(r) ≤ V(x) + Defect(r)"
    
    def verify_descent(
        self,
        v_before: float,
        v_after: float,
        spend: float,
        defect: float
    ) -> Tuple[bool, str]:
        """
        Verify discrete descent law.
        
        Args:
            v_before: V(x)
            v_after: V(x')
            spend: Spend(r)
            defect: Defect(r)
            
        Returns:
            (is_accepted, message)
        """
        lhs = v_after + spend
        rhs = v_before + defect
        
        if lhs <= rhs:
            return True, f"ACCEPT: {v_after} + {spend} ≤ {v_before} + {defect}"
        else:
            return False, f"REJECT: {v_after} + {spend} > {v_before} + {defect}"


# =============================================================================
# Descent Consequence — Theorem
# =============================================================================

@dataclass
class DescentConsequence(Theorem):
    """
    Descent Consequence — §4.1
    
    # [PROVED]
    
    If Defect(r) ≤ Spend(r), then V(x') ≤ V(x).
    
    Reference: docs/section_ii_discrete_governance.md §4.1
    """
    name: str = "Descent Consequence"
    section_ref: str = "§4.1"
    tag: str = "PROVED"
    statement: str = "Defect(r) ≤ Spend(r) ⇒ V(x') ≤ V(x)"
    
    def is_non_increasing(
        self,
        spend: float,
        defect: float,
        v_before: float,
        v_after: float,
        tolerance: float = 1e-10
    ) -> Tuple[bool, str]:
        """
        Check if transition is non-increasing in violation.
        
        Args:
            spend: Spend(r)
            defect: Defect(r)
            v_before: V(x)
            v_after: V(x')
            tolerance: Numerical tolerance
            
        Returns:
            (is_non_increasing, message)
        """
        if defect <= spend + tolerance:
            if v_after <= v_before + tolerance:
                return True, f"Non-increasing: V(x')={v_after} ≤ V(x)={v_before}"
            else:
                return False, f"Increasing violation: V(x')={v_after} > V(x)={v_before}"
        else:
            return False, f"Defect > Spend: {defect} > {spend}"


# =============================================================================
# Positive-Variation Dominance — Theorem 8.2
# =============================================================================

@dataclass
class PositiveVariationDominance(Theorem):
    """
    Positive-Variation Dominance — Theorem 8.2 / §6
    
    # [PROVED]
    
    V(x(T)) - V(x(0)) ≤ ∫₀ᵀ (dV/dt)_+ dt
    
    Reference: docs/section_ii_discrete_governance.md §6
    """
    name: str = "Positive-Variation Dominance"
    section_ref: str = "§6"
    tag: str = "PROVED"
    statement: str = "V(T) - V(0) ≤ ∫₀ᵀ (dV/dt)_+ dt"
    
    def compute_positive_variation(
        self,
        v_trajectory: np.ndarray,
        dt: float = 1.0
    ) -> float:
        """
        Compute positive variation from trajectory.
        
        Args:
            v_trajectory: V(x(t)) values over time
            dt: Time step
            
        Returns:
            Positive variation integral
        """
        dv = np.diff(v_trajectory)
        positive_part = np.maximum(dv, 0.0)
        return float(np.sum(positive_part)) * dt
    
    def verify_dominance(
        self,
        v_initial: float,
        v_final: float,
        positive_variation: float,
        tolerance: float = 1e-10
    ) -> Tuple[bool, str]:
        """
        Verify positive variation dominates endpoint difference.
        
        Args:
            v_initial: V(x(0))
            v_final: V(x(T))
            positive_variation: ∫(dV/dt)_+ dt
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, message)
        """
        endpoint_diff = v_final - v_initial
        
        if endpoint_diff <= positive_variation + tolerance:
            return True, f"Dominance verified: {endpoint_diff} ≤ {positive_variation}"
        else:
            return False, f"Dominance violated: {endpoint_diff} > {positive_variation}"


# =============================================================================
# Discrete Budget Update — Axiom/Contract
# =============================================================================

@dataclass
class DiscreteBudgetUpdate(Theorem):
    """
    Discrete Budget Update — §7
    
    # [AXIOM] / [CONTRACT]
    
    B_{k+1} = B_k - κ·D̂_k - τ_k ≥ 0
    
    Reference: docs/section_ii_discrete_governance.md §7
    """
    name: str = "Discrete Budget Update"
    section_ref: str = "§7"
    tag: str = "AXIOM"
    statement: str = "B_{k+1} = B_k - κ·D̂_k - τ_k ≥ 0"
    
    kappa: float = 1.0  # Budget consumption rate
    
    def compute_next_budget(
        self,
        b_current: float,
        dissipation_proxy: float,
        truncation_defect: float
    ) -> float:
        """
        Compute next budget after dissipation.
        
        Args:
            b_current: B_k
            dissipation_proxy: D̂_k
            truncation_defect: τ_k
            
        Returns:
            B_{k+1}
        """
        return max(0.0, b_current - self.kappa * dissipation_proxy - truncation_defect)
    
    def is_valid(
        self,
        b_current: float,
        dissipation_proxy: float,
        truncation_defect: float,
        tolerance: float = 1e-10
    ) -> Tuple[bool, str]:
        """
        Verify budget update is valid (non-negative).
        
        Args:
            b_current: B_k
            dissipation_proxy: D̂_k
            truncation_defect: τ_k
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, message)
        """
        b_next = self.compute_next_budget(b_current, dissipation_proxy, truncation_defect)
        
        if b_next >= -tolerance:
            return True, f"Budget valid: B_{k+1} = {b_next} ≥ 0"
        else:
            return False, f"Budget exhausted: B_{k+1} = {b_next} < 0"


# =============================================================================
# Finite Budget Bound — Theorem
# =============================================================================

@dataclass
class FiniteBudgetBound(Theorem):
    """
    Finite Budget Bound — §7.2
    
    # [PROVED]
    
    Σ(κ·D̂_k + τ_k) ≤ B_0
    
    Reference: docs/section_ii_discrete_governance.md §7.2
    """
    name: str = "Finite Budget Bound"
    section_ref: str = "§7.2"
    tag: str = "PROVED"
    statement: str = "Σ(κ·D̂_k + τ_k) ≤ B_0"
    
    kappa: float = 1.0
    
    def verify_budget_bound(
        self,
        b_initial: float,
        b_final: float,
        dissipation_proxies: np.ndarray,
        truncation_defects: np.ndarray,
        tolerance: float = 1e-10
    ) -> Tuple[bool, str]:
        """
        Verify finite budget bound.
        
        Args:
            b_initial: B_0
            b_final: B_N
            dissipation_proxies: Array of D̂_k
            truncation_defects: Array of τ_k
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, message)
        """
        total_spent = b_initial - b_final
        total_dissipation = np.sum(self.kappa * dissipation_proxies + truncation_defects)
        
        if total_spent <= total_dissipation + tolerance:
            return True, f"Budget bound: {total_spent} ≤ {total_dissipation}"
        else:
            return False, f"Budget violation: {total_spent} > {total_dissipation}"


# =============================================================================
# Oplax Morphism — Definition
# =============================================================================

@dataclass
class OplaxMorphism(Theorem):
    """
    Oplax Morphism — Definition §9
    
    # [DEFINITION]
    
    A morphism f: A → B preserves legality up to slack Δ_f.
    
    Reference: docs/section_ii_discrete_governance.md §9
    """
    name: str = "Oplax Morphism"
    section_ref: str = "§9"
    tag: str = "DEFINITION"
    statement: str = "B.V(f(x')) + B.Spend(f(r)) ≤ B.V(f(x)) + B.Defect(f(r)) + Δ_f"
    
    def compute_slack(
        self,
        v_before_target: float,
        v_after_target: float,
        spend_target: float,
        defect_target: float,
        v_before_source: float,
        v_after_source: float,
        spend_source: float,
        defect_source: float
    ) -> float:
        """
        Compute slack introduced by morphism.
        
        Args:
            v_before_target: B.V(f(x))
            v_after_target: B.V(f(x'))
            spend_target: B.Spend(f(r))
            defect_target: B.Defect(f(r))
            v_before_source: A.V(x)
            v_after_source: A.V(x')
            spend_source: A.Spend(r)
            defect_source: A.Defect(r)
            
        Returns:
            Slack Δ_f
        """
        lhs_target = v_after_target + spend_target
        rhs_target = v_before_target + defect_target
        
        lhs_source = v_after_source + spend_source
        rhs_source = v_before_source + defect_source
        
        # Slack is how much more the target inequality allows
        return max(0.0, lhs_target - rhs_target)


# =============================================================================
# Pos-Enrichment by Slack — Order
# =============================================================================

@dataclass
class PosEnrichment(Theorem):
    """
    Pos-Enrichment by Slack — §9.1
    
    # [ORDER]
    
    f ≤ g iff Δ_f ≤ Δ_g
    
    Reference: docs/section_ii_discrete_governance.md §9.1
    """
    name: str = "Pos-Enrichment by Slack"
    section_ref: str = "§9.1"
    tag: str = "ORDER"
    statement: str = "f ≤ g iff Δ_f ≤ Δ_g"
    
    def compare_morphisms(
        self,
        slack_f: float,
        slack_g: float,
        tolerance: float = 1e-10
    ) -> Tuple[str, str]:
        """
        Compare morphisms by slack.
        
        Args:
            slack_f: Δ_f
            slack_g: Δ_g
            tolerance: Numerical tolerance
            
        Returns:
            (comparison, message)
        """
        if abs(slack_f - slack_g) <= tolerance:
            return "f ≈ g", f"Equal slack: Δ_f = Δ_g = {(slack_f + slack_g) / 2}"
        elif slack_f < slack_g:
            return "f < g", f"Tighter: Δ_f = {slack_f} < Δ_g = {slack_g}"
        else:
            return "f > g", f"Weaker: Δ_f = {slack_f} > Δ_g = {slack_g}"


# =============================================================================
# Canon Profile — Contract
# =============================================================================

@dataclass
class CanonProfile(Theorem):
    """
    Canon Profile — Contract §11
    
    # [CONTRACT]
    
    H_{n+1} = SHA256(tag | H_n | JCS(r_n))
    
    Reference: docs/section_ii_discrete_governance.md §11
    """
    name: str = "Canon Profile"
    section_ref: str = "§11"
    tag: str = "CONTRACT"
    statement: str = "H_{n+1} = SHA256(tag | H_n | JCS(r_n))"
    
    digest_tag: str = "COH_V1"
    
    def compute_digest(
        self,
        prev_digest: str,
        receipt_json: str
    ) -> str:
        """
        Compute next chain digest.
        
        Args:
            prev_digest: H_n
            receipt_json: JCS(r_n) - canonical JSON
            
        Returns:
            H_{n+1}
        """
        combined = f"{self.digest_tag}|{prev_digest}|{receipt_json}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def verify_digest(
        self,
        prev_digest: str,
        receipt_json: str,
        claimed_next_digest: str
    ) -> Tuple[bool, str]:
        """
        Verify chain digest.
        
        Args:
            prev_digest: H_n
            receipt_json: JCS(r_n)
            claimed_next_digest: Claimed H_{n+1}
            
        Returns:
            (is_valid, message)
        """
        computed = self.compute_digest(prev_digest, receipt_json)
        
        if computed == claimed_next_digest:
            return True, f"Digest verified: {computed[:16]}..."
        else:
            return False, f"Digest mismatch: computed={computed[:16]}... vs claimed={claimed_next_digest[:16]}..."


# =============================================================================
# Theorem Factory
# =============================================================================

class SectionIITheorems:
    """
    Factory class for all Section II theorems.
    
    Usage:
        theorems = SectionIITheorems()
        
        # Verify discrete descent
        is_accepted, msg = theorems.descent_law.verify(...)
        
        # Verify oplax subadditivity
        is_valid, msg = theorems.oplax_subadditivity.verify_subadditivity(...)
        
        # Verify budget bound
        is_valid, msg = theorems.finite_budget_bound.verify_budget_bound(...)
    """
    
    def __init__(self, **kwargs):
        """
        Initialize all theorems with optional parameters.
        
        Args:
            kappa: Budget consumption rate (default: 1.0)
            digest_tag: Digest tag for canon profile (default: COH_V1)
        """
        # PDES
        self.pdes_projection = PDESProjection()
        
        # Canonical envelope
        self.canonical_envelope = CanonicalEnvelope()
        
        # Oplax subadditivity
        self.oplax_subadditivity = OplaxSubadditivityTheorem()
        
        # Coh discrete object
        self.coh_discrete = CohDiscreteObject()
        
        # Discrete descent law
        self.descent_law = DiscreteDescentLaw()
        
        # Descent consequence
        self.descent_consequence = DescentConsequence()
        
        # Positive variation
        self.positive_variation = PositiveVariationDominance()
        
        # Discrete budget update
        self.budget_update = DiscreteBudgetUpdate(
            kappa=kwargs.get('kappa', 1.0)
        )
        
        # Finite budget bound
        self.finite_budget_bound = FiniteBudgetBound(
            kappa=kwargs.get('kappa', 1.0)
        )
        
        # Oplax morphism
        self.oplax_morphism = OplaxMorphism()
        
        # Pos-enrichment
        self.pos_enrichment = PosEnrichment()
        
        # Canon profile
        self.canon_profile = CanonProfile(
            digest_tag=kwargs.get('digest_tag', 'COH_V1')
        )
    
    def get_theorem_summary(self) -> dict:
        """Get summary of all theorems."""
        return {
            "PDES Projection": {
                "name": self.pdes_projection.name,
                "tag": self.pdes_projection.tag,
                "statement": self.pdes_projection.statement
            },
            "Canonical Envelope": {
                "name": self.canonical_envelope.name,
                "tag": self.canonical_envelope.tag,
                "statement": self.canonical_envelope.statement
            },
            "Oplax Subadditivity": {
                "name": self.oplax_subadditivity.name,
                "tag": self.oplax_subadditivity.tag,
                "statement": self.oplax_subadditivity.statement
            },
            "Coh Discrete Object": {
                "name": self.coh_discrete.name,
                "tag": self.coh_discrete.tag,
                "statement": self.coh_discrete.statement
            },
            "Discrete Descent Law": {
                "name": self.descent_law.name,
                "tag": self.descent_law.tag,
                "statement": self.descent_law.statement
            },
            "Descent Consequence": {
                "name": self.descent_consequence.name,
                "tag": self.descent_consequence.tag,
                "statement": self.descent_consequence.statement
            },
            "Positive Variation": {
                "name": self.positive_variation.name,
                "tag": self.positive_variation.tag,
                "statement": self.positive_variation.statement
            },
            "Discrete Budget Update": {
                "name": self.budget_update.name,
                "tag": self.budget_update.tag,
                "statement": self.budget_update.statement
            },
            "Finite Budget Bound": {
                "name": self.finite_budget_bound.name,
                "tag": self.finite_budget_bound.tag,
                "statement": self.finite_budget_bound.statement
            },
            "Oplax Morphism": {
                "name": self.oplax_morphism.name,
                "tag": self.oplax_morphism.tag,
                "statement": self.oplax_morphism.statement
            },
            "Pos-Enrichment": {
                "name": self.pos_enrichment.name,
                "tag": self.pos_enrichment.tag,
                "statement": self.pos_enrichment.statement
            },
            "Canon Profile": {
                "name": self.canon_profile.name,
                "tag": self.canon_profile.tag,
                "statement": self.canon_profile.statement
            }
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_section_ii_theorems(**kwargs) -> SectionIITheorems:
    """
    Factory function to create configured Section II theorems.
    
    Args:
        **kwargs: Theorem parameters
        
    Returns:
        SectionIITheorems instance
    """
    return SectionIITheorems(**kwargs)


# =============================================================================
# Tag Reference
# =============================================================================

"""
TAG REFERENCE (from docs/section_ii_discrete_governance.md):

[POLICY]      - PDES projection system
[DEFINITION]  - Canonical envelope, Coh object, Oplax morphism
[PROVED]      - Oplax subadditivity, descent consequence, positive variation dominance, finite budget bound
[AXIOM]       - Discrete descent law, discrete budget update
[CONTRACT]    - Canon profile, receipt schemas, verifier predicate
[ORDER]       - Pos-enrichment by slack
[LEMMA-NEEDED] - Endpoint sampling failure, chattering theorem
"""
