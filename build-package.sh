#!/bin/bash

# make build-time version of the source
rm -rf build
mkdir build
cp -r code_rypl/ build/code_rypl_build/

# freeze the version info
python3 build/code_rypl_build/versioning.py --pre-process-in-place

# package the source
pyinstaller --noconfirm\
    --windowed\
    --name=CodeRypl\
    build/code_rypl_build/__main__.py
    # --icon=icon.ico\