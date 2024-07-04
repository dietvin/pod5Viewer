# Compile pod5Viewer to DEB package

To compile the pod5Viewer to Windows installer, follow the following instructions:

1. Make sure the pyinstaller is installed and iscc is available in the command line
2. In a PowerShell change directory to `./windows_compile`
3. Adjust the VERSION `create_installer.ps1`
4. run `create_installer.ps1`

If the script runs successfully the DEB `pod5viewer-VERSION-Setup.exe` will be placed in the `windows_compile` directory.
