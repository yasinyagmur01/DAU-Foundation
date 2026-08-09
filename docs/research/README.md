# Gemini Deep Research arşivi

Bu klasör **ham** Deep Research çıktılarını tutar. Düzenlenmez, kısaltılmaz,
temizlenmez — olduğu gibi durur. Amaç provenans: altı ay sonra "bu karar
nereden geldi" sorusunun cevabı burada bulunabilsin.

Damıtılmış çıktı ayrı dosyada: `RECONCILIATION.md` (Claude Code üretir).

## Dosya adlandırma

```
YYYY-MM-DD_kisa-konu.md
```

Örnek: `2026-08-05_layer5-ozbilinc.md`, `2026-07-28_lora-vs-online.md`

Tarih önde olduğu için `ls` kronolojik sıralar — ayrıca sıra tutmaya gerek yok.
Tarihi hatırlamıyorsan yaklaşık ver, `~` koy: `2026-07~_konu.md`.

Kural: **bir Deep Research koşumu = bir dosya.** Nerede bittiğini
hatırlamıyorsan konuya göre böl, sorun değil.

## Dosya yapısı

`_TEMPLATE.md`'yi kopyala. Üç frontmatter alanı + iki bölüm:

```markdown
---
tarih: 2026-08-05
konu: Layer 5 özbilinç / metacognition
tetikleyen soru: ...
---

## Kaynak prompt
## Rapor
```

`tetikleyen soru` en değerlisi — "bunu neden araştırdık" bilgisi,
araştırmanın kendisinden daha hızlı kayboluyor. Hatırlamıyorsan boş bırak,
uydurma.

`## Kaynak prompt` bölümü orijinal Deep Research prompt'unu birebir tutar.
Prompt'un kendisi provenansın yarısıdır: hangi soruyu sorduğun, gelen
cevabın neden o şekilde geldiğini açıklar.

## İçeriğe dokunma

Tek izinli dönüşüm: başlıkların markdown biçimine normalize edilmesi
(`##`, `###`) — Claude Code'un başlık ağacını taraması için gerekli.
Metnin kendisi değişmez.

Kısaltma, özetleme, "işe yaramaz" kısımları atma. İki nedenle:

1. Neyin işe yaradığı ancak kodla karşılaştırınca belli oluyor — şu an
   gereksiz görünen bir bölüm, üç ay sonra bir GAP'in cevabı çıkabiliyor.
2. Kısaltılmış bir kaynak provenans olarak zayıftır. Bu klasörün tek işi
   provenans.

Token endişesi yok: Claude Code önce yalnızca başlıkları tarar, sonra
gerekli bölümleri seçerek okur. Ham metin sohbete girmez.

## Süreç (D-006)

1. Sen dosyaları buraya bırakırsın, "hazır" dersin
2. Claude Code tek komutla bütün başlık ağacını çıkarır
3. Öncelik sırası önerir, sen onaylarsın
4. Brief başına bir tur: ilgili bölümler okunur, kodla karşılaştırılır
5. Sonuç `RECONCILIATION.md`'ye **DAU konusuna göre** işlenir (brief'e göre
   değil), dört karardan biriyle:

   | Karar | Nereye gider |
   |---|---|
   | bilinçli sapma | `docs/DECISIONS.md`, gerekçesiyle |
   | fark edilmemiş kayma | `CLAUDE.md`, GAP olarak |
   | uyumlu | `RECONCILIATION.md`'de kalır |
   | brief yanılmış | `RECONCILIATION.md`'de kalır — ileride tekrar içeri sızmasın diye |
