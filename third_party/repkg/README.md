# RePKG (сторонний компонент)

Бинарники **не хранятся в git**. Их создаёт сборка:

- **Linux:** `scripts/bundle_repkg_linux.sh` (нужны `git` и **dotnet SDK 8+**) → `linux/RePKG`
- **Windows:** `build_portable_windows.ps1` качает [релиз](https://github.com/notscuffed/repkg/releases) → `repkg/RePKG.exe` внутри портативной папки

Исходный проект: [notscuffed/repkg](https://github.com/notscuffed/repkg) (MIT).
