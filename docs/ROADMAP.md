# YOL HARİTASI — DAU nereye gidiyor

**2026-08-24 · D-175 · Yasin: *"nereye gidiyoruz, gözümüzü kapattık gidiyoruz gibi geliyor"***

⚠️ **Bu belge baştan yazıldı.** Önceki sürüm (*"Yön 3'e hızlandırılmış geçiş"*)
**iptal edilmiş bir hedefi** gösteriyordu — Yön 3 **D-135'te kapatıldı** ve
belge güncellenmedi ⇒ **2026-08-19'dan 08-24'e kadar projenin yazılı varış
noktası yoktu.** Eski sürüm `ROADMAP_v1_yon3.md.bak` olarak duruyor.

---

## 1. Sonunda kurmak istediğimiz cümle

> **Aksiyom:** *"Bir agent'a trait veremezsin, sadece yaşam verebilirsin,
> trait oradan çıkar."*

Bunun **ölçülebilir** hâli, aletin kendi tanımladığı dört seviyedir
(`analyze_population_run.py` başlığı):

| seviye | ne gösterir | iddia edilebilecek cümle |
|---|---|---|
| **0** | `Var(w) > 0` | ⛔ **hiçbir şey** — yalnız ön-koşul |
| **1** | `Cov(w, z) ≠ 0` | *"seçilim yaşanmış drift'e etki etti"* |
| **2** | terim nesiller boyu sönmüyor | *"etki birikimli"* |
| **3** | `lived ≠ shuffle ≠ null` | ⭐ **"yaşanmış iz aktarılıyor" — AKSİYOM** |

⛔ **Aletin kendi uyarısı, unutulmasın:** *"Price **SEÇİLİMİ** verir, kol
karşılaştırması **KALITIMI**. Seviye 1 dolu, seviye 3 boş olabilir."*
⇒ **Seviye 1 bitiş çizgisi değildir.**

---

## 2. Üç kat — hedefi nereye koyarsak maliyet ne

⚠️⚠️ **BU TABLO D-176'DA DÜZELTİLDİ — aşağıdaki ilk sürüm İKİ KOL üzerinden
hesaplanmıştı ve Kat 2 için geçersizdi.** Seviye 3 tanımı gereği **üç kol**
(`lived ≠ shuffle ≠ null`, `analyze_population_run.py:18`); D-173 pilotu
`--arms lived shuffle` ile koştu.

| kat | iddia | seviye | `G` | kol | `T_max` | N | MDE |
|---|---|---|---|---|---|---|---|
| **1** | *"seçilim ölçülebilir"* | 1 | 4 | 2 | 47 sa | 20 | 0.676 |
| ⭐ **2** | *"yaşanmış iz aktarılıyor, karıştırılmış aktarılmıyor"* — **AKSİYOM** | 3 | **4** | **3** | **70 sa** | **20** | **0.676** |
| **3** | *"kümülatif birikim"* — başarım artıyor **ve** kontrolde artmıyor | 2+3 | 6 | 3 | 103 sa | 20 | 0.68 |

⚠️ **`G = 8` "ölçülmeden hayır"** — adapter sönümü uzun soyda sinyali
seyreltebilir (D-130 §12).

⭐ **Ve `G = 6` de Kat 2'nin şartı değil, Kat 3'ün kancasının şartı.**
Seviye 3 bir **kol karşıtlığı** — nesil başına okunuyor, `G = 4` onu verir.
Aynı 70 saatte `G = 6`'ya çıkmak tohum sayısını 20 → 13'e, duyarlılığı
0.676 → **0.866**'ya düşürür (D-176 §3).

**Karar (D-176, Yasin): Kat 2 · 70 sa · `G` = 4 · üç kol.** Kat 3'ün kancası
**ertelendi** — §4'ün *"seçilim-tek-başına null modeli"* henüz yazılmadı,
bugün ödenirse boşa gider.

---

## 3. ⚠️ Kat 2'nin önündeki engel — **bu bölüm D-178'de DÜZELTİLDİ**

⛔ **Aşağıdaki ilk sürüm doğru olguyu yanlış sonuca bağlamıştı.** Olgu duruyor,
çıkarım düştü.

**Ölçülen (D-178/B4):**

| | |
|---|---|
| `consolidate_generation` popülasyon yolunda | ✅ **çağrılıyor** (`run_population_experiment.py:1692`) |
| **I5.4** — sembolik kayıt varise ulaşıyor mu | ✅ **True**, pilotta *"applied 463x"* |
| **I5.1** — ilişki grafiği | ❌ boş (`run_consolidation` çağrılmıyor) |

⇒ **Kanal 1 ölü değil.** Ölü olan **uyku konsolidasyonu**: ilişki grafiği,
Ebbinghaus budaması, güçlendirme — yani **yaşam içi** bir bellek dinamiği,
kalıtım kanalı değil.

⭐ **Ve asıl düzeltme:** `lived ↔ shuffle` karşıtlığının Kanal 2'yi izole
etmesinin sebebi konsolidasyonun bağlı olmaması **değil** — **müdahalenin
kendisi** Kanal 2'ye yapılıyor (tercih çiftleri karıştırılıyor). ⇒
`run_consolidation`'ı bağlamak `lived ≠ shuffle`'ı bir **Kanal 1 testi
yapmaz**. Kanal 1'i sınamak ayrı bir **üçüncü müdahale** ister (örn. kasası
karıştırılmış bir kol) — bu bir kablolama düzeltmesi değil, bir **tasarım
değişikliği**.

⇒ **Karar (D-178/B4): bağlanmıyor, sınır ilan ediliyor.** Eksik dinamik **her
kolda simetrik** olarak yok ⇒ seviye 3 karşıtlığını oynatamaz. `I5.1` artık
`None` (**değerlendirilmedi**) diyor ve sebebini adlandırıyor; sabit
(`SLEEP_CONSOLIDATION_WIRED`) bağlandığı gün kapı kendiliğinden geri geliyor.
**Kaldıraç hakkı harcanmadı: 2/2 duruyor.**

<details><summary>ilk sürüm (D-175, çıkarımı düşen)</summary>

**D-172 §4:** popülasyon yolunda **`run_consolidation` hiç çağrılmıyor.**

Aksiyom **iki kanal** diyor (§3, `CLAUDE.md`): sembolik kasa (Kanal 1) ve LoRA
(Kanal 2), *"biri diğerinin yerine geçmez"*.

⇒ Bugün `lived`/`shuffle` karşıtlığı **yalnız Kanal 2'nin testi**.
⇒ **Seviye 3 — yani aksiyomun kendisi — bugünkü kablolamayla sınanamaz.**
⚠️ Ebbinghaus unutması da popülasyon ajanlarında çalışmıyor (aynı sebep).
</details>

---

## 4. Kat 3'ün kancası — ölçüldü, ve tuzağı da ölçüldü

Kümülatif iddia **artabilen** bir nicelik ister. Var (D-175 §4, kollar birlikte,
L9 korunarak):

| | gen1 | gen4 |
|---|---|---|
| ömür | 22.29 | **26.94** |
| enerji | 0.4970 | **0.6664** |
| `F_agent` | 0.5643 | **0.6871** |

⛔ **Bu kümülatif birikim DEĞİL.** Turnuva `F_agent` üzerinden seçiyor ⇒ artış
**tanım gereği**; ömür ve enerji onun girdileri ⇒ **döngüsel**.

⭐ **Eksik olan nicelik değil, karşılaştırma modeli:** *"seçilim tek başına ne
kadar artış öngörür, gerçekleşen ondan fazla mı?"*
⇒ **Seçilim-tek-başına null modeli koşumdan ÖNCE ilan edilmeli.**

---

## 5. Bugün nerede duruyoruz

| | durum |
|---|---|
| Fizik | ⭐ **Katman 1b (D-171)** — tavan **24/24 hücrede** bağlıyor, kurucular **her tohumda 8/8 ayrı**, kriz kanalı **canlı** (1068 olay) |
| Ön-koşul zinciri | ✅ **kurulu** — `q` = 3/3, seviye 0 = 18/18 |
| Alet | 11 kapı · checkpoint · replay · pozitif kontrol · K1–K6 |
| Kapanmış sonuçlar | **B2 = alet null'ı** · **C2 = evren null'ı** — ikisi de raporlandı |
| Harcanan kaldıraç | **2** (Katman 1, Katman 1b) · ⭐ **kalan hak: 2** (D-176 tanımı: yalnız **tabanı geçersiz kılan** değişiklikler sayılır) |
| Yapılmamış | ⛔ **hipotez testinin kendisi — bir kez bile koşulmadı** |

---

## 6. Döngünün çıkışı — bu belgenin asıl işi

⛔ **Kaldıraç bütçesi sıfırlandığında yalnız iki dal kalır:**

| dal | koşul |
|---|---|
| **GEÇ** | `q > 0` ve `N_eff ≥ 2` ⇒ doğrulayıcı koşum, MDE ne çıkarsa **ilan edilir** |
| **DUR ve RAPORLA** | uç nokta hiçbir tohumda tanımlı değil ⇒ evren olduğu gibi kilitlenir, sonuç **sınırlarıyla** raporlanır |

⭐ **İkincisi meşru bir bilimsel çıktıdır** (Değiştirilemez Süreç Kuralı) ve
kuyrukta uzun süre **adı bile yoktu**. *"Bir kaldıraç daha"* her zaman
durmaktan ucuz göründüğü için, sayı olmadan bu döngünün çıkışı yoktur.

---

## 7. ⛔ Bilerek YAPILMAYACAKLAR

1. **Davranışa dokunmak** — C1 / kilit K7, aksiyom.
2. **Trait enjeksiyonu** — Değiştirilemez Yasak #1. ⚠️ DR #13'ün önerdiği
   *"epigenetik trait vektörü"* buraya düşer (D-169).
3. **Çıkarım anında aktivasyon yönlendirme** — kilit K7 zaten reddetti (D-169).
4. **`G = 8`** — ölçülmeden hayır (D-130 §12).
5. **Kapasite / kriz eşiği ayarı** — D-131'de aritmetikle elendi.
6. **Sabiti sonuca bakarak seçmek** — §2.7.

---

## 8. ✅ Karar noktaları — **İLAN EDİLDİ, D-176** (2026-08-24, Yasin)

| # | karar | **ilan edilen** |
|---|---|---|
| 1 | **Hedef katı** | ⭐ **Kat 2** — aksiyom, seviye 3 |
| 2 | `T_max` · `G` · kol | **70 sa · G = 4 · üç kol** ⇒ `N_eff` = 20, **MDE 0.676** |
| 3 | Koşum şekli | **parçalı**, saate dokunulmadan, gece başına tohum mümkün olduğunca çok (I4.1 replay sabit maliyeti ~35 dk/çağrı) |
| 4 | Kaldıraç hakkı | **2** — yalnız **tabanı geçersiz kılan** değişiklikler sayılır; **alet onarımı bedava** |
| 5 | DR brief #14 | ⏸ **ERTELENDİ, D-178** — sorusu *ratcheting* = **Kat 3**, ve Kat 3 bu koşumun kapsamından çıktı (karar 2). Kat 3 masaya gelince gönderilir |

✅ **Üç alet onarımı bitti (D-177):** **I4.2 kilidi** (`250f7e5`) · **resume**
(`07d0cae`) · **çok-dosya birleştirici** (`00f1252`). Üçü de GPU'suz, üçü de
koşum yolunu değiştirdiği için 🔒 kilitten önce yapıldı.
✅ **B4 — Kanal 1 kararı: bağlanmıyor, sınır ilan edildi** (D-178, §3).

⇒ **Sıradaki: C** — ön-kayıt taslağının dört kusuru (D-145) + yeni sınırlar
(bütçe sansürü · uyku konsolidasyonu), sonra 🔒 **D: KİLİT**.

---

## 9. ⭐ Kat 3'ten SONRA — keşif hattı (2026-08-25, Yasin)

⚠️ **Bu bölüm D-175'in dersinin tekrarını önlemek için var.** Belge daha önce
varış noktasını gösteriyordu ama **sonrasını göstermiyordu**, ve beş gün
boyunca iptal edilmiş bir hedefi işaret etti. Kat 3 bir bitiş çizgisi değil,
**bir kapı**; arkasında ne olduğu burada yazılı.

**Yasin'in çerçevesi:** *"makul bir noktada gerçekten bir şey kanıtlayarak
listeyi bitir, sonra sınırlara takılmadan yapabileceğimizi yap, sonra gerekirse
belimizi büken kısımların mimarisini değiştir — kodun aslını koruyarak, bir
branch'te."*

### 9.1 ⭐⭐ İlk iş: NAKİL TESTİ (common-garden)

**Soru:** kalıtılan şey bir **özellik** mi, yoksa taşınan bir **durum** mu?

Bu, bu projeye yöneltilecek **en sert eleştirinin** ta kendisi — ve biyolojide
cevabının standart bir yöntemi var: farklı soyları **aynı** ortamda okumak.

**Tasarım:**

| | |
|---|---|
| **girdi** | Her koldan (`lived` · `shuffle` · `null`) **doğum anındaki varisler**, aynı tohumdan |
| **ortam** | ⭐ **Üçü için de ÖZDEŞ, taze bir niş** — hiçbirinin yaşamadığı |
| ⭐ **niş seçimi** | Rastgele **değil**: ajanları **D-090'ın işaretlediği bölgeye** sokan bir niş (düşük enerji + yüksek birikmiş drift). Orada `cooperate` eşiği **keskin ve tırtıksız** ölçülmüştü |
| **okuma** | Karar dağılımı, ve ajanların eşiğin **hangi tarafına** düştüğü |
| **karşıtlık** | **Kol, eşiğin hangi tarafına düşüleceğini öngörüyor mu?** |

⭐ **Neden bu tasarım:** *"taze dünyaya koy, bak"* L18 yüzünden **bilgisiz
dönebilir** — ikisi de DEFECT der, hiçbir şey öğrenilmez. Ajanları bilerek
ayrımın olduğu bölgeye sokmak, soruyu *"davranış değişti mi"*den
**sayılabilir** bir soruya çevirir.

⭐ **Maliyeti kavramsal olarak sıfır:** yeni fizik yok, yeni sabit yok, ve
**hiçbir taahhüt kırılmıyor** — K7'ye, C1'e, C2'ye dokunmuyor. Bir **okuma**,
bir müdahale değil.

⚠️ **Ama iki şey ölçülmeden varsayılmayacak:**
1. **Varis diskten diriltilebiliyor mu?** Adapter'lar `dau_runs/adapters/`
   altında **duruyor**; **kasanın (vault) kalıcılığı doğrulanmadı**
   (`arm_vault` bir bağlam yöneticisi ve çıkışta kapanıyor). Diriltilemiyorsa
   nakil, varisleri **üreten kısa bir koşum** gerektirir ve bedeli sıfır olmaz.
2. **D-090 bugünkü fizikte hâlâ geçerli mi?** O ölçüm **tek-soy yolunda** ve
   Katman 1/1b'den **önce** yapıldı. Eşik hâlâ orada mı, **önce sınanmalı**.

### 9.2 ⛔ Sıralama kuralı — nakil, sınır kırmadan ÖNCE

Nakil bir sonuç değil, bir **gündem belirleyici**: hangi sınırı kırmaya
değeceğini **o söylüyor**.

| nakil sonucu | okuma | sonraki hamle |
|---|---|---|
| davranış **gerçekten farklı** | iz davranışa ulaşıyor; **L18 sanıldığı kadar zarar vermiyor** | ⇒ **K7 kırılmaz**; enerji `z`'nin boyutuna (L3, `r_eff` medyan **1.000**) gider |
| davranış **aynı**, yalnız sayı farklı | kalıtılan şey gerçekten bir **durum** | ⇒ **K7 kırılır**, ve gerekçesi artık **ölçüme** dayanır |

⇒ Sınırları önce kırıp sonra bakmak, **hangisini kırmak gerektiğini bilmeden**
kaldıraç harcamaktır.

### 9.3 ⛔ Disiplin şartı — bu olmazsa doğrulayıcı turu kirletir

> **`docs/C3_RESULTS.md` yazılıp commit edilmeden hiçbir keşifsel nakil
> sonucuna BAKILMAZ.**

Sebebi ölçülü bir insan zaafı: kilitli koşumun sonucunu, sonradan gelen
keşifsel bir bulgunun ışığında **yeniden yorumlama** baskısı gerçektir. Sıra
bozulursa *"ön-kayıt neyi korudu"* sorusunun cevabı kalmaz.

### 9.4 Branch mekaniği — kodun aslı korunur

- **Kilit noktasından dallan**, `main`'in ucundan değil:
  `git branch exp/transplant a1163ac778c9` ⇒ dalın tabanı ön-kayıtın
  **dondurduğu** hâldir, karşılaştırma anlamlı kalır.
- `main` **dondurulmuş sayılır**: doğrulayıcı koşum + `C3_RESULTS.md` bitene
  kadar. ⚠️ Koşum sürerken `.py` düzenleme **dalda da yasak** — aynı GPU.
- Dalın çıktıları **ayrı isim alanına**: `dau_runs/exp_*`. Yoksa birleştirici
  alet uyuşmazlığı diye **reddeder** — doğru davranış, ama kafa karıştırır.
- ⚠️ **Dalda keşif serbest, İDDİA değil.** Bir şey iddia edilecekse
  **dördüncü ön-kayıt** ve yeni bir kilit gerekir. Keşif ucuz, iddia pahalı;
  ikisini ayıran şey **kilit**.

### 9.5 Yeniden tasarım aday listesi — DR #14'ten (D-184)

⛔ Hepsi **fizik değişikliği**, hepsi **dördüncü ön-kayıta**:

| aday | neyi hedefliyor | not |
|---|---|---|
| ⭐⭐ **`z` = eksen vektörü + eksen başı ölçek** (argmax'ı uç noktadan çıkar) | **L3** — `r_eff` 1.000 | ⭐ **Ölçüldü (D-187): `r_eff` 1.000 → 1.453 → 3.194.** İkisi birden gerekiyor: argmax'ı kaldırmak tek başına 1.45'te kalıyor, çünkü `energy` `uncertainty`'nin **8.7 katı**. ⭐ **Ucuz yolu var:** `z`'yi kaydedilmiş eksen vektöründen okumak **fizik değiştirmez** ⇒ kaldıraç harcamaz. ⛔ Normalizasyon referansı **önceden** ilan edilmeli (§2.7) |
| **Uzamsal kafes + komşu dışlama** | **L18** — davranış çökük | ⚠️ Ortamın özelliği, karar kuralının değil ⇒ K7'yi açmıyor. Ama `I5.6`/`I4.2` yeniden kalibre edilmeli |
| **Wasserstein + permütasyon** | **tanımlılık problemi** | `W1`, `Var(z)=0` iken de tanımlı ⇒ sıfır-şişkinliği yapı gereği kaldırıyor |
| **Doğrusal olmayan havuz yenilenmesi (devrilme noktası)** | **L18** | ⚠️ D-163'ün şartı: **denge noktası** da yazılacak |
| **Darboğaz 5'in gerçek reçetesi** | **GAP-3 / L20** | ⛔ DR'nin reçetesi mimariye uymuyor; düzeltme **kayıt yapısı** üzerinden |

### 9.6 Sıra — tek bakışta

```
doğrulayıcı koşum (5 gece)  →  C3_RESULTS.md  →  🔒 tur kapanır
                                      ↓
                        D-090 hâlâ geçerli mi? (ucuz sonda)
                                      ↓
                    NAKİL TESTİ (exp/transplant dalında, keşifsel)
                                      ↓
                    ⇒ hangi sınırın kırılacağına KARAR
                                      ↓
                    dördüncü ön-kayıt  →  kilit  →  yeni koşum
```
