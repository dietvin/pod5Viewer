# Compile pod5Viewer to DEB package

To compile the pod5Viewer to an installable DEB package, follow the following instructions:

1. Make sure the pyinstaller is installed
2. Change directory to `./linux_compile`
3. Adjust the VERSION, SYSTEM and SYSTEMVERSION variables in `create_deb.sh`
4. run `create_deb.sh`

If the script runs successfully the DEB `pod5viewer_VERSION_SYSTEM_SYSTEMVERSION.deb` will be placed in the `linux_compile` directory.
