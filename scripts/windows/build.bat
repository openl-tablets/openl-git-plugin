@ECHO OFF
python -c "import sys;print('x64' if sys.maxsize > 2**32 else 'x86')" > PYTHON_ARCH
set /p PYTHON_ARCH= < PYTHON_ARCH
del PYTHON_ARCH

pyinstaller --onefile .\src\diff.py --name=git-openl-diff-%PYTHON_ARCH%.exe
pyinstaller --onefile .\src\cli.py --name=git-openl-%PYTHON_ARCH%.exe