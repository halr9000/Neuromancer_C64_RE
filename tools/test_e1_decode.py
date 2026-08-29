#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.analyze_e1_runtime_init import execute_runtime_init
from tools.d64 import D64Image, SectorRef
from tools.decode_e1_first_room import ROOM_RUNTIME_LENGTH
from tools.decode_e1_modules import COMMON_MODULES, ModuleSpec, decode_module, overlay
from tools.decode_e1_stage2 import execute_stage2
from tools.decode_e1_stage3 import execute_stage3
from tools.finalize_e1_startup import execute_final_stub


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = PROJECT_ROOT / "extracted" / "e1"
SIDE1 = PROJECT_ROOT / "intake" / "NEUROMA0.D64"
SIDE2 = PROJECT_ROOT / "intake" / "NEUROMA1.D64"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class E1DecodeTests(unittest.TestCase):
    def test_frontline_stage(self) -> None:
        memory, report = execute_stage2(EXTRACTED / "e1_fastload_0801_cf56.bin")
        self.assertEqual(report["bootstrap_instructions"], 1_887)
        self.assertEqual(report["unpack_instructions"], 2_279_075)
        self.assertEqual(report["instructions_executed"], 2_280_962)
        self.assertEqual(
            sha256(memory),
            "ff364efe1e15c4b764fb2845fa4e80d71638768a9a6ab51cf795e51deb1e9460",
        )

    def test_runtime_relocation(self) -> None:
        memory, report = execute_runtime_init(EXTRACTED / "e1_unpacked_memory.bin")
        self.assertEqual(report["instructions_executed"], 288_375)
        self.assertEqual(
            sha256(memory),
            "66efe6b6eb4f83fe9a5a959e587c1b575f635e0d928b19b84f438caefb792be3",
        )

    def test_zero_page_decoder(self) -> None:
        memory, report = execute_stage3(EXTRACTED / "e1_runtime_memory.bin")
        self.assertEqual(report["instructions_executed"], 558_474)
        self.assertEqual(
            sha256(memory),
            "844afa29d91d2fd732acc100e9e864c93dd07fa42941293d509f0ded4c1784d6",
        )

    def test_self_erasing_final_stub(self) -> None:
        memory, report = execute_final_stub(EXTRACTED / "e1_stage3_memory.bin")
        self.assertEqual(report["instructions_executed"], 596)
        self.assertEqual(report["game_entry"], "0x03E7")
        self.assertEqual(
            sha256(memory),
            "f70a7209695636e2032353deb91b7305d5d34d3051518f588017a50afd64e3ca",
        )

    def test_correct_hex_sector_and_initial_module_snapshot(self) -> None:
        image = D64Image.read(SIDE1)
        room_tables = COMMON_MODULES[1]
        self.assertEqual(room_tables.start, SectorRef(6, 19))
        data, report = decode_module(image, room_tables)
        self.assertEqual(len(data), 509)
        self.assertEqual(report["end_exclusive"], "0xFFFD")
        self.assertEqual(
            sha256(data),
            "96bcb7e0d59eb109e684739e833f96fff5d4cf53d4911fd739516c328a14e9c8",
        )
        self.assertEqual(
            sha256((EXTRACTED / "e1_new_game_ready_memory.bin").read_bytes()),
            "a2972b228a6305475f84aa82f7c18cf25d7c3fb144d14b9adbe5b2d9bbd03e1a",
        )

    def test_first_room_cross_side_runtime(self) -> None:
        memory = bytearray((EXTRACTED / "e1_new_game_ready_memory.bin").read_bytes())
        side1 = D64Image.read(SIDE1)
        side2 = D64Image.read(SIDE2)
        specs = (
            (side1, ModuleSpec("frontend", SectorRef(6, 6), 0xCA00, "test")),
            (side2, ModuleSpec("overlay", SectorRef(1, 17), 0xAC80, "test")),
            (side2, ModuleSpec("room_logic", SectorRef(6, 0), 0xCA00, "test")),
        )
        expected_hashes = (
            "aab8121aff2430bb050f5e0b6ea79a105956dd5da7e0130401966caf23f35b84",
            "774af0a906e953d352e637889eb1dc48a03be95ca4c05ccfb70f98f4c8d52dce",
            "e0b974a828ba62a90c8ce1faa54b8a8335184218291e8bc2d268016a6eb870b0",
        )
        for (image, spec), expected_hash in zip(specs, expected_hashes, strict=True):
            data, _ = decode_module(image, spec)
            self.assertEqual(sha256(data), expected_hash)
            overlay(memory, spec.destination, data)
        memory[0xF000 : 0xF000 + ROOM_RUNTIME_LENGTH] = memory[
            0xCA00 : 0xCA00 + ROOM_RUNTIME_LENGTH
        ]
        self.assertEqual(
            memory[0xF00A:0xF013],
            bytes.fromhex("4C F6 F0 4C 0E F1 4C 0D F1"),
        )
        self.assertEqual(
            sha256(memory),
            "66316f2f3b0ccb2b03dfba6314978afbe665b470290cd51290db2f9837c32089",
        )


if __name__ == "__main__":
    unittest.main()
