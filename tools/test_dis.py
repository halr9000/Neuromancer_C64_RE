#!/usr/bin/env python3

from __future__ import annotations

import unittest

from tools.dis import Image, disassemble


class DisassemblerTests(unittest.TestCase):
    def test_branch_target_and_sizes(self) -> None:
        image = Image(bytes.fromhex("A9 01 D0 FC 60"), 0x1000)
        lines = disassemble(image, 0x1000, 3, {})
        self.assertIn("LDA   #$01", lines[0])
        self.assertIn("BNE   $1000", lines[1])
        self.assertIn("RTS", lines[2])

    def test_undocumented_byte_stays_synchronized(self) -> None:
        image = Image(bytes.fromhex("02 EA"), 0x2000)
        lines = disassemble(image, 0x2000, 2, {})
        self.assertIn(".byte $02", lines[0])
        self.assertIn("NOP", lines[1])


if __name__ == "__main__":
    unittest.main()
