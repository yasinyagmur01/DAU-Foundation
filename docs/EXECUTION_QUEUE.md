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

# SIRADAKİ İŞ — ⛔ **3.0d · KARAR: hangi kaldıraç** (GPU yok, karar)

⚠️ **3.0 bitti (D-164) · 3.0b verilemedi (D-165) · 3.0c koştu (D-168) — ve
3.0c, 3.0b'nin gerekçesini ÇÜRÜTTÜ.** D-165'in *"boş küme"*si hatalı bir
başlangıç varsayımından geliyormuş; havuz `POOL_INIT`'ten değil **tohumun
nişinden** başlıyor (0.40–1.00). ⇒ Mekanizma **çalışıyor**, ama **tohuma
bağlı**.

## İşaretler
✅ iyi haber · ❌ kötü haber · ⚠️ uyarı/sınır · **KARAR** senin ·
*(bitti)* iş tamamlandı, sonucu iyi de olabilir kötü de.
⚠️ Aşağıdaki eski maddelerde eski işaretler (⛔ ⭐ 🔒) hâlâ duruyor.

## ✅ 3.0 · Katman 1 pilotu — tavan işe yaradı mı *(bitti — sonucu karışık)*

⚠️ **Tam talimat `CLAUDE.md` §1'de** (*"devam et" = KATMAN 1 PİLOTU*) — komut, üç kural, koşum sonrası adımlar ve tehlikeler orada tek blokta.
Aşağısı özettir; **çelişki olursa `CLAUDE.md` geçerlidir** (D-001).

**Ön-taahhüt D-162 §5'te commit'li** (P1'in eşiği D-163 §7'de güncellendi).

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9920 9921 9922 --n-agents 8 --n-generations 4 --events 30 \
  --lora --fresh-pasture --arms lived shuffle \
  --results dau_runs/layer1_pilot_g4_s9920_9922.json
```

⚠️ Dış `timeout` **YOK** (D-126) · `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez**
(D-116) · tohumlar **taze** (kullanılmışlar …9919).

| kural | ne sorar |
|---|---|
| **P1** | Kıtlık kademeli mi oldu? 3 tohumun **≥2'sinde** ilk eksik alma **olay ≤ 8** |
| **P2** | Kurucular ayrışıyor mu? **6 kurucu hücrenin ≥4'ünde** `Var(F_agent) > 0` ⚠️ bugünkü taban **8'de 2** |
| **P3** | Zincirin geri kalanı kendiliğinden oynadı mı? ⚠️ **EŞİKSİZ, betimleyici** |

⛔ **Okunmayacaklar (L9):** kovaryans · işaret · kol farkı · etki büyüklüğü ·
`ΔP_active`.

**Bitti sayılır:** koşum `complete`, üç kural da D-kaydında **yazıldığı gibi**
okundu, ve `I5.6` verdict'i raporlandı.

### ✅ *(bitti — 2026-08-21, D-164)* · sonucu: **P2 tuttu, P1 tutmadı**

Bitti ölçütünün üçü de karşılandı: koşum `complete` (8 sa 3 dk, çökme yok),
üç kural **gevşetilmeden** okundu, `I5.6` raporlandı (**bayrak**: s9922'nin
5 nesil hücresinde tavan hiç bağlamadı).

| kural | sonuç |
|---|---|
| **P1** | ❌ **1/3** (ölçüt ≥2/3) — s9921 olay 2 · s9920 olay 9 · s9922 hiç |
| **P2** | ✅ **4/6** (ölçüt ≥4) ⚠️ gen1'de kollar özdeş ⇒ fiilen 2/3 tohum |
| **P3** | `k` **192/192 sabit** · tanımlılık **11/17** · `cooperate` ve `null` ⛔ **okunamadı** |

⛔ **Teşhis (D-164 §4):** kriz kanalı **0/192** öldü (sabitin seçilme
gerekçesiydi) · tavan kanonik DEFECT'i ancak oran < 0.561'de bağlıyor, havuz
0.60–0.86'da oturuyor · eksik almaların çoğu havuzdan değil **ilandan**
(`EXTRACTION_PARSE_MAX = 25`) · D-163'ün **denge noktası hiç kurulmadı**.

⇒ **Açtığı iş: 3.0b (aşağıda).**

---

## ❌ 3.0b · ~~KARAR: `EXTRACTION_LIMIT_RATIO`~~ — **VERİLEMEDİ (D-165)**

⛔ **Bant BOŞ ÇIKTI.** Bandın sınanmamış ikinci şartı (*tavan landmark'tan önce
bağlamalı*, D-084/D-163 §4) uygulanınca:

```
landmark'tan ÖNCE bağlasın     ⇒  r ≤ 0.06271
kriz rejimi erişilebilir olsun ⇒  r >  0.10500
```
**Arada 1.67 kat, örtüşme yok ⇒ seçilecek `r` yok.**

⭐ **Asıl değişken `r` değil TALEP:** kritik talep **`D* = 6.078`**.
`D > D*` ise bant dolu, `D < D*` ise hiçbir `r` çalışmaz. Pilot talebi
**aralık** olarak bıraktı (`[4.438, 6.578]`) ve **`D*` aralığın içinde** ⇒
karar **verilebilir değil**, sabit **değiştirilmedi**.

⇒ **Açtığı iş: 3.0c.** Karar, ölçümden sonra **kaldıraç seçimi** olarak geri
gelecek (talep · `POOL_INIT` · Katman 2) — üçü de **senin** (D-007).

---

## ✅ 3.0c · Talep ölçüm koşumu *(bitti — D-168, ve D-165'i çürüttü)*

**Alet:** D-166 — pool satırı artık karar sınıfını (`outcome`) da taşıyor;
nesil kaydında `demand` ve `demand_to_landmark` (mean · median · p90 · max +
`outcomes` histogramı).

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9923 9924 9925 --n-agents 8 --n-generations 2 --events 30 \
  --lora --fresh-pasture --arms lived \
  --results dau_runs/demand_probe_g2_s9923_9925.json
```

| kural | ne sorar |
|---|---|
| **M1** *(bağlayıcı)* | gen1'de `demand_to_landmark.requested_mean`, 3 tohumun **≥2'sinde > 6.078** mü? |
| **M2** *(eşiksiz)* | `outcomes` histogramı — D-164'ün P3'ünde **okunamayan** `cooperate` sayısı |
| **M3** *(eşiksiz)* | `median` · `p90` · `max` — talebin ne kadarı ayrıştırılmış büyük ilanlardan |

⛔ **`D* = 6.078` D-165'te sabitlendi, koşuma bakılarak değişmez.**
⛔ **Koşumdan sonra hiçbir sabit değişmeyecek** — sonraki adım bir karardır.

**Bitti sayılır:** koşum `complete`, M1/M2/M3 **yazıldığı gibi** okundu ve
**D-168** yazıldı.

### ✅ *(bitti — 2026-08-22, D-168)*

Koşum `complete`, **2 sa 9 dk**, kapı **9/10**, ⭐ **`I5.6` GEÇTİ**.

| kural | sonuç |
|---|---|
| **M1** | ❌ **1/3** (7.325 · 5.125 · 5.450 vs eşik 6.078) — ⛔ **ama eşik geçersiz**, hatalı cebirden geldi |
| **M2** | ⭐ `cooperate` **523/1190 = %43.9** — karar kanalı işliyor |
| **M3** | landmark'ta talep iki değerli (8.0 / 2.0), `25.0` ilanlar **geç yaşam** olgusu |

⛔ **D-165'in *"BOŞ KÜME"*si geri çekildi.** Düzeltilmiş bant: 9923 bandın
tamamı · 9924 boş · 9925 ince şerit ⇒ ortak şerit `r ∈ (0.1050, 0.1085)`,
⚠️ genişlik 0.0035, **kırılgan**.

⭐⭐ **Baskın değişken bulundu:** başlangıç nişi.
`0.577 → olay 2` · `0.605 → 3` · `0.620 → 3` · `0.794 → 5` · `0.825 → hiç` ·
`0.877 → 9`. ⚠️ Kriz kanalı hâlâ **0/48**.

## ✅ 3.0e · DR #13 mutabakatı + `I5.1` bağlandı — **D-169 · D-170**

✅ **D-169:** v3.0 mimari raporu mutabakata bağlandı, **koddan hiçbir değişiklik
çıkmadı.** Taşıyıcı iddia cebirsel olarak ters (`L = ln 2` ⟺ marj **sıfır**;
doygunlukta `L → 0`). Ölçüldü: 64 eğitim çağrısı, **28/64 `ln 2`'nin üstünde**
(= negatif marj) · eğitim başına **1–7 optimizer adımı** ⇒ bu veriden teşhis
konulamaz. **EGI** ⛔ Yasak #1 · **SVC** ⛔ kilit K7 · **CKE** ⛔ L9 ·
**LoRA-FA/TIES** ⏸ üçüncü ön-kayıt · **RCI** ✅ alındı, **fizik kararından sonra**.
Tam tablo: `docs/research/RECONCILIATION.md` **§V**.

✅ **D-170:** `I5.1` popülasyon kapılarına bağlandı — **tanımlıydı, bağlı
değildi** (D-149'un tekrarı). Kapı **11**, suite **644**. Mutasyon 4/4.

⛔ **Verdict YOK:** mock'un sıfır kenarı gerçek koşum hakkında kanıt değil
(kenarlar yalnız DEEP/TRAUMA düğümlerinden doğuyor, stub onları üretmiyor),
ve gerçek sayı diskte de yok. **Bir sonraki gerçek koşumda okunacak.**

⏸ **Açılan borç:** konsolidasyon telemetrisi (`edges_created` · `deleted_count`)
popülasyon çıktısına yazılmıyor ⇒ `I5.1` sıfır dediğinde *"konsolidasyon
çalışmadı"* ile *"çalıştı, eşleşecek DEEP düğüm yoktu"* **ayırt edilemez**.

⏸ **Bekleyen, fizik kararına bağlı: RCI.** `inherit_adapter` nesiller boyunca
adapter yığıyor (D-102) ve taban temsilin bozulup bozulmadığı **hiç ölçülmedi**.
Fizik değişirse `H^(0)` tabanı kayar ⇒ karardan sonra.

---

## ⛔ 3.0d · **KARAR — hangi kaldıraç** *(senin, D-007)*

⚠️ **Kaldıraç listesi D-168 §9'da güncellendi:** **0 —
`NICHE_POOL_FRACTION_RANGE (0.40, 1.00)`** (yeni, baskın) · **I — talep**
(K7 sınırı) · ~~II — `POOL_INIT`~~ (**geçersiz**, havuz oradan başlamıyor) ·
**III — Katman 2**.
⛔ **Hangisi seçilirse seçilsin ön-taahhüt YENİDEN yazılır** — bu turda hem
P1'in hem M1'in eşiği yanlış bir cebirden türetilmişti.

<details><summary>eski başlık (sabit kararı olarak yazılmıştı)</summary>

⚠️ **Tam gerekçe ve üç seçenek `CLAUDE.md` §1'de** (*"devam et" = KARAR*).
Özet: yapısal bant **0.1050 < r < 0.1425** (yalnız `POOL_REGEN_RATE`,
`POOL_CRISIS_THRESHOLD`, `COLLAPSE_EPSILON`'dan türetildi — hiçbir koşum
verisi girmiyor). D-163 bandın **üst ucunu** seçmişti.

| # | seçenek | özet |
|---|---|---|
| **A** ⭐ | `r`'yi bandın içinde aşağı al | tavan erken bağlar **ve** kriz rejimi erişilebilir kalır |
| **B** | `EXTRACTION_PARSE_MAX`'e bak | eksik almaların %63'ünün kaynağı ⚠️ **talep tarafı, K7 sınırı** |
| **C** | olduğu gibi bırak, Katman 2'ye geç | tanımlılık zaten açıldı ⚠️ kriz kanalı ölü kalır |

**Bitti sayılır:** **D-165** yazıldı — seçilen değer, **türetmesi**, **denge
noktası**, hangi eşiklerin altında/üstünde kaldığı (D-163'ün şartı) ve
reddedilen adaylar kayıtta.

---

## ⚠️ 2.2 · Bütçe kararı — **ertelendi, iptal değil**

Alan (`energy`) ve `G` (**4**) ölçümle kararlaştırıldı (D-161). Kalan bütçe
kararı (**kaç tohum · kestirim mi test mi**) için gereken iki sayı Katman 1
öncesi fizikten geliyordu ve geçersizdi.

✅ **3.0 pilotu ikisini de yeniden ölçtü (D-164 §5, ölçüt D-161 §1 ile aynı):**

| sayı | Katman 1 öncesi | **bugün** |
|---|---|---|
| Tohum kullanılabilirliği | 2/3 | ✅ **3/3** |
| Puanlanan hücre tanımlılığı | (seyrek) | ✅ **11/12** |
| Tohum başına süre | ~1 sa 58 dk | ⚠️ **2 sa 41 dk** (+%36) |

⇒ **Bütçe kararı artık yapılabilir** — ama **3.0b'den sonra**: fizik yine
değişirse süre de tanımlılık da değişir.

---

## ✅ 2.4b · **KARAR VERİLDİ: B yolu** — **D-156** (Yasin: *"önerdiğin şekilde devam et"*)
✅ **B: kurucu nesil ısınma neslidir**; Price yalnız ebeveyni **gen ≥ 2** olan
geçişlerden okunur ⇒ kullanılabilir geçiş **G − 2**. ⛔ **A elenmedi,
ertelendi** — kıtlık rejimi dejenerasyonun **sebebine** dokunuyor ama önünde
bir **sabit kararı** var (§2.7, D-082/D-084).

✅ **Öncül sınandı ve geçti (D-157, GPU'suz, ön-taahhüt D-156'da commit'li):**
C2'nin kurucu geçişinde **Var(z) > 0 olan hücre 0** (7 satır + 2 hiç satır
üretmeyen hücre). Sonda-3'le birlikte **4 tohum · 3 kol · 11 kurucu hücre,
ölçülebilir 0** — ve **iki ayrı fizikte** aynı ⇒ dejenerasyon **yapısal**.
⚠ **K4:** D-156'da *"9 satır"* demiştim, gerçekte **7** çıktı; karar
değişmiyor ama tahmin **düzeltilerek** kayda geçti.

⛔⛔ **B2 uyardı: B gerekli ama YETERLİ DEĞİL.** Kurucu nesil atıldıktan sonra
bile eski fizikte hücrelerin yalnız 4'ü ölçülebilir, ve **birincil alanla
(`energy`) bakılınca `ΔCov` 0/3 tohumda tanımlı olurdu** ⇒ D-145'in **1. ve
2. kusuru B'den etkilenmiyor** ⇒ **2.2'ye bağlandı**.

✅ **Taslağa yazıldı:** `PREREGISTRATION_3.md` **YENİ-4** (tasarım) + **L21**
(sınır); **L17** ve **L20** taze ölçümle güncellendi.
⛔ **Yazılmadı çünkü karar: G kaç olacak** — `G − 2` bugünkü `G = 3`'ü tohum
başına **tek geçişe** düşürüyor ⇒ doğrudan bütçe slotu ⇒ **2.2**.

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

## ✅ 2.5 · Somatik zincirin kırıldığı halka sayaçlandı — **D-158**
✅ `select_for_transfer` sekiz sayaç yazıyor (`candidates` · `dropped_recall` ·
`trauma` · `warning_low` · `dropped_salience` · `warning_high` ·
`dropped_drift` · `standard`); `consolidate_generation` sayacı açıyor,
koşucu ajan satırına **`transfer_gates`** olarak yazıyor. **Hesap değişmedi.**
K2 ✅ (dört aday dört farklı kader + iki farklı bant) · K3 ✅ (iki çağrı yeri) ·
K5 ✅ (**8 mutasyon, 8 doğru test**, md5'li).

⭐ **İki uyarı yolu AYRI sayılıyor** — alt bant salience çıtasını atlıyor, üst
bant geçmek zorunda; birleştirilse yalnız üst yolun ateşlediği bir koşum
*"alt yol çalışıyor"* gibi okunurdu (D-155 §2'nin bıraktığı karışıklık).
⚠ **İlan:** bu madde bir **sayı üretmedi**, bir soruyu **üretilebilir** hâle
getirdi — sayaçlar ancak **gerçek koşumda** dolar (stub değerleri teşhis
dayanağı **değil**, D-138'in PE_w dersi).

## ✅ 2.6 · Kurucu nesil bir kapıya bağlandı — **D-159**, ve kapı hemen bir kusur buldu
✅ **I5.5** (FLAG) bağlandı, **iki yönlü**: ebeveyni gen ≥ 2 olan bir geçişte
hiçbir alan ölçülebilir değilse **bayrak**; kurucu geçiş **ölçülebilir
çıkarsa da bayrak** (YENİ-4 kullanılabilir veri atıyor demek ⇒ D-157'nin
yeniden açılma tetiği). Kapı sayısı **8 → 9**; `PREFLIGHT_INVARIANTS.md`
**27 madde**.

⛔ **2.6'nın kendi tarifi ölçümle değişti:** *"`F_agent` **ve** uç nokta
yayılımı ikisi birden sıfırsa"* koşulu C2'nin **9 kurucu hücresinin 6'sını
kaçırırdı** (s9911 · s9913 yayılımı sıfır **değil**, `Var(z)` yine 0).
Karar veren nicelik **`selection_estimable`**; `F_agent` yayılımı
**raporlanır, verdict'e girmez**.

⭐⭐ **Geriye dönük koşuldu:** sonda-3 **geçti**, ⛔ **C2 bayrak** —
puanlanan **6 geçişin 5'i ölü**, ve C2 bunu **`clean`** raporlamıştı.
**K6'nın bedeli üçüncü kez ölçüldü.**

⚠ **Kalan iş, karara bağlı:** kapı *"herhangi bir alan"* diye soruyor, ön-kayıt
ise **bir alan** ilan ediyor (`energy`). `s9911`'in hücreleri `resource`'ta
geçti, `energy` ile **düşerdi** ⇒ **alan kararı verilince (2.2) kapı o alana
daraltılmalı.**

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

⚠ **D-155/D-157 bu maddeye üç şey ekledi — karar verilirken birlikte
görülmeli:**

1. ⛔ **Kusur 4 tekrarlandı ve genelleşti:** kusur #1 (`energy` nadiren
   ölçülebilir) ve #2 (alan **tohuma** bağlı) **kurucu nesli atmaktan
   etkilenmiyor**. Eski fizikte, gen1 atıldıktan **sonra bile**, birincil
   alanda `ΔCov` **0/3 tohumda** tanımlı olurdu (D-157 §2). ⇒ **Alan kararı
   bütçe kararından önce gelir.**
2. **`G` yeniden hesaplanmalı:** YENİ-4 ile kullanılabilir geçiş **G − 2**
   ⇒ `G = 3` tohum başına **tek** geçiş bırakıyor. `G = 4` koşumu ~1.5 kat
   uzatır ve süre kestirimleri buna göre yeniden yazılmalı.
3. ⭐ **Kusur 3 (`ΔP_active` sıfır-şişkin) hâlâ açık** — sonda-3 uç nokta
   adayını **reddetti** (L17), yani bu kusuru çözecek sürekli uç nokta yolu
   **kapandı**.

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

</details>
