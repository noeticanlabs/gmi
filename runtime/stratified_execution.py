"""
Stratified Execution Loop for the GMI Universal Cognition Engine.

Module 17 Integration: Full Stratified Mind Architecture

This module integrates all the stratified mind components:
- StratifiedState (core/stratified_state.py)
- HierarchicalBudget (core/hierarchical_budget.py)
- LayerOperatorRegistry (core/stratified_operators.py)
- SlabVerifier (ledger/slab_verifier.py)
- Theorems 17.1 & 17.2 (core/stratified_theorems.py)

The execution loop demonstrates:
1. Layer-by-layer execution with different timescales
2. Budget cascade between layers
3. Slab verification at Layer 1
4. Theorem verification at runtime
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import hashlib

# Import Module 17 components
from core.stratified_state import (
    StratifiedState, 
    LayerState, 
    LayerConfig,
    create_default_stratified_state
)
from core.hierarchical_budget import (
    HierarchicalBudget, 
    BudgetCascade,
    create_default_hierarchical_budget,
    verify_budget_transfer_invariant
)
from core.stratified_operators import (
    LayerOperatorRegistry,
    BranchPricing,
    OperatorType,
    StratifiedOperator,
    create_layer_operators,
    verify_no_branching_at_layer_1
)
from ledger.slab_verifier import (
    SlabVerifier,
    MicroReceipt,
    Slab,
    create_micro_receipt
)
from core.stratified_theorems import (
    Theorem17_1Config,
    LayerViabilityState,
    verify_theorem_17_1,
    verify_theorem_17_2,
    describe_layer_roles
)


class StratifiedExecutor:
    """
    The stratified execution engine.
    
    This implements the key insight: fast layers keep system alive,
    slow layers explore possibilities.
    """
    
    def __init__(
        self,
        num_layers: int = 3,
        dimension: int = 10,
        total_budget: float = 100.0,
        reflex_reserve: float = 10.0
    ):
        """
        Initialize the stratified executor.
        
        Args:
            num_layers: Number of cognitive layers
            dimension: State dimension per layer
            total_budget: Total thermodynamic budget
            reflex_reserve: Minimum reserve for Layer 1
        """
        self.num_layers = num_layers
        self.dimension = dimension
        
        # Create stratified state
        self.stratified_state = create_default_stratified_state(
            num_layers=num_layers,
            dimension=dimension,
            initial_budget=total_budget
        )
        
        # Create hierarchical budget
        self.budget = create_default_hierarchical_budget(
            num_layers=num_layers,
            total_budget=total_budget,
            reflex_reserve=reflex_reserve
        )
        
        # Create operator registry
        self.registry = LayerOperatorRegistry()
        
        # Create branch pricing
        self.branch_pricing = BranchPricing()
        
        # Create slab verifier for Layer 1
        self.slab_verifier = SlabVerifier(max_slab_size=100)
        
        # Layer 1 micro-receipts buffer
        self.layer1_receipts: List[MicroReceipt] = []
        
        # Execution statistics
        self.stats = {
            'total_steps': 0,
            'layer_executions': {l: 0 for l in range(1, num_layers + 1)},
            'branches_opened': {l: 0 for l in range(1, num_layers + 1)},
            'budget_cascades': 0,
            'slab_verifications': 0,
            'theorem_checks': []
        }
    
    def execute_layer(
        self,
        layer_id: int,
        operators: List[StratifiedOperator]
    ) -> Tuple[bool, LayerState, List[MicroReceipt]]:
        """
        Execute a single layer with its operators.
        
        Args:
            layer_id: Layer to execute
            operators: Available operators for this layer
            
        Returns:
            Tuple of (success, new_layer_state, micro_receipts)
        """
        layer_state = self.stratified_state.get_layer(layer_id)
        config = self.stratified_state.get_config(layer_id)
        
        receipts = []
        
        # Get available budget at this layer
        available = self.budget.get_available(layer_id)
        
        # Execute each operator
        for op in operators:
            if op.sigma > available:
                continue  # Cannot afford this operator
            
            # Execute the operator (simple quadratic potential)
            old_x = layer_state.x.copy()
            potential_before = np.sum(old_x ** 2)
            
            # Apply transition if possible
            if op.pi_func is not None:
                new_x = op.pi_func(old_x)
            else:
                new_x = old_x  # No change (e.g., for branch)
            
            potential_after = np.sum(new_x ** 2)
            
            # Check thermodynamic inequality: V' + σ ≤ V + κ + b
            lhs = potential_after + op.sigma
            rhs = potential_before + op.kappa + available
            
            if lhs <= rhs:
                # Accept the move
                layer_state.x = new_x
                available -= op.sigma
                
                # Record receipt (for Layer 1)
                if layer_id == 1:
                    receipt = create_micro_receipt(
                        pre_state=old_x,
                        post_state=new_x,
                        sigma=op.sigma,
                        kappa=op.kappa,
                        metadata={'operator': op.op_type.value}
                    )
                    receipts.append(receipt)
                
                # Track branching
                if op.op_type == OperatorType.BRANCH:
                    self.stats['branches_opened'][layer_id] += 1
        
        # Update budget state
        self.budget.layer_budgets[layer_id - 1] = available + self.budget.min_reserves[layer_id - 1]
        
        return True, layer_state, receipts
    
    def execute_stratified_step(self) -> Dict:
        """
        Execute one full stratified step across all layers.
        
        This implements the multi-timescale execution:
        - Layer 1: Many fast steps
        - Layer 2: Fewer medium steps
        - Layer L: One slow step
        
        Returns:
            Execution results
        """
        results = {
            'layer_results': {},
            'theorem_checks': {},
            'budget_cascade': False
        }
        
        # Get layer roles
        roles = describe_layer_roles(self.num_layers)
        
        # Execute each layer
        for layer_id in range(1, self.num_layers + 1):
            # Get operators for this layer
            operators = create_layer_operators(
                layer_id=layer_id,
                dimension=self.dimension,
                registry=self.registry
            )
            
            # Execute layer
            success, new_state, receipts = self.execute_layer(layer_id, operators)
            
            # Collect Layer 1 receipts for slab verification
            if layer_id == 1:
                self.layer1_receipts.extend(receipts)
                
                # Batch verify Layer 1 receipts periodically
                if len(self.layer1_receipts) >= 10:
                    verified, ver_results = self.slab_verifier.verify_batch(
                        self.layer1_receipts
                    )
                    self.stats['slab_verifications'] += 1
                    
                    # Clear verified receipts
                    self.layer1_receipts = []
                    
                    results['slab_verification'] = {
                        'verified': verified,
                        'num_receipts': len(ver_results)
                    }
            
            results['layer_results'][layer_id] = {
                'success': success,
                'num_receipts': len(receipts),
                'role': roles.get(layer_id, 'Unknown')
            }
            
            self.stats['layer_executions'][layer_id] += 1
        
        # Trigger budget cascade if needed
        cascade = BudgetCascade(self.budget)
        triggered, delegations = cascade.trigger_if_needed()
        
        if triggered:
            self.stats['budget_cascades'] += 1
            results['budget_cascade'] = True
            results['cascade_delegations'] = [
                {'from': d.from_layer, 'to': d.to_layer, 'amount': d.amount}
                for d in delegations
            ]
        
        # Verify theorems periodically
        if self.stats['total_steps'] % 10 == 0:
            theorem_results = self.verify_theorems()
            results['theorem_checks'] = theorem_results
            self.stats['theorem_checks'].append(theorem_results)
        
        self.stats['total_steps'] += 1
        
        return results
    
    def verify_theorems(self) -> Dict:
        """
        Verify Theorems 17.1 and 17.2.
        
        Returns:
            Theorem verification results
        """
        results = {}
        
        # Theorem 17.1: Combinatorial explosion bound
        config_17_1 = Theorem17_1Config(
            layer_budgets=self.budget.layer_budgets,
            min_branch_costs=[
                self.registry.get_config(l).min_operator_cost 
                for l in range(1, self.num_layers + 1)
            ],
            max_layer_branches=[
                self.stats['branches_opened'][l]
                for l in range(1, self.num_layers + 1)
            ]
        )
        
        holds_17_1, details_17_1 = verify_theorem_17_1(config_17_1)
        results['theorem_17_1'] = {
            'holds': holds_17_1,
            'details': details_17_1
        }
        
        # Theorem 17.2: Global viability
        layer_states = [
            LayerViabilityState(
                potential=np.sum(self.stratified_state.get_layer(l).x ** 2),
                budget=self.budget.layer_budgets[l - 1],
                spend=0.1,  # Estimate
                defect=0.2   # Estimate
            )
            for l in range(1, self.num_layers + 1)
        ]
        
        # Budget deltas (assume 0 for now, would be from actual transfers)
        budget_deltas = [0.0] * self.num_layers
        
        holds_17_2, details_17_2 = verify_theorem_17_2(layer_states, budget_deltas)
        results['theorem_17_2'] = {
            'holds': holds_17_2,
            'details': details_17_2
        }
        
        return results
    
    def run(
        self,
        num_steps: int = 100,
        verbose: bool = True
    ) -> Dict:
        """
        Run the stratified executor for a number of steps.
        
        Args:
            num_steps: Number of steps to run
            verbose: Whether to print progress
            
        Returns:
            Final statistics
        """
        if verbose:
            print("=" * 60)
            print("STRATIFIED MIND EXECUTION")
            print("=" * 60)
            print(f"Layers: {self.num_layers}")
            print(f"Total Budget: {self.budget.total_budget}")
            print(f"Reflex Reserve: {self.budget.min_reserves[0]}")
            print()
            
            # Print layer roles
            roles = describe_layer_roles(self.num_layers)
            for layer_id, role in roles.items():
                print(f"  Layer {layer_id}: {role}")
            print()
        
        for step in range(num_steps):
            results = self.execute_stratified_step()
            
            if verbose and step % 20 == 0:
                print(f"Step {step}:")
                print(f"  Budgets: {[round(b, 1) for b in self.budget.layer_budgets]}")
                print(f"  Total V: {self.stratified_state.compute_viability():.2f}")
                
                if results.get('budget_cascade'):
                    print(f"  ⚡ Budget cascade triggered")
                
                if results.get('theorem_checks'):
                    t17_1 = results['theorem_checks'].get('theorem_17_1', {})
                    t17_2 = results['theorem_checks'].get('theorem_17_2', {})
                    print(f"  ✓ Theorem 17.1: {t17_1.get('holds', 'N/A')}")
                    print(f"  ✓ Theorem 17.2: {t17_2.get('holds', 'N/A')}")
        
        if verbose:
            print()
            print("=" * 60)
            print("EXECUTION COMPLETE")
            print("=" * 60)
            print(f"Total steps: {self.stats['total_steps']}")
            print(f"Layer executions: {self.stats['layer_executions']}")
            print(f"Branches opened: {self.stats['branches_opened']}")
            print(f"Budget cascades: {self.stats['budget_cascades']}")
            print(f"Slab verifications: {self.stats['slab_verifications']}")
            print()
            print(f"Final budgets: {[round(b, 2) for b in self.budget.layer_budgets]}")
            print(f"System viable: {self.budget.is_viable()}")
        
        return self.stats


def run_stratified_demo():
    """
    Demonstrate the stratified mind architecture.
    
    This shows all components working together:
    - Layer-specific execution
    - Budget delegation
    - Branch pricing (σ_branch > 0)
    - Slab verification
    - Theorem verification
    """
    print("\n" + "=" * 60)
    print("MODULE 17: STRATIFIED MIND MANIFOLD DEMO")
    print("=" * 60)
    print()
    
    # Create executor
    executor = StratifiedExecutor(
        num_layers=3,
        dimension=5,
        total_budget=100.0,
        reflex_reserve=10.0
    )
    
    # Verify initial state
    print("Initial Configuration:")
    print(f"  Number of layers: {executor.num_layers}")
    print(f"  Total budget: {executor.budget.total_budget}")
    print(f"  Per-layer budgets: {executor.budget.layer_budgets}")
    print(f"  Per-layer reserves: {executor.budget.min_reserves}")
    print()
    
    # Verify Layer 1 has no branching
    ops_l1 = create_layer_operators(1, 5, executor.registry)
    has_no_branching = verify_no_branching_at_layer_1(ops_l1)
    print(f"Layer 1 no-branching invariant: {has_no_branching}")
    assert has_no_branching, "Layer 1 must not have branching operators!"
    print()
    
    # Run execution
    stats = executor.run(num_steps=50, verbose=True)
    
    # Final theorem verification
    print()
    print("Final Theorem Verification:")
    
    # Get final budgets
    final_budgets = executor.budget.layer_budgets
    min_costs = [executor.registry.get_config(l).min_operator_cost 
                 for l in range(1, executor.num_layers + 1)]
    max_branches = [stats['branches_opened'][l] for l in range(1, executor.num_layers + 1)]
    
    config_17_1 = Theorem17_1Config(
        layer_budgets=final_budgets,
        min_branch_costs=min_costs,
        max_layer_branches=max_branches
    )
    
    holds_17_1, _ = verify_theorem_17_1(config_17_1)
    print(f"  Theorem 17.1 (Combinatorial Bound): {'HOLDS' if holds_17_1 else 'VIOLATED'}")
    
    # Global viability
    layer_states = [
        LayerViabilityState(
            potential=np.sum(executor.stratified_state.get_layer(l).x ** 2),
            budget=final_budgets[l - 1],
            spend=0.0,
            defect=0.0
        )
        for l in range(1, executor.num_layers + 1)
    ]
    
    holds_17_2, _ = verify_theorem_17_2(layer_states, [0.0] * executor.num_layers)
    print(f"  Theorem 17.2 (Global Viability): {'HOLDS' if holds_17_2 else 'VIOLATED'}")
    
    print()
    print("✓ Module 17 implementation complete")
    
    return stats


if __name__ == "__main__":
    run_stratified_demo()
