#!/usr/bin/env python3
"""Validate a LINE sticker directory or ZIP without third-party packages."""

from __future__ import annotations

import argparse
import binascii
import io
import struct
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_000_000
STAMP_MAX = (320, 270)
MAIN_MAX = (240, 240)
TAB_MAX = (96, 74)


@dataclass
class PngInfo:
    width: int
    height: int
    color_type: int
    has_trns: bool
    declared_frames: int | None
    frame_controls: int

    @property
    def has_alpha(self) -> bool:
        return self.color_type in (4, 6) or self.has_trns

    @property
    def animated(self) -> bool:
        return self.declared_frames is not None


def parse_png(data: bytes) -> PngInfo:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("PNG形式ではありません")

    offset = len(PNG_SIGNATURE)
    width = height = color_type = None
    declared_frames = None
    frame_controls = 0
    has_trns = False
    saw_iend = False

    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("PNGチャンクが途中で切れています")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("PNGチャンク長がファイルサイズを超えています")
        chunk_data = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = binascii.crc32(chunk_type)
        actual_crc = binascii.crc32(chunk_data, actual_crc) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise ValueError(f"{chunk_type.decode('ascii', 'replace')}チャンクのCRCが不正です")

        if chunk_type == b"IHDR":
            if length != 13:
                raise ValueError("IHDRチャンクが不正です")
            width, height, _, color_type, _, _, _ = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"acTL":
            if length != 8:
                raise ValueError("acTLチャンクが不正です")
            declared_frames, _ = struct.unpack(">II", chunk_data)
        elif chunk_type == b"tRNS":
            has_trns = True
        elif chunk_type == b"fcTL":
            frame_controls += 1
        elif chunk_type == b"IEND":
            saw_iend = True
            break
        offset = end

    if width is None or height is None or color_type is None or not saw_iend:
        raise ValueError("必須PNGチャンクがありません")
    return PngInfo(width, height, color_type, has_trns, declared_frames, frame_controls)


def expected_names(names: set[str]) -> list[str]:
    numbered = sorted(
        name for name in names if len(name) == 6 and name[:2].isdigit() and name.endswith(".png")
    )
    return ["main.png", "tab.png", *numbered]


def validate_files(files: dict[str, bytes]) -> list[str]:
    errors: list[str] = []
    names = set(files)
    required = expected_names(names)

    for name in ("main.png", "tab.png"):
        if name not in names:
            errors.append(f"不足: {name}")

    numbered = sorted(
        name for name in names if len(name) == 6 and name[:2].isdigit() and name.endswith(".png")
    )
    if not numbered:
        errors.append("不足: 01.png から始まるスタンプ画像")
    else:
        expected = [f"{i:02d}.png" for i in range(1, len(numbered) + 1)]
        if numbered != expected:
            errors.append(f"連番が不正です: {', '.join(numbered)}")
        if len(numbered) not in (8, 16, 24, 32, 40):
            errors.append(f"スタンプ個数が一般的なセット数ではありません: {len(numbered)}")

    allowed = set(required)
    extra = sorted(name for name in names if name not in allowed)
    if extra:
        errors.append(f"ZIP直下に不要なファイルがあります: {', '.join(extra)}")

    stamp_animation_modes: set[bool] = set()
    for name in required:
        if name not in files:
            continue
        data = files[name]
        if len(data) > MAX_BYTES:
            errors.append(f"{name}: ファイル容量が1MBを超えています ({len(data)} bytes)")
        try:
            info = parse_png(data)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue

        max_size = TAB_MAX if name == "tab.png" else MAIN_MAX if name == "main.png" else STAMP_MAX
        if info.width > max_size[0] or info.height > max_size[1]:
            errors.append(
                f"{name}: 寸法 {info.width}x{info.height} が上限 {max_size[0]}x{max_size[1]} を超えています"
            )
        if not info.has_alpha:
            errors.append(f"{name}: アルファチャンネル付きPNGではありません")

        if info.animated:
            if info.declared_frames != info.frame_controls:
                errors.append(
                    f"{name}: APNGフレーム数が不一致です "
                    f"(宣言 {info.declared_frames}, 実体 {info.frame_controls})"
                )
            if info.declared_frames is not None and not 5 <= info.declared_frames <= 20:
                errors.append(f"{name}: APNGフレーム数が5〜20の範囲外です ({info.declared_frames})")

        if name not in ("main.png", "tab.png"):
            stamp_animation_modes.add(info.animated)
        if name == "tab.png" and info.animated:
            errors.append("tab.png: トークルームタブ画像は静止PNGにしてください")

    if len(stamp_animation_modes) > 1:
        errors.append("静止PNGとAPNGがスタンプ画像内で混在しています")
    return errors


def read_input(path: Path) -> dict[str, bytes]:
    if path.is_dir():
        return {p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}
    if path.suffix.lower() != ".zip":
        raise ValueError("入力はディレクトリまたはZIPファイルにしてください")
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"ZIP内のファイルが破損しています: {bad}")
            files: dict[str, bytes] = {}
            for info in archive.infolist():
                if info.is_dir():
                    continue
                pure = PurePosixPath(info.filename)
                if len(pure.parts) != 1:
                    raise ValueError(f"ZIP直下ではないファイルがあります: {info.filename}")
                files[pure.name] = archive.read(info)
            return files
    except zipfile.BadZipFile as exc:
        raise ValueError("ZIPファイルを開けません") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LINEスタンプ画像一式を申請前に検査します")
    parser.add_argument("path", type=Path, help="スタンプ画像ディレクトリまたはZIP")
    args = parser.parse_args(argv)

    try:
        files = read_input(args.path)
        errors = validate_files(files)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        print(f"NG: {len(errors)}件の問題が見つかりました")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {len(files)}ファイルを検査し、問題は見つかりませんでした")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
