# Section IV — Formal Verification, Implementation Contract, and System Realization

**Canonical role:** engineering standard for canon-admissible modules  
**Status:** derived from interface contract and C-pu lifecycle

---

## 1. Purpose of Section IV

A mathematical object in Coh is not considered repo-valid merely because someone wrote equations for it. A system is only **canon-admissible** if it provides:

* a deterministic object specification,
* a frozen serialization and numeric profile,
* a total receipt verifier,
* a proof obligation set,
* mandatory test vectors,
* and versioned identity / drift protection.

The Coh canon explicitly says a valid module must provide `state_space`, `potential`, `receipt_schema`, `verifier`, and `canon_profile`. It also lists referee-grade proof obligations such as determinism, closure, and soundness.

The interface contract then sharpens that into a mechanical acceptance checklist: all required functions must exist, receipts must validate under a frozen schema, RV must be deterministic and total, required test vectors must pass, the canon profile must be pinned and hashed, and slab verification must work.

So Section IV is the bridge from:
\[
\text{"interesting theory"} \quad \longrightarrow \quad \text{"repeatable engineering standard"}.
\]

---

## 2. Canon-admissible module structure

> **Tag**: `[DEFINITION]`

A Coh module must provide at least the following five components:
\[
\mathcal M = (X,V,\Sigma,\mathrm{RV},\mathcal C),
\]
where:

* $X$ is the state-space representation,
* $V$ is the deterministic potential evaluator or a bounded certified potential payload,
* $\Sigma$ is the receipt schema family,
* $\mathrm{RV}$ is the deterministic total verifier,
* $\mathcal C$ is the canon profile.

More explicitly, the canon requires:

1. `state_space` — canonical type representation of $X$,
2. `potential` — deterministic evaluator of $V(x)$, or bounded interval receipt field if verifier does not compute it,
3. `receipt_schema` — canonical serialization plus required fields,
4. `verifier` — deterministic $\mathrm{RV}(x,r,x')$,
5. `canon_profile` — numeric representation, rounding rules, hash rules, signature rules.

---

## 3. Determinism canon

> **Tag**: `[AXIOM]` / `[CONTRACT]`

The canon says this part is **non-negotiable**. Receipts must serialize canonically, verifier arithmetic must not depend on IEEE-754 floating point, and the verifier must be total, deterministic, and side-effect free.

### 3.1 Canonical serialization

There exists a frozen canonicalization map
\[
\mathrm{JCS}:\text{Receipt}\to \text{Bytes},
\]
using RFC 8785 JCS or another frozen binary format. The canon requires canonical JSON or a frozen binary encoding, UTF-8 normalization if text exists, fixed key ordering, and no floating point values in receipts.

So the same receipt content must always produce the same bytes:
\[
r_1 \equiv r_2 \implies \mathrm{JCS}(r_1)=\mathrm{JCS}(r_2).
\]

### 3.2 Canonical numeric profile

The allowed verifier numeric domains are restricted to deterministic choices such as:

* scaled integers ($\mathrm{Fixed}(p)$),
* integer rationals,
* interval arithmetic over scaled integers.

Formally, one freezes a numeric domain
\[
\mathbb D_{\mathrm{canon}}
\]
and all verifier arithmetic must be total over that domain.

This is actually a huge deal. It means the same receipt cannot be accepted on one machine and rejected on another because one compiler got moody about floating point rounding.

### 3.3 Deterministic verifier law

The verifier is a total function
\[
\mathrm{RV}:\text{Bytes}\to \{\mathrm{ACCEPT}\}\cup \{\mathrm{REJECT}(c)\},
\]
or more concretely, given prior digest and boundary hashes,
\[
\mathrm{RV}(\mathrm{prev\_state\_hash},r,\mathrm{next\_state\_hash},\mathrm{prev\_chain\_digest})
\to \mathrm{Decision}.
\]

Determinism requires:
\[
\text{same bytes} \implies \text{same decision}.
\]

The canon states this explicitly as the Determinism Lemma.

---

## 4. Chain law and trace closure

> **Tag**: `[PROVED]`

Coh treats execution as a receipt-witnessed trace:
\[
x_0 \xrightarrow{r_0} x_1 \xrightarrow{r_1} \cdots \xrightarrow{r_{n-1}} x_n.
\]

The canon calls this the "receipt category" view and requires that legal steps compose into legal histories because receipts chain deterministically via hash, schema, policy, and canon profile.

### 4.1 Chain digest update

The Lean binding notes state the contract shape explicitly:
\[
H_{n+1}=\mathrm{hash}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)).
\]

### 4.2 Trace closure principle

> **Tag**: `[PROVED]`

If each step receipt is accepted and chain-linked, then the whole trace is accepted as a legal history. This is the canon's closure law.

### Theorem 4.1 — Trace closure

> **Tag**: `[PROVED]`

Let
\[
x_0 \xrightarrow{r_0} x_1 \xrightarrow{r_1}\cdots\xrightarrow{r_{n-1}}x_n
\]
be a receipt trace such that every step is locally accepted and every digest/state hash link matches the contract. Then the trace is globally legal under the canonical chain law.

This is what prevents "locally plausible, globally fake" execution histories.

---

## 5. Receipt schemas

> **Tag**: `[CONTRACT]`

The Lean binding notes and contract together define the required minimal schema shapes.

### 5.1 Micro receipt

A micro receipt is a tuple of the form
\[
r_{\mathrm{micro}}=
(\mathrm{schema\_id},\mathrm{version},\mathrm{object\_id},
\mathrm{canon\_profile\_hash},\mathrm{policy\_hash},
\mathrm{step\_type},\mathrm{step\_index},
H_n,H_{n+1},S_n,S_{n+1},M,\Sigma),
\]
where:

* $H_n,H_{n+1}$ are previous/next chain digests,
* $S_n,S_{n+1}$ are previous/next state boundary hashes,
* $M$ is the metrics payload,
* $\Sigma$ is the optional signature payload.

### 5.2 Slab receipt

A slab receipt aggregates a range of microsteps:
\[
r_{\mathrm{slab}}=
(\mathrm{schema\_id},\mathrm{version},\mathrm{object\_id},
\mathrm{canon\_profile\_hash},\mathrm{policy\_hash},
[m,n),\mathrm{MerkleRoot},H_m,H_n,\mathrm{Summary},\Sigma).
\]

---

## 6. Reject-code algebra

> **Tag**: `[CONTRACT]`

A verifier that merely says "nah" is not a real contract system. It is a grumpy oracle.

The Lean notes list the minimum Coh reject-code set:

\[
\begin{aligned}
&\mathrm{REJECT\_SCHEMA},\\
&\mathrm{REJECT\_CANON\_PROFILE},\\
&\mathrm{REJECT\_CHAIN\_DIGEST},\\
&\mathrm{REJECT\_STATE\_HASH\_LINK},\\
&\mathrm{REJECT\_NUMERIC\_PARSE},\\
&\mathrm{REJECT\_INTERVAL\_INVALID},\\
&\mathrm{REJECT\_OVERFLOW},\\
&\mathrm{REJECT\_POLICY\_VIOLATION},\\
&\mathrm{REJECT\_SLAB\_MERKLE},\\
&\mathrm{REJECT\_SLAB\_SUMMARY}.
\end{aligned}
\]

So the reject space is not just a set; it is a typed diagnostic algebra:
\[
\mathcal R_{\mathrm{rej}}=\{\mathrm{ACCEPT}\}\sqcup \{\mathrm{REJECT}(c): c\in \mathcal C_{\mathrm{rej}}\}.
\]

---

## 7. Minimal proof obligations

> **Tag**: `[OBLIGATION]`

The canon explicitly lists the minimum referee-grade proof obligations:

1. **Determinism Lemma** — same inputs imply same decision,
2. **Closure Lemma** — accepted chains remain accepted under chaining,
3. **Soundness Lemma** — accepted receipts imply claimed contract property,
4. **Descent / Boundedness Lemma** — when relevant, $V$ decreases or remains bounded.

### 7.1 Determinism Lemma

For any canonical inputs $I$,
\[
\mathrm{RV}(I)=\mathrm{RV}(I).
\]

More meaningfully, if two invocations receive byte-identical inputs,
\[
I_1=I_2 \implies \mathrm{RV}(I_1)=\mathrm{RV}(I_2).
\]

### 7.2 Closure Lemma

If
\[
\mathrm{RV}(x_k,r_k,x_{k+1})=\mathrm{ACCEPT}
\quad \text{for }k=0,\dots,n-1,
\]
and chain/state linkage conditions hold, then the composite trace is legal.

### 7.3 Soundness Lemma

If
\[
\mathrm{RV}(x,r,x')=\mathrm{ACCEPT},
\]
then the module's promised law actually holds, such as:
\[
V(x')+\mathrm{Spend}(r)\le V(x)+\mathrm{Defect}(r),
\]
or a conservative invariant law, or a clamp/interlock law in a specialized module.

### 7.4 Descent / Boundedness Lemma

For the governed class,
\[
V(x_{k+1})\le V(x_k)+\text{authorized slack},
\]
and under repair-only regimes the cumulative positive variation is bounded by budget.

---

## 8. Optional subclass obligations

> **Tag**: `[OBLIGATION]`

The interface contract defines extra obligations for CK-0 and PhaseLoom subclasses.

### 8.1 CK-0 extension

If the object is CK-0 subclassed, it must provide:

* residual schema,
* weight dictionary hash,
* canonical scalarization
  \[
  V(x)=\sum_i w_i r_i(x)^2,
  \]
* and receipts containing residual norm bounds and budget-law fields if amplification is budgeted.

### 8.2 PhaseLoom extension

If the module uses PhaseLoom memory, it must define boundary metrics such as:
\[
V,\ C,\ T,\ B,\ A
\]
for base risk, curvature, tension, budget, and authority; and it must publish verifier checks for recurrence clamps, low-budget interlocks, and monotone descent bounds in repair-only regimes.

---

## 9. Mechanical acceptance theorem

> **Tag**: `[CONTRACT]`

The interface contract gives a direct checklist:

A Coh module is canon-admissible iff:

1. all required functions exist,
2. receipts validate under frozen schema,
3. RV is deterministic and total,
4. all required test vectors pass,
5. canon profile is pinned and hashed,
6. slab receipts verify and challenge openings work.

### Definition 9.1 — Canon-admissibility predicate

For a module $\mathcal M$, define
\[
\mathrm{CanonOK}(\mathcal M)=\bigwedge_{i=1}^{6} P_i(\mathcal M),
\]
where each $P_i$ is one checklist item above.

### Theorem 9.2 — Mechanical acceptance criterion

\[
\mathcal M \text{ is a Coh-valid module } \iff \mathrm{CanonOK}(\mathcal M).
\]

This is the engineering reading of the contract's acceptance checklist.

---

## 10. Lean binding as the formalization layer

> **Tag**: `[DEFINITION]`

The Review of Sources file lays out drop-in Lean skeletons for:

* `CanonProfile.V1`,
* `RejectCode`,
* `MicroReceipt`,
* `Slab`,
* and related structures.

This means Section IV should explicitly declare a formalization bridge:
\[
\mathfrak F:\text{Canon Spec}\to \text{Proof Assistant Objects}.
\]

The purpose of $\mathfrak F$ is not to do cryptography in Lean for its own sake. It is to prove that the shape-level contract is coherent:

* receipt types exist,
* reject codes are exhaustive,
* chain updates are well-typed,
* closure theorems can be stated precisely.

---

## 11. Development lifecycle as a staged realization theorem

> **Tag**: `[REALIZATION]`

The C-pu lifecycle document gives a staged roadmap from math to silicon:

* Stage 0 — Mathematical Formalization,
* Stage 1 — Canonical Specification,
* Stage 2 — Reference Software Runtime,
* Stage 3 — Formal Verification,
* Stage 4 — Micro-Architecture Design,
* Stage 5 — FPGA Prototype,
* Stage 6 — ASIC Fabrication,
* Stage 7 — Operating Environment,
* Stage 8 — Distributed C-pu Network.

### 11.1 Stage map as a compositional sequence

Let $S_k$ denote the artifact at stage $k$. Then the lifecycle defines a compositional pipeline:
\[
S_0 \to S_1 \to S_2 \to S_3 \to S_4 \to S_5 \to S_6 \to S_7 \to S_8.
\]

Each stage strengthens the object:

* $S_0$: closed formal system with invariants,
* $S_1$: consensus-grade spec,
* $S_2$: functioning deterministic runtime,
* $S_3$: proof that implementation satisfies spec,
* $S_4$: hardware micro-architecture,
* $S_5$: FPGA validation,
* $S_6$: ASIC realization,
* $S_7$: deterministic operating environment,
* $S_8$: distributed coherence-verified network.

---

## 12. Section IV theorem stack

### [DEFINITION] Canon-complete module

A Coh module is a tuple
\[
\mathcal M=(X,V,\Sigma,\mathrm{RV},\mathcal C)
\]
providing state space, potential, receipt schema, verifier, and canon profile.

### [AXIOM / CONTRACT] Determinism canon

All receipts serialize canonically; verifier arithmetic uses a frozen deterministic numeric domain; RV is total, deterministic, and side-effect free.

### [DEFINITION] Chain digest law

\[
H_{n+1}=\mathrm{hash}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)).
\]

### [PROVED] Trace closure

Legal steps compose into legal histories under schema + policy + canon-profile + digest linkage.

### [DEFINITION] Reject-code algebra

The verifier returns either $\mathrm{ACCEPT}$ or one of the required typed reject codes.

### [OBLIGATION] Determinism Lemma

Same input bytes imply same verifier decision.

### [OBLIGATION] Closure Lemma

Accepted chains preserve digest / linkage legality.

### [OBLIGATION] Soundness Lemma

Accepted receipts imply the claimed object law.

### [OBLIGATION] Descent / Boundedness Lemma

For governed objects, $V$ decreases or remains bounded according to the module's law.

### [CONTRACT] Canon-admissibility predicate

A module is Coh-valid iff all checklist items in the interface contract pass.

### [REALIZATION] Lifecycle chain

A valid engineering path proceeds through formalization, spec freeze, runtime, proof, hardware design, prototype, fabrication, operating environment, and network realization.

---

## 13. Repo-ready canonical writeup for Section IV

---

# Section IV — Formal Verification, Implementation Contract, and System Realization

A Coh system is not canon-admissible merely by possessing a mathematical description. To participate in the Coh validator/compression/governance pipeline, a module must provide a canonical state-space representation $X$, a deterministic potential evaluator $V$ or bounded potential certificate, a frozen receipt schema family $\Sigma$, a total deterministic verifier $\mathrm{RV}$, and a canon profile $\mathcal C$ specifying numeric, serialization, and hash rules. The verifier must be side-effect free, deterministic on bytes, and independent of floating-point behavior.

Receipts must serialize canonically under a frozen profile, and chained execution must obey a deterministic digest law of the form
\[
H_{n+1}=\mathrm{hash}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)).
\]
A legal trace
\[
x_0 \xrightarrow{r_0} x_1 \xrightarrow{r_1}\cdots\xrightarrow{r_{n-1}}x_n
\]
is valid only if each step receipt is accepted and all digest, schema, policy, and state-hash linkage constraints are satisfied. Thus legal steps compose into legal histories.

The verifier must return either $\mathrm{ACCEPT}$ or a typed reject code. The minimum canonical reject set includes schema failure, canon-profile mismatch, chain-digest failure, state-hash linkage failure, numeric parse failure, interval invalidity, overflow, policy violation, slab Merkle failure, and slab summary failure. This makes verification failure explicit and machine-auditable.

Every Coh module must identify and eventually discharge the minimal referee-grade proof obligations: determinism, closure, soundness, and descent or boundedness. Determinism requires byte-identical inputs to produce identical decisions. Closure requires accepted step chains to remain accepted under chained verification. Soundness requires accepted receipts to imply the module's claimed contract law. Descent or boundedness requires the object's violation functional to decrease, remain bounded, or consume explicit budget according to the module's governance law.

Optional subclasses impose further obligations. CK-0 modules must publish residual schemas, weight-dictionary hashes, and canonical scalarizations such as
\[
V(x)=\sum_i w_i r_i(x)^2.
\]
PhaseLoom modules must additionally publish recurrence clamp, low-budget interlock, and repair-regime monotonicity checks for their extended boundary metrics.

A module is canon-admissible if and only if all required interfaces exist, receipts validate under the frozen schema, the verifier is deterministic and total, mandatory test vectors pass, the canon profile is pinned and hashed, and slab verification plus challenge opening succeed. This criterion converts Coh from a mathematical category into a repeatable engineering standard.

Finally, the realization path of a Coh system proceeds through staged artifacts: mathematical formalization, canonical specification, deterministic runtime, formal verification, micro-architecture design, FPGA prototyping, ASIC fabrication, deterministic operating environment, and distributed coherence-verified networking. This staged chain defines the engineering realization of Coh from abstract governance law to physical computational substrate.

---

## 14. Honest status flags for Section IV

This section is the most repo-ready of the four. The strongest parts are:

* deterministic module contract,
* receipt schema discipline,
* chain closure,
* reject-code structure,
* proof-obligation framework,
* acceptance checklist,
* staged implementation roadmap.

The parts that still need polishing before "production-grade canon" are mostly editorial and formalization-related:

* unify the contract language between canon, PDF contract, and Lean skeletons,
* remove transcript-style duplication from raw source captures,
* freeze one canonical vocabulary for micro/slab metrics payloads,
* convert the Lean sketches into a clean actual repo tree.

The structure itself is solid. It is the least mystical and most executable part of the stack.

---

## 15. Code Implementation Reference

The following modules implement the concepts in this section:

| Module | Implements |
|--------|------------|
| `ledger/oplax_verifier.py` | Deterministic verifier RV |
| `ledger/receipt.py` | Receipt schemas |
| `ledger/hash_chain.py` | Chain digest law |
| `ledger/slab_verifier.py` | Slab verification |

See individual module docstrings for `[AXIOM]`, `[CONTRACT]`, `[PROVED]`, and `[OBLIGATION]` tags.

---

*This document is the canonical source for Section IV — Formal Verification, Implementation Contract, and System Realization.*
