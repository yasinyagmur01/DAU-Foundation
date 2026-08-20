# ▶ YÜRÜTME KUYRUĞU — *"devam et"* denince buradan başlanır

**2026-08-19 · D-134 · tek otorite sıra.** Fazlar (`ROADMAP.md`) ve eski
borçlar **tek listede**, yapılma sırasına göre.

## Sözleşme

1. **"devam et"** = kuyruktaki **ilk ⬜ maddeyi** al, yap, ✅ işaretle,
   D-kaydı yaz, commit + push et.
2. Madde **⛔ KARAR** ile işaretliyse **Yasin'e sor**, kendin karar verme (D-007).
3. Her maddede *bitti sayılma ölçütü* yazılı — ona bakmadan ✅ işaretleme.
4. ⚠ **K1–K6** (`CLAUDE.md §2.4-b`) her maddede geçerli. GPU koşumu öncesi
   **K1 yazılmadan** koşum başlamaz, ve **K6**: kayda geçen kusur bir kapıya
   bağlanmadan madde ✅ işaretlenmez.
5. Sıra değiştirilecekse **gerekçesiyle** D-kaydına yazılır.

---

# FAZ 0 — GPU'suz, %100 taşınır (~3–4 sa)

## ✅ 0.1 · Eşleştirme rotasyondan türetilebiliyor mu? — **D-135, ve soru düştü**
⛔ **Cevap sorudan büyük çıktı:** ajan-ajan etkileşimi **özdeş ajanlarda simetriyi
kırmıyor** (gerçek fonksiyonlarla ölçüldü, sıfır GPU). Sosyal kuplaj bir
**çarpan**, kaynak değil ⇒ eşleştirme sabiti sorusu **anlamsızlaştı**.
⇒ **Faz 1 ve 0.4/0.5 İPTAL.** Ayrıntı D-135.

<details><summary>özgün madde</summary>

**Neden ilk:** cevabı, Yön 3'ün **yeni sabit gerektirip gerektirmediğini** ve
dolayısıyla bütün fazın maliyetini belirliyor.
**İş:** `run_convention_pilot.py:203` (`_pair_opponents`) ve popülasyon
koşucusundaki rotasyon (`ROTATE_ACT_ORDER`, D-104) okunur; aynı rotasyonun
eşleştirmeyi de tanımlayıp tanımlayamayacağı **hesapla** gösterilir.
**Bitti sayılır:** *"sıfır yeni sabit"* ya da *"şu N sabit gerekli"* cevabı
D-kaydında, aritmetiğiyle. **GPU yok. Kod değişmez.**
</details>

## ✅ 0.2 · Uç noktanın boyutunu geri kazan — **D-136**, ve teşhis değişti
✅ **Bitti:** PE satırı `affected_domain` + `axis_deltas` taşıyor; sonuç
dosyasında `delta_profile["axes"]` ve `to_landmark["axes"]`. Hesap değişmedi.
K2 ✅ · K3 ✅ · K5 ✅ (**6 mutasyon, 6 doğru test**, md5'li).

⭐ **Ölçüm borcu kapattı ama cevabı ters çevirdi:** `social`/`uncertainty`
**ölü değil** (max 0.200 / 0.171) — C2'nin *"sıfır kez"*i bir **argmax
artefaktı**. ⛔ **Ama dört sayı dört boyut değil:** spillover **tekdüze**
(`PE × 0.20`) ⇒ üç eksen birincilin **ölçekli kopyası**. Tek boyutluluğun
asıl sebebi argmax değil, **skaler spillover**.

⇒ ⛔ **GAP-10 tetiklendi (D-136 §6): asimetrik spillover matrisi.** Gerekçesi
ilk kez bir sayı, ve pencere hâlâ açık (üçüncü ön-kayıt kilitlenmedi).
**Karar Yasin'in** — sabit ailesi değişikliği (D-007, §2.7).

<details><summary>özgün madde</summary>

**Borç:** D-130 §9 — `z` dört alanlı görünüyor, **tek kullanılabilir boyutu
var** (`energy`, 216 okumanın 11'inde). `social`/`uncertainty` **sıfır kez**
yazıldı, çünkü `_primary_affected_domain` (`graph.py:842`) **en çok oynayan**
ekseni seçiyor ve enerji her olayda metabolizmayla oynuyor.
**İş:** dört eksenin büyüklüklerini de kaydet — argmax kazananının **yanına**,
yerine değil. Hesap **değişmez**.
**Bitti sayılır:** yeni alan sonuç dosyasında · **K2** (çok-ajanlı test) ·
**K3** (çağrı yeri testi) · **K5** (md5'li mutasyon, 4 mutasyon 4 doğru test).
</details>

## ✅ 0.2b · Birincil eksen `k` raporlansın — **D-138**
✅ PE satırı `target_domain` taşıyor; `delta_profile["axes"]["primary_axis"]`.
K2/K3/K5 ✅ (**7 mutasyon, 7 doğru test**). İlk okuma D-137 §2'yi **sonuç
dosyasından** yeniden üretti: `k` 8/8 `resource_load`, `social`/`uncertainty`
**0**. ⭐ Ve `k` ile argmax `wins` **ayrı şeyler** olduğu görüldü (hedef 8/8
`resource`, argmax 7/8 `energy`) ⇒ tek alanla raporlansaydı biri yanlış olurdu.

<details><summary>özgün madde</summary>
**Borç:** D-137 §9 — kaydın merkezî iddiası (*"`k` bütün olaylarda
`resource_load`"*) **stub koşumda** ölçüldü ve bugünkü aletle **gerçek koşumda
doğrulanamıyor**: `k` hiçbir yere yazılmıyor. `axis_deltas` (D-136) **sonucu**
kaydeder, birincil ekseni değil.
**İş:** `_pe_target_load_domain`'in döndürdüğü `target_domain` PE satırına
yazılsın; ajan satırında dağılımı özetlensin. Hesap **değişmez**.
**Bitti sayılır:** alan sonuç dosyasında · K2 · K3 · K5.
⚠ **Neden ucuz ama önemli:** D-137'nin yeniden açılma tetiği (§7) *"`k` ajanlar
arasında değişken hale gelirse"*. Tetiğin ateşlenip ateşlenmediğini görmenin
tek yolu `k`'yi kaydetmek.
</details>

## ✅ 0.3 · `precision_weight` raporlansın — **D-138**
✅ Ajan satırında **`precision`**: `n_distinct`/`min`/`max`/`mean` + PE_w
doygunluğu. Sayaçlar `_precision_audit_from_pe_rows`'tan **çağrılıyor**,
yeniden yazılmadı (§2.8). K2/K3/K5 ✅.

⭐ **L13 ilk kez çürütülebilir.** İlk okuma: `n_distinct = 2` — pilotun gördüğü
sayının **aynısı** ⇒ L13'ü **destekliyor**. ⚠ Ama *"tavanda takılı"* tarifi
**yanlışmış**: π `1.0`'da donmuş değil, **1.0 ↔ 1.2 arasında** oynuyor.
⛔ PE_w doygunluğu (%75) bu koşumdan **okunmaz** — stub kararlar ham PE'yi
sabit 1.000 yapıyor; gerçek koşumun sayısıdır.

<details><summary>özgün madde</summary>

**Borç:** L13 *"Precision-PE atıl"* — D-130 §10 ölçtü ki nicelik **sonuç
dosyasına hiç çıkmıyor**, yani iddia **ne doğrulanabiliyor ne çürütülebiliyor**.
**İş:** PE satırındaki `precision_weight` ajan satırına özetlensin (saf
raporlama, ~1 alan).
**Bitti sayılır:** alan dosyada · K3 · K5.
</details>

## ⛔ 0.4 · ~~Sosyal kablolama~~ — **İPTAL (D-135)**

<details><summary>iptal edilen madde</summary>

**İş:** popülasyon koşucusunda `opponent_id`, NPC yerine **başka bir popülasyon
ajanına** bağlanır (0.1'in verdiği eşleştirmeyle). Mekanizma `record_interaction`
ve `compute_social_load` — **ikisi de genel, kodda mevcut**.
⚠ **K1 zorunlu:** (a) hangi mekanizma varyans üretecek, (b) hangi bayrak onu
kapatır, (c) dejenere olmadığının **mevcut veriden** kanıtı — üçü de
koşumdan önce yazılır.
**Bitti sayılır:** mock prova geçti · K2/K3/K5 · K1 kaydı commit'li.
</details>

## ⛔ 0.5 · ~~Faz 1'in karar kuralı~~ — **İPTAL (D-135)**

<details><summary>iptal edilen madde</summary>

**Yasin'e sorulacak:** `null` kolunun *"değişkenleşti"* sayılması için eşik ne?
(öneri: `Var(F_agent) > 0` **ve** hasat yayılımı > 0, **her iki nesilde**).
⚠ Kural **koşumdan önce** commit edilir (D-125 deseni; sıra kanıttır).
</details>

---

# ⛔ FAZ 1 — **İPTAL (D-135)**

Sorusu GPU'suz cevaplandı: sosyal kuplaj `null`'ı değişken **yapmıyor**.

<details><summary>iptal edilen faz</summary>


## ⬜ 1.1 · Sosyal kuplaj koşumu
**Tek soru:** sosyal kuplaj `null` kolunu değişken yapıyor mu?
**Yapılandırma:** 1 taze tohum · N=8 · G=3 · 30 olay · `--lora` ·
**`--arms lived null`** (D-128'in dersi: **zayıf kol dahil**) · dış `timeout`
**yok** (D-126) · izleyici **PID ile** (pgrep kendi kabuğuyla eşleşiyor).
**Okunacak:** ⛔ **yalnız tanımlılık.** Kol farkı · kovaryans · etki
büyüklüğü **hesaplanmaz**.
**Bitti sayılır:** `run_quality=clean`, kapılar 6/6, ve 0.5'in kuralı
uygulanmış — sonucu ne olursa olsun.

## ⬜ 1.2 · ⛔ KARAR — yol ayrımı
`null` değişkenleşti ⇒ **Yön 3 kuruldu**, Faz 2'ye geç.
Değişkenleşmedi ⇒ **D-131 kalıcılaşır** (null betimleyici), Yön 2'ye dön.

---

</details>

# ✅ FAZ 0 BİTTİ (D-135 · D-136 · D-138) — sıradaki iş **FAZ 2**

⛔ **Ve Faz 2'nin önündeki ilk iki madde KARAR, kod değil.** İkisi de Yasin'in
(D-007) ve ikisi de §2.7'ye tabi: değer **etkiye bakılarak seçilemez**.

---

# ▶▶ SIRADAKİ İŞ — **2.4b · ⛔ KARAR (Yasin'in)** — sonda-3 dördüncü yola girdi

⛔ **"devam et" denince BU madde alınır, ama kendim karar veremem** (D-007).
Sonda koştu, üç sorunun üçü de ön-taahhüdün yazdığı gibi okundu (**D-155**),
ve sonuç D-154 §5'in **dördüncü yolu**: *"bu fizikle test edilemez"*.

## ⬜ 2.4b · ⛔ **KARAR** — kurucu neslin dejenerasyonu ne yapılacak

**Sondanın verdiği kanıt (D-155 §1):** gen1'in sekiz ajanı **iki kolda da bit
düzeyinde özdeş** (`pool_ratio_end = 0.757` ⇒ kıtlık gen1'de hiç ısırmıyor)
⇒ birinci Price geçişi **hangi uç nokta seçilirse seçilsin** `Var = 0`.
Uç nokta değiştirmek düzeltmiyor — sonda tam da bunu sınadı ve aday **girmedi**
(2/4, kural ≥3/4).

| | yol | bedeli | sondanın söylediği |
|---|---|---|---|
| **A** | **Yön 3'ü aç** — kıtlık rejimini değiştir (Holling II / kapasite, D-082/D-084) | bugünkü sayılar **taşınmaz**, ve §2.7 sınırında **bir sabit** kararı ister (`h` ya da kapasite) | ⭐ dejenerasyonun sebebine **doğrudan** dokunuyor |
| **B** ⭐ | **Kurucu nesli ölçümün dışında bırak** — Price yalnız gen ≥ 2 geçişlerinden okunur, G artırılır | koşum ~1.5 kat uzar; sıfır yeni sabit | gen2→gen3 hücrelerinin **ikisi de** `estimable=True` çıktı ⇒ varsayım bu koşumla **zaten sınanabilir** |
| **C** | **Kestirim damgasıyla devam** (P7-b / D-096) | ucuz | ⛔ D-145'in 3. kusuru **açık kalır**, uç nokta da düzelmedi |

⚠ **Claude Code'un önerisi: B önce ölçülsün, A onun yanında değerlendirilsin.**
Gerekçe D-155 §5'te. **Öneri, karar değil.**

**Bitti sayılır:** Yasin bir yol seçti, seçim D-kaydına gerekçesiyle yazıldı.

## ✅ 2.4 · Sonda-3 — **koştu, üç soru da okundu** (**D-155**)
✅ `dau_runs/probe3_endpoint_s9916.json` · `complete: true` ·
`run_quality=flagged` · **I4.1 identical** · **2 sa 09 dk 47 sn**
(⭐ süre tahmini ilk kez tuttu).

| # | ön-taahhüt | ölçülen | sonuç |
|---|---|---|---|
| **S1** | ≥3/4 hücrede `Var(to_landmark.max) > 0` | **2/4** (düşen ikisi **gen1**, iki kolda da) | ⛔ **aday GİRMEZ** — kapanmış soru |
| **S2** | `I5.4` geçer, ≥1 varis somatik ölçek | **0 / 32** varis · `never applied (skipped=1563)` | ⛔ **D-152 vaadini tutmadı** |
| **S3** | `I4.2` FLAG basar | FLAG bastı (`gen3: 2 states`) | ✅ öncül doğru ⇒ **ABORT'a yükseltilmiyor** |

⭐ **Retin deseni retten önemli:** aynı `Var = 0` deseni **bugünkü uç noktada
da** var (`z_variance`, gen1→gen2, iki kol) ⇒ kusur uç noktada değil **fizikte**.
⭐ **D-152'nin hangi yarısı tuttu ölçüldü:** göreli bant **çalışıyor** (48
yaşamın 10'u `low`, 15'i `high`), `low` bant **üreyebiliyor** da (w = 3/1/1) —
kırılma **bandın arkasında** (⇒ 2.5).

<details><summary>özgün madde (ön-taahhüt, koşumdan önce commit'li)</summary>

| # | soru | ön-taahhüt edilmiş okuma kuralı |
|---|---|---|
| **S1** | Sürekli uç nokta (`to_landmark.max`) taze veride tanımlı mı? | **4 hücrenin ≥ 3'ünde** `Var > 0` ⇒ **girer**, aksi hâlde **girmez** |
| **S2** | `I5.4` geçiyor mu (D-152 somatik kanalı canlandırdı mı)? | **Tahmin: geçer**, ≥1 varis `has_somatic_scale`. **Sıfır ⇒ D-152 vaadini tutmadı** |
| **S3** | `I4.2` ne diyor (kollar aynı RNG durumundan mı giriyor)? | **Tahmin: FLAG basar.** **Geçerse** öncül yanlıştı ⇒ ABORT'a yükseltilir |

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9916 --n-agents 8 --n-generations 3 --events 30 \
  --lora --fresh-pasture --arms lived shuffle \
  --results dau_runs/probe3_endpoint_s9916.json
```
</details>

## ⬜ 2.5 · Somatik zincirin **kırıldığı halka** ölçülsün (K6, D-155 §6)

**Borç:** D-155 §2 dört halkanın **üçünün çalıştığını** ölçtü (göreli bant ·
travma eşiği 48/48 · `low` bant üreyebiliyor), ama varis **0/32**
`inherited_warning` alıyor. Kalan şüpheli `select_for_transfer`
(`generation.py:175–183`) üçlü şartının son iki bileşeni:
`recall_count ≥ GENERATION_MIN_RECALL` ve `is_trauma(candidate.record)`.
⛔ **Bugünkü hâli çıkarım, ölçüm değil** — sonuç dosyası `recall_count`
taşımıyor.

**İş:** saf raporlama — `select_for_transfer`'a giren adaylardan kaçının
recall kapısında, kaçının `is_trauma` kapısında, kaçının bant kapısında
düştüğü sayılsın ve ajan satırına yazılsın. **Hesap değişmez.**
**Bitti sayılır:** üç sayaç sonuç dosyasında · **K2** · **K3** · **K5**.
⚠ §2.11: `n_at_or_above_trauma` (PE-delta) ile `is_trauma(record)` (anı
imprint sınıfı) **ayrı niceliklerdir**; sayaç ikisini karıştırmamalı.

## ⬜ 2.6 · Kurucu neslin dejenerasyonu bir **kapıya** bağlansın (K6, D-155 §6)

**Borç:** D-155 §1 ölçtü ki gen1'in 8 ajanı iki kolda da özdeş ⇒ birinci Price
geçişi yapısal olarak `Var = 0`. **Bugün bunu yakalayan kapı yok** —
`selection_estimable` alan başına yazılıyor ama *"kurucu nesil dejenere"*
diye bir bayrak yok, ve C2 bu durumu **`clean`** raporlamıştı (D-149 deseni).

**İş:** yeni bir preflight maddesi (**FLAG**) — bir nesil geçişinde ebeveyn
kümesinin `F_agent` **ve** uç nokta yayılımı ikisi birden sıfırsa bayrak.
⚠ **Eşik yok, sabit yok:** koşul `Var == 0` (`Z_VARIANCE_EPSILON` zaten var).
**Bitti sayılır:** kapı `invariants` sözlüğünde · bu koşumun dosyasında
**geriye dönük** ateşlendiği gösterildi · K2 · K3 · K5.
⚠ **2.4b'nin kararından bağımsız** — hangi yol seçilirse seçilsin kapı gerekli.

---

# FAZ 2 — üçüncü ön-kayıt (GPU'suz)

## ✅ 2.0 · Travma eşiği — **D-143: eşik DEĞİŞMİYOR, `P_active` eş-birincil**
⚠ **Yetki devredildi** (Yasin, 2026-08-19: *"önerdiğin yolla kararları al"*).

⛔ **Üç seçenek de kapalı çıktı:** **(a)** eşiği indir — dağılımı **zaten
gördük** (§2.7), ve sabitlerden türetilebilecek tek eşitsizlik **bağlamıyor**
(`M(1.0) = 0.8200 ≥ 0.70` zaten sağlanıyor) · **(b)** formülü değiştir — fizik
değişir · **(c)** eşik-öncesi uç nokta — ⛔ **zaten ön-taahhüt edilmiş,
ölçülmüş, reddedilmiş** (D-125/128/129, **2/4**).

✅ **Seçilen (d): eşiği düzeltme, geçilme oranını ÖLÇ.** `P_active`
(`Var(z) > 0` hücre oranı) **eş-birincil**, `Cov_cond` yalnız aktif hücrelerde.
**Sıfır yeni sabit · sıfır fizik değişikliği · sıfır ön-taahhüt ihlali.**
⚠ `P_active` **ön-eleme değil, sonuçtur** (U10). ⚠ Ve bu karar uç noktayı
**güçlü** yapmıyor, **dürüst** yapıyor — aktif oran ~%22, güç 2.2'de ilan
edilecek.

⏸ **`to_landmark.max` yeniden açılabilir** ama **üç şart birden**: yeni
ön-taahhüt · sonda **`shuffle` içerir** (D-129'unki `lived null`'dı) · kural
**taze veriye** uygulanır.

## ✅ 2.0b · Rice yanlılığı ölçüldü — **D-142**, ve tehlike başka yerde çıktı
✅ **GPU'suz, gerçek fonksiyonlarla** (`allocate_heirs` + `price_partition`
çağrıldı, yeniden yazılmadı). N=8, turnuva k=2, R=20 000.

⭐ **Sonuç 1 — işaretli kestirimci null'da yansız.** β=0'da
`E[Cov] = 0.000372`, `SE = 0.000419` ⇒ **0.89 SE**, sıfırdan ayırt edilemiyor.
Oran β≥0.5'te **1.01–1.05** ⇒ çarpansal büyütme de yok. Eşli null
`E[ΔCov] = −0.000603` (**−1.02 SE**).
⇒ **DR'nin U7'si olmayan bir sorunu çözüyor** — iptal edilecek yanlılık yok.

⭐⭐ **Sonuç 2 — asıl tehlike magnitude kanalında, DR bunu görmedi.** Null'da
`E[|Cov|] = 0.046` (**sıfır değil**), ve gerçek fark 0.0355 iken `|Cov|` farkı
yalnız 0.0073 ⇒ **4.86 kat sıkışma**. ✅ Bugün temiziz (her yer işaretli), ⚠ ama
**korunması gereken bir özellik** ⇒ ön-kayıta sınır olarak yazılacak.

## ✅ 2.1 · **CEVAPLANDI — DR #12 / D-140**
⭐⭐ **Q1 indirgemeyle cevaplandı, yeni istatistik gerekmiyor:** kovaryansı
tohum başına bir skalere indir — `ΔCov = Cov_lived(w,z) − Cov_shuffle(w,z)` —
sonra tohumlar arası **Cohen's `d_z`**. Bu noktadan sonra D-052'nin makinesi
(Lakens 2022, bütçe-kısıtlı N + duyarlılık analizi) **olduğu gibi** çalışıyor.
⇒ Geriye kalan **tohum sayısı**, ve o **bütçeden** seçilir.

⭐ **Turun üç kazancı daha:** tekrarlama birimi **tohum** (Lazic 2010,
pseudoreplication — 8 ajan alt-örneklem, G=2 geçiş bağımlı) · eşikli uç nokta
için **iki aşamalı yapı** (`P_active` + `Cov_cond`, ve `P_active`
**eş-birincil**) · **boşluk ilanı:** Price + güç analizi birleşimi literatürde
**yok**, sentez ilan edilerek yapılacak.

✅ **U6 karara bağlandı (Yasin, D-141): ikisi birden.** Ortalama **test eder**
(pseudoreplication kısıtı karşılanır), nesil satırları **raporlamada kalır**
(D-132'nin sönüm sorusu açık kalır). Biri istatistik, öteki betimleme.

## ✅ 2.1b · Kapılar bağlandı — **D-149**, ve I5.4 anında bir kusur buldu
✅ **`I4.2`** (FLAG — ölçüm için, gerekçesi ön-kayıt §5.1'de) ve **`I5.4`**
(FLAG) bağlandı. Kapı sayısı **6 → 8**; kalan **18** ilan edildi.

⛔⛔ **I5.4 bağlandığı anda ölçtü:** C2'de 144 varisin **0'ında** somatik ölçek,
**0'ında** miras uyarısı — buna karşılık **anılar geçmiş** (~10/varis) ve
**adapter geçmiş** (96/144). ⇒ **Kanal 1'in engram yarısı çalışıyor, somatik
yarısı çalışmıyor** (GAP-3). ⚠ Ve C2 bunu **`clean`** diye raporlamıştı,
çünkü kapı bağlı değildi.

✅ **GAP-3 kısmen kapandı (D-152):** fitness bantları **göreli** yapıldı, eşik
**değeri değişmeden**. İki ölü bant canlandı ⇒ miras uyarısı dalı
**ulaşılabilir**. ⚠ **Tam kapanmadı** — zincirin geri kalanı `is_trauma`
eşiğine bağlı; darboğaz **bir adım ileri taşındı**, I5.4 koşumda ölçecek.

## 🔴 2.2 · Ön-kayıt taslağı — **D-145: KİLİTLENEMEZ, dört kusur bulundu**
📝 `docs/PREREGISTRATION_3.md` yazıldı (D-144), ⛔ **kilit öncesi denetim
durdurdu** (D-145, Yasin'in talebiyle).

| # | kusur |
|---|---|
| 1 | Birincil alan `energy` C2'de **15 hücrenin 1'inde** ölçülebilirdi |
| 2 | ⛔⛔ Alan **kola değil TOHUMA** bağlı: kriz → `resource`, kriz yok → `energy` ⇒ sabit alan tohumların bir kısmını **tamamen** atar |
| 3 | ⛔⛔ `ΔP_active` sıfır-şişkin; Wilcoxon sıfırları atar ⇒ **S=12'de reddedebilme ihtimali %6.6** (güç değil, **mümkün olma**) |
| 4 | Bir kol-tohumun **hiç** Price satırı olmayabilir (`null` s9912: 0/2) |

⛔ **KARAR Yasin'in (D-145 §7):** **A** ⭐ kestirim koşumu S=12, 24 sa,
**hipotez testi yok** (P7-b/D-096 damgası) · **B** test koşumu S ≥ 30,
**60 sa** (aralık 40–91) · **C** uç noktayı düzelt — ⛔ **§2.7 yasaklıyor**.
**Öneri A.**

## ⬜ 2.3 · Kilit
Slotlar kapanınca 🔒, commit hash, alet kimliği dondurulur (§12 deseni).

---

# FAZ 3 — tek pahalı koşum

## ⬜ 3.1 · Doğrulayıcı koşum
Nihai fizikle, 2.1'in verdiği tohum sayısıyla. Checkpoint sayesinde
**gözetimsiz** koşar. ⚠ Maliyet **tohum başına ~2 sa** (ölçüldü; nişler arası
yayılım **2.3 kat** — tek sayı değil **aralık** verilir, K4).

## ⬜ 3.2 · Analiz ve sonuç sınıfı
`analyze_population_run` ile dört seviye · sonuç sınıfı **koşumdan önce**
tanımlı (alet null'ı / evren null'ı / etki null'ı / pozitif).

---

# ⏸ ERTELENMİŞ BORÇLAR — sırası gelmedi, unutulmadı

| borç | neden ertelendi | tetiği |
|---|---|---|
| **GAP-4 ikinci yarısı** — Ebbinghaus **hangi** anıyı siliyor, silinenin LoRA'daki izi kalıyor mu | D-130 yalnız **sayıyı** ölçtü (null 14.4 anı alıyor ve yine klon); **içerik** ölçülmedi | koşum sırasında ek aletleme gerekir ⇒ Faz 2'de ön-kayıta yazılırsa Faz 3'te ölçülür |
| **LoP mu yakınsama mı** — adapter sönümü (6/6 dizide 1.8×–4.8×) | ayırt etmek için **güncelleme büyüklüğü değil öğrenme sonucu** ölçülmeli (D-132) | Faz 3'ün aletlemesi |
| **GAP-3** — gen2 ilk olayda somatik ölçek boşluğu | gen2 yaşamları kısaldığı için payı büyüdü | ⏸ üçüncü ön-kayıt |
| **GAP-18 / KTO** | `uniq_rejected` 100/94 ölçüldü, karar verilmedi | ⏸ üçüncü ön-kayıt |
| **`fitness_class` `high` bandı boş** · **`landmark_energy` doygunluğu** | ön-kayıt kararı, kod değil | ⏸ üçüncü ön-kayıt |
| **GAP-10 / spillover** | ✅ **D-137: ölçüldü, skaler kalıyor, sınır ilan edildi.** Matris `k` sabit olduğu için skalerin üç kopyalı hâli olurdu (192/192) ve eşiği de geçirmiyordu (+%2.29) | ⏸ **yeniden açılır:** `k` ajanlar **arasında** değişken hale geldiği gün (D-137 §7) |
| **GAP-10 / `W_SEM = 0.0`** · **negation sarmalayıcı** | ikisi de L8'de sınır, spillover'dan **bağımsız** ve daha ucuz; ölçülmediler | ⏸ üçüncü ön-kayıt |
| **Belge borcu** — master ref §6/§19 consolidation anlatısı | mekanik değil, karar gerektiriyor | ⏸ |
| **Magic number kalıntıları** — `time.sleep(10)`, bare `0.5`, `k: int = 5` | **Cursor'a uygun** | ⏸ |
| **Yöntem makalesi** | Faz 1'in sonucundan bağımsız yazılabilir | ⏸ Yasin'in kararı |

---

# ⚠ Yeni oturumun bilmesi gereken

1. **K1–K5 bağlayıcı** (`CLAUDE.md §2.4-b`) — hepsi bu oturumda **gerçekleşen**
   hatalardan türedi.
2. **Popülasyon koşucusu:** `dau/diagnostics/run_population_experiment.py`.
   `run_cprime_multigen.py` **değişmedi** (B2'nin yolu).
3. **Zorunlu:** `PYTHONHASHSEED=0` · `--lora/--no-lora` · `--pasture-carryover/--fresh-pasture`.
   `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez** (D-116).
4. ⛔ **Bir sayıya bakıp cümle kurmadan önce hangi mekanizmanın onu ürettiğini
   sor.** Bu oturumda beş okuma bu yüzden çürüdü.
5. **Kullanılmış tohumlar:** …9901–9904 (C2 öncesi) · **9911–9913** (C2) ·
   **9915** (sonda-2) · 9305–9310 (mock). Taze blok: **9916+**.
   ⚠ **9916 sonda-3'te HARCANDI** (D-155) ⇒ deneyin tohumları **9917+**.
6. ⭐ **K6 (yeni, D-151):** kayda geçen kusur **bir kapıya bağlanmadıkça**
   kapanmamıştır. Bir madde bir mekanizmanın çalışmadığını ölçtüyse, ✅
   işaretlenmeden önce ya bir preflight kapısına ya da kuyruğa bağlanır.
7. ⚠ **`K`-serisi çakışması** (D-153): işaretsiz `K5` **çalışma kontrolüdür**
   (`CLAUDE.md §2.4-b`); ikinci ön-kaydın kilit kararına atıf **"kilit K5"**
   diye yazılır.
8. ⛔ **Ön-kayıt (`PREREGISTRATION_3.md`) KİLİTLENEMEZ durumda** — D-145'in
   dört kusuru duruyor, ve 3.'sü (uç noktanın yapısal test edilemezliği)
   **sonda-3'te cevaplandı: düzelmedi** (D-155). Sürekli uç nokta adayı
   **girmedi** (2/4), ve sebep uç noktada değil **kurucu neslin
   dejenerasyonunda** ⇒ kilit **2.4b kararına** bağlı.
