#!/usr/bin/env bash
# Скачивает исходники RePKG (MIT) и собирает self-contained бинарник для linux-x64.
# Нужны: git, dotnet SDK 8+.
# Результат: ../third_party/repkg/linux/RePKG (+ THIRD-PARTY-NOTICES.txt)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT="${ROOT}/third_party/repkg/linux"
REPKG_TAG="${REPKG_TAG:-v0.4.0-alpha}"
SRC="${ROOT}/.build-repkg-src"

rm -rf "${SRC}"
mkdir -p "${OUT}"

if ! command -v dotnet >/dev/null 2>&1; then
  echo "[bundle_repkg_linux] dotnet не найден — пропуск (установи dotnet-sdk для встраивания RePKG в Linux-сборку)."
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[bundle_repkg_linux] git не найден — пропуск."
  exit 0
fi

echo "[bundle_repkg_linux] клон notscuffed/repkg @ ${REPKG_TAG}…"
if ! git clone --depth 1 --branch "${REPKG_TAG}" https://github.com/notscuffed/repkg.git "${SRC}"; then
  echo "[bundle_repkg_linux] git clone не удался — сборка PKG-Extractor продолжится без встроенного RePKG."
  rm -rf "${SRC}"
  exit 0
fi

CSPROJ="${SRC}/RePKG/RePKG.csproj"
if [[ ! -f "${CSPROJ}" ]]; then
  echo "[bundle_repkg_linux] не найден ${CSPROJ}"
  exit 0
fi

# net472 под Linux не соберётся — переключаем на net8.0 (обычно достаточно для этого проекта).
sed -i 's/<TargetFramework>net472<\/TargetFramework>/<TargetFramework>net8.0<\/TargetFramework>/' "${CSPROJ}"

echo "[bundle_repkg_linux] dotnet publish linux-x64…"
if ! dotnet publish "${SRC}/RePKG/RePKG.csproj" \
  -c Release \
  -r linux-x64 \
  --self-contained true \
  -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true \
  -o "${OUT}"; then
  echo "[bundle_repkg_linux] сборка RePKG не удалась — продолжим без встроенного бинарника."
  rm -rf "${SRC}"
  exit 0
fi

BIN="${OUT}/RePKG"
if [[ ! -f "${BIN}" ]]; then
  echo "[bundle_repkg_linux] ожидался ${BIN}, не найден."
  rm -rf "${SRC}"
  exit 0
fi

chmod +x "${BIN}"
if [[ -f "${SRC}/THIRD-PARTY-NOTICES.txt" ]]; then
  cp -f "${SRC}/THIRD-PARTY-NOTICES.txt" "${OUT}/"
fi
if [[ -f "${SRC}/LICENSE" ]]; then
  cp -f "${SRC}/LICENSE" "${OUT}/LICENSE-RePKG.txt"
fi

rm -rf "${SRC}"
echo "[bundle_repkg_linux] готово: ${BIN}"
