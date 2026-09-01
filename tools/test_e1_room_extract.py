#!/usr/bin/env python3
"""Regression tests for generalized selected-room extraction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.d64 import D64Image
from tools.extract_e1_room import extract_room


ROOT = Path(__file__).resolve().parents[1]


class E1RoomExtractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report, cls.assets = extract_room(
            (ROOT / "extracted/e1/e1_new_game_ready_memory.bin").read_bytes(),
            {
                2: D64Image.read(ROOT / "intake/NEUROMA1.D64"),
                3: D64Image.read(ROOT / "intake/NEUROMA2.D64"),
                4: D64Image.read(ROOT / "intake/NEUROMA3.D64"),
            },
            room_id=6,
            location_room_id=0,
            text_count=5,
        )

    def test_extracts_selected_cheap_hotel_room(self) -> None:
        self.assertEqual(self.report["room_id"], 6)
        self.assertEqual(self.report["display_name"], "You're at the Cheap Hotel.")
        self.assertEqual(
            self.report["selection"]["room"], {"side": 2, "track": 11, "sector": 14}
        )
        self.assertEqual(len(self.assets["room_logic"]), 4045)
        self.assertEqual(len(self.assets["runtime"]), 3072)

    def test_retains_chiba_location_overlay_and_terminal(self) -> None:
        self.assertEqual(self.report["selection"]["location"]["room_id"], 0)
        self.assertTrue(self.report["terminal"]["pax_enabled"])
        self.assertEqual(
            self.report["hit_regions"]["sets"][0]["regions"][0],
            {"x": 4, "y": 5, "width": 2, "height": 25, "event": 1},
        )

    def test_promotes_room_entity(self) -> None:
        self.assertEqual(len(self.report["entities"]), 1)
        self.assertEqual(self.report["entities"][0]["address"], "0xC430")
        self.assertEqual(self.report["entities"][0]["colors"], 0x33)

    def test_checked_in_map_matches(self) -> None:
        checked = json.loads(
            (ROOT / "extracted/e1/room6/e1_room6_map.json").read_text(encoding="utf-8")
        )
        self.assertEqual(checked, self.report)

    def test_rejects_room_without_table_mapping(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid side mapping"):
            extract_room(
                (ROOT / "extracted/e1/e1_new_game_ready_memory.bin").read_bytes(),
                {
                    2: D64Image.read(ROOT / "intake/NEUROMA1.D64"),
                    3: D64Image.read(ROOT / "intake/NEUROMA2.D64"),
                    4: D64Image.read(ROOT / "intake/NEUROMA3.D64"),
                },
                room_id=42,
                location_room_id=0,
                text_count=1,
            )


if __name__ == "__main__":
    unittest.main()
