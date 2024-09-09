#!/bin/bash

### --- ADJUST VERSION, SYSTEM, AND SYSTEMVERSION TO MATCH THE SYSTEM: --- ###
VERSION=1.1.0
SYSTEM=ubuntu
SYSTEMVERSION=22.04
### ---------------------------------------------------------------------- ###

BASEDIR="./pod5viewer_${VERSION}_${SYSTEM}_${SYSTEMVERSION}"

echo "Running pyinstaller"
pyinstaller pod5Viewer.spec --noconfirm || exit 1

echo "Creating and populating folder ${BASEDIR}/usr/local/bin"

mkdir -p ${BASEDIR}/usr/local/bin
mv ./dist/pod5Viewer/* ${BASEDIR}/usr/local/bin/
rm -r ./dist ./build

cp ../images/icon.png ${BASEDIR}/usr/local/bin/

echo "Creating and populating folder ${BASEDIR}/DEBIAN"

mkdir -p ${BASEDIR}/DEBIAN
echo -e "Package: pod5viewer\nVersion: ${VERSION}\nSection: base\nPriority: optional\nArchitecture: amd64\nMaintainer: Vincent Dietrich <dietricv@uni-mainz.de>\nDescription: GUI for inspecting pod5 files\n The pod5Viewer is a Python application that provides a graphical user interface for viewing and navigating through POD5 files. \n It allows users to open multiple POD5 files, explore their contents, and display detailed data for selected read IDs.\n" \
    > ${BASEDIR}/DEBIAN/control
echo -e "#!/bin/bash\nset -e\n# Update MIME database\nupdate-mime-database /usr/share/mime\n# Update desktop database\nupdate-desktop-database /usr/share/applications\nexit 0\n" \
    > ${BASEDIR}/DEBIAN/postinst
chmod 0755 ${BASEDIR}/DEBIAN/postinst

echo "Creating and populating folder ${BASEDIR}/usr/share/applications"

mkdir -p ${BASEDIR}/usr/share/applications
echo -e "[Desktop Entry]\nVersion=${VERSION}\nName=pod5Viewer\nComment=View and navigate through POD5 files\nExec=/usr/local/bin/pod5Viewer %F\nIcon=/usr/local/bin/icon.png\nTerminal=false\nType=Application\nCategories=Utility;Viewer;\nMimeType=application/x-pod5;\n" \
    > ${BASEDIR}/usr/share/applications/pod5Viewer.desktop

echo "Creating and populating folder ${BASEDIR}/usr/share/mime/packages"

mkdir -p ${BASEDIR}/usr/share/mime/packages
echo -e "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<mime-info xmlns=\"http://www.freedesktop.org/standards/shared-mime-info\">\n    <mime-type type=\"application/x-pod5\">\n        <comment>POD5 file</comment>\n        <glob pattern=\"*.pod5\"/>\n    </mime-type>\n</mime-info>" \
    > ${BASEDIR}/usr/share/mime/packages/pod5viewer.xml

echo "Compiling deb package"

dpkg-deb --build ${BASEDIR} || exit 1

echo "Cleaning up"
rm -r ${BASEDIR}
