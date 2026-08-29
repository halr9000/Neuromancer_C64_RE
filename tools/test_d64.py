#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

from tools.d64 import D64Image, SectorRef


PROJECT_ROOT = Path(__file__).resolve().parent.parent
E5_IMAGE = PROJECT_ROOT / "intake" / "NEUROMA4.D64"


class D64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.image = D64Image.read(E5_IMAGE)

    def test_known_sector_offset(self) -> None:
        self.assertEqual(D64Image.sector_offset(SectorRef(18, 0)), 0x16500)

    def test_e5_directory(self) -> None:
        entries = list(self.image.directory_entries())
        self.assertEqual(
            [entry.filename for entry in entries],
            ["NEUROMANCER DOX", "NEUROMANCER SOL"],
        )

    def test_dox_chain(self) -> None:
        entry = self.image.find_entry("NEUROMANCER DOX")
        chain = self.image.follow_chain(entry.start)
        self.assertEqual(entry.start, SectorRef(17, 0))
        self.assertEqual(len(chain.sectors), 22)
        self.assertEqual(len(chain.payload), 5_577)
        self.assertEqual(chain.payload[:2], b"\x01\x08")

    def test_solution_chain(self) -> None:
        entry = self.image.find_entry("NEUROMANCER SOL")
        chain = self.image.follow_chain(entry.start)
        self.assertEqual(entry.start, SectorRef(19, 0))
        self.assertEqual(len(chain.sectors), 90)
        self.assertEqual(len(chain.payload), 22_655)
        self.assertEqual(chain.payload[:2], b"\x01\x08")


if __name__ == "__main__":
    unittest.main()
