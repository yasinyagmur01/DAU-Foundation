# Deep Research ↔ DAU kod tabanı mutabakatı

**DAU konusuna göre** indekslidir, brief'e göre değil. Karar sütunu:
`uyumlu` · `bilinçli sapma` · `fark edilmemiş kayma` · `brief yanılmış` · `açık`

Süreç: D-006. Kaynaklar: `docs/research/*.md`. Tamamlanma: 2026-08-09.

## İşlenen brief'ler

| Dosya | Durum |
|---|---|
| `2026-08-08~_per-agent-lora-serving.md` | ✅ tam tur |
| `2026-08-06_protocol-c-metacognition-eval.md` | ✅ tam tur |
| `2026-08-06_protocol-cprime-teshis.md` | ✅ tam tur |
| `2026-08-06_sentetik-kognisyon-mimari.md` | ✅ tam tur |
| `2026-08-04_metacognition-neuroscience.md` | ✅ tam tur |
| `2026-08-04_v1-kritik-sistem-audit.md` | ✅ tarandı |
| `2026-08-04_minilm-meta-ab-audit.md` | ✅ tarandı |
| `2026-08-05_daerm-trauma-magnitude.md` | ✅ formül kontrolü |
| `2026-08-04_daerm-allostatic-recovery.md` | ✅ formül kontrolü |
| `2026~_agent-curriculum-engine.md` | ertelendi — Yasin: DAU sonrası proje |
| `2026-08-10_low-data-dpo-pair-selection.md` | ✅ tam tur — **bölüm F** |

---

# A. DPO eğitim sinyali — beş ayrı ayar, tek sonuç

Arşivin en tutarlı teması bu: **beş bağımsız brief tavsiyesi aynı yöne
işaret ediyor ve beşi de kısmen veya hiç uygulanmamış.** Hepsi DPO'nun
sinyal gücünü etkiliyor.

| # | Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|---|
| A1 | 08-08~ §2 | `BATCH_SIZE=1` **+ gradient accumulation** | accumulation yok; `local_llm.py:610-627` her çift için ayrı `zero_grad()`+step → efektif batch = 1. Uygulanan şey gradient *checkpointing* (bellek tekniği) | **fark edilmemiş kayma** → GAP-8 |
| A2 | cprime-teshis H-B1 | `seq_len` 128 → **512**; "128 tokenlik sınır olayın ve bellek bağlamının kırpılmasına yol açarak eğitimin etkinliğini düşürmektedir" | `DPO_MAX_SEQUENCE_TOKENS = 256` — yarı yol | **kısmi sapma** → GAP-8 |
| A3 | cprime-teshis H-B2 | Nesil sonu eğitimde **3 epoch** | `DPO_EPOCHS = 1` | **sapma** → GAP-8 |
| A4 | cprime-teshis H-A2 | **%10 yüksek-somatik replay** (`F_agent ≥ 0.7`) SQLite'tan micro-train batch'ine karıştırılsın; +0.3 GiB VRAM; felaket unutmayı önler | Kodda **hiç yok** — `grep replay/rehearsal/anchor` yalnızca biyoloji analojisi docstring'leri buluyor | **fark edilmemiş kayma** → GAP-8 |
| A5 | sentetik-kognisyon §1.2 | **SNR eşiği:** 8B'de PE'nin parametrik güncellemeyi yönlendirebilmesi için `PE ≥ 0.40` (DEEP) gerekir; **`PE < 0.15` sinyalleri modelin ön-eğitilmiş ağırlık gürültüsünde kaybolur** | `build_pe_ranked_pairs` yalnızca `PE_RANK_MIN_GAP = 1e-6` fark arıyor. **Mutlak PE eşiği yok** → eğitim seti gürültü bandındaki çiftlerle dolabilir | **fark edilmemiş kayma** → GAP-8, muhtemelen en kritik olanı |
| A6 | 08-08~ §7 | Qwen-2.5-7B: "keskin logit ayrımı" vs Llama "platoya düşebilir" | Llama-3.1-8B | **bilinçli sapma**, D-005 ile yeniden açıldı |
| A7 | sentetik-kognisyon Öneri 1 | Unlikelihood kaybı: `L = CE_chosen − 0.5·CE_rejected` | Standart DPO kaybı (`−logsigmoid(β·logits)`) | **bilinçli sapma** (DPO daha ilkeli), gerekçesi kayıtlı değildi |
| A8 | sentetik-kognisyon §1.3 | EWC mikro-ölçekte verimsiz; yerine **KL-divergence veya L2 penalty** | Hiçbiri yok | **açık** (düşük öncelik) |
| A9 | sentetik-kognisyon §1.3 | %10-20 **anchor rehearsal** (genel veri) temel yetenekleri korur | Yok | **açık** — A4 ile aynı aileden |

**Sentez:** A1+A2+A3+A4+A5 birlikte, "eğitim çalıştı ama iz bırakmadı"
sonucunun teknik açıklaması olabilir. Beşi de tek tek küçük; birlikte
sinyal gücünü katlayarak düşürüyorlar. Ve `SAMPLE_N15_UNDERPOWERED`
tam olarak bu tabloyla uyumlu.

# B. İstatistiksel güç — N=15 baştan yetersizdi

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| protocol-c-eval "Statistical Power" | `σ_PE = 0.256`. Eşleştirilmiş tasarımda `d_z ≈ 1.5·d`. Gerekli çift sayısı: **d=0.5 → 16 · d=0.4 → 24 · d=0.3 → 41 · d=0.2 → 90**. Protocol C için **N=40-50 çift** öneriliyor | Protocol C′ N=15 koşuldu | **fark edilmemiş kayma** → GAP-9 |
| sentetik-kognisyon §1.6 | "`d = 0.5` (orta etki) için minimum **N = 15 ila 20**" | N=15 kullanıldı | uyumlu — **ama yalnızca d≥0.5 için** |
| 08-08~ §5 | `N ≥ 15`, `K = 5`, `n_eff ≥ 12` | aynı | uyumlu |

**Bu bulgu tabloyu değiştiriyor.** N=15 rakamı iki brief'ten geliyor ama
**yalnızca orta-büyük etki (d ≥ 0.5) varsayımı altında** geçerli. DAU'nun
gözlediği etkiler çok daha küçük (`lived +0.008` vs `shuffle +0.019`,
σ≈0.256 ⇒ d ≈ 0.04). Bu büyüklükte bir etki için gereken çift sayısı
yüzlerce.

Yani **`SAMPLE_N15_UNDERPOWERED` bir sürpriz değildi — güç analizi onu
önceden söylüyordu.** N=15 hiçbir zaman "etki var mı" sorusunu
cevaplayabilecek bir tasarım değildi; yalnızca büyük bir etkiyi
yakalayabilirdi.

**Sonuç:** çok-nesilli pre-reg'de N, varsayılan olarak 15 alınamaz.
Ya (a) beklenen etki büyüklüğü açıkça gerekçelendirilip N ona göre
hesaplanmalı, ya da (b) D-002'nin daha yüksek güçlü uç noktası
(doğum-drift, tamsayı sayımlar) kullanılmalı — ki bu D-002'yi bağımsız
olarak destekliyor.

# C. Değerlendirme tasarımı — D-002'ye dokunanlar

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| protocol-c-eval "Sensitivity Hierarchy" | Duyarlılık sırası: **Rank 1 `PE_{t+1}`** · Rank 2 travma sıklığı · Rank 3 `W_transfer` · Rank 4 `γ(t)` | D-002 PE'yi **ikincile** düşürdü | **gerilim** — aynı deney değil (Protocol C nesil-içi, doğum-drift nesiller-arası) ama kayda geçmeli |
| sentetik-kognisyon §1.6 | **OOD Behavioral Probing:** yaşantıdan sonra ChromaDB retrieval **tamamen kapatılır**, yalnızca ağırlıklara (LoRA) yansıyan değişim ölçülür | DAU'da yok | **açık** — Kanal 2'yi Kanal 1'den izole etmenin temiz yolu; D-002'nin doğrudan tamamlayıcısı |
| sentetik-kognisyon §1.4 | Trait stabilizasyonu **≥30-50 olay VE ≥3 nesil konsolidasyonu** gerektirir | Multigen **2 nesil** | **açık** → pre-reg tasarımını etkiler |
| protocol-c-eval "Primary Hypothesis Tests" | PE için **tek-kuyruklu paired t-test / Wilcoxon**; travma için **McNemar** (eşleştirilmiş ikili) | CLAUDE.md paired t/Wilcoxon'u destekleyici sayıyor; McNemar hiç geçmiyor | uyumlu + **eksik test** |
| — | **Kruskal-Wallis / Fisher-Freeman-Halton** | `CLAUDE.md`'de kilitli maddeydi | **PROVENANS BULUNAMADI** — 9 brief'in hiçbirinde yok. Muhtemelen 3-grup tasarımı için **türetildi**, kaynaklanmadı |
| sentetik-kognisyon §1.6 | Ek metrikler: çapraz-bağlamsal transfer, eylem dağılımı entropisi `H(A)`, NLI kararsal tutarlılık indeksi | Yok | **açık** (düşük öncelik) |

# D. Ölçüm geçerliliği — süresi dolmuş ertelemeler

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| v1-audit S1 / "Erteletilebilir" | `W_SEM = 0.0` → ChromaDB vektörü skorlamaya girmiyor, sadece depo. "**Baseline kilitlenince** `W_SEM = 0.3–0.4` yapılmalı" | Hâlâ `W_SEM = 0`. Baseline (Protocol C) **artık kilitli** — erteleme koşulu gerçekleşti, kimse dönmedi | **fark edilmemiş kayma** → GAP-10 |
| minilm-audit SELECTIVE_FIX #3 | `semantic_similarity.py`'ye MiniLM cosine öncesi **olumsuzluk eki kural denetimi** (not/never/no/refuse) eklensin | `grep negation/refuse` → **hiç yok**. NLI yalnızca tercih çiftlerinde, PE sensöründe değil | **fark edilmemiş kayma** → GAP-10 |
| v1-audit S1 / minilm-audit S1 | **El yazısı `expected_outcome`**: ajanın beklentisi kendi kognisyonundan değil, tasarımcı şablonundan geliyor → "PE, tasarımcının şablonu ile ajanın eylemi arasındaki mesafeyi ölçüyor" | Devam ediyor | **açık** — GAP-5'in ta kendisi, iki bağımsız denetim aynı şeyi işaret etmiş ⇒ GAP-5'e provenans |
| daerm-trauma §"Spillover" | Skaler `S=0.20` yerine **domain-özgü asimetrik spillover matrisi** (`S_res→unc=0.35`, `S_soc→res=0.10`, …) benimsensin | `CROSS_AXIS_SPILLOVER: float = 0.20` — skaler | **açık** — bilinçli mi bilinmiyor |
| v1-audit "İmkansızlıklar" | `F_agent` doğal seçilim değil, **tasarımcı puanlama fonksiyonu**; doğal seçilim iddiası savunulamaz, dokümante edilmeli | Master reference §18 kabul ediyor | **uyumlu** — D-003'ün gerekçesini bağımsız olarak destekliyor |
| v1-audit / minilm-audit | AB_ENERGY_FLOOR yapay yaşam uzatması ölçümü düzleştiriyor | Devam ediyor, dokümante | **uyumlu** (kabul edilmiş sınır) |

# E. Uyumlu — birebir uygulanmış

| Kaynak | İddia | DAU | Karar |
|---|---|---|---|
| daerm-trauma §"Formal Spec" | `MAGNITUDE_PEAK_WEIGHT = 0.70`, `M = 0.70·max + 0.30·mean = 0.82·PE`; PE≥0.854 → TRAUMA | `constraints.py:33` birebir | **uyumlu** |
| daerm-recovery "Unified Spec" | `μ = min(M_drift/(1+M_drift), 0.75)`, `γ = E/(1+M_total)`, `L(t+1) = clamp(L + PE − γ(L−μ), μ, 1)` | birebir | **uyumlu** |
| daerm-trauma "Decoupling" | Magnitude, DAERM recovery çıkarılmadan **ham PE vektörü** üzerinden hesaplansın | Uygulandı (v1.2) | **uyumlu** |
| sentetik Öneri 2 | Punica deseni, ajan başına `r=8, α=16` | `PER_AGENT_LORA_RANK=8`, `ALPHA=16` | **uyumlu** |
| sentetik Öneri 3 | HippoRAG 2 tarzı PPR bellek motoru | ADIM 4 | **uyumlu** |
| sentetik Öneri 4 | Havuz kritik eşiğin altına inince somatik travma + `F_agent` cezası | ADIM 1 crisis | **uyumlu** |
| 08-08~ §1 | Adapter izolasyonu disk düzeyinde, bellekte tek slot | `f25b0ef` | **uyumlu** |
| protocol-c-eval | Protocol C = seed-locked counterfactual paired, T=0.2, eşik 0.65 | Birebir uygulanmış | **uyumlu** |
| protocol-c-eval "Null Framing" | Null sonucun akademik çerçevesi: Intervention Paradox · Performative Metacognition · Verification Theatre | Master reference'ın "paper-locked null" çerçevesi bununla örtüşüyor | **uyumlu** |
| Tüm brief'ler | Trait injection yasağı | Aksiyom | **uyumlu**, dört bağımsız kaynakla doğrulanmış |

Kısmen: 08-08~ §1 hot-swap'te **CUDA sync + gradyan önbellek temizliği**
istiyor; `local_llm.py`'de `empty_cache`/`synchronize` yok → GAP-6.

# F. Brief yanılmış

| Kaynak | İddia | Ne oldu |
|---|---|---|
| metacognition-neuroscience §"Feasibility" | *"Genuine metacognition is **fully achievable** with frozen-weight LLMs when implemented as a system-level property… Metacognition is a property of the structural control loop, not the individual model weights."* | **DAU bunu deneyle yanlışladı.** Protocol C: ΔPE ≈ 0, paper-locked null. Brief fazla iyimserdi; out-of-band meta-observer mimarisini doğru tarif etti ama etkinliğini yanlış öngördü. |
| metacognition-neuroscience §7 | Blueprint hâlâ `Δ = 1 − JaccardOverlap` varsayıyor | 08-04 tarihli, MiniLM geçişinden önce — tarihsel, sorun değil |
| 08-08~ (kök triyaj) | Scheduler-state drift / stale KV-cache — concurrent multi-tenant riski | DAU sıralı çalışıyor, geçerli değil (Yasin doğru triyaj etmişti) |

**F1 kayda değer:** bu, projenin ana bilimsel katkısının bir Deep Research
öngörüsünü çürütmesi demek. Paper'da bu açıkça söylenebilir — literatürün
"sistem seviyesinde çözülür" beklentisi, frozen ağırlıklarda ampirik
olarak karşılanmadı.

---

## Aksiyonlar

| # | Bulgu | Nereye |
|---|---|---|
| 1 | A1-A5, A9: DPO sinyal gücü beş ayarı | CLAUDE.md **GAP-8** (genişletildi) |
| 2 | B: N=15 güç analizine göre yetersiz | CLAUDE.md **GAP-9** (yeni) |
| 3 | D: W_SEM=0 + negation wrapper, süresi dolmuş ertelemeler | CLAUDE.md **GAP-10** (yeni) |
| 4 | C: OOD probing, ≥3 nesil, McNemar | **D-010** — pre-reg tasarım girdisi |
| 5 | A6 Qwen | **D-005** girdisi |
| 6 | 08-08~ §1 CUDA sync | GAP-6 (önceliği yükseltildi) |
| 7 | KW/FFH provenansı | **BULUNAMADI** — 9 brief'te yok; türetilmiş kabul edilmeli |
| 8 | GAP-5'e provenans (iki denetim bağımsız işaret etmiş) | CLAUDE.md GAP-5 notu |
| 9 | F1: brief yanıldı, DAU çürüttü | Paper anlatısına girdi |


---

# F. Düşük veri rejiminde DPO — `2026-08-10_low-data-dpo-pair-selection.md`

**İşlendi:** 2026-08-10, U5'ten hemen önce. Brief'i isteyen soru: filtre 746
aday çiftten 745'ini eliyor, tek haneli çiftle DPO ne yapar?

| # | Brief iddiası | DAU'da durum / **yerel ölçüm** | Karar |
|---|---|---|---|
| **F1** | `lr = 5e-5` az veride **unlikelihood push** ve **parametre büzülmesi** yaratır; DPO başarıları **5e-7 – 1e-6** kullanıyor (Zephyr-Beta, Tülu 2) | `DPO_LEARNING_RATE = 5e-5` — brief'in bandının **50–100 katı**. Gerekçesi hiçbir D-kaydında yok. **Ölçülmedi** | **açık — en ağır madde** |
| **F2** | NLI cross-encoder bu görev için **yapısal olarak yanlış araç**; eylem cümleleri "Neutral"a düşer | ✅ **Yerel ölçümle doğrulandı ve güçlendirildi** (aşağıda) | **uyumlu** |
| **F3** | NLI skorları **0.01–0.20** bandında döner | ❌ **Yanlış.** 85 gerçek aday çiftte medyan **0.0024** — bandın bir mertebe altı. Bandın içinde kalan pay yalnızca **%12.9** | **brief yanılmış** (yönü doğru, sayısı yanlış) |
| **F4** | Eşik (0.60) yanlış kalibre **değil**, araç yanlış | ✅ **Ölçümle kanıtlandı:** 0.60 → 0.30 eşiği düşürmek geçme oranını **hiç değiştirmiyor** (%12.9 → %12.9). 0.05'e inince ancak %20. Dağılım **çift tepeli**: kütle sıfıra yığılmış, azınlık 0.99'a | **uyumlu — brief'ten daha güçlü** |
| **F5** | Alternatif: gömme kosinüs mesafesi, `1-cos ≥ 0.35` | ✅ Aynı 85 çiftte kosinüs medyan **0.3575**, 0.35 eşiğinde geçme oranı **%56.5** (NLI'nin %12.9'una karşı, **4.4×**). MiniLM zaten kod tabanında (`semantic_similarity.py`) | **uyumlu**, U5 adayı |
| **F6** | "Olay başına en güçlü marj" = literatürdeki **Marj Maksimizasyonu**; Deng 2025 en yüksek marjlı %10 ile +3–8 puan | `build_pe_ranked_pairs` `best_by_event` ile tam bunu yapıyor | **uyumlu** — DAU'nun tasarımı literatürle örtüşüyor |
| **F7** | Tuzak 1: uç değer hassasiyeti — sadece maksimum marj gürültülü outlier'ları içeri alır | A5/U5'in `SNR_FLOOR`'u tam bunu hedefliyor ama **mutlak** eşik, marj değil | **kısmen uyumlu** — U5 tasarımına girdi |
| **F8** | Tuzak 2: **hizalama evresi ihlali** — erken ajanlarda olay başına tek çifte indirgemek keşif çeşitliliğini öldürür | DAU tüm nesillerde aynı kuralı uyguluyor; evre ayrımı **yok** | **fark edilmemiş kayma** — yeni |
| **F9** | KTO çift kurmayı gereksiz kılar, O(n²) darboğazını **tamamen** aşar | DAU çiftli DPO. KTO tekil PE etiketiyle çalışır — DAU'nun PE'si zaten sürekli bir skaler | **açık** — ciddi alternatif |
| **F10** | IPO az veride DPO'dan kararlı (sınırlı kayıp) | DAU vanilla DPO | **açık** |
| **F11** | SimPO N≤5'te hızla aşırı uyum — **çelişen bulgular** olduğu belirtiliyor | — | brief kendi çelişkisini bildiriyor, not edildi |
| **F12** | Greedy < T ≤ 0.1 tercih edilmeli; sampling **style bias / reward hacking** riski | Karar **açık** (D-026). Brief greedy'yi destekliyor | **açık karara girdi** |
| **F13** | Replay **%10–15**; %5 altı yetersiz, %25 üstü adaptasyonu geciktirir | A4 kararı açık (D-027) — brief %10'u destekliyor | **açık karara girdi** |
| **F14** | M-DPO — `arXiv:2506.08965` (2024) | ⚠ **Kimlik/yıl çelişkili**: `2506` öneki 2025 Haziran'ı gösterir, 2024 makalesi olamaz | **kaynak doğrulanamadı** — kullanılmamalı |

## F2–F5'in yerel ölçümü (`dau_runs/nli_score_distribution.json`)

2 seed × 10 olay, greedy, gerçek Llama-3.1-8B-Instruct çıktıları.
85 aday çift, 15 benzersiz completion.

| | NLI çelişki | Kosinüs mesafe |
|---|---|---|
| min | 0.0001 | 0.0013 |
| **medyan** | **0.0024** | **0.3575** |
| max | 0.9976 | 0.7484 |

**Eşiğe göre geçme oranı — asıl bulgu burada:**

| eşik | 0.05 | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | **0.60** |
|---|---|---|---|---|---|---|---|
| NLI | %20.0 | %15.3 | %14.1 | %12.9 | %12.9 | %12.9 | **%12.9** |

**Eşiği 0.60'tan 0.30'a indirmek tek bir çift bile kazandırmıyor.** Dağılım
çift tepeli: kütlenin çoğu sıfıra yığılmış, küçük bir azınlık 0.99'a. Yani
bu bir kalibrasyon sorunu **değil** — brief bunu iddia etmişti, ölçüm
bunu brief'ten daha kesin gösteriyor.

| eşik | 0.15 | 0.25 | **0.35** | 0.50 |
|---|---|---|---|---|
| Kosinüs | %95.3 | %84.7 | **%56.5** | %18.8 |

⚠ **Bu oranlar dedup öncesi.** `best_by_event` olay başına tek çift
bıraktığı için eğitime giren sayı bunların çok altında kalır — 20 olayda
tavan 20 çift. Kosinüs geçişi %56.5 olsa da eğitilen çift sayısı ~20'yi
aşamaz.
