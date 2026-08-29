#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

from tools.d64 import D64Image
from tools.decode_e1_fastload import decode_record, parse_basic_sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
E1_IMAGE = PROJECT_ROOT / "intake" / "NEUROMA0.D64"


class E1FastloadTests(unittest.TestCase):
    def test_reconstruct_record(self) -> None:
        data, report = decode_record(D64Image.read(E1_IMAGE), "NEUROMANCER")
        self.assertEqual(report["bootstrap_sectors"], ["T13/S09", "T13/S10", "T13/S11"])
        self.assertEqual(report["first_fastload_sector"], "T13/S12")
        self.assertEqual(report["last_fastload_sector"], "T30/S07")
        self.assertEqual(report["fastload_sector_count"], 201)
        self.assertEqual(report["destination"], "0x0801")
        self.assertEqual(report["end_exclusive"], "0xCF57")
        self.assertEqual(len(data), 51_030)

    def test_basic_launcher(self) -> None:
        data, _ = decode_record(D64Image.read(E1_IMAGE), "NEUROMANCER")
        launcher = parse_basic_sys(data, 0x0801)
        self.assertEqual(launcher["next_line"], "0x080B")
        self.assertEqual(launcher["line_number"], 1744)
        self.assertEqual(launcher["sys_target_decimal"], 2051)
        self.assertEqual(launcher["sys_target"], "0x0803")


if __name__ == "__main__":
    unittest.main()
