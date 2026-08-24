#!/usr/bin/env bash
# Master reference .md -> .html + .pdf
#
# D-172 turunda yazıldı. Daha önce iki kez elle koşulmuştu (v2.4.3, v2.5) ve
# ikisinde de reçete yalnız CLAUDE.md'nin bir cümlesinde duruyordu — bu yüzden
# .html/.pdf üç sürüm boyunca (v2.6, v2.7, v2.8) geride kaldı. Betik tam olarak
# o borcu kapatmak için var: reçete artık koşturulabilir.
#
# Emoji dönüşümü NEDEN var: xelatex'in DejaVu ailesinde bu kod noktalarının
# glifi yok; dönüştürülmezse PDF'te sessizce KAYBOLUYORLAR — yani anlamı taşıyan
# işaretler (⛔ / ⚠) bir uyarı bile vermeden düşüyor. Anlam korunur, PDF'in
# görüntüsü md'den bilerek farklıdır.
#
# ⚠ HTML dönüşüm YAPMAZ — tarayıcıda emoji zaten görünüyor, ve orada metne
# çevirmek md ile gereksiz bir fark yaratırdı.
#
# Kullanım:  bash docs/build_master_reference.sh

set -euo pipefail

cd "$(dirname "$0")/.."

SRC="docs/DAU_MASTER_REFERENCE_v20.md"
HTML="docs/DAU_MASTER_REFERENCE_v20.html"
PDF="docs/DAU_MASTER_REFERENCE_v20.pdf"
TMP="$(mktemp -t dau_master_ref_XXXXXX.md)"
trap 'rm -f "$TMP"' EXIT

command -v pandoc  >/dev/null || { echo "pandoc yok"  >&2; exit 1; }
command -v xelatex >/dev/null || { echo "xelatex yok" >&2; exit 1; }

echo "== pandoc: $(pandoc --version | head -1)"

# --- HTML: kaynak olduğu gibi ---
pandoc "$SRC" \
  --standalone --toc --toc-depth=3 \
  --metadata title="DAU — Master Reference" \
  -o "$HTML"
echo "== yazildi: $HTML"

# --- PDF: emoji -> metin karsiligi, sonra xelatex ---
# Listedeki her kod noktasi kaynakta FIILEN geciyor (sayimla dogrulandi);
# yeni bir emoji eklenirse buraya da eklenmeli, yoksa PDF'te sessizce duser.
python3 - "$SRC" "$TMP" <<'PY'
import sys

SUBS = {
    "✅": "[OK]",      # ✅
    "⚠": "[!]",       # ⚠
    "⛔": "[STOP]",    # ⛔
    "❌": "[X]",       # ❌
    "⭐": "[*]",       # ⭐
    "\U0001f512": "[LOCK]",   # 🔒
    "\U0001f514": "[BELL]",   # 🔔
    "\U0001f4dd": "[NOTE]",   # 📝
    "\U0001f5fa": "[MAP]",    # 🗺
    "\U0001f50d": "[AUDIT]",  # 🔍
    "\U0001f534": "[RED]",    # 🔴
    "⏸": "[PAUSE]",   # ⏸
    "⏳": "[WAIT]",    # ⏳
    "️": "",          # variation selector-16: gliflenmez, sessizce dusmeli
    # ⚠ DejaVu Sans Mono'da YOK. Prose'da (DejaVu Sans) duruyor ama KOD
    # BLOGUNDA sessizce dusuyordu — ve dustugu yer bir turetmenin "ancak ve
    # ancak"iydi (D-171 §3). Olculdu: md'de 3 gecis, PDF'te 1.
    "⟺": "<=>",
}

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
for k, v in SUBS.items():
    text = text.replace(k, v)

# Kalan gliflenmeyecek kod noktasi var mi? Sessiz kayip bu betigin onlemek
# icin var oldugu sey, o yuzden uyariyla bitiyor (susturmadan).
leftover = sorted({c for c in text if ord(c) > 0x2600 and c not in "✓✗"})
if leftover:
    print("[!] PDF'te dusebilecek islenmemis kod noktalari: "
          + " ".join(f"{c!r}(U+{ord(c):04X})" for c in leftover), file=sys.stderr)

open(dst, "w", encoding="utf-8").write(text)
PY

pandoc "$TMP" \
  --standalone --toc --toc-depth=3 \
  --pdf-engine=xelatex \
  --metadata title="DAU — Master Reference" \
  -V mainfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  -V geometry:margin=2cm \
  -o "$PDF"
echo "== yazildi: $PDF"

# --- URETIM SONRASI DOGRULAMA ---
# Sebep: xelatex'in "Missing character" uyarisi gurultunun icinde kayboluyor ve
# kayip SESSIZ oluyor. Ilk kosuda tam olarak bu oldu: `⟺` kod blogunun icinde
# dustu ve fark edilmedi.
#
# ⛔ ILK SURUM BOS BIR BEKCIYDI ve mutasyon kontrolu onu yakaladi. "Bu isaret
# PDF'te GECIYOR MU" diye soruyordu; `⟺` hem duz metinde (DejaVu Sans: glif
# VAR) hem kod blogunda (DejaVu Sans Mono: glif YOK) geciyor ⇒ duz metindeki
# tek gecis, kod blogundaki kaybi maskeliyordu. SUBS'tan ⟺ silindiginde bekci
# yine "hepsi bulundu" dedi. §2.4'un U7/A2 ornegiyle ayni sinif hata.
#
# ⇒ Test "var mi" degil "KAC TANE" diye soruyor. Tek yonlu, bilerek: PDF sayisi
# md'ninkinden BUYUK olabilir (icindekiler basliklari tekrarliyor), ama KUCUK
# olamaz — kucukse bir yerde dusmustur.
#
# ⚠ PDF ana metnini okur, PDF ANA HATTINI (bookmark) OKUMAZ — sinir asagida.
if command -v pdftotext >/dev/null; then
  python3 - "$TMP" "$PDF" <<'PY'
import subprocess, sys

sub_md, pdf = sys.argv[1], sys.argv[2]
text = subprocess.run(["pdftotext", pdf, "-"], capture_output=True,
                      text=True, check=True).stdout

src = open(sub_md, encoding="utf-8").read()
cands = {c for c in src if ord(c) > 0x7F and not c.isspace()}

lost = []
for c in sorted(cands):
    want, got = src.count(c), text.count(c)
    if got < want:
        lost.append((c, want, got))

if lost:
    print("[!] PDF'te EKSIK isaretler (sessiz kayip):", file=sys.stderr)
    for c, want, got in lost:
        print(f"[!]   {c!r} (U+{ord(c):04X}): md {want} -> PDF {got}",
              file=sys.stderr)
    print("[!] Duzeltme: bu kod noktalarini yukaridaki SUBS tablosuna ekle.",
          file=sys.stderr)
    sys.exit(1)

print(f"== dogrulama: {len(cands)} ASCII-disi isaretin hepsi PDF'te TAM sayida")
PY
else
  echo "[!] pdftotext yok — uretim sonrasi dogrulama ATLANDI" >&2
fi

# ⚠ ILAN EDILEN SINIR (olculdu, cozulmedi): xelatex 12 kez
# "no <turkce harf> in font ectt1000" uyariyor. ANA METIN ETKILENMIYOR —
# `havuz_oranı`, `çağrılmıyor`, `kurucunun nişinden` PDF'ten geri okundu ve
# saglam. Uyarilarin kaynagi yerellestirilemedi (en olasi aday PDF ana hatti /
# hyperref, DOGRULANMADI). Tahmin yerine sinir yaziliyor (K4).

echo "== bitti"
ls -la "$HTML" "$PDF"
