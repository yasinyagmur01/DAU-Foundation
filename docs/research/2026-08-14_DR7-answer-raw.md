# DR #7 — ham cevap (değiştirilmeden)

**Brief:** `2026-08-14_heterogeneity-among-identical-agents_PLAIN.txt`
**Alındı:** 2026-08-14, Yasin sohbete yapıştırdı.
**Mutabakat:** `RECONCILIATION.md` §O · kayıt **D-080**

⚠ Aşağısı **ham metindir**, tek harfi değiştirilmedi. Doğrulama §O'da.

---

- **Claim:** Spatial heterogeneity causes identical agents to diverge.  For example, Schelling’s segregation model shows that agents with identical preferences will nonetheless form distinct clusters when placed in space.  
  **Source:** Schelling (1971) (J. Math. Sociol.) via JASSS and Gilbert (2002, Agent 2002), no DOI.  
  **Location:** In [56], Sec.1 (intro) lines 6–10: “Schelling’s model illustrates how … segregation can emerge even if individuals are only weakly segregationist.”  In [22], pg.7 lines 346–354: “all the agents are identical, except for their location … they all have exactly the same tolerance.”  
  **Evidence:** Simulation of the Schelling model (and similar ABMs) demonstrates emergent segregation.  
  **Applicability:** This mechanism fits our setup if we introduce a spatial structure or local resource variation (no constraint violated).  In a non-spatial model it doesn’t apply, but with space it shows how identical decision rules can produce heterogeneity.  

- **Claim:** Sequential (asynchronous) resource access creates order effects: first movers gain an advantage regardless of behavior.  In sequential public-goods/commons games, experiments consistently find a strong “first-mover advantage” – e.g. first movers contribute more (or harvest more) than later movers.  
  **Source:** Nishimura et al. (2024, arXiv:2308.00179) – cites multiple exp. studies (Rapoport, Budescu, etc.).  
  **Location:** [58] lines 249–253 notes “this literature has identified significant ordering effects”; lines 267–270 state “robust evidence of first movers contributing more than later movers.”  
  **Evidence:** Laboratory experiments on sequential public-good/common-pool games.  
  **Applicability:** If we use a sequential harvest rule, agent *order* (position) will create heterogeneity that isn’t due to agent strategy.  This violates the ideal that only behavior causes differences.  It’s a design confound: the advantage comes purely from sequence position, not agent rule.  

- **Claim:** Experimenters refer to this as an “order effect,” and typically eliminate it by randomizing or rotating agent order.  For instance, Bru et al. (2003) explicitly randomized treatment order “to control for order-of-treatment effects”.  
  **Source:** Bru et al. (2003, *Experimental Economics*, DOI:10.1023/A:1024209010570).  
  **Location:** [39] lines 1092–1099: “The order of the treatments was changed in each session with the objective of controlling for order-of-treatment effects.”  
  **Evidence:** Experimental protocol/design statement.  
  **Applicability:** In our ABM, we could similarly cycle which agent harvests first each generation to break positional bias (no rule violation).  If we do not randomize, positional bias remains.  Rotating order may not fully eliminate subtle history effects, but it’s standard practice.  

- **Claim:** No fixed “magic number” of generations guarantees cumulative evolution; convergence generally scales with problem complexity.  Theoretical iterated-learning models show that equilibrium is reached after roughly $O(n\log n)$ generations (with $n$ the number of parameters), not a small constant.  
  **Source:** Rafferty et al. (2009, *CogSci/J. AI Research*, arXiv:0810.3070) – iterated learning convergence bounds.  
  **Location:** [51] lines 75–83: “iterated learning with a uniform prior reaches equilibrium after $O(n\log n)$ generations…”  
  **Evidence:** Mathematical analysis of a Bayesian iterated-learning model (theory).  
  **Applicability:** Suggests that ‘cumulative’ effects require many generations as model complexity grows.  There is no universal minimal generation count; it depends on the size and learning biases in the system.  This is theoretical (no immediate run-time effect) and violates no constraints.  

- **Claim:** Agent-based modeling requires multiple Monte Carlo runs for statistical robustness: one “experiment” should be repeated with different random seeds.  
  **Source:** Lee et al. (2015, *J. Artificial Soc. Social Simulation* 18(4):4, DOI:10.18564/jasss.2897).  
  **Location:** [69] lines 135–140: “an ABM is typically a stochastic process and thus requires Monte Carlo sampling…each experiment is multiply performed using distinct pseudo-random sequences…to achieve the statistical robustness necessary.”  
  **Evidence:** Methodological guideline/discussion.  
  **Applicability:** Our requirement of strict reproducibility (one seed per run) *violates* this principle.  We cannot change seeds if we need runs to be identical.  In practice, more replicates would reduce noise and allow distinguishing small effects.  This highlights that our one-seed constraint means we forego statistical averaging, which undermines power (but we keep it for determinism).  

- **Claim:** However, producing excessively many runs can lead to “absurd” precision: extremely trivial differences become statistically significant.  
  **Source:** Lee et al. (2015, same as above).  
  **Location:** [63] lines 24–30: “expedient ABMs… may produce far greater sample counts…increasing the sensitivity of statistical tests possibly to the point of absurdity.”  
  **Evidence:** Methodological analysis discussion.  
  **Applicability:** Under a fixed compute budget, this advises balancing replication: do enough runs to get stable estimates, but beyond that additional runs yield diminishing insight.  We should choose replicates so that sample variance stabilizes.  This does not violate constraints, but suggests not to “over-replicate” to absurd precision (though with one run we under-replicate).
