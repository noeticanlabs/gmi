# Unified Implementation Plan: Coh-IL Evaluator + CharacterShell Integration

> **Status**: Planning Complete  
> **Priority**: Tier 1 - Critical Infrastructure Gaps  
> **Created**: 2026-03-12

## Executive Summary

This plan addresses two critical bleeding wounds in the GM-OS codebase:

1. **Wound 1: Missing Coh-IL Evaluator** - The kernel accepts proposals without formal instruction parsing or cost validation
2. **Wound 2: Disconnected CharacterShell** - The hosted agent doesn't use real `character_shell.py` or `tension_law.py`

### Dependency Graph

```
Phase 1: Coh-IL Evaluator (Foundation)
├── 1.1 Define CohInstructionType enum
├── 1.2 Define CohInstruction dataclass
├── 1.3 Define ValidationResult type
├── 1.4 Implement CohILParser.parse()
├── 1.5 Implement cost/defect calculation (σ/κ)
├── 1.6 Implement CohILParser.validate()
├── 1.7 Implement CohILParser.normalize()
├── 1.8 Create to_transition_proposal() converter
└── 1.9 Create CohILEvaluator facade class

Phase 2: Mediator Integration
├── 2.1 Add CohILEvaluator to KernelMediator
├── 2.2 Insert evaluator between proposal and verifier
└── 2.3 Wire instruction lineage into receipts

Phase 3: CharacterShell Integration (Independent of Phase 1-2)
├── 3.1 Analyze character_shell.py module
├── 3.2 Import CharacterShell into hosted_agent.py
├── 3.3 Integrate tension_law.py residuals
├── 3.4 Wire χ parameters into proposal generation
├── 3.5 Add character drift under experience
└── 3.6 Extend AgentConfig with character_config

Phase 4: Testing
├── 4.1 Unit tests for CohILParser
├── 4.2 Integration test for evaluator-verifier flow
└── 4.3 Integration test for CharacterShell behavior modulation

Phase 5: Backward Compatibility & Migration
├── 5.1 Evaluator passthrough mode for legacy proposals
├── 5.2 Mediator dual-mode support (feature flag)
├── 5.3 Feature flag rollout sequence
└── 5.4 Migration checklist
```

---

## Phase 1: Coh-IL Evaluator Implementation

### 1.1-1.3: Core Types (Expanded)

**File**: `gmos/src/gmos/kernel/cohil_evaluator.py`

Create the following types per `docs/cohil_evaluator_spec.md`:

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union

class CohInstructionType(Enum):
    """Core instruction types per Coh-IL specification."""
    NOOP = "noop"
    OBSERVE = "observe"
    INFER = "infer"
    RETRIEVE = "retrieve"
    REPAIR = "repair"
    BRANCH = "branch"
    PLAN = "plan"
    ACT_PREPARE = "act_prepare"
    ACT_COMMIT = "act_commit"

@dataclass
class CohInstruction:
    """
    Structured Coh-IL instruction.
    
    Fields:
        intent: The instruction type (CohInstructionType)
        parameters: Typed parameters for the instruction
        cost_estimate: Computed thermodynamic cost σ
        defect_estimate: Computed uncertainty κ
        prerequisites: List of required prior instruction IDs
        raw_payload: Original dict for audit trail
    """
    intent: CohInstructionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    cost_estimate: float = 0.0
    defect_estimate: float = 0.0
    prerequisites: List[str] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for hashing/JSON."""
        return {
            "intent": self.intent.value,
            "parameters": self.parameters,
            "cost_estimate": self.cost_estimate,
            "defect_estimate": self.defect_estimate,
            "prerequisites": self.prerequisites,
        }

@dataclass
class ValidationResult:
    """Result of instruction validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        return self.is_valid
```

### 1.4-1.7: Parser Implementation (Detailed)

The `CohILParser` class with full implementation:

```python
class CohILParser:
    """
    Parses raw proposals into structured Coh-IL instructions.
    
    Responsibilities:
    1. Validate instruction syntax
    2. Normalize parameters to canonical forms
    3. Compute cost/defect estimates
    4. Build dependency graph
    """
    
    # Per instruction type cost baseline
    COST_BASELINES = {
        CohInstructionType.NOOP: 0.0,
        CohInstructionType.OBSERVE: 0.1,
        CohInstructionType.INFER: 0.2,
        CohInstructionType.RETRIEVE: 0.15,
        CohInstructionType.REPAIR: 0.3,
        CohInstructionType.BRANCH: 0.25,
        CohInstructionType.PLAN: 0.35,
        CohInstructionType.ACT_PREPARE: 0.4,
        CohInstructionType.ACT_COMMIT: 0.5,
    }
    
    # Per instruction type defect baseline
    DEFECT_BASELINES = {
        CohInstructionType.NOOP: 0.0,
        CohInstructionType.OBSERVE: 0.05,
        CohInstructionType.INFER: 0.15,
        CohInstructionType.RETRIEVE: 0.1,
        CohInstructionType.REPAIR: 0.2,
        CohInstructionType.BRANCH: 0.15,
        CohInstructionType.PLAN: 0.25,
        CohInstructionType.ACT_PREPARE: 0.2,
        CohInstructionType.ACT_COMMIT: 0.3,
    }
    
    def parse(self, raw_proposal: Dict[str, Any]) -> CohInstruction:
        """
        Parse raw proposal dict into CohInstruction.
        
        Args:
            raw_proposal: Dict with keys "intent", "parameters", optional "prerequisites"
            
        Returns:
            CohInstruction with computed cost/defect
            
        Raises:
            ValueError: If intent is unknown or parameters invalid
        """
        intent_str = raw_proposal.get("intent", "").upper()
        try:
            intent = CohInstructionType(intent_str)
        except ValueError:
            raise ValueError(f"Unknown instruction intent: {intent_str}")
        
        parameters = raw_proposal.get("parameters", {})
        prerequisites = raw_proposal.get("prerequisites", [])
        
        # Compute cost with parameter-based adjustments
        cost = self._compute_cost(intent, parameters)
        
        # Compute defect with parameter-based adjustments
        defect = self._compute_defect(intent, parameters)
        
        return CohInstruction(
            intent=intent,
            parameters=parameters,
            cost_estimate=cost,
            defect_estimate=defect,
            prerequisites=prerequisites,
            raw_payload=raw_proposal,
        )
    
    def _compute_cost(self, intent: CohInstructionType, params: Dict) -> float:
        """Compute thermodynamic cost (σ) for instruction."""
        base = self.COST_BASELINES.get(intent, 0.0)
        
        # Parameter-based adjustments
        if intent == CohInstructionType.RETRIEVE:
            depth = params.get("depth", 1)
            base += 0.05 * depth  # Deeper retrieval = more cost
        elif intent == CohInstructionType.PLAN:
            horizon = params.get("horizon", 5)
            base += 0.02 * horizon  # Longer horizon = more cost
        elif intent == CohInstructionType.OBSERVE:
            targets = params.get("targets", 1)
            base += 0.03 * (targets - 1)  # More targets = more cost
            
        return base
    
    def _compute_defect(self, intent: CohInstructionType, params: Dict) -> float:
        """Compute uncertainty (κ) for instruction."""
        base = self.DEFECT_BASELINES.get(intent, 0.0)
        
        # Parameter-based adjustments
        if intent == CohInstructionType.INFER:
            confidence = params.get("confidence", 0.5)
            base += 0.1 * (1 - confidence)  # Lower confidence = higher defect
        elif intent == CohInstructionType.BRANCH:
            n_branches = params.get("n_branches", 2)
            base += 0.05 * (n_branches - 1)
            
        return base
    
    def validate(self, instruction: CohInstruction) -> ValidationResult:
        """
        Validate instruction semantics.
        
        Checks:
        - Intent is valid
        - Required parameters present
        - Parameter types correct
        - Prerequisites are valid references
        """
        errors = []
        warnings = []
        
        # Check required parameters per intent
        required = self._get_required_params(instruction.intent)
        for param in required:
            if param not in instruction.parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Validate parameter types
        param_types = self._get_param_types(instruction.intent)
        for param, expected_type in param_types.items():
            if param in instruction.parameters:
                actual = instruction.parameters[param]
                if not isinstance(actual, expected_type):
                    warnings.append(
                        f"Parameter '{param}' expected {expected_type.__name__}, "
                        f"got {type(actual).__name__}"
                    )
        
        # Check for circular dependencies
        if instruction.intent in instruction.prerequisites:
            errors.append("Instruction cannot be its own prerequisite")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def _get_required_params(self, intent: CohInstructionType) -> List[str]:
        """Return required parameters for each intent."""
        return {
            CohInstructionType.RETRIEVE: ["query"],
            CohInstructionType.PLAN: ["goal"],
            CohInstructionType.BRANCH: ["policy_id"],
        }.get(intent, [])
    
    def _get_param_types(self, intent: CohInstructionType) -> Dict[str, type]:
        """Return expected parameter types."""
        return {
            CohInstructionType.RETRIEVE: {"query": str, "depth": int},
            CohInstructionType.PLAN: {"goal": str, "horizon": int},
            CohInstructionType.BRANCH: {"policy_id": str, "n_branches": int},
        }.get(intent, {})
    
    def normalize(self, instruction: CohInstruction) -> CohInstruction:
        """
        Normalize to canonical form.
        
        - Lowercase string parameters
        - Sort dict keys
        - Default missing optional params
        """
        normalized_params = {}
        
        for key, value in instruction.parameters.items():
            key_lower = key.lower()
            
            if isinstance(value, str):
                normalized_params[key_lower] = value.lower()
            elif isinstance(value, dict):
                normalized_params[key_lower] = self._normalize_dict(value)
            elif isinstance(value, list):
                normalized_params[key_lower] = [
                    v.lower() if isinstance(v, str) else v
                    for v in value
                ]
            else:
                normalized_params[key_lower] = value
        
        return CohInstruction(
            intent=instruction.intent,
            parameters=normalized_params,
            cost_estimate=instruction.cost_estimate,
            defect_estimate=instruction.defect_estimate,
            prerequisites=sorted(instruction.prerequisites),
            raw_payload=instruction.raw_payload,
        )
    
    def _normalize_dict(self, d: Dict) -> Dict:
        """Recursively normalize dict keys."""
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k.lower()] = self._normalize_dict(v)
            elif isinstance(v, str):
                result[k.lower()] = v.lower()
            else:
                result[k.lower()] = v
        return result
```

### 1.8: TransitionProposal Converter

```python
from gmos.kernel.mediator import TransitionOpcode

def map_intent_to_opcode(intent: CohInstructionType) -> TransitionOpcode:
    """Map CohInstructionType to TransitionOpcode."""
    mapping = {
        CohInstructionType.NOOP: TransitionOpcode.NOOP,
        CohInstructionType.OBSERVE: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.INFER: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.RETRIEVE: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.REPAIR: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.BRANCH: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.PLAN: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.ACT_PREPARE: TransitionOpcode.STATE_UPDATE,
        CohInstructionType.ACT_COMMIT: TransitionOpcode.STATE_UPDATE,
    }
    return mapping.get(intent, TransitionOpcode.NOOP)

def to_transition_proposal(instruction: CohInstruction) -> TransitionProposal:
    """Convert CohInstruction to kernel TransitionProposal."""
    return TransitionProposal(
        opcode=map_intent_to_opcode(instruction.intent),
        cost=instruction.cost_estimate,
        defect=instruction.defect_estimate,
        new_state=instruction.parameters.get("new_state"),
        metadata={
            "coh_instruction": instruction.intent.value,
            "raw_payload": instruction.raw_payload,
            "parameters": instruction.parameters,
        }
    )
```

### 1.9: CohILEvaluator Facade Class

For convenient use, wrap parser in a facade:

```python
class CohILEvaluator:
    """
    Main interface for Coh-IL evaluation.
    
    Usage:
        evaluator = CohILEvaluator()
        raw = {"intent": "OBSERVE", "parameters": {"target": "memory"}}
        
        # Parse and validate in one step
        result = evaluator.evaluate(raw)
        
        if result.is_valid:
            proposal = result.to_proposal()
        else:
            print(result.errors)
    """
    
    def __init__(self, strict: bool = False):
        self.parser = CohILParser()
        self.strict = strict
    
    def evaluate(self, raw_proposal: Dict[str, Any]) -> "EvaluationResult":
        """
        Full evaluation: parse + validate + normalize.
        
        Args:
            raw_proposal: Raw dict from agent
            
        Returns:
            EvaluationResult with instruction, validation, and proposal
        """
        # Parse
        instruction = self.parser.parse(raw_proposal)
        
        # Validate
        validation = self.parser.validate(instruction)
        
        # Normalize
        normalized = self.parser.normalize(instruction)
        
        return EvaluationResult(
            instruction=normalized,
            validation=validation,
            to_proposal=lambda: to_transition_proposal(normalized),
        )

@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    instruction: CohInstruction
    validation: ValidationResult
    to_proposal: Callable[[], TransitionProposal]
    
    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid
    
    @property
    def errors(self) -> List[str]:
        return self.validation.errors
    
    @property
    def warnings(self) -> List[str]:
        return self.validation.warnings
```
```

---

## Phase 2: Mediator Integration

### 2.1-2.3: KernelMediator Changes

**File**: `gmos/src/gmos/kernel/mediator.py`

Insert CohILEvaluator into the `_tick` flow:

```python
# Current flow:
# 1. scheduler.next() → process
# 2. router.spend(ADMIN_TICK_COST)
# 3. process.policy_propose(event) → TransitionProposal  ← CHANGE HERE
# 4. verifier.verify() → TransitionDecision
# 5. router.spend(proposal.cost)
# 6. process.apply_verified_proposal()
# 7. receipt_engine.emit()

# New flow:
# 1. scheduler.next() → process
# 2. router.spend(ADMIN_TICK_COST)
# 3. process.policy_propose(event) → raw proposal (dict)
# 3a. evaluator.parse(raw_proposal) → CohInstruction     ← NEW
# 3b. evaluator.validate(coh_instruction) → ValidationResult
# 3c. evaluator.to_transition_proposal() → TransitionProposal
# 4. verifier.verify() → TransitionDecision
# ...
```

---

## Phase 3: CharacterShell Integration

### 3.1: CharacterShell Module Analysis

The `character_shell.py` provides these key components:

| Component | Purpose |
|-----------|---------|
| `CharacterState` | Dataclass with χ parameters (chi_courage, chi_discipline, etc.) |
| `EpistemicThresholds` | Base thresholds for v1-v4 epistemic shell |
| `ModulatedThresholds` | Character-modulated thresholds (Θ_χ = M_χ(Θ_0)) |
| `compute_modulated_thresholds(base, chi)` | Applies character modulation formula |
| `update_character(current, ...)` | Character drift under experience |

**Pre-built Character Profiles** (in CharacterState):
- `create_scientist()`: chi_discipline=0.8, chi_laziness=0.2
- `create_warrior()`: chi_courage=0.9, chi_restraint=0.3
- `create_explorer()`: chi_curiosity=0.9, chi_courage=0.7
- `create_diplomat()`: chi_restraint=0.8, chi_discipline=0.7

### 3.2: Import CharacterShell

**File**: `gmos/src/gmos/agents/gmi/hosted_agent.py`

Current state (line 107-111):
```python
# GMI-specific components
self.potential = create_potential(**config.potential_config)
self.policy_selector = PolicySelector(**config.policy_config)
self.affective_budget = AffectiveBudgetManager(**config.affect_config)
self.affective_state = AffectiveCognitiveState()
```

Required addition:
```python
from gmos.agents.gmi.character_shell import (
    CharacterState,
    EpistemicThresholds,
    ModulatedThresholds,
    compute_modulated_thresholds,
)

# Add after affective_state initialization
self.character_state = CharacterState(
    chi_courage=config.character_config.get("chi_courage", 0.5),
    chi_discipline=config.character_config.get("chi_discipline", 0.5),
    chi_patience=config.character_config.get("chi_patience", 0.5),
    chi_curiosity=config.character_config.get("chi_curiosity", 0.5),
    chi_restraint=config.character_config.get("chi_restraint", 0.5),
    chi_persistence=config.character_config.get("chi_persistence", 0.5),
    chi_laziness=config.character_config.get("chi_laziness", 0.3),
    chi_humility=config.character_config.get("chi_humility", 0.5),
)

# Base epistemic thresholds
self.base_thresholds = EpistemicThresholds()
```

### 3.3: Integrate Tension Law Residuals

The `HostedGMIAgent.step()` method (around line 150) must:

1. Compute residual vector from tension_law
2. Apply character modulation
3. Use modulated thresholds in proposal generation

**Step 3.3a: Add imports**
```python
from gmos.agents.gmi.tension_law import ResidualVector, compute_tension_residuals
```

**Step 3.3b: Add state variables**
```python
# Add to __init__
self._residual_vector: Optional[ResidualVector] = None
self._modulated_thresholds: Optional[ModulatedThresholds] = None
```

**Step 3.3c: Modify step() method**
```python
def step(self, sensory_input=None):
    # ... existing state retrieval (lines 167-179) ...
    
    # NEW: Compute tension residuals (after line 179)
    self._residual_vector = compute_tension_residuals(
        x=x,
        b=b,
        sensory_input=sensory_input,
        memory_state=self._memory_state,
        goal_state=self._goal_state,
    )
    
    # NEW: Get character-modulated thresholds
    self._modulated_thresholds = compute_modulated_thresholds(
        self.base_thresholds,
        self.character_state
    )
    
    # Continue with existing proposal generation...
```

### 3.4: χ Parameter Wiring

The `compute_modulated_thresholds()` function (character_shell.py lines 211-294) applies these formulas:

| χ Parameter | Effect Formula | Impact on Proposals |
|-------------|----------------|-------------------|
| `chi_humility` | λ_collapse × (1 + 0.5χ) | Higher = resist premature collapse |
| `chi_courage` | τ_frag + (0.3χ - 0.2χ_restraint) | Higher = tolerate more ambiguity |
| `chi_laziness` | τ_refresh × (1 + 0.5χ - 0.4χ_disc) | Higher = use current rep longer |
| `chi_discipline` | λ_overreach × (1 + 0.5χ + 0.3χ_hum) | Higher = pay more for accuracy |
| `chi_curiosity` | τ_epi × (1 - 0.5χ + 0.3χ_laz) | Higher = ask more often |
| `chi_restraint` | τ_corr × (1 + 0.5χ + 0.3χ_hum - 0.3χ_courage) | Higher = require more corroboration |

**Proposal Generation Integration** (new method in HostedGMIAgent):
```python
def _generate_proposal_with_character(
    self,
    residuals: ResidualVector,
    thresholds: ModulatedThresholds
) -> TransitionProposal:
    """
    Generate proposal using character-modulated thresholds.
    
    The character affects:
    - Which actions are considered viable
    - Cost tolerance for pointer preservation
    - Defect acceptance for speed
    """
    # Use tau_refresh threshold to decide if we need new representatives
    if residuals.mem.sum() > thresholds.tau_refresh:
        # High discipline: refresh now; high laziness: defer
        opcode = TransitionOpcode.STATE_UPDATE
    
    # Use tau_corr for corroboration requirements
    if residuals.obs.sum() > thresholds.tau_corr:
        # High restraint: require more evidence before acting
    
    # Use lambda weights for cost/defect tradeoffs
    cost_factor = thresholds.lambda_overreach  # Discipline effect
    defect_factor = 1.0 - thresholds.lambda_shock  # Shock effect
    
    return TransitionProposal(
        opcode=opcode,
        cost=base_cost * cost_factor,
        defect=base_defect * defect_factor,
        # ...
    )
```

### 3.5: Character Drift Under Experience

After each action, update character based on outcomes (add to step() result handling):
```python
def _update_character_from_result(self, result: Dict[str, Any]):
    """Update character state based on action outcomes."""
    self.character_state = update_character(
        current=self.character_state,
        action_taken=result.get("action_taken", False),
        action_successful=result.get("success", False),
        action_value=result.get("value", 0.0),
        pressure_input=result.get("pressure", 0.0),
        shock_received=result.get("shock", False),
    )
```

### 3.6: AgentConfig Extension

**File**: `gmos/src/gmos/agents/gmi/hosted_agent.py` (line 50-61)

Add character configuration to AgentConfig:
```python
@dataclass
class AgentConfig:
    # ... existing fields ...
    
    # NEW: Character configuration
    character_config: Dict[str, float] = field(default_factory=lambda: {
        "chi_courage": 0.5,
        "chi_discipline": 0.5,
        "chi_patience": 0.5,
        "chi_curiosity": 0.5,
        "chi_restraint": 0.5,
        "chi_persistence": 0.5,
        "chi_laziness": 0.3,
        "chi_humility": 0.5,
    })
```

**Preset options** (can be used in config):
```python
# Usage:
config = AgentConfig(
    process_id="gmi-1",
    character_config=CharacterState.create_scientist().to_dict(),  # Or .create_warrior(), etc.
)
```

---

## Phase 4: Testing

### 4.1: CohILEvaluator Unit Tests

**File**: `gmos/tests/kernel/test_cohil_evaluator.py`

```python
def test_parser_parses_valid_instruction():
    """Parser correctly extracts intent and parameters."""
    parser = CohILParser()
    raw = {"intent": "OBSERVE", "parameters": {"target": "memory"}}
    instruction = parser.parse(raw)
    assert instruction.intent == CohInstructionType.OBSERVE
    assert instruction.cost_estimate > 0

def test_cost_calculation_respects_baselines():
    """Each instruction type has minimum cost baseline."""
    parser = CohILParser()
    for intent, baseline in COST_BASELINES.items():
        raw = {"intent": intent.value, "parameters": {}}
        instruction = parser.parse(raw)
        assert instruction.cost_estimate >= baseline

def test_validate_rejects_invalid_intent():
    """Validation catches unknown intents."""
    parser = CohILParser()
    raw = {"intent": "INVALID_OP", "parameters": {}}
    result = parser.validate(parser.parse(raw))
    assert not result.is_valid

def test_normalize_standardizes_parameters():
    """Normalization produces canonical form."""
    parser = CohILParser()
    raw = {"intent": "OBSERVE", "parameters": {"Target": "MEMORY", "depth": 3}}
    instruction = parser.parse(raw)
    normalized = parser.normalize(instruction)
    assert normalized.parameters["target"] == "memory"
```

### 4.2: Mediator Integration Test

**File**: `gmos/tests/kernel/test_cohil_mediator_integration.py`

```python
def test_evaluator_in_flow():
    """Coh-IL evaluator correctly parses before verifier."""
    mediator = create_kernel_mediator()
    
    # Register a process that submits raw dict proposals
    process = MockProcess(raw_proposals=[
        {"intent": "OBSERVE", "parameters": {"target": "memory"}},
        {"intent": "PLAN", "parameters": {"horizon": 5}},
    ])
    mediator.register_process("test-proc", process)
    
    # Execute tick
    result = mediator.tick()
    
    # Verify evaluator processed the instruction
    assert result.proposal is not None
    assert result.proposal.metadata.get("coh_instruction") == "observe"
    
    # Verify receipt includes instruction lineage
    assert result.receipt.metadata.get("instruction_type") == "observe"
```

### 4.3: CharacterShell Behavior Test

**File**: `gmos/tests/agents/gmi/test_character_shell_integration.py`

```python
def test_character_modulates_thresholds():
    """Different characters produce different modulated thresholds."""
    base = EpistemicThresholds(tau_refresh=0.5, tau_corr=0.6)
    
    # Scientist: high discipline, low laziness
    scientist = CharacterState.create_scientist()
    scientist_thresholds = compute_modulated_thresholds(base, scientist)
    
    # Explorer: high curiosity, high laziness  
    explorer = CharacterState.create_explorer()
    explorer_thresholds = compute_modulated_thresholds(base, explorer)
    
    # Scientist should have lower refresh threshold (more disciplined)
    assert scientist_thresholds.tau_refresh < explorer_thresholds.tau_refresh
    
    # Explorer should have lower EVI threshold (more curious)
    assert explorer_thresholds.tau_epistemic < scientist_thresholds.tau_epistemic

def test_character_drift_under_experience():
    """Character updates based on outcomes."""
    initial = CharacterState(chi_courage=0.5, chi_humility=0.5)
    
    # Repeated successful high-pressure actions
    updated = update_character(
        initial,
        action_taken=True,
        action_successful=True,
        action_value=1.0,
        pressure_input=0.8,
        shock_received=False,
    )
    
    # Courage should increase, humility should adjust
    assert updated.chi_courage > initial.chi_courage

def test_hosted_agent_uses_character():
    """HostedGMIAgent generates character-modulated proposals."""
    config = AgentConfig(
        process_id="test",
        character_config=CharacterState.create_warrior().to_dict(),
    )
    agent = HostedGMIAgent(config, state_host, budget_router, receipt_engine)
    
    result = agent.step()
    
    # Warrior character should produce proposals with specific properties
    # (based on chi_courage=0.9, chi_restraint=0.3)
    assert result is not None
```

---

## Phase 5: Backward Compatibility & Migration

### 5.1: Evaluator Passthrough Mode

The CohILEvaluator should support gradual migration by accepting both raw dicts and existing TransitionProposal objects:

```python
class CohILEvaluator:
    """
    Main interface for Coh-IL evaluation.
    
    Supports backward compatibility:
    - Raw dict: {"intent": "OBSERVE", "parameters": {...}}
    - Legacy TransitionProposal: Direct kernel proposal
    """
    
    def __init__(self, strict: bool = False, passthrough: bool = True):
        self.parser = CohILParser()
        self.strict = strict
        self.passthrough = passthrough  # NEW: Accept legacy proposals
    
    def evaluate(
        self, 
        raw_proposal: Union[Dict, TransitionProposal, CohInstruction]
    ) -> EvaluationResult:
        """
        Full evaluation with backward compatibility.
        
        Args:
            raw_proposal: Can be:
                - Dict: Parse as Coh-IL instruction
                - TransitionProposal: Wrap as-is (legacy mode)
                - CohInstruction: Validate and convert
        """
        # Case 1: Already a CohInstruction
        if isinstance(raw_proposal, CohInstruction):
            validation = self.parser.validate(raw_proposal)
            normalized = self.parser.normalize(raw_proposal)
            return EvaluationResult(
                instruction=normalized,
                validation=validation,
                to_proposal=lambda: to_transition_proposal(normalized),
            )
        
        # Case 2: Legacy TransitionProposal - passthrough
        if isinstance(raw_proposal, TransitionProposal):
            if not self.passthrough:
                raise ValueError("Passthrough disabled - must use Coh-IL format")
            
            # Wrap legacy proposal in minimal instruction
            instruction = CohInstruction(
                intent=CohInstructionType.NOOP,
                parameters={},
                cost_estimate=raw_proposal.cost,
                defect_estimate=raw_proposal.defect,
                raw_payload={"legacy": True, "metadata": raw_proposal.metadata},
            )
            return EvaluationResult(
                instruction=instruction,
                validation=ValidationResult(is_valid=True),
                to_proposal=lambda: raw_proposal,  # Return as-is
            )
        
        # Case 3: Raw dict - parse normally
        return self._evaluate_dict(raw_proposal)
```

### 5.2: Mediator Dual-Mode Support

The KernelMediator should support both modes:

```python
@dataclass
class MediatorConfig:
    # ... existing fields ...
    evaluator_enabled: bool = True  # NEW: Toggle Coh-IL evaluation
    evaluator_strict: bool = False  # NEW: Reject non-Coh-IL proposals

class KernelMediator:
    def __init__(self, config: MediatorConfig):
        # ... existing init ...
        self._evaluator = CohILEvaluator(strict=config.evaluator_strict) if config.evaluator_enabled else None
    
    def _tick(self) -> MediatorResult:
        # ... existing code ...
        
        # Get proposal (could be dict or TransitionProposal)
        raw_proposal = process.policy_propose(event)
        
        # NEW: Evaluate through Coh-IL if enabled
        if self._evaluator is not None:
            result = self._evaluator.evaluate(raw_proposal)
            if not result.is_valid:
                # Reject with validation errors
                return self._reject_proposal(
                    process_id=next_pid,
                    proposal=raw_proposal,
                    reason=f"Coh-IL validation failed: {result.errors}"
                )
            proposal = result.to_proposal()
        else:
            # Legacy mode: use raw proposal directly
            proposal = raw_proposal if isinstance(raw_proposal, TransitionProposal) else self._dict_to_proposal(raw_proposal)
        
        # Continue with verification...
```

### 5.3: Feature Flag Rollout

Recommended rollout sequence:

| Phase | Flag `evaluator_enabled` | Impact |
|-------|------------------------|--------|
| Initial | `False` | Legacy mode, no changes |
| Alpha | `True`, `passthrough=True` | Log all Coh-IL parsed proposals, don't reject |
| Beta | `True`, `passthrough=True`, `strict=False` | Accept both formats, warn on legacy |
| Release | `True`, `passthrough=False` | Require Coh-IL format |

### 5.4: Migration Checklist

```markdown
- [ ] Update all agents to emit Coh-IL dicts
- [ ] Update process.policy_propose() signatures
- [ ] Add deprecation warnings for TransitionProposal-only code
- [ ] Migrate tests to use Coh-IL format
- [ ] Remove passthrough code after full migration
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `gmos/src/gmos/kernel/cohil_evaluator.py` | CREATE |
| `gmos/src/gmos/kernel/mediator.py` | MODIFY - integrate evaluator |
| `gmos/src/gmos/kernel/__init__.py` | MODIFY - export CohILEvaluator |
| `gmos/src/gmos/agents/gmi/hosted_agent.py` | MODIFY - add CharacterShell |
| `gmos/tests/kernel/test_cohil_evaluator.py` | CREATE |
| `gmos/tests/agents/gmi/test_character_shell_integration.py` | CREATE |

---

## Implementation Notes

1. **Coh-IL Evaluator is blocking**: Phase 2 (mediator integration) depends on Phase 1
2. **CharacterShell depends on Evaluator**: Both affect proposal generation, but CharacterShell can be tested independently
3. **Backward Compatibility**: The evaluator should accept existing TransitionProposal objects for gradual migration
4. **Cost Bounds**: Enforce σ(composite) ≥ σ(r1) + σ(r2) for instruction sequences
5. **Feature Flags**: Use MediatorConfig to control rollout pace
