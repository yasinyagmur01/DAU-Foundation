# DR brief #5 — yaşam uzunluğu değişkenken uç nokta nasıl tanımlanır

**Öncelik: 1** — ikinci ön-kaydın uç noktası bu cevaba bağlı. Yanlış seçersek
koşumdan sonra düzeltmek **post-hoc** olur ve ön-kayıt geçersizleşir.

**Durum:** gönderilmedi · **Tarih:** 2026-08-13

---

## 0. Bu brief'i okuyan için: neye ihtiyacımız var, neye yok

**İhtiyacımız olan:** gözlem penceresinin kendisi bir **sonuç** olduğunda —
yani denek ne kadar yaşayacağı davranışına bağlı olarak değiştiğinde — uç
noktanın nasıl tanımlandığına dair **yerleşik yöntem bilgisi**: adları,
tuzakları, teşhis ölçütleri.

**İhtiyacımız olmayan:**

- **Bizim proje geçmişimiz.** Erişimin yok; makul görünen ama kaynaksız bir
  anlatı bize zarar verir.
- ⚠ **"Hangi uç nokta size daha büyük fark verir" sorusunun cevabı.** Bunu
  bilerek sormuyoruz. Etkiyi görüp uç nokta seçmek post-hoc olur ve bütün
  ön-kaydı geçersiz kılar. **Çözünürlük ve geçerlilik** ölçütleri istiyoruz,
  etki büyüklüğü değil.
- **LLM/prompt tarafı.** Onu ayrı bir turda kapattık; bu brief saf ölçüm
  metodolojisi.

⚠ **Kaynak kimliği kritik ve sicilimiz kötü.** Önceki dört brief'te **yedi**
kaynak yanlış atfedildi. Son turda bir DOI (`10.1007/s00778-019-00574-9`) bir
hareket-ekolojisi makalesine atfedilmişti; o DOI aslında bir VLDB Journal
derlemesine ait. Bir başka iddia yazar/yıl yerine bir dergi **ISSN**'iyle
"kaynaklandırılmıştı".

**Her iddia için yazar + yıl + kalıcı kimlik (DOI/arXiv) ver. Emin değilsen
"doğrulanamadı" yaz — biz her kimliği Crossref/arXiv üzerinden tek tek
doğruluyoruz ve doğrulanmayanı kullanmıyoruz.** Uydurulmuş bir referans,
cevapsız bir sorudan **daha** pahalı.

---

## 1. Sistemin dürüst tarifi — özellikle uç noktanın ne OLMADIĞI

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit, ajan başına LoRA adapter.
  Olay başına bir karar.
- **Yaşam:** olay sıralı, duvar saati yok. Ortak kaynak havuzu (lojistik
  yenilenme), anı kasası (Ebbinghaus unutması), MiniLM ile ölçülen anlamsal
  tahmin hatası (PE).
- **Nesil:** ata **bir** varis üretiyor. Varis anıları ve drift durumunu miras
  alıyor; **ebeveynin adapter'ını almıyor.**

⚠ **Birincil uç noktamız bir AĞIRLIK VEKTÖRÜ DEĞİLDİR.** Geçen tur bu
yanlış anlaşıldı ve cevabın yarısı optimizer gürültüsü üzerine kuruldu.
Doğrusu: uç nokta, **varisin doğum anındaki drift durumunun büyüklük
vektörü** — üç alan (`resource`, `social`, `uncertainty`) üzerinde tanımlı,
ajanın yaşadıklarından türeyen bir **durum** ölçüsü. Varis daha tek bir olay
yaşamadan, ve ebeveynin ağırlıkları hiç aktarılmadan alınıyor. Model
parametrelerine bakan bir ölçü değildir.

**Kontrol kolu:** aynı tercih çiftleri, tercih yönü %100 ters (`shuffle`).
Yani *"eğitim oldu mu"* değil, *"eğitimin içeriği yaşama özgü mü"* soruluyor.

---

## 2. Ne değişti: yaşam uzunluğu artık sabit değil

Önceki tasarımda her yaşam **tam 50 olay** sürüyordu; ölüm yapısal olarak
imkânsızdı ve hayatta kalma terimi 120 kolun 120'sinde 1.0 okuyordu.

Bunu bilerek değiştirdik: hasat artık enerjiye dönüyor (içbükey/doygun kazanç
eğrisi), boş havuz hiçbir şey vermiyor, ve enerji tükenince yaşam **biter**.

**Sonuç (N=2 pilot, keşifsel):** yaşamlar 50 olaylık bütçeye karşı **19** ve
**10** olayda bitti. Ve ölüm zamanı **davranışın sonucudur**: ajan havuzu
çökertiyor, çökmüş havuz besin vermiyor, ajan ölüyor.

### 2.1 Ölçüm aletimiz bunun altında kırıldı

| Ölçüm | Değer |
|---|---|
| Faz-1 PE dizisinde **doldurma (padding)** oranı | **426/600 = %71** |
| Faz-2/gen2 doldurma oranı | 30/120 = %25 |
| PE olayı kapsaması (gen1) | 174/600 = **0.29** |

Uç nokta, sabit 50 slotluk bir diziyi **son değerle doldurup ortalamasını**
alıyor. Yaşamların %60-80'i boşken bu ortalama artık büyük ölçüde doldurmayı
ölçüyor. Aletimiz bunu kendi başına raporladı: *"arm not measurable."*

### 2.2 Ve bir durum değişkeni ölümün seçtiği anda okunuyor

Uygunluk skorumuz üç girdiyi ağırlıklandırıyor:
`F = 0.4·(enerji) + 0.3·(1 − |Δhavuz|/P_max) + 0.3·(hayatta kalma)`

Enerji, **yaşamın son anında** okunuyor. Ama ajanlar **tükenerek** ölüyor ⇒
son enerji tanımı gereği sıfır ⇒ pilotta altı kolun altısında `E_final =
0.000`. **En büyük ağırlıklı terim, ölüm kuralının kendisi yüzünden hiçbir
bilgi taşımıyor.** (Diğer iki terim canlandı: hayatta kalma 19 vs 10 olay,
`|Δhavuz|` 130.8 vs 62.2 — önceki tasarımda bu ikincisi %0.7 yayılıyordu.)

### 2.3 Ayrım kollara da ulaştı

Aynı pilotta bir varis gen2'de **17 olay**, diğer iki kolun varisleri **20**
olay yaşadı. Yani yaşam uzunluğu artık kola göre değişebiliyor — bu, önceki
tasarımda **var olmayan** bir kanal. Ama tam da bu yüzden kolları
karşılaştıran her ölçü, farklı uzunluktaki dizileri karşılaştırmak zorunda.

---

## 3. Asıl soru

**Gözlem penceresinin uzunluğu deneğin davranışının sonucuysa, uç nokta nasıl
tanımlanır ki hem ölçülebilir kalsın hem de "erken ölen az veri üretir"
artefaktını sonuca karıştırmasın?**

---

## 4. Cevaplanmasını istediğimiz sorular

### S1 — Bilgilendirici sansürleme: adı, teşhisi, standart çözümü

Gözlem penceresi rastgele değil, deneğin kendi davranışıyla belirleniyor.
- Bu durum literatürde nasıl adlandırılıyor (informative / dependent
  censoring? competing risks?) ve **hangi teşhis ölçütleriyle** saptanıyor?
- Sabit uzunluklu bir pencereyi son gözlemle doldurup ortalamak (bizim
  yaptığımız) hangi yanlılığı üretir, ve bu işlemin literatürdeki adı var mı
  (LOCF benzeri bir şey)?
- **Ölçülmüş** alternatifler neler: olay-başına oran (rate), ölüme kadarki
  eğri altı alan (AUC), sabit yaşta kesit (landmark), yoksa doğrudan
  zaman-olay (time-to-event) uç noktası mı?

### S2 — Sabit yaşta kesit (landmark) mi, yaşam boyu özet mi

İki aday var ve tercihin sonuçlarını bilmiyoruz:
- **Landmark:** herkesin hayatta olduğu sabit bir yaşta ölç (bizde ör. 10.
  olay). Karşılaştırılabilirlik kazanır, geç yaşamı atar.
- **Yaşam boyu özet:** yaşadığı kadarı üzerinden normalize et. Bilgiyi tutar,
  ama farklı uzunluktaki dizileri karşılaştırır.

Hangi koşullarda hangisi **savunulabilir** sayılıyor, ve landmark noktasının
seçimi için bir ilke var mı? (Bizde ilk 10 olay ayrıca bir "doğum geçişi"
penceresi — enerji tam dolu, yükler sıfır — yani orası da temsili değil.)

### S3 — Ölümün belirlediği bir durum değişkeni nasıl ölçülür

`E_final = 0` sorunu: tükenme yoluyla ölen her denek için terminal değer
sabittir. Kondisyon/rezerv benzeri değişkenleri ölüm altında ölçmek için
literatürde ne kullanılıyor — zaman-integre kondisyon, sabit yaştaki değer,
ortak (joint) modelleme? **Ölçülmüş** karşılaştırma var mı?

### S4 — Hayatta kalma hem uygunluğun bileşeni hem sonucuyken

Uygunluk skorumuzun %30'u hayatta kalma. Ölüm mümkün hale gelince hayatta
kalma hem **girdi** hem **sonuç** oldu.
- Evrimsel/yapay yaşam literatüründe uygunluk ile ömür arasındaki bu
  çift-sayım riski nasıl ele alınıyor?
- Ömrün kendisini uygunluk vekili yapmak (yaygın çözüm) hangi varsayımları
  gerektiriyor, ve hangi durumlarda **yanıltıcı** olduğu ölçülmüş?

### S5 — Farklı uzunluklu dizilerde kol karşılaştırması

Tasarımımız eşleştirilmiş: her tohum için üç kol (`lived`, `null`, `shuffle`)
aynı başlangıç koşullarından koşuyor, ve `null` çapa olarak kullanılıp iki
mesafe karşılaştırılıyor (eşleştirilmiş Wilcoxon).
- Kollardan biri sistematik olarak daha erken ölüyorsa bu eşleştirme ne
  zaman geçersizleşir?
- Eşit olmayan gözlem desteği altında eşleştirilmiş karşılaştırma için
  **kabul gören** yaklaşımlar neler?

### S6 — Küçük N'de zaman-olay uç noktası için güç

Bizim ölçeğimiz küçük (onlarca tohum, yüzlerce olay değil binlerce değil).
- Zaman-olay uç noktalarında güç, olay **sayısına** mı dayanır denek
  sayısına mı, ve bu bizim gibi her deneğin kesin olarak öldüğü (sansürsüz)
  bir tasarımda nasıl değişir?
- Simülasyon çalışmalarında örneklem büyüklüğü gerekçelendirmesi için
  **kullanılan** standart var mı?

---

## 5. Cevabın biçimi

Her iddia için:
1. **Ne söyleniyor** — tek cümle
2. **Kaynak** — yazar, yıl, DOI/arXiv. Emin değilsen **"doğrulanamadı"**
3. **Kanıt türü** — ölçülmüş deney mi, simülasyon mu, teorik öneri mi
4. **Bizim kurulumumuza uyarlanabilirliği** — hangi varsayımı ihlal ediyor

Bir öneri bizim ölçtüğümüz bir sayıyla çelişiyorsa **çelişkiyi göster**; biz o
sayıyı yeniden ölçeriz. Geçmiş turlarda en değerli çıktı, bizim varsayımımızı
çürüten satır oldu.

---

## 6. Bu brief'in bilerek dışarıda bıraktıkları

- **Prompt / davranış müdahalesi.** Geçen turda kapandı (GovSim ve persona
  manifold çöküşü); kalanı bizim tasarım kararımız.
- **Öğrenme oranı, DPO ayarları, model seçimi, quantization.** Ölçüldü,
  donduruldu.
- **"Hangi uç nokta daha büyük fark verir."** Bilerek sorulmuyor — §0.
- **Bizim karar geçmişimiz.** Erişimin yok.
