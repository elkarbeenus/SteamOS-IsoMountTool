#!/usr/bin/env bash
# Builds SteamOS-IsoMountTool-<version>-x86_64.AppImage into ./dist
# Created by Dominic Lesina x Claude
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
APP_ID="steamos-isomounttool"
BUILD="$ROOT/build"
APPDIR="$BUILD/AppDir"
DIST="$ROOT/dist"
APPIMAGETOOL="${APPIMAGETOOL:-$BUILD/appimagetool}"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/$APP_ID" \
         "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/icons/hicolor/scalable/apps" "$DIST"

install -m 755 "$ROOT/src/$APP_ID"               "$APPDIR/usr/bin/$APP_ID"
install -m 644 "$ROOT/VERSION"                    "$APPDIR/usr/share/$APP_ID/VERSION"
install -m 755 "$ROOT/packaging/AppRun"           "$APPDIR/AppRun"
install -m 644 "$ROOT/packaging/$APP_ID.desktop"  "$APPDIR/$APP_ID.desktop"
install -m 644 "$ROOT/packaging/$APP_ID.desktop"  "$APPDIR/usr/share/applications/$APP_ID.desktop"
install -m 644 "$ROOT/packaging/$APP_ID.svg"      "$APPDIR/usr/share/icons/hicolor/scalable/apps/$APP_ID.svg"

# PNG icon (rsvg-convert or ImageMagick), fallback: SVG
if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 256 -h 256 "$ROOT/packaging/$APP_ID.svg" -o "$APPDIR/$APP_ID.png"
elif command -v convert >/dev/null 2>&1; then
    convert -background none "$ROOT/packaging/$APP_ID.svg" -resize 256x256 "$APPDIR/$APP_ID.png"
fi
if [[ -f "$APPDIR/$APP_ID.png" ]]; then
    cp "$APPDIR/$APP_ID.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
    ln -sf "$APP_ID.png" "$APPDIR/.DirIcon"
else
    cp "$ROOT/packaging/$APP_ID.svg" "$APPDIR/$APP_ID.svg"
    ln -sf "$APP_ID.svg" "$APPDIR/.DirIcon"
fi

if [[ ! -x "$APPIMAGETOOL" ]]; then
    echo "Downloading appimagetool…"
    curl -fsSL -o "$APPIMAGETOOL" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$APPIMAGETOOL"
fi

OUT="$DIST/SteamOS-IsoMountTool-${VERSION}-x86_64.AppImage"
rm -f "$OUT"
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUT"
echo "Built: $OUT"
