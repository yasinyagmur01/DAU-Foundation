---
tarih: 2026-08-06
konu: Sentetik kognisyon ve yaşantısal plastisite — DAU mimari doğrulama
tetikleyen soru: 
---

## Kaynak prompt

```text
I am building DAU (Dynamic Agent Universe), a research simulation system where LLM-powered agents develop internal identity and traits through lived experience rather than injected personality parameters. The central axiom: "You cannot give an agent a trait. You can only give it life. Trait emerges from there."

Current architecture (all implemented, Python/LangGraph):

- Prediction error as delta magnitude via MiniLM cosine similarity (PE = 1 − cosine_sim)

- Ebbinghaus memory decay with ChromaDB + SQLite domain co-occurrence graph

- EmotionalWeight with somatic markers (threat, reward, novelty, social, loss) computed deterministically

- DriftState for permanent trauma-driven domain flagging with healing

- Generation consolidation with fitness-based transfer filtering

- LOD engine: T_cognitive index, System 1 (NPC heuristic) / System 2 (LLM) switching with hysteresis

- DAERM: Dynamic Allostatic Equilibrium Recovery Model (allostatic setpoints, endogenous gamma)

- Meta-observer with 4 actuators: lod_override, context_prune, drift_healing, trigger_retrieval

- Local LLM (Llama-3.1-8B, 4-bit QLoRA) with generation-end micro fine-tuning

- All metrics deterministic Python — no LLM-as-judge

Key empirical findings so far:

1. FROZEN WEIGHT NULL (paper-locked): Protocol C — seed-locked counterfactual, 40 pairs × 50 events, T=0.2 — mean ΔPE ≈ 0. Frozen-weight in-context metacognition cannot close the loop without parametric plasticity.

2. WEAK_LORA (N=3, signal v1, placeholder train bug): ΔPE_lived ≈ 0.001 — inconclusive.

3. SMOKE_SEPARATION (N=1, signal v2, lived-train cable fixed): ΔPE_lived ≈ −0.026 vs null ≈ +0.006 / shuffle ≈ +0.016. Correct direction, no statistical claim. Wall time ≈ 33 min on RTX 4070 Laptop 8GB.

4. Convention emergence: format sync observed, restraint sync NOT observed (75/75 defect). Agents synchronize linguistic form but continue resource extraction.

5. Meta-observer actuators: triggered 100/100 for lod_override + trigger_retrieval; trigger_drift_healing = 0 (threshold mismatch F_agent < 0.5 AND reward > 0.4 simultaneously).

6. System 2 rarely triggered under normal PE distribution (most events NORMAL/NOISE class).

Current blockers (prioritized):

TIER 1 — Existential:

A. Frozen weights = no parametric plasticity → closed-loop learning impossible under Groq. Local LLM + QLoRA partially addresses this but N=1 smoke only.

B. API token budget (Groq TPD 500k) → statistical testing impossible at scale. Prevents paired t-test on Protocol C.

TIER 2 — No meaningful evolution:

C. In-context memory (ChromaDB retrieval) does not produce systematic behavioral change — Protocol C and Meta A/B both null.

D. System 2 trigger rate too low → meta-observer has no substrate to act on.

E. MiniLM PE behavioral validity unclear — measures linguistic variation, may not capture genuine prediction error in agent decision-making.

TIER 3 — Hypothesis stage:

F. LoRA signal too weak / N too small for any statistical claim (SMOKE_SEPARATION N=1).

G. F_agent fitness externally defined by researcher — not emergent from environment (philosophical tension with trait-injection prohibition).

I need a comprehensive research investigation across the following questions. Please search recent literature (2022–2025), preprints, and technical reports:

---

QUESTION 1 — Parametric plasticity alternatives to full fine-tuning:

What are the most promising alternatives to QLoRA for continual/online learning in small LLMs (7–13B) during inference-time simulation? Specifically:

- Test-Time Training (TTT) and its variants — feasibility on 8GB VRAM

- Retrieval-Augmented Fine-Tuning (RAFT) vs pure RAG for behavioral persistence

- Prefix/prompt tuning as lightweight plasticity (vs full LoRA)

- In-context learning with structured memory vs parametric updates — which produces more persistent behavioral change?

- Is there evidence that generation-end (episodic) fine-tuning produces more stable behavioral traces than per-event online updates?

QUESTION 2 — Prediction error as a behavioral signal:

Is cosine similarity (MiniLM) between expected_outcome and actual_outcome a valid proxy for prediction error in agent decision-making? Specifically:

- What does neuroscience / cognitive science say about prediction error signals that drive learning vs those that don't?

- Are there better semantic distance metrics for measuring genuine surprise vs linguistic variation?

- Does Friston's Free Energy Principle suggest specific mathematical forms for PE computation that could replace or augment cosine similarity?

- What signal-to-noise ratio thresholds are needed for PE to drive learning in small LLMs?

QUESTION 3 — Continual learning and catastrophic forgetting in small LLMs:

For Llama-3.1-8B with QLoRA (r=16, seq=128) and generation-end micro-training:

- What is the catastrophic forgetting risk with shared adapter across agents/generations?

- Is per-agent adapter (separate LoRA weights per agent) feasible on 8GB VRAM with multiple agents?

- What replay/rehearsal strategies are most effective for episodic fine-tuning in simulation settings?

- Elastic Weight Consolidation (EWC) or similar — applicable at micro-train scale?

- What minimum N (training examples per generation) is needed before behavioral change becomes statistically detectable?

QUESTION 4 — Emergent trait and behavioral consistency:

Is there empirical evidence that LLM agents develop consistent behavioral traits through experience without explicit trait injection?

- Generative Agents (Park et al. 2023) — did agents develop consistent personalities or was it prompt-driven?

- Recent work on agent identity emergence, behavioral consistency across contexts

- What architectural features most reliably produce cross-situational behavioral consistency without trait injection?

- Is there a known minimum simulation length (events/interactions) for trait stabilization?

QUESTION 5 — Convention and restraint emergence:

Our finding: agents achieve format synchronization but not behavioral restraint (resource conservation). Is this expected?

- Literature on convention emergence in multi-agent LLM systems (2023–2025)

- What conditions are necessary for restraint/cooperation norms to emerge vs just surface-level linguistic alignment?

- GovSim (Piatti et al.) follow-up work — did agents ever achieve genuine resource conservation without external enforcement?

- Evolutionary game theory + LLM agents — what enforcement mechanisms produce stable cooperation?

QUESTION 6 — Evaluation methodology for trait emergence:

Our current evaluation: MiniLM PE comparison (lived vs null vs shuffle arms). Is this sufficient?

- What evaluation frameworks exist for measuring genuine behavioral change vs prompt-following in LLM agents?

- Behavioral consistency metrics across contexts (not just PE comparison)

- Statistical power requirements for paired experiments with N=10–40 in agent simulation settings

- Are there better experimental designs than seed-locked counterfactual (Protocol C) for isolating experience effects?

QUESTION 7 — Architectural alternatives:

Given our findings, what architectural changes could unlock emergent trait formation?

- World models in LLM agents (Dreamer-style) — could an explicit world model replace our DAERM allostatic recovery?

- Neurosymbolic approaches — combining deterministic state machines (our foundation layers) with learned components

- Memory-augmented transformers (MemGPT, A-Mem, HippoRAG 2) — which memory architecture best supports behavioral persistence?

- Is there a known architecture where in-context experience reliably produces out-of-context behavioral change?

Please structure your response as:

1. For each question: key findings, most relevant papers (with years), and direct implications for DAU architecture

2. A synthesis section: which findings most challenge or validate our current architecture

3. A recommendations section: top 3–5 architectural changes with evidence base and estimated feasibility on RTX 4070 Laptop 8GB + Groq free tier

4. Open questions: what remains genuinely unknown even in the literature

Focus on actionable findings. If a finding directly contradicts or supports a specific DAU design decision, call it out explicitly.
```

## Rapor

Sentetik Kognisyon ve Yaşantısal Plastisite: DAU Simülasyon Sistemi İçin Araştırma ve Mimari Doğrulama Raporu

## 1. Yedi Temel Soruya İlişkin Literatür Bulguları ve Mimari İzdüşümler

### 1.1 Parametrik Plastisite Alternatifleri ve Çıkarım Zamanı Eğitimi

Büyük Dil Modellerinde (LLM) çıkarım anında veya simülasyon sürecinde sürekli öğrenme (continual learning) sağlamak için parametrik plastisite alternatifleri, modelin temel ağırlıklarını dondurarak geçici veya kalıcı adaptör güncellemeleri yapmayı hedefler. DAU (Dynamic Agent Universe) sistemindeki dondurulmuş ağırlık hipotezinin (Frozen Weight Null) kanıtladığı üzere, yalnızca bağlam içi bellek (in-context memory) kullanımı, ajanın temel karar politikasını değiştirmede yetersiz kalmaktadır ($\Delta PE \approx 0$).Test-Time Training (TTT) ve türevleri (örneğin Policy of Thoughts - PoT, In-Place TTT, TTT-E2E), girdinin kafa karışıklığını (perplexity) minimize ederek veya Monte Carlo Ağaç Araması (MCTS) ve Group Relative Policy Optimization (GRPO) gibi yöntemlerle geçici LoRA adaptörlerini tek bir örnek üzerinde güncelleyip çıkarım sonrası bu adaptörleri silme mantığına dayanır. TTT süreçleri, ajanın o anki karmaşık olay karşısındaki akıl yürütme kalitesini artırsa da, adaptörlerin olay sonunda atılması nedeniyle nesiller arası veya uzun ufuklu yaşantısal kalıcılık (behavioral persistence) sağlamaz. Ayrıca 8GB VRAM (RTX 4070 Laptop) sınırında, çıkarım sırasında dinamik geri yayılım (backpropagation) çalıştırmak, özellikle uzun bağlamlarda KV-bellek (KV-cache) maliyeti nedeniyle bellek taşmalarına yol açmaktadır.Retrieval-Augmented Fine-Tuning (RAFT) ve saf RAG karşılaştırıldığında, RAG mimarilerinin 8k-32k bağlam uzunluklarında performans düşüşü yaşadığı ve çeldirici bilgilere karşı duyarlı olduğu görülmüştür. RAFT ise ajanın arama sonuçları içinden doğru davranışı süzmesini parametrik seviyede öğrettiği için davranışsal kararlılık açısından saf RAG'a kıyasla belirgin bir üstünlük sergiler.Ön ek / İstem Ayarlaması (Prefix/Prompt Tuning), LoRA ile kıyaslandığında 7B-13B ölçeğinde yetersiz kapasite sunmaktadır. Soft prompt vektörleri, ajanın karmaşık karar verme mekanizmalarını değiştirmek yerine yüzeysel dil biçimlendirmesine odaklanmaktadır.Bağlam içi öğrenme (ICL) ile parametrik güncellemeler arasındaki temel fark, kalıcılıktır. Literatür, ICL'in yalnızca geçici duyusal bias yarattığını, parametrik güncellemelerin ise ajanın mantıksal öncüllerini ve karar uzayını kalıcı olarak dönüştürdüğünü doğrulamaktadır.Olay bazlı online güncellemeler (per-event online updates) yerine nesil sonu (episodic generation-end) mikro fine-tuning yaklaşımlarının çok daha kararlı davranışsal izler bıraktığı gözlemlenmiştir. Olay bazlı güncellemeler derece düşmesine (gradient collapse) ve felaket unutmasına (catastrophic forgetting) yol açarken, nesil sonu tercih sıralamalı mikro-eğitimler (PE-ranked preference pairs, Signal v2) ajanın yaşadığı tüm olaylar arasından yüksek tahmin hatası ve somatik ağırlık içerenleri konsolide ederek kararlı bir adaptör güncellemesi sağlar.YöntemVRAM İhtiyacı (8B Model)Davranışsal KalıcılıkMimari KarmaşıklıkDAU UyumluluğuSaf RAG / ChromaDBDüşük (<1 GB)Yok (Bağlam İçi Sınırlı)DüşükMevcut (Yetersiz)Test-Time Training (TTT/PoT)Yüksek (>8 GB peak)Yok (Geçici Adaptör)Çok YüksekUygulanamazPrefix / Prompt TuningDüşük (<1 GB)ZayıfOrtaKısmen UygunPer-Event Online LoRAYüksek (>7.5 GB)Kararsız / Unutma RiskiYüksekUygun DeğilEpisodic QLoRA (Signal v2)Orta (6.4 GB peak)Yüksek (Parametrik Plastisite)OrtaTam Uyumlu[cite: 3]DAU mimarisine doğrudan çıkarım olarak, per-event online LoRA yaklaşımı terk edilmeli; nesil sonu preference-pair tabanlı mikro QLoRA güncellemesi (Signal v2 kablo mimarisi) ana parametrik plastisite rotası olarak benimsenmelidir.

### 1.2 Tahmin Hatasının (Prediction Error) Davranışsal Sinyal Geçerliliği

Nörobilim ve kognitif bilimde (özellikle Karl Friston’ın Serbest Enerji İlkesi - Free Energy Principle / FEP), canlı organizmalar çevreye dair içsel modellerinin ürettiği tahminler ile duyusal girdiler arasındaki farkı (tahmin hatası / Prediction Error - PE) minimize etmeye çalışır. Ancak organizmadaki her duyusal fark plastisiteye yol açmaz; yalnızca hassasiyetle ağırlıklandırılmış (precision-weighted) ve homeostatik setpoint'leri tehdit eden tahmin hataları sinaptik güncellemeyi tetikler.DAU Layer 1.5'te kullanılan all-MiniLM-L6-v2 embedding tabanlı kosinüs benzerliği ($PE = 1 - \text{cosine\_sim}$), semantik ve sentaktik varyasyonu ölçmede başarılı olsa da, kararsal seviyedeki gerçek sürprizi (decision-theoretic surprise) tam olarak yansıtamamaktadır. Örneğin, MiniLM kosinüs mesafesi zıtlıkları (negation/polarity) kaçırmakta; "kaynağı korumayı seçiyorum" ile "kaynağı korumayı reddediyorum" cümle çiftleri arasında yüksek semantik yakınlık verebilmektedir. Bu durum, ajanın kararsal sapmasını gürültüden ayırt etmeyi zorlaştırmaktadır.Daha geçerli semantik mesafe metrikleri şunlardır:Mantıksal Çelişki Düzeyi (NLI Cross-Encoder): Tahmin edilen eylem ile gerçekleşen eylem arasındaki Doğal Dil Çıkarımı (Entailment / Contradiction) skorlaması.Model İçi Perplexity Sapması (Log-Likelihood Ratio): Gerçekleşen çıktının ajanın kendi olasılık dağılımındaki log-olasılık karşılığı.PE-Ranked Preference Scoring: Alternatif kararların MiniLM veya NLI skoru üzerinden göreceli sıralanarak $PE(\text{chosen}) < PE(\text{rejected})$ biçiminde unlikelihood kayıp fonksiyonuna ($L_{\text{pref}} = \text{CE}_{\text{chosen}} - \alpha \cdot \text{CE}_{\text{rejected}}$) dönüştürülmesi.Friston'ın Serbest Enerji İlkesi, DAERM (Dynamic Allostatic Equilibrium Recovery Model) mimarisindeki allostatic setpoint $\mu_i$ ve endojen recovery $\gamma(t)$ ile birleştirildiğinde şu matematiksel forma dönüştürülmelidir:$$PE_i(t) = \pi_i \cdot \left(1 - \text{Sim}(E_i, A_i)\right) + \lambda \cdot \mathcal{D}_{KL}\left(q(\theta) \parallel p(\theta)\right)$$Burada $\pi_i$ değişkeni hassasiyet ağırlığıdır (precision weighting):$$\pi_i = \frac{1}{\sigma_{\text{history}, i}^2 + \epsilon}$$Ajanın geçmiş delta varyansı düşükse hassasiyet yüksek olur ve küçük bir sapma dahi büyük bir PE tetikler. 8B ölçeğindeki küçük dil modellerinde tahmin hatasının parametrik güncellemeyi yönlendirebilmesi için Sinyal-Gürültü Oranı (SNR) eşiğinin $PE \ge 0.40$ (DEEP sınıfı) seviyesinde tutulması gerekmektedir. Sub-threshold ($PE < 0.15$) sinyaller modelin öncül eğitilmiş (pretrained) ağırlıklarının gürültüsü içinde kaybolmaktadır.DAU mimarisine doğrudan çıkarım olarak, MiniLM kosinüs PE metriği tek başına karar sapmasını ölçmede yetersizdir; Sinyal v2 tercih çiftleri (preference pairs) ve NLI tabanlı zıtlık kontrolü ile takviye edilmelidir.

### 1.3 Küçük LLM'lerde Sürekli Öğrenme ve Felaket Unutması

Llama-3.1-8B modeli üzerinde $r=16, \text{seq}=128$ konfigürasyonu ile yapılan QLoRA mikro-eğitimlerinde, tek bir adaptörün (shared adapter) birden fazla ajan veya nesil tarafından ortak kullanılması aşırı felaket unutmasına (catastrophic forgetting) ve ajanın temel akıl yürütme yeteneklerinin bozulmasına yol açar. Birden fazla ajanın farklı yaşantısal izlerinin tek adaptörde toplanması, parametrik çatışmaya (inter-agent parameter interference) sebep olmaktadır.8GB VRAM sınırında (RTX 4070 Laptop) çoklu ajan simülasyonu için Ajan Başına Adaptör (Per-Agent Adapter) mimarisi teknik olarak mümkündür ve uygulanabilirdir. Modern multi-tenant LoRA servis mimarileri (Punica, S-LoRA, SALT) gösteriyor ki, 4-bit kuantize edilmiş dondurulmuş bir temel model (Llama-3.1-8B, ~4.5 GiB VRAM) GPU belleğinde tutulurken, her ajana ait ultra-düşük rütbeli ($r=4$ ila $r=16$) LoRA ağırlıkları VRAM'de yalnızca 10-20 MB ek alan kaplamaktadır. Çıkarım sırasında ilgili ajanın LoRA katmanlarının dinamik olarak çağrılması (adapter switching) 1 ms'nin altında gerçekleşmektedir.Episodik mikro-eğitimde felaket unutmasını önlemek için en etkili prova/tekrarlama (replay/rehearsal) stratejisi Çapa Veri Seti (Anchor Rehearsal) kullanımıdır. Eğitime ajanın yaşadığı deneyimlerin yanı sıra, temel modelin genel yeteneklerini ve format kurallarını koruyan %10-20 oranında sabit genel veri eklenmelidir.Esnek Ağırlık Konsolidasyonu (Elastic Weight Consolidation - EWC), mikro-eğitim ölçeğinde ($N=10\text{--}30$ veri noktası) matris mertebesinde Fisher Bilgi Matrisi hesaplama yükü getirdiği için 8GB VRAM'de verimsizdir. Bunun yerine, kayıp fonksiyonuna eklenen KL-ıraksaması (KL-divergence penalty) veya L2 norm düzenlileştirmesi aynı görevi çok daha az bellek yükü ile yerine getirir.Davranışsal değişimin istatistiksel olarak tespit edilebilir ($\Delta PE$ ayrışması, $p < 0.05$) hale gelmesi için gereken minimum eğitim örneği sayısı ($N$) yapılan güç analizleriyle belirlenmiştir.Eğitim YaklaşımıÖrnek Sayısı (N)İstatistiksel Tespit EdilebilirlikVRAM Süreç MaliyetiKarar / DurumN=1 Smoke (SMOKE_SEPARATION)1 çiftYok (Anlamlılık İddiası Yapılamaz)~33 dkİpuçsal / YetersizN=3 Mini (WEAK_LORA)3 çiftÇok Zayıf / Kararsız~97 dkWEAK_LORA Hyp.N=10-15 Target Protocol C'10-15 çiftYüksek (Paired t-test $p < 0.05$ Gücü)~3.5-5 saatHedef Ölçek[cite: 3]N=40 Extended Horizon40 çiftÇok Yüksek (Doygunluk Riski)Groq TPD SınırıLimit AşımıDAU mimarisine doğrudan çıkarım olarak, tekli paylaşımlı adaptör yerine Punica mimari deseniyle ajan başına bağımsız $r=8$ QLoRA adaptörü tanımlanmalı; istatistiksel geçerlilik için $N \ge 15$ tercih çiftli episodik mikro-eğitim hedeflenmelidir.

### 1.4 Emergent Karakter Özellikleri ve Davranışsal Tutarlılık

LLM tabanlı ajan literatüründe (2023–2025), ajanların deneyim yoluyla tutarlı kişilik özellikleri geliştirip geliştiremediği sorusu kritik bir tartışma konusudur. Generative Agents (Park et al. 2023) çalışmasındaki ajanların tutarlı gibi görünen davranışlarının, aslında yaşantısal plastisiteye değil, sistem istemine enjekte edilen son derece detaylı metinsel karakter tanımlarına (prompt-driven personality) ve anlık bellek getirimine (RAG) dayandığı kanıtlanmıştır. İstemdeki karakter etiketleri çıkarıldığında, ajanların standart temel model davranışlarına geri döndüğü saptanmıştır.Son dönem araştırmalar (Caron & Srivastava, Hartley et al., Bodroža et al., Dubedy 2025), dışarıdan metin olarak enjekte edilen emotion: "anxious" veya cooperation: 0.8 gibi niteliklerin ajanın mantıksal karar verme süreçlerinde sürdürülebilir bir tutarlılık yaratmadığını; bu durumun yüzeysel bir mimetik taklit ile sınırlı kaldığını göstermektedir.İstem enjeksiyonu olmadan çapraz-durumsal (cross-situational) davranışsal tutarlılık sağlayan temel mimari bileşenler şunlardır:Duyusal/Somatik Durum Döngüleri (Somatic Marker Vectors): Damasio'nun Somatik İşaretçi Hipotezi'ne dayanan ve DAU Layer 2'de uygulanan tehdit, ödül, yenilik, sosyal yük ve kayıp boyutlarındaki sayısal bias matrisleri.Allostatic Drift & Dynamic Recovery: Karar uzayını kalıcı olarak kısıtlayan travma birikimi ve DAERM setpoint kaymaları.Parametrik Plastisite (LoRA Adaptörleri): Yaşantının dil modelinin ağırlık dağılımına kazınması.Karakter özelliğinin kararlı hale gelmesi (trait stabilization) için gereken minimum simülasyon uzunluğu, ajanın karşılaştığı olayların çeşitliliğine bağlı olarak en az 30 ila 50 etkileşimsel olay döngüsü ve en az 3 nesil konsolidasyon aşaması gerektirmektedir.DAU mimarisine doğrudan çıkarım olarak, DAU'nun "Bir ajana trait veremezsin, sadece yaşam verebilirsin" temel aksiyomu literatürce tamamen doğrulanmaktadır. Ancak bu yaşamın karakter özelliğine dönüşmesi için somatik işaretçilerin parametrik LoRA güncellemeleri ile mühürlenmesi şarttır.

### 1.5 Konvansiyon ve Restraint (Kısıtlama) Uzlaşısının Ortaya Çıkışı

DAU simülasyonlarında elde edilen bulgu — ajanların biçimsel/dilsel senkronizasyonu (format sync) başarması ancak davranışsal kısıtlamayı / kaynak korumayı (restraint sync) başaramayarak 75/75 oranında iltica (defect) etmesi — LLM multi-ajan literatüründeki temel bir olgu ile tamamen örtüşmektedir.GovSim (Piatti et al. 2024–2026) ve ilişikli Ortak Havuz Kaynakları (Common Pool Resources - CPR) çalışmalarında, açık kanalda iletişim kurabilen LLM ajanlarının retorik seviyede iş birliği mesajları verirken (örneğin "kaynakları korumalıyız" tümcesi kurarak format uyumu göstermeleri), eylem safhasında kendi bireysel kaynak çıkarımlarını maksimumda tuttukları saptanmıştır. Dil modellerinin otoregresif yapısı, bağlamdaki cümle yapısını hızlıca taklit etmelerini (format sync) sağlarken, kısa vadeli çıkarım önceliği davranışsal kısıtlamayı engellemektedir.Literatüre göre yüzeysel uyumun ötesinde gerçek bir davranışsal kısıtlama/iş birliği normunun ortaya çıkabilmesi için şu koşullar gereklidir:Kurumsal/Yaptırım Mekanizmaları: Gruptan aforoz edilme, ceza puanı veya liderlik seçimi (örneğin AgentElect mimarisi).Yüksek Tehdit/Travma Somatik Ağırlığı: Kaynağın çökmesinin ajan üzerinde yıkıcı bir somatik travma ($M_{\text{drift}} \ge 0.7$) oluşturması ve bu durumun ajanın hayatta kalma fitness skorusunu ($F_{\text{agent}}$) doğrudan düşürmesi.Gelecek Sonuçlarını Değerlendirme (Consideration of Future Consequences - CFC): Ajanın anlık çıkarım yerine uzun vadeli tükeniş eğrisini System 2 kognitif modunda simüle etmesi.DAU mimarisine doğrudan çıkarım olarak, sadece serbest iletişim kanalı üzerinden davranışsal kısıtlama (restraint) çıkması beklenmemelidir; GovSim bulgularına paralel olarak, kaynak çöküşü anında Layer 4 ortam fiziğinde ajanlara somatik travma ve cezalandırıcı yaptırım mekanizmaları yüklenmelidir.

### 1.6 Karakter Özelliklerinin Ortaya Çıkışına Yönelik Değerlendirme Metodolojisi

DAU'da kullanılan mevcut MiniLM PE karşılaştırması (lived vs null vs shuffle kolları), ajanın dilsel tepki sapmasını ölçmekte faydalı olsa da, karakter özelliklerinin ortaya çıkışını ve kararlı davranışsal değişimi doğrulamak için tek başına yeterli değildir.LLM ajanlarında istem takibi ile gerçek davranışsal değişimi ayırt eden modern değerlendirme çerçeveleri şunlardır:Çapraz-Bağlamsal Davranışsal Transfer (Cross-Contextual Transfer): Ajanın kaynak yönetimi simülasyonunda edindiği davranışı, hiçbir istem veya bellek ipucu sunulmaksızın tamamen farklı bir sosyal müzakere senaryosunda sergileyip sergilemediğinin ölçülmesi.Eylem Dağılımı Entropisi ($\mathcal{H}(A)$): Ajanın belirli durumlar karşısında aldığı kararların rassal varyasyonunun düşüp düşmediği ve spesifik bir davranışsal desene odaklanıp odaklanmadığı.NLI Kararsal Tutarlılık İndeksi: Ajanın benzer somatik yükler altındayken verdiği kararlar arasındaki mantıksal çelişgisizlik skoru.İstatistiksel güç gereksinimleri açısından, counterfactual paired (eşleştirilmiş) deney tasarımlarında (Protocol C / C'):$$\text{Effect Size } (d) = \frac{\mu_{\text{lived}} - \mu_{\text{null}}}{\sigma_{\text{pooled}}}$$Güç analizi ($1 - \beta = 0.80, \alpha = 0.05$) çerçevesinde, etki büyüklüğü $d = 0.5$ (orta derece etki) için minimum $N = 15$ ila $20$ bağımlı seed çifti gereklidir. $N=1$ (SMOKE_SEPARATION) veya $N=3$ (WEAK_LORA) boyutundaki koşular akademik seviyede istatistiksel iddia taşımamaktadır.Tasarım olarak Seed-Locked Counterfactual (Protocol C) mimarisine alternatif en iyi yaklaşım, Dağılım Dışı Davranışsal Problama (Out-of-Distribution Behavioral Probing) yöntemidir. Bu yöntemde ajan belirli bir yaşantıdan geçirildikten sonra bellek arama bileşenleri (ChromaDB retrieval) tamamen kapatılır ve ajanın sadece ağırlıklarına (LoRA adaptörüne) yansıyan değişim ölçülür.DAU mimarisine doğrudan çıkarım olarak, Protocol C' koşuları $N \ge 15$ seed seviyesine çıkarılmalı ve sadece PE farkı değil, bellek getiriminden bağımsız OOD Davranışsal Transfer skorları ana değerlendirme metriği olarak eklenmelidir.

### 1.7 Mimari Alternatifler ve Derin Kognitif Mekanizmalar

DAU mimarisinin yaşadığı tıkanıklıkları aşmak için literatürde öne çıkan derin kognitif mimariler ve DAU bileşenleri ile karşılaştırmaları aşağıda sunulmuştur:Dünyanın İçsel Modelleri (World Models / Dreamer): Dreamer tarzı yapılar, ortamın durum geçiş dinamiklerini ($s_{t+1} \sim P(s_t, a_t)$) bir gizil uzayda tahmin eder. DAU'daki DAERM (Dynamic Allostatic Equilibrium Recovery Model) ise ajanın içsel fizyolojik/somatik durum gidişatını modeller. Bu iki yapı birbirine rakip değil, tamamlayıcıdır. Hafif bir latent ortam tahminleyicisi ortam tahmini $E(t)$ üretmeli; gerçekleşen $A(t)$ ile farkı PE'yi beslemeli ve PE de DAERM setpoint'lerini ($\mu_i$) kaydırmalıdır.Nörosembolik Mimariler: DAU'nun katmanlı yapısı (Layer 0–4 deterministik Python durum makineleri + Layer 1.5/5 LLM kognisyonu), tam da önerilen nörosembolik sentezdir. Saf LLM tabanlı simülasyonların fizik kurallarını ve kaynak hesaplarını ihlal ettiği kanıtlandığından, DAU'nun deterministik kısıt omurgası (constraints.py, environment.py) korunmalıdır.Gelişmiş Bellek Mimarileri (HippoRAG 2 ve GAAMA): Standart ChromaDB vektör benzerlik aramaları yerine, HippoRAG 2 (ICML 2025) insan hipokampal indeksleme teorisini taklit eden ikili düğümlü (passage + phrase nodes) Açık Bilgi Grafı (OpenIE KG) ve Kişiselleştirilmiş PageRank (Personalized PageRank - PPR) kullanmaktadır. HippoRAG 2, vektör RAG sistemlerine kıyasla çok adımlı çağrışım (associativity) ve bağlam anlama (sense-making) skorlarında 7 puanlık F1 artışı sağlarken, felaket unutmasını engellemektedir.Bağlam-İçi Yaşantıdan Bağlam-Dışı Davranışsal Değişime Geçiş Zinciri, duyusal girdinin değerlendirilmesi, tercih çiftlerinin oluşturulması, episodik QLoRA ile parametrik ağırlıklara yazılması ve bellek bileşenleri kapalıyken dağılım dışı kısıtlama kararlılığının ölçülmesi adımlarından oluşur.DAU mimarisine doğrudan çıkarım olarak, DAU SQLite alan eş-oluşum grafı, HippoRAG 2 benzeri Kişiselleştirilmiş PageRank (PPR) algoritması ile güçlendirilmeli; ChromaDB tek başına tekil vektör deposu seviyesine indirgenmelidir.

## 2. Sentez: DAU Mimarisine Yönelik Doğrulamalar ve Yanlışlamalar

Literatür taraması ve mevcut deneysel bulgular ışığında, DAU mimari kararlarının doğruluk ve yanlışlık matrisi detaylandırılmıştır.DAU'nun birinci temel aksiyomu olan Trait Enjeksiyon Yasağı, Caron & Srivastava, Dubedy (2025) ve Park et al. (2023) çalışmalarındaki bağımsız bulgularla kesin olarak doğrulanmaktadır. İstem seviyesinde metin olarak enjekte edilen karakter özelliklerinin ajanın mantıksal kararlarını kalıcı olarak değiştiremediği, yalnızca yüzeysel bir mimetik taklit ürettiği sabittir. Benzer şekilde, Layer 0–4 aralığındaki deterministik Python durum makinesi omurgası, nörosembolik mimarlık ilkeleriyle tam bir uyum sergilemektedir. Kaynak fiziğinin ve fizyolojik allostatic setpoint recovery (DAERM) mekanizmasının deterministik kod olarak korunması, stokastik dil modellerinin fiziksel ihlallerini engellemektedir. Ayrıca per-event online güncellemeler yerine episodik nesil-sonu mikro-eğitimi yaklaşımı (Generation-End Micro QLoRA), parametrik kararlılık açısından literatürce desteklenmektedir.Buna karşın, dondurulmuş ağırlıklar altında kapalı döngü metakognisyon geliştirme beklentisi (Layer 5 Meta-Observer) Protocol C sonuçlarıyla kesin olarak yanlışlanmıştır. Parametrik plastisite olmadan yalnızca bağlam içi bellek müdahalelerinin kararsal delta üzerinde iyileşme yaratmadığı ($\Delta PE \approx 0$) ve kapalı döngü öğrenmeyi sağlayamadığı paper-locked bir negatif bulgu olarak tescillenmiştir. İkinci olarak, tekil MiniLM kosinüs benzerliğine dayalı PE sensörünün kararsal zıtlıkları ve polarity değişimlerini ayırt edemediği anlaşılmıştır. Son olarak, serbest iletişim kanalında ajanların kendiliğinden davranışsal kısıtlama (restraint sync) geliştireceği hipotezi GovSim bulgularıyla yanlışlanmıştır; harici yaptırım ve yüksek somatik travma olmadan otoregresif dil modellerinin iltica eğilimini sürdürdüğü görülmüştür.DAU Hipotezi / Mimari BileşenDeneysel DurumLiteratür HükmüMimari Karar / YönelimTrait Enjeksiyon Yasağı (Aksiyom 1)DoğrulandıKesin Doğrulamaİstemle trait tanımlama yasaktır; yaşantısal plastisite şarttır.Deterministik State Machine (Layer 0-4)DoğrulandıKesin DoğrulamaNörosembolik omurga korunacak; LLM-as-judge kullanılmayacaktır.Dondurulmuş Ağırlıklı MetakognisyonYanlışlandıProtocol C Null (Locked)Dondurulmuş ağırlık kapalı döngü kuramaz; LoRA zorunludur.MiniLM Kosinüs PE SensörüYanlışlandıYetersiz SinyalMiniLM tek başına yetersizdir; Sinyal v2 tercih çiftleri eklenecektir.Serbest Kanalda Restraint EmergenceYanlışlandıGovSim ParalelliğiCeza ve somatik yaptırım olmadan kısıtlama çıkmaz (75/75 defect).

## 3. Öncelikli Mimari Öneriler ve Uygulanabilirlik Analizi

DAU simülasyon sisteminin mevcut kilitlenmelerini aşmak için RTX 4070 Laptop 8GB VRAM ve Groq ücretsiz tier kısıtları dahilinde uygulanabilecek en öncelikli 4 mimari değişiklik aşağıda detaylandırılmıştır.

### Öneri 1: Sinyal v2 Tercih Çiftleri (PE-Ranked Preference Pairs) ve Unlikelihood Kayıp Fonksiyonu Değişimi

MiniLM tekil PE skoru yerine, ajanın anlık beklenen çıktısı altında ürettiği eylem alternatifleri MiniLM + NLI zıtlık filtresinden geçirilerek tercih çiftleri ($PE_{\text{chosen}} < PE_{\text{rejected}}$) oluşturulmalıdır. Eğitim aşamasında standart Causal LM Cross-Entropy yerine Unlikelihood Tercih Kaybı ($L = \text{CE}_{\text{chosen}} - 0.5 \cdot \text{CE}_{\text{rejected}}$) uygulanmalıdır. Bu yaklaşım PoT (Policy of Thoughts 2026) ve DPO ilkeleriyle tamamen uyumludur. RTX 4070 8GB VRAM üzerinde %100 uygulanabilir durumdadır; Sinyal v2 kablosu kodlanmış (lora_update.py) ve tek seed SMOKE_SEPARATION koşusunda $\Delta PE_{\text{lived}} \approx -0.026$ ile doğru yön sinyali elde edilmiştir.

### Öneri 2: Punica / S-LoRA Desenli Ajan Başına Bağımsız Ultra-Düşük Düzeyli QLoRA Adaptörleri

Tüm ajanların tek bir LoRA adaptörünü paylaşması yerine, her ajana özel bağımsız $r=8, \alpha=16$ QLoRA adaptör dizini tanımlanmalıdır. Llama-3.1-8B temel modeli 4-bit (NF4) olarak GPU'da dondurulmuş tutulurken, çıkarım sırasındaki ajanın adaptörü belleğe dinamik olarak aktarılmalıdır. Punica, S-LoRA ve SALT multi-tenant LoRA servis mimarileri bu yöntemin başarısını kanıtlamıştır. Llama-3.1-8B 4-bit taban modeli ~4.5 GiB VRAM kaplamakta, 3 ajana ait adaptörler ise toplamda 45 MB ek yük getirmektedir. Toplam VRAM kullanımı ~6.5 GiB seviyesinde kaldığından RTX 4070 8GB sınırları dahilindedir.

### Öneri 3: HippoRAG 2 Tarzı Graf-Kişiselleştirilmiş PageRank (PPR) Bellek Arama Motoru

ChromaDB saf kosinüs vektör araması, DAU SQLite alan eş-oluşum grafı üzerinde çalışan Kişiselleştirilmiş PageRank (PPR) algoritması ile birleştirilmelidir. Bellekten geçmiş çağrışımlar getirilirken doğrudan kelime/vektör benzerliği değil, yaşantısal graf üzerindeki olasılıksal yayılım esas alınmalıdır. HippoRAG 2 (ICML 2025) mimarisini temel alan bu yapı, tamamen NetworkX / SciPy veya saf Python ile CPU üzerinde deterministik olarak çalıştırılabilir; GPU VRAM üzerinde sıfır ek maliyet oluşturur.

### Öneri 4: Layer 4 Ortam Fiziğine Somatik Yaptırım ve Kurumsal Yönetişim Ekleme

Serbest kanalda kısıtlama (restraint sync) ortaya çıkmadığı için, kaynak seviyesi kritik eşiğin altına indiğinde ($P_{\text{pool}} < 0.30$) ajanların $M_{\text{drift}}$ travma birikimi katlanarak artırılmalı ve bu durum $F_{\text{agent}}$ fitness skorlarına cezalandırıcı olarak yansıtılmalıdır. Ayrıca oy çokluğuyla aforoz veya ceza mekanizması eklenmelidir. GovSim takip çalışmaları ve AgentElect (2026) bulguları bu yaptırımların zorunluluğunu ortaya koymaktadır. Değişiklik tamamen Layer 4 Python kodunda (environment.py, social.py) kural düzenlemesi gerektirdiğinden VRAM ve token maliyeti sıfırdır.Değişiklik ÖnerisiHedeflenen BlockerVRAM Maliyetiİcralık / FizibiliteÖneri 1: Sinyal v2 Preference PairsPE Geçerliliği & Zayıf Signal (Tier 2-E, 3-F)0 MB Ek MaliyetHazır / Test EdilecekÖneri 2: Punica Per-Agent AdaptersParametrik Plastisite & Felaket Unutması (Tier 1-A)~45 MB (3 Ajan)Mimariye EklenecekÖneri 3: HippoRAG 2 PPR EngineBağlam İçi Bellek Etkisizliği (Tier 2-C)0 MB (CPU Çalışır)Mimariye EklenecekÖneri 4: Yaptırımlı Kurum FiziğiRestraint Uyumsuzluğu (GovSim Bulgu 4)0 MB (Python Rule)Mimariye Eklenecek

## 4. Açık Araştırma Soruları

Mevcut literatür ve deneysel çalışmalara rağmen henüz bilimin kesin yanıt üretemediği ve DAU projesinin ön safhada araştırabileceği açık alanlar şunlardır:Ultra-Düşük Dereceli (Ultra-Low Rank $r \le 4$) Adaptörlerin Sıfır-Toplamlı Karar Alanlarındaki Limitleri: Küçük boyutlu adaptörlerin temel modelin genel dil yeteneklerini bozmadan spesifik kararsal stratejileri ne kadar süreyle saklayabileceği sınırları ve kapasite doygunluk noktaları netleşmemiştir.Endojen Yaşantısal Allostasis ile Sinaptik Plastisite Arasındaki Dinamik Rezonans: DAERM allostatic setpoint kaymaları ile QLoRA matris gradyanları arasındaki matrisel hiyerarşinin teorik optimal dengesi ve somatik kısıtların gradyan adımlarına nasıl yön vermesi gerektiği henüz formüle edilmemiştir.Açık Kaynak 8B Modellere Özgü "Restraint Collapsibility" Sınırı: Büyük modellerin (GPT-4o, DeepSeek-V3) kurumsal yönlendirmeyle kaynak koruma dengesi kurabildiği görülürken, 8B ölçeğindeki açık modellerin kaç nesil sonra ve hangi somatik ceza katsayısında davranışsal kısıtlama mühürlemesini başarabileceği sorusu açık kalmaya devam etmektedir.
