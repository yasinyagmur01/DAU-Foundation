# DR brief #3 — tek soylu Lamarckçı tasarımın iddia sınırı, ve kanal ayrımı

**Öncelik: 3 / 3** — kilidi bloke etmiyor. İddianın **ne kadar geniş
yazılabileceğini** ve bir sonraki ön-kaydın mimarisini belirliyor.

**Durum:** gönderilmedi · brief #1 ve #2'yi beklemez

⚠ Bu brief'in S4 (en küçük anlamlı etki) soruları **brief #1'e taşındı** —
orası öncelik 1 ve kilidi o tutuyor.

---

## Deneyin dürüst tarifi

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit, ajan başına LoRA. Olay başına
  bir karar; LLM yalnız bilişsel yük eşiği aşılınca çağrılıyor (altında
  deterministik durum makinesi).
- **Yaşam:** 50 olay. Ortak kaynak havuzu, kıtlık/kriz, anı kasası
  (Ebbinghaus + PageRank benzeri getirim), MiniLM ile ölçülen anlamsal
  tahmin hatası.
- **Eğitim:** faz sonunda, ajanın **kendi** olaylarından türetilen çiftlerle
  DPO. Tercih yönü: düşük tahmin hatası. İnsan etiketçi yok, yargıç yok.
- **Nesil:** ata **bir** varis üretiyor. Varis anıları ve drift durumunu
  miras alıyor, **ebeveynin adapter'ını almıyor**.
- **Tekrarlanabilirlik:** aynı seed + kod bit düzeyinde aynı (ölçüldü).

**İlan edilmiş sınırlar:** popülasyon yok · **farklı üreme yok** — her ata
tam olarak bir varis bırakıyor, iyi de yaşasa kötü de ⇒ aktarım
**Lamarckçı**, Darwinci değil · iki nesil · uygunluk skoru (`F_agent`)
dejenere, seçilim katmanı atıl.

---

## Sorular

### 1. Tek soylu Lamarckçı düzenek neyi kurabilir

- *"Çevresel baskı organizmayı şekillendirir"* iddiasını **ne kadar**
  destekleyebilir? Hangi **daha dar** iddiayı meşru kılar?
- Bu iddiayı gerçekten kurmak için literatürdeki **minimum mimari** nedir —
  kaç birey, kaç nesil, hangi seçilim baskısı? Yapay yaşam / evrimsel
  hesaplamanın yerleşik düzenekleri (Avida, Tierra, Lenski'nin uzun-vadeli
  deneyi) ne gerektirmiş?
- Tek soylu, kazanılmış-özellik-aktarımlı düzeneklerin literatürde karşılığı
  var mı, ve ne iddia etmişler?
- ⚠ Bizim kullandığımız *"ontogenetik uyarlanma"* çerçevesi doğru mu?

### 2. İçsel amaçlı ince ayar — sürprizi hedef yapmak

Eğitim sinyali dışarıdan değil ajanın **kendi ölçülen sonucundan** geliyor,
ama **amaç fonksiyonunu biz seçtik**: düşük tahmin hatası tercih edilir.
Serbest enerji ilkesi bu seçimi savunuyor gibi görünüyor.

- Bu savunma literatürde ne kadar sağlam? Sürprizi vekil hedef yapmanın
  bilinen başarısızlık kipleri neler?
- ⚠ Bizde bir tanesi **gözlendi**: `lr=5e-5`'te ajan *"düşük PE'liyi tercih
  et"* değil *"yüksek PE'liyi asla söyleme"* öğreniyordu — bir tercih değil
  **bastırma deseni**. lr'yi 1e-6'ya çektik. Bu bilinen bir kip mi, adı var
  mı, ve **öğrenilenin tercih mi bastırma mı olduğunu ayıran bir ölçüm** var
  mı?
- Sürpriz minimizasyonu, ajanı sıkıcılaşmaya / tekrar etmeye iter mi?
  Literatürde bunun karşı-önlemi ne?

### 3. Kanal ayrımı — bu projenin kendi sorusu

Aktarım iki kanaldan olabiliyor: **sembolik anı kasası** ve **ağırlıklar**.
Bir varis değiştiğinde hangisinin taşıdığını ayırmak istiyoruz.

Bizim gördüğümüz öneri: yaşantıdan sonra anı getirimini **tamamen kapat**,
yalnız ağırlıklara yansıyanı ölç (*OOD behavioral probing*).

- Bu yaygın ve kabul gören bir yöntem mi? Adı, kaynağı?
- Sınırları neler — getirimi kapatmak ajanı dağılım dışına atıp ölçümü
  bozmaz mı?
- Alternatif kanal-ayrım yöntemleri var mı?
- Bu tipte bir ayrım iddiası için **ne kadar** kanıt yeterli sayılıyor?

### 4. Uç nokta seçimi — yörünge mi düzey mi

Ölçtük: adapter, ajanın **neye şaşırdığını** yeniden düzenliyor ama ortalama
şaşkınlık düzeyini kaydırmıyor. Faz ortalaması ayrımın %80–86'sını iptal
ediyor (iptal simetrik, işaretlerin %44–64'ü pozitif).

Aynı ölçüm ikinci nesilde de yapıldı: orada da ayrımın **%73'ü** iptal
oluyor, ama iptal **simetrik değil** — bağımsız altı karşıtlığın beşinde
yaşamın ikinci yarısı daha pozitif, ve kaynak eğitim görmemiş kontrol
kolunun ikinci yarıda çöken tahmin hatası. ⚠ N=3, gözlem düzeyinde.

- Bir müdahalenin etkisi zamanla **yön değiştiriyorsa**, tek sayılı bir uç
  nokta yerine ne kullanılır? (Fonksiyonel veri analizi, karışık etkiler
  modelinde zaman × kol etkileşimi, başka bir şey?)

- Bu tipte bir müdahaleyi ölçmek için **yörünge tabanlı** uç noktalar
  literatürde nasıl kuruluyor? (Dizi mesafeleri, değişim noktası, dağılım
  karşılaştırması?)
- ⚠ Bunu **bu koşumdan sonra** düşündük, yani mevcut ön-kayıta alamayız —
  post-hoc olur. Bir sonraki ön-kayıt için hangi uç nokta **önceden**
  gerekçelendirilebilir?

---

## Beklenen çıktı

Her soru için **kaynaklı** cevap (yazar, yıl, yer). ⚠ Kaynak kimlikleri
kontrol edilecek — önceki bir brief'te `arXiv:2506.08965` kimlik/yıl olarak
çelişkili çıktı ve o madde kullanılmadı.

Provenans sorusu **sorulmuyor** — DR'nin commit geçmişimize erişimi yok ve
makul görünen ama kaynaksız metin üretir (D-007).

Geldiğinde: `RECONCILIATION.md`'ye mutabakat bölümü. Sorular 1–2 iddianın
genişliğini, 3–4 bir sonraki ön-kaydın mimarisini belirleyecek.
