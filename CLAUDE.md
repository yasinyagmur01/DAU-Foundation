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

# 1. Şu An Neredeyiz (2026-08-17) — ✅ **D-091 blokajı kapandı (D-092)**

- **Branch:** **`main`** tek branch (D-013 kapandı, **D-054**). Eski main
  `archive/main-pre-c116` etiketinde. B2'nin koştuğu kod **`prereg/b2-code`**
  etiketinde. ⚠ **`origin/main`'in önünde on beş commit** — push edilmedi.
- **Suite:** `441 passed, 2 deselected`. Çalışma ağacı temiz (`43b4220`+).
- **Son D-kaydı: D-097.** Sıradaki kayıt **D-098** olarak açılır.
- **Bugün (2026-08-13) kapananlar:** W1/W2/W3 (D-062…D-064) · DR #4 mutabakatı
  (D-065, §J) · A4-① (D-066) · GAP-19 (D-067) · ilk pilot (D-068) · yerel
  tarama (D-069, §K) · yedi kilit karar (D-070) · **K4-b (D-071)** ·
  **landmark aletlemesi (D-072)** · **LOCF kaldırıldı (D-073)** · **sıralama: ② kilitten önce (D-074)** · **popülasyon taraması (D-075, §L)**.
- **2026-08-17:** model erişimi kontrol edildi (**etkilenmiyoruz**) · ⛔ **davranış çöküşü artefakt olabilir (D-091)** · Yasin **üç kararı verdi** · ✅ **eşleme onarıldı (D-092)** · ⭐ **havuz aritmetiği yeniden hesaplandı, davranış ilk kez ortamı değiştiriyor (D-093)** · ⭐⭐ **P2/P3/P4 kilitlendi ve E4 yazıldı (D-094)**.
- **2026-08-14:** DR #6 mutabakatı (**D-076**, §M) · ② tasarım önerisi + **P0 bulgusu (D-077)** · **P0 ölçüldü ve E3 uygulandı (D-078)** · **P0 taraması (D-079, §N)** · **DR #7 mutabakatı (D-080, §O)** · **havuz aritmetiği + landmark önerisi geri çekildi (D-081)** · **DR #8 mutabakatı: Holling II üçüncü yol (D-082, §P)** · **rotasyon ölçüldü + prompt kanalı tam duyarlı (D-083)** · ⛔ **karar kanalı doygun çıktı (D-084)** · ⭐ **doğrulama koşumu: uygunluk kapısı kalıtımın %90'ını kesiyor (D-085)** · ✅ **`F_agent` enerji terimi düzeltildi (D-086)** · ⛔ **aktarım eşiği yanlış niceliğe uygulanmış + D-086'nın yan hasarı (D-087)** · ✅ **salience çıtası geri verildi (D-088)** · ⭐ **kalıtım akıyor, doğrulandı (D-089)** · ⭐⭐ **karar kanalı ölü değil: drift ekseninde temiz eşik (D-090)**.
- ⚠ **Evrenin fiziği değişti (D-066/D-067), sonra ölçüm aleti değişti
  (D-071/D-072/D-073).** `dau_runs/`'daki **hiçbir** koşum bugünün aletiyle
  karşılaştırılamaz.

---

## ▶▶ SIRADAKİ İŞ — ⛔ **iki ölçüm borcu, sonra Kuşak 1 (C/D/E)**

✅ **D-091 blokajı kapandı (D-092, `53fdf04` + `67ba99f`).** Eşleme onarıldı,
0a-2 ve 0a-3 koşuldu. ⇒ Sıradaki iş **Kuşak 1'e girmeden önce iki yeniden
hesap**, çünkü D-092 üç sayıyı birden geçersiz kıldı.

### ✅ D-092 ne yaptı — üç cümlede

`decision_to_outcome` artık *"take a moment"* (deyim) ve *"extract
**information**"* (nesne havuz değil) kullanımlarını eşlemeden **önce**
ayıklıyor; yalnız **fiil** siliniyor, çevresi kalıyor. Dal sırası bilerek
değişmedi — reddedilen iki alternatif (`en çok anahtar` / `ilk eylem`) hasat
miktarını **retoriğe** bağlıyordu ve 36 metnin **17'sinde** ayrışıyorlar.

| ölçüm | önce | **sonra** |
|---|---|---|
| sentetik ızgara (36 çağrı, metinler **36/36 birebir aynı**) | 35 defect / 1 coop | **20 / 16** |
| **canlı koşum** gen2 `defect` payı (N=2) | 78.4 % | **53.3 %** |
| canlı `cooperate` payı | 2.0 % | **30.5 %** |
| ömür sonunda havuz ölü | 6/6 soy | **5/6 soy** |

⛔ **D-090'ın ⭐⭐ bulgusu düştü:** drift ekseni artık tekdüze değil
(D D D C C C C → **C D C C C C C**). ✅ **Enerji havzası birebir ayakta.**
⇒ **D kararının drift yarısı zayıfladı, enerji yarısı duruyor.**

~~⛔ Bedeli: `fitness_class` 6/6 `normal`~~ ⇒ ✅ **çürütüldü (D-093)** —
N=4'te yayılım **0.239** (D-089'un 0.210'unun üstünde), sınıflar 10 `normal`
+ 2 `low`. **Tohum etkisiymiş.** ⚠ Açık madde **A** (`high` bandı) 12/12 boş,
yerinde duruyor; madde **B** (`landmark_energy` doygunluğu) **1/12**'ye düştü.

### 🚧 Kuşak 0 — kalan iki iş *(Kuşak 1'in önünde)*

| # | İş | Durum |
|---|---|---|
| ~~0a~~ | Eşleme düzeltmesi + mutasyon kontrollü test + D-092 | ✅ `53fdf04` |
| ~~0a-2~~ | D-090 taraması yeniden (57 çağrı, 198 sn) | ✅ **drift eşiği düştü** |
| ~~0a-3~~ | Doğrulama koşumu N=2 (seed 5008–9) | ✅ `dau_runs/validate_d092_n2.json` |
| ~~0c~~ | Havuz aritmetiği yeniden hesaplandı | ✅ **D-093** — kıtlık anı 17 → **28**, kapasite 67 → **50** |
| ~~0d~~ | `fitness_class` daralması ölçüldü | ✅ **D-093** — **tohum etkisiymiş**; N=4'te yayılım **0.239** (D-089'un üstünde) |
| **0b** | `SYSTEM_PROMPT` kelime dayatması (*"prefer … extract, take"*) | ⏸ **Yasin'in** — rakam artık var, oranlar **hâlâ o prompt'un altında** alındı |

⭐⭐ **D-093'ün asıl bulgusu — ①'in aradığı simetri kırılması görünüyor.**
Eski eşlemede altı soyun **altısı** havuzu öldürüyordu; N=4'te **12 soyun 4'ü**
20 olay boyunca öldürmüyor, ve fark **davranıştan** geliyor (çökmeyenlerin
ortalama hasadı **4.612**, çökenlerin **7.411**). En temiz örnek seed 5011:
olay başına **2.625**, `cooperate` **%56**, havuz sonunda **0.791**.
⇒ **D-084'ün *"ayrım ancak ortam kuralıyla gelir"* öncülü düştü.**
⚠ *"Havuz korunuyor"* **denmez** — 4.612 de MSY'nin (3.75) üstünde, kıtlık
yalnız 45. olaya kayıyor, yani pencerenin dışına.

⛔ **C kararı hâlâ bekliyor:** D-082'nin Holling II tablosu `d = 8.0`/olay
üzerine kurulu, **yeniden hesaplanmalı** (0c bunu D-081 için yaptı, D-082 için
yapmadı).

### ⛔ Kuşak 1 — evrenin fiziği *(üçü de Yasin'in, 0c bitmeden sorulmaz)*

| # | Karar | Not |
|---|---|---|
| **D** ⭐ | **Çıkarımın bedeli olsun mu** | ⚠ **D-092 gerekçeyi yarıya indirdi:** D-090'ın drift eşiği düştü, **enerji havzası ayakta** ⇒ *"bedel ajanları düşük enerjiye iter"* duruyor, *"drift'i artırır"* dayanaksız. Ölçümü hâlâ **yarıda** |
| **C** | Hasat kuralı — sabit kota / **Holling II** (+ `h`) | ⛔ **0c'den önce sorulmaz** — bütün aritmetiği *"%94–100 DEFECT"*a oturuyordu, gerçek oran **%53** |
| **E** | **P0 = ①** + aksiyom sorusu | ⚠ D-090 çerçeveyi değiştirdi: *"özdeş karar veren ajanlar"* **zorunlu değilmiş**. ⭐ D-092 bunu **güçlendirdi**: davranış artık %30 `cooperate` üretiyor |

### 🎯 Kuşak 2 — asıl hedef, hiç dokunulmadı

| # | İş | Durum / bağlı |
|---|---|---|
| ~~**E4**~~ ⭐⭐ | **Üreme: turnuva k=2, `w` sayacı, varis üretimi + Price ayrışması** | ✅ **D-094** (`374906c`) — `dau/generation/reproduction.py`, 12 test, dört mutasyon ⚠ **bağlı değil** |
| ~~E1/E5~~ | Havuz adımı N ajana çıktı (`advance_commons`) | ✅ **D-097** (`43b4220`) — N=1 yolu `--mock-llm` ile **birebir** doğrulandı, üç mutasyon |
| **E2** ⬜ | N ajanı olay bazında ilerleten dış döngü | ⭐ **tek kalan kod işi** · `advance_commons` arayüzü hazır · ⚠ **denetimsiz yapılmaz** |
| — | E4'ü orkestrasyona bağla + `TOURNAMENT_K`'yı alet kimliğine ekle | E1/E5 + E2 |

⭐ **Linçpin teknik olarak çözüldü:** `w` artık değişken olabiliyor ve Price
kimliği testle korunuyor (`test_price_identity_holds_exactly`). ⛔ **Ama hâlâ
hiçbir koşum seçilim ölçmüyor** — modül bağlanana kadar.

### ✅ P1 ve P6 kilitlendi (D-095) — ⛔ P7'de **iki** soru açık

| # | Karar | Durum |
|---|---|---|
| ~~P1~~ | Havuz paylaşımı | ✅ **kol başına ayrı havuz.** ⚠ İlan edilecek sınır: iddia birey düzeyinden **grup düzeyine** kayar (Chevin 2011) |
| ~~P6~~ | İki faz | ✅ **tek faz.** ⛔ Bedeli: **`delta_pe` uç noktası kaybolur**, S3/S4 yeniden yazılır |
| **P7-a** | **Bütçe tavanı (kaç saat GPU)** | ⛔ **tek kalan sayı sorusu, Yasin'in.** Üçlü tavandan **türetilir**, seçilmez (§2.7). Üç eksen ayrı iş yapıyor: **N** → Price kestiriminin *yanlılığı* (Rice 2008) · **G ≥ 5** → birikimli kalıtım iddiası (D-014/D-074) · **tohum** → *kesinlik* (D-076: tekrar > N) |
| ~~P7-b~~ ⭐ | Hipotez testi mi, kestirim mi | ✅ **kestirim (D-096).** ⇒ en küçük anlamlı etki ilan etmek **gerekmiyor** · birincil slot **test değil kestirim** · geçiş kapısı **`Var(w) > 0`** (tanım, kalibre eşik değil) · **null sonuç meşru çıktı** · bütçe artık *"ne harcayabiliriz"* sorusu |

### ✅ E1/E5 kapandı (D-097) — ⬜ **tek kalan kod işi E2**

`advance_commons(env, [CommonsRequest, …])` yazıldı; `pool_step_node` onun
**N=1 çağıranı**. ⭐ `CommonsRequest.event_counter` **ajanın** saati, ortamın
değil — havuz tur başına bir tik atarken her yaşam kendi olayını sayıyor.

Davranış korunumu iki yoldan doğrulandı: **441 passed**, ve `--mock-llm` ile
aynı tohumda refactor **öncesi/sonrası** `arm_digest` · gen2 `pe_list` ·
`f_agent` · `extraction_by_event` **birebir aynı**.

⚠ **Yan bulgu (D-097/§3):** anı kayıt id'leri `uuid4()` tabanlı ⇒ **aynı kodun
iki koşumunda da değişiyor**. Digest'i, anı sayısını ve uç noktaları
etkilemiyor, ama `inherited_memory_ids` **replay kanıtı olarak kullanılamaz**.
İlan edilmiş sınır olarak kaydedildi, kusur açılmadı.

⚠ **Hâlâ hiçbir şey N ajanla koşmuyor** — eklenen şey bir **yetenek**, bir
koşum değil.

### 📋 Kuşak 3 — ikinci ön-kayıta ertelendi

`fitness_class`'ın boş `high` bandı · `landmark_energy` doygunluğu (1/6
tavanda) · KTO kararı · `lr` bandı · uç nokta seçimi · DTW · MAP-Elites

### ⚠ Ölçüm borcu — D-092 sonrası **güncellendi**

| kayıt | durum |
|---|---|
| **D-090 Bulgu 3** (drift eşiği) | ⛔ **düştü** — eşlemenin eseriymiş |
| D-090 Bulgu 2 (enerji havzası) | ✅ **ayakta, birebir** |
| **D-068** (%94–100 defect) | ⛔ sayı geçersiz ⇒ **%53** (N=2, keşifsel) |
| **D-084** (karar kanalı doygun) | ⛔ **öncülü düştü (D-093)** — davranış ayrışıyor ve ortamı değiştiriyor |
| **D-081** (kıtlık anı, kapasite) | ✅ **yeniden hesaplandı (D-093)** — 17 → 28, kapasite 67 → **50** |
| **D-082** (Holling II tablosu) | ⬜ **hâlâ `d = 8.0` üzerine kurulu** — C kararından önce |
| **D-060** (`fitness_class` dejenerasyonu) | ✅ **D-093** — dejenerasyon yok, 10 `normal` + 2 `low` |
| **K7** (*"çöküş bulgudur"*) | ⚠ öncülü **iyice zayıfladı** — N=4'te 12 soyun **4'ü** havuzu öldürmüyor |

---

## ▶ ÖNCEKİ SIRADAKİ İŞ — aletin iki ölü kanalı (D-085) ✅ kapandı

⭐ **Doğrulama koşumu yapıldı (D-085, N=4 tohum, ~29 dk).** Bugünkü aletle
**ilk kez** uçtan uca soy koşuldu. **Ölçüm makinesi çalışıyor** — landmark
**12/12** soyda okundu, replay birebir, aletleme canlıda yazıldı. ⚠ **Ama
evrende iki şey ölü, ve popülasyon bunların üstüne kurulursa ikisi de miras
alınır:**

| # | Bulgu | Sayı |
|---|---|---|
| **1** | **Uygunluk kapısı kalıtımın %90'ını kesiyor.** `w_transfer = memory_score × F_agent × valans`, eşik **0.6**; `memory_score ≤ 1` olduğu için `w_transfer` **`F_agent`'ı aşamaz**. Ölçülen `F_agent` **0.084–0.184** | kapı açıkken **4** anı / 12 soy · `f_agent=None` kolunda **39** |
| **2** | **`fitness_class` yine 12/12 `low`** — D-060'ın dejenerasyonu A4'ten sonra geri gelmiş. ⚠ Ama `F_agent`'ın kendisi ayrım taşıyor ⇒ sorun **eşiklerde** | 12/12 |
| ~~**3**~~ | ✅ **D-086 — kapandı.** Enerji terimi artık **ömür-boyu ortalamayı** okuyor, ölüm anındaki sıfırı değil. `F_agent` **0.14 → 0.45**, sınıf dağılımı 12 low → **11 normal**. ⚠ Landmark alternatifi **reddedildi**: K2'nin uç noktasıyla döngüsellik (Mills & Beatty) | `energy_lived`, commit `f3a132d` |
| **4** | ⚠ `landmark_energy` **12'nin 5'inde tavanda** (1.000) ⇒ K2'nin seçtiği okuma **doygunluk riski** taşıyor; `energy_mean_over_life` (0.59–0.86) daha ayırt edici | 5/12 |
| **5** | ⭐ Ayrım **gen2 ömründe** görünüyor: 5004'te lived **14**, null/shuffle **10** | ⚠ hücre başına N=1 |

⇒ ⭐ **Sıra değişti:** P0 (ajanlar nasıl farklılaşacak) hâlâ Yasin'in, ama
**önce aletin kendi kanalları açılmalı** — yoksa popülasyon kurulduğunda
kalıtım akmıyor, uygunluk tek sınıfta toplanıyor ve seçilim yine ölçülemiyor.

### ✅ Alet kanalları AÇILDI — D-086 → D-088 → D-089 zinciri kapandı

| | ne yapıldı |
|---|---|
| **D-086** | `F_agent`'ın enerji terimi ölüm anı yerine **ömür-boyu ortalamayı** okuyor ⇒ `F_agent` 0.14 → 0.45 |
| **D-087** | ⛔ Ölçtü: `w_transfer` kapısı 12 soyda **0 anı** geçirmiş; eşik `memory_score` için kalibre edilip **çarpıma** uygulanmış (Layer-3 → Layer-4 kayması) |
| **D-088** | Salience çıtası **kalibre edildiği niceliğe** geri verildi. `0.6` **değişmedi**, uygulandığı nicelik düzeldi. `w_transfer` hesaplanıp raporlanıyor ama kapı değil |
| **D-089** | ⭐ **Doğrulandı:** aktarım **4/12 soy → 23/6 soy**, hiç almayan soy **8/12 → 0/6**, ve gölge kolla örtüşüyor (23 vs 22) |

⭐ **Yan kapılar da açıldı:** `I5.4` ilk kez **geçti** (*"applied 14x"*) ⇒
somatik miras varise gerçekten ulaşıyor · `fitness_class` **ilk kez ayrım
taşıyor** (4 `normal`, 2 `low`) · `I3.2` gen1'de **ilk kez geçti**
(`pi_n_distinct=9`), bayrak artık yalnız gen2'den geliyor.

### ⬜ Alette kalan iki küçük madde

| | İş | Aciliyet |
|---|---|---|
| **A** | `fitness_class`'ın **`high` bandı (≥0.70) hâlâ boş** | ⚠ düştü — iki bant artık dolu |
| **B** | `landmark_energy` tavanda **1/6** (D-085'te 5/12) | ⚠ azaldı, kalkmadı · **ön-kayıt kararı**, kod değil |

⇒ ⭐ **Alet işi burada kapandı.** A ve B ikinci ön-kayıt tartışmasına gider.

---

## ⭐⭐ D-090 — **karar kanalı ölü değil**, ve bu C/D/E'yi yeniden sıraladı

D-084 *"kanal doygun"* demişti ve **C/D/E'nin üçü de o tek ölçüme
dayanıyordu**. ⚠ Ama o **dar bir sondaydı**: çıplak `SYSTEM_PROMPT`, tek
durum, yalnız enerji. Gerçek prompt katmanlarıyla yeniden tarandı (57 çağrı):

- Geniş tarama: **35/36 `defect`** — ama **biri `cooperate`**.
- İstisna **tekil nokta değil**: aynı girdi 3/3 aynı (deterministik), ve
  enerji ekseninde **E ≈ [0.04, 0.08]** aralığında dört ardışık `cooperate`.
- ⭐⭐ **Drift ekseni temiz ve tekdüze:** `(1.0, 1.5]` arasında eşik, üstünde
  **dört ardışık `cooperate`**, tırtık yok. Gürültü değil **kaldıraç**.

⇒ **Doğru okuma:** davranış ölü değil — **ajanlar o bölgeye nadiren giriyor**.
`cooperate` *travma-bilgili + düşük enerjili* durumda çıkıyor ve bugünkü fizik
ajanları oraya sokmuyor.

### ⇒ Sıra değişti: **D önce**

| | Karar | Yeni durumu |
|---|---|---|
| **D** ⭐ | **Çıkarımın bedeli olsun mu** | *"Muhtemelen anlamsız"*dan **en umut verici kaldıraç**a döndü: bedel ajanları tam o bölgeye sokar (hızlı düşen enerji + artan drift). ⚠ **Dünyanın özelliği, davranışsal önsel değil ⇒ K7'yi açmıyor** |
| **C** | Hasat kuralı (sabit kota / Holling II) | ⚠ Bütün hesabım *"her ajan hep 8.0 alır"* varsayımına dayanıyordu; D bunu değiştirirse **yeniden hesaplanmalı** |
| **E** | P0 = ① ve aksiyom sorusu | ⚠ *"Özdeş karar veren ama farklı yaşayan ajanlar"* çerçevesi **zorunlu değilmiş** — davranış hareket edebiliyor |

⭐ **Ve D-089 bunu zaten genişletmiş olabilir:** kalıtım aktığı için varisler
**doğuştan** miras drift + anı taşıyor ⇒ bu bölgeye daha yakın başlıyorlar.
⚠ **Ölçülmedi, çıkarım.**

---

## ▶ P0 — **karar Yasin'in** (D-084 sonrası yeniden tarif edildi)

### 1. ✅ DR #7 mutabakata bağlandı (**D-080**, §O) — **P0'ı kapatmadı**

Ham cevap `docs/research/2026-08-14_DR7-answer-raw.md`. Altı iddia, altı
kimlik açıldı. **Sonuç P0'ı değiştirmedi ama tabloya ⑤'i ekledi.**

⭐ **Turun asıl çıktısı süreçte:** *"iddia kaynağın neresinde geçiyor"* şartı
**işe yaradı** — yerini gösterebildiğim iddia **6'nın 4'ü** (#6'da 13/13
*"Tam Uyumlu"* çıkıp **sıfır** ayırt etme vardı). Şart hataları engellemedi,
**yakalanabilir** yaptı: **altı iddianın üçü kendi alıntısının söylemediği bir
şey söylüyor**, ve ⚠ **yalnız DOI doğrulamasıyla üçü de geçerdi.**

- ❌ **İki kimlik hatası daha** (sekizinci ve dokuzuncu): `arXiv:2308.00179`
  *"Nishimura ve ark."* değil **Anwar & Georgalos** · `arXiv:0810.3070` ise
  **bambaşka bir makale** (alfa-Wiener köprüleri) ⇒ doğrusu **Rafferty,
  Griffiths & Klein 2014**, `10.1111/cogs.12112`. İkisi de **tamir edildi**.
- ❌ **①'i zayıflatacak gibi görünen tek iddia — *"birinci hamle avantajı"* —
  kaynağında yoktu.** DR iki **ters yönlü** bulguyu (Varian'ın kuramsal
  bedavacılığı + leading-by-example'ın **maliyetli** katkısı) tek cümlede
  birleştirmiş, üstüne *"ya da daha çok hasat eder"* eklemişti — o ifade
  kaynakta **hiç geçmiyor**.
- ⭐ **İki bağımsız yol aynı yere çıktı** (D-065/J20): DR'nin kaynağı
  **Suleiman 1996**'ya atıf veriyor (= §N'in W3'ü) ve **Bru 2003** = §N'in
  W4'ü.
- ⭐ **Konum etkisinin stratejik bileşeni bizde yapı gereği kapalı** — ajan
  sıradaki konumunu görmüyor (prompt'ta yok). Geriye **mekanik** bileşen
  kalıyor, ki aradığımız simetri kırılması odur.
- ⚠ *"Tohum değiştiremezsiniz"* uyarısı **bizim kısıtımızın yanlış
  okunması** — I0.6/D-037 aynı tohumun aynı sonucu vermesini istiyor, farklı
  tohumları yasaklamıyor (B2 **40 tohumla** koşuldu). ⚠ Kısmen bizim brief
  tarifimizden; **§9'un dersi dördüncü kez**.
- **Brief #8 için iki süreç düzeltmesi:** *kaynakça* istenecek (`[56]` hiçbir
  makaleye bağlanamadı) · *satır numarası değil* **birebir alıntı** istenecek
  (satır numaraları hiçbir kopyada tutmuyor; bulmayı sağlayan alıntıydı).

### 2. ⛔ P0 — **karar Yasin'in**, ve her şey buna bağlı

**Sorun (ölçüldü, D-078):** aynı nişte doğan iki ajan yaşam boyunca **bit
düzeyinde özdeş** kalıyor — dokuz nicelikte de. Popülasyon bunun üstüne
kurulursa N tane **aynı** ajan olur, `F_agent`'lar özdeş çıkar, turnuva
yazı-turaya döner ve `Cov(w, z) = 0` **yapı gereği** olur. Bu bir bulgu değil,
**ölçüm hatası** olurdu.

**Soru:** ajanlar arasındaki farkı **ne** yaratacak?

| Seçenek | Fark nereden gelir | Not |
|---|---|---|
| **① Sıralı erişim, sıra dönerek** ⭐ | Tükenen ortak kaynak için çekişmeden | **Claude Code'un önerisi.** Aksiyom testini geçen tek seçenek · **sıfır yeni sabit** · var olan fiziğin üstüne oturuyor. ⚠ **En zayıf yeri aşağıda** |
| ② Ajan başına ayrı niş | Doğduğu dünyadan | Fark yaşamaktan **önce** gelir; "ortak havuz" iddiası zayıflar. Yeni sabit ister (*nişler ne kadar farklı?*) |
| ③ Asimetrik doğum koşulları | Doğrudan bizim elimizden | Aksiyomun sınırında. Yeni sabit ister |
| ④ Örneklemeli çözümleme | Rastgele sayı üretecinden | ⛔ **D-037'yi ve I0.6'yı kırar** — `warn_only` altında aynı tohum farklı adapter + 21/50 farklı karar üretiyordu, **gürültü etkiden büyüktü** |
| ⑤ **Uzamsal gömme** (yeni, D-080) | Başlangıçtaki konumdan | Mekanizma gerçek (Schelling 1971, `10.1080/0022250X.1971.9989794`) ve §N.4'ün cevapsızını doldurdu. ⚠ Ama **②'nin yanına düşüyor**: Schelling'de farkı yaratan başlangıç yerleşimidir ⇒ **fark yaşamaktan önce gelir**. ⚠ DR *"kısıt ihlal etmiyor"* dedi, **eksik**: ızgara boyutu + komşuluk yarıçapı + kaynağın uzamsal dağılımı = **en az üç yeni sabit** |

⚠ **①'in ilan edilmiş zayıflığı — D-081 bunu yeniden yazdı.** Eski metin
*"havuz 80 → yenilenmeyle ~89"* diyordu; **yanlıştı**, yenilenme +2.40, stok
**82.40**, ve olay 1'den sonra havuz **18.40**'a düşüyor. Zayıflık *"ayrışma
geç başlar"* değil:

> **Bu evrende kademeli kıtlık yok, kıtlık *anı* var.** Kişi başı azami
> yenilenme `r·K/4 = 3.75`/olay, DEFECT'in talebi **8.0**/olay ve olayların
> %94–100'ü DEFECT ⇒ yenilenme **hiçbir başlangıç stoğunda** yetişemez.
> Havuz *"herkese yeter"* ile *"ölü"* arasında **tek adımda** geçer ⇒ bir
> yaşamda **tam olarak bir** kısmen karşılanan olay olur. Başlangıç stoğu bir
> çalışma noktası değil, **geri sayım sayacı**dır.

⚠ **①'e özgü değil:** ②/③ de havuza dokunmuyor. Havuzun çalışma kuralı
**hangi P0 seçilirse seçilsin** ilan edilmek zorunda.

⚠ **D-079 ①'in çerçevesini değiştirdi:** bu bir uygulama ayrıntısı değil,
**ilan edilmesi gereken bir fizik kararı** (Schönfisch & de Roos 1999;
Fatès 2014). Ve konum etkisi **ölçülmüş** bir olgu (Suleiman ve ark. 1996) —
rotasyon onu **yok etmiyor**, yalnız **kalıcı olmasını** engelliyor.

⚠ **D-080 ①'i sınadı ve zayıflatmadı.** DR #7'nin *"birinci hamle eden
davranıştan bağımsız avantajlıdır"* iddiası **kaynağında yoktu** (§O.2). Ve
rotasyonun gerekçesi §N'deki hâliyle kalıyor: *"konum etkisini yok etmek"*
değil — **kalıcı olmasını engellemek**. (DR'nin rotasyon dayanağı Bru 2003
idi; o alıntı **koşulların sunuluş sırasından** bahsediyor, ajan sırasından
değil ⇒ **alınmadı**.)

### ⛔ P0-b — **havuzun çalışma noktası**, karar Yasin'in (D-081)

P0 ①'i seçse bile ayrı bir sayı kararı kalıyor, ve **ikisi birlikte** ilan
edilmeli.

✅ **Karara bağlandı (Yasin, D-081):** havuz **N ile ölçeklenecek**, kişi başı
kapasite/başlangıç **bugünkü sayılarda** (100 / 80) ⇒ **sıfır yeni sabit**,
ve kişi başı yörünge N=1 evreninin **birebir aynısı** kalıyor.

⛔ **Claude Code kendi önerisini geri çekti:** *"landmark yapısal
tanımlansın (= kıtlık anı)"* demiştim, Yasin onaylamıştı, **uygulamaya
geçerken çöktü.** `LANDMARK_EVENT = 10` keyfi değil —
`constraints.py:64–77` onu `METABOLIC_GRACE_EVENTS`'e bağlıyor ki **ölüm
landmark'ta hâlâ askıda** olsun ve **her soy oraya ulaşsın**. Kıtlık anına
(17) taşımak 11–16'da ölen soyları **okumasız** bırakır ⇒ K1–K3'ün ve DR #5'in
konusu olan **bilgilendirici sansürleme** geri gelir. ⇒ **landmark 10'da
kalıyor.**

### ⭐ D-082 tabloyu değiştirdi — **kapasite artık tek seçenek değil**

DR #8 D-081'i **çürütmedi, adlandırdı**: `d = 8.0` bir **constant quota**'dır
ve *"sabit kotada herhangi bir bozulma yok oluşa götürür"* bilinen bir sonuç
(Azar, Lindgren & Holmberg 1996, `10.1007/BF00699291`).

⛔ **DR'nin verdiği iki çıkış da bizde mekanizmayı öldürüyor** (§P.4):
*constant effort* ve *escapement* kıtlığı ortadan kaldırıyor — hasat `h·P`
ise **kimse eksik almaz**, eksik alma yoksa **paylaştırma yoktur**,
paylaştırma yoksa **sıralı erişimin tahkim edeceği bir şey kalmaz**.

⭐ **Üçüncü yol çalışıyor: Holling II** (§P.5, keşifsel). **Talep sabit kalır
(8.0), gerçekleşen hasat stoka bağlanır:** `gerçekleşen = d·P/(h+P)`.

| olay | sabit kota (bugün) | **Holling II (h=2)** |
|---|---|---|
| 1–9 | fark **tam sıfır** | 0.017 → 0.049 |
| **10 (landmark)** | fark **tam sıfır** | **0.058** |
| 15 | fark **tam sıfır** | 0.250 |
| 17 | 1.763 vs 0, **yedi ajan hiç almıyor** | — |
| 18 | hepsi sıfır | 3.246 |

⇒ **Ortamın özelliğidir, karar kuralının değil** ⇒ K7'yi ve aksiyomu ihlal
etmiyor. Ve `metabolic_gain` **zaten aynı fonksiyon ailesini** kullanıyor
(D-066/J9) — evrene ikinci bir sabit ailesi açmıyor.

### ✅ D-083 iki uyarıyı da ölçtü — **biri doğrulandı, biri çürütüldü**

**Rotasyon farkı ~4.5 kat kısıyor ama öldürmüyor.** Landmark'ta (olay 1–10):
sabit sırada hasat yayılımı 0.325, rotasyonlu **0.071** — ama **her
yapılandırmada 8 ajanın 8'i de farklı**, ve rotasyon *tamamlandığında*
(16 olay) yayılım **büyüyor**. ⇒ §N.1'in çıkarımı **ölçüldü**.

⛔ **Kendi endişemi çürüttüm: prompt kanalı tam duyarlı.** *"Sayılar
`.2f`'ye yuvarlanıyor, fark görünmez"* demiştim; yuvarlama **yalnız sistem
prompt'unda**. Karar anında modele giden kullanıcı mesajı
[graph.py:1079](dau/foundation/graph.py:1079) → `view.model_dump_json()`,
**tam kayan nokta duyarlılığı**. Ölçüldü: **1e-9'luk fark bile** prompt
dizgisini değiştiriyor (`0.4523177` → `0.452317701`). Holling II'nin
landmark farkı **3.–4. ondalıkta** ⇒ rahatça görünür.

### ⛔ D-084 — o soru da ölçüldü: **karar kanalı doygun**

Gerçek model, greedy, on fark büyüklüğü (1e-9 … 1e-1), **43 saniye**.
Ham metin değişiyor (1e-9 bile), ama **hasat miktarı onda onunda `8.0`** —
benzersiz outcome sayısı **1**. Kontrol (fark=0) birebir aynı ⇒ sonda
deterministik.

⇒ **D-068'in çöküşü burada mekanizma olarak görünüyor:** davranış
eşlemesinin **tek soğurucu çıktısı** var ⇒ hiçbir girdi tedirginliği onu
oynatamaz ⇒ ajanlar **karar vererek ayrışamaz**.

⭐ **Ama ① karar kanalına ihtiyaç duymuyor.** Holling II'de iki ajan aynı
şeye karar verip **farklı miktar alıyor** (7.654 vs 7.596) — ayrım
**ortamın karnesinde**, tercihte değil. Oradan `metabolic_gain` → enerji →
iç durum → **drift**'e akıyor, ve birincil uç nokta zaten **landmark'taki
drift**.

⇒ ⭐ **①'in tarifi değişti:** *"özdeş karar veren ama **farklı yaşayan**
ajanlar"*. ⚠ **Bunun aksiyomu karşılayıp karşılamadığı tasarım kararıdır ve
Yasin'indir** — Claude Code tek başına vermez. **P0'ın gerçek sorusu artık
bu.**

⚠ **Kalan bedel:** Holling II **yeni bir sabit (`h`)** getiriyor ⇒ kapasite
sorusu **kaybolmuyor, yer değiştiriyor**.

⏳ **Açık kalan sayı — kapasite ya da `h`.** Bugünkü kapasite 100 ile
sabit-kota kıtlığı **olay 17**'de, yani landmark'tan (10) **sonra** ⇒ ölçüm
anında ajanlar **özdeş**, ① hiçbir şey ölçmez.

| kişi başı kapasite | kıtlık anı |
|---|---|
| 50 | 7 |
| 60 | 8 |
| **67** ⭐ | **9** — kıtlığı landmark'tan önce düşüren **en büyük** değer |
| 70 | 10 |
| 100 (bugünkü) | **17** ⛔ landmark'tan sonra |

⭐ Kapasite 67 (başlangıç 54) seçilirse: olay 1–8 herkes tam alır ve
**özdeştir** · olay 9 **tek ayrışma olayı** · olay 10'da havuz ölü ama
**enerjiler farklı**, landmark tam orayı okur · ölüm askıda olduğu için
**her soy landmark'a ulaşır**.
⚠ **Bu bir sabit seçimidir ve §2.7'nin sınırındadır.** Savunulabilir biçimi:
değer **etkiye bakılarak değil**, yalnız sabitlerden türetilen bir
eşitsizlikle seçilir (*"kıtlık anı < `LANDMARK_EVENT`, ve bunu sağlayan en
büyük kapasite"*) — hiçbir pilot verisi girmez, tıpkı `LANDMARK_EVENT`'in
`GRACE`'e bağlanması gibi. ⚠ **Karar Yasin'in** (D-007).

### 3. P0 verildikten sonra, sırayla

**Tasarım:** `docs/POPULATION_DESIGN_PROPOSAL.md` — **P0–P7**, kanıtları,
maliyet zarfı, kod iş sırası. ⚠ Kod yazılmadı (§2.3).

| # | İş | Bağlı |
|---|---|---|
| ~~E3~~ | ✅ **D-078** — olay satırları `agent_id` taşıyor, okuyucular filtreliyor | — |
| E1/E5 | Ortak havuzu akışların dışına al; `pool_step_node` N talebi toplasın | P0, P1 |
| E2 | N ajanı olay bazında ilerleten dış döngü | ⚠ **denetimsiz yapılmaz** |
| E4 | Üreme katmanı: turnuva, `w` sayacı, varis üretimi | P2, P3, P4 |
| — | Price aletlemesi: `Cov(w,z)` + `E(w·Δz)` nesil başına | P4 |

Sonra **pilot** → **ikinci ön-kayıt** → **koşum**.

### ⭐ Linçpin — unutulmaması gereken

D-076'nın getirdiği **Price eşitliği** `Cov(wᵢ, zᵢ)` istiyor ve bu ancak `w`
**değişkense** tanımlı. Bugün her ebeveynin **tam olarak bir** varisi var ⇒
`w` sabit ⇒ **seçilim ölçülemez.** ⇒ ②'nin asıl işi popülasyon eklemek değil,
**`w`'yi değişken yapmak**; gerisi altyapı.
⚠ `F_agent`'ı doğrudan `w` yapma — D-071'den beri içinde **gerçekleşmiş
hayatta kalma** var, Mills & Beatty'nin totolojisi geri gelir (D-075). Üç
katman ayrı: `F_agent` (girdi) → `w` (varis sayısı) → **`z` = landmark drift
(sonuç)**.

### ⚠ Ön-kayıta girmesi gereken geçerlilik kapısı

`F_agent` dağılımının yayılımı ve `w`'nin varyansı **ön-koşul**. Yayılım
yoksa turnuva yazı-turaya döner ve koşum **seçilim hakkında bilgisizdir**.
⚠ Bu **etkiye bakmak değil** (L9): kol farkına değil, dağılımın **var olup
olmadığına** bakılıyor ve kural koşumdan **önce** yazılıyor.

### ⚠ Bu iş sırasında geçerli sınırlar

- **Hiçbir sabit sonuca bakılarak ayarlanmaz** (§2.7).
- **Uç nokta etkiye bakılarak seçilmez** (L9).
- ⚠ **Davranış hâlâ çökük** (D-068): olayların %94–100'ünde DEFECT. K7
  bilişsel önseli aksiyom gerekçesiyle kapattı; D-074 bunu **açık risk** olarak
  kaydetti. **Vallinder & Hughes 2024** (D-075) en yakın yayımlanmış analogun
  sonucu **strateji metni aktararak** aldığını gösteriyor — yani bizim
  kapattığımız kanaldan. K7'nin bedelinin **üçüncü** bağımsız teyidi.
- ⚠ **Kullanılmış tohumlar:** 2001–2043 · 3001–3004 · 4001–4002 diskte adapter
  bıraktı ⇒ I0.7 abort eder. **7777 · 7801 · 9101** adapter yazmadı ama
  deneyde kullanılmamalı.

---

## ▶ TARİHÇE — Faz A/B/C ve bekleme işleri (kapandı)

⚠ Aşağısı **tarihçedir**; güncel iş yukarıda. Hangi kararın hangi adımdan
çıktığını aramak için duruyor.

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

## ▶ İKİNCİ ÖN-KAYIT — önümüzdeki tablo

⚠ İki liste ayrı: **birincisi olmadan koşum başlayamaz**, ikincisi koşuma
girip girmeyeceği tartışılacak adaylar.

### A. Yedi kilit kararı — ✅ **VERİLDİ (D-070) ve UYGULANDI (D-071…D-073)**

| # | Karar | Seçilen |
|---|---|---|
| **K1** | PE uç noktalarının penceresi | **Landmark + olay-başına oran.** LOCF bırakılıyor (D-069/V1) |
| **K2** | Enerji okuma anı | **Landmark değeri + zaman-integre ortalama**; `E_final` bırakılıyor |
| **K3** | N ve güç | **Olay sayısı üzerinden** (Schoenfeld 1983); sansür yok ⇒ olay = soy |
| **K4** | Üç metabolik sabit | **Olduğu gibi kilitlenir**, `CALIBRATED = False` **kalır** |
| **K4-b** | `F_agent` havuz terimi | **Olay başına normalize** — ⚠ D-068'in *"Δhavuz canlandı"*sının %90'ı ömürmüş (%110 → %10.7) |
| **K5** | Birincil uç nokta | **Landmark drift.** ⚠ Aktarılan şey değil, karşılaştırılabilir kesiti — iddia daralır, sınır ilan edilecek |
| **K5-b** | `social` ön-koşulu | **Hayır** — D-064'ün kanal dağılımı eski fiziğe ait |
| **K6** | S5'in "ilk travma"sı | **Commons krizi** |
| **K7** | Davranış müdahalesi | **Hayır** — aksiyom. Çöküş **bulgu olarak** raporlanır |

⇒ **Üç kod değişikliğinin üçü de uygulandı:**

| # | İş | Kayıt | Commit |
|---|---|---|---|
| 1 | **K4-b** — havuz terimi olay başına normalize | **D-071** | `74834e6` |
| 2 | **Landmark aletlemesi** — 10. olaydaki drift + enerji + zaman-integre enerji | **D-072** | `345c9f3` |
| 3 | **LOCF kaldırıldı** — uç nokta pad edilmiş dizinin ortalaması olmaktan çıktı | **D-073** | `709b2ac` |

⚠ **İkisi yol üzerinde ek karar çıkardı ve Yasin'e soruldu (§2.3):**
D-071'de `F_agent`'ın **hayatta kalma terimi hiçbir zaman ömrü ölçmüyormuş**
(`t_survived/t_survived` ≡ 1.0) ⇒ payda faz bütçesine çevrildi.
D-073'te LOCF'a dokunan **iki kapı** ayrıldı: `I3.1`'in paydası yaşanan olaya
çevrildi, `I3.4` bayrak basmayı bıraktı (yeni `MODE_REPORT`).

Sonra: ikinci ön-kayıt taslağı, ve **ondan sonra** koşum.

### B. Adaylar — koşuma girip girmeyeceği ayrıca tartışılır

| Aday | Nereden geldi |
|---|---|
| **A2 — kanal ayrımı, plasebo anı enjeksiyonu ile** | ⚠ Eski tasarım ("getirimi tamamen kapat") **kusurluydu**: OOD şoku ölçer (D-049/I12) |
| **Çifte ayrışma protokolü** (`ΔE_ağırlık + ΔE_bellek ≈ ΔE_toplam`) | DR #3 / I15 — kanal ayrımı iddiasının literatürdeki çıtası |
| **`DPO_MAX_SEQUENCE_TOKENS`** | **D-062**: dizilerin **%85.5'i** 512'de kesiliyor ve sohbet şablonu başlığı gidiyor ⇒ D-027'nin gerekçesi o dizilerde geçersiz |
| **Uzunluk kontrolü (çift kurma)** | **D-062**: `chosen` 57.2 vs `rejected` 38.7 token; DPO **toplam** logp kullandığı için uzunluk doğrudan marja giriyor |
| **KTO'ya geçiş** | DR #2 baş tavsiyesi. `uniq_rejected` 100/94 ölçüldü (GAP-18) |
| **Zaman × kol etkileşimi (LMM/FDA)** — **genel form** | DR #3 / I17. ⚠ "ikinci yarı AUC" özel formu **alınmaz** |
| **DTW / Fréchet yörünge ölçütü** | DR #4 / J18–J19. ⚠ **Etkiye bakmadan** kilitlenmeli |
| **MAP-Elites / davranışsal tanımlayıcı ızgarası** | DR #4 / J16 — ⚠ popülasyonu (aşağıdaki madde) önkoşul kılıyor |
| **Popülasyon / N nesil** | **D-014**: hedef N nesil. DR #4 / J20 sıralamayı doğruladı: **önce bedel, sonra popülasyon** |
| **`W_SEM` 0.0 → 0.3–0.4** · negation sarmalayıcı · asimetrik spillover | GAP-10, üçü de L8'de sınır |
| **Precision-PE `VAR_REF`** | L13 — π tavanda takılı, mekanizma atıl (pilotta `pi_n_distinct=2`, hâlâ atıl) |
| **`SYSTEM_PROMPT` lexicon** | L14 — davranışsal sınıflandırıcıyı besliyor. ⚠ K7 ile aynı yeri tutuyor |
| **Magic number kalıntıları** | `time.sleep(10)`, bare `0.5`, `k: int = 5`. **Cursor'a uygun** |

⚠ **Kapananlar bu listeden çıktı:** `F_agent` + GAP-19 birlikte (D-066+D-067),
A4 (D-066).

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

## ▶ DR KANALI — ✅ **#8 cevaplandı (D-082)** · ✅ **#7 cevaplandı (D-080)** · ✅ **#6 cevaplandı (D-076)** · ⏳ **#5 hâlâ gönderilmedi**

| # | Brief | Durum |
|---|---|---|
| **8** | **Ortak havuzda *kademeli* kıtlık rejimi kurulabilir mi, ve ölçüm anı sonuca ayar yapmadan nasıl seçilir** — `docs/research/2026-08-14_scarcity-band-and-operating-point.md` · gönderilen: `_SHORT-A` + `_SHORT-B` | ✅ **cevaplandı ve mutabakata bağlandı (D-082, §P).** Ham: `2026-08-14_DR8-answer-raw.md`. ⭐ **D-081 çürütülmedi, adlandırıldı** (Azar ve ark. 1996: bizim `d=8.0`'ımız *constant quota*, ve çöküş o rejimin bilinen özelliği). ⛔ **DR'nin iki çıkışı da mekanizmayı öldürüyor** — kıtlığı kaldırıyorlar, karne kalmıyor. ⭐ **Üçüncü yol Holling II** ve DR onu atladı; kendim hesapladım. ⚠ **Üç kimlik hatası daha** (10., 11., 12.) — desen net: **makaleyi buluyor, künyeyi uyduruyor**. ⭐ **İlk kez bir boşluk ilan edildi** (*"no specific claim found in sources"*) ve **kaynakça eklendi** ⇒ D-080'in iki düzeltmesinden ikincisi tuttu. ⚠ **Rice 2008: Price kestirimi küçük N'de yanlı** — ikinci ön-kayıta sınır. ⚠ İlk gönderim denemesi cevapsız dönmüştü — araç konuyu hiç görmedi (*"Unspecified Topic"* başlıklı jenerik bir araştırma planı üretti; beş sorumuzdan tek kelime yok ⇒ **mutabakat yapılacak bir şey yok**). Teşhis: brief gövde metni olarak ulaşmamış. ⇒ **saf ASCII düz metin sürümü üretildi** (#6/#7'nin `_PLAIN` alışkanlığı, markdown yazmak hataydı). Hedef **OpenAI Deep Research** (matematik gücü için). ⚠ **İngilizce yazıldı**, bilerek. D-081'in açtığı iş. Beş soru: **Q1** §2'deki türetmemiz doğru mu + *kritik yavaşlama* uzun bir geçiş bandı verir mi · **Q2** davranışa dokunmadan kademeli kıtlık üreten mekanizmalar (stoka bağlı hasat / Holling / escapement) — ⚠ hangisi **ortamın** özelliği, hangisi **karar kuralının** · **Q3** sabit yaşta ölçüm ile mekanizmanın geç açılması çatışınca · **Q4** bir sabiti *"mekanizma çalışsın diye"* seçmenin kabul görmüş adı var mı · **Q5** Price kovaryansı kaç seçilim epizodunda tanımlı olur. ⭐ **D-080'in iki süreç düzeltmesi girdi:** kaynakça iste · satır numarası **değil birebir alıntı** iste. ⚠ Tekrarlanabilirlik kısıtı bu kez **açıkça** *"tek tohum demek değil, 40 tohumla koştuk"* diye yazıldı (D-080'in yanlış okumasına karşı). ⚠ **Etki sorulmuyor** (L9) |
| **7** | **Davranışsal olarak özdeş ajanlar arasında heterojenlik nereden gelir** — `docs/research/2026-08-14_heterogeneity-among-identical-agents_PLAIN.txt` (baştan düz metin) | ✅ **cevaplandı ve mutabakata bağlandı (D-080, §O).** Ham: `2026-08-14_DR7-answer-raw.md`. ⭐ **Süreç eklemesi işe yaradı:** *"iddia kaynağın neresinde"* şartı sayesinde yerini gösterebildiğim iddia **6/4** oldu (#6'da 13/13 *"Tam Uyumlu"*, sıfır ayırt etme) ve **altı iddianın üçü kendi alıntısını taşımıyor** çıktı — ⚠ **yalnız DOI ile üçü de geçerdi**. ❌ **İki kimlik hatası daha** (8. ve 9.), ikisi de tamir edildi: `arXiv:2308.00179` = **Anwar & Georgalos** (*"Nishimura"* uydurma) · `arXiv:0810.3070` **bambaşka makale** ⇒ doğrusu **Rafferty ve ark. 2014** `10.1111/cogs.12112`. ⭐ **①'i zayıflatacak tek iddia (*birinci hamle avantajı*) kaynağında yoktu** · **⑤ uzamsal gömme** tabloya eklendi (ama ②'nin yanına) · **iki bağımsız yol** Suleiman 1996 ve Bru 2003'te §N ile kesişti. ⚠ **§N.3'ün hipotezi düştü** — cevap geldi. **Brief #8:** kaynakça iste, satır numarası değil **birebir alıntı** iste |
| **6** | **Tek soy yerine popülasyon: seçilim şeması ve ortak havuz** — `docs/research/2026-08-13_population-selection-and-shared-commons.md` (⚠ **Gemini'ye giden sürüm `..._PLAIN.txt`**) | ✅ **cevaplandı ve mutabakata bağlandı (D-076, §M).** Ham: `2026-08-14_DR6-answer-raw.md`. ⚠ **Yeni kusur türü: doğru kimlik, yanlış iddia** — üç iddia gerçek kaynaklara yüklenmiş ama o kaynaklarda yok; DOI doğrulaması bunu yakalamıyor. Bir DOI kırık (Bedau 1998, 404). 13/13 satır *"Tam Uyumlu"* ⇒ ayırt etme yok. ⚠ **İçsel çelişki:** §5 birikimli iz için G=5–10 diyor, §6 sentezi G=3 öneriyor. ⭐ **Değerli:** Price eşitliği D-075'in totoloji borcunu ödüyor · ayrı havuz iki bağımsız kaynakta aynı yerde. Önce: **D-075 yerel taraması** (§L, dokuz kimlik) D-074'ün açtığı iş. Altı soru: S1 küçük N'de üreme/seçilim şeması · S2 sürüklenme mi seçilim mi · **S3 ortak havuzda kol kirlenmesi** (en kritik: müdahale bireye, ortam paylaşılıyor) · S4 uygunluk hem seçilim girdisi hem sonuçken · S5 kaç nesil = birikimli kalıtım · S6 sabit bütçede birey mi nesil mi. ⚠ **Etki sorulmuyor** (L9). Kısıtlar §1.1'de listelendi ki DR yasak bir şey önermesin; ihlal ederse **işaretlemesi** isteniyor |
| **5** | **Yaşam uzunluğu değişkenken uç nokta nasıl tanımlanır** — `docs/research/2026-08-13_variable-lifespan-endpoints-and-censoring.md` | ⏳ **gönderilemedi — DR'de teknik sorun.** ⇒ **D-069: yerel tarama yapıldı** (§K, sekiz kimlik Crossref'ten doğrulandı), K1–K3 karara hazır hale geldi. ⚠ Tarama **sistematik derleme değil**; brief geçerliliğini koruyor, DR düzelince aynen sorulabilir. Altı soru: S1 bilgilendirici sansürleme · S2 landmark vs yaşam boyu özet · S3 ölümün belirlediği durum değişkeni · S4 hayatta kalma hem girdi hem sonuçken · S5 farklı uzunluklu dizilerde eşleştirilmiş karşılaştırma · S6 küçük N'de zaman-olay gücü. ⚠ **Etki sorulmuyor, bilerek** (D-064/L9 disiplini) |
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
| Formül · tarihçe · empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` **v2.4.4** — ⚠ **§26 yeni: evrenin fiziği değişti** (D-054…D-068). `.html`/`.pdf` v2.4.3'te kaldı |
| Ön-kayıt: slotlar, uç noktalar, **on yedi ilan edilmiş sınır**, donmuş alet kimliği | `docs/PREREGISTRATION.md` 🔒 **KİLİTLİ** |
| **Sonuç, sınıflandırma, ne iddia edilebilir** | **`docs/B2_RESULTS.md`** |
| Gönderilemeyen DR brief'i (#5) | `docs/research/2026-08-13_variable-lifespan-endpoints-and-censoring.md` · yerine yapılan yerel tarama: `RECONCILIATION.md` **§K** |
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
