from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.extract_e1_assets import (
    decode_hires_sprite,
    extract_sprite_bank,
    extract_startup_sprites,
)


class HiresSpriteTests(unittest.TestCase):
    def test_decode_hires_sprite_preserves_msb_first_pixels(self) -> None:
        source = bytes.fromhex("800001") + bytes(60)

        pixels = decode_hires_sprite(source)

        self.assertEqual((21, 24), (len(pixels), len(pixels[0])))
        self.assertEqual([1, 0, 0, 0], pixels[0][:4])
        self.assertEqual([0, 0, 0, 1], pixels[0][-4:])

    def test_decode_hires_sprite_rejects_wrong_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "63 bytes"):
            decode_hires_sprite(bytes(62))


class StartupSpriteExtractionTests(unittest.TestCase):
    def test_extract_startup_sprites_writes_two_valid_pngs(self) -> None:
        module = bytes.fromhex("fff800c03000") + bytes(57) + bytes(63) + b"\x00"
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "module.bin"
            output = Path(temporary_directory) / "assets"
            source.write_bytes(module)

            report = extract_startup_sprites(source, output, scale=2)

            self.assertEqual(2, len(report["sprites"]))
            first_png = output / "startup_sprite_0e.png"
            self.assertTrue(first_png.is_file())
            png = first_png.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", png[:8])
            width, height = struct.unpack(">II", png[16:24])
            self.assertEqual((48, 42), (width, height))
            sheet_png = (output / "startup_sprites_0e_0f.png").read_bytes()
            sheet_width, sheet_height = struct.unpack(">II", sheet_png[16:24])
            self.assertEqual((104, 42), (sheet_width, sheet_height))
            self.assertEqual("0x0E", report["sprites"][0]["pointer"])
            self.assertEqual("0x0380", report["sprites"][0]["address"])

    def test_extract_sprite_bank_uses_64_byte_slot_boundaries(self) -> None:
        bank = bytes.fromhex("800000") + bytes(60) + b"\xaa" + bytes.fromhex("000001") + bytes(60) + b"\xbb"
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "bank.bin"
            output = Path(temporary_directory) / "assets"
            source.write_bytes(bank)

            report = extract_sprite_bank(source, output, scale=1, columns=2)

            self.assertEqual(2, len(report["sprites"]))
            self.assertEqual(["0x00", "0x40"], [item["source_offset"] for item in report["sprites"]])
            sheet = (output / "bank_sprite_bank.png").read_bytes()
            self.assertEqual((52, 21), struct.unpack(">II", sheet[16:24]))


if __name__ == "__main__":
    unittest.main()
