# Compiling the pod5Viewer for Ubuntu systems

## Compile python code to executable binaries
Spec file:
```
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../pod5Viewer/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('../pod5Viewer/icon.ico', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pod5Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../pod5Viewer/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pod5Viewer',
)
```
Use pyinstaller with spec file:
```bash
pyinstaller pod5Viewer.spec --noconfirm
```
