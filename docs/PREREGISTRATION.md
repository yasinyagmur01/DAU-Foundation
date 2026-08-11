# Çok-Nesilli C′ — Ön-Kayıt (Pre-Registration)

**Durum: TASLAK — KİLİTLİ DEĞİL.** Beş slot kapandı (2026-08-11); **S4 ve
S2 açık**. Doldurulup Yasin bu satır `KİLİTLİ · <tarih> · <commit>` ile değiştirilir. O andan
itibaren bu belgedeki hiçbir madde değişmez; değişiklik gerekirse yeni bir
ön-kayıt açılır ve bu belge süperseded işaretlenir.

**Kilitlenene kadar:** alet değişikliği hâlâ meşru (CLAUDE.md §2.10), ama her
biri kendi D-kaydını ister.

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

**L8 — `W_SEM = 0.0`.** ChromaDB vektör benzerliği anı skorlamasına
girmiyor (GAP-10). Anı seçimi şu an semantik değil.

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

### Açık — kilidi bunlar tutuyor

| # | Slot | Durum |
|---|---|---|
| **S4** | **En küçük anlamlı etki (`d_z`)** | ⏸ Beyan bekliyor. **Gözlenen d_z'den seçilemez** — D-043'te `lived−null` 0.87, `lived−shuffle` 0.39 ölçüldü ve ikisi de n=3'ten geliyor; birini hedef yapmak §2.7'nin yasakladığı post-hoc tuning olur |
| **S2** | **N (seed sayısı)** | ⏸ S4'ün fonksiyonu |

**Güç tablosu** (eşleştirilmiş Wilcoxon, çift yönlü, α=0.05, güç 0.80):

| d_z | 0.2 | 0.3 | 0.4 | 0.5 | 0.8 | 1.0 | 1.5 |
|---|---|---|---|---|---|---|---|
| **gereken N** | 197 | 88 | 50 | 32 | 13 | 8 | 4 |

⚠ **N ≥ 6 matematiksel şart:** altında Wilcoxon çift yönlü α=0.05'te
reddedemez, etki ne kadar büyük olursa olsun.

Bütçe: seed başına ~20 dk + koşum başına ~7 dk (I4.1 replay).
N=10 ≈ 3.5 sa · N=15 ≈ 5.1 sa · N=20 ≈ 6.8 sa · N=32 ≈ 10.8 sa.

**S4'ü doldurmanın iki meşru yolu var** — ikisi de post-hoc değil:

1. **Etkiden N'e.** *"Şu büyüklükten küçük bir etki bizi ilgilendirmez"*
   beyan edilir, N tablodan okunur. Literatür gerekçesi güçlendirir.
2. **Bütçeden etkiye.** N bütçeden seçilir (ör. *"N=20 karşılayabiliriz"*),
   ve ön-kayıt **tespit edilebilir en küçük etkiyi ilan eder** (N=20 →
   d_z ≈ 0.66). Bundan küçük etkiler için *"güçsüzdük"* denir, *"etki yok"*
   değil. Bu da meşrudur çünkü N veriden değil **bütçeden** geliyor.

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

## 12. Alet kimliği (kilitte dondurulacak)

Kilit anında bu bölüm o commit'in `tool_identity` çıktısıyla doldurulur.
Taslak anındaki hali (commit `4d26b31`):

- backend `local` · model `meta-llama/Meta-Llama-3.1-8B-Instruct`
- quantization NF4 + double_quant, compute dtype fp16
- DPO: β=0.1 · lr=1e-6 · epochs=1 · batch=1 · grad_accum=4 (etkin batch 4) ·
  max_seq=512 · max_grad_norm=1.0
- LoRA: rank=8 · alpha=16
- sampling: `do_sample=False` · temperature=0.2 · max_new_tokens=64
- polarite: kosinüs, MiniLM, bant `[0.25, 0.80]`, kalibre değil
- python 3.14.6 · torch 2.13.0 · transformers 5.14.1 · peft 0.20.0 ·
  bitsandbytes 0.50.0 · numpy 2.4.5 · scipy 1.18.0
