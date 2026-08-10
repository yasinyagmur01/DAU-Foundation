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

### Uygulama borçları

Ayrıntılı adım planı: **§F (Faz 2)**. Özet sıra:
`U1 → U2 → U3 → (U7 kararı) → U4 → U5 → U6`.

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

---

# F. Faz 2 — Kararların uygulanması (U1–U7)

**Açıldı:** 2026-08-10, karar kapısı kapandıktan sonra.
**Girdi:** D-018 · D-019 · D-020 · D-021 · D-022 — hepsi `DECISIONS.md`'de.
**Çıktı:** alet kilitli, ölçümler yapılmış, pilota hazır kod.

## F.0 — Bu fazın sözleşmesi (her adımda geçerli)

1. **Önce doğrula, sonra dokun.** Bu plandaki her satır numarası
   2026-08-10'da doğrulandı — ama koda dokunmadan önce **yeniden oku**.
   Bu projede belge iki kez yanıldı: GAP-11 (docstring eski formatı
   yazıyordu) ve GAP-14 ("hiç kimse çağırmıyor" — yanlıştı, `graph.py:1426`
   çağırıyor). Hafızaya ve belgeye değil, dosyaya güven.
2. **Gate-and-confirm.** Analiz → öneri → **Yasin'in onayı** → uygulama.
   Onaysız kod değişmez. Analiz şunu içerir: ne bulundu, ne değişecek,
   hangi test gelecek, ne riskli.
3. **Her düzeltme testiyle gelir**, ve test **mutasyon kontrolünden geçer**:
   düzeltme geçici olarak geri alınır, test kırılmalı, sonra geri konur.
   Kırılmıyorsa test o hatayı yakalamıyor demektir.
4. **Commit ritmi:** tek konu → tam suite (`python -m pytest -q`) →
   gerekçeli commit. Ölçüm veya karar içeriyorsa **ayrıca D-kaydı**.
5. **Sessiz fallback yasak.** Bu fazda eklenen hiçbir kod, belirlenemeyen
   bir durumu varsayılana düşürerek geçiştirmez — `SystemExit`, `ValueError`
   veya en azından `[WARN]`.
6. **`constraints.py`'deki eşik değerleri** yalnızca bir D-kaydıyla değişir.
   Taşımak/yeniden adlandırmak serbest, **değerini değiştirmek** ön-kaydı
   ilgilendirir.
7. **Ön-kayıt henüz yazılmadı** → alet değişikliği hâlâ meşru. Ama her biri
   D-kaydı ister; pre-reg kilitlendiği an bu pencere kapanır.

## F.1 — Sıra ve bağımlılıklar

```
U1 (backend=local) ─┐
U2 (NF4)  ──────────┴─→ U3 (model + VRAM ölçümü) ─→ U7 (A2/A3/A4 kararı)
U4 (accumulation)   ← bağımsız, ama U3'ten sonra ölçüm tekrarı gerekmesin diye sonraya
U5 (SNR filtresi)   ← bağımsız
U6 (consolidation)  ← bağımsız, ama gen2 mirasını değiştirir → U3'ten sonra
```

**Neden bu sıra:** U3 ölçümü **NF4 açıkken ve lokal backend'de** yapılmalı,
yoksa ölçülen alet pilotun aleti olmaz. U7 tamamen U3'ün VRAM sonucuna bağlı.

---

## U1 — Backend varsayılanı `local` (D-018) ✅ `7adb01d`

**Bitti** 2026-08-10. Planlananın dışında bir şey çıktı ve karara bağlandı:
varsayılanı çevirmek, `_resolve_llm_backend`'in tanınmayan değerde sessizce
varsayılana düşmesini **zararsızdan zararlıya** çevirdi (`grok` yazım hatası
eskiden `groq`'a, artık `local`'a düşerdi). Fonksiyon artık `ValueError`
fırlatıyor; boş/unset hâlâ varsayılan (GAP-15 emsali). Kaydı **D-023**.
`llm_backend.py`'deki kopya sabitler bilerek tekilleştirilmedi — bekçi testi
bağlıyor, temizlik ayrı iş.

| | |
|---|---|
| **Kayıt** | D-018 (kilitli) + **D-023** (uygulama sırasında çıkan yan ürün) |
| **Dosya** | `dau/foundation/llm_backend.py:18` · `dau/foundation/graph.py:293` — ikisinde de `LLM_BACKEND_DEFAULT: str = "groq"` |
| **Değişiklik** | İkisi de `"local"` |
| **Dikkat** | `install_mock_llm` (`run_cprime_multigen.py`) `os.environ.setdefault("DAU_LLM_BACKEND", "groq")` yapıyor. Mock **yalnızca groq yolunda** mock — backend `local` olursa graph gerçek `LocalBackend`'i çağırır ve 8B modeli yükler. Bu `setdefault` **kalmalı**, ama artık varsayılanı değil, mock'un kendi gereksinimini ifade ediyor; yorumu buna göre güncellensin. |
| **Test** | ✅ yeni `dau/foundation/tests/test_llm_backend.py` (13 vaka) + `test_cprime_multigen.py`'ye 2 `install_mock_llm` vakası. 5 mutasyon denendi, 5'i de yakalandı. |
| **Dur-kontrol** | ✅ tam suite 255 → **270 passed**. Backend'e dokunan 4 test env'i zaten açıkça set ediyordu; groq varsayımına dayanan test çıkmadı. |
| **Yan etki** | Adım 5'in `--lora` + uzak backend kontrolü fiilen ateşlenmez hale gelir. **Kaldırılmaz** — yanlış env set eden koşumu hâlâ yakalar. |

## U2 — NF4 + double_quant, açıkça (D-020) ✅

| | |
|---|---|
| **Kayıt** | D-020 (kilitli), D-016'yı kapatır |
| **Dosya** | `dau/foundation/local_llm.py:99` `build_load_kwargs()`, içindeki `BitsAndBytesConfig(...)` (`:115` civarı) |
| **Değişiklik** | `bnb_4bit_quant_type="nf4"` + `bnb_4bit_use_double_quant=True` **açıkça** eklenir |
| **İlke** | Asıl mesele fp4 değil, **bayrağın hiç yazılmamış olması**. Kütüphane varsayılanı değişirse alet habersiz değişir — D-018'de uzak backend için reddedilen riskin aynısı. |
| **Test** | ✅ **yeni** `test_quantization_flags_are_pinned_not_inherited`. ⚠ Planın "`afbb552`'deki test zaten var, değeri güncellenir" ifadesi **yanlıştı**: `test_tool_identity_quantization_matches_loader` rapor↔loader **tutarlılığını** ölçüyor, değeri değil — bayraklar silinince de geçiyor (mutasyonla doğrulandı). O test doğru şeyi yapıyor, dokunulmadı; değeri sabitleyen ayrı bir test eklendi. |
| **Bedava kazanç** | ✅ doğrulandı — `describe_quantization` config'i loader'dan okuyor, ikinci bir yer güncellenmedi |
| **Dur-kontrol** | ⚠ **Planın dur-kontrolü ateşlenemez.** `tool_identity._quantization` backend `local` değilse `{"available": false, "reason": "remote backend"}` döndürüyor; `--mock-llm` koşumu `install_mock_llm` yüzünden backend'i `groq`'a sabitliyor, yani mock JSON'unda `quant_type` **hiç yazmıyor**. Yerine geçen kontrol: `describe_quantization()` model **yüklemiyor**, yalnızca config kuruyor — GPU'ya dokunmadan birim testinde doğrulanır. |
| **Kalan risk** | Birim testi config'in **ne olduğunu** kanıtlıyor, modelin o config'le **yüklendiğini** değil. NF4+double_quant ilk kez U3'te gerçek yükleme görecek. |

## U3 — Model + VRAM ölçümü (D-019) ⚠ ön-kayıtlı

| | |
|---|---|
| **Kayıt** | D-019 — **kabul kriteri zaten kilitli, değiştirilemez** |
| **Ön koşul** | U1 ve U2 bitmiş olmalı (lokal backend + NF4 açık) |
| **Tasarım** | 3 seed × 10 olay, **iki model**, aynı seed'ler / prompt'lar / sıcaklık, greedy decoding |
| **Ölçülen** | `_phase1_diversity`'nin saydığı `n_unique` — üretim metriğinin aynısı, yeni metrik icat edilmez. Ayrıca VRAM tepe değeri (karar kriteri değil, envanter) |
| **Kabul kriteri (ÖNCEDEN KİLİTLİ)** | Qwen benimsenir **ancak ve ancak** (1) medyan `n_unique ≥ DIVERSITY_MIN_UNIQUE (5)` **ve** (2) medyan Llama'nınkinden **kesin büyük**. **Beraberlik/belirsizlikte statüko kazanır — Llama'da kalınır.** |
| **YASAK** | Sayıları gördükten sonra kriteri gevşetmek. Bu, ölçümü tavsiyeyi onaylatma törenine çevirir. |
| **Kayıt** | Sonuç **D-kaydına** girer (ham sayılarla): hangi model, hangi seed'ler, `n_unique` dağılımı, VRAM tepe değerleri. Karar bu kayıtla kilitlenir. |
| **Maliyet** | ~15GB indirme. Reddedilirse boşa gider — D-019'da kabul edilen bedel. |
| **Not** | Brief'in ~6.4 / ~7.2 GiB rakamları **fp4 varsayımıyla** verilmişti; NF4+double_quant ölçümü onları düzeltecek. |

## U7 — A2/A3/A4 kararı (D-021) — U3'ten sonra

| | |
|---|---|
| **Kayıt** | D-021 (bölünmüş paketin ölçüme bağlanan yarısı) |
| **Girdi** | U3'ün VRAM tepe ölçümü → gerçek boşluk |
| **Karar** | A2 (`DPO_MAX_SEQUENCE_TOKENS` 256→512) · A3 (`DPO_EPOCHS` 1→3) · A4 (%10 yüksek-somatik replay, `F_agent ≥ 0.7`) |
| **Maliyetler** | A2 aktivasyon belleğini ~2×; A3 koşum süresini 3×; A4 ~+0.3 GiB |
| **Kim karar verir** | **Yasin.** Claude Code ölçümü sunar, seçenekleri ve bütçeyi gösterir, öneri verir |
| **Sonra** | Karar D-kaydına girer, sonra kod |

## U4 — Gradient accumulation (D-021/A1)

| | |
|---|---|
| **Kayıt** | D-021 (kilitli) |
| **Dosya** | `dau/foundation/local_llm.py` — `_run_dpo_epochs`, `:659` epoch döngüsü, `:677` `zero_grad()`, `:701` `clip_grad_norm_`, `:702` `step()` |
| **Sorun** | Her çift için ayrı `zero_grad()`+`step()` ⇒ **efektif batch = 1**. Uygulanan şey gradient *checkpointing* (bellek tekniği); tavsiye edilen gradient *accumulation* (gradyan tekniği). İkisi karıştırılmış görünüyor. |
| **Değişiklik** | Mikro-batch 1 kalır; `step()` ve `zero_grad()` **N mikro-adımda bir** atılır. `clip_grad_norm_` step'ten hemen önce. Bölen: kayıp `N`'e bölünür ki gradyan büyüklüğü batch=N ile aynı olsun |
| **N nerede** | Yeni UPPER_CASE sabit, `constraints.py` (örn. `DPO_GRADIENT_ACCUMULATION_STEPS`). Değeri bu adımda **karara bağlanır** — yeni sabit, mevcut bir eşiğin değişmesi değil |
| **Bellek** | Accumulation OOM **vermez** — mikro-batch değişmiyor |
| **Test** | N mikro-adımda tek `optimizer.step()` (sayaçla doğrula); son kısmi grup da işlensin (pairs % N ≠ 0 durumu **kaybolmamalı**) |
| **Bedava kazanç** | Alet kimliği `gradient_accumulation_steps` ve `effective_batch_size`'ı kendiliğinden doğru raporlar (`tool_identity.py`) — **sabiti oradan da güncellemeyi unutma**, bugün `GRADIENT_ACCUMULATION_STEPS: int = 1` olarak sabitlenmiş durumda |
| **Dur-kontrol** | I1.3 (grad adımı atıldı) ileride yazılırken bu sayaç kullanılabilir mi |

## U5 — Mutlak PE (SNR) filtresi (D-021/A5)

| | |
|---|---|
| **Kayıt** | D-021 (mekanizma kilitli, **eşik kilitli değil**) |
| **Dosya** | `dau/foundation/lora_update.py` — `build_pe_ranked_pairs`, `:286` `abs(pe_left - pe_right) < PE_RANK_MIN_GAP` |
| **Sorun** | Yalnızca PE **farkı** aranıyor, PE **büyüklüğü** aranmıyor ⇒ `PE=0.030` vs `0.031` farkı, `0.8` vs `0.2` farkı kadar meşru sinyal sayılıyor |
| **Değişiklik** | Mutlak eşik: her iki tarafın (veya en azından `chosen`'ın) PE'si `SNR_FLOOR`'un altındaysa çift **elenir** |
| **Eşik** | Başlangıç `0.40` (brief), ama **`calibrated: false`** işaretlenir ve pilotun ölçtüğü PE dağılımıyla kilitlenir. `PREFLIGHT_INVARIANTS.md` `SNR_FLOOR`'u zaten "kaynağı var, kalibre edilmeli" diyor ve I1.4'ü bu yüzden FLAG'de tutuyor |
| **ZORUNLU** | **Elenen çift sayısı loglanmalı** ve sonuç JSON'una yazılmalı. `MIN_PAIRS` kalibre edilmemiş (I1.5 FLAG) — bu sayı olmadan "az sayıda güçlü çift" ile "eğitim seti boşaldı" ayırt edilemez |
| **Test** | Düşük-PE çiftler eleniyor, yüksek-PE çiftler kalıyor; elenen sayı raporlanıyor; eşik `0` iken davranış eskisiyle birebir aynı (geriye dönük kapı) |
| **Dur-kontrol** | Mock koşumunda kaç çift eleniyor — hepsi eleniyorsa eşik pilottan önce gözden geçirilir |

## U6 — Consolidation'ı deney yoluna bağla (D-022)

| | |
|---|---|
| **Kayıt** | D-022 (kilitli), GAP-14'ü kapatır |
| **Dosya** | `dau/diagnostics/run_cprime_multigen.py` — `run_lineage` (`:669`); `consolidate_run` `dau/foundation/memory_bridge.py:102` |
| **Doğrulanmış durum** | `consolidate_run` **ölü kod değil** — `graph.py:1426` çağırıyor (demo/long-run yolu). Deney yolu `app.stream()`'i doğrudan sürüyor ve o fonksiyona uğramıyor |
| **AÇIK SORU — bu adımda karara bağlanacak** | Gen1 **iki yaşam** sürüyor (phase-1, phase-2). "Yaşam sonu" hangisi? Phase-1 sonrası mı, phase-2 sonrası mı, ikisi de mi? D-022 bunu bilerek açık bıraktı. **Sessizce seçme — analiz et, öner, onay al, D-kaydına yaz.** |
| **Kapsam uyarısı** | `run_consolidation` üç iş yapıyor: **siler** (Ebbinghaus unutması), **güçlendirir**, **kenar yazar**. Yani bu değişiklik yalnızca PPR'ı canlandırmıyor — **unutmayı da açıyor**, ve unutma gen2'ye giden miras malzemesini değiştiriyor ⇒ **birincil uç noktaya (doğum-drift, D-002) dokunuyor** |
| **Zamanlama** | Vault `run_lineage`'in `finally`'sinde kapanıyor — consolidation ondan **önce** çalışmalı |
| **Test** | Consolidation sonrası `store.count_edges() > 0`; `deleted_count` / `strengthened_count` / `edges_created` sonuç JSON'una giriyor |
| **I5.1** | **FLAG kalır.** Pilot kenarların gerçekten oluştuğunu doğrulayınca ABORT'a yükseltilir — doğrulanmamış bir düzeltmeye koşum öldürme yetkisi verilmez |
| **Pilot borcu** | Pilot `deleted` / `strengthened` / `edges_created` **ve transfer aday sayısındaki değişimi** raporlamalı |

---

## F.2 — Faz 2 bittiğinde nerede olunur

Alet kilitli ve ölçülmüş. Sıradaki (bu fazın dışı, `D.` bölümündeki sıra):

8. **Pilot** — hipotez testi **değil**: gate geçiyor mu, kollar ayrışıyor mu,
   consolidation'ın miras etkisi ne
9. **Güç hesabı** — pilotun gözlediği `d`'den gerçek `N`
   (⚠ GAP-9: N=15 varsayılan alınamaz)
10. **Pre-registration** — kilitlendiği an alet donar
11. **Master reference v2.4.2** — birikmiş borçlar (§21 NLI satırı yanlış,
    §6/§19 ADIM 4 iddiası, multigen hiç geçmiyor, D-020 quantization notu)
12. **main merge** (D-013)

## F.3 — Bu fazda YAPILMAYACAKLAR

- **Pre-registration yazmak** — alet kilitlenmeden olmaz
- **Gerçek pilot koşumu** — U3 ölçümü pilot değildir, kapsamı 3 seed × 10 olay
- Kalan 7 preflight değişmezini (I1.1–I1.5, I2.3, I4.1) yazmak — ikisi
  zaten U5/U7'ye bağlı, ötekiler ayrı bir parça
- **main merge** (D-013)
- GAP-5 / GAP-10'a dokunmak (ayrı kararlar, baseline'ı etkiler)
- Yeni katman, yeni özellik, kapsam dışı refactor
