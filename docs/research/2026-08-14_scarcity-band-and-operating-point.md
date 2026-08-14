# RESEARCH REQUEST #8 — Can a common-pool resource have a *graded* scarcity
# regime, and how is a measurement point chosen without tuning to the outcome?

Date: 2026-08-14 · Target tool: OpenAI Deep Research
⚠ Written in English on purpose: this is a literature + mathematics request,
and every previous answer came back in English anyway.

---

## 0. HOW TO READ THIS REQUEST

**What we need:** (a) a check of a short piece of mathematics we did
ourselves, (b) established mechanisms from bioeconomics / resource ecology /
agent-based modelling that produce the regime we cannot produce, (c)
established methodology for choosing *when* to measure and *what parameter
value* to run at, when both choices could be accused of being fitted to the
result.

**What we do NOT need:**

- Our project history. You have no access to it.
- A prediction of what our setup will produce. Choosing a design by
  anticipating its effect is post-hoc.
- Code. We write the implementation ourselves.

### SOURCE DISCIPLINE — our record is poor and we now know why

Across seven previous requests we hit two distinct failure modes.

**Failure mode 1 — wrong identity.** Nine citations turned out to be
misattributed: DOIs pointing at a different paper, a journal ISSN used as a
"source", an invented author list on a real arXiv number, and one dead DOI.

**Failure mode 2 — right source, wrong claim.** Sources were real, DOIs
resolved, but the claim was not in them. Verifying the DOI does **not** catch
this.

So from the last round we additionally ask **where** in the source each claim
appears. That change worked: we could finally place each claim next to its
own quotation, and **three of six claims turned out to say something their
own quotation did not**. Two refinements this round:

1. ⭐ **Give a bibliography.** Last time the answer used internal reference
   numbers (`[56]`, `[58]`, …) with no bibliography attached, so one claim
   could not be traced to any paper at all and was discarded.
2. ⭐ **Quote verbatim; do not give line numbers.** Last time "lines 249–253"
   pointed at nothing — the same sentence sat at line 313 of our extraction.
   Line numbers do not survive between copies. **The verbatim quotation is
   what made verification possible.** Section name + short quotation, please.

This is not an accusation — we made the same class of error ourselves: in one
of our own local scans we wrote the wrong DOI for a sampling paper, opened it,
found a different article, and corrected it.

**We open every DOI/arXiv identifier through Crossref, and we do not use a
claim whose location cannot be shown.**

---

## 1. THE SYSTEM

A population of software agents shares one renewable resource pool. Time is
event-ordered (integer counter; no wall clock). Each event, every agent
announces an action; a deterministic mapping (no LLM judge) turns the action
into a harvest quantity.

### 1.1 The pool

Logistic renewal, then harvest, then clamp:

```
regenerated_t = P_t + r · P_t · (1 − P_t / K)
granted_t     = allocation_rule( regenerated_t , {d_i} )
P_{t+1}       = clamp( regenerated_t − Σ_i granted_t,i , 0 , K )
```

with, per agent:

| symbol | value | note |
|---|---|---|
| `r` | 0.15 | renewal rate per event |
| `K` | 100.0 | carrying capacity (per agent, see §1.4) |
| `P_0` | 80.0 | initial stock = 0.8·K |
| `d_i` | **8.0** | harvest demanded by the dominant action |

Other actions demand 2.0, 1.0 or 0.0, but **94–100 % of all observed events
take the 8.0 action** (measured in our own pilot), so the analysis below
treats demand as 8.0 per agent per event.

`allocation_rule` is currently proportional sharing of any shortfall. We are
considering replacing it with **sequential access with a rotating order** —
that is the design question that started this.

### 1.2 The harvest → energy link

```
gain(x) = G_max · x / (H + x) ,  G_max = 0.50 , H = 2.0
```

Concave and saturating, deliberately (a proportional link would leave
over-extraction strictly dominant). Realized harvest, never the announced
amount: an empty pool feeds nobody. Energy falls each event by a fixed
metabolic cost; when it reaches zero the agent's life ends.

### 1.3 The measurement point

The primary endpoint is read at a **fixed event ordinal L = 10**, identical
for every lineage. `L` is not free: death is suspended for the first 10
events (a birth-transient grace window), and `L` is anchored to the end of
that window precisely so that **every lineage reaches the measurement point**
and nothing is censored. Observed lifespans are 11–20 events.

### 1.4 Population

We are moving from one lineage to N agents (target: tens of individuals,
single-digit generations). We intend to scale `K` and `P_0` linearly with N,
holding the per-agent numbers above fixed.

### 1.5 CONSTRAINTS WE CANNOT RELAX

- **No trait injection.** No personality/tendency value may be assigned to an
  agent. Every difference must arise from what the agent lived. This is an
  axiom of the project.
- **No behavioural priors.** We may not instruct agents toward any decision
  rule, and we may not intervene to fix the observed over-extraction. The
  collapse is reported as a finding, not corrected.
- **No LLM judge.** All metrics are deterministic Python.
- **Reproducibility is enforced by a gate:** *the same seed with the same code
  must produce the same result.* ⚠ **This does not mean one seed.** We run
  many independent seeds — the last confirmatory run used 40. A previous
  answer misread this constraint; please do not repeat that reading.
- **Event-ordered time only.** No wall clock.

If a proposal violates one of these, **still give it**, but mark which one.
Knowing the price of relaxing a constraint beats not seeing the option.

---

## 2. THE MATHEMATICS WE DID — PLEASE CHECK IT

We need heterogeneity between agents to arise from competition for a
depleting resource. That requires a **scarcity regime**: a stretch of events
in which the pool cannot satisfy everyone but is not yet dead, so that who
harvests first matters repeatedly. We derived that no such stretch exists.
Please verify or refute each step.

**(a) Maximum sustainable yield.** For the logistic map above, renewal is
maximised at `P = K/2` and equals `r·K/4` = **3.75 per agent per event**.
Demand is **8.0**. Demand exceeds maximum renewal by a factor of 2.13.

**(b) Sustainability threshold.** Setting `r·P·(1−P/K) = d` gives
`P = (K/2)·(1 ± √(1 − 4d/(rK)))`. Real roots exist iff `K ≥ 4d/r` =
**213.33 per agent**. So:

- `K < 213.33` → no equilibrium; the stock declines monotonically to zero.
- `K > 213.33` → two equilibria (upper stable, lower unstable). Starting at
  0.8·K the stock converges to the **upper stable** level and stays there.

**(c) The consequence we cannot get around.** Below the threshold the pool
collapses; above it, scarcity never occurs at all. **Neither region contains
a graded scarcity regime.**

**(d) Zero is absorbing.** Logistic growth from `P = 0` is 0. In the single
event where demand first exceeds availability, the agents jointly take
everything available (whatever the allocation rule), so the pool is emptied
in that same event and never recovers.

**(e) Therefore: exactly one partially-satisfied event per life**, whatever
the initial stock. Changing `P_0` or `K` only moves *when* that event happens,
not how long it lasts. Worked values (per-agent `K`, `P_0 = 0.8K`), giving the
ordinal of the single partial event:

| K per agent | 40 | 50 | 60 | 67 | 70 | 80 | 100 |
|---|---|---|---|---|---|---|---|
| partial event at | 5 | 7 | 8 | **9** | 10 | 12 | **17** |

With today's `K = 100` the single partial event falls at ordinal 17 — i.e.
**after** the measurement point L = 10, so at the moment we measure, all
agents are still identical by construction.

**(f) The bind.** `L = 10` cannot move later without losing the no-censoring
guarantee (§1.3). The scarcity event cannot be made to last longer (d). So
the only remaining lever is `K`, and choosing `K = 67` because it puts the
scarcity event at ordinal 9 is uncomfortably close to selecting a constant so
that the measurement lands where the mechanism fires.

---

## 3. QUESTIONS

### Q1 — Is §2 correct, and is there a parameter region we have missed?

Check (a)–(e). Specifically:

- Is the threshold `K ≥ 4d/r` the standard bioeconomic result, and under what
  name?
- **Near-critical slowing:** if demand is set just barely above maximum
  renewal, does the stock spend many events crawling through the bottleneck
  near `P = K/2` (the delay associated with a saddle-node / fold), producing
  in effect a long graded regime? If so, how many events, how does that scale
  with the excess `d − rK/4`, and how fragile is it to perturbation?
- Does the discrete-time formulation change any of this relative to the
  continuous-time one?

### Q2 — What produces graded scarcity **without** changing agent behaviour?

Our harvest is a **fixed quantity** independent of stock. We suspect this is
what makes collapse a cliff rather than a slope.

- In fisheries / resource ecology, what are the standard alternatives —
  stock-proportional catch, Holling-type functional responses, escapement or
  refuge rules, stock-dependent search efficiency?
- For each: does it produce a *prolonged* interval of partial satisfaction,
  and has that been **measured** (simulation or empirical) rather than
  asserted?
- ⚠ Which of these can be stated as a property of the **environment** rather
  than of the agent's decision rule? That distinction decides whether we may
  use it at all (§1.5, no behavioural priors).

### Q3 — Measuring at a fixed age when the mechanism turns on later

We measure every lineage at the same ordinal so that arms are comparable and
nothing is censored by death. But the mechanism of interest may not have
engaged by then.

- How is this handled in experimental evolution / life-history studies:
  fixed-age measurement versus measurement at a fixed physiological state or
  event, and what is the accepted vocabulary for each?
- If measuring later means some individuals have died, what is the standard
  treatment when that death is **informative** (correlated with the very
  quantity being measured)?
- Is there a defensible way to hold a fixed-age endpoint **and** capture a
  mechanism that engages after it — e.g. a fixed-age primary plus a
  post-onset rate as a declared secondary?

### Q4 — Choosing a parameter so a mechanism is *in range*, without it being tuning

We would set `K` so that scarcity occurs inside the observation window. The
value would be derived from an inequality over constants declared before any
run, with no data entering — but it is still chosen so the mechanism fires.

- Is there an accepted term and practice for this (operating point selection,
  design for detectability, manipulation check, positive control)?
- Where is the line drawn in reporting guidelines between *"parameter set so
  the mechanism is active"* and *"parameter fitted to the outcome"*?
- Are there worked examples of a pre-registration or simulation-study
  protocol that declares such a choice explicitly, and how is it justified in
  the text?

### Q5 — How many competition events does a selection estimate need?

If differentiation arises only in a small number of events, we want to know
the floor.

- For a selection differential expressed as a covariance between relative
  reproductive success and a trait (Price-equation form), what is known about
  estimability and bias at small population size and few episodes of
  selection?
- Is there measured guidance on the minimum number of selection episodes
  before such an estimate is interpretable?
- ⚠ We are **not** asking what effect size we will get. We are asking what
  makes the estimate defined rather than degenerate.

---

## 4. FORMAT OF THE ANSWER

For every claim, five things:

1. **What is claimed.** One sentence.
2. **Source.** Author, year, DOI or arXiv id. If unsure, write
   *"identity not verified"*.
3. **Where in the source.** Section name, figure/table number, **and a short
   verbatim quotation**. ⚠ **Do not give line numbers** — they do not survive
   between copies. If you cannot locate it, write *"cannot show where this
   appears in the source"*. We will not use a claim without this.
4. **Type of evidence.** Measured experiment, simulation, or theoretical
   proposal.
5. **Applicability to our setup.** Which assumption does it break?

⭐ **Attach a bibliography** mapping every reference marker you use to a full
citation. Last round an internal marker with no bibliography entry cost us an
entire claim.

If a proposal violates one of the constraints in §1.5, still give it and
**mark which one**.

⚠ **If anything in §2 is wrong, say so plainly and show the correction.** In
previous rounds the single most valuable line we received was the one that
refuted an assumption of ours. A clean *"your derivation is right and there
is no way around it"* is also a usable answer — it tells us the constraint is
structural rather than a gap in our reading.

---

## 5. DELIBERATELY OUT OF SCOPE

- Where between-agent heterogeneity comes from in general. Answered last
  round.
- Arm contamination and isolation of a shared pool. Answered.
- Endpoint definition and censoring in the general case. Answered.
- Fixing the agents' over-extraction. Closed by axiom.
- Learning rate, model choice, quantization. Measured and frozen.
