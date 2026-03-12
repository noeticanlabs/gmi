"""
Coh-IL Evaluator for GM-OS Kernel.

This module provides the Coh-IL (Coh Instruction Language) evaluator - the
"algebra of intents" that parses, validates, and normalizes instruction
payloads from GMI agents before they reach the verifier.

The evaluator ensures thermodynamic honesty by:
1. Parsing raw dict proposals into structured CohInstruction objects
2. Computing honest cost (σ) and defect (κ) estimates
3. Validating semantic correctness
4. Normalizing parameters to canonical forms
5. Converting to TransitionProposal for the verifier

Per GM-OS Canon Spec: The kernel must not blindly trust agent-provided
cost/defect values - they must be independently computed from the
instruction semantics.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Callable
import copy


# ============================================================================
# Core Types
# ============================================================================

class CohInstructionType(Enum):
    """
    Core instruction types per Coh-IL specification.
    
    Each instruction type has associated thermodynamic costs that are
    computed independently of what the agent claims.
    """
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
    
    This is the canonical representation of an agent's intent after
    parsing and validation. All cost/defect values are computed
    from the instruction semantics, not from agent claims.
    
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
    """
    Result of instruction validation.
    
    Contains validation status, errors, and warnings.
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class EvaluationResult:
    """
    Complete evaluation result from CohILEvaluator.
    
    Contains the parsed instruction, validation result, and a callable
    to convert to TransitionProposal.
    """
    instruction: CohInstruction
    validation: ValidationResult
    to_proposal: Callable[['CohILEvaluator'], 'TransitionProposal']
    
    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid
    
    @property
    def errors(self) -> List[str]:
        return self.validation.errors
    
    @property
    def warnings(self) -> List[str]:
        return self.validation.warnings


# ============================================================================
# Cost and Defect Baselines
# ============================================================================

# Per instruction type cost baseline (minimum thermodynamic cost)
COST_BASELINES = {
    CohInstructionType.NOOP: 0.0,
    CohInstructionType.OBSERVE: 0.1,     # Sensory acquisition cost
    CohInstructionType.INFER: 0.2,        # Memory inference cost
    CohInstructionType.RETRIEVE: 0.15,    # Memory retrieval cost
    CohInstructionType.REPAIR: 0.3,       # Reconciliation cost
    CohInstructionType.BRANCH: 0.25,      # Policy branching cost
    CohInstructionType.PLAN: 0.35,        # Planning cost
    CohInstructionType.ACT_PREPARE: 0.4,  # Preparation cost
    CohInstructionType.ACT_COMMIT: 0.5,   # External action cost
}

# Per instruction type defect baseline (minimum uncertainty)
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


# ============================================================================
# Parser Implementation
# ============================================================================

class CohILParser:
    """
    Parses raw proposals into structured Coh-IL instructions.
    
    Responsibilities:
    1. Validate instruction syntax
    2. Normalize parameters to canonical forms
    3. Compute cost/defect estimates based on instruction semantics
    4. Build dependency graph
    
    The key principle is "thermodynamic honesty" - cost and defect
    are computed from the instruction type and parameters, not from
    what the agent claims.
    """
    
    def __init__(self):
        self.cost_baselines = COST_BASELINES
        self.defect_baselines = DEFECT_BASELINES
    
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
        # Extract intent
        intent_str = raw_proposal.get("intent", "").upper()
        if not intent_str:
            raise ValueError("Missing required field: intent")
        
        try:
            intent = CohInstructionType(intent_str)
        except ValueError:
            raise ValueError(f"Unknown instruction intent: {intent_str}")
        
        # Extract parameters (default to empty dict)
        parameters = raw_proposal.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError(f"parameters must be a dict, got {type(parameters)}")
        
        # Extract prerequisites
        prerequisites = raw_proposal.get("prerequisites", [])
        if not isinstance(prerequisites, list):
            raise ValueError(f"prerequisites must be a list, got {type(prerequisites)}")
        
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
        """
        Compute thermodynamic cost (σ) for instruction.
        
        Cost is computed from instruction semantics, not from agent claims.
        Base cost is adjusted by parameters that affect computational work.
        """
        base = self.cost_baselines.get(intent, 0.0)
        
        # Parameter-based cost adjustments
        if intent == CohInstructionType.RETRIEVE:
            depth = params.get("depth", 1)
            base += 0.05 * max(0, depth - 1)  # Deeper retrieval = more cost
        elif intent == CohInstructionType.PLAN:
            horizon = params.get("horizon", 5)
            base += 0.02 * max(0, horizon - 5)  # Longer horizon = more cost
        elif intent == CohInstructionType.OBSERVE:
            targets = params.get("targets", 1)
            base += 0.03 * max(0, targets - 1)  # More targets = more cost
        elif intent == CohInstructionType.BRANCH:
            n_branches = params.get("n_branches", 2)
            base += 0.05 * max(0, n_branches - 2)  # More branches = more cost
        elif intent == CohInstructionType.INFER:
            confidence = params.get("confidence", 0.5)
            # Lower confidence = more computational work to resolve
            base += 0.1 * max(0, 0.5 - confidence)
            
        return base
    
    def _compute_defect(self, intent: CohInstructionType, params: Dict) -> float:
        """
        Compute uncertainty (κ) for instruction.
        
        Defect represents the epistemic uncertainty associated with
        the instruction outcome.
        """
        base = self.defect_baselines.get(intent, 0.0)
        
        # Parameter-based defect adjustments
        if intent == CohInstructionType.INFER:
            confidence = params.get("confidence", 0.5)
            base += 0.1 * max(0, 1 - confidence)  # Lower confidence = higher defect
        elif intent == CohInstructionType.BRANCH:
            n_branches = params.get("n_branches", 2)
            base += 0.05 * max(0, n_branches - 2)  # More branches = more uncertainty
        elif intent == CohInstructionType.PLAN:
            horizon = params.get("horizon", 5)
            base += 0.02 * max(0, horizon - 5)  # Longer horizon = more uncertainty
            
        return base
    
    def validate(self, instruction: CohInstruction) -> ValidationResult:
        """
        Validate instruction semantics.
        
        Checks:
        - Intent is valid
        - Required parameters present
        - Parameter types correct
        - Prerequisites are valid references
        
        Args:
            instruction: Parsed CohInstruction to validate
            
        Returns:
            ValidationResult with errors and warnings
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
        if instruction.intent.value in instruction.prerequisites:
            errors.append("Instruction cannot be its own prerequisite")
        
        # Validate prerequisites format
        for prereq in instruction.prerequisites:
            if not isinstance(prereq, str):
                errors.append(f"Prerequisite must be string, got {type(prereq)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def _get_required_params(self, intent: CohInstructionType) -> List[str]:
        """Return required parameters for each intent type."""
        return {
            CohInstructionType.RETRIEVE: ["query"],
            CohInstructionType.PLAN: ["goal"],
            CohInstructionType.BRANCH: ["policy_id"],
        }.get(intent, [])
    
    def _get_param_types(self, intent: CohInstructionType) -> Dict[str, type]:
        """Return expected parameter types for validation."""
        return {
            CohInstructionType.RETRIEVE: {"query": str, "depth": int},
            CohInstructionType.PLAN: {"goal": str, "horizon": int},
            CohInstructionType.BRANCH: {"policy_id": str, "n_branches": int},
            CohInstructionType.OBSERVE: {"targets": int},
        }.get(intent, {})
    
    def normalize(self, instruction: CohInstruction) -> CohInstruction:
        """
        Normalize instruction to canonical form.
        
        - Lowercase string parameters
        - Sort dict keys
        - Default missing optional params
        
        Args:
            instruction: Instruction to normalize
            
        Returns:
            New CohInstruction in canonical form
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
        """Recursively normalize dict keys to lowercase."""
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k.lower()] = self._normalize_dict(v)
            elif isinstance(v, str):
                result[k.lower()] = v.lower()
            else:
                result[k.lower()] = v
        return result


# ============================================================================
# TransitionProposal Converter
# ============================================================================

# Forward declaration for type hints
class TransitionProposal:
    """Placeholder for kernel TransitionProposal - imported lazily."""
    pass


def map_intent_to_opcode(intent: CohInstructionType) -> str:
    """
    Map CohInstructionType to kernel TransitionOpcode string.
    
    Most Coh-IL instructions result in STATE_UPDATE, which is the
    general case for cognitive operations.
    """
    mapping = {
        CohInstructionType.NOOP: "NOOP",
        CohInstructionType.OBSERVE: "STATE_UPDATE",
        CohInstructionType.INFER: "STATE_UPDATE",
        CohInstructionType.RETRIEVE: "STATE_UPDATE",
        CohInstructionType.REPAIR: "STATE_UPDATE",
        CohInstructionType.BRANCH: "STATE_UPDATE",
        CohInstructionType.PLAN: "STATE_UPDATE",
        CohInstructionType.ACT_PREPARE: "STATE_UPDATE",
        CohInstructionType.ACT_COMMIT: "STATE_UPDATE",
    }
    return mapping.get(intent, "NOOP")


def to_transition_proposal(instruction: CohInstruction) -> 'TransitionProposal':
    """
    Convert CohInstruction to kernel TransitionProposal.
    
    This is the bridge between the Coh-IL layer and the kernel layer.
    The cost and defect are the honestly-computed values from parsing.
    
    Args:
        instruction: Parsed and validated CohInstruction
        
    Returns:
        TransitionProposal for the kernel verifier
    """
    # Import here to avoid circular dependency
    from gmos.kernel.mediator import TransitionProposal as TP, TransitionOpcode
    
    opcode = TransitionOpcode[map_intent_to_opcode(instruction.intent)]
    
    return TP(
        opcode=opcode,
        cost=instruction.cost_estimate,
        defect=instruction.defect_estimate,
        new_state=instruction.parameters.get("new_state"),
        metadata={
            "coh_instruction": instruction.intent.value,
            "raw_payload": instruction.raw_payload,
            "parameters": instruction.parameters,
            "cohil_validated": True,
        }
    )


# ============================================================================
# Main Evaluator Facade
# ============================================================================

class CohILEvaluator:
    """
    Main interface for Coh-IL evaluation.
    
    This facade provides a convenient interface for evaluating proposals
    through the full Coh-IL pipeline: parse → validate → normalize → convert.
    
    Usage:
        evaluator = CohILEvaluator()
        raw = {"intent": "OBSERVE", "parameters": {"target": "memory"}}
        
        # Parse and validate in one step
        result = evaluator.evaluate(raw)
        
        if result.is_valid:
            proposal = evaluator.to_proposal(result.instruction)
        else:
            print(result.errors)
    
    The evaluator also supports backward compatibility mode where it can
    accept legacy TransitionProposal objects for gradual migration.
    """
    
    def __init__(self, strict: bool = False, passthrough: bool = True):
        """
        Initialize the evaluator.
        
        Args:
            strict: If True, raise on validation errors. If False, allow warnings.
            passthrough: If True, accept legacy TransitionProposal objects directly.
        """
        self.parser = CohILParser()
        self.strict = strict
        self.passthrough = passthrough
    
    def evaluate(
        self, 
        raw_proposal: Union[Dict[str, Any], CohInstruction, 'TransitionProposal']
    ) -> EvaluationResult:
        """
        Full evaluation: parse + validate + normalize.
        
        Supports multiple input types for backward compatibility:
        - Dict: Parse as Coh-IL instruction
        - CohInstruction: Validate and convert
        - TransitionProposal: Wrap as-is (if passthrough=True)
        
        Args:
            raw_proposal: Input in any supported format
            
        Returns:
            EvaluationResult with instruction, validation, and proposal converter
            
        Raises:
            ValueError: If format is invalid or passthrough is disabled
        """
        # Case 1: Already a CohInstruction - validate and return
        if isinstance(raw_proposal, CohInstruction):
            validation = self.parser.validate(raw_proposal)
            normalized = self.parser.normalize(raw_proposal)
            return EvaluationResult(
                instruction=normalized,
                validation=validation,
                to_proposal=lambda instr=normalized: to_transition_proposal(instr),
            )
        
        # Case 2: Legacy TransitionProposal - passthrough mode
        if isinstance(raw_proposal, TransitionProposal):
            if not self.passthrough:
                raise ValueError(
                    "Passthrough disabled - must use Coh-IL format. "
                    "Pass raw dict or CohInstruction."
                )
            
            # Wrap legacy proposal in minimal instruction for compatibility
            instruction = CohInstruction(
                intent=CohInstructionType.NOOP,
                parameters={},
                cost_estimate=raw_proposal.cost,
                defect_estimate=raw_proposal.defect,
                raw_payload={
                    "legacy": True, 
                    "metadata": raw_proposal.metadata,
                },
            )
            return EvaluationResult(
                instruction=instruction,
                validation=ValidationResult(is_valid=True, warnings=["Legacy proposal - bypassing Coh-IL validation"]),
                to_proposal=lambda: raw_proposal,  # Return as-is
            )
        
        # Case 3: Raw dict - full parsing pipeline
        if isinstance(raw_proposal, dict):
            return self._evaluate_dict(raw_proposal)
        
        # Unknown type
        raise ValueError(f"Unknown proposal type: {type(raw_proposal)}")
    
    def _evaluate_dict(self, raw_proposal: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate a raw dict proposal through full pipeline.
        
        Args:
            raw_proposal: Dict with "intent", "parameters", etc.
            
        Returns:
            Complete EvaluationResult
        """
        try:
            # Parse
            instruction = self.parser.parse(raw_proposal)
            
            # Validate
            validation = self.parser.validate(instruction)
            
            # Check strict mode
            if self.strict and not validation.is_valid:
                raise ValueError(f"Validation failed: {validation.errors}")
            
            # Normalize
            normalized = self.parser.normalize(instruction)
            
            return EvaluationResult(
                instruction=normalized,
                validation=validation,
                to_proposal=lambda instr=normalized: to_transition_proposal(instr),
            )
            
        except ValueError as e:
            # Propagate parsing/validation errors
            return EvaluationResult(
                instruction=CohInstruction(
                    intent=CohInstructionType.NOOP,
                    raw_payload=raw_proposal,
                ),
                validation=ValidationResult(
                    is_valid=False,
                    errors=[str(e)],
                ),
                to_proposal=lambda: to_transition_proposal(CohInstruction(
                    intent=CohInstructionType.NOOP,
                    cost_estimate=0.0,
                    defect_estimate=0.0,
                )),
            )
    
    def to_proposal(self, instruction: CohInstruction) -> 'TransitionProposal':
        """
        Convert a CohInstruction to TransitionProposal.
        
        Args:
            instruction: Parsed and validated instruction
            
        Returns:
            TransitionProposal for the kernel
        """
        return to_transition_proposal(instruction)


# ============================================================================
# Factory Functions
# ============================================================================

def create_evaluator(
    strict: bool = False,
    passthrough: bool = True,
) -> CohILEvaluator:
    """
    Create a CohILEvaluator with standard configuration.
    
    Args:
        strict: Enable strict validation mode
        passthrough: Enable legacy proposal passthrough
        
    Returns:
        Configured CohILEvaluator instance
    """
    return CohILEvaluator(strict=strict, passthrough=passthrough)


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Core types
    'CohInstructionType',
    'CohInstruction', 
    'ValidationResult',
    'EvaluationResult',
    # Parser
    'CohILParser',
    # Evaluator
    'CohILEvaluator',
    'create_evaluator',
    # Converter
    'to_transition_proposal',
    'map_intent_to_opcode',
    # Constants
    'COST_BASELINES',
    'DEFECT_BASELINES',
]
