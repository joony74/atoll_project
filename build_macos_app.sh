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

APP_DIR="dist/CocoAIStudy.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
LAUNCHER_M="/tmp/cocoai_launcher.m"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
cp "$ICON_ICNS" "$RESOURCES_DIR/CocoAIStudy.icns"
printf 'APPL????' > "$CONTENTS_DIR/PkgInfo"

cat > "$CONTENTS_DIR/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>CocoAIStudy</string>
  <key>CFBundleIconFile</key>
  <string>CocoAIStudy</string>
  <key>CFBundleIdentifier</key>
  <string>com.cocoai.study</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>CocoAi Study</string>
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
</dict>
</plist>
EOF

cat > "$LAUNCHER_M" <<EOF
#import <Cocoa/Cocoa.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        [NSApplication sharedApplication];

        NSString *projectRoot = @"/Users/juhwigeun/Desktop/atoll_project";
        NSString *pythonBin = @"/Users/juhwigeun/Desktop/atoll_project/${PYTHON_BIN}";
        NSString *desktopEntry = @"/Users/juhwigeun/Desktop/atoll_project/desktop_app.py";

        [[NSFileManager defaultManager] changeCurrentDirectoryPath:projectRoot];

        NSTask *task = [[NSTask alloc] init];
        task.launchPath = pythonBin;
        task.arguments = @[desktopEntry];
        task.standardOutput = [NSFileHandle fileHandleWithNullDevice];
        task.standardError = [NSFileHandle fileHandleWithNullDevice];
        [task launch];
    }
    return 0;
}
EOF

clang -O2 -framework Cocoa -o "$MACOS_DIR/CocoAIStudy" "$LAUNCHER_M"
chmod +x "$MACOS_DIR/CocoAIStudy"

echo ""
echo "Build complete:"
echo "  dist/CocoAIStudy.app"
