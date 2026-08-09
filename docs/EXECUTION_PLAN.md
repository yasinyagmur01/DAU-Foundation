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

---

## C. Adım 7'den sonra: karar kapısı — DUR

Kod düzeltmeleri bitince durulur. Sıradakiler kod değil **karar** gerektirir
ve üçü tek "alet yükseltmesi" paketidir — üçü de aynı şeyi (DPO sinyal
gücü) etkiliyor:

| Karar | Kayıt | Neden şimdi |
|---|---|---|
| GAP-8'in beş ayarı: gradient accumulation · `seq_len` 512 · 3 epoch · %10 somatik replay · `PE ≥ 0.40` eşiği | GAP-8 | Alet gücü; pre-reg'den önce |
| Backend `local` + **Qwen-2.5-7B** | D-005 (durum: **önerildi**, kilitli değil) | Aynı pencere; pre-reg kilitlenince post-hoc olur |
| PPR: koşum yoluna bağlansın mı, "inert" diye belgelensin mi | GAP-14 | I5.1'in ABORT/FLAG modunu belirliyor |

---

## D. Sonrası (bu fazın dışı — sırayı kaybetmemek için)

8. **Pilot** — hipotez testi **değil**: gate geçiyor mu, kollar ayrışıyor mu
9. **Güç hesabı** — pilotun gözlenen `d`'sinden gerçek `N`.
   ⚠ **N=15 varsayılan olarak alınmayacak** (GAP-9: güç analizi N=15'i
   yalnızca `d ≥ 0.5` için geçerli sayıyor; gözlenen `d ≈ 0.04`)
10. **Pre-registration** — D-002 (doğum-drift birincil), D-003
    (`f_agent=None` duyarlılık kolu), OOD probing kararı, 2 vs 3 nesil
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
