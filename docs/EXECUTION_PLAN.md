# Kod Fazı — Uygulama Planı

**Oluşturuldu:** 2026-08-09 · **Faz:** kod düzeltmeleri
**Önceki faz:** salt-yazı denetimi (D-010, D-011, D-012 ile kapandı)

Bu dosya, kod fazının adım adım yürütülmesi içindir. Her oturum başında
`CLAUDE.md` "Şu An Neredeyiz" bölümü buraya işaret eder.

---

## A. Bu fazın kuralları

1. **Tek konu → tek commit → gerekçeli mesaj.** Karar içeriyorsa ayrıca
   `docs/DECISIONS.md`'ye D-kaydı.
2. **Her düzeltme, o hatayı yakalayacak testle birlikte gelir.** Bu kural
   pazarlığa açık değil — yoksa N+1'inci düzeltme N'inciyi bozar ve kimse
   görmez. Bu projenin zincirleme arıza deseninin panzehiri budur.
3. **Kod değiştirmeden önce mevcut davranışı teste bağla.** Sonra test ya
   yeşil kalır (davranış değişmedi) ya da kırılır — kırılma kasıtlıysa
   **aynı commit'te** gerekçesiyle güncellenir.
4. `constraints.py`'deki eşik **değerleri bu fazda değişmez.** Taşınabilir,
   yeniden adlandırılabilir; değeri değişemez — ön-kaydı bozar, ayrı karar.
5. **Gerçek deney koşulmaz.** Bu fazın tek koşumu Adım 7'deki gate testi.
6. Gate-and-confirm: her değişiklik önce analiz, sonra onay, sonra uygulama.

---

## B. Adım sırası

Bağımlılık sırasına göre. Adım 1–4 birer satırlık; asıl iş 5 ve 6.

**Durum (2026-08-10):** Adım 1 ✅ `8cf2ac0` · Adım 2 ✅ `ab8966c` ·
Adım 3 ✅ `ab30f9c` · Adım 4 ✅ `090a5bc` · Adım 5 ✅ `afbb552` ·
Adım 6 **kısmen** (`75239d1` faz 0 · `0b48f93` faz 3 · `30c80da` faz 4/5 ·
`b8c3e69` faz 2) · Adım 7 ✅ **ateşlendi**.

Adım 1–5 mutasyon kontrolünden geçti. Adım 6'da **24 değişmezin 17'si**
kodda; kalan 7'si eğitim yoluna ölçüm eklemeyi gerektiriyor (aşağıda).

⚠ **Sayı düzeltmesi:** `CLAUDE.md` ve bu dosya "20 değişmez" diyordu;
`PREFLIGHT_INVARIANTS.md` tablosunda **24** madde var (6+5+3+4+2+4).
Belge kilitli, sayı yanlıştı.

**Adım 6'da kalan 7 değişmez** — hepsi `local_llm`'in eğitim yoluna ölçüm
eklemeyi gerektiriyor, o yüzden ayrı bir parça olarak duruyor:

| id | Neden henüz yok |
|---|---|
| I1.1 | `lora_B` abs-sum öncesi/sonrası ölçen yardımcı yok |
| I1.2 | Adapter dizini içerik denetimi (izolasyon) yazılmadı |
| I1.3 | `grad_norm` `clip_grad_norm_`'dan alınıp atılıyor (`local_llm.py:651`) |
| I1.4 | `SNR_FLOOR` çift filtresi — GAP-8/A5 kararına bağlı |
| I1.5 | `MIN_PAIRS` kalibre edilmemiş |
| I2.3 | `_train_adapter` çift listesini döndürmüyor |
| I4.1 | Replay: ilk seed'i iki kez koşan orkestrasyon yok |

I1.4 ve I2.3 zaten karar kapısındaki GAP-8 paketine bağlı — o karar
verilmeden yazılmaları erken olurdu.

### Adım 1 — GAP-11: shuffle kolu reproducible değil

| | |
|---|---|
| **Dosya** | `dau/diagnostics/run_protocol_c_prime.py:567-573` |
| **Sorun** | `_seed_from_agent_id("cprime-shuffle-2001-g1")` → `int("g1")` ValueError → `abs(hash(...)) % 2**31`. `PYTHONHASHSEED` set değil → her process farklı seed. Ölçüldü: `419643228` / `227385495` / `229629477` |
| **Kök neden** | `cd64cc8` `agent_id`'ye `-g1` ekledi; docstring hâlâ eski formatı yazıyor |
| **Test** | Aynı `agent_id` iki ayrı process → aynı seed. `-g1`/`-g2` ekli id'ler doğru seed'i çıkarmalı. Hash fallback'e düşülürse **hata** (sessiz fallback yasak) |
| **Dur-kontrol** | Üç kolun da seed'i deterministik mi |

### Adım 2 — GAP-12: gen2 seed-locked değil

| | |
|---|---|
| **Dosya** | `dau/diagnostics/run_cprime_multigen.py` → `run_gen2_measure` |
| **Sorun** | Gen1 phase-1 (`:411`) ve phase-2 (`:446`) `_lock_seeds` çağırıyor, gen2 çağırmıyor. Asimetri: lived/shuffle eğitim yapıp torch RNG tüketiyor, null tüketmiyor → üç varis gen2'ye farklı RNG durumuyla giriyor |
| **Test** | Gen2 öncesi RNG durum hash'i üç kolda aynı olmalı |
| **Dur-kontrol** | Kol farkı ile RNG farkı ayrıştı mı |

### Adım 3 — GAP-15: TEMPERATURE import'ta donuyor

| | |
|---|---|
| **Dosya** | `run_protocol_c_prime.py:73` (import-time okuma), `:460` (geri yazma) |
| **Sorun** | `_lock_seeds` her çağrıda env'i import anındaki değerle geri yazıyor → import sonrası env değişimi sessizce etkisiz |
| **Test** | Import sonrası `DAU_LLM_TEMPERATURE` değişimi koşuma yansımalı |

### Adım 4 — GAP-13: multigen'de precision audit yok

| | |
|---|---|
| **Dosya** | `run_cprime_multigen.py` → `ArmResult` doldurma |
| **Sorun** | `saturation_rate` / `pi_n_distinct` / `n_pe_events_audited` / `n_saturated` / `pi_values` hiç doldurulmuyor → JSON'a default sıfırlar. v2.4.1'de v3 smoke'un tüm anlamı bu alanlardı |
| **Test** | JSON'da bu alanlar gerçek değer taşımalı; hepsi sıfırsa test kırılsın |
| **Dur-kontrol** | Alet sağlık kontrolü fiilen çalışıyor mu |

### Adım 5 — GAP-1 / D-004: LoRA kapısı

| | |
|---|---|
| **Dosya** | `run_cprime_multigen.py` + `run_protocol_c_prime.py` |
| **Değişiklik** | (a) `DAU_LORA_ENABLED` kapalıyken ve `--no-lora` verilmemişken **hard fail**; (b) explicit `--lora` / `--no-lora` CLI flag'i; (c) her results JSON'una **alet kimliği**: backend · model id · quantization · `seq_len` · `epochs` · `batch` · accumulation · adapter durumu · sampling params · seed aralığı · torch/transformers/peft sürümleri |
| **İlke** | Bir koşum kendi konfigürasyonunu inkâr edememeli |
| **Test** | env kapalı + flag yok → `SystemExit`; `--no-lora` → geçer ama JSON'da işaretli; alet kimliğinin her alanı dolu |
| **Dur-kontrol** | `--no-lora` bilinçli bir seçim olarak çalışıyor mu (yasak değil, sessiz değil) |
| **Not** | `test_cprime_multigen.py:181` ve `test_protocol_c_prime.py:280` env'i `"0"`'a sabitliyor → `--no-lora`'ya uyarlanmalı |

### Adım 6 — Preflight gate (D-012)

| | |
|---|---|
| **Kaynak** | `docs/PREFLIGHT_INVARIANTS.md` — 20 değişmez, I0.1–I5.4 |
| **Dosya** | Yeni modül (öneri: `dau/diagnostics/preflight.py`) + runner'a bağlanma |
| **Kural** | Koddaki id'ler belgedeki id'lerle **birebir aynı** olmalı; JSON'daki `invariants` bloğu belgeyle eşleşsin |
| **Çıktı** | `invariants: {"<id>": true\|false}` + `run_quality: clean\|flagged\|aborted` |
| **Test** | Her değişmez için ayrı birim test — hem geçen hem **kasten kırılmış** hali |
| **Dur-kontrol** | 20 değişmezin her biri ayrı ayrı ateşleniyor mu |

Mod dağılımı: Faz 0 (6 adet) · I1.1–I1.3 · I2.1–I2.3 · I4.1–I4.2 → **ABORT**.
Diğerleri **FLAG**. Kalibre edilmemiş eşiği olan hiçbir değişmez ABORT olamaz.

Mock istisnası: `DAU_MULTIGEN_MOCK_LLM=1` iken I2.1 (kollar aynı değil)
FLAG'e düşer — mock'ta kollar tasarım gereği aynıdır.

### Adım 7 — Gate testi (bu fazın tek koşumu)

```bash
python -m dau.diagnostics.run_cprime_multigen --n-pairs 1 --mock-llm
```

LoRA kapalıyken bu komut **hata vermeli**. Vermezse gate çalışmıyordur.

Sonra `--lora` ile tekrar: gate Faz 0'ı geçmeli ama mock deterministik
olduğu için I2.1 FLAG üretmeli. İki koşum birlikte gate'in hem ABORT hem
FLAG yolunun kanıtıdır.

> **Hiç ateşlenmemiş gate, gate değildir.** Gate'in çalıştığının tek kanıtı,
> onu kasten kırıp abort ettirmektir.

**✅ Koşuldu (2026-08-10).**

*Koşum 1* — planın tam komutu, `exit=1`, JSON yazılmadı:
```
Refusing to start: neither --lora nor --no-lora was given. LoRA training is
off by default, so falling through would run three identical arms and report
a p-value for it (GAP-1).
```

*Koşum 2* — `--lora --mock-llm`, `exit=0`, Faz 0'ın altısı da geçti,
`run_quality=flagged`. Planın öngördüğü FLAG çıktı:
```
FLAG I2.1  seed=2001: identical arms ['lived', 'null', 'shuffle']
FLAG I3.2  saturation_rate=0.2000 > 0.05; pi_n_distinct=2 < 8
FLAG I5.1  memory_edges is empty in every life — PPR is inert
FLAG I5.4  never applied (skipped=36)
```

İki koşum birlikte hem ABORT hem FLAG yolunu kanıtlıyor. Ayrıca iki koşum
arasındaki fark da bilgi taşıyor: `--no-lora` koşumunda I5.2 (NLI aktif mi)
**kaldı**, `--lora` koşumunda **geçti** (`total_candidates=20 rejected=8`) —
kapı gerçekten ayrım yapıyor, sabit yeşil basmıyor.

**Gate iki bilinen gap'i kendiliğinden buldu:** I5.1 → GAP-14 (PPR atıl),
I5.4 → GAP-3 (somatic scale hiç uygulanmadı). İkisi de Ağustos'ta salt-yazı
denetimiyle bulunmuştu; artık koşum kendisi söylüyor.

---

## C. Adım 7'den sonra: karar kapısı — DUR

Kod düzeltmeleri bitince durulur. Sıradakiler kod değil **karar** gerektirir
ve üçü tek "alet yükseltmesi" paketidir — üçü de aynı şeyi (DPO sinyal
gücü) etkiliyor:

**✅ KAPANDI — 2026-08-10.** Dört kararın hepsi verildi:

| Karar | Sonuç | Kayıt |
|---|---|---|
| Backend | `local` **kilitlendi**; groq legacy/keşif olarak kalır | **D-018** |
| Model | Qwen-2.5-7B **ölçülmeden kilitlenmez**; kabul kriteri ön-kayıtlı (medyan `n_unique ≥ 5` **ve** Llama'yı kesin geçme; beraberlikte statüko) | **D-019** |
| Quantization | **NF4 + `double_quant`**, bayrak açıkça yazılır | **D-020** (D-016 kapandı) |
| GAP-8 | **Bölündü.** A1 (accumulation) + A5 (SNR filtresi) kilitli; A5'in eşiği pilottan sonra kalibre edilir. A2/A3/A4 VRAM ölçümüne bağlı | **D-021** |
| PPR / consolidation | Deney yoluna **bağlanır**; I5.1 pilota kadar FLAG; miras etkisi pilotta ölçülür | **D-022** (GAP-14 kapandı) |

**Kararların ortak deseni:** hiçbiri doğrulanmamış bir iddiaya dayanarak
kilitlenmedi. Kaynağı olan mekanizmalar kabul edildi, **sayılar ölçüme
bırakıldı** — model seçimi, SNR eşiği, VRAM'e bağlı üç ayar ve
consolidation'ın miras etkisi.

### Uygulama borçları (kod henüz değişmedi)

| # | İş | Kayıt |
|---|---|---|
| U1 | `LLM_BACKEND_DEFAULT` → `local` (`llm_backend.py:18`, `graph.py:293`); `install_mock_llm`'in groq `setdefault`'u gözden geçirilir | D-018 |
| U2 | `build_load_kwargs`: `quant_type="nf4"` + `use_double_quant=True` | D-020 |
| U3 | Model ölçümü: 3 seed × 10 olay, iki model, NF4 açık; `n_unique` + VRAM tepe | D-019 |
| U4 | Gradient accumulation (`local_llm`); alet kimliği `effective_batch_size`'ı kendiliğinden düzeltir | D-021/A1 |
| U5 | `build_pe_ranked_pairs`'e mutlak PE filtresi; elenen çift sayısı **loglanmalı** (`MIN_PAIRS` kalibresiz, I1.5 FLAG) | D-021/A5 |
| U6 | `consolidate_run` deney yolunda yaşam sonunda; **hangi fazın sonu olduğu açık soru** | D-022 |
| U7 | A2/A3/A4 kararı — U3'ün VRAM sonucundan sonra | D-021 |

---

## D. Sonrası (bu fazın dışı — sırayı kaybetmemek için)

8. **Pilot** — hipotez testi **değil**: gate geçiyor mu, kollar ayrışıyor mu
9. **Güç hesabı** — pilotun gözlenen `d`'sinden gerçek `N`.
   ⚠ **N=15 varsayılan olarak alınmayacak** (GAP-9: güç analizi N=15'i
   yalnızca `d ≥ 0.5` için geçerli sayıyor; gözlenen `d ≈ 0.04`)
10. **Pre-registration** — D-002 (doğum-drift birincil), D-003
    (`f_agent=None` duyarlılık kolu), OOD probing kararı, **kaç nesil**
    (D-014: hedef 2 değil N; N'in kendisi ve güç etkisi açık soru)
11. **Master reference v2.4.2** — biriken borçlar: §21 NLI satırı **yanlış**
    (`lora_update.py:297` tersini yapıyor) · §6 ve §19 ADIM 4 iddiası
    (GAP-14: PPR inert) · multigen belgede hiç geçmiyor · 4 commit gecikmesi
12. **main merge** — D-013

---

## E. Bu fazda YAPILMAYACAKLAR

- **main merge** (D-013 — alet işi bitmeden değil)
- `constraints.py` eşik **değerlerini** değiştirmek (ön-kaydı bozar)
- Gerçek deney koşumu
- `RUNPATH_AUDIT.md`'deki 28 BELİRSİZ'in kalanını kovalamak (altın kaplama)
- GAP-5 / GAP-10'a dokunmak (ayrı kararlar, baseline'ı etkiler)
- Yeni katman, yeni özellik, refactor
