# NPE + GMI Integration Design

## Overview

This document describes how to integrate the Noetican Proposal Engine (NPE) with the Governed Metabolic Intelligence (GMI) runtime. The integration creates a "wild imagination + strict verifier" architecture where:

- **NPE**: Generates creative proposals (symbolic operators, beam search, coherence metrics)
- **GMI**: Verifies proposals against thermodynamic constraints and maintains ledger

## Current Architecture

### GMI Runtime
```
Proposal Pool → OplaxVerifier.check() → State Update → Receipt
                     ↓
              Memory Manifold
```

### NPE v2.0
```
ProposalContext → NPE.propose() → List[Tuple[Module, ProposalReceipt]]
```

## Integration Design

### 1. Shared Types

Create a unified proposal interface that both systems understand:

```python
# core/proposal.py
from dataclasses import dataclass
from typing import Protocol, List, Optional
import numpy as np

@dataclass
class GMIProposal:
    """Unified proposal format for GMI verification."""
    instruction: 'GMIInstruction'
    x_prime: np.ndarray  # Precomputed result (no re-evaluation)
    coherence: Optional[CoherenceMetrics] = None  # From NPE
    source: str = "npe"  # "npe" | "inference" | "explore"

@dataclass  
class GMIInstruction:
    """GMI instruction wrapper around NPE modules."""
    op_code: str  # Human-readable
    module: Optional[Any] = None  # NPE Module if from NPE
    sigma: float = 1.0  # Energy cost
    kappa: float = 1.0  # Defect budget
```

### 2. NPE → GMI Adapter

```python
# adapters/npe_adapter.py
from nsc.npe_v2_0 import NPEv2_0, ProposalContext
from core.proposal import GMIProposal, GMIInstruction
from core.state import Proposal
import numpy as np

class NPEAdapter:
    """Bridge between NPE proposals and GMI verification."""
    
    def __init__(self, npe: NPEv2_0):
        self.npe = npe
    
    def generate_proposals(self, state, context: ProposalContext) -> List[Proposal]:
        """Convert NPE proposals to GMI Proposals."""
        npe_proposals = self.npe.propose(context)
        
        gmi_proposals = []
        for module, receipt in npe_proposals:
            # Extract the transformation from NPE module
            x_prime = self._module_to_vector(module, state.x)
            
            # Convert coherence metrics to sigma/kappa bounds
            sigma, kappa = self._coherence_to_bounds(receipt.metrics)
            
            instr = GMIInstruction(
                op_code=module.module_id,
                module=module,
                sigma=sigma,
                kappa=kappa
            )
            
            gmi_proposals.append(Proposal(
                instruction=instr,
                x_prime=x_prime,
                coherence=receipt.metrics
            ))
        
        return gmi_proposals
    
    def _module_to_vector(self, module, current_x):
        """Extract vector transformation from NPE module."""
        # Implementation depends on NPE module structure
        return module.apply(current_x)
    
    def _coherence_to_bounds(self, metrics):
        """Convert NPE coherence metrics to thermodynamic bounds.
        
        r_phys (physics defect) → kappa (allowed defect)
        r_num (numerical stability) → sigma (energy cost)
        """
        sigma = 1.0 + metrics.r_num * 10  # Unstable = expensive
        kappa = metrics.r_phys * 5  # High defect = high allowance needed
        return sigma, kappa
```

### 3. GMI → NPE Feedback

Send verification results back to NPE for learning:

```python
class GMIToNPEFeedback:
    """Send GMI verification results to NPE for adaptation."""
    
    def __init__(self, npe: NPEv2_0):
        self.npe = npe
    
    def report_accept(self, proposal: Proposal, receipt):
        """Tell NPE a proposal was accepted."""
        self.npe.record_success(proposal.instruction.module, receipt)
    
    def report_reject(self, proposal: Proposal, receipt):
        """Tell NPE a proposal was rejected and why."""
        self.npe.record_failure(
            proposal.instruction.module,
            reason=receipt.message,
            residual=receipt.v_after - receipt.v_before
        )
```

### 4. Combined Runtime Loop

```python
# runtime/npe_gmi_loop.py
def run_npe_gmi(
    npe: NPEv2_0,
    initial_x,
    initial_budget,
    steps=20
):
    """Combined NPE + GMI execution loop."""
    
    # Setup
    memory = MemoryManifold(lambda_c=10.0)
    total_potential = make_total_potential(memory)
    verifier = OplaxVerifier(potential_fn=total_potential)
    
    npe_adapter = NPEAdapter(npe)
    feedback = GMIToNPEFeedback(npe)
    
    state = State(initial_x, initial_budget)
    
    for step in range(steps):
        # 1. Generate proposals from NPE
        context = ProposalContext(module_id_prefix=f"step_{step}")
        proposals = npe_adapter.generate_proposals(state, context)
        
        # 2. Add fallback proposals (INFER, etc.)
        proposals.extend(generate_fallback_proposals(state))
        
        # 3. Verify with GMI
        survivors = []
        for proposal in proposals:
            accepted, next_state, receipt = verifier.check(step, state, proposal)
            
            if accepted:
                survivors.append((proposal, next_state, receipt))
            else:
                # Send rejection feedback to NPE
                feedback.report_reject(proposal, receipt)
        
        # 4. Selection with efficiency + novelty + coherence
        if survivors:
            best = select_best(survivors)
            state = best[1]
            feedback.report_accept(best[0], best[2])
            
            print(f"Step {step}: ACCEPTED {best[0].instruction.op_code}")
        else:
            print(f"Step {step}: HALT - No valid proposals")
            break
    
    return state
```

### 5. Bidirectional Flow

```
┌─────────────────────────────────────────────────────────┐
│                    NPE (Imagination)                    │
│  ProposalContext → Beam Search → Coherence Metrics    │
└─────────────────────┬───────────────────────────────────┘
                      │ List[Module + Receipt]
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  NPEAdapter (Bridge)                    │
│  Module → Vector → sigma/kappa → GMIProposal          │
└─────────────────────┬───────────────────────────────────┘
                      │ Proposal with x_prime
                      ▼
┌─────────────────────────────────────────────────────────┐
│              GMI (Thermodynamic Verifier)                │
│  check() → Receipt → Accept/Reject/Halt               │
└─────────────────────┬───────────────────────────────────┘
                      │ Receipt + Feedback
                      ▼
┌─────────────────────────────────────────────────────────┐
│              GMIToNPEFeedback (Learning)                │
│  record_success/failure → NPE adapts                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
              (back to NPE for next iteration)
```

## Key Design Decisions

### 1. Precomputed Proposals
NPE generates proposals with precomputed `x_prime`. GMI verifier uses this directly without re-evaluation, ensuring:
- Deterministic verification
- No stochastic mismatch
- Efficiency

### 2. Metric Translation
NPE coherence metrics → GMI thermodynamic bounds:
- `r_phys` (physics defect) → `kappa` (allowed defect)
- `r_num` (numerical) → `sigma` (energy cost)
- `r_cons` (constraint) → budget impact

### 3. Feedback Loop
Rejected proposals carry detailed receipts back to NPE, enabling:
- NPE learns which proposals fail thermodynamic checks
- Improves future proposal quality
- Creates closed-loop learning

### 4. Fallback Proposals
NPE may not always produce valid proposals. Keep fallback (INFER, EXPLORE) for robustness.

## Implementation Priority

1. **Phase 1**: Basic adapter (NPE → GMI)
2. **Phase 2**: Feedback loop (GMI → NPE)
3. **Phase 3**: Metric translation tuning
4. **Phase 4**: Full integration with beam search

## Testing Strategy

```python
# tests/test_npe_integration.py

def test_npe_adapter_creates_proposals():
    """Test adapter converts NPE proposals to GMI format."""
    npe = NPEv2_0()
    adapter = NPEAdapter(npe)
    
    ctx = ProposalContext(module_id_prefix="test")
    proposals = adapter.generate_proposals(state, ctx)
    
    assert all(isinstance(p, Proposal) for p in proposals)
    assert all(p.x_prime is not None for p in proposals)

def test_feedback_records_rejection():
    """Test rejection feedback is sent to NPE."""
    npe = NPEv2_0()
    feedback = GMIToNPEFeedback(npe)
    
    # ... verify NPE receives rejection info
```

## Summary

This integration creates a powerful "wild imagination + strict governance" loop:

- **NPE** provides creative, beam-searched proposals with coherence metrics
- **GMI** provides thermodynamic verification and ledger proof
- **Feedback** enables continuous learning

The key insight is that both systems speak "proposal" - we just need a thin adapter layer to translate between them.
