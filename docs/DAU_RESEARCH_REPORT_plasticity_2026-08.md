# DAU — Teşhis, Mimari İnceleme ve Parametrik Plastisite Araştırma Raporu

**Tarih:** 2026-08-06 · **Master içerik:** v1.6 · **Dosya:** `DAU_MASTER_REFERENCE_v15.md`  
**Durum:** Referans artefakt (operasyonel kilit Master’dadır)

---

## 0. Bir cümlelik özet

DAU Layer 0–5 omurgası çalışıyor; **frozen LLM’de bağlamsal üstbiliş PE’yi düşürmüyor** (paper-locked null). Yaşantı-LoRA mini pilot **WEAK** kaldı (üstelik eğitim kablosu kopuktu). Sinyal v2 + gerçek train ile **N=1 smoke’ta ayrışma** görüldü — bu evrim kanıtı değil; N büyütme tartışması için zayıf yeşil ışık. Default: `DAU_LORA_ENABLED=0`.

---

## 1. Executive Diagnosis (12 madde, v1.6 güncel)

1. **Mimari tamamlılık:** Layer 0–5 (State, Delta, Memory, PE, EmotionalWeight/Drift, Generation, Society, Meta-Observer) kodda tamam; 162+ test.
2. **Frozen metacognition null (paper-locked):** Groq Llama-3.1-8B Protocol C — Meta ON vs OFF, ΔPE ≈ 0 (N≈35 temiz çift; resmi paired t-test yok — stats caveat). Full 40 tekrar yok (TPD + eğilim net).
3. **Literatür hizası:** Harici hakem olmadan in-context self-correction başarısızlığı (Huang et al. 2023) ile nedensel uyum.
4. **VRAM GO:** RTX 4070 Laptop 8GB — 4-bit Llama-3.1-8B + MiniLM(CPU) + QLoRA (r=16, seq=128); peak ≈ 6.4 GiB < 7.5 GiB bütçe.
5. **HARDWARE_NOGO:** Per-event online LoRA reddedildi; nesil sonu / train-then-A/B tek uygulanabilir yol.
6. **WEAK_LORA_HYPOTHESIS (C′ mini):** N=3 (seeds 2001–2003), wall≈97 dk — ΔPE_lived≈+0.001, null≈−0.008, shuffle≈+0.010.
7. **Placeholder-train caveat:** C′ mini döneminde `run_micro_train_step` yaşantı JSONL’ini yok sayıp sabit micro-train metninde SFT yapıyordu. WEAK sonucu “yalnızca zayıf sinyal” değil, **kopuk kablo** da içerir. v1.6’da onarıldı.
8. **Sinyal v2 + SMOKE_SEPARATION:** N=1 seed 2001, `DAU_CPRIME_SIGNAL=v2`, wall≈1959 s (≈32.7 dk) — ΔPE_lived≈**−0.0264**, null≈**+0.0062**, shuffle≈**+0.0159**. Lived < kontroller; **significance claim yok**.
9. **Naratif evrimi:** “Parametrik iz yokken frozen bağlamsal üstbiliş null” → “mikro LoRA + yanlış/kopuk sinyalde WEAK” → “doğru kablo + PE-ranked pref ile tek-seed ayrışma adayı”.
10. **Sinyal v1 yetersizliği (tasarım):** Skalar PE/delta/trauma/drift SFT, aksiyon uzayında PE minimizasyonunu doğrudan hedeflemez.
11. **Operasyonel güvenlik:** `DAU_LORA_ENABLED=0`, `DAU_LLM_BACKEND=groq` default; omurga dokunulmaz.
12. **Bilimsel hedef:** Ana paper = frozen null (publishable negative). LoRA = appendix; v2 smoke methods note; N expand opsiyonel araştırma.

---

## 2. Architecture Critique

### 2.1 PE, Free Energy, DAERM

Layer 1.5 MiniLM PE: \(PE = 1 - \cos(\theta)\). DAERM:

\[
\mu_i(t)=\min\!\left(\frac{M_{\mathrm{drift},i}}{1+M_{\mathrm{drift},i}},\,0.75\right),\quad
\gamma(t)=\frac{E(t)}{1+M_{\mathrm{total}}}
\]

\[
L_i(t+1)=\mathrm{clamp}\big(L_i + PE_i - \gamma\cdot(L_i-\mu_i),\,\mu_i,\,1.0\big)
\]

Saturasyon/donma çözüldü. Meta-Observer aktüatörleri (lod_override, context_prune, trigger_drift_healing, trigger_retrieval) deterministik Python’dır; frozen LLM’in generative distribution’ını **kalıcı** iyileştirmez → açık döngü müdahalesi, kapalı döngü evrim değil.

### 2.2 LOD karıştırıcısı

\(T_{\mathrm{cognitive}}\) System1 (NPC, 0 token) / System2 (LLM) ayrımı. Meta ON → lod_override System2’ye zorlar → stokastik gürültü PE ölçümüne girer. Deterministik seed replay’de System2=0 → SUBSTRATE_ABSENT.

### 2.3 expected_outcome

Bellek zayıf → yapay yüksek PE; bellek çok güçlü → totolojik düşük PE. PE Std≈0.256 (endojen recovery sonrası). Her iki uç Meta etkisini maskeleyebilir.

### 2.4 Aksiyom tablosu

| Katman | Uyumlu iyileştirme | Yasak anti-pattern |
|--------|--------------------|--------------------|
| L1.5 | PE-ranked / loss-weighted sinyal | LLM-as-judge PE |
| L2 | Somatik × PE | Prompt persona |
| L3 | Yaşantı → nesil sonu QLoRA | Trait/persona LoRA |
| L4 | Kontrollü T A/B | Hakem ajan LLM |
| L5 | Python eşik kalibrasyonu | Aktüatörü serbest metinden parse |

---

## 3. Local LLM & LoRA Deep Dive

### 3.1 Inference

Lokal 4-bit Llama-3.1-8B; Groq TPD/TPM’siz. Kuantizasyon gürültüsü + T=0.2 stokastisite.

### 3.2 Plastisite

QLoRA r=16, α=32, seq_len=128, steps=2, lr=2e-4. Generation-end / train-then-A/B. Per-event online = HARDWARE_NOGO.

### 3.3 Eğitim kablosu (v1.6 kritik)

- `format_micro_train_texts(examples)` → lived `prompt\ncompletion`
- `run_micro_train_step(examples=…)` CE (+ loss_weight)
- `run_micro_train_preference_step(pairs=…)`:  
  \(L = L_{\mathrm{CE}}(\mathrm{chosen}) - \alpha\, L_{\mathrm{CE}}(\mathrm{rejected})\), \(\alpha=0.5\)

### 3.4 Sinyal v2 veri

`build_pe_ranked_pairs`: expected_outcome sabit şablon + completion vs reject adayı; MiniLM PE sıralar. Trait/persona yok. Meta: `pe_ranked_pref_v2`.

### 3.5 Kontroller

| Adapter | Anlamı |
|---------|--------|
| shared_lived | Doğru sinyal ile train |
| null_control | Train yok |
| shuffle_pe_control | v1: PE skalar karıştır; v2: chosen↔rejected |

### 3.6 Empirik sonuçlar

| Deney | N | ΔPE_lived | null | shuffle | Wall | Karar |
|-------|---|-----------|------|---------|------|-------|
| C frozen | ~35 | ≈0 (ON−OFF) | — | — | TPD | paper-locked null |
| C′ mini | 3 | +0.001 | −0.008 | +0.010 | ~97 dk | WEAK_LORA |
| C′ v2 smoke | 1 | **−0.0264** | +0.0062 | +0.0159 | ~33 dk | SMOKE_SEPARATION |

Log/JSON: `dau_runs/protocol_c_prime_v2_smoke_*.json|.log`

### 3.7 Ne bulduk / ne bulmadık

**Buldık:** Frozen null; VRAM GO; kablo bug’ı; v2 pipeline; N=1’de lived < kontroller.

**Bulmadık:** Kapalı döngü evrim garantisi; istatistiksel anlamlı LoRA etkisi; production LoRA açma gerekçesi.

---

## 4. Literature Map

| Alan | Çalışmalar | DAU karşılığı |
|------|------------|---------------|
| Intrinsic self-correction | Huang et al. 2023 | Protocol C paper-locked null |
| Quantized continual learning | Luo, Dettmers | C′ QLoRA; replay henüz uygulanmadı |
| Hakemsiz tercih | DPO/SFT equivalence 2024/25 | Sinyal v2 MiniLM PE-ranked unlikelihood |

---

## 5. Prioritized Next Experiments

### Kova A (omurgayı koru)

| ID | Hipotez | N | GO / NO-GO | Not |
|----|---------|---|------------|-----|
| H-A1 | v2 smoke ayrışması N≥5–15’te tutulur | tartışma sonrası | lived < null & shuffle, p<0.05 adayı | Otomatik değil |
| H-A2 | %10 somatik replay stabilize eder | 10 | varyans ↓ | VRAM +~0.3 GiB |
| H-A3 | Frozen null paper gövdesi | mevcut | — | **Öncelik: yazım** |

### Kova B (mühendislik, ikincil)

seq_len=512, epoch↑ — yalnızca sinyal sabitken ve H-A1 kararı sonrası.

### Kova C (yasak)

Persona LoRA · LLM-as-judge · per-event online LoRA · full FT · Groq C tekrarı · Layer 6.

---

## 6. Paper Narrative Outline

1. **Title (taslak):** Limits of In-Context Metacognition and Experience-Conditioned Parametric Adaptation in Autonomous LLM Agents
2. **Study 1 (ana):** Protocol C frozen null
3. **Study 2 / App A:** C′ mini WEAK + placeholder-train caveat
4. **App B:** C′ v2 smoke SMOKE_SEPARATION (N=1; no significance)
5. **Discussion:** Yaşantı omurgası ≠ parametrik evrim; sinyal tasarımı kritik köprü
6. **Explicit non-recommendations:** trait LoRA, LLM-as-judge, online LoRA, omurga rewrite

---

## 7. Decision Framework (v1.6 sonrası)

| Seçenek | Anlam | Tavsiye |
|---------|-------|---------|
| 1 | LoRA’yı appendix bırak, paper yaz | **Ana yol (kaynak/bilim)** |
| 2 | N expand v2 (5→15) | Yalnızca bilinçli onay; smoke yeşil ışık ama zayıf |
| 3 | Lokal LLM sadece araç | Zaten default runtime böyle |

**Ürün evrimi:** Hâlâ alınmadı. **Bilimsel fayda:** Negatif bulgu kilit + ölçülebilir LoRA hipotezi + dürüst caveat’ler.

---

## 8. Operasyonel bayraklar

```
DAU_LLM_BACKEND=groq|local     # default groq
DAU_LORA_ENABLED=0|1           # default 0
DAU_CPRIME_SIGNAL=v1|v2        # C′ harness
DAU_CPRIME_N_PAIRS / EVENTS / SEEDS
```

Plasticity gate: `dau_runs/vram_spike_results.json` status=GO.

---

*Bu rapor Master v1.6 ile senkron tutulmalıdır. Çelişki halinde Master üstündür.*
