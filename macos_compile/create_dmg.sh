#!/bin/bash

### --- ADJUST VERSION, AND SYSTEMVERSION TO MATCH THE SYSTEM: --- ###
VERSION=1.0.2
SYSTEMVERSION=14.04
### -------------------------------------------------------------- ###

python setup.py py2app -A || exit 1

create-dmg \
    --volname "pod5Viewer Setup" \
    --volicon icon.icns \
    --eula ../LICENSE \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "pod5Viewer.app" 200 190 \
    --hide-extension "pod5Viewer.app" \
    --app-drop-link 600 185 \
    ./pod5viewer_${VERSION}_macos_${SYSTEMVERSION}-Setup.dmg \
    dist/

echo "Cleaning up"
rm -r build dist