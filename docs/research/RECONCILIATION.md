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
| `2026-08-11_lamarckian-scope-and-channel-separation.md` | ✅ tam tur — **bölüm I** |

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


---

# I. DR brief #3 — Lamarckçı kapsam + kanal ayrımı (2026-08-11)

**Üç brief'in kaynak disiplini en iyisi.** Kimlikler büyük ölçüde doğru,
kavramsal düzeltmesi isabetli, ve önerdiği teşhislerden birini **zaten
yapmışız**. Ama sonundaki "Mutabakat Metni" bölümü alınmıyor — orası bizim
kalemimiz, ve DR kararları **alınmış gibi** yazmış.

## I.1 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| I1 | Düzenek **Darwinci** şekillenme iddiasını destekleyemez: popülasyon yok, diferansiyel üreme yok, seçilim atıl | Zaten böyle ilan ediyoruz (§8-L1 `F_agent` dejenere; "her ata tam olarak bir varis") | **uyumlu — doğruluyor** |
| I2 | Meşru daraltılmış iddia: *tek soy hattında, öz-ölçülen PE üzerinden öz-hizalama ile, sembolik bellek + parametrik ağırlık üzerinden **Lamarckçı epigenetik aktarım*** | Aksiyomun "iki kanal" formülasyonuyla örtüşüyor; iddia cümlemizi **daraltmak için kullanılabilir** | **uyumlu — benimsenir** |
| I3 | ⭐ **Kavramsal düzeltme:** *"ontogenetik adaptasyon"* değil, *"ontogenetik kazanımların **transjenerasyonel** Lamarckçı aktarımı"*. Ontogenez bireyin yaşamı içindedir; aktarım ondan sonraki adımdır | Brief'te *"ontogenetik uyarlanma çerçevesi doğru mu"* diye sormuştuk. Cevap: **kısmen**, ve düzeltme yerinde | **uyumlu — benimsenir** |
| I4 | ALife asgari mimarisi: Lenski LTEE (~10⁸ hücre, >75.000 nesil) · Tierra (Ray, 1991) · Avida (Ofria ve ark., 2004) | Kimlikler doğru. Karşılaştırma bizim ölçeğimizi (N=1, 2 nesil) dürüstçe konumlandırıyor | **uyumlu** |
| I5 | Lamarckçı operatör literatürü: Grefenstette (1991) · Ackley & Littman (1992). Lamarckçı aktarım yakınsamayı hızlandırır ama **çeşitliliği yok edip erken yakınsama** yaratır | Kimlikler gerçek. ⚠ Bizde çeşitlilik kaybı **iki nesilde gözlenemez**; not olarak değerli, kanıt olarak değil | **uyumlu — sınırlı** |
| I6 | Watson (2002) **SEAM**: "tek soy hattı üzerinde birikimli değişim" | ⚠ SEAM (Watson & Pollack) **simbiyogenetik modül birleşimi** üzerine ve **popülasyon** varsayar; "tek soy hattı" tarifi yanlış | **brief yanılmış** — kullanılmadı |
| I7 | FEP (Friston) sürprizi vekil hedef yapmayı destekler; başarısızlık kipleri: **Karanlık Oda**, öngörülebilir yıkım, kendi kalıbını tekrarlama | Kaynak gerçek (Karanlık Oda: Friston, Thornton & Clark, 2012). Bizde **GAP-17'nin tersi** ilginç: çeşitlilik düşmedi, 3-4 kat **arttı** — yani gözlenen kip bu değil | **uyumlu — bizde gözlenmedi** |
| I8 | ⭐⭐ **Tercihi bastırmadan ayıran ölçüm:** `Δlogπ(y_w)` ile `Δlogπ(y_l)` **ayrı ayrı** izlenmeli. Gerçek tercihte `Δlogπ(y_w) > 0` baskın; bastırmada `Δlogπ(y_w) ≈ 0` iken `Δlogπ(y_l) ≪ 0` | ✅ **Bunu zaten yapmışız.** D-029'un lr probe'u tam bu ayrımı ölçtü: **5e-5**'te chosen **−0.123** / rejected **−4.371** (seçilen bile düşüyor ⇒ saf bastırma); **1e-6**'da chosen **+0.085** / rejected −0.143 (yapıcı tercih). Karar buna dayanmıştı. ⚠ Ama **tek seferlik probe**ydu; gerçek koşumlar kaydetmiyordu → **D-049 ile kalıcı** (`985df29`) | **uyumlu — ve aletlendi** |
| I9 | Olgunun literatürdeki adı: *Probability Collapse / Logit Suppression / DPO over-optimization* | Ad doğru ve yararlı; ⚠ **spesifik atıf verilmemiş** (yazar/yıl yok) | **kısmen kullanılabilir** — ad alındı, atıf yok |
| I10 | Karşı-önlemler: EFE epistemik değer · içsel merak (Pathak ve ark., 2017; Houthooft ve ark., 2016) · entropi alt sınırı | Kimlikler gerçek. ⚠ Üçü de **ödül/amaç fonksiyonuna** dokunur ⇒ aksiyomun "trait verilmez" yasağına yakın; sonraki ön-kayıtta **tasarım kararı** olarak ele alınmalı | **ertelendi** |
| I11 | Getirimi kapatmanın adı: **Component Ablation / zero-shot parametrik probing**; RAG'de Lewis ve ark. (2020) benzer ablasyon kurar | Kimlik gerçek. Bizim **A2**'nin (OOD probing) literatür karşılığı | **uyumlu** |
| I12 | ⭐ **Getirimi kapatmanın riski: context starvation / OOD şoku.** Düşüş ağırlıkların yetersizliğinden değil, alışılmadık istem yapısından gelebilir | ⚠ **A2'yi olduğu gibi yapsaydık bu tuzağa düşüyorduk.** A2 "getirimi tamamen kapat" diye tarif edilmişti | **brief haklı — A2 yeniden tasarlanacak** |
| I13 | ⭐ Alternatif: **Plasebo / karşı-olgusal anı enjeksiyonu** — getirim kapatılmaz, gelen anıların **içeriği** nötr metinle değiştirilir. İstem yapısı ve uzunluğu korunur ⇒ OOD şoku yok | Bizim tasarımımızdan **kesinlikle daha iyi**. Sonraki ön-kayıt için A2'nin yerine geçer | **benimsenir → sonraki ön-kayıt** |
| I14 | Alternatif: **Nedensel aracı analizi / activation patching** (ROME deseni) · **SAE özellik kilitleme** | Kimlikler gerçek (ROME: Meng ve ark., 2022). ⚠ İkisi de bizim mevcut aletimizin çok ötesinde | **not edildi** |
| I15 | Kanal ayrımı iddiası için **çifte ayrışma** (double dissociation) kanıtı aranır: `ΔE_ağırlık + ΔE_bellek ≈ ΔE_toplam` | Somut ve savunulabilir bir çıta. ⚠ Bizde **hiç kurulmadı** — mevcut tasarım yalnız tek yönü ölçüyor | **açık — sonraki ön-kayıtın şartı** |
| I16 | Tek sayılı uç nokta zamanla yön değiştiren etkide **maskeleme artefaktı** üretir | D-044/D-045 tam olarak bunu ölçtü (%73–86 iptal). Brief **bizim bulgumuzu** doğruluyor | **uyumlu** |
| I17 | Yörünge araçları: **FDA** (Ramsay & Silverman, 2005) · **LMM zaman × kol etkileşimi** · DTW · değişim noktası · faz AUC | Kimlikler gerçek. `β₃` (zaman × kol) **ilkesel olarak savunulabilir**: etki zamanla değişiyorsa zamanı modelle | **uyumlu — sonraki ön-kayıt adayı** |
| I18 | **Tavsiye: sonraki birincil = "ikinci yarı yaşam AUC farkı"** | ⚠ **Tuzak.** *"İkinci yarı"* tam olarak D-045'te **gözlediğimiz** şey (6 karşıtlığın 5'i). Onu bir sonraki birincil yapmak, post-hoc gözlemi ön-kayıta taşımaktır. **Genel form (zaman × kol etkileşimi) ilkeseldir; "ikinci yarı" özel formu değildir** | **kısmen reddedildi** — genel form alınır, özel form alınmaz |
| I19 | Raporun kapanışı: *"Mutabakat Metni (RECONCILIATION.md) … birincil uç nokta FDA olarak **tescil edilmiştir**"* | ❌ DR kararları **alınmış gibi** yazmış ve bizim mutabakat belgemizin metnini üretmiş. Mutabakat **bizim** işimiz (D-006); bir brief kendi kabulünü ilan edemez | **alınmadı** |

## I.2 Ne değişti

**Kod:** yalnız **I8** → D-049 (`985df29`). `dpo_delta_logp_chosen`,
`dpo_delta_logp_rejected`, `dpo_chosen_went_down` artık her eğitim kolunda
kaydediliyor. Bu brief'in tavsiyesi olduğu için değil — **D-029 kararımız
zaten buna dayanıyordu ve gerçek koşumlarda görünmüyordu.**

**Değişmeyen:** hiçbir eşik, hiçbir amaç fonksiyonu, hiçbir uç nokta.
I10 (entropi/merak terimi) ve I13/I15 (kanal ayrımı protokolü) **sonraki
ön-kayıta**; ikisi de bu ön-kaydı günlerce bekletir (§2.10).

## I.3 Sonraki ön-kayıta taşınanlar

| Ne | Kaynak | Neden şimdi değil |
|---|---|---|
| **A2 yeniden tasarımı: getirimi kapatma → plasebo anı enjeksiyonu** | I12, I13 | A2 zaten bilerek ertelenmişti; brief tasarımının **kusurlu** olduğunu gösterdi ⇒ ertelemek artık daha da doğru |
| **Çifte ayrışma protokolü** | I15 | Kanal ayrımı iddiasının çıtası; mevcut tasarım tek yön ölçüyor |
| **Zaman × kol etkileşimi (LMM/FDA)** — genel form | I17 | ⚠ "ikinci yarı AUC" özel formu **alınmaz** (I18) |
| **İddia cümlesinin daraltılması + "transjenerasyonel" terimi** | I2, I3 | B4 raporunda kullanılır, kod değişikliği değil |


---

# J. DR brief #4 — ayrım üretmeyen bir evrende seçilim (2026-08-13)

**Ham cevap:** `2026-08-13_DR4-answer-raw.md` · **Sorusu:**
`2026-08-12_environment-differentiation-and-selection.md` · **Kayıt:** D-065.

Raporun **içeriği dört brief içinde en isabetlisi**, **kaynak disiplini ise
en kötüsü**. İki ayrı şeyi ayırmak gerekiyor: hangi mekanizmayı önerdiği
(çoğu yerinde), ve o mekanizmayı kime dayandırdığı (çoğu havada).

## J.0 ⚠ Kaynak denetimi — brief'in kendi şartıydı, rapor uymadı

Brief §0 açıkça *"her iddia için yazar + yıl + kalıcı kimlik, emin değilsen
**doğrulanamadı** yaz"* dedi. Rapor on iki kimlikten **beşini** eksiksiz
verdi, ve verdiklerinden **biri yanlış makaleye ait**.

| Kimlik | Denetim (Crossref / arXiv, 2026-08-13) | Sonuç |
|---|---|---|
| `10.1086/341018` | Pepper & Smuts, *A Mechanism for the Evolution of Altruism among Nonkin*, Am. Nat. 2002 | ✅ **birebir doğru** |
| `10.1103/PhysRevLett.95.098104` | Santos & Pacheco, *Scale-Free Networks Provide a Unifying Framework…*, PRL 2005 | ✅ **birebir doğru** |
| `10.1017/S0140525X06009083` | Mesoudi, Whiten & Laland, *Towards a unified science of cultural evolution*, BBS 2006 | ✅ **birebir doğru** |
| `arXiv:2404.16698` | Piatti, Jin, Kleiman-Weiner, Schölkopf, Sachan, Mihalcea, *Cooperate or Collapse* (GovSim), 2024 | ✅ **doğru** |
| `arXiv:2604.21255` | Yang, Zhang, Wen, Gong, Liu, Chu, Yu, *When Agents Look the Same: Quantifying Distillation-Induced Similarity in Tool-Use Behaviors*, 2026 | ✅ **kimlik gerçek** — rapor "doğrulanamadı" demişti, **biz doğruladık** |
| `arXiv:2606.18263` | Bhattacharyya, Singla, Shah, Chen, Ajmera, *How Well Do Large Language Models Capture Human Personality?*, 2026 | ✅ **kimlik gerçek** — persona manifold collapse orada |
| `10.1007/s00778-019-00574-9` → *"Cleasby vd., 2019"* | Gerçek sahibi: **Su, Liu, Zheng, Zhou, Zheng**, *A survey of trajectory distance measures and performance evaluation*, **VLDB Journal 2020** | ❌ **YANLIŞ ATIF** |
| *"MDPI 2072-4292"* (eşikli biliş iddiası) | 2072-4292 = **Remote Sensing** dergisinin ISSN'i. Yazar/yıl/başlık yok | ❌ **kimlik değil** |
| Kacser & Burns 1973 · Dykhuizen vd. 1987 | Gerçek: Dykhuizen, Dean & Hartl, *Metabolic flux and fitness*, **Genetics 115:25–31, 1987**; Kacser & Burns akı kontrol kuramı | ✅ **biz tamamladık** |
| Mouret & Clune 2015 (MAP-Elites) | *Illuminating search spaces by mapping elites*, **arXiv:1504.04909** | ✅ **biz tamamladık** |
| Reidys & Stadler 2001 · Ackley & Littman 1992 · Hinton & Nowlan 1987 · Sherratt & Morand-Ferron | kimlik verilmedi, doğrulanmadı | ⛔ **kullanılmadı** |
| *"popülasyon için alt sınır N=20–50"* | **hiçbir kaynak verilmedi** | ⛔ **kullanılmadı** |

⚠ **Cleasby yanlış atfı, bu projede yedinci kaynak kimliği hatası.** Doğrusu:
Cleasby, Wakefield, Morrissey ve ark., *Using time-series similarity measures to
compare animal movement trajectories in ecology*, **Behav. Ecol. Sociobiol. 73
(2019)** — makale **gerçek**, rapor yalnız **DOI'yi başka bir makaleden almış**.

## J.1 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| J1 | Özdeş kurallı kapalı sistemde salt stokastiklik (farklı seed) kalıcı ayrım üretmez; ortak havuz → trajedi Nash dengesi | Ölçtüğümüzle aynı yönde (D-060: %94–100 defect). ⚠ Ama **bize atfettiği varsayım bizim değil**: brief §3 zaten *"popülasyon tek başına yetmez"* diyordu | **uyumlu — ama DR bizi yanlış okudu** |
| J2 | **Yerel havuz + koşullu hareket ("Walk Away")** akrabalık olmadan pozitif kümelenme üretir (Pepper & Smuts 2002 ✅) | Kodda tek ve **global** havuz (`EnvironmentState.pool`, `step_pool`), uzam yok, ajan **bir** | **uyumlu — önkoşulu yok**, ② ile birlikte anlamlı |
| J3 | Ölçek-bağımsız ağ topolojisi işbirliğini ve çeşitliliği taşır (Santos & Pacheco 2005 ✅) | Etkileşim ağı **sıfır** (N=1) | **uyumlu — önkoşulu yok** |
| J4 | ⭐ **GovSim:** LLM ajanları iletişim kursa bile sürdürülebilirliği kuramıyor, GPT-4 dahil hayatta kalma <%54; **"evrenselleştirme" bilişsel önseli** işbirliğini belirgin biçimde artırıyor (Piatti vd. 2024 ✅) | ⭐ **Bizim için en değerli satır.** Bir alternatif açıklamayı eliyor: %94–100 defect **bizim evrenimizin özel kusuru değil**, literatürün taban gözlemi. Ve müdahalenin **prompt düzeyinde** işe yaradığı ölçülmüş | **uyumlu — dış referans noktası kazandık** |
| J5 | Davranışsal homojenizasyon: farklı ajanlar aynı akıl yürütmeye çöker, sebebi ortak öğretmenden damıtma (Yang vd. 2026 ✅ kimlik) | ⚠ **Kapsam kayması:** o çalışma **modeller arası** benzerliği ölçüyor; bizde tek model, tek ajan. Bizim çöküşümüzü "damıtma" açıklayamaz — açıklaması **bedelsizlik** (D-060 §2.3) | **kısmen — mekanizma bizim vakamıza uymuyor** |
| J6 | Persona manifold çöküşü: zengin persona **çeşitliliği azaltıyor** (Bhattacharyya vd. 2026 ✅ kimlik) | Doğrudan A4-③'e dokunuyor: `SYSTEM_PROMPT`'u **zenginleştirmek** çeşitlilik satın almıyor. L14 ile uyumlu | **uyumlu — ikinci ön-kayıt girdisi** |
| J7 | Prompt→sınıflandırıcı kısa devresinin adı *"Verbal Alignment Masking / reward hacking"* | ⚠ Ad için gösterilen kaynak (2604.21255) **bu iddiayı taşımıyor** — o makale tool-use benzerliği üzerine. Olgunun kendisi bizde **ölçülü** (L14: COOPERATE sözlüğünün 3/4'ü prompt'ta) | **ad alınmadı — kaynak eşleşmiyor** |
| J8 | `decay ≥ recovery` yapısaldır; enerji monoton azalan; sıfır bedel ⇒ defect bedava | **D-061'in cebirsel kanıtının aynısı.** Rapor bizim ölçümümüzü tekrar ediyor ⇒ **kanıt değil**, teyit | **uyumlu — ama bağımsız kanıt değil** |
| J9 | ⭐ **Azalan getiri:** akı, enzim aktivitesinin **içbükey/hiperbolik** fonksiyonudur; yüksek ifadede **seçilim nötrleşir** (Dykhuizen, Dean & Hartl 1987, Genetics 115:25–31 ✅ biz doğruladık) | ⭐ **A4-① için literatürdeki en sağlam dayanak.** Ve tersten okununca bugünkü durumumuzun teşhisi: doyum ⇒ nötrlük. *"Çıkarım = enerji"* doğrusal bağı defect'i baskın bırakır; **içbükey** kazanç eğrisi gerekir | **uyumlu — ① için benimsenir** |
| J10 | Ölüm eşiği ajanı "yeterince al"maya zorlar; yenilik arayışını açlık tetikler | Kodda ölüm yok: `should_continue` `AB_ENERGY_FLOOR` yastığıyla yaşamı sürdürüyor. ⚠ Destek kaynağı (Sherratt & Morand-Ferron) **doğrulanmadı** | **yön uyumlu — kaynak kullanılmadı** |
| J11 | Eşikli/çift modlu maliyet: yüksek efor ancak eşik aşılınca mobilize olur | ⚠ Kaynak kimliği **dergi ISSN'i** ⇒ kullanılmaz. Ayrıca DR bilmiyor: bizde **zaten** eşikli çift mod var (LOD: SYSTEM_1/SYSTEM_2, bilişsel yük eşiği). Eksik olan o değil, **eylemin ajana yansıyan enerji farkı** | **kullanılmadı — ve kısmen zaten var** |
| J12 | İddia Darwinci değil **Lamarckçı/kültürel**; bu çerçevede nicel modellenebilir (Mesoudi vd. 2006 ✅) | Brief #3'ün mutabakatı (§I2/I3) bunu zaten karara bağlamıştı. Rapor **bağımsız olarak aynı yere** geldi | **uyumlu — §I ile örtüşüyor** |
| J13 | `shuffle` kolu (aynı çiftler, ters yön) plastik yanıtı gürültüden ayırmak için **mükemmel bir epigenetik kontrol** | Kontrolümüzün dışarıdan tasdiki. ⚠ Ama **tek başına** yeterli olduğunu söylemiyor; çifte ayrışma çıtası (§I15) hâlâ açık | **uyumlu** |
| J14 | Popülasyon için asgari **N=20–50** | ⛔ **Kaynaksız sayı.** Brief #1'in dersi birebir tekrar ediyor: kaynaksız eşik kilitli karara **giremez** | **kullanılmadı** |
| J15 | Düz/nötr fitness manzarası tanısı; varyans eşiğin altındaysa adaptif yürüyüş rastgele yürüyüşe döner | Teşhis bizim ölçümümüzle aynı (D-060: sınıf 120/120 `low`). ⚠ Kaynak (Reidys & Stadler) doğrulanmadı, ve **nicel eşik verilmedi** — brief tam da onu sormuştu | **uyumlu — ama sorulan sayı gelmedi** |
| J16 | ⭐ **MAP-Elites / Kalite-Çeşitlilik**: tek hedefli fitness yerine davranışsal tanımlayıcı ızgarası (Mouret & Clune 2015 ✅ biz tamamladık) | Fikir sağlam ama **arşiv + popülasyon varsayıyor** ⇒ ②'nin önkoşulu. Önerdiği eksenler (ortalama PE × havuz çekimi) bizde **zaten ölçülü** | **uyumlu — ②'ye bağlı, ikinci ön-kayıt** |
| J17 | Birincil uç noktanız **ağırlık vektörü L-normu**, AdamW gürültüsüne boğuluyor | ❌ **Olgusal hata.** Birincilimiz ağırlık değil: varisin **doğum-drift büyüklük vektörü** (`transfer_to_heir` → `birth_drift_magnitudes`), gen2 koşmadan, ve varis **ebeveynin adapter'ını almıyor** (kodda `3A: do not load parent adapter`). AdamW'nin o vektöre değen bir yolu yok | **DR yanılmış** |
| J18 | Uç noktayı **varisin eylem dizisinin `shuffle` koluna DTW uzaklığı** yap | İki ayrı sorun: (a) o bir **uç nokta değil karşıtlık** — birincilimiz `null` çapasına uzaklıkları karşılaştırıyor; (b) ⚠ **yörünge uç noktalarının daha büyük ayrım gösterdiğini zaten ölçtük** (D-044/D-045) ve **bilerek almadık**: etkiyi görüp uç nokta seçmek post-hoc olur (§2.7, L9) | **bilinçli sapma — sıralama korunuyor** |
| J19 | Yörünge benzerliği araçları: DTW, Fréchet (Cleasby vd. 2019) | Araçlar yerinde; §I17 de aynı yere işaret etmişti. ⚠ **DOI yanlış** (bkz. J.0), doğrusu Behav. Ecol. Sociobiol. 73 (2019) | **uyumlu — kimlik düzeltildi** |
| J20 | Sonuç: popülasyon **tek başına** düz manzarayı aşmaz; önce bedel + azalan getiri gerekir | ⭐ Bu, `CLAUDE.md`'nin **"①  önce, sonra ②"** önerisiyle bağımsız olarak **aynı sıralama**. Rapor bunu bizden duymadan söyledi (brief §3 soruyordu, cevap vermiyordu) | **uyumlu — öneriyi güçlendiriyor** |

## J.2 ⚠ Girdi kalitesi: J17'nin yarısı bizim hatamız

Brief §1 *"varis ebeveynin adapter'ını almıyor"* diyordu ama §2.5 birincili
yalnızca *"doğum-drift vektörü"* diye adlandırdı ve **neyin vektörü olduğunu
yazmadı**. DR onu ağırlık vektörü sandı ve S6'nın yarısını (AdamW gürültüsü,
"milyarlarca parametreye dağılma") o yanlış varsayım üstüne kurdu.

**Üç brief'in ortak dersi burada dördüncü kez tekrarlandı:** brief kalitesi
girdi kalitesiyle sınırlı, ve girdiyi biz yazıyoruz.

## J.3 A4 kararına ne girdi

| Seçenek | Raporun getirdiği |
|---|---|
| **① metabolik döngü** | **Güçlendi.** J9 kazanç eğrisinin **biçimini** söylüyor (doğrusal değil içbükey) — D-061 *"toparlanma terimi yeniden tasarlanmalı"* demişti ama biçimi söylemiyordu. J10 ölüm eşiğini ekliyor (yön uyumlu, kaynağı zayıf) |
| **② popülasyon** | **Sıralaması doğrulandı, öncelik almadı.** J20 bağımsız olarak *"tek başına yetmez"* diyor; J16 (MAP-Elites) ②'nin **üstüne** gelecek bir katman |
| **③ prompt priming'i kaldır** | **Karışık.** J4 prompt düzeyindeki bilişsel önselin **ölçülmüş** bir kaldıraç olduğunu gösteriyor (evrenselleştirme) ⇒ ③'ün "tek başına işe yaramaz" değerlendirmesi **zayıfladı**. Ama J6 tersini hatırlatıyor: prompt'u **zenginleştirmek** çeşitlilik satın almıyor. İkisi çelişmiyor — fark, eklenen şeyin **persona** mı **karar kuralı** mı olduğu |

⇒ **Claude Code'un önerisi değişmedi: ① önce, sonra ②.** Rapor bunu iki
bağımsız yoldan destekledi (J9 mekanizma, J20 sıralama).
⚠ **①'in nasıl yapılacağı hâlâ tasarım kararı** (D-007) ve içinde en az üç
alt seçim var: kazanç eğrisinin biçimi, ölüm eşiği olacak mı, ve
`METABOLIC_FLOOR`'un çifte rolü (asgari tüketim **ve** azami toparlanma)
ayrılacak mı.

## J.4 İkinci ön-kayıta taşınanlar

| Ne | Kaynak | Not |
|---|---|---|
| **İçbükey (azalan getirili) enerji kazanç eğrisi** | J9 | ⚠ Eğrinin **parametreleri** ölçümden seçilemez (§2.7) — biçim literatürden, değer gerekçeyle |
| **Ölüm eşiği** (enerji 0 ⇒ yaşam biter) | J10 | ⚠ Erken ölüm örneklemi daraltır; N hesabına girer |
| **MAP-Elites / davranışsal tanımlayıcı ızgarası** | J16 | ②'nin önkoşulu; eksenler bizde zaten ölçülü |
| **DTW / Fréchet yörünge ölçütü** | J18, J19 | ⚠ **Etkiye bakmadan** kilitlenmeli — D-064'ün çözünürlük envanteri bunun disiplinli yolu |
| **"Evrenselleştirme" tarzı karar kuralı önseli** | J4 | ⚠ Aksiyomun *"trait verilmez"* yasağına yakın; **tasarım kararı**, sessizce alınmaz |


---

# K. Yerel literatür taraması — değişken yaşam uzunluğunda uç nokta (2026-08-13)

⚠ **Bu bir DR raporu DEĞİL.** Deep Research bu tur çalışmadı; tarama Claude
Code tarafından yapıldı. **Sistematik derleme değil, hedefli tarama** —
bulunmamış bir alt literatür olabilir. DR düzeldiğinde
`2026-08-13_variable-lifespan-endpoints-and-censoring.md` aynen sorulabilir.

**Yöntem:** her kimlik Crossref/arXiv'den **açılıp** doğrulandı (başlık +
yazar + dergi + yıl). ⚠ **Yalnız kimlik doğrulandı, içerik okunmadı** —
D-065'e koyduğumuz sınırın aynısı burada da geçerli.

⚠ **Taramanın kendisi bir yanlış atıf üretti ve yakalandı:** Schoenfeld'in
örneklem büyüklüğü makalesi için ilk aday DOI `10.2307/2530643` yazılmıştı;
açıldığında **Greenland & Robins 1985** çıktı. Doğrusu `10.2307/2531021`.
⇒ Doğrulama döngüsü DR'ye olduğu kadar **bize de** gerekiyor.

## K.0 Doğrulanan kimlikler

| # | Kaynak | Kimlik | Durum |
|---|---|---|---|
| V1 | Lachin, *Fallacies of last observation carried forward analyses*, Clinical Trials | `10.1177/1740774515602688` · **2015** | ✅ |
| V2 | Suissa, *Immortal Time Bias in Pharmacoepidemiology*, Am J Epidemiol, 2008 | `10.1093/aje/kwm324` | ✅ |
| V3 | Anderson, Cain & Gelber, *Analysis of survival by tumor response*, J Clin Oncol, 1983 | `10.1200/jco.1983.1.11.710` | ✅ |
| V4 | Matthews, Altman, Campbell & Royston, *Analysis of serial measurements in medical research*, BMJ, 1990 | `10.1136/bmj.300.6719.230` | ✅ |
| V5 | Fine & Gray, *A Proportional Hazards Model for the Subdistribution of a Competing Risk*, JASA, 1999 | `10.1080/01621459.1999.10474144` | ✅ |
| V6 | Schoenfeld, *Sample-Size Formula for the Proportional-Hazards Regression Model*, Biometrics, 1983 | `10.2307/2531021` | ✅ (ilk aday yanlıştı) |
| V7 | Henderson, Diggle & Dobson, *Joint modelling of longitudinal measurements and event time data*, Biostatistics, 2000 | `10.1093/biostatistics/1.4.465` | ✅ |
| V8 | Stearns, *Trade-Offs in Life-History Evolution*, Functional Ecology, 1989 | `10.2307/2389364` | ✅ |

## K.1 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| K1 | ⭐ **Bizim yaptığımız şeyin adı var: LOCF.** `_pad_pe_list` diziyi **son gözlemle** 50'ye tamamlıyor, sonra ortalaması alınıyor — bu literatürde *last observation carried forward*. V1 doğrudan bunun eleştirisi: LOCF **muhafazakâr değildir**, yanlılığın yönü **iki tarafa da** olabilir ve varyansı **olduğundan küçük** gösterir | D-068: gen1'de **%71** pad. Yani uç noktamızın çoğu artık LOCF çıktısı | **fark edilmemiş kayma** — icat etmemiz gereken bir şey yok, **bırakmamız** gereken bir şey var |
| K2 | **Hayatta kalma süresi maruziyeti/pencereyi belirlediğinde ortaya çıkan yanlılığın adı: immortal time bias** (V2) | Bizde birebir karşılığı: uzun yaşayan kol daha çok **gerçek** olay üretiyor; sabit pencerede ortalama almak *"nasıl yaşadı"* ile *"ne kadar yaşadı"*yı karıştırıyor | **uyumlu — teşhis adı kazandık** |
| K3 | ⭐ **Standart çözüm: landmark analizi** (V3). Sabit bir zamana kadar bekle, o anda **hayatta olanları** al, ölçümü oradan yap | Bizde doğrudan uygulanabilir: uç nokta sabit bir **olay indeksinde** okunur, o indekste ölmüş soylar **önceden ilan edilmiş** bir kuralla dışarıda kalır | **benimsenmeye aday — K1 kararı** |
| K4 | **Seri ölçümler tek bir özet istatistiğe indirgenip o karşılaştırılır** (AUC, eğim, tepe) — V4. Farklı uzunluktaki dizileri ham ortalamayla karşılaştırmaya alternatif | Bizim *"yaşam boyu özet"* adayımızın literatürdeki karşılığı. ⚠ Uzunluk farkı **hâlâ** içeride: AUC yaşam uzunluğuyla ölçeklenir, oran (olay başına) ölçeklenmez | **uyumlu — ama normalizasyon biçimi ayrıca karar** |
| K5 | **Ölüm, ilgilendiğimiz sonucun önünü kesiyorsa bu bir rekabet eden risktir** ve alt-dağılım modeli o iş için (V5) | ⚠ Bizde ölüm **sonucun kendisiyle iç içe**, sadece rakip değil. Uygulanabilir ama tasarımı büyütür | **not edildi — bu tur alınmıyor** |
| K6 | ⭐ **Zaman-olay analizinde güç, denek sayısına değil OLAY sayısına dayanır** (V6) | ⇒ **K3'ün (N/güç) cevabı buradan:** bizde **sansür yok**, her ajan kesin ölüyor ⇒ olay sayısı = soy sayısı. Bu **lehimize**: ömür uç noktası için güç, sansürlü tasarımlardan daha verimli | **uyumlu — hesap yeniden yapılabilir** |
| K7 | **Uzunlamasına bir değişkenle olay zamanını birlikte modelleme** (joint models, V7) — tam olarak "değerin son hâli ölüm mekanizmasınca belirlendiğinde" için | ⚠ Bizim ölçeğimizin (onlarca soy) **çok üstünde**. Doğru araç ama şu an pahalı | **not edildi — ertelendi** |
| K8 | **Ömür bir yaşam-tarihi bileşenidir ve uygunlukla takas ilişkisi içindedir** (V8) | ⚠ `F_agent`'ın %30'u `t_surv/T_gen`. Ölüm mümkün hale gelince ömür hem **girdi** hem **sonuç** oldu ⇒ **çift sayım** riski gerçek | **açık — K4/K5 kararına girdi** |

## K.2 Bu taramanın **cevaplayamadığı**

- ALife/yapay yaşam literatüründe bu problemin **kendi** geleneği ne diyor
  (tarama biyoistatistik tarafında kaldı).
- Landmark noktasının **nasıl seçildiğine** dair bir ilke bulunamadı;
  V3 yöntemi tarif ediyor, seçim kuralını değil.
- Küçük-N simülasyon çalışmalarında örneklem gerekçelendirmesi standardı.

⇒ **DR brief #5 hâlâ geçerli ve gönderilmeyi bekliyor.** Bu tarama K1/K2'yi
karara bağlanabilir hale getirdi, kapatmadı.

## K.3 Claude Code'un önerisi (literatür değil, öneri)

1. **LOCF bırakılır.** Uç nokta pad edilmiş dizinin ortalaması olmaktan çıkar.
2. **Birincil: landmark.** Sabit bir olay indeksinde okunur. ⚠ İndeks
   **yapısal** bir çapadan seçilir — `METABOLIC_GRACE_EVENTS = 10`, yani doğum
   geçişinin bittiği an — **ölüm zamanlarına bakılarak değil**. Ölçülen ölüm
   zamanlarına bakıp landmark seçmek post-hoc olur (L9).
3. **Landmark'tan önce ölen soy için kural önceden ilan edilir**, ve *"kaç soy
   düştü"* bir **geçerlilik kriteri** olur (sonuç değil).
4. **İkincil: yaşam boyu özet**, olay başına oran olarak normalize (AUC değil —
   AUC ömürle ölçeklenir ve K8'in çift sayımını geri getirir).
5. **Enerji (K2) aynı iki biçimde okunur:** landmark anındaki değer +
   zaman-integre ortalama. `E_final` **bırakılır** — değeri ölüm kuralının
   kendisi belirliyor.
6. **Güç (K3):** sansürsüz olduğumuz için olay sayısı = soy sayısı; hesap V6
   ile yeniden yapılır.

---

# §L — Popülasyon, seçilim şeması ve ortak havuz (yerel tarama, 2026-08-13)

⚠ **DR raporu DEĞİL.** Deep Research bu turda da çalışmadı: dört farklı
cihaz/ağdan denendi, hepsinde *"size yardımcı olamıyorum, ben sadece metin
tabanlıyım"* dönüp kota çıktısız tükendi. Tarama **Claude Code** tarafından
yapıldı; brief #6
(`docs/research/2026-08-13_population-selection-and-shared-commons.md`)
geçerliliğini korur ve DR düzelirse aynen sorulur.

**Yöntem:** D-069'un yöntemi — her kimlik Crossref/arXiv üzerinden **açılarak**
doğrulandı. ⚠ İçerik yalnız **açık erişimli** olanlarda okundu; iki kaynağın
bulgusu alınamadı (aşağıda işaretli).

## L.0 Doğrulanan kimlikler

| # | Kaynak | Kimlik | Durum |
|---|---|---|---|
| V1 | Goldberg & Deb 1991, *A Comparative Analysis of Selection Schemes Used in Genetic Algorithms*, Foundations of Genetic Algorithms 1 | `10.1016/b978-0-08-050684-5.50008-2` | ✅ kimlik |
| V2 | Miller & Goldberg 1996, *Genetic Algorithms, Selection Schemes, and the Varying Effects of Noise*, Evolutionary Computation 4(2) | `10.1162/evco.1996.4.2.113` | ✅ kimlik |
| V3 | Vallinder & Hughes 2024, *Cultural Evolution of Cooperation among LLM Agents* | `arXiv:2412.10270` (13 Ara 2024) | ✅ kimlik + özet |
| V4 | Kofler & Schlötterer 2013, *A Guide for the Design of Evolve and Resequencing Studies*, Mol Biol Evol 31(2):474–483 | `10.1093/molbev/mst221` | ✅ kimlik + **bulgu** |
| V5 | Xiao, Duarri-Redondo, Thorhölludottir, Chen & Schlötterer 2023, *Non-additive effects between genotypes: Implications for competitive fitness assays*, Ecology and Evolution 13(11):e10713 | `10.1002/ece3.10713` | ✅ kimlik + **bulgu** |
| V6 | Mills & Beatty 1979, *The Propensity Interpretation of Fitness*, Philosophy of Science 46:263–286 | `10.1086/288865` | ✅ kimlik |
| V7 | Lehman & Stanley 2011, *Abandoning Objectives: Evolution Through the Search for Novelty Alone*, Evolutionary Computation 19(2):189–223 | `10.1162/evco_a_00025` | ✅ kimlik |
| V8 | Kirby, Cornish & Smith 2008, *Cumulative cultural evolution in the laboratory*, PNAS 105(31):10681–10686 | `10.1073/pnas.0707835105` | ✅ kimlik · ⚠ **tasarım sayıları doğrulanamadı** |
| V9 | Briesch, Sobania & Rothlauf 2023, *On the Trade-Off between Population Size and Number of Generations in GP for Program Synthesis*, GECCO Companion | `10.1145/3583133.3590681` | ✅ kimlik · ⚠ **bulgu alınamadı (403)** |

⚠ **Tarama yine kendi hatasını yakaladı.** V3'ü ararken yazarı *"Vallinder &
**Hubinger**"* diye yazdım; doğrulama **Hughes** olduğunu gösterdi (Hubinger
başka biri). D-069'daki Schoenfeld hatasının aynısı — **doğrulama döngüsü
bize de gerekiyor**, yalnız DR'ye değil.

## L.1 Soru bazında bulgular

### ⭐ S3 — ortak havuzda kol kirlenmesi: **literatürde adı ve ölçülmüş kusuru var**

**Bulgu (V5, ölçülmüş):** Referans suş kullanan rekabetçi uygunluk ölçümü,
genotipler arasında **etkileşim olmaması** varsayımına dayanır. Xiao ve ark.
bu varsayımın ihlal edildiğini gösteriyor: frekansa bağlı seçilim rakibin
kimliğine göre değişiyor, ölçüm **zamanına** göre uygunluk sıralaması
değişebiliyor, ve odak popülasyon **ortamı değiştirerek** referans suşun
gelişimini etkiliyor.

⇒ **Bu bizim tasarımımızın doğrudan tarifi.** Bizim `null` kolumuz bir
**referans suş** — iki mesafe ona göre ölçülüyor (`‖lived−null‖` vs
`‖shuffle−null‖`). Brief #6'nın (b) seçeneği (tek havuz, karışık kollar), o
varsayımı **tükenen bir ortak kaynak üzerinden yapı gereği** ihlal eder: bir
kolun aşırı hasadı diğerinin ortamıdır.

⚠ V5 böcek popülasyonlarında; bizim ajanlarımıza taşınması **analoji**.
Ama ihlal edilen varsayım aynı varsayım.

### S1 — üreme/seçilim şeması

- **V1:** seçilim baskısının ölçüsü **devralma süresi** (takeover time);
  orantılı, sıralama, turnuva ve durağan-durum şemaları bu eksende
  karşılaştırılıyor. Turnuva baskısı turnuva boyutuyla **ayarlanabiliyor**.
- **V2:** aynı şemalar **gürültülü uygunluk** altında farklı davranıyor.
  ⚠ Bizde uygunluk **tek yaşamdan** geliyor ⇒ gürültülü. Bu, şema seçiminin
  bizde teknik bir ayrıntı **olmadığını** gösteriyor.
- **V3 (en yakın analog):** LLM ajanları, nesiller boyu, **kesme seçilimi**
  (üst %50 hayatta kalır). ⚠ Tasarım sayıları (12 ajan / 12 tur) yalnız
  ikincil özetten geldi, **birincil kaynakta doğrulanmadı**.

⚠ **V3'ün bizim için kritik kısıtı:** aktarılan şey **strateji metni** —
yani doğrudan **davranışsal önsel**. Bu bizim aksiyomumuzun (§1.1) yasakladığı
kanalın ta kendisi. ⇒ **En yakın yayımlanmış analog, bizim kapattığımız
kanalı kullanıyor.**

### S2 / S6 — sürüklenme, tekrar sayısı ve bütçe

**Bulgu (V4, ölçülmüş, birebir alıntı):** *"replication of E&R is more
important for detecting the targets of selection than increasing the
population size"* ve *"We advise to prioritizing replication over population
size for species such as Drosophila, where maintenance of large population
sizes is resource intensive."* Sabit 8.000 bireylik bütçede tekrar sayısını
artırmak gücü artırıyor; güçlü seçilim için **beş tekrar** yetiyor.

⇒ **Bizim eşleştirmemiz:** *tekrar* = tohum, *popülasyon boyutu* = N ajan.
Literatürün yönü: **daha çok tohum, daha küçük popülasyon.**

⚠ **Ama ölçek uyuşmuyor ve bu dürüstçe söylenmeli.** V4'ün rejimi 60 nesil ve
yüzlerce-binlerce birey; bizim tartıştığımız N=5–20 ve G=3–5. Yön alınabilir,
**sayı alınamaz**. V9 (evrimsel hesaplamada aynı takas) **bulgusu
alınamadı** (403).

### S4 — uygunluk hem seçilim girdisi hem sonuç

**Bulgu (V6):** *tautology problem* — uygunluk **gerçekleşmiş** sonuçla
tanımlanırsa o sonucu açıklayamaz; *"en uygunun hayatta kalması"*, *"hayatta
kalanların hayatta kalması"*na indirgenir. Yerleşik çözüm **propensity
(eğilim) yorumu**: uygunluk, bağımsız ölçülebilir özelliklerden **tahmin
edilen** üreme eğilimidir, gerçekleşmiş hayatta kalma değil.

⇒ **Bizde doğrudan karşılığı var ve D-071 bunu hem yarı düzeltti hem yarı
büyüttü.** `F_agent`'ın %30'u artık **gerçekten** hayatta kalma ölçüyor
(D-071 öncesi sabit 1.0'dı). Popülasyonda o skor **kimin üreyeceğini**
belirlerse, gerçekleşmiş hayatta kalma hem girdi hem seçilim ölçütü hem
raporlanan sonuç olur — V6'nın tarif ettiği döngü.

**V7:** seçilim ölçütünü sonuç ölçüsünden **ayırmak** incelenmiş bir strateji
(novelty search); amaç fonksiyonunun kendisi aramayı yanlış yöne
sürükleyebiliyor.

### S5 — kaç nesil

**V8** bizim ata→varis zincirimizin **birebir paradigması** (iterated
learning / aktarım zinciri) ve iddiası **birikimli** yapının nesiller boyunca
ortaya çıkması. ⚠ **Kaç nesil / kaç zincir olduğu birincil kaynakta
doğrulanamadı** (sayfa vermedi). ⇒ *"kaç nesil yeter"* sorusuna bu taramadan
**sayı çıkmadı**.

## L.2 Bu taramanın **cevaplayamadığı**

1. **Kaç nesil = birikimli kalıtım.** V8 paradigmayı veriyor, çıtayı değil.
2. **V9'un bulgusu** (403) — evrimsel hesaplama tarafındaki popülasyon/nesil
   takasının sayısı.
3. **Bizim ölçeğimiz için tekrar/popülasyon dengesi.** V4 yön veriyor, ama
   rejimi bizimkinin çok üstünde.
4. **ALife geleneğinin kendi yaklaşımı** — hedefli tarama bunu kapsamadı.

## L.3 Claude Code'un okuması (literatür değil, okuma — karar Yasin'in)

1. **S3 cevabı (a) yönünde güçlü:** kol başına ayrı havuz. Gerekçe literatür:
   `null` çapamız bir referans suş tasarımıdır ve V5 tam da o tasarımın ortak
   ortamda nasıl bozulduğunu **ölçmüş**. Tek havuzda karışık kollar,
   birincil karşıtlığın anlamını değiştirir.
2. **Tohum sayısını popülasyon boyutuna tercih et** (V4'ün yönü) — bu, GPU
   bütçesiyle de uyumlu.
3. **⚠ S4 açık bir tasarım borcu yarattı:** `F_agent` şu an gerçekleşmiş
   hayatta kalmayı içeriyor. Popülasyonda seçilim ölçütü yapılırsa V6'nın
   döngüsüne girer. Seçilim ölçütü ile raporlanan sonucun **ayrılması**
   gerekebilir — bu bir ön-kayıt kararıdır, kod kararı değil.
4. **V3 bir uyarı olarak okunmalı:** en yakın yayımlanmış analog, sonucu
   **strateji metni aktararak** alıyor. Bizim aksiyomumuz o kanalı kapatıyor.
   Bu, K7'nin bedelinin literatürdeki üçüncü bağımsız teyidi (J4 ve D-068'den
   sonra).

---

# §M — DR brief #6 mutabakatı: popülasyon ve ortak havuz (2026-08-14)

**Ham cevap:** `2026-08-14_DR6-answer-raw.md` · **Brief:**
`2026-08-13_population-selection-and-shared-commons.md`

⚠ DR nihayet çalıştı (beş denemeden sonra). Cevap **kapsamlı ve iki yerde
gerçekten değerli**, ama sicil deseni tekrarlandı ve **yeni bir kusur türü**
ekledi.

## M.0 Kimlik doğrulaması — 13 iddia, 12 kaynak

| Kaynak | Verilen DOI | Crossref'te ne çıktı | Durum |
|---|---|---|---|
| Goldberg & Deb 1991 | `10.1016/b978-0-08-050684-5.50008-2` | *A Comparative Analysis of Selection Schemes Used in Genetic Algorithms* | ✅ (D-075/V1 ile aynı) |
| Bäck 1994 | `10.1109/ICEC.1994.350042` | *Selective pressure in evolutionary algorithms: a characterization of selection mechanisms*, IEEE ICEC | ✅ |
| Branke & Schmidt 2003 | `10.1007/3-540-45105-6_91` | **Selection in the Presence of Noise**, GECCO 2003 | ✅ kimlik |
| Chevin 2011 | `10.1098/rsbl.2010.0580` | *On measuring selection in experimental evolution*, Biology Letters 7:210–213 (Crossref yıl: 2010) | ✅ **ve konuya birebir** |
| Hudgens & Halloran 2008 | `10.1198/016214508000000292` | *Toward Causal Inference With Interference*, JASA 103:832–842 | ✅ **ve konuya birebir** |
| Price 1970 | `10.1038/227520a0` | *Selection and Covariance*, Nature 227:520–521 | ✅ |
| **Bedau, Snyder & Packard 1998** | `10.1162/artl.1998.4.4.431` | **404 — DOI çözülmüyor.** Crossref başlık taraması da bulmuyor | ❌ **KIRIK** |
| Wright 1931 · Elena & Lenski 2003 · Aronow & Samii 2017 · Haigh 1978 · Wiser vd. 2013 | — | ⏳ **doğrulanmadı** (Crossref 429; bu turda sıraya girmedi) | ⏳ |

⚠ **Evrimsel aktivite istatistikleri kavramı gerçek** (Bullock & Bedau 2006,
`10.1162/artl.2006.12.2.193` doğrulandı) — **kırık olan atıf**, kavram değil.

## M.1 ⚠ YENİ KUSUR TÜRÜ: doğru kimlik, **yanlış iddia**

Önceki turlarda hata *"kaynak yok / kaynak uydurma"*ydı. Bu turda kaynaklar
**gerçek** ama bazılarına **o kaynakta olmayan iddialar** yükleniyor. Bu daha
tehlikeli: DOI doğrulaması bunu **yakalamıyor**.

| Nereye | Ne yükleniyor | Kaynak gerçekte ne | Karar |
|---|---|---|---|
| **S6** | *"tespit gücü N'ye üstel olarak daha duyarlı"* → Goldberg & Deb 1991 | O makale **devralma süresi / seçilim baskısı** analizidir; deney tasarımı güç analizi **değildir** | ❌ **brief yanılmış** |
| **S2** | *"nötr ebeveyn seçim kontrolü"* → Branke & Schmidt 2003 | O makale **gürültülü uygunluk altında seçilim** üzerinedir; sürüklenme kontrolü tasarımı değil | ❌ **brief yanılmış** |
| **S6** | *"olay bütçesi 30'un altına düşmemeli"* → Elena & Lenski 2003 | Mikrobiyal evrim derlemesi bizim olay bütçemiz hakkında **hiçbir şey söyleyemez** | ❌ **çıkarım, atıf kılığında** |
| **S1** | Bäck 1994 → *"Ölçülmüş Deney"* | **Teorik karakterizasyon** | ⚠ kanıt türü yanlış etiketlenmiş |

## M.2 ⚠ On üç iddianın on üçü *"Tam Uyumlu"*

Brief açıkça *"bir öneri kısıtlardan birini ihlal ediyorsa **işaretle**"* dedi.
On üç satırda **sıfır** işaret. Bu ayırt etme değil, onaylama.

**En az iki öneri kısıtlara dokunuyor ve işaretlenmemiş:**

- **İki aşamalı doygunluk tasarımı** (%25/%50/%75 `lived` oranlı kovanlar)
  kolların **ne olduğunu** değiştirir; bu ön-kayıtlı bir protokol maddesidir.
- **Price eşitliği** `wᵢ` = *"ürettiği varis sayısı"* istiyor. Bugün bir
  ebeveynin **tam olarak bir** varisi var ⇒ `w` **sabit**, kovaryans tanımsız.
  Yani öneri, henüz var olmayan bir mekanizmayı **varsayıyor**.

## M.3 ⭐ İçsel çelişki — ve ②'nin amacını doğrudan vuruyor

- **§5 (kendi cümlesi):** birikimli seçilim izleri **G = 5–10** aralığında
  belirir; G=2 yalnız *"anlık aktarım"* gösterir.
- **§6 sentezi:** bütçe **G = 3**'e kaydırılmalı.

⇒ **Rapor kendi çıtasının altını öneriyor.** ②'nin bütün gerekçesi birikimli
kalıtım iddiası (D-014, D-074); G=3 o iddiayı raporun kendi ölçütüne göre
kuramaz. Rapor bu çelişkiyi **fark etmiyor**.

## M.4 D-075 ile çelişki — ve çözümü

| | Ne diyor | Dayanağı |
|---|---|---|
| **DR (§6)** | N'yi büyüt, G'yi küçült ⇒ **N=16, G=3** | Goldberg & Deb 1991 — ⚠ **yanlış atıf** (M.1) |
| **D-075/V4** | *"replication … is more important … than increasing the population size"* | Kofler & Schlötterer 2013, **birebir alıntı, ölçülmüş** |

⚠ **Ama bunlar aynı ekseni konuşmuyor.** Kofler'in ekseni *tekrar sayısı vs
popülasyon boyutu*; DR'nin ekseni *popülasyon boyutu vs nesil sayısı*.
Üç eksen var: **tohum · N · G**.

⇒ **Doğrudan çelişki değil, ama DR'nin dayanağı çürük ve Kofler'inki ölçülmüş.**
Birleştirilmiş yön: **tohum > N > G**. ⚠ Bu da §5'in G çıtasıyla çarpışıyor
(M.3) ⇒ **üç eksenin dengesi bir tasarım kararıdır ve literatür bizim
ölçeğimiz için vermiyor.**

## M.5 ✅ Gerçekten değerli üç şey

1. **⭐ S4 çözüldü: Price eşitliği.** D-075'te açtığım totoloji borcunun
   yerleşik cevabı bu. Değişimi **Cov(w, z)** (seçilim) + **E(w·Δz)** (aktarım
   sapması) diye ayırıyor ⇒ uygunluk (`w`) seçilimi sürüklerken, **sabit yaşta
   okunan drift vektörü (`z`)** sonuç ölçütü olarak kalabiliyor. Bizim K5
   kararımız (landmark drift) tam olarak `z` rolüne oturuyor.
   ⚠ **Ön koşul:** `w` değişken olmalı — yani gerçek üreme farkı gerekiyor.
2. **⭐ S3'ün adı: SUTVA ihlali / kısmi girişim.** Hudgens & Halloran 2008
   doğrulandı ve konuya birebir. **D-075'in bağımsız olarak vardığı sonuçla
   aynı yere çıkıyor:** kol başına ayrı havuz, SUTVA'yı korur.
   ⚠ Ve **bedelini** de söylüyor (Chevin 2011): izolasyon, seçilim iddiasını
   birey düzeyinden **grup düzeyine** kaydırır.
3. **Turnuva seçilimi (k=2)**, kesme seçilimine karşı: küçük N'de çeşitliliği
   koruma gerekçesi Goldberg & Deb'in **gerçekten** olduğu yer.
   ⚠ Vallinder & Hughes 2024'ün (D-075/V3) kesme seçilimi kullandığını not
   et — yayımlanmış en yakın analog, DR'nin önerdiğinin **tersini** yapıyor.

## M.6 Karara hazır olanlar / olmayanlar

**Karara hazır:** ayrı havuz (iki bağımsız kaynak aynı yerde) · Price
eşitliğinin `w`/`z` ayrımı · turnuva vs kesme tartışmasının çerçevesi.

**Karara hazır DEĞİL:** N/G/tohum dengesi (M.3+M.4) · birikimli kalıtım çıtası
(hâlâ sayı yok; D-075 de verememişti) · Bedau atfı kırık olduğu için
çeşitlilik/aktivite ölçütleri.

---

# §N — Özdeş ajanlar arasında heterojenlik (yerel tarama, 2026-08-14)

⚠ **DR raporu DEĞİL.** Brief #7
(`2026-08-14_heterogeneity-among-identical-agents_PLAIN.txt`) gönderilemedi:
Gemini *"ben bir dil modeliyim, bu beceriye sahip değilim"* deyip kotayı
çıktısız tüketti. ⚠ **#6 cevaplanmıştı** ⇒ artık kontrollü bir karşılaştırma
var; farklar §N.3'te.

**Yöntem:** D-069/D-075'in aynısı — her kimlik Crossref/arXiv'den **açılarak**
doğrulandı. ⚠ Bu turda **yeni bir işaret** kullanılıyor: bir iddianın kaynağın
**neresinde** geçtiğini gösteremediysem öyle yazıyorum (D-076'nın yakaladığı
*"doğru kimlik, yanlış iddia"* kusuru için).

## N.0 Doğrulanan kimlikler

| # | Kaynak | Kimlik | Durum |
|---|---|---|---|
| W1 | Schönfisch & de Roos 1999, *Synchronous and asynchronous updating in cellular automata*, BioSystems 51:123–143 | `10.1016/s0303-2647(99)00025-8` | ✅ kimlik |
| W2 | Fatès 2014, *A guided tour of asynchronous cellular automata* | `arXiv:1406.0792` | ✅ kimlik + özet |
| W3 | Suleiman, Rapoport & Budescu 1996, *Fixed position and property rights in sequential resource dilemmas under uncertainty*, Acta Psychologica 93:229–245 | `10.1016/0001-6918(96)00008-x` | ✅ kimlik |
| W4 | Bru, Cabrera, Capra & Gomez 2003, *A Common Pool Resource Game with Sequential Decisions and Experimental Evidence*, Experimental Economics 6:91–114 | `10.1023/A:1024209010570` | ✅ kimlik |

## N.1 ⭐ S2 — sıralı erişimde konum etkisi **ölçülmüş**, ve önerimi zorluyor

**W3 (insan deneyi):** sıralı kaynak ikilemlerinde bir **konum etkisi** var —
talep ile sıradaki konum ters orantılı (*"erken davranan avantajı, geç kalan
dezavantajı"*). Suleiman ve ark. konumun **nasıl dağıtıldığını** manipüle
ediyor: hak edilmişlik yüksekken (açık artırma / sınav puanı) konum etkisi
**dönen konumlardakiyle aynı biçimde** görülüyor; konumlar **rastgele**
dağıtıldığında etki **belirgin biçimde azalıyor**.

⚠ **Bu, P0(d) önerimi olduğu gibi bırakmıyor.** Ben *"sıra dönsün, konum
kalıcı avantaja dönüşmesin"* demiştim. W3'e göre **dönen konumlarda da** etki
gözleniyor.

⚠ **Aşağıdaki benim çıkarımım, W3'ün bulgusu değil:** dönen sırada her ajan
her konumu işgal ettiği için **birikimli** maruziyet eşitlenir; geriye kalan,
durumun (enerji, drift, anı) **doğrusal olmayan** biriktiği için ortaya çıkan
yörünge ayrışmasıdır — ki aradığımız simetri kırılması **tam olarak budur**.
Yani konum etkisi bizde bir kusur değil, **mekanizmanın kendisi** olabilir;
kusur olan, onun **kalıcı** hâle gelmesi.

**W4:** sıralı CPR oyununda stratejik olarak **ilgisiz** parametreler bile
davranışı değiştiriyor, ve tahminden fazla işbirliği gözleniyor.

⚠ **İkisi de insan deneyi.** LLM ajanlarına taşınması **analoji**; ve W3'ün
mekanizması *"hak edilmişlik algısı"* — bizim ajanlarımızda böyle bir algının
karşılığı olup olmadığı **bilinmiyor**.

## N.2 S1 — güncelleme sırası nötr bir uygulama ayrıntısı **değil**

**W1/W2:** hücresel otomatlarda eşzamanlı (synchronous) ve eşzamansız
(asynchronous) güncelleme **temelde farklı** dinamikler üretiyor; eşzamansız
güncelleme literatürü bunun için ayrı bir alan.

⇒ **Bu, önerimin çerçevesini düzeltiyor.** Sıralı erişimi *"aksiyoma uygun,
hafif bir mekanizma"* diye sunmuştum. Literatür güncelleme sırasını **birinci
sınıf bir modelleme kararı** sayıyor — yani P0(d) bir uygulama detayı değil,
**fizik kararı**dır ve ön-kayıtta öyle ilan edilmeli.

⚠ *"Sabit süpürme (fixed sweep) düzeni dinamiğe istenmeyen yapı sokar"*
iddiası ikincil bir özetten geldi; **birincil kaynakta yerini gösteremedim**
⇒ **kullanılmıyor**, yalnız not ediliyor.

⚠ **Uzamsal gömme** (ALife'ın muhtemel standart cevabı): arama bunu
destekleyen genel ifadeler döndürdü ama **tek bir doğrulanmış kaynağa
bağlayamadım** ⇒ bu turda **cevapsız**.

## N.3 ⚠ #6 cevaplandı, #7 cevaplanmadı — fark ne

Kontrollü karşılaştırma: aynı hesap, aynı düz metin biçimi, aynı uzunluk
mertebesi.

| #6 (cevaplandı) | #7 (reddedildi) |
|---|---|
| Kaynak + kanıt türü + uyum istiyordu | ⭐ ek olarak **iddianın kaynağın neresinde geçtiğini** istiyor |
| Sicil bölümü kısa | Sicil bölümü **daha uzun ve daha sert** (*"kaynak uydurma"*, *"yeni kusur türü"*) |

⇒ **Hipotez (kanıt değil):** #7'nin doğrulama şartı tarayıcısız bir modelin
karşılayamayacağı bir şart, ve dürüst cevabı *"yapamam"* oluyor. ⚠ Sınanabilir:
sicil bölümü ve *"neresinde geçtiğini yaz"* şartı çıkarılıp gönderilir; cevap
gelirse sorun içerikte, gelmezse ürün/hesap tarafında.

## N.4 Cevapsızlar

1. **Uzamsal gömme** — doğrulanmış kaynağa bağlanamadı.
2. **S3: birikimli kalıtım çıtası.** ⚠ **İkinci bağımsız denemede de sayı
   çıkmadı** (DR #6 ve bu tarama). ⇒ Artık bunu bir **bulgu** saymak makul:
   *yerleşik bir çıta yok*, ve G bizim kendi gerekçemizle seçilip ön-kayıtta
   **ilan edilmiş bir seçim** olarak yazılmalı.
3. **S4: üç eksenli denge.** Simülasyon deney tasarımı literatürü *"tekrar mı
   koşu uzunluğu mu"* çerçevesini ve ortak rastgele sayı gibi varyans azaltma
   tekniklerini veriyor; **bizim ölçeğimiz için sayı vermiyor**.

## N.5 Claude Code'un okuması (karar Yasin'in)

1. **P0(d) hâlâ en iyi aday ama çerçevesi değişti:** bir uygulama ayrıntısı
   değil, **ilan edilmesi gereken bir fizik kararı** (N.2).
2. **Sıra dönmeli** — ama gerekçe *"konum etkisini yok etmek"* değil (W3 onu
   yok etmiyor), **kalıcı olmasını engellemek**.
3. **Konum etkisinin kendisi ölçülmeli**, bastırılmaya çalışılmamalı: pilotta
   konum ile `F_agent` arasındaki ilişkiye bakılır. ⚠ Kol farkına değil —
   L9 sınırı geçerli.

---

# §O — DR brief #7 mutabakatı: özdeş ajanlar arasında heterojenlik (2026-08-14)

**Ham cevap:** `docs/research/2026-08-14_DR7-answer-raw.md` (değiştirilmeden).
**Brief:** `2026-08-14_heterogeneity-among-identical-agents_PLAIN.txt`.
**Kayıt:** D-080. **Karşılaştırma:** aynı dört soruyu ben de taradım → **§N**.

⚠ **§N.3'ün hipotezi düştü.** Orada *"#7'nin 'neresinde geçtiğini yaz' şartı
tarayıcısız bir modelin karşılayamayacağı bir şart"* diye yazmıştım ve cevap
gelmemesini buna bağlamıştım. **Cevap geldi ve şartı karşılamaya çalıştı.**
⇒ hipotez **desteklenmedi**. (Cevabı hangi hesabın/aracın ürettiğini
bilmiyorum; iç kaynak indeksi `[22] [39] [51] [56] [58] [63] [69]` biçiminde
geldiği için erişimli bir derleme koştuğu anlaşılıyor.)

---

## O.0 Kimlik doğrulaması — **iki hata**, ikisi de tamir edildi

Her kimlik Crossref/arXiv'den **açılarak** kontrol edildi.

| # | DR ne yazdı | Açınca ne çıktı | Durum |
|---|---|---|---|
| 1 | Schelling (1971), J. Math. Sociol., **"no DOI"** | ✅ var: `10.1080/0022250X.1971.9989794` · *Dynamic models of segregation* · 1(2):143–186 | ⚠ **kimlik doğru, "DOI yok" yanlış** |
| 1b | `[56]` *"via JASSS"* · `[22]` Gilbert (2002, Agent 2002) | `[56]` **hangi makale olduğu belirsiz** (kaynakça verilmedi) · Gilbert 2002 Crossref'te yok (konferans bildirisi), **açamadım** | ❌ **kimliksiz** |
| 2 | **Nishimura ve ark. (2024)**, `arXiv:2308.00179` | **Anwar & Georgalos**, *Position Uncertainty in a Sequential Public Goods Game: An Experiment* · Exp. Econ. 27:820–853 · `10.1007/s10683-024-09831-3` | ❌ **yanlış yazar**, arXiv no doğru ⇒ **tamir edildi** |
| 3 | Bru ve ark. (2003), `10.1023/A:1024209010570` | ✅ *A Common Pool Resource Game with Sequential Decisions…* · Exp. Econ. 6(1):91–114 | ✅ (= §N'in **W4**'ü) |
| 4 | **Rafferty ve ark. (2009)**, *CogSci/J. AI Research*, `arXiv:0810.3070` | **Barczy & Pap**, *alpha-Wiener bridges…*, Stochastic Analysis and Applications 28:447–466 — **konuyla hiçbir ilgisi yok** | ❌ **tamamen yanlış makale** ⇒ doğrusu bulundu: **Rafferty, Griffiths & Klein (2014)**, *Analyzing the Rate at Which Languages Lose the Influence of a Common Ancestor*, Cognitive Science 38(7):1406–1431, `10.1111/cogs.12112` |
| 5/6 | Lee ve ark. (2015), JASSS 18(4):4, `10.18564/jasss.2897` | ✅ *The Complexities of Agent-Based Modeling Output Analysis* · Lee, Filatova, Ligmann-Zielinska ve ark. | ✅ |

⇒ **Sekizinci ve dokuzuncu kimlik hatası** projenin sicilinde. ⚠ Ama ikisi de
**tamir edilebilir** çıktı: birinde numara doğru yazar uydurma, diğerinde
numara başka bir makaleyi gösteriyor ama tarif edilen makale **gerçekten var
ve iddia orada**.

---

## O.1 ⭐ "Neresinde geçiyor" şartı **işe yaradı** — ve yakaladığı şey bu

**Yerini gösterebildiklerim: 6 iddianın 4'ü.** (#6'da bu oran **0/13**'tü —
13 satırın hepsi *"Tam Uyumlu"* çıkmıştı ve ayırt etme yoktu.)

⭐ **Asıl kazanç şu:** şart hataları **engellemedi**, ama **yakalanabilir**
hâle getirdi. İlk kez iddiayı kendi alıntısının **yanına koyup**
karşılaştırabildim — ve **altı iddianın üçü kendi alıntısının söylemediği bir
şey söylüyor.** ⚠ Yalnız DOI doğrulamasıyla (D-076 öncesi rejim) **üçü de
geçerdi**.

| # | İddia | Kimlik | Yer | Alıntı iddiayı taşıyor mu | **Karar** |
|---|---|---|---|---|---|
| 1 | Uzamsal gömme özdeş ajanları ayrıştırır (Schelling) | ⚠ kısmi | ❌ yalnız ikincil metinlerde, biri kimliksiz | — | **kullanılmıyor** (mekanizma ayrıca not edilir) |
| 2 | Sıralı erişim sıra etkisi yaratır | ❌→tamir | ✅ **iki alıntı da birebir bulundu** | ⚠ **kısmen** | **ikiye bölündü** — bak O.2 |
| 3 | Sıra etkisi rastgeleleme/rotasyonla giderilir (Bru) | ✅ | ⚠ ödemeli, açamadım | ❌ **hayır** | **brief yanılmış** |
| 4 | Birikimli evrim için sabit nesil sayısı yok; O(n log n) | ❌→tamir | ✅ **özette birebir** | ⚠ **yorum kaymış** | **alınır, çerçevesi düzeltilerek** |
| 5 | ABM için Monte Carlo tekrar şart | ✅ | ✅ **birebir, §1.3** | ✅ alıntı doğru | **uyumlu** ⚠ ama **uyarlaması yanlış** — bak O.3 |
| 6 | Aşırı tekrar "absürt" hassasiyet üretir | ✅ | ✅ **birebir, §2.2** | ✅ | **uyumlu** |

---

## O.2 ⭐ İddia 2 — alıntılar gerçek, **iddia iki ters bulguyu birleştirmiş**

Makaleyi (Anwar & Georgalos 2024) **açıp okudum**. DR'nin iki alıntısı da
**birebir var**:

- s.6: *"This literature has identified significant ordering effects, even in
  the case where later subjects in a sequence could not observe past
  decisions"* — ve atıfları: **Rapoport ve ark. 1993; Budescu ve ark. 1995;
  Suleiman ve ark. 1996; Rapoport 1997**.
- s.6–7: *"They all find robust evidence of first movers contributing more
  than later movers"*.

⚠ **Ama DR'nin cümlesi bu ikisini birleştirip üçüncü bir şey söylüyor:**
*"birinci hamle eden, davranışından bağımsız olarak avantaj kazanır — örneğin
daha çok katkı verir (ya da daha çok hasat eder)"*. Üç ayrı kusur:

1. **"first-mover advantage"** makalede **Varian (1994)**'e ait, **kuramsal**,
   ve orada birinci hamle eden avantajını **daha AZ katkı vererek**
   (bedavacılık) kullanıyor.
2. **"first movers contributing more"** ise **leading-by-example** yazınının
   **ampirik** bulgusu, **doğrusal kamu malı** oyunlarında — ve katkı
   **maliyetli** bir davranıştır, **avantaj değil**. İki bulgu **ters yönde**.
3. ***"ya da daha çok hasat eder"*** ifadesi kaynakta **hiç geçmiyor** —
   DR'nin bizim kurulumumuza uydurmak için eklediği köprü.

⇒ **Alınan:** *"sıralı protokollerde sıra etkileri belgelenmiştir"* ✅.
⇒ **Alınmayan:** *"birinci hamle eden davranıştan bağımsız avantajlıdır"* ❌.
⚠ Bu, P0'da ①'i zayıflatacak gibi görünen tek yeni iddiaydı; **kaynağında
yoktu**.

⭐ **İki bağımsız yol aynı yere çıktı.** O alıntının atıf listesi **Suleiman
ve ark. 1996**'yı içeriyor — §N'de kendi taramamda bulduğum **W3**. Bu,
D-065/J20 desenidir: iki bağımsız kaynak aynı birincil kaynağa varıyorsa delil
değeri taşır. (İkinci kesişme: **Bru 2003 = §N'in W4'ü**.)

⭐ **DR'nin atladığı, bizim işimize yarayan asıl bulgu:** makalenin **kendi
deneyi** konum **belirsizliği** üzerine ve *"increased cooperation under
positional uncertainty"* buluyor — ajanlar sıradaki konumlarını
bilmediklerinde işbirliği artıyor.
⚠ **Bizim için sınırlı ama gerçek:** bizim ajanlarımız konumlarını zaten
görmüyor (prompt'ta yok) ⇒ konum etkisinin **stratejik** bileşeni bizde
**yapı gereği kapalı**. Geriye kalan **mekanik** bileşen — tükenen havuzdan
önce alanın daha çok alması — ki **aradığımız simetri kırılması tam olarak
odur** (§N.1).

---

## O.3 ⚠ İddia 3 ve 5 — alıntı doğru olsa bile iddiayı taşımıyor

**İddia 3 (Bru 2003).** Makale ödemeli, alıntıyı **doğrulayamadım**. ⚠ Ama
**doğrulamaya gerek yok:** alıntının kendisi iddiayı taşımıyor.
*"The order of the **treatments** was changed in each **session**"* =
**koşulların sunuluş sırası** (öğrenme/yorulma etkisine karşı dengeleme).
İddia ise **ajan sırasını döndürmek**. Bir oturumda hangi *koşulun* önce
geldiği ≠ bir olayda hangi *ajanın* önce hasat ettiği. ⇒ **brief yanılmış**,
alınmıyor.
⚠ *"Rotasyon standart uygulamadır"* muhtemelen doğrudur ama **bu kaynakla
desteklenmemiştir**; ve §N/W3 zaten daha güçlüsünü söylemişti: **rotasyon
konum etkisini yok etmiyor**, yalnız kalıcı olmasını engelliyor.

**İddia 5 (Lee 2015).** Alıntı **birebir doğru** (§1.3, açıp buldum). ⚠ Ama
DR'nin uyarlaması **bizim kısıtımızı yanlış okuyor**: *"tekrarlanabilirlik
kısıtımız bu ilkeyi ihlal ediyor, tohum değiştiremeyiz"*. **Değiştirebiliriz.**
I0.6/D-037 *"aynı tohum + aynı kod aynı sonucu versin"* diyor — **farklı
tohumlarla koşmayı yasaklamıyor**. B2 zaten **40 farklı tohumla** koşuldu
(2004–2043).
⇒ **brief yanılmış**, ama ⚠ **kısmen bizim tarifimizden**: §1.1'de büyük
harfle *"TEKRARLANABILIRLIK ZORUNLU"* yazıp hemen ardından tek tohumlu bir
örnek vermiştik. **§9'un dersi dördüncü kez:** brief kalitesi girdi kalitesiyle
sınırlı, ve girdiyi biz yazıyoruz.

---

## O.4 İddia 4 — sayı doğru, **ölçtüğü şey iddianın söylediği şey değil**

Doğru makale: **Rafferty, Griffiths & Klein (2014)**, `10.1111/cogs.12112`.
Özette **birebir**: *"…results in convergence in a number of generations that
is on the order of n log n"* (n = ikili parametre sayısı).

⚠ **Ama makalenin ölçtüğü şey, ortak atanın etkisinin KAYBOLMASI** ve
dağılımın öğrenme önseline yakınsaması. *"Birikimli etki oluşması"* için
gereken süre **değil** — başlığı da bunu söylüyor: *"…Lose the Influence of a
Common Ancestor"*.

⇒ **Bizim için ters yönde ama daha kullanışlı:** n log n, atadan gelen izin
**ne kadar süre hâlâ görülebilir olduğunun** ölçeği. Küçük G'de ata etkisi
**henüz silinmemiş** demektir — yani küçük G, ata izini **aramak** için
elverişsiz değil, tersine tam da o pencerede.
⚠ **Bu benim çıkarımım, makalenin ifadesi değil.**

⇒ **§N Bulgu 3 güncelleniyor:** *"birikimli kalıtım için yerleşik bir çıta
yok"* **hâlâ geçerli** (üçüncü bağımsız denemede de sayı gelmedi). Yeni olan:
çıta yerine bir **ölçek** var ve *"küçük bir sabit değil"*. G'yi kendi
gerekçemizle seçip ön-kayıtta **ilan edilmiş bir seçim** olarak yazma kararı
**değişmiyor**; gerekçeye eklenecek bir dayanak çıktı.

---

## O.5 ⭐ P0'a etkisi — **öneri değişmiyor**, ama tabloya beşinci seçenek giriyor

1. **①'i zayıflatacak gibi görünen tek iddia (*"birinci hamle avantajı"*)
   kaynağında yoktu** (O.2). ⇒ ① **zayıflamadı**.
2. **Rotasyonun gerekçesi §N'deki hâliyle kalıyor:** *"konum etkisini yok
   etmek"* değil (W3 onu yok etmiyor, Bru onu desteklemiyor), **kalıcı
   olmasını engellemek**.
3. ⭐ **Yeni bilgi:** konum etkisinin **stratejik** bileşeni bizde yapı gereği
   kapalı (ajan konumunu görmüyor); geriye **mekanik** bileşen kalıyor — ki
   istediğimiz o.
4. **⑤ Uzamsal gömme** — §N.4'ün cevapsız #1'i **dolduruldu**, mekanizma
   gerçek (Schelling). ⚠ **Ama bizim P0 tablomuzda ①'in değil ②/③'ün yanına
   düşüyor:** Schelling'de farkı yaratan **başlangıçtaki rastgele yerleşim**
   ⇒ **fark yaşamaktan önce geliyor**. Ve DR'nin *"hiçbir kısıt ihlal
   edilmiyor"* değerlendirmesi **eksik**: ızgara boyutu, komşuluk yarıçapı,
   kaynağın uzamsal dağılımı = **en az üç yeni sabit**. ①'in ilan edilmiş
   üstünlüğü **sıfır yeni sabit**tı.

⇒ **Claude Code'un önerisi değişmedi: ①.** ⚠ **Karar hâlâ Yasin'in.**

---

## O.6 Süreç — brief #8 için iki düzeltme

1. ⭐ **Kaynakça istenecek.** Cevap iç indeks numaralarıyla geldi
   (`[22] [39] [51] [56] [58] [63] [69]`) ama **kaynakça verilmedi** ⇒ `[56]`
   hiçbir makaleye bağlanamadı ve iddia 1 bu yüzden düştü.
2. ⭐ **Satır numarası işe yaramıyor, birebir alıntı yarıyor.** DR *"lines
   249–253"* dedi, aynı cümleyi kendi çıkarımımda **313. satırda** buldum —
   satır numaraları hiçbir kopyada tutmuyor. **Bulmayı sağlayan şey birebir
   alıntıydı.** ⇒ #8'de *"bölüm adı **ve** birebir alıntı; satır numarası
   yazma"* denecek.

---

# §P — DR brief #8 mutabakatı: sabit kota mı, stoka bağlı hasat mı (2026-08-14)

**Ham cevap:** `docs/research/2026-08-14_DR8-answer-raw.md` · **kayıt D-082**
**Gönderim:** `_SHORT-A.txt` + `_SHORT-B.txt`, iki ayrı koşum (tam brief
gövdeye sığmadı). ⚠ **İlk deneme cevapsız dönmüştü** — araç konuyu hiç
görmemişti; kısaltma çözdü.

## P.0 ⭐ Baş sonuç: **türetmemiz doğrulandı, adıyla birlikte**

D-081'de çıkardığımız cebir literatürde **adı konmuş** bir sonuçmuş.
Azar, Lindgren & Holmberg 1996'nın makalesinin **başlığı** birebir bizim
sorunumuz: *"Constant quota versus constant effort harvesting"*.

- Bizim `d = 8.0` sabit hasadımız **constant quota** demekmiş.
- `H_MSY = rK/4` eşiği **standart** sonuçmuş.
- Ve alıntı bizim (d) adımımızı aynen söylüyor: *"there is no lower limit
  for the constant effort case, but constant quota harvesting is at the
  lower limit — any disturbance that decreases the population size leads to
  extinction."*

⇒ **Beş adımın hiçbiri çürütülmedi.** D-081'in *"kademeli kıtlık yok, kıtlık
anı var"* sonucu **sabit kota rejiminin bilinen bir özelliğiymiş**. Bu bir
kusur değil, seçtiğimiz hasat kuralının tanımı.

## P.1 Kimlik doğrulaması — **on bir kaynak açıldı**

| Kaynak | Durum |
|---|---|
| Azar, Lindgren & Holmberg 1996, *Constant quota versus constant effort harvesting*, Env. & Resource Economics **7:193–196**, `10.1007/BF00699291` | ✅ **birebir** |
| Hilker & Liz 2020, *Threshold harvesting as a conservation or exploitation strategy…*, Theoretical Ecology **13:519–536**, `10.1007/s12080-020-00465-8` | ✅ **birebir** |
| NRC 2010, *The Prevention and Treatment of Missing Data in Clinical Trials*, `10.17226/12955` | ✅ **birebir** |
| Rice 2008, *A stochastic version of the Price equation…*, BMC Evol. Biol. **8:262**, `10.1186/1471-2148-8-262` | ✅ **birebir** |
| Gomez 2018, `10.5287/ora-jv6j78zbd` | ⚠ **var ama Crossref'te değil** (DataCite/ORA). Başlık: ***Ghosts and bottlenecks in elastic snap-through*** — **elastisite tezi**, ekoloji değil. Alıntıdaki *"pull-in transition"* MEMS terimi |
| *"Maklakov & Chapman 2021"*, `10.1002/evl3.254` | ⚠ **YAZARLAR YANLIŞ** — gerçek: **Carlsson, Ivimey-Cook, Duxbury, Edden, Sales & Maklakov**. **Chapman yazar değil**; Maklakov **son** yazar. Makale ve başlık doğru |
| *"Ioannidis 2022, Adv. Theor. Simul. 5(1):2100182"*, `10.1016/j.mbs.2022.108782` | ⚠ **DERGİ VE MAKALE NO UYDURMA** — doğrusu ***Mathematical Biosciences* 345:108782**. Başlık/yazar/DOI doğru |
| *"Moher ve ark. 2010 (Lancet 375:1133–1143)"* | ⚠ **DERGİ VE SAYFA YANLIŞ** — CONSORT 2010 E&E = **BMJ 340:c869**, `10.1136/bmj.c869` |
| Siepe ve ark. 2024, ADEMP-PreReg | ⚠ **DOI verilmedi**; buldum: **`10.1037/met0000695`** (*Psychological Methods*), önbaskı `10.31234/osf.io/ufgy6`. ⚠ Yazar listesi de eksikti (Morris, Boulesteix, Heck atlanmış) |
| *"Atwood 2020, wildlife textbook"* | ❌ **KİMLİK YOK** — yazar+yıl dışında hiçbir tanımlayıcı verilmedi ⇒ **kullanılmıyor** |
| Földesi 2021, Rockland Immunochemicals | ⚠ **ticari firma blog yazısı**, literatür değil ⇒ iddiası ders kitabı düzeyinde doğru ama **kaynak olarak sayılmıyor** |

⇒ **Onuncu, on birinci, on ikinci kimlik hatası.** Hepsi **tamir edilebilir**
cinsten: doğru makale, yanlış künye. ⚠ Desen artık nettir — bu araçlar
**makaleyi buluyor, künyeyi uyduruyor**.

## P.2 Yer doğrulaması

**Açabildiğim tek tam metin: Rice 2008** (açık erişim, Europe PMC
`PMC2577117`). İddia **doğrulandı**: *"the expected change due to selection
in a very small population can be substantially larger than would be expected
from classical theory… the amplification of the selection differential decays
with increasing population size"*, ve **Şekil 1**'in başlığı *"Amplification
of expected selection differentials in small populations"*.
⚠ DR bunu *"section"* diye gösterdi; aslında **şekil başlığı + Sonuçlar
metni**. Küçük sapma, iddia gerçek.

⚠ **Azar 1996 ve Hilker & Liz 2020 ödemeli — alıntıları doğrulayamadım.**
Kimlikleri birebir ve alıntılar konularıyla tutarlı, ama **yerini
gösteremedim**; kuralımız gereği bunu **açıkça yazıyorum**.

## P.3 ⭐ Süreç kazanımı: **ilk kez bir boşluk ilan edildi**

Q3'ün ikinci yarısına DR şunu yazdı:

> *"(No specific claim found in sources – inference from population genetics
> theory.)"*

⭐ **Üç turdur istediğimiz şey tam olarak bu.** İlk kez bir iddia
*"kaynağım yok, bu benim çıkarımım"* diye işaretlendi. ⇒ *"gösteremezsen
gösteremediğini yaz"* şartı **çalışıyor**, ve kaynakça da eklendi
(D-080'in iki düzeltmesinden ikincisi tuttu).

## P.4 ⛔ DR'nin verdiği iki çıkış yolu — **ikisi de bizde çalışmıyor**

DR iki alternatif verdi ve ikisi de matematiksel olarak doğru:

1. **Constant effort** (hasat ∝ stok): `P* = (r−h)K/r`, `h < r` iken çöküş yok.
2. **Escapement / eşik hasadı** (Hilker & Liz): `T ≤ K` ise `T` **küresel
   çekici**, çöküş yok.

⚠ **Ama ikisi de bizim ihtiyacımızı öldürüyor, ve DR bunu göremezdi** —
çünkü bizim **karneye ihtiyacımız** olduğunu bilmiyor.

> **Constant effort'ta kıtlık *hiç* olmaz.** Herkesin hasadı `h·P` olarak
> tanımlıysa kimse **eksik almaz**; eksik alma yoksa **paylaştırılacak bir
> şey yoktur**; paylaştırma yoksa **sıralı erişimin tahkim edecek hiçbir şeyi
> kalmaz.** Çöküşü çözer, **mekanizmayı yok eder.**

Aynısı escapement için de geçerli: `T`'de dengelenen bir havuz herkese aynı
payı verir.

⇒ **İhtiyacımız olan üçüncü seçenek, ve DR onu atladı:** brief'in Q2'sinde
adı geçen **Holling tipi tepki fonksiyonu** — *talep sabit kalır (8.0), ama
**gerçekleşen** hasat stoka bağlıdır*. DR bu maddeye yalnız
*"Empirical studies of such functional responses are sparse"* dedi ve
geçti.

## P.5 ⭐ Kendi hesabım: Holling II bandı **üretiyor** (keşifsel)

`gerçekleşen_i = d·P/(h+P)`, `h = 2.0`, N=8, olay içinde **sıralı** erişim
(her ajandan sonra stok güncelleniyor). Kişi başı `K=100`, `P₀=0.8K`:

| olay | havuz/kişi | ilk ajan | son ajan | **fark** |
|---|---|---|---|---|
| 1 | 74.60 | 7.810 | 7.794 | **0.017** |
| **10** ⭐ | 36.62 | 7.654 | 7.596 | **0.058** |
| 15 | 14.33 | 7.320 | 7.071 | **0.250** |
| 18 | 0.56 | 5.660 | 2.414 | **3.246** |

**Sabit kotada aynı tablo:** olay 1–16 fark **tam sıfır**, olay 17'de
1.763 vs 0 (yedi ajan **hiç** alamıyor), olay 18'den sonra hepsi sıfır.

⇒ **Holling II, landmark'ta (olay 10) sıfırdan farklı ve tekdüze büyüyen bir
ayrışma veriyor**, hiç kimse sıfır almıyor, havuz bir uçurumdan düşmüyor.
⚠ **Ama landmark'taki fark 7.65 üzerinden 0.058 — yani %0.76.** Küçük.
Bugünkü durum **tam sıfır** (bit düzeyinde özdeş) olduğu için bu bir simetri
kırılmasıdır, ama **yeterli olduğu gösterilmedi**; pilotun işi.

⚠ **Ve rotasyonla çelişiyor:** sıra dönerse ajanlar konumları eşitler ve
landmark'taki fark daha da küçülür. §N.1'de yazdığım gerilim burada
**sayıya döndü**. 8 ajan, 10 olay ⇒ rotasyon **tamamlanmıyor**, artık fark
kalıyor — ama ne kadar, ölçülmedi.

## P.6 ⚠ Bize dokunan diğer bulgu: Price kestirimi küçük N'de **yanlı**

Rice 2008 (doğrulandı, P.2): çok küçük popülasyonlarda beklenen seçilim
farkı klasik kuramın öngördüğünden **sistematik olarak büyük** çıkıyor, ve
bu **büyütme** N arttıkça sönüyor.

⇒ ⚠ **Bizim `Cov(w, z)` kestirimimiz küçük N'de yalnız gürültülü değil,
şişkin olabilir.** D-076'nın getirdiği Price eşitliği bu uyarıyla birlikte
okunmalı ve **ikinci ön-kayıta sınır olarak yazılmalı**.

## P.7 Q1'in cevaplanmayan yarısı

Kritik yavaşlama için *"how many events, how does it scale with the excess"*
diye **sayı sormuştum**; DR olguyu doğruladı ama **ölçekleme yasası
vermedi**, ve dayanağı bir **elastisite tezi** (P.1). ⇒ *"talebi MSY'nin
hemen üstüne koyup uzun bir geçiş bandı elde etme"* seçeneği **hâlâ
sayısız**. ⚠ Zaten kırılgan bir seçenek: `d`'yi `rK/4`'e ayarlamak, sabiti
sonuca göre seçmenin **en uç** hâli olurdu.

## P.8 Yöntem soruları — alınanlar

| İddia | Karar |
|---|---|
| *"fixed study time"* / *"fixed event time"* ayrımı (NRC 2010) | ✅ **kullanılabilir sözcük dağarcığı** — bizim landmark'ımız *fixed study time* |
| Ölçümden önce ölüm = **rekabet eden risk**, rastgele sansür sayılamaz | ✅ K1–K3'ün gerekçesini dışarıdan destekliyor |
| Bilgilendirici ölüm dışlanmamalı (Carlsson ve ark. 2021) | ✅ yön uyumlu ⚠ künye yanlıştı (P.1), yer doğrulanamadı |
| **Sabit yaşta birincil + açılış-sonrası oran ikincil** | ⭐ **doğrudan işimize yarıyor** — K1 zaten *"landmark + olay-başına oran"* diyordu; DR bunu bağımsız olarak öneriyor |
| Simülasyon ön-kaydı şablonu (Siepe ve ark. 2024, `10.1037/met0000695`) | ⭐ **ikinci ön-kayıt için doğrudan kullanılabilir** ⚠ künyesini ben tamamladım |
| **Pozitif kontrol** benzetmesi | ⚠ **kaynağı geçersiz** (firma blogu) ama kavram gerçek ⇒ P0-b'nin savunması için **daha iyi bir kaynak gerekiyor** |

## P.9 Claude Code'un okuması (karar Yasin'in)

1. **D-081 çürütülmedi, adlandırıldı.** Sabit kota = uçurum, bu bilinen bir
   özellik.
2. **DR'nin iki çıkışı da mekanizmayı öldürüyor** (P.4) — kabul edilemez.
3. ⭐ **Holling II üçüncü yol ve tek çalışanı** (P.5): talep sabit kalır,
   gerçekleşen hasat stoka bağlanır. **Ortamın özelliği**, karar kuralının
   değil ⇒ K7'yi ve aksiyomu **ihlal etmiyor**. Ve `metabolic_gain` zaten
   **aynı fonksiyon ailesini** kullanıyor (D-066/J9) — evrende ikinci bir
   sabit ailesi açmıyor.
4. ⚠ **Bedeli:** yeni bir sabit (`h`) girer, ve `h`'nin değeri **P0-b'nin
   kapasite sorusunun yerini alır** — sorun kaybolmuyor, yer değiştiriyor.
5. ⚠ **Landmark'taki fark %0.76** ve rotasyon onu küçültüyor. **Pilotun ilk
   sorusu bu olmalı.**

---

# §Q — DR brief #9 mutabakatı: ön-kayıtlı uç nokta pilotta ölçülemez çıkarsa (2026-08-18)

**Brief:** *"Revising a pre-registered primary endpoint after a pilot shows the
endpoint cannot be measured, without turning the change into post-hoc
selection."* Dört soru (Q1 uç nokta revizyonu · Q2 pozitif kontrol · Q3 nadir
olayda örneklem · Q4 *"etki yok"* ile *"uç nokta duyarsız"* ayrımı).
⚠ **Hedef değişti:** Gemini DR çalışmadığı için **ChatGPT Deep Research**
kullanıldı. Yapı farklı ve **bu iş için daha iyi çalıştı** (aşağıya bak).

## Q.0 ⭐ Kaynak sicili — bu kanalda **ilk kez sıfır kimlik hatası**

Beş kaynağın beşi Crossref/arXiv'den **doğrulandı**: Evans 2007
(`10.1371/journal.pctr.0020018`) · Harris ve ark. 2020
(`10.3389/fpsyg.2020.00605`) · Haynes ve ark. 2021 (`10.21105/joss.03118`) ·
McGrath & Burke (`arXiv:2109.02516`) · Dienes 2014
(`10.3389/fpsyg.2014.00781`).

⭐ **Ve alıntılar kaynakta var.** Evans'ın *"independent of the data"* ve
*"cherry-picking"* cümlelerini, Harris'in *"sensitive to variation… novices and
experts"* cümlesini birebir buldum. ⚠ Bu, **D-076'nın yakaladığı kusur türünün
(doğru kimlik, yanlış iddia) bu turda çıkmadığı** anlamına gelir — ve onu
yakalayan şey **DOI değil, S2'nin birebir alıntı şartıydı**.

⇒ **D-080 ve D-082'de eklediğimiz iki süreç şartı ilk kez eksiksiz tuttu:**
kaynakça verildi, satır numarası yerine alıntı verildi, ve **boşluk ilan
edildi** (*"Harris 'positive control' terimini kullanmıyor"* — teyit ettim,
doğru).

⚠ İki eksik künye, kimlik hatası **değil**: Harris ve ark. **beş** yazarlı
(Samuel J. Vine atlanmış) · McGrath & Burke'ün *"2024"*ü yayın yılı değil **v4
tarihi** (arXiv'e 2021-09-06'da girmiş).

## Q.1 Mutabakat tablosu

| # | Rapor ne diyor | Kod/tasarım ne yapıyor | Karar |
|---|---|---|---|
| 1 | Uç nokta değişikliği **veriden bağımsız** olmalı; bağımsız kurul, körlük açılmadan (Evans) | ⚠ **Brief eksik sordu.** Evans *koşum ortasını* anlatıyor. Kilitli ön-kayıt tek soy çalışmasınındı, **bitti ve null raporlandı**; ikinci ön-kayıt **taslak**; B1 **pilot** (JSON'un ilk alanı: *"exploratory, not pre-registered"*) | **uyumlu** — pilottan uç nokta seçmek pilotun görevidir. ⭐ Evans'ın soyut şartının bizdeki karşılığı **zaten var**: §6 tohum yakma |
| 2 | Cherry-picking tip-1 hatasını şişirir (Evans) | §2.7 + L9 aynısını söylüyor | **uyumlu**; iki reddi dışarıdan doğruluyor: travma eşiğini indirme · ömrü sonradan uç nokta yapma |
| 3 | Construct validity = *"gerçekten farklı olanı ayırt edebilme"* (Harris) | ⚠ **DR fazla genelledi** ve kendisi itiraf etti. Harris simülasyonu **gerçek dünyaya** karşı doğruluyor; bizde referans yok | **kısmen uyumlu** — kullanılabilir kısım *simülasyonun gerçekçiliği* değil **aletin duyarlılığı** |
| 4 | Kesinlik temelli örneklem, etki varsaymadan (Haynes) | Doğrudan uygulanabilir; B1 oranı verdi | **uyumlu ve kullanılabilir** — P7-a'nın sorusunu değiştiriyor |
| 5 | Çok küçük p'de küçük n sıfır olay verir (McGrath & Burke) | p ≈ 0.042; onların örneği 10⁻⁵ | **uyumlu ama marjinal** |
| 6 | Anlamsızlık ≠ etki yok; TOST / Bayes faktörü (Dienes) | ⛔ **P7-b ile çarpışıyor** (ilk koşum kestirimdir) ve TOST *"en küçük anlamlı etki"*yi önceden isimlendirmeyi şart koşuyor — **DR #1'in cevaplanmamış sorusu** | **uyumlu ama kapalı bir kararı açıyor** |
| 7 | Q2'nin çekirdeği (çalışmanın etkisine bakmadan pozitif kontrol) | Harris vermiyor, DR de veremedi | **boşluk, ilan edilmiş** |

## Q.2 ⭐ Bu turun bulduğu gerçek boşluk — alet değil, evren

Harris'in fikrini kodda aradım:

- **Birim düzeyinde pozitif kontrol ZATEN VAR:** `test_drift.py` 0.69'da drift
  yazılmadığını, **0.70'te yazıldığını** tutuyor; `test_cprime_multigen`
  landmark okuyucusunun `z` ürettiğini tutuyor.
- **Sistem düzeyinde YOK:** bugüne kadar hiçbir koşum, **canlı bir ajanın
  10. olaydan önce 0.7 eşiğini geçtiğini** düzenli biçimde göstermedi.

⇒ **Alet çalışıyor; evren o girdiyi üretmiyor.** D-109'da *"uç nokta bozuk"*
diye okunabilecek ifade böylece daraltıldı.

## Q.3 P7-a yeniden tanımlandı — saat değil **kesinlik**

B1'in kendi sayısı: landmark'ta `z` dolu olan **ajan-nesli 3/72 = %4.2**.
Wald yaklaşımıyla (`n = z²p(1−p)/h²`):

| yarı-genişlik | gereken ajan-nesli | B1 hızında |
|---|---|---|
| ±0.05 | **61** | ~1.1 sa |
| ±0.03 | **170** | ~3.0 sa |
| ±0.02 | **383** | ~6.7 sa |

⚠ **Bu yalnız ORANI kestirir.** Kollar arasında nadir bir olayın farkını
görmek kat kat fazlasını ister; o hesap ayrıdır ve yapılmadı.
⚠ Wald aralığı küçük p'de zayıftır (McGrath & Burke'ün konusu) — kesinleşecekse
Wilson ya da tam aralık kullanılmalı.

## Q.4 Alınmayanlar

- **Dienes'in TOST'u şimdi alınmadı:** *"en küçük anlamlı etki"* isimlendirmeden
  uygulanamaz ve o değer §2.7 gereği kalibrasyon ister. **Yasin'in kararı.**
- **Harris'in "gerçek dünyaya karşı doğrulama"sı alınmadı:** karşılığı yok.
- **DR'ye *"hangi uç noktayı seçelim"* sorulmadı** (bilerek, §9/D-007) ve DR de
  önermeye kalkışmadı — brief'in *"NOT asking"* bölümü işini yaptı.

## Q.5 Süreç dersi

⭐ **Üç turdur eklenen şartların üçü de bu turda meyve verdi:** DOI (D-065),
birebir alıntı (D-080), kaynakça + boşluk ilanı (D-082). Sonuç: **doğrulaması
en kolay, hatası en az DR turu.**
⚠ **Ama şart listesi kusuru engellemiyor, yakalanabilir kılıyor** — 3 numaralı
satırdaki aşırı genelleme yine de geçti, ve onu yakalayan şey **kodun kendisiydi**
(§2.2: belgeye değil dosyaya güven).

---

# §R — **Yerel tarama: ortak şok bir uç noktayı eşitlerken ne yapılır** (2026-08-18, D-119)

⚠ **Bu bir DR mutabakatı DEĞİL.** DR #10 gönderildi ama cevabı gelmedi. Bu
bölüm, cevabın **çapraz kontrolü** için önceden yapılmış yerel taramadır —
D-069 (§K) ve D-075 (§L) ile aynı desen, ve o desen bu projede üç kez DR
hatası yakaladı.

⚠ **Sistematik derleme değil.** Adaylar benim bildiklerimden çıktı, hepsi
**Crossref'ten doğrulandı**, ve *"kaynağın kimliği"* ile *"kaynağın iddiayı
taşıdığı"* ayrı tutuldu.

## R.0 ⭐ Doğrulama ilk iş yapıldı ve **iki kendi hatamı** yakaladı

| verdiğim DOI | gerçekte ne | doğrusu |
|---|---|---|
| `10.1086/285447` (Goodnight ve ark. 1992 sanıyordum) | **Stevens 1992**, yükselti gradyanı — aynı dergi, aynı yıl, **komşu numara** | ✅ `10.1086/285438` |
| `10.1016/j.jtbi.2008.03.008` (Rice 2008 sanıyordum) | **Chattopadhyay ve ark.**, plankton | ✅ `10.1186/1471-2148-8-262` |

⇒ **DR'yi suçladığımız hata biçiminin ikisi de bende çıktı** (*"makaleyi
biliyor, künyeyi uyduruyor"*). Doğrulanmamış hiçbir kimlik kullanılmadı.

## R.1 Doğrulanmış kimlikler (9/9 Crossref'ten)

| kaynak | DOI | nereye bakıyor |
|---|---|---|
| Heisler & Damuth 1987, *Am Nat* | `10.1086/284732` | **contextual analysis** — hiyerarşik popülasyonda seçilim ayrıştırması |
| Goodnight, Schwartz & Stevens 1992, *Am Nat* | `10.1086/285438` | contextual analysis'in grup seçilimi modellerine uygulanışı |
| Queller 1992, *Am Nat* | `10.1086/285343` | nicel genetik ↔ kapsayıcı uygunluk ↔ grup seçilimi köprüsü |
| Rice 2008, *BMC Evol Biol* | `10.1186/1471-2148-8-262` | Price'ın **stokastik** sürümü (küçük N borcu buradan) |
| Kruuk 2004, *Phil Trans R Soc B* | `10.1098/rstb.2003.1437` | animal model — **ortak çevre varyansı** ayrı bileşen olarak |
| Enders & Tofighi 2007, *Psych Methods* | `10.1037/1082-989X.12.2.121` | **grup-içi merkezleme** (group-mean centering) |
| Pesaran 2006, *Econometrica* | `10.1111/j.1468-0262.2006.00692.x` | panelde **ortak faktör** yapısı |
| ⭐ Montgomery, Nyhan & Torres 2018, *AJPS* | `10.1111/ajps.12357` | **müdahale-sonrası değişkene koşullanma** |
| ⭐ Cinelli, Forney & Pearl 2022, *Sociol Methods Res* | `10.1177/00491241221099552` | *"iyi ve kötü kontroller"* |
| Elwert & Winship 2014, *Annu Rev Sociol* | `10.1146/annurev-soc-071913-043455` | collider / içsel seçilim yanlılığı |
| Evans 2007, *PLoS Clin Trials* | `10.1371/journal.pctr.0020018` | uç noktanın koşum başladıktan sonra değişmesi (D-110'da zaten kullanıldı) |
| Thabane ve ark. 2010, *BMC Med Res Methodol* | `10.1186/1471-2288-10-1` | pilot çalışma metodolojisi |
| Temple & Ellenberg 2000, *Ann Intern Med* | `10.7326/0003-4819-133-6-200009190-00014` | **assay sensitivity** — *"çalışma bir farkı görebilir miydi"* |

## R.2 ⛔⛔ Turun en önemli bulgusu — **D seçeneği literatürde adı konmuş bir tuzağa değiyor**

Montgomery, Nyhan & Torres 2018'in **özeti** (Crossref'ten, birebir):

> *"…controlling for posttreatment variables in statistical models,
> eliminating observations based on posttreatment criteria, or **subsetting
> the data based on posttreatment variables**."*

⚠ **Bizim durumumuz tam buraya oturuyor:** kriz, ajanların **kendi hasat
davranışından** doğuyor; davranış adapter'dan (yani **koldan**) etkileniyor
⇒ kriz **müdahale-sonrası** bir olaydır. `z`'yi *"kriz kaynaklı kısmı hariç"*
diye yeniden tanımlamak, **müdahale-sonrası bir ölçüte göre uç noktayı
budamak** olur.

⚠ **Ama birebir aynı değil, ve bunu abartmamak gerekiyor:** biz **hiçbir
yaşamı elemiyoruz** (örneklem budaması yok) ve regresyona kontrol
**eklemiyoruz**; uç noktanın **tanımını** daraltıyoruz. Literatürün bu üçüncü
biçime ne dediği **taramanın cevaplayamadığı yer** — ve DR #10'un **Q2'si tam
olarak bu.**

⇒ ⭐ **Bu bulgu D ile E arasındaki dengeyi E'ye kaydırıyor:** ayrıştırma
(contextual analysis deseni) hiçbir şeyi **atmıyor**, iki bileşeni de
**raporluyor**; budama ise atıyor. Ve ayrıştırmanın evrimsel biyolojide
**adı ve yerleşik formu var** (Heisler & Damuth 1987; Goodnight ve ark. 1992).

⚠ **İddia değil, yön:** kaynakların **kimliği** doğrulandı, **iddiayı
taşıdıkları** yalnız iki tanesinde (Montgomery, Cinelli — özetleri açıkça
söylüyor) doğrulanabildi. Heisler & Damuth'un contextual analysis'inin bizim
*"hücre-ortak bileşen"*imize uyup uymadığı **okunmadan iddia edilemez**.

## R.3 Soru bazında durum

| soru | yerel taramanın verebildiği | eksik kalan |
|---|---|---|
| **Q1** ad ve yordam | Dört ayrı gelenek var: contextual analysis (evrim) · ortak çevre varyansı (nicel genetik) · grup-içi merkezleme (çok düzeyli model) · ortak faktör (panel) | hangisi bizim *"hücre içinde sabit artım"* hâlimize **tam** oturuyor |
| **Q2** ne zaman geçersiz | ⭐ Müdahale-sonrası koşullanma **adı konmuş bir hata** (Montgomery 2018; Cinelli 2022) | uç nokta **tanımını** daraltmak da aynı sınıfa girer mi |
| **Q3** ayrıştırma | ✅ **Var ve adı var:** contextual analysis | küçük N'de (8 ajan, 2 epizod) güvenilirliği — Rice 2008 uyarısı bu yöne bakıyor |
| **Q4** pilottan sonra uç nokta | Evans 2007 (D-110'da alındı) + Thabane 2010 | sınır koşulları: pilot verisi ana analizden çıkar mı |
| **Q5** *"değişemezdi"* ilanı | **assay sensitivity** (Temple & Ellenberg 2000) kavramsal olarak tam karşılık | simülasyon/ABM literatüründe karşılığı var mı |

## R.4 DR #10 geldiğinde ne yapılacak

1. DR'nin kimliklerini **Crossref'ten** doğrula (bu turda benim iki hatam bu
   şekilde çıktı).
2. DR'nin verdiği alıntıları kaynakta **yerini göstererek** kontrol et.
3. ⭐ **Bu bölümle kesişimi ara:** DR bağımsız olarak contextual analysis'e
   ve müdahale-sonrası koşullanmaya çıkarsa, iki yol aynı yere varmış olur
   (D-065/J20 deseni). Çıkmazsa, **hangisinin eksik olduğu** sorusu açılır.
4. Ancak ondan sonra **uç nokta kararı** — ve karar **Yasin'in** (D-007).

---

# §S — **DR #10 mutabakatı** (2026-08-18, D-120) · ⛔ **cevap sağlam, ama sorduğumuz sistem yanlış tarif edilmişti**

**Kanal:** Gemini Deep Research (⚠ CLAUDE.md §9 *"ChatGPT DR"* diyordu; **bu tur
Gemini'ydi** — belge düzeltildi).

## S.0 Kaynak sicili — **beşin dördü temiz, biri 13. kimlik hatası**

| DR'nin verdiği | Crossref | karar |
|---|---|---|
| Price 1972, `10.1111/j.1469-1809.1957.tb01874.x` | ✅ **doğru** (1957'li dizge Wiley'nin eski numarası, gerçek) | alındı |
| Angrist & Pischke, `10.2307/j.ctvcm4j72` | ✅ doğru (kitap) | alındı |
| Eldridge ve ark. 2016, `10.1136/bmj.i5239` | ✅ doğru | alındı |
| Cinelli, Forney & Pearl, `10.1177/00491241221099552` | ✅ doğru | alındı |
| Enders & Tofighi 2007, `10.1037/1082-989X.12.2.121` | ✅ doğru | alındı |
| Pesaran 2006, `10.1111/j.1468-0262.2006.00692.x` | ✅ doğru | alındı |
| ❌ **Rothenberg 1971, `10.2307/1913258`** | **Kamien & Schwartz**, *Limit Pricing and Uncertain Entry* | ⛔ **düzeltildi: `10.2307/1913267`** |
| ⚠ Wooldridge 2010 / Lynch & Walsh 1998 | kitap, DOI verilmedi; **bölüm iddiaları doğrulanamadı** | yön olarak alındı, alıntı olarak **alınmadı** |
| ⛔ *"CONSORT 2025 Guidelines"* → **pozitif kontrol** satırının kaynağı | künye yok; CONSORT'un konusu bu değil | ⛔ **alınmadı** |
| ⛔ *"Standard Parameter Identification Theory"* bir kaynak olarak | kaynak değil, alan adı | ⛔ **alınmadı** |

⚠ **Desen tekrar etti:** hatalı DOI, doğru makalenin **komşu numarası**
(`1913258` ↔ `1913267`). Aynı desen bu turda **bende de** çıkmıştı (§R).

## S.1 ⛔⛔ Turun asıl bulgusu — **brief'imiz sistemi yanlış tarif etti**

Brief §2'de şunu yazdım:

> *"The crisis applies a fixed magnitude to EVERY agent of that arm at the
> SAME event. The magnitude is a constant, so **every agent receives an
> identical increment**."*

**Kod böyle demiyor** (`drift.py:58`):

```
new_magnitudes[domain] = current + magnitude * exp(-current / TRAUMA_DECAY_BASE)
```

⇒ Uygulanan artış **sabit değil**, ajanın **o anki drift'ine bağlı**. Ölçüldü
(`m = 1.0`, `TRAUMA_DECAY_BASE = 1.0`):

| `z` (kriz öncesi) | kriz sonrası | artış |
|---|---|---|
| **0.00** | 1.0000 | **1.0000** |
| 0.20 | 1.0187 | 0.8187 |
| 0.60 | 1.1488 | 0.5488 |
| 1.00 | 1.3679 | 0.3679 |

⇒ Harita **monoton** (türev ≥ 0, hiç ters dönmüyor) ama **sıkıştırıcı**: 0.20'lik
bir fark 0.0187'ye iniyor (**~10.7 kat**). ⚠ Ve türev **tam `z=0`'da sıfır** —
yani sıkıştırma en çok **ajanlarımızın yaşadığı yerde**.

⇒ ⛔ **DR'nin Q1 cevabının tamamı (TWFE · CWC · `c²` · CCE) "şok toplamsal ve
özdeş" varsayımına dayanıyor** ve bu varsayım **bizde tutmuyor**. DR'nin suçu
değil — **girdiyi biz yazdık.** Bu, *"brief kalitesi girdi kalitesiyle
sınırlıdır"* dersinin **dördüncü** örneği.

## S.2 ⭐⭐ Ve ölçüm, seçeneği tersine çevirdi: **D en kötüsü**

27 hücre (3 tohum × 3 kol × 3 nesil), `headroom_n8_g3_s3` checkpoint'inden:

| tanım | hücre içi **tek değer** (dejenere) |
|---|---|
| **bugünkü `z`** (iki kanal birlikte) | **14 / 27** |
| **seçenek D** (yalnız bireysel kanal) | ⛔ **en az 21 / 27** |

**Sebep, koddan:** bireysel kanal `magnitude ≥ 0.7` ile ateşleniyor ve
**landmark'tan (olay 10) önce neredeyse hiç ateşlenmiyor** ⇒ `z_before` çoğu
ajanda **tam olarak 0**. Kriz o sıfırları **hepsi 1.0** yapıyor; D seçeneği ise
**hepsi 0.0** yapıyor. **İkisi de dejenere**, ve D daha sık.

⇒ ⭐ **Sorun ortak şok değil.** Sorun: **bireysel kanal landmark'tan önce
yeterince ateşlenmiyor.** Kriz bilgi yok etmiyor, **olmayan bilgiyi
gizlemiyor** — sadece sabit bir değere taşıyor. Farklar **var olduğunda**
krize rağmen hayatta kalıyor (9904'te, her nesilde kriz olmasına rağmen bir
hücrede **4 farklı `z`**).

⚠ Bu, D-115'in *"herkese aynı şey oldu"* okumasını **daraltıyor**: doğru, ama
sebebi krizin gücü değil, **bireysel kanalın sessizliği**.

## S.3 Mutabakat tablosu

| # | DR ne diyor | kod/veri ne diyor | karar |
|---|---|---|---|
| 1 | Q1: ortak şoku TWFE/CWC/`c²`/CCE ile ayır | ⛔ hepsi **toplamsal özdeş şok** varsayıyor; bizim artış `m·e^{-z/B}` | **brief yanılmış** (bizim hatamız) ⇒ Q1 **uygulanamaz** |
| 2 | Q2: içsel şoku çıkarmak *bad control* / müdahale-sonrası koşullanma | ✅ kriz gerçekten içsel (ajan davranışından) | **uyumlu** — ve §R'de bağımsız olarak aynı yere varmıştım (**iki yol kesişti**) |
| 3 | Q2'nin *"sınanabilir ölçütü"* (`P(Z\|X)=P(Z)` d-ayrılığı) | Cinelli alıntısı **d-ayrılığın tanımını** veriyor, bu ölçütü değil | ⚠ **DR'nin kendi sentezi** — mantığı sağlam, **alıntısı taşımıyor** |
| 4 | Q3: Price'ın **çok düzeyli** ayrıştırması (gruplar arası + grup içi) | ⚠ Bizde kol başına **tek** popülasyon var; ihtiyacımız **hücre içi** ayrım | **kısmen uyumlu** — kimlik doğru, **bizim yapımıza doğrudan oturmuyor** |
| 5 | Q3: küçük N için **boşluk ilanı** | — | ✅ **doğru davranış**, D-110'un şartı yine tuttu |
| 6 | Q3: `Var_j(z)=0` ⇒ örnek kovaryansı **özdeş sıfır** | ✅ ölçüldü: 14/27 hücre | **uyumlu** |
| 7 | Q4: üç sınır koşulu (pilot verisi ayrı · ön-kayıt · **kol karşıtlığına bakmadan**) | ✅ üçü de zaten bizim disiplinimiz (L9, §2.7) | **uyumlu**, ikinci ön-kayıta yazılacak |
| 8 | Q5: **dejenere uç nokta ilanı** + **estimability** kontrolü + **pozitif kontrol** | analiz aracımız bugün *"Cov = 0"* yazıyor, *"tanımsız"* demiyor | ⭐ **alındı** — kod işi çıkardı |
| 9 | Q5'in pozitif kontrol satırının kaynağı *"CONSORT 2025"* | konusu bu değil, künye yok | ⛔ **kaynak alınmadı**, **fikir alındı** |

## S.4 Alınanlar

1. ⭐ **Dejenere uç nokta ilanı** — `Var(z) = 0` olan hücre *"sıfır seçilim
   ölçtük"* değil ***"bu hücrede seçilim tanımsız"*** diye raporlanacak.
   Dayanak: **Rothenberg 1971**, `10.2307/1913267` (yerel kimlik düzeltmesiyle).
2. ⭐ **Pozitif kontrol özelliği** — krizden bağımsız değişen bir nicelik
   (ör. `energy_mean_over_life`, ölçülen aralık 0.59–0.86) üzerinde
   `Cov(w, ·) ≠ 0` gösterilirse, seçilim motorunun **çalıştığı** ayrıca
   kanıtlanır. ⚠ Koşumdan **önce** ilan edilmeli, ve **Lamarckçı iddia değil**.
3. ✅ **Q4'ün üç sınır koşulu** ikinci ön-kayıta madde olarak girdi.
4. ✅ **Q2** bağımsız olarak §R ile kesişti ⇒ **D seçeneğinin nedensel riski
   iki yoldan doğrulandı**, ve ölçüm ayrıca onu **ampirik olarak** da eledi.

## S.5 Alınmayanlar

- **Q1'in dört yordamı** — varsayımı bizde tutmuyor (S.1).
- **d-ayrılık ölçütünün** alıntıya dayandırılması — sentez olarak not edildi.
- *"CONSORT 2025"* ve *"Standard Parameter Identification Theory"* künyeleri.
- ⚠ **Wooldridge/Lynch & Walsh bölüm alıntıları** — kitap, doğrulayamadım;
  yön olarak not, kanıt olarak **hayır**.

---

# §T — **DR #11 mutabakatı** (2026-08-19, D-132)

## T.0 Kaynak sicili — ⚠ **DOI disiplini geriledi**, ve 14. kimlik hatası

| DR'nin verdiği | Crossref | karar |
|---|---|---|
| Huberman & Glance 1993, `10.1073/pnas.90.16.7716` | ✅ doğru | **alındı** |
| Dohare ve ark. 2024, `10.1038/s41586-024-07711-7` | ✅ doğru | **alındı** |
| Arthur 1989, `10.2307/2234208` | ✅ doğru | alındı (yan) |
| ❌ **"El-Horbaty ve ark."**, *Permutation Tests for Random Effects in LMM* | ⛔ o makale **Lee & Braun 2012**, *Biometrics*, `10.1111/j.1541-0420.2011.01675.x` | **künye düzeltildi**, iddia alındı |
| ⚠ Caravaggio ve ark. 2021, *"non-linear **dynamic** model"* | gerçek başlık *"non linear **marketing** model"*, `10.1007/s10203-021-00339-6` | ⚠ **alan farkı önemli** — düopol pazarlama modeli |
| Flache & Macy 2011 (DOI yok) | `10.1080/0022250X.2010.532261`, *Small Worlds and Cultural Polarization* | ⚠ **alıntı kaynaktan değil**, başka makalenin onları anlatan cümlesinden |
| *"Spontaneous Formation of Stereotypes…"* (DOI yok) | Martin ve ark. 2014, `10.1177/0956797614541129` | künye tamamlandı |
| Ash & Adams 2020 · Lyle 2023 · Wang 2025 · "Churn and Plasticity" · "Dual Nature of Plasticity Loss" · "Probability for Data Science" · "Local Interactions and Heterogeneity…" | **DOI verilmedi**, doğrulanamadı | **kanıt olarak alınmadı** |

⚠ **~15 iddianın yalnız 3'ünde DOI vardı** ⇒ D-080'den beri istediğimiz 1.
şart bu turda **tutmadı**. (DR #9 ve #10'da tutuyordu.)
✅ Buna karşılık **boşluk ilanı iki kez yapıldı** (argmax+eşik bileşimi ·
evrensel nesil alt sınırı) ⇒ 3. şart **tuttu**.

## T.1 ⛔ Alıntısı iddiasını taşımayan iki yer

1. *"analyzing differences in treatment induced variance rather than species
   numbers"* — aynı LMM özetine atfedilmiş, ama **"species numbers"** ekoloji
   terimi; bir LMM permütasyon-testi özetinde bulunamaz. ⇒ **alınmadı**.
2. *"Probability for Data Science" §5.8:* *"Dimensionality reduction can thus
   be achieved by… only keeping the larger coefficients."* Bu **katsayı
   seçme** hakkında; bizim **eksenler üzerinde argmax** yapımızı desteklemiyor.
   ⇒ **alınmadı** (2. hata biçimi: gerçek kaynak, taşımadığı iddia).

## T.2 ⛔ İç çelişki — ve bizim için en riskli madde

DR, Q5'te **boşluk ilan ediyor**: *"No specific claim was found… establishing a
single universal mathematical minimum generation threshold…"* — ama hemen
ardından **normatif bir tablo** basıyor: *"1–3 nesil ⇒ birikimli kalıtım iddia
edilemez · 8+ nesil ⇒ edilir."*

⚠ Tek dayanağı **Martin ve ark. 2014**'ün sekizli zincirleri, ki o **bir
çalışmanın tasarımı**, standart değil. ⇒ **Normatif tablo alınmadı**;
⚠ **ama uyarısı alındı:** tasarımımız **G=3** ve *"birikimli"* kelimesi
üçüncü ön-kayıtta **ilan edilmiş sınırla** kullanılmalı.

## T.3 ⭐ Alınanlar

### (a) **Loss of Plasticity** — D-130 §12'nin adı bulundu
Dohare ve ark. 2024 (*Nature*, doğrulandı): *"standard deep-learning methods
gradually lose plasticity in continual-learning settings until they learn no
better than a shallow network."*
⇒ Adapter sönümümüz (6/6 dizide 1.8×–4.8×) **adı konmuş bir olgu**.
⚠ **Bizim eklediğimiz çekince:** LoP *"öğrenme yeteneğini yitirme"*dir; bizde
gözlenen **güncelleme büyüklüğünün küçülmesi** olabilir ki bu **yakınsama** da
olabilir. Ayırt etmek için güncelleme büyüklüğü değil **öğrenme sonucu**
ölçülmeli. DR bu ayrımı yapmadı; sınır olarak yazıldı.

### (b) Sıfır-varyanslı kolun istatistiği
Lee & Braun 2012 (künye düzeltilmiş): varyans bileşeni **parametre uzayının
sınırında** olduğunda standart LRT asimptotiği çöker; çözüm **karışım χ²**
(`0.5χ²_q + 0.5χ²_{q+1}`) ya da **permütasyon testi**.
⚠ Bizi **şimdi** bağlamıyor (P7-b: kestirim, test değil) ama doğrulayıcı
koşumun test bölümüne girecek.

## T.4 ⛔ Alınmayan — ve **neden**: Q2'nin iki mekanizması bizde zaten var ya da uygulanamaz

| DR'nin önerisi | bizdeki durum |
|---|---|
| **Asenkron güncelleme** (Huberman & Glance, doğrulandı) | ⚠ **Zaten var**: havuz sırayla ve **rotasyonla** hizmet ediyor. İşe yaramamasının sebebi asenkronluk eksikliği değil, **karar fonksiyonunun basamak olması** — D-084: davranış eşlemesinin **tek soğurucu çıktısı** var, 1e-9'luk girdi farkı bile çıktıyı oynatmıyor |
| **Birlikte var olan çekiciler / kaotik ayrışma** (Caravaggio) | ⚠ Sürekli, duyarlı dinamik gerektiriyor; bizim karar haritamız **ayrık ve soğurucu**. Ayrıca kaynak **düopol pazarlama modeli** |

## T.5 ⭐⭐ Turun **gerçek** kazancı — hiç düşünmediğimiz kaldıraç

DR'nin Q2 cevaplarının **hepsi** (uzamsal topoloji · yerel etkileşim ·
aspirasyon karşılaştırması) tek bir şeye dayanıyor: **ajanların birbiriyle
etkileşmesi**.

⛔ **Bizim popülasyonumuzda ajanlar birbirleriyle hiç etkileşmiyor** (D-130
§9): sekizinin de `opponent_id`'si **aynı NPC**, ve tek ortaklıkları mera.

⇒ **Ajan-ajan etkileşimi**, kıtlıktan **bağımsız** ve C1'i **ihlal etmeyen**
(hiçbir trait atanmıyor) bir simetri kırma kaldıracı — ve bugüne kadar
tasarımda hiç yer almadı.
⚠ Bedeli: en az iki yeni sabit (kim kiminle, hangi sıklıkta) ⇒ **üçüncü
ön-kayıtın konusu**, bu koşumun değil.

## T.6 ⇒ D-131 **ayakta**

DR'de D-131'i çürüten hiçbir şey yok; dolaylı olarak **destekliyor** (dejenere
kontrol parametrik testi geçersiz kılar ⇒ kolu betimleyiciye indirmek tutarlı).
⭐ **Eklenen tek şey:** ajan-ajan etkileşimi, kontrolü yeniden değişken
yapabilecek **en güçlü aday** olarak kayda giriyor.

---

# §U — **DR #12 mutabakatı** (2026-08-19, D-140) · ⭐ **biçimde en iyi tur, ama dört alıntı kaynağında yok**

**Brief:** `2026-08-19_price-sensitivity-and-seed-budget_PLAIN.txt` ·
**Ham cevap:** `2026-08-19_DR12-answer-raw.md`

**Kısa hüküm:** ⭐ **Q1 indirgemeyle cevaplandı ve bu 2.1'i açıyor** — kovaryans
için yeni bir istatistik gerekmiyor; kovaryansı **tohum başına bir skalere**
(`ΔCov`) indirgeyince DR #1'de zaten benimsediğimiz Lakens çerçevesi
**olduğu gibi** uygulanabiliyor. ⛔ Ama iki madde alınmıyor: §3'ün yanlılık
iptali **kaynaksız ve adreslenmemiş bir boşluk taşıyor**, ve dört "birebir
alıntı" kaynaklarında **yok**.

## U.0 Kaynak kimlikleri — ⭐ **4/4 doğrulandı**

| kaynak | doğrulama |
|---|---|
| **Lakens 2022**, *Sample Size Justification*, Collabra: Psychology 8(1):33267, `10.1525/collabra.33267` | ✅ DR #1'de zaten yerel doğrulanmıştı (§G.1/G1) |
| **Rice 2008**, *BMC Evol Biol* 8:262, `10.1186/1471-2148-8-262` | ✅ DR #8'de zaten doğrulanmıştı (§P.2, *"birebir"*) |
| **Gelman & Carlin 2014**, *Perspectives on Psychological Science* 9(6):641–651, `10.1177/1745691614551642` | ✅ **Crossref'ten doğrulandı** — başlık, yazarlar, dergi, cilt, sayı, sayfa **birebir** |
| **Lazic 2010**, *BMC Neuroscience* 11:5, `10.1186/1471-2202-11-5` | ✅ **Crossref'ten doğrulandı** — birebir |

⇒ **12 kimlik hatasından sonra ikinci temiz tur** (ilki DR #9). Künye disiplini
**oturdu**.

## U.1 ⛔ Ama R2 (birebir alıntı) **kısmen çöktü** — dört alıntı kaynağında yok

| # | alıntı | denetim |
|---|---|---|
| **A1** | Lakens: *"A sensitivity power analysis answers the question: 'Across a range…'"* | ✅ **gerçek** — ifade Lakens'in altı yönteminden biriyle örtüşüyor |
| **A2** | Lakens: *"The minimal statistically detectable effect size addresses…"* | ✅ **gerçek** — aynı listeden |
| **A3** ⛔ | Lakens'ten alıntı diye: *"A sensitivity analysis will report the smallest effect size … **(Lakens, 2022; Perugini et al., 2018)**"* | ❌ **yapısal olarak imkânsız.** Bir makale kendi gövde metninde **kendini** parantez içinde anamaz ⇒ bu, Lakens'i **anan başka bir metinden** alınmış |
| **A4** ⛔ | Lakens'ten alıntı diye: *"When a sample size justification is based on resource constraints, **Lakens recommends** that researchers…"* | ❌ **yapısal olarak imkânsız.** Lakens kendinden **üçüncü şahısla** söz etmez |
| **A5** ⛔ | Gelman & Carlin: *"Type S errors occur when a null hypothesis is confidently rejected in light of the alternative being true…"* | ❌ **makalede YOK** — PDF tam metninde arandı, bulunamadı |
| **A6** ⛔ | Gelman & Carlin: *"Type M errors … and was likely the very reason why 'statistical significance' occurred in the first place"* | ❌ **makalede YOK** — aynı arama |

**Makalenin kendi tanımı** (PDF'ten birebir): *"(a) the probability that claims
with confidence have the wrong sign (Type S [sign] error) and (b) the factor by
which the magnitude of an effect might be overestimated (Type M [magnitude]
error or exaggeration ratio)"*.

⚠ **Ve DR'nin uydurma tanımı bir şeyi düşürüyor:** gerçek tanımlar
**anlamlılığa koşullu** (*"conditional on being significant"*); DR'nin
sürümünde bu koşul **yok**, ki Type S/M'in bütün anlamı odur.

⇒ **Yeni kusur türü değil ama yeni bir kip:** kimlik doğru, **alıntı uydurma**
(§M'in *"doğru kimlik, yanlış iddia"*ının kardeşi). ⭐ **R2 şartı tam da bunu
yakalamak için konmuştu ve yakaladı** — DOI doğrulaması bu dördünü **geçirirdi**.

## U.2 İddia bazında mutabakat

| # | İddia | DAU'da durum | Karar |
|---|---|---|---|
| **U1** ⭐⭐ | Birincil ölçüt: tohum başına `ΔCov = Cov_lived − Cov_shuffle`, sonra tohumlar arası **Cohen's `d_z`** | ⭐ **Q1'in gerçek cevabı, ve indirgemeyle geliyor:** kovaryans için yeni MDE aleti gerekmiyor — tohum başına **bir skalere** indirgenince D-052'nin kullandığı makine **aynen** çalışıyor. Birincil karşıtlık zaten `lived ↔ shuffle` (D-131) | **uyumlu — benimsenir**, 2.1'i açan madde |
| **U2** | Bütçe-kısıtlı gerekçelendirme + duyarlılık analizi kovaryans için de geçerli | DR #1'de zaten benimsenmişti (§G.3); DR #12 **bağımsız olarak** teyit ediyor | **uyumlu** |
| **U3** | Parametrik formül yerine **permütasyon/Monte Carlo** ile ampirik null | Kuyruk 2.1'in **C seçeneği** buydu. DR onu *"alternatif"* değil **tamamlayıcı** yapıyor | **uyumlu — C, B'nin yerine değil yanına** |
| **U4** ⭐ | **Gelman & Carlin**: küçük N + gürültüde anlamlı sonuçlar **işaret** (Type S) ve **büyüklük** (Type M) hatası taşır | ⭐ Bize **birebir** uyuyor: küçük N + eşikli uç nokta + az sayıda tohum. ⚠ **Alıntılar uydurma (A5/A6) ⇒ fikir alınır, alıntı alınmaz**; kaynağın kendi cümlesi kullanılır | **uyumlu — fikir alınır, metin alınmaz** |
| **U5** ⭐ | **Lazic 2010**: tekrarlama birimi **tohum**; 8 ajan alt-örneklem; G=2 geçiş **zamansal olarak bağımlı** ⇒ ikisini bağımsız saymak **pseudoreplication** | ✅ **Kodla doğrulandı:** varis ebeveynin **adapter'ını** (D-102) ve anılarını miras alıyor ⇒ nesil 2 nesil 1'in durumundan türüyor. Bu kısıtı **hiç yazmamıştık** | **uyumlu — ve bağlayıcı** |
| **U6** ⛔ | Öneri: G=2 geçişi tohum başına **tek ortalamaya indir** | ⛔ **D-132 ile çelişiyor:** adapter sönümünü (6/6 dizide **1.8×–4.8×**) ölçmek istiyoruz, ortalama tam onu **siliyor**. ⚠ DR'nin kendi saldırı vektörü de bunu söylüyor | **bilinçli sapma adayı** — test istatistiği ortalama olsun, **nesil satırları raporlamada kalsın**. ⛔ Karar Yasin'in |
| **U7** ⛔ | Eşleştirilmiş fark, Rice'ın küçük-N şişmesini **iptal eder** (iki kol da N=8 ve aynı tohum) | ❌ **Kaynaksız ve boşluğu adreslenmemiş.** Rice'ın bulgusu bir **büyütme** (*"effects of selection are actually amplified"*); büyütme **çarpansal** ise farklı gerçek seçilime sahip kollar **farklı oranda** büyür ve **iptal olmaz**. DR toplamsal-mı-çarpansal-mı sorusuna **hiç değinmiyor**, ve bunu [OPINION] diye de işaretlememiş | **brief yanılmış** — ⚠ **yük taşıyan madde**, §3'ün bütün çaresi buna dayanıyor |
| **U8** | Kol başına ham `Cov` (shuffle ve null dahil) **ayrıca raporlansın**, etki büyüklüğüne emilmesin | Aletimiz zaten kol başına Price satırı yazıyor ⇒ **neredeyse bedava** | **uyumlu — alınır** |
| **U9** ⭐⭐ | **İki aşamalı ön-kayıt:** `P_active` (`Var(z) > 0` olan hücre oranı) **+** `Cov_cond` (yalnız aktif hücrelerde kovaryans) | ⭐⭐ **Üçüncü ön-kaydın omurgası olabilir.** D-121 *"tanımsız ≠ sıfır"* ayrımını zaten çizmişti; PROVENANCE_AUDIT ölçülebilir hücre oranını **%22** ölçtü. DR bunu **ön-kayıtlanabilir bir yapıya** çeviriyor | **uyumlu — benimsenir** |
| **U10** ⚠ | U9'un saldırı vektörü: aktif hücreye koşullamak **survivorship bias** yaratır, çünkü eşiği geçmek **müdahaleden etkilenmiş** olabilir | ⚠ **Bizde varsayımsal değil:** `lived` kolunun eşiği daha sık geçmesi tam olarak beklenen şey ⇒ **`P_active`'in kendisi bir sonuçtur**, bir eleme filtresi değil | **uyumlu — ve U9'un uygulanma biçimini belirliyor:** `P_active` **eş-birincil**, ön-eleme değil |
| **U11** | Rapor dili kalıpları (yöntem + anlamsız sonuç) | Dil doğru ve L9/L10'un ruhuyla aynı. ⚠ **Ama birebir yapıştırılamaz:** kalıp *"S seeds **per experimental arm**"* diyor — bizde tohumlar **kollar arasında paylaşılıyor** (tohum içi eşleştirme). DR #1'in G12'siyle **aynı sınıf** hata | **uyumlu ama düzeltilerek** |
| **U12** ⭐ | **Boşluk ilanı:** Price ayrıştırmasını güç/duyarlılık beyanıyla birleştiren **yayımlanmış örnek yok** | ⭐ **R3 ikinci kez tuttu.** ⇒ Taklit edecek örnek yok; sentez **ilan edilerek** yapılacak | **uyumlu — sınır olarak yazılır** |
| **U13** | *"Bunu özgün bir metodolojik sentez olarak ilan edin"* [OPINION] | ⚠ Gereksiz ve DR'nin kendi saldırı vektörü zaten çürütüyor. Bize gereken **özgünlük iddiası** değil, **sınır ilanı** | **alınmaz** |

## U.3 ⭐ R5 (saldırı vektörleri) — **yeni şart, ve işe yaradı**

Altı bölümün altısında da geldi, ve **ikisi benim de yazacağım itirazdı**:

1. **§1'in vektörü** — permütasyon **değiştirilebilirlik** varsayar; ortak
   havuzda ajanların yaşam öyküleri **bağımsız değil**. ⚠ Bizde bu **kesin
   doğru** (P0-①: sıralı erişim, paylaşılan mera) ⇒ U3'ün permütasyon şeması
   **naif hâliyle uygulanamaz**, tohum içi blok yapısı korunmalı.
2. **§4'ün vektörü** — U10, yukarıda.

⇒ **R5 kalıcı şart olsun.** Maliyeti sıfır, ve bir turda iki gerçek kusur
yakalattı.

## U.4 Ne alınıyor, ne alınmıyor

**Alınan:** U1 (`ΔCov` indirgemesi — **2.1'i açan madde**) · U2 · U3
(tamamlayıcı olarak, ⚠ blok-permütasyon düzeltmesiyle) · U4'ün **fikri**
(Type S/M sınır olarak ilan edilir) · U5 (**tekrarlama birimi = tohum**,
bağlayıcı) · U8 · U9 + U10 (`P_active` **eş-birincil**) · U12 (sınır).

**Alınmayan:** U7'nin iptal iddiası (kanıtsız, ⚠ **yük taşıyor**) · U13
(özgünlük iddiası) · **A3–A6 alıntı metinleri** (dördü de kaynağında yok) ·
U11'in kalıbı **birebir** (tohum tarifi yanlış).

**Yasin'e giden:** **U6** — nesil geçişleri ortalanacak mı? Test istatistiği
için *evet*, ama D-132'nin sönüm ölçümü için nesil satırları **kalmalı**.
Öneri: **ikisi birden** — ortalama test eder, satırlar raporlar.

**Açık kalan:** U7'nin boşluğu. Rice'ın büyütmesi **toplamsal mı çarpansal mı**
sorusu cevaplanmadan `ΔCov`'un yanlılığı iptal ettiği **iddia edilemez**.
⇒ Ya kaynaktan çözülür, ya **simülasyonla** ölçülür (GPU'suz: `w` ve `z`'yi
bilinen bir üretici modelden örnekleyip N=8'de kestirimin yanlılığını ölçmek).

---

# §V — **DR #13 mutabakatı: DAU v3.0 mimari incelemesi** (2026-08-22, D-169) · ⛔ **taşıyıcı iddia cebirsel olarak ters**

**Brief:** Yasin'in yazdığı *"[DEEP RESEARCH & ARCHITECTURAL REVIEW REQUEST]"*
prompt'u — dört sütun: (1) ardışık ince ayara alternatifler, (2) grafik tabanlı
kümülatif bilgi aktarımı, (3) hibrit mimari ayrımı, (4) v3.0 yol haritası.
**Kanal:** dosya olarak girmedi, sohbete yapıştırıldı ⚠️ (§9'un usulünden sapma,
D-006). **İkinci bir değerlendirme** de eklendi — ⚠️ **kodu görmeyen** bir ajandan.

⚠️ **Bu tur, şart listesinin ilk kez tamamen boş döndüğü turdur** (§V.5).

---

## §V.1 ⛔ Taşıyıcı iddia: *"DPO kaybı `ln 2`'ye DOYUYOR"* — **brief yanılmış**

| | |
|---|---|
| **Rapor ne diyor** | Ajan öğrendikçe `σ(r̂_l − r̂_w) → 0` ⇒ gradyan sönüyor ⇒ *"loss saturates near `ln 2 ≈ 0.693`"* ⇒ **structural null**: yeni krizde bile parametre güncellenmiyor |
| **Cebir ne diyor** | `L = −log σ(βΔ)`. Raporun tarif ettiği hâlde (`σ(r̂_l − r̂_w) → 0`) marj `Δ` **büyük ve pozitiftir** ⇒ `σ(βΔ) → 1` ⇒ **`L → 0`**, `ln 2`'ye değil. `L = ln 2` **tam olarak `Δ = 0`** iken, yani **hiç marj öğrenilmemişken** olur — bu başlangıç durumudur |
| **Ölçüm** | Bu koşumun **64 eğitim çağrısı**: ortalama **0.69201** · `ln2 = 0.69315` · ortalama `\|L − ln2\| = 0.00343` · **36/64 altında, 28/64 ÜSTÜNDE** |
| **Verdict** | **Semptomda uyumlu, mekanizmada brief yanılmış** |

⛔ **Belirleyici sayı `28/64`.** `L > ln 2` ⟺ `σ(βΔ) < ½` ⟺ **`Δ < 0`** — yani o partide politika **reddedilen tarafa** kaymış. *"Çok iyi öğrendiği için donmuş"* bir model negatif marj **üretemez**. Doygunluk hipotezi bu dağılımı açıklayamaz.

⚠️ **Ve asıl sınır:** `epochs = 1`, `batch = 1`, `grad_accum = 4`, çift sayısı
6–28 ⇒ eğitim başına **1–7 optimizer adımı**, `lr = 1e-6`. **Beş adımda kayıp
`ln 2` civarında olur.** ⇒ Bu veriden ne doygunluk ne dejenerasyon teşhis
edilebilir; **rapor da biz de o sayıdan fazlasını okuduk.**

⇒ **Reçete düşüyor:** raporun *"saf DPO yığınını kaldır"* tavsiyesi bu iddiaya
dayanıyordu. Bizim `ln 2`'mizin **zaten ölçülmüş** açıklamaları var:
**GAP-18** (`uniq_rejected` 100/94 vs `uniq_chosen` 1025/971) · **D-062**
(dizilerin %85.5'i 512'de kesiliyor; `chosen` 57.2 vs `rejected` 38.7 token ⇒
uzunluk doğrudan marja giriyor) · **D-029** (kaldıraç `lr`).

## §V.2 Brief'in kendi tarifi — üç iddia koda soruldu

⚠️ **DR #1 ve #2'nin dersi:** *"brief kalitesi girdi kalitesiyle sınırlı, ve
girdiyi biz yazıyoruz."* Bu yüzden önce prompt'un mimari iddiaları doğrulandı.

| prompt ne dedi | kod ne yapıyor | verdict |
|---|---|---|
| *"HippoRAG 2 (PageRank over NetworkX knowledge graphs)"* | `dau/memory/ppr_retrieval.py` — kendi docstring'i *"HippoRAG 2 **inspired** PPR over **SQLite domain co-occurrence graph**"*. NetworkX gerçek, PPR **canlı skorlama yolunda** (`PPR_WEIGHT_IN_SCORE = 0.30`, `retrieval.py:84`). ⛔ **OpenIE yok · üçlü yok · varlık grafiği yok** | **brief eksik tarif edildi** |
| *"prohibitive memory/VRAM overhead"* | ❌ **VRAM'de yanlış:** koşum 6.1 GB / 8.2 GB, adapter **14 MB**. ⭐ **Diskte doğru ve prompt'un söylediğinden büyük:** `dau_runs/adapters` **16 GB, 1194 dizin** | **brief yanılmış (VRAM) · yetersiz (disk)** |
| *"Ebbinghaus forgetting curves"* | `dau/memory/decay.py`, deney yoluna bağlı (D-031, ölçülen `deleted_count` ort. 24.90) | **uyumlu** |

⇒ **Raporun 2. sütununun tamamı** (*"HippoRAG 2'yi nesiller arası kalıtım için
optimize et"*, OpenIE üçlüleri, PHR kodlayıcı, üç katmanlı konsolidasyon)
**bizde olmayan bir makineyi** optimize ediyor.

⛔ **Ve bir kör nokta ölçüldü:** `I5.1` (*PPR gerçekten aktif mi*) `preflight.py:1020`'de
**tanımlı**, `run_protocol_c_prime` yolunda **bağlı**, ama **popülasyon koşumunun
kapı listesinde YOK** (son iki koşumun kapıları: I0.3 · I0.4 · I0.6 · I0.7 ·
I1.1 · I4.1 · I4.2 · I5.4 · I5.5 · I5.6). ⇒ PPR'ın boş grafikte
`{seed: 1.0}` döndürüp döndürmediğini **bilmiyoruz**. **D-149'un birebir
deseni** (kapı tanımlı, bağlı değil) ⇒ **K6.**

## §V.3 ⛔ Üç desenin ikisi değiştirilemez kurallara çarpıyor

| desen | çarptığı kural | verdict |
|---|---|---|
| **EGI** — `v_pheno ∈ [0,1]^p` (*risk aversion, altruism, stress response*) yapılandırılmış sistem direktifine derlenip prompt'a giriyor | **Yasak #1 — No trait injection.** ⚠️ Vektör yaşanmışlıktan türetilse de **etiket olarak geri verilmesi** aksiyomun tam sınırı | ⛔ **aksiyom kararı, Yasin'in** (D-007) |
| **SVC** — çıkarım anında aktivasyona yönlendirici vektör | **Kilit K7 (D-070)** bunu zaten reddetti: *"Davranış müdahalesi: Hayır — aksiyom"* | ⛔ **kilitli kararla çelişiyor** |
| **CHRE-FA** — LoRA-FA (`A` donuk) + TIES-Merging | Aksiyoma dokunmuyor: *"ajana ne verelim"* değil **"nasıl eğitelim"** | ⏸ **meşru aday, üçüncü ön-kayıta** |

⚠️ **İkinci ajanın değerlendirmesi EGI'yi *"EN TAVSİYE EDİLEN & RİSKSİZ"* diye
işaretlemiş.** Kodu ve `CLAUDE.md` §3'ü görmediği için iki çarpışmayı da
göremiyor. **Aksiyom açısından EGI en riskli olanıdır.** ⇒ Mutabakat adımının
neden zorunlu olduğunun bu turdaki kanıtı.

⚠️ Ayrıca *"DPO'yu kaldır"* **Kanal 2'yi** boşaltır — o **kilitli mimari karar**
(§4, *"Dual-channel mimari"*) ve aksiyomun iki kanalından biri.

## §V.4 ⭐ Alınan tek şey: **RCI** — ve gerçek bir kör noktaya denk geliyor

`RCI(g) = 1 − H(σ(H^(g))) / H(σ(H^(0)))`, ara katman aktivasyonlarının
**spektral entropisi**.

⭐ **Neden gerçek:** `run_population_experiment.py:1338` → `inherit_adapter(parent_id, heir_id)`
— **varis ebeveyninin adapter'ını miras alıyor** (D-102, Yasin 2026-08-17) ⇒
adapter'lar nesiller boyunca **fiilen üst üste biniyor**, ve taban temsilin
bozulup bozulmadığını **hiç ölçmedik, bir kapıya da bağlamadık**.

✅ Deterministik · GPU'da ucuz · **hiçbir fiziği değiştirmiyor** ⇒ §2.10 altında
meşru (saf ölçüm).

⛔ **CKE ALINMADI:** içinde `D_KL(π_g ‖ π_0)` var — kol farkına yakın bir nicelik,
**L9'un okunmayacaklar listesiyle çakışıyor**; ayrıca `S_task` bizde tanımsız.

## §V.5 ⚠️ Süreç bulgusu — **şart listesi ilk kez tamamen boş döndü**

Prompt açıkça *"Cite key research papers, arXiv IDs, and established
methodologies from 2023–2026"* istedi. **Rapor tek bir tanımlayıcı vermedi.**
TIES-Merging · LoRA-FA · RegMean · HippoRAG 2 · RepE · MSRS **adları** geçiyor,
hiçbirine **yazar-yıl-DOI yok**, kaynakça yok, boşluk ilanı yok.

| şart | nereden geldi | bu turda |
|---|---|---|
| **DOI / kimlik** | D-080 | ❌ |
| **birebir alıntı** | D-080 | ❌ |
| **kaynakça + boşluk ilanı** | D-082 | ❌ |

⚠️ Önceki turlarda **12 kimlik hatası** çıkmıştı ve hepsi bu şartlarla
yakalanmıştı. ⇒ **`CLAUDE.md`'nin kuralı gereği bu rapordan kilitli karar
yazılamaz:** *"Kanıtı olmayan hiçbir madde kilitli karar olarak yazılmaz."*

⚠️ **Usul sapması da kayda geçsin:** brief **dosya olarak** girmedi, sohbete
yapıştırıldı (D-006 dosya istiyor). Bu turda zarar vermedi ama izlenebilirliği
düşürdü — ham metin `docs/research/` altında **yok**.

## §V.6 Sonuç

**Bu rapor kodu değiştirmemeli.** Değeri teşhiste değil — teşhisi ters —
**bir ölçüm fikrinde** (`RCI`), ve o da gerçek bir kör noktamıza denk geliyor.

| ne | ne zaman |
|---|---|
| ❌ EGI · SVC | **şimdi değil** — aksiyom/K7 kararı, Yasin'in |
| ❌ DPO'yu kaldırmak | **hayır** — gerekçesi çürük (§V.1), Kanal 2 kilitli |
| ⏸ LoRA-FA · TIES-Merging | üçüncü ön-kayıt **aday listesi** |
| ⏸ **RCI** | **fizik kararından sonra** — fizik değişirse tabanı kayar |
| ⭐ **`I5.1`'i popülasyon kapılarına bağla** | **şimdi** — fizikten bağımsız, saf aletleme, K6 borcu |
