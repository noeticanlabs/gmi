"""
Stochastic LLM Synthesizer for NPE

This module adds "wild imagination" to the NPE by bypassing the strict registry
and allowing hallucinated NSC modules to be proposed to the gatekeeper.

The key insight: if governance is embedded in the generator, the generator becomes
timid. Timid generators never discover novel structures.

This synthesizer deliberately generates invalid, unregistered operators to test
the boundaries of thermodynamic feasibility - exactly like the INVENT/glyph
mechanic in the GMI evolution loop.

Key differences from BeamSearchSynthesizer:
1. No registry bounds - can propose ANY operator name
2. No type checking during proposal - gatekeeper decides validity
3. High entropy generation - discovers novel structures
4. Registry expansion - successful proposals get registered

References:
- gmi/runtime/evolution_loop.py (INVENT mechanic)
- coherence_spine/04_control/gates_and_rails.md
"""

from __future__ import annotations

import random
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum

# We'll create placeholder types that would connect to NPE's actual classes
class Module:
    """Placeholder for NPE Module - would be imported from nsc in real integration"""
    def __init__(self, module_id: str, nodes: List[Dict], metadata: Dict = None):
        self.module_id = module_id
        self.nodes = nodes
        self.metadata = metadata or {}
    
    def apply(self, x):
        """Apply module to input vector - placeholder"""
        return x


@dataclass
class WildProposal:
    """
    A hallucinated NSC module proposal.
    
    Unlike BeamSearch proposals, these can have:
    - Unregistered operator IDs
    - Invalid node structures
    - Completely novel compositions
    """
    module: Module
    is_registered: bool = False  # False = hallucinated, True = from registry
    novelty_score: float = 0.0  # How novel is this?
    hallucination_strength: float = 1.0  # Temperature-like parameter


class OperatorHallucinator:
    """
    Generates unregistered operator names and structures.
    
    This is the "dreaming" component - it invents new math.
    """
    
    # Base operations to mutate
    BASE_OPS = [
        "add", "mult", "sub", "div", "pow", "sqrt", "log", "exp",
        "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh",
        "neg", "abs", "floor", "ceil", "round", "mod", "max", "min",
    ]
    
    # Prefix/suffixes for creating novel operators
    PREFIXES = ["hyper", "quantum", "fractal", "chaos", "meta", "proto", "neo", "crypto"]
    SUFFIXES = ["ion", "oid", "ium", "ax", "ex", "or", "gen", "scope"]
    
    def generate_operator_id(self) -> str:
        """Generate a novel unregistered operator ID"""
        strategy = random.choice([
            self._mutate_existing,
            self._compose_two,
            self._add_suffix,
            self._completely_novel,
        ])
        return strategy()
    
    def _mutate_existing(self) -> str:
        """Mutate an existing operator"""
        base = random.choice(self.BASE_OPS)
        mutation = random.choice(["_", "+", "*"])
        return f"{base}{mutation}{random.randint(1, 99)}"
    
    def _compose_two(self) -> str:
        """Compose two operators into a new one"""
        op1 = random.choice(self.BASE_OPS)
        op2 = random.choice(self.BASE_OPS)
        return f"{op1}_{op2}"
    
    def _add_suffix(self) -> str:
        """Add scientific suffix to base"""
        base = random.choice(self.BASE_OPS)
        prefix = random.choice(self.PREFIXES)
        return f"{prefix}_{base}"
    
    def _completely_novel(self) -> str:
        """Generate something totally new"""
        prefix = random.choice(self.PREFIXES)
        suffix = random.choice(self.SUFFIXES)
        num = random.randint(100, 999)
        return f"{prefix}{suffix}{num}"


class StochasticSynthesizer:
    """
    The "wild" synthesizer that bypasses registry constraints.
    
    Unlike BeamSearchSynthesizer:
    - Does NOT check operator registry
    - Does NOT type-check during proposal
    - Does NOT prune by heuristics
    - CAN discover novel operators
    
    The gatekeeper (NVE) decides what's actually valid.
    """
    
    def __init__(
        self,
        temperature: float = 1.5,
        hallucination_rate: float = 0.7,
        novelty_bonus: float = 0.3,
        registry = None  # Would be OperatorRegistry in real NPE
    ):
        """
        Args:
            temperature: Higher = more wild proposals
            hallucination_rate: Probability of generating unregistered operators
            novelty_bonus: Extra score for novel discoveries
            registry: The operator registry (for adding accepted operators)
        """
        self.temperature = temperature
        self.hallucination_rate = hallucination_rate
        self.novelty_bonus = novelty_bonus
        self.registry = registry
        
        self.hallucinator = OperatorHallucinator()
        self.discovered_operators: Set[str] = set()
        
        # Statistics
        self.proposals_generated = 0
        self.hallucinations_generated = 0
    
    def generate_wild_proposals(
        self,
        context: Dict[str, Any],
        n_proposals: int = 3
    ) -> List[WildProposal]:
        """
        Generate a pool of wild proposals.
        
        Unlike BeamSearch, we deliberately generate some invalid proposals
        to test thermodynamic boundaries.
        """
        proposals = []
        
        for i in range(n_proposals):
            # Decide: hallucinate or use registered?
            if random.random() < self.hallucination_rate:
                # HALLUCINATE - generate unregistered operator
                proposal = self._generate_hallucination(context, i)
                self.hallucinations_generated += 1
            else:
                # Use something from registry (if available)
                proposal = self._generate_registry_proposal(context, i)
            
            self.proposals_generated += 1
            proposals.append(proposal)
        
        return proposals
    
    def _generate_hallucination(
        self,
        context: Dict[str, Any],
        index: int
    ) -> WildProposal:
        """Generate a hallucinated (unregistered) NSC module"""
        
        # Generate novel operator ID
        op_id = self.hallucinator.generate_operator_id()
        
        # Create nodes with this novel operator
        nodes = self._create_wild_nodes(op_id, context)
        
        # Generate unique module ID
        module_id = f"WILD_{op_id}_{random.randint(1000, 9999)}"
        
        module = Module(
            module_id=module_id,
            nodes=nodes,
            metadata={
                "is_hallucination": True,
                "original_operator": op_id,
                "hallucination_temperature": self.temperature
            }
        )
        
        # Calculate novelty score (higher = more novel)
        novelty = self._calculate_novelty(op_id)
        
        return WildProposal(
            module=module,
            is_registered=False,
            novelty_score=novelty,
            hallucination_strength=self.temperature
        )
    
    def _generate_registry_proposal(
        self,
        context: Dict[str, Any],
        index: int
    ) -> WildProposal:
        """Generate proposal using registered operators"""
        
        # This would use actual registry in real implementation
        # For now, create a "safe" proposal
        op_id = "add"  # Safe default
        
        nodes = [
            {
                "op_id": op_id,
                "inputs": ["$input"],
                "outputs": ["$output"]
            }
        ]
        
        module_id = f"SAFE_{op_id}_{random.randint(1000, 9999)}"
        module = Module(
            module_id=module_id,
            nodes=nodes,
            metadata={"is_hallucination": False}
        )
        
        return WildProposal(
            module=module,
            is_registered=True,
            novelty_score=0.0,
            hallucination_strength=0.0
        )
    
    def _create_wild_nodes(
        self,
        op_id: str,
        context: Dict[str, Any]
    ) -> List[Dict]:
        """Create NSC nodes with the hallucinated operator"""
        
        # Vary node structure for diversity
        structure = random.choice(["simple", "composed", "nested"])
        
        if structure == "simple":
            return [
                {
                    "op_id": op_id,
                    "inputs": ["$input"],
                    "outputs": ["$temp1"]
                },
                {
                    "op_id": "mult",
                    "inputs": ["$temp1", "$temp1"],
                    "outputs": ["$output"]
                }
            ]
        elif structure == "composed":
            return [
                {
                    "op_id": op_id,
                    "inputs": ["$input"],
                    "outputs": ["$temp1"]
                },
                {
                    "op_id": random.choice(["sin", "cos", "exp"]),
                    "inputs": ["$temp1"],
                    "outputs": ["$temp2"]
                },
                {
                    "op_id": "add",
                    "inputs": ["$temp2", "$input"],
                    "outputs": ["$output"]
                }
            ]
        else:  # nested
            return [
                {
                    "op_id": "mult",
                    "inputs": [
                        {"op_id": op_id, "inputs": ["$input"]},
                        {"op_id": op_id, "inputs": ["$input"]}
                    ],
                    "outputs": ["$output"]
                }
            ]
    
    def _calculate_novelty(self, op_id: str) -> float:
        """Calculate how novel this operator is"""
        
        # Already discovered = less novel
        if op_id in self.discovered_operators:
            return 0.1
        
        # Check similarity to known operators
        base_ops_str = " ".join(self.BASE_OPS)
        if op_id.split("_")[0] in base_ops_str:
            return 0.5  # Somewhat similar
        
        return 1.0  # Completely novel
    
    def register_discovery(self, op_id: str) -> bool:
        """
        Register a previously hallucinated operator.
        
        Called when the gatekeeper accepts a hallucinated proposal.
        This is the "Symbolic Atlas" expansion - the system invents
        new math and adds it to its language.
        """
        if op_id in self.discovered_operators:
            return False  # Already registered
        
        self.discovered_operators.add(op_id)
        
        # In real NPE, this would add to OperatorRegistry
        # self.registry.add_operator(op_id, ...)
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return synthesis statistics"""
        return {
            "total_proposals": self.proposals_generated,
            "hallucinations": self.hallucinations_generated,
            "discoveries": len(self.discovered_operators),
            "discovery_rate": (
                len(self.discovered_operators) / 
                max(1, self.hallucinations_generated)
            )
        }


class GMIGatekeeper:
    """
    The thermodynamic gatekeeper that validates wild proposals.
    
    This is the NVE side of the equation - it takes wild hallucinated
    modules and tests them against thermodynamic constraints.
    
    If a proposal passes:
    - It's accepted for execution
    - The hallucinated operator gets registered (Symbolic Atlas)
    
    If it fails:
    - It's rejected with detailed receipt
    - The failure is fed back for learning
    """
    
    def __init__(
        self,
        potential_fn,  # V(x) - thermodynamic tension
        budget: float = 25.0,
        sigma_base: float = 5.0,
        kappa_base: float = 12.0
    ):
        self.potential_fn = potential_fn
        self.budget = budget
        self.sigma_base = sigma_base
        self.kappa_base = kappa_base
        
        self.accepted_count = 0
        self.rejected_count = 0
        self.discoveries = []
    
    def validate(
        self,
        proposal: WildProposal,
        current_state: Any
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a wild proposal against thermodynamic constraints.
        
        Returns:
            (accepted, receipt)
        """
        # Extract the transformation from the module
        # In real implementation, this would execute the NSC module
        x_prime = self._execute_module(proposal.module, current_state)
        
        # Calculate thermodynamic metrics
        v_current = self.potential_fn(current_state)
        v_proposed = self.potential_fn(x_prime)
        
        # Calculate sigma/kappa based on novelty
        sigma = self.sigma_base * (1 + proposal.novelty_score)
        kappa = self.kappa_base * (1 + proposal.novelty_score)
        
        # Thermodynamic inequality: V(x') + σ ≤ V(x) + κ + b
        thermo_valid = (v_proposed + sigma) <= (v_current + kappa + self.budget)
        
        # Budget check
        budget_valid = sigma <= self.budget
        
        if thermo_valid and budget_valid:
            self.accepted_count += 1
            
            receipt = {
                "accepted": True,
                "module_id": proposal.module.module_id,
                "v_before": v_current,
                "v_after": v_proposed,
                "sigma": sigma,
                "kappa": kappa,
                "novelty": proposal.novelty_score,
                "message": "Thermodynamically admissible"
            }
            
            # If this was a hallucination, mark for registry
            if not proposal.is_registered:
                receipt["should_register"] = True
                receipt["operator_id"] = proposal.module.metadata.get("original_operator")
            
            return True, receipt
        
        else:
            self.rejected_count += 1
            
            reason = []
            if not thermo_valid:
                reason.append(f"Thermodynamic violation: {v_proposed}+{sigma} > {v_current}+{kappa}")
            if not budget_valid:
                reason.append(f"Budget exhausted: {sigma} > {self.budget}")
            
            receipt = {
                "accepted": False,
                "module_id": proposal.module.module_id,
                "v_before": v_current,
                "v_after": v_proposed,
                "sigma": sigma,
                "kappa": kappa,
                "novelty": proposal.novelty_score,
                "message": "; ".join(reason)
            }
            
            return False, receipt
    
    def _execute_module(self, module: Module, state) -> Any:
        """Execute the NSC module - placeholder"""
        # In real implementation, this would:
        # 1. Parse the NSC module JSON
        # 2. Execute each node in topological order
        # 3. Handle unregistered operators gracefully
        return state  # Placeholder
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return gatekeeper statistics"""
        total = self.accepted_count + self.rejected_count
        return {
            "accepted": self.accepted_count,
            "rejected": self.rejected_count,
            "acceptance_rate": self.accepted_count / max(1, total),
            "discoveries": len(self.discoveries)
        }


# Example usage
if __name__ == "__main__":
    import numpy as np
    
    # Simple quadratic potential
    def V(x):
        return float(np.sum(x**2))
    
    # Create components
    synthesizer = StochasticSynthesizer(
        temperature=1.5,
        hallucination_rate=0.7
    )
    
    gatekeeper = GMIGatekeeper(
        potential_fn=V,
        budget=25.0
    )
    
    # Generate wild proposals
    context = {"task": "test"}
    proposals = synthesizer.generate_wild_proposals(context, n_proposals=5)
    
    print("=== Wild Proposal Generation ===")
    for p in proposals:
        print(f"  {p.module.module_id}: registered={p.is_registered}, novelty={p.noveltyf}")
    
    print("\n=== Gatekeeper Validation_score:.2 ===")
    current_state = np.array([1.0, 1.0])
    
    for proposal in proposals:
        accepted, receipt = gatekeeper.validate(proposal, current_state)
        status = "ACCEPTED" if accepted else "REJECTED"
        print(f"  {proposal.module.module_id}: {status}")
        print(f"    {receipt['message']}")
        
        # Register if hallucinated and accepted
        if accepted and not proposal.is_registered:
            op_id = proposal.module.metadata.get("original_operator")
            if op_id:
                synthesizer.register_discovery(op_id)
                gatekeeper.discoveries.append(op_id)
                print(f"    → Registered new operator: {op_id}")
    
    print("\n=== Statistics ===")
    print(f"Synthesizer: {synthesizer.get_statistics()}")
    print(f"Gatekeeper: {gatekeeper.get_statistics()}")
