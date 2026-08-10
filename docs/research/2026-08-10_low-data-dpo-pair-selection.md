# Aşırı Düşük Veri Rejiminde Çok-Ajanlı DPO Hizalaması
## Çift Üretimi, Filtreleme ve Öğrenme Dinamikleri

**Kaynak:** Gemini Deep Research · **Alındı:** 2026-08-10
**Prompt'u yazan:** Claude Code (U5 öncesi) · **İsteyen:** Yasin

⚠ **Bu dosya bir iddia listesidir, kanıt değil.** CLAUDE.md kuralı: brief'teki
her iddia DAU kod tabanında ayrıca doğrulanır; doğrulanmadan "kilitli karar"
olarak yazılmaz. Mutabakat tablosu → `RECONCILIATION.md`.

⚠ **Bağlam:** 08-08 brief'inin iki merkezî iddiası (Qwen "şiddetle önerilir",
VRAM farkı ~800 MiB) 2026-08-10'da yerel ölçümde **düştü** (D-026). Aynı
şüphecilik buna da uygulanır.

⚠ **Kaynak tutarsızlığı (Claude Code notu, 2026-08-10):** M-DPO için verilen
`arXiv:2506.08965` kimliği ile "(2024)" yılı **birbiriyle çelişiyor** — `2506`
öneki 2025 Haziran'ı gösterir, bir 2024 makalesi bu kimliği taşıyamaz. Bu
iddia kaynağı doğrulanana kadar kullanılmamalıdır.

---

## 1. Aşırı düşük veri rejiminde DPO operasyonel dinamikleri

DPO kaybı:

```
L_DPO(θ) = -E[ log σ( β·log(π_θ(y_w|x)/π_ref(y_w|x))
                     - β·log(π_θ(y_l|x)/π_ref(y_l|x)) ) ]
```

1–5 çiftle tek epoch → 1–5 gradyan güncellemesi. LoRA rank 8 / alpha 16
(ölçekleme α/r = 2.0, hedef q_proj + v_proj) altında tek adımdaki ağırlık
değişimi `Δθ = -η · (α/r) · ∇_θ L_DPO` ile sınırlı. β = 0.10 gradyan
genliğini ölçeklediğinden toplam logit kayması küçük kalır: genel karar
mekanizması değil, yalnızca ilgili prompt bağlamındaki eylem logitlerinde
marj kayması.

### Literatürde bildirilen minimum örnek sayıları

**DITTO** — Kim ve ark. (2024, `arXiv:2406.00888`). **10'dan az** gösterim-
tercih çiftiyle DPO hizalaması. Mistral-7B, hem LoRA hem tam parametre.
E-posta / haber özeti / blog alanlarında kazanma oranı: few-shot prompting'e
göre **+%33.4**, SFT'ye göre **+%11**, SPIN'e göre **+%20.2**.

**M-DPO** — Zhang ve ark. (`arXiv:2506.08965`, ⚠ yıl/kimlik çelişkili).
Llama-3-8B-Instruct üzerinde CoT örneklemesi + perplexity tabanlı tercih
puanlaması ile few-shot M-DPO'nun binlerce örnekli standart DPO ile eşdeğer
ödül modelleme performansına ulaştığı iddia ediliyor.

**Parametre büzülmesi** — Deng ve ark. (2025, `arXiv:2502.14560`, *"Less is
More: Improving LLM Alignment via Preference Data Selection"*). Az/gürültülü
veriyle DPO'da **parameter shrinkage**. Az veri rejiminde β = 0.10 gibi
görece yüksek bir değer ve lr = 5e-5, modelin `y_w` olasılığını artırmak
yerine `y_l` olasılığını aşırı bastırmasına (**unlikelihood push**) yol açar.
DPO başarısı düşük öğrenme oranlarına bağlı: Zephyr-Beta ve Tülu 2'de
**5e-7 – 1e-6**. 5e-5 gibi yüksek oranlar az örnekle birleştiğinde genel dil
yeteneğinde bozulma riski taşır.

---

## 2. Alternatif hizalama yöntemleri (tek haneli çift)

| Yöntem | Veri yapısı | Kayıp mantığı | Düşük veride davranış | Kaynak |
|---|---|---|---|---|
| **DPO** | çiftli | log-sigmoid log-oranı | N ≤ 5'te unlikelihood baskısı yüksek; log-olasılık düşüşü, parametre büzülmesi | Rafailov 2023; Deng 2025 |
| **IPO** | çiftli | karesel hata, kısıtlı log-oranı | Sınırlı kayıp → aşırı uyumu ve logit patlamasını engeller | Azar 2024, `arXiv:2310.12036` |
| **KTO** | **tekli** (x, y, z∈{−1,1}) | Kahneman-Tversky değer fonksiyonu | Çift kurma zorunluluğunu kaldırır; **O(n²) eleme darboğazını aşar** | Ethayarajh 2024, `arXiv:2402.01306` |
| **SimPO** | çiftli | referanssız, uzunluk-normalize marj | Referans çıpası yok → az veride hızla aşırı uyum; erken durdurma şart | Meng 2024, `arXiv:2405.14734` |
| **Tercih ağırlıklı SFT** | **tekli** (x, y_w) | ağırlıklı çapraz entropi | Negatif itme yok → gradyan kararlılığı en yüksek, dil bozma riski en düşük | Touvron 2023; Ouyang 2022 |

**IPO kaybı:**

```
L_IPO(θ) = E[ ( log(π_θ(y_w|x)/π_ref(y_w|x))
              - log(π_θ(y_l|x)/π_ref(y_l|x)) - 1/(2β) )² ]
```

Marjı `1/(2β)`'ye sabitler; az sayıdaki örneğin gradyanı domine etmesini
engeller.

**KTO** — eylemler tek tek PE'ye göre "başarılı/başarısız" etiketlenebiliyorsa,
eşleştirmedeki O(n²) karmaşıklığı **ve** NLI filtreleme kayıplarını tamamen
ortadan kaldırır.

⚠ **SimPO'da çelişen bulgular:** büyük veri setlerinde DPO'dan iyi, ama
N ≤ 5'te referans çıpası olmadığından hızla aşırı uyum + reward collapse.

---

## 3. Tercih çifti seçimi

**Deng ve ark. (2025, `arXiv:2502.14560`).** UltraFeedback üzerinde
Llama-3-8B / Mistral-7B / Qwen-2.5-7B ile: veri setinin **yalnızca en yüksek
marjlı %10'u** kullanıldığında, %100 ile eğitilen modellere kıyasla
AlpacaEval 2.0'da **+3 ile +8 puan** kazanma oranı. Dışsal ödül marjı `r_ex`
ile örtük DPO ödül marjı `r_im`'in birleştiği **çift-marjlı seçim** savunuluyor.
Düşük marjlı/gürültülü çiftler **parametre büzülmesi**, net kontrastlı yüksek
marjlı çiftler **parametre enflasyonu** yaratıyor.

**DAU'nun "olay başına en güçlü PE farkı" kuralı** literatürdeki **Marj
Maksimizasyonu** ilkesiyle **örtüşüyor**. Ancak iki tuzak:

1. **Uç değer hassasiyeti.** Sinha ve ark. (2025, `arXiv:2605.10855`) ve MADPO
   (2025, `arXiv:2510.05342`): aşırı zor / uç değerdeki örnekleri tutmak
   tercih öğreniminde gürültü etkisi yaratıp performansı düşürüyor. Yalnızca
   maksimum farka odaklanmak, gerçek politika tercihini temsil etmeyen
   gürültülü uç değerleri eğitim setine sokabilir.
2. **Hizalama evresi ihlali.** OpenReview (2024, `tz9mJmgrdM`): süreç iki
   evre — **Tercih Enjeksiyonu** (çeşitlilik odaklı) ve **Tercih İnce Ayarı**
   (kalite/marj odaklı). Erken aşamadaki ajanlarda tüm adayları olay başına
   tek çifte indirgemek, keşfedilmemiş davranış uzayını daraltır ve
   enjeksiyon evresi için gereken çeşitlilik sinyalini yok eder.

---

## 4. NLI çelişki filtresinin yetersizliği

**İddia:** %99.9 eleme oranı (746 adaydan 745), yalnızca 0.60 eşiğinin yanlış
kalibre olduğunu değil, **NLI cross-encoder'ının bu görev için yapısal olarak
yanlış araç** olduğunu gösterir.

**Gerekçe:** `nli-deberta-v3-small` MNLI/SNLI ile eğitilmiş; **önermesel
mantık çelişkisini** ölçer — bir ifadenin doğruluğunun diğerini imkânsız
kılması. Simülasyondaki eylem cümleleri ise **aynı kayıt düzeyinde alternatif
kararlar**. "I cooperate and share resources" ile "I extract all resources"
stratejik olarak zıt, ama biçimsel mantıkta biri diğerini yanlışlamaz. NLI bu
tür cümleleri büyük oranda **Neutral** sınıfına atar ve çelişki olasılığını
**0.01–0.20** bandında döndürür. Bu nedenle ≥ 0.60 eşiği geçerli davranışsal
zıtlıkların neredeyse tamamını hatalı eler.

### Önerilen alternatif kutupsallık ölçütleri

1. **Gömme kosinüs mesafesi** (all-MiniLM-L6-v2 veya Contriever):
   `d(y_w, y_l) = 1 - cos(e(y_w), e(y_l))`. Alt sınır **> 0.25** (aynı eylemin
   tekrarını engeller), üst sınır **< 0.80** (tamamen farklı konuya kaymayı
   engeller).
2. **Politika logit ıraksaması** — harici model gerekmez; mevcut `π_θ`'nin iki
   tamamlama üzerindeki jeton bazlı logit dağılımları arasında **Jensen-Shannon
   ıraksaması**. Yüksek JSD = modelin iki eyleme kesin farklı olasılık kütlesi
   ataması.
3. **Alan sınıflandırıcısı** — eylemleri stratejik boyutlara (Bencil vs
   İşbirlikçi) haritalayan hafif, alana özgü kural/başlık.

---

## 5. Greedy vs sampling

DAU ölçümü (brief'e girdi olarak verildi): 50 olayda greedy **27**, sampling
(T=0.2) **44** benzersiz completion. Brief'in yorumu: **çeşitlilik darboğazı
üretimde değil, filtrelemede.**

- OpenReview (2024, `tz9mJmgrdM`): on-policy tercih verisi statik off-policy'ye
  göre Llama-3'te **3×** hizalama verimliliği — ama üretilenlerin yüksek
  kaliteli ve düşük gürültülü olması şartıyla.
- N ≤ 5'te sampling'in çeşitlilik kazancı **jeneratif gürültü** getirir. `y_l`'ye
  karışan sentaktik detaylar / biçimsel tutarsızlıklar, DPO'nun stratejik
  davranış yerine **biçimsel unsurları cezalandırmasına** yol açar (style bias
  / reward hacking). Greedy, PE farkının tamamen anlamsal içerikten gelmesini
  garanti eder.

**Sonuç:** düşük güçlü ve az örnekli deneylerde sampling'in çeşitlilik kazancı,
gradyan kararsızlığı maliyetini karşılamıyor. Literatür **greedy veya T ≤ 0.1**
destekliyor.

---

## 6. Replay (sürekli tercih öğrenimi)

- **COFS-DPO** — Zhang ve ark. (2024, `arXiv:2406.05534`): DPO ardışık ve
  çapraz alan eğitimlerinde geçmiş tercihleri hızla unutuyor; hızlı/yavaş LoRA
  modülleri + replay tamponu ile geçmiş hizalama performansı korunuyor.
- **Korycki & Krawczyk** (2021, `arXiv:2104.11861`): concept drift altında
  merkez odaklı (centroid-driven) replay hafızası hem geçmişi koruyor hem yeni
  tercihlere uyumu hızlandırıyor.

**Önerilen parametreler:**
- **Karışım oranı:** toplam eğitim verisinin **%10–15'i** geçmiş yaşam
  döngülerinden. %5 altı unutmayı önlemede yetersiz; %25 üstü yeni nesle
  adaptasyonu geciktiriyor.
- **Seçim kriteri:** geçmişte en yüksek marjlı çiftler (**Top-Margin**) veya
  gömme uzayında merkez noktalarını temsil eden **prototype** çiftler.

---

## 7. Brief'in önerdiği, yerel olarak ucuza doğrulanabilir 3 iddia

**H1 — NLI yerine kosinüs mesafesi.** `1 - cos ≥ 0.35` kullanıldığında 50
olaylık tek yaşamda kabul edilen çift sayısı **1–2'den 15–30 bandına** çıkacak
ve DPO gradyan normu dalgalanması **en az %50** azalacak.

**H2 — IPO > DPO tek haneli rejimde.** β=0.10, lr=5e-5 ile 1–5 çiftte IPO,
vanilla DPO'ya kıyasla tercih edilen eylemlerin ortalama log-olasılığındaki
çöküşü önleyecek ve 3 nesil sonunda karar çeşitliliğini **%40 daha yüksek**
tutacak.

**H3 — %10 replay politika çökmesini önler.** Mevcut yaşamın 2–3 çiftine
geçmiş yaşamların en yüksek PE farklı %10'luk (1–2 çift) replay verisi
eklenmesi, 5 ardışık nesil sonunda dil üretebilirliğini (perplexity + gramer
geçerliliği) koruyarak politika çökmesini **tamamen** engelleyecek.

⚠ H1/H2/H3'ün "%50 azalacak", "%40 daha yüksek", "tamamen engelleyecek" gibi
nicel vaatleri **brief'in tahminleri**, ölçüm değil. Yerel doğrulama bu
sayıları teyit etmek zorunda değil — yön doğruysa iddia kısmen tutmuş sayılır,
ama sayılar D-kaydına brief'in tahmini olarak geçer.
