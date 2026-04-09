#!/usr/bin/env python3
"""
Интеграция с notscuffed/repkg (C#): распаковка .pkg и TEX → изображения.

Binary: https://github.com/notscuffed/repkg/releases
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional

LogFn = Callable[[str], None]


def _default_log(msg: str) -> None:
    print(msg, flush=True)


def bundled_repkg_candidates() -> List[Path]:
    """
    Порядок: рядом с exe (портативка), затем third_party при запуске из исходников.
    """
    paths: List[Path] = []
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
        name = "RePKG.exe" if sys.platform == "win32" else "RePKG"
        paths.append(base / "repkg" / name)
    else:
        root = Path(__file__).resolve().parent
        if sys.platform == "win32":
            paths.append(root / "third_party" / "repkg" / "win" / "RePKG.exe")
        else:
            paths.append(root / "third_party" / "repkg" / "linux" / "RePKG")
        name = "RePKG.exe" if sys.platform == "win32" else "RePKG"
        paths.append(root / "repkg" / name)
    return paths


def bundled_repkg_path() -> Optional[Path]:
    for p in bundled_repkg_candidates():
        if p.is_file():
            return p.resolve()
    return None


def resolve_repkg_executable(explicit: Optional[Path]) -> Optional[Path]:
    if explicit is not None:
        p = explicit.expanduser().resolve()
        if p.is_file():
            return p
    b = bundled_repkg_path()
    if b is not None:
        return b
    for name in ("RePKG", "repkg", "RePKG.exe"):
        found = shutil.which(name)
        if found:
            return Path(found).resolve()
    return None


def run_repkg_extract_pkg(
    repkg_exe: Path,
    pkg_path: Path,
    output_dir: Path,
    *,
    log: LogFn = _default_log,
    timeout: int = 600,
) -> dict:
    """
    Run: repkg extract --overwrite -o <output_dir> <pkg_path>
    Uses RePKG's own PKG reader when our Python PKGV parser fails.
    """
    repkg_exe = repkg_exe.expanduser().resolve()
    pkg_path = pkg_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not repkg_exe.is_file():
        raise FileNotFoundError(f"RePKG executable not found: {repkg_exe}")
    if not pkg_path.is_file():
        raise FileNotFoundError(f"PKG not found: {pkg_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(repkg_exe),
        "extract",
        "--overwrite",
        "-o",
        str(output_dir),
        str(pkg_path),
    ]
    log(f"[repkg unpack] {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(output_dir.parent),
    )
    if proc.stdout:
        for line in proc.stdout.splitlines()[-20:]:
            log(f"[repkg] {line}")
    if proc.returncode != 0 and (proc.stderr or "").strip():
        log(f"[repkg stderr]\n{(proc.stderr or '')[-2000:]}")

    return {
        "executable": str(repkg_exe),
        "pkg": str(pkg_path),
        "output": str(output_dir),
        "returncode": proc.returncode,
    }


def run_repkg_tex_convert(
    repkg_exe: Path,
    input_dir: Path,
    output_dir: Path,
    *,
    log: LogFn = _default_log,
) -> dict:
    """
    Run: repkg extract -t -r --overwrite -o <output_dir> <input_dir>
    Recursively finds .tex under input_dir and writes images under output_dir.
    """
    repkg_exe = repkg_exe.expanduser().resolve()
    input_dir = input_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not repkg_exe.is_file():
        raise FileNotFoundError(f"RePKG executable not found: {repkg_exe}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(repkg_exe),
        "extract",
        "-t",
        "-r",
        "--overwrite",
        "-o",
        str(output_dir),
        str(input_dir),
    ]
    log(f"[repkg] {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=3600,
        cwd=str(output_dir.parent),
    )
    out_tail = (proc.stdout or "")[-4000:]
    err_tail = (proc.stderr or "")[-4000:]
    if proc.stdout:
        for line in proc.stdout.splitlines()[-30:]:
            log(f"[repkg] {line}")
    if proc.returncode != 0:
        log(f"[repkg] exit {proc.returncode}")
        if err_tail.strip():
            log(f"[repkg stderr]\n{err_tail}")

    return {
        "executable": str(repkg_exe),
        "input": str(input_dir),
        "output": str(output_dir),
        "returncode": proc.returncode,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }
