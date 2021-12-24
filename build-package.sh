
# check if pyinstaller is installed
pip show pyinstaller
if [ $? -eq 1 ]; then
    pip install pyinstaller
fi

pyinstaller --noconfirm\
    --windowed\
    --name=CodeRypl\
    code_rypl/__main__.py
    # --icon=icon.ico\