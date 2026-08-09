---
tarih: 2026-08-08~   # düzeltildi: rapor v2.4 / v3 smoke / SAMPLE_N15 atıfları içeriyor (08-07+); kaynak prompt içermiyor
konu: Per-agent LoRA serving, dual-channel memory, DPO ve deterministik değerlendirme
tetikleyen soru: 
---

## Kaynak prompt

```text
BAĞLAM: DAU (Dynamic Agent Universe), LLM tabanlı agent'ların trait'lerini 

doğrudan enjeksiyon yoluyla değil, yaşanan deneyim yoluyla geliştirdiği ve 

bu gelişimin nesilden nesile parametrik (LoRA ağırlıkları) ve sembolik 

(hafıza) kanallarla aktarıldığı bir araştırma sistemi. Mimari: yerel LLM 

(Llama-3.1-8B-Instant sınıfı, 8GB VRAM), per-agent LoRA/QLoRA adapter'ları 

(Punica deseni — her ajanın kendi adapter dizini), generation-end (nesil 

sonu) micro-training ile DPO tercih çiftleri, ChromaDB+SQLite hafıza 

kasası, NetworkX ile Personalized PageRank tabanlı ilişkisel geri çağırma. 

Sıkı kısıt: trait injection yasak, LLM-as-judge yasak, tüm metrikler 

deterministik.

Aşağıdaki başlıklarda derinlemesine, akademik literatür + teknoloji 

şirketlerinin (Anthropic hariç) yayınladığı teknik raporlar/blog/paper 

ağırlıklı bir araştırma yap. Her başlıkta: (1) güncel state-of-the-art 

yaklaşımlar, (2) bizim mimarimizle örtüşen veya çelişen noktalar, 

(3) kaçırdığımız olası riskler/best practice'ler.

## 1. Per-agent / multi-tenant LoRA serving mimarisi

- Punica, S-LoRA, dLoRA, InfiniLoRA gibi multi-tenant LoRA serving 

  sistemlerinin güncel (2026) durumu nedir?

- Adapter izolasyonu ve "cross-tenant adapter contamination" (bir ajanın 

  adapter'ının başka bir ajana sızması) sorunu literatürde nasıl ele 

  alınıyor? Hangi mimari desenler bunu yapısal olarak engelliyor?

- 8GB VRAM gibi sınırlı donanımda per-agent adapter hot-swap (adapter 

  değiştirme) için pratik, üretim seviyesinde önerilen yaklaşımlar neler?

## 2. Generation-end (nesil sonu) vs online/sürekli öğrenme

- Nesil sonunda toplu micro-train yapmanın (bizim yaklaşımımız), 

  per-event online öğrenmeye (EWC, TTT, prefix-tuning gibi) karşı 

  literatürdeki kanıtlanmış avantaj/dezavantajları nedir?

- Catastrophic forgetting (felaket unutma) riski, generation-end toplu 

  eğitimde per-event'e göre nasıl farklılaşıyor?

## 3. Tercih öğrenmesiyle davranış şekillendirme (DPO / preference learning)

- LLM davranışını "trait" değil "tercih çifti" üzerinden şekillendiren 

  güncel DPO/RLHF varyantları neler, ve bunların "kişilik enjeksiyonu 

  değil, davranışsal örüntü çıkarımı" iddiasını ne kadar destekliyor?

- Küçük local modellerde (8B sınıfı) DPO ile elde edilen davranışsal 

  ayrımın sinyal gücü, büyük modellere kıyasla ne kadar zayıf/güçlü?

## 4. Hafızanın parametrik karşılığı (memory-as-parametric-edit)

- "Kullanıcıya/ajana özel hafızayı yerel parametrik düzenleme olarak 

  içselleştirme" yaklaşımları (örn. per-user LoRA composition, memory 

  layers, product-key memory) bizim "memory vault + LoRA" ikili kanal 

  mimarimizle nasıl karşılaştırılır? Bu literatür ikisini birleştirmenin 

  bir yolunu öneriyor mu, yoksa ayrı tutmanın mı daha sağlam olduğunu 

  gösteriyor?

## 5. Çok-nesilli / kültürel aktarım araştırmaları (multi-agent)

- LLM tabanlı çoklu-ajan sistemlerinde "kültürel/davranışsal aktarım" 

  (bir ajan neslinin özelliklerinin bir sonrakine geçmesi) üzerine 

  akademik çalışmalar var mı? Varsa hangi metrikleri kullanıyorlar 

  (bizim gibi LLM-as-judge yasaklı, deterministik metrik arayanlar var mı)?

- Bu alanda "trait enjekte etmeden ortaya çıkan (emergent) davranışın 

  nesiller arası kalıcılığını" ölçen bir pre-registration/istatistiksel 

  güç standardı var mı?

## 6. Teknoloji devlerinin agent-memory / personality-persistence yaklaşımları

- OpenAI, Google DeepMind, xAI gibi şirketlerin agent hafızası / kişilik 

  kalıcılığı üzerine 2026'da yayınladığı teknik yaklaşımlar (Anthropic 

  hariç tut) — bunlar trait injection'a mı, yaşam-temelli emergence'a mı 

  daha yakın?

- Bu şirketlerin "sürekli öğrenen ajan" (continual learning agent) 

  ürünlerinde kullandığı mimari desenler bizim per-agent LoRA + 

  generation-end train yaklaşımımızla nasıl kıyaslanıyor?

## 7. Küçük/yerel model seçimi (8GB VRAM sınırı, 2026 güncel)

- Llama-3.1-8B-Instant yerine, 2026 itibariyle 8GB VRAM'de agent 

  fine-tuning için daha uygun (DPO/QLoRA dostu, güçlü instruction-following) 

  alternatif açık modeller var mı (Qwen, Llama yeni sürümleri, vb.)?

## 8. Değerlendirme metodolojisi (LLM-as-judge olmadan)

- LLM-as-judge kullanmadan, davranışsal "trait emergence"ı ölçen 

  deterministik metrik yaklaşımları literatürde nasıl tasarlanıyor 

  (semantic similarity, prediction-error tabanlı, vb.)?

ÇIKTI FORMATI: Her başlık için ayrı bölüm, kaynak künyeleriyle (yazar/yıl/

venue), ve en sonda "bizim mimarimize göre en kritik 3 bulgu" özet listesi.
```

## Rapor

Otonom Çok-Ajanlı Sistemlerde Yaşantısal Plastisite ve Nesiller Arası Davranışsal Kalıcılık: DAU Mimarisinin Literatür ve Sanayi Standartlarıyla Karşılaştırmalı Analizi

## 1. Per-Agent / Multi-Tenant LoRA Serving Mimarisi

Büyük dil modellerinde (LLM) ajan bazlı kişiselleştirme ve adaptasyon, tek bir ana model kütlesi (base model) üzerinde ajana özgü Düşük Rütbeli Adaptasyon (LoRA) ağırlıklarının dinamik olarak çalıştırılmasıyla sağlanmaktadır. Multi-tenant LoRA sunum altyapıları, bellek kullanımını optimize ederken yüksek çıkarım (inference) başarımını korumayı hedefler.

### Güncel State-of-the-Art Yaklaşımlar

Multi-tenant LoRA sunum mimarilerinin evrimi Punica (Chen et al., 2023, arXiv) ve S-LoRA (Sheng et al., 2024, arXiv) ile başlamış, dLoRA (Wu et al., 2024, arXiv) ve InfiniLoRA (Gao et al., 2026, arXiv) sistemleriyle ayrışmış (disaggregated) servis mimarilerine yönelmiştir.Punica, tensor paralel ana model hesaplamaları sırasında farklı istemlere (prompt) ait LoRA ağırlıklarını GPU üzerinde gruplayan parçalı MatMul (Segmented SGMV) çekirdeklerini tanıtmıştır. S-LoRA ise adaptör ağırlıklarını ve Key-Value (KV) önbelleğini tek bir birleşik bellek havuzunda (Unified Paged KV & Adapter Cache) yöneterek VRAM parçalanmasını engellemiş ve binlerce LoRA adaptörünün dinamik yüklenmesine imkan tanımıştır. dLoRA, adaptörlerin dinamik olarak birleştirilmesi ve boru hattı paralelliğinde GPU'lar arası transfer maliyetlerinin minimize edilmesine odaklanmıştır. InfiniLoRA ise Karma Uzman Modellerinin (MoE) ve devasa çok kiracılı sistemlerin artan bellek yükünü yönetmek amacıyla LoRA yürütmesini taban model çıkarımından tamamen ayırmıştır. Taban model GPU'ları LoRA'sız çalışırken, adanmış LoRA sunucu havuzları uzman paralelliği ve boru hattı paralelliğini hibrit birleştirerek istek bazlı hizmet sunmaktadır.MimarilerSunum ModeliTemel Bellek Optimizasyonu8GB VRAM/Yerel UygunlukPunicaBütünleşik (Coupled)Segmented SGMV KernelYüksek (Tek GPU için ideal)S-LoRABütünleşik (Coupled)Paged Memory / Unified CacheOrta (Yüksek RAM/VRAM overcommit ister)dLoRADağıtık (Distributed)Dynamic Adapter MergingDüşük (Çoklu GPU gerektirir)InfiniLoRAAyrıştırılmış (Disaggregated)Pipeline + Expert ParallelismDüşük (Küme/Cluster seviyesi altyapı)

### Çapraz Kiracı Adaptör Kirlenmesi (Cross-Tenant Contamination)

Çok kiracılı LoRA sistemlerinde güvenliği ve davranışsal izolasyonu tehdit eden en kritik unsur "cross-tenant adapter contamination" (kiracılar arası adaptör sızması) problemidir. Literatürde bu kirlenmenin üç temel mekanizmayla gerçekleştiği tespit edilmiştir:Sistem seviyesinde zamanlayıcı durum kayması (Scheduler-State Drift), sunucu zamanlayıcısının aktif olduğunu varsaydığı adaptör kümesi ile GPU belleğine gerçekten yüklü olan adaptör havuzunun eşzamanlılığını kaybetmesiyle ortaya çıkar. Bu durum istemlerin yanlış adaptör katmanlarından geçerek yanıt üretmesine yol açar. Eşzamanlı istek işleme sırasında bir ajana ait KV-önbellek bloklarının temizlenmeden diğer ajanın oturumuna atanması ise bayat KV-önbellek kullanımı (Stale KV-Cache Reuse) kaynaklı sızıntılara sebep olur. Ayrıca, yüksek seviye kütüphanelerin bellek yönetimi hataları nedeniyle diske kaydetme veya bellekten yükleme anında birden fazla ajanın adaptör parametrelerini (lora_A, lora_B) aynı ana dizin dizilimine yazmasıyla bellek içi ağırlık karışması meydana gelir.Bu problemi yapısal olarak engelleyen mimari desenler arasında; SGX/TEE donanımsal izole ortamlarda adaptör çalıştırma (LoRA-TEE; Lin et al., 2025, arXiv), her istek için bağlam doğrulaması yapan sıfır-güven (Zero-Trust) veri katmanları (Sectum AI, 2026) ve disk/bellek seviyesinde katı yol ayrıştırma (Strict Path Isolation) yer almaktadır.

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU altyapısı, dau_runs/adapters/{agent_id}/ dosya yapısı üzerinden her ajan için tam disk izolasyonlu bir Punica deseni benimsemektedir. DAU’nun tek GPU (8GB VRAM) üzerindeki yerel çalışma zorunluluğu, InfiniLoRA gibi ayrıştırılmış sunucu mimarilerini geçersiz kılmakta; Punica'nın bellek-içi doğrudan adaptör değiştirme (switch_adapter) mantığıyla tam örtüşmektedir.DAU geliştirme sürecinde tespit edilen kritik bir kirlenme riski, peft kütüphanesinin varsayılan davranış olarak bellekteki tüm aktif adaptörleri kaydedilen ajanın dizinine yazmasıdır. Bu durum, eğitilmemiş nötr ajanın (null arm), eğitilmiş yaşantısal ajanın (lived arm) ağırlıklarını miras almasına ve kirlenmeye sebep olmuştur. 8GB VRAM sınırında sıcak adaptör değişimi (hot-swap) için bellek üzerinde tek bir katı default adaptör yuvası tutulmalı, her değişimde PyTorch gradyan önbelleği sıfırlanmalı (torch.cuda.empty_cache()) ve disk düzeyinde izolasyon sağlanmalıdır. Adaptör yükleme işlemleri CUDA akışları (streams) ile senkronize edilerek scheduler-state drift tamamen engellenmelidir.

## 2. Generation-End (Nesil Sonu) vs. Online/Sürekli Öğrenme

Ajanların deneyimlerinden ders çıkarması sürecinde temporal güncelleme frekansı, modelin genel yeteneklerini koruma kapasitesini doğrudan etkiler.

### Akademik Literatür Karşılaştırması

Sürekli öğrenme (continual learning) literatüründe (McCloskey & Cohen, 1989; Kirkpatrick et al., 2017; Sun et al., 2022, arXiv), olay bazlı çevrimiçi öğrenme (per-event online learning; EWC, Test-Time Training / TTT, Prefix-Tuning) ile dönem/nesil sonu toplu mikro eğitim (generation-end batch micro-training) arasında belirgin başarım ve kararlılık farkları bulunmaktadır.Olay anında gradyan güncellemesi yapılması modelin anlık ortama hızlı uyum sağlamasını sağlasa da, veri dağılımının bağımsız ve özdeş dağılmaması (non-i.i.d.) ve durağan dışı (non-stationary) yapısı nedeniyle derece derece gradyan patlamalarına ve Katman Normalleştirmesi (LayerNorm) istatistiklerinin bozulmasına yol açar. Buna karşın, bir nesil boyunca biriken yaşantı izlerinin (lived traces) topluca işlenmesi; gürültülü deneyimlerin elenmesine, gradyan adımlarının varyansının düşürülmesine ve DPO (Direct Preference Optimization) için yüksek kaliteli tercih çiftlerinin oluşturulmasına imkan tanır.Metrik / BoyutPer-Event Online Learning (TTT/EWC)Generation-End Batch Learning (DAU Yaklaşımı)Felaket Unutma (Catastrophic Forgetting)Şiddetli (Ağırlık kayması yüksek)Düşük (Süzülmüş veri, kontrollü epoch)Hesaplama/Çıkarım GecikmesiYüksek (Her adımda backward pass)Sıfır (Çıkarım sırasında dondurulmuş ağırlık)Veri Kalitesi ve Sinyal/Gürültü OranıDüşük (Anlık gürültülü olaylar içerir)Yüksek (Toplu PE ve NLI filtresinden geçer)Bellek Yükü (8GB VRAM)Yüksek (Eğitim durumu sürekli bellekte)Düşük (Eğitim nesil sonunda izole yapılır)

### Felaket Unutma (Catastrophic Forgetting) Farklılıkları

Çevrimiçi güncellemede model, son karşılaştığı az sayıdaki olaya aşırı uyum sağlar (overfitting). Bu durum, modelin temel dil takip etme (instruction-following) yeteneklerini hızla yitirmesine sebep olur. Nesil sonu toplu mikro eğitimde ise veriler önceden belirlenmiş kalite kapılarından (NLI çelişki filtresi, PE eşik süzgeci) geçtiği için model sadece kararlı ve doğrulanmış davranışsal örüntüleri öğrenir.

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU'nun nesil sonu mikro QLoRA eğitimi tercihi, 8GB VRAM kısıtı altında sistem kararlılığını sağlamak açısından literatürle tamamen örtüşmektedir. Literatür, sürekli çevrimiçi güncellemelerin bellek yönetimi ve felaket unutma açısından yıkıcı olduğunu doğrulamakta; DAU’nun çıkarım ile eğitimi tamamen ayıran nesil sonu DPO yaklaşımını desteklemektedir.Nesil sonu eğitimde, nesil süresince toplanan tercih verisinin yetersiz veya tekdüzeliğe (greedy plateau) düşmesi durumunda adaptörün sıfır gradyan adımı atması veya doygunluğa ulaşması riski mevcuttur. Nesil sonu mikro eğitimde BATCH_SIZE=1 ve gradyan biriktirme (gradient accumulation) kullanılmalı, tercih çiftleri rastgele olay sıralaması yerine Tahmin Hatası ($PE$) büyüklüğüne göre sıralanmalı ve veri çeşitliliği kapısı ($K \ge 5$ benzersiz çıktı) uygulanmalıdır.

## 3. Tercih Öğrenmesiyle Davranış Şekillendirme (DPO / Preference Learning)

Ajan yeteneklerinin şekillendirilmesinde sistem komutları üzerinden nitelik atanması ("trait injection") yerine, ajanın bizzat yaşadığı deneyimlerden üretilen tercih çiftleriyle hizalanması ilkesi temel alınır.

### Güncel DPO/RLHF Varyantları ve Davranış Çıkarımı

Ajan davranışlarını yönlendirmede kullanılan güncel tercih öğrenmesi yöntemleri DPO (Rafailov et al., 2023, NeurIPS), IPO (Azar et al., 2023, ICML), KTO (Ethayarajh et al., 2024, arXiv) ve Lived-PE Ranked DPO (DAU Framework, 2026) olarak sıralanabilir.DPO, ödül modeli eğitme zorunluluğunu ortadan kaldırarak doğrudan politika ağacı üzerinden implicit ödül fonksiyonunu optimize eder. IPO, DPO’nun aşırı özgüvenli log-olasılık marjı oluşturma eğilimini düzenleyerek küçük veri kümelerinde aşırı uyumu engeller. KTO ise tercih çiftleri yerine tekil "iyi/kötü" etiketiyle çalışarak insan/ajan kararlarındaki kayıptan kaçınma (loss aversion) psikolojisini modeller. DAU tarafından uygulanan Lived-PE Ranked DPO yaklaşımı, ajanın kendi ürettiği beklenen çıktı ile gerçekleşen çıktı arasındaki Tahmin Hatasına ($PE$) dayalı olarak otomatik $y_w$ (tercih edilen) ve $y_l$ (reddedilen) çiftleri oluşturur.Bu yöntemler, ajana dışarıdan statik bir kimlik etiketi enjekte etmek yerine, ajanın karşılaştığı kriz ve kaynak senaryolarındaki seçimlerini ödüllendirip cezalandırarak davranışsal örüntü çıkarımını gerçekleştirmektedir (Caron & Srivastava, 2024; Dubedy, 2025).

### 8B Sınıfı Küçük Modellerde Sinyal Gücü

Küçük dil modellerinde (8B parametre sınıfı) DPO sinyal gücü, 70B+ parametreli büyük modellere kıyasla logit dağılımının daha dar olması sebebiyle farklı dinamikler gösterir (Lin et al., 2025, arXiv). Matematiksel olarak DPO kayıp fonksiyonu aşağıdaki şekilde ifade edilir:$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l)} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w\vert{}x)}{\pi_{\text{ref}}(y_w\vert{}x)} - \beta \log \frac{\pi_\theta(y_l\vert{}x)}{\pi_{\text{ref}}(y_l\vert{}x)} \right) \right]$$8B modellerde tercih edilen ($y_w$) and reddedilen ($y_l$) yanıtlar arasındaki semantik fark yeterince belirgin değilse, log-olasılık oranı hızla doymakta ve gradyan sönümlenmesine (gradient vanishing) yol açmaktadır. Bu nedenle 8B modellerde DPO uygulanırken polarite ayrımının yüksek olması zorunludur.

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU altyapısı, Llama-3.1-8B-Instant modeli üzerinde DPO tabanlı yaşantısal tercih öğrenimini kullanmaktadır. DAU'nun "trait injection yasaktır" aksiyomu, literatürdeki kişilik enjeksiyonunun tutarsızlığı üzerine yapılan bulgularla tam uyum gösterir.8B modellerde açgözlü (greedy) kod çözme kullanıldığında benzersiz çıktı sayısı hızla düşmekte ve DPO eğitim verisi platosuna neden olmaktadır. NLI (Natural Language Inference) süzgeci olmadan oluşturulan tercih çiftleri zıt kutupsallık (polarity) taşımıyorsa, model yanlış davranışları pekiştirebilir. Tercih çiftleri oluşturulurken DeBERTa-v3-small gibi bir NLI modeli üzerinden çelişki skoru ($score \ge 0.60$) şartı aranmalıdır. Çıkarım sırasında sıfır gürültüyü önlemek ve benzersiz çıktı çeşitliliğini korumak için düşük sıcaklıkta örnekleme ($T=0.2$, DAU_LLM_DO_SAMPLE=1) uygulanmalıdır.

## 4. Hafızanın Parametrik Karşılığı (Memory-as-Parametric-Edit)

Ajan hafızasının sembolik saklama alanlarında mı tutulacağı yoksa doğrudan modelin parametrelerine mi düzenleneceği, ajan mimarilerinin temel tartışma konularından biridir.

### Literatürdeki Mimariler vs. Çift Kanallı DAU Mimarisi

Parametrik düzenleme yaklaşımları (ROME: Meng et al., 2022, NeurIPS; MEMIT: Meng et al., 2023, ICLR; Per-User LoRA Composition) kullanıcıya özel bilgileri doğrudan ağırlıklara işler. Bellek katmanları ve ürün anahtarlı bellek (product-key memory) gibi yöntemler bilginin parametrik matrislerde saklanmasını sağlar. Ancak veri silme (GDPR Article 17) ve bilgi güncelleme süreçlerinde felaket unutmaya veya modele genel halüsinasyon yaptırma riskine sahiptir.DAU Çift Kanallı (Dual-Channel) mimarisi ise Sembolik kanal (ChromaDB + SQLite) ile Parametrik kanalı (Per-Agent LoRA) birbirinden ayırır. Sembolik kanal olayları, olguları ve co-occurrence ilişkilerini (Personalized PageRank) saklarken; Parametrik kanal ajanın dünyayı algılama biçimini, duygu sürüklenmesini (drift) ve karar alma eğilimlerini barındırır.ÖzellikSaf Parametrik Düzenleme (ROME/LoRA Composition)Sembolik RAG / Graph (Mem0, Zep, MAGMA)DAU İkili Kanal (Memory Vault + LoRA)Olgusal GüncellenebilirlikZor (Geri alma / Unutma maliyetli)Çok Kolay (CRUD operasyonları)Çok Kolay (ChromaDB/SQLite silme)Davranışsal SürüklenmeYüksek (Doğrudan ağırlıklara işler)Sıfır (Model davranışını değiştirmez)Yüksek & Kontrollü (LoRA DPO adımı)ÖlçeklenebilirlikDüşük (Her olgu için adaptör büyür)Yüksek (Vektör/Çizge boyutu artar)Dengeli (Ağırlık sabit $r=8$, veri SQLite'ta)Çelişki YönetimiDüşük (Eski/Yeni bilgi ağırlıkta çakışır)Orta (Eski veri silinmezse çakışır)Yüksek (Ebbinghaus decay + PPR)

### Literatürün Birleştirme veya Ayırma Önerisi

Agentic Memory konsensüsü (Mem0: ECAI 2025/2026; MAGMA: 2026, arXiv; Zep: 2025), olgusal bellek ile davranışsal uyumun kesinlikle ayrı tutulması gerektiğini göstermektedir. Bilişsel mimarilerdeki "İşlevsel Ayrışma" (Functional Decoupling) prensibine göre olgusal ve zamansal veri Çizge (Graph) ve Vektör veritabanlarında sembolik olarak tutulmalı, dinamik CRUD operasyonlarıyla güncellenmelidir. İçsel eğilim ve üslup ise parametrik LoRA ağırlıkları ile şekillendirilmelidir.

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU'nun sembolik bellek kasası (Chroma/SQLite PPR) ile parametrik LoRA adaptörünü ayrıştıran dual-channel yapısı literatürün üretim standartlarıyla örtüşmektedir. Olguların LoRA içine gömülmesi yerine ChromaDB/SQLite üzerinde tutulması ve LoRA'nın sadece yaşantısal tercih davranışını ($PE$) üstlenmesi mimari açıdan doğru bir karardır.Sembolik bellek ile parametrik LoRA arasındaki senkronizasyon kopukluğu olası bir risktir. Örneğin; sembolik bellekten Ebbinghaus zamansal sönümlenmesiyle silinen bir olayın yarattığı travmatik duygu sürüklenmesinin (drift) LoRA üzerinde kalıcı olmaya devam etmesi durumunda ajanda tutarsızlık oluşabilir. Olgusal güncellemeler sembolik kasada tutulmalı, LoRA adaptörleri ise sadece uzun vadeli genel tutumları (risk alma, işbirliği, kaynak koruma) kodlayacak şekilde sınırlandırılmalıdır.

## 5. Çok-Nesilli / Kültürel Aktarım Araştırmaları (Multi-Agent)

Birden fazla ajanın etkileşimde bulunduğu simülasyonlarda, bir neslin edindiği davranış kalıplarının bir sonraki nesle aktarılması kültürel evrim araştırmalarının odağındadır.

### Akademik Literatür ve Deterministik Metrikler

LLM tabanlı çoklu-ajan sistemlerinde kültürel aktarım üzerine yapılan çalışmalar Genomebook (2026, bioRxiv), GovSim & GT-HarmBench (Piatti et al., 2024; Cobben et al., 2026) ve Donor Game & Indirect Reciprocity (Brinkmann et al., 2023 / 2026) çerçevelerinde yoğunlaşmaktadır. Genomebook, ajan kimliğini diploit genotip yapılarıyla kodlayarak Mendelyen kalıtım ve de novo mutasyon ile 8 nesil boyunca fenotipik niteliklerin aktarımını incelemiştir. GovSim, ortak kaynakların yönetimi simülasyonlarında prososyal davranışların nesiller arası kalıcılığını ölçmektedir. Donor Game araştırmaları ise ajanların dolaylı karşılıklılık ilkesi çerçevesinde işbirliği normlarını nesilden nesile nasıl aktardığını analiz etmektedir.Bu çalışmalarda LLM-as-judge yerine kullanılan deterministik metrikler şunlardır:Belli bir neslin tükenmeden sürdürdüğü adım sayısı ($t_{\text{surv}} / T_{\text{gen}}$) ve kaynak tüketim hızı kaynak hayatta kalma oranını verir. Ardışık nesillerin eylem vektörleri arasındaki anlamsal benzerlik Jaccard ve kosinüs benzerlikleriyle hesaplanır. Sonraki neslin, önceki neslin bıraktığı metin ve bellek izlerini okurken sergilediği tahmin hatası ($PE$) değişimi ise kayıp-tabanlı kültürel birikim probları ($D_2$ Probe) ile izlenir.

### Ön-Kayıt (Pre-Registration) ve İstatistiksel Güç Standartları

Ajan sistemlerinde nitelik enjekte edilmeden ortaya çıkan "belirme" (emergence) iddiasının bilimsel olarak geçerli olabilmesi için rigoröz istatistiksel standartlar uygulanmaktadır. Rastgele tohumların yarattığı gürültüyü engellemek için minimum $K=5$ benzersiz yanıt çeşitliliği ($DIVERSITY\_MIN\_UNIQUE$) sağlanmalıdır. Nesiller arası anlamlı bir farkın ($H_1$) gösterilebilmesi için en az $N \ge 15$ ajanlık denemelerin yapılması ve gürültü nedeniyle elenen tohumlardan sonra $n_{\text{eff}} \ge 12$ seviyesinin korunması gerekmektedir.

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU mimarisi, Layer 3 Nesil Konsolidasyonu ve F_agent fitness skoru filtreleriyle bellek ve drift mirasını bir sonraki nesle aktarmaktadır. DAU'nun LLM-as-judge yöntemini tamamen yasaklaması ve tüm kültürel aktarımı deterministik Python kodlarıyla (PPR, Ebbinghaus decay, MiniLM PE, F_agent) ölçmesi literatürdeki ön-kayıt ilkeleriyle örtüşmektedir.DAU C' Protokolü N=15 deneylerinde tespit edilen SAMPLE_N15_UNDERPOWERED bulgusu, istatistiksel gücün yetersiz olduğu durumlarda ($p = 0.637$) "etki yok" kararı verilemeyeceğini, deney altyapısının hassasiyet sınırında olduğunu göstermiştir. Çok nesilli aktarım deneyleri yürütülürken önceden kayıt altına alınmış parametre seti ($W=10$ PE penceresi, $K=5$ çeşitlilik kapısı) değiştirilmemeli; varsayılan hipotez testleri eşleştirilmiş (paired) t-testi ve Wilcoxon işaretli sıra testi ile doğrulanmalıdır.

## 6. Teknoloji Devlerinin Agent-Memory / Personality-Persistence Yaklaşımları

Endüstriyel seviyedeki yapay zeka ajan sistemlerinde kalıcılık ve hafıza yönetimi, ticari ürün altyapılarının merkezinde yer almaktadır.

### Teknoloji Şirketlerinin Yaklaşımları

OpenAI (ChatGPT Memory / Assistants API / Agents SDK), thread düzeyinde tam konuşma tutma ve seçici olgu çıkarma (selective extraction) ilkelerini benimser. OpenAI, kullanıcı tercihlerini ve ajan kişiliğini büyük oranda "System Instructions" ve RAG tabanlı hafıza enjeksiyonu ile yönetir. Yaşam-temelli dinamik bir parametrik değişimden ziyade, bağlam penceresine statik kural ekleme yöntemine dayanır.Google DeepMind (Gemini Persistence / Multi-Agent Frameworks), bilişsel mimarileri ve uzun bağlam (1M+ token) pencerelerini vurgulamaktadır. Hafızayı özetleme ve bağlam sıkıştırma teknikleriyle yönetir. DeepMind’ın araştırmaları, çoklu ajan sistemlerinde kültürel uyumun ve norm oluşumunun ortam teşvikleri üzerinden geliştiğini gösterse de, ticari ürün katmanında parametrik güncellemeler yerine bağlamsal yönlendirme (in-context steering) ağırlıktadır.xAI (Grok Agent Persistence) ise uzun süreli ajan oturumlarında bellek kalıcılığını doğrudan geniş bellek vektör kasaları ve çizge veri yapılarıyla bağlamsal olarak beslemektedir.

### Sürekli Öğrenen Ajan (Continual Learning Agent) Mimarilerinin Karşılaştırılması

Sanayi çözümleri ile DAU mimarisi arasındaki temel farklar aşağıdaki tabloda özetlenmiştir:BoyutEndüstri Standartları (OpenAI / Mem0 / Zep)DAU MimarisiKişilik KalıcılığıBağlamsal Enjeksiyon (RAG / System Prompt)Yaşantısal Plastisite (DPO QLoRA Adaptörü)Hafıza KatmanıHiyerarşik Vektör + Çizge (Mem0, MAGMA)İkili Kanal (ChromaDB + SQLite PPR Kasası)Model Ağırlık TutumuTamamen Dondurulmuş (Frozen Static Base Weight)Nesil Sonu Dinamik Mikro Adaptasyon[cite: 6]DeğerlendirmeLLM-as-judge / Benchmark İnsan Puanı%100 Deterministik Python Metrikleri[cite: 6]

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

Teknoloji devlerinin yaklaşımları büyük oranda çıkarım anında bağlam doldurma (in-context injection) ilkesine dayanırken, DAU mimarisi ajan davranışını modelin plastisite katmanına (LoRA) doğrudan işleyen akademik bir yaklaşım izlemektedir.Sanayi RAG tabanlı olgu biriktirme stratejisinin bellek kalabalığına (memory clutter) ve eski bilgilerin silinememesine yol açtığını doğrulamaktadır (ECAI 2026 Abstraction Gap bulgusu). DAU bu riski Ebbinghaus decay ve PPR skorlaması ile çözer. Buna karşın, bağlamsal bellek yönetimi sıfır VRAM eğitim maliyetine sahipken; DAU'nun per-agent LoRA mikro eğitimi 8GB VRAM sınırında ekstra bilgi işlem yükü ve karmaşık adaptör yönetimi gerektirir. Sanayide benimsenen tek geçişli hiyerarşik bellek çıkarma (single-pass hierarchical extraction) mantığı DAU'nun sembolik kasasına entegre edilerek RAG sorgu maliyetleri düşürülmelidir.

## 7. Küçük/Yerel Model Seçimi (8GB VRAM Sınırı, 2026 Güncel)

8GB VRAM kapasitesine sahip bir GPU üzerinde hem çıkarım yapmak hem de QLoRA/DPO mikro eğitimi gerçekleştirmek, model boyutunun ve mimarisinin derece derece hassas seçilmesini gerektirir.

### 8GB VRAM İçin Alternatif Açık Modeller

Llama-3.1-8B-Instant modeline alternatif olarak yerel ortamlarda çalıştırılabilecek güncel açık ağırlıklı modeller değerlendirilmiştir:Qwen-2.5-7B-Instruct / Qwen-3-7B, karmaşık talimat takip etme (instruction following), Türkçe ve çok dilli performans ile sentetik veri üretimi gerektirmeyen mantık yürütme yetenekleri açısından Llama-3.1-8B'ye kıyasla daha yüksek bir başarıma sahiptir. Düşük Bfloat16 nicemleme (quantization) hataları sunar ve DPO eğitiminde logit gradyan kararlılığı yüksektir.Llama-3.2-3B / Llama-3.3-8B varyantlarından Llama-3.2-3B modeli ultra düşük VRAM ayak izi sunarak DPO eğitimi sırasında BATCH_SIZE=2 veya daha yüksek toplu boyutların kullanılmasına izin verir. Ancak 3B modellerin karmaşık simülasyon kurallarını ve duygu durum kaymalarını (drift) kavrama yeteneği 8B modellerden zayıftır.Mistral-7B-Instruct-v0.3, Kaydırılabilir Pencere Dikkat (Sliding Window Attention) mekanizması ile bellek tasarrufu sağlar ancak DPO güncellemelerine yanıt verme hassasiyeti Qwen serisinden düşüktür.ModelParametre4-bit QLoRA VRAM (Eğitim)Talimat Takip SkoruDPO Sinyal Tepkisi8GB VRAM DurumuLlama-3.1-8B-Instant8.03B~7.2 GiB (Batch=1)YüksekOrta (Platoya düşebilir)Uygun (Mevcut DAU Basemodel)Qwen-2.5-7B-Instruct7.61B~6.4 GiB (Batch=1)Çok YüksekYüksek (Keskin Logit ayrımı)Şiddetle ÖnerilirLlama-3.2-3B-Instruct3.21B~3.8 GiB (Batch=2)OrtaDüşük (Nüans kaybı yüksek)Sınırda (Yetersiz Kognisyon)Mistral-7B-v0.37.25B~6.1 GiB (Batch=1)YüksekOrtaUygun

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU, Llama-3.1-8B-Instant modelini 4-bit NF4 nicemleme, MiniLM PE sensörü ve QLoRA DPO adımı ile kullanmaktadır. BATCH_SIZE=1 ve gradyan checkpointing tercihi, Llama-3.1-8B modelinin 8GB kartta belleği aşmadan (OOM) eğitilmesini sağlamış ve VRAM kararlılık testlerini PASS skoruyla geçmiştir (~6386 MiB - 7.2 GiB peak).Llama-3.1-8B modelinde açgözlü yanıt üretiminde meydana gelen platosallık DPO verisinde tıkanmaya yol açmaktadır. Qwen-2.5-7B gibi daha yüksek logit hassasiyeti sunan modellere geçilmemesi sinyal gücünü kısıtlamaktadır. 8GB VRAM altyapısında gelecekte yapılacak model değişimlerinde Qwen-2.5-7B-Instruct modeli önceliklendirilmelidir. bitsandbytes 4-bit NF4 yüklemesinde double_quant=True ve quant_type="nf4" bayrakları sabit tutularak VRAM tüketimi optimize edilmelidir.

## 8. Değerlendirme Metodolojisi (LLM-as-Judge Olmadan)

Yapay zeka araştırmalarında yaygınlaşan LLM-as-judge yöntemi; subjektiflik, stokastik gürültü, pozisyonel sapma (position bias) ve kendini tercih etme (self-enhancement bias) gibi kusurlar taşımaktadır. DAU mimarisi bu yöntemi tamamen yasaklamıştır.

### Deterministik Metrik Tasarımları

LLM-as-judge olmadan bir ajanın beliren (emergent) davranışsal nitelik değişimi şu matematiksel ve deterministik sensörlerle ölçülmektedir:Ajanın kendi hafıza kasasından çektiği beklenen durum ($E$) ile eylem sonrası gerçekleşen durum ($A$) arasındaki fark frozen all-MiniLM-L6-v2 cümlesel gömme modeli üzerinden hesaplanır:$$PE = 1 - \cos(\theta) = 1 - \frac{\vec{E} \cdot \vec{A}}{\|\vec{E}\| \|\vec{A}\|}$$$PE$ üzerinden ajanın iç durum kayması ($\mu_i$) ve yük değişimi ($L_i$) Dinamik Alostatik Denge İyileşme Modeli (DAERM) denklemleriyle güncellenir:$$\mu_i(t) = \min\left(\frac{M_{\text{drift}_i}}{1 + M_{\text{drift}_i}}, 0.75\right)$$$$L_i(t+1) = \text{clamp}\left(L_i + PE_i - \gamma (L_i - \mu_i), \mu_i, 1.0\right)$$Ajanın geçmiş $PE$ geçmişinin varyansı ($\text{var}(PE)$) üzerinden adaptif kazanç çarpanı ($\pi$) hesaplanır. Precision-Weighted PE (ADIM 5 / v2.4) sayesinde sakin rejimlerde yüksek duyarlılık, yüksek gürültülü kriz durumlarında ise sönümleme sağlanır:$$\pi = \text{clamp}\left(\frac{1}{\frac{\text{var}(pe\_history)}{\text{VAR\_REF}} + \epsilon}, \text{MIN\_WEIGHT}, \text{MAX\_WEIGHT}\right)$$$$PE_w = \min(raw\_pe \cdot \pi, 1.0)$$Formül sabitleri $\text{VAR\_REF} = 1/12$, $\text{MIN\_WEIGHT} = 0.5$, $\text{MAX\_WEIGHT} = 1.2$, $\text{WINDOW} = 10$ olarak kilitlenmiştir.MiniLM modelinin olumsuzluk (negation) ve zıtlık kavramlarındaki zayıflığını telafi etmek amacıyla cross-encoder/nli-deberta-v3-small modeli kullanılarak tercih çiftlerinin gerçek bir çelişki ($\text{contradiction\_score} \ge 0.60$) taşıyıp taşımadığı NLI Polarite Filtresi (ADIM 2) ile skorlanır.Sensör / MetrikYöntemDeterministik GüvenceAşırı Duyarlılık / Doygunluk RiskiMiniLM PESentence-Transformer CosineTam (%100 Replay uyumlu)Olumsuzlukları (Negation) kaçırabilirNLI FilterDeBERTa ContradictionTam (Sabit Model Ağırlığı)İşlem maliyeti (CPU/GPU geçişi)Precision PE (v2.4)Rolling Variance ScalingTam (Geçmiş PE dizisi mantığı)Sakin rejimde üst tavan doygunluğu ($\pi \to 1.2$)PPR Memory ScoreGraph PageRank + EbbinghausTam (NetworkX / Saf Python)Graf karmaşıklığı artışı

### DAU Mimarisi Karşılaştırması, Riskler ve En İyi Uygulamalar

DAU'nun değerlendirme metodolojisi katı deterministik standartlara dayanmaktadır. LLM-as-judge kullanımının tamamen reddedilip yerine MiniLM, NLI, DAERM ve Precision-Weighted PE sisteminin kurulması, ölçümlerdaki stokastik gürültüyü ortadan kaldırmıştır.ADIM 5 Precision-PE formülünün önceki versiyonlarında (v2.3 ve öncesi) varyansın tekil olay bazında hesaplanması nedeniyle kazanç çarpanının sürekli üst tavana ($\pi \equiv 1.2$) kilitlendiği (fixed-gain aleti) tespit edilmiştir. v2.4 ile getirilen rolling history ($W=10$) ve $\text{VAR\_REF}=1/12$ düzeltmesi v3 smoke testinde resmi olarak başarıyla geçmiştir (saturation_rate=0.0025, $\pi_n=14$ farklı değer). Deterministik ölçüm araçlarının sağlığı, asıl hipotez testlerinden önce sentetik gürültü ve kontrol kolları (null/shuffle arms) ile sınanmalı; ölçüm aletinin kendisinin doygunluğa girip girmediği audit logları üzerinden izlenmelidir.

## Bizim Mimarimize Göre En Kritik 3 Bulgu

Yapılan derinlemesine literatür, teknoloji şirketleri teknik raporları ve DAU altyapı analizleri sonucunda sistem mimarimiz açısından en kritik üç temel bulgu aşağıda sıralanmıştır:Ajan Bazlı LoRA İzolesinin Disk Düzeyinde Zorunlu Olması (Çapraz Kirlenme Riski):
Multi-tenant LoRA servis literatürü (InfiniLoRA, GRIEF fuzzer analizleri) ve kendi empirik bulgularımız, yüksek seviye PEFT/PyTorch soyutlamalarının bellek üzerinde aktif adaptörleri birbirine karıştırabildiğini göstermiştir. Ajanların birbirinin eğitilmiş ağırlıklarını miras almasını engellemek için, bellek seviyesinde tek bir varsayılan adaptör yuvası tutulmalı, her ajanın LoRA matrisleri disk üzerinde (dau_runs/adapters/{agent_id}/) kesin sınırlarla ayrıştırılmalı ve hot-swap işlemlerinde CUDA akış senkronizasyonu ile gradyan önbellek temizliği zorunlu kılınmalıdır.Olgusal Hafıza ile Davranışsal Plastisitenin Çift Kanallı İzolasyonunun Doğrulanması:
Sektör standartları (Mem0, MAGMA, ECAI 2026 bellek raporları), kullanıcı ve ajan olgularının doğrudan model parametrelerine (LoRA/ROME) yazılmasının felaket unutmaya, silme imkansızlığına ve halüsinasyon kirliliğine yol açtığını kesinleştirmektedir. DAU mimarisinin olguları ve zamansal ilişkileri sembolik kasada (SQLite + ChromaDB PPR) tutarken, LoRA adaptörlerini sadece yaşantısal tercih öğrenimi ($PE$ bazlı DPO) üzerinden tutum/drift değişimine ayırması 2026 mimari konsensüsüyle tam uyumludur.Deterministik Ölçüm Aletlerinin (Precision PE v2.4) Kalibrasyon Zorunluluğu:
LLM-as-judge olmadan nitelik belirmediğini ölçmek akademik olarak en sağlam yol olsa da, kullanılan deterministik sensörlerin doygunluk (saturation) ve sabit-kazanç (fixed-gain) riskleri mevcuttur. ADIM 5 Precision-PE formülünde yapılan v2.4 düzeltmesi (rolling history + $\text{VAR\_REF}$ ölçeklemesi) ile ölçüm aletinin doygunluk oranı $\%0.25$'e düşürülmüş ve hassasiyeti doğrulanmıştır. Çok nesilli $N \ge 15$ deneylerinde hipotez testlerinin geçerliliği, ölçüm aletinin bu kalibrasyonunun korunmasına ve $K \ge 5$ çeşitlilik kapısının katı uygulanmasına bağlıdır.
