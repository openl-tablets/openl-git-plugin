pyinstaller --onefile src/diff.py --name=git-openl-diff --add-data='src/config.properties:.'
pyinstaller --onefile src/cli.py --name=git-openl --add-data='src/config.properties:.'