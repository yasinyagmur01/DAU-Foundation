# DAU — Master Reference

**Versiyon 2.2** · 2026-08-07  
**Dosya:** `docs/DAU_MASTER_REFERENCE_v20.{md,html,pdf}`  
*(`.html` / `.pdf` türevleri v2.2 için henüz yeniden üretilmedi — md kaynaktır)*  
*(eski `v10` / Versiyon 1.x belge ailesi süpersede edildi — arşiv olarak kalabilir)*

Layer 0–5 kod ✅ · MiniLM PE · DAERM · Protocol C **paper-locked negative
finding** · C′ N=15 (eski reçete) **INSTRUMENT_LIMITED_NULL** · C′ düzeltme
zinciri + mini-testler → **SAMPLE_LIVED_PE_SEPARATION** (N=1, sampling +
yaşam-PE tercih) · **ADIM 1–6 kodlandı** · bu branch’te **177 test**.

**İddia disiplini:** Layer 5 **kod** ✅ · frozen-weight kapalı döngü
metacognition **UNSUPPORTED (paper-locked null)** · C′ N=15 eski koşum
(**INSTRUMENT_LIMITED_NULL** — alet bozukken alınmış; etki iddiası değil) ·
düzeltme sonrası tek-seed sampling+B: lived ΔPE=−0.180 · null=0.000 ·
shuffle=−0.149 · sıra `lived < shuffle < null` (**SAMPLE_LIVED_PE_SEPARATION**;
significance yok; N=15 henüz yok).
`DAU_LORA_ENABLED=0` · `DAU_LLM_BACKEND=groq` default · C′ local koşumda
`DAU_LLM_DO_SAMPLE=1` + `DAU_LLM_TEMPERATURE=0.2`.

**Faz 0 kilit:** Frozen Protocol C null **paper-locked**; full Groq
Protocol C tekrar yok.

**Plastisite / ADIM durumu (v2.2):**
- Flags: `DAU_LLM_BACKEND=groq|local` (default groq), `DAU_LORA_ENABLED=0`,
  `DAU_NLI_FILTER_ENABLED=1`, `DAU_LLM_DO_SAMPLE=0` (C′ için `=1`),
  `DAU_LLM_TEMPERATURE` / `DAU_LLM_SEED` / `DAU_TORCH_THREADS`.
- VRAM: Llama-3.1-8B 4-bit + MiniLM + QLoRA; DPO `BATCH_SIZE=1` +
  gradient checkpointing ile **8GB kartta train tamamlanır** (önceki
  `BATCH_SIZE=2` OOM).
- ADIM 1–6 kod + unit test; ADIM 6 uçtan uca çalıştırıldı; ölçüm reçetesi
  v2.2’de yeniden kuruldu (aşağı).
- Bilinen gap: `apply_crisis_trauma` / `step_pool_with_crisis` API hazır;
  production `graph.py` henüz otomatik çağırmıyor.
- **Replay:** sampling açıkken `sha256(DAU_LLM_SEED:prompt)` per-generate
  tohum + strict CUDA lock → null faz1≡faz2 ölçüldü (N=10 event).

---

## 1. Aksiyom

DAU, yapay zeka agent'larının dışarıdan tanımlanmış trait'lerle değil,
yaşantı yoluyla iç dünya inşa ettiği bir simülasyon evrenidir.

AMADS'ın temel bulgusundan doğdu: `cooperation = 0.8` atadık, agent farklı
davrandı. Dışarıdan enjekte edilen trait çalışmıyor. İçten gelen bir "ben" lazım.

> **Bir agent'a trait veremezsin. Sadece yaşam verebilirsin. Trait oradan çıkar.**

Caron & Srivastava, Hartley et al., Bodroža et al., Dubedy — dört bağımsız
çalışma trait injection'ın tutarsız, yüzeysel ve davranışa bağlanmayan
sonuçlar ürettiğini gösteriyor. Gemini 2026 Deep Research raporu bu yasağı
literatürce yeniden doğruladı.

### Değiştirilemez yasaklar

1. Trait injection yok
2. LLM-as-judge yok — tüm metrikler deterministik Python
3. Clock-driven zaman yok — event sırası (`int`, `now_counter`)
4. Her sabit `UPPER_CASE`, tek yerde (tercihen `constraints.py` veya modül başı)
5. Magic number yok — semantic field isimleri

---

## 2. Evren modeli

- Kapalı simülasyon — agent'lar yapay zeka olduklarını bilmiyor
- Az sayıda LLM-powered tam kognisyon agent
- Büyük çoğunluk: deterministik mock NPC (Layer 4)
- Farklı katmanlarda roller (Mimar / Kahin benzeri karar mekanizmaları)

**Üç temel mücadele:** kaynak, evrimleşme, "Bu gerçek mi?" öz sorgusu.

**Çok-ajan gerçekliği (Layer 4 + ADIM 3):** Convention pilot `N_AGENTS=3`.
Graph life-loop tek `agent_id` / `thread_id` ile çalışır; per-agent LoRA
adapter dizini `dau_runs/adapters/{agent_id}/` ile ajana özel plastisite
hazır (Punica deseni).

---

## 3. Zaman ve Free Energy

Reaktif LLM (−t: geçmiş pattern) yerine proaktif anticipation (+t):
deneyim → internal model → tahmin → eylem → yeni deneyim.

Friston Free Energy: organizma sürprizi minimize eder. **Delta = tahmin hatası.**
Layer 1.5 bunu graph döngüsüne bağladı.

---

## 4. Duygu ve drift (Layer 2 — tamam)

Damasio: duygu = önceliklendirme. Dubedy 2025: `emotion: "anxious"` JSON
etiketi kararı değiştirmiyor. Duygu etiket değil, fonksiyondur.

```
Uyaran → delta(iç durum) → EmotionalWeight → etkilenen karar bölgesi → drift
```

- `EmotionalWeight.somatic_markers`: threat, reward, novelty, social, loss ∈ [0, 1]
- `apply_emotional_weight`: en yüksek marker → `You are currently prioritizing: {top_marker}`
- Travma (`magnitude ≥ 0.7`) → `update_drift` → kalıcı domain flag + magnitude birikimi
- Drift healing: `heal_drift` (`HEAL_RATE=0.3`, ~5 güçlü deneyim)
- **ADIM 1 eklentisi:** pool krizinde (`pool_ratio < 0.30`) resource domain’e
  çarpanlı travma (`CRISIS_TRAUMA_MULTIPLIER=2.5`) — bkz. §10 / §20

---

## 5. Delta eşikleri

```
DELTA_THRESHOLD_NOISE  = 0.1  # NO_TRACE
DELTA_THRESHOLD_NORMAL = 0.4  # NORMAL
DELTA_THRESHOLD_DEEP   = 0.7  # DEEP
# ≥ DEEP → TRAUMA → drift
```

```
delta küçük     → hafızaya yazılmaz
delta orta      → kısa süreli / NORMAL
delta büyük     → DEEP → disk
delta çok büyük → TRAUMA → drift tetiklenir
```

Travma birikimi:
`magnitudes[domain] = current + magnitude × exp(−current / TRAUMA_DECAY_BASE)`  
`TRAUMA_DECAY_BASE = 1.0` — azalan getiri.

**Magnitude (v1.2+ peak-weighted, DAERM’den bağımsız):**
```
M = 0.70 · max(PE_vec) + 0.30 · mean(PE_vec)
# MAGNITUDE_PEAK_WEIGHT = 0.70
# Uniform spillover S=0.20 → M ≈ 0.82 · PE
# PE ≥ 0.854 → M ≥ 0.70 → TRAUMA reachable
```

---

## 6. Hafıza formülleri (Layer 1 + ADIM 4)

### Ebbinghaus (değişmedi)

```
t = now_counter - record.last_activated_counter
S = max(1, round(record.magnitude / S_UNIT))  # S_UNIT=0.1
R = exp(-t / S)
# Recall: S += 1 · Travma silinmez (TRAUMA_S_BASE = 10)
```

### memory_score (v2.0 — HippoRAG 2 PPR entegre)

Legacy üçlü (0.3 / 0.4 / 0.3) `PPR_WEIGHT_IN_SCORE=0.30` ile ölçeklenir
(`× 0.70`), böylece toplam ağırlık 1.0 kalır:

```
W_RECENCY    = 0.3 × 0.7 = 0.21
W_IMPORTANCE = 0.4 × 0.7 = 0.28
W_RELEVANCE  = 0.3 × 0.7 = 0.21
PPR_WEIGHT   = 0.30

memory_score = 0.21·recency + 0.28·magnitude
             + 0.21·domain_match + 0.30·ppr_score
```

PPR sabitleri (`constraints.py`):
```
PPR_ALPHA = 0.85
PPR_WEIGHT_IN_SCORE = 0.30
PPR_TOP_K_DOMAINS = 10
```

Modül: `dau/memory/ppr_retrieval.py` — SQLite domain co-occurrence grafı
üzerinde Personalized PageRank (CPU; NetworkX bağımlılığı yoksa saf Python
yolu). `W_SEM=0` — ChromaDB embedding hâlâ skor değil, depo.

---

## 7. Layer 1.5 — Prediction Error (tamam)

```
agent_node:
  expected_outcome = memory-gated (Chroma) veya domain fallback
  → karar + expected_outcome event payload

evaluator_node:
  prediction_error = 1 - cosine_sim_MiniLM(expected, actual)
  after = apply_prediction_error(before, prediction_error)  # DAERM
  delta = compute_delta(before, after, raw_pe=PE)
  drift_state = update_drift(drift_state, delta)
  → memory record_delta
```

Sensör: `semantic_similarity.py` — frozen `all-MiniLM-L6-v2`, cosine ∈ [0,1].
Jaccard yalnızca diagnostik. Bilinen MiniLM sınırı: negation / polarity zayıf
→ **ADIM 2 NLI filtresi** preference çiftlerinde bunu telafi eder.

### DAERM (Dynamic Allostatic Equilibrium Recovery Model)

```
μ_i(t) = min(M_drift_i / (1 + M_drift_i), 0.75)
γ(t)   = E(t) / (1 + M_total)
L_i(t+1) = clamp(L_i + PE_i − γ·(L_i − μ_i), μ_i, 1.0)
```

Sabitler: `ALLOSTATIC_SETPOINT_MAX=0.75`, `CROSS_AXIS_SPILLOVER=0.20`,
`METABOLIC_FLOOR=0.05`.

### ADIM 5 — Precision-weighted PE (kodlandı; fiili davranış)

`semantic_similarity.compute_precision_weight` / `apply_precision_weighting`:

```
variance = var(pe_vector.values())        # tek event, history yok (Seçenek B)
π        = 1 / (variance + PRECISION_EPSILON)
π_clamp  = min(π, PRECISION_MAX_WEIGHT)
PE_w     = min(raw_pe · π_clamp, 1.0)
```

```
PRECISION_EPSILON     = 1e-6
PRECISION_MAX_WEIGHT  = 1.2    # 3.0'dan düşürüldü (541c02c)
PRECISION_HISTORY_WINDOW = 10
```

**Tavan neden 3.0 → 1.2:** ölçülen raw PE aralığı **0.2875–0.8102**. 3× kazançla
10 event’in **7’si** tam `1.0`’a doyuyordu; protokollerin ölçtüğü ΔPE farkı
clamp tarafından siliniyordu. 1.2 tavanı 0.81 tepesini 0.97’de tutar.

**Teorik not (kayda geçsin — belgelenen amaçla çelişki):** PE ∈ [0,1] olduğu
sürece örnek varyansı **0.5’i geçemez**, dolayısıyla `π = 1/(var+ε)` hiçbir
koşulda **2.0’ın altına inmez**. `PRECISION_MAX_WEIGHT = 1.2 < 2.0` olduğundan
tavan **her girdi için bağlayıcıdır** ve `π_clamp` sabit `1.2`’dir. Yani
formülün vaat ettiği “düşük varyans → yüksek precision, kriz → düşük precision”
adaptifliği bu formülasyonda **ulaşılamaz**; ADIM 5 pratikte **sabit kazanç**
uygular. Tavanı 2.0’ın üstüne çıkarmak adaptifliği geri getirir ama yukarıdaki
doygunluk sorununu da geri getirir. Formül ile davranış arasındaki bu çelişki
açık kalemdir (§17). Regresyon: `tests/test_precision_pe.py` —
`test_clamp_binds_for_every_pe_vector_in_unit_interval`.

---

## 8. Layer 2 — EmotionalWeight + Drift (tamam)

### EmotionalWeight

```
threat  = clamp(magnitude · resource_load, 0, 1)
reward  = clamp((1 − magnitude) · energy, 0, 1)
novelty = clamp(magnitude · uncertainty_load, 0, 1)
social  = clamp(social_load, 0, 1)
loss    = 1.0 if is_trauma(delta) else 0.0
```

### Drift

```
DriftState(flags: dict[str,bool], magnitudes: dict[str,float])
update_drift: travma → flags[domain]=True,
  magnitudes[domain] = current + magnitude × exp(−current / TRAUMA_DECAY_BASE)
heal_drift: flagged + magnitude≥0.6 + non-trauma → magnitudes azalır (HEAL_RATE=0.3)
get_drift_bias: flagged ise magnitude, değilse 0.0
```

---

## 9. Layer 3 — Nesil Konsolidasyonu + Drift Healing (tamam)

- `select_for_transfer`: memory_score ≥ 0.6, recall_count ≥ 1;
  travma yalnızca drift ≥ 1.5 ise (veya F_agent bandına göre cautionary)
- `F_agent < 0.35` → travma cautionary (`inherited_warning=True`,
  `somatic_scale=-0.3`)
- Constants: `GENERATION_TRANSFER_THRESHOLD=0.6`, `GENERATION_MIN_RECALL=1`,
  `DRIFT_TRANSFER_MIN=1.5`, `HEAL_THRESHOLD=0.6`, `HEAL_RATE=0.3`

---

## 10. Layer 4 — Society (tamam + ADIM 1)

### GovSim Kaynak Fiziği (`environment.py`)

```
P_next = clamp(P + r·P·(1 - P/P_max) - Σe_i, 0, P_max)
collapse = P_next <= P_max · COLLAPSE_EPSILON
# POOL_MAX=100, POOL_REGEN_RATE=0.15, COLLAPSE_EPSILON=0.05
```

### ADIM 1 — Somatic Enforcement (kodlandı)

```
POOL_CRISIS_THRESHOLD   = 0.30
CRISIS_TRAUMA_MULTIPLIER = 2.5
CRISIS_BASE_MAGNITUDE    = 0.4   # × 2.5 → 1.0 TRAUMA (clamp)
CRISIS_AFFECTED_DOMAIN   = "resource"
```

API:
```
apply_crisis_trauma(drift_state, pool_ratio, base_magnitude=…) -> DriftState
step_pool_with_crisis(env, extractions, drift_states) -> (env, drift_states)
```

`pool_ratio < 0.30` → sentetik `DeltaRecord` + `update_drift` (mevcut imza).
Eşik ve üstü: no-op. Unit testler: `dau/society/tests/test_environment.py`
(crisis 5 test). **Gap:** `graph.py` henüz her adımda otomatik çağırmıyor —
pilot / harness / `step_pool_with_crisis` üzerinden.

### Sosyal yük / LOD / Fitness

```
social_load = 0.5·cooperation_stress + 0.5·coordination_friction
T_cognitive = 0.35·(δ/0.7) + 0.25·max_drift + 0.20·coord_friction + 0.20·(1-pool_ratio)
F_agent = 0.4·(E/E_max) + 0.3·(1-|ΔP|/P_max) + 0.3·(t_surv/T_gen)
```

NPC conserve kuralı: `NPC_POOL_RATIO_CONSERVE=0.3` (crisis eşiği ile hizalı).

### Graph wiring

```
social_pre_node → agent_node → evaluator_node → meta_observer_node
  → (social_pre | END)
```

---

## 10b. Layer 5 — Metacognition (kod tamam · empirik UNSUPPORTED)

### Empirik verdict (kilitli)

- Meta A/B: deterministic seed replay → tüm farklar 0 → **STOCHASTIC_NOISE_CONFIRMED**
- Closed-loop metacognition **UNSUPPORTED (paper-locked)**
- Protocol C (Groq frozen): ΔPE≈0 gürültü → **paper-locked negative finding**
  (temiz çekirdek ~31–35 çift; resmi paired t-test yok; full 40 tekrar yok)
- **Protocol C′ N=15 (eski reçete, 2026-08-07 gece):** 50 event/arm ·
  `lived −0.008935 · null −0.009007 · shuffle −0.002849 · t=0.019 · p=0.985`
  → harness **INCONCLUSIVE**, belge **`INSTRUMENT_LIMITED_NULL`**
  (artefakt: `dau_runs/protocol_c_prime_results.json`)
- **C′ düzeltme sonrası mini-test (N=1, seed=9101, 10 event, sampling + yaşam-PE):**
  `lived −0.180 · null 0.000 · shuffle −0.149` · sıra `lived < shuffle < null`
  · null faz1≡faz2 → **`SAMPLE_LIVED_PE_SEPARATION`** (significance yok; N=15 sırada)

**`INSTRUMENT_LIMITED_NULL` ne demek:** “yaşantı-LoRA’nın etkisi yok” **değil**;
**“o koşumdaki ölçüm aletiyle bir etki görülemez”**. Dayanak o koşumda:
(1) gizli `maybe_lora_update_after_life` null’u da eğitiyordu; (2) greedy +
tohum trajektoriyi değiştirmiyordu (N=15≈N=1 kopya); (3) plato tercih
verisini öldürüyordu; (4) tasarımcı `PREF_EXPECTED` trait-adjacent’tı.
Eski C′ null’ı Protocol C null’ı ile **aynı statüde sunulmamalıdır**.

**`SAMPLE_LIVED_PE_SEPARATION` ne demek:** düzeltme zinciri + `DAU_LLM_DO_SAMPLE=1`
+ yaşam-PE tercih ile tek seed’de H1 yönü görüldü; henüz N≥15 değil,
istatistik iddiası yok. N=15 bu reçeteyle koşulacak (§20).

### Aktüatörler (deterministik Python, LLM okumaz)

1. `lod_override` — DEEP + düşük m_ratio → System 2 zorla
2. `context_prune` — yüksek retrieval variance → düşük skor at
3. `trigger_drift_healing` — düşük F_agent + reward → `heal_drift`
4. `trigger_retrieval` — düşük m_ratio + NORMAL+ → Chroma ek sorgu

---

## 11. Mimari durum (v2.2)

| Katman | Durum | Özet |
|--------|-------|------|
| Layer 0 Foundation | ✅ | State, delta, event-clock, constraints, LangGraph |
| Layer 1 Memory | ✅ + ADIM 4 | Chroma+SQLite, Ebbinghaus, **PPR memory_score** |
| Layer 1.5 PE | ✅ | MiniLM cosine PE → DAERM → magnitude decoupling |
| Layer 2 Emotion+Drift | ✅ + ADIM 1 API | EmotionalWeight + DriftState + crisis trauma API |
| Layer 3 Generation | ✅ | Konsolidasyon, miras, heal; fitness filtresi |
| Layer 4 Society | ✅ + ADIM 1 | GovSim, social, LOD, F_agent, crisis constants |
| Layer 5 Metacognition | ✅ kod / ❌ empirik (frozen) | Protocol C **paper-locked null** |
| Plastisite (ADIM 2–3) | ✅ kod / ⚠ default off | Yaşam-PE tercih · QLoRA+DPO · sampling opt-in |
| ADIM 5 Precision PE | ✅ kod / ⚠ tavan bağlayıcı | Sabit kazanç `π=1.2` (§7) |
| ADIM 6 C′ | ✅ kod + yeniden kuruldu | Eski N=15 `INSTRUMENT_LIMITED_NULL`; mini **SAMPLE_LIVED_PE_SEPARATION** |

---

## 12. Kod ağacı (v2.2)

```
dau/foundation/
 ├── state.py              — DAUAgentState (+ drift, social, lod, env, self_model)
 ├── delta.py              — compute_delta / classify / is_trauma (peak-weighted)
 ├── emotional_weight.py   — EmotionalWeight
 ├── drift.py              — DriftState, update_drift, heal_drift
 ├── social.py             — cooperation_stress, coordination_friction, Markov
 ├── lod.py                — T_cognitive, NPC heuristics
 ├── self_model.py         — SelfModel / build_self_model
 ├── meta_observer.py      — dört aktüatör + meta_observer_node
 ├── semantic_similarity.py — MiniLM PE sensor + precision weighting (ADIM 5)
 ├── constraints.py        — pressures + DAERM + NLI + LoRA + PPR + DPO
 │                          + PRECISION constants
 ├── time_model.py         — EventClock
 ├── graph.py              — social_pre → agent → evaluator → meta_observer
 │                          (+ DAU_LLM_BACKEND; local → switch_adapter)
 ├── llm_backend.py        — complete() Protocol; GroqBackend; LocalBackend
 ├── local_llm.py          — 4-bit load; per-agent adapter; DPO (batch=1 +
 │                          checkpointing); opt-in sampling
 │                          (`DAU_LLM_DO_SAMPLE` + prompt-keyed seed)
 ├── lora_update.py        — LivedTrace / PreferencePair; **yaşam-PE ranking**
 │                          (tasarımcı PREF_EXPECTED kaldırıldı)
 ├── nli_filter.py         — contradiction_score / is_genuine_polarity_pair
 ├── memory_bridge.py      — graph ↔ memory
 ├── generation.py         — consolidate / apply_generation
 └── tests/                — foundation + NLI + per-agent adapter
                           + test_precision_pe + …

dau/memory/
 ├── store.py / decay.py / retrieval.py / consolidation.py
 ├── ppr_retrieval.py      — HippoRAG-style PPR (ADIM 4)
 └── tests/                — + test_ppr_retrieval

dau/generation/
 └── fitness.py            — F_agent, W_transfer

dau/society/
 ├── environment.py        — pool physics + apply_crisis_trauma (ADIM 1)
 ├── run_convention_pilot*.py / run_meta_ab.py / run_nuance_loss_pilot.py
 └── tests/

dau/diagnostics/
 ├── run_protocol_c.py     — frozen Meta ON/OFF (paper-locked)
 ├── run_protocol_c_prime.py — C′ harness (ADIM 6; lived/null/shuffle, N≥15)
 └── long_run.py / pe_histogram.py / actuator_audit.py

docs/
 └── DAU_MASTER_REFERENCE_v20.md            — operasyonel kaynak (**v2.1**)
 └── DAU_MASTER_REFERENCE_v20.{html,pdf}    — v2.0 türevleri (stale)
 └── DAU_MASTER_REFERENCE_v10.*              — arşiv (v1.4; süpersede)
```

**Adapter kökleri (dikkat):**
- Runtime Punica path: `dau_runs/adapters/{agent_id}/` (`ADAPTER_BASE_DIR`)
- C′ disk artefaktları (untracked): `dau_lora_adapters/cprime_seed…`

---

## 13. Graph yaşam döngüsü

```
social_pre_node:
  opponent varsa Markov P(cooperate) + entropy → retrieval_context

agent_node:
  expected_outcome → retrieve_relevant → EmotionalWeight / drift bias
  → if DAU_LLM_BACKEND=local: switch_adapter(model, agent_id)
  → LLM (Groq veya LocalBackend.complete) veya npc_decision → Event

evaluator_node:
  MiniLM PE → DAERM InternalState → compute_delta(raw_pe)
  → update_drift → T_cognitive/LOD → record_delta

meta_observer_node:
  build_self_model → lod_override → context_prune
  → trigger_drift_healing → trigger_retrieval

should_continue:
  energy ≤ TERMINATION_ENERGY → END else → social_pre_node
```

**Stack:** LangGraph · Pydantic v2 · ChromaDB · SQLite/SqliteSaver ·
Groq Llama-3.1-8b-instant · (ops.) local 4-bit Llama-3.1-8B + peft · LangSmith

---

## 14. Test durumu (bu branch)

| Alan | Not |
|------|-----|
| Foundation + PE + Emotion + Drift + LOD + Social | mevcut |
| Generation + Fitness | mevcut |
| Meta-Observer + Convention + Meta A/B + Nuance | mevcut |
| Society environment (+ crisis ADIM 1) | genişletildi |
| NLI filter (ADIM 2) | `test_nli_filter.py` |
| Per-agent adapter (ADIM 3) | `test_per_agent_adapter.py` |
| PPR retrieval (ADIM 4) | `test_ppr_retrieval.py` |
| Precision PE (ADIM 5) | `test_precision_pe.py` (tavan bağlayıcılığı dahil) |
| **Collect (v2.2 branch)** | **177** |

*(Master v1.4’teki “137” ve main v1.6’daki “162+” sayıları farklı ağaç
kesitleri; bu belge **bu branch collect=177** ile kilitlenir.)*

**Kırılgan test:** `test_nli_filter.py` yaklaşık **3–6 koşuda bir** düşüyor.
İzole + `HF_HUB_OFFLINE=1` ile daha stabil; suite içinde sıra/hub yolu
şüphesi. Açık kalem.

Empirik artefaktlar (`dau_runs/`):
- `protocol_c_run.log` — provisional/paper-locked null izi
- `protocol_c_prime_results.json` — C′ N=15 eski, `INSTRUMENT_LIMITED_NULL`
- Mini sampling+B: `/tmp/cprime_full_arm/dau_runs/protocol_c_prime_sample_pilot.json`
  (`SAMPLE_LIVED_PE_SEPARATION`)
- `vram_spike_results.json` — GO (~6386 MiB)
- `overnight_audit_results.json`

---

## 15. AMADS / GovSim karşılaştırma

| AMADS / klasik | DAU |
|----------------|-----|
| Trait dışarıdan atanıyor | Trait yaşantıdan inşa ediliyor |
| Her run sıfır | Sonraki run değişmiş başlıyor (memory + drift + ops. adapter) |
| Kaynak var, agent değişmiyor | Kaynak → travma → drift → (kriz çarpanı) → evrim |
| Duygu etiketi | EmotionalWeight fonksiyonu |
| Zaman = round | Zaman = event + delta |

---

## 16. Beş evrensel kısıt

| Kısıt | Anlam | DAU karşılığı |
|-------|-------|---------------|
| time_pressure | Her şeyin sonu var | Nesil sonu / konsolidasyon |
| resource_scarcity | Her şey sınırlı | CPR / GovSim + crisis trauma |
| social_pressure | Başkaları var | İşbirliği ≠ koordinasyon |
| uncertainty | Bilgi eksik | Eksik bilgiyle karar |
| generation_end | Nesil kapanır | Miras + ops. per-agent LoRA |

---

## 17. Açık sorular (güncel)

### Kilitli / kapanmış

- ✅ EmotionalWeight, Layer 1.5 PE, nesil, drift heal, LOD, fitness
- ✅ Protocol C frozen: **paper-locked negative finding**
- ✅ C′ mini: **WEAK_LORA** (placeholder-train caveat + sinyal v1)
- ✅ C′ v2 smoke N=1: **SMOKE_SEPARATION** (significance yok; N=15 otomatik değil)
- ✅ C′ N=15 uçtan uca **çalıştırıldı** — sonuç `INSTRUMENT_LIMITED_NULL`;
  kapanan soru “harness çalışıyor mu”, kapanmayan soru “etki var mı” (§10b)
- ✅ Trait injection yasağı — Gemini raporu ile yeniden doğrulandı
- ✅ MiniLM tek başına polarity için yetersiz → NLI filter (ADIM 2) kodlandı
- ✅ Serbest kanalda restraint emergence yaptırımsız çıkmaz → crisis API (ADIM 1)

### Hâlâ açık

- **C′ N=15 sampling+B koşumu** — mini-test `SAMPLE_LIVED_PE_SEPARATION`
  sonrası istatistiksel doğrulama (GPU ≈ 1.5–2.5 saat; eski 13 saat CPU
  tahmini iptal)
- **Plato / W penceresi** — sinyal varken null kilidinden ön-kayıtlı W;
  post-hoc yasak (§18/2 tarihsel)
- **ADIM 5 precision** PE bounded iken nasıl gerçekten adaptif yapılır? (§7)
- `apply_crisis_trauma` → production graph kablolama
- Energy floor / γ=0 erken kapanma
- Meta `trigger_drift_healing` eşik kalibrasyonu
- Spontaneous convention: format sync ≠ restraint sync
- `test_nli_filter.py` kırılganlığı (HF offline / tokenizer yolu)
- Dual adapter root tekilleştirme

### Kapanan (v2.2 — bu branch’te ölçüldü)

- ✅ Yerel LLM replay — greedy birebir; sampling’te prompt-keyed seed +
  strict CUDA lock ile null faz1≡faz2
- ✅ Null kontaminasyonu — `_build_lived_examples` artık train etmiyor
- ✅ Tohum = niş (`_seed_niche`) — N=15≠N=1 kopya
- ✅ Tercih hedefi — yaşam-PE ranking (reçete B); tasarımcı cümle yok
- ✅ DPO OOM — `BATCH_SIZE=1` + gradient checkpointing (8GB)
- ✅ Chat-template DPO / eval mode / adapter izolasyonu (önceki commit’ler)

---

## 18. Bilinen Sınırlar + Plastisite günlüğü

### Bilinen sınırlar (özet)

- LOD System2→1 nüans kaybı ölçüldü (kasıtlı)
- MiniLM negation zayıf; NLI gate yalnızca preference çiftlerinde
- `F_agent` dışsal tasarım skoru (doğal seçilim değil)
- Frozen weights: parametrik öğrenme default **kapalı**
- Protocol C: TPD kirlenmesi; pair t-test yok; claim locked
- C′ v2: N=1 — istatistik iddiası yok
- Crisis: API var, graph otomatik çağrı kısmi
- ADIM 5 precision: tavan her koşulda bağlayıcı → adaptif değil, sabit kazanç (§7)

### Yeni sınırlar (v2.1 tarihsel) → v2.2 durumu

#### 1. Replay non-determinism — **kapatıldı (v2.2)**

Eski N=15’te null faz1≠faz2 sanılıyordu; asıl nedenler sırayla:
gizli train hook, tohumun trajektoriyi değiştirmemesi, sampling’te RNG
kirlenmesi (`switch_adapter` early-return + LoRA reset). Düzeltmeler:
`torch.manual_seed` / CUDA strict lock · prompt-keyed sample seed ·
hook kaldırıldı · niş tohumları. **Ölçüldü:** sampling + aynı agent_id ile
10 event null replay birebir.

#### 2. Metrik plato dilusyonu — **kısmen çözüldü / hâlâ izleniyor**

Greedy plato (~3 unique completion / 10 event) tercih verisini öldürüyordu.
`DAU_LLM_DO_SAMPLE=1` (T=0.2) ile unique ≈5 ve yaşam-PE çiftleri gerçek
kontrast kazandı. 50 event’te plato hâlâ seyreltebilir — N=15’te W’yi
null kilidinden **ön-kayıtla** sabitlemek açık (§17).

### Plastisite günlüğü

#### Sinyal v1 vs v2 vs yaşam-PE (v2.2)

| | Sinyal v1 | Sinyal v2 (eski A) | Yaşam-PE (B, v2.2) |
|---|-----------|-------------------|---------------------|
| Kimlik | `pe_delta_trauma_drift_v1` | `pe_ranked_pref_v2` | aynı dosya, yeni ranking |
| Tercih | skalar CE | MiniLM vs **tasarımcı** expected + sabit reject | ajanın kendi kararları, **yaşam PE** |
| Aksiyom | — | ⚠ trait-adjacent | ✅ yalnızca yaşam |
| Mini-test | — | ΔPE ≈ +0.002 (zarar) | sampling ile ΔPE ≈ −0.180 |

#### Empirik tablo

| Deney | N | Backend | Sinyal | ΔPE_lived | ΔPE_null | ΔPE_shuffle | Karar |
|-------|---|--------|--------|-----------|----------|-------------|-------|
| Protocol C (Groq) | ~35 temiz | groq | meta ON/OFF | ≈0 | — | — | **paper-locked null** |
| C′ mini / smoke | ≤3 | local | v1/v2 erken | (tarihsel) | | | **WEAK / SMOKE** (†) |
| C′ N=15 eski | 15 | local | v2+A, greedy, kontamine | −0.0089 | −0.0090 | −0.0028 | **INSTRUMENT_LIMITED_NULL** |
| C′ mini sampling+B | 1 (9101) | local | yaşam-PE + sample | **−0.180** | **0.000** | −0.149 | **SAMPLE_LIVED_PE_SEPARATION** |

**(†)** Gradyansız eğitim / adapter sızıntısı düzeltilmeden önce; ileri sürülmez.

C′ mini sampling+B parametreleri: 10 event/arm, `DAU_LLM_DO_SAMPLE=1`,
`T=0.2`, `DAU_LORA_ENABLED=1`, yaşam-PE pairs, GPU ≈ 71 sn / seed (3 kol).
Eski “13 saat CPU” tahmini **iptal**; GPU N=15×50 ≈ **1.5–2.5 saat**.

VRAM: peak ≈ **6.4 GiB** + DPO batch=1 → **GO** (8GB).

#### Paper naratif iskeleti (kilitli)

1. Ana katkı: frozen-weight in-context metacognition null (Protocol C)
2. Mimari: trait yasağı, MiniLM PE, DAERM, LOD, format≠restraint
3. Appendix: C′ alet evrimi — `INSTRUMENT_LIMITED_NULL` (eski) →
   reçete düzeltmesi → `SAMPLE_LIVED_PE_SEPARATION` (N=1) → (sırada N=15)
4. Non-claims: persona LoRA, LLM-as-judge, per-event online LoRA, Layer 6,
   full Groq C rerun, N<15 istatistik iddiası, post-hoc W bulgusu

---

## 19. ADIM uygulama kaydı (v2.2 — bu branch)

### ADIM 1 — Layer 4 Somatic Enforcement ✅ kod

| | |
|--|--|
| Dosyalar | `dau/society/environment.py` (+ tests) |
| Sabitler | `POOL_CRISIS_THRESHOLD=0.30`, `CRISIS_TRAUMA_MULTIPLIER=2.5`, `CRISIS_BASE_MAGNITUDE=0.4` |
| Davranış | `pool_ratio < 0.30` → resource TRAUMA via `update_drift` |
| Test | crisis 5 unit test |
| Gap | graph otomatik çağrı yok |

### ADIM 2 — Signal v2 NLI Polarity Filter ✅ kod

| | |
|--|--|
| Dosyalar | `nli_filter.py`, `constraints.py`, `lora_update.build_pe_ranked_pairs` |
| Model | `cross-encoder/nli-deberta-v3-small` (CPU; transformers path) |
| Eşik | `NLI_CONTRADICTION_THRESHOLD=0.60` |
| Flag | `DAU_NLI_FILTER_ENABLED` (default on; `_NLI_AVAILABLE` soft-import) |
| Test | `test_nli_filter.py` |

### ADIM 3 — Per-Agent QLoRA (Punica) ✅ kod

| | |
|--|--|
| Dosyalar | `local_llm.py`, `llm_backend.py`, `lora_update.py`, `graph.py` |
| Path | `dau_runs/adapters/{agent_id}/` |
| Rank/α | `PER_AGENT_LORA_RANK=8`, `PER_AGENT_LORA_ALPHA=16` |
| Inference | `DAU_LLM_BACKEND=local` → `switch_adapter` + `LocalBackend.complete` |
| Train | `run_micro_train_preference_step(..., agent_id=)` → gerçek DPO adımı → `save_agent_adapter` |
| Default | `DAU_LORA_ENABLED=0` |
| Test | `test_per_agent_adapter.py` |
| Gap | **kapandı** (`e4c026b`, `f25b0ef`) — generation-end hook bağlı, eğitim gerçek |

**Düzeltme 1 — eğitim gerçekten yoktu (`e4c026b`).** Önceki halinde
`run_micro_train_preference_step` **hiçbir gradyan adımı içermiyordu**: taze
adapter’ı diske kaydedip `trained: True` dönüyordu. Yani üretilen her adapter
`lora_B = 0` ile **birim dönüşümdü** ve lived kolu davranışsal olarak null
kolundan ayırt edilemezdi. Şimdi generation-end hook bağlı ve gerçek DPO
micro-train çalışıyor. Doğrulama: eğitim sonrası `lora_B` abs-sum
**0.0 → 128.8**.

**Düzeltme 2 — adapter izolasyonu (`f25b0ef`).** Öncesinde peft, **kayıtlı tüm
adapter’ları her ajanın dizinine** yazıyordu
(`adapters/cprime-null-2001/cprime-lived-2001/` gibi), dolayısıyla null kolu
lived kolunun eğitimini **miras alıyordu**. Şimdi bellekte tek bir `default`
slot tutuluyor; **izolasyon disk düzeyinde** sağlanıyor.

Bu iki düzeltme öncesinde üretilmiş **tüm C′ sonuçları geçersizdir** (§18
empirik tablosunda **†** ile işaretli satırlar).

### ADIM 4 — HippoRAG 2 PPR ✅ kod

| | |
|--|--|
| Dosyalar | `dau/memory/ppr_retrieval.py`, `retrieval.py` |
| Formül | §6 memory_score |
| Test | `test_ppr_retrieval.py` |

### ADIM 5 — Precision-Weighted PE ✅ kod (⚠ tavan bağlayıcı)

| | |
|--|--|
| Dosyalar | `semantic_similarity.py` (`compute_precision_weight` / `apply_precision_weighting`), `constraints.py`, `graph.py` |
| Formül | `π = min(1/(var(pe_vector)+ε), PRECISION_MAX_WEIGHT)`; `PE_w = min(raw_pe·π, 1.0)` |
| Sabitler | `PRECISION_EPSILON=1e-6`, `PRECISION_MAX_WEIGHT=1.2` (3.0’dan; `541c02c`) |
| Test | `test_precision_pe.py` |
| ⚠ Uyarı | PE bounded ⇒ var ≤ 0.5 ⇒ π ≥ 2.0 ⇒ **tavan her koşulda bağlayıcı**; adaptif değil, **sabit kazanç** (§7) |

Tavan düşürülmeseydi: ölçülen raw PE 0.2875–0.8102 aralığında, 3× kazanç
10 event’in 7’sini tam 1.0’a doyuruyordu.

### ADIM 6 — Protocol C′ N≥15 ✅ kod + yeniden kuruldu

| | |
|--|--|
| Dosyalar | `dau/diagnostics/run_protocol_c_prime.py` |
| Eski koşum | N=15 · 50 event · greedy · reçete A → **INSTRUMENT_LIMITED_NULL** |
| Mini (v2.2) | N=1 · 10 event · sample+B → **SAMPLE_LIVED_PE_SEPARATION** |
| Sırada | N=15 · 50 event · `DAU_LLM_DO_SAMPLE=1` · yaşam-PE · niş tohum |
| Harness | lived vs shuffle birincil; null bütünlük assert; sıfır-varyans guard |

### Bağımlılık grafiği

```
ADIM 1 ──────────────────────────────┐
ADIM 2 ──────────────────────────────┤
                                      ↓
ADIM 3 ← ADIM 2 sonrası ────────────→ ADIM 6
ADIM 4 ← ADIM 1+2 sonrası ──────────→ (Protocol C′ N≥15 sampling+B)
ADIM 5 ← ADIM 2+4 sonrası ──────────┘
```

ADIM 1–6 kodlandı. ADIM 6 ölçüm reçetesi v2.2’de yeniden kuruldu; N=15
sampling+B **sıradaki empirik adım**.

---

## 20. Yol haritası + Anti-roadmap (v2.2)

### Doğrulanan / kilitli

- Trait injection yasağı
- Deterministik Layer 0–4 omurgası
- Nesil sonu micro-QLoRA ≫ per-event online
- Protocol C paper-locked null
- C′ harness + replay (sampling’te prompt-keyed seed)
- Yaşam-PE tercih (reçete B) · niş tohumları · DPO 8GB fit

### Yeniden değerlendirilmesi gereken

- SMOKE / WEAK / eski N=15 `INSTRUMENT_LIMITED_NULL` — tarihsel alet kayıtları;
  sampling+B N=15 öncesi ileri sürülmez

### Yanlışlanan / kapatılan

- Frozen-weight kapalı döngü metacognition
- MiniLM tek başına PE polarity yeterliliği
- Yaptırımsız restraint emergence
- “Replay imkânsız” (v2.1 blocker — kapatıldı)
- Tasarımcı `PREF_EXPECTED` tercih hedefi

### Sıradaki (öncelik)

1. **C′ N=15 sampling+B** — GPU, `DAU_LLM_DO_SAMPLE=1`, T=0.2, yaşam-PE,
   niş tohum; ~1.5–2.5 saat (13 saat CPU tahmini iptal)
2. İsteğe bağlı: diversity gate (`n_unique < K` → skip) · ön-kayıtlı W
3. Crisis’i graph’a kablola
4. ADIM 5 precision formülünü PE bounded’da adaptif yap (§7)
5. Paper gövdesi (frozen-null ana; C′ alet evrimi appendix)

### Anti-roadmap (yasak)

- Per-event online LoRA · EWC · TTT/PoT · prefix ana rota
- N<15 ile istatistiksel iddia · post-hoc W bulgusu
- Eski `INSTRUMENT_LIMITED_NULL` koşumunu “etki yok” diye sunmak
- Layer 6 · LLM-as-judge · trait injection · wall-clock zaman
- Persona/trait adapter · Groq Protocol C tekrarı

---

## 21. Ortam bayrakları (referans)

| Env | Default | Anlam |
|-----|---------|-------|
| `DAU_LLM_BACKEND` | `groq` | `groq` \| `local` |
| `DAU_LORA_ENABLED` | `0` | generation-end train/save |
| `DAU_NLI_FILTER_ENABLED` | `1` | (yaşam-PE path’te ranking NLI kullanmaz) |
| `DAU_LLM_DO_SAMPLE` | `0` | local sampling; C′ için `1` |
| `DAU_LLM_TEMPERATURE` | (model) | sampling sıcaklığı (C′: `0.2`) |
| `DAU_LLM_SEED` | — | faz tohumu (+ prompt hash) |
| `DAU_TORCH_THREADS` | `14` | CPU thread pin |
| `CUBLAS_WORKSPACE_CONFIG` | `:4096:8` | CUDA deterministic |
| `HF_HUB_OFFLINE` | — | C′ koşumunda `1` önerilir |
| `DAU_THREAD_ID` | — | checkpoint resume |
| `DAU_META_AB_*` | — | Meta A/B protokol |
| `GROQ_API_KEY` | — | remote LLM |
| `DAU_CPRIME_*` | (C′ harness) | N_PAIRS / EVENTS / SIGNAL |

---

## 22. Versiyon geçmişi

| Ver | Tarih | Not |
|-----|-------|-----|
| 0.1–0.9 | 2026-07/08 | Taslak → Layer 0–4 |
| **1.0** | 2026-08-04 | Layer 5 kod; 109 test |
| **1.0+** | 2026-08-04 | Empirik: format≠restraint; L5 UNSUPPORTED; **137 test** |
| **1.1** | 2026-08-05 | DAERM |
| **1.2** | 2026-08-05 | Magnitude decoupling; TRAUMA reachable |
| **1.3** | 2026-08-06 | Protocol C tasarımı |
| **1.4** | 2026-08-06 | Protocol C kısmi null; lokal LoRA roadmap (`v10` docs) |
| **1.5** | 2026-08-06 | VRAM GO; C′ mini WEAK_LORA |
| **1.6** | 2026-08-06 | Paper-locked null; v2 smoke SMOKE_SEPARATION (`v15` docs) |
| **1.7** | 2026-08-06 | Gemini roadmap Section 20 planı (6 ADIM) |
| **2.0** | **2026-08-07** | **Yeni belge ailesi `v20`.** ADIM 1–4 kodlandı (crisis, NLI, per-agent QLoRA, PPR). memory_score PPR formülü. 159 test (bu branch). ADIM 5–6 açık. `DAU_LORA_ENABLED=0` korunuyor. `v10` süpersede. |
| **2.1** | **2026-08-07** | Ölçüm zincirinde 6 katmanlı hata düzeltildi; C′ N=15 uçtan uca → **`INSTRUMENT_LIMITED_NULL`**. Replay/plato blocker kaydı. 175 test. |
| **2.2** | **2026-08-07** | Alet yeniden kuruldu: null train hook kaldırıldı · niş tohum · yaşam-PE tercih · DPO 8GB fit · sampling + prompt-keyed seed. Mini N=1 → **`SAMPLE_LIVED_PE_SEPARATION`** (lived −0.180 · null 0 · shuffle −0.149). N=15 sampling sırada; 13 saat CPU tahmini iptal (GPU ≈1.5–2.5 saat). **177 test**. `.html`/`.pdf` henüz yenilenmedi. |

---

**Güncellendi (v2.2):** v2.1’in kazancı “alet bozuk” teşhisiydi. v2.2’nin
kazancı teşhisi **kapatmak**: replay, null bütünlüğü, endojen tercih ve
sampling ile tek seed’de H1 yönü (`SAMPLE_LIVED_PE_SEPARATION`). Bu henüz
N=15 değildir; istatistik iddiası yok. Omurga default’ları değişmedi: LoRA
kapalı, Groq default, trait yasak. C′ local koşumda `DAU_LLM_DO_SAMPLE=1`.

Bu döküman her önemli katman / empirik dönüm tamamlanınca güncellenir.  
Versiyon 2.2 — ADIM 1–6 kod; C′ alet yeniden kuruldu; Protocol C paper-locked
null; eski C′ **INSTRUMENT_LIMITED_NULL**; mini **SAMPLE_LIVED_PE_SEPARATION**.
