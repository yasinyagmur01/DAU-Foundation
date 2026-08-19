# ▶ YÜRÜTME KUYRUĞU — *"devam et"* denince buradan başlanır

**2026-08-19 · D-134 · tek otorite sıra.** Fazlar (`ROADMAP.md`) ve eski
borçlar **tek listede**, yapılma sırasına göre.

## Sözleşme

1. **"devam et"** = kuyruktaki **ilk ⬜ maddeyi** al, yap, ✅ işaretle,
   D-kaydı yaz, commit + push et.
2. Madde **⛔ KARAR** ile işaretliyse **Yasin'e sor**, kendin karar verme (D-007).
3. Her maddede *bitti sayılma ölçütü* yazılı — ona bakmadan ✅ işaretleme.
4. ⚠ **K1–K5** (`CLAUDE.md §2.4-b`) her maddede geçerli. GPU koşumu öncesi
   **K1 yazılmadan** koşum başlamaz.
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

# FAZ 2 — üçüncü ön-kayıt (GPU'suz)

## ⬜ 2.0 · ⛔ KARAR — **travma eşiği**, uç noktanın asıl darboğazı
**D-137 §8 bunu ayrı madde yaptı.** `Var(z) = 0` çıkan 14/18 geçişin sebebi
uç noktanın **boyutu değil**, travma kapısıydı: bireysel kanalın tepe
değerleri **0.42–0.62**, kapı **`DELTA_THRESHOLD_DEEP = 0.70`** (D-124).
⚠ Spillover'ın üç seçeneğinin **hiçbiri** bunu geçirmiyordu (D-137 §4) ⇒
bu bağımsız bir sorundur, GAP-10'un yan ürünü değil.
**Seçenek uzayı:** eşiği indir · `magnitude` formülünü değiştir · eşik-öncesi
bir uç nokta tanımla (D-124'ün penceresi bunun için aletlendi).
⛔ **Karar Yasin'in** — sabit değişikliği (D-007), ve §2.7 bağlayıcı: değer
**etkiye bakılarak seçilemez**, sabitlerden türetilen bir eşitsizlikle gelir.

## ⬜ 2.1 · ⛔⛔ KARAR — **soru yeniden çerçevelendi (D-139)**
⚠ **Eski hâli:** *"en küçük anlamlı etki, DR #1'den beri açık."*
⛔ **Denetim bunu düşürdü:** DR #1 cevapladı ve **benimsedik** —
`RECONCILIATION.md` §G.3: *"SESOI ilan edilmiyor. Yerine bütçe-kısıtlı N +
duyarlılık analizi"* (Lakens 2022, `10.1525/collabra.33267`). D-052 bunu
uyguladı (N=40 bütçeden, MDE `d_z = 0.465` ilan edildi).

⭐ **Gerçek boşluk başka yerde:** usul sağlam ama **istatistik değişti** —
`Cov(w, z)` için MDE'nin nasıl hesaplanacağını bilmiyoruz. Üstüne üç iç içe
sayım (tohum · 8 ajan · 2 geçiş), Rice 2008'in küçük-N yanlılığı, ve eşikli
uç noktanın **tanımsız** hücreleri var.

⛔ **Yasin'in seçimi (D-139 §3):** **A** 2.1'i düşür · **B** ⭐ kovaryans için
duyarlılık analizi olarak yeniden yaz (**DR #12 gönderilmeyi bekliyor**) ·
**C** permütasyonla ampirik MDE üret.
**Claude Code önerisi: B, ve C'yi B'nin cevabına göre karara bağla.**

📄 **DR #12 hazır:** `docs/research/2026-08-19_price-sensitivity-and-seed-budget_PLAIN.txt`
(saf ASCII · İngilizce · tablosuz · etki sorulmuyor · DR #1'in iki kusuruna
önlem yazılı).

## ⬜ 2.2 · Ön-kayıt taslağı
Kilitlenecekler: sosyal kuplaj fiziği · uç nokta (0.2'den) · birincil
karşıtlık (D-131: `lived ↔ shuffle`) · geçerlilik kriterleri · güç hesabı ·
tohum sayısı · durma kuralı.
**İlan edilecek sınırlar:** G=3 (DR #11'in "8 nesil" normatifi reddedildi,
§T.2) · **adapter sönümü / LoP** (D-132) · Price küçük N'de yanlı (Rice 2008) ·
kriz **müdahale-sonrası** (D-119/120) · n=1 deney, tek model ·
**I0.1/I0.2 popülasyon yolunda bağlı değil** (D-105) · ⭐ **`z` etkin olarak
tek boyutlu** — `k` 192/192 `resource_load`'a kilitli, alan kimliği hakkında
iddia yok, kovaryans drift'in **büyüklüğü** üzerine (D-137 §6).

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
