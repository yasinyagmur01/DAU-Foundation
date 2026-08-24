# Popülasyon C‴ — Üçüncü Ön-Kayıt

**Durum: 📝 TASLAK · 2026-08-24 · ✅ **ALTI SLOTUN ALTISI DA KAPALI** ·
⏳ KİLİDE HAZIR — kilit Yasin'in**

✅ **D-145'in dört kusuru kapandı** (D-161 · D-179) ve **SLOT 3 (bütçe)
D-176'da kapandı.** Geriye yalnız kilit anının kendisi kalıyor: §12'nin alet
kimliği donduruluyor ve durum satırına **🔒 + commit hash** yazılıyor.

| # | kusur (D-145) | durum (2026-08-24) |
|---|---|---|
| 1 | Birincil alan `energy` C2'de **15 hücrenin 1'inde** ölçülebilirdi | ✅ **KAPANDI ve TERSİNE DÖNDÜ (D-179).** Katman 1b pilotunda `energy` **16/16 satırda**, **10'u tanımlı**. Eski ölçüm eski fizikten |
| 2 | Hangi alanın yazıldığı **TOHUMA** bağlı ⇒ sabit alan tohumların bir kısmını atar | ✅ **KAPANDI (D-179).** Kriz D-173'te geri döndü ve alan tablosunu **bozmadı**: `resource` `energy`'nin **yerine değil yanına** yazılıyor ⇒ **her hücrede `energy` satırı var**, hiçbir tohum düşmüyor |
| 3 | `ΔP_active` sıfır-şişkin; Wilcoxon sıfırları atar ⇒ reddedebilme ihtimali düşük | ✅ **ÇÖZÜLDÜ, ama gizlenerek değil (§4.1).** Test çerçevesi karara bağlandı: Wilcoxon + **ilan edilmiş MDE** + `p` **her zaman CI ve etki büyüklüğüyle birlikte**. ⛔ Yapısal itiraz **ayakta ve bir SONUÇ olarak raporlanacak**. ⚠️ Ve bu değerlendirme sırasında **L9 ihlal edildi** — D-179, sınır **L25** |
| 4 | Bütün bir kol-tohumun **hiç** Price satırı olmayabilir — üçüncü kategori tanımsız | ✅ **KAPANDI (D-159 kapı, D-179 kural).** `I5.5` yakalıyor; ve §3.1 artık *"inaktif"* ile *"hiç oluşmadı"*yı **ayrı** raporluyor. Ölçüldü: D-173'te 18 değil **16 hücre** |

⚠️ **Kilitten önce yakalanan iki eskime** (ikisi de burada düzeltildi):
**§3.1'in `P_active` beklentisi** ters yöndeydi · **L20'nin sonuç cümlesi**
(*"somatik yarı akmıyor"*) bugünkü fizikte **yanlış** — `I5.4` pilotta
**`applied 463x`**.

⚠ **Önceki iki ön-kayıt yürürlükte kalır.** `PREREGISTRATION.md` B2'yi,
`PREREGISTRATION_2.md` C2'yi bağlar; ikisi de **kapanmış bölümlerdir**. Bu
belge onları geçersiz kılmaz, **ayrı bir deneyi** bağlar. Çelişki görülürse
sessizce seçilmez, ilan edilir (§2.11).

---

## 0. Neden üçüncü bir ön-kayıt

İkinci ön-kayıt koşuldu (C2) ve sonucu **evren null'ıydı** (D-123): makine
çalıştı (`run_quality=clean`, 6/6 kapı, I4.1 identical, pozitif kontrol
hareket etti) ama **uç nokta ölçmedi** — 18 Price satırının yalnız **4'ü**
tanımlıydı.

Sebep sonradan bulundu ve **tek bir cümleye indi** (D-129/D-130):

> Farklılaşmanın tek kaynağı **adapter**. Sıralı erişim ancak **kıtlıkta**
> ısırır, kıtlık ancak davranış farkıyla doğar, davranış farkı ancak
> adapter'la. ⇒ `null` kolu zengin nişte **donmuş klon popülasyonu**.

Bu ön-kayıt o teşhisin sonuçlarını uygular: birincil karşıtlık **değişti**
(D-131), uç noktanın **ölçülebilirliği** artık kendisi bir uç nokta (D-143),
ve test istatistiği **tohum başına bir skalere** indirgendi (D-140).

---

## 1. İddia

Sınanan parça (aksiyomun **tamamı değil**):

> Bir ajanın **yaşayarak edindiği izin yönü**, popülasyonda **kimin varis
> bıraktığıyla** ilişkilidir; ve iz **tersine çevrildiğinde** bu ilişki
> değişir.

⛔ **Bu ön-kaydın iddia ETMEYECEKLERİ** — olumlu sonuçta bile:

- **Birey düzeyi hiçbir şey.** P1 kol başına ayrı popülasyon veriyor ⇒ iddia
  **grup düzeyinde** kalır.
- *"LLM ajanlarında Lamarckçı kalıtım vardır"* — tek model, tek niş ailesi,
  **n = 1 deney**.
- **`z`'nin hangi alanında** olduğu — `z` etkin olarak **tek boyutludur**
  (L3).
- *"Seçilim"* — `null` kolunda sürüklenme ile seçilim ayrılamaz (L12).
- **Nesiller arası eğilim** — nesil satırları **betimleyicidir** (D-141).

---

## 2. Tasarım — ✅ kilitli (C2'den devralındı, iki değişiklikle)

| # | Karar | Seçilen | Kayıt |
|---|---|---|---|
| **P0** | Ajanlar nasıl farklılaşır | ① sıralı erişim, **tur başına rotasyon** | D-104 |
| **P1** | Kol yapısı | kol başına **ayrı popülasyon ve ayrı mera** | D-095 |
| **P2** | Seçilim şeması | turnuva, **k = 2** | D-094 |
| **P3** | Üreme | sabit N; ölen her ajanın yerine turnuva kazananından bir varis ⇒ `w ∈ {0,1,2,…}` | D-094 |
| **P4** | Katmanlar | `F_agent` (girdi) → `w` (varis) → `z` (sonuç), **üçü ayrı** | D-094 |
| **P5** | Havuz | kapasite **N ile ölçeklenir**, kişi başı 100/80 sabit | D-081 |
| **P6** | Faz | **tek faz**; `delta_pe` uç noktası yok | D-095 |
| — | Mera | **her nesilde taze** | D-104 |
| — | Kanal 2 | ebeveynin adapter'ı **varise kopyalanır** | D-102 |
| — | Price | **bir nesil gecikmeli**: G nesil ⇒ **G−1** satır | D-101 |
| — | N · G · olay | **N = 8** · **G = 4** · **30 olay** | D-107, C2, **D-161** |
| ⭐ **YENİ-1** | **Birincil karşıtlık** | **`lived` ↔ `shuffle`**; `null` **betimleyici** | **D-131** |
| ⭐ **YENİ-2** | **Test birimi** | tohum başına **ortalanmış** değer; nesil satırları **raporlanır ama test edilmez** | **D-141** |
| ⭐ **YENİ-3** | **Fitness bantları** | **göreli** (hücre içi min-max); eşik **değerleri değişmedi** | **D-152** |
| ⭐ **YENİ-4** | **Kurucu nesil = ısınma** | Price **yalnız ebeveyni gen ≥ 2 olan** geçişlerden okunur ⇒ kullanılabilir geçiş **G − 2** | **D-156/D-157** |

⛔ **YENİ-4 bir düzeltme değil, ilan edilmiş bir KAPSAM kısıtıdır.** Kurucu
nesil ölçülebilir hâle gelmiyor; ölçüm onu **dışarıda bırakıyor**. Gerekçe
mekanizma, veri değil: kurucular **özdeş doğar**, farklılaşmanın tek kaynağı
**adapter**'dır (D-129/D-130), ve adapter ancak birinci nesil **bittikten
sonra** doğar ⇒ birinci geçiş **hangi uç noktayla olursa olsun** `Var = 0`.
**Ölçüldü: 4 tohum · 3 kol · 11 kurucu hücre, ölçülebilir olan 0** — ve iki
ayrı fizikte (D-152 öncesi/sonrası) aynı (D-155 §1, D-157 §1).
⚠ **Bedeli L21'de ilan edildi.**
✅ **G = 4 karara bağlandı (D-161, ölçümle).** Tanımlılık pilotunda birinci
puanlanan geçiş (gen2→gen3) **üç tohumun üçünde de** kullanılamaz çıktı;
ikinci geçiş (gen3→gen4) **iki tohumu kurtardı**. ⇒ `G = 3` ile bu üç tohumun
**hiçbiri** kullanılabilir olmazdı (**0/3**), `G = 4` ile **2/3**.
⚠ Bu **L10'un ilan ettiği `G = 3`'ten sapmadır** ve L10 buna göre güncellendi.

⚠ **Hiçbir sabit DEĞERİ değişmedi.** `constraints.py` C2'deki hâliyle; özellikle
`DELTA_THRESHOLD_DEEP = 0.70` (D-143) ve `CROSS_AXIS_SPILLOVER = 0.20`
(D-137) **korunuyor**.

---

## 3. Uç noktalar — ✅ **SLOT 1 KAPALI (D-143 · D-140)**

⭐ **İki eş-birincil uç nokta.** İkisi **farklı soru** soruyor ve ikisi de
koşumdan **önce** tanımlı.

### 3.1 Birincil A — `ΔP_active` (ölçülebilirlik)

| | |
|---|---|
| **hücre** | (kol, tohum, nesil geçişi) üçlüsü |
| **alan** | ⭐ **`energy`** — aşağıda gerekçelendirildi |
| **aktif** | o hücrenin **`energy`** alanında `selection_estimable = True`, yani `Var(z) > 0` |
| **alan yoksa** | hücre **inaktiftir** — `energy` anahtarı hiç yazılmamışsa hiçbir ajan o alanda drift taşımıyor demektir, ve *"eksik veri"* değil **gözlem**tir |
| **`P_active(kol, tohum)`** | o kol-tohumun **G−1 = 2** geçişinden aktif olanların **oranı** ∈ {0, ½, 1} |
| **karşıtlık** | `ΔP_active(tohum) = P_active(lived) − P_active(shuffle)` |

⚠ **Neden `energy`, ve neden bu etkiye bakmak değil.** `selection_estimable`
bayrağı **alan başına** yazılıyor, dolayısıyla *"hangi alan"* ön-kayıtta
söylenmek zorunda. Gerekçe **mekaniktir, sonuca bakmaz** (D-130 §9):

- `resource` — krizin **sabit** alanı, ve kriz **bütün kola aynı anda** vurur
  ⇒ herkes aynı skarı alır ⇒ hücre içi bilgi taşımaz (L14).
- `social` · `uncertainty` — argmax'ı **hiç kazanmıyorlar**; C2'de 216 yaşamda
  **sıfır kez** yazıldılar (D-136 bunun sebebini ölçtü: skaler spillover).
- ⇒ **`energy`, bireysel kanalın tek yazdığı alandır.**

⚠️ **BU BEKLENTİ D-179'DA GÜNCELLENDİ.** Eski metin *"C2'de `energy` 216
okumanın 11'inde doluydu ⇒ `P_active` düşük beklenmelidir"* diyordu. **Katman
1/1b'den sonra ölçüm ters yönde** (`layer1b_pilot_g4_s9926_9928.json`,
16 Price hücresi / 25 satır):

| alan | satır | `selection_estimable` |
|---|---|---|
| **`energy`** | **16/16** | **10** |
| `resource` | 9/16 | **0** — 9 satırın 9'unda `z_variance = 0.0` |

⇒ `P_active` **yüksek** beklenmelidir. ⭐ Ve `resource`'un dışlanma gerekçesi
artık **türetilmiş değil ölçülmüş**: L14'ün confound'u (kriz alanı sabit,
herkese aynı skar) kendini **sıfır varyans** olarak gösteriyor.

⛔ **Ve bu bir uç nokta değişikliği DEĞİLDİR** — alan `energy` olarak
D-143/D-144'te, bu ölçümden **önce** ilan edilmişti; değişen yalnız
**beklenti**. Uç noktanın kendisi D-179'dan sonra da **değişmedi** (karar:
Yasin, 2026-08-24).

⛔⛔ **ÜÇÜNCÜ KATEGORİ — hücre hiç oluşmadı** (D-145/kusur 4, ölçüldü D-179).
*"Alan yoksa hücre inaktiftir"* kuralı, **Price satırının kendisi yoksa** ne
olacağını söylemiyordu. Ölçüldü: D-173 pilotunda **s9927'nin gen2 hücresi
iki kolda da yok** ⇒ 18 değil **16 hücre**. ⇒ **Kural:** oluşmamış hücre
`P_active`'in **paydasına girmez** ve sayısı **raporlanır**; *"inaktif"*
(alan var, `Var(z) = 0`) ile *"hiç oluşmadı"* (satır yok) **ayrı** raporlanır.

**Betimleyici olarak dört alanın hepsi ayrı ayrı raporlanır** (§3.3) — ama
birincil **yalnız `energy`**, ve sonradan alan değiştirilemez (L9).

**Sorduğu:** *yaşanmış iz, uç noktayı daha sık **ölçülebilir** yapıyor mu?*

⛔ **`P_active` bir ön-eleme filtresi DEĞİLDİR, bir sonuçtur** (D-140/U10).
Eşiği geçmek müdahaleden etkilenebilir ve bu bizde **varsayımsal değildir**.

### 3.2 Birincil B — `ΔCov_cond` (koşullu seçilim)

| | |
|---|---|
| **alan** | ⭐ **`energy`** — §3.1'deki gerekçenin aynısı, ve **aynı alan** olmak zorunda: iki eş-birincil farklı alanlarda okunursa *"nerede ölçülebildi"* ile *"nerede seçilim vardı"* farklı şeyler hakkında olur |
| **`Cov_cond(kol, tohum)`** | o kol-tohumun **aktif** geçişlerindeki `energy` Price seçilim teriminin ortalaması |
| **karşıtlık** | `ΔCov_cond(tohum) = Cov_cond(lived) − Cov_cond(shuffle)` |
| **tanımsız** | bir kol-tohumun **hiç** aktif geçişi yoksa o tohum B'den **düşer** ve **sayılır** |

**Sorduğu:** *ölçülebilir olduğu yerde, iz seçilimle ilişkili mi?*

⛔ **`Cov` İŞARETLİ kullanılır.** Mutlak değer, norm ya da `z` vektörünün
büyüklüğü **alınamaz** — ölçüldü: null'da `E[|Cov|] = 0.046` (sıfır değil) ve
gerçek fark **4.86 kat** sıkışıyor (D-142).

### 3.3 Betimleyici — test edilmez

`null` kolunun her iki niceliği · **nesil başına** Price satırları
(D-141) · `P_active`'in ham payı/paydası · `z`'nin dört ekseni (D-136) ·
`k` dağılımı (D-138) · π ve PE_w doygunluğu (D-138) · pozitif kontrol
(`energy_mean_over_life`, D-121).

⛔ Bunların hiçbirinden **sonradan** uç nokta seçilemez (L9).

---

## 4. Test — ✅ **SLOT 2 KAPALI (D-140 · D-141)**

| | |
|---|---|
| **birim** | **tohum** (Lazic 2010 — 8 ajan ve 2 geçiş **bağımsız replikat değil**) |
| **test** | eşleştirilmiş **Wilcoxon signed-rank**, **çift yönlü** |
| **α** | 0.05, ⚠ **iki eş-birincil için Holm-Bonferroni** ⇒ ilk test **0.025** |
| **etki ölçüsü** | Cohen's `d_z` = ortalama(Δ) / SD(Δ), tohumlar üzerinden |
| **güç** | 0.80 |

⚠ **Neden Holm:** iki eş-birincilden **herhangi birinde** olumlu sonuç
iddiası kurulursa hata oranı şişer. Düzeltme **koşumdan önce** ilan ediliyor
ve bedeli §7'nin MDE sütununda **görünüyor**.

⚠ **Neden Wilcoxon:** `ΔCov`'un dağılımı bilinmiyor ve `ΔP_active` üç
değerli. D-052'nin seçimiyle aynı; MDE'ye ARE = 3/π bedeli **dahil**.

### ⭐ 4.1 D-145 §6 ile çelişki — **çözüldü (Yasin, 2026-08-24)**

D-145 §6 *"bu bütçede hipotez testi yapılamaz; yapılabilecek şey kestirimdir —
p yok, α yok, Holm yok"* demişti (P7-b/D-096 damgası). §4 ise α ve Holm
diyordu. ⚠ **İki kapalı kayıt birbiriyle çelişiyordu ve §2.11 sessizce
seçilmesini yasaklıyor.**

**Karar: ikisi birden, ve rapor dili bunu zorunlu kılıyor.**

| | |
|---|---|
| test | **Wilcoxon**, çift yönlü, α = 0.05, **Holm** ⇒ ilk test 0.025 (§4 aynen) |
| ⭐ **duyarlılık** | **MDE koşumdan önce İLAN EDİLİR** (`d_z` = **0.676**, D-176) — ve **bir kapı değil bir ilandır** (D-174) |
| ⛔ **rapor kuralı** | `p` **tek başına yazılamaz**: her `p` yanında **etki büyüklüğü ve güven aralığı** gelmek zorunda. *"Anlamlı"* kelimesi CI olmadan kullanılamaz |
| ⛔ | D-145'in yapısal itirazı **ayakta**: `ΔP_active` sıfır-şişkin, dolayısıyla A'nın reddedebilme ihtimali düşük. **Bu bir sonuç olarak raporlanır**, tasarım değiştirilerek gizlenmez |

⇒ Böylece D-145'in kaygısı (*"tek bir p-değeriyle sonuç iddia etmek"*)
karşılanıyor, §4'ün kapalı slotu **yeniden açılmıyor**.

---

## 5. Geçerlilik kriterleri — koşum başlamadan sabit

Aşağıdakilerden **biri** düşerse koşum **bilgisizdir** ve öyle raporlanır;
uç noktalar **yorumlanmaz**.

| # | kapı |
|---|---|
| **V1** | ⚠ **ABORT sınıfı kapıların hepsi geçmeli.** `run_quality = clean` **şart değildir** — bak §5.2 |
| **V2** | **I4.1 replay `identical`** |
| **V3** | `PYTHONHASHSEED=0` · `TORCH_DETERMINISTIC_WARN_ONLY=False` (I0.6) |
| **V4** | I0.7 temiz başlangıç — tohum bloğu diskte adapter bırakmamış |
| **V5** | `I1.1` — her eğitim kolunda `Σ\|lora_B\|` hareket etti |
| **V6** | **`Var(F_agent) > 0`**, `lived` ve `shuffle` kollarının **her ikisinde** ve **her nesilde** |

⚠ **V6 etkiye bakmak değildir** (L9): kol **farkına** değil, seçilim
girdisinin **var olup olmadığına** bakıyor, ve kural koşumdan **önce**
yazıldı. `Var(F_agent) = 0` ise turnuva yazı-turadır ve `Cov(w,z)` seçilim
hakkında **bilgisizdir**.

⚠ **V6 `null` kolunu KAPSAMAZ** — D-129 o kolun bu nişte donmuş olabileceğini
ölçtü ve D-131 onu betimleyiciye indirdi.

### ⛔ 5.2 `run_quality = flagged` koşumu geçersiz KILMAZ (D-149)

⚠ **Bu bir düzeltmedir.** V1 önce `run_quality = clean` istiyordu. **Ölçüldü:
I5.4 gerçek koşumda FLAG basacak** — C2'de 144 varisin **0'ında** somatik
ölçek vardı. `clean` şartı, bilinen ve ilan edilmiş bir eksikliği koşumu
**geçersiz sayma** sebebine çevirirdi.

| sınıf | kural |
|---|---|
| **ABORT** kapıları | **hepsi geçmeli** — düşerse koşum **bilgisizdir** |
| **FLAG** kapıları | **raporlanır**, koşumu geçersiz kılmaz; hangisi neden bastı §8'de sınır olarak yazılı |

⛔ **Beklenen flag: `I5.4`.** Beklenmeyen bir flag çıkarsa **rapor edilir ve
yorumlanır**, sessizce geçilmez (§2.11).

### ⛔ 5.1 Kapı kapsamı — *"6/6"* **tam kapsam değildir** (D-147/AV-3)

⚠ **Bu satır bir düzeltmedir.** V1 önce yalnız *"preflight 6/6"* diyordu ve bu
**tam kapsam gibi okunuyordu**. Ölçüldü: `PREFLIGHT_INVARIANTS.md` **26**
değişmez tanımlıyor, popülasyon yolunda **6'sı** bağlı.

| durum | kapılar |
|---|---|
| ✅ **bağlı** (8) | `I0.3` · `I0.4` · `I0.6` · `I0.7` · `I1.1` · `I4.1` · ⭐ **`I4.2`** · ⭐ **`I5.4`** |
| ⛔ **bağlı değil** (18) | `I0.1 I0.2 I0.5 I1.2 I1.3 I1.3b I1.4 I1.5 I2.1 I2.2 I2.3 I3.1 I3.2 I3.3 I3.4 I5.1 I5.2 I5.3` |

⭐ **`I4.2` ve `I5.4` D-149'da bağlandı** — ve I5.4 bağlandığı anda bir kusur
buldu (§8/L20).

⚠ **`I4.2` bu koşumda FLAG, ABORT değil**, ve gerekçesi yazılı: bu koşucu
RNG'yi nesil döngüsünün **önünde bir kez** kilitliyor, multigen ise **her
nesilden önce**. Eğitimin global akışı tüketip tüketmediği **stub'la
ölçülemez** (K1(b)) ⇒ ilk koşum **ölçer**, mod sayı geldikten sonra
yükseltilir.

⚠ **`I2.1`** (*"iki kol özdeşse dur"*, ABORT) olduğu gibi bağlanamaz:
popülasyonda **gen1 tasarım gereği özdeştir** ⇒ meşru bir durumda abort
ederdi. **Uyarlanması** gerekir, ve bunu bugüne kadar kimse yazmamıştı.

⚠ Kalan 17 kapı **sınıflandırılmadı** — hangisinin N/A hangisinin eksik
olduğu **denetlenmedi**. Kilitten önce sınıflandırılır ya da *"bağlı değil,
sınıflandırılmadı"* diye **ilan edilir**. Sessizce geçilmez.

---

## 6. Okuma kuralları — koşumdan önce tanımlı

### 6.1 Sonuç sınıfları

| sınıf | koşul |
|---|---|
| **ALET NULL'I** | V1–V6'dan biri düştü ⇒ *"ölçemedik"* |
| **EVREN NULL'I** | kapılar geçti ama **`P_active` her iki kolda ~0** ⇒ evren uç noktayı üretmedi |
| **ETKİ NULL'I** | kapılar geçti, `P_active > 0`, ama `p > α` ⇒ *"şu MDE'nin altında güçsüzüz"* |
| **POZİTİF** | `p ≤ α` (Holm sonrası), her iki eş-birincil ayrı ayrı raporlanır |

### 6.2 ⛔ Anlamsız sonuç nasıl yazılır

Aşağıdaki kalıp **bağlayıcıdır** (DR #12 §5, ⚠ tohum tarifi düzeltilerek):

> *"Birincil karşıtlık `ΔX = [ort]` (SD = […], p = […], `d_z` = […]). Gözlenen
> etki, ön-ilan edilmiş asgari saptanabilir etki `d_z = [MDE]`'nin altında
> kaldığı için bu veri H0'ı reddetmeye yetmiyor. Bu **etkinin yokluğunun
> kanıtı değildir**; deneyimden doğan bir etki varsa büyüklüğü
> `d_z < [MDE]` ile sınırlıdır."*

⛔ *"Etki yok"* · *"aktarılmıyor"* · *"mekanizma yanlış"* **yazılamaz**.

### 6.3 Type S / Type M

Anlamlı çıkan her sonuç için **işaret hatası** ve **büyüklük şişmesi**
riski birlikte raporlanır (Gelman & Carlin 2014, `10.1177/1745691614551642`).
⚠ Küçük `S` + gürültülü uç noktada anlamlılık, etkiyi **abartma** eğilimindedir.

---

## 7. Bütçe ve tohum sayısı — ✅ **SLOT 3 KAPALI (D-176, Yasin)**

⭐ **İlan edilen bütçe:**

| | |
|---|---|
| **`T_max`** | **70 GPU saat** |
| **`G`** | **4** ⇒ kullanılabilir geçiş **G − 2 = 2** (D-156/B yolu) |
| **kol** | **ÜÇ** — `lived` `shuffle` `null`. ⛔ Seviye 3 tanımı gereği üç kol ister; D-173 pilotu **iki kolla** koşmuştu ve yol haritasının maliyet tablosu bu yüzden geçersizdi (D-176/Bulgu 1) |
| **`t`** (tohum başına) | ölçülen taban **2 sa 20 dk** (2 kol, G=4) ⇒ üç kolla **tahmin 3 sa 09 dk – 3 sa 30 dk** |
| **`N_eff` = ⌊q·T_max/t⌋** | **20** (muhafazakâr uçtan) |
| ⭐ **MDE `d_z`** | **0.676** — ve bu bir **ilandır, kapı değil** (D-174) |
| **tohum bloğu** | **9929+**, ardışık, taze (denetlendi: 9929–9969 arasında **0 adapter**) |
| **koşum şekli** | **parçalı**, saate dokunulmadan; gece başına tohum mümkün olduğunca çok (I4.1 replay sabit maliyeti ~35 dk/çağrı). Devam **`--resume`** ile (D-177/B2), birleştirme **`--results` N dosya** ile (D-177/B3) |

⛔ **Kaldıraç hakkı: 2**, ve yalnız **tabanı geçersiz kılan** değişiklikler
sayılır; alet onarımı harcamaz (D-176/karar 4). Sıfırlandığında yalnız **GEÇ**
ya da **DUR ve RAPORLA** kalır (D-174).

<details><summary>SLOT 3 açıkken yazılmış eski bölüm (tarihçe)</summary>

### 7-eski. Bütçe ve tohum sayısı — ⛔ SLOT 3 AÇIK

**Maliyet (ölçüldü, C2):** tohum başına **~2 saat**. ⚠ **Nişler arası yayılım
2.3 kat** (toplam olay 104 ↔ 240) ⇒ tek sayı değil **aralık** verilir (K4).

**MDE — exact noncentral-t, sonra Wilcoxon ARE = 3/π.**
⚠ Yöntem **D-052'nin sayılarıyla doğrulandı**: `N=32 → 0.5113 / 0.5232` ve
`N=40 → 0.4543 / 0.4649`, D-052'nin yazdığıyla **birebir**.

| S | GPU saat | 2.3× aralık | MDE (α=.05) | **MDE (α=.025, Holm)** |
|---|---|---|---|---|
| 6 | 12 | 8–18 | 1.468 | **1.745** |
| 8 | 16 | 11–24 | 1.183 | **1.370** |
| **10** | **20** | **13–30** | 1.019 | **1.165** |
| **12** | **24** | **16–36** | 0.909 | **1.032** |
| 15 | 30 | 20–46 | 0.796 | **0.897** |
| 20 | 40 | 26–61 | 0.676 | **0.756** |

⚠ **S ≥ 6 matematiksel şart** — altında çift yönlü Wilcoxon α=0.05'te
reddedemez.

⛔ **SESOI ilan edilmiyor** (DR #1 §G.3, Lakens 2022 `10.1525/collabra.33267`).
`S` **bütçeden** seçilir ve **MDE ilan edilir**.

**Claude Code'un önerisi: `S = 12`** — 24 GPU saat (aralık 16–36), Holm
sonrası MDE `d_z = 1.032`. Gerekçe: S=10'dan S=12'ye geçiş MDE'yi 1.165 →
1.032 indiriyor (**%11**) ve 4 saate mal oluyor; S=15'e geçmek 6 saat daha
alıp yalnız 0.897'ye indiriyor. ⚠ **Bu bir bütçe önerisidir, bilimsel bir
gerekçe değil** — kararı Yasin verir.

⚠ **MDE'ler büyük ve bu bilerek yazılıyor:** `d_z ≈ 1.0` **büyük** bir etkidir.
Bu tasarım mütevazı etkileri **göremez** ve sonuç raporunda o **ilan edilir**.

**Tohum bloğu:** taze **9916+**, ardışık. ⚠ Kullanılmışlar: …9901–9904 ·
9911–9913 (C2) · 9915 (sonda-2) · 9305–9310 (mock).

**Durma kuralı:** koşum **tek atıştır**. Kilitten sonra tohum **eklenemez**;
eklenirse analiz **post-hoc** olur. Çökme hâlinde checkpoint'ten (D-111)
**aynı tohumlarla** devam edilir, tohum değiştirilmez.

</details>

---

## 8. İlan edilen sınırlar

| # | sınır | kayıt |
|---|---|---|
| **L1** | **n = 1 deney** — tek model (Llama-3.1-8B-Instruct), tek niş ailesi, tek kod tabanı | — |
| **L2** | İddia **grup düzeyinde**; P1 ayrı popülasyon veriyor ⇒ birey düzeyi çıkarım yok | D-095 |
| **L3** | ⭐ **`z` etkin olarak TEK BOYUTLU.** Birincil eksen `k` bütün olaylarda `resource_load`'a kilitli (**192/192**, ⚠ **karar-stub'lı keşifsel koşumda** ölçüldü; gerçek koşumda `k` artık kaydediliyor ve doğrulanabilir, D-138) ve ikincil eksenler `k`'nin sabit katı ⇒ **alan kimliği hakkında iddia yok**; kovaryans drift'in **büyüklüğü** üzerine | D-136, D-137 |
| **L4** | ⭐ **Tekrarlama birimi tohum.** 8 ajan ve G−1 geçiş **bağımsız replikat değil**; ajanlar ortak merada, nesiller adapter mirasıyla bağlı | D-140, Lazic 2010 |
| **L5** | ⭐ **Uç nokta `Cov`'un İŞARETLİ hâlidir.** Mutlak değer/norm alınamaz: null'da `E[\|Cov\|] = 0.046` ve etki **4.86 kat** sıkışır | D-142 |
| **L6** | ⭐ **Type S / Type M** riski — küçük `S`'te anlamlılık işaret ve büyüklük hatası taşır | D-140, Gelman & Carlin 2014 |
| **L7** | ⭐ **Price + güç analizi birleşiminin literatürde yayımlanmış örneği yok** ⇒ taklit edilen bir çerçeve değil, **ilan edilmiş bir sentez** | D-140 (boşluk ilanı) |
| **L8** | **Price kestirimi küçük N'de** klasik beklentiden sapabilir. ⚠ *"Eşleştirme iptal eder"* gerekçesi **düştü** (işaretli kestirimci null'da yansız ölçüldü, 0.89 SE), ama Rice'ın **en genel** koşulu kapsanmadı | D-140, D-142, Rice 2008 |
| **L9** | ⛔ **Hiçbir uç nokta etkiye bakılarak seçilmez.** Betimleyici alanlardan sonradan uç nokta türetilemez | süregelen |
| **L10** | **G = 4** (D-161 ile 3'ten yükseltildi — ölçüldü: `G = 3`'te kullanılabilir tohum **0/3**, `G = 4`'te **2/3**). DR #11'in *"8 nesil"* normatifi **hâlâ reddedildi**; birikimli kalıtım iddiası kurulamaz. ⚠ Ve YENİ-4 ile kullanılabilir geçiş **G − 2 = 2** | D-132 §T.2, **D-161** |
| **L11** | **Adapter sönümü / LoP** — 6/6 dizide 1.8×–4.8× azalma ölçüldü; uzun soyda sinyali **seyreltebilir**. Nesil satırları bunu **raporlar ama test etmez** | D-132, D-141 |
| **L12** | **`null` kolunda sürüklenme ile seçilim ayrılamaz** — bu nişte donmuş klon popülasyonu olabilir ⇒ **betimleyici** | D-129, D-131 |
| **L13** | ⭐ **Aktif hücre oranı düşük** (C2'de ~%22) ⇒ `Cov_cond` az hücreye dayanır; ⚠ ve **aktif hücreye koşullamak survivorship bias taşır** — eşiği geçmek müdahaleden etkilenebilir | D-143, D-140/U10 |
| **L14** | **Kriz müdahale-sonrasıdır** ve bütün kola **aynı anda** vurur ⇒ `z`'nin `resource` bileşeni hücre içi bilgi taşımaz | D-119/120, D-130 |
| **L15** | **I0.1/I0.2 popülasyon yolunda bağlı değil** | D-105 |
| **L16** | **GAP-10 / spillover skaler kalıyor.** Matris `k` sabit olduğu için skalerin üç kopyalı hâli olurdu; eşiği de geçirmiyordu (+%2.29) | D-137 |
| **L17** | **`to_landmark.max` reddedildi** ve bu koşumda **kullanılmaz**. ⭐ **Üç şart yerine getirilerek YENİDEN AÇILDI, taze veriyle sınandı ve YİNE reddedildi** (D-154 ön-taahhüdü → D-155): sonda `shuffle` içeriyordu, kural koşumdan önce yazılmıştı, ve D-129'un sayıları yeniden okunmadı. Sonuç **yine 2/4** (kural ≥ 3/4). ⇒ **Kapalı soru**; bir daha açılmaz | D-143 §5, **D-155 §1** |
| **L18** | **Davranış çökük** — olayların %94–100'ünde DEFECT; K7 bilişsel önseli aksiyom gerekçesiyle kapattı ve bu **açık risktir** | D-068, D-074 |
| **L19** | **GAP-4'ün ikinci yarısı** (silinen anının LoRA izi) **açık** | GAP tablosu |
| **L20** ⭐⭐ | ⛔ **Sembolik kanalın somatik yarısı varise HİÇ ULAŞMIYOR.** C2'de 144 varisin **0'ında** somatik ölçek, **0'ında** miras uyarısı vardı — buna karşılık **anılar geçti** (varis başına ~10, `n_inherited_by_parent` ort. **9.74**) ve **adapter geçti** (96/144 = eğitim alan iki kol). ⇒ Kanal 1'in **engram yarısı çalışıyor, somatik yarısı çalışmıyor** (GAP-3).
⭐ **D-150 kökü buldu:** uyarı **iki bantta** doğuyor — `f < 0.35` ya da
`f ≥ 0.70`. C2'de **alt bant 0/216** (eşik dağılımın **tamamının** altında,
min 0.3919 — D-086 `F_agent`'ı 0.14→0.45 taşımış, eşik geri dönülmemiş) ve
üst bant **12/216**, ki travmayla aynı yaşamda buluşması ≈ **%0.6**.
⇒ **Alt bant yapısal olarak ölü, üst bant canlı ama nadir** — iki farklı sorun.
✅ **D-152 düzeltti — ve hiçbir eşik değeri değişmeden.** Bantlar artık
**göreli**: eşikler hücre içi min-max konumuna uygulanıyor (D-088'in deseni —
*"çıta kalibre edildiği niceliğe uygulanır"*). C2'nin yayılımıyla iki ölü bant
**canlandı**. ⚠ **Bedeli ilan edildi:** min-max her hücrede birini `low`
birini `high` yapar. ⚠ **Ve GAP-3 tam kapanmadı** — bant ateşlenebilir oldu,
ama zincirin geri kalanı hâlâ `is_trauma` eşiğine bağlı; darboğaz **bir adım
ileri taşındı** ve I5.4 gerçek koşumda ölçecek. ⚠ Ve C2 bunu `run_quality = clean` diye raporladı, çünkü **I5.4 bağlı değildi** — D-149'da bağlandı ve ilk koşumda **FLAG** bastı.
⛔⛔ **SONDA-3 ÖLÇTÜ VE D-152'NİN TAHMİNİ ÇÜRÜDÜ (D-155 §2):** bugünkü fizikle,
göreli bantlarla koşulan taze veride **32 varisin 0'ında** somatik ölçek,
**0'ında** miras uyarısı — `I5.4` yine `never applied`. ⚠ Ama zincirin
**hangi halkasının** tuttuğu ölçüldü: göreli bant **çalışıyor** (48 yaşamın
10'u `low`, 15'i `high`), travma eşiği **48/48** aşılıyor, ve `low` bant
ajanı **üreyebiliyor** da (w = 3/1/1). ⇒ Kırılma **bandın arkasında** ve
kalan şüpheli `select_for_transfer`'ın recall/`is_trauma` şartı — ⚠ **çıkarım,
ölçüm değil** (kuyruk 2.5).
⛔⛔ **L20'NİN SONUÇ CÜMLESİ ARTIK YANLIŞ — D-179'da yakalandı, kilitten
önce.** Yukarıdaki *"somatik yarı AKMIYOR"* okuması **eski fizikten**. Bugünkü
fizikte ölçüldü:

| koşum | `I5.4` |
|---|---|
| C2 (eski fizik) | 144 varişte **0** |
| sonda-3 (eski fizik) | 32 varişte **0** |
| ⭐ **D-161** | **34/144** — kanal varise **ulaşıyor** |
| ⭐⭐ **D-173 pilotu (bugünkü fizik)** | ✅ **geçti — `applied 463x`** |

⇒ 🔒 **Bu koşum için GEÇERLİ sınır:** somatik kanal **akıyor**, ama ⚠️
**birinci varis kuşağında yapısal olarak sıfır** ve **tohuma çok bağlı**
(D-161). ⇒ Aksiyomun *"iki kanal"* iddiasının bu yarısı **test ediliyor, ama
kapsamı sınırlı**. | **D-149**, **D-155**, ⭐ **D-161**, **D-173**, **D-179** |
| **L22** ⭐ | ⛔ **BÜTÇE SANSÜRÜ.** Yaşamlar `--events 30` tavanına dayanıyor ve dayanma oranı nesille **artıyor**: tavandaki ajan gen1'de **2.0/8**, gen3–4'te **5.2/8** (D-176/Bulgu 6). ⇒ Geç nesillerde yaşamların çoğu **ölümle değil bütçeyle** bitiyor. ⚠️ **Ölçüldü ve `F_agent` yayılımını ÇÖKERTMİYOR** — korelasyon **+0.283**, yayılım 0.114 → 0.190 **büyüyor**, `w_variance` hep > 0. ⇒ Sınır **ilan ediliyor**, sabit **değiştirilmiyor** (§2.7) | **D-176** |
| **L23** ⭐ | ⛔ **UYKU KONSOLİDASYONU YOK.** `run_consolidation`'ın popülasyon yolunda çağrısı yok ⇒ ilişki grafiği boş, **Ebbinghaus budaması ve güçlendirme çalışmıyor**. ⚠️ **Kanal 1'in kendisi ölü DEĞİL** — `consolidate_generation` çağrılıyor ve `I5.4` geçiyor; eksik olan **yaşam içi** bir bellek dinamiği. ⇒ Eksiklik **her kolda simetrik**, dolayısıyla seviye 3 karşıtlığını oynatamaz. `I5.1` bu yüzden **`None`** raporluyor (*"değerlendirilmedi"*), `False` değil | **D-172**, **D-178** |
| **L24** ⭐ | ⛔ **`resource` alanı hiçbir hücrede tanımlı değil** — D-173 pilotunda **9 satırın 9'unda `z_variance = 0.0`**. L14'ün confound'unun ölçülmüş hâli. ⇒ Birincil alanın `energy` olması artık **türetilmiş değil ölçülmüş**, ama bedeli de açık: **kriz kanalı `z`'ye bilgi taşımıyor** | **D-179** |
| **L25** ⛔⛔ | **L9 BİR KEZ İHLAL EDİLDİ VE İLAN EDİLİYOR.** 2026-08-24'te `ΔP_active` D-173 pilotunda hesaplandı (3/3 tohumda **0**, tavan etkisi). ⇒ Bu ön-kayıt *"birincil A kör seçildi"* **diyemez**; diyebileceği şey: **tanımı bu okumadan ÖNCE (D-143/D-144) kilitlenmişti ve okumadan SONRA değiştirilmedi** (karar: Yasin). ⭐ Yasak artık bir **kapıya** bağlı: `analyze_population_run` kilit alınmadan seviye 1–3'ü **raporlamayı reddediyor**, ve izni **bu belgeden** okuyor. ⚠️ **Kapının sınırı da ilan ediliyor:** ad-hoc betiklerde geçerli değil — ihlal zaten öyle olmuştu | **D-179** |
| **L21** ⭐ | ⛔ **Kurucu nesil hakkında hiçbir iddia yok** (YENİ-4). Price yalnız ebeveyni gen ≥ 2 olan geçişlerden okunuyor ⇒ tasarım **birinci nesildeki seçilim hakkında sessizdir**, ve bu bir bulgu değil **kapsam kısıtıdır**. ⚠ **Ve B tek başına tanımlılığı kurtarmıyor:** eski fizikte kurucu nesil atıldıktan sonra bile birincil alanda (`energy`) `ΔCov` **0/3 tohumda** tanımlı olurdu (D-157 §2). Bugünkü fizikte karşı-veri var ama **n = 1** | **D-156**, **D-157** |

---

## 9. Slotlar

| # | Slot | Durum |
|---|---|---|
| **1** | Uç noktalar (`ΔP_active` + `ΔCov_cond`) | ✅ **KAPALI** — D-143, D-140 |
| **2** | Test, α, düzeltme, etki ölçüsü | ✅ **KAPALI** — D-140, D-141 |
| **3** | **Tohum sayısı `S` ve bütçe** | ✅ **KAPALI** — D-176 (`T_max`=70 sa · `G`=4 · 3 kol · `N_eff`=20 · MDE 0.676) |
| **4** | Geçerlilik kapıları (V1–V6) | ✅ **KAPALI** |
| **5** | Sonuç sınıfları ve rapor dili | ✅ **KAPALI** |
| **6** | Alet kimliği | ⏳ **kilitte donacak** (§12) |

---

## 10. Sapma politikası

Koşum sırasında ön-kayıttan sapma gerekirse: koşum **durdurulur**, sapma
`DECISIONS.md`'ye **gerekçesiyle** yazılır, ve sonuç **keşifsel** damgalanır.
⛔ Sapma sessizce uygulanmaz (§2.11).

Çökme/OOM **sapma değildir**: checkpoint'ten aynı tohumlarla devam edilir.

---

## 11. Null sonuç politikası

**Null meşru bilimsel çıktıdır ve gizlenmez** (5 Değiştirilemez Yasak).
Sonuç ne olursa olsun `docs/C3_RESULTS.md` yazılır; §6.1'in sınıfı ve §8'in
sınırları **rapora aynen taşınır**.

⚠ **C2'nin dersi:** *"ölçemedik"* ile *"ölçtük, yoktu"* farkı bu ön-kayıtta
`P_active` sayesinde **tek bir sayıyla** kuruluyor — bu, üçüncü ön-kaydın
C2'ye göre asıl kazancıdır.

---

## 12. Alet kimliği — ⏳ kilitte dondurulacak

Kilit anında (kuyruk 2.3) buraya yazılacaklar: commit hash · `tool_identity`
çıktısı · model kimliği ve quantization · `constraints.py` özeti ·
`pip freeze` özeti · suite sayısı.

---

## 13. Koşum komutu — kilitte tam olarak yazılacak

⚠️ **D-176/D-177'ye göre güncellendi** (eski hâli `G=3`, iki kol ve tohum
bloğu 9916 diyordu — üçü de geçersiz).

**Gece başına bir çağrı**, tohum bloğu ardışık bölünür:

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9929 9930 9931 9932 9933 --n-agents 8 --n-generations 4 --events 30 \
  --lora --fresh-pasture --arms lived shuffle null \
  --results dau_runs/c3_population_n8_g4_night1.json
```

Kesilirse **aynı komut + `--resume`** (D-177/B2). Bütün geceler bitince:

```
python -m dau.diagnostics.analyze_population_run \
  --results dau_runs/c3_population_n8_g4_night*.json \
  --out docs/C3_RESULTS_report.md
```

⛔ Birleştirici **çakışan tohumu**, **uyuşmayan aleti** ve **checkpoint**'i
reddeder (D-177/B3). ⛔ Ve kilit alınmadan **seviye 1–3'ü raporlamaz**
(D-179/L25).

⚠ **Dış `timeout` YOK** (D-126: I4.1 replay sırasında kesilirse sonuç dosyası
hiç yazılmaz). ⚠ `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez** (D-116).
