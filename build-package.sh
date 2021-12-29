#!/bin/bash

# make build-time version of the source
rm -rf build
mkdir build
cp -r code_rypl/ build/code_rypl/

# freeze the version info, pass through build mode ($@)
python3 build/code_rypl/versioning.py --pre-process-in-place $@

# package the source
pyinstaller --noconfirm\
    --windowed\
    --name=CodeRypl\
    build/code_rypl/__main__.py
# --icon=icon.ico\