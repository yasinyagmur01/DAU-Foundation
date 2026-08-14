# A4-② Popülasyon — tasarım önerisi (read-only denetim sonrası)

**Tarih:** 2026-08-14 · **Durum:** ⏳ **öneri, karar bekliyor** · **kod
yazılmadı** (§2.3)

**Girdiler:** read-only denetim (bu belge §1) · **D-075** (yerel tarama, §L) ·
**D-076** (DR #6 mutabakatı, §M) · **D-074** (sıralama kararı)

⚠ **Bu belge karar vermiyor.** Yedi karar noktası (**P1–P7**) çıkarıyor,
her birine kanıtı ve önerisiyle. Kararlar Yasin'in (D-007), ve verildiklerinde
`DECISIONS.md`'ye D-077 olarak geçerler.

---

## 1. Denetim: ne hazır, ne engel

### Hazır (kod değişikliği gerekmiyor)

| Ne | Durum |
|---|---|
| `step_pool_with_crisis(env, extractions: dict, drift_states: dict)` | **Gerçekten N-ajanlı.** Talep oransal bölüşülüyor (D-066), kriz travması ajan başına |
| `_memory_stores` / `_memory_written` | `agent_id` ile anahtarlı |
| Sosyal katman | `opponent_id` + Markov beklentisi zaten iki-ajanlı |

### Engel (ciddiyet sırasına göre)

| # | Engel | Nerede |
|---|---|---|
| **E1** | **Havuz özel mülk.** Her ajan `_seed_niche(seed)`'ten kendi `EnvironmentState`'iyle doğuyor; `env_state` `DAUAgentState`'in alanı | `run_protocol_c_prime.py` `_initial_state` |
| **E2** | **Grafik akış başına tek ajan.** `StateGraph(DAUAgentState)` | `graph.py` `build_graph` |
| **E3** | ⚠ **Üç olay tamponu ajan kimliği taşımıyor** — N ajan aynı anda yaşarsa satırlar karışır ve **landmark okuması sessizce yanlış ajanı okur** | `graph.py` `_pe_event_log` · `_pool_event_log` · `_body_event_log` |
| **E4** | **Üreme tekil:** 1 ebeveyn → 1 varis. *"Kim ürer, kaç varis"* katmanı **yok** | `generation.py` · `run_cprime_multigen.py` |
| **E5** | `pool_step_node` tek girdilik sözlük geçiyor: `{state.agent_id: amount}` | `graph.py:1229` |

⚠ **E3 en sinsi olanı:** kod çalışmaya devam eder, sayı üretir, ve sayı
yanlış olur. Diğer dördü çalışmayı durdurur.

---

## 2. ⭐ Linçpin: `w` sabit olduğu sürece seçilim ÖLÇÜLEMEZ

D-076'nın en değerli çıktısı **Price eşitliği**:

```
Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)
        └── seçilim ──┘      └── aktarım sapması ──┘
```

Bu, D-075'in açtığı **totoloji borcunu** ödüyor: uygunluk `w` seçilimi
sürükler, **sabit yaşta okunan drift vektörü `z`** sonuç ölçütü kalır ⇒
döngü kırılır. **K5 kararımız (landmark drift) tam olarak `z` rolüne
oturuyor** — D-070/D-072'de verilen karar bağımsız gerekçeyle desteklendi.

⚠ **Ama ön koşulu var ve bugün sağlanmıyor:** `Cov(wᵢ, zᵢ)` ancak `w`
**değişkense** tanımlıdır. Bugün her ebeveynin **tam olarak bir** varisi var
⇒ `w` sabit ⇒ **kovaryans tanımsız, seçilim ölçülemez.**

⇒ **②'nin asıl işi popülasyon eklemek değil, `w`'yi değişken yapmaktır.**
Diğer her şey bunun altyapısı.

---

## 3. Karar noktaları

### P1 — Havuz paylaşımı

| Seçenek | Kanıt |
|---|---|
| **(a) Kol başına ayrı havuz** | ⭐ **İki bağımsız literatür aynı yerde:** Hudgens & Halloran 2008 (SUTVA / kısmi girişim, D-076) ve Xiao vd. 2023 (referans suş varsayımı, D-075). `null` kolumuz **bir referans suştur**; ortak havuz o varsayımı yapı gereği ihlal eder |
| (b) Tek havuz, karışık kollar | Doğrudan rekabet olur; ama bir kolun aşırı hasadı diğerinin ortamı olur. İki aşamalı doygunluk tasarımı (%25/%50/%75) gerektirir ⇒ kolların **ne olduğunu** değiştirir |

**Öneri: (a).** ⚠ **Bedeli ilan edilmeli** (Chevin 2011, doğrulandı):
izolasyon, seçilim iddiasını **birey düzeyinden grup düzeyine** kaydırır.
İkinci ön-kayıta ilan edilmiş sınır olarak yazılır — K5'in sınırının yanına.

### P2 — Seçilim şeması

| Seçenek | Kanıt |
|---|---|
| **Turnuva (k=2)** | Goldberg & Deb 1991 (doğrulandı): baskı `k` ile ayarlanabilir; küçük N'de çeşitliliği kesme seçiliminden iyi korur |
| Kesme (üst %50) | ⚠ **Yayımlanmış en yakın analog bunu kullanıyor** (Vallinder & Hughes 2024, D-075/V3). Ama N=8–10'da çeşitliliği hızla tüketir |
| Uygunlukla orantılı | Uygunluk farkları küçülünce baskıyı kaybeder — **bizde tam da bu risk var** (D-060: 120/120 kol aynı sınıf) |

**Öneri: turnuva k=2.** Gerekçe çeşitlilik değil **ölçülebilirlik**: orantılı
şema bizim dar uygunluk dağılımımızda baskı üretmez, kesme ise N=8'de iki
nesilde tek soya iner.

### P3 — Kim ürer, kaç varis, popülasyon sabit mi

**Öneri:** popülasyon boyutu **sabit N**; her nesilde ölen her ajanın yerine
turnuva ile seçilmiş bir ebeveynden **bir varis** doğar. ⇒ `wᵢ` = *o ajanın o
nesilde kazandığı turnuva sayısı* = **0, 1, 2, …** ⇒ **`w` değişken olur** ve
Price'ın kovaryansı tanımlanır.

⚠ **Alternatif:** ölüm-doğum dengesine bırakmak (popülasyon dalgalanır).
Daha "doğal" ama N=8'de popülasyonun sıfıra inme riski var — davranış çökük
olduğu için (D-068) bu **gerçek bir risk**, teorik değil.

### P4 — `w` ne olsun (⚠ D-071 buraya bağlanıyor)

⚠ **`F_agent`'ı doğrudan `w` yapmak totolojiyi geri getirir:** D-071'den beri
`F_agent`'ın %30'u **gerçekleşmiş hayatta kalma**. O skor hem kimin üreyeceğini
belirler hem sonuç olarak raporlanırsa, D-075'in Mills & Beatty (1979)
üzerinden yazdığı döngüye girilir.

**Öneri — üç katmanı ayır:**

| Katman | Ne | Rol |
|---|---|---|
| **Seçilim girdisi** | `F_agent` (turnuva bunun üzerinden) | **girdi**, raporlanır ama **sonuç değildir** |
| **Demografik başarı `w`** | varis sayısı (turnuva kazanımı) | Price'ın `w`'si |
| **Sonuç `z`** | **landmark drift vektörü** (K5) | **birincil uç nokta** |

⇒ `F_agent` → `w` → seçilim; `z` bağımsız olarak okunur. Döngü kırılır.

### P5 — Kol yapısı popülasyonda ne demek

**Öneri:** kol, **popülasyonun tamamına uygulanan eğitim kuralıdır**.
Üç ayrı popülasyon + üç ayrı havuz: `lived` popülasyonunda her ajan kendi
yaşadığı tercihlerle eğitilir; `shuffle`'da tercih yönü ters; `null`'da hiç
eğitim yok. **Kol içi seçilim `F_agent`'tan, kollar arası karşılaştırma
`z`'nin nesiller boyu dağılımından.**

### P6 — İki faz korunsun mu

Bugün her soy nesil başına **iki** yaşam yaşıyor (eğitim öncesi/sonrası,
`delta_pe` için). Popülasyonda bu maliyeti **ikiye katlıyor**.

**Öneri: tek faz.** Popülasyonda karşılaştırma **nesiller arası** yapılıyor
(nesil *g* → *g+1*), yani faz-2'nin işini bir sonraki nesil zaten görüyor.
⚠ **Bedeli:** `delta_pe` (nesil içi ΔPE) uç noktası **kaybolur**. S3/S4'ün
ön-kayıtlı hâli buna göre yazılmalı.

### P7 — N / G / tohum zarfı

⚠ **Bu karar için literatür bize sayı VERMEDİ** ve iki kaynak farklı eksenleri
konuşuyor (D-076/§M.4): Kofler & Schlötterer *tekrar > N*, DR *N > G*
(⚠ dayanağı yanlış atıf). ⚠ Ayrıca DR **kendi içinde çelişiyor**: §5 birikimli
iz için **G=5–10** diyor, §6 sentezi **G=3** öneriyor.

**Öneri: G ≥ 5'i taban kabul et** (birikimli kalıtım iddiası ②'nin gerekçesi,
D-014/D-074), sonra tohum ve N'yi bütçeye sığdır.

| Tohum | N | G | Olay | Toplam olay | Süre |
|---|---|---|---|---|---|
| 6 | 8 | 5 | 30 | 21.600 | **19.6 sa** |
| 10 | 6 | 5 | 30 | 27.000 | **24.5 sa** |
| **10** | **8** | **5** | **30** | **36.000** | **32.7 sa** |
| 10 | 10 | 5 | 30 | 45.000 | 40.9 sa |
| 16 | 6 | 5 | 30 | 43.200 | 39.2 sa |

*(tek faz, kol başına ayrı popülasyon, 3.27 sn/olay — B2'nin ölçülen hızı.
İki faz korunursa bu sayılar **ikiye katlanır**.)*

⚠ **Olay bütçesi 30:** D-068'de havuz çöküşü 10–19. olayda gerçekleşti, yani
30 olay krizi yakalamaya yetiyor. **Ama bu sayı ölçülmüş bir eşik değil,
pilot gözleminden çıkarılmış bir çıkarımdır** — ön-kayıtta öyle etiketlenmeli.

---

## 4. Kod işleri (P1–P7 karara bağlandıktan sonra, sırayla)

| # | İş | Bağlı olduğu karar |
|---|---|---|
| 1 | **E3 — üç tampona `agent_id` ekle** | hiçbiri; **ilk yapılmalı**, sessiz kusur riski |
| 2 | **E1/E5 — ortak havuzu akışların dışına al**, `pool_step_node` N ajanın talebini toplasın | P1 |
| 3 | **E2 — N ajanı olay bazında kilit adımda ilerleten dış döngü** | P1, P6 |
| 4 | **E4 — üreme katmanı:** turnuva, `w` sayacı, varis üretimi | P2, P3, P4 |
| 5 | **Price aletlemesi:** `Cov(w, z)` ve `E(w·Δz)` nesil başına kaydedilir | P4 |
| 6 | **Geçerlilik kapısı:** `w` ve `F_agent` dağılımının yayılımı raporlanır | aşağıya bak |

---

## 5. ⚠ Ön-kayıta girmesi gereken geçerlilik kapısı

**Seçilim, `w`'de varyans yoksa görünemez.** Davranış çökük (D-068: olayların
%94–100'ünde DEFECT) ve K7 tek ölçülmüş kaldıracı kapattı (D-074). Bu, ②
sonrasında da devam edebilir: N ajanın hepsi aynı baskın stratejiyi oynarsa
`F_agent`'ları özdeş olur, turnuva **yazı-tura**ya döner, `Cov(w, z) ≈ 0`.

⇒ **Ön-kayıta şu yazılmalı:** *"`F_agent` dağılımının yayılımı ve `w`'nin
varyansı geçerlilik ön-koşuludur; yayılım yoksa koşum **seçilim hakkında
bilgisizdir** ve öyle raporlanır."*

⚠ Bu **etkiye bakmak değil** (L9): kol farkına değil, **dağılımın var olup
olmadığına** bakılıyor, ve kural koşumdan **önce** yazılıyor. Pilotta
ölçülecek şey de tam olarak bu.

---

## 6. Bu önerinin dayanmadığı şeyler

- **`N=16, G=3, 35 olay` (DR sentezi) alınmadı** — dayanağı yanlış atıf
  (D-076/M.1), kendi §5'iyle çelişiyor (M.3).
- **Birikimli kalıtım için kaç nesil** — ne DR ne yerel tarama sayı verebildi.
  `G ≥ 5` bir **taban**, ölçülmüş bir çıta değil.
- **Bedau'nun çeşitlilik/aktivite ölçütleri** — atıf kırık (404), alınmadı.
- **Hiçbir sabit ölçüme bakılarak seçilmedi** (§2.7).
