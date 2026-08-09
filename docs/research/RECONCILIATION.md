# Deep Research ↔ DAU kod tabanı mutabakatı

Bu dosya **DAU konularına göre** indekslenir, brief'e göre değil. "Backend
hakkında literatür ne diyor" sorusunun cevabı tek başlık altında, kaynak
atıflarıyla bulunur.

Karar sütunu: `uyumlu` · `bilinçli sapma` · `fark edilmemiş kayma` ·
`brief geçerli değil` · `açık`

Süreç: D-006. Kaynak dosyalar: `docs/research/*.md`.

## İşlenen brief'ler

| Dosya | Durum |
|---|---|
| `2026-08-08~_per-agent-lora-serving.md` | ✅ işlendi (2026-08-09) |
| `2026-08-06_protocol-c-metacognition-eval.md` | sırada (#1) |
| `2026-08-06_protocol-cprime-teshis.md` | sırada (#2) |
| `2026-08-06_sentetik-kognisyon-mimari.md` | sırada (#3) |
| `2026-08-04_metacognition-neuroscience.md` | sırada (#4) |
| `2026-08-04_v1-kritik-sistem-audit.md` | tarama yeterli |
| `2026-08-04_minilm-meta-ab-audit.md` | tarama yeterli |
| `2026-08-04_daerm-allostatic-recovery.md` | formül uyum kontrolü |
| `2026-08-05_daerm-trauma-magnitude.md` | formül uyum kontrolü |
| `2026~_agent-curriculum-engine.md` | **ertelendi** — Yasin: DAU sonrası proje |

---

## Adapter izolasyonu (per-agent LoRA serving)

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §1 | Yüksek seviye PEFT/PyTorch soyutlamaları bellekte aktif adaptörleri karıştırır; izolasyon **disk düzeyinde** zorunlu, bellekte tek `default` slot tutulmalı | `f25b0ef` tam olarak bunu yaptı; `test_no_dead_adapter_root_reference` koruyor | **uyumlu** |
| 08-08~ §1 / Kritik Bulgu 1 | Hot-swap'te **CUDA akış senkronizasyonu + gradyan önbellek temizliği** zorunlu | `local_llm.py`'de `empty_cache` / `synchronize` **yok**; yalnızca `optimizer.zero_grad()` var | **açık** — GAP-6'daki `empty_cache()` maddesi "temizlik" değil, brief'e göre **izolasyon doğruluğu** meselesi. Önceliği yükseltilmeli. |

## Nesil sonu eğitim vs online öğrenme

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §2 | Generation-end batch ≫ per-event online (felaket unutma, gradyan patlaması, LayerNorm bozulması) | Kilitli karar, uygulanmış | **uyumlu** |
| 08-08~ §2 | Tercih çiftleri PE büyüklüğüne göre sıralanmalı | `build_pe_ranked_pairs` (`f2ac7db`) | **uyumlu** |
| 08-08~ §2 | `K ≥ 5` benzersiz çıktı çeşitlilik kapısı | `DIVERSITY_MIN_UNIQUE=5` (`500c32d`) | **uyumlu** |
| 08-08~ §2 | `BATCH_SIZE=1` **ve gradyan biriktirme (gradient accumulation)** | `BATCH_SIZE=1` ✅ ama accumulation **yok** — `local_llm.py:610-627` her çift için ayrı `zero_grad()` + step. Uygulanan şey gradient **checkpointing** (bellek tekniği), accumulation (sinyal tekniği) değil. | **fark edilmemiş kayma** → CLAUDE.md GAP-8 |

**Neden önemli:** efektif batch = 1 → gradyan varyansı yüksek. DAU'nun
`n_pairs` rejimi zaten küçük; accumulation **ek VRAM maliyeti olmadan**
(micro-batch 1 kalır, step N mikro-adımda bir atılır) efektif batch'i
büyütür. `BATCH_SIZE=2` OOM verdiği için batching kapatılmış, ama
accumulation OOM vermez — iki teknik karıştırılmış görünüyor.

## Tercih öğrenmesi (DPO)

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §3 | NLI çelişki skoru ≥ 0.60 şartı zorunlu | `NLI_CONTRADICTION_THRESHOLD=0.60`, `18fb01e` üretim yoluna bağladı | **uyumlu** |
| 08-08~ §3 | 8B'de greedy → benzersiz çıktı düşer → DPO platosu; `T=0.2` sampling uygulanmalı | `DAU_LLM_DO_SAMPLE=1`, `T=0.2` | **uyumlu** |
| 08-08~ §3 | IPO, DPO'nun küçük veri kümelerinde aşırı özgüvenli marj üretmesini düzenler | DAU düz DPO kullanıyor | **açık** — DAU'nun rejimi (küçük `n_pairs`) tam olarak IPO'nun hedeflediği rejim. Aksiyon değil, D-005 alet kilidinde değerlendirilecek bir girdi. |

## Çift kanallı hafıza (sembolik ↔ parametrik)

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §4 | Olgusal bellek ile davranışsal uyum **kesinlikle ayrı** tutulmalı (Mem0, MAGMA, Zep, ECAI 2026) | Dual-channel mimari | **uyumlu** — kilitli karar |
| 08-08~ §4 | Sembolik kasadan Ebbinghaus ile silinen bir anının drift'i LoRA'da kalıcı kalabilir → tutarsızlık | Kodda doğrulanmadı | **açık** — GAP-4'ün kaynağı. Etiket doğru: "araştırmadan çıktı, kodda doğrulanmadı". |
| 08-08~ §4 | LoRA yalnızca **uzun vadeli genel tutumları** kodlamalı (risk alma, işbirliği, kaynak koruma) | Yaşam-PE tercih çiftleri olay bazlı; "uzun vadeli tutum" kısıtı açıkça uygulanmıyor | **açık** — GAP-4 ile birlikte değerlendirilmeli |

## Çok-nesilli deney / ön-kayıt standartları

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §5 | `K = 5` (DIVERSITY_MIN_UNIQUE) | aynı | **uyumlu** — ✅ provenans bulundu |
| 08-08~ §5 | `N ≥ 15` | aynı | **uyumlu** — ✅ provenans bulundu |
| 08-08~ §5 | `n_eff ≥ 12` | aynı | **uyumlu** — ✅ provenans bulundu |
| 08-08~ §5 | Varsayılan hipotez testleri: **paired t-test + Wilcoxon** | CLAUDE.md bunları "destekleyici" diyor | **uyumlu** (gen1 ΔPE eşleştirilmiş tasarımına oturuyor) |
| — | **Kruskal-Wallis + Fisher-Freeman-Halton** | `CLAUDE.md:64`'te "kilitli" olarak duruyor | **açık** — bu brief'te **yok**. Provenans hâlâ kayıp. Sıradaki aday: `2026-08-06_protocol-c-metacognition-eval.md` ("Statistical Power Analysis", "Primary Hypothesis Tests"). |

Not: çelişki değil, farklı uç noktaların testleri. Paired t/Wilcoxon =
eşleştirilmiş 2 kol (gen1 lived vs shuffle, aynı seed). Kruskal-Wallis =
eşleştirilmemiş 3 grup (D-002 doğum-drift tasarımı). D-002 yanlışlanmadı.

## Model seçimi / backend

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §7 | **Qwen-2.5-7B-Instruct şiddetle önerilir**: ~6.4 GiB (Llama 7.2), DPO sinyal tepkisi "yüksek, keskin logit ayrımı" vs Llama "orta, platoya düşebilir". *"Qwen gibi modellere geçilmemesi sinyal gücünü kısıtlamaktadır."* | Hâlâ Llama-3.1-8B 4-bit NF4 | **bilinçli sapma** — kök triyajda "aksiyon değil, karşılaştırma önerisi" olarak ertelenmişti. **D-005 ile yeniden açıldı.** |
| 08-08~ §7 | 4-bit NF4'te `double_quant=True`, `quant_type="nf4"` sabit tutulmalı | doğrulanmadı | **açık** (küçük) |

**Doğrulama (2026-08-09):** Qwen yalnızca bu brief'te geçiyor (arşivde
başka hiçbir dosya model seçimi tartışmıyor). Ve bu brief arşivin **en
yenisi** — bkz. tarih düzeltmesi D-008. Yani Yasin'in "en güncel öneri
olmalı" sezgisi **doğrulandı**.

**Bağlam değişikliği:** greedy-plato sampling (`T=0.2`) ile *çözülmedi,
etrafından dolaşıldı*. D-005 aleti kilitlemek üzere; model seçimi aletin
parçası. Pre-reg kilitlendikten sonra model değişimi post-hoc olur.

## Deterministik değerlendirme (LLM-as-judge yasağı)

| Kaynak | İddia | DAU'da durum | Karar |
|---|---|---|---|
| 08-08~ §8 | MiniLM PE + DAERM + Precision-PE + NLI yığını doğru | aynı | **uyumlu** |
| 08-08~ §8 | Hipotez testinden önce null/shuffle kontrol kolları + doygunluk audit'i | v3 smoke (`null_arm_clean`, `saturation_rate`) | **uyumlu** |

## Uygulanabilir olmayan / reddedilen

| Kaynak | İddia | Neden geçersiz | Karar |
|---|---|---|---|
| 08-08~ §1 (kök triyaj) | Scheduler-state drift / stale KV-cache reuse — concurrent multi-tenant serving riski | DAU sıralı (tek thread) çalışıyor; concurrent serving yok | **brief geçerli değil** (Yasin doğru triyaj etmiş) |
| 08-08~ §6 | Single-pass hierarchical extraction ile RAG sorgu maliyeti düşürülmeli | Maliyet DAU'da darboğaz değil; PPR + Ebbinghaus zaten var | **açık** (düşük öncelik) |

---

## Bu brief'ten çıkan aksiyonlar

| # | Bulgu | Nereye gitti |
|---|---|---|
| 1 | Gradient accumulation yok | CLAUDE.md **GAP-8** (yeni) |
| 2 | CUDA sync / `empty_cache` adapter hot-swap'te yok | GAP-6 önceliği yükseltildi |
| 3 | Qwen-2.5-7B tavsiyesi güncel | **D-005** girdisi (alet kilidi) |
| 4 | K=5 / N≥15 / n_eff≥12 provenansı | ✅ kapandı |
| 5 | Kruskal-Wallis / FFH provenansı | hâlâ açık → sıradaki brief |
| 6 | GAP-4 kaynağı doğrulandı | etiket doğru, aksiyon yok |
