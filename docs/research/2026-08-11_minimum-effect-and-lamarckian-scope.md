# DR brief — en küçük anlamlı etki, ve tek soylu Lamarckçı tasarımın iddia sınırı

**Durum:** gönderilmedi (taslak) · **Açan:** Claude Code, Yasin'in onayıyla
**Bağlam:** `docs/PREREGISTRATION.md` §9-S4 kilidi · D-043

---

## Neden bu soru DR'ye gidiyor

D-007'nin iş bölümü: *"literatürde X mi Y mi savunulabilir"* DR'nin işi.
S4 tam olarak bu tipte — **kodda cevabı yok**, ve kendi verimizden seçmek
§2.7'nin yasakladığı post-hoc tuning olur.

⚠ **Provenans sorusu sorulmuyor.** DR'nin commit geçmişine erişimi yok ve
makul görünen ama kaynaksız metin üretir (D-007). Sorular yalnızca literatüre
dair.

⚠ **Bu brief bir iddia toplar, kanıt değil.** §9'un sicili: yedi iddiadan
dördü yerelde çürüdü. Gelen her madde mutabakat tablosuna girer
(brief ne diyor / kod-veri ne diyor / karar), ve doğrulanmadan `CLAUDE.md`'ye
"kilitli karar" yazılmaz.

---

## Deneyin dürüst tarifi — DR'ye aynen verilecek

Yanlış tarif edilirse gelen cevap işe yaramaz. Süslemeden:

- **Ajan:** yerel Llama-3.1-8B-Instruct, 4-bit NF4, ajan başına LoRA
  adapter (r=8, α=16). Karar döngüsü LangGraph; ajan olay başına bir kez
  davranıyor.
- **Yaşam:** 50 olaylık bir faz. Ortak kaynak havuzu (GovSim tipi CPR),
  kıtlık/kriz baskısı, anı kasası (Ebbinghaus unutma + PageRank benzeri
  getirim), tahmin hatası (MiniLM cümle gömme ile ölçülen anlamsal sürpriz).
- **Eğitim:** faz sonunda, ajanın **kendi** yaşadığı olaylardan türetilen
  tercih çiftleriyle DPO. Tercih yönü: **düşük tahmin hatası tercih edilir.**
  İnsan etiketçi yok, yargıç model yok.
- **Kollar (aynı seed içinde eşleştirilmiş):** `lived` (gerçek çiftler) ·
  `null` (hiç eğitim) · `shuffle` (**aynı** çiftler, tercih yönü tamamen
  ters çevrilmiş).
- **Nesil:** ata bir varis üretiyor. Varis anıları ve drift durumunu miras
  alıyor; **ebeveynin adapter'ını almıyor**.
- **Uç nokta:** transfer anında ölçülen doğum-drift büyüklükleri.
- **Tekrarlanabilirlik:** aynı seed + aynı kod bit düzeyinde aynı sonucu
  veriyor (ölçüldü, dokuz kol, iki koşum).

**Tasarımın ilan edilmiş sınırları** (bunlar DR'ye de söylenecek):
popülasyon yok · her ata tam olarak bir varis bırakıyor, yani **farklı
üreme yok** ⇒ aktarım **Lamarckçı**, Darwinci değil · iki nesil ·
uygunluk skoru (`F_agent`) şu an dejenere ve seçilim katmanı atıl.

---

## Sorular

### 1 — En küçük anlamlı etki (S4'ün doğrudan hedefi)

Bu tipte bir deneyde — LLM ajanı, yaşanmış deneyimden türetilmiş DPO,
eşleştirilmiş kol tasarımı, içsel bir uç nokta — **hangi etki büyüklüğü
"anlamlı" sayılır?**

- Benzer parametrik-plastisite çalışmalarında raporlanan etki büyüklükleri
  ne aralıkta? Eşleştirilmiş tasarımlarda `d_z`, eşleştirilmemişte `d`
  olarak ayrı ayrı.
- *"Bu büyüklüğün altı ilgilendirmez"* eşiğini **gerekçelendirmenin**
  yerleşik yolları neler? (smallest effect size of interest / SESOI
  literatürü, eşdeğerlik testi çerçeveleri.)
- Bir alanın kendi tipik etkisinden eşik türetmek ne zaman meşru, ne zaman
  döngüsel?

### 2 — Bütçeden N seçmek meşru mu

Ön-kayıtta N'i **bütçeden** seçip *"bu N şu büyüklükten küçük etkiler için
güçsüzdür"* diye ilan etmek yerleşik bir uygulama mı, yoksa eleştirilen bir
kaçamak mı? Hangi koşullarda kabul görüyor, raporda nasıl yazılması
gerekiyor?

### 3 — Tek soylu Lamarckçı tasarım neyi kurabilir

Popülasyonu ve farklı üremesi olmayan, iki nesilli, kazanılmış özelliğin
doğrudan aktarıldığı bir düzenek:

- *"Çevresel baskı organizmayı şekillendirir"* iddiasını **ne kadar**
  destekleyebilir? Hangi daha dar iddiayı meşru kılar?
- Bu iddiayı gerçekten kurmak için literatürdeki **minimum mimari** nedir —
  kaç birey, kaç nesil, hangi seçilim baskısı? (Yapay yaşam / evrimsel
  hesaplama: Avida, Tierra, Lenski'nin uzun-vadeli deneyi gibi yerleşik
  düzenekler ne gerektirmiş?)
- Tek soylu düzeneklerin literatürdeki karşılıkları var mı, ve ne iddia
  etmişler?

### 4 — İçsel amaçlı ince ayar

Eğitim sinyali dışarıdan değil ajanın **kendi ölçülen sonucundan** geliyor
(düşük tahmin hatası tercih edilir), ama **amaç fonksiyonunu biz seçtik.**
Serbest enerji ilkesi bu seçimi savunuyor gibi görünüyor.

- Bu savunma literatürde ne kadar sağlam? Sürprizi vekil hedef yapmanın
  bilinen başarısızlık kipleri neler? (Bizde `lr=5e-5`'te gözlendi: ajan
  *"düşük PE'liyi tercih et"* değil *"yüksek PE'liyi asla söyleme"*
  öğreniyordu — bir tercih değil bastırma deseni.)
- Bunu tercih yönünün korunduğunu doğrulayan **ölçüm** nasıl kurulur?

### 5 — Kanal ayrımı

Aktarım iki kanaldan olabiliyor: sembolik anı kasası, ve ağırlıklar.
Bir varis değiştiğinde hangisinin taşıdığını ayırmanın yerleşik yolu var mı?
Bizim gördüğümüz öneri "yaşantıdan sonra anı getirimini tamamen kapat,
yalnız ağırlıklara yansıyanı ölç" (OOD behavioral probing) — bu yaygın ve
kabul gören bir yöntem mi, sınırları neler?

---

## Beklenen çıktı

Her soru için: literatürden **kaynaklı** cevap + kaynak kimliği (yazar, yıl,
yer). ⚠ Kaynak kimlikleri kontrol edilecek — 08-10 brief'inde
`arXiv:2506.08965` kimlik/yıl olarak çelişkili çıktı ve kullanılmadı.

Cevap geldiğinde: `docs/research/RECONCILIATION.md`'ye mutabakat bölümü,
ve S4 kapanırsa `PREREGISTRATION.md` §9 güncellenir.
