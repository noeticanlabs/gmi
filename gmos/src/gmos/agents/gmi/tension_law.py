"""
GMI Tension Law v1 - Per GMI Tension Law Appendix.

Implements the canonical executable tension law per the appendix:

V_GMI(x) = Σ_α w_α |r^α(x)|² + Φ_B(b) + Φ_A(x)

Where residual components are:
- r^obs: Observation residual (reality prediction error)
- r^mem: Memory coherence residual
- r^goal: Goal progress residual
- r^cons: Consistency/contradiction residual
- r^plan: Planning precondition/deadline residual
- r^act: Action risk residual
- r^meta: Meta-stability (oscillation/indecision) residual

Plus barrier terms:
- Φ_B(b): Budget barrier (diverges at reserve)
- Φ_A(x): Anchor-authority interlock penalty
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import time


# === Residual Types ===

@dataclass
class ResidualVector:
    """
    Container for all residual components.
    
    Per appendix, r(x) = (r^obs, r^mem, r^goal, r^cons, r^plan, r^act, r^meta)
    """
    # Observation residual (observation vs prediction)
    obs: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Memory coherence residual
    mem: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Goal residual
    goal: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Consistency residual (contradictions, assumptions, ambiguities)
    cons: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Planning residual (precondition violations, deadline debt)
    plan: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Action risk residual
    act: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Meta-stability residual (oscillation, uncertainty, flips)
    meta: np.ndarray = field(default_factory=lambda: np.array([]))
    
    def to_dict(self) -> Dict[str, List[float]]:
        """Serialize to dictionary."""
        return {
            "obs": self.obs.tolist() if len(self.obs) else [],
            "mem": self.mem.tolist() if len(self.mem) else [],
            "goal": self.goal.tolist() if len(self.goal) else [],
            "cons": self.cons.tolist() if len(self.cons) else [],
            "plan": self.plan.tolist() if len(self.plan) else [],
            "act": self.act.tolist() if len(self.act) else [],
            "meta": self.meta.tolist() if len(self.meta) else [],
        }


@dataclass
class TensionWeights:
    """
    Weight coefficients for residual components.
    
    Per appendix: w_α > 0 for each component α
    """
    w_obs: float = 1.0
    w_mem: float = 1.0
    w_goal: float = 1.0
    w_cons: float = 1.0
    w_plan: float = 1.0
    w_act: float = 1.0
    w_meta: float = 1.0
    
    # Barrier weights
    kappa_budget: float = 1.0
    zeta_auth: float = 1.0
    zeta_anchor: float = 1.0
    zeta_scope: float = 1.0


# === Observation Residual (Section 2) ===

def compute_observation_residual(
    predicted_s: np.ndarray,
    actual_s: np.ndarray,
    confidence_weights: np.ndarray,
) -> np.ndarray:
    """
    Compute observation residual r^obs(x) = D_A(ŝ - s)
    
    Per appendix §2:
    - If sensory channel is strongly anchored, mismatch hurts more
    - If weakly anchored/noisy, contributes less
    
    Args:
        predicted_s: Predicted sensory observation ŝ
        actual_s: Actual anchored sensory vector s
        confidence_weights: Per-channel confidence a_i >= 0
        
    Returns:
        Residual vector
    """
    diff = predicted_s - actual_s
    D_A = np.sqrt(confidence_weights + 1e-8)  # diag(√a_i)
    return D_A * diff


def compute_observation_potential(
    predicted_s: np.ndarray,
    actual_s: np.ndarray,
    confidence_weights: np.ndarray,
    w_obs: float,
) -> float:
    """
    Compute V_obs(x) = w_obs * Σ a_i(ŝ_i - s_i)²
    
    Args:
        predicted_s: Predicted sensory
        actual_s: Actual sensory
        confidence_weights: Channel weights
        w_obs: Weight coefficient
        
    Returns:
        Observation potential energy
    """
    residual = compute_observation_residual(predicted_s, actual_s, confidence_weights)
    return w_obs * np.sum(residual ** 2)


# === Memory Coherence Residual (Section 3) ===

@dataclass
class MemoryFragmentationMetrics:
    """Memory fragmentation metrics per appendix."""
    stale_count: int = 0
    stale_penalty: float = 0.0
    conflicted_count: int = 0
    conflicted_penalty: float = 0.0
    lossy_count: int = 0
    lossy_penalty: float = 0.0


def compute_memory_residual(
    predicted_m: np.ndarray,
    actual_m: np.ndarray,
    memory_weights: np.ndarray,
) -> np.ndarray:
    """
    Compute memory residual r^mem(x) = D_M(Û - m)
    
    Args:
        predicted_m: Memory implied by current latent state
        actual_m: Active retrieved memory slice
        memory_weights: Weight matrix D_M
        
    Returns:
        Memory residual vector
    """
    diff = predicted_m - actual_m
    D_M = np.sqrt(memory_weights + 1e-8)
    return D_M * diff


def compute_memory_potential(
    predicted_m: np.ndarray,
    actual_m: np.ndarray,
    memory_weights: np.ndarray,
    w_mem: float,
    fragmentation: MemoryFragmentationMetrics,
    w_frag: float,
) -> float:
    """
    Compute V_mem(x) = w_mem * Σ μ_j(Û_j - m_j)² + w_frag * Frag(m)
    
    Args:
        predicted_m: Predicted memory
        actual_m: Actual memory
        memory_weights: Memory weights
        w_mem: Memory weight
        fragmentation: Fragmentation metrics
        w_frag: Fragmentation weight
        
    Returns:
        Memory potential energy
    """
    residual = compute_memory_residual(predicted_m, actual_m, memory_weights)
    residual_term = w_mem * np.sum(residual ** 2)
    
    # Fragmentation term
    frag_term = w_frag * (
        fragmentation.stale_penalty +
        fragmentation.conflicted_penalty +
        fragmentation.lossy_penalty
    )
    
    return residual_term + frag_term


# === Goal Residual (Section 4) ===

@dataclass
class GoalState:
    """Goal state with target and progress."""
    goal_id: str
    target_value: float
    current_progress: float
    weight: float = 1.0
    is_inequality: bool = False
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


def compute_goal_residual(
    goals: List[GoalState],
) -> Tuple[np.ndarray, float]:
    """
    Compute goal residual and potential.
    
    Per appendix §4:
    - For equality: e_k(x) = ψ_k - y_k*
    - For inequality: use hinge residuals
    
    Args:
        goals: List of active goals
        
    Returns:
        (residual vector, potential value)
    """
    residuals = []
    potential = 0.0
    
    for goal in goals:
        error = goal.current_progress - goal.target_value
        
        if goal.is_inequality and goal.lower_bound is not None:
            # Hinge residual for lower bound
            e_plus = max(0.0, error - goal.upper_bound) if goal.upper_bound else 0.0
            e_minus = max(0.0, goal.lower_bound - error)
            residual = np.array([e_plus, e_minus])
            potential += goal.weight * (e_plus ** 2 + e_minus ** 2)
        else:
            residual = np.array([error])
            potential += goal.weight * (error ** 2)
        
        residuals.append(np.sqrt(goal.weight) * residual)
    
    if residuals:
        return np.concatenate(residuals), potential
    return np.array([]), 0.0


# === Consistency Residual (Section 5) ===

@dataclass
class ConsistencyMetrics:
    """Consistency state per appendix."""
    contradictions: List[float] = field(default_factory=list)  # q_i ∈ [0,1]
    assumptions: List[float] = field(default_factory=list)       # a_j ∈ [0,1]
    ambiguities: List[float] = field(default_factory=list)      # b_k ∈ [0,1]


def compute_consistency_potential(
    consistency: ConsistencyMetrics,
    w_cons: float,
    lambda_weight: float = 1.0,
    rho_weight: float = 1.0,
    sigma_weight: float = 1.0,
) -> float:
    """
    Compute V_cons(x) = w_cons * (Σ λ_i q_i² + Σ ρ_j a_j² + Σ σ_k b_k²)
    
    Per appendix §5: contradictions become literal paid-for structure
    
    Args:
        consistency: Consistency metrics
        w_cons: Overall weight
        lambda_weight: Weight for contradictions
        rho_weight: Weight for assumptions
        sigma_weight: Weight for ambiguities
        
    Returns:
        Consistency potential energy
    """
    term = 0.0
    
    # Contradictions
    for q in consistency.contradictions:
        term += lambda_weight * (q ** 2)
    
    # Assumptions
    for a in consistency.assumptions:
        term += rho_weight * (a ** 2)
    
    # Ambiguities
    for b in consistency.ambiguities:
        term += sigma_weight * (b ** 2)
    
    return w_cons * term


# === Planning Residual (Section 6) ===

@dataclass
class PlanNode:
    """Planning node with metrics."""
    node_id: str
    precondition_violation: float = 0.0
    deadline_debt: float = 0.0
    rollback_risk: float = 0.0
    weight_precond: float = 1.0
    weight_deadline: float = 1.0
    weight_rollback: float = 1.0


def compute_planning_potential(
    plan_nodes: List[PlanNode],
    w_plan: float,
) -> float:
    """
    Compute V_plan(x) = w_plan * Σ_j (α_j p_j² + β_j d_j² + γ_j u_j²)
    
    Per appendix §6
    
    Args:
        plan_nodes: Active plan graph nodes
        w_plan: Planning weight
        
    Returns:
        Planning potential energy
    """
    potential = 0.0
    
    for node in plan_nodes:
        potential += (
            node.weight_precond * (node.precondition_violation ** 2) +
            node.weight_deadline * (node.deadline_debt ** 2) +
            node.weight_rollback * (node.rollback_risk ** 2)
        )
    
    return w_plan * potential


# === Action Risk Residual (Section 7) ===

@dataclass
class PendingAction:
    """Pending action with risk metrics."""
    action_id: str
    external_risk: float = 0.0      # R_ext(u)
    authority_mismatch: float = 0.0  # R_auth(u)
    irreversibility: float = 0.0     # R_irr(u)
    anchor_insufficiency: float = 0.0 # R_anch(u)
    weight_ext: float = 1.0
    weight_auth: float = 1.0
    weight_irr: float = 1.0
    weight_anch: float = 1.0


def compute_action_potential(
    pending_actions: List[PendingAction],
    w_act: float,
) -> float:
    """
    Compute V_act(x) = w_act * Σ_u (a_u R_ext² + b_u R_auth² + c_u R_irr² + d_u R_anch²)
    
    Per appendix §7: dangerous/under-authorized actions create tension spikes
    
    Args:
        pending_actions: List of pending actions
        w_act: Action weight
        
    Returns:
        Action risk potential energy
    """
    potential = 0.0
    
    for action in pending_actions:
        potential += (
            action.weight_ext * (action.external_risk ** 2) +
            action.weight_auth * (action.authority_mismatch ** 2) +
            action.weight_irr * (action.irreversibility ** 2) +
            action.weight_anch * (action.anchor_insufficiency ** 2)
        )
    
    return w_act * potential


# === Meta-stability Residual (Section 8) ===

@dataclass
class MetaStabilityMetrics:
    """Meta-stability metrics per appendix."""
    oscillation_magnitude: float = 0.0    # ζ
    self_uncertainty: float = 0.0        # υ
    recent_flip_count: int = 0            # Δ_flip


def compute_meta_potential(
    meta: MetaStabilityMetrics,
    w_meta: float,
    eta_osc: float = 1.0,
    eta_unc: float = 1.0,
    eta_flip: float = 1.0,
) -> float:
    """
    Compute V_meta(x) = w_meta * (η_1 ζ² + η_2 υ² + η_3 Δ_flip)
    
    Per appendix §8: indecisive flailing becomes visible
    
    Args:
        meta: Meta-stability metrics
        w_meta: Meta weight
        eta_osc: Oscillation weight
        eta_unc: Uncertainty weight
        eta_flip: Flip count weight
        
    Returns:
        Meta-stability potential energy
    """
    return w_meta * (
        eta_osc * (meta.oscillation_magnitude ** 2) +
        eta_unc * (meta.self_uncertainty ** 2) +
        eta_flip * meta.recent_flip_count
    )


# === Budget Barrier (Section 9) ===

def compute_budget_barrier(
    budget: Dict[str, float],
    reserves: Dict[str, float],
    kappa: float = 1.0,
    barrier_type: str = "reciprocal",
) -> float:
    """
    Compute budget barrier Φ_B(b) per appendix §9.
    
    Two forms:
    - reciprocal: Σ κ_i / (b_i - b_i,reserve)
    - log: -Σ κ_i * log((b_i - b_i,reserve) / (B_i^max - b_i,reserve))
    
    Args:
        budget: Current budget values
        reserves: Reserve floors per channel
        kappa: Barrier coefficient
        barrier_type: "reciprocal" or "log"
        
    Returns:
        Budget barrier potential (diverges at reserve)
    """
    potential = 0.0
    
    for channel, b in budget.items():
        reserve = reserves.get(channel, 0.0)
        margin = b - reserve
        
        if margin <= 1e-6:
            # At or below reserve - barrier diverges
            return float('inf')
        
        if barrier_type == "reciprocal":
            potential += kappa / margin
        elif barrier_type == "log":
            max_val = reserves.get(f"{channel}_max", 100.0)
            if margin < max_val:
                potential += -kappa * np.log(margin / max_val)
    
    return potential


# === Anchor Authority Interlock (Section 10) ===

@dataclass
class AuthorityState:
    """Authority and anchor state."""
    auth_mismatch: float = 0.0
    anchor_conflicts: List[float] = field(default_factory=list)
    scope_violations: float = 0.0


def compute_authority_penalty(
    authority: AuthorityState,
    zeta_auth: float = 1.0,
    zeta_anchor: float = 1.0,
    zeta_scope: float = 1.0,
) -> float:
    """
    Compute authority penalty Φ_A(x) per appendix §10.
    
    Φ_A(x) = ζ_1 * AuthMismatch + ζ_2 * AnchorConflict + ζ_3 * ScopeViolation
    
    Args:
        authority: Authority state
        zeta_auth: Auth mismatch weight
        zeta_anchor: Anchor conflict weight
        zeta_scope: Scope violation weight
        
    Returns:
        Authority penalty
    """
    # Anchor conflict term: Σ max(0, δ_A - (A(q_ext) - A(q_int)))
    delta_a = 0.1  # Authority margin from anchors
    anchor_term = sum(
        max(0, delta_a - conflict) 
        for conflict in authority.anchor_conflicts
    )
    
    return (
        zeta_auth * authority.auth_mismatch +
        zeta_anchor * anchor_term +
        zeta_scope * authority.scope_violations
    )


# === Full Tension Law (Section 11) ===

@dataclass
class GMITensionState:
    """
    Complete state for GMI tension law computation.
    
    Bundles all inputs needed for V_GMI(x) evaluation.
    """
    # Core state
    latent_state: np.ndarray = field(default_factory=lambda: np.array([0.0]))
    
    # Observation
    predicted_sensory: np.ndarray = field(default_factory=lambda: np.array([]))
    actual_sensory: np.ndarray = field(default_factory=lambda: np.array([]))
    sensory_confidence: np.ndarray = field(default_factory=lambda: np.array([1.0]))
    
    # Memory
    predicted_memory: np.ndarray = field(default_factory=lambda: np.array([]))
    actual_memory: np.ndarray = field(default_factory=lambda: np.array([]))
    memory_weights: np.ndarray = field(default_factory=lambda: np.array([1.0]))
    fragmentation: MemoryFragmentationMetrics = field(default_factory=MemoryFragmentationMetrics)
    
    # Goals
    goals: List[GoalState] = field(default_factory=list)
    
    # Consistency
    consistency: ConsistencyMetrics = field(default_factory=ConsistencyMetrics)
    
    # Planning
    plan_nodes: List[PlanNode] = field(default_factory=list)
    
    # Actions
    pending_actions: List[PendingAction] = field(default_factory=list)
    
    # Meta-stability
    meta: MetaStabilityMetrics = field(default_factory=MetaStabilityMetrics)
    
    # Budget
    budget: Dict[str, float] = field(default_factory=dict)
    reserves: Dict[str, float] = field(default_factory=dict)
    
    # Authority
    authority: AuthorityState = field(default_factory=AuthorityState)
    
    # Weights
    weights: TensionWeights = field(default_factory=TensionWeights)


class GMITensionLaw:
    """
    Complete GMI tension law per appendix §11.
    
    V_GMI(x) = Σ_α w_α |r^α(x)|² + Φ_B(b) + Φ_A(x)
    """
    
    def __init__(
        self,
        weights: Optional[TensionWeights] = None,
        barrier_type: str = "reciprocal",
    ):
        """
        Initialize tension law.
        
        Args:
            weights: Tension weight coefficients
            barrier_type: Budget barrier type
        """
        self.weights = weights or TensionWeights()
        self.barrier_type = barrier_type
    
    def compute_residuals(self, state: GMITensionState) -> ResidualVector:
        """
        Compute all residual components.
        
        Args:
            state: Tension state
            
        Returns:
            Residual vector
        """
        residuals = ResidualVector()
        
        # Observation residual
        if len(state.predicted_sensory) > 0 and len(state.actual_sensory) > 0:
            residuals.obs = compute_observation_residual(
                state.predicted_sensory,
                state.actual_sensory,
                state.sensory_confidence,
            )
        
        # Memory residual
        if len(state.predicted_memory) > 0 and len(state.actual_memory) > 0:
            residuals.mem = compute_memory_residual(
                state.predicted_memory,
                state.actual_memory,
                state.memory_weights,
            )
        
        # Goal residual
        if state.goals:
            residuals.goal, _ = compute_goal_residual(state.goals)
        
        # Consistency - already a scalar in metrics
        # Planning - already a scalar in metrics
        # Action - already a scalar in metrics
        # Meta - already a scalar in metrics
        
        return residuals
    
    def compute(self, state: GMITensionState) -> float:
        """
        Compute full tension V_GMI(x).
        
        Per appendix §11:
        
        V_GMI(x) = V_obs + V_mem + V_goal + V_cons + V_plan + V_act + V_meta + Φ_B + Φ_A
        
        Args:
            state: Tension state
            
        Returns:
            Total potential energy
        """
        V = 0.0
        
        # V_obs
        if len(state.predicted_sensory) > 0:
            V += compute_observation_potential(
                state.predicted_sensory,
                state.actual_sensory,
                state.sensory_confidence,
                self.weights.w_obs,
            )
        
        # V_mem
        if len(state.predicted_memory) > 0:
            V += compute_memory_potential(
                state.predicted_memory,
                state.actual_memory,
                state.memory_weights,
                self.weights.w_mem,
                state.fragmentation,
                self.weights.w_mem * 0.1,  # frag weight
            )
        
        # V_goal
        if state.goals:
            _, goal_pot = compute_goal_residual(state.goals)
            V += self.weights.w_goal * goal_pot
        
        # V_cons
        V += compute_consistency_potential(
            state.consistency,
            self.weights.w_cons,
        )
        
        # V_plan
        V += compute_planning_potential(
            state.plan_nodes,
            self.weights.w_plan,
        )
        
        # V_act
        V += compute_action_potential(
            state.pending_actions,
            self.weights.w_act,
        )
        
        # V_meta
        V += compute_meta_potential(
            state.meta,
            self.weights.w_meta,
        )
        
        # Φ_B (budget barrier)
        V += compute_budget_barrier(
            state.budget,
            state.reserves,
            self.weights.kappa_budget,
            self.barrier_type,
        )
        
        # Φ_A (authority penalty)
        V += compute_authority_penalty(
            state.authority,
            self.weights.zeta_auth,
            self.weights.zeta_anchor,
            self.weights.zeta_scope,
        )
        
        return V
    
    def compute_component_breakdown(self, state: GMITensionState) -> Dict[str, float]:
        """
        Compute individual component contributions.
        
        Useful for diagnostics.
        
        Args:
            state: Tension state
            
        Returns:
            Dictionary of component potentials
        """
        components = {}
        
        # Observation
        if len(state.predicted_sensory) > 0:
            components['obs'] = compute_observation_potential(
                state.predicted_sensory, state.actual_sensory,
                state.sensory_confidence, self.weights.w_obs,
            )
        
        # Memory
        if len(state.predicted_memory) > 0:
            components['mem'] = compute_memory_potential(
                state.predicted_memory, state.actual_memory,
                state.memory_weights, self.weights.w_mem,
                state.fragmentation, self.weights.w_mem * 0.1,
            )
        
        # Goal
        if state.goals:
            _, goal_pot = compute_goal_residual(state.goals)
            components['goal'] = self.weights.w_goal * goal_pot
        
        # Consistency
        components['cons'] = compute_consistency_potential(
            state.consistency, self.weights.w_cons,
        )
        
        # Planning
        components['plan'] = compute_planning_potential(
            state.plan_nodes, self.weights.w_plan,
        )
        
        # Action
        components['act'] = compute_action_potential(
            state.pending_actions, self.weights.w_act,
        )
        
        # Meta
        components['meta'] = compute_meta_potential(
            state.meta, self.weights.w_meta,
        )
        
        # Budget barrier
        components['budget_barrier'] = compute_budget_barrier(
            state.budget, state.reserves,
            self.weights.kappa_budget, self.barrier_type,
        )
        
        # Authority
        components['authority'] = compute_authority_penalty(
            state.authority,
            self.weights.zeta_auth,
            self.weights.zeta_anchor,
            self.weights.zeta_scope,
        )
        
        # Total
        components['total'] = sum(components.values())
        
        return components


# === Step Scoring (Section 12) ===

@dataclass
class CandidateStep:
    """A candidate local step."""
    step_id: str
    proposed_state: GMITensionState
    predicted_spend: float
    predicted_descent: float = 0.0
    efficiency: float = 0.0
    hard_constraints_ok: bool = True
    contradiction_risk: float = 0.0
    authority_risk: float = 0.0


def compute_step_efficiency(
    current_V: float,
    candidate: CandidateStep,
    epsilon: float = 1e-6,
) -> float:
    """
    Compute efficiency score η(u) = Δ⁻V / (Σ(u) + ε)
    
    Per appendix §12
    
    Args:
        current_V: Current potential
        candidate: Candidate step
        epsilon: Small constant for numerical stability
        
    Returns:
        Efficiency score
    """
    predicted_descent = max(0.0, current_V - candidate.predicted_descent)
    return predicted_descent / (candidate.predicted_spend + epsilon)


def score_and_rank_candidates(
    current_V: float,
    candidates: List[CandidateStep],
    epsilon: float = 1e-6,
    efficiency_threshold: float = 0.0,
    contradiction_threshold: float = float('inf'),
    authority_threshold: float = float('inf'),
) -> List[CandidateStep]:
    """
    Score and rank candidate steps.
    
    Per appendix §12:
    1. Reject candidates violating hard constraints
    2. Among survivors, minimize contradiction burden
    3. Among survivors, maximize efficiency
    
    Args:
        current_V: Current potential
        candidates: List of candidates
        epsilon: Numerical stability constant
        efficiency_threshold: Minimum efficiency to keep
        contradiction_threshold: Max contradiction risk
        authority_threshold: Max authority risk
        
    Returns:
        Ranked list of candidates
    """
    scored = []
    
    for c in candidates:
        # Check hard constraints
        if not c.hard_constraints_ok:
            continue
        
        # Check risk thresholds
        if c.contradiction_risk > contradiction_threshold:
            continue
        if c.authority_risk > authority_threshold:
            continue
        
        # Compute efficiency
        c.efficiency = compute_step_efficiency(current_V, c, epsilon)
        
        # Filter by efficiency threshold
        if c.efficiency >= efficiency_threshold:
            scored.append(c)
    
    # Sort by efficiency (descending)
    scored.sort(key=lambda c: c.efficiency, reverse=True)
    
    return scored


# === Branching Law (Section 13) ===

@dataclass
class Branch:
    """A planning branch."""
    branch_id: str
    hypothetical_state: GMITensionState
    cost: float
    predicted_V: float = 0.0
    descent: float = 0.0
    score: float = 0.0


def compute_branch_score(
    current_V: float,
    branch: Branch,
    epsilon: float = 1e-6,
) -> float:
    """
    Compute branch score η_j = max(Δ_j, 0) / (c_j + ε)
    
    Per appendix §13
    
    Args:
        current_V: Current potential
        branch: Branch to score
        epsilon: Numerical stability
        
    Returns:
        Branch score
    """
    descent = current_V - branch.predicted_V
    return max(0.0, descent) / (branch.cost + epsilon)


def filter_branches(
    branches: List[Branch],
    current_V: float,
    max_branches: int = 5,
    score_threshold: float = 0.0,
    consistency_threshold: float = float('inf'),
    authority_threshold: float = float('inf'),
    epsilon: float = 1e-6,
) -> List[Branch]:
    """
    Filter and rank branches.
    
    Per appendix §13:
    - Score each branch
    - Keep branches meeting thresholds
    - Return top J <= J_max
    
    Args:
        branches: List of branches
        current_V: Current potential
        max_branches: Maximum branches to keep
        score_threshold: Minimum score to survive
        consistency_threshold: Max consistency risk
        authority_threshold: Max authority risk
        epsilon: Numerical stability
        
    Returns:
        Filtered and ranked branches
    """
    scored = []
    
    for b in branches:
        b.score = compute_branch_score(current_V, b, epsilon)
        
        # Filter by score
        if b.score < score_threshold:
            continue
        
        # Note: In practice would check consistency/authority risks from state
        scored.append(b)
    
    # Sort by score descending
    scored.sort(key=lambda b: b.score, reverse=True)
    
    return scored[:max_branches]


# === Repair Mode (Section 14) ===

class RepairModeTensionLaw:
    """
    Specialized tension law for repair mode.
    
    V_repair(x) = V_cons(x) + V_mem(x) + Φ_A(x)
    
    Stricter than normal planning: monotone descent required.
    """
    
    def __init__(self, base_law: GMITensionLaw):
        """
        Initialize repair mode.
        
        Args:
            base_law: Base tension law
        """
        self.base_law = base_law
    
    def compute(self, state: GMITensionState) -> float:
        """
        Compute repair potential.
        
        Args:
            state: Tension state
            
        Returns:
            Repair potential
        """
        V = 0.0
        
        # V_cons (consistency)
        V += compute_consistency_potential(
            state.consistency,
            self.base_law.weights.w_cons,
        )
        
        # V_mem (memory)
        if len(state.predicted_memory) > 0:
            V += compute_memory_potential(
                state.predicted_memory,
                state.actual_memory,
                state.memory_weights,
                self.base_law.weights.w_mem,
                state.fragmentation,
                self.base_law.weights.w_mem * 0.1,
            )
        
        # Φ_A (authority penalty)
        V += compute_authority_penalty(
            state.authority,
            self.base_law.weights.zeta_auth,
            self.base_law.weights.zeta_anchor,
            self.base_law.weights.zeta_scope,
        )
        
        return V


# === Factory Functions ===

def create_tension_law(
    weights: Optional[Dict[str, float]] = None,
    barrier_type: str = "reciprocal",
) -> GMITensionLaw:
    """
    Create tension law with optional custom weights.
    
    Args:
        weights: Optional weight dictionary
        barrier_type: Budget barrier type
        
    Returns:
        Configured GMITensionLaw
    """
    if weights:
        tw = TensionWeights(**weights)
    else:
        tw = TensionWeights()
    
    return GMITensionLaw(weights=tw, barrier_type=barrier_type)


def create_repair_law(tension_law: GMITensionLaw) -> RepairModeTensionLaw:
    """
    Create repair mode tension law.
    
    Args:
        tension_law: Base tension law
        
    Returns:
        RepairModeTensionLaw
    """
    return RepairModeTensionLaw(tension_law)
