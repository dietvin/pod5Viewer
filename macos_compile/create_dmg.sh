#!/bin/bash

### --- ADJUST VERSION, SYSTEM, AND SYSTEMVERSION TO MATCH THE SYSTEM: --- ###
VERSION=1.0.2
# ALSO ADJUST VERSION IN SPEC FILE! (CFBundleVersion)
SYSTEM=macos
SYSTEMVERSION=14.04
### ---------------------------------------------------------------------- ###
# echo "Running pyinstaller"
# pyinstaller pod5Viewer.spec --noconfirm || exit 1

# mkdir -p dist/dmg
# rm -r dist/dmg/*

# cp -r dist/pod5Viewer dist/dmg/pod5Viewer.app

hdiutil create -volname "pod5Viewer Setup" -srcfolder "dist/dmg" -ov -format UDZO "pod5Viewer-${VERSION}-${SYSTEM}-${SYSTEMVERSION}.dmg"

# create-dmg \
#     --volname "pod5Viewer Setup" \
#     --volicon icon.icns \
#     --eula ../LICENSE \
#     --window-pos 200 120 \
#     --window-size 800 400 \
#     --icon-size 100 \
#     --icon "pod5Viewer.app" 200 190 \
#     --hide-extension "pod5Viewer.app" \
#     --app-drop-link 600 185 \
#     ./pod5viewer_${VERSION}_${SYSTEM}_${SYSTEMVERSION}-Setup.dmg \
#     dist/dmg