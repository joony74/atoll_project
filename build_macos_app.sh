#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN=""
for candidate in "venv_clean/bin/python" "venv/bin/python"; do
  if [[ -x "$candidate" ]]; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "No runtime python found in venv_clean/bin/python or venv/bin/python" >&2
  exit 1
fi

ICON_SOURCE="${ICON_SOURCE:-assets/cocoai_icon_1024_clean.png}"
ICON_PNG="assets/cocoai_app_icon.png"
ICON_ICNS="assets/cocoai_app_icon.icns"
ICONSET_DIR="/tmp/cocoai_app_icon.iconset"
APP_NAME="CocoAi Study"
APP_EXECUTABLE="CocoAIStudy"
BUNDLE_ID="com.futureplatform.cocoaistudy"
PRODUCT_BUNDLE_IDENTIFIER="$BUNDLE_ID"
INSTALL_APP_PATH="${INSTALL_APP_PATH:-$HOME/Desktop/$APP_NAME.app}"
INSTALL_BACKUP_ROOT="${INSTALL_BACKUP_ROOT:-$HOME/Desktop/CocoAiStudyBackups}"
DEFAULT_CODESIGN_IDENTITY="CocoAi Study Local Code Signing"
CODE_SIGN_IDENTITY="${COCO_CODESIGN_IDENTITY:-}"
if [[ -z "$CODE_SIGN_IDENTITY" ]] && /usr/bin/security find-identity -v -p codesigning 2>/dev/null | /usr/bin/grep -q "\"$DEFAULT_CODESIGN_IDENTITY\""; then
  CODE_SIGN_IDENTITY="$DEFAULT_CODESIGN_IDENTITY"
fi

if [[ ! -f "$ICON_SOURCE" ]]; then
  echo "Icon source not found: $ICON_SOURCE" >&2
  exit 1
fi

cp "$ICON_SOURCE" "$ICON_PNG"

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

sips -z 16 16 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
sips -z 64 64 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
cp "$ICON_PNG" "$ICONSET_DIR/icon_512x512@2x.png"
if ! iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"; then
  echo "iconutil failed; falling back to Pillow-generated icns"
  "$PYTHON_BIN" -c '
from PIL import Image
src = Image.open("'"$ICON_PNG"'").convert("RGBA")
src.save("'"$ICON_ICNS"'", sizes=[(16,16),(32,32),(64,64),(128,128),(256,256),(512,512),(1024,1024)])
'
fi

find . -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf build dist

APP_DIR="dist/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
BUNDLE_PROJECT_DIR="$RESOURCES_DIR/project"
BUNDLE_RUNTIME_DIR="$RESOURCES_DIR/runtime"
LAUNCHER_M="macos/CocoAIStudyLauncher.m"
RUNTIME_ROOT="$(cd "$(dirname "$PYTHON_BIN")/.." && pwd)"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR" "$BUNDLE_PROJECT_DIR"
cp "$ICON_ICNS" "$RESOURCES_DIR/$APP_EXECUTABLE.icns"
printf 'APPL????' > "$CONTENTS_DIR/PkgInfo"

ditto "$RUNTIME_ROOT" "$BUNDLE_RUNTIME_DIR"
ditto app "$BUNDLE_PROJECT_DIR/app"
ditto assets "$BUNDLE_PROJECT_DIR/assets"
if [[ -d config ]]; then
  ditto config "$BUNDLE_PROJECT_DIR/config"
fi
if [[ -d data/problem_bank ]]; then
  mkdir -p "$BUNDLE_PROJECT_DIR/data"
  ditto data/problem_bank "$BUNDLE_PROJECT_DIR/data/problem_bank"
fi
cp app.py "$BUNDLE_PROJECT_DIR/app.py"
cp desktop_app.py "$BUNDLE_PROJECT_DIR/desktop_app.py"

cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>$APP_EXECUTABLE</string>
  <key>CFBundleIconFile</key>
  <string>$APP_EXECUTABLE</string>
  <key>CFBundleIdentifier</key>
  <string>$PRODUCT_BUNDLE_IDENTIFIER</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundleDisplayName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleSupportedPlatforms</key>
  <array>
    <string>MacOSX</string>
  </array>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSScreenCaptureUsageDescription</key>
  <string>CocoAi Study uses screen capture only when you choose an area to register as a learning image.</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
</dict>
</plist>
EOF

clang -O2 -framework Cocoa -framework WebKit -framework ImageIO -framework CoreServices -o "$MACOS_DIR/$APP_EXECUTABLE" "$LAUNCHER_M"
chmod +x "$MACOS_DIR/$APP_EXECUTABLE"
if [[ -n "$CODE_SIGN_IDENTITY" ]]; then
  codesign --force --deep --sign "$CODE_SIGN_IDENTITY" --identifier "$PRODUCT_BUNDLE_IDENTIFIER" "$APP_DIR" >/dev/null
else
  echo "Warning: no stable code signing identity found; falling back to ad-hoc signing." >&2
  echo "         Screen Recording permission can reset between builds until a stable identity is installed." >&2
  codesign --force --deep --sign - --identifier "$PRODUCT_BUNDLE_IDENTIFIER" "$APP_DIR" >/dev/null
fi

if [[ "${INSTALL_TO_STABLE_PATH:-1}" == "1" ]]; then
  mkdir -p "$(dirname "$INSTALL_APP_PATH")"
  if [[ -d "$INSTALL_APP_PATH" ]]; then
    mkdir -p "$INSTALL_BACKUP_ROOT"
    BACKUP_PATH="$INSTALL_BACKUP_ROOT/CocoAiStudy-$(date +%Y%m%d_%H%M%S).app.tar.gz"
    tar -C "$(dirname "$INSTALL_APP_PATH")" -czf "$BACKUP_PATH" "$(basename "$INSTALL_APP_PATH")"
    rm -rf "$INSTALL_APP_PATH"
    echo "Backed up existing app:"
    echo "  $BACKUP_PATH"
  fi
  ditto "$APP_DIR" "$INSTALL_APP_PATH"
  echo "Installed stable app path:"
  echo "  $INSTALL_APP_PATH"
fi

echo ""
echo "Build complete:"
echo "  $APP_DIR"
echo "Bundle identifier:"
echo "  $PRODUCT_BUNDLE_IDENTIFIER"
echo "Code signing identity:"
if [[ -n "$CODE_SIGN_IDENTITY" ]]; then
  echo "  $CODE_SIGN_IDENTITY"
else
  echo "  ad-hoc"
fi
