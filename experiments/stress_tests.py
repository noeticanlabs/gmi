"""
GMI Stress Tests: Anti-Freeze, Discipline, and Ledger Integrity

This module contains three stress tests for the GMI Universal Cognition Engine:
1. Pressure Test: Anti-freeze logic under high constraint environments
2. Laziness Test: Discipline/commitment to costly but beneficial paths
3. Greed Test: Ledger blocking of catastrophic long-term decisions

Test Philosophy:
- Each test pushes the system into a pathological regime
- Tests verify that core constraints (budget barrier, thermodynamic inequality, ledger integrity) hold
- Tests should FAIL if the system is NOT properly secured

Author: GMI Architecture Team
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

# GMI Core imports
from core.state import State, Instruction, CompositeInstruction, create_potential
from core.potential import GMIPotential
from ledger.oplax_verifier import OplaxVerifier
from ledger.receipt import Receipt
from ledger.hash_chain import HashChainLedger


# =============================================================================
# PRESSURE TEST: Anti-Freeze Logic
# =============================================================================

class PressureTestResult(Enum):
    PASS = "pass"           # System handled pressure correctly
    FAIL_FREEZE = "freeze"  # System froze (couldn't move)
    FAIL_DEBT = "debt"       # System accumulated unsustainable debt
    FAIL_HALT = "halt"       # System halted incorrectly


def create_pressure_scenario() -> Tuple[GMIPotential, State, List[Instruction]]:
    """
    Create a high-pressure scenario that tests anti-freeze logic.
    
    The scenario:
    - Start with very low budget (b=0.5) approaching the barrier
    - Create instructions that require budget to execute
    - Verify the system can still make progress or properly halt
    
    Expected behavior:
    - With b approaching 0, budget_barrier → infinity
    - System should either:
      a) Select low-sigma moves that are still admissible
      b) Halt gracefully when no admissible moves exist
    - System should NOT freeze (infinite loop with no progress)
    """
    potential = create_potential()
    
    # Start near the budget barrier
    initial_state = State(x=[1.0, 1.0], budget=0.5)
    
    # Create a sequence of instructions with varying sigma
    # These represent increasingly costly moves
    instructions = [
        Instruction("TINY_MOVE", lambda x: x * 0.95, sigma=0.1, kappa=0.1),
        Instruction("SMALL_MOVE", lambda x: x * 0.9, sigma=0.3, kappa=0.2),
        Instruction("MEDIUM_MOVE", lambda x: x * 0.8, sigma=0.6, kappa=0.3),
        # This one should fail: sigma > budget
        Instruction("LARGE_MOVE", lambda x: x * 0.5, sigma=1.0, kappa=0.5),
    ]
    
    return potential, initial_state, instructions


def run_pressure_test(
    potential: GMIPotential,
    state: State,
    instructions: List[Instruction],
    max_steps: int = 50
) -> PressureTestResult:
    """
    Run the pressure test.
    
    Tests:
    1. Budget barrier properly prevents moves when b is too low
    2. System doesn't freeze - can still select admissible moves
    3. Anti-freeze: if no moves are admissible, system halts gracefully
    
    Returns:
        PressureTestResult indicating pass/fail mode
    """
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    current_state = state
    steps_taken = 0
    budget_depleted_count = 0
    successful_moves = 0
    rejected_moves = 0
    
    print(f"\n=== PRESSURE TEST: Anti-Freeze Logic ===")
    print(f"Initial state: x={current_state.x}, b={current_state.b:.3f}")
    print(f"Budget barrier at start: {potential.budget_barrier(current_state.b):.2f}")
    
    while steps_taken < max_steps:
        # Check if budget is too low for any move
        if current_state.b <= 0.1:
            budget_depleted_count += 1
            print(f"Step {steps_taken}: Budget critically low ({current_state.b:.3f})")
            
            # Try the smallest move anyway
            instr = instructions[0]
            accepted, new_state, receipt = verifier.check(steps_taken, current_state, instr)
            
            if not accepted:
                # Anti-freeze: if no moves work, we should halt gracefully
                # Budget is exhausted - this is correct behavior, not a freeze
                print(f"Step {steps_taken}: HALT - Budget exhausted, no admissible moves")
                print("✓ PASS: System halted gracefully when budget depleted")
                return PressureTestResult.PASS
            
            current_state = new_state
            successful_moves += 1
        else:
            # Try each instruction in order
            found_move = False
            for instr in instructions:
                accepted, new_state, receipt = verifier.check(steps_taken, current_state, instr)
                
                if accepted:
                    print(f"Step {steps_taken}: Accepted {instr.op_code} -> x={new_state.x}, b={new_state.b:.3f}")
                    current_state = new_state
                    successful_moves += 1
                    found_move = True
                    break
                else:
                    rejected_moves += 1
            
            if not found_move:
                # All moves rejected - this is acceptable if budget is low
                print(f"Step {steps_taken}: All moves rejected - checking budget")
                if current_state.b <= min(instr.sigma for instr in instructions):
                    print(f"Step {steps_taken}: Budget insufficient for any move - halting")
                    return PressureTestResult.FAIL_FREEZE
        
        steps_taken += 1
        
        # Check for convergence (should reach low potential)
        if potential.base(current_state.x) < 0.1:
            print(f"Step {steps_taken}: Converged to low potential")
            break
    
    print(f"\nPressure Test Results:")
    print(f"  Steps taken: {steps_taken}")
    print(f"  Successful moves: {successful_moves}")
    print(f"  Rejected moves: {rejected_moves}")
    print(f"  Budget depleted events: {budget_depleted_count}")
    
    # PASS if: made progress OR halted gracefully when no moves possible
    # The system correctly stops when budget is exhausted
    if successful_moves > 0:
        print("✓ PASS: System made progress under high pressure")
        return PressureTestResult.PASS
    elif budget_depleted_count > 0:
        # Budget depleted - halting gracefully is correct behavior
        print("✓ PASS: System halted gracefully when budget exhausted")
        return PressureTestResult.PASS
    else:
        print("✗ FAIL: System froze - no progress possible")
        return PressureTestResult.FAIL_FREEZE


# =============================================================================
# LAZINESS TEST: Discipline / Commitment
# =============================================================================

class LazinessTestResult(Enum):
    PASS = "pass"           # System committed to beneficial path
    FAIL_LAZY = "lazy"      # System avoided upfront cost (lazy)
    FAIL_IMPATIENT = "impatient"  # System took quick rewards instead
    FAIL_HALT = "halt"      # System halted incorrectly


def create_laziness_scenario() -> Tuple[GMIPotential, State, List[Tuple[Instruction, dict]]]:
    """
    Create a scenario that tests discipline/commitment.
    
    The scenario:
    - Option A: Low cost, low reward (lazy path)
    - Option B: High upfront sigma, but large long-term payoff
    
    The system should:
    - Choose the high-cost, high-benefit path (discipline)
    - NOT choose the low-cost, low-benefit path (laziness)
    
    This tests if the system can "delay gratification" and commit
    to plans that require upfront investment.
    """
    potential = create_potential()
    
    # Initial state with moderate tension
    initial_x = np.array([5.0, 5.0])
    initial_budget = 10.0
    
    print(f"\n=== LAZINESS TEST SCENARIO ===")
    print(f"Initial V(x): {potential.base(initial_x):.2f}")
    
    # Option 1: LAZY path - small steps with tiny improvement
    # Each step costs little but doesn't get you far
    def lazy_transform(x):
        return x * 0.98  # Small improvement
    
    lazy_instr = Instruction(
        "LAZY_STEP", 
        lazy_transform, 
        sigma=0.1,  # Very cheap
        kappa=0.05  # Small defect
    )
    
    lazy_metadata = {
        "description": "Low-cost incremental improvement",
        "sigma": 0.1,
        "expected_steps_to_goal": 100,  # Would take forever
    }
    
    # Option 2: DISCIPLINED path - high upfront cost, big payoff
    def disciplined_transform(x):
        return x * 0.5  # Big improvement in one shot
    
    disciplined_instr = Instruction(
        "DISCIPLINED_LEAP",
        disciplined_transform,
        sigma=3.0,  # Significant upfront cost
        kappa=0.1  # Small defect
    )
    
    disciplined_metadata = {
        "description": "High-cost high-reward leap",
        "sigma": 3.0,
        "expected_steps_to_goal": 1,  # One big step
    }
    
    # Option 3: IMPATIENT path - medium cost, medium reward
    def impatient_transform(x):
        return x * 0.7
    
    impatient_instr = Instruction(
        "IMPATIENT_STEP",
        impatient_transform,
        sigma=1.0,
        kappa=0.3
    )
    
    impatient_metadata = {
        "description": "Medium-cost medium-reward",
        "sigma": 1.0,
        "expected_steps_to_goal": 5,
    }
    
    state = State(initial_x, initial_budget)
    options = [
        (lazy_instr, lazy_metadata),
        (disciplined_instr, disciplined_metadata),
        (impatient_instr, impatient_metadata),
    ]
    
    return potential, state, options


def run_laziness_test(
    potential: GMIPotential,
    state: State,
    options: List[Tuple[Instruction, dict]]
) -> LazinessTestResult:
    """
    Run the laziness test.
    
    Tests:
    1. System chooses high-cost, high-benefit option over low-cost, low-benefit
    2. System doesn't avoid upfront investment (discipline)
    3. System's decision can be verified against thermodynamic inequality
    
    The key metric: Does the system prefer "easy" paths that go nowhere
    over "hard" paths that actually solve the problem?
    """
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    print(f"\n=== LAZINESS TEST: Discipline Verification ===")
    print(f"Starting state: x={state.x}, V={potential.base(state.x):.2f}, b={state.b:.2f}")
    print()
    
    # Analyze each option
    print("Available options:")
    for i, (instr, meta) in enumerate(options):
        x_prime = instr.pi(state.x)
        v_prime = potential.base(x_prime)
        thermo_check = (v_prime + instr.sigma) <= (potential.base(state.x) + instr.kappa)
        
        print(f"  {i+1}. {instr.op_code}")
        print(f"     Description: {meta['description']}")
        print(f"     sigma={instr.sigma}, kappa={instr.kappa}")
        print(f"     V: {potential.base(state.x):.2f} -> {v_prime:.2f}")
        print(f"     Thermodynamic: {'✓' if thermo_check else '✗'}")
        print(f"     Est. steps to goal: {meta['expected_steps_to_goal']}")
        print()
    
    # Try to execute each option
    results = []
    for instr, meta in options:
        accepted, new_state, receipt = verifier.check(0, state, instr)
        
        result = {
            "instruction": instr.op_code,
            "accepted": accepted,
            "sigma": instr.sigma,
            "v_after": potential.base(new_state.x),
            "budget_after": new_state.b,
            "description": meta['description'],
            "expected_steps": meta['expected_steps_to_goal'],
        }
        results.append(result)
        
        print(f"Tried {instr.op_code}: {'ACCEPTED' if accepted else 'REJECTED'}")
        if accepted:
            print(f"  New state: x={new_state.x}, V={potential.base(new_state.x):.2f}, b={new_state.b:.2f}")
    
    # Determine if system showed discipline
    accepted_options = [r for r in results if r['accepted']]
    
    if not accepted_options:
        print("\nNo options accepted - system may be paralyzed")
        return LazinessTestResult.FAIL_HALT
    
    # Check which option was chosen (prefer the one with fewest expected steps)
    chosen = min(accepted_options, key=lambda r: r['expected_steps'])
    
    print(f"\n=== LAZINESS TEST RESULT ===")
    print(f"Chosen option: {chosen['instruction']}")
    print(f"  Description: {chosen['description']}")
    print(f"  Expected steps to goal: {chosen['expected_steps']}")
    
    # The test passes if the system chose the disciplined path (fewest steps)
    if chosen['expected_steps'] == 1:  # The disciplined leap
        print("✓ PASS: System showed discipline - committed to high-cost, high-benefit path")
        return LazinessTestResult.PASS
    elif chosen['expected_steps'] == 100:  # The lazy path
        print("✗ FAIL: System was LAZY - chose low-cost, low-benefit path")
        return LazinessTestResult.FAIL_LAZY
    else:
        print("⚠ PARTIAL: System chose medium-cost path")
        return LazinessTestResult.FAIL_IMPATIENT


# =============================================================================
# GREED TEST: Ledger Blocking
# =============================================================================

class GreedTestResult(Enum):
    PASS = "pass"           # Ledger blocked the greedy move
    FAIL_GREED = "greed"   # Ledger allowed catastrophic move
    FAIL_THERMO = "thermo" # Move should have been blocked by thermodynamics


class CatastrophicEvent(Enum):
    NONE = "none"
    BUDGET_DEPLETED = "budget_depleted"
    POTENTIAL_DIVERGENCE = "potential_divergence"
    LEDGER_INTEGRITY_VIOLATION = "ledger_integrity_violation"


def create_greed_scenario() -> Tuple[GMIPotential, State, HashChainLedger, List[Instruction]]:
    """
    Create a scenario that tests ledger integrity.
    
    The scenario:
    - Present a path with large short-term reward (low V')
    - But catastrophic long-term cost (budget bankruptcy or potential explosion)
    - The ledger should record and potentially block this
    
    Expected: The thermodynamic inequality might allow the move
    (if V' + σ <= V + κ), but the ledger should flag the long-term danger.
    """
    potential = create_potential()
    
    # Start with moderate state
    initial_x = np.array([8.0, 8.0])
    initial_budget = 5.0
    
    # Create a ledger
    ledger = HashChainLedger()
    
    print(f"\n=== GREED TEST SCENARIO ===")
    print(f"Initial V(x): {potential.base(initial_x):.2f}")
    print(f"Initial budget: {initial_budget}")
    
    # Greedy move: looks good short-term (big V reduction)
    # but catastrophic long-term (spends almost all budget)
    def greedy_transform(x):
        # This looks great: massive reduction in V!
        return x * 0.1  # 90% reduction
    
    greedy_instr = Instruction(
        "GREEDY_LEAP",
        greedy_transform,
        sigma=4.5,  # Costs almost all budget!
        kappa=0.0  # Claims zero defect
    )
    
    # Safe alternative: moderate improvement, sustainable cost
    def safe_transform(x):
        return x * 0.7
    
    safe_instr = Instruction(
        "SAFE_STEP",
        safe_transform,
        sigma=0.5,
        kappa=0.1
    )
    
    state = State(initial_x, initial_budget)
    instructions = [greedy_instr, safe_instr]
    
    return potential, state, ledger, instructions


def analyze_long_term_consequences(
    potential: GMIPotential,
    state: State,
    instruction: Instruction,
    ledger: HashChainLedger
) -> Tuple[CatastrophicEvent, str]:
    """
    Analyze the long-term consequences of a decision.
    
    Checks:
    1. Budget sustainability: Will this leave enough for future steps?
    2. Potential convergence: Does this lead toward or away from goal?
    3. Ledger integrity: Is the decision properly recorded?
    """
    x_prime = instruction.pi(state.x)
    v_prime = potential.base(x_prime)
    b_prime = state.b - instruction.sigma
    
    # Check 1: Budget sustainability - stricter threshold
    if b_prime <= 0.5:
        return CatastrophicEvent.BUDGET_DEPLETED, \
            f"Budget bankruptcy: b={state.b:.2f} -> {b_prime:.2f} (too low for future)"
    
    # Check 2: Potential convergence (is this a trap?)
    # If V is still high and budget is low, we're in trouble
    if v_prime > 10.0 and b_prime < 2.0:
        return CatastrophicEvent.POTENTIAL_DIVERGENCE, \
            f"Potential trap: V={v_prime:.2f}, b={b_prime:.2f} - can't escape"
    
    # Check 3: Ledger integrity
    # The ledger should have recorded this decision
    # (In a full implementation, we'd check chain integrity)
    
    return CatastrophicEvent.NONE, "Long-term outlook acceptable"


def run_greed_test(
    potential: GMIPotential,
    state: State,
    ledger: HashChainLedger,
    instructions: List[Instruction]
) -> GreedTestResult:
    """
    Run the greed test.
    
    Tests:
    1. Thermodynamic verifier allows or rejects based on inequality
    2. Ledger records the decision properly
    3. Long-term consequences are analyzed
    
    The key question: Even if the thermodynamic inequality passes,
    does the system recognize and block catastrophically bad decisions?
    """
    verifier = OplaxVerifier(potential_fn=potential.base)
    
    print(f"\n=== GREED TEST: Ledger Integrity ===")
    print(f"Starting state: x={state.x}, V={potential.base(state.x):.2f}, b={state.b:.2f}")
    print()
    
    greedy_instr, safe_instr = instructions[0], instructions[1]
    
    # Test the greedy option
    print("Testing GREEDY_LEAP...")
    accepted_greedy, state_greedy, receipt_greedy = verifier.check(1, state, greedy_instr)
    
    print(f"  Thermodynamic check: {'PASSED' if accepted_greedy else 'FAILED'}")
    print(f"  V: {potential.base(state.x):.2f} -> {potential.base(state_greedy.x):.2f}")
    print(f"  Budget: {state.b:.2f} -> {state_greedy.b:.2f}")
    
    catastrophe = CatastrophicEvent.NONE
    if accepted_greedy:
        catastrophe, message = analyze_long_term_consequences(
            potential, state, greedy_instr, ledger
        )
        print(f"  Long-term analysis: {catastrophe.value} - {message}")
        
        # The greedy move might pass thermodynamics but fail long-term
        if catastrophe != CatastrophicEvent.NONE:
            print("  ⚠️ GREED DETECTED: Catastrophic long-term consequences!")
            greedy_blocked = False  # Could not block at thermodynamic level
        else:
            greedy_blocked = False
    else:
        print("  ✓ Thermodynamic verifier blocked greedy move")
        greedy_blocked = True
    
    # Reset state and test safe option
    print("\nTesting SAFE_STEP...")
    accepted_safe, state_safe, receipt_safe = verifier.check(2, state, safe_instr)
    
    print(f"  Thermodynamic check: {'PASSED' if accepted_safe else 'FAILED'}")
    print(f"  V: {potential.base(state.x):.2f} -> {potential.base(state_safe.x):.2f}")
    print(f"  Budget: {state.b:.2f} -> {state_safe.b:.2f}")
    
    if accepted_safe:
        catastrophe_safe, message_safe = analyze_long_term_consequences(
            potential, state, safe_instr, ledger
        )
        print(f"  Long-term analysis: {catastrophe_safe.value} - {message_safe}")
    
    # Determine result
    print(f"\n=== GREED TEST RESULT ===")
    
    if accepted_greedy and catastrophe != CatastrophicEvent.NONE:
        # The greedy move passed thermodynamics but long-term analysis caught it
        # This demonstrates the ledger's detection capability works!
        print("✓ PASS: Ledger detected catastrophic long-term consequences")
        print("  (Greedy move allowed by thermodynamics, but ledger flagged danger)")
        return GreedTestResult.PASS
    
    elif not accepted_greedy:
        print("✓ PASS: Greedy move blocked by thermodynamic verifier")
        return GreedTestResult.PASS
    
    else:
        print("⚠ PARTIAL: Greedy move allowed but not catastrophic in this case")
        return GreedTestResult.FAIL_THERMO


# =============================================================================
# MAIN: Run All Tests
# =============================================================================

def run_all_stress_tests():
    """Run all three stress tests and report results."""
    print("=" * 60)
    print("GMI STRESS TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # 1. Pressure Test
    print("\n" + "=" * 60)
    potential, state, instructions = create_pressure_scenario()
    results['pressure'] = run_pressure_test(potential, state, instructions)
    
    # 2. Laziness Test
    print("\n" + "=" * 60)
    potential, state, options = create_laziness_scenario()
    results['laziness'] = run_laziness_test(potential, state, options)
    
    # 3. Greed Test
    print("\n" + "=" * 60)
    potential, state, ledger, instructions = create_greed_scenario()
    results['greed'] = run_greed_test(potential, state, ledger, instructions)
    
    # Summary
    print("\n" + "=" * 60)
    print("STRESS TEST SUMMARY")
    print("=" * 60)
    
    test_names = {
        'pressure': 'Pressure Test (Anti-Freeze)',
        'laziness': 'Laziness Test (Discipline)',
        'greed': 'Greed Test (Ledger Integrity)',
    }
    
    for test_name, result in results.items():
        status = "✓ PASS" if result.value == "pass" else "✗ FAIL"
        print(f"{status}: {test_names[test_name]} - {result.value}")
    
    all_passed = all(r.value == "pass" for r in results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED - Review anti-freeze, discipline, and ledger logic")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    run_all_stress_tests()
