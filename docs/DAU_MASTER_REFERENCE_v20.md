# DAU — Master Reference

**Versiyon 2.5** · 2026-08-18
**Dosya:** `docs/DAU_MASTER_REFERENCE_v20.{md,html,pdf}`
*(`.md` kaynaktır. ⚠ `.html` ve `.pdf` **v2.4.3'te kaldı** — v2.4.4'ün
§26'sı ve v2.5'in §27'si orada **yok**. `.md` tek güncel kaynaktır.
Önceki üretim v2.4.3'te yapılmıştı —
pandoc; PDF'te emoji'ler metin karşılığına çevrildi (`✅` → `[OK]` vb.)
çünkü LaTeX fontunda karşılıkları yok. Anlam korunur, yalnız PDF'in görüntüsü
md'den farklıdır.)*

---

## 🔔 v2.4.4 — EVRENİN FİZİĞİ DEĞİŞTİ (2026-08-13)

**v2.4.3 bir null sonuçla kapanmıştı. Ondan sonra o null'ın sebebi ölçüldü
ve evren değiştirildi.**

| | |
|---|---|
| Sebep | Seçilim katmanı atıldı: `f_agent`=0.000 · `energy`=0.000 · `fitness_class`=`low`, **120/120 kolda** (D-060); enerji **yapı gereği** artamıyordu (D-061) |
| Değişiklik | Hasat enerjiye dönüyor (**içbükey** kazanç), havuz defteri **gerçekleşeni** yazıyor, tükenmek **öldürüyor** (D-066); kasa saati fazlar arasında sürüyor (D-067) |
| İlk pilot | Sınıf bariyeri **kırıldı** (`low` 0.208 vs `normal` 0.413), yaşamlar 19 ve 10 olayda bitti, varis ömrü kola göre değişti (D-068) |
| ⚠ Yeni sorun | Uç nokta **%71 padding**'e boğuldu; `E_final` hâlâ 0.000 (ölüm kuralının kendisi yüzünden) |

⚠ **`dau_runs/`'daki hiçbir koşum bugünün aletiyle karşılaştırılamaz** — bu,
D-036/D-037/D-042'den **daha büyük** bir kırılmadır: onlar aletin nasıl
ölçtüğünü, bu ölçülen evreni değiştirdi.

Ayrıntı **§26'da**. Aşağıdaki v2.4.3 kutusu **tarihçe olarak** duruyor.

---

## 🔔 v2.4.3 — DOĞRULAYICI KOŞUM YAPILDI, SONUÇ NULL

**Bu belgenin bütün anlatısı, henüz sonucu olmayan bir projeye aitti.
Artık sonuç var.**

| | |
|---|---|
| Koşum | seed **2004–2043**, N=40, iki batch, ~13.1 saat |
| Birincil (ön-kayıt §3) | `a_s − b_s`, eşleştirilmiş Wilcoxon, **p = 0.9914**, `d_z = −0.000` |
| Karar | **H0 reddedilemedi** |
| §11 sınıfı | **ALET NULL'I** — §5 geçerlilik kapısından üç kriter düştü (**D-053**) |
| Rapor | **`docs/B2_RESULTS.md`** — sonucun ne olduğu *ve ne olmadığı* orada |

⚠ **"Etki yok" denemez** (§9-S4/D-047, koşum görülmeden bağlandı). Doğru
ifade: *"`d_z ≥ 0.465` büyüklüğünde etki yok; altındaki için veri bilgisiz."*
⚠ **Mekanizma hakkında hüküm verilemez** — sonuç alet null'ı sınıfında.

Ayrıntı §23'te (yeniden yazıldı) ve §25'te (D-045…D-053).
⚠ **§23 v2.4.3'te yazıldı ve D-066 sonrası eskidi** — *"sıradaki iş"* dediği
şeylerin çoğu yapıldı; güncel durum §26'da ve `CLAUDE.md` §1'de.

---

## ⚠ v2.4.2 okuma uyarısı — önce bunu oku

Bu belge 2026-08-08'de v2.4.1 olarak yazıldı ve o tarihten sonra alet
**yirmi kez** değişti. v2.4.2 anlatıyı yeniden yazmıyor; **yanlış olan
yerleri işaretliyor ve eksik olanı ekliyor.** İşaretsiz her bölüm hâlâ
v2.4.1 anlatısıdır.

**Otorite sırası:** `CLAUDE.md` (güncel durum) → `docs/DECISIONS.md`
(**D-001…D-053**, append-only, kanıtlı) → `docs/PREREGISTRATION.md`
(🔒 **KİLİTLİ**, `befd72b4ee57`) → **`docs/B2_RESULTS.md`** (sonuç) →
**bu belge**. Çelişki görürsen bu belge kaybeder.

### Bu belgedeki sayıların hiçbiri bugünkü aletten değil

Üç ayrı kırılma, sırayla:

1. **D-036** — ölçüm penceresi 10 olaydan **fazın tamamına** çıktı. Belgedeki
   her ΔPE, 50 olaylık fazın **ilk beşte birinin** ortalamasıydı.
2. **D-037** — `TORCH_DETERMINISTIC_WARN_ONLY=False`. Öncesinde aynı seed +
   aynı kod iki koşumda **farklı adapter** üretiyordu; koşum-arası gürültü
   0.026, ölçülen etki 0.015–0.025 ⇒ **gürültü etkiden büyüktü**.
3. **D-042** — adapter graft'ı süreçteki konumdan bağımsız hale geldi.
   Öncesinde `lived` daima taze bir graft'tan, `shuffle` daima bir kez
   eğitilip sıfırlanmış olandan eğitiliyordu ⇒ birincil karşıtlığın içinde
   **sistematik** bir terim.

⇒ **§18'in empirik tablosu, §10b'nin verdict'i ve başlıktaki bütün ΔPE
değerleri bugünkü aletle karşılaştırılamaz.** Silinmiyorlar — tarihçe olarak
duruyorlar — ama etki iddiası olarak okunamazlar.

### Belgeye girmemiş, tamamen eksik olan katman

**Preflight değişmez sistemi** (`dau/diagnostics/preflight.py`) ve **alet
kimliği** (`tool_identity.py`) bu belgede **hiç geçmiyor**. İkisi de bugün
projenin en sağlam parçası. Bkz. yeni **§24**.

---

## Bugünkü gerçek durum (2026-08-11)

| Ne | Değer | Kaynak |
|---|---|---|
| Backend varsayılanı | **`local`** (groq legacy) | D-018 |
| Model | `meta-llama/Meta-Llama-3.1-8B-Instruct` — ölçüldü, Qwen kapı altında | D-026 |
| Quantization | NF4 + `double_quant`, **açıkça yazılı** | D-020/D-024 |
| Sampling | **greedy** (`do_sample=0`) — ⚠ belge boyunca `=1` yazıyor | D-026 · pre-reg S1 |
| Ölçüm penceresi | **fazın tamamı** (`PE_WINDOW_EVENTS=0`) — ⚠ belge boyunca `W=10` | **D-036** |
| Determinizm | strict; aynı seed+kod **bit düzeyinde** aynı | **D-037**, D-038 |
| DPO | β=0.1 · **lr=1e-6** · epochs=1 · batch=1 · grad_accum=4 · max_seq=512 | D-027/28/29 |
| DPO prompt'u | **kararın verildiği prompt'un kendisi** | **D-032** |
| Polarite kapısı | **kosinüs** `[0.25, 0.80]`, MiniLM (NLI değil) | **D-032** |
| Shuffle kolu | **çiftlerin tamamı ters** (eskiden %50 yazı-tura) | **D-040** |
| Adapter graft'ı | sabit `LORA_INIT_SEED`, konumdan bağımsız | **D-042** |
| Değişmez kapıları | **20 kayıtlı** (belgede tanımlı 25'ten) | D-012, D-039, D-041 |
| Test | **582 passed, 2 deselected** (v2.5; 35 dosyada 551 test fonksiyonu) — ⚠ belge boyunca 206 | — |
| Ön-kayıt | **taslak**, 5 slot kapalı, S4/S2 açık | `PREREGISTRATION.md` |

### Kapanmış iki büyük darboğaz

- **Çift darboğazı (D-032):** eğitim 51 token'lık, `system=""` olan sentetik
  bir prompt altında koşuyordu; çıkarım 246–306 token. Üstelik prompt cevap
  anahtarını veriyordu — PE karardan **sonra** hesaplanır. Artık eğitim,
  kararın gerçekten verildiği prompt'la yapılıyor.
- **Çeşitlilik tavanı:** 50 olayda `n_unique` 7'den **22–29**'a çıktı, kapı 5
  (D-026, D-034). §18'in "greedy plato yapar" reçetesi bu ölçümle çürüdü.

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

⚠ **v2.4.3'ten sonra eksik (D-066):** bu denklem enerjinin **yalnız düşen**
tarafını anlatıyor ve o haliyle `decay ≥ recovery` yapısal olarak her zaman
doğruydu (D-061'in cebirsel kanıtı) — enerji 2. olayda tabana vurup yaşamın
%96'sında sıfırda kalıyordu. Artık **üçüncü bir terim** var: hasat enerjiye
dönüyor (`gain = 0.50·x/(2.0+x)`, `x` = **gerçekleşen** hasat) ve enerji
tükenince yaşam **biter**. Bkz. §26.

### ADIM 5 — Precision-weighted PE (kodlandı; v2.4 adaptif)

`semantic_similarity.compute_precision_weight` / `apply_precision_weighting`
+ `DAUAgentState.pe_history` (graph `evaluator_node` yazar).

#### v2.3 ve öncesi formül — sabit kazanç, tarihsel

Bu formülle alınan tüm empirik sonuçlar (C′ N=15 vb.) **sabit-kazanç aleti**
ile ölçülmüştür — iddialar kilitli kalır; alet etiketi §10b’de.

```
variance = var(pe_vector.values())        # tek event, history yok
π        = 1 / (variance + PRECISION_EPSILON)
π_clamp  = min(π, PRECISION_MAX_WEIGHT)   # = 1.2 her girdi için
PE_w     = min(raw_pe · π_clamp, 1.0)
```

PE ∈ [0,1] ⇒ örnek var ≤ 0.5 ⇒ π ≥ 2.0 ⇒ tavan **her zaman** bağlayıcı;
fiili davranış `π ≡ 1.2`. Tavan 3.0→1.2 (541c02c): ölçülen raw PE
**0.2875–0.8102**; 3× kazanç 10 event’in **7’sini** tam `1.0`’a doyuruyordu.
1.2 tavanı 0.81 tepesini 0.97’de tutar. Eski regresyon:
`test_clamp_binds_for_every_pe_vector_in_unit_interval` (silindi, v2.4).

#### v2.4+ — rolling history + VAR_REF ölçekleme

```
# π, pe_history'ye raw_pe EKLENMEDEN önce hesaplanır; sonra unweighted
# raw_pe append edilir (kendi çıktısını beslemez).
variance = sample_var(pe_history)         # son W raw PE skaler
π_raw    = 1 / (variance / VAR_REF + ε)
π        = clamp(π_raw, MIN_WEIGHT, MAX_WEIGHT)
PE_w     = min(raw_pe · π, 1.0)
```

```
PRECISION_EPSILON         = 1e-6
PRECISION_HISTORY_WINDOW  = 10
PRECISION_MIN_HISTORY     = 2      # cold start → π = 1.0
PRECISION_VAR_REF         = 1/12   # Uniform[0,1] pop. variance
PRECISION_MIN_WEIGHT      = 0.5
PRECISION_MAX_WEIGHT      = 1.2    # doygunluk bütçesi korunur
```

Cold start (`len(pe_history) < MIN_HISTORY`): nötr `π = 1.0`.
Sakin (düşük var) → π → MAX; kriz/yüksek var → π → MIN (dampen).
Sınır notu: tipik sakin pencerelerde π hâlâ 1.2’ye yakın doyabilir;
gerçek dampen çoğunlukla yüksek-varyans rejimde. Regresyon:
`tests/test_precision_pe.py` (rolling-history suite).

#### Precision smoke doğrulama (v2.4.1)

| Koşum | Param | Sonuç | Artefakt |
|-------|--------|--------|----------|
| v1 (ön-kayıtlı usable-only) | events=10, N=3, seeds 9101–9103 | **INCONCLUSIVE** — instrument starvation (`n_pe_events=0`; diversity gate lived+shuffle 3/3) | `dau_runs/protocol_c_prime_precision_smoke.json` (+ `_v2.log`) |
| v2 (exploratory all-audit) | aynı seed/events | teşhis; pair-gate bağımsız; confirmatory değil (`2528e79` dual gates) | aynı JSON `smoke_gates_v2` |
| **v3 (resmi smoke)** | events=22, N=3, seeds 9201–9203 | **PASS** — `n_pe_events=396`, `saturation_rate=0.0025`, `pi_n_distinct=14` (bant ~0.76–1.2), `null_arm_clean=true`, `n_gated=0` | `dau_runs/protocol_c_prime_precision_smoke_v3.json` |

v3 ile precision fix **davranışsal olarak doğrulandı** (alet sağlıklı:
doygunluk düşük, π çeşitli, null temiz). Formül commit: `231c222`.

> **Informal gözlem (etki iddiası DEĞİL):** v3 mean ΔPE lived≈0.107 ·
> null=0.0 · shuffle≈0.017 — lived kolu belirgin yüksek. Bu **N=3 smoke
> ölçümü**; istatistiksel güç **YOK**; hipotez testi değil. Asıl test
> çok-nesilli N=15 pre-registered koşumda yapılacak. Bu satır gelecekte
> **“etki doğrulandı”** diye okunamaz.

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

### ⚠ v2.4.3: konsolidasyon deney yolunda **nereye** bağlı (D-022/D-031)

Yukarısı konsolidasyonun **ne yaptığını** anlatıyor; v2.4.1'de eksik olan,
deney yolunda **ne zaman** koştuğuydu. GAP-14 bunu *"hiç kimse çağırmıyor"*
diye açmıştı ve **belge yanılmıştı** — demo yolu çağırıyordu, deney yolu
çağırmıyordu.

**Karar (D-031, uygulama `987a1bc`): faz-2'den sonra, `transfer_to_heir`'den
hemen önce.** Reddedilen alternatifler: *faz-1 sonrası* ve *her iki faz
sonrası*.

**Gerekçe — `null` kolunu korumak.** Gen1 iki yaşam sürüyor (faz-1 → eğitim
→ faz-2) ve `delta_pe = pe_after − pe_before` aradaki **tek müdahaleyi**
(eğitimi) yalıtmak için var. `null` iki fazı da eğitimsiz koşuyor ⇒
`delta_pe ≈ 0` olmalı, kontrolün varlık sebebi bu. `run_consolidation`
**siliyor** (Ebbinghaus). Fazların **arasına** girerse faz-2 farklı bir kasa
görür ve `null`'ın `delta_pe`'si **saf unutma etkisi** olur — kontrol,
ölçmesi gereken sıfırı ölçemez hale gelir. Faz-2 seçeneği bunu yapmıyor.

### İlk ölçüm (B2, N=40, 120 kol)

Konsolidasyon raporu JSON'a **hiç girmiyordu**; `060d907` ile bağlandı
(D-051'in yan bulgusu). İlk kez görünen sayılar:

| Kol | `deleted_count` ort. | aralık |
|---|---|---|
| `lived` | 25.25 | 10 – 57 |
| `null` | 24.52 | 8 – 56 |
| `shuffle` | 24.93 | 10 – 63 |
| **toplam** | **24.90** | 8 – 63 |

Rapor ayrıca `strengthened_count`, `edges_created`, `drift_flag_count` ve
`now_counter` taşıyor. Kollar arası fark yok — beklenen, çünkü konsolidasyon
adapter'dan bağımsız çalışıyor.

⚠ **İki ilan edilmiş sınır buraya bağlı:**
- **L15** — Ebbinghaus **kasada** çalışıyor, çift kurucu kasayı **hiç
  okumuyor** ⇒ kanal 2 unutmaya **bağışık**, kanal 1 değil. Bir anı
  unutulup varise geçmese bile, ondan türetilmiş çift ağırlıkları **çoktan
  eğitmiştir**. Hata değil, "iki kanal"ın tanımı — ama D-002'nin *"ikisi de
  yaşamın izidir"* cümlesi bunu taşımıyor.
- **L16** — `now_counter = 50` (faz-2 uzunluğu) kullanılıyor ve faz-2
  `EventClock`'u sıfırdan sayıyor ⇒ faz-1 anıları bir faz daha taze
  görünüyor (GAP-19). Etkisi şu an **bloke** ama **gizli**: `F_agent` tek
  başına düzeltilirse canlanır (D-051).
  ✅ **KAPANDI (D-067).** Kasa `counter_base` tutuyor; `F_agent` D-066'da
  canlandığı için düzeltme **aynı gün** yapıldı, D-051'in *"ikisi birlikte ya
  da hiçbiri"* şartına uyularak. L16 artık tarihçedir.

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
(crisis 5 test). **Kablolama:** `graph.py` `pool_step_node` →
`step_pool_with_crisis` (meta_observer sonrası). Extraction:
`dau/society/extraction.py` (`decision_to_extraction`).

### Sosyal yük / LOD / Fitness

```
social_load = 0.5·cooperation_stress + 0.5·coordination_friction
T_cognitive = 0.35·(δ/0.7) + 0.25·max_drift + 0.20·coord_friction + 0.20·(1-pool_ratio)
F_agent = 0.4·(E/E_max) + 0.3·(1-|ΔP|/P_max) + 0.3·(t_surv/T_gen)
```

⚠ **Formül değişmedi, girdileri değişti (D-066/D-068).** B2'de üç girdinin
ikisi sabitti (`E`=0.000 ve `t_surv/T_gen`=1.0, 120/120 kolda) ve skor
120/120 `low` okuyordu. Metabolik döngü kapandıktan sonra `t_surv` ve `ΔP`
canlandı — pilotta sınıf bariyeri **ilk kez kırıldı** (`low` 0.208 vs
`normal` 0.413). ⚠ Ama `E` **hâlâ 0.000**, çünkü artık ajanlar tükenerek
ölüyor ve tükenerek ölenin son enerjisi tanımı gereği sıfır. Bkz. §26.

NPC conserve kuralı: `NPC_POOL_RATIO_CONSERVE=0.3` (crisis eşiği ile hizalı).

### Graph wiring

```
social_pre_node → agent_node → evaluator_node → meta_observer_node
  → pool_step_node → (social_pre | END)
```

---

## 10b. Layer 5 — Metacognition (kod tamam · empirik UNSUPPORTED)

### Empirik verdict (kilitli)

- Meta A/B: deterministic seed replay → tüm farklar 0 → **STOCHASTIC_NOISE_CONFIRMED**
- Closed-loop metacognition **UNSUPPORTED (paper-locked)**
- Protocol C (Groq frozen): ΔPE≈0 gürültü → **paper-locked negative finding**
  (temiz çekirdek ~31–35 çift; resmi paired t-test yok; full 40 tekrar yok)
  *[instrument: ADIM 5 fixed-gain π≡1.2, pe_vector-based — PE yolu
  evaluator üzerinden; iddia geçersiz kılınmaz, yalnızca alet etiketi]*
⚠ **v2.4.2: aşağıdaki üç C′ satırı da D-036/D-037/D-042 öncesi.** Alet
etiketleri (`fixed-gain π≡1.2`) doğru ama eksik — pencere, determinizm ve
graft konumu da o tarihte bugünkünden farklıydı.

- **Protocol C′ N=15 (eski reçete, 2026-08-07 gece):** 50 event/arm ·
  `lived −0.008935 · null −0.009007 · shuffle −0.002849 · t=0.019 · p=0.985`
  → harness **INCONCLUSIVE**, belge **`INSTRUMENT_LIMITED_NULL`**
  *[instrument: ADIM 5 fixed-gain π≡1.2, pe_vector-based]*
  (artefakt: `dau_runs/protocol_c_prime_results.json`)
- **C′ düzeltme sonrası mini-test (N=1, seed=9101, 10 event, sampling + yaşam-PE):**
  `lived −0.180 · null 0.000 · shuffle −0.149` · sıra `lived < shuffle < null`
  · null faz1≡faz2 → **`SAMPLE_LIVED_PE_SEPARATION`** (significance yok)
- **C′ N=15 sampling+B final (2026-08-07, GPU ~76 dk):** 50 event/arm ·
  ön-kayıtlı `W=10` ⚠ **D-036 ile geçersiz — pencere artık fazın tamamı** ·
  diversity `K=5` (5-seed tarama median) ·
  `lived +0.0081 · null 0.0000 · shuffle +0.0190` ·
  t=−0.485 · p=0.637 · Wilcoxon p=0.850 · n_eff=12 (gated 3: 2001/2007/2013) ·
  `null_arm_clean=True` → harness **INCONCLUSIVE** · belge
  **`SAMPLE_N15_UNDERPOWERED`**
  *[instrument: ADIM 5 fixed-gain π≡1.2, pe_vector-based]*
  (artefakt: `dau_runs/protocol_c_prime_results.json`; eski greedy sonuçlar
  `dau_runs/archive_cprime_instrument_limited_*`)

**`INSTRUMENT_LIMITED_NULL` ne demek:** “yaşantı-LoRA’nın etkisi yok” **değil**;
**“o koşumdaki ölçüm aletiyle bir etki görülemez”**. Dayanak o koşumda:
(1) gizli `maybe_lora_update_after_life` null’u da eğitiyordu; (2) greedy +
tohum trajektoriyi değiştirmiyordu (N=15≈N=1 kopya); (3) plato tercih
verisini öldürüyordu; (4) tasarımcı `PREF_EXPECTED` trait-adjacent’tı.
Eski C′ null’ı Protocol C null’ı ile **aynı statüde sunulmamalıdır**.

**`SAMPLE_LIVED_PE_SEPARATION` ne demek:** düzeltme zinciri + `DAU_LLM_DO_SAMPLE=1`
+ yaşam-PE tercih ile tek seed’de H1 yönü görüldü; N=1 — istatistik iddiası yok.

**`SAMPLE_N15_UNDERPOWERED` ne demek:** alet bütünlüğü tutuldu (`null ΔPE=0`);
mean lived &lt; mean shuffle (+0.008 &lt; +0.019) ama **ikisi de ≥0** (mini’deki
−0.180 çoğalmadı); p n.s.; diversity gate 3 seed düşürdü → n_eff=12 &lt; 15 →
**N&lt;15 istatistik iddiası yok**. “Etki yok” diye sunulmaz; underpowered +
zayıf/gürültülü yön.

### Aktüatörler (deterministik Python, LLM okumaz)

1. `lod_override` — DEEP + düşük m_ratio → System 2 zorla
2. `context_prune` — yüksek retrieval variance → düşük skor at
3. `trigger_drift_healing` — düşük F_agent + reward → `heal_drift`
4. `trigger_retrieval` — düşük m_ratio + NORMAL+ → Chroma ek sorgu

---

## 11. Mimari durum (v2.3)

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
| ADIM 5 Precision PE | ✅ kod / v2.4 rolling+VAR_REF | Adaptif band açık; sakin≈MAX (§7) |
| ADIM 6 C′ | ✅ kod + N=15 sampling+B | Eski `INSTRUMENT_LIMITED_NULL`; mini **SAMPLE_LIVED_PE_SEPARATION**; N=15 **SAMPLE_N15_UNDERPOWERED** |

---

## 12. Kod ağacı (v2.5)

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
 ├── fitness.py            — F_agent, W_transfer
 ├── reproduction.py       — 321 satır; turnuva (k=2), w tahsisi,
 │                          **price_partition** (+ z_variance /
 │                          selection_estimable, D-121) ve
 │                          **positive_control_partition** (D-121)
 └── population.py         — 147 satır; GenerationPlan / heir_id /
                            plan_next_generation / close_transition (D-101)

dau/society/
 ├── environment.py        — pool physics + apply_crisis_trauma (ADIM 1)
 ├── run_convention_pilot*.py / run_meta_ab.py / run_nuance_loss_pilot.py
 └── tests/

dau/diagnostics/
 ├── run_protocol_c.py     — frozen Meta ON/OFF (paper-locked)
 ├── run_protocol_c_prime.py — C′ harness (ADIM 6; lived/null/shuffle, N≥15)
 ├── run_cprime_multigen.py — 1610 satır; gen1→transfer→gen2 (B2'nin yolu,
 │                          DEĞİŞMEDİ — `prereg/b2-code` etiketi)
 ├── run_population_experiment.py — 1464 satır; **popülasyon sarmalayıcısı**
 │                          (N ajan · G nesil · kol başına ayrı mera);
 │                          I0.3·I0.4·I0.6·I0.7·I1.1·I4.1 + checkpoint
 ├── analyze_population_run.py — 724 satır; dört seviyeye göre okuma;
 │                          **p-değeri üretmez** (test bekçiliğiyle)
 ├── preflight.py          — 1293 satır; değişmez kapıları (I0.1–I5.4);
 │                          ABORT/FLAG modları
 ├── tool_identity.py      — 299 satır; koşumun alet kimliği; yüklenen
 │                          ağırlığı ve ayarları raporlar (+ cuda_allocator)
 └── long_run.py / pe_histogram.py / actuator_audit.py

docs/
 └── PREREGISTRATION.md                     — 🔒 birinci ön-kayıt (B2)
 └── PREREGISTRATION_2.md                   — 🔒 ikinci ön-kayıt (popülasyon)
 └── DAU_MASTER_REFERENCE_v20.md            — operasyonel kaynak (**v2.5**)
 └── DAU_MASTER_REFERENCE_v20.pdf           — türev (md ile senkron)
 └── DAU_MASTER_REFERENCE_v20.html          — türev (stale; md kaynaktır)
 └── DAU_MASTER_REFERENCE_v10.*              — arşiv (v1.4; süpersede)
```

**Adapter kökleri:**
- Runtime tek kök: `dau_runs/adapters/{agent_id}/` (`ADAPTER_BASE_DIR`)
- Dead constant `ADAPTER_ROOT_DIR` / `dau_lora_adapters` kaldırıldı
  (`c9bdbaf`); disk → `archive/dau_lora_adapters_cprime_legacy/` (veri kaybı yok)

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
| Precision PE (ADIM 5) | `test_precision_pe.py` (rolling-history suite) |
| **Collect (v2.4.4 branch)** | **384 passed, 2 deselected** |

*(Master v1.4’teki “137” / v2.2’deki “177” / v2.3’teki “182” / v2.4.1’deki
“206” sayıları önceki kesitler; bu belge **bu branch collect=384** ile
kilitlenir.)*

**NLI flake ÇÖZÜLDÜ (`3d760e8`):** unit path mock HF; gerçek model
`@pytest.mark.integration` (günlük suite dışı). Kök neden: HF Hub canlı
çağrı + ağ kesintisi (`RemoteProtocolError`).

Empirik artefaktlar (`dau_runs/`):
- `protocol_c_run.log` — provisional/paper-locked null izi
- `archive_cprime_instrument_limited_*` — eski greedy N=15
  (`INSTRUMENT_LIMITED_NULL`)
- `protocol_c_prime_results.json` — C′ N=15 sampling+B final
  (`SAMPLE_N15_UNDERPOWERED`)
- `protocol_c_prime_sample_n15.log` — final koşum logu
- `cprime_diversity_prereg_scan.json` — K/W ön-kayıt taraması (5×10 evt)
- Mini sampling+B: `/tmp/cprime_full_arm/dau_runs/protocol_c_prime_sample_pilot.json`
  (`SAMPLE_LIVED_PE_SEPARATION`)
- `protocol_c_prime_precision_smoke.json` — precision smoke v1/v2
  (`smoke_gates_v1` locked; `smoke_gates_v2` exploratory)
- `protocol_c_prime_precision_smoke_v3.json` — precision smoke **v3 PASS**
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
- ✅ Crisis wiring production (`a1ec2b4`) — `pool_step_node` + extraction /
  `long_run` çift-step düzeltmesi
- ✅ Adapter kök temizliği (`c9bdbaf`) → `archive/dau_lora_adapters_cprime_legacy/`
- ✅ NLI flake (`3d760e8`) — unit mock + `@pytest.mark.integration`
- ✅ Memory vault no-op (`231c222`) — `MemoryStore.seed_inherited_record` /
  `apply_generation` yazar; EW `inherited_warning` / `somatic_scale` tüketir
- ✅ **ADIM 5 precision — formül** (`231c222`) rolling history + `VAR_REF` (§7)
- ✅ **ADIM 5 precision — smoke doğrulaması (v2.4.1):**
  - v1 (events=10, N=3, seeds 9101–9103): **INCONCLUSIVE** (instrument
    starvation; diversity gate lived+shuffle 3/3 eledi; `n_pe_events=0`)
  - v2 (exploratory all-audit, aynı seed/events): teşhis; confirmatory değil
  - **v3 (events=22, N=3, seeds 9201–9203): RESMİ PASS** — `n_pe_events=396`,
    `saturation_rate=0.0025`, `pi_n_distinct=14` (bant ~0.76–1.2),
    `null_arm_clean=true`, `n_gated=0`. Precision fix davranışsal doğrulandı.

### Hâlâ açık

- **C′ etki sorusu** — N=15 sampling+B aleti temiz ama n_eff=12 + n.s. →
  H1 desteklenmedi; mini −0.180 N≥15’e taşınmadı. Yeni ön-kayıt olmadan
  K/W oynatılamaz (post-hoc yasak)
- ~~**ADIM 5 precision** formül + smoke doğrulaması~~ → **ÇÖZÜLDÜ**
  (v2.4 formül + v3 PASS; §7)
- **Çok-nesilli Protocol C′ pre-registration henüz yazılmadı** — sıradaki
  oturumun ilk görevi (§23)
- **Pool collapse → terminasyon mantığı henüz kablosuz** —
  `EnvironmentState.collapsed` / `COLLAPSE_EPSILON` üretiliyor ama
  `should_continue` yalnızca `MAX_EVENTS` + `TERMINATION_ENERGY` bakıyor;
  crisis travması terminasyon değil (somatik), collapse için ayrı END
  koşulu henüz yok
- Energy floor / γ=0 erken kapanma
- Meta `trigger_drift_healing` eşik kalibrasyonu
- Spontaneous convention: format sync ≠ restraint sync
- ~~`test_nli_filter.py` kırılganlığı~~ — **ÇÖZÜLDÜ** (`3d760e8`)
- ~~Legacy disk `dau_lora_adapters/` arşiv~~ — **ÇÖZÜLDÜ** (`c9bdbaf`;
  `archive/dau_lora_adapters_cprime_legacy/`)

### Kapanan (v2.2–v2.3 — bu branch’te ölçüldü)

- ✅ Yerel LLM replay — greedy birebir; sampling’te prompt-keyed seed +
  strict CUDA lock ile null faz1≡faz2
- ✅ Null kontaminasyonu — `_build_lived_examples` artık train etmiyor
- ✅ Tohum = niş (`_seed_niche`) — N=15≠N=1 kopya
- ✅ Tercih hedefi — yaşam-PE ranking (reçete B); tasarımcı cümle yok
- ✅ DPO OOM — `BATCH_SIZE=1` + gradient checkpointing (8GB)
- ✅ Chat-template DPO / eval mode / adapter izolasyonu (önceki commit’ler)
- ✅ Diversity gate + ön-kayıtlı W — 5-seed tarama → K=5; W=10 (mini/null)
  ⚠ **W kısmı D-036 ile geçersiz**: 10-olay penceresi 50 olaylık fazın ilk
  beşte birini okuyordu ve etkiyi kaçırıyordu. K=5 geçerli.
- ✅ C′ N=15 sampling+B koşumu — **SAMPLE_N15_UNDERPOWERED** (§10b)

---

## 18. Bilinen Sınırlar + Plastisite günlüğü

### Bilinen sınırlar (özet)

- LOD System2→1 nüans kaybı ölçüldü (kasıtlı)
- MiniLM negation zayıf; NLI gate yalnızca preference çiftlerinde
- `F_agent` dışsal tasarım skoru (doğal seçilim değil)
- Frozen weights: parametrik öğrenme default **kapalı**
- Protocol C: TPD kirlenmesi; pair t-test yok; claim locked
- C′ v2: N=1 — istatistik iddiası yok
- Crisis: graph `pool_step_node` kablolu (`a1ec2b4`); collapse → END henüz yok (§17)
- ADIM 5 precision: **ÇÖZÜLDÜ (v2.4 formül + v2.4.1 v3 smoke PASS)** —
  rolling history + `VAR_REF` (§7). Sınır: sakin pencerelerde π hâlâ ≈1.2’ye
  doyabilir; v3’te sat≈0.0025 / π_n=14 ile alet sağlıklı ölçüldü. v2.3 ve
  öncesi empirik sonuçlar sabit-kazanç aletiyle alınmıştır (§10b etiketleri).

### Yeni sınırlar (v2.1 tarihsel) → v2.2 durumu

#### 1. Replay non-determinism — **kapatıldı (v2.2)**

Eski N=15’te null faz1≠faz2 sanılıyordu; asıl nedenler sırayla:
gizli train hook, tohumun trajektoriyi değiştirmemesi, sampling’te RNG
kirlenmesi (`switch_adapter` early-return + LoRA reset). Düzeltmeler:
`torch.manual_seed` / CUDA strict lock · prompt-keyed sample seed ·
hook kaldırıldı · niş tohumları. **Ölçüldü:** sampling + aynı agent_id ile
10 event null replay birebir.

#### 2. Metrik plato dilusyonu — ⚠ **D-026 ÇÜRÜTTÜ**

> Aşağıdaki reçete *"greedy plato yapar, sampling şart"* diyordu. Ölçüldü:
> greedy 50 olayda `n_unique` **22–29**, kapı 5 (D-026, D-034). Plato yok.
> Ön-kayıt S1 **greedy**'de karar kıldı — sampling gürültü ekliyor ve GAP-9
> altında gürültü azaltmak çiftten değerli. Metin tarihçe olarak duruyor.

Greedy plato (~3 unique completion / 10 event) tercih verisini öldürüyordu.
`DAU_LLM_DO_SAMPLE=1` (T=0.2) ile unique ≈5. N=15 öncesi: 5-seed tarama →
`DIVERSITY_MIN_UNIQUE=K=5` (median); ⚠ `PE_WINDOW_EVENTS=W=10` **D-036 ile
0'a (fazın tamamı) çekildi**; aşağıdaki gerekçe tarihsel — (mini + null
clean; post-hoc değil). N=15’te 3 seed `n_unique=4` ile gated → n_eff=12.

### Plastisite günlüğü

#### Sinyal v1 vs v2 vs yaşam-PE (v2.2)

| | Sinyal v1 | Sinyal v2 (eski A) | Yaşam-PE (B, v2.2) |
|---|-----------|-------------------|---------------------|
| Kimlik | `pe_delta_trauma_drift_v1` | `pe_ranked_pref_v2` | aynı dosya, yeni ranking |
| Tercih | skalar CE | MiniLM vs **tasarımcı** expected + sabit reject | ajanın kendi kararları, **yaşam PE** |
| Aksiyom | — | ⚠ trait-adjacent | ✅ yalnızca yaşam |
| Mini-test | — | ΔPE ≈ +0.002 (zarar) | sampling ile ΔPE ≈ −0.180 |

#### Empirik tablo

> ⚠ **v2.4.2: aşağıdaki ΔPE sütunlarının hiçbiri bugünkü aletle
> karşılaştırılamaz.** Üç kırılma, hepsi bu tablodan sonra: **D-036** (pencere
> 10 olaydan fazın tamamına — bu satırlar 50 olaylık fazın **ilk beşte
> birinin** ortalaması) · **D-037** (öncesinde koşum-arası gürültü **0.026**,
> ölçülen etki 0.015–0.025 ⇒ gürültü etkiden büyüktü) · **D-042** (eğitim
> kollarının graft'ı süreçteki konuma bağlıydı).
>
> Ayrıca **D-044**: ΔPE'nin kendisi ayrımın %80–86'sını atıyor, yani bu
> sütunlar düşük duyarlıklı bir aletin çıktısı.
>
> Tablo **tarihçe olarak** duruyor. Bugünkü sayılar `dau_runs/`'ta ve
> D-038/D-043'te.

| Deney | N | Backend | Sinyal | ΔPE_lived | ΔPE_null | ΔPE_shuffle | Karar |
|-------|---|--------|--------|-----------|----------|-------------|-------|
| Protocol C (Groq) | ~35 temiz | groq | meta ON/OFF | ≈0 | — | — | **paper-locked null** |
| C′ mini / smoke | ≤3 | local | v1/v2 erken | (tarihsel) | | | **WEAK / SMOKE** (†) |
| C′ N=15 eski | 15 | local | v2+A, greedy, kontamine | −0.0089 | −0.0090 | −0.0028 | **INSTRUMENT_LIMITED_NULL** |
| C′ mini sampling+B | 1 (9101) | local | yaşam-PE + sample | **−0.180** | **0.000** | −0.149 | **SAMPLE_LIVED_PE_SEPARATION** |
| C′ N=15 sampling+B | 15 (n_eff=12) | local | yaşam-PE + sample · W=10 · K=5 | **+0.0081** | **0.000** | +0.0190 | **SAMPLE_N15_UNDERPOWERED** |

**(†)** Gradyansız eğitim / adapter sızıntısı düzeltilmeden önce; ileri sürülmez.

**v2.4.2 eki — bugünkü aletle alınan sayılar** (keşifsel, N=3, hipotez testi
**değil**; seed 2001–2003 yakılmış):

| Koşum | Ne kanıtladı | `lived − null` | `lived − shuffle` |
|---|---|---|---|
| `baseline_d037` + `repro_d038` | **tekrarlanabilirlik**: dokuz kol, altı adapter `sha256` özdeş | +0.025 / +0.045 / +0.017 (**3/3**) | +0.029 / +0.037 / −0.039 |
| `control_d042` (D-043) | D-039…D-042 sonrası **20/20 değişmez**; üç `null` kolu D-038'le byte düzeyinde aynı | +0.004 / +0.018 / +0.072 (**3/3**) | −0.007 / +0.027 / +0.001 |

⚠ N=3'te işaret testinin verebileceği en küçük p **0.25** — hiçbiri anlamlı
değil ve olamaz. Bu koşumların işi sinyal değil **alet doğrulaması**.

#### ⚠ v2.4.3: yukarıdaki iki satır **keşifseldir ve aşılmıştır**

Doğrulayıcı koşum (B2, N=40, seed 2004–2043) yapıldı ve **birincil uç nokta
ΔPE değil doğum-drift'tir** (D-002). Yukarıdaki `lived − null` /
`lived − shuffle` sütunları ΔPE'dir, yani **birincil sonuç değildir** ve
onun yerine okunamaz.

| Koşum | Uç nokta | Sonuç |
|---|---|---|
| **B2 (N=40)** | **doğum-drift büyüklüğü** (ön-kayıt §3) | `a_s − b_s` ort. **−0.0002** · W=217.0 · **p = 0.9914** · `d_z = −0.000` ⇒ **H0 reddedilemedi** |
| B2, ikincil S3 | gen1 ΔPE (fazın tamamı) | ort. **+0.0104**, 24/16 pozitif, **p = 0.070** — iddia edilmiyor |
| B2, ikincil S4 | gen2 ortalama PE | ort. **−0.0128**, **p = 0.035** ama **ters yönde**, medyan 0 — iddia edilmiyor |

⚠ İlginç olan: N=3'lük keşifsel koşumlarda `lived − null` **9/9 pozitifti**
(yukarıdaki tablo). N=40'lık doğrulayıcı koşumda birincil uç noktada
**hiçbir ayrım yok**. Bu, küçük-N keşifsel işaret desenlerinin neden
kanıt sayılmadığının doğrudan örneğidir.

Ayrıntı: **`docs/B2_RESULTS.md`**.

C′ mini sampling+B: 10 event/arm, `DAU_LLM_DO_SAMPLE=1`, `T=0.2`,
`DAU_LORA_ENABLED=1`, yaşam-PE pairs, GPU ≈ 71 sn / seed (3 kol).

C′ N=15 sampling+B final: 50 event/arm, aynı reçete + `W=10` + diversity
`K=5`, GPU ≈ **76 dk** (eski 13 saat CPU tahmini iptal; 1.5–2.5 saat
üst sınırı da aşılmadı). Peak VRAM ≈ **7.2 GiB** train sırasında.

VRAM: peak ≈ **6.4–7.2 GiB** + DPO batch=1 → **GO** (8GB).

#### Paper naratif iskeleti (kilitli)

1. Ana katkı: frozen-weight in-context metacognition null (Protocol C)
2. Mimari: trait yasağı, MiniLM PE, DAERM, LOD, format≠restraint
3. Appendix: C′ alet evrimi — `INSTRUMENT_LIMITED_NULL` (eski) →
   reçete düzeltmesi → `SAMPLE_LIVED_PE_SEPARATION` (N=1) →
   `SAMPLE_N15_UNDERPOWERED` (null clean; n_eff=12; H1 yok)
   → ⚠ **v2.4.3: ön-kayıtlı doğrulayıcı koşum (N=40), birincil null
   (p=0.9914), §11 sınıfı alet null'ı** (`docs/B2_RESULTS.md`)
4. Non-claims: persona LoRA, LLM-as-judge, per-event online LoRA, Layer 6,
   full Groq C rerun, N&lt;15 istatistik iddiası, post-hoc W/K bulgusu,
   eski `INSTRUMENT_LIMITED_NULL` = “etki yok”
   → ⚠ **v2.4.3'te eklenenler:** B2'nin null'ı **"aktarılmıyor" demek
   değildir** (D-047); adapter'ın davranışı değiştirmesi **aktarımın kanıtı
   değildir** (`shuffle` de aynı ölçüde değiştiriyor); S4'ün p=0.035'i
   **sinyal değildir** (ters işaret, §4 önceden bağladı)

---

## 19. ADIM uygulama kaydı (v2.4.1 — bu branch)

### ADIM 1 — Layer 4 Somatic Enforcement ✅ kod + wiring

| | |
|--|--|
| Dosyalar | `environment.py`, `extraction.py`, `graph.py` `pool_step_node` (+ tests) |
| Sabitler | `POOL_CRISIS_THRESHOLD=0.30`, `CRISIS_TRAUMA_MULTIPLIER=2.5`, `CRISIS_BASE_MAGNITUDE=0.4` |
| Davranış | `pool_ratio < 0.30` → resource TRAUMA via `update_drift` |
| Wiring | ✅ production (`a1ec2b4`) — `pool_step_node` → `step_pool_with_crisis`; `long_run` çift-step düzeltmesi |
| Test | crisis 5 unit + `test_graph_crisis_wiring.py` |
| Gap | pool collapse → terminasyon kablosuz (§17) |

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
| Path | `dau_runs/adapters/{agent_id}/` (`ADAPTER_BASE_DIR`; tek runtime kök) |
| Rank/α | `PER_AGENT_LORA_RANK=8`, `PER_AGENT_LORA_ALPHA=16` |
| Inference | `DAU_LLM_BACKEND=local` → `switch_adapter` + `LocalBackend.complete` |
| Train | `run_micro_train_preference_step(..., agent_id=)` → gerçek DPO adımı → `save_agent_adapter` |
| Default | `DAU_LORA_ENABLED=0` |
| Test | `test_per_agent_adapter.py` (+ `test_no_dead_adapter_root_reference`) |
| Gap | **kapandı** (`e4c026b`, `f25b0ef`) — generation-end hook bağlı, eğitim gerçek; dead `ADAPTER_ROOT_DIR` kaldırıldı |

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

### ADIM 5 — Precision-Weighted PE ✅ kod + smoke PASS (v2.4.1)

| | |
|--|--|
| Dosyalar | `semantic_similarity.py`, `constraints.py`, `graph.py`, `state.py` (`pe_history`) |
| Formül (v2.4+) | `π = clamp(1/(var(pe_history)/VAR_REF+ε), MIN, MAX)`; cold start `π=1.0`; append sırası: π sonra raw (`231c222`) |
| Sabitler | `WINDOW=10` (⚠ bu **precision** history penceresi, ölçüm penceresi değil — D-036 onu değiştirmedi), `MIN_HISTORY=2`, `VAR_REF=1/12`, `MIN_WEIGHT=0.5`, `MAX_WEIGHT=1.2` |
| Test | `test_precision_pe.py` (rolling-history suite) |
| Smoke | v1 INCONCLUSIVE (starvation, evt=10) · v3 **PASS** (evt=22, seeds 9201–9203) — §7 |
| Not | v2.3 ve öncesi = sabit kazanç `π≡1.2` (pe_vector); kilitli C′ sonuçları o aletle (§7, §10b). v3 smoke aleti doğrular; ΔPE lived>shuffle **informal only** (N=3; etki iddiası yok). |

### ADIM 6 — Protocol C′ N≥15 ✅ kod + sampling+B koşuldu

| | |
|--|--|
| Dosyalar | `dau/diagnostics/run_protocol_c_prime.py` (+ tests) |
| Eski koşum | N=15 · 50 event · greedy · reçete A → **INSTRUMENT_LIMITED_NULL** |
| Mini (v2.2) | N=1 · 10 event · sample+B → **SAMPLE_LIVED_PE_SEPARATION** |
| Final (v2.3) | N=15 · 50 event · sample+B · W=10 · K=5 → **SAMPLE_N15_UNDERPOWERED** ⚠ **W=10 ve sampling ikisi de artık geçersiz (D-036, S1)** |
| Harness | lived vs shuffle birincil; null bütünlük; diversity gate; sıfır-varyans; n_eff&lt;N → INCONCLUSIVE |

### Bağımlılık grafiği

```
ADIM 1 ──────────────────────────────┐
ADIM 2 ──────────────────────────────┤
                                      ↓
ADIM 3 ← ADIM 2 sonrası ────────────→ ADIM 6
ADIM 4 ← ADIM 1+2 sonrası ──────────→ (Protocol C′ N≥15 sampling+B ✅ koşuldu)
ADIM 5 ← ADIM 2+4 sonrası ──────────┘
```

ADIM 1–6 kodlandı. ADIM 6 sampling+B N=15 empirik sonuç:
**SAMPLE_N15_UNDERPOWERED** (alet temiz; H1 yok; N&lt;15 claim yok).

---

## 20. Yol haritası + Anti-roadmap (v2.3)

### Doğrulanan / kilitli

- Trait injection yasağı
- Deterministik Layer 0–4 omurgası
- Nesil sonu micro-QLoRA ≫ per-event online
- Protocol C paper-locked null
- C′ harness + replay (sampling’te prompt-keyed seed)
- Yaşam-PE tercih (reçete B) · niş tohumları · DPO 8GB fit
- C′ diversity gate + ön-kayıtlı W · N=15 null_arm_clean

### Yeniden değerlendirilmesi gereken

- SMOKE / WEAK / eski N=15 `INSTRUMENT_LIMITED_NULL` — tarihsel alet kayıtları
- Mini `SAMPLE_LIVED_PE_SEPARATION` — N=1; N=15’te çoğalmadı
- `SAMPLE_N15_UNDERPOWERED` — underpowered; yeni ön-kayıtlı reçete olmadan
  K/W gevşeterek “kurtarma” yasak

### Yanlışlanan / kapatılan

- Frozen-weight kapalı döngü metacognition
- MiniLM tek başına PE polarity yeterliliği
- Yaptırımsız restraint emergence
- “Replay imkânsız” (v2.1 blocker — kapatıldı)
- Tasarımcı `PREF_EXPECTED` tercih hedefi

### Sıradaki (öncelik)

1. Çok-nesilli Protocol C′ **pre-registration yazımı** (§23) — **henüz yok**
2. Pilot N=1–3 → tam N=15 iki-nesil koşum (~2sa GPU, Varyant B) → dürüst analiz
3. Pool collapse → `should_continue` terminasyon (§17)
4. Paper gövdesi (frozen-null ana; C′ alet evrimi appendix:
   INSTRUMENT_LIMITED → SAMPLE_LIVED → SAMPLE_N15_UNDERPOWERED → precision v3 PASS)
5. ~~ADIM 5 precision formül + smoke~~ → **v2.4.1 tamam** (§7)

### Anti-roadmap (yasak)

- Per-event online LoRA · EWC · TTT/PoT · prefix ana rota
- N&lt;15 ile istatistiksel iddia · post-hoc W/K bulgusu
- Eski `INSTRUMENT_LIMITED_NULL` veya `SAMPLE_N15_UNDERPOWERED` koşumunu
  “etki yok” diye sunmak
- Layer 6 · LLM-as-judge · trait injection · wall-clock zaman
- Persona/trait adapter · Groq Protocol C tekrarı

---

## 21. Ortam bayrakları (referans)

| Env | Default | Anlam |
|-----|---------|-------|
| `DAU_LLM_BACKEND` | `groq` | `groq` \| `local` |
| `DAU_LORA_ENABLED` | `0` | generation-end train/save |
| `DAU_NLI_FILTER_ENABLED` | `1` | ⚠ **iki kez eskidi.** (a) Parantez **yanlıştı** — `lora_update` içinde `is_genuine_polarity_pair` çağrılıyordu (`18fb01e`). (b) **D-032** kapıyı NLI'dan **kosinüs mesafeye** çevirdi; bant `[0.25, 0.80]`, MiniLM. `POLARITY_FILTER=nli` ile eskisine hâlâ erişilir. `NLI_CONTRADICTION_THRESHOLD=0.60` **değeri değişmedi** — ölçüm eşiğin yanlış değil **ilgisiz** olduğunu gösterdi (0.60'ta %12.9, 0.30'da %12.9) |
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

---

## 22. Versiyon geçmişi

| **2.4.2** | **2026-08-11** | Anlatı yeniden yazılmadı; **yanlışlar işaretlendi, eksik katman eklendi**. Preflight (20 değişmez) ve alet kimliği ilk kez belgede (§24) · karar kaydı sistemi D-001…D-044 (§25) · W=10, greedy platosu, NLI satırı ve sampling reçetesi ⚠ ile geçersiz işaretlendi · §18'in empirik tablosu üç kırılmayla (D-036 pencere, D-037 determinizm, D-042 konum) **karşılaştırılamaz** ilan edildi · GAP-2 kapandı · **332 test**. `.html`/`.pdf` **v2.4.1'de kaldı**. |
| **2.4.3** | **2026-08-12** | **Doğrulayıcı koşum yapıldı ve sonuç bu belgeye girdi.** B2: seed 2004–2043, N=40, ~13.1 sa · birincil **p = 0.9914**, `d_z = −0.000` ⇒ **H0 reddedilemedi** · §11 sınıfı **alet null'ı** (D-053, §5'ten üç kriter düştü). §23 **baştan yazıldı** (v2.4.2'de "tek düğüm S4" diyordu, bitti) · §25 **D-045…D-053** · §9'a konsolidasyonun deney yolundaki **yeri** (D-022/D-031) ve ilk ölçülen `deleted_count` (ort. 24.90) · §18'in ampirik tablosuna *"bunlar ΔPE'dir, birincil sonuç değildir"* uyarısı · §20 non-claims'e üç madde · §12 kod ağacına `preflight.py`/`tool_identity.py` · **344 test**. `.html`/`.pdf` **yeniden üretildi**. |

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
| **2.3** | **2026-08-07** | Diversity gate (K=5) + ön-kayıtlı W=10. C′ N=15 sampling+B final (~76 dk GPU): null **0.000** clean · lived **+0.008** · shuffle **+0.019** · n_eff=12 · p=0.637 → **`SAMPLE_N15_UNDERPOWERED`** / INCONCLUSIVE. Mini separation N≥15’e taşınmadı; “etki yok” iddiası yok. **182 test**. `.html`/`.pdf` henüz yenilenmedi. |
| **2.4** | **2026-08-07** | Precision fix (`231c222`: rolling history + `VAR_REF`); memory vault seed API (`apply_generation`); inherited somatic scale EW tüketimi; **206 test**. `.html`/`.pdf` henüz yenilenmedi. |
| **2.4.1** | **2026-08-08** | Oturum kapanışı. Zincir: `231c222` precision+vault · `a1ec2b4` crisis wiring · `c9bdbaf` adapter cleanup · `3d760e8` NLI flake · `2528e79` dual smoke_gates. Smoke: v1 (`protocol_c_prime_precision_smoke.json`, seeds 9101–9103, evt=10) **INCONCLUSIVE** / instrument starvation · v2 exploratory all-audit (aynı JSON) · **v3 (`…_smoke_v3.json`, seeds 9201–9203, evt=22) RESMİ PASS** (n_pe=396, sat=0.0025, π_n=14, null_clean, n_gated=0). Precision davranışsal doğrulandı. ΔPE lived≈0.107 informal only (N=3; güç yok; “etki doğrulandı” yasak). Sıradaki = multi-gen pre-reg (§23). **206 test**. Push yok. `.pdf` md ile senkron; `.html` henüz stale. |

---

## 23. Nerede Duruyoruz (v2.4.3 — baştan yazıldı)

⚠ **Bu bölüm v2.4.1'de *"pre-reg sıradaki oturumun İLK görevi"* diyordu,
v2.4.2'de *"tek düğüm S4"* diyordu. İkisi de bitti.** Ön-kayıt kilitlendi,
doğrulayıcı koşum yapıldı, analiz koşuldu, rapor yazıldı.

### Bitenler

| Adım | Ne oldu |
|---|---|
| **Ön-kayıt** | 🔒 kilitli, commit `befd72b4ee57`, 7/7 slot kapalı, **on yedi** ilan edilmiş sınır (L1–L17) |
| **B2 — koşum** | seed 2004–2043, N=40, iki batch, ~13.1 sa, çökme yok |
| **B3 — analiz** | birincil + dört ikincil koşuldu; **S5 ve S6 koşulamadı** (verisi/kolu yok) |
| **B4 — rapor** | `docs/B2_RESULTS.md` · on yedi sınır + dört yeni (L18–L21) |

### Sonuç

**Birincil null:** `a_s − b_s` ortalama −0.0002, W = 217.0, **p = 0.9914**,
`d_z = −0.000`.

Ve bu bir *sınırda kaçırma* değil — uç noktanın çözünürlüğü ayrıca ölçüldü:

| Mesafe | Ortalama |
|---|---|
| `‖lived − null‖` | 0.3812 |
| `‖shuffle − null‖` | 0.3814 |
| **`‖lived − shuffle‖`** | **0.3852** |

Üç kol birbirine **eşit uzaklıkta**. Yaşamın tercihleriyle eğitmek ile o
tercihlerin **%100 tersiyle** eğitmek, varisin doğum-drift'ini aynı ölçüde
ve ayırt edilemez biçimde oynatıyor. Uç nokta dejenere değil (120 kolda
76 farklı büyüklük değeri).

### §11 sınıflandırması: **ALET NULL'I**

Ön-kayıt §11 tanımları koşum görülmeden yazmıştı: *"alet null'ı = §5'ten
biri düştü **veya** kanal 2 kararları değiştirmedi."* §5'ten üç kriter
düştü (D-053) ⇒ sınıf belirlendi. Bu bir yorum değil, kural uygulaması.

⚠ Kanal 2 tarafı **tersini** işaret ediyordu: adapter faz-2 kararlarının
`lived`'de ort. 26.1/50, `shuffle`'da 26.6/50'sini değiştirdi, hiç
değiştirmeyen seed **yok**. Tanım "veya" ile bağlı olduğu için §5 tek
başına belirledi.

### Sınıflandırmayı bağımsız destekleyen üç ölçüm

| Ölçüm | Değer | Ne diyor |
|---|---|---|
| `dpo_loss` | **0.6919 / 0.6940** | **ln 2 = 0.6931** ⇒ tercih marjı ≈ 0 |
| Kırpılan adım | **%100** | Adım boyunu `lr` değil `DPO_MAX_GRAD_NORM=1.0` belirliyor |
| `dpo_grad_norm_min` | **≈ 2.96** | En küçük gradyan bile tavanın ~3 katı |

⇒ D-029'un kilitlediği `lr = 1e-6` bu koşumu **tarif etmiyor**. `I1.3b`
(D-046) tam bunun için eklenmişti ve **kapı işini yaptı** (L18).

⚠ Buna karşılık `dpo_delta_logp_chosen` = **+0.064**, 18/20 pozitif ⇒
D-049'un korktuğu **bastırma deseni gerçekleşmedi**. Öğrenmenin **yönü
doğru, büyüklüğü yok.**

### Ne iddia edilemez

1. ❌ *"Yaşanmışlık parametrik kanaldan aktarılmıyor"* — D-047 yasakladı.
2. ❌ *"Mekanizma yanlış"* — sonuç alet null'ı sınıfında.
3. ❌ *"Adapter davranışı değiştiriyor, demek ki bir şey aktarılıyor"* —
   `shuffle` de aynı ölçüde değiştiriyor. **Değişimin varlığı yönünü
   göstermez**; birincilin `lived` vs `shuffle` olmasının sebebi budur.
4. ❌ *"S4 anlamlı çıktı (p=0.035), en azından bir sinyal var"* — işaret
   H1'in tersi, medyan 0, ve §4 birincil null iken ikincilin sonucu
   değiştirmeyeceğini önceden bağladı.

### Bu null'ın değeri

Boş bir null değil: **neden göremediğimizi ölçtük.** Bir sonraki koşum
neyi düzelteceğini tahminle değil sayıyla biliyor — kırpma doygunluğu,
`dpo_loss ≈ ln 2`, ve ilk kez nicelenmiş GAP-18 (`uniq_rejected` 100/94'e
karşı `uniq_chosen` 1025/971).

### Sıradaki

**Faz C** (belge borcu) → **D-013** (branch main'e taşınmadı, tetiği
ateşledi) → **ikinci ön-kayıt**. Liste `CLAUDE.md` §1'de.

---

## 24. Preflight değişmez sistemi ve alet kimliği (v2.4.2 — yeni)

Bu katman v2.4.1'de **hiç yoktu** ve bugün projenin en sağlam parçası.

### Neden var

`preflight.py`'nin kendi docstring'i tanıyı koyuyor: bu projede **yedi alet
arızası da sayı üretti** — `lora_B=0` sahte eğitim, adapter sızıntısı, greedy
platosu, precision doygunluğu, GAP-1 (üç özdeş kol), GAP-11 (rastgele shuffle
tohumu), GAP-14 (atıl PPR). Hiçbiri çökmedi.

> Hastalık *"hataları kaçırdık"* değil — sistemin, çıktısının bir anlamı olup
> olmadığından **bağımsız olarak** çıktı üretmesi.

Değişmezler bunu tersine çeviriyor: sonuç yazılmadan önce koşum kendisi
hakkında bir listeyi kanıtlamak zorunda.

**İki başarısızlık kipi.** `ABORT` → koşum durur, **JSON yazılmaz**; sessiz
sahte sonuç imkânsız hale gelir. `FLAG` → koşum sürer, sonuç
`invariants.<id>=false` ve bir `run_quality` damgası taşır — analiz edilebilir
ama etiketli.

**D-012 kuralı:** eşiği hâlâ kalibre edilmemiş hiçbir değişmez ABORT edemez.
Uydurma bir sabit üstünden koşum öldürmek, etiketlemekten kötüdür.

### Kayıtlı 20 değişmez

| Faz | Değişmezler |
|---|---|
| 0 — koşum başlamadan | I0.1 alet kimliği tam · I0.2 LoRA seçimi açık · I0.3 `PYTHONHASHSEED` · I0.4 `agent_id`→seed türetimi · I0.5 import-anı env · **I0.6 strict determinizm** (D-037) · **I0.7 adapter sızıntısı** (D-033) |
| 1 — eğitim | **I1.1 eğitim gerçekten oldu** (D-039) |
| 2 — kollar | I2.1 kollar özdeş değil · I2.2 null eğitilmemiş |
| 3 — ölçüm sağlığı | I3.1–I3.4 (precision doygunluğu, kapılanma oranı, padding) |
| 4 — tekrar | **I4.1 replay bit-identik** (D-041) · I4.2 gen2 RNG tekdüze |
| 5 — bileşen canlılığı | I5.1 PPR aktif · I5.2 · I5.3 anı yazıldı · I5.4 somatik ölçek |

⚠ Belgede tanımlı 25'ten **beşi hâlâ kodda yok**: I1.2 (regresyon testinde),
I2.3 (yapısal olarak sağlanıyor), **I1.3 / I1.4 / I1.5 (yok)**.

### İki kapı kendini ilk gününde ödedi

- **I1.1** — eğitim kolunun `Σ|lora_B|` değerini adım öncesi/sonrası okur.
  Diğer her sinyal gradyan adımının **öncesinde** üretiliyor: çift sayıları
  polarite filtresinden gelir, adapter dosyası döngüden sonra koşulsuz
  yazılır, `dpo_loss` son ileri geçişin değeridir. `lora_B=0` hatası üçünü de
  geçmişti; **yalnız ağırlıklar biliyordu.** ⚠ `CLAUDE.md` §6 bu kontrolün
  "regresyon testinde" olduğunu söylüyordu ve **yanlıştı** — kod tabanında
  `lora_B`'ye değen tek bir test yoktu (D-038 Bulgu 2).
- **I4.1** — bir eğitim kolunu ikinci kez koşup `arm_digest` karşılaştırır.
  **İlk canlı koşumunda ayrışma bildirdi ve koşumu öldürdü — haklıydı.**
  Kovalanınca D-042'nin konum bağımlılığı bulundu.

### Alet kimliği (`tool_identity.py`)

Her koşum JSON'una kendisini üreten aletin tam kimliğini yazar: backend,
**yüklenen** model adı, quantization bayrakları, DPO hiperparametreleri, LoRA
rank/alpha, sampling, polarite bandı, kütüphane sürümleri, `argv`.

**Kural (CLAUDE.md §2.8):** *rapor aleti takip etmeli, aleti tekrar
etmemeli.* Yeni bir sabit eklerken sor: alet kimliği bunu raporluyor mu, ve
raporu **sabitten mi okuyor yoksa yeniden mi üretiyor**? Bu sınıf hata bir
günde dört kez çıktı (U2, U3a, U4, U5).

`describe_quantization` bunun örneği: `build_load_kwargs`'ı geri okur, kendi
config'ini kurmaz — kuran bir rapor er geç yükleyiciyle çelişir, ki açığa
çıkarması gereken sessiz uyumsuzluk tam olarak odur.

---

## 25. Karar kaydı sistemi (v2.4.2 — yeni)

v2.4.1'den sonra proje **kanıtlı karar kaydına** geçti: `docs/DECISIONS.md`,
**append-only**, **D-001…D-053**. Kilitli her madde bir D-numarasına işaret
eder; kanıtı olmayan hiçbir madde "kilitli karar" yazılmaz.

**D-kaydı ne zaman şart:** `constraints.py` eşik **değeri** değişiyorsa · bir
ölçüm yapıldıysa (sonucu ne olursa olsun) · bir alternatif reddedildiyse ·
ön-kayıtlı protokol değişiyorsa · kilitli bir karar sorgulanıyorsa.

### Bu belgeyi doğrudan geçersizleştiren kayıtlar

| Kayıt | Ne değişti |
|---|---|
| **D-018/D-023** | Backend varsayılanı `local`; tanınmayan değer `ValueError` |
| **D-026** | Model ölçüldü → Llama kalıyor; **greedy platosu çürüdü** |
| **D-027/28/29** | DPO penceresi 512, gradient accumulation, **lr 5e-5→1e-6** |
| **D-032** | DPO prompt'u = yaşanan prompt · polarite kapısı **kosinüs** |
| **D-036** | Ölçüm penceresi = **fazın tamamı** |
| **D-037** | **Strict determinizm**; I0.6 zorunlu kılıyor |
| **D-040** | Shuffle **%100 ters** |
| **D-042** | Adapter graft'ı **konumdan bağımsız** |
| **D-044** | ΔPE uç noktası ayrımın **%80–86'sını atıyor** |

### D-029 — aksiyoma doğrudan dokunan kayıt

`lr=5e-5` ile eğitilen ajan *"düşük PE'li şeyi tercih et"* değil *"yüksek
PE'li şeyi asla söyleme"* öğreniyordu. Kanal 2'den aktarılan iz bir tercih
değil **bastırma deseni** olurdu. Hangi izin aktarıldığı, aksiyomun iddiasının
ne olduğunu değiştirir. lr literatürden alındı, ölçümden **seçilmedi**.

### D-044 — uç nokta duyarlılığı

Faz-2'de kollar olay bazında 0.065–0.194 ayrışıyor; faz ortalaması bunun
yalnız **%14–20**'sini görüyor. İptal **simetrik** (fark işaretlerinin
%44–64'ü pozitif) ⇒ adapter ajanın **neye şaşırdığını** yeniden düzenliyor,
ortalama şaşkınlık düzeyini kaydırmıyor.

⇒ Birincil uç noktayı (doğum-drift, tek anın vektörü) **etkilemez** ve o
seçimi destekler. ΔPE ikincilleri null çıkarsa **"ölçemedik"** diye
raporlanır, "etki yok" diye değil.

### D-045…D-053 — Faz A'nın kapanışı, kilit ve doğrulayıcı koşum (v2.4.3)

| Kayıt | Ne yaptı |
|---|---|
| **D-045** | A5: gen2 uç noktası da kayıplı — korunan pay `lived−null` **%17.5**. ⇒ **S4 null'ı "ölçemedik"** (L10). Yan bulgu: gen2'nin iptali gen1'inki gibi **simetrik değil** |
| **D-046** | A3: **I1.3 daraltıldı · I1.3b eklendi** (kırpma görünürlüğü) · I1.4 spec tautolojisiydi, çevrildi · I1.5 `MIN_PAIRS` config'den. **GAP-6 kapandı** — temizlik swap'e değil **DPO adımına** kondu |
| **D-047** | **S4 slotu: SESOI ilan edilmiyor.** Bütçe-kısıtlı örneklem gerekçelendirmesi (Lakens 2022) + ilan edilen duyarlılık. `p > 0.05` ⇒ *"şu MDE'nin altında güçsüzüz"*, asla *"etki yok"* |
| **D-048** | GAP-18'in şiddeti hiç ölçülmemişti; sayaçlar eklendi, karar sayıdan sonraya bırakıldı |
| **D-049** | DR #3 mutabakatı. ⚠ **A2'nin eski tasarımı kusurlu çıktı** — "getirimi tamamen kapat" OOD şoku ölçer, parametrik kapasiteyi değil. Ayrıca bastırma teşhisi (`delta_logp_chosen`) kalıcı ölçüme çevrildi |
| **D-050** | A6: **precision ağırlığı aday olarak elendi.** Yan bulgular: **Precision-PE atıl** (L13, π tavanda takılı) · **GAP-5 doğrulandı ve nicelendi** (L14) · GAP-4'ün mekanizması yok (L15) |
| **D-051** | A7/GAP-19: saat gerçekten kırık ama birincile giden yol L1 + travma muafiyetiyle kapalı ⇒ **değiştirilmedi** (L16). ⚠ **Gizli bağımlılık:** `F_agent` tek başına düzeltilirse GAP-19 canlanır |
| **D-052** | A8: **N = 40**, seed 2004–2043, iki batch. MDE `d_z = 0.465`. **GAP-9 kapandı** — `N=40–50` ΔPE için hesaplanmıştı, bizim birinciliğimiz için değil |
| **D-053** | **B2 koştu; §5 geçerlilik kapısı düştü, sapma ilan edilerek doğrulayıcı sayıldı.** Üç kriter düştü (`run_quality`, `prompt_skipped_no_record`, `adapters/` boş değildi) ve üçü de belge içi çelişkiye işaret ediyordu |

### D-053 — sonucun sınıfını belirleyen kayıt

İki olgu bu kaydı önemli kılıyor:

**1. `prompt_skipped_no_record = 0` kriteri yeniden koşumla sağlanamaz.**
D-037 determinizmi gereği aynı seed aynı SYSTEM_1 kararını üretir; sayaç
yine 2 olur. Kriter ihlal edildiğinde **kurtarılamaz** — ancak aleti
(kilit sonrası yasak) veya seed setini (§6 yasak) değiştirerek sağlanabilirdi.
**Taslak hatası**, koşumun kusuru değil.

**2. Sapmayı kabul edilebilir kılan şey ölçüldü.** İhlallerin hiçbiri
birincil karşıtlığa **yönlü** terim eklemiyor: kırpma iki eğitim kolunda
birebir (10.8/10.8 adım, `grad_norm_min` 2.959 vs 2.984), atlanan iki karar
birer birer `lived` ve `shuffle` kollarında.

⇒ Ama §11'in tanımı gereği sonuç yine de **alet null'ı** sınıfında, çünkü
o tanım "§5'ten biri düştü" diyor ve düştü. **Sınıflandırma sonucu görmeden
yazılmış bir kuraldan geliyor, yorumdan değil.**


---

## 26. D-054…D-068: evrenin fiziği değişti (v2.4.4 — yeni)

⚠ **Bu bölüm, belgenin geri kalanının hangi kısımlarının artık geçersiz
olduğunu söyler.** v2.4.3 doğrulayıcı koşumla (B2) kapanmıştı; ondan sonra
on beş karar alındı ve son üçü **evrenin fiziğini** değiştirdi. §7'nin DAERM
denklemi, §10'un `F_agent` formülü ve §18'in empirik tablosu bu yüzden yerinde
işaretlendi.

### 26.1 Neden değiştirildi — üç ölçüm

| Kayıt | Bulgu |
|---|---|
| **D-060** | Seçilim katmanı atıl: `f_agent`=0.000 · `energy`=0.000 · `fitness_class`=`low`, **120/120 kolda**. Formül düzeltilse bile hepsi aynı sınıfa düşüyor |
| **D-061** | Enerji **yapı gereği** asla artamıyor: `decay ≥ recovery` cebirsel olarak her zaman. 2. olayda tabana vuruyor, yaşamın %96'sı sıfırda |
| **D-056 / D-064** | Birincil uç noktanın çözünürlüğü: `resource` kanalı 120/120 kolda var ama **38/40 seed'de kollar özdeş**; ayırt etme gücünü taşıyan `social` kanalı kolların **%42.5'inde hiç yok** |

**Kök neden (D-060 §2.3):** ajanlar olayların %94–100'ünde en yüksek çıkarımı
seçiyordu, çünkü **defect'in bedeli yoktu** — çıkarım enerjiye dönmüyor, havuz
çökünce kimse ölmüyordu.

### 26.2 Ne değişti (D-066, `a7b157f`)

Üç parça, biri olmadan diğerleri anlamsız:

1. **Havuz defteri gerçekleşen hasatı yazıyor.** `step_pool` havuzu `POOL_MIN`'de
   clamp'liyor ama deftere **istenen** miktarı yazıyordu ⇒ boş meradan
   *"8.0 aldım"* fiziksel olarak olmamış bir olaydı. `agent_delta_pool`
   bu yüzden kararın **sınıfını** topluyordu, ortak kaynağı değil.
2. **Kazanç içbükey:** `gain(x) = METABOLIC_GAIN_MAX · x / (HALF_SAT + x)`,
   `x` = gerçekleşen hasat. Dayanak DR #4 / J9 (Dykhuizen, Dean & Hartl 1987,
   *Metabolic flux and fitness*, Genetics 115:25–31): akı, aktivitenin içbükey
   fonksiyonudur ve **doyumda seçilim nötrleşir**. Doğrusul bir bağ defect'i
   kesin baskın bırakırdı. Sonuç aritmetik: COOPERATE→0.25, DEFECT→0.40 ⇒
   **4× havuz hasarı 1.6× enerji**.
3. **Ölüm açıldı.** `AB_ENERGY_FLOOR` yastığı `TERMINATION_ENERGY`'nin üstünde
   oturduğu için ölüm **yapısal olarak imkânsızdı**; artık yalnız doğum
   geçişini (`METABOLIC_GRACE_EVENTS`) kapsıyor.

⚠ Üç sabit de **kalibre değil** (`METABOLIC_GAIN_CALIBRATED = False`) ve alet
kimliği bunu `metabolism` bloğunda raporluyor. Değerleri **ikinci ön-kayıt**
kilitler; sonuca bakarak ayarlamak post-hoc tuning olur.

### 26.3 Ve borcu ödendi (D-067, `7c76a8c`)

D-051 gizli bağımlılığı yazmıştı: *"`F_agent` tek başına düzeltilirse GAP-19
canlanır."* D-066 `F_agent`'ı canlandırdı ⇒ GAP-19 **aynı gün** kapatıldı.
Kasa artık `counter_base` tutuyor; kasaya giren her sayaç **faz-yereldir** ve
çeviriyi yalnız kasa yapar. Yaşam bitince **yaşanan** olay sayısıyla
mühürlenir — bütçeyle değil, çünkü artık yaşam erken bitebiliyor.

### 26.4 İlk pilot ne gösterdi (D-068, N=2, keşifsel)

| | B2 (eski fizik) | Pilot |
|---|---|---|
| Ölüm | imkânsız | yaşamlar **19** ve **10** olay (50 bütçesine karşı) |
| `fitness_class` | 120/120 `low` | `low` 0.208 **vs `normal` 0.413** |
| `\|Δhavuz\|` | 393.55 ± 2.62 (%0.7) | **130.8 vs 62.2** |
| Varis ömrü | her kolda eşit | `lived` **17**, `null`/`shuffle` **20** |

Bedel zinciri canlıda ateşledi: havuz 8. olayda tabana vurunca gerçekleşen
hasat **8.0 → 6.17 → 0** düştü.

⚠ **İki yeni sorun, ikisi de bu koşumun ürettiği:**

- **Uç nokta padding'e boğuldu** — gen1'de %71 pad, alet *"arm not
  measurable"* bastı. Sabit 50 olaylık pencere, ölümün mümkün olduğu bir
  evrende çalışmıyor.
- **Enerji terimi hâlâ ölü, başka sebeple** — `E_final = 0.000` altı kolun
  altısında, çünkü tükenerek ölenin son enerjisi tanımı gereği sıfırdır.

Her ikisi de **DR brief #5**'in konusu
(`docs/research/2026-08-13_variable-lifespan-endpoints-and-censoring.md`).

⚠ **Davranış hâlâ çökmüş:** hasat neredeyse her olayda 8.0. Evren bedeli
kesiyor, ajan davranışını değiştirmiyor — DR #4 / J4'ün (GovSim, Piatti vd.
2024) rapor ettiği olgunun aynısı.

### 26.5 ⚠ Karşılaştırılabilirlik kesildi

**`dau_runs/` altındaki hiçbir koşum bugünün aletiyle karşılaştırılamaz.**
D-036 (ölçüm penceresi), D-037 (determinizm) ve D-042 (konum bağımsızlığı)
aletin nasıl ölçtüğünü değiştirmişti; D-066/D-067 **ölçülen evreni**
değiştirdi. Bu daha büyük bir kırılmadır.

### 26.6 Bu turda kapanan diğer kayıtlar

| Kayıt | Ne |
|---|---|
| **D-062** | W1 sahte-PE kontrolü: confound *tarif edildiği biçimiyle* **yok** (PE ↔ token başı olabilirlik ρ=+0.06, p=0.37). Ama D-059'un *"`lived` daha kolay öğreniliyor"* bulgusu **seed-kararlı değil**. Yan bulgu: eğitim dizilerinin **%85.5'i** 512 token tavanında kesiliyor ve sohbet şablonu başlığı kayboluyor |
| **D-063** | S5 aletlendi (hasat + `pool_ratio` + kriz bayrağı `Gen2Result`'a giriyor). **S6 kol olarak üretilmedi:** denetim birincilin `F_agent`'ı **hiçbir yoldan göremediğini** gösterdi ⇒ gölge kayıt |
| **D-064** | Uç nokta çözünürlük envanteri (21 aday). Dördü **yapı gereği kör** |
| **D-065** | DR #4 mutabakatı (§J). Bir DOI yanlış makaleye atıflı (yedinci kimlik hatası), bir "kimlik" dergi ISSN'i, *"N=20–50"* kaynaksız ⇒ kullanılmadı |

---

## 27. D-069…D-122: popülasyon makinesi ve ikinci ön-kayıt (v2.5 — yeni)

⚠ **Bu bölüm §26'nın devamıdır ve belgenin geri kalanının hangi kısımlarının
artık *deney tarihçesi* olduğunu söyler.** §26 evrenin fiziğinin değiştiğini
anlatıyordu; burada anlatılan şey **deneyin kendisinin değiştiği**: tek soy
yerine **popülasyon**, sabit `w` yerine **değişken `w`**, ve ölçülen şey
*"bir varis nasıl doğdu"* değil ***"kim varis bıraktı"***.

### 27.1 Linçpin — neden popülasyon zorunluydu

Price eşitliği `Cov(wᵢ, zᵢ)` ister ve bu ancak `w` **değişkense** tanımlıdır.
Birinci ön-kayıtta her ebeveynin **tam olarak bir** varisi vardı ⇒ `w` sabit ⇒
**seçilim ölçülemez**. Popülasyonun asıl işi ajan sayısını artırmak değil,
`w`'yi değişken yapmaktı; gerisi altyapıdır.

⚠ **Üç katman ayrı tutulur** (P4/D-094), yoksa Mills & Beatty'nin totolojisi
geri gelir: `F_agent` (**girdi**) → `w` (**varis sayısı**) → `z` (**sonuç**).
`F_agent`'ın içinde D-071'den beri gerçekleşmiş hayatta kalma var, o yüzden
doğrudan `w` yapılamaz.

### 27.2 Tasarım — kilitli kararlar

| # | Karar | Kayıt |
|---|---|---|
| **P0** | ① sıralı erişim, **tur başına rotasyon** — ajanlar karar vererek değil **farklı yaşayarak** ayrışır | D-104 |
| **P1** | kol başına **ayrı popülasyon ve ayrı mera** (kol kirlenmesi kapatıldı) | D-095 |
| **P2/P3** | turnuva **k=2**; sabit N, ölenin yerine varis ⇒ `w ∈ {0,1,2,…}` | D-094 |
| **P5** | havuz kapasitesi **N ile ölçeklenir**, kişi başı yörünge N=1 evreninin aynısı | D-081 |
| **P6** | tek faz; `delta_pe` uç noktası **kayboldu** | D-095 |
| **P7-b** | ilk koşum **kestirimdir, hipotez testi değildir** | D-096 |
| — | mera her nesilde **taze**; Kanal 2 **varise miras kalır** (3A tersine çevrildi) | D-104 · D-102 |
| — | Price **bir nesil gecikmeli**: G nesil ⇒ **G−1** satır | D-101 |
| — | **G ≥ 3 yapısal** — G=2 yalnız sıfır raporlayabilir | D-107 |

### 27.3 ⛔ Uç nokta krizi ve çözülmesi — bu dönemin en pahalı dersi

Koşumlar `Cov(w,z) = 0` verdi ve **dört ayrı okuma sırayla çürüdü**. Son
teşhis zinciri:

1. **D-115:** `z`'yi **iki yol** yazıyor — ajanın kendi `DeltaRecord`'u ve
   **ortak havuz krizi**. Kriz kolun **tamamına aynı anda** vuruyor.
2. **D-117:** kriz yolu hiçbir günlüğe yazmıyordu ⇒ D-112'nin *"eşiğe kalan
   mesafe"* profili evrenin **yarısını** görüyordu. Kapatıldı; iki kanal artık
   **ayrı** raporlanıyor (havuzlanmıyor: kriz ajanlar arası bilgi taşımaz).
3. **D-120:** ⛔ **Ve asıl teşhis burada değişti.** DR #10'a *"her ajan özdeş
   bir artış alır"* diye yazmıştık; **kod öyle demiyor** —
   `current + magnitude·exp(−current/BASE)` ⇒ artış ajanın **kendi drift'ine**
   bağlı, harita **monoton ama sıkıştırıcı** (~10.7×), ve türev **tam `z=0`'da
   sıfır**. Ölçüm seçeneği tersine çevirdi: *"yalnız bireysel kanaldan oku"*
   dejenere hücreyi **14/27 → en az 21/27** yapardı.
   ⇒ ⭐ **Sorun ortak şok değil, bireysel kanalın landmark'tan önce
   ateşlenmemesi.**
4. **D-121 (karar, Yasin):** `z` **korunur**; eklenen şey **okuma kuralı** —
   `Var(z)=0` olan hücre *"sıfır seçilim ölçtük"* değil ***"seçilim
   tanımsız"*** raporlanır (Rothenberg 1971, `10.2307/1913267`), ve krizden
   bağımsız bir nicelikte (`energy_mean_over_life`) **pozitif kontrol** koşulur.

⚠ **Genel ders (§2.2'nin dördüncü teyidi):** bir sayıya bakıp cümle kurmadan
önce **hangi mekanizmanın** onu ürettiği sorulur. Bu dönemde tek tohumdan
yazılan hiçbir cümle ayakta kalmadı.

### 27.4 Alet: bu dönemde eklenenler

| Kayıt | Ne | Neden saf raporlama |
|---|---|---|
| **D-105/106/107** | kapılar sarmalayıcıya (I0.3·I0.6·I0.7·I1.1·I4.1), nesil başına replay digest'i, `generations_informative` damgası | hesaba dokunmuyor |
| **D-108** | I1.1 muafiyeti **sebebe** bağlandı, sayıya değil — beş erken çıkışın dördü sıfır çift raporluyor | — |
| **D-111** | **checkpoint**: her nesilden sonra kısmi sonuç. ⚠ `complete:false`, analiz aracı **reddeder** | bir gecede üç kez veri kurtardı |
| **D-113** | aralık kestirimi **Wilson** (Wald nadir olayda bozuluyor) | test değil |
| **D-116** | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`; tahsis ediciye ulaştığı **ölçüldü** (`is_expandable` True ↔ ayarsız False) | tahsisi değiştirir, aritmetiği değil |
| **D-118** | **I0.4** popülasyona bağlandı — kapı aynı, **parser çağırana** bırakıldı | `shuffle` permutasyonu id'den çözülen tohumdan gelir ⇒ okunamayan id replay'i götürür |
| **D-121** | `z_variance` + `selection_estimable` + pozitif kontrol | sayı gizlenmiyor, **etiketleniyor** |

### 27.5 Süreç: mutasyon kuralı sertleşti

⛔ *"Bir test kırıldı mı"* yetmiyor; **hangi** testin kırıldığına bakılıyor —
ve bu dönemde **dört kez** aynı boşluk çıktı: düzeltme **kod tabanında** var,
**koşum yolunda** yok (D-116'nın `main()` çağrısı · D-117'nin kayıtçısı ·
D-118'in kapısı · D-121'in kontrol okuması). ⇒ **Kural:** testin,
düzeltmenin **çağrıldığı yerden** geçmesi gerekir; fonksiyonu doğrudan çağıran
test *"repoda var"*ı kanıtlar, *"koşumda var"*ı değil.

### 27.6 DR kanalı: 12 kimlik hatasından sonra ne değişti

Üç şart (DOI · **birebir alıntı** · kaynakça + **boşluk ilanı**) DR #9'da ilk
kez birlikte tuttu. ⚠ Ama şart listesi kusuru **engellemiyor, yakalanabilir
kılıyor**: DR #10'da yine bir kimlik hatası çıktı (13.), ve **aynı hata bizde
de** çıktı (§R) — ikisi de **komşu DOI numarası** deseninde.
⚠ Ve DR #10'un asıl dersi kaynakta değil **girdide**ydi: sistemi yanlış tarif
ettiğimiz için cevabın yarısı uygulanamaz çıktı. *"Brief kalitesi girdi
kalitesiyle sınırlıdır"*, dördüncü kez.

### 27.7 İkinci ön-kayıt — 🔒 kilitli

`docs/PREREGISTRATION_2.md`, commit `72df476ebd54`. Dört slot kapalı:
uç nokta (**A**) · ikincil uç nokta (**yok** — karar, eksik değil) ·
bütçe (**3 tohum · N=8 · G=3 · 30 olay ⇒ 18 Price satırı**) ·
tohumlar (**9911–9913**).

⚠ **Birinci ön-kayıt yürürlükte kalır** — ayrı bir deneyi bağlar, bu belge onu
geçersiz kılmaz.
