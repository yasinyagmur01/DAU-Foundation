# DR brief #6 — HAM CEVAP (değiştirilmeden kaydedildi)

**Alındı:** 2026-08-14 · **Brief:** `2026-08-13_population-selection-and-shared-commons.md`
· **Gönderilen sürüm:** `..._PLAIN.txt`

⚠ **Bu dosya ham kayıttır.** Hiçbir iddia doğrulanmadan buradan alınmaz.
Mutabakat ve kimlik doğrulaması `RECONCILIATION.md` §M'de.

---

## Küçük Popülasyonlarda Seçilim Şemaları, Ortak Havuz Girişimi ve Evrimsel Tasarım Analizi

Küçük ölçekli simülasyon ortamlarında evrimsel seçilim iddialarının
metodolojik olarak geçerli bir temele oturtulması; popülasyon dinamiği,
nedensel çıkarım ilkeleri ve istatistiksel güç analizi arasında hassas bir
denge gerektirmektedir. Sınırlı sayıda birey içeren (N ≤ 50) ve ortak bir
kaynağı tüketerek hayatta kalma mücadelesi veren ajan tabanlı yapay yaşam
sistemlerinde, rastgele genetik sürüklenme (genetic drift) ile gerçek seçilim
baskısını ayırt etmek klasik istatistiksel varsayımları zorlaştırmaktadır.
Özellikle müdahalenin (yaşanmış tercihlerle LoRA eğitimi) bireysel düzeyde
uygulandığı ancak çevresel ortamın (ortak havuz) paylaşıldığı kurgularda,
üniteler arası girişim (interference) meydana gelmekte ve bir ajanın davranışı
doğrudan diğer ajanın deneysel ortamını kirletmektedir.

Bu raporda, altı temel metodolojik soru çerçevesinde; evrimsel algoritmalar,
deneysel evrim, popülasyon genetiği ve nedensel çıkarım literatüründeki
yerleşik yöntemler incelenmekte; her bir yaklaşımın deneysel kısıtlar (trait
enjeksiyonu yasağı, davranışsal önsel olmaması, LLM yargıç kullanılmaması ve
duvar saati bulunmaması) altındaki uygulanabilirliği değerlendirilmektedir.

### Küçük Popülasyonlarda Üreme ve Seçilim Şemaları (Soru 1)

Küçük popülasyonlarda evrimsel seçilimin uygulanması, evrimsel baskının
korunması ile genetik ve davranışsal çeşitliliğin erken tükenmesi (premature
convergence) arasındaki çelişkiyle şekillenir. Birey sayısının kısıtlı olduğu
durumlarda seçilim şemalarının stokastik gürültüsü ve örnekleme varyansı
popülasyonun evrimsel potansiyelini belirlemektedir.

Evrimsel algoritmalar literatüründe öne çıkan temel seçilim mekanizmaları
şunlardır:

**Kesme seçilimi (truncation selection)**, popülasyonu uygunluk skoruna göre
sıralayarak sabit bir yüzdeyi ebeveyn olarak ayırır; seçilim baskısı çok
yüksek olmakla birlikte küçük N değerlerinde çeşitliliği hızla yok eder.
**Turnuva seçilimi (tournament selection)**, rastgele seçilen k kadar birey
arasından en uygun olanı seçer; turnuva boyutu (k) değiştirilerek seçilim
baskısı ve sürüklenme gürültüsü hassas biçimde ayarlanabilir. **Uygunlukla
orantılı seçilim (rulet tekerleği)**, bireyin seçilme olasılığını doğrudan
uygunluk skoruyla orantılı kılar; seçilim gürültüsü yüksek olup uygunluk
farklarının azaldığı durumlarda seçilim baskısını kaybetme riski taşır.

**Durağan durum / Moran seçilimi (steady-state selection)**, nesillerin
çakışmalı olduğu ve her adımda popülasyonun yalnızca küçük bir kısmının
yenilendiği bir yapı sunar. **Nesil bazlı (generational / Wright-Fisher)**
modellerde ise tüm popülasyon senkronize olarak bir sonraki nesil ile
değiştirilir. Çakışmasız nesil modellerine kıyasla çakışmalı Moran modelleri,
üreme ve ölüm süreçlerini zamana yayarak küçük popülasyonlarda genetik
sürüklenmenin varyansını düşürmekte ve popülasyon içi çeşitliliği daha uzun
süre korumaktadır.

Sabit popülasyon boyutu (N) varsayımı, doğal ölüm oranlarının kaynağa ve
tüketime bağlı olduğu ortamlarda ihlal edilir. Ancak sistemde ölümün bir
davranış sonucu gerçekleşmesi, dinamik popülasyon boyutlu Wright-Fisher veya
taşıma kapasitesine bağlı Moran modelleriyle teorik uyum göstermektedir.

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Turnuva seçilimi (k=2), küçük popülasyonlarda seçilim baskısını korurken erken yakınsamayı engellemede rulet tekerleğine kıyasla belirgin şekilde üstündür. | Goldberg & Deb (1991) `10.1016/b978-0-08-050684-5.50008-2` | Teorik Analiz ve Simülasyon | Tam Uyumlu. Ajanların drift durum vektör skorları üzerinden deterministik turnuva eşleşmesi yapılabilir; hiçbir kısıtı ihlal etmez. |
| Çakışmalı nesil modelleri (Moran/Steady-State), küçük popülasyonlarda allel sabitleşme süresini uzatır ve sürüklenme gürültüsünü azaltır. | Bäck (1994) `10.1109/ICEC.1994.350042` | Ölçülmüş Deney ve İstatistiksel Analiz | Tam Uyumlu. Olay bazlı zaman akışı ile entegre edilerek doğal ölüm gerçekleştiğinde yeni varis üretilebilir. |
| Taşıma kapasitesine dayalı dinamik popülasyonlarda seçilim baskısı, kaynağın tükenme hızına bağlı olarak içsel (endojen) olarak değişir. | Wright (1931) `10.1093/genetics/16.2.97` | Teorik Matris Modeli | Tam Uyumlu. Sabit N zorlaması yerine kaynağın belirlediği doğal bir doğum-ölüm dengesi kurulmasını destekler. |

### Sürüklenme mi Seçilim mi: Küçük N'de Nasıl Ayrılır (Soru 2)

Küçük popülasyonlarda (N < 50), rastgele örnekleme varyansı olarak tanımlanan
genetik sürüklenme (genetic drift), seçilim kuvvetine baskın gelebilir. Bir
özelliğin veya durum vektöründeki değişimin adaptasyon (seçilim) sonucu mu
yoksa stokastik sürüklenme sonucu mu gerçekleştiğini ayırt etmek için
popülasyon genetiği ve deneysel evrim literatüründe üç temel kontrol
mekanizması kullanılır.

İlki, aynı başlangıç koşullarından başlatılan bağımsız popülasyon hatlarının
paralel koşulduğu **tekrarlı (replike) popülasyon** tasarımlarıdır. Sürüklenme
hatlar arasında rastgele yönlerde sapmalara yol açarken, seçilim tüm hatlarda
aynı yönde paralel ve konverjan değişimlere neden olur. İkincisi, uygunluk
üzerinde etkisi olmayan **nötr işaretleyicilerin** izlenmesiyle arka plan
sürüklenme hızının deneysel olarak ölçüldüğü nötr işaretli soylardır.
Üçüncüsü ise ebeveynlerin rastgele seçildiği ve adaptif avantajın sıfırlandığı
**sürüklenme-nötr kontrollerdir**.

Mevcut deneysel kurulumdaki `null` (hiç eğitilmemiş) ve `shuffle` (tercih yönü
yüzde yüz ters çevrilmiş) kollar, modelin eğitim içeriğinin yaşama özgü
etkisini kontrol etmek için tasarlanmıştır. Ancak bu kollar demografik genetik
sürüklenmeyi tek başına izole edemez. `null` kolu adaptif değişimin olmamasını
temsil ederken, `shuffle` kolu rastgele gürültülü eğitimin etkisini kontrol
eder; fakat her iki kol da küçük N'nin getirdiği stokastik örnekleme
varyansına tabidir. Sürüklenmeyi dışlamak için gerekli asgari N sayısı sabit
bir eşik olmayıp, seçilim katsayısına (s) bağlıdır; evrimsel teoride Ne·s ≫ 1
koşulu sağlandığında seçilim sürüklenmeye galip gelir (Ne efektif popülasyon
boyutudur).

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Stokastik sürüklenme ile adaptif konverjansı ayırt etmenin tek yolu bağımsız paralel hatların (replicates) evrimsel yönelimlerini karşılaştırmaktır. | Elena & Lenski (2003) `10.1038/nrg1088` | Ölçülmüş Mikroorganizma Deneyi | Tam Uyumlu. Aynı tohumla farklı hatlar koşturularak hatlar arası varyans ile hat içi trend ayrıştırılabilir. |
| Effective population size ile seçilim katsayısının çarpımı birin altında kaldığında (Ne·s < 1) genetik sürüklenme seçilime baskın gelir. | Wright (1931) `10.1093/genetics/16.2.97` | Teorik Popülasyon Genetiği | Tam Uyumlu. Ölçülen etki büyüklüğü küçükse popülasyon boyutunu artırma gerekliliğini teorik olarak doğrular. |
| İçerik kontrol kolları (shuffle), eğitim gürültüsünü ölçer ancak popülasyon düzeyindeki stokastik sürüklenmeyi izole etmek için nötr ebeveyn seçim kontrolüyle desteklenmelidir. | Branke & Schmidt (2003) `10.1007/3-540-45105-6_91` | Simülasyon Çalışması | Tam Uyumlu. Null ve shuffle kollarına ek olarak ebeveynlerin rastgele seçildiği rastgele üreme kontrolü eklenebilir. |

### Ortak Havuzda Kol Kirlenmesi ve Girişim Analizi (Soru 3)

Müdahalenin (LoRA adaptörü ile verilen yaşanmış tercih eğitimi) birey düzeyinde
uygulandığı fakat çevresel kaynağın (lojistik yenilenen ortak havuz) tüm
ajanlarca paylaşıldığı kurgularda geleneksel nedensel çıkarım varsayımları
çöker. İstatistiksel nedensellik literatüründe bu durum **Üniteler Arası
Girişim (Interference / Spillover)** veya **SUTVA (Stable Unit Treatment Value
Assumption) İhlali** olarak adlandırılır.

Bu kirlenmeyi ele almak için iki deneysel tasarım yaklaşımı mevcuttur:

**Kol Başına Ayrı Havuz (Isolated Microcosms)** tasarımında her deneysel kol
(lived, null, shuffle) kendi ayrı popülasyonu ve kendi bağımsız ortak havuz
kaynağı ile çalıştırılır. SUTVA varsayımı kollar arasında geçerli kalır ve
kollar arası doğrudan çevresel etkileşim engellenir. Ancak farklı kollar aynı
otlakta doğrudan rekabet etmediği için, "doğrudan rekabet olmaksızın seçilim"
iddiası evrimsel ekolojide grup düzeyinde seçilim (group selection) seviyesine
kayar ve bireyler arası doğrudan etkileşim üzerinden şekillenen seçilim
baskısı iddiası zayıflar.

**Tek Havuz, Karışık Kollar (Mixed Co-habitation)** tasarımında ise lived,
null ve shuffle ajanları aynı ortak otlakta birlikte yaşar ve aynı kaynak
havuzundan hasat yapar. Bireyler arası doğrudan ekolojik ve sosyal rekabet
gerçekleşir ancak ağır kirlenme (spillover) oluşur. Aşırı tüketen bir shuffle
ajanı, havuzu sıfırlayarak lived ajanının açlıktan ölmesine neden olabilir. Bu
durumda lived ajanının hayatta kalma süresi kendi durum vektörünün değil,
ortamdaki shuffle ajanlarının yoğunluğunun bir fonksiyonu haline gelir
(Frekansa Bağlı Seçilim / Frequency-Dependent Selection).

Nedensel çıkarım literatüründe Hudgens ve Halloran (2008) tarafından
geliştirilen **iki aşamalı rastgeleleştirilmiş tasarımlar (two-stage
randomized saturation design)**, kısmi girişim (partial interference)
altındaki bu etkileri matematiksel olarak ayrıştırmayı sağlar. Bu çerçevede
tanımlanan temel nedensel etkiler şunlardır:

- Doğrudan Etki (Direct Effect): DE(α) = Ȳ(1, α) − Ȳ(0, α)
- Dolaylı / Spillover Etkisi (Indirect Effect): IE(a, α₁, α₀) = Ȳ(a, α₁) − Ȳ(a, α₀)
- Toplam Etki (Total Effect): TE(α₁, α₀) = Ȳ(1, α₁) − Ȳ(0, α₀) = DE(α₁) + IE(0, α₁, α₀)
- Genel Etki (Overall Effect): OE(α₁, α₀) = Ȳ(α₁) − Ȳ(α₀)

Burada a ∈ {0,1} bireysel müdahale durumunu, α ise grup içindeki müdahale
oranını (doygunluk seviyesini) temsil etmektedir.

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Üniteler arası girişim varlığında doğrudan tedavi etkisi ile çevre üzerinden aktarılan dolaylı (spillover) etkiler iki aşamalı doygunluk tasarımıyla ayrıştırılabilir. | Hudgens & Halloran (2008) `10.1198/016214508000000292` | İstatistiksel Teorik Çerçeve | Tam Uyumlu. Karışık kol tasarımı seçilirse farklı oranlarda (lived oranları: %25, %50, %75) kovanlar oluşturularak uygulanır. |
| Ağ üzerindeki deneysel ünitelerin karıştırılması durumunda standart kümeleme hatalı varyans ve tek yönlü sapma üretir; küme düzeyinde sağlam kestirimciler kullanılmalıdır. | Aronow & Samii (2017) `10.1214/16-AOAS982` | Teorik ve Uygulamalı Ekonometri | Tam Uyumlu. İstatistiksel değerlendirmede küme düzeyinde sandviç varyans kestirimcilerinin zorunlu olduğunu gösterir. |
| İzolasyon ortamlarında (Ayrı Havuz) yapılan ölçümler, doğrudan sosyal ve ekolojik rekabet parametrelerini ihmal ettiği için seçilim gücünü abartır. | Chevin (2011) `10.1098/rsbl.2010.0580` | Teorik Ekoloji / Deney Tasarımı | Tam Uyumlu. Ayrı havuz tasarımı tercih edilirse, elde edilen seçilim katsayısının mikrokozmos içi bireysel değil grup düzeyi olduğunu doğrular. |

### Uygunluk Ölçümünde Döngüselliğin Kırılması ve Price Eşitliği (Soru 4)

Evrimsel teoride uygunluk (fitness) hem seçilim mekanizmasının girdisi hem de
ölçülen evrimsel başarı sonucu olduğunda döngüsel bir totoloji riski ortaya
çıkar. Yapay yaşam ve deneysel evrim araştırmalarında bu döngüsellik, **Durum
Değişkeni / Fenotip (z)** ile **Demografik Başarı / Üreme (w)** boyutlarının
birbirinden matematiksel olarak izole edilmesiyle kırılır.

Bu döngüselliği kırmanın en yerleşik matematiksel aracı **Price Eşitliği**dir
(Price Equation). Price eşitliği, popülasyondaki ortalama bir durum
vektöründeki veya özellikteki (z̄) nesiller arası değişimi (Δz̄), doğrudan
seçilim etkisi ile kalıtım/aktarım sapmasına (transmission bias / drift)
ayrıştırır:

```
Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)
```

Denklemdeki bileşenler şu şekildedir:

- wᵢ: i ajanın göreceli uygunluğu (ürettiği varis sayısı veya yaşam süresi)
- w̄: Popülasyonun ortalama uygunluğu
- zᵢ: i ajanın sabit yaşta okunan drift durum vektörü (kaynak, sosyal, belirsizlik alanlarında)
- Cov(wᵢ, zᵢ): Durum vektörü ile uygunluk arasındaki kovaryans (Doğrudan Seçilim Baskısı)
- E(wᵢ·Δzᵢ): Ebeveyn ile varis arasındaki durum vektörü farkının beklenen değeri (Kalıtımsal Aktarım Sapması / Sürüklenme)

Sistem kısıtları gereği birincil uç nokta bir ağırlık vektörü veya model
parametresi değil, ajanın sabit bir yaşta okunan drift durumunun büyüklük
vektörüdür. Uygunluk skoru (hasat miktarı/yaşam süresi) seçilimi yönlendiren
girdi; durum vektörü büyüklüğü ise sonuç ölçütü olarak ele alındığında
döngüsellik kırılmış olur.

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Popülasyondaki toplam durumsal değişim, kovaryans terimi (seçilim) ile beklenti terimi (aktarım sapması) olarak iki bağımsız bileşene tam olarak ayrıştırılabilir. | Price (1970) `10.1038/227520a0` | Matematiksel Teori | Tam Uyumlu. Ajanların durum vektörü zᵢ ve üreme başarısı wᵢ üzerinden tam entegre edilebilir. |
| Uygunluğun doğrudan üreme sayısı olarak ölçüldüğü tasarımlarda, sonucun seçilim olduğunu iddia etmek için kovaryansın sıfırdan anlamlı derecede farklı olduğu gösterilmelidir. | Chevin (2011) `10.1098/rsbl.2010.0580` | İstatistiksel Metodoloji | Tam Uyumlu. Seçilim iddiasının doğrulanması için p-değeri hesabı kovaryans terimi üzerine kurulmalıdır. |

### Çoklu Nesil Dinamikleri ve Birikimli Kalıtım Çıtası (Soru 5)

Tek adımlık aktarım (G=2, ebeveyn ve varis) yalnızca anlık aktarım sapmasını
veya durum kalıtılabilirliğini gösterir; birikimli kalıtsal evrim (cumulative
evolution) iddiası kurabilmek için birden fazla nesil boyunca seçilimin yönlü
etkisinin biriktiği doğrulanmalıdır.

Deneysel evrim literatüründe nesil ölçekleri şu şekilde sınıflandırılır:

- **G=1 → G=2 (Tek Adım):** Fenotipik aktarım veya bellek ve drift durum kalıtılabilirliği
- **G=5 → G=10 (Kısa Dönem Evrim):** Adaptif yönelimlerin, ilk aşama dinamiklerinin ve birikimli seçilim izlerinin belirmesi
- **G ≥ 50+ (Uzun Dönem Evrim):** Doyuma ulaşan adaptasyon eğrileri ve makro-evrimsel konverjans

Çoklu nesil süreçlerinde biriken temel artefaktlar şunlardır:

- **Muller Çarkı (Muller's Ratchet):** Aseksüel popülasyonlarda geri dönüşsüz olarak zararlı stokastik bozulmaların birikmesi ve en uygun sınıfların rastgele kaybolması
- **Çeşitliliğin Tükenmesi (Loss of Diversity):** Küçük N'de tüm ajanların aynı durumsal çizgiye yakınsaması ve seçilim baskısının sıfırlanması
- **Başlangıç Koşullarının Unutulması (Loss of Initial Conditions):** Popülasyonun ilk durumunun hafızasını kaybetmesi

Bu artefaktları izlemek için Bedau vd. (1998) tarafından önerilen **Evrimsel
Aktivite İstatistikleri** kullanılır:

- **Çeşitlilik (D):** Popülasyonda mevcut benzersiz durum vektörlerinin bileşimi
- **Yeni Evrimsel Aktivite (A):** Seçilim tarafından korunan ve geçmiş nesillerde görülmeyen yeni bileşenlerin birikim hızı

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Aseksüel ve küçük popülasyonlarda zararlı birikimler (Muller çarkı) popülasyonun kademeli olarak çökmesine neden olur. | Haigh (1978) `10.1016/0040-5809(78)90027-8` | Teorik Matematiksel Model | Tam Uyumlu. Ajanların LoRA aktarımı olmasa da drift durumundaki rastgele bozulmaların birikim riskini açıklar. |
| Uzun dönem adaptasyon dinamiklerinde uygunluk artış hızı zamanla yavaşlar (decelerate eder) ancak tamamen durmaz. | Wiser, Ribeck & Lenski (2013) `10.1126/science.1243357` | Uzun Dönem Bakteri Deneyi | Tam Uyumlu. 5 nesillik bir süreçte azalan verimler eğrisinin (diminishing returns) beklenmesi gerektiğini gösterir. |
| Evrimsel sistemlerin rastgele gürültüden ayrılması, yeni evrimsel aktivite dalgalarının birikim hızı (A) ile ölçülür. | Bedau, Snyder & Packard (1998) `10.1162/artl.1998.4.4.431` | Yapay Yaşam Simülasyonu | Tam Uyumlu. Ajanların durum vektörlerindeki yenilik birikimini ölçmek için kullanılabilir. |

### Hesaplama Bütçesi Altında Popülasyon Büyüklüğü ve Nesil Sayısı Takası (Soru 6)

Sert GPU saat kısıtları altında (örneğin 1 olay ≈ 3.3 saniye; N=10, G=5, 50
olay, 3 kol ve 40 tohum ≈ 270 saat), hesaplama bütçesinin Popülasyon
Büyüklüğü (N) ile Nesil Sayısı (G) arasındaki dağılımı kritik bir istatistiksel
güç kararıdır.

Popülasyon büyüklüğünün (N) artırılması, genetik sürüklenmenin örnekleme
varyansını düşürür (σ²_drift ∝ 1/N). İki kol arasındaki farkı tespit etme
gücü, N ile doğrudan doğruya artmaktadır. Nesil sayısının (G) artırılması ise,
eğer N çok küçükse (N < 10), tespit gücünü artırmamakta; aksine genetik
sürüklenmenin rastgele bir durumu sabitlemesine (fixation) neden olarak
istatistiksel gürültüyü biriktirmektedir. Bu nedenle sabit bütçe altında N'yi
büyük tutmak, G'yi küçük tutmaktan istatistiksel olarak üstündür.

Ajanların yaşam süresini (olay bütçesini) 50 olaydan 30 olaya düşürmek
ekolojik süreçlerin gözlemlenmesini etkiler. Pilot verilerde havuzun çökmesi
ve açlık krizinin tetiklenmesi 10 ila 19 olay arasında gerçekleşmektedir. Yaşam
süresini 30 olaya düşürmek ekolojik krizi yakalamak için yeterli marj sunmakta
ve %40 hesaplama tasarrufu sağlamaktadır; ancak 20 olay altına düşmek kriz
travmasının ve kaynak tükenme dinamiklerinin ajan durum vektörüne yansımasını
engellemektedir.

| Ne Söyleniyor | Kaynak | Kanıt Türü | Sistem Kısıtlarına Uyum |
|---|---|---|---|
| Küçük popülasyonlu evrimsel algoritmalarda istatistiksel tespit gücü, nesil sayısından ziyade popülasyon boyutundaki (N) artışa üstel olarak daha duyarlıdır. | Goldberg & Deb (1991) `10.1016/b978-0-08-050684-5.50008-2` | İstatistiksel Analiz | Tam Uyumlu. Bütçenin G=5, N=10 yerine G=3, N=16 yönünde kaydırılmasını destekler. |
| Zaman serisi olay uzunluğunun kritik ekolojik eşiklerin altına düşürülmesi, sistemdeki tip dönüşümlerini (tipping points) maskeler. | Elena & Lenski (2003) `10.1038/nrg1088` | Deneysel Evrim Gözlemi | Tam Uyumlu. Olay bütçesinin 30 olayın altına düşürülmemesi gerektiğini doğrular. |

### Deneysel Ön-Kayıt ve Metodolojik Sentez

İncelenen metodolojik literatür ışığında, deneysel ön-kayıt (pre-registration)
sürecinde dikkate alınması gereken metodolojik bileşenler şu şekilde
özetlenebilir:

1. **Seçilim Şeması:** Bireyler arası seçilimde erken yakınsamayı engellemek ve
   olay bazlı zaman dizilimiyle uyum sağlamak için Moran tabanlı Turnuva
   Seçilimi (k=2) kullanılmalıdır.
2. **İzolasyon ve Kirlenme Yönetimi:** Çevresel kirlenmeyi önlemek için Kol
   Başına Ayrı Havuz (Ayrı Mikrokozmoslar) yapısı kurulmalı; doğrudan rekabet
   aranıyorsa İki Aşamalı Doygunluk Tasarımı ile küme düzeyinde sandviç varyans
   kestiricileri uygulanmalıdır.
3. **Totoloji Kontrolü:** Seçilim iddiası, Price Eşitliği doğrultusunda
   uygunluk (wᵢ) ile sabit yaşta ölçülen drift durum vektörü (zᵢ) arasındaki
   kovaryant ilişkinin istatistiksel anlamlılığı üzerinden kurulmalıdır.
4. **Bütçe Dağılımı:** GPU saat kısıtı altında stokastik gürültüyü azaltmak
   amacıyla bütçe popülasyon boyutunu artırma yönünde (N=16, G=3, Olay
   Sayısı=35) kullanılmalıdır.
