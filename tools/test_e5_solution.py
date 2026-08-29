#!/usr/bin/env python3

from __future__ import annotations

import unittest

from tools.decode_e5_solution import decode_rle


class RleTests(unittest.TestCase):
    def test_literals_runs_and_escaped_marker(self) -> None:
        stream = bytes((0x41, 0xF3, 0x04, 0x42, 0xF3, 0x02, 0x43))
        values = iter(stream)
        decoded, stats = decode_rle(lambda: next(values), 7)
        self.assertEqual(decoded, b"ABBBB" + bytes((0xF3, 0xF3)))
        self.assertEqual(stats["run_records"], 2)


if __name__ == "__main__":
    unittest.main()
