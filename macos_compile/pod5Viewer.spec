# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../pod5Viewer/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('../pod5Viewer/icon.ico', '.'),],
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
    icon=['../images/icon.png'],
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

app = BUNDLE(
    coll,
    name='pod5Viewer',
    icon='icon.icns',
    info_plist={
        'CFBundleVersion': '1.0.2',
        'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'POD5 File',
                    'CFBundleTypeIconFile': 'icon.icns',
                    'CFBundleTypeRole': 'Viewer',
                    'LSItemContentTypes': ['public.data'],
                    'LSHandlerRank': 'Owner',
                    'CFBundleTypeExtensions': ['pod5']
                    }
                ]
    }
)
