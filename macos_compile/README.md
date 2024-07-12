# Compile pod5Viewer to DEB package

To compile the pod5Viewer to an installable DMG file, follow the following instructions:

1. Make sure py2app is installed
2. Change directory to `./macos_compile`
3. Adjust the VERSION, SYSTEM and SYSTEMVERSION variables in `create_deb.sh`
4. Adjust the VERSION in setup.py
4. run `create_dmg.sh`

If the script runs successfully the DMG `pod5viewer_<VERSION>_macos_<SYSTEMVERSION>-Setup.dmg` will be placed in the `macos_compile` directory.
