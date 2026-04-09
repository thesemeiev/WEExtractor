#!/usr/bin/env python3
"""
Heuristics to skip Wallpaper Engine workshop junk (previews, tiny sprites, shaders)
when extracting for use as a normal desktop wallpaper (image/video).
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Callable, Optional, Set, Tuple

IMAGE_EXT: Set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tga",
}
VIDEO_EXT: Set[str] = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v"}
SHADER_EXT: Set[str] = {".frag", ".vert", ".hlsl", ".shader", ".compute"}
AUDIO_EXT: Set[str] = {".ogg", ".mp3", ".wav", ".m4a"}

PREVIEW_FILENAMES = {
    "preview.jpg",
    "preview.jpeg",
    "preview.png",
    "preview.gif",
    "preview.webp",
    "workshop_preview.jpg",
    "workshop_preview.png",
}


def read_sniff(path: Path, max_bytes: int = 262_144) -> bytes:
    with path.open("rb") as f:
        return f.read(max_bytes)


def sniff_image_dimensions(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) < 24:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        w, h = struct.unpack_from(">II", data, 16)
        if 1 <= w <= 32_768 and 1 <= h <= 32_768:
            return w, h
        return None
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        w, h = struct.unpack_from("<HH", data, 6)
        if 1 <= w <= 32_768 and 1 <= h <= 32_768:
            return w, h
        return None
    if data.startswith(b"BM") and len(data) >= 26:
        w, h = struct.unpack_from("<ii", data, 18)
        w, h = abs(w), abs(h)
        if 1 <= w <= 32_768 and 1 <= h <= 32_768:
            return w, h
        return None
    if data.startswith(b"\xff\xd8"):
        return _jpeg_dimensions(data)
    return None


def _jpeg_dimensions(data: bytes) -> Optional[Tuple[int, int]]:
    i = 0
    n = len(data)
    while i < n - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8,):  # SOI
            continue
        if marker in (0xD9, 0xDA):  # EOI, SOS — stop
            break
        if i + 2 > n:
            break
        seg_len = struct.unpack_from(">H", data, i)[0]
        if seg_len < 2 or i + seg_len > n:
            break
        # SOF0–SOF15 except DHT/DAC
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if seg_len >= 8:
                h, w = struct.unpack_from(">HH", data, i + 3)
                if 1 <= w <= 32_768 and 1 <= h <= 32_768:
                    return w, h
            break
        i += seg_len
    return None


def is_likely_preview_path(rel: Path) -> bool:
    name = rel.name.lower()
    suf = rel.suffix.lower()
    if name in PREVIEW_FILENAMES:
        return True
    if suf not in IMAGE_EXT and suf not in {".jpg", ".jpeg"}:
        if "thumbnail" in name:
            return True
        return False
    stem = rel.stem.lower()
    if stem == "preview" or stem.endswith("_preview") or stem.startswith("preview_"):
        return True
    if "thumbnail" in name or (name.startswith("thumb") and suf in IMAGE_EXT):
        return True
    return False


def _skip_loose_web_stack(rel: Path, project_type: str) -> bool:
    if project_type == "web":
        return False
    suf = rel.suffix.lower()
    return suf in {".html", ".htm", ".css", ".js", ".map"}


def make_loose_copy_filter(
    *,
    desktop_mode: bool,
    min_image_w: int,
    min_image_h: int,
    min_video_bytes: int,
    project_type: str,
) -> Callable[[Path, Path], bool]:
    """
    Returns True if the file at src_path (relative rel) should be copied to loose/.
    """

    def keep(rel: Path, src_path: Path) -> bool:
        if not desktop_mode:
            return True
        if is_likely_preview_path(rel):
            return False
        suf = rel.suffix.lower()
        if suf == ".json":
            return False
        if _skip_loose_web_stack(rel, project_type):
            return False
        if suf in AUDIO_EXT:
            return False
        try:
            st = src_path.stat()
        except OSError:
            return False
        if suf in IMAGE_EXT:
            data = read_sniff(src_path)
            dims = sniff_image_dimensions(data)
            if dims:
                w, h = dims
                if w < min_image_w or h < min_image_h:
                    return False
            elif st.st_size < 24_576:
                return False
        if suf in VIDEO_EXT:
            if st.st_size < min_video_bytes:
                return False
        return True

    return keep


def desktop_pkg_keep_file(
    rel: Path,
    *,
    sniff_bytes: bytes,
    size: int,
    min_image_w: int,
    min_image_h: int,
    min_video_bytes: int,
) -> bool:
    """
    True = оставить файл при режиме desktop (после распаковки RePKG или для записи из PKG).
    rel — относительный путь внутри одной папки пакета.
    """
    rel_norm = Path(rel.as_posix().lower())
    if is_likely_preview_path(rel_norm):
        return False
    suf = rel_norm.suffix.lower()
    if suf == ".json":
        return False
    if suf in SHADER_EXT:
        return False
    if suf in AUDIO_EXT:
        return False
    if suf in IMAGE_EXT:
        dims = sniff_image_dimensions(sniff_bytes)
        if dims:
            w, h = dims
            if w < min_image_w or h < min_image_h:
                return False
        elif size < 24_576:
            return False
    if suf in VIDEO_EXT:
        if size < min_video_bytes:
            return False
    return True


def prune_pkg_tree_for_desktop(
    pkg_unpack_root: Path,
    *,
    min_image_w: int,
    min_image_h: int,
    min_video_bytes: int,
    log: Callable[[str], None],
) -> None:
    """Удаляет из дерева распакованного пакета файлы, которые desktop-режим не копировал бы."""
    if not pkg_unpack_root.is_dir():
        return
    for path in sorted(pkg_unpack_root.rglob("*"), reverse=True):
        if not path.is_file():
            continue
        rel = path.relative_to(pkg_unpack_root)
        try:
            st = path.stat()
        except OSError:
            continue
        sniff = read_sniff(path)
        if not desktop_pkg_keep_file(
            rel,
            sniff_bytes=sniff,
            size=st.st_size,
            min_image_w=min_image_w,
            min_image_h=min_image_h,
            min_video_bytes=min_video_bytes,
        ):
            try:
                path.unlink()
                log(f"[desktop prune] {rel.as_posix()}")
            except OSError:
                pass
