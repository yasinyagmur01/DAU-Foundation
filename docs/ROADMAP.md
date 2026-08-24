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

## 3. ⛔ Kat 2'nin önündeki tek yapısal engel

**D-172 §4:** popülasyon yolunda **`run_consolidation` hiç çağrılmıyor.**

Aksiyom **iki kanal** diyor (§3, `CLAUDE.md`): sembolik kasa (Kanal 1) ve LoRA
(Kanal 2), *"biri diğerinin yerine geçmez"*.

⇒ Bugün `lived`/`shuffle` karşıtlığı **yalnız Kanal 2'nin testi**.
⇒ **Seviye 3 — yani aksiyomun kendisi — bugünkü kablolamayla sınanamaz.**
⚠️ Ebbinghaus unutması da popülasyon ajanlarında çalışmıyor (aynı sebep).

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
| Harcanan kaldıraç | **2** (Katman 1, Katman 1b) · **kalan hak: 1** |
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
| 5 | DR brief #14 | ✅ **evet** — tek soru: ratcheting'in yayımlanmış ampirik standardı |

⛔ **Ve koşumdan önce üç alet onarımı** (D-176 §6): **I4.2 kilidi** ·
**resume** · **çok-dosya birleştirici**. Üçü de GPU'suz, üçü de koşum yolunu
değiştirdiği için 🔒 **kilitten sonra yapılamaz**.
