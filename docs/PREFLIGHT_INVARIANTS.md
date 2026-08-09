# Preflight Değişmezleri (D-012)

**Durum:** kilitli (2026-08-09). Koda dökülmeyi bekliyor.

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

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I0.1 | **Alet kimliği tam.** backend · model id · quantization · `seq_len` · `epochs` · `batch` · accumulation · `DAU_LORA_ENABLED` · adapter dizini · sampling params · seed aralığı · torch/transformers/peft sürümleri. Herhangi biri belirlenemiyorsa dur. | ABORT | D-004; "koşum kendi konfigürasyonunu inkâr edemesin" |
| I0.2 | **LoRA kapısı bilinçli.** `--lora` / `--no-lora` explicit verilmiş ve env ile tutarlı. Default'a düşülmüşse dur. | ABORT | GAP-1 |
| I0.3 | **`PYTHONHASHSEED` sabit.** Set değilse dur (veya runner set edip kendini yeniden başlatsın). | ABORT | GAP-11 |
| I0.4 | **Seed türetmesi doğrulanabilir.** Her `agent_id` için `_seed_from_agent_id` beklenen değeri dönmeli; hash fallback'e düşerse dur. | ABORT | GAP-11 (spesifik) |
| I0.5 | **Import-time env tutarlı.** `TEMPERATURE` gibi import anında yakalanan değerler mevcut env ile aynı mı. | ABORT | GAP-15 |
| I0.6 | **Determinizm ayarları aktif.** `CUBLAS_WORKSPACE_CONFIG` · torch deterministic algorithms · cudnn deterministic. | ABORT | replay kaybı |

Faz 0 saniyeler sürer ve hiçbir GPU maliyeti yoktur. Hepsi ABORT, çünkü
hepsi ikili (var/yok), kalibrasyon gerektirmiyor.

## Faz 1 — Eğitim bütünlüğü (kol başına, eğitimden hemen sonra)

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I1.1 | **Eğitim gerçekten oldu.** lived/shuffle: `lora_B` abs-sum öncesi ≠ sonrası. null: **değişmemiş olmalı**. | ABORT | `lora_B=0` sahte eğitim; null kontaminasyonu |
| I1.2 | **Adapter izolasyonu.** Her ajanın dizininde yalnızca kendi adaptörü; başka `agent_id` görülürse dur. | ABORT | adapter sızıntısı (`f25b0ef` öncesi) |
| I1.3 | **Gradyan adımı atıldı.** `step_count > 0`, loss sonlu, `grad_norm > 0`. | ABORT | boş eğitim döngüsü |
| I1.4 | **Çiftler gürültü değil.** `PE ≥ SNR_FLOOR` olan çiftlerin oranı ≥ eşik. | FLAG → kalibrasyon sonrası ABORT | GAP-8/A5 |
| I1.5 | **Çift sayısı yeterli.** `n_pairs ≥ MIN_PAIRS`. | FLAG | sessiz boş eğitim |

## Faz 2 — Kol ayrışması (seed başına, üç kol bitince) ← en kritik

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I2.1 | **Kollar birbirinin aynısı değil.** Karar dizisi + PE dizisi hash'i; herhangi iki kol identikse dur. | ABORT | **GAP-1'in asıl sonucu** |
| I2.2 | **Null eğitilmemiş.** Null'ın adapter dizini boş **ve** `lora_B` değişmemiş. | ABORT | null kontaminasyonu |
| I2.3 | **Shuffle gerçekten karışmış.** En az bir çiftin yönü lived'a göre ters. | ABORT | shuffle no-op |

**I2.1 tek başına listedeki en değerli değişmez.** `null ΔPE = 0.000 clean`
metriğinin ikircikliğini ortadan kaldırır: artık "alet deterministik" ile
"hiçbir kol eğitilmedi" ayrışır.

⚠ **Mock modu istisnası:** `DAU_MULTIGEN_MOCK_LLM=1` iken kollar tasarım
gereği aynı olur. Mock'ta I2.1 **FLAG**'e düşer, ABORT'a değil.

## Faz 3 — Ölçüm sağlığı

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I3.1 | **PE olayı yeterli.** `n_pe_events ≥ MIN_TRACE_FRACTION × beklenen`. Şu an yalnızca WARN basıyor. | FLAG | instrument starvation (v1 smoke) |
| I3.2 | **Precision doygunluğu düşük.** `saturation_rate ≤ eşik`, `pi_n_distinct ≥ eşik`. Alanların multigen'de doldurulması şart. | FLAG | GAP-13 + precision regresyonu |
| I3.3 | **Diversity.** Mevcut kapı korunur; ek olarak `n_gated / N > eşik` ise **tüm koşum** INCONCLUSIVE damgalanır. | FLAG | `n_eff < N` (geçen sefer 12/15) |
| I3.4 | **PE listesi pad edilmedi.** Pad oranı > eşikse işaretle. | FLAG | erken biten stream'in `0.0`'larla dolması (K6) |

## Faz 4 — Determinizm kanıtı

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I4.1 | **Replay testi.** Bir seed iki kez koşulur, PE dizisi bit-identik. | ABORT | her türlü gizli RNG sızıntısı |
| I4.2 | **Gen2 RNG durumu kol-bağımsız.** Gen2 öncesi RNG durum hash'i üç kolda aynı. | ABORT | GAP-12 |

I4.1 pahalı (bir seed'i iki kez koşmak). Öneri: **her koşumun ilk seed'inde
bir kez** çalışsın, sonra atlansın. Maliyeti ~1/N.

## Faz 5 — Bileşen canlılığı (GAP-14'ten türedi)

Yeni kategori. Soru şu değil: "bu bileşen doğru mu?" — şu: **"bu bileşen
hiç çalıştı mı?"**

| id | Değişmez | Mod | Yakaladığı |
|---|---|---|---|
| I5.1 | **PPR aktif mi.** `memory_edges` satır sayısı > 0. | FLAG (+ JSON'a `ppr_active`) | GAP-14 |
| I5.2 | **NLI aktif mi.** `NLI_FILTER_STATS.total_candidates > 0`. | FLAG | `nli_filter.py:55` kapalıyken sessizce `True` döner |
| I5.3 | **Hafıza yazıldı mı.** `_memory_written[agent_id] > 0`. | FLAG | boş vault zinciri (K6) |
| I5.4 | **Inherited somatic scale uygulandı mı.** Gen2'de ≥1 kez. | FLAG | GAP-3 |

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
| `MIN_PAIRS` | **kalibre edilmeli** | kaynak yok |
| `SNR_PAIR_RATIO_MIN` | **kalibre edilmeli** | kaynak yok — pilottan gelmeli |
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
