# RESEARCH_BRIEF_v1.md

> **Not:** Bu belge dış literatür + sanayi bağlamıdır (Gemini Deep Research,
> 2026-08). DAU'nun kendi kod tabanındaki mevcut durumu bu belgedeki
> iddialara göre **varsayılmamalı**, ayrıca doğrulanmalıdır. Çelişki halinde
> kod/test gerçeği esastır, bu belge değil.

## Kritik 3 bulgu (özet)

1. **Ajan bazlı LoRA izolasyonu disk düzeyinde zorunlu.** Yüksek seviye
   PEFT/PyTorch soyutlamaları bellekte aktif adaptörleri karıştırabiliyor —
   DAU'da bu zaten `f25b0ef` ile bir kez gerçekleşmiş ve düzeltilmiş bir risk.
   Literatür bunun yapısal bir sınıf sorun olduğunu doğruluyor.
2. **Sembolik hafıza (vault) ile parametrik plastisite (LoRA) çift kanallı
   izolasyonu 2026 sanayi/akademi konsensüsüyle uyumlu** (Mem0, MAGMA, ECAI
   2026). Olguları LoRA'ya gömmek felaket unutma + silme imkansızlığı riski
   taşıyor; DAU'nun ayrımı doğru.
3. **Deterministik ölçüm aletlerinin kendisi kalibrasyon gerektirir.**
   Precision-PE v2.4 öncesi (v2.3) sabit-kazanç (fixed-gain, π≡1.2) hatası
   vardı; v2.4 rolling history + VAR_REF=1/12 ile düzeltildi
   (saturation_rate=0.0025). Ölçüm aletinin kendi doygunluğu, hipotez
   testinden önce izlenmeli.

## Yeni / kod tabanında henüz doğrulanmamış bulgular

- **Memory-vault ↔ LoRA senkron kopukluğu:** Ebbinghaus decay ile sembolik
  kasadan silinen bir anının yarattığı drift, LoRA ağırlıklarında kalıcı
  kalabilir → CLAUDE.md GAP-4.
- **Scheduler-state drift / stale KV-cache reuse:** Concurrent multi-tenant
  serving riskleri. DAU'nun sıralı (sequential, tek thread) yapısında
  geçerliliği şüpheli — doğrulanmadan uygulanmamalı.

## Model seçimi notu (aksiyon değil, karşılaştırma önerisi)

Qwen-2.5-7B-Instruct, Llama-3.1-8B-Instant'a kıyasla daha keskin logit
ayrımı ve daha düşük VRAM (6.4 GiB vs 7.2 GiB) sunuyor olabilir — DAU'nun
yaşadığı greedy-plato sorununu hafifletebilir. **Değiştirme kararı değil,
küçük bir karşılaştırmalı smoke test önerisi.**

## Tam başlıklar

Aşağıdaki 8 başlık altında ayrıntılı literatür/sanayi karşılaştırması mevcut
(orijinal Gemini Deep Research çıktısından):

1. Per-Agent / Multi-Tenant LoRA Serving Mimarisi
2. Generation-End vs. Online/Sürekli Öğrenme
3. Tercih Öğrenmesiyle Davranış Şekillendirme (DPO/RLHF)
4. Hafızanın Parametrik Karşılığı (Memory-as-Parametric-Edit)
5. Çok-Nesilli / Kültürel Aktarım Araştırmaları
6. Teknoloji Devlerinin Agent-Memory / Personality-Persistence Yaklaşımları
7. Küçük/Yerel Model Seçimi (8GB VRAM, 2026 güncel)
8. Değerlendirme Metodolojisi (LLM-as-Judge Olmadan)

(Ayrıntılı metin için orijinal araştırma çıktısına bakınız — bu brief onun
aksiyon-odaklı özetidir.)
