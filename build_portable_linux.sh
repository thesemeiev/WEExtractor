#!/usr/bin/env bash
# Собирает портативную папку + ZIP: распаковал — запустил, без установки в систему.
# На машине сборки нужны Python 3, pip и рабочий tkinter (Arch: sudo pacman -S tk).
#
# Сборка на стабильной версии Python (рекомендуется для PyInstaller):
#   PYTHON_BIN=python3.12 ./build_portable_linux.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON}" >/dev/null 2>&1; then
  echo "Не найден интерпретатор: ${PYTHON}"
  echo "Укажи другой, например: PYTHON_BIN=python3.12 ./build_portable_linux.sh"
  exit 1
fi

PY_MINOR="$("${PYTHON}" -c 'import sys; print(sys.version_info.minor)')"
if [[ "$("${PYTHON}" -c 'import sys; print(sys.version_info.major)')" -eq 3 ]] && [[ "${PY_MINOR}" -ge 13 ]]; then
  echo "Внимание: Python 3.${PY_MINOR} с PyInstaller иногда даёт сбои. Надёжнее собрать на 3.11 или 3.12:"
  echo "  sudo pacman -S python312   # или pyenv"
  echo "  PYTHON_BIN=python3.12 ./build_portable_linux.sh"
  echo ""
fi

if ! "${PYTHON}" -c "import tkinter" 2>/dev/null; then
  echo "Ошибка: не работает import tkinter для ${PYTHON}."
  echo "Установи Tcl/Tk (например Arch: sudo pacman -S tk) — только на этом ПК для сборки."
  exit 1
fi

chmod +x "${SCRIPT_DIR}/scripts/bundle_repkg_linux.sh"
bash "${SCRIPT_DIR}/scripts/bundle_repkg_linux.sh"

"${PYTHON}" -m venv .venv-build
# shellcheck disable=SC1091
source .venv-build/bin/activate
python -m pip install -U pip wheel
python -m pip install -r requirements-build.txt

# Полная очистка: без этого PyInstaller иногда падает на COLLECT (os.remove на каталог + rmtree).
chmod -R u+w build dist 2>/dev/null || true
rm -rf build dist
rm -f "${SCRIPT_DIR}/PKG-Extractor.spec"

python -m PyInstaller \
  --onedir \
  --noconsole \
  --clean \
  --noconfirm \
  --name PKG-Extractor \
  --hidden-import we_wallpaper \
  --hidden-import we_media_filter \
  --hidden-import we_repkg \
  --collect-all tkinter \
  --add-data "assets/app_icon.png:assets" \
  --add-data "VERSION:." \
  pkg_extractor_gui.py

rm -f "${SCRIPT_DIR}/PKG-Extractor.spec"

PORTABLE="dist/PKG-Extractor-Portable-Linux"
rm -rf "${PORTABLE}"
mv dist/PKG-Extractor "${PORTABLE}"

chmod +x "${PORTABLE}/PKG-Extractor"

if [[ -f "${SCRIPT_DIR}/third_party/repkg/linux/RePKG" ]]; then
  mkdir -p "${PORTABLE}/repkg"
  cp -f "${SCRIPT_DIR}/third_party/repkg/linux/RePKG" "${PORTABLE}/repkg/RePKG"
  chmod +x "${PORTABLE}/repkg/RePKG"
  for f in THIRD-PARTY-NOTICES.txt LICENSE-RePKG.txt; do
    if [[ -f "${SCRIPT_DIR}/third_party/repkg/linux/${f}" ]]; then
      cp -f "${SCRIPT_DIR}/third_party/repkg/linux/${f}" "${PORTABLE}/repkg/"
    fi
  done
  echo "В портативку добавлен repkg/RePKG (notscuffed/repkg)."
else
  echo "Внимание: встроенный RePKG для Linux не собран (нужны git + dotnet при сборке). Укажи RePKG в PATH или в GUI."
fi

cat > "${PORTABLE}/Run.sh" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
exec ./PKG-Extractor "$@"
EOS
chmod +x "${PORTABLE}/Run.sh"

cp -f packaging/README_PORTABLE.txt "${PORTABLE}/README.txt"
cp -f VERSION "${PORTABLE}/VERSION.txt"

ZIP="dist/PKG-Extractor-Portable-Linux.zip"
rm -f "${ZIP}"
if command -v zip >/dev/null 2>&1; then
  (cd dist && zip -qr "$(basename "${ZIP}")" "$(basename "${PORTABLE}")")
  echo ""
  echo "ZIP: ${SCRIPT_DIR}/${ZIP}"
else
  echo ""
  echo "Подсказка: установи zip для архива: sudo pacman -S zip"
fi

echo ""
echo "Портативная папка: ${SCRIPT_DIR}/${PORTABLE}"
echo "Запуск: ${PORTABLE}/Run.sh  или  ./PKG-Extractor внутри этой папки"
echo ""
echo "=== Важно ==="
echo "НЕ запускай бинарник из каталога build/ — это не готовая сборка, будет ошибка libpython."
echo "Только: ${SCRIPT_DIR}/${PORTABLE}/PKG-Extractor"
