# DR #8 — ham cevap (değiştirilmeden)

**Brief:** `2026-08-14_scarcity-band-and-operating-point_PLAIN.txt`
(gönderilen biçim: `_SHORT-A.txt` ve `_SHORT-B.txt`, iki ayrı koşum).
**Alındı:** 2026-08-14, Yasin arka arkaya iki parça hâlinde yapıştırdı.
**Mutabakat:** `RECONCILIATION.md` §P · kayıt **D-082**

⚠ Aşağısı **ham metindir**, tek harfi değiştirilmedi. Doğrulama §P'de.

---

## A — matematik (SHORT-A'nın cevabı)

# Key Claims and Evidence

- **Maximum Sustainable Yield (MSY):** In the logistic constant-yield model, the highest sustainable harvest occurs at half the carrying capacity, yielding $H_{\rm MSY}=rK/4$ (so here $3.75$ when $r=0.15,K=100$). *(Azar et al., 1996, DOI:10.1007/BF00699291, *Constant Quota vs Constant Effort*: "At MSY, we have $X_{MSY}=K/2$ and $H_{MSY}=Kr/4$.")*

- **Equilibria and Collapse:**  If the fixed harvest $H<rK/4$, two equilibria exist (an upper stable stock and a lower unstable "collapse threshold"); if $H>rK/4$, no positive equilibrium remains.  In other words, exceeding $rK/4$ causes inevitable collapse. *(Azar et al., 1996; **Constant Quota vs Constant Effort**: "At MSY... $H_{MSY}=Kr/4$," and "constant quota harvesting is at the lower limit – any disturbance that decreases the population size leads to extinction.")*

- **Saddle‐Node (Fold) Bifurcation:** The transition at $H=rK/4$ is a classic saddle-node (fold) bifurcation: the stable and unstable equilibria coalesce and disappear.  Near this point, the dynamics exhibit critical slowing ("bottleneck" effect) due to the "ghost" of the vanished equilibrium.  *(Gomez 2018, DPhil thesis, DOI:10.5287/ora-jv6j78zbd, *Abstract*: "time delay near the pull-in transition is a type of critical slowing down – a so-called 'bottleneck' due to the 'ghost' of a saddle-node bifurcation.")*

- **Constant‐proportion (Effort) Harvest:** Harvest proportional to stock (constant effort) always admits a positive equilibrium for any harvest rate $h<r$ (the equilibrium $P^*=(r-h)K/r$).  Collapse only occurs if $h\ge r$, i.e. only when harvest exceeds the intrinsic growth rate. *(Atwood 2020, wildlife textbook; **Harvesting Model**: "a fixed proportional harvest always has a positive equilibrium population unless $h>r$.")*

- **Constant‐quota vs. Effort:**  Unlike fixed‐quota harvests, constant‐effort rules have no strict lower threshold.  As Azar et al. note, "notice that there is no lower limit for the constant effort case, but constant quota harvesting is at the lower limit – any disturbance that decreases the population size leads to extinction".  In practice this means constant‐proportion harvesting allows gradual decline/recovery, whereas fixed quotas cause abrupt collapse once the stock falls below the collapse threshold. *(Azar et al., 1996, DOI:10.1007/BF00699291, *Results*: "no lower limit for the constant effort case, but constant quota harvesting… any disturbance…leads to extinction.")*

- **Escapement (Threshold) Harvesting:**  In models where a minimum stock $T$ is preserved (escapement rule), if $T\le K$ the population will stabilize at $T$ and never collapse.  In particular, Hilker & Liz (2020) show that "if $T\le K$, then $T$ is the unique positive equilibrium… and it is a global attractor" (no collapse as long as threshold is below carrying capacity). *(Hilker & Liz 2020, DOI:10.1007/s12080-020-00465-8, *Prop.2.1*: "If $T\le K$, then $T$ is the unique positive equilibrium… and it is a global attractor.")*

**Evidence Types:** The above claims are supported by mathematical analysis of logistic harvest models (e.g. Azar et al. on equilibria, Gomez on bifurcation dynamics, Hilker & Liz on threshold rules) and represent theoretical results. (Empirical studies of such functional responses are sparse; most statements here come from analytical models.)

---

## B — yöntem (SHORT-B'nin cevabı)

# Fixed-age vs fixed-state measurement
- **Vocabulary:** Clinical trial nomenclature distinguishes a **"fixed study time"** (measuring at a predetermined time) from a **"fixed event time"** (measuring at a specific biological event). For example, one design assesses outcomes at a fixed post-randomization time, whereas another waits until a defined event (e.g. childbirth) occurs. *(Source: National Research Council 2010, Appendix A; theoretical overview)*.
- **Competing risks (death):** When measurement is delayed and some individuals die first, the situation is treated as a *competing-risk* problem.  Outcomes are then defined as "time to [the desired] event, provided it occurs before a competing event that precludes measurement". In other words, death before measurement "precludes" the event of interest and cannot be treated as random censoring. *(Source: NRC 2010, Appendix A; theoretical)*.
- **Informative censoring:** If early deaths are correlated with the trait of interest, standard practice in life-history studies is to avoid excluding them.  For example, Maklakov & Chapman (2021) note that although censoring early "matricidal" deaths is common in aging studies, they argue it is "very important to include all deaths" to correctly infer evolutionary effects. Excluding such deaths would bias results if mortality is **informative** (i.e. linked to the process being measured). *(Source: Maklakov & Chapman 2021, Evolution Letters; experimental measurement)*.
- **Multiple endpoints:** One can keep a fixed-age primary endpoint and add secondary measures to capture late-onset effects.  In trial designs this is done via composite or co-primary outcomes. For instance, a composite "bad outcome" might be defined as the first occurrence of any of several events. By analogy, an experimental evolution study could pre-specify a fixed-age endpoint (primary outcome) and also report a post-onset rate or time-to-event (secondary endpoint), as long as these are declared a priori. *(Source: NRC 2010, Appendix A; theoretical guidelines)*.

# Parameter choice and pre-registration (Q2)
- **Pre-specification:** Best practice is to pre-specify all design elements (including parameter values) before data collection.  Pre-registration "aims to enhance the trust" in research by fixing the protocol (hypotheses, outcomes, analysis plan) in advance, making any deviations transparent. In simulation or experimental design, this means declaring in the protocol which constants will be used (and why) without peeking at outcomes. *(Source: Ioannidis 2022, Adv. Theor. Simul., "Abstract"; theoretical discussion)*.
- **Design focus:** In simulations, guidelines emphasize focusing on the *design* of the study (data-generating mechanism and key parameters) up front. Siepe et al. (2024) stress that preregistration templates "place considerable focus on the design of the simulation study (e.g. the data-generating mechanism…)" as a major source of flexibility. In practice, this means choosing environment parameters by theoretical reasoning (e.g. an inequality that guarantees the mechanism will fire) rather than by fitting to pilot data. *(Source: Siepe et al. 2024, ADEMP-PreReg Simulation Template; methodological recommendation)*.
- **Positive/Manipulation checks:** It is common to include "positive control" conditions to ensure an experiment can detect an effect.  A positive control is a case known to produce a positive result and thus "confirms that the experiment is capable of producing results under the experimental conditions".  By analogy, selecting parameters so that the mechanism (competition) **will** engage acts as a positive control for detectability. *(Source: Földesi 2021, Rockland Inc. article "Positive and Negative Controls"; descriptive)*.
- **Reporting guidelines:**  Regulatory guidance (e.g. CONSORT for trials) requires that primary and secondary outcomes be fully prespecified in the protocol.  Consistent with this, CONSORT states that reported outcomes "should be consistent with the outcomes prespecified in the trial protocol" and that any changes must be explained.  By extension, choosing parameters a priori (with logical justification) is acceptable, but changing them post hoc to force an effect would be disallowed. *(Source: Moher et al. 2010, CONSORT 2010 Explanation; guideline advice)*.

# Selection differential in small populations (Q3)
- **Stochastic amplification:** In very small populations or under strong stochastic variation, the sample covariance form of the selection differential can be highly unstable.  Rice (2008) shows that "in a very small population" random fluctuations cause the expected selection differential to be **amplified** relative to classical predictions. In practice, this means the covariance between relative fitness and trait may be much larger (or smaller) than expected from deterministic theory, leading to bias. *(Source: Rice 2008, BMC Evol. Biol., section "Amplification in small populations"; theoretical + simulation)*.
- **Estimability:** No simple rule exists for a minimum number of selection episodes.  However, with only one or very few episodes the estimated selection differential is essentially a single-sample covariance, which can be zero or undefined if mean fitness is extreme.  Larger sample sizes or multiple independent selection events are required for a reliable estimate.  (In statistical terms, each new episode gives another replication of the covariance estimate, reducing sampling variance.) *(No specific claim found in sources – inference from population genetics theory.)*

**Bibliography:**
- National Research Council (2010) *The Prevention and Treatment of Missing Data in Clinical Trials*, Appendix A: Clinical Trials Terminology. DOI:10.17226/12955.
- Ioannidis JPA (2022) "Pre-registration of mathematical models," *Adv. Theor. Simul.* 5(1): article 2100182. DOI:10.1016/j.mbs.2022.108782.
- Maklakov AA & Chapman T (2021) "Ageing as 'early-life inertia': Disentangling life-history trade-offs along a lifetime," *Evolution Letters* 5(5):551–564. DOI:10.1002/evl3.254.
- Siepe BS, Bartoš F & Pawel S (2024) *ADEMP-PreReg: A preregistration template for simulation studies* (preprint/guideline).
- Földesi B (2021) "Positive and Negative Controls," *Rockland Immunochemicals Resources* (Dec 14, 2021).
- Moher D et al. (2010) "CONSORT 2010 Explanation and Elaboration" (Lancet 375:1133–1143).
- Rice SH (2008) "A stochastic version of the Price equation reveals the interplay of..." *BMC Evolutionary Biology* 8:262.
