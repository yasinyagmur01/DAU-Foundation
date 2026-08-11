# Çok-Nesilli C′ — Ön-Kayıt (Pre-Registration)

**Durum: 🔒 KİLİTLİ · 2026-08-11 · commit `befd72b4ee57`**

**Yedi slotun yedisi kapalı.** Bu andan itibaren bu belgedeki hiçbir madde
değişmez. Değişiklik gerekirse **yeni bir ön-kayıt** açılır ve bu belge
*superseded* işaretlenir.

⚠ **Alet değişikliği penceresi KAPANDI** (CLAUDE.md §2.10). Kilitten sonra
`constraints.py` eşiği, uç nokta, test veya çift kurma stratejisi değişirse
sonuç **post-hoc** olur. Kalan bütün iş kalemleri **ikinci ön-kayıta** gider.

**Doğrulayıcı koşum:** seed **2004–2043** (N=40), iki batch (2004–2023,
2024–2043). Seed 2001–2003 **yakılmış** (D-038) ve bu analize **giremez**.

---

## 1. İddia

DAU aksiyomu: *"Bir agent'a trait veremezsin, sadece yaşam verebilirsin, trait
oradan çıkar."*

Bu ön-kaydın sınadığı iddia, aksiyomun **tamamı değil**, ölçülebilir bir
parçasıdır:

> Bir ajanın yaşadığı olayların **içeriği ve sırası**, o ajanın varisinin
> **hangi alanda ve ne kadar hasarlı doğduğunu** değiştirir.

**Bu ön-kaydın iddia ETMEDİĞİ şeyler** (§8'de gerekçesiyle):

- Yaşamın *neyin miras kalacağını seçtiği* — seçilim katmanı bu koşumda atıl.
- Aktarılan izin *kalıcı* olduğu — tek varis, iki nesil ölçülüyor.
- Popülasyon düzeyinde uyarlanma — popülasyon yok.

---

## 2. Tasarım

Üç kol, **aynı seed içinde eşleştirilmiş**, tek soy (bir ata → bir varis):

| Kol | Ne yapar | Neyi kontrol eder |
|---|---|---|
| `lived` | Faz-1'in PE-sıralı tercih çiftleriyle DPO | — (deney kolu) |
| `null` | Hiç eğitim yok, adapter yok | "Eğitim bir şey yapıyor mu" |
| `shuffle` | **Aynı** çiftlerle, eşleştirme bozularak DPO | "Eğitimin **içeriği** önemli mi" |

Her seed için üç kol da aynı faz-1 ortamından başlar; faz-1 kollar arasında
özdeştir (doğrulandı: `arm_digest`'in faz-1 bileşeni ve `pe_before` üç kolda
aynı). Kollar yalnızca faz-2'de, adapter devreye girdikten sonra ayrışır.

**Birincil karşıtlık `lived` ↔ `shuffle`'dır.** Gerekçe: `null` yalnızca
"eğitim var mı" sorusunu cevaplar; aksiyomun iddiası eğitimin *içeriğine*
dairdir, ve o ancak aynı çiftlerin bozulmuş eşleştirmesine karşı sınanabilir.
`lived` ↔ `null` ön-kayıtlı **ikincil** olarak koşulur.

---

## 3. Birincil uç nokta

**Doğum-drift'in büyüklük kanalı**, transfer anında ölçülür
(`transfer_to_heir` → `birth_drift_magnitudes`). Gen2 koşmadan elde edilir.

Her seed *s* için, `null` kolu ortak çapa alınarak iki mesafe hesaplanır:

```
a_s = || m_lived(s)   − m_null(s) ||₂
b_s = || m_shuffle(s) − m_null(s) ||₂
```

`m_arm(s)` = o kolun doğum-drift büyüklük vektörü, üç alanın (`resource`,
`social`, `uncertainty`) birleşimi üzerinde; bayraklanmamış alan 0 sayılır.

**H0:** `lived` ve `shuffle` değiştirilebilir ⇒ `a_s` ile `b_s` aynı dağılımdan.
**H1 (çift yönlü):** `a_s ≠ b_s`.

**Test:** eşleştirilmiş Wilcoxon işaretli sıra testi, `a_s − b_s` üzerinden,
çift yönlü, α = §9-S3. N < 6 ise Wilcoxon çift yönlü α=0.05'te reddedemez;
bu yüzden N §9-S2'de bu kısıt altında seçilir.

**Neden bu:** kollar arası tek fark adapter'dır (D-037'den sonra aynı seed +
aynı kod bit düzeyinde tekrarlanabilir), yani sıfırdan farklı bir mesafe
tesadüf değil adapter'ın eseridir. Ölçüm gen2'nin stokastikliğinden önce, dört
halkalı nedensel zincirin **ilk** halkasında yapılır (D-002'nin gerekçesi).

---

## 4. Ön-kayıtlı ikincil uç noktalar

İddia edilmez; varyans tahmini üretir ve bir sonraki ön-kaydı güçlendirir.
Hiçbiri birincilin yerine geçemez; birincil null çıkarsa ikincillerden biri
anlamlı olsa bile sonuç **null** olarak raporlanır.

| # | Uç nokta | Test |
|---|---|---|
| S1 | Doğum-drift **kategorik** kanalı: varisin bayraklanan alan kümesi ⚠ **birincilden bağımsız değil, bkz. L11** | Fisher-Freeman-Halton, kol × profil |
| S2 | Doğum-drift **sayım** kanalı: `n_transfer_candidates`, `n_inherited_warnings` | Kruskal-Wallis (⚠ §8-L1: bu kanalın atıl olması bekleniyor) |
| S3 | Faz-1 ΔPE (fazın tamamı, D-036) ⚠ **düşük duyarlıklı, bkz. L9** | eşleştirilmiş Wilcoxon, `lived−shuffle` |
| S4 | Gen2 ortalama PE ⚠ **düşük duyarlıklı, ölçüldü, bkz. L10** | eşleştirilmiş Wilcoxon |
| S5 | Gen2 davranışsal: kriz anında `decision_to_extraction`, ilk travmaya kadar geçen olay | McNemar (ikili sonuçlar) |
| S6 | `f_agent=None` duyarlılık kolu (D-003) | birincil ile aynı test |

**Çoklu karşılaştırma:** ikincillerde düzeltme yapılmaz, çünkü iddia
edilmiyorlar. Bu, her ikincil sonucun yanında **açıkça** yazılır.

---

## 5. Geçerlilik kriterleri (koşum başlamadan önce sabit)

Bir koşum analiz edilebilmek için şunların **hepsini** sağlamalıdır:

- `run_quality = clean`
- 18 değişmezin tamamı geçer (`I0.1–I0.7, I2.1–I2.2, I3.1–I3.4, I4.2, I5.1–I5.4`)
- I0.7 (adapter sızıntısı) yeşil başlar — koşum öncesi `dau_runs/adapters/` boş
- `prompt_skipped_no_record = 0`
- `[LORA][WARN]` sayısı 0
- Her `lived`/`shuffle` kolunda `adapter_present = True`, her `null` kolunda `False`
- `TORCH_DETERMINISTIC_WARN_ONLY = False` (D-037; I0.6 zorunlu kılıyor)

Bunlardan biri düşerse koşum **atılır ve yeniden koşulur** — kısmi analiz yok.
Atılan koşum D-kaydına sebebiyle yazılır.

---

## 6. Seed politikası — kilitleyici

**Onaylı koşum seed 2004'ten başlar.** 2001–2003 keşifsel olarak koşuldu ve
sonuçlarına bakıldı (`baseline_d037_n3_local.json`,
`repro_d038_n3_local.json`); o seed'lerden gelen hiçbir sayı doğrulayıcı
analize giremez. Onlar yalnızca **aletin çalıştığının** kanıtıdır.

Seed'ler `[2004, 2004+N-1]` aralığından, atlamasız, sırayla kullanılır. Bir
seed atlanamaz, değiştirilemez, sonuca bakıp eklenemez.

---

## 7. Durma kuralı

N §9-S2'de kilitlenir. **Ara sonuca bakıp N artırılmaz veya azaltılmaz.**
Koşum donanım arızası dışında durdurulamaz; durdurulursa baştan koşulur.

Ara sonuçlara bakmak **yasak değildir** (alet sağlığı için gerekebilir) ama
bakılan her ara sonuç D-kaydına yazılır ve N'i değiştirmek için kullanılamaz.

---

## 8. İlan edilen sınırlar

Bunlar bu ön-kaydın **bilinen ve kabul edilen** zayıflıklarıdır. Sonuç ne
çıkarsa çıksın bu liste raporda aynen yer alır.

**L1 — Seçilim katmanı atıl.** `F_agent` dokuz koşumun dokuzunda tam olarak
0.000. Sebep birim uyuşmazlığı: `compute_fitness` formülü `|Δpool|`'u havuzun
anlık kapasitesine (`POOL_MAX=100`) böler, ama çağıran `agent_delta_pool` faz
boyunca **kümülatif** çıkarımı veriyor (gözlenen 381–394). Havuz terimi −2.8'e
düşüyor, `[0,1]` clamp'i hepsini sıfıra eziyor. Sonuç: `W_transfer` her
travma-dışı anı için 0, ve `select_for_transfer` "hatırlanan travmayı uyarı
olarak aktar, başka hiçbir şeyi aktarma"ya indirgeniyor. `memory_score` —
ajanın ne öğrendiğinin yaşadığı yer — sıfırla çarpılıyor. Diğer iki girdi de
dejenere: `E=0.000` (9/9), `t_survived/t_generation = 1.0` (9/9).
⇒ **Bu koşum "yaşam neyin miras kalacağını seçer" iddiasını sınamıyor.**

**L2 — Popülasyon yok, dolayısıyla seçilim yok.** Her ata tam olarak bir varis
üretiyor (`transfer_to_heir`); ölen soy, farklı üreme yok. Aktarım
mekanizması **Lamarckçı** (kazanılmış özelliğin doğrudan aktarımı), Darwinci
değil. `F_agent` düzeltilse bile bu değişmez.
⇒ **"Çevresel baskı organizmayı şekillendirir" iddiası bu tasarımla
kurulamaz**; kurulması için popülasyon + farklı üreme + çok nesil gerekir
(D-014).

**L3 — İki nesil.** Kalıcılık iddia edilemez; yalnızca aktarım.

**L4 — Kalibre edilmemiş eşikler.** Polarite bandı `[0.25, 0.80]`
(`POLARITY_COSINE_CALIBRATED=False`, brief'ten geldi, D-032) ve
`SNR_MARGIN_FLOOR=0.15` (`SNR_MARGIN_FLOOR_CALIBRATED=False`, D-030). Bunlar
hangi çiftlerin eğitime girdiğini belirliyor; farklı değerler farklı bir
eğitim seti üretirdi. Duyarlılık analizi **yapılmadı**.

**L5 — GAP-18: `rejected` tarafı az çeşitli.** `best_by_event` sabit bir
`chosen` için en büyük marjı seçtiğinden global maksimum-PE completion çoğu
çiftin reddedilen tarafı oluyor. Yapısal; her yaşamda olur. Doğrudan
kapatmak ölçüldü, ters tepiyor (çift sayısı 9→2, ve çelişik denetim üretiyor).

**L6 — GAP-19: faz-1 ve faz-2 anıları aynı sayaç uzayını paylaşıyor.** Faz-2
taze gövdeyle başladığı için faz-1 anıları olduğundan taze görünüyor;
Ebbinghaus unutma kararı bundan etkileniyor.

**L7 — GAP-5: SYSTEM_PROMPT lexicon priming.** SYSTEM_PROMPT,
`decision_to_outcome`'ın eşlediği kelimelere yönlendiriyor olabilir. İki
bağımsız denetim aynı maddeyi işaret etti (D-010). Metodolojik, bug değil.

**L9 — ΔPE uç noktası ayrımın %80–86'sını atıyor** (D-044). Faz-2'de kollar
olay bazında 0.065–0.194 ayrışıyor, ama faz ortalaması bunun yalnız
%14–20'sini görüyor; kalanı iptal ediyor. İptal simetrik (fark işaretlerinin
%44–64'ü pozitif), yani adapter ajanın **neye şaşırdığını** yeniden
düzenliyor, ortalama şaşkınlık düzeyini kaydırmıyor — ve faz ortalaması buna
yapı gereği kör. En uç örnek: seed 2003 `lived−shuffle`, ham ayrım 0.094, uç
nokta 0.00073 (%99.2 iptal).
⇒ **S3 null çıkarsa bu "etki yok" değil "ölçemedik" demektir** ve raporda
öyle yazılır (§11). ⚠ Bu madde yazıldığında S4 için "muhtemelen" deniyordu;
**S4 sonradan ölçüldü, aynı sınır doğrulandı → L10.**
⇒ Birincil uç noktayı **etkilemez**: doğum-drift büyüklükleri tek bir anın
vektörü, olaylar üstünde ortalama alınmıyor. Bu bulgu birinciliği doğum-
driftte tutma kararını destekliyor.
⚠ Yörünge tabanlı bir uç nokta bu veride çok daha büyük etki gösteriyor ama
**bu ön-kayıta alınmadı** — ölçümü gördükten sonra istatistik seçmek post-hoc
tuning olur (§2.7). Bir sonraki ön-kayıta ve taze veriye bırakıldı.

**L10 — Gen2 `mean_pe` de kayıplı; S4 null'ı teşhis edilebilir değil**
(D-045). L9'un açık bıraktığı soru ölçüldü: gen2'nin uç noktası da olay
düzeyindeki ayrımın çoğunu atıyor. Korunan pay `lived−null` **%17.5**
(gen1: %19.6), üç çiftin ortalaması %26.7.
⇒ **S4 null çıkarsa S3 ile aynı şekilde "ölçemedik" diye raporlanır** (§11).
⚠ İki ek uyarı, sonuç okunurken geçerli:
- `lived−shuffle`'ın %41.6'sı ortalama; seed değerleri %61.4 · %35.6 · %27.9,
  yayılım ortalamadan büyük. **N=3, tek koşum.**
- Gen2'nin iptali gen1'inki gibi **simetrik değil**: bağımsız altı
  karşıtlığın beşinde yaşamın ikinci yarısı daha pozitif, ve kol bazında
  bakınca kaynak iki seed'de `null` varisinin ikinci yarıda çöken PE'si
  (−0.254 / −0.143, `lived` +0.032 / +0.059). Mekanizma adayları **GAP-19**
  (paylaşılan sayaç uzayı ⇒ Ebbinghaus) ve **GAP-3**. Gözlem, iddia değil;
  kilit öncesi kod değişikliğine çevrilmedi.

**L11 — S1 birincilden bağımsız bir kanal değil, ve `resource` atıl**
(D-047). İki ayrı olgu, ikisi de `update_drift`'in yapısından geliyor:
`flags[domain]=True` ile `magnitudes[domain]` **aynı anda, yalnız travma
anında** yazılıyor (`drift.py:41`). Ölçüldü: 11 dosyadaki **69 transfer
kaydının 69'unda** iki sözlüğün anahtar kümesi özdeş, ve hiçbir bayrak
`False` değil.
⇒ **S1 = `set(magnitudes.keys())`**, yani birincilin girdi vektörünün
**desteği**. Korelasyon değil türetilebilirlik. Birincil bir bayrak farkı
üzerinden anlamlı çıkarsa S1 aynı olguyu ikinci kez ölçer. **S1 bu yüzden
destekleyici kanıt olarak raporlanmaz**; birincilin ayrıştırması olarak
raporlanır ve bu §11'de yazılıdır.
⇒ **`resource` bileşeni ayrım üretmiyor:** dokuz kolun tamamı
`3.6404 … 3.7414` (yayılım düzeyin **%2.7'si**), ve seed 2001'de üç kolda
**birebir aynı**. Birincilin ayrımı pratikte ikinci alandan geliyor.
⚠ Uç nokta tanımı **değiştirilmedi**: "bayraklanmamış alan = 0" kuralı
mekanizmaya göre **doğru** (travma yoksa birikmiş büyüklük gerçekten sıfır),
ve tanımı bu noktada değiştirmek aşağıdaki L12 yüzünden post-hoc olurdu.

**L12 — Tasarım pilot seed'lerinde denetlendi, o seed'ler hariç** (D-047).
Birincil uç nokta 2001–2003 seed'lerinde hesaplandı ve `a_s − b_s`'in
**işareti görüldü**. Bu seed'ler **D-038 ile zaten yakılmıştı** ve
doğrulayıcı koşum 2004'ten başlıyor (§6), yani doğrulayıcı analiz
kirlenmedi. Yine de kayda geçer: L11'in iki bulgusu bu denetimden çıktı, ve
**uç nokta tanımı bu bilgi alındıktan sonra değiştirilmedi** — değiştirilse
post-hoc olurdu.

**L13 — Precision-PE işletim noktasında atıl** (D-050). `π = clamp(1/(var/
VAR_REF + ε), 0.5, 1.2)`, `VAR_REF = 1/12` ⇒ π tavandan ancak `var > 0.0694`
(SD > 0.263) olunca çıkar. Ölçülen faz-2 varyansı **0.0289 … 0.0473**,
dokuz kolun dokuzu da altında. Tavana yapışma: gen1 faz-1 **%96**, faz-2'nin
**son 25 olayı %100**, gen2'nin ikinci yarısı **%100**.
⇒ **PE pratikte ham anlamsal PE'nin 1.2 katı.** "Sürpriz sert salınırken
kazancı kıs" mekanizması devreye girmiyor.
⚠ Kilitli karar *"Precision-PE v2.4, kalibrasyon doğrulandı"* **yanlış
değil, ilgisiz**: doğrulama bandı bu koşumların varyans aralığını
kapsamıyor. Değiştirilmedi — kilitli eşiği ölçümü gördükten sonra oynatmak
post-hoc olurdu. L1 (`F_agent`) ve L11 (`resource`) ile aynı sınıf: üçüncü
dejenere girdi.

**L14 — Davranışsal sınıflandırıcı `SYSTEM_PROMPT` tarafından besleniyor**
(D-050, GAP-5 **doğrulandı**). Prompt'un son satırı *"Prefer plain English
words such as resource, extract, take, social, talk, or cooperate…"* diyor;
`decision_to_outcome` tam bu kelimelere bakıyor:

| Sınıf | prompt'un andığı | toplam |
|---|---|---|
| COOPERATE | `cooperate`, `talk`, `social` | **3 / 4** |
| DEFECT | `extract`, `take` | 2 / 7 |
| CONSERVE → COORDINATE | **hiçbiri** | **0 / 6** |

⇒ Davranışsal ölçüm kısmen **prompt'a uyumu** ölçüyor. Doğrudan **S5**'i
etkiliyor ve `OUTCOME_TO_EXTRACTION` üzerinden havuz dinamiğine iniyor.
Düzeltilmedi: `SYSTEM_PROMPT` değişirse her koşum geçersiz olur.

**L15 — Kanal 2 unutmaya bağışık, kanal 1 değil** (D-050, GAP-4 denetimi).
Çiftler `delta_log` + PE olay günlüğünden kuruluyor; Ebbinghaus **kasada**
çalışıyor ve çift kurucu kasayı **hiç okumuyor** ⇒ GAP-4'ün tarif ettiği
senkron kopukluğu **yok**. Ama asimetri var: bir anı kasadan unutulup
varise geçmese de, o olaydan türetilmiş çift ağırlıkları **çoktan
eğitmiştir**. Hata değil — "iki kanal"ın tanımı — ama D-002'nin *"ikisi de
yaşamın izidir"* cümlesi bunu taşımıyor.

**L16 — Olay sayacı fazlar arasında sıfırlanıyor (GAP-19); etkisi şu an
bloke, ama gizli** (D-051). Faz-2 `initial=None` ile başlıyor ⇒
`EventClock` 0'dan sayıyor ⇒ faz-1 ve faz-2 anıları **aynı sayaç
uzayını** paylaşıyor. Konsolidasyon `now_counter = 50` (faz-2 uzunluğu)
kullandığından faz-1'de son kullanılmış bir anı bir faz daha taze görünüyor.
⇒ **Şu an birincile ulaşamıyor**, iki bağımsız halka kesiyor: `should_forget`
travmayı hiç silmiyor, ve L1 gereği (`f_agent=0.000`, 9/9) varise **yalnız
travma** geçiyor (ölçüldü: `n_transfer_candidates=3`, hepsi uyarı).
⚠ **Gizli bağımlılık:** `F_agent` düzeltilir de sayaç düzeltilmezse GAP-19
**anında canlanır** — travma-dışı anılar aktarılabilir olur ve tutulmaları
kırık saatle hesaplanır. **İkisi birlikte düzeltilmeli ya da hiçbiri.**
Değiştirilmedi: ölçülen etkisi sıfır, maliyeti her koşumun geçersizliği.

**L8 — `W_SEM = 0.0`** (GAP-10). ChromaDB vektör benzerliği anı skorlamasına
girmiyor ⇒ **anı seçimi şu an semantik değil**, yalnız yakınlık/güç/PPR.
"Baseline kilitlenince 0.3–0.4 yapılmalı" denmişti; koşul gerçekleşti ama
dönülmedi, ve şimdi dönmek **tabanı yine sıfırlar**. Bu ön-kayıt için sınır,
sonraki için iş kalemi. GAP-10'un diğer iki maddesi de aynı durumda:
**negation sarmalayıcı PE sensöründe yok** (yalnız tercih çiftlerinde), ve
**spillover skaler** (`CROSS_AXIS_SPILLOVER = 0.20`), brief domain-özgü
matris öneriyordu.

**L17 — Gen2'nin ilk kararı ata verisini kaçırıyor** (GAP-3).
`apply_inherited_somatic_scale` yalnız `delta_log` doluyken çalışıyor, ama
varisler **boş `delta_log` ile doğuyor** ⇒ miras alınan tehdit/kayıp
ölçeklemesi **gen2 olay 2'den itibaren** ölçülebilir, olay 1'de değil.
Gate **I5.4** bunu her koşumda raporluyor. Gen2 ikincillerini (S4, S5)
etkiliyor ve o ikinciller zaten L10 ile sınırlı. ⚠ D-045 bunu `null`
varisinin ikinci-yarı PE çöküşü için **mekanizma adayı** olarak da
işaretledi — doğrulanmadı, aday olarak duruyor.

---

## 9. Slotlar

Beşi 2026-08-11'de Yasin tarafından karara bağlandı. **İkisi açık** ve
kilidi onlar tutuyor.

### Kapananlar

| # | Slot | **Karar** | Gerekçe |
|---|---|---|---|
| **S1** | Sampling | **greedy** (`do_sample=False`, temperature 0.2) | D-026'nın reçetesi çürüdü — greedy 50 olayda `n_unique=27`, kapı 5, yani plato yok. Sampled %63 daha çok çift verir ama gürültü ekler; GAP-9 altında gürültü azaltmak çiftten değerli. Bu bir darboğaz elemesi, üretim değil |
| **S3** | α ve düzeltme | **α = 0.05, çift yönlü, düzeltme yok** | Tek birincil test var (§3). İkincillerde de düzeltme yok çünkü iddia edilmiyorlar — her ikincil sonucun yanında bu açıkça yazılır (§4) |
| **S5** | `DPO_EPOCHS` 1 → 3? | **1'de kalır** | Üç gerekçe: koşum süresi 3× artar (N=15'te 5 saat → 15 saat) · 47 çiftin **2 benzersiz `rejected`**'ı üstünde üç tur, GAP-18 altında ezberleme riski · ve D-029'un yakaladığı bastırma deseni (*"yüksek PE'liyi asla söyleme"*) tam olarak aşırı eğitimin failure mode'u. Sınadığımız şey eğitimi maksimize edip edemediğimiz değil, yaşanmışlığın aktarılıp aktarılmadığı. İlk ön-kayıtlı sonuçtan sonra yeniden açılabilir |
| **S6** | A4 — %10 somatik replay? | **girmez** | Kanalları karıştırır. Kanal 1 (sembolik kasa) malzemesi Kanal 2'nin eğitim setine girerse *"izi hangi kanal taşıdı"* sorusu cevapsız kalır — ve D-002'nin dört-halkalı nedensel zincir mantığı tam olarak o ayrıma dayanıyor. VRAM maliyeti olmaması (D-027) onu bedava yapıyor ama **ücretsiz olması dahil etmek için gerekçe değil** |
| **S7** | `events_gen1` / `gen2` / `k_gen2` | **50 / 20 / 3 — değişmez** | Değişirse ΔPE tabanı yine sıfırlanır ve D-043'ün regresyon değeri kaybolur |

### Son iki slot da kapandı

| # | Slot | Karar |
|---|---|---|
| **S2** | **N (seed sayısı)** | ✅ **N = 40**, seed 2004–2043, **iki batch** (2004–2023 · 2024–2043) — **D-052**. MDE (Wilcoxon, çift yönlü, α=0.05, güç 0.80) = **`d_z = 0.465`**. Bütçe 13.3 GPU saat. Batch'leme çökme maliyetini yarıya indiriyor ve **önceden ilan edildi**; batch'ler yapı gereği bağımsız (seed başına RNG kilidi + D-037 determinizm + D-042 konum bağımsızlığı). ⚠ Bir batch abort ederse **o batch** yeniden koşulur; sonuç seçmek için batch atılamaz |

| # | Slot | Karar |
|---|---|---|
| **S4** | En küçük anlamlı etki (`d_z`) | ✅ **SESOI ilan edilmiyor** (D-047). Bütçe-kısıtlı örneklem gerekçelendirmesi (Lakens 2022, *Sample Size Justification*, Collabra 8(1):33267) + ilan edilen duyarlılık analizi. Gerekçe: birinciliğimizin literatürde karşılığı olan bir etki yok ⇒ SESOI uydurmak bütçeyi şeffaf ilan etmekten **daha az** dürüst. `p > 0.05` ⇒ *"şu MDE'nin altında güçsüzüz, veri o bantta bilgisiz"*, asla *"etki yok"* |

**Güç tablosu** (eşleştirilmiş Wilcoxon, çift yönlü, α=0.05, güç 0.80):

| d_z | 0.2 | 0.3 | 0.4 | 0.5 | 0.8 | 1.0 | 1.5 |
|---|---|---|---|---|---|---|---|
| **gereken N** | 197 | 88 | 50 | 32 | 13 | 8 | 4 |

⚠ **N ≥ 6 matematiksel şart:** altında Wilcoxon çift yönlü α=0.05'te
reddedemez, etki ne kadar büyük olursa olsun.

Bütçe: seed başına ~20 dk + koşum başına ~7 dk (I4.1 replay).
N=10 ≈ 3.5 sa · N=15 ≈ 5.1 sa · N=20 ≈ 6.8 sa · N=32 ≈ 10.8 sa.

**S4 bu iki yoldan ikincisiyle dolduruldu** (D-047); birincisi reddedildi:

1. **Etkiden N'e.** *"Şu büyüklükten küçük bir etki bizi ilgilendirmez"*
   beyan edilir, N tablodan okunur. Literatür gerekçesi güçlendirir.
2. ✅ **Bütçeden etkiye — SEÇİLEN.** N bütçeden seçilir ve ön-kayıt
   **tespit edilebilir en küçük etkiyi ilan eder**. Bundan küçük etkiler için
   *"güçsüzdük"* denir, *"etki yok"* değil. Meşru, çünkü N veriden değil
   **bütçeden** geliyor (Lakens 2022).

⚠ **Yukarıdaki güç tablosu normal yaklaşımdır.** Exact noncentral-t ile
doğrulanan MDE'ler biraz daha büyük: N=20 → `d_z=0.660` · N=24 → `0.597` ·
**N=32 → `0.511`** · N=40 → `0.454` · N=50 → `0.404` (tek yönlü sırasıyla
0.577 · 0.523 · **0.449** · 0.400 · 0.357). **Ön-kayıta exact değer yazılır**,
tablodaki yaklaşık değer değil.

## 10. Sapma politikası

Kilitlendikten sonra bu belgeden herhangi bir sapma — parametre, test, N,
uç nokta, dışlama — **post-hoc**tur ve raporda öyle etiketlenir. Sapma
gerekirse: koşum durdurulur, D-kaydı açılır, yeni ön-kayıt yazılır, koşum
baştan başlar. Kısmi düzeltme yok.

## 11. Null sonuç politikası

Null meşru bilimsel çıktıdır ve gizlenmez (Değiştirilemez Süreç Kuralları).
Birincil test null çıkarsa rapor şunu ayırt etmek zorundadır:

- **Mekanizma null'ı** — kollar ayrışmadı, alet çalışıyordu (§5'in hepsi
  yeşil, kanal 2 faz-2 kararlarını değiştirdi).
- **Alet null'ı** — §5'ten biri düştü, veya kanal 2 kararları değiştirmedi.

Ayırt edilemiyorsa `INSTRUMENT_LIMITED_NULL` etiketiyle raporlanır ve
hangi halkanın koptuğu bilinmediği **açıkça** yazılır.

⚠ **S3 ve S4 için bu ayrım baştan biliniyor:** L9 gereği gen1'in ΔPE uç
noktası ayrımın %80–86'sını, L10 gereği gen2'nin `mean_pe`'si ayrımın
%73'ünü atıyor. Dolayısıyla o iki ikincilin null'ı **ölçüm duyarsızlığı**
olarak raporlanır, mekanizma yokluğu olarak değil. İkisi de **ölçüldü**,
varsayılmadı.

⚠ **S1 birincili desteklemez, ayrıştırır** (L11). Birincil anlamlı çıkarsa
raporda "S1 de anlamlı" cümlesi **ikinci bir kanıt olarak kurulmaz** — S1
birincilin girdi vektörünün desteğidir. Raporda birincilin ne kadarının
bayrak kümesi farkından, ne kadarının büyüklük farkından geldiği
**ayrıştırılarak** verilir.

---

## 12. Alet kimliği — 🔒 **DONDURULDU** (commit `befd72b4ee57`)

Aşağıdaki değerler **kilit anındaki `build_tool_identity()` çıktısıdır**,
elle yazılmadı. Koşumun kendi `tool_identity` bloğu bunlarla **birebir
eşleşmelidir**; eşleşmezse koşum bu ön-kaydın koşumu değildir.

**Koşum:** seed **2004–2043**, N=40, iki batch (2004–2023 · 2024–2043) ·
`--lora` · `events_gen1=50` · `events_gen2=20` · `k_gen2=3` ·
`pe_window = fazın tamamı` (`PE_WINDOW_EVENTS=0`, D-036).

| Alan | Değer |
|---|---|
| backend | `local` |
| model | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| quantization | 4-bit **NF4** + double_quant, compute dtype **fp16**, device_map `auto` |
| DPO | β=0.1 · **lr=1e-6** · epochs=1 · batch=1 · **grad_accum=4** (etkin 4) · max_seq=512 · max_grad_norm=1.0 |
| LoRA | rank=8 · alpha=16 · `dau_runs/adapters/{agent_id}/` |
| sampling | `do_sample=False` · temperature=0.2 · max_new_tokens=64 |
| polarite | kosinüs · MiniLM · bant `[0.25, 0.80]` · ⚠ **kalibre değil** |
| SNR marj | `0.15` · ⚠ **kalibre değil** |
| `MIN_PAIRS` | `4` (= batch × accum, D-046) · ⚠ **kalibre değil** |
| determinizm | `TORCH_DETERMINISTIC_WARN_ONLY=False` (D-037), I0.6 zorunlu kılıyor |
| sürümler | python 3.14.6 · torch 2.13.0 · transformers 5.14.1 · peft 0.20.0 · bitsandbytes 0.50.0 · accelerate 1.14.0 · numpy 2.4.5 · scipy 1.18.0 |
| değişmezler | **24 kapı** kodda (I0.1–I0.7 · I1.1/I1.3/I1.3b/I1.4/I1.5 · I2.1/I2.2 · I3.x · I4.1/I4.2 · I5.x) |

⚠ **`DAU_LORA_ENABLED` env'e güvenilmez** — koşum `--lora` bayrağıyla
başlatılır ve bayrak env ile tutarsızsa **I0.2 abort eder** (GAP-1).

<details><summary>Taslak anındaki hali (commit `4d26b31`) — tarihsel</summary>

- backend `local` · model `meta-llama/Meta-Llama-3.1-8B-Instruct`
- quantization NF4 + double_quant, compute dtype fp16
- DPO: β=0.1 · lr=1e-6 · epochs=1 · batch=1 · grad_accum=4 (etkin batch 4) ·
  max_seq=512 · max_grad_norm=1.0
- LoRA: rank=8 · alpha=16
- sampling: `do_sample=False` · temperature=0.2 · max_new_tokens=64
- polarite: kosinüs, MiniLM, bant `[0.25, 0.80]`, kalibre değil
- python 3.14.6 · torch 2.13.0 · transformers 5.14.1 · peft 0.20.0 ·
  bitsandbytes 0.50.0 · numpy 2.4.5 · scipy 1.18.0

</details>
