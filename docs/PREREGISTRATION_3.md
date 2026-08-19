# Popülasyon C‴ — Üçüncü Ön-Kayıt

**Durum: 📝 TASLAK · 2026-08-19 · kuyruk 2.2 · ⛔⛔ KİLİTLENEMEZ — D-145**

⛔⛔ **KİLİT DURDURULDU (D-145).** Kilit öncesi denetim, bu belgedeki §3, §4 ve
§7'de **dört kusur** buldu. Aşağıdaki metin **tarihçe olarak duruyor**;
kusurlu maddeler yerinde işaretlendi ve **karar verilmeden yeniden
yazılmayacak**.

| # | kusur | nerede |
|---|---|---|
| 1 | Birincil alan `energy` C2'de **15 hücrenin 1'inde** ölçülebilirdi | §3.1 |
| 2 | ⛔⛔ Hangi alanın yazıldığı **kola değil TOHUMA** bağlı (kriz → `resource`, kriz yok → `energy`) ⇒ sabit alan tohumların bir kısmını **tamamen** atar | §3.1, §3.2 |
| 3 | ⛔⛔ `ΔP_active` üç değerli ve **sıfır-şişkin**; Wilcoxon sıfırları atar ⇒ **S=12'de reddedebilme ihtimali %6.6** | §4, §7 |
| 4 | Bütün bir kol-tohumun **hiç** Price satırı olmayabilir — üçüncü kategori tanımsız | §3.1 |

⇒ ⛔ **Yasin'in kararı bekleniyor (D-145 §7):** **A** kestirim koşumu (S=12,
24 sa, **hipotez testi yok**) · **B** test koşumu (S ≥ 30, **60 sa**) ·
**C** uç noktayı düzelt (⛔ §2.7 yasaklıyor).
**Öneri: A.**

⚠ **§7'nin MDE tablosu yanıltıcıdır** — sürekli, bağlaşımsız bir değişken
varsayıyor; gerçek uç nokta öyle değil. Karar verilene kadar **kullanılmaz**.

⚠ **Önceki iki ön-kayıt yürürlükte kalır.** `PREREGISTRATION.md` B2'yi,
`PREREGISTRATION_2.md` C2'yi bağlar; ikisi de **kapanmış bölümlerdir**. Bu
belge onları geçersiz kılmaz, **ayrı bir deneyi** bağlar. Çelişki görülürse
sessizce seçilmez, ilan edilir (§2.11).

---

## 0. Neden üçüncü bir ön-kayıt

İkinci ön-kayıt koşuldu (C2) ve sonucu **evren null'ıydı** (D-123): makine
çalıştı (`run_quality=clean`, 6/6 kapı, I4.1 identical, pozitif kontrol
hareket etti) ama **uç nokta ölçmedi** — 18 Price satırının yalnız **4'ü**
tanımlıydı.

Sebep sonradan bulundu ve **tek bir cümleye indi** (D-129/D-130):

> Farklılaşmanın tek kaynağı **adapter**. Sıralı erişim ancak **kıtlıkta**
> ısırır, kıtlık ancak davranış farkıyla doğar, davranış farkı ancak
> adapter'la. ⇒ `null` kolu zengin nişte **donmuş klon popülasyonu**.

Bu ön-kayıt o teşhisin sonuçlarını uygular: birincil karşıtlık **değişti**
(D-131), uç noktanın **ölçülebilirliği** artık kendisi bir uç nokta (D-143),
ve test istatistiği **tohum başına bir skalere** indirgendi (D-140).

---

## 1. İddia

Sınanan parça (aksiyomun **tamamı değil**):

> Bir ajanın **yaşayarak edindiği izin yönü**, popülasyonda **kimin varis
> bıraktığıyla** ilişkilidir; ve iz **tersine çevrildiğinde** bu ilişki
> değişir.

⛔ **Bu ön-kaydın iddia ETMEYECEKLERİ** — olumlu sonuçta bile:

- **Birey düzeyi hiçbir şey.** P1 kol başına ayrı popülasyon veriyor ⇒ iddia
  **grup düzeyinde** kalır.
- *"LLM ajanlarında Lamarckçı kalıtım vardır"* — tek model, tek niş ailesi,
  **n = 1 deney**.
- **`z`'nin hangi alanında** olduğu — `z` etkin olarak **tek boyutludur**
  (L3).
- *"Seçilim"* — `null` kolunda sürüklenme ile seçilim ayrılamaz (L12).
- **Nesiller arası eğilim** — nesil satırları **betimleyicidir** (D-141).

---

## 2. Tasarım — ✅ kilitli (C2'den devralındı, iki değişiklikle)

| # | Karar | Seçilen | Kayıt |
|---|---|---|---|
| **P0** | Ajanlar nasıl farklılaşır | ① sıralı erişim, **tur başına rotasyon** | D-104 |
| **P1** | Kol yapısı | kol başına **ayrı popülasyon ve ayrı mera** | D-095 |
| **P2** | Seçilim şeması | turnuva, **k = 2** | D-094 |
| **P3** | Üreme | sabit N; ölen her ajanın yerine turnuva kazananından bir varis ⇒ `w ∈ {0,1,2,…}` | D-094 |
| **P4** | Katmanlar | `F_agent` (girdi) → `w` (varis) → `z` (sonuç), **üçü ayrı** | D-094 |
| **P5** | Havuz | kapasite **N ile ölçeklenir**, kişi başı 100/80 sabit | D-081 |
| **P6** | Faz | **tek faz**; `delta_pe` uç noktası yok | D-095 |
| — | Mera | **her nesilde taze** | D-104 |
| — | Kanal 2 | ebeveynin adapter'ı **varise kopyalanır** | D-102 |
| — | Price | **bir nesil gecikmeli**: G nesil ⇒ **G−1** satır | D-101 |
| — | N · G · olay | **N = 8** · **G = 3** · **30 olay** | D-107, C2 |
| ⭐ **YENİ-1** | **Birincil karşıtlık** | **`lived` ↔ `shuffle`**; `null` **betimleyici** | **D-131** |
| ⭐ **YENİ-2** | **Test birimi** | tohum başına **ortalanmış** değer; nesil satırları **raporlanır ama test edilmez** | **D-141** |

⚠ **Hiçbir sabit değişmedi.** `constraints.py` C2'deki hâliyle; özellikle
`DELTA_THRESHOLD_DEEP = 0.70` (D-143) ve `CROSS_AXIS_SPILLOVER = 0.20`
(D-137) **korunuyor**.

---

## 3. Uç noktalar — ✅ **SLOT 1 KAPALI (D-143 · D-140)**

⭐ **İki eş-birincil uç nokta.** İkisi **farklı soru** soruyor ve ikisi de
koşumdan **önce** tanımlı.

### 3.1 Birincil A — `ΔP_active` (ölçülebilirlik)

| | |
|---|---|
| **hücre** | (kol, tohum, nesil geçişi) üçlüsü |
| **alan** | ⭐ **`energy`** — aşağıda gerekçelendirildi |
| **aktif** | o hücrenin **`energy`** alanında `selection_estimable = True`, yani `Var(z) > 0` |
| **alan yoksa** | hücre **inaktiftir** — `energy` anahtarı hiç yazılmamışsa hiçbir ajan o alanda drift taşımıyor demektir, ve *"eksik veri"* değil **gözlem**tir |
| **`P_active(kol, tohum)`** | o kol-tohumun **G−1 = 2** geçişinden aktif olanların **oranı** ∈ {0, ½, 1} |
| **karşıtlık** | `ΔP_active(tohum) = P_active(lived) − P_active(shuffle)` |

⚠ **Neden `energy`, ve neden bu etkiye bakmak değil.** `selection_estimable`
bayrağı **alan başına** yazılıyor, dolayısıyla *"hangi alan"* ön-kayıtta
söylenmek zorunda. Gerekçe **mekaniktir, sonuca bakmaz** (D-130 §9):

- `resource` — krizin **sabit** alanı, ve kriz **bütün kola aynı anda** vurur
  ⇒ herkes aynı skarı alır ⇒ hücre içi bilgi taşımaz (L14).
- `social` · `uncertainty` — argmax'ı **hiç kazanmıyorlar**; C2'de 216 yaşamda
  **sıfır kez** yazıldılar (D-136 bunun sebebini ölçtü: skaler spillover).
- ⇒ **`energy`, bireysel kanalın tek yazdığı alandır.**

⚠ **Bedeli açıkça:** C2'de `energy` 216 okumanın **11'inde** doluydu ⇒
`P_active` **düşük** beklenmelidir. Bu tasarımın zayıflığı değil, ölçtüğü
şeyin ta kendisidir (§0).

**Betimleyici olarak dört alanın hepsi ayrı ayrı raporlanır** (§3.3) — ama
birincil **yalnız `energy`**, ve sonradan alan değiştirilemez (L9).

**Sorduğu:** *yaşanmış iz, uç noktayı daha sık **ölçülebilir** yapıyor mu?*

⛔ **`P_active` bir ön-eleme filtresi DEĞİLDİR, bir sonuçtur** (D-140/U10).
Eşiği geçmek müdahaleden etkilenebilir ve bu bizde **varsayımsal değildir**.

### 3.2 Birincil B — `ΔCov_cond` (koşullu seçilim)

| | |
|---|---|
| **alan** | ⭐ **`energy`** — §3.1'deki gerekçenin aynısı, ve **aynı alan** olmak zorunda: iki eş-birincil farklı alanlarda okunursa *"nerede ölçülebildi"* ile *"nerede seçilim vardı"* farklı şeyler hakkında olur |
| **`Cov_cond(kol, tohum)`** | o kol-tohumun **aktif** geçişlerindeki `energy` Price seçilim teriminin ortalaması |
| **karşıtlık** | `ΔCov_cond(tohum) = Cov_cond(lived) − Cov_cond(shuffle)` |
| **tanımsız** | bir kol-tohumun **hiç** aktif geçişi yoksa o tohum B'den **düşer** ve **sayılır** |

**Sorduğu:** *ölçülebilir olduğu yerde, iz seçilimle ilişkili mi?*

⛔ **`Cov` İŞARETLİ kullanılır.** Mutlak değer, norm ya da `z` vektörünün
büyüklüğü **alınamaz** — ölçüldü: null'da `E[|Cov|] = 0.046` (sıfır değil) ve
gerçek fark **4.86 kat** sıkışıyor (D-142).

### 3.3 Betimleyici — test edilmez

`null` kolunun her iki niceliği · **nesil başına** Price satırları
(D-141) · `P_active`'in ham payı/paydası · `z`'nin dört ekseni (D-136) ·
`k` dağılımı (D-138) · π ve PE_w doygunluğu (D-138) · pozitif kontrol
(`energy_mean_over_life`, D-121).

⛔ Bunların hiçbirinden **sonradan** uç nokta seçilemez (L9).

---

## 4. Test — ✅ **SLOT 2 KAPALI (D-140 · D-141)**

| | |
|---|---|
| **birim** | **tohum** (Lazic 2010 — 8 ajan ve 2 geçiş **bağımsız replikat değil**) |
| **test** | eşleştirilmiş **Wilcoxon signed-rank**, **çift yönlü** |
| **α** | 0.05, ⚠ **iki eş-birincil için Holm-Bonferroni** ⇒ ilk test **0.025** |
| **etki ölçüsü** | Cohen's `d_z` = ortalama(Δ) / SD(Δ), tohumlar üzerinden |
| **güç** | 0.80 |

⚠ **Neden Holm:** iki eş-birincilden **herhangi birinde** olumlu sonuç
iddiası kurulursa hata oranı şişer. Düzeltme **koşumdan önce** ilan ediliyor
ve bedeli §7'nin MDE sütununda **görünüyor**.

⚠ **Neden Wilcoxon:** `ΔCov`'un dağılımı bilinmiyor ve `ΔP_active` üç
değerli. D-052'nin seçimiyle aynı; MDE'ye ARE = 3/π bedeli **dahil**.

---

## 5. Geçerlilik kriterleri — koşum başlamadan sabit

Aşağıdakilerden **biri** düşerse koşum **bilgisizdir** ve öyle raporlanır;
uç noktalar **yorumlanmaz**.

| # | kapı |
|---|---|
| **V1** | `run_quality = clean` · ⚠ **preflight 6/6 — ama 6/26** (aşağıya bak) |
| **V2** | **I4.1 replay `identical`** |
| **V3** | `PYTHONHASHSEED=0` · `TORCH_DETERMINISTIC_WARN_ONLY=False` (I0.6) |
| **V4** | I0.7 temiz başlangıç — tohum bloğu diskte adapter bırakmamış |
| **V5** | `I1.1` — her eğitim kolunda `Σ\|lora_B\|` hareket etti |
| **V6** | **`Var(F_agent) > 0`**, `lived` ve `shuffle` kollarının **her ikisinde** ve **her nesilde** |

⚠ **V6 etkiye bakmak değildir** (L9): kol **farkına** değil, seçilim
girdisinin **var olup olmadığına** bakıyor, ve kural koşumdan **önce**
yazıldı. `Var(F_agent) = 0` ise turnuva yazı-turadır ve `Cov(w,z)` seçilim
hakkında **bilgisizdir**.

⚠ **V6 `null` kolunu KAPSAMAZ** — D-129 o kolun bu nişte donmuş olabileceğini
ölçtü ve D-131 onu betimleyiciye indirdi.

### ⛔ 5.1 Kapı kapsamı — *"6/6"* **tam kapsam değildir** (D-147/AV-3)

⚠ **Bu satır bir düzeltmedir.** V1 önce yalnız *"preflight 6/6"* diyordu ve bu
**tam kapsam gibi okunuyordu**. Ölçüldü: `PREFLIGHT_INVARIANTS.md` **26**
değişmez tanımlıyor, popülasyon yolunda **6'sı** bağlı.

| durum | kapılar |
|---|---|
| ✅ **bağlı** (6) | `I0.3` · `I0.4` · `I0.6` · `I0.7` · `I1.1` · `I4.1` |
| ⛔ **bağlı değil** (20) | `I0.1 I0.2 I0.5 I1.2 I1.3 I1.3b I1.4 I1.5 I2.1 I2.2 I2.3 I3.1 I3.2 I3.3 I3.4 I4.2 I5.1 I5.2 I5.3 I5.4` |

**İkisi bu deneyin iddiasına doğrudan dokunuyor ve ön-kayıttan ÖNCE
bağlanmalıdır:**

- **`I4.2`** (ABORT) — *gen2 öncesi RNG durumu kol-bağımsız* (GAP-12). Koşum
  çok nesilli; nesiller arası determinizmi kapıya bağlayan tek şey buydu.
- **`I5.4`** (FLAG) — *inherited somatic scale gen2'de ≥1 kez uygulandı*
  (GAP-3). ⛔ İddia **kalıtım** hakkında ve sembolik kanalın varise
  ulaştığını doğrulayan kapı budur.

⚠ **`I2.1`** (*"iki kol özdeşse dur"*, ABORT) olduğu gibi bağlanamaz:
popülasyonda **gen1 tasarım gereği özdeştir** ⇒ meşru bir durumda abort
ederdi. **Uyarlanması** gerekir, ve bunu bugüne kadar kimse yazmamıştı.

⚠ Kalan 17 kapı **sınıflandırılmadı** — hangisinin N/A hangisinin eksik
olduğu **denetlenmedi**. Kilitten önce sınıflandırılır ya da *"bağlı değil,
sınıflandırılmadı"* diye **ilan edilir**. Sessizce geçilmez.

---

## 6. Okuma kuralları — koşumdan önce tanımlı

### 6.1 Sonuç sınıfları

| sınıf | koşul |
|---|---|
| **ALET NULL'I** | V1–V6'dan biri düştü ⇒ *"ölçemedik"* |
| **EVREN NULL'I** | kapılar geçti ama **`P_active` her iki kolda ~0** ⇒ evren uç noktayı üretmedi |
| **ETKİ NULL'I** | kapılar geçti, `P_active > 0`, ama `p > α` ⇒ *"şu MDE'nin altında güçsüzüz"* |
| **POZİTİF** | `p ≤ α` (Holm sonrası), her iki eş-birincil ayrı ayrı raporlanır |

### 6.2 ⛔ Anlamsız sonuç nasıl yazılır

Aşağıdaki kalıp **bağlayıcıdır** (DR #12 §5, ⚠ tohum tarifi düzeltilerek):

> *"Birincil karşıtlık `ΔX = [ort]` (SD = […], p = […], `d_z` = […]). Gözlenen
> etki, ön-ilan edilmiş asgari saptanabilir etki `d_z = [MDE]`'nin altında
> kaldığı için bu veri H0'ı reddetmeye yetmiyor. Bu **etkinin yokluğunun
> kanıtı değildir**; deneyimden doğan bir etki varsa büyüklüğü
> `d_z < [MDE]` ile sınırlıdır."*

⛔ *"Etki yok"* · *"aktarılmıyor"* · *"mekanizma yanlış"* **yazılamaz**.

### 6.3 Type S / Type M

Anlamlı çıkan her sonuç için **işaret hatası** ve **büyüklük şişmesi**
riski birlikte raporlanır (Gelman & Carlin 2014, `10.1177/1745691614551642`).
⚠ Küçük `S` + gürültülü uç noktada anlamlılık, etkiyi **abartma** eğilimindedir.

---

## 7. Bütçe ve tohum sayısı — ⛔ **SLOT 3 AÇIK**

**Maliyet (ölçüldü, C2):** tohum başına **~2 saat**. ⚠ **Nişler arası yayılım
2.3 kat** (toplam olay 104 ↔ 240) ⇒ tek sayı değil **aralık** verilir (K4).

**MDE — exact noncentral-t, sonra Wilcoxon ARE = 3/π.**
⚠ Yöntem **D-052'nin sayılarıyla doğrulandı**: `N=32 → 0.5113 / 0.5232` ve
`N=40 → 0.4543 / 0.4649`, D-052'nin yazdığıyla **birebir**.

| S | GPU saat | 2.3× aralık | MDE (α=.05) | **MDE (α=.025, Holm)** |
|---|---|---|---|---|
| 6 | 12 | 8–18 | 1.468 | **1.745** |
| 8 | 16 | 11–24 | 1.183 | **1.370** |
| **10** | **20** | **13–30** | 1.019 | **1.165** |
| **12** | **24** | **16–36** | 0.909 | **1.032** |
| 15 | 30 | 20–46 | 0.796 | **0.897** |
| 20 | 40 | 26–61 | 0.676 | **0.756** |

⚠ **S ≥ 6 matematiksel şart** — altında çift yönlü Wilcoxon α=0.05'te
reddedemez.

⛔ **SESOI ilan edilmiyor** (DR #1 §G.3, Lakens 2022 `10.1525/collabra.33267`).
`S` **bütçeden** seçilir ve **MDE ilan edilir**.

**Claude Code'un önerisi: `S = 12`** — 24 GPU saat (aralık 16–36), Holm
sonrası MDE `d_z = 1.032`. Gerekçe: S=10'dan S=12'ye geçiş MDE'yi 1.165 →
1.032 indiriyor (**%11**) ve 4 saate mal oluyor; S=15'e geçmek 6 saat daha
alıp yalnız 0.897'ye indiriyor. ⚠ **Bu bir bütçe önerisidir, bilimsel bir
gerekçe değil** — kararı Yasin verir.

⚠ **MDE'ler büyük ve bu bilerek yazılıyor:** `d_z ≈ 1.0` **büyük** bir etkidir.
Bu tasarım mütevazı etkileri **göremez** ve sonuç raporunda o **ilan edilir**.

**Tohum bloğu:** taze **9916+**, ardışık. ⚠ Kullanılmışlar: …9901–9904 ·
9911–9913 (C2) · 9915 (sonda-2) · 9305–9310 (mock).

**Durma kuralı:** koşum **tek atıştır**. Kilitten sonra tohum **eklenemez**;
eklenirse analiz **post-hoc** olur. Çökme hâlinde checkpoint'ten (D-111)
**aynı tohumlarla** devam edilir, tohum değiştirilmez.

---

## 8. İlan edilen sınırlar

| # | sınır | kayıt |
|---|---|---|
| **L1** | **n = 1 deney** — tek model (Llama-3.1-8B-Instruct), tek niş ailesi, tek kod tabanı | — |
| **L2** | İddia **grup düzeyinde**; P1 ayrı popülasyon veriyor ⇒ birey düzeyi çıkarım yok | D-095 |
| **L3** | ⭐ **`z` etkin olarak TEK BOYUTLU.** Birincil eksen `k` bütün olaylarda `resource_load`'a kilitli (**192/192**, ⚠ **karar-stub'lı keşifsel koşumda** ölçüldü; gerçek koşumda `k` artık kaydediliyor ve doğrulanabilir, D-138) ve ikincil eksenler `k`'nin sabit katı ⇒ **alan kimliği hakkında iddia yok**; kovaryans drift'in **büyüklüğü** üzerine | D-136, D-137 |
| **L4** | ⭐ **Tekrarlama birimi tohum.** 8 ajan ve G−1 geçiş **bağımsız replikat değil**; ajanlar ortak merada, nesiller adapter mirasıyla bağlı | D-140, Lazic 2010 |
| **L5** | ⭐ **Uç nokta `Cov`'un İŞARETLİ hâlidir.** Mutlak değer/norm alınamaz: null'da `E[\|Cov\|] = 0.046` ve etki **4.86 kat** sıkışır | D-142 |
| **L6** | ⭐ **Type S / Type M** riski — küçük `S`'te anlamlılık işaret ve büyüklük hatası taşır | D-140, Gelman & Carlin 2014 |
| **L7** | ⭐ **Price + güç analizi birleşiminin literatürde yayımlanmış örneği yok** ⇒ taklit edilen bir çerçeve değil, **ilan edilmiş bir sentez** | D-140 (boşluk ilanı) |
| **L8** | **Price kestirimi küçük N'de** klasik beklentiden sapabilir. ⚠ *"Eşleştirme iptal eder"* gerekçesi **düştü** (işaretli kestirimci null'da yansız ölçüldü, 0.89 SE), ama Rice'ın **en genel** koşulu kapsanmadı | D-140, D-142, Rice 2008 |
| **L9** | ⛔ **Hiçbir uç nokta etkiye bakılarak seçilmez.** Betimleyici alanlardan sonradan uç nokta türetilemez | süregelen |
| **L10** | **G = 3.** DR #11'in *"8 nesil"* normatifi **reddedildi**; birikimli kalıtım iddiası kurulamaz | D-132 §T.2 |
| **L11** | **Adapter sönümü / LoP** — 6/6 dizide 1.8×–4.8× azalma ölçüldü; uzun soyda sinyali **seyreltebilir**. Nesil satırları bunu **raporlar ama test etmez** | D-132, D-141 |
| **L12** | **`null` kolunda sürüklenme ile seçilim ayrılamaz** — bu nişte donmuş klon popülasyonu olabilir ⇒ **betimleyici** | D-129, D-131 |
| **L13** | ⭐ **Aktif hücre oranı düşük** (C2'de ~%22) ⇒ `Cov_cond` az hücreye dayanır; ⚠ ve **aktif hücreye koşullamak survivorship bias taşır** — eşiği geçmek müdahaleden etkilenebilir | D-143, D-140/U10 |
| **L14** | **Kriz müdahale-sonrasıdır** ve bütün kola **aynı anda** vurur ⇒ `z`'nin `resource` bileşeni hücre içi bilgi taşımaz | D-119/120, D-130 |
| **L15** | **I0.1/I0.2 popülasyon yolunda bağlı değil** | D-105 |
| **L16** | **GAP-10 / spillover skaler kalıyor.** Matris `k` sabit olduğu için skalerin üç kopyalı hâli olurdu; eşiği de geçirmiyordu (+%2.29) | D-137 |
| **L17** | **`to_landmark.max` reddedildi** (D-129, **2/4**) ve bu koşumda **kullanılmaz**. Yeniden açılması **üç şart** ister | D-143 §5 |
| **L18** | **Davranış çökük** — olayların %94–100'ünde DEFECT; K7 bilişsel önseli aksiyom gerekçesiyle kapattı ve bu **açık risktir** | D-068, D-074 |
| **L19** | **GAP-3** (gen2 ilk olayda somatik ölçek boşluğu) ve **GAP-4'ün ikinci yarısı** (silinen anının LoRA izi) **açık** | GAP tablosu |

---

## 9. Slotlar

| # | Slot | Durum |
|---|---|---|
| **1** | Uç noktalar (`ΔP_active` + `ΔCov_cond`) | ✅ **KAPALI** — D-143, D-140 |
| **2** | Test, α, düzeltme, etki ölçüsü | ✅ **KAPALI** — D-140, D-141 |
| **3** | **Tohum sayısı `S` ve bütçe** | ⛔ **AÇIK — Yasin** |
| **4** | Geçerlilik kapıları (V1–V6) | ✅ **KAPALI** |
| **5** | Sonuç sınıfları ve rapor dili | ✅ **KAPALI** |
| **6** | Alet kimliği | ⏳ **kilitte donacak** (§12) |

---

## 10. Sapma politikası

Koşum sırasında ön-kayıttan sapma gerekirse: koşum **durdurulur**, sapma
`DECISIONS.md`'ye **gerekçesiyle** yazılır, ve sonuç **keşifsel** damgalanır.
⛔ Sapma sessizce uygulanmaz (§2.11).

Çökme/OOM **sapma değildir**: checkpoint'ten aynı tohumlarla devam edilir.

---

## 11. Null sonuç politikası

**Null meşru bilimsel çıktıdır ve gizlenmez** (5 Değiştirilemez Yasak).
Sonuç ne olursa olsun `docs/C3_RESULTS.md` yazılır; §6.1'in sınıfı ve §8'in
sınırları **rapora aynen taşınır**.

⚠ **C2'nin dersi:** *"ölçemedik"* ile *"ölçtük, yoktu"* farkı bu ön-kayıtta
`P_active` sayesinde **tek bir sayıyla** kuruluyor — bu, üçüncü ön-kaydın
C2'ye göre asıl kazancıdır.

---

## 12. Alet kimliği — ⏳ kilitte dondurulacak

Kilit anında (kuyruk 2.3) buraya yazılacaklar: commit hash · `tool_identity`
çıktısı · model kimliği ve quantization · `constraints.py` özeti ·
`pip freeze` özeti · suite sayısı.

---

## 13. Koşum komutu — kilitte tam olarak yazılacak

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9916..<9916+S-1> --n-agents 8 --n-generations 3 --events 30 \
  --lora --fresh-pasture \
  --results dau_runs/c3_population_n8_g3_s<S>.json
```

⚠ **Dış `timeout` YOK** (D-126: I4.1 replay sırasında kesilirse sonuç dosyası
hiç yazılmaz). ⚠ `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez** (D-116).
