# Popülasyon C″ — İkinci Ön-Kayıt

**Durum: 🔒 KİLİTLİ · 2026-08-18 · commit `72df476ebd54`**

**Dört slotun dördü kapalı.** Bu andan itibaren bu belgedeki hiçbir madde
değişmez. Değişiklik gerekirse **yeni bir ön-kayıt** açılır ve bu belge
*superseded* işaretlenir.

⚠ **Alet değişikliği penceresi KAPANDI** (§2.10). Kilitten sonra
`constraints.py` eşiği, uç nokta, test, çift kurma stratejisi ya da herhangi
bir ön-kayıtlı protokol maddesi değişirse sonuç **post-hoc** olur.

⚠ **Birinci ön-kayıt (`PREREGISTRATION.md`) yürürlükte kalır** — o kilit
Protocol C′'nin tek-soy koşumunu bağlar (B2, `p = 0.9914`, alet null'ı).
Bu belge onu **geçersiz kılmaz**, ayrı bir deneyi bağlar. Çelişki görülürse
sessizce seçilmez, ilan edilir (§2.11).

---

## 0. Neden ikinci bir ön-kayıt

Birinci ön-kayıtta **seçilim katmanı atıldı**: her ebeveynin tam olarak bir
varisi vardı ⇒ `w` sabit ⇒ `Cov(w, z)` tanımsız. Bu koşum tam olarak o
eksiği kapatmak için var: **`w`'yi değişken yapan** bir popülasyon.

⚠ **Evrenin fiziği ve ölçüm aleti B2'den bu yana değişti** (D-054…D-118).
`dau_runs/`'daki hiçbir koşum bu ön-kayıtla karşılaştırılamaz.

---

## 1. İddia

Sınanan parça (aksiyomun **tamamı değil**):

> Bir popülasyonda **kimin varis bıraktığı**, ajanların **yaşayarak edindiği**
> iz ile ilişkilidir; ve bu ilişki nesiller boyunca **sönmez**.

⛔ **Bu ön-kaydın iddia ETMEYECEKLERİ** — olumlu sonuçta bile:

- *"anlamlı"* — ilk koşum **kestirimdir, hipotez testi değildir** (P7-b/D-096).
- **Birey düzeyi** — P1 kol başına ayrı popülasyon veriyor ⇒ iddia **grup
  düzeyinde** kalır (Chevin 2011).
- *"LLM ajanlarında Lamarckçı kalıtım vardır"* — tek model, tek niş ailesi,
  **n = 1 deney**.
- `delta_pe` üzerinden hiçbir şey — P6 o uç noktayı kaldırdı.

---

## 2. Tasarım — ✅ **kilitli** (D-094 · D-095 · D-101 · D-102 · D-104)

| # | Karar | Seçilen | Kayıt |
|---|---|---|---|
| **P0** | Ajanlar nasıl farklılaşır | ① sıralı erişim, **tur başına rotasyon** | D-104 |
| **P1** | Kol yapısı | kol başına **ayrı popülasyon ve ayrı mera** | D-095 |
| **P2** | Seçilim şeması | turnuva, **k = 2** | D-094 |
| **P3** | Üreme | sabit N; ölen her ajanın yerine turnuva kazananından bir varis ⇒ `w ∈ {0,1,2,…}` | D-094 |
| **P4** | Katmanlar | `F_agent` (girdi) → `w` (varis sayısı) → `z` (sonuç), **üçü ayrı** | D-094 |
| **P5** | Havuz | kapasite **N ile ölçeklenir**, kişi başı 100/80 sabit | D-081 |
| **P6** | Faz | **tek faz**; `delta_pe` uç noktası yok | D-095 |
| — | Mera | **her nesilde taze** | D-104 |
| — | Kanal 2 | ebeveynin adapter'ı **varise kopyalanır** (3A tersine çevrildi) | D-102 |
| — | Price | **bir nesil gecikmeli**: G nesil ⇒ **G−1** satır | D-101 |
| — | G | **G ≥ 3 yapısal** (G=2 yalnız sıfır raporlayabilir) | D-107 |

---

## 3. Birincil uç nokta — ✅ **SLOT 1 KAPANDI (D-121, Yasin 2026-08-18)**

**Karar: seçenek A — `z` bugünkü hâliyle kalır** (iki kanal birlikte),
**okuma kuralı eklenir**:

| | |
|---|---|
| **`z`** | landmark'taki (olay 10) drift büyüklüğü, sabit yaşta, **iki kanal birlikte** |
| ⭐ **dejenere hücre ilanı** | `Var(z) = 0` olan hücrede `Cov(w,z)` **yapı gereği** sıfırdır ⇒ *"sıfır seçilim ölçtük"* değil ***"seçilim tanımsız"*** raporlanır (Rothenberg 1971, `10.2307/1913267`) |
| ⭐ **pozitif kontrol** | aynı `w`, krizden **bağımsız** değişen `energy_mean_over_life` ile kovaryans. ⛔ **Uç nokta değil**, hiçbir kalıtım iddiası buna dayanmaz |

**Gerekçe — ölçüldü, seçilmedi** (D-120/D-121):

| tanım | hücre içi tek değer (dejenere) |
|---|---|
| **A — bugünkü `z`** | **14 / 27** |
| ⛔ D — yalnız bireysel kanal | **en az 21 / 27** |

⇒ Bireysel kanal `magnitude ≥ 0.7` ile ateşleniyor ve landmark'tan **önce
neredeyse hiç** ateşlenmiyor ⇒ `z_before` çoğu ajanda **tam 0**. Kriz o
sıfırları *hepsi 1.0*, D *hepsi 0.0* yapardı. ⚠ Ayrıca kriz
**müdahale-sonrası** olduğu için onu budamak *bad control* riski taşıyordu
(DR #10 Q2 + yerel tarama §R — **iki bağımsız yol**).

⚠ **İlan edilen sınır:** bu koşumun bilgilendirici hücre oranı **~%48**
(13/27, ⚠ kapısız checkpoint'ten kestirim). Bütçe buna göre kurulur (§7).

⚠ **Kararın verildiği andaki durum (arşiv, D-115 → D-120):** `z`'yi **iki yol**
yazıyor — ajanın kendi `DeltaRecord`'u (`magnitude ≥ 0.7`) ve ortak havuz krizi
(`pool_ratio < 0.30`, kolun tamamına aynı anda). Beş seçenek tartışıldı
(A koru · B okuma anını kaydır · C uç noktayı değiştir · D yalnız bireysel
kanal · E ayrıştır). **A seçildi**; B **sansürleme** getirdiği için (⚠ `null`
kolu ~10 olayda ölüyor, landmark 10'da tam bu yüzden), D **ölçümle** ve
*bad control* riskiyle, E ise **işlevsiz** olduğu için (dejenere hücrede
ayrıştırma da sıfır verir) alınmadı.

⚠ **L9 uyuldu:** uç nokta **etkiye bakılarak seçilmedi** — yukarıdaki bütün
sayılar **hücre içi çeşitlilik**, kol karşıtlığı değil. Kol karşıtlığına
bakılmadı.

---

## 4. Ön-kayıtlı ikincil uç noktalar — ✅ **SLOT 2 KAPANDI: YOK** (D-122, Yasin)

⛔ **Bu koşumun ön-kayıtlı ikincil uç noktası yoktur.** Boş bırakmak bir eksik
değil, bir karardır: elimizdeki tek meşru aday **ömür**dü ve `lived ≈ shuffle`
olduğu için **Lamarckçı kanalın kanıtı olamaz** — ikincil olarak konsa bile
ön-kayıtı zayıflatır, çünkü null çıktığında *"ama ikincilde bir şey var"*
demenin yolunu açar.

⚠ Ölçülen her şey (ömür · somatik marker · `F_agent` dağılımı · havuz oranı)
**betimleyici** olarak raporlanmaya devam eder; hiçbiri hipotez taşımaz.

**Adaylar ve neden alınmadıkları (arşiv):**

| aday | durum |
|---|---|
| **Ömür** | ⚠ **post-hoc tuzağı** — B1'de hareket ettiği görüldü (`lived` 24.8 · `shuffle` 28.2 · `null` 10.0). Meşru tek yol: **koşumdan önce** yazmak ve **taze tohumla** sınamak. ⚠ Ve `lived ≈ shuffle` ⇒ kanalın kanıtı **olamaz** |
| `F_agent` dağılımının yayılımı | **geçerlilik ön-koşulu** olarak zaten var (§5), uç nokta değil |
| Somatik marker (ödül/tehdit) | ölçülüyor, uç nokta olarak **seçilmedi** |

---

## 5. Geçerlilik kriterleri — koşum başlamadan sabit

⚠ Bunlar **etkiye bakmak değil** (L9): kol farkına değil, dağılımın **var olup
olmadığına** bakılıyor ve kural koşumdan **önce** yazılıyor.

| # | kriter | karşılanmazsa |
|---|---|---|
| **V1** | `Var(w) > 0` | koşum **seçilim hakkında bilgisizdir** — turnuva yazı-turaya döner |
| **V2** | `F_agent` dağılımı yayılım taşır | aynı |
| **V3** | `G ≥ 3` | Price yalnız sıfır raporlayabilir (D-107) |
| **V4** | `run_quality = clean` | `flagged` ise bayrak adıyla raporlanır, sonuç **çekilmez** |
| **V5** | I4.1 replay birebir | koşum tekrarlanamaz ⇒ sonuç değil |

---

## 6. Okuma kuralları — **koşumdan önce tanımlı** (CLAUDE.md §1'den, değişmedi)

| seviye | ne görülür | ne **iddia edilir** | ne **edilmez** |
|---|---|---|---|
| **0 — kapı** | `Var(w) > 0` | hiçbir şey; **ön koşul** | — |
| **1 — seçilim** | `Cov(w,z) ≠ 0`, işaret tohumlar arası tutarlı | *"seçilim landmark drift üzerinde etki etti"* | *"kalıtım aktı"* |
| **2 — birikim** | terim nesiller boyu sönmüyor | *"etki birikimli"* | *"kanal parametrik/sembolik"* |
| **3 — kol farkı** | `lived` ≠ `shuffle` ≠ `null` | **Lamarckçı kanal iddiası** | *"anlamlı"* |

⚠ **En sık yapılacak hata:** Price **seçilimi** verir, kolların karşılaştırması
**kalıtımı**. Seviye 1 dolup seviye 3 boş çıkabilir.

---

## 7. Bütçe ve durma kuralı — ✅ **SLOT 3 KAPANDI** (D-122, Yasin)

| | |
|---|---|
| **Tohumlar** | **9911 · 9912 · 9913** (taze blok, Slot 4) |
| **N** | 8 ajan / kol / nesil |
| **G** | 3 nesil ⇒ kol başına **2** Price satırı (D-101) |
| **Kollar** | `lived` · `null` · `shuffle` + I4.1 replay kolu |
| **Olay bütçesi** | 30 |
| ⇒ **Price satırı** | 3 tohum × 3 kol × 2 = **18** |
| ⇒ **beklenen bilgilendirici** | **~9** (%48 kestiriminden, ⚠ kestirim) |
| **Beklenen süre** | ~4–5.5 sa (B1: 1 tohum 1 sa 15 dk, kapılı) |

**Gerekçe — neden tam 3 tohum:** seviye 1 iddiası *"işaret **tohumlar arası**
tutarlı"* şartına bağlı; 3 tohum bu şartın sorulabildiği en küçük sayıdır ve
şekil B1/headroom ile **aynı** olduğu için maliyeti tahmin değil **ölçüm**.
İlk koşum zaten **kestirimdir, hipotez testi değildir** (P7-b/D-096), o yüzden
tohum sayısını büyütmek bu koşumun sınıfını değiştirmez.

⛔ **Durma kuralı:** koşum ne **uzatılır** ne **kısaltılır**. Ara sonuca
bakılırsa **kayda geçer** (D-114 deseni) ve N değişmez. Çökme hâlinde
checkpoint elle incelenir, **sonuç sayılmaz** (D-111).

### 7b. Eski hâli (arşiv)

Biçimi karara bağlandı (D-110): *"kaç saat"* değil ***"olay oranını hangi
kesinlikle"***. ⭐ **Aranan nicelik D-121 ile belirlendi: bilgilendirici hücre
oranı** — yani `Var(z) > 0` olan, dolayısıyla seçiliminin **tanımlı** olduğu
hücrelerin payı. Bugünkü kestirim **13/27 ≈ %48** (⚠ kapısız checkpoint'ten,
sonuç değil).

⛔ **Kalan karar:** bu oranı **hangi kesinlikle** bilmek istiyoruz, ya da kaç
**bilgilendirici hücre** hedefliyoruz. Ondan sonra tohum sayısı aritmetikle
çıkar.

**Bilinen maliyetler** (ölçüldü):

| ne | süre |
|---|---|
| Pilot (N=8 · G=3 · 30 olay · 3 kol + replay) | **~1 sa 15 dk** |
| 3 tohumlu koşum | **~5 sa 20 dk** |
| Replay'in payı | **%25** |

**Durma kuralı:** bütçe koşumdan önce yazılır; koşum ne uzatılır ne kısaltılır.
⚠ D-114'te ara sonuca bakıldı ve **kayda geçti** — N değişmedi.

---

## 8. İlan edilen sınırlar (taslak — kilitte numaralanacak)

1. **Kestirimdir, test değildir** (P7-b/D-096). *"Anlamlı"* kelimesi kullanılmaz.
2. **Grup düzeyi** — kol başına ayrı popülasyon (P1) ⇒ birey düzeyi iddia yok.
3. **Price küçük N'de yanlı** (Rice 2008, DR #8) — 8 ajan, tohum başına 2
   seçilim epizodu.
4. **Tek model, tek niş ailesi, n = 1 deney.**
5. **Davranış çökük** — olayların %94–100'ünde DEFECT (D-068). K7 bilişsel
   önseli aksiyom gerekçesiyle kapattı; **açık risk** olarak kaydedildi (D-074).
6. **`fitness_class` `high` bandı boş** · **`landmark_energy` doygunluk riski**
   (6'da 1 tavanda).
7. **`z`'nin ölçülebilirliği nişe bağlı** — bilgilendirici hücre oranı
   **~%48** (13/27, D-120). ⚠ Sebep krizin gücü değil, **bireysel kanalın
   landmark'tan önce ateşlenmemesi** (D-120 §S.2).
11. ⚠ **Pozitif kontrol bir uç nokta değildir** — `Cov(w, energy_mean_over_life)`
    yalnız *"bu koşum seçilimi ölçebilir miydi"* sorusunu cevaplar; hiçbir
    kalıtım iddiası ona dayandırılamaz.
8. ⚠ **Kriz kanalı ile `TRAUMA` sınıfı imprint aynı şey değil** (§2.11/D-063).
9. **Sabitler kalibre edilmedi** — `METABOLIC_GAIN_CALIBRATED = False`,
   `POLARITY_COSINE_CALIBRATED = False`.
10. **GAP-3** (gen2 ilk olayda somatik ölçek boşluğu) ve **GAP-4**
    (kasa ↔ LoRA senkron kopukluğu) açık; ikincisi D-067'den sonra **büyüdü**.

✅ **Borçtan çıkanlar:** I0.4 (D-118'de bağlandı, artık sınır değil).

---

## 9. Slotlar

| # | slot | durum |
|---|---|---|
| ~~**1**~~ | Birincil uç nokta (`z`) | ✅ **KAPANDI (D-121)** — seçenek A + dejenere ilanı + pozitif kontrol |
| ~~**2**~~ | İkincil uç noktalar | ✅ **KAPANDI (D-122): YOK** — karar, eksik değil |
| ~~**3**~~ | Bütçe (P7-a) | ✅ **KAPANDI (D-122):** 3 tohum · N=8 · G=3 · 30 olay ⇒ 18 Price satırı |
| ~~**4**~~ | Tohum politikası | ✅ **KAPANDI (D-122):** **9911 · 9912 · 9913**, taze blok |
| — | Tasarım (P0–P6) | ✅ kapalı |
| — | Geçerlilik kriterleri | ✅ kapalı (§5) |
| — | Okuma kuralları | ✅ kapalı (§6) |
| — | Sapma / null politikası | ✅ kapalı (§10/§11) |

---

## 10. Sapma politikası

Koşum sırasında ya da sonrasında protokole aykırı hiçbir değişiklik yapılmaz.
Zorunlu bir değişiklik çıkarsa: koşum **durdurulur**, D-kaydı açılır, ve
sonuç **keşifsel** olarak etiketlenir — gizlenmez.

⚠ **Meşru kalan tek istisna:** hesabı değiştirmeyen **saf raporlama/aletleme**
eklemesi (§2.10). D-112 · D-116 · D-117 · D-118 bu sınıftaydı.

---

## 11. Null sonuç politikası

**Null meşru bilimsel çıktıdır ve gizlenmez.** Sonuç üç sınıftan biriyle
etiketlenir:

| sınıf | ne demek |
|---|---|
| **alet null'ı** | ölçüm makinesi görebilecek durumda değildi (B2 bu sınıftaydı, D-053) |
| **evren null'ı** | makine çalıştı, evren ayrım üretmedi |
| **etki null'ı** | ayrım vardı, kollar farklı çıkmadı |

⚠ Hangi sınıf olduğu **koşumdan önce yazılan geçerlilik kriterleriyle** (§5)
belirlenir, sonuçtan sonra seçilmez.

---

## 12. Alet kimliği — 🔒 **DONDURULDU**

Koşumdan önce, koşumun kullanacağı sabitlerden **okunarak** üretildi (§2.8).
Sonuç JSON'u aynı bloğu kendisi de yazar; **ikisi ayrışırsa koşum geçersizdir.**

```json
{
 "backend": "local",
 "model_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
 "quantization": {"load_in_4bit": true, "quant_type": "nf4",
                  "compute_dtype": "torch.float16", "double_quant": true,
                  "device_map": "auto"},
 "dpo": {"beta": 0.1, "learning_rate": 1e-06, "epochs": 1, "batch_size": 1,
         "gradient_accumulation_steps": 4, "effective_batch_size": 4,
         "max_sequence_tokens": 512, "max_grad_norm": 1.0},
 "lora": {"choice": "explicit_on", "rank": 8, "alpha": 16},
 "metabolism": {"gain_max": 0.5, "gain_half_saturation": 2.0,
                "grace_events": 10, "calibrated": false,
                "death_on_exhaustion": true},
 "fitness": {"w_energy": 0.4, "w_pool": 0.3, "w_survival": 0.3,
             "pool_term_per_event_max": 8.0,
             "energy_reading": "mean_over_life"},
 "endpoints": {"landmark_event": 10},
 "sampling": {"do_sample": false, "temperature": 0.2, "max_new_tokens": 64},
 "cuda_allocator": {"env": "PYTORCH_CUDA_ALLOC_CONF",
                    "value": "expandable_segments:True", "applied": true},
 "seeds": {"n": 3, "list": [9911, 9912, 9913]},
 "versions": {"python": "3.14.6", "torch": "2.13.0",
              "transformers": "5.14.1", "peft": "0.20.0",
              "bitsandbytes": "0.50.0", "accelerate": "1.14.0",
              "numpy": "2.4.5", "scipy": "1.18.0"}
}
```

⚠ **Okuma notları:**

- `temperature: 0.2` **ama `do_sample: false`** ⇒ üretim **greedy**; sıcaklık
  okunuyor, kullanılmıyor (D-026).
- `calibrated: false` — üç metabolik sabit **kalibre edilmedi**, olduğu gibi
  kilitlendi (K4/D-070). Ölçülmüş gibi okunamaz.
- `n_agent_dirs` dondurulmadı: koşum sırasında **büyüyor**, ve I0.7 zaten
  planlanan id'lere bakıyor.
- `argv` dondurulmadı: koşuma özgüdür, sonuç dosyası kendi argv'sini yazar.

---

## 13. Koşum komutu — tam olarak bu

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9911 9912 9913 --n-agents 8 --n-generations 3 --events 30 \
  --lora --fresh-pasture \
  --results dau_runs/c2_population_n8_g3_s3.json
```

⚠ `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez** — `main()` kuruyor (D-116).
