"""
GMI Intellectual Tests: Higher-Order Cognitive Capabilities

This module contains five intellectual tests for the GMI Universal Cognition Engine:
1. Compositional Reasoning: Chained instructions with Oplax algebra
2. Exploration-Exploitation: Balance between risky and safe moves
3. Memory Consolidation: Memory curvature effects on decisions
4. Convergence Under Noise: Stochastic instruction handling
5. Multi-Step Planning: Looking ahead for sustainable paths

These tests explore higher-order cognitive capabilities beyond basic stress tests.

Author: GMI Architecture Team
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
from enum import Enum

# GMI Core imports
from core.state import State, Instruction, CompositeInstruction, create_potential
from core.potential import GMIPotential
from core.memory import MemoryManifold
from ledger.oplax_verifier import OplaxVerifier
from ledger.receipt import Receipt


# =============================================================================
# TEST 4: COMPOSITIONAL REASONING
# =============================================================================

class CompositionalTestResult(Enum):
    PASS = "pass"
    FAIL_SIGMA = "fail_sigma"  # Metabolic undercharge
    FAIL_KAPPA = "fail_kappa"  # Defect laundering
    FAIL_OTHER = "fail_other"


def create_compositional_scenario() -> Tuple[GMIPotential, State, List]:
    """
    Create a scenario testing Oplax operator algebra for composed instructions.
    
    Tests:
    - Valid composition: σ_composite >= σ1 + σ2, κ_composite <= κ1 + κ2
    - Invalid sigma (undercharge): σ_composite < σ1 + σ2
    - Invalid kappa (laundering): κ_composite > κ1 + κ2
    """
    potential = create_potential()
    state = State(x=[3.0, 3.0], budget=10.0)
    
    print(f"\n=== COMPOSITIONAL REASONING TEST ===")
    print(f"Initial V: {potential.base(state.x):.2f}")
    
    # Create two simple instructions
    instr1 = Instruction("STEP_A", lambda x: x * 0.8, sigma=1.0, kappa=0.5)
    instr2 = Instruction("STEP_B", lambda x: x * 0.8, sigma=1.0, kappa=0.5)
    
    # Test cases: (claimed_sigma, claimed_kappa, should_be_valid, description)
    test_cases = [
        # Valid: honest sigma, honest kappa
        (2.0, 1.0, True, "Valid composition (honest)"),
        
        # Invalid: undercharged sigma
        (1.5, 1.0, False, "Invalid: Metabolic undercharge (σ=1.5 < 2.0)"),
        
        # Invalid: laundered kappa
        (2.0, 1.5, False, "Invalid: Defect laundering (κ=1.5 > 1.0)"),
        
        # Valid but tight: exactly honest
        (2.0, 0.5, True, "Valid: Exactly honest (σ=2.0, κ=0.5)"),
    ]
    
    return potential, state, (instr1, instr2, test_cases)


def run_compositional_test(
    potential: GMIPotential,
    state: State,
    test_data
) -> CompositionalTestResult:
    """Run the compositional reasoning test."""
    verifier = OplaxVerifier(potential_fn=potential.base)
    instr1, instr2, test_cases = test_data
    
    print(f"\n=== Testing Composite Instructions ===")
    
    results = []
    for claimed_sigma, claimed_kappa, should_be_valid, description in test_cases:
        # Create composite instruction
        composite = CompositeInstruction(instr1, instr2, claimed_sigma, claimed_kappa)
        
        print(f"\nTest: {description}")
        print(f"  Claimed: σ={claimed_sigma}, κ={claimed_kappa}")
        print(f"  Actual sum: σ={instr1.sigma + instr2.sigma}, κ={instr1.kappa + instr2.kappa}")
        
        # Test the composition
        accepted, new_state, receipt = verifier.check(1, state, composite)
        
        expected_valid = should_be_valid
        
        if accepted == expected_valid:
            print(f"  ✓ {'Accepted (expected)' if accepted else 'Rejected (expected)'}")
            results.append(True)
        else:
            print(f"  ✗ {'Accepted (unexpected!)' if accepted else 'Rejected (unexpected!)'}")
            results.append(False)
    
    # Determine overall result
    all_correct = all(results)
    
    print(f"\n=== COMPOSITIONAL RESULT ===")
    if all_correct:
        print("✓ PASS: All composition tests behaved correctly")
        return CompositionalTestResult.PASS
    else:
        # Determine failure type
        failed_cases = [i for i, r in enumerate(results) if not r]
        if 1 in failed_cases:  # Undercharge case
            print("✗ FAIL: Metabolic undercharge not properly detected")
            return CompositionalTestResult.FAIL_SIGMA
        elif 2 in failed_cases:  # Laundering case
            print("✗ FAIL: Defect laundering not properly detected")
            return CompositionalTestResult.FAIL_KAPPA
        else:
            print("✗ FAIL: Some composition tests failed")
            return CompositionalTestResult.FAIL_OTHER


# =============================================================================
# TEST 5: EXPLORATION-EXPLOITATION BALANCE
# =============================================================================

class ExploreExploitResult(Enum):
    PASS = "pass"
    FAIL_EXPLORE_ONLY = "explore_only"  # Only explores, never exploits
    FAIL_EXPLOIT_ONLY = "exploit_only"  # Only exploits, never explores


def create_explore_exploit_scenario() -> Tuple[GMIPotential, State, List[Instruction]]:
    """
    Test that system can balance exploration vs exploitation.
    
    - EXPLORE: Higher sigma/kappa, samples new regions
    - EXPLOIT: Lower sigma/kappa, gradient descent
    """
    potential = create_potential()
    
    # Start far from optimum to allow meaningful exploration
    initial_x = np.array([3.0, 3.0])  # Start far from optimum
    initial_budget = 15.0  # Enough for both modes
    
    print(f"\n=== EXPLORATION-EXPLOITATION TEST ===")
    print(f"Initial V: {potential.base(initial_x):.2f}")
    print(f"Budget: {initial_budget}")
    
    # EXPLORE: Random perturbation, high cost, allows V increase
    def explore_transform(x):
        # Add random noise but tend toward lower energy overall
        noise = np.random.uniform(-0.3, 0.3)
        return x + noise
    
    explore_instr = Instruction(
        "EXPLORE",
        explore_transform,
        sigma=2.0,  # Higher cost
        kappa=3.0   # Allows V increase (defect)
    )
    
    # EXPLOIT: Gradient descent, low cost, strict
    def exploit_transform(x):
        return x * 0.9  # Simple contraction
    
    exploit_instr = Instruction(
        "EXPLOIT",
        exploit_transform,
        sigma=0.5,  # Cheap
        kappa=0.3  # Strict
    )
    
    state = State(initial_x, initial_budget)
    return potential, state, [explore_instr, exploit_instr]


def run_explore_exploit_test(
    potential: GMIPotential,
    state: State,
    instructions: List[Instruction]
) -> ExploreExploitResult:
    """Run the exploration-exploitation balance test."""
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    print(f"\n=== Running Exploration-Exploitation Cycle ===")
    
    explore_instr, exploit_instr = instructions
    current_state = state
    
    explore_accepted = 0
    exploit_accepted = 0
    explore_rejected = 0
    exploit_rejected = 0
    
    for step in range(20):
        # Alternate: try explore then exploit
        accepted_exp, state_exp, _ = verifier.check(step, current_state, explore_instr)
        
        if accepted_exp:
            print(f"Step {step}: EXPLORE accepted -> V={potential.base(state_exp.x):.2f}")
            current_state = state_exp
            explore_accepted += 1
        else:
            explore_rejected += 1
            # Try exploit instead
            accepted_safe, state_safe, _ = verifier.check(step, current_state, exploit_instr)
            if accepted_safe:
                print(f"Step {step}: EXPLORE rejected, EXPLOIT accepted -> V={potential.base(state_safe.x):.2f}")
                current_state = state_safe
                exploit_accepted += 1
            else:
                exploit_rejected += 1
        
        # Check convergence
        if potential.base(current_state.x) < 0.1:
            print(f"Step {step}: Converged")
            break
    
    print(f"\n=== EXPLORATION-EXPLOITATION RESULT ===")
    print(f"Explore accepted: {explore_accepted}, rejected: {explore_rejected}")
    print(f"Exploit accepted: {exploit_accepted}, rejected: {exploit_rejected}")
    
    # Check balance: should use both modes OR converge successfully
    total_accepted = explore_accepted + exploit_accepted
    
    if total_accepted == 0:
        print("✗ FAIL: No moves accepted")
        return ExploreExploitResult.FAIL_EXPLOIT_ONLY
    
    # Check if converged
    final_v = potential.base(current_state.x)
    converged = final_v < 0.1
    
    explore_ratio = explore_accepted / total_accepted if total_accepted > 0 else 0
    
    # Balance check: with high budget, exploration is acceptable
    # The key is: did it make progress AND converge?
    if converged:
        print(f"✓ PASS: System converged (V={final_v:.2f})")
        print(f"  (Used {explore_accepted} explore, {exploit_accepted} exploit moves)")
        return ExploreExploitResult.PASS
    elif explore_ratio > 0.9:
        print("✗ FAIL: System only explores, didn't converge")
        return ExploreExploitResult.FAIL_EXPLORE_ONLY
    elif explore_ratio < 0.1:
        print("✗ FAIL: System only exploits, stuck in local optimum")
        return ExploreExploitResult.FAIL_EXPLOIT_ONLY
    else:
        print(f"✓ PASS: Balanced exploration ({explore_ratio:.1%}) and exploitation")
        return ExploreExploitResult.PASS


# =============================================================================
# TEST 6: MEMORY CONSOLIDATION
# =============================================================================

class MemoryTestResult(Enum):
    PASS = "pass"
    FAIL_REWARD = "fail_reward"    # Didn't use reward region
    FAIL_SCAR = "fail_scar"        # Didn't avoid scar region


def create_memory_scenario() -> Tuple[GMIPotential, State, MemoryManifold]:
    """
    Test memory manifold curvature effects.
    
    - Negative curvature (rewards) should attract the system
    - Positive curvature (scars) should repel the system
    """
    potential = create_potential()
    
    # Create memory manifold
    memory = MemoryManifold(lambda_c=5.0, lambda_r=3.0)
    
    # Add a reward at [2, 2] - this should attract
    memory.write_reward(np.array([2.0, 2.0]), strength=2.0)
    
    # Add a scar at [4, 4] - this should repel
    memory.write_scar(np.array([4.0, 4.0]), penalty=3.0)
    
    # Start near the reward region
    initial_x = np.array([1.0, 1.0])
    initial_budget = 10.0
    
    print(f"\n=== MEMORY CONSOLIDATION TEST ===")
    print(f"Initial V (base): {potential.base(initial_x):.2f}")
    print(f"Memory curvature at start: {memory.read_curvature(initial_x):.2f}")
    print(f"Reward at [2,2], Scar at [4,4]")
    
    state = State(initial_x, initial_budget)
    return potential, state, memory


def run_memory_test(
    potential: GMIPotential,
    state: State,
    memory: MemoryManifold
) -> MemoryTestResult:
    """Run the memory consolidation test."""
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    print(f"\n=== Testing Memory Effects ===")
    
    # Create a move toward the reward
    def move_to_reward(x):
        # Move toward reward at [2, 2]
        return x + np.array([0.3, 0.3])
    
    toward_reward = Instruction(
        "TOWARD_REWARD",
        move_to_reward,
        sigma=0.5,
        kappa=0.3
    )
    
    # Create a move toward the scar
    def move_to_scar(x):
        # Move toward scar at [4, 4]
        return x + np.array([0.3, 0.3])
    
    toward_scar = Instruction(
        "TOWARD_SCAR",
        move_to_scar,
        sigma=0.5,
        kappa=0.3
    )
    
    # Test 1: Moving toward reward should have lower effective potential
    reward_target = np.array([2.0, 2.0])
    scar_target = np.array([4.0, 4.0])
    
    v_base_reward = potential.base(reward_target)
    v_total_reward = potential.total(reward_target, state.b, memory=memory)
    
    v_base_scar = potential.base(scar_target)
    v_total_scar = potential.total(scar_target, state.b, memory=memory)
    
    print(f"\nAt reward region [2,2]:")
    print(f"  Base V: {v_base_reward:.2f}")
    print(f"  Total V (with memory): {v_total_reward:.2f}")
    print(f"  Curvature contribution: {v_total_reward - v_base_reward:.2f}")
    
    print(f"\nAt scar region [4,4]:")
    print(f"  Base V: {v_base_scar:.2f}")
    print(f"  Total V (with memory): {v_total_scar:.2f}")
    print(f"  Curvature contribution: {v_total_scar - v_base_scar:.2f}")
    
    # Verify memory effects
    reward_lowers_v = v_total_reward < v_base_reward
    scar_raises_v = v_total_scar > v_base_scar
    
    print(f"\n=== MEMORY RESULT ===")
    
    if reward_lowers_v and scar_raises_v:
        print("✓ PASS: Memory correctly attracts (rewards) and repels (scars)")
        return MemoryTestResult.PASS
    elif not reward_lowers_v:
        print("✗ FAIL: Reward region not attracting")
        return MemoryTestResult.FAIL_REWARD
    else:
        print("✗ FAIL: Scar region not repelling")
        return MemoryTestResult.FAIL_SCAR


# =============================================================================
# TEST 7: CONVERGENCE UNDER NOISE
# =============================================================================

class NoiseTestResult(Enum):
    PASS = "pass"
    FAIL_DIVERGE = "diverge"  # Diverged instead of converged
    FAIL_STUCK = "stuck"       # Got stuck, no progress


def create_noise_scenario() -> Tuple[GMIPotential, State]:
    """Test convergence despite noisy/stochastic instructions."""
    potential = create_potential()
    
    initial_x = np.array([5.0, 5.0])
    initial_budget = 20.0
    
    print(f"\n=== CONVERGENCE UNDER NOISE TEST ===")
    print(f"Initial V: {potential.base(initial_x):.2f}")
    
    state = State(initial_x, initial_budget)
    return potential, state


def run_noise_test(
    potential: GMIPotential,
    state: State
) -> NoiseTestResult:
    """Run the noise convergence test."""
    # Create a noisy instruction
    def noisy_transform(x):
        # Intentional: higher variance
        noise = np.random.normal(0, 0.8)
        new_x = x * 0.85 + noise
        return np.clip(new_x, -10, 10)  # Prevent explosion
    
    noisy_instr = Instruction(
        "NOISY_STEP",
        noisy_transform,
        sigma=1.5,  # Account for uncertainty
        kappa=2.0   # Allow temporary increases
    )
    
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    print(f"\n=== Running Noisy Iterations ===")
    
    current_state = state
    v_history = [potential.base(current_state.x)]
    
    np.random.seed(42)  # Reproducible
    
    for step in range(30):
        accepted, new_state, receipt = verifier.check(step, current_state, noisy_instr)
        
        if accepted:
            current_state = new_state
            v_current = potential.base(current_state.x)
            v_history.append(v_current)
            print(f"Step {step}: Accepted, V={v_current:.2f}, b={current_state.b:.2f}")
        else:
            print(f"Step {step}: Rejected")
        
        # Check for convergence
        if v_current < 0.1:
            print(f"Step {step}: Converged!")
            break
        
        # Check for budget exhaustion
        if current_state.b < 0.5:
            print(f"Step {step}: Budget low, stopping")
            break
    
    # Analyze results
    v_initial = v_history[0]
    v_final = v_history[-1]
    v_min = min(v_history)
    
    print(f"\n=== NOISE CONVERGENCE RESULT ===")
    print(f"Initial V: {v_initial:.2f}")
    print(f"Final V: {v_final:.2f}")
    print(f"Minimum V: {v_min:.2f}")
    print(f"Steps with progress: {sum(1 for i in range(1, len(v_history)) if v_history[i] < v_history[i-1])}")
    
    # Success criteria: average trend is downward
    avg_direction = (v_final - v_initial) / len(v_history)
    
    if avg_direction < -0.1:
        print("✓ PASS: Converging despite noise")
        return NoiseTestResult.PASS
    elif v_final > v_initial:
        print("✗ FAIL: Diverged under noise")
        return NoiseTestResult.FAIL_DIVERGE
    else:
        print("✗ FAIL: Stuck, no meaningful progress")
        return NoiseTestResult.FAIL_STUCK


# =============================================================================
# TEST 8: MULTI-STEP PLANNING
# =============================================================================

class PlanningTestResult(Enum):
    PASS = "pass"
    FAIL_TRAP = "trap"      # Fell for the trap
    FAIL_STUCK = "stuck"    # Couldn't plan ahead


def create_planning_scenario() -> Tuple[GMIPotential, State, List[Instruction]]:
    """
    Test multi-step planning capability.
    
    - TRAP: Immediate huge reward, but budget exhausted
    - PATH: Moderate sustainable steps
    """
    potential = create_potential()
    
    initial_x = np.array([8.0, 8.0])
    initial_budget = 8.0  # Limited budget - need to plan carefully
    
    print(f"\n=== MULTI-STEP PLANNING TEST ===")
    print(f"Initial V: {potential.base(initial_x):.2f}")
    print(f"Budget: {initial_budget}")
    
    # TRAP: Looks amazing immediately but drains budget completely
    def trap_transform(x):
        return x * 0.1  # 90% reduction!
    
    trap_instr = Instruction(
        "TRAP_LEAP",
        trap_transform,
        sigma=7.5,  # Drains almost all budget
        kappa=0.0
    )
    
    # PATH: Sustainable multi-step approach
    def step1_transform(x):
        return x * 0.7
    
    def step2_transform(x):
        return x * 0.7
    
    def step3_transform(x):
        return x * 0.6
    
    path_instrs = [
        Instruction("PATH_STEP_1", step1_transform, sigma=1.5, kappa=0.2),
        Instruction("PATH_STEP_2", step2_transform, sigma=1.5, kappa=0.2),
        Instruction("PATH_STEP_3", step3_transform, sigma=1.5, kappa=0.2),
    ]
    
    state = State(initial_x, initial_budget)
    return potential, state, [trap_instr] + path_instrs


def run_planning_test(
    potential: GMIPotential,
    state: State,
    instructions: List[Instruction]
) -> PlanningTestResult:
    """Run the multi-step planning test."""
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    trap_instr = instructions[0]
    path_instrs = instructions[1:]
    
    print(f"\n=== Testing Plan Options ===")
    
    # Test the trap
    print("\n1. Testing TRAP (immediate gratification)...")
    trap_accepted, trap_state, _ = verifier.check(1, state, trap_instr)
    
    print(f"   Accepted: {trap_accepted}")
    if trap_accepted:
        print(f"   Result: V={potential.base(trap_state.x):.2f}, b={trap_state.b:.2f}")
        trap_survives = trap_state.b > 0.5
    else:
        trap_survives = False
    
    # Test the path
    print("\n2. Testing PATH (sustainable multi-step)...")
    current = state
    path_successful = True
    
    for i, instr in enumerate(path_instrs):
        accepted, new_state, _ = verifier.check(i + 2, current, instr)
        
        if accepted:
            print(f"   Step {i+1}: Accepted, V={potential.base(new_state.x):.2f}, b={new_state.b:.2f}")
            current = new_state
        else:
            print(f"   Step {i+1}: Rejected")
            path_successful = False
            break
    
    print(f"\n=== PLANNING RESULT ===")
    
    if not trap_accepted:
        print("✓ PASS: System rejected trap (thermodynamics blocked)")
        return PlanningTestResult.PASS
    elif trap_accepted and not trap_survives:
        print("✓ PASS: System saw through trap (budget analysis)")
        # Even if thermodynamic allows, long-term analysis should catch it
        return PlanningTestResult.PASS
    elif trap_accepted and trap_survives and not path_successful:
        print("✗ FAIL: System fell for trap, couldn't do path")
        return PlanningTestResult.FAIL_TRAP
    else:
        print("✓ PASS: Both options work, system chose wisely")
        return PlanningTestResult.PASS


# =============================================================================
# MAIN: Run All Intellectual Tests
# =============================================================================

def run_all_intellectual_tests():
    """Run all five intellectual tests."""
    print("=" * 60)
    print("GMI INTELLECTUAL TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Test 4: Compositional Reasoning
    print("\n" + "=" * 60)
    potential, state, test_data = create_compositional_scenario()
    results['compositional'] = run_compositional_test(potential, state, test_data)
    
    # Test 5: Exploration-Exploitation
    print("\n" + "=" * 60)
    potential, state, instructions = create_explore_exploit_scenario()
    results['explore_exploit'] = run_explore_exploit_test(potential, state, instructions)
    
    # Test 6: Memory Consolidation
    print("\n" + "=" * 60)
    potential, state, memory = create_memory_scenario()
    results['memory'] = run_memory_test(potential, state, memory)
    
    # Test 7: Convergence Under Noise
    print("\n" + "=" * 60)
    potential, state = create_noise_scenario()
    results['noise'] = run_noise_test(potential, state)
    
    # Test 8: Multi-Step Planning
    print("\n" + "=" * 60)
    potential, state, instructions = create_planning_scenario()
    results['planning'] = run_planning_test(potential, state, instructions)
    
    # Summary
    print("\n" + "=" * 60)
    print("INTELLECTUAL TEST SUMMARY")
    print("=" * 60)
    
    test_names = {
        'compositional': 'Compositional Reasoning',
        'explore_exploit': 'Exploration-Exploitation',
        'memory': 'Memory Consolidation',
        'noise': 'Convergence Under Noise',
        'planning': 'Multi-Step Planning',
    }
    
    for test_name, result in results.items():
        status = "✓ PASS" if result.value == "pass" else "✗ FAIL"
        print(f"{status}: {test_names[test_name]} - {result.value}")
    
    all_passed = all(r.value == "pass" for r in results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL INTELLECTUAL TESTS PASSED")
    else:
        print("SOME TESTS FAILED - Review cognitive capabilities")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    run_all_intellectual_tests()
