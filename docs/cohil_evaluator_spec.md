# Coh-IL Evaluator Design Specification

> **Status**: Design Draft  
> **Priority**: High  
> **Gap**: Nascent implementation

## Overview

Coh-IL (Coh Instruction Language) is the "algebra of intents" - a strictly parsed, normalized instruction language for GMI proposals. This document outlines the design for a complete Coh-IL evaluator.

## Current State

The notebooks call for:
- Strictly parsed instruction language
- Payload normalizer
- Structured Coh-IL objects for the verifier

**Current Gap**: The exact parser and payload normalizer is nascent. The verifier (`kernel/verifier.py`) currently accepts generic `Proposal` objects but lacks structured Coh-IL parsing.

## Design Requirements

### 1. Coh-IL Instruction Types

```python
class CohInstructionType(Enum):
    """Core instruction types per Coh-IL."""
    NOOP = "noop"                    # No operation
    OBSERVE = "observe"              # Sensory acquisition
    INFER = "infer"                  # Memory inference
    RETRIEVE = "retrieve"            # Memory retrieval
    REPAIR = "repair"                # Memory reconciliation
    BRANCH = "branch"                # Policy branching
    PLAN = "plan"                    # Planning
    ACT_PREPARE = "act_prepare"      # Action preparation
    ACT_COMMIT = "act_commit"        # External action commit
```

### 2. Instruction Payload Schema

Each instruction must have:
- `intent`: The instruction type
- `parameters`: Typed parameters
- `cost_estimate`: Computed sigma (σ)
- `defect_estimate`: Computed kappa (κ)
- `prerequisites`: List of required prior instructions

### 3. Parser Requirements

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
    
    def parse(self, raw_proposal: Dict[str, Any]) -> CohInstruction:
        """Parse raw proposal into CohInstruction."""
        ...
    
    def validate(self, instruction: CohInstruction) -> ValidationResult:
        """Validate instruction semantics."""
        ...
    
    def normalize(self, instruction: CohInstruction) -> CohInstruction:
        """Normalize to canonical form."""
        ...
```

### 4. Integration Points

| Component | Interface |
|-----------|------------|
| `OplaxVerifier` | Accept `CohInstruction` instead of generic `Proposal` |
| `Scheduler` | Queue instructions by type |
| `ReceiptEngine` | Record instruction lineage |

### 5. Oplax Algebra Integration

The parser must enforce:

```
# Metabolic Honesty
σ(composite) >= σ(r1) + σ(r2)

# Defect Monotonicity  
κ(composite) <= κ(r1) + κ(r2)
```

## Implementation Plan

### Phase 1: Core Types
- [ ] Define `CohInstruction` dataclass
- [ ] Define `CohInstructionType` enum
- [ ] Define `ValidationResult` type

### Phase 2: Parser
- [ ] Implement `CohILParser.parse()`
- [ ] Implement parameter normalization
- [ ] Implement validation rules

### Phase 3: Integration
- [ ] Update `OplaxVerifier` to accept CohInstruction
- [ ] Add instruction tracking to receipts

## Related Files

- [`gmos/src/gmos/kernel/verifier.py`](gmos/src/gmos/kernel/verifier.py) - Current verifier
- [`gmos/src/gmos/kernel/gmi_receipts.py`](gmos/src/gmos/kernel/gmi_receipts.py) - Receipt types

## Notes

This is a Tier 1 rigorous goal. The Python implementation should eventually be verifiable against Lean 4 formalization (`CohOplax`).
