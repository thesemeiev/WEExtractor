#!/usr/bin/env python3
"""GUI: извлечение папки Wallpaper Engine (RePKG)."""

from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from we_repkg import resolve_repkg_executable
from we_wallpaper import extract_wallpaper_folder


def _resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _app_version() -> str:
    vf = _resource_root() / "VERSION"
    try:
        if vf.is_file():
            line = vf.read_text(encoding="utf-8").strip().splitlines()[0]
            return line.strip() or "1.0.0"
    except OSError:
        pass
    return "1.0.0"


class ExtractorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"Wallpaper Engine Extractor v{_app_version()}")
        self.root.geometry("720x520")
        self.root.minsize(640, 440)

        self.we_dir_var = tk.StringVar()
        self.we_out_var = tk.StringVar()
        self.we_desktop_var = tk.BooleanVar(value=True)
        self.we_repkg_path_var = tk.StringVar()

        self.status_var = tk.StringVar(value="Готово")

        self._build_ui()
        self._apply_window_icon()

    def _apply_window_icon(self) -> None:
        icon = _resource_root() / "assets" / "app_icon.png"
        if not icon.is_file():
            return
        try:
            img = tk.PhotoImage(file=str(icon))
            self.root.iconphoto(True, img)
            self.root._pkg_app_icon = img  # noqa: SLF001
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Папка одних обоев (Workshop): project.json, scene.pkg, preview.jpg, видео и т.д.",
            wraplength=680,
        ).pack(anchor="w", pady=(0, 8))

        self._row_dir(outer, "Папка обоев:", self.we_dir_var, self.pick_we_dir)
        self._row_dir(outer, "Папка вывода:", self.we_out_var, self.pick_output_we)
        ttk.Checkbutton(
            outer,
            text="Режим рабочего стола: без превью и мусора (крупные картинки/видео, без json/шейдеров)",
            variable=self.we_desktop_var,
        ).pack(anchor="w", pady=4)
        ttk.Label(
            outer,
            text="Каждый .pkg распаковывается через RePKG; в конце TEX → изображения. "
            "Путь ниже — только если не используется встроенный repkg/ рядом с программой.",
            wraplength=680,
        ).pack(anchor="w", pady=(4, 0))
        self._row_file(outer, "RePKG (опц.):", self.we_repkg_path_var, self.pick_repkg_exe)
        ttk.Button(outer, text="Извлечь обои", command=self.start_we_extract).pack(anchor="w", pady=8)

        ttk.Button(outer, text="Открыть папку вывода", command=self.open_output).pack(anchor="w", pady=(4, 0))

        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(6, 2))

        self.log = tk.Text(outer, height=12, wrap="word")
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        self._append_log(
            "Все .pkg через RePKG, затем конвертация .tex. "
            "Встроенный бинарник: папка repkg/ рядом с программой.\n"
        )
        self.log.configure(state="disabled")

    def _row_file(self, parent: ttk.Frame, label: str, var: tk.StringVar, cmd) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=18).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Обзор…", command=cmd).pack(side="left")

    def _row_dir(self, parent: ttk.Frame, label: str, var: tk.StringVar, cmd) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=18).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Обзор…", command=cmd).pack(side="left")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def pick_we_dir(self) -> None:
        p = filedialog.askdirectory(title="Папка обоев Wallpaper Engine")
        if p:
            self.we_dir_var.set(p)
            if not self.we_out_var.get().strip():
                self.we_out_var.set(str(Path(p).resolve().with_name(Path(p).name + "_WE_extracted")))

    def pick_output_we(self) -> None:
        p = filedialog.askdirectory(title="Папка вывода")
        if p:
            self.we_out_var.set(p)

    def pick_repkg_exe(self) -> None:
        p = filedialog.askopenfilename(
            title="Исполняемый файл RePKG",
            filetypes=[("Все", "*.*")],
        )
        if p:
            self.we_repkg_path_var.set(p)

    def open_output(self) -> None:
        out = self.we_out_var.get().strip()
        if not out:
            messagebox.showinfo("Папка", "Укажите папку вывода.")
            return
        p = Path(out).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        try:
            import webbrowser

            webbrowser.open(p.as_uri())
        except OSError:
            messagebox.showinfo("Папка", str(p))

    def start_we_extract(self) -> None:
        wd = self.we_dir_var.get().strip().strip('"')
        od = self.we_out_var.get().strip().strip('"')
        if not wd or not od:
            messagebox.showerror("Проверка", "Укажите папку обоев и папку вывода.")
            return
        src = Path(wd).expanduser().resolve()
        dst = Path(od).expanduser().resolve()
        if not src.is_dir():
            messagebox.showerror("Проверка", f"Нет такой папки:\n{src}")
            return
        desktop = bool(self.we_desktop_var.get())
        raw = self.we_repkg_path_var.get().strip().strip('"')
        explicit: Optional[Path] = None
        if raw:
            cand = Path(raw).expanduser().resolve()
            explicit = cand if cand.is_file() else None
            if explicit is None:
                messagebox.showerror("RePKG", f"Файл не найден:\n{raw}")
                return
        repkg_exe = resolve_repkg_executable(explicit)
        if repkg_exe is None:
            messagebox.showerror(
                "RePKG",
                "RePKG не найден.\n"
                "Укажите исполняемый файл выше, либо положите repkg/RePKG рядом с программой, либо добавьте в PATH.",
            )
            return
        self.status_var.set("Wallpaper Engine…")

        def log_cb(msg: str) -> None:
            self.root.after(0, lambda m=msg: self._append_log(m))

        threading.Thread(
            target=self._run_we,
            args=(src, dst, desktop, repkg_exe, log_cb),
            daemon=True,
        ).start()
        self._append_log(f"[WE] {src} -> {dst} (desktop={desktop}, repkg={repkg_exe})")

    def _run_we(
        self,
        src: Path,
        dst: Path,
        desktop: bool,
        repkg_exe: Path,
        log_cb,
    ) -> None:
        try:
            extract_wallpaper_folder(
                src,
                dst,
                desktop_mode=desktop,
                repkg_executable=repkg_exe,
                repkg_output_dir=None,
                log=log_cb,
            )
            self.root.after(0, lambda: self._finish_ok("Wallpaper Engine: готово (см. manifest.json)", dst))
        except Exception as exc:
            self.root.after(0, lambda: self._finish_error(exc, traceback.format_exc()))

    def _finish_ok(self, msg: str, output_path: Path) -> None:
        self.status_var.set(msg)
        self._append_log(msg + "\n")
        messagebox.showinfo("Готово", f"{msg}\n\n{output_path}")

    def _finish_error(self, exc: Exception, tb: str) -> None:
        self.status_var.set("Ошибка")
        self._append_log(str(exc))
        self._append_log(tb)
        messagebox.showerror("Ошибка", str(exc))


def main() -> int:
    root = tk.Tk()
    ExtractorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
