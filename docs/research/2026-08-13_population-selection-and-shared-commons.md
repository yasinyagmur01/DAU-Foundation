# DR brief #6 — tek soy yerine popülasyon: seçilim şeması ve ortak havuz

**Öncelik: 1** — bir sonraki ön-kayıt bu cevaba bağlı. Popülasyon **fizik**
değişikliğidir; yanlış kurulursa kilit yeniden yazılır ve bir 13 saatlik
koşum daha harcanır.

**Durum:** gönderilmedi · **Tarih:** 2026-08-13

---

## 0. Bu brief'i okuyan için: neye ihtiyacımız var, neye yok

**İhtiyacımız olan:** küçük popülasyonlarda **üreme/seçilim şemasının** ve
**paylaşılan bir ortak kaynağın** deney tasarımına nasıl kurulduğuna dair
yerleşik yöntem bilgisi — adları, tuzakları, ve **ölçülmüş** karşılaştırmalar.

**İhtiyacımız olmayan:**

- **Bizim proje geçmişimiz.** Erişimin yok; makul görünen ama kaynaksız bir
  anlatı bize zarar verir.
- ⚠ **"Sizin kurulumunuz hangi sonucu verir" tahmini.** Etkiyi öngörüp
  tasarım seçmek post-hoc olur. **Geçerlilik ve ayırt etme gücü** ölçütleri
  istiyoruz, etki büyüklüğü değil.
- **LLM/prompt tarafı.** Ayrı turda kapandı (aşağıda §6).
- **Kod önerisi.** Uygulamayı biz yazıyoruz; sorumuz yöntem sorusu.

⚠ **Kaynak kimliği kritik ve sicilimiz kötü.** Önceki beş brief'te **yedi**
kaynak yanlış atfedildi: bir DOI (`10.1007/s00778-019-00574-9`) bir
hareket-ekolojisi makalesine atfedilmişti ama bir VLDB Journal derlemesine
ait; bir iddia yazar/yıl yerine dergi **ISSN**'iyle "kaynaklandırılmıştı";
Distinct-N ve Self-BLEU'nun ikisi birden "Papineni 2002"ye bağlanmıştı (o
BLEU'dur).

⚠ **Ve bu hata bize de oldu:** kendi yerel taramamızda Schoenfeld'in örneklem
makalesi için `10.2307/2530643` yazdık; açtığımızda **Greenland & Robins
1985** çıktı. Doğrusu `10.2307/2531021`. Yani doğrulama döngüsü tek taraflı
bir suçlama değil — biz de her kimliği Crossref/arXiv üzerinden **tek tek
açıyoruz** ve doğrulanmayanı kullanmıyoruz.

**Her iddia için yazar + yıl + kalıcı kimlik (DOI/arXiv) ver. Emin değilsen
"doğrulanamadı" yaz.** Uydurulmuş bir referans, cevapsız bir sorudan **daha**
pahalı.

---

## 1. Sistemin dürüst tarifi

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit, ajan başına LoRA adapter.
  Olay başına bir karar, olay-sıralı zaman (duvar saati yok).
- **Ortam:** lojistik yenilenen ortak kaynak havuzu (CPR). Karar → hasat
  miktarı deterministik bir eşlemeyle çıkıyor (LLM-yargıç yok).
- **Bedel:** hasat enerjiye dönüyor (içbükey/doygun kazanç eğrisi), boş havuz
  hiçbir şey vermiyor, enerji tükenince **yaşam biter**.
- **Nesil:** ata **bir** varis üretiyor. Varis anıları ve drift durumunu miras
  alıyor; **ebeveynin adapter'ını almıyor.**

⚠ **Birincil uç noktamız bir AĞIRLIK VEKTÖRÜ DEĞİLDİR.** Önceki bir turda bu
yanlış anlaşıldı ve cevabın yarısı optimizer gürültüsü üzerine kuruldu.
Doğrusu: **varisin sabit bir yaşta okunan drift durumunun büyüklük vektörü**
— üç alan (`resource`, `social`, `uncertainty`) üzerinde tanımlı, ajanın
yaşadıklarından türeyen bir **durum** ölçüsü. Model parametrelerine bakmıyor.

**Kontrol kolu:** aynı tercih çiftleri, tercih yönü **%100 ters** (`shuffle`)
+ hiç eğitilmemiş kol (`null`). Yani *"eğitim oldu mu"* değil, *"eğitimin
içeriği yaşama özgü mü"* soruluyor.

### 1.1 Değiştiremeyeceğimiz kısıtlar (öneriler bunlara uymalı)

| Kısıt | Ne demek |
|---|---|
| **Trait enjeksiyonu yok** | Ajana hiçbir kişilik/eğilim değeri **atanamaz**. Her şey yaşanandan çıkmalı. Bu bir aksiyom, tasarım tercihi değil |
| **Davranışsal önsel yok** | Karar kuralı / evrenselleştirme türü bilişsel önseller **kapalı** (aynı aksiyomun sonucu). ⚠ Bunun bedelini biliyoruz — §2.2 |
| **LLM-yargıç yok** | Bütün metrikler deterministik Python |
| **Duvar saati yok** | Zaman = olay sırası |

---

## 2. Neredeyiz: bedel kuruldu, seçilim katmanı hâlâ tek soy

### 2.1 Bedel çalışıyor

Önceki tasarımda ölüm yapısal olarak imkânsızdı ve hayatta kalma terimi 120
kolun 120'sinde 1.0 okuyordu. Metabolik döngü kapatıldıktan sonra (N=2 pilot,
keşifsel): yaşamlar 50 olaylık bütçeye karşı **19** ve **10** olayda bitti;
havuz çöktüğünde gerçekleşen hasat **8.0 → 6.17 → 0** diye düştü; bir varis
gen2'de **17**, diğerleri **20** olay yaşadı.

⇒ Bedel zinciri uçtan uca ateşliyor.

### 2.2 ⚠ Ama davranış çökük ve bunu **sormuyoruz**

Aynı pilotta ajanlar olayların **%94–100'ünde** en yüksek hasadı (defect)
seçmeye devam etti: bedeli ödüyor, havuzu çökertiyor, ölüyor ve
**değişmiyor**. Önceki bir turda bunun evrenimize özgü olmadığını, LLM
ajanlarının ortak kaynak ikilemini kendiliğinden çözemediğini öğrendik.

**Bu brief bunu çözmeyi sormuyor** — tek ölçülmüş kaldıraç (bilişsel önsel)
bizde aksiyom gereği kapalı (§1.1) ve bu **ilan edilmiş bir sınır** olarak
ön-kayda yazılacak. Sorumuz şu: *böyle bir popülasyonda seçilim iddiası
kurulabilir mi, ve kurulamıyorsa bunu **önceden** hangi ölçütle anlarız?*

### 2.3 Popülasyon tarafında elimizde ne var

| Zaten çoklu ajan | Hâlâ tek ajan |
|---|---|
| Havuz fiziği: N ajanın talebi **oransal** bölüşülüyor, kıtlıkta herkes eksik alıyor | Her ajan **kendi** havuz kopyasıyla doğuyor ⇒ şu an ortak mülk değil, **özel mülk** |
| Kriz travması ajan başına uygulanıyor | Grafik döngüsü akış başına **bir** ajan yürütüyor |
| İki-ajanlı sosyal katman (rakibin işbirliği olasılığı üzerine Markov beklentisi) | Üreme tekil: **1 ebeveyn → 1 varis**; "kim ürer, kaç varis" katmanı **yok** |

---

## 3. Asıl soru

**Ortak bir kaynağı paylaşan, onlarca bireylik bir popülasyonda seçilim
iddiası nasıl kurulur — ve müdahale (bizde: yaşanmış tercihlerle eğitim)
bireye uygulanıp ortam paylaşılıyorken kollar birbirini kirletmeden nasıl
karşılaştırılır?**

---

## 4. Cevaplanmasını istediğimiz sorular

### S1 — Küçük popülasyonda üreme/seçilim şeması

Onlarca bireylik popülasyonlarda hangi şemalar **yerleşik**: kesme
(truncation), turnuva, uygunlukla orantılı, Moran/durağan-durum (steady
state) mı nesil-nesil (generational) mi?

- Bunlar arasında **ölçülmüş** karşılaştırma var mı — hangisi küçük N'de
  seçilim baskısını korurken çeşitliliği en az yok ediyor?
- Popülasyon **sabit** mi tutulur, yoksa doğum/ölüm dengesine mi bırakılır?
  Bizde ölüm zaten davranışın sonucu — bu, sabit-boyut varsayımını ihlal
  ediyor mu?

### S2 — Sürüklenme (drift) mi seçilim mi: küçük N'de nasıl ayrılır

N onlarcayken rastgele sürüklenme gerçek bir rakip açıklama.

- Bir değişimin **seçilim** olduğunu göstermek için hangi tasarımlar
  kullanılıyor (tekrarlı/replike popülasyonlar, nötr işaretli soylar,
  sürüklenme-nötr kontroller)?
- Sürüklenmeyi dışlamak için **ölçülmüş** bir asgari N veya asgari nesil
  sayısı var mı, yoksa bu her zaman etki büyüklüğüne mi bağlı?
- Bizim `null` ve `shuffle` kollarımız bu rolü üstlenebilir mi, yoksa
  sürüklenme kontrolü **ayrı** bir şey mi?

### S3 — ⚠ Ortak havuzda kol kirlenmesi (bu brief'in en kritik sorusu)

Müdahale **bireye** uygulanıyor ama ortam **paylaşılıyor**. İki tasarım
mümkün ve sonuçları farklı:

- **(a) Kol başına ayrı havuz** — her kol kendi popülasyonu ve kendi
  otlağıyla koşar. Kollar bağımsız kalır, ama farklı davranışlar **doğrudan
  rekabet etmez**.
- **(b) Tek havuz, karışık kollar** — `lived`/`null`/`shuffle` ajanları aynı
  otlakta yaşar. Doğrudan rekabet olur, ama bir kolun aşırı hasadı diğerinin
  ortamını değiştirir ⇒ bağımsızlık varsayımı düşer.

Sorular:
- Bu ayrımın literatürde **adı** var mı, ve hangi koşulda hangisi
  savunulabilir sayılıyor?
- (b) seçilirse, bir kolun diğerinin ortamını değiştirmesi nasıl ele
  alınıyor — frekansa bağlı seçilim, referans/işaretli suş, yoksa istatistik
  düzeyinde mi (küme/kümelenmiş tasarım) düzeltiliyor?
- (a) seçilirse, "rekabet etmeden seçilim" iddiası hangi noktada zayıflar?

### S4 — Uygunluk hem seçilim girdisi hem ölçülen sonuçken

Popülasyonda uygunluk skorumuz **kimin ürediğini belirleyecek**, ve aynı
zamanda raporladığımız bir sonuç. Bu döngüsel.

- Yapay yaşam / deneysel evrim literatüründe bu döngüsellik nasıl
  kırılıyor — seçilim ölçütü ile sonuç ölçütünün **ayrı** tutulması standart
  mı, yoksa aynı olması kabul mü ediliyor?
- Uygunluğu ölçen ile seçen aynı sayıysa hangi çıkarımlar **geçersiz**
  oluyor?

### S5 — Kaç nesil: "birikimli kalıtım" iddiasının çıtası

Hedefimiz N nesil; bugün elimizde ata→varis (iki nesil) var.

- Tek adımlık aktarım ile **birikimli/kalıtsal** etki iddiası arasındaki
  fark literatürde nasıl konuyor, ve kaç nesil **ölçülmüş** bir çıta olarak
  geçiyor?
- Nesil sayısı arttıkça biriken artefaktlar neler (ör. başlangıç
  koşullarının unutulması, çeşitliliğin tükenmesi), ve bunlar hangi
  teşhislerle izleniyor?

### S6 — Sabit hesap bütçesi altında: daha çok birey mi, daha çok nesil mi

Bizim kısıtımız GPU-saati ve sert. Kaba ölçek: bir olay ≈ 3.3 saniye; 10
birey × 5 nesil × 50 olay × 3 kol × 40 tohum ≈ **270 saat**.

- Sabit değerlendirme bütçesi altında popülasyon büyüklüğü ile nesil sayısı
  arasındaki takas için **ölçülmüş** bir rehber var mı?
- Güç, birey sayısına mı nesil sayısına mı daha duyarlı — ve bu, "olay
  sayısına dayalı güç" mantığıyla nasıl uzlaşıyor?
- Küçük bütçede yaşam **kısaltmak** (ör. 50 → 30 olay) hangi noktada
  ölçtüğümüz şeyi bozar?

---

## 5. Cevabın biçimi

Her iddia için:

1. **Ne söyleniyor** — tek cümle
2. **Kaynak** — yazar, yıl, DOI/arXiv. Emin değilsen **"doğrulanamadı"**
3. **Kanıt türü** — ölçülmüş deney mi, simülasyon mu, teorik öneri mi
4. **Bizim kurulumumuza uyarlanabilirliği** — hangi varsayımı ihlal ediyor

Bir öneri bizim ölçtüğümüz bir sayıyla çelişiyorsa **çelişkiyi göster**; biz
o sayıyı yeniden ölçeriz. Geçmiş turlarda en değerli çıktı, bizim
varsayımımızı çürüten satır oldu.

⚠ **Bir öneri §1.1'deki kısıtlardan birini ihlal ediyorsa** (trait
enjeksiyonu, davranışsal önsel, LLM-yargıç, duvar saati) yine de yaz — ama
**hangi kısıtı ihlal ettiğini işaretle**. Kısıtı gevşetmenin bedelini
bilmek, öneriyi hiç görmemekten iyidir.

---

## 6. Bu brief'in bilerek dışarıda bıraktıkları

- **Davranış çöküşünü çözmek.** Tek ölçülmüş kaldıraç aksiyom gereği kapalı;
  §2.2'de sınır olarak duruyor.
- **Uç nokta tanımı ve sansürleme.** Önceki brief'in (#5) konusu; sabit yaşta
  kesit + olay-başına oran kararı **verildi** ve uygulandı.
- **Öğrenme oranı, DPO ayarları, model seçimi, quantization.** Ölçüldü,
  donduruldu.
- **"Hangi tasarım daha büyük fark verir."** Bilerek sorulmuyor — §0.
- **Bizim karar geçmişimiz.** Erişimin yok.
