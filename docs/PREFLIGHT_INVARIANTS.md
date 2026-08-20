# Preflight Değişmezleri (D-012)

**Durum:** kilitli (2026-08-09) · **koda döküldü** (2026-08-12).
⚠ Bu satır 2026-08-12'ye kadar *"koda dökülmeyi bekliyor"* diyordu ve
**yanlıştı** — kapılar D-039…D-046 arasında yazıldı ve doğrulayıcı koşumda
(B2, N=40) hepsi çalıştı.

> **28 madde tanımlı, 26'sı kodda kapı olarak uygulanmış.** Sağdaki `Kodda`
> sütunu bunu gösterir. Kaynak: koşum JSON'unun `invariants` bloğu
> (`dau_runs/prereg_b2_batch1_2004_2023.json`), **belge değil**.
>
> ⚠ **İki koşucu, iki kapı kümesi** (2026-08-18). Popülasyon sarmalayıcısı
> (`run_population_experiment.py`) **I0.3 · I0.4 · I0.6 · I0.7 · I1.1 · I4.1 ·
> I4.2 · I5.4 · I5.5 · I5.6** koşar (⭐ **6 → 9 + I5.6**; D-149 · D-159 · D-163)
> koşar; **I0.1/I0.2 bilerek yok** (D-105'te gerekçesi yazılı) ve I0.5 bu yolda
> tanımlı değil. Multigen koşucusu (`run_cprime_multigen.py`, B2'nin yolu)
> **değişmedi**. Bir kapının *"kodda"* olması, **her koşucuda** koştuğu
> anlamına gelmez — koşumun kendi `invariants` bloğuna bakılır.
>
> B2'de 23 kapı geçti, **`I1.3b` bayrak kaldırdı** (kırpma %100) — kapının
> tasarlandığı iş tam olarak buydu. Ayrıntı `docs/B2_RESULTS.md` L18.

## İlke

Bu liste bug listesi değil. Amacı **bozuk bir koşumun başarılı bir koşum
gibi görünmesini imkânsız kılmak.**

Gerekçe ampirik: bu projede yedi ayrı alet arızası oluştu ve **yedisi de
sayı üretti** — `lora_B=0` sahte eğitim, adapter sızıntısı, greedy plato,
precision doygunluğu, GAP-1 (üç kol aynı), GAP-11 (shuffle seed rastgele),
GAP-14 (PPR inert). Hiçbiri çökmedi. Hastalık "bug kaçırdık" değil,
**sistem anlamlılıktan bağımsız olarak çıktı üretiyor.**

Değişmez, bunu tersine çevirir: koşum, sonuç yazmadan önce kendisi
hakkında bir listeyi kanıtlamak zorundadır.

## Başarısızlık modları

| Mod | Anlamı |
|---|---|
| **ABORT** | Koşum durur, **JSON yazılmaz**. Sessiz sahte sonuç imkânsız. |
| **FLAG** | Koşum devam eder, sonuç JSON'a `invariants.<id> = false` + genel `run_quality` damgasıyla yazılır. Analizde kullanılabilir ama etiketlidir. |

Kural: **eşiği henüz kalibre edilmemiş hiçbir değişmez ABORT olamaz.**
Kalibrasyonsuz ABORT, keyfi bir sabitle koşum öldürmek demektir.

---

## Faz 0 — Ön kontrol (koşum başlamadan, GPU'ya dokunmadan)

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I0.1 | **Alet kimliği tam.** backend · model id · quantization · `seq_len` · `epochs` · `batch` · accumulation · `DAU_LORA_ENABLED` · adapter dizini · sampling params · seed aralığı · torch/transformers/peft sürümleri. Herhangi biri belirlenemiyorsa dur. | ABORT | D-004; "koşum kendi konfigürasyonunu inkâr edemesin" | ✅ |
| I0.2 | **LoRA kapısı bilinçli.** `--lora` / `--no-lora` explicit verilmiş ve env ile tutarlı. Default'a düşülmüşse dur. | ABORT | GAP-1 | ✅ |
| I0.3 | **`PYTHONHASHSEED` sabit.** Set değilse dur (veya runner set edip kendini yeniden başlatsın). | ABORT | GAP-11 | ✅ |
| I0.4 | **Seed türetmesi doğrulanabilir.** Her `agent_id` planlanan tohumlardan birini vermeli; okunamayan id'de dur (hash fallback yok). ⚠ **Parser çağırana aittir** (D-118): Protocol C′ `cprime-{arm}-{seed}` (sonda), popülasyon `pop-{arm}-s{seed}-a{index}` (ortada, varis ekleri sona eklenir). | ABORT | GAP-11 (spesifik) | ✅ |
| I0.5 | **Import-time env tutarlı.** `TEMPERATURE` gibi import anında yakalanan değerler mevcut env ile aynı mı. | ABORT | GAP-15 | ✅ |
| I0.6 | **Determinizm ayarları aktif.** `CUBLAS_WORKSPACE_CONFIG` · torch deterministic algorithms · cudnn deterministic · **`warn_only` kapalı** (D-037). warn_only altında aynı seed/kod iki koşumda farklı adapter ve 21/50 karar farkı üretti; `null` bit-exact kaldı. Artık raporlanmıyor, **başarısız sayılıyor**. | ABORT | replay kaybı · **D-037** | ✅ |
| I0.7 | **Hiçbir ajan önceki koşumun adapter'ıyla başlamıyor.** Koşumun `agent_id`'lerinden herhangi birinde kayıtlı adapter varsa dur. `switch_adapter` her yerel kararda diskten yüklüyor ve **`DAU_LORA_ENABLED`'a bağlı değil**, yani `--no-lora` koşumu da kirlenir. Yerel backend dışında **N/A (`None`)**, `True` değil. | ABORT | **D-033** — 08-10 smoke'unda ölçüldü: kollar ayrıştı (`n_unique` 6/7/6), sapma **hipotez lehine** | ✅ |

Faz 0 saniyeler sürer ve hiçbir GPU maliyeti yoktur. Hepsi ABORT, çünkü
hepsi ikili (var/yok), kalibrasyon gerektirmiyor.

## Faz 1 — Eğitim bütünlüğü (kol başına, eğitimden hemen sonra)

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I1.1 | **Eğitim gerçekten oldu.** lived/shuffle: `lora_B` abs-sum öncesi ≠ sonrası. null: **değişmemiş olmalı**. | ABORT | `lora_B=0` sahte eğitim; null kontaminasyonu | ✅ |
| I1.2 | **Adapter izolasyonu.** Her ajanın dizininde yalnızca kendi adaptörü; başka `agent_id` görülürse dur. | ABORT | adapter sızıntısı (`f25b0ef` öncesi) | ❌ testte |
| I1.3 | **Adım gerçekten iş yaptı.** `dpo_optimizer_steps > 0` · loss sonlu · `grad_norm_min > 0`. ⚠ **Kapsam D-046'da daraltıldı:** eski metin (`step_count > 0`) I1.1'i tekrar ediyordu — `lora_B` kımıldadıysa bir adım zaten atılmıştır. Kalan üç kusur bir ağırlık okumasıyla **görülemez**. | ABORT | NaN/inf loss · biriktirip hiç `optimizer.step` çağırmayan döngü · **tam sıfır gradyanla atılan adım** | ✅ |
| I1.3b | **Kırpma görünür.** Kaç `optimizer.step`'in `DPO_MAX_GRAD_NORM` tavanına değdiği. ⚠ **D-046'da eklendi, bu belgede yoktu.** Hata değil: her adım kırpılıyorsa adım boyunu tavan belirler ve D-029'un kilitlediği lr koşumu tarif etmez. | FLAG (herhangi bir kırpma etiket alır — `PAD_FRACTION_MAX` katılığı) | D-029'un gerekçesinin sessizce geçersizleşmesi | ✅ |
| I1.4 | **Filtre aç bırakmadı.** Aday havuzunun ne kadarı marjın altında elendi; hiç çift kalmadıysa düş. ⚠ **Spec değişti (D-046).** Eski metin *"`PE ≥ SNR_FLOOR` olan çiftlerin oranı"* diyordu ve **D-030 onu tautolojiye çevirdi**: marj testi `build_pe_ranked_pairs`'in içine taşındığından eğitime ulaşan her çift eşiği yapı gereği geçiyor, oran **daima 1.0**. Kırılamayan bekçi yazmak yerine D-030'dan sonra ayakta kalan soru soruldu. | FLAG | eğitim açlığı (ölçülen: 3714/7983 = %46.5 elendi) | ✅ |
| I1.5 | **Çift sayısı yeterli.** `n_pairs ≥ MIN_PAIRS`, ve `MIN_PAIRS = DPO_BATCH_SIZE × DPO_GRADIENT_ACCUMULATION_STEPS` — **config'den türetilmiş, gözlemden değil** (§2.7). Sabit yazılmadı: 4 yazılsaydı accumulation değişince "bir tam grup" demeye devam ederdi. | FLAG (`MIN_PAIRS_CALIBRATED=False`) | tek kısa tail grubuyla eğitim; efektif batch'in alet kimliğinin dediği olmaması | ✅ |

## Faz 2 — Kol ayrışması (seed başına, üç kol bitince) ← en kritik

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I2.1 | **Kollar birbirinin aynısı değil.** Karar dizisi + PE dizisi hash'i; herhangi iki kol identikse dur. | ABORT | **GAP-1'in asıl sonucu** | ✅ |
| I2.2 | **Null eğitilmemiş.** Null'ın adapter dizini boş **ve** `lora_B` değişmemiş. | ABORT | null kontaminasyonu | ✅ |
| I2.3 | **Shuffle gerçekten karışmış.** En az bir çiftin yönü lived'a göre ters. | ABORT | shuffle no-op | ❌ yapısal |

**I2.1 tek başına listedeki en değerli değişmez.** `null ΔPE = 0.000 clean`
metriğinin ikircikliğini ortadan kaldırır: artık "alet deterministik" ile
"hiçbir kol eğitilmedi" ayrışır.

⚠ **Mock modu istisnası:** `DAU_MULTIGEN_MOCK_LLM=1` iken kollar tasarım
gereği aynı olur. Mock'ta I2.1 **FLAG**'e düşer, ABORT'a değil.

## Faz 3 — Ölçüm sağlığı

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I3.1 | **PE olayı yeterli.** `n_pe_events ≥ MIN_TRACE_FRACTION ×` **yaşanan olay** (D-073; eskiden bütçe). | FLAG | instrument starvation (v1 smoke) | ✅ |
| I3.2 | **Precision doygunluğu düşük.** `saturation_rate ≤ eşik`, `pi_n_distinct ≥ eşik`. Alanların multigen'de doldurulması şart. | FLAG | GAP-13 + precision regresyonu | ✅ |
| I3.3 | **Diversity.** Mevcut kapı korunur; ek olarak `n_gated / N > eşik` ise **tüm koşum** INCONCLUSIVE damgalanır. | FLAG | `n_eff < N` (geçen sefer 12/15) | ✅ |
| I3.4 | **Erken sonlanma oranı.** Kohortun bütçenin ne kadarına ulaşamadığı. **Ölçülür ve raporlanır, bayrak yok** (D-073). | REPORT | *(artık bir arıza değil, evren hakkında bir bulgu)* | ✅ |

✅ **I3.1 ve I3.4 D-073'te düzeltildi.** Uzun süre şu not duruyordu: ölüm
mümkün olmadan önce erken biten bir yaşam bir **anormallikti** ve iki kapı da
onu yakalamak için vardı; D-066'dan sonra erken ölüm **tasarımın kendisi**
oldu (D-068 pilotunda yaşamlar 50 olaylık bütçeye karşı 19 ve 10 olayda bitti,
I3.4 gen1'de **%71 pad** bastı, I3.1 kapsamayı **0.29** raporladı) ama kapılar
hâlâ bunu arıza gibi okuyordu. Uç nokta yeniden tanımlanınca ikisi de ayrıldı:

- **I3.1'in paydası artık yaşanan olay sayısı.** Kapı ilan edilmiş işine
  döndü — *"alet aç kaldı mı"*. 12 olay yaşayıp 12 satır yazan ajan sağlam;
  50 yaşayıp 12 satır yazan **bozuk**, ve ikisini yalnız bu payda ayırıyor.
  Payda yoksa (D-073 öncesi bölüm) kapı **geçmiyor**, *"değerlendirilemez"*
  diyor (§2.9).
- **I3.4 bayrak olmaktan çıktı, `MODE_REPORT`'a geçti.** Aynı aritmetik, yeni
  ad: bütçeye göre **erken sonlanma oranı**. `PAD_FRACTION_MAX = 0.0` olduğu
  ve LOCF kalktığı için bayrak bırakılsaydı bundan sonraki **her koşum**
  `flagged` olurdu ve `run_quality` bir şey ayırt etmeyi bırakırdı. Sayı yine
  JSON'a yazılıyor — ikinci ön-kayıtta **geçerlilik kriteri** adayı.

⚠ **Kapı sayısı değişti:** `MODE_FLAG` bir azaldı, `MODE_REPORT` (yeni mod)
bir arttı. `run_quality` yalnız `abort` ve `flag`'e bakıyor.

⚠ Bir kapının tasarım gereği sürekli bayrak basması, onu **okunmaz** hale
getirir. İkinci ön-kayıt ya eşiği yeni uç noktaya göre yeniden tanımlamalı ya
da bu iki kapıyı *"ölçülebilirlik ön-koşulu"* olarak açıkça yeniden
konumlandırmalı. Sessizce görmezden gelinmesi **yasak**.

## Faz 4 — Determinizm kanıtı

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I4.1 | **Replay testi.** Bir seed iki kez koşulur, PE dizisi bit-identik. | ABORT | her türlü gizli RNG sızıntısı | ✅ |
| I4.2 | **Gen2 RNG durumu kol-bağımsız.** Gen2 öncesi RNG durum hash'i üç kolda aynı. | ABORT | GAP-12 | ✅ |

I4.1 pahalı (bir seed'i iki kez koşmak). Öneri: **her koşumun ilk seed'inde
bir kez** çalışsın, sonra atlansın. Maliyeti ~1/N.

## Faz 5 — Bileşen canlılığı (GAP-14'ten türedi)

Yeni kategori. Soru şu değil: "bu bileşen doğru mu?" — şu: **"bu bileşen
hiç çalıştı mı?"**

| id | Değişmez | Mod | Yakaladığı | Kodda |
|---|---|---|---|---|
| I5.1 | **PPR aktif mi.** `memory_edges` satır sayısı > 0. | FLAG (+ JSON'a `ppr_active`) | GAP-14 | ✅ |
| I5.2 | **Polarite kapısı aktif mi.** `POLARITY_FILTER_STATS.total_candidates > 0` (D-032'de NLI→kosinüs; sayaç da yeniden adlandırıldı). | FLAG | kapı kapalıyken sessizce `True` döner | ✅ |
| I5.3 | **Hafıza yazıldı mı.** `_memory_written[agent_id] > 0`. | FLAG | boş vault zinciri (K6) | ✅ |
| I5.4 | **Inherited somatic scale uygulandı mı.** Gen2'de ≥1 kez. | FLAG | GAP-3 | ✅ |
| I5.5 | **Seçilim terimi, tasarımın okuduğu yerde ölçülebilir mi.** Ebeveyni gen ≥ 2 olan her geçişte en az bir alan `selection_estimable` · **ve** kurucu geçiş ölçülebilir **çıkarsa da** bayrak (YENİ-4'ün öncülü kırılmış demektir). ⛔ `F_agent` yayılımı **rapor edilir, karara girmez** | FLAG | ⛔ *"sıfır, çünkü yapı gereği"* ile *"sıfır, çünkü seçilim yok"* ayrımı — C2 bunu **`clean`** raporlamıştı | ✅ |
| I5.6 | **Hasat tavanı bağladı mı.** Her nesilde en az bir olayda `talep > alınan`, **ve** ilk eksik alma `LANDMARK_EVENT`'ten **önce**. İki kusur **ayrı** raporlanır: *hiç bağlamadı* (katman hiçbir şey yapmadı) ile *geç bağladı* (çalıştı ama uç noktanın penceresi dışında). ⚠️ Kanned LLM'de **değerlendirilmez** — talebi stub belirler | FLAG | ⛔ Sabit kotada eksik alma **olay 16'ya kadar tam sıfırdı** ve her özet sağlıklı görünüyordu | ✅ |

GAP-14 kararı verilene kadar I5.1 FLAG kalır. "PPR bağlansın" kararı
çıkarsa ABORT'a yükselir.

---

## Kalibre edilmesi gereken eşikler

**Bu değerleri uydurmuyorum.** Kaynağı olanı yazdım, olmayanı işaretledim.

| Sabit | Öneri | Kaynak |
|---|---|---|
| `SNR_FLOOR` | 0.40 | `sentetik-kognisyon` §1.2: "PE ≥ 0.40 (DEEP)"; `PE < 0.15` gürültüde kaybolur |
| `SATURATION_MAX` | ~0.05 | v3 smoke ölçümü 0.0025; 20× marj |
| `PI_N_DISTINCT_MIN` | ~8 | v3 smoke 14 ölçtü |
| `MIN_TRACE_FRACTION` | 0.5 | zaten var (`run_protocol_c_prime.py:99`) |
| `MIN_PAIRS` | `DPO_BATCH_SIZE × DPO_GRADIENT_ACCUMULATION_STEPS` = 4 | **D-046** — yapısal taban (bir tam accumulation grubu), config'den türetildi. ⚠ Yeterlilik düzeyi **değil**; ABORT'a yükseltmek pilot ister |
| ~~`SNR_PAIR_RATIO_MIN`~~ | **gereksiz kaldı** | D-030 marj testini çift kurulumuna taşıdı ⇒ oran daima 1.0. I1.4 D-046'da reddetme oranına çevrildi, eşik **uydurulmadı** |
| `GATED_FRACTION_MAX` | **kalibre edilmeli** | geçen sefer 3/15 = 0.20 |

Kalibrasyonsuz olanlar FLAG kalır; pilot koşumdan sonra ön-kayıtla
ABORT'a yükseltilebilir. Bu sıralama önemli: **eşik önce ölçülür, sonra
kilitlenir** — tersi post-hoc olur.

## Kapsam dışı bırakılanlar (ve neden)

| Ne | Neden hariç |
|---|---|
| K1'deki 98 sessiz yolun çoğu | Çoğu iyi huylu (`store.close()` hatası yutulması zararsız). Yalnızca sonuç sayısına dokunanlar alındı. |
| Kütüphane sürüm pinleme | Sürümler **kaydedilir** (I0.1), ama sabitlenmez — bu ayrı bir karar. |
| 28 BELİRSİZ maddesinin çoğu | Altın kaplama. Bulgu 1 ve 4 zaten çıkarıldı; kalanlar açık bırakıldı. |
| GAP-5 (prompt priming) | Değişmezle yakalanamaz. Kod doğru olanı yapıyor; sorun kavramsal. Yalnızca akıl yürütme yakalar. |
| GAP-10 (W_SEM, negation) | Ölçüm geçerliliği; baseline'ı değiştirir. Ayrı karar. |

## Kilitlenen tasarım kararları (2026-08-09)

1. **I4.1 kapsamı:** replay testi **yalnızca koşumun ilk seed'inde**
   çalışır, sonra atlanır. Maliyet ~1/N. Gerekçe: RNG sızıntısı
   sistemiktir; bir seed'de yoksa diğerlerinde de olmaz. Sızıntı
   seed'e özgü olsaydı zaten I2.1 yakalardı.

2. **I2.1 hash kapsamı:** `sha256(karar dizisi ++ PE dizisi)`.
   Ajanın son durumu **dahil değil** — durum, karar ve PE'nin türevi
   olduğu için ekstra bilgi getirmez ama kayan nokta gürültüsüyle
   yanlış-pozitif üretir. Kararlar tek başına da yetmez: aynı kararlar
   farklı PE üretebilir (farklı beklenti), bu gerçek bir ayrışmadır.

3. **I5.1 modu:** GAP-14 kararına kadar **FLAG**. "PPR koşum yoluna
   bağlansın" kararı çıkarsa ABORT'a yükselir.

4. **FLAG raporlaması:** results JSON'a
   - `invariants: { "<id>": true|false, ... }` — her değişmezin sonucu
   - `run_quality: "clean" | "flagged" | "aborted"` — tek özet alan

   **Analiz kuralı:** `flagged` koşumlar varsayılan olarak **dışlanır**.
   Dahil etmek isteniyorsa ön-kayıtta açıkça gerekçelendirilir.
   `aborted` koşumun JSON'u zaten yoktur.

## Sıradaki adım

Koda dökülüş sırası (her biri ayrı commit + kendi testi):
`GAP-11 → GAP-12 → GAP-15 → GAP-13 → GAP-1 (D-004) → preflight gate`.

Gate yazıldıktan sonra ilk koşum **deney değil gate testi** olmalı:
LoRA kapalıyken `--n-pairs 1 --mock-llm` **hata vermeli**. Vermezse gate
çalışmıyordur. Hiç ateşlenmemiş gate, gate değildir.
