#!/bin/bash

# Script must be executed from the base directory of the repository!

echo "Building pip package"
# https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
python3 -m pip install --upgrade build
python -m build

echo "Uploading pip package"
# https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives
python3 -m pip install --upgrade twine
python3 -m twine upload dist/*

echo "Cleaning up"
rm -r dist pod5Viewer.egg-info

