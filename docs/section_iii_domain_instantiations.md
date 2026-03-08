# Section III — Domain Instantiations and Verified Solver Theories

**Canonical role:** domain-specific Coh object realizations  
**Status:** derived from Volume III and Volume IV instantiations

---

## 1. Purpose of Section III

Sections I and II gave the universal laws:

* admissible state spaces,
* violation functionals,
* budget laws,
* receipt verification,
* oplax composition.

Section III answers the next question:

**What does a concrete Coh object look like in a real mathematical domain?**

Formally, a domain instantiation is a Coh object
\[
\mathcal S_{\mathrm{dom}}=(X,V,\mathrm{Spend},\mathrm{Defect},\mathrm{RV},\mathcal P),
\]
where:

* $X$ is now a domain-specific state space,
* $V$ is a domain-specific risk / obstruction / residual scalar,
* $\mathrm{Spend}$ measures verified irreversible cost,
* $\mathrm{Defect}$ tracks discretization or observational tolerance,
* $\mathrm{RV}$ is the deterministic verifier,
* $\mathcal P$ is the package of constitutive PDE, variational, or geometric laws.

This is consistent with the Section II Coh-object law and the interface contract's "canon-admissible module" requirement.

---

## 2. General template for a domain instantiation

> **Tag**: `[DEFINITION]`

A Section III solver module should specify six things.

### 2.1 State space

$X_{\mathrm{dom}}$

For example:

* function spaces for PDEs,
* tangent-bundle or phase-space objects for mechanics,
* residual dictionaries for CK-0 systems.

### 2.2 Domain violation functional

$V_{\mathrm{dom}}:X_{\mathrm{dom}}\to \mathbb R_{\ge 0}\cup\{+\infty\}.$

This is the scalar that tells the governance layer what counts as risk or unresolved obstruction.

### 2.3 Physical spend

$\mathrm{Spend}_{\mathrm{dom}}(r)\ge 0.$

This is the irreversible thermodynamic, variational, or dissipation cost certified by the receipt.

### 2.4 Defect law

$\mathrm{Defect}_{\mathrm{dom}}(r)\ge 0.$

This captures numerical truncation, observational loss, or modeling slack.

### 2.5 Soundness inequality

Every accepted step must satisfy
\[
V_{\mathrm{dom}}(x')+\mathrm{Spend}_{\mathrm{dom}}(r)
\le
V_{\mathrm{dom}}(x)+\mathrm{Defect}_{\mathrm{dom}}(r).
\]

That comes straight from Section II and remains non-negotiable in the instantiated domain.

### 2.6 Canon interface

The module must also satisfy the receipt schema, deterministic verifier rules, and digest law frozen by the interface contract.

So Section III is not "applications" in the casual sense. It is **the theorem that the abstract Coh object can be realized in specific mathematical worlds**.

---

## 3. Instantiation A — Navier–Stokes as NS-PCM

> **Tag**: `[INSTANTIATION]`

This is the most developed PDE instantiation in the archive.

### 3.1 PDE foundation

Work on the flat 3-torus $\mathbb T^3$, with smooth divergence-free velocity field
\[
u:[0,T]\times \mathbb T^3\to \mathbb R^3,
\qquad \nabla\cdot u=0.
\]

The incompressible Navier–Stokes equations are
\[
\partial_t u+(u\cdot \nabla)u+\nabla p=\nu \Delta u,
\qquad \nu>0.
\]

This is the base PDE law in Volume III.

Define vorticity
\[
\omega:=\nabla\times u
\]
and symmetric strain tensor
\[
S:=\frac12\big(\nabla u+(\nabla u)^\top\big).
\]

Then taking curl gives
\[
\partial_t\omega+(u\cdot \nabla)\omega
= (\omega\cdot \nabla)u+\nu\Delta \omega.
\]

The nonlinear obstruction is the vortex stretching term
\[
(\omega\cdot \nabla)u=S\omega.
\]

### 3.2 Exact enstrophy identity

> **Tag**: `[PROVED]`

Take the $L^2$ inner product of the vorticity equation with $\omega$. By incompressibility and periodicity, the transport term cancels, yielding
\[
\frac12\frac{d}{dt}|\omega|_2^2+\nu|\nabla\omega|_2^2
= \int (S\omega)\cdot \omega\,dx.
\]

This is the central identity in Volume III.

Writing
\[
\omega=|\omega|\xi,
\qquad |\xi|=1
\]
on the support of $\omega$, one gets
\[
\int (S\omega)\cdot \omega\,dx
= \int (S\xi\cdot \xi)\,|\omega|^2\,dx.
\]

So the whole regularity problem concentrates into one question:

Can the stretching term be dominated by viscosity?

### 3.3 Regularized polar decomposition

To avoid singularities where $\omega=0$, introduce $\varepsilon>0$ and define
\[
\rho_\varepsilon:=\sqrt{|\omega|^2+\varepsilon^2},
\qquad
\xi_\varepsilon:=\frac{\omega}{\rho_\varepsilon}.
\]

Then
\[
\omega=\rho_\varepsilon \xi_\varepsilon,
\qquad
|\xi_\varepsilon|\le 1.
\]

This is the regularized decomposition in Volume III.

This is mathematically useful because it splits the vorticity into:

* magnitude $\rho_\varepsilon$,
* direction $\xi_\varepsilon$.

That lets the theory isolate **directional complexity** as a separate geometric obstruction rather than treating the whole nonlinear mess as one undifferentiated fluid goblin.

### 3.4 Weak-vorticity geometry and the Route C bottleneck

Define the weak-vorticity region
\[
A_\delta(t):=\{x:|\omega(t,x)|<\delta\}.
\]

The source isolates the remaining obstruction into the low-frequency strain integral
\[
R_{\le J}(\delta,t)
= \int_{A_\delta}|S_{\le J}|_{\mathrm{op}}\,dx.
\]

This is explicitly described as the "Route C Lipschitz bottleneck."

By contrast, the high-frequency contribution
\[
R_{>J}(\delta,t)
\le
|A_\delta|^{1/2}|S_{>J}|_{L^2}
\lesssim
|A_\delta|^{1/2}2^{-J}|\nabla\omega|_{L^2}
\]
is absorbable for large $J$.

So the whole problem reduces to the low-frequency term on the weak-vorticity geometry. That is the serious mathematical payload here.

### 3.5 Bony paraproduct and boundary bleed

Substitute the decomposition $\omega=\rho_\varepsilon\xi_\varepsilon$ into dyadic blocks:
\[
\Delta_k\omega
= \Delta_k(T_{\rho_\varepsilon}\xi_\varepsilon)
+ \Delta_k(T_{\xi_\varepsilon}\rho_\varepsilon)
+ \Delta_k(R(\rho_\varepsilon,\xi_\varepsilon)).
\]

This is the Bony paraproduct decomposition used in Section 11 of Volume III.

The critical leakage channel is the term
\[
T_{\rho_\varepsilon}\xi_\varepsilon.
\]

Now decompose
\[
\rho_\varepsilon=\rho_\varepsilon^{\mathrm{in}}+\rho_\varepsilon^{\mathrm{out}},
\]
where $\rho_\varepsilon^{\mathrm{in}}$ lives inside $A_\delta$ and $\rho_\varepsilon^{\mathrm{out}}$ outside.

The low-pass filter leaks outside mass into the weak-vorticity eye through the **boundary bleed**
\[
B_k(\delta)
= |S_{k-1}\rho_\varepsilon^{\mathrm{out}}|_{L^\infty(A_\delta)}.
\]

This term measures penetration across the boundary $\partial A_\delta$ at dyadic scale $2^{-k}$. That is the place where the geometry of the weak-vorticity interface becomes decisive.

### 3.6 Measure-theoretic maximum principle

The source then states a shrinkage law for the deep weak-vorticity core:
\[
\mu_{2\lambda}(t)
= \big|\{x:|\omega(t,x)|<\delta-2\lambda\}\big|.
\]

The theorem gives
\[
\mu_{2\lambda}(t)^{1/3}
\le
C_0\frac{(\delta-\lambda)^2}{\nu\lambda^2}R_{\le J}(\delta-\lambda,t).
\]

Interpretation: if the weak-vorticity core stays macroscopically large, then low-frequency strain must pile up there in a very specific way. So the geometry is not arbitrary; it is constrained by the PDE itself.

### 3.7 Besov-SSL boundary hypothesis

> **Tag**: `[HYPOTHESIS]`

Define the indicator of the weak-vorticity set
\[
f_\delta(t,x):=\mathbf 1_{A_\delta(t)}(x).
\]

The Besov-SSL hypothesis is
\[
|f_\delta(t)|_{\dot B^s_{1,\infty}}
:= \sup_{k\in\mathbb Z}2^{sk}|\Delta_k f_\delta(t)|_{L^1}
\le C_{\mathrm{SSL}}.
\]

This hypothesis says the interface is not pathologically space-filling across scales.

### 3.8 Closure theorem and diagnostic gate

> **Tag**: `[PROVED]` (under hypothesis)

Theorem 12.1 in Volume III says: if the Besov-SSL hypothesis holds, then the low-frequency obstruction is bounded by structural dissipation, preventing finite-time blow-up.

The exact numerical diagnostic is
\[
\mathcal Q_\delta(t)
= \frac{\delta^2\int_{A_\delta}|S(u)|_{\mathrm{op}}\,dx}{\nu|\nabla\omega(t)|_2^2}.
\]

The "Millennium gate" is:
\[
\mathcal Q_\delta(t)<1.
\]

If this inequality holds, the obstruction is absorbable by viscosity. In Coh language, that means the solver's physical spend dominates the obstruction term and the ledger can certify non-blow-up over the verified interval.

### 3.9 NS-PCM as Coh object

> **Tag**: `[INSTANTIATION]`

The NS-PCM instantiation can be packaged as:

\[
X_{\mathrm{NS}}=
\{u\in H^s(\mathbb T^3;\mathbb R^3):\nabla\cdot u=0\},
\]

with an obstruction scalar such as
\[
V_{\mathrm{NS}}(u)
= \big(\mathcal Q_\delta(u)-1\big)_+,
\]
or a more refined dyadic residualization.

---

## 4. Instantiation B — Coh-Relativity and the GR bridge

> **Tag**: `[INSTANTIATION]`

Now the second major instantiation.

This one takes the viability/barrier machinery and interprets it as relativistic kinematics and then as a constitutive gravitational geometry.

### 4.1 Half-log velocity barrier

Impose the admissible velocity ball
\[
|v|<c.
\]

Define the barrier
\[
\widetilde V(v)
= -\frac12\log\left(1-\frac{|v|^2}{c^2}\right).
\]

The viability density is
\[
e^{-\widetilde V(v)}
= \sqrt{1-\frac{|v|^2}{c^2}}.
\]

Hence the action is
\[
\mathcal A[x]
= \int_{t_0}^{t_1}e^{-\widetilde V(\dot x(t))}\,dt.
\]

### 4.2 Proper time from viability

> **Tag**: `[PROVED]`

Define intrinsic time density
\[
\varphi:=\frac{d\tau}{dt}=e^{-\widetilde V(v)}.
\]

Then
\[
\frac{d\tau}{dt}
= \sqrt{1-\frac{|v|^2}{c^2}},
\]
so
\[
d\tau
= \sqrt{1-\frac{|v|^2}{c^2}}\,dt.
\]

Since $dx=v\,dt$,
\[
d\tau^2
= dt^2-\frac{dx^2}{c^2}.
\]

This is the explicit "Minkowski interval" theorem in the source.

So in this instantiation, proper time is not postulated as primitive. It is generated from the viability barrier.

### 4.3 Hessian metric on velocity space

> **Tag**: `[PROVED]`

The induced Hessian metric is
\[
g_{ij}(v)
= \frac{\partial^2\widetilde V}{\partial v_i\partial v_j}.
\]

The source identifies this with the Klein hyperbolic geometry and states that Lorentz boosts act as isometries of this risk manifold.

The archive also states the induced Einstein velocity addition law:
\[
\mathbf v'
= \frac{\mathbf v_\parallel-\mathbf u+\frac{1}{\gamma_u}\mathbf v_\perp}
{1-\frac{\mathbf u\cdot \mathbf v}{c^2}},
\qquad
\gamma_u=(1-|\mathbf u|^2/c^2)^{-1/2}.
\]

### 4.4 Relativistic dynamics via Legendre transform

> **Tag**: `[PROVED]`

Introduce a scale parameter $m>0$ and define the Lagrangian
\[
L(v)
= -mc^2 e^{-\widetilde V(v)}.
\]

Since
\[
e^{-\widetilde V(v)}
= \sqrt{1-\frac{|v|^2}{c^2}},
\]
this becomes
\[
L(v)
= -mc^2\sqrt{1-\frac{|v|^2}{c^2}}.
\]

Then the momentum is
\[
p
= \frac{\partial L}{\partial v}
= \gamma_v m v,
\qquad
\gamma_v=(1-|v|^2/c^2)^{-1/2}.
\]

The source further states that this yields the mass-shell condition
\[
E^2-(pc)^2=(mc^2)^2.
\]

### 4.5 Electrodynamics by minimal coupling

> **Tag**: `[PROVED]`

Add a background 1-form
\[
A_\mu=(-\phi,\mathbf A)
\]
and coupling parameter $q$. The source modifies the Lagrangian by
\[
L'
= L+q(\mathbf v\cdot \mathbf A-\phi).
\]

Then the Euler–Lagrange equations yield
\[
\frac{d\mathbf p}{dt}
= q(\mathbf E+\mathbf v\times \mathbf B).
\]

Gauge transformation
\[
\mathbf A'=\mathbf A+\nabla\chi,
\qquad
\phi'=\phi-\partial_t\chi
\]
changes the Lagrangian by a total derivative:
\[
L'\mapsto L'+q\frac{d\chi}{dt},
\]
so the equations are gauge invariant.

This gives a second concrete domain theorem: external fields enter as minimal bias couplings of the viability action.

### 4.6 Lawfulness power and the ADM lapse

> **Tag**: `[CONSTITUTIVE BRIDGE]`

Define the lawfulness power
\[
\Lambda(x):=b+\alpha\mathcal D_a\ge 0.
\]

Then identify the lapse
\[
N(x):=\sqrt{\Lambda(x)}=\sqrt{b+\alpha\mathcal D_a}.
\]

Define the spatial metric from a symmetric positive-definite resistance operator:
\[
\gamma_{ij}(x):=\alpha \mathcal R_{ij}(x).
\]

Then the line element becomes
\[
ds^2=-b(x)\,dt^2+\alpha \mathcal R_{ij}(x)\,dx^i dx^j,
\]
in the source's constitutive presentation.

### 4.7 Horizon theorem

> **Tag**: `[PROVED]`

When
\[
\Lambda\to 0,
\]
the lapse vanishes:
\[
N\to 0.
\]

That means coordinate time diverges relative to proper time. The source calls this the "vanishing-lapse horizon."

So in the domain-instantiated sense, budget exhaustion plus zero dissipation becomes a geometric freezing boundary.

That is the gravitational analogue of Section I's budget-boundary absorption.

### 4.8 Scalar budget gravity and weak-field expansion

> **Tag**: `[WEAK-FIELD BRIDGE]`

The source then imposes mobility-resistance duality
\[
\mathcal R_{ij}=b^{-1}\delta_{ij}.
\]

Expand the budget in weak field form:
\[
b(x)\approx 1-\frac{2GM}{rc^2}.
\]

Then
\[
\gamma_{ij}
\approx
\left(1-\frac{2GM}{rc^2}\right)^{-1}\delta_{ij}
\approx
\left(1+\frac{2GM}{rc^2}\right)\delta_{ij}.
\]

The source claims this gives the PPN parameter
\[
\gamma=1.
\]

For repo discipline, this should be labeled as:

* **constitutive weak-field bridge** if you want conservative canon language,
* not "full GR derivation complete" unless you've independently closed the field-equation side.

---

## 5. CK-0 and contract-residual instantiations

> **Tag**: `[INSTANTIATION]`

Section III should also leave room for contract-driven systems, because the canon explicitly defines CK-0 as a full subcategory of Coh.

A canonical CK-0 scalarization is
\[
V(x)=\sum_{i=1}^m w_i r_i(x)^2,
\qquad w_i>0.
\]

This is in the Coh canon and interface contract.

So Section III should not be written as though only PDEs matter. It should define domain instantiations broadly enough to include:

* PDE solver theories,
* geometric mechanics,
* residual-verified runtime systems,
* and bounded hybrid systems like RCFA.

The RCFA file is one such example:
\[
\mathcal X=\mathcal Z\times \mathcal A\times [0,B_{\max}],
\]
with risk functional $V$, budget $b$, renormalization operator $R$, and refinement operator $U$.

So the general theorem is that Section III hosts all **Coh-valid module realizations**, not just the glamorous physics beasts.

---

## 6. Canonical mathematical structure of Section III

### [DEFINITION] Domain-instantiated Coh object

A domain solver theory is a tuple
\[
\mathcal S_{\mathrm{dom}}
= (X_{\mathrm{dom}},V_{\mathrm{dom}},\mathrm{Spend}_{\mathrm{dom}},\mathrm{Defect}_{\mathrm{dom}},\mathrm{RV}_{\mathrm{dom}},\mathcal P_{\mathrm{dom}})
\]
satisfying the universal Coh soundness law and interface contract.

### [INSTANTIATION] NS-PCM PDE object

\[
\partial_t u+(u\cdot \nabla)u+\nabla p=\nu\Delta u,\qquad \nabla\cdot u=0
\]

with vorticity equation
\[
\partial_t\omega+(u\cdot \nabla)\omega=(\omega\cdot \nabla)u+\nu\Delta\omega.
\]

### [PROVED] Enstrophy balance

\[
\frac12\frac{d}{dt}|\omega|_2^2+\nu|\nabla\omega|_2^2
= \int (S\omega)\cdot \omega\,dx.
\]

### [INSTANTIATION] Boundary-bleed obstruction

\[
B_k(\delta)=|S_{k-1}\rho_\varepsilon^{\mathrm{out}}|_{L^\infty(A_\delta)}.
\]

### [HYPOTHESIS] Besov-SSL boundary regularity

\[
\sup_k 2^{sk}|\Delta_k f_\delta|_{L^1}\le C_{\mathrm{SSL}}.
\]

### [PROVED UNDER HYPOTHESIS] Closure theorem

If Besov-SSL holds, the low-frequency obstruction is absorbable by dissipation.

### [DIAGNOSTIC] Millennium gate

\[
\mathcal Q_\delta(t)
= \frac{\delta^2\int_{A_\delta}|S(u)|_{\mathrm{op}}dx}{\nu|\nabla\omega|_{L^2}^2}<1.
\]

### [INSTANTIATION] Relativistic barrier object

\[
\widetilde V(v)=-\frac12\log\left(1-\frac{|v|^2}{c^2}\right).
\]

\[
\frac{d\tau}{dt}=e^{-\widetilde V(v)}
= \sqrt{1-\frac{|v|^2}{c^2}}.
\]

### [PROVED] Minkowski interval

\[
d\tau^2=dt^2-\frac{dx^2}{c^2}.
\]

### [PROVED] Relativistic momentum law

\[
p=\gamma_v m v.
\]

### [PROVED] Minimal-coupling Lorentz force

\[
\frac{d\mathbf p}{dt}=q(\mathbf E+\mathbf v\times \mathbf B).
\]

### [CONSTITUTIVE BRIDGE] Gravitational lapse law

\[
N(x)=\sqrt{b+\alpha\mathcal D_a},
\qquad
\gamma_{ij}=\alpha \mathcal R_{ij}.
\]

### [WEAK-FIELD BRIDGE] Scalar budget gravity

\[
b(x)\approx 1-\frac{2GM}{rc^2},
\qquad
\gamma_{ij}\approx \left(1+\frac{2GM}{rc^2}\right)\delta_{ij}.
\]

---

## 7. Repo-ready canonical writeup for Section III

---

# Section III — Domain Instantiations and Verified Solver Theories

A domain instantiation of Coh is a concrete module
\[
\mathcal S_{\mathrm{dom}}
= (X_{\mathrm{dom}},V_{\mathrm{dom}},\mathrm{Spend}_{\mathrm{dom}},\mathrm{Defect}_{\mathrm{dom}},\mathrm{RV}_{\mathrm{dom}},\mathcal P_{\mathrm{dom}})
\]
that realizes the universal governance laws of Sections I and II inside a specific mathematical domain. The module must provide a domain state space, a scalar obstruction or residual functional, a verified irreversible spend law, a defect law, a deterministic receipt verifier, and a constitutive domain dynamics package. Every accepted transition must satisfy the Coh soundness inequality
\[
V_{\mathrm{dom}}(x')+\mathrm{Spend}_{\mathrm{dom}}(r)
\le
V_{\mathrm{dom}}(x)+\mathrm{Defect}_{\mathrm{dom}}(r).
\]

For the Navier–Stokes instantiation, let
\[
u:[0,T]\times \mathbb T^3\to\mathbb R^3
\]
be divergence free and satisfy
\[
\partial_t u+(u\cdot \nabla)u+\nabla p=\nu\Delta u.
\]

With vorticity $\omega=\nabla\times u$, the induced vorticity law is
\[
\partial_t\omega+(u\cdot \nabla)\omega=(\omega\cdot \nabla)u+\nu\Delta\omega.
\]

The exact enstrophy identity is
\[
\frac12\frac{d}{dt}|\omega|_2^2+\nu|\nabla\omega|_2^2
= \int (S\omega)\cdot \omega\,dx.
\]

Thus regularity reduces to domination of vortex stretching by viscous dissipation. Under the regularized decomposition
\[
\omega=\rho_\varepsilon\xi_\varepsilon,
\qquad
\rho_\varepsilon=\sqrt{|\omega|^2+\varepsilon^2},
\qquad
\xi_\varepsilon=\omega/\rho_\varepsilon,
\]
the remaining obstruction is localized into low-frequency boundary bleed across the weak-vorticity set $A_\delta=\{|\omega|<\delta\}$. The decisive geometric hypothesis is the Besov-SSL regularity of the interface indicator $f_\delta=\mathbf 1_{A_\delta}$, which yields dyadic decay of the bleed term and absorbability of the low-frequency obstruction. The corresponding dimensionless verification diagnostic is
\[
\mathcal Q_\delta(t)
= \frac{\delta^2\int_{A_\delta}|S(u)|_{\mathrm{op}}dx}{\nu|\nabla\omega|_{L^2}^2}.
\]

A verified interval with $\mathcal Q_\delta(t)<1$ lies in the non-blow-up regime certified by the dissipative ledger.

For the relativistic instantiation, impose the admissible velocity ball $|v|<c$ and define the half-log barrier
\[
\widetilde V(v)
= -\frac12\log\left(1-\frac{|v|^2}{c^2}\right).
\]

The induced viability density is
\[
e^{-\widetilde V(v)}=\sqrt{1-\frac{|v|^2}{c^2}},
\]
so the root-clock satisfies
\[
d\tau=\sqrt{1-\frac{|v|^2}{c^2}}\,dt,
\qquad
d\tau^2=dt^2-\frac{dx^2}{c^2}.
\]

Thus special-relativistic proper time appears as the barrier-generated intrinsic clock. With the Lagrangian
\[
L(v)=-mc^2 e^{-\widetilde V(v)},
\]
the Legendre transform yields the relativistic momentum law
\[
p=\gamma_v m v.
\]

Adding a 1-form bias $A_\mu=(-\phi,\mathbf A)$ by
\[
L'=L+q(\mathbf v\cdot \mathbf A-\phi)
\]
produces the Lorentz force equation
\[
\frac{d\mathbf p}{dt}=q(\mathbf E+\mathbf v\times \mathbf B).
\]

For the gravitational constitutive bridge, define the lawfulness power
\[
\Lambda(x)=b+\alpha\mathcal D_a\ge 0.
\]

The ADM lapse is identified as
\[
N(x)=\sqrt{\Lambda(x)},
\]
while the spatial metric is generated from a symmetric positive-definite resistance operator by
\[
\gamma_{ij}(x)=\alpha\mathcal R_{ij}(x).
\]

In the weak-field scalar-budget model with
\[
\mathcal R_{ij}=b^{-1}\delta_{ij},
\qquad
b(x)\approx 1-\frac{2GM}{rc^2},
\]
the spatial metric expands as
\[
\gamma_{ij}\approx \left(1+\frac{2GM}{rc^2}\right)\delta_{ij},
\]
giving the constitutive weak-field bridge to the standard relativistic gravitational regime.

More generally, contract-residual systems such as CK-0 modules and bounded hybrid systems such as RCFA also live in this section, provided they implement the same deterministic receipt law, canon profile, and soundness inequality.

---

## 8. Honest status flags for Section III

This section is strong, but it should be labeled carefully.

### Cleanly supported by the archive

* NS vorticity foundation
* enstrophy identity
* low-frequency obstruction framing
* boundary bleed decomposition
* Besov-SSL conditional closure theorem
* $\mathcal Q_\delta$ diagnostic
* half-log barrier to proper time
* relativistic momentum law
* minimal-coupling Lorentz force
* lapse/resistance constitutive bridge

### Should remain tagged as conditional or constitutive

* unconditional global Navier–Stokes closure
* full Einstein-field-equation derivation from budget geometry
* any empirical claim stronger than the weak-field constitutive bridge already shown in the source

---

## 9. Code Implementation Reference

The following modules implement the concepts in this section:

| Module | Implements |
|--------|------------|
| `core/relativistic_dynamics.py` | Half-log barrier, Minkowski interval, Lorentz boost |
| `core/gr_solver.py` | Gravitational constitutive bridge |
| `core/potential.py` | Domain violation functional |

See individual module docstrings for `[INSTANTIATION]`, `[PROVED]`, `[HYPOTHESIS]`, `[CONSTITUTIVE BRIDGE]`, and `[WEAK-FIELD BRIDGE]` tags.

---

*This document is the canonical source for Section III — Domain Instantiations and Verified Solver Theories.*
