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


## Set up DEB package

Folder structure for the DEB package:

```
pod5viewer_<version>
|--DEBIAN
   |--control
   |--postinst
|--usr
   |--local
      |--bin
         |--_internal
	    |--...
	 |--icon.ico
	 |--pod5Viewer
  |--share
     |--applications
        |--pod5Viewer.desktop
     |--mime
	|--packages
	   |--pod5viewer.xml
```
Copy the _internal folder, the icon file and the binary into the usr/local/bin folder. Contents of the other files:

- control:
    ```
    Package: pod5viewer
    Version: 1.0.1
    Section: base
    Priority: optional
    Architecture: amd64
    Maintainer: Vincent Dietrich <dietricv@uni-mainz.de>
    Description: GUI for inspecting pod5 files
    The pod5Viewer is a Python application that provides a graphical user interface for viewing and navigating through POD5 files. 
    It allows users to open multiple POD5 files, explore their contents, and display detailed data for selected read IDs.

    ```

- postinst
    ```
    #!/bin/bash
    set -e

    # Update MIME database
    update-mime-database /usr/share/mime

    # Update desktop database
    update-desktop-database /usr/share/applications

    exit 0
    ```
- pod5Viewer.desktop
    ```
    [Desktop Entry]
    Version=1.0.1
    Name=Pod5 Viewer
    Comment=View and navigate through POD5 files
    Exec=/usr/local/bin/pod5Viewer %F
    Icon=/usr/local/bin/icon.ico
    Terminal=false
    Type=Application
    Categories=Utility;Viewer;
    MimeType=application/x-pod5;
    ```
- pod5viewer.xml
    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
        <mime-type type="application/x-pod5">
            <comment>POD5 file</comment>
            <glob pattern="*.pod5"/>
        </mime-type>
    </mime-info>
    ```

Compile the package:
```bash
dpkg-deb --build pod5viewer_1.0.1
```