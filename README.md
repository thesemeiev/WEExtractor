# Wallpaper Engine Extractor

## Скачать (без установки Python)

Готовые портативные сборки лежат в разделе **Releases** твоего репозитория на GitHub: открой страницу репозитория → **Releases** → последняя версия → скачай архив для Windows (zip) или Linux (zip/tar.gz), распакуй и запусти `Run.sh` / `PKG-Extractor.exe`.

Исходный код клонируется отдельно; для пользователей достаточно релиза.

---

## Wallpaper Engine — папка обоев

Укажи **одну папку** проекта (как в Workshop: `…/workshop/content/431960/<id>/`).

Все файлы `*.pkg` распаковываются **только через [RePKG](https://github.com/notscuffed/repkg)** (notscuffed/repkg). После распаковки тот же бинарник конвертирует найденные `.tex` в изображения (каталог `tex_png/` по умолчанию).

**CLI:**

```bash
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output"
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output" --desktop
# Явный путь к RePKG (иначе — встроенный в сборке, third_party/repkg/* или PATH):
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output" --repkg /path/to/RePKG
```

Опции:

- `--desktop` — режим «как обои на стол»: в `loose/` не копируются превью, мелкие картинки, `.json`, веб-стек (кроме type=web), аудио; после распаковки каждого пакета RePKG лишние файлы **удаляются** из соответствующей папки в `pkg/`. Пороги: `--min-image-w`, `--min-image-h` (по умолчанию 640×480), `--min-video-bytes` (по умолчанию 100000).
- `--repkg` — без аргумента: встроенный рядом с программой или `PATH`; с путём — конкретный исполняемый файл.
- `--tex-png-dir` — куда писать картинки из `.tex` (по умолчанию `<output>/tex_png`).

**Результат в `output`:**

- `loose/` — все файлы **кроме** `.pkg`, дерево путей как в исходной папке.
- `pkg/<имя>/` — содержимое каждого `*.pkg` после **RePKG extract**.
- `tex_png/` (или `--tex-png-dir`) — результат **RePKG** для `.tex` по всему дереву вывода.
- `manifest.json` — отчёт (в т.ч. код выхода RePKG по каждому пакету).

Если RePKG завершился с ошибкой для конкретного `.pkg`, в `manifest.json` будет запись об ошибке.

**GUI:** ищет RePKG (встроенный `repkg/`, опциональный путь в поле, затем `PATH`).

---

## Встроенный RePKG в портативной сборке

- **Windows:** `build_portable_windows.ps1` скачивает официальный `RePKG.zip` и кладёт `repkg/RePKG.exe` в папку сборки.
- **Linux:** перед PyInstaller запускается `scripts/bundle_repkg_linux.sh` (нужны **git** и **dotnet SDK 8+**). Собирается self-contained `RePKG` под `linux-x64` и копируется в `repkg/RePKG`. Если `dotnet` нет — сборка идёт дальше, но встроенного бинарника не будет (нужен RePKG в `PATH` или поле в GUI).

Исходники и лицензия RePKG: [notscuffed/repkg](https://github.com/notscuffed/repkg) (MIT). Уведомления см. `repkg/THIRD-PARTY-NOTICES.txt` в сборке.

---

## Сборка портативной версии

См. `build_portable_linux.sh` / `build_portable_windows.ps1` (нужны Python, tkinter, PyInstaller).

```bash
chmod +x build_portable_linux.sh
./build_portable_linux.sh
```

Запуск: `dist/PKG-Extractor-Portable-Linux/Run.sh`

---

## Файлы

| Модуль | Назначение |
|--------|------------|
| `we_wallpaper.py` | Папка обоев → loose + pkg (RePKG) + TEX + manifest |
| `we_media_filter.py` | Эвристики для `--desktop` и подрезки дерева после RePKG |
| `we_repkg.py` | Поиск встроенного RePKG, вызов extract / TEX |
| `scripts/bundle_repkg_linux.sh` | Сборка RePKG для Linux при `build_portable_linux.sh` |
| `pkg_extractor_gui.py` | Tk GUI |
