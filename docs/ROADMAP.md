# Yol Haritası — Yön 3'e (ajan-ajan etkileşimi) hızlandırılmış geçiş

**2026-08-19 · D-133 · Yasin: *"Yön 3 cazip, ona geçme adımlarını hızlandıralım"***

---

## ⭐ Stratejik çıkış noktası

> **Yön 3'e gideceksek, bugünkü fizikle 30–80 saatlik doğrulayıcı koşum
> yapmak boşa gider.** Sosyal kuplaj eklendiğinde evren değişir ve o sayılar
> ne karşılaştırılabilir ne yeniden kullanılabilir.

⇒ GPU **yalnız geçişten sağ çıkacak** şeylere harcanır.

| taşınır mı | ne |
|---|---|
| ✅ | Uç noktanın boyut düzeltmesi (Yön 1) — yeni evrende de aynı problem |
| ✅ | Alet: kapılar · checkpoint · estimability · pozitif kontrol · K1–K5 |
| ✅ | Provenans denetimi yöntemi ve maliyet modeli |
| ✅ | **C2 sonucu** — kapanmış, raporlanmış bir bölüm (evren null'ı) |
| ❌ | Bugünkü fizikle atılacak **yeni** doğrulayıcı koşum |

---

## ⭐⭐ Yön 3 sanıldığı kadar pahalı değil — mekanizma **kodda var**

| parça | durum |
|---|---|
| `compute_social_load(social, agent_id, opponent_id)` | ✅ **genel** — NPC'ye özel değil |
| `record_interaction` · `compute_coordination_friction` · `compute_markov_expectation` | ✅ hepsi rastgele id alıyor |
| **N ajan arasında hepsi-hepsiyle sosyal güncelleme** | ✅ `run_convention_pilot.py:243` — **çalışan referans uygulama** |
| Popülasyon koşucusunun bağlantısı | ⛔ `opponent_id = OPPONENT_ID` (**tek NPC**) — değişecek tek yer |

⭐ **Eşleştirme için yeni sabit gerekmeyebilir:** havuz erişimi zaten
**rotasyonlu** (D-104). Aynı rotasyon eşleştirmeyi de tanımlarsa **sıfır yeni
sabit** ile sosyal kuplaj kurulur. ⚠ Doğrulanacak, varsayılmayacak.

---

## Fazlar

### Faz 0 — GPU'suz, %100 taşınır (~2–3 sa)

| # | iş | çıktı |
|---|---|---|
| 0.1 | **Uç nokta boyutu:** dört eksenin büyüklüklerini de kaydet (argmax kazananı **yanında**, yerine değil). Saf raporlama | `delta_profile` yeni alan |
| 0.2 | **Sosyal kablolama tasarımı:** eşleştirme rotasyondan türetilebiliyor mu — **grep + hesap**, koşum yok | evet/hayır + kaç yeni sabit |
| 0.3 | **K1 mekanizma kontrolü** yazılı: niceliği ne üretiyor · hangi bayrak kapatır · dejenere olmadığının kanıtı | D-kaydı |
| 0.4 | Testler: **K2** (çok-tohumlu/çok-ajanlı) · **K3** (çağrı yeri) · **K5** (md5'li mutasyon) | yeşil suite |

### Faz 1 — tek ucuz doğrulama koşumu (~1–2 sa GPU)

**Tek soru:** *sosyal kuplaj `null` kolunu değişken yapıyor mu?*

| | |
|---|---|
| yapılandırma | 1 tohum · N=8 · G=3 · `--lora` · **`lived` + `null`** (D-128'in dersi: zayıf kol dahil) |
| önce | **mock prova** — birebir aynı bayraklarla, yapı doğrulaması |
| okunacak | ⛔ **yalnız tanımlılık:** `Var(F_agent)`, `Var(z)`, hasat yayılımı — kol farkı **hesaplanmaz** |
| karar kuralı | **koşumdan önce** yazılır (D-125 deseni) |

⇒ **Bu koşum yol ayrımı:** `null` değişkenleşiyorsa Yön 3 kuruldu;
değişkenleşmiyorsa D-131 (null betimleyici) kalıcı olur ve Yön 2'ye dönülür.

### Faz 2 — üçüncü ön-kayıt (GPU'suz)

Kilitlenecekler: sosyal kuplaj fiziği · uç nokta (Faz 0.1'den) · birincil
karşıtlık · geçerlilik kriterleri · **gerçek güç hesabı** (*en küçük anlamlı
etki* nihayet isimlendirilir — DR #1'den beri açık) · tohum sayısı.

⚠ İlan edilecek sınırlar: **G=3** (DR #11'in "8 nesil" normatifi reddedildi,
T.2) · **adapter sönümü / LoP** (D-132) · **n=1 deney, tek model**.

### Faz 3 — tek pahalı koşum

Nihai fizikle, Faz 2'nin verdiği tohum sayısıyla. Checkpoint sayesinde
gözetimsiz koşar. ⚠ Maliyet **tohum başına ~2 sa** (ölçüldü, yayılım 2.3 kat).

---

## ⛔ Bilerek YAPILMAYACAKLAR

1. **Bugünkü fizikle doğrulayıcı koşum** — Yön 3'e gidiliyorsa taşınmaz.
2. **G'yi 8'e çıkarmak** — DR'nin normatifi dayanaksız (T.2), ve adapter
   sönümü uzun soyda sinyali **seyreltebilir** (D-130 §12). Ölçülmeden hayır.
3. **Davranışa dokunmak** — C1/K7.
4. **Kapasite / kriz eşiği ayarı** — D-131'de aritmetikle elendi.

---

## Karar noktaları (Yasin'in)

| ne zaman | karar |
|---|---|
| Faz 0 sonu | Eşleştirme rotasyondan mı türetilsin, yoksa ayrı sabit mi |
| Faz 1 öncesi | Karar kuralı: `null`'ın *"değişkenleşti"* sayılması için eşik |
| Faz 1 sonu | Yön 3 mi, Yön 2'ye dönüş mü |
| Faz 2 | **En küçük anlamlı etki** — bu, DR #1'den beri açık olan ve hâlâ verilmemiş tek karar |
