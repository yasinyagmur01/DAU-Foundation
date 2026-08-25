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

---

## D-100 · 2026-08-17 · **E2 adım 3**: yaşam döngüsü grafın dışına çıktı — N=1 digest'i **birebir**

**Durum:** kod (`f690b88`) · **Etiket:** yeni yetenek, üretim yolu değişmedi ·
suite **`455 passed, 2 deselected`**

### 1. Ne yazıldı

`run_population(env_state, states, app, max_rounds) → PopulationOutcome`
[graph.py](dau/foundation/graph.py). `build_graph`'ın koşullu kenarının sahip
olduğu **döngü** artık dışarıda; **yetkili durma kuralı hâlâ
`should_continue`**.

Üç tasarım kararı açıkça yazıldı:

| # | karar | gerekçe |
|---|---|---|
| **1** | `max_rounds` bir **guard**, ikinci bir bütçe değil, ve **zorunlu** | Hatalı bir `MAX_EVENTS` sonsuza dönerdi. Varsayılan vermedim: hiçbir çağıran **seçmediği** bir sayıyı miras almamalı (§2.9) |
| **2** | Guard ısırırsa `hit_round_cap = True` | Kısa bir yaşamı **tamamlanmış gibi** döndürmek, D-073'te `MODE_REPORT`'u getiren akıl yürütmenin tersi olurdu — sessiz kırpma yok |
| **3** | Ölen ajan son state'ini `states`'te **bırakıyor** | Altı turda bitmiş bir yaşam **veridir**; düşürmek onu *hiç başlamamış* bir yaşamdan ayırt edilemez yapardı |

### 2. ⭐ Doğrulama — söz verilen digest kontrolü yapıldı

D-098'de şu şart yazılmıştı: *"N=1 bugünün yaşamıyla **birebir** olmalı
(`arm_digest`)"*. Yapıldı, ve **kod yolunun içinden**, koşum sarmalayıcısına
bağlanmayı beklemeden:

Aynı doğum state'i **iki yoldan** koşuldu — (a) üretim grafının `app.stream`'i,
(b) `run_population`. Sonuç:

| karşılaştırılan | sonuç |
|---|---|
| **`arm_digest`** (= `sha256(karar dizisi ++ PE dizisi)`, D-012) | **birebir aynı** |
| havuz | aynı |
| enerji | aynı |
| tur sayısı | `MAX_EVENTS` ile aynı, `hit_round_cap = False` |

⚠ **Karşılaştırmanın boş olmadığı ayrıca ölçüldü** — bu tam olarak D-099'un
yakaladığı zayıflık sınıfı: 4 karar, 4 PE (0.856 / 0.856 / 1.000 / 1.000), ve
digest boş-dizi digest'inden farklı. İki taraf da boş dizi verse hash'ler
**zaten** eşleşirdi ve test hiçbir şey söylemezdi.

### 3. Mutasyon kontrolü (§2.4) — üç mutasyon

| mutasyon | kırılan |
|---|---|
| havuzu turlar arası ilerletme (`env` sabit) | digest testi **+** iki-ajan testi |
| `hit_round_cap` her zaman `False` | guard testi |
| `should_continue`'yu yok say (`alive` yerine hepsi) | digest testi |

### 4. Kalan tek adım — E2-4

| ne | bağlı |
|---|---|
| Nesil döngüsü (G) + E4'ün `allocate_heirs`'ı + Price aletlemesi | P7-a (bütçe) hariç hepsi karara bağlandı |
| `TOURNAMENT_K` + `HEIRS_PER_TOURNAMENT_WIN` alet kimliğine girer | **D-094'ün borcu** |
| `run_population`'ı `run_protocol_c_prime`'ın koşum sarmalayıcısına bağlamak | ⚠ anı kasası bağlama ve adapter yolu **bilerek dışarıda** tutuldu |

⚠ **`run_population` bilerek saf:** anı kasası açma/bağlama ve adapter
yaşam döngüsü içine **alınmadı**, çağıranda kalıyor. İkisi de global durum
tutuyor (`_memory_stores`, adapter diski) ve ikisi de zaten `agent_id`
anahtarlı; kopyalamak D-033'ün *"adapter'lar koşumlar arası diskte kalıyordu"*
kusurunun ikinci bir kopyasını açardı.

⚠ **Üretim yolu bu kayıtta da değişmedi.** `build_graph`, `pool_step_node` ve
`_collect_pe_events` olduğu gibi duruyor; hiçbir koşum `run_population`'ı
kullanmıyor.

---

## D-101 · 2026-08-17 · **E2-4 ikiye bölündü** · nesil defteri yazıldı — ⭐ Price **bir nesil gecikmeli** okunur

**Durum:** kapsam kararı (Claude Code) + kod (`e9d07a9`) · **Etiket:** yeni
yetenek, üretim yolu değişmedi · suite **`463 passed, 2 deselected`**

### 1. Kapsam kararı — neden bölündü

D-098 E2'yi dört adıma bölmüştü. Dördüncüsüne girerken **tek adımda iki ayrı
risk sınıfının karıştığı** görüldü:

| | ne | risk |
|---|---|---|
| **E2-4a** | nesil döngüsü defteri + Price'ın kapatılması | **saf**, test edilebilir, üretim yoluna dokunmaz |
| **E2-4b** | koşum sarmalayıcısına bağlama | ⛔ **ön-kayıtlı yola dokunuyor** ve **kasa + adapter yaşam döngüsünü N ajana açıyor** |

⚠ E2-4b, **D-033'ün** (adapter'lar koşumlar arası diskte kalıyordu ⇒ I0.7) ve
**D-067'nin** (kasa saati, faz-yerel sayaç) tam kavşağında duruyor. İkisini bir
commit'te götürmek, ikisinin hangisinin bozduğunu ayırt edilemez yapardı.

⇒ Bu kayıt **(a)**. (b) ayrı adım, ayrı onay.

### 2. ⭐ İki nesillik bağımlılık — bu katmanın var olma nedeni

Price, `Δzᵢ` için **varislerin** z'sine ihtiyaç duyuyor:

```
Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)
```

⇒ **g → g+1 geçişinin ayrışması, g'nin sonunda hesaplanamaz.** Hiçbir koşum
*bitirdiği* nesil için *"seçilim terimi"* raporlayamaz; ancak **bir nesil
gecikmeyle** raporlayabilir.

**Sonuçları:**

- G = 5 nesil ⇒ **4 geçiş** ⇒ Price ayrışması **4 kez** okunur, 5 değil.
  (P7-a'nın *"kol başı 40 epizod"* hesabı bunu **zaten** böyle sayıyordu — 10
  tohum × (G−1) = 40. Tutarlı.)
- Son nesil **hiçbir Price satırı üretmez** — varisi yok. Bütçede o nesil
  *"terim üretmeyen ama `z` sağlayan"* nesil.
- ⚠ Bunu unutan bir okuyucu **yanlış sayı çiftini** yan yana koyar. Bu yüzden
  plan sonradan `agent_id`'lerden yeniden kurulmuyor, **açık bir nesne** olarak
  tutuluyor (`GenerationPlan`).

### 3. Ne yazıldı — `dau/generation/population.py`

| parça | ne |
|---|---|
| `plan_next_generation(...)` | Bir neslin uygunluğunu, sonraki neslin **soy ağacına** çevirir. P3 gereği `n_slots` = **bütün popülasyon** (nesil = ajan başına bir yaşam, sonunda her yuva yenilenir) |
| `close_transition(plan, heir_z)` | Varisler yaşadıktan sonra geçişin Price ayrışmasını **alan alan** kapatır |
| `heir_id(parent, generation, ordinal)` | Deterministik varis kimliği |

⭐ **Varis id'sindeki sıralayıcı yük taşıyor:** iki turnuva kazanan ebeveynin
**iki ayrı** varis kimliği olmalı, ve `w` tam olarak onların sayısı. Ebeveyn
adıyla isimlendirmek ikisini **sessizce birleştirir** ve `Var(w)`'yi sıfıra
düşürür — yani katmanın var olma sebebi olan **dejenere durum** geri gelir.

### 4. Mutasyon kontrolü (§2.4) — üç mutasyon

| mutasyon | kırılan |
|---|---|
| varis id'sinden sıralayıcı kaldırıldı | **dört** test (Price kimliği dahil) |
| eksik varisi sessizce atla | eksik-varis testi |
| bütün varisleri ilk ebeveyne yaz (soy ağacı bozuk) | **Price kimlik testi** |

⚠ Üçüncüsü için plan bilerek **asimetrik `w`** ile kuruldu ve test bunu
assert ediyor (*"seed gave a flat w; pick another"*). Her ebeveyne bir varis
düşseydi yanlış gruplama da dengelenir ve test **bozuk bir soy ağacına karşı
geçerdi** — D-099'da yakalanan zayıflık sınıfının aynısı.

### 5. Kalan tek adım — E2-4b

| ne | not |
|---|---|
| `run_population` + `plan_next_generation`'ı koşum sarmalayıcısına bağla | ⚠ **ilk kez üretim yolu değişir** |
| Kasa + adapter yaşam döngüsünü N ajana aç | ⛔ D-033 / I0.7 ve D-067 tam burada |
| `TOURNAMENT_K` + `HEIRS_PER_TOURNAMENT_WIN` → `tool_identity` | **D-094'ün borcu**, bağlanma anında ödenir |
| Price satırlarını koşum çıktısına yaz | bir nesil gecikmeli, §2 |

⚠ **Öneri:** E2-4b'yi mevcut `run_cprime_multigen`'i **değiştirerek** değil,
**yeni bir sarmalayıcı** olarak yazmak. Gerekçe: multigen koşucusu gen1 → aktarım
→ gen2 şemasına ve üç kola göre kurulu; popülasyon şeması (P1: kol başına ayrı
popülasyon **ve** ayrı havuz, P6: tek faz) farklı bir iskelet. Değiştirmek
B2'nin koştuğu yolu geri dönüşsüz biçimde karıştırır. ⚠ **Karar Yasin'in.**

---

## D-102 · 2026-08-17 · **E2-4b**: popülasyon sarmalayıcısı koştu — ⭐ linçpin çalıştı · ⛔ **D-081 ile çelişki bulundu**

**Durum:** kod (`7eee33f`) + duman koşumu · **Etiket:** ⚠ **keşifsel**, hiçbir
şey ön-kayıtlı değil · suite **`471 passed, 2 deselected`** · ham
`scratchpad/pop_smoke.json`

### 1. Yasin'in kararı ve ne yazıldı

**Karar:** mevcut `run_cprime_multigen`'i **değiştirmek yerine yeni
sarmalayıcı** — `dau/diagnostics/run_population_experiment.py`. Gerekçe: o
koşucu `gen1 → aktarım → gen2` iskeletine kurulu; popülasyon şeması (P1: kol
başına ayrı popülasyon **ve** ayrı mera; P6: tek faz) o iskelete sığmıyor, ve
değiştirmek **B2'nin koştuğu yolu** `prereg/b2-code` etiketi dışında
referanssız bırakırdı.

Kol başına, nesil başına: N doğum state → `run_population` (E2-3) → `F_agent`
(`build_self_model`) → `z` = landmark drift (K5) → `plan_next_generation` (E4)
→ sonraki nesil; ve **bir nesil sonra** `close_transition` Price'ı kapatıyor.

✅ **D-094'ün borcu ödendi:** `TOURNAMENT_K` ve `HEIRS_PER_TOURNAMENT_WIN` artık
`tool_identity`'de, **sabitten okunarak** (§2.8), üç bayrakla birlikte.

⭐ **P0 tek bir fonksiyonda:** `build_arm_population` bütün kurucuları **aynı
nişe** doğuruyor = **P0 seçeneği ①**. ⚠ P0 formen hâlâ Yasin'in (Kuşak 1 / E);
②, ③ veya ⑤ seçilirse **yalnız o fonksiyon** değişir, ve bugüne kadar hiçbir
ölçüm oradan geçmedi.

### 2. ⭐ Duman koşumu — linçpin **çalıştı**

Mock LLM, N=4, G=3, 4 olay, `exit 0`. Üç kolun üçünde de:

| nesil | `w` dağılımı | `selection_measurable` |
|---|---|---|
| 1 | **[0, 0, 1, 3]** | **True** |
| 2 | **[0, 0, 2, 2]** | **True** |
| 3 | — (son nesil, varisi yok) | — |

⇒ **`Var(w) > 0` gerçek bir koşumda ilk kez oluştu.** D-076'dan beri açık olan
*"`w` sabit ⇒ `Cov(w,z)` tanımsız"* linçpini **mekanik olarak** kapandı.

### 3. ⛔ Ama bu koşumun sayılarından **bilim okunmaz** — beş sebep, hepsi kodda yazılı

| # | sebep |
|---|---|
| **1** | **Kalıtım bağlanmadı** — `transfer_to_heir` çağrılmıyor ⇒ üç kol **aynı deney**, aktarım terimi gürültü |
| **2** | **Adapter eğitimi bağlanmadı** |
| **3** | ⛔ **D-081 çelişkisi** (aşağıda) |
| **4** | **`F_agent` 4 ajanda özdeş** (0.654 ×4): P0-① + mock LLM ⇒ özdeş yaşamlar ⇒ turnuvayı **ilan edilmiş eşitlik kırıcı** (`agent_id`) belirliyor. Yani buradaki `Var(w)` **tie-break'in eseri**, uygunluk farkının değil |
| **5** | **Olay bütçesi 4 < `LANDMARK_EVENT` 10** ⇒ landmark okunamıyor, `z` boş, Price satırları **boş sözlük**. ✅ Kod **imputasyon yapmıyor**, `[LANDMARK][WARN]` basıyor — D-069/V1'in LOCF yasağı burada da tutuyor |

### 4. ⛔ Bulunan çelişki — havuz N ile ölçeklenmiyor

**D-081 (Yasin, onaylı):** *"havuz **N ile ölçeklenecek**, kişi başı
kapasite/başlangıç bugünkü sayılarda (100 / 80) ⇒ sıfır yeni sabit, ve kişi
başı yörünge N=1 evreninin birebir aynısı kalıyor."*

⛔ **Sarmalayıcı bunu yapamıyor.** `POOL_MAX` bir **modül sabiti**: `step_pool`
lojistik büyümede ona doğru büyüyor ve `get_pool_ratio` ona bölüyor. Stoğu
ölçekleyip kapasiteyi ölçeklememek oranı **1'in üstüne** çıkarır ve kriz
eşiğini bozar — daha büyük bir mera modellemez.

⇒ **Kapasiteyi `dau/society/environment.py` üzerinden geçirmek gerekiyor**, bu
bir **fizik değişikliği** ve ayrı adım. §2.11 gereği **sessizce yamanmadı**:
modül docstring'i ve `tool_identity` (`pool_capacity_scaled: False`) bunu ilan
ediyor.

⚠ **Bugünkü durumda kişi başı kapasite 100/N**, yani D-081'in tarif ettiğinden
**N kat kıt**. Duman koşumunda sonucu görünüyor: N=4'te mera **2. nesilde ölü**.

### 5. ⚠ Bu oturumda **üçüncü** boş test yakalandı

`MAX_EVENTS` testi ilk hâlinde global'i *"ne tutuyorsa"* okuyordu. Önceki
testler bütçeyi sızdırdığı için `before == bütçe` oluyor ve *"geri verme"*
mutasyonu **geçiyordu**. Ayırt edici bir sentinel (137) ile düzeltildi.

⇒ **Ders üçüncü kez tekrarlandı ve kurala dönüştürülmeli:** mutasyon kontrolü
*"bir test kırıldı mı"* diye sorulunca yetmiyor — **hangi** testin kırıldığına
bakmak gerekiyor. Global durum okuyan testler **ayırt edici sentinel** kullanmak
zorunda, yoksa test sırası testi boşaltıyor.

### 6. Sıradaki iş

| # | ne | not |
|---|---|---|
| **1** ⛔ | **Havuz kapasitesini N'e ölçekle** — `environment.py` | D-081'i geri getirir. ⚠ Fizik değişikliği, N=1 davranışı **birebir** korunmalı |
| **2** | Kasa kalıtımını bağla (`transfer_to_heir`) | ⛔ **D-067**'nin kasa saati tam burada |
| **3** | Adapter eğitimini kola göre bağla | ⛔ **D-033 / I0.7** tam burada |
| **4** | Pilot (1.3 sa) | 1–3 bitmeden anlamsız |

---

## D-103 · 2026-08-17 · **Pilot koştu** — makine çalışıyor, ⛔ **seçilim terimi yapı gereği sıfır**

**Durum:** pilot koşum (gerçek model, `--lora`) · **Etiket:** ⚠ **keşifsel** ·
ham `dau_runs/pilot_population_n8_g2.json` · tohum 9601, N=8, G=2, 30 olay ·
**~70 dk**, 998 PE olayı, `exit 0` · 32 adapter (~0.45 GB)

### 1. ✅ Makine çalışıyor — dört kanalın dördü de canlıda

| kanal | kanıt |
|---|---|
| **Seçilim mekaniği** | `w = [0,0,0,0,1,1,3,3]`, **`Var(w) = 1.500`**, `selection_measurable = True` — üç kolda da |
| **Kanal 1 (kasa)** | miras **3 → 4–6**, varislerde `retrieval_context = 3`, `generation = 1` |
| **Kanal 2 (adapter)** | `lived` ve `shuffle`'da **8/8 varis** ata ağırlıklarını aldı, `null`'da **0/8**. Eğitim: ajan başına **17 çift**, `lora_b_abs_sum_delta` **3.25–3.34** ⇒ ağırlıklar gerçekten hareket etti |
| **Havuz** | gen1 sonunda **0.706** — kapasite ölçeklemesi (D-081) N=8'de tutuyor |

⇒ D-076'dan beri açık olan linçpin **gerçek modelle** kapandı: `Cov(w,z)`
hesaplanabilir durumda ve Price ayrışması alan alan yazılıyor.

### 2. ⛔ Ama seçilim terimi **her satırda 0.0**

| kol | gen1→gen2 Price |
|---|---|
| `lived` | energy `sec=0.0` `akt=−0.544` · resource `sec=0.0` `akt=1.0` |
| `null` | energy `sec=0.0` `akt=−0.540` |
| `shuffle` | energy `sec=0.0` `akt=−0.338` |

**Sebebi ölçüldü:** gen1'in sekiz ajanı **bit düzeyinde özdeş**.

| ölçüm | sonuç |
|---|---|
| `f_agent_inputs` sekiz ajanda | **hepsi aynı** |
| landmark `z` sekiz ajanda | **hepsi aynı** (`{energy: 0.82}`) |
| `F_agent` yayılımı | **0.000** |
| ömür | **21, sekizinde de** |

⇒ `Cov(w, z)` **z'nin varyansı sıfır** olduğu için tanımı gereği 0.
⇒ Ve `w = [0,0,0,0,1,1,3,3]` **uygunluk farkının değil**, ilan edilmiş eşitlik
kırıcının (`agent_id`) ve turnuva çekilişlerinin eseri. **Seçilim gen1'de
kurgusal.**

### 3. ⛔⛔ Kök neden — **①'i eksik uyguladım**

P0-①'in tam adı *"**sıralı erişim, sıra dönerek**"*. `run_round` (D-099) ise
şunu yapıyor: bütün talepler toplanır, `realized_extractions` eksik stoğu
**talep oranında** paylaştırır. Yani **eşzamanlı erişim + orantılı bölüşüm**.

⇒ Özdeş ajanlar eşzamanlı erişimde **özdeş pay** alır ⇒ özdeş kalır, sonsuza
kadar. **①'in simetriyi kıran özelliği tam da atladığım şeydi.**

⚠ D-099'da *"tık tur başına bir kez, yoksa oransal paylaştırma devreye
girmez"* diye yazmıştım ve o **doğru**du — ama iki ayrı şeyi birbirine
bağlamışım:

| | doğru olan |
|---|---|
| **yenilenme** | tur başına **bir kez** ✅ (kalmalı) |
| **çekiliş** | ① **sıralı** olmalı: ajan *i*, *i−1*'den **artan** stoktan alır. İkinci bir yenilenme yok, yalnız hizmet sırası |

Bu ayrım korunursa hem havuz fiziği bozulmaz hem ① gerçekten uygulanır.
⚠ **Sıra bir fizik kararı** (D-079) ve `run_round` onu bilerek çağırana
bırakmıştı — kararın kendisi hâlâ Yasin'in.

### 4. ⚠ İkinci ilan edilmemiş sapma — mera nesiller arası **devrediyor**

Sarmalayıcı `env`'i nesilden nesile taşıyor. Tek soy tasarımı ise
**1A: *"gen2 taze havuz, gen1'in devam eden ortak alanı değil"*** demişti.
Pilotta sonucu görünüyor: gen2'de havuz **üç kolda da 0.000**.

⚠ Hangisinin doğru olduğu **açık bir tasarım kararı**: popülasyonda ortak
kaynağın nesiller arası devri savunulabilir (mera da miras kalır), ama 1A'nın
tersidir ve **ilan edilmeden** yapılmamalı.

### 5. ⭐ Yine de gen2'de ayrım **başladı**

| kol | gen2 `F_agent` yayılımı | gen2 ömür |
|---|---|---|
| `lived` | **0.189** | 18–22 |
| `shuffle` | 0.049 | 24 (sekizi de) |
| `null` | **0.000** | 18 (sekizi de) |

⇒ Ayrım **kalıtımdan** geliyor: `null` hiçbir şey almadığı için özdeş kalıyor,
`lived` en çok ayrışıyor. ⚠ **Tek tohum, N=8, hipotez testi değil** — ama
mekanizmanın çalıştığının ilk canlı işareti.

### 6. Maliyet ölçüldü

| | |
|---|---|
| süre | **~70 dk** (tahmin 1.3 sa — tuttu) |
| PE olayı | 998 |
| adapter | 32 × 14 MB ≈ **0.45 GB** |
| boş disk | **60 GB** (Qwen önbellekleri silindikten sonra) |

⇒ Ana koşum tahmini (10 tohum × N=8 × G=5) **~20 sa**, adapter **~11 GB**.
Zarf **doğrulandı**.

### 7. Sıradaki karar — Yasin'in

| # | soru | öneri |
|---|---|---|
| **1** ⛔ | Çekiliş **sıralı** mı olsun (①'in gerçek hâli), sıra nesil başına mı döndürülsün | ⭐ **Evet, sıralı + rotasyon.** Aksi hâlde seçilim terimi **yapı gereği** sıfır kalır ve koşum seçilim hakkında hiçbir şey söyleyemez |
| **2** | Mera nesiller arası devretsin mi, yoksa 1A gibi **taze** mi başlasın | ⚠ Karar ne olursa olsun **ilan edilmeli** |

---

## D-104 · 2026-08-17 · **P0-① tamamlandı** (sıralı + rotasyon) · **mera taze kalıyor** — ⭐ simetri kırıldı

**Durum:** kod (`860243d`) + iki karşılaştırma koşumu · **Etiket:** ⚠ **keşifsel**
· ham `dau_runs/cmp_pasture_carryover_n8_g3.json` ve
`dau_runs/cmp_pasture_fresh_n8_g3.json` · tek kol (`lived`), N=8, G=3, 30 olay,
`--lora` · varyant başına ~35 dk

### 1. D-103'ün kök nedeni giderildi

①'in tam adı *"**sıralı erişim, sıra dönerek**"*. `run_round` ise eşzamanlı
erişim + orantılı bölüşüm yapıyordu ⇒ özdeş ajanlar özdeş pay alıyor ve özdeş
kalıyordu.

`realized_extractions_sequential`: talepler **sırayla**, her biri kalandan.
⚠ **Yenilenme hâlâ tur başına bir kez** — değişen yalnız hizmet sırası.
`run_population` sırayı **tur başına** döndürüyor (yaşam içinde sabit sıra aynı
ajana her kıt olayı verirdi; Suleiman ve ark. 1996'nın ölçtüğü kalıcı avantaj).

### 2. Mera devri — **koşumdan önce ilan edilen** karar kuralıyla karşılaştırıldı

⚠ Yasin *"emin olamadım, karşılaştırabilir miyiz"* dedi. §2.7/L9 sonucu görüp
tasarım seçmeyi yasakladığı için kural **koşumdan önce** yazıldı:

**Bakılacak (üçü de aletin ölçebilirliği, sonuç değil):** (1) kaç nesil canlı
merada başlıyor · (2) `z`'de `resource` var mı / tavanda mı · (3) `z`'de varyans
var mı.
**⛔ Bakılmayacak:** `Cov(w,z)`'nin büyüklüğü · kol farkları · `F_agent`
yayılımlarının varyantlar arası karşılaştırması.
**Beraberlik:** ayrım yoksa **(b) taze** kalır (1A yürürlükte, sıfır yeni sabit).

### 3. Sonuç — (b) üçünde de önde, beraberlik kuralına gerek kalmadı

| gösterge | **(a) devreden** | **(b) taze** |
|---|---|---|
| canlı merada başlayan nesil | **1 / 3** (gen2–3: 0.000) | **3 / 3** (0.757 · 0.848 · 0.836) |
| `z`'de `resource` tavanda | gen2–3'te **8/8** | **0/8, hiçbir neslde** |
| farklı `z` sayısı (8 ajanda) | 1 · 1 · 2 | 1 · **4** · **4** |

**⇒ Karar: taze mera. 1A korunuyor.**

**Destekleyici gözlem** (karar kuralına girmedi): (a)'da gen2 ve gen3'te sekiz
ajanın **sekizi de 10. olayda** ölüyor — ölü merada açlık. (b)'de ömürler 10–30
arasında dağılıyor.

⚠ **İlan edilecek sınır:** ortak kaynak nesiller arası **birikmiyor**; bu koşum
kuşaklararası mera bozulması hakkında hiçbir şey söyleyemez. İstenirse üçüncü
ön-kayıta ayrı bir kol olarak girer — ama o zaman `z` için havuzdan **bağımsız**
bir uç nokta gerekir, çünkü (a) tam olarak bu yüzden düştü.

### 4. ⭐ Claude Code'un tahmini **yanlış çıktı** — ve bu tabloyu değiştirdi

Koşumdan önce *"(b) de muhtemelen takılır, `z` varyansı 1/8 kalır, sonra
kapasite (100 → 50) tartışılır"* demiştim. **Olmadı:** (b)'de gen2 ve gen3'te
**8 ajanda 4 farklı `z`**.

⇒ **Sıralı erişim + rotasyon + taze mera simetriyi kırıyor.** D-103'ün *"sekiz
ajan bit düzeyinde özdeş, `Cov(w,z)` yapı gereği sıfır"* tablosu **artık
geçerli değil**.
⇒ ⭐ **Kapasite sorusu (100 mü 50 mi) şimdilik zorunlu olmaktan çıktı** — D-081'in
açtığı ve 0c'nin yeniden hesapladığı karar **askıya alınabilir**, çünkü ayrım
kapasiteye dokunmadan doğuyor.

⚠ **gen1 hâlâ 1/8:** kurucular P0-① gereği özdeş doğuyor ve landmark'tan (10)
önce kıtlık ısırmıyor ⇒ **ilk geçişin seçilim terimi hâlâ sıfır**. Ayrım ikinci
nesilden başlıyor. ⇒ G'nin en az 3 olması **yapısal bir gereklilik**, tercih
değil: G=2 bir koşum yalnız sıfır terim üretir.

### 5. Karar sonrası gözlem — açıkça etiketli

Karar üç göstergeden verildikten **sonra** Price'a bakıldı:

| | seçilim terimi |
|---|---|
| (a) gen2 · gen3 | `0.0` · `0.0` |
| **(b) gen3** | **−0.201** |

⇒ **Seçilim terimi ilk kez sıfırdan farklı.** ⚠ Tek tohum, tek kol, N=8 —
**hiçbir iddia değil**; söylenen yalnızca *tanımsız/sıfır değil*. İşareti ve
büyüklüğü yorumlanmıyor.

### 6. Sıradaki iş

| # | ne |
|---|---|
| 1 | ⛔ **G ≥ 3** ön-kayıta yapısal gereklilik olarak yazılır (gen1 sıfır terim üretir) |
| 2 | Üç kollu tam pilot (taze mera, sıralı erişim) — kol farkı ilk kez anlamlı olur |
| 3 | İkinci ön-kayıt taslağı: okuma kuralları, ilan edilmiş sınırlar, P7-a bütçesi |

---

## D-105 · 2026-08-17 · **A1: kapılar sarmalayıcıya bağlandı** — ⭐ üç sessiz kusur yakalandı (biri **testlerin yarısını mock'a çeviriyormuş**)

**Ne yapıldı:** `run_population_experiment` bugüne kadar **sıfır** preflight
kapısıyla koşuyordu; multigen koşucusunda dokuz yerde geçen aynı sistem burada
hiç yoktu. Bağlananlar: **faz 0 = I0.3 · I0.6 · I0.7** (ABORT, GPU işinden
önce), **I1.1** (koşum sonrası, ABORT), ve sonuç JSON'una **`invariants` +
`invariant_details` + `run_quality`** bloğu.

Commit: kod+test `[A1]`, sızıntı düzeltmesi `[TEST]`.

### 1. Neden en kritik iş buydu

D-102'de **3A tersine çevrildi**: varis artık ebeveynin adapter dizinini
**kopyalıyor**. ⇒ diskte kalmış bir adapter D-033 günündeki gibi **bir yaşamı**
kirletmiyor, **bir soyu kuruyor** — ve kirlenme yönü hipotez lehine
(`lived` koşumlar arası eğitim biriktirir, `null` hiç biriktirmez).

### 2. Ne bağlanmadı, ve neden — sessizce atlanmadı

| kapı | durum |
|---|---|
| **I0.4** (tohum ajan id'sinden türetilebiliyor mu) | ⛔ **bağlanamaz.** `AGENT_ID_SEED_PATTERN` = `-(\d+)(-g\d+)?$`; popülasyon id'si `pop-{arm}-s{seed}-a{index}` ve varis id'si `…-g{n}-h{k}` **eşleşmiyor** ⇒ bağlansa **her** koşum abort ederdi. ⚠ Kalan borç: bu kapı popülasyon yolunda **yok**, ikinci ön-kayıta girer |
| **I0.1 / I0.2** (alet kimliği tam · LoRA seçimi ilan edilmiş) | ⏸ **kapsam dışı bırakıldı**, A1'in tanımı dört kapıydı. Ucuzlar; ikinci ön-kayıt öncesi eklenebilir |

### 3. ⭐ Üç sessiz kusur — kapılar bağlanınca ortaya çıktılar

**(a) Varislerin I0.7'si yokmuş.** Varis id'leri turnuvadan çıkıyor ⇒ faz 0
**yalnız kurucuları** temizleyebiliyor. `inherit_adapter` diski kontrol
ediyordu ama **ebeveyn kontrolünden sonra** ⇒ ebeveyni hiç eğitilmeyen tek kol,
yani **`null`**, eski bir koşumun ağırlıklarıyla doğabilirdi. Sıra ters
çevrildi. ⚠ Boş dizin **kasten** geçiriliyor: `dau_runs/adapters` altındaki
114 dizinin 79'u boş ve hiçbiri yüklenmiyor; onları reddetmek üç saatlik bir
koşumu sahte alarmla düşürürdü.

**(b) ⭐⭐ `DAU_MOCK_LLM=1` süreç boyunca sızıyormuş.**
`test_mock_llm_flag_installs_the_canned_llm` `main()` üzerinden bu değişkeni
`os.environ`'a yazıyor ve **kimse geri almıyordu** ⇒ o testten **sonra** koşan
her test sessizce **mock koşum** sayılıyordu. A1'e kadar görünmezdi; `run_quality`
bağlanınca damga `mock` döndü ve **I1.1 ABORT'tan FLAG'e düştü** — yani kapı
kendini kapatıyordu.

**(c) `DAU_LLM_BACKEND=groq` de sızıyormuş.** `monkeypatch.delenv` **var
olmayan** bir değişken için geri alma kaydı tutmuyor; `install_mock_llm`'in
`setdefault`'u onu sonra yaratıyor. İki test bunu bırakıyordu, ve backend groq
olunca **I0.7 "uygulanamaz"a** düşüyor (disk yolu yalnız local). Sonuç: kapı
sırf test sırası yüzünden kapanabiliyordu.

⇒ (b) ve (c) **A1'in kendi ürünü değil**, A1'in ortaya çıkardığı şeyler. İkisi
de kaynağında düzeltildi (§2.11: sessizce birini seçme).

### 4. Mutasyon kontrolü (§2.4) — beş mutasyon, beşi de **doğru testi** kırdı

| mutasyon | kırılan test |
|---|---|
| I0.7 kapısı silindi | `test_a_stale_founder_adapter_aborts_before_any_life_runs` |
| faz 0'dan sonraki `enforce()` silindi | aynı test — ⭐ ve **yalnız o**: I0.3 testi geçmeye devam etti, çünkü ikinci `enforce()` yine abort ediyor. Ayırt eden şey *"koşum başlamadan önce"* iddiası (`lives == []`) |
| I1.1 (faz 2) silindi | üç I1.1 testi |
| `inherit_adapter` sırası eskiye alındı | `…refuses_a_stale_heir_even_with_no_parent_adapter` |
| `**gate.block()` sonuca yazılmadı | `test_results_carry_the_invariant_block…` |

### 5. Bilerek alınan sertlik — ve bedeli

I1.1 **ABORT** (mock'ta FLAG), multigen ile aynı. Popülasyon yolunda
**çeşitlilik kapısı yok** ⇒ `gated` hiç işaretlenmiyor ⇒ hayatı hiç kullanılabilir
tercih çifti üretmeyen **tek** ajan bütün koşumu düşürür.
⚠ Gevşek alternatif (çift sayısına bakıp muaf tutmak) **kasten reddedildi**:
kapının kendi belgesi *"kapılanmış kol ile sessizce başarısız olan kol aynı
sıfırı raporlar"* diyor — muafiyeti sayıdan türetmek kapıyı kapatmak olurdu.
⚠ Ölçülmüş taban: D-103/D-104 koşumlarında çift sayısı **7–20**, ve eğitilen
**her** ajan `lora_B`'yi oynatmış ⇒ risk gerçek ama bugüne kadar hiç gerçekleşmedi.

⚠ Abort sonrası **JSON yazılmıyor** — 20 saatlik ana koşumda bu, koşumun
kaybı demektir. Multigen'in sözleşmesi bu ve **değiştirilmedi**; farklı bir
politika (ör. `*.aborted.json`) istenirse **ayrı bir karardır**.

### 6. Kanıt

- Suite **502 passed** (önce 493; +9 yeni test), çalışma ağacı temiz.
- Duman koşumu (mock, `--no-lora`, tohum 9801): PYTHONHASHSEED **yokken**
  `Preflight ABORT — results will not be written: I0.3` ve **dosya yazılmadı**;
  `PYTHONHASHSEED=0` ile `run_quality=mock`, blok
  `I0.3=True · I0.6=True · I0.7=None (backend local değil) · I1.1=None (LoRA kapalı)`.
  ⭐ `None` ile `True`'nun ayrı tutulması burada görülüyor: koşamayan kapı
  **geçmiş sayılmıyor**.

---

## D-106 · 2026-08-17 · **A2: I4.1 replay popülasyona bağlandı** — ⭐ iki nesil **bit düzeyinde** tekrarlandı, ilk `clean` popülasyon koşumu

**Ne yapıldı:** popülasyon koşucusu artık her **nesil** için bir `arm_digest`
üretiyor ve koşumun sonunda `lived` kolunu **ikinci kez** koşup digest'leri
karşılaştırıyor (`I4.1`, ABORT; mock'ta FLAG).

### 1. Neden gerekliydi

Tek geçişin içinde her ajan **bir kez** eğitiliyor ⇒ koşum kendi determinizmi
hakkında hiçbir şey söyleyemez. D-037'de aynı tohum + aynı kod iki koşumda
**farklı adapter** ve 21/50 karar farkı üretmişti, ve **diğer bütün kapılar
yeşil kalmıştı**. Bunu gören tek şey ikinci bir geçiştir.

### 2. Üç tasarım kararı, üçü de türetildi

| karar | gerekçe |
|---|---|
| digest **nesil** başına | ayrışma **okunabilir** olsun: 1. nesli tutup 2. neslde ayrılan bir replay, kaymanın **miras alınan adapter'da** olduğunu söyler. Kol başına tek digest yalnız *"bir yerde"* derdi |
| replay **kendi kol etiketiyle** (`pop-replay-…`) | aynı id'lerle koşsa ilk geçişin yazdığı adapter'ları yükler ⇒ 1. nesil **çıplak yerine adapte** koşar ve digest determinizmle ilgisi olmayan bir sebeple ayrışır. Multigen'in `replay_agent_id`'siyle aynı gerekçe. ⇒ replay kurucuları **I0.7'nin listesine** de eklendi |
| derinlik `REPLAY_GENERATIONS = 2` | ⭐ **türetildi, seçilmedi:** kurucular adapter'sız doğar ⇒ 1. neslin kararları taban politikadan gelir ⇒ tek başına replay edilmesi **aranan kusuru göremez**. Eğitilmiş ağırlığa bağlı ilk nesil, varisin adapter'ı miras aldığı **2. nesildir** ⇒ 2, kusuru görebilen **en küçük** derinlik |

Replay **en son** koşuyor (hiçbir kol onun bıraktığı adapter'ı tüketmesin), ve
replay kolunun ajanları **I1.1'e de giriyor** — iki geçiş de hiçbir şey
eğitmediyse digest'ler **yanlış sebeple** eşleşirdi.

### 3. ⭐ Canlı doğrulama — tohum **9802**, N=2, G=2, 12 olay, `--lora`, ~13 dk

| | sonuç |
|---|---|
| **I4.1** | ⭐ **identical** — iki neslin ikisi de bit düzeyinde aynı |
| `run_quality` | ⭐ **clean** — popülasyon yolunda **ilk kez** |
| kapılar | I0.3 ✅ · I0.6 ✅ · I0.7 ✅ (*"8 agent start from the base policy"*) · I1.1 ✅ (*"12 train arms moved lora_B; null arms unread"*) · I4.1 ✅ |

⭐ **Beklenmeyen ama doğrulayıcı iki gözlem:**

| gözlem | ne anlama geliyor |
|---|---|
| **gen1 digest'i DÖRT kolda da özdeş** (`f4490e0091dc`) | kollar yalnız **2. nesilden** ayrışıyor ⇒ kurucular gerçekten aynı fizikte koşuyor ve kol farkı **yalnız Kanal 2'den** geliyor. Bu, aletin doğru bağlandığının bağımsız kanıtı |
| gen2: `lived` = `21547bc4` · `null` = `ec5e3c12` · `shuffle` = `a33c8d36` · **`replay` = `21547bc4`** | üç kol ayrışıyor **ve** replay `lived`'i birebir tekrarlıyor ⇒ ayrım gerçek, tekrar gerçek |

Ham çıktı `scratchpad/a2_replay_smoke.json` (keşifsel, **dau_runs'a
alınmadı**; N=2/G=2 duman koşumu, hiçbir bulgu taşımıyor).

### 4. Bedel — ve bunun kimin kararı olduğu

Replay bir kol × `REPLAY_GENERATIONS` nesil demek. Üç kollu G=3 bir koşumda
**+2 kol-nesli ≈ %22 ek süre** ve N × 2 ek adapter dizini.
⚠ Bunu kısmak **P7-a'nın (bütçe) konusudur ve Yasin'indir**; Claude Code
multigen'in sözleşmesini korudu (replay her koşumda var, yalnız mock'ta atlanır)
çünkü onu kapatmak *"determinizm"* iddiasını da kapatır.

### 5. Sınır

⚠ Replay **tek tohumun tek kolunu** tekrar ediyor (multigen'de de öyle). Bir
koşumun *"deterministik"* olduğu iddiası, o kolun iki geçişte aynı çıktığı
gözlemine dayanır — bütün kolların bütün tohumlarda test edildiği anlamına
**gelmez**.

---

## D-107 · 2026-08-17 · **A3: G ≥ 3 yapısal gereklilik olarak yazıldı** — iki taban ayrıldı

**Ne yapıldı:** *"kaç nesil"* sorusunun **iki ayrı tabanı** olduğu kodda ve
belgede ayrıldı, ve ikisi **farklı türde** kurallar:

| taban | değer | ne olur | kural türü |
|---|---|---|---|
| `MINIMUM_GENERATIONS_DEFINED` | **2** | G=1'de geçiş yok ⇒ Price **tanımsız** | ⛔ **hata** (`ValueError`) |
| `MINIMUM_GENERATIONS_INFORMATIVE` | **3** | G=2'de tek geçiş var, ama o geçişin seçilim terimi **yapı gereği sıfır** | ⚠ **damga** (`[WARN]` + `generations_informative: false`) |

### 1. Neden 3 — türetim, tercih değil

P0-① gereği kurucular **aynı nişe** doğuyor ve bit düzeyinde özdeşler. ⇒ 1.
nesil geçişine `z`'de **sıfır varyansla** giriyor, ve sabit bir `z` üzerinde
`Cov(w, z)` turnuva ne yaparsa yapsın **sıfırdır** — *"küçük"* değil,
*"tespit edemedik"* değil, **tanım gereği sıfır**.

⭐ D-104 bunu **ölçtü**: gen1'de 8 ajanda **1** farklı `z`, gen2 ve gen3'te **4**.

⇒ G=2 bir koşumun **tek** geçişi, yalnızca sıfır raporlayabilen geçiştir.
**G ≥ 3 tasarımın yapısal gereğidir**, güç ya da bütçe tercihi değil ⇒ ⛔
**P7-a (bütçe) bunu kesemez.** Bütçe kesme sırası zaten *tohum* idi (§B3).

### 2. Neden hata değil de damga — ve bu bir taviz değil

G=2 **iyi tanımlı** (Price hesaplanıyor) ve duman koşumunun istediği şey tam
olarak o; A2'nin replay'i de `REPLAY_GENERATIONS = 2` ile koşuyor. Hata yapmak
kendi doğrulama aletimizi kapatırdı.

⚠ Ama sessiz de bırakılmadı (§2.9): **yalnızca sıfır raporlayabilen bir koşum,
sıfır ölçmüş bir koşum gibi okunamaz.** Konsola `[WARN]` basılıyor **ve**
sonuç JSON'una `generations_informative: false` yazılıyor — ikincisi
bilerek: bir ay sonra dosyayı açan okuyucunun terminal geçmişi yok.

### 3. Mutasyon kontrolü (§2.4)

| mutasyon | kırılan test |
|---|---|
| damga her koşumda `True` | `test_two_generations_are_stamped_uninformative` |
| konsol uyarısı silindi | aynı test (`capsys` ile metni tutuyor) |

Ve `test_three_generations_are_not_stamped` ters yönü tutuyor: damga
**ayırt etmek** zorunda, her zaman basmak değil.

### 4. Sınır

⚠ Bu, G ≥ 3'ün **yeterli** olduğunu söylemiyor. Söylediği tek şey: G=2
**yetersizdir ve bunu koşumdan önce biliyoruz**. Kaç nesil gerektiği (D-076'nın
S5'i: *"kaç nesil = birikimli kalıtım"*) hâlâ ikinci ön-kaydın ve P7-a'nın
konusu; ⚠ DR #6'nın kendi içinde çelişkili olduğu yer de burasıydı (§5 G=5–10
derken §6 sentezi G=3 öneriyordu).

---

## D-108 · 2026-08-17 · ⛔ **B1'in ilk denemesi düşecekti** — I1.1 sessiz bir *yaşamı* reddediyordu, sessiz bir *aleti* değil

**Nasıl bulundu:** B1 pilotu koşarken (N=8, G=3, 30 olay, tohum 9901) log'a iki
uyarı düştü:

```
[WARN] pop-lived-s9901-a6-g2-h1: no training happened (no preference pairs)
[WARN] pop-lived-s9901-a6-g2-h2: no training happened (no preference pairs)
```

48 ajanın **ikisi** hiç kullanılabilir tercih çifti üretemedi; diğerleri **5–12**
çift üretti. Bu iki ajanın `lora_B`'si okunmadan kaldı ⇒ **I1.1 koşumun sonunda
ABORT edecekti** ⇒ JSON hiç yazılmayacak, **~1.5 saatlik pilot** ve diğer 46
ajanın verisi birlikte kaybolacaktı.

⭐ Bu tam olarak **D-105 §5'te kayda geçirdiğim risk**: *"popülasyon yolunda
çeşitlilik kapısı yok ⇒ hayatı hiç kullanılabilir çift üretmeyen tek ajan bütün
koşumu düşürür… risk gerçek ama bugüne kadar hiç gerçekleşmedi."* **İlk gerçek
pilotta gerçekleşti.**

**Karar (Yasin, koşum sırasında):** *"şimdi öldür, düzeltmeyi uygula, yeniden
koş"* ⇒ 13 dk GPU kaybedildi, ~1.3 saat kurtarıldı.

### 1. Kapı neden haksızdı — ve gerekçe ölçüm değil **taraflılık**

> Hayatı sessiz geçen bir ajan yüzünden koşumu düşürmek, **hangi koşumların
> rapor edilebileceğine bir seçilim etkisi** koyar: her ajanı zengin yaşamış
> koşumlar geçer, sessiz yaşamlı koşumlar **hiç yazılmaz**. Kapının koruduğu
> riskten daha büyük bir zarar.

Ve *"hiç çift üretmemek"* aletin arızası değil, **yaşamın özelliğidir**: kısa
ömür + düşük PE çeşitliliği + polarite filtresi ⇒ boş küme. Bu **veridir**.

### 2. ⛔ Sayıya bakarak muaf tutmak **reddedildi** — ve sebebi ölçüldü

`_train_adapter`'ın beş erken çıkışının **dördü** de sıfır çift raporluyor:

| çıkış | sıfır çift mi | muaf mı |
|---|---|---|
| LoRA env kapalı | evet | (zaten `lora_enabled=False` ile ele alınıyor) |
| `lora_update` import hatası | **evet** | ⛔ **hayır** |
| çift kurucu exception attı | **evet** | ⛔ **hayır** |
| eğitim exception attı | **evet** | ⛔ **hayır** |
| eğitici *"no preference pairs"* dedi | evet | ✅ **evet** |

⇒ Sayı bunları **ayırt etmiyor**; e4c026b'nin sahte eğitimi tam bu delikten
geri girerdi. **Sebep ayırt ediyor.**

### 3. Uygulama — saf aletleme, hesaba dokunulmadı

| ne | nerede |
|---|---|
| `TrainOutcome.reason` alanı eklendi | `run_protocol_c_prime.py` — ⚠ **kilitli yol**, ama §2.10'un izin verdiği *"hesaplamayı değiştirmeyen raporlama eklemesi"*: tek soy yolunda **hiçbir şey okumuyor** |
| beş çıkışın her birine ayırt edici sebep | aynı dosya, isimli sabitler |
| eğiticinin kendi sebebi geçirildi | `result["reason"]` → `TrainOutcome.reason` |
| `TRAIN_SKIP_NO_PAIRS` **tek yerde** | `constraints.py` (Kural 4). ⚠ Kapı artık **bu dizgi üzerinde dallanıyor**; iki dosyada iki literal, birinin yeniden yazıldığı gün **sessizce çalışmayı bırakan** bir dal demektir |
| muafiyet | `training_sections` `gated=True` yalnız o sebep için; `reason` sonuç JSON'una da yazılıyor |

### 4. ⭐ Muafiyet bir **off-switch değil**

Her ajan muaf tutulursa kapı **yine abort ediyor** — `"no ungated train arm to
check"`. Gerekçe: hiçbir şeyin eğitilmediği bir koşum Kanal 2 hakkında hiçbir
şey göstermez ve `lived`/`shuffle`/`null` yalnız **isimde** ayrışır.
⚠ Bu davranış **tasarlanmadı, keşfedildi**: testi *"bütün ajanlar muaf"* biçiminde
yazdım, abort etti, ve **doğru cevap oydu** ⇒ ayrı bir testle sabitlendi.

### 5. ⚠⚠ Mutasyon kontrolü **ilk turda iki mutasyonu kaçırdı** — ve sebebi öğretici

| mutasyon | ilk tur | sebebi |
|---|---|---|
| muafiyet **sayıya** bağlandı | ⛔ **kaçtı** | test popülasyonunun **hepsi** aynı sonucu döndürüyordu ⇒ kapı zaten *"hiç eğitilmiş kol yok"* diye abort ediyordu ⇒ test **yanlış sebeple** geçiyordu |
| muafiyet **her sebebe** açıldı | ⛔ **kaçtı** | aynı |

⇒ Test **karışık popülasyona** çevrildi (bir ajan bozuk, diğerleri sağlıklı).
Şimdi dört mutasyonun dördü de yakalanıyor.
⭐ **§2.4'ün asıl dersi bir kez daha:** *"bir test kırıldı mı"* değil, **hangi
testin, hangi sebeple** kırıldığı. Bu oturumda ikinci kez oldu (ilki A1'de
`enforce()` mutasyonuydu).

### 6. Kanıt ve sınırlar

- Suite **538 passed** (önce 529; +9 test).
- ⚠ **Tohum 9901 yeniden kullanıldı.** Düşen denemeden **görülen tek şey** alet
  sağlığıydı: çift sayıları (5–12 ve iki kez 0) ve uyarı satırları. **Hiçbir uç
  nokta görülmedi** — `z` yok, Price yok, kol karşılaştırması yok, JSON hiç
  yazılmadı. Aynı tohumla devam etmenin **lehine** bir gerekçe de var:
  düzeltmenin, onu doğuran senaryonun **tam üstünde** sınanması.
- Düşen denemenin adapter'ları (24 dizin) **silindi**, yoksa I0.7 yeniden
  koşumu abort ederdi.
- ⚠ **Kalan borç:** *"kaç ajan çift üretemedi"* artık sonuç dosyasında
  görünüyor ama **hiçbir kapı bunu sınırlamıyor**. Yarısı çift üretemeyen bir
  koşum bugün `clean` damgası alır. Eşik **kalibre edilmemiş** olurdu (§2.7)
  ⇒ ikinci ön-kayıta gider.

---

## D-109 · 2026-08-18 · **B1 koştu** — ⭐ makine `clean`, ⛔ **uç nokta dejenere**: `z` sekiz ajanda tek değer

**Koşum:** tohum 9901 · N=8 · G=3 · 30 olay · `--lora` · taze mera · üç kol +
replay · **~1 sa 15 dk** · `dau_runs/b1_pilot_n8_g3.json` ·
rapor `dau_runs/b1_pilot_n8_g3_report.md` (analiz aracıyla, D-107 sonrası).
⚠ **Keşifsel** — hipotez testi değil (P7-b/D-096).

⚠ Üçüncü deneme. Birincisi **I1.1'den düşecekti** (D-108), ikincisi **elektrik
kesintisi** (bilgisayar kapandı). ⇒ **C1 için ders:** koşum sonuna kadar hiçbir
şey diske yazmıyor; 20 saatlik ana koşumda bu kabul edilemez. **Checkpoint
önerisi Yasin'e sunuldu, karar bekliyor.**

### 1. ✅ Seviye 0 — makine tarafı geçti

| | |
|---|---|
| `run_quality` | **clean** |
| kapılar | I0.3 ✅ I0.6 ✅ I0.7 ✅ **I1.1 ✅** I4.1 ✅ |
| **I4.1** | ⭐ **identical**, iki nesil bit düzeyinde |
| `Var(w)` | **1.00 – 1.75**, `w ∈ {0,1,2,3}` her kolda ⇒ **linçpin çalışıyor** |
| **D-108 muafiyeti** | ⭐ **canlıda çalıştı**: üç ajan *"no preference pairs"* ile muaf tutuldu, koşum **düşmedi** ve 48 adapter yazıldı |

⭐ **Süreçler arası determinizmin dördüncü teyidi:** düşen deneme, elektrik
kesilen deneme ve bu koşum — üçünde de **aynı iki ajan** (`…-a6-g2-h1/h2`) çift
üretemedi ve ilk çift sayıları birebir aynı çıktı.

### 2. ⛔ Ama seviye 0'ın ikinci yarısı **kapalı** — ve bu her şeyi belirliyor

| ölçüm | değer | anlamı |
|---|---|---|
| **farklı `z` sayısı** | **8 ajanda 1** (yalnız `shuffle` gen3'te 3) | ⛔ `z`'nin varyansı **sıfır** |
| `z`'nin kendisi | **`{}`** — 24 kol-neslinin 23'ünde | landmark'ta **hiç drift bayrağı yok** ⇒ gerçek bir sıfır okuması |
| `F_agent` yayılımı gen1 | **0.0000** (üç kolda da) | turnuva **yazı-tura**; `Var(w)` rastgelelikten geldi, uygunluktan değil |

⇒ **D-104'ün *"8 ajanda 4 farklı `z`"* bulgusu bu tohumda TEKRARLANMADI.**
⚠ Bu, D-104'ü çürütmüyor — farklı tohum, ve orası da tek tohumdu. Söylediği
şey: **simetri kırılması tohuma bağlı ve güvenilir değil.**
⭐ Bu projede coşkuyla yazılan bulguların ikinci ölçümü sağ atlatmama deseninin
**dördüncü** örneği (D-090, D-092, D-059'dan sonra).

### 3. Seviye 1 / 2 / 3 — dördü de boş, ve **sebebi ölçüldü**

| seviye | sonuç |
|---|---|
| **1 — seçilim** | Altı geçişin **beşinde** Price partition'ı **boş** (`z` hiç alan taşımıyor). Altıncısında (`shuffle` gen3, `energy`) **`selection = +0.000000`**. ⇒ `Cov(w,z)` **yapı gereği sıfır**: sabit bir `z` üzerinde kovaryans tanım gereği sıfırdır |
| **2 — birikim** | `shuffle`/`energy`: gen2 `0.0` → gen3 `0.0`. Yok |
| **3 — kol farkı** | gen1 ve gen2'de **üç mesafe de 0.000000**. gen3'te `‖lived−null‖ = 0.000` · `‖lived−shuffle‖ = ‖null−shuffle‖ = 0.2585` ⇒ ⚠ **ters yön**: hareket eden kol **kontrol** (`shuffle`), ve deney kolu eğitilmemiş kolla **özdeş** |

⚠ **Tek tohum ⇒ seviye 1 iddiası zaten mümkün değildi** (işaretin tohumlar
arası tutarlılığı sorulamıyor). Rapor bunu sayının yanına basıyor.

### 4. ⭐⭐ Uç noktanın **görmediği** şey — ve bu bulgunun asıl değeri

Ömürler (ortalama, parantez içi aralık):

| kol | gen1 | gen2 | gen3 |
|---|---|---|---|
| `lived` | 10.0 (10–10) | **17.0 (10–30)** | **24.8 (23–30)** |
| `shuffle` | 10.0 (10–10) | **17.8 (10–30)** | **28.2 (22–30)** |
| **`null`** | 10.0 (10–10) | **11.0 (11–11)** | **10.0 (10–10)** |

⇒ **Eğitilen kollar kontrolün 2–3 katı yaşıyor**, ve ömürleri **yayılıyor**;
`null` 10–11'de **düz** kalıyor. Kol digest'leri gen2'den itibaren **3/3
farklı**. `F_agent` `lived`'de nesiller boyunca **0.41 → 0.51–0.68 → 0.65–0.69**
yükseliyor.

⇒ **Kanal 2 büyük bir etki yapıyor, ama seçilen uç nokta (landmark drift) buna
kör** — çünkü `z` herkeste boş.

⚠ **`lived` ile `shuffle` arasında fark yok** (17.0 vs 17.8 · 24.8 vs 28.2, ve
`shuffle` **daha uzun**). ⇒ Uzayan ömür *"doğru"* adapter'dan değil,
**adapter'ın varlığından** geliyor. **B2'nin deseninin birebir tekrarı**
(D-053: *"`shuffle` de aynı ölçüde değiştiriyor"*).

### 5. ⛔ Şimdi yapılmayacak şey — ve neden

**Uç noktayı ömre çevirmek YASAK.** Ömrün hareket ettiğini **gördükten sonra**
onu uç nokta yapmak, L9'un tam olarak yasakladığı post-hoc seçimdir — ve bu
projede aynı hata D-044'te (yörünge uç noktası) bilerek reddedilmişti.
⇒ Ömür gözlemi **ikinci ön-kayıta girdi olarak** taşınır; oraya **koşumdan önce**
yazılır ve **taze tohumla** sınanır.

### 6. Bundan sonrası için ölçülmüş girdiler

| soru | bu koşumun verdiği sayı |
|---|---|
| kaç ajan çift üretemez | **43'ün 3'ü (%7)**, hepsi 2.–3. nesil |
| bir pilotun maliyeti | N=8·G=3·30 olay·üç kol + replay = **~1 sa 15 dk**, 48 adapter (~670 MB) |
| replay'in payı | 64 eğitimin 16'sı ⇒ **~%25** |
| `z`'nin çalışma noktası | bu nişte **tamamen boş** — landmark'ta travma bayrağı yok |

⚠ **En kritik açık soru artık uç nokta:** `z = landmark drift` (K5) bu evrende
**ölçülebilir bir şey üretmiyor**. Bunun üç olası sebebi var (travma hiç
tetiklenmiyor · landmark çok erken · drift bayrağı çok seyrek) ve **hiçbiri bu
koşumdan ayırt edilemez**. Bu bir **tasarım kararıdır (D-007) ve Yasin'indir.**

---

## D-110 · 2026-08-18 · **DR #9 mutabakata bağlandı** (§Q) — ⭐ ilk sıfır-kimlik-hatalı tur · uç nokta değişikliği **meşru** çıktı

**Brief:** *"Ön-kayıtlı birincil uç nokta pilotta ölçülemez çıkarsa, post-hoc
seçim yapmadan nasıl değiştirilir."* Dört soru. Ham cevap sohbette geldi,
mutabakat `docs/research/RECONCILIATION.md` **§Q**.

⚠ **Kanal değişti:** Gemini DR çalışmadığı için **ChatGPT Deep Research**.
⭐ Ve bu iş için **daha iyi çalıştı** — aşağıdaki sicile bak.

### 1. ⭐ Kaynak sicili: **5/5 kimlik doğru, alıntılar kaynakta**

Bu kanalda **ilk kez sıfır kimlik hatası** (önceki turlarda toplam **12** hata
çıkmıştı, ve D-076'da *"doğru kimlik, yanlış iddia"* diye yeni bir kusur türü
bulunmuştu). Beş DOI/arXiv kimliği Crossref'ten teyit edildi, ve **Evans ile
Harris'in alıntıları kaynakta birebir bulundu**.

⇒ **Üç turdur eklenen üç şartın üçü de meyve verdi:** DOI (D-065) · birebir
alıntı (D-080) · kaynakça + boşluk ilanı (D-082). ⭐ DR **kendi boşluğunu ilan
etti** (*"Harris 'positive control' terimini kullanmıyor"*) ve teyit edildi.

⚠ Kimlik hatası **değil** ama kayda geçer: Harris ve ark. beş yazarlı (biri
atlanmış) · McGrath & Burke'ün *"2024"*ü **v4 tarihi**, yayın yılı değil.

### 2. ⛔ En önemli sonuç: **soruyu ben yanlış çerçevelemişim**

Evans'ın kuralı *"koşum sürerken uç nokta değiştirmek"* hakkında. **Biz koşum
ortasında değiliz:**

- kilitli ön-kayıt (`befd72b4ee57`) **tek soy** çalışmasınındı ⇒ **bitti, null
  raporlandı** (`B2_RESULTS.md`)
- ikinci ön-kayıt **taslak**, altında hiç doğrulayıcı veri toplanmadı
- B1 bir **pilot** — JSON'un ilk alanı: `"exploratory, not pre-registered"`

⇒ ⭐ **Pilottan uç nokta seçmek post-hoc değildir; pilotun görevinin ta
kendisidir.** Meşru olmayan tek şey, **kilitlendikten sonra** oynatmaktır.
⭐ Ve Evans'ın soyut şartının (*"veriden bağımsızlık"*) bizdeki operasyonel
karşılığı **zaten var**: §6'nın tohum yakma politikası.

⇒ **D-109'un *"uç nokta kararı"* maddesi bu yüzden bir engel değil, normal bir
tasarım adımı.** Değişmeyen tek şart: yeni uç nokta **taze tohumla** ve
**kilitten önce** yazılır.

### 3. ⭐ Kodda bulunan gerçek boşluk — alet değil, **evren**

Harris'in pozitif kontrol fikri kodda arandı:

| düzey | durum |
|---|---|
| **birim** | ✅ **var** — `test_drift.py` 0.69'da drift yazılmadığını, **0.70'te yazıldığını** tutuyor; `test_cprime_multigen` okuyucunun `z` ürettiğini tutuyor |
| **sistem** | ⛔ **yok** — hiçbir koşum, canlı bir ajanın **10. olaydan önce 0.7 eşiğini geçtiğini** düzenli olarak göstermedi |

⇒ **Alet çalışıyor, evren o girdiyi üretmiyor.** D-109'da *"uç nokta bozuk"*
diye okunabilecek ifade bununla daraltılıyor.

### 4. P7-a yeniden tanımlandı — **saat değil kesinlik** (Haynes ve ark.)

Ölçülen: landmark'ta `z` dolu olan **ajan-nesli 3/72 = %4.2**.
`n = z²p(1−p)/h²` ile:

| yarı-genişlik | ajan-nesli | B1 hızında |
|---|---|---|
| ±0.05 | 61 | ~1.1 sa |
| ±0.03 | 170 | ~3.0 sa |
| ±0.02 | 383 | ~6.7 sa |

⇒ P7-a'nın sorusu artık *"kaç saat"* değil ***"olay oranını hangi kesinlikle
bilmek istiyoruz"***.
⚠ **Yalnız ORANI kestirir** — kollar arası farkı görmek kat kat fazlasını ister.
⚠ Wald aralığı küçük p'de zayıf; kesinleşirse **Wilson/tam aralık** kullanılmalı.

### 5. ⏸ Alınmayan: **Dienes'in eşdeğerlik testi**

*"Anlamsızlık ≠ etki yok"* bizde **zaten ilan edilmiş sınır** (§11'in
*"ölçemedik"* ≠ *"etki yok"* ayrımı, L9/L10) ⇒ literatür **yeni bir şey
eklemedi, var olanı doğruladı**.

⛔ TOST/Bayes faktörünü **benimsemek iki kapalı kararı açar**:
1. **P7-b** — *"ilk koşum kestirimdir, hipotez testi değildir"* (D-096). Analiz
   aracı kasten **hiç p-değeri üretmiyor** ve bunu bir test bekçiliği tutuyor.
2. **En küçük anlamlı etki** önceden isimlendirilmeli — **DR #1'in (S4) hâlâ
   cevaplanmamış sorusu**, ve §2.7 kalibre edilmemiş eşik seçmeyi yasaklıyor.

⇒ **Karar Yasin'in.** Bugün alınmadı.

### 6. Süreç dersi

⚠ **Şart listesi kusuru engellemiyor, yakalanabilir kılıyor.** 3 numaralı
iddia (Harris'in construct validity'sini *"pozitif kontrol"*e genellemesi)
şartların hepsini geçti; onu yakalayan şey **kodun kendisi** oldu (§2.2:
belgeye değil dosyaya güven).

---

## D-114 · 2026-08-18 · **Headroom koşumu** — ⛔ abort **doğruydu**, ⭐ checkpoint kurtardı, ⭐⭐ oran **tohuma bağlı: %0 ile %36 arası**

**Koşum:** tohum 9902·9903·9904 · N=8 · G=3 · 30 olay · üç kol + replay ·
**~5 sa 20 dk** · ilan edilmiş amacı **seviye 0**: travma eşiğini geçme oranı.
Ham veri `dau_runs/headroom_n8_g3_s3.json.partial.json` ⚠ **checkpoint dosyası,
sonuç değil** — hiçbir kapı üzerinden geçmedi.

### 1. ⛔ Koşum I1.1'den abort etti — ve **abort doğruydu**

```
I1.1: 2 train arm(s) never had lora_B read:
  seed=9903/g2/pop-shuffle-s9903-a1-g2-h1
  seed=9904/g3/pop-shuffle-s9904-a7-g2-h1-g3-h3
```

Sebep **"no preference pairs" değil**: `train failed: CUDA out of memory`.
⇒ Bu **sessiz bir yaşam değil, sessiz bir alet** — tam olarak D-108'in muaf
tutmayı **reddettiği** durum.

⭐⭐ **D-108'in tasarımı üretimde kendini kanıtladı.** Muafiyeti *sayıya*
bağlasaydım (reddettiğim kolay sürüm), bu iki OOM hatası **sıfır çift
raporladığı için** muaf tutulur, koşum `clean` damgalanır ve **hiç eğitilmemiş
iki ajanla** rapor edilirdi. Muafiyet **sebebe** bağlı olduğu için tuttu.

### 2. ⭐ D-111 beş saatlik koşumu kurtardı

Abort JSON yazmadı — **ama checkpoint diskte:** 301 KB, **9 kolun 9'u**,
216 yaşamın 216'sı. Dün gece aynı olay ~5 saatlik GPU'yu buharlaştırırdı
(D-108 ve elektrik kesintisi bunu iki kez yapmıştı).

### 3. Ölçüm — ilan edilmiş amaç

| | değer |
|---|---|
| ölçülen yaşam | **216/216** (hedeflenen örneklem tam) |
| eşiği geçen | **32/216 = %14.8** · %95 **Wilson** [%10.7, %20.2] |
| ulaşılan yarı-genişlik | **±0.047** ⚠ hedef **±0.03** idi — tutmadı |
| en yüksek magnitude | min 0.339 · **medyan 0.606** · max 0.820 |

### 4. ⭐⭐ Asıl bulgu: **havuzlanmış sayı yanıltıcı** — tohumlar ortak bir orana sahip değil

| tohum | geçen / yaşam | oran | %95 Wilson |
|---|---|---|---|
| 9902 | 6/72 | **%8.3** | [3.9, 17.0] |
| 9903 | 26/72 | **%36.1** | [26.0, 47.7] |
| **9904** | **0/72** | **%0.0** | [0.0, 5.1] |
| *(B1: 9901)* | *3/72* | *%4.2* | — |

⇒ **Oran %0 ile %36 arasında değişiyor**, ve aralıkları **örtüşmüyor**
(9903 ile 9904). Havuzlanmış %14.8 **ortak bir p varsayıyor ve o varsayım
tutmuyor** ⇒ tek sayı olarak **kullanılamaz**.

⇒ ⛔ **Uç nokta kararı için asıl sonuç bu:** `z`'nin **ölçülebilirliği tasarımın
değil, tohumun nişinin özelliği**. Bir nişte 72 yaşamda **hiç** ateşlenmiyor.
Bu, kollar arası karşılaştırmayı tohumlar arasında **yapısal olarak eşitsiz**
kılar — ve seviye 1'in *"işaret tohumlar arası tutarlı"* şartı, `z`'nin hiç
değişmediği bir tohumda **sorulamaz bile**.

⚠ **D-109'un *"uç nokta dejenere"* okuması da, ara sonuçtaki *"dört kat
yüksek, A'yı işaret ediyor"* okumam da eksikti.** Doğrusu: **uç nokta bazı
nişlerde çalışıyor, bazılarında hiç çalışmıyor.** ⇒ Bu projede tek tohumla
yazılan bulgunun düşmesinin **beşinci** örneği, ve bu kez düşen **kendi iki
okumam**.

### 5. Yan gözlemler — iddia değil

- **Tepe magnitude'lar kuantize:** 0.6002 ×24 · 0.6071 ×24 · 0.82 ×24 · 0.621
  ×12. **24 = 8 ajan × 3 nesil**, yani **bir kolun bütün ajanları bütün
  nesillerde aynı tepe değerini** görüyor ⇒ ajanlar tepe olayında **ayrışmıyor**.
- **`null` kolu da eşiği geçiyor** ⇒ geçmek eğitimin eseri değil.

### 6. ⛔ C1 için gerçek engel: **GPU belleği**

280 OOM uyarısı, **2'si ölümcül**. Log boyunca dağılım düz (dilim başına
0–52), **artan değil** ⇒ sızıntı değil, **kronik bellek baskısı**: 8 GB'lık
kartta 4-bit Llama 8B + LoRA eğitimi tavana yakın çalışıyor.

⇒ 20 saatlik ana koşumda bu **kesin** vurur. En güvenli kaldıraç, hatanın
kendi önerisi: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` —
**tahsis edici davranışını** değiştirir, **hesabı değil**.
⚠ `DPO_BATCH_SIZE` / `DPO_MAX_SEQUENCE_TOKENS` düşürmek de bellek kazandırır
ama **ön-kayıtlı sabitlerdir** ve eğitimi değiştirir ⇒ D-kaydı + Yasin onayı.

### 7. Disiplin notu (§7)

Koşum sürerken **ara sonuca bakıldı** (120 yaşamda %18.3). Kayda geçiyor.
**N değiştirilmedi**, koşum ne durduruldu ne uzatıldı.

---

## D-115 · 2026-08-18 · ⛔⛔ **D-114 düzeltiliyor** — `z`'yi yazan **iki** yol var, aletim yalnız **birini** ölçüyordu · ⭐ mekanizma **sıfır GPU** ile bulundu

**Nasıl bulundu:** Yasin *"tekrar koşmadan bilimsel olarak bulgularımızı nasıl
inceliyoruz"* diye sordu. Mevcut veri **yeniden ölçülmeden ayrıştırıldı** (yedi
analiz, hiç GPU harcanmadı) ve dördüncüsü bir **iç çelişki** verdi:

> tohum 9904'te **hiçbir yaşam** travma eşiğini geçmemiş, ama **72/72 ajanın
> `z`'si dolu**.

Aletim doğru niceliği okusaydı bu **imkânsızdı**.

### 1. ⛔ Kök neden: drift'i yazan iki yol, biri günlüğe hiç girmiyor

| yol | nerede | tetik | PE günlüğüne yazıyor mu |
|---|---|---|---|
| **bireysel şaşırma** | `graph.py:1190` | ajanın kendi `DeltaRecord`'u, `magnitude ≥ 0.7` | ✅ evet — D-112 bunu görüyor |
| ⛔ **ortak havuz krizi** | `environment.py:252` | `pool_ratio < POOL_CRISIS_THRESHOLD = 0.30` ⇒ `dummy_delta`, `magnitude × CRISIS_TRAUMA_MULTIPLIER = 2.5`, alan **`resource`** | ❌ **hayır** — `update_drift`'i doğrudan çağırıyor |

⇒ **D-112'nin *"travma eşiğine mesafe"* profili yalnız bireysel kanalı
ölçüyor.** §2.8'in tam olarak uyardığı hata: *"rapor aleti takip etmeli, aleti
tekrar etmemeli"* — ben `delta_magnitude`'ı PE günlüğünden okuyup onun
`update_drift`'in gördüğü şeyle **aynı** olduğunu varsaydım; ikinci yolda değil.

### 2. ⭐⭐ Mekanizma — tohum farklılığının tamamı bununla açıklanıyor

| tohum | havuz oranı (nesil sonu) | kriz? | `z`'nin kaynağı | eşik geçişi (bireysel) | `z` dolu |
|---|---|---|---|---|---|
| **9903** | 0.729 · 0.743 · 0.761 | ⛔ **hiç** (hep > 0.30) | **bireysel** (`energy`) | **26/72** | 48/72 |
| **9902** | 0.238 · 0.000 · 0.353 | ✅ kısmen | **karışık**: 48 `resource` + 8 `energy` | 6/72 | 48/72 |
| **9904** | 0.000 · 0.000 · 0.000 | ✅ **her nesilde** | **yalnız kriz** (`resource`) | **0/72** | **72/72** |
| *(9901/B1)* | — | — | `energy` ×3 | 3/72 | 3/72 |

⇒ ⭐ **D-114'ün *"oran %0–%36, uç noktanın ölçülebilirliği tohuma bağlı"*
cümlesi YANLIŞ.** `z` üç tohumun **üçünde de** ajanların çoğunda **dolu**.
Değişen şey ölçülebilirlik değil, **hangi kanalın onu doldurduğu**.

### 3. ⭐ Asıl tasarım sonucu — ve bu bir öncekinden daha ciddi

Kriz **kolun tamamına aynı anda** vuruyor ⇒ sekiz ajan **aynı** drift'i alıyor:

| nesil-hücresi | farklı `z` / 8 ajan |
|---|---|
| 9904 (yalnız kriz) | **1 · 2 · 2** |
| 9902 (karışık) | **1 · 2 · 3** |
| **9903 (yalnız bireysel)** | **1 · 3 · 5** |

⇒ **`z` yalnız BİREYSEL kanal sürdüğünde ajanlar arası varyans taşıyor.**
Kriz sürdüğünde `Cov(w, z)` yine sıfıra gidiyor — ama *"hiçbir şey olmadı"*
diye değil, ***"herkese aynı şey oldu"*** diye. İki sıfırın sebebi **zıt**, ve
sonuç dosyasından ayırt edilemiyorlardı.

⚠ **Bu, P0-①'in altını oyuyor:** ortak havuz, ajanları ayrıştırması beklenen
mekanizmanın (kıtlık) kendisi — ama kıtlık **kriz eşiğini** geçtiğinde
uç noktayı **eşitliyor**.

### 4. Çürütülen okumalar — üçü de benim

| ne demiştim | ne çıktı |
|---|---|
| D-109: *"uç nokta dejenere"* | ⛔ hayır — B1'in tohumunda **iki kanal da** sessizdi, uç nokta değil |
| Ara rapor: *"oran dört kat yüksek, A'yı işaret ediyor"* | ⛔ farklı kanalı sayıyordum |
| D-114: *"ölçülebilirlik tohuma bağlı, %0–%36"* | ⛔ ölçülebilirlik değil, **kanal kimliği** değişiyor |
| Ara rapor: *"uzun yaşam = daha çok geçiş fırsatı"* | ⛔ **ölçüldü, tutmadı**: geçenlerin ömrü 20.4, geçmeyenlerin 20.1 |

### 5. Kalan borç

1. ⛔ **D-112 eksik:** kriz yolunun büyüklüğü **hiçbir yere yazılmıyor**.
   `environment.py`'deki `crisis_magnitude` de günlüğe girmeli — saf raporlama
   (§2.10), ama **yapılmadı**, Yasin'in sırasını bekliyor.
2. ⚠ `headroom_n8_g3_s3.json.partial.json` **kapısız**, ve bu kayıttaki bütün
   sayılar oradan geliyor ⇒ **hiçbiri ön-kayıtlı sonuç değil**.
3. ⚠ **n = 4 tohum.** Niş parametreleriyle (`social_pressure` 0.516 ↔ en yüksek
   oran) ilişki **gözlem**, iddia değil; dört noktadan parametre seçmek tam
   olarak §2.7'nin yasakladığı şey olur.

---

## D-116 · 2026-08-18 · ✅ **OOM düzeltmesi uygulandı** — `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, ve tahsis ediciye ulaştığı **ölçüldü**

**Yetki:** Yasin **onayladı** (2026-08-18, CLAUDE.md §1 ⏭ tablosu madde 2).
D-114'ün bulgusunun tek açık işi buydu: 280 OOM uyarısı, **2'si ölümcül**,
dağılım log boyunca **düz** ⇒ sızıntı değil **kronik bellek baskısı**.

### 1. Ne değişti

| yer | ne |
|---|---|
| `dau/foundation/local_llm.py` | `apply_cuda_allocator_config()` + `describe_cuda_allocator()` + sabitler |
| `dau/diagnostics/run_population_experiment.py` | `main()` en başta çağırıyor, seçilen değeri konsola basıyor |
| `dau/diagnostics/tool_identity.py` | `cuda_allocator` bloğu |

⚠ **`run_cprime_multigen.py`'ye dokunulmadı** — B2'nin yolu olarak duruyor.

### 2. ⭐ Neden bir "kurulum satırı" değil de üç sonuçlu bir kapı

`apply_cuda_allocator_config()` üç şeyden **birini** yapar, dördüncüsü yok:

1. değer yoksa **kurar**;
2. operatör **aynı** değeri vermişse kabul eder;
3. aksi hâlde **süreci durdurur** — ve iki ayrı sebeple:
   - ⛔ **farklı bir operatör değerini sessizce ezmez** (§2.11: iki kaynak
     çelişiyorsa seçen ben olmam);
   - ⛔ **CUDA başlamışsa yazmaz.** PyTorch bu değişkeni tahsis edici
     açılırken **bir kez** okur. Sonradan yazmak `os.environ`'da **başarılı
     olur**, tahsis edicide **hiçbir şey yapmaz**, ve `tool_identity`
     (os.environ'ı okuyor) kosumun **hiç sahip olmadığı** bir düzeltmeyi ilan
     ederdi. **GAP-15'in hata biçimi**, sıcaklık yerine bellekte.

### 3. ⭐ Ölçüldü — varsayılmadı (keşifsel, tek atış, GPU)

⚠ Bu kaydın en önemli maddesi: *"env değişkenini süreç içinde set etmek
işe yarar"* bir **varsayımdı** ve §2.8 tam olarak bunu yasaklıyor.

| koşul | tahsis edilen segment `is_expandable` |
|---|---|
| bizim `apply_cuda_allocator_config()` yolumuz | ⭐ **True** |
| değişken hiç verilmeden (negatif kontrol) | **False** |

⇒ **Süreç içinde kurmak tahsis ediciye gerçekten ulaşıyor.** `torch 2.13.0+cu130`.
⚠ İlk sondam **yanlış alan adını** okudu (`is_expandable_segment`) ve **her
üç kolda da `False`** verdi — yani *"çalışmıyor"* diye okunabilirdi. Alan adı
snapshot'tan **doğrulanınca** tablo yukarıdaki hâlini aldı. Bu, §2.2'nin
(*"hafızaya değil dosyaya güven"*) bir kez daha çalıştığı yer.

Ayrıca ölçüldü: koşucu **import edildikten sonra**
`torch.cuda.is_initialized()` **False** ⇒ `main()` gerçekten tahsis ediciden
önce koşuyor, yani kapının 3. şıkkı üretimde ateşlenmiyor.

### 4. Mutasyon kontrolü — beş mutasyon, beşi de **doğru** testi kırdı (§2.4)

| mutasyon | kırılan test |
|---|---|
| `os.environ[...] = ...` silindi | `test_allocator_config_is_applied_before_the_gpu` |
| rapor sabitten üretildi (§2.8 ihlali) | `test_tool_identity_reports_the_allocator_from_the_environment` |
| çakışan operatör değeri sessizce ezildi | `test_allocator_config_refuses_to_overwrite_a_different_value` |
| CUDA açıkken yine de yazıldı | `test_allocator_config_refuses_once_cuda_is_up` |
| **`main()`'deki çağrı silindi** | `test_main_applies_the_allocator_setting` |

⛔ **Sonuncusu ilk hâlinde HİÇBİR şeyi kırmadı.** Fonksiyon repoda vardı,
koşum yolunda yoktu — *"düzeltme kod tabanında var, koşumda yok"*. Bekçi
sonradan yazıldı ve kırılması doğrulandı. **Bu oturumun dördüncü boş testi**
olacaktı (§1'in 5. uyarısı).

### 5. Test oturumu ≠ koşum süreci

Tahsis testleri `fresh_cuda_process` fixture'ı ile gerçek koşumun koşulunu
**açıkça** kuruyor: pytest oturumunda CUDA zaten başlamış oluyor (daha önceki
bir test GPU'da encode ediyor), o yüzden kapı ateşliyordu ve testler **sıraya
göre** geçip kalıyordu. Fixture ayrıca değişkeni `""` yaparak teardown'ı
monkeypatch'e bırakıyor ⇒ bir test ayarı bir sonrakine **sızdıramaz**.

### 6. Sınırlar

1. ⚠ **Tek atış, keşifsel ölçüm.** Sonda 64 MB'lık bir tahsis; **eğitim
   yükünde** OOM'un azaldığı **ölçülmedi**. Bunun kanıtı ancak bir sonraki
   gerçek koşumun OOM sayısıdır.
2. ⚠ Ayar **hesabı değiştirmiyor** ama determinizmi de **yeniden
   doğrulamadım**; I4.1 replay kapısı bir sonraki koşumda bunu zaten söyler.
3. Suite: **560 passed, 2 deselected**.

**Commit:** `244b767`.

---

## D-117 · 2026-08-18 · ✅ **D-112 tamamlandı** — krizin yazdığı büyüklük günlüğe giriyor, iki kanal **ayrı** raporlanıyor

**Yetki:** CLAUDE.md §1 ⏭ tablosu madde 1 (D-115'in açtığı iş). Saf raporlama
(§2.10): **hiçbir hesap değişmiyor**, hiçbir ön-kayıtlı nicelik kaymıyor.

### 1. Kapatılan boşluk

`z`'yi **`update_drift`** yazıyor — ama onun **iki çağırıcısı** var:

| yol | nerede | günlüğe yazıyor muydu |
|---|---|---|
| bireysel şaşırma | `graph`, PE yolu | ✅ evet (`delta_magnitude`) |
| ⛔ **ortak havuz krizi** | `environment.apply_crisis_trauma` | ❌ **hayır** |

⇒ D-112'nin *"travma eşiğine mesafe"* profili evrenin **yarısını** görüyordu.
Bedeli D-115'te ölçüldü: tohum 9904'te bireysel eşiği geçen yaşam **0/72**,
`z` dolu olan ajan **72/72**, ve profil *"hiçbir şey yaklaşmadı"* diyordu.

### 2. Ne yapıldı — dört parça

1. **`crisis_trauma_magnitude()` ayrıldı ve tek yetki oldu.**
   `apply_crisis_trauma` artık onu çağırıyor. ⚠ Kayıtçı çarpımı kendisi
   yapsaydı (`CRISIS_BASE_MAGNITUDE × CRISIS_TRAUMA_MULTIPLIER`) bu **§2.8'in
   hatası** olurdu — D-115'in cezalandırdığı hatanın aynısı.
2. **`graph._record_pool_event` `crisis_magnitude` yazıyor.** Kriz yoksa
   **`None`**, `0.0` değil: *"kimse yaralanmadı"* ile *"sıfır büyüklükte
   yaralandı"* bu evrende **zıt** iki şey.
3. **`delta_profile` iki kanalı AYRI veriyor.** Üst düzey anahtarlar
   D-112'nin tanımladığı anlamda kalıyor (**bireysel**, `channel` alanıyla
   açıkça damgalı), kriz **yanına** ekleniyor.
   ⛔ **Toplanmıyor** — ve bu maddenin gerekçesi kaydın en önemli cümlesi:
   > **Kriz kolun tamamına aynı anda vuruyor ⇒ ajanlar arası hiçbir bilgi
   > taşımıyor.** Havuzlanırsa D-115'in körlüğü **aynen geri gelir**.
4. **`analyze_population_run` raporda ikisini ayrı yazıyor**, ve D-117 öncesi
   koşumlar için *"blok YOK"* diyor. ⚠ Sıfır raporlamak D-115'in hatasının ta
   kendisiydi.

### 3. Mutasyon kontrolü — **altı** mutasyon, altısı da **doğru** testi kırdı

| mutasyon | kırılan test |
|---|---|
| kriz kanalı hiç okunmuyor | `delta_profile`'ın iki kriz testi |
| iki kanal toplanıyor | `..._keeps_the_two_channels_apart` |
| eşik sınırda ters (`>=` → `>`) | `test_recorded_crisis_magnitude_is_the_one_the_universe_scarred_with` |
| rapor krizi saymıyor | `test_the_report_names_the_channel_that_filled_z` |
| eski koşumda 0 raporlanıyor | `test_a_run_without_the_crisis_block_says_so...` |
| ⛔ **çağrı yerinde büyüklük `None`** | `test_advance_commons_logs_the_scar_the_famine_actually_wrote` |

⛔ **Sonuncusu ilk hâlinde hiçbir şeyi kırmadı** — birim testi kayıtçıyı
**doğrudan** çağırıyordu, dolayısıyla kablolamayı hiç görmüyordu. ⚠ **Bu
oturumda aynı boşluk ikinci kez çıktı** (diğeri D-116'nın `main()` çağrısı).
⇒ **Kural sertleşiyor:** bir düzeltmenin testi, düzeltmenin **çağrıldığı
yerden** geçmeli; fonksiyonu doğrudan çağıran test *"kod tabanında var"*
demeyi kanıtlar, *"koşum yolunda var"* demeyi değil.

### 4. Doğrulama ve sınırları

- Mock koşum (N=4, G=3, 40 olay, tohum 9307): kriz bloğu **sonuç dosyasında
  ve raporda** görünüyor, bireysel kanal 36/36 geçiş veriyor.
- ⚠ **Mock evrende kriz oluşmadı** — mock kararlar havuzu çökertmiyor ⇒ kriz
  yolunun uçtan uca kanıtı `advance_commons` testinde (üretim çağrı yeri),
  canlı koşumda değil.
- ⚠ **Geçmiş koşumlar geriye dönük düzelmiyor.** `headroom_n8_g3_s3` ve B1
  bu bloğu **taşımıyor**; rapor onlar için *"D-117 öncesi"* diyor.
- Suite: **569 passed, 2 deselected**.

### 5. ⇒ Uç nokta kararına etkisi (Yasin'in kararı #1)

Bu kayıt kararı **vermiyor**, ama dördüncü seçeneği (*"`z`'yi yalnız bireysel
kanaldan oku"*) artık **ölçülebilir** kılıyor: bir sonraki koşum, `z`'nin
hangi kanaldan geldiğini **koşum sırasında** raporlayacak. ⚠ Uç noktanın
kendisi **değişmedi** — değişmesi ön-kayıt kararıdır (L9).

**Commit:** `85b70fa`.

---

## D-118 · 2026-08-18 · ✅ **I0.4 bağlandı** — D-105'in ilan ettiği borç ödendi

**Neden borçtu:** `check_seed_derivation` Protocol C′'nin **sonda** tohum arayan
desenini (`AGENT_ID_SEED_PATTERN`) içine gömülü tutuyordu. Popülasyon id'si
`pop-{arm}-s{seed}-a{index}` biçiminde ve tohum **ortada** ⇒ desen hiçbir şeyle
eşleşmiyor, kapı **her koşumu abort ederdi**. D-105 bu yüzden onu dışarıda
bıraktı ve ikinci ön-kayıta borç yazdı.

### Çözüm — kapının anlamı değişmedi, **parser çağırana bırakıldı**

| | |
|---|---|
| `check_seed_derivation(agent_ids, seeds, derive=None)` | varsayılan hâlâ C′'nin çözücüsü ⇒ **multigen yolu birebir aynı** |
| `seed_from_population_id()` | popülasyonun kendi çözücüsü; varis ekleri **sona** eklendiği için üçüncü nesil varis de aynı tohumu verir |
| fallback | ⛔ **yok** (§2.9) — okunamayan id `ValueError` |

⇒ İki koşucu **I0.4 ile aynı şeyi kastetmeye** devam ediyor, farklı id
biçimleri okuyarak (§2.8).

### ⚠ Kozmetik değil — neyi koruyor

`shuffle` kolu permutasyonunu **id'den çözülen tohumdan** çekiyor. Okunamayan
bir id koşumun **replay garantisini** götürür — **GAP-11 tam olarak buydu**, ve
popülasyonda bir yaşamı değil **bir soyu** tohumlar.

### Mutasyon kontrolü — üç mutasyon, üçü de doğru testi kırdı

| mutasyon | kırılan |
|---|---|
| kapı `run_population_phase0`'dan silindi | `test_i04_aborts_the_run_...` + değişmez bloğu testi |
| parser sessizce `0` dönüyor | `test_an_unreadable_id_raises_instead_of_defaulting` |
| paylaşılan kapı çağıranın parser'ını yok sayıyor | popülasyon testlerinin **36'sı birden** ⇒ kapı gerçekten yük taşıyor |

Suite: **573 passed, 2 deselected**. Commit: bu kaydın bir öncekinde.

---

## D-119 · 2026-08-18 · 🔍 **DR #10 gönderildi + yerel tarama önden yapıldı** — ⛔ **D seçeneği adı konmuş bir tuzağa değiyor**

**Yetki:** Yasin *"bir soralım bakalım"* (2026-08-18). Karar 1 (`z` uç noktası)
için DR turu açıldı, ve cevap beklenirken **çapraz kontrol taraması** yapıldı.

### 1. Brief

`docs/research/2026-08-18_common-shock-endpoint_PLAIN.txt` — düz ASCII,
İngilizce, 225 satır. Beş soru: **Q1** ortak şokun bileşeninden birime özgü
bileşeni ayırmanın **adı/yordamı** · **Q2** ⛔ ortak şok **müdahale-sonrası**
ise bu ayırma geçersiz mi (*bad control* / *collider*) · **Q3** ayırmak yerine
**ayrıştırma** (contextual analysis) var mı · **Q4** pilottan sonra uç nokta
yeniden tanımlamanın sınır koşulları · **Q5** *"bu uç nokta değişemezdi"*yi
sıfır kovaryans raporlamadan ilan etmenin yolu.

⚠ **Etki sorulmuyor** (L9), ve brief'te **açıkça yazıldı**: kol karşıtlığına
bakılmadı, karar verilene kadar bakılmayacak. ⚠ Kısıtlar (C1–C5) listelendi
ki DR aksiyomu ihlal eden bir şey önermesin; ihlal ederse **işaretlemesi**
isteniyor. D-110'un üç şartı (DOI · **birebir alıntı** · kaynakça + **boşluk
ilanı**) aynen tekrarlandı.

### 2. ⭐ Yerel tarama ilk iş **kendi iki hatamı** yakaladı

| verdiğim DOI | gerçekte | doğrusu |
|---|---|---|
| `10.1086/285447` | **Stevens 1992**, yükselti gradyanı (aynı dergi/yıl, **komşu numara**) | `10.1086/285438` |
| `10.1016/j.jtbi.2008.03.008` | Chattopadhyay ve ark., plankton | `10.1186/1471-2148-8-262` |

⇒ DR'yi 12 kez suçladığımız hata biçimi (*"makaleyi biliyor, künyeyi
uyduruyor"*) **bende de çıktı**. 13 kimlik Crossref'ten doğrulandı, ayrıntı
`RECONCILIATION.md` **§R**.

### 3. ⛔⛔ Bulgu — **D seçeneği ile E seçeneği arasındaki denge değişti**

Montgomery, Nyhan & Torres 2018 (`10.1111/ajps.12357`) özetinden **birebir**:

> *"…eliminating observations based on posttreatment criteria, or **subsetting
> the data based on posttreatment variables**."*

⚠ **Kriz müdahale-sonrasıdır:** ajanların kendi hasat davranışından doğuyor,
davranış adapter'dan yani **koldan** etkileniyor. ⇒ `z`'yi *"kriz kaynaklı
kısmı hariç"* diye tanımlamak (**seçenek D**) müdahale-sonrası bir ölçüte göre
uç noktayı **budamak** olabilir.

⚠ **Abartmıyorum, birebir aynı değil:** hiçbir yaşam elenmiyor, regresyona
kontrol eklenmiyor; **uç noktanın tanımı** daraltılıyor. Literatürün bu
**üçüncü** biçime ne dediği taramanın cevaplayamadığı yer — ve DR'nin **Q2**'si
tam olarak bu.

⇒ ⭐ **Seçenek E (ayrıştırma) öne geçti:** hiçbir şeyi atmıyor, iki bileşeni de
raporluyor, ve evrimsel biyolojide **yerleşik bir formu var** (Heisler &
Damuth 1987, `10.1086/284732`; Goodnight ve ark. 1992, `10.1086/285438`).
⚠ **Yön, iddia değil:** kimlikler doğrulandı; **iddiayı taşıdıkları** yalnız
ikisinde (Montgomery, Cinelli — Crossref özetleri açıkça söylüyor)
doğrulanabildi. Contextual analysis'in bizim *"hücre-ortak bileşen"*imize
uyup uymadığı **okunmadan iddia edilemez**.

### 4. Sınırlar

1. ⚠ **Sistematik derleme değil** — adaylar benim bildiklerimden çıktı.
2. ⚠ **Tam metinler okunmadı**; iddia doğrulaması iki özetle sınırlı.
3. ⚠ Karar **hâlâ Yasin'in** (D-007). Bu kayıt seçenekleri sıralıyor, seçmiyor.

---

## D-120 · 2026-08-18 · ⛔⛔ **DR #10 mutabakatı: cevap sağlam ama soru yanlış tarif edilmişti** — ve ölçüm **D seçeneğini eledi**

Mutabakat tablosu `RECONCILIATION.md` **§S**. Ham cevap sohbetten alındı.

### 1. Kaynak sicili — 5/6 temiz, **13. kimlik hatası**

❌ **Rothenberg 1971 `10.2307/1913258`** → gerçekte **Kamien & Schwartz**,
*Limit Pricing and Uncertain Entry*. Doğrusu **`10.2307/1913267`**.
⚠ Yine **komşu numara** deseni — aynı desen bu turda **bende de** çıkmıştı
(§R: `10.1086/285447` ↔ `285438`).
⛔ İki *"kaynak"* alınmadı: *"CONSORT 2025"* (konusu bu değil, künye yok) ve
*"Standard Parameter Identification Theory"* (kaynak değil, alan adı).
⚠ Wooldridge ve Lynch & Walsh **kitap** ve bölüm iddiaları doğrulanamadı ⇒
yön olarak not, **kanıt olarak alınmadı**.

### 2. ⛔⛔ Asıl bulgu: **brief'imiz sistemi yanlış tarif etti**

Brief'e *"her ajan **özdeş** bir artış alır"* yazdım. **Kod öyle demiyor**
(`drift.py:58`): artış `magnitude × exp(-current / TRAUMA_DECAY_BASE)` ⇒
**ajanın o anki drift'ine bağlı**.

| `z` öncesi | sonrası | artış |
|---|---|---|
| **0.00** | 1.0000 | **1.0000** |
| 0.20 | 1.0187 | 0.8187 |
| 1.00 | 1.3679 | 0.3679 |

Harita **monoton** (sıralama hiç tersinmiyor) ama **sıkıştırıcı** (~10.7×), ve
türev **tam `z=0`'da sıfır**.

⇒ **DR'nin Q1 cevabının tamamı** (TWFE · CWC · `c²` · CCE) *"toplamsal ve
özdeş şok"* varsayıyor ⇒ **bizde uygulanamaz**. ⚠ DR'nin suçu değil:
**girdiyi biz yazdık.** *"Brief kalitesi girdi kalitesiyle sınırlı"*
dersinin **dördüncü** örneği (D-006'dan beri).

### 3. ⭐⭐ Ölçüm seçeneği tersine çevirdi — **D en kötüsü**

27 hücre (3 tohum × 3 kol × 3 nesil), `headroom_n8_g3_s3` checkpoint'i:

| tanım | hücre içi **tek değer** |
|---|---|
| bugünkü `z` | **14 / 27** |
| ⛔ **seçenek D** (yalnız bireysel kanal) | **en az 21 / 27** |

**Sebep koddan okundu:** bireysel kanal `magnitude ≥ 0.7` ile ateşleniyor ve
landmark'tan (olay 10) **önce neredeyse hiç ateşlenmiyor** ⇒ `z_before` çoğu
ajanda **tam 0**. Kriz o sıfırları *hepsi 1.0*, D seçeneği *hepsi 0.0* yapıyor.

⇒ ⭐ **Sorun ortak şok değil, bireysel kanalın sessizliği.** Farklar **var
olduğunda** krize rağmen yaşıyor: 9904'te her nesilde kriz var, yine de bir
hücrede **4 farklı `z`**.

⚠ **D-115'in okuması daralıyor** (yanlış değil): *"herkese aynı şey oldu"*
doğru, ama sebebi krizin gücü değil, **ateşlenmeyen bireysel kanal**.

⚠ **Sınır:** D'nin yeniden kurulumu **yaklaşık** — `delta_profile` yaşamın
**tamamını**, `z` ise **olay 10'u** okuyor. Kesin olan alt sınır: bireysel
geçişi **0/8** olan hücreler D altında **tam** dejenere ⇒ **21/27**.

### 4. Alınanlar

1. ⭐ **Dejenere uç nokta ilanı** — `Var(z)=0` hücre *"sıfır seçilim ölçtük"*
   değil ***"seçilim tanımsız"*** raporlanacak (Rothenberg 1971,
   `10.2307/1913267`, düzeltilmiş künyeyle).
2. ⭐ **Pozitif kontrol özelliği** — krizden bağımsız değişen bir nicelikte
   (ör. `energy_mean_over_life`, 0.59–0.86) `Cov(w,·) ≠ 0` gösterilirse
   seçilim motorunun çalıştığı ayrıca kanıtlanır. ⚠ Koşumdan **önce** ilan
   edilir, **Lamarckçı iddia değildir**.
3. ✅ Q4'ün üç sınır koşulu ikinci ön-kayıta girdi.
4. ✅ Q2 (**içsel şoku çıkarmak = müdahale-sonrası koşullanma riski**) §R ile
   **bağımsız olarak kesişti** ⇒ D iki yoldan zayıfladı, ölçüm üçüncüsü oldu.

### 5. ⇒ Karar 1 yeniden çerçevelendi

Eski çerçeve *"krizi uç noktadan çıkaralım mı"*ydı. **Yanlış soruymuş.**
Gerçek soru: **bireysel kanal landmark'tan önce neden ateşlenmiyor, ve bu
tasarım kararıyla mı yoksa evrenin kendisiyle mi ilgili?**

Yeni seçenek kümesi (karar **Yasin'in**, D-007) sohbette sunuldu.
⚠ Hiçbiri **etkiye bakılarak** seçilmeyecek (L9); yukarıdaki bütün sayılar
**hücre içi çeşitlilik** sayıları, **kol karşıtlığı değil** — kol karşıtlığına
bakılmadı.

---

## D-121 · 2026-08-18 · ✅ **KARAR: `z` uç noktası = seçenek A** (Yasin) — koru, ve *"tanımsız"*ı *"sıfır"*dan ayır

**Yetki:** Yasin, 2026-08-18. Seçenekler D-120'nin ölçümüyle birlikte sunuldu.

### 1. Karar

**`z` bugünkü hâliyle kalır** (iki kanal birlikte, landmark'ta sabit yaşta).
Değişen şey uç nokta **değil**, onu **okuma kuralı**:

1. ⭐ **Dejenere hücre ilanı** — `Var(z) = 0` olan hücrede `Cov(w,z)` **yapı
   gereği** sıfırdır ⇒ *"sıfır seçilim ölçtük"* değil ***"seçilim tanımsız"***.
   Dayanak **Rothenberg 1971** `10.2307/1913267` (⚠ DR'nin verdiği DOI yanlıştı,
   D-120'de düzeltildi).
2. ⭐ **Pozitif kontrol** — aynı `w`, krizden **bağımsız** değişen
   `energy_mean_over_life` ile kovaryans. Taşımayan koşumda **`None`**, `0.0`
   değil. ⛔ **Uç nokta değil**; işi yalnızca *"seçilim etki etti, ölçemedik"*
   ile *"bu koşum hiçbir seçilimi ölçemezdi"*yi ayırmak.

### 2. Neden D değil A — **ölçüm, tercih değil**

| tanım | hücre içi tek değer |
|---|---|
| **A (bugünkü `z`)** | **14 / 27** |
| ⛔ **D** | **en az 21 / 27** |

Ve D'nin **nedensel** riski ayrıca vardı: kriz müdahale-sonrası ⇒ budamak
*bad control* (DR #10 Q2 + §R, **iki bağımsız yol**). ⇒ Üç ayrı gerekçe aynı
yöne baktı.

⚠ **E (ayrıştırma) reddedilmedi, işlevsiz bulundu:** hücre içi varyans sıfırken
ayrıştırma da sıfır verir; yalnız zaten çalışan 13 hücreye ek okuma katardı.
⚠ **B (landmark'ı kaydır) elendi:** `null` kolu ~10 olayda ölüyor
(B1: `lived` 24.8 · `shuffle` 28.2 · **`null` 10.0**), landmark 10'da tam bu
yüzden — kaydırmak **sansürleme** getirirdi.

### 3. Uygulama

| yer | ne |
|---|---|
| `reproduction.price_partition` | `z_variance` + `selection_estimable` (saf raporlama) |
| `reproduction.positive_control_partition` | `Cov(w, control)` + varyans + estimability |
| `Candidate.control` | isteğe bağlı alan; taşınmıyorsa `None` |
| `run_population_experiment` | kontrolü landmark bloğundan okuyor, satıra yazıyor |
| `analyze_population_run` | dejenere alanı **⛔ UNDEFINED** diye işaretliyor, kontrolü basıyor, D-121 öncesi koşum için **"YOK"** diyor |

⚠ **Eşik sabit değil, epsilon:** `Z_VARIANCE_EPSILON = 1e-12` — `z` kayan
noktaların toplamı, tam sıfır tek yol değil.

### 4. Mutasyon kontrolü — beş mutasyon, beşi doğru testi kırdı

⚠ **İkisi bilerek çağrı yerini hedefliyor** (koşucu kontrolü hesaplamıyor ·
özelliği okumuyor): bu oturumda *"kod var, koşum yolunda yok"* boşluğu
**dördüncü** kez çıktı (D-116 · D-117 · D-118 · burada), artık **önce o test
yazılıyor**.

### 5. ⇒ Karar 3 (bütçe) de çözüldü

D-110 *"olay oranını hangi kesinlikle"* demişti; D-115 sonrası *"hangi kanalın
oranı"* diye açılmıştı. ⭐ **Aranan nicelik belli: bilgilendirici hücre oranı**
(bugünkü kestirim **13/27 ≈ %48**, ⚠ kapısız checkpoint'ten).

Suite: **582 passed, 2 deselected**. Commit `968c31f`.

---

## D-122 · 2026-08-18 · ✅ **Son üç slot kapandı** — ikincil YOK · bütçe 3 tohum · tohumlar 9911–9913

**Yetki:** Yasin, 2026-08-18 (*"bütçemiz senin önerdiğin kadar ama gerçekten
gerektiği kadar · ikincil uç noktalar önerinle boş · tohum politikası önerdiğin
gibi"*).

### Slot 2 — ikincil uç nokta **YOK**

⛔ Boş bırakmak **karar**, eksik değil. Tek meşru aday **ömür**dü:
`lived` 24.8 · `shuffle` 28.2 · `null` 10.0 (B1) ⇒ `lived ≈ shuffle`, yani
**Lamarckçı kanalın kanıtı olamaz**. İkincil olarak konsaydı, birincil null
çıktığında *"ama ikincilde bir şey var"* demenin yolunu açardı.
⚠ Ömür ve diğer nicelikler **betimleyici** olarak raporlanmaya devam eder.

### Slot 3 — bütçe

| | |
|---|---|
| tohum × kol × nesil | 3 × 3 × 3 |
| Price satırı | **18** (G−1 = 2 / kol / tohum) |
| beklenen bilgilendirici | **~9** (⚠ %48 kestiriminden) |
| olay bütçesi | 30 |
| beklenen süre | ~4–5.5 sa |

**Neden tam 3:** seviye 1 iddiası *"işaret tohumlar arası tutarlı"* şartına
bağlı ⇒ 3, bu şartın **sorulabildiği en küçük** sayı. Şekil B1/headroom ile
aynı olduğundan maliyet **tahmin değil ölçüm**. Ve ilk koşum zaten
**kestirimdir** (P7-b/D-096) — tohum büyütmek sınıfını değiştirmez.
⛔ **Durma kuralı:** uzatma yok, kısaltma yok; ara sonuca bakılırsa kayda geçer.

### Slot 4 — tohumlar **9911 · 9912 · 9913**

Taze blok. ⚠ **9901–9904 yanmış** (`dau_runs/adapters/` altında `pop-` dizinleri
var ⇒ I0.7 abort eder). Bugünkü mock duman koşumları (9305–9308) `--no-lora`
ile koştu, **adapter yazmadı**, ama yine de deneyde kullanılmayacak.

⇒ **Dört slotun dördü kapalı.** Sıradaki iş: **kilit**.

---

## D-123 · 2026-08-18 · ⭐⭐ **C2 KOŞULDU** — makine çalıştı, **uç nokta ölçmedi**; seviye 1 kurulamadı, seviye 3'ün deseni **teşhis edilmiş bir confound taşıyor**

**Koşum:** `dau_runs/c2_population_n8_g3_s3.json` · tohum 9911–9913 · N=8 · G=3 ·
30 olay · `--lora --fresh-pasture` · **5 sa 53 dk** · `exit 0`.
Ön-kayıt `docs/PREREGISTRATION_2.md`, kilit `72df476ebd54`.

### 1. Seviye 0 — kapı ✅ ama **V2 beş geçişte düştü**

| kapı | sonuç |
|---|---|
| `run_quality` | ✅ **clean** |
| Değişmezler | ✅ **6/6** (I0.3 · I0.4 · I0.6 · I0.7 · I1.1 · I4.1) |
| I4.1 replay | ✅ **identical** (2 nesil) |
| `complete` · `generations_informative` | ✅ true · true |
| **V1** `Var(w) > 0` | ✅ **18/18** (0.75–2.25, distinct(w) 3–4) |
| ⛔ **V2** `F_agent` yayılımı > 0 | ❌ **13/18** |

⚠ **V2'nin düştüğü beş geçişte `Var(w) > 0` ama `F_agent` yayılımı tam
sıfır** ⇒ turnuva **yazı-tura**, yani o geçişlerde ölçülen şey seçilim değil
**sürüklenme**. ⭐ V2'nin ön-kayıta yazılma sebebi tam olarak buydu; V1 tek
başına yeterli olsaydı bu beş hücre *"seçilim vardı"* diye okunacaktı.

### 2. Seviye 1 — ⛔ **KURULAMADI**

| | |
|---|---|
| Price satırı | **18** (ön-kayıtta yazıldığı gibi) |
| ⛔ **ölçülebilir** (`Var(z) > 0`) | **4 / 18 = %22** |
| ön-kayıtta ilan edilen kestirim | **~%48** ⇒ **yarısından az çıktı** |
| sıfırdan farklı ve tanımlı terim | **yalnız tohum 9911, gen3, `resource`** |

    lived +0.010873 · null +0.021746 · shuffle +0.021746

⇒ Seviye 1 iddiası *"işaret **tohumlar arası** tutarlı"* şartına bağlı ve
**tek tohum** tanımlı terim üretti ⇒ **şart sorulamıyor bile**.
⚠ Ve tanımlı üç terimin ikisi **`null` ve `shuffle`** kollarında — eğitimin
içeriğiyle ilgisi olmayan kollarda.

### 3. Seviye 2 — tanımsız (seviye 1'e bağlı)

### 4. Seviye 3 — ⚠ **desen var, ama mekanizması teşhis edildi**

⛔ **Analiz aracı burada tohumları çakıştırıyordu** (kusur B, §6) — doğru tablo:

| tohum | gen3 ‖lived−null‖ | ‖lived−shuffle‖ | ‖null−shuffle‖ |
|---|---|---|---|
| 9911 | 0.589 | 0.619 | **0.030** |
| 9912 | 0.388 | 0.196 | 0.193 |
| 9913 | 0.318 | 0.187 | 0.130 |

Üç tohumda da `lived`, kontrollerden **birbirlerine olduklarından daha uzak**.
⚠ B2'nin *"üç kol eşit uzaklıkta"* null deseni **değil**.

⛔ **Ama bu kanal iddiası olarak alınamaz, ve sebebi tahmin değil ölçüm:**
kollar **kriz maruziyetinde** ayrışıyor. Tohum 9911 gen2'de kriz olayı
`lived` 32 · `null` 69 · `shuffle` 80; gen3'te ömürler 23.6 / 30.0 / 26.1.
`z`'yi bu evrende **çoğunlukla kriz yazıyor** (216 yaşamın 144'ünde kriz,
bireysel eşik geçişi yalnız **24/216 = %11.1**, Wilson [7.6, 16.0]).

⇒ Kolların `z` farkı, **kendi meralarının ne kadar çöktüğünün** farkı olabilir
— kalıtılan iç yapının değil. **D-115/D-120 dersinin kol düzeyinde tekrarı:**
sayıya bakıp cümle kurmadan önce hangi mekanizmanın onu ürettiğini sor.

### 5. ⭐ Pozitif kontrol — **bu koşum alet null'ı DEĞİL**

`Cov(w, energy_mean_over_life)` gen3'te üç tohumda da hareket etti
(**+0.106 · +0.068 · +0.134** `lived` kollarında; bazı gen2 hücrelerinde
`Var = 0` ⇒ **UNDEFINED** damgalandı).

⇒ **Aynı `w`, değişen bir nicelikle kovaryans üretiyor.** Yani seçilim
makinesi **çalışıyor**; düz olan şey **uç nokta**. D-121'in pozitif kontrolü
ilk koşumda tam bu ayrımı yaptı.

### 6. ⛔ Üç rapor kusuru — **hiçbiri ölçülen sayıyı değiştirmiyor, ikisi okumayı değiştiriyor**

| # | kusur | etkisi |
|---|---|---|
| **A** | `RESULTS_NOTE` sonuç dosyasına *"exploratory, not pre-registered"* yazıyor — **bu koşum ön-kayıtlı** | ⚠ dosya kendi statüsü hakkında yanlış konuşuyor |
| **B** ⛔ | `level3_arm_contrast` tohumları **sessizce çakıştırıyor** (`by_generation[gen][arm] = view` ⇒ **son tohum kazanıyor**) | ⛔ üç tohumluk kol karşıtlığı **tek tohum** gibi raporlanıyordu |
| **C** | Boş partition'da *"estimability ABSENT — predates D-121"* basılıyor | ⚠ **yanlış cümle**: koşum D-121 sonrası, partition sadece boş |

⚠ **B, bu projenin tam olarak korunduğu hata sınıfı:** rapor sağlıklı
görünüyor ve başka bir şey söylüyor. Düzeltme **Yasin'in onayına** sunuldu
(kilit sonrası: saf raporlama düzeltmesi, hiçbir hesabı değiştirmiyor).

### 7. Sonuç sınıfı (ön-kayıt §11, koşumdan **önce** tanımlı)

⇒ ⭐ **EVREN NULL'I.** Makine çalıştı (kapılar temiz, replay birebir, pozitif
kontrol hareket etti); **evren uç noktada yeterli hücre-içi değişkenlik
üretmedi**. Alet null'ı değil (B2 oydu), etki null'ı da değil (etki sorusu
sorulabilir hâle **gelmedi**).

### 8. ⛔ Bu koşumdan iddia EDİLEMEYECEKLER

- *"Seçilim landmark drift üzerinde etki etti"* — **seviye 1 kurulamadı**
- *"Lamarckçı kanal"* — seviye 3'ün deseni **kriz maruziyeti confound'u** taşıyor
- *"anlamlı"* — test yok (P7-b)
- Birey düzeyi · genelleme (tek model, tek niş ailesi, **n = 1 deney**)
- ⚠ **V2'nin düştüğü beş geçişte** *"seçilim"* kelimesi hiç kullanılamaz — orada **sürüklenme** var

### 9. ⭐ Bu koşumun ölçtüğü asıl şey — bir sonraki tasarımın girdisi

1. **Bireysel kanal %11.1 oranında ateşleniyor** (24/216, Wilson [7.6, 16.0]).
   Ölçülebilir hücre oranı **%22** — ön-kayıtın **%48** kestirimi **fazla iyimserdi**.
2. **`z`'yi çoğunlukla kriz yazıyor** (144/216 yaşam) ve kriz **hücre içi
   bilgi taşımıyor** ⇒ uç noktanın sorunu tasarımda değil, **oranda**.
3. **`F_agent` yayılımı 5/18 geçişte tam sıfır** ⇒ seçilim girdisi de dejenere.
4. ⇒ Bir sonraki tasarımın hedefi belli: **bireysel kanalın landmark'tan önceki
   ateşleme oranı** ve **`F_agent` ayrımı**. ⚠ İkisi de **sabit değişikliği**
   ister ⇒ §2.7: değer etkiye bakılarak değil, **sabitlerden türetilen bir
   eşitsizlikle** seçilir, ve **üçüncü ön-kayıta** yazılır.

---

## D-125 · 2026-08-18 · 🔒 **ÖN-TAAHHÜT** — sonda koşulmadan önce yazıldı

⚠ **Bu kayıt, sondadan ÖNCE commit edilmiştir.** Sırası kasıtlıdır: sonra
yazılsaydı, sayıyı görüp kriteri ona göre seçmiş olurdum (§2.7 / L9). Commit
sırası bunun kanıtıdır.

### 1. Sonda ne yapacak

| | |
|---|---|
| amaç | `to_landmark` penceresindeki **bireysel** kanal büyüklüklerinin, uç nokta olarak **tanımlı** olup olmadığını ölçmek |
| yapılandırma | tohum **9914** · N=8 · G=2 · 30 olay · **`--no-lora`** · `--fresh-pasture` |
| neden `--no-lora` | maliyetin ~%90'ı DPO eğitimi; sorulan soru **yaşamların ürettiği dağılım**, eğitim değil ⇒ eğitim kapatılınca cevap değişmez, süre 6 saatten ~20 dakikaya iner |
| neden G=2 | tanımlılık **hücre içi** bir özellik; bir nesil yeter. Üreme/Price bu sorunun parçası değil |
| damga | **keşifsel** — sonuç değil, bir sonraki ön-kayıtın girdisi. Tohum 9914 deneyde **kullanılmaz** |

### 2. ⛔ Sondadan **yalnız** şu okunacak

`Var(z') > 0` olan hücrelerin oranı, `z'` = pencere içi **bireysel** kanalın
tepe değeri (`to_landmark.max`).

⛔ **Hesaplanmayacaklar:** `Cov(w, z')` · kol karşıtlığı · etki büyüklüğü ·
herhangi bir işaret. Bunlara bakmak uç noktayı **etkiye göre** seçmek olurdu.

### 3. 🔒 Karar kuralı — **şimdi** yazıldı

> **Yeni uç nokta ancak `Var(z') > 0` oranı hücrelerin ⅔'ünde veya daha
> fazlasında sağlanırsa aday olarak üçüncü ön-kayıta girer.**

- **≥ ⅔** ⇒ aday **girer**; nihai karar yine Yasin'in (D-007).
- **< ⅔** ⇒ ⛔ **girmez.** Bugünkü `z` ile devam edilir ya da tasarım
  yeniden açılır. ⚠ *"Az kalmıştı, biraz daha tohum atalım"* **geçersizdir** —
  kural şimdi yazıldı.

**Karşılaştırma tabanı** (D-123'ten, ölçülmüş): bugünkü `z` **4/18 = %22**.
Ömür-boyu vekilleri: `delta_profile.max` %39 · `mean` %72. ⚠ Vekiller uç nokta
**olamaz** (sabit yaşta okuma ilkesini bozarlar, K2/K3) — sondanın ölçtüğü şey
gerçek pencere.

### 4. Elenen adaylar ve **neden** (bu kaydın parçası, sonradan tartışılmaz)

| aday | tanımlılık | ⛔ eleme sebebi |
|---|---|---|
| `hasat (delta_pool)` | %72 | `F_agent`'ın **girdisi** ⇒ `Cov(w,z)` kısmen totoloji (Mills & Beatty, D-075) |
| `energy_mean_over_life` | %72 | **Pozitif kontrolümüz** (D-121) — uç nokta olursa kontrol işlevini kaybeder |
| `ömür` | %39 | Post-hoc tuzağı (D-122'de reddedildi) + `F_agent`'ın hayatta kalma terimi |
| `landmark_energy` | %33 | Sabit yaşta ✅ ama düşük, ve enerji zaten `F_agent`'ta |
| `delta_profile.max/mean` | %39/%72 | **Ömür boyu** ⇒ sabit yaşta okuma ilkesini bozar |

---

## D-126 · 2026-08-18 · ⛔ **Sonda GEÇERSİZ — tasarım hatası bende**, ve D-125'in kuralı **tetiklenmedi**

**Koşum:** `dau_runs/probe_endpoint_window_s9914.json.partial.json` (checkpoint;
sonuç dosyası **yok** — dış `timeout 3000` I4.1 replay sırasında kesti, `exit 124`).
Tohum 9914 · N=8 · G=2 · 30 olay · **`--no-lora`** · ~50 dk GPU.

### 1. Ölçülen

| | gen1 | gen2 |
|---|---|---|
| `to_landmark.max` hücre içi | **tek değer** (0.5413) | **tek değer** (0.4139) |
| `Var(z')` | **0** | **0** |
| bugünkü `z` | 0 | 0 |

Üç kolun `arm_digest`'i **birebir aynı** (1/3 farklı) ⇒ `--no-lora` altında
kollar özdeş, yani 6 hücre aslında **2**.

### 2. ⛔ Neden bu bir sonuç değil — mekanizma, mazeret değil

C2'nin **kendi verisinde**, adapter **açıkken**, ömür-boyu tepe büyüklüğünün
tanımlılığı:

| nesil | tanımlı hücre | farklı değer / 8 |
|---|---|---|
| **gen1** | **0/9 = %0** | **1.00** |
| gen2 | 7/9 = %78 | 3.00 |
| gen3 | 8/9 = %89 | 3.56 |

⇒ Bu nicelikte ayrışma **gen2'den itibaren** doğuyor: adapter gen1'in
**sonunda** eğitiliyor ve üreme asimetrisi de o anda başlıyor. `--no-lora`
sondası evrenin yalnız **gen1 rejimini** örnekleyebilir ⇒ dejenere çıkması
**yapısal olarak garanti**, ve o rejim hakkında zaten verimiz vardı.

⇒ **Sonda, cevaplaması istenen soruyu göremeyecek biçimde tasarlanmış.**
Hata bende: maliyeti düşürmek için kapattığım şey, tam da farklılaşmayı
üreten kanaldı.

### 3. ⚠ D-125'in kuralı neden **uygulanmıyor** — ve bunun neden bahane olmadığı

D-125 *"< ⅔ ⇒ aday girmez"* diyor. **Uygulanmıyor**, çünkü kuralın örtük ön
koşulu — *"niceliğin değişebileceği koşullarda yapılmış bir ölçüm"* —
sağlanmadı.

⚠ Bu, güdülenmiş bir okuyucunun yapacağı hamlenin **aynısı** (*"test kötü
çıktı, demek ki test geçersiz"*). Meşru kılan dört şey, hepsi denetlenebilir:

1. Teşhis **sondadan önce var olan** veriye dayanıyor (C2 gen1 = **0/9**),
   sonda sonrası üretilmiş bir açıklama değil.
2. Sorgu **tek satır**, herkes tekrar koşabilir.
3. Düzeltilmiş sonda **daha pahalı** — kolay yolu seçmiyorum.
4. Kural **değiştirilmedi**; değişen tek şey **sonda tasarımı**. `≥ ⅔` aynen
   duruyor ve düzeltilmiş sondaya uygulanacak.

### 4. Bedel ve ders

**~50 dk GPU boşa gitti.** Ders, §2.2'nin bir varyantı:

> **Bir sondayı ucuzlatırken kapattığın şeyin, ölçmek istediğin şeyi üreten
> mekanizma olup olmadığını sor.**

⚠ Ve maliyet tahminim de yanlıştı: *"15–30 dk"* dedim, `--no-lora` ile bile
**50 dk**'da bitmedi (48 yaşam × 30 olaya kadar çıkarım). Eğitim maliyetin
%90'ı **değilmiş** — çıkarım da ciddi bir pay.

### 5. Düzeltilmiş sonda — Yasin'in kararına sunuldu

| | |
|---|---|
| yapılandırma | **`--lora`** · `--arms lived` (tek kol) · G=3 · N=8 · 30 olay |
| bilgilendirici hücre | **gen2 ve gen3** (gen1 yapısal olarak dejenere, biliniyor) |
| 1 tohum | ~1 sa · **2 hücre** ⇒ `≥ ⅔` kuralı kaba (2/2 geçer, 1/2 kalır) |
| 2 tohum | ~2 sa · **4 hücre** ⇒ kural anlamlı çözünürlükte |

⚠ Alternatif: sondayı **hiç yapmamak** ve üçüncü ön-kayıtı C2'nin ömür-boyu
vekiliyle (**15/18 = %83**) gerekçelendirmek. ⛔ Riski açık: pencere ömrün
**alt kümesi** olduğu için tanımlılık ancak **düşebilir**, ve ne kadar
düştüğünü bilmeden ön-kayıt yazmış oluruz.

---

## D-127 · 2026-08-18 · ⛔ **Dört rapor kusuru düzeltildi + beş ek kontrol** (Yasin: *"bir daha görmek istemiyorum"*)

**Yetki:** Yasin, 2026-08-18. Kilit sonrası **açık hata düzeltmesi** (§2.10):
D-kaydı + onay ile meşru, ve **hiçbir ölçülen sayı değişmiyor** — değişen
şey raporun ne **söylediği**.

### 1. Düzeltilen dört kusur

| # | kusur | ne yapıyordu |
|---|---|---|
| **A** | `level3_arm_contrast`, `by_generation[gen][arm] = view` | ⛔ **son tohum diğerlerini eziyordu** ⇒ üç tohumluk kol karşıtlığı **tek tohum** gibi raporlanıyordu. Kol karşıtlığı **kalıtım sorusudur**; bu raporun basabileceği **en pahalı yanlış sayı** |
| **B** | `level2_persistence`, `by_arm[arm]` | ⛔ Üç tohumun geçişlerini tek diziye topluyordu ⇒ `gen2 → gen3 → gen2 → …` **bir soyun yörüngesi** gibi okunuyordu. ⚠ Ve daha ağırı: **hiçbir soyun iki geçişi olmadığı** bir koşumda tohumları havuzlayarak asgari şartı geçip *"kalıcılık"* basabiliyordu — **bölümün ön koşulunu uyduruyordu** |
| **C** | *"estimability ABSENT — predates D-121"* | Boş partition'da ateşleniyordu ⇒ D-121 **sonrası** koşum için **yanlış cümle** |
| **D** | `RESULTS_NOTE = "exploratory, not pre-registered"` | C2 **ön-kayıtlıydı** ⇒ dosya kendi statüsü hakkında yanlış konuşuyordu. Koşucu bunu **bilemez** (statü belgede ve commit'te), o yüzden artık **bildiğini** söylüyor |

⇒ **A ve B**, `(tohum, …)` anahtarına çevrildi: çakıştırma artık **yapısal
olarak** imkânsız.

### 2. ⭐ Ortak sebep bulundu — ve o düzeltildi

**Analiz testlerinin tamamı tek tohumla kuruluyordu** (`_three_arms` hep
`seed: 9901`). Tohum boyutunu çakıştıran bir kod, **çakışacak ikinci tohum
olmadığı için** testlerde görünmez. ⇒ `_multi_seed()` fixture'ı eklendi (üç
tohum × üç kol, ayrı bloklar) ve fixture üç nesle çıkarıldı, ki her soyun
**gerçekten** iki kapanmış geçişi olsun.

### 3. Mutasyon kontrolü — **md5 doğrulamalı** (K5)

| mutasyon | kırılan test |
|---|---|
| level3 tohumu tekrar çakıştırıyor | `test_level3_reports_every_seed_not_just_the_last` |
| level2 tohumları tekrar birleştiriyor | `test_level2_keeps_each_seed_its_own_sequence` |
| level2 satırından tohum etiketi kalkıyor | aynı test |
| boş partition yine *"predates D-121"* diyor | `test_an_empty_partition_is_not_called_a_pre_D121_run` |

⚠ **İlk denememde toplu betik çelişkili sonuç verdi** (M2, level2 yerine
level3 testini kırdı gibi göründü). Sebep kodda değil **benim ölçüm
aracımdaydı**; matris dosya md5'i doğrulanarak ve `-p no:cacheprovider` ile
yeniden koşuldu, dördü de doğru testi kırdı. ⇒ **K5** bundan doğdu.

### 4. C2 raporu yeniden üretildi

Sayılar **değişmedi**; gruplama ve etiketler değişti. Düzeltilmiş seviye 3,
elle çıkardığım tabloyla **birebir** uyuşuyor (9911 gen3: 0.589 / 0.619 /
0.030). ⚠ `dau_runs/c2_population_n8_g3_s3.json` içindeki `note` alanı **eski
metni taşımaya devam ediyor** — dosya yeniden yazılmadı; statünün otoritesi
`docs/PREREGISTRATION_2.md` kilidi (`72df476ebd54`).

### 5. ⇒ Beş ek kontrol, `CLAUDE.md §2.4-b`'ye bağlayıcı olarak yazıldı

**K1** mekanizma kontrolü · **K2** boyut testi · **K3** çağrı yeri testi ·
**K4** sayı disiplini · **K5** kendini kanıtlayan mutasyon koşumu.

⚠ Hepsi bu oturumda **gerçekleşmiş** hatalardan türetildi; hiçbiri
varsayımsal değil.

Suite: **590 passed, 2 deselected**.

---

## D-128 · 2026-08-18 · 🔒 **K1 MEKANİZMA KONTROLÜ** — düzeltilmiş sonda, koşumdan önce yazıldı

**Yetki:** Yasin onayladı (2026-08-18), *"bu koşumun sonunda hata ve gözden
kaçan bir şey istemiyorum"* şartıyla. ⚠ Bu kayıt **koşum başlamadan** commit
edilmiştir (K1, `CLAUDE.md §2.4-b`).

### (a) Ölçülen niceliği hangi mekanizma üretiyor

`to_landmark.max` = ajanın **kendi** `DeltaRecord` büyüklüklerinin, olay ≤ 10
penceresindeki tepesi. Ajanlar arası fark şu zincirden doğuyor:

> sıralı erişim + rotasyon → hasat farkı → enerji farkı → **adapter eğitimi
> (Kanal 2)** → varis farklı ağırlıkla doğuyor → farklı kararlar → farklı PE

⛔ **Zincirin belirleyici halkası Kanal 2.** Ölçüldü (C2, `delta_profile.max`):

| nesil | tanımlı hücre |
|---|---|
| gen1 (adapter **henüz yok**) | **0/9** |
| gen2 | 7/9 |
| gen3 | 8/9 |

### (b) Seçtiğim bayraklardan hangisi bu mekanizmayı kapatır

| bayrak | mekanizmaya etkisi | kararım |
|---|---|---|
| ⛔ `--no-lora` | **Kanal 2'yi tamamen kapatır** ⇒ ölçülecek fark hiç doğmaz | **KULLANILMIYOR** — D-126'da 50 dk buna gitti |
| ⛔ `--mock-llm` | Model yok ⇒ eğitim yok, kararlar kanned | **KULLANILMIYOR** (yalnız kuru provada) |
| `--n-generations 3` | gen1 yapısal dejenere ⇒ **2'nin altı hiçbir bilgi vermez** | **3** |
| `--arms` | ⭐ `null` **eğitim almıyor** ⇒ en zayıf kol. Yalnız `lived` koşulsa **en iyi durum** ölçülürdü | **`lived null`** — en iyi **ve** en kötü birlikte |
| `--fresh-pasture` | Deneyle aynı (D-104) | **aynı** |
| `--events 30` · `--n-agents 8` | Deneyle aynı | **aynı** |

⭐ **Kol seçiminin gerekçesi ölçüm** (C2, gen2+gen3): `lived` **6/6** ·
`shuffle` **6/6** · ⛔ `null` **3/6**. `shuffle` `lived`'ın kopyası gibi
davrandığı için **alınmadı**; bilgi taşıyan ayrım `lived` ↔ `null`.

### (c) Bu yapılandırmada niceliğin dejenere olmadığının kanıtı

Aynı yapılandırmayla (`--lora`, G=3, N=8) koşulan C2'de ömür-boyu vekil
gen2/gen3'te **15/18** hücrede tanımlıydı. Sonda, aynı niceliğin **pencere
içi** hâlini ölçüyor — pencere alt küme olduğu için oran **ancak düşebilir**,
ve ölçülmek istenen tam olarak **ne kadar düştüğü**.

### Kuru prova (mock, aynı bayraklar) — yapı doğrulandı

2 kol · `lived` eğitiyor / `null` eğitmiyor · `to_landmark` penceresi **10
olay** · **4** Price satırı · `I1.1` mock'ta **tasarım gereği** FLAG
(`reason: "no loaded model"`), gerçek koşumda ABORT olarak kalıyor.

### Koşum komutu (tam olarak bu)

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9915 --n-agents 8 --n-generations 3 --events 30 \
  --lora --fresh-pasture --arms lived null \
  --results dau_runs/probe2_endpoint_window_s9915.json
```

⚠ **Dış `timeout` YOK.** D-126'da `timeout 3000` koşumu I4.1 replay sırasında
kesti ve sonuç dosyası hiç yazılmadı. Beklenen süre **~1 sa 40 dk**
(C2'den: kol-tohum başına ~39 dk + replay payı) — ⚠ **tahmin**, ve D-126'da
tahminim tutmamıştı.

### Okuma kuralı — D-125 aynen geçerli

**4 hücrenin en az 3'ünde** (`≥ ⅔`) `Var(to_landmark.max) > 0` ⇒ aday üçüncü
ön-kayıta girer. Aksi hâlde **girmez**. ⛔ Kovaryans · kol karşıtlığı · etki
büyüklüğü **hesaplanmayacak**.

---

## D-129 · 2026-08-19 · 🔒 **SONDA-2 OKUNDU: aday GİRMEZ (2/4)** — ve sondanın asıl bulgusu uç nokta değil, **`null` kolunun donmuş olması**

**Koşum:** `dau_runs/probe2_endpoint_window_s9915.json` · tohum 9915 · N=8 ·
G=3 · 30 olay · `--lora` · `--arms lived null` · **~2 sa 20 dk** ·
`run_quality = clean` · **6/6 kapı** · I4.1 **identical** · `complete: true`.

### 1. D-125'in kuralı — aynen uygulandı

| kol · nesil | `Var(to_landmark.max)` | farklı değer / 8 | aralık | sonuç |
|---|---|---|---|---|
| `lived` gen2 | 0.01246979 | 3 | 0.3918–0.6270 | **TANIMLI** |
| `lived` gen3 | 0.00995394 | 3 | 0.3952–0.6358 | **TANIMLI** |
| ⛔ `null` gen2 | **0.00000000** | **1** | 0.6050 | **DEJENERE** |
| ⛔ `null` gen3 | **0.00000000** | **1** | 0.7797 | **DEJENERE** |

⇒ **2/4.** Kural **≥ ¾** istiyordu (D-125, koşumdan önce yazıldı).
⛔ **ADAY GİRMEZ.** *"Eğitimli kolda çalışıyor, yeter"* denmedi; kural
yazıldığı gibi uygulandı.

⚠ **Kovaryans · kol karşıtlığı · etki büyüklüğü hesaplanmadı.**

### 2. ⭐⭐ Asıl bulgu — sorun uç noktada değil, **`null` kolunda**

`null` kolunda ajanlar **hiçbir nicelikte** ayrışmıyor. Üç nesilde de:

| nicelik | `lived` gen2/gen3 yayılımı | `null` gen2/gen3 yayılımı |
|---|---|---|
| hasat (`delta_pool`) | 96.0 / 114.0 | **0.0 / 0.0** |
| enerji | 0.496 / 0.404 | **0.0 / 0.0** |
| ömür | 29–30 / 30–30 | **30–30 / 30–30** |
| `F_agent` | 0.092 / 0.022 | **0.0 / 0.0** |
| pencere tepesi | 0.235 / 0.241 | **0.0 / 0.0** |

**Mekanizma ölçüldü:**

| kol · nesil | havuz sonu oranı | kriz olayı | eksik alan ajan |
|---|---|---|---|
| `lived` gen2 | **0.000** | 62 | ✅ 6 farklı hasat |
| `lived` gen3 | 0.225 | 24 | ✅ 3 farklı |
| `null` gen2 | **0.593** | **0** | ❌ hepsi eşit |
| `null` gen3 | **0.611** | **0** | ❌ hepsi eşit |

⇒ **Zincir:** adapter → farklı davranış → farklı talep → **mera kıtlaşır** →
sıralı erişim ısırır → ayrışma.

⛔ **P0-① yalnızca kıtlık varken ayrım üretiyor.** Bolluk varken sıralı erişim
**işlemsiz**: herkes istediğini tam alır, sıra hiçbir şeyi değiştirmez. Adapter
olmadan varisler klon kalıyor, aynı talebi yapıyor, mera hiç kıtlaşmıyor.

⇒ `null`, *"parametrik mirası olmayan kontrol"* değil; bu nişte **donmuş bir
klon popülasyonu**: `Var(F_agent) = 0` ⇒ turnuva saf yazı-tura, ve **hangi uç
nokta seçilirse seçilsin** `Var(z) = 0`.

### 3. ⇒ Bu, uç nokta sorusunu **kapatıyor ve yerine daha derinini açıyor**

*"Hangi nicelik uç nokta olsun"* yanlış soruymuş. Doğru soru:

> ⛔ **`null` kolu ajanlarını nasıl ayrıştıracak — yoksa yapısal olarak
> ayrıştıramayacağını ilan mı edeceğiz?**

⚠ Bu, D-123'ün **V2 düşüşlerini de açıklıyor**: C2'de `F_agent` yayılımı sıfır
çıkan beş geçişin **üçü `null` kolundaydı**.

### 4. ⭐ Kol seçimi kararı kendini doğruladı

D-128'de `null`'ı **bilerek** dahil etmiştim (C2'de 3/6 ile en zayıf koldu).
⚠ **Yalnız `lived` koşulsaydı sonuç 2/2 = %100 çıkacak, aday "geçti" diye
ilan edilecek ve gerçek deneyde `null` hücreleri yine boş çıkacaktı.**
Bu, D-126'nın hatasının tekrarı olurdu.

### 5. Sınırlar

1. ⚠ **Tek tohum, tek niş.** C2'de `null` bazı hücrelerde ayrışmıştı (3/6) ⇒
   donmuşluk **nişe bağlı**, evrensel değil.
2. ⚠ Sonda **keşifsel**; tohum 9915 deneyde kullanılmaz.
3. ⚠ Süre: **~2 sa 20 dk** — tahminim önce *"1 sa 40 dk"*, sonra *"3.5–4 sa"*
   demişti. ⇒ K4'e ek: maliyet tahmini tabanın **yayılımını** taşımalı
   (nişler arası toplam-olay farkı **2.3 kat**: 104 ↔ 240).

---

## D-131 · 2026-08-19 · ⭐ **TASARIM KARARI: birincil karşıtlık `lived` ↔ `shuffle`; `null` betimleyici kola indiriliyor** — iki fizik kaldıracı da **aritmetikle** elendi

**Yetki:** Yasin, 2026-08-19: *"DR'ye güvenmeden kontrol ederek tasarım kararı
al."* ⚠ Karar **DR #11'in cevabıyla çapraz kontrol edilecek** ve Yasin'in
vetosuna açıktır.

### 1. Çözülmesi gereken problem (D-129/D-130)

Farklılaşmanın **tek** kaynağı adapter: adapter → farklı davranış → farklı
talep → kıtlık → sıralı erişim ısırır → ayrışma. ⇒ Adapter'ı olmayan `null`
kolu, zengin nişte **donmuş klon popülasyonu**: `Var(F_agent) = 0`, turnuva
yazı-tura, ve **hangi uç nokta seçilirse seçilsin** `Var(z) = 0`.

### 2. ⛔ Denenen iki fizik kaldıracı — **ikisi de ölü**, sabitlerden hesaplandı

**Kaldıraç 1 — kapasiteyi düşürüp kıtlığı garantilemek.**
Kişi başı dinamik `p ← p + r·p(1−p/K) − d` üzerinde, K ∈ {100…5} ve
d ∈ {1, 2, 8} için ilk kıtlık ve ilk kriz olayları hesaplandı.
⇒ **Her yapılandırmada kriz, kıtlıktan önce (ya da aynı olayda) ateşliyor.**
Sebep: kriz eşiği `0.30·K`, kıtlık noktası `d`; havuz büyük olandan küçüğe
inerken **önce krize** giriyor.

**Kaldıraç 2 — kriz eşiğini düşürüp sırayı öne almak.**
`CRIT ∈ {0.30, 0.15, 0.10, 0.05, 0.02}` × `K ∈ {100…10}` × `d ∈ {2, 8}` = 70
kombinasyon tarandı. Aranan: *kıtlık ≤ olay 9 **ve** kriz kıtlıktan sonra.*
⇒ ⛔ **Hiçbir kombinasyon sağlamıyor.**

**Neden — ve bu zaten kayıtlıydı:** D-081, *"bu evrende kademeli kıtlık yok,
**kıtlık anı** var"* demişti. Havuz tek adımda *"herkese yeter"*den *"boş"*a
geçiyor ⇒ **kıtlık ile kriz aynı olaydır**, eşik nereye konursa konsun
ayrılmıyorlar.

⚠ Ve ikinci bir imkânsızlık: talep davranışa bağlı (`COOPERATE` 2.0 ↔
`DEFECT` 8.0) ve C1 davranışa dokunmayı yasaklıyor. d=2 için kıtlığı olay
9'dan önce getiren K (≈15), d=8 için havuzu **olay 2'de** öldürüyor.
⇒ Tek bir K iki talep düzeyinde birden çalışamaz.

⇒ **Fizikle çözülemez.** Bu, aritmetiğin verdiği bir sonuç, tercih değil.

### 3. ⭐ Karar

| # | madde |
|---|---|
| **1** | **Birincil karşıtlık `lived` ↔ `shuffle`.** İkisi de eğitiliyor ⇒ ikisi de ayrışıyor (C2: **6/6** ve **6/6**) |
| **2** | **`null` betimleyici kola indirilir.** Geçerlilik kriteri **taşımaz**; raporlanır ama hiçbir kapı ona bağlanmaz |
| **3** | **İlan edilen sınır:** *"Bu tasarımda farklılaşma davranışa bağlıdır; eğitilmemiş kol zengin nişte yapısal olarak dejeneredir."* Bu bir kusur değil, **bulgudur** ve öyle raporlanır |
| **4** | Uç nokta kararı **üçüncü ön-kayıta** bırakılır. ⚠ D-125'in *"aday girmez"* hükmü **eski tasarım için geçerliliğini korur**; yeni tasarım yeni bir kriteri **ölçümden önce** ilan eder |

**Neden meşru:** ilk ön-kayıt da birincili `lived ↔ shuffle` yapmıştı — gerekçe
oradaki gibi: *"`null` yalnız 'eğitim oldu mu' sorusunu cevaplar; aksiyomun
iddiası eğitimin **içeriğine** dairdir."* Karar yeni bir çerçeve değil, o
çerçeveye **geri dönüş**, ve şimdi ölçülmüş bir sebeple.

### 4. ⚠ İtiraz edilebilecek tek yer — açıkça yazıyorum

`lived`/`shuffle`'ın ayrıştığını **ölçtükten sonra** onları birincil yapıyorum.
Savunmam: bakılan şey **etki değil, tanımlılık** — dağılımın var olup olmadığı,
ki bu ön-kayıtta zaten **geçerlilik ön-koşulu** olarak tanımlı (V2) ve L9'un
yasakladığı şey **kol farkına** bakmak. Kol farkına **bakılmadı**.
⚠ Yine de bir hakem bunu itiraz konusu yapabilir; üçüncü ön-kayıtta **bu
paragrafla birlikte** ilan edilecek.

### 5. Bu kararın çözmediği iki şey

1. **Uç noktanın tek boyuta çökmesi** (D-130 §9): `social`/`uncertainty` hiç
   yazılmıyor, `resource` krizin alanı ⇒ bireysel kanalın tek boyutu `energy`,
   216 okumanın **11'inde** dolu. ⇒ Üçüncü ön-kayıtın asıl konusu bu.
2. **Adapter sönümü** (D-130 §12): 6/6 dizide 1.8×–4.8× azalma. İlan edilecek
   sınır; düzeltme denenmiyor.

---

## D-132 · 2026-08-19 · **DR #11 mutabakatı** — D-131 ayakta, ve **hiç düşünmediğimiz bir kaldıraç** çıktı

Mutabakat tablosu `RECONCILIATION.md` **§T**.

### 1. Kaynak sicili — ⚠ **gerileme**

- ❌ **14. kimlik hatası:** *Permutation Tests for Random Effects in LMM*
  → *"El-Horbaty ve ark."* değil, **Lee & Braun 2012** (`10.1111/j.1541-0420.2011.01675.x`).
- ⚠ **~15 iddianın yalnız 3'ünde DOI var** ⇒ D-080'in 1. şartı bu turda
  tutmadı (DR #9/#10'da tutuyordu).
- ⚠ İki alıntı iddiasını taşımıyor: *"species numbers"* cümlesi bir LMM
  özetinde olamaz · *"larger coefficients"* cümlesi **argmax** yapısını
  desteklemiyor.
- ✅ Buna karşılık **boşluk iki kez ilan edildi** ⇒ 3. şart tuttu.
- ⛔ **İç çelişki:** Q5'te *"evrensel nesil alt sınırı bulunamadı"* denip
  hemen ardından *"8+ nesil ⇒ birikimli kalıtım"* normatif tablosu basılmış.
  Tek dayanağı **bir** çalışmanın (Martin ve ark. 2014) sekizli zincirleri.
  ⇒ **Tablo alınmadı; uyarısı alındı** — tasarımımız **G=3**, ve *"birikimli"*
  kelimesi ilan edilmiş sınırla kullanılacak.

### 2. Alınanlar

| ne | dayanak |
|---|---|
| ⭐ **Loss of Plasticity** — D-130 §12'nin adı | Dohare ve ark. 2024, *Nature*, **doğrulandı** |
| Sıfır-varyanslı kolda **sınır problemi** ve karışım χ² / permütasyon çözümü | Lee & Braun 2012, künye **düzeltilmiş** |

⚠ **LoP'a kendi çekincemizi ekledik:** LoP *"öğrenme yeteneğini yitirme"*dir;
bizde ölçülen **güncelleme büyüklüğünün küçülmesi**, ki bu **yakınsama** da
olabilir. Ayırt etmek için güncelleme değil **öğrenme sonucu** ölçülmeli.
DR bu ayrımı yapmadı.

### 3. ⛔ Alınmayan — Q2'nin iki mekanizması bizde zaten var ya da uygulanamaz

- **Asenkron güncelleme:** ⚠ **zaten var** (sıralı + rotasyonlu hizmet). İşe
  yaramama sebebi asenkronluk değil, **karar fonksiyonunun basamak olması**
  (D-084: tek soğurucu çıktı, 1e-9 girdi farkı bile oynatmıyor).
- **Kaotik ayrışma / çoklu çekici:** sürekli ve duyarlı dinamik gerektiriyor;
  bizim karar haritamız **ayrık ve soğurucu**. Kaynak ayrıca **düopol
  pazarlama** modeli (başlık DR'de yanlış yazılmıştı).

### 4. ⭐⭐ Turun gerçek kazancı: **ajan-ajan etkileşimi**

DR'nin Q2 cevaplarının **hepsi** tek bir şeye dayanıyor: ajanların
**birbiriyle** etkileşmesi. ⛔ Bizim popülasyonumuzda bu **hiç yok** — sekiz
ajanın da `opponent_id`'si **aynı NPC** (D-130 §9), tek ortaklıkları mera.

⇒ Ajan-ajan etkileşimi:
- kıtlıktan **bağımsız** simetri kırar,
- **C1'i ihlal etmez** (hiçbir trait atanmıyor),
- ve **kontrol kolunu yeniden değişken yapabilir** — D-131'in kabul etmek
  zorunda kaldığı dejenereliği **ortadan kaldırabilir**.

⚠ Bedeli: en az iki yeni sabit (kim kiminle · hangi sıklıkta) ⇒ **üçüncü
ön-kayıtın konusu**, bu koşumun değil.

### 5. ⇒ D-131 **değişmiyor**

Birincil karşıtlık `lived ↔ shuffle`, `null` betimleyici. DR bunu çürütmedi;
dejenere kontrolün parametrik testi geçersiz kıldığını söyleyerek dolaylı
olarak **destekledi**. Ajan-ajan etkileşimi **bir sonraki tasarımın** en güçlü
adayı olarak kayda geçti.

---

## D-133 · 2026-08-19 · 🗺 **Yol haritası: Yön 3'e hızlandırılmış geçiş** (`docs/ROADMAP.md`)

**Yetki:** Yasin, 2026-08-19: *"Yön 3 çok cazip geldi ama onu sonraya saklayıp
ona geçme adımlarını hızlandırmak isterim."*

### 1. ⭐ Stratejik çıkış noktası — **pahalı koşumu atlıyoruz**

Yön 3'e (ajan-ajan etkileşimi) gidilecekse, **bugünkü fizikle 30–80 saatlik
doğrulayıcı koşum boşa gider**: sosyal kuplaj evreni değiştirir, o sayılar ne
karşılaştırılabilir ne yeniden kullanılabilir. ⇒ GPU yalnız **geçişten sağ
çıkacak** işlere harcanır.

### 2. ⭐⭐ Yön 3 sanılandan ucuz — mekanizma **kodda mevcut**

| parça | durum |
|---|---|
| `compute_social_load` · `record_interaction` · `compute_coordination_friction` · `compute_markov_expectation` | ✅ hepsi **genel**, rastgele ajan id'leri alıyor |
| N ajan arasında **hepsi-hepsiyle** sosyal güncelleme | ✅ `run_convention_pilot.py:243` — **çalışan referans** |
| Değişecek tek yer | ⛔ popülasyon koşucusunda `opponent_id = OPPONENT_ID` (tek NPC) |

⭐ **Muhtemelen sıfır yeni sabit:** havuz erişimi zaten rotasyonlu (D-104);
aynı rotasyon eşleştirmeyi de tanımlarsa yeni sabit gerekmez.
⚠ **Doğrulanacak, varsayılmayacak** (Faz 0.2).

### 3. Fazlar

| faz | maliyet | çıktı |
|---|---|---|
| **0** GPU'suz | ~2–3 sa | uç nokta boyut düzeltmesi · sosyal kablolama tasarımı · K1 kontrolü · K2/K3/K5 testleri |
| **1** tek ucuz koşum | ~1–2 sa GPU | ⭐ **tek soru:** sosyal kuplaj `null`'ı değişken yapıyor mu |
| **2** ön-kayıt | GPU'suz | fizik + uç nokta + **gerçek güç hesabı** kilitlenir |
| **3** tek pahalı koşum | tohum başına ~2 sa | nihai fizikle, gözetimsiz |

**Faz 1 yol ayrımıdır:** `null` değişkenleşiyorsa Yön 3 kurulur;
değişkenleşmiyorsa D-131 kalıcılaşır ve Yön 2'ye dönülür.

### 4. ⛔ Bilerek yapılmayacaklar

1. Bugünkü fizikle doğrulayıcı koşum (taşınmaz)
2. G'yi 8'e çıkarmak — DR normatifi dayanaksız (§T.2) **ve** adapter sönümü
   uzun soyda sinyali seyreltebilir (D-130 §12)
3. Davranışa dokunmak (C1/K7)
4. Kapasite / kriz eşiği ayarı — D-131'de aritmetikle elendi

### 5. ⚠ Açık kalan tek eski borç

**En küçük anlamlı etki** — DR #1'den beri açık, hâlâ verilmemiş. Faz 2'de
verilmek zorunda, yoksa güç hesabı yapılamaz.

---

## D-135 · 2026-08-19 · ⛔⛔ **Kuyruk 0.1: ajan-ajan etkileşimi de simetriyi kırmıyor** — ve bu bir **trilemma**yı açığa çıkarıyor

**İş:** `EXECUTION_QUEUE.md` madde 0.1. **Sıfır GPU**, gerçek fonksiyonlarla.

### 1. Ölçüm

`dau/foundation/social.py`'nin **kendi** fonksiyonlarıyla (`record_interaction`,
`compute_social_load`), dört özdeş ajan:

| senaryo | `social_load` | sonuç |
|---|---|---|
| **hepsi-hepsiyle**, özdeş davranış | `{a0:0.0, a1:0.0, a2:0.0, a3:0.0}` | ⛔ **özdeş** |
| **ikili eşleştirme + rotasyon**, özdeş davranış | `{a0:0.0, …}` | ⛔ **özdeş** |
| hepsi-hepsiyle, **davranış farklı** (biri defect) | `{a0:0.125, diğerleri 0.0}` | ✅ ayrışıyor |

⇒ **Sosyal kuplaj bir ayrım kaynağı değil, bir çarpandır** — tıpkı sıralı
erişim gibi (D-129). Fark **yaratmıyor**, var olanı büyütüyor.

### 2. ⭐⭐ Ortaya çıkan yapısal sonuç — bir trilemma

> **Deterministik** bir evrende, **bit düzeyinde özdeş** ajanlarla ve **trait
> enjeksiyonu yasakken**, tek olası simetri kırıcı **çekişmeli bir kaynaktaki
> konumdur.** Diğer bütün mekanizmalar (sosyal kuplaj · uzamsal topoloji ·
> asenkronluk) **çarpandır**.

Ve çekişme, bu evrende **talep farkına** bağlı ⇒ **döngü**: fark için fark
gerekiyor.

⚠ **DR #11'in Q2 cevapları neden bizde çalışmıyor:** literatürdeki modeller
(Axelrod, Flache & Macy) simetriyi **rastgele başlangıç özellikleriyle**
kırıyor — bizde **C1** yasaklıyor; ya da **stokastik güncellemeyle** — bizde
**D-037/I0.6** yasaklıyor. Mekanizmalar gerçek, **ön koşulları bizde yok**.

### 3. Döngüden çıkışlar — ve hangisinin açık olduğu

| çıkış | durum |
|---|---|
| **(a)** Kurucuları farklı doğur (② ayrı niş · ③ asimetrik doğum · ⑤ uzamsal yerleşim) | ⚠ **Fark yaşamaktan önce gelir** — aksiyomun sınırında; D-077/D-080'de bu yüzden geri çekilmişti |
| **(b)** Determinizmi kır (④ örnekleme) | ⛔ **D-037 / I0.6** yasaklıyor: gürültü etkiden büyüktü |
| **(c)** ⭐ **Simetri kaynağının müdahalenin kendisi olduğunu kabul et** | ✅ **D-131 bunu zaten seçti** — `lived ↔ shuffle` birincil, `null` betimleyici |
| **(d)** Kaynağı talepten bağımsız çekişmeli yap | ⛔ D-131'de aritmetikle elendi (kıtlık ile kriz **aynı olay**) |

⇒ ⭐ **D-131 bir geri çekilme değil, C1 + D-037 ile uyumlu TEK seçenek.**

### 4. Yol haritasına etkisi — **Faz 1 iptal**

`ROADMAP.md`'nin Faz 1'i (*"sosyal kuplaj `null`'ı değişken yapıyor mu"*,
~1–2 sa GPU) **gereksiz**: cevap **hayır**, ve on dakikalık bir testle alındı.
⇒ Faz 0.4 (sosyal kablolama) ve 0.5 (karar kuralı) da **düşüyor**.

⚠ **Kuyruğun amacı buydu:** ucuz faz, iki saatlik GPU koşumunu **on dakikada**
öldürdü. K1'in *"mekanizmayı önce sor"* kuralının ilk kez **kazandırdığı** yer.

### 5. ⇒ Sıradaki soru değişti

*"Nasıl ayrıştırırız"* sorusu kapandı: **ayrıştıran şey müdahaledir**, ve bu
kabul edilmiş durumda (D-131). Geriye kalan tek açık teknik iş, uç noktanın
**tek boyuta çökmesi** (D-130 §9) — yani kuyruğun **0.2** maddesi.

---

## D-136 · 2026-08-19 · **Kuyruk 0.2: uç noktanın dört ekseni raporlanıyor** — ve ölçüm, tek boyutluluğun sebebini **argmax'tan spillover'a** taşıyor

**İş:** `EXECUTION_QUEUE.md` madde 0.2. **Saf raporlama, hesap değişmedi,
GPU yok.** Borç: PROVENANCE_AUDIT §9 (D-130).

### 1. Borç neydi

`z` = landmark drift, dört alan taşıyor. Alanı seçen `_primary_affected_domain`
**en çok oynayan ekseni** alıyor ve kalan üçünü **atıyor** — hesapladıktan bir
satır sonra. C2'de (216 yaşam) `z` bayraklarında yalnız `energy` ve `resource`
göründü, `social`/`uncertainty` **sıfır kez**.

⛔ Ama bu **tag hakkında** bir cümledir, ve tag bir argmax'tır. Dosyada
*"o eksen hiç oynamadı"* ile *"oynadı ve argmax'ı kaybetti"* **ayırt
edilemiyordu**.

### 2. Ne yapıldı — üç dosya, sıfır hesap değişikliği

| yer | ne |
|---|---|
| `graph.py` · `_axis_deltas` (yeni) | dört eksenin `\|after−before\|` değeri; `_primary_affected_domain` **artık bunun üstünde** argmax alıyor ⇒ tek otorite korunuyor (§2.8) |
| `graph.py` · `_record_pe_event` | PE satırı `affected_domain` **ve** `axis_deltas` taşıyor — kazananın **yanına**, yerine değil |
| `run_population_experiment.py` · `_axis_profile` (yeni) | eksen başına `max`/`mean`/`n_events` + `wins` (argmax sayacı); `delta_profile["axes"]` ve `to_landmark["axes"]` |

⚠ **`_magnitude_summary` bilerek kullanılmadı.** İki nicelik **farklı kapıya**
karşı ölçülüyor: `delta_magnitude` skarın **yazılıp yazılmayacağına** karar
veriyor (`is_trauma`, ≥ 0.70), eksen deltası yalnız **hangi alana**
dosyalanacağına. Bir eksene `headroom_to_trauma` yazmak, evrenin hiç
hesaplamadığı bir eşiği raporlamak olurdu — §2.8'in tam hatası.

⚠ **Aletlenmemiş satır sıfır sayılmıyor, atlanıyor** — *"kaydedilmedi"* ile
*"oynamadı"* aynı şey değil (D-121'in `z` için çizdiği ayrım).

### 3. K1–K5

| | |
|---|---|
| **K2** | eksen bloğu **iki ajanla** test edildi; filtresiz hâli "a"ya "b"nin 0.99'unu yazıyor |
| **K3** | `run_population_experiment` üzerinden **uçtan uca**: alan sonuç dosyasında, ve `n_events > 0` |
| **K5** | **altı mutasyon**, her birinin md5'i okundu (öncesi → sonrası → geri yükleme), `-p no:cacheprovider`. Altısı da **doğru testi** kırdı |
| **K4** | aşağıdaki sayıların hepsi çıktıdan **okundu**; koşum **keşifsel ve karar-stub'lı**, öyle etiketlendi |

Mutasyonlar: eksenlerden üçünü at · ajan filtresini kaldır · aletlenmemiş
satırı sıfır say · pencereyi landmark'ın ötesine taşır · tag'i yeniden türet ·
bloğu hiç yazma.

### 4. ⭐⭐ Ölçüm — ve borcun cevabı **beklenenden farklı** çıktı

⚠ **Keşifsel, ön-kayıtlı değil.** Kararlar **stub** (LLM yok), tohum 9301,
3 ajan × 6 olay, `lived`, nesil 0. Bu koşum **davranış** hakkında hiçbir şey
söylemez; söylediği şey **PE → InternalState eşlemesinin yapısı**.

| eksen | max | mean | argmax kazancı |
|---|---|---|---|
| `energy` | 0.826 | 0.500 | **5/6** |
| `resource` | 0.856 | 0.167 | **1/6** |
| `social` | **0.200** | 0.190 | **0/6** |
| `uncertainty` | **0.171** | 0.136 | **0/6** |

⇒ **`social` ve `uncertainty` ölü değil — oynuyorlar.** C2'nin *"sıfır kez"*i
bir **argmax artefaktı**, eksik hareket değil. Borç bu haliyle kapandı:
dosya artık farkı söyleyebiliyor.

### 5. ⛔ Ama sayının mekanizması sorulduğunda kazanç daralıyor

`social` max'ı **tam 0.200** ve `CROSS_AXIS_SPILLOVER = 0.20`
(`constraints.py:31`). `_apply_prediction_error` (`graph.py:802–809`) birincil
olmayan her eksene **`PE × 0.20`** veriyor — **tekdüze**.

⇒ ⛔ **Dört sayıyı geri kazanmak dört boyut geri kazanmıyor.** `social` ve
`uncertainty`, birincil ekseni süren **aynı PE'nin sabit katı**; bağımsız
bilgi taşımıyorlar. Aralarındaki fark (0.200 vs 0.171) yalnız **setpoint
kırpmasından** (`max(setpoint, …)`) geliyor, ayrı bir kanaldan değil.

⚠ Bu koşumda `source=fallback` ⇒ PE **her olayda 1.000**. Gerçek koşumda PE
değişir, ama **tekdüzelik yapısaldır**, koşuma bağlı değil.

⇒ **Uç noktanın tek boyutluluğunun sebebi teşhis değiştirdi:** argmax'ın
kazanan-hepsini-alır olması **ikincil**; asıl sebep **spillover'ın tekdüze
olması**. Argmax düzeltilse bile üç eksen birbirinin ölçekli kopyası kalırdı.

### 6. ⭐ Bu, açık bir GAP'i tam zamanında tetikliyor — **GAP-10**

GAP-10'un üçüncü maddesi: *"asimetrik spillover matrisi — kod skaler
`CROSS_AXIS_SPILLOVER = 0.20` kullanıyor; brief domain-özgü matris
öneriyor."* §5 tam olarak bunun bedelini ölçtü.

⭐ **Neden şimdi optimal:** GAP-10 bugüne kadar *"süresi dolmuş ölçüm
ertelemesi"* olarak duruyordu, **gerekçesi yoktu**. Artık var, ve gerekçe bir
sayı: uç noktanın üç boyutu, spillover skaler olduğu için birbirinin
kopyası. Ve zamanlama doğru — **üçüncü ön-kayıt henüz açık** (Faz 2), yani
sabit değişikliği hâlâ meşru; kilitlendikten sonra olmayacak (§2.10).

⚠ **Karar Yasin'in (D-007).** Bu bir **sabit ailesi** değişikliğidir
(skaler → matris) ⇒ Claude Code tek başına vermez. Ve §2.7 bağlayıcı: değer
**etkiye bakılarak seçilemez**.

### 7. Sınırlar

- Koşum **keşifsel**, kararlar **stub**, PE sabit 1.000 ⇒ tablo **büyüklük
  dağılımı** hakkında değil, **yapı** hakkında delildir.
- Üç ajan **birebir aynı** sayıları üretti — D-129/D-135'in klon sonucu,
  **yeni bir bulgu değil**, tutarlılık kontrolü.
- Eksen bloğu **hiçbir hesaba girmiyor**; ondan uç nokta seçmek **üçüncü
  ön-kaydın** işidir ve **etkiye bakılarak yapılamaz** (L9).
- `z`'nin `resource` girdisi ağırlıkla **krizden** geliyor
  (`CRISIS_AFFECTED_DOMAIN` sabit) — eksen bloğu **bireysel kanalı** ölçer,
  kriz kanalını değil; ikisi `delta_profile`'da zaten ayrı.

---

## D-137 · 2026-08-19 · ✅ **KARAR (Yasin): GAP-10 / spillover — skaler KALIYOR, sınır ilan ediliyor** — ve önerilen düzeltmenin **vaat ettiğini yapmadığı ölçüldü**

**Soru:** D-136 §6 GAP-10'u tetikledi. Skaler `CROSS_AXIS_SPILLOVER = 0.20`
kalsın mı, domain-özgü asimetrik matris mi? **GPU yok, keşifsel ölçüm.**

⚠ **Bu bir kapanış değil, gerekçeli bir ertelemedir** (Yasin: *"ileride
değiştirip geliştirebileceğimiz bir nokta olarak bırakalım"*). Yeniden açılma
tetiği §7'de yazılı.

### 1. Kaynak bulundu — ve kaynaksız çıktı

Matris gerçek bir brief'te duruyor:
`docs/research/2026-08-05_daerm-trauma-magnitude.md`, somut 4×4 tablo
(`S_res→unc = 0.35`, `S_soc→res = 0.10`, …). Brief bunlara *"empirically
grounded coupling coefficients"* diyor ve **hiçbir atıf vermiyor**.

⇒ **Literatür yolu açık değil.** D-065'in kuralı: kaynaksız sayı kullanılmaz.

### 2. ⛔⛔ Ölçüm 1 — birincil eksen `k` **sabit**

Matrisin hangi satırının uygulanacağını `_pe_target_load_domain`
(`graph.py:823`) belirliyor. Ölçüldü (tohum 9301, 24 ajan, dört kol, iki
nesil, **192 olay**):

| `target_domain` | sayı |
|---|---|
| `resource_load` | **192 / 192** |

⇒ **`S[k][·]` sabit bir satır.** Matris alınsaydı üç ikincil eksen
`0.20·PE, 0.20·PE, 0.20·PE` yerine `0.30·PE, 0.20·PE, 0.35·PE` olurdu —
**bir skaler yerine üç skaler**, ama üçü de hâlâ **aynı PE'nin ölçekli
kopyası**. ⛔ **Boyut yine tek. Matris D-136'nın sorununu çözmüyor.**

### 3. ⭐ `k` neden kilitli — mekanizma

Doğumda üç yükün üçü de `0.0` (`state.py:25–27`) ⇒ berabere ⇒
`dominant_load_domain` **"energy"** döndürüyor ⇒ energy `DAERM_LOAD_DOMAINS`'te
**yok** ⇒ `delta_log` boş ⇒ fallback **`DAERM_DEFAULT_TARGET_DOMAIN =
resource_load`**.

Sonra kilit kendini besliyor: hedeflenen eksen `PE` alıyor, diğerleri
`0.2·PE` ⇒ resource **beş kat** hızlı büyüyor ⇒ dominant kalıyor ⇒ hep o
hedefleniyor. **Doğumdaki bir beraberlik-bozma kuralı ömür boyu birincil
ekseni belirliyor.**

### 4. Ölçüm 2 — matris **eşiği de** kurtarmıyor

`M(PE) = α·max(PE_vec) + (1−α)·mean(PE_vec)`, `α = 0.70`. Hesaplandı:

| | `M(PE)` |
|---|---|
| skaler 0.20 (bugün) | **0.8200 · PE** |
| brief matrisi (`resource` satırı) | **0.8387 · PE** — değişim **+%2.29** |

D-124'ün ölçtüğü tepe değerleri bu çarpanla:

| bugün | matris altında | travma kapısı |
|---|---|---|
| 0.42 | 0.430 | 0.70 |
| 0.52 | 0.532 | 0.70 |
| 0.62 | **0.634** | 0.70 |

⇒ **Hiçbiri kapıyı geçmiyor.** 0.62'yi 0.70'in üstüne taşımak için tekdüze
spillover'ın **0.671** olması gerekirdi — ve §2.7 gereği o değer **etkiye
bakılarak seçilemez**.

### 5. Reddedilen iki alternatif

| | ne | neden reddedildi |
|---|---|---|
| **A** | Brief'in matrisini şimdi al | 12 **kaynaksız** sabit · `magnitude` değiştiği için **fizik değişir** ⇒ eski bütün sayılar karşılaştırılamaz olur · ölçülen kazanç **≈ sıfır** (§2, §4) |
| **B** | Önce `k` kilidini aç, sonra matris | ⚠ **D-135'in trilemması geri geliyor:** `k` yüklerden türüyor, **özdeş ajanların yükleri özdeş** ⇒ `k`'leri de özdeş olur. `k` bir yaşam **içinde** oynardı, ajanlar **arasında** oynamazdı — ve gereken varyans tam olarak ikincisi |

### 6. ✅ Seçilen: **C — skaler kalıyor, sınır ilan ediliyor**

**Sıfır yeni sabit, sıfır kod değişikliği, sıfır fizik değişikliği.**

Ön-kayıta girecek sınır metni:

> **L-x:** Uç nokta `z` dört alanlı bir drift vektörü olarak tanımlıdır,
> ancak bu evrenin fiziğinde birincil eksen `k` bütün olaylarda
> `resource_load`'a kilitlidir (192/192 ölçüldü, D-137) ve ikincil eksenler
> `k`'nin sabit katıdır. Dolayısıyla `z` **etkin olarak tek boyutludur** ve
> alan kimliği hakkında hiçbir iddiada bulunulamaz. Raporlanan kovaryans
> drift'in **büyüklüğü** üzerinedir, **alanı** üzerine değil.

**İddia neyden neye gerileşiyor:** *"yaşam ajanı **nerede** şekillendirdi"*
→ *"yaşam ajanı **ne kadar** şekillendirdi"*. Alan kimliği düşüyor, şiddet
kalıyor.

**Geri çekilmeyenler:** iki kanallı kalıtım (kasa + LoRA) · birincil
karşıtlık `lived ↔ shuffle` (D-131) · aksiyom. Tek değişkenli Price zaten
standarttır ⇒ daralan şey ölçümün **meşruiyeti** değil, iddianın
**zenginliği**.

### 7. ⚠ Yeniden açılma tetiği — bu madde kapanmadı

> **GAP-10 / spillover, `k` ajanlar arasında değişken hale geldiği gün
> yeniden açılır.** Matrisin bütün değeri `S[k][·]`'nin satır satır
> farklılaşmasına bağlı; `k` sabit olduğu sürece matris skalerin üç kopyalı
> hâlidir. Bir tasarım `k`'yi serbest bırakırsa (⚠ §5-B'nin trilemması
> aşılarak), bu kayıt yeniden okunur ve karar **yeniden verilir**.

### 8. ⛔ C'nin **çözmediği** şey — bilerek seçildi

C **boyut** sorununu ilan ediyor, **eşik** sorununu çözmüyor. C2'de
`Var(z) = 0` çıkan 14/18 geçişin sebebi boyut değil **travma kapısıydı**
(tepeler 0.42–0.62, kapı 0.70). ⇒ C uç noktayı **ölçülebilir yapmıyor**,
yalnız neden ölçülemediğini dürüstçe yazıyor.

⚠ **Bu C'ye özgü bir eksiklik değil:** A ve B de eşiği geçirmiyordu (§4).
Üçünün ortak açığı. ⇒ **Eşik, kuyruğa ayrı bir madde olarak eklendi (2.0)**
ve üçüncü ön-kaydın konusudur; sabit değişikliği ister ⇒ §2.7 geçerli.

### 9. Bu ölçümün sınırları

- **Keşifsel, ön-kayıtlı değil.** Kararlar **stub** (LLM yok), PE `fallback`
  kanalından **1.000** sabit, tek tohum (9301).
- ⇒ `k = resource_load` sonucu **bu yapılandırmada** ölçüldü. §3'ün kilit
  argümanı **yapısaldır** (`PE` vs `0.2·PE` her `PE > 0` için geçerli), ama
  **gerçek koşumda doğrulanmadı**.
- ⚠ Ve bugünkü aletle **doğrulanamaz**: `k` hiçbir yere yazılmıyor.
  D-136 `axis_deltas`'ı ekledi, ama o **sonucu** kaydeder, `k`'yi değil.
  ⇒ Kuyruğa **0.2b** olarak eklendi (saf raporlama, ~3 satır).
- §4'ün aritmetiği **kapalı formdur**, koşuma bağlı değil.

---

## D-138 · 2026-08-19 · **Kuyruk 0.2b + 0.3: `k` ve π raporlanıyor** — iki iddianın ikisi de ilk kez **çürütülebilir** hale geldi

**İş:** `EXECUTION_QUEUE.md` maddeleri **0.2b** ve **0.3**. İkisi de **saf
raporlama**, hesap değişmedi, GPU yok. Tek commit'te, çünkü aynı sınıf iş ve
aynı dosyalara dokunuyorlar.

### 1. Neden bu ikisi birlikte

İkisinin de borcu **aynı biçimde**: evren bir nicelik hesaplıyor, kullanıyor,
ve **sonuç dosyasına hiç yazmıyor** ⇒ o nicelik hakkındaki iddia ne
doğrulanabiliyor ne çürütülebiliyor.

| | nicelik | iddianın sahibi | borcun kaynağı |
|---|---|---|---|
| **0.2b** | `k` = birincil eksen (`target_domain`) | **D-137**: *"`k` 192/192 `resource_load`"* — bütün spillover kararı buna dayanıyor | D-137 §9: **stub koşumda** ölçüldü, gerçek koşumda **doğrulanamıyor** |
| **0.3** | π = `precision_weight` | **L13**: *"Precision-PE atıl"* | D-130 §10: ajan satırında `precision` alanı **yok** |

⚠ **0.2b'nin özel bir yükümlülüğü var:** D-137 §7 yeniden açılma tetiğini
*"`k` ajanlar arasında değişkenleşirse"* diye yazdı. Tetiğin ateşlenip
ateşlenmediğini **görmenin tek yolu** `k`'yi kaydetmek. Aksi hâlde tetik
yazılmış ama gözlenemez olurdu.

### 2. Ne yapıldı

| yer | ne |
|---|---|
| `graph.py` · `_record_pe_event` | PE satırı `target_domain` taşıyor — `_apply_prediction_error`'a **verilen** değer, ikinci bir çağrıyla yeniden türetilmiş değil (§2.8) |
| `run_population_experiment.py` · `_primary_axis_counts` | `k` dağılımı; `delta_profile["axes"]["primary_axis"]` |
| `run_population_experiment.py` · `_precision_profile` | π'nin `n_distinct`/`min`/`max`/`mean` + PE_w doygunluğu; ajan satırında **`precision`** |

⚠ **`_precision_audit_from_pe_rows` yeniden yazılmadı, çağrıldı** — protokol-C
koşucusunun denetlediği fonksiyonun **aynısı**. *"π oynuyor mu"* sorusuna iki
yerde iki fonksiyonun cevap vermesi, §2.8'in dört kez yakaladığı kayma.
Yalnız `min`/`max`/`mean` burada, o fonksiyonun döndürdüğü π listesinden
türetiliyor.

⚠ **`k`'nin anahtar kümesi `wins`'inkinden farklı, bilerek:** `energy` durumun
oynayabildiği bir eksen ama güncellemenin **asla hedefleyemeyeceği** bir eksen
(`DAERM_LOAD_DOMAINS`'te yok). İkisini tek listeye düzleştirmek, **imkânsız
bir sıfırı** gözlem gibi raporlamak olurdu.

⚠ **`precision` `delta_profile`'ın içine konmadı:** π, magnitude'ü **besleyen**
PE'yi ağırlıklandırıyor; bir magnitude profilinin içine konsa aynı niceliğin
başka bir kanalı gibi okunurdu.

### 3. K1–K5

| | |
|---|---|
| **K2** | `k` ve π **iki ajanla** uçtan uca test edildi; π'nin filtresiz hâli iki ajanın olaylarını tek ajana yazıyor |
| **K3** | ikisi de `run_population_experiment` üzerinden **sonuç dosyasında** doğrulandı; `n_events == events_lived` bağlandı |
| **K5** | **yedi mutasyon**, her birinin md5'i okundu (öncesi → sonrası → geri yükleme), `-p no:cacheprovider`. **Yedisi de doğru testi kırdı** |
| **K4** | §4'ün sayıları çıktıdan **okundu**; koşum **keşifsel ve karar-stub'lı**, öyle etiketlendi |

Mutasyonlar: `k`'yi argmax kazananı diye raporla · hiç hedeflenmemiş ekseni
listeden düşür · aletlenmemiş satırı `resource_load` say · `target_domain`'i
PE satırına hiç yazma · π sütununu okumayı bırak · π'yi ajana göre filtreleme ·
boş yaşamda `None` yerine `0.0` yaz.

### 4. İlk okuma — ⚠ **keşifsel, kararlar stub, tohum 9301**

| nicelik | değer (3 ajanın üçünde de aynı, 8 olay) |
|---|---|
| `k` | `resource_load: 8` · `social_load: 0` · `uncertainty_load: 0` |
| argmax `wins` | `energy: 7` · `resource: 1` · `social: 0` · `uncertainty: 0` |
| π | `n_distinct = 2` · min **1.0** · max **1.2** · mean 1.15 |
| PE_w doygunluk | **0.75** (6/8) |

- ✅ `k` sonucu **D-137 §2'yi yeniden üretti**, bu kez sonuç dosyasından
  okunarak.
- ✅ `wins` ile `primary_axis` **ayrı şeyler** olduğunu gösterdi: hedef 8/8
  `resource`, ama argmax'ı 7/8 `energy` kazanıyor. Tek alanla raporlansaydı
  ikisinden biri yanlış olurdu.
- ⚠ **π hakkında:** `n_distinct = 2`, L13'ün pilotta gördüğü sayının **aynısı**
  ⇒ ilk okuma L13'ü **destekliyor**, çürütmüyor. Ama π `1.0`'da takılı da
  değil (max 1.2) ⇒ *"tavanda takılı"* tarifi **düzeltilmeli**: π **iki değer
  arasında** oynuyor.

⛔ **PE_w doygunluğu bu koşumdan okunmaz.** Stub kararlar yüzünden ham PE
`fallback` kanalından **sabit 1.000** geliyor; %75'lik doygunluk bunun
sonucudur, evrenin değil. **Gerçek koşumun sayısıdır.**

### 5. Sınırlar

- Koşum **keşifsel, ön-kayıtlı değil**; kararlar **stub**, tek tohum (9301),
  8 olay, iki nesil.
- Üç ajan birebir aynı sayıları verdi — D-129/D-135'in klon sonucu, **yeni
  bulgu değil**.
- Hiçbir alan **hiçbir hesaba girmiyor**. Bunlardan uç nokta seçmek üçüncü
  ön-kaydın işidir ve **etkiye bakılarak yapılamaz** (L9).
- ⇒ **Faz 0 bitti.** Sıradaki iş **Faz 2**, ve önündeki iki ⛔ karar Yasin'in:
  **2.0** (travma eşiği) ve **2.1** (*"en küçük anlamlı etki"* — DR #1'den beri
  açık, Faz 3'ün ön koşulu).

---

## D-139 · 2026-08-19 · 🔍 **Kuyruk 2.1'in seçim uzayı — ve soru yanlış sorulmuş olabilir**

⚠ **Bu bir karar kaydı değil, bir hazırlık kaydıdır.** Karar Yasin'in (D-007).
İki çıktısı var: **(a)** aşağıdaki yeniden çerçeveleme, **(b)** DR brief #12
(`docs/research/2026-08-19_price-sensitivity-and-seed-budget_PLAIN.txt`).

### 1. ⛔ Önce bulunan şey: **DR #1 bu soruyu zaten cevapladı ve cevabı benimsedik**

`CLAUDE.md` ve kuyruk 2.1 *"en küçük anlamlı etki — DR #1'den beri açık,
hâlâ verilmedi"* diyor. Denetim (`RECONCILIATION.md` §G.3) bunun **eksik bir
okuma** olduğunu gösteriyor:

> **"Alınan (S4 slotunu kapatan): SESOI ilan edilmiyor. Yerine bütçe-kısıtlı
> N + duyarlılık analizi (G1, G2, G9)."**

Yani DR #1 *"eşiği söyle"* sorusuna **"söyleme"** cevabını verdi, kaynağıyla
(**Lakens 2022**, *Sample Size Justification*, Collabra: Psychology 8(1):33267,
`10.1525/collabra.33267` — yerel doğrulamada **gerçek ve doğru anılmış**), ve
biz o cevabı **uyguladık**: D-052'de N=40 **bütçeden** seçildi ve
**MDE `d_z = 0.465`** ilan edildi.

⇒ **S4 kapandı, açık kalan S2'ydi** (N'in **değeri**), ve o da **D-052'de
kapandı** — birinci ön-kayıt için.

⇒ ⚠ **Kuyruk 2.1 bugünkü hâliyle, vermemeye karar verdiğimiz bir sayıyı
istiyor.** Bu, 0.1 maddesinin başına gelenin aynısı (D-135): soru sorulduğu
biçimde **düşüyor**.

### 2. ⭐ Ama gerçek bir boşluk **var** — sadece başka yerde

DR #1'den bu yana değişen şey eşik değil, **istatistiğin kendisi**:

| | birinci ön-kayıt (DR #1'in cevapladığı) | üçüncü ön-kayıt (bugün) |
|---|---|---|
| istatistik | eşleştirilmiş fark, Wilcoxon | **Price seçilim terimi** `Cov(w, z)` |
| birim | tohum başına bir sayı | popülasyon içi kovaryans, **geçiş başına** |
| MDE aleti | `d_z`, kapalı form | ⛔ **bilinmiyor** |
| yanlılık | yok | ⚠ **Rice 2008: küçük N'de şişkin** |
| örneklem katmanı | tek (tohum) | **üç iç içe** (tohum · 8 ajan · 2 geçiş) |
| uç nokta | sürekli | **eşikli** ⇒ çoğu hücrede `Var(z) = 0` |

⇒ **Boşluk şu:** *"bütçeden N seç, MDE ilan et"* usulü sağlam — ama bir
**kovaryans** için MDE'nin nasıl hesaplanacağını **bilmiyoruz**, ve yerel
taramada bulamadım.

### 3. Yasin'in önündeki seçim uzayı

| | seçenek | ne demek | maliyet |
|---|---|---|---|
| **A** | 2.1'i **düşür**, DR #1'in cevabı geçerli say | *"SESOI ilan etmiyoruz"* zaten karar; geriye yalnız **tohum sayısı** kalır ve o **bütçeden** seçilir | sıfır. ⚠ Ama MDE'yi **hesaplayamadığımız** için ilan edemeyiz ⇒ D-052'nin yaptığı şeyi yapamayız |
| **B** ⭐ | 2.1'i **yeniden yaz**: *"kovaryans için duyarlılık analizi"* | Asıl boşluk bu. DR #12 tam bunu soruyor | bir DR turu |
| **C** | Permütasyon temelli **ampirik** MDE kendimiz üret | Kapalı form yoksa null'ı permütasyonla simüle edip saptanabilir bölgeyi ölçmek | GPU'suz ama **aletleme** işi; ⚠ ve usulün kabul görüp görmediğini **bilmiyoruz** ⇒ B'nin cevabı bunu söyleyebilir |

⭐ **Claude Code'un önerisi: B, ve C'yi B'nin cevabına göre karara bağla.**
Gerekçe: A dürüst değil — MDE ilan edemeyeceksek *"bütçe-kısıtlı
gerekçelendirme"* yarım kalır, ve Lakens'in yönteminin **çalışan yarısı** tam
olarak duyarlılık analizidir. C ise B'den önce yapılırsa, kabul görmeyen bir
usule aletleme yazma riski taşır.

### 4. DR brief #12 — ne soruluyor, ne sorulmuyor

Dosya: `docs/research/2026-08-19_price-sensitivity-and-seed-budget_PLAIN.txt`
(**saf ASCII doğrulandı**, İngilizce, tablosuz — D-110'un biçimi).

**Altı soru:** Q1 kovaryans için duyarlılık analizi var mı · Q2 üç iç içe
sayımdan **hangisi** tekrarlama birimi · Q3 Rice 2008'in yanlılığı güç
hesabıyla **etkileşiyor mu** · Q4 eşikli uç noktanın **tanımsız** hücreleri
nasıl raporlanır · Q5 bütçe-kısıtlı çerçeve kovaryans için **hâlâ geçerli mi**
· Q6 taklit edilebilecek **yayımlanmış örnek** var mı.

⚠ **Etki sorulmuyor** (L9) — §0 bunu açıkça yazıyor ve kendi sayılarımızı
**bilerek vermiyoruz**.

**DR #1'in iki kusuru brief'e önlem olarak girdi (§1):**
1. *"Determinizm ⇒ `r ≥ 0.85`"* çıkarımı — brief artık **açıkça** yasaklıyor.
   O çıkarım bizim *"koşum-arası gürültü sıfır"* cümlemizden türemişti.
2. Kaynaksız etki bandı — R1/R2/R3 (DOI · **birebir alıntı** · **boşluk
   ilanı** + kaynakça) bağlayıcı olarak yazıldı; D-110'da bu üçü birlikte
   **ilk kez** tutmuştu.

**Ek olarak R5:** her tavsiyenin **nasıl eleştirileceği** isteniyor.
DR #1'in G11'i (*"iptal, birincilin saf olduğunu doğruluyor"*) bir
**non sequitur**'du ve rapora girseydi hakem tam oradan girerdi.

### 5. Bu hazırlığın sınırları

- Yerel tarama **sistematik derleme değil**; *"kovaryans için MDE usulü yok"*
  benim **bulamadığım** anlamına gelir, **yok** anlamına değil. Q1 tam da
  bunu soruyor.
- §1'in hükmü `RECONCILIATION.md` §G.3'ün **kendi cümlesine** dayanıyor,
  yorumuma değil.
- §3'ün maliyet sütunu **tahmindir**, ölçüm değil (K4).

---

## D-140 · 2026-08-19 · **DR #12 mutabakatı** — ⭐ 2.1 **açıldı**, ve şart listesi **dört uydurma alıntı** yakaladı

**Mutabakat tablosu:** `RECONCILIATION.md` **§U** (13 iddia) ·
**Ham cevap:** `docs/research/2026-08-19_DR12-answer-raw.md`

### 1. ⭐⭐ Turun asıl kazancı: Q1 **indirgemeyle** cevaplandı

D-139 boşluğu *"bir kovaryans için MDE nasıl hesaplanır, bilmiyoruz"* diye
tarif etmişti. DR'nin cevabı **problemi çözmüyor, ortadan kaldırıyor**:

> Kovaryansı **tohum başına bir skalere** indir —
> `ΔCov = Cov_lived(w,z) − Cov_shuffle(w,z)` — sonra tohumlar arası
> **Cohen's `d_z`**. Bu noktadan sonra D-052'nin kullandığı makine
> (Lakens 2022, bütçe-kısıtlı N + duyarlılık analizi) **olduğu gibi** çalışır.

⇒ **Yeni istatistik gerekmiyor.** Ve indirgeme tasarımla uyumlu: birincil
karşıtlık zaten `lived ↔ shuffle` (D-131), tohumlar zaten kollar arasında
**eşleştirilmiş**.

⇒ ⭐ **Kuyruk 2.1'in B seçeneği cevaplandı.** Geriye kalan **tohum sayısı**,
ve o **bütçeden** seçilir — tıpkı D-052'de olduğu gibi.

### 2. ⭐ İkinci kazanç: **tekrarlama birimi = tohum**, ve bunu hiç yazmamıştık

Lazic 2010 (`10.1186/1471-2202-11-5`, **Crossref'ten doğrulandı**):
üç iç içe sayımdan yalnız **tohum** gerçek tekrarlama birimi.

- 8 ajan **alt-örneklem**: kovaryansın **ölçüm gürültüsünü** düşürür,
  istatistiksel örneklem büyüklüğünü **artırmaz**.
- G=2 geçiş **zamansal olarak bağımlı** — ✅ **kodla doğrulandı:** varis
  ebeveynin **adapter'ını** (D-102) ve anılarını miras alıyor.

⇒ İkisini bağımsız saymak **pseudoreplication** olurdu. Bu kısıt üçüncü
ön-kayıta **bağlayıcı** olarak girer.

### 3. ⭐⭐ Üçüncü kazanç: eşikli uç nokta için **ön-kayıtlanabilir bir yapı**

DR'nin iki aşamalı çerçevesi (U9):

| | uç nokta |
|---|---|
| **`P_active`** | `Var(z) > 0` olan hücrelerin oranı |
| **`Cov_cond`** | yalnız **aktif** hücrelerde kovaryans |

⇒ D-121'in *"tanımsız ≠ sıfır"* ayrımı ilk kez bir **ön-kayıt yapısına**
dönüşüyor. PROVENANCE_AUDIT aktif oran için **%22** ölçmüştü.

⚠ **Ve DR'nin kendi saldırı vektörü uygulama biçimini belirledi (U10):**
aktif hücreye koşullamak **survivorship bias** yaratır, çünkü eşiği geçmek
**müdahaleden etkilenmiş** olabilir — ki bizde bu **varsayımsal değil**,
`lived`'in daha sık geçmesi tam olarak beklenen şey.
⇒ **`P_active` eş-birincildir, ön-eleme filtresi değil.**

### 4. ⛔ Alınmayan: §3'ün yanlılık iptali (U7) — **yük taşıyan ve kanıtsız**

DR diyor ki: iki kol da N=8 ve aynı tohum olduğu için Rice'ın küçük-N
şişmesi **çıkarmada iptal olur**.

❌ **Kaynaksız, ve boşluğu adreslenmemiş.** Rice'ın bulgusu bir **büyütme**
(*"the effects of selection are actually amplified by random variation in
fitness"*). Büyütme **çarpansal** ise, farklı gerçek seçilime sahip kollar
**farklı oranda** büyür ve **iptal olmaz**. DR toplamsal-mı-çarpansal-mı
sorusuna hiç değinmiyor, ve iddiayı `[OPINION]` diye de işaretlememiş.

⇒ **Açık kalıyor.** Ya kaynaktan çözülür, ya **GPU'suz simülasyonla** ölçülür
(`w` ve `z`'yi bilinen bir üretici modelden örnekle, N=8'de kestirimin
yanlılığını ölç). ⇒ Kuyruğa **2.0b** olarak eklendi.

### 5. ⛔ R2 (birebir alıntı) **kısmen çöktü** — dört alıntı kaynağında yok

⭐ **Kimlikler mükemmel: 4/4 doğrulandı** (Gelman & Carlin ve Lazic
Crossref'ten; Lakens ve Rice zaten yerel doğrulanmıştı). **12 kimlik
hatasından sonra ikinci temiz tur.**

⛔ **Ama alıntılar değil:**

| | kusur |
|---|---|
| **A3, A4** | Lakens'ten *"birebir"* diye verilen iki alıntı **yapısal olarak imkânsız**: biri kendi gövde metninde **kendini** parantezle anıyor, öteki Lakens'ten **üçüncü şahısla** söz ediyor ⇒ ikisi de **Lakens'i anan başka bir metinden** |
| **A5, A6** | Gelman & Carlin'in iki *"tanımı"* **makalede yok** — PDF tam metninde arandı, bulunamadı |

**Makalenin kendi cümlesi:** *"(a) the probability that claims with confidence
have the wrong sign (Type S [sign] error) and (b) the factor by which the
magnitude of an effect might be overestimated (Type M [magnitude] error or
exaggeration ratio)"*.

⚠ **Ve uydurma tanım bir şeyi düşürüyor:** gerçek tanımlar **anlamlılığa
koşullu**; DR'nin sürümünde o koşul **yok**, ki Type S/M'in bütün anlamı odur.

⇒ ⭐ **R2 tam da bunun için konmuştu ve yakaladı.** **Yalnız DOI
doğrulamasıyla dördü de geçerdi** — D-080'in §O'da yazdığı desenin aynısı,
bu kez alıntı düzeyinde.

### 6. ⭐ R5 (saldırı vektörü) — yeni şart, **kalıcı olsun**

Altı bölümün altısında da geldi ve **ikisi benim de yazacağım itirazdı**:
permütasyonun **değiştirilebilirlik** varsayımı (bizde P0-① yüzünden **ihlal**)
ve U10'un survivorship bias'ı. **Maliyeti sıfır, bir turda iki gerçek kusur.**

### 7. ⛔ Yasin'e giden tek karar: **U6 — nesil geçişleri ortalanacak mı**

DR *"G=2'yi tohum başına tek ortalamaya indir"* diyor. ⛔ Bu **D-132 ile
çelişiyor**: adapter sönümünü (6/6 dizide **1.8×–4.8×**) ölçmek istiyoruz ve
ortalama tam onu siliyor. DR'nin kendi saldırı vektörü de bunu söylüyor.

⭐ **Claude Code'un önerisi: ikisi birden.** Ortalama **test eder** (U5'in
pseudoreplication kısıtını karşılar), nesil satırları **raporlamada kalır**
(D-132'nin sönüm sorusunu açık tutar). Çelişki yok — biri istatistik, öteki
betimleme.

### 8. Sınırlar

- U7 **açık** ve §3'ün çaresi ona dayanıyor ⇒ `ΔCov`'un yanlılığı iptal ettiği
  **henüz iddia edilemez**.
- Lakens'in A1/A2 alıntıları **arama sonucuyla** teyit edildi, tam metinden
  değil (yayıncı 403 döndü) ⇒ *"ifade örtüşüyor"* düzeyinde.
- U9'un `P_active`'i **ön-kayıt yapısıdır**, henüz karar değil — 2.2'nin işi.
- Bu tur **hiçbir sabiti** değiştirmedi, **hiçbir kod** yazılmadı.

---

## D-141 · 2026-08-19 · ✅ **KARAR (Yasin): U6 — nesil geçişleri hem ortalanır hem satır satır kalır**

**Soru:** DR #12 §2 (U6) *"G=2 geçişi tohum başına tek ortalamaya indir"*
diyor, gerekçesi pseudoreplication (Lazic 2010). ⛔ Ama bu **D-132 ile
çelişiyor**: adapter sönümü 6/6 dizide **1.8×–4.8×** ölçüldü ve ortalama tam
onu siliyor. DR'nin **kendi saldırı vektörü** de bunu söylüyor.

**Karar:** ⭐ **İkisi birden.**

| katman | ne |
|---|---|
| **test istatistiği** | tohum başına **ortalanmış** `ΔCov` ⇒ U5'in tekrarlama-birimi kısıtı karşılanır, pseudoreplication yok |
| **raporlama** | **nesil başına** Price satırları **kalır** ⇒ D-132'nin sönüm sorusu açık kalır |

⇒ **Çelişki yok:** biri **istatistik** (hipotez testi neyin üstünde yapılır),
öteki **betimleme** (koşum neyi kaydeder). D-112/D-124/D-136'nın deseninin
aynısı — hesaba girmeyen saf raporlama, kararı sonraki ön-kayıta bırakır.

⚠ **Ön-kayıta yazılacak:** nesil satırları **betimleyicidir**; onlardan uç
nokta seçmek **etkiye bakarak seçmek** olur (L9). Sönüm sorusu ayrı bir
ön-kayıt maddesidir, bu koşumun ikincil uç noktası **değildir**.

---

## D-142 · 2026-08-19 · ⭐⭐ **Kuyruk 2.0b: Rice yanlılığı ölçüldü — DR'nin çaresi olmayan bir sorunu çözüyor, ve asıl tehlike başka yerde**

**İş:** `EXECUTION_QUEUE.md` madde 2.0b, D-140 §4'ün açtığı borç.
**GPU yok, evrene dokunulmadı.** ⚠ **Keşifsel, ön-kayıtlı değil.**

### 1. Soru

DR #12 §3: *"iki kol da N=8 ve aynı tohum olduğu için Rice'ın stokastik
büyütmesi çıkarmada iptal olur."* ⛔ **Kaynaksız**, ve **toplamsal mı
çarpansal mı** sorusuna hiç değinmiyor — çarpansalsa iptal **olmaz**.

### 2. Yöntem

⚠ **Mekanizma yeniden yazılmadı:** `allocate_heirs` (turnuva, k=2) ve
`price_partition` **gerçek modülden** çağrıldı (§2.8). Ölçülen şey, deneyin
**fiilen kullandığı** kestirimci.

Üretici model: `z ~ N(0.5, 0.15²)`, `f_agent = β·z + N(0, 0.15²)`.
`β` tek başına seçilimin `z`'ye ne kadar nişanlandığını belirliyor; **β = 0
null**. N=8, **R = 20 000** tekrar. Referans: `Cov(E[w], z)` — yani *"uygunluk
sabit ve bilinen olsaydı"* hâli, ki Rice'ın klasik Price için söylediği
varsayım tam budur.

### 3. ⛔ Sonuç 1 — **işaretli kestirimci null'da yansız**

| β | `E[Cov]` | `Cov(E[w],z)` | oran | offset |
|---|---|---|---|---|
| **0.00** | **0.000372** | 0.001713 | — | −0.001341 |
| 0.25 | 0.019996 | 0.021765 | 0.919 | −0.001769 |
| 0.50 | 0.037634 | 0.037185 | **1.012** | +0.000449 |
| 1.00 | 0.059952 | 0.056923 | **1.053** | +0.003029 |
| 2.00 | 0.075681 | 0.074690 | **1.013** | +0.000991 |

**β = 0'da `E[Cov] = 0.000372`, `SE = 0.000419` ⇒ sıfırdan 0.89 SE**
(%95 GA `[−0.000448, +0.001192]`) ⇒ **sıfırdan ayırt edilemiyor**.

**Oran β ≥ 0.5'te 1.01–1.05** ⇒ **çarpansal büyütme de yok**.

Eşli fark, iki kol da null: `E[ΔCov] = −0.000603`, **−1.02 SE** ⇒ sıfır.

⇒ ⭐ **DR'nin §3'ü olmayan bir sorunu çözüyor.** İşaretli kovaryansta
**iptal edilecek bir yanlılık yok**; çaresi zararsız ama **gerekçesi yanlış**.
⇒ **U7 nihai olarak alınmıyor** — ama sonucu D-140'takinden **daha iyi**:
endişe geçersiz çıktı.

### 4. ⭐⭐ Sonuç 2 — **asıl tehlike magnitude kanalında, ve DR bunu hiç görmedi**

| β | `E[Cov]` (işaretli) | **`E[\|Cov\|]`** |
|---|---|---|
| 0.00 (**null**) | 0.000372 | **0.046154** |
| 0.50 | 0.037634 | 0.053446 |

⛔ **Null'da `E[|Cov|] = 0.046` — sıfır değil.** Ve gerçek fark **0.0355**
iken `|Cov|` farkı yalnız **0.0073** çıkıyor ⇒ **4.86 kat sıkışma**.

Sebep: gürültü tabanı (`SD = 0.059`) etkiden büyük; mutlak değer alınca
taban **eklenmiyor, yutuyor**.

⇒ **Bir uç nokta `|Cov|` ya da `z` vektörünün **normunu** alırsa: null sıfır
değildir ve gerçek etki ~5 kat küçük görünür.**

✅ **Bugün temiziz:** `price_partition` alan başına **işaretli** değer
döndürüyor ve `analyze_population_run` onu `+.6f` ile **işaretiyle**
raporluyor — hiçbir yerde norm/mutlak değer alınmıyor (denetlendi).

⚠ **Ama bu bir tesadüf değil, korunması gereken bir özellik** ⇒ üçüncü
ön-kayıta **sınır** olarak yazılır: *"uç nokta `Cov`'un **işaretli** hâlidir;
mutlak değer veya vektör normu alınamaz — null'ı sıfırdan uzaklaştırır ve
etkiyi ~5 kat sıkıştırır (D-142)."*

⚠ Ve bu, D-002'nin eski birincilinin (`L2` mesafesi, §G.2) neden kırılgan
olduğuna **bağımsız bir açıklama** getiriyor.

### 5. Sınırlar

- **Tek üretici model** (Gauss `z`, doğrusal `f_agent` + Gauss gürültü),
  turnuva k=2, N=8. **Kanıt değil, bu model altında ölçüm.**
- Referans `Cov(E[w], z)` da Monte Carlo ile kestirildi (500 dış × 400 iç)
  ⇒ oran sütununun hatası `E[Cov]`'unkinden **büyük**; β=1.00'daki 1.053
  buna binebilir.
- Rice'ın sonucu **uygunluğun tam dağılımı** hakkında; buradaki model
  uygunluğu ortalama+gürültü olarak kuruyor ⇒ Rice'ın en genel koşulunu
  **kapsamıyor olabilir**. ⇒ Sınır ilanı (D-140) **kalkmıyor**, yalnız
  *"eşleştirme iptal ediyor"* gerekçesi **düşüyor**.
- Hiçbir sabit değişmedi, hiçbir kod yazılmadı.

### 6. Yeniden üretim

⚠ **Sonda commit edilmedi** — §2.7 gereği keşifsel ölçüm scratchpad'den
koşulur, ön-kayıtlı alete girmez (`dau_runs/` zaten git'te takipli değil).
Yeniden kurmak için gereken her şey §2'de; kullanılan tohumlar:
tek-kol taramasında **`4242 + round(100·β)`**, eşli farkta kol A **777**,
kol B **999**, deterministik referansta **`4342 + round(100·β)`**
(= tek-kol tohumu + 100 000). `PYTHONHASHSEED=0`.

---

## D-143 · 2026-08-19 · ✅ **KARAR: travma eşiği DEĞİŞMİYOR — `P_active` eş-birincil uç nokta olur** (kuyruk 2.0)

**Yetki:** ⚠ Bu madde kuyrukta **⛔ KARAR** işaretliydi ve D-007 gereği
Yasin'indir. **Yasin 2026-08-19'da açıkça devretti** (*"önerdiğin yolla
kararları al"*). Karar Claude Code tarafından alındı, **devir kayda geçti**.

⛔ **Ve karar hiçbir sayı seçmiyor** — aşağıdaki gerekçenin bütün ağırlığı
tam da bunun üzerinde.

### 1. ⛔ Önce kendi önerimi geri çekiyorum

Bir önceki turda seçenek (c)'yi — *"eşik-öncesi bir uç nokta tanımla"* —
**en umut verici** diye sunmuştum. **Yanlıştı:** o seçenek zaten
**ön-taahhüt edilmiş, ölçülmüş ve reddedilmiştir**.

| kayıt | ne |
|---|---|
| **D-125/D-128** | Kural **koşumdan önce** yazıldı: *"4 hücrenin en az 3'ünde `Var(to_landmark.max) > 0` ⇒ aday girer"* |
| **D-129** | Sonuç **2/4** ⇒ ⛔ **ADAY GİRMEZ**. `lived` 2/2 tanımlı, `null` 0/2 dejenere |

⚠ **Ve "ama D-131 `null`'ı betimleyiciye indirdi, `lived` 2/2 geçiyor" denemez.**
D-129 §4 tam bu tuzağı **önceden** adlandırmış:

> *"Yalnız `lived` koşulsaydı sonuç 2/2 = %100 çıkacak, aday 'geçti' diye ilan
> edilecek ve gerçek deneyde `null` hücreleri yine boş çıkacaktı."*

Aynı sayıları, sonradan değişmiş bir kol yapısıyla yeniden okumak **kuralı
sayıyı gördükten sonra yeniden yazmaktır**. ⇒ (c) **kapalı**.

### 2. Seçenek uzayı — üçü de kapalı çıktı

| | seçenek | neden kapalı |
|---|---|---|
| **a** | Eşiği indir | ⛔ **§2.7.** Dağılımı **zaten gördük** (tepeler 0.39–0.64) ⇒ bugün seçilecek her değer **etkiye bakılarak** seçilmiş olur. ⚠ Ve sabitlerden türetilebilecek tek doğal eşitsizlik **bağlamıyor**: *"kapı azami PE ile ulaşılabilir olmalı"* ⇒ `M(1.0) = 0.8200 ≥ 0.70` **zaten sağlanıyor** (pay 0.12; kapıyı geçmek için ham PE ≥ **0.8537**). Ölçüldü, uydurulmadı |
| **b** | `magnitude` formülünü değiştir | ⛔ **Fizik değişir** ⇒ bugüne kadarki bütün sayılar karşılaştırılamaz olur; üstelik yeni formül de **tepelerin nerede durduğuna bakılarak** seçilirdi |
| **c** | Eşik-öncesi uç nokta | ⛔ **§1** — ön-taahhüt edilmiş, ölçülmüş, reddedilmiş |

### 3. ✅ Seçilen: **(d) — eşiği düzeltme, geçme oranını ÖLÇ**

> **`DELTA_THRESHOLD_DEEP = 0.70` değişmiyor.** Bunun yerine, eşiğin
> **geçilme oranı** `P_active` **eş-birincil uç nokta** olarak ön-kayıta
> yazılır (DR #12 / U9, D-140 §3).

| | uç nokta |
|---|---|
| **`P_active`** | `Var(z) > 0` olan hücrelerin oranı — **eş-birincil** |
| **`Cov_cond`** | yalnız **aktif** hücrelerde `ΔCov` (D-140 §1'in indirgemesi) |

⭐ **Neden bu, bir kaçamak değil:**

1. **Sıfır yeni sabit, sıfır fizik değişikliği, sıfır ön-taahhüt ihlali** —
   a/b/c'nin üçünün de düştüğü yerlerden hiçbirine dokunmuyor.
2. **Sorunu ölçüme çeviriyor.** *"Hücrelerin %78'i boş"* bir arıza değil,
   **evrenin bir özelliği**; `P_active` onu bir arıza olmaktan çıkarıp
   **raporlanan bir nicelik** yapıyor.
3. **Dışarıdan geldi:** DR #12 bunu bizim eşik sorunumuzu bilmeden önerdi
   (U9), ve D-140'ta zaten benimsenmişti. Bu karar onu **uygular**, yeni bir
   şey icat etmez.
4. **D-121 ile aynı çizgide:** *"tanımsız"* ile *"sıfır"* ayrımı zaten
   verilmiş bir karardı; `P_active` o ayrımın **sayısal hâli**.

⚠ **Ve U10'un kısıtı bağlayıcı:** `P_active` **ön-eleme filtresi değildir**.
Eşiği geçmek **müdahaleden etkilenmiş** olabilir — bizde bu varsayımsal değil,
`lived` kolunun daha sık geçmesi tam olarak beklenen şey ⇒ `P_active`
**kendisi bir sonuçtur** ve öyle raporlanır.

### 4. Bunun bedeli — açıkça

- **Aktif hücre oranı ~%22** (PROVENANCE_AUDIT) ⇒ `Cov_cond`'un dayandığı
  hücre sayısı az; **güç 2.2'nin duyarlılık analizinde** açıkça çıkacak ve
  **ilan edilecek** (D-140 §1'in `ΔCov` makinesi).
- ⇒ **Bu karar uç noktayı güçlü yapmıyor**; onu **dürüst** yapıyor.
  *"Ölçemedik"* ile *"ölçtük, yoktu"* ayrımı `P_active` sayesinde ilk kez
  **tek bir sayıyla** kuruluyor.

### 5. `to_landmark.max` yeniden ne zaman açılır

⏸ **Kapanmadı, ertelendi.** Yeniden açılma koşulu **üç şartın üçü birden**:

1. **Yeni** bir ön-taahhüt yazılır (D-125 deseni: koşumdan **önce** commit),
2. sonda **`shuffle` kolunu içerir** — D-129'un sondası `lived null` koşmuştu,
   bugünkü birincil karşıtlık ise `lived ↔ shuffle` (D-131) ⇒ mevcut veri o
   karşıtlık hakkında **hiçbir şey söylemiyor**,
3. okuma kuralı **taze veriye** uygulanır; D-129'un sayıları **tekrar
   okunmaz**.

### 6. Sınırlar

- Karar **devredilmiş yetkiyle** alındı (§Yetki). Yasin geri almak isterse
  bu kayıt **tek yerde** duruyor.
- `P_active`'in **eşiği yok ve olmayacak**: *"kaç aktif hücre yeterli"*
  sorusu bir SESOI sorusudur ve DR #1'den beri cevabımız **eşik ilan
  etmemek** (§G.3) ⇒ bütçeden tohum, **ilan edilmiş MDE**.
- Bu kayıt **hiçbir kod değiştirmiyor**; `P_active` zaten ölçülebilir
  (`selection_estimable`, D-121) — 2.2'nin işi onu **ön-kayıta yazmak**.

---

## D-144 · 2026-08-19 · 📝 **Üçüncü ön-kayıt taslağı yazıldı** (kuyruk 2.2) — **beş slot kapalı, biri Yasin'de**

**Belge:** `docs/PREREGISTRATION_3.md` (342 satır) · **⛔ KİLİTLİ DEĞİL.**

### 1. Ne yapıldı

Bugünkü sekiz kaydın (D-136…D-143) çıktıları tek bağlayıcı belgeye toplandı.
**Hiçbir yeni karar alınmadı** — taslak, verilmiş kararları **yazıya geçiriyor**.

| slot | durum | dayanak |
|---|---|---|
| **1** Uç noktalar | ✅ `ΔP_active` + `ΔCov_cond`, ikisi de **eş-birincil** | D-143, D-140 |
| **2** Test | ✅ eşleştirilmiş Wilcoxon · **birim tohum** · Holm (α=0.025) | D-140, D-141 |
| **3** **Tohum sayısı `S`** | ⛔ **AÇIK** | — |
| **4** Geçerlilik kapıları | ✅ V1–V6 | — |
| **5** Sonuç sınıfları + rapor dili | ✅ dört sınıf, bağlayıcı kalıp | D-140/U11 |
| **6** Alet kimliği | ⏳ kilitte donacak | — |

**On dokuz sınır ilan edildi (L1–L19).**

### 2. ⛔ Neden `S` açık bırakıldı

Yasin yetkiyi devretmişti (D-143), ama `S` **metodolojik bir seçim değil**:
Yasin'in makinesinde **20–36 saat** GPU taahhüdü, ve **tek atışlık** (kilitten
sonra tohum eklenemez). ⇒ Geri döndürülemez bir kaynak kararı; onayı ayrıca
alınır.

### 3. Güç hesabı — ⭐ **yöntem bilinen bir sonuçla doğrulandı**

Exact noncentral-t MDE, sonra Wilcoxon `ARE = 3/π`. ⚠ **Önce D-052'nin
sayıları yeniden üretildi:** `N=32 → 0.5113 / 0.5232` · `N=40 → 0.4543 /
0.4649` — D-052'nin yazdığıyla **birebir**. Yöntem doğrulanmadan yeni sayı
üretilmedi (K4).

| S | GPU saat (2.3× aralık) | MDE α=.05 | **MDE α=.025 (Holm)** |
|---|---|---|---|
| 8 | 16 (11–24) | 1.183 | 1.370 |
| **10** | 20 (13–30) | 1.019 | **1.165** |
| **12** | 24 (16–36) | 0.909 | **1.032** |
| 15 | 30 (20–46) | 0.796 | 0.897 |

**Öneri: `S = 12`.** S=10→12 MDE'yi %11 indirip 4 saate mal oluyor;
S=15 altı saat daha alıp yalnız 0.897'ye iniyor. ⚠ **Bütçe önerisi, bilimsel
gerekçe değil.**

⚠ **MDE'ler büyük ve bu bilerek yazıldı:** `d_z ≈ 1.0` **büyük** bir etkidir;
tasarım mütevazı etkileri **göremez** ve bu §7'de ilan edildi.

### 4. ⭐ Taslak yazılırken çıkan **belirtilmemiş** bir nokta

`selection_estimable` bayrağı **alan başına** yazılıyor (`reproduction.py:255`)
⇒ *"hücre aktif"* tanımı **hangi alan** olduğunu söylemeden eksik.

**Kapatıldı: birincil alan `energy`.** Gerekçe **mekanik**, sonuca bakmıyor:

- `resource` — krizin sabit alanı, kriz **bütün kola aynı anda** vurur ⇒
  herkes aynı skarı alır ⇒ hücre içi bilgi yok (L14);
- `social`/`uncertainty` — argmax'ı hiç kazanmıyorlar (C2'de **sıfır kez**);
- ⇒ `energy` **bireysel kanalın tek yazdığı alan**.

⚠ Bedeli ilan edildi: C2'de `energy` 216 okumanın **11'inde** doluydu ⇒
`P_active` **düşük** beklenmeli. Ve `Cov_cond` **aynı alanda** okunur —
farklı alanlar seçilseydi iki eş-birincil **farklı şeyler** hakkında olurdu.

⚠ Ayrıca: alan anahtarı **hiç yazılmamışsa** hücre **inaktiftir** —
*"eksik veri"* değil **gözlem** (D-121'in ayrımı).

### 5. Doğrulananlar (§2.2 — belgeye değil dosyaya güven)

- `selection_estimable` **zaten** sonuç dosyasında (`price_partition` yazıyor,
  `analyze_population_run` okuyor) ⇒ `P_active` için **kod değişikliği yok**.
- CLI bayrakları doğrulandı: `--seeds` (liste), `--n-agents`,
  `--n-generations`, `--events`, `--arms`, `--fresh-pasture`, `--lora`.

### 6. Sınırlar

- Taslak **bağlayıcı değil**; kilit kuyruk 2.3'te.
- §7'nin maliyet aralığı C2'den **ölçülmüş** yayılıma dayanıyor (2.3×), ama
  yeni fizik yok ⇒ **tahmin**, ve D-126/D-129'da süre tahminim **iki kez
  tutmadı**.
- L3'ün `192/192` sayısı **karar-stub'lı** koşumdan; gerçek koşumda `k` artık
  kaydediliyor (D-138) ⇒ **doğrulanabilir**.

---

## D-145 · 2026-08-19 · ⛔⛔ **KİLİT ÖNCESİ DENETİM: taslak KİLİTLENEMEZ** — birincil uç nokta yapısal olarak test edilemiyor

**Yetki:** Yasin, 2026-08-19: *"daha önceki runları, brieflerimizi ve
brieflerde kullandığımız kısımları kontrol et… daha önce yaptığımız hatalara
düşmeyelim."* ⇒ Kilit **durduruldu**.

⚠ **Denetim, D-144'ün taslağında kendi yazdığım üç kusuru buldu.** Kilit tek
atışlıktır; bunlar kilitten sonra bulunsaydı **24 GPU saati** boşa giderdi.

### 1. Geçen kontroller

| | kontrol | sonuç |
|---|---|---|
| ✅ | Tohum bloğu 9916+ (I0.7) | temiz — diskteki en yüksek **9915**, 650 adapter dizini tarandı |
| ✅ | Maliyet tabanı | C2 = **3 tohum × 3 kol**, `run_quality=clean` ⇒ ~2 sa/tohum doğrulandı |
| ✅ | `P_active` **kod değişikliği istemiyor** | `selection_estimable` zaten sonuç dosyasında |
| ✅ | Dış `timeout` yok (D-126) · `PYTORCH_CUDA_ALLOC_CONF` elle verilmiyor (D-116) · CLI bayrakları | taslakta doğru |

### 2. ⛔ Kusur 1 — seçtiğim birincil alan neredeyse hiç yazılmıyor

D-144 §4'te birincil alanı **`energy`** ilan etmiştim, gerekçesi mekanikti.
**C2'nin gerçek çıktısı okundu** (15 Price satırı, ⚠ **kol karşıtlığı
hesaplanmadı** — L9):

| alan | yazıldı | tanımlı |
|---|---|---|
| `energy` | **4 / 15** | **1** |
| `resource` | 12 / 15 | 3 |

⇒ **`energy` birincili C2'de 15 hücrenin 1'inde ölçülebilirdi.**

### 3. ⛔⛔ Kusur 2 — hangi alanın yazıldığı **kola değil TOHUMA** bağlı

| tohum | kriz olayı / nesil | `z` alanları |
|---|---|---|
| 9911 | 75 · 32 · 85 | `resource` (+1 `energy`) |
| **9912** | **0 · 0 · 0** | **`energy`** |
| 9913 | 120 · 96 · 72 | `resource` |

⇒ ⭐ **Mekanizma kesin: kriz olan tohumda `z` `resource`'a, kriz olmayan
tohumda `energy`'ye yazılıyor.** Kriz `CRISIS_AFFECTED_DOMAIN`'e sabit
(L14), ve krizin olup olmaması **nişin, yani tohumun** özelliği.

⇒ ⛔ **Sabit bir birincil alan, tohumların bir kısmını TAMAMEN dışarı atar.**
`energy` seçilirse kriz tohumları, `resource` seçilirse kriz-olmayan tohumlar
düşer — ve `resource` ayrıca **confounded** (L14).

⚠ **Bunu D-144'te göremezdim çünkü bakmamıştım.** `selection_estimable`'ın
**alan başına** yazıldığını fark edip alanı ilan ettim, ama **hangi alanın
hangi koşulda yazıldığını** ölçmedim. §2.2'nin ihlali: belgeye güvendim,
dosyaya bakmadım.

### 4. ⛔⛔ Kusur 3 — `ΔP_active` üzerinde Wilcoxon **yapısal olarak çalışmıyor**

`P_active ∈ {0, ½, 1}` ve çoğu tohumda iki kol da **aynı** ⇒ `ΔP_active = 0`.
**Wilcoxon sıfır farkları ATAR** ⇒ etkin N = sıfır-olmayan çift sayısı.

Reddedebilmenin **matematiksel** alt sınırı (çift yönlü):

| sıfır-olmayan çift | mümkün en küçük p | α=0.05 | **α=0.025 (Holm)** |
|---|---|---|---|
| 6 | 0.0312 | EVET | **hayır** |
| **7** | 0.0156 | EVET | **EVET** |

C2'nin desenine göre (alan tohuma bağlı) tohumların ~⅓'ü bilgi taşıyor:

| S | E[sıfır-olmayan] | **P(n ≥ 7)** | GPU saat |
|---|---|---|---|
| **12** (önerim) | 4.0 | ⛔ **0.066** | 24 |
| 18 | 6.0 | 0.391 | 36 |
| 24 | 8.0 | 0.737 | 48 |
| 30 | 10.0 | 0.916 | 60 |

⇒ ⛔⛔ **S=12'de testin reddedebilme ihtimali %6.6.** Bu bir **güç** sorunu
değil — test **yapısal olarak** sonuca ulaşamıyor. §7'nin MDE tablosu
`d_z = 1.032` diyordu ve **yanıltıcıydı**: o tablo sürekli, bağlaşımsız bir
değişken varsayıyor; `ΔP_active` üç değerli ve **sıfır-şişkin**.

⇒ ⚠ **K4'ün yeni bir biçimi:** *sayıyı okudum ama **dağılımının biçimini**
sormadım.*

### 5. ⛔ Kusur 4 — bütün bir kol-tohumun **hiç** Price satırı olmayabilir

`null` s9912: **0/2** geçişte Price satırı var. Taslağım *"alan anahtarı
yoksa hücre inaktif"* diyordu ama **satırın kendisi yoksa** ne olacağını
söylemiyordu. Üçüncü bir kategori: **hücre hiç oluşmadı**.

### 6. ⭐ Çözüm kayıtta zaten varmış — **P7-b / D-096**

`PREREGISTRATION_2.md` §1: *"ilk koşum **kestirimdir, hipotez testi
değildir**"* (P7-b / D-096). C2 o damgayla koştu.

⇒ **Aynı damga burada da doğru cevap.** Bu bütçede `Cov(w,z)` üzerinde
hipotez testi **yapılamaz**; yapılabilecek şey **kestirim**:
`P_active` ve `ΔCov` **güven aralıklarıyla** raporlanır, **p-değeri yok,
α yok, Holm yok**, ve `S` **kesinlik** için seçilir, güç için değil.

⚠ Bu Lakens'le **çelişmiyor**: bütçe-kısıtlı gerekçelendirme + *"neyi
kestirebiliriz"* ilanı aynı çerçevenin parçası.

### 7. Yasin'in önündeki seçim — ⛔ kilit bunlardan biri seçilmeden atılmaz

| | seçenek | maliyet | ne verir |
|---|---|---|---|
| **A** ⭐ | **Kestirim koşumu**, S=12 | 24 sa (16–36) | `P_active` + `ΔCov` **güven aralıklarıyla**; hipotez testi **yok**, ve bu **ilan edilir** |
| **B** | Test koşumu, S ≥ 30 | **60 sa (40–91)** | Reddedebilme ihtimali %92 — ⚠ ama gerçek güç MDE tablosundan **düşük** (sıfır şişmesi) |
| **C** | Uç noktayı düzelt | — | ⛔ **§2.7 + D-143**: eşik/alan artık **etkiye bakılarak** seçilemez |

⭐ **Claude Code'un önerisi: A.** Gerekçe: B'nin 60 saati, **hâlâ** üç değerli
ve sıfır-şişkin bir uç noktaya harcanıyor; C yasak. A ise C2'nin dersini
tekrarlamak yerine **ölçüyor** ve hiçbir şey vaat etmiyor.

⚠ **A'nın bedeli açıkça:** üst üste **üçüncü** kestirim koşumu olur ve
*"anlamlı"* kelimesi yine kullanılamaz.

### 8. Sınırlar

- §2–§5'in sayıları C2'nin **tek** koşumundan (3 tohum) ⇒ *"tohumların ⅓'ü"*
  oranı **3 tohumluk bir gözlem**, kestirim değil.
- ⚠ **Kol karşıtlığı hiçbir yerde hesaplanmadı** (L9) — okunan yalnız
  *"uç nokta canlı mı"*.
- Taslak (`PREREGISTRATION_3.md`) **kilitlenmedi** ve §3/§4/§7 bu kayıttan
  sonra **yeniden yazılacak**.

---

## D-146 · 2026-08-19 · ⭐⭐ **Ölçüldü: darboğaz bütçe değil, uç noktanın EŞİKLİ olması**

**Soru (Yasin):** *"şu an kestirim koşumu bizi hedeflediğimiz şeye sağlıklı
olarak ulaştıracak mı?"* ⇒ Cevap vermek için ölçüldü. **GPU yok**, C2'nin
mevcut çıktısından. ⚠ **Yalnız tanımlılık okundu; kol karşıtlığı
HESAPLANMADI** (L9).

### 1. Ölçüm — aynı koşum, üç nicelik, aynı hücreler

| nicelik | hücre içi varyansı olan hücre |
|---|---|
| **`F_agent`** (seçilim **girdisi**) | **21 / 27 = %78** |
| **`energy_mean_over_life`** (sürekli) | **21 / 27 = %78** |
| ⛔ **`z`** (eşikli drift, Price alanı) | **4 / 16 = %25** |

### 2. ⭐⭐ Ne söylüyor

**Seçilim makinesi çalışıyor.** `F_agent` hücrelerin **%78'inde** ayrışıyor ⇒
turnuva yazı-tura değil, `w` değişken, Price'ın girdisi **canlı**.

⛔ **Ölü olan tek şey `z`.** Ve sebebi tek bir tasarım seçimi: **`z` eşikli**.
Aynı yaşamlardan okunan **sürekli** bir nicelik **üç kat** daha çok hücrede
tanımlı.

⇒ ⛔ **Darboğaz `S` değil.** Tohum eklemek, hücrelerin **%75'inde tanımsız**
olan bir niceliği daha çok kez tanımsız ölçmektir. ⇒ **Kestirim koşumu da
hedefe götürmez** — D-145 §7'nin **A seçeneği zayıfladı**.

### 3. ⇒ Tabloya **D** seçeneği giriyor: **sürekli uç nokta**

⚠ **Bu L9'u ihlal etmez.** L9 uç noktayı **etkiye** bakarak seçmeyi yasaklar;
buradaki ölçüt **tanımlılık** — niceliğin **var olup olmadığı**. Ön-kayıtın
geçerlilik kapıları (`Var(F_agent) > 0`) zaten aynı mantıkla yazılmıştı, ve
D-125'in sondası tam bu türdendi.

⛔ **Ama D henüz hazır değil — iki gerçek engeli var:**

1. **`energy_mean_over_life` doğrudan kullanılamaz:** o **pozitif kontroldür**
   (D-121). Aynı niceliği hem uç nokta hem kontrol yapmak kontrolü yok eder.
2. **`to_landmark.max` de doğrudan kullanılamaz:** D-129'da **2/4** ile
   reddedildi, ve D-143 §5 yeniden açılmasını **üç şarta** bağladı — en
   önemlisi sondanın **`shuffle` içermesi** (D-129'unki `lived null`'dı).

⇒ **D'nin somut biçimi bir sonraki adımın işi**, ve **yeni bir ön-taahhüt +
yeni bir sonda** ister.

### 4. Sınırlar

- Tek koşum (C2, **3 tohum**) ⇒ %78 ve %25 **gözlem**, kestirim değil.
- `z`'nin paydası 16 (alan bazında), diğerlerininki 27 (hücre bazında) ⇒
  oranlar **aynı tabana** oturmuyor; ⚠ ama fark (%78 ↔ %25) bu farkı
  taşıyamayacak kadar büyük.
- Hiçbir kol karşıtlığı, kovaryans veya etki büyüklüğü hesaplanmadı.

---

## D-147 · 2026-08-19 · 🔍 **KUSUR AVI — üç bulgu, üçü de koşumu sessizce bozabilecek türden**

**Yetki:** Yasin, 2026-08-19: *"avlan"*. Av alanları D-146'da önerildiği gibi:
**(1)** analiz aracı, **(2)** kapı envanteri. **GPU yok.**

⚠ **Hiçbiri düzeltilmedi** — üçü de gerçek koşumu okuyacak aracı ya da
ön-kaydı değiştiriyor ⇒ §2.3, karar Yasin'in.

### 0. ⚠ Önce kendi ölçüm aracım yanıldı

İlk taramam *"32 testin 0'ı çok-tohumlu"* dedi. **Yanlıştı** — regex'im
fixture'ları görmüyordu. Dosya okununca `_multi_seed` (3 tohum × 3 kol)
fixture'ı çıktı, docstring'i **D-127'yi ve K2'yi** anıyor. ⇒ **K5'in dersi
üçüncü kez:** güvenilmez olan kod değil **ölçüm aracımdı**. Aşağıdaki üç
bulgu bu yüzden **gerçek çıktı üzerinde** doğrulandı, regex'le değil.

### 1. ⛔ AV-1 — rapor, satırın **hangi tohuma** ait olduğunu söylemiyor

`analyze_population_run` C2 üzerinde koşuldu. **Level 0** ve **Level 1**
listeleri yalnız `kol` + `nesil` etiketliyor:

```
  lived    gen1: Var(w)=1.2500 ...   ← s9911
  lived    gen1: Var(w)=1.5000 ...   ← s9912
  lived    gen1: Var(w)=2.2500 ...   ← s9913
```

Aynı etiket **üç kez**, farklı sayılarla, ve okuyan hangisinin hangi tohum
olduğunu **bilemiyor**. Aynı kusur `Distinct z`, `Level 1 selection` ve
`pozitif kontrol` listelerinde de var.

⭐ **Level 2 ve Level 3 tohumu YAZIYOR** (`lived s9911 …`, `s9911 gen1:`)
⇒ D-127 **toplama** kusurunu düzeltmiş ama **listeleme** kusurunu
düzeltmemiş. Yarım kalmış bir düzeltme.

⚠ Sayılar **çökmüyor** (27 satırın 27'si basılıyor) ⇒ veri kaybı yok,
**atfedilebilirlik** kaybı var. Rapor bir insanın koşumu yargılaması için.

### 2. ⛔⛔ AV-2 — Level 3'ün *"kol mesafesi"* bir **yapısal yokluğu** büyüklük sanıyor

**Ölçüldü ve tam olarak doğrulandı** (s9912, nesil 2):

| kol | `mean_z` |
|---|---|
| `lived` | `{energy: 0.087899}` |
| `null` | `{}` — **alan hiç yok** |
| `shuffle` | `{}` |

Rapor: `‖lived − null‖ = 0.087899`.
⇒ **Mesafenin TAMAMI `lived`'in kendi değeri.** `null` o alanda hiçbir okuma
taşımıyor; `l2` yokluğu **0** sayıyor (`analyze_population_run.py:237`) ve
fark, bir karşılaştırma değil **tek kolun büyüklüğü** oluyor.

⚠ **Bu yeni bir kusur değil — 2026-08-11'de görülmüştü** ve
`RECONCILIATION.md` **§G.2** onu tek-soy tasarımı için yazmıştı:

> *"L2 mesafesi bir **kategorik uyuşmazlığı** büyüklük farkı gibi okuyor."*

⛔ **Popülasyon aracında hâlâ canlı**, ve bu kez **sayısı var**.

⚠ Ve **D-142 bunu ağırlaştırıyor**: L2 bir **magnitude kanalıdır**, null'ı
sıfır değildir ve etkiyi ~5 kat sıkıştırır.

### 3. ⛔⛔ AV-3 — **26 değişmezin yalnız 6'sı** popülasyon yolunda bağlı

C2'nin raporladığı: `I0.3 · I0.4 · I0.6 · I0.7 · I1.1 · I4.1`.
**Bağlı olmayan 20:** `I0.1 I0.2 I0.5 I1.2 I1.3 I1.3b I1.4 I1.5 I2.1 I2.2
I2.3 I3.1 I3.2 I3.3 I3.4 I4.2 I5.1 I5.2 I5.3 I5.4`.

**İkisi doğrudan bu deneyin iddiasına dokunuyor:**

| kapı | ne yapar | neden önemli |
|---|---|---|
| **I4.2** (ABORT) | *"Gen2 öncesi RNG durum hash'i üç kolda aynı"* — GAP-12 | Koşum **çok nesilli**; nesiller arası determinizmi kapıya bağlayan tek şey buydu ve **bağlı değil** |
| **I5.4** (FLAG) | *"Inherited somatic scale gen2'de ≥1 kez uygulandı"* — GAP-3 | ⛔ **İddiamız kalıtım hakkında**, ve sembolik kanalın varise **ulaştığını** doğrulayan kapı bu |

⚠ **I2.1** (*"kollar birbirinin aynısı değilse dur"*, ABORT) bağlı değil —
ama popülasyonda **gen1 tasarım gereği özdeş** ⇒ olduğu gibi bağlansa
**meşru bir durumda abort ederdi**. ⇒ *"eksik"* değil **uyarlanmamış**, ve
bunu hiç kimse yazmamış.

⇒ ⛔ **Ve bu benim taslağıma doğrudan dokunuyor:** `PREREGISTRATION_3.md`
§5'in **V1 kapısı** *"preflight **6/6**"* diyor. Bu **tam kapsam gibi
okunuyor**, oysa **6/26**. Bir hakem bunu böyle okur. **V1 yeniden
yazılmalı.**

### 4. Yasin'e giden üç karar

| | ne | sınıf |
|---|---|---|
| **AV-1** | Level 0/1 listelerine tohum etiketi | ⭐ **saf raporlama, tersine çevrilebilir** — bence yapılmalı |
| **AV-2** | *"Alan yokluğu"* ile *"alan var, değeri 0"* mesafede nasıl ayrılacak | ⛔ **tasarım kararı** — L2 korunacak mı, yoksa mesafe yalnız **ortak alanlar** üzerinde mi hesaplanacak |
| **AV-3** | Hangi kapılar popülasyon yoluna bağlanacak (**I4.2** ve **I5.4** öncelikli), hangileri **N/A ilan** edilecek | ⛔ **kapsam kararı** + ön-kayıt metni |

### 5. Sınırlar

- Av **iki alanla sınırlı** kaldı (analiz aracı + kapı envanteri). Önerilen
  3–5 (L1–L19 doğrulaması · brief'lerden benimsenenler · C2'nin okunmamış
  alanları) **yapılmadı**.
- AV-2 tek tohumdan (`s9912`) doğrulandı; deseni C2'nin tamamında saymadım.
- Hiçbir kol karşıtlığı yorumlanmadı (L9) — okunan yalnız **mekanizma**.

---

## D-148 · 2026-08-19 · ✅ **AV-1 ve AV-2 düzeltildi, AV-3 ayrıldı** — ve ⭐⭐ **K5'in kendisinde bir delik bulundu**

**Yetki:** Yasin, *"önerdiğin şekilde yap"*. D-147'nin üç bulgusu.
**Suite 607 → 611.**

### 1. ⛔ Önce D-147 §2'yi düzeltiyorum — kendi tarifim fazla sertti

D-147'de *"`l2` yokluğu 0 sayıyor"*u bir **hata** gibi yazmıştım. **Değil.**
`mean_z` **birleşim** alanları üzerinden çağrılıyor ve bayraklanmamış bir alan
gerçekten **birikmiş büyüklük taşımıyor** ⇒ yokluk = 0 **uç noktanın kendi
tanımı**, ve docstring bunu zaten doğru yazmış.

⚠ **Kendi sondam farklı bir fonksiyon hesaplamıştı** (alanları kolun kendi
z'sinden türetmiştim) ⇒ ölçümüm koda oturmuyordu. **Gerçek fonksiyonlarla
yeniden koşuldu.**

⇒ **Bulgu ayakta ama daha zayıf ve daha kesin:** aritmetik doğru, eksik olan
**yorumlanabilirlik**. `‖lived − null‖ = 0.087899` **doğru bir sayı**, ama
%100'ü `null`'ın **hiç girmediği** bir eksenden geliyor ⇒ bir **fark** değil
bir **varlık**.

### 2. ✅ AV-1 — her liste artık tohumu yazıyor

Level 0'ın iki listesi, Level 1'in başlığı ve pozitif kontrol listesi
`s{seed}` taşıyor. **Hesap değişmedi.**

### 3. ✅ AV-2 — mesafe **ayrıştırılıyor**, aritmetiği **değişmiyor**

`one_sided_share()` eklendi: `(n_shared, n_one_sided, one_sided_fraction)`.
Level 3 mesafenin yanına yazıyor:

```
‖lived − null‖ = 0.087899  ⚠ 100% of it from 1 axis/axes only one arm entered
‖lived − null‖ = 0.588788                     ← uyarı yok: paylaşılan eksen
```

⇒ §G.2'nin **2026-08-11'de** adlandırdığı okuma ilk kez **görünür**. Ve
`l2`'ye **dokunulmadı** — D-136'nın deseni: kazananın **yanına**, yerine değil.

### 4. ⭐⭐ K5'in kendisinde delik: `-p no:cacheprovider` **yetmiyor**

Mutasyon koşumu **P4'ü *"hiçbir test kırılmadı"*** diye raporladı. Sebep
kodda değildi:

> `-p no:cacheprovider` **pytest**'in önbelleğini kapatıyor, **CPython'un
> bytecode önbelleğini değil**. Geri yükleme **aynı bayt uzunluğunda** olunca
> `.pyc`'nin mtime iddiası tutuyor ve sonraki koşum **mutasyonlu bytecode'u**
> çalıştırıyor ⇒ mutasyon teste **hiç ulaşmıyor**.

**Ölçüldü:** `__pycache__` silindikten sonra aynı suite **36/36 temiz**
geçti. ⇒ **K5'e üçüncü şart eklendi** (`CLAUDE.md §2.4-b`): `__pycache__`
silinir **ve** `PYTHONDONTWRITEBYTECODE=1`.

⚠ **Bu delik bugünkü üç mutasyon koşumunun hepsinde açıktı** (D-136, D-138,
D-148). Yönü **iyi haber**: bayat bytecode **eski** kodu çalıştırır ⇒ hata
*"kırılmadı"* yönünde olur, *"kırıldı"* yönünde değil. D-136'nın 6/6'sı ve
D-138'in 7/7'si **kırıldı** raporlamıştı ⇒ o sonuçlar **etkilenmemiş**.

### 5. ⭐ Düzeltilmiş koşum **iki zayıf testimi** yakaladı

| mutasyon | neden sağ kaldı |
|---|---|
| **P2** *"level-1 başlığından tohumu kaldır"* | Testim `_multi_seed()`'i **`price=None`** ile çağırıyordu ⇒ level 1 **hiç satır üretmiyordu** |
| **P4** *"oranı sayı olarak raporla"* | Testimde **tek** tek-taraflı eksen vardı ⇒ `count = 1` ile `fraction = 1.0` **aynı değer** |

İkisi de düzeltildi (level 1'e gerçek `price`, ve **karışık** bir durum:
1 paylaşılan + 1 tek-taraflı ⇒ oran kesinlikle `0 < x < 1`).
⇒ **Altı mutasyon, altı doğru test.**

### 6. ⏸ AV-3 **bağlanmadı, ayrıldı** — ve gerekçesi

`I4.2` **ABORT**'tur. 24 saatlik bir koşuma yarım bağlanan bir abort kapısı,
çözdüğünden çok sorun yaratır ⇒ kendi adımı ve kendi **K1** kontrolü olmalı.
⇒ Kuyruğa **2.1b** olarak açıldı.

✅ **Ama honestlik açığı ŞİMDİ kapatıldı:** `PREREGISTRATION_3.md` §5'in
V1 kapısı *"preflight 6/6"* diyordu ve **tam kapsam gibi okunuyordu**.
Yeni **§5.1** bağlı 6'yı, bağlı olmayan 20'yi, `I2.1`'in **uyarlanma**
ihtiyacını ve kalan 17'nin **sınıflandırılmadığını** açıkça yazıyor.

### 7. Sınırlar

- Av hâlâ **iki alanla** sınırlı; önerilen 3–5 (L1–L19 doğrulaması ·
  brief'lerden benimsenenler · C2'nin okunmamış alanları) **yapılmadı**.
- AV-2'nin ayrışımı **raporlama**dır; hiçbir hesaba girmiyor.
- Kalan 17 kapı sınıflandırılmadı — ön-kayıtta **öyle ilan edildi**.

---

## D-149 · 2026-08-19 · ⛔⛔ **Kuyruk 2.1b: I4.2 ve I5.4 bağlandı — ve I5.4 bağlandığı anda bir kusur buldu**

**Yetki:** Yasin, *"baştan sona bizi runa hazır hale getirene kadar avlan"*.
D-147/AV-3'ün açtığı borç. **Suite 611, GPU yok.**

### 1. ⭐⭐ Asıl bulgu: **sembolik kanalın somatik yarısı varise hiç ulaşmıyor**

I5.4'ü bağladım, stub koşumda **FLAG** bastı: *"never applied (skipped=0)"*.
⚠ `skipped=0` demek fonksiyonun **hiç çağrılmadığı** demek. C2'nin (gerçek,
6 saatlik) çıktısı okundu:

| nicelik | C2 (144 varis) |
|---|---|
| `n_retrieval_context` | **4–16**, ort. ~10 ✅ |
| `n_inherited_by_parent` | ort. **9.74** anı ✅ |
| `adapter_inherited` | **96 / 144** ✅ (= eğitim alan iki kol) |
| ⛔ `has_somatic_scale` | **0 / 144** |
| ⛔ `has_inherited_warning` | **0 / 144** |

⇒ ⛔ **Kanal 1'in engram yarısı çalışıyor, somatik yarısı çalışmıyor.**
Bu **GAP-3'ün tam kendisi**, ve bugüne kadar *"gen2'nin ilk olayında küçük
bir boşluk"* diye taşınıyordu — ölçülen şey **hiç uygulanmadığı**.

⛔⛔ **Ve C2 bunu `run_quality = clean` diye raporladı**, çünkü **I5.4 bağlı
değildi** (20 bağsız kapıdan biri). ⇒ **Tamamlanmış, temiz görünen bir koşum,
iddia ettiği iki kanaldan birinin yarısı sessizken.**

⚠ **Abartmıyorum, sınırı yazıyorum:** anılar **geçiyor**. Ulaşmayan şey
somatik ölçek ve miras uyarısı. İddia *"kalıtım yok"* değil,
*"**somatik** kalıtım yok"*.

### 2. I4.2 — RNG kilidi asimetrisi **ölçüme bağlandı**

Ölçüldü (`grep`, çıkarım değil): popülasyon koşucusu `_lock_seeds(seed)`'i
nesil döngüsünün **önünde bir kez** çağırıyor (satır 1168 vs döngü 1217);
multigen ise **her nesilden önce** (dört çağrı yeri). ⇒ Nesil 2+ , nesil 1'in
bıraktığı durumdan başlıyor, ve `lived`/`shuffle` **eğitiyor**, `null`
**eğitmiyor** — GAP-12'nin tam şekli.

⚠ **Ve `fork_rng` bunu kapatmıyor:** koruma yalnız **adapter init/reset**
üzerinde (`local_llm.py:311, 452` — D-042'nin düzeltmesi), eğitim döngüsünün
üstünde **değil**.

⛔ **Stub'la ölçemedim ve ölçmeye kalkışmadım:** stub eğitimi kapatıyor, yani
**ölçmek istediğim mekanizmayı** kapatıyor — D-126'nın 50 GPU dakikası buna
gitmişti (K1(b)). ⇒ Koşum artık her neslin başındaki global RNG durumunu
**kaydediyor**, ve `check_generation_rng_uniform` onu okuyor.

⚠ **Bilerek FLAG, ABORT değil.** Ölçülmemiş bir öncül üzerine kurulu bir
ABORT, 24 saatlik koşumu **bir tahmin yüzünden** öldürür. İlk koşum **ölçer**,
mod sayı geldikten sonra yükseltilir. Ön-kayıt §5.1'de **koşumdan önce**
ilan edildi.

### 3. Kapı sayısı **6 → 8**

Bağlananlar `I4.2` (FLAG) ve `I5.4` (FLAG). Kalan **18** hâlâ bağlı değil ve
ön-kayıt §5.1 bunu **sayıyla** yazıyor.

### 4. ⛔ Ve bu, kendi ön-kaydımın V1 kapısını **kırdı**

`PREREGISTRATION_3` §5 V1 *"`run_quality = clean`"* istiyordu. I5.4 gerçek
koşumda **FLAG** basacağına göre, V1 **bilinen ve ilan edilmiş** bir eksikliği
**koşumu geçersiz sayma** sebebine çevirirdi.

⇒ **§5.2 eklendi:** ABORT kapıları **hepsi geçmeli**; FLAG kapıları
**raporlanır**, koşumu geçersiz kılmaz. **Beklenen flag `I5.4`**, ve
beklenmeyen bir flag **yorumlanır**, sessizce geçilmez.

### 5. İki test disiplini dersi

| | ders |
|---|---|
| **`None ≠ False`** | Yardımcı testim `ok is not True` ile filtreliyordu ⇒ *"değerlendirilmedi"*i **başarısızlık** sayıyordu. D-121'in üzerine karar verdiği ayrım, testte kaybolmuş. `is False` oldu |
| **mock'ta anlamsız kapı basmaz** | I5.4 mock altında **her zaman** flag basardı ve *"mock"* damgasını **yok ederdi**. I4.1'in deseniyle aynı: mock'ta **`None`** döner — hak etmediği bir yeşil de basmaz |

⭐ Ve testler artık `clean` yerine **flag KÜMESİNİ** doğruluyor — hangi
kapıların bastığını **ve başkasının basmadığını** söyleyen daha güçlü bir
iddia.

### 6. Sınırlar

- I4.2 stub'da **geçti** ama bu **hiçbir şey söylemiyor** (§2).
- I5.4'ün `applied` sayacı **global**; çok kollu koşumda *"herhangi bir yerde
  ≥1"* demek ⇒ kol başına ayrım yapmıyor. Multigen'de de böyleydi.
- Kalan **18** kapı hâlâ sınıflandırılmadı.
- GAP-3'ün **düzeltilmesi** bu kayıtta **yapılmadı** — ölçüldü ve ilan edildi.
  Düzeltmek fizik değiştirir ve **Yasin'in kararıdır**.

---

## D-150 · 2026-08-19 · ⛔⛔ **GAP-3'ün kökü bulundu — ve önerdiğim düzeltme §2.7'ye çarpıyor**

**Yetki:** Yasin *"önerdiğin yolu uygula"* (= D-149'un **A** seçeneği: GAP-3'ü
düzelt). ⚠ **Uygulayamadım, ve sebebi kaydın konusu.** Ölçüm yapıldı, teşhis
değişti, ve düzeltme artık **Yasin'in bir sabit kararına** bağlı.

### 1. ⛔ Teşhis, belgede yazandan **üç kez** farklı çıktı

`CLAUDE.md` GAP-3'ü *"gen2 ilk olayda somatik ölçek boşluğu —
`apply_inherited_somatic_scale` sadece `delta_log` dolu olunca çalışıyor"*
diye taşıyordu. **Kod okundu, üçü de yanlış çıktı:**

| sanılan | ölçülen |
|---|---|
| *"ilk olayda kaçırılıyor"* | ⛔ **hiç uygulanmıyor** — `skipped=0`, fonksiyon **çağrılmıyor bile** |
| *"`delta_log` boş olduğu için"* | ⛔ Sebep **uygulama tarafı değil, YAZMA tarafı**: `retrieval_context`'e hiçbir zaman `inherited_warning` girmiyor (C2: **0/144**) |
| — | ⛔ Uyarı **iki şart** istiyor ve biri **yapısal olarak ölü** |

### 2. Kök sebep — ölçülmüş sayılarla

`select_for_transfer` (`generation.py:158`) bir travma anısını miras uyarısına
**yalnız iki bantta** çeviriyor:

```
f_agent <  FITNESS_LOW_THRESHOLD  (0.35)  ve trauma   →  uyarı
f_agent >= FITNESS_HIGH_THRESHOLD (0.70)  ve trauma   →  uyarı
```

**C2'nin 216 ajanı** (`classify_fitness` ile, kendi fonksiyonuyla):

| bant | sayı |
|---|---|
| ⛔ `low` | **0 / 216** |
| `normal` | 204 |
| `high` | **12 / 216** (%5.6) |

⇒ ⛔ **`FITNESS_LOW_THRESHOLD = 0.35`, gözlenen dağılımın TAMAMININ altında**
(min **0.3919**). Alt dal **yapısal olarak ulaşılamaz**.

⭐ **Ve sebebi kayıtta duruyor: D-086.** O düzeltme `F_agent`'ı **0.14 → 0.45**
taşıdı; eşik **eski dağılım için** kalibreydi ve **kimse geri dönüp
bakmadı**. ⇒ D-087/D-088'in deseninin aynısı: *"kalibre edildiği niceliğin
yerine başkasına uygulanan eşik"*, bu kez **kalibre edildiği dağılımın yerine
başkasına**.

**Üst dal ölü değil ama nadir:** `high` %5.6, `is_trauma` %11 ⇒ ikisinin
**aynı yaşamda** buluşması ≈ **%0.6** ⇒ 144 variste **0** gözlemi tutarlı.

### 3. ⛔ Neden düzeltmeyi uygulamadım — §2.7

Düzeltmenin üç yolu var ve **üçü de bir karar istiyor**:

| | yol | engel |
|---|---|---|
| **a** | `FITNESS_LOW_THRESHOLD`'a yeni değer | ⛔ **§2.7**: dağılımı **gördüm** (min 0.3919) ⇒ bugün seçilecek her değer **etkiye bakılarak** seçilmiş olur |
| **b** | Bantları **göreli** yap (hücre içi sıra) | ⭐ Tasarımla **tutarlı** — turnuva zaten göreli (k=2) — ama **mekanizma değişikliği**, sabit değil |
| **c** | Sabitlerden türetilen bir eşitsizlik | Aranıyor; `FITNESS_HIGH_THRESHOLD = 0.70` ile `DELTA_THRESHOLD_DEEP = 0.70` **aynı sayı** ⇒ bir bağ olabilir ama **doğrulanmadı** |

⇒ **Karar Yasin'in** (D-007). Kendi başıma değer seçmek, bu projenin
sekiz oturumdur savunduğu tek kuralı çiğnemek olurdu.

### 4. ✅ Bu turda **yapılan** — §2.7'ye uyan kısım

`fitness_class` ajan satırına eklendi (`classify_fitness` **çağrılıyor**,
yeniden yazılmadı — §2.8). ⇒ C2'nin *"216 ajanın f_agent'ını yazıp bandını
hiç söylememesi"* durumu bitti; bir sonraki koşum bandı **kendi dosyasında**
raporlar.

**K2** üç bantla · **K3** sonuç dosyasından · suite **611 → 613**.

### 5. ⇒ Ön-kayıta etkisi

**L20 güncellenmeli:** *"somatik kanal çalışmıyor"* yetersiz bir tarif.
Doğrusu: **alt bant yapısal olarak ölü** (eşik dağılımın altında), **üst bant
canlı ama nadir** (%0.6 birleşim). İkisi farklı şeyler ve farklı düzeltmeler
ister.

### 6. Sınırlar

- Bant dağılımı **tek koşumdan** (C2, 3 tohum, 216 ajan).
- `high ∧ trauma` birleşimini **doğrudan saymadım** — iki marjinalden
  çarpımla **tahmin ettim** (%0.6), ve bağımsızlık varsaydım. ⚠ **Tahmin**,
  ölçüm değil (K4).
- §3-c'nin *"0.70 = 0.70"* gözlemi **bir bağ değil, bir tesadüf olabilir**;
  doğrulanmadı.

---

## D-151 · 2026-08-19 · ⛔ **c yolu ÇALIŞMIYOR** — ve asıl bulgu: bu tespit **sekiz oturum önce yapılmış, kapıya çevrilmemiş**

**Yetki:** Yasin *"onaylıyorum"* (D-150 §3'ün **c** yolunu araştır).
**GPU yok, salt aritmetik ve arşiv.**

### 1. ⛔⛔ Önce süreç bulgusu — teknik bulgudan ağır

D-150'de *"kök sebep bulundu"* dedim. **Yanlış: yeniden bulundu.**
`DECISIONS.md` D-086'nın kaydında birebir yazıyor:

> **"⛔ Bulgu 2 — D-086 o tek yolu kapattı (benim açtığım hasar)"**
> `FITNESS_LOW_THRESHOLD = 0.35` altında: eski `F_agent` **12/12** →
> yeni **1/12**. *"Kanıt aritmetiktir."*

⇒ Bulgu **doğruydu, aritmetiğiyle yazılmıştı, ve orada kaldı.** Kuyruğa
girmedi, kapıya çevrilmedi, ön-kayıta sınır olmadı. Sekiz oturum sonra C2
koşuldu, **`run_quality = clean`** raporladı, ve **144 varisin 0'ı** somatik
ölçek aldı.

⭐ **I5.4 bağlı olsaydı ilk koşumda yakalanırdı.** ⇒ Ders bir sabit hakkında
değil: **kayda geçen bir kusur, bir kapıya bağlanmadıkça kayıp sayılır.**
Bu, K1–K5'e adaylık eden bir kural (§7).

### 2. c yolu — iki aday sınandı, ikisi de düştü

**Aday 1 — yapısal taban.** Ölüm `METABOLIC_GRACE_EVENTS = 10`'a kadar askıda
⇒ her yaşam en az 10 olay yaşar ⇒
`F_agent ≥ FITNESS_W_SURVIVAL × grace / bütçe`:

| bütçe | taban | eşik 0.35 |
|---|---|---|
| 30 (deney) | **0.100** | altında ⇒ bant **ulaşılabilir** |
| 20 | 0.150 | altında |
| 10 | 0.300 | altında |

Taban eşiği ancak **bütçe < 8.57** olsaydı aşardı. ⇒ **Eşitsizlik bağlamıyor.**

**Aday 2 — eşikler birbirinden türemiş mi?**

| ilişki | sonuç |
|---|---|
| `FITNESS_HIGH = 0.70` vs `DELTA_DEEP = 0.70` | **aynı** |
| `FITNESS_LOW = 0.35` vs `DELTA_NORMAL = 0.40` | farklı |
| `FITNESS_LOW = 0.35` vs `FITNESS_HIGH / 2` | ⭐ **tam eşit** |

⇒ ⭐ **`0.35` keyfi bir sayı değil: üst eşiğin tam yarısı.** Yani **zaten
türetilmiş**. Onu değiştirmek, var olan bir ilişkiyi **bozmak** olurdu — ve
yerine konacak değer ancak **dağılıma bakılarak** seçilebilirdi (§2.7).

⇒ ⛔ **c yolu kapandı.** Hiçbir sabit-eşitsizliği 0.35'i çürütmüyor ya da
yerine bir değer vermiyor.

### 3. ⇒ Sorun sabitte değil, **fizikte**

Bant **ilkece ulaşılabilir** (taban 0.10 < 0.35) ama **hiç ulaşılmıyor**
(C2 min 0.3919). ⇒ Kusur eşikte değil: **bu evren düşük-uygunluklu ajan
üretmiyor.**

⭐ **Ve bu, oturumun bütün bulgularının aynı deseni:**

| mekanizma | durum |
|---|---|
| `z` (travma eşiği) | %25 hücrede tanımlı |
| `fitness_class` | **216/216 `normal`** — üç bandın ikisi boş |
| `null` kolu | donmuş klon (D-129) |
| `z`'nin boyutu | dörtte bir (D-137) |

⇒ **Bu evren her şeyi ortaya sıkıştırıyor.** Uç noktalar uçlarda tanımlı,
evren uç üretmiyor.

### 4. ⇒ Geriye **b** kalıyor, ve gerekçesi güçlendi

**b: bantları göreli yap** (hücre içi sıra), mutlak eşik yerine.

⭐ **Bu §2.7'yi ihlal etmiyor, çünkü bir DEĞER seçmiyor** — kuralı
değiştiriyor, ve yerine konan referans **popülasyonun kendisi**.

⭐ **Ve tasarımla iç tutarlılık argümanı var:** bu deneyin seçilimi **zaten
göreli** — turnuva `k = 2` iki ajanı **birbirine** karşı yarıştırıyor
(P2/D-094). Tek mutlak eşik **`fitness_class`**. ⇒ Göreli yapmak bir
uyarlama değil, **var olan mantığın tamamlanması**.

⚠ **Bedeli açıkça:** fizik değişir ⇒ C2 ile karşılaştırılamaz (zaten öyle) ·
kendi doğrulaması gerekir · ve *"düşük bant"* artık **her hücrede dolu**
olur, ki bu da bir tasarım iddiasıdır (her nesilde birileri *"düşük"* sayılır).

### 5. ⛔ Karar Yasin'in — üç seçenek, biri yeni

| | ne | not |
|---|---|---|
| **a** | Yeni eşik değeri | ⛔ **§2.7** + var olan `high/2` ilişkisini bozar |
| **b** ⭐ | Bantları **göreli** yap | Yeni sabit **yok**, tasarımla tutarlı. **Öneri** |
| **d** | **Sınır ilan et, dokunma** | Somatik kanal *"bu evrende ateşlenmiyor"* diye yazılır; iddia **engram kanalıyla** sınırlanır |

⚠ **d, D-149'da reddettiğiniz B seçeneğidir** — ama o zaman kökün **stranded
bir sabit** olduğunu bilmiyorduk. Şimdi biliyoruz ki sabit **türetilmiş** ve
sorun **fizikte** ⇒ d'nin gerekçesi eskisinden **güçlü**.

### 6. Sınırlar

- Aday 1'in tabanı **yalnız hayatta kalma teriminden**; enerji ve havuz
  terimlerinin yapısal tabanı **sabitlerden türetilemedi** (dinamiğe bağlı).
- *"0.35 = 0.70/2"* bir **gözlemdir**; `da6880b`'nin niyetini gösteren bir
  yorum ya da brief **bulunamadı** ⇒ ilişki **gerçek ama belgelenmemiş**.
- §3'ün tablosu bu oturumun ölçümlerinden derlendi, hepsi **tek koşumdan**.

### 7. ⭐ K1–K5'e aday altıncı kural

> **K6 — kayda geçen kusur, bir kapıya bağlanmadıkça kapanmamıştır.**
> Bir D-kaydı bir mekanizmanın çalışmadığını ölçtüyse, aynı turda ya bir
> preflight kapısına ya da kuyruğa **bitti-ölçütüyle** bağlanır. Aksi hâlde
> *"biliniyordu"* ile *"bilinmiyordu"* arasında **pratik fark kalmaz**.
> **Ölçülen bedel:** D-086'nın Bulgu 2'si → sekiz oturum → C2'nin
> `clean` raporu → 144 variste 0 somatik kalıtım.

---

## D-152 · 2026-08-19 · ✅ **UYGULANDI: fitness bantları GÖRELİ** — iki ölü bant canlandı

**Yetki:** Yasin *"ne öneriyorsan öyle yapalım"* (= D-151 §5'in **b** yolu).
**Suite 613 → 618.** ⚠ **Bu bir fizik değişikliğidir.**

### 1. Ne değişti — ve ne DEĞİŞMEDİ

⛔ **Hiçbir eşik değeri değişmedi.** `FITNESS_LOW_THRESHOLD = 0.35` ve
`FITNESS_HIGH_THRESHOLD = 0.70` **aynen duruyor**. Değişen şey **uygulandıkları
nicelik**:

| | önce | sonra |
|---|---|---|
| bant | `f_agent`'ın **mutlak** değeri | hücre içinde **göreli konumu** (min-max, [0,1]) |

⇒ Bu **tam olarak D-088'in yaptığı düzeltme**: *"çıta, kalibre edildiği
niceliğe uygulanır."* Eşikler [0,1] yayılan bir nicelik için kalibreydi;
D-086 `F_agent`'ı ortaya sıkıştırınca çıta havada kaldı. Şimdi yine [0,1]
yayılan bir nicelik görüyor.

⚠ **§2.7 ihlal edilmedi:** hiçbir **değer** veriden seçilmedi. Kural
değişti, ve referans **popülasyonun kendisi**.

### 2. Neden göreli — iç tutarlılık

Bu deneyin seçilimi **zaten göreli**: turnuva `k = 2` iki ajanı **birbirine**
karşı yarıştırıyor (P2/D-094). `fitness_class` geriye kalan **tek mutlak
kural**dı. ⇒ Göreli yapmak bir uyarlama değil, **var olan mantığın
tamamlanması**.

### 3. ⛔ Yasak referans — ve testle çivilendi

En çekici göreli referans **turnuva sonucu** (`w = 0` ⇒ *"en uygunsuz"*).
⛔ **Yasak:** bant hangi anıların aktarılacağını belirliyor ⇒ `z`'yi
şekillendiriyor ⇒ `w`'den türetilseydi `Cov(w, z)` **kısmen özdeşlik**
olurdu. D-075'in totolojisi, P4'ün üç katmanı ayrı tutma sebebi.

⇒ Referans **`F_agent` değerleri**, ve
`test_the_band_is_not_derived_from_heir_count` imzayı **kilitliyor**.

### 4. Ölçülen etki

C2'nin gerçek yayılımıyla (min 0.3919 … max 0.7696):

| | bantlar |
|---|---|
| **mutlak** (bugüne kadar) | `normal` ×7, `high` ×1 — **low: 0** |
| ⭐ **göreli** | `low, low, low, normal, normal, high, high, high` |

⇒ **İki ölü bant canlandı**, ve miras uyarısı dalı **ulaşılabilir** oldu.

⚠ **Düz hücrede hiçbir şey uydurulmuyor:** yayılım ≤ epsilon ise
`normalize_fitness` **`None`** döner ve herkes `normal` olur. Özdeş ajanlarda
kimse *"göreli olarak uygunsuz"* değildir — ve düz hücre varsayımsal değil,
D-129 donmuş bir `null` kolu ölçtü.

### 5. İlan edilen bedel

⚠ **Min-max, her hücrede birini `low` birini `high` yapar.** Bu bir tasarım
iddiasıdır: *"her nesilde birileri göreli olarak uygunsuzdur."* Gizlemiyorum
— mekanizmayı ateşlenebilir kılan şey tam olarak bu.

⚠ **`F_agent` hem `w`'yi hem hangi anıların aktarıldığını etkiliyor.** Bu
**yeni değil** (D-088 kabul etmişti: *"F_agent hangi anıların aktarılacağını
şekillendirir, aktarılıp aktarılmayacağını değil"*) ama göreli hâlde de
**geçerli** ⇒ sınır olarak yazıldı.

⚠ **Tek-soy yolu değişmedi:** referans verilmezse mutlak bantlar çalışır.
Bir ajan yalnız yaşarken **göreli olacağı bir hücre yoktur**.

### 6. K1–K5

**K2** hücrede spread var, üç bant birden · **K3** hem sonuç dosyasından hem
`select_for_transfer`'dan · **K5** **beş mutasyon**, bytecode şartıyla.

⭐ **Ve K5 yine kazandırdı:** ilk turda **Q4 ve Q5 sağ kaldı** — testlerim
sınıflandırıcıyı kapsıyordu ama **aktarım yolunu** kapsamıyordu, ki asıl
davranış değişikliği orada. İki test eklendi (*"göreli bant
`select_for_transfer`'a ulaşıyor mu"* + *"hücrenin üst ucu da uyarı
kazanıyor mu"*) ⇒ **5/5**.

### 7. Sınırlar

- Etki **C2'nin yayılımıyla** gösterildi; yeni fizikte yayılımın ne olacağı
  **bilinmiyor**.
- ⚠ **Fizik değişti** ⇒ C2 ve öncesi **karşılaştırılamaz** (zaten öyleydi).
- Somatik ölçeğin varise **gerçekten ulaştığı** doğrulanmadı — bant artık
  ateşlenebilir, ama zincirin geri kalanı (`is_trauma` olan bir anının
  **var olması**) hâlâ travma eşiğine bağlı ⇒ **GAP-3 tam kapanmadı**,
  darboğazı **bir adım ileri taşındı**. I5.4 bunu gerçek koşumda ölçecek.

---

## D-153 · 2026-08-19 · **K6 bağlayıcı oldu · sınırlar doğrulandı · D seçeneğinin ön-taahhüdü yazıldı**

**Yetki:** Yasin *"önerdiğin şekilde işlemleri bitirip öyle gel"*.
**GPU yok.** Üç iş: **K6**, **L-sınırlarının denetimi**, **D seçeneği**.

### 1. ✅ K6 `CLAUDE.md §2.4-b`'ye bağlayıcı kural olarak girdi

> **Kayda geçen kusur, bir KAPIYA bağlanmadıkça kapanmamıştır.**

Ölçülen bedeli kuralın yanında duruyor: D-086'nın Bulgu 2'si → sekiz oturum →
C2'nin `clean` raporu → **144 varişte 0** somatik kalıtım. Kapı (I5.4)
**tanımlıydı, bağlı değildi**.

### 2. ⛔ Ve K6'yı eklerken bir **ad çakışması** çıktı — D-070'ten beri varmış

İki ayrı `K`-serisi aynı adları kullanıyor:

| seri | ne | durum |
|---|---|---|
| `§2.4-b` **K1–K6** | çalışma kontrolleri | **yürürlükte** |
| `§4` **K1–K7** | ikinci ön-kaydın **kilit kararları** | 🔒 kapanmış |

Ölçüldü: `DECISIONS.md`'de `K5` **30 kez** geçiyor ve **her iki anlamda da**
kullanılmış (ör. *"`z` = landmark drift, K5"* = kilit kararı;
*"K5 mutasyon koşumu"* = kontrol).

⇒ **Kapatıldı, yeniden adlandırmadan:** `§2.4-b`'ye disambiguation tablosu
eklendi — işaretsiz `K5` bundan sonra **kontrol serisinin** K5'i, kilit
kararına atıf **"kilit K5"** diye yazılır. ⚠ Eski kayıtlar
**append-only** olduğu için düzeltilemez; kural **ileriye dönük**.

### 3. ✅ Av alanı 3 — ilan edilen sınırların **kodda** denetimi

*"On dokuz sınır ilan ettim; kaçını doğruladım, kaçını kopyaladım?"*
sorusunun cevabı, **kod okunarak**:

| sınır | doğrulama |
|---|---|
| **L3** `z` tek boyutlu | ✅ `DAERM_LOAD_DOMAINS` **`energy` içermiyor** ⇒ hedef ekseni asla energy olamaz |
| **L4** tekrarlama birimi tohum | ✅ `inherit_adapter` çağrısı var ⇒ nesiller **gerçekten bağımlı** |
| **L5** `Cov` işaretli | ✅ rapor `+.6f` basıyor · ✅ `selection` üzerinde `abs()`/norm **yok** |
| **L10** G ≥ 3 | ✅ `MINIMUM_GENERATIONS_INFORMATIVE = 3` |
| **L14** kriz sabit alana | ✅ `CRISIS_AFFECTED_DOMAIN = 'resource'` |
| **L15** I0.1/I0.2 bağlı değil | ✅ C2'nin kapı bloğunda **yok** |
| **L16** spillover skaler | ✅ `CROSS_AXIS_SPILLOVER = 0.2` (float) |
| **L17** `to_landmark.max` kullanılmıyor | ✅ ön-kayıt §3'te **geçmiyor** |
| **L20** göreli bant çalışıyor | ✅ üç bandı da üretiyor |

⇒ **10/10 doğrulandı.** ⚠ Kalanlar (**L1 · L2 · L6 · L7 · L8 · L9 · L11 ·
L12 · L13 · L18 · L19**) **kod özelliği değil** — literatür, tasarım ya da
tarihsel ölçüm beyanları. **Kod denetimiyle sınanamazlar** ve bu, ilan
edilmiş bir sınırdır, kusur değil.

### 4. 🔒 D seçeneği — **ön-taahhüt yazıldı, karar YAZILMADI**

**Durum:** GPU'suz **kapanamaz**, ve zorlamak D-129'un yasakladığı şey olur.

**Neden:** iki sürekli aday da kapalı — `energy_mean_over_life` **pozitif
kontroldür** (D-121, aynı niceliği hem uç nokta hem kontrol yapmak kontrolü
yok eder) · `to_landmark.max` **reddedilmiştir** (D-129, **2/4**) ve D-143 §5
yeniden açılmasını **üç şarta** bağlamıştır.

⚠ **Ve teknik bir kaçamak var, bilerek almıyorum:** D-129 *pencere* sürümünü
reddetti; ömür-boyu kardeşi (`delta_profile.max`) **adı geçmediği için**
serbest görünüyor. ⛔ Bunu kullanmak, kuralı **sayıyı gördükten sonra dar
yorumlamak** olurdu — D-129 §4'ün önceden adlandırdığı tuzak.

⭐ **Üçüncü aday, ve D-152'nin mantığının aynısı:** `is_trauma`'yı da
**göreli** yapmak — *"bir yaşamın en şiddetli olayı o yaşamın travmasıdır."*
⚠ **Bedeli çok ağır ve peşinen yazıyorum:** her yaşamda **tam olarak bir**
travma olur ⇒ `z` her hücrede dolar ⇒ ama *"travma"* kelimesi **şiddet**
anlamını kaybeder ve **sıralama** anlamına gelir. Bu, D-152'den **çok daha
büyük** bir iddia değişikliğidir. ⛔ **Önermiyorum**, tabloda duruyor.

🔒 **ÖN-TAAHHÜT (D-125 deseni — sonda koşulmadan ÖNCE yazılıyor):**

> Sürekli bir uç nokta adayı **ancak** şu üç şart birlikte sağlanırsa
> üçüncü ön-kayıta girer:
> 1. Sonda **`lived` ve `shuffle`** kollarını içerir (D-129'unki `lived null`
>    koşmuştu; bugünkü birincil karşıtlık `lived ↔ shuffle`);
> 2. **4 hücrenin en az 3'ünde** aday `Var > 0` taşır;
> 3. Kural **taze veriye** uygulanır — D-129'un sayıları **yeniden okunmaz**.
>
> ⛔ Kovaryans · kol farkı · etki büyüklüğü **hesaplanmaz** (L9).

### 5. Sınırlar

- §3'ün denetimi **kod özelliği olan** sınırlarla sınırlı; 11 sınır **doğası
  gereği** kod denetimine kapalı.
- §4 bir **taahhüttür**, bir sonuç değil. Sondayı koşmadan D **kapanmaz**.
- Av alanları **4 ve 5** (brief'lerden yerel doğrulaması yapılmadan
  benimsenenler · C2'nin hiç okunmamış alanları) **yapılmadı**.

---

## D-154 · 2026-08-19 · 🔒 **K1 MEKANİZMA KONTROLÜ + ÖN-TAAHHÜT — sonda-3, koşumdan ÖNCE yazıldı**

⚠ **Bu kayıt sonda KOŞULMADAN önce commit edilmiştir.** Sırası kasıtlıdır:
sonra yazılsaydı sayıyı görüp kriteri ona göre seçmiş olurdum (§2.7 / L9).
**Commit sırası bunun kanıtıdır** (D-125/D-128 deseni).

**Yetki:** Yasin, 2026-08-19: *"şu 2 saatlik run üzerinden tüm sorunlarımızı
çözmeye çalışalım."*

---

### 1. Sonda **üç** soruyu birden cevaplıyor

Üçü de bugün **bilinmiyor** ve üçü de pahalı koşumdan **önce** bilinmeli.

| # | soru | neden şimdi |
|---|---|---|
| **S1** | Sürekli bir uç nokta adayı **taze veride** daha sık tanımlı mı? | D seçeneğinin tek kapısı (D-153 §4 ön-taahhüdü) |
| **S2** | **I5.4** geçiyor mu — somatik kanal D-152'den sonra canlandı mı? | D-152 bir **tahmin**; sonda onu çürütebilir |
| **S3** | **I4.2** ne diyor — kollar aynı RNG durumundan mı giriyor? | GAP-12; ölçülmemiş bir öncül, ve stub'la ölçülemez |

---

### 2. K1 — mekanizma kontrolü (bağlayıcı, `CLAUDE.md §2.4-b`)

**(a) Ölçülen niceliği hangi mekanizma üretiyor**

| nicelik | zincir |
|---|---|
| **S1** aday | sıralı erişim + rotasyon → hasat farkı → enerji farkı → **adapter eğitimi (Kanal 2)** → varis farklı ağırlıkla doğar → farklı karar → farklı PE → `delta_profile` |
| **S2** `I5.4` | `F_agent` yayılımı → **göreli bant** (D-152) → `low`/`high` ajan → **travma sınıfı anı** → `inherited_warning` → varişte `somatic_scale` → `apply_inherited_somatic_scale` |
| **S3** `I4.2` | nesil 1'in eğitimi global torch akışını tüketiyorsa → `lived`/`shuffle` nesil 2'ye `null`'dan **farklı** durumdan girer |

**(b) ⛔ Seçtiğim bayraklardan hangisi bu mekanizmayı kapatır**

| bayrak | etkisi | kararım |
|---|---|---|
| ⛔ `--no-lora` | **Kanal 2'yi kapatır** ⇒ S1'in zinciri hiç doğmaz, S3'ün sorusu **anlamsızlaşır** | ⛔ **KULLANILMIYOR** (D-126'da 50 dk buna gitti) |
| ⛔ `--mock-llm` | Eğitim yok, kararlar kanned ⇒ S2 **her zaman** flag basar | ⛔ **KULLANILMIYOR** (yalnız kuru provada) |
| `--n-generations 3` | Price **G−1** satır ister; G=2 yalnız sıfır raporlar (D-107) | **3** |
| `--events 30` · `--n-agents 8` | Deneyle aynı | **aynı** |
| `--fresh-pasture` | Deneyle aynı (D-104) | **aynı** |
| **`--arms lived shuffle`** | ⭐ **Ön-taahhüdün 1. şartı** (D-153 §4) | **`lived shuffle`** |
| dış `timeout` | D-126'da I4.1 replay'i kesti, **sonuç dosyası hiç yazılmadı** | ⛔ **YOK** |

⚠ **`null` bilerek dışarıda, ve gerekçesi D-129'unkinin tersi değil aynısı.**
D-129 *"yalnız güçlü kolu koşma"* diyordu; bugünkü **birincil karşıtlık
`lived ↔ shuffle`** (D-131) ve ikisi de eğitim alıyor ⇒ sonda tam olarak
**ön-kayıtın ölçeceği popülasyonu** ölçüyor. `null` betimleyici olduğu için
tanımlılık sorusunun parçası **değil**.
⚠ **Bedeli ilan ediyorum:** bu sonda `null`'ın tanımlılığı hakkında **hiçbir
şey söylemez**, ve söylemeye de çalışılmayacak.

**(c) Bu yapılandırmada dejenere olmadığının **mevcut veriden** kanıtı**

| | C2'den (gerçek koşum, aynı yapılandırma) |
|---|---|
| `F_agent` yayılımı | **21/27 hücrede > 0** (D-146) ⇒ göreli bant **girdi bulacak** |
| sürekli nicelik tanımlılığı | **21/27 = %78** (D-146) ⇒ S1'in adayı **dejenere değil** |
| bireysel kanal travma geçişi | **24/216 = %11** ⇒ S2'nin ikinci şartı **var ama nadir** |
| `lived`/`shuffle` eğitim | **96/144 varis adapter aldı** ⇒ Kanal 2 **çalışıyor** |

---

### 3. 🔒 ÖN-TAAHHÜT — okuma kuralları, **koşumdan önce**

#### S1 — sürekli uç nokta

**Aday:** `delta_profile.to_landmark.max` (bireysel kanalın pencere içi tepesi).

⚠ **Bu D-129'un reddettiği niceliktir ve bilerek aynısı seçildi.** Ret
`lived null` koşumundan geldi ve `null`'ın donmuşluğu yüzündeydi (0/2).
D-143 §5 yeniden açılmayı **üç şarta** bağladı; üçü de burada sağlanıyor:
**(1)** sonda `shuffle` içeriyor · **(2)** kural aşağıda, koşumdan önce ·
**(3)** D-129'un sayıları **yeniden okunmayacak**.

> **KURAL:** **4 hücrenin (2 kol × 2 nesil geçişi) en az 3'ünde**
> `Var(to_landmark.max) > 0` ⇒ aday üçüncü ön-kayıta **girer**.
> Aksi hâlde **girmez**, ve bu **kapanmış** bir sorudur.

⛔ **Hesaplanmayacaklar:** kovaryans · kol farkı · etki büyüklüğü · herhangi
bir işaret. (L9)

#### S2 — somatik kanal

> **TAHMİN (çürütülebilir):** `I5.4` **geçer**, ve **≥ 1** varis
> `has_somatic_scale = true` taşır.
> **Aritmetik:** göreli bant ajanların ~%65'ini `low`/`high`'a koyuyor ×
> travma anısı %11 ⇒ 48 variste **~3**, 144 variste ~10 beklenir.
> ⚠ **Bağımsızlık varsayımıyla çarpım — tahmin, ölçüm değil (K4).**
> ⛔ **Sıfır çıkarsa D-152 vaat ettiğini yapmamıştır** ve öyle raporlanır.

#### S3 — RNG asimetrisi

> **TAHMİN:** `I4.2` **FLAG basar** (kollar farklı RNG durumundan girer).
> Gerekçe: bu koşucu `_lock_seeds`'i döngünün **önünde bir kez** çağırıyor,
> ve `fork_rng` yalnız adapter init'ini koruyor.
> ⛔ **Geçerse** öncül yanlıştı, ve I4.2 **ABORT'a yükseltilir**.

---

### 4. Yapılandırma ve komut

**Tohum: 9916** (taze blok; kullanılmışlar …9915 · 9305–9310).
⚠ Sonda **keşifsel** — tohum 9916 deneyde **kullanılmaz**.

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9916 --n-agents 8 --n-generations 3 --events 30 \
  --lora --fresh-pasture --arms lived shuffle \
  --results dau_runs/probe3_endpoint_s9916.json
```

⚠ **Dış `timeout` YOK** (D-126). ⚠ `PYTORCH_CUDA_ALLOC_CONF` **elle
verilmez** (D-116).

**Süre tahmini: ~2 sa** (C2'den: kol-tohum başına ~39 dk × 2 + replay).
⚠ **Tahmin, ve tahminlerim D-126/D-129'da iki kez tutmadı.** Nişler arası
yayılım **2.3 kat** ⇒ gerçekçi aralık **1.5–4 sa**.

---

### 5. Sonda bittiğinde ne olur — dört yol, hepsi önceden yazılı

| S1 | S2 | ne yapılır |
|---|---|---|
| **geçti** | geçti | ⭐ Uç nokta `to_landmark.max`'a çevrilir, ön-kayıt §3/§4/§7 yeniden yazılır, **kilit yolu açılır** |
| **geçti** | düştü | Uç nokta çevrilir; **somatik kanal sınır** olarak ilan edilir (L20 güncellenir) |
| **düştü** | geçti | Uç nokta `z` olarak kalır; ⛔ D-145'in 3. kusuru **açık kalır** ⇒ **S ≥ 30 mu, kestirim mi** kararı Yasin'e döner |
| **düştü** | düştü | ⛔ *"Bu fizikle test edilemez"* **kanıtla** yazılır ⇒ Yön 3 tartışması yeniden açılır |

⛔ **Hiçbir yolda kural sonradan gevşetilmez.** *"3/4 olmadı ama 2/4 da
fena değil"* denmez — D-129'da denmedi, burada da denmeyecek.

### 6. Sınırlar

- **Tek tohum, tek niş.** C2'de tanımlılık nişe göre değişiyordu ⇒ 3/4
  sonucu **genellenemez**, yalnız *"aday girer/girmez"* kararını verir.
- Sonda **`null` hakkında hiçbir şey** söylemez (§2-b).
- S2'nin aritmetiği **bağımsızlık varsayıyor**; gerçek birleşim farklı olabilir.
- Sonda **keşifsel**; sonuç dosyası `note` alanıyla öyle damgalanır.

---

## D-155 · 2026-08-20 · ⛔⛔ **SONDA-3 KOŞTU — S1 düştü (2/4), S2 düştü (0/32), S3 tahmin tuttu** ⇒ D-154 §5'in **dördüncü yolu**

**Koşum:** `dau_runs/probe3_endpoint_s9916.json` · tohum **9916** · 8 ajan ·
3 nesil · 30 olay · kollar **`lived shuffle`** · `--lora --fresh-pasture` ·
komut **D-154 §4'ün birebir aynısı**, dış `timeout` yok.
**Süre: 2 sa 09 dk 47 sn** (01:43:25 → 03:53:12, dosya damgalarından okundu).
⭐ Tahmin (~2 sa) **ilk kez tuttu** — D-126/D-129'da iki kez tutmamıştı.

`complete: true` · `run_quality=flagged` · **I4.1 `identical`** (replay birebir).
Kapılar: I0.3 ✅ · I0.4 ✅ · I0.6 ✅ · I0.7 ✅ · I1.1 ✅ · I4.1 ✅ ·
**I4.2 ✗ (flag)** · **I5.4 ✗ (flag)**.

⛔ **Okunmayanlar (L9, ön-taahhüt):** kovaryans değeri · kol farkı · etki
büyüklüğü · işaret. Aşağıdaki her sayı **tanımlılık** sayısıdır.

---

### 1. S1 — sürekli uç nokta: **2/4 ⇒ aday GİRMEZ**

🔒 **Kural (D-154 §3, koşumdan önce):** 4 hücrenin (2 kol × 2 nesil geçişi)
**en az 3'ünde** `Var(to_landmark.max) > 0` ⇒ aday üçüncü ön-kayıta girer.

Tahmin edici ve eşik `price_partition`'ınkiyle **aynı** (§2.8): popülasyon
varyansı + `Z_VARIANCE_EPSILON = 1e-12`. Hiçbir hücrede eksik değer yok (8/8).

| kol | geçiş | n | `Var(to_landmark.max)` | Var > 0 |
|---|---|---|---|---|
| lived | gen1→gen2 | 8/8 | **0** | ❌ |
| lived | gen2→gen3 | 8/8 | 0.00104645 | ✅ |
| shuffle | gen1→gen2 | 8/8 | **0** | ❌ |
| shuffle | gen2→gen3 | 8/8 | 0.00032915 | ✅ |

⇒ **2/4 < 3/4 ⇒ aday GİRMEZ, ve bu kapanmış bir sorudur.**
⛔ *"2/4 da fena değil"* denmiyor — D-129'da denmedi, burada da denmedi.
⚠ Ve sayı **D-129'un aldığı 2/4'ün aynısı**, bu kez `shuffle`'lı ve taze
veriyle: ret **iki bağımsız yapılandırmada** tekrarlandı.

#### ⭐⭐ Asıl bulgu ret değil, **retin deseni**

Düşen iki hücre **rastgele değil**: ikisi de **gen1**, ve ikisi de **her iki
kolda**. Sebep ham veride açık — gen1'in **sekiz ajanı bit düzeyinde özdeş**:

```
lived   gen1: 8/8 ajan  to_landmark.max = 0.5390205025672912,  F_agent = 0.5458143853860838
shuffle gen1: 8/8 ajan  to_landmark.max = 0.5390205025672912,  F_agent = 0.5458143853860838
```

`pool_ratio_end = 0.757` ⇒ **havuz gen1'de hiç ısırmadı**. P0 ①'in (sıralı
erişim + rotasyon) farklılaştırma zinciri **kıtlıkla** başlıyor (D-081); kıtlık
olmayınca zincir hiç doğmuyor. Farklılaşma **yalnız gen2'den itibaren**
görünüyor ve kaynağı **adapter** (Kanal 2, D-129/D-130'un teşhisi).

⇒ **Bu tek bir uç noktanın kusuru değil.** Aynı desen bugünkü uç noktada da
var, sonuç dosyasından okundu (yalnız `z_variance` ve `selection_estimable`;
kovaryans **okunmadı**):

| kol | geçiş | alan | `z_variance` | estimable |
|---|---|---|---|---|
| lived | gen1→gen2 | energy | **0** | ❌ |
| lived | gen2→gen3 | energy | 0.0972 | ✅ |
| lived | gen2→gen3 | resource | 0 | ❌ |
| shuffle | gen1→gen2 | energy | **0** | ❌ |
| shuffle | gen2→gen3 | energy | 0.0197438 | ✅ |
| shuffle | gen2→gen3 | resource | 0 | ❌ |

⇒ ⛔ **Kurucu nesil yapısal olarak dejenere:** birinci Price geçişi
(gen1→gen2) **hangi uç nokta seçilirse seçilsin** `Var = 0` verir. Uç nokta
değiştirmek bunu düzeltmez — **fizik düzeltir**. Bu, D-123'ün *"evren null'ı"*
teşhisinin **mekanizma düzeyinde** tekrarıdır.
⚠ **Sınır:** tek tohum, tek niş (D-154 §6). Desen **genellenemez**, ama iki
kolda birden ve iki ayrı uç noktada aynı çıkması rastlantı okumasını zorlaştırır.

---

### 2. S2 — somatik kanal: **0/32 ⇒ D-152 vaat ettiğini yapmadı**

🔒 **Tahmin (D-154 §3):** `I5.4` **geçer**, ≥1 varis `has_somatic_scale`.
Aritmetik ~%65 × %11 ⇒ 48 variste ~3 bekleniyordu.

**Ölçülen:**

| nicelik | sayı |
|---|---|
| varis (doğum kaydı) | **32** |
| `has_somatic_scale` | **0** |
| `has_inherited_warning` | **0** |
| `adapter_inherited` | **32 / 32** ⇒ Kanal 2 çalışıyor |
| anı (`n_retrieval_context`) ort. | **7.19** (min 5, max 11) ⇒ engram yarısı çalışıyor |
| `I5.4` | `never applied (skipped=1563)` |

⇒ ⛔ **Tahmin çürütüldü, ve öyle raporlanıyor.** D-149'un bulduğu tablo
**aynen duruyor**: Kanal 1'in **engram yarısı akıyor, somatik yarısı akmıyor**
(GAP-3). D-152 bunu kapatmayı **ummuştu**, kapatmadı.

#### ⭐ Ama D-152'nin *hangi yarısı* tuttu — ölçüldü

| zincir halkası | durum |
|---|---|
| göreli bant ajan sınıflandırıyor | ✅ **çalışıyor** — 48 yaşamın 10'u `low`, 15'i `high` (mutlak bantta 48/48 tek sınıftı) |
| travma eşiği aşılıyor | ✅ **48/48 yaşam** en az bir kez aşıyor (`n_at_or_above_trauma_either_channel > 0`) |
| `low` bant ajanı **üreyebiliyor** | ✅ **çalışıyor** — `shuffle` gen2'de üç `low` ebeveyn w = 3/1/1 ⇒ 5 varis |
| varis `inherited_warning` alıyor | ❌ **0 / 32** |

⇒ **Kırılma bandın kendisinde değil, bandın ARKASINDA.** `select_for_transfer`
(`generation.py:175–183`) üç şart birden istiyor:
`recall_count ≥ GENERATION_MIN_RECALL` **ve** `band == low` **ve**
`is_trauma(candidate.record)`. İlk üç halka sağlandığına göre kalan tek şüpheli
**travma-sınıfı anının hiç geri çağrılmamış olması** (ya da Ebbinghaus'un onu
silmiş olması, GAP-4).
⚠ **Bu çıkarım, ölçüm değil (K4).** Sonuç dosyası `recall_count` taşımıyor;
bu yüzden **kuyruk 2.5** açılıyor (K6, aşağıda).
⚠ Ayrıca §2.11'in iki travma okuması **burada da ayrı**: `n_at_or_above_trauma`
PE-delta kanalıdır, `is_trauma(record)` anı imprint sınıfıdır. İkisinin
örtüşüp örtüşmediği **ölçülmedi**.

---

### 3. S3 — RNG asimetrisi: **tahmin tuttu, I4.2 FLAG bastı**

🔒 **Tahmin:** `I4.2` FLAG basar (kollar farklı RNG durumundan girer).
**Ölçülen:** `arms entered a generation from different RNG states: s9916 gen3: 2 states`

⇒ Öncül **doğru** ⇒ ön-taahhüdün *"geçerse ABORT'a yükseltilir"* şartı
**ateşlenmedi**; I4.2 **FLAG olarak kalıyor** (gerekçesi ön-kayıt §5.1).
⚠ Ve artık **stub'la değil gerçek koşumla** ölçülmüş durumda — GAP-12'nin
ölçülmemiş öncülü kapandı.

---

### 4. ⇒ D-154 §5'in **dördüncü yolu**: S1 düştü · S2 düştü

> ⛔ *"Bu fizikle test edilemez"* **kanıtla** yazılır ⇒ **Yön 3 tartışması
> yeniden açılır.**

**Kanıt, üç cümlede:**

1. Kurucu nesil **bit düzeyinde özdeş** (8/8, iki kolda) çünkü kıtlık gen1'de
   hiç ısırmıyor (`pool_ratio_end = 0.757`) ⇒ birinci Price geçişi **hangi uç
   noktayla olursa olsun** `Var = 0`.
2. Farklılaşmanın tek kaynağı **hâlâ adapter** (D-129/D-130 aynen geçerli) ⇒
   ölçülebilir hücreler yalnız gen2'den sonra doğuyor ⇒ G nesil koşumun
   **G−1 geçişinin yalnız G−2'si** kullanılabilir.
3. Sembolik kanalın **somatik yarısı hâlâ ölü** (0/32) ⇒ aksiyomun *"iki ayrı
   kanal"* iddiasının bir yarısı popülasyon yolunda **hiç akmıyor**.

⛔ **Yasin'in kararı gerekiyor** (D-007) ve seçenekler §5'te.

---

### 5. ⛔ KARAR — Yasin'in, ve sonda bunu **daraltarak** verdi

| | yol | bedeli | sondanın söylediği |
|---|---|---|---|
| **A** | **Yön 3'ü aç** — evrenin fiziğini değiştir (ajan-ajan kuplajı D-135'te elendi ⇒ geriye **kıtlık rejimi** kalıyor: Holling II / kapasite, D-082/D-084) | en büyük iş, bugünkü sayılar **taşınmaz** | ⭐ **En doğrudan cevap:** gen1'in dejenerasyonunun sebebi tam olarak *"kıtlık ısırmıyor"* |
| **B** | **Kurucu neslini ölçümün dışında bırak** — Price yalnız gen ≥ 2 geçişlerinden okunur, G artırılır | G=4 için koşum süresi ~1.5 kat | ⚠ Sıfır fizik değişikliği, ama **tohum başına maliyet artıyor** ve gen1 yine de koşuluyor |
| **C** | **Kestirim damgasıyla devam** (P7-b / D-096) — test değil kestirim | ucuz | ⛔ D-145'in 3. kusuru **açık kalır**, ve S1 düştüğü için uç nokta da düzelmedi |

⚠ **Claude Code'un önerisi: A ile B birlikte değerlendirilsin, ama önce B
ölçülsün** — çünkü B'nin *"gen1 hariç"* varsayımı **bu koşumla zaten
sınanabilir** (gen2→gen3 hücrelerinin ikisi de `estimable=True` çıktı) ve
sıfır yeni sabit istiyor. A ise §2.7'nin sınırında bir sabit kararı
(`h` ya da kapasite) gerektiriyor ve D-084'ten beri açık.
⚠ **Bu bir öneridir, karar değil.** İkisi de fizik/tasarım kararı ⇒ D-007.

---

### 6. K6 — kayda geçen kusur bir kapıya bağlandı

| kusur | bağlandığı yer |
|---|---|
| somatik kanal 0/32 | **I5.4** zaten kapı (D-149) ve **flag bastı** ⇒ bağlı ✅ |
| kollar farklı RNG durumundan giriyor | **I4.2** zaten kapı (D-149) ve **flag bastı** ⇒ bağlı ✅ |
| ⛔ **kurucu nesil dejenere** (`Var = 0`, gen1, 2 kol) | **kapı YOK** ⇒ **kuyruk 2.6** açıldı, bitti-ölçütüyle |
| ⛔ **somatik zincirin kırıldığı halka bilinmiyor** | **kuyruk 2.5** açıldı, bitti-ölçütüyle |

---

### 7. Sınırlar (ilan)

- **Tek tohum (9916), tek niş.** C2'de tanımlılık nişe göre değişiyordu ⇒
  hiçbir oran genellenemez; sonda yalnız *"aday girer/girmez"* kararını verdi.
- Sonda **`null` hakkında hiçbir şey söylemiyor** (D-154 §2-b, bilerek).
- **Keşifsel** — sonuç dosyası ön-kayıt damgası taşımıyor, ve hiçbir sabit
  bu koşuma bakılarak seçilmedi (§2.7).
- §2'nin *"kırılma travma anısının geri çağrılmamasında"* cümlesi **çıkarımdır**;
  ölçüm 2.5'te yapılacak.
- Tohum **9916 harcandı**, deneyde kullanılmaz.

---

## D-156 · 2026-08-20 · ✅ **KARAR: B yolu (kurucu nesil ölçümün dışında)** + 🔒 **ÖN-TAAHHÜT — öncül sınaması, OKUMADAN ÖNCE yazıldı**

**Yetki:** Yasin, 2026-08-20: *"önerdiğin şekilde devam et"* ⇒ D-155 §5'in
önerisi (**B önce ölçülsün, A onun yanında değerlendirilsin**) **karar oldu**.

⚠ **Bu kayıt okuma YAPILMADAN önce commit edilmiştir.** Sırası kasıtlıdır:
sonra yazılsaydı sayıyı görüp kriteri ona göre seçmiş olurdum (§2.7 / L9).
**Commit sırası bunun kanıtıdır** (D-125/D-128/D-154 deseni).

---

### 1. Seçilen yol ve **ne olmadığı**

**B:** Price yalnız **ebeveyni gen ≥ 2 olan** geçişlerden okunur; kurucu nesil
ilan edilmiş bir **ısınma (burn-in)** nesli olur, ve G buna göre artar.
⇒ Bir koşumun kullanılabilir geçiş sayısı **G − 2**.

⛔ **B bir düzeltme değil, ilan edilmiş bir kısıttır.** Kurucu nesil ölçülemez
olmaktan **çıkmıyor**; ölçüm onu **kapsam dışı ilan ediyor**. Bunun bedeli
üçüncü ön-kayıta **sınır** olarak yazılacak: *"bu tasarım kurucu nesildeki
seçilim hakkında hiçbir şey söylemez."*

⛔ **A elenmedi, ertelendi.** A (kıtlık rejimi) dejenerasyonun **sebebine**
dokunuyor; B yalnız **etkisinden kaçıyor**. A'nın önündeki engel ölçüm değil
**bir sabit kararı** (`h` ya da kapasite, D-082/D-084, §2.7 sınırında) ve o
karar hâlâ Yasin'in.

### 2. Neden ölçmeden kabul edilmiyor

B'nin dayandığı öncül şu: *"kurucu neslin dejenerasyonu **yapısaldır**, tohuma
ya da nişe bağlı bir kaza değildir."* Sonda-3 bunu **tek tohumda** gösterdi
(D-155 §1) — **n = 1**. Öncül yanlışsa B'nin gerekçesi *"yapısal kısıt"*tan
*"maliyet tercihine"* düşer, ve o zaman A'nın ağırlığı artar.

⇒ **Sınama GPU'suz, mevcut veriyle:** C2 (`dau_runs/c2_population_n8_g3_s3.json`,
3 tohum × 3 kol) **9 adet** gen1→gen2 hücresi taşıyor.

#### ⚠ Karşılaştırılabilirlik — neden C2'nin *yalnız gen1'i* okunabilir

`CLAUDE.md` *"hiçbir eski koşum bugünün aletiyle karşılaştırılamaz"* diyor ve
bu **genel olarak doğru**. Bu okuma bir istisna değil, **daraltma**:

| | okunabilir mi | gerekçe (kodla doğrulandı) |
|---|---|---|
| **gen1→gen2 hücresi** (ebeveyn = gen1 ajanları) | ✅ **evet** | D-152'nin diff'i yalnız `consolidate_parents` (aktarım) + `fitness_class` **raporlaması**. Gen1 ajanının yaşamı aktarımdan **önce** gelir ⇒ z'si D-152'den etkilenmez |
| **gen2→gen3 hücresi** (ebeveyn = gen2 ajanları) | ❌ **hayır** | Gen2 ajanı **miras aldığı anılarla** yaşıyor, ve D-152 tam da hangi anıların miras kalacağını değiştirdi ⇒ başka bir fizik |

⇒ **Sınama yalnız öncülün BİRİNCİ yarısını** (*kurucu nesil dejenere*) test
eder. İkinci yarı (*gen ≥ 2 geçişleri tanımlı*) bugün **yalnız n = 2**
(sonda-3'ün iki hücresi) ve bu **ilan edilmiş bir zayıflıktır**.

---

### 3. 🔒 ÖN-TAAHHÜT — okuma kuralları

**Okunacak nicelik:** C2'nin `price_for_previous_transition` bloklarındaki
**`z_variance`** ve **`selection_estimable`**, yalnız **gen1→gen2** geçişinde.
⛔ **Okunmayacaklar (L9):** `selection` · `transmission` · `delta_zbar` ·
kol farkı · işaret · etki büyüklüğü.
⛔ **`to_landmark.max` yeniden okunmayacak** — S1'de reddedildi, **kapalı soru**
(D-155 §1). Yeniden açmak ön-taahhüt ihlali olur.

> **KURAL B1:** 9 hücrenin **9'unda da** `Var(z) = 0` ⇒ kurucu neslin
> dejenerasyonu **yapısaldır**; B'nin gerekçesi mekanizmadır, ve B uygulanır.
> **≥ 1 hücrede `Var(z) > 0`** ⇒ dejenerasyon **tohuma/nişe bağlıdır**;
> B'nin *"yapısal kısıt"* gerekçesi **düşer**, B yalnız bir **maliyet
> tercihi** olarak kalır ve bu **açıkça öyle** yazılır ⇒ A yeniden Yasin'e
> gider.

⛔ **8/9 yeterli değildir.** *"Dokuzun sekizi de yapısal sayılır"* denmeyecek —
D-129'da denmedi, D-155'te denmedi, burada da denmeyecek. Tek bir tanımlı
kurucu hücre, *"yapısal"* iddiasını **çürütmeye yeter**, çünkü iddia
*"olamaz"* biçimindedir.

> **KURAL B2 (bağlam, gerekçe DEĞİL):** aynı dosyanın gen2→gen3 hücreleri de
> sayılır, **ama B'yi haklı çıkarmak için kullanılamaz** (§2'nin tablosu).
> Yalnız şu soruyu cevaplar: *desen gen1'e mi özgü, yoksa eski fizikte gen2 de
> mi ölüydü?* İkincisi çıkarsa **B tek başına yetmeyebilir** ve bu bir
> **uyarı** olarak yazılır.

### 4. Sonrasında ne yapılacak — üç yol, önceden yazılı

| B1 | ne yapılır |
|---|---|
| **9/9 `Var = 0`** | B uygulanır: ön-kayıt taslağına *"ebeveyni gen ≥ 2 olan geçişler"* kuralı + kurucu nesil sınırı yazılır, G ve tohum bütçesi **G − 2** üzerinden yeniden hesaplanır (kuyruk 2.2) |
| **≥ 1 hücre tanımlı** | ⛔ B'nin gerekçesi düşer ⇒ kayda **öyle** yazılır, kuyruk 2.4b **yeniden açılır**, karar Yasin'e döner |

⚠ **Her iki yolda da kuyruk 2.6 (kurucu nesil kapısı) gerekli kalır** —
bayrak, hangi tasarım seçilirse seçilsin durumu **görünür** kılıyor.

### 5. Sınırlar (ilan)

- Sınama öncülün **yalnız birinci yarısını** test ediyor (§2).
- C2 **3 tohum**; 9 hücre bağımsız değil (tohum başına 3 kol aynı çevreyi
  paylaşıyor) ⇒ etkin n **3'e yakın**, 9'a değil.
- Hiçbir sabit bu okumaya bakılarak seçilmiyor; B bir **kapsam** kararıdır,
  bir eşik kararı değil (§2.7 kapsam dışı).

---

## D-157 · 2026-08-20 · ✅ **B1 GEÇTİ: kurucu neslin dejenerasyonu yapısal** — ⛔ **ama B2 uyardı: B gerekli, YETERLİ DEĞİL**

D-156'nın ön-taahhüdü uygulandı. Okunan nicelikler yalnız `z_variance` ve
`selection_estimable`. ⛔ `selection` · `transmission` · `delta_zbar` · kol
farkı · işaret **okunmadı**; `to_landmark.max` **hiç açılmadı** (kapalı soru).

---

### 1. KURAL B1 — kurucu geçiş: **0 / 9 ölçülebilir** ⇒ öncül **doğrulandı**

C2 (`c2_population_n8_g3_s3.json`, tohum 9911–9913 × üç kol):

| tohum | kol | alan | `z_variance` | estimable |
|---|---|---|---|---|
| 9911 | lived · null · shuffle | resource | **0** (üçü de) | ❌ |
| 9912 | lived | energy | **0** | ❌ |
| 9912 | **null · shuffle** | — | ⛔ **Price satırı YOK** (`price = {}`) | ❌ |
| 9913 | lived · null · shuffle | resource | **0** (üçü de) | ❌ |

⇒ **Var(z) > 0 olan kurucu hücre sayısı: 0.** Ön-taahhüdün çürütücü şartı
(*"≥ 1 hücrede `Var > 0`"*) **ateşlenmedi** ⇒ **B uygulanır.**

⚠ **K4 — kendi paydam tutmadı, ilan ediyorum.** D-156'da *"9 hücre"* yazmıştım;
gerçekte bu geçiş **7 Price satırı** üretti, iki hücre (`s9912 null`,
`s9912 shuffle`) **hiç satır üretmedi**. Karar değişmiyor — satırı olmayan
hücre *"tanımlı"* olamaz, yani çürütücü şart iki okumada da ateşlenmiyor —
ama **tahmin ettiğim sayı yanlıştı ve düzeltilmeden geçirilmiyor.**
(Bu, D-145'in 4. kusurunun bağımsız tekrarıdır.)

⭐ **Sonda-3'ün iki kurucu hücresiyle birlikte: 4 tohum · 3 kol · 11 kurucu
hücre, ölçülebilir olan 0.** İki ayrı fizikte (D-152 öncesi ve sonrası) aynı.

⇒ 🔒 **İlan:** *Bu tasarımda kurucu neslin seçilim geçişi ölçülemez, ve bu
tohuma bağlı bir kaza değil mekanizmanın sonucudur* — kurucular özdeş doğar,
farklılaşmanın tek kaynağı adapter'dır (D-129/D-130), ve adapter **ancak
birinci nesil bittikten sonra** doğar.

---

### 2. KURAL B2 (bağlam) — ⛔ **B tek başına yetmiyor**

Aynı dosyanın gen2→gen3 hücreleri (**eski fizik** — D-152 aktarım yolunu
değiştirdi ⇒ **B'yi haklı çıkarmak için kullanılamaz**, D-156 §2):

| tohum | kol | alan | estimable |
|---|---|---|---|
| 9911 | lived | **energy** | ❌ (`Var = 0`) |
| 9911 | lived · null · shuffle | resource | ✅ (0.00189159, üçü de) |
| 9912 | lived | **energy** | ✅ (0.0540837) |
| 9912 | shuffle | **energy** | ❌ |
| 9912 | null | — | ⛔ Price satırı yok |
| 9913 | lived · null · shuffle | resource | ❌ (`Var = 0`) |

⇒ Kurucu nesil atıldıktan **sonra bile** hücrelerin yalnız **4'ü** ölçülebilir.

⛔⛔ **Ve ön-kayıtın ilan ettiği birincil alanla (`energy`, D-144) bakılınca
tablo daha da sert:** `energy` yalnız **s9912 lived**'de ölçülebilir. Birincil
karşıtlık `lived ↔ shuffle` (YENİ-1) **iki kolun da** tanımlı olmasını
istediğine göre, eski fizikte **`ΔCov` hiçbir tohumda tanımlı olmazdı (0/3).**

⚠ **Bu D-145'in 1. ve 2. kusurunun bağımsız tekrarıdır** — ve B onlara
**dokunmuyor**. B yalnız *garantili ölü* hücreyi ölçümün dışına çıkarıyor.

⭐ **Karşı-veri, ve zayıf:** sonda-3'te (bugünkü fizik) gen2→gen3'ün **iki
kolu da** `energy`'de ölçülebilir çıktı ⇒ o tohumda `ΔCov` **tanımlı olurdu**.
⚠ **n = 1.** İki fizik arasındaki farkın D-152'den mi tohumdan mı geldiği
**bilinmiyor**, ve bu koşumla bilinemez.

---

### 3. ⇒ Ne yapıldı, ne yapılmadı

✅ **Yapıldı:** B ön-kayıt taslağına **tasarım kuralı (YENİ-4)** ve **sınır
(L21)** olarak yazıldı; L17 ve L20 taze ölçümle güncellendi.

⛔ **Yapılmadı, çünkü karar:** **G kaç olacak.** B ile bir koşumun
kullanılabilir geçiş sayısı **G − 2**'ye düşüyor ⇒ bugünkü `G = 3` **tohum
başına tek geçiş** bırakıyor. G'yi 4'e çıkarmak koşumu ~1.5 kat uzatır ve
doğrudan **bütçe slotunun** (§7, SLOT 3 **AÇIK**) konusudur — ki o slot zaten
D-145'in **A/B/C kararını** bekliyor. ⇒ **Tek bir karar noktasında birleşti**
ve Yasin'in.

⛔ **Ve B2'nin gösterdiği asıl darboğaz alan kararı** (D-145 kusur #2): alan
tohuma bağlı olduğu sürece, kurucu nesli atmak tanımlılığı **kurtarmıyor**.
⇒ Kuyruk **2.2**'ye bu bağlandı.

### 4. Sınırlar

- B1 öncülün **birinci yarısını** doğruladı; ikinci yarısı (*gen ≥ 2 tanımlı*)
  bugünkü fizikte hâlâ **n = 1**.
- C2'nin 9 hücresi bağımsız değil (tohum başına 3 kol ortak çevre) ⇒ etkin n
  **3'e yakın**.
- §2 tablosu **eski fizik**; oran olarak taşınamaz, yalnız *"B yeterli mi"*
  sorusuna uyarı üretir.
- Hiçbir sabit bu okumayla seçilmedi; B bir **kapsam** kararıdır.

---

## D-158 · 2026-08-20 · ✅ **Kuyruk 2.5 — aktarım kapısı sayaçlandı** (saf raporlama, GPU'suz)

**Borç (D-155 §2, K6):** sonda-3 ölçtü ki **32 varisin 0'ı** somatik ölçek
taşıyor, ama **hangi kapının** adayı yuttuğu sonuç dosyasından okunamıyordu ⇒
teşhis **çıkarım** olarak kaldı. *"Biliniyordu"* ile *"bilinmiyordu"* arasında
pratik fark yoktu.

### 1. Ne yapıldı

`select_for_transfer` artık geçtiği her adayı **kendi dallarında** sayıyor;
sayaç `consolidate_generation` tarafından açılıyor, `GenerationRecord`'a
takılıyor, koşucu **ajan satırına** `transfer_gates` olarak yazıyor.

| sayaç | ne demek |
|---|---|
| `candidates` | kapıya giren aday sayısı |
| `dropped_recall` | `recall_count < GENERATION_MIN_RECALL` ⇒ hiç hatırlanmamış |
| `trauma` | recall'ı geçenler içinde **travma sınıfı** anı (bir kader değil, **sınıf** sayacı) |
| `warning_low` | ⭐ **alt bant yolu** — uyarı doğdu, salience çıtası **atlandı** |
| `dropped_salience` | `memory_score < GENERATION_TRANSFER_THRESHOLD` |
| `warning_high` | ⭐ **üst bant yolu** — uyarı doğdu, ama çıtayı **geçtikten sonra** |
| `dropped_drift` | travma ama `drift < DRIFT_TRANSFER_MIN` |
| `standard` | normal aktarım |

⭐ **Hesap değişmedi** — hiçbir dal, hiçbir eşik, hiçbir sıra. Sayaç
eklenmeden önce ve sonra `select_for_transfer` **aynı listeyi** döndürüyor.

### 2. §2.8 — rapor aleti **takip ediyor**, tekrar etmiyor

⛔ **Reddedilen alternatif:** kapının yanında duran, koşulları **yeniden
uygulayan** bir `transfer_gate_report(...)` fonksiyonu. Bu tam olarak §2.8'in
hatası olurdu (U2/U3a deseni): rapor, artık var olmayan bir kapıyla
**hemfikir** kalabilirdi. Sayaçlar **dalın içine** kondu.
⚠ Ve sayaç **koşulsuz** yazılıyor — çağıran istemese bile yerel bir sink
açılıyor — çünkü *"yalnız raporlama açıkken say"* ikinci bir kod yolu demek,
ve gerçek deneyde koşan yol **test edilmemiş** olan olurdu (K3).

### 3. Kontroller

- **K2** ✅ — dört aday, **dört farklı kader**, tek çağrıda; ve iki farklı
  **bantla** iki ayrı çağrı (alt/üst uyarı yolları ayrı sayılmalı, çünkü
  ikisi salience çıtası karşısında **farklı davranıyor**). Koşucu testi
  **iki ajanlı**.
- **K3** ✅ — iki ayrı çağrı yeri testi: `consolidate_generation` sayacı
  **kendisi açıyor mu**, ve sayaç **sonuç dosyasına** ulaşıyor mu.
- **K5** ✅ — **8 mutasyon, 8 doğru test kırılması.** Her turda md5
  doğrulandı (`generation.py` tabanı `1d9343d2`, geri yükleme birebir),
  `-p no:cacheprovider`, `__pycache__` **silindi**, `PYTHONDONTWRITEBYTECODE=1`
  (D-148'in üç şartı).

| # | mutasyon | sonuç |
|---|---|---|
| Q1 | `dropped_recall` sayacı kaldırıldı | 1 failed ✅ |
| Q2 | `dropped_salience` kaldırıldı | 1 failed ✅ |
| Q3 | `dropped_drift` kaldırıldı | 1 failed ✅ |
| Q4 | alt bant uyarısı **üst bant diye** sayıldı | 1 failed ✅ |
| Q5 | sayaç `GenerationRecord`'a yazılmıyor | 1 failed ✅ |
| Q6 | `standard` kaldırıldı | 1 failed ✅ |
| Q7 | sayaç **sonuç dosyasına** yazılmıyor | 1 failed ✅ |
| Q8 | girdi sayacı kaldırıldı | **2** failed ✅ |

- **Suite:** `618 → 622 passed, 2 deselected`.

### 4. Ne **ölçmedi** — ilan

⛔ **Bu madde bir sayı üretmedi, bir soru üretilebilir hâle getirdi.** Sayaçlar
ancak **gerçek bir koşumda** dolar; bugünkü değerleri stub kararlardan geliyor
ve **hiçbir teşhis dayanağı değildir** (D-138'in PE_w doygunluğunda öğrenilen
ders).
⇒ **Bitti ölçütü karşılandı** (üç sayaçtan fazlası dosyada · K2 · K3 · K5),
ama D-155 §2'nin sorusu (*"recall mi, `is_trauma` mı"*) **bir sonraki gerçek
koşumda** cevaplanacak.

⚠ **`trauma` sayacı §2.11'in iki okumasından `is_trauma(record)` olanıdır** —
`n_at_or_above_trauma` (PE-delta kanalı) **başka bir niceliktir** ve sayaç
onunla karıştırılmamalı. İkisinin örtüşmesi **hâlâ ölçülmedi**.

---

## D-159 · 2026-08-20 · ✅ **Kuyruk 2.6 — I5.5 kapısı bağlandı**, ve kapı ilk bakışta **C2'nin 5 ölü geçişini** buldu

**Borç (D-155 §6, K6):** kurucu neslin dejenerasyonunu yakalayan **kapı yoktu**.
*"Sıfır, çünkü yapı gereği"* ile *"sıfır, çünkü seçilim yok"* sonuç dosyasında
**aynı görünüyordu**, ve C2 tam bu durumu `run_quality = clean` diye
raporlamıştı — D-149'un I5.4'te bulduğu desenin aynısı.

### 1. Kapı ne yapıyor — **iki yönlü**

`I5.5` (**FLAG**), `check_selection_estimable_where_claimed`:

| durum | verdict |
|---|---|
| ebeveyni **gen ≥ 2** olan bir geçişte **hiçbir alan** `selection_estimable` değil | ⛔ **bayrak** — ön-kayıtın okuduğu kısım ölü |
| **kurucu** geçiş (ebeveyn = gen 1) ölçülemiyor | ✅ **beklenen** — YENİ-4 onu kapsam dışı ilan etti, ayrıntıda yazılır |
| ⭐ **kurucu** geçiş **ölçülebilir çıkarsa** | ⛔ **bayrak** — YENİ-4 kullanılabilir veriyi atıyor demektir ⇒ **D-157'nin yeniden açılma tetiği** |

⇒ Kapı aynı zamanda **D-156/D-157'nin kapsam kuralının bekçisi**: kural iki
yönde de kırılabilir ve ikisinde de sessiz kalmıyor.

⚠ **FLAG, ABORT değil**, ve gerekçesi yazılı: ölçülemeyen bir geçiş **evren
hakkında meşru bir bulgudur** (D-123'ün *"evren null'ı"*), bozuk bir alet
değil. ABORT, deneyin raporlamaya razı olduğu sonucu **kaydetmeyi
reddederdi**. Kabul edilemez olan şey onu **`clean`** diye raporlamaktı.

### 2. ⛔ Kuyruk 2.6'nın kendi tarifini değiştirdim — **ve ölçümle**

**2.6 şöyle yazıyordu** (benim kalemimden, D-155 §6): *"ebeveyn kümesinin
`F_agent` **ve** uç nokta yayılımı **ikisi birden** sıfırsa bayrak."*

⛔ **Uygulamaya geçerken C2 bu tarifi çürüttü:**

| | `f_agent_spread` | kurucu `Var(z)` |
|---|---|---|
| s9911 (üç kol) | **0.0079** (sıfır değil) | **0** |
| s9913 (üç kol) | **0.0101** (sıfır değil) | **0** |
| s9912 (üç kol) | 0.0 | 0 |
| s9913 lived gen2→gen3 | **0.1595** | **0** |

⇒ *"İkisi birden sıfır"* koşulu C2'nin **9 kurucu hücresinin 6'sını
kaçırırdı** — yani kapıyı gerektiren koşumların tam da üzerinde **yeşil**
yanardı. Ve `s9913 lived`'de yayılım **0.16** iken uç nokta yine ölü.

⇒ **Karar veren nicelik `selection_estimable`'dır**; `F_agent` yayılımı
**ayrıntıda raporlanır, verdict'e girmez**. ⚠ Bu bir tasarım daraltması değil
**bir düzeltme**: eski tarif ölçülünce yanlış çıktı (§2.11 — çelişki sessizce
seçilmedi, kayda yazıldı). Ve tarifi yazan bendim, Yasin değil.

### 3. ⭐ Kapı geriye dönük koşuldu — **ilk bakışta bir kusur buldu**

| dosya | verdict |
|---|---|
| `probe3_endpoint_s9916.json` (sonda-3) | ✅ **geçti** — *"4 geçiş; 2 kurucu (YENİ-4 ile kapsam dışı), 2 puanlanan ve ölçülebilir"* |
| `c2_population_n8_g3_s3.json` (C2) | ⛔ **bayrak** — puanlanan **6 geçişin 5'i** ölü: `s9912 null`, `s9912 shuffle`, `s9913 lived`, `s9913 null`, `s9913 shuffle` |

⛔⛔ **C2 bunu `clean` raporlamıştı.** Kapı olsaydı, D-123'ün *"evren null'ı"*
sonucu koşumun **kendi yüzünde** yazılı olurdu — sekiz oturum sonra elle
kazılarak değil. **K6'nın bedeli üçüncü kez ölçüldü.**

### 4. Kontroller

- **K2** ✅ — iki kol × iki geçiş; hücreleri toplayan ya da yalnız ilkine
  bakan bir sürüm **tek kol/tek geçişle geçerdi**. Sağlıklı kolun ölü kolun
  verdict'ine **karışmadığı** da sınandı.
- **K3** ✅ — kapı `invariants` sözlüğünde, **ve** kaydedilen verdict'in
  gerçek yüklemenin bu koşumun kollarında ürettiği değere **eşit** olduğu
  sınandı (yalnız *"anahtar var mı"* demek yetmiyordu — K5 bunu yakaladı).
- **K5** ✅ — **7 mutasyon, 7 doğru test kırılması.** md5 her turda doğrulandı
  (`run_population_experiment.py` tabanı `1d72f7d8`), `no:cacheprovider` +
  `__pycache__` silme + `PYTHONDONTWRITEBYTECODE=1`.

| # | mutasyon | ilk tur | son |
|---|---|---|---|
| R1 | kurucu muafiyeti kaldırıldı | 2 failed ✅ | ✅ |
| R2 | kurucu ölçülebilirse sessiz kal | 1 failed ✅ | ✅ |
| R3 | ölü geçiş bayrak basmıyor | 2 failed ✅ | ✅ |
| R4 | gen0 geçişi de sayılıyor | ⛔ **SAĞ KALDI** | ✅ test eklendi |
| R5 | kapı bağlantısı koparıldı (`lambda: (True, "skipped")`) | ⛔ **SAĞ KALDI** | ✅ test sıkılaştırıldı |
| R6 | *"hiç geçiş yok"* yeşil sayılıyor | ⛔ **SAĞ KALDI** | ✅ test eklendi |
| R7 | mod ABORT'a çevrildi | 1 failed ✅ | ✅ |

⭐ **Üç mutasyon ilk turda sağ kaldı ve üçü de gerçek bir boşluktu** — özellikle
**R5**: K3 testim *"`I5.5` anahtarı var mı"* diye soruyordu, ki **stub bir
lambda da** o testi geçerdi. Tam olarak D-149'un I5.4'te bulduğu hata sınıfı,
bu kez **kendi testimde**.

- **Suite:** `622 → 628 passed, 2 deselected`.
- **Belge:** `PREFLIGHT_INVARIANTS.md` I5.5 satırı eklendi (**27 madde
  tanımlı**).

### 5. Sınırlar

- Kapı **tanımlılığı** ölçer, **etkiyi değil** (L9) — hiçbir kovaryans değeri,
  işaret ya da kol farkı okumuyor.
- Kurucu muafiyeti **YENİ-4'e bağlı**; YENİ-4 kalkarsa kapının ilk satırı
  yeniden yazılmalı.
- `s9911`'in gen2→gen3 hücreleri `resource` alanında ölçülebilir olduğu için
  **geçti**; ⚠ **birincil alan `energy` ile bakılsaydı düşerdi** — kapı
  *"herhangi bir alan"* diye soruyor, ön-kayıt ise **bir alan** ilan ediyor.
  ⇒ **Alan kararı verilince (kuyruk 2.2) kapı o alana daraltılmalı.**

---

## D-160 · 2026-08-20 · 🔒 **TANIMLILIK PİLOTU — K1 kontrolü + ön-taahhüt, KOŞUMDAN ÖNCE yazıldı**

**Yetki:** Yasin, 2026-08-20: *"önerdiğin şekilde yap"* ⇒ 3 tohumluk tanımlılık
pilotu (~9 sa) onaylandı.

⚠️ **Bu kayıt koşum BAŞLAMADAN önce commit edilmiştir.** Sırası kasıtlıdır
(D-125/D-128/D-154/D-156 deseni): sonra yazılsaydı sayıyı görüp kriteri ona
göre seçmiş olurdum (§2.7 / L9). **Commit sırası bunun kanıtıdır.**

---

### 1. Pilot neyi satın alıyor

⛔ **Bu pilot bir sonuç değil, bir KARAR üretiyor.** Kuyruk 2.2'nin iki
kararı (**alan** ve **bütçe/G**) bugün **tahminle** verilmek zorunda; pilot
ikisini de aritmetiğe çeviriyor.

**Bugünkü kanıt durumu:** `energy` alanının bugünkü fizikte yaşadığına dair
elimizde **tek tohum** var (sonda-3). Aksini söyleyen kanıt (C2, 0/3) **eski
fizikten** geliyor — D-152 aktarım yolunu değiştirdi ve varislerin ayrışması
tam da o yoldan geçiyor (D-157 §2).

⚠️ **Pilotun istatistiği zayıf ve bu ilan ediliyor:** 3 ikili gözlem. Gerçek
oran C2'deki kadar kötüyse (%33) 3/3 görme olasılığı **%3.6**; gerçek oran
%90 ise ≤1/3 görme olasılığı **%2.8**. ⇒ **Uçlarda ayırt edici, ortada kör.**
Bu bir kestirim değil, **ele/geç ekranıdır**.

---

### 2. K1 — mekanizma kontrolü (bağlayıcı, `CLAUDE.md §2.4-b`)

**(a) Ölçülen niceliği hangi mekanizma üretiyor**

`Var(z) > 0` ⇐ hücre içindeki ajanlar farklı drift taşıyor ⇐ soylar ayrışmış
⇐ **iki kanal birden**: varis ebeveynin **adapter'ını** miras alıyor (Kanal 2,
D-102) **ve** D-152'den beri **bandına göre farklı anılar** miras alıyor
(Kanal 1). C2'de ikinci yarı yoktu ve varisler özdeş bitiyordu.

**(b) ⛔ Seçtiğim bayraklardan hangisi bu mekanizmayı kapatır**

| bayrak | etkisi | kararım |
|---|---|---|
| ⛔ `--no-lora` | Kanal 2'yi kapatır ⇒ ayrışmanın yarısı ölür | **KULLANILMIYOR** |
| ⛔ `--mock-llm` | Kararlar kanned ⇒ yaşamlar özdeşleşir, tanımlılık **yapay** çıkar | **KULLANILMIYOR** |
| ⚠️ `--n-generations` | **G−2 = puanlanan geçiş.** G=3 tohum başına **1**, G=4 **2** geçiş verir. Kural 2 iki geçiş **olmadan sorulamaz** | **4** |
| `--events 30` · `--n-agents 8` · `--fresh-pasture` | Deneyle aynı | **aynı** |
| `--arms lived shuffle` | Birincil karşıtlık (D-131); `null` betimleyici | **`lived shuffle`** |
| dış `timeout` | D-126'da replay'i kesti, sonuç dosyası hiç yazılmadı | **YOK** |

⚠️ **G = 4 bu koşumun tek yapılandırma değişikliğidir** ve gerekçesi
sonuçtan bağımsız: **Kural 2 tanım gereği iki puanlanan geçiş istiyor.**

**(c) Bu yapılandırmada dejenere olmadığının **mevcut veriden** kanıtı**

| | sonda-3'ten (aynı fizik, aynı yapılandırma, G=3) |
|---|---|
| puanlanan hücrelerin tanımlılığı | **2/2** ölçülebilir (`energy`) |
| ebeveyn yayılımı | `f_agent_spread` gen2'de **0.154** ve **0.080** (iki kol) |
| Kanal 2 aktif mi | **32/32** varis adapter miras aldı |
| Kanal 1 aktif mi | varis başına **7.19** anı (min 5, maks 11) |
| ölçüm makinesi | I4.1 **identical**, `complete: true` |

---

### 3. 🔒 ÖN-TAAHHÜT — okuma kuralları

**Puanlanan geçiş** = ebeveyni **gen ≥ 2** olan geçiş (YENİ-4 / D-156).
G = 4 ⇒ kol başına **iki** puanlanan geçiş: gen2→gen3 ve gen3→gen4.
**Bir tohum "kullanılabilir"** = en az bir puanlanan geçişte **`energy` alanı
İKİ KOLDA BİRDEN** `selection_estimable`.

> **KURAL 1 — ALAN.** 3 tohumun kaçı kullanılabilir?
> **3/3 ya da 2/3** ⇒ `energy` **birincil alan olarak kalır**, ön-kayıt §3
> değişmez, ve D-145'in 1./2. kusuru ölçümle kapanır.
> **1/3 ya da 0/3** ⇒ `energy` **yaşamıyor**. ⛔ **Bu, skaler `z`'ye geçildiği
> anlamına GELMEZ** — o seçenek kendi ayrı ön-taahhüdüyle sınanır. Bu kural
> yalnız `energy`'yi eler.

> **KURAL 2 — G.** Kaç tohumda **ikinci** puanlanan geçiş, **birincisi
> kullanılamazken** kullanılabilirdi (yani tohumu kurtardı)?
> **≥ 1/3** ⇒ G = 4 kendi +%33'ünü ödüyor, G = 4 önerilir.
> **0/3** ⇒ bu kanıtla G = 4'ün bedeli **haklı çıkmadı**, G = 3 kalır.

> **KURAL 3 — TAVAN RİSKİ.** Puanlanan **hücrelerin** (tohum × kol × geçiş,
> toplam 12) kaçı `energy`'de ölçülebilir?
> **12/12** ⇒ ⛔ **`P_active` tavanda donmuş demektir** — iki kol da her zaman
> tanımlıysa `ΔP_active` yapı gereği sıfırdır ve eş-birincil uç nokta
> **hareket edemez**. Bu, D-145'in 3. kusurunun **tavan** hâlidir ve kilit
> öncesi **yeniden açılır**.
> **1–11 / 12** ⇒ tavan riski gerçekleşmedi, `P_active` yaşayabilir.
> ⚠️ **Bu bir SEVİYE okumasıdır, kol farkı DEĞİL** — `ΔP_active` hesaplanmıyor.

> **KURAL 4 — SOMATİK ZİNCİR (betimleyici, eşiksiz).** D-158'in sayaçları
> (`transfer_gates`) tüm ajanlar üzerinde toplanır ve **hangi kapının** en çok
> aday yuttuğu **adıyla** yazılır. ⛔ Eşik yok, karar yok — D-155 §2'nin
> *"çıkarım"* diye bıraktığı soru **ölçüme** çevriliyor, o kadar.

⛔ **OKUNMAYACAKLAR (L9):** kovaryansın **değeri** · **işareti** · `lived` ile
`shuffle` **arasındaki fark** · etki büyüklüğü · **`ΔP_active`**.
⛔ **`to_landmark.max` açılmayacak** — D-155'te reddedildi, kapalı soru.

---

### 4. Yapılandırma ve komut

**Tohumlar: 9917 · 9918 · 9919** — üçü de taze (`dau_runs/adapters/` altında
**0** eşleşme, kontrol edildi). ⚠️ Pilot **keşifsel**; bu üç tohum deneyde
**kullanılmaz** ⇒ deneyin tohumları **9920+**.

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9917 9918 9919 --n-agents 8 --n-generations 4 --events 30 \
  --lora --fresh-pasture --arms lived shuffle \
  --results dau_runs/pilot_definedness_g4_s9917_9919.json
```

⚠️ Dış `timeout` **YOK** (D-126) · `PYTORCH_CUDA_ALLOC_CONF` **elle verilmez**
(D-116).

**Süre tahmini: ~8 sa 40 dk.** ⚠️ **Tahmin, ve dayanağı yazılı (K4):**
sonda-3 **2 sa 09 dk 47 sn** sürdü, 6 kol-nesil ⇒ kol-nesil başına **~21.6 dk**;
G=4'te kol-nesil sayısı 8 ⇒ tohum başına ~2 sa 53 dk × 3 tohum.
⚠️ **Gerçekçi aralık 7–13 sa** — nişler arası ömür yayılımı 2.3 kat (D-154),
ve süre tahminlerim üçte ikisinde tutmadı.

**Disk:** 51 GB boş; beklenen adapter yazımı ~2.7 GB (192 dizin × ~14 MB).
⚠️ **Tahmin.** Çökme hâlinde `.partial.json` ölçümleri bırakır (D-111).

---

### 5. Koşum bittiğinde ne olur — önceden yazılı

| Kural 1 | ne yapılır |
|---|---|
| **3/3 · 2/3** | `energy` kalır ⇒ Kural 2 G'yi belirler ⇒ §7 bütçe slotu **hesapla** doldurulur ⇒ 2.3 kilit yolu açılır. ⚠️ Kural 3 **12/12** derse kilit **yine durur** — bu kez `P_active` yüzünden |
| **1/3 · 0/3** | ⛔ `energy` elenir. Büyük koşum **başlatılmaz**. Ertelenen **A yolu** (kıtlık rejimi, D-082/D-084) gerekçesiyle Yasin'e döner |

⛔ **Hiçbir dalda kural gevşetilmez.** *"2/3 olmadı ama 1/3 de fena değil"*
denmeyecek — D-129'da, D-155'te denmedi.

### 6. Sınırlar (ilan)

- **3 tohum.** Uçlarda ayırt edici, **ortada kör** (§1'in aritmetiği).
- Pilot **keşifsel**; hiçbir sabit ona bakılarak seçilmeyecek (§2.7).
- Kural 1 **yalnız `energy`'yi** sınıyor; başka bir alanın ya da skaler `z`'nin
  yaşayıp yaşamadığı hakkında **hiçbir şey** söylemez.
- `null` kolu yok ⇒ pilot `null` hakkında **hiçbir şey** söylemez.
- G=4, **L10'un ilan ettiği G=3'ten sapmadır** ve yalnız **pilotta** geçerli;
  deneyin G'si Kural 2'nin sonucuyla ayrıca kararlaştırılacak.
- ⚠️ **L11 (adapter sönümü)** G=4'te bir nesil daha derinleşiyor ⇒ dördüncü
  neslin sinyali üçüncüden zayıf olabilir. Bu **tanımlılığı** etkileyebilir ve
  Kural 2'nin sonucu bu etkiyi **içerir**, ondan ayrıştırılamaz.
- **9917–9919 harcanıyor**; deneyin tohumları 9920+.

---

## D-161 · 2026-08-20 · ✅ **TANIMLILIK PİLOTU KOŞTU — dört kural da okundu, ve G=3 olsaydı büyük koşum SIFIR kullanılabilir tohum verecekti**

**Koşum:** `dau_runs/pilot_definedness_g4_s9917_9919.json` · tohum
**9917 · 9918 · 9919** · 8 ajan · **4 nesil** · 30 olay · kollar
`lived shuffle` · `--lora --fresh-pasture` · komut **D-160 §4'ün birebir
aynısı**, dış `timeout` yok.

`complete: true` · `run_quality = flagged` · **I4.1 `identical`** ·
I5.4 ✅ **GEÇTİ** · I4.2 ✗ (beklenen, D-155/S3) · I5.5 ✗ (aşağıda).

**Süre: 6 sa 10 dk 41 sn** (10:38:34 → 16:49:15).
⚠️ **K4 — tahminim yine tutmadı, bu kez TERS yönde ve ilan ettiğim aralığın
DIŞINDA.** D-160'ta *"~8 sa 40 dk, aralık 7–13 sa"* yazmıştım. Hata kaynağı
tespit edildi: sonda-3'ün kol-nesil başına **21.6 dk**'sını taban aldım, bu
tohumlarda gerçekleşen **~14.7 dk** — ömürler daha kısa. ⇒ **Süre modelim
kol-nesil sayısını doğru, birim maliyeti yanlış tahmin ediyor**, ve birim
maliyet tohuma göre **%47 oynuyor**. Bundan sonraki tahminlerde aralık bu
oynamayı içermeli.

⛔ **Okunmayanlar (L9, ön-taahhüt):** kovaryans değeri · işareti · kol farkı ·
etki büyüklüğü · `ΔP_active`. `to_landmark.max` **açılmadı**.

---

### 1. KURAL 1 (ALAN) — **2/3 ⇒ `energy` KALIR**

Puanlanan hücreler (ebeveyni gen ≥ 2), **`energy` alanında**:

| tohum | gen2→gen3 | gen3→gen4 | tohum kullanılabilir mi |
|---|---|---|---|
| **9917** | lived ✗ · shuffle ✗ | lived ✗ · shuffle ✗ | ❌ **hayır** |
| **9918** | lived ✗ · shuffle ✓ | **lived ✓ · shuffle ✓** | ✅ **evet** |
| **9919** | lived ✗ · shuffle ✗ | **lived ✓ · shuffle ✓** | ✅ **evet** |

⇒ **2/3** ⇒ ön-taahhüdün *"3/3 ya da 2/3"* dalı ⇒ **`energy` birincil alan
olarak kalır**, ön-kayıt §3 değişmez, **D-145'in 1. ve 2. kusuru** (alan
nadiren ölçülebilir · alan tohuma bağlı) **bugünkü fizikte kapanır**.

⚠️ **Dürüstlük notu:** 2/3, D-160 §1'de *"ortada kör"* diye ilan ettiğim
banttır. Kural **koşumdan önce** yazıldı ve *"2/3 ⇒ kalır"* diyor; sonradan
*"ama 2/3 zayıf, tohum ekleyelim"* **denmiyor** — bu kuralı gevşetmek olurdu.
Kanıtın zayıflığı **sınır olarak** ilan ediliyor, verdict değiştirilmiyor.

⚠️ **Ve C2'nin `energy` sayısı artık geçersiz sayılmalı:** eski fizikte
0/3 idi, bugünkü fizikte 2/3. Fark D-152'nin aktarım yolu değişikliğiyle
uyumlu ama **kanıtlanmış değil** (tohumlarla karışık).

---

### 2. KURAL 2 (G) — **2/3 kurtarma ⇒ G = 4 kendini ödüyor.** ⭐ Ve asıl sayı bu değil

| tohum | birinci geçiş (gen2→gen3) | ikinci geçiş (gen3→gen4) | ikinci kurtardı mı |
|---|---|---|---|
| 9917 | ✗ | ✗ | — |
| 9918 | ✗ | ✓ | ✅ **kurtardı** |
| 9919 | ✗ | ✓ | ✅ **kurtardı** |

⇒ **2/3 ≥ 1/3** ⇒ **G = 4 önerilir.**

⛔⛔ **Ama tablonun asıl söylediği daha sert: birinci geçiş ÜÇ TOHUMUN
ÜÇÜNDE de kullanılamaz çıktı.** Yani:

> **G = 3 ile koşulsaydı — ki ön-kayıtın ilan ettiği değer buydu (L10) —
> bu üç tohumun HİÇBİRİ kullanılamazdı. 0/3.**

⇒ **S = 12 · G = 3'lük ~24 saatlik koşum, sıfır kullanılabilir tohumla
bitebilirdi.** Pilotun 6 saati **tam olarak bu felaketi** satın aldı, ve
gerekçesi tahmin değil **ölçüm**.

⚠️ Sebep muhtemelen soyların ayrışmak için **iki nesil** istemesi (varis önce
adapter + anı miras alıyor, ayrışma bir sonraki nesilde görünür hâle geliyor).
⚠️ **Bu bir mekanizma çıkarımı, ölçüm değil.**

---

### 3. KURAL 3 (TAVAN RİSKİ) — **5/12 ⇒ tavan gerçekleşmedi** ✅

12 puanlanan hücrenin **5'i** `energy`'de ölçülebilir.
⇒ **12/12 değil** ⇒ `P_active` **tavanda donmuş değil**, eş-birincil uç nokta
**hareket edebilir**.

⚠️ D-145'in 3. kusuru (`ΔP_active` sıfır-şişkinliği) **çözülmedi** — yalnız
**tavan** hâli gerçekleşmedi. Taban tarafı hâlâ bütçe hesabının konusu.
⚠️ Bu bir **seviye** okumasıdır; `ΔP_active` **hesaplanmadı**.

---

### 4. KURAL 4 (SOMATİK ZİNCİR) — ⭐ **I5.4 İLK KEZ GEÇTİ**

**D-158'in sayaçları ilk kez doldu** (2733 aday, tüm ajanlar):

| kapı | sayı | payı |
|---|---|---|
| `candidates` | **2733** | — |
| `dropped_recall` | **501** | %18 — ⭐ **en çok aday yutan kapı** |
| `dropped_salience` | **0** | — |
| `standard` | 2148 | %79 |
| `trauma` (sınıf sayacı) | **84** | %3 |
| `warning_low` | 38 | ↓ |
| `warning_high` | 35 | ↓ |
| `dropped_drift` | 11 | ↓ |

⭐ **Zincir kapanıyor ve aritmetiği tam:** `38 + 35 + 11 = 84` — travma sınıfı
her adayın kaderi sayılmış durumda. ⇒ **Travma anısı nadir (%3), ama ortaya
çıktığında %87'si uyarıya dönüşüyor.** Darboğaz *"uyarıya dönüşme"* değil,
**travma sınıfı bir anının recall kapısından sağ çıkması**.

⭐⭐ **Ve varise ULAŞIYOR — D-155'in bulamadığı şey:**

| | sonda-3 (D-155) | bu pilot |
|---|---|---|
| `has_somatic_scale` | **0 / 32** ❌ | **34 / 144** ✅ |
| `has_inherited_warning` | 0 / 32 | **34 / 144** |
| `I5.4` | `never applied` ❌ | ✅ **`applied 918x`** |

⇒ **GAP-3'ün somatik yarısı ilk kez canlı**, ve **D-152 vaadini SONUNDA
tuttu** — sonda-3'te tutmamış görünmesinin iki sebebi ölçüldü:

**(a) Birinci varis kuşağı YAPISAL olarak sıfır:**

| varisin derinliği | somatik ölçek |
|---|---|
| 1. kuşak | **0 / 48** ❌ (sonda-3: **0/16**, birebir aynı) |
| 2. kuşak | 14 / 48 ✅ |
| 3. kuşak | 20 / 48 ✅ |

⭐ **Sebep, kurucu neslin dejenerasyonunun ta kendisi:** birinci kuşağın
ebeveynleri **kurucular** ve hepsi özdeş ⇒ **düz hücre** ⇒ göreli bant kimseyi
`low`/`high` diye adlandıramıyor (D-152'nin kendi koruması: düz hücrede
`normalize_fitness` `None` döner) ⇒ **uyarı doğmuyor.**
⇒ **Aynı kök sebep iki ayrı arızayı üretiyor:** `Var(z) = 0` **ve** somatik
kanalın ölü görünmesi. **Bu, D-155/D-157'nin bulgusunun bağımsız teyididir.**

**(b) Tohuma bağlılık güçlü:** s9917 **0/48** · s9918 **15/48** · s9919
**19/48**. ⇒ Sonda-3 tek tohumdu ve **"s9917 gibi" bir tohuma denk gelmiş**.

⭐ **Ve iki arıza AYNI tohumda buluşuyor:** Kural 1'de kullanılamayan tek tohum
**s9917**, somatik ölçeği sıfır olan tek tohum da **s9917**.
⚠️ **n = 3, ve bu bir gözlem, iddia değil** — ama *"soylar ayrışmıyorsa ne
kovaryans ne miras uyarısı doğar"* tek-sebep okumasıyla uyumlu.

---

### 5. I5.5 kapısı taze veride çalıştı ✅

Dün bağlanan kapı (D-159) bu koşumda **4 ölü hücre** işaretledi:
`s9917 lived gen3→gen4` · `s9918 lived gen2→gen3` · `s9919 lived gen2→gen3` ·
`s9919 shuffle gen2→gen3`.
⇒ Koşum `flagged` damgalandı. **Kapı olmasaydı bu koşum da `clean` görünürdü.**

---

### 6. ⇒ Bütçe artık ARİTMETİK (D-160'ın satın aldığı şey)

**Ölçülen girdiler:** tohum kullanılabilirliği **2/3 ≈ 0.67** (G = 4) ·
tohum başına süre **~1 sa 58 dk** (ana koşum; replay tohum başına değil,
koşum başına ~18 dk).

| hedef | koşulacak tohum | süre |
|---|---|---|
| 8 kullanılabilir | ~12 | **~24 sa** |
| 12 kullanılabilir | ~18 | **~36 sa** |
| 20 kullanılabilir | ~30 | **~59 sa** |

⚠️ **`0.67` üç tohumdan geliyor** — güven aralığı geniş (%9–%99). Sayı
gerçekte %40 ise 12 kullanılabilir tohum ~30 koşum tohumu ister.
⚠️ Süre modeli **%47 oynayabiliyor** (§başlangıç).

⛔ **Kalan karar Yasin'in (kuyruk 2.2):** kaç kullanılabilir tohum, ve
**kestirim mi test mi** (D-145'in A/B'si). Alan ve G artık **kararlaştırıldı**.

### 7. Sınırlar (ilan)

- **3 tohum.** Kural 1'in 2/3'ü, önceden *"ayırt edici değil"* diye ilan
  edilen bantta. Verdict kurala göre verildi, **kanıt zayıf**.
- Pilot **keşifsel**; hiçbir sabit ona bakılarak seçilmedi.
- `null` kolu yok ⇒ pilot `null` hakkında **hiçbir şey** söylemiyor.
- Kural 2'nin *"iki nesil gerekiyor"* açıklaması **çıkarım**; ölçülen şey
  yalnız *"birinci geçiş 3/3 ölü, ikinci 2/3 canlı"*.
- **G = 4, L10'un G = 3'ünden sapmadır** ⇒ ön-kayıt §2 ve L10 güncellenmeli.
- ⚠️ **L11 (adapter sönümü)** dördüncü nesilde bir kat daha derin; Kural 2'nin
  sonucu bu etkiyi **içerir**, ondan ayrıştırılamaz.
- **9917–9919 harcandı** ⇒ deneyin tohumları **9920+**.

---

## D-162 · 2026-08-20 · ✅ **KATMAN 1 KARARI: kademeli kıtlık** + 🔒 **K1 kontrolü ve ön-taahhüt — KODA DOKUNULMADAN ÖNCE yazıldı**

**Yetki:** Yasin, 2026-08-20: *"onaylıyorum"* — `docs/PHYSICS_LAYER_PROPOSAL.md`
§6'nın üç sorusu. Üçüncüsünde (pilot boyu) iki seçenek sunulmuştu; **önerilen
olan alındı: 3 tohum, G = 4.**

⚠️ **Bu kayıt kod değişmeden önce commit edilmiştir.** Sırası kasıtlıdır
(D-154/D-156/D-160 deseni): sonra yazılsaydı kuralı çıktıya göre seçmiş
olurdum (§2.7 / L9).

---

### 1. ⛔ Önce: bu kararın dayandığı teşhis **düzeltildi**

Bu katmanı *"kıtlık ısırmıyor"* gerekçesiyle önermeye başlamıştım. **Kod ve
veri ölçüldü, gerekçe yanlış çıktı** ve düzeltilmeden karara bağlanmadı.

| iddia | durum |
|---|---|
| *"Havuz ısırmıyor"* | ❌ **YANLIŞ.** 34 nesil hücresinin **22'sinde** havuz tamamen çöküyor (`pool_ratio_end = 0.000`) |
| *"P0-① çalışmıyor"* | ❌ **YANLIŞ.** Havuzun çöktüğü tohumda (s9917) kurucular **ayrışıyor**: 3 farklı `F_agent`, 3 farklı `Δhavuz`, 2 farklı ömür |
| ⭐ **Doğrusu** | **Havuz iki kararlı durumda:** ya çöker (geç ve şiddetli) ya hiç ısırmaz. **Arada rejim yok.** 4 tohumun 3'ünde birinci nesilde hiç kıtlaşmıyor ⇒ kurucular bit düzeyinde özdeş |

⚠️ **Hatanın kaynağı (K4):** sonda-3'ün **tek** sayısını (`0.757`, birinci
nesil) genelledim. **Bir sayıdan zincir kurdum ve zincir çürüktü.**

⇒ Bu, D-081'in *"kademeli kıtlık yok, kıtlık **anı** var"* tespitinin
**doğrudan kanıtı**, ve değiştirilecek şey kıtlığın **varlığı değil biçimi**.

---

### 2. Karar — Katman 1

**Stoka oranlı hasat tavanı.** Bir ajanın bir olayda alabileceği miktar,
**sırası geldiğinde kalan** stokla orantılı bir tavana tabi olur:

```
cap_i    = EXTRACTION_LIMIT_RATIO × (kalan_stok / N)
alınan_i = min(talep_i, cap_i, kalan_stok)
```

⭐ **Tavanın KALAN stoktan hesaplanması tasarımın çekirdeğidir** — ayrışmayı
üreten şey budur. Rotasyon (D-104) farkın **kalıcı** olmasını engeller,
**var olmasını** değil (D-079/D-083).

⛔ **Talep (`EXTRACTION_DEFECT = 8.0`) DEĞİŞMİYOR.** Talep davranıştır; ona
dokunmak **K7 ihlali** olurdu. Değişen şey **ortamın karnesi** — D-082 §P.5'in
ölçütü budur ve aksiyomu ihlal etmez.

### 3. ⭐ Sabit — yeni serbest parametre **yok**

```
EXTRACTION_LIMIT_RATIO = EXTRACTION_DEFECT / POOL_INIT = 8.0 / 80.0 = 0.10
```

**Türetme, sonuca bakmadan:** *"azami talebin, başlangıçtaki kişi başı stokta
tam olarak bağlayıcı hâle geldiği oran."* Başlangıçta tavan **= talep** (eksik
yok); stok bir adım düşer düşmez eksik alma **başlar** ve stokla birlikte
**kademeli** büyür.

⇒ Değer **iki mevcut sabitin oranı**; hiçbir koşum verisi girmiyor. §2.7
karşılanıyor — `LANDMARK_EVENT`'in `METABOLIC_GRACE_EVENTS`'e bağlanmasıyla
**aynı** türetme biçimi. Kodda **ifade olarak** yazılacak, sayı olarak değil,
ki türetme kaybolmasın (§2.8).

⚠️ **AMADS'ın `0.12`'si taşınmıyor.** Yasin'in önceki çalışmasından alınan şey
**form** (stoka oranlı tavan, 45/45 koşumda çöküş üretti) ve **türetme
disiplini**; **değer değil** — ölçek farklı.

### 4. K1 — mekanizma kontrolü (pilot için, bağlayıcı)

**(a) Ölçülen niceliği hangi mekanizma üretir**
tavan bağlar → eksik alma doğar → sıralı servis sırayı gradyana çevirir →
hasat farkı → `metabolic_gain` → enerji farkı → ömür/drift farkı → `Var(z) > 0`

**(b) ⛔ Hangi bayrak bu mekanizmayı kapatır**

| bayrak | etkisi | kararım |
|---|---|---|
| ⛔ `--mock-llm` | talepler kanned ⇒ tavanın bağlayıp bağlamadığı **stub'ın özelliği** olur | **KULLANILMIYOR** |
| ⛔ `sequential=False` | tavan herkese **aynı** uygulanır ⇒ gradyan doğmaz | **`SEQUENTIAL_ACCESS` açık kalır** |
| ⛔ `rotate=False` | fark **kalıcı** olur; ölçtüğümüz şey konum avantajı olurdu | **`ROTATE_ACT_ORDER` açık kalır** |
| `--no-lora` | Kanal 2'yi kapatır | **KULLANILMIYOR** |
| dış `timeout` | D-126 | **YOK** |

**(c) Dejenere olmadığının **mevcut veriden** kanıtı**
s9917'de havuz çöktüğünde kurucular **zaten ayrıştı** (3 farklı `F_agent`) ⇒
mekanizma **var ve çalışıyor**; bu katman onu **her tohumda** çalışır hâle
getiriyor. ⚠️ **Kanıt tek tohum.**

### 5. 🔒 ÖN-TAAHHÜT — pilotun okuma kuralları

**Pilot:** tohum **9920 · 9921 · 9922** (taze), N = 8, **G = 4**, 30 olay,
kollar `lived shuffle`, `--lora --fresh-pasture`. ~6–9 sa.

> **KURAL P1 — kıtlık kademeli mi oldu?**
> 3 tohumun **en az 2'sinde**, birinci nesilde ilk eksik alma **olay ≤ 3**'te
> gerçekleşti ⇒ ✅ tavan bağlıyor. Aksi hâlde ❌ **katman vaadini tutmadı.**

> **KURAL P2 — kurucular ayrışıyor mu?**
> **6 kurucu hücrenin en az 4'ünde** `Var(F_agent) > 0` ⇒ ✅.
> ⚠️ **Bugünkü taban: 8 hücrenin 2'si** (yalnız s9917). Kural bunun **üstünü**
> istiyor, eşitini değil.

> **KURAL P3 — zincirin geri kalanı kendiliğinden oynadı mı?** *(betimleyici,
> EŞİKSİZ)*
> `k` dağılımı · `cooperate` sayısı · tanımlılık oranı · `null`'ın donmuşluğu
> **okunur ve yazılır**. ⛔ **Eşik yok, bilerek:** *"bir kaldıraç üçünü birden
> oynatır"* benim **iddiam**; ona kural koymak onu çürütülemez kılardı.
> Tutmadıysa **tutmadı** diye yazılır.

⛔ **OKUNMAYACAKLAR (L9):** kovaryans değeri · işareti · kol farkı · etki
büyüklüğü · `ΔP_active`.

### 6. Ne yapılacak, ne yapılmayacak

**Değişecek:** `dau/society/environment.py` — `realized_extractions_sequential`,
`realized_extractions`, sabit bloğu. **Yeni kapı `I5.6`** (FLAG): bir nesilde
hiçbir olayda `talep > alınan` olmadıysa bayrak ⇒ tavan bağlamadıysa koşum
bunu **kendi yüzünde** söyler (K6).

**Değişmeyecek:** `EXTRACTION_DEFECT` ve karar→çıkarım eşlemesi · bütün
`POOL_*` sabitlerinin **değerleri** · `metabolic_gain` · landmark · travma
eşiği · fitness bantları · prompt · adapter yolu · Katman 2/3/4.

### 7. İlan edilen bedeller

| bedel | büyüklüğü |
|---|---|
| ❌ **Bütün sayılar sıfırlanır** | pilot · sonda-3 · C2 **karşılaştırılamaz** olur |
| ⚠️ Enerji geliri düşer | hasat 8.0 → 3.7'de kazanç **0.400 → 0.325** (**−%19**; `metabolic_gain` içbükey olduğu için, doğrusal olsa −%54) |
| ⚠️ Kriz kanalı ateşlenmeyebilir | havuz artık çökmüyorsa çöküş kaynaklı krizler kaybolur ⇒ **K6 (D-070) yeniden bakılmalı** |
| ⚠️ Rotasyon gradyanı kısabilir | D-083 rotasyonun yayılımı **4.5 kat** kıstığını ölçtü |
| ⚠️ Ön-kayıt taslağı yeniden yazılacak | `G = 4` kalır; alan kararı **yeniden sınanmalı** |

### 8. Projeksiyon — ⚠️ **hesap, ölçüm değil**

Gerçek sabitlerle, 8 ajan, hepsi DEFECT, 30 olay: eksik alma **olay 2**'de
başlıyor (bugün: olay 17), tur içi yayılım **0.33–0.56** (D-083 bugünkü
kuralla **0.071** ölçmüştü ⇒ ~5–8 kat), havuz **%36'da dengeleniyor** ⇒ çöküş
**soğurucu olmaktan çıkıyor**.
⚠️ **Bunlar tahmindir**; pilot ölçecek.

---

## D-163 · 2026-08-20 · ⚠️ **D-162'nin SABİTİ DEĞİŞTİ — uygulama sırasında bir kanalı öldürdüğü ölçüldü**

**Yetki:** Yasin, 2026-08-20: *"D ya önerdiğin gibi"*.

⚠️ **Bu kayıt D-162'yi düzeltir.** D-162 append-only olduğu için orada
düzenlenmedi; **karar burada revize edilmiştir** ve `environment.py`'deki
gerekçe bu kayda işaret eder.

---

### 1. Ne oldu

D-162 sabiti şöyle türetmişti:
`EXTRACTION_LIMIT_RATIO = EXTRACTION_DEFECT / POOL_INIT = 0.10`
(*"azami talep başlangıç stokunda tam bağlayıcı olsun"*).

⛔ **Kod yazılırken ortaya çıkan sonuç ölçüldü ve kabul edilemez:** tavan
konunca havuz artık sıfıra çakılmıyor, bir **dengeye** oturuyor ve denge
kapalı formda:

```
r·p = REGEN·p·(1 − p/kapasite)   ⇒   denge = 1 − r/REGEN
```

`r = 0.10` için **denge = 0.333**, kriz eşiği ise **0.30** ⇒ havuz eşiğin
**hep üstünde** kalır ⇒ ❌ **kriz kanalı yapısal olarak ölür.**

⇒ **Sabit seçimi aslında "havuz nerede duracak" seçimidir.** D-162 bunu
görmemişti; oradaki türetme *başlangıç* hakkındaydı, oysa belirleyici olan
**yörüngenin sonu**.

### 2. Neden bu kabul edilemez — ölçüldü

| | sayı |
|---|---|
| Kriz kanalının bugün ateşlendiği yaşam | **127 / 192** (pilot) · **144 / 216** (C2) |
| Toplam kriz olayı | **1461** (pilot) · 1386 (C2) |
| Ön-kayıt bağı | **D-070 / K6:** *"S5'in ilk travması = commons krizi"* |

⇒ `r = 0.10` **ön-kayıtlı bir kanalı sessizce silerdi.**

### 3. Yeni türetme

```
denge = COLLAPSE_EPSILON  ⇒  EXTRACTION_LIMIT_RATIO = POOL_REGEN_RATE × (1 − COLLAPSE_EPSILON)
                            = 0.15 × 0.95 = 0.1425
```

**Ölçüt yapısal:** *evren, kodun kendi tanımladığı rejimleri (normal → kriz →
çöküş) kat edebilmelidir.* Hiçbir koşum verisi girmiyor; `LANDMARK_EVENT`'in
`METABOLIC_GRACE_EVENTS`'e bağlanmasıyla aynı standart. **Yeni serbest
parametre yok** — yine iki mevcut sabitin ifadesi.

### 4. Üç aday, gerçek sabitlerle hesaplandı

| | `r` | türetme | ilk eksik alma | landmark'tan önce? | kriz / 30 olay | **landmark penceresinde yayılım** |
|---|---|---|---|---|---|---|
| **bugün** | — | — | olay 17 | ❌ | 20 | ❌ **0.0000** |
| A | 0.1000 | `DEFECT / POOL_INIT` | olay 1 | ✅ | ❌ **0** | 0.5361 |
| B | 0.1050 | `REGEN × (1 − KRİZ)` | olay 1 | ✅ | ❌ **0** | 0.5290 |
| **D** ✅ | **0.1425** | `REGEN × (1 − ÇÖKÜŞ)` | **olay 6** | ✅ | ✅ **15** | ✅ **0.3923** |

⭐⭐ **Tablonun asıl bulgusu son sütun:** bugün, birincil uç noktanın okunduğu
**landmark anında ortamdan gelen ayrışma tam olarak `0.0000`**. C2'nin ve
sonda-3'ün *"kurucular bit düzeyinde özdeş"* sonucu burada **tek bir sayıya**
indi — ve bu katmanın gerekçesi artık bu sayıdır.

✅ **D'nin landmark'tan önce açılması tesadüf değil, ölçüt:** D-084 kapasite
tartışmasında aynı kriteri kullanmıştı — *"kıtlık anı < `LANDMARK_EVENT`"*.
Olay 6 < 10 ⇒ gradyan, uç nokta okunmadan önce mevcut.

### 5. Gerçek kodla doğrulama (`step_pool`, 8 ajan, hepsi DEFECT)

| olay | havuz oranı | ilk / son alan | tur içi yayılım |
|---|---|---|---|
| 5 | 0.555 | 8.000 / 8.000 | 0.0000 *(tavan henüz bağlamıyor)* |
| **6** | 0.514 | 8.000 / 7.453 | **0.5475** |
| **10 (landmark)** | 0.394 | 6.479 / 5.713 | **0.7660** |
| 20 | 0.248 | 4.078 / 3.596 | 0.4821 |
| 30 | 0.179 | 2.953 / 2.604 | 0.3491 |

Kriz **15 / 30** olayda aktif. ⚠️ Bunlar hepsi-DEFECT varsayımıyla; gerçek
koşumda talep karışık olacağı için havuz **daha yüksek** kalır ve bu sayılar
**üst sınır** değil, **senaryo**dur.

### 6. Ders (K4'ün akrabası)

⚠️ **Bir sabitin türetmesi "temiz" olması onu doğru yapmıyor.** A da B kadar
temiz türetilmişti ve ikisi de bir kanalı öldürüyordu. Fark ölçümden çıktı:
*"bu sabit sistemin hangi rejimlerini erişilebilir bırakıyor?"* sorusu
türetmenin **parçası** olmalı.
⇒ **Bundan sonra:** bir hasat/havuz sabiti önerilirken **denge noktası ve
hangi eşiklerin altında/üstünde kaldığı** aynı kayda yazılır.

### 7. Değişmeyen her şey

D-162'nin §5 ön-taahhüdü (**P1 · P2 · P3**), K1 kontrolü, pilot yapılandırması
(9920–9922, N=8, G=4, `lived shuffle`) ve okunmayacaklar listesi **aynen
geçerlidir**. Değişen tek şey **sabitin türetmesi ve değeri**.
⚠️ P1'in eşiği (*"ilk eksik alma olay ≤ 3"*) `r = 0.10` varsayımıyla
yazılmıştı; `r = 0.1425` ile projeksiyon **olay 6** diyor ⇒ **P1'in eşiği
`olay ≤ 8` olarak güncellenir**, gerekçesi: eşik *"landmark'tan (10) önce"*
olmayı sınamalı, keyfi bir erkenliği değil.
⛔ **Bu bir gevşetme değil, ölçütün asıl amacına döndürülmesidir** — ve
**pilottan önce** yazılıyor.

---

## D-164 · 2026-08-21 · ⚠️ **KATMAN 1 PİLOTU KOŞTU — P2 tuttu, P1 TUTMADI, ve kriz kanalı sabitin seçilme gerekçesine rağmen öldü**

**Yetki:** Yasin, 2026-08-20: *"devam et run'ı başlat"* — koşum; 2026-08-21:
*"mevcut veriden önce çözümleme yapalım sonra yazmasını yaparız"* — teşhis
önce, kayıt sonra.

⚠️ **Bu kayıt bir sonuç kaydıdır.** Ön-taahhüt **D-162 §5**'te, P1'in
güncellenmiş eşiği **D-163 §7**'de, ikisi de **koşumdan önce** commit'liydi.
Aşağıda hiçbir kural gevşetilmedi, hiçbir eşik sonradan değiştirilmedi.

---

### 0. Koşumun kimliği — tek süreç, kesintisiz

| | |
|---|---|
| Dosya | `dau_runs/layer1_pilot_g4_s9920_9922.json` (+ `.log`) |
| **Süre (ölçüldü, K4)** | 01:38:21 → 09:41:29 = **8 sa 3 dk 8 sn** · tohum başına **2 sa 41 dk** |
| `complete` | **True** · 3 tohum × 2 kol = 6 kol · Traceback/ABORT **0** |
| Yeniden başlatma izi | **yok** — logda tek allocator satırı, tek model yükleme bloğu |
| argv | talimattaki komutla **birebir** · dış `timeout` yok · allocator'ı runner koydu (D-116) |
| Koşum sırasında `.py` değişikliği | **yok** (01:30–09:45 penceresi tarandı); ağaç temiz, HEAD `df46b6a` |

**K1 (b) doğrulandı — mekanizmayı kapatan hiçbir bayrak açık değil:**
`mock=False` · `sequential_access=true` · `rotate_act_order=true` ·
`lora=explicit_on`.

**Kapılar: 7/10 geçti, 3 bayrak** (`run_quality=flagged`, üçü de `mode=flag`):

| kapı | detay |
|---|---|
| `I4.2` | kollar gen3/gen4'e farklı RNG durumundan girmiş — 6 tohum-nesil hücresi |
| `I5.5` | s9922 lived gen2→gen3'te tanımlı alan yok (`max_z_variance=0`) |
| **`I5.6`** | **tavan hiç bağlamadı:** s9922 lived gen1 · gen4 · shuffle gen1 · gen3 · gen4 |

---

### 1. KURAL P1 — kıtlık kademeli mi oldu? ❌ **TUTMADI**

Ölçüt (D-163 §7): *3 tohumun **≥2'sinde**, birinci nesilde ilk eksik alma
**olay ≤ 8***

| tohum | gen1'de ilk eksik alma | ölçüt |
|---|---|---|
| **9920** | olay **9** | ❌ |
| **9921** | olay **2** | ✅ |
| **9922** | **hiç olmadı** (0/88 satır) | ❌ |

⇒ **1/3.** Kural 2/3 istiyordu. **P1 tutmadı.** `I5.6` kapısı aynı şeyi
bağımsız olarak raporladı.

⛔ **Gevşetme yok.** s9920 eşiği bir olay kaçırdı (9 vs 8) ve landmark'tan
(10) hâlâ önceydi; bu **kaydedildi, kural değiştirilmedi** — D-129'da,
D-155'te, D-161'de de değiştirilmemişti.

⚠️ **Ve §5'in teşhizi bu okumayı daha da sertleştirdi:** P1'in tek geçen
tohumu **kanıtlanabilir biçimde tasarlanan mekanizmadan gelmiyor** ⇒
mekanizma için gerçek sayı **0/3**.

### 2. KURAL P2 — kurucular ayrışıyor mu? ✅ **TUTTU**

Ölçüt: *6 kurucu hücrenin **≥4'ünde** `Var(F_agent) > 0`* (bugünkü taban: 8'de 2)

| tohum | lived | shuffle |
|---|---|---|
| 9920 | ✅ 8 benzersiz `F_agent` | ✅ 8 |
| 9921 | ✅ 8 | ✅ 8 |
| 9922 | ❌ 1 (Var = 0) | ❌ 1 |

⇒ **4/6 ⇒ kural yazıldığı gibi tuttu.**

⛔ **İlan edilen sınır:** gen1'de iki kol **birebir aynıdır** (adapter henüz
yok) ⇒ 6 hücre yapısal olarak **3 bağımsız tohum**, okuması fiilen **2/3**.
Ve **aynı tohum (9922) hem P1'i hem P2'yi düşürüyor** ⇒ iki başarısızlık
**bağımsız değil**. Kural 6 üzerinden yazılmıştı; verdict değişmiyor, **sınır
ilan ediliyor** (D-161'in dürüstlük notu deseni).

### 3. KURAL P3 — zincirin geri kalanı oynadı mı? *(eşiksiz, betimleyici)*

| okunacak | sonuç |
|---|---|
| **`k` dağılımı** | ⚠️ **192/192 ajan `resource_load`** (4483 ajan-olayın tamamı). **Hiç oynamadı.** ⇒ D-137'nin GAP-10'u yeniden açma tetiği **ateşlenmedi** |
| **`cooperate` sayısı** | ⛔ **OKUNAMADI** — popülasyon koşumu karar→sonuç dağılımını ne JSON'a ne loga yazıyor. Ön-taahhüt, **aletin üretmediği** bir sayıyı istemiş |
| **Tanımlılık oranı** | **11/17 = %64.7** (alan `energy`). Desen keskin: **bütün gen1→gen2 geçişleri tanımsız** (`z_variance = 0`); gen2→gen3 ve gen3→gen4'ün **12'de 11'i** tanımlı |
| **`null`'ın donmuşluğu** | ⛔ **OKUNAMADI** — `null` kolu bu pilotta koşulmadı (`--arms lived shuffle`, tasarım gereği) |
| *(ek)* `Var(w) > 0` | **18/18 hücrede** ⇒ seviye-0 ön-koşulu her yerde sağlanıyor |
| *(ek)* pozitif kontrol | **16/18 hücrede tanımlı** |
| *(ek)* drift ekseni kazananları | `energy` 4049 · `resource` 351 · `social` 80 · `uncertainty` 3 |

⛔ **L9 uygulandı:** kovaryansın **değeri, işareti, kol farkı, etki büyüklüğü
ve `ΔP_active`** okunmadı.

⭐ **P3'ün iki maddesi okunamadı ve bu bir bulgudur (K6):** ön-taahhüt,
ölçülemeyecek iki nicelik istemişti. Bir kural yazarken *"bu sayıyı hangi kod
satırı üretiyor"* sorusu K1'in (a) şıkkının **raporlama tarafında** da
sorulmalıymış.

---

### 4. TEŞHİS — beş bulgu, hepsi mevcut veriden ve koddan

#### Bulgu 1 — ⛔ Kriz kanalı öldü: **0 / 192 yaşam**

D-163'ün `r = 0.10`'u reddedip `r = 0.1425`'i seçmesinin **tek gerekçesi**
kriz kanalını yaşatmaktı (§2: kanal 192 yaşamın **127**'sinde ateşleniyordu).

| | |
|---|---|
| Kriz olayı (24 hücre, 192 yaşam) | **0** |
| Kriz gören yaşam | **0 / 192** |
| Gözlenen en düşük havuz oranı | **0.375** (kriz eşiği **0.30**) |

⇒ **Sabit kanalı kurtarmak için değiştirildi, kanal yine öldü.** Bu ön-kayıtlı
bir bağdır: **D-070 / kilit K6** *"S5'in ilk travması = commons krizi"* diyor;
o uç nokta bugünkü fizikte **ölçülemez**.

#### Bulgu 2 — Tavan, kanonik talebin belirgin üstünde duruyor

8 ajanla `cap = EXTRACTION_LIMIT_RATIO × (kalan/N) = 14.25 × havuz_oranı`:

| talep | tavanın bağladığı havuz oranı |
|---|---|
| `EXTRACTION_DEFECT` **8.0** | oran < **0.561** |
| `EXTRACTION_COOPERATE` 2.0 | oran < 0.140 |
| başlangıç tavanı (olay 1) | **11.74** |

Havuz koşum boyunca **0.60–0.86** arasında oturuyor ⇒ kanonik DEFECT talebi
için tavan **neredeyse hiçbir zaman bağlayıcı değil**.

#### Bulgu 3 — Eksik almaların çoğu havuzdan değil, **ilan edilen miktardan**

24 hücre `max_shortfall` üzerinden sınıflandırıldı:

| rejim | ölçüt | hücre |
|---|---|---|
| **A — tasarlanan** | küçük gap (≤3) + düşük oran (<0.45) | **2** |
| **B — ilan artefaktı** | gap ≥ 14 ⇒ talep `EXTRACTION_PARSE_MAX = 25`'e yakın | **15** |
| **C — hiç bağlamadı** | — | **5** |
| ? — marjinal | küçük gap, yüksek havuz | 2 |

`decision_to_extraction` metinden miktar ayrıştırıyor (tavan 25.0). Bir ajan
büyük miktar ilan ettiğinde tavan **her havuz oranında** bağlar — ama bu
**kıtlık değil, ilan büyüklüğü**.

⭐ **P1'in tek geçen tohumu için kesin sınır** (`METABOLIC_GRACE_EVENTS = 10`
olduğu için olay 2'de ölüm yok ⇒ N = 8 kesin):

```
olay 1: yenilenmiş stok 659.20 (oran 0.824) → tavan/ajan 11.742
olay 2: yenilenmiş stok ≥ 590.14 (oran 0.738) → tavan/ajan ≥ 10.512   [en kötü durum]
```

⇒ **s9921'in olay 2'deki eksik alması ancak ilan > 10.51 ise mümkündür ve
`EXTRACTION_DEFECT = 8.0`'dan GELEMEZ.** ⇒ P1'in 1/3'ü, tasarlanan mekanizma
için **0/3**.

#### Bulgu 4 — D-163'ün denge hesabı **hiç kurulmadı**

Denge türetmesi (`1 − r/REGEN = COLLAPSE_EPSILON = 0.05`) şunu varsayıyordu:
*her ajan her olayda tavanı alır* ⇒ toplam hasat `= 0.1425 × havuz`.

| | ölçülen |
|---|---|
| Oran 0.65'te tavanların toplamı | **74.1** birim/olay |
| Gerçekleşen toplam hasat | **~36** birim/olay (hücre aralığı 23.6–39.8) |
| Azami yenilenme (oran 0.50) | **30.0** birim/olay |

Toplam talep havuzla **orantılı değil** — ajan sayısına bağlı, kabaca sabit.
⇒ `0.1425 p` terimi hiç oluşmadı ⇒ **0.05 dengesi de hiç oluşmadı.**

Havuzu asıl sınırlayan şey tavan değil **ölüm**: hasat (23–40) yenilenmeyi
(25–30) aşıyor → havuz yavaş düşüyor → ajanlar ölüyor → talep düşüyor → havuz
toparlıyor. Sistem **0.6–0.7'de** dengeleniyor. ⚠️ Ölen ajan tavanı da
**gevşetiyor** (`kalan/N`'de N küçülüyor) ⇒ kıtlığa karşı **yapısal negatif
geri besleme**.

#### Bulgu 5 — s9922 gen1: zincir **ilk halkada** koptu

```
pop-lived-s9922-a0 … a7:  F = 0.420587919  ömür = 11  Δhavuz = 50.000000
                          E_lived = 0.452606   landmark_drift = {}
```
Sekiz kurucu **bit düzeyinde özdeş**. D-162 §4(a)'nın zinciri *"tavan bağlar →
eksik alma → sıralı servis gradyana çevirir → …"* diye başlıyordu; tavan hiç
bağlamadığı için sıralı erişimin ayıracağı bir şey olmadı. **Katman 1'in
ortadan kaldırmak için kurulduğu kusurun ta kendisi.**

---

### 5. Kuyruk 2.2'nin beklediği iki sayı — **yeniden ölçüldü**

D-161'in bütçe aritmetiğini besleyen iki sayı Katman 1 öncesi fizikten
geliyordu ve geçersizdi. Bu pilot ikisini de yeniden ölçtü. **Ölçüt D-161 §1
ile aynı:** puanlanan hücre = ebeveyni gen ≥ 2, alan `energy`.

| tohum | gen2→gen3 | gen3→gen4 | kullanılabilir |
|---|---|---|---|
| 9920 | lived ✓ · shuffle ✓ | lived ✓ · shuffle ✓ | ✅ |
| 9921 | lived ✓ · shuffle ✓ | lived ✓ · shuffle ✓ | ✅ |
| 9922 | lived ✗ · shuffle ✓ | lived ✓ · shuffle ✓ | ✅ |

| sayı | Katman 1 öncesi (D-161) | **bugün** |
|---|---|---|
| Tohum kullanılabilirliği | 2/3 | ✅ **3/3** |
| Puanlanan hücre tanımlılığı | (seyrek) | ✅ **11/12** |
| Tohum başına süre | ~1 sa 58 dk | ⚠️ **2 sa 41 dk** (**+%36**) |

⇒ **Katman 1'in tuttuğu asıl vaat burada:** P1 tutmasa da **ölçüm zinciri
belirgin biçimde daha sık tanımlı**. Bütçe kararı (kuyruk 2.2) artık bu üç
sayıyla yapılabilir.

⚠️ **Karşılaştırma sınırı:** D-161 başka fizikten; iki sütun **aynı ölçütün**
iki evrende okunuşudur, kontrollü karşılaştırma değildir.

---

### 6. İlan edilen sınırlar

1. ⛔ **Kriz kanalı bu fizikte ölçülemez** (0/192) ⇒ D-070/K6'nın S5 uç
   noktası askıda.
2. ⛔ **P3'ün iki maddesi (`cooperate` sayısı · `null` donmuşluğu) bu koşumdan
   okunamaz** — biri aletlenmemiş, diğeri kol olarak koşulmamış.
3. ⚠️ **P2'nin 6 hücresi 3 bağımsız tohumdur**; gen1'de kollar özdeştir.
4. ⚠️ **`I4.2` bayrağı açık:** kollar gen3/gen4'e farklı RNG durumundan
   giriyor ⇒ kol karşıtlığı okunacaksa bu **önce** açıklanmalı.
5. ⚠️ **Teşhisin sınıflandırması `max_shortfall` üzerinden yapıldı**; gap
   **dağılımı** JSON'a yazılmıyor ⇒ A/B/C oranları **hücre düzeyinde**
   geçerli, satır düzeyinde değil.
6. ⚠️ **Bulgu 4'ün "~36 birim/olay"ı** `Σ Δhavuz / en uzun ömür` ile türetildi;
   olay-bazlı seri değil, **hücre ortalaması**.

---

### 7. Ders — D-163'ün dersi bir kat derinleşti

D-163 şunu yazmıştı: *"bir hasat/havuz sabiti önerilirken denge noktası da
kayda yazılır."* Bu koşum o kuralın **yetmediğini** ölçtü: denge noktası
yazıldı, **doğru hesaplandı**, ama **evrenin üretmediği bir talep varsayımı
altında**.

> ⭐ **Ek şart:** bir havuz/hasat sabitinin denge noktası, sabitlerin
> **izin verdiği** talebe göre değil, evrenin **fiilen ürettiği** talebe göre
> hesaplanır; ve o talep **ölçülmüş bir sayı** olarak kayda girer.

⚠️ Aynı sınıf hata ikinci kez: türetme temiz, **varsayımı ölçülmemiş**. K4'ün
(*"okunmamış sayı yazılmaz"*) türetmelere uzanan hâli.

---

### 8. Açık kalan karar — **Yasin'in** (D-007), D-165'e

Sabitin ne olacağı bu kayda yazılmıyor, bilerek: teşhis **kaydedilmeden**
sabit önerilirse öneri, çürüttüğü ölçümün içinden seçilmiş olur (§2.7).
Kararın önündeki üç seçenek §1'de (`CLAUDE.md`) listelendi.

---

## D-165 · 2026-08-21 · ⛔ **SABİT DEĞİŞMİYOR — çünkü karar VERİLEBİLİR DEĞİL: `r` bir talep eşiğine bağlı ve o talep ölçülmemiş**

**Yetki:** Yasin, 2026-08-21: *"önerdiğin sırada ard arda işleri yapmanı
istiyorum … duraksamadan gidebildiğin kadar"* — A seçeneğinin uygulanması için
verilmiş yetki.

⚠️ **Yetki kullanılmadı, ve gerekçesi bu kayıttır.** A seçeneği (*"`r`'yi
bandın içinde aşağı al"*) uygulanmadan önce türetildi ve **türetme A'yı
çürüttü**. Değer seçilmedi; §2.3'ün *"adım içinde yeni karar noktası çıkarsa"*
şartı burada **kendi önerimin aleyhine** işletildi.

---

### 1. A seçeneği neydi ve neden çöktü

`CLAUDE.md` §1'de (D-164 ile birlikte) şu bant yazılmıştı — yalnız mevcut
eşiklerden, sıfır koşum verisiyle:

```
denge = 1 − r / POOL_REGEN_RATE
denge < POOL_CRISIS_THRESHOLD (0.30)  ⇒  r > 0.10500
denge > COLLAPSE_EPSILON      (0.05)  ⇒  r < 0.14250
```

Bandın **ikinci** bir şartı sınanmamıştı: **tavan landmark'tan (olay 10) önce
bağlamalı** — D-084'ün ve D-163 §4'ün zaten kullandığı ölçüt.

**Sınandı.** Gerçek `step_pool` cebiri, N = 8, `METABOLIC_GRACE_EVENTS = 10`
olduğu için olay 1–9'da ölüm yok ⇒ N sabit. Tavan bağlamazken havuzun
yörüngesi ve her olayda bağlamak için gereken en büyük `r`:

| olay | havuz oranı | bağlaması için `r ≤` |
|---|---|---|
| 1 | 0.8240 | 0.05386 |
| 5 | 0.7578 | 0.05856 |
| **9** | 0.7077 | **0.06271** |
| 10 *(landmark)* | 0.6968 | 0.06369 |

```
landmark'tan ÖNCE bağlasın   ⇒  r ≤ 0.06271
kriz rejimi erişilebilir olsun ⇒  r >  0.10500
```

⛔ **BOŞ KÜME. Arada 1.67 kat var, örtüşme yok.** ⇒ **`EXTRACTION_LIMIT_RATIO`
için seçilecek bir değer YOK.** A seçeneği bir değer sorunu değilmiş.

### 2. Asıl değişken `r` değil, **talep**

Yukarıdaki hesap ölçülen talebe (`D = 4.438` birim/ajan/olay, D-164) bağlı.
Aynı hesap `D` için çözülürse:

| talep `D` | `r ≤` (olay 9) | bantta uygun `r` var mı |
|---|---|---|
| **4.438** *(ölçülen alt sınır)* | 0.06369 | ⛔ **BOŞ** |
| 6.000 | 0.10259 | ⛔ **BOŞ** |
| **6.078** | 0.10500 | ⭐ **tam sınır** |
| 8.000 *(kanonik `EXTRACTION_DEFECT`)* | 0.19095 | ✅ bandın tamamı |

⭐ **KRİTİK TALEP: `D* = 6.078` birim/ajan/olay.**
`D > D*` ise Katman 1 çalışır ve bant içinde değer vardır;
`D < D*` ise **hiçbir `r` çalışmaz.**

⇒ **Katman 1, talebin `8.0` olduğu bir evren için tasarlandı** — D-163 §5'in
tablosu tam olarak *"hepsi DEFECT"* varsayımıyla hesaplanmıştı. D-164 §4/Bulgu
4 o varsayımın tutmadığını ölçmüştü; bu kayıt **aynı kusurun sabiti seçilemez
kıldığını** gösteriyor.

### 3. ⛔ Ve sonuç **kesinleştirilemedi** — ölçülen sayı bir aralık

`D = 4.438` **gerçekleşen hasattır**, yani talebin **alt sınırı**: tavanın
bağladığı satırlarda talep bundan büyüktü. Üst sınır, her kısa satırın o
hücrenin **en büyük** gap'i kadar olduğu varsayılarak hesaplandı (kaba, bilerek
cömert):

```
ortalama talep ∈ [4.438, 6.578]        D* = 6.078
```

⛔ **`D*` bu aralığın İÇİNDE.** ⇒ *"hiçbir `r` çalışmaz"* iddiası **ölçülen alt
sınır için kurulmuştur, kanıtlanmamıştır.**

⚠️ **Ve sebebi tam olarak D-164'ün P3'te çarptığı duvar:** talep dağılımı ne
JSON'a ne loga yazılıyor. Elimizde **ortalama bile yok, aralık var**.

⇒ **Bu yüzden sabit değişmiyor.** Bir sabiti, değerini belirleyen niceliğin
**ölçülmediği** bir anda seçmek §2.7'nin yasakladığı şeyin ta kendisidir —
ve bu kez yasağı çiğneyecek olan **benim önerimdi**.

### 4. Kararın önündeki üç kaldıraç — büyüklükleriyle

| # | kaldıraç | gereken büyüklük | engel |
|---|---|---|---|
| **I** | **Talep** (`EXTRACTION_PARSE_MAX`, karar→miktar eşlemesi) | ortalama talep **> 6.078** olmalı; ölçülen alt sınır 4.438 ⇒ açık **×1.37** | ⛔ **K7 sınırı** — *"ortamın ayrıştırma kuralı mı, davranışsal önsel mi"* sorusu **Yasin'in** (D-007) |
| **II** | **`POOL_INIT`** (havuz daha aşağıdan başlasın) | tavanın olay 1'de bağlaması için başlangıç oranı `≤ D/(100·r)`: `r = 0.1425`'te **≤ 0.311** ⇒ `POOL_INIT ≤ 31` (bugün **80**) | ⛔ **D-081 kilitli kararı** (Yasin, *"kişi başı 100/80 sabit"*) |
| **III** | Katman 1'i bırak, Katman 2'ye geç | — | ⚠️ kriz kanalı ölü kalır ⇒ D-070/kilit K6'nın S5 uç noktası askıda |

⛔ **Üçü de Yasin'in** (D-007): biri K7'ye, biri kilitli bir karara dokunuyor,
üçüncüsü bir ön-kayıt uç noktasını feda ediyor. Claude Code hiçbirini tek
başına seçmez.

### 5. ⇒ Karardan ÖNCE yapılması gereken tek iş

**Talep dağılımını aletlemek.** Üç kaldıracın **üçünün de** büyüklüğü `D`'ye
bağlı, ve `D` bugün bir aralık. Aletleme:

- **saf raporlamadır** — hesabı değiştirmiyor ⇒ §2.10 altında meşru;
- fiziğin kullandığı **aynı fonksiyondan** okunur (`decision_to_outcome`),
  yeniden türetilmez ⇒ §2.8;
- D-164'ün **P3'te okunamayan** iki maddesinden birini (`cooperate` sayısı)
  aynı hamlede kapatır;
- ve hangi kaldıraç seçilirse seçilsin **gerekli** ⇒ boşa gitmez.

⇒ **D-166'da uygulanıyor.**

### 6. Ders

⚠️ **D-164 §7'nin şartı ilk kullanımında işe yaradı ve bir önerimi öldürdü.**
Şart şuydu: *"denge, evrenin fiilen ürettiği talebe göre hesaplanır."*
Uygulandığında ortaya çıkan şey bir düzeltme değil, **kararın kendisinin
zamansız olduğu** oldu.

> ⭐ **Ek:** bir sabit için bant türetildiğinde, bandın **boş olmadığı** aynı
> turda gösterilir. D-164'ün bandı boş olmadığı **varsayılarak** yazılmıştı;
> bir tur sonra boş çıktı.

⚠️ Ve şu kaydedilsin: bu kayıt bir **geri çekmedir**. `CLAUDE.md` §1'de
*"Claude Code'un önerisi: A"* yazıyordu. **A çürüdü, ve çürüten hesap A'yı
uygulamak için yapılan hesabın kendisiydi.**

---

## D-166 · 2026-08-21 · ✅ **TALEP DAĞILIMI ALETLENDİ — D-165'in kararı bunun üstünde duruyor, D-164'ün P3'ü bunu okuyamamıştı**

**Yetki:** Yasin, 2026-08-21: *"duraksamadan gidebildiğin kadar"*.
D-165 §5 bu işi *"karardan önce yapılması gereken tek iş"* diye adlandırmıştı.

### 1. Neden

İki bağımsız yer aynı eksik sayıya çarptı:

| | |
|---|---|
| **D-164 / P3** | ön-taahhüt `cooperate` sayısını istiyordu; ⛔ **alet onu üretmiyordu** |
| **D-165 / §3** | tavan aritmetiğinin talep terimi lazımdı; elde **sayı değil aralık** vardı (`[4.438, 6.578]`, eşik `6.078` **aralığın içinde**) |

⇒ Karar, ölçülmemiş bir niceliğe bağlıydı.

### 2. Ne yapıldı — **saf raporlama** (§2.10 altında meşru)

| yer | değişiklik |
|---|---|
| `graph.py` · `CommonsRequest` | yeni alan **`outcome: str`** — varsayılan **yok** (§2.9) |
| `graph.py` · `commons_request_from_state` | `decision_to_outcome(decision)` ile dolduruluyor — **fiziğin kullandığı fonksiyonun aynısı, aynı yerde** (§2.8) |
| `graph.py` · `_record_pool_event` | satıra `outcome` yazılıyor |
| `graph.py` | yeni sabit **`POOL_STEP_EMPTY_OUTCOME = "no_decision"`** |
| `run_population_experiment.py` | **`demand_summary(pool_rows)`** → `n_rows` · `requested_mean` · `median` · `p90` · `max` · **`outcomes` histogramı**; nesil kaydına `"demand"` olarak giriyor |

⭐ **Alanın var olma sebebi tek bir ayrım:** `requested = 2.0` hem gerçek bir
COOPERATE'ten hem *"extract 2 units"* diyen bir DEFECT'ten gelebilir
(`decision_to_extraction` metinden miktar ayrıştırıyor, tavan
`EXTRACTION_PARSE_MAX = 25`). **Miktar bu ikisini ayırt edemez; etiket eder.**

⛔ **Hesap değişmedi:** tek satır fizik değişmedi, hiçbir sabitin **değeri**
değişmedi, kapı eklenmedi. `outcome` yalnız yazılıyor, hiçbir yerde okunup
karara girmiyor.

### 3. Kasıtlı test kırılması (Faz kuralı A.3)

`outcome`'a **varsayılan verilmedi** — verilseydi çağıranın unuttuğu yerde
sessizce yanlış bir karar sınıfı kaydedilirdi (§2.9). Bedeli: `_record_pool_event`'i
doğrudan çağıran **iki test** kırıldı ve aynı commit'te gerekçesiyle güncellendi.

### 4. ⚠️ Mutasyon kontrolü — **dört mutasyon, biri kendi testimi çürüttü**

| # | mutasyon | sonuç |
|---|---|---|
| 1 | etiketi karar metninden değil **miktardan** türet | ✅ yakalandı |
| 2 | `POOL_STEP_EMPTY_OUTCOME`'u `"coordinate"` yap (sessiz fallback) | ❌ **YAKALANMADI** |
| 3 | boş nesilde `None` yerine `0.0` döndür | ✅ yakalandı |
| 4 | `cooperate` etiketini `defect`'e katla | ✅ yakalandı |

⛔ **Mutasyon 2 testimin boş olduğunu gösterdi.** Test
`outcome == POOL_STEP_EMPTY_OUTCOME` diyordu — **totoloji**: sabit
değiştirildiğinde test de onunla birlikte değişiyor, yani her koşulda geçiyor.
Bu, §2.4'ün U7/A2 örneğinin **birebir tekrarı**.

⇒ Test, sabite değil **`OUTCOME_*` kümesine** karşı yazıldı
(*"kararın çalışmadığı olay gerçek bir karar sınıfı olarak etiketlenemez"*),
mutasyon tekrarlandı ve **yakalandı**.

⚠️ **Kayda geçsin:** mutasyon kontrolü olmasaydı repoya **işe yaramaz bir
bekçi** girecekti — ve tam da sessiz fallback yasağını koruyan yere.

**Suite:** 636 → **639 passed**, 2 deselected. `no:cacheprovider` +
`__pycache__` silme + md5 doğrulaması uygulandı (K5 / D-148).

### 5. Ne açtı

- D-164'ün P3'ünde **okunamayan** `cooperate` sayısı bundan sonra **okunabilir**.
- D-165'in üç kaldıracının (**talep · `POOL_INIT` · Katman 2**) büyüklüğü
  ölçülebilir hâle geldi.
- ⚠️ **Hâlâ okunamayan:** `null`'ın donmuşluğu — o bir kol meselesi, aletleme
  değil.

---

## D-167 · 2026-08-21 · 🔒 **TALEP ÖLÇÜM KOŞUMU — K1 kontrolü ve ön-taahhüt, KOŞUMDAN ÖNCE yazıldı**

**Yetki:** Yasin, 2026-08-21: *"run da koşabilirsin"*.

⚠️ **Bu kayıt koşum başlamadan önce commit edilmiştir** (D-160/D-162 deseni).
Sonra yazılsaydı kuralı çıktıya göre seçmiş olurdum (§2.7 / L9).

### 1. Neyi ölçüyor ve neden

D-165 tek bir sayıya takıldı: **landmark'tan önceki ortalama talep**.
`D > D* = 6.078` ise Katman 1'in bandında (`0.1050 < r < 0.1425`) çalışan bir
değer **vardır**; `D < D*` ise **hiçbir `r` çalışmaz** ve kaldıraç başka yerde
olmak zorunda. Pilot bu sayıyı **aralık** olarak bırakmıştı (`[4.438, 6.578]`)
ve **`D*` aralığın içinde**. D-166 aleti yazdı; bu koşum sayıyı okuyor.

⭐ **`D* = 6.078` bu kayıttan önce, D-165'te sabitlendi ve koşuma bakılarak
değiştirilmeyecek.**

### 2. Koşum yapılandırması

```
PYTHONHASHSEED=0 python -m dau.diagnostics.run_population_experiment \
  --seeds 9923 9924 9925 --n-agents 8 --n-generations 2 --events 30 \
  --lora --fresh-pasture --arms lived \
  --results dau_runs/demand_probe_g2_s9923_9925.json
```

⚠️ **Tek kol, bilerek:** pilotta birinci nesil `lived` ve `shuffle`'da
**birebir aynı** çıktı (adapter henüz yok) ⇒ gen1 talebi kola bağlı değil.
İkinci kol koşmak aynı sayıyı iki kez ölçerdi.
⚠️ **G = 2, çünkü G = 1 reddediliyor** (*"Price tanımsız"*, D-101).
⚠️ Süre **~2–2.5 sa** — ⚠️ **tahmin**, dayanağı pilotun birim maliyeti
(~20 dk / tohum·kol·nesil). Benim süre tahminlerim üçte ikisinde tutmadı.

### 3. K1 — mekanizma kontrolü (bağlayıcı)

**(a) Ölçülen niceliği hangi mekanizma üretir:**
politika (model + prompt + adapter) → karar metni → `decision_to_extraction`
→ `requested` → satır. Etiketi `decision_to_outcome` veriyor (D-166).

**(b) ⛔ Hangi bayrak bu mekanizmayı kapatır**

| bayrak | etkisi | kararım |
|---|---|---|
| ⛔ `--mock-llm` | kararlar kanned ⇒ ölçülen dağılım **stub'ın** olur | **KULLANILMIYOR** |
| ⛔ `--no-lora` | gen1'i etkilemez ama gen2 talebini üreten kanalı kapatır ⇒ pilotla karşılaştırılamaz | **KULLANILMIYOR** |
| dış `timeout` | D-126 | **YOK** |

**(c) Dejenere olmadığının mevcut veriden kanıtı:** pilot aynı niceliğin
**gerçekleşen** hâlini hücre başına 3.41–5.23 aralığında ölçtü ⇒ nicelik
tohuma göre **oynuyor**, sabit değil.

### 4. 🔒 ÖN-TAAHHÜT — okuma kuralları

> **KURAL M1 — bağlayıcı.** `demand_to_landmark.requested_mean`, **birinci
> nesilde**, 3 tohumun **en az 2'sinde `> 6.078`** ⇒ ✅ Katman 1'in bandı
> **boş değil**, karar *"bantta hangi değer"*e döner (**Yasin'in**).
> Aksi hâlde ⇒ ❌ **D-165'in imkânsızlığı doğrulanır**; kaldıraç **talep** ya
> da **`POOL_INIT`** olmak zorunda, ikisi de **Yasin'in**.

> **KURAL M2 — betimleyici, EŞİKSİZ.** `outcomes` histogramı yazılır:
> `cooperate` · `defect` · `coordinate` · `deadlock` · `no_decision`.
> ⛔ **Eşik yok:** D-164'ün P3'ünde bu madde **okunamamıştı**; şimdi
> okunabiliyor, ama *"karar kanalı canlandı"* benim iddiam olurdu.

> **KURAL M3 — betimleyici.** `median` · `p90` · `max` yazılır ⇒ talebin ne
> kadarı ayrıştırılmış büyük ilanlardan geliyor.

⛔ **OKUNMAYACAKLAR (L9):** kovaryans değeri · işareti · kol farkı · etki
büyüklüğü · `ΔP_active`. ⚠️ Bu koşumda **tek kol** var; kol karşıtlığı
zaten kurulamaz ve **kurulmaya çalışılmayacak**.

⛔ **Hiçbir kural gevşetilmez.** *"2/3 olmadı ama 6.0 da 6.078'e yakın"*
denmez — eşik koşumdan önce yazıldı.

### 5. Ne yapılmayacak

❌ Bu koşumdan sonra **hiçbir sabit değiştirilmeyecek.** M1 hangi cevabı
verirse versin, sıradaki adım bir **karardır** ve Yasin'indir (D-007):
talep K7'nin sınırında, `POOL_INIT` D-081'in kilitli kararı.
Claude Code sonucu okur, kaydeder, **seçmez**.

---

## D-168 · 2026-08-22 · ⛔ **TALEP ÖLÇÜLDÜ — M1 yazıldığı gibi TUTMADI, ama M1'in EŞİĞİ GEÇERSİZ: D-165'in cebrinde hata bulundu**

**Yetki:** Yasin, 2026-08-21: *"duraksamadan gidebildiğin kadar"*; koşum
2026-08-22'de yeniden başlatıldı (*"koşum yarıda kaldı, tekrar başlat"*).

⚠️ **Bu kayıt kendi önceki kaydımı (D-165) düzeltiyor.** D-165 append-only
olduğu için orada düzenlenmedi; hata burada ilan ediliyor.

---

### 0. Koşumun kimliği

| | |
|---|---|
| Dosya | `dau_runs/demand_probe_g2_s9923_9925.json` |
| **Süre (ölçüldü)** | 11:55:45 → 14:05:19 = **2 sa 9 dk 34 sn** · tohum başına **43 dk** |
| `complete` | **True** · 3 tohum × 1 kol × 2 nesil · Traceback/ABORT **0** |
| Kapılar | **9/10** · tek bayrak **`I5.5`** — ⭐ ve *ters yönde*: *"FOUNDER transition is estimable — YENİ-4 discards usable data"* (s9925) |
| ⭐ **`I5.6`** | **GEÇTİ** — tavan **altı nesil hücresinin altısında da** bağladı |

⚠️ **İlk deneme yarıda kaldı** (makine kapandı, s9923 bitmiş, s9924'te kesilmiş).
Yarım çıktı **silinmedi**: `demand_probe_g2_s9923_9925.ABORTED-1303.{json,log}`.
s9923'ün adapter'ları I0.7'nin yolundan çekildi (silinmedi). Koşum **üç tohumla
baştan**, aynı komutla, `.py` değişmeden tekrarlandı.

---

### 1. KURAL M1 — yazıldığı gibi ❌ **TUTMADI**

Ölçüt (D-167 §4): *gen1'de `demand_to_landmark.requested_mean`, 3 tohumun
≥2'sinde `> 6.078`*

| tohum | ortalama talep (landmark penceresi) | ölçüt |
|---|---|---|
| **9923** | **7.325** | ✅ |
| **9924** | **5.125** | ❌ |
| **9925** | **5.450** | ❌ |

⇒ **1/3.** ⛔ **Gevşetme yok** — üç ortalamanın ortalaması `5.967` ve eşiğe
`0.111` uzakta, ama kural *"tohumların ≥2'si"* diyordu ve **öyle okundu**.

**D-167'ye göre bunun anlamı:** *"D-165'in imkânsızlığı doğrulanır."*

---

### 2. ⛔ AMA EŞİK GEÇERSİZ — D-165'in cebrinde hata var

`D* = 6.078` D-165'te şu varsayımla türetilmişti: **havuz `POOL_INIT`'ten,
yani oran `0.80`'den başlar.** Kod okundu (§2.2 — *belgeye değil dosyaya
güven*), **varsayım yanlış**:

```
run_population_experiment.py · shared_pasture():
    pool = per_capita_stock × n_agents        ← kurucunun NİŞİNDEN
run_protocol_c_prime.py · _seed_niche():
    pool = POOL_MAX × rng.uniform(*NICHE_POOL_FRACTION_RANGE)
    NICHE_POOL_FRACTION_RANGE = (0.40, 1.00)
```

⇒ **Başlangıç oranı sabit değil, tohuma göre 0.40–1.00 arasında çekiliyor.**

| tohum | 9917 | 9918 | 9919 | 9920 | 9921 | 9922 | 9923 | 9924 | 9925 |
|---|---|---|---|---|---|---|---|---|---|
| başlangıç oranı | 0.474 | 0.848 | 0.966 | **0.877** | **0.577** | **0.825** | 0.794 | 0.620 | 0.605 |

⛔ **İki hata birlikte ve aynı yönde çalıştı:**

| # | hata | etkisi |
|---|---|---|
| 1 | başlangıç oranı **0.80 sabit** varsayıldı | yörünge yanlış |
| 2 | talep olarak **ömür-boyu gerçekleşen hasat** (4.438) kullanıldı | landmark penceresindeki gerçek talep **5.1–7.3** |

İkisi de tavanın bağlamasını **olduğundan zor** gösterdi.

### 3. ⭐ Düzeltilmiş hesap — bant **BOŞ DEĞİL**, ama **tohuma bağlı**

Aynı `step_pool` cebiri, gerçek başlangıç havuzu ve **ölçülen** landmark
talebiyle, *"tavan olay ≤ 9'da bağlasın"* için gereken en büyük `r`:

| tohum | başlangıç oranı | ölçülen `D` | `r_max` | bantta uygun `r` |
|---|---|---|---|---|
| **9923** | 0.7936 | 7.325 | 0.14366 | ✅ **(0.1050, 0.1425)** — bandın tamamı |
| **9924** | 0.6202 | 5.125 | 0.09476 | ⛔ boş |
| **9925** | 0.6050 | 5.450 | 0.10852 | ✅ **(0.1050, 0.1085)** — ince şerit |

⇒ **2/3 tohumda bant dolu.** Ortak şerit: **`r ∈ (0.1050, 0.1085)`**,
genişliği `0.0035`. ⚠️ **Kırılgan** — üç tohumun üçünde birden çalışan `r`
**yok** (9924 için gereken `r < 0.09476` bandın altında).

⛔ **D-165'in *"BOŞ KÜME"* sonucu yanlıştır ve geri çekilmiştir.**

### 4. ⭐⭐ Ve mekanizma bu koşumda **çalıştı**

`I5.6` geçti; tavan **altı hücrenin altısında** ve **landmark'tan önce** bağladı:

| hücre | ilk eksik alma | kısa satır | havuz sonu |
|---|---|---|---|
| s9923 gen1 · gen2 | **5** · **6** | 60/192 · 49/155 | 0.458 · 0.745 |
| s9924 gen1 · gen2 | **3** · **2** | 43/224 · 39/181 | 0.485 · 0.543 |
| s9925 gen1 · gen2 | **3** · **2** | 57/224 · 75/214 | 0.512 · 0.560 |

⚠️ Landmark penceresinde azami talep **8.0** (6 hücrenin 5'inde) ⇒ bu erken
eksik almalar **ayrıştırılmış büyük ilandan gelemez**, **havuzun çekilmesinden**
geliyor. **Tasarlanan rejim.**

⭐ **Başlangıç oranı ile ilk bağlama arasındaki sıralama temiz:**

| başlangıç oranı | 0.577 | 0.605 | 0.620 | 0.794 | 0.825 | 0.877 |
|---|---|---|---|---|---|---|
| ilk eksik alma | **2** | 3 | 3 | 5 | **hiç** | 9 *(ilandan)* |

⇒ **Katman 1'in çalışıp çalışmadığını belirleyen baskın değişken, `r` de
talep de değil — tohumun çektiği BAŞLANGIÇ NİŞİ.** D-164'ün P1 başarısızlığı
(1/3) bu sıralamayla **birebir uyumlu**: pilotun üç tohumundan yalnız en
düşük başlangıçlı olan (9921, 0.577) erken bağladı.
⚠️ **Bu bir gözlem, kontrollü karşılaştırma değil** — iki farklı koşum, ve
pilotun landmark talebi ölçülmemişti (alet yoktu).

### 5. KURAL M2 — karar sınıfı histogramı *(eşiksiz)*

⭐⭐ **`cooperate` ölü değil, ve azınlık bile değil.**

| | defect | cooperate | deadlock |
|---|---|---|---|
| **bütün koşum** (1190 satır) | **626** | **523 (%43.9)** | 41 |

Landmark penceresinde tohuma göre: s9923 **9/80** · s9924 **29/80** ·
s9925 **34/80**.

⚠️ **D-068'in *"olayların %94–100'ünde DEFECT"* tablosu bugünkü fizik için
geçerli değil.** ⛔ Ama *"davranış canlandı"* demiyorum: D-068 başka fizikte
ve başka bir okuma yoluyla ölçülmüştü; bu iki sayı **karşılaştırılabilir
değil**. Söylenebilecek olan tek şey: **bugün, bu koşumda, karar kanalı
işliyor.**

⚠️ **Sınır:** etiket `decision_to_outcome`'un anahtar-kelime eşlemesinden
geliyor (`cooperate`/`share`/`talk`/`social`). Bu **fiziğin kendi
sınıflandırması** olduğu için hasat miktarını gerçekten belirliyor; ama
metnin gerçekten kısıtlama niyeti taşıyıp taşımadığı **ayrı bir sorudur ve
ölçülmedi**.

### 6. KURAL M3 — dağılımın şekli *(eşiksiz)*

| pencere | median | p90 | max |
|---|---|---|---|
| **landmark** (6 hücre) | 8.00 | 8.00 | **8.00** *(5 hücrede)* · 25.00 *(1)* |
| tam yaşam | 2.00–8.00 | 8.00 | **25.00** *(6 hücrede)* |

⇒ **Talep landmark penceresinde iki değerli:** DEFECT `8.0` ya da COOPERATE
`2.0`. **Ayrıştırılmış büyük ilanlar (`EXTRACTION_PARSE_MAX = 25`) geç yaşam
olgusu.**

⇒ Ortalama talebin aritmetiği kapalı formda: `mean = 8p + 2(1−p)`, `p` =
defect payı. `mean > 6.078` için **`p > 0.680`** gerekiyor; ölçülen paylar
**%88.8 · %55.0 · %57.5**.

⇒ ⭐ **D-164'ün Bulgu 3'ü (*"eksik almaların %63'ü ilandan"*) landmark
penceresi için GEÇERSİZ** — orada ilan enflasyonu yok. Bulgu tam yaşam
penceresi için geçerliliğini koruyor.

### 7. Kriz kanalı — hâlâ **0**

`0 / 48` yaşam, `0` kriz olayı. En düşük nesil-sonu havuz oranı **0.458**,
eşik **0.30**. ⇒ **D-070 / kilit K6'nın S5 uç noktası askıda kalmaya devam
ediyor.**

### 8. İlan edilen sınırlar

1. ⛔ **M1'in eşiği hatalı bir cebirden geldi** ⇒ M1'in *"tutmadı"* verdict'i
   **kayda geçer** ama D-167'nin ona yüklediği anlamı (*"imkânsızlık
   doğrulandı"*) **taşıyamaz**.
2. ⛔ **Düzeltilmiş hesap ÖN-TAAHHÜTLÜ DEĞİL** — koşum görüldükten sonra
   yapıldı. Bir karara temel olacaksa **yeni bir ön-taahhütle** yeniden
   sınanmalı.
3. ⚠️ Düzeltilmiş hesap **tekdüze talep** varsayıyor; gerçek talep iki
   değerli ve ajanlar arasında değişiyor ⇒ `r_max` bir **kestirim**.
4. ⚠️ **Tek kol** koşuldu ⇒ kol karşıtlığı yok, `null`'ın donmuşluğu yine
   okunamadı.
5. ⚠️ Başlangıç oranı ↔ ilk bağlama sıralaması **iki ayrı koşumdan** derlendi.
6. ⚠️ `cooperate` etiketi anahtar-kelime eşlemesidir (§5).

### 9. ⇒ Kararın yeri değişti — ve hâlâ **Yasin'in** (D-007)

D-165 üç kaldıraç saymıştı (talep · `POOL_INIT` · Katman 2). Düzeltilmiş
hesap **dördüncüsünü** ortaya çıkardı ve baskın olan o:

| # | kaldıraç | ölçülen büyüklük |
|---|---|---|
| **0** ⭐ **YENİ** | **`NICHE_POOL_FRACTION_RANGE = (0.40, 1.00)`** | Başlangıç oranı ≤ ~0.62 olan tohumlarda tavan olay 2–3'te bağlıyor; ≥ 0.82 olanlarda hiç bağlamıyor. **Aralığın üst ucu mekanizmayı öldüren tohumlar üretiyor.** |
| I | Talep | `mean > 6.078` için defect payı **> %68**; ölçülen %55–89 |
| II | `POOL_INIT` | ⚠️ **Bu kaldıraç zaten çalışmıyor** — havuz `POOL_INIT`'ten değil nişten başlıyor (§2). D-165'in II'si **geçersiz** |
| III | Katman 2'ye geç | — |

⛔ **Claude Code hiçbirini seçmiyor.** Kaldıraç 0 bir **ön-kayıt aralığına**
dokunuyor, I **K7'nin sınırında**, III bir uç noktayı feda ediyor.

⚠️ **Ve bir sonraki adım ne olursa olsun, ön-taahhüdü yeniden yazılmalı:**
bu turda hem P1'in hem M1'in eşiği **yanlış bir cebirden** türetilmişti.
İki tur üst üste aynı kusur: **türetme temiz, girdisi doğrulanmamış** (§2.2).

---

## D-169 · 2026-08-22 · ⛔ **DR #13 (DAU v3.0 mimari incelemesi) MUTABAKATI — taşıyıcı iddia cebirsel olarak ters, rapordan kod değişikliği ÇIKMIYOR**

**Yetki:** Yasin, 2026-08-22: *"bu iddialar hakkında karşılaştırma yaparak ne
olmalı ne olmamalı … inceleme"* ve *"kayıt olarak yaz"*.

**Tam mutabakat tablosu:** `docs/research/RECONCILIATION.md` **§V**.
Bu kayıt kararı ve **ölçümü** tutuyor.

---

### 1. Ölçüm — raporun taşıyıcı iddiası sınandı

**İddia:** *"DPO kaybı `ln 2`'ye **doyuyor**, gradyan sönüyor, ajan yeni krizde
bile güncellenemiyor (structural null)."*

**Cebir:** `L = −log σ(βΔ)`. Raporun tarif ettiği hâlde marj `Δ` büyük ve
pozitiftir ⇒ `L → 0`. **`L = ln 2` tam olarak `Δ = 0` iken**, yani hiç marj
öğrenilmemişken olur.

**Ölçüldü** (`demand_probe_g2_s9923_9925.log`, 64 eğitim çağrısı):

| | |
|---|---|
| ortalama kayıp | **0.69201** (`ln 2 = 0.69315`) |
| ortalama `\|L − ln2\|` | **0.00343** |
| `ln 2`'nin **altında** | 36/64 |
| ⭐ `ln 2`'nin **üstünde** | **28/64** |

⛔ **`L > ln 2` ⟺ `Δ < 0`** — politika o partide **reddedilen tarafa** kaymış.
*"Çok iyi öğrendiği için donmuş"* bir model bunu üretemez ⇒ **doygunluk
hipotezi ölçümle çelişiyor.**

⚠️ **Ve bu veriden zaten teşhis konulamaz:** `epochs = 1`, `batch = 1`,
`grad_accum = 4`, çift 6–28 ⇒ **eğitim başına 1–7 optimizer adımı**,
`lr = 1e-6`. Beş adımda kayıp `ln 2` civarında olur. **Sınır ilan ediliyor:
`ln 2` gözlemi ne doygunluğun ne dejenerasyonun kanıtıdır.**

⚠️ **Kendi geçmiş metnimiz de düzeltiliyor:** `CLAUDE.md` ve `B2_RESULTS.md`
*"`dpo_loss` 0.6919/0.6940 — `ln 2` = 0.6931, tercih marjı ≈ 0"* diyor. Bu
**doğru** ama eksik: yanına *"ve bu, 1–7 adımlık bir eğitimde beklenen
değerdir"* yazılmalıydı. Rapor o boşluğa **yanlış bir mekanizma** yerleştirdi.

### 2. Kararlar

| # | ne | karar | gerekçe |
|---|---|---|---|
| 1 | **EGI** (epigenetik trait vektörü → sistem direktifi) | ⛔ **ALINMADI** | **Yasak #1 — No trait injection.** Vektör yaşanmışlıktan türetilse de etiket olarak geri verilmesi aksiyomun sınırı ⇒ **aksiyom kararı, Yasin'in** (D-007) |
| 2 | **SVC** (aktivasyon yönlendirme) | ⛔ **ALINMADI** | **Kilit K7 (D-070)** bunu zaten reddetti: *"davranış müdahalesi: hayır — aksiyom"* |
| 3 | **"Saf DPO yığınını kaldır"** | ⛔ **ALINMADI** | Gerekçesi §1'de çürüdü; ayrıca **Kanal 2 kilitli mimari karar** (§4) ve aksiyomun iki kanalından biri |
| 4 | **LoRA-FA · TIES-Merging · RegMean** | ⏸ **ERTELENDİ, elenmedi** | Aksiyoma dokunmuyor (*nasıl eğitelim*, *ne verelim* değil) ⇒ **üçüncü ön-kayıt aday listesine**. ⚠️ Şu an bir sorunu çözmüyor: 1–7 adımda çakışacak gradyan yok |
| 5 | **CKE metriği** | ⛔ **ALINMADI** | İçinde `D_KL(π_g ‖ π_0)` var — **L9'un okunmayacaklar listesiyle çakışıyor**; `S_task` bizde tanımsız |
| 6 | ⭐ **RCI metriği** | ✅ **ALINDI, fizik kararından sonra** | Gerçek bir kör noktaya denk geliyor (§3) |
| 7 | ⭐ **`I5.1`'i popülasyon kapılarına bağla** | ✅ **ALINDI, ŞİMDİ** | Fizikten bağımsız, saf aletleme, **K6 borcu** |

### 3. ⭐ Neden RCI gerçek bir boşluk

`run_population_experiment.py:1338` → `inherit_adapter(parent_id, heir_id)`:
**varis ebeveyninin adapter dizinini miras alıyor** (D-102, Yasin 2026-08-17).
⇒ Adapter'lar nesiller boyunca **fiilen üst üste biniyor**, ve taban temsilin
bozulup bozulmadığı **hiç ölçülmedi, bir kapıya da bağlanmadı**.

`RCI(g) = 1 − H(σ(H^(g))) / H(σ(H^(0)))` — deterministik, GPU'da ucuz, **hiçbir
fiziği değiştirmiyor** ⇒ §2.10 altında meşru.

⚠️ **Neden şimdi değil:** fizik kararı (kaldıraç) beklemede; fizik değişirse
`H^(0)` tabanı da kayar ve ölçüm baştan yapılır.

### 4. ⛔ Brief'in kendi tarifindeki iki hata (bizden çıktı)

| iddia | gerçek |
|---|---|
| *"HippoRAG 2, OpenIE, knowledge graphs"* | **HippoRAG 2 *inspired* PPR**, SQLite domain co-occurrence grafiği üzerinde. **OpenIE yok, üçlü yok, varlık grafiği yok.** PPR canlı skorlama yolunda (`PPR_WEIGHT_IN_SCORE = 0.30`) |
| *"prohibitive VRAM overhead"* | ❌ VRAM 6.1 GB / 8.2 GB, adapter **14 MB**. ⭐ **Ama disk gerçek: `dau_runs/adapters` 16 GB, 1194 dizin** ⇒ ev işleri listesine |

⇒ Raporun **2. sütununun tamamı** bizde olmayan bir makineyi optimize ediyor.
⚠️ **DR #1 ve #2'nin dersi üçüncü kez:** *brief kalitesi girdi kalitesiyle
sınırlı, ve girdiyi biz yazıyoruz.*

### 5. ⚠️ Süreç: şart listesi **ilk kez tamamen boş döndü**

Prompt arXiv ID/DOI istedi; rapor **tek tanımlayıcı vermedi** — yöntem adları
var, kaynak yok, kaynakça yok, boşluk ilanı yok. D-080/D-082'nin üç şartı
**0/3**. Önceki turlarda 12 kimlik hatası bu şartlarla yakalanmıştı ⇒
**bu rapordan kilitli karar yazılamaz** (`CLAUDE.md` girişi).

⚠️ Usul: brief **dosya olarak girmedi**, sohbete yapıştırıldı (D-006 dosya
istiyor) ⇒ ham metin `docs/research/` altında **yok**, izlenebilirlik düşük.

⚠️ **Ve kodu görmeyen ikinci değerlendirme EGI'yi *"EN TAVSİYE EDİLEN &
RİSKSİZ"* diye işaretledi** — Yasak #1 ile K7'nin ikisini de kaçırarak.
Mutabakat adımının neden zorunlu olduğunun bu turdaki kanıtı.

---

## D-170 · 2026-08-22 · ✅ **I5.1 POPÜLASYON KAPILARINA BAĞLANDI** — tanımlıydı, bağlı değildi (D-149'un birebir tekrarı)

**Yetki:** Yasin, 2026-08-22: *"bir diğer adımı önerdiğin şekilde çözelim"* —
D-169 §2'nin 7. kararı.

### 1. Borç

**D-169 ölçtü:** `I5.1` (*PPR grafiğinde hiç kenar var mı*) `preflight.py:1020`'de
**tanımlı** ve `run_cprime_multigen` yolunda **bağlı**, ama popülasyon
koşumunun kapı listesinde **yok**. Son iki popülasyon koşumu on kapı raporladı
ve bu onlardan biri değildi.

⇒ *"PPR sabit katkı verdi"* (`{seed: 1.0}`, GAP-14) ile *"PPR skor verdi"*
**bugüne kadarki her popülasyon koşumunda ayırt edilemez** durumdaydı.
**D-149'un birebir tekrarı** — K6 bu yüzden var.

### 2. Değişiklik — saf aletleme, fizik değişmedi

| yer | ne |
|---|---|
| `preflight.check_ppr_active` | yeni `unit` parametresi (varsayılan `"lives"`). Popülasyon koşucusu **ARM başına tek kasa** tutuyor (P1); altı kol kasasını *"altı yaşam"* diye raporlamak §2.8'in bozulma deseni olurdu. **Mesajı değiştirir, verdict'i asla** |
| `run_arm` sonucu | `"memory_edges": _count_edges(vault.store)` — **burada** okunuyor, çünkü `arm_vault` çıkışta store'u kapatıyor |
| `UNREADABLE_EDGES = -1` | okunamayan kasa **boş grafik değildir**; `I5.1` tam olarak bu ikisini ayırmak için var |
| kapı | **FLAG kalıyor** — PPR'ın koşum yoluna bağlanması mı yoksa atıl ilan edilmesi mi gerektiği **GAP-14 kararı**, kapının kararı değil |

### 3. ⚠️ Kapıyı kaydederken yazdığım yorum **aynı turda çürüdü**

İlk sürüm şöyle diyordu: *"Kenarlar bellek hattının özelliği, modelin değil —
stub da yazar; bu yüzden mock altında da değerlendirilir."*

**Ölçüldü, yanlış:** `write_edge`'in **tek çağıranı** `consolidation.py:106`
ve yalnız **DEEP/TRAUMA** düğümlerini `DOMAIN_EDGE_WINDOW` içinde eşliyor.
Stub duygusal ağırlık biriktirmiyor ⇒ o düğümleri **hiç üretmiyor** ⇒ kapı
*"PPR atıl"* derse **stub hakkında** konuşmuş olur.

⚠️ **`I5.6`'nın ilk sürümü tam aynı hatayı yapmıştı** (D-163: *"arz tarafı
model-bağımsız görünüyordu, ama talep tarafı karardır"*). ⇒ Aynı sınıf hata,
aynı yerde, ikinci kez.

**Düzeltildi:** `--mock-llm` altında `None` kaydediyor (I4.1/I5.4/I5.6
sözleşmesi); stub'lı testlerde `STUB_EXPECTED_FLAGS`'e **beyan edildi** —
susturma değil, *"burada grafik yapı gereği boş"* ilanı.

### 4. ⛔ Hiçbir iddia yapılmıyor — ve yapılamaz

Mock koşum `0` kenar raporladı. **Bu gerçek koşum hakkında kanıt değildir**
(§3). Ve gerçek sayı **diskte de yok**: popülasyon çıktı dosyası
konsolidasyon telemetrisini (`edges_created` · `deleted_count` ·
`strengthened`) **hiç yazmıyor** ⇒ D-051'in düzeltmesi bu yola ulaşmamış.

⇒ **Verdict bir sonraki GERÇEK koşumda okunacak.** Bugün elde olan şey:
o koşum artık **sorabilir**.

⏸ **Açılan küçük borç:** konsolidasyon raporu popülasyon çıktısına da yazılmalı,
yoksa `I5.1` sıfır dediğinde *"konsolidasyon çalışmadı"* ile *"çalıştı, eşleşecek
DEEP düğüm yoktu"* ayırt edilemez.

### 5. Mutasyon kontrolü (K5) — dördü de yakalandı, **ama biri ilk hâlinde değil**

| # | mutasyon | sonuç |
|---|---|---|
| M1 | okunamayan store (`-1`) sıfır sayılsın | ✅ yakalandı |
| M2 | `unit` yok sayılsın | ✅ yakalandı |
| **M3** | kasa okunmasın, sabit `0` yazılsın | ⛔ **İLK TESTTE YAKALANMADI** |
| M4 | kapı başka adla kaydedilsin | ✅ yakalandı |

⛔ **M3:** ilk testim `memory_edges >= 0` diyordu ve **sabit `0` da bunu
sağlıyordu** — stub'ta gerçek değer de `0` olduğu için test *"kasayı oku"* ile
*"sabit yaz"* arasını göremiyordu. Okuma noktası **sentinel** ile pinlendi
(`_count_edges` → 4242), mutasyon tekrarlandı, **yakalandı**.

⚠️ **Bu oturumda mutasyon kontrolünün ikinci kez zayıf test yakalaması**
(ilki D-166/M2, totolojik `outcome == SABIT`). İkisi de repoya **işe yaramaz
bekçi** sokacaktı.

**Suite:** 640 → **644 passed**, 2 deselected. md5 doğrulaması +
`no:cacheprovider` + `__pycache__` silme uygulandı (K5 / D-148).

---

## D-171 · 2026-08-22 · ✅ **KALDIRAÇ 0 SEÇİLDİ: `NICHE_POOL_FRACTION_RANGE` daraltılıyor** + 🔒 **K1 kontrolü ve ön-taahhüt — KODA DOKUNULMADAN ÖNCE yazıldı**

**Yetki:** Yasin, 2026-08-22: *"0. önerisini baştan sona koş"*.

⚠️ **Bu kayıt kod değişmeden önce commit edilmiştir** (D-160/D-162/D-167
deseni). Sonra yazılsaydı kuralı çıktıya göre seçmiş olurdum (§2.7 / L9).

---

### 1. Neden bu kaldıraç

**D-168 ölçtü:** Katman 1'in mekanizması **çalışıyor** — tavan 6 nesil
hücresinin 6'sında da landmark'tan **önce** bağladı. Ama **hangi tohumu
çektiğine bağlı**:

| başlangıç oranı | 0.577 | 0.605 | 0.620 | 0.794 | 0.825 | 0.877 |
|---|---|---|---|---|---|---|
| ilk eksik alma | 2 | 3 | 3 | 5 | **hiç** | 9 *(ilandan)* |

⇒ **Baskın değişken `r` de talep de değil, tohumun çektiği BAŞLANGIÇ NİŞİ.**
Bu kaldıraç tam olarak o değişkene dokunuyor.

### 2. ⚠️ Önce girdiler koddan doğrulandı (D-168'in dersi)

İki tur üst üste eşik **doğrulanmamış bir girdiden** türetilmişti. Bu turda
zincir `grep` ile okundu (§2.2):

```
run_protocol_c_prime.py:697   pool = POOL_MAX * rng.uniform(*NICHE_POOL_FRACTION_RANGE)
run_population_experiment.py  shared_pasture(): pool = per_capita_stock * N
                                                capacity = POOL_MAX * N
⇒ başlangıç ORANI = uniform(*NICHE_POOL_FRACTION_RANGE), N'den BAĞIMSIZ
```

```
environment.py:242  step_pool(): ÖNCE yenilenir, SONRA hasat
⇒ tavan, yenilenmiş stoktan hesaplanır
```

### 3. Türetme — sıfır yeni serbest parametre, sıfır koşum verisi

**Ölçüt:** *"bir nesil, kanonik `EXTRACTION_DEFECT` talebinin tavana **ilk
olaydan itibaren** takıldığı bir havuzdan başlamalıdır."*

```
tavan/ajan   = EXTRACTION_LIMIT_RATIO × POOL_MAX × oran₁  = 14.25 × oran₁
oran₁        = p·(1 + POOL_REGEN_RATE·(1 − p))          ← yenilenme önce
DEFECT bağlar ⟺ 14.25·oran₁ < 8.0 ⟺ oran₁ < T = 0.561404

REGEN·p² − (1+REGEN)·p + T = 0   ⇒   p_max = 0.523990
```

⇒ **`NICHE_POOL_FRACTION_RANGE = (0.40, 0.523990)`**

**Taban `0.40` DEĞİŞMİYOR** — kodun kendi assert'i (`run_protocol_c_prime.py:247`)
tabanın `POOL_CRISIS_THRESHOLD = 0.30`'u aşmasını zaten dayatıyor, ve D-084'ün
*"ölçütü sağlayan en az müdahale"* ilkesi tabanı yerinde bırakmayı söylüyor.

⛔ **Kodda İFADE olarak yazılacak, sayı olarak değil** (D-162 §3), ki türetme
kaybolmasın (§2.8).

### 4. ⭐ BANT BOŞ DEĞİL — aynı turda gösteriliyor (D-165'in dersi)

D-165 bandın boş olmadığını **varsaymıştı** ve bir tur sonra boş çıkmıştı.
Bu kez aralığın her noktası tek tek kontrol edildi:

| `p₀` | `oran₁` | tavan | DEFECT bağlar mı |
|---|---|---|---|
| 0.4000 | 0.4360 | 6.213 | ✅ |
| 0.4500 | 0.4871 | 6.942 | ✅ |
| 0.5000 | 0.5375 | 7.659 | ✅ |
| **0.5240** | 0.5614 | **8.000** | ✅ *(tam sınır)* |

⇒ Genişlik **0.124**, ve **aralığın tamamı ölçütü sağlıyor** — üst uç bir
seçim değil, **en kötü çekilişin garantisi**.

### 5. DENGE NOKTASI (D-163'ün şartı) ve ⭐ bir TAHMİN

`r` **değişmiyor** ⇒ denge de değişmiyor:

```
tavan bağladığında hasat = r·p  ⇒  denge = 1 − r/POOL_REGEN_RATE = 0.0500
```

| eşik | değer | dengenin konumu |
|---|---|---|
| `COLLAPSE_EPSILON` | 0.05 | denge **tam burada** (D-163'ün seçimi, miras) |
| `POOL_CRISIS_THRESHOLD` | 0.30 | **yeni aralığın altında, dengenin üstünde** ⇒ **yol üzerinde** |
| yeni başlangıç aralığı | 0.40 – 0.524 | krizin üstünde başlıyor |

⭐ **TAHMİN (kural değil, ve bilerek eşiksiz):** havuz artık 0.40–0.524'ten
başlayıp 0.05'e doğru gittiği için **kriz eşiği 0.30 yol üzerindedir ⇒ kriz
kanalı ateşlenmelidir.** D-164'te **0/192**, D-168'de **0/48** idi.
⛔ **Ateşlenmezse bu bir bulgudur ve öyle yazılır** — kendi tahminime kural
koymak onu çürütülemez kılardı (D-162 §5'in P3 gerekçesi).

### 6. K1 — mekanizma kontrolü (bağlayıcı)

**(a) Ölçülen niceliği hangi mekanizma üretir**
başlangıç nişi ≤ 0.524 → tavan olay 1'de bağlar → eksik alma → sıralı servis
sırayı gradyana çevirir → hasat farkı → `metabolic_gain` → enerji → ömür/drift
→ `Var(z) > 0`

**(b) ⛔ Hangi bayrak bu mekanizmayı kapatır**

| bayrak | etkisi | kararım |
|---|---|---|
| ⛔ `--mock-llm` | talepler kanned ⇒ tavanın bağlaması stub'ın özelliği olur | **KULLANILMIYOR** |
| ⛔ `sequential=False` | tavan herkese aynı uygulanır ⇒ gradyan doğmaz | **`SEQUENTIAL_ACCESS` açık** |
| ⛔ `rotate=False` | fark kalıcı olur ⇒ ölçülen şey konum avantajı olur | **`ROTATE_ACT_ORDER` açık** |
| `--no-lora` | Kanal 2'yi kapatır | **KULLANILMIYOR** |
| dış `timeout` | D-126 | **YOK** |

**(c) Dejenere olmadığının **mevcut veriden** kanıtı**
D-168: landmark penceresinde talep ≥ 8.0 olan hücre **6/6**; defect payı
**44–71/80 (%55–89)**. ⇒ Tavanın bağlayacağı talep **her hücrede mevcut**.

### 7. 🔒 ÖN-TAAHHÜT — pilotun okuma kuralları

**Pilot:** tohum **9926 · 9927 · 9928** (taze), N = 8, **G = 4**, 30 olay,
kollar `lived shuffle`, `--lora --fresh-pasture`. ⚠️ Süre **~8 sa** — tahmin,
dayanağı Katman 1 pilotunun aynı şekli (8 sa 3 dk).

> **KURAL Q1 — kıtlık her tohumda mı başlıyor?**
> **3 tohumun 3'ünde de**, birinci nesilde ilk eksik alma **olay ≤ 2**.
> **Eşiğin türetmesi:** tavan kanonik DEFECT'i olay 1'de **yapı gereği**
> bağlıyor (§3–4); geriye yalnız o olayda bir DEFECT kararı çıkması kalıyor.
> Ölçülen defect payı ≥ %55 ve N = 8 ⇒ iki olay boyunca hiç DEFECT çıkmama
> olasılığı `(0.45⁸)² ≈ 3×10⁻⁶`. ⇒ **3/3 istemek meşru; 2/3 gevşetme olurdu.**

> **KURAL Q2 — kurucular her tohumda ayrışıyor mu?**
> **3 tohumun 3'ünde de** birinci nesilde `Var(F_agent) > 0`.
> ⚠️ **Kasıtlı olarak tohum başına, hücre başına değil:** D-168 gen1'de iki
> kolun **birebir aynı** olduğunu gösterdi ⇒ 6 hücre yapısal olarak 3 tohumdur.
> Taban: Katman 1 pilotunda **2/3**.

> **KURAL Q3 — zincirin geri kalanı *(betimleyici, EŞİKSİZ)*.**
> `k` dağılımı · **`cooperate` histogramı** (D-166'dan beri okunabiliyor) ·
> tanımlılık oranı · **`I5.1` verdict'i** (D-170'ten beri bağlı) ·
> **kriz olayı sayısı** (§5'in tahmini).

⛔ **OKUNMAYACAKLAR (L9):** kovaryans değeri · işareti · kol farkı · etki
büyüklüğü · `ΔP_active`.

⛔ **Hiçbir kural gevşetilmez.** *"3/3 olmadı ama 2/3 de iyi"* denmez.

### 8. İlan edilen bedeller

| bedel | büyüklüğü |
|---|---|
| ❌ **Sayılar ÜÇÜNCÜ kez sıfırlanıyor** | Katman 1 pilotu (8 sa) ve talep ölçümü (2 sa 9 dk) **taban olmaktan çıkıyor** |
| ⚠️ Ön-kayıtlı bir **aralık** değişiyor | `NICHE_POOL_FRACTION_RANGE` üçüncü ön-kayıt taslağında ilan edilmişti; taslak **kilitli değil** (D-145) ⇒ pencere açık, ama bedel kayda geçiyor |
| ⚠️ Nişin **çeşitliliği azalıyor** | aralık 0.60 → **0.124** genişliğe iniyor ⇒ tohumlar arası ortam farkı küçülüyor; *"tohuma bağlılık"* azalırken **tohum çeşitliliği** de azalıyor |
| ⚠️ Kriz kanalı **canlanabilir** | §5'in tahmini. Canlanırsa D-070/K6'nın S5 uç noktası **askıdan çıkar** — ama travma yükü de artar |
| ⚠️ Enerji geliri düşer | tavan olay 1'den bağladığı için hasat baştan kısıtlı |

### 9. Ne değişmeyecek

`EXTRACTION_DEFECT` · `EXTRACTION_LIMIT_RATIO` · `POOL_REGEN_RATE` ·
`POOL_MAX` · `POOL_CRISIS_THRESHOLD` · `COLLAPSE_EPSILON` ·
`NICHE_POOL_FRACTION_RANGE`'in **tabanı (0.40)** · `metabolic_gain` ·
landmark · travma eşiği · fitness bantları · prompt · adapter yolu ·
Katman 2/3/4 · diğer üç niş aralığı.

---

## D-172 · 2026-08-24 · 🔍 **OKUNABİLİRLİK DENETİMİ (koşum sürerken, SALT-OKUNUR)** — ⛔ ve `I5.1` popülasyon yolunda **yapı gereği sıfır** çıktı

**Yetki:** Yasin, 2026-08-24: *"tüm yapılabilir işleri yap"* — Katman 1b pilotu
koşarken yapılabilecek işler sorulmuş, sınır çizilmiş ve onaylanmıştı.

⚠️ **Bu kayıt koşum SÜRERKEN yazıldı. Tek satır `.py` değişmedi, test suite
koşulmadı, `git checkout` yapılmadı** (§1.8). Kaynak: koşan sürecin kendi
yazdığı `.partial.json` + `grep`.

---

### 1. Neden bu denetim — D-164'ün 8 saatlik dersi

D-164'te ön-taahhüdün **P3'ünün iki maddesi** (`cooperate` ve `null` kolu)
koşum bittikten **sonra** *"okunamadı"* çıktı. Bedeli 8 saatti.

⇒ **Sorulmamış soru:** *ön-taahhüde yazdığım niceliğin, koşumun ürettiği
artefaktta bir KARŞILIĞI var mı?* K1(c) *"mevcut veriden dejenere olmadığını
göster"* diyor; bu onun kardeşi ve **hiç sorulmamıştı**.

⭐ Ve bu tur sorulabilir, çünkü koşum `.partial.json` yazıyor (D-111) —
tohum 9926'nın 1. nesli **13:11'de** diske düşmüştü.

### 2. Koşumun durumu (ölçüldü, tahmin değil)

| ne | ölçüm |
|---|---|
| PID 82377 | `etime` 27:17 @ 13:24 ⇒ başlangıç **2026-08-24 ~12:57** |
| ⚠️ `CLAUDE.md` §1 ne diyordu | *"başlangıç 2026-08-22 ~17:5x"* — **yanlış** |
| gerçek | makine 08-22 koşumunun ortasında kapandı; Yasin bugün **Cursor'dan** yeniden başlattı (uptime 1 sa 36 dk @ 13:24 ⇒ açılış ~11:48) |
| ⚠️ 08-22 denemesi | **hiçbir çıktı bırakmadı** — `ABORTED`/`partial` dosyası yok. D-168'in `…ABORTED-1303.json` deseni bu kez işlemedi |
| temizlik | `pop-*-s9926/9927/9928` adapter dizinlerinin **hepsi bugün 13:05+** ⇒ kalıntı yok, I0.7 temiz başladı |
| GPU | 7289 / 8188 MiB · 87 °C · %100 ⇒ VRAM boşluğu **~900 MiB** |

⛔ **Bu yüzden test suite KOŞULMADI:** torch ayıran herhangi bir test
**koşumu** OOM'a sokabilirdi. Ayrıca `__pycache__` yazardı (K5'in tuzağı).

### 3. Sonuç — D-171 §7'nin beş kalemi

Kaynak: `layer1b_pilot_g4_s9926_9928.json.partial.json`, kol `lived`,
tohum **9926**, nesil **1**, 8 ajan, 172 havuz olayı satırı.

| kural | nicelik | alan | okunabilir mi |
|---|---|---|---|
| **Q1** | ilk eksik alma olayı | `generations[].harvest_shortfall.first_event` | ✅ **okunuyor** |
| **Q2** | `Var(F_agent) > 0` | `generations[].agents[].f_agent` | ✅ **okunuyor** |
| **Q3-a** | `k` dağılımı | `agents[].delta_profile.axes.primary_axis` | ✅ **okunuyor** |
| **Q3-b** | `cooperate` histogramı | `generations[].demand.outcomes` | ✅ **okunuyor** |
| **Q3-c** | tanımlılık oranı | `price_for_previous_transition` | ⏳ gen1'de **yapısal olarak `null`** (önceki geçiş yok) ⇒ gen2'de okunacak. Alan **mevcut** |
| **Q3-d** | **`I5.1` verdict'i** | `invariants["I5.1"]` | ⛔ **okunacak ama BİLGİSİZ** — §4 |
| **Q3-e** | kriz olayı sayısı | `agents[].delta_profile.crisis.n_crisis_events` | ✅ **okunuyor** |

⇒ **Beş kalemin dördü sağlam.** Q3-c gen2'yi bekliyor (yapısal, kusur değil).
**Q3-d bir kusur ve aşağıda.**

### 4. ⛔⛔ BULGU — popülasyon yolunda **konsolidasyon hiç çağrılmıyor**

D-170 `I5.1`'i popülasyon kapılarına bağladı ve kendi borcunu şöyle yazmıştı:
*"`I5.1` sıfır dediğinde «konsolidasyon çalışmadı» ile «çalıştı, eşleşecek DEEP
düğüm yoktu» ayırt edilemez."*

**Zincir `grep`'le sonuna kadar okundu (§2.2) ve gerçek daha keskin çıktı:**

```
store.write_edge            ← TEK çağıran: consolidation.py:106
  └ run_consolidation()       (consolidation.py:41)
      └ memory_bridge.consolidate_run  (memory_bridge.py:113)
          ├ run_cprime_multigen.py:1091      ← TEK SOY yolu
          └ graph.py:2033                    ← ⛔ `if __name__ == "__main__":`
                                                bloğunun İÇİNDE (graph.py:1962)
```

`run_population_experiment.py`, `run_cprime_multigen`'den yalnız
`_count_edges · _decisions · _landmark_reading · install_mock_llm ·
mock_llm_enabled` alıyor — **`consolidate_run` ve `_consolidate_gen1` yok**.
Ve `graph`'ı **modül olarak** import ediyor (`graph_mod`), yani `__main__`
bloğu **hiç çalışmıyor**.

⇒ **Popülasyon koşumlarında `run_consolidation` HİÇ çağrılmıyor.**
⇒ `write_edge` hiç çağrılmıyor ⇒ ilişki grafiği **yapı gereği boş**
⇒ `_count_edges` **0** ⇒ `I5.1` *"PPR is inert"* der — **sistem hakkında
değil, koşucunun kablolaması hakkında.**

⚠️ **Ve bu telemetriden büyük.** `run_consolidation` yalnız kenar yazmıyor;
**budama (`deleted_count`) ve güçlendirme (`strengthened_count`)** de onun
işi. Popülasyon yolunda **hiçbiri olmuyor** ⇒ Ebbinghaus unutması popülasyon
ajanlarında **çalışmıyor**.

⛔ **Ad, boşluğu gizlemiş.** `run_population_experiment.py:1590` şu yorumu
taşıyor: *"Channel 1: end-of-life consolidation for every parent"*. Çağrılan
şey `consolidate_parents → consolidate_generation` ve o fonksiyon
(`generation.py:364`) **yalnız aktarım paketini** kuruyor — `select_for_transfer`
+ `GenerationRecord`. **Uyku konsolidasyonuna hiç dokunmuyor.**
⇒ **§2.8'in deseni en saf hâlinde: rapor aleti tekrar ediyor, takip etmiyor.**

### 5. ⭐ TAHMİN — sayı yazılmadan önce kayda geçiyor

`memory_edges` alanı **D-170'te eklendi**; tamamlanmış hiçbir popülasyon
koşumunda **henüz yok** (D-168'in dosyasında üç kolda da `None`).

> **TAHMİN:** bu koşumun **her kolunda** `memory_edges = 0` ve `I5.1 = false`,
> detay *"memory_edges is empty in every one of the arm vaults — PPR is inert"*.

⛔ **Sıfır çıkmazsa yukarıdaki zincir yanlıştır ve bu da bir bulgudur.**
D-171 §5'in deseni: kendi tahminime kural koymak onu çürütülemez kılardı.

⚠️ **Bu koşumu geçersiz KILMAZ.** Aynı kablolama C2'de, Katman 1 pilotunda ve
talep ölçümünde de vardı ⇒ **sabit**, kollar arası bir terim değil.

### 6. ⚠️ `CLAUDE.md`'de üç eskimiş madde bulundu

| madde | durum |
|---|---|
| *"D-164: `cooperate` sayısı aletlenmemiş"* | ❌ **ESKİMİŞ.** D-166 aletledi. `demand.outcomes` hem D-168'in dosyasında hem bu koşumda **dolu**. D-171 §7 zaten *"D-166'dan beri okunabiliyor"* diyordu; §1 güncellenmemişti |
| ⛔ **`deadlock` üçüncü bir karar sonucu** | Hiçbir belgede **geçmiyor**. Ölçüldü: bu koşum gen1 **9**, D-168 gen1 **4**, gen2 **11**. *"cooperate vs defect"* ikili anlatısı **eksik** |
| *"D-170: konsolidasyon telemetrisi yazılmıyor"* | ✅ **doğru, ve sebebi §4'te** — alan yok çünkü **iş yapılmıyor** |

### 7. Salt-okunur okunanlar *(Q3 eşiksiz ve betimleyici — D-171 §7)*

⚠️ **Tek tohumun tek neslinin tek kolu.** Genelleme değil, kanıt:

```
harvest_shortfall : n_rows=172 · n_short=100 · first_event=2 · max=20.3955
demand            : mean=8.384 · median=8.0 · p90=25.0 · max=25.0
                    outcomes = {cooperate: 91, defect: 72, deadlock: 9}
demand_to_landmark: n_rows=80 · mean=7.800 · {cooperate: 40, defect: 40}
F_agent (n=8)     : var=4.4668e-4 · min=0.4981 · max=0.5741
fitness_class     : high 1 · normal 5 · low 2
reproduction      : f_agent_spread=0.0759 · w_variance=1.25 · w_n_distinct=4
                    w=[2,0,1,2,0,0,3,0] · selection_measurable=TRUE
primary_axis      : resource_load 172 · social_load 0 · uncertainty_load 0
n_crisis_events   : 8 ajanın 8'inde de 0
pool_ratio_end    : 0.4180 · hit_round_cap=False
events_lived      : [21,21,22,21,21,25,21,20] · landmark 8/8
```

### 8. ⚠️ GAP TETİK KONTROLÜ (§2.1 adım 2)

**GAP-10'un yeniden açılma tetiği** (D-137 §7): *"`k` ajanlar arasında
değişkenleşirse"*. **Ölçüldü: 172/172 `resource_load` ⇒ TETİK ATEŞLENMEDİ.**
D-164'te 192/192 idi; **Katman 1b de oynatmadı.** GAP-10 kapalı kalıyor.

### 9. ⛔ OKUNMAYANLAR (L9 — D-171 §7'nin yasağı)

Kovaryans değeri · işareti · kol farkı · etki büyüklüğü · `ΔP_active`
**açılmadı**. `price_for_previous_transition` gen1'de `null` olduğu için
**bakma fırsatı da doğmadı**; gen2'den itibaren **bakılmayacak**.

### 10. K6 — bu kayıttaki kusur nereye bağlandı

⛔ **§4'ün bulgusu bir KAPIYA bağlanamaz** — `I5.1` zaten var ve zaten
raporlayacak; eksik olan **kapı değil, kablolama**. ⇒ Kuyruğa **3.0f** olarak,
bitti-ölçütüyle yazıldı. ⚠️ **Ve düzeltmesi saf aletleme DEĞİL** — popülasyon
yoluna `run_consolidation` eklemek **bellek budamasını açar**, yani koşumun
davranışını değiştirir ⇒ **karar Yasin'in** (D-007, §2.7).

### 11. Reddedilen alternatif

*"Koşumu durdurup kabloyu şimdi düzeltelim"* — **reddedildi.** (a) 27 dakikalık
ilerleme ve temiz bir I0.7 başlangıcı çöpe giderdi; (b) düzeltme bir **karar**
gerektiriyor (§10) ve karar Yasin'in; (c) kablolama **bugüne kadarki her
popülasyon koşumunda aynıydı** ⇒ bu pilot kendi tabanıyla karşılaştırılabilir
kalıyor. ⇒ Koşum **dokunulmadan** devam ediyor.

---

## D-173 · 2026-08-24 · ⭐⭐ **KATMAN 1b PİLOTU: Q1 ve Q2 İKİSİ DE 3/3 TUTTU — mekanizma ilk kez HER tohumda çalıştı, ve kriz kanalı geri döndü**

**Yetki:** Yasin, 2026-08-24: *"0. önerisini baştan sona koş"*.
**Ön-taahhüt:** **D-171 §7**, koşumdan önce commit'li (`4fd266f`, 12:50 —
koşum 12:57:11'de başladı).

---

### 0. Koşumun kimliği

| | |
|---|---|
| Dosya | `dau_runs/layer1b_pilot_g4_s9926_9928.json` |
| **Süre (ölçüldü)** | 12:57:11 → 19:56:22 = **6 sa 59 dk 11 sn** · tohum başına **2 sa 20 dk** |
| `complete` | **True** · 3 tohum × 2 kol × G=4 · Traceback/ABORT **0** |
| Kapılar | **8/11** · bayrak `I4.2` · `I5.1` · `I5.5` |
| ⭐ **`I5.6`** | **GEÇTİ** — tavan **24 nesil hücresinin 24'ünde de** bağladı |
| Koşum sırasında `.py` | **dokunulmadı** — hepsinin mtime'ı 12:51–12:56, koşum 12:57:11 |

⚠️ **Süre Katman 1 pilotundan kısa** (8 sa 3 dk → 6 sa 59 dk; tohum başına
2 sa 41 dk → **2 sa 20 dk**). ⛔ **Sebebi ölçülmedi.** Koşum sürerken
*"muhtemelen ömürler kısalıyor"* demiştim; **ömür ortalaması 25.2** çıktı ve
bu açıklamayı **desteklemiyor**. Gözlem geri çekiliyor, sayı kayda geçiyor.

---

### 1. KURAL Q1 — kıtlık her tohumda mı başlıyor? ✅ **TUTTU (3/3)**

Ölçüt (D-171 §7): *3 tohumun **3'ünde de**, birinci nesilde ilk eksik alma
**olay ≤ 2***

| tohum | ilk eksik alma (gen1) | kısa satır | ölçüt |
|---|---|---|---|
| **9926** | olay **2** | 100/172 | ✅ |
| **9927** | olay **2** | 122/216 | ✅ |
| **9928** | olay **1** | 65/147 | ✅ |

⇒ **3/3.** Ve `I5.6` bunu bütün koşuma yaydı: **24 hücrenin 24'ünde** tavan
bağladı, **20'sinde olay 1'de**, 4'ünde olay 2'de.

⭐ **Karşılaştırma:** Katman 1 pilotu (D-164) **1/3** idi ve bir tohumda tavan
**hiç** bağlamamıştı. Talep ölçümü (D-168) 6/6 bağlamıştı ama **tohuma bağlı**
biçimde (olay 2 ile 9 arasında saçılmış). ⚠️ **Fizik değiştiği için bu bir
kontrollü karşılaştırma değil**, aynı ölçütün üç evrende okunuşudur.

### 2. KURAL Q2 — kurucular her tohumda ayrışıyor mu? ✅ **TUTTU (3/3)**

| tohum | benzersiz `F_agent` | `Var(F_agent)` |
|---|---|---|
| **9926** | **8/8** | 4.47e-4 |
| **9927** | **8/8** | 1.99e-3 |
| **9928** | **8/8** | 1.61e-3 |

⇒ **3/3, ve sekiz kurucunun sekizi de her tohumda ayrı.** Taban: Katman 1
pilotunda **2/3** (ve s9922'de 8 kurucu bit düzeyinde özdeşti).

⭐⭐ **P0-①'in aradığı şey ilk kez her tohumda kuruldu.** D-078'den beri açık
olan *"aynı nişte doğan ajanlar bit düzeyinde özdeş kalıyor"* kusuru, bu
koşumda **hiçbir tohumda görülmedi**.

### 3. KURAL Q3 — betimleyici, eşiksiz

| # | nicelik | ölçüm |
|---|---|---|
| **a** | `k` dağılımı | ⚠️ **4839/4839 `resource_load`** — yine **hiç oynamadı**. GAP-10'un yeniden açılma tetiği (D-137) **ateşlenmedi** |
| **b** | karar dağılımı | `defect` **2823 (%58.3)** · `cooperate` **1859 (%38.4)** · `deadlock` **155 (%3.2)** · `coordinate` **2 (%0.04)** |
| **c** | tanımlılık | **10/16 = %62.5** (alan `energy`) |
| **d** | **`I5.1`** | ❌ **false** — *"memory_edges is empty in every one of the arm vaults"*, altı kolun altısında **`memory_edges = 0`** |
| **e** | **kriz** | ⭐ **1068 olay · 79/192 yaşam** |

⚠️ **Drift ekseni kazananları:** `energy` 4300 · `resource` 470 ·
`uncertainty` 59 · `social` 10.

### 4. ⭐⭐ D-171 §5'in TAHMİNİ **TUTTU** — kriz kanalı geri döndü

D-171 §5, sayı yazılmadan önce şunu ilan etmişti: *"havuz artık 0.40–0.524'ten
başlayıp 0.05'e doğru gittiği için kriz eşiği 0.30 yol üzerindedir ⇒ kriz
kanalı ateşlenmelidir."*

| koşum | kriz olayı | kriz gören yaşam |
|---|---|---|
| Katman 1 pilotu (D-164) | **0** | **0 / 192** |
| Talep ölçümü (D-168) | **0** | **0 / 48** |
| ⭐ **bu koşum** | **1068** | **79 / 192** |

Havuz yörüngesi tahminle uyumlu — nesil sonu oranları **0.223 – 0.671**
arasında, kriz eşiğinin (**0.30**) **altına inen hücreler var**
(s9926 g2: 0.284, g4: 0.292 · s9928 g3: 0.264, g4: 0.223).

⇒ ⭐ **D-070 / kilit K6'nın S5 uç noktası** (*"ilk travma = commons krizi"*)
**askıdan çıktı** — D-164'ten beri ölçülemez durumdaydı.

### 5. ⭐ D-172'nin TAHMİNİ de **TUTTU** — ve teşhisi doğruladı

D-172 §5, okumadan önce şunu yazmıştı: *"bu koşumun her kolunda
`memory_edges = 0` ve `I5.1 = false`, detay «PPR is inert»."*

**Ölçülen:** altı kolun altısında da `memory_edges = 0`; `I5.1` detayı
**birebir** o cümle.

⇒ D-172 §4'ün zinciri doğrulandı: **popülasyon yolunda `run_consolidation`
hiç çağrılmıyor** ⇒ ilişki grafiği yapı gereği boş.
⚠️ **Bu koşumu geçersiz kılmaz** — aynı kablolama C2'de, Katman 1 pilotunda
ve talep ölçümünde de vardı ⇒ **sabit**, kollar arası bir terim değil.
⛔ **Ama Ebbinghaus unutması popülasyon ajanlarında çalışmıyor** ve bu
kapanmamış bir borçtur.

### 6. Durma kuralının (kuyruk 2.2-DURMA) beklediği iki girdi — ölçüldü

| girdi | değer |
|---|---|
| **`q`** (ΔCov'ün tanımlı olduğu tohum oranı) | ⭐ **3/3 = 1.00** |
| **`t`** (tohum başına süre) | **2 sa 20 dk** |

| sayı | Katman 1 öncesi | Katman 1 (D-164) | **bugün** |
|---|---|---|---|
| Tohum kullanılabilirliği | 2/3 | 3/3 | ✅ **3/3** |
| Tohum başına süre | ~1 sa 58 dk | 2 sa 41 dk | **2 sa 20 dk** |

⇒ **Bütçe kararı için gereken aritmetik artık tam.** ⛔ `T_max` (GPU bütçesi)
**hâlâ Yasin'in ilan edeceği sayı** (D-007).

### 7. İlan edilen sınırlar

1. ⚠️ **Fizik üçüncü kez değişti** ⇒ Katman 1 pilotu ve talep ölçümü **taban
   olmaktan çıktı**; yukarıdaki karşılaştırmalar **kontrollü değil**.
2. ⛔ **`I5.1` bu koşum hakkında bilgisiz** — sıfır, sistemin değil koşucunun
   kablolamasının sonucu (D-172 §4).
3. ⚠️ **`I5.5` iki hücrede bayrak:** s9927 gen2→gen3, her iki kolda
   (`max_z_variance = 0`).
4. ⚠️ **`I4.2` bayrağı açık:** kollar gen3/gen4'e farklı RNG durumundan giriyor
   — Katman 1 pilotunda da açıktı. **Kol karşıtlığı okunacaksa önce bu
   açıklanmalı.**
5. ⚠️ **`k` hâlâ tek değerde** (4839/4839) ⇒ `z` **etkin olarak tek boyutlu**
   (GAP-10'un ilan edilmiş sınırı, L8).
6. ⛔ **L9 uygulandı:** kovaryansın değeri, işareti, kol farkı, etki büyüklüğü
   ve `ΔP_active` **okunmadı**.
7. ⚠️ **Süre kısalmasının sebebi ölçülmedi**, ve tahminim (kısa ömür)
   **desteklenmedi** (ömür ort. 25.2).

### 8. ⇒ Ne açıldı

⭐ **Katman 1 ilk kez vaadini tuttu:** kıtlık her tohumda kademeli, kurucular
her tohumda ayrışıyor, kriz kanalı canlı, tohum kullanılabilirliği 3/3.
⇒ **Ön-koşul zinciri artık kurulu.**

⛔ **Sıradaki iş bir KARAR ve Yasin'in:** durma kuralının `T_max`'ı
(kuyruk 2.2-DURMA) — ondan sonra doğrulayıcı koşumun `N`'i ve MDE'si
aritmetikle çıkıyor.
⏸ **Kapanmamış:** popülasyon yolunda konsolidasyon (D-172 §4) · `k`'nin
tek değerliliği · `I4.2`.

---

## D-174 · 2026-08-24 · 🔢 **DURMA KURALININ ARİTMETİĞİ KURULDU** — ⛔ ama kuralın kendi ön-taahhüt şartı **kaçtı**, ve bu ilan ediliyor

**Yetki:** Yasin, 2026-08-24: *"ne yapılacaksa yapabilirsin"*.
⛔ **Üç sayının ilanı bu kayıtta YAPILMIYOR** — kuyruk 2.2-DURMA onları
açıkça Yasin'e bırakıyor (D-007). Bu kayıt yalnız **aritmetiği** kuruyor.

---

### 1. ⛔ ÖNCE: kuralın kendi şartı kaçtı

Kuyruk 2.2-DURMA'nın *bitti sayılır* maddesi şöyle yazıyordu:

> *"üç sayı bir D-kaydında ilan edilmiş, ve kayıt **D-173'ten önce** commit
> edilmiş olacak — sonra yazılırsa kural değil, gerekçelendirme olur."*

| olay | zaman |
|---|---|
| taslak commit'i (`af27e29`) | 24.08 **14:17** |
| **D-173** (pilotun okuması, `9cceac3`) | 24.08 **~20:05** |
| bu kayıt | 24.08 **20:2x** |

⇒ **Şart karşılanmadı.** İlan, okumadan **sonra** yapılacak.

**Bulaşmanın tam yeri, abartmadan:**

| sayı | okumadan etkilenir mi |
|---|---|
| **kaldıraç hakkı** (öneri 1) | ❌ hayır — taslakta **14:17'de** yazılıydı, okumadan önce |
| **`G`** (öneri 4) | ❌ hayır — **D-161**'de ölçümle kararlaştırılmıştı |
| ⚠️ **`T_max`** | ⭐ **EVET** — `t` ve `q` artık biliniyor, yani `T_max` seçmek fiilen **`N_eff` seçmektir** |

⇒ **Sınır olarak ilan ediliyor:** `T_max`'ın ön-taahhüt niteliği **zayıf**.
⚠️ Hafifletici olan ve uydurma olmayan şey: kuralın kendisi *"MDE bir kapı
değil, bir **ilandır**"* diyor, ve **D-052 zaten aynı usulle** çalıştı
(`N = 40` **bütçeden**, MDE **raporlandı**). ⇒ Bu bir hipotez testi ayarı
değil, **kaynak planlaması**. Ama şart yine de kaçtı ve **kayda geçiyor**.

### 2. Alet — D-052'nin makinesi, yeniden yazılmadı (§2.8)

Eşleştirilmiş **Wilcoxon**, α = 0.05 çift yönlü, güç 0.80; non-central `t`
üzerinden, `ARE = 3/π` düzeltmesiyle (D-052 §"MDE'ler yeniden hesaplandı").

**Doğrulama — D-052'nin yayımladığı sayılara karşı:**

| N | t-testi (D-052) | bu alet | Wilcoxon (D-052) | bu alet |
|---|---|---|---|---|
| 32 | 0.511 | **0.511** | 0.524 | **0.523** |
| 40 | 0.454 | **0.454** | 0.465 | **0.465** |

⚠️ **İlk denemem yanlış tablo üretti ve atıldı.** `scipy.stats.nct` büyük
`ncp`'de `NaN` veriyor; onu `0.0` saymıştım ⇒ güç fonksiyonu sahte biçimde
düşüyor ⇒ çözücü **sahte kök** buluyordu (MDE'ler monoton değildi: 17.9,
19.2, 16.4, 7.8, 0.68…). ⇒ `NaN` → `1.0` ve ızgara üzerinde ikili arama.
**Monotonluk artık açıkça kontrol ediliyor.**

### 3. Girdiler — D-173'te ölçüldü

```
q = ΔCov'ün tanımlı olduğu tohum oranı = 3/3 = 1.00
t = tohum başına süre                  = 2 sa 20 dk   (G = 4, iki kol)
N_eff = floor(q × T_max / t)
```

### 4. Bütçe → duyarlılık tablosu

| `T_max` | ≈ gün | `N_eff` | **MDE (`d_z`)** | not |
|---|---|---|---|---|
| 14 sa | 0.6 | 6 | 1.468 | B2'nin çıpası 13.3 sa idi |
| 23 sa | 1.0 | 9 | 1.092 | |
| 35 sa | 1.5 | 15 | 0.796 | |
| **47 sa** | **2.0** | **20** | **0.676** | ⭐ MDE ilk kez 0.7'nin altında |
| 70 sa | 2.9 | 30 | 0.542 | |
| 93 sa | 3.9 | 39 | 0.471 | ≈ D-052'nin `N = 40` duyarlılığı |

⚠️ **Azalan getiri ölçüldü:** 47 → 70 sa (**+23 sa**) MDE'yi **0.124**
iyileştiriyor; 70 → 93 sa (**+23 sa**) yalnız **0.071**.

⛔ **Claude Code bir değer seçmiyor.** Bu bir GPU/zaman taahhüdü ve D-007
onu Yasin'e bırakıyor.

### 5. ⭐ `G` sorusu **kapandı: G = 4 baskın**

`G`, hem `q`'yu hem `t`'yi belirlediği için tek başına seçilemez. İkisi de
**bu koşumdan** okundu:

| | `q` | `t` |
|---|---|---|
| **G = 4** | **1.00** (3/3) | 2 sa 20 dk |
| G = 3 *(yalnız gen2→gen3 okunur, D-156/B)* | **0.67** (s9927 iki kolda da `max_z_variance = 0`) | 1 sa 45 dk |

| `T_max` | G = 4 | G = 3 |
|---|---|---|
| 35 sa | N=15 · **0.796** | N=13 · 0.866 |
| 47 sa | N=20 · **0.676** | N=17 · 0.741 |
| 70 sa | N=30 · **0.542** | N=26 · 0.585 |
| 93 sa | N=39 · **0.471** | N=35 · 0.499 |

⇒ **G = 4 her bütçede daha duyarlı.** G = 3'ün tohum başına ucuzluğu,
`q`'daki kaybı **kapatmıyor**. ⇒ **D-161'in `G = 4` kararı doğrulandı**,
ve bu bir tercih değil **aritmetik**.

### 6. Ne kaldı

⛔ **Tek eksik `T_max`** — ve o Yasin'in (D-007). Diğer iki sayı zaten
taslakta önerilmişti (kaldıraç hakkı **1**, `G` = **4**) ve §5 ikincisini
ölçümle doğruladı.

⇒ `T_max` söylendiği an `N_eff` ve MDE **aritmetikle** çıkıyor, kayıt
yazılıyor, kuyruk **3.1 doğrulayıcı koşum**a geçiyor.

---

## D-175 · 2026-08-24 · 🧭 **STRATEJİK DENETİM — projenin ilan edilmiş varış noktası 5 gündür YOK, ve üç katlı hedef önerildi**

**Yetki:** Yasin, 2026-08-24: *"nereye gidiyoruz gözümüzü kapattık gidiyoruz
gibi geliyor"* ve *"sence nereye gitmeliyiz … çıtayı ne kadar yukarı
koyabileceğimizi hayal edelim"*.

⛔ **Bu kayıt karar VERMİYOR.** Üç ölçüm + bir teşhis + bir öneri taşıyor;
hedef kararı Yasin'in (D-007).

---

### 1. ⛔ TEŞHİS — yol haritası iptal edilmiş bir hedefi gösteriyor

`docs/ROADMAP.md`'nin başlığı bugün hâlâ *"Yön 3'e (ajan-ajan etkileşimi)
hızlandırılmış geçiş"* ve bütün faz yapısı oraya gitmek için kurulmuş. İçinde
şu bağlayıcı cümle var: *"Yön 3'e gideceksek, bugünkü fizikle 30–80 saatlik
doğrulayıcı koşum **boşa gider**."*

⛔ **Yön 3, D-135'te iptal edildi.**

⇒ **2026-08-19'dan beri projenin yazılı bir varış noktası yok.** O tarihten
sonra ~40 karar kaydı yazıldı, fizik **üç kez** değişti, ama *"bunların
sonunda hangi cümleyi kuracağız"* sorusu hiçbir belgede güncellenmedi.
⇒ Yasin'in *"gözümüzü kapattık gidiyoruz"* hissinin **belgesel karşılığı budur**.

### 2. Merdiven — projenin kendi tanımı (uydurulmadı)

`analyze_population_run.py`'nin başlığı dört seviye tanımlıyor:

| seviye | ne gösterir | iddia | durum |
|---|---|---|---|
| **0** | `Var(w) > 0` | ⛔ **hiçbir şey**, ön-koşul | ✅ 18/18 (D-173) |
| **1** | `Cov(w, z) ≠ 0` | *"seçilim landmark drift'ine etki etti"* | ← 3.1'in sınayacağı |
| **2** | terim sönmüyor | *"etki birikimli"* | `G−2` geçiş; `G=4` yalnız **2** |
| **3** | `lived ≠ shuffle ≠ null` | ⭐ **Lamarckçı kanal = AKSİYOM** | ⛔ B2 sınadı, **üç kol eşit uzaklıkta** |

⭐ Aletin kendi uyarısı: *"Price **SEÇİLİMİ** verir, kol karşılaştırması
**KALITIMI**. Seviye 1 dolu, seviye 3 boş olabilir."*
⇒ **Doğrulayıcı koşum bitiş çizgisi değil.**

### 3. ⛔ Ve seviye 3 bugün **sınanamaz** — aksiyomun yarısı fişi çekik

D-172 §4: popülasyon yolunda **`run_consolidation` hiç çağrılmıyor**.
Aksiyom (§3) *"iki kanal, biri diğerinin yerine geçmez"* diyor.
⇒ Bugün `lived`/`shuffle` karşıtlığı **yalnız Kanal 2'nin (LoRA) testi**.
⇒ **Seviye 3'e giden yol kapalı** ve bu hiçbir plana yazılmamıştı.

### 4. ÖLÇÜM A — artabilen bir uç nokta **var** (⚠️ ama seçilimle çakışık)

Kümülatif iddianın **artabilen** bir niceliğe ihtiyacı var. Ölçüldü
(`layer1b_pilot_g4_s9926_9928.json`, **kollar birlikte havuzlandı — L9,
kol farkı okunmadı**), 48 ajan/nesil:

| | gen1 | gen2 | gen3 | gen4 |
|---|---|---|---|---|
| ömür (olay) | 22.29 | 25.50 | 26.08 | **26.94** |
| enerji (ömür boyu ort.) | 0.4970 | 0.5693 | 0.6469 | **0.6664** |
| `F_agent` | 0.5643 | 0.6318 | 0.6676 | **0.6871** |

⛔ **BU KÜMÜLATİF BİLGİ BİRİKİMİ DEĞİL.** Varisler turnuva kazananlarından
geliyor ve turnuva **`F_agent` üzerinden** seçiyor ⇒ `F_agent`'ın artması
**tanım gereği**. Ömür ve enerji onun girdileri (ağırlık 0.3 / 0.4) ⇒ aynı
sebeple yükseliyorlar. **Döngüsel, ve öyle raporlanmalı.**

⭐ **Değerli olan:** artabilen, nesiller boyu **tanımlı** bir nicelik var.
Eksik olan nicelik değil, **karşılaştırma modeli** — *"seçilim tek başına ne
kadar artış öngörür, gerçekleşen ondan fazla mı"*. ⇒ Kat 3'ün kancası budur
ve **koşumdan önce ilan edilmesi gerekir**.

### 5. ÖLÇÜM B — makine termal olarak zorlanmadı

Yasin *"97 CPU, 87 GPU gördüm, çok yük gibi"* dedi. Sürücünün ihlal sayaçları
(8 sa 33 dk uptime, içinde **7 saatlik tam yük koşumu**):

| sayaç | değer |
|---|---|
| **HW Thermal Slowdown** | **0 µs** |
| **SW Thermal Slowdown** | **0 µs** |
| SW Power Capping | 38 ms (≈ %0.0002) |

⇒ **GPU hiç termal kısma yapmadı.** 87 °C tasarım çalışma noktası, sınır değil.
⚠️ **Ama endişe yersiz değil:** 7 saat ile 47 saat **kesintisiz** aynı şey
değil (aşınma ve oda ısısı açısından).

⭐ **Ve saati düşürmek bilim kaybettirir**, çünkü bütçe **saat** cinsinden:
`N_eff = T_max / t`. %20 yavaşlama ⇒ 20 → **16 tohum**, MDE 0.676 → **0.767**.

⇒ **Öneri: parçalı koşum (B2 deseni — N=40 iki batch'te koşuldu).**
**5 tohum/gece × 4 gece**: gecede 11.7 sa · N=20 **korunur** · MDE **0.676**
· kayıp **yok** · ve çökmeye dayanıklı (08-22'de bir koşum makine kapanınca
**hiçbir çıktı bırakmadan** ölmüştü).

### 6. ÖNERİ — üç kat, ve **Kat 2 hedeflensin**

| kat | iddia | `G` | N=20 için |
|---|---|---|---|
| **1** | *"seçilim ölçülebilir"* (seviye 1) | 4 | **47 sa** |
| **2** ⭐ | *"yaşanmış iz aktarılıyor, karıştırılmış aktarılmıyor"* — **AKSİYOM** (seviye 3) | 6 | **70 sa** |
| **3** | *"kümülatif birikim"* (başarım artıyor **ve** kontrolde artmıyor) | 8 | 93 sa ⚠️ |

⚠️ `G = 8` şu an `ROADMAP.md`'de *"ölçülmeden **hayır**"* — gerekçe adapter
sönümünün uzun soyda sinyali seyreltebilmesi (D-130 §12).

**Claude Code'un önerisi: Kat 2'yi hedefle, Kat 3'ün kancasını aynı koşuma
göm.** Üç gerekçe:

1. **Kat 3, Kat 2 olmadan çürütülemez** — iz aktarılmıyorsa *"birikiyor"*
   denemez. Sıra zorunlu.
2. **Kalan tek kaldıraç hakkı Kanal 1'in onarımına harcansın** (§3). Aksiyomun
   yarısı fişi çekikken 47 saat harcamak, sonunda aynı soruya çıkar.
3. **Kat 3'ün kancası ucuz:** artabilen uç nokta + **seçilim-tek-başına null
   modeli**, ikisi de koşumdan önce ilan edilir. Ek GPU ≈ 0; maliyet
   `G`'yi 4 → 6 yapmakta (47 → 70 sa).

### 7. DR brief'i — **tek ve dar** bir soru

⚠️ Sicil: DR #13 taşıyıcı iddiasında **cebirsel olarak tersti** ve üç kaynak
şartının **0/3**'ünü karşıladı; önceki turlarda **12 kimlik hatası**.
⇒ DR'ye *"hedefimiz ne olsun"* **sorulmaz**.

**Sorulacak tek soru:**

> *Kümülatif kültürel aktarımın (ratcheting) yayımlanmış ampirik standardı
> nedir? Bir gösterimin kabul görmesi için asgari tasarım ne olmalı — kaç
> nesil, hangi kontrol kolu, hangi null model? LLM ajanlarında bunu iddia eden
> çalışmalar bu standardı karşılıyor mu?*

⇒ Cevabı doğrudan `G`'yi, kontrol kolunu ve null modeli belirler.
⛔ **Kendi sayılarımız verilmez** (tasarımı bize geri okumasın) · şartlar
aynen bağlayıcı (DOI · birebir alıntı · kaynakça + boşluk ilanı).

### 8. ⛔ Yasin'in vermesi gereken kararlar

| # | karar | öneri |
|---|---|---|
| 1 | **Hedef katı** | **Kat 2** (+ Kat 3 kancası) |
| 2 | `T_max` · `G` | Kat 2 ⇒ **70 sa · G = 6** ⚠️ (47 sa · G = 4 onaylanmıştı, hedef değişirse bu da değişir) |
| 3 | Koşum şekli | **5 tohum × 4–6 gece**, saate dokunulmadan |
| 4 | Kalan kaldıraç hakkı (1) nereye | **Kanal 1'in onarımı** |
| 5 | DR brief'i gönderilsin mi | evet, §7'nin tek sorusuyla |

---

## D-176 · 2026-08-24 · ⭐⭐ **BEŞ KARAR İLAN EDİLDİ (Yasin) + KOŞUM-ÖNCESİ DENETİM — denetim iki kararı değiştirdi**

**Bağlam:** `ROADMAP.md` §8'in beş kararı Yasin'e soruldu. Üçü doğrudan
cevaplandı; **bütçe kararı için Yasin önce denetim istedi**:

> *"her uzun runda tekrar kontrol edilmesi istediğimde ya uğraşılması gereken
> sorunlarla ya da çok daha az run süresiyle istediklerimizi alabileceğimizi
> bulmuştum … 70 saat 100 saat kaybetmeyelim"*

⇒ Denetim yapıldı (**salt-okunur, sıfır GPU**), ve **haklı çıktı**: bulgu 1
tek başına yol haritasının bütçe tablosunu çürüttü.

---

### 1. ⛔ Denetimin altı bulgusu

#### Bulgu 1 — **Kat 2 = seviye 3 = ÜÇ kol; pilot İKİ kolla koştu**

`analyze_population_run.py:18` seviye 3'ü `lived != shuffle != null` diye
tanımlıyor. `level3_arm_contrast` (§627) kapanış uyarısı:
*"B2 0.3852 / 0.3812 / 0.3814 ölçtü ve bu desen bir NULL"*.
⇒ **İki kolla o deseni görmek yapısal olarak imkânsız** — tek mesafe çıkar,
kıyas ekseni olmaz.

D-173 pilotunun argv'si (koşum dosyasından okundu):
`--arms lived shuffle` ⇒ **null kolu koşulmadı.**
⛔ **`ROADMAP.md` §2'nin 47/70/93 saatlik tablosunun tamamı iki kol
üzerinden hesaplanmış** ⇒ Kat 2 için geçersiz.

#### Bulgu 2 — **devam (resume) yok**

`Checkpoint` (D-111) her nesilde **yazıyor**; dosyada `checkpoint` geçen
15 satırın **hepsi yazma tarafında**, okuyan/atlayan kod yok.
⇒ Kesilen bir parti **baştan** koşulur. ⚠️ Bir kez yaşandı
(`…ABORTED-1303.json`, makine kapandı).

#### Bulgu 3 — **analiz aracı tek dosya alıyor**

`analyze_population_run.py:776` → `--results` tek `Path`; birleştirici yok.
⇒ Parçalı koşum N dosya üretir ve **okuyacak alet olmaz**.

#### Bulgu 4 — **disk (ölçüldü, bloke etmiyor)**

D-173 pilotu (3 tohum · 2 kol · G=4): **208 dizin / 2.7 GB**
(tohum-nesil başına ~208 MB, dizin başına ~13 MB).
Boş alan **41 GB**; `dau_runs/adapters/` **18 GB / 1402 dizin**.

| şekil | adapter | 41 GB'a |
|---|---|---|
| 21 tohum · G=4 · 3 kol | ~17 GB | ✅ |
| 30 tohum · G=6 · 3 kol | ~37 GB | ⛔ |

⭐ **~9.3 GB temizlenebilir (tahmin, 712 dizin × ~13 MB):** Katman 1 öncesi
fizikten s9601 · s9911–9913 · s9915–9922. ⚠️ s9923–9928 **korunur** (D-168 ve
D-173'ün kanıtı).
✅ **Yasin: *"disk temizlemek sorun değil"*** ⇒ disk bağlayıcı kısıt değil.
⚠️ **Ve zaten değildi** — seçilen şekil temizliksiz de sığıyordu.

#### Bulgu 5 — **I4.2'nin sayısı geldi; kodun kendi planı "mod yükselir" diyordu**

`run_population_experiment.py:1988–1998` gerekçeyi koşumdan önce yazmıştı:
*"the first run MEASURES, and the mode escalates once there is a number."*
**Sayı:** D-173'te **6/6 hücrede** kollar gen3 ve gen4'e **farklı RNG
durumundan** girdi. Sebep kodda yazılı (`:1526`): bu koşucu döngü **başında
bir kez** kilitliyor, `run_cprime_multigen` **her nesilden önce** (dört çağrı).
⇒ G=6'da 6 değil **12** hücre.

⭐ **Ama maruziyet sanıldığından dar — ölçüldü:** çalışma yolunda
(`graph.py` · `society/` · `memory/`) global RNG'yi tüketen **tek çağrı yok**;
üretim `reproduction.py`'ye **açıkça verilen yerel** `random.Random(seed)`
ile. Ortam da global stream'den gelmiyor: `shared_pasture` havuzu
**kurucuların nişinden** okuyor (`:861`). ⇒ Kalan gerçek maruziyet **DPO
eğitimi** (torch RNG).
⇒ **Düzeltme tek satır** (`_lock_seeds` döngünün içine), **sıfır GPU**, ve
🔒 **kilitten ÖNCE** yapılmalı — sonra yapılırsa ön-kayıt geçersizleşir.

#### Bulgu 6 — **bütçe sansürü büyüyor; ⛔ ve kendi hipotezim çürüdü**

Yaşamlar `--events 30` tavanına dayanıyor. Tavandaki ajan sayısı (24 hücre):

| | gen1 | gen2 | gen3 | gen4 |
|---|---|---|---|---|
| tavandaki ajan | **2.0/8** | 4.2/8 | **5.2/8** | 5.2/8 |
| `f_agent` yayılımı | 0.1139 | 0.1211 | 0.1873 | **0.1899** |

⛔ **Hipotezim:** *"tavan yayılımı çökertir ⇒ turnuva yazı-turaya döner"*.
❌ **Ölçüm tersini söyledi:** korelasyon(tavandaki ajan, `f_agent` yayılımı)
= **+0.283** (n=24), yayılım nesilden nesile **büyüyor**, `w_variance`
**0.75–1.75** (hepsi > 0), `selection_measurable` **True**.
⇒ Koşumu kırmıyor. ⚠️ Kalan gerçek: geç nesillerde yaşamların çoğu **ölümle
değil bütçeyle** bitiyor ⇒ **ön-kayıta sınır olarak yazılacak**, sabit
**değiştirilmeyecek** (§2.7 — sayıyı sonuca bakarak oynatmak).

---

### 2. Süre kaldıraçları — üçü ölü, biri gerçek

| kaldıraç | sonuç |
|---|---|
| **Paralel koşum** (2 süreç) | ❌ **imkânsız** — GPU `RTX 4070 Laptop`, **8188 MiB**. NF4 8B tek örnek zaten sığıyor |
| **Kuantizasyon / model** | ❌ NF4 en ucuzu; fp16 sığmaz; model değişimi alet kimliğini bozar (D-026) |
| **Üretim ayarı** | ❌ `max_new_tokens=64` + greedy, zaten en dar. Düşürmek kararı keser ⇒ fizik değişikliği |
| ⭐ **`G`** | **gerçek** — ve G=6'yı **Kat 2 istemiyor, Kat 3'ün kancası istiyor** (`ROADMAP.md` §2/c'nin kendi cümlesi). Seviye 3 bir **kol karşıtlığı**, nesil başına okunuyor |
| ⭐ **parçalı koşumun sabit maliyeti** | her çağrı I4.1 replay kolunu yeniden ödüyor (~2 nesil ≈ **35 dk**) ⇒ gece başına tohum sayısı büyük tutulur |

---

### 3. Bütçe aritmetiği — **ölçülmüş tabandan**

**Taban (ölçüldü, D-173):** 2 kol · G=4 = **2 sa 20 dk**/tohum.
**Üçüncü kol (`null`) eğitim yapmıyor** ⇒ maliyeti çıkarım payına eşit.
⚠️ **Tahmin ve sınırı (K4):** eğitim payı ölçülmedi; alt sınır +%35
(eğitim ≈ %30), üst sınır **+%50** (eğitim ≈ 0).

| 3 kol · G=4 varsayımı | `t`/tohum | `N_eff` = ⌊70/t⌋ | MDE `d_z` |
|---|---|---|---|
| +%35 | 3 sa 09 dk | 22 | 0.641 |
| +%43 | 3 sa 20 dk | 21 | 0.658 |
| ⭐ **+%50 (muhafazakâr)** | **3 sa 30 dk** | **20** | **0.676** |

⇒ **İlan edilen değer muhafazakâr olan:** `N_eff` = **20**, MDE = **0.676**.
Durma kuralının aritmetiği (`N_eff = ⌊q × T_max / t⌋`) `t` ölçülünce yeniden
uygulanır; bu **post-hoc değil**, kuralın kendi tanımı (D-174).

⭐ **MDE aleti bu turda yeniden doğrulandı:** noncentral-t + Wilcoxon ARE
(0.955) ile hesaplanan eğri D-174'ün üç sayısını **birebir** üretti
(20 → 0.676 · 30 → 0.542 · 39 → 0.471).

**Elenen şekiller:**

| şekil | neden alınmadı |
|---|---|
| 70 sa · G=6 · 3 kol → 13 tohum, MDE **0.866** | aynı parayla duyarlılık **düşüyor**; satın aldığı şey Kat 2 değil Kat 3'ün kancası |
| 103 sa · G=6 · 3 kol → 20 tohum, MDE 0.68 | +33 saatin aldığı Kat 3 kancasının **karşılaştırma modeli henüz yazılmadı** (`ROADMAP.md` §4: *"seçilim-tek-başına null modeli"*) ⇒ bugün ödenirse boşa gider. ⚠️ Disk **engeli değil** (Yasin temizliği onayladı) |
| 70 sa · G=4 · 2 kol → 30 tohum, MDE 0.542 | en duyarlı okuma, **ama `null` yok ⇒ seviye 3 raporlanamaz** ⇒ Kat 2 iddiası kurulamaz |

---

### 4. ⭐⭐ İLAN — beş karar (Yasin, D-007)

| # | karar | **ilan edilen** |
|---|---|---|
| **1** | Hedef katı | ⭐ **Kat 2 — aksiyom, seviye 3** (`lived ≠ shuffle ≠ null`) |
| **2** | `T_max` · `G` · kol | **`T_max` = 70 sa** · **`G` = 4** · **3 kol** (`lived shuffle null`) ⇒ `N_eff` = **20** (muhafazakâr), MDE = **0.676** |
| **3** | Koşum şekli | **parçalı**, saate dokunulmadan; gece başına tohum **mümkün olduğunca çok** (replay sabit maliyeti). Taze blok **9929+** (denetlendi: 9929–9969 arasında **0 adapter**, I0.7 temiz) |
| **4** | Kaldıraç hakkı | **2**, ve ⭐ **tanım değişti:** yalnız **tabanı geçersiz kılan** (fizik/sabit) değişiklikler sayılır. **Alet onarımı bedava** — bilimi değiştirmiyor, aleti çalıştırıyor |
| **5** | DR brief #14 | ✅ **evet**, D-175 §7'nin tek sorusuyla (ratcheting'in yayımlanmış ampirik standardı) |

⚠️ **Karar 4'ün gerekçesi Yasin'in itirazıyla değişti** — *"neden kendimizi
araştırmayı tamamlayabilecekken kısıtlayalım"*. Haklı olduğu yer: eski taslak
**iki farklı şeyi tek sayıda topluyordu**. Bulgu 2/3/5'in onarımları
(resume · birleştirici · I4.2 kilidi) hiçbir sayıyı sıfırlamıyor ⇒ hak
harcamaları için sebep yok. **Sınırın kalma gerekçesi tek cümlede:** karmaşık
bir sistemde *"kırık bir şey"* her zaman bulunur, dolayısıyla *"bir kaldıraç
daha"*nın kendi içinde durma noktası yoktur — sayı araştırmayı kısıtlamak
için değil, **döngünün çıkışı olsun** diye var (C2'den bu yana **50 karar
kaydı**, hepsi ön-koşul, hiçbiri hipotez).

---

### 5. ⚠️ Bu kaydın sınırları

- **Üçüncü kolun süresi ÖLÇÜLMEDİ** — +%35…+%50 bandı bir tahmindir, dayanağı
  *"`null` eğitim yapmıyor, çıkarım payı kadar sürer"*. İlk gecede `t` okunur.
- **G=6'nın süresi de tahmindir** (×1.55), dayanağı nesil başına olay sayısı
  (kol başına 178.3 · 204.0 · 208.7 · 215.5) ve gen5/gen6 için düzleşme
  varsayımı. ⭐ Vekil doğrulandı: gen1 payı %22.1 × 70 dk = **15.5 dk**,
  D-174'ün ölçtüğü tek sayı **14 dk**.
- **Bulgu 5'in "maruziyet dar" sonucu bir grep taramasıdır**, koşum
  ölçümü değil. Düzeltme yine de yapılır (bedeli sıfır).
- **Hiçbir sabit değişmedi, hiçbir kod değişmedi** bu kayıtta.

### 6. Sıradaki iş — ⛔ kilitten önce, hepsi GPU'suz

| # | iş | bitti sayılır |
|---|---|---|
| **B1** | **I4.2 kilidi** — `_lock_seeds` nesil döngüsünün içine | kod + test + **mutasyon kontrolü** (K5: md5 + `__pycache__` silinmiş) |
| **B2** | **Resume** — checkpoint okunup tamamlanmış kollar atlanır | kesilip devam ettirilen koşum, digest'ler birebir |
| **B3** | **Birleştirici** — `analyze_population_run.py` çok dosya alsın | K2: testte **en az iki tohum**, iki dosya |
| **B4** | **Kanal 1 kararı** (kuyruk 3.0f) — kaldıraç hakkı 2, biri buraya aday | D-kaydında seçilen şık + reddedilenler |
| **B5** | Adapter temizliği (~9.3 GB) · DR #14 brief'i | — |
| **C** | Ön-kayıt taslağının dört kusuru (D-145) | — |
| **D** | 🔒 **KİLİT** — `PREREGISTRATION_3.md` | commit hash + §12 deseni |

⛔ **B1–B3 kilitten önce yapılmak zorunda** — üçü de koşum yolunu değiştiriyor.

---

## D-177 · 2026-08-24 · ✅ **ÜÇ ALET ONARIMI (B1·B2·B3) — kilitten önce, sıfır GPU** · ⛔ ve mutasyon koşumu bir kusur daha buldu

**Bağlam:** D-176'nın koşum-öncesi denetimi üç alet kusuru ölçmüştü. Yasin:
*"hepsini ard arda yap"* ⇒ üçü tek turda kapandı. **Hiçbiri fizik
değişikliği değil**, ama **üçü de koşum yolunu değiştiriyor** ⇒ 🔒
`PREREGISTRATION_3` kilidinden **önce** yapılmak zorundaydı (§2.10).

**Suite: 645 → 660.** Commit'ler `250f7e5` · `07d0cae` · `00f1252`.

---

### B1 — I4.2: RNG her nesilden önce yeniden kilitleniyor (`250f7e5`)

D-149 kapıyı **kilitsiz** göndermiş ve gerekçesini yazmıştı: eğitimin global
stream'i tüketip tüketmediği stub koşumdan çözülemez (K1(b) tuzağı), *"ilk
koşum ÖLÇER ve sayı gelince mod yükselir"*. **Sayı D-173'te geldi: 6/6
hücrede ayrışma.**

⇒ `_run_arm_generations` artık her nesilden önce `_lock_seeds(seed)` çağırıyor
— `run_cprime_multigen`'in **dört çağrı yeriyle aynı şekil, aynı tohum**.

⛔ **Mod FLAG'de bırakıldı — ve karar burada ilan ediliyor, Yasin
değiştirebilir.** Gerekçe **değişti**, o yüzden yeniden yazıldı: artık
*"önerme ölçülmedi"* değil, **maliyet şekli**. Kapı faz-2'de, bütün
yaşamlardan **sonra** koşuyor ve `main()` `PreflightAbort`'ta **sonuç dosyası
yazmıyor** (okundu, `run_population_experiment.py` `main()`) ⇒ ABORT, son
hücrede ayrışan **70 saatlik bir koşumu okunacak hiçbir şey bırakmadan**
öldürürdü. Yakaladığı şey **kirli ölçüm değil, alet regresyonu**.

⭐ **Ve maruziyet ölçüldü, sanıldığından dar:** çalışma yolunda (`graph.py` ·
`society/` · `memory/`) global RNG'yi tüketen **tek çağrı yok**; üretim
`reproduction.py`'ye **açıkça verilen yerel** `random.Random(seed)` ile,
mera `shared_pasture` üzerinden **kurucuların nişinden**. Kalan gerçek
maruziyet **DPO** (torch RNG). ⚠️ **Bu bir grep taramasıdır**, koşum ölçümü
değil — düzeltme yine de yapıldı, bedeli sıfır.

**Testin kendi tuzağı:** stub global stream'i **kol başına farklı miktarda**
tüketiyor, yoksa sessiz bir stub kolları **kazara** uyumlu bırakır ve test
**hiç kilitlemeyen** bir koşucuya karşı da geçerdi (K1(b)'nin test hâli).
Fixture kendini önce kanıtlıyor. ⭐ **Test bir kusur yakaladı:** replay kolu
`pop-replay-*` id'siyle geliyor ve sessiz bir varsayılan onun çekilişlerini
yanlış kovaya koyardı.

**K5:** 1 mutasyon, yakalandı. md5 `251645fb…` birebir.

---

### B2 — checkpoint artık okunabiliyor: `--resume` (`07d0cae`)

D-111 checkpoint'i verdi ve o günden beri **yazma-yalnız**: `checkpoint`
geçen 15 satırın hepsi yazma tarafındaydı. Planlanan 70 saatte bu **bir
geceyi kaybetmekle bütçeyi kaybetmek** arasındaki fark.

| karar | gerekçe |
|---|---|
| **opt-in** (`--resume`), asla otomatik | bayat `.partial` dosyası `Checkpoint`'in kendi docstring'inin uyardığı tuzak; `--results`'taki bir yazım hatası **başkasının kollarını** sessizce miras alırdı |
| uyuşmayan checkpoint **reddediliyor**, yok sayılmıyor | §2.9 — sıfırdan başlamak *"resume"*'u bazen hiçbir şey ifade etmeyen bir söze çevirirdi |
| bitmiş kol **yapısal** olarak tanınıyor (nesil sayısı + RNG defteri), konumla değil | ileride başka yere ekleyen bir yazar **yarı-yaşanmış** bir kolu sonuç hâline getiremesin |
| **I0.7 muafiyeti** (`planned_founder_ids.skip_cells`) | bitmiş kolun adapterları diskte **olmak zorunda**, kapı onları kirlilik diye okur |
| ⛔ **replay kolu asla muaf değil** | replay **sırasında** kesilen koşum ikinci geçişi **adapterli** başlatır ⇒ yüksek sesle abort etmeli, koşucu kendi kendine **silmemeli** |

⚠️ `build_tool_identity` faz-0'ın **üstüne taşındı**: I0.7'nin muafiyet listesi
checkpoint'ten çıkıyor, checkpoint ise karşılaştırılacak bir header olmadan
okunamaz. Faz 0 bu okumanın gördüğü hiçbir şeyi **yaratmıyor** (env,
determinizm, adapter dizini) ⇒ sayım iki tarafta da aynı. `_lock_seeds`'in
**altında** kalıyor, o load-bearing.

⭐ **Testin kendi zayıflığı kapatıldı:** eşitlik **tek başına yetmiyordu** —
her şeyi yeniden koşan bir resume de **aynı dosyayı** üretir ve geçerdi. ⇒
kazanılan GPU zamanı da ölçülüyor (**2 çağrı, 6 değil**). Ve eşitlik **dosya**
üzerinden iddia ediliyor: resume edilen kol `json.loads`'tan geliyor,
tuple'ları list; **ölçüldü**, iki taraf aynı byte'lara dönüyor.

**Kasıtlı test kırılması aynı commit'te:** `i04` testinin
`planned_founder_ids` sahtesi imza büyüyünce eskidi.

**K5:** **4 mutasyon, dördü de yakalandı.** md5 `aeebfed0…` birebir.

---

### B3 — analiz aracı N dosya okuyor (`00f1252`)

`--results` **tek** `Path` alıyordu; parçalı koşum biter, **okuyacak alet
olmazdı**.

`merge_runs` **üç şeyi reddediyor:** checkpoint (D-111'in arka kapısı olmasın)
· alet/tasarım uyuşmazlığı (**iki geceyi değil iki DENEYİ** ortalamak olurdu)
· ⛔ **çakışan tohum** — tekrarlama birimi **tohum** (Lazic 2010, D-140) ⇒
aynı tohumu iki kez saymak **pseudoreplication**, ve bu tam da parçalı
koşumun **davet ettiği** hata (ters görünen bir geceyi yeniden koşmak doğal
gelir).

⚠️ **Kapı verdictleri tek bir sağlıklı damgaya düzleştirilmiyor.** Birleşik
koşum ancak **her gece** clean ise clean; kalite `mixed:…` diye yazılıyor —
hiçbir koşumun içinde olmadığı bir kategori **uydurulmuyor**; dosya başına
defter sonuca giriyor. Tek gecenin replay'i **çalışmaya kalmıyor**.

### ⛔⛔ Mutasyon koşumu gerçek bir kusur buldu — K5'in asıl işi

İlk sürüm `all(v is True)`'ya düşüyordu ⇒ bir gece **GEÇEN**, öteki gece
**HİÇ DEĞERLENDİRİLMEYEN** bir değişmez **FAILED** çıkıyordu — **D-121'in
ayırdığı iki şey tam tersine çevrilmiş.** ⇒ Üç sonuçlu hâle getirildi
(`False` / `True` / `None`) ve **karışık durum `None`**: çalışma tam
denetlenmedi, *"geçti"* demek sahip olunmayan bir kapsamı iddia etmek olurdu.
Bulgunun **kendi testi** yazıldı.

⭐ **Bu, mutasyon kontrolünün testi değil KODU düzelttiği ilk kayıt.** K5'e
kadarki bütün örnekler *"test boştu"* idi.

**K5:** **7 mutasyon, yedisi de yakalandı.** md5 `4e74f63a…` birebir.

---

### ⚠️ Bu kaydın sınırları

- **Hiçbiri GPU'da koşulmadı.** Üçü de stub/mock altında sınandı; B1'in gerçek
  maruziyet iddiası (*"yalnız DPO"*) bir **grep taramasıdır**.
- **B2'nin eşdeğerlik iddiası stub altında ölçüldü** — eğitim açıkken
  (`--lora`) resume'un aynı dosyayı üretip üretmediği **denenmedi**.
  ⚠️ Doğrulayıcı koşumun **ilk gecesinde** bir kez fiilen sınanmalı.
- **Hiçbir sabit değişmedi**, hiçbir fizik değişmedi ⇒ **kaldıraç hakkı
  harcanmadı** (D-176/karar 4'ün tanımı gereği).
- ⚠️ **Digest'ler değişti** (B1, RNG stream'i oynattı) ⇒ D-173 öncesi
  `arm_digest`'lerle bugünküler **karşılaştırılamaz**. Sayılar sıfırlanmadı,
  **kimlikler** değişti.

### Sıradaki

| # | iş |
|---|---|
| **B4** | ⛔ **KARAR — Kanal 1** (kuyruk 3.0f), kaldıraç hakkı **2**, biri buraya aday |
| **B5** | adapter temizliği (~9.3 GB) · **DR #14 brief'i** |
| **C** | ön-kayıt taslağının dört kusuru (D-145) + **yeni sınır: bütçe sansürü** |
| **D** | 🔒 **KİLİT** |

---

## D-178 · 2026-08-24 · ✅ **B4 — KANAL 1: BAĞLANMIYOR, SINIR İLAN EDİLİYOR** (devredilmiş yetki) · ⛔ ve `ROADMAP.md` §3'ün çıkarımı düştü · ⏸ **DR #14 ertelendi**

**Bağlam:** Yasin *"önerdiğin şekilde yapalım"* dedi ⇒ B4 devredilmiş yetkiyle
karara bağlandı (D-143 deseni). Ve *"brief gerekiyor mu"* diye sordu ⇒ D-176'nın
**beşinci kararı yeniden değerlendirildi**.

---

### 1. ⛔ Kararı tersine çeviren ölçüm — Kanal 1 ölü değil

Kuyruk 3.0f ve `ROADMAP.md` §3, D-172'nin bulgusundan *"aksiyomun kendisi
bugünkü kablolamayla sınanamaz"* sonucunu çıkarmıştı. **Karar vermeden önce
kod okundu** (§2.2) ve sonuç bu çıkarımı çürüttü:

| ölçüm | sonuç |
|---|---|
| `consolidate_generation` popülasyon yolunda çağrılıyor mu | ✅ **evet** — `run_population_experiment.py:1692` → `consolidate_parents:1422` |
| **I5.4** (sembolik kayıt varise ulaşıyor mu), D-173 pilotu | ✅ **True** — *"applied 463x"* |
| **I5.1** (ilişki grafiği) | ❌ boş — `run_consolidation`'ın çağrısı yok (D-172) |

⇒ **Ölü olan Kanal 1 değil, UYKU KONSOLİDASYONU:** ilişki grafiği, Ebbinghaus
budaması, güçlendirme. Bu bir **yaşam içi bellek dinamiği**, bir kalıtım
kanalı değil. Kalıtım (D-161'in somatik kanalı, 34/144; D-173'ün 463 uygulama)
**çalışıyor**.

### 2. ⭐ Ve asıl düzeltme: bağlamak zaten işe yaramazdı

`lived ↔ shuffle` karşıtlığının **Kanal 2'yi izole etmesinin sebebi
konsolidasyonun bağlı olmaması değil** — **müdahalenin kendisi** Kanal 2'ye
yapılıyor (DPO tercih çiftleri karıştırılıyor). ⇒ `run_consolidation`'ı
bağlamak `lived ≠ shuffle`'ı bir **Kanal 1 testi yapmaz**.

Kanal 1'i sınamak **üçüncü bir müdahale** ister (örn. kasası karıştırılmış bir
kol) ⇒ bir kablolama düzeltmesi değil, bir **tasarım değişikliği**, ve bu
koşumun kapsamı dışında.

### 3. Karar — **seçenek B** (kuyruk 3.0f)

| şık | değerlendirme |
|---|---|
| **A** — bağla | ⛔ **reddedildi.** Fizik **dördüncü kez** değişir, D-173'ün tabanı (`q`=1.00, `t`=2 sa 20 dk) geçersizleşir, GAP-4 riski canlanır — ve §2'ye göre **karşılaştırmayı oynatmaz** |
| ⭐ **B** — bağlama, sınır ilan et | ✅ **seçildi.** Eksik dinamik **her kolda simetrik** yok ⇒ seviye 3 karşıtlığını yapı gereği etkileyemez |
| **C** — yalnız telemetri | ⛔ kuyruğun kendi değerlendirmesi: *"yetersiz — sıfırın sebebini yazmak sıfırı açıklamıyor"* |

⭐ **Kaldıraç hakkı harcanmadı: 2/2 duruyor.**

**Uygulama:** `SLEEP_CONSOLIDATION_WIRED: bool = False` +
`SLEEP_CONSOLIDATION_BOUNDARY`. `I5.1` artık **`None`** (*"değerlendirilmedi"*)
diyor ve sebebini adlandırıyor. ⭐ **`False` demek yanlış olurdu** — kablolama
hakkında bir cümleyi sistem hakkındaymış gibi sunardı; D-121'in ayrımı, ve
B3'ün mutasyon koşumunda yeni kazanılmış.

⛔ **Bu bir susturma DEĞİL, bir KOŞUL** — ve ikisi ayrı testle bağlandı:

| test | neyi imkânsız kılıyor |
|---|---|
| `test_wiring_consolidation_brings_the_gate_back` | sabit `True` olduğu an **gerçek yüklem geri geliyor** ⇒ sınır kendi sebebi bitince ayakta kalamaz |
| `test_the_declared_boundary_matches_the_code` | **K6.** Modülün kaynağı taranıyor (yerel import da yakalansın diye **metin** olarak): biri konsolidasyonu bağlayıp sabiti unutursa test kırılıyor |

⚠️ **K6'nın bedeli neden ödendi:** D-151 ölçtü — D-086 bir kusuru **düzyazıyla**
yazdı, sekiz oturum geçti, koşum üstüne `clean` raporladı.

**Kasıtlı test kırılması aynı commit'te:** `test_i51_and_arm_edge_count_…`
`check_ppr_active`'in çıktısını bekliyordu; artık o yüklem koşmuyor.
**K5:** 2 mutasyon, ikisi de yakalandı. md5 `5c8f1c42…` birebir.

---

### 4. ⛔ `ROADMAP.md` §3'ün çıkarımı düştü — belge düzeltildi

§3 *"Seviye 3 — yani aksiyomun kendisi — bugünkü kablolamayla sınanamaz"*
diyordu. **Olgu doğru, çıkarım yanlıştı** (§1–§2). Belge düzeltildi, ilk sürüm
`<details>` içinde bırakıldı. ⚠️ **Bu, bir günde ikinci kez** bir yol haritası
maddesinin ölçümle çürütülmesi (birincisi D-176/Bulgu 1, *"iki kol"*).

⇒ **Ders, ve D-175'in kendi dersinin tekrarı:** bir belge güncel olduğu için
doğru olmuyor. §2.2 *"belgeye değil dosyaya güven"* diyor, ve bu turda **karar
verilmeden önce** uygulandığı için karar tersine döndü.

---

### 5. ⏸ DR #14 ertelendi — **D-176'nın 5. kararının değiştirilmesi**

⚠️ **Bu bir karar değişikliğidir ve öyle ilan ediliyor**, sessizce düşürülmüyor.

D-176 *"evet"* demişti. Sorusu: **ratcheting'in (kümülatif kültürel aktarım)
yayımlanmış ampirik standardı**. Ama **aynı denetim** hedefi `G=6`'dan
`G=4`'e çekerken **Kat 3'ü bu koşumun kapsamından çıkardı** (D-176/karar 2)
⇒ brief, **sormadığımız** bir sorunun cevabını getirir.

| | |
|---|---|
| bloke ediyor mu | ❌ hayır — Kat 2'nin hiçbir adımı ona bağlı değil |
| maliyeti | bir **mutabakat turu** (§9/D-006 zorunlu) |
| sicil | 13 turda **12 kimlik hatası**; DR #13 taşıyıcı iddiasında **cebirsel olarak tersti** ve üç kaynak şartının **0/3**'ünü karşıladı |

⇒ **Kat 3 masaya geldiğinde gönderilir.** Brief'in kendisi hazır (D-175 §7),
silinmiyor.

---

### 6. B5 — adapter temizliği: ⛔ **YAPILMADI, ve bu bir öneri değişikliği**

D-176 *"~9.3 GB temizlenebilir"* demişti ve Yasin izin verdi (*"disk temizlemek
sorun değil"*). **İzin, gereklilik değil** — ve ölçünce gerekmediği çıktı:

| | |
|---|---|
| boş alan | **41 GB** |
| seçilen şeklin ihtiyacı (20 tohum · G=4 · 3 kol; yalnız `lived`+`shuffle` adapter yazıyor) | **~17 GB** |
| **pay** | **~24 GB** |

⛔ **Ve silinecek olanların hepsi bir D-kaydını destekliyor:** s9911–9913 = C2
(**D-123, raporlanmış sonuç**) · s9920–9922 = Katman 1 pilotu (**D-164**) ·
s9917–9919 = tanımlılık pilotu · s9915/9916 = sonda-2/3. `CLAUDE.md` §EV
İŞLERİ zaten *"2001–2043 kanıttır, silinmemeli"* kuralını koymuş; aynı gerekçe
`pop-*` blokları için de geçerli.

⇒ **İhtiyaç duyulmayan alanı açmak için kanıt silmek kötü bir takas.**
⏸ Tetik: doğrulayıcı koşumdan **önce** boş alan **25 GB'ın altına düşerse**
yeniden değerlendirilir.

---

### 7. ⚠️ Bu kaydın sınırları

- §1'in *"Kanal 1 çalışıyor"* iddiası **iki kapıya** dayanıyor (I5.4 = 463
  uygulama, ve `consolidate_generation`'ın çağrı yeri). **Kasanın içeriğinin
  varise ne kadar bilgi taşıdığı ölçülmedi** — yalnız *aktığı* ölçüldü.
- §2'nin *"bağlamak Kanal 1 testi yapmaz"* çıkarımı **tasarım okumasıdır**,
  ölçüm değil. Çürütülmesi için `shuffle`'ın kasayı da karıştırdığının
  gösterilmesi gerekir; kod okundu, karıştırmıyor.
- Uyku konsolidasyonunun **yokluğunun** yaşam içi dinamiğe etkisi
  **ölçülmedi** — sınır bu yüzden *"etkisi yok"* değil, ***"her kolda
  simetrik"*** diye ilan edildi.

---

## D-179 · 2026-08-24 · ⛔⛔ **L9 İHLALİ — `ΔP_active` pilot verisinde okundu** · ✅ ve D-145'in dört kusurundan üçü kapandı

**Bağlam:** Adım C (ön-kayıt taslağının dört kusuru, D-145). Yasin *"runa
gelene kadar devam edebilirsin onayım gerekmezse"* dedi. Kusur 3'ü
değerlendirirken **onay gereken bir sınır aşıldı** ⇒ iş durduruldu.

---

### 1. ⛔⛔ İhlal — ne yapıldı, ne görüldü

`CLAUDE.md` §5 (*"Koşum yaparken — değişmeyen kurallar"*) şunu yazıyor:

> ⛔ **OKUNMAYACAKLAR (L9):** kovaryans **değeri** · **işareti** ·
> `lived`↔`shuffle` **farkı** · etki büyüklüğü · **`ΔP_active`**

Kusur 3'ün (*"`ΔP_active` üzerinde Wilcoxon yapısal olarak çalışmıyor"*)
bugünkü fizikte hâlâ geçerli olup olmadığını sınamak için, D-173 pilotundan
**kol başına `P_active` hesaplanıp farkı alındı**. Bu **tam olarak
`ΔP_active`**'tir.

**Görülen:** üç tohumun **üçünde de `ΔP_active` = 0**. Sebebi tavan etkisi:
`energy` alanı **her iki kolda da** aynı geçişlerde tanımlı çıkıyor.

⚠️ **Bu bilgi geri alınamaz.** Kaydın burada olmasının sebebi de bu: gizlemek,
kilitten sonra *"kör seçildi"* diyebilmek için ihlali yok saymak olurdu.

### 2. Neden oldu — ve neden kapılar yakalamadı

L9 bir **kapıya bağlı değil**; `CLAUDE.md`'de bir cümle olarak duruyor ve
uygulanması okuyanın disiplinine bırakılmış. ⇒ **K6'nın tarifi birebir:**
*"kayda geçen kusur bir KAPIYA bağlanmadıkça kapanmamıştır"* — burada
kapanmamış olan bir kusur değil, bir **yasak**.

⚠️ Ve ironi kayda geçsin: aynı oturumda K6'yı bir sınırı bağlamak için
kullandım (D-178, `test_the_declared_boundary_matches_the_code`), ama L9'un
kendisi bağlanmamıştı.

### 3. Zararın kapsamı — abartılmadan

| | |
|---|---|
| Birincil A'nın **tanımı** ne zaman kilitlendi | **D-143/D-144**, bugünden **önce** — yani seçim bu okumadan etkilenmedi |
| Bulaşma riski | **ileriye dönük**: bu sayıya bakarak Birincil A'yı değiştirmek **post-hoc** olurdu |
| Doğrulayıcı koşum | **taze tohumlarda** (9929+) ve **ilan edilmiş kuralla** hesaplanacak |

⇒ **Kapsama alma yolu tek:** **Birincil A değiştirilmiyor.** Değiştirilirse,
değişiklik *"pilot sonucuna bakılarak yapıldı"* diye ilan edilmek ve iddia
buna göre **zayıflatılmak** zorunda.

⛔ **Claude Code bu kararı vermez** (D-007). Karar Yasin'in.

### 4. ✅ Aynı turda meşru biçimde kapanan üç kusur

⚠️ **Bunlar L9'a girmiyor** — hepsi **tanımlılık** okumasıdır, kol farkı
değil. `CLAUDE.md`'nin kendi ifadesi: *"kol farkına değil, dağılımın var olup
olmadığına bakılıyor."*

**Ölçüm:** `dau_runs/layer1b_pilot_g4_s9926_9928.json`, 16 Price hücresi,
25 satır (anahtar: `selection_estimable`).

| kusur (D-145) | C2'de | **bugün** | durum |
|---|---|---|---|
| **1** — birincil alan `energy` neredeyse hiç yazılmıyor | 4/15 satır, **1** tanımlı | **16/16 satır, 10 tanımlı** | ✅ **kapandı, ve tersine döndü** |
| **2** — hangi alanın yazıldığı **tohuma** bağlı ⇒ tohum düşer | kriz→`resource`, yoksa→`energy` | **her hücrede `energy` satırı var**; s9926 `energy`+`resource`, s9927 yalnız `energy`, s9928 `energy`+`resource` | ✅ **kapandı — hiçbir tohum düşmüyor** |
| **4** — bütün bir kol-tohumun **hiç** Price satırı olmayabilir | `null` s9912: 0/2 | **s9927 gen2 iki kolda da yok** ⇒ 18 değil **16 hücre** | ⚠️ **gerçek, sınır olarak ilan edilecek** |

⭐ **Ve yeni bir yapısal olgu (L9 dışı, tanımlılık):** `resource` **9 satırın
9'unda `z_variance = 0.0`** ⇒ **hiç tanımlı değil**. L14'ün confound'u
(`CRISIS_AFFECTED_DOMAIN` sabit ⇒ kriz herkese aynı skarı verir) kendini
**sıfır varyans** olarak gösteriyor. ⇒ §3.1'in *"`resource` hücre içi bilgi
taşımaz"* gerekçesi **artık ölçülmüş**, türetilmiş değil.

⚠️ **§3.1'in bir cümlesi eskidi:** *"C2'de `energy` 216 okumanın 11'inde
doluydu ⇒ `P_active` düşük beklenmelidir."* Katman 1/1b'den sonra bu **yanlış
yönde**. Cümle düzeltilmeli — ⚠️ ama bu bir **beklenti**dir, uç nokta seçimi
değil.

### 5. Sıradaki — ⛔ Yasin'in kararı olmadan ilerlemiyor

| # | soru |
|---|---|
| **1** | Birincil A (`ΔP_active`) **olduğu gibi mi kalsın** (öneri: evet), yoksa betimleyiciye mi düşsün — ikincisi **post-hoc olarak ilan edilmek** zorunda |
| **2** | §4'ün testi ile D-145 §6'nın *"kestirim, hipotez testi değil"* sonucu **çelişiyor** (§4 hâlâ α + Holm diyor). Hangisi geçerli? ⚠️ §2.11: sessizce seçilmez |
| **3** | L9 bir **kapıya** bağlansın mı — yani analiz aracı bu nicelikleri pilot dosyalarında hesaplamayı **reddetsin** mi |

---

## D-180 · 2026-08-24 · ✅ **ADIM C KAPANDI — dört kusur, üç karar, ve kilitten önce yakalanan iki eskime** · ⭐ L9 artık bir KAPIYA bağlı

**Bağlam:** D-179 üç soruyu Yasin'e bıraktı. **Üçünde de öneri kabul edildi:**

| # | soru | karar |
|---|---|---|
| 1 | Birincil A (`ΔP_active`) | ⭐ **olduğu gibi kalıyor** — bulaşma ileriye taşınmıyor, iddia zayıflatılmıyor |
| 2 | §4 ↔ D-145 §6 çelişkisi | ⭐ **Wilcoxon + ilan edilmiş MDE**, ve `p` **her zaman CI + etki büyüklüğüyle birlikte** |
| 3 | L9 kapıya bağlansın mı | ⭐ **evet — analiz aracı kilit alınmadan reddediyor** |

---

### 1. ⭐ L9 KAPISI — izin belgeden okunuyor, bayraktan değil

`analyze_population_run.py`: kilit alınmadan **seviye 1, 2 ve 3** raporlanmıyor
(üçü de yasak niceliği basıyor: kovaryans değeri/işareti · terimin hareketi ·
`lived ↔ shuffle` mesafesi). **Seviye 0, sağlık ve travma başlığı açık
kalıyor** — onlar **tanımlılık**, ve `CLAUDE.md` onları aynı cümlede
serbest bırakıyor (*"kol farkına değil, dağılımın var olup olmadığına"*).

⭐ **İzin elle çevrilen bir bayrak değil:** `preregistration_locked()`
**`PREREGISTRATION_3.md`'nin kendi durum satırını** okuyor ve **🔒 + commit
hash**'in ikisini birden arıyor. ⇒ Belge ile kod **ayrışamaz**: yazılmamış bir
kilit raporu açmıyor, açılan bir rapor kilidin yazıldığının kanıtı.
⚠️ **Hash şartı gevşek değil:** işaret var hash yoksa **kilitli sayılmıyor** —
§12'nin bütün amacı dondurulan hâlin **bulunabilir** olması.
⚠️ **Eksik belge = kilitsiz.** Yanlış tahminin iki yönünden yalnız biri geri
alınabilir.

⛔⛔ **VE KAPININ SINIRI İLAN EDİLİYOR — kapı, D-179'un ihlalini
YAKALAYAMAZDI.** İhlal ad-hoc bir betikti; bu kapı yalnız **aletin kendisini**
kapatıyor. Kazanılan şey: yasak bir sayıyı okumak artık **kolay yol** değil,
**kasıtlı bir eylem**. Kendini olduğundan güçlü gösteren bir kapı, hiç
olmayandan kötüdür.

**K5:** 4 mutasyon, dördü de yakalandı (varsayılan izinli olsun · hash şartı
kalksın · eksik belge kilitli sayılsın · seviye 3 geri çekilmesin).
md5 `c25ce958…` birebir.

⚠️ **Testler bir boşluk gösterdi:** kapı eklendiğinde **hiçbir mevcut test
kırılmadı** ⇒ mevcut suite seviye 1–3'ün rapora **girdiğini** hiç iddia
etmiyormuş. Dört yeni test o boşluğu da kapatıyor.

---

### 2. Taslakta kapanan dört kusur

| kusur | nasıl kapandı |
|---|---|
| **1** | ✅ **tersine döndü.** `energy` **16/16 Price satırında**, **10'u tanımlı** (C2: 4/15, 1 tanımlı). §3.1'in *"`P_active` düşük beklenmelidir"* cümlesi **ters yöndeydi**, düzeltildi |
| **2** | ✅ Kriz D-173'te geri döndü ama alan tablosunu **bozmadı**: `resource`, `energy`'nin **yerine değil yanına** yazılıyor ⇒ hiçbir tohum düşmüyor |
| **3** | ✅ Test çerçevesiyle çözüldü (**§4.1**), ⛔ **yapısal itiraz gizlenmedi**: `ΔP_active`'in sıfır-şişkinliği bir **sonuç olarak** raporlanacak |
| **4** | ✅ Üçüncü kategori **tanımlandı**: *"inaktif"* (alan var, `Var(z)=0`) ile *"hiç oluşmadı"* (satır yok) **ayrı** raporlanıyor; oluşmamış hücre `P_active`'in **paydasına girmiyor** |

⭐ **Ve yeni bir ölçülmüş sınır (L24):** `resource` **9 satırın 9'unda
`z_variance = 0.0`** ⇒ hiçbir hücrede tanımlı değil. L14'ün confound'unun
sayısal hâli — birincil alanın `energy` olması artık **türetilmiş değil
ölçülmüş**, ama bedeli de açık: **kriz kanalı `z`'ye bilgi taşımıyor**.

---

### 3. ⛔ Kilitten önce yakalanan İKİ ESKİME — kilidin asıl kazancı

| ne | eski metin | ölçülen |
|---|---|---|
| **§3.1 beklentisi** | *"`energy` 216 okumanın 11'inde ⇒ `P_active` **düşük**"* | **16/16 satır, 10 tanımlı** ⇒ **yüksek** |
| ⭐⭐ **L20'nin sonucu** | *"sembolik kanalın somatik yarısı varise **HİÇ ULAŞMIYOR**"* | ⛔ **YANLIŞ.** D-161: **34/144** · D-173 pilotu: `I5.4` ✅ **`applied 463x`** |

⚠️ **L20 kilitlenseydi**, aksiyomun *"iki kanal"* iddiasının **yarısını
gereksiz yere feda etmiş** olurduk — ve sonuç raporunda *"bu yarı test
edilmedi"* yazacaktı, oysa ediliyor.

⇒ **Bugünün üçüncü belge-ölçüm çelişkisi** (D-176/*"iki kol"* · D-178/ROADMAP
§3 · bu). **Desen artık tek cümlede:** bu projede bir belgenin en riskli hâli
*yanlış* olması değil, **eskimiş** olması — ikisi aynı görünüyor.

---

### 4. Taslağın bugünkü durumu

**Altı slotun altısı da kapalı.** §7 D-176'nın sayılarıyla yeniden yazıldı
(eski hâli `<details>` içinde tarihçe olarak duruyor), §13'ün koşum komutu
`G=4` · **üç kol** · tohum **9929+** · `--resume` · çok-dosya birleştirme ile
güncellendi. Yeni sınırlar: **L22** (bütçe sansürü) · **L23** (uyku
konsolidasyonu yok) · **L24** (`resource` hiç tanımlı değil) · **L25** (L9
ihlali + kapı ve kapının sınırı).

**Suite: 666 passed.**

⏳ **Kalan tek şey KİLİT (adım D)** — §12'nin alet kimliği dondurulur ve durum
satırına 🔒 + commit hash yazılır. ⛔ **Bu Yasin'in kararı**, ve tek atıştır.

### 5. ⚠️ Bu kaydın sınırları

- Kusur 1/2/4'ün kapanışı **tek bir pilota** dayanıyor (3 tohum, 16 hücre).
- §4.1 bir **çerçeve** kararıdır; `ΔP_active`'in gerçekten reddedip
  reddedemeyeceği **koşum sonrası** belli olur.
- L9 kapısı **yalnız `analyze_population_run`'ı** kapatıyor.

---

## D-181 · 2026-08-24 · ⛔⛔ **KİLİT ÖNCESİ DUMAN TESTİ: birleştirici HER parçalı koşumu reddediyordu** — ve birim testi bunu göremezdi

**Bağlam:** Yasin *"kilitle eğer runı bozucak bir şey kalmadıysa"* dedi. ⇒
Kilitten önce, gerçek komut zinciri **mock ile uçtan uca** koşuldu (GPU yok,
adapter yok, mock tohumları **9305–9310** — 9929+ bloğu temiz kaldı).

---

### 1. ⛔⛔ Bulunan kusur — 70 saatin **sonunda** ortaya çıkardı

İki mock gece koşuldu, sonra birleştirildi:

```
ValueError: night2.json was produced by a different instrument or design
than night1.json (['tool_identity'] differ)
```

⇒ **B3'ün birleştiricisi, aynı çalışmanın iki meşru gecesini reddediyordu.**
Ölçüldü (tahmin edilmedi) — gece gece **tasarım gereği** değişen alanlar:

| alan | gece 1 | gece 2 |
|---|---|---|
| `tool_identity.argv` | (dışlanmıştı ✅) | |
| `tool_identity.seeds.{n,start,end,list}` | `[9305, 9306]` | `[9307, 9308]` |
| `tool_identity.sampling.seed_env` | `9305` | `9307` |

**Düzeltme:** dışlanan alan sayısı **2 → 4**. ⚠️ **`sampling` bloğunun tamamı
değil, yalnız `seed_env`** — `do_sample`, `temperature`, `max_new_tokens`
modelin **ne yaptığını** belirliyor ve eşleşmek zorunda. (Bunun kendi testi
yazıldı: `do_sample` farkı hâlâ **reddediliyor**.)

⚠️ **`_resume_fingerprint` (B2) etkilenmedi ve bilerek değiştirilmedi:**
resume aynı tohumlarla koşar ⇒ bu alanlar zaten aynı; farklıysa **reddetmek
doğrudur**.

### 2. ⭐ Asıl ders — birim testi neden göremedi

`test_two_nights_merge_into_one_study` **geçiyordu**, çünkü fixture'ında
**`tool_identity` hiç yoktu.** Karşılaştırılan alan **fixture'da mevcut
değildi** ⇒ test, gerçekte her parçalı koşumu reddeden bir kontrole karşı
boş yere yeşildi.

⇒ **K2'nin bir üst basamağı, ve kayda geçiyor:**

> **K2 bir boyutta *iki farklı değer* ister. Bu vaka bir öncesini gösterdi:
> karşılaştırılan alan fixture'da ÖNCE VAR OLMALI. Yok olan bir alan, testte
> "eşit" görünür.**

Fixture gerçeğe yaklaştırıldı (gece gece değişen üç alanı **taşıyor**) ve
**önce kusuru gösterdi** (5 test kırıldı), sonra düzeltme yeşile çevirdi.

**K5:** 2 mutasyon (`seeds` dışlanmasın · `seed_env` dışlanmasın), ikisi de
yakalandı. md5 `092339ce…` birebir.

### 3. ✅ Duman testinin doğruladıkları — gerçek komut zinciri

| kontrol | sonuç |
|---|---|
| `--arms lived shuffle null` · `--n-generations 4` | ✅ üç kol, 6 kol-tohum/gece |
| ⭐ **B1 canlıda** | ✅ **`I4.2 = True`** (pilotta 6/6 hücrede ayrışıyordu) |
| ⭐ **B2 canlıda** | ✅ koşum 60 sn'de **öldürüldü** → `--resume` → **3 bitmiş kol korundu**, **yarım kalan kol (1 nesil, RNG defteri yok) yeniden koşuldu** → `complete: true`, 6 kol, partial **silindi** |
| ⭐ **B3 canlıda** | ✅ **üç gece tek çalışma** olarak okundu (6 tohum), dosya başına defter basıldı |
| ⭐ **D-178 canlıda** | ✅ `I5.1 = None` (*"değerlendirilmedi"*), `False` değil |
| ⭐ **D-180 canlıda** | ✅ `pre-registration: 📝 NOT LOCKED — levels 1-3 WITHHELD (L9)` |

**Suite: 667 passed.**

### 4. ⚠️ Sınırlar

- Duman testi **mock LLM** ile koşuldu ⇒ **eğitim yolu (DPO) hiç çalışmadı**.
  Doğrulanan şey **orkestrasyon**, öğrenme değil.
- Süre ölçümü değil: mock koşumun süresi gerçek koşum hakkında **hiçbir şey**
  söylemez.
- `I5.5 = False` ve `run_quality = flagged` **stub'ın kendi özelliği**
  (`STUB_EXPECTED_FLAGS` deseni), koşum hakkında bir şey değil.

---

## D-182 · 2026-08-24 · 🔒🔒 **ÜÇÜNCÜ ÖN-KAYIT KİLİTLENDİ** — commit `a1163ac778c9`

**Yetki:** Yasin, 2026-08-24: *"kilitle eğer runı bozucak bir şey
kalmadıysa."* ⇒ Şart D-181'in duman testiyle karşılandı (bir kusur bulundu,
düzeltildi, zincir uçtan uca doğrulandı), sonra kilit atıldı.

`docs/PREREGISTRATION_3.md` durum satırı: **🔒 KİLİTLİ · 2026-08-24 · commit
`a1163ac778c9`**. §12'nin alet kimliği **donduruldu** — hepsi koddan okundu,
yeniden yazılmadı (§2.8).

### 1. Dondurulan hâl — özet

| | |
|---|---|
| commit · suite | **`a1163ac778c9`** · **667 passed** |
| model · quantization | Llama-3.1-8B-Instruct · NF4 + double_quant, fp16 compute |
| LoRA · DPO | rank 8 / alpha 16 · β=0.1, lr=1e-06, grad_accum=4, max_seq=512 |
| üretim | greedy, `max_new_tokens`=64 |
| uç nokta ordinali | `LANDMARK_EVENT` = 10 |
| havuz fiziği (Katman 1b) | `NICHE_POOL_FRACTION_RANGE` = (0.40, 0.5239898356037742) · `EXTRACTION_LIMIT_RATIO` = 0.1425 |
| üreme | turnuva k=2 · kazanan başına 1 varis · sıralı erişim + rotasyon açık |
| sınır sabiti | `SLEEP_CONSOLIDATION_WIRED` = False (L23) |

### 2. ⭐ Kilit kendi kapısını açtı — ve bu tasarlanmıştı

D-180'in L9 kapısı izni **bu belgenin durum satırından** okuyor. Kilit
atılınca `preregistration_locked()` **kendiliğinden `True`** döndü ve rapor
seviye 1–3'ü açtı — **hiçbir bayrak elle çevrilmedi**.

⇒ İki yönlü kanıt: yazılmamış bir kilit raporu **açmıyor**, açılan bir rapor
kilidin **yazıldığının kanıtı**.

### 3. Kilide giden yolda bulunan ve düzeltilenler

| kayıt | ne bulundu |
|---|---|
| **D-176** | Kat 2 = seviye 3 = **üç kol**; yol haritasının maliyet tablosu **iki kol** üzerinden yazılmıştı |
| **D-177** | I4.2 kilitsizdi · **resume yoktu** · **birleştirici yoktu** |
| **D-178** | ROADMAP §3'ün çıkarımı çürüktü — Kanal 1 **ölü değil** |
| **D-179** | ⛔ **L9 ihlali** (ilan edildi, L25) · kusur 1 **tersine döndü** |
| **D-180** | §3.1'in beklentisi ve **L20'nin sonuç cümlesi eskimişti** |
| **D-181** | ⛔⛔ birleştirici **her parçalı koşumu reddediyordu** |

⇒ **Altı denetimin altısı da bir şey buldu.** ⚠️ Bunların **üçü** (D-176,
D-178, D-180) *"belge güncel ama eskimiş"* sınıfındandı — bu projenin en
tekrarlayan hata deseni, ve artık adı var.

### 4. ⚠️ Kilit anında bilinen ve ilan edilen riskler

- ⛔ **Eğitim yolu (DPO) B1'den SONRA gerçek GPU'da koşulmadı.** D-181'in
  duman testi **mock**tu ⇒ doğrulanan şey orkestrasyon. B1'in eklediği
  `_lock_seeds` **multigen koşucusunun eğitim yolunda zaten kullandığı**
  desendir, ama bu koşucuda ölçülmedi. ⇒ **`I1.1` kapısı bunu ilk gecede
  sınar ve ağırlık hareket etmediyse ABORT eder.**
- ⚠️ **Resume'un eşdeğerliği stub altında ölçüldü** (D-177 §5); `--lora`
  açıkken **denenmedi**. İlk gecede fiilen sınanmalı.
- ⚠️ **Tohum başına süre bir TAHMİNDİR** (3 sa 00 dk – 3 sa 13 dk), dayanağı
  D-173'ün ölçülen **16.1 dk/kol-nesil** oranı. Gerçek `t` **ilk geceden**
  okunacak ve `N_eff` durma kuralının aritmetiğiyle (`⌊q·T_max/t⌋`) yeniden
  uygulanacak — bu **post-hoc değil**, kuralın kendi tanımı (D-174).

---

## D-183 · 2026-08-25 · ✅✅ **GPU DUMAN KOŞUMU: `run_quality = clean`** — eğitim yolu ve resume muafiyeti canlıda doğrulandı

**Yetki:** Yasin, 2026-08-24: *"duman yapalım sorun yok."*
⚠️ **Süre tahminim düzeltildi ve öyle ilan edildi:** 40 dk demiştim, gerçek
tasarım **1 sa 48 dk** sürdü — çünkü mock duman `--no-lora` koştuğu için
**hiç adapter yazmamıştı** ⇒ resume'un I0.7 muafiyeti **hiç sınanmamıştı**.

**Koşum:** `dau_runs/smoke_d182_lora_s9970.json` · tohum **9970** (koşum
bloğunun **dışında**, 9929–9948 temiz kaldı) · 8 ajan · G=2 · 2 kol · `--lora`
· 23:07:56 → 00:55:36 = **1 sa 48 dk** · ⚠️ **keşifsel**, hipotez testi değil.

**Tasarım:** koşum, `lived` kolu **bitip diske gerçek adapter yazdıktan sonra**
öldürüldü (çökme benzetimi), sonra `--resume` ile devam edildi. ⛔ Resume
adımında **dış `timeout` YOK** (D-126).

### 1. ⭐ Sonuç: 11 kapının hepsi

| kapı | sonuç | detay |
|---|---|---|
| **I1.1** | ✅ **PASS** | *"48 train arms moved lora_B"* ⇒ ⭐ **eğitim yolu B1'in RNG kilidinden sonra çalışıyor** — kilit anında ilan edilen **en büyük risk kapandı** |
| **I0.7** | ✅ **PASS** | *"16 agent(s) start from the base policy"* — ⭐ **diskte `lived` kolunun 16 adapter dizini varken**. ⇒ **resume muafiyeti (D-177/B2) canlıda doğrulandı** |
| **I4.2** | ✅ **PASS** | *"one RNG state each"* — B1 gerçek eğitim altında da tutuyor |
| **I4.1** | ✅ **PASS** | replay **bit-birebir** (`13173ca05451`), `--lora` altında |
| **I5.4** | ✅ **PASS** | *"applied 321x"* ⇒ ⭐ **D-180'in L20 düzeltmesi teyit edildi** — somatik kanal akıyor |
| **I5.1** | **None** | *"not evaluated: sleep consolidation is not wired…"* ⇒ **D-178'in sınırı canlıda okundu**, `False` değil |
| **I5.6** · **I0.3/4/6** · **I5.5** | ✅ PASS | — |

⇒ **`run_quality = clean`**, `complete = true`.

⚠️ **I5.5'in içeriği bu koşumda bilgisiz:** *"2 transitions; 2 founder (out of
scope by YENİ-4), 0 scored"* — G=2'de her iki geçiş de kurucu geçişi. Beklenen
ve **koşumun amacı değil**.

### 2. Ölçülen hız — ve bütçeye etkisi

| | |
|---|---|
| koşum 1 (`lived`, 2 nesil, 424 olay) | 35.5 dk ⇒ **5.03 sn/olay** |
| koşum 2 (`shuffle` 2 nesil + replay, ~856 olay) | 72.2 dk ⇒ **5.06 sn/olay** |

⭐ **İki bağımsız ölçüm 5.03 / 5.06 sn** — D-173 pilotunun **5.2 sn/olay**'ıyla
tutuyor ⇒ hız tabanı **doğrulandı**.

**Doğrulayıcı koşum için yeniden hesap** (pilotun kol başına olay eğrisi:
178 · 204 · 209 · 216 = **806.5 olay/kol**, üç kol ⇒ **2419.5 olay/tohum**):

| | |
|---|---|
| tohum başına | **3 sa 12 dk – 3 sa 22 dk** (alt uç: `null` eğitim yapmıyor) |
| replay (çağrı başına) | **~36 dk** |
| **20 tohum · 5 gece** | **67 – 70.3 sa** |

⛔ **Bu, ilan edilen `T_max` = 70 saatin SINIRINDA.** Durma kuralının kendi
aritmetiği (`N_eff = ⌊q·T_max/t⌋`, D-174) replay yükü sayıldığında **19–20
tohum** veriyor ⇒ MDE **0.676 – 0.696**.

⇒ ⚠️ **Bu post-hoc bir daralma değil**, kuralın tanımı: `t` ölçülür, `N_eff`
türetilir. **İlk gecenin gerçek `t`'si okunduktan sonra bir kez daha
uygulanacak.**

### 3. ⚠️ Sınırlar

- **Keşifsel koşum**, G=2 ⇒ Price/seviye okumaları **bilgisiz** ve okunmadı.
- Hız ölçümü **tek tohum**; niş yayılımı D-145'te **2.3 kat** ölçülmüştü ⇒
  gece uzunluğu tohuma göre oynayabilir.
- Model yükleme her çağrıda tekrar ödeniyor ve bu ölçümde **iki kez** ödendi
  ⇒ uzun gecelerde etkin hız **biraz daha iyi** olur (tahmin **tutucu**).
- **Tohum 9970 kullanıldı** ve diskte 48 adapter dizini bıraktı.

### 4. Koşum öncesi durum

Boş disk **40 GB** · `adapters/` **19 GB** · tohum bloğu **9929–9948
tertemiz** (0 adapter) · suite **667 passed** · ön-kayıt 🔒 `a1163ac778c9`.

---

## D-184 · 2026-08-25 · 🔍 **DR #14 MUTABAKATI** — iki şey alındı, merkez tavsiye **ölçümle çürüdü**

**Bağlam:** Yasin brief'i bilerek gevşetmemi istedi (*"sınırlamalardan çekil
ki radikal karar alabilsin"*). Uygulandı: C1–C6 **yasak** olarak değil
**meydan okunacak liste** olarak verildi, her öneri için **COST satırı** (R6)
istendi. Tam mutabakat `RECONCILIATION.md` **§W**.

### 1. ⭐⭐ Alınan birinci şey: effective rank — ve **hemen ölçüldü**

Roy & Vetterli 2007 (`10.1109/TSP.2007.898918`):
`r_eff(Z) = exp(−Σ p_k ln p_k)`, `p_k = σ_k / Σσ_j`.

**Gece 1 verisinde hesaplandı** (48 hücre, `z` = 8 ajan × 4 alan):

| | |
|---|---|
| **medyan** | **1.000** |
| ortalama | 0.947 · min 0.000 · max 1.995 |
| nesil | gen1 **0.250** → gen2 1.000 → gen3 1.203 → gen4 **1.337** |
| | 48 hücrenin **38'i** `r_eff ≤ 1.0` |

⇒ ⭐ **L3 artık türetme değil, ölçülmüş istatistik.** *"`z` etkin olarak tek
boyutlu"* iddiasının dayanağı bugüne kadar bir **argümandı** (`k` 192/192
sabit + skaler spillover). Artık **atıf verilebilir bir yöntemle çıkmış bir
sayı**, ve nesil boyunca **yükseldiği ama 4'e yaklaşmadığı** da görünüyor.

⚠️ **Alıntısı bozuk** (§W.7) ama **yöntem doğru** — formül literatürdeki
tanımla birebir, ve kendi verimizde çalıştı.

### 2. ⭐ Alınan ikinci şey: van Veelen 2005 — elimizde olmayan eleştiri

`10.1016/j.jtbi.2005.04.026` — Price eşitliğinin **totoloji** olduğu ve
dinamik yetersizliği. Bu kaynağı **hiç görmemiştik**. L7/L8'i keskinleştiriyor
ve sonuç raporuna *"Price seçilimi verir, dinamiği vermez"* için dayanak.
⚠️ Alıntı birebirliği **doğrulanmadı**.

### 3. ⛔⛔ Merkez tavsiye ölçümle çürüdü

DR'nin en yüksek sesle söylediği şey: *"evrensel defection ⇒ özdeş `z`
yörüngeleri ⇒ `Var(z)=0`; darboğaz 2/3'ü 1'i düzeltmeden çözmek boşa emek."*

| ölçüm | sonuç |
|---|---|
| kurucular ayrışıyor mu (D-173/Q2) | ✅ **her tohumda 8/8** |
| `Var(w) > 0` (gece 1) | ✅ **48/48 hücre OPEN** |

⭐ **Sebep:** DR **eşzamanlı, iyi karışmış hasat** varsaydı. Bizde hasat
**sıralı** ve tavan **kalan stoka oranlı** — *"özdeş karar veren ama farklı
yaşayan ajanlar"* bu evrenin **kurulma amacı** (D-084). Defection'da
birleşseler bile ayrışıyorlar.

⇒ ⚠️ Brief mimariyi **anlatıyordu**; okunmamış ya da modellenmemiş.

### 4. ⛔ Ölçülmüş bir şeyin tersini önerdi

*"Greedy'yi bırak, `T=0.7, p=0.9` + deterministik tohum hattı."*
⛔ **D-037 bunu ölçtü:** `warn_only` altında aynı tohum + aynı kod **farklı
adapter** ve **21/50 karar farkı**; gürültü **0.026**, kol farkı **0.015–0.025**
⇒ **gürültü etkiden büyüktü.** `I0.6` determinizmi bu yüzden zorunlu kılıyor.

### 5. ✅ Teşhis doğru, reçete mimariye uymuyor (darboğaz 5)

DR *"kapı `if len(heir.log) > 0`"* dedi — ✅ **kodda doğrulandı**,
`graph.py:1116` → `if state.delta_log:`.
⛔ Ama önerdiği düzeltme (`heir.somatic_scale = parent.final_...`) **böyle bir
alan olmadığı için** uygulanamaz: ölçek `inherited_warning` bayraklı
**bellek kayıtlarının içinde**, `emotional_weight.py:124` onu **retrieval
bağlamından** okuyor.
⛔ Ve DR'nin *"hiçbir taahhüdü kırmıyor"* COST satırı **yanlış** — bu bir
**fizik değişikliği** ve ön-kayıt **kilitli**.

### 6. Kaynak disiplini — R2 iki kez kırıldı, şart yine yakalattı

| şart | sonuç |
|---|---|
| R1 DOI | ✅ 8/8 |
| **R2 birebir alıntı** | ⛔ **Roy & Vetterli**: verilen alıntı **onlar hakkında üçüncü bir makalenin** metni (bir makale kendi yazarlarından üçüncü şahısla söz edemez) · ⛔ **Park ve ark. 2023**: *"alıntı"* olarak **makale başlığı**, üç ayrı iddiaya dayanak gösterilmiş |
| R3 boşluk ilanı | ⚠️ bir kez yapıldı; *"S ≥ 30 tohum standarttır"* **kaynaksız** |
| R5 saldırı vektörü | ✅ |
| R6 COST | ✅ ama **biri hatalı** |

⚠️ **Desen üçüncü kez teyit edildi:** şart listesi kusuru **engellemiyor**,
**yakalanabilir** kılıyor. İkisi de birebir-alıntı şartı olmasa fark
edilmeden geçerdi.

⛔ **Cevaplanmayan soru Q1c:** *"çevresel yapı TEK BAŞINA, özdeş promptlu LLM
ajanlarında çeşitlilik üretir mi"* sorusuna **Nowak 2006** (replikatör
dinamiği, LLM değil) ile cevap verildi ⇒ **ikame**, ve boşluk **ilan
edilmedi**.

### 7. ⛔ Kesişen sınır — hiçbiri bu tura uygulanamaz

DR'nin **aksiyona dönük her önerisi bir fizik değişikliği**; ön-kayıt
🔒 **kilitli** (`a1163ac778c9`) ve koşum **sürüyor** (gece 2).

⇒ Bu bir kayıp değil: brief **zamanlaması bilinerek** yazıldı. Çıktısı
**dördüncü ön-kayıtın girdisi**.

### 8. Bu turdan çıkan iş listesi

| # | iş | ne zaman |
|---|---|---|
| **1** | `r_eff`'i `analyze_population_run`'a ekle (saf raporlama, §2.10 altında meşru) | ⏸ **koşum bitince** |
| **2** | van Veelen 2005 ve Roy & Vetterli 2007 alıntılarını **kaynaktan doğrula** | ⏸ koşum bitince |
| **3** | Wasserstein + permütasyon · uzamsal kafes + dışlama · alan-ayrıştırılmış `z` | ⏸ **dördüncü ön-kayıt** aday listesi |
| **4** | Darboğaz 5'in **gerçek** reçetesi (kayıt yapısı üzerinden) | ⏸ dördüncü ön-kayıt |

### 9. ⚠️ Sınırlar

- `r_eff` **tek gecede** (4 tohum) ölçüldü; beş gece bitince tam veriyle
  yeniden okunacak.
- van Veelen ve Roy & Vetterli alıntıları **doğrulanmadı** — kimlikler makul,
  metin kontrolü bekliyor. **Doğrulanmadan kayda *"kaynak şunu diyor"* diye
  yazılmayacak.**
- §W.5'in çürütmesi **bizim ölçümümüze** dayanıyor; DR'nin genel iddiası
  (iyi karışmış sistemlerde 1→2→3) **başka mimariler için doğru olabilir**.

---

## D-185 · 2026-08-25 · ⭐ **KAT 3 SONRASI YOL AÇILDI — nakil testi (common-garden) ve iki bağlayıcı kural**

**Yetki:** Yasin, 2026-08-25. Kendi çerçevesi: *"makul bir noktada gerçekten
bir şey kanıtlayarak listeyi bitir, sonra sınırlara takılmadan yapabileceğimizi
yap … sonra gerekirse belimizi büken kısımların mimarisini değiştiririz, kodun
aslını koruyarak, bir branch'te."*

⚠️ **Bu kayıt bir plan kaydıdır**, ölçüm değil. Ama iki **bağlayıcı kural**
kuruyor (§2, §3) ve o yüzden `ROADMAP.md` §9'a yazıldı.

### 1. ⭐ Fikrin adı var: common-garden

Yasin'in önerisi (*"bu agentları alıp sıfır bir ortama koysak davranışları
gerçekten değişmiş mi, yoksa sadece bir rakam mı"*) biyolojide **common-garden
deneyidir**: farklı soyları **özdeş** bir ortamda okuyup farkın sürüp
sürmediğine bakmak.

⭐ **Ve bu, bu projeye yöneltilecek en sert eleştirinin doğrudan cevabı.**
D-176'dan beri kayıtlı olan saldırı: *"bu bir trait'in kalıtımı mı, yoksa bir
durumun taşınması mı?"* Eğer `lived` ve `shuffle` varisleri **hiçbirinin
yaşamadığı özdeş bir nişte** farklı davranıyorsa, kalıtılan şey **durum
değildir** — çünkü durum orada yok.

⭐ **Hiçbir taahhüdü kırmıyor:** K7'ye, C1'e, C2'ye dokunmuyor. Bir **okuma**,
müdahale değil.

### 2. ⛔ BAĞLAYICI KURAL 1 — nakil, sınır kırmadan ÖNCE

Nakil bir sonuç değil **gündem belirleyicidir**: hangi sınırı kırmaya
değeceğini o söylüyor.

| nakil sonucu | sonraki hamle |
|---|---|
| davranış gerçekten farklı | **K7 kırılmaz**; enerji `z`'nin boyutuna (L3) gider |
| davranış aynı, yalnız sayı farklı | **K7 kırılır**, gerekçesi artık **ölçüme** dayanır |

⇒ Sınırı önce kırıp sonra bakmak, **hangisini kırmak gerektiğini bilmeden**
kaldıraç harcamaktır (kalan hak: **2**).

### 3. ⛔ BAĞLAYICI KURAL 2 — sıra bozulamaz

> **`docs/C3_RESULTS.md` yazılıp commit edilmeden hiçbir keşifsel nakil
> sonucuna BAKILMAZ.**

Kilitli koşumun sonucunu, sonradan gelen keşifsel bir bulgunun ışığında
**yeniden yorumlama** baskısı gerçektir. Sıra bozulursa *"ön-kayıt neyi
korudu"* sorusunun cevabı kalmaz.

### 4. ⚠️ Tasarımın keskinleştirilmesi — ve iki ölçülmemiş varsayım

**Ham hâliyle *"taze dünyaya koy, bak"* bilgisiz dönebilir:** L18 yüzünden
ikisi de DEFECT der. ⇒ Niş **rastgele seçilmiyor**: ajanları **D-090'ın
işaretlediği bölgeye** sokan bir niş (düşük enerji + yüksek drift), çünkü orada
`cooperate` eşiği **keskin ve tırtıksız** ölçülmüştü. Soru böylece
*"davranış değişti mi"*den **"kol, eşiğin hangi tarafına düşüleceğini öngörüyor
mu"**ya döner — sayılabilir bir soru.

⛔ **İki şey ölçülmeden varsayılmayacak:**
1. **Varis diskten diriltilebiliyor mu?** Adapter'lar `dau_runs/adapters/`
   altında **duruyor**; **kasanın kalıcılığı doğrulanmadı** (`arm_vault` bir
   bağlam yöneticisi, çıkışta kapanıyor). Diriltilemiyorsa nakil, varisleri
   üreten **kısa bir koşum** ister ⇒ bedeli sıfır değil.
2. **D-090 bugünkü fizikte hâlâ geçerli mi?** O ölçüm **tek-soy yolunda** ve
   **Katman 1/1b'den önce** yapıldı. Eşiğin hâlâ orada olduğu **önce
   sınanmalı** — aksi hâlde nakil yanlış bölgeye yapılır.

### 5. Branch mekaniği — kayda geçirilen dört ayrıntı

- **Kilit noktasından dallan:** `git branch exp/transplant a1163ac778c9` ⇒
  dalın tabanı ön-kayıtın **dondurduğu** hâl.
- `main` **dondurulmuş sayılır** (koşum + `C3_RESULTS.md` bitene kadar).
  ⚠️ Koşum sürerken `.py` düzenleme **dalda da yasak** — aynı GPU.
- Çıktılar **ayrı isim alanına**: `dau_runs/exp_*`. Yoksa D-177/B3'ün
  birleştiricisi alet uyuşmazlığı diye reddeder (**doğru** davranış).
- ⚠️ **Dalda keşif serbest, İDDİA değil.** İddia ⇒ **dördüncü ön-kayıt** +
  kilit. *Keşif ucuz, iddia pahalı; ikisini ayıran şey kilittir.*

### 6. `ROADMAP.md` §9 açıldı — ve neden

Belge **Kat 3'te bitiyordu**. ⚠️ Bu, D-175'te düzelttiğimiz durumun aynısı:
*"projenin yazılı varış noktası yoktu."* Kat 3 bir **bitiş çizgisi değil bir
kapı**; arkasında ne olduğu artık yazılı (§9.1–§9.6), aday listesi DR #14'ten
geliyor (D-184).

### 7. ⚠️ Sınırlar

- Bu **plan**, ölçüm değil. §4'ün iki varsayımı **ölçülmeden** nakil
  tasarlanamaz.
- Nakil **keşifseldir**; iddia üretmez. İddia dördüncü ön-kayıta bağlıdır.
- §2'nin tablosu bir **karar ağacı**, tahmin değil — nakil sonucu her iki dala
  da düşebilir.

---

## D-186 · 2026-08-25 · ⭐⭐ **L3'ÜN SONUCU DOĞRU, GEREKÇESİ YANLIŞ** — `z` argmax'ta ölüyor, spillover'da değil

**Bağlam:** Yasin *"iddiamızı daraltan sonuçlara insana ve evrime bakarak
basit çözümler düşünelim"* dedi. L3'e (*"`z` etkin olarak tek boyutlu"*)
bakarken **eksenlerin kendisi ölçüldü** — ve gerekçe çöktü.

### 1. Ölçüm (gece 1, 384 ajan-yaşamı, 9736 olay)

**a) Dört eksen birbirinin skaler kopyası DEĞİL:**

| çift | korelasyon |
|---|---|
| energy ↔ resource | **+0.101** |
| energy ↔ social | **+0.021** |
| energy ↔ uncertainty | **+0.060** |
| resource ↔ social | **−0.062** |

Oranların std'si **0.019–0.224**, 384 satırda **319 benzersiz oran**.
⇒ Skaler kopya olsalardı oran **sabit** olurdu. Değil.

**b) Ama `z` yine de tek boyutlu** (`r_eff` medyan **1.000**, D-184).

**c) Sebep bulundu — argmax:**

`graph.py:916` → `_primary_affected_domain` = `max(changes, key=changes.get)`.
**Kazanan-hepsini-alır.** Sonuç:

| `z`'de dolu alan sayısı | ajan |
|---|---|
| **0** | 182 / 384 |
| **1** | 164 / 384 |
| **2** | 38 / 384 |
| 3 veya 4 | **0** |

Argmax'ı kim kazanıyor: `energy` **8589**, `resource` 725, `social` 387,
`uncertainty` 35 (9736 olayda).

### 2. ⛔ L3'ün yazılı gerekçesi çürüdü

`PREREGISTRATION_3.md` L3 ve `CLAUDE.md` GAP-10 şunu diyor: *"ikincil eksenler
`k`'nin sabit katı ⇒ dört sayı dört boyut değil."*

⛔ **Ölçüm bunu desteklemiyor.** Eksenler neredeyse **bağımsız**. `CROSS_AXIS_SPILLOVER
= 0.20` yalnız **PE enjeksiyonuna** uygulanıyor (`delta.py:84`); durum
değişkenleri ayrıca metabolizma ve hasattan da hareket ediyor
(`graph.py:897` — dört ayrı fiziksel niceliğin farkı).

⚠️ **D-136 bunun yarısını zaten görmüştü** (*"social/uncertainty ölü değil,
C2'nin sıfırı bir argmax artefaktı"*) ama sonra *"asıl sebep argmax değil,
skaler spillover"* dedi. **Bugünkü veriyle o çıkarım ayakta değil.**
⚠️ Adil olmak gerekirse D-136 **C2 fiziğinde** ölçmüştü; fizik üç kez değişti.

### 3. ⭐ Bunun neden büyük fark yarattığı

| gerekçe | düzeltmenin bedeli |
|---|---|
| *"skaler spillover"* (eski) | **yeni fizik** — asimetrik matris denendi, **+%2.29**, eşiği geçmedi (D-137) |
| ⭐ *"argmax bilgiyi atıyor"* (ölçülen) | **yeni sabit YOK, yeni fizik YOK** — uç noktanın **tanımı** değişir |

⇒ **Bilgi zaten üretiliyor ve zaten kaydediliyor** (`delta_profile.axes.deltas`,
D-136'nın aletlemesi). Onu **atan** şey uç noktanın indirgeme operatörü.

⭐ **İnsan bilişi açısından:** Damasio'nun somatik işaretleyicileri
**kazanan-hepsini-alır değildir** — beden aynı anda birden çok kanalda
işaretler ve bunlar **birlikte** karara girer. `argmax` bir *hissin* değil,
*bir kararın* modelidir. Bedende argmax yok.

### 4. ⛔ Bu koşuma etkisi: YOK

`z` ön-kayıtta **tanımlı ve kilitli**. Bu bir **dördüncü ön-kayıt** bulgusu.
Koşan tur etkilenmiyor, hiçbir sayı değişmiyor.

### 5. Kayıt düzeltmesi

⛔ **L3'ün metni dördüncü ön-kayıtta düzeltilmeli.** Bugünkü doğru hâli:

> `z` **etkin olarak tek boyutludur** (`r_eff` medyan 1.000) — ⚠️ ama sebebi
> eksenlerin bağımlı olması **değil**, uç noktanın **argmax ile indirgenmesidir**.
> Alttaki dört eksen **neredeyse bağımsız** ölçüldü (|r| ≤ 0.10).

⚠️ `PREREGISTRATION_3.md` **kilitli** ⇒ metin **bu belgede değiştirilmiyor**;
düzeltme dördüncü ön-kayıta taşınıyor ve burada ilan ediliyor.

### 6. ⚠️ Sınırlar

- Tek gecede (4 tohum) ölçüldü; beş gece bitince tekrarlanacak.
- Korelasyonlar **yaşam-ortalaması** eksen deltaları üzerinden; olay
  düzeyinde bağımlılık farklı çıkabilir.
- *"Argmax kaldırılırsa `r_eff` yükselir"* bir **çıkarım**, ölçüm değil —
  dördüncü ön-kayıt öncesi **mevcut veriden hesaplanabilir** (eksen
  vektörünü doğrudan `z` sayıp `r_eff` bakmak). Ucuz, ve yapılmalı.

---

## D-187 · 2026-08-25 · ⭐⭐ **`z`'nin BOYUTU GERİ KAZANILABİLİR: `r_eff` 1.000 → 3.194** — ve iki müdahale birden gerekiyor

**Bağlam:** D-186 argmax'ı suçlu ilan etmişti ve son satırında *"argmax
kaldırılırsa `r_eff` yükselir, bu bir ÇIKARIM, mevcut veriden hesaplanabilir"*
diyordu. Yasin *"yap"* dedi. Hesaplandı.

⚠️ **Keşifsel yeniden-analiz**, gece 1 verisi (48 hücre). Koşuma dokunulmadı,
hiçbir sabit değişmedi.

### 1. Üç senaryo, aynı 48 hücre

| # | `z` tanımı | `r_eff` medyan | ort | `≥ 3` |
|---|---|---|---|---|
| 1 | **mevcut** — argmax'la etiketlenen alan | **1.000** | 0.947 | 0/48 |
| 2 | argmax **yok**, dört eksen doğrudan | **1.453** | 1.536 | 0/48 |
| 3 | ⭐ argmax yok **+ eksen başı z-skor** | **3.194** | 3.167 | **33/48** |

Hücre başına artış (1→2): medyan **+0.490**, **43/48 hücrede** yükseldi.

### 2. ⛔ Kendi tahminimi düzeltiyorum

D-186'yı sunarken *"argmax kaldırılırsa `r_eff` 3.2 çıkabilir"* diye örnek
vermiştim. ❌ **Tek başına argmax'ı kaldırmak 1.453 veriyor**, 3.2 değil.
**3.194'e ancak ikinci müdahaleyle** ulaşılıyor.

### 3. ⭐ Sebep ölçüldü — bağımsızlık yetmiyor, ÖLÇEK de gerekiyor

| eksen | ortalama büyüklük |
|---|---|
| `energy` | **0.3153** |
| `social` | 0.1006 |
| `resource` | 0.0774 |
| `uncertainty` | **0.0361** |

`energy / uncertainty` = **8.7 kat**, `energy / social` = **3.1 kat**.

⇒ Effective rank **tekil değerlere göre** ağırlıklandırır. Eksenler
**bağımsız** (D-186: |r| ≤ 0.10) ama **küçük** olan neredeyse hiç katkı
vermiyor. ⇒ **Düşük korelasyon ≠ karşılaştırılabilir varyans.**

⭐ **DR #14 ile bağımsız yakınsama:** DR'nin 2.1 adayı (*"her ekseni tarihsel
popülasyon varyansına normalize et"*) teoriden önerilmişti; burada **sayısı
çıktı**.

### 4. ⛔⛔ En önemli ayrım — hangi versiyon KALDIRAÇ HARCAR

| değişiklik | fizik değişir mi | bedel |
|---|---|---|
| `z`'yi **eksen vektörü** olarak tanımla (argmax etiketini **runtime'da bırak**) | ❌ **hayır** — eksen değerleri **zaten hesaplanıyor ve zaten kaydediliyor** (`delta_profile.axes.deltas`, D-136) | ⭐ **saf ölçüm değişikliği** ⇒ taban sıfırlanmaz |
| Argmax'ı **runtime'dan** kaldır | ✅ **evet** — `affected_domain` etiketi delta log'a yazılıyor, o da duygusal ağırlığa, o da prompt'a gidiyor | **kaldıraç harcar** |

⇒ ⭐ **Ucuz yol var ve önce o denenmeli.** `z`'yi kaydedilmiş eksen
vektöründen okumak **hiçbir sayıyı sıfırlamaz**.

### 5. ⚠️ Sınırlar — ve bir §2.7 tuzağı

- ⛔ **z-skor normalizasyonu bu hesapta KOŞUMUN KENDİ istatistiğini kullandı.**
  Ön-kayıtlı bir uç noktada bu **sonuca göre ayar** olur (§2.7). Dördüncü
  ön-kayıtta referans **önceden** ilan edilmek zorunda — örn. **kurucu
  neslin** yayılımı ya da sabit bir bölen. **Bu hâliyle uç nokta olamaz.**
- Tek gece, **4 tohum**, 48 hücre. Beş gece bitince tekrarlanacak.
- `r_eff` **yaşam-ortalaması** eksen deltaları üzerinden; landmark anının
  kesitiyle farklı çıkabilir.
- ⚠️ `r_eff = 3.19` *"dört bağımsız içerik kanalı"* **demek değil** — dört
  farklı fiziksel niceliğin farkı olduğunu gösterir. Kovaryansın **hangi
  alanda** olduğu iddiası hâlâ ayrı bir savunma ister.

### 6. Bu koşuma etkisi: YOK

`z` ön-kayıtta kilitli. Bulgu **dördüncü ön-kayıtın** girdisi; `ROADMAP.md`
§9.5'in *"alan-ayrıştırılmış `z`"* adayı artık **bir sayıya** dayanıyor.

---

## D-188 · 2026-08-25 · ⛔⛔⛔ **L18 ARTIK DOĞRU DEĞİL — davranış çökük değil, %57 `cooperate`**

**Bağlam:** ROADMAP §9.1 kendi şartını koymuştu: *"D-090 bugünkü fizikte hâlâ
geçerli mi? Önce sınanmalı."* Sınamak için gece 1'in davranış dağılımına
bakıldı — ve **daha büyük bir şey çıktı**.

⚠️ **Havuzlanmış, betimleyici okuma. KOL KIRILIMI YAPILMADI (L9).**
Ön-kayıt §3.3 `demand`'i betimleyici olarak listeliyor.

### 1. Ölçüm — gece 1, 9736 karar olayı, tüm kollar havuzlanmış

| sonuç | sayı | oran |
|---|---|---|
| **`cooperate`** | **5575** | **57.3 %** |
| `defect` | 3854 | **39.6 %** |
| `deadlock` | 307 | 3.2 % |

⛔ **L18'in iddiası: *"olayların %94–100'ünde DEFECT"* (D-068).**
⇒ **Ölçülen: %39.6.** Sınır **iki buçuk kat** yanlış tarafta.

**Landmark'a kadar (ilk 10 olay, 3840 karar):** defect **%57.7** ·
cooperate %41.4 ⇒ ⭐ **erken yaşamda defect baskın, yaşam boyunca cooperate
öne geçiyor.** Bu, D-090'ın *"cooperate düşük enerji + yüksek drift
bölgesinde"* gözlemiyle **yön olarak tutarlı** — ama artık **dar bir bölge
değil, çoğunluk**.

**Nesil bazında defect (havuzlanmış):** gen1 %38.5 · gen2 %33.5 ·
gen3 %39.3 · gen4 %46.6.
⚠️ **Bu bir etki değil, betimleme** — kollar birlikte, yorumlanmıyor.

### 2. ⭐ İkinci, DAHA GÜÇLÜ ayak — talep miktarları

`cooperate` etiketi **sözcük tabanlıdır** (`extraction.py:181`, anahtar
kelime eşleme) ve **GAP-5/L14'ün tam konusudur** (prompt sözlüğü etiketi
yönlendirebilir). O yüzden tek başına yeterli kanıt değil.

⭐ **Ama hasat miktarı metinden AYRI parse ediliyor** (`decision_to_extraction`
önce sayıyı arar) ve **o da dağılmış**:

| | eski fizik (D-084) | **bugün (48 hücre)** |
|---|---|---|
| hasat miktarı | **10/10 sondada 8.0**, benzersiz outcome = **1** (*"soğurucu çıktı"*) | hücre ortalamaları **3.63 – 6.93** |
| medyan talep | — | **2.0 – 8.0** |
| en büyük talep | — | **25.0** (⇒ `EXTRACTION_DEFECT = 8.0`'in **üstünde**) |

⇒ **Bu bir etiketleme artefaktı değil.** Ajanlar gerçekten **farklı sayılar**
istiyor, ve bazıları eski *"defect kotası"*nın üstüne çıkıyor.

### 3. ⛔ Neden bunu bugüne kadar görmedik

L18, **D-068'de** ölçüldü — ve o ölçüm **sabit kota fiziğinden**. Katman 1
(D-162/163) hasadı **stoka oranlı bir tavana** bağladı, Katman 1b (D-171)
niş bandını daralttı. ⇒ Ortamın karnesi değişti, **davranış onunla birlikte
değişti**, ve **L18 güncellenmedi**.

⚠️ **Bugünün DÖRDÜNCÜ belge-ölçüm çelişkisi.** Önceki üçü: *"iki kol"*
(D-176) · ROADMAP §3 (D-178) · L20 (D-180). **Desen artık istisna değil
kural:** bu projede bir belgenin en riskli hâli *yanlış* olması değil,
**eskimiş** olması.

### 4. ⛔⛔ ACİL — DR #14 brief'i obsolet bir soru soruyor

`2026-08-25_five-bottlenecks-radical-redesign_PLAIN.txt` **Darboğaz 1**'i
şöyle tarif ediyor: *"Between 94 and 100 percent of decision events resolve
to DEFECT."*

⇒ **Bu tarif bugünkü fizik için YANLIŞ.** Brief gönderildiyse, DR **var
olmayan bir problemi** çözmeye çalışıyor: uzamsal kafes, devrilme noktası,
yansıma döngüsü — hepsi *"defection tuzağından kaçış"* için.

⇒ **Brief'in Darboğaz 1 bölümü yeniden yazılmalı.** Yeni soru artık
*"nasıl kaçarız"* değil: **"davranış zaten dağılmış — bu dağılım `z`'ye ve
kalıtıma ulaşıyor mu?"**

### 5. ⭐ İddiaya etkisi — beş sınırın en ağırı hafifledi

D-176'dan beri kayıtlı *"en sert saldırı"*: *"ajanlarınız zaten hep aynı
kararı veriyor ⇒ bu bir trait'in kalıtımı değil, bir sayının taşınması."*

⇒ **Bu eleştirinin dayanağı zayıfladı.** Davranış **gerçekten dağılmış**
(%57/%40/%3) ve talep miktarları **sürekli bir aralıkta**.

⚠️ **Ama iddia HENÜZ güçlenmedi.** Kurulması gereken zincir hâlâ eksik:
davranış dağılımının **`z`'ye**, oradan **kalıtıma** ulaştığı **ölçülmedi**.
Bugün gösterilen şey yalnız **ön-koşulun var olduğu**.

### 6. ⚠️ Sınırlar

- **Tek gece, 4 tohum.** Beş gece bitince tekrarlanacak.
- `cooperate` **sözcük etiketidir**; GAP-5/L14 sınırı **aynen geçerli**.
  Güçlü ayak **miktar dağılımıdır**, etiket değil.
- **Kol kırılımı yapılmadı ve yapılmayacak** — o, ön-kayıtlı okumanın işi.
- Nesil eğilimi (%38.5 → %46.6) **havuzlanmış betimleme**, tedavi etkisi
  değil.
- ⛔ **L18'in metni kilitli belgede** (`PREREGISTRATION_3.md`) ⇒ **orada
  değiştirilmiyor**; düzeltme burada ilan ediliyor ve dördüncü ön-kayıta
  taşınıyor. Sonuç raporunda **bu kayda atıfla** okunacak.
