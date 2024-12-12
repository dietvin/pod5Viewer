# Compile pod5Viewer to a Snap package

To compile the pod5Viewer to an installable snap package, follow the following instructions:

1. Make sure snapcraft is installed and configured
2. Change directory to `./compile_snap`
3. Adjust the version [`snap/snapcraft.yaml` and `snap/gui/pod5viewer.desktop`
4. run `snapcraft` in the command line

If the script runs successfully the snap file `pod5viewer_<version>_amd64.snap` will be placed in the `compile_snap` directory.
