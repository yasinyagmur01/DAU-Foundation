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
