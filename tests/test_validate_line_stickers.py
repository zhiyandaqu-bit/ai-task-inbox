import binascii
import io
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

from scripts.validate_line_stickers import read_input, validate_files


def chunk(kind: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(kind)
    crc = binascii.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def png(width=32, height=32, declared_frames=None, actual_frames=0) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    result = signature + chunk(b"IHDR", ihdr)
    if declared_frames is not None:
        result += chunk(b"acTL", struct.pack(">II", declared_frames, 4))
        for index in range(actual_frames):
            frame = struct.pack(">IIIIIHHBB", index, width, height, 0, 0, 1, 8, 0, 0)
            result += chunk(b"fcTL", frame)
    raw = b"".join(b"\x00" + b"\x00\x00\x00\x00" * width for _ in range(height))
    result += chunk(b"IDAT", zlib.compress(raw))
    return result + chunk(b"IEND", b"")


def valid_set(animated=False) -> dict[str, bytes]:
    frame_args = {"declared_frames": 6, "actual_frames": 6} if animated else {}
    files = {f"{index:02d}.png": png(320, 270, **frame_args) for index in range(1, 9)}
    files["main.png"] = png(240, 240, **frame_args)
    files["tab.png"] = png(96, 74)
    return files


class ValidatorTests(unittest.TestCase):
    def test_valid_static_set(self):
        self.assertEqual(validate_files(valid_set()), [])

    def test_valid_animated_set(self):
        self.assertEqual(validate_files(valid_set(animated=True)), [])

    def test_apng_frame_mismatch(self):
        files = valid_set(animated=True)
        files["05.png"] = png(320, 270, declared_frames=6, actual_frames=4)
        errors = validate_files(files)
        self.assertTrue(any("APNGフレーム数が不一致" in error for error in errors))

    def test_nested_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stickers.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("stickers/01.png", png())
            with self.assertRaisesRegex(ValueError, "ZIP直下ではない"):
                read_input(path)


if __name__ == "__main__":
    unittest.main()
