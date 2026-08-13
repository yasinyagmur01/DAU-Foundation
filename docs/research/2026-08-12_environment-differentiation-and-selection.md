# DR brief #4 — ayrım üretmeyen bir evrende seçilim kurulabilir mi

**Öncelik: 1** — ikinci ön-kaydın mimarisini bu belirliyor. Bir sonraki
doğrulayıcı koşum (≈13 GPU saat) bu sorunun cevabı olmadan tasarlanamaz.

**Durum:** gönderilmedi · **Tarih:** 2026-08-12

---

## 0. Bu brief'i okuyan için: neye ihtiyacımız var, neye yok

**İhtiyacımız olan:** literatürde, çok-ajanlı veya tek-ajanlı yapay yaşam /
LLM-ajan simülasyonlarında **ajanlar arası ayrım (heterojenlik) üretmenin**
bilinen tasarım kalıpları; ve bunların hangi koşullarda **seçilim iddiasını**
desteklediği.

**İhtiyacımız olmayan:** bizim proje geçmişimiz, hangi kararı ne zaman
verdiğimiz. Bunlara erişimin yok; makul görünen ama kaynaksız bir anlatı
üretmen bize zarar verir.

⚠ **Kaynak kimliği kritik.** Önceki üç brief'imizde altı kaynak yanlış
atfedilmişti (iki farklı metrik aynı 2002 tarihli makaleye atfedilmiş, bir
arXiv kimliği ile yılı çelişiyordu). **Her iddia için yazar + yıl + kalıcı
kimlik (DOI/arXiv) ver, ve emin değilsen "doğrulanamadı" yaz.** Uydurulmuş
bir referans, cevapsız bir soru kadar değil, ondan **daha** pahalı.

---

## 1. Sistemin dürüst tarifi

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit, ajan başına LoRA adapter.
  Olay başına bir karar. LLM yalnız bilişsel yük eşiği aşılınca çağrılıyor;
  altında deterministik bir durum makinesi karar veriyor.
- **Yaşam:** 50 olay. Ortak kaynak havuzu (lojistik yenilenme), kıtlık krizi,
  anı kasası (Ebbinghaus unutması + PageRank benzeri getirim), MiniLM ile
  ölçülen anlamsal tahmin hatası (PE).
- **Öğrenme:** yaşam sonunda, ajanın **kendi** olaylarından türetilen tercih
  çiftleriyle DPO. Tercih yönü: düşük PE tercih edilir. İnsan etiketçi yok,
  LLM yargıç yok.
- **Nesil:** ata **bir** varis üretiyor (popülasyon yok, farklı üreme yok).
  Varis anıları ve drift durumunu miras alıyor, **ebeveynin adapter'ını
  almıyor**.
- **Test edilen iddia:** yaşanmışlığın izi ağırlıklara işlenip nesle
  aktarılabilir mi. Kontrol kolu: **aynı çiftler, tercih yönü %100 ters**
  (`shuffle`). Yani "eğitim oldu mu" değil, "eğitimin **içeriği** yaşama
  özgü mü" sorusu soruluyor.
- **Tekrarlanabilirlik:** aynı seed + aynı kod bit düzeyinde aynı sonucu
  veriyor (ölçüldü, dokuz kol).

---

## 2. Ölçülmüş durum — hepsi 40 seed × 3 kol = 120 kol üzerinde

Aşağıdaki sayıların **hepsi ölçümdür**, tahmin değil. Türetilmiş olanlar
öyle etiketlendi.

### 2.1 Seçilim katmanı tamamen atıl

Fitness formülü: `F = 0.4·(E/E_max) + 0.3·(1 − |Δhavuz|/P_max) + 0.3·(t_hayatta/t_nesil)`

| Girdi | 120 kolda gözlenen |
|---|---|
| `E` (enerji, ağırlık **0.4**) | **0.000** — tek bir farklı değer |
| `t_hayatta / t_nesil` (ağırlık 0.3) | **1.0** — kimse ölmüyor |
| `Δhavuz` (ağırlık 0.3) | 393.55 ± 2.62 · **6 farklı değer** · yayılım **%0.7** |
| Sonuç `F` | **0.000**, ve fitness sınıfı 120/120 `low` |

**Karşı-olgusal (hesaplandı):** formüldeki birim uyuşmazlığı düzeltilse bile
`F` 0.3048 ± 0.0020 (%0.64 yayılım) ya da 0.5764 ± 0.0002 (%0.03) oluyor —
her iki durumda da **120 kolun hepsi aynı fitness sınıfına** düşüyor.
Yani formülü düzeltmek ayrım üretmiyor; **girdilerin ikisi sabit**.

### 2.2 Enerji **yapı gereği** asla artamıyor

Olay başına:
```
decay    = max(PE, METABOLIC_FLOOR)        ≥ 0.05
recovery = METABOLIC_FLOOR · (1 − mean_load) ≤ 0.05
energy  := clamp(energy − decay + recovery, 0, 1)
```
`mean_load ≥ 0` olduğundan `decay ≥ recovery` **her zaman** ⇒ enerji
monoton azalan. Ölçülen PE ortalaması 0.425 ⇒ olay başına net −0.40 ⇒
enerji **2. olayda** tabana vuruyor ve kalan 48 olay boyunca 0'da kalıyor.

Aynı sabit hem asgari tüketim hem azami toparlanma olarak kullanılıyor;
toparlanma tüketimin en fazla **%12'si** olabiliyor.

### 2.3 Davranış tek noktada toplanmış: defect bedava ve baskın

Karar sınıfına göre çıkarım: `DEFECT=8.0` · `COOPERATE=2.0` ·
`COORDINATE=1.0` · `DEADLOCK=0.0` (4 kat aralık).

Gözlenen toplam çıkarım 50 olayda: ortalama **393.55**, min 382,
**max tam 400**.

**Türetilmiş:** 400 = 50/50 olay DEFECT. Ortalama ≈ **48.9/50 (%98)**,
min ≈ 47/50 (%94). ⇒ Ajanlar olayların %94–100'ünde **en yüksek çıkarımı**
seçiyor.

Sebebi: çıkarılan kaynak **enerjiye dönmüyor** (kodda bağ yok) ve havuz
çökünce **kimse ölmüyor**. Yani en çok çıkarmanın hiçbir bedeli yok.
Ayrıca sistem prompt'u `extract, take` gibi kelimelere yönlendiriyor ve
karar sınıflandırıcısı tam o kelimelere bakıyor (ölçüldü: COOPERATE
sınıfının eşleştiği kelimelerin 3/4'ü prompt'ta geçiyor).

### 2.4 Kıtlık var ama ayırt edici değil

Havuz gerçekten çöküyor: kaynak travması **120/120 kolda** bayraklı. Ama
büyüklüğü yalnız **%1.9** yayılıyor, ve 40 seed'in **38'inde üç kolun
kaynak travması birebir aynı**. Baskı var, **ayırt edici** baskı yok.

### 2.5 Bunun sonucu: ön-kayıtlı test null çıktı

Birincil uç nokta varisin doğum-drift vektörü. `lived` ile `shuffle`'ın
`null`'dan uzaklıkları karşılaştırıldı (N=40, eşleştirilmiş Wilcoxon):
**p = 0.9914**, etki `d_z = −0.000`. Üç kol birbirine **eşit uzaklıkta**.

Ve uç noktanın çözünürlüğü ölçüldü: vektörün **%99'u** her kolda bulunan
neredeyse sabit bir terim; **40 seed'in 11'inde** `lived` ve `shuffle`
birebir aynı vektörü üretiyor, yani o seed'lerde **mükemmel eğitilmiş bir
adapter bile görünemezdi**.

### 2.6 Öğrenme tarafı düzeltilebilir çıktı (bu kısım çözüldü)

96 hücrelik bir tarama (öğrenme oranı × gradyan kırpma tavanı):
- Kırpma tavanını yükseltmek (kırpma %100 → %0) kaybı **hiç** değiştirmiyor
  — AdamW ikinci momente bölerek normalize ettiği için gradyan ölçeğine
  duyarsız.
- Öğrenme oranı kaldıraç: DPO kaybı 0.694 → 0.651 (ln 2 = 0.6931'in
  0.044 altına).
- Taranan bantta bastırma deseni yok (`Δlogp` chosen/rejected oranı
  0.33 → 1.01, simetrik).

⇒ **Parametrik kanal öğrenebiliyor.** Darboğaz eğitim değil, evren.

---

## 3. Asıl soru

**Ajanlar birbirinden farklı hayat yaşamıyorsa, "yaşamın izi aktarılıyor mu"
sorusu ölçülebilir mi — ve ölçülebilir hale getirmenin bilinen yolları
nelerdir?**

Bizim okumamız şu ve **çürütülmesini istiyoruz**: popülasyon eklemek tek
başına yetmez, çünkü N ajanın hepsi aynı baskın stratejiyi oynarsa
fitness'ları yine özdeş olur. Önce **seçimin bir bedeli** olmalı.

---

## 4. Cevaplanmasını istediğimiz sorular

### S1 — Yapay yaşam / commons simülasyonlarında heterojenlik nasıl üretiliyor

Ajanlar aynı kural setiyle başladığında davranışsal ayrımı üreten **standart
mekanizmalar** neler? Özellikle:
- kaynak-tükenmesi oyunlarında (commons dilemma, GovSim benzeri kurulumlar)
- metabolik modellerde (enerji kazanma/harcama döngüleri)
- stokastik başlangıç koşulu mu, rol asimetrisi mi, mekânsal ayrım mı,
  yoksa ödül yapısının kendisi mi baskın çözüm?

Hangi mekanizmaların **çalıştığı ölçülmüş**, hangileri teorik öneri?

### S2 — Baskın strateji çökmesi LLM ajanlarında bilinen bir olgu mu

Bizde ajan olayların %94–100'ünde aynı eylemi seçiyor. LLM tabanlı
ajan simülasyonlarında **eylem uzayının tek noktaya çökmesi** rapor
edilmiş mi? Sebep olarak ne gösteriliyor — prompt priming, ödül yapısı,
model önseli? Ve **ölçülmüş** karşı-tedbirler neler?

⚠ Bizim özel durumumuz: sistem prompt'u eylem kelimelerini **sayıyor**, ve
davranış sınıflandırıcısı aynı kelimelere bakıyor. Bu tür bir
"prompt→sınıflandırıcı" kısa devresi literatürde adlandırılmış mı?

### S3 — Metabolik döngü tasarımı: enerji neyle kazanılmalı

Enerjiyi kazanılabilir yapacağız. İki uç var:
- **doğru orantı** (çıkarılan kaynak = kazanılan enerji) ⇒ defect yine
  baskın kalır
- **azalan getiri / eşikli** ⇒ aşırı çıkarım cezalanır

Yapay yaşam literatüründe bu tercihin sonuçları üzerine **ölçülmüş** ne var?
Hangi biçim davranışsal çeşitlilik üretiyor, hangisi yine tek noktaya
çöküyor? Ölüm eşiği (enerji 0 ⇒ ajan ölür) ayrımı artırıyor mu, yoksa
erken ölümlerle örneklemi mi daraltıyor?

### S4 — Tek soylu (popülasyonsuz) tasarımda seçilim iddiası nereye kadar

Bizde ata **bir** varis üretiyor. Bu, kazanılmış özelliğin doğrudan
aktarımı — Lamarckçı. Literatürde:
- popülasyon ve farklı üreme **olmadan** hangi iddialar savunulabilir?
- "kültürel/epigenetik aktarım" çerçevesi bu tasarıma uyuyor mu, ve o
  çerçevede kabul gören **kontrol** nedir? (bizimki: aynı çiftler, ters yön)
- popülasyona geçmek zorunluysa, **minimum** popülasyon büyüklüğü ve
  nesil sayısı için literatürde bir alt sınır var mı?

### S5 — Bağlantılı: ödül/fitness manzarasının düz olması

Bizim fitness'ımızın etkin varyansı **%0.2**. Evrimsel hesaplama
literatüründe "düz fitness manzarası" (flat/neutral landscape) tanılı bir
sorun; **teşhis ölçütleri** ve **kurtarma stratejileri** neler? Özellikle:
fitness'ın hangi varyansın altında seçilim baskısı üretemediğine dair
nicel bir eşik var mı?

### S6 — Bağlantılı: uç nokta seçimi

Bizim birincil uç noktamız tek bir andaki vektör (doğum anındaki drift) ve
ölçüldü ki **%99'u sabit bir terim**. Nesiller arası aktarımı ölçen
çalışmalarda hangi uç noktalar kullanılıyor, ve **düşük çözünürlüklü uç
nokta** sorunu nasıl teşhis ediliyor? Yörünge tabanlı ölçütler (tüm dizi
üzerinden) tek-an ölçütlerine göre ne kazandırıyor, ne kaybettiriyor?

---

## 5. Cevabın biçimi

Her iddia için:
1. **Ne söyleniyor** — tek cümle
2. **Kaynak** — yazar, yıl, DOI/arXiv. Emin değilsen **"doğrulanamadı"**
3. **Kanıt türü** — ölçülmüş deney mi, simülasyon mu, teorik öneri mi
4. **Bizim kurulumumuza uyarlanabilirliği** — hangi varsayımı ihlal ediyor

Bir öneri bizim ölçtüğümüz bir sayıyla çelişiyorsa **çelişkiyi göster**;
biz o sayıyı yeniden ölçeriz. Geçmiş brief'lerde en değerli çıktı, bizim
varsayımımızı çürüten satır oldu.

---

## 6. Bu brief'in bilerek dışarıda bıraktıkları

- **Öğrenme oranı / DPO ayarları** — ölçüldü, çözüldü (§2.6). Sorma.
- **Bizim karar geçmişimiz** — erişimin yok, sorulmuyor.
- **Model seçimi, quantization, LoRA rank** — donmuş, bu turda açılmıyor.
- **İstatistiksel test seçimi** — ön-kayıtlı, kapalı.
