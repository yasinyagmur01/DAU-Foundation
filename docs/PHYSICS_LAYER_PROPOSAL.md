# Fizik Değişikliği — Katman Katman Öneri

**Durum: TASLAK · 2026-08-20 · karar Yasin'in (D-007) · henüz D-kaydı yok**

⚠️ Bu belge bir **öneri**dir, karar değil. Kod yazılmadı. Onay gelirse
ön-taahhüt + D-kaydı **koda dokunmadan önce** commit edilir (D-154/D-160 deseni).

## İşaretler
✅ iyi haber · ❌ kötü haber · ⚠️ uyarı/sınır · **KARAR** senin

---

# 0. ⚠️ ÖNCE BİR DÜZELTME — önceki teşhisim yanlıştı

Bu belgeyi yazmaya *"kıtlık ısırmıyor"* teşhisiyle başladım. **Kodu ve veriyi
ölçtüm, teşhis yanlış çıktı.** Düzeltmeden devam etmek, yanlış bir premise
üzerine fizik değiştirmek olurdu.

**Hatanın kaynağı (K4):** sonda-3'ün **tek** bir sayısını (`pool_ratio_end =
0.757`) genelledim ve *"havuz hiç ısırmıyor"* diye okudum. O sayı sonda-3'ün
**birinci neslinin** sayısıydı.

**Gerçek tablo — 34 nesil-hücresi, üç koşum:**

| havuz rejimi | kaç hücre |
|---|---|
| **Çöktü** (`pool_ratio_end = 0.000`) | **22** |
| Arada (0.00–0.45) | 4 |
| Hiç ısırmadı (≥ 0.45) | 8 |

⇒ ❌ *"Kıtlık ısırmıyor"* **yanlış**. Havuz hücrelerin çoğunda **tamamen
çöküyor**.

---

# 1. Düzeltilmiş teşhis — ve belirleyici ölçüm

Havuzun çöküp çökmemesi **tohuma göre değişiyor**, ve bu değişkenlik
farklılaşmayı doğrudan belirliyor. Kurucu neslin ajanları:

| tohum | kol | `pool_ratio_end` (nesil 1) | farklı `F_agent` | farklı `Δhavuz` | farklı ömür |
|---|---|---|---|---|---|
| **9917** | lived / shuffle | **0.000** (çöktü) | **3** | **3** | **2** |
| 9918 | lived / shuffle | 0.513 | 1 | 1 | 1 |
| 9919 | lived / shuffle | 0.561 | 1 | 1 | 1 |
| 9916 | lived / shuffle | 0.757 | 1 | 1 | 1 |

## ⭐ Bunun söylediği şey teşhisi tersine çeviriyor

> ✅ **P0-① (sıralı erişim) BOZUK DEĞİL. Havuz gerçekten kıtlaştığında
> kurucuları ayrıştırıyor — tasarlandığı gibi.**
>
> ❌ **Sorun havuzun 4 tohumun 3'ünde birinci nesilde hiç kıtlaşmaması.**

Ve bu, D-081'in *"bu evrende kademeli kıtlık yok, kıtlık **anı** var"*
tespitinin doğrudan kanıtı. Havuz **iki kararlı durumda**:

- **ya çöker** (ve o zaman ayrışma olur, ama geç ve şiddetli),
- **ya hiç ısırmaz** (ve ajanlar bit düzeyinde özdeş kalır).

Arada bir rejim **yok**. Gerçek fonksiyonlarla ölçüldü (`step_pool`,
8 ajan × 8.0 talep): eksik alma **olay 17'ye kadar tam olarak sıfır**, sonra
havuz **sıfıra** çakılıyor ve orada kalıyor (soğurucu durum).

⇒ **Değiştirilecek şey kıtlığın VARLIĞI değil, BİÇİMİ.**

---

# 2. Tasarım hedefi — tek cümle

> Kıtlığı **ikili** (çöktü / hiç ısırmadı) olmaktan çıkarıp **kademeli** hâle
> getir; böylece sıralı erişimin ayrıştıracağı bir eksik-alma farkı **her
> nesilde, her tohumda, birinci olaydan itibaren** var olsun.

⛔ **Bu, davranışa dokunmuyor** — dolayısıyla K7'yi ve aksiyomu ihlal etmiyor.
Değişen şey **ortamın karnesi**, ajanın kararı değil (D-082/§P.5'in ölçütü).

---

# 3. KATMAN 1 — hasat kuralı (bu aşamada YALNIZ bu)

## 3.1 Ne değişiyor

**Tek fikir:** bir ajanın bir olayda alabileceği miktar, **o an kalan stokla
orantılı bir tavana** tabi olur. Talep (`8.0`) **değişmiyor** — tavan değişiyor.

```
cap_i = EXTRACTION_LIMIT_RATIO × (kalan_stok / N)
alınan_i = min(talep_i, cap_i, kalan_stok)
```

⭐ **Tavan, sıra kendisine geldiğinde KALAN stoktan hesaplanır.** Ayrışmayı
üreten şey budur: erken servis edilen daha büyük bir stok görür. Rotasyon
(D-104) bunun **kalıcı** olmasını engeller, **var olmasını** değil (D-079/D-083).

## 3.2 Nerede değişiyor

| dosya | fonksiyon | değişiklik |
|---|---|---|
| `dau/society/environment.py` | `realized_extractions_sequential` | döngü içine tavan eklenir; `available` zaten adım adım azalıyor |
| `dau/society/environment.py` | `realized_extractions` (orantılı yol) | aynı tavan, N=1 ve orantılı kol için |
| `dau/society/environment.py` | sabit bloğu (satır ~19–23) | `EXTRACTION_LIMIT_RATIO` eklenir |

⛔ **Dokunulmayanlar** — hepsi bilerek:

| ne | neden |
|---|---|
| `EXTRACTION_DEFECT = 8.0` ve karar→çıkarım eşlemesi | **Talep davranıştır**; ona dokunmak K7 ihlali olur |
| `POOL_MAX`, `POOL_INIT`, `POOL_REGEN_RATE`, `COLLAPSE_EPSILON` | Hiçbir mevcut sabitin **değeri** değişmiyor |
| `metabolic_gain` ve sabitleri | Fonksiyon aynı; girdisi (gerçekleşen hasat) doğal olarak değişiyor |
| `LANDMARK_EVENT`, travma eşiği, fitness bantları | Bu katmanın konusu değil |
| Prompt, karar akışı, adapter yolu | Hiçbiri |

## 3.3 ⭐ Yeni sabit — ve **yeni serbest parametre yok**

```
EXTRACTION_LIMIT_RATIO = EXTRACTION_DEFECT / POOL_INIT = 8.0 / 80.0 = 0.10
```

**Türetme, sonuca bakmadan:** *"azami talebin, başlangıçtaki kişi başı stokta
tam olarak bağlayıcı hâle geldiği oran."* Yani:

- Başlangıçta (`stok/kişi = 80`): tavan `= 8.0` **= talep** ⇒ eksik alma **yok**.
- Stok bir adım düştüğü anda tavan talebin **altına** düşer ⇒ eksik alma
  **başlar** ve stokla birlikte **kademeli** büyür.

⇒ Değer **iki mevcut sabitin oranı**. Hiçbir pilot verisi girmiyor; `§2.7`
karşılanıyor — `LANDMARK_EVENT`'in `METABOLIC_GRACE_EVENTS`'e bağlanmasıyla
**aynı** türetme biçimi.

⚠️ **AMADS'ın `0.12`'si TAŞINMIYOR.** Oradan alınan şey **form** (stoka oranlı
tavan) ve **türetme disiplini**, değer değil — DAU'nun ölçeği farklı.

## 3.4 Projeksiyon — ⚠️ **hesap, ölçüm değil**

Gerçek sabitlerle, 8 ajan, hepsi DEFECT, 30 olay:

| | bugün (sabit kota) | öneri (stoka oranlı tavan) |
|---|---|---|
| olay 1 | havuz 0.744 · eksik **0.00** | havuz 0.746 · **tur içi yayılım 0.45** |
| olay 5 | havuz 0.555 · eksik **0.00** | havuz 0.600 · yayılım **0.56** |
| olay 10 | havuz 0.339 · eksik **0.00** | havuz 0.501 · yayılım **0.47** |
| olay 20 | havuz **0.000** (çöktü) | havuz 0.404 · yayılım 0.38 |
| olay 30 | havuz **0.000** | havuz **0.359** · yayılım 0.33 |

✅ **Üç şey birden düzeliyor:**

1. **Eksik alma birinci olaydan itibaren var** (bugün olay 17'ye kadar tam sıfır)
   ⇒ sıralı erişimin ayrıştıracağı bir gradyan **her zaman** mevcut.
2. **Tur içi yayılım 0.33–0.56.** Karşılaştırma: D-083 bugünkü kuralla,
   landmark penceresinde, rotasyonlu yayılımı **0.071** ölçtü ⇒ **~5–8 kat**.
3. **Çöküş soğurucu olmaktan çıkıyor** — havuz ~%36'da dengeleniyor. Stok
   düştükçe tavan da düşüyor, yenilenme yetişebiliyor. ⇒ Bütün ajanların aynı
   anda ölmesi biter, **ömür farkı** doğar.

## 3.5 ⚠️ Riskler — ilan

| risk | büyüklüğü | ölçülen dayanak |
|---|---|---|
| Enerji geliri düşer, ajanlar erken ölür | ⚠️ **küçük** — `metabolic_gain` içbükey: hasat 8.0 → 3.7 iken kazanç **0.400 → 0.325** (**−%19**), doğrusal olsaydı −%54 olurdu | `metabolic_gain` gerçek fonksiyonla hesaplandı |
| Havuz artık hiç çökmez ⇒ kriz kanalı (S5/K6) hiç ateşlenmez | ⚠️ **gerçek** — bugün krizlerin bir kısmı çöküşten geliyor | Projeksiyonda havuz %36'da kalıyor |
| `cooperate` (2.0) tavanın altında kalır ⇒ hiç bağlanmaz | ✅ **istenen** — davranışsal sıralama korunuyor, tavan yalnız aç talebi kısıyor | tavan olay 30'da ~3.7 > 2.0 |
| Tur içi yayılım rotasyonla sönebilir | ⚠️ açık — D-083 rotasyonun yayılımı **4.5 kat** kıstığını ölçtü; 0.45 → ~0.10 kalabilir | D-083 |
| **Bütün sayılar sıfırlanır** | ❌ **kesin** — pilot, sonda-3, C2 karşılaştırılamaz hâle gelir | — |

## 3.6 Bunu ne kanıtlayacak — kapı, test, kontrol

**Yeni kapı — `I5.6` (FLAG):** *"eksik alma gradyanı var mı?"*
Bir nesilde hiçbir olayda `talep > alınan` olmadıysa bayrak. ⇒ Tavan
bağlamadıysa bu katman **hiçbir şey yapmamıştır** ve koşum bunu **kendi
yüzünde** söyler (K6).

**K-kontrolleri:**
- **K1** — GPU koşumundan önce mekanizma kontrolü yazılır (hangi bayrak tavanı
  kapatır: hiçbiri; `--mock-llm` talebi kanned yapar ⇒ **kullanılmaz**).
- **K2** — test **en az iki ajanla** ve **iki farklı stok düzeyiyle**.
- **K3** — testin `step_pool` / `advance_commons` **çağrı yerinden** geçmesi.
- **K5** — md5'li, önbelleksiz mutasyon turu.

**Geriye dönük kontrol:** yeni kural eski koşum verisine uygulanıp *"eksik alma
ne zaman başlardı"* hesaplanır — **kod değişmeden önce**.

## 3.7 Pilot ve ön-taahhüt

**Koşum:** 3 taze tohum (**9920–9922**), N=8, G=4, 30 olay, `lived shuffle`
⇒ ~6–9 sa.

🔒 **Koşumdan ÖNCE yazılacak okuma kuralları** (öneri):

| # | soru | kural |
|---|---|---|
| **P1** | Kıtlık **kademeli** mi oldu? | 3 tohumun **≥ 2'sinde** birinci nesilde eksik alma **olay ≤ 3'te** başladı ⇒ ✅ |
| **P2** | Kurucular ayrışıyor mu? | 6 kurucu hücrenin **≥ 4'ünde** `Var(F_agent) > 0` ⇒ ✅ **(bugün 8'de 2)** |
| **P3** | Zincirin geri kalanı **kendiliğinden** oynadı mı? | `k` dağılımı · `cooperate` sayısı · tanımlılık oranı **betimleyici** okunur, eşik yok |

⛔ **P3 eşiksiz, bilerek.** Zincir hakkındaki okumam (bir kaldıraç üçünü birden
oynatır) bir **iddia**dır; kural koymak onu doğrulanamaz kılardı. Ölçülür ve
yazılır — tutmadıysa **tutmadı** diye yazılır.

⛔ **Okunmayacaklar (L9):** kovaryans · kol farkı · etki büyüklüğü · işaret.

---

# 4. Katman planı — her katman iddiayı **hangi yönde** genişletiyor

Bugünkü ön-kayıt §1 iddiayı beş yerde daraltıyor. Her katman **bir daraltmayı**
hedefliyor. ⛔ **Bir katman bitmeden diğeri açılmaz** — birlikte değiştirilirse
hangisinin işe yaradığı **bilinemez**.

| # | katman | kaldıraç | kaldırdığı sınır | iddia ne kazanır | tetik |
|---|---|---|---|---|---|
| **1** | **Kademeli kıtlık** | stoka oranlı tavan | ❌ *"farklılaşmanın tek kaynağı adapter"* (D-129/D-130) — **aksiyoma en yakın tehdit** | ⭐ **İz YAŞAMAKTAN doğuyor**, yalnız eğitimden değil. Aksiyomun çekirdeği | **şimdi** |
| **1-b** | *(katman 1'in yan ürünü, ölçülür)* | — | **L12** — `null` donmuş klon popülasyonu | `null` bilgilendirici olur ⇒ **sürüklenme ile seçilim ayrılabilir** | P3 |
| **2** | **`k` değişkenleşsin** | doğumdaki beraberlik-bozma | **L3** — `z` etkin olarak tek boyutlu | Drift'in **içeriği/yönü**, yalnız büyüklüğü değil | katman 1 sonrası `k` hâlâ sabitse |
| **3** | **Karar kanalı katılsın** | enerji düşüşü ajanı D-090'ın bölgesine soksun | **L18** — davranış çökük | **Kararlar** da ayrıştırıyor, yalnız ortam değil | katman 1 sonrası `cooperate` hâlâ 0 ise |
| **4** | **Birikimli kalıtım** | G artışı | **L10/L11** | **Nesiller arası eğilim** iddiası | 1–3 tuttuysa |

⚠️ **Katman 3 en hassası:** *"davranışı düzelt"* K7'yi ihlal eder. Meşru tek yol
**dünyayı pahalı yapmak** (D-090: bölge var, ajanlar oraya girmiyor). Ve katman
1 bunu **kendiliğinden** yapıyor olabilir — ölçülecek (P3).

⚠️ **Katman 2'nin kaldıracı henüz belirsiz.** D-137 ölçtü ki spillover matrisi
**işe yaramıyor** (`k` sabit olduğu için). Gerçek kaldıraç doğumdaki
beraberlik-bozmada, ve **tasarlanmadı**.

---

# 5. ⛔ Bu aşamada YAPILMAYACAKLAR

- Talebi (`8.0`) değiştirmek — davranışa dokunmak, K7.
- `POOL_*` sabitlerinin **değerlerini** değiştirmek — gerek yok.
- Holling II (`h`) — türetmesi yok; tavan formu **aynı işi yeni parametresiz** yapıyor.
- Dört katmanı birlikte açmak.
- Ön-kaydı bu değişiklikten önce kilitlemek.

---

# 6. Karar için özet

**Onayın gerekiyor (D-007):**

1. Katman 1 uygulansın mı — stoka oranlı hasat tavanı?
2. `EXTRACTION_LIMIT_RATIO = EXTRACTION_DEFECT / POOL_INIT = 0.10` türetmesi
   kabul mü? (yeni serbest parametre yok)
3. Pilot 3 tohum / G=4 (~6–9 sa) mı, 2 tohum (~5 sa) mı?

**Onay gelirse sıra:** ön-taahhüt + K1 kaydı commit → kod + testler + `I5.6`
kapısı + K5 mutasyon turu → suite → commit → pilot → okuma → D-kaydı.
