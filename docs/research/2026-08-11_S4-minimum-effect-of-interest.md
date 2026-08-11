# DR brief #1 — S4: en küçük anlamlı etki nasıl gerekçelendirilir

**Öncelik: 1 / 3** — bu cevap gelmeden ön-kayıt kilitlenemez, N hesaplanamaz,
doğrulayıcı koşum başlayamaz. Diğer iki brief bunu beklemiyor.

**Durum:** gönderilmedi · **Slot:** `PREREGISTRATION.md` §9-S4 → S2

---

## Cevaplaman gereken tek karar

Bir ön-kayıt yazıyoruz ve **tek bir sayıyı** gerekçelendirmemiz gerekiyor:

> Eşleştirilmiş bir tasarımda, **hangi büyüklüğün altındaki etki bizi
> ilgilendirmez** — ve bu eşiği **veriye bakmadan** nasıl savunuruz?

Sayı `d_z` cinsinden (eşleştirilmiş farkın etki büyüklüğü). N doğrudan ondan
çıkıyor: `N ≈ ((1.96 + 0.84) / d_z)²`.

| d_z | 0.2 | 0.3 | 0.4 | 0.5 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| gereken N | 197 | 88 | 50 | 32 | 13 | 8 |

Bütçemiz: seed başına ~20 dakika GPU + koşum başına ~7 dakika. N=20 ≈ 6.8
saat, N=32 ≈ 10.8 saat. **N ≥ 6 matematiksel şart** (altında Wilcoxon çift
yönlü α=0.05'te reddedemez).

---

## ⚠ İşe yaramayacak cevap — bunu okumadan yazma

Aşağıdakiler bizi **hiç** ilerletmez, çünkü hepsini zaten biliyoruz:

- *"Cohen'e göre 0.2 küçük, 0.5 orta, 0.8 büyük."* — Cohen'in kendisi bunları
  keyfi ve alan-bağımsız olarak kullanılmaması gereken etiketler diye
  yazmıştı. Bu bir gerekçelendirme değil, bir sözlük.
- *"Genellikle d=0.5 varsayılır, N=15–20 yeterlidir."* — bizim elimizdeki
  brief zaten bunu söylüyordu ve bu proje `SAMPLE_N15_UNDERPOWERED` ile
  çarptı. Varsayımın **nereden geldiğini** soruyoruz, tekrarını değil.
- Kaynaksız genel tavsiye. **Her iddia yazar + yıl + yer ile gelmeli.**

⚠ Kaynak kimliklerini kontrol et: önceki bir brief'te `arXiv:2506.08965`
kimlik/yıl olarak çelişkiliydi ve o madde kullanılamadı.

---

## Cevabın taşıması gereken üç şey

### 1. SESOI'yi gerekçelendirmenin yerleşik yöntemleri

*Smallest Effect Size Of Interest* literatüründe eşik **nasıl** savunulur?
Bildiğimiz aday yaklaşımlar — hangileri geçerli, hangi koşulda, ve hangi
eleştirileri almışlar:

- **Bütçe/kaynak temelli** (small telescopes: *"öncekinin %33 gücüyle
  saptayabileceği en küçük etki"*)
- **Alanın kendi dağılımından** (o alanda yayımlanan etkilerin alt çeyreği)
- **Pratik/anlamlılık temelli** (etkinin karar değiştirdiği eşik)
- **Eşdeğerlik testi çerçeveleri** (TOST ve türevleri) — eşiği önceden ilan
  edip *"anlamlı fark yok"* diyebilmenin yolu

Bir alanın kendi tipik etkisinden eşik türetmek **ne zaman döngüsel**, ne
zaman meşru?

### 2. Bütçeden N seçmek: meşru mu, kaçamak mı?

Alternatif yolumuz: N'i **bütçeden** seç, ve ön-kayıtta *"bu N şu d_z'nin
altını saptayamaz; o bandda güçsüzüz"* diye **ilan et**.

- Bu yerleşik ve kabul gören bir uygulama mı, yoksa eleştirilen bir kaçamak
  mı? Hangi isimle anılıyor?
- Kabul gördüğü koşullar neler?
- **Raporda nasıl yazılmalı** ki "etki yok" ile "güçsüzdük" karışmasın?
- Bu yolla yazılmış, örnek alınabilecek ön-kayıtlar var mı?

### 3. Bizim tipimizde çalışmalarda etki büyüklükleri nerede

Bu **kritik** kısım, ve bizim özgün durumumuz:

Deney LLM ajanlarında **parametrik plastisite** ölçüyor — ajanın kendi
yaşadığı olaylardan türetilmiş DPO çiftleriyle ajan-başına LoRA eğitimi, ve
uç nokta ajanın **içsel** bir durumu (varisin doğum anındaki drift
büyüklükleri), bir görev başarım skoru değil.

- Bu tipte — LLM ajan, kendinden türetilmiş tercih verisi, içsel uç nokta,
  eşleştirilmiş kol tasarımı — raporlanan etki büyüklükleri hangi aralıkta?
- Eşleştirilmiş tasarımlarda `d_z`, eşleştirilmemişte `d` olarak **ayrı ayrı**
  ver; ikisi karıştırılırsa N iki kat yanlış çıkar.
- Bu alanda **yayın yanlılığı** ne kadar ciddi? Yani raporlanan etkilerin
  medyanı, gerçek etki dağılımının ne kadar üstünde olabilir?

---

## Deneyin dürüst tarifi

Yanlış tarif edilirse cevap işe yaramaz. Süslemeden:

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit NF4, ajan başına LoRA (r=8,
  α=16). Olay başına bir karar.
- **Yaşam:** 50 olay. Ortak kaynak havuzu (GovSim tipi), kıtlık/kriz baskısı,
  anı kasası (Ebbinghaus unutma + PageRank benzeri getirim), tahmin hatası
  (MiniLM cümle gömme ile ölçülen **anlamsal** sürpriz).
- **Eğitim:** faz sonunda, ajanın **kendi** olaylarından türetilen tercih
  çiftleriyle DPO. Tercih yönü: düşük tahmin hatası tercih edilir. İnsan
  etiketçi yok, yargıç model yok.
- **Kollar** (aynı seed içinde eşleştirilmiş): `lived` gerçek çiftler ·
  `null` hiç eğitim · `shuffle` **aynı** çiftler, tercih yönü tamamen ters.
- **Nesil:** ata bir varis üretiyor; varis anıları ve drift durumunu miras
  alıyor, **ebeveynin adapter'ını almıyor**.
- **Birincil uç nokta:** transfer anında ölçülen doğum-drift büyüklükleri
  (üç alanlı vektör; olaylar üstünde ortalama **yok**).
- **Tekrarlanabilirlik:** aynı seed + aynı kod **bit düzeyinde** aynı sonucu
  veriyor (dokuz kol, üç koşum, altı adapter `sha256` özdeş). Yani
  koşum-arası gürültü **sıfır**; tek varyans kaynağı seed'ler arası.

**İlan edilmiş sınırlar:** popülasyon yok, her ata tam olarak bir varis ⇒
aktarım **Lamarckçı** · iki nesil · uygunluk skoru dejenere, seçilim katmanı
atıl · ΔPE ikincilleri ayrımın **%73–86'sını** iptal ediyor — her iki nesilde
de ayrı ayrı ölçüldü (bu yüzden birincil onlar değil).

⚠ **Elimizdeki N=3 sayılarını bilerek vermiyorum.** Onlardan eşik türetmek
post-hoc olur ve brief'i kirletir. Sayı istersen sonra veririm; **eşiği
onlara bakmadan gerekçelendir.**

---

## İstenen çıktı biçimi

1. Yukarıdaki üç başlığa **kaynaklı** cevap (yazar, yıl, yer).
2. **Somut bir tavsiye:** bizim tarif ettiğimiz deney için hangi yolu
   önerirsin (SESOI beyanı mı, bütçeden N mi), ve **neden**.
3. Önerdiğin yol SESOI ise: hangi `d_z`, hangi gerekçeyle.
   Önerdiğin yol bütçeden N ise: raporda kullanılacak **tam cümle** kalıbı.
4. Karşı argüman: seçtiğin yolun bu deneyde **nasıl eleştirileceği**.

---

## Geldiğinde ne olacak

Claude Code her iddia için mutabakat tablosu üretir (brief ne diyor / bizim
veri-kod ne diyor / karar ∈ {bilinçli sapma · fark edilmemiş kayma · uyumlu ·
brief yanılmış}), `docs/research/RECONCILIATION.md`'ye bölüm ekler. S4
kapanırsa `PREREGISTRATION.md` §9 güncellenir ve S2 (N) hesaplanır.
