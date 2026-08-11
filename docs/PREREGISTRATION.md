# Çok-Nesilli C′ — Ön-Kayıt (Pre-Registration)

**Durum: TASLAK — KİLİTLİ DEĞİL.** Açık slotlar (§9) doldurulup Yasin
onayladığında bu satır `KİLİTLİ · <tarih> · <commit>` ile değiştirilir. O andan
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
| S1 | Doğum-drift **kategorik** kanalı: varisin bayraklanan alan kümesi | Fisher-Freeman-Halton, kol × profil |
| S2 | Doğum-drift **sayım** kanalı: `n_transfer_candidates`, `n_inherited_warnings` | Kruskal-Wallis (⚠ §8-L1: bu kanalın atıl olması bekleniyor) |
| S3 | Faz-1 ΔPE (fazın tamamı, D-036) | eşleştirilmiş Wilcoxon, `lived−shuffle` |
| S4 | Gen2 ortalama PE | eşleştirilmiş Wilcoxon |
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

**L8 — `W_SEM = 0.0`.** ChromaDB vektör benzerliği anı skorlamasına
girmiyor (GAP-10). Anı seçimi şu an semantik değil.

---

## 9. Açık slotlar — kilitlemeden önce doldurulacak

| # | Slot | Seçenekler / not | Kim |
|---|---|---|---|
| **S1** | **Sampling: greedy mi sampled mı** | D-026'da açık kaldı. Greedy 50 olayda `n_unique=27` (kapı 5) ⇒ reçetenin "greedy plato yapar" gerekçesi çürüdü. Sampled %63 daha çok çift veriyor ama gürültü ekler. **Claude Code'un görüşü: greedy** — GAP-9 altında gürültü azaltmak, çift sayısından değerli. | Yasin |
| **S2** | **N (seed sayısı)** | Bütçe: kol başına ~7 dk, seed başına ~20 dk. N=10 → ~3.3 sa · N=15 → ~5 sa · N=20 → ~6.7 sa · N=30 → ~10 sa. Wilcoxon çift yönlü α=0.05'te **N≥6 şart** (altında matematiksel olarak reddedemez). Güç tablosu: d_z=0.5 → 32 · 0.8 → 13 · 1.0 → 8. ⚠ Bu tablodan N seçmek için **önce en küçük anlamlı etki** (S4) beyan edilmeli. | Yasin |
| **S3** | **α ve düzeltme** | Tek birincil test ⇒ düzeltme gereksiz. Öneri: α=0.05 çift yönlü. | Yasin |
| **S4** | **En küçük anlamlı etki (d_z)** | N'i buradan hesaplarız. **Gözlenen d'den seçilemez** (§2.7, post-hoc tuning). Literatürden veya "bu büyüklükten küçük bir etki bizi ilgilendirmez" beyanıyla gelmeli. | Yasin (DR girdi verebilir) |
| **S5** | **A3: `DPO_EPOCHS` 1 → 3?** | Ertelenmişti (GAP-8). Kilitlenirse koşum süresi ~3× artar. | Yasin |
| **S6** | **A4: %10 somatik replay?** | D-027 VRAM bütçesinden çıkardı (batch=1'de maliyeti yok). Deney tasarımı kararı, aksiyoma değiyor. | Yasin |
| **S7** | **`events_gen1` / `events_gen2` / `k_gen2`** | Şu ana kadar 50 / 20 / 3 koşuldu. Değişirse ΔPE tabanı yine sıfırlanır. Öneri: **değiştirme**. | Yasin |

---

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
