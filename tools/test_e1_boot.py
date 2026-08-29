#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.analyze_e1_boot import (
    CLIENT_CODE_END_EXCLUSIVE,
    CLIENT_SOURCE,
    DRIVE_ENTRY,
    DRIVE_DESTINATION,
    ISTOP_VECTOR,
    PRG_LOAD,
    REDIRECT_DESTINATION,
    REDIRECT_END_EXCLUSIVE,
    REDIRECT_SOURCE,
    STAGE1_ENTRY,
    STAGE1_SOURCE_END_EXCLUSIVE,
    address_slice,
)
from tools.d64 import D64Image, SectorRef


PROJECT_ROOT = Path(__file__).resolve().parent.parent
E1_IMAGE = PROJECT_ROOT / "intake" / "NEUROMA0.D64"
E1_PRG = PROJECT_ROOT / "extracted" / "e1" / "neuromancer_e1.prg"


class E1ExtractionTests(unittest.TestCase):
    def test_real_directory_chains(self) -> None:
        image = D64Image.read(E1_IMAGE)
        main_entry = image.find_entry("NEUROMANCER")
        main = image.follow_chain(main_entry.start)
        self.assertEqual(main_entry.start, SectorRef(13, 9))
        self.assertEqual(len(main.sectors), 204)
        self.assertEqual(len(main.payload), 51_794)
        self.assertEqual(main.payload[:2], b"\xA7\x02")

        aux_entry = image.find_entry("A")
        auxiliary = image.follow_chain(aux_entry.start)
        self.assertEqual(aux_entry.start, SectorRef(18, 5))
        self.assertEqual(len(auxiliary.sectors), 6)
        self.assertEqual(len(auxiliary.payload), 1_274)
        self.assertEqual(auxiliary.payload[:2], b"\x00\x3E")

    def test_redirected_bootstrap_alignment(self) -> None:
        prg = E1_PRG.read_bytes()
        self.assertEqual(prg[:2], b"\xA7\x02")
        payload = prg[2:]
        self.assertEqual(
            address_slice(payload, PRG_LOAD, ISTOP_VECTOR, ISTOP_VECTOR + 2),
            b"\xA7\x02",
        )
        stage = address_slice(
            payload,
            PRG_LOAD,
            REDIRECT_SOURCE,
            STAGE1_SOURCE_END_EXCLUSIVE,
        )
        self.assertEqual(len(stage), REDIRECT_END_EXCLUSIVE - REDIRECT_DESTINATION)
        self.assertEqual(
            hashlib.sha256(stage).hexdigest(),
            "e866772ef159403b7096f419e36a897c9a877899e9b2b2b8d2e8b4b29b32f76e",
        )
        self.assertEqual(stage[STAGE1_ENTRY - REDIRECT_DESTINATION :][:3], b"\x20\xE7\xFF")
        self.assertEqual(stage[DRIVE_ENTRY - DRIVE_DESTINATION :][:2], b"\xA9\x10")
        client = stage[
            CLIENT_SOURCE - REDIRECT_DESTINATION :
            CLIENT_CODE_END_EXCLUSIVE - REDIRECT_DESTINATION
        ]
        self.assertEqual(client[:5], b"\xA0\xFC\x84\x22\x20")
        self.assertEqual(client[-1], 0x60)


if __name__ == "__main__":
    unittest.main()
