"""
Hosted GMI Agent for GM-OS.

A true process-facing GMI agent that runs inside the GM-OS kernel substrate.
This agent consumes GM-OS kernel services while maintaining GMI-specific cognitive logic.

Key features:
- step(): Execute one cognitive step
- propose_action(): Generate candidate moves
- evaluate_candidates(): Score and rank candidates using GMI potential
- commit_transition(): Commit a lawful transition through the kernel
- handle_halt(): Handle halt condition when no lawful moves exist
- handle_wake(): Handle wake condition from torpor

GM-OS services consumed:
- state_host: Process state management
- budget_router: Budget allocation and reserve enforcement  
- kernel_verifier: Lawfulness verification
- receipt_engine: Receipt generation and chain updates
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import numpy as np

# GM-OS Kernel imports
from gmos.kernel.state_host import StateHost, HostedState, ProcessStateFlag
from gmos.kernel.budget_router import BudgetRouter, ReserveTier
from gmos.kernel.scheduler import KernelScheduler, ScheduleMode
from gmos.kernel.receipt_engine import ReceiptEngine, ReceiptType

# GMI imports - these import from the root gmi package
from gmos.agents.gmi.state import State as GMIState, Proposal as GMIProposal
from gmos.agents.gmi.state import Instruction, CognitiveState
from gmos.agents.gmi.potential import GMIPotential, create_potential
from gmos.agents.gmi.affective_budget import AffectiveBudgetManager
from gmos.agents.gmi.affective_state import AffectiveCognitiveState
from gmos.agents.gmi.policy_selection import PolicySelector


class AgentStatus(Enum):
    """Agent execution status."""
    ACTIVE = "active"
    HALTED = "halted"
    TORPOR = "torpor"
    WAKE_PENDING = "wake_pending"


@dataclass
class AgentConfig:
    """Configuration for the hosted GMI agent."""
    process_id: str
    initial_x: List[float]
    initial_budget: float
    reserve_floor: float = 1.0
    survival_reserve: float = 0.5
    # GMI-specific configuration
    potential_config: Dict[str, Any] = field(default_factory=dict)
    policy_config: Dict[str, Any] = field(default_factory=dict)
    affect_config: Dict[str, Any] = field(default_factory=dict)


class HostedGMIAgent:
    """
    A true hosted GMI process that runs inside GM-OS.
    
    This agent:
    1. Registers with GM-OS kernel (state_host, budget_router)
    2. Uses GM-OS services for state management and verification
    3. Maintains GMI-specific cognitive logic (potential, policy, affect)
    4. Emits receipts through the receipt engine
    
    Usage:
        # Create GM-OS services
        state_host = StateHost()
        budget_router = BudgetRouter()
        receipt_engine = ReceiptEngine()
        
        # Create agent
        config = AgentConfig(
            process_id="gmi-1",
            initial_x=[1.0, 1.0],
            initial_budget=10.0,
            reserve_floor=1.0
        )
        agent = HostedGMIAgent(config, state_host, budget_router, receipt_engine)
        
        # Execute steps
        result = agent.step()
    """
    
    def __init__(
        self,
        config: AgentConfig,
        state_host: StateHost,
        budget_router: BudgetRouter,
        receipt_engine: ReceiptEngine,
        scheduler: Optional[KernelScheduler] = None
    ):
        self.config = config
        self.state_host = state_host
        self.budget_router = budget_router
        self.receipt_engine = receipt_engine
        self.scheduler = scheduler
        
        # GMI-specific components
        self.potential = create_potential(**config.potential_config)
        self.policy_selector = PolicySelector(**config.policy_config)
        self.affective_budget = AffectiveBudgetManager(**config.affect_config)
        self.affective_state = AffectiveCognitiveState()
        
        # Agent state
        self.status = AgentStatus.ACTIVE
        self._gmi_state: Optional[GMIState] = None
        self._step_count = 0
        
        # Register with GM-OS kernel
        self._register_with_kernel()
    
    def _register_with_kernel(self) -> None:
        """Register this agent with GM-OS kernel services."""
        # Register with state host
        initial_state = {
            "x": self.config.initial_x,
            "b": self.config.initial_budget,
            "potential": self.potential.total(
                np.array(self.config.initial_x),
                self.config.initial_budget
            )
        }
        self.state_host.register_process(self.config.process_id, initial_state)
        
        # Register with budget router
        self.budget_router.register_process_budget(
            process_id=self.config.process_id,
            layer=1,  # survival layer
            amount=self.config.initial_budget,
            reserve=self.config.reserve_floor,
            tier=ReserveTier.SURVIVAL
        )
        
        # Register with scheduler if provided
        if self.scheduler:
            self.scheduler.register_process(
                self.config.process_id,
                ScheduleMode.ACTIVE
            )
    
    def step(self, sensory_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute one cognitive step.
        
        Args:
            sensory_input: Optional sensory state to process
            
        Returns:
            Step result with status, action taken, and metadata
        """
        if self.status == AgentStatus.HALTED:
            return {"status": "halted", "reason": "Agent already halted"}
        
        if self.status == AgentStatus.TORPOR:
            return {"status": "torpor", "reason": "Agent in torpor"}
        
        # Get current state from GM-OS
        hosted_state = self.state_host.get_state(self.config.process_id)
        if hosted_state is None:
            return {"status": "error", "reason": "State not found"}
        
        # Reconstruct GMI state from hosted state
        x = np.array(hosted_state.state_data.get("x", self.config.initial_x))
        b = hosted_state.state_data.get("b", self.config.initial_budget)
        
        self._gmi_state = GMIState(x=x.tolist(), budget=b)
        
        # Process sensory input if provided
        if sensory_input:
            self._process_sensory(sensory_input)
        
        # Propose actions
        candidates = self.propose_action()
        
        if not candidates:
            # No candidates - trigger halt
            return self.handle_halt()
        
        # Evaluate and select best candidate
        selected = self.evaluate_candidates(candidates)
        
        if selected is None:
            # No admissible moves - trigger halt
            return self.handle_halt()
        
        # Commit transition through kernel
        result = self.commit_transition(selected)
        
        self._step_count += 1
        return result
    
    def propose_action(self) -> List[GMIProposal]:
        """
        Generate candidate actions using the policy selector.
        
        Returns:
            List of candidate proposals
        """
        if self._gmi_state is None:
            return []
        
        # Generate instructions using policy selector
        instructions = self.policy_selector.generate_instructions(
            self._gmi_state,
            self.potential
        )
        
        # Create proposals
        proposals = []
        for instruction in instructions:
            x_prime = instruction.apply(self._gmi_state.x)
            proposal = GMIProposal(
                instruction=instruction,
                x_prime=x_prime
            )
            proposals.append(proposal)
        
        return proposals
    
    def evaluate_candidates(
        self, 
        candidates: List[GMIProposal]
    ) -> Optional[GMIProposal]:
        """
        Evaluate and rank candidates using GMI potential and budget constraints.
        
        Args:
            candidates: List of candidate proposals
            
        Returns:
            Best admissible candidate, or None if no admissible moves
        """
        if not candidates or self._gmi_state is None:
            return None
        
        budget = self._gmi_state.b
        admissible = []
        
        for proposal in candidates:
            # Get sigma (cost) from instruction
            sigma = proposal.instruction.sigma
            
            # Check budget constraint via budget router (reserve law enforcement)
            if not self.budget_router.can_spend(
                self.config.process_id, 
                layer=1, 
                amount=sigma
            ):
                continue
            
            # Check that new budget doesn't violate reserve floor
            new_budget = budget - sigma
            if new_budget < self.config.reserve_floor:
                continue
            
            # Compute potential change (GMI-specific scoring)
            current_pot = self.potential.total(
                self._gmi_state.x, 
                self._gmi_state.b
            )
            new_pot = self.potential.total(
                proposal.x_prime,
                budget - sigma
            )
            
            # Score: prefer decreasing potential (gradient descent)
            score = current_pot - new_pot
            
            # Apply affect modulation
            affect_score = self.affective_state.modulate_score(score)
            
            admissible.append((proposal, affect_score))
        
        if not admissible:
            return None
        
        # Select best by score
        admissible.sort(key=lambda x: x[1], reverse=True)
        return admissible[0][0]
    
    def commit_transition(self, proposal: GMIProposal) -> Dict[str, Any]:
        """
        Commit a transition through GM-OS kernel.
        
        This method:
        1. Gets current state hash
        2. Applies the instruction
        3. Updates budget via budget router
        4. Verifies the transition
        5. Commits new state to state host
        6. Generates receipt
        
        Args:
            proposal: The selected proposal to commit
            
        Returns:
            Transition result
        """
        if self._gmi_state is None:
            return {"status": "error", "reason": "No GMI state"}
        
        # Get current state for receipt
        hosted_state = self.state_host.get_state(self.config.process_id)
        state_hash_prev = hosted_state.state_hash if hosted_state else ""
        budget_prev = self._gmi_state.b
        
        # Apply instruction
        sigma = proposal.instruction.sigma
        new_x = proposal.x_prime
        new_budget = budget_prev - sigma
        
        # Update budget via router
        self.budget_router.apply_spend(
            self.config.process_id,
            layer=1,
            amount=sigma
        )
        
        # Verify budget is still above reserve after spend
        if new_budget < self.config.reserve_floor:
            return {"status": "rejected", "reason": "Reserve floor violation"}
        
        # Update state in state host
        new_state_data = {
            "x": new_x.tolist() if hasattr(new_x, 'tolist') else list(new_x),
            "b": new_budget,
            "potential": self.potential.total(new_x, new_budget)
        }
        self.state_host.set_state(self.config.process_id, new_state_data)
        
        # Get new state hash
        new_hosted_state = self.state_host.get_state(self.config.process_id)
        state_hash_next = new_hosted_state.state_hash if new_hosted_state else ""
        
        # Generate receipt
        receipt = self.receipt_engine.make_transition_receipt(
            process_id=self.config.process_id,
            step_index=self._step_count,
            state_hash_prev=state_hash_prev,
            state_hash_next=state_hash_next,
            budget_prev=budget_prev,
            budget_next=new_budget,
            decision_code=1,  # accepted
            metadata={"instruction": proposal.instruction.name}
        )
        
        # Update GMI state
        self._gmi_state = GMIState(x=new_x.tolist() if hasattr(new_x, 'tolist') else list(new_x), budget=new_budget)
        
        return {
            "status": "success",
            "step": self._step_count,
            "instruction": proposal.instruction.name,
            "new_x": new_x.tolist() if hasattr(new_x, 'tolist') else new_x,
            "new_budget": new_budget,
            "receipt_id": receipt.receipt_id
        }
    
    def handle_halt(self) -> Dict[str, Any]:
        """
        Handle halt condition when no lawful moves exist.
        
        This is called when:
        - No admissible candidates found
        - Budget exhausted below reserve floor
        - All moves rejected by verifier
        
        Returns:
            Halt result
        """
        # Mark halted in state host
        self.state_host.mark_halt(self.config.process_id)
        
        # Update status
        self.status = AgentStatus.HALTED
        
        # Generate halt receipt
        hosted_state = self.state_host.get_state(self.config.process_id)
        receipt = self.receipt_engine.make_halt_receipt(
            process_id=self.config.process_id,
            step_index=self._step_count,
            state_hash=hosted_state.state_hash if hosted_state else "",
            budget=self._gmi_state.b if self._gmi_state else 0.0
        )
        
        return {
            "status": "halted",
            "receipt_id": receipt.receipt_id,
            "reason": "No lawful moves available"
        }
    
    def handle_wake(self, wake_condition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle wake condition from torpor.
        
        Called when:
        - Budget replenished above wake threshold
        - External event triggers wake
        - Scheduled wake condition met
        
        Args:
            wake_condition: Condition that triggered wake
            
        Returns:
            Wake result
        """
        # Check if we can wake
        if self.status != AgentStatus.TORPOR:
            return {"status": "error", "reason": "Not in torpor"}
        
        # Verify wake condition is met
        current_budget = self.budget_router.get_budget(self.config.process_id)
        wake_threshold = self.config.reserve_floor * 2  # Wake at 2x reserve
        
        if current_budget < wake_threshold:
            return {"status": "rejected", "reason": "Budget too low to wake"}
        
        # Mark waking in state host
        self.state_host.mark_wake(self.config.process_id)
        
        # Update status
        self.status = AgentStatus.ACTIVE
        
        # Generate wake receipt
        hosted_state = self.state_host.get_state(self.config.process_id)
        receipt = self.receipt_engine.make_wake_receipt(
            process_id=self.config.process_id,
            state_hash=hosted_state.state_hash if hosted_state else "",
            budget=current_budget
        )
        
        return {
            "status": "woken",
            "receipt_id": receipt.receipt_id,
            "budget": current_budget
        }
    
    def enter_torpor(self) -> Dict[str, Any]:
        """
        Enter torpor mode (low budget / idle).
        
        Returns:
            Torpor result
        """
        # Mark in torpor in state host
        self.state_host.mark_torpor(self.config.process_id)
        
        # Update status
        self.status = AgentStatus.TORPOR
        
        # Generate torpor receipt
        hosted_state = self.state_host.get_state(self.config.process_id)
        receipt = self.receipt_engine.make_torpor_receipt(
            process_id=self.config.process_id,
            step_index=self._step_count,
            state_hash=hosted_state.state_hash if hosted_state else "",
            budget=self._gmi_state.b if self._gmi_state else 0.0
        )
        
        return {
            "status": "torpor",
            "receipt_id": receipt.receipt_id
        }
    
    def _process_sensory(self, sensory_input: Dict[str, Any]) -> None:
        """
        Process sensory input into the cognitive state.
        
        Args:
            sensory_input: Sensory state from sensory layer
        """
        # Update affective state based on sensory input
        self.affective_state.update_from_sensory(sensory_input)
        
        # Update affect-modulated budget
        self.affective_budget.update(
            base_budget=self._gmi_state.b if self._gmi_state else 0.0,
            affective_state=self.affective_state
        )
    
    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        return self.status
    
    def get_state(self) -> Optional[GMIState]:
        """Get current GMI state."""
        return self._gmi_state
    
    def get_hosted_state(self) -> Optional[HostedState]:
        """Get current hosted state from state host."""
        return self.state_host.get_state(self.config.process_id)
