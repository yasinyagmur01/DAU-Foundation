# B2 — Doğrulayıcı Koşum Sonuç Raporu

**Tarih:** 2026-08-12 · **Ön-kayıt:** `docs/PREREGISTRATION.md`, kilit commit
`befd72b4ee57` · **Analiz:** `dau_runs/b3_prereg_analysis.json`

---

## 0. ⚠ SAPMA İLANI — okumadan önce

Bu koşum ön-kayıt **§5'in geçerlilik kapısından geçmedi.** Sapma D-053'te
kayıtlıdır ve raporun başına, sonucun önüne konmuştur.

| §5 kriteri | batch 1 (2004–2023) | batch 2 (2024–2043) |
|---|---|---|
| `run_quality = clean` | ❌ `flagged` | ❌ `flagged` |
| §5'in adıyla saydığı **18 kapı** geçer | ✅ 18/18 | ✅ 18/18 |
| I0.7 yeşil başlar | ✅ | ✅ |
| `prompt_skipped_no_record = 0` | ❌ **2** / 2050 | ✅ 0 |
| `[LORA][WARN]` = 0 | ❌ **2** | ✅ 0 |
| `adapter_present` doğru | ✅ 120/120 | ✅ 120/120 |
| `TORCH_DETERMINISTIC_WARN_ONLY=False` | ✅ | ✅ |

Ek olarak: §5 *"koşum öncesi `dau_runs/adapters/` boş"* diyor; dizin hiçbir
zaman boş değildi (batch 1 başlarken 2001–2003'ün 7 adapter'ı, batch 2
başlarken batch 1'inkiler). I0.7 çakışmaya bakıyor ve geçti, ama metnin
harfi "boş" diyor.

**Sapmanın kabul edilme gerekçesi (D-053):** ihlallerin hiçbiri birincil
karşıtlığa **yönlü** bir terim eklemiyor — kırpma iki eğitim kolunda birebir
(10.8/10.8 adım, `grad_norm_min` 2.959 vs 2.984), atlanan iki karar birer
birer `lived` ve `shuffle` kollarında (log satır 6084 ve 6578), `null` kolu
uyarı vermedi. Ayrıca `prompt_skipped_no_record = 0` kriteri D-037
determinizmi altında **yeniden koşumla sağlanamaz**: aynı seed aynı SYSTEM_1
kararını üretir.

⚠ Bu sapmanın sonucun **sınıflandırmasına** doğrudan etkisi vardır — §3'e bak.

---

## 1. Koşum kimliği

| | |
|---|---|
| Seed | **2004–2043**, atlamasız, N = **40** |
| Koşum | iki batch, `--lora`, `events_gen1=50` · `events_gen2=20` · `k_gen2=3` |
| Süre | ~6.4 sa + ~6.7 sa |
| Model | `meta-llama/Meta-Llama-3.1-8B-Instruct`, NF4 + double_quant, fp16 |
| DPO | β=0.1 · lr=1e-6 · epochs=1 · batch=1 · accum=4 · max_seq=512 |
| Sampling | greedy (`do_sample=False`), temperature 0.2 |
| Değişmez | 24 kapı kodda, **23 geçti**, bayrak: `I1.3b` (iki batch'te de) |

`tool_identity` ön-kayıt §12 ile **birebir eşleşti** — backend, model,
quantization, DPO ayarları, LoRA, sampling ve sekiz kütüphane sürümü dahil.
Yani bu koşum, o ön-kaydın koşumudur.

---

## 2. Birincil sonuç (§3) — **H0 reddedilemedi**

Her seed *s* için `null` kolu çapa alınarak:

```
a_s = ‖m_lived(s)   − m_null(s)‖₂
b_s = ‖m_shuffle(s) − m_null(s)‖₂
```

| | |
|---|---|
| `a_s` ortalama | **0.3812** |
| `b_s` ortalama | **0.3814** |
| `a_s − b_s` ortalama | **−0.0002** · medyan **0.0000** |
| İşaret dağılımı | pozitif **15** · negatif **14** · berabere **11** |
| Eşleştirilmiş Wilcoxon, çift yönlü | **W = 217.0** · **p = 0.9914** |
| Gözlenen etki | **`d_z` = −0.000** |

**α = 0.05'te H0 reddedilemedi.**

### Bu bir "sınırda kaçırma" değil

Uç noktanın çözünürlüğü ayrıca ölçüldü:

| Mesafe | Ortalama |
|---|---|
| `‖lived − null‖` | 0.3812 |
| `‖shuffle − null‖` | 0.3814 |
| **`‖lived − shuffle‖`** | **0.3852** |

Üç kol birbirine **eşit uzaklıkta**. Yaşamın tercihleriyle eğitmek ile o
tercihlerin **%100 tersiyle** eğitmek, varisin doğum-drift'ini aynı ölçüde
ve ayırt edilemez biçimde oynatıyor. 40 seed'in **11'inde** `lived` ve
`shuffle` birebir aynı vektörü üretti.

Uç nokta dejenere değil: 120 kolda **76 farklı** büyüklük değeri var.

⚠ **Ama "etki yok" denmez** (§9-S4 / D-047, koşum görülmeden bağlandı).
N=40'ın tespit edilebilir en küçük etkisi `d_z = 0.465` (Wilcoxon, çift
yönlü, güç 0.80). Doğru ifade: **bu uç noktada `d_z ≥ 0.465` büyüklüğünde
bir etki yok; altındaki etkiler için veri bilgisiz.**

---

## 3. §11 sınıflandırması — **ALET NULL'I**

§11 null'ı iki sınıfa ayırmayı şart koşuyor ve tanımları koşum görülmeden
yazılmıştı:

> **Mekanizma null'ı** — kollar ayrışmadı, alet çalışıyordu (§5'in hepsi
> yeşil, kanal 2 faz-2 kararlarını değiştirdi).
> **Alet null'ı** — **§5'ten biri düştü**, veya kanal 2 kararları değiştirmedi.

**§5'ten üç kriter düştü** (§0). Dolayısıyla ön-kaydın kendi tanımına göre
bu sonuç **alet null'ıdır** — bu bir yorum değil, önceden yazılmış bir
kuralın uygulanmasıdır.

### Kanal 2 tarafı ise mekanizma null'ını işaret ediyordu

| Ölçüm | Değer |
|---|---|
| Adapter'ın değiştirdiği faz-2 kararı, `lived` | ort. **26.1 / 50** |
| aynısı, `shuffle` | ort. **26.6 / 50** |
| Hiç değişiklik olmayan seed | **0 / 40** |

Yani kanal 2 atıl değildi. §11'in tanımı "veya" ile bağlı olduğundan §5'in
düşmesi tek başına sınıflandırmayı belirliyor.

### Sınıflandırmayı bağımsız olarak destekleyen üç ölçüm

Bunlar §11'in tanımının parçası değil, ama aynı yöne işaret ediyor:

| Ölçüm | Değer | Ne diyor |
|---|---|---|
| `dpo_loss` (lived / shuffle) | **0.6919 / 0.6940** | **ln 2 = 0.6931**. Eğitimden sonra tercih marjı ≈ 0 |
| Kırpılan adım oranı | **%100** (iki kolda da) | Adım boyunu `lr` değil `DPO_MAX_GRAD_NORM=1.0` belirliyor |
| `dpo_grad_norm_min` | **≈ 2.96** | Koşumun **en küçük** gradyanı bile tavanın ~3 katı |

⇒ D-029'un literatürden kilitlediği `lr = 1e-6` bu koşumu **tarif etmiyor**;
kırpma tarif ediyor. `I1.3b` (D-046) tam bunun için eklenmişti ve **kapı
işini yaptı.**

⚠ Buna karşılık `dpo_delta_logp_chosen` = **+0.064**, 20 seed'in **18'inde
pozitif** ⇒ D-049'un korktuğu **bastırma deseni gerçekleşmedi**. Öğrenmenin
**yönü doğru, büyüklüğü yok.** (`shuffle`'da da +0.025, 15/20 ⇒ bu bulgu
eğitim yordamının sağlığı hakkında, `lived`'e özgü değil.)

---

## 4. §11'in şart koştuğu ayrıştırma (S1 / L11)

L11 gereği S1 birincilden bağımsız bir kanal değil — `flags[domain]` ile
`magnitudes[domain]` aynı anda yazıldığından S1, birincilin girdi vektörünün
**desteğidir**. §11 birincilin ne kadarının bayrak kümesi farkından, ne
kadarının büyüklük farkından geldiğinin ayrıştırılmasını istiyor:

| Alt küme | n | `a_s − b_s` ortalama | tam sıfır |
|---|---|---|---|
| Üç kolun **bayrak kümesi aynı** | 11 | **−0.0420** | 6 |
| **En az biri farklı** | 29 | **+0.0156** | 5 |
| Toplam | 40 | −0.0002 | 11 |

İki alt küme **ters işaretli** ve toplamda birbirini götürüyor. Bayrak
kümesi özdeş olduğunda bile (yani ayrım yalnız büyüklükten gelebilecekken)
fark sıfır değil ama yönü `shuffle` lehine; bayrak kümesi farklıyken yön
`lived` lehine. **Hiçbiri anlamlı değil ve hiçbiri iddia edilmiyor** —
ayrıştırma §11'in şart koştuğu için raporlanıyor.

---

## 5. İkincil uç noktalar (§4)

⚠ **Hiçbiri iddia edilmiyor. Çoklu karşılaştırma düzeltmesi yapılmadı**
(§4/§9-S3, koşumdan önce bağlandı). Birincil null çıktığı için, bir ikincil
anlamlı olsa bile **sonuç null olarak raporlanır** — bu da §4'te yazılıdır.

| # | Uç nokta | Test | Sonuç | Not |
|---|---|---|---|---|
| **S1** | Doğum-drift kategorik | Fisher-Freeman-Halton | **p = 0.877** | MC permütasyon, 200k, seed=0 |
| **S2** | `n_transfer_candidates` | Kruskal-Wallis | **p = 0.726** | lived 1.52 / null 1.38 / shuffle 1.25 |
| **S2** | `n_inherited_warnings` | Kruskal-Wallis | **p = 0.726** | ⚠ iki alan **birebir aynı** değerleri taşıyor |
| **S3** | Gen1 ΔPE (fazın tamamı) | eşleştirilmiş Wilcoxon | **p = 0.070** | ort. **+0.0104**, 24/16 pozitif — yön H1'le uyumlu |
| **S4** | Gen2 ortalama PE | eşleştirilmiş Wilcoxon | **p = 0.035** | ort. **−0.0128**, 11/19 — **ters yönde**, medyan 0.0000 |
| **S5** | Gen2 davranışsal | McNemar | **KOŞULMADI** | veri kayıtlı çıktıda yok |
| **S6** | `f_agent=None` kolu | birincil ile aynı | **KOŞULMADI** | koşumda bu kol yok |

**S3 ve S4'ün null'ı §11 gereği "ölçüm duyarsızlığı" olarak okunur**, mekanizma
yokluğu olarak değil: L9 gen1 uç noktasının ayrımın %80–86'sını, L10 gen2
uç noktasının %73'ünü attığını **ölçtü** (varsaymadı).

**S4'ün p = 0.035'i sonucu değiştirmiyor.** Üç sebep, üçü de önceden yazılı:
(1) §4 birincil null iken ikincilin sonucu değiştirmeyeceğini söylüyor,
(2) işaret H1'in beklediğinin **tersi**, (3) altı ikincilde düzeltmesiz bir
tanesinin 0.05 altına düşmesi şans beklentisiyle uyumlu.

**S5 ve S6 için yerine başka ölçü konmadı.** S5'in gerektirdiği
`decision_to_extraction` ve travmaya kadar geçen olay sayısı kayıtlı çıktıda
yok — gen2 bloğu yalnız PE izi taşıyor. S6'nın gerektirdiği `f_agent=None`
kolu bu koşumda üretilmedi (kollar: `lived`/`null`/`shuffle`).
⇒ **Altı ikincilin ikisi eksiktir ve bu bir sınırdır.**

---

## 6. İlan edilen sınırlar

§8 gereği bu liste sonuç ne olursa olsun raporda yer alır. **Tam metinleri
`PREREGISTRATION.md` §8'dedir**; aşağıdaki tek satırlar tanımlayıcıdır,
yerine geçmez.

⚠ **Düzeltme:** `CLAUDE.md` beş yerde *"on sekiz ilan edilmiş sınır"* diyor.
Ön-kayıtta **on yedi** var (L1–L17). Sayı bir fazla yazılmış.

| # | Sınır |
|---|---|
| **L1** | Seçilim katmanı atıl — `F_agent` = 0.000 (9/9), birim uyuşmazlığı; aktarım "travmayı uyar"a indirgeniyor |
| **L2** | Popülasyon yok ⇒ seçilim yok; aktarım Lamarckçı, Darwinci değil |
| **L3** | İki nesil ⇒ kalıcılık değil yalnız aktarım iddia edilebilir |
| **L4** | Polarite bandı ve SNR marjı **kalibre değil**; duyarlılık analizi yapılmadı |
| **L5** | GAP-18: `rejected` tarafı az çeşitli, yapısal |
| **L6** | GAP-19: faz-1/faz-2 anıları aynı sayaç uzayını paylaşıyor |
| **L7** | GAP-5: `SYSTEM_PROMPT` lexicon priming |
| **L8** | `W_SEM = 0.0` ⇒ anı seçimi semantik değil; negation sarmalayıcı yok; spillover skaler |
| **L9** | Gen1 ΔPE uç noktası ayrımın %80–86'sını atıyor |
| **L10** | Gen2 `mean_pe` de kayıplı (%73) ⇒ S4 null'ı teşhis edilebilir değil |
| **L11** | S1 birincilden bağımsız değil, onun **desteği**; `resource` bileşeni ayrım üretmiyor |
| **L12** | Tasarım pilot seed'lerinde denetlendi (2001–2003); o seed'ler doğrulayıcı analize girmedi |
| **L13** | Precision-PE işletim noktasında atıl — π tavanda takılı |
| **L14** | Davranışsal sınıflandırıcı `SYSTEM_PROMPT` tarafından besleniyor (GAP-5 doğrulandı) |
| **L15** | Kanal 2 unutmaya bağışık, kanal 1 değil |
| **L16** | Olay sayacı fazlar arası sıfırlanıyor; etkisi bloke ama **gizli** — `F_agent` tek başına düzeltilirse canlanır |
| **L17** | Gen2'nin ilk kararı ata verisini kaçırıyor (GAP-3) |

### Bu koşumda **eklenen** sınırlar

| # | Sınır |
|---|---|
| **L18** | **Kırpma doygunluğu.** `DPO_MAX_GRAD_NORM = 1.0` altında adımların **%100'ü** kırpıldı, en küçük gradyan tavanın ~3 katı. Adım boyunu `lr` değil tavan belirledi ⇒ D-029'un kilitlediği öğrenme oranı bu koşumu tarif etmiyor. Kollara **simetrik** |
| **L19** | **§5 geçerlilik kapısı düştü** (D-053); sonuç §11 gereği **alet null'ı** sınıfında |
| **L20** | **İkincillerin ikisi koşulmadı** — S5'in verisi kayıtlı çıktıda yok, S6'nın kolu üretilmedi |
| **L21** | **Batch başına sayaçlar.** `pair_filter` sayaçları batch'e özgü; B3 topladı, ama `I1.4` her batch'i ayrı yargıladı (D-052'de önceden ilan edildi) |

### GAP-17 — açıklanmadı, açıkça

Üretim çeşitliliği 08-09 pilotuna göre 3–4 kat arttı (`n_unique` 7·4·8 →
bugün ortalama **29.5**) ve sebep **izole edilmedi**. Bu koşumda da yüksek
kaldı. Bisect yapılmadı: karşılaştırma tabanı olan 08-09 pilotu
`tool_identity`'den önce koşuldu ve sampling durumu kayıtlı değil ⇒ **delil
olarak kullanılamıyor**. Raporda bilinmeyen olarak duruyor; bu koşumun
sonucunu etkileyen bir yolu tespit edilmedi, ama **dışlanmadı** da.

---

## 7. Ne iddia edilebilir, ne edilemez

### İddia edilebilir

1. **Ön-kayıtlı doğrulayıcı testte, doğum-drift büyüklüğünde `lived` ile
   `shuffle` arasında fark bulunamadı** (eşleştirilmiş Wilcoxon, N=40,
   p = 0.99, `d_z` = −0.000).
2. **Bu uç noktada `d_z ≥ 0.465` büyüklüğünde bir etki yoktur.**
3. **Alet çalıştı:** deterministik (D-037), konumdan bağımsız (D-042),
   24 kapının 23'ü geçti, kimlik ön-kayıtla birebir.
4. **Kanal 2 atıl değil:** adapter faz-2 kararlarının ortalama %52'sini
   değiştirdi, sıfır değiştiren seed yok.
5. **Eğitim bastırma değil tercih öğrendi:** `delta_logp_chosen` 18/20
   pozitif — D-029'un yakaladığı failure mode tekrarlanmadı.

### İddia **edilemez**

1. ❌ *"Yaşanmışlık parametrik kanaldan aktarılmıyor."* §9-S4/D-047 bunu
   koşum görülmeden yasakladı: `p > 0.05` ⇒ *"şu MDE'nin altında güçsüzüz"*,
   asla *"etki yok"*.
2. ❌ *"Mekanizma yanlış."* §5 düştüğü için sonuç §11 gereği **alet null'ı**
   sınıfında; mekanizma hakkında hüküm vermeye elverişli değil.
3. ❌ *"Adapter davranışı değiştiriyor, demek ki bir şey aktarılıyor."*
   `shuffle` — tercihleri **%100 ters** çevrilmiş kol — davranışı aynı ölçüde
   değiştiriyor (26.6 vs 26.1 / 50). Değişimin varlığı yönünü göstermiyor;
   birincilin `lived` vs `shuffle` olmasının sebebi tam olarak budur.
4. ❌ *"S4 anlamlı çıktı, en azından bir sinyal var."* İşaret ters, medyan
   sıfır, ve §4 birincil null iken ikincilin sonucu değiştirmeyeceğini
   önceden bağladı.

### Bu null'ın değeri

Boş bir null değil: **neden göremediğimizi ölçtük.** `dpo_loss ≈ ln 2` ve
%100 kırpma, bir sonraki koşumun neyi düzelteceğini tahminle değil **sayıyla**
söylüyor. GAP-18 ilk kez nicelendi. Uç noktanın çözünürlüğü ölçüldü.

---

## 8. İkinci ön-kayıta giden liste (bu koşumdan çıkanlar)

| İş | Bu koşumun verdiği girdi |
|---|---|
| **`DPO_MAX_GRAD_NORM` / lr bandı** | %100 kırpma, `grad_norm_min ≈ 2.96` — en somut aksiyon çıktısı |
| **KTO'ya geçiş (GAP-18)** | `uniq_rejected` **100 / 94**, `uniq_chosen` 1025 / 971, `max_rejected_reuse` 47 / 45 ⇒ karar artık sayıyla verilir |
| **S5'in verisini kaydet** | Gen2 davranışsal çıktılar JSON'a hiç girmiyor; ikincil koşulamadı |
| **S6 kolunu üret** | `f_agent=None` duyarlılık kolu tasarımda var, koşumda yok |
| **Uç nokta duyarlılığı** | Yörünge tabanlı uç nokta bu veride daha büyük etki gösteriyor (L9) — **taze veriye** yazılmalı |
| **`F_agent` + GAP-19 birlikte** | ⚠ Ayrı düzeltilirse GAP-19 canlanır (L16/D-051) |
| **A2 — plasebo anı enjeksiyonu** | Eski "getirimi kapat" tasarımı kusurluydu (D-049) |

⚠ Bunların **hiçbiri** bu koşuma geri uygulanamaz; kilit `befd72b4ee57`'de
kapandı (§2.10).

---

## 9. Ham çıktılar

| Ne | Nerede |
|---|---|
| Batch 1 | `dau_runs/prereg_b2_batch1_2004_2023.json` |
| Batch 2 | `dau_runs/prereg_b2_batch2_2024_2043.json` |
| Analiz | `dau_runs/b3_prereg_analysis.json` |
| Koşum logları | `dau_runs/prereg_b2_batch{1,2}.log` |
| Adapter'lar | `dau_runs/adapters/` (80 dizin, seed 2004–2043) |
| Sapma kaydı | `docs/DECISIONS.md` → **D-053** |
