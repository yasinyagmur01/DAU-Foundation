# DAU — Karar Kaydı (Decision Log)

**Bu dosya append-only'dir. Hiçbir kayıt düzenlenmez veya silinmez.**
Bir karar geçersizleştiğinde eski kayda dokunulmaz; onu süperseden yeni bir
kayıt eklenir ve `Süperseder:` alanıyla eskiye bağlanır.

## Bu dosya neden var

2026-08-09 read-only denetiminde, çok-nesilli C′ deneyinin birincil metriği
hakkında **dört kaynak** bulundu ve üçü birbiriyle çelişiyordu:

| Kaynak | Ne diyor |
|---|---|
| `docs/DAU_MASTER_REFERENCE_v20.md` §23 (satır 935) | birincil = gen2 ΔPE, **ikincil** = doğum-drift |
| `CLAUDE.md` satır 64, "Kilitli Kararlar" altında | **birincil** = doğum-drift (Kruskal-Wallis) |
| `cd64cc8` commit gövdesi | "Design decisions (locked, see **pre-reg v1.0 draft §3.3**)" |
| Kod (`run_cprime_multigen._summary`) | `mean_gen2_pe_by_gen1_arm` özetliyor → gen2 PE |

Doğrulanan provenans durumu:

- `Kruskal-Wallis` ve `Fisher-Freeman-Halton` dizgeleri **yalnızca**
  `CLAUDE.md:64`'te geçiyor — master reference'ta, brief'te, kodda yok.
- `pre-reg v1.0 draft §3.3` diye bir dosya **repoda mevcut değil**
  (`find`/`grep` ile arandı). Bir Cursor oturumunda veya belge dışında
  kalmış.
- Yani "yeniden tartışılmaz" başlığı altında, izi sürülemeyen bir madde
  vardı. Ön-kayıt disiplini üzerine kurulu bir projede en tehlikeli hata
  tipi budur: altı ay sonra herkes ona kilitli muamelesi yapar.

Kök neden: iki tane **durum** belgesi (üzerine yazılan) var, hiç **karar**
belgesi (append-only) yok. Bu dosya o boşluğu kapatır.

## Kayıt formatı

```
## D-00X · YYYY-MM-DD · Tek cümlelik başlık
**Durum:** kabul edildi | önerildi | reddedildi | süperseden
**Karar:** ne yapılacak
**Gerekçe:** neden
**Kanıt:** dosya:satır, commit, koşum artefaktı
**Reddedilen alternatifler:** ne değerlendirildi, neden seçilmedi
**Kabul edilen bedel:** bu kararın bilinen maliyeti / daralttığı iddia
**Süperseder:** D-00Y (varsa)
```

`Kanıt` alanı zorunludur. Kanıtı olmayan bir madde karar değil, taslaktır —
`Durum: önerildi` ile girer.

---

## D-001 · 2026-08-09 · Belge stratejisi: üç dosya, üç ayrı iş

**Durum:** kabul edildi

**Karar:** Üç belge, örtüşmeyen görevlerle:

| Dosya | İşi | Yazma modu |
|---|---|---|
| `CLAUDE.md` (kök) | geçerli kurallar + açık GAP'ler, kısa | üzerine yazılır |
| `docs/DECISIONS.md` | karar kaydı | **append-only** |
| `docs/DAU_MASTER_REFERENCE_v20.md` | bilimsel anlatı, formüller, empirik tablo | sürüm sürüm |

`CLAUDE.md`'nin "Kilitli Kararlar" bölümü artık nesir değil, D-numaralarına
işaretçi tutar. Master reference senkronu mekanik iştir → Cursor'a
devredilebilir. Karar kaydı yazmak yargı gerektirir → Claude Code'da kalır.

**Gerekçe:** Durum belgeleri üzerine yazıldıkları için sürüklenir ve
çelişebilir. Append-only bir kayıtta çelişki yapısal olarak imkânsızdır —
eski kayıt durur, yenisi süperseder. Ayrıca `CLAUDE.md` her oturum bağlama
yüklendiği için kısa kalmalı; ayrıntı ayrı dosyaya taşınmalı.

**Kanıt:** Yukarıdaki "Bu dosya neden var" bölümündeki dört-kaynak çelişkisi.
Master reference'ın koddan 4 commit geride kalması (`8c5344b`, `18fb01e`,
`cd64cc8`, `075576e` hiçbiri belgede yok; `04adbdc` yalnızca docs'a dokunmuş).

**Reddedilen alternatifler:**
- *Her şeyi master reference'ta tutmaya devam* — bugüne kadarki yöntem;
  969 satıra ulaştı, güncellemek pahalı olduğu için atlanıyor, gecikme bu
  yüzden oluştu.
- *Her şeyi CLAUDE.md'ye taşımak* — her oturum yüklendiği için token
  maliyeti ve okunabilirlik bozulur.
- *Sadece commit mesajlarına güvenmek* — `cd64cc8` gövdesi gerçekten iyi
  yazılmış, ama commit mesajları anlatı olarak taranamıyor ve mevcut
  olmayan bir belgeye ("pre-reg v1.0 draft") atıf yapabiliyor.

**Kabul edilen bedel:** Üç dosya bakımı. Karşılığında her kilitli maddenin
provenansı yapısal olarak garanti altına alınıyor.

---

## D-002 · 2026-08-09 · Çok-nesilli C′ birincil uç noktası = doğum-drift

**Durum:** kabul edildi

**Karar:** Çok-nesilli C′ pre-registration'ında **birincil uç nokta
transfer anında ölçülen doğum-drift'tir** (`BirthDriftLog`):
`n_transfer_candidates`, doğum drift flag/magnitude'ları,
`n_inherited_warnings` — gen1 koluna göre.

Gen2 ölçümleri (window mean PE **ve** davranışsal: kriz anında
`decision_to_extraction`, hayatta kalma süresi, ilk travmaya kadar geçen
event) **ön-kayıtlı ikincil** olarak koşulur; iddia edilmez, varyans
tahmini üretir.

**Gerekçe:** Nedensel zincir dört halkalı — gen1 kolu → LoRA → ebeveynin son
durumu → transfer içeriği → varisin davranışı. Tek bir uzak uç nokta
ölçüldüğünde null çıkarsa **hangi halkanın koptuğu bilinemez**; projeyi iki
kez yakan tam olarak bu oldu (`INSTRUMENT_LIMITED_NULL`,
`SAMPLE_N15_UNDERPOWERED` — ikisi de yerelleştirilemeyen null).

Doğum-drift, mekanizma çalışıyorsa kolların ayrışmak zorunda olduğu **ilk**
halkadır. Burada fark yoksa gen2'de fark olması imkânsızdır → teşhis
edilebilir null. Ayrıca tamsayı sayımlar üstüne gen2 stokastikliği binmediği
için güç daha yüksek, ve transfer anında ölçüldüğü için gen2 koşmadan elde
edilir → aynı GPU bütçesiyle daha çok seed → `n_eff=12 < 15` sorununu
doğrudan adresler.

**Kanıt:**
- `BirthDriftLog` zaten transfer anında loglanıyor:
  `dau/diagnostics/run_cprime_multigen.py:126-143`, `370-393`.
- Kod yorumu bağımsızlığı doğruluyor: "Birth-drift logged at transfer time
  — independent of gen2 PE" (`run_cprime_multigen.py:541`).
- Yerelleştirilemeyen null geçmişi: master reference §10b.

**Reddedilen alternatifler:**
- *Gen2 PE birincil* (master reference §23 taslağı) — dört halka uzakta,
  null teşhis edilemez, ve önceki N=15 koşumu bu metrikte p=0.637 ile
  underpowered çıktı.
- *Gen2 davranışsal birincil* — aksiyomun asıl iddiası burada yaşıyor, ama
  gürültü tabanı bilinmiyor. Kalibre edilmemiş bir metriği birincil yapmak
  ön-kaydı yakmak olur. Bu yüzden ikincil olarak koşulup bir sonraki
  pre-reg'i güçlendirecek.

**Kabul edilen bedel:** Paper'ın iddiası daralır. "Yaşam nesilden nesile iz
bırakır" değil, **"gen1 plastisitesi neyin miras kaldığını değiştirir"**
olur. Aktarım kanıtlanır, kalıcılık kanıtlanmaz. Bu pre-reg metninde
**açıkça** yazılmalıdır. Beklenen eleştiri — "zor metrik başarısız oldu,
kolayına kaçtınız" — kabul edilir; savunma, doğum-drift'in bir **gerek
koşul** olduğu ve gerek koşulları sırayla kurmanın alet inşasının kendisi
olduğudur.

**Süperseder:** `CLAUDE.md:64`'teki kaynaksız "Kruskal-Wallis (primary,
birth-drift)" maddesi ve master reference §23'ün "birincil = gen2 ΔPE"
taslağı. Not: satır 64'ün adlandırdığı testler (Kruskal-Wallis 3 grup için,
Fisher-Freeman-Halton küçük r×c kontenjans tabloları için) bu uç nokta
tasarımına **iyi oturuyor** — bu, satırın uydurma değil gerçek bir metodoloji
danışmanlığından geldiğini düşündürüyor. Testler korunur, provenansı
Gemini Deep Research arşivi geldiğinde aranacak (bkz. D-006).

---

## D-003 · 2026-08-09 · F_agent transfer kapısı korunur; `f_agent=None` duyarlılık kolu eklenir

**Durum:** kabul edildi

**Karar:** `select_for_transfer` içindeki F_agent kapısı **kaldırılmaz**.
F_agent ayrıca loglanır ve analiz F_agent bandına göre stratifiye edilir.
Ek olarak, aynı koşum `f_agent=None` (legacy Layer-3 yolu) ile **ön-kayıtlı
duyarlılık analizi** olarak tekrarlanır.

**Gerekçe:** Aksiyom, ajanın **içine** trait enjekte etmeyi yasaklar;
dışarıdan seçilim baskısı tanımlamayı değil. Doğal seçilim tam olarak
budur — çevre neyin aktarılacağına karar verir. Kapı kaldırılırsa seçilim
kalmaz, saf Lamarck'çı kopyalama kalır; bu "insanın evrimi gibi" hedefine
daha az benzer.

Ayrıca F_agent yalnızca kısıtlamıyor: düşük fitness + travma durumunda anıyı
düşürmüyor, `inherited_warning` olarak **ekliyor**. Yani kötü giden bir
hayatın travması varise "buradan uzak dur" notuyla geçiyor — bu bir ceza
değil, öğretme mekanizması.

Deneysel olarak da: lived kolu daha uzun hayatta kalırsa → F_agent yükselir
→ daha çok anı eşiği geçer. Bu bir confound değil, **iddianın kendisi**
("yaşam şekillendirdi → daha iyi hayatta kaldı → anıları aktarılmayı hak
etti"). Kapı silinseydi bu nedensel yol da silinmiş olurdu.

Kalan gerçek kırılganlık: `F_agent = 0.4·enerji + 0.3·havuz istikrarı +
0.3·hayatta kalma` ağırlıkları tasarımcı seçimi. Etki F_agent üzerinden
akarsa "bulgu fitness ağırlıklarının artefaktı" eleştirisi gelir. Duyarlılık
kolu tam olarak bunu kapatır: etki iki yolda da varsa artefakt değildir;
sadece kapılı yolda varsa "etki fitness üzerinden dolayımlanıyor" diye
dürüstçe raporlanır.

**Kanıt:**
- Kapının üç ayrı davranışı: `dau/foundation/generation.py:137` (düşük
  fitness + travma → cautionary **ekleme**), `:143-150` (W_transfer eşiği),
  `:152-167` (yüksek fitness → inherited_warning; orta bant → `drift ≥ 1.5`).
- İkinci kod yolu zaten mevcut: `generation.py:127` — `f_agent is None` →
  `_legacy_select_for_transfer`, saf salience/rehearsal/drift.
- Multigen şu an kapılı yolu kullanıyor:
  `run_cprime_multigen.py:340-346` (`consolidate_generation(..., f_agent=...)`).

**Reddedilen alternatifler:**
- *Kapıyı kaldır, F_agent salt gözlem olsun* — Yasin'in ilk tercihiydi,
  sonra ikimiz de geri çektik. Seçilim yolunu siler, aksiyomu korumaz
  (aksiyom içeri enjeksiyonu yasaklar, dışarıdan seçilimi değil).
- *Kapı kalsın, hiçbir şey yapma* — fitness-artefaktı eleştirisine açık kalır.

**Kabul edilen bedel:** Fazladan bir duyarlılık koşumu. `generation.py`'de
**sıfır kod değişikliği** (her iki yol da mevcut); runner'a bir seçenek
eklenmesi gerekir.

---

## D-004 · 2026-08-09 · GAP-1 fix yönü: hard fail + explicit `--lora` flag + alet kimliği

**Durum:** kabul edildi (uygulanmadı)

**Karar:** Multigen runner:
1. `DAU_LORA_ENABLED` kapalıyken **hard fail** etsin — sessiz sahte-null
   üretmesi imkânsız olsun.
2. Explicit `--lora / --no-lora` CLI flag'i alsın; seçim results JSON'una
   yazılsın. `--no-lora` bilinçli bir tercih olarak mümkün kalsın, ama
   varsayılan sessizlik olmasın.
3. Her results JSON'una **alet kimliği** yazılsın: backend, model id,
   quantization, `DAU_LORA_ENABLED`, adapter durumu, sampling parametreleri.

**Gerekçe:** LoRA kapalıyken `run_gen1_arm_lineage`'de `arm` değişkeni
davranışa tek bir yerde dokunuyor (`_train_adapter` çağrısı,
`run_cprime_multigen.py:429-443`). Niş yalnızca `seed`'den geliyor
(`_seed_niche`), `agent_id` prompt'a girmiyor, hafıza deposu her soy için
taze. Dolayısıyla eğitim no-op olunca `lived`/`null`/`shuffle` üç kol değil,
**aynı deneyin üç kopyası** — strict seed lock ile muhtemelen bit-identik.
Böyle bir koşumdan çıkacak p-değeri bilimsel sonuç değil, tautolojidir.

Genel ilke: **bir koşum kendi konfigürasyonunu inkâr edememeli.** Alet
kimliğini kaydetmeyen veya yanlış aletle koşan bir run baştan reddedilmeli.

**Kanıt:**
- `run_cprime_multigen.py` `DAU_LORA_ENABLED`'ı hiçbir yerde set etmiyor;
  yalnızca satır 692'de JSON'a raporlamak için okuyor. CLI flag yok.
- Üç kapı da kapalı: `run_protocol_c_prime.py:697`, `lora_update.py:369`,
  `lora_update.py:404`.
- `_train_adapter` konumu: `run_protocol_c_prime.py:684`
  (`lora_update.py`'de değil).

**Kabul edilen bedel:** Var olan bazı smoke/test akışları env'i açıkça
`0`'a sabitliyor (`test_cprime_multigen.py:181`); hard fail bunları
etkileyecek → `--no-lora` explicit flag'i ile uyarlanmalı.

---

## D-005 · 2026-08-09 · Backend lokale çekilsin (ÖNERİ — kilitli değil)

**Durum:** önerildi

**Karar (önerilen, henüz kabul edilmedi):** Deney runner'larının varsayılanı
`DAU_LLM_BACKEND=local` olsun; `groq` "legacy/keşif" etiketiyle korunsun
(Protocol C provenansı için gerekli, silinmemeli).

**Gerekçe:** Kanal 2 (per-agent adapter, `switch_adapter`, DPO) ağırlık
erişimi ister — Groq'ta ontolojik olarak imkânsız. Yani projenin merkezî
iddiasının test edilemediği konfigürasyon, şu anki varsayılan
konfigürasyon. Mimari zaten ~%90 lokal (MiniLM, DeBERTa NLI, Chroma,
SQLite, PPR); uzak olan tek bileşen karar veren LLM.

Ek gerekçeler:
- **Ön-kayıt bütünlüğü:** uzak endpoint sahibi olunmayan bir alettir.
  Sağlayıcı model sürümünü/quantization'ı habersiz değiştirirse ön-kayıt
  geriye dönük geçersiz olur. `sha256(DAU_LLM_SEED:prompt)` + strict CUDA
  lock makinesi yalnızca lokalde anlamlı.
- **Kayıtsız alet uyumsuzluğu:** Protocol C = Groq `llama-3.1-8b-instant`,
  C′ = lokal Llama-3.1-8B 4-bit NF4. Farklı aletler, ama belgede backend
  farkına dair hiçbir alet etiketi yok (§10b etiketleri yalnızca ADIM 5
  precision'a dair).
- Groq'un kalan tek işlevi (büyük-N frozen koşum) zaten anti-roadmap'te
  yasak; hızlı iterasyon ihtiyacını `DAU_MULTIGEN_MOCK_LLM=1` daha iyi
  karşılıyor.

**Kanıt:** `075576e` commit gövdesi — gerçek Groq ile pilot yeniden
koşumu **TPD rate limit'ine takılmış**, 6 soydan yalnızca 5'i tamamlanmış
("unrelated infra issue"). Uzak backend koşumu fiilen yarıda kesiyor;
teorik risk değil, yaşanmış.

**Kabul edilen bedel:** 8GB VRAM tavanı → çok-ajanlı eşzamanlılık zorlaşır.
Punica adapter takası bunu çözüyor; bedeli bellek değil, zaman.

**Zamanlama uyarısı:** Backend varsayılanını değiştirmek aleti
değiştirmektir. Çok-nesilli pre-reg henüz yazılmadığı için pencere şu an
açık; pre-reg kilitlendiği an bu değişiklik **post-hoc** olur ve
pre-registration kuralını çiğner. Karar pre-reg yazımından **önce**
verilmelidir.

---

## D-006 · 2026-08-09 · Gemini Deep Research arşivi mutabakat süreci

**Durum:** kabul edildi (uygulanmayı bekliyor — arşiv henüz gelmedi)

**Karar:** Geçmiş tüm Gemini Deep Research çıktıları repo köküne
`RESEARCH_BRIEF_v*.md` olarak dosya halinde girer (sohbete yapıştırılmaz —
dosyalar oturumlar arası kalır, grep'lenir, commit'lenir). Her brief için
Claude Code bir mutabakat tablosu üretir:

| Brief ne diyor | Kod ne yapıyor | Karar |
|---|---|---|

Karar sütunu dört değerden biri: `bilinçli sapma` (+gerekçe) ·
`fark edilmemiş kayma` · `uyumlu` · `brief yanılmış`.

Sonuç yönlendirmesi:
- **bilinçli sapma** → bu dosyaya gerekçesiyle D-kaydı olarak girer
- **fark edilmemiş kayma** → `CLAUDE.md`'ye GAP olarak girer
- **brief yanılmış** → kaydedilir, ileride yeniden içeri sızmasın diye

**Gerekçe:** Araştırmadan sapılan yerler kafa karıştıran şey değil, en
değerli veri — her sapma ya gerekçesi kaybolmuş bilinçli bir karardır ya da
fark edilmemiş bir kaymadır. İkisi de bilinmelidir. Brief'ler **iddia değil
hipotez** olarak alınır ve her iddia kod tabanında ayrıca doğrulanır, yani
brief ile kodun çelişmesi bir eylem değil bir soru üretir.

**Kanıt:** D-002'de tespit edilen provenans boşluğu — `Kruskal-Wallis` /
`Fisher-Freeman-Halton` yalnızca `CLAUDE.md:64`'te geçiyor ve testler uç
nokta tasarımına teknik olarak iyi oturuyor. Kaynağın bu arşivin içinde
olması kuvvetle muhtemel.

---

## D-007 · 2026-08-09 · Soru yönlendirme: hangi soruyu kim cevaplar

**Durum:** kabul edildi

**Karar:**

| Soru tipi | Kim cevaplar |
|---|---|
| "Biz neye karar vermiştik / neden böyle yaptık" | git geçmişi + Yasin; Claude Code kazar |
| "Kod gerçekten ne yapıyor" | Claude Code, read-only denetim |
| "Literatürde X mi Y mi savunulabilir, kim ne yapmış" | Gemini Deep Research |
| "Bu deneyde X mi Y mi olsun" | Yasin — DR ve Claude Code girdi verir, karar Yasin'in |

**Gerekçe:** 2026-08-09'da "§23 mü CLAUDE.md mi haklı, buna Deep Research
karar versin mi?" sorusu geldi. Cevap hayır: bu bir literatür sorusu değil,
**provenans** sorusu. DR'nin commit geçmişine, Cursor oturumlarına veya
kayıp pre-reg taslağına erişimi yok; sorulsaydı makul görünen bir metodoloji
metni üretirdi ve kaynaksız satır sayısı ikiye çıkardı.

**Kanıt:** Çelişki fiilen arkeolojiyle çözüldü (`grep` + `git log` +
`find`), literatürle değil — bkz. D-002 `Süperseder` alanı.

---

## D-008 · 2026-08-09 · Deep Research arşivi: konum, tarih düzeltmesi, ilk mutabakat

**Durum:** kabul edildi

**Karar:**
1. Ham brief'ler `docs/research/` altında durur (D-006'nın "repo kökü"
   maddesini **süperseder** — 10+ dosya kökü dağıtıyordu).
2. Damıtılmış mutabakat: `docs/research/RECONCILIATION.md`, **DAU konusuna
   göre** indeksli (brief'e göre değil).
3. Kök `RESEARCH_BRIEF_v1.md` **kaldırıldı**; içeriği (Yasin'in elle yaptığı
   triyaj) `RECONCILIATION.md`'ye devredildi. Mutabakatın iki dosyaya
   bölünmesi D-001'in önlemek için var olduğu sürüklenme desenidir.
4. `2026-08-03_per-agent-lora-serving.md` → `2026-08-08~_...` olarak
   yeniden adlandırıldı.

**Gerekçe (tarih düzeltmesi):** Raporun gövdesi `v2.3`, `v2.4`,
`SAMPLE_N15_UNDERPOWERED` ve v3 smoke sonuçlarına (`saturation_rate=0.0025`,
`π_n=14`) atıf yapıyor. Master reference §22'ye göre v2.3/v2.4 = 2026-08-07,
v2.4.1 (v3 smoke PASS) = 2026-08-08. Kaynak prompt'un tamamı tarandı; bu
dizgelerin **hiçbiri** prompt'ta yok. Dolayısıyla rapor en erken 08-07'de,
gerçekçi olarak 08-08'de üretilmiş. Kök triyaj dosyasının mtime'ı
2026-08-09 15:05.

**Kanıt:**
- `grep -c -i qwen docs/research/*.md` → yalnızca bu dosyada (3 eşleşme);
  arşivde başka hiçbir brief model seçimi tartışmıyor.
- Sürüm işaretçisi taraması: `v2.3`/`v2.4`/`SAMPLE_N15` yalnızca bu
  dosyada; diğer 9 brief kendi tarih damgası dışında hiçbir DAU sürüm
  etiketi içermiyor.

**Sonuç:** Bu brief arşivin **en yenisi**, en eskisi değil. Dolayısıyla
§7'deki Qwen-2.5-7B tavsiyesi bayat değil, **güncel** tavsiye —
Yasin'in sezgisi doğrulandı.

**Kabul edilen bedel:** Tarih `~` ile yaklaşık işaretlendi (08-08 ile 08-09
arası kesinleştirilemedi). Yasin tam tarihi hatırlarsa `git mv` ile
sabitlenebilir.

**Süperseder:** D-006 (yalnızca dosya konumu maddesi; süreç maddeleri
geçerliliğini korur).

---

## D-009 · 2026-08-09 · İlk mutabakattan çıkan üç bulgu

**Durum:** kabul edildi (bulgu kaydı — aksiyonlar ayrı kararlara bağlı)

**Karar:** `2026-08-08~_per-agent-lora-serving.md` mutabakatı üç yeni bulgu
üretti; üçü de kaydedildi ve yönlendirildi:

1. **Gradient accumulation yok** → `CLAUDE.md` GAP-8 (yeni).
   Brief §2 "`BATCH_SIZE=1` ve gradyan biriktirme" diyor; DAU
   `BATCH_SIZE=1` + gradient **checkpointing** uygulamış — farklı teknik.
   `local_llm.py:610-627` her çift için ayrı `zero_grad()` + step →
   efektif batch = 1. `fark edilmemiş kayma`.
2. **Adapter hot-swap'te CUDA sync / `empty_cache` yok** → GAP-6 önceliği
   yükseltildi. Brief §1 bunu izolasyon **doğruluğu** şartı sayıyor;
   CLAUDE.md ise "temizlik" olarak listeliyordu. `açık`.
3. **Qwen-2.5-7B tavsiyesi güncel** → D-005 girdisi. `bilinçli sapma`
   (kök triyajda "aksiyon değil" diye ertelenmişti), ama D-005 aleti
   kilitlemek üzere olduğu için yeniden açıldı.

**Ayrıca kapandı:** `K=5` / `N≥15` / `n_eff≥12` provenansı — brief §5.
D-002'nin `Süperseder` alanındaki provenans boşluğunun bu kısmı çözüldü.

**Ayrıca hâlâ açık:** Kruskal-Wallis + Fisher-Freeman-Halton bu brief'te
**yok**. Brief §5'in önerdiği varsayılan testler paired t-test + Wilcoxon.
Çelişki değil — paired testler gen1'in eşleştirilmiş 2-kol tasarımına,
KW ise D-002'nin eşleştirilmemiş 3-grup doğum-drift tasarımına oturuyor.
Provenans araması sıradaki brief'te sürecek
(`2026-08-06_protocol-c-metacognition-eval.md`).

**Kanıt:** `docs/research/RECONCILIATION.md`, tam tablo.

**Zamanlama uyarısı:** Bulgu 1 ve 3 **alet değişikliği** anlamına gelir.
D-005 ile aynı pencerede — pre-reg kilitlenmeden önce karara bağlanmalı,
sonrasında post-hoc olur.

---

## D-010 · 2026-08-09 · Deep Research arşivi mutabakatı tamamlandı (9 brief)

**Durum:** kabul edildi

**Karar:** D-006 mutabakat süreci 9 brief için tamamlandı. Tam tablo:
`docs/research/RECONCILIATION.md`, DAU konusuna göre indeksli.
`2026~_agent-curriculum-engine.md` Yasin tarafından "DAU sonrası proje"
olarak ertelendi, işlenmedi.

**Üretilen kayıtlar:**
- `CLAUDE.md` GAP-8 genişletildi (beş ayarlı DPO sinyal gücü)
- `CLAUDE.md` GAP-9 eklendi (N=15 güç analizi)
- `CLAUDE.md` GAP-10 eklendi (süresi dolmuş ölçüm ertelemeleri)
- GAP-5'e provenans notu eklendi
- GAP-6 önceliği yükseltildi (CUDA sync = izolasyon doğruluğu şartı)

### Bulgu 1 — Beş tavsiye, tek yön: DPO sinyal gücü

Beş bağımsız brief maddesi aynı şeye işaret ediyor ve beşi de kısmen veya
hiç uygulanmamış: gradient accumulation yok · `seq_len` 512 yerine 256 ·
1 epoch yerine 3 önerilmiş · %10 somatik replay hiç yok · **tercih
çiftlerinde mutlak PE eşiği yok** (`PE_RANK_MIN_GAP = 1e-6`, oysa brief
`PE < 0.15`'in ön-eğitilmiş ağırlık gürültüsünde kaybolduğunu, SNR için
`PE ≥ 0.40` gerektiğini söylüyor).

Tek tek küçük; birlikte "eğitim çalıştı ama iz bırakmadı" sonucunun
teknik açıklaması olabilirler.

**Kanıt:** `local_llm.py:610-627` · `constraints.py:51,56` ·
`lora_update.py:66` (`PE_RANK_MIN_GAP`) · `grep replay|rehearsal|anchor`
yalnızca biyoloji-analojisi docstring'leri buluyor.

### Bulgu 2 — N=15 baştan yetersizdi, ve bu öngörülmüştü

`protocol-c-metacognition-eval` güç analizi: `σ_PE = 0.256`, eşleştirilmiş
tasarımda `d_z ≈ 1.5·d`. Gerekli çift sayısı d=0.5→16, d=0.4→24,
d=0.3→41, d=0.2→90; Protocol C için **N=40-50** öneriliyor.
`sentetik-kognisyon` §1.6 de N=15-20'yi **açıkça d=0.5 varsayımına**
bağlıyor.

DAU'nun gözlediği etki: `lived +0.008` vs `shuffle +0.019`, σ≈0.256
⇒ **d ≈ 0.04**. Bu büyüklük için yüzlerce çift gerekir.

`SAMPLE_N15_UNDERPOWERED` bir sürpriz değildi; güç analizi onu önceden
söylüyordu. **Sonuç:** çok-nesilli pre-reg'de N varsayılan olarak 15
alınamaz. Bu, D-002'yi bağımsız olarak destekliyor — doğum-drift tamsayı
sayımları PE'den yüksek güçlü.

### Bulgu 3 — KW / FFH provenansı yok, arama bitti

`Kruskal-Wallis` ve `Fisher-Freeman-Halton` **9 brief'in hiçbirinde
geçmiyor.** Brief'lerin önerdiği testler: paired t-test, Wilcoxon
(08-08~ §5 ve protocol-c-eval) ve eşleştirilmiş ikili travma sonuçları
için **McNemar** (protocol-c-eval).

**Karar:** bu iki test adı **türetilmiş** kabul edilir, kaynaklı değil.
Silinmiyorlar — 3-grup eşleştirilmemiş doğum-drift tasarımına teknik
olarak uygunlar — ama `CLAUDE.md`'de "kilitli" etiketleri kaldırıldı.
McNemar eksik test olarak kaydedildi.

### Bulgu 4 — D-002'ye dokunan üç tasarım girdisi

- **Duyarlılık hiyerarşisi gerilimi:** protocol-c-eval `PE_{t+1}`'i
  Rank 1 (en duyarlı) sayıyor; D-002 PE'yi ikincile düşürdü. Farklı
  deney (Protocol C nesil-içi vs doğum-drift nesiller-arası), yani
  doğrudan çelişki değil — ama kayda geçmeli.
- **OOD Behavioral Probing** (sentetik §1.6): yaşantıdan sonra ChromaDB
  retrieval **tamamen kapatılır**, yalnızca ağırlıklara yansıyan değişim
  ölçülür. Kanal 2'yi Kanal 1'den izole etmenin temiz yolu; DAU'da yok.
  D-002'nin doğrudan tamamlayıcısı — pre-reg'e alınmalı.
- **≥3 nesil:** sentetik §1.4 trait stabilizasyonu için ≥30-50 olay **ve
  ≥3 nesil konsolidasyonu** gerektiğini söylüyor. Multigen 2 nesil.

### Bulgu 5 — Süresi dolmuş ertelemeler

`W_SEM = 0.0` (ChromaDB skorlamaya girmiyor) ve negation kural
sarmalayıcısı, `v1-kritik-sistem-audit` tarafından "baseline kilitlenince
yap" diye ertelenmişti. Protocol C baseline'ı artık paper-locked — koşul
gerçekleşti, kimse dönmedi. → GAP-10.

### Bulgu 6 — Bir brief yanıldı, DAU deneyle çürüttü

`metacognition-neuroscience` §"Feasibility": *"Genuine metacognition is
**fully achievable** with frozen-weight LLMs when implemented as a
system-level property… Metacognition is a property of the structural
control loop, not the individual model weights."*

DAU bunu Protocol C ile **yanlışladı** (ΔPE ≈ 0, paper-locked null).
Brief out-of-band meta-observer mimarisini doğru tarif etti ama
etkinliğini yanlış öngördü.

**Bu paper için değerli:** projenin ana katkısı, literatürün "sistem
seviyesinde çözülür" beklentisini ampirik olarak karşılamıyor. Paper
anlatısına girdi olarak kaydedildi.

### Doğrulananlar (aksiyon yok)

DAERM formülleri, `MAGNITUDE_PEAK_WEIGHT=0.70` / `M=0.82·PE`, ham-PE
decoupling, Punica `r=8/α=16`, HippoRAG 2 PPR, crisis somatic enforcement,
adapter disk izolasyonu, Protocol C tasarımı, null framing çerçevesi ve
trait injection yasağı — hepsi brief tavsiyeleriyle **birebir uyumlu**.
Trait yasağı dört bağımsız kaynakta doğrulanmış.

**Kabul edilen bedel:** Bulgu 1 ve 2 birlikte, GAP-1 fix'inden önce bir
"alet yükseltmesi" kararı gerektiğini gösteriyor. Bu, pre-reg'i geciktirir.
Alternatif — mevcut aletle koşmak — güç analizine göre baştan başarısız
olacağı bilinen bir deney koşmak demektir.

---

## D-011 · 2026-08-09 · Koşum yolu denetimi: beş sessiz sapma

**Durum:** kabul edildi (bulgu kaydı — düzeltmeler ayrı commit'lerde)

**Karar:** `docs/RUNPATH_AUDIT.md` (Cursor, read-only, 28 dosya, K1–K8 +
28 BELİRSİZ) üzerinden yapılan doğrulamada beş sessiz sapma tespit edildi
ve `CLAUDE.md`'ye GAP-11..15 olarak kaydedildi. Hiçbiri exception atmıyor;
hepsi sessizce başka bir davranışa düşüyor.

**Kanıt:** commit `db6931f` (denetim dosyası) + aşağıdaki bireysel
doğrulamalar.

### Bulgu 1 — Shuffle kolu process'ler arası reproducible değil

`_seed_from_agent_id` (`run_protocol_c_prime.py:567-573`) trailing segmenti
int'e çevirmeye çalışır, olmazsa `abs(hash(agent_id)) % 2**31` döner.
Multigen `agent_id`'si `cprime-{arm}-{seed}-g1` → `int("g1")` ValueError →
hash fallback. `PYTHONHASHSEED` repoda hiçbir yerde set edilmiyor; Python
string hash'ini process başına rastgeleleştirir.

Ampirik: aynı `agent_id`, üç ayrı process → `419643228`, `227385495`,
`229629477`.

**Kök neden:** `cd64cc8` (multigen) `agent_id`'ye `-g1` eki ekledi.
Protocol C′'de `cprime-shuffle-2001` → `int("2001")` çalışıyordu.
Fonksiyonun docstring'i hâlâ eski formatı (`cprime-{arm}-{seed}`) yazıyor.
Uzaktaki bir dosyada, sessizce, fark edilmeden kırıldı.

**Etki:** shuffle kolunun tercih çifti karıştırması her koşumda farklı.
Üç koldan biri replay garantisinin dışında.

### Bulgu 2 — Gen2 seed-locked değil, ve asimetrik

`run_gen1_arm_lineage` phase-1 (`:411`) ve phase-2 (`:446`) `_lock_seeds`
çağırıyor; `run_gen2_measure` çağırmıyor. Gen2, gen1'in bıraktığı global
RNG durumuyla başlıyor.

Asıl sorun asimetri: lived ve shuffle kolları eğitim yapıyor (LoRA reset
`init_lora_weights=True` + DPO, torch RNG tüketiyor), null yapmıyor.
Üç varis gen2'ye farklı RNG durumlarıyla giriyor — kol farkından değil,
eğitimin yan etkisinden.

### Bulgu 3 — Multigen'de precision audit hiç yapılmıyor

`ArmResult`'ın `saturation_rate` / `pi_n_distinct` / `n_pe_events_audited`
/ `n_saturated` / `pi_values` alanları `run_cprime_multigen.py`'de hiç
doldurulmuyor (grep sıfır sonuç) → JSON'a default sıfır/boş gidiyor.

v2.4.1'de v3 smoke'un tüm anlamı bu alanlardı ("alet sağlıklı mı").
Multigen koşumunda o kontrol yok; precision doygunluğu geri gelse
haberimiz olmaz.

### Bulgu 4 — PPR (ADIM 4) koşum yolunda inert

Zincir sonuna kadar takip edildi:
- `memory_edges` tablosunu dolduran tek yer: `store.write_edge`
- `write_edge`'i çağıran tek yer: `consolidation.run_consolidation`
- `run_consolidation`'ı çağıranlar: `run_memory_demo.py` (demo) ve
  `memory_bridge.py:113` (sarmalayıcı)
- O sarmalayıcıyı çağıran: **hiç kimse** (testler hariç)

Sonuç: `memory_edges` koşum boyunca boş. `compute_ppr_scores` boş graf
görüp `{seed_domain: 1.0}` dönüyor. Yani:

```
memory_score = 0.21·recency + 0.28·magnitude + 0.21·domain_match + 0.30·ppr
             → ppr sabit → fiilen 0.21·recency + 0.28·magnitude + 0.51·domain_match
```

PPR bir HippoRAG çağrışımı değil, domain_match'in ağırlığını büyüten bir
sabit. **Master reference §6 ve §19 ADIM 4'ü uygulanmış entegrasyon olarak
sunuyor** — kod ve test var, ama koşum yolunda çalışmıyor. Belge
düzeltmesi gerekecek (v2.4.2).

### Bulgu 5 — `TEMPERATURE` import anında donuyor

`run_protocol_c_prime.py:73` `DAU_LLM_TEMPERATURE`'ı **import anında**
okuyor. `_lock_seeds` her çağrıldığında env'i o import-time değeriyle
**geri yazıyor** (`:460`). Import'tan sonra env'i değiştirmek sessizce
etkisiz.

**Kabul edilen bedel / kapsam notu:** Denetim 28 BELİRSİZ maddesi bıraktı;
çoğu kovalanmadı (altın kaplama olurdu). Bulgu 1 ve 4 bu maddelerden
türetildi, kalanlar açık bırakıldı.

**Metodolojik not:** Arşiv mutabakatı (D-010) *yoklukları* buldu (GAP-8:
olması gerekip olmayan şeyler). Koşum yolu denetimi *sessiz sapmaları*
buldu (bu kayıt). İki yöntem farklı hata sınıfları yakalıyor; ikisi de
gerekliydi. Hiçbiri kavramsal hataları yakalayamaz (GAP-5 tipi).

---

## D-012 · 2026-08-09 · Preflight değişmezleri kilitlendi

**Durum:** kabul edildi (koda dökülmeyi bekliyor)

**Karar:** `docs/PREFLIGHT_INVARIANTS.md` — 20 değişmez, 6 faz. Koşum,
sonuç yazmadan önce kendisi hakkında bu listeyi kanıtlamak zorunda.
İki mod: **ABORT** (JSON yazılmaz) ve **FLAG** (yazılır ama etiketlenir).

**Gerekçe:** Bu projede yedi alet arızası oluştu ve yedisi de sayı üretti
(`lora_B=0`, adapter sızıntısı, greedy plato, precision doygunluğu,
GAP-1, GAP-11, GAP-14). Hiçbiri çökmedi. Hastalık "bug kaçırdık" değil,
sistemin anlamlılıktan bağımsız çıktı üretmesi. Değişmez bunu tersine
çevirir.

Daha çok kod okumak bu sorunu çözmez: okuma tek seferlik fotoğraftır ve
yalnızca *orada olanı* gösterir. GAP-1 okumayla bulundu; GAP-8
(gradient accumulation, replay, PE eşiği **yoklukları**) okumayla
bulunamazdı. Değişmez ise kalıcıdır ve regresyonu da yakalar.

**Kilitlenen tasarım kararları:**
1. I4.1 (replay testi) yalnızca ilk seed'de — maliyet ~1/N. RNG sızıntısı
   sistemiktir; seed'e özgü olsaydı I2.1 yakalardı.
2. I2.1 hash = `sha256(karar dizisi ++ PE dizisi)`. Ajan son durumu hariç
   (türev bilgi + kayan nokta yanlış-pozitifi). Kararlar tek başına yetmez:
   aynı kararlar farklı PE üretebilir, bu gerçek ayrışmadır.
3. I5.1 (PPR canlılığı) GAP-14 kararına kadar FLAG.
4. Raporlama: JSON'a `invariants: {}` + `run_quality: clean|flagged|aborted`.
   **`flagged` koşumlar analizde varsayılan olarak dışlanır**; dahil etmek
   ön-kayıtta gerekçe ister.

**Kural:** Eşiği kalibre edilmemiş hiçbir değişmez ABORT olamaz —
keyfi sabitle koşum öldürmek olur. `SNR_FLOOR=0.40` ve
`SATURATION_MAX≈0.05` kaynaklı (sırasıyla sentetik-kognisyon §1.2 ve
v3 smoke ölçümü); `MIN_PAIRS`, `SNR_PAIR_RATIO_MIN`, `GATED_FRACTION_MAX`
kaynaksız → pilotta ölçülüp **sonra** ön-kayıtla kilitlenecek.

**Kapsam dışı (bilinçli):** K1'deki 98 sessiz yolun çoğu (iyi huylu),
28 BELİRSİZ'in kalanı (altın kaplama), GAP-5 (değişmezle yakalanamaz —
kod doğru olanı yapıyor, sorun kavramsal), GAP-10 (baseline'ı değiştirir,
ayrı karar).

**Kabul edilen sınır:** Değişmezler mekanik arızayı yakalar, kavramsal
arızayı yakalamaz. Kalan riski sıfırlamıyoruz; riski *sessiz* olmaktan
çıkarıp *gürültülü* yapıyoruz.

---

## D-013 · 2026-08-09 · main merge'ü alet fazı sonrasına ertelendi

**Durum:** kabul edildi (ertelenmiş iş — unutulmaması için kayıt)

**Karar:** `main` merge'ü/taşıması, kod düzeltme + alet yükseltmesi fazı
bitene kadar yapılmaz. Çalışma `cursor/per-agent-qlora-adapter-c116`
üzerinde sürer.

**Kanıt (2026-08-09'da ölçüldü):**
- Ortak ata `ece09b1` (v1.4 milestone). main'de **10**, bu branch'te **40**
  commit → `git merge-base --is-ancestor main HEAD` **başarısız**:
  fast-forward değil, **gerçek diverjans**.
- İki hat aynı özellikleri **bağımsız** geliştirmiş: `local_llm.py`,
  `lora_update.py`, `nli_filter.py`, `llm_backend.py`, `environment.py`
  crisis. Merge çatışmaları tam da en kritik dosyalarda çıkar.
- main'de bu branch'te **hiç olmayan 9 dosya** var. Üçü önemli:
  `dau/foundation/tests/test_llm_backend.py`,
  `dau/foundation/tests/test_local_llm.py`,
  `dau/foundation/tests/test_lora_update.py` — **tam da değiştireceğimiz
  modüllerin testleri.** main'in implementasyonuna göre yazıldılar,
  bu branch'e olduğu gibi geçmeyebilirler → körlemesine alınmaz, incelenir.
  Diğerleri: `dau/diagnostics/run_vram_spike.py`, `requirements-lora.txt`,
  süpersede `DAU_MASTER_REFERENCE_v15.{md,html,pdf}` ve `v16.md`.
- main'in tepe commit'i `43efef6 "checkpoint before checking out
  cursor/per-agent-qlora-adapter-c116"` — Cursor otomatik checkpoint'i,
  kasıtlı bir geliştirme değil.

**Gerekçe:** Hassas kod fazının hemen öncesinde riskli bir git operasyonu,
"bir daha başarısız çok adımlı aksiyon istemiyorum" ilkesinin tam tersi.
Ayrıca çözülmek istenen asıl sorun — yeni oturumun hangi hatta olduğunu
bilmemesi — merge gerektirmiyor; `CLAUDE.md`'deki "Şu An Neredeyiz"
bölümüyle çözüldü.

**Reddedilen alternatifler:**
- *Şimdi merge* — çatışmalar `local_llm.py`/`lora_update.py`'de çıkar,
  yani tam da değiştirmek üzere olduğumuz dosyalarda. İki riski üst üste
  bindirir.
- *`main`'i şimdi bu branch'e force-push ile sıfırla* — muhtemelen doğru
  nihai çözüm (main hattı süpersede görünüyor), ama geri dönüşü zor ve o
  üç test dosyası incelenmeden yapılamaz.

**Yapılacak sıra (alet fazı sonrası):**
1. Üç test dosyasını incele — bu branch'e uyarlanabilir bir şey var mı
2. Varsa cherry-pick / uyarla
3. `main`'i bu hatta taşı
4. Uzağa gönder (push — kullanıcı onayıyla; şimdiye kadar hiç push yapılmadı)

**Kabul edilen bedel:** Branch adı (`per-agent-qlora-adapter-c116`) artık
içeriği tarif etmiyor — repoda karar kaydı, araştırma arşivi ve denetimler
de var. Kozmetik, zararsız.

---

## D-014 · 2026-08-09 · Nesil zinciri 2 ile sınırlı değil — hedef N nesil

**Durum:** yön beyanı (Yasin, 2026-08-09). Kilitli karar **değil** — ön-kayıt
yazılmadı, N belirlenmedi. Kaybolmaması için kayda geçiriliyor.

**Beyan:** "Uzun nesiller devam etmek gibi bir düşüncem var." Yani gen1 → gen2
tek sıçraması nihai tasarım değil, şu an koşulabilen en kısa hal. Asıl hedef,
evrimin birden fazla nesil boyunca aktarılıp aktarılmadığını görmek.

**Neden şimdi kayda giriyor:** GAP-13 düzeltmesinin kapsamı bu beyanla
belirlendi. Plan yalnızca gen1'in precision audit alanlarını doldurmayı
istiyordu; gen2 de eklendi (`090a5bc`), çünkü zincir uzayacaksa her nesil
kendi alet sağlığını taşımalı — yoksa N. nesildeki doygunluk, N-1'in
verisiyle örtülür ve zincir boyunca sessizce birikir.

**Kodun bugünkü durumu (2026-08-09'da doğrulandı):**

Nesil-agnostik olan (değişiklik gerektirmez):
- `consolidate_generation` / `apply_generation` (`generation.py:236`, `:316`)
  — sayaç bire bir artıyor, derinlik varsayımı yok.
- `_seed_from_agent_id` (`8cf2ac0`) — `-g{n}` ekini herhangi bir `n` için
  ayrıştırıyor, `-g3`/`-g7` bugünden çalışır.

İki nesle çakılı olan (zincir uzatılırken elden geçecek):
- `PARENT_SUFFIX = "g1"` / `HEIR_SUFFIX = "g2"` sabitleri
  (`run_cprime_multigen.py:104-105`) — nesil indeksinin fonksiyonu olmalı.
- `run_lineage` tek sıçrama: gen1 → transfer → gen2. Döngüye dönmeli.
- `Gen2Result` adı ve `EVENTS_GEN1` / `EVENTS_GEN2` parametre çifti —
  nesil başına liste ya da tek parametre.
- Vault ömrü: bugün soy başına bir `TemporaryDirectory`, zincir boyunca
  büyüyecek bir kasanın maliyeti ölçülmedi.

**Açık sorular (ön-kayıttan önce cevaplanmalı):**
- N kaç? Her nesil ayrı bir ölçüm noktası ⇒ istatistiksel güç N ile nasıl
  değişiyor (GAP-9 güç analizi 2 nesil varsayımıyla yapıldı).
- Adapter mirası: bugün 3A kuralı "varis ebeveynin adaptörünü yüklemez".
  Zincir uzarsa bu kural her nesilde mi geçerli, yoksa parametrik mi olmalı?
- Ebbinghaus decay + N nesil: GAP-4'ün (kasa↔LoRA senkron kopukluğu)
  şiddeti nesil sayısıyla artar mı?

**Etki:** `EXECUTION_PLAN.md` D-10'daki "2 vs 3 nesil" maddesi artık
"2 vs N" olarak okunmalı.

---

## D-015 · 2026-08-09 · "Proje safi lokal LLM'de koşacak" — yön beyanı

**Durum:** yön beyanı (Yasin, 2026-08-09). D-005'i **kilitlemez**, ona kanıt
ve niyet ekler. Kod default'u bu kayıtla değişmiyor.

**Beyan:** "Proje safi lokal LLM'de çalışacak." Uzak backend (groq) hedef
konfigürasyon değil; Protocol C provenance'ı için tarihsel olarak duruyor.

**Neden şimdi kayda giriyor:** Adım 5'te (`afbb552`) `--lora` + uzak backend
kombinasyonuna hard fail kondu. O kontrolün gerekçesi doğrudan bu beyandır:
kod **hâlâ** uzak backend'i varsayılan kabul ediyor (`LLM_BACKEND_DEFAULT =
"groq"`, `llm_backend.py:18`), yani lokal kullanmak isteyen her koşumun
env'i açıkça set etmesi gerekiyor. Set etmeyi unutan bir koşum bugün sessizce
uzağa gider ve eğitim hiç olmaz. Kontrol, yanlış varsayılanın sessiz zararını
gürültülü hale getiriyor — varsayılanı düzeltmiyor.

**Neden default şimdi değişmiyor:** backend varsayılanını değiştirmek aleti
değiştirmektir; GAP-8 (DPO ayarları) ve GAP-14 (PPR) ile aynı karar
paketinde, `EXECUTION_PLAN.md` C bölümündeki karar kapısında verilecek.
Beyan orada tartışmayı sıfırdan başlatmamak için buraya yazıldı.

**Sonuç:** Karar kapısında D-005 kilitlenirken bu beyan girdi kabul edilir.
Kilitlenirse `LLM_BACKEND_DEFAULT` lokale döner ve `--lora`/backend tutarlılık
kontrolü fiilen hiç ateşlenmez hale gelir — istenen budur.

---

## D-016 · 2026-08-09 · Quantization belgede NF4, kodda fp4 — ölçüldü

**Durum:** bulgu kaydı. Karar **verilmedi**, kod değiştirilmedi.

**Ölçüm (2026-08-09):** `local_llm.build_load_kwargs` (eskiden
`load_local_model` gövdesi) `BitsAndBytesConfig(load_in_4bit=True,
bnb_4bit_compute_dtype=torch.float16)` kuruyor. `bnb_4bit_quant_type`
**set edilmiyor**. Kurulu transformers 5.14.1'de bu alanın default'u `fp4`:

```
quant_type default: fp4      double_quant default: False
```

`CLAUDE.md` GAP-7 ve master reference "lokal Llama-3.1-8B **4-bit NF4**"
diyor. Koşulan şey NF4 değil.

**Neden kod değiştirilmedi:** quantization tipini değiştirmek aleti
değiştirmektir. Ön-kayıt henüz yazılmadı, yani pencere açık — ama değişiklik
karar kapısına getirilmeden yapılırsa "önce karar, sonra değişiklik" kuralı
çiğnenir ve proje bir kez daha sessizce alet değiştirmiş olur.

**Bunun yerine yapılan:** `afbb552` alet kimliğine **gerçek** değeri yazıyor
(`quantization.quant_type: "fp4"`), ve `describe_quantization()` config'i
loader'ın kendisinden okuyor — ikinci bir kurulum bir gün ayrışırdı.

**Karar kapısına taşınan soru:** NF4'e geçilsin mi (belge doğru, kod yanlış),
yoksa fp4 kabul edilip belgeler mi düzeltilsin (kod doğru, belge yanlış)?
NF4 literatürde 4-bit için normal tercih; ama bu, ölçülmemiş bir kalite
iddiası. GAP-8 paketiyle birlikte karara bağlanacak.

**Belge borcu:** `CLAUDE.md` GAP-7 ve master reference §10b — v2.4.2'de
düzeltilecek.

---

## D-017 · 2026-08-10 · Preflight gate koşuldu; 24 değişmezin 17'si kodda

**Durum:** uygulama kaydı + iki düzeltme.

**Adım 7 sonucu (ateşlendi, 2026-08-10):**

- *Koşum 1* — `--n-pairs 1 --mock-llm`, flag yok → `exit=1`, JSON yazılmadı.
  Gerekçe I0.2 (LoRA kapısı bilinçli değil).
- *Koşum 2* — `--lora --mock-llm` → `exit=0`, Faz 0'ın altısı geçti,
  `run_quality=flagged`, planın öngördüğü I2.1 FLAG'i çıktı.

İki koşum arasındaki fark gate'in sabit yeşil basmadığını gösteriyor:
I5.2 (NLI aktif mi) `--no-lora`'da **kaldı**, `--lora`'da **geçti**.

**Gate'in kendiliğinden bulduğu iki gap:** I5.1 → GAP-14 (PPR atıl,
`memory_edges` her yaşamda boş), I5.4 → GAP-3 (inherited somatic scale hiç
uygulanmıyor, `skipped=36`). İkisi de Ağustos'ta salt-yazı denetimiyle
bulunmuştu; artık koşumun kendi çıktısı.

**Düzeltme 1 — değişmez sayısı 20 değil 24.** `CLAUDE.md` ve
`EXECUTION_PLAN.md` "20 preflight değişmezi" diyordu.
`PREFLIGHT_INVARIANTS.md` tablosu sayıldı: 6+5+3+4+2+4 = **24**. Belge
kilitli ve doğru; sayı yanlış aktarılmış. İki durum belgesi düzeltildi,
kilitli belgeye dokunulmadı.

**Düzeltme 2 — mock koşum asla `clean` olamaz.** `--mock-llm` ile `--lora`
birlikte verilemiyordu (Adım 5'in uzak-backend kontrolü, mock backend'i
groq'a sabitlediği için). Planın Adım 7'si bu kombinasyonu gerektiriyordu.
Çözüm: mock, backend kontrolünden muaf; karşılığında koşum
`run_quality="mock"` damgası alıyor ve **asla `clean` olamıyor**. Muafiyeti
güvenli kılan şey bu damga.

**Eşik çelişkisi (karara bağlanmadı, kayda geçiyor):** aynı büyüklük için
iki eşik var — `run_protocol_c_prime.SMOKE_SATURATION_MAX_RATE = 0.30` /
`SMOKE_PI_MIN_DISTINCT = 3` ve D-012'nin önerdiği `~0.05` / `~8`. Preflight
D-012'nin değerlerini ayrı sabit olarak aldı ve `calibrated: false` diye
işaretledi; smoke gate'e dokunulmadı. Pilot sonrası tek eşiğe indirilmeli.

**Kalan 7 değişmez** (I1.1–I1.5, I2.3, I4.1) `local_llm`'in eğitim yoluna
ölçüm eklemeyi gerektiriyor: `lora_B` abs-sum, `grad_norm` (bugün
`clip_grad_norm_`'dan alınıp atılıyor), tercih çifti listeleri, ve ilk
seed'i iki kez koşan replay orkestrasyonu. I1.4 (SNR eşiği) ve I2.3 zaten
GAP-8 karar paketine bağlı — karar verilmeden yazılmaları erken olurdu.

---

## D-018 · 2026-08-10 · Backend varsayılanı `local` — KİLİTLENDİ

**Durum:** kabul edildi (Yasin, 2026-08-10). **D-005'i kilitler**, D-015'i
karara dönüştürür.

**Karar:** Deney runner'larının varsayılan backend'i `local`. `groq`
silinmez — Protocol C provenansı için "legacy/keşif" etiketiyle korunur.

**Gerekçe (D-005'ten devralınan, hepsi kayıtlı):**
- Kanal 2 (per-agent adapter + DPO) ağırlık erişimi ister; uzak endpoint'te
  ontolojik olarak imkânsız. Merkezî iddianın test edilemediği
  konfigürasyon varsayılan olamaz.
- Ön-kayıt bütünlüğü: sahibi olunmayan bir endpoint sürümünü habersiz
  değiştirebilir; ön-kayıt geriye dönük geçersizleşir.
- **Ölçülmüş kanıt:** `075576e` — gerçek Groq ile pilot TPD rate limit'ine
  takıldı, 6 soydan 5'i tamamlandı. Uzak backend koşumu fiilen yarıda kesti.

**Zamanlama:** pre-reg henüz yazılmadı, pencere açıktı. D-005'in kendi
uyarısı gereği karar tam da bu pencerede verildi.

**Uygulama borcu (kod henüz değişmedi):** `llm_backend.py:18` ve
`graph.py:293` `LLM_BACKEND_DEFAULT = "groq"`. Bu karar onları `local`
yapmayı gerektiriyor. `install_mock_llm` groq'a `setdefault` yapıyor —
mock yolu gözden geçirilmeli. Uygulama ayrı bir adımda, testleriyle.

**Yan etki:** Adım 5'teki `--lora` + uzak backend kontrolü, varsayılan
lokal olunca fiilen hiç ateşlenmez hale gelir. Kaldırılmaz: yanlış env
set eden bir koşumu hâlâ yakalar.

---

## D-019 · 2026-08-10 · Model seçimi: Qwen-2.5-7B ölçülmeden kilitlenmez

**Durum:** yöntem kararı (Yasin, 2026-08-10). Model **henüz seçilmedi**.

**Karar:** Llama-3.1-8B → Qwen-2.5-7B geçişi, brief tavsiyesine dayanarak
yapılmaz. Önce ölçülür, sonra kilitlenir.

**Neden ölçüm şart:** Tavsiyenin provenansı sağlam
(`2026-08-08~_per-agent-lora-serving.md` §7, D-010'da güncelliği
doğrulandı) — ama `CLAUDE.md` kuralı açık: *"Brief'teki her iddia DAU kod
tabanında ayrıca doğrulanır; doğrulanmadan kilitli karar olarak
yazılmaz."* Qwen'in "keskin logit ayrımı" ve "~6.4 GiB" iddiaları bu
repoda **ölçülmedi**.

**Brief'in merkezî iddiası ve neden ciddiye alınıyor:** "Llama-3.1-8B'de
açgözlü yanıt üretimindeki platosallık DPO verisinde tıkanmaya yol
açıyor." Bu iddia projenin kendi ölçümüyle örtüşüyor — master reference
§2: *"Greedy plato (~3 unique completion / 10 event) tercih verisini
öldürüyordu."* `DIVERSITY_MIN_UNIQUE = 5` olduğu için ölçülen plato
kapının altında; geçen koşumda 15 çiftin 3'ü bu yüzden elendi.

### Ön-kayıtlı ölçüm protokolü (sayılar görülmeden yazıldı)

**Ölçülen:** `_phase1_diversity`'nin saydığı `n_unique` — üretim kodunun
kullandığı metriğin aynısı, yeni bir metrik icat edilmiyor.

**Tasarım:** 3 seed × 10 olay, her iki model için **aynı seed'ler, aynı
prompt'lar, aynı sıcaklık, greedy decoding**. Llama'nın arşiv değeri
(~3/10) referans alınmaz — aynı koşulda yeniden ölçülür.

**Kabul kriteri (önceden kilitli):** Qwen benimsenir ancak ve ancak
1. Qwen'in seed'ler üzerindeki **medyan `n_unique` ≥ DIVERSITY_MIN_UNIQUE
   (5)**, **ve**
2. Qwen'in medyanı Llama'nınkinden **kesin olarak büyük**.

**Beraberlik / belirsizlik durumunda statüko kazanır** — Llama'da kalınır.
Bu kural bilerek konuyor: kriteri sonradan gevşetmek, ölçümü tavsiyeyi
onaylatma törenine çevirir.

**Ayrıca kaydedilecek (karar kriteri değil, envanter):** her iki model
için ölçülen VRAM tepe değeri. Brief Qwen için ~6.4 GiB, Llama için
~7.2 GiB diyor; iddia doğrulanır veya düzeltilir. Bu sayı GAP-8'in bellek
isteyen ayarlarının (seq_len 512, %10 replay) bütçesini belirliyor.

**Maliyet:** ~15GB indirme + iki kısa koşum. Reddedilirse indirme boşa
gider — kabul edilen bedel, çünkü alternatifi doğrulanmamış bir iddiaya
dayanarak aleti değiştirmek.

---

## D-020 · 2026-08-10 · Quantization: NF4 + double_quant, açıkça yazılır

**Durum:** kabul edildi (Yasin, 2026-08-10). **D-016'yı kapatır.**

**Karar:** `bnb_4bit_quant_type = "nf4"` ve `bnb_4bit_use_double_quant =
True` koda **açıkça** yazılır. Kütüphane varsayılanına bırakılmaz.

**Asıl mesele fp4 değildi.** D-016'da ölçülen şey şuydu: bayrak hiç
yazılmamıştı, alet transformers'ın varsayılanına teslim edilmişti (5.14.1'de
`fp4`, `double_quant=False`). Kütüphane bir gün varsayılanı değiştirirse
alet, kimse haberdar olmadan değişir ve ön-kayıt sessizce geçersizleşir.
**Bu, D-018'de uzak backend için reddedilen riskin birebir aynısı** —
sadece kendi makinede. Karar bu yüzden "hangi tip" sorusundan önce
"açıkça yaz" ilkesini içeriyor.

**Neden NF4:**
- Brief tavsiyesi açık (`2026-08-08~_per-agent-lora-serving.md` §7 sonu):
  `double_quant=True` + `quant_type="nf4"` sabitlensin.
- Belgeler (CLAUDE.md GAP-7, master reference) zaten NF4 diyor — bu bir
  değişiklik değil, belgenin iddiasına **uyum**.
- QLoRA literatüründe NF4 normal dağılımlı ağırlıklar için 4-bit'in
  yerleşik tercihi; fp4 üzerinde bilgi-teorik gerekçesi var.
- `double_quant=True` ~0.3–0.4 GiB açar → doğrudan GAP-8 bütçesine girer.

**Kabul edilen bedel:** alet değişir. Maliyeti pratikte sıfır, çünkü
geçerli hiçbir C′ sonucu yok — `e4c026b` ve `f25b0ef` öncesi üretilenlerin
tümü zaten geçersiz sayılmıştı. Pre-reg kilitlendikten sonra aynı
değişiklik post-hoc olurdu; pencere şimdi açık.

**Uygulama borcu:** `local_llm.build_load_kwargs`. `afbb552`'de
`describe_quantization()` config'i loader'ın kendisinden okuyacak şekilde
yazılmıştı, bu yüzden alet kimliği değişikliği kendiliğinden doğru
raporlayacak — ayrıca bir yer güncellenmesi gerekmiyor.

**Belge borcu:** CLAUDE.md GAP-7 ve master reference §10b artık **doğru**
olacak; v2.4.2'de "kod fp4 idi, NF4'e geçildi (D-020)" notu düşülür —
belgeyi sessizce haklı çıkarmış gibi göstermemek için.

**D-019 ile ilişki:** model ölçümü NF4 açıkken yapılır. İki modelin VRAM
tepe değerleri de bu konfigürasyonda ölçülür; brief'in ~6.4 / ~7.2 GiB
rakamları fp4 varsayımıyla verilmişti, ölçüm onları düzeltecek.

---

## D-021 · 2026-08-10 · GAP-8 bölündü: A1+A5 kilitli, A2/A3/A4 ölçüme bağlı

**Durum:** kabul edildi (Yasin, 2026-08-10). GAP-8'i **kısmen** kapatır.

**Karar:** GAP-8'in beş maddesi tek paket olarak ele alınmaz. İkisi
bellek bütçesinden bağımsız — şimdi kilitlenir. Üçü doğrudan VRAM
harcıyor — D-019'un ölçümü gelmeden karar verilmez.

### Şimdi kilitlenen

**A1 — gradient accumulation eklenir.** Bu bir tavsiye kabulünden çok
**hata düzeltmesi**: `BATCH_SIZE=2` OOM verdiği için batching kapatılmış,
ama accumulation OOM vermez — mikro-batch 1 kalır, optimizer adımı N
mikro-adımda bir atılır. Kodda uygulanan şey gradient **checkpointing**
(bellek tekniği); tavsiye edilen şey gradient **accumulation** (gradyan
tekniği). İki teknik karıştırılmış görünüyor. Bugün `local_llm.py` her
çift için ayrı `zero_grad()` + `step()` çağırıyor ⇒ **efektif batch = 1**.
Bellek bedeli yok.

⚠ `afbb552`'nin alet kimliği bugün `gradient_accumulation_steps: 1` ve
`effective_batch_size: 1` yazıyor — olguydu, A1 uygulanınca kendiliğinden
doğru değeri raporlayacak. `N` değeri uygulama adımında belirlenir.

**A5 — mutlak PE (SNR) filtresi eklenir.** Bugün `build_pe_ranked_pairs`
yalnızca `PE_RANK_MIN_GAP = 1e-6` **farkı** arıyor; PE **büyüklüğüne**
göre filtre yok. Yani `PE=0.030` ile `PE=0.031` arasındaki fark,
`PE=0.8` ile `PE=0.2` arasındaki fark kadar meşru bir eğitim sinyali
sayılıyor. Brief (`sentetik-kognisyon` §1.2): `PE < 0.15` sinyalleri
ön-eğitilmiş ağırlık gürültüsünde kaybolur.

**Eşik ayrıca karara bağlandı: mekanizma şimdi, değer pilottan sonra.**
Filtre koda girer, başlangıç değeri brief'in `0.40`'ı olur, ama
`calibrated: false` işaretlenir ve pilotun ölçtüğü PE dağılımıyla
kilitlenir. Gerekçe: `0.40` bu repoda ölçülmedi ve
`PREFLIGHT_INVARIANTS.md` `SNR_FLOOR`'u zaten "kaynağı var, kalibre
edilmeli" diye işaretleyip I1.4'ü bu yüzden FLAG'de tutmuş. Karar o
tutumla tutarlı: **eşik önce ölçülür, sonra kilitlenir.**

⚠ Uygulama uyarısı: eşik çift **sayısını** düşürür. `MIN_PAIRS` hâlâ
kalibre edilmemiş (I1.5 FLAG). Filtre eklenirken elenen çift sayısı
loglanmalı, yoksa "az sayıda güçlü çift" ile "eğitim seti boşaldı" ayırt
edilemez.

### Ölçüme bağlananlar

**A2 (`seq_len` 256→512), A3 (1→3 epoch), A4 (%10 yüksek-somatik
replay).** Üçü de doğrudan VRAM/zaman harcıyor: `seq_len` aktivasyon
belleğini kabaca iki katına çıkarır, 3 epoch koşum süresini üçe katlar,
replay +0.3 GiB.

Kullanılabilir bütçe şu an **bilinmiyor**: D-020 (double_quant) ~0.3–0.4
GiB açıyor, D-019 Qwen'i seçerse brief'e göre ~0.8 GiB daha. İkisi de
henüz ölçülmedi. Şimdi karar vermek, miktarını bilmediğimiz bir bütçeyi
harcamak olurdu — ve fatura pilotta OOM olarak gelir.

**Sıra:** D-019 ölçümü (model + VRAM tepe değerleri, NF4 açıkken) →
gerçek boşluk → A2/A3/A4 kararı → pre-registration.

---

## D-022 · 2026-08-10 · Consolidation deney yoluna bağlanır; I5.1 pilota kadar FLAG

**Durum:** kabul edildi (Yasin, 2026-08-10). **GAP-14'ü kapatır**, ama
tarifini önce düzeltir.

### GAP-14'ün tarifi yanlıştı

`CLAUDE.md` GAP-14 şöyle diyordu: *"onu çağıran `memory_bridge.py:113`
sarmalayıcısını **hiç kimse çağırmıyor** (testler hariç)."*

**Kod bunu doğrulamıyor.** `consolidate_run` (`memory_bridge.py:102`)
`graph.py:1426`'dan çağrılıyor — `persist_run_snapshot` ve
`_print_summary`'nin bulunduğu demo/long-run bloğunda.

Doğru tespit: **consolidation ölü kod değil, yanlış yolda.** Demo yolu
çağırıyor, deney yolu çağırmıyor — çünkü C′ runner'ları `app.stream()`'i
doğrudan sürüyor ve o fonksiyona hiç uğramıyor. İki yol arasındaki sessiz
sapma.

**Ölçüm (preflight I5.1, `30c80da`):** `memory_edges is empty in every
life`. Sonuç doğruydu, sebebi yanlış yazılmıştı.

### Sanılandan geniş: unutma da kapalıymış

`run_consolidation` üç iş yapıyor, kenar yazmak yalnızca biri:
1. Solmuş izleri **siler** (`deleted_count`) — Ebbinghaus unutması burada
2. DEEP/TRAUMA izleri **güçlendirir** (`boost_strength`)
3. Eş-zamanlı baskılar arasına **kenar yazar** → PPR'ın yakıtı

Yani deney yolunda consolidation çalışmadığı için **unutma da hiç
çalışmamış.** Bunun iki sonucu var:
- Gen2'ye hangi anıların miras kalacağı olduğundan farklı ⇒ **birincil uç
  noktaya (doğum-drift, D-002) doğrudan dokunuyor.**
- **GAP-4** ("kasadan silinen anının drifti LoRA'da kalıyor olabilir") şu
  an teorik olarak bile test edilemez — hiçbir şey silinmiyor.

### Skorlamadaki fiili durum

`memory_score = 0.21·recency + 0.28·magnitude + 0.21·domain_match +
0.30·ppr` → PPR boş grafta sabit döndüğü için fiilen
`0.21·recency + 0.28·magnitude + 0.51·domain_match`.
`PPR_WEIGHT_IN_SCORE = 0.30`, domain_match'i gizlice büyüten bir sabit.

### Karar

**1. `consolidate_run` deney yolunda da yaşam sonunda çağrılır.** Bu bir
özellik ekleme değil, **tasarlanmış davranışın geri gelmesi**:
fonksiyonun docstring'i "end-of-life sleep consolidation" diyor ve demo
yolu onu doğru çağırıyor.

**2. I5.1 pilota kadar FLAG kalır.** Bağladıktan sonra kenarların
gerçekten oluştuğunu ölçmeden ABORT'a yükseltmek, doğrulanmamış bir
düzeltmeye koşum öldürme yetkisi vermek olurdu. Pilot kenarları
doğrularsa ABORT'a yükselir.

**3. Miras etkisi pilotta ölçülür, pre-reg'de kilitlenir.** Pilot
`deleted_count` · `strengthened_count` · `edges_created` sayılarını **ve
transfer aday sayısındaki değişimi** raporlar. Değişiklik gen2'ye giden
malzemeyi değiştiriyor ve etkisi ölçülmedi; D-019 ve D-021'deki tutumun
aynısı — bağla, ama ölçmeden kilitleme.

**Uygulama notu:** çağrı noktası, vault'un hâlâ açık olduğu yer olmalı.
`run_lineage` store'u `finally`'de kapatıyor; consolidation ondan önce,
gen1 yaşamının sonunda çalışmalı. Hangi fazın sonunda çağrılacağı
(phase-1 sonrası mı, phase-2 sonrası mı, ikisinde de mi) uygulama
adımında karara bağlanır — gen1 iki yaşam sürüyor ve "yaşam sonu"nun
karşılığı belirsiz. Bu belirsizlik burada açıkça bırakılıyor, sessizce
seçilmiyor.

**Belge borcu:** master reference §6 ve §19 ADIM 4'ü uygulanmış entegrasyon
olarak sunuyor. v2.4.2'de düzeltilir: "atıldı, D-022 ile bağlandı".

---

## D-023 · 2026-08-10 · Tanınmayan backend değeri sessizce varsayılana düşmez

**Durum:** kabul edildi (Yasin, 2026-08-10), U1 ile aynı oturumda uygulandı
(`7adb01d`). D-018'in **yan ürünü** — D-018 bu davranışı yazmıyordu.

**Karar:** `_resolve_llm_backend` üç dilim tanır:
1. env hiç set edilmemiş **veya** boş/whitespace → varsayılan (`local`).
   Emsal: `_resolve_llm_temperature` (`ab30f9c`, GAP-15) boş değeri "set
   edilmemiş" sayıyor; aynı okuma.
2. `groq` veya `local` (case/boşluk toleranslı) → o değer.
3. Başka her şey → `ValueError`, mesajda geçerli değerler listeli.

**Neden şimdi — ölçülen senaryo:** Değişiklikten önce fonksiyon
tanınmayan **her** değer için varsayılanı döndürüyordu:

```python
raw = os.environ.get(LLM_BACKEND_ENV, LLM_BACKEND_DEFAULT).strip().lower()
if raw == LLM_BACKEND_LOCAL: return LLM_BACKEND_LOCAL
return LLM_BACKEND_DEFAULT      # ← tanınmayan her şey buraya
```

Varsayılan `groq` iken bu **zararsızdı**: `DAU_LLM_BACKEND=grok` yazım
hatası sessizce `groq`'a düşüyordu, yani kullanıcının istediği şeye. U1
varsayılanı `local` yapınca aynı satır zararlı hale geldi: aynı yazım
hatası artık sessizce **`local`** döndürüyor, 8B model yükleniyor ve
sonuç JSON'una `tool_identity.backend = "local"` yazılıyor — kullanıcı
uzak backend istediğini sanırken lokal koşuyor ve **koşum kendini doğru
raporluyor**. Yanlış aletle üretilmiş bir sonucun kendini temiz göstermesi,
tam olarak GAP-1'in ve `075576e`'in dersi.

**Yani karar bir tercih değil, D-018'in açtığı deliğin kapatılması.**
Varsayılanı çevirmek, önceden zararsız olan bir sessiz fallback'i zararlı
hale getirdi; F.0 madde 5 ("sessiz fallback yasak") bunu zaten yasaklıyordu.

**Neden `ValueError`, `SystemExit` değil:** `_resolve_llm_backend` karar
anında (`graph.py:921`, her olayda) çağrılıyor, runner girişinde değil.
`tool_identity.resolve_lora_choice` gibi giriş kapıları `SystemExit`
kullanır; kütüphane derinliğindeki bir çözümleyici `ValueError` fırlatır ve
çağıran katman ne yapacağına karar verir. İkisi de sessiz değil.

**Reddedilen alternatif — `[WARN]` basıp `local`'a düşmek:** koşum devam
ederdi ve uyarı, saatler sonra bakılan bir logda kalırdı. Alet kimliği
yanlış kalırdı; ölçüm zaten yapılmış olurdu.

**Kapsam dışı bırakılan (bilinçli):** `llm_backend.py`'deki
`LLM_BACKEND_*` sabitleri `graph.py`'dekilerin **kopyası** ve modülün
`resolve_backend_name`/`get_backend` fonksiyonlarının **hiçbir çağıranı
yok** — `graph.py:929` yalnızca `LocalBackend` sınıfını import ediyor,
backend seçimini kendi yapıyor. Yasak #4 ("her sabit tek yerde") burada
zaten ihlal. Tekilleştirme U1'e sokulmadı: `graph.py` ↔ `llm_backend.py`
import yönünü değiştiriyor ve U1'in kapsamı değil. Yerine
`test_llm_backend_module_mirrors_graph_constants` iki kopyayı bağlıyor —
sessizce ayrışamazlar. Tekilleştirme ayrı, mekanik bir iş olarak duruyor.

**Kanıt (mutasyon kontrolü, 5 mutasyon 5 kırılma):** varsayılanı `groq`'a
geri al → 6 test kırılır · sessiz fallback'i geri koy → 4 test kırılır ·
boş değeri "set edilmiş" say → 5 test kırılır · mock'un `setdefault`'unu
kaldır → 1 test kırılır · `setdefault`'u koşulsuz `set` yap → 1 test kırılır.
Tam suite: 255 → **270 passed**.

**Ek not (2026-08-10, aynı gün):** D-023'ün "kapsam dışı bırakılan"
maddesi kapandı — tekilleştirme `9ce5269` ile yapıldı (Cursor, mekanik,
davranış değişmedi). Sabitler, `LLM_BACKEND_UNKNOWN_MESSAGE` ve
çözümleyici gövdesi `llm_backend.py`'de tek yerde; `graph._resolve_llm_backend`
ince alias olarak korundu (`graph.agent_node` ve
`tool_identity.resolve_backend` onu adıyla çağırıyor). Bekçi testi eşitlik
yerine **kimlik** iddia ediyor: CPython kısa string'leri intern ettiği için
`LLM_BACKEND_DEFAULT` üzerinden `is` testi iki ayrı tanımla da geçerdi ve
hiçbir şey kanıtlamazdı; tuple intern edilmiyor. Mutasyonla doğrulandı —
`graph.py`'ye aynı değerli bir kopya geri kondu, test kırıldı.
`get_backend`'in hâlâ çağıranı yok; silinmedi.

---

## D-024 · 2026-08-10 · U2 uygulandı; planın iki maddesi yanlıştı

**Durum:** D-020'nin uygulama kaydı (`70edeba`). Yeni bir karar değil —
D-020 kilitliydi; bu kayıt **uygulama sırasında planın yanlış çıkan iki
maddesini** ve kalan riski tutuyor.

**Ölçülen:** `transformers 5.14.1` → `BitsAndBytesConfig(load_in_4bit=True)`
varsayılanı `quant_type='fp4'`, `double_quant=False`. Yani alet bugüne
kadar **fp4, double-quant kapalı** koştu. D-020'nin "bayrak hiç yazılmamıştı"
tespiti doğrulandı.

### Planın 1. hatası — "mevcut testin değeri güncellenir"

§F U2 satırı, `afbb552`'de yazılan
`test_tool_identity_quantization_matches_loader`'ın değerinin
güncelleneceğini söylüyordu. **Yanlış.** O test rapor ile loader'ın
**tutarlılığını** ölçüyor:

```python
assert quantization["quant_type"] == str(config.bnb_4bit_quant_type)
```

İki taraf da aynı `build_load_kwargs()`'tan geldiği için, bayraklar
silinip fp4 varsayılanı geri gelse bile bu test **geçer**. Mutasyonla
doğrulandı: bayraklar kaldırıldığında o test yeşil kaldı, yalnızca yeni
`test_quantization_flags_are_pinned_not_inherited` kırıldı.

**Karar:** eski test doğru şeyi koruyor (iki inşa birbirinden ayrışmasın),
dokunulmadı. Değeri sabitleyen **ayrı** bir test eklendi. İkisi farklı
şeyleri bekliyor ve ikisi de gerekli.

### Planın 2. hatası — dur-kontrolü ateşlenemez

§F, dur-kontrol olarak *"`--no-lora --mock-llm` koşumunda JSON
`quantization.quant_type: "nf4"` yazıyor mu"* diyordu. `tool_identity.
_quantization` backend `local` değilse
`{"available": false, "reason": "remote backend — not applicable"}`
döndürüyor; `--mock-llm` koşumu `install_mock_llm`'in `setdefault`'u
yüzünden backend'i `groq`'a sabitliyor. Mock JSON'unda `quant_type`
**hiç yazmıyor** — kontrol hiçbir zaman ateşlenemezdi.

**Yerine:** `describe_quantization()` model **yüklemiyor**, yalnızca
config kuruyor; GPU'ya dokunmadan birim testinde doğrulanıyor.

### Kalan risk — açıkça kaydediliyor

Birim testi config'in **ne olduğunu** kanıtlıyor, 8B modelin o config'le
**yüklendiğini** değil. NF4 + double_quant bu repoda ilk kez **U3'te**
gerçek yükleme görecek. Yükleme başarısız olursa orada çıkar.

**Bunun "yeni run atmamak sorun çıkarır mı" sorusuna cevabı:** hayır,
çünkü (1) geçerli hiçbir C′ sonucu yok — `e4c026b` ve `f25b0ef`
öncesi üretilenlerin tümü zaten geçersiz sayılmıştı, yani "yeniden
koşulacak" bir sonuç yok; (2) U3 zaten NF4 açıkken ölçmek üzere
tasarlanmış, ilk gerçek koşum o. **Ama bir sonucu var:**
`dau_runs/vram_spike_results.json`'daki **6386 MiB** ölçümü fp4 /
double-quant-kapalı konfigürasyonda alınmıştı — U7'nin bellek bütçesi
için **artık geçerli bir sayı değil**, U3'ün taze ölçümü beklenmeli.

---

## D-025 · 2026-08-10 · D-019 düzeltmesi: iki kol da **instruction-tuned** olmalı

**Durum:** ön-kayıt düzeltmesi (Yasin onayı, 2026-08-10). **Hiçbir sayı
görülmeden, indirme yapılmadan önce yazıldı** — sıra bilerek böyle: kayıt
önce, indirme sonra, ölçüm en son.

**Değişen:** D-019'un ölçüm kollarının tanımı. İki kol da
instruction-tuned checkpoint olacak:
`meta-llama/Meta-Llama-3.1-8B-Instruct` **vs** `Qwen/Qwen2.5-7B-Instruct`.

**DEĞİŞMEYEN — D-019'un kabul kriteri aynen kilitli kalır:**
> Qwen benimsenir ancak ve ancak (1) medyan `n_unique ≥
> DIVERSITY_MIN_UNIQUE (5)` **ve** (2) medyanı Llama'nınkinden **kesin
> olarak büyük**. Beraberlik/belirsizlikte **statüko kazanır — Llama'da
> kalınır.**

Bu kayıt **kolun tanımını** düzeltiyor, **kriteri değil**. Kriteri
gevşetmek D-019'da açıkça yasaklanmıştı; o yasak yürürlükte.

### Neden — üç gerekçe, en ağırı sonda

**1. Provenans.** Brief `2026-08-08~_per-agent-lora-serving.md` §7 iki
ayrı yerde **`Qwen-2.5-7B-Instruct`** yazıyor (tavsiye tablosu + kapanış
paragrafı). D-019'daki "Qwen-2.5-7B" onun kısaltmasıydı. Cache'de duran
`Qwen/Qwen2.5-7B` ise **base** sürüm.

**2. Asimetri.** `LOCAL_MODEL_NAME` instruction-tuned bir checkpoint.
Instruct'ı base'e karşı ölçmek model ailesini değil, **instruction
tuning'in kendisini** ölçer. D-019'un "aynı seed, aynı prompt, aynı
sıcaklık" simetrisi bu ekseni hiç kapsamıyordu.

**3. Metrik ters dönebilir — ve sessizce.** Ölçülen şey
`_phase1_diversity`'nin saydığı `n_unique`: **benzersiz completion
string sayısı** (`run_protocol_c_prime.py:386`, boş ve
`COMPLETION_FALLBACK="continue"` olanlar eleniyor). Instruction tuning
görmemiş bir model, karar vermek yerine prompt'u sürdürür/yankılar; her
olayın prompt'u farklı olduğu için **çıktılar da farklı olur ve
`n_unique` yükselir — yanlış sebeple.** Yani base Qwen bu metrikte
Llama'yı yenebilir, üstelik hiçbir işe yaramazken.

**Ve bu sessiz olurdu:** `Qwen/Qwen2.5-7B` base sürümü **chat_template
taşıyor** (kontrol edildi). `_build_prompt` (`local_llm.py:412`) template
bulduğu için `used_chat_template=True` döndürür, hiçbir uyarı çıkmaz.
Ölçüm temiz görünür ve yanlış olur. Bu, projenin tekrar tekrar
yakaladığı hata sınıfının aynısı (GAP-1, D-018, D-020).

### Ön-kayda eklenen iki madde (D-019'da belirsizdi)

**a. "Aynı prompt" ne demek — açıkça:** aynı **mesaj listesi**
(system+user), her modele **kendi chat template'i** ile uygulanır
(`_build_prompt`). Ortak düz-metin formatı **kullanılmaz** — o, her iki
modeli de kendi eğitildiği formatın dışında çalıştırırdı.

**b. Template yoksa kol geçersizdir.** `_build_prompt` template
bulamazsa sessizce düz birleştirmeye düşüyor. U3'te bu **kabul
edilmez**: her iki kol için `used_chat_template` **True** olmalı, aksi
halde ölçüm geçersiz sayılır ve rapor edilir. Sessiz fallback yasağının
bu ölçüme uygulanması.

**c. Greedy decoding** — `local_llm` varsayılanı zaten greedy
(`LLM_DO_SAMPLE_DEFAULT="0"`); ölçümde `DAU_LLM_DO_SAMPLE` set edilmez.

### Bedel

`Qwen/Qwen2.5-7B-Instruct` ≈ 15.2 GB indirme. Disk temizliği sonrası
39 GB boş — sığıyor. Cache'deki base Qwen (15 GB) ölçüm için işe
yaramaz hale gelir; Instruct doğrulandıktan sonra silinebilir (ayrı,
mekanik iş).

**D-019 iptal edilmiyor** — protokolü, metriği, kabul kriteri ve
"statüko kazanır" kuralı aynen yürürlükte. Bu kayıt yalnızca hangi iki
checkpoint'in karşılaştırılacağını netleştiriyor.

---

## D-026 · 2026-08-10 · U3 ölçüldü: **Llama'da kalınıyor**

**Durum:** D-019'un ön-kayıtlı kriteri ölçüme uygulandı. Karar kriterden
mekanik olarak çıktı; yorum katılmadı. Kollar D-025 uyarınca iki
instruction-tuned checkpoint.

### Ham sayılar

Harness: `dau/diagnostics/measure_model_diversity.py` (`13e3b9e`),
3 seed (2001/2002/2003) × 10 olay, greedy, nf4 + double_quant, her model
kendi process'inde. Ölçülen: `_phase1_diversity`'nin `n_unique`'i —
üretim metriğinin aynısı.

| | Llama-3.1-8B-Instruct | Qwen2.5-7B-Instruct |
|---|---|---|
| `n_unique` (2001/2002/2003) | 7 · 9 · 10 | 4 · 4 · 4 |
| **medyan** | **9.0** | **4.0** |
| `pe_gap_max` | 0.6526 · 0.7090 · 0.6153 | 0.6731 · 0.6731 · 0.6731 |
| VRAM tepe (üretim) | 5804.5 MiB | 5662.8 MiB |
| chat template | ✅ | ✅ |

Ham JSON: `dau_runs/u3_model_diversity_meta-llama__Meta-Llama-3.1-8B-Instruct.json`
ve `dau_runs/u3_model_diversity_Qwen__Qwen2.5-7B-Instruct.json`.

### Kriterin uygulanması (D-019, değiştirilmedi)

1. Qwen medyanı ≥ `DIVERSITY_MIN_UNIQUE` (5)? → **HAYIR** (4.0)
2. Qwen medyanı Llama'nınkinden kesin büyük? → **HAYIR** (4 < 9)

Her iki şart da başarısız — beraberlik bile değil. **`LOCAL_MODEL_NAME`
`meta-llama/Meta-Llama-3.1-8B-Instruct` olarak kalır.** Kod değişmiyor.

### Brief'in doğrulanmayan iki iddiası

- **"Keskin logit ayrımı / şiddetle önerilir"** (§7): bu kod tabanında
  **üretilmedi**. Qwen kapının altında kaldı.
- **VRAM ~6.4 vs ~7.2 GiB (≈800 MiB fark)**: ölçülen fark **142 MiB**
  (5662.8 vs 5804.5). Brief'in rakamları fp4 varsayımıyla verilmişti;
  nf4 + double_quant altında iki model neredeyse aynı yeri kaplıyor.

D-019'un "ölçmeden kilitleme" kuralı işini yaptı. Provenansı sağlam bir
tavsiye, bu repoda tekrar üretilemedi.

### Anomali: Qwen seed'e duyarsız

Qwen'in `pe_gap_max`'i üç seed'de de **dört ondalık basamağa kadar aynı**
(0.6731) ve `n_unique` sabit 4. Llama aynı harness'ta, aynı seed'lerle
değişkenlik gösteriyor. **Bu, harness'ın seed'leri doğru uyguladığını
kanıtlıyor** — aksi halde Llama da sabit çıkardı. Anlamı: Qwen niş
değişse de aynı dört cevabı üretiyor. Karar zaten kriterden çıkmıştı;
bu bulgu onu zayıflatmıyor, güçlendiriyor.

### Keşifsel ek ölçüm — **ön-kayıtlı DEĞİL**

D-019'un kriteri buna uygulanmaz; yalnızca sampling reçetesini
bilgilendirir. Tek process, tek model yükü (Llama), 50 olay/seed —
gerçek C′ gen1 kolu uzunluğu. U3 harness'ına dokunulmadı, scratchpad'den
çağrıldı. Ham JSON: `dau_runs/exploratory_greedy_vs_sampled_50events.json`.

| | `n_unique` (2001/2002/2003) | medyan | gate'lenen |
|---|---|---|---|
| greedy | 29 · 22 · 27 | **27** | 0 |
| sampled (T=0.2) | 34 · 44 · 48 | **44** | 0 |

**Master reference §2'nin gerekçesi çürüdü.** Belge sampling'i şu sebeple
istiyor: *"Greedy plato (~3 unique/10 event) tercih verisini
öldürüyordu."* Greedy 50 olayda **27** veriyor, kapı 5. "Greedy tercih
verisini öldürüyor" iddiası artık yanlış.

**Ama sampling boşa çalışmıyor:** %63 daha çok benzersiz completion.

**Sampling kararı AÇIK bırakıldı** — Yasin verecek (D-007). Kayda geçen
argümanlar:
- *Greedy lehine:* gerekçe çürüdü; determinizm ek mekanizmaya
  (`fb1b125` prompt-keyed tohumlama) bağımlı olmadan gelir; ve asıl
  darboğaz çeşitlilik değil **eleme** — 08-09 pilotunda 746 aday çiftten
  1'i eğitime girmiş (`n_pairs_rejected: 745`), kabul oranı binde 1.3.
  Çeşitliliği ikiye katlamak 1'i 2 yapar. Doğru müdahale U5 (A5 filtresi).
  GAP-9 (d≈0.04) altında gürültü kaynağı azaltmak değerli.
- *Sampled lehine:* az çift = zayıf tedavi = küçük etki; o da gücü düşürür.

### YENİ GAP — üretim çeşitliliği açıklanamayan biçimde değişti

08-09 pilotu **aynı 50 olayda** `n_unique` 7 · 4 · 8 vermiş (bir seed
gate'lenmiş). Bugün greedy **29 · 22 · 27**. Aynı protokol yolu, **3–4 kat
fark.** Sebep izole edilmedi. Adaylar: GAP-11/12/13/15 düzeltmeleri,
GAP-1 kapısı, fp4→nf4 (U2). Arşivden ayırt edilemiyor.

**Ayrıca 08-09 pilotu bu tartışmada delil olarak kullanılamıyor:**
JSON'unda sampling durumu **kayıtlı değil**, çünkü koşum `tool_identity`
bloğundan önce. Alet kimliği tam da bu boşluk için yazılmıştı; yokluğu
bugün bize bir cevap kaybettirdi.

**Bu GAP pre-reg'den önce kapatılmalı.** Aletin davranışı bu ölçekte
oynuyorsa, ön-kayıt neyi kilitlediğini bilmiyor demektir.

### Düzeltme — VRAM sayısı U7 için kullanılamaz

Oturum içinde "~2000 MiB boşluk var" denmişti; **erken bir çıkarımdı.**
Bugün ölçülen 5804 MiB **yalnızca üretim** sırasında alındı. Eğitim
gradyan, optimizer durumu ve aktivasyon ister. Eski 6386 MiB eğitimi
kapsıyordu (`micro_train_ran: true`) ama **fp4**'teydi. İki sayı farklı
işi, farklı konfigürasyonda ölçüyor.

**nf4 + double_quant altında eğitim tepe değeri henüz yok.** U7 (A2/A3/A4)
bu ölçüm yapılmadan karara bağlanamaz.

---

## D-027 · 2026-08-10 · U7: A2 kabul (256→512) · A3 ertelendi · A4 yanlış yerde tartışılıyordu

**Durum:** kabul edildi (Yasin, 2026-08-10). D-021'in ölçüme bağlanan
yarısı. `constraints.DPO_MAX_SEQUENCE_TOKENS` **256 → 512**.

### Ölçüm: eğitim VRAM tepe değeri, nf4 + double_quant

Eksik olan sayı buydu — D-026 önceki "~2000 MiB boşluk" çıkarımını geri
çekmişti, çünkü 5804 MiB **üretim** sırasında ölçülmüştü ve eski 6386 MiB
eğitimi kapsıyordu ama **fp4**'teydi. Şimdi ikisi de aynı konfigürasyonda:

Llama-3.1-8B-Instruct, nf4 + double_quant, `DPO_BATCH_SIZE=1`,
`DPO_EPOCHS=1`, 6 çift, her konfigürasyon kendi process'inde.
Ham JSON: `dau_runs/vram_train_peak_nf4.json`.

| | seq=256 (mevcut) | seq=512 (A2) |
|---|---|---|
| Yükleme sonrası yerleşik | 5456.1 MiB | 5456.1 MiB |
| **Eğitim tepe (allocated)** | **6139.5 MiB** | **6618.6 MiB** |
| Eğitim tepe (reserved) | 6378.0 MiB | 6848.0 MiB |
| Kart toplamı | 7807.6 MiB | 7807.6 MiB |
| Kalan boşluk | 1668.1 MiB | **1189.0 MiB** |

İkisi de `trained: true`. **A2'nin faturası 479.1 MiB.** D-021 "aktivasyon
belleğini ~2×" diyordu; gerçek maliyet çok daha ucuz ve rahat sığıyor.

### Ama A2'nin gerekçesi bellek değil — eğitim/çıkarım uyumsuzluğu

`_encode_pair_side` (`local_llm.py:568`) sınır aşılınca **prompt'un başını**
kesiyor ("Keep the completion intact; the prompt head is the expendable
part"). Prompt'un başında chat template başlığı ve `SYSTEM_PROMPT` (78
token) var — yani kesilen şey **talimatın kendisi**.

Gerçek DAU prompt'u ölçüldü (Llama tokenizer, `_initial_state(2001)` view'ı
+ drift uyarısı + `_format_memory_context`):

| Bellekten çekilen anı | Toplam token | 256 sınırı |
|---|---|---|
| 0 | 246 | sığıyor |
| **1** | **274** | 18 token aşıyor |
| 2 | 290 | 34 token aşıyor |
| **3** (`MAX_RETRIEVED_MEMORIES`) | **306** | **50 token aşıyor** |

`MEMORY_ENABLED = True` ve `retrieve_relevant` her kararda çağrılıyor, yani
**tek bir anı çekildiği anda sınır aşılıyor.**

**Sonuç:** `generate_completion` kesme yapmıyor — ajan karar verirken tam
prompt'u görüyor. DPO ise sakatlanmış prompt üzerinden öğreniyor. Bu,
projenin bir kez daha yakaladığı hata sınıfının aynısı: `d18ffe9` "Train
DPO in the same chat format inference uses" aynı uyumsuzluğu **format**
tarafında düzeltmişti; bu sefer **uzunluk** tarafında.

**Bu, bugüne kadar yapılmış her DPO eğitimini etkiliyor.** Yeni bir
geçersizlik ilanı gerekmiyor: `e4c026b`/`f25b0ef` öncesi sonuçlar zaten
geçersizdi ve sonrasında geçerli sayılan bir C′ sonucu üretilmedi.

512, en kötü durumda (306 token) rahat yetiyor. Aşılması için prompt'un
%67 büyümesi gerekir.

### A3 (`DPO_EPOCHS` 1→3) — **ertelendi, reddedilmedi**

Bellek maliyeti yok (batch=1, epoch tepe değeri değiştirmez); maliyeti
süre 3×. Ertelenme sebebi bütçe değil **sıra**: 08-09 pilotunda filtre 746
aday çiftten 1'ini geçirdi (`n_pairs_rejected: 745`). Tek örnek üzerinde 3
tur dönmek öğrenmek değil, o örneği ezberlemektir. A3'ün değeri U5'in (A5
mutlak PE / SNR filtresi) çift darboğazını açmasına bağlı — **U5'ten sonra
karara bağlanacak.**

### A4 (%10 somatik replay) — bütçe kalemi değilmiş

`DPO_BATCH_SIZE = 1` olduğu için replay daha büyük adım değil **daha çok
adım** demek: tepe değer değişmez, süre uzar. D-021'in "~+0.3 GiB"
tahmini bu nedenle yanlış görünüyor. **Doğrudan ölçülmedi**, batch=1'den
çıkarıldı — bu kayıt onu ölçülmüş gibi sunmuyor.

Yani A4 bir VRAM sorusu değil: ajanın **neyle** eğitildiğine dair deney
tasarımı kararı (yüksek `F_agent` anılarının %10 oranında geri
karıştırılması), ve aksiyoma değiyor. **Bu kayıtta karara bağlanmıyor**;
kendi başına, bellek bütçesine sıkıştırılmadan tartışılacak.

### Kabul edilen bedel

`constraints.py` eşik değeri değişiyor — CLAUDE.md bunu yalnızca D-kaydıyla
mümkün kılıyor, kayıt bu. Ön-kayıt henüz yazılmadı, pencere açık; pre-reg
kilitlendikten sonra aynı değişiklik post-hoc olurdu.

---

## D-028 · 2026-08-10 · U4 uygulandı; `N = 4` **kalibre edilmemiş**

**Durum:** D-021/A1'in uygulama kaydı (`9718737`). Mekanizma D-021'de
kilitliydi; bu kayıt **yeni sabitin değerini** ve uygulama sırasında
çıkanları tutar.

**Yeni sabit:** `constraints.DPO_GRADIENT_ACCUMULATION_STEPS = 4`.
Mevcut bir eşiğin değişmesi değil, yeni bir sabit — plan (§F U4) değerin
bu adımda karara bağlanmasını istiyordu.

**Değer neden kalibre edilmemiş sayılıyor:** Bugün ölçüldü ki filtre
yaşam başına **1–2 çift** geçiriyor (D-026, D-027). `len(pairs) = 1` iken
herhangi bir `N` tek bir kısmi gruba düşer — yani U4'ün bugün ölçülebilir
etkisi **yok**. `N`'in değeri ancak U5 (A5, SNR filtresi) çift
darboğazını açtıktan sonra kalibre edilebilir. `4` muhafazakâr bir
varsayılan, ölçülmüş bir değer değil — A5'in `0.40` eşiğiyle aynı statüde.

**A3 ile aynı bağımlılık, farklı sonuç:** A3 (D-027) bu yüzden
**ertelendi**; A1 ertelenmedi çünkü D-021'de **kilitli** ve bellek maliyeti
yok. Yani U4 bugün bir davranış iyileştirmesi değil, **U5 sonrası anlam
kazanacak bir doğruluk düzeltmesi**. Bu kayıt onu iyileştirme gibi
sunmuyor.

### Uygulama sırasında karara bağlananlar

**1. Kısmi son grup boyutu hesaplanır, varsayılmaz.** `group_size =
min(N, micro_batches - group_index * N)`. Bu savunmacı bir süs değil:
1–2 çiftle **tek çalışan grup kısa gruptur**. Düşen bir tail, "eğitim hiç
olmadı ama koşum başarılı raporladı" demek olurdu. Artakalan `pending`
varsa `RuntimeError` — sessiz kayıp yasağı.

**2. İki metrik anlamını korudu, bilerek.** `dpo_loss` hâlâ çift başına
ortalama (bölen yalnızca `backward()`'a giden tensöre uygulanıyor);
`dpo_steps` hâlâ mikro-adım sayıyor. Optimizer adımı **yeni alan** olarak
eklendi (`dpo_optimizer_steps`) — mevcut bir alanın anlamını sessizce
değiştirmek, bu projenin tam olarak kaçındığı şey.

**3. `tool_identity.GRADIENT_ACCUMULATION_STEPS` literal `1`'di.**
`afbb552` onu **olgu** olarak yazmıştı ve o gün doğruydu. U4 olguyu
değiştirdi; sabit artık `constraints`'ten okunuyor. Aynı sınıf tuzak
U3a'da (`model_id`) ve U2'de (quantization) da çıkmıştı: **rapor, aleti
takip etmeli, aleti tekrar etmemeli.**

**4. Kasıtlı test kırılması.** `test_tool_identity_has_no_undeterminable_
field` içinde `effective_batch_size == 1` sabitlenmişti. Faz kuralı gereği
aynı commit'te güncellendi — ama literal yerine
`DPO_BATCH_SIZE * DPO_GRADIENT_ACCUMULATION_STEPS`'e bağlandı. Literal
bir değer, alanın var oluş amacını (raporun aleti izlemesi) test edemez.

**Kanıt:** 3 mutasyon, 3 kırılma — her mikro-adımda step · kısmi tail'i
düşür · tool_identity literalini geri koy. Tam suite **289 passed**.

---

## D-029 · 2026-08-10 · `DPO_LEARNING_RATE` 5e-5 → **1e-6**

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `10697f1`.
`constraints.py` eşik değeri değişikliği — CLAUDE.md bunu yalnızca
D-kaydıyla mümkün kılıyor.

**Tetikleyen:** DR brief'i (`2026-08-10_low-data-dpo-pair-selection.md`, F1)
5e-5'in az veride **unlikelihood push** yarattığını, DPO başarılarının
**5e-7 – 1e-6** kullandığını söyledi. Brief iddia, kanıt değil — ölçüldü.

### Ölçüm

Gerçek 10 olaylık koşumdan toplanan **9 tercih çifti** (NLI kapalı, bkz.
tasarım notu), dört öğrenme oranı **aynı çiftler** üzerinde, her biri kendi
process'inde. Eğitim öncesi adapter sıfır başlatıldığı için `π_θ = π_ref`.
Ham JSON: `dau_runs/lr_probe_results.json` + `dau_runs/lr_probe_pairs.json`.

| lr | Δlogp(chosen) | Δlogp(rejected) | Δmarj | chosen düşen | nötr perplexity oranı |
|---|---|---|---|---|---|
| **5e-5** (eski) | **−0.1230** | **−4.3715** | +4.2484 | 5/9 | ×0.998 |
| 1e-5 | −0.0492 | −0.4213 | +0.3721 | 5/9 | ×0.992 |
| **1e-6** (yeni) | **+0.0846** | −0.1435 | +0.2281 | **2/9** | ×1.003 |
| 5e-7 | +0.1325 | −0.0375 | +0.1700 | 4/9 | ×0.998 |

### Brief'in yarısı doğrulandı

✅ **Unlikelihood push — doğrulandı, çarpıcı biçimde.** 5e-5'te seçilen
cevabın log-olasılığı **düşüyor** (−0.12), reddedilen **çöküyor** (−4.37).
Marjdaki +4.25'in **tamamı bastırmadan** geliyor; reddedilen taraf
seçilenin **35 katı** hareket ediyor, ters yönde. 1e-6'da seçilen yükseliyor.

❌ **Genel dil bozulması — gözlenmedi.** Nötr metin perplexity'si her lr'de
sabit (0.992–1.003), 5e-5 dahil. **Bu "brief yanıldı" demek değil:** ölçüm
**tek bir** mikro-eğitimdi; brief'in iddiası tekrarlı eğitim hakkında
olabilir ve DAU tam olarak öyle çalışıyor (D-014, N nesil). Birikimli etki
**dışlanmadı**, ölçülmedi.

### Neden bu DAU için ayrıca önemli

Bastırmayla öğrenen ajan *"düşük PE'li şeyi tercih et"* değil *"yüksek PE'li
şeyi asla söyleme"* öğreniyor. Kanal 2'den gen2'ye aktarılan iz bir tercih
değil bir **bastırma deseni** olur. Aksiyom "yaşamın izi aktarılabilir
olmalı" diyor; hangi izin aktarıldığı bu ayrımla değişiyor. N nesil boyunca
birikir.

### Değer neden ölçümden seçilmedi

1e-6, brief'in verdiği bandın **üst ucu** — literatür değeri. Kendi
sweep'imizden seçmedim: 1 seed ve 9 çift, 1e-6 ile 5e-7 arasında ayrım
yapacak güçte değil (1e-6 tutarlılıkta iyi — 9 çiftin 2'sinde chosen düştü;
5e-7 ortalamada iyi ama 4'ünde düştü). Ölçüm **yönü** kanıtlıyor, **değeri**
değil. Değeri ölçümden seçmek post-hoc tuning olurdu.

`DPO_LEARNING_RATE_MIN/MAX = 5e-7 / 1e-6` bandı da kaydedildi ve test
literal değil **bandı** iddia ediyor — gerekçesiyle birlikte, ki ileride
değiştiren biri bir diff değil bir açıklama görsün.

### Ölçümün sınırları (kayda geçiyor)

1 seed · 9 çift · 1 mikro-eğitim · tek nötr paragraf · **ön-kayıtlı değil**.
NLI çiftleri toplarken **bilerek kapatıldı**: açık olsaydı 1–2 çift gelirdi
ve dört kol öğrenme oranından değil şanstan ayrışırdı. `build_pe_ranked_pairs`
kendi kuralını (olay başına en güçlü marj) uygulamaya devam etti.

**U5 ile ilişki:** sıra bilerek böyle kuruldu. 5e-5'te kalıp U5 ile daha çok
çift eklemek, daha çok öğrenme değil **daha çok bastırma** üretirdi.

---

## D-030 · 2026-08-10 · A5 yeniden tanımlandı: mutlak PE değil **marj** eşiği

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `5ad70a8`.
**D-021/A5'in mekanizmasını korur, neyi filtrelediğini değiştirir.**
A5'te mekanizma kilitliydi, eşik kilitli değildi — bu kayıt eşiğin hem
değerini hem **anlamını** belirliyor.

### Neden planın yazdığı gibi uygulanmadı

§F U5 ve D-021/A5 `SNR_FLOOR = 0.40`'ı **mutlak PE eşiği** olarak tarif
ediyordu. Gerçek dağılım ölçüldü (9 çift, 10 olay, greedy;
`dau_runs/lr_probe_pairs.json`):

```
pe_chosen  : min 0.220  medyan 0.376  max 0.451
pe_rejected: 0.8728 — dokuz çiftin hepsinde aynı
marj       : min 0.422  medyan 0.497  max 0.653
```

Üç okumanın üçü de başarısız:

| Okuma | Sonuç |
|---|---|
| `chosen ≥ 0.40` | **3/9 kalır** — ve elenen 6'sı **en iyileri** |
| `rejected ≥ 0.40` | 9/9 — hiç ateşlenmez |
| "her ikisi de < 0.40 ise ele" | 9/9 — hiç ateşlenmez |

**Birinci okuma tanım gereği ters:** `chosen` düşük-PE tarafıdır (iyi
sonuç). Ondan yüksek PE istemek "iyi sonucun kötü olmasını" şart koşmaktır.

### Karar

Eşik **marja** taşındı: `SNR_MARGIN_FLOOR`. A5'in gerekçesi
(*"`PE=0.030` vs `0.031` farkı, `0.8` vs `0.2` kadar meşru sayılıyor"*)
zaten marj hakkındaydı; `PE_RANK_MIN_GAP = 1e-6` onu fiilen kapısız
bırakıyordu. DR brief'i de aynı yeri işaret etmişti (F7: *"A5/U5'in
SNR_FLOOR'u tam bunu hedefliyor ama mutlak eşik, marj değil"*).

**Filtre NLI'den ÖNCE koşuyor:** daha ucuz, ve "burada sinyal var mı"
sorusu "dilsel kutupsallık var mı" sorusundan önce gelir.

### `0.15` **KALİBRE EDİLMEMİŞ**

Değer brief'in *"PE < 0.15 sinyalleri ön-eğitilmiş ağırlık gürültüsünde
kaybolur"* iddiasından geliyor — **ölçümden değil**. Gözlenen marjlar
0.42–0.65 olduğu için bu eşik o örneklemde **hiç ateşlenmiyor**; bu
bilinçli: eğitim seti zaten 1–2 çifte inmiş durumda, dar bir eşik onu
büsbütün boşaltırdı. Pilot, raporlanan ret sayılarından kalibre edecek.

`SNR_MARGIN_FLOOR_CALIBRATED = False` sabiti ve sonuç JSON'undaki
`pair_filter.snr_margin_floor_calibrated` alanı bunu **koşumun kendi
kaydına** yazıyor — kalibre edilmemiş bir eşiğin yerleşmiş gibi
okunmasını engellemek için. Plan bunu şart koşuyordu ("`calibrated: false`
işaretlenir").

### Raporlama zorunluluğu (plan şartı, uygulandı)

`pair_filter` bloğu: `snr_candidates`, `snr_rejected_below_margin`,
`nli_candidates`, `nli_rejected`, `pairs_passed`, eşik ve kalibrasyon
bayrağı. Ayrıca `[SNR]` log satırı. Gerekçe: `MIN_PAIRS` kalibre edilmemiş
(I1.5), bu sayılar olmadan **"az ama güçlü çift"** ile **"filtre eğitim
setini boşalttı"** JSON'da birbirinin aynısı görünür.

### Kanıt

3 mutasyon, 3 kırılma: filtreyi kaldır · NLI'den sonraya taşı ·
`calibrated=True` yalanı söyle. Ayrıca planın istediği geriye dönük kapı
test altında: **eşik 0 iken davranış eskisiyle birebir aynı** (marjlar
sıralama sonrası pozitif olduğundan sıfır eşik hiç ateşlenemez).
Tam suite **296 passed**.

### Bu kayıtta karara BAĞLANMAYAN

Ölçüm sırasında çıkan yapısal bulgu: **dokuz çiftin `rejected` tarafı aynı
metin.** Örneklem tesadüfü değil, `best_by_event`'in yapısı — verilen bir
chosen için en büyük marj her zaman global maksimum-PE olaydan gelir, yani
en kötü tek completion bütün çiftlerin reddedilen tarafı olur. Eğitim seti
"bir kötü örnek vs diğer her şey" biçiminde.

Bu bir eşik ayarı değil, `build_pe_ranked_pairs`'in **eşleştirme
tasarımı**; U5'e sıkıştırmak yanlış olurdu. **GAP-18** olarak açıldı.
D-029'un ölçtüğü −4.37'lik çöküşü de kısmen açıklıyor (aynı metin 9 kez
aşağı itiliyor) ve DR brief'inin F8 uyarısıyla (hizalama evresi ihlali)
örtüşüyor.

---

## D-031 · 2026-08-10 · U6: consolidation **faz-2'den sonra**, transfer'den önce

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `987a1bc`.
D-022'nin **bilerek açık bıraktığı** zamanlama sorusunu kapatır.
GAP-14 kapanır.

### Açık soru neydi

Gen1 **iki yaşam** sürüyor (faz-1 → eğitim → faz-2), ikisi de aynı vault
üzerinde. "Yaşam sonu" hangisi? D-022 bunu sessizce seçmemek için açık
bırakmıştı.

### Karar: **faz-2 sonrası, `transfer_to_heir`'den hemen önce**

Reddedilen alternatifler: *faz-1 sonrası* ve *her iki faz sonrası*.

**Gerekçe — null kolu.** `delta_pe = pe_after − pe_before` iki faz
arasındaki **tek müdahaleyi** (eğitimi) yalıtmak için tasarlanmış. Kod
`_train_adapter`'ı yalnızca `{ARM_LIVED, ARM_SHUFFLE}` için çağırıyor;
**null iki fazı da eğitimsiz koşuyor**, yani `delta_pe ≈ 0` olmalı —
kontrolün varlık sebebi bu.

`run_consolidation` **siliyor** (Ebbinghaus unutması). Fazların arasına
girerse faz-2'nin bellek çağırması faz-1'inkinden farklı bir kasa görür ve
null'ın `delta_pe`'si **saf unutma etkisi** olur. **Kontrol, ölçmesi
gereken sıfırı ölçemez hale gelir.** Faz-1 ve "her ikisi" seçenekleri bunu
yapıyor; faz-2 yapmıyor.

Ek olarak faz-2 seçeneği D-022'nin hedefini tam karşılıyor (mirasa giden
malzeme uykudan geçsin) ve demo yolunun semantiğiyle örtüşüyor —
`graph.py:1433` koşum sonunda **bir kez** çağırıyor.

### Kapsam uyarısı tekrarlanıyor

Bu yalnızca PPR'ı canlandırmıyor: `run_consolidation` siler, güçlendirir,
kenar yazar. **Unutmayı da açıyor**, ve unutma gen2'ye giden miras
malzemesini değiştiriyor ⇒ **birincil uç noktaya (doğum-drift, D-002)
dokunuyor.** D-022 bunu kabul etmişti; etkisi pilotta ölçülecek.

### Raporlama

Her soy için `consolidation` bloğu: `deleted_count` · `strengthened_count`
· `edges_created` · `drift_flag_count` · `now_counter`. Ayrıca
`[CONSOLIDATE]` log satırı. Hata **yükseltiliyor**, sessizce atlanmıyor —
atlanan bir uyku, JSON'un "uyku oldu" demesiyle birlikte gelirdi.

**I5.1 FLAG kalıyor** (D-022 madde 2): pilot kenarların gerçekten
oluştuğunu göstermeden, doğrulanmamış bir düzeltmeye koşum öldürme yetkisi
verilmiyor.

**Kanıt:** 2 mutasyon, 2 kırılma — çağrıyı fazların arasına taşı · hatayı
yut. Tam suite **299 passed**.

### Yan gözlem → **GAP-19** (kapsam dışı bırakıldı)

Faz-2 taze gövdeyle başlıyor (`initial=None`), yani `event_log` sıfırdan
sayıyor. İki fazın anıları **aynı sayaç uzayını** paylaşıyor: faz-1
anıları, faz-2'ninkiler kadar taze görünüyor. Ebbinghaus decay
`now_counter − last_activated_counter`'a dayandığı için bu doğrudan
unutma kararını etkiliyor.

U6'nın getirdiği bir sorun **değil** — zaten vardı. Ama consolidation
deney yoluna bağlandığı için **ilk kez etkisi olacak**. `now_counter`
olarak `len(parent_final.event_log)` seçildi, çünkü vault'a yazılan
sayaçlar da faz-yerel; farklı bir değer seçmek uyumsuzluğu büyütürdü.
Doğru çözüm sayaç uzayının kendisini düzeltmek — ayrı iş.

---

## D-032 · 2026-08-10 · Çift darboğazı: sorun eşik değil, **prompt**

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `5afc9ee` ·
`7232a04` · `17bc9bd`. `CLAUDE.md` §1'in üç bağlı maddesini (NLI eşiği ·
GAP-18 · `SNR_MARGIN_FLOOR`) **tek kayıtta** kapatır — plan §D 8.0'ın
istediği biçimde. GAP-18 küçülür, GAP-2'nin açık yarısı etkilenmez.

### Ölçüm — keşifsel, ön-kayıtlı değil

`dau_runs/exploratory_pair_design_replay.json`. Seed 2001'in **tüm aday
uzayı** `lr_probe_pairs.json`'daki 9 çiftten geri kuruldu (9 chosen +
paylaşılan rejected = 10 olay) ve `nli_score_distribution.json`'a `pe_gap`
üzerinden bağlandı: **41/41 birebir eşleşti**, yani gerçek NLI ve kosinüs
skorlarıyla o yaşam GPU'suz yeniden koşulabiliyor.

**Sınırlar:** tek seed, 10 olay, greedy, tek atış. Seed 2002'nin
completion'ları geri kurulamadı, tasarımlar orada tekrarlanmadı.

| Tasarım (SNR floor sonrası) | çift | benzersiz `rejected` |
|---|---|---|
| Şimdiki: `best_by_event` + NLI≥0.60 | 3 | 1 |
| Polarite filtresi yok | 9 | 1 |
| NLI yerine kosinüs [0.25, 0.80] | 9 | 2 |
| Ayrık eşleştirme (`rejected` tekil) | **2** | 2 |

### Dört bulgu

**1. Darboğaz NLI değil.** 10 olay yalnızca **7 benzersiz completion**
üretmiş (1, 2, 3 aynı cümle). Filtre tamamen kaldırılsa bile tavan burada.

**2. GAP-18 ile çift sayısı birbirini yiyor.** `rejected`'ı tekilleştirmek
9 çifti 2'ye düşürüyor. Dejenerelik **veriye bağlı değil, yapısal**: sabit
bir `chosen` için en büyük marjlı partner her zaman global maksimum-PE
completion'dır, yani `best_by_event` **her** yaşamda `uniq_rejected=1`
verir. Zorla çeşitlendirince ölçüldü: aynı metin (*"I will extract
resources…"*) bir çiftte `chosen`, başkasında `rejected` oluyor — PE
`(durum, eylem)`'in fonksiyonu, çift ise yalnızca metnin. Çeşitlilik
satın alırken **çelişik denetim** satın alınıyor.

**3. `SNR_MARGIN_FLOOR` ateşleniyor ama etkisiz.** 41 adayın 25'ini eliyor
(%61), ama `best_by_event` çıktısı floor açıkken de kapalıyken de birebir
aynı — yalnızca argmax'ın zaten atacağı çiftleri atıyor. D-030 "gerçek
veride ateşlenmiyor" demişti; **yarısı doğru**: ateşleniyor, ama seçiciyle
gereksiz. Bu seçici dururken kalibre edilemez. Değeri değişmedi.

**4 (en ağır, listede yoktu). DPO prompt'unun içinde yaşam yok.**
Eğitim prompt'u **51 token**, `system=""` — `PreferencePair`'de `system`
alanı yoktu, hiçbir yer set etmiyordu. İçeriği:
`"Lived preference: pe=0.413 decision over pe=0.873"`. Çıkarım prompt'u
246–306 token: `SYSTEM_PROMPT` + anı bloğu + stratejik beklenti + somatik +
drift + AgentView JSON. Üstelik prompt modele **cevap anahtarını** veriyor:
tercih edeceği cümlenin PE'sini söylüyor, ama PE karardan **sonra**
hesaplanıyor — çıkarımda hiç tetiklenemeyecek bir kısayol.

### Karar: **önce prompt, sonra filtre.** Reddedilen alternatifler

- **KTO'ya geçmek** (brief F9). Üç maddeyi birden buharlaştırırdı, ama
  kayıp fonksiyonunu, eğitim döngüsünü ve master reference'ı değiştirir —
  ve **prompt sorunu KTO'da da aynen durur**. Ertelendi, çürütülmedi.
- **Sadece filtre takası.** Çifti 3→9 yapardı, ama bilimsel değeri
  açmazdı: model yine hiç görmeyeceği bir prompt altında eğitilirdi.
- **Yalnızca AgentView'ı saklayıp system'i `SYSTEM_PROMPT` sabitinden
  yeniden üretmek.** Daha küçük payload, ama sabitten yeniden üretme
  deseni (§2.8) ve anı/somatik/drift katmanlarını düşürüyor.
- **Ayrık eşleştirmeyle GAP-18'i doğrudan kapatmak.** Ölçüldü: 9→2 çift.

### Uygulama

**`5afc9ee` — kayıt.** `agent_node` karar olayına, modele giden **iki
metnin aynısını** yazıyor (backend dalının üstünde bir kez bağlanıyor,
sonradan yeniden üretilmiyor). SYSTEM_1 (NPC) kararları **bilerek**
hiçbir prompt anahtarı taşımıyor: LLM hiç koşmadı, o karar politikadan
bir örnek değil. Bu yol bugün `_run_system1_fallback` üzerinden erişilebilir
ve NPC metni şimdiye kadar `chosen`/`rejected` olarak eğitime girebiliyordu.

**`7232a04` — kullanım.** Çift prompt'u artık **`chosen` olayının kendi
prompt'u**; `PREF_LIVED_CONTEXT_TEMPLATE` emekliye ayrıldı. `PreferencePair`
`system` alanı kazandı — `local_llm._run_dpo_epochs` onu zaten `getattr`
ile okuyordu, kanca yazıldığından beri ölüydü. Prompt'suz olay `[LORA][WARN]`
ile atlanıyor ve `_pair_filter_report`'a `prompt_skipped_no_record` olarak
giriyor (§2.9). `shuffle_preference_pairs` `dataclasses.replace`'e geçti:
alan alan yeniden kuruyordu, yani `system` eklendiği anda sessizce
düşürecekti ve shuffled kol lived koldan **farklı koşullamayla** eğitilecekti
— iki kol zıt değil, kıyaslanamaz olurdu.

**`17bc9bd` — filtre.** Polarite kapısı NLI çelişkisinden **kosinüs
mesafesine** geçti, bant `[0.25, 0.80]`. `NLI_CONTRADICTION_THRESHOLD`
**0.60'ta bırakıldı** — ölçüm eşiğin *yanlış* olduğunu değil, *ilgisiz*
olduğunu söyledi (85 çiftte geçme oranı 0.60'ta %12.9, 0.30'da %12.9;
dağılım çift tepeli). Karar eşik değil **alet seçimi**; eski eşik
`POLARITY_FILTER=nli` ile okunabilir ve erişilebilir kalıyor. Alt sınır
paraphrase'i eliyor (NLI'nin işiydi), üst sınır konudan kayan çiftleri
eliyor (NLI'de karşılığı yoktu). MiniLM zaten PE sensörü — yeni model yok,
LLM-as-judge yok. **`POLARITY_COSINE_CALIBRATED = False`**: bant brief'ten
geldi, kendi seed'imizden seçilmedi (§2.7 — değer ölçümden seçilmez).

`NLI_FILTER_STATS` → `POLARITY_FILTER_STATS`, sonuç anahtarları
`nli_*` → `polarity_*`, ve `describe_polarity_filter()` hem
`_pair_filter_report`'a hem I5.2'nin mesajına bağlandı. NLI adını taşıyan
bir sayaç kosinüs koşarken her sonuç dosyasında yanlış aleti etiketlerdi.

### D-027 düzeltmesi (kayıt append-only olduğu için burada)

D-027'nin gerekçesi — *"kesilen baş chat şablonu + `SYSTEM_PROMPT`"*,
*"gerçek prompt 246, anıyla 306 token, yani bir anı 256'yı taşırıyordu"* —
**çıkarım** prompt'unu tarif ediyor. Eğitim dizileri ölçüldü:
**61–116 token, prompt tarafı 51**. 256'da kesme dalı gerçek eğitim
verisinde **hiç ateşlenemezdi**. `DPO_MAX_SEQUENCE_TOKENS = 512`
**değişmiyor** ve D-032 sonrası ilk kez gerçekten gerekli oluyor: gerçek
prompt 246–306 + completion ~65 ≈ 370. Doğru değer, yanlış gerekçe.

### Dur-kontrol (plan §D 8.0)

*"Değişiklikten sonra gerçek koşumda kaç çift eğitime giriyor? 1–2'de
kalıyorsa darboğaz kapanmamıştır."* Gerçek `build_pe_ranked_pairs`, seed
2001'in gerçek completion ve PE'leri üzerinde koşuldu (prompt'lar sentetik
— o yaşam kayıttan önce; filtreler completion ve PE okuduğu için **sayı
gerçek**):

> **9 çift** · 9 **farklı** prompt · 2 benzersiz `rejected` ·
> SNR 41 adayın 25'ini, polarite kalan 16'nın 2'sini eledi.

Önce 1–3'tü. **Darboğaz açıldı.** GAP-18 de niteliksel olarak değişti:
eğitim seti artık "aynı soru 9 kez" değil, **9 farklı durum, 2 ortak
negatif** — literatürde standart bir yapı.

### Bunu kapatmayan şey

10 olayda 7 benzersiz metin tavanı duruyor. Uzun yaşam bunu açar (U3: 50
olayda 27 benzersiz), ama bu pilotun kararı. `SNR_MARGIN_FLOOR` hâlâ
kalibre değil ve `best_by_event` dururken kalibre edilemez.

**Kanıt:** 8 mutasyon, 8 kırılma — sabitten yeniden üretilen system
prompt'u · SYSTEM_1'in prompt iddia etmesi · PE-değerli template'e dönüş ·
eksik prompt'un sessizce yutulması · shuffle'ın alan alan yeniden kurulması
· hep-geçen polarite kapısı · üst sınırın kaldırılması · tanınmayan filtre
adının varsayılana düşmesi. Tam suite **314 passed, 2 deselected**.

---

## D-033 · 2026-08-10 · İlk gerçek koşum: darboğaz açık, ama **adapter'lar koşumlar arası sızıyor**

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `782ca33`.
D-032'nin dur-kontrolünü canlı doğrular, **GAP-20**'yi açar ve kapatır.

### Ölçüm — keşifsel, ön-kayıtlı değil

`dau_runs/smoke_d032_local.json`. On bir alet değişikliğinden sonra **ilk
uçtan uca gerçek koşum**: yerel Llama-3.1-8B, N=1 (seed 2001), gen1=10 olay,
gen2=5, `--lora`. `exit 0`, toplam **2dk 47sn** (model yüklemesi dahil),
yaşam içi 162.9sn.

**Sınırlar:** tek seed, 10 olay, tek atış. Süre tahminleri (gen1=50'de seed
başına ~11–12 dk) doğrusal ölçekleme varsayıyor, ölçülmedi.

### Çalıştığı doğrulanan (D-032'nin canlı dur-kontrolü)

| Ne | Sonuç |
|---|---|
| Eğitime giren çift | `lived` **8**, `shuffle` 6, `null` 0 (doğru) — önce 1–2 idi |
| `[LORA][WARN]` | **0** — canlı koşumda her kararın kayıtlı prompt'u vardı |
| I5.2 | geçti — polarite kapısı gerçek modelde danışıldı |
| VRAM | 3 OOM **uyarısı**, allocator toparladı, koşum tamamlandı. D-032'nin ~370 token'lık dizileri 8 GB'a sığıyor ama **payı yok** |
| Bayraklar | I3.2 (`pi_n_distinct` düşük, kalibre değil) · I5.4 (somatik hiç uygulanmadı — GAP-3) |

`loss≈0.698 (≈ln2)`, `acc=0.375`: lr 1e-6'da politika referanstan çok az
kımıldıyor — D-029'un kasıtlı sonucu, pilotta bakılacak.

### Bulunan kusur — pilotu bloke ederdi

Üç kolun **faz-1 yaşamları ayrıştı**: `n_unique` 6 / 7 / 6, çift 8 / 0 / 6.
Shuffle tanımı gereği "lived ile aynı faz-1, sonra takas" olduğundan bu
sayılar eşit olmalıydı.

**Sebep:** `graph.agent_node` her yerel kararda `switch_adapter` çağırıyor
ve `switch_adapter`, `adapter_exists(agent_id)` doğruysa **diskten
yüklüyor**. Adapter dizinleri yalnızca `agent_id` ile anahtarlanıyor, yani
aynı seed'le yeniden koşmak onları yeniden kullanıyor — **faz-1 önceki
koşumun eğittiği ağırlıklarla başlıyor.**

⚠ Çağrı **`DAU_LORA_ENABLED`'a bağlı değil** → `--no-lora` koşumu da kirlenir.

**Kanıt:** `dau_runs/adapters` altında **35 dolu dizin**, en eskisi 08-07.
08-09 pilotu (N=3, seed 2001–2003, `lora_enabled=1`) tam olarak
`cprime-{lived,shuffle}-{2001,2003}-g1`'i eğitip kaydetmiş; 2003'ünkiler
**hâlâ 08-09 09:15 tarihli, dokunulmamış**. Bugünkü smoke'ta `lived` ve
`shuffle` 08-09 ağırlıklarını yükledi; `null` hiç eğitilmediği için dizini
boştu ve tek temiz kol o oldu.

**Sapmanın yönü kötü:** LIVED koşumdan koşuma eğitim biriktiriyor, NULL hiç
biriktirmiyor ⇒ sızıntı **H1 lehine**. Bu, §6'daki koşum-içi sızıntının
(`f25b0ef`) **koşumlar arası ikizi**; `test_no_dead_adapter_root_reference`
bunu görmüyor.

### Karar: **I0.7 — kirli dizinle koşum başlamaz (ABORT)**

Reddedilen alternatifler:

- **Koşum başında otomatik silme.** En az sürtünme, ama **veri siliyor**;
  yanlış bir `--seed-start` başka bir koşumun çıktısını götürebilirdi.
  Önceki koşumun artığını silmek **kapının değil operatörün** kararı.
- **`agent_id`'ye koşum kimliği eklemek.** Hiçbir şey silinmezdi, ama
  `AGENT_ID_SEED_PATTERN`'e ve mevcut bütün çıktıların kimliklerine
  dokunurdu — en geniş değişiklik.
- **Sadece GAP açıp elle temizlemek.** Koruma olmazdı; aynı tuzağa bir
  sonraki koşumda düşmek serbest kalırdı.

Yerel backend dışında **`None` (N/A)** döner, `True` değil: `switch_adapter`'ın
disk yolu yalnızca yerelde çalışır ve **hiç bakmamış bir kontrol, geçmiş
gibi okunmamalı** (`InvariantResult.passed=None` bunun için var).

### Yan düzeltme: sorgu yazmayı bıraktı

`adapter_exists` → `get_adapter_path` üzerinden gidiyordu, o da `mkdir`
yapıyor. **Sorulan şeyi yaratan bir sorgu**: 114 dizinin **79'u** bu yan
etkinin izi. Yeni `adapter_dir()` salt-okunur; yoksa I0.7'nin denetimi
denetlediği şeyi değiştirirdi.

### Yan düzeltme: multigen `pair_filter` raporlamıyordu

`_pair_filter_report` yalnızca Protocol C′'nin dosyasına giriyordu. Deney
yolu D-014/D-031 uyarınca **multigen**, yani `prompt_skipped_no_record`,
polarite red sayıları ve `pairs_passed` **asıl koşumun çıktısında
görünmüyordu**. D-032'nin eksiğiydi, burada kapandı.

**Kanıt:** gerçek dizine karşı canlı kontrol kirli dört ajanı adlandırıyor.
3 mutasyon, 3 kırılma — hiç ateşlemeyen kapı · faz-0'a bağlanmamış kapı ·
yerel-olmayanı `True` sayan kapı. Tam suite **317 passed, 2 deselected**.

### Pilot öncesi kalan

`dau_runs/adapters/` **temizlenmeli** (ya da pilot taze seed'lerle
koşulmalı) — I0.7 artık unutmaya izin vermiyor ama temizliği yapmıyor.

---

## D-034 · 2026-08-10 · Pilot koşuldu (N=3): alet çalışıyor, sinyal **kurulmadı**

**Durum:** ölçüm kaydı. Karar içermez — pilotun işi kalibrasyondu.
Ham: `dau_runs/pilot_d033_n3_local.json`. Kod değişikliği yok.

### Koşum

Yerel Llama-3.1-8B, greedy, **N=3** (seed 2001–2003), gen1=50 olay,
gen2=20, k=3, `--lora`. **58 dk** (15:18:39 → 16:17:00), `exit 0`.
Adapter dizini koşumdan önce `archive/adapters_pre_pilot_2026-08-10/`'a
taşındı, **I0.7 yeşil** başladı.

**Sınırlar:** N=3, tek atış, tek seed ailesi. **Hipotez testi değil** —
GAP-9'a göre N=3 hiçbir etkiyi saptayamaz. Aşağıdaki yön ifadeleri
kanıt değil, kalibrasyon girdisidir.

### Alet: çalışıyor

| Ne | Sonuç |
|---|---|
| Değişmezler | **18'in 17'si geçti.** Yalnız I3.2 bayrak (`gen2 pi_n_distinct=7 < 8`, **kalibre değil**) |
| I0.7 | geçti — temiz başlangıç doğrulandı |
| **I5.4** | **ilk kez geçti** — somatik ölçek uygulandı. Smoke'larda "never applied" bayraktaydı; 50 olayda GAP-3'ün belirtisi çıkmıyor |
| I2.2 / I4.2 | null eğitimsiz + adapter'sız · gen2 RNG üç kolda birebir aynı |
| **D-032 doğrulaması** | `prompt_examples_seen=300`, **`prompt_skipped_no_record=0`** — pilotun bütün kararlarının kayıtlı prompt'u vardı |
| VRAM | **1** OOM uyarısı (10 olaylık smoke'ta 3'tü), çökme yok |

**Çift simetrisi — I0.7'nin doğrudan kanıtı:** her seed'de `lived` ve
`shuffle` **birebir aynı** sayıda çift aldı: **47/47 · 41/41 · 38/38**
(toplam 252). Kirli smoke'ta 8'e karşı 6'ydı. Tasarımın gerektirdiği eşitlik
geri geldi ⇒ kolların ayrışma sebebi gerçekten adapter sızıntısıymış.

**Çeşitlilik tavanı açıldı:** `n_unique` = 29 · 22 · 27 (50 olayda),
D-032'nin 10 olayda ölçtüğü 7'ye karşı. U3'ün greedy ölçümüyle (27) uyumlu.

### Filtre kalibrasyon verisi — ilk gerçek sayılar

| Kapı | Aday | Elenen | Oran |
|---|---|---|---|
| `SNR_MARGIN_FLOOR=0.15` | 6800 | 3076 | **%45** |
| Polarite (kosinüs `[0.25, 0.80]`) | 3724 | 1078 | **%29** |
| Geçen | — | — | **252 çift** |

⚠ **D-032'nin bir ifadesi 50 olayda geçersiz.** Orada "SNR tabanı ateşleniyor
ama **etkisiz**; `best_by_event` dururken kalibre edilemez" demiştim — bu
**10 olaylık** veriye dayanıyordu (41 aday). 50 olayda aday uzayı
C(50,2)≈1225'e çıkıyor ve taban 6800 adayın 3076'sını eliyor. Etkisizlik
iddiası bu ölçekte **doğrulanmadı**; kalibrasyon artık mümkün.

### Sinyal: kurulmadı

`ΔPE = pe_after − pe_before` (gen1, eğitim iki faz arasındaki müdahale):

| Kol | ortalama ΔPE | s2001 | s2002 | s2003 |
|---|---|---|---|---|
| lived | **+0.0800** | +0.0412 | +0.0601 | +0.1386 |
| null | +0.0583 | +0.0412 | +0.1612 | −0.0276 |
| shuffle | +0.1125 | +0.0412 | +0.1438 | +0.1527 |

- **lived vs null:** 1 seed H1 yönünde (−0.101), 1 seed ters (+0.166),
  1 seed **tam berabere**. Ortalamada lived null'dan **kötü**.
- **lived vs shuffle:** 3 seed'in **üçünde de lived ≤ shuffle**
  (0.000 · −0.084 · −0.014). Daha temiz karşılaştırma, çünkü iki kol aynı
  sayıda çiftle, aynı hesapla eğitildi; yalnız **yön** farklıydı. Ama
  farkların ikisi küçük ve biri sıfır.

**Seed 2001'de eğitim hiçbir şey değiştirmedi:** `pe_after` üç kolda da
**bit düzeyinde aynı** (0.45483523726463315). 47 çiftle eğitilmiş adapter,
faz-2 davranışını ölçülebilir biçimde etkilemedi. Diğer iki seed'de etkiledi.
lr=1e-6'nın (D-029) etkiyi ne kadar bastırdığı **açık soru** — D-029 bilerek
küçük seçmişti, bu onun bedeli olabilir.

`acc` (eğitim sonrası marj doğruluğu): 0.404 · 0.537 · 0.447 (lived) —
yarının altında ya da civarında, yani politika referanstan çok az kımıldıyor.

### gen2 (ikincil; **adapter miras alınmıyor** ⇒ yalnızca Kanal 1)

ortalama PE: lived 0.500 · null 0.484 · shuffle 0.444. Ters yönde, ama
gen2'ye adapter geçmediği için bu Kanal 2'yi değil, eğitimin faz-2
davranışını değiştirmesi üzerinden **kasaya yazılanı** ölçüyor.
`n_transfer_candidates` toplam 14; her soyda `f_agent=0.000`,
`fitness=low` — **f_agent üç kolda da sıfır**, ayrıca bakılmalı.

### ⚠ Çelişki — raporlanıyor, sessizce seçilmiyor (§2.11)

`NULL_ARM_MAX_ABS_DELTA = 1e-9` ve yorumu: *"NULL takes no training, so with
the harness clean its replay is exact."* Pilotta null'ın ΔPE'si
**+0.041 / +0.161 / −0.028**. Sabit yalnızca `run_protocol_c_prime`'da
kullanılıyor (satır 326, 1186), **multigen'de değil** — ve multigen'de faz-2
aynı kasayla devam ettiği için (`run_life_keep_vault`) null'ın ΔPE'si
doğal olarak sıfır değil. Yani kod hatası **değil**, ama yorumun iddiası
deney yolunda geçerli değil ve şu sonucu doğuruyor: **multigen'de ΔPE
eğitimi tek başına yalıtmıyor**, kasa büyümesiyle birlikte ölçüyor. Bu
yüzden yorumlanabilir kontrast `lived − null`, ham ΔPE değil.

### Pilotun cevapladıkları / cevaplamadıkları

**Cevapladı:** alet uçtan uca koşuyor · kapılar geçiyor · çift darboğazı
gerçekten açık (252 çift) · çeşitlilik tavanı 50 olayda açılıyor ·
VRAM yetiyor · süre = **seed başına ~19.4 dk** ⇒ N=15 ≈ **4.9 saat**.

**Cevaplamadı:** `SNR_MARGIN_FLOOR` ve kosinüs bandının **değerleri**
(dağılım verisi artık var, seçim yapılmadı) · U4'ün `N`'i · A3 ·
`MIN_PAIRS` · GAP-9'un güç hesabı (N=3'ten `d` kestirilemez) ·
**lr=1e-6 etkiyi bastırıyor mu**.

---

## D-035 · 2026-08-10 · Enstrümantasyon + ikinci N=3: **ölçüm penceresi darboğaz**

**Durum:** ölçüm kaydı + Adım 0 uygulaması (`1250483` · `c2dd2ae` · `a0d54f3`).
Karar içermez; **dört karar açar** (aşağıda). Ham:
`dau_runs/step0_d035_n3_local.json`. **`run_quality=clean`** — 18 değişmezin
**hepsi** geçti, projede ilk kez.

### Koşum

Pilotla birebir aynı şekil (N=3, seed 2001–2003, gen1=50, greedy, `--lora`),
temiz adapter dizini, **59 dk 37 sn**, `exit 0`.

**Sınırlar:** N=3, tek atış. Aşağıdakiler alet bulgusu; etki büyüklüğü değil.

### 1. Kanal 2 atıl değil — kararların **%68'ini** değiştiriyor

| Seed | `lived` ≠ `null` | `shuffle` ≠ `null` | **ilk 10 olayda** | ilk fark |
|---|---|---|---|---|
| 2001 | 21/50 (%42) | 19/50 | **0** | index 16 |
| 2002 | 43/50 (%86) | 44/50 | 6 | index 3 |
| 2003 | 38/50 (%76) | 39/50 | 8 | index 0 |

Faz-1 kollar arasında özdeş (adapter henüz yok), dolayısıyla bu fark
**yalnızca adapter'ın eseri**.

### 2. Asıl bulgu: **ΔPE, değişimin düştüğü yere bakmıyor**

`_window_mean` = `pe_list[:10]`, faz ise **50 olay**. Uç nokta, her fazın
yalnızca **ilk beşte birini** okuyor. Sonuç mekanik:

- **s2001'de 21 karar değişti, ilk 10'da sıfırı.** İlk fark 16. indekste.
  `pe_after` `null` ile **bit düzeyinde aynı** çıktı — hem pilotta hem burada.
- s2002 (ilk 10'da 6) ve s2003 (ilk 10'da 8) ΔPE'de ayrıştı.

Yani uç nokta, müdahalenin büyüklüğüne değil, **penceresine kaç tanesinin
düştüğüne** tepki veriyor. D-034'te "sinyal kurulmadı" diye kaydettiğim şeyin
sebebi büyük ölçüde bu: yaşamın %68'ini yeniden yazan bir müdahale, %20'lik
bir pencereden küçük ve tutarsız bir fark olarak görünüyor.

⚠ `PE_WINDOW_EVENTS = 10` kodda **ön-kayıtlı** işaretli. Değiştirmek D-kaydı
ve Yasin'in kararını ister — burada **değiştirilmedi**.

### 3. `F_agent` yapısal olarak sıfır — D-003'e dokunuyor

Dokuz soyun **hepsinde** `f=0.000`, `E=0.000`, `|dpool|` **381–394**;
`POOL_MAX = 100`. Formül `0.4·(E/E_max) + 0.3·(1 − |dpool|/POOL_MAX) +
0.3·survival`, `[0,1]`'e kırpılıyor. Pool terimi ≈ **−0.87**, enerji terimi
**0**, hayatta kalma terimi en fazla **+0.3** ⇒ toplam negatif ⇒ **0**.

Sebep: `agent_delta_pool` yaşam boyunca yapılan **bütün çıkarımların
toplamı** — hep pozitif, monoton. Formül ise bunu bir bütçe **sapması** gibi
kullanıyor. 10 olayda görünmez, 50 olayda kaçınılmaz.

Sonucu: **D-003'ün F_agent transfer kapısı bu rejimde ayırt etmiyor** —
her ajan "low", davranışı ne olursa olsun. Kilitli karar, düzeltilmedi.

### 4. Eğitilmiş kol **tekrarlanabilir değil**

Pilotla karşılaştırma (aynı seed, aynı şekil):

| | `pe_before` | çift sayısı | `pe_after` |
|---|---|---|---|
| `null` (9 kol) | aynı | 0 | **aynı** |
| `lived`/`shuffle` | aynı | aynı (47/41/38) | **s2002 ve s2003'te FARKLI** |

Girdi birebir aynı, çıktı farklı ⇒ sapma **eğitimde**. Eğitimsiz yol bit
düzeyinde tekrarlanabilir, eğitilen yol değil. `TORCH_DETERMINISTIC_WARN_ONLY
= True` bunun muhtemel kaynağı. **Ön-kayıtlı bir deneyde test edilen kolun
replay edilememesi ayrı bir sorundur.**

(s2001'de `pe_after` aynı çıktı — çünkü değişen 21 kararın hiçbiri pencereye
düşmüyor; madde 2 ile tutarlı.)

### 5. Kalibrasyon dağılımları — ilk kez elimizde

**SNR marjı** (n=6800): min 0.0000 · p25 **0.0778** · **p50 0.1717** ·
p75 0.3646 · p95 0.5494 · max 0.7416.
Mevcut taban **0.15**, medyanın hemen altında, %45 eliyor.

**Polarite / kosinüs** (n=3724): min 0.0010 · p25 **0.2119** ·
**p50 0.4289** · p75 0.5649 · p95 0.6746 · **max 0.8049**.
Mevcut bant **[0.25, 0.80]**. ⚠ **Üst sınır fiilen atıl** — gözlenen en büyük
değer 0.8049, yani 0.80'i aşan neredeyse hiç yok. İş yapan alt sınır.

İkisi de hâlâ `*_CALIBRATED = False`; **değer seçilmedi** (§2.7: ölçüm yönü
kanıtlar, değeri seçmez).

### Bu koşumun açtığı dört karar — hepsi Yasin'in (D-007)

1. **`PE_WINDOW_EVENTS`** — ön-kayıtlı parametre. Pencere mi büyümeli, yoksa
   uç nokta mı değişmeli (D-002 zaten doğum-driftı birincil sayıyor)?
2. **`F_agent` formülü** — D-003 kilitli. `agent_delta_pool` kümülatif mi
   kalmalı, net değişime mi dönmeli, yoksa pool terimi mi normalize edilmeli?
3. **Eğitim determinizmi** — `TORCH_DETERMINISTIC_WARN_ONLY` sıkılaştırılsın
   mı, yoksa tekrarlanamazlık kabul edilip çoklu seed'e mi yaslanılsın?
4. **İki eşiğin değerleri** — dağılım var, seçim yok.

### Yan bulgu: doğum-drift kola tepki veriyor

s2001 ve s2002'de `lived` ile `null` farklı drift bayrakları üretti
(`{social,resource}` vs `{uncertainty,resource}`), s2003'te aynı. Birincil uç
nokta (D-002) ΔPE'nin göremediği yerde ayrışıyor — madde 1'in kararına girdi.

**Kanıt:** 8 mutasyon, 8 kırılma (ilk turda ikisi geçti, testler düzeltildi).
Tam suite **323 passed, 2 deselected**.

---

## D-036 · 2026-08-10 · Uç nokta fazın **tamamını** okuyor (`PE_WINDOW_EVENTS`)

**Durum:** kabul edildi (Yasin, 2026-08-10), uygulandı `1489548` · `42e966c`.
D-035'in açtığı **dört karardan birincisi**. Ön-kayıtlı bir parametreye
dokunur, o yüzden kendi kaydını ister.

### Sorun

`PE_WINDOW_EVENTS = 10`, faz ise `EVENTS_PER_ARM = 50`. `_window_mean` =
`pe_list[:10]` ⇒ uç nokta her fazın **ilk beşte birini** okuyordu.

D-035 bunun bedelini ölçtü: adapter faz-2 kararlarının 21/43/38'ini
değiştiriyor, ama `delta_pe` yalnızca **pencereye kaç tanesinin düştüğüne**
tepki veriyor. Seed 2001'de 21 karar değişmiş, **ilk 10'da sıfırı**, ilk fark
16. indekste — ve `pe_after` iki ayrı koşumda da `null` ile bit düzeyinde
aynı çıkmıştı.

`W=10` bu faz uzunluğu için hiç seçilmemişti: fazların 10 olay olduğu bir
mini-testten geliyordu, orada **pencere = fazın kendisi**ydi. Faz 50'ye
çıktı, pencere 10'da kaldı.

### Karar: pencere = fazın tamamı

**İlkeden seçildi, veriden değil.** Müdahale tüm fazı etkiliyor, ölçüm de tüm
fazı kapsıyor. Sonuca uydurulması **mümkün bile değildi**: karar verildiği an
gen1 PE izleri kaydedilmiyordu, yani hiçbir alternatif pencere puanlanmamıştı
(§2.7 — ölçüm yönü kanıtlar, değeri seçmez).

`PE_WINDOW_ALL_EVENTS = 0` sentinel; pozitif değer eski prefix davranışını
korur (gen2 smoke testleri hâlâ onu kullanıyor). Raporlar
`describe_pe_window()` üzerinden gidiyor — ham sabiti basmak sonuç dosyasında
`"pe_window_events": 0` yazardı, bu da "tüm faz" değil "bozuk koşum" gibi
okunurdu (§2.8).

**İlk kanıt:** değişiklikten sonraki ilk koşumda (`repro_a`) seed 2001'in üç
kolu **ayrıştı** — eski pencerede üçü de bit düzeyinde aynıydı.
`lived +0.0445 · null +0.0296 · shuffle +0.0304`.

### Yanında kapanan iki enstrümantasyon kusuru

**1. gen1 PE izleri kaydedilmiyordu.** gen2 `pe_list`'ini saklıyordu, gen1
saklamıyordu; pencere sorusu çıktığında uç noktayı özetlediği izle
karşılaştırmanın yolu yoktu. `pe_before_list` / `pe_after_list` eklendi.
Bunları saklamak pencere seçimini etkileyemez — seçim, bunlar yokken ilkeden
yapılmıştı.

**2. `phase2_decision_divergence` hesaplanıyor, yazılmıyordu.** `pairs`
listesi elle kurulan bir dict, dolayısıyla dataclass'a alan eklemek dosyaya
ulaşmıyor. Bekçi testi **nesneyi** kontrol ediyordu, **dosyayı** değil — suite
yeşil kalırken her sonuç dosyası o alan olmadan yazıldı. `a0d54f3`'te
yakalanan iki boş-bekçiyle aynı sınıf; üçüncüsü.

**Kanıt:** 4 mutasyon, 4 kırılma — sentinel'i yok say · ham sabiti raporla ·
uç noktayı prefix'e döndür · JSON'a yazmayı kaldır. Tam suite
**325 passed, 2 deselected**.

### Kapsam uyarısı

Bu, D-034/D-035'in ΔPE sayılarını **karşılaştırılamaz** kılar: onlar ilk 10
olayın ortalamasıydı, bundan sonrakiler 50 olayın. Eski sayılar geçersiz
değil, **başka bir şeyin** ölçümü.
