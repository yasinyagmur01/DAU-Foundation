# DAU (Dynamic Agent Universe) — Claude Code Authority Document

## Belge Düzeni (D-001)

| Dosya | İşi | Yazma modu |
|---|---|---|
| `CLAUDE.md` (bu dosya, kök) | geçerli kurallar + açık GAP'ler, kısa | üzerine yazılır |
| `docs/DECISIONS.md` | karar kaydı: ne/ne zaman/neden/**kanıt** | **append-only** |
| `docs/DAU_MASTER_REFERENCE_v20.md` | bilimsel anlatı, formüller, empirik tablo | sürüm sürüm |

Bu dosya Claude Code'un her oturum otomatik yüklediği otorite belgesidir —
**kısa tutulur**, ayrıntı `DECISIONS.md`'ye gider. Çelişki durumunda bu dosya
geçerlidir, ama çelişkiyi açıkça belirt ve kullanıcıya sor — sessizce birini
seçme.

**Kural:** Kanıtı olmayan hiçbir madde "kilitli karar" olarak yazılmaz.
Kilitli her madde bir `D-00X` kaydına işaret etmelidir. (2026-08-09'da
kaynaksız bir kilitli madde bulundu — bkz. `DECISIONS.md` "Bu dosya neden
var".)

## Şu An Neredeyiz (2026-08-09)

- **Branch:** `cursor/per-agent-qlora-adapter-c116`. main'e taşınmadı —
  gerçek diverjans var, ertelendi (**D-013**).
- **Faz:** kod düzeltmeleri. Salt-yazı denetim fazı D-010/011/012 ile kapandı.
- **Sıradaki adım:** `docs/EXECUTION_PLAN.md` → **Adım 1 (GAP-11)**.
- **Son durum:** GAP-1..15 açık; 20 preflight değişmezi kilitli (D-012),
  koda dökülmeyi bekliyor.

**Bu fazın üç kuralı:**
1. Tek konu → tek commit → gerekçeli mesaj → karar varsa D-kaydı.
2. **Her düzeltme, o hatayı yakalayacak testle birlikte gelir.** Yoksa
   N+1'inci düzeltme N'inciyi bozar ve kimse görmez.
3. Koda dokunmadan önce mevcut davranışı teste bağla. Onaysız kod değiştirme.

**Okuma haritası — hangi soruda hangi dosya:**

| Ne zaman | Dosya |
|---|---|
| Her oturum başı | `CLAUDE.md` (otomatik yüklenir) |
| Sıradaki iş ne | `docs/EXECUTION_PLAN.md` |
| "Bunu neden böyle kararlaştırdık?" | `docs/DECISIONS.md`, D-numarasıyla |
| Gate'i kodlarken | `docs/PREFLIGHT_INVARIANTS.md` (D-012, I0.1–I5.4) |
| "Bu dosyanın sessiz yolları neler?" | `docs/RUNPATH_AUDIT.md` (K1–K8) |
| Alet/literatür kararı öncesi | `docs/research/RECONCILIATION.md` |
| Formül · tarihçe · empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` ⚠ 4+ commit geride, v2.4.2 borcu var |

## Axiom

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
- **Tek dosya / tek görev / tek commit:** Her onaylanan adımdan hemen sonra commit.
- **Gate-and-confirm:** Her değişiklik önce analiz edilir, kullanıcı onayı
  alınır, sonra uygulanır. Asla onaysız kod değiştirme.
- **Null/underpowered sonuç meşru bilimsel çıktıdır** — gizlenmez, "kurtarılmaya"
  çalışılmaz.
- **Read-only audit, implementasyondan önce gelir.** Yeni bir faza girmeden
  önce ilgili dosyalar tam okunur, iddia doğrulanır — hafızaya/dokümana
  güvenilmez.

## Kilitli Kararlar (yeniden tartışılmaz)

- Generation-end batch micro-QLoRA ≫ per-event online learning (literatür +
  8GB VRAM kararlılığı ile doğrulandı, bkz. `docs/research/2026-08-08~_per-agent-lora-serving.md` §2).
- Dual-channel mimari (sembolik vault ayrı, parametrik LoRA ayrı) — 2026
  sanayi/akademi konsensüsüyle örtüşüyor (bkz. `docs/research/2026-08-08~_per-agent-lora-serving.md` §4).
- Per-agent adapter disk izolasyonu (`dau_runs/adapters/{agent_id}/`) —
  Punica deseni, tek GPU/8GB VRAM için doğru seçim.
- `heal_drift` çift-uygulama riski KAPANDI: `meta_observer._evaluator_healed_domains`
  skip-set ile dedup edildi, `test_drift.py` bunu kanıtlıyor.
- Precision-PE v2.4 (rolling history + VAR_REF=1/12) doygunluk sorununu
  düzeltti (saturation_rate=0.0025), kalibrasyon doğrulandı.
- NLI contradiction threshold: `NLI_CONTRADICTION_THRESHOLD=0.60`,
  `cross-encoder/nli-deberta-v3-small`.
- İstatistik eşikleri: N≥15, K≥5 (DIVERSITY_MIN_UNIQUE), n_eff≥12 —
  ✅ provenans bulundu: `2026-08-08~_per-agent-lora-serving.md` §5.
- **Çok-nesilli C′ birincil uç noktası = doğum-drift** (D-002). Gen2 PE +
  gen2 davranışsal = ön-kayıtlı ikincil. Testler: Kruskal-Wallis (doğum
  drift magnitude, 3 grup), Fisher-Freeman-Halton (transfer aday sayıları),
  paired t-test/Wilcoxon (destekleyici — ✅ provenansı 08-08~ §5'te,
  ayrıca protocol-c-eval bunları birincil test olarak öneriyor + travma
  için **McNemar**). ⚠ Kruskal-Wallis + FFH provenansı **9 brief'in
  hiçbirinde yok** — arama bitti (D-010). Türetilmiş kabul edilir, kilitli
  değil; 3-grup tasarımına uygun oldukları için korunuyorlar.
- **F_agent transfer kapısı korunur** + `f_agent=None` duyarlılık kolu
  (D-003). Kapı kaldırılmaz: aksiyom içeri trait enjeksiyonunu yasaklar,
  dışarıdan seçilim baskısını değil.

## Açık Gap'ler (öncelik sırasıyla — doğrulanmadan "kapalı" sayılmaz)

### GAP-1 (en kritik): LoRA default-off → eğitim hiç çalışmıyor — **DOĞRULANDI**
Read-only denetim (2026-08-09) sonucu: `run_cprime_multigen.py`
`DAU_LORA_ENABLED`'ı **hiçbir yerde set etmiyor**; yalnızca satır 692'de
JSON'a raporlamak için okuyor. CLI'da flag yok. `run_protocol_c_prime.py`
da zorlamıyor. Gate üç katmanlı ve hepsi kapalı:
`_train_adapter` (run_protocol_c_prime.py:697) · `run_micro_train_
preference_step` (lora_update.py:369) · `lora_update` (lora_update.py:404).

**Sonucu sanılandan sert:** `run_gen1_arm_lineage`'de `arm` değişkeni
davranışa **tek bir yerde** dokunuyor — `_train_adapter` çağrısı
(satır 429-443). Niş yalnızca `seed`'den geliyor (`_seed_niche`), `agent_id`
prompt'a girmiyor, hafıza deposu her soy için taze. Eğitim no-op olunca
`lived`/`null`/`shuffle` üç kol değil, **aynı deneyin üç kopyası**; strict
seed lock ile muhtemelen bit-identik. Böyle bir koşumdan çıkacak p-değeri
bilimsel sonuç değil, tautolojidir. `null ΔPE=0.000 clean` metriği bu yüzden
ikircikli: "alet deterministik" de demek olabilir, "hiçbir kol eğitilmedi" de.

**Fix kararı — D-004** (onaylandı, henüz uygulanmadı): env kapalıyken runner
**hard fail** etsin + explicit `--lora/--no-lora` CLI flag'i + her results
JSON'una alet kimliği (backend, model id, quantization, adapter durumu,
sampling parametreleri). İlke: bir koşum kendi konfigürasyonunu inkâr
edememeli.

### GAP-2: Silent train failure — kısmen açık
Doğrulandı, ama CLAUDE.md'nin önceki tarifi olduğundan geniş:
- **Açık:** `build_pe_ranked_pairs` exception'ı hâlâ sessizce yutuluyor —
  `run_protocol_c_prime.py:723-724`, bare `except Exception: return (0,0)`,
  log yok.
- **Kapalı:** train exception'ı (satır 742-748) ve `trained=False` durumu
  (satır 751-757) artık `[WARN]` basıyor.

### GAP-3: Gen2 event-1 somatic scale boşluğu
`apply_inherited_somatic_scale` sadece `delta_log` dolu olunca çalışıyor;
heir'ler boş `delta_log` ile doğuyor, ilk karar ata verisini kaçırıyor. Kısa
PE pencereli gen2 ölçümleri kirlenmiş olabilir.

### GAP-4: Memory-vault ↔ LoRA senkron kopukluğu (araştırmadan çıktı, kodda doğrulanmadı)
Ebbinghaus decay ile sembolik kasadan silinen bir anının yarattığı drift,
LoRA ağırlıklarında kalıcı kalabilir. Sistem "unuttum" derken davranışsal
olarak hâlâ o anıyı taşıyor olabilir. **Kodda gerçek bir risk mi, yoksa
teorik mi — doğrulanmalı.**

### GAP-5: SYSTEM_PROMPT lexicon priming (metodolojik soru işareti, bug değil)
`graph.py`'deki SYSTEM_PROMPT, `decision_to_outcome`'ın eşlediği kelimelere
(extract/cooperate/...) doğru dilsel çıktıyı yönlendiriyor olabilir — bu
"serbest dilsel emergence" iddiasını ne kadar zedeler, tartışılmalı.

**Provenans (D-010):** iki bağımsız denetim aynı şeyi işaret etmiş.
`v1-kritik-sistem-audit` S1: "ajanın beklentisi kendi kognitif süreçleriyle
değil, `f(dominant_load_domain)` ile tasarımcı şablonundan atanır → PE,
tasarımcının şablonu ile ajanın eylemi arasındaki mesafeyi ölçer."
`minilm-meta-ab-audit` aynı maddeyi S1 olarak sıralıyor ve endojen
`expected_outcome` mikro-pilotu öneriyor. GAP-5 teorik bir kaygı değil,
iki kez bağımsız tespit edilmiş bir ölçüm sapması.

### GAP-6: Magic number kalıntıları + adapter hot-swap CUDA temizliği
Temizlik (düşük öncelik): `time.sleep(10)` (run_protocol_c_prime.py), bare
`0.5` (shuffle_preference_pairs), default `k: int = 5` (retrieval.py).

**Önceliği yükseltilen madde:** `2026-08-08~_per-agent-lora-serving.md` §1,
adapter hot-swap'te **CUDA akış senkronizasyonu + gradyan önbellek
temizliğini izolasyon doğruluğu şartı** olarak sayıyor — sadece temizlik
değil. `local_llm.py`'de `empty_cache` / `synchronize` **yok**, yalnızca
`optimizer.zero_grad()` var. `f25b0ef` disk izolasyonunu çözdü; bellek
tarafındaki bu şart doğrulanmadı.

### GAP-8 (en kritik ikinci): DPO sinyal gücünü düşüren beş ayar
Arşiv mutabakatının (D-010) en tutarlı bulgusu: **beş bağımsız brief
tavsiyesi aynı yöne işaret ediyor, beşi de kısmen veya hiç uygulanmamış.**
Tek tek küçük, birlikte sinyali katlayarak zayıflatıyorlar.

| | Tavsiye | Kod | Kaynak |
|---|---|---|---|
| A1 | gradient **accumulation** | yok — `local_llm.py:610-627` her çift için ayrı `zero_grad()`+step ⇒ efektif batch=1. Uygulanan: gradient *checkpointing* (bellek tekniği, farklı şey) | 08-08~ §2 |
| A2 | `seq_len` 512 | `DPO_MAX_SEQUENCE_TOKENS = 256` (128'den yükseltilmiş, yarı yol) | cprime-teshis H-B1 |
| A3 | 3 epoch | `DPO_EPOCHS = 1` | cprime-teshis H-B2 |
| A4 | %10 yüksek-somatik **replay** (`F_agent ≥ 0.7`), +0.3 GiB | kodda hiç yok | cprime-teshis H-A2 |
| A5 | **SNR eşiği `PE ≥ 0.40`**; `PE < 0.15` sinyalleri ön-eğitilmiş ağırlık gürültüsünde kaybolur | `build_pe_ranked_pairs` yalnızca `PE_RANK_MIN_GAP = 1e-6` fark arıyor, **mutlak PE eşiği yok** ⇒ eğitim seti gürültü çiftleriyle dolabilir | sentetik-kognisyon §1.2 |

A5 muhtemelen en kritik olanı: tercih çiftleri PE **farkına** göre
seçiliyor ama PE **büyüklüğüne** göre filtrelenmiyor.

A1 ve A4 `fark edilmemiş kayma`; A2/A3 kısmi sapma. `BATCH_SIZE=2` OOM
verdiği için batching kapatılmış — ama accumulation OOM vermez
(micro-batch 1 kalır, step N mikro-adımda bir atılır); iki teknik
karıştırılmış görünüyor.

⚠ **Alet değişikliği** — D-005 ile aynı pencerede, pre-reg kilitlenmeden
önce karara bağlanmalı.

### GAP-9: N=15 güç analizine göre baştan yetersizdi
`protocol-c-metacognition-eval` güç analizi: `σ_PE = 0.256`, eşleştirilmiş
tasarımda `d_z ≈ 1.5·d`. Gerekli çift sayısı **d=0.5 → 16 · d=0.4 → 24 ·
d=0.3 → 41 · d=0.2 → 90**; Protocol C için **N=40-50** öneriliyor.
`sentetik-kognisyon` §1.6: "d=0.5 için minimum N=15-20".

Yani N=15 **yalnızca d ≥ 0.5 varsayımı altında** geçerliydi. DAU'nun
gözlediği etki: `lived +0.008` vs `shuffle +0.019`, σ≈0.256 ⇒ **d ≈ 0.04**.
Bu büyüklük için yüzlerce çift gerekir.

**`SAMPLE_N15_UNDERPOWERED` sürpriz değildi — güç analizi onu önceden
söylüyordu.** Çok-nesilli pre-reg'de N varsayılan olarak 15 alınamaz:
ya beklenen etki büyüklüğü açıkça gerekçelendirilip N ona göre hesaplanır,
ya da D-002'nin yüksek güçlü uç noktası (doğum-drift, tamsayı sayımlar)
kullanılır — ki bu D-002'yi bağımsız olarak destekliyor.

### GAP-11 (canlı hata): Shuffle kolu process'ler arası reproducible değil
`_seed_from_agent_id` (`run_protocol_c_prime.py:567-573`) trailing segmenti
int'e çevirir, olmazsa `abs(hash(agent_id)) % 2**31` döner. Multigen
`agent_id`'si `cprime-{arm}-{seed}-g1` → `int("g1")` ValueError → hash
fallback. `PYTHONHASHSEED` **hiçbir yerde set edilmiyor**.

Ampirik kanıt — aynı `agent_id`, üç ayrı process:
`419643228` · `227385495` · `229629477`.

**Kök neden:** `cd64cc8` multigen `agent_id`'ye `-g1` ekledi; Protocol C′'de
`cprime-shuffle-2001` → `int("2001")` çalışıyordu. Docstring hâlâ eski
formatı yazıyor. Uzaktaki dosyada sessizce kırıldı.

**Etki:** üç koldan biri replay garantisinin dışında. Düzeltme tek satır,
ama determinizm assertion'ı ile birlikte gelmeli.

### GAP-12: Gen2 seed-locked değil — ve asimetrik
`run_gen1_arm_lineage` phase-1 (`:411`) ve phase-2 (`:446`) `_lock_seeds`
çağırıyor; `run_gen2_measure` çağırmıyor.

Asıl sorun asimetri: lived/shuffle eğitim yapıyor (LoRA reset + DPO, torch
RNG tüketiyor), null yapmıyor → üç varis gen2'ye **farklı RNG durumlarıyla**
giriyor. Kol farkı ile RNG farkı karışıyor.

### GAP-13: Multigen'de precision audit hiç yapılmıyor
`ArmResult`'ın `saturation_rate` / `pi_n_distinct` / `n_pe_events_audited` /
`n_saturated` / `pi_values` alanları `run_cprime_multigen.py`'de **hiç
doldurulmuyor** → JSON'a default sıfırlar gidiyor.

v2.4.1'de v3 smoke'un tüm anlamı bu alanlardı. Multigen koşumunda alet
sağlık kontrolü yok; doygunluk geri gelse haberimiz olmaz.

### GAP-14: PPR (ADIM 4) koşum yolunda inert
`memory_edges` tablosunu dolduran tek yer `store.write_edge`; onu çağıran
tek yer `consolidation.run_consolidation`; onu çağıran `memory_bridge.py:113`
sarmalayıcısını **hiç kimse çağırmıyor** (testler hariç).

Sonuç: tablo boş → `compute_ppr_scores` boş graf → `{seed_domain: 1.0}`
sabit dönüyor:
```
memory_score = 0.21·recency + 0.28·magnitude + 0.21·domain_match + 0.30·ppr
             → fiilen 0.21·recency + 0.28·magnitude + 0.51·domain_match
```
PPR bir çağrışım motoru değil, domain_match'in ağırlığını büyüten sabit.
⚠ **Master reference §6 ve §19 ADIM 4'ü uygulanmış entegrasyon olarak
sunuyor** — v2.4.2'de düzeltilmeli. Karar gerekiyor: consolidation'ı koşum
yoluna bağla mı, yoksa "inert" diye belgele mi?

### GAP-15: `TEMPERATURE` import anında donuyor
`run_protocol_c_prime.py:73` `DAU_LLM_TEMPERATURE`'ı import anında okuyor;
`_lock_seeds` her çağrıda env'i o değerle geri yazıyor (`:460`). Import'tan
sonra env değiştirmek sessizce etkisiz.

### GAP-10: Süresi dolmuş ölçüm ertelemeleri (v1 denetimlerinden)
- **`W_SEM = 0.0`** — ChromaDB vektörü skorlamaya girmiyor, sadece depo.
  `v1-kritik-sistem-audit` "**baseline kilitlenince** `W_SEM = 0.3–0.4`
  yapılmalı" demiş. Protocol C baseline'ı **artık kilitli** — erteleme
  koşulu gerçekleşti, kimse geri dönmedi.
- **Negation kural sarmalayıcı yok** — `minilm-meta-ab-audit`
  SELECTIVE_FIX #3 `semantic_similarity.py`'ye MiniLM cosine öncesi
  olumsuzluk eki denetimi (not/never/no/refuse) istiyor. Kodda yok. NLI
  yalnızca tercih çiftlerinde, **PE sensörünün kendisinde değil**.
- **Asimetrik spillover matrisi** — `daerm-trauma-magnitude` skaler
  `S=0.20` yerine domain-özgü matris öneriyor
  (`S_res→unc=0.35`, `S_soc→res=0.10`…). Kod skaler kullanıyor
  (`CROSS_AXIS_SPILLOVER = 0.20`). Bilinçli mi bilinmiyor.

### GAP-7 (D-005, henüz kilitlenmedi): Backend aksiyomu test edemeyen konfigürasyon
`DAU_LLM_BACKEND=groq` default. Ama Kanal 2 (per-agent adapter,
`switch_adapter`, DPO) ağırlık erişimi ister — **Groq'ta ontolojik olarak
imkânsız**. Yani projenin merkezî iddiasının test edilemediği konfigürasyon,
varsayılan konfigürasyon. Mimari zaten %90 lokal (MiniLM, DeBERTa NLI,
Chroma, SQLite, PPR); uzak olan tek bileşen karar veren LLM.

Ek riskler:
- **Ön-kayıt bütünlüğü:** uzak endpoint sahibi olmadığın bir alettir;
  sağlayıcı model sürümünü/quantization'ı habersiz değiştirirse ön-kayıt
  **geriye dönük** geçersiz olur. `sha256(DAU_LLM_SEED:prompt)` + strict
  CUDA lock makinesi yalnızca lokalde anlamlı.
- **Kayıtsız alet uyumsuzluğu:** Protocol C = Groq `llama-3.1-8b-instant`;
  C′ = lokal Llama-3.1-8B 4-bit NF4. Farklı aletler, ama belgede backend
  farkına dair **hiçbir alet etiketi yok** (§10b etiketleri yalnızca ADIM 5
  precision'a dair).
- Groq'un kalan tek işlevi (büyük-N frozen koşum) zaten anti-roadmap'te
  yasak; hızlı iterasyon ihtiyacını `DAU_MULTIGEN_MOCK_LLM=1` daha iyi
  karşılıyor.

Karşı maliyet: 8GB VRAM tavanı (çok-ajanlı eşzamanlılık). Punica adapter
takası bunu çözüyor — bedeli bellek değil, zaman.

**Zamanlama uyarısı:** backend default'unu değiştirmek aleti değiştirmektir.
Çok-nesilli pre-reg **henüz yazılmadı**, yani pencere şu an açık; pre-reg
kilitlendiği an bu değişiklik post-hoc olur ve kendi kuralını çiğner.

Önerilen (henüz kilitlenmedi): deney runner'larının default'u `local`;
`groq` "legacy/keşif" etiketiyle kalsın (Protocol C provenance'ı için
gerekli); her results JSON'una **alet kimliği** yazılsın — backend, model
id, quantization, `DAU_LORA_ENABLED`, adapter durumu, sampling parametreleri.

## Kapatılmış/Geçersiz Sayılan Geçmiş Bulgular (yeniden açılmaz)

- **Sahte eğitim bug'u** (`e4c026b` öncesi): `lora_B=0`, gradyan adımı hiç
  atılmıyordu. Düzeltildi, `lora_B` abs-sum kontrolü regresyon testinde var.
- **Adapter izolasyon sızıntısı** (`f25b0ef` öncesi): peft tüm aktif
  adaptörleri her ajanın dizinine yazıyordu, null kol lived kolun eğitimini
  miras alıyordu. Düzeltildi, `test_no_dead_adapter_root_reference` ile korunuyor.
- Bu iki düzeltme öncesi üretilen **tüm C′ sonuçları geçersizdir** — kurtarılmaya
  çalışılmaz, yeniden çalıştırılır.

## Dosya Konumu Notları

- `TransferCandidate` → `dau/foundation/generation.py` (generation/ değil).
  Doğrulandı: `generation.py:55`.
- `_train_adapter` → `dau/diagnostics/run_protocol_c_prime.py:684`
  (**`lora_update.py`'de değil** — multigen oradan import ediyor).
- Multigen orkestrasyon: `dau/diagnostics/run_cprime_multigen.py` (792 satır)
  + `dau/diagnostics/tests/test_cprime_multigen.py` (226 satır) — mevcut,
  LoRA gate'i doğrulandı ve kapalı (GAP-1).
- `CLAUDE.md` **repo kökünde** durur, `docs/`'a taşınamaz — Claude Code
  onu yalnızca kökten otomatik yükler.
- Deep Research arşivi: `docs/research/` (ham brief'ler + `RECONCILIATION.md`).
  Eski kök `RESEARCH_BRIEF_v1.md` kaldırıldı — içeriği mutabakat dosyasına
  devredildi (D-008).

## Master Reference ↔ Kod Gecikmesi (2026-08-09 denetimi)

`docs/DAU_MASTER_REFERENCE_v20.md` (v2.4.1) koddan **4 commit geride**.
`04adbdc` yalnızca docs dosyalarına dokunmuş, içeriği bir gün önceki koda
göre güncellenmemiş:

| Commit | Kodda | Master reference'ta |
|---|---|---|
| `8c5344b` heal_drift dedup | ✅ | ❌ (§8 değişmemiş) |
| `18fb01e` NLI'yi üretim yoluna bağla | ✅ | ❌ — **§21 tersini yazıyor** |
| `cd64cc8` multigen orkestrasyon | ✅ | ❌ hiç geçmiyor |
| `075576e` STREAM_NODES 4→5 | ✅ | ❌ |

**§21 aktif olarak yanlış:** tablo `DAU_NLI_FILTER_ENABLED` için "yaşam-PE
path'te ranking NLI kullanmaz" diyor, ama `lora_update.py:297`
`build_pe_ranked_pairs` içinde `is_genuine_polarity_pair` çağırıyor
(`18fb01e` bunu bilerek bağladı).

Ayrıca belge beş yerde "çok-nesilli pre-reg henüz yazılmadı, sıradaki
oturumun İLK görevi" diyor — ama orkestrasyon kodu bir gün önce yazılmış.
**Kod pre-registration'ın önüne geçmiş.** Henüz hiçbir şey koşulmadığı için
kural ihlali değil, ama sıra bozuk ve belge bunu bilmiyor.

Düzeltme, GAP-1 fix + backend kararı sonrasında tek bir temiz `v2.4.2`
girdisiyle yapılacak (iki kez yazmamak için).

## Araştırma Kanalı: Gemini Deep Research

Mimari kararlarda sıkışıldığında veya yeni bir katman/ADIM'a girmeden önce
geniş literatür + teknoloji taraması **Gemini Deep Research** ile yapılır.
Yasin detaylı prompt yazar, çıktı repo köküne `RESEARCH_BRIEF_*.md` olarak
girer.

Bu bir yedek değil, karar sürecinin bir organı. İki işlevi var:

1. **İleri bakış** — yeni katman/teknoloji seçiminden önce literatür
   haritası (örn. `2026-08-08~_per-agent-lora-serving.md`: generation-end QLoRA ≫
   per-event online öğrenme; dual-channel mimari konsensüsü).
2. **Geriye dönük tutarlılık denetimi** — Layer 5 (özbilinç) araştırılırken
   önceki 4 katmanın iç tutarlılığı dışarıdan bağımsız olarak doğrulandı.
   Yeni bir katmanı araştırmak, eskilerin denetimi anlamına da gelir.

**Hangi soruyu kim cevaplar (D-007):**

| Soru tipi | Kim |
|---|---|
| "Biz neye karar vermiştik / neden böyle yaptık" | git geçmişi + Yasin; Claude Code kazar |
| "Kod gerçekten ne yapıyor" | Claude Code, read-only denetim |
| "Literatürde X mi Y mi savunulabilir" | Gemini Deep Research |
| "Bu deneyde X mi Y mi olsun" | Yasin (DR + Claude Code girdi verir) |

Provenans sorusu (**"biz ne karar vermiştik"**) Deep Research'e sorulmaz —
DR'nin commit geçmişine erişimi yok, sorulursa makul görünen ama kaynaksız
bir metin üretir ve kaynaksız satır sayısı artar.

**Arşiv mutabakatı (D-006):** Geçmiş brief'ler repo köküne
`RESEARCH_BRIEF_v*.md` olarak **dosya** halinde girer (sohbete
yapıştırılmaz). Her biri için Claude Code bir mutabakat tablosu üretir:
brief ne diyor / kod ne yapıyor / karar ∈ {bilinçli sapma · fark
edilmemiş kayma · uyumlu · brief yanılmış}. Bilinçli sapmalar
`DECISIONS.md`'ye gerekçesiyle girer, kaymalar buraya GAP olur.

**Claude Code'un buradaki rolü:**

- Açık uçlu literatür sorusu geldiğinde kendi kendine tahmin yürütmez —
  "bu bir Gemini Deep Research sorusu" der ve **kopyala-yapıştıra hazır,
  detaylı bir araştırma prompt'u üretir**.
- Gelen brief'i **iddia olarak değil, hipotez olarak** alır. Brief'teki her
  iddia DAU kod tabanında ayrıca doğrulanır; doğrulanmadan bu dosyaya
  "kilitli karar" olarak yazılmaz.
- Brief ile kodun çeliştiği yeri sessizce seçmez — çelişkiyi raporlar.

## Roller

- Yasin: yön, onay, yerel test çalıştırma, Claude Code ↔ Cursor arası köprü
  (ikisi birbirine bağlı değil, prompt'lar elle taşınır).
- Claude Code: triyaj, dosya bazlı implementasyon (onay sonrası), test
  çalıştırma, commit, master reference güncellemesi, Cursor'a devredilecek
  işleri tespit edip hazır prompt üretmek.
- Cursor: sadece Claude Code'un "CURSOR'A DEVRET" etiketiyle işaretlediği
  düşük riskli, mekanik işler. Kendi başına mimari karar almaz.
- Açık uçlu araştırma Claude Code'un işi değil — Gemini Deep Research'e
  yönlendirilir (bkz. "Araştırma Kanalı" bölümü).

## Cursor'a Devretme Kuralı (Claude Code her adımda bunu uygulamalı)

Yasin'in Cursor limiti var, boşa harcanmasın isteniyor. Claude Code, her
görev/adımda önce şunu değerlendirir: **bu iş karar mı gerektiriyor, yoksa
mekanik mi?**

**Cursor'a devredilebilir (mekanik, düşük risk, tersine çevrilebilir):**
- Magic number → UPPER_CASE constants taşıma (davranış değişmiyor)
- Zaten karara bağlanmış DOC_MISMATCH düzeltmeleri (hangi taraf doğru
  biliniyor, sadece diğerini ona uydurma)
- TEST_GAP doldurma (mevcut davranışı test altına alma, davranış değişmiyor)
- Basit performans/temizlik ekleri (örn. `torch.cuda.empty_cache()`)
- Tek dosya, tek fonksiyon, açık ve dar kapsamlı mekanik değişiklikler

**Claude Code'da kalır (karar/wiring/axiom'a değiyor):**
- Herhangi bir GAP (GAP-1..6) — tasarım kararı veya wiring değişikliği içeriyor
- İki karar arasında seçim gerektiren her şey (örn. "fail loud mu fail
  silent mi", "ata verisi ilk kararda nasıl kullanılsın")
- `constraints.py`'deki eşik/formül değerlerinin kendisinin değişmesi
  (taşınması değil, değerinin değişmesi — bu pre-registration'ı bozar)
- Multi-gen orchestration, LoRA gate, memory-vault senkronizasyonu gibi
  axiom'un kalbine değen her şey

**Nasıl uygulanır:** Claude Code bir işi Cursor'a uygun görürse, kod
değişikliğine kendi girişmez. Bunun yerine Yasin'e şunu söyler:
"Bu iş Cursor'a uygun — [1 cümle gerekçe]. Şu prompt'u Cursor'a ver:"
ve ardından kopyala-yapıştıra hazır, dar kapsamlı, davranış-değiştirmeyeceğini
açıkça belirten bir prompt üretir. Cursor'un çıktısı geri geldiğinde Claude
Code onu test sonuçlarıyla doğrular, sonra commit eder.
