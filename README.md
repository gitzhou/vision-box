# Vision Box

## Build

- Mac

```sh
pyinstaller src/startup.py \
  -i resources/icon.icns \
  --windowed \
  --noconfirm \
  --collect-all mvclib \
  --collect-all coincurve \
  --add-data "src/contract/index.html:contract" \
  --add-data "src/contract/meta-contract.browser.min.js:contract" \
  --add-data "src/contract/meta-contract.js:contract" \
  --add-data "src/contract/qwebchannel.js:contract" \
  --name "Vision Box"
```

- Windows

```
pyinstaller src/startup.py -i resources/icon.ico --windowed --noconfirm --collect-all mvclib --collect-all coincurve --add-data "src/contract/index.html;contract" --add-data "src/contract/meta-contract.browser.min.js;contract" --add-data "src/contract/meta-contract.js;contract" --add-data "src/contract/qwebchannel.js;contract" --name "Vision Box"
```
