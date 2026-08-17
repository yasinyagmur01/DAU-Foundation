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

---

## D-037 · 2026-08-11 · Tekrarlanabilirlik ölçüldü: kaynak eğitim, çözüm **strict determinizm**

**Durum:** ölçüm kaydı. D-035'in açtığı **üçüncü kararın** kanıtı; kalıcı
bayrak değişikliği **henüz yapılmadı** (Yasin'in onayını bekliyor).
Ham: `dau_runs/repro_{a,b}_seed2001.json` ·
`dau_runs/repro_{c,d}_strict_seed2001.json` ·
`dau_runs/exploratory_train_determinism.json`.

### Kontrollü tasarım

Dört koşum, hepsi seed 2001, N=1, gen1=50, aynı kod, temiz adapter dizini:
**A, B** = `warn_only=True` (mevcut) · **C, D** = `warn_only=False` (strict).

| | A ↔ B (warn_only) | C ↔ D (strict) |
|---|---|---|
| faz-1 | özdeş | özdeş |
| `null` faz-2 | **0/50** fark | **0/50** fark |
| `lived` faz-2 | **21/50** fark | **0/50** |
| `shuffle` faz-2 | **23/50** fark | **0/50** |
| adapter ağırlıkları | **farklı** | **birebir aynı** |
| `arm_digest` | farklı | aynı |
| süre | 20dk25 / 20dk16 | 20dk24 / 20dk30 |

**Strict determinizm sapmayı tamamen kapatıyor, maliyeti ölçülemiyor,
abort etmiyor.**

### Sapmanın büyüklüğü — asıl mesele

`warn_only` altında aynı kolun koşumdan koşuma ΔPE yayılımı:
`lived` +0.0445 / +0.0283 / +0.0545 ⇒ **0.026**; `shuffle` ⇒ **0.029**.
Tek koşumda ölçülen `lived − null` farkı ise +0.015 / −0.001 / +0.025.

**Gürültü etkiden büyük.** Bu haliyle tek koşumluk kol karşılaştırması
ölçmek istediği şeyi çözemez — ön-kayıtın önündeki asıl engel buydu.

### ⚠ Kendi ara değerlendirmemin düzeltmesi

Sıra şuydu: D-035 kaynağı `TORCH_DETERMINISTIC_WARN_ONLY` diye **tahmin
etti** → izole probe'lar (8 çift, 47 çift, iki ayrı süreç, adapter
round-trip, adapter takılı çıkarım — hepsi bit düzeyinde deterministik) →
bunlara dayanarak *"atıf desteklenmiyor, eğitim elendi"* diye raporladım →
boru hattı karşılaştırması A ve B'nin **farklı adapter** ürettiğini gösterdi
⇒ eğitim tam da kaynakmış → C↔D testi D-035'in ilk tahminini **doğruladı**.

Yanlış olan D-035 değil, **ara değerlendirmemdi**. İzole probe temiz
koşullarda koştuğu için olguyu yeniden üretemiyordu; ben bir *negatif
sonucu* aklama sayıp raporladım. Ders: bir probe olguyu yeniden
üretemiyorsa, o probe kanıt değil — yalnızca probe'un yetersizliğidir.

**Aynı hata D-035'in metninde de duruyor** (kayıt append-only): orada
"`TORCH_DETERMINISTIC_WARN_ONLY=True` muhtemel kaynak" yazıyor ve bu artık
**doğrulanmış** sayılmalıdır, "muhtemel" değil.

### Neden `null` deterministikti de diğerleri değildi

`null` adapter'sız koşuyor (`lora_B=0` özdeşlik aşısı), yani LoRA yolu
sayısal olarak devre dışı. `lived`/`shuffle` gerçek ek matmul yapıyor;
non-deterministik kernel'lerin yarattığı çok küçük ağırlık farkını greedy
argmax karar değişikliğine çeviriyor ve fark yaşam boyunca birikiyor.

### Öneri (uygulanmadı)

`TORCH_DETERMINISTIC_WARN_ONLY = True → False`. Mevcut yorum bayrağı
*"unsupported ops must not abort a long run"* diye gerekçelendiriyor; bu
korku bu şekilde **ölçülerek yanlışlandı** — dört koşumun ikisi strict
koştu, ikisi de `exit 0`. Kod zaten sampling altında strict'e zorluyordu;
değişiklik greedy'yi de aynı yere getiriyor.

**Sınırlar:** tek seed, tek makine, tek GPU, tek shape (47 çift, 50 olay).
Farklı bir şekilde deterministik karşılığı olmayan bir op çıkarsa strict
mod abort eder — o zaman bu kayıt yeniden açılır.

---

## D-038 · 2026-08-11 · D-036+D-037 tabanı kuruldu, ve iki koşum **birebir** aynı

**Durum:** kabul edildi (ölçüm kaydı)

**Karar:** D-036 (pencere = fazın tamamı) ve D-037 (strict determinizm)
açıkken yeni bir N=3 tabanı kuruldu, ardından **aynı komut ikinci kez**
koşuldu. Taban `dau_runs/baseline_d037_n3_local.json`, tekrar
`dau_runs/repro_d038_n3_local.json` (ikisi de `.gitignore`'da — ham çıktı
yalnız yerelde).

```
PYTHONHASHSEED=0 DAU_LLM_BACKEND=local python -u -m dau.diagnostics.run_cprime_multigen \
  --lora --n-pairs 3 --seed-start 2001 --events-gen1 50 --events-gen2 20 \
  --k-gen2 3 --results dau_runs/<ad>.json
```

Her iki koşumdan **önce** `dau_runs/adapters/` arşive taşındı (I0.7 aksi
halde ABORT ederdi); arşivler `archive/adapters_2026-08-11_0104/` ve
`archive/adapters_2026-08-11_0211/`.

### Sonuç 1 — alet doğrulandı

Her iki koşum: `run_quality=clean`, **18 değişmezin 18'i geçti**, `exit 0`,
62.8 dk / 61.0 dk.

| Kontrol | Beklenen | Çıkan |
|---|---|---|
| çift sayısı | 47/41/38 | 47/41/38 |
| `prompt_skipped_no_record` | 0 | **0 / 300** |
| `[LORA][WARN]` | 0 | **0** |
| `adapter_present` | lived/shuffle ✓, null ✗ | öyle |
| `n_unique` | — | 29/22/27 (faz-1 kollardan bağımsız, D-035 ile aynı) |

Kanal 2 canlı: adapter faz-2 kararlarının **22/45/33**'ünü (lived) ve
**25/17/38**'ini (shuffle) null'dan farklı verdi.

### Sonuç 2 — tekrarlanabilirlik **tam**

Dokuz kolun dokuzu birebir aynı:

| seed | kol | ΔPE | gen2 PE | `arm_digest` | tekrar aynı mı |
|---|---|---|---|---|---|
| 2001 | lived | +0.05454 | 0.3981 | `d0468f926d64` | ✅ |
| 2001 | null | +0.02962 | 0.3447 | `9f8dccac593d` | ✅ |
| 2001 | shuffle | +0.02595 | 0.3854 | `94c77dc7a52c` | ✅ |
| 2002 | lived | +0.00940 | 0.3873 | `194d6135f335` | ✅ |
| 2002 | null | −0.03518 | 0.3968 | `04a562a2179e` | ✅ |
| 2002 | shuffle | −0.02793 | 0.4768 | `757112b50420` | ✅ |
| 2003 | lived | −0.03947 | 0.5026 | `e1b2b642a563` | ✅ |
| 2003 | null | −0.05656 | 0.4622 | `766b34931ad5` | ✅ |
| 2003 | shuffle | −0.00012 | 0.5272 | `6351e5ccd077` | ✅ |

**Altı adapter'ın altısı `sha256` düzeyinde özdeş.** `invariants`,
`pair_filter` (252 çift dahil), `summary` — hepsi aynı.

İki JSON alan alan gezildi: **volatil alanlar dışında tek fark anı
UUID'leri** (koşum başına yeniden üretilen rastgele tanımlayıcılar). Tek bir
sayı, hash veya sayım farklı değil.

⚠ **I4.1 uygulanacaksa bu alanlar dışlanmalı.** Naif bir "iki JSON'u
diff'le" kontrolü determinizm varken bile kırmızı yanardı. Doğru kanca
`arm_digest` — karar dizisi + PE dizisinin hash'i, dokuz kolda da tuttu.

D-037'nin ölçtüğü koşum-arası gürültü (0.026) artık **tam olarak sıfır**.

### Sonuç 3 — sinyal (keşifsel, N=3, hipotez testi **değil**)

`lived − null` = +0.0249 / +0.0446 / +0.0171 ⇒ **3/3 pozitif**, ortalama
+0.0289, sd 0.0142, eşleştirilmiş t(2)=3.53, **p=0.072**; işaret testi
3/3 ⇒ p=0.25. Anlamlı değil, ama yön ilk kez tutarlı **ve gürültü sıfır**.

`lived − shuffle` = +0.0286 / +0.0373 / −0.0394 ⇒ **tutarsız** (bkz. Bulgu 3).

⚠ **D-034'ün bir gözlemi çürüdü:** orada `lived ≤ shuffle` 3/3 seed'de
tutuyordu; tam-faz penceresiyle 2/3 seed'de **ters**. O sıralama 10-olay
penceresinin artefaktıymış.

---

### Bulgu 1 — `F_agent` dejenere değil, **clamp'te ezilmiş**; birim uyuşmazlığı

Dokuz kolun dokuzunda `f_agent = 0.000` **tam olarak**. Sebep ölçüldü:

`compute_fitness` = `0.4·E + 0.3·(1 − |Δpool|/POOL_MAX) + 0.3·(t_surv/t_gen)`.
Formülün `[0,1]`'de kalması `Δpool`'un havuzun **net yer değiştirmesi**
olmasını gerektiriyor. Ama çağıran `agent_delta_pool`
(`society/environment.py:107`) *"Sum of all extractions by agent_id"* —
faz boyunca **kümülatif toplam**. Gözlenen 381–394, `POOL_MAX=100`'ün ~3.9
katı.

```
E=0.000, |dpool|=381 → pool_term = −2.810 → ham F = −0.543 → clamp[0,1] → 0.0000
```

Ham F'ler aslında farklı (−0.543 … −0.582); `|Δpool|`'daki %3.3 yayılım
orada duruyor ama clamp hepsini sıfıra eziyor.

**Sonucu:** `f_agent=0 < FITNESS_LOW_THRESHOLD=0.35` olduğundan
`select_for_transfer` (`foundation/generation.py:137`) her travma anısını
ilk daldan koşulsuz geçiriyor, ve travma **olmayan** anılar
`W = memory_score · f_agent · valence = 0 < 0.6` ile hepsi eleniyor. Yani:

> `select_for_transfer` şu an "hatırlanan travmaları uyarı olarak aktar,
> başka hiçbir şeyi aktarma"ya indirgenmiş. `memory_score` — ajanın ne
> öğrendiğinin yaşadığı yer — sıfırla çarpılıyor.

Parmak izi: `n_cand == n_warn` dokuz satırın dokuzunda.

**D-002'nin birincil uç noktasına etkisi:** sayım kanalı
(`n_transfer_candidates`, `n_inherited_warnings`) üç seed'in üçünde de üç
kolda **özdeş** (3/3/3 · 1/1/1 · 1/1/1) — sıfır varyans. D-002 bu kanalı
"tamsayı sayımlar PE'den yüksek güçlü" diye seçmişti; ölçülen gücü sıfır.
Varyans gösteren tek kanal **büyüklük/bayrak** kanalı (seed 2002'de lived
`social`, iki kontrol `uncertainty`; seed 2003'te social magnitude 0.023 vs
0.756/0.639).

⚠ D-035'in ertelenen 2. kararı ("F_agent'a dokunulmadı") bu yüzden yan bir
konu değil, **pre-reg'i bloke eden şeyin kendisi**. D-035 orada "formül
düzeltmesi ayrım üretmiyor (fark 0.0008–0.0016)" demişti; şimdi sebebi
belli: düzeltilse bile `E=0.000` (9/9) ve `t_surv/t_gen=1.0` (9/9) hâlâ
dejenere, yani üç girdinin **üçü de** bilgi taşımıyor.

**Dokunulmadı.** Düzeltme ayrı bir karar; ve popülasyon gelmeden `F_agent`'ın
*ne yapması gerektiği* de belirsiz (aşağıya bak).

### Bulgu 2 — belgelenen 25 değişmezin **7'si kodda yok**

`docs/PREFLIGHT_INVARIANTS.md` 25 madde tanımlıyor, `preflight.py` 18'ini
kaydediyor. Eksik: **I1.1–I1.5, I2.3, I4.1.** Tek tek denetlendi:

| Değişmez | Belgede | Gerçekte |
|---|---|---|
| I2.3 shuffle gerçekten karışmış | ABORT | ✅ **yapısal** — `shuffle_preference_pairs` sonundaki `if pairs and out == pairs: out[0] = _swap(pairs[0])` en az bir ters çifti garantiliyor. Belge kapıyı abartıyor, özellik tutuyor |
| I1.2 adapter izolasyonu | ABORT | ✅ `test_no_dead_adapter_root_reference` |
| **I1.1 eğitim gerçekten oldu** (`lora_B` abs-sum) | ABORT | ❌ **hiçbir yerde yok** — `lora_B` tüm kod tabanında yalnız `local_llm.py` (sıfırlama) ve `preflight.py` docstring'inde (tarihçe) geçiyor; tek bir test referans vermiyor |
| **I4.1 replay testi** | ABORT | ❌ yok — bu kaydın ikinci koşumu onu **elle** yaptı |
| I1.3 / I1.4 / I1.5 | ABORT/FLAG/FLAG | ❌ yok (I1.4'ün girdisi `pair_filter`'da loglanıyor, kapı yok) |

⚠ **`CLAUDE.md` §6'nın "`lora_B` abs-sum kontrolü regresyon testinde"
cümlesi yanlış.** I1.1, projenin bütün C′ sonuçlarını bir kez geçersiz kılan
hatanın (`lora_B=0`, gradyan adımı atılmıyor) bekçisi olarak tasarlanmış ve
uygulanmamış. Şu an "eğitim oldu mu" yalnız dolaylı işaretlerden
(`n_pairs_trained>0`, `adapter_present`) çıkarılıyor — o hata ikisini de
geçerdi.

**Düzeltilmedi.** Ayrı karar.

### Bulgu 3 — `shuffle`'ın %50 yazı-turasının **kaydı yok**, ve kolun gücü seed'e göre oynuyor

`shuffle_preference_pairs` her çift için bağımsız yazı-tura atıp %50
olasılıkla `chosen`↔`rejected` değiştiriyor. Kodun içine `f8aabf3`
(2026-08-06, Cursor ortak-yazarlı, "Sinyal v2" toplu commit'i) ile girmiş;
**commit mesajı shuffle'dan hiç bahsetmiyor.** `DECISIONS.md`'de shuffle'a
değen üç kayıt var (GAP-11 seed determinizmi, D-032 `replace`'e geçiş,
sonuç raporları) ve hiçbiri bozulmanın **oranını** konu etmiyor.

⇒ D-006'nın taksonomisiyle **"fark edilmemiş kayma"**, "bilinçli sapma" değil.

Gerçekleşen bozulma hesaplandı (`random.Random(seed)`, sevk edilen kural):

| seed | çift | ters çevrilen | net sinyal (birinci mertebeden) |
|---|---|---|---|
| 2001 | 47 | 20 (%42.6) | **+%14.9** → shuffle *hafifçe lived gibi* |
| 2002 | 41 | 20 (%48.8) | **+%2.4** → shuffle *neredeyse null gibi* |
| 2003 | 38 | 23 (%60.5) | **−%21.1** → shuffle *anti-lived* |

Kontrol kolunun gücü seed'den seed'e **+%15 ile −%21 arasında** salınıyor.
Hiçbir kapı bunu denetlemiyor (I2.3 yalnız "özdeş değil" diyor). `lived −
null`'ın 3/3 tutarlı, `lived − shuffle`'ın tutarsız çıkması bununla
tutarlı: null sabit çapa, shuffle oynak hedef. Ve seed 2003'te — shuffle en
çok bozulmuşken — `lived − shuffle` **negatif** çıkmış.

**Değiştirilmedi.** Öneri: yazı-tura kalksın, çiftlerin **tamamı** ters
çevrilsin ⇒ sabit ve tam kuvvetli kontrol. Bedeli: `lived − shuffle`
tabanı yine sıfırlanır. Ayrı D-kaydı ister.

---

### Kabul edilen mimari sınır (ölçümün değil, tasarımın)

Koşum `transfer_to_heir` ile **tek ata → tek varis** ilerliyor; popülasyon,
ölen soy, farklı üreme yok. `F_agent` ajanın **üreyip üremeyeceğine** karar
vermiyor, yalnız hangi anıların kopyalanacağını ağırlıklandırıyor.

⇒ Aktarım mekanizması **Lamarckçı**, Darwinci değil. Kodun içindeki
*"natural selection over engrams"* ifadesi bir metafor ve mekanizmayı
karşılamıyor. `F_agent` düzeltilse bile bu değişmez: seçilim için
çeşitlilik + **farklı hayatta kalma** + kalıtım gerekir, ikincisi yok.

Bu bir hata değil, kapsamdır — ve D-014'ün "hedef N nesil" yönü bu boşluğun
doğal evi. Kayda geçiyor ki ön-kayıt "yaşam neyin miras kalacağını seçer"
gibi savunulamaz bir cümle yazmasın.

### Ölçümün sınırları

3 seed · tek makine · tek GPU (RTX 4070 Laptop 8GB) · greedy · gen1=50,
gen2=20 olay · tek şekil. Tekrarlanabilirlik **bu** shape ve donanımda
gösterildi. `lived−null`'ın 3/3'ü **hipotez testi değil**; N=3'te işaret
testinin verebileceği en küçük p 0.25.

⚠ **Seed 2001–2003 bundan sonra yakılmış sayılır.** Sonuçlarına bakıldı ve
bu kayıttaki bulgular onlardan türetildi; doğrulayıcı bir analize
giremezler. Ön-kayıtlı koşum **seed 2004'ten** başlamalıdır.

**Reddedilen alternatif:** ikinci koşumu N'i 6'ya çıkarmak için kullanmak.
Aynı seed'lerin tekrarı **bağımsız gözlem değildir**; N hâlâ 3, yalnızca iki
kez doğrulanmış.

---

## D-043 · 2026-08-11 · D-039…D-042 sonrası kontrol koşumu: **20/20**, ve bir hipotezim çürüdü

**Durum:** kabul edildi (ölçüm kaydı)

**Karar:** Dört alet değişikliğinden (D-039 I1.1, D-040 shuffle, D-041 I4.1,
D-042 konum bağımsızlığı) sonra aynı şekil yeniden koşuldu:
`dau_runs/control_d042_n3_local.json`, N=3, seed 2001–2003, gen1=50, gen2=20,
`--lora`, greedy. **`run_quality=clean`, 20 değişmezin 20'si geçti.**

Yakılmış seed'lerin doğru kullanımı: 2001–2003 doğrulayıcı analize giremez
ama regresyon testi olarak birebir bunun içindir.

### Sonuç 1 — D-042 yalnız dokunması gereken yere dokundu

| seed | kol | ΔPE | digest | D-038 ile | `lora_B` Δ |
|---|---|---|---|---|---|
| 2001 | lived | +0.03329 | `14995989b4e4` | farklı | 7.845 |
| 2001 | **null** | +0.02962 | `9f8dccac593d` | **AYNI** | — |
| 2001 | shuffle | +0.04038 | `b898592bfe44` | farklı | 7.886 |
| 2002 | lived | −0.01693 | `83299de1f106` | farklı | 7.805 |
| 2002 | **null** | −0.03518 | `04a562a2179e` | **AYNI** | — |
| 2002 | shuffle | −0.04394 | `b2ae6175fc6d` | farklı | 7.789 |
| 2003 | lived | +0.01525 | `c4acb8b03bd9` | farklı | 6.907 |
| 2003 | **null** | −0.05656 | `766b34931ad5` | **AYNI** | — |
| 2003 | shuffle | +0.01452 | `01ca5a8f7e10` | farklı | 6.913 |

**Üç null kolunun üçü de byte düzeyinde D-038'deki gibi; altı eğitim kolunun
altısı da farklı.** Tahmin edilen desenin tamı: null hiç eğitmediği için
`lora_B=0` kalıyor, dolayısıyla `lora_A`'nın nereden geldiği ona ulaşamıyor.

Ayrıca iki bağımsız ölçüm üst üste bindi: D-042'nin doğrulama sondası
seed 2001 için `14995989b4e4` (lived) ve `b898592bfe44` (shuffle) vermişti;
tam koşum ikisini de birebir üretti.

### Sonuç 2 — iki yeni kapı çalışıyor

- **I4.1:** `replay bit-identical (14995989b4e4)`. İlk kez otomatik geçti.
  Bir önceki koşumda ayrışma bildirip koşumu öldürmüştü ve **haklıydı** —
  D-042 o ayrışmanın sebebiydi.
- **I1.1:** `6 train arms moved lora_B; null arms unread`. Eğitim kollarının
  `Σ|lora_B|` deltası 6.9–7.9; null kolları okunmamış (doğru semantik).
- `prompt_skipped_no_record = 0`, çift sayıları 47/41/38 korundu.

⚠ `pairs_passed=299`, D-038'de 252'ydi. Fark tam olarak I4.1 replay kolunun
47 çifti (252+47). Sayaç koşum-global; filtrede değişiklik yok. Bir sonraki
okuyan bunu filtre değişikliği sanmasın.

### Sonuç 3 — sinyal, ve **çürüyen hipotez**

| Karşılaştırma | 2001 | 2002 | 2003 | ortalama | sd | gözlenen d_z |
|---|---|---|---|---|---|---|
| `lived − null` | +0.0037 | +0.0182 | +0.0718 | **+0.0312** | 0.0359 | +0.87 |
| `lived − shuffle` | −0.0071 | +0.0270 | +0.0007 | +0.0069 | 0.0179 | +0.39 |

`lived − null` **3/3 pozitif** — D-038'deki yönle aynı, düzeltilmiş aletle.

⚠ **`lived − shuffle` hâlâ tutarsız.** D-042'yi bulduğumda *"bu, `lived −
shuffle`'ın tutarsızlığını açıklıyor olabilir; null hiç eğitmediği için o
karşılaştırma bağışık"* demiştim. **Ölçüm bu hipotezi desteklemedi.** Konum
confound'u gerçekti ve düzeltilmesi kendi başına doğruydu, ama tutarsızlığın
sebebi o değildi. Sebep hâlâ bilinmiyor.

Gözlenen d_z'ler **hedef değildir** ve N seçmek için kullanılamaz (§2.7);
n=3'te d_z'nin belirsizliği devasa. Bağlam olarak kayda geçiyorlar.

### Ölçümün sınırları

3 seed · tek makine · tek GPU · greedy · gen1=50 / gen2=20 · tek şekil.
N=3'te işaret testinin verebileceği en küçük p = 0.25, yani **hiçbir sonuç
anlamlı değil ve olamaz**. Bu koşumun işi sinyal değil **alet doğrulaması**;
o işi yaptı.

⚠ Seed 2001–2003 yakılmış durumda (D-038). Ön-kayıtlı koşum **2004'ten**
başlar.

**Reddedilen alternatif:** bu koşumu yeni taban saymak. Değil — alet dört kez
değişti ve bu koşum onun regresyon testi. Taban, ön-kayıt kilitlendikten
sonra taze seed'lerle kurulur.

---

## D-044 · 2026-08-11 · ΔPE uç noktası **kayıplı**: ayrımın %80–86'sı ortalamada iptal oluyor

**Durum:** kabul edildi (ölçüm kaydı) · **Keşifsel, ön-kayıtlı değil**

**Karar (A1):** D-043'ün `lived − shuffle` sayıları küçük ve tutarsız
görünüyordu. İki okuma uyumluydu: etki gerçekten küçük, ya da **uç nokta onu
ortalamada yok ediyor.** Ayırt etmek için yeniden koşum gerekmedi — koşum her
kolun 50 olaylık `pe_after_list`'ini ve karar hash'lerini saklıyor
(D-036'nın getirdiği alan). **GPU maliyeti sıfır.**

Bu soruyu kilitten önce sormanın sebebi D-036: uç nokta 50 olaylık fazın ilk
beşte birini okuyordu ve kimse fark etmemişti. O da bir uç nokta sorunuydu ve
geç bulunmuştu.

### Ölçü: iptal oranı

Her seed ve kol çifti için, faz-2'nin olay olay:

```
raw      = ortalama |pe_A[i] − pe_B[i]|      (kollar olay bazında ne kadar ayrı)
endpoint = |ortalama (pe_A[i] − pe_B[i])|    (ön-kayıtlı istatistiğin gördüğü)
kept     = endpoint / raw
```

| seed | çift | farklı karar | raw | endpoint | **kept** |
|---|---|---|---|---|---|
| 2001 | lived−null | 18 | 0.08985 | 0.00368 | **4.1%** |
| 2001 | lived−shuffle | 20 | 0.06476 | 0.00709 | **10.9%** |
| 2001 | shuffle−null | 23 | 0.10088 | 0.01076 | 10.7% |
| 2002 | lived−null | 44 | 0.10366 | 0.01824 | **17.6%** |
| 2002 | lived−shuffle | 43 | 0.08706 | 0.02700 | **31.0%** |
| 2002 | shuffle−null | 20 | 0.07295 | 0.00876 | 12.0% |
| 2003 | lived−null | 39 | 0.19365 | 0.07180 | **37.1%** |
| 2003 | lived−shuffle | 34 | 0.09392 | 0.00073 | **0.8%** |
| 2003 | shuffle−null | 41 | 0.17265 | 0.07108 | 41.2% |

**Ortalama korunan pay: `lived−null` %19.6 · `lived−shuffle` %14.2 ·
`shuffle−null` %21.3.** Yani ayrımın **%80–86'sı ortalamada iptal oluyor.**

En çarpıcısı seed 2003 `lived−shuffle`: uç nokta **+0.00073** diyor, yani
"neredeyse hiç fark yok". Ham ayrım **0.094** — olay başına ortalama fark,
`lived−null`'ınkinden bile büyük. **%99.2'si iptal ediyor.**

### İptal simetrik, yapılı değil

Fark işaretlerinin pozitif payı dokuz satırda **%44–64** (rastgeleye yakın),
ve ilk 25 / son 25 olay ortalamaları arasında tutarlı bir eğilim yok.

⇒ Adapter, ajanın **neye şaşırdığını yeniden düzenliyor**, ortalama şaşkınlık
düzeyini sistematik olarak kaydırmıyor. Faz ortalaması bu farka **yapı gereği
kör.**

### Ne anlama geliyor, ne anlama gelmiyor

**Birincil uç noktayı tehdit etmiyor.** §3'ün birinciliği doğum-drift
büyüklükleri — transfer anında ölçülen bir vektör, olaylar üstünde ortalama
yok, dolayısıyla bu iptal mekanizması ona uygulanamaz. Bu bulgu birinciliği
doğum-driftte tutma kararını **destekliyor**.

**Etkilediği: ΔPE, yani §4'ün S3 ikincili.** Ve §11'in "teşhis edilebilir
null" şartı için kritik: S3 null çıkarsa artık biliyoruz ki bu **düşük
duyarlıklı bir ölçüm**, "etki yok" kanıtı değil. Bu, ilan edilmiş sınır
olarak §8'e giriyor (L9).

**D-043'ün bir cümlesi yumuşuyor** (kayıt append-only): orada `lived −
shuffle`'ın tutarsızlığı "sebebi hâlâ bilinmiyor" diye kaydedilmişti.
Sebebin en az bir parçası bulundu — uç nokta ayrımın %86'sını atıyor. Seed
2003'ün "+0.0007"si küçük etki değil, **iptal artefaktı.**

### ⚠ Bu ölçümden yeni bir uç nokta seçilmiyor

`|ortalama mutlak fark|` bu veride çok daha büyük bir etki gösteriyor. **Onu
uç nokta yapmak tam olarak §2.7'nin yasakladığı post-hoc tuning olurdu** ve
yapılmadı.

İlkesel bir argüman kurulabilir — aksiyomun iddiası *"ajan farklı şeylere
şaşırır hale gelir"* ise yörünge tabanlı bir uç nokta daha uygun olur. Ama
⚠ **bu argümanı bu ölçüm sayesinde düşündüm**, ve bunu saklamak dürüst
olmazdı. Temiz yol: bu ön-kayıtta S3'ün duyarsızlığı **sınır olarak ilan
edilir**, yörünge tabanlı uç nokta **bir sonraki ön-kayıta** ve taze veriye
bırakılır.

**Reddedilen alternatifler:**
- *Uç noktayı şimdi değiştirmek* — post-hoc, yukarıdaki gerekçe.
- *Bulguyu görmezden gelmek* — S3 null çıkarsa teşhis edilemez null üretirdi,
  ki D-002 tam olarak ondan kaçmak için yazılmıştı.

**Sınırlar:** 3 seed · tek koşum · yalnız gen1 faz-2. Gen2'nin `mean_pe`'si
(S4 ikincili) aynı iptal riskini taşıyor olabilir, **ölçülmedi.**

---

## D-045 · 2026-08-11 · Gen2 `mean_pe` de kayıplı — S4, S3 ile aynı sınırı taşıyor

**Durum:** kabul edildi (ölçüm kaydı) · **Keşifsel, ön-kayıtlı değil**

**Karar (A5):** D-044 kendi sınırlar satırında açık bırakmıştı: *"Gen2'nin
`mean_pe`'si (S4 ikincili) aynı iptal riskini taşıyor olabilir,
**ölçülmedi**."* Ölçüldü. Yeniden koşum gerekmedi — `Gen2Result.pe_list`
20 olayın tamamını saklıyor. **GPU maliyeti sıfır.**

Ham çıktı: `dau_runs/exploratory_gen2_endpoint_sensitivity.json`.

### Önce iki ön koşul, varsayılmadı — ölçüldü

1. **Kollar olay bazında karşılaştırılabilir mi?** `run_gen2_measure`
   varis koşmadan önce `_lock_seeds(seed)` çağırıyor (GAP-12). Üç kolun
   `rng_digest`'i **üç seed'de de aynı** ⇒ olay *i* üç kolda aynı durum.
   Aynı olmasaydı satır anlamsız olurdu; script bunu kontrol edip atlıyor.
2. **`mean_pe` gerçekten `pe_list`'in ortalaması mı?** Dokuz kolun
   dokuzunda `|fark| < 1e-12`. Rapor aleti tekrar etmiyor (§2.8).

### Sonuç: evet, aynı sınır geçerli

| çift | **gen2 kept** | gen1 faz-2 kept (D-044) |
|---|---|---|
| `lived−null` | **%17.5** | %19.6 |
| `lived−shuffle` | **%41.6** | %14.2 |
| `shuffle−null` | **%20.9** | %21.3 |
| **dokuz satırın ortalaması** | **%26.7** | %18.4 |

`lived−null` iki nesilde neredeyse aynı: **%17.5 / %19.6.** Gen2'nin uç
noktası da ayrımın çoğunu atıyor ⇒ **S4 null çıkarsa "etki yok" değil
"ölçemedik" demektir**, S3 ile aynı şekilde.

Gen2'nin toplamda biraz daha fazlasını koruması (%26.7 / %18.4) beklenen
yönde: ortalamada 20 terim var, 50 değil — iptal edecek daha az yer.
`lived−shuffle`'ın %41.6'sı **tek başına okunmamalı**: üç seed'in değerleri
%61.4 · %35.6 · %27.9, yani yayılım ortalamadan büyük, N=3.

### Gen2'nin iptali gen1'inki gibi **değil** — ve bu beklenmiyordu

D-044 gen1'de iptali "simetrik, yapısız" bulmuştu: işaretlerin %44–64'ü
pozitif, ilk yarı/son yarı arasında tutarlı eğilim yok. Gen2'de yarı-bölme
çok daha büyük: bağımsız altı karşıtlığın **beşinde** ikinci yarı birinciden
daha pozitif, kayma **0.056–0.155**. Gen1'de aynı sayı 4/6 ve kayma
**0.003–0.070** — bir büyüklük mertebesi küçük. (Gen1 rakamı bu oturumda
yeniden türetildi, D-044'ten devralınmadı.)

**Üç çift bağımsız değil** — `lived−null` = `(lived−shuffle) + (shuffle−null)`
tam olarak, yani seed başına 3 değil **2** bağımsız karşıtlık var. "9 satırın
8'i" diye sayılmadı.

Kol bazında ayrıştırınca kaynak görünüyor:

| seed | `lived` kayması | `null` kayması | `shuffle` kayması |
|---|---|---|---|
| 2001 | **+0.032** | **−0.254** | −0.099 |
| 2002 | **+0.059** | **−0.143** | −0.086 |
| 2003 | −0.089 | −0.098 | −0.019 |

Yani ortak bir zaman eğilimi değil: iki seed'de `null` varisinin PE'si
yaşamın ikinci yarısında **çöküyor**, `lived`'inki çökmüyor. Üçüncü seed'de
üçü birlikte düşüyor.

⚠ **Bu bir iddia değil, bir gözlem.** N=3, 2/3 seed, tek koşum. Ama
mekanizma adayı var ve ikisi de zaten açık GAP: **GAP-19** (faz-1 ve faz-2
anıları aynı sayaç uzayını paylaşıyor ⇒ Ebbinghaus decay varisin yaşamı
boyunca farklı işliyor) ve **GAP-3** (varisler boş `delta_log` ile doğuyor).
→ **A6 ve A7'ye girdi olarak kaydedildi**, burada karara bağlanmadı.

**Ayrım büyümüyor:** `|delta|`'nın son yarı / ilk yarı oranı dokuz satırda
0.61–1.40 (tek istisna seed 2001 `lived−shuffle` 15.35x, çünkü ilk yarıda
ayrım zaten 0.011'di). Kollar yaşam boyunca giderek **açılmıyor**; ayrım
baştan var, sırası değişiyor.

### Yan bulgu: D-042 için bağımsız kanıt

Robustluk için `baseline_d037` ve `repro_d038` de okundu. İkisi gen2
`pe_list` düzeyinde **birebir aynı** ⇒ D-037'nin determinizm düzeltmesi
gen2'de de tutuyor (D-038 bunu gen1 digest'inde göstermişti, gen2
yörüngesinde değil).

Ve seed 2001'de: **`baseline_d037.shuffle`'ın gen2 `pe_list`'i,
`control_d042.lived`'inkiyle bit düzeyinde aynı.** D-042 öncesi 3. sıradaki
kol, düzeltme sonrası 1. sıradaki kolun yörüngesini üretiyordu — etiket ile
muamele birbirinden kopmuştu. D-042 bunu gen1 `arm_digest`'inde ölçmüştü;
bu, aynı kusurun **gen2 yörüngesinde** bıraktığı iz. Üç seed'de `null`
kolları her iki dosyada da aynı (D-043 ile tutarlı).

### ⚠ Yine uç nokta değiştirilmedi

Gen2'de de yörünge tabanlı bir ölçü daha büyük etki gösteriyor. D-044'te
olduğu gibi **alınmadı** — ölçümü görüp istatistik seçmek post-hoc tuning
olur (§2.7). Sonraki ön-kayıta ve taze veriye bırakıldı.

**Reddedilen alternatifler:**
- *S4'ü ön-kayıttan çıkarmak* — ikincil zaten iddia etmiyor, ve çıkarmak
  duyarsızlığı belgelemek yerine gizlerdi.
- *`null` kolunun çöküşünü şimdi kovalamak* — N=3'lük bir gözlemden kilit
  öncesi kod değişikliği çıkarmak tam olarak §2.10'un uyardığı kuyu. A6/A7'ye
  girdi olarak yazıldı.
- *Gen2 uç noktasını yörünge tabanlısıyla değiştirmek* — post-hoc.

**Sınırlar:** 3 seed · tek koşum (`control_d042_n3_local`, `run_quality=clean`)
· 20 olay · yalnız `lived/null/shuffle` üçlüsü. Yarı-bölme gözlemi
**hipotez testi değil**; 2 bağımsız karşıtlık × 3 seed ile hiçbir güç iddiası
kurulamaz.

---

## D-046 · 2026-08-11 · A3: üç eksik kapı yazıldı, biri **spec'iyle yazılamadı**; GAP-6 kapandı

**Durum:** kabul edildi · **Onay:** Yasin, üç seçenekli soru, 2026-08-11
**Commit:** `8bc996b` (kapılar) · `b66f7fc` (GAP-6)

**Karar (A3):** `PREFLIGHT_INVARIANTS.md` 25 değişmez tanımlıyordu, kodda 20
vardı. Eksik beşin üçü (I1.3/I1.4/I1.5) bu adımın konusuydu. Üçü de yazıldı
ama **hiçbiri belgedeki haliyle yazılamadı** — ve sebepleri farklı.

### I1.4 — spec'i bir tautoloji, yazılmadı

Belge: *"`PE ≥ SNR_FLOOR` olan çiftlerin oranı ≥ eşik."* O metin, marj
testinin çift kurulduktan **sonra** uygulandığı zamandan kalma. **D-030
testi `build_pe_ranked_pairs`'in içine taşıdı** ⇒ eğitime ulaşan her çift
eşiği yapı gereği geçiyor, oran **daima 1.0**. Spec'e sadık kalınsaydı
repoya hiçbir koşulda kırılamayan bir bekçi girerdi — §2.4'ün U7/A2'de
yakaladığı şeyin aynısı.

D-030'dan sonra ayakta kalan ölçülebilir soru: **aday havuzunun ne kadarı
atıldı.** Ölçülen (`control_d042`): 3714/7983 aday marjın altında elendi
(**%46.5**), 299 çift hayatta kaldı. Kapı bu oranı **kaydediyor** ve yalnız
dejenere uçta düşüyor — hiçbir çift kalmadıysa. O okumanın yorumlanması
kalibrasyon istemiyor, o yüzden eşik **uydurulmadı**. FLAG.

⚠ §2.11 gereği bu sessizce seçilmedi: belge/kod çelişkisi Yasin'e üç
seçenekle soruldu, "reddetme oranına çevir" onaylandı.

### I1.3 — spec'i I1.1'i tekrar ediyordu, daraltıldı

Belge: *"`step_count > 0`, loss sonlu, `grad_norm > 0`."* Ama I1.1 zaten
`Σ|lora_B|`'nin kımıldadığını okuyor; kımıldadıysa bir adım atılmıştır.
Aynen yazılsa ikinci bir boş bekçi olurdu.

Kapsam, **bir ağırlık okumasının göremeyeceği üç kusura** daraltıldı:
sonlu olmayan loss (ağırlıklar yine değişir — NaN'a), biriktirip hiç
`optimizer.step` çağırmayan döngü, ve **tam sıfır gradyanla atılan adım**.
Testi bu üç şeklin **önce I1.1'i geçtiğini** doğruluyor ⇒ örtüşmenin
olmadığı iddia değil **kanıt**.

⚠ **Sıfır gradyan varsayımsal değildi.** Kapı eklenir eklenmez mevcut DPO
test harness'ı düştü: `_encode_pair_side` stub'ı `chosen` ile `rejected`
için **aynı** kodlamayı dönüyordu ⇒ `policy_chosen − policy_rejected` her
mikro-adımda tam **0**. Yani `test_optimizer_steps_once_per_accumulation_
steps` D-028'den beri **sıfır gradyanla atılan adımları** sayıp eğitim diye
raporluyordu. Stub düzeltildi. **Kapı, kendisini doğrulayacak testi
yazarken bir kusur buldu.**

### I1.3b — yeni, belgede yoktu

`clip_grad_norm_` kırpma öncesi normu zaten hesaplıyor ve **dönüş değerini
atıyorduk**. Saklamak D-029'un açık bıraktığı bir soruyu cevaplıyor: o karar
`DPO_LEARNING_RATE`'i literatürden aldı, ama bu gerekçe **adım boyunu
gradyan belirlediği sürece** geçerli. Her adım kırpılıyorsa boyu tavan
belirler ve kilitlenen lr koşumu tarif etmez. Kaç adımın tavana değdiği
raporlanıyor. **FLAG, ve eşik uydurulmadı** — herhangi bir kırpma etiket
alır, `PAD_FRACTION_MAX`'in katılığı.

### I1.5 — değer config'den türetildi, veriden değil

`MIN_PAIRS`'in kaynağı yoktu. Ölçtüğümüz 47/41/38'den seçmek §2.7'nin
yasakladığı post-hoc tuning. Türetildi:
`MIN_PAIRS = DPO_BATCH_SIZE × DPO_GRADIENT_ACCUMULATION_STEPS` — **bir tam
accumulation grubu**. Sabit yazılmadı: 4 yazılsaydı accumulation değişince
"bir tam grup" demeye devam ederdi (§2.8). Testi tam olarak bunu kırıyor.
`MIN_PAIRS_CALIBRATED = False` yanında duruyor, yerleşmiş gibi okunmasın.

### GAP-6 — brief'in yeri yanlıştı

08-08~ §1 CUDA temizliğini **adapter hot-swap'te** izolasyon şartı sayıyor.
Harfiyen uygulanamazdı: `graph.agent_node` `switch_adapter`'ı **her yerel
kararda** çağırıyor, `empty_cache` bütün allocator'ı geziyor, ve swap
serbest bırakılacak bir şey **ayırmıyor** ⇒ faz başına 50+ allocator gezisi,
karşılığında sıfır. Maliyet, tahsisin yapıldığı yere kondu: DPO adımı.

Altındaki izolasyon kaygısı **gerçek, ama brief'in verdiği sebepten değil.**
Tasarım gereği **tek** bellek-içi adapter slotu var (ajan başına slot
kaydetmek peft'e her adapter'ı her ajanın dizinine yazdırır). Yani bir kolun
eğittiği tensörler, sonraki kolun adapter'ının **yükleneceği** tensörler, ve
bu kolun `.grad`'ı çıkışta hâlâ onlara asılıydı. Kimse okumuyordu — sonraki
`_run_dpo_epochs` epoch döngüsünün başında `zero_grad` çağırıyor — ama bu, A
ajanının izolasyonunu **B'nin çağrı sırasına** emanet eder. Bu projenin iki
sızıntısı da (`f25b0ef`, D-042) tam olarak o şekildi. `None` yapıldı,
sıfırlanmadı: tampon da gitsin.

İkinci ve bağımsız sebep: DPO adımı koşumun tepe noktası, D-034 pilotu zaten
bir OOM uyarısı basmıştı.

Swap'in süre logu **düzeltilmedi, etiketlendi**: host tarafı dispatch
ölçüyor, GPU tamamlanmasını değil. Doğru yapmak her-karar yolunda
`synchronize` ister; bir debug satırını keskinleştirmek için pipeline'ı
durdurmak kötü takas. Ne ölçtüğünü yazmak dürüst olan (§2.8).

**Mutasyon kontrolü — altı mutasyon, altısı da testini kırdı:**
sıfır gradyan tolere edildi · `MIN_PAIRS` 4'e sabitlenip accumulation 8
yapıldı · `grad_norm` yine atıldı · I1.4 tautolojiye döndürüldü · grad
release kaldırıldı · temizlik `switch_adapter`'a bağlandı.

**Reddedilen alternatifler:**
- *I1.4'ü spec'iyle yazmak* — kırılamayan bekçi.
- *I1.4'ü hiç yazmayıp belgede işaretlemek* — eğitim açlığını gören kapı
  kalmazdı; ölçüm o riskin gerçek olduğunu gösteriyor (%46.5 eleme).
- *`MIN_PAIRS`'i 38'den (en düşük gözlem) seçmek* — post-hoc.
- *I1.3'ü spec'iyle yazmak* — I1.1'in kopyası.
- *`empty_cache`'i `switch_adapter`'a koymak* — brief'in dediği, ölçülen
  maliyeti karşılıksız.

**Sınırlar:** I1.3b, I1.4, I1.5 üçü de **FLAG** ve **kalibre değil**;
ABORT'a yükseltilmeleri pilot ister (§"Kalibre edilmesi gereken eşikler").
I1.4'ün oranı tek koşumdan (`control_d042`) okundu, eşik olarak
**kullanılmadı** — yalnız kapının dejenere ucu sabit. Kapıların hiçbiri
canlı GPU koşumunda henüz ateşlenmedi; ilk gerçek sınav B2.

**Değişmez sayısı: 20 → 24** (I1.3, I1.3b, I1.4, I1.5). Belgede tanımlı
25 → 26 (I1.3b yeniydi). Kodda hâlâ yok: I1.2 (testte), I2.3 (yapısal).

---

## D-047 · 2026-08-11 · DR #1 işlendi: S4 kapandı, ama S1'in bağımsız olmadığı çıktı

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-11) · **GPU'suz**
**Mutabakat:** `docs/research/RECONCILIATION.md` bölüm **G**

### S4 kapanıyor — cevaplanarak değil, **çözülerek**

DR #1'in asıl katkısı bir `d_z` sayısı vermek değil, S4'ü **cevaplanması
gereken bir soru olmaktan çıkarmak**: Lakens (2022), *Sample Size
Justification*, Collabra: Psychology 8(1):33267 — **bütçe-kısıtlı örneklem
gerekçelendirmesi** altı meşru yöntemden biri. Literatürde birinciliğimizin
karşılığı olan bir etki yokken SESOI uydurmak, bütçeyi şeffaf ilan edip
duyarlılık analizi vermekten **daha az** dürüst.

⇒ **SESOI ilan edilmiyor.** Yerine: bütçe beyanı + duyarlılık analizi (MDE)
+ `p > 0.05` durumunda "şu MDE'nin altında güçsüzüz, veri o bantta bilgisiz"
dili. Bu, L9/L10'un ΔPE ikincilleri için zaten yazdığının birincile
taşınması.

MDE aritmetiği yerel doğrulandı (exact noncentral-t): DR'nin `N=32` için
verdiği **0.512 / 0.450**, hesaplanan **0.5113 / 0.4495**. Üç hane doğru.

### DR'nin iki dayanağı düştü

**`r ≥ 0.85` geçersiz, iki ayrı sebeple.** DR "koşum-arası gürültü sıfır
(sha256 özdeş) ⇒ `r ≥ 0.85` ⇒ `d_z=0.512` aslında `d≈0.28`" diyor.
(a) Determinizm **aynı kolu tekrar koşmanın** gürültüsünü sıfırlar; farklı
kolların **seed'ler arası** korelasyonu hakkında hiçbir şey söylemez.
(b) Daha temel: birinciliğimiz iki kolun eşleştirilmiş ölçümü **değil**, iki
mesafenin farkı (`a_s − b_s`, §3) ⇒ `d_z = d/√(2(1−r))` dönüşümü bu forma
**uygulanamaz**. Yakılmış üç seed'de `corr(a_s,b_s) = −0.80` (N=3, kendisi
anlamsız; işaret bile ters).

**Literatür bandı `d_z ≈ 0.85–1.70` kaynaksız.** Brief "yazar+yıl+yer" şart
koşmuştu; yalnız "ProtoAlign"/"Anchor Bias" adları geçiyor. Aynı rapor
yayın yanlılığının medyanı %50–100 şişirdiğini söyleyip bu bandı dayanak
yapıyor — **kendi içinden çürüyor** (Meehl 1990 argümanıyla).

Ayrıca kullanılmayanlar: Eleştiri 2 savunması (*"iptal, birincilin saf
parametrik iz olduğunu doğrular"* — non sequitur; D-044'ün gerçek argümanı
"tehdit etmiyor"du, "doğruluyor" değil) · şablonun birebir metni (0.512'nin
yanındaki formül 0.4953 verir; "her seed 3 koşum" yanlış, seed başına 3
**kol** var).

### ⚠ Bir önceki çerçeveleme düzeltiliyor

Oturum içinde önce *"birincil uç noktanın kendisinde yapısal kusur"* dendi.
**Fazlaydı.** `update_drift` (`drift.py:41`) `flags[domain]=True` ile
`magnitudes[domain]`'i **birlikte, yalnız travma anında** yazıyor ⇒
"bayraklanmamış alan = 0" bir kolaylık kabulü **değil, doğru**: o alanda
travma yoksa birikmiş büyüklük gerçekten sıfırdır. Seed 2002'de bayrak
uyuşmazlığının büyük L2 mesafesi üretmesi kusur değil — `lived` sosyal,
`null` belirsizlik alanında yaralanmış, ve bu gerçek bir fark.

### Geriye kalan iki bulgu — ikisi de ilan edilen sınır oldu

**1. S1 bağımsız bir ikincil değil (L11).** Ölçüldü: 11 dosyadaki **69
transfer kaydının 69'unda** `flags` ile `magnitudes` anahtar kümeleri
**özdeş**, hiçbir bayrak `False` değil. ⇒ S1 (*"bayraklanan alan kümesi"*)
= `set(magnitudes.keys())` = birincilin girdi vektörünün **desteği**.
Korelasyon değil **türetilebilirlik**. Birincil bir bayrak farkı üzerinden
anlamlı çıkarsa S1 aynı olguyu ikinci kez ölçer, ama §4 onu ayrı uç nokta
ilan ettiği için raporda **destekleyici kanıt** gibi okunurdu.
⇒ §11'e yazıldı: S1 birincili desteklemez, **ayrıştırır**.

**2. `resource` atıl (L11).** Dokuz kolun tamamı `3.6404 … 3.7414` (yayılım
düzeyin %2.7'si), seed 2001'de üç kolda birebir aynı. L1'in `F_agent` için
yazdığının aynısı. Birinciliğin ayrımı pratikte **ikinci alandan** geliyor.

**3. Şeffaflık borcu ödendi (L12).** Bu denetim yapılırken `a_s − b_s`'in
**işareti görüldü**. Seed 2001–2003 D-038 ile zaten yakılmıştı ve
doğrulayıcı koşum 2004'ten başlıyor (§6) ⇒ doğrulayıcı analiz kirlenmedi.
Ama kayda geçer, ve **uç nokta tanımı bu bilgi alındıktan sonra
değiştirilmedi** — değiştirilse post-hoc olurdu. L11'in "tanım değişmedi"
notu buraya bağlı.

**Reddedilen alternatifler:**
- *DR'nin `N=32`'sini şimdi kilitlemek* — G13 uzlaşmadı: GAP-9'un dayandığı
  `protocol-c-metacognition-eval` Protocol C için **N=40–50** diyordu.
  İki sayı karşılaştırılmadan S2 kapanmaz.
- *Birinciliği bayrak/büyüklük diye ikiye ayırmak* — L12'den sonra post-hoc.
- *S1'i ön-kayıttan çıkarmak* — bağımlılığı belgelemek yerine gizlerdi;
  ayrıştırma olarak raporlamak daha bilgilendirici.
- *`resource`'u uç noktadan atmak* — post-hoc, ve atıllığı ilan etmek
  (L1 deseni) hem dürüst hem ucuz.

**Sınırlar:** L11'in iki bulgusu **yapısal** (koda bakılarak türetildi, 69
kayıtla doğrulandı) ⇒ N'e bağlı değil. Ama `resource`'un atıllığı **üç
seed'den** okundu; daha geniş N'de ayrım üretmesi dışlanmadı. S2 (N) **açık
kalıyor**.

---

## D-048 · 2026-08-11 · DR #2 işlendi: GAP-18'in dayandığı sayı iki ayrı koşumdan birleştirilmiş

**Durum:** kabul edildi · **GPU'suz** · **Commit:** `daa5f4b`
**Mutabakat:** `docs/research/RECONCILIATION.md` bölüm **H**

### ⚠ Asıl bulgu raporda değil, kendi brief'imizde

`2026-08-11_GAP18-...md` şunu yazıyordu:

> Ölçülen: **47 çiftlik** bir eğitim setinde **47 farklı prompt**, ama yalnız
> **2 benzersiz `rejected`** metni.

İki sayı **aynı koşumdan gelmiyor**:

| Sayı | Kaynağı |
|---|---|
| 47 çift / 47 prompt | `control_d042_n3_local`, seed 2001, **50 olay** |
| 2 benzersiz `rejected` | `exploratory_pair_design_replay`, seed 2001, **10 olay** — yaşamda **toplam 7 benzersiz completion**, tasarım **9 çift** üretmişti |

**47 çiftte benzersiz negatif sayısı hiç ölçülmedi.** Ve ölçüm noktası
kaydı: aynı koşumlar `n_unique` **29 · 22 · 27** veriyor — D-034 zaten
*"7-benzersiz tavanı açıldı"* diye yazmıştı. 29 completion'dan çekilen
negatif havuzu 7'den çekilenle aynı havuz değil.

Bu §2.8'in klasik kipi: **rapor aleti takip etmedi, iki aletin çıktısını
birleştirdi.** Ve bu sefer maliyeti dışarı taştı — DR'nin bütün şiddet
zinciri (*"serbestlik derecesi 2'ye iner ⇒ parameter shrinkage ⇒
catastrophic collapse"*) o premisin üstünde duruyor. **Rapor yanılmadı,
yanlış beslendi.**

### Karar: tahmin etme, say

`PAIR_DIVERSITY_STATS` eklendi (`lora_update.py`), çiftlerin kurulduğu yerde
okunuyor, `pair_filter` raporuna giriyor:

- `uniq_rejected` — DR'nin şiddet iddiasının doğrudan öngördüğü sayı
- `uniq_chosen`
- `max_rejected_reuse` — tek bir negatifin kaç çifti domine ettiği
- `texts_in_both_roles` — DR'nin "çelişik gradyan" uyarısı; ayrık
  eşleştirmede olmuştu, `best_by_event`'te olup olmadığı **bilinmiyordu**

Sonradan JSON'dan yeniden türetilmiyor: ikinci bir yeniden kurulum, aletle
ikinci bir anlaşmazlık şansıdır — bu sayının brief'e girme şekli tam olarak
oydu.

### Raporun alınan kısımları

- **H3 ⭐ Shuffle kolu loss testi.** *"Shuffle belirgin biçimde daha yüksek
  loss üretmezse model tercih içeriğini değil düzenlileştirmeyi
  öğrenmiştir."* Bizde shuffle var (D-040) ama **loss karşılaştırması hiç
  yapılmadı**. D-046 `dpo_loss`'u kol bazında JSON'a yeni koymuştu ⇒ **B2'de
  ek maliyetsiz gelecek.** Ön-kayıta alınabilir bir yanlışlama testi.
- **H2 Kolay negatifler ≈0 gradyan üretir** — mekanizma doğru, ve D-046'nın
  I1.3'ü (`dpo_grad_norm_min`, sıfır gradyan ⇒ ABORT) ile I1.3b'si (kırpma
  oranı) bunu **zaten görünür kıldı**. İki iş bağımsız çıkmış ama aynı yere
  bakıyor.
- **H4/H5 doğrulama:** 40 çiftte 1 epoch doğru (S5), `lr=1e-6` politikayı
  referans yakınında tutuyor (D-029). İkisi de bizim kararımızı destekliyor.

### Kaynak kimlikleri — dördü sağlam, altısı değil

**Doğrulandı:** Rafailov ve ark. 2023 (DPO) · Ethayarajh ve ark. 2024 ICML
(KTO) · Meng ve ark. 2024 NeurIPS (SimPO) · Kulesza & Taskar 2012 (DPP).

**Düştü:**
- **Distinct-N → "Papineni ve ark., 2002"** ❌ Papineni 2002 **BLEU**'dur;
  Distinct-N **Li ve ark., 2016**.
- **Self-BLEU → "Papineni ve ark., 2002"** ❌ Self-BLEU **Zhu ve ark., 2018
  (Texygen)**.
- **Cal-DPO → "Xu ve ark., 2024"** ⚠ NeurIPS 2024'te **Xiao ve ark.**
- **`nrDPO` (Applied Sciences 2025) · DualLoop-DPO · ExPO 2025 · DQO 2025 ·
  Lanchantin ve ark. 2025** ❌ yazar/başlık yok ⇒ kimlik doğrulanamıyor.
- **"Label Flip Rate > %10 bozar"** ❌ sayısal eşik kaynaksız. Metrik alındı,
  eşik alınmadı.

§9 sicili: yedi iddiadan dördü çürümüştü, sahte `arXiv:2506.08965` de böyle
yakalanmıştı. **Bu brief'te de aynı desen var.**

### Reddedilen alternatifler

- ***KTO'ya geçmek (DR'nin baş tavsiyesi)*** — hizalama algoritmasının
  tamamen değişmesi. Kanal 2'nin mekanizmasını değiştirir, bugüne kadarki
  her ölçümü geçersiz kılar, ve **doğrulanmamış H1 premisine dayanıyor**.
  → sonraki ön-kayıt.
- *Kullanım tavanı (`N≤3`) / marjin bandı / olay başına çok çift* — üçü de
  eğitim setini değiştirir; DR kendi de uyarıyor ki tavan ikincil
  negatifleri `SNR_MARGIN_FLOOR=0.15`'in altına düşürebilir. **Önce ölç.**
- *`best_by_event`'i şimdi değiştirmek* — kilit öncesi, ölçümsüz, §2.10.
- *Sayıyı JSON'dan sonradan türetmek* — yukarıdaki gerekçe.

**Sınırlar:** Hiçbir eşik ve hiçbir çift kurma stratejisi değişmedi; yalnız
aletleme eklendi. Yapısal argüman (**`best_by_event` global maks-PE
completion'ı çoğu çiftin reddedilen tarafı yapar**) ayakta duruyor —
değişen, **şiddetinin ölçülmemiş olduğunun** kayda geçmesi. Sayaçlar canlı
koşumda henüz çalışmadı; ilk gerçek okuma **B2**.

---

## D-049 · 2026-08-11 · DR #3 işlendi: tercih mi bastırma mı, artık her koşum söylüyor

**Durum:** kabul edildi · **GPU'suz** · **Commit:** `985df29`
**Mutabakat:** `docs/research/RECONCILIATION.md` bölüm **I**

### Karar: `Δlogπ(chosen)` ve `Δlogπ(rejected)` ayrı kaydediliyor

Yükselen bir DPO marjı **iki farklı sonuçla** uyumludur: ajan düşük-PE
cevabı tercih etmeye başlamıştır, ya da yüksek-PE olanı **asla söylememeyi**
öğrenmiştir. Aksiyomun kanal 2 için iddia ettiği yalnız birincisi, ve
**marj tek başına ikisini ayıramaz** — ikisi de onu yükseltir.

D-029 bu ayrımı zaten yapmış ve `lr` kararını ona dayandırmıştı:

| lr | `Δlogp_chosen` | `Δlogp_rejected` | okuma |
|---|---|---|---|
| 5e-5 | **−0.123** | **−4.371** | seçilen bile düşüyor ⇒ **saf bastırma** |
| 1e-6 | **+0.085** | −0.143 | **yapıcı tercih** |

⚠ Ama bu **tek seferlik bir probe**ydu (9 çift, 3 optimizer adımı, tek
seed). Gerçek koşumlar bu iki sayıyı **kaydetmiyordu** ⇒ işletim
konfigürasyonu bastırmaya doğru kayarsa hiçbir şey söylemezdi. Artık her
eğitim kolu `dpo_delta_logp_chosen`, `dpo_delta_logp_rejected`,
`dpo_chosen_went_down` raporluyor. İki terim marjın içinde **zaten vardı**;
ayrı tutmak bedava.

**Bu brief tavsiye ettiği için yapılmadı** — kendi kararımızın dayanağı
görünmez olduğu için yapıldı. Brief'in katkısı, bakmamız gereken yeri
bağımsız olarak işaret etmesi.

### Brief'in isabetli çıktığı iki yer

**1. A2'nin tasarımı kusurluymuş (I12).** *"Yaşantı sonrasında anı getirimini
tamamen kapat, yalnız ağırlıklara yansıyanı ölç"* diye tarif etmiştik. Brief
bunun **context starvation / OOD şoku** yarattığını söylüyor: varisin
performans düşüşü ağırlıkların yetersizliğinden değil, **alışılmadık istem
yapısından** gelebilir — adapter eğitim boyunca bağlamda hep anı gördü.
⇒ Ölçtüğümüz şey parametrik kapasite değil, dağılım dışı şok olurdu.

**Alternatifi daha iyi (I13):** *plasebo / karşı-olgusal anı enjeksiyonu* —
getirim kapatılmaz, gelen anıların **içeriği** nötr metinle değiştirilir.
İstem yapısı ve uzunluğu korunur ⇒ OOD şoku yok, anlamsal etki izole.
**A2 sonraki ön-kayıta bu haliyle taşınıyor.**

**2. Kavramsal düzeltme (I3).** *"Ontogenetik uyarlanma"* çerçevemiz
**kısmen** doğruymuş: ontogenez bireyin yaşamı içindedir, ama kazanımların
varise geçmesi ondan **sonraki** adımdır. Doğru terim: **"ontogenetik
kazanımların transjenerasyonel Lamarckçı aktarımı."** B4 raporunda kullanılır.

### ⚠ İki yerde brief'e uyulmadı

**I18 — "ikinci yarı yaşam AUC farkı"nı sonraki birincil yapmak.** *"İkinci
yarı"* tam olarak D-045'te **gözlediğimiz** şey (bağımsız altı karşıtlığın
beşi). Onu bir sonraki ön-kaydın birincili yapmak, post-hoc gözlemi ön-kayıta
taşımaktır — D-044/D-045'in iki kez reddettiği hareket.
⇒ **Genel form (zaman × kol etkileşimi, `β₃`) ilkeseldir ve alınabilir**
— *"etki zamanla değişiyorsa zamanı modelle"* argümanı veriye bakmadan
kurulur. **Özel form ("ikinci yarı") alınmaz.**

**I19 — brief kendi mutabakatını yazmış.** Raporun sonunda *"Mutabakat Metni
(RECONCILIATION.md)"* diye bir bölüm var ve kararları **alınmış gibi**
yazıyor (*"birincil uç nokta FDA olarak tescil edilmiştir"*). Mutabakat
D-006 gereği **bizim** işimiz; bir brief kendi kabulünü ilan edemez.
**Kullanılmadı.**

### Kaynak kimlikleri — üç brief'in en iyisi

**Doğrulandı:** Lenski LTEE · Tierra (Ray, 1991) · Avida (Ofria ve ark.,
2004) · Grefenstette (1991) · Ackley & Littman (1992) · Friston FEP ve
Karanlık Oda (Friston, Thornton & Clark, 2012) · Pathak ve ark. (2017) ·
Houthooft ve ark. (2016) · Ramsay & Silverman (2005) · Lewis ve ark. (2020) ·
ROME (Meng ve ark., 2022) · Rafailov ve ark. (2023).

**Düştü:** **Watson (2002) SEAM** — "tek soy hattı üzerinde birikimli
değişim" diye tarif edilmiş; SEAM simbiyogenetik **modül birleşimi** üzerine
ve **popülasyon** varsayar. Kullanılmadı.
**Eksik:** "Probability Collapse / Logit Suppression" olgusunun **adı**
verilmiş ama **atıf yok** — ad alındı, kaynak alınmadı.

**Reddedilen alternatifler:**
- *EFE epistemik değeri / merak terimi / entropi alt sınırı eklemek* (I10) —
  üçü de **amaç fonksiyonuna** dokunuyor, aksiyomun "trait verilmez"
  yasağına yakın, ve kilit öncesi §2.10'un kuyusu. Sonraki ön-kayıt.
- *Çifte ayrışma protokolünü şimdi kurmak* (I15) — çıta doğru, ama mevcut
  tasarım tek yön ölçüyor; yeni bir kol demek.
- *Activation patching / SAE* (I14) — mevcut aletin çok ötesinde.

**Sınırlar:** Kod değişikliği yalnız **aletleme**; hiçbir eşik, amaç
fonksiyonu veya uç nokta değişmedi. Yeni alanlar canlı koşumda henüz
çalışmadı — ilk gerçek okuma **B2**. I5'in "Lamarckçı aktarım çeşitliliği
yok eder" uyarısı **iki nesilde gözlenemez**; not, kanıt değil.

---

## D-050 · 2026-08-11 · A6: precision kanalı atıl, GAP-5 doğrulandı, GAP-4'ün mekanizması yok

**Durum:** kabul edildi (ölçüm + iki denetim) · **Keşifsel, ön-kayıtlı değil**
**GPU'suz.** Ham: `dau_runs/exploratory_a6_precision_and_channel_audit.json`

### A6'nın sorusu ve cevabı

D-043 `lived − shuffle`'ı tutarsız bulmuştu (−, +, +). D-044 bir parçasını
açıkladı (uç nokta ayrımın %86'sını iptal ediyor). A6 kalanı arıyordu, ve
D-045 bir iz bırakmıştı: `null` varisinin ikinci-yarı PE çöküşü.

**Aday eleme:** PE **precision-ağırlıklı**. Eğer ağırlık kollar arasında
farklı davranıyorsa, tutarsızlık bir **ölçüm artefaktı** olabilirdi.
Ağırlık bölünüp ham PE'ye bakıldı:

| seed | `lived−shuffle` ağırlıklı | ham | işaret |
|---|---|---|---|
| 2001 | −0.00709 | −0.00569 | aynı |
| 2002 | +0.02700 | +0.02241 | aynı |
| 2003 | +0.00073 | +0.00061 | aynı |

**Dokuz karşıtlığın dokuzunda işaret aynı.** ⇒ Tutarsızlık precision
ağırlığından **gelmiyor**. D-045'in `null` varisi çöküşü de ham PE'de
duruyor (−0.234 / −0.148, `lived` +0.007 / +0.012) ⇒ o da artefakt değil.
**Bir aday elendi, mekanizma hâlâ açık.**

### ⚠ Ama eleme yapılırken kilitli bir karar sorgulandı: Precision-PE atıl

`π = clamp(1/(var/VAR_REF + ε), 0.5, 1.2)`, `VAR_REF = 1/12`.
π tavandan **ancak** `var > 0.0694` (SD > 0.263) olunca çıkabilir.

**Ölçülen faz-2 varyansı: 0.0289 … 0.0473** — dokuz kolun dokuzu da eşiğin
**altında**. Tavana yapışma oranı:

| Nerede | π = 1.2 olan olay payı |
|---|---|
| gen1 faz-1 | **%96** (dokuz kolda da) |
| gen1 faz-2 | %84–96 |
| gen1 faz-2, **son 25 olay** | **%100** (dokuz kolda da) |
| gen2, ikinci yarı | **%100** (dokuz kolda da) |

⇒ **Precision-PE, işletim noktasında sabit 1.2 çarpanı.** "Sürpriz sert
salınırken kazancı kıs" mekanizması, olayların büyük çoğunluğunda hiç
devreye girmiyor.

⚠ Bu **kilitli bir karara** dokunuyor: *"Precision-PE v2.4 (rolling history
+ VAR_REF=1/12), kalibrasyon doğrulandı."* Kalibrasyon yanlış değil —
**ilgisiz**: doğrulama bandı bu koşumların ürettiği varyans aralığını
kapsamıyor. §2.11 gereği sessizce seçilmedi, kayda geçiriliyor.

**Değiştirilmedi.** `VAR_REF`'i şimdi oynatmak (a) kilitli bir eşik değeri,
(b) ölçümü gördükten sonra ⇒ post-hoc, (c) bütün koşumları geçersiz kılar.
**İlan edilen sınır** olarak yazılıyor — L1 (`F_agent`) ve L11 (`resource`)
deseninin üçüncüsü.

### GAP-5 — **doğrulandı ve nicelendi**, "olabilir" değil

`SYSTEM_PROMPT`'un son satırı:

> *"Prefer plain English words such as resource, **extract**, **take**,
> **social**, **talk**, or **cooperate** when those actions apply."*

`decision_to_outcome` tam bu kelimelere bakıyor:

| Sınıf | Prompt'un **isimle andığı** anahtar | Toplam |
|---|---|---|
| COOPERATE | `cooperate`, `talk`, `social` | **3 / 4** |
| DEFECT | `extract`, `take` | 2 / 7 |
| CONSERVE → COORDINATE | **hiçbiri** | **0 / 6** |

Prompt, sınıflandırıcının **işbirliği sözlüğünün dörtte üçünü** öneriyor ve
**korunma sözlüğünden tek kelime anmıyor**. `conserve/rest/wait/observe/
restrain/spare` yalnız prompt'un önermediği kelimelerden çıkabilir.

⇒ Davranışsal ölçüm kısmen **prompt'a uyumu** ölçüyor, ajanın eğilimini
değil. Doğrudan **S5**'i (gen2 davranışsal, `decision_to_extraction`)
etkiliyor, ve `OUTCOME_TO_EXTRACTION` üzerinden havuz dinamiğine ve
`F_agent`'ın `delta_pool`'una kadar iniyor.

**Düzeltilmedi:** `SYSTEM_PROMPT` değişirse her koşum geçersiz olur.
**İlan edilen sınır.**

### GAP-4 — tarif edilen mekanizma **yok**

İddia: *"Ebbinghaus ile kasadan silinen anının yarattığı drift LoRA'da
kalıcı kalabilir"* — bir **senkron kopukluğu**.

Read-only denetim: çiftler `build_lived_trace_examples(agent_state,
pe_event_log)`'dan geliyor — kaynak `delta_log` **+ PE olay günlüğü**.
Unutma ise `dau/memory/consolidation.py` ve `retrieval.py`'de, **kasa**
üzerinde çalışıyor. **Çift kurucu kasayı hiç okumuyor** ⇒ kopacak bir
senkron bağı yok.

⚠ Ama **gerçek bir asimetri var** ve adı konmalı: bir anı kasadan
unutulabilir (varis onu miras almaz, getirim yüzeye çıkarmaz) ama o olaydan
türetilmiş DPO çifti **ağırlıkları çoktan eğitmiştir**. Yani **kanal 2
Ebbinghaus'a bağışık, kanal 1 değil.** Bu bir hata değil — "iki kanal"ın
tanımı bu — ama D-002'nin *"ikisi de yaşamın izidir"* cümlesi bu asimetriyi
taşımıyor. İlan edilen sınır.

**Reddedilen alternatifler:**
- *`VAR_REF`/`PRECISION_MAX_WEIGHT` ayarlamak* — kilitli eşik, post-hoc,
  bütün koşumları geçersiz kılar.
- *`SYSTEM_PROMPT`'tan kelime listesini çıkarmak* — aynı gerekçe, ve
  D-032'nin ölçtüğü prompt/çıkarım uyumunu bozar.
- *GAP-4'ü "kapandı" diye yazmak* — mekanizma yok ama asimetri var;
  ikisini ayırmadan kapatmak bilgi kaybı olurdu.

**Sınırlar:** N=3, tek koşum. π tavan doluluğu **yapısal** (formülden
türetildi, dokuz kolda doğrulandı) ⇒ N'e bağlı değil. GAP-5 örtüşmesi
**tamamen statik** (iki sabit listenin karşılaştırması) ⇒ koşumdan bağımsız.
`lived − shuffle`'ın kalan tutarsızlığı **açıklanmadı**; elenen tek şey
precision ağırlığı. N=3'te küçük bir etkinin etrafındaki gürültüden
ayırt edilemez — bunu ancak B2'nin N'i söyler.

---

## D-051 · 2026-08-11 · A7/GAP-19: saat gerçekten kırık, ama birincile giden yolu iki dejenerelik kapatıyor

**Durum:** analiz + öneri · **Kod değişikliği:** yalnız raporlama (`060d907`)
**⚠ GAP-19 kararının kendisi Yasin'in** — burada değiştirilen bir şey yok.

### Mekanizma doğrulandı: sayaç fazlar arasında sıfırlanıyor

`graph.py:869/967` → `clock = EventClock(counter=len(state.event_log))`.
Faz-2 `initial=None` ile başlıyor ⇒ `event_log` boş ⇒ **saat 0'dan sayıyor**.
Yani faz-1 de faz-2 de anılarını `last_activated_counter ∈ [1,50]` ile
yazıyor.

`_consolidate_gen1` ise `counter = len(parent_final.event_log)` = **50**
kullanıyor (faz-2'nin uzunluğu). Ebbinghaus `t = now_counter −
last_activated` hesaplıyor ⇒ faz-1'de 48. olayda son kullanılmış bir anı
`t = 2` görünüyor; **gerçekte üzerinden bir faz + 2 olay geçmiş (t = 52).**

Bu bir ayar sorunu değil, **iki farklı saatin karşılaştırılması** — D-042'nin
sınıfı (karşıtlığın içinde sistematik terim). 5 Yasak #3 zamanı olay sırasına
bağlıyor, ama burada olay sırası **resetleniyor**.

### ⚠ Ama etkisi şu an sıfır — ve sebebi iki ayrı dejenerelik

Kırık saatin birincil uç noktaya ulaşabilmesi için, yanlış hesaplanan
unutmanın **varise geçen şeyi** değiştirmesi gerekir. İki bağımsız halka
bunu kesiyor:

1. **`should_forget` travmayı hiç silmiyor** (`decay.py:60` — `if
   is_trauma(record): return False`). Konsolidasyonun silme kararı yalnız
   travma-dışı anılara uygulanıyor.
2. **Varise yalnız travma geçiyor.** `select_for_transfer` `f_agent`
   verildiğinde: `if f_value < FITNESS_LOW_THRESHOLD and trauma → selected`.
   **L1**: `f_agent = 0.000`, dokuz koşumun dokuzunda ⇒ koşul **daima**
   sağlanıyor, ve travma-dışı her aday `w_transfer` yoluna düşüyor, o da
   L1 gereği 0. Ölçülen: `n_transfer_candidates = 3`,
   `n_inherited_warnings = 3` — **üçü üçü de uyarı**.

⇒ Aktarılan her şey travma; travma unutmadan muaf; kırık saat yalnız
unutmayı yanlış hesaplıyor. **GAP-19'un birincile giden yolu kapalı.**

### ⇒ Öneri: **şimdi değiştirme**, ama gizli bağımlılığı yaz

Değiştirmenin kazandıracağı bir şey yok (etkisi sıfır), maliyeti bütün
koşumların geçersiz olması. D-042'yi düzeltmiştik çünkü **ölçülen** bir
sapma üretiyordu; bu üretmiyor.

⚠ **Ama gizli (latent):** **L1 düzeltilir de sayaç düzeltilmezse GAP-19
anında canlanır.** `F_agent` çalışır hale gelince travma-dışı anılar
aktarılabilir olur, ve onların tutulup tutulmayacağı **kırık saatle**
hesaplanır. İkisi **birlikte** düzeltilmeli ya da hiçbiri.

Bu, bugünün üçüncü "iki kusur birbirini gizliyor" örneği:
L1 (`F_agent`) ↔ GAP-19 · L13 (precision atıl) ↔ ΔPE duyarlılığı ·
GAP-4 (senkron yok) ↔ L15 (kanal asimetrisi).

### Yapılan tek kod değişikliği: raporlama

`write_multigen_results_json`'ın `pairs` sözlüğü elle kuruluyor ve
`consolidation` **hiç yazılmıyordu** — `control_d042` içinde
`"consolidation"` dizgisi **sıfır kez** geçiyor. Alan hesaplanıyor,
`[CONSOLIDATE]` diye stdout'a basılıyor, dosyaya girmiyordu.

Üstelik aynı sözlüğün **iki satır yukarısındaki** yorum tam bunu anlatıyor
(D-036'da `phase2_decision_divergence` aynı şekilde düşmüştü, ve onu koruyan
test **nesneye** baktığı için suite yeşil kalmıştı). Aynı hata, bir alan
ötede. Test bu sefer **dosyaya** bakıyor.

Bu, A7 için önkoşuldu: GAP-19 "konsolidasyon neyi siliyor" sorusudur ve
`deleted_count` görünmüyordu. **B2'de görünecek.**

**Reddedilen alternatifler:**
- *Sayaç uzayını şimdi birleştirmek* — ölçülen etkisi sıfır, maliyeti her
  koşumun geçersizliği. Kilit öncesi §2.10'un kuyusu.
- *GAP-19'u "kapandı" saymak* — mekanizma gerçek ve **gizli**; kapatmak
  L1 düzeltilince sessizce canlanmasına yol açardı.
- *L1'i (F_agent) burada düzeltmek* — birlikte düzeltilmeleri gerektiği
  tespiti tam olarak bunu **tek başına** yapmamayı söylüyor.

**Sınırlar:** Zincirin tamamı **koddan** türetildi ve dokuz kolun transfer
sayımlarıyla tutarlı (`3/3` uyarı), ama `deleted_count` hiçbir koşumda
**görülmedi** — alan düşürülmüştü. Yani *"konsolidasyon travma-dışı bir şey
sildi mi"* sorusu hâlâ ölçülmemiş; B2 cevaplayacak. N=3, tek koşum.

---

## D-052 · 2026-08-11 · A8: **N = 40**, iki batch hâlinde. S2 kapandı, GAP-9 kapandı

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-11) · **Slot:** §9-S2

### Karar: `N = 40` seed (2004–2043)

**MDE (Wilcoxon, çift yönlü, α=0.05, güç 0.80): `d_z = 0.465`.**
Bütçe: **13.3 GPU saat** (ölçülen seed başına 19.9 dk × 40 + 7 dk replay).

| N | GPU | MDE (Wilcoxon) | güç @`d_z=0.50` | güç @`d_z=0.45` |
|---|---|---|---|---|
| 32 | 10.6 sa | 0.524 | %76 | %67 |
| **40** | **13.3 sa** | **0.465** | **%85** | **%77** |

**Gerekçe:** `N` **tek atışlık** — kilitten sonra seed eklemek post-hoc olur
ve ön-kaydı geçersiz kılar. +2.7 saat, `d_z ≈ 0.45–0.50` bandında **~%10
puan** yakalama şansı satın alıyor, ve o bant tam olarak "gerçek ama mütevazı
etki"nin yaşadığı yer. İki seçenek de **tek gecelik** (20:00'de başlarsa
06:40 vs 09:20) ⇒ marjinal maliyet bir iş günü değil, birkaç sabah saati.

### ⚠ İki düzeltme

**1. MDE'ler Wilcoxon'a göre yeniden hesaplandı.** Daha önce (ve DR #1'de)
verilen `N=32 → d_z=0.511` **t-testi** sayısı. §3 **eşleştirilmiş Wilcoxon**
kullanıyor, o da normal veride ~%5 daha fazla N ister (ARE = 3/π).
Doğrusu **0.524**. `N=40` için t-testi 0.454, **Wilcoxon 0.465** —
ön-kayıta **Wilcoxon değeri** yazıldı.

**2. GAP-9'un `N=40–50`'si bize ait değildi.** O sayı
`protocol-c-metacognition-eval`'den ve **Protocol C için**, uç noktası
**ΔPE** olan bir güç analizi (`σ_PE = 0.256`). Ama **D-002 tam da ΔPE'yi
bıraktığı için** doğum-drifti birincil yaptı — gerekçesi *"yüksek güçlü uç
nokta"*ydı. Yani o sayı **kullanmadığımız bir ölçüm için** hesaplanmış ve
doğrudan taşınmıyor. **İki sayı çelişmiyordu, karşılaştırılabilir bile
değillerdi.** GAP-9'un gerçek talebi *"N'i gerekçelendirmeden alma"*ydı ve
o D-047 ile karşılandı. ⇒ **GAP-9 kapandı.**

### Koşum iki batch hâlinde: 2004–2023 · 2024–2043

`write_multigen_results_json` **yalnız en sonda** çağrılıyor; multigen'de
heartbeat de kısmi yazma da **yok** (Protocol C′'de var). Tek koşumda 39.
seed'de bir çökme **13 saati** götürür.

Batch'ler **yapı gereği bağımsız**: her seed kendi `_lock_seeds(seed)`'i ile
başlıyor, koşum bit düzeyinde deterministik (D-037), ve adapter graft'ı
konumdan bağımsız (D-042). Seed 2024'ün sonucu, 2004–2023'ün aynı süreçte
koşup koşmadığına bağlı değil. Kod değişikliği **gerekmiyor** —
`DAU_MULTIGEN_SEED_START` ve `DAU_MULTIGEN_N_PAIRS` env ile ayarlanıyor.

Maliyeti: ikinci bir I4.1 replay (+7 dk) ve `pair_filter` sayaçlarının
batch başına olması (B3 toplar; I1.4 her batch'i ayrı yargılar).
Kazancı: çökme maliyeti **13.3 saatten ≤6.7 saate** iniyor.

⚠ **Önceden ilan ediliyor**, koşum görüldükten sonra değil. Bir batch abort
ederse **o batch** yeniden koşulur; sonuçları seçmek için batch atılamaz.

### OOM davranışı — bilinerek kabul edildi

GPU **8188 MiB**, pilot ~7.5 GiB kullandı ve **bir OOM uyarısı** verdi
(D-034). 40 seed × 3 kol = **120 eğitim** ⇒ gerçek bir OOM olasılığı ihmal
edilebilir değil. Çıkarsa `_train_adapter` yakalar, `trained=False` döner,
ve **I1.1 koşumu ABORT eder** — sessizce eğitimsiz kol üretmez. Doğru
davranış, ama koşumun durması demek. Batch'leme bunun maliyetini yarıya
indiriyor.

**Reddedilen alternatifler:**
- *`N=32`* — 2.7 saat ucuz, ama `d_z≈0.45`'te %10 puan güç kaybı, ve karar
  geri alınamaz.
- *`N=50`* — 16.6 saat, MDE 0.414. Kazanç azalıyor (0.465→0.414), maliyet
  bir geceyi aşıyor, OOM penceresi büyüyor.
- *Tek 13.3 saatlik koşum* — çökme maliyeti iki katı, karşılığında hiçbir
  bilimsel kazanç yok.
- *Koşumu yeniden başlatılabilir (resume) yapmak* — koşum-genelindeki
  sayaçlar (`PAIR_DIVERSITY_STATS`, `POLARITY_FILTER_STATS`,
  `SNR_MARGIN_SAMPLES`) seed'ler boyunca birikiyor; kısmi resume onları
  bozardı. Batch'leme aynı korumayı **kod değiştirmeden** veriyor.

**Sınırlar:** 19.9 dk/seed **`control_d042`'den** ölçüldü; ondan sonra dört
kapı ve üç sayaç grubu eklendi (hepsi ucuz ama **ölçülmedi**) ⇒ gerçekçi
tampon **%5–10**. Batch bağımsızlığı D-042'nin konum bağımsızlığına
dayanıyor; o bozulursa batch'leme de bozulur — ama o durumda tek koşum da
bozuk olurdu. I4.1 replay her batch'te bunu sınıyor.

---

## D-053 · 2026-08-12 · B2 koştu, §5 geçerlilik kapısı düştü: sapma ilan edilerek doğrulayıcı sayılır

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-12) · **Etkilenen:** `PREREGISTRATION.md` §5

### Ne oldu

B2 doğrulayıcı koşumu iki batch hâlinde tamamlandı — seed 2004–2043, N=40,
`exit 0`, çökme yok.

| | batch 1 (2004–2023) | batch 2 (2024–2043) |
|---|---|---|
| dosya | `dau_runs/prereg_b2_batch1_2004_2023.json` | `dau_runs/prereg_b2_batch2_2024_2043.json` |
| süre | ~6.4 sa | ~6.7 sa |
| `run_quality` | **flagged** | **flagged** |
| geçen kapı | 23 / 24 | 23 / 24 |
| bayrak kaldıran | **I1.3b** | **I1.3b** |
| `prompt_skipped_no_record` | **2** / 2050 | 0 / 2050 |
| `[LORA][WARN]` | **2** | 0 |

§5'in **adıyla saydığı 18 kapının hepsi** (I0.1–I0.7, I2.1–I2.2, I3.1–I3.4,
I4.2, I5.1–I5.4) iki batch'te de geçti. `adapter_present` 240/240 doğru
(`lived`/`shuffle`=True, `null`=False). `tool_identity` ön-kayıt §12 ile
**birebir** eşleşti — backend, model, NF4+double_quant, DPO ayarları, LoRA,
sampling ve sekiz kütüphane sürümü dahil.

### Karar

**Sapma ilan edilir, koşum doğrulayıcı sayılır.** Rapor (B4) sapmayı en
üstte, bu kayda atıfla duyurur.

### Gerekçe — üç ayrı olgu

**1. `run_quality = clean` şartı §5'in kendi listesiyle çelişiyor.**
Bayrak kaldıran tek kapı `I1.3b` ve o, §5'in "geçmeli" diye saydığı 18
kapının **içinde değil**. Listede olmayan bir kapının bayrağı koşumu
düşürebiliyorsa, 18'i tek tek saymanın anlamı kalmaz. `CLAUDE.md`'nin B2
runbook'u koşumdan **önce** *"I3.2/I1.3b/I1.4/I1.5 FLAG olabilir (kalibre
değil), gerisi geçmeli"* diye yazmıştı — yani bu bayrak öngörülmüş ve
öldürücü sayılmamıştı. İki belge çelişiyordu; §2.11 gereği sessizce
seçilmedi, Yasin'e taşındı.

**2. `prompt_skipped_no_record = 0` yeniden koşumla sağlanamaz.**
D-037'den beri aynı seed + aynı kod **bit düzeyinde** aynı sonucu veriyor.
Batch 1 yeniden koşulsa seed 2012 yine aynı SYSTEM_1 kararını üretir ve
sayaç yine 2 olur. Kriter ihlal edildiğinde **kurtarılamaz**: ancak aleti
değiştirerek (kilit sonrası yasak, §2.10) veya seed setini değiştirerek
(§6 yasak) sağlanabilirdi. Şiddeti **2 / 2050 karar (%0.1)**; pilotta
0/300 çıktığı için 0'ın ulaşılabilir olduğu varsayılmıştı — ölçüm bunu
çürüttü. **Bu bir taslak hatasıdır**, koşumun kusuru değil.

**3. `dau_runs/adapters/` hiçbir zaman boş değildi.** §5 "koşum öncesi boş"
diyor; batch 1 başlarken 2001–2003'ün 7 adapter'ı, batch 2 başlarken batch
1'inkiler duruyordu. Biz bunu "kendi seed'lerimizle çakışma yok" diye
okuduk ve I0.7 de öyle denetliyor (ve geçti), ama metnin harfi "boş" diyor.
Eksiksiz olsun diye kayda geçiyor.

### İhlallerin hiçbiri birincil karşıtlığa yönlü terim eklemiyor

Sapmayı kabul edilebilir kılan şey bu, ve **ölçülmüştür**:

| İhlal | Simetri kanıtı |
|---|---|
| I1.3b (kırpma) | `lived` 10.8/10.8 adım · `shuffle` 10.8/10.8 · `grad_norm_min` 2.959 vs 2.984 |
| atlanan 2 karar | ikisi de seed 2012'de, **biri `lived` biri `shuffle`** kolunda (log satır 6084 ve 6578); `null` kolu uyarı vermedi |

Yani `a_s − b_s` farkına tek yönde çalışan bir terim yok.

### I1.3b'nin şiddeti — kayda değer, ayrı bulgu

`DPO_MAX_GRAD_NORM = 1.0`; **kırpılan adım / toplam adım = %100** (iki
eğitim kolunda da). `dpo_grad_norm_min ≈ 2.96` — koşumun **en küçük**
gradyanı bile tavanın ~3 katı. Doygunluk marjinal değil.

⇒ Adım boyunu artık gradyan değil **tavan** belirliyor, dolayısıyla D-029'un
literatürden kilitlediği `lr = 1e-6` koşumu tarif etmiyor. D-046 I1.3b'yi
tam olarak bunun için eklemişti ve kapı **işini yaptı**.

Yanında duran ikinci ölçüm: `dpo_loss` = **0.6919** (lived) / **0.6940**
(shuffle) — ikisi de **ln 2 = 0.6931**'e yapışık, yani eğitimden sonra
tercih marjı ≈ 0. DR #2'nin H3'ü *"shuffle belirgin yüksek olmalı"*
diyordu; **gerçekleşmedi** (fark 0.002).

⚠ Buna karşılık `dpo_delta_logp_chosen` = **+0.064**, 20 seed'in **18'inde
pozitif** ⇒ D-049'un korktuğu **bastırma deseni gerçekleşmedi**; öğrenmenin
yönü doğru, büyüklüğü yok. (`shuffle`'da da +0.025, 15/20 ⇒ bu bulgu
eğitim yordamının sağlığı hakkında, `lived`'e özgü değil.)

**Kilit kapalı olduğu için `DPO_MAX_GRAD_NORM`'a dokunulmadı** (§2.10).
İkinci ön-kayıta girer.

### GAP-18 ilk kez ölçüldü

| | batch 1 | batch 2 |
|---|---|---|
| `pairs_passed` | 1707 | 1741 |
| `uniq_chosen` | 1025 | 971 |
| **`uniq_rejected`** | **100** | **94** |
| `max_rejected_reuse` | 47 | 45 |
| `texts_in_both_roles` | 28 | 51 |

⇒ GAP-18'in tetiği ateşledi. **KTO'ya geçiş kararı artık brief'in
varsayımıyla değil bu sayılarla verilir** — ve kilit kapalı olduğu için
**ikinci ön-kayıta** gider, bu koşuma değil.

### Reddedilen alternatifler

- **Tümüyle post-hoc raporlamak** (§10'un harfi). En savunulabilir duruş,
  ama kilidin bütün amacı olan doğrulayıcı statü kaybedilir ve 13 GPU saati
  keşifsel veriye döner. İhlaller kollara simetrik olduğu için bu bedel
  karşılıksız kalırdı.
- **Her şeyi atıp baştan koşmak** (§5'in harfi). ⚠ §5'i düzeltmeden
  yeniden koşmak determinizm gereği **aynı sonucu** verir ⇒ bu yol zorunlu
  olarak §5'in yeniden yazılmasını içerir. 13.3 GPU saat karşılığında hiçbir
  bilimsel kazanç yok.
- **İlan etmemek.** Kanıt zaten gönderilecek dosyaların içinde:
  `PREREGISTRATION.md` git'te `befd72b4ee57` ile kilitli, JSON'ların kökünde
  `"run_quality": "flagged"` yazıyor. Gizliliğin faydasını vermez, yalnız
  yakalanmanın bedelini bırakır.

### Sınırlar

Bu kayıt **birincil sonuca bakılmadan** yazıldı — geçerlilik kararı sonuç
görülmeden verilsin diye analiz kasıtlı olarak ertelendi. `I1.3b`'nin etki
büyüklüğü üzerindeki payı **nicelenmedi**: %100 kırpmanın etkiyi ne kadar
küçülttüğü bilinmiyor, yalnız simetrik olduğu biliniyor. Bu, B4'ün
mekanizma-null / alet-null ayrımında **alet tarafına** yazılacak kanıttır,
ama tek başına "etki vardı da kırpma yuttu" demeye yetmez.

---

## D-054 · 2026-08-12 · D-013 kapandı: branch main'e taşındı, main ata olarak birleştirildi

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-12) · **Kapattığı:** D-013

### Diverjansın gerçek boyutu

| | |
|---|---|
| Ayrım noktası | `ece09b1` (v1.4 milestone) |
| Branch → main | **150 commit önde** |
| main → branch | **10 commit önde** |

main'in 10 commit'i erken **LAYER-5 LoRA** çalışması. Bu branch aynı alanı
baştan geliştirip geçti: `local_llm.py`'de **18 vs 6** commit,
`lora_update.py`'de **13 vs 3**, `run_protocol_c_prime.py`'de **28 vs 3**.

### Ölçüm: main'in benzersiz dosyaları aşılmış mı?

main'de olup bu branch'te **hiç olmayan** (silinmemiş — hiç girmemiş) altı
dosya vardı. İkisi test ve ikisi de bu branch'in koduna karşı **koşuldu**:

| Dosya | Ölçüm |
|---|---|
| `tests/test_local_llm.py` | ❌ **import edemiyor** — `MICRO_TRAIN_COMPLETION`, `MICRO_TRAIN_PROMPT`, `STATUS_GO`, `STATUS_NOGO` artık yok |
| `tests/test_lora_update.py` | ⚠ **5 geçti, 3 düştü** |
| `run_vram_spike.py` | bizde VRAM aracı yok; ölçümler var (`vram_train_peak_nf4.json`) |
| `DAU_MASTER_REFERENCE_v15.md` · `v16.md` | v2.4.3 tarafından aşıldı |
| `requirements-lora.txt` | ⚠ **gerçek boşluk** — aşağıda |

**Düşen üç testin hangileri olduğu belirleyici:**
`test_build_pe_ranked_pairs_orders_by_injected_pe` (**D-032** çift kurma
prompt'unu değiştirdi), `test_shuffle_preference_pairs_swaps_direction`
(**D-040** shuffle'ı %50 yazı-turadan **%100 tersine** çevirdi),
`test_lora_update_writes_traces_when_enabled_without_gpu`.

⇒ **main'in testleri kayıp kapsam değil, aşılmış kararları kodlayan eski
testler.** O testlerin *geçmesi* bu branch için **regresyon** olurdu.
Suite'e alınsalardı 344'ü kırarlardı.

### Karar: etiketle → `-s ours` birleştir → main'i ilerlet

1. **`archive/main-pre-c116`** etiketi (annotated) eski main'e çakıldı
   (`43efef6`). Doğrulandı: v16 master ref'i ve eski `requirements-lora.txt`
   etiketten hâlâ okunabiliyor. **Hiçbir commit kaybolmadı.**
2. Branch'te **`git merge -s ours main`** (`7909100`) — main'in commit'leri
   **ata** oldu, içerikleri alınmadı. Tarih tek ve doğrusal okunuyor.
3. **`requirements-lora.txt`** ayrı commit'le eklendi (`12a2270`) —
   main'inki gibi `>=` gevşek aralıklarla **değil**, B2'nin
   `tool_identity.versions` bloğundan okunan **tam** sürümlerle:
   torch 2.13.0 · transformers 5.14.1 · peft 0.20.0 · bitsandbytes 0.50.0 ·
   accelerate 1.14.0 · numpy 2.4.5 · scipy 1.18.0.
   **Gerekçe:** alet kimliği bu sürümleri her koşumda raporluyor ama hiçbir
   dosya pinlemiyordu; ön-kayıtlı koşumu yeniden üretmek isteyen biri
   sürümleri **tahmin etmek** zorunda kalırdı. Tekrarlanabilirlik iddiası
   gevşek aralıkla kurulamaz.
4. **`git branch -f main HEAD`** — fast-forward, zorlama gerekmedi.

Suite her adımda **344 passed**.

### Reddedilen alternatifler

- **Gerçek merge, çatışmaları elle çözmek.** ~18 dosyada çatışma çıkardı ve
  ölçüme göre **her çatışmada bizim taraf kazanacaktı** (18 vs 6 commit).
  Sonuç aynı, maliyeti saatler, yan etkisi iki eski testin suite'e girip
  onu kırması.
- **Dokunmamak, paper aşamasına bırakmak.** Tetik zaten ateşlemişti ve
  diverjans her commit'te büyüyor; 150-10 iken çözmek sonra çözmekten ucuz.
- **main'i zorla taşımak (etiketsiz).** 10 commit yalnız reflog'da kalırdı;
  reflog budanabilir. Etiket kalıcı.
- **main'in iki testini de almak.** Ölçüldü: biri import edemiyor, diğeri
  aşılmış kararları sınıyor.

### Sınırlar

`origin`'e **push edilmedi** — uzak `main` hâlâ `43efef6`'da. Push ayrı bir
karar ve Yasin'in onayını ister.
`run_vram_spike.py` alınmadı: şu an ihtiyaç yok ve etiketten her an
çıkarılabilir. Alınmadığı için bu branch'te **VRAM ölçüm aracı yok**, yalnız
geçmiş ölçüm çıktıları var.

---

## D-055 · 2026-08-12 · `run_vram_spike.py` geri alınmadı: sarmaladığı API yok

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-12) · **Düzelttiği:** D-054 §Sınırlar

D-054 *"`run_vram_spike.py` alınmadı; etiketten her an çıkarılabilir"* diyordu.
**Ölçüldü, ve o cümle yanıltıcıydı** — dosya çıkarılabilir ama **çalışmaz.**

34 satırlık ince bir sarmalayıcı ve `local_llm`'den üç isim çağırıyor:
`STATUS_GO` · `run_vram_spike` · `write_vram_spike_report`. **Üçü de bu
branch'in `local_llm.py`'sinde yok** (`hasattr` ile denetlendi). main'in
`test_local_llm.py`'siyle aynı sınıf: erken LAYER-5 API'sine yazılmış,
o API 18 commit boyunca değişmiş.

⇒ **Geri alınmadı.** Bu branch'te **VRAM ölçüm aracı yok**; yalnız geçmiş
ölçüm çıktıları var (`vram_train_peak_nf4.json`, `vram_spike_results.json`,
`protocol_c_prime_multigen_pilot_n3_local_vram.csv`).

**İkinci ön-kayıt için sonuç:** VRAM sınırı yeniden ölçülecekse araç
**yeniden yazılır**, etiketten geri alınmaz. Bu, B2'nin OOM marjı göz önüne
alınınca gerçek bir ihtiyaç olabilir — koşum 8188 MiB'de 49 allocator
uyarısı üretti (çökme yok).

**Reddedilen alternatif:** dosyayı alıp eksik üç fonksiyonu yazmak. Yazılacak
şey aracın kendisi olurdu, sarmalayıcı değil; ve kilit sonrası dönemde
ölçüm aracı yazmak ikinci ön-kaydın işi.

---

## D-056 · 2026-08-12 · Birincil uç noktanın çözünürlüğü ölçüldü: %99'u sabit, 11/40 seed'de yapısal olarak kör

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** — B2 verisinin
**post-hoc** teşhisi. **B2'nin raporlanan sonucunu değiştirmez** (birincil
null, §11 alet null'ı, D-053); ikinci ön-kaydın tasarımı içindir.
**GPU kullanılmadı**, koda dokunulmadı.

### Soru

B2'de `a_s − b_s` 40 çiftin **11'inde tam sıfır** çıktı. Sebep tesadüf mü,
yoksa uç noktanın yapısı mı?

### Bulgu 1 — uç nokta vektörünün **%99'u sabit bir terim**

| Alan | Kaç kolda bayraklı (120) | Yayılım / ortalama | Farklı değer |
|---|---|---|---|
| **`resource`** | **120 (%100)** | **%1.9** | **12** |
| `social` | 51 (%43) | %54.1 | 50 |
| `uncertainty` | 16 (%13) | %16.0 | 13 |

`‖m‖` ortalaması **3.8073**, `resource` bileşeni **3.7735**
⇒ **vektörün ~%99'u** her kolda bulunan, neredeyse sabit bir terim.

Ve o terim kollar arasında ayrım **üretmiyor**: `resource` tek bayrakken
kollar arası fark **40 seed'in 38'inde tam sıfır**.

⇒ Ayrımın tamamı `social` ve `uncertainty`'den geliyor, ve o ikisi
kolların yalnız **%43** ve **%13**'ünde bayraklanıyor.

### Bulgu 2 — 11 beraberlik tesadüf değil, **yapısal**

11 seed'in hepsinde `lived` ve `shuffle` **birebir aynı vektörü** üretti.
İki desen var:

- **6 seed** (2005, 2017, 2025, 2031, 2039, 2042): üç kol da aynı bayrak
  kümesi, aynı büyüklük ⇒ `a = b = 0`. **Uç nokta tamamen kör.**
- **5 seed** (2013, 2014, 2022, 2032, 2043): `lived` ve `shuffle` yalnız
  `resource`, `null` ek olarak `social`/`uncertainty` bayraklı ⇒ iki mesafe
  de **aynı şeyi** ölçüyor, `a = b` **tanım gereği**.

⇒ Bu 11 seed'de **mükemmel eğitilmiş bir adapter bile** birincil uç noktada
görünemezdi. Bu bir güç sorunu değil, **ölçülemezlik**.

### Bulgu 3 — travma seyrek: **33/120 kolda hiç yok**

`consolidation.drift_flag_count`: ortalama **1.38** (50 olaylık yaşamda),
min 0, max 7, ve **120 kolun 33'ünde sıfır**. Doğum-drift yalnız travma
anında yazıldığından (L11, `drift.py:41`), uç nokta **yaşam başına ~1.4
olaya** dayanıyor.

### Bulgu 4 — kalan 29 seed'de duyarsızlık **yok**, ama işaret rastgele

| | |
|---|---|
| `\|a − b\|` (sıfır olmayan 29) | ort. **0.4440** · medyan 0.5173 · max 1.0586 |
| İşaret | **+15 / −14** |

⇒ Uç nokta çözünürlüğü olduğunda **büyük** hareket ediyor (ortalama 0.44,
sabit terimin %12'si), ama **yönü kolla ilgisiz** — yazı-tura.

**Bu, null'ın okunuşunu değiştiriyor:** *"küçük etkiyi göremedik"* değil,
*"29 seed'de büyük hareket var ve hangi eğitimi aldığı yönü belirlemiyor."*

### Ne anlama geliyor

D-002'nin dört halkalı nedensel zinciri şunu gerektiriyor: adapter'ın
öğrendiği → ajanın davranışı → hangi alanda travma → varisin doğum-drifti.
**Birinci halka çalışıyor** (kanal 2 kararların %52'sini değiştiriyor,
D-053). **Son halka ölçülüyor.** Aradaki bağlantı — *"adapter hangi alanda
travma yaşanacağını etkiliyor mu"* — bu veride **kurulamıyor**.

İki ayrı yetersizlik, ikisi de aletin değil **evrenin** özelliği:

1. `resource` travması herkeste, hep, aynı büyüklükte oluyor — havuz krizi
   (`POOL_CRISIS_THRESHOLD = 0.30`) bütün ajanları aynı anda vuruyor.
2. `social` ve `uncertainty` travması **çok seyrek** — ayrım üretecek
   olaylar yaşam başına ~1.4 kez oluyor, üçte birinde hiç olmuyor.

⇒ **A4 (environment'ı ayrım üretir hale getirme) artık gerekçelendirilmiş
bir zorunluluk.** L1 (`F_agent=0.000`), L11 (`resource` yayılımı %2.7) ve bu
kayıt aynı olguyu üç ayrı yerden gösteriyor: **ajanlar birbirinden farklı
hayat yaşamıyor.** Aksiyom *"yaşam verirsin, trait oradan çıkar"* diyor;
evren şu an **ayırt edici yaşam vermiyor**.

### Sınırlar

Post-hoc teşhis; hipotez testi değil, ön-kayıta girmedi. Uç noktanın
%99'unun sabit olması **tek başına** null'ı açıklamaz — 29 seed'de
çözünürlük vardı ve orada da yön çıkmadı. Yani bu kayıt *"uç noktayı
düzeltirsek etki çıkar"* **demiyor**; *"bu uç noktayla 11/40 seed'de hiçbir
şey çıkamazdı, kalanında da bağlantı halkası kurulamadı"* diyor.
Uç nokta tanımı **değiştirilmedi** — ölçümü görüp uç nokta seçmek post-hoc
olur (§2.7); değişecekse ikinci ön-kayıta ve **taze veriye** yazılır.

---

## D-057 · 2026-08-12 · Eğitim girdileri diske yazılıyor: sweep artık yaşamları yeniden koşmuyor

**Durum:** kabul edildi · **Onay:** Yasin (2026-08-12) · **Uygulama:** `82e09d6`

### Sorun

B2 **13.1 GPU saat** harcadı ve tek bir konfigürasyonun sorusunu cevapladı.
Sonraki soru — hangi `lr`, hangi kırpma tavanı, hangi çift kurma stratejisi —
her seferinde **bir tam koşum daha** isteyecekti.

Ama pahalı olan kısım eğitim değil **yaşamak**: kol başına **~11 optimizer
adımı**, saniyeler. Yaşamlar hiçbir yere yazılmıyordu.

### Karar

`dau/diagnostics/training_artifacts.py` iki şeyi yazıyor:

| Ne | Neden |
|---|---|
| `lived_examples` — aday havuzu, **çift kurmadan önce** | Farklı bir çift kurma stratejisi (KTO, GAP-18'in ayrık eşleştirmesi) ürünü değil **havuzu** gerektiriyor |
| `pairs` — eğitime giden çiftler | DPO ayarlarını sabit bir sete karşı taramak için |

Env: **`DAU_DUMP_TRAINING_ARTIFACTS`**, varsayılan **kapalı**.
Çıktı: `dau_runs/training_artifacts/{agent_id}.json`.

### İki tasarım kısıtı

**1. Alet takip ediliyor, tekrar edilmiyor (§2.8).** Dump, eğitime
**gerçekten verilen** nesneleri seri hale getiriyor — SNR ve polarite
kapılarından sonra, shuffle ters çevriminden sonra. Yeniden kurma yapsaydı
koşumla ancak ikisi ayrışana kadar uyuşurdu, ve ayrıştığı an önemli olan an.

**2. Varsayılan kapalı, yan etkisiz.** Dosya yazmak koşumun hesabını
değiştirmemeli. **Kancanın yeri `shuffle_preference_pairs`'den sonra**:
önceki çiftleri yazmak replay'e **kontrol kolunun adı altında lived yönünü**
verirdi — D-040'ın bitirdiği karışıklığın aynısı.

Tanınmayan bayrak değeri **`ValueError`** (D-023 deseni): yanlış yazılmış bir
bayrak sessizce dump'ı kapatırsa, bedeli GPU saatleri harcandıktan **sonra**
fark edilir.

### Mutasyon kontrolü — dördü de kırdı

| Mutasyon | Düşen test |
|---|---|
| `pairs_digest` sırayı yok saysın (`sorted`) | 1 |
| Tanınmayan bayrak sessizce `False` dönsün | 2 |
| Dump listeyi yerinde sıralasın (yan etki) | 4 |
| `lived_examples` yazılmasın | 4 |

⇒ Testler bu kusurları **gerçekten** yakalıyor. Suite **344 → 351**.

### Ne açıyor

| Soru | Eskiden | Şimdi |
|---|---|---|
| `lr` × kırpma taraması | tam koşum / ayar | model yükleme + 11 adım |
| KTO vs DPO (GAP-18) | tam koşum | havuzdan offline |
| Filtre eşikleri (SNR, polarite) | tam koşum | offline |

### Sınırlar

Dump **yalnız `_train_adapter` yolunu** kapsıyor; `null` kolu eğitmediği için
artefakt üretmiyor (doğru davranış, ama korpusta null yok). Yazılan dosyalar
`dau_runs/` altında ve **git'te takip edilmiyor** — korpus makineye özgü,
ama D-037 determinizmi sayesinde `prereg/b2-code` etiketinden yeniden
üretilebilir. Replay sürücüsü **bu kayda dahil değil**, ayrı iş.

---

## D-059 · 2026-08-12 · Tarama sonucu: kaldıraç kırpma değil `lr`. L18 doğruydu ama sebep değildi

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** · adapter kaydedilmedi ·
`constraints.py` değiştirilmedi · korpus: seed 3001–3004, 8 kol, 96 hücre

### Soru

B2 iki şey ölçmüştü: kırpma **%100** (`grad_norm_min ≈ 2.96` vs tavan 1.0) ve
`dpo_loss ≈ ln 2` (tercih marjı ≈ 0). **L18** bunu sınır olarak yazdı ve
`CLAUDE.md` *"en somut aksiyon çıktısı"* dedi. Tarama şunu sordu: tercih marjı
kıpırdatılabiliyor mu, ve kıpırdatan şey ne?

### Bulgu 1 — **kırpma kaldıraç değil**

| `lr` | clip=1 (kırpma %100) | clip=3 (%95) | clip=10 (%0) |
|---|---|---|---|
| 1e-6 | 0.6951 | 0.6935 | 0.6939 |
| 5e-6 | 0.6894 | 0.6891 | 0.6911 |
| 1e-5 | 0.6801 | 0.6813 | 0.6804 |
| 2e-5 | 0.6518 | 0.6520 | 0.6491 |

Tavanı 1'den 10'a çıkarmak kırpmayı **%100'den %0'a** indiriyor ve kayıp
**değişmiyor** — dört `lr` değerinin dördünde de.

**Sebebi mekanik:** `AdamW` adımı ikinci moment tahminine bölerek normalize
ediyor, yani gradyanın **ölçeğine büyük ölçüde duyarsız**. `clip_grad_norm_`
gradyanı yeniden ölçekliyor; Adam o ölçeklemeyi zaten geri alıyor.

⇒ **L18'in gözlemi doğru, çıkarımı yanlıştı.** Kırpma gerçekten doygundu, ama
zayıf öğrenmenin **sebebi o değildi**. Bu belge ve `CLAUDE.md` onu "en somut
aksiyon çıktısı" diye işaretlemişti; **düzeltiliyor**.

### Bulgu 2 — kaldıraç **`lr`**, ve marj kıpırdıyor

`dpo_loss` ortalaması (clip'ten bağımsız): **0.694 → 0.689 → 0.680 → 0.651**
(`lr` 1e-6 → 5e-6 → 1e-5 → 2e-5). ln 2 = 0.6931'den **0.044** aşağı.

⇒ *"Tercih marjı ln 2'de çakılı"* durumu **aşılabilir bir durum**, kalıcı bir
tavan değil.

### Bulgu 3 — taranan bantta **bastırma yok**

D-049/D-029'un teşhisi: bastırma = `chosen` ≈ 0 veya negatif iken `rejected`
güçlü negatif.

| `lr` | `Δlogp chosen` | `Δlogp rejected` | oran | yorum |
|---|---|---|---|---|
| 1e-6 | −0.003 | +0.013 | — | chosen yükselmiyor |
| 5e-6 | **+0.053** | −0.017 | 0.33 | dengeli |
| 1e-5 | **+0.147** | −0.113 | 0.77 | dengeli |
| 2e-5 | **+0.447** | −0.451 | 1.01 | dengeli |
| *5e-5 (D-029)* | *−0.123* | *−4.371* | *35* | **bastırma** |

⇒ 5e-6 … 2e-5 bandında öğrenme **simetrik**: `chosen` yükselirken `rejected`
aynı ölçüde düşüyor. Bastırma 2e-5 ile 5e-5 arasında bir yerde başlıyor.

### Bulgu 4 — `lived` her `lr` değerinde `shuffle`'dan **daha kolay öğreniliyor**

| `lr` | `lived` kayıp | `shuffle` kayıp | fark |
|---|---|---|---|
| 1e-6 | 0.6921 | 0.6957 | −0.0036 |
| 5e-6 | 0.6901 | 0.6921 | −0.0020 |
| 1e-5 | 0.6788 | 0.6820 | −0.0032 |
| 2e-5 | 0.6466 | 0.6517 | **−0.0051** |

Dördünde de aynı yönde, ve `lr` büyüdükçe fark büyüyor. İki kol **aynı
çiftleri** kullanıyor, yalnız yönü ters — yani yön keyfi olsaydı ikisi eşit
zorlukta olurdu.

⚠ **Bu bir sinyal iddiası DEĞİL, ve alternatif açıklaması var:** `lived`'in
`chosen`'ı daima düşük-PE completion. Taban model kısa/sık kalıpları zaten
daha olası buluyorsa, `lived` yönü **taban önseldan** dolayı da daha kolay
olabilir — yaşamdan öğrenilmiş bir şey olmadan. Ayırt etmek için sahte-PE
kontrolü gerekir (rastgele PE atanmış çiftler); **koşulmadı**.
N=4 seed, hipotez testi yok, düzeltme yok.

### Ne değişti, ne değişmedi

⇒ **Aletin zayıf öğrenmesi düzeltilebilir bir sorun**, ve düzeltmesi `lr`.
⇒ **Kırpma tavanına dokunmak gereksiz** — ikinci ön-kayıtta `DPO_MAX_GRAD_NORM`
değiştirmek için gerekçe **yok**.
⇒ `lr` değeri bu tablodan **seçilmedi** (§2.7). Tarama bandın şeklini gösterdi;
kilitlenecek değer ayrıca gerekçelendirilir ve tercihen sahte-PE kontrolüyle
birlikte kararlaştırılır.

### Sınırlar

Korpus **tek bir evrenden** geliyor (seed 3001–3004, mevcut environment), ve
D-056 o evrenin ajanları ayırmadığını gösterdi. Tarama *"eğitim öğrenebiliyor
mu"* sorusunu cevaplıyor, *"öğrendiği şey yaşama özgü mü"* sorusunu **değil** —
ikincisi A4'ün arkasında. Bulgu 4 o soruya değiyor ama alternatif açıklaması
elenmedi.

---

## D-060 · 2026-08-12 · A4 teşhisi: seçilim katmanı formül hatası değil, **girdi yokluğu**

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel** — B2 verisinin post-hoc teşhisi.
**GPU kullanılmadı**, koda dokunulmadı. 120 kol (40 seed × 3).

### Soru

L1 *"seçilim katmanı atıl, sebep birim uyuşmazlığı"* diyor: `compute_fitness`
`|Δpool|`'u `POOL_MAX=100`'e bölüyor ama çağıran **kümülatif** çıkarımı
veriyor (~393), pool terimi −2.9'a düşüyor, `[0,1]` clamp'i sıfıra eziyor.
Soru şu: **formülü düzeltmek yeter mi?**

### Bulgu 1 — seçilim katmanı tam anlamıyla ölü

| Alan | 120 kolda |
|---|---|
| `f_agent` | **0.000**, tek bir farklı değer |
| `f_agent_energy_final` | **0.000**, tek bir farklı değer |
| `fitness_class` | **`low`**, 120/120 |
| `f_agent_delta_pool` | 393.55 ± 2.62 · **6 farklı değer** · yayılım **%0.7** |
| Aynı seed içinde kollar arası `Δpool` farkı | **40 seed'in 32'sinde tam sıfır** |

Ayrıca `n_transfer_candidates` ile `n_inherited_warnings` **birebir aynı
dağılım** ⇒ L1'i doğruluyor: varise **yalnız travma uyarısı** geçiyor,
başka hiçbir şey. **33/120 kol hiçbir şey aktarmıyor** (0 aday).

### Bulgu 2 — **formülü düzeltmek ayrım üretmiyor**

Ağırlıklar: enerji **0.4** · havuz **0.3** · survival **0.3**.

Karşı-olgusal: birim uyuşmazlığı düzeltilip `Δpool` kendi ölçeğinde
normalize edilse —

| Normalizasyon | `F_agent` | yayılım | sınıf dağılımı |
|---|---|---|---|
| gözlenen max (400) | 0.3048 ± 0.0020 | **%0.64** | **120 `low`**, 0 normal, 0 high |
| olay başına havuz (5000) | 0.5764 ± 0.0002 | **%0.03** | **120 `normal`**, 0 low, 0 high |

⇒ Sayı değişiyor, **ayrım değişmiyor**: hangi normalizasyon seçilirse
seçilsin **120 kolun hepsi aynı fitness sınıfına** düşüyor. Seçilim yine
çalışamaz.

**Sebebi aritmetik:** üç girdinin **ikisi sabit** —
`energy_final` = 0.000 (120/120) ve `t_survived/t_generation` = 1.0
(kimse ölmüyor) — üçüncüsü %0.7 yayılıyor. Ağırlıklarla birlikte
**fitness'ın etkin varyansı ≈ %0.2**.

### Bulgu 3 — kıtlık var ama **herkese aynı**

`resource` travması **120/120 kolda** bayraklı ve büyüklüğü **%1.9** yayılıyor
(D-056). Havuz gerçekten çöküyor (`pool_ratio < POOL_CRISIS_THRESHOLD=0.30`),
ama **herkes için aynı anda ve aynı şiddette**. Kıtlık bir baskı yaratıyor,
**ayırt edici** bir baskı yaratmıyor.

### Sonuç: A4 bir formül düzeltmesi değil

L1 *"formül bozuk"* diyordu ve doğruydu; bu kayıt onun **yetersiz** olduğunu
gösteriyor. A4'ün ajanları ayırmak için üç kaldıraçtan **en az birini**
değiştirmesi gerekiyor:

| Kaldıraç | Ağırlık | Şu anki durum | Ne gerekir |
|---|---|---|---|
| **Enerji** | **0.4** | **daima 0.000** | Enerjinin gerçekten birikip harcanması — en büyük ağırlık, tamamen atıl |
| **Survival** | 0.3 | **daima 1.0** | Ölüm. Kimse ölmüyorsa seçilim yok (L2) |
| **Çıkarım** | 0.3 | %0.7 yayılım | Farklı stratejilerin farklı sonuç vermesi |

⚠ **Gizli bağımlılık hatırlatması (D-051/L16):** `F_agent` tek başına
düzeltilirse GAP-19 canlanır — travma-dışı anılar aktarılabilir hale gelir ve
tutulmaları kırık sayaçla hesaplanır. **İkisi birlikte ya da hiçbiri.**

### Sınırlar

Post-hoc teşhis, hipotez testi değil. Karşı-olgusal iki normalizasyon
seçeneğiyle hesaplandı; başka bir normalizasyon başka bir ortalama verir ama
**yayılımı değiştiremez** — yayılım girdilerden geliyor, bölenden değil.
Hangi kaldıracın seçileceği **tasarım kararıdır** (D-007) ve bu kayıt onu
vermiyor, yalnız üçünü ölçüyor. `energy_final`'ın neden 0 olduğu **bu kayıtta
izlenmedi** — kodda mı yazılmıyor, yoksa gerçekten sıfır mı, ayrı iş.

---

## D-061 · 2026-08-12 · `energy_final = 0` bir raporlama boşluğu değil: enerji **yapı gereği** asla artamıyor

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel**, koda dokunulmadı, GPU yok ·
**Açtığı:** D-060'ın bilerek açık bıraktığı soru

### Soru

D-060, `energy_final`'ın 120 kolun 120'sinde **0.000** olduğunu ve fitness'ın
**en büyük ağırlıklı** teriminin (0.4) böylece atıl kaldığını ölçtü, ama
sebebini izlemedi: kodda hiç mi yazılmıyor, yoksa gerçekten sıfıra mı iniyor?

### Cevap: yazılıyor — ve **matematiksel olarak** sıfıra iniyor

`graph.py:665-670`:

```
energy_decay    = max(max_pe, METABOLIC_FLOOR)
energy_recovery = METABOLIC_FLOOR * (1.0 - mean_load)
new_energy      = clamp(before.energy - energy_decay + energy_recovery, 0.0, 1.0)
```

`METABOLIC_FLOOR = 0.05`.

**Kanıt (ampirik değil, cebirsel):**

- `energy_decay = max(max_pe, 0.05) ≥ 0.05`
- `energy_recovery = 0.05 · (1 − mean_load) ≤ 0.05`, çünkü `mean_load ≥ 0`
  (load'lar `[setpoint, METRIC_MAX]`'a clamp'li ve `setpoint ≥ 0`)
- ⇒ **`decay ≥ recovery` her zaman** ⇒ **`new_energy ≤ before.energy` her zaman**

⇒ **Enerji asla artamaz.** Ajan ne yaparsa yapsın, hangi kararı verirse
versin. En iyi durumda (`max_pe = 0.05`, `mean_load = 0`) net değişim tam
sıfır; her diğer durumda negatif.

`METABOLIC_FLOOR` **aynı anda** hem asgari tüketim hem azami toparlanma
olarak kullanılıyor. Tüketim PE ile ölçekleniyor (`[0,1]`), toparlanma
0.05'te sabit tavanlı ⇒ toparlanma tüketimin en fazla **%12'si** olabiliyor.

### Ne kadar hızlı

Ölçülen PE ortalaması **0.425** ⇒ olay başına net **−0.400**.
`DEFAULT_ENERGY = 1.0`'dan başlayıp **~2.5 olayda** tabana vuruyor.

Seed 2004 `lived`'in gerçek PE dizisiyle: olay 1 → 0.3498, **olay 2 → 0.0000**,
kalan **48 olay boyunca 0**.

### Sonuç

`energy` bir **durum değişkeni değil, tek yönlü bir sayaç**: iki olayda
tükeniyor ve yaşamın %96'sında sıfırda kalıyor. Dolayısıyla:

- Fitness'ın **%40'ı** hiçbir bilgi taşımıyor (D-060).
- `compute_endogenous_recovery_rate` ve `get_allostatic_setpoints` enerjiyi
  okuyorsa, onlar da yaşamın %96'sında aynı girdiyi görüyor.
- **A4 için doğrudan sonuç:** enerjiyi ayrım üretir hale getirmek bir sabit
  ayarı değil, **toparlanma teriminin yeniden tasarlanmasıdır** — mevcut
  biçimiyle tavanı yükseltmek bile yetmez, çünkü sorun tavanın değeri değil
  `recovery ≤ decay` eşitsizliğinin **yapısal** olması.

⚠ Bu, aksiyoma da dokunuyor. `state.py` enerjiyi *"metabolik kıtlık — madde
ve enerji sonlu, açlık seçilimi sürükler"* diye tanımlıyor. Açlık seçilimi
sürükleyebilmesi için **bazı ajanların daha aç olması** gerekir; şu an hepsi
ikinci olayda eşit derecede aç.

### Sınırlar

Kanıt `_advance_internal_state`'in okunmasından ve iki sabitten çıkıyor;
`mean_load ≥ 0` varsayımı load alanlarının clamp'ine dayanıyor ve o clamp
kodda görüldü, **ayrı bir testle doğrulanmadı**. Enerjinin başka bir yolla
(ör. `run_meta_ab.py:437`'deki `AB_ENERGY_FLOOR`) yazıldığı yollar
**deney yolunda değil** — bu kayıt yalnız C′/multigen yolu için geçerli.
Düzeltme önerilmedi: hangi toparlanma tasarımının seçileceği **tasarım
kararı** (D-007).

---

## D-062 · 2026-08-13 · W1 sahte-PE kontrolü: confound **bu biçimiyle yok**, ama D-059 Bulgu 4 **seed-kararlı değil**

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** · adapter kaydedilmedi ·
`constraints.py` değiştirilmedi · ön-kayıtlı harness'a dokunulmadı ·
korpus: `dau_runs/training_artifacts/`, seed 3001–3004 · ham çıktı
`dau_runs/w1_pe_loglik_confound.json`

### Soru

D-059 Bulgu 4: `lived` kolu dört `lr` değerinin dördünde de `shuffle`'dan daha
düşük kayıpla eğitiliyor. Kayıt alternatifi kendisi yazmıştı: *"`lived`'in
`chosen`'ı daima düşük-PE completion; taban model kısa/sık kalıpları zaten daha
olası buluyorsa `lived` yönü **taban önseldan** dolayı da kolay olabilir."*
CLAUDE.md bunu **W1** olarak kuyruğa aldı ve ölçümü tarif etti: korpustaki
completion'ların taban model log-olabilirliği ile PE'si arasındaki korelasyon.

### Yöntem

Taban model (`meta-llama/Meta-Llama-3.1-8B-Instruct`, NF4 + double_quant,
adapter **yok**, peft sarmalayıcı **yok**) altında öğretmen-zorlamalı skorlama.
Kodlama eğitimin kullandığı `_encode_pair_side` + `_sequence_logprob`
fonksiyonlarının **aynısı** — yani ölçüm eğitimin gördüğü diziyi görüyor.
386 ileri geçiş, üretim yok.

İki katman: **M1** olay düzeyi (4 seed × 50 yaşanmış karar, her biri kendi
gerçek karar prompt'u altında; pseudo-replikasyon yok) · **M2** çift düzeyi
(186 çift). `shuffle` ayrıca skorlanmadı: korpusta `shuffle` `lived`'in
**birebir rol takası** olduğu programla doğrulandı (4/4 seed) ⇒ Δ_shuffle = −Δ_lived.

**Karar kuralı sonuçlara bakılmadan önce yazıldı** (scratchpad `w1_analyze.py`):
confound *güçlü* = çiftlerin ≥%70'inde taban `chosen`'ı zaten tercih ediyor **ve**
|ρ(PE, logp)| ≥ 0.30 · *zayıf* = oran %50 ± %10 **ve** |ρ| < 0.15 · arası = kısmi.

### Bulgu 1 — **PE ile token başına olabilirlik arasında ilişki yok**

| İlişki (Spearman, n=200) | ρ | p |
|---|---|---|
| PE ~ `logp_sum` | **+0.165** | 0.020 |
| PE ~ `logp_mean` (token başı) | **+0.063** | 0.37 |
| PE ~ `n_tokens` | **−0.190** | 0.007 |
| PE ~ `logp_mean` \| uzunluk (kısmi) | **+0.044** | — |
| PE ~ `logp_sum` \| uzunluk (kısmi) | **+0.059** | — |

⇒ Confound'un tarif edildiği biçimi — *"düşük PE'li metin taban modelce daha
olası"* — **desteklenmiyor**: token başına olabilirlik PE hakkında bilgi
taşımıyor, ve zayıf toplam-logp ilişkisinin **işareti ters** (yüksek PE = daha
yüksek toplam logp). O ilişki de uzunluk kontrol edilince kayboluyor: PE ile
korele olan şey **uzunluk** (yüksek PE = daha kısa completion).

### Bulgu 2 — çift düzeyinde taban tercih **yazı-tura**, ama seed'e göre uçuyor

| Ölçü (n=186) | Değer |
|---|---|
| toplam logp marjı > 0 (DPO'nun kullandığı ölçü) | **%52.2** (97/186) |
| token başı marj > 0 | **%89.8** (167/186) |
| `chosen` token başı logp | **−1.389** |
| `rejected` token başı logp | **−2.584** |
| uzunluk | `chosen` 57.2 vs `rejected` 38.7 token |

Token başına `chosen` tarafı çok daha olası, ama bu **PE'nin değil paylaşılan
negatifin** özelliği (GAP-18: seed başına 1–2 benzersiz `rejected`). Toplam
marjda avantaj kayboluyor çünkü `chosen` daha uzun. Seed bazında oran
**%100 / %33 / %65 / %7** ve sırası uzunluk farkını (−4.6 / +23.2 / +15.1 /
+42.1 token) birebir izliyor.

⚠ Kayıp **referans-göreli** (`logits = policy marjı − reference marjı`, ve
referans aynı modelin adapter'sız hali) ⇒ taban marjı başlangıç kaybında
**cebirsel olarak sadeleşiyor**. Taban önseli kaybı doğrudan açıklayamaz;
ancak optimizasyon geometrisiyle etki edebilir.

### Bulgu 3 — **asıl bulgu: D-059 Bulgu 4 seed-kararlı değil**

D-059'un tablosu seed'ler üzerinden ortalamaydı. `sweep_dpo_hyperparams.jsonl`
seed bazında açıldığında:

| seed | taban toplam marj | marj>0 | `lived − shuffle` kayıp farkı (lr 1e-6 → 2e-5) |
|---|---|---|---|
| 3001 | **+56.3** | %100 | −0.0088 · −0.0082 · −0.0083 · −0.0065 |
| 3002 | **−17.7** | %33 | **+0.0037 · +0.0038 · +0.0027 · +0.0025** |
| 3003 | +4.1 | %65 | −0.0094 · −0.0106 · −0.0110 · −0.0079 |
| 3004 | **−31.3** | %7 | −0.0001 · −0.0003 · −0.0023 · **+0.0013** |

⇒ *"Dört `lr` değerinin dördünde de aynı yön"* **dört bağımsız olgu değil**:
aynı dört seed'lik havuzun dört tekrarı. Seed düzeyinde yön **2 seed'de
`lived` lehine, 1 seed'de tersine, 1 seed'de sıfır**. Seed'ler arası oynaklık
etkiden büyük.

Ve yönü açıklayan aday, seed'in **taban marjı**: taban toplam marj ile kayıp
farkı arasındaki sıra korelasyonu dört `lr` değerinin dördünde de **ρ = −0.6**
(n=4 — p verilmiyor, verilemez).

⇒ Confound *reddedilmedi*, **yeri değişti**: PE ile olabilirlik arasında değil,
**uzunluk → taban marj → kayıp farkı** zincirinde.

### Bulgu 4 (yan) — eğitim dizilerinin **%85.5'i 512 token tavanında kesiliyor**

Tokenizer ile ölçüldü, GPU yok (scratchpad `w1_truncation.py`, n=372 dizi):

- kesilen dizi **318/372 = %85.5** · tam uzunluk medyan **894** token (tavanın 1.75 katı)
- kesilenlerde atılan prompt tokenı medyan **444**, maks 908
- `_encode_pair_side` taşmayı prompt'un **başından** attığı için, kesilen her
  dizide **sohbet şablonu başlığı + BOS kayboluyor**: 318/372 = **%85.5**

⚠ D-027'nin gerekçesi *"eğitim ile çıkarım aynı sohbet biçiminde olsun"*du.
Dizilerin %85.5'inde o biçim **eğitim tarafında bozuluyor** — model sistem
prompt'unun ortasından, başlıksız bir metin görüyor. `DPO_MAX_SEQUENCE_TOKENS`
**kilitli** (§2.10) ⇒ bu koşumda değiştirilmedi, yalnız raporlandı.

### Ne değişti, ne değişmedi

⇒ **İkinci ön-kayıta *"lived öğrenilebilir yapı taşıyor"* girmiyor.** CLAUDE.md
bunu "confound elenmeden tehlikeli" diye işaretlemişti; ölçüm tehlikeyi
doğruladı ama **başka bir sebeple**: etki seed-kararlı değil.
⇒ `lr` bandı (D-059) etkilenmiyor — Bulgu 1–3 kayıp **seviyesine** değil kollar
**arası farka** dair.
⇒ **İkinci ön-kayıt kuyruğuna iki madde eklendi:** (a) `DPO_MAX_SEQUENCE_TOKENS`
yeniden değerlendirmesi (Bulgu 4) · (b) uzunluk kontrolü — çift kurma
`chosen`/`rejected` uzunluk farkını dengelemiyor, ve DPO toplam logp kullandığı
için bu doğrudan marja giriyor.

### Sınırlar

**N=4 seed**, tek evren (D-056: bu evren ajanları ayırmıyor), hipotez testi yok,
çoklu karşılaştırma düzeltmesi yok, n=4 üzerindeki ρ = −0.6 **yön göstergesi
bile sayılmaz**, kanıt değil. Skorlama eğitimin kesme davranışını **birebir**
taşıyor ⇒ log-olabilirlikler başlıksız prompt'lar altında; bu eğitim koşulu
olduğu için istenen davranış, ama "modelin bu metne verdiği olabilirlik"
genel bir ifade **değil**. CLAUDE.md'nin tarif ettiği *rastgele PE atanmış
çiftler* kolu **koşulmadı** — bu ölçüm korelasyonel biçimdi; randomize kol
hâlâ daha güçlü tasarım ve açık.
Koşumda bir `CUDACachingAllocator` OOM **uyarısı** görüldü, istisna yok,
386 ileri geçişin hepsi tamamlandı.

---

## D-063 · 2026-08-13 · W2: S5 aletlendi, S6 **kol olarak üretilmedi** — birincil `F_agent`'ı göremiyor

**Durum:** karar + aletleme · **Etiket:** saf raporlama eklemesi (§2.10'un
"hesaplamayı değiştirmeyen" izni) · hesaplama/RNG/digest değişmedi ·
kod `134073a` (S5) + `deee036` (S6) · suite 356 → **367**

### Soru

L20: B2'de altı ikincilin ikisi koşulamadı. **S5**'in verisi (`decision_to_extraction`,
travmaya kadar geçen olay) kayıtlı çıktıda yoktu; **S6**'nın (`f_agent=None`)
kolu üretilmemişti. W2 bu ikisini aletlemek için açıldı.

### S5 — aletlendi

`pool_step_node` zaten iki değeri hesaplıyordu ve ikisini de atıyordu: hasat
miktarı (`decision_to_extraction`) ve adım sonrası `pool_ratio`. Artık
`pe_event_log` ile **aynı desende** modül-yerel bir tampona yazılıyorlar
(`reset_pool_event_log` / `get_pool_event_log`), `run_life_keep_vault` yaşam
başında sıfırlıyor, `run_gen2_measure` akış bittikten sonra boşaltıyor.
`Gen2Result` altı yeni alan taşıyor ⇒ `asdict` üzerinden JSON'a giriyor.

- Kriz bayrağı **`apply_crisis_trauma`'nın kapı olarak okuduğu ratio'nun
  aynısından** üretiliyor. Kendi eşiğini yeniden hesaplayan bir bayrak drift
  haritasıyla sessizce anlaşmazlığa düşerdi (§2.8).
- ⚠ **İki travma okuması, bilerek** (§2.11): ön-kayıtın S5 satırı *"ilk travmaya
  kadar geçen olay"* diyor ama **commons krizi** (`apply_crisis_trauma`) ile PE
  yolundaki **`TRAUMA` sınıfı imprint** farklı olaylar, ve satır hangisini
  kastettiğini söylemiyor. Burada seçilmedi; ikisi de kaydediliyor.
- **Özet istatistik yok.** S5'in hangi istatistiği kullanacağı ön-kayıt kararı,
  kaydedicinin değil (§2.7). Ham per-olay diziler + iki sıra numarası.
- Yokluk `EVENT_NEVER_OCCURRED = -1`: krizsiz bir yaşam *"sıfırıncı olayda
  kriz"* diye okunamaz.

### S6 — **kol üretilmedi, gerekçe yapısal**

Aletlemeden önceki salt-okunur denetim şunu buldu:

```
birth_drift_magnitudes ← heir.drift_state ← GenerationRecord.inherited_drift
                       ← consolidate_generation: ebeveyn drift'inin kopyası
select_for_transfer(candidates, drift, f_agent=...) → drift'i yalnız OKUR
```

⇒ **Birincil uç nokta `F_agent`'ı hiçbir yoldan göremiyor.** *"`f_agent=None`,
birincil ile aynı test"* hangi değer verilirse verilsin **bit düzeyinde aynı**
`a_s`/`b_s` üretir. Dördüncü bir kol, bilinen bir cevabı ~%33 koşum süresiyle
satın alırdı. Bulgu teste bağlandı: `test_birth_drift_cannot_see_f_agent_at_all`.

**Sunulan üç seçenek ve Yasin'in kararı (§2.3 kapısı):** ① gölge kayıt ·
② tam dördüncü kol · ③ şimdilik dokunma. **Seçilen: ①.**

Transfer anında, gerçek kayıttan **sonra**, ikinci bir
`consolidate_generation(..., f_agent=None)` çağrılıyor ve yalnız *ne miras
kalırdı* kaydediliyor (`f_agent_none_*`, dört alan). Kasa açısından salt-okunur
olduğu denetlendi (`_candidates_from_store` yalnız `list_nodes` /
`get_record_payload` / `compute_memory_score` çağırıyor; `compute_memory_score`
da yalnız `get_node`/`get_edge`) ve **testle korunuyor**.

**Ölçülebilir kanal ölçüldü:** kapının farkı test ebeveyninde id kümesinde
**değil işaretlemede** — kapılı yolda travma negatif somatik ölçekli
*inherited warning* olarak geçiyor, legacy yolda işaretsiz geçiyor. Özdeşlik
bayrağı bu yüzden hem id'lere hem uyarı id'lerine bakıyor.

### Mutasyon kontrolü (§2.4) — on bir testin hepsi için koşuldu

S5: kayıt çağrısını kaldır (**3** kırılma) · sayacı `event.timestamp` yerine
`len()`'den üret (1) · `crisis`'i sabitle (1) · iki travma okumasını aynı
kaynağa bağla (2) · yokluğu `0` yap (1) · sırayı 0-tabanlı yap (2) · izi
`Gen2Result`'a bağlama (1) · yaşam başında tamponu sıfırlama (1).
S6: gölgeyi gerçek `f_agent` ile çağır (1) · özdeşliği yalnız id kümesine bağla
(1) · gölge sayacını gerçek kayıttan oku (1). **Hepsi yakalandı.**

### Sınırlar

Aletleme **çalıştırılmadı** — hiçbir koşum yapılmadı, bu kayıt yalnız verinin
artık üretildiğini söylüyor, ne söylediğini **değil**. S5'in iki okumasından
hangisinin ön-kayıta gireceği, ve S6'nın gölge kanalının hangi testle
sınanacağı **ikinci ön-kayıtın işi**. Gölge kaydın maliyeti kasa üzerinde bir
geçiş; 40 seed × 3 kolda ölçülmedi, tahmin edilmedi.

---

## D-064 · 2026-08-13 · W3 çözünürlük envanteri: birincilin ayırt etme gücünü **51/120 kolda var olan** bir kanal taşıyor

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** · GPU yok · koda
dokunulmadı · kaynak: B2'nin iki batch'i (40 seed × 3 kol) · ham çıktı
`dau_runs/w3_endpoint_resolution.json`

### Soru ve sınır

D-056 birincilin *"%99'unun sabit"* olduğunu ölçtü. W3 alternatif uç noktaların
**çözünürlüğünü** sorar: kaç farklı değer alıyorlar, kaç seed'de kollar özdeş?

⚠ **Yalnız çözünürlük, ETKİ DEĞİL.** Script hiçbir kol karşıtlığı hesaplamıyor —
kolların farklı olup olmadığını sayıyor, **hangi yönde** farklı olduğunu değil.
Hangi uç noktanın büyük `lived−shuffle` farkı verdiğine bakıp seçmek post-hoc
tuning olurdu (§2.7, L9). Ölçüler sonuçlara bakılmadan önce sabitlendi.

⚠ **Çözünürlük ≠ duyarlılık.** D-044/D-045 tam da yüksek çözünürlüklü ΔPE uç
noktasının ayrımın **%80–86'sını attığını** ölçtü. Aşağıdaki tablo *"ölçebilir
mi"* sorusunu cevaplıyor, *"iyi mi"* sorusunu **değil**.

### Envanter (120 kol; `n_dist` = farklı değer, `modal%` = en sık değerin payı)

| Uç nokta | n_dist | modal% | 3 kol özdeş | `lived`=`shuffle` |
|---|---|---|---|---|
| `arm_digest` · `gen1 delta_pe` (S3) · `pe_after` · faz-2 yörüngeleri | **120** | 0.8% | 0/40 | **0/40** |
| `gen2 mean_pe` (S4) · `gen2 pe_list` | 96 | 2.5% | 5/40 | 10/40 |
| `gen2 pe_gap_max` | 89 | 3.3% | 5/40 | 11/40 |
| **`birth_drift_magnitudes` (BİRİNCİL)** | **73** | 10.8% | 5/40 | **11/40** |
| `consolidation deleted_count` | 31 | 8.3% | 1/40 | 4/40 |
| `consolidation edges_created` | 27 | 17.5% | 3/40 | 6/40 |
| `gen2 n_unique` | 14 | 21.7% | 11/40 | 17/40 |
| `n_transfer_candidates` · `n_inherited_warnings` (S2) · `n_retrieval_context` | 8 | 38.3% | 13/40 | 19/40 |
| `f_agent_delta_pool` | 6 | 86.7% | 32/40 | 34/40 |
| `birth_drift_flags` (S1) | 4 | 47.5% | 11/40 | 18/40 |
| **`gen1 n_unique` · `gen1 pe_gap_max`** | 39 / 17 | — | **40/40** | **40/40** |
| **`f_agent` · `fitness_class`** | **1** | 100% | 40/40 | 40/40 |

### Bulgu 1 — dört uç nokta **yapı gereği kör**, gürültüden değil

`gen1` bloğundaki `n_unique` ve `pe_gap_max` `_phase1_diversity`'den geliyor ve
**faz-1** adapter yüklenmeden önce koşuyor (`run_gen1_arm_lineage`, grep ile
doğrulandı) ⇒ üç kolda özdeş olmaları **zorunlu**, 40/40 ölçümü bunun teyidi.
`f_agent`/`fitness_class` 120 kolda tek değer (D-060). Bu dördü aday listesinden
**ölçümle değil yapıyla** düşüyor.

### Bulgu 2 — birincilin çözünürlüğünü taşıyan kanal, kolların **çoğunda yok**

Birincil üç alanlı bir vektör. Alan alan:

| Alan | kaç kolda var | n_dist | 3 kol özdeş |
|---|---|---|---|
| `resource` | **120/120** | 12 | **38/40** |
| `social` | **51/120** | 51 | 9/40 |
| `uncertainty` | 16/120 | 14 | 29/40 |

Kol başına alan kümesi: yalnız `resource` **51**, `resource+social` 53,
`resource+uncertainty` 11, üçü birden 5.

⇒ D-056'nın *"%99 sabit"* cümlesi **`resource` kanalına aitmiş**: her kolda var
ve 38/40 seed'de kollar arasında özdeş. Birincilin ayırt etme gücünün neredeyse
tamamını **`social`** taşıyor — ve `social` kolların **%42.5'inde hiç yok**.

**Mekanizma sayıyla:** `social`'ın üç kolda da bulunmadığı **9** seed var;
`lived`=`shuffle` olan **11** seed'in **7'si** bu dokuzun içinde. Yani birincilin
"göremediği" seed'lerin çoğunluğu, taşıyıcı kanalın hiç açılmadığı seed'ler.
Kalan 4'te (2013, 2014, 2032, 2043) `social` var ama kollar yine de özdeş.

### Ne değişti, ne değişmedi

⇒ **Uç nokta seçilmedi.** Bu kayıt aday havuzunu *ölçebilirlik* ekseninde
sıralıyor; seçim ikinci ön-kayıtın işi ve **etkiye bakılarak yapılmayacak** (L9).
⇒ **İkinci ön-kayıta yeni bir soru girdi:** birincil bir vektör olarak mı kalsın,
yoksa taşıyıcı kanalın varlığı bir **geçerlilik ön-koşulu** mu olsun (ör.
*"`social` üç kolda da kapalıysa o seed birincil için ölçülemez"*)? ⚠ Bu bir
**tasarım kararı** (D-007) — B2 verisine bakarak karara bağlanamaz, çünkü hangi
seed'lerin düşeceği zaten biliniyor.

### Sınırlar

Tek koşum (B2, 40 seed), tek evren — D-056 o evrenin ajanları ayırmadığını
gösterdi, yani buradaki çözünürlük sayıları **bu evrene özgü** olabilir. Tam
eşitlik (float) kullanıldı: "özdeş" bit düzeyinde demek. Yörünge uç noktaları
(120 farklı değer) yüksek çözünürlüklü görünüyor ama **hiçbiri test edilmedi**;
D-044'ün iptal bulgusu tam da yüksek çözünürlüğün duyarlılık anlamına
gelmediğini gösteriyor. Hiçbir kol karşıtlığı hesaplanmadı, bilerek.

---

## D-065 · 2026-08-13 · DR brief #4 cevaplandı: mutabakat §J, bir kaynak yanlış atıflı, A4 sıralaması bağımsız olarak doğrulandı

**Durum:** mutabakat (D-006 zorunlu adımı) · **Etiket:** kod değişmedi ·
ham cevap `docs/research/2026-08-13_DR4-answer-raw.md` · tablo
`docs/research/RECONCILIATION.md` **§J** (J1–J20)

### Kaynak denetimi — önce yapıldı, çünkü kullanılamayacak kaynağı tartışmanın anlamı yok

Brief §0 yazar+yıl+kalıcı kimlik şart koşmuştu. Rapor on iki kimlikten
**beşini** eksiksiz verdi ve **birini yanlış makaleye** bağladı.

- ✅ **Doğrulandı (Crossref/arXiv, bugün):** Pepper & Smuts 2002
  (`10.1086/341018`) · Santos & Pacheco 2005 (`10.1103/PhysRevLett.95.098104`) ·
  Mesoudi, Whiten & Laland 2006 (`10.1017/S0140525X06009083`) · Piatti vd.
  2024 GovSim (`arXiv:2404.16698`).
- ✅ **Rapor "doğrulanamadı" demişti, biz doğruladık:** `arXiv:2604.21255`
  (Yang vd. 2026, tool-use damıtma benzerliği) · `arXiv:2606.18263`
  (Bhattacharyya vd. 2026, persona manifold collapse) · Mouret & Clune 2015
  MAP-Elites (`arXiv:1504.04909`) · Dykhuizen, Dean & Hartl 1987
  (*Metabolic flux and fitness*, Genetics 115:25–31).
- ❌ **Yanlış atıf:** `10.1007/s00778-019-00574-9` *"Cleasby vd. 2019"* diye
  verilmiş; o DOI **Su, Liu, Zheng, Zhou, Zheng**, *A survey of trajectory
  distance measures*, **VLDB Journal 2020**. Kastedilen makale gerçek ama
  başka yerde: Cleasby ve ark., **Behav. Ecol. Sociobiol. 73 (2019)**.
  **Bu projede yedinci kaynak kimliği hatası.**
- ❌ **Kimlik değil:** *"MDPI 2072-4292"* — o bir dergi ISSN'i (*Remote
  Sensing*), yazar/yıl/başlık yok ⇒ iddia **kullanılmadı**.
- ⛔ **Kullanılmadı:** Reidys & Stadler 2001 · Ackley & Littman 1992 ·
  Hinton & Nowlan 1987 · Sherratt & Morand-Ferron (kimlik yok) ve
  **kaynaksız "N=20–50 popülasyon alt sınırı"** sayısı.

### Alınan üç şey

1. **J9 — azalan getiri (Dykhuizen vd. 1987).** Akı, aktivitenin **içbükey**
   fonksiyonu; doyumda **seçilim nötrleşir**. Bu hem bugünkü durumumuzun
   teşhisi hem de A4-①'in **biçim** reçetesi: *"çıkarım = enerji"* doğrusal
   bağı defect'i baskın bırakır, kazanç eğrisi içbükey olmalı. D-061
   *"toparlanma terimi yeniden tasarlanmalı"* demişti ama biçimi
   söylemiyordu — **eksik parça buydu**.
2. **J4 — GovSim (Piatti vd. 2024).** En güçlü modeller bile ortak kaynak
   ikileminde sürdürülebilirlik kuramıyor (<%54 hayatta kalma). ⇒ Bizim
   **%94–100 defect** oranımız evrenimizin özel kusuru **değil**, alanın taban
   gözlemi. Bir alternatif açıklama elendi.
3. **J20 — sıralama.** Rapor bağımsız olarak *"popülasyon tek başına düz
   manzarayı aşmaz, önce bedel gerekir"* dedi. `CLAUDE.md`'nin **① önce,
   sonra ②** önerisiyle aynı.

### Reddedilen / düzeltilenler

- **J17 — DR'nin olgusal hatası.** Birincilimizi *"ağırlık vektörü L-normu"*
  sanıp S6'nın yarısını AdamW gürültüsü üstüne kurmuş. Birincil ağırlık
  değil: varisin **doğum-drift büyüklük vektörü**, gen2 koşmadan alınıyor ve
  varis ebeveynin adapter'ını **almıyor**. ⚠ Hatanın yarısı **bizim**: brief
  §2.5 birincili *"doğum-drift vektörü"* diye adlandırıp neyin vektörü
  olduğunu yazmamıştı.
- **J18 — DTW'yi şimdi birincil yapmak.** İki sorun: önerdiği şey uç nokta
  değil **karşıtlık** (bizimki `null` çapasına uzaklıkları karşılaştırıyor);
  ve yörünge uç noktalarının daha büyük ayrım gösterdiğini **zaten ölçtük**
  (D-044/D-045) ve bilerek almadık — etkiyi görüp uç nokta seçmek post-hoc
  olur (§2.7, L9). **Sıralama korunuyor**, araç ikinci ön-kayıta gidiyor ve
  orada **etkiye bakılmadan** kilitlenecek (D-064'ün envanteri bunun yolu).
- **J5 — kapsam kayması.** Damıtma kaynaklı homojenizasyon **modeller arası**
  bir olgu; bizde tek model, tek ajan. Bizim çöküşümüzün açıklaması
  bedelsizlik (D-060 §2.3), damıtma değil.
- **J7 — ad alınmadı.** *"Verbal alignment masking"* için gösterilen kaynak o
  iddiayı taşımıyor. Olgu bizde ölçülü (L14), ama adı kaynaksız kalıyor.
- **J14 — kaynaksız eşik.** N=20–50 sayısı kilitli karara giremez; brief #1'in
  dersi (`r≥0.85` varsayımı) birebir tekrar ediyor.

### A4 için durum

Öneri **değişmedi: ① önce, sonra ②.** Rapor bunu iki bağımsız yoldan
destekledi (mekanizma J9, sıralama J20). ③ (prompt priming) için tablo
karıştı: J4 prompt düzeyindeki **karar kuralı** önselinin ölçülmüş bir
kaldıraç olduğunu gösteriyor, J6 ise **persona** zenginleştirmenin çeşitlilik
satın almadığını. İkisi çelişmiyor; fark eklenen şeyin ne olduğunda.

⚠ **Karar Yasin'in (D-007) ve henüz verilmedi.** ①'in içinde en az üç alt
seçim var: kazanç eğrisinin biçimi · ölüm eşiği olacak mı · `METABOLIC_FLOOR`'un
çifte rolü (asgari tüketim **ve** azami toparlanma) ayrılacak mı. Ayrıca ①
`F_agent`'a dokunduğu için **GAP-19 aynı anda düzeltilmeli** (D-051/L16).

### Sınırlar

Bu bir mutabakattır, ölçüm değil: §J'nin hiçbir satırı DAU'da yeni bir sayı
üretmedi. Doğrulanan kimlikler **kimlik** doğrulamasıdır — makalelerin
içeriği okunmadı, yalnız başlık/yazar/yıl eşleşmesi denetlendi. GovSim'in
%54 rakamı ve "evrenselleştirme" etkisi rapordan alındı, **makaleden
okunmadı**; ikinci ön-kayıta girecekse önce okunmalı.

---

## D-066 · 2026-08-13 · A4-①: metabolik döngü kapandı — hasat enerjiye dönüyor, tükenmek öldürüyor

**Durum:** tasarım kararı + uygulama · **Karar: Yasin'in** (üç kapı, üç onay:
① metabolik döngü · doygun/hiperbolik kazanç · ölüm eşiği başlangıç
dokunulmazlığıyla) · **Kod:** `a7b157f` · suite 367 → **378**

### Neden ① ve neden şimdi

D-060/D-061 seçilim katmanının atıl olduğunu ölçtü: `F = 0.4·(E/E_max) +
0.3·(1−|Δhavuz|/P_max) + 0.3·survival` üç girdisinin ikisi sabit (`E`=0.000
120/120 kolda, survival=1.0 120/120), üçüncüsü %0.7 yayılıyordu. Ayrım
üretmeyen evrenin kökü buydu, ve DR #4 (D-065) sıralamayı bağımsız olarak
doğruladı: **popülasyon tek başına düz manzarayı aşmaz, önce bedel gerekir.**

### Üç parça — biri olmadan diğerleri anlamsız

**1. Havuz fiziği: kusur düzeltmesi, ayar değil.** `step_pool` havuzu
`POOL_MIN`'de clamp'liyor ama deftere **istenen** miktarı yazıyordu. Boş
meradan *"8.0 aldım"* fiziksel olarak gerçekleşmemiş bir olaydı ve deftere
öyle geçiyordu. ⇒ `agent_delta_pool` **kararın sınıfını** topluyordu, ortak
kaynağı değil — D-060'ın 393.55 ≈ 50×8 değerinin ve %0.7 yayılımın sebebi bu.
Artık defter **teslim edileni** yazıyor (`realized_extractions`), kısa düşen
havuz isteme oranlı paylaşılıyor.

⚠ **Bu olmadan ① ölü doğardı:** çökmüş havuzdan enerji akmaya devam eder,
defect yine bedelsiz kalırdı.

**2. Kazanç eğrisi içbükey, doğrusal değil.**
`gain(x) = 0.50 · x / (2.0 + x)`, `x` = **gerçekleşen** hasat.
Dayanak D-065/J9 (Dykhuizen, Dean & Hartl 1987, *Metabolic flux and fitness*,
Genetics 115:25–31, kimliği bizim doğruladığımız): akı, aktivitenin
**içbükey-hiperbolik** fonksiyonudur ve **doyumda seçilim nötrleşir**.
Doğrusal *"hasat = enerji"* bağı defect'i kesin baskın bırakır ⇒ düz manzarayı
yeni kostümle geri getirirdi.

Sonuç **aritmetik, ayarlanmış değil:** COORDINATE (1.0) → 0.167 ·
COOPERATE (2.0) → 0.250 · DEFECT (8.0) → 0.400 ⇒ **4× havuz hasarı 1.6×
enerji** satın alıyor. Çökmüş havuz **0.0** veriyor.

Kredi `pool_step_node`'da veriliyor, değerlendirici'ye dokunulmadı: enerji bir
sonraki olayın başında görünüyor (yedin, sonra gücün var). Denetlendi —
`internal_state`'i yazan tek başka düğüm değerlendirici ve o **önce** koşuyor,
`meta_observer` bu alana dokunmuyor ⇒ ezme yok.

**3. Ölüm.** `AB_ENERGY_FLOOR = 0.15`, `TERMINATION_ENERGY = 0.05`'in
**üstünde** oturuyordu ⇒ `effective_energy` asla ölüm eşiğine inemiyordu,
yani **ölüm yapısal olarak imkânsızdı** ve survival terimi 120/120 kolda 1.0
okuyordu. Yastık artık yalnız **doğum geçişini** kapsıyor
(`METABOLIC_GRACE_EVENTS`); sonrasında tükenmek yaşamı bitiriyor.

### Sabitler — üçü de **kalibre değil**, ve alet kimliği bunu söylüyor

| Sabit | Değer | Çapa (yapısal, ölçümden seçilmedi) |
|---|---|---|
| `METABOLIC_GAIN_MAX` | 0.50 | `METRIC_MAX`'ın yarısı ⇒ **tek olay depoyu dolduramaz** |
| `METABOLIC_GAIN_HALF_SATURATION` | 2.0 | `EXTRACTION_COOPERATE` ⇒ işbirlikçi hasat yarı-doyum noktası |
| `METABOLIC_GRACE_EVENTS` | 10 | fazın beşte biri ⇒ doğum geçişi |

`METABOLIC_GAIN_CALIBRATED = False` ve `build_tool_identity` bir
`metabolism` bloğu yazıyor (U5/D-030 deseni: kalibre edilmemiş eşik yerleşmiş
gibi okunmasın). **Değerleri ikinci ön-kayıt kilitler.**

### Kasıtlı test kırılması (Faz kuralı A.3, aynı commit)

`test_step_pool_over_extraction_causes_collapse` deftere **90.0** yazıldığını
doğruluyordu; artık teslim edilen **82.4**. Gerekçe testin içine yazıldı.

### Mutasyon kontrolü — sekiz mutasyon, biri ilk denemede **yakalanmadı**

Yakalananlar: defteri yine istenen miktara bağla (**4** kırılma) · kazancı
doğrusallaştır (3) · enerji kredisini kaldır (2) · krediyi gerçekleşen yerine
istenenden hesapla (1) · yastığı yine tüm koşuma yay (1) · kimlik bloğunu
kaldır (1) · kimliği kalibre gibi raporla (1).

⚠ **Yakalanmayan:** *"kimlikte sabiti yeniden üret"* (`METABOLIC_GAIN_MAX`
yerine literal `0.5`). Test sabiti **kendi değeriyle** karşılaştırıyordu, yani
sahte bir blok da geçiyordu — **§2.8'in tam deseni**, ve bu sefer testin
kendisinde. Test, sabiti oynatıp kimliğin **takip ettiğini** doğrulayacak
biçimde yeniden yazıldı; mutasyon o zaman yakalandı.

### ⚠ Sonuçları

- **`dau_runs/`'daki hiçbir koşum bugünün aletiyle karşılaştırılamaz.**
  Evrenin fiziği değişti — D-036/D-037/D-042'den daha büyük bir kırılma.
- **Yaşam uzunluğu artık sabit değil.** Ölüm mümkün ⇒ `n_events` kollar
  arasında değişebilir ⇒ çift sayısı, `arm_digest`, güç hesabı etkilenir.
  ⚠ İkinci ön-kayıtın N hesabı bunu içermeli.
- ⏳ **GAP-19 şimdi tetiklendi.** D-051 gizli bağımlılığı yazmıştı: *"L1
  düzeltilir de sayaç düzeltilmezse GAP-19 anında canlanır."* `F_agent` artık
  dejenere değil ⇒ `select_for_transfer`'ın `f < LOW ∧ travma` dalı her zaman
  ateşlemeyecek ⇒ travma-dışı anılar aktarılabilir hale gelecek ⇒ tutulup
  tutulmayacakları **kırık saatle** hesaplanacak. **Bir sonraki iş budur ve
  koşum ondan önce başlatılamaz.**

### Sınırlar

**Hiçbir koşum yapılmadı.** Bu kayıt fiziğin değiştiğini söylüyor, yeni fiziğin
ne ürettiğini **değil**. Kazancın enerjiyi gerçekten dalgalandırıp
dalgalandırmadığı, ölümün ne sıklıkta olduğu, ve `F_agent`'ın gerçekten
yayılıp yayılmadığı **ölçülmedi** — küçük bir pilot şart. Üç sabit de
kalibre değil ve ⚠ **parametreleri sonuca bakarak ayarlamak post-hoc
tuning olur** (§2.7): pilot **yönü** gösterebilir, değeri seçemez.

---

## D-067 · 2026-08-13 · GAP-19 kapandı: kasa nerede kaldığını hatırlıyor

**Durum:** tasarım kararı + uygulama · **Karar: Yasin'in** (üç seçenek sunuldu:
kasa tabanı · açık faz kaydırması · önce ölç sonra düzelt) · **Kod:** `7c76a8c` ·
suite 378 → **384** · **Tetikleyen:** D-066

### Neden şimdi — D-051'in gizli bağımlılığı ateşlendi

D-051 GAP-19'u ölçmüş ama **değiştirmemişti**, çünkü kırık saatin birincile
giden yolunu iki dejenerelik kesiyordu: `should_forget` travmayı hiç silmiyor,
ve `f_agent = 0.000` olduğu için varise **yalnız travma** geçiyordu. Kayıt şunu
yazmıştı: *"L1 düzeltilir de sayaç düzeltilmezse GAP-19 anında canlanır. İkisi
birlikte düzeltilmeli ya da hiçbiri."*

**D-066 `F_agent`'ı canlandırdı** ⇒ `select_for_transfer`'ın `f < LOW ∧ travma`
dalı artık her zaman ateşlemeyecek ⇒ travma-dışı anılar aktarılabilir hale
gelecek ⇒ tutulup tutulmayacakları **kırık saatle** hesaplanacaktı. Tetik
çekildi, ve borç aynı gün ödendi.

### Mekanizma (D-051'de doğrulanmıştı, burada düzeltildi)

Faz-2 `initial=None` ile başlıyor ⇒ `event_log` boş ⇒
`EventClock(counter=len(state.event_log))` **sıfırdan** sayıyor — ama kasa
faz-1 ile **ortak**. İki fazın anıları aynı `[1,50]` aralığını paylaşıyordu ve
`_consolidate_gen1` 50'yi *"şimdi"* sayıyordu:

| | kırık saat | gerçek |
|---|---|---|
| faz-1'de 48. olayda son kullanılan anı | `t = 2` ⇒ `R = 0.72` ⇒ **kalır** | `t = 52` ⇒ `R = 0.0002 < R_MIN` ⇒ **silinir** |

### Seçilen çözüm: yaş kasanın özelliği, gövdenin değil

`MemoryStore` bir `counter_base` tutuyor. **Kural:** kasaya giren her sayaç
**faz-yereldir**, ve çeviriyi (`vault_counter`) yalnızca kasa yapar. Yaşam
bitince `seal_phase` çağrılıyor ve bir sonraki yaşam onun üstüne sayıyor.

- ⚠ **Bütçeyle değil yaşananla mühürleniyor:** D-066'dan sonra yaşam erken
  bitebiliyor; `n_events` ile mühürlemek kasayı **ajanın yaşamadığı zaman
  kadar** yaşlandırırdı.
- **Ajanın prompt'undaki `event_count` değişmedi** — faz-2'nin *"taze gövde"*
  tasarımı ona bağlıydı ve korundu.
- **Demo yolu birebir aynı:** yeni kasa `COUNTER_BASE_NEW_VAULT = 0` ile
  başlıyor, hiç mühürlenmezse hiçbir şey değişmiyor.
- **5 Yasak #3 ihlal edilmiyor:** saat hâlâ saf olay sırası; yalnız **başlangıç
  noktası** gövdeyle değil kasayla taşınıyor.

**Reddedilen alternatifler:** *açık faz kaydırması* (`counter_offset` parametresi)
— daha dar ama üçüncü bir faz eklendiğinde kaydırmayı vermeyi unutmak serbest;
*önce ölç sonra düzelt* — D-051'in *"ikisi birlikte ya da hiçbiri"* şartını
esnetirdi.

### Mutasyon kontrolü — yedi mutasyon, **ikisi ilk turda yakalanmadı**

Yakalananlar: yazım yine faz-yerel damgalar (1) · hatırlama yine faz-yerel
damgalar (1) · taban hiç ilerlemez (3) · yaşam kasayı mühürlemez (1) · mühür
bütçeyle atılır (1).

⚠ **Yakalanmayanlar: konsolidasyon ve getirim çevirisi** — yani D-051'in tarif
ettiği hatanın **tam yaşadığı iki yer** bekçisizdi. Yazma yolunu test etmek
okuma yolunu test etmiş sayılmıyor. İki test eklendi:

1. **Uyku, faz-1 anısını gerçek yaşıyla yargılıyor mu** — `t = 52`'de trace
   siliniyor; kırık saatte `t = 2` ile kalıyordu.
2. **Getirim, ajanın kaçıncı yaşamda olduğundan bağımsız mı** — aynı yaştaki
   iz, birinci yaşamda da ikinci yaşamda da aynı skoru almalı.

⚠ İkinci test **ilk yazılışında da yakalamıyordu**: *"yeni olan daha yüksek
skor alır"* sıralaması çevirisiz de doğru çıkıyordu (çevirisiz `t < 0` olup
retention 1'in üstüne çıkıyor ve sıra yine tutuyordu). **Saat-kayması
değişmezliğine** çevrildi; o zaman yakaladı.

### ⚠ Sonuçları

- **Unutma davranışı değişti** ⇒ konsolidasyonun sildiği anı sayısı, dolayısıyla
  varise geçen küme değişecek. D-031'in ölçtüğü `deleted_count` ort. 24.90
  **artık geçerli değil**.
- D-066 ile birlikte: **`dau_runs/`'daki hiçbir koşum bugünün aletiyle
  karşılaştırılamaz.**

### Sınırlar

Yine **hiçbir koşum yapılmadı**. Kırık saatin düzeltilmesinin varise geçen
kümeyi *ne kadar* değiştirdiği ölçülmedi — D-051 etkinin o zaman **sıfır**
olduğunu göstermişti, ama o iki dejenereliğin ikisi de artık kalkıyor. Gen2
kasası da aynı mühürleme yolundan geçiyor (varis yaşamı üçüncü faz olarak
sayıyor); bu **tasarım gereği** ama **ölçülmedi**.

---

## D-068 · 2026-08-13 · Metabolik evren pilotu: seçilim katmanı **canlandı**, ölçüm penceresi **kırıldı**

**Durum:** ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** · N=2 (seed
4001–4002), `--lora`, 50 olay bütçesi · `run_quality = flagged` · ham çıktı
`dau_runs/pilot_d066_metabolic_n2.json`

### Soru

D-066 ve D-067 fiziği değiştirdi ama **hiçbir şey ölçülmemişti**. Pilotun beş
sorusu: enerji dalgalanıyor mu · ölüm oluyor mu · `F_agent` yayılıyor mu ·
`Δhavuz` ayrışıyor mu · konsolidasyon ne siliyor.

⚠ İlk deneme `--no-lora` ile koşuldu ve **I2.1 abort etti** (*"identical arms"*)
— kapı doğru davrandı: eğitim yokken üç kol özdeş. Kayda değer, çünkü fizik
sorusu kol ayrımı gerektirmiyordu ama alet geçerli koşum istiyor.

### Cevaplar

| Soru | Cevap |
|---|---|
| Ölüm oluyor mu | ✅ **Evet.** Faz-1 yaşamları **19** (seed 4001) ve **10** (seed 4002) olayda bitti, 50 bütçesine karşı |
| `F_agent` yayılıyor mu | ✅ **Sınıf bariyeri kırıldı.** 0.2076 (`low`) vs **0.4135 (`normal`)**. B2'de 120/120 kol `low` ve `f_agent=0.000`'dı |
| `Δhavuz` ayrışıyor mu | ✅ **130.8 vs 62.2.** B2: 393.55 ± 2.62, altı farklı değer, yayılım %0.7 |
| Enerji dalgalanıyor mu | ⚠ **Kısmen — aşağıya bak** |
| Konsolidasyon | ✅ değişti: silinen 9/8/9 ve 4/3/3. D-031'in ölçtüğü ort. **24.90 artık geçerli değil** |

**Bedel mekanizması çalışıyor, gözle görülür biçimde.** Seed 4002'nin gen2
havuzu 8. olayda tabana vuruyor (`pool_ratio` 0.372 → 0.000) ve **gerçekleşen
hasat 8.0 → 6.17 → 0** diye düşüyor: D-066'nın defter düzeltmesi canlıda
ateşledi. Her yaşamda **3 olay sıfır hasatla** geçiyor.

**Ayrım artık uç noktalara da ulaşıyor:** `lived`-4001'in varisi gen2'de
**17 olay** yaşadı, `null`/`shuffle`'ınki **20**. Yaşam uzunluğu kola göre
değişiyor — B2'de böyle bir kanal **yoktu**. Ayrıca `lived`-4001'in doğum
drift'i `{'energy': True, 'resource': True}` — **`energy` alanı ilk kez
bayraklandı**.

### ⚠ İki yeni sorun, ikisi de bu koşumun ürettiği

**1. Enerji terimi hâlâ ölü — ama artık BAŞKA bir sebeple.** `E_final = 0.000`,
altı kolun altısında. Sebep formül değil **seçilim**: ajanlar tükenerek
ölüyor, ve tükenerek ölen bir ajanın son enerjisi tanımı gereği sıfır.
`F_agent`'ın en büyük ağırlığı (0.4) yine bilgi taşımıyor; yayılımın tamamı
`survival` ve `Δhavuz`'dan geliyor. ⇒ **Ölçüm anı yanlış:** ya yaşam boyu
ortalama enerji, ya sabit bir olaydaki enerji alınmalı. **Tasarım kararı.**

**2. Uç nokta padding'e boğuldu.** I3.4: gen1'de **426/600 slot padding
(%71)**, I3.1 PE kapsaması 0.29'a düştü. Alet her kolda bunu bastı:
*"PE trace 19/50 events — mean is padding-dominated, arm not measurable"*.
⇒ **Sabit 50 olaylık pencere, ölümün mümkün olduğu bir evrende çalışmıyor.**

⚠ Bu yüzden bu koşumun `pe_after` sayıları (`lived` 0.5005 · `null` 0.4265 ·
`shuffle` 0.3500) **okunmayacak**. Aralarındaki fark padding oranından da
gelebilir; aletin kendisi ölçülemez diyor.

### ⚠ Davranış hâlâ çökmüş durumda

Hasat neredeyse her olayda **8.0 = DEFECT**. Evren artık bunun bedelini
kestiriyor (havuz çöküyor, hasat sıfırlanıyor, ajan ölüyor) ama **ajan
davranışını değiştirmiyor** — bedeli ödeyip aynı şeyi yapmaya devam ediyor.

Bu, D-065/J4'ün (GovSim, Piatti vd. 2024) **tam olarak rapor ettiği olgu**:
LLM ajanları ortak kaynak ikileminde kendiliğinden düzenlenmiyor, ve orada
ölçülmüş tek kaldıraç **bilişsel önsel** (evrenselleştirme) oldu.
⇒ **A4-③ (prompt/karar kuralı) artık spekülatif değil, sıradaki aday.**

### Ne değişti, ne değişmedi

⇒ ① **mekanik olarak çalıştı**: fitness girdilerinin ikisi (survival, Δhavuz)
canlandı, sınıf bariyeri kırıldı, bedel zinciri uçtan uca ateşledi.
⇒ Kalan darboğaz **davranışsal**, ve literatürde adresi belli.
⇒ ⚠ **Hiçbir sabit ayarlanmadı ve ayarlanmayacak.** Üç metabolik sabitin
değerini bu sonuca bakarak seçmek post-hoc tuning olur (§2.7). Pilot **yönü**
gösterdi: kazanç yeterli, ama ölçüm penceresi ve enerji okuma anı yeniden
tasarlanmalı.

### Sınırlar

**N=2**, tek evren, hipotez testi yok, `run_quality=flagged` (I3.1 · I3.2 ·
I3.4 · I1.3b). Kol karşılaştırması **yapılmadı ve yapılamaz** — hem N=2 hem
padding. `pi_n_distinct = 2` (I3.2) ⇒ precision mekanizması hâlâ atıl (L13).
Kırpma yine %100 (I1.3b, D-059 ile aynı). Gen2 kolları seed 4002'de birebir
aynı çıktı; seed 4001'de `lived` ayrıştı — **N=2'de bu gözlem, bulgu değil**.

---

## D-069 · 2026-08-13 · DR yerine yerel tarama: uç noktamızın adı **LOCF**'muş

**Durum:** literatür taraması + öneri · **Etiket:** ⚠ **DR raporu değil** —
Deep Research bu tur çalışmadı, tarama Claude Code tarafından yapıldı ·
**kod değişmedi** · mutabakat `docs/research/RECONCILIATION.md` **§K**

### Neden burada

K1 (uç nokta tanımı) ve K2 (enerji okuma anı) DR brief #5'i bekliyordu; DR
kullanılamadı. İkisi de *"literatürde X mi Y mi savunulabilir"* tipi (D-007
⇒ normalde DR'nin işi), ama **kaynak kimliği doğrulanabilir** sorular
olduğu için yerel tarama meşru bir ara çözüm sayıldı — Yasin onayladı.

**Yöntem:** sekiz kimlik Crossref üzerinden **açılıp** doğrulandı. ⚠ Yalnız
kimlik; **içerik okunmadı** (D-065'in sınırının aynısı).

⚠ **Tarama kendi yanlış atıfını üretti ve yakaladı:** Schoenfeld'in örneklem
makalesi için ilk aday `10.2307/2530643`'tü; açıldığında **Greenland & Robins
1985** çıktı. Doğrusu `10.2307/2531021`. ⇒ Doğrulama döngüsü **bize de**
gerekiyor, yalnız DR'ye değil.

### Bulgu 1 — ⭐ yaptığımız şeyin adı var ve eleştirisi yazılmış

`_pad_pe_list` diziyi **son gözlemle** 50'ye tamamlıyor, sonra ortalaması
alınıyor. Bu, literatürde **LOCF** (*last observation carried forward*).
Lachin (Clinical Trials, 2015, `10.1177/1740774515602688`) doğrudan bunun
eleştirisi: LOCF **muhafazakâr değildir**, yanlılığın yönü **iki tarafa da**
olabilir, ve varyansı **olduğundan küçük** gösterir.

D-068'de gen1'in **%71'i** pad'di ⇒ uç noktamızın çoğu artık LOCF çıktısı.

⇒ **İcat etmemiz gereken bir şey yok, bırakmamız gereken bir şey var.**

### Bulgu 2 — teşhis ve çözüm adları

- **Immortal time bias** (Suissa 2008, `10.1093/aje/kwm324`): hayatta kalma
  süresi pencereyi belirlediğinde ortaya çıkan yanlılık. Bizdeki karşılığı:
  sabit pencerede ortalama almak *"nasıl yaşadı"* ile *"ne kadar yaşadı"*yı
  karıştırıyor.
- **Landmark analizi** (Anderson, Cain & Gelber, J Clin Oncol 1983,
  `10.1200/jco.1983.1.11.710`): sabit bir ana kadar bekle, o anda hayatta
  olanları al, ölçümü oradan yap. Bizde doğrudan uygulanabilir.
- **Seri ölçümü özet istatistiğe indirgeme** (Matthews ve ark., BMJ 1990,
  `10.1136/bmj.300.6719.230`): *"yaşam boyu özet"* adayımızın karşılığı.
  ⚠ AUC ömürle **ölçeklenir** ⇒ olay-başına oran tercih edilmeli.
- **Rekabet eden riskler** (Fine & Gray, JASA 1999,
  `10.1080/01621459.1999.10474144`): not edildi, bu tur alınmıyor.
- **Joint models** (Henderson, Diggle & Dobson, Biostatistics 2000,
  `10.1093/biostatistics/1.4.465`): "değerin son hâlini ölüm mekanizması
  belirliyor" durumunun doğru aracı ⚠ ama ölçeğimizin çok üstünde.

### Bulgu 3 — K3'ün (N/güç) cevabı beklenmedik biçimde **lehimize**

Schoenfeld (Biometrics 1983, `10.2307/2531021`): zaman-olay analizinde güç
**denek sayısına değil olay sayısına** dayanır. Bizde **sansür yok** — her
ajan kesin ölüyor ⇒ **olay sayısı = soy sayısı**. Ömür uç noktası için güç,
sansürlü tasarımlardan **daha verimli**.

### Bulgu 4 — `F_agent`'ta çift sayım riski gerçek

Stearns (Functional Ecology 1989, `10.2307/2389364`): ömür bir yaşam-tarihi
**bileşenidir** ve uygunlukla takas ilişkisi içindedir. `F_agent`'ın %30'u
`t_surv/T_gen`; ölüm mümkün olunca ömür hem **girdi** hem **sonuç** oldu.
⇒ K4/K5 kararına girdi.

### Öneri (literatür değil, öneri — karar Yasin'in)

1. **LOCF bırakılır.**
2. **Birincil: landmark**, sabit bir olay indeksinde. ⚠ İndeks **yapısal**
   çapadan (`METABOLIC_GRACE_EVENTS = 10`, doğum geçişinin bitişi) seçilir —
   **ölçülen ölüm zamanlarına bakılarak değil** (L9).
3. Landmark'tan önce ölen soy için kural **önceden** ilan edilir; kaç soyun
   düştüğü bir **geçerlilik kriteri** olur, sonuç değil.
4. **İkincil:** yaşam boyu özet, **olay başına oran** olarak normalize
   (AUC değil — ömürle ölçeklenir, Bulgu 4'ün çift sayımını geri getirir).
5. **Enerji:** landmark değeri + zaman-integre ortalama; `E_final` bırakılır.
6. **Güç:** olay sayısı = soy sayısı, hesap Schoenfeld ile yeniden yapılır.

### Sınırlar

**Sistematik derleme değil, hedefli tarama** — bulunamamış bir alt literatür
olabilir. Üç şey **cevaplanamadı**: ALife geleneğinin kendi yaklaşımı ·
**landmark noktasının nasıl seçileceğine dair bir ilke** (yöntem var, seçim
kuralı yok — bu yüzden yapısal çapa öneriliyor) · küçük-N simülasyonda
örneklem gerekçelendirme standardı. ⇒ **DR brief #5 geçerliliğini koruyor**;
bu tarama K1/K2'yi karara bağlanabilir hale getirdi, **kapatmadı**.
Hiçbir kod değişmedi, hiçbir sabit seçilmedi.

---

## D-070 · 2026-08-13 · İkinci ön-kaydın yedi kilit kararı — **Yasin'in**

**Durum:** tasarım kararları · **Karar: Yasin'in** (D-007) · **kod henüz
değişmedi** — bu kayıt kararları sabitliyor, uygulaması ayrı commit'lerde ·
**girdiler:** D-064, D-068, D-069 (yerel tarama, §K)

### Kararlar

| # | Karar | Seçilen | Gerekçe |
|---|---|---|---|
| **K1** | PE tabanlı uç noktaların penceresi | **Landmark + olay-başına oran** | LOCF bırakılıyor (D-069/V1). Landmark yöntemi V3; oran ikincil |
| **K2** | Enerji okuma anı | **Landmark değeri + zaman-integre ortalama**; `E_final` **bırakılıyor** | `E_final`'i ölüm kuralının kendisi belirliyor (D-068) |
| **K3** | N ve güç | **Olay sayısı üzerinden** (V6, Schoenfeld 1983) | Sansür yok ⇒ olay = soy sayısı |
| **K4** | Üç metabolik sabit | **Olduğu gibi kilitlenir**, `CALIBRATED = False` **kalır** | Üçü de yapısal çapadan; pilota bakarak ayarlamak post-hoc olurdu (§2.7) |
| **K4-b** | `F_agent`'ın havuz terimi | **Olay başına normalize** | ⚠ aşağıdaki düzeltme |
| **K5** | Birincil uç nokta | **Landmark drift** (sabit yaşta okunan drift) | Ömür karışmasını keser |
| **K5-b** | `social` geçerlilik ön-koşulu | **Hayır** | D-064'ün kanal dağılımı **eski fiziğe** ait; yeni fizikte hangi kanalın taşıdığını bilmiyoruz (pilotta `energy` ilk kez bayraklandı) |
| **K6** | S5'in "ilk travma"sı | **Commons krizi** | S5 *"kriz anında davranış"* diyor; ölçü ajanın eylemine bağlı |
| **K7** | Davranış müdahalesi | **Hayır** | Aksiyomun ruhu: evrenin kısıtı şekillendirir, verilen kural değil. Çöküş **bulgu olarak** raporlanır |

### ⚠ D-068'in bir cümlesi düzeltiliyor

D-068 *"`Δhavuz` ayrışıyor mu → ✅ 130.8 vs 62.2"* diye yazdı. **Yayılımın
onda dokuzu ömürmüş:**

| seed | ham `\|Δhavuz\|` | yaşam | olay başına |
|---|---|---|---|
| 4001 | 130.8 | 19 olay | **6.88** |
| 4002 | 62.2 | 10 olay | **6.22** |
| | yayılım **%110** | | yayılım **%10.7** |

⇒ Bugünkü `F_agent` = 0.4·enerji (**ölü**) + 0.3·havuz (**≈ ömür vekili**) +
0.3·hayatta kalma (**ömür**) ⇒ skorun ~**%60'ı ömrü iki kez sayıyor**.
Stearns'in (D-069/V8) uyardığı çift sayımın ta kendisi. **K4-b bunu kesiyor.**

⚠ Terim normalize edilince **zayıflıyor** (%110 → %10.7). Kabul edildi:
*zayıf ve dürüst, güçlü ve yanıltıcıdan iyidir.*

### K5'in bedeli — ilan edilen sınır

Landmark drift, varise **aktarılan** şey **değildir**: varis yaşam sonundaki
drift'i miras almaya devam ediyor, ölçüm mekanizması değişmiyor. Değişen
yalnız **neyi birincil saydığımız**.

⇒ İkinci ön-kayıtta **ilan edilmiş sınır** olarak yazılacak: *"birincil uç
nokta, aktarılan drift'in kendisi değil, sabit yaşta okunan karşılaştırılabilir
kesitidir."* İddia cümlesi buna göre **daralır**.

### Yapısal tutarlılık (ölçümden seçilmedi)

Landmark = **10. olay** ve `METABOLIC_GRACE_EVENTS = 10`. Ölüm zaten grace
bitene kadar askıda olduğu için **her soy landmark'ta yapısal olarak
hayatta** ⇒ *"landmark'tan önce ölen"* kuralı hiç ateşlemez. Bu bir uyum
ayarı değil, iki sabitin aynı yapısal ana bağlı olmasının sonucu.

⚠ Yine de kural **yazılacak** (§2.9, sessiz fallback yasağı): grace ileride
değişirse kural sessizce boşa düşmemeli.

### Reddedilenler

- **`social` ön-koşulu** — eski ölçümle yeni evrene tasarım yapmak olurdu.
- **Havuz terimini kaldırmak** — commons tasarımının ruhuna aykırı.
- **Davranış önseli vermek** (her iki biçimde de) — aksiyom.
- **Kalibrasyon taraması** — taramadan değer seçmek post-hoc tuning.

### Sınırlar

**Hiçbiri uygulanmadı.** Bu kayıt yalnız kararları sabitliyor; kod
değişiklikleri (K4-b'nin normalizasyonu, landmark aletlemesi, LOCF'un
kaldırılması) ayrı commit'lerde ve her biri kendi mutasyon kontrolüyle
gelecek. Kararların **hiçbiri ölçüm sonucuna bakılarak** verilmedi; K4-b'nin
girdisi olan %10.7 rakamı bir **çift sayım teşhisi**, etki büyüklüğü değil.

---

## D-071 · 2026-08-13 · K4-b uygulandı — ve `F_agent`'ın hayatta kalma terimi hiçbir zaman ömrü ölçmüyormuş

**Durum:** kod değişikliği + ölçüm · **Karar: Yasin'in** (gate-and-confirm,
§2.3) · **commit `74834e6`** · **girdi:** D-070/K4-b · suite `388 passed`

### Uygulamadan önce çıkan çelişki (§2.11)

D-070'in K4-b gerekçesi *"bugünkü `F_agent` = 0.4·enerji (ölü) + 0.3·havuz
(≈ ömür vekili) + 0.3·hayatta kalma (ömür) ⇒ skorun ~%60'ı ömrü iki kez
sayıyor"* diyordu. Kod bunu doğrulamadı.

`f_agent_inputs`, `t_generation`'a **ajanın kendi ömrünü** veriyordu
(`max(t_survived, MIN_SURVIVAL_DENOMINATOR)`) ⇒ hayatta kalma terimi
`t_survived / t_survived` ≡ **1.0**, her soyda, bugüne kadarki **her
koşumda**. Terim ömrü ölçmüyordu; her soya sabit **+0.3** ekliyordu.

**Kanıt — pilotun iki soyu, `F = 0.3·(1 − |Δhavuz|/100) + 0.3` ile:**

| seed | `Δhavuz` | hesap | JSON'daki `f_agent` |
|---|---|---|---|
| 4001 | 130.7955 | 0.3·(−0.307955) + 0.3 = **0.2076134** | 0.20761337418662523 |
| 4002 | 62.1716 | 0.3·(0.3782844) + 0.3 = **0.4134853** | 0.41348533116013630 |

Enerji `0.000` (D-068), survival sabit `0.3` ⇒ yayılımın **%100'ü** havuz
teriminden geliyordu. ⇒ **D-068'in *"yayılımın tamamı `survival` ve
`Δhavuz`'dan geliyor"* cümlesi ve D-070'in K4-b gerekçesindeki *"0.3 hayatta
kalma = ömür"* teşhisi yanlış** (kayıtlar append-only; düzeltme burada).

⚠ **Bunun K4-b'ye doğrudan sonucu var:** ömrün `F_agent`'a girdiği tek yer o
kümülatif toplamdı. K4-b tek başına uygulansaydı ömür skordan **tamamen**
çıkacaktı — D-066'nın canlandırdığı ölüm kanalı fitness'ta görünmez olurdu.
`compute_fitness`'in **kendi docstring'i** (*"what fraction of the
generation's event span the organism endured"*) en baştan doğruyu söylüyordu;
çelişen `f_agent_inputs`'tı.

**Yasin'e soruldu, iki karar alındı** (§2.3, "adım içinde yeni karar noktası
çıkarsa tekrar sor"):

| Soru | Seçilen | Reddedilen |
|---|---|---|
| Hayatta kalma terimi | **Düzeltilsin — payda faz bütçesi** | Dokunma (ömür skordan tümüyle silinirdi) · Önce ölç (§2.7: sonuca bakıp formül seçmek post-hoc) |
| Olay başına ölçek | **`EXTRACTION_DEFECT = 8.0`** | `POOL_MAX` (stok ÷ akış, boyut hatası; terimi ~0.93'e sıkıştırır) · `EXTRACTION_PARSE_MAX = 25.0` (tasarım hedefi değil, kaçak ayrıştırmaya karşı emniyet freni) |

### Ne değişti

`F = w_e·(E/E_max) + w_p·(1 − (|Δhavuz|/t_survived)/X_max) + w_s·(t_survived/t_gen)`

- **Havuz terimi bir oran.** `X_max = EXTRACTION_DEFECT`, deterministik
  karar→sonuç tablosunun verebileceği en büyük hasat ⇒ terim davranışsal
  okunur: **1.0** havuza hiç dokunmadı, **0.0** her olayda defect etti.
  ⚠ Serbest metinden 8'in üstü ayrıştırılabildiği için terim negatife
  düşebilir; nihai kırpma sınırlıyor — ömür toplamı `POOL_MAX`'ı aştığında
  zaten böyleydi.
- **`t_generation` = fazın olay bütçesi**, zorunlu parametre, **varsayılan
  yok** (§2.9): fonksiyonun kendi başına ulaşabildiği tek değer zaten hataya
  yol açan ömrün kendisi.
- Bütçenin taşınması: `meta_observer_node` imzasını LangGraph sabitlediği
  için `graph.MAX_EVENTS`'ten **çağrı anında** okuyor (import fonksiyon
  içinde — `graph` bu modülü yüklüyor, `state.py` aynı döngüyü aynı biçimde
  kırıyor; her çağrıda çünkü her koşucu global'i bir yaşamın etrafında
  yeniden bağlıyor). `transfer_to_heir` ise **parametre** alıyor: oraya
  gelindiğinde `run_life_keep_vault` global'i `finally` bloğunda geri
  yüklemiş oluyor.

### Raporlama (§2.8)

`BirthDriftLog` → **`f_agent_t_survived` + `f_agent_t_generation`**. Havuz
terimi oran olduğu için `delta_pool` tek başına anlamsız, ve okuyanın
`t_generation`'ın `t_survived`'a çöküp çökmediğini **görebilmesi** gerekiyor.
`tool_identity` → **`fitness` bloğu** (üç ağırlık + `pool_term_per_event_max`):
aynı `f_agent` değeri artık iki farklı fizikten çıkabiliyor ve başka hiçbir
alan hangisinin koştuğunu söylemiyor.

### Mutasyon kontrolü (§2.4) — üçü de kırdı

| Mutasyon | Kıran test |
|---|---|
| havuz terimi `\|Δhavuz\|/POOL_MAX`'a geri | `test_pool_term_is_a_rate_not_a_lifetime_sum` |
| `t_generation` yeniden `t_survived` | `test_transfer_records_what_f_agent_was_computed_from` |
| `meta_observer` bütçeyi donduruyor (sabit 20) | `test_meta_observer_reads_the_live_event_budget` |

### Sınırlar

- **Hiçbir sabit sonuca bakılarak seçilmedi** (§2.7). `EXTRACTION_DEFECT`
  yapısal bir çapa (tablonun maksimumu), pilotun 6.88/6.22'sinden türetilmedi.
- **Pilotun `f_agent`'ları yeni formülle yeniden hesaplanamıyor.**
  `dau_runs/pilot_d066_metabolic_n2.json` `t_survived`'ı **kaydetmiyor** —
  yeni formül ona ihtiyaç duyuyor. Bu eksiklik zaten yeni iki alanın gerekçesi.
  ⇒ D-071 öncesi ve sonrası `f_agent` değerleri **karşılaştırılamaz**.
- Ölçülmedi: yeni formülün gerçek koşumda ne kadar yayılım ürettiği. Bu
  **kasıtlı** — etkiye bakıp formül seçmek L9/§2.7 ihlali olurdu.
- `METABOLIC_GAIN_CALIBRATED = False` **değişmedi** (K4).

---

## D-072 · 2026-08-13 · Landmark aletlendi — kollar artık aynı **yaşta** okunabiliyor

**Durum:** kod değişikliği (saf aletleme) · **commit `345c9f3`** ·
**girdi:** D-070/K1-K2-K5 · suite `400 passed`

### Neden

D-066'dan beri ömürler kola göre değişiyor (D-068: gen2'de `lived` 17 olay,
`null`/`shuffle` 20). Yaşam sonunda okunan her uç nokta **iki soruyu aynı anda**
cevaplıyor — kol ajanı nasıl değiştirdi, ve ajan ne kadar dayandı — ve ikincisi
birinciyi boğuyor. D-071 aynı confound'u `F_agent`'ın havuz teriminin **içinde**
buldu. Sabit ordinalde okumak kolları karşılaştırılabilir kılıyor.

⚠ **Bedeli D-070/K5'te zaten kabul edildi:** karşılaştırılan şey bir **kesit**,
yaşamın tamamı değil. İkinci ön-kayıtta ilan edilmiş sınır olarak yazılacak.

### Ne eklendi

| Nerede | Ne |
|---|---|
| `graph.py` | `_body_event_log` — olay başına enerji + drift; `reset_/get_body_event_log`, `_record_body_event` |
| `constraints.py` | **`LANDMARK_EVENT = 10`** |
| `run_cprime_multigen.py` | `_landmark_reading` — sabit ordinaldeki drift + enerji, artı **yaşam boyu ortalama enerji** |
| `run_protocol_c_prime.py` | `ArmResult`: `events_lived` · `landmark_reached` · `landmark_energy` · `landmark_drift_flags/magnitudes` · `energy_mean_over_life` |
| `tool_identity.py` | **`endpoints`** bloğu (`landmark_event`) |

**Satır nerede yazılıyor:** `pool_step_node`'un **sonunda** — döngünün son
düğümü orası: hasat girmiş, metabolik kredi uygulanmış, kriz travması drift
haritasını çizmiş. Daha erken yazılsa satır **hâlâ olmakta olan** bir olayı
anlatırdı. Drift **kopyalanıyor**: `DriftState` mutable ve ajan satır
yazıldıktan sonra da yaralanmaya devam ediyor.

**Hangi yaşamdan:** **faz 2**. Faz 1'de henüz adapter yok, üç kol özdeş —
faz 1'den okunan bir landmark kola göre **hiç** değişemezdi. Ayrıca aktarılan
drift'in geldiği yaşam da o.

**`E_final` neden bırakıldı (K2):** onu **ölüm kuralının kendisi** belirliyor.
Tükenerek ölen bir ajanın son enerjisi tanımı gereği 0.000 — pilotta altı kolun
altısı. Ortalama burada **zaman integralinin ömre bölünmüşü**: `EventClock`
birer birer tıklıyor ve her satır o olayın bir sonrakine kadar bıraktığı
enerjiyi tutuyor.

### `LANDMARK_EVENT = 10` ile `METABOLIC_GRACE_EVENTS = 10`

Ayarlanmış bir uyum **değil**, aynı yapısal anın iki kez görünmesi: grace doğum
geçişini örtüyor, karşılaştırmaya değer ilk ordinal onun hemen sonrası.

⚠ **Testi yazarken sınır bir kez yanlış çakıldı ve test yakaladı.** İlk hâli
*"landmark olayından sonra da yaşamaya devam eder"* diye iddia ediyordu;
`should_continue` `len(event_log) >= GRACE` olduğunda floor'u kaldırıyor, yani
**10. olay kapandıktan hemen sonra ölüm mümkün**. Doğru ifade: bir yaşam
**10. olayına ulaşmadan bitemez** — `should_continue`, N. olayın koşulup
koşulmayacağını `len(event_log)` N−1 iken soruyor. Test artık sınırı **iki
yönlü** çakıyor: `LANDMARK_EVENT − 1`'de tükenmiş ajan yaşamaya devam ediyor,
`LANDMARK_EVENT`'te ölüm mümkün hâle geliyor.

### Sessiz fallback yasağı (§2.9) — iki yol da gürültülü

- **Yaşam landmark'a ulaştı ama satırı yok** ⇒ `SystemExit`. Bu **bozuk
  alet**tir, kısa yaşam değil, ve ikisi satırlardan ayırt edilemez.
- **Yaşam landmark'tan önce bitti** ⇒ `NaN` + `[WARN]`, başka bir ordinalden
  **ikame yok**. Grace landmark'ı örttüğü sürece erişilemez; kural tam da bu
  yüzden yazıldı (D-070'in şartı).

### Dur-kontrol (⚠ keşifsel, ön-kayıtlı değil)

Mock LLM, 12 olaylık **gerçek akış**, tek kol, GPU'suz: **12 satır, ordinaller
1…12**, landmark 10'dan okundu, `energy_mean_over_life` hesaplandı.
⇒ Kalıcı teste çevrildi (0.25 sn). Gerekçe: grafik testleri satırın
**yazıldığını**, okuyucu testleri **doğru satırın seçildiğini** kanıtlıyor ama
aradaki **kavşağı** — yazılan ordinallerin okunanla uyuşması ve tamponun faz
2'nin sonundan drenaja kadar yaşaması — ikisi de görmüyor. S5'te (D-063/L20)
kırılan tam olarak orasıydı.

### Mutasyon kontrolü (§2.4) — beşi de kırdı

| Mutasyon | Kıran test |
|---|---|
| enerji krediden **önce** kaydediliyor | `test_body_event_log_records_energy_after_the_metabolic_credit` |
| drift kopyalanmıyor, referans veriliyor | `test_body_event_row_snapshots_drift_instead_of_aliasing_it` |
| landmark **son** satırdan okunuyor | `test_landmark_reading_reads_the_fixed_ordinal_not_the_last_event` (+3) |
| eksik satır abort etmiyor | `test_missing_landmark_row_on_a_long_life_aborts` |
| kol sonucu drenaj edilen logu okumuyor | `test_arm_result_carries_the_landmark_of_phase_two` |

### Sınırlar

- **Saf aletleme.** Hiçbir hesaplama değişmedi; `pool_step_node`'un döndürdüğü
  patch aynı (`drift_state` artık aynı nesneyi bir değişkenden veriyor).
- **Uç nokta henüz değişmedi.** Birincil hâlâ doğum-drift'ten okunuyor; landmark
  alanları **yanında** duruyor. Değişimi ikinci ön-kayıt yapacak (K5).
- **Landmark değerlerine bakılmadı** ve bakılmayacak (L9/§2.7): dur-kontrol
  alanların *dolduğunu* doğruladı, *ne söylediğini* değil.
- Society fiziği olmayan bir yaşamda satır **hiç yazılmıyor** (`pool_step_node`
  erken dönüyor). C′ yolunda `env_state` her zaman var; okuyucu bu durumu
  sessizce doldurmuyor, abort ediyor.

---

## D-073 · 2026-08-13 · LOCF kaldırıldı; `I3.1`'in paydası ve `I3.4`'ün modu düzeltildi

**Durum:** kod değişikliği · **Karar: Yasin'in** (üç soru, §2.3) ·
**commit `709b2ac`** · **girdi:** D-069 Bulgu 1, D-070/K1 · suite `410 passed`

### 1. LOCF gitti

`_pad_pe_list` diziyi **son gözlemle** bütçeye tamamlıyordu. D-069 bunun adını
koydu: **LOCF**, ve Lachin 2015 (`10.1177/1740774515602688`) doğrudan
eleştirisi — muhafazakâr değil, yanlılık iki yöne de olabilir, varyansı küçük
gösterir. D-068 pilotunda gen1'in **%71'i** pad'di.

⇒ `_clip_pe_trace` yalnızca bütçeye kırpıyor. **Yerine hiçbir şey konmadı**:
kısa yaşam kısa yaşamdır.

### 2. Karşılaştırılabilirlik sabit yaştan geliyor

| Okuma | Ne | Rol |
|---|---|---|
| `pe_before` / `pe_after` / `mean_pe` | yaşanan olay başına **oran** | ikincil |
| `pe_*_landmark` | ilk `LANDMARK_EVENT` olayın ortalaması | **birincil** |
| `pe_*_at_landmark` | 10. olayın tek değeri | yalnız kayıt |

**Neden nokta değil pencere (Yasin'in kararı):** drift bir **durum**, PE ise
olay başına **akış**. Tek olayın PE'si izin sunduğu en gürültülü şey — D-044
kolların olay bazında 0.065–0.194 ayrıştığını ölçmüştü. Pencerede her kol
**tam olarak aynı** 10 olayla katılıyor ⇒ ömür farkı bu sayıya giremez.

⚠ Kısa izde **kısmî pencere yok**, `NaN`. *"Ne kadarını becerdiyse onun
ortalaması"* sabit yaşın kaldırmak için var olduğu confound'u geri getirirdi.

⚠ **Nokta okuması kaydediliyor ama birincil değil**, ve hangisinin birincil
olduğu **ikisi de görülmeden** sabitlendi (L9).

### 3. `I3.1`'in paydası: bütçe → **yaşanan olay**

Bütçeye karşı ölçerken kapı **bozuk sensör** ile **kısa yaşam**ı ayırt
edemiyordu, ve D-066'dan beri kısa yaşam kural. 12 olay yaşayıp 12 satır yazan
ajan **sağlam**; 50 yaşayıp 12 yazan **bozuk**. Payda yoksa (D-073 öncesi
bölüm) kapı geçmiyor, *"değerlendirilemez"* diyor (§2.9).

### 4. `I3.4` bayrak olmaktan çıktı — yeni `MODE_REPORT`

⚠ **Kapı zaten `_pad_pe_list`'e hiç bakmıyordu** — her zaman
`bütçe − loga ulaşan satır` idi. Yani LOCF'u kaldırmak onu mekanik olarak
bozmadı; **anlamını** değiştirdi: artık uç noktadaki pad oranı değil, **erken
sonlanma oranı**.

`PAD_FRACTION_MAX = 0.0` olduğu için bayrak bırakılsaydı bundan sonraki **her
koşum** `flagged` olurdu ve `run_quality` bir şey ayırt etmeyi bırakırdı.
D-070/K7 çöküşün **bulgu olarak** raporlanmasına zaten karar vermişti.
⇒ Sayı JSON'a yazılmaya devam ediyor (ikinci ön-kayıtta **geçerlilik kriteri**
adayı), ama `MODE_REPORT` `run_quality`'ye ve `enforce`'a hiç dokunmuyor.

### Raporlama (§2.8)

`describe_pe_window` → **`pe_locf_padding: False`** + `pe_landmark_event`.
`pe_before`/`pe_after`/`mean_pe` **adlarını koruyor ama anlamları değişti**;
JSON'da bunu söyleyen tek şey bu bayrak.

Ayrıca `ArmResult.events_lived` → `events_lived_phase1` + `events_lived_phase2`
(PE denetimi iki fazı birleştiriyor, `I3.1` ikisinin toplamına bölüyor) ve
`Gen2Result`'a `events_lived` + iki landmark alanı.

### Dur-kontrol (⚠ keşifsel, mock LLM, N=1)

12 olaylık gerçek akışta bütün alanlar doldu, iz uzunluğu **12/12** (pad yok),
landmark penceresi ile nokta okuması **ayrı** değerler verdi.
⚠ **Sayıların kendisi okunmadı** — soru *"alan doluyor mu"*ydu (L9).

### Mutasyon kontrolü (§2.4)

| Mutasyon | Kıran test |
|---|---|
| LOCF geri geliyor | `test_short_pe_trace_is_not_padded_to_the_budget` + `test_whole_phase_mean_is_now_a_per_event_rate` |
| landmark penceresi kısmî ortalama alıyor | `test_landmark_window_refuses_a_partial_window` |
| `I3.1` paydası yine bütçe | `test_i3_1_does_not_call_a_short_life_a_starved_instrument` (+3) |
| `MODE_REPORT` `run_quality`'yi kirletiyor | `test_report_mode_records_without_touching_run_quality` |

⚠ **Bir test mutasyon altında kırılmadı ve düzeltildi.** `per_event_rate`
testi **sabit değerli** iz kullanıyordu; sabit bir izin ortalaması son
değerine eşit olduğu için LOCF hiçbir şeyi oynatmıyor ⇒ test, yasakladığı
padding'in altında **geçiyordu**. Almaşık desene çevrildi. §2.4'ün tarif
ettiği boş bekçinin ta kendisi.

### Sınırlar

- **Uç nokta hâlâ ön-kayıtlı değil.** Bu commit aleti hazırladı; hangi
  okumanın birincil olduğunu **ikinci ön-kayıt** yazacak.
- **Eski koşumlarla karşılaştırılamaz.** `dau_runs/`'daki her `pe_before` /
  `pe_after` / `mean_pe` LOCF çıktısı; yenilerinde `pe_locf_padding=False`
  var, eskilerinde alan **hiç yok**.
- **`run_protocol_c_prime.py`'nin kendi koşucusu da değişti** — aynı yardımcıyı
  paylaşıyorlar ve aletin iki yerde farklı davranması daha kötü olurdu.
- Değişmeyen: `MIN_TRACE_FRACTION = 0.5` ve `PAD_FRACTION_MAX = 0.0` **değer
  olarak** dokunulmadı (§2.7); değişen paydaları ve modları.

---

## D-074 · 2026-08-13 · Sıralama: **② popülasyon kilitten önce** — ve alet işinin muhasebesi

**Durum:** sıralama kararı · **Karar: Yasin'in** (D-007) · **kod değişmedi** ·
**tetikleyen:** Yasin'in sorusu — *"biz bir süredir optimizasyon yapıyoruz,
alete değil mi?"*

### Muhasebe — soru haklıydı

B2'den (tek gerçek koşum) bu yana:

| Ne | Kayıtlar |
|---|---|
| Alet / ölçüm / kapı | D-055…D-064, D-071…D-073 (~15) |
| **Evrenin fiziği** | **D-066** (metabolik döngü), D-067 (kasa saati) |
| Gerçek ölçüm | **B2** (13.1 sa) + D-068 pilotu (N=2, `flagged`) |

**Alet işinin savunması var ama tam değil.** B2 *alet null'ı* olarak sınıflandı
(D-053) ⇒ hipotez değil aletin kendisi test edilmişti. D-066 ömrü değişken
hâle getirdi, ve **değişken ömür sabit pencereli uç noktayı fiziksel olarak
bozar** ⇒ D-071/072/073 keyfi değil, D-066'nın mecbur bıraktığı işti. Onlar
olmadan koşum kolları **farklı yaşlarda** okuyup aradaki farkı kol etkisi diye
raporlardı.

⚠ **Savunma burada bitiyor.** D-068 kalan darboğazın **davranışsal** olduğunu
zaten ölçmüştü: D-066'dan *sonra* bile ajanlar olayların **%94–100'ünde**
DEFECT çekiyor, bedeli ödüyor, ölüyor ve **değişmiyor**. Bugünkü iş, düz
olduğu zaten ölçülmüş bir evreni daha hassas ölçen bir cetvel üretti.

### Karar

**② (popülasyon) kilitten önce gelir.** Ön-kayıt taslağı ② yerleştikten sonra
yazılır, koşum ondan sonra.

**Gerekçe:**
1. **Her fizik değişikliği kilidi geçersizleştirir.** Şimdi kilitleyip koşmak,
   ② sonrası **üçüncü** bir ön-kayıt demek.
2. **D-014'ün hedefi zaten N nesil**, gen1→gen2 en kısa koşulabilir biçim.
3. **D-065/J20 sıralamayı bağımsız olarak doğrulamıştı:** *önce bedel, sonra
   popülasyon*. Bedel D-066'da bitti ⇒ sıra ②'de.
4. **Farklı üreme olmadan seçilim iddiası kurulamaz** — ve tek başına ② de
   yetmez: N ajanın hepsi aynı baskın stratejiyi oynarsa fitness'ları yine
   özdeş olur (D-060'ın kökü).

### Reddedilenler

- **Şimdi kilitle ve koş.** *"Bedel var, adaptasyon yok"* temiz bir null olarak
  gerçek bir sonuç olurdu ve B2'nin alet null'ından farklıdır. Reddedilme
  sebebi sonucun değeri değil, **iki kilit maliyeti**.
- **Önce K7'yi yeniden aç.** Davranışsal önsel (J4/GovSim'in ölçtüğü tek
  kaldıraç) hâlâ aksiyom gerekçesiyle kapalı. ⚠ **Açık risk olarak kayda
  geçiyor:** davranış çökük kaldığı sürece hangi fizik eklenirse eklensin
  seçilim görünmeyebilir. K7 değişmedi; bu satır onu sorgulamıyor, **ilan
  edilmiş bir sınır** olarak duruyor ve ikinci ön-kayıta geçecek.

### ⚠ Pilot ön-kaydın zorunlu girdisi

**K3'ün N hesabı yeni aletten bir varyans tahmini istiyor** (D-052 B2 için tam
bunu yapmıştı) ve **elimizde yok**: D-068 pilotu D-071/072/073'ten önce, N=2 ve
kırık pencereyle koştu. ⇒ Pilot **② yerleştikten sonra** koşar; şimdi koşulan
varyans ölçülecek evrene ait olmaz.
⚠ Pilotta yalnız **dağılım** okunur; **kol farkı mühürlü kalır** (L9).

### Bugünkü alet işi ②'den etkilenmiyor

`LANDMARK_EVENT` yapısal çapası `METABOLIC_GRACE_EVENTS`'e bağlı, popülasyon
ona dokunmuyor; `F_agent`'ın oran terimi, LOCF'un kalkması ve `I3.1`/`I3.4`'ün
ayrılması popülasyondan bağımsız. ⇒ D-071…D-073 **② seçildiği için boşa
gitmedi**; hangi yol seçilse gerekliydi.

### Sıradaki iş

**② için read-only denetim + tasarım önerisi** (§2.3, kod yazılmadan).
Denetimin cevaplaması gerekenler: bugünkü orkestrasyonun tek-ajan
varsayımlarının **nerede** gömülü olduğu · üremenin biçimi (kim kopyalanır,
kaç varis, seçilim `F_agent`'tan mı) · ortak havuzun N ajanla nasıl
paylaşılacağı (`realized_extractions` zaten oransal bölüşüm yapıyor) ·
maliyet (N ajan × nesil × GPU).

---

## D-075 · 2026-08-13 · Popülasyon için yerel tarama: `null` çapamız bir **referans suş**muş

**Durum:** literatür taraması · **Etiket:** ⚠ **DR raporu değil** — Deep
Research bu turda da çalışmadı · **kod değişmedi** · mutabakat
`docs/research/RECONCILIATION.md` **§L**

### Neden burada

D-074 ②'yi (popülasyon) kilitten öne aldı ve brief #6 yazıldı. DR **dört
farklı cihaz ve ağdan** denendi; hepsinde *"size yardımcı olamıyorum, ben
sadece metin tabanlıyım"* dönüp kota **çıktısız** tükendi.

⚠ **Teşhis (kanıt değil, gözlem):** bu cümle Deep Research'ün değil, **düz
modelin** yetenek reddi. Muhtemelen DR modu devreye girmiyor, prompt düz
modele düşüyor. Not edilmeye değer bir yan etki: brief *"her iddia için DOI
ver, emin değilsen doğrulanamadı yaz"* dediği için model uyduramıyor ve
reddediyor. **Bu şart olmasaydı muhtemelen kaynak uydurup akıcı bir cevap
verirdi ve bozuk olduğunu fark etmezdik.**

**Yöntem:** D-069'un aynısı — dokuz kimlik Crossref/arXiv'den **açılarak**
doğrulandı. ⚠ İçerik yalnız açık erişimlilerde okundu; ikisinin bulgusu
alınamadı.

⚠ **Tarama yine kendi hatasını yakaladı:** V3'ün yazarını *"Vallinder &
Hubinger"* diye aradım, doğrulama **Hughes** olduğunu gösterdi. D-069'daki
Schoenfeld hatasının aynısı ⇒ doğrulama döngüsü **bize de** gerekiyor.

### ⭐ Ana bulgu — S3'ün cevabı var ve tasarımımızı doğrudan bağlıyor

**Xiao ve ark. 2023** (`10.1002/ece3.10713`, ölçülmüş): referans suşlu
rekabetçi uygunluk ölçümü, genotipler arasında **etkileşim olmaması**
varsayımına dayanır — ve bu varsayım ihlal edilince uygunluk **sıralaması**
ölçüm anına ve rakibin kimliğine göre **tersine dönebiliyor**.

⇒ **Bizim `null` kolumuz tam olarak bir referans suş.** Birincil karşıtlık
`‖lived−null‖` vs `‖shuffle−null‖`. Brief #6'nın (b) seçeneği — tek havuz,
karışık kollar — o varsayımı **tükenen bir ortak kaynak üzerinden yapı
gereği** ihlal eder: bir kolun aşırı hasadı, diğerinin ortamıdır.

⚠ Böcek popülasyonlarından bize taşınması **analoji**; ama ihlal edilen
varsayım aynı varsayım.

### İkinci bulgu — tekrar sayısı popülasyon boyutundan önemli

**Kofler & Schlötterer 2013** (`10.1093/molbev/mst221`, birebir alıntı):
*"replication of E&R is more important for detecting the targets of selection
than increasing the population size."* Bizim eşleştirmemiz: **tekrar =
tohum**, **popülasyon boyutu = N ajan** ⇒ yön: **daha çok tohum, daha küçük
popülasyon**. GPU bütçesiyle de uyumlu.

⚠ **Ölçek uyuşmuyor:** onların rejimi 60 nesil, yüzlerce-binlerce birey.
**Yön alınır, sayı alınmaz.**

### ⚠ Üçüncü bulgu — D-071 bir tasarım borcu yarattı

**Mills & Beatty 1979** (`10.1086/288865`): uygunluk **gerçekleşmiş** sonuçla
tanımlanırsa o sonucu açıklayamaz (*tautology problem*); yerleşik çözüm
**propensity** yorumu — bağımsız ölçülebilir özelliklerden **tahmin edilen**
üreme eğilimi.

D-071'den sonra `F_agent`'ın %30'u **gerçekten** hayatta kalma ölçüyor (önce
sabit 1.0'dı). Popülasyonda o skor **kimin üreyeceğini** belirlerse,
gerçekleşmiş hayatta kalma aynı anda **girdi + seçilim ölçütü + raporlanan
sonuç** olur. ⇒ Seçilim ölçütü ile raporlanan sonucun **ayrılması** gerekebilir.
**Ön-kayıt kararı, kod kararı değil** (D-007).

### Dördüncü bulgu — en yakın analog bizim kapattığımız kanalı kullanıyor

**Vallinder & Hughes 2024** (`arXiv:2412.10270`): LLM ajanları, nesiller boyu,
**kesme seçilimi** (üst %50). ⚠ Nesiller arası aktarılan şey **strateji
metni** — yani doğrudan **davranışsal önsel**, bizim aksiyomumuzun kapattığı
kanal.

⇒ **K7'nin bedelinin üçüncü bağımsız teyidi** (D-065/J4 ve D-068'den sonra).
İddia değil, ilan edilmiş sınır olarak ön-kayıta geçecek.

### Cevaplanamayanlar

**Kaç nesil = birikimli kalıtım** (Kirby ve ark. 2008 paradigmayı veriyor,
çıtayı değil; tasarım sayıları birincil kaynakta doğrulanamadı) ·
**Briesch ve ark. 2023'ün bulgusu** (403) · **bizim ölçeğimiz için
tekrar/popülasyon dengesi** · **ALife geleneğinin kendi yaklaşımı**.

### Sınırlar

**Sistematik derleme değil, hedefli tarama.** Kimlikler doğrulandı, **içerik
yalnız açık erişimlilerde okundu**. Bulunamamış bir alt literatür olabilir.
⇒ **Brief #6 geçerliliğini koruyor**; DR düzelirse aynen sorulur ve iki
bağımsız kaynak mutabakata bağlanır. **Hiçbir kod değişmedi, hiçbir sabit
seçilmedi, hiçbir tasarım kararı verilmedi.**

---

## D-076 · 2026-08-14 · DR #6 mutabakatı: **doğru kimlik, yanlış iddia** — yeni bir kusur türü

**Durum:** mutabakat · **kod değişmedi** · ham cevap
`docs/research/2026-08-14_DR6-answer-raw.md` · mutabakat
`RECONCILIATION.md` **§M**

### DR nihayet çalıştı

Beş denemeden sonra brief #6 cevaplandı. ⚠ **D-075 geçersizleşmiyor** — yerel
tarama bağımsız bir kaynak olarak duruyor ve iki yerde DR ile **aynı sonuca**
varmış olması (ayrı havuz) delil değeri taşıyor.

### ⚠ Yeni kusur türü: kaynak gerçek, iddia ona ait değil

Önceki dört turda kusur *"kaynak yok / kimlik yanlış"*tı. Bu turda kaynaklar
**gerçek**, ama üç iddia **o kaynakta olmayan** şeyler söylüyor:

| İddia | Yüklendiği kaynak | Kaynak gerçekte ne |
|---|---|---|
| *"tespit gücü N'ye üstel duyarlı"* (S6) | Goldberg & Deb 1991 | devralma süresi / seçilim baskısı analizi — deney tasarımı güç analizi **değil** |
| *"nötr ebeveyn seçim kontrolü"* (S2) | Branke & Schmidt 2003 | *Selection in the Presence of Noise* — gürültülü uygunluk, sürüklenme kontrolü değil |
| *"olay bütçesi 30'un altına inmemeli"* (S6) | Elena & Lenski 2003 | mikrobiyal evrim derlemesi; bizim olay bütçemiz hakkında hiçbir şey söyleyemez |

⇒ **DOI doğrulaması bu kusuru YAKALAMIYOR.** Kimlik kontrolü artık yetmez;
iddianın kaynağın **konusu** olup olmadığı da bakılmalı. Bu, kaynak disiplinine
eklenen yeni bir adımdır.

**Bir kırık DOI:** Bedau, Snyder & Packard 1998 → `10.1162/artl.1998.4.4.431`
**404**. ⚠ Kavram (evrimsel aktivite istatistikleri) gerçek — Bullock & Bedau
2006 (`10.1162/artl.2006.12.2.193`) doğrulandı — **atıf** kırık.

**Beş kimlik doğrulandı ve konuya uygun:** Goldberg & Deb 1991 · Bäck 1994
(⚠ *"ölçülmüş deney"* diye etiketlenmiş, teorik) · Chevin 2011
(`10.1098/rsbl.2010.0580`) · Hudgens & Halloran 2008
(`10.1198/016214508000000292`) · Price 1970 (`10.1038/227520a0`).
Beş kaynak **doğrulanmadı** (Crossref 429).

### ⚠ On üç iddianın on üçü *"Tam Uyumlu"*

Brief açıkça *"kısıt ihlal ediliyorsa işaretle"* demişti; **sıfır işaret**
geldi. En az ikisi kısıtlara dokunuyor: iki aşamalı doygunluk tasarımı kolların
**ne olduğunu** değiştirir, ve Price eşitliği `w` = varis sayısı istiyor —
bugün her ebeveynin **tam olarak bir** varisi var ⇒ `w` sabit, kovaryans
**tanımsız**.

### ⭐ İçsel çelişki — ②'nin amacını vuruyor

**§5:** birikimli seçilim izleri **G = 5–10**'da belirir; G=2 yalnız anlık
aktarım gösterir. **§6 sentezi:** bütçe **G = 3**'e kaydırılsın.

⇒ Rapor **kendi çıtasının altını** öneriyor ve bunu fark etmiyor. ②'nin bütün
gerekçesi birikimli kalıtım iddiasıydı (D-014, D-074).

### ⭐ Gerçekten değerli: Price eşitliği D-075'in borcunu ödüyor

D-075, `F_agent`'ın hem seçilim ölçütü hem sonuç olmasının **tautology
problem**'e girdiğini yazmıştı. Price (1970) yerleşik cevabı veriyor:

`Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)`

Uygunluk `w` **seçilimi sürükler**, sabit yaşta okunan drift vektörü `z`
**sonuç ölçütü** olarak kalır ⇒ döngü kırılır. **K5 kararımız (landmark drift)
tam olarak `z` rolüne oturuyor** — yani D-070/D-072'de verdiğimiz karar,
bağımsız bir gerekçeyle desteklenmiş oldu.

⚠ **Ön koşulu var:** `w` değişken olmalı. Bugün sabit.

### ⭐ İki bağımsız kaynak aynı yerde: **ayrı havuz**

DR (Hudgens & Halloran 2008: SUTVA ihlali / kısmi girişim) ve D-075 (Xiao vd.
2023: referans suş varsayımı) **farklı literatürlerden** aynı sonuca varıyor:
kol başına ayrı havuz. ⚠ Bedeli de ilan edilmiş (Chevin 2011): izolasyon,
seçilim iddiasını birey düzeyinden **grup düzeyine** kaydırır.

### Sınırlar

**Hiçbir tasarım kararı verilmedi, hiçbir sabit seçilmedi, kod değişmedi.**
Beş kimlik doğrulanmadı. `N=16, G=3, 35 olay` önerisi **alınmadı**: dayanağı
yanlış atıf (M.1), kendi §5'iyle çelişiyor (M.3), ve sayı seçimi §2.7 gereği
ölçümle gerekçelendirilmeli.

---

## D-077 · 2026-08-14 · ⛔ Popülasyonun önündeki asıl engel: iki ajan bugün **ayrışamıyor**

**Durum:** kod denetimi (bulgu) · **kod değişmedi** · **karar bekliyor** ·
tasarım önerisi `docs/POPULATION_DESIGN_PROPOSAL.md` **§2.5**

### Bulgu

`POPULATION_DESIGN_PROPOSAL.md`'nin ilk sürümü popülasyonu *"N ajan"* diye ele
aldı ve ajanların birbirinden **farklı olacağını varsaydı**. Kod bunu
desteklemiyor. Üç yer birlikte:

| Doğrulanan | Nerede |
|---|---|
| `_seed_niche(seed)` — **`agent_id` parametresi yok** ⇒ aynı tohumdaki her ajan **aynı nişte** doğar | `run_protocol_c_prime.py:662` |
| Çözümleme **greedy** (`LLM_DO_SAMPLE_DEFAULT = "0"`); D-037 determinizmi I0.6 ile **zorunlu** | `local_llm.py:64` |
| `realized_extractions` — **eşit talep, eşit pay** | `environment.py:88` |

⇒ **Aynı nişte doğan N ajan, aynı bedenle, aynı kararı verip aynı payı alır ve
yaşam boyunca bit düzeyinde özdeş kalır.**

### Neden bu, projenin en önemli engeli

Popülasyon bugünkü kodun üstüne kurulursa N tane **aynı** ajan olur:
`F_agent`'lar özdeş ⇒ turnuva yazı-tura ⇒ **`Cov(w, z) = 0` yapı gereği**.
Ve bu sıfır, D-076'nın Price eşitliğiyle kurduğumuz bütün seçilim iddiasının
tam olarak ölçtüğü şey.

⚠ **D-060'ın tekrarı değil, daha kötüsü.** D-060'ta 120 kol aynı sınıfa
düşüyordu çünkü **evren ayrım üretmiyordu**; burada ajanlar ayrışamıyor çünkü
**aynı ajanlar**. Birincisi bir bulgu, ikincisi bir ölçüm hatası olurdu.

⚠ **§5'in geçerlilik kapısından da farklı:** orada risk *"davranış çökük
olabilir, seçilim görünmeyebilir"*di. Burada **ölçüm kurulamıyor**.

### ⇒ Yeni karar noktası: P0 — heterojenlik evrene nereden girer

| Seçenek | Değerlendirme |
|---|---|
| **(d) Sıralı erişim** — ajanlar olay içinde sırayla hasat eder; havuz tükenirken sıradaki daha azını bulur | ⭐ **Claude Code'un önerisi.** Farkı **evrenin kendisi** üretiyor (tükenen kaynak için çekişme), atanan bir etiket değil ⇒ **aksiyoma uygun**. Deterministik kalır ⇒ **D-037 korunur** |
| (a) Ajan başına ayrı niş | Ajanlar farklı **ortamlarda** olur; "ortak havuz" iddiası zayıflar |
| (b) Örneklemeli çözümleme | ⛔ **D-037'yi ve I0.6'yı kırar** — tekrarlanabilirlik ön-kaydın önündeki en büyük engeldi (D-037: gürültü etkiden büyüktü) ve çözülmüştü |
| (c) Asimetrik doğum koşulları | ⚠ Aksiyoma yakın: "trait" olmasa da **atanmış** bir fark |

⚠ **P0 çözülmeden P1–P7 anlamsızdır.**

### Sınırlar

**Kod okumasıyla bulundu, ölçümle değil.** Doğrulanması ucuz ve P0 kararından
sonra yapılacak: aynı tohumda iki ajan koşulur, `arm_digest`'leri
karşılaştırılır. ⚠ Bugün beklenen sonuç **birebir aynı**; farklıysa bu kayıt
yanlıştır ve düzeltilir.

---

## D-078 · 2026-08-14 · D-077 **ölçüldü**: iki ajan gerçekten özdeş · E3 uygulandı

**Durum:** ölçüm + kod değişikliği · **Etiket:** ⚠ **keşifsel, ön-kayıtlı
değil** · ölçüm 93 sn · **commit `32c1a8b`** · suite `414 passed`

### 1. D-077 doğrulandı — iddia değil, ölçüm

D-077 **kod okumasından** çıkmıştı ve *"doğrulaması ucuz, sonra yapılacak"*
diye kaydedilmişti. Yapıldı.

**Kurulum:** tohum **7801** (deneyde kullanılmamış), `null` kolu (eğitim yok),
LoRA **kapalı** ⇒ diske adapter yazmadı. İki ajan (`agentA`, `agentB`), aynı
tohum, 12 olay, **gerçek yerel Llama** (mock değil).

**Sonuç: ölçülen dokuz niceliğin dokuzu da birebir aynı.**

| Ne | Sonuç |
|---|---|
| `arm_digest` (= sha256(karar dizisi ++ PE dizisi), iki faz) | **AYNI** |
| `pe_before_list` · `pe_after_list` | **AYNI** |
| `events_lived_phase1/2` | **AYNI** |
| `landmark_energy` · `landmark_drift_magnitudes` · `energy_mean_over_life` | **AYNI** |
| `phase2_decision_hashes` | **AYNI** |

⇒ **D-077 doğrulandı.** Aynı nişte doğan iki ajan, yaşam boyunca ayrışmıyor.
`arm_digest`'in aynı çıkması özellikle güçlü: o, iki fazın **bütün** karar ve
PE dizisinin özeti — tek bir olayda bile ayrışsalar farklı çıkardı.

⚠ **P0 hâlâ açık ve Yasin'in.** Bu ölçüm P0'ı **gerekli** kıldı, çözmedi.

### 2. E3 uygulandı — karara bağlı olmayan tek iş

Popülasyon engellerinden **en sinsisi**. Diğerleri (ortak havuz, çok-ajanlı
döngü, üreme katmanı) kodu **çalıştırmaz**; bu **çalıştırır ve yanlış sayı
üretir**: N ajan aynı anda yaşarsa üç olay tamponunda her ordinal için N satır
olur ve *"`event_counter == 10` olan satır"* arayan okuyucu bunlardan birini
alır — gerçek bir sayı, **yanlış ajanın** sayısı, hata yok uyarı yok.

**Ne değişti:** üç kayıt fonksiyonu `agent_id` alıyor ve satıra yazıyor
(`EVENT_ROW_AGENT_ID`) · `graph.rows_for_agent()` yardımcısı ·
`_landmark_reading`, `_s5_behaviour` ve `run_life_keep_vault`'un PE izi
filtreliyor.

⚠ **Filtre `get_*_event_log()` içine konmadı, bilerek:** paylaşılan bir
tamponu **kimin** satırlarını istediğini söylemeden okumak, çağıranın kazara
yapabileceği bir şey olmamalı (§2.9). Filtreleme çağrı yerinde görünür.

**Tek ajanlı yolda davranış birebir aynı** — tampon zaten yaşam başına
sıfırlanıyor, yani filtre bugün her satırı geçiriyor.

⚠ **Testler karışık tamponda kanıtlıyor:** iki ajanın satırları birbirine
geçmiş hâlde, çünkü peş peşe eklenmiş satırlarda ilk eşleşmeyi alan bir
okuyucu **öne gelen ajan için doğru görünür**.

**Mutasyon kontrolü (§2.4), üçü de kırdı:** landmark filtresi kalkıyor ·
S5 filtresi kalkıyor · satırlar `agent_id` taşımıyor.

⚠ **Mevcut bir test filtrenin çalıştığını kendiliğinden gösterdi:** gen2
commons testinin sahte yaşamı başka bir ajanın satırlarını yazıyordu ve
okuyucu onları **doğru şekilde reddetti**. Fikstür düzeltildi.

### Sınırlar

- Ölçüm **N=2, tek tohum, 12 olay**. Genelleme değil; ama iddia da genel
  değildi (*"ayrışma mekanizması yok"*) ve tek karşı örnek onu çürütürdü.
- **Tohum 7801 artık kullanılmış sayılır** — adapter yazmadı, yani I0.7'yi
  tetiklemez, ama deneyde kullanılmamalı.
- E3 popülasyonu **kurmuyor**; onun sessiz kusurunu önceden kapatıyor.
- **P0–P7'nin hiçbiri karara bağlanmadı.**

---

## D-079 · 2026-08-14 · P0 için yerel tarama: sıralı erişim **fizik kararı**ymış, ve konum etkisi ölçülmüş

**Durum:** literatür taraması · **Etiket:** ⚠ **DR raporu değil** · **kod
değişmedi** · mutabakat `RECONCILIATION.md` **§N** · dört kimlik doğrulandı

### Neden burada

Brief #7 gönderilemedi: Gemini *"ben bir dil modeliyim, bu beceriye sahip
değilim"* deyip kotayı **çıktısız** tüketti. D-069/D-075'in yöntemi üçüncü kez
uygulandı.

⚠ **Bu turda yeni bir işaret kullanıldı:** bir iddianın kaynağın **neresinde**
geçtiğini gösteremediysem **kullanılmıyor**, yalnız not ediliyor. D-076'nın
*"doğru kimlik, yanlış iddia"* kusuruna karşı eklenen adım — ve bu turda
**iki kez işe yaradı** (§N.2'deki iki iddia bu yüzden alınmadı).

### ⭐ Bulgu 1 — konum etkisi ölçülmüş, ve **önerimi olduğu gibi bırakmıyor**

**Suleiman, Rapoport & Budescu 1996** (`10.1016/0001-6918(96)00008-x`, Acta
Psychologica 93:229–245): sıralı kaynak ikilemlerinde **konum etkisi** var —
talep ile sıradaki konum ters orantılı. Konumun **nasıl dağıtıldığı** etkiyi
değiştiriyor: rastgele dağıtım etkiyi azaltıyor, hak edilmiş dağıtım
**dönen konumlardakiyle aynı** etkiyi veriyor.

⚠ **D-077/P0'da *"sıra dönsün"* demiştim; W3'e göre dönen konumlarda da etki
görülüyor.** Yani rotasyon konum etkisini **yok etmiyor**.

⚠ **Şu benim çıkarımım, kaynağın bulgusu değil:** dönen sırada her ajan her
konumu işgal ettiği için **birikimli** maruziyet eşitlenir; geriye kalan,
durumun (enerji, drift, anı) doğrusal olmayan biriktiği için oluşan yörünge
ayrışmasıdır — **aradığımız simetri kırılması tam olarak bu**. ⇒ Konum etkisi
bizde bir kusur değil, **mekanizmanın kendisi** olabilir; kusur olan onun
**kalıcı** hâle gelmesi.

⚠ İkisi de **insan deneyi**; LLM ajanına taşınması analoji. Üstelik W3'ün
mekanizması *"hak edilmişlik algısı"* — ajanlarımızda karşılığı bilinmiyor.

### ⭐ Bulgu 2 — güncelleme sırası **birinci sınıf bir modelleme kararı**

**Schönfisch & de Roos 1999** (`10.1016/s0303-2647(99)00025-8`) ve **Fatès
2014** (`arXiv:1406.0792`): eşzamanlı ve eşzamansız güncelleme **temelde
farklı** dinamikler üretiyor; eşzamansız güncelleme kendi başına bir
literatür.

⇒ **Önerimin çerçevesi düzeliyor.** Sıralı erişimi *"aksiyoma uygun, hafif bir
mekanizma"* diye sunmuştum. Değil: **fizik kararıdır** ve ön-kayıtta öyle ilan
edilmeli — tıpkı metabolik döngü (D-066) gibi.

### Bulgu 3 — birikimli kalıtım çıtası: **ikinci kez sayı çıkmadı**

DR #6 ve bu tarama, **bağımsız olarak**, kaç neslin *"birikimli kalıtım"*
demeye yettiğine dair yerleşik bir çıta bulamadı. ⇒ Bunu artık bir **bulgu**
saymak makul: **yerleşik çıta yok**, ve G bizim kendi gerekçemizle seçilip
ön-kayıtta **ilan edilmiş bir seçim** olarak yazılmalı — literatürden
türetilmiş gibi değil.

### Cevapsızlar

**Uzamsal gömme** (ALife'ın muhtemel standart cevabı) doğrulanmış kaynağa
bağlanamadı · **üç eksenli (tekrar/N/nesil) denge** bizim ölçeğimiz için sayı
vermiyor.

### ⚠ #6 cevaplandı, #7 reddedildi — kontrollü fark

Aynı hesap, aynı düz metin, aynı uzunluk mertebesi. İki fark: #7 ek olarak
**iddianın kaynağın neresinde geçtiğini** istiyor, ve sicil bölümü daha uzun
ve daha sert.

⚠ **Hipotez, kanıt değil:** #7'nin doğrulama şartı tarayıcısız bir modelin
karşılayamayacağı bir şart ve dürüst cevabı *"yapamam"* oluyor. **Sınanabilir**
— sicil bölümü ve *"neresinde"* şartı çıkarılıp gönderilir.

### Sınırlar

**Sistematik derleme değil, hedefli tarama.** Dört kimlik doğrulandı, **içerik
yalnız açık erişimlilerde** okundu. İki iddia *"kaynakta yerini
gösteremedim"* diye **alınmadı**. **Hiçbir karar verilmedi, hiçbir kod
değişmedi.** P0 **hâlâ Yasin'in** ve tarama onu kapatmadı — çerçevesini
değiştirdi.

---

## D-080 · 2026-08-14 · DR #7 mutabakatı: *"neresinde geçiyor"* şartı **işe yaradı** — altı iddianın üçü kendi alıntısını taşımıyor

**Durum:** literatür mutabakatı · **Etiket:** **kod değişmedi** · ham cevap
`docs/research/2026-08-14_DR7-answer-raw.md` · mutabakat
`RECONCILIATION.md` **§O** · altı kimlik açıldı · karşılaştırma **§N (D-079)**

### Neden burada

Brief #7 (`2026-08-14_heterogeneity-among-identical-agents_PLAIN.txt`)
cevaplandı. §9/D-006 süreci koştu. ⚠ D-076'nın yakaladığı *"doğru kimlik,
yanlış iddia"* kusuru için bu turda **ek şart** vardı: iddianın kaynağın
**neresinde** geçtiği. Bu kayıt o şartın **ne yaptığını** ölçüyor.

### ⭐ Bulgu 1 — şart hataları engellemedi, **yakalanabilir** yaptı

**Yerini gösterebildiğim iddia: 6'nın 4'ü.** (#6'da 13 satırın hepsi *"Tam
Uyumlu"* çıkmıştı, ayırt etme **sıfır**.)

⭐ Asıl kazanç: ilk kez iddiayı **kendi alıntısının yanına koyup**
karşılaştırabildim. Sonuç: **altı iddianın üçü, kendi alıntısının söylemediği
bir şey söylüyor.** ⚠ **Yalnız DOI doğrulamasıyla (D-076 öncesi rejim) üçü de
geçerdi.** ⇒ şart kalıcı hâle getirilir.

### ⭐ Bulgu 2 — iddia 2: alıntılar gerçek, **iki ters bulgu birleştirilmiş**

DR *"Nishimura ve ark. (2024), arXiv:2308.00179"* dedi. Açtım: **Anwar &
Georgalos**, *Position Uncertainty in a Sequential Public Goods Game*, Exp.
Econ. 27:820–853, `10.1007/s10683-024-09831-3`. **Yazar uydurma, numara
doğru** ⇒ **sekizinci kimlik hatası**, tamir edilebilir.

PDF'i okudum, **iki alıntı da birebir var**. ⚠ Ama DR'nin cümlesi
(*"birinci hamle eden davranışından bağımsız avantaj kazanır — daha çok katkı
verir ya da daha çok hasat eder"*) üç yerden kusurlu:

1. *"first-mover advantage"* makalede **Varian (1994)**'e ait, **kuramsal**,
   ve orada avantaj **daha AZ katkı vererek** kullanılıyor.
2. *"first movers contributing more"* **leading-by-example** yazınının
   **ampirik** bulgusu, **doğrusal kamu malı** oyunlarında — katkı
   **maliyetlidir, avantaj değildir**. İki bulgu **ters yönde**.
3. *"ya da daha çok hasat eder"* kaynakta **hiç geçmiyor** — bizim
   kurulumumuza uydurmak için eklenmiş köprü.

⇒ **Alınan:** sıralı protokollerde sıra etkileri belgelenmiştir.
⇒ **Alınmayan:** birinci hamle eden davranıştan bağımsız avantajlıdır.
⚠ **P0'da ①'i zayıflatacak gibi görünen tek yeni iddia buydu ve kaynağında
yoktu.**

⭐ **İki bağımsız yol aynı yere çıktı** (D-065/J20 deseni): o alıntının atıf
listesi **Suleiman ve ark. 1996**'yı içeriyor = §N'in **W3**'ü; ve DR'nin
üçüncü kaynağı **Bru ve ark. 2003** = §N'in **W4**'ü.

### Bulgu 3 — iddia 3 ve 5: alıntı doğru olsa bile iddiayı taşımıyor

**Bru 2003:** alıntı *"order of the **treatments** … in each **session**"* =
**koşulların sunuluş sırası** (dengeleme), iddia ise **ajan sırasını
döndürmek**. Farklı şeyler ⇒ **brief yanılmış**, alınmıyor. (Makale ödemeli,
alıntıyı doğrulayamadım — ama gerek yok, alıntının kendisi iddiayı taşımıyor.)

**Lee 2015:** alıntı **birebir doğru** (JASSS 18(4):4 §1.3, açıp buldum). ⚠
Uyarlaması yanlış: *"tekrarlanabilirlik kısıtınız tohum değiştirmenizi
engelliyor"*. **Engellemiyor** — I0.6/D-037 *"aynı tohum + aynı kod aynı
sonuç"* diyor; B2 **40 farklı tohumla** koşuldu. ⇒ **brief yanılmış**, ama
⚠ **kısmen bizim tarifimizden**: §1.1'de büyük harfle *"TEKRARLANABILIRLIK
ZORUNLU"* deyip tek tohumlu örnek vermiştik. **§9'un dersi dördüncü kez.**

### Bulgu 4 — iddia 4: sayı doğrulandı, **ölçtüğü şey başka**

DR `arXiv:0810.3070` dedi; açtım: **Barczy & Pap, *alpha-Wiener bridges***,
Stochastic Analysis and Applications 28:447–466 — **konuyla ilgisi yok** ⇒
**dokuzuncu kimlik hatası**. Doğru makaleyi buldum: **Rafferty, Griffiths &
Klein (2014)**, *Analyzing the Rate at Which Languages Lose the Influence of a
Common Ancestor*, Cognitive Science 38(7):1406–1431, `10.1111/cogs.12112`.
Özette **birebir**: *"…convergence in a number of generations that is on the
order of n log n"*.

⚠ **Ama makale *birikimli etki oluşması* süresini değil, *ortak atanın
etkisinin kaybolması* süresini ölçüyor** — başlığın kendisi bunu söylüyor.

⇒ ⚠ **Şu benim çıkarımım, makalenin ifadesi değil:** n log n, atadan gelen
izin **ne kadar süre hâlâ görülebilir** olduğunun ölçeği ⇒ küçük G, ata izini
**aramak** için elverişsiz değil.

⇒ **§N Bulgu 3 güncellendi:** *"yerleşik çıta yok"* **hâlâ geçerli** (üçüncü
bağımsız denemede de sayı gelmedi); yeni olan, çıta yerine bir **ölçek** ve
*"küçük bir sabit değil"* ifadesi. **G kendi gerekçemizle seçilip ön-kayıtta
ilan edilecek** kararı **değişmedi**.

### Bulgu 5 — uzamsal gömme: §N.4'ün cevapsızı doldu, **ama ②'nin yanına**

Schelling (1971) — DR *"DOI yok"* dedi, **var**:
`10.1080/0022250X.1971.9989794`. ⚠ Yeri yalnız **ikincil** metinlerde
gösterildi ve biri (`[56]`) **hiçbir makaleye bağlanamadı** (kaynakça
verilmedi) ⇒ **kaynağıyla kullanılmıyor**.

⚠ **Ama asıl mesele kimlikte değil, uygulanabilirlikte:** Schelling'de farkı
yaratan **başlangıçtaki rastgele yerleşim** ⇒ **fark yaşamaktan önce geliyor**
— bizim P0 tablomuzda ②/③'ün konumu. Ve DR'nin *"hiçbir kısıt ihlal
edilmiyor"* değerlendirmesi **eksik**: ızgara boyutu, komşuluk yarıçapı,
kaynağın uzamsal dağılımı = **en az üç yeni sabit**; ①'in ilan edilmiş
üstünlüğü **sıfır yeni sabit**tı. ⇒ P0 tablosuna **⑤** olarak eklendi.

### ⚠ §N.3'ün hipotezi düştü

§N.3'te *"#7'nin 'neresinde' şartı tarayıcısız bir modelin karşılayamayacağı
bir şart"* diye yazmış ve cevapsızlığı buna bağlamıştım. **Cevap geldi ve
şartı karşılamaya çalıştı** ⇒ hipotez **desteklenmedi**. Cevabı hangi
aracın ürettiği bilinmiyor.

### Süreç — brief #8 için iki düzeltme

1. **Kaynakça istenecek.** İç indeks numaraları (`[56]` vb.) verildi, kaynakça
   verilmedi ⇒ bir iddia bu yüzden düştü.
2. **Satır numarası yerine birebir alıntı.** DR *"lines 249–253"* dedi, aynı
   cümle benim çıkarımımda **313. satırdaydı**; bulmayı sağlayan **alıntıydı**.

### Sınırlar

**Hiçbir karar verilmedi, hiçbir kod değişmedi.** İki kaynak (Bru 2003,
Gilbert 2002) **açılamadı** — biri ödemeli, biri konferans bildirisi.
Schelling 1971'in kendisini de açamadım; kimliği doğrulandı, **iddianın yeri
birincil kaynakta gösterilmedi**. **P0 hâlâ Yasin'in** ve DR #7 onu
kapatmadı — ①'i **zayıflatmadı**, tabloya **⑤**'i ekledi.

---

## D-081 · 2026-08-14 · Havuzun aritmetiği: **kademeli kıtlık diye bir şey yok**, ve landmark önerimi geri çekiliyor

**Durum:** ölçüm (saf aritmetik, mevcut sabitler) · **Etiket:** ⚠ **keşifsel,
ön-kayıtlı değil** · **kod değişmedi, sabit değişmedi, koşum yapılmadı** ·
tetikleyen soru Yasin'den

### Neden burada

Yasin sordu: *"P0'ı sonradan değiştirmek çileli olur mu; ajanlar geç tepki
veriyorsa tepki verecekleri aralıktan başlatsak runlar boşa gitmez mi?"*
Sorunun ilk yarısı koda bakmayı, ikinci yarısı havuzun yörüngesini
hesaplamayı gerektirdi. §2.6 gereği ölçüm kaydediliyor — **sonucu önerimi
çürüttü.**

### Bulgu 1 — `CLAUDE.md`'deki hesap yanlıştı

Belge *"havuz 80 → yenilenmeyle ~89"* diyordu. Lojistik yenilenme 80'de
**+2.40** veriyor (`0.15·80·(1−0.8)`), stok **82.40**. Olay 1'in sonucu
değişmiyor (64 < 82.40) ama yörünge ileri taşınmamıştı: olay 1'den sonra
havuz **18.40**'a düşüyor.

⚠ Ve belgenin çıkarımı (*"ilk olaylarda herkes tam alır, ayrışma geç
başlar"*) **N=8 için terstir**. Bugünkü kodda havuz N ile ölçeklenmiyor
(`POOL_MAX=100` sabit):

| N | kıtlığın başladığı olay |
|---|---|
| 1 | 17 |
| 2 | 7 |
| 4 | 3 |
| **8** | **2** |

⇒ Landmark'a (10) gelindiğinde havuz **sekiz olaydır sıfır**, herkes sıfır
alıyor, ajanlar ölçüm anında **yine özdeş**. Riskin yönü belgede yazdığının
tersiymiş.

### ⭐ Bulgu 2 — bu bir ayar sorunu değil, **cebirsel bir sonuç**

Kişi başı azami yenilenme, lojistik eğrinin tepesinde
`r·K/4 = 0.0375·K` = kapasite 100'de **3.75/olay**. DEFECT'in talebi
**8.0/olay**, ve olayların **%94–100'ü DEFECT** (D-068).

⇒ **Yenilenme bedavacılığa hiçbir başlangıç stoğunda yetişemez.** Havuz
tekdüze düşer ve *"herkese yeter"* ile *"ölü"* arasında **tek adımda** geçer.

⚠ **Sonuç:** bir yaşamda **tam olarak bir tane** kısmen karşılanan olay
vardır — başlangıç stoğu ne olursa olsun. Yani **kıtlık bandı yok, kıtlık
anı var.** Başlangıç stoğu bir çalışma noktası değil, yalnız bir **geri
sayım sayacı**dır: hangi olayda öleceğini belirler, biçimini değiştirmez.

⚠ Bu **①'e özgü değil**: ②/③ de havuza dokunmuyor. Havuzun çalışma kuralı
hangi P0 seçilirse seçilsin ilan edilmek zorunda.

### Bulgu 3 — kişi başı ölçekleme N'den bağımsız, **birebir**

Havuz kapasitesi ve başlangıcı N ile ölçeklenirse (kişi başı 100 / 80 —
*bugünkü sayılar*), lojistik denklem doğrusal ölçeklendiği için kişi başı
yörünge **N=1 evreninin aynısı** oluyor: N = 1, 4, 8, 16 için kıtlık anı
**hepsinde olay 17**. **Sıfır yeni sabit** girer.

### ⛔ Bulgu 4 — **kendi önerimi geri çekiyorum**

Yasin'e *"landmark yapısal tanımlansın: kıtlığın başladığı olay"* önermiştim
ve onayını almıştım. **Uygulamaya geçerken çöktü.**

`LANDMARK_EVENT = 10` keyfi bir sayı değil. `constraints.py:64–77` onu
`METABOLIC_GRACE_EVENTS = 10`'a bağlıyor ve gerekçesini yazıyor: grace
doğum geçicisini örtüyor, **ölüm landmark'ta hâlâ askıda**
(`should_continue` yalnız `len(event_log) >= GRACE` olunca yaşamı
bitiriyor) ⇒ **her soy landmark'a ulaşıyor, sansür yok.**

⇒ Landmark'ı kıtlık anına (17) taşımak onu grace'in **dışına** çıkarır:
11–16 arasında ölen soyların **okuması olmaz**. Bu, tam da K1–K3'ün (D-070)
ve DR brief #5'in konusu olan **bilgilendirici sansürlemeyi** geri getirir.

⚠ **§2.2'nin dersi bir kez daha:** öneriyi belge düzeyindeki resimden
kurdum, sabitin kendi yorumunu okumadan. *"Hafızaya ve belgeye değil,
dosyaya güven."*

### Bulgu 5 — geriye kalan tek kaldıraç ve sınırı

Landmark 10'da kalmak zorundaysa ve kıtlık anı ondan **önce** düşmeliyse,
oynayabilecek tek şey kişi başı kapasite:

| kişi başı kapasite | kıtlık anı |
|---|---|
| 40 | 5 |
| 50 | 7 |
| 60 | 8 |
| **67** | **9** ⭐ en büyük değer |
| 70 | 10 |
| 100 (bugünkü) | 17 |

⭐ **Kıtlık anını landmark'tan önce düşüren en büyük kapasite = 67**
(başlangıç 54, kıtlık olay 9'da). O yapılandırmada: olay 1–8 herkes tam alır
ve **özdeştir**; olay 9 **tek ayrışma olayıdır** ve sırayı kim aldıysa payı
o alır; olay 10'da havuz ölüdür ama **enerjiler artık farklıdır** ve
landmark tam orayı okur; ölüm hâlâ askıda olduğu için **her soy oraya
ulaşır**.

⚠ **Ama bu bir sabit seçimidir ve §2.7'nin sınırındadır.** Savunulabilir
biçimi: değer **etkiye bakılarak** değil, **yalnız sabitlerden türetilen bir
eşitsizlikle** seçilir (*"kıtlık anı < LANDMARK_EVENT olsun, ve bunu
sağlayan en büyük kapasite alınsın"*) — hiçbir pilot verisi girmez, tıpkı
`LANDMARK_EVENT`'in `GRACE`'e bağlanması gibi. ⚠ Yine de **bu bir karardır
ve Yasin'indir** (D-007); Claude Code tek başına almaz.

### Ne karara bağlandı, ne bağlanmadı

| | Durum |
|---|---|
| **Havuz N ile ölçeklensin, kişi başı sayılar bugünkü değerinde** | ✅ Yasin onayladı, **ayakta** — sıfır yeni sabit |
| **Landmark yapısal tanımlansın (= kıtlık anı)** | ⛔ **Claude Code geri çekti** (Bulgu 4). `LANDMARK_EVENT = 10` **kalıyor** |
| Kişi başı kapasite değeri | ⏳ **açık, Yasin'in** — Bulgu 5 |
| P0 = ① | ⏳ ⚠ Yasin *"önerdiğin olsun"* dedi; bunu ①'i de kapsıyor diye okuyorum ama **açıkça teyit edilmedi** — yanlışsa D-082 düzeltir |

### Sınırlar

**Saf aritmetik.** Model koşulmadı, ajan yaşamadı, adapter yazılmadı.
Hesap üç varsayıma dayanıyor: (i) her ajan her olayda DEFECT ediyor (D-068:
%94–100), (ii) `EXTRACTION_DEFECT = 8.0` sabit, (iii) havuzdan başka enerji
kaynağı yok. Gerçek koşumda davranış karışırsa talep düşer ve kıtlık anı
**gecikir** — yani yukarıdaki tablo **en erken** durumu verir. ⚠ Ölüm
modelinin (`should_continue` + grace) etkisi hesaba **katılmadı**;
landmark'tan sonra ömürlerin ne olacağı **ölçülmedi**.

---

## D-082 · 2026-08-14 · DR #8: D-081 **doğrulandı ve adlandırıldı**; DR'nin iki çıkışı da mekanizmayı öldürüyor, üçüncüsü çalışıyor

**Durum:** literatür mutabakatı + keşifsel hesap · **Etiket:** **kod
değişmedi** · ham `docs/research/2026-08-14_DR8-answer-raw.md` · mutabakat
`RECONCILIATION.md` **§P** · on bir kimlik açıldı

### ⭐ Bulgu 1 — türetmemizin literatürde adı var

**Azar, Lindgren & Holmberg 1996** (`10.1007/BF00699291`, Env. & Resource
Economics 7:193–196) — makalenin **başlığı** birebir bizim sorunumuz:
*"Constant quota versus constant effort harvesting"*.

Bizim `d = 8.0`'ımız **constant quota**. `H_MSY = rK/4` standart eşik. Ve
alıntı D-081'in (d) adımını aynen söylüyor: *"constant quota harvesting is at
the lower limit — any disturbance that decreases the population size leads to
extinction."*

⇒ **D-081'in beş adımının hiçbiri çürütülmedi.** *"Kademeli kıtlık yok"*
bizim evrenimizin kusuru değil, **sabit kota rejiminin bilinen özelliği**.

### ⛔ Bulgu 2 — DR'nin verdiği iki çıkış da bizde **mekanizmayı yok ediyor**

DR iki alternatif verdi, ikisi de matematiksel olarak doğru: **constant
effort** (`P* = (r−h)K/r`) ve **escapement** (Hilker & Liz 2020,
`10.1007/s12080-020-00465-8`: `T ≤ K` ise `T` küresel çekici).

⚠ **İkisi de kıtlığı ortadan kaldırıyor, çöküşü değil sadece.** Hasat
`h·P` olarak tanımlıysa kimse **eksik almaz** ⇒ paylaştırılacak bir şey
yoktur ⇒ **sıralı erişimin tahkim edeceği hiçbir şey kalmaz**. DR bunu
göremezdi: bizim **karneye ihtiyacımız olduğunu** bilmiyor.

### ⭐ Bulgu 3 — üçüncü yol çalışıyor: **Holling II** (keşifsel hesap)

Brief'in Q2'sinde adı geçiyordu, DR yalnız *"empirical studies are sparse"*
deyip geçti. Kendim hesapladım: **talep sabit kalır (8.0), gerçekleşen hasat
stoka bağlanır**, `gerçekleşen = d·P/(h+P)`, `h = 2.0`, N=8, olay içinde
sıralı erişim (her ajandan sonra stok güncelleniyor):

| olay | havuz/kişi | ilk ajan | son ajan | fark |
|---|---|---|---|---|
| 1 | 74.60 | 7.810 | 7.794 | 0.017 |
| **10** (landmark) | 36.62 | 7.654 | 7.596 | **0.058** |
| 15 | 14.33 | 7.320 | 7.071 | 0.250 |
| 18 | 0.56 | 5.660 | 2.414 | 3.246 |

**Sabit kotada aynı tablo:** olay 1–16 fark **tam sıfır**; olay 17'de
1.763 vs 0 (yedi ajan hiç alamıyor); sonrası hep sıfır.

⇒ Holling II **landmark'ta sıfırdan farklı ve tekdüze büyüyen** bir ayrışma
veriyor, kimse sıfır almıyor, havuz uçurumdan düşmüyor. **Ortamın
özelliğidir, karar kuralının değil** ⇒ K7'yi ve aksiyomu ihlal etmiyor. Ve
`metabolic_gain` **zaten aynı fonksiyon ailesini** kullanıyor (D-066/J9).

⚠ **Üç uyarı:**
1. Landmark'taki fark 7.65 üzerinden **0.058 = %0.76**. Sıfırdan farklı ama
   **küçük**; yeterliliği **gösterilmedi**.
2. **Rotasyonla çelişiyor** — sıra dönerse konumlar eşitlenir ve fark daha da
   küçülür. §N.1'in gerilimi burada sayıya döndü. 8 ajan/10 olayda rotasyon
   **tamamlanmıyor**, artık fark kalıyor; **ne kadar, ölçülmedi**.
3. **Yeni bir sabit (`h`) girer** ⇒ P0-b'nin kapasite sorusu **kaybolmuyor,
   yer değiştiriyor**.

### ⚠ Bulgu 4 — Price kestirimi küçük N'de yalnız gürültülü değil, **yanlı**

**Rice 2008** (`10.1186/1471-2148-8-262`) — **açık erişimden okundu ve
doğrulandı** (Europe PMC `PMC2577117`): *"the expected change due to
selection in a very small population can be substantially larger than would
be expected from classical theory… the amplification of the selection
differential decays with increasing population size"*, Şekil 1 başlığı
*"Amplification of expected selection differentials in small populations"*.

⇒ **`Cov(w, z)` küçük N'de şişkin olabilir.** D-076'nın getirdiği Price
eşitliği bu uyarıyla birlikte okunmalı ve **ikinci ön-kayıta sınır olarak**
yazılmalı.

### Bulgu 5 — üç kimlik hatası daha (onuncu, on birinci, on ikinci)

Hepsi **tamir edilebilir**; desen artık net: **makaleyi buluyor, künyeyi
uyduruyor**.

- *"Maklakov & Chapman 2021"* (`10.1002/evl3.254`) ⇒ gerçek yazarlar
  **Carlsson, Ivimey-Cook, Duxbury, Edden, Sales & Maklakov**; **Chapman
  yazar değil**.
- *"Ioannidis 2022, Adv. Theor. Simul. 5(1):2100182"* ⇒ doğrusu
  ***Mathematical Biosciences* 345:108782** (DOI doğruydu, dergi uydurma).
- *"Moher ve ark. 2010 (Lancet 375:1133–1143)"* ⇒ CONSORT 2010 E&E =
  **BMJ 340:c869**.
- ❌ *"Atwood 2020, wildlife textbook"* — **hiçbir tanımlayıcı yok**,
  kullanılmadı.
- ⚠ *Gomez 2018* (`10.5287/ora-jv6j78zbd`) **gerçek** (DataCite) ama
  ***Ghosts and bottlenecks in elastic snap-through*** — **elastisite tezi**;
  saddle-node hayaleti genel bir olgu olduğu için fizik taşınıyor, ama
  sorduğum **ölçekleme yasası verilmedi**.
- ⚠ *Földesi 2021* — **ticari firma blogu**, kaynak sayılmadı.

### ⭐ Bulgu 6 — süreç: **ilk kez bir boşluk ilan edildi**

Q3'ün ikinci yarısına DR *"(No specific claim found in sources – inference
from population genetics theory.)"* yazdı. **Üç turdur istediğimiz şey tam
olarak buydu.** ⇒ *"gösteremezsen gösteremediğini yaz"* şartı çalışıyor, ve
**kaynakça da eklendi** — D-080'in iki düzeltmesinden ikincisi tuttu.

### Yan kazanım — ikinci ön-kayıt için iki alet

- **Siepe ve ark. 2024**, simülasyon çalışmaları için ön-kayıt şablonu —
  künyesini ben tamamladım: **`10.1037/met0000695`** (*Psychological
  Methods*), önbaskı `10.31234/osf.io/ufgy6`.
- **NRC 2010**'un *"fixed study time"* / *"fixed event time"* ayrımı: bizim
  landmark'ımız **fixed study time**, ve ölçümden önceki ölüm **rekabet eden
  risk** olarak adlandırılıyor — K1–K3'ün gerekçesini dışarıdan destekliyor.
- ⚠ **Pozitif kontrol** benzetmesi P0-b'yi savunmak için tam yerinde ama
  **kaynağı bir firma blogu** ⇒ daha iyi bir dayanak gerekiyor.

### Sınırlar

**Hiçbir karar verilmedi, hiçbir kod değişmedi, hiçbir sabit değişmedi.**
Yer doğrulaması yalnız **Rice 2008**'de yapılabildi (açık erişim); Azar 1996
ve Hilker & Liz 2020 **ödemeli**, alıntıları **doğrulanamadı**. P.5'teki
Holling II tablosu **keşifsel aritmetik**: model koşulmadı, ajan yaşamadı,
ve hesap *"her ajan her olayda DEFECT eder"* varsayımına dayanıyor.
**Rotasyonun etkisi hesaba katılmadı.**

---

## D-083 · 2026-08-14 · Rotasyon farkı öldürmüyor, ve prompt kanalı **tam duyarlı** — ①'in önündeki engel kaldırıldı

**Durum:** iki ölçüm · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** · **kod
değişmedi, sabit değişmedi, model koşulmadı** · D-082'nin açtığı iş

### Neden burada

D-082'de Holling II'nin landmark'ta **%0.76**'lık bir ayrışma verdiğini
hesaplamış, iki uyarı bırakmıştım: (1) rotasyon bunu daha da kısabilir,
(2) fark davranışa taşınacak kanalın çözünürlüğünün altında kalabilir.
İkisi de ölçüldü. **Biri doğrulandı, biri çürütüldü.**

### Ölçüm 1 — rotasyon farkı **kısıyor ama öldürmüyor**

Holling II (`h=2.0`), N=8, kişi başı `K=100`, `P₀=0.8K`, olay 1–10:

| | hasat yayılımı | birikmiş enerji yayılımı | farklı ajan |
|---|---|---|---|
| sabit sıra | 0.325 (%0.42) | 0.00345 (%0.087) | **8/8** |
| **rotasyonlu** | 0.071 (%0.092) | **0.00077 (%0.019)** | **8/8** |
| rotasyonlu, 16 olay | 0.458 | — | **8/8** |

⭐ **İki sonuç:**
1. Rotasyon yayılımı **~4.5 kat kısıyor** — uyarım yönü doğruymuş.
2. ⭐ **Ama sıfırlamıyor: her yapılandırmada 8 ajanın 8'i de farklı.**
   Üstelik rotasyon **tamamlandığında** (16 olay = 2×N) yayılım
   **büyüyor**, küçülmüyor.

⇒ **D-079/§N.1'in çıkarımı ölçüldü.** Orada *"dönen sırada birikimli
maruziyet eşitlenir; geriye kalan, durumun doğrusal olmayan biriktiği için
oluşan yörünge ayrışmasıdır"* diye yazmış ve **bunun benim çıkarımım
olduğunu, kaynağın bulgusu olmadığını** belirtmiştim. Artık sayısı var.

### ⛔ Ölçüm 2 — **kendi endişemi çürüttüm**

Prompt'a giden sayıların **iki ondalığa yuvarlandığını** görüp *"fark 0.005'i
geçmezse prompt'lar özdeş olur, D-078'e döneriz"* demiştim. **Yanlıştı.**

Yuvarlama **yalnız sistem prompt'unda** var: anı şiddeti
(`{magnitude:.2f}`), drift uyarısı (`{bias:.2f}`), stratejik beklenti
(`{p:.2f}`). ⚠ **Ama karar anında modele giden kullanıcı mesajı bunlardan
biri değil** — `graph.py:1079`:

```
user_content = view.model_dump_json()
```

`AgentView` **tam kayan nokta duyarlılığıyla** serileştiriliyor. Ölçtüm:

| enerji farkı | prompt değişiyor mu |
|---|---|
| 0.00345 (sabit sıra, landmark) | ✅ `0.4523177` → `0.4557677` |
| **0.00077 (rotasyonlu, landmark)** | ✅ `0.4523177` → `0.4530877` |
| **1e-9 (uç test)** | ✅ `0.4523177` → `0.452317701` |

⇒ ⭐ **Kanal tam açık.** 1e-9'luk bir fark bile prompt dizgisini değiştiriyor.
Holling II'nin landmark'ta ürettiği fark **3.–4. ondalıkta**, yani rahatça
görünür.

⚠ **Ayrıca not:** `apply_emotional_weight` prompt'a **sayı değil alan adı**
enjekte ediyor ⇒ o kanal sürekli değil **kategorik**; yalnız somatik
işaretlerin **sıralaması** değişince değişir.

### ⚠ Kapanmayan soru — ve sıradaki ölçüm

**Prompt'un değişmesi kararın değişmesini garanti etmez.** Greedy argmax
4. ondalıktaki bir değişikliğe tepki vermeyebilir.

⇒ **Sıradaki ölçüm (model gerekiyor, ~dakikalar):** yalnız enerjinin
ondalığında farklılaşan iki `AgentView` üretilip gerçek modelle greedy
koşulur, ve **kararın hangi fark büyüklüğünde değiştiği** taranır. Bu,
①'in çalışıp çalışmayacağını **kod yazmadan, pilot koşmadan** söyler.

⚠ Elimizdeki dolaylı kanıt **iki yönlü**: D-035 adapter'ın faz-2
kararlarının **%68'ini** değiştirdiğini ölçtü (model girdiye duyarlı), ama
bir adapter takası 4. ondalıktaki bir basamaktan **çok daha büyük** bir
tedirginlik. ⇒ **Tahmin edilmiyor, ölçülecek.**

### Sınırlar

**Saf aritmetik + bir serileştirme testi.** Model koşulmadı, ajan yaşamadı,
adapter yazılmadı. Rotasyon hesabı *"her ajan her olayda DEFECT eder"*
varsayımına dayanıyor. Enerji yayılımı **birikmiş metabolik kazanç**
üzerinden hesaplandı; gerçek `energy` durumu ayrıca **azalma** terimi
taşıyor ve bu hesaba katılmadı — ⚠ azalma her ajanda **aynı** olduğu için
yayılımı değiştirmez, ama **düzeyi** değiştirir.

---

## D-084 · 2026-08-14 · Karar kanalı **doygun**: 1e-9'dan 1e-1'e kadar her tedirginlik aynı hasadı veriyor

**Durum:** ölçüm (gerçek model, greedy) · **Etiket:** ⚠ **keşifsel,
ön-kayıtlı değil** · `DAU_LORA_ENABLED=0`, **adapter yazılmadı, sabit
değişmedi** · süre **43.2 sn** (model yüklemesi dahil 20.4 sn)

### Soru

D-083 prompt kanalının **tam duyarlı** olduğunu gösterdi (1e-9 bile dizgiyi
değiştiriyor). Kapanmayan soru: **prompt'un değişmesi kararı değiştiriyor
mu?** ①'in çalışıp çalışmadığı buna bağlıydı.

### Yöntem

Yalnız `energy` ondalığında farklılaşan `AgentView`'ler, çıplak
`SYSTEM_PROMPT`, gerçek Llama-3.1-8B-Instruct, greedy, on fark büyüklüğü.
Karşılaştırma **iki düzeyde**: ham metin **ve** `decision_to_extraction`
(kararın eşlendiği hasat miktarı).

### ⛔ Sonuç

| fark | ham metin | **hasat** |
|---|---|---|
| **0 (kontrol)** | aynı | 8.0 |
| 1e-9 | **farklı** (165. karakterden) | 8.0 |
| 1e-7 | **farklı** | 8.0 |
| 1e-5 | **farklı** | 8.0 |
| 1e-4 | aynı | 8.0 |
| **7.7e-4 (rotasyonlu landmark)** | **farklı** | 8.0 |
| 3.45e-3 | **farklı** | 8.0 |
| 1e-2 | **farklı** | 8.0 |
| 5e-2 | aynı | 8.0 |
| 1e-1 | **farklı** (70. karakterden) | 8.0 |

**Benzersiz hasat miktarı: 1.** Benzersiz outcome: `defect`. **Onda on.**

⭐ **Kontrol geçti** (fark=0 → birebir aynı) ⇒ sonda deterministik, D-037
tutuyor.

⚠ **Metin farkı büyüklükle sıralı değil:** 1e-9 metni değiştiriyor ama 1e-4
değiştirmiyor. Yani ham metin duyarlılığı **kaotik**, ölçüsüz.

### Ne öldü, ne ölmedi

⛔ **Karar kanalı doygun.** D-068'in çöküşü (%94–100 DEFECT) burada
mekanizma olarak görünüyor: davranış eşlemesinin **tek bir soğurucu çıktısı**
var, dolayısıyla **hiçbir girdi tedirginliği onu oynatamaz**. ⇒ ajanlar
**karar vererek ayrışamaz**.

⭐ **Ama ① karar kanalına ihtiyaç duymuyor.** Holling II'de iki ajan aynı
şeye karar verip (*"8.0 al"*) **farklı miktar alıyor** (7.654 vs 7.596,
D-082) — çünkü ayrım **ortamın karnesinde**, ajanın tercihinde değil.
Oradan `metabolic_gain` → enerji → iç durum → drift'e akıyor, ve **birincil
uç nokta landmark'taki drift**.

⇒ ⭐ **①'in ürettiği şey yeniden tarif edilmeli:** *"özdeş karar veren ama
farklı yaşayan ajanlar"*. ⚠ Bunun aksiyomu (*"trait yaşamdan çıkar"*)
karşılayıp karşılamadığı **tasarım kararıdır ve Yasin'indir** (D-007) —
Claude Code tek başına vermez.

### Sınırlar — ⚠ önemli

- **Çıplak `SYSTEM_PROMPT` kullanıldı**: anı bloğu, drift uyarısı, stratejik
  beklenti katmanları **yok**. Gerçek ajan 10. olayda bunları taşır. ⇒ sonda
  gerçek prompt'un değişkenliği için bir **alt sınır**. ⚠ Ama drift uyarısı
  `.2f` yuvarlanıyor (D-083) yani o katman **daha az** duyarlı, daha çok
  değil.
- **Tek karar bağlamı**, tek durum vektörü, on örnek. Yaşam boyu davranışın
  taraması değil.
- Doygunluk **bugünkü fizikte** ölçüldü; A4-① metabolik döngüsü davranışı
  değiştirirse (K7 kapattı) bu sonuç yeniden ölçülmeli.
- ⚠ Sonda çıktısını **repo köküne** yazdı, fark edildi ve scratchpad'e
  taşındı. Repoda iz bırakmadı.

---

## D-085 · 2026-08-14 · Doğrulama koşumu: **ölçüm makinesi çalışıyor**, ama uygunluk kapısı kalıtımın %90'ını kesiyor

**Durum:** ölçüm (doğrulama koşumu) · **Etiket:** ⚠ **keşifsel, ön-kayıtlı
değil** · N=4 tohum (5001–5004), üç kol, `--lora`, gen1+gen2 · ham çıktı
`dau_runs/validate_d085_n1_local.json` + `..._n3_local.json` ·
`run_quality = flagged` (ikisinde de) · süre **5 dk 48 sn + 23 dk**

### Neden koşuldu

**Aletin bugünkü hâliyle uçtan uca tek bir soy koşulmamıştı.** D-071/072/073
(havuz teriminin normalizasyonu, landmark aletlemesi, LOCF'un kaldırılması)
uygulandıktan sonra yapılan tek ölçüm D-078'in 12 olaylık sondasıydı.
⚠ Bu oturumda P0 tartışılırken kullanılan *"ömürler 11–20"*, *"davranış
%94–100 DEFECT"* gibi sayılar **eski aletin** pilotundan (D-068) geliyordu.
Yasin'in planının birinci maddesi — *"aleti tam anlamıyla doğrula"* —
yapılmamıştı.

### ✅ Çalışan: ölçüm makinesi

| | Sonuç |
|---|---|
| Uçtan uca koşum | `exit 0`, çökme yok · 3 OOM uyarısı, toparladı |
| **Landmark'a ulaşan soy** | ⭐ **12/12** — grace penceresi tasarlandığı gibi çalışıyor, **sansür yok** |
| **Landmark aletlemesi** | ⭐ **İlk kez canlıda yazıldı:** `landmark_energy`, `landmark_drift_magnitudes`, `energy_mean_over_life`, `delta_pe_landmark` |
| Tekrarlanabilirlik | `I4.1` replay **birebir aynı** ⇒ D-037 tutuyor |
| Adapter davranışı değiştiriyor mu | seed 5001'de faz-2 kararlarının **8/11'i** farklı (%73) — kanal 2 canlı |
| Ömür değişkenliği | tohum bazında **11 · 20 · 17 · 13** olay — gerçek yayılım var |

### ⛔ Bulgu 1 — uygunluk kapısı kalıtımın **%90'ını** kesiyor

| | anı |
|---|---|
| `F_agent` kapısı **açık** (gerçek yol) | **4** anı / 12 soy — ve **8 soy hiçbir şey almıyor** |
| `f_agent=None` duyarlılık kolu | **39** anı |

Sebebi cebirsel. Kapı:
`w_transfer = memory_score × F_agent × valans`, eşik **0.6**.
`memory_score ≤ 1` ve valans nötrken 1 ⇒ **`w_transfer` `F_agent`'ı aşamaz.**

Ölçülen `F_agent`: **0.084 – 0.184**, ortalama **0.139**. Eşiğin **dörtte
biri**. ⇒ Aksiyomun *"iz iki kanaldan aktarılır"* iddiasında **Kanal 1
neredeyse hiç akmıyor**.

⚠ **Bu bir bug değil**, tasarlanmış kapının *"kimsenin fit olmadığı"* bir
evrende verdiği doğru sonuç. D-066 ölümü gerçek yapınca ajanlar 11–20 olayda
ölmeye başladı ve `F_agent` kapının çok altına düştü.

### ⛔ Bulgu 2 — `fitness_class` yine **12/12 `low`**

D-060'ın *"120/120 kolda tek değer"* bulgusu, A4 düzeltmesinden sonra
**aynen geri gelmiş**. Uygunluk sınıfı hiçbir ayrım taşımıyor.

⚠ Ama `F_agent`'ın **kendisi** ayrım taşıyor (0.084–0.184, kollar arasında
farklı) — sorun sürekli değerde değil, **sınıflandırmanın eşiklerinde**.

### ⚠ Bulgu 3 — enerji terimi neredeyse ölü (⚠ *"tam sıfır"* demiştim, yanlıştı)

`f_agent_energy_final`: **12 soyun 10'unda 0.000**, kalan ikisinde 0.041 ve
0.040. Yani fitness'ın **%40'ını** taşıyan terim pratikte hiçbir şey
katmıyor — çünkü ajanlar **enerjileri bittiği için** ölüyor, dolayısıyla son
enerji yapısı gereği tabana yakın.

⚠ **Düzeltme:** N=1 sonrası *"yapı gereği tam sıfır"* demiştim; dört tohumda
iki istisna çıktı. Doğrusu: **10/12'de 0.000, azami 0.041.**

⭐ **Ve ironi:** enerji **bilgi taşıyor** — `energy_mean_over_life` 0.59–0.86,
`landmark_energy` 0.130–1.000 arasında. K2 uç nokta için tam da bunları
seçmişti. `F_agent` ise onları değil, ölüm anındaki sıfırı okuyor.

### ⚠ Bulgu 4 — `landmark_energy` **12'nin 5'inde tavanda** (1.000)

Enerji `METRIC_MAX`'tan başlıyor ve grace penceresi 10 olay sürüyor ⇒ 10.
olayda ajanların yaklaşık %40'ı **hâlâ tavanda**. ⇒ K2'nin seçtiği landmark
enerji okuması **doygunluk riski taşıyor**; `energy_mean_over_life`
(0.59–0.86, hiç tavana değmiyor) daha ayırt edici.
⚠ Bu bir **ön-kayıt tasarım sorunudur**, kod hatası değil.

### ⭐ Bulgu 5 — ayrım **gen2 ömründe** görünüyor

| tohum | lived | null | shuffle |
|---|---|---|---|
| 5002 | **20** | 19 | 19 |
| 5003 | 18 | 19 | 19 |
| 5004 | **14** | **10** | **10** |

Gen1'de kollar aynı ömrü yaşıyor (adapter yalnız faz-2'yi etkiliyor), ama
**varislerin ömrü kola göre farklılaşıyor** — 5004'te 14'e karşı 10.
⚠ Hücre başına N=1, **gözlem, iddia değil**. Ama bu, aletin bir ayrım
taşıdığı ilk canlı işaret.

### ⭐ Bulgu 6 — D-084 canlıda doğrulandı

Seed 5001'de `lived` ve `null` kollarının `F_agent`'ı **bit düzeyinde aynı**
(0.11855132990852824) ve `delta_pool`'ları da aynı (72.58494322683171) —
**ama faz-2 kararlarının 8/11'i farklı.**

⇒ **Farklı metin, aynı hasat.** D-084'ün sondasının öngördüğü davranış
doygunluğu, gerçek koşumda birebir çıktı.

### Bayraklar

`I3.2` (Precision-PE atıl, `pi_n_distinct=2 < 8` ⇒ **L13 bugünkü aletle de
geçerli**) · `I1.3b` (kırpma doygun ⇒ **L18 sürüyor**) · `I3.4` (ömür 11–20,
bütçe 50 ⇒ rapor modu, **D-073 tasarlandığı gibi**) · `I5.4` yalnız N=1'de
(miras somatik ölçek hiç uygulanmadı — Kanal 1 kapalı olduğu için beklenen).

### Sınırlar

**Dört tohum, hücre başına bir soy.** Hipotez testi değil, alet denetimi.
⚠ **P0 bu koşumda test edilmedi** — sıralı erişim, Holling kuralı, çıkarım
bedeli, popülasyon: hiçbiri yok. Bulgular aletin **kendi** özellikleri, ve
popülasyon katmanı bunların üstüne kurulursa **hepsi miras alınır**.
Hiçbir sabit değişmedi, hiçbir karar verilmedi.

---

## D-086 · 2026-08-14 · `F_agent`'in enerji terimi **yaşamı** okuyor, ölümü değil

**Durum:** kod değişikliği · **Etiket:** ⚠ **formül değişikliği** — ikinci
ön-kayıtta ilan edilmeli · commit `f3a132d` · suite **417 passed** (414 + 3)
· Yasin onayladı (§2.3)

### Sorun — D-085'in ölçtüğü

`F = 0.4·E + 0.3·havuz + 0.3·hayatta` formülünde enerji terimi, dört tohumun
**on iki soyunun onunda tam olarak 0.0000** katkı yapıyordu.

Sebep bir ayar değil, **tanım**: D-066'dan beri tek ölüm biçimi enerji
tükenmesi ⇒ `E_final` **ölüm kuralının kendisi tarafından** sıfıra çakılıyor.
Terim yaşamayı değil **ölmeyi** ölçüyordu.

⚠ **Teşhis yeniydi ama gözlem değildi.** `run_protocol_c_prime.py:355` zaten
*"it measures the ending, not the living"* diye yazıyordu — ama bunu **yalnız
K2'nin uç nokta okumasına** uygulamış, `F_agent`'ı ölü terimin üzerinde
bırakmıştı. D-071'in hayatta kalma teriminde bulduğu kusurun
(`t_survived/t_survived ≡ 1.0`) **aynı sınıfı**: adının söylediği şeyi
ölçmeyen bir terim.

### Üç seçenek, aynı on iki soyda ölçüldü

| | `F_agent` | sınıf dağılımı | 0.6 kapısı |
|---|---|---|---|
| `E_final` (eski) | 0.083 – 0.184 | **12/12 low** | 0/12 |
| ⭐ **ömür-boyu ortalama** | **0.334 – 0.490** | 1 low, **11 normal** | 0/12 |
| landmark enerjisi | 0.171 – 0.568 | 4 low, 8 normal | 0/12 |

### Reddedilen alternatif — ve **neden yayılıma bakılarak seçilmedi**

Landmark enerjisinin **yayılımı en büyüktü (0.398)** ve tam da bu yüzden
**alınmadı**:

1. ⛔ **Döngüsel.** Landmark enerjisi **K2'nin uç noktası**. Fitness'a koymak
   `F_agent` ile sonucu **aynı sayıyı paylaştırır** ⇒ D-075'in işaretlediği
   Mills & Beatty totolojisi geri gelir. Üç katman ayrı kalmalı:
   **`F_agent` (girdi) → `w` (varis) → `z` (landmark drift, sonuç)**.
2. Girdisi **12'nin 5'inde tavanda**; ömür-boyu ortalama hiç tavana değmiyor.

⚠ §2.7 gereği: seçim **sonuca bakılarak yapılmadı**. Yayılımı en büyük olan
seçenek reddedildi, gerekçe **yapısal** (döngüsellik + doygunluk).

### Uygulama

`self_model.f_agent_inputs` artık olay kaydındaki enerjilerin ortalamasını
veriyor. **Yeni boru hattı gerekmedi** — enerji zaten her karar satırında
vardı (iki yazıcı da koyuyor).

**Adlandırma:** `energy_final` → `energy_lived`, JSON alanı
`f_agent_energy_lived`. Eski ad artık taşıdığı şeyi söylemiyordu (§2.8'in
tekrar eden hata deseni). ⇒ eski ve yeni koşumlar **alan adından** ayırt
edilebiliyor.

**Alet kimliği:** `tool_identity.fitness.energy_reading` eklendi
(`FITNESS_ENERGY_READING = "mean_over_life"`). Bloğun kendi yorumu
*"nothing else in the results file says which formula ran"* diyordu; artık
diyor. U5/D-030 deseni.

### Test ve mutasyon kontrolü (§2.4)

**Bekçi:** aynı `E_final`'e sahip ama enerji yörüngeleri farklı iki yaşam
**farklı `F_agent`** almalı. **Mutasyon uygulandı** (`energy_lived` = son
enerji) → test **kırıldı** → geri alındı. ✅

İki bekçi daha: enerji anahtarı olmayan bir olay **`ValueError` fırlatıyor**
(§2.9, sessiz fallback yok) · sıfır olaylı yaşam **mevcut enerjisini** alıyor
— bu bir boşluk değil, o yaşamın tek okuması.

⚠ **Kasıtlı test kırılması** (§2.5): `test_meta_observer`'ın bütçe sondası
payload'sız sentetik `Event` üretiyordu. Gerçek sistemde böyle bir olay yok;
sonda olayları **sabit** bir enerji taşıyacak biçimde güncellendi — sabit
olduğu için testin asıl konusu olan **survival paydasını** etkilemiyor.

### ⚠ Neyi ÇÖZMÜYOR

**Üç seçeneğin hiçbiri 0.6 aktarım eşiğini açmıyor.** `F_agent` 0.14'ten
0.45'e çıkıyor, eşik hâlâ 0.6 ⇒ **kalıtım hâlâ akmıyor**. Aktarım eşiği
kararı (D-085'in 1 numaralı maddesi) ayrı duruyor, ama artık **yeni ölçeğe
göre** türetilebilir — önerilen sıralamanın gerekçesi buydu.

### Sınırlar

Değişiklik **kalıtımı etkiliyor** (F_agent aktarım kapısına giriyor) ⇒
**D-085'in dört doğrulama koşumu artık karşılaştırılamaz**. Kabul edilebilir:
onlar alet denetimiydi, hipotez ölçümü değil.
⚠ `_resolve_f_agent` yaşam **sırasında** da çağrılıyor ⇒ `F_agent` artık
yaşam boyunca **yürüyen ortalama**. Yasin'e söylendi ve onayla girdi.

---

## D-087 · 2026-08-14 · Aktarım eşiği **yanlış niceliğe** uygulanmış — ve D-086'nın yan hasarı ölçüldü

**Durum:** ölçüm + yapısal denetim · **Etiket:** ⚠ **keşifsel** · **kod
değişmedi** · ham `dau_runs/validate_d087_postfix_n1.json` (seed 5005, N=1,
~6 dk) · D-085 verisi üzerinde yeniden hesap

### ⛔ Bulgu 1 — `w_transfer` kapısı **hiçbir zaman hiçbir şey geçirmedi**

D-085'in on iki soyunda aktarılan **4 anının 4'ü de `inherited_warning`**
(`n_transfer` = `n_inherited_warnings`, üçü de seed 5002'de). Yani hepsi
**düşük-uygunluk travma baypasından** geçmiş:

```
if f_value < FITNESS_LOW_THRESHOLD and trauma:   → aktar (baypas)
w_transfer = memory_score × F_agent × valans
if w_transfer < GENERATION_TRANSFER_THRESHOLD: continue   ← 12/12 burada
```

⇒ **`w_transfer` yolu 12 soyda 0 anı geçirdi.** Çalışan tek kalıtım yolu
baypastı.

### ⛔ Bulgu 2 — **D-086 o tek yolu kapattı** (benim açtığım hasar)

Baypas `F_agent < 0.35` istiyor. D-086 `F_agent`'ı 0.14'ten 0.45'e çıkardı.
Aynı on iki soy, yeni formülle yeniden hesaplandı:

| | eski `F_agent` | yeni `F_agent` |
|---|---|---|
| `FITNESS_LOW_THRESHOLD = 0.35` altında | **12 / 12** | **1 / 12** |

**Doğrulama koşumu (seed 5005, yeni kod):** `F_agent` 0.485 / 0.516 / 0.540,
sınıf **üçü de `normal`**, **aktarılan anı 0 / 0 / 0**, uyarı 0. Gölge kol
(`f_agent=None`) aynı yaşamlardan **3'er** anı aktarıyor.

⚠ **Bu tek koşum kanıt değil** — D-085'te de dört tohumun üçü sıfır vermişti.
**Kanıt aritmetiktir:** 4 aktarımın hepsini üreten baypas, artık on iki soyun
**en fazla birinde** ateşlenebilir.

⇒ **D-086 ölü bir terimi düzeltti ve tek canlı kalıtım yolunu kapattı.**

### ⭐ Bulgu 3 — eşik, kalibre edildiği nicelikten **başkasına** uygulanmış

Aynı `0.6` sabiti iki farklı şeyi kapılıyor:

```
_legacy_select_for_transfer:   memory_score           < 0.6
select_for_transfer (F_agent): memory_score × F × v   < 0.6
```

**Git sırayı gösteriyor:**

| commit | tarih | ne |
|---|---|---|
| `cf400eb` | 2026-08-01 | **Layer-3** — eşik doğuyor, `memory_score`'u kapılıyor |
| `da6880b` | 2026-08-03 | **Layer-4** — `F_agent`/`w_transfer` geliyor, **aynı sabit çarpıma uygulanıyor** |

`memory_score ≤ 1` olduğu için `w_transfer ≤ F_agent × valans` ⇒ kapı fiilen
**ilan edilmemiş bir *"F_agent ≥ 0.6"* şartına** dönüşmüş.

**Ulaşılabilirlik** (valans = `1 + tanh(ödül − tehdit)`, tavan 2):

| `F_agent` | gereken |
|---|---|
| 0.139 (D-086 öncesi) | valans ≥ 4.32 ⇒ ⛔ **matematiksel olarak imkânsız** |
| 0.446 (D-086 sonrası) | valans ≥ 1.35 ⇒ **ödül − tehdit ≥ 0.36** |
| 0.6 | nötr valans yeter |

⇒ D-086 kapıyı **imkânsızdan koşullu-mümkün**e taşıdı; tek başına yetmedi.

### ⚠ Bulgu 4 — iç tutarsızlık: bantlar ölü kod olurdu

Kod üç uygunluk bandı (`low` <0.35 · `normal` · `high` ≥0.70) ve **her birine
ayrı aktarım politikası** tanımlıyor. Kapı fiilen `F_agent ≥ 0.6` istiyorsa
`low` ve `normal` bantlarının politika makinesi **ölü koddur**. ⇒ Tasarım,
düşük ve orta uygunluktaki ajanların bir şey aktarmasını **bekliyordu**.

### ⭐ Yapısal çerçeve — neden bu bir *"sayıyı düşür"* sorunu değil

Aktarımı **mutlak uygunluğa** kapılamak, seçilimi **iki kez** saymaktır:
uygunluk zaten `w`'yi (varis sayısını) belirleyecek (D-076/Price). Aynı
uygunluğun ayrıca *"hiçbir şey aktarılsın mı"* anahtarını da çevirmesi,
**K4-b/D-070'in havuz teriminde bulduğu çifte sayımın** aynısı
(*"longevity wearing a second hat"*, Stearns 1989).

⇒ Savunulabilir yön: **`F_agent` hangi anıların aktarılacağını biçimlendirir,
hiç aktarılıp aktarılmayacağını değil.** Salience çıtası (`memory_score`)
kalibre edildiği yerde kalır; uygunluk zaten var olan **bant politikalarından**
girer.

⚠ **Bu bir tasarım kararıdır ve Yasin'indir (D-007).** Claude Code önermiştir,
uygulamamıştır. **Hiçbir sabit değişmedi.**

### Sınırlar

Doğrulama koşumu **tek tohum, üç soy**. Bant geçişi hesabı D-085'in
**aynı** verisi üzerinde yeniden hesaptır, yeni ölçüm değil. Valans için
gerçek ödül/tehdit değerleri koşum çıktısında **yok** — ulaşılabilirlik
tablosu bu yüzden `memory_score = 1.0` en iyi durumunu varsayıyor.

---

## D-089 · 2026-08-14 · D-088 doğrulandı: **kalıtım akıyor**, ve iki yan kapı da açıldı

**Durum:** doğrulama koşumu · **Etiket:** ⚠ **keşifsel, ön-kayıtlı değil** ·
N=2 (seed 5006–5007), üç kol, `--lora` · ham
`dau_runs/validate_d088_n2.json` · `run_quality = flagged` · **kod değişmedi**

### ⭐ Bulgu 1 — kalıtım akıyor, ve gölge kolla **örtüşüyor**

| | D-085 (D-086/088 öncesi) | **D-089 (şimdi)** |
|---|---|---|
| aktarılan anı | **4 / 12 soy** — hepsi travma baypasından | **23 / 6 soy** (3–5 her soya) |
| hiç almayan soy | **8 / 12** | **0 / 6** |
| gölge kol (`f_agent=None`) | 39 / 12 soy | 22 / 6 soy |

⭐ **F_agent yolu 23, gölge yol 22.** D-088'in tam beklentisi buydu: kapı
kalibre edildiği niceliğe döndüğü için F_agent yolu artık Layer-3'ün salience
oranına oturuyor, üstüne bant politikaları biniyor. Aradaki **+1**, seed
5007/`lived`'in travma baypasından gelen uyarısı.

⚠ **İddia daraltılıyor:** *"kalıtım akıyor"* denebilir; *"doğru miktarda
akıyor"* **denemez** — doğru miktarın ölçüsü yok. N=2.

### ⭐ Bulgu 2 — `I5.4` ilk kez **geçti**: somatik miras uygulanıyor

D-085'te `I5.4` *"never applied (skipped=111)"* diye bayrak basıyordu.
Şimdi: **`applied 14x`**, ve `n_retrieval_context` her soyda 3–5.

⇒ Kanal 1 yalnız *seçilmiyor*, **varise gerçekten ulaşıyor** ve somatik
ölçek uygulanıyor. ⚠ GAP-3'ün *"gen2 ilk olay ata verisini kaçırıyor"*
sorunu bundan **ayrı**; bu bulgu onu kapatmıyor.

### ⭐ Bulgu 3 — `fitness_class` **ilk kez ayrım taşıyor**

`F_agent` 0.334 – 0.544 · sınıflar **4 `normal`, 2 `low`**.

D-085'te 12/12 `low`, D-087'de 3/3 `normal` idi — yani dejenerasyon iki kez
**yer değiştirmişti**. İlk kez **iki bant birden** doluyor.
⚠ **`high` bandı (≥0.70) hâlâ boş.** Açık madde A tamamen kapanmadı, ama
aciliyeti düştü.

### Bulgu 4 — landmark doygunluğu **azaldı ama sürüyor**

`landmark_energy`: 0.685 · 0.408 · **1.000** · 0.400 · 0.556 · 0.400
⇒ tavanda **1/6** (D-085'te 5/12). Ömürler uzadığı için enerji landmark'a
kadar daha çok düşüyor. ⚠ Risk **azaldı, kalkmadı** — açık madde B duruyor.

### Bulgu 5 — ömürler uzadı

Faz-1: **19 · 19 · 19 · 16 · 16 · 16** (D-085: 11–20). Gen2: 19 · 18 · 20 ·
15 · 15 · 15. ⚠ Seed 5006'da gen2 ömrü **kola göre farklı** (19/18/20) —
gözlem, hücre başına N=1.

### Bayraklar

`I3.2` ⚠ **kısmen düzeldi**: gen1 `pi_n_distinct=9 ≥ 8` (ilk kez geçiyor),
gen2 hâlâ 3 ⇒ bayrak gen2'den geliyor. L13 gen1 için **artık geçerli
olmayabilir**, ölçülmeli. · `I1.3b` kırpma 14/14 doygun ⇒ **L18 sürüyor** ·
`I3.4` rapor modu.

### Sınırlar

**İki tohum, altı soy.** Alet denetimi, hipotez testi değil. Aktarım
sayılarının *"doğru"* olduğu iddia edilmiyor — yalnız **sıfır olmadığı** ve
gölge kolla tutarlı olduğu. Üç OOM uyarısı, çökme yok.

---

## D-090 · 2026-08-14 · Karar kanalı **ölü değil** — drift ekseninde temiz bir eşik var

**Durum:** ölçüm (gerçek model, greedy) · **Etiket:** ⚠ **keşifsel** ·
`DAU_LORA_ENABLED=0`, **adapter yazılmadı, sabit değişmedi** · 36 + 21 çağrı,
**83.5 sn + 53.9 sn** · ham `scratchpad/sweep_d090.json`

### Neden

D-084 *"karar kanalı doygun"* demişti — ama **dar bir sondaydı**: çıplak
`SYSTEM_PROMPT`, tek durum vektörü, yalnız enerji. Ve C/D/E kararlarının
**üçü de** o tek ölçüme dayanıyordu. Bu tarama gerçek prompt katmanlarını
kuruyor (`_format_memory_context`, `STRATEGIC_EXPECTATION_TEMPLATE`,
`DRIFT_WARNING_TEMPLATE` — kodun kendi fonksiyonları, yeniden üretilmedi).

### Bulgu 1 — geniş tarama: **35/36 `defect`**, ama biri değil

Enerji × yük × bağlam (36 kombinasyon): **35 `defect` (8.0)**, **1
`cooperate` (2.0)**. Tek istisna: **anı + drift uyarısı + ölüme yakın enerji**.
⇒ D-068'in sahada ölçtüğü %94–100 DEFECT ile tutarlı, **ama mutlak değil**.

### ⭐ Bulgu 2 — istisna **tekil nokta değil, havza**

Aynı girdi **3 kez** koşuldu, **3 kez aynı** ⇒ deterministik, D-037 tutuyor.

**Enerji ekseni** (anı + drift 2.4, yük 0.05):

| E | 0.0 | 0.02 | 0.03 | 0.04 | 0.05 | 0.06 | 0.08 | 0.1 | 0.15 | 0.2 | 0.3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | D | **C** | D | **C** | **C** | **C** | **C** | D | D | D | D |

⇒ **E ≈ [0.04, 0.08]** aralığında **dört ardışık `cooperate`** — havza var, ama
**dar** ve kenarları tırtıklı (0.02'de C, 0.03'te D). Tırtıklılık D-084'ün
bulduğu kaotik duyarlılıkla uyumlu.

### ⭐⭐ Bulgu 3 — **drift ekseni temiz ve tekdüze**

**Drift ekseni** (E=0.05, yük 0.05):

| drift | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 | 2.4 | 3.0 |
|---|---|---|---|---|---|---|---|
| | D | D | D | **C** | **C** | **C** | **C** |

⇒ **Tırtık yok.** `(1.0, 1.5]` arasında bir eşik ve üstünde **dört ardışık
`cooperate`**. Bu, gürültü değil **kaldıraç**.

### ⭐ Ne değişti — C/D/E'nin çerçevesi

D-084'ün *"kanal doygun"*u **çok geniş okunmuştu**. Doğrusu:

> **Davranış ölü değil; ajanlar o bölgeye nadiren giriyor.** Cooperate,
> *travma-bilgili + düşük enerjili* durumda çıkıyor, ve bugünkü fizik
> ajanları oraya sokmuyor.

⇒ ⭐ **D (çıkarımın bedeli) *"muhtemelen anlamsız"*dan *"en umut verici
kaldıraç"*a döndü.** Bedel, ajanları tam da bu bölgeye — daha hızlı düşen
enerji ve daha çok drift — sokar. ⚠ Ve bu bir **davranışsal önsel değil**,
dünyanın özelliği ⇒ **K7'yi açmıyor**.

⭐ **Ve D-089 bunu zaten genişletmiş olabilir:** kalıtım artık aktığı için
varisler **doğuştan** miras drift ve anı taşıyor — yani bu bölgeye eskisinden
**yakın** başlıyorlar. ⚠ Ölçülmedi, çıkarım.

### Sınırlar — ⚠ ağır

- **Prompt sentetik.** Katman fonksiyonları gerçek, ama içlerine koyduğum
  **değerler benim** (anı seti, beklenti, drift). Canlı koşumun ürettiği
  prompt bu değil.
- **Tek karar bağlamı**, tek anı seti, tek `resource_scarcity`.
- **Drift eşiği `(1.0, 1.5]` aralığında**; gerçek sınır ölçülmedi.
  ⚠ 1.5'in `DRIFT_TRANSFER_MIN` ile aynı olması **örnekleme ızgaramın
  eseri**, bir bulgu değil.
- Enerji havzasının kenarları tırtıklı ⇒ bir kısmı kaotik duyarlılık olabilir.
- **Hiçbir karar verilmedi, hiçbir kod değişmedi.**

---

## D-091 · 2026-08-17 · ⛔ *"Davranış çöküşü"* büyük ölçüde **ölçüm aletinin eseri** olabilir

**Durum:** ölçüm (gerçek model, greedy, çevrimdışı) · **Etiket:** ⚠ **keşifsel**
· `DAU_LORA_ENABLED=0`, **kod değişmedi, sabit değişmedi** · 36 çağrı,
177.7 sn · ham `scratchpad/kw_audit.json`

### Nasıl bulundu

Yasin *"yerel model erişimi kapandı"* diye bir mail almış. Kontrol edildi:
model **15 GB diskte**, ve `HF_HUB_OFFLINE=1` altında **24 sn'de yüklenip
karar üretti** ⇒ koşumlar etkilenmiyor. (Meta'nın kapattığı **Llama API
Public Preview**, 2026-07-06; ağırlıklar değil. Biz o servisi hiç
kullanmadık.) ⭐ **Ama o testin çıktısı kusuru gösterdi.**

### ⛔ Bulgu 1 — eşleme koruma dilini `defect` sayıyor

`decision_to_outcome` **DEFECT anahtarlarını en önce** sınıyor
(`extraction.py:100`), ve `"take"` bir DEFECT anahtarı. Deterministik
kanıt:

| metin | sınıf |
|---|---|
| *"I need to **conserve** energy. I will **take** a short rest to recover."* | **defect 8.0** |
| *"I choose to **cooperate** and **share** what I **gathered**."* | **defect 8.0** |
| *"I will **restrain** myself and **take** only what I need."* | **defect 8.0** |

⭐ İkincisinde *"cooperate"* **birebir geçiyor** ve yine `defect` — çünkü
`"gathered"` önce sınanıyor.

### ⛔ Bulgu 2 — gerçek çıktılarda oran **yüksek**

36 çağrı, 35'i `defect`:

| | sayı |
|---|---|
| `defect` sayılan | **35 / 36** |
| bunlardan **koruma/işbirliği dili de içeren** | **31 / 35** |
| saf `defect` (yalnız DEFECT anahtarı) | **4 / 35** |
| *"take a moment / take time"* **deyimi** içeren | **30 / 35** |
| *"extract/gather **information**"* (kaynak değil) | **6 / 35** |
| ⭐ **gerçek hasat ifadesi HİÇ olmayan** | **14 / 35** |

Tetikleyen anahtarlar: **`take` 32** · `extract` 23 · `gather` 3.

Örnek: *"I will **take a moment** to assess my internal state… I will
**extract** as much **information** as possible"* → **hasat 8.0**.

### ⛔⛔ Bulgu 3 — `SYSTEM_PROMPT` sınıflandırıcının anahtarlarını **dikte ediyor**

```
"Prefer plain English words such as resource, extract, take,
 social, talk, or cooperate when those actions apply."
```

⇒ Prompt modele *"**extract** ve **take** kullan"* diyor; ikisi de **DEFECT
anahtarı** ve prompt'un listesinde **en önde**. **GAP-5 / L14'ün
(lexicon priming) somut ve ölçülmüş hâli** — artık kuramsal risk değil.

### ⇒ Neye dokunuyor

*"Olayların %94–100'ü DEFECT"* ifadesi **güvenli değil**. Ona dayanan her
okuma yeniden değerlendirilmeli:

- **D-060** `f_agent`/`fitness_class` dejenerasyonunun kök nedeni
- **D-068** davranış çöküşü
- **D-084** karar kanalı doygunluğu · **D-090** 35/36 `defect`
- **D-081/082** havuz aritmetiği — hepsi `d = 8.0`/olay varsayıyor
- ⚠ **K7** *"çöküş bir bulgudur, müdahale etme"* dedi. **Öncülü sarsıldı:**
  çöküşün bir kısmı bulgu değil **artefakt** olabilir.

⚠ **İddia sınırı:** gösterilen şey, `defect` sınıflamalarının **31/35'inin
çelişkili dil taşıdığı** ve **14/35'inde hiçbir gerçek hasat ifadesi
bulunmadığı**. *"Şu kadarı yanlış sınıflandı"* **denmiyor** — her metni
tek tek yargılamak gerekir, ve bunu bir LLM'e yaptırmak **yasak**
(2. Değiştirilemez Yasak). ⇒ Kusurun **varlığı** ve **büyüklük mertebesi**
ölçüldü; kesin oran ölçülmedi.

### Sınırlar

Sentetik prompt taraması (katman fonksiyonları gerçek, değerler benim), tek
karar bağlamı, 36 örnek. Canlı koşum metinleri `dau_runs/*.json`'da **yok**
(yalnız hash var) ⇒ geçmiş koşumlara geriye dönük uygulanamadı.
**Hiçbir karar verilmedi, hiçbir kod değişmedi.**

---

## D-092 · 2026-08-17 · Davranış eşlemesi onarıldı — **D-090'ın drift eşiği düştü, enerji havzası ayakta**

**Durum:** kod değişikliği (`53fdf04`) + iki ölçüm · **Etiket:** ⚠ ölçümler
**keşifsel** · suite `423 passed, 2 deselected` · ham
`scratchpad/sweep_d092.json` (57 çağrı, 198.3 sn) ve
`dau_runs/validate_d092_n2.json` (N=2, seed 5008–5009, `--lora`,
`run_quality = flagged`)

D-091'in açtığı blokajın kapanışı. Yasin'in 2026-08-17'de verdiği karar
(**0a**): *"Öncelik + deyim ayıklama. Prompt'a dokunulmaz."*

### 1. Ne değişti

`decision_to_outcome` artık anahtar eşlemesinden **önce** iki deseni
ayıklıyor (`dau/society/extraction.py`):

| desen | ne yakalar |
|---|---|
| `NON_HARVEST_IDIOM_RE` | *"take a moment / a short rest / some time"* — İngilizce deyim, nesnesi yok |
| `NON_COMMONS_OBJECT_RE` | *"extract as much **information**"* — nesne havuz değil |

**Dal sırası bilerek değişmedi.** İlan edilen çekim fizikseldir; yanında
duran işbirliği dili birimleri geri koymaz.

### 2. Reddedilen iki alternatif — ölçüldü, seçilmedi

D-091'in ham 36 metninde üç kural karşılaştırıldı (model çağrısı yok):

| kural | 36 metinde |
|---|---|
| bugünkü (ayıklama yok, DEFECT önce) | 35 defect / 1 coop |
| **P — ayıklama + DEFECT yine önce** ⭐ seçilen | **20 / 16** |
| C — en çok anahtar taşıyan sınıf | 6 / 30 |
| F — metinde ilk ilan edilen eylem | 6 / 28 |

Üç kural **36 metnin 17'sinde** ayrışıyor ⇒ bu bir uygulama ayrıntısı değil.
**C ve F reddedildi:** C uzun cümleyi, F açılış cümlesini ödüllendiriyor;
ikisi de hasat miktarını **retoriğe** bağlıyor ve `SYSTEM_PROMPT`'un dayattığı
kelimelere P'den daha açık.

⚠ **Yasin'in kararı *"DEFECT'in mutlak önceliği kalkar"* diyordu; P onu
kısmen koruyor.** Sapma Yasin'e sunuldu ve onaylandı (2026-08-17) — gerekçe
yukarıdaki ölçüm: kusurun kaynağı önceliğin kendisi değil **ayıklamanın
yokluğu**.

### 3. Yol üzerinde çıkan alt karar (§2.3)

İlk uygulama ifadenin **tamamını** siliyordu; *"take a short rest"*
ayıklanırken `rest` de gidiyordu ⇒ düzeltme DEFECT'i onarırken **CONSERVE
kanıtını sessizce siliyordu**. ⇒ desenler **lookahead**'e çevrildi: yalnız
**fiil** siliniyor, çevresi kalıyor. Kendi testi var
(`test_strip_removes_only_the_verb`).

### 4. Mutasyon kontrolü (§2.4) — üç mutasyon, üçü de doğru testi kırdı

| mutasyon | kırılan |
|---|---|
| ayıklama `return text` (no-op) | 3 test |
| lookahead → span (tümünü sil) | verb-only testi |
| `"resource"` nesne listesine (aşırı ayıklama) | gerçek-hasat regresyon testi |

### 5. ⭐ 0a-2 — D-090 taraması yeniden (57 çağrı)

⭐ **Önce kontrol:** 36 ızgara metni D-091'inkiyle **36/36 birebir aynı**
⇒ sınıf değişiminin **tamamı** eşlemeden geliyor, model kaymasından değil.
Determinizm üçlüsü 3/3 aynı (D-037 tutuyor).

| sonda | D-090 | **şimdi** |
|---|---|---|
| geniş ızgara | 35 defect / 1 coop | **20 / 16** |
| ortalama hasat | 7.833 | **5.333** |
| **enerji ekseni** | D C D C C C C D D D D | **birebir aynı** ✅ |
| **drift ekseni** ⭐⭐ | D D D **C C C C** | **C D C C C C C** |

⛔ **D-090'ın ⭐⭐ işaretli asıl bulgusu düştü.** *"Drift ekseninde tırtıksız,
tekdüze bir eşik — gürültü değil kaldıraç"* ifadesi **eşlemenin eseriymiş**:
metinler aynı, eski eşleme ilk üç noktayı `defect` sayıyordu, düzelince
monotonluk kalmadı (7 noktanın 6'sı `cooperate`, biri değil).

✅ **Enerji havzası (D-090 Bulgu 2) ayakta**, hem de nokta nokta aynı.

⇒ ⚠ **D kararının gerekçesinin drift yarısı zayıfladı.** *"Bedel ajanları
drift'i artırarak `cooperate` bölgesine sokar"* argümanı düşen bulguya
dayanıyordu; **enerji yarısı duruyor.**

### 6. ⭐ 0a-3 — canlı doğrulama koşumu (N=2, seed 5008–5009)

| | D-089 (5006–7, eski eşleme) | **D-092 (5008–9, yeni eşleme)** |
|---|---|---|
| gen2 `defect` (8.0) payı | **78.4 %** | **53.3 %** |
| gen2 `cooperate` (2.0) payı | 2.0 % | **30.5 %** |
| ortalama çıkarım | 6.896 | **5.951** |
| ömrün sonunda havuz ölü | **6 / 6 soy** | **5 / 6 soy** |
| `F_agent` bandı | 0.334 – 0.544 | 0.470 – 0.516 |
| `fitness_class` | 4 `normal` · 2 `low` | **6 `normal`** |
| aktarılan anı | 23 | 19 |
| landmark drift ≠ ∅ | 3 / 6 | **4 / 6** (resource 1.26–1.82) |

⭐ *"Olayların %94–100'ü DEFECT"* ifadesi **artık geçerli değil**: aynı alette,
aynı fizikte, yalnız eşleme düzeltilerek oran **%53**'e indi ve `cooperate`
sıfırdan **%30**'a çıktı.

⚠ **Ama çöküş kalkmadı, gecikti:** 6 soyun 5'inde havuz yine ölüyor. ⇒ D-081'in
*"kıtlık anı"* okuması **niteliksel olarak** ayakta; sayıları (`d = 8.0`/olay
varsayımı) yeniden hesaplanmalı.

⛔ **Ve bir bedeli var: uygunluk ayrımı daraldı.** `fitness_class` D-089'da ilk
kez iki bant birden doluyordu, şimdi **6/6 `normal`**. `F_agent` bandı
0.210 → 0.046'ya düştü. Açık madde **A** (`high` bandı boş) **kötüleşti**.
⚠ Farklı tohumlar ⇒ tohum etkisi dışlanamaz.

### 7. Neye dokunuyor

| kayıt | durum |
|---|---|
| **D-090 Bulgu 3** (drift eşiği) | ⛔ **düştü** |
| D-090 Bulgu 2 (enerji havzası) | ✅ ayakta, birebir |
| **D-068** (%94–100 defect) | ⛔ sayı geçersiz; yeni ölçüm %53 |
| **D-084** (karar kanalı doygun) | ⚠ yeniden ölçülmeli |
| **D-081 / D-082** (havuz aritmetiği) | ⚠ `d = 8.0`/olay varsayımı düştü; **yeniden hesaplanmalı** |
| **D-060** (`fitness_class` dejenerasyonu) | ⚠ kök neden okuması değişti |
| **K7** (*"çöküş bulgudur, müdahale etme"*) | ⚠ öncülü zayıfladı ama **çürümedi** — çöküş hâlâ 5/6 soyda var |

### 8. Sınırlar — ⚠ ağır

- **Farklı tohumlar.** D-089 5006–5007, bu koşum 5008–5009; her ikisi de
  **N=2**. Karşılaştırma **tohum etkisiyle karışık**, aynı tohumda A/B değil.
  ⚠ Aynı tohumda koşulamazdı: I0.7 diskteki adapter'lar yüzünden abort eder.
- Tarama **sentetik** (katman fonksiyonları gerçek, değerler benim), tek karar
  bağlamı.
- **P kuralının iki kalıntısı ilan ediliyor**, düzeltilmedi:
  *"I choose to cooperate and share what I **gathered**"* → `defect` ·
  *"I will restrain myself and **take** only what I need"* → `defect` 8.0.
  İkisi de gerçek bir hasat fiili taşıyor; eşlemede *"kısıtlı çekim"* sınıfı
  **yok**. Bir sınıf eklemek ön-kayıt konusudur, düzeltme değil.
- **0b hâlâ ertelenmiş.** `SYSTEM_PROMPT`'un *"prefer … extract, take"*
  dayatması **kaldırılmadı** (prompt'a dokunulmadı ⇒ koşumlar geçersiz olmadı).
  Artık rakam var: bu oranlar **hâlâ o prompt'un altında** alındı.

---

## D-093 · 2026-08-17 · Havuz aritmetiği yeniden hesaplandı · **`fitness_class` daralması tohum etkisiymiş** · ⭐ davranış ilk kez ortamı değiştiriyor

**Durum:** üç ölçüm (0c · 0d-1 · 0d-2) · **Etiket:** ⚠ **keşifsel, ön-kayıtlı
değil** · **kod değişmedi, sabit değişmedi** · ham
`dau_runs/validate_d093_n4.json` (N=4, seed 5010–5013, `--lora`,
`run_quality = flagged`, I4.1 replay **identical**)

D-092'nin açtığı iki ölçüm borcunun kapanışı.

### 1. 0c — havuz aritmetiği, `d = 8.0` varsayımı olmadan

D-081 ve D-082'nin bütün hesabı *"her ajan her olayda 8.0 alır"*a
dayanıyordu. Ölçülen ortalama **5.951** (D-092) / **6.402** (N=4).

| kişi başı talep | kıtlık anı | çöküş anı |
|---|---|---|
| **8.0** — D-081/082'nin varsayımı | 17 | 16 |
| 6.896 — D-089'un ölçtüğü | 21 | 20 |
| **5.951** — D-092'nin ölçtüğü | **28** | 27 |
| 4.95 — koşumdaki en düşük soy | 45 | 44 |
| **3.75 = `r·K/4`** (azami sürdürülebilir verim) | **hiç** | hiç |

⇒ **D-081'in derdi kapanmadı, büyüdü.** *"Kıtlık anı landmark'tan (10) sonra
geliyor ⇒ ölçüm anında ajanlar özdeş"* problemindeki boşluk **7 olaydan 18
olaya** çıktı.

**Ve kapasite karar tablosu kaydı.** D-081'in ilan ettiği eşitsizlik
(*"kıtlık anı < `LANDMARK_EVENT`, ve bunu sağlayan en büyük kapasite"*) aynen
korunarak yeniden çözüldü:

| talep | eşitsizliği sağlayan **en büyük** kişi başı kapasite | kıtlık anı |
|---|---|---|
| d = 8.0 (D-081'in hesabı) | **67** | 9 |
| **d = 5.951 (ölçülen)** | **50** | 9 |

⚠ **Hiçbir sabit değiştirilmedi.** Bu bir **karar girdisi** (D-007, Yasin'in);
burada yapılan yalnız D-081'in kendi eşitsizliğini yeni ölçülen talebe
uygulamaktır. Değer **etkiye bakılarak seçilmedi** (§2.7).

### 2. ⛔ 0d-1'in okuması **çürütüldü** (kendi ölçümümle)

D-092'nin N=2 koşumunda `F_agent` yayılımı 0.210 → **0.046**'ya düşmüştü.
Ayrıştırdım: girdi terimlerinin **hiçbiri** daralmamıştı (`delta_pool`
40.3 → 71.8, `t_survived` 9 → 18 **büyümüştü**), ama terimler arası
korelasyon **+0.73 → −0.97**'ye dönmüştü. **Okuma:** *"davranış çeşitlendi,
gerçek bir ödünleşme doğdu, `0.4/0.3/0.3` ağırlıkları eş-uygunluk çizgisine
oturuyor ⇒ yapısal, E4 turnuvası yazı-tura olur."*

⛔ **N=4 bunu desteklemedi:**

| | D-089 (N=2, eski eşleme) | D-092 (N=2, yeni) | **D-093 (N=4, yeni)** |
|---|---|---|---|
| `F_agent` yayılımı | 0.210 | **0.046** | **0.239** |
| `fitness_class` | 4 `normal` · 2 `low` | 6 `normal` | **10 `normal` · 2 `low`** |
| korelasyon E~S | +0.73 | **−0.97** | **−0.31** |
| korelasyon E~P | +0.27 | −0.87 | −0.33 |

⇒ **Daralma tohum etkisiymiş.** D-092'nin ilan ettiği sınır (*"farklı
tohumlar, tohum etkisi dışlanamaz"*) haklı çıktı, ve **altı soyluk bir
korelasyondan yapısal iddia çıkarmak hataydı**. Anti-korelasyon 12 soyda
**−0.31**'e iniyor: zayıf, yapısal değil.

⚠ **Açık madde A yerinde:** `high` bandı (≥0.70) **12/12'de yine boş**;
`F_agent` tavanı 0.518. Ama **iki bant birden doluyor** ⇒ turnuva için ayrım
var. `landmark_energy` tavanda **1/12** (D-085'te 5/12).

### 3. ⭐ 0d-2 — davranış oranı N=4'te doğrulandı, **ve ortamı değiştiriyor**

| | D-089 (eski eşleme) | D-092 (N=2) | **D-093 (N=4)** |
|---|---|---|---|
| gen2 `defect` (8.0) | 78.4 % | 53.3 % | **50.5 %** |
| gen2 `cooperate` (2.0) | 2.0 % | 30.5 % | **29.9 %** |
| ortalama hasat | 6.896 | 5.951 | **6.402** |
| **20 olayda havuzu çökmeyen soy** | **0 / 6** | 1 / 6 | **4 / 12** |
| aktarılan anı | 23 / 6 soy | 19 / 6 | **42 / 12**, hiç almayan **0/12** |

⭐⭐ **Asıl bulgu bu:** eski eşlemede **altı soyun altısı** havuzu öldürüyordu.
Şimdi 12 soyun **4'ü** 20 olay boyunca öldürmüyor, ve fark davranıştan
geliyor — çökmeyen soyların ortalama hasadı **4.612**, çökenlerinki **7.411**.

En temiz örnek **seed 5011 `lived` ve `null`**: olay başına **2.625**,
`cooperate` oranı **%56**, havuz sonunda **0.791** — ortak kaynak fiilen
korunmuş.

⇒ ⭐ **①'in aradığı simetri kırılması ilk kez görünüyor:** ajanlar **farklı
karar veriyor** ve bu **ortamın karnesine** yansıyor. D-084'ün
*"karar kanalı doygun, ayrım ancak Holling II gibi bir ortam kuralıyla
gelir"* öncülü **artık zorunlu değil**.

⚠ **Ama sürdürülebilir değil.** Çökmeyen soyların 4.612'si de MSY'nin (3.75)
üstünde; o talepte kıtlık **45. olaya** düşüyor, yani 20 olaylık gen2
penceresinin **dışına**. *"Havuz korunuyor"* denemez, **"pencere içinde
çökmüyor"** denir.

### 4. Neye dokunuyor

| kayıt | durum |
|---|---|
| **D-081** (kıtlık anı, kapasite tablosu) | ⚠ **sayıları geçersiz** — kıtlık 17 → 28, kapasite 67 → 50 |
| **D-082** (Holling II tablosu) | ⚠ `d = 8.0`/olay üzerine kurulu ⇒ **yeniden hesaplanmalı** |
| **D-084** (karar kanalı doygun) | ⛔ **öncülü düştü** — davranış ayrışıyor ve ortamı değiştiriyor |
| **D-092 §6'nın `fitness_class` uyarısı** | ⛔ **çürütüldü** — tohum etkisiymiş |
| Açık madde **A** (`high` bandı boş) | ⚠ **yerinde**, 12/12 |
| Açık madde **B** (`landmark_energy` doygunluğu) | ⭐ **düştü** — 1/12 |

### 5. Sınırlar

- **N=4, 12 soy, tek koşum.** Hipotez testi değil, `run_quality = flagged`.
- Çökme/çökmeme **20 olaylık gen2 penceresine** göre tanımlı; MSY hesabı
  dördünün de uzun vadede çökeceğini söylüyor.
- 0c'nin bütün tablosu **sabit talep** modeli — gerçek talep dağılımlı ve
  soydan soya değişken. Model D-081'inkiyle **aynı** tutuldu ki karşılaştırma
  anlamlı olsun.
- **Hiçbir karar verilmedi, hiçbir sabit değişmedi.**

---

## D-094 · 2026-08-17 · **P2/P3/P4 kilitlendi** ve E4 yazıldı — `w` artık değişken olabiliyor

**Durum:** üç tasarım kararı (Yasin) + kod (`374906c`) · **Etiket:** karar +
uygulama · suite **`435 passed, 2 deselected`** · ⚠ **modül henüz bağlı değil**

### 1. Yasin'in üç kararı

| # | Karar | Seçilen | Reddedilen ve neden |
|---|---|---|---|
| **P2** | Seçilim şeması | ⭐ **Turnuva, k = 2** (Goldberg & Deb 1991) | **Kesme (üst %50)**: en yakın yayımlanmış analog bunu kullanıyor (Vallinder & Hughes 2024) ama N=8'i iki nesilde tek soya indirir · **Uygunlukla orantılı**: ölçülen dar `F_agent` bandında (0.279–0.518, D-093) baskı üretmez |
| **P3** | Popülasyon boyutu | ⭐ **Sabit N + turnuva** — ölen her ajanın yerine turnuva kazananından bir varis ⇒ `w ∈ {0,1,2,…}` | **Ölüm-doğum dengesi (dalgalanan N)**: D-093'te 12 soyun **8'i** havuzu hâlâ öldürüyor ⇒ popülasyonun sıfıra inmesi gerçek risk; bütçe de öngörülemez olur |
| **P4** | Price'ın `w`'si | ⭐ **Üç katman ayrı**: `F_agent` (girdi) → `w` (varis sayısı) → `z` (landmark drift, K5) | **`F_agent` doğrudan `w`**: D-071'den beri `F_agent`'ın %30'u gerçekleşmiş hayatta kalma; aynı sayı hem üremeyi belirler hem sonuç olarak raporlanırsa Mills & Beatty totolojisi geri gelir (D-075) |

⭐ **P2'nin gerekçesi çeşitlilik değil ölçülebilirlik**, ve bu D-093'ün
sayısına dayanıyor: `F_agent` yayılımı **0.239** ölçüldü, tavanı 0.518. Orantılı
şema bu bandı baskıya çeviremez; turnuva `k` ile çevirebilir.

### 2. Ne yazıldı — `dau/generation/reproduction.py`

| parça | ne yapıyor |
|---|---|
| `tournament_winner` | k aday çekilir, `F_agent`'ı en yüksek olan kazanır. **Eşitlik `agent_id` ile kırılır** — liste sırasına bırakmak D-042'nin konum kusurunun aynısı olurdu |
| `allocate_heirs` | `n_slots` boşluğu turnuvayla doldurur, **her ebeveyni** döndürür (kazanmayanlar `w = 0`) — sıfırları düşürmek kovaryansı kazananlara doğru saptırırdı |
| `price_partition` | `Δz̄ = (1/w̄)·Cov(w,z) + (1/w̄)·E(w·Δz)`, **alan alan** |
| `reproduction_report` | geçerlilik kapısı girdileri: `F_agent` yayılımı, `Var(w)`, `w`'nin farklı değer sayısı, `selection_measurable` |

**İki ölçüm kararı açıkça ilan edildi:**

1. **Price terimleri popülasyon momentleriyle** (N bölen, N−1 değil). Bu bir
   üslup seçimi değil: ayrışma **ancak** popülasyon momentleriyle bir cebirsel
   kimlik. ⚠ Rice 2008'in *"kestirim küçük N'de yanlı"* uyarısı (D-082/§P)
   **iddia tarafında bir sınır**, bölen değiştirme gerekçesi değil.
2. **`z` vektör kalıyor**, ayrışma alan alan dönüyor. Norma indirmek
   (‖z‖, ya da tek alan seçmek) **etkiyi görüp uç nokta seçmek** olurdu ⇒ L9.

**Ve bir semantik karar:** drift bayrağı hiç yanmamış bir alan için magnitude
**0.0** sayılıyor (`DRIFT_ABSENT_MAGNITUDE`). Yokluk veri, eksik değer değil —
aksi halde o ebeveyn o alanın kovaryansından **düşerdi**.

### 3. Mutasyon kontrolü (§2.4) — dört mutasyon, dördü de doğru testi kırdı

| mutasyon | kırılan test |
|---|---|
| `w = 0` ebeveynleri sonuçtan düş | `test_allocate_heirs_keeps_the_losers` |
| kovaryansta N−1 böleni | **`test_price_identity_holds_exactly`** |
| eşitlik kırıcıyı kaldır (liste sırası kazanır) | `test_tournament_tie_breaks_on_agent_id_not_list_order` |
| `selection_measurable` her zaman `True` | `test_report_flags_the_degenerate_case` |

⭐ **Yük taşıyan test `test_price_identity_holds_exactly`:** ayrışmanın toplamı,
varislerden doğrudan hesaplanan `Δz̄` ile **birebir** eşleşmek zorunda. Bölen,
ağırlık ya da `w = 0` işlemesi kayarsa makul görünen bir sayı değil
**uyuşmazlık** çıkıyor.

### 4. ⚠ Bağlanmadı, ve bilerek

`run_cprime_multigen` bu modülü **çağırmıyor**. Sırada E1/E5 (ortak havuzu
akışların dışına al) ve E2 (N ajanı ilerleten dış döngü) var, **ikisi de
P1/P6'ya bağlı ve ikisi de karara bağlanmadı**.

⚠ **`TOURNAMENT_K` bilerek `tool_identity`'ye eklenmedi.** Koşmayan bir ayarı
raporlamak U2/D-024'ün **tersi** hatası olurdu (§2.8: rapor aleti takip etmeli).
⇒ **Borç:** E4 bağlandığı anda `TOURNAMENT_K` + `HEIRS_PER_TOURNAMENT_WIN` alet
kimliğine girer.

### 5. Bugün kapanan ve açık kalan

✅ **Linçpin teknik olarak çözüldü:** `w` değişken olabiliyor, `Cov(w,z)`
tanımlı, kimlik testle korunuyor.

⛔ **Ama hâlâ hiçbir koşum seçilim ölçmüyor** — modül bağlanana kadar. Kalan
üç karar **Yasin'in**: **P1** (kol başına ayrı havuz mu tek havuz mu) · **P6**
(iki faz korunsun mu) · **P7** (N/G/tohum zarfı, ⚠ literatür burada sayı
vermedi, D-076/§M.4).

⚠ **E2 için tasarım belgesinin uyarısı yerinde:** *"N ajanı olay bazında
ilerleten dış döngü **denetimsiz yapılmaz**"*.

---

## D-095 · 2026-08-17 · **P1 ve P6 kilitlendi** · E1/E5 denetimi: havuz fiziği zaten N'e hazır

**Durum:** iki tasarım kararı (Yasin) + read-only denetim · **Etiket:** karar +
denetim · **kod değişmedi**

### 1. Yasin'in iki kararı

| # | Karar | Seçilen | İlan edilmesi gereken bedeli |
|---|---|---|---|
| **P1** | Havuz paylaşımı | ⭐ **Kol başına ayrı havuz** | ⚠ **İzolasyon, seçilim iddiasını birey düzeyinden grup düzeyine kaydırır** (Chevin 2011). İkinci ön-kayıta **ilan edilmiş sınır** olarak yazılacak, K5'in sınırının yanına. Gerekçe: `null` kolumuz bir **referans suştur** ve ortak havuz o varsayımı yapı gereği ihlal eder — Hudgens & Halloran 2008 (SUTVA/kısmi girişim) ve Xiao vd. 2023 aynı yerde buluşuyor |
| **P6** | İki faz korunsun mu | ⭐ **Tek faz** | ⛔ **`delta_pe` uç noktası kaybolur** ⇒ S3/S4'ün ön-kayıtlı hâli yeniden yazılacak. Gerekçe: popülasyonda karşılaştırma nesiller arası (g → g+1), faz-2'nin işini bir sonraki nesil zaten görüyor; iki faz maliyeti **ikiye katlıyor** |

### 2. ⭐ E1/E5 denetimi — iş sanıldığından **küçük**

Tasarım belgesi E1/E5'i *"ortak havuzu akışların dışına al"* diye tarif ediyor.
Denetim (read-only) bunun **yarısının zaten yapılmış** olduğunu gösterdi:

| katman | N'e hazır mı |
|---|---|
| `step_pool`, `realized_extractions`, `step_pool_with_crisis` | ✅ **hazır** — üçü de **N girişli sözlük** alıyor, ve `realized_extractions` eksik kalan stoğu **talep oranında paylaştırma** kuralını zaten uyguluyor (D-066) |
| `pool_step_node` ([graph.py:1237](dau/foundation/graph.py:1237)) | ⛔ **tek ajanlı** — `{state.agent_id: amount}` diye **tek girişli** sözlük geçiyor |

⇒ Havuz **fiziği** N ajanlı; tek ajanlı olan şey **düğüm**, çünkü LangGraph
düğümü tek bir ajanın state'i üzerinde çalışıyor.

⇒ **E1/E5'in gerçek içeriği:** ajan başına yapılan defter işini (`_record_pool_event`
· metabolik kredi · `_record_body_event` · landmark satırı) N ajan üzerinde
dönen bir fonksiyona çıkarmak; `pool_step_node` o fonksiyonun **N=1 çağıranı**
olarak kalır.

### 3. ⚠ Neden burada durdum (§2.3)

Bu bir **davranış korumalı yeniden düzenleme**, ama **üretim grafiğinin
ön-kayıtlı yoluna** dokunuyor. Ve bugün (D-092) o yolun davranışı **zaten
değişti** ⇒ sessiz bir kayma, bugünün iki koşumunu (`validate_d092_n2`,
`validate_d093_n4`) karşılaştırma tabanı olarak **geçersiz kılar**.

⇒ Uygulanmadan önce Yasin'e sunuluyor, ve doğrulama şartı **şimdiden**
yazılıyor: N=1 yolu yeniden düzenlemeden **sonra** aynı env / drift / internal
state ve **aynı defter satırlarını** üretmek zorunda; testi mutasyon
kontrolünden geçecek.

---

## D-096 · 2026-08-17 · **P7-b: ilk popülasyon koşumu bir kestirim koşumudur**, hipotez testi değil

**Durum:** tasarım kararı (Yasin) · **Etiket:** karar · **kod değişmedi**

### Karar

⭐ **Seçilen: kestirim.** İlk popülasyon koşumu *"seçilim var / yok"* demeyi
hedeflemiyor; **`w` ve `z`'nin dağılımını ve Price ayrışmasının terimlerini
ölçmeyi** hedefliyor.

**Reddedilen: hipotez testi.** Gerekçe iki katmanlı:

1. `Cov(w, z)` üzerinde güç hesabı bir **etki büyüklüğü tahmini** ister.
   Elimizde yok, ve bakmak **yasak** (L9: etkiyi görüp istatistik seçmek
   post-hoc). DR #1'in S4 için yaptığı *"en küçük anlamlı etki"* işi seçilim
   terimi için **hiç yapılmadı**.
2. **GAP-9'un dersi:** N=15 *"varsayılan"* alınmıştı, güç analizi baştan
   yetersiz olduğunu söylüyordu, B2 40 tohumla koştu ve **p = 0.9914** çıktı.
   32 saatlik bir zarf, nesillere ve tohumlara bölündükten sonra seçilim terimi
   üzerinde anlamlı bir teste güç taşıması **muhtemel değil**.

Yasin'in gerekçesi: *"sonucuna göre farklı yerlere de gidebiliriz,
savunulabilir bir şeyler elde etmek daha mantıklı."*

### ⇒ Beş somut sonucu

| # | ne değişiyor |
|---|---|
| **1** | **En küçük anlamlı etki ilan etmek gerekmiyor** — türetemediğimiz bir sayıyı uydurmaktan kurtuluyoruz |
| **2** | Ön-kayıtın birincil slotu bir **test** değil bir **kestirim** olur: `Cov(w,z)`, `E(w·Δz)`, `Var(w)` + ilan edilmiş kesinlik |
| **3** | ⭐ Koşumun asıl geç/kal kapısı **geçerlilik kapısı** olur: `Var(w) > 0`. Bu **kalibre edilmiş bir eşik değil, bir tanım** ⇒ §2.7 devrede değil, ve kural koşumdan **önce** yazıldı (`reproduction_report`, D-094) |
| **4** | ⚠ **Null sonuç başarısızlık değil** — *"`Var(w)` şu, `Cov(w,z)` şu aralıkta"* raporlanabilir bir çıktıdır. Bu, *"Null/underpowered sonuç meşru bilimsel çıktıdır"* süreç kuralının doğrudan uygulaması |
| **5** | **P7-a (bütçe) basitleşti:** artık *"güç ne gerektiriyor"* değil **"ne kadarını harcayabiliriz"** sorusu. Zarf gücün değil kesinliğin fonksiyonu |

### ⚠ Kesinlik / yanlılık ödünleşmesi — kilitte açıkça yazılacak

Kestirim koşumunda üçlü şu şekilde ayrışıyor, ve üçü aynı işi yapmıyor:

| eksen | neyi belirler |
|---|---|
| **N** (nesil başına ajan) | Price kestiriminin **yanlılığı** — Rice 2008 küçük N'de yanlı olduğunu söylüyor |
| **G** (nesil) | **birikimli kalıtım iddiasının** ön koşulu, G ≥ 5 (D-014/D-074) |
| **tohum** | **kesinlik** / tekrar (Kofler & Schlötterer: *tekrar > N*, D-076) |

⚠ Bu tablo bir **karar değil, türetme çerçevesi**. Sayılar P7-a'dan
(bütçe tavanı) türetilecek ve türetme ön-kayıta yazılacak — **hiçbir pilot
verisine bakılmadan**.

### Sınır

⚠ **Bu karar iddianın kapsamını daraltıyor ve bu bilinçli.** Koşum sonunda
*"seçilim çalışıyor"* denemeyecek; denebilecek olan *"seçilim terimi ölçüldü,
şu büyüklükte, ve `w`'de şu kadar varyans vardı"*. K5'in ve P1'in sınırlarının
yanına yazılacak.

---

## D-097 · 2026-08-17 · **E1/E5 uygulandı** — havuz adımı N ajana çıktı, N=1 yolu birebir korundu

**Durum:** kod (`43b4220`) · **Etiket:** davranış korumalı yeniden düzenleme ·
suite **`441 passed, 2 deselected`** · doğrulama ham
`scratchpad/mock_before.json` + `mock_after.json` + `mock_after2.json`

D-095'in denetimi onaylanınca uygulandı.

### 1. Ne yapıldı

`advance_commons(env, [CommonsRequest, …]) → (env, {agent_id: CommonsOutcome})`
[graph.py](dau/foundation/graph.py). `pool_step_node` artık bunun **N=1
çağıranı**.

**Sıra birebir korundu** (bu yük taşıyor): yenile + yarala → **tur için bir kez**
`pool_ratio` → ajan başına defteri oku, havuz satırını yaz, metabolik krediyi
uygula, beden satırını yaz.

⭐ **`CommonsRequest.event_counter` ajanın saati, ortamın değil.** N ajan bir
merayı paylaştığında havuz **tur başına bir tik** atıyor ama her yaşam **kendi
olayını** sayıyor; satırın ortamın sayacını ödünç almaması gerekiyor. M1
mutasyonu tam bunu yakaladı.

### 2. Davranış korunumu — iki bağımsız yol

| # | yöntem | sonuç |
|---|---|---|
| **1** | Tam suite | **441 passed** (435 + 6 yeni). Mevcut testler N=1 fiziğini **zaten pinliyordu**: `pool == step_pool`, enerji kredisi, defter satırları, kriz eşiği |
| **2** | `--mock-llm`, aynı tohum (8801), refactor **öncesi ve sonrası** | üç kolda da **`arm_digest` · gen2 `pe_list` · `f_agent` · `extraction_by_event` birebir aynı** |

Kalan **19 fark** yalnızca: `wall_seconds` · `tool_identity/argv` (çıktı yolu) ·
`inherited_memory_ids`.

### 3. ⚠ Yan bulgu — anı kayıt id'leri deterministik değil

Üçüncü grup şüpheli göründüğü için ayrıca ölçüldü: **aynı kodun iki koşumu** da
farklı `inherited_memory_ids` üretiyor. Kaynak `uuid4()`
([store.py:213](dau/memory/store.py:213), `:281`).

| | |
|---|---|
| **etkilemediği** | `arm_digest` üç kolda da aynı · anı **sayısı** aynı (2/2) · hiçbir uç nokta id kullanmıyor |
| **etkilediği** | ⚠ `inherited_memory_ids` **replay karşılaştırmasında kullanılamaz** — I4.1 zaten digest üzerinden çalışıyor, ama bir okuyucu bu alanı determinizm kanıtı sanabilir |

⇒ **Bir kusur olarak açılmadı**, ilan edilmiş bir sınır olarak kaydedildi.
D-037'nin determinizm iddiası **digest üzerinden** kurulu ve o tutuyor.

### 4. Mutasyon kontrolü (§2.4) — üç mutasyon, üçü de doğru testi kırdı

| mutasyon | kırılan |
|---|---|
| ajan saati yerine havuz sayacı | **üç** satır-sayacı testi (ikisi refactor'dan önce de vardı) |
| herkesi ilk ajanın hasadıyla besle | oransal paylaştırma + kendi-hasadı testleri |
| tekrar eden `agent_id` kontrolünü kaldır | tekrar testi |

### 5. Sıradaki iş ve sınırlar

⬜ **E2 kaldı** — N ajanı olay bazında ilerleten dış döngü. ⚠ Tasarım belgesinin
uyarısı yerinde: **denetimsiz yapılmaz**. `advance_commons` onun çağıracağı
arayüz olarak hazır.

⚠ **Hâlâ hiçbir şey N ajanla koşmuyor.** Bu kayıt bir **yetenek** ekledi, bir
koşum değil: `advance_commons` N girişle test edildi ama üretim yolu hâlâ
N=1'den geçiyor.

⚠ `TOURNAMENT_K` / `HEIRS_PER_TOURNAMENT_WIN` **hâlâ `tool_identity`'de değil**
(D-094'ün borcu) — E2 bağlanınca girecek.

---

## D-098 · 2026-08-17 · **E2 adım 1**: tek olaylık graf — dış döngü artık mümkün

**Durum:** kod (`285d2fd`) · **Etiket:** yeni yetenek, üretim yolu değişmedi ·
suite **`445 passed, 2 deselected`**

E2 dört adıma bölündü ve birincisi yapıldı. ⚠ **E2 bir bütün olarak
"denetimsiz yapılmaz"** (tasarım belgesi); adım adım Yasin'in onayıyla
gidiliyor.

### 1. Neden bölündü — mimari kısıt

Üretim grafı ([graph.py](dau/foundation/graph.py) `build_graph`) döngüsünü
`pool_step_node` üzerinden **kapatıyor** ve yaşam bitene kadar kendi içinde
dönüyor (`app.stream`). Tek ajan için doğru. ⛔ **N ajan için yanlış:** mera
**tur başına bir kez** tıklamalı, her ajan için bir kez değil — yoksa aynı
turda ikinci ajan, birincinin çekilişinden **sonraki** havuzu görür ve
`realized_extractions`'ın oransal paylaştırması (D-066) hiç devreye girmez.

⇒ İki şey grafın dışına çıkmak zorunda: **havuz adımı** (E1/E5, D-097 yaptı) ve
**döngünün kendisi**.

### 2. Ne yazıldı

| parça | ne |
|---|---|
| `build_event_graph()` | `social_pre → agent → evaluator → meta → END`. Üretim çevriminin **wiring'i çıkarılmış** hâli — ikinci bir uygulama değil, aynı düğüm fonksiyonları aynı sırada |
| `step_agent_once(state, app)` | Tek ajanı **tam bir olay** ilerletir, havuza dokunmaz |

**İki tasarım ayrıntısı bilinçli:**

1. `agent_node` graf **build anında** modülden okunuyor ⇒ Protocol C'nin
   monkeypatch'i (`graph_mod.agent_node = _safe_agent`) `build_graph`'ta olduğu
   gibi çalışmaya devam ediyor.
2. `app` **dışarıdan** veriliyor. N ajan × çok tur bir döngüde grafı binlerce
   kez yeniden derlemek yerine bir kez derliyoruz; ayrıca çağrı başına build
   etmek `agent_node`'u **koşum ortasında** yeniden okurdu — D-042'nin adapter
   yolunda kovaladığı sessiz kaymanın aynısı.

### 3. ⚠ Test yazarken öğrenilen bir değişmez

Stub agent'ın `agent_decision` olayına **`energy` koyması zorunlu**: meta
gözlemci, enerji izinde **delik** olan bir satırı reddediyor
([self_model.py:186](dau/self_model.py:186) — *"F_agent cannot average a life
whose energy trace has holes"*, D-086'nın koyduğu kapı).

⇒ Stub da gerçek düğüm gibi bu değişmeze uymak zorunda. Uymasaydı test **daha
zayıf bir sözleşmeye** karşı geçerdi — §2.4'ün *"mutasyon kontrolü olmadan
repoya işe yaramaz bir bekçi girer"* uyarısının test-kurgusu hâli.

### 4. Mutasyon kontrolü (§2.4) — iki mutasyon, ikisi de doğru testi kırdı

| mutasyon | kırılan |
|---|---|
| havuz düğümü grafa geri eklendi | *"havuz düğümü yok"* + *"havuza dokunmuyor"* |
| `step_agent_once` girdiyi aynen döndürdü | *"tam bir olay ekler"* + tip kontrolü |

### 5. Kalan üç adım

| adım | ne | doğrulama şartı (şimdiden yazılı) |
|---|---|---|
| **E2-2** | `run_round`: her canlı ajanı bir olay ilerlet → `advance_commons` **bir kez** → sonuçları uygula → `should_continue` | N=2'de havuz **tur başına bir tik** atmalı |
| **E2-3** | `run_population`: turlar üzerinde yaşam döngüsü, ajan başına ölüm, anı kasası bağlama | ⭐ **N=1 bugünün yaşamıyla birebir aynı** olmalı (`--mock-llm`, `arm_digest`) |
| **E2-4** | Nesil döngüsü (G) + E4'ün `allocate_heirs`'ı + Price aletlemesi | `TOURNAMENT_K` alet kimliğine girer (D-094'ün borcu) |

⚠ **Üretim yolu bu kayıtta değişmedi.** `build_graph` ve `pool_step_node`
olduğu gibi duruyor; eklenen şey **yeni bir yetenek**, ve hiçbir koşum onu
henüz kullanmıyor.

---

## D-099 · 2026-08-17 · **E2 adım 2**: `run_round` — mera tur başına bir kez tıklıyor

**Durum:** kod (`56943af`) · **Etiket:** yeni yetenek, üretim yolu değişmedi ·
suite **`451 passed, 2 deselected`**

### 1. Ne yazıldı

`run_round(env_state, states, app) → RoundOutcome(env_state, states, alive,
granted)` [graph.py](dau/foundation/graph.py).

Bir tur: her ajan `step_agent_once` ile **bir olay** ilerler → bütün talepler
toplanır → `advance_commons` **bir kez** çağrılır → sonuçlar her ajanın
state'ine yazılır → `should_continue` kimin yaşadığına karar verir.

### 2. İki tasarım ayrımı — biri çağıranın, biri değil

⭐ **Eylem sırası bilerek çağıranın.** Sıra bir **fizik kararı** ve ilan
edilmesi gerekiyor (D-079 — Schönfisch & de Roos 1999; Fatès 2014), ve
**P0-① tam olarak bu sıra hakkında bir karar** (sıralı erişim, sıra dönerek).
Burada `sorted()` yazmak Yasin'e ait bir soruyu sessizce kapatırdı.

⛔ **Tık çağıranın değil.** Bütün talepler havuz kımıldamadan **önce**
toplanıyor. Ajan başına tıklamak, aynı turda ikinci ajanın birincinin çektiği
havuzu görmesine yol açar ve `realized_extractions`'ın oransal paylaştırması
(D-066) **hiç devreye girmez** ⇒ *"ortak havuz"* iddiası **kodda yanlış** olur
ama sonuçlarda doğru görünür.

### 3. Tekrarın kaldırılması

`commons_request_from_state` çıkarıldı: *"bu ajan ne istedi"* kuralını artık
`pool_step_node` (N=1) ve `run_round` (N) **paylaşıyor**. İki çağıranın aynı
kuralı yeniden türetmesi, §2.8'deki ölçüm/rapor çiftlerinin **dört kez**
ayrışma biçimiydi.

### 4. ⭐ Mutasyon kontrolü bir **test zayıflığı** yakaladı

İlk hâlinde iki stub ajan **aynı** kararı veriyordu. *"Havuz ajan başına
tıklasın"* mutasyonu altında sıra-bağımsızlığı testi **geçti** — çünkü simetrik
talepte sıralı çekiliş her iki sırada da aynı sayıları veriyor. ⇒ **Test tam da
yakalamak için yazıldığı mutasyona karşı boştu.**

Düzeltildi: iki ajan artık **farklı** talep ediyor (8.0 vs 2.0) ve mera **ince**
(stok 1.0, paylaştırma fiilen devreye giriyor). Test ayrıca *"mera gerçekten
kıt mı"* diye assert ediyor, yoksa kontrol yine boşa düşerdi.

| mutasyon | kırılan (düzeltmeden sonra) |
|---|---|
| havuz ajan başına tıklasın | *"tur başına bir tık"* **+ *"sıra bağımsız"*** |
| ölen ajanı süzme | bütçe testi |

⇒ **§2.4'ün kendisi hakkında bir ders:** mutasyon kontrolü *"test kırıldı mı"*
diye sorulunca yeterli değil; **hangi** testlerin kırıldığına bakmak gerekiyor.
Kırılması beklenen bir test ayakta kalıyorsa o test boştur.

### 5. Bir yan gözlem — ölüm testi neden enerjiyle kurulamadı

`should_continue` hasat **krediye yazıldıktan sonra** yargılıyor (D-066: *"eat
now, act on it next event"*). ⇒ Stoklu bir merada enerjisi **sıfır** olan bir
ajan tur içinde **canlanıyor** (`metabolic_gain(8.0) ≈ 1.0`). Boş merada ise
**ikisi de** ölüyor. ⇒ Test **olay bütçesi** yolundan kuruldu.

⚠ Bu bir kusur değil, fiziğin sonucu — ama **kayda değer**: bugünkü evrende
*"açlıktan ölmek"* ancak **havuz çöktüğünde** mümkün, bireysel kötü karardan
değil. D-093'ün *"8/12 soy havuzu öldürüyor"* ölçümüyle birlikte okunmalı.

### 6. Kalan iki adım

| adım | doğrulama şartı |
|---|---|
| **E2-3** `run_population` | ⭐ **N=1 bugünün yaşamıyla birebir** (`--mock-llm`, `arm_digest`) |
| **E2-4** nesil döngüsü + `allocate_heirs` + Price | `TOURNAMENT_K` alet kimliğine girer (D-094'ün borcu) |

⚠ **Üretim yolu bu kayıtta da değişmedi** — `pool_step_node` artık paylaşılan
yardımcıyı çağırıyor ama davranışı aynı (451 test yeşil, D-097'nin mock
karşılaştırması hâlâ geçerli).
