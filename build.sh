#!/usr/bin/env bash
# Builds dist/SteamOS-IsoMountTool-<version>-x86_64.AppImage
# (bundled Python from python-build-standalone + PySide6). Needs internet access.
# Created by Dominic Lesina x Claude
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
APP_ID="steamos-isomounttool"
PY_SERIES="${PY_SERIES:-3.12}"
PYSIDE_SPEC="${PYSIDE_SPEC:-PySide6-Essentials~=6.8.0}"
BUILD="$ROOT/build"
APPDIR="$BUILD/AppDir"
DIST="$ROOT/dist"
APPIMAGETOOL="${APPIMAGETOOL:-$BUILD/appimagetool}"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/opt" "$APPDIR/usr/share/$APP_ID" "$APPDIR/usr/lib/fallback" \
         "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps" "$DIST"

# --- 1. Python (relocatable python-build-standalone build, fetched with uv) --------
if ! command -v uv >/dev/null 2>&1; then
    python3 -m pip install --user --quiet uv
    export PATH="$HOME/.local/bin:$PATH"
fi
UVPY="$BUILD/uv-python"
uv python install "$PY_SERIES" --install-dir "$UVPY"
SRC_PY="$(find "$UVPY" -maxdepth 1 -type d -name "cpython-$PY_SERIES*-linux-x86_64-gnu" | sort | tail -n1)"
[[ -n "$SRC_PY" ]] || { echo "uv did not install Python $PY_SERIES"; ls -la "$UVPY"; exit 1; }
echo ">> Using $SRC_PY"
cp -a "$SRC_PY" "$APPDIR/opt/python"
rm -f "$APPDIR/opt/python/lib/python$PY_SERIES/EXTERNALLY-MANAGED"
PY="$APPDIR/opt/python/bin/python$PY_SERIES"
[[ -x "$PY" ]] || { echo "python binary missing: $PY"; exit 1; }
"$PY" -m ensurepip --upgrade >/dev/null 2>&1 || true

# --- 2. PySide6 ----------------------------------------------------------------
echo ">> Installing $PYSIDE_SPEC"
"$PY" -m pip install --no-cache-dir --disable-pip-version-check --no-compile "$PYSIDE_SPEC"

SITE="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
PS="$SITE/PySide6"
echo ">> Trimming"
rm -rf "$PS/Qt/qml" "$PS/Qt/translations" "$PS/include" "$PS/typesystems" "$PS/glue" "$PS/scripts" \
       "$PS"/{designer,linguist,assistant,lrelease,lupdate,qmllint,qmlformat,qmlls,balsam,balsamui,svgtoqml,qsb} \
       "$PS"/Qt/libexec "$SITE/PySide6/examples" 2>/dev/null || true
for mod in Quick Qml QuickWidgets QuickControls2 QuickTest Designer Pdf PdfWidgets ShaderTools \
           3DCore 3DRender 3DInput 3DLogic 3DAnimation 3DExtras Charts DataVisualization Graphs \
           Multimedia MultimediaWidgets SpatialAudio Sql Test Help UiTools Concurrent \
           RemoteObjects Scxml StateMachine TextToSpeech WebSockets Positioning Location \
           SerialPort SerialBus Sensors Nfc Bluetooth HttpServer; do
    rm -f "$PS"/Qt"$mod".*.so "$PS"/Qt"$mod".pyi "$PS"/Qt/lib/libQt6"$mod".so* 2>/dev/null || true
done
rm -rf "$PS"/Qt/plugins/{qmltooling,sqldrivers,multimedia,designer,sceneparsers,geometryloaders,renderers,assetimporters,position,sensors,texttospeech} 2>/dev/null || true
"$PY" -m pip uninstall -y pip setuptools >/dev/null 2>&1 || true
rm -rf "$APPDIR/opt/python/include" "$APPDIR/opt/python/share" \
       "$APPDIR/opt/python/lib/python$PY_SERIES"/{test,idlelib,tkinter,turtledemo,ensurepip,lib2to3} \
       "$APPDIR/opt/python/lib"/{libtcl*,libtk*,tcl*,tk*,itcl*,thread*} 2>/dev/null || true

# --- 3. App -------------------------------------------------------------------------
cp -r "$ROOT/src/isomounttool" "$APPDIR/usr/share/$APP_ID/"
find "$APPDIR/usr/share/$APP_ID" -name __pycache__ -prune -exec rm -rf {} +
install -m 755 "$ROOT/src/steamos-isomounttool.py" "$APPDIR/usr/share/$APP_ID/steamos-isomounttool.py"
install -m 644 "$ROOT/VERSION" "$APPDIR/usr/share/$APP_ID/isomounttool/VERSION"
install -m 644 "$ROOT/packaging/$APP_ID.svg" "$APPDIR/usr/share/$APP_ID/isomounttool/icon.svg"
"$PY" -m compileall -q "$APPDIR/usr/share/$APP_ID" "$SITE" >/dev/null 2>&1 || true

# --- 4. Fallback libs (only used if the system lacks libxcb-cursor) ------------
if command -v apt-get >/dev/null 2>&1; then
    tmpdeb="$(mktemp -d)"
    ( cd "$tmpdeb" && apt-get download libxcb-cursor0 libxcb-image0 libxcb-render-util0 libxcb-util1 >/dev/null 2>&1 ) || true
    for deb in "$tmpdeb"/*.deb; do
        [[ -f "$deb" ]] || continue
        dpkg -x "$deb" "$tmpdeb/x"
    done
    find "$tmpdeb/x" -name 'libxcb-*.so.*' -exec cp -P {} "$APPDIR/usr/lib/fallback/" \; 2>/dev/null || true
    rm -rf "$tmpdeb"
fi

# --- 5. AppImage metadata ------------------------------------------------------------
install -m 755 "$ROOT/packaging/AppRun" "$APPDIR/AppRun"
sed -i "s|@PYBIN@|opt/python/bin/python$PY_SERIES|" "$APPDIR/AppRun"
install -m 644 "$ROOT/packaging/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
install -m 644 "$ROOT/packaging/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"
if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 256 -h 256 "$ROOT/packaging/$APP_ID.svg" -o "$APPDIR/$APP_ID.png"
else
    convert -background none "$ROOT/packaging/$APP_ID.svg" -resize 256x256 "$APPDIR/$APP_ID.png"
fi
cp "$APPDIR/$APP_ID.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
ln -sf "$APP_ID.png" "$APPDIR/.DirIcon"

if [[ ! -x "$APPIMAGETOOL" ]]; then
    curl -fsSL -o "$APPIMAGETOOL" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$APPIMAGETOOL"
fi
OUT="$DIST/SteamOS-IsoMountTool-${VERSION}-x86_64.AppImage"
rm -f "$OUT"
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUT"
du -h "$OUT"
echo "Built: $OUT"
