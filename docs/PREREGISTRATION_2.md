# Popülasyon C″ — İkinci Ön-Kayıt · ⚠ **TASLAK, KİLİTLİ DEĞİL**

**Durum: ✍️ taslak · 2026-08-18 · açık slot: 3** (Slot 1 kapandı, D-121)

⚠ **Bu belge henüz bir ön-kayıt değildir.** Slotlar kapanmadan hiçbir koşum
"doğrulayıcı" sayılmaz. Kapanma anında bu satır **🔒 KİLİTLİ** ile değişir,
commit hash'i yazılır ve alet kimliği §12'de dondurulur.

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

**Eski hâli (arşiv):** `z` = landmark'taki (olay 10) drift büyüklüğü, sabit
yaşta okunur.

⛔ **Kapanmadan koşum başlayamaz.** Sebep D-115'te ölçüldü: `z`'yi **iki yol**
yazıyor —

| yol | tetik | ajanlar arası bilgi |
|---|---|---|
| bireysel şaşırma | ajanın kendi `DeltaRecord`'u, `magnitude ≥ 0.7` | ✅ taşır (kriz olmayan tohumda 8 ajanda **5 farklı `z`**) |
| ⛔ ortak havuz krizi | `pool_ratio < 0.30` ⇒ **kolun tamamına aynı anda**, sabit büyüklük | ❌ **taşımaz** (kriz olan tohumda 8 ajanda **1–2 farklı `z`**) |

⇒ Kriz `z`'yi **doldurur ama eşitler**; `Cov(w, z)` sıfır çıkar ve sıfırın
sebebi *"hiçbir şey olmadı"* değil ***"herkese aynı şey oldu"*** olur.

**Açık seçenekler** (karar Yasin'in, D-007):

| | seçenek | bedeli |
|---|---|---|
| A | koru + krizin uç noktayı eşitlediğini ilan et | koşum büyük ihtimalle seviye 1'i boş verir |
| B | okuma anını kaydır | ⚠ sansürleme bedeli, D-081'de bir kez reddedildi |
| C | uç noktayı değiştir | B2 sıfırdan yazılır |
| D | **yalnız bireysel kanaldan oku** | ⚠ *"ortak şoklar uç noktaya girmiyor"* sınırı ilan edilir |
| E | `Cov(w,z)`'yi **ayrıştır** (hücre-içi + hücre-ortak), ikisini de raporla | ⚠ literatürdeki adı/tuzakları **DR #10'a soruldu** |

⚠ **D-117 sonrası her seçenek ölçülebilir:** hangi kanalın yazdığı artık
koşum sırasında günlüğe giriyor ve raporda **ayrı** çıkıyor.

⚠ **L9 geçerli:** uç nokta **etkiye bakılarak seçilmez**. Kol karşıtlığına
bakılmadı ve karar verilene kadar bakılmayacak.

---

## 4. Ön-kayıtlı ikincil uç noktalar — ⛔ **SLOT 2, AÇIK**

Adaylar (hiçbiri seçilmedi):

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

## 7. Bütçe ve durma kuralı — ⛔ **SLOT 3, AÇIK (P7-a)**

Biçimi karara bağlandı (D-110): *"kaç saat"* değil ***"olay oranını hangi
kesinlikle"***. ⚠ **D-115 sonrası oran yeniden tanımlanmalı — hangi kanalın
oranı?** ⇒ **Slot 1'e bağımlı**, ondan sonra kapanır.

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
| **2** | İkincil uç noktalar | ⛔ **AÇIK** — Slot 1 kapandı, sıra bunda |
| **3** | Bütçe (P7-a) | ⛔ **AÇIK** — ⭐ aranan oran artık belli: **bilgilendirici hücre oranı** (~13/27) |
| **4** | Tohum politikası | ⛔ **AÇIK** — kullanılmış tohumlar yeniden kullanılamaz (I0.7 abort eder) |
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

## 12. Alet kimliği — kilitte dondurulacak

Koşum sırasında `tool_identity` bloğu sonuç JSON'una yazılıyor ve şunları
**sabitlerden okuyor** (§2.8): backend · model · quantization · DPO ayarları ·
LoRA · metabolizma · fitness ağırlıkları · landmark ordinali · sampling ·
üreme kuralı · **CUDA tahsis edici** (D-116) · tohumlar · kütüphane sürümleri.

⚠ Kilit anında buraya **commit hash + ölçülen değerler** yazılır.
