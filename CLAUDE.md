# DAU (Dynamic Agent Universe) — Claude Code Authority Document

## Belge Düzeni (D-001)

| Dosya | İşi | Yazma modu |
|---|---|---|
| `CLAUDE.md` (bu dosya, kök) | geçerli kurallar + açık GAP'ler, kısa | üzerine yazılır |
| `docs/DECISIONS.md` | karar kaydı: ne/ne zaman/neden/**kanıt** | **append-only** |
| `docs/EXECUTION_PLAN.md` | adım ayrıntısı, dur-kontrol, adım durumu | adım bitince ✅ + hash |
| `docs/DAU_MASTER_REFERENCE_v20.md` | bilimsel anlatı, formüller, empirik tablo | sürüm sürüm |

Bu dosya Claude Code'un her oturum otomatik yüklediği otorite belgesidir —
**kısa tutulur**, ayrıntı `DECISIONS.md`'ye gider. Çelişki durumunda bu dosya
geçerlidir, ama çelişkiyi açıkça belirt ve kullanıcıya sor — sessizce birini
seçme.

**Kural:** Kanıtı olmayan hiçbir madde "kilitli karar" olarak yazılmaz.
Kilitli her madde bir `D-0XX` kaydına işaret etmelidir.

---

# 1. Şu An Neredeyiz (2026-08-12, gece) — ⏳ **DR CEVABI BEKLENİYOR**

- **Branch:** **`main`** tek branch (D-013 kapandı, **D-054**). `origin` ile
  senkron, push edildi. Eski main `archive/main-pre-c116` etiketinde.
  B2'nin koştuğu kod **`prereg/b2-code`** etiketinde.
- **Suite:** `384 passed, 2 deselected`. Çalışma ağacı temiz.
- **Son D-kaydı: D-068.** Sıradaki kayıt **D-069** olarak açılır.
- **A yolu bitti (W1 ✅ · W2 ✅ · W3 ✅).** **B yolu da bitti:** DR #4
  cevaplandı, mutabakat §J yazıldı, kaynak kimlikleri denetlendi (D-065).
- ✅ **A4-① uygulandı (D-066):** hasat enerjiye dönüyor (içbükey kazanç),
  defter teslim edileni yazıyor, tükenmek öldürüyor. ⚠ **Evrenin fiziği
  değişti — `dau_runs/`'daki hiçbir koşum bugünün aletiyle karşılaştırılamaz.**
- ✅ **GAP-19 kapandı (D-067)** — kasa nerede kaldığını hatırlıyor; kasaya
  giren her sayaç faz-yerel, çeviriyi yalnız kasa yapıyor. D-051'in *"ikisi
  birlikte ya da hiçbiri"* şartı ödendi.
- ✅ **Pilot koşuldu (D-068, N=2).** ① **mekanik olarak çalıştı:** ölüm var
  (yaşamlar 19 ve 10 olay), **sınıf bariyeri kırıldı** (`low` 0.208 vs
  **`normal` 0.413**; B2'de 120/120 `low`), `Δhavuz` 130.8 vs 62.2 (B2: ±%0.7),
  bedel zinciri uçtan uca ateşledi (havuz çökünce hasat 8.0→6.17→0), ve
  **yaşam uzunluğu kola göre değişti** (gen2: `lived` 17, `null`/`shuffle` 20).
- ⏳ **SIRADAKİ İŞ — üç açık karar, üçü de Yasin'in:**
  ① **Ölçüm penceresi:** sabit 50 olay, ölümün mümkün olduğu evrende
  çalışmıyor (gen1'de **%71 padding**, alet *"arm not measurable"* diyor).
  ② **Enerji okuma anı:** `E_final` hâlâ 0.000 — formül değil **seçilim**
  yüzünden (tükenerek ölenin son enerjisi sıfırdır). `F_agent`'ın 0.4
  ağırlığı hâlâ bilgi taşımıyor.
  ③ **Davranış hâlâ çökmüş:** hasat neredeyse hep 8.0 (DEFECT); evren bedeli
  kesiyor ama ajan davranışını değiştirmiyor. **D-065/J4 (GovSim) tam bunu
  rapor ediyor** ve ölçülmüş tek kaldıraç bilişsel önsel ⇒ **A4-③ artık
  spekülatif değil.**

## ▶▶ SIRADAKİ İŞ — iki dal, hangisi geçerliyse

⚠ **DR raporu her an gelebilir.** Yasin'in DR hakkı tükendi, ~3–4 saat
bekleme var (2026-08-12 gecesi). O gelene kadar **A yolu** koşulur; rapor
sunulduğu anda **B yolu** öne geçer ve A yarıda bırakılabilir (üçü de
bağımsız iş, yarım kalan zarar vermez).

### ▸ A yolu — rapor gelmeden yapılacak üç iş, **bu sırayla**

Üçü de DR cevabından bağımsız ve ikinci ön-kayıt için zaten gerekli.
Yasin onayladı (2026-08-12). ⚠ **W** öneki bilerek: Faz A'nın **A1–A8**'i
ayrı iştir ve **A4 = environment ayrımı**, karıştırma.

| # | İş | Süre | Neden şimdi |
|---|---|---|---|
| ~~W1~~ | ✅ **D-062** — confound *tarif edildiği biçimiyle* **yok** (PE ↔ token başı olabilirlik ρ=+0.063, p=0.37; uzunluk kontrollü kısmi +0.044). **Ama D-059 Bulgu 4 seed-kararlı değil:** seed bazında 2 seed `lived` lehine, 1 seed **tersine**, 1 seed sıfır. Confound'un yeri değişti: **uzunluk → taban marj → kayıp farkı**. Yan bulgu: eğitim dizilerinin **%85.5'i 512 tavanında kesiliyor** ve sohbet şablonu başlığı kayboluyor (D-027'nin gerekçesi o dizilerde bozuluyor) | — | ✅ |
| ~~W2~~ | ✅ **D-063** — S5 aletlendi (`pool_step_node` hasat + `pool_ratio` + kriz bayrağını `pe_event_log` desenine yazıyor; `Gen2Result` altı yeni alan). ⚠ **İki travma okuması bilerek** (§2.11): commons krizi ≠ `TRAUMA` sınıfı imprint, ön-kayıt hangisi olduğunu söylemiyor. **S6 kol olarak üretilmedi:** denetim birincilin `F_agent`'ı **hiçbir yoldan göremediğini** gösterdi (birth-drift ebeveyn drift'inin kopyası, `select_for_transfer` drift'i yalnız okur) ⇒ Yasin **gölge kayıt** seçti | — | ✅ |
| ~~W3~~ | ✅ **D-064** — 21 aday sıralandı. **Dördü yapı gereği kör:** `gen1 n_unique`/`pe_gap_max` faz-1'den geliyor (adapter'dan önce) ⇒ 40/40 seed'de üç kol özdeş; `f_agent`/`fitness_class` 120 kolda tek değer. **Birincilin dökümü:** `resource` 120/120 kolda ama 38/40 seed'de kollar özdeş, ayırt etme gücünü **`social`** taşıyor ve `social` kolların **%42.5'inde hiç yok** — `lived`=`shuffle` olan 11 seed'in 7'si tam da `social`'ın hiç açılmadığı seed'ler. En yüksek çözünürlük: `arm_digest`/`delta_pe`/yörüngeler (120/120 farklı) ⚠ **ama çözünürlük ≠ duyarlılık** (D-044) | — | ✅ |

### ▸ B yolu — Yasin raporu sunup "devam et" dediğinde

1. **`docs/research/2026-08-12_environment-differentiation-and-selection.md`**
   okunur — gönderilen brief odur, altı soru (S1–S6) orada.
2. **Mutabakat tablosu üretilir** (§9 / D-006, zorunlu): her iddia için
   *brief ne diyor / kod ne yapıyor / karar ∈ {bilinçli sapma · fark
   edilmemiş kayma · uyumlu · brief yanılmış}*. Çıktı
   `docs/research/RECONCILIATION.md`'ye **§J** olarak eklenir.
3. ⚠ **Kaynak kimlikleri kontrol edilir.** Geçmişte altı kaynak yanlış
   atfedilmişti; brief bu yüzden yazar+yıl+DOI istedi. Doğrulanmamış kaynak
   **kullanılmaz**.
4. Sonra **A4 tasarım kararı** (aşağıda), Yasin'in onayıyla.

**Bekleyen karar — A4'ün hangi kaldıracı çevireceği (D-007, Yasin'in):**

| Seçenek | Kanıt | Maliyet |
|---|---|---|
| **① Metabolik döngüyü kapat** — çıkarım enerjiyi beslesin, enerji bitince ölüm | Fitness'ın %70'i (enerji 0.4 + survival 0.3) canlanır. ⚠ D-061: toparlanma terimi **yeniden tasarlanmalı**. ⭐ **D-065/J9 biçimi verdi:** kazanç eğrisi **içbükey** olmalı (doğrusal *"çıkarım = enerji"* defect'i baskın bırakır) | orta, orkestrasyon değişmiyor |
| **② Popülasyon** (D-014 / L2) | Tek gerçek Darwinci yol; farklı üreme olmadan seçilim iddiası kurulamaz. **D-065/J16:** üstüne MAP-Elites gelebilir | en büyük iş |
| **③ Prompt priming'i kaldır** (L14) | ⚠ **D-065 ile karıştı:** J4 (GovSim) prompt düzeyindeki **karar kuralı** önselinin ölçülmüş bir kaldıraç olduğunu gösteriyor; J6 ise **persona** zenginleştirmenin çeşitlilik satın almadığını. Yine de bedel yokken tek başına yetmez, ve her koşumu geçersiz kılar | ucuz ama yıkıcı |

**Claude Code'un önerisi değişmedi: ① önce, sonra ②.** Artık iki bağımsız
dayanağı var: kendi ölçümümüz (② tek başına çalışmaz — N ajanın hepsi aynı
baskın stratejiyi oynarsa fitness'ları yine özdeş olur) ve **DR'nin bağımsız
aynı sıralaması** (D-065/J20).

✅ ① `F_agent`'a dokundu ve **GAP-19 aynı gün düzeltildi** (D-067) —
D-051/L16'nın şartı ödendi.

⚠ **①'in içinde üç alt karar var, üçü de sessizce alınmayacak (§2.3):**
kazanç eğrisinin **biçimi** (içbükey — hangi aile?) · **ölüm eşiği** olacak mı
(J10: yön uyumlu, kaynağı doğrulanamadı; erken ölüm N hesabına girer) ·
`METABOLIC_FLOOR`'un **çifte rolü** (aynı sabit hem asgari tüketim hem azami
toparlanma — D-061'in kökü) ayrılacak mı.

## ✅ B2 sonrası ne öğrenildi (D-055…D-061)

| Kayıt | Bulgu |
|---|---|
| **D-055** | `run_vram_spike.py` çalışmaz (sarmaladığı üç fonksiyon yok) ⇒ bu branch'te **VRAM aracı yok** |
| **D-056** | **Uç noktanın %99'u sabit.** `resource` 120/120 kolda, kollar arası fark 40 seed'in **38'inde sıfır**. 11/40 seed'de `lived`=`shuffle` **birebir** ⇒ orada mükemmel adapter bile görünemezdi. Kalan 29'da `\|a−b\|` ort. 0.444 ama **işaret +15/−14** ⇒ büyük hareket, rastgele yön |
| **D-057** | Eğitim girdileri diske yazılıyor (`DAU_DUMP_TRAINING_ARTIFACTS`) ⇒ sweep artık yaşamları yeniden koşmuyor |
| **D-058** | Sweep sürücüsü + **devam ettirilebilirlik** (`sweep_dpo_hyperparams.jsonl`) |
| **D-059** | ⚠ **Kırpma kaldıraç DEĞİL.** Tavanı 1→10 (kırpma %100→%0) kaybı hiç değiştirmiyor — AdamW ölçeğe duyarsız. **L18'in gözlemi doğru, çıkarımı yanlıştı.** Kaldıraç `lr`: kayıp 0.694→**0.651**, bastırma yok. **Parametrik kanal öğrenebiliyor** |
| **D-060** | **A4 formül düzeltmesi değil.** `f_agent`=0.000 · `energy`=0.000 · `fitness_class`=`low` 120/120 · `Δpool` yayılım %0.7. Birim hatası düzeltilse bile **120 kolun hepsi aynı sınıfa** düşüyor |
| **D-061** | **Enerji yapı gereği asla artamıyor** (cebirsel kanıt: `decay ≥ recovery` her zaman). 2. olayda tabana vuruyor, yaşamın %96'sı sıfırda |

**Kök neden (D-060 §2.3):** ajanlar olayların **%94–100'ünde** en yüksek
çıkarımı seçiyor, çünkü **defect'in bedeli yok** — çıkarım enerjiye dönmüyor,
havuz çökünce kimse ölmüyor. Ayrım üretmeyen evrenin sebebi bu.

## ⬜ Açık kalan iş

| İş | Not |
|---|---|
| ~~Sahte-PE kontrolü~~ | ⇒ **W1 oldu**, yukarıdaki A yolunda |
| **İkinci ön-kayıt** | A4 kararından sonra. Girdiler: `lr` bandı (D-059), KTO kararı (GAP-18: `uniq_rejected` 100/94), uç nokta seçimi (D-056 + **D-064 envanteri**). ⚠ **S5/S6 artık aletli (D-063)** ama iki karar açık: S5'in **hangi travma okuması** (kriz mi `TRAUMA` imprint mi) ve S6'nın gölge kanalı **hangi testle** sınanacak. ⚠ **D-064'ün açtığı üçüncü karar:** birincil vektör olarak mı kalsın, yoksa taşıyıcı kanalın (`social`) varlığı **geçerlilik ön-koşulu** mu olsun — tasarım kararı (D-007), B2 verisine bakarak verilemez |
| **13.3 saatlik doğrulayıcı koşum** | ⚠ **Kilit yazılmadan başlanmaz** |

## ✅ B2/B3/B4 BİTTİ — sonuç `docs/B2_RESULTS.md`'de

**Koşum:** seed 2004–2043, N=40, iki batch, `--lora` · toplam ~13.1 saat ·
çökme yok · `tool_identity` ön-kayıt §12 ile **birebir**.

| Ne | Sonuç |
|---|---|
| **Birincil** (§3) | `a_s − b_s` ort. **−0.0002** · W=217.0 · **p = 0.9914** · `d_z = −0.000` ⇒ **H0 reddedilemedi** |
| Çözünürlük | `‖lived−shuffle‖` **0.3852** ≈ `‖lived−null‖` 0.3812 ≈ `‖shuffle−null‖` 0.3814 ⇒ üç kol **eşit uzaklıkta** |
| **§11 sınıfı** | **ALET NULL'I** — §5'ten üç kriter düştü (D-053) |
| S1 (FFH) | p = 0.877 · S2 (KW) p = 0.726 · **S3** p = 0.070 (+, yön H1'le uyumlu) · **S4** p = 0.035 (**ters yönde**) |
| S5 / S6 | **KOŞULMADI** — S5'in verisi JSON'da yok, S6'nın kolu üretilmedi (L20) |
| `run_quality` | **flagged** (iki batch), 23/24 kapı, bayrak `I1.3b` |
| Kırpma | **%100**, `grad_norm_min ≈ 2.96` vs tavan 1.0 ⇒ **L18** |
| `dpo_loss` | 0.6919 / 0.6940 — **ln 2 = 0.6931**, tercih marjı ≈ 0 |
| `delta_logp_chosen` | **+0.064, 18/20 pozitif** ⇒ bastırma **değil**, D-049'un failure mode'u tekrarlanmadı |
| GAP-18 | `uniq_rejected` **100 / 94** · `uniq_chosen` 1025 / 971 · `max_rejected_reuse` 47 / 45 |

⚠ **İddia edilemeyecekler** (rapor §7): *"aktarılmıyor"* (D-047 yasakladı) ·
*"mekanizma yanlış"* (alet null'ı) · *"adapter davranışı değiştiriyor demek
ki bir şey aktarılıyor"* (**`shuffle` de aynı ölçüde değiştiriyor**: 26.6 vs
26.1 / 50) · *"S4 anlamlı, en azından sinyal var"* (ters işaret, medyan 0,
§4 önceden bağladı).

**Bu null'ın değeri:** neden göremediğimizi **ölçtük**. Kırpma doygunluğu ve
`dpo_loss ≈ ln 2`, bir sonraki koşumun neyi düzelteceğini tahminle değil
sayıyla söylüyor.

## ▶ İKİNCİ ÖN-KAYIT — kilitten sonra biriken her şey buraya

Kilit kapandığı için aşağıdakilerin **hiçbiri** bu koşuma giremez.

| İş | Nereden geldi |
|---|---|
| **A2 — kanal ayrımı, plasebo anı enjeksiyonu ile** | ⚠ Eski tasarım ("getirimi tamamen kapat") **kusurluydu**: OOD şoku ölçer, parametrik kapasiteyi değil (D-049/I12) |
| **Çifte ayrışma protokolü** (`ΔE_ağırlık + ΔE_bellek ≈ ΔE_toplam`) | DR #3 / I15 — kanal ayrımı iddiasının literatürdeki çıtası |
| ~~**`F_agent` + GAP-19 birlikte**~~ | ✅ **ikisi de yapıldı** — D-066 (`F_agent` girdileri) + D-067 (kasa saati), aynı gün, D-051'in şartına uyularak |
| **A4 — environment'ı ayrım üretir hale getirme** | Faz A'da bilerek ertelendi |
| **KTO'ya geçiş** | DR #2 baş tavsiyesi. ⚠ Doğrulanmamış premise dayanıyordu; **B2'nin `uniq_rejected` sayısı** karar verir |
| **Zaman × kol etkileşimi (LMM/FDA)** — **genel form** | DR #3 / I17. ⚠ "ikinci yarı AUC" **özel formu alınmaz** — o D-045'te gözlediğimiz şey, post-hoc olur |
| **`W_SEM` 0.0 → 0.3–0.4** · negation sarmalayıcı · asimetrik spillover | GAP-10, üçü de L8'de sınır olarak duruyor |
| **Precision-PE `VAR_REF`** | L13 — π tavanda takılı, mekanizma atıl |
| **`SYSTEM_PROMPT` lexicon** | L14 — davranışsal sınıflandırıcıyı besliyor |
| **Popülasyon / N nesil** | **D-014**: hedef N nesil, gen1→gen2 en kısa çalışabilir biçim |
| **`DPO_MAX_SEQUENCE_TOKENS` yeniden değerlendirmesi** | **D-062** Bulgu 4: dizilerin **%85.5'i** 512'de kesiliyor (tam uzunluk medyan 894), ve kesme prompt'un başından olduğu için **sohbet şablonu başlığı + BOS gidiyor** ⇒ D-027'nin *"eğitim=çıkarım biçimi"* gerekçesi o dizilerde geçersiz. ⚠ Kilitli sabit, bu koşumda dokunulmadı |
| **Uzunluk kontrolü (çift kurma)** | **D-062** Bulgu 2: `chosen` ort. 57.2 vs `rejected` 38.7 token, seed'e göre fark −4.6 … +42.1. DPO **toplam** logp kullandığı için uzunluk doğrudan marja giriyor; taban marjın seed'ler arası %100↔%7 salınımının açıklaması bu |
| **Magic number kalıntıları** | `time.sleep(10)`, bare `0.5`, `k: int = 5`. **Cursor'a uygun** |

## ⚠ Bugün öğleden önce dört alet değişikliği daha girdi

| Kayıt | Commit | Ne |
|---|---|---|
| **D-039** | `b82bdf9` | **I1.1 kapısı** — `Σ\|lora_B\|` eğitim öncesi/sonrası. Belgede vardı, kodda yoktu; `CLAUDE.md` §6 "regresyon testinde" diyordu ve **yanlıştı** |
| **D-040** | `0c61b0e` | **Shuffle %100 ters.** %50 yazı-turanın kaydı yoktu (`f8aabf3`, Cursor toplu commit'i). Gerçekleşen bozulma seed'e göre +%15 … −%21 salınıyordu |
| **D-041** | `3b16bba` | **I4.1 replay kapısı** — bir kolu ikinci kez koşup `arm_digest` karşılaştırıyor. Maliyet ~7 dk/koşum |
| **D-042** | `e89404a` | **Adapter graft'ı artık konumdan bağımsız** — `fork_rng` + sabit `LORA_INIT_SEED`. I4.1'in ilk canlı koşumda yakaladığı kusur |

**D-042 küçük değildi:** `lived` daima 1. sırada taze graft'tan, `shuffle`
daima 3. sırada bir kez eğitilip sıfırlanmış olandan eğitiliyordu ⇒ birincil
karşıtlığın içinde her koşumda aynı yönde çalışan **sistematik** bir terim.
Ölçüldü: aynı shuffle kolu konum 1'de `598d67bce291`, konum 3'te
`43930cf5013b`. Düzeltmeden sonra beş kolluk sonda ile doğrulandı.

⚠ **D-034…D-038'in bütün digest'leri ve `lived − shuffle` sayıları geçersiz.**

## ✅ Kontrol koşumu 20/20 (D-043)

`dau_runs/control_d042_n3_local.json` · `run_quality=clean` · I4.1 ilk kez
otomatik geçti · üç `null` kolu D-038'le **byte düzeyinde aynı**, altı eğitim
kolu farklı (D-042'nin yalnız eğitim yolunu değiştirdiğinin kanıtı).

Sinyal (keşifsel, N=3): `lived − null` **3/3 pozitif** (ort. +0.0312) ·
`lived − shuffle` tutarsız (−, +, +). ⚠ D-042'yi bulduğumda tutarsızlığı
onun açıklayabileceğini söylemiştim; **ölçüm desteklemedi.**

## ✅ A1: ΔPE uç noktası kayıplı çıktı (D-044)

Ham izlerden, **GPU'suz**: faz-2'de kollar olay bazında 0.065–0.194
ayrışıyor ama faz ortalaması bunun yalnız **%14–20**'sini görüyor. İptal
simetrik (işaretlerin %44–64'ü pozitif) ⇒ adapter ajanın **neye şaşırdığını**
yeniden düzenliyor, ortalama şaşkınlık düzeyini kaydırmıyor.

Uç örnek: seed 2003 `lived−shuffle` uç noktası +0.00073 ("fark yok"), ham
ayrım **0.094** — %99.2 iptal. Yani D-043'teki "tutarsızlık"ın en az bir
parçası **iptal artefaktı**, küçük etki değil.

⇒ Birinciliği doğum-driftte tutmayı **destekliyor** (o bir anın vektörü,
ortalama alınmıyor). ΔPE ikincilleri (S3/S4) için `PREREGISTRATION.md` **L9**
sınırı yazıldı: null çıkarlarsa "ölçemedik" diye raporlanır.
⚠ Yörünge tabanlı uç nokta bu veride çok daha büyük etki gösteriyor ama
**alınmadı** — ölçümü görüp istatistik seçmek post-hoc olurdu (§2.7).

## ✅ A5: gen2 uç noktası da kayıplı (D-045)

D-044'ün açık bıraktığı soru kapandı, **GPU'suz**. Korunan pay
`lived−null` **%17.5** (gen1: %19.6) · üç çiftin ortalaması %26.7 (gen1
%18.4). ⇒ **S4 null çıkarsa "ölçemedik"**, S3 ile aynı. `PREREGISTRATION.md`
**L10** yazıldı; §11 artık iki ikincil için de "ölçüldü, varsayılmadı" diyor.

⚠ **Ama gen2'nin iptali gen1'inki gibi simetrik değil.** Bağımsız altı
karşıtlığın **beşinde** yaşamın ikinci yarısı daha pozitif (kayma
0.056–0.155; gen1'de 4/6 ve 0.003–0.070 — bir mertebe küçük). Kol bazında
kaynak: iki seed'de **`null` varisinin PE'si ikinci yarıda çöküyor**
(−0.254 / −0.143), `lived`'inki çökmüyor (+0.032 / +0.059).
Adaylar **GAP-19** (paylaşılan sayaç uzayı ⇒ Ebbinghaus) ve **GAP-3**.
⚠ GAP-19 o gözlemden sonra **kapandı** (D-067) — gözlem tekrar ölçülmedi.
**Gözlem, iddia değil** — N=3, koda dokunulmadı, A6/A7'ye girdi.

Yan bulgu: seed 2001'de `baseline_d037.shuffle`'ın gen2 `pe_list`'i
`control_d042.lived`'inkiyle **bit düzeyinde aynı** ⇒ D-042'nin konum
kusuru için gen2 yörüngesinden bağımsız kanıt. Ayrıca `baseline_d037` ile
`repro_d038` gen2'de de birebir aynı ⇒ D-037 determinizmi gen2'de tutuyor.

## ✅ Faz 2 KAPANDI

Kod düzeltme fazı (Adım 1–7), karar kapısı (D-018…D-022) ve uygulama fazı
(U1–U7) bitti. Bugün 35 commit, dokuz yeni karar (**D-023…D-031**).

| Adım | Commit | Ne yaptı |
|---|---|---|
| U1 | `7adb01d` | backend varsayılanı `local` (D-018) + **D-023** tanınmayan değer `ValueError` |
| — | `9ce5269` | `LLM_BACKEND_*` tekilleştirme (Cursor, mekanik) |
| U2 | `70edeba` | NF4 + `double_quant` açıkça (D-020) · kaydı **D-024** |
| U3a | `64f953a` | `DAU_LOCAL_MODEL` env + alet kimliği yüklenen ağırlığı raporluyor |
| U3b | `13e3b9e` | ölçüm harness'ı, beş kapı |
| U3 | `9fcfcbe` | **ölçüldü → Llama kalıyor** (**D-026**) |
| U7/A2 | `8cff2fd` | DPO penceresi 256→512 (**D-027**) |
| U4 | `9718737` | gradient accumulation (**D-028**) |
| — | `10697f1` | **D-029** öğrenme oranı 5e-5 → 1e-6 |
| U5 | `5ad70a8` | A5 marj eşiğine çevrildi (**D-030**) |
| U6 | `987a1bc` | consolidation deney yoluna bağlandı (**D-031**), GAP-14 kapandı |

## ✅ Çift darboğazı KAPANDI (D-032)

Sorun eşik değil **prompt**muş. Eğitim, 51 token'lık ve `system=""` olan
`"Lived preference: pe=0.413 decision over pe=0.873"` altında koşuyordu;
çıkarım 246–306 token (`SYSTEM_PROMPT` + anı + somatik + drift + AgentView).
Üstelik prompt cevap anahtarını veriyordu: PE karardan **sonra** hesaplanır.

| Commit | Ne yaptı |
|---|---|
| `5afc9ee` | karar olayı, modele giden prompt'un **aynısını** saklıyor; SYSTEM_1 (NPC) bilerek saklamıyor |
| `7232a04` | çift prompt'u = `chosen` olayının kendi prompt'u; `PREF_LIVED_CONTEXT_TEMPLATE` emekli; prompt'suz olay `[WARN]`+atla; shuffle `replace`'e geçti |
| `17bc9bd` | polarite kapısı NLI→**kosinüs** `[0.25, 0.80]`; sayaç/anahtarlar `polarity_*` |

**Dur-kontrol:** gerçek `build_pe_ranked_pairs`, seed 2001'in gerçek
verisinde **9 çift** · **9 farklı prompt** · 2 benzersiz `rejected`
(önce 1–3). Ham: `dau_runs/exploratory_pair_design_replay.json`.

## ✅ İlk gerçek koşum yapıldı (D-033) — alet artık uçtan uca koştu

`dau_runs/smoke_d032_local.json` · yerel Llama, N=1, gen1=10 olay · `exit 0`,
**2dk 47sn**. D-032'nin dur-kontrolü canlıda doğrulandı: `lived` **8 çift**,
`shuffle` 6, `null` 0 · `[LORA][WARN]` **sıfır** · I5.2 geçti.

⚠ **Ama bu koşumun kendisi de kirliydi** — kusuru koşum sırasında buldu.
`lived` ve `shuffle` 08-09 ağırlıklarıyla başladı, yani **8 ve 6 sayıları
temiz ölçüm değil**. Adapter üretilen completion'ları, o da çeşitliliği ve
çift sayısını etkiliyor. Güvenilir olan **yön**: 1–2'den 8'e çıkması, ve
`[LORA][WARN]=0`. Kesin sayı I0.7 temizken yeniden ölçülmeli.

⚠ Aynı koşum bir kusur buldu: **adapter'lar koşumlar arası diskte kalıyordu**
ve `switch_adapter` faz-1 başında yüklüyordu (üstelik `DAU_LORA_ENABLED`'a
bağlı değil ⇒ `--no-lora` da kirlenir). Kollar bu yüzden ayrıştı. Sapma
**H1 lehineydi**. → **I0.7** ABORT kapısı eklendi (`782ca33`).

## ✅ PİLOT KOŞULDU (D-034) — alet çalışıyor, sinyal kurulmadı

`dau_runs/pilot_d033_n3_local.json` · N=3 (seed 2001–2003), gen1=50 olay,
greedy, `--lora` · **58 dk**, `exit 0`, I0.7 yeşil başladı.

| Ne | Sonuç |
|---|---|
| Değişmezler | **18'in 17'si geçti**; yalnız I3.2 bayrak (kalibre değil). **I5.4 ilk kez geçti** |
| D-032 | `prompt_skipped_no_record = 0 / 300` — her kararın kayıtlı prompt'u vardı |
| Çift | **252** (47/47 · 41/41 · 38/38). `lived`=`shuffle` simetrisi geri geldi ⇒ I0.7 çalışıyor |
| `n_unique` | 29 · 22 · 27 (50 olayda) — 7-benzersiz tavanı **açıldı** |
| VRAM | 1 OOM uyarısı, çökme yok |
| Süre | seed başına **~19.4 dk** ⇒ N=15 ≈ **4.9 saat** |

**Sinyal (N=3, hipotez testi değil):** ΔPE ortalaması lived **+0.080** ·
null +0.058 · shuffle +0.113. `lived − null` bir seed'de H1 yönünde, birinde
ters, birinde tam berabere. `lived ≤ shuffle` **3/3** seed'de ama farklar
küçük.

⚠ **D-034'ün bir cümlesi düzeltiliyor** (kayıt append-only, düzeltme burada;
D-035'e geçecek). Orada *"seed 2001'de eğitim hiçbir şeyi değiştirmedi"*
yazıyor. Doğrusu: **uç nokta değişmedi, davranış değişti.** `pe_after` üç
kolda bit düzeyinde aynı (0.45483523726463315), ama `arm_digest`
(= `sha256(karar dizisi ++ PE dizisi)`, faz-1+faz-2) üçünde de **farklı**,
ve faz-1 özdeş (`pe_before` aynı). Demek ki adapter faz-2'de kararları
ve/veya pencere dışındaki PE'leri değiştirdi; değişmeyen şey **son 10 olayın
ortalaması**. Bu, lr'nin yanında **`PE_WINDOW_EVENTS=10`'un 50 olayda etkiyi
kaçırıyor olabileceğini** de şüpheli hale getiriyor. Digest "bir şey değişti"
diyor ama "ne kadar" demiyor — Adım 0 bunu sayıya çeviriyor.

## ✅ ADIM 0 + ikinci N=3 koşumu (D-035) — **`run_quality=clean`**, ilk kez

`dau_runs/step0_d035_n3_local.json` · aynı şekil, temiz adapter · 59dk 37sn ·
**18 değişmezin hepsi geçti.**

**Kanal 2 atıl değil:** adapter faz-2 kararlarının **%68'ini** değiştiriyor
(21/50 · 43/50 · 38/50). Faz-1 kollar arasında özdeş, yani fark yalnız
adapter'ın eseri.

⚠ **Asıl bulgu — ölçüm penceresi darboğaz.** `_window_mean` = `pe_list[:10]`,
faz 50 olay. Uç nokta her fazın **ilk beşte birini** okuyor:

| Seed | değişen karar | **ilk 10'da** | ΔPE ayrıştı mı |
|---|---|---|---|
| 2001 | 21/50 | **0** (ilk fark idx 16) | **hayır** — `pe_after` null ile bit düzeyinde aynı |
| 2002 | 43/50 | 6 | evet |
| 2003 | 38/50 | 8 | evet |

D-034'ün "sinyal kurulmadı"sının sebebi büyük ölçüde bu.

## ✅ D-035'in dört kararından **ikisi kapandı**

| Karar | Durum |
|---|---|
| **1. Ölçüm penceresi** | ✅ **D-036** — pencere = fazın tamamı (`1489548`). İlk koşumda işe yaradı: seed 2001'in üç kolu eskiden bit düzeyinde aynıydı, şimdi ayrışıyor |
| **3. Eğitim determinizmi** | ✅ **D-037** — `TORCH_DETERMINISTIC_WARN_ONLY=False` (`48be16e`), I0.6 artık **bunu zorunlu kılıyor** |
| **2. `F_agent`** | ⏸ dokunulmadı, sınır kayda geçti. Girdilerin **üçü de dejenere**: `E=0.000` (9/9), survival=1.0 (9/9), `\|dpool\|` yayılımı %3.3. Formül düzeltmesi ayrım üretmiyor (denendi: fark 0.0008–0.0016) |
| **4. İki eşik** | ⏸ değer seçilmedi (§2.7). Dağılım var; sınır başına red sayısı hâlâ loglanmıyor |

**D-037'nin ölçtüğü:** dört kontrollü koşum, aynı seed/kod. `warn_only`
altında iki koşum **farklı adapter** ve 21/50 · 23/50 karar farkı üretti;
strict altında **birebir aynı adapter, 0/50 fark**, aynı süre (20dk24 vs
20dk25), abort yok. Koşumdan koşuma gürültü **0.026**, ölçülen `lived−null`
farkı 0.015–0.025 ⇒ **gürültü etkiden büyüktü.** Ön-kayıtın önündeki asıl
engel buydu ve kalktı.

## ▶ ÇALIŞMA KUYRUĞU — ✅ **A/B/C fazlarının hepsi kapandı**

⚠ **Bu bölüm artık tarihçedir.** Güncel iş §1'in başındaki
**▶▶ SIRADAKİ İŞ**'te; "devam et" oradan başlar. Aşağısı Faz A/B/C'nin
nasıl kapandığını gösteriyor ve hangi kararın hangi adımdan çıktığını
aramak için duruyor.

### Faz A — kilitten önce (pencere kapanınca biter, §2.10)

| # | İş | Süre | Durum |
|---|---|---|---|
| ~~A5~~ | ✅ **D-045** — gen2 de kayıplı, S4 sınırı L10 olarak yazıldı | — | ✅ |
| ~~A3~~ | ✅ **D-046** — I1.3 (daraltıldı) · I1.3b (yeni) · I1.4 (spec tautolojiydi, çevrildi) · I1.5 (`MIN_PAIRS` config'den) | — | ✅ |
| ↳ | ✅ **GAP-6 kapandı** (`b66f7fc`) — temizlik swap'e değil **DPO adımına** kondu | — | ✅ |
| ~~A6~~ | ✅ **D-050** — precision ağırlığı aday olarak **elendi** (dokuz karşıtlıkta işaret aynı). Yan bulgu: **Precision-PE atıl** (L13) | — | ✅ |
| ↳ | ✅ **GAP-5 doğrulandı ve nicelendi** → L14 · **GAP-4'ün mekanizması yok**, asimetri → L15 | — | ✅ |
| ~~A7~~ | ✅ **D-051** — saat gerçekten kırık ama birincile giden yol **L1 + travma muafiyeti** ile kapalı ⇒ **değiştirilmedi**, L16 olarak yazıldı. ⚠ **Gizli:** `F_agent` tek başına düzeltilirse canlanır. Yan bulgu: konsolidasyon raporu JSON'a hiç girmiyormuş (`060d907`) | — | ✅ |

**Ertelendi, bilerek:** **A2** (OOD probing) ve **A4** (environment'ı ayrım
üretir hale getirme). İkisi de değerli, ikisi de bu ön-kaydı **günlerce**
bekletir. §2.10'un uyardığı "önce şunu da düzeltelim" kuyusu tam olarak
bunlar. → ikinci ön-kayıt / popülasyon çalışması.
⚠ **A2'nin tasarımı zaten kusurlu çıktı (D-049/I12):** "getirimi tamamen
kapat" OOD şoku ölçer, parametrik kapasiteyi değil. Yerine **plasebo anı
enjeksiyonu** geçecek — sonraki ön-kayıt.

### Faz B — kilit ve sonrası (**A8 kararı gelmeden başlayamaz**; S4 D-047 ile kapandı)

| # | İş | Süre | Durum |
|---|---|---|---|
| ~~A8~~ | ✅ **D-052** — **N=40**, seed 2004–2043, iki batch. MDE `d_z=0.465` (Wilcoxon). **GAP-9 kapandı**: `N=40–50` ΔPE için hesaplanmış, bizim birinciliğimiz için değil | — | ✅ |
| ~~B1~~ | ✅ **KİLİTLENDİ** `befd72b4ee57` — 7/7 slot, alet kimliği donduruldu (§12), GAP-3→L17 · GAP-10→L8 | — | ✅ |
| ~~B2~~ | ✅ **Koşuldu** — seed 2004–2043, ~13.1 sa, çökme yok. ⚠ `run_quality=flagged` iki batch'te de (bayrak `I1.3b`) | — | ✅ |
| ~~B3~~ | ✅ **Analiz koşuldu** — birincil **p = 0.9914** (null). S5/S6 **koşulamadı**, verisi/kolu yok. Çıktı `dau_runs/b3_prereg_analysis.json` | — | ✅ |
| ~~B4~~ | ✅ **`docs/B2_RESULTS.md`** — on yedi sınır + dört yeni (L18–L21) + **§11 sınıfı: alet null'ı** (D-053) | — | ✅ |

⇒ **Sıradaki iş: Faz C** (belge borcu). Ondan sonra **ikinci ön-kayıt**.

### ✅ Faz C — KAPANDI (2026-08-12)

| İş | Nasıl kapandı |
|---|---|
| Master ref D-045…D-053 + §23 baştan | ✅ **v2.4.3** (`33fcd1e`) |
| §9 consolidation anlatısı (D-022/D-031) | ✅ ilk ölçülen `deleted_count` (ort. 24.90) ile |
| §12 kod ağacı · §14 test sayısı (206 → 344) | ✅ Cursor |
| `PREFLIGHT_INVARIANTS.md` **Kodda** sütunu | ✅ Cursor · 24/26 · *"koda dökülmeyi bekliyor"* satırı da düzeltildi |
| `dau_runs/` etiketleme | ✅ **`dau_runs/README.md`** · 38 dosya · dört kategori · ⚠ mtime güvenilmez, `.gitignore` istisnasıyla takipli |
| `.html` / `.pdf` | ✅ pandoc ile **yeniden üretildi** (29 sayfa). PDF'te emoji → metin karşılığı |
| `EXECUTION_PLAN.md` | ✅ **kapatıldı**, geri doldurulmadı — gerekçe dosyanın başında |

⚠ Cursor'ın yakaladığı iki eskimiş sayı düzeltildi: `preflight.py` **805 → 1208**,
`run_cprime_multigen.py` **1153 → 1378**, testi **~900 → 1495** (§7).

---

## ▶ GAP TETİK TABLOSU — ne zaman gündeme getirilecek

Yasin'in talimatı: *"GAP'ler için uygun zamanı gözet, o an geldiğinde
hatırlat ve neden o anın optimal olduğunu belirt."* Aşağıdaki **Tetik**
sütunu bağlayıcı — o adıma gelindiğinde GAP **kendiliğinden** gündeme gelir.

| GAP | Tetik | Neden o an optimal | Nasıl çözülür |
|---|---|---|---|
| ~~GAP-18~~ | ✅ **ÖLÇÜLDÜ (B2)** — `uniq_rejected` **100 / 94** · `uniq_chosen` 1025 / 971 · `max_rejected_reuse` **47 / 45** · `texts_in_both_roles` 28 / 51, 1707+1741 çift üzerinde. Şiddet artık sayıyla biliniyor: reddedilen taraf 10 kat daha az çeşitli. ⚠ **KTO kararı ikinci ön-kayıta** — kilit kapalı | ikinci ön-kayıt |
| ~~GAP-17~~ | ✅ **RAPORDA NOT EDİLDİ** — `docs/B2_RESULTS.md` §6, "açıklanmadı" olarak. Bisect yapılmadı; 08-09 tabanı `tool_identity` öncesi olduğu için delil değeri yok | kapandı (not olarak) |

**Kilitte sınıra çevrilenler** — yeniden açılmaz, `PREREGISTRATION.md` §8'de:
GAP-3 → **L17** · GAP-4 → **L15** · GAP-5 → **L14** · GAP-10 → **L8** ·
GAP-19 → **L16**. GAP-9 **kapandı** (D-052). ⚠ **L16 artık tarihçedir:**
GAP-19'un kendisi D-067'de kapandı; sınır ilk ön-kayıt için geçerliydi.

---

## ▶ DR KANALI — ⏳ **brief #4 gönderildi, cevap bekleniyor**

| # | Brief | Durum |
|---|---|---|
| **5** | **Yaşam uzunluğu değişkenken uç nokta nasıl tanımlanır** — `docs/research/2026-08-13_variable-lifespan-endpoints-and-censoring.md` | ⏳ **gönderilmeyi bekliyor.** Altı soru: S1 bilgilendirici sansürleme · S2 landmark vs yaşam boyu özet · S3 ölümün belirlediği durum değişkeni · S4 hayatta kalma hem girdi hem sonuçken · S5 farklı uzunluklu dizilerde eşleştirilmiş karşılaştırma · S6 küçük N'de zaman-olay gücü. ⚠ **Etki sorulmuyor, bilerek** (D-064/L9 disiplini) |
| **4** | **Ayrım üretmeyen bir evrende seçilim kurulabilir mi** — `docs/research/2026-08-12_environment-differentiation-and-selection.md` | ✅ **cevaplandı ve mutabakata bağlandı (D-065, §J).** Ham cevap: `2026-08-13_DR4-answer-raw.md`. **İçeriği dört brief'in en isabetlisi, kaynak disiplini en kötüsü:** 12 kimlikten 5'i eksiksiz, biri **yanlış makaleye** atıflı (yedinci kimlik hatası), biri dergi ISSN'i, ve *"N=20–50"* kaynaksız ⇒ kullanılmadı |

**Cevaptan alınan üç şey (D-065):** ⭐ **J9** azalan getiri (Dykhuizen, Dean &
Hartl 1987, Genetics 115:25–31) — akı, aktivitenin **içbükey** fonksiyonu,
doyumda seçilim **nötrleşir** ⇒ A4-①'in eksik parçası olan **kazanç eğrisinin
biçimi** · **J4** GovSim (Piatti vd. 2024): GPT-4 dahil hiçbir model ortak
kaynak ikilemini çözemiyor (<%54) ⇒ bizim %94–100 defect'imiz **evrenimizin
özel kusuru değil** · **J20** rapor bağımsız olarak *"popülasyon tek başına
yetmez, önce bedel"* dedi ⇒ **① önce, sonra ②** sıralaması dışarıdan doğrulandı.

**Reddedilenler:** **J17** DR birincili *"ağırlık vektörü"* sandı (değil —
doğum-drift, ve varis adapter almıyor); hatanın yarısı **bizim brief'imizin**
eksik tarifi · **J18** DTW'yi şimdi birincil yapmak — yörünge uç noktalarının
daha büyük ayrım verdiğini **zaten ölçtük** (D-044/045) ve bilerek almadık,
etkiyi görüp seçmek post-hoc olur (L9).

⚠ **Yalnız brief gönderildi, master reference gönderilmedi** — bilerek.
Master ref kendi başında *"işaretsiz her bölüm hâlâ v2.4.1 anlatısıdır"*
diyor ve içinde **32 ⚠ işaretli yanlış** var; ayrıca karar geçmişini
içeriyor ve §9 provenans sorusunu DR'ye yasaklıyor. Brief'in 15 sayısı
programla teyit edildi.

**Cevap gelince ne yapılacağı §1'in başında yazılı.**

### İlk üç brief — kapandı

Üçü de gönderildi, cevaplandı ve mutabakata bağlandı. Ayrıntı
`docs/research/RECONCILIATION.md` **§G, §H, §I**.

| # | Brief | Neyi açar | Dosya |
|---|---|---|---|
| **1** | **S4 — en küçük anlamlı etki** | 🔒 **Kilidi bu tutuyor.** Cevap gelmeden B fazı başlayamaz. GAP-9 da bununla kapanır | `2026-08-11_S4-minimum-effect-of-interest.md` |
| **2** | **GAP-18 — ortak negatif / az çeşitli `rejected`** | Eğitim seti kalitesi. Kilidi bloke etmiyor | `2026-08-11_GAP18-shared-negatives-in-preference-learning.md` |
| **3** | **Lamarckçı kapsam + kanal ayrımı** | İddianın genişliği (1–2) ve **bir sonraki ön-kaydın mimarisi** (3–4). GAP-5'in literatür yarısı burada | `2026-08-11_lamarckian-scope-and-channel-separation.md` |

**Üçünün ortak dersi (kayda değer):** ikisi **bizim verdiğimiz yanlış
bilgiden** zarar gördü — #1'in `r≥0.85` varsayımı bizim "determinizm"
tarifimizden türedi, #2'nin bütün teşhisi bizim iki koşumdan birleştirdiğimiz
"47 çift / 2 benzersiz negatif" sayısından. **Brief kalitesi girdi kalitesiyle
sınırlı, ve girdiyi biz yazıyoruz.**

⚠ Kaynak kimlikleri: #3 en sağlamı (12 doğrulandı, 1 düştü) · #2 en zayıfı
(6 düştü — Distinct-N ve Self-BLEU'nun ikisi de "Papineni 2002"ye
atfedilmişti, o BLEU'dur).

---

## ▶ EV İŞLERİ — tetiklendiğinde

| İş | Tetik | Not |
|---|---|---|
| **`archive/` 2.3 GB** | **isteğe bağlı** | ⚠ **Artık bloke etmiyor:** ölçüldü, B2 ~1.1 GB yazacak (40×2 adapter × 14 MB) ve **36 GB boş** var. Temizlik hijyen, zorunluluk değil |
| **Adapter'lar** (`dau_runs/adapters/`, artık **87 dizin** ~1.2 GB) | **isteğe bağlı** | 2001–2003 D-042/D-043'ün kanıtı; **2004–2043 B2'nin kanıtı** ⇒ ikisi de silinmemeli. ⚠ Bir sonraki koşum başka seed'lerden başlamalı, yoksa I0.7 abort eder |
| **`dau_runs/` JSON etiketleme** | **Faz C** | Bir kısmı geçersiz (D-036/037/042 öncesi). Silinmemeli, etiketlenmeli. B2'nin üç dosyası **geçerli ve nihai** |
| ~~D-013 — branch main'e taşınmadı~~ | ✅ **KAPANDI (D-054)** | main = branch. Eski main `archive/main-pre-c116` etiketinde, hiçbir commit kaybolmadı. ⚠ **push edilmedi** — ayrı karar |

# 2. Yeni Oturum Protokolü (bağlayıcı)

## 2.1 İlk beş dakika — sırayla, atlamadan

1. **Bu dosya** (otomatik yüklenir) → §1'in başındaki **▶▶ SIRADAKİ İŞ**.
   "devam et" denince oradan başlanır, başka yere bakılmaz. DR raporu
   sunulduysa adım adım orada yazılı.
2. **GAP TETİK TABLOSU** — alınan adımın bir GAP tetiği var mı? Varsa
   **Yasin'e hatırlat ve neden o anın optimal olduğunu söyle** (talimat,
   2026-08-11).
3. **`docs/DECISIONS.md`** — ilgili D-kaydı. En çok bağlam taşıyanlar:
   **D-036** (ölçüm penceresi) · **D-037** (tekrarlanabilirlik) · **D-042**
   (konum bağımsızlığı) · **D-044** (uç nokta duyarlılığı).
4. **`docs/PREREGISTRATION.md`** — 🔒 **KİLİTLİ** (`befd72b4ee57`), 7/7 slot
   kapalı, **on yedi ilan edilmiş sınır** (L1–L17), alet kimliği §12'de
   donduruldu. Rapor dört sınır daha ekledi: **L18–L21** (`docs/B2_RESULTS.md`).
5. Koda dokunmadan önce **§2.2**.

⚠ `docs/EXECUTION_PLAN.md` **Faz 2'de donmuş** — D-038…D-044 orada yok.
Kuyruk bu dosyada, planda değil.

## 2.2 Önce doğrula, sonra dokun

**Bu belgedeki hiçbir satır numarasına güvenme** — `grep` ile teyit et.
Bu projede belge üç kez yanıldı: GAP-11 (docstring eski `agent_id` formatı),
GAP-14 ("hiç kimse çağırmıyor" — çağırıyordu), U5 (`SNR_FLOOR=0.40` tarifi
ölçünce ters çıktı). **Hafızaya ve belgeye değil, dosyaya güven.**

## 2.3 Gate-and-confirm — onaysız kod değişmez

Analiz → öneri → **Yasin'in onayı** → uygulama. Analiz şunları içerir:
ne bulundu (**kanıtla**), ne değişecek, hangi test gelecek, ne riskli.

Yasin "devam et" / "önerini uygula" dediğinde bu **o adım için** onaydır;
adım içinde yeni bir karar noktası çıkarsa (yeni sabit değeri, iki tasarım
arasında seçim) **tekrar sor**. Bugün bu beş kez oldu ve beşinde de doğru
olan sormaktı.

## 2.4 Her düzeltme testiyle gelir, test mutasyon kontrolünden geçer

Düzeltmeyi geçici geri al → test **kırılmalı** → geri koy. Kırılmıyorsa
test o hatayı yakalamıyordur.

**Bu kural bugün kendi testimi yakaladı:** U7/A2'nin ilk testi "dönen dizi
pencereye sığıyor mu" diye soruyordu; fonksiyon zaten sığdırmak için
kestiğinden test her koşulda geçiyordu. Mutasyon (256'ya geri dön) geçti →
test boştu → "kesme oldu mu" sorusuna çevrildi. **Mutasyon kontrolü
olmadan repoya işe yaramaz bir bekçi girecekti.**

## 2.5 Commit ritmi

**Tek konu → tam suite (`python -m pytest -q`) → gerekçeli commit.**
Suite yeşil değilse commit yok.

- **Kod ve D-kaydı ayrı commit.** Kod commit'i `[U4]` / `[D-029]` gibi
  etiketlenir, kayıt commit'i `[DOCS]`.
- Commit mesajı **ne yaptığını değil neden yaptığını** anlatır: hangi ölçüm,
  hangi alternatif reddedildi, hangi mutasyon denendi.
- Kasıtlı test kırılması **aynı commit'te** gerekçesiyle güncellenir
  (Faz kuralı A.3).
- Belge güncellemesi (plan ✅ + `CLAUDE.md` durum satırı) ayrı `[DOCS]`.

## 2.6 Ne nereye yazılır

| Ne | Nereye | Mod |
|---|---|---|
| Karar, ölçüm sonucu, gerekçe, **reddedilen alternatif**, ölçümün sınırları | `docs/DECISIONS.md` (**D-kaydı**) | **append-only**, asla düzenleme |
| "Şu an neredeyiz", sıradaki iş, açık GAP | `CLAUDE.md` | üzerine yazılır, **kısa** |
| Adım ayrıntısı, dur-kontrol, adım durumu | `docs/EXECUTION_PLAN.md` | ✅ + commit hash |
| Formül, tarihçe, empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` | sürüm sürüm ⚠ borç |
| Ham ölçüm çıktısı | `dau_runs/*.json` | koşum yazar |
| DR brief'i (ham) | `docs/research/YYYY-MM-DD_konu.md` | dosya, sohbete yapıştırılmaz |
| DR mutabakatı | `docs/research/RECONCILIATION.md` | bölüm ekle |

**D-kaydı ne zaman şart:** `constraints.py` eşik **değeri** değişiyorsa ·
ön-kayıtlı bir protokol değişiyorsa · kilitli bir karar sorgulanıyorsa ·
bir ölçüm yapıldıysa (sonucu ne olursa olsun) · bir alternatif reddedildiyse.

## 2.7 Ölçüm disiplini (bugün oturdu, bağlayıcı)

- **Keşifsel ölçüm ≠ ön-kayıtlı ölçüm.** Keşifsel olan JSON'unun ilk
  alanına `"note": "exploratory, not pre-registered"` yazar ve D-kaydında
  öyle etiketlenir. D-019'un kriteri keşifsel ölçüme uygulanmaz.
- **Ön-kayıtlı harness'a keşifsel soru için dokunulmaz** — scratchpad'den
  çağrılır. (U3 harness'ı böyle korundu.)
- **Ölçümün sınırları kayda geçer:** kaç seed, kaç örnek, tek atış mı.
  D-029 bunun örneği — brief'in yarısı doğrulandı, yarısı "gözlenmedi"
  diye kaydedildi, "yanlış" diye değil.
- **Değer ölçümden seçilmez.** Ölçüm **yönü** kanıtlar; tek seed'den değer
  seçmek post-hoc tuning'dir. D-029'da lr literatürden alındı.
- Diske yazan/silen keşifsel koşum **adapter kaydetmez**, sabit değiştirmez.

## 2.8 Tekrarlayan hata deseni — **her adımda kontrol et**

Bugün **dört kez** aynı sınıf hata çıktı:

> **Rapor aleti takip etmeli, aleti tekrar etmemeli.**

- U2: `describe_quantization` doğru okuyordu ama kod fp4 koşuyordu
- U3a: `tool_identity._model_id` sabiti okuyordu → Qwen sayılarını "Llama"
  diye etiketleyebilirdi
- U4: `GRADIENT_ACCUMULATION_STEPS` literal `1`'di — o gün olguydu
- U5: `SNR_MARGIN_FLOOR_CALIBRATED` bayrağı eklendi ki kalibre edilmemiş
  eşik yerleşmiş gibi okunmasın

**Yeni bir sabit/ayar eklerken sor:** alet kimliği bunu raporluyor mu, ve
raporu **sabitten mi okuyor yoksa yeniden mi üretiyor**?

## 2.9 Neye sadık kal

5 Değiştirilemez Yasak · Değiştirilemez Süreç Kuralları · **sessiz fallback
yasağı** (belirlenemeyen durum `SystemExit`/`ValueError`/`[WARN]` ile
gürültü çıkarır, varsayılana düşmez) · `constraints.py` eşik **değerleri
yalnızca D-kaydıyla** değişir.

## 2.10 🔒 Ön-kayıt penceresi **KAPANDI** (2026-08-11, `befd72b4ee57`)

Bugün on iki karar (D-039…D-052) bu pencerede meşruydu. **Artık değil.**

**Kilitten sonra yasak:** `constraints.py` eşik değeri · uç nokta · test ·
çift kurma stratejisi · `SYSTEM_PROMPT` · herhangi bir ön-kayıtlı protokol
maddesi. Bunlardan biri değişirse sonuç **post-hoc** olur ve ön-kayıt
geçersizleşir.

**Hâlâ meşru:** saf raporlama/aletleme eklemesi (hesaplamayı değiştirmeyen),
ve **açık hata düzeltmesi** — ama ikincisi D-kaydı **ve** Yasin onayı ister,
ve "bu bir hata mı yoksa ayar mı" sorusu sessizce cevaplanmaz (§2.11).

**Aklına gelen her iyileştirme ikinci ön-kayıta gider.** Listesi §1'de.

## 2.11 Çelişki görürsen sessizce seçme

Belge ile kod, ya da iki belge çelişiyorsa: **raporla, kullanıcıya sor.**
(Bugün dört kez oldu: U2'nin dur-kontrolü ateşlenemezmiş · U5'in eşiği
ters çalışıyormuş · brief'in NLI bandı yanlışmış · planın satır numaraları
kaymış.)

## 2.12 Okuma haritası

| Ne zaman | Dosya |
|---|---|
| Her oturum başı | `CLAUDE.md` (otomatik) |
| Sıradaki iş ne | `docs/EXECUTION_PLAN.md` §D/§F |
| "Bunu neden böyle kararlaştırdık?" | `docs/DECISIONS.md`, D-numarasıyla |
| Gate'i kodlarken | `docs/PREFLIGHT_INVARIANTS.md` (**26 madde tanımlı, 24'ü kodda** — I1.2 testte, I2.3 yapısal) + `dau/diagnostics/preflight.py` |
| "Bu dosyanın sessiz yolları neler?" | `docs/RUNPATH_AUDIT.md` (K1–K8) |
| Alet/literatür kararı öncesi | `docs/research/RECONCILIATION.md` |
| Formül · tarihçe · empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` **v2.4.2** — yanlışlar ⚠ ile işaretli, §24/§25 yeni |
| Ön-kayıt: slotlar, uç noktalar, **on yedi ilan edilmiş sınır**, donmuş alet kimliği | `docs/PREREGISTRATION.md` 🔒 **KİLİTLİ** |
| **Sonuç, sınıflandırma, ne iddia edilebilir** | **`docs/B2_RESULTS.md`** |
| Bekleyen DR sorusu (S1–S6) | `docs/research/2026-08-12_environment-differentiation-and-selection.md` |
| Sıradaki iş · GAP tetikleri · DR sırası | **bu dosya §1** |

---

# 3. Axiom

> "Bir agent'a trait veremezsin, sadece yaşam verebilirsin, trait oradan çıkar."

Yorum (kilitli): Agent'a hiçbir trait etiketi verilmez. Evrenin koyduğu
kısıtlar (kıtlık, kriz, sosyal sürtünme, drift) agent'ı şekillendirir. Bu
şekillenmenin davranışsal izi, trait etiketi hiç var olmadan, nesilden nesile
**iki ayrı kanaldan** deterministik biçimde aktarılabilir olmalı:

- **Kanal 1 — Memory Vault (sembolik):** `apply_generation → seed_inherited_record`.
  Somut anılar/somatic scale gen2'ye veri olarak kopyalanır. LoRA'dan bağımsız.
- **Kanal 2 — LoRA (parametrik):** Gen1'in PE-ranked tercih çiftleri, agent'ın
  kendi ağırlıklarına DPO ile işlenir. `DAU_LORA_ENABLED=1` gerektirir.

İkisi de "yaşamın izi" sayılır, biri diğerinin yerine geçmez.

⚠ **D-029 bu aksiyoma doğrudan dokundu:** `lr=5e-5` ile eğitilen ajan
*"düşük PE'li şeyi tercih et"* değil *"yüksek PE'li şeyi asla söyleme"*
öğreniyordu. Kanal 2'den aktarılan iz bir tercih değil **bastırma deseni**
olurdu. Hangi izin aktarıldığı, aksiyomun iddiasının ne olduğunu değiştirir.

## 5 Değiştirilemez Yasak

1. **No trait injection** — trait/personality değerlerinin doğrudan atanması yasak.
2. **No LLM-as-judge** — tüm metrikler deterministik Python (MiniLM PE, NLI,
   DAERM, PPR, Precision-PE).
3. **No clock-driven time** — sadece olay sırası (`EventClock`, int counter),
   wall-clock zaman yasak (log/run_id etiketleme hariç).
4. **UPPER_CASE constants** — her sabit `constraints.py` veya modül başında,
   tek yerde tanımlı.
5. **No magic numbers** — semantik alan adları zorunlu, gömülü sayı yasak.

## Değiştirilemez Süreç Kuralları

- **Pre-registration:** Her run öncesi parametre/kriter kilitlenir. Run
  sırasında/sonrasında post-hoc değişiklik yasak.
- **Tek dosya / tek görev / tek commit.**
- **Gate-and-confirm.**
- **Null/underpowered sonuç meşru bilimsel çıktıdır** — gizlenmez.
- **Read-only audit, implementasyondan önce gelir.**

---

# 4. Kilitli Kararlar

- Generation-end batch micro-QLoRA ≫ per-event online learning
  (`docs/research/2026-08-08~_per-agent-lora-serving.md` §2).
- Dual-channel mimari (sembolik vault ayrı, parametrik LoRA ayrı) — 08-08~ §4.
- Per-agent adapter disk izolasyonu (`dau_runs/adapters/{agent_id}/`), Punica.
- `heal_drift` çift-uygulama riski KAPANDI (`meta_observer._evaluator_healed_domains`).
- Precision-PE v2.4 (rolling history + VAR_REF=1/12), kalibrasyon doğrulandı.
- **Backend `local`** (D-018); groq legacy kalır. Tanınmayan değer `ValueError` (D-023).
- **Model: `meta-llama/Meta-Llama-3.1-8B-Instruct`** — ölçüldü, Qwen kapının
  altında kaldı (**D-026**). `DAU_LOCAL_MODEL` ile değiştirilebilir ama alet
  kimliği **yüklenen** ağırlığı raporlar (D-023 deseni).
- **Quantization NF4 + `double_quant`, açıkça** (D-020/D-024).
- **`DPO_MAX_SEQUENCE_TOKENS = 512`** (D-027) — ayar değil, eğitim/çıkarım
  uyumsuzluğu düzeltmesiydi.
- **`DPO_LEARNING_RATE = 1e-6`**, bant `[5e-7, 1e-6]` (**D-029**).
- **Consolidation faz-2 sonrası, transfer'den önce** (**D-031**) — null
  kolunun `delta_pe`'sini korumak için.
- **DPO prompt'u = kararın verildiği prompt'un kendisi** (**D-032**).
  `agent_node` saklar, `build_pe_ranked_pairs` `chosen` olayınınkini oynatır.
  SYSTEM_1 (NPC) kararları prompt taşımaz ⇒ eğitime **giremez**.
- **Polarite kapısı: kosinüs mesafe, bant `[0.25, 0.80]`, MiniLM** (**D-032**).
  `NLI_CONTRADICTION_THRESHOLD = 0.60` **değeri değişmedi** — ölçüm eşiğin
  yanlış değil **ilgisiz** olduğunu gösterdi (0.60'ta %12.9, 0.30'da %12.9).
  `POLARITY_FILTER=nli` ile hâlâ erişilebilir. ⚠ Bant **kalibre değil**
  (`POLARITY_COSINE_CALIBRATED=False`), brief'ten geldi.
- **Ölçüm penceresi = fazın tamamı** (**D-036**). `PE_WINDOW_ALL_EVENTS = 0`
  sentinel; `PE_WINDOW_EVENTS = 0`. Eskiden 10'du ve 50 olaylık fazın ilk
  beşte birini okuyordu. ⚠ D-034/D-035'in ΔPE sayıları bu yüzden
  **karşılaştırılamaz** — onlar başka bir şeyin ölçümü.
- **`TORCH_DETERMINISTIC_WARN_ONLY = False`** (**D-037**) ve **I0.6 bunu
  zorunlu kılıyor** (raporlamıyor, başarısız sayıyor). warn_only altında aynı
  seed+kod iki koşumda farklı adapter ve 21/50 karar farkı üretiyordu.
- İstatistik eşikleri: N≥15, K≥5 (`DIVERSITY_MIN_UNIQUE`), n_eff≥12 —
  provenans 08-08~ §5. ⚠ **N≥15 GAP-9 ile çelişiyor**, aşağıya bak.
- **Çok-nesilli C′ birincil uç noktası = doğum-drift** (D-002). Gen2 PE +
  gen2 davranışsal = ön-kayıtlı ikincil. Testler: Kruskal-Wallis,
  Fisher-Freeman-Halton, paired t-test/Wilcoxon, travma için McNemar.
  ⚠ KW + FFH provenansı hiçbir brief'te yok (D-010) — türetilmiş, kilitli değil.
- **F_agent transfer kapısı korunur** + `f_agent=None` duyarlılık kolu (D-003).

---

# 5. Açık GAP'ler

## Kapanmışlar — yeniden açılmaz, kanıtı commit'te

| GAP | Nasıl kapandı |
|---|---|
| GAP-1 | LoRA kapısı + alet kimliği (D-004, `afbb552`), I0.1/I0.2 gate'te |
| GAP-7 | Backend `local` — **D-018**, uygulama `7adb01d` |
| GAP-8 | Bölündü (D-021) → A1 ✅`9718737` · A2 ✅`8cff2fd` · A5 ✅`5ad70a8` · **A3/A4 açık** |
| GAP-11 | Shuffle seed deterministik (`8cf2ac0`) |
| GAP-12 | Gen2 + transfer öncesi RNG kilidi (`ab8966c`), I4.2 gate'te |
| GAP-13 | Precision audit gen1 **ve** gen2'de (`090a5bc`), I3.2 gate'te |
| GAP-14 | Consolidation deney yoluna bağlandı — D-022 kararı, **D-031** uygulaması (`987a1bc`) |
| GAP-15 | `TEMPERATURE` çağrı anında okunuyor (`ab30f9c`) |
| GAP-16 | Quantization NF4 + double_quant (D-020) — uygulandı `70edeba` |
| GAP-20 | Koşumlar arası adapter sızıntısı — **D-033**, I0.7 ABORT kapısı (`782ca33`). Açıldığı gün kapandı |
| GAP-19 | **D-067** (`7c76a8c`) — kasa `counter_base` tutuyor; kasaya giren her sayaç faz-yerel, çeviriyi yalnız kasa yapıyor, yaşam bitince **yaşanan** olay sayısıyla mühürleniyor. D-051'in *"ikisi birlikte ya da hiçbiri"* şartı **D-066 ile aynı gün** ödendi |

> ⚠ **Her açık GAP'in bir tetiği var — §1'deki GAP TETİK TABLOSU'na bak.**
> Aşağısı GAP'in *ne olduğu*; *ne zaman ele alınacağı* orada.

## Açık — pre-reg'i **bloke edenler**

### GAP-18: `rejected` tarafı hâlâ az çeşitli — ama artık dejenere değil (D-032)
`best_by_event` sabit bir `chosen` için en büyük marjı seçtiğinden, global
maksimum-PE completion çoğu çiftin reddedilen tarafı oluyor. Bu **yapısal**:
veriye bağlı değil, her yaşamda olur.

⚠ **D-032 bunu küçülttü ama kapatmadı.** Prompt düzeldiği için eğitim seti
artık "aynı soru 9 kez" değil, **9 farklı durum, 2 ortak negatif** — ortak
negatif literatürde standart bir yapı. Ölçüldü: 9 çift, 9 farklı prompt.

⚠ **Doğrudan kapatmaya kalkışma — ölçüldü, ters teper.** `rejected`'ı
tekilleştiren ayrık eşleştirme 9 çifti **2**'ye düşürüyor; ayrıca aynı metnin
bir çiftte `chosen` başkasında `rejected` olmasına yol açıyor (PE
`(durum, eylem)`'in fonksiyonu, çift yalnızca metnin) — yani **çelişik
denetim**. Kalanı pilotun işi.

### GAP-9: N=15 güç analizine göre baştan yetersizdi
`protocol-c-metacognition-eval`: `σ_PE = 0.256`, `d_z ≈ 1.5·d`. Gerekli çift:
**d=0.5 → 16 · d=0.4 → 24 · d=0.3 → 41 · d=0.2 → 90**; Protocol C için
**N=40–50** öneriliyor. DAU'nun gözlediği etki `d ≈ 0.04`.
**`SAMPLE_N15_UNDERPOWERED` sürpriz değildi.** Pre-reg'de N varsayılan 15
alınamaz: ya etki büyüklüğü gerekçelendirilip N hesaplanır, ya da D-002'nin
yüksek güçlü uç noktası (doğum-drift, tamsayı sayımlar) kullanılır.
→ **Pilot çözer.**

## Açık — bloke etmeyenler

### GAP-17: üretim çeşitliliği açıklanamayan biçimde 3–4 kat arttı (D-026)
08-09 pilotu 50 olayda `n_unique` 7·4·8; bugün greedy **29·22·27**. Sebep
izole edilmedi. ⚠ **Önceliği düşürüldü:** karşılaştırma tabanı olan 08-09
pilotu `tool_identity`'den önce ve sampling durumu kayıtlı değil — yani
**delil olarak kullanılamaz**. Kullanılamayan bir tabana karşı bisect pahalı
ve sonucu bir şeyi değiştirmiyor. Bugünkü alet doğrudan ve kapsamlı ölçüldü.

### ~~GAP-2: Silent train failure~~ — **KAPANDI** (`d65100d`)
`_train_adapter`'ın beş erken dönüşünün hepsi artık konuşuyor: pair builder
exception'ı ve `lora_update` import hatası `[WARN]` basıyor, train exception'ı
ve `trained=False` zaten basıyordu. `DAU_LORA_ENABLED=0` dalı bilerek sessiz —
belgelenmiş kapı, hata değil.

### GAP-3: Gen2 event-1 somatic scale boşluğu
`apply_inherited_somatic_scale` sadece `delta_log` dolu olunca çalışıyor;
heir'ler boş `delta_log` ile doğuyor, ilk karar ata verisini kaçırıyor.
Gate I5.4 bunu koşumda raporluyor — D-068 pilotunda **16 kez** uygulandı.
⚠ Durumu D-066/D-067'den **etkilenmedi**; ama gen2 yaşamları artık kısaldığı
için kaçırılan ilk kararın **payı büyüdü** (11–20 olaylık bir yaşamda 1 olay,
20 olaylıkta olduğundan daha ağır).

### GAP-4: Memory-vault ↔ LoRA senkron kopukluğu (kodda doğrulanmadı)
Ebbinghaus ile kasadan silinen anının yarattığı drift LoRA'da kalıcı
kalabilir. ⚠ **U6 bunu canlı hale getirdi** — deney yolunda unutma artık
gerçekten çalışıyor, yani bu risk teorik olmaktan çıktı.

⚠ **D-067 riski BÜYÜTTÜ, küçültmedi.** Kırık saat faz-1 anılarını olduğundan
taze gösteriyordu, yani onları **silinmekten koruyordu**. Saat düzeldiğine
göre faz-1 anıları artık gerçek yaşlarıyla yargılanıyor ve daha fazlası
siliniyor — ama o anıların LoRA'ya işlenmiş izi silinmiyor. **Ölçülmedi**
(pilotun `deleted_count` sayıları kısa yaşamlardan geldiği için D-031'in
24.90'ıyla karşılaştırılamaz).

### GAP-5: SYSTEM_PROMPT lexicon priming (metodolojik, bug değil)
SYSTEM_PROMPT, `decision_to_outcome`'ın eşlediği kelimelere yönlendiriyor
olabilir. İki bağımsız denetim aynı maddeyi işaret etti (D-010).

### ~~GAP-6: adapter hot-swap CUDA temizliği~~ — **KAPANDI** (`b66f7fc`)
D-046. Temizlik **`switch_adapter`'a değil DPO adımına** kondu: swap her
yerel kararda koşuyor ve serbest bırakılacak bir şey ayırmıyor. Asıl risk
brief'in dediği değildi — tek adapter slotu paylaşıldığı için eğitim sonrası
`.grad` sonraki ajanın tensörlerinde asılı kalıyordu.
⚠ **Magic number kalıntıları GAP-6'dan ayrıldı, hâlâ açık:** `time.sleep(10)`,
bare `0.5` (shuffle), default `k: int = 5`. **Cursor'a uygun**, Faz C.

### GAP-10: Süresi dolmuş ölçüm ertelemeleri
- **`W_SEM = 0.0`** — ChromaDB vektörü skorlamaya girmiyor. "Baseline
  kilitlenince 0.3–0.4 yapılmalı" denmişti; koşul gerçekleşti, dönülmedi.
- **Negation kural sarmalayıcı yok** — NLI yalnızca tercih çiftlerinde,
  **PE sensörünün kendisinde değil**.
- **Asimetrik spillover matrisi** — kod skaler `CROSS_AXIS_SPILLOVER = 0.20`
  kullanıyor; brief domain-özgü matris öneriyor.

---

# 6. Kapatılmış/Geçersiz Sayılan Geçmiş Bulgular

- **Sahte eğitim bug'u** (`e4c026b` öncesi): `lora_B=0`, gradyan adımı hiç
  atılmıyordu. Artık **I0.1 değil, I1.1 kapısı** koruyor: her eğitim kolunun
  `Σ|lora_B|` değeri adım öncesi/sonrası okunuyor, hareket etmediyse ABORT
  (**D-039**). ⚠ Bu satır 2026-08-11'e kadar *"abs-sum kontrolü regresyon
  testinde"* diyordu ve **yanlıştı** — kod tabanında `lora_B`'ye değen tek bir
  test yoktu (D-038, Bulgu 2).
- **Adapter izolasyon sızıntısı** (`f25b0ef` öncesi): null kol lived kolun
  eğitimini miras alıyordu. `test_no_dead_adapter_root_reference` koruyor.
- **Bu iki düzeltme öncesi üretilen tüm C′ sonuçları geçersizdir.**
- ⚠ **Ek olarak:** bugünün dokuz alet değişikliğinden sonra, **bugünden
  önceki hiçbir ölçüm karşılaştırılabilir değil.** `dau_runs/`'daki
  08-09 tarihli pilot dahil.

---

# 7. Dosya Konumu Notları

⚠ **Satır numaraları 2026-08-13'te doğrulandı ama kayar — `grep` ile teyit et.**

| Ne | Nerede |
|---|---|
| `build_pe_ranked_pairs` | `dau/foundation/lora_update.py:346` |
| `_encode_pair_side` (D-027 kesme) | `dau/foundation/local_llm.py:609` |
| `_run_dpo_epochs` (D-028 accumulation) | `dau/foundation/local_llm.py:781` |
| `build_load_kwargs` (D-020 quantization) | `dau/foundation/local_llm.py:135` |
| `_consolidate_gen1` (D-031) | `dau/diagnostics/run_cprime_multigen.py:942` |
| `run_lineage` | `dau/diagnostics/run_cprime_multigen.py:976` |
| `_pair_filter_report` (D-030/D-032) | `dau/diagnostics/run_protocol_c_prime.py:871` |
| Polarite kapısı (D-032) | `dau/foundation/polarity_filter.py` (NLI `nli_filter.py`'de durmaya devam ediyor) |
| Karar prompt'unun saklanması (D-032) | `dau/foundation/graph.py`, `agent_node` SYSTEM_2 dalı |
| `_train_adapter` | `dau/diagnostics/run_protocol_c_prime.py:950` (**`lora_update.py`'de değil**) |
| `TransferCandidate` | `dau/foundation/generation.py:55` |
| **Metabolik kazanç** (D-066) | `dau/society/extraction.py` → `metabolic_gain` |
| **Gerçekleşen çıkarım** (D-066) | `dau/society/environment.py` → `realized_extractions` / `realized_extraction_at` |
| **Enerji kredisi + S5 kaydı** (D-066/D-063) | `dau/foundation/graph.py` → `pool_step_node` |
| **Ölüm eşiği** (D-066) | `dau/foundation/graph.py` → `should_continue` |
| **Kasa saati** (D-067) | `dau/memory/store.py` → `vault_counter` / `seal_phase` |
| Gate altyapısı | `dau/diagnostics/preflight.py` (**1208** satır) + `tool_identity.py` (**257**) |
| Multigen orkestrasyon | `dau/diagnostics/run_cprime_multigen.py` (**1476**) + testi (**1799**) |

- `CLAUDE.md` **repo kökünde** durur — Claude Code onu yalnızca kökten
  otomatik yükler.
- Deep Research arşivi: `docs/research/` (ham brief'ler + `RECONCILIATION.md`).
- Ham ölçümler: `dau_runs/*.json`. Bugünküler: `u3_model_diversity_*`,
  `vram_train_peak_nf4`, `nli_score_distribution`, `lr_probe_*`,
  `exploratory_greedy_vs_sampled_50events`.

---

# 8. Master Reference — v2.4.2 yazıldı

`docs/DAU_MASTER_REFERENCE_v20.md` **v2.4.2** (2026-08-11). Anlatı yeniden
yazılmadı — **yanlışlar yerinde işaretlendi, eksik katman eklendi.**

**Eklenen:** §24 preflight değişmez sistemi + alet kimliği (v2.4.1'de **hiç
yoktu**) · §25 karar kaydı sistemi, D-001…D-044 · §23 baştan yazıldı
(eski hali beş yerde "pre-reg sıradaki oturumun İLK görevi" diyordu).

**⚠ ile işaretlenen yanlışlar:** `W=10` beş yerde (D-036) · greedy plato
reçetesi (D-026 çürüttü) · §21'in NLI satırı (iki kez eskidi: parantez zaten
yanlıştı, sonra D-032 kapıyı kosinüse çevirdi) · sampling reçetesi (S1 greedy)
· §18 empirik tablosu ve §10b verdict'i (üç kırılma: D-036 pencere, D-037
determinizm, D-042 konum; ayrıca D-044 uç nokta duyarlılığı).

**§18'e eklenen:** bugünkü aletle alınan sayılar (baseline/repro/control),
"keşifsel, N=3, hipotez testi değil" etiketiyle.

⚠ **`.html` ve `.pdf` v2.4.1'de kaldı** — md tek güncel kaynak.

**Kalan borç:** §6/§19'un consolidation anlatısı (D-022/D-031 ile eskimişti,
işaretlenmedi) · §12 kod ağacı `preflight.py`/`tool_identity.py`'yi listelemiyor
· §11/§14'ün test sayıları eski. Hiçbiri okuyanı yanlış yöne sokmuyor.

# 9. Araştırma Kanalı: Gemini Deep Research

Mimari kararlarda sıkışıldığında veya yeni bir katmana girmeden önce geniş
literatür taraması **Gemini Deep Research** ile yapılır. Yedek değil, karar
sürecinin bir organı.

## Hangi soruyu kim cevaplar (D-007)

| Soru tipi | Kim |
|---|---|
| "Biz neye karar vermiştik / neden böyle yaptık" | git geçmişi + Yasin; Claude Code kazar |
| "Kod gerçekten ne yapıyor" | Claude Code, read-only denetim |
| "Literatürde X mi Y mi savunulabilir" | Gemini Deep Research |
| "Bu deneyde X mi Y mi olsun" | **Yasin** (DR + Claude Code girdi verir) |

Provenans sorusu DR'ye **sorulmaz** — commit geçmişine erişimi yok, makul
görünen ama kaynaksız metin üretir.

## Süreç (D-006)

Brief `docs/research/YYYY-MM-DD_konu.md` olarak **dosya** halinde girer
(sohbete yapıştırılmaz). Claude Code her iddia için mutabakat tablosu üretir:
brief ne diyor / kod ne yapıyor / karar ∈ {**bilinçli sapma · fark edilmemiş
kayma · uyumlu · brief yanılmış**}. Sapmalar `DECISIONS.md`'ye, kaymalar
buraya GAP olur.

## ⚠ Brief'lerin sicili — bugün ölçüldü

| Brief iddiası | Yerel doğrulama |
|---|---|
| 08-08~: Qwen "şiddetle önerilir", "keskin logit ayrımı" | ❌ **düştü** — Qwen medyan `n_unique` 4, kapı 5, Llama 9 (D-026) |
| 08-08~: VRAM farkı ~800 MiB | ❌ **düştü** — ölçülen 142 MiB |
| 08-10: NLI yapısal olarak yanlış araç | ✅ **doğrulandı ve güçlendirildi** |
| 08-10: NLI skorları 0.01–0.20 bandında | ❌ **yanlış** — medyan 0.0024 |
| 08-10: lr 5e-5 unlikelihood push yaratır | ✅ **doğrulandı** (D-029) |
| 08-10: lr 5e-5 genel dil yeteneğini bozar | ⚠ **gözlenmedi** — ama tek atış, dışlanmadı |
| 08-10: M-DPO `arXiv:2506.08965` (2024) | ❌ **kimlik/yıl çelişkili** — kullanılmadı |

**Ders:** brief **iddia**, kanıt değil. Her iddia kodda doğrulanır;
doğrulanmadan bu dosyaya "kilitli karar" yazılmaz. Kaynak kimliklerini de
kontrol et.

---

# 10. Roller ve Cursor'a Devretme

- **Yasin:** yön, onay, karar (D-007), Claude Code ↔ Cursor köprüsü.
- **Claude Code:** triyaj, ölçüm, onay sonrası implementasyon, test, commit,
  D-kaydı, Cursor prompt'u üretme.
- **Cursor:** yalnızca "CURSOR'A DEVRET" etiketli mekanik işler.

## Devretme kuralı

**Cursor'a uygun** (mekanik, düşük risk, tersine çevrilebilir): magic number →
sabit taşıma · **zaten karara bağlanmış** DOC_MISMATCH düzeltmeleri ·
TEST_GAP doldurma · basit temizlik · tek dosya tek fonksiyon dar değişiklik.

**Claude Code'da kalır:** herhangi bir GAP · iki karar arasında seçim ·
`constraints.py` **değer** değişikliği · multi-gen orkestrasyon, LoRA gate,
memory-vault senkronizasyonu.

**Nasıl:** Claude Code kod değişikliğine girişmez; Yasin'e *"Bu iş Cursor'a
uygun — [1 cümle gerekçe]"* der ve **kopyala-yapıştıra hazır, dar kapsamlı**
bir prompt üretir. Prompt'ta **YAPMA** listesi bulunur. Çıktı gelince Claude
Code diff'i okur, suite'i koşar, commit eder.

**Bugünkü örnek** (`9ce5269`): prompt'a "kimlik testi `LLM_BACKEND_VALID`
üzerinden olsun" yazıldı — çünkü kısa string'ler intern edilir ve
`LLM_BACKEND_DEFAULT` üzerinden `is` testi tekilleştirmeyi kanıtlamazdı.
**Cursor'a verilen prompt bu tür tuzakları önceden içermeli.**

## Şu an Cursor'a uygun bekleyen işler

**Faz C'ye kadar hiçbiri başlatılmaz** (Yasin: belge borcu işler bittikten
sonra). Faz C geldiğinde:

1. Master ref §12 kod ağacına `preflight.py` + `tool_identity.py` ekle.
2. Master ref §11/§14 test sayılarını güncelle (206 → güncel).
3. `PREFLIGHT_INVARIANTS.md`'ye "kodda uygulandı mı" sütunu (20/25).
4. `dau_runs/*.json` etiketleme: hangi koşum hangi alet sürümünden.

⚠ Master ref §6/§19'un consolidation anlatısı **Cursor'a uygun değil** —
D-022/D-031'in ne dediğine karar vermek gerekiyor, mekanik değil.
