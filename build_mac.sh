rm -rf __pycache__
rm -rf build
rm -rf dist
rm -rf updater.spec
rm -rf mac
pyinstaller --clean --onefile compress.py
cp config.ini dist
cp eicar.com dist
cp あああ.txt dist
mv dist mac