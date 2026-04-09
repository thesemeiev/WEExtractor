# Wallpaper Engine Extractor

Небольшая утилита: берёшь **одну папку обоев** из Workshop (ту, где лежат `project.json`, `scene.pkg` и остальное), на выходе получаешь аккуратно разложенные файлы и картинки из текстур.  
Python на компьютере пользователю **не нужен** — в [релизах](https://github.com/thesemeiev/WEExtractor/releases/latest) лежат готовые архивы.

[![Версия](https://img.shields.io/github/v/release/thesemeiev/WEExtractor?label=релиз&logo=github)](https://github.com/thesemeiev/WEExtractor/releases/latest)

---

## Скачать и запустить

| | |
|--|--|
| **Сборки** | [**Releases → Latest**](https://github.com/thesemeiev/WEExtractor/releases/latest) — скачай zip под свою систему. |
| **Код** | [Репозиторий](https://github.com/thesemeiev/WEExtractor) — если хочешь собрать сам или помочь с проектом. |

**Linux:** распакуй архив → зайди в папку → `./Run.sh` (или запусти `PKG-Extractor`).  
Если не стартует: `chmod +x Run.sh PKG-Extractor repkg/RePKG`.

**Windows:** распакуй → `Run.bat` или `PKG-Extractor.exe`.

Внутри архива рядом с программой лежит папка **`repkg/`** с [RePKG](https://github.com/notscuffed/repkg) — так не нужно ничего ставить в систему. Если её нет (редкая сборка без dotnet), укажи путь к RePKG вручную в окне программы или положи его в `PATH`.

---

## Что она делает

1. Копирует «рассыпные» файлы обоев (превью, видео, json и т.д.) в подпапку **`loose/`** — структура путей как в оригинале.  
2. Каждый **`*.pkg`** распаковывает через **RePKG** — в **`pkg/<имя пакета>/`**.  
3. В конце прогоняет тот же RePKG по **`.tex`** и складывает картинки в **`tex_png/`** (или в папку из опции `--tex-png-dir` в консоли).  
4. Пишет **`manifest.json`** — что произошло и если что-то пошло не так.

Отдельный установщик не нужен: распаковал папку — работаешь из неё.

---

## Окно программы (GUI)

1. Укажи **папку обоев** — обычно что-то вроде  
   `…/steam/steamapps/workshop/content/431960/<id>/`
2. Укажи **куда сохранить** результат.
3. Включи или выключи **режим рабочего стола** (см. ниже).
4. Поле **RePKG** можно оставить пустым, если в архиве есть `repkg/RePKG` (Linux) или `repkg/RePKG.exe` (Windows).
5. **Извлечь обои** — дождись окончания, лог смотри внизу окна.

Кнопка **«Открыть папку вывода»** — открывает проводником каталог с результатом.

---

## Режим рабочего стола

Когда включён, программа старается оставить то, что имеет смысл как **картинка или видео для стола**: без мелких превью, лишних json, шейдеров и аудио.  
Для содержимого пакетов после распаковки лишние файлы **удаляются** из деревьев в `pkg/`, чтобы не копить мусор.

Пороги размера картинок и видео можно подстроить в консоли (`--min-image-w`, `--min-image-h`, `--min-video-bytes`).

---

## Консоль (для своих скриптов)

Нужны установленные **Python 3** и зависимости из репозитория (для разработки). Примеры:

```bash
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output"
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output" --desktop
python3 we_wallpaper.py "/path/to/wallpaper_folder" -o "/path/to/output" --repkg /path/to/RePKG
```

- **`--repkg`** без пути — ищется встроенный рядом с проектом или в `PATH`.  
- **`--tex-png-dir`** — куда сложить картинки из `.tex` (по умолчанию `<output>/tex_png`).

---

## RePKG и лицензии

Распаковка пакетов и конвертация текстур опирается на открытый проект **[notscuffed/repkg](https://github.com/notscuffed/repkg)** (MIT).  
В портативной сборке лежат его уведомления и лицензии в **`repkg/`** (в т.ч. `THIRD-PARTY-NOTICES.txt`).

Сборка **Linux** при желании сама собирает RePKG из исходников (`scripts/bundle_repkg_linux.sh`, нужны **git** и **dotnet**).  
**Windows**-скрипт сборки подтягивает готовый бинарник из релизов RePKG.

---

## Собрать портативку самому

На машине, где ставишь только **для сборки**: Python 3, **tkinter**, **PyInstaller** (ставится скриптом в виртуальное окружение).

```bash
chmod +x build_portable_linux.sh
./build_portable_linux.sh
```

Готовая папка: **`dist/PKG-Extractor-Portable-Linux/`**.  
Если PyInstaller капризничает на свежем Python, попробуй:

```bash
PYTHON_BIN=python3.12 ./build_portable_linux.sh
```

На Windows: **`build_portable_windows.ps1`** в PowerShell (нужны Python с tkinter и доступ в интернет для загрузки RePKG).

---

## Файлы в репозитории

| Файл | Зачем |
|------|--------|
| `pkg_extractor_gui.py` | Окно программы |
| `we_wallpaper.py` | Логика: папка → loose, pkg, tex, manifest |
| `we_repkg.py` | Запуск RePKG |
| `we_media_filter.py` | Фильтры для режима рабочего стола |
| `build_portable_linux.sh` / `build_portable_windows.ps1` | Сборка «распаковал — запустил» |
| `scripts/bundle_repkg_linux.sh` | Сборка RePKG под Linux |

---

Если что-то не взлетело — загляни в **`manifest.json`** в папке вывода или открой [Issues](https://github.com/thesemeiev/WEExtractor/issues) в репозитории.
