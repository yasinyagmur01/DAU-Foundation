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
| `2026-08-11_S4-minimum-effect-of-interest.md` | ✅ tam tur — **bölüm G** |
| `2026-08-11_GAP18-shared-negatives-in-preference-learning.md` | ✅ tam tur — **bölüm H** |

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

## §F'nin kapanışı — D-032 (2026-08-10)

| # | Nereye gitti |
|---|---|
| **F2/F3/F4** | Kabul edildi ama **eşik olarak değil**: NLI 0.60 değeri korunarak alet değiştirildi. Ölçüm brief'in "yanlış araç" iddiasını doğruladı, "0.01–0.20 bandı" sayısını çürüttü |
| **F5** | **Uygulandı** — kosinüs bandı `[0.25, 0.80]`, `polarity_filter.py`. Bant brief'ten alındı, kendi seed'imizden seçilmedi |
| **F6/F7** | `best_by_event` marj maksimizasyonu olarak kalıyor. F7'nin uç-değer kaygısı `SNR_MARGIN_FLOOR`'da duruyor ama **etkisiz** ölçüldü (argmax zaten eliyor) |
| **F8** | GAP-18 küçüldü: prompt olay-özgü olunca ortak negatif dejenerelik olmaktan çıkıyor. Evre ayrımı **hâlâ yok** |
| **F9/F10 (KTO/IPO)** | **Ertelendi, çürütülmedi.** Prompt sorunu KTO'da da aynen dururdu, o yüzden önce prompt |
| **F12 (greedy)** | Karar hâlâ açık — ön-kayıtla verilecek |

⚠ **Brief'in görmediği asıl sorunu yerel ölçüm buldu:** DPO prompt'unun
çıkarım prompt'uyla hiç ilgisi yoktu (51 token vs 246–306, `system=""`).
Brief bunu hiçbir maddesinde işaret etmiyor. **Ders yine aynı: brief iddia,
kanıt kodda.**


---

# G. DR brief #1 — S4: en küçük anlamlı etki (2026-08-11)

**Cevap geldi. Yöntem tavsiyesi alınabilir, sayısal savunması alınamaz.**

Kısa hüküm: DR'nin **usul** önerisi (bütçe-kısıtlı N + duyarlılık analizi)
sağlam, kaynaklı ve S4'ü **çözmüyor — çözülmesi gereken bir soru olmaktan
çıkarıyor**. Ama önerdiği N'i savunan iki dayanak da yerel doğrulamada
düştü, ve DR'nin göremediği bir kusur bu kararı şimdilik **erteletiyor**.

## G.1 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| G1 | **Bütçe-kısıtlı örneklem gerekçelendirmesi meşrudur** (Lakens 2022, *Sample Size Justification*, Collabra: Psychology 8(1):33267) — altı meşru yöntemden biri | Kaynak gerçek ve doğru anılmış. Yöntem bizim durumumuza **birebir uyuyor**: birincil uç nokta için literatürde referans etki yok, bu yüzden SESOI uydurmak temelsiz kalırdı | **uyumlu — benimsenir** |
| G2 | **Duyarlılık güç analizi ilan edilmeli**, MDE raporlanmalı | Bizde hiç yoktu. GAP-9 tam olarak bunun yokluğuydu | **uyumlu — benimsenir** |
| G3 | `N=32` için MDE: iki yönlü `d_z=0.512`, tek yönlü `0.450` | Yerel exact noncentral-t: **0.5113 / 0.4495**. Üç hane doğru | **uyumlu** |
| G4 | Bunun türetimi `N ≈ (1.96+0.842)²/d_z²` | O formül `d_z = 0.4953` verir, 0.512'yi **değil**. Sayı doğru, yanında gösterilen formül onu üretmiyor (normal yaklaşım vs exact nct) | **brief tutarsız** — şablon **birebir yapıştırılamaz** |
| G5 | **`r ≥ 0.85`**, çünkü koşum-arası gürültü sıfır (sha256 özdeş) ⇒ `d_z = 0.512` aslında `d ≈ 0.28`, yani tasarım duyarlı | ❌ **Çıkarım geçersiz, iki kere.** (a) Determinizm *aynı kolu tekrar koşmanın* gürültüsünü sıfırlar; **farklı kolların seed'ler arası korelasyonu** hakkında hiçbir şey söylemez. (b) Daha temel: bizim birinciliğimiz iki kolun eşleştirilmiş ölçümü **değil**, iki mesafenin farkı (`a_s − b_s`, §3) — DR'nin `d_z = d/√(2(1−r))` dönüşümü bu forma **uygulanamaz**. Yakılmış üç seed'de gözlenen `corr(a_s, b_s) = −0.80` (N=3, kendisi anlamsız; ama işaret bile ters) | **brief yanılmış** |
| G6 | İçsel temsil / drift çalışmalarında literatür **`d_z ≈ 0.85–1.70`** | ❌ **Kaynaksız.** Brief "her iddia yazar + yıl + yer" şart koşmuştu; burada yalnız "ProtoAlign", "Anchor Bias" adları geçiyor, atıf yok. §9 sicilinde aynı kip iki kez çürüdü (Qwen "şiddetle önerilir"; NLI 0.01–0.20 bandı) | **kullanılamaz** — N gerekçesi buna dayandırılmaz |
| G7 | Small telescopes: Simonsohn (2015), *Psychological Science* 26(5):559–569 | Kaynak gerçek. Ama DR "Simons ve ark. (2014) tarafından yaygınlaştırıldı" diyor — **2014, 2015'i yaygınlaştıramaz**; kronoloji ters | **kısmen yanlış** — yöntem zaten bize uygulanamıyor (doğrudan replikasyon yok), etkisiz |
| G8 | Meehl (1990) crud factor; alanın dağılımından eşik türetmek **döngüsel** olabilir | Kaynak gerçek (*Psychological Reports* 66:195–244), argüman geçerli ve G6'yı **kendi içinden** çürütüyor: DR yayın yanlılığının medyanı %50–100 şişirdiğini söyleyip aynı raporda kaynaksız `d_z≈1.0+` değerlerini dayanak yapıyor | **uyumlu — ve G6'ya karşı kullanılır** |
| G9 | Dodge ve ark. (2019), *Show Your Work*, EMNLP; Responsible NLP Checklist hesaplama bütçesi beyanını zorunlu kılıyor | Kaynak gerçek ve iddia doğru | **uyumlu** |
| G10 | TOST eşdeğerlik çerçevesi | Doğru anlatılmış, ama `H01`/`H02` bloğu **iki kez, ikisi de `H01` etiketiyle** basılmış. Bize uygulanabilir değil: TOST bir SESOI ister, DR'nin kendi tavsiyesi SESOI koymamak | **uyumlu ama uygulanamaz** |
| G11 | "ΔPE'nin ikincilde iptal yaratması, birincilin **saf parametrik iz** olduğunu **doğrulamaktadır**" (Eleştiri 2 savunması) | ❌ **Non sequitur.** D-044/D-045'in gerçek argümanı: iptal birinciliği **tehdit etmiyor**, çünkü doğum-drift olaylar üstünde ortalanmıyor. "Tehdit etmiyor" ile "doğruluyor" aynı şey değil ve ikincisinin dayanağı yok. Rapora bu haliyle girerse hakem tam buradan girer | **brief yanılmış** — savunma metni kullanılmaz |
| G12 | Şablon: "her bir seed … **3 koşum** içeren bit-düzeyinde deterministik bir süreç" | Yanlış tarif: seed başına **3 kol** var (lived/null/shuffle), 3 koşum değil; I4.1 replay'i **koşum başına bir kez**, seed başına değil | **brief yanılmış** (bizim tarifimizden türemiş olabilir) — şablon düzeltilmeden kullanılmaz |
| G13 | Tavsiye: `N=32`, ~10.8 GPU saat | Bütçe aritmetiği doğru (32 × 20 dk = 10.7 sa). ⚠ Ama GAP-9'un dayandığı `protocol-c-metacognition-eval` briefi Protocol C için **N=40–50** öneriyordu; iki sayı **uzlaştırılmadı** | **açık** — G.3'e bak |

## G.2 DR'nin göremediği: birincil uç noktanın kendisinde yapısal kusur

DR'ye deneyin dürüst tarifi verildi ama `birth_drift_magnitudes`'in **çalışma
zamanındaki şekli** verilmedi — verilemezdi, biz de bakmamıştık. Bakıldı
(`control_d042`, seed 2001–2003, **D-038 ile zaten yakılmış** ⇒ doğrulayıcı
koşumun dışında):

**1. "Üç alanlı vektör" pratikte iki alanlı, ve hangi ikisi olduğu kola göre
değişiyor.**

| seed | lived | null | shuffle |
|---|---|---|---|
| 2001 | resource, social | resource, social | resource, social |
| **2002** | resource, **social** | resource, **uncertainty** | resource, **uncertainty** |
| 2003 | resource, social | resource, social | resource, social |

`uncertainty` yalnız 2002'de, orada da yalnız iki kolda görünüyor.

**2. `resource` bileşeni atıl.** Dokuz kolun tamamı `3.6404 … 3.7414`
(yayılım 0.101, düzeyin **%2.7'si**). Seed 2001'de üç kolda **birebir aynı**.

**3. Bu ikisi birleşince birincil, ikincil S1'i taşıyor.** §3 bayraklanmamış
alanı 0 sayıyor. Seed 2002'de `lived` `social`, `null` `uncertainty`
bayraklıyor ⇒ L2 mesafesi bir **kategorik uyuşmazlığı** büyüklük farkı gibi
okuyor: fark vektörü `[0.052, 0.809, −0.786]` — iki büyük terim tamamen
bayrak uyuşmazlığından. Üç seed'in toplam sinyalinin **%86'sı** bu tek
seed'den ve bu tek mekanizmadan geliyor.

⇒ **Birincil (büyüklük kanalı) ile S1 (kategorik kanal) bağımsız değil.**
Ön-kayıt ikisini ayrı uç noktalar diye ilan ediyor.

⚠ **Şeffaflık borcu:** bu hesap yapılırken `a_s − b_s`'in **işareti de
görüldü** (üç seed'de de aynı yönde). Seed'ler yakılmış olduğu için
doğrulayıcı analizi kirletmiyor, ama **uç nokta tanımı bundan sonra
değiştirilirse** bu bilgi altında değiştirilmiş olur. Ön-kayıta
*"tasarım 2001–2003 pilot seed'lerinde denetlendi, o seed'ler doğrulayıcı
koşumdan hariç"* diye **yazılmalı**.

## G.3 Ne alınıyor, ne alınmıyor

**Alınan (S4 slotunu kapatan):** SESOI **ilan edilmiyor**. Yerine bütçe-kısıtlı
N + duyarlılık analizi (G1, G2, G9). Rapor dili DR'nin ayrımını kullanıyor:
`p > 0.05` ⇒ *"şu MDE'nin altında güçsüzüz, veri o bantta bilgisiz"*, asla
*"etki yok"*. Bu L9/L10'un ΔPE için zaten yazdığı şeyin birincile taşınması.

**Alınmayan:** `r ≥ 0.85` ve ondan türeyen "aslında `d ≈ 0.28`" savunması
(G5) · literatür `d_z` bandı (G6) · Eleştiri 2 savunması (G11) · şablonun
birebir metni (G4, G12).

**Bekleyen:** N'in **değeri**. G13 uzlaşmamış, ve G.2 daha ağır basıyor —
N, uç noktanın tanımı düzelmeden seçilirse kusurlu bir ölçüme hassasiyet
satın alınmış olur. **S2 açık kalıyor; S4 kapanıyor.**


---

# H. DR brief #2 — GAP-18: ortak negatifler (2026-08-11)

**Cevap geldi. En önemli bulgu raporda değil: brief'in kendisi yanlış bir
sayı vermiş, ve rapor bütün teşhisini o sayının üstüne kurmuş.**

## H.1 ⚠ Önce bizim hatamız

Brief şöyle diyordu:

> Ölçülen: **47 çiftlik** bir eğitim setinde **47 farklı prompt**, ama yalnız
> **2 benzersiz `rejected`** metni.

**Bu iki sayı aynı koşumdan gelmiyor.**

| Sayı | Gerçek kaynağı |
|---|---|
| **47 çift / 47 prompt** | `control_d042_n3_local`, seed 2001, **50 olay** |
| **2 benzersiz `rejected`** | `exploratory_pair_design_replay`, seed 2001, **10 olay** — o yaşamda **toplam 7 benzersiz completion** vardı ve tasarım **9 çift** üretmişti |

**47 çiftte benzersiz negatif sayısı hiç ölçülmedi.** Üstelik ölçüm noktası
o zamandan beri **değişti**: aynı koşumlar `n_unique` **29 · 22 · 27**
raporluyor (D-034: *"7-benzersiz tavanı açıldı"*). 29 completion'dan çekilen
negatif havuzu, 7'den çekilenle aynı havuz değildir.

⇒ DR'nin *"47 prompt yalnız 2 ortak negatif paylaşıyor ⇒ gradyan uzayındaki
serbestlik derecesi 2'ye iner ⇒ parameter shrinkage / catastrophic collapse"*
zincirinin **ilk halkası bizden geldi ve doğrulanmamış.** Rapor yanılmadı;
yanlış beslendi (§2.8'in klasik kipi: rapor aleti takip etmedi, iki aletin
çıktısını birleştirdi).

**Yapılan:** tahmin yerine sayaç. `PAIR_DIVERSITY_STATS` → `uniq_rejected`,
`uniq_chosen`, `texts_in_both_roles`, `max_rejected_reuse`, çiftlerin
kurulduğu yerde okunuyor ve `pair_filter` raporuna giriyor (`daa5f4b`).
**B2 bu soruyu cevaplayacak.**

## H.2 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| H1 | 47 prompt / 2 ortak negatif **ağır yapısal patoloji** | Premis doğrulanmamış — H.1. Yapısal argüman (**`best_by_event` global maks-PE completion'ı çoğu çiftin reddedilen tarafı yapar**) ayakta, ama **şiddeti** ölçülmedi | **premis açık** — B2'de ölçülecek |
| H2 | **Kolay negatifler** `σ(−z)` uyarınca erken adımlardan sonra ≈0 gradyan üretir | Mekanizma doğru ve bizde **artık görünür**: D-046'nın **I1.3**'ü `dpo_grad_norm_min`'i kaydediyor, tam sıfır gradyanlı adım **ABORT**; **I1.3b** kırpma oranını raporluyor | **uyumlu — zaten aletlendi** |
| H3 | **Shuffle kolu**, gerçek tercih öğrenildi mi diye bakmanın temel testi: shuffle **belirgin biçimde daha yüksek loss** üretmezse model içerik değil düzenlileştirme öğrenmiştir | ⭐ **En değerli madde.** Bizde shuffle zaten var (D-040, %100 ters) ama **loss karşılaştırması hiç yapılmadı**. D-046 `dpo_loss`'u kol bazında JSON'a yeni koydu ⇒ **B2'de bedava gelecek** | **uyumlu — ön-kayıta alınabilir** |
| H4 | 40 çiftte **1 epoch** doğru; fazlası kesin ezberleme | `DPO_EPOCHS = 1` (S5 kapalı) | **uyumlu — doğruluyor** |
| H5 | `lr=1e-6` politikayı `π_ref` yakınında tutar, ani çöküşü engeller | D-029 tam olarak bu gerekçeyle seçmişti | **uyumlu — doğruluyor** |
| H6 | Kosinüs bandı `[0.25,0.80]` ve SNR tabanı `0.15` **sezgisel**, kalibre edilmeli | Zaten biliyoruz ve **ilan ediyoruz**: `POLARITY_COSINE_CALIBRATED=False`, `SNR_MARGIN_FLOOR_CALIBRATED=False` | **uyumlu — yeni bilgi yok** |
| H7 | Bağlamsız çift ⇒ aynı metin iki rolde ⇒ **çelişik gradyan** | Bizim gözlemimizle örtüşüyor (ayrık eşleştirme denemesi). ⚠ Ama bu **`best_by_event`'te olmuyor**, ayrık eşleştirmede oluyordu — DR ikisini ayırmıyor. Artık `texts_in_both_roles` ile **ölçülüyor** | **uyumlu ama kapsam karışık** |
| H8 | **Label Flip Rate > %10 DPO'yu bozar** | Sayısal eşik, **kaynaksız**. Metrik makul, %10 dayanaksız | **kullanılamaz** (eşik); metrik alındı |
| H9 | Distinct-N → *Papineni et al., 2002* | ❌ **Yanlış atıf.** Papineni 2002 = **BLEU**. Distinct-N = **Li et al., 2016** | **brief yanılmış** |
| H10 | Self-BLEU → *Papineni et al., 2002* | ❌ **Yanlış atıf.** Self-BLEU = **Zhu et al., 2018 (Texygen)** | **brief yanılmış** |
| H11 | Cal-DPO → *Xu et al., 2024, NeurIPS* | ⚠ Cal-DPO NeurIPS 2024'te **Xiao et al.** olarak geçiyor. Yazar adı şüpheli | **doğrulanmadı** |
| H12 | `nrDPO` (*Applied Sciences, 2025*) · `DualLoop-DPO` · `ExPO, 2025` · `DQO, 2025` · `Lanchantin et al., 2025` | ❌ Yazar/başlık yok veya eksik ⇒ **kimlik doğrulanamıyor**. Brief "yazar+yıl+yer" şart koşmuştu; §9 sicilinde sahte `arXiv:2506.08965` bu şekilde yakalanmıştı | **kullanılamaz** |
| H13 | DPO = *Rafailov et al., 2023* · KTO = *Ethayarajh et al., 2024, ICML* · SimPO = *Meng et al., 2024, NeurIPS* · DPP = *Kulesza & Taskar, 2012* | Dördü de gerçek ve doğru anılmış | **uyumlu** |
| H14 | **Tavsiye: DPO'yu bırak, KTO'ya geç** | Hizalama algoritmasının **tamamen değişmesi**. Kanal 2'nin mekanizmasını değiştirir, bugüne kadarki her ölçümü geçersiz kılar, ve ön-kayıt kilitlenmek üzere. Ayrıca **H1 premisine dayanıyor** — o doğrulanmadan bu büyüklükte bir değişiklik yapılmaz | **ertelendi** → sonraki ön-kayıt |
| H15 | DPO kalacaksa: negatif başına kullanım tavanı (`N≤3`), marjin bandı, olay başına çok çift | Üçü de eğitim setini değiştirir. Aynı gerekçe: **önce ölç**. Ayrıca DR kendi de uyarıyor — tavan koyarsa ikincil negatifler `SNR_MARGIN_FLOOR=0.15`'in altında kalabilir | **ertelendi** — B2'nin sayısına bağlı |

## H.3 Ne değişti, ne değişmedi

**Değişen:** yalnız **aletleme** — dört sayaç eklendi (`daa5f4b`). Hiçbir
eşik, hiçbir çift kurma stratejisi, hiçbir sabit değişmedi.

**Değişmeyen ve bilerek:** `best_by_event`. DR'nin bütün alternatifleri
(KTO, kullanım tavanı, marjin bandı) **doğrulanmamış bir premise** dayanıyor
ve hepsi eğitim setini değiştirir ⇒ kilit öncesi yapılırsa §2.10'un kuyusu.

**GAP-18 kapanmadı.** Durumu değişti: *"biliyoruz ama ne yapacağımızı
bilmiyoruz"*tan *"şiddetini ölçmedik, B2 ölçecek"*e. Karar B2'nin
`uniq_rejected` sayısından sonra.
