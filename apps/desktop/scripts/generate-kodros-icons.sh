#!/usr/bin/env bash
# Regenerate every Kodros Desktop icon from assets/kodros-mark.svg.
#   assets/icon*.png|ico|icns, assets/appx/*, assets/icon.icon/Assets/*,
#   public/apple-touch-icon.png, public/kodros-mark*.png (BrandMark tiles).
# Needs rsvg-convert and ImageMagick 7 (`magick`). The dark tile is the
# brand default; the light tile only paints BrandMark on light surfaces.
set -euo pipefail

cd "$(dirname "$0")/.."
src=assets/kodros-mark.svg
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Variants derived from the one source: light tile, and tile-less glyphs.
sed -e 's/fill="#000000"/fill="#ffffff"/' -e 's/stroke="#262626"/stroke="#e4e4e7"/' -e 's/stroke="#f5f5f5"/stroke="#0a0a0a"/' \
  "$src" > "$work/light.svg"
sed -e '/<rect width="1024"/d' -e '/<rect x="2"/d' "$src" > "$work/glyph-paper.svg"
sed -e 's/stroke="#f5f5f5"/stroke="#0a0a0a"/' "$work/glyph-paper.svg" > "$work/glyph-ink.svg"

png() { rsvg-convert -w "$2" -h "$2" "$1" -o "$3"; }

png "$src" 1024 assets/icon.png
cp assets/icon.png assets/icon-dark.png
png "$src" 1024 public/apple-touch-icon.png
png "$src" 256 public/kodros-mark-dark.png
png "$work/light.svg" 256 public/kodros-mark.png

# macOS <= 15 artwork: the tile inset to Apple's 824/1024 grid.
png "$src" 824 "$work/mac-824.png"
magick -size 1024x1024 xc:none "$work/mac-824.png" -gravity center -composite assets/icon-mac.png

for size in 16 24 32 48 64 128 256; do png "$src" "$size" "$work/ico-$size.png"; done
magick "$work"/ico-{16,24,32,48,64,128,256}.png assets/icon.ico
cp assets/icon.ico assets/icon-dark.ico

for size in 16 32 64 128 256 512 1024; do magick "$work/mac-824.png" -resize "${size}x${size}" "$work/icns-$size.png"; done
# ImageMagick cannot write ICNS; the container is a header plus typed PNG chunks.
python3 - "$work" assets/icon.icns <<'PY'
import struct, sys
work, out = sys.argv[1], sys.argv[2]
chunks = b''
for kind, size in (('icp4', 16), ('icp5', 32), ('icp6', 64), ('ic07', 128), ('ic08', 256), ('ic09', 512), ('ic10', 1024)):
    data = open(f'{work}/icns-{size}.png', 'rb').read()
    chunks += kind.encode() + struct.pack('>I', len(data) + 8) + data
open(out, 'wb').write(b'icns' + struct.pack('>I', len(chunks) + 8) + chunks)
PY
cp assets/icon.icns assets/icon-dark.icns

# Icon Composer layers: glyph only; the package's fill paints the tile.
png "$work/glyph-ink.svg" 1024 assets/icon.icon/Assets/art-light.png
png "$work/glyph-paper.svg" 1024 assets/icon.icon/Assets/art-dark.png
png "$work/glyph-paper.svg" 1024 assets/icon.icon/Assets/mono.png

# MSIX logos: every file keeps its own pixel size. Plated logos sit on the
# black brand field; unplated forms are the glyph alone on transparency.
for file in assets/appx/*.png; do
  read -r width height < <(magick identify -format '%w %h\n' "$file")
  case "$file" in
    *altform-lightunplated*) art="$work/glyph-ink.svg" field=none ;;
    *altform-unplated*) art="$work/glyph-paper.svg" field=none ;;
    *) art="$work/glyph-paper.svg" field='#000000' ;;
  esac
  side=$((width < height ? width : height))
  rsvg-convert -w "$side" -h "$side" "$art" -o "$work/tile.png"
  magick -size "${width}x${height}" "xc:$field" "$work/tile.png" -gravity center -composite "$file"
done
