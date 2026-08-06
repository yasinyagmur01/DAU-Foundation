# DAU — Master Reference

**Versiyon 1.4** · 2026-08-06  
Layer 0–5 kod tamam · MiniLM PE · DAERM · Protocol C **provisional null** (ΔPE≈0, N≈35 temiz çift) · **137 test passed**.

**İddia disiplini:** Layer 5 **kod** ✅ · frozen-weight kapalı döngü metacognition **empirik iddiası UNSUPPORTED (provisional)** · sıradaki araştırma: **lokal LLM + yaşantı-koşullu LoRA**.

---

## 1. Aksiyom

DAU, yapay zeka agent'larının dışarıdan tanımlanmış trait'lerle değil, yaşantı yoluyla iç dünya inşa ettiği bir simülasyon evrenidir.

AMADS'ın temel bulgusundan doğdu: `cooperation = 0.8` atadık, agent farklı davrandı. Dışarıdan enjekte edilen trait çalışmıyor. İçten gelen bir "ben" lazım.

> **Bir agent'a trait veremezsin. Sadece yaşam verebilirsin. Trait oradan çıkar.**

Caron & Srivastava, Hartley et al., Bodroža et al., Dubedy — dört bağımsız çalışma trait injection'ın tutarsız, yüzeysel ve davranışa bağlanmayan sonuçlar ürettiğini gösteriyor. DAU'nun aksiyomu empirik destekli.

### Değiştirilemez yasaklar

1. Trait injection yok
2. LLM-as-judge yok — tüm metrikler deterministik Python
3. Clock-driven zaman yok — event sırası (`int`, `now_counter`)
4. Her sabit `UPPER_CASE`, tek yerde
5. Magic number yok — semantic field isimleri

---

## 2. Evren modeli

- Kapalı simülasyon — agent'lar yapay zeka olduklarını bilmiyor
- Az sayıda LLM-powered tam kognisyon agent
- Büyük çoğunluk: deterministik mock NPC (Layer 4)
- Farklı katmanlarda roller (Mimar / Kahin benzeri karar mekanizmaları)

**Üç temel mücadele:** kaynak, evrimleşme, "Bu gerçek mi?" öz sorgusu.

---

## 3. Zaman ve Free Energy

Reaktif LLM (−t: geçmiş pattern) yerine proaktif anticipation (+t): deneyim → internal model → tahmin → eylem → yeni deneyim.

Friston Free Energy: organizma sürprizi minimize eder. **Delta = tahmin hatası.** Layer 1.5 bunu graph döngüsüne bağladı.

---

## 4. Duygu ve drift (Layer 2 — tamam)

Damasio: duygu = önceliklendirme. Dubedy 2025: `emotion: "anxious"` JSON etiketi kararı değiştirmiyor. Duygu etiket değil, fonksiyondur.

```
Uyaran → delta(iç durum) → EmotionalWeight → etkilenen karar bölgesi → drift
```

- `EmotionalWeight.somatic_markers`: threat, reward, novelty, social, loss ∈ [0, 1]
- `apply_emotional_weight`: en yüksek marker → `You are currently prioritizing: {top_marker}`
- Travma (`magnitude ≥ 0.7`) → `update_drift` → kalıcı domain flag + magnitude birikimi
- Drift healing: `heal_drift` Layer 3'te eklendi (`HEAL_RATE=0.3`, ~5 güçlü deneyim)

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

Travma birikimi: `magnitudes[domain] = current + magnitude × exp(−current / TRAUMA_DECAY_BASE)`  
`TRAUMA_DECAY_BASE = 1.0` — azalan getiri; beşinci travma birinciden materyal olarak küçük.

---

## 6. Hafıza formülleri (Layer 1)

```
memory_score = 0.3·recency + 0.4·magnitude + 0.3·domain_match
# W_SEM = 0.0 — ChromaDB embedding depo, skor değil

t = now_counter - record.last_activated_counter
S = max(1, round(record.magnitude / S_UNIT))  # S_UNIT=0.1
R = exp(-t / S)
# Recall: S += 1 · Travma silinmez (TRAUMA_S_BASE = 10)
```

---

## 7. Layer 1.5 — Prediction Error (tamam)

`evaluator_node` sabit artış yerine beklenen vs gerçekleşen farkını kullanır. Referans: Predictive Minds / Friston; duyusal eşleşme **sentence-transformers MiniLM** cosine similarity (LLM-as-judge yok). Jaccard kelime kesişimi yalnızca diagnostik karşılaştırma için saklanır.

```
agent_node:
  expected_outcome = f(dominant_load_domain)  # natural-language anticipation
  → karar + expected_outcome event payload

evaluator_node:
  prediction_error = 1 - cosine_sim_MiniLM(expected, actual)
  after = apply_prediction_error(before, prediction_error)
  delta = compute_delta(before, after)
  drift_state = update_drift(drift_state, delta)
  → memory record_delta
```

Prediction error tüm homeostatic eksenleri kaydırır; energy için metabolik taban (`ENERGY_DECAY_PER_EVENT`) korunur. Böylece anlamlı delta sınıfları (NORMAL/DEEP/TRAUMA) üretilebilir — Layer 0/1'deki sabit artış NO_TRACE sınırı aşıldı.

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

`agent_node` son delta üzerinden marker üretir ve system prompt'a tek satır bias enjekte eder.

### Drift

```
DriftState(flags: dict[str,bool], magnitudes: dict[str,float])
update_drift: travma → flags[domain]=True,
  magnitudes[domain] = current + magnitude × exp(−current / TRAUMA_DECAY_BASE)
  # TRAUMA_DECAY_BASE = 1.0
get_drift_bias: flagged ise magnitude, değilse 0.0
# kalıcı — healing için heal_drift (Layer 3, HEAL_THRESHOLD=0.6)
```

Bias > 0 ise prompt uyarısı: `Warning: drift detected in {domain} (bias={bias:.2f})`

---

## 9. Layer 3 — Nesil Konsolidasyonu + Drift Healing (tamam)

### DAU-Generation (`generation.py`)

- `TransferCandidate`: DeltaRecord + memory_score + recall_count wrapper
- `select_for_transfer`: memory_score >= 0.6, recall_count >= 1, trauma sadece drift >= 1.5 ise geçer
- `consolidate_generation`: store'dan tüm izleri çeker, filtreler, GenerationRecord paketler
- `apply_generation`: drift kopyalar, generation sayacı artırır, retrieval_context'e inherited izleri yazar
- Constants: `GENERATION_TRANSFER_THRESHOLD=0.6`, `GENERATION_MIN_RECALL=1`, `DRIFT_TRANSFER_MIN=1.5`
- Fitness yolu (`f_agent` verildiğinde): `F_agent < 0.35` → travma izleri silinmez; `inherited_warning=True`, `somatic_scale=-0.3` ile cautionary trace olarak sonraki nesle aktarılır. `retrieval_context`'e `inherited_warning` ve `somatic_scale` alanları eklenerek geçer.

### DAU-DriftHealing (`drift.py` eklentisi)

- `heal_drift`: flagged domain + magnitude >= 0.6 + is_trauma=False → magnitudes azalır
- `HEAL_RATE=0.3` → bir travmayı temizlemek ~5 güçlü deneyim gerektirir
- magnitude=0 olunca flag kalkar
- Constants: `HEAL_THRESHOLD=0.6`, `HEAL_RATE=0.3`

### `state.py`

- `retrieval_context: list[dict[str, Any]]` — inherited memory path
- `generation_record: Any | None` — konsolidasyon kaydı, checkpoint'e yazılıyor

---

## 10. Layer 4 — Society (tamam)

### GovSim Kaynak Fiziği (`environment.py`)

```
P_next = clamp(P + r·P·(1 - P/P_max) - Σe_i, 0, P_max)
collapse = P_next <= P_max · COLLAPSE_EPSILON
# Constants: POOL_MAX=100.0, POOL_REGEN_RATE=0.15, COLLAPSE_EPSILON=0.05
```

### Sosyal Yük Ayrımı (`social.py`)

```
cooperation_stress = clamp((defect_rate) · (1 - trust), 0, 1)
coordination_friction = H(outcomes) · I(last_deadlock)
social_load = clamp(0.5·coop + 0.5·coord, 0, 1)
# Markov pre-node: P(cooperate) deterministik
# strategic expectation → retrieval_context
```

### Cognitive LOD Engine (`lod.py`)

```
T_cognitive = 0.35·(δ/0.7) + 0.25·max_drift + 0.20·coord_friction + 0.20·(1-pool_ratio)
T_COGNITIVE_ESCALATE=0.65 → System 2 (LLM)
T_COGNITIVE_DEESCALATE=0.25, T_COOLDOWN_STEPS=5 → System 1 (NPC)
# npc_decision: deterministik heuristic, 0 LLM token
```

### Fitness-Based Nesil Filtresi (`fitness.py`)

```
F_agent = 0.4·(E/E_max) + 0.3·(1-|ΔP|/P_max) + 0.3·(t_surv/T_gen)
W_transfer = memory_score · F_agent · (1 + tanh(reward - threat))
F_agent < 0.35 → travma izleri silinmez; inherited_warning=True,
  somatic_scale=-0.3 ile cautionary trace olarak sonraki nesle aktarılır.
  retrieval_context'e inherited_warning ve somatic_scale alanları eklenerek geçer.
F_agent >= 0.70 + travma → inherited_warning (somatic scale 0.3)
```

### Graph Wiring

```
social_pre_node → agent_node (LOD: NPC veya LLM) → evaluator_node
  → meta_observer_node → social_pre_node | END
# SYSTEM_2: strategic expectation system prompt'a eklenir
# SYSTEM_1: npc_decision, ChromaDB/LangSmith yok
# Layer 5: meta_observer_node evaluator'dan sonra (closed-loop)
```

---

## 10b. Layer 5 — Metacognition (kod tamam · empirik UNSUPPORTED)

### Mimari geçiş: open-loop → closed-loop (wiring)

v0.9'a kadar tüm kontrol kararları deterministik dış kurallarla alınıyordu: `lod.py` statik `T_cognitive` formülü, `drift.py` pasif metin uyarısı, `evaluator_node` delta hesaplayıp bırakıyordu. Layer 5 sistemi kendi telemetrisini gözlemleyip düzenleyebilir hale getirdi (graph wiring).

### Empirik verdict (v1.0+)

Meta-Observer A/B (Meta ON vs OFF), MiniLM PE altında sistemik iyileşme üretmedi:

- NPC System1 / 20c: `delta_mean_diff = 0`
- System2 / Groq 8c (T=0.2): zayıf farklar (`Δδ≈−0.001`, `Δm_ratio≈−0.10`, `+1 system2_cycles`) — iddia için yetersiz
- **Deterministic seed replay** (`DAU_META_AB_DETERMINISTIC=1`, T=0.0, seed=42, 8c, 2 replicate): tüm farklar **0.0** → önceki zayıf sinyal **stokastik LLM gürültüsü**, aktuator etkisi değil

**Sonuç:** Closed-loop metacognition **UNSUPPORTED**. Kod çalışır; Meta ON/OFF ortalama delta’yı düşürmez. Aktüatör eşikleri (DEEP≥0.7 vb.) yumuşak PE altında nadiren tetiklenir; tetiklense bile LLM/bellek yolu PE’yi iyileştirmiyor.

### Layer 5A — SelfModel (`self_model.py`)

Tüm katmanların telemetrisini tek Pydantic nesnesinde birleştirir (frozen). Alanlar (mevcut state'den okunur, yeni alan üretilmez):

- `delta_current`, `delta_history`, `drift_state`, `emotional_weight`
- `t_cognitive`, `memory_retrieval_scores`, `f_agent`, `generation_count`

Computed field:

```
m_ratio = mean(delta_history) / (delta_current + EPSILON)
EPSILON = 1e-6, META_HISTORY_SIZE = 10
M_RATIO_OPTIMAL = 1.0, M_RATIO_LOW_THRESHOLD = 0.6
```

`build_self_model(state)` → pure assembly, no LLM, no side effects.

### Layer 5B — Meta-Observer Node (`meta_observer.py`)

Out-of-band LangGraph node. `evaluator_node`'dan SONRA çalışır. LLM çıktı metni okumaz. LLM çağrısı yapmaz. Deterministik Python.

Dört aktuatör (sırayla):

**1. `lod_override(self_model, lod_state) → LODState`**

- Koşul: `delta_current ≥ DELTA_THRESHOLD_DEEP` AND `m_ratio < M_RATIO_LOW_THRESHOLD`
- Eylem: `CognitiveMode.SYSTEM_2` zorla, `T_cognitive` formülünü bypass et
- Sabit: `META_LOD_OVERRIDE_ENABLED = True`

**2. `context_prune(retrieval_context, self_model) → list[dict]`**

- Koşul: `variance(memory_retrieval_scores) > META_RETRIEVAL_VARIANCE_THRESHOLD`
- Eylem: `memory_score < META_RETRIEVAL_MIN_SCORE` girdileri at
- Sabitler: `META_RETRIEVAL_VARIANCE_THRESHOLD = 0.3`, `META_RETRIEVAL_MIN_SCORE = 0.4`

**3. `trigger_drift_healing(drift_state, self_model) → DriftState`**

- Koşul: flagged domain var AND `f_agent < META_DRIFT_HEAL_FITNESS_THRESHOLD` AND `somatic_markers["reward"] > META_DRIFT_HEAL_REWARD_MIN`
- Eylem: `heal_drift()` çağır (`drift.py`, Layer 2)
- Sabitler: `META_DRIFT_HEAL_FITNESS_THRESHOLD = 0.5`, `META_DRIFT_HEAL_REWARD_MIN = 0.4`

**4. `trigger_retrieval(state, self_model) → list[dict]`**

- Koşul: `m_ratio < M_RATIO_LOW_THRESHOLD` AND `delta_current ≥ DELTA_THRESHOLD_NORMAL`
- Eylem: ChromaDB supplementary query, `retrieval_context`'e ekle
- Not: `bind_memory_store(agent_id, store)` bağlı değilse deterministic no-op

### Graph wiring

```
social_pre_node → agent_node → evaluator_node → meta_observer_node → (loop | END)
```

`should_continue` `evaluator_node`'dan `meta_observer_node`'a taşındı.

### `state.py` eklentisi

`self_model: Any | None = None` (circular import önlemek için Any, `generation_record` patterni)

### Semantic sensor (Layer 1.5)

`semantic_similarity.py`: frozen `all-MiniLM-L6-v2`, cosine ∈ [0,1], PE = 1 − sim.
Jaccard `_keyword_overlap_ratio` diagnostik için kaldı; PE yolunda kullanılmıyor.
Bilinen MiniLM sınırı: negation / polarity zayıf (refuse≈cooperate kısmen yakın).
Empiric label: `under sentence-transformers MiniLM`.

---

## 11. Mimari durum

| Katman | Durum | Özet |
|--------|-------|------|
| Layer 0 Foundation | ✅ | State, delta, event-clock, constraints, LangGraph döngüsü |
| Layer 1 Memory | ✅ | ChromaDB+SQLite, Ebbinghaus, retrieval, sleep consolidation, memory_bridge |
| Layer 1.5 Prediction Error | ✅ | expected vs actual → MiniLM cosine PE → homeostatic swing |
| Layer 2 Emotion + Drift | ✅ | EmotionalWeight fonksiyonu + kalıcı DriftState graph'ta |
| Layer 3 Generation | ✅ | Nesil konsolidasyonu, miras, drift healing; fitness filtresi Layer 4'e kaldı |
| Layer 4 Society | ✅ | GovSim pool fiziği, cooperation_stress + coordination_friction, T_cognitive LOD engine, F_agent fitness, W_transfer nesil filtresi, graph wiring |
| Layer 5 Metacognition | ✅ kod / ❌ empirik (provisional null) | SelfModel + meta_observer wiring tamam. Meta A/B v1: SUBSTRATE_ABSENT (T=0, System2=0). Protocol C (T=0.2, seed-locked): checkpoint ΔPE≈0 (5…35/40); TPD 500k → pair~32+ System1 kirlenmesi; run 40/40 tamamlanmadan abort. Full 40 tekrar koşulmayacak. Publishable negative finding çerçevesi. Sıradaki: lokal LLM araştırması → LoRA plastisite → Protocol C′. |

---

## 12. Kod ağacı (v1.0+)

```
dau/foundation/
 ├── state.py              — DAUAgentState (+ drift_state, social_state, lod_state,
 │                            env_state, opponent_id, self_model)
 ├── delta.py              — compute_delta, classify_delta, should_persist, is_trauma
 ├── emotional_weight.py   — EmotionalWeight, compute/apply (Layer 2)
 ├── drift.py              — DriftState, update_drift, get_drift_bias, heal_drift (Layer 2/3)
 ├── social.py             — cooperation_stress, coordination_friction, social_load, Markov expectation
 ├── lod.py                — T_cognitive, CognitiveMode, LODState, update_lod, npc_decision
 ├── self_model.py         — SelfModel, build_self_model() (Layer 5A)
 ├── meta_observer.py      — dört aktuatör + meta_observer_node (Layer 5B)
 ├── semantic_similarity.py — MiniLM cosine PE sensor (Layer 1.5)
 ├── constraints.py        — 5 evrensel kısıt
 ├── time_model.py         — EventClock
 ├── graph.py              — LangGraph: social_pre → agent → evaluator → meta_observer
 ├── memory_bridge.py      — graph ↔ memory köprüsü
 ├── generation.py         — TransferCandidate, consolidate/apply_generation
 ├── run_demo.py
 └── tests/                — foundation + emotional_weight + drift + lod + social
                            + generation + meta_observer + prediction_error

dau/memory/
 ├── store.py / decay.py / retrieval.py / consolidation.py
 └── tests/

dau/generation/
 ├── fitness.py            — compute_fitness, classify_fitness, compute_w_transfer
 └── tests/

dau/society/
 ├── environment.py        — EnvironmentState, step_pool, get_pool_ratio, agent_delta_pool
 ├── run_convention_pilot.py / run_convention_pilot_llm.py
 ├── run_meta_ab.py / run_nuance_loss_pilot.py
 └── tests/                — environment + convention + meta_ab + nuance_loss
```

---

## 13. Graph yaşam döngüsü

```
social_pre_node:
  opponent varsa Markov P(cooperate) + entropy → retrieval_context

agent_node:
  expected_outcome → retrieve_relevant → EmotionalWeight bias
  → drift warning (bias>0) → LLM veya npc_decision → Event

evaluator_node:
  prediction_error → InternalState güncelle → compute_delta
  → update_drift → T_cognitive/LOD → record_delta (memory)

meta_observer_node:
  build_self_model → lod_override → context_prune
  → trigger_drift_healing → trigger_retrieval → state.self_model

should_continue (meta_observer sonrası):
  energy ≤ TERMINATION_ENERGY → END else → social_pre_node

run sonu:
  consolidate_run → düşük R sil, TRAUMA güçlendir, edge kur
```

**Stack:** LangGraph · Pydantic v2 · ChromaDB · SQLite/SqliteSaver · Groq Llama-3.1-8b-instant · LangSmith

---

## 14. Test durumu

- Foundation (Layer 0–1): 32
- EmotionalWeight: 8
- Drift: 11
- LOD: 7
- Social: 10
- Prediction Error (MiniLM): 7
- Memory: 8
- Generation (foundation + fitness): 15
- Society environment: 6
- Meta-Observer: 13
- Convention pilot (+ LLM mock): 13
- Meta A/B: 4
- Nuance-loss pilot: 3
- **Toplam: 137 passed**

Empirik koşular (unit dışı): `dau_runs/overnight_audit_results.json`
(convention LLM, Meta A/B Jaccard + MiniLM, deterministic seed replay, nuance-loss).

---

## 15. AMADS / GovSim karşılaştırma

| AMADS / klasik | DAU |
|----------------|-----|
| Trait dışarıdan atanıyor | Trait yaşantıdan inşa ediliyor |
| Her run sıfır | Sonraki run değişmiş başlıyor (memory + drift) |
| Kaynak var, agent değişmiyor | Kaynak → travma → drift → evrim |
| Duygu etiketi / sayı | EmotionalWeight fonksiyonu |
| Zaman = round | Zaman = event + delta büyüklüğü |

---

## 16. Beş evrensel kısıt

| Kısıt | Anlam | DAU karşılığı |
|-------|-------|---------------|
| time_pressure | Her şeyin sonu var | Nesil sonu / konsolidasyon |
| resource_scarcity | Her şey sınırlı | CPR / GovSim fiziği |
| social_pressure | Başkaları var | İşbirliği ≠ koordinasyon (Akata) |
| uncertainty | Bilgi eksik | Eksik bilgiyle karar |
| generation_end | Nesil kapanır | Miras aktarımı (Layer 3) |

---

## 17. Açık sorular (güncel)

- ✅ Duygu fonksiyonu ne? → EmotionalWeight (Layer 2 ✅)
- ✅ Delta = tahmin hatası nasıl bağlanır? → Layer 1.5 ✅
- ✅ Her şeyin bir sonu var → Nesil sonu, konsolidasyon tetikleyicisi ✅
- ✅ Drift healing mekanizması ✅
- ✅ İşbirliği ≠ koordinasyon ayrımı ✅
- ✅ Fitness-based transfer filtering ✅
- ✅ NPC / Gerçek agent geçişi ✅
- ⚠️ Closed-loop metacognition (frozen Groq): Protocol C **provisional null**.
  Tasarım: 40 çift × 50 event, T=0.2, seed 1001–1040, seed-locked ON/OFF.
  Koşu: `dau/diagnostics/run_protocol_c.py` · log: `dau_runs/protocol_c_run.log`.
  Checkpoint (kümülatif mean_ΔPE):
    5/40 → +0.000 · 10/40 → +0.000 · 15/40 → −0.000 · 20/40 → −0.004
    25/40 → +0.009 · 30/40 → −0.000 · 35/40 → +0.000
  Yorum: ΔPE sıfır etrafında gürültü — sistematik H1 (PE düşüşü) yok.
  Limitasyon: Groq TPD 500k doldu (~212 TPD fallback); pair~32+ System2
  substratı bozuldu → temiz çekirdek ~31–32 çift. Run pair=40 META_OFF’ta
  abort; `protocol_c_results.json` / resmi paired t-test yazılmadı.
  Karar: full 40 tekrar koşulmayacak (eğilim net + TPD riski). Resmi
  UNSUPPORTED damgası pair-level vektör olmadan teknik olarak eksik;
  akademik çerçeve: **provisional null / publishable negative finding**.
  H0: μ_ΔPE ≥ 0 · H1: μ_ΔPE < 0 · one-tailed paired t-test, α=0.05
  (tam vektör kurtarılırsa veya Protocol C′ ile yeniden ölçülür).
- ❌ Parametrik plastisite olmadan “yaşantıdan trait”: frozen 8B’de
  context-level metacognition kapalı döngü kuramadı. Açık araştırma:
  lokal LLM + LoRA (delta history → adapter; trait injection yasak).
- Energy floor ve uzun ufuk: gamma=0 erken kapanıyor.
  Uzun koşularda agent'ın hayatta kalması için energy recovery
  mekanizması yeterli mi? METABOLIC_FLOOR · (1 - mean_load) formülü
  düşük yük altında enerji kazandırıyor ama yüksek yük altında
  yetersiz kalıyor. Açık.
- trigger_drift_healing (meta_observer): 100 event long_run'da
  evaluator heal_drift çalışıyor ama meta_observer aktüatörü
  triggered=0. F_agent < 0.5 AND reward > 0.4 koşulları aynı anda
  karşılanmıyor. Eşik kalibrasyonu gerekebilir. Açık.
- Continual learning / parametrik iz? → Roadmap v1.4: lokal LLM + LoRA
  (frozen dönemde yok; açık araştırma)
- LLM embedding match henüz skor değil (W_SEM=0)
- "İyi"yi "kötü"den ayıran mekanizma?
- Öz sorgu nasıl aktive olur?
- Fitness dışarıdan geliyorsa gerçek evrim mi?

### Hâlâ Açık

- Spontaneous convention emergence: 8B frozen model kurumsal mekanizma olmadan kendi kendine anlaşma yapabilir mi?
  - Empirik not (v1.0+): açık kanalda **format sync** (aynı cümle iskeleti) görüldü; **restraint sync** (cooperate/coordinate) LLM 25r pilotunda görülmedi — hepsi defect (75/75). Metrikler ayrıldı: `format_convention_detected` vs `restraint_convention_detected`.
  - **Dürüst akademik iddia:** Dondurulmuş parametreli LLM’ler, harici yaptırım içermeyen açık kanalda hızla söylemsel biçim senkronizasyonu geliştirebilir; bu, davranışsal kısıtlama uzlaşısına (restraint) dönüşmez — ajanlar dilsel kalıpta anlaşırken kaynağı sömürmeye devam eder. Aksiyom-imkânsız değil; empirik sınır.
  - NPC’de görülen restraint kognitif uzlaşma değil: `pool_ratio < 0.3` → conserve kuralının mekanik sonucu.
- Felaket eşiği: pool=0 anında W_transfer eşikleri nasıl otomatik ayarlanır?
- System 2→1 geçişinde nüans kaybı: LLM deneyimi state machine'e özetlenirken ne kaybolur?
  - Empirik not: nüans kaybı mikropilotu doğruladı — System 2 çeşitliliği (10 unique) → System 1 tek NPC aksiyonu (`extract_moderate`).
- Homeostatic recovery nasıl modellenmeli?
  - Seçenek A: Sabit `RECOVERY_RATE` (basit, ama tüm agentlar identik)
  - Seçenek B: Deneyime bağlı recovery — `drift_magnitude` arttıkça recovery yavaşlar (trait injection riski taşımaz; yaşantının sonucu)
  - Seçenek C: Eksen bağımsızlığı — PE domain-spesifik ekseni etkiler; cross-contamination kaldırılır
  - Kritik kısıt: recovery dışarıdan inject edilmemeli; deneyimden (delta history, drift birikimi) çıkmalı.
  - Literatür (araştırılacak): Friston allostasis, Dynamic Affective Dynamics, Synthetic Somatic Markers.

---

## 18. Bilinen Sınırlar

- LOD deescalation: System 2→1 geçişinde LLM karar geçmişi heuristic rule'lara özetlenmiyor (kasıtlı kabul; nüans-loss pilotu ile ölçüldü)
- Pool physics tek havuz: çoklu kaynak havuzu ertelendi
- Layer 1.5: Jaccard **kapatıldı** → MiniLM cosine (`semantic_similarity.py`). Parafraz PE ~0.40 (eski Jaccard 1.0). Negation hâlâ MiniLM zayıf noktası.
- `W_SEM=0`: ChromaDB embedding skorlamada yok
- `F_agent`: doğal seçilim değil — tasarımcı tanımlı dışsal fitness (`0.4·E + 0.3·pool + 0.3·survival`)
- Frozen weights: öğrenme = in-context / DeltaRecord izleri; parametrik plastisite yok
- Meta-Observer A/B:
  - Jaccard dönemi (NPC + System2/4c): `delta_mean_diff=0`
  - MiniLM: NPC System1/20c → diff=0; System2/Groq 8c (T=0.2) → zayıf farklar (gürültü adayı)
  - **Deterministic seed replay** (T=0.0, seed=42, 8c×2): `delta_mean_diff=0`, `m_ratio_mean_diff=0`, `system2_cycles_diff=0` → **STOCHASTIC_NOISE_CONFIRMED**; Layer 5 kapalı döngü iddiası **UNSUPPORTED**
  - Protokol: `DAU_META_AB_DETERMINISTIC=1` → `DAU_LLM_TEMPERATURE=0` + `DAU_LLM_SEED` (`graph.py` / `run_meta_ab.py`)
- Convention: format sync ≠ restraint sync; NPC “restraint” kıtlık kuralıyla (`pool_ratio<0.3` → conserve) tetiklenebilir
- A/B protokolü: PE tek adımda energy’yi sıfırlayabildiği için sabit ufukta `AB_ENERGY_FLOOR` kullanılıyor (ölçüm protokolü notu; uzun ufuk/tükeniş farkını maskeler)
- `expected_outcome`: Chroma-gated lived memory (`retrieve_relevant` → past outcomes); boş store / ilk event’te domain şablonuna fall back. PE artık endojen öngörüye yaklaşabilir (S1 düzeltmesi kısmi).
- DAERM (Dynamic Allostatic Equilibrium Recovery Model) eklendi
  (Faz 5). Saturasyon ve donma çözüldü; 20/20 event magnitude > 0.
  Formüller:
    μ_i(t) = min(M_drift_i / (1 + M_drift_i), 0.75)
    γ(t)   = E(t) / (1 + M_total)
    L_i(t+1) = clamp(L_i + PE_i − γ·(L_i − μ_i), μ_i, 1.0)
  Sabitler: ALLOSTATIC_SETPOINT_MAX=0.75, CROSS_AXIS_SPILLOVER=0.20,
  METABOLIC_FLOOR=0.05 → constraints.py
- DAERM + magnitude decoupling (Faz 6, v1.2): magnitude hesabı
  DAERM recovery'den ayrıldı. Ham PE vektörü üzerinden peak-weighted
  formül:
    M = 0.70 · max(PE_vec) + 0.30 · mean(PE_vec)
    Uniform spillover (S=0.20): M ≈ 0.82 · PE
  PE≥0.854 → M≥0.70 → TRAUMA reachable. ✅
  Sabit: MAGNITUDE_PEAK_WEIGHT=0.70 → constraints.py
  compute_delta(..., raw_pe=float) — raw_pe verilmezse legacy fallback.
- Energy exhaustion + gamma collapse: Final gamma=E/(1+M_total).
  Energy=0 → gamma=0 → recovery durur. Biyolojik olarak doğru;
  enerjisiz agent toparlanamaz. AB_ENERGY_FLOOR sadece
  should_continue için — InternalState.energy'yi yükseltmez.
- expected_outcome endojen yapıldı (Faz 4): ChromaDB geçmiş
  outcome'larından üretiliyor. PE Std=0.256 (öncesi: 0.000).
  Event 1: fallback (boş store), Event 2+: memory-gated.
- run_demo → meta_observer_node bağlantısı düzeltildi (Faz 2):
  Graph wire doğruydu; run_demo farklı instance kullanıyordu.
  Düzeltme sonrası called=100/100.
- Event-level PE logging eklendi (Faz 2):
  dau_runs/overnight_audit_results.json → runs[] array,
  her event için prediction_error + delta_magnitude + delta_class.
- Meta A/B v1 (DAERM öncesi + sonrası): Her iki dönemde de
  META_ON = META_OFF (diff=0). DAERM öncesi: sistem donuyordu.
  DAERM sonrası: T=0 + NPC System1 → system2_cycles=0 → meta_observer
  etki edemez. Kök neden: deterministik seed kapalı döngüyü değil
  gürültüyü sıfırlıyor; System2 yoksa metacognition substrat bulamıyor.
- Protocol C (Seed-Locked Counterfactual) koşuldu (kısmi):
  T=0.2 + master seed · 40 çift tasarımı · script:
  `dau/diagnostics/run_protocol_c.py`.
  ~1139 LLM çağrısı · ~213 rate-limit fallback (1× TPM, ~212× TPD).
  Checkpoint mean_ΔPE ≈ 0 (gürültü; H1 yok). Temiz çekirdek ~31–32 çift
  (TPD öncesi). pair=40 META_OFF abort; JSON/t-test yok.
  Full 40 tekrar **yapılmayacak**. (Bkz. Section 17, Roadmap)
- Null sonuç akademik çerçevesi (v1.4, provisional):
  "mimari hatalı" değil —
  "frozen-weight LLM'de context-level metacognition, parametrik
  plastisite olmadan kapalı döngü kuramıyor"
  → publishable negative finding. Paper + çalışan sistem hedefi:
  bu bulgu frozen dönemi kapatır; lokal LLM+LoRA devam bölümüdür.

### Roadmap (v1.4 — sıradaki)

Frozen Groq Layer 0–5 empirik dönemi **belgelendi**. Sıradaki:

1. **Belgeleme sabitleme (bu sürüm)** — Protocol C provisional null +
   limitasyonlar Master’da; full Groq Protocol C tekrar koşusu yok.
2. **Lokal LLM araştırması** — Hugging Face / transformers +
   bitsandbytes; Llama-3.1-8B (4-bit) hedef GPU: RTX 4070 Notebook (~8GB).
   Lokal inference tek başına null’u çözmez (yine frozen).
3. **Yaşantı-koşullu LoRA** — peft adapter; nesil sonu delta history →
   training signal. Trait injection yasak; sinyal yalnızca yaşantıdan.
   Layer 3 sınırına `lora_update` adayı. Omurga (state/delta/DAERM/LOD)
   korunur; backend + plastisite sözleşmesi değişir (smooth swap değil).
4. **Protocol C′** — LoRA sonrası aynı counterfactual protokol;
   H1 yeniden test. Metacognition sinyali parametrik ize dönüşebilir mi?
5. **Paper** — paralel: (i) trait injection neden yetmez, (ii) DAERM,
   (iii) format≠restraint convention, (iv) metacognition null,
   (v) frozen sınır → LoRA motivasyonu.

### Anti-roadmap (kaynak koruma)

Hâlâ yasak: Layer 6 icat etme · LLM-as-judge · trait injection ·
wall-clock zaman · Jaccard’ı ana PE’ye geri alma · multi-pool fizik ·
kuantum-LLM hayali.

**Güncellendi (v1.4):** “parametrik fine-tune yasak” kaldırıldı —
yerine **kontrollü, yaşantı-koşullu LoRA araştırması** açıldı.
Full-weight fine-tune ve dışarıdan trait/personality adapter’ı hâlâ yasak.

---

## 19. Versiyon geçmişi

| Ver | Tarih | Not |
|-----|-------|-----|
| 0.1 | 2026-07-30 | İlk taslak |
| 0.2 | 2026-07-30 | Nesil aktarımı, zaman modeli, orchestrator |
| 0.3 | 2026-07-30 | 5 evrensel kısıt, fizyolojik eksen hiyerarşisi |
| 0.4 | 2026-07-30 | DAU Pathway: 6 katman, araştırma listesi |
| 0.5 | 2026-08-01 | Akademik havuz, Foundation tamamlandı |
| 0.6 | 2026-08-01 | Layer 1 Memory + SleepConsolidation, Graph-Memory, 32+8 test |
| 0.7 | 2026-08-01 | Layer 1.5 prediction_error; Layer 2 EmotionalWeight + DriftState; graph wiring; 53 test geçiyor |
| 0.8 | 2026-08-01 | Layer 3 tamamlandı: GenerationConsolidation + DriftHealing + state.py formal fields. 66 test geçiyor. |
| 0.9 | 2026-08-03 | Layer 4 tamamlandı: Society (environment, social, lod, fitness, graph wiring). 95 test geçiyor. |
| **1.0** | **2026-08-04** | Layer 5 tamamlandı: SelfModel (S_self), meta_observer_node, dört aktuatör (lod_override, context_prune, drift_healing, trigger_retrieval), graph wiring. Travma birikimi azalan getiri. Başarısız agent travmaları cautionary trace olarak korunuyor. 109 test geçiyor. |
| **1.0+** | **2026-08-04** | Empirik denetim + MiniLM PE: convention format≠restraint; Meta A/B; nüans-loss. Deterministic seed replay → S2 zayıf sinyal = gürültü; L5 kapalı döngü **UNSUPPORTED**. **137 test**. |
| **1.0++** | **2026-08-04** | Memory-cued `expected_outcome` (PE dağılımı açıldı). Bilinen sınır: InternalState saturasyonu → PE canlı / delta=0 / aktüatör `triggered=0`. Açık soru: homeostatic recovery (A/B/C; Friston allostasis). |
| **1.1** | **2026-08-05** | DAERM implement edildi (Faz 5): allostatic recovery, endojen γ(t), domain PE vektörü. Saturasyon çözüldü. expected_outcome endojen (ChromaDB-gated). PE Std=0.256. lod_override + trigger_retrieval triggered=100/100. DAERM+TRAUMA çelişkisi tespit edildi — açık. 137 test passed. |
| **1.2** | **2026-08-05** | Magnitude decoupling (Faz 6): peak-weighted M = 0.70·peak + 0.30·mean, raw_pe bağımsız. TRAUMA reachable (PE=0.876 → M=0.718). Production spillover pin kaldırıldı. Energy/γ collapse + meta heal eşiği açık. 137 test passed. |
| **1.3** | **2026-08-06** | Protocol C tasarlandı: seed-locked counterfactual paired sampling, 40 çift × 50 event, T=0.2, seed 1001–1040. Meta A/B v1 null sebebi netleşti: SUBSTRATE_ABSENT (System2=0). Master güncellendi. |
| **1.4** | **2026-08-06** | Protocol C kısmi koşu: checkpoint ΔPE≈0 (provisional null); TPD 500k → pair~32+ kirlenmesi; 40/40 abort; full tekrar yok. Roadmap: lokal LLM araştırması → yaşantı-koşullu LoRA → Protocol C′. Anti-roadmap: kontrollü LoRA açıldı. 137 test. |

---

Bu döküman her önemli katman tamamlanınca güncellenir.  
Versiyon 1.4 — Protocol C provisional null belgelendi; sıradaki lokal LLM + LoRA araştırması.
