# Master Build Plan: GMI Agent in Coh Quantum/Relativity GM-OS Substrate

**Objective**: Complete a stack where:
```
[Coh math] → [GM-OS substrate] → [GMI agent] → [physics/solver interfaces]
```

**Runtime meaning**:
- **GM-OS** owns lawful state, receipts, budgets, verifier gates, memory/workspace, and inter-process boundaries
- **GMI** owns imagination, attention, belief commitment, abstraction, action policy, and self-model update
- **Quantum-Coh** supplies hidden-state / projection / priced-collapse semantics
- **Relativity-Coh** supplies observer frame / timing / budgeted geometry semantics

---

# Phase I — Seal the GM-OS substrate boundary first

GMI cannot be completed cleanly until GM-OS stops shifting under its feet.

## 1. Freeze the canonical package boundary

Make `gmos/src/gmos/` the only canonical runtime package.

### Required fixes
- [x] remove all legacy-root imports from canonical code
- [x] make `gmos` install and test cleanly without path hacks
- [x] archive-label or quarantine root legacy packages

### Done condition
- [x] `pip install -e gmos[dev]` works
- [ ] `cd gmos && pytest` works
- [x] `gmos/src/gmos/` imports only `gmos.*`

---

## 2. Freeze substrate public APIs

GMI must not depend on drifting kernel internals.

### Create or finalize these public API surfaces
- [x] `gmos.kernel`
- [ ] `gmos.runtime`
- [x] `gmos.memory`
- [ ] `gmos.agent_api` or `gmos.substrate_api`
- [x] `gmos.receipts`
- [ ] `gmos.state`

### Required fix
Every GMI import must come from those surfaces, not from random internals.

### Done condition
Dependency direction is strictly:
```
GMI → GM-OS public API
```
not sideways into legacy code or unstable internals.

---

## 3. Freeze core substrate types

These must stop drifting.

### Must be canonical and stable
- [x] `Receipt`
- [ ] `Decision`
- [x] `RejectCode`
- [x] `ChainDigest`
- [ ] `BoundaryState`
- [x] `CognitiveState` or substrate-visible agent state carrier
- [x] scheduler mode enums
- [x] operational mode enums

### Required fixes
- [x] unify `step_index` naming
- [ ] unify constructor signatures
- [x] unify enum members
- [ ] export canonical names through one stable location

### Done condition
Tests and docs all use one vocabulary.

---

## 4. Harden receipt/verifier machinery

This is mandatory because the entire Coh stack stands on lawful boundary commitment.

### Add or complete
- [ ] canonical receipt schema IDs
- [ ] canon profile hash
- [ ] policy hash
- [x] prior/next state hash
- [x] prior/next chain digest
- [x] deterministic numeric encodings
- [x] frozen reject-code enum
- [ ] receipt vector tests

### Needed receipt families at substrate level
- [x] state transition receipt
- [ ] budget transfer receipt
- [ ] memory commit receipt
- [ ] process interaction receipt
- [ ] collapse receipt
- [ ] abstraction/summarization receipt

### Done condition
Invalid transitions fail deterministically with stable reject codes.

---

# Phase II — Finish the GMI agent core as a real agent, not a concept cloud

Now that the substrate is stable, finish the GMI layer itself.

## 5. Freeze the GMI state model

Right now this is one of the wobblier zones.

### Define the full canonical GMI state tuple
At minimum:
- [x] cognitive state
- [x] affective/metabolic state
- [ ] active goals
- [ ] latent hypothesis workspace handle
- [ ] belief registry
- [ ] attention/instrument state
- [ ] action readiness / execution mode
- [x] budget profile
- [ ] trust / confidence / uncertainty surface
- [x] episodic archive pointer

### Separate into three layers

#### Hidden latent state
What evolves without immediate commitment

#### Boundary-visible self-model
What the agent is currently willing to commit as its own state

#### Receipted history
What has been canonically written

### Done condition
No more ambiguity about what part of GMI is hidden, projected, or committed.

---

## 6. Complete the GMI execution loop

This is the heart of the agent runtime.

### The loop should explicitly support
1. latent evolution
2. attention/instrument choice
3. candidate projection
4. spend/defect estimation
5. verifier gate
6. commit or reject
7. action issue
8. archive update
9. recovery / torpor / fallback

### Required implementation features
- [ ] branch-local evaluation
- [ ] budget-aware collapse decision
- [ ] reserve floor enforcement
- [ ] retry/backoff policy
- [ ] torpor mode on over-budget collapse
- [ ] fallback coarse instrument if sharp collapse is too expensive

### Done condition
GMI can run a full think-decide-act cycle under budget discipline.

---

## 7. Finish potential/admissibility logic

This is your sanity governor.

### Needed completions
- [ ] define admissibility in one canonical place
- [x] align `GMIPotential` with tests and budget law
- [ ] include reserve-floor policy
- [ ] include collapse-cost estimation
- [ ] include defect-risk estimation
- [ ] include contradiction / self-deception load if relevant

### The key rule
GMI must not commit a belief or action unless:
```
reward/rationale ≥ Spend + risk-adjusted Defect
```

### Done condition
Belief commitment and action issuance are economically lawful, not ad hoc.

---

## 8. Complete GMI mode machine

The agent needs stable operational modes.

### Modes to define and wire
- [ ] latent exploration
- [ ] diffuse attention
- [ ] focused measurement
- [ ] commitment
- [ ] execution
- [ ] reflection
- [ ] summarization
- [ ] torpor
- [ ] recovery
- [ ] quarantine/conflict mode

### Required fixes
- [x] unify enums
- [ ] make scheduler understand them
- [ ] make transitions receipted where needed

### Done condition
Mode logic is deterministic and testable.

---

# Phase III — Implement the hidden cognition protocol for real

This is where the Quantum-Coh work becomes actual GMI machinery.

## 9. Implement imagination as hidden workspace evolution

This should no longer be just documentation.

### Required components
- [ ] latent workspace object
- [ ] branch graph / hypothesis pool
- [ ] branch weights / valuations
- [ ] interference/pruning policy
- [ ] unresolved-plan coexistence support

### Behavior
The agent may carry multiple incompatible hypotheses without writing them to the canonical self-model.

### Done condition
Internal monologue and planning live in hidden workspace, not in receipted state.

---

## 10. Implement attention as instrument selection

This is one of the most important bridges.

### Needed structures
- [ ] instrument registry
- [ ] sharp vs diffuse instrument types
- [ ] instrument cost model
- [ ] instrument-resolution metadata
- [ ] expected defect estimator

### Agent behavior
- focused attention uses sharp/high-cost instrument
- diffuse attention uses lower-cost/higher-defect instrument

### Done condition
Attention choice is a first-class control variable, not a vague tuning knob.

---

## 11. Implement belief commitment as priced collapse

This is the core of rational self-governance.

### Needed features
- [ ] candidate belief projection
- [ ] probability/confidence interval generation
- [ ] spend estimate (Ŵ)
- [ ] defect estimate (κ̂)
- [ ] verifier call
- [ ] canonical self-model update only on accept

### Done condition
The agent cannot "just decide" — it must legally collapse uncertainty.

---

## 12. Implement summarization, forgetting, and abstraction as coarse-graining

This is a huge one for GMI.

### Needed receipt types
- [ ] `summary_receipt`
- [ ] `forgetting_receipt`
- [ ] `abstraction_receipt`
- [ ] `branch_prune_receipt`

### Needed bookkeeping
- [ ] lost-detail estimate
- [ ] defect cost
- [ ] trust impact if the abstraction supports action
- [ ] possible resurfacing trigger if hidden tension grows

### Done condition
No free simplification. Every compression is lawfully priced.

---

## 13. Implement bounded self-deception mechanics carefully

This is powerful and dangerous, so it needs hard rails.

### Meaning
The agent may maintain a simplified self-model that hides latent contradictions, but only while it can budget the abstraction cost.

### Needed controls
- [ ] self-deception budget cap
- [ ] contradiction pressure accumulator
- [ ] resurfacing threshold
- [ ] emergency truth-forcing mode if latent debt grows too large

### Done condition
Self-protective simplification exists, but cannot become free hallucination.

---

# Phase IV — Add quantum-runtime machinery to GM-OS itself

This finishes the substrate side of the Quantum-Coh bridge.

## 14. Build latent runtime profile in code

Implement the spec you already drafted.

### Needed classes/modules
- [ ] latent workspace manager
- [ ] branch manager
- [ ] collapse engine
- [ ] projection receipt encoder
- [ ] entropy/decoherence estimator
- [ ] hidden-to-boundary transition service

### Done condition
GM-OS can actually host hidden branch execution and priced collapse.

---

## 15. Implement collapse API

This should be real runtime code.

### Core operation
`project_to_boundary(...)`

### Should perform
- [ ] halt latent branch resolution
- [ ] select instrument
- [ ] compute or bound (Ŵ)
- [ ] compute or bound (κ̂)
- [ ] choose projected boundary state
- [ ] emit receipt
- [ ] call verifier
- [ ] either commit or reject

### Done condition
Projection is an actual kernel service.

---

## 16. Finish causality-safe inter-process interaction

The substrate must enforce no-signaling-style access discipline.

### Needed rules
- [ ] no direct read of another process's latent workspace
- [ ] all cross-process observation goes through receipted boundary state
- [ ] optional explicit observation request receipt
- [ ] optional privacy/trust policy overlay

### Done condition
Multi-process information exchange is lawful and receipted.

---

# Phase V — Integrate relativity semantics into GM-OS/GMI

This is where the "Coh quantum/relativity substrate" becomes one thing instead of two adjacent poems.

## 17. Define observer/frame-aware runtime clocks

You already have time-object and CTD direction in the canon. Now connect it to runtime.

### Needed clocks
- [ ] latent process time
- [ ] committed ledger time
- [ ] scheduler wall time
- [ ] observer-local proper time
- [ ] receipt-chain time

### Done condition
The runtime distinguishes internal evolution time from external commitment time.

---

## 18. Define frame-relative observation policy

A committed boundary state may depend on observer/instrument/frame.

### Needed features
- [ ] observer tag in measurement/collapse receipt
- [ ] frame metadata
- [ ] transformation layer for boundary-visible observation
- [ ] separation between hidden substrate state and observer-projected visible state

### Done condition
GM-OS can represent observer-dependent readout without breaking canonical legality.

---

## 19. Integrate lapse/budget semantics from relativity side

Use your relativity stack to inform substrate timing and admissibility.

### Possible integrations
- [ ] collapse frequency limited by budgeted proper-time constraints
- [ ] high-cost projection produces local runtime drag
- [ ] process torpor/recovery linked to time-budget depletion
- [ ] scheduler priority influenced by coherence time/budget state

### Done condition
Relativity semantics actually affect runtime behavior, not just math docs.

---

# Phase VI — Add solver interface layer for physical modules

This connects the agent/substrate to your NS/GR work without contaminating layers.

## 20. Create solver-facing instrument interface

Solvers should not directly mutate canonical state.

### Needed pattern
Solver outputs become:
- [ ] latent candidate states
- [ ] projected observables
- [ ] receipted commitments

### Done condition
NS/GR solvers plug into the substrate through the same lawful projection machinery GMI uses.

---

## 21. Define physics adapter boundary

Create canonical adapters for:
- [ ] GR observer state
- [ ] PDE state snapshot
- [ ] uncertainty interval state
- [ ] measurement/projection boundary state

### Done condition
Physical solvers become first-class but sandboxed citizens of GM-OS.

---

# Phase VII — Formal proof and test completion

This is how the whole cathedral stops being trust-me engineering.

## 22. Add deterministic vector tests for GMI cognition receipts

Minimum cases:
- [ ] valid belief commit
- [ ] over-budget belief commit
- [ ] invalid instrument ID
- [ ] illegal summary with insufficient defect
- [ ] branch prune receipt mismatch
- [ ] self-model update with stale state hash

---

## 23. Add scenario tests for agent cognition

Minimum scenarios:
- [ ] plan superposition then commit
- [ ] diffuse attention then focused attention
- [ ] summarization under adequate budget
- [ ] failed collapse causes torpor
- [ ] hidden contradiction eventually surfaces
- [ ] cross-process observation requires receipt

---

## 24. Add theorem-facing interface tests

For the Lean/Python boundary:
- [ ] receipt schema matches imported theorem assumptions
- [ ] projector/POVM identifiers serialize canonically
- [ ] valuation and instrument registries are deterministic
- [ ] no-signaling assumptions are not violated structurally

---

## 25. Add import-boundary and layering tests

These should fail the build if:
- [ ] GMI imports legacy roots
- [ ] GM-OS imports agent code
- [ ] solver code bypasses receipts
- [ ] cognition code mutates committed state directly without verifier gate

---

# Phase VIII — Documentation and canon alignment

Now lock the repo and docs together so they stop drifting.

## 26. Create one master architecture map

A single document showing:
```
Coh Core → Quantum Bridge → Relativity Bridge → GM-OS substrate → GMI cognition → Solver adapters
```

### Done condition
No ambiguity about ownership of concepts or code.

---

## 27. Rewrite repo status matrix honestly

For each subsystem, show:
- spec status
- code status
- tests status
- proof status
- runtime readiness

Do not let "canon-ready" mean "implemented."

---

## 28. Freeze developer-facing completion definitions

For GM-OS and GMI define:

### GM-OS complete means
- [x] canonical package sealed
- [ ] receipts/verifier deterministic
- [ ] latent runtime operational
- [ ] inter-process observation lawful
- [ ] timing/frame semantics integrated

### GMI complete means
- [ ] hidden cognition loop works
- [ ] attention is instrument choice
- [ ] belief commitment is priced collapse
- [ ] summarization/forgetting are receipted coarse-graining
- [ ] self-model and archive update lawfully

---

# Recommended build order

This is the order that hurts least and gives the fastest real payoff:

## Batch A — Substrate seal
1. package/import cleanup ✅
2. substrate API freeze ✅
3. receipt/verifier hardening

## Batch B — GMI core stabilization
4. state model
5. execution loop
6. potential/admissibility
7. mode machine

## Batch C — Hidden cognition machinery
8. imagination workspace
9. attention instruments
10. belief collapse
11. summarization/forgetting/self-deception

## Batch D — Quantum runtime substrate
12. latent runtime manager
13. collapse API
14. inter-process observation rules

## Batch E — Relativity integration
15. clocks
16. observer/frame policy
17. time-budget effects

## Batch F — Proof/test/doc closure
18. vectors
19. scenarios
20. layering checks
21. status/canon docs

---

# Definition of complete

You can call the **GMI agent inside a complete Coh quantum/relativity GM-OS substrate** complete only when this sentence is true:

> A GMI process can evolve hidden cognitive state, choose an attention instrument, compute lawful collapse cost, project a belief/action into the canonical ledger through a deterministic verifier, interact with other processes only through receipted observation, compress or forget state through priced coarse-graining, and do all of this under frame-aware, budget-aware, test-verified GM-OS runtime rules.

That is the actual finish line.
