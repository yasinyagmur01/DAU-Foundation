# DR brief #2 — GAP-18: tercih öğrenmesinde ortak negatif / az çeşitli `rejected`

**Öncelik: 2 / 3** — kilidi bloke etmiyor ama eğitim setinin kalitesini
belirliyor, ve bir sonraki alet kararını bu cevap yönlendirecek.

**Durum:** gönderilmedi · **GAP-18** · brief #1'i beklemez

---

## Durum

DPO çiftlerimizi ajanın kendi yaşadığı olaylardan kuruyoruz. Her olay için
üretilen completion'lar tahmin hatasına (PE) göre sıralanıyor; `chosen` düşük
PE'li, `rejected` yüksek PE'li.

**Yapısal sonuç:** `best_by_event` sabit bir `chosen` için **en büyük marjı**
seçtiğinden, yaşamın **global maksimum-PE completion'ı** çiftlerin çoğunda
reddedilen taraf oluyor.

Ölçülen: 47 çiftlik bir eğitim setinde **47 farklı prompt**, ama yalnız
**2 benzersiz `rejected` metni**.

## ⚠ Bunu kapatmaya iki kez kalkıştık, ikisi de ters tepti

Bu kısmı okumadan çözüm önerme — önerilerin çoğu bu iki duvara çarpıyor.

**1. `rejected`'ı tekilleştiren ayrık eşleştirme.** Her negatifi bir kez
kullanmaya zorladık: **9 çift 2'ye düştü.** Eğitim seti yok oldu.

**2. Aynı metnin farklı çiftlerde farklı rol alması.** Ayrık eşleştirme buna
da yol açıyor: bir metin bir çiftte `chosen`, başkasında `rejected` oluyor.
Sebep yapısal — **PE `(durum, eylem)` çiftinin fonksiyonu, ama tercih çifti
yalnızca metnin.** Aynı cümle bir durumda az, başka durumda çok sürpriz
üretiyor. Sonuç: modele **çelişik denetim**.

---

## Sorular

### 1. Ortak negatif yapısı literatürde ne kadar normal

Çok sayıda farklı prompt'un **az sayıda ortak negatifi paylaştığı** bir
tercih veri seti:

- Bu yerleşik bir yapı mı (hard negative mining, contrastive learning'deki
  paylaşılan negatifler), yoksa patoloji mi?
- Hangi koşullarda öğrenmeyi bozar? Model *"şu iki cümleyi asla söyleme"*
  öğrenip genelleme yapmayı bırakır mı?
- Bunun teşhisi için **ölçülebilir bir gösterge** var mı — yani "negatif
  çeşitliliği yeterli mi" sorusunun kabul görmüş bir metriği?

### 2. Bizim özel çelişkimiz: bağlama bağlı tercih, bağlamsız çift

Tercih sinyalimiz `(durum, eylem)`'in fonksiyonu ama DPO çifti yalnızca metin
taşıyor. Aynı metin farklı durumlarda farklı yönde tercih edilebiliyor.

- Bu bilinen bir problem mi, adı var mı?
- Bağlam-koşullu tercihi DPO'ya sokmanın yolları neler? (Prompt'a durum
  gömmek bizde zaten yapılıyor — `chosen` olayının **gerçek** prompt'u
  kullanılıyor. Bu yeterli mi, yoksa ek bir şey mi gerekiyor?)
- Çelişik denetim (aynı metin iki yönde) modeli **ne kadar** bozar, ve bunu
  önceden saptamanın yolu var mı?

### 3. Az veriyle DPO

Elimizde yaşam başına **38–47 çift** var, ve bu sayı yaşamın kendisiyle
sınırlı — sentetik olarak artıramayız, çünkü aksiyom gereği çiftler
**yaşanmış** olmak zorunda.

- Bu ölçekte DPO ne kadar güvenilir? Bilinen alt sınır var mı?
- Az veri rejiminde `rejected` çeşitliliği mi yoksa çift sayısı mı daha
  belirleyici?
- Ezberleme riski: 40 çift üzerinde kaç epoch güvenli? (Biz 1 epoch'ta karar
  kıldık, lr=1e-6.)

### 4. Alternatif çift kurma stratejileri

`best_by_event` yerine ne kullanılabilir — ve her birinin **bizim
kısıtımızda** maliyeti ne:

- Olay başına birden çok çift (marj eşiğinin üstündeki her ikili)
- Marj bandı (çok büyük marjları da eleme — kolay negatifler bilgi taşımaz)
- Negatif başına kullanım tavanı
- Başka bir şey

⚠ Kısıtımız: **çiftler yaşanmış olaylardan gelmek zorunda**, sentetik
completion üretilemez, ve bir yaşam 50 olay.

---

## Bağlam

Tercih yönü: **düşük PE tercih edilir**. Polarite kapısı: MiniLM kosinüs
mesafe, bant `[0.25, 0.80]` — ⚠ **kalibre değil**, bir brief'ten geldi.
Ayrıca bir SNR marj tabanı var (`0.15`), o da **kalibre değil**.
DPO: β=0.1, lr=1e-6, 1 epoch, batch=1, grad_accum=4, max_seq=512.

**Kontrol kolumuz** `shuffle`: aynı çiftler, tercih yönü **tamamen** ters.
Yani "eğitimin içeriği mi önemli, yoksa sadece DPO yapmış olmak mı" sorusunu
bu kol cevaplıyor.

⚠ Her iddia yazar + yıl + yer ile gelmeli; kaynak kimlikleri kontrol
edilecek.
