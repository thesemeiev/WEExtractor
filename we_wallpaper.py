#!/usr/bin/env python3
"""
Extract a single Wallpaper Engine workshop / project folder:
  - copies loose files (json, preview, video, web, etc.) preserving paths
  - unpacks every *.pkg with RePKG (notscuffed/repkg)
  - optional --desktop: skip previews, json, tiny images, shaders, audio; then prune unpacked pkg trees
  - TEX → images via RePKG at the end (same binary)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from we_media_filter import make_loose_copy_filter, prune_pkg_tree_for_desktop
from we_repkg import resolve_repkg_executable, run_repkg_extract_pkg, run_repkg_tex_convert

LogFn = Callable[[str], None]


def _default_log(msg: str) -> None:
    print(msg, flush=True)


def extract_wallpaper_folder(
    wallpaper_dir: Path,
    output_dir: Path,
    *,
    desktop_mode: bool = False,
    min_image_w: int = 640,
    min_image_h: int = 480,
    min_video_bytes: int = 100_000,
    repkg_executable: Path,
    repkg_output_dir: Optional[Path] = None,
    log: LogFn = _default_log,
) -> dict:
    """
    wallpaper_dir: folder that contains project.json, scene.pkg, etc.
    output_dir: root for extraction (created if needed).
    repkg_executable: path to RePKG binary (required).
    """
    wallpaper_dir = wallpaper_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    repkg_executable = repkg_executable.expanduser().resolve()
    if not wallpaper_dir.is_dir():
        raise FileNotFoundError(f"Not a directory: {wallpaper_dir}")
    if not repkg_executable.is_file():
        raise FileNotFoundError(f"RePKG not found: {repkg_executable}")

    output_dir.mkdir(parents=True, exist_ok=True)
    loose_root = output_dir / "loose"
    pkg_root = output_dir / "pkg"
    loose_root.mkdir(exist_ok=True)

    project_type = ""
    pj_path = wallpaper_dir / "project.json"
    pj_parse_error: str | None = None
    if pj_path.is_file():
        try:
            proj = json.loads(pj_path.read_text(encoding="utf-8"))
            project_type = str(proj.get("type", "")).lower()
        except (OSError, json.JSONDecodeError) as exc:
            pj_parse_error = str(exc)

    loose_filter = make_loose_copy_filter(
        desktop_mode=desktop_mode,
        min_image_w=min_image_w,
        min_image_h=min_image_h,
        min_video_bytes=min_video_bytes,
        project_type=project_type,
    )

    manifest: dict = {
        "source": str(wallpaper_dir),
        "output": str(output_dir),
        "desktop_mode": desktop_mode,
        "project_type": project_type or None,
        "min_image": [min_image_w, min_image_h],
        "min_video_bytes": min_video_bytes,
        "repkg": str(repkg_executable),
        "loose_files": [],
        "packages": [],
        "errors": [],
    }

    if pj_parse_error:
        manifest["errors"].append(f"project.json: {pj_parse_error}")

    pkg_files: list[Path] = []

    for path in sorted(wallpaper_dir.rglob("*")):
        if path.is_dir():
            continue
        try:
            rel = path.relative_to(wallpaper_dir)
        except ValueError:
            continue
        if path.suffix.lower() == ".pkg":
            pkg_files.append(path)
            continue
        if not loose_filter(rel, path):
            log(f"[loose skip] {rel}")
            continue
        dest = loose_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        manifest["loose_files"].append({"from": str(rel), "to": str(dest)})
        log(f"[loose] {rel}")

    for pkg in sorted(pkg_files):
        target = pkg_root / pkg.stem
        target.mkdir(parents=True, exist_ok=True)
        try:
            runpack = run_repkg_extract_pkg(repkg_executable, pkg, target, log=log)
            ok = runpack.get("returncode") == 0
            entry: dict = {
                "pkg": str(pkg),
                "stem": pkg.stem,
                "repkg_unpack": runpack,
            }
            if not ok:
                err = f"{pkg.name}: RePKG exit {runpack.get('returncode')}"
                manifest["errors"].append(err)
                log(f"[pkg ERROR] {err}")
            else:
                log(f"[pkg] {pkg.name} -> {target} (RePKG)")
                if desktop_mode:
                    prune_pkg_tree_for_desktop(
                        target,
                        min_image_w=min_image_w,
                        min_image_h=min_image_h,
                        min_video_bytes=min_video_bytes,
                        log=log,
                    )
            manifest["packages"].append(entry)
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
            err = f"{pkg.name}: {exc}"
            manifest["errors"].append(err)
            manifest["packages"].append({"pkg": str(pkg), "stem": pkg.stem, "error": str(exc)})
            log(f"[pkg ERROR] {err}")

    exe = repkg_executable
    tex_out = (repkg_output_dir or (output_dir / "tex_png")).expanduser().resolve()
    n_tex = sum(1 for _ in output_dir.rglob("*.tex"))
    if not exe.is_file():
        manifest["errors"].append(f"RePKG не найден: {exe}")
        manifest["repkg_tex"] = {"skipped": "executable_missing"}
    elif n_tex == 0:
        log("[repkg] нет .tex под каталогом вывода — пропуск конвертации TEX")
        manifest["repkg_tex"] = {"skipped": "no_tex_files"}
    else:
        log(f"[repkg] найдено .tex: {n_tex}, вывод изображений → {tex_out}")
        try:
            rinfo = run_repkg_tex_convert(exe, output_dir, tex_out, log=log)
            manifest["repkg_tex"] = rinfo
            if rinfo.get("returncode", 1) != 0:
                manifest["errors"].append(f"RePKG TEX: код {rinfo.get('returncode')}")
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
            err = f"RePKG TEX: {exc}"
            manifest["errors"].append(err)
            manifest["repkg_tex"] = {"error": str(exc)}
            log(err)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"[done] manifest: {manifest_path}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Wallpaper Engine wallpaper folder (loose files + RePKG for each .pkg).",
    )
    parser.add_argument("wallpaper_dir", help="Path to one wallpaper project folder")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output directory",
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Только крупные картинки/видео: без превью, json, шейдеров, аудио; подрезка содержимого pkg после RePKG.",
    )
    parser.add_argument(
        "--min-image-w",
        type=int,
        default=640,
        help="Мин. ширина изображения в режиме --desktop (по умолчанию 640)",
    )
    parser.add_argument(
        "--min-image-h",
        type=int,
        default=480,
        help="Мин. высота изображения в режиме --desktop (по умолчанию 480)",
    )
    parser.add_argument(
        "--min-video-bytes",
        type=int,
        default=100_000,
        help="Мин. размер видеофайла в байтах для --desktop (по умолчанию 100000)",
    )
    parser.add_argument(
        "--repkg",
        nargs="?",
        const="__bundle__",
        default="__bundle__",
        metavar="EXE",
        help="Исполняемый файл RePKG; без значения — встроенный рядом с программой или в PATH",
    )
    parser.add_argument(
        "--tex-png-dir",
        default=None,
        help="Куда писать картинки из RePKG (по умолчанию <output>/tex_png)",
    )
    args = parser.parse_args()

    if args.repkg == "__bundle__":
        exe = resolve_repkg_executable(None)
    else:
        exe = resolve_repkg_executable(Path(args.repkg).expanduser().resolve())
    if exe is None:
        print(
            "RePKG не найден. Укажи путь: --repkg /path/to/RePKG\n"
            "Или положи бинарник в third_party/repkg/<linux|win>/ или в PATH.",
            flush=True,
        )
        return 1

    tex_dir = Path(args.tex_png_dir).expanduser().resolve() if args.tex_png_dir else None
    extract_wallpaper_folder(
        Path(args.wallpaper_dir),
        Path(args.output),
        desktop_mode=args.desktop,
        min_image_w=args.min_image_w,
        min_image_h=args.min_image_h,
        min_video_bytes=args.min_video_bytes,
        repkg_executable=exe,
        repkg_output_dir=tex_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
