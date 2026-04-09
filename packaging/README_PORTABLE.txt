================================================================================
  PKG Extractor — portable edition
================================================================================

No installer. No Python. No system Tcl/Tk packages required.

--------------------------------------------------------------------------------
  Linux
--------------------------------------------------------------------------------

  1. Unzip this folder anywhere you have write access (e.g. Desktop or USB).
  2. Double-click "Run.sh" or run in a terminal:

       ./Run.sh

  If the file manager blocks execution: right-click Run.sh → Properties →
  allow executing, or run: chmod +x Run.sh PKG-Extractor

--------------------------------------------------------------------------------
  Windows
--------------------------------------------------------------------------------

  1. Unzip this folder anywhere (e.g. Desktop or USB stick).
  2. Double-click "Run.bat" or "PKG-Extractor.exe".

  If SmartScreen warns about an unknown publisher: click "More info" →
  "Run anyway" (this is normal for unsigned portable apps).

--------------------------------------------------------------------------------
  Usage
--------------------------------------------------------------------------------

  Choose your wallpaper project folder → output folder → Extract.

  Every .pkg is unpacked with RePKG; TEX files are converted to images with the
  same binary. If the folder contains "repkg/RePKG" (Linux) or
  "repkg/RePKG.exe" (Windows), you do not need to set a path.

--------------------------------------------------------------------------------
  Bundled RePKG (MIT, notscuffed/repkg)
--------------------------------------------------------------------------------

  See repkg/THIRD-PARTY-NOTICES.txt. Linux build includes RePKG only if the
  packager had dotnet SDK; Windows includes RePKG.exe from the official release.

================================================================================
  PKG Extractor — портативная версия
================================================================================

Без установки. Без Python. Без пакета tk в системе.

--------------------------------------------------------------------------------
  Linux
--------------------------------------------------------------------------------

  1. Распакуй папку куда угодно (Рабочий стол, флешка).
  2. Запусти Run.sh двойным щелчком или в терминале: ./Run.sh

  Если не запускается: chmod +x Run.sh PKG-Extractor repkg/RePKG

  RePKG обязателен; если рядом лежит repkg/RePKG, путь не нужен.

--------------------------------------------------------------------------------
  Windows
--------------------------------------------------------------------------------

  1. Распакуй папку в любое место.
  2. Двойной щелчок по Run.bat или PKG-Extractor.exe.

================================================================================
