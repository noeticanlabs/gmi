# Section II — Discrete Governance and the Oplax Ledger

**Canonical role:** discrete governance layer converting continuous viability law into deterministic, receipt-verifiable algebra  
**Status:** derived from Volume II and interface contract

---

## 1. Scope of Section II

Section II formalizes four things:

1. how a continuous trajectory is observed only through coarse records,
2. why exact additive thermodynamic equality becomes **subadditive** after projection,
3. how a discrete transition is accepted or rejected by a deterministic verifier, and
4. how receipts, chain digests, and oplax morphisms organize these transitions categorically.

The two key transitions are:

* from **continuous dissipation** to **discrete certified envelope**, and
* from **continuous viability** to **discrete descent inequality**.

---

## 2. Projection–Dissipation Envelope System (PDES)

> **Tag**: `[POLICY]`

### 2.1 Continuous microscopic reality vs discrete macroscopic record

Let $\mathcal X$ be the true microstate path space and let $\mathcal Y$ be the observable record space.
A projection map
\[
\Pi:\mathcal X\to\mathcal Y
\]
sends a full microscopic trajectory to a coarse observable record. Because the record does not retain all hidden variables, $\Pi$ is many-to-one. The source states this explicitly as the geometry of irreversible observation.

For an observed record $R\in\mathcal Y$, define the hidden fiber
\[
\mathcal F_R:=\{\xi\in \mathsf{Sol}([0,T]) : \Pi(\xi)=R\},
\]
where $\mathsf{Sol}([0,T])$ is the set of dynamically lawful microscopic paths.

This means one observed record $R$ corresponds to many possible true paths $\xi$. So the coarse record cannot inherit exact microscopic equalities for free.

---

### 2.2 Canonical envelope

> **Tag**: `[DEFINITION]`

Let
\[
W:\mathsf{Sol}([0,T])\to \mathbb R_{\ge 0}
\]
be the true additive continuous work or dissipation functional. Then the discrete record cannot honestly claim a single exact value of $W$, because the hidden fiber contains many lawful realizations.

So define the **canonical envelope**
\[
\widehat W(R):=\sup_{\xi\in\mathcal F_R} W(\xi).
\]

This is the fundamental discrete cost functional in Section II.

#### Interpretation

Why supremum? Because a verifier must use a safe upper bound, not a wishful average. If you use anything smaller, hidden oscillations or unobserved microstructure can inject unaccounted work. The supremum is the "no cheating" choice.

---

### 2.3 Oplax composition inevitability

> **Tag**: `[PROVED]`

Suppose $R_1$ and $R_2$ are sequential records, and $R_2\odot R_1$ denotes concatenation.
Assume the true micro-physics is exactly additive:
\[
W(\xi_1\cdot \xi_2)=W(\xi_1)+W(\xi_2).
\]

Then the macroscopic envelope obeys
\[
\widehat W(R_2\odot R_1)\le \widehat W(R_1)+\widehat W(R_2).
\]

This is Theorem 6.1 in Volume II.

#### Proof

Take any composite lawful microscopic path
\[
\xi\in\mathcal F_{R_2\odot R_1}.
\]

Then $\xi$ splits into two lawful pieces
\[
\xi_1\in\mathcal F_{R_1},\qquad \xi_2\in\mathcal F_{R_2}.
\]

By microscopic additivity,
\[
W(\xi)=W(\xi_1)+W(\xi_2).
\]

Now each piece is bounded above by the relevant supremum:
\[
W(\xi_1)\le \sup_{\eta\in\mathcal F_{R_1}}W(\eta)=\widehat W(R_1),
\]
\[
W(\xi_2)\le \sup_{\zeta\in\mathcal F_{R_2}}W(\zeta)=\widehat W(R_2).
\]

Therefore
\[
W(\xi)\le \widehat W(R_1)+\widehat W(R_2).
\]

Taking the supremum over all admissible composite $\xi$ gives
\[
\widehat W(R_2\odot R_1)\le \widehat W(R_1)+\widehat W(R_2).
\]

Done.

#### Why "oplax"?

Because composition is no longer preserved by equality. It is preserved only up to inequality:
\[
\text{cost of composite} \le \text{sum of component costs}.
\]

That is exactly the oplax flavor: structure is preserved with controlled slack, not rigid equality. The universe lost information under projection, so the ledger lost strict additivity. That is not a bug. That is the theorem.

---

## 3. Coh object in the discrete category

> **Tag**: `[DEFINITION]`

Volume II defines the base discrete governed object as a 5-tuple
\[
\mathcal S=(X,V,\mathrm{Spend},\mathrm{Defect},\mathrm{RV}),
\]
where:

1. $X$ is the state space with admissible subset $\mathcal K\subset X$,
2. $V:X\to \mathbb R_{\ge 0}\cup\{+\infty\}$ is the violation functional,
3. $\mathrm{Spend}:\mathcal R\to \mathbb R_{\ge 0}$ is verified irreversible dissipation,
4. $\mathrm{Defect}:\mathcal R\to \mathbb R_{\ge 0}$ is truncation / observation tolerance,
5. $\mathrm{RV}:X\times \mathcal R\times X\to\{\mathrm{ACCEPT},\mathrm{REJECT}\}$ is the deterministic receipt verifier.

Here $\mathcal R$ is the receipt space. A receipt $r\in\mathcal R$ is the algebraic certificate of a proposed transition
\[
x \xrightarrow{,r,} x'.
\]

---

## 4. The soundness contract

> **Tag**: `[AXIOM]` / `[CONTRACT]`

A transition is accepted only if it satisfies the discrete descent law
\[
V(x')+\mathrm{Spend}(r)\le V(x)+\mathrm{Defect}(r).
\]

This is the central soundness inequality of Section II.

This is the discrete projection of the continuous absorbing boundary law from Section I.

### 4.1 Rearrangement

Move terms to isolate the risk change:
\[
V(x')-V(x)\le \mathrm{Defect}(r)-\mathrm{Spend}(r).
\]

So the increase in risk is bounded above by "allowed defect minus actual spend."

### Consequences

> **Tag**: `[PROVED]`

If
\[
\mathrm{Defect}(r)\le \mathrm{Spend}(r),
\]
then
\[
V(x')\le V(x).
\]

So the transition is non-increasing in violation.

If the inequality is strict:
\[
\mathrm{Defect}(r)<\mathrm{Spend}(r),
\]
then
\[
V(x')<V(x),
\]
provided $V$ lives in an exact arithmetic setting that can witness the strict gap.

This is the discrete analogue of continuous dissipation dominating outward drift.

---

### 4.2 Boundary absorption in discrete form

> **Tag**: `[PROVED]`

Section I had:
\[
b=0 \implies \frac{dV}{dt}\le 0.
\]

Section II translates that into receipt form. The source phrases it as: if budget is exhausted and the defect is bounded by the spend, the discrete inequality forces boundary absorption. In effect, as $b\to 0$, admissible accepted steps must satisfy vanishing spend/defect leakage, so
\[
V(x')\le V(x).
\]

The goblin-free version is: once the budget is gone, the verifier cannot legally approve a step that increases risk.

---

## 5. Failure of endpoint sampling

> **Tag**: `[LEMMA-NEEDED]`

A major point in Section II is that naive endpoint comparison is not safe.

Consider an absolutely continuous trajectory $x(t)$ on a partition
\[
t_0<t_1<\cdots<t_N=T.
\]

The naive discrete risk estimate is
\[
\big(V(x(T))-V(x(0))\big)_+.
\]

But this can miss oscillatory excursions where risk rises and falls within subintervals. Volume II states this explicitly as Theorem 8.1.

#### Example

Suppose on some interval $[t_k,t_{k+1}]$, the path does this:

* first $V$ rises by $(+10)$,
* then it falls by $(-10)$.

Then the endpoint change is $0$, but a verifier that uses only endpoints sees no cost. That is nonsense if the continuous law spends budget whenever $\dot V>0$. The path had genuine positive-variation episodes and must not be free.

So endpoint sampling underestimates accumulated risk.

---

## 6. Positive variation as the minimal safe discrete quantity

> **Tag**: `[PROVED]`

To correctly bind the discrete ledger to the continuous spend law
\[
\dot b=-\kappa \left(\frac{dV}{dt}\right)_+,
\]
Volume II defines the positive variation
\[
\mathcal V_+(T)=\int_0^T \left(\frac{d}{dt}V(x(t))\right)_+dt.
\]

This is Theorem 8.2's central object.

### 6.1 Why it dominates endpoint change

For any absolutely continuous scalar function $f$,
\[
f(T)-f(0)=\int_0^T f'(t)\,dt
= \int_0^T (f'(t))_+\,dt - \int_0^T (f'(t))_-\,dt,
\]
where
\[
a_-:=\max(-a,0).
\]

Hence
\[
f(T)-f(0)\le \int_0^T (f'(t))_+\,dt.
\]

Applying this to $f(t)=V(x(t))$,
\[
V(x(T))-V(x(0))\le \mathcal V_+(T).
\]

So $\mathcal V_+(T)$ dominates net positive endpoint increase.

And since any slab refinement can only reveal more oscillatory structure, the integral positive variation is the minimal safe quantity that survives all refinements. That is exactly the theorem's intended role.

---

## 7. Deterministic discrete budget law

> **Tag**: `[AXIOM]` / `[CONTRACT]`

Let $\widehat{\mathcal D}_k$ be the verified discrete dissipation proxy at step $k$, and let
\[
\tau_k=\mathcal O(\Delta t_k^2)
\]
be the truncation defect. Then the deterministic budget update law is
\[
B_{k+1}=B_k-\kappa \widehat{\mathcal D}_k-\tau_k\ge 0.
\]

This is stated explicitly in Section 8.3.

### 7.1 Monotonicity

> **Tag**: `[PROVED]`

Since $\widehat{\mathcal D}_k\ge 0$ and $\tau_k\ge 0$,
\[
B_{k+1}\le B_k.
\]

So $(B_k)$ is monotone nonincreasing.

### 7.2 Summed inequality

> **Tag**: `[PROVED]`

Summing from $k=0$ to $N-1$:
\[
B_N = B_0-\sum_{k=0}^{N-1}\big(\kappa\widehat{\mathcal D}_k+\tau_k\big).
\]

Since $B_N\ge 0$,
\[
\sum_{k=0}^{N-1}\big(\kappa\widehat{\mathcal D}_k+\tau_k\big)\le B_0.
\]

This is exactly the certified finite-lifespan estimate in the source.

#### Interpretation

You cannot spend more verified dissipation-plus-defect than the initial budget. So infinite runaway legal computation is blocked unless the cost per step degenerates to zero. The ledger is literally a fuel tank with math instead of gasoline fumes.

---

## 8. Chattering theorem for normalized descent

> **Tag**: `[LEMMA-NEEDED]`

Volume II includes a warning theorem about normalized root-clock descent. Define
\[
\mathcal D(\Psi):=|\nabla E(\Psi)|^2
\]
and the normalized field
\[
\widetilde{\mathcal F}(\Psi)
= -\frac{\nabla E(\Psi)}{\sqrt{\mathcal D(\Psi)}}
= -\frac{\nabla E(\Psi)}{|\nabla E(\Psi)|},
\qquad \Psi\notin Z,
\]
where
\[
Z:=\{\Psi:\nabla E(\Psi)=0\}.
\]

This is stated in Section 8.4.

The theorem says this normalized map is not Lipschitz near $Z$, so a purely normalized explicit discrete solver can chatter infinitely around a critical point rather than settle.

#### Why?

Because the direction field
\[
-\frac{\nabla E}{|\nabla E|}
\]
has unit magnitude but unstable direction near zeros of $\nabla E$. If $\nabla E$ changes sign rapidly near a critical point, the normalized direction can flip abruptly while refusing to shrink in magnitude. So the solver jitters instead of converging.

This matters because Section II is not just a ledger section. It also says: beware of discrete control laws that look elegant but explode into pathological chatter under finite stepping.

---

## 9. Morphisms and Pos-enrichment

> **Tag**: `[DEFINITION]` / `[ORDER]`

Now the categorical part.

A morphism
\[
f:\mathcal A\to \mathcal B
\]
consists of state and receipt mappings that preserve legality up to explicitly quantified slack $\Delta_f$. Formally, if
\[
\mathcal A.\mathrm{RV}(x,r,x')=\mathrm{ACCEPT},
\]
then
\[
\mathcal B.\mathrm{RV}(f(x),f(r),f(x'))=\mathrm{ACCEPT},
\]
and
\[
\mathcal B.V(f(x'))+\mathcal B.\mathrm{Spend}(f(r))
\le
\mathcal B.V(f(x))+\mathcal B.\mathrm{Defect}(f(r))+\Delta_f.
\]

This is Definition 7.2.

### 9.1 Meaning of slack

$\Delta_f$ measures how much descent law looseness is introduced by reinterpretation. A perfect strict morphism would have
\[
\Delta_f=0.
\]

A weaker morphism has $\Delta_f>0$.

The preorder on morphisms is:
\[
f\le g \iff \Delta_f\le \Delta_g.
\]

So tighter morphisms are smaller in the Pos-enriched order.

That is a neat move: morphism quality is not vibes, it is an ordered scalar slack.

---

## 10. Internal bridge morphism

> **Tag**: `[DEFINITION]`

Volume II also includes an internal bridge between different dissipative parametrizations. If
\[
\mathcal D_a=\int \pi^{2-a}|\nabla u|^2\,dx
\]
and $\varepsilon$ is a density floor, then
\[
\mathcal D_a\le \varepsilon^{1-a}\mathcal D_1
\implies
\mathrm{Spend}_a(r)\le \varepsilon^{1-a}\mathrm{Spend}_1(r).
\]

This is the Shannon-to-power bridge in the source.

So one defines an internal morphism
\[
\Phi_a=(\mathrm{id},f_R,\alpha_a,\Delta_{1\to a})
\]
that translates one ledger parameterization into another with explicit distortion control.

This is good categorical hygiene: different physical parametrizations are not just handwaved "equivalent"; they are connected by a morphism with tracked slack.

---

## 11. Canon profile and digest law

> **Tag**: `[CONTRACT]`

Section II becomes repo-real only when paired with the interface contract.

Every Coh module must freeze a canon profile with:

* RFC 8785 JCS canonical JSON,
* SHA-256 with domain tag `COH_V1`,
* deterministic numeric encoding,
* and the chain digest update law
  \[
  H_{n+1}=\mathrm{SHA256}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)).
  \]

This is explicitly stated in the interface contract.

#### Why this matters

Without canonicalization, the same receipt could hash differently on different machines. Then your "deterministic ledger" becomes a clown car.

The contract also forbids verifier-side IEEE-754 float and restricts numeric domains to fixed-point, rationals, or intervals.

---

## 12. Receipt schemas

### 12.1 Micro receipt

> **Tag**: `[CONTRACT]`

A micro receipt must contain at least:

* `schema_id`, `version`,
* `object_id`,
* `canon_profile_hash`, `policy_hash`,
* `step_type`, `step_index`,
* `chain_digest_prev`, `chain_digest_next`,
* `state_hash_prev`, `state_hash_next`,
* module-defined canonical `metrics`,
* optional signatures.

In math-ish abstract form, we can write a micro receipt as
\[
r_{\text{micro}}
= (\mathrm{id},\mathrm{policy},\mathrm{step},H_n,H_{n+1},S_n,S_{n+1},M,\Sigma).
\]

Here:

* $H_n,H_{n+1}$ are chain digests,
* $S_n,S_{n+1}$ are state-boundary hashes,
* $M$ is the metrics payload,
* $\Sigma$ is optional authority/signature data.

The Lean-oriented notes mirror this schema exactly.

### 12.2 Slab receipt

> **Tag**: `[CONTRACT]`

A slab receipt aggregates a range of micro receipts and must include:

* `schema_id`, `version`,
* `object_id`,
* `canon_profile_hash`, `policy_hash`,
* `range:{start,end}` with $start<end$,
* `merkle_root`,
* `chain_digest_prev`, `chain_digest_next`,
* `summary`,
* optional signatures.

Abstractly:
\[
r_{\text{slab}}
= (\mathrm{id},\mathrm{policy},[m,n),\mathrm{MerkleRoot},H_m,H_n,\mathrm{Summary},\Sigma).
\]

This lets the ledger compress many microsteps into one higher-level commitment without losing cryptographic linkage.

---

## 13. Core verifier predicate

> **Tag**: `[CONTRACT]`

The mandatory verifier interface is
\[
\mathrm{RV}(\mathrm{prev\_state\_hash},\mathrm{receipt},\mathrm{next\_state\_hash},\mathrm{prev\_chain\_digest})\to \mathrm{Decision},
\]
with decision in
\[
\{\mathrm{ACCEPT}\}\cup \{\mathrm{REJECT}(\mathrm{code})\}.
\]

This is frozen in the interface contract.

Importantly, the contract says the verifier should validate using only receipt bytes, prior digest, and state-boundary hashes, not full internal state.

That is a powerful design constraint: the verifier is a lawful border guard, not an omniscient deity.

---

## 14. Minimal reject-code structure

> **Tag**: `[CONTRACT]`

The review notes extract a minimum reject-code set including:

* schema failure,
* canon profile failure,
* chain digest failure,
* state hash linkage failure,
* numeric parse failure,
* interval invalidity,
* overflow,
* policy violation,
* slab Merkle failure,
* slab summary failure.

That means every rejected transition has a typed reason. This is good. "Rejected because bad" is not a theory. It is a sulk.

---

## 15. Formal theorem stack for Section II

### [POLICY] PDES projection

There exists a many-to-one projection
\[
\Pi:\mathcal X\to \mathcal Y,
\]
with hidden fiber
\[
\mathcal F_R=\{\xi\in\mathsf{Sol}([0,T]):\Pi(\xi)=R\}.
\]

### [DEFINITION] Canonical envelope

\[
\widehat W(R)=\sup_{\xi\in\mathcal F_R}W(\xi).
\]

### [PROVED] Oplax subadditivity

If microscopic work is additive, then
\[
\widehat W(R_2\odot R_1)\le \widehat W(R_1)+\widehat W(R_2).
\]

### [DEFINITION] Coh discrete object

\[
\mathcal S=(X,V,\mathrm{Spend},\mathrm{Defect},\mathrm{RV}).
\]

### [AXIOM / CONTRACT] Discrete descent law

A transition $x\xrightarrow{r}x'$ is accepted only if
\[
V(x')+\mathrm{Spend}(r)\le V(x)+\mathrm{Defect}(r).
\]

### [PROVED] Descent consequence

If
\[
\mathrm{Defect}(r)\le \mathrm{Spend}(r),
\]
then
\[
V(x')\le V(x).
\]

### [PROVED] Positive-variation dominance

\[
V(x(T))-V(x(0))\le \int_0^T\left(\frac{d}{dt}V(x(t))\right)_+dt.
\]

Supported by the Section 8.2 construction.

### [AXIOM / CONTRACT] Discrete budget update

\[
B_{k+1}=B_k-\kappa\widehat{\mathcal D}_k-\tau_k\ge 0.
\]

### [PROVED] Finite budget bound

\[
\sum_{k=0}^{N-1}\big(\kappa\widehat{\mathcal D}_k+\tau_k\big)\le B_0.
\]

### [DEFINITION] Oplax morphism

\[
\mathcal B.V(f(x'))+\mathcal B.\mathrm{Spend}(f(r))
\le
\mathcal B.V(f(x))+\mathcal B.\mathrm{Defect}(f(r))+\Delta_f.
\]

### [ORDER] Pos-enrichment by slack

\[
f\le g \iff \Delta_f\le \Delta_g.
\]

### [CONTRACT] Canon profile

\[
H_{n+1}=\mathrm{SHA256}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)).
\]

---

## 16. Repo-ready canonical writeup for Section II

---

# Section II — Discrete Governance and the Oplax Ledger

Let $\Pi:\mathcal X\to\mathcal Y$ be a many-to-one projection from microscopic lawful paths to observable records. For each record $R\in\mathcal Y$, define the hidden fiber
\[
\mathcal F_R=\{\xi\in\mathsf{Sol}([0,T]):\Pi(\xi)=R\}.
\]

If
\[
W:\mathsf{Sol}([0,T])\to\mathbb R_{\ge 0}
\]
is the exact additive continuous work functional, then the verifiable discrete thermodynamic cost of $R$ is the canonical envelope
\[
\widehat W(R)=\sup_{\xi\in\mathcal F_R}W(\xi).
\]

For sequential records $(R_1,R_2)$, microscopic additivity implies the macroscopic oplax law
\[
\widehat W(R_2\odot R_1)\le \widehat W(R_1)+\widehat W(R_2).
\]

A discrete governed system is a tuple
\[
\mathcal S=(X,V,\mathrm{Spend},\mathrm{Defect},\mathrm{RV}),
\]
where $X$ is the state space, $V$ is the violation functional, $\mathrm{Spend}$ is the verified irreversible dissipation, $\mathrm{Defect}$ is the truncation or observational tolerance, and $\mathrm{RV}$ is a total deterministic receipt verifier. A proposed step
\[
x\xrightarrow{,r,}x'
\]
is accepted only if
\[
V(x')+\mathrm{Spend}(r)\le V(x)+\mathrm{Defect}(r).
\]

Hence any accepted step with
\[
\mathrm{Defect}(r)\le \mathrm{Spend}(r)
\]
is non-increasing in violation:
\[
V(x')\le V(x).
\]

To bind the discrete ledger to the continuous spend law, one must account not merely for endpoint difference but for the positive variation
\[
\mathcal V_+(T)=\int_0^T\left(\frac{d}{dt}V(x(t))\right)_+dt.
\]

This is the minimal safe scalar that dominates all endpoint-based underestimates caused by oscillatory excursions.

The deterministic budget update law is
\[
B_{k+1}=B_k-\kappa\widehat{\mathcal D}_k-\tau_k\ge 0,
\]
where $\widehat{\mathcal D}_k\ge 0$ is the verified discrete dissipation proxy and $\tau_k\ge 0$ is the rigorous truncation defect. Summation yields
\[
\sum_{k=0}^{N-1}\big(\kappa\widehat{\mathcal D}_k+\tau_k\big)\le B_0,
\]
so the total certified spend is bounded by the initial budget.

A morphism $f:\mathcal A\to\mathcal B$ between governed systems preserves legality up to additive slack $\Delta_f$, satisfying
\[
\mathcal B.V(f(x'))+\mathcal B.\mathrm{Spend}(f(r))
\le
\mathcal B.V(f(x))+\mathcal B.\mathrm{Defect}(f(r))+\Delta_f.
\]

Morphisms are ordered by tightness:
\[
f\le g \iff \Delta_f\le \Delta_g.
\]

Thus the category of governed systems is naturally $\mathbf{Pos}$-enriched.

Each receipt is canonically serialized and chain-bound by a frozen digest law
\[
H_{n+1}=\mathrm{SHA256}(\mathrm{tag}\ |\ H_n\ |\ \mathrm{JCS}(r_n)),
\]
with deterministic numeric encoding and verifier-side rejection on overflow or schema violation. Micro receipts certify individual transitions; slab receipts compress ranges of micro receipts through a Merkle commitment while preserving chain linkage and policy summaries.

---

## 17. Code Implementation Reference

The following modules implement the concepts in this section:

| Module | Implements |
|--------|------------|
| `ledger/oplax_verifier.py` | Receipt verifier RV, discrete descent law |
| `ledger/receipt.py` | Micro receipt schema, chain digests |
| `ledger/slab_verifier.py` | Slab receipt, Merkle commitment |
| `ledger/hash_chain.py` | Canon profile, SHA256 digest law |

See individual module docstrings for `[AXIOM]`, `[POLICY]`, `[PROVED]`, and `[LEMMA-NEEDED]` tags.

---

*This document is the canonical source for Section II — Discrete Governance and the Oplax Ledger. All theorems are either directly from the source material or verified derivations.*
