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

# 1. Şu An Neredeyiz (2026-08-11, akşam)

- **Branch:** `cursor/per-agent-qlora-adapter-c116`. main'e taşınmadı —
  gerçek diverjans var, ertelendi (**D-013**).
- **Suite:** `344 passed, 2 deselected`. Çalışma ağacı temiz.
- **Son D-kaydı: D-049.** Sıradaki kayıt **D-050** olarak açılır.
- **GAP-2 ve GAP-6 kapandı** (`d65100d`, `b66f7fc`); açık GAP'ler:
  3, 4, 5, 9, 10, 17, 18, 19 — **her birinin tetiği §1'deki GAP TETİK
  TABLOSU'nda.**
- **Son GAP: GAP-20** (D-033 ile açıldı ve kapandı). Sıradaki **GAP-21**.
- **Değişmez sayısı: 24** (I1.3/I1.3b/I1.4/I1.5 **D-046** ile eklendi).
  Belgede tanımlı 26'nın ikisi kodda yok — I1.2 testte, I2.3 yapısal.
- **Ön-kayıt taslağı:** `docs/PREREGISTRATION.md` — **KİLİTLİ DEĞİL**.
  **Altı slot kapandı** (S1 greedy · S3 α=0.05 · **S4 SESOI yok, bütçeden
  N — D-047** · S5 1 epoch · S6 replay yok · S7 50/20/3); **yalnız S2 (N)
  açık** ve kilidi o tutuyor. **On iki ilan edilmiş sınır** (L11/L12 D-047).
- **Master reference: v2.4.2** yazıldı (§8).
- **Üç DR cevabı da geldi ve işlendi** (D-047 §G · D-048 §H · D-049 §I).
  DR kanalı bu ön-kayıt için **kapandı**.

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

## ▶ ÇALIŞMA KUYRUĞU — sıradaki iş buradan alınır

**"devam et" denince:** kuyruğun en üstündeki ✅ olmayan satırı al, §2.3
gereği analiz→öneri→onay ile ilerle. Kuyruk sırası **Yasin tarafından
onaylandı (2026-08-11)**; sıra değiştirmek yeni onay ister.

### Faz A — kilitten önce (pencere kapanınca biter, §2.10)

| # | İş | Süre | Durum |
|---|---|---|---|
| ~~A5~~ | ✅ **D-045** — gen2 de kayıplı, S4 sınırı L10 olarak yazıldı | — | ✅ |
| ~~A3~~ | ✅ **D-046** — I1.3 (daraltıldı) · I1.3b (yeni) · I1.4 (spec tautolojiydi, çevrildi) · I1.5 (`MIN_PAIRS` config'den) | — | ✅ |
| ↳ | ✅ **GAP-6 kapandı** (`b66f7fc`) — temizlik swap'e değil **DPO adımına** kondu | — | ✅ |
| **A6** | `lived − shuffle` tutarsızlığının **kalan kısmı**. D-044 bir parçasını açıkladı (iptal artefaktı), tamamını değil. ⚠ **D-045 yeni bir iz bıraktı:** `null` varisinin ikinci-yarı PE çöküşü — A6 buradan başlasın. Analiz, GPU yok | ~1 sa | ⬜ |
| ↳ | **GAP-5 ve GAP-4 buraya bağlı** — tetik tablosu | +1,5 sa | ⬜ |
| **A7** | **GAP-19 kararı** — faz-1/faz-2 sayaç uzayı. Neyin eğitildiğine dokunuyor, kilitten önce karara bağlanmalı. ⚠ **D-045 ona bir gözlem borçlu**: gen2'nin zamana bağlı iptali GAP-19'un öngördüğü desene benziyor | ~1 sa | ⬜ |

**Ertelendi, bilerek:** **A2** (OOD probing) ve **A4** (environment'ı ayrım
üretir hale getirme). İkisi de değerli, ikisi de bu ön-kaydı **günlerce**
bekletir. §2.10'un uyardığı "önce şunu da düzeltelim" kuyusu tam olarak
bunlar. → ikinci ön-kayıt / popülasyon çalışması.
⚠ **A2'nin tasarımı zaten kusurlu çıktı (D-049/I12):** "getirimi tamamen
kapat" OOD şoku ölçer, parametrik kapasiteyi değil. Yerine **plasebo anı
enjeksiyonu** geçecek — sonraki ön-kayıt.

### Faz B — kilit ve sonrası (S4 gelmeden başlayamaz)

| # | İş | Süre | Durum |
|---|---|---|---|
| **A8** | **S2 (N) kararı.** DR bütçeden `N=32` diyor (MDE `d_z=0.511` iki yönlü, doğrulandı); GAP-9'un dayandığı brief Protocol C için **N=40–50** diyordu. İkisi uzlaştırılmadan kilit yok. ⚠ `resource` atıl (L11) ⇒ N ne alınırsa alınsın ayrım ikinci alandan gelecek | ~45 dk | ⬜ |
| **B1** | Pre-reg'i güncelle, `tool_identity` dondur, **kilitle** | ~45 dk | 🔒 A8 |
| **B2** | **Doğrulayıcı koşum, seed 2004'ten.** ⚠ 2001–2003 yakılmış (D-038) | N×20 dk +7 | 🔒 B1 |
| **B3** | Ön-kayıtlı analiz: birincil + altı ikincil, düzeltmesiz | ~1 sa | 🔒 B2 |
| **B4** | Rapor + on ilan edilmiş sınır + null ise mekanizma/alet ayrımı | ~2 sa | 🔒 B3 |

### Faz C — işler bitince (Yasin: "belge borcu işler bittikten sonra")

Master ref §6/§19 consolidation anlatısı · §12 kod ağacı (`preflight.py`,
`tool_identity.py` yok) · §11/§14 test sayıları · **`.html`/`.pdf` v2.4.1'de
kaldı** · `EXECUTION_PLAN.md` (D-038…D-044 hiç geçmiyor) ·
`PREFLIGHT_INVARIANTS.md` uygulanma durumu sütunu. **Cursor'a uygun.**

---

## ▶ GAP TETİK TABLOSU — ne zaman gündeme getirilecek

Yasin'in talimatı: *"GAP'ler için uygun zamanı gözet, o an geldiğinde
hatırlat ve neden o anın optimal olduğunu belirt."* Aşağıdaki **Tetik**
sütunu bağlayıcı — o adıma gelindiğinde GAP **kendiliğinden** gündeme gelir.

| GAP | Tetik | Neden o an optimal | Nasıl çözülür |
|---|---|---|---|
| **GAP-5** | **A6'dan hemen sonra** | A6 `lived−shuffle`'ın kalanını arıyor. SYSTEM_PROMPT'un `decision_to_outcome` kelimelerini primlemesi tam da o kalanın adayı — **aynı veriye bakarken** sormak ikinci bir tur gerektirmez. Ve kilitten önce bilinmeli: gerçekse davranışsal ölçümün geçerliliğini daraltır | Yerel denetim (ucuz) + DR brief #3'ün kapsamında |
| **GAP-4** | **A6 ile birlikte** | Kanal kirlenmesi sorusu. A6 zaten kolların nerede ayrıştığına bakıyor; vault↔LoRA senkron kopukluğu **kodda hiç doğrulanmadı** ve read-only denetim aynı oturumda biter | Read-only denetim (Claude Code) |
| **GAP-19** | **A7 = kendisi** | Neyin eğitildiğine dokunuyor. Kilitten sonra değiştirilirse post-hoc olur | Karar + D-kaydı (Yasin onayı) |
| **GAP-9** | **A8'de** | S4 kapandı (D-047) ama GAP-9 kapanmadı: DR `N=32`, eski brief `N=40–50` diyor. A8 tam olarak bu uzlaşma | A8 kararı + D-kaydı |
| **GAP-18** | **B2'nin `uniq_rejected` sayısı gelince** | Cevap geldi (D-048) ama **şiddeti hiç ölçülmemiş** çıktı: "2 benzersiz negatif" 10 olaylık replay'den, "47 çift" 50 olaylık koşumdan. Sayaçlar eklendi (`daa5f4b`); karar sayıdan sonra | B2 ölçümü → sonra karar |
| **GAP-3** | **B1'de (kilit anı)** | Gen2 ikincillerini etkiliyor, ve o ikinciller zaten L10 ile sınırlı. Düzeltmek yerine **ilan edilmiş sınır** olarak yazmak dürüst ve ucuz. ⚠ D-045 onu `null` varisinin ikinci-yarı çöküşü için **mekanizma adayı** olarak da işaretledi | Sınır olarak ilan et |
| **GAP-10** | **B1'de (kilit anı)** | `W_SEM=0.0` değiştirilirse **taban yine sıfırlanır**. Kilitten önce dokunmak pahalı, kilitten sonra yasak ⇒ bu ön-kayıt için **sınır**, sonraki için iş kalemi | Sınır olarak ilan et |
| **GAP-17** | **B4'te (rapor)** | Karşılaştırma tabanı delil olarak kullanılamıyor; bisect pahalı ve sonucu bir şeyi değiştirmiyor. Raporda "açıklanmadı" diye geçer | Raporda not |

---

## ▶ DR BRIEF SIRASI — Yasin gönderecek

Üçü de yazıldı ve `docs/research/` altında hazır. **Sıra bağlayıcı**, ama
2 ve 3 birbirini beklemez.

| # | Brief | Neyi açar | Dosya |
|---|---|---|---|
| **1** | **S4 — en küçük anlamlı etki** | 🔒 **Kilidi bu tutuyor.** Cevap gelmeden B fazı başlayamaz. GAP-9 da bununla kapanır | `2026-08-11_S4-minimum-effect-of-interest.md` |
| **2** | **GAP-18 — ortak negatif / az çeşitli `rejected`** | Eğitim seti kalitesi. Kilidi bloke etmiyor | `2026-08-11_GAP18-shared-negatives-in-preference-learning.md` |
| **3** | **Lamarckçı kapsam + kanal ayrımı** | İddianın genişliği (1–2) ve **bir sonraki ön-kaydın mimarisi** (3–4). GAP-5'in literatür yarısı burada | `2026-08-11_lamarckian-scope-and-channel-separation.md` |

Cevap gelince: her iddia için mutabakat tablosu → `RECONCILIATION.md`.
⚠ Brief **iddia**, kanıt değil — sicil §9'da, yedi iddiadan dördü çürüdü.

---

## ▶ EV İŞLERİ — tetiklendiğinde

| İş | Tetik | Not |
|---|---|---|
| **`archive/` 2.3 GB, 15 dizin** | **B2'den önce** | Doğrulayıcı koşum N×2 yeni adapter yazacak; disk payı önceden açılmalı. `.gitignore`'da, silinebilir — ama D-042/D-043'ün kanıt adapter'ları hangisi diye bakılmalı |
| **`dau_runs/` 33 JSON etiketleme** | **Faz C** | Bir kısmı geçersiz (D-036/037/042 öncesi). Silinmemeli, etiketlenmeli |
| **D-013 — branch main'e taşınmadı** | **B4'ten sonra** | Gerçek diverjans var. Paper aşamasında ele alınır |

# 2. Yeni Oturum Protokolü (bağlayıcı)

## 2.1 İlk beş dakika — sırayla, atlamadan

1. **Bu dosya** (otomatik yüklenir) → §1'deki **ÇALIŞMA KUYRUĞU**. "devam et"
   denince kuyruğun en üstündeki ⬜ satır alınır, başka yere bakılmaz.
2. **GAP TETİK TABLOSU** — alınan adımın bir GAP tetiği var mı? Varsa
   **Yasin'e hatırlat ve neden o anın optimal olduğunu söyle** (talimat,
   2026-08-11).
3. **`docs/DECISIONS.md`** — ilgili D-kaydı. En çok bağlam taşıyanlar:
   **D-036** (ölçüm penceresi) · **D-037** (tekrarlanabilirlik) · **D-042**
   (konum bağımsızlığı) · **D-044** (uç nokta duyarlılığı).
4. **`docs/PREREGISTRATION.md`** — beş slot kapalı, S4/S2 açık, on ilan
   edilmiş sınır. Kilitli **değil**.
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

## 2.10 Ön-kayıt penceresi hâlâ açık

Pre-reg yazılmadı → alet değişikliği hâlâ meşru, ama her biri D-kaydı ister.
**Pre-reg kilitlendiği an bu pencere kapanır** ve aynı değişiklik post-hoc
olur. Bugünün dokuz kararı bu pencerede meşruydu.

⚠ Ama pencere sonsuz değil: alet bugün **on bir kez** değişti ve bu haliyle
**bir kez bile uçtan uca koşmadı**. Pilot bunun için var.

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
| Gate'i kodlarken | `docs/PREFLIGHT_INVARIANTS.md` (25 madde tanımlı, **20'si kodda**) + `dau/diagnostics/preflight.py` |
| "Bu dosyanın sessiz yolları neler?" | `docs/RUNPATH_AUDIT.md` (K1–K8) |
| Alet/literatür kararı öncesi | `docs/research/RECONCILIATION.md` |
| Formül · tarihçe · empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` **v2.4.2** — yanlışlar ⚠ ile işaretli, §24/§25 yeni |
| Ön-kayıt: slotlar, uç noktalar, **on ilan edilmiş sınır** | `docs/PREREGISTRATION.md` (kilitli değil) |
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

### GAP-19: faz-1 ve faz-2 anıları aynı sayaç uzayını paylaşıyor (D-031)
Faz-2 taze gövdeyle başlıyor (`initial=None`), `event_log` sıfırdan sayıyor —
faz-1 anıları faz-2'ninkiler kadar taze görünüyor. Ebbinghaus decay
`now_counter − last_activated_counter`'a dayandığından **unutma kararını
doğrudan** etkiliyor. U6'nın getirdiği sorun değil; ama consolidation
bağlandığı için **ilk kez etkisi olacak**.

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
Gate I5.4 bunu koşumda raporluyor.

### GAP-4: Memory-vault ↔ LoRA senkron kopukluğu (kodda doğrulanmadı)
Ebbinghaus ile kasadan silinen anının yarattığı drift LoRA'da kalıcı
kalabilir. ⚠ **U6 bunu canlı hale getirdi** — deney yolunda unutma artık
gerçekten çalışıyor, yani bu risk teorik olmaktan çıktı.

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

⚠ **Satır numaraları 2026-08-10'da doğrulandı ama kayar — `grep` ile teyit et.**

| Ne | Nerede |
|---|---|
| `build_pe_ranked_pairs` | `dau/foundation/lora_update.py:270` |
| `_encode_pair_side` (D-027 kesme) | `dau/foundation/local_llm.py:542` |
| `_run_dpo_epochs` (D-028 accumulation) | `dau/foundation/local_llm.py:684` |
| `build_load_kwargs` (D-020 quantization) | `dau/foundation/local_llm.py:122` |
| `_consolidate_gen1` (D-031) | `dau/diagnostics/run_cprime_multigen.py:687` |
| `run_lineage` | `dau/diagnostics/run_cprime_multigen.py:721` |
| `_pair_filter_report` (D-030/D-032) | `dau/diagnostics/run_protocol_c_prime.py:727` |
| Polarite kapısı (D-032) | `dau/foundation/polarity_filter.py` (NLI `nli_filter.py`'de durmaya devam ediyor) |
| Karar prompt'unun saklanması (D-032) | `dau/foundation/graph.py`, `agent_node` SYSTEM_2 dalı |
| `_train_adapter` | `dau/diagnostics/run_protocol_c_prime.py:756` (**`lora_update.py`'de değil**) |
| `TransferCandidate` | `dau/foundation/generation.py:55` |
| Gate altyapısı | `dau/diagnostics/preflight.py` (805 satır) + `tool_identity.py` (242) |
| Multigen orkestrasyon | `dau/diagnostics/run_cprime_multigen.py` (1153) + testi (~900) |

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
