# Provenans Denetimi — her nicelik: **kim yazıyor · ne besliyor · ne zaman dejenere**

**2026-08-19 · D-130 · GPU'suz, salt okuma**

⚠ **Neden yazıldı:** bu projede büyük sürprizlerin **çoğu** tek bir soruyla
önceden görülebilirdi ve o soru hiç sistematik sorulmadı — *"bu niceliği kim
yazıyor, ne besliyor, hangi koşulda hepsi aynı çıkar?"* Üç örnek, üçü de gün
kaybettirdi: `z`'yi **iki** fonksiyonun yazdığı (D-115) · bireysel kanalın
landmark'tan önce ateşlenmediği (D-120) · `null` kolunun **hiç** ayrışmadığı
(D-129).

⛔ **Bu belge iddia üretmez.** Yalnız kod okur ve *"şu koşulda varyans sıfır
olur"* der. Sayılar, işaretli yerlerde ölçülmüş koşumlardan alınmıştır.

---

## Zincir — tek bakışta

```
[niş] → talep → HASAT → enerji → F_agent → turnuva → w → varis
                  ↓                                        ↓
              havuz oranı                            miras (kasa + adapter)
                  ↓                                        ↓
              KRİZ ──────────────┐                    davranış
                                 ↓                         ↓
        bireysel şaşırma → delta.magnitude → [EŞİK 0.70] → z
```

---

## 1. `z` — birincil uç nokta (landmark drift)

| | |
|---|---|
| **Kim yazıyor** | ⛔ **İKİ çağıran:** `graph.py:1203` (ajanın kendi `DeltaRecord`'u) · `environment.py:276` (**ortak havuz krizi**) |
| **Ne besliyor** | `delta.magnitude`, ve **yalnız** `is_trauma` geçerse: `magnitude ≥ DELTA_THRESHOLD_DEEP = 0.70` |
| **Nasıl birikiyor** | `current + magnitude·exp(−current/TRAUMA_DECAY_BASE)` ⇒ **monoton ama sıkıştırıcı**; türev `z=0`'da **tam sıfır** |
| ⛔ **Ne zaman dejenere** | (a) hiçbir ajan eşiği geçmezse ⇒ hepsi **0** · (b) kriz ateşlenirse ⇒ kolun **tamamına aynı anda** aynı artış · (c) `z_before` herkeste 0 ise ⇒ kriz hepsini **aynı** değere taşır |
| **Ölçülmüş** | bireysel geçiş **24/216 (%11.1)** · `Var(z)=0` **14/18** geçişte (C2) |

## 2. `delta.magnitude` — `z`'nin girdisi

| | |
|---|---|
| **Kim yazıyor** | PE yolu (ajanın tahmin hatası) · kriz yolu (`CRISIS_BASE_MAGNITUDE × CRISIS_TRAUMA_MULTIPLIER = 1.0`, sabit) |
| ⛔ **Ne zaman dejenere** | Tepe değerler **0.42–0.62** bandında oturuyor, eşik **0.70** ⇒ eşiğin **altında** kalan bilgi `z`'ye hiç geçmiyor |
| **Ölçülmüş** | `to_landmark.max` `lived`'da 3 farklı değer / 8 ajan; `null`'da **1** (sonda-2) |

## 3. `F_agent` — seçilim **girdisi**

`F = w_e·(E_lived/E_max) + w_p·(1 − (|Δpool|/t_survived)/X_max) + w_s·(t_survived/t_gen)`

| terim | ne besliyor | ⛔ ne zaman dejenere |
|---|---|---|
| enerji | ömür-boyu **ortalama** enerji (D-086) | ajanlar aynı hasatı alırsa **aynı** |
| havuz | olay başına hasat oranı (K4-b) | **hasat farkı yoksa aynı** |
| hayatta kalma | `t_survived / t_generation` (D-071) | herkes bütçeyi doldurursa **hepsi 1.0** |

⛔ **Üç terim de tek bir şeye bağlı: hasat farkı.** Hasat eşitse `F_agent`
yayılımı **tam sıfır**, ve turnuva **yazı-turaya** döner.
**Ölçülmüş:** C2'de **5/18** geçişte yayılım = 0 (üçü `null`) · sonda-2'de
`null`'ın **üç neslinde de** 0.

## 4. **Hasat** — bütün zincirin kökü

| | |
|---|---|
| **Kim yazıyor** | `realized_extractions_sequential` (P0-①): talepler **sırayla** karşılanır, son ajan kalanı içer |
| **Ne besliyor** | talep (davranıştan) · yenilenmiş stok |
| ⛔⛔ **Ne zaman dejenere** | **Stok bütün talepleri karşılıyorsa sıra hiçbir şeyi değiştirmez** — herkes istediğini tam alır ⇒ **ayrım sıfır** |
| **Ölçülmüş** | sonda-2 `null`: havuz sonu **0.593 / 0.611**, kriz **0**, hasat farkı **0** — üç nesilde de |

⇒ ⭐ **P0-① bir ayrım kaynağı değil, kıtlığa bağlı bir çarpandır.**

## 5. Talep — davranıştan

| | |
|---|---|
| **Kim yazıyor** | ajanın kararı → `decision_to_extraction` |
| ⛔ **Ne zaman dejenere** | Ajanlar aynı ağırlıklara sahipse **aynı kararı** verir (greedy, deterministik) ⇒ aynı talep |
| **Ölçülmüş** | gen1'de üç kolun **arm_digest'i birebir aynı**; `null`'da gen2/gen3'te de ajanlar özdeş |

⇒ ⛔ **Farkın tek kökeni adapter.** Kasa mirası tek başına davranışı ayırmıyor.

## 6. `w` — varis sayısı

| | |
|---|---|
| **Kim yazıyor** | turnuva (k=2) → `plan_next_generation` |
| ⛔ **Ne zaman anlamsız** | `Var(F_agent) = 0` iken `Var(w) > 0` olur ama bu **sürüklenmedir**, seçilim değil |
| **Ölçülmüş** | C2: `Var(w) > 0` **18/18**, ama `F_agent` yayılımı **13/18** ⇒ beş geçiş sürüklenme |

## 7. Kriz

| | |
|---|---|
| **Kim yazıyor** | `pool_ratio < POOL_CRISIS_THRESHOLD = 0.30` ⇒ kolun **her** ajanına |
| ⛔ **Ne zaman zararlı** | Ateşlediğinde `z`'yi **doldurur ama eşitler**; ve **müdahale-sonrasıdır** (ajanların kendi hasadından doğar) ⇒ uç noktadan budanamaz (D-119/D-120) |
| **Ölçülmüş** | 216 yaşamın **144'ünde** kriz (C2) |

## 8. Miras — iki kanal

| kanal | ⛔ ne zaman etkisiz |
|---|---|
| Kasa (sembolik) | Tek başına **davranışı ayırmıyor** — `null` kolu kasayı alıyor ve yine de klon kalıyor |
| Adapter (parametrik) | `--no-lora` ile **tamamen kapalı**; `null` kolunda **yok**; ⚠ ağırlık hareketi nesilden nesle **sönüyor** (3.56 → 0.98, C2) |

---

## ⛔ Dejenerasyon koşulları — tek liste

Bir koşum şu koşullardan **herhangi biri** sağlanırsa seçilim hakkında bilgisizdir:

1. **Stok talebi karşılıyor** ⇒ hasat farkı 0 ⇒ `F_agent` farkı 0 ⇒ turnuva yazı-tura
2. **Adapter yok** (`--no-lora` ya da `null` kolu) ⇒ davranış farkı 0 ⇒ (1)
3. **Tepe magnitude < 0.70** ⇒ bireysel kanal `z`'ye hiç yazmıyor
4. **Kriz ateşliyor** ⇒ `z` dolu ama hücre içinde **sabit**
5. **gen1** ⇒ kurucular özdeş, hiçbir uç nokta ayrım gösteremez (yapısal)
6. **Yaşam landmark'tan önce bitiyor** ⇒ okuma yok (bugün `GRACE` bunu engelliyor)

⚠ **1 ve 2 aynı zincirin iki ucudur** ve C2'nin `null` kolunda **birlikte**
gerçekleşti. Üçüncü ön-kayıtın çözmesi gereken şey budur; uç nokta seçimi
**bunun altında** kalan bir ayrıntıdır.

---

## Bu denetimin **kapatmadığı** yerler

⚠ Dürüstlük için: aşağısı okunmadı, dolayısıyla sürpriz **hâlâ mümkün**.

- `MemoryStore` / Ebbinghaus silme oranlarının varise ne taşıdığı (GAP-4 açık)
- `precision_weight`'in PE'ye katkısı (L13: mekanizma atıl)
- `social` alanının drift'e katkısı (C2'de `social` alanı `z`'de hiç görünmedi)
- Adapter sönümünün (3.56 → 0.98) uzun soylarda nereye gittiği
