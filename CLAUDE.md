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

## Şu An Neredeyiz (2026-08-10)

- **Branch:** `cursor/per-agent-qlora-adapter-c116`. main'e taşınmadı —
  gerçek diverjans var, ertelendi (**D-013**).
- **Faz:** **Faz 2 — kararların uygulanması.** Kod düzeltme fazı (Adım 1–7)
  ve karar kapısı (D-018..D-022) kapandı.
- **SIRADAKİ İŞ:** `docs/EXECUTION_PLAN.md` **§F** → **U2** (NF4 +
  `double_quant` açıkça, D-020). Sıra: `U1 ✅ → U2 → U3 → U7 → U4 → U5 → U6`.
- **U1 bitti** (`7adb01d`): backend varsayılanı `local`. Yan ürün **D-023** —
  tanınmayan `DAU_LLM_BACKEND` değeri artık `ValueError`; varsayılanı
  çevirmek, eskiden zararsız olan sessiz fallback'i zararlı hale getirdi
  (`grok` yazım hatası eskiden `groq`'a, artık `local`'a düşerdi ve koşum
  kendini `backend=local` diye doğru raporlardı). Boş/unset hâlâ varsayılan
  (GAP-15 emsali). Suite 270 passed.
- **Biten:** Adım 1–5 (GAP-11 `8cf2ac0`, GAP-12 `ab8966c`, GAP-15
  `ab30f9c`, GAP-13 `090a5bc`, GAP-1 `afbb552`) · Adım 6 **kısmen**
  (`preflight.py`, **24 değişmezin 17'si**: `75239d1` faz 0 · `0b48f93`
  faz 3 · `30c80da` faz 4/5 · `b8c3e69` faz 2) · Adım 7 ✅ gate ateşlendi
  (flagsız koşum `exit=1`; `--lora --mock-llm` I2.1/I3.2/I5.1/I5.4
  FLAG'leriyle geçti — D-017).
- **Karar kapısının çıktısı — hepsi kilitli, hiçbiri henüz kodda:**
  **D-018** backend `local` (groq legacy kalır) · **D-019** Qwen-2.5-7B
  ölçülmeden kilitlenmez, **kabul kriteri ön-kayıtlı** · **D-020** NF4 +
  `double_quant` açıkça yazılır · **D-021** GAP-8 bölündü (A1+A5 kilitli,
  A2/A3/A4 VRAM ölçümüne bağlı) · **D-022** consolidation deney yoluna
  bağlanır, I5.1 pilota kadar FLAG.
- **Yön:** nesil zinciri 2 ile sınırlı değil, hedef **N nesil** (**D-014**).
- **Gate'in kendi bulduğu:** I5.1 → GAP-14 (PPR atıl), I5.4 → GAP-3.
  Denetimle bulunmuş iki maddeyi koşum artık kendisi söylüyor.

## Yeni Oturum Protokolü (bu bölüm bağlayıcıdır)

**1. Nereden başla.** Bu dosyanın "SIRADAKİ İŞ" satırı → `EXECUTION_PLAN.md`
§F'de o U-adımının tablosu → gerekçesini merak edersen `DECISIONS.md`'de
ilgili D-kaydı. Üçünü okumadan koda dokunma.

**2. Önce doğrula, sonra dokun.** Plandaki satır numaraları yazıldıkları
gün doğruydu; **yeniden oku**. Bu projede belge iki kez yanıldı: GAP-11
(docstring eski `agent_id` formatını yazıyordu) ve GAP-14 ("hiç kimse
çağırmıyor" — `graph.py:1426` çağırıyordu). Hafızaya ve belgeye değil,
dosyaya güven.

**3. Gate-and-confirm.** Analiz → öneri → **Yasin'in onayı** → uygulama.
Analiz şunları içerir: ne bulundu (kanıtla), ne değişecek, hangi test
gelecek, ne riskli. Onaysız kod değişmez.

**4. Her düzeltme testiyle gelir, test mutasyon kontrolünden geçer.**
Düzeltmeyi geçici geri al → test kırılmalı → geri koy. Kırılmıyorsa test o
hatayı yakalamıyordur.

**5. Commit ritmi.** Tek konu → tam suite (`python -m pytest -q`) →
gerekçeli commit. Suite yeşil değilse commit yok.

**6. Ne nereye yazılır:**

| Ne | Nereye | Mod |
|---|---|---|
| Karar, ölçüm sonucu, gerekçe, reddedilen alternatif | `docs/DECISIONS.md` (**D-kaydı**) | **append-only**, asla düzenleme |
| "Şu an neredeyiz", sıradaki iş, açık GAP | `CLAUDE.md` (bu dosya) | üzerine yazılır, **kısa tutulur** |
| Adım ayrıntısı, dur-kontrol, adım durumu | `docs/EXECUTION_PLAN.md` | adım bitince ✅ + commit hash |
| Formül, tarihçe, empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` | sürüm sürüm (v2.4.2 borcu var) |

**7. Neye sadık kal.** 5 Değiştirilemez Yasak · Değiştirilemez Süreç
Kuralları · sessiz fallback yasağı (belirlenemeyen durum `SystemExit`/
`ValueError`/`[WARN]` ile gürültü çıkarır, varsayılana düşmez) ·
`constraints.py` eşik **değerleri yalnızca D-kaydıyla** değişir.

**8. Ön-kayıt henüz yazılmadı** → alet değişikliği hâlâ meşru, ama her biri
D-kaydı ister. Pre-reg kilitlendiği an bu pencere kapanır ve aynı değişiklik
post-hoc olur.

**9. Çelişki görürsen sessizce seçme.** Belge ile kod, ya da iki belge
çelişiyorsa: raporla, kullanıcıya sor. (Bu oturumda üç kez oldu: değişmez
sayısı 20↔24, saturation eşiği 0.30↔0.05, GAP-14'ün tarifi.)

**Okuma haritası — hangi soruda hangi dosya:**

| Ne zaman | Dosya |
|---|---|
| Her oturum başı | `CLAUDE.md` (otomatik yüklenir) |
| **Sıradaki iş ne** | `docs/EXECUTION_PLAN.md` **§F (Faz 2, U1–U7)** |
| "Bunu neden böyle kararlaştırdık?" | `docs/DECISIONS.md`, D-numarasıyla |
| Gate'i kodlarken | `docs/PREFLIGHT_INVARIANTS.md` (D-012, I0.1–I5.4 — **24 madde**, "20" yanlıştı) + `dau/diagnostics/preflight.py` |
| "Bu dosyanın sessiz yolları neler?" | `docs/RUNPATH_AUDIT.md` (K1–K8) |
| Alet/literatür kararı öncesi | `docs/research/RECONCILIATION.md` |
| Formül · tarihçe · empirik tablo | `docs/DAU_MASTER_REFERENCE_v20.md` ⚠ geride, v2.4.2 borcu var |

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

## Açık Gap'ler (doğrulanmadan "kapalı" sayılmaz)

**Kapanmışlar — yeniden açılmaz, kanıtı commit'te:**

| GAP | Nasıl kapandı |
|---|---|
| GAP-1 | LoRA kapısı + alet kimliği (D-004, `afbb552`); I0.1/I0.2 olarak gate'e bağlandı (`75239d1`) |
| GAP-7 | Backend `local` kilitlendi — **D-018** |
| GAP-11 | Shuffle seed process'ler arası deterministik (`8cf2ac0`) |
| GAP-12 | Gen2 + transfer öncesi RNG kilidi (`ab8966c`); I4.2 olarak gate'te (`30c80da`) |
| GAP-13 | Precision audit gen1 **ve** gen2'de dolduruluyor (`090a5bc`); I3.2 gate'te |
| GAP-14 | Consolidation deney yoluna bağlanacak — **D-022** (uygulama U6) |
| GAP-15 | `TEMPERATURE` çağrı anında okunuyor (`ab30f9c`) |
| GAP-16 (D-016) | Quantization NF4 + double_quant — **D-020** (uygulama U2) |

⚠ **GAP-14'ün eski tarifi yanlıştı ve düzeltildi.** "Sarmalayıcıyı hiç kimse
çağırmıyor" deniyordu; `graph.py:1426` çağırıyor. Consolidation **ölü kod
değil, yanlış yolda** — demo yolu çağırıyor, deney yolu çağırmıyor. Bunun
sonucu sanılandan geniş: deney yolunda **unutma da hiç çalışmamış**, yani
gen2'ye giden miras malzemesi olduğundan farklı ve **birincil uç noktaya**
(doğum-drift, D-002) dokunuyor. Ayrıntı: **D-022**.

**GAP-8 bölündü (D-021):** A1 (gradient accumulation) ve A5 (mutlak PE / SNR
filtresi) **kilitli** — uygulama U4 ve U5. A2 (`seq_len` 512), A3 (3 epoch),
A4 (%10 somatik replay) **VRAM ölçümüne bağlı** — U3'ten sonra, U7'de karara
bağlanacak. A5'in eşiği (`0.40`) kilitli **değil**: mekanizma şimdi, değer
pilottan sonra kalibre edilir.

**Hâlâ açık olanlar:**

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

~~`LLM_BACKEND_*` sabitleri iki dosyada~~ ✅ **kapandı `9ce5269`** (Cursor,
2026-08-10): sabitler + mesaj + çözümleyici gövdesi `llm_backend.py`'de tek
yerde, `graph._resolve_llm_backend` ince alias. Bekçi testi eşitlik değil
**kimlik** iddia ediyor (kısa string'ler intern edilir; tuple edilmez).
`get_backend`'in hâlâ çağıranı yok — silinmedi, kapsam dışıydı.

**Önceliği yükseltilen madde:** `2026-08-08~_per-agent-lora-serving.md` §1,
adapter hot-swap'te **CUDA akış senkronizasyonu + gradyan önbellek
temizliğini izolasyon doğruluğu şartı** olarak sayıyor — sadece temizlik
değil. `local_llm.py`'de `empty_cache` / `synchronize` **yok**, yalnızca
`optimizer.zero_grad()` var. `f25b0ef` disk izolasyonunu çözdü; bellek
tarafındaki bu şart doğrulanmadı.

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
- `_train_adapter` → `dau/diagnostics/run_protocol_c_prime.py:726`
  (**`lora_update.py`'de değil** — multigen oradan import ediyor).
- Multigen orkestrasyon: `dau/diagnostics/run_cprime_multigen.py` (~1086
  satır) + `dau/diagnostics/tests/test_cprime_multigen.py` (~805 satır).
- **Faz 2'de en çok dokunulacak dosyalar:** `dau/foundation/local_llm.py`
  (U2 quantization `build_load_kwargs:99`, U4 DPO döngüsü `:659–702`) ·
  `dau/foundation/lora_update.py` (U5, `build_pe_ranked_pairs:286`) ·
  `dau/foundation/llm_backend.py:18` + `dau/foundation/graph.py:293` (U1) ·
  `run_cprime_multigen.run_lineage:669` (U6).
- Gate altyapısı (Adım 6'da yazıldı): `dau/diagnostics/preflight.py` (~805
  satır, I0.x/I2.x/I3.x/I4.2/I5.x) + `dau/diagnostics/tool_identity.py`
  (~228 satır, LoRA kapısı + alet kimliği).
- ⚠ **Satır numaraları kayar.** Bu bölüm 2026-08-10'da doğrulandı; her
  oturumda `grep` ile teyit et, güvenme.
- `CLAUDE.md` **repo kökünde** durur, `docs/`'a taşınamaz — Claude Code
  onu yalnızca kökten otomatik yükler.
- Deep Research arşivi: `docs/research/` (ham brief'ler + `RECONCILIATION.md`).
  Eski kök `RESEARCH_BRIEF_v1.md` kaldırıldı — içeriği mutabakat dosyasına
  devredildi (D-008).

## Master Reference ↔ Kod Gecikmesi (2026-08-09 denetimi)

⚠ **Gecikme 2026-08-10'da büyüdü:** o denetimden bu yana 13 commit daha
geçti (Adım 1–7 + karar kapısı). v2.4.2'ye eklenecek yeni borçlar:
`preflight.py` ve `tool_identity.py` belgede hiç geçmiyor · GAP-14'ün
düzeltilmiş tarifi (D-022) · quantization NF4 kararı (D-020) · gate
ateşleme sonucu (D-017). **v2.4.2 Faz 2 bitince tek seferde yazılır** —
her adımda güncellemek iki kez yazmak olur.

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
