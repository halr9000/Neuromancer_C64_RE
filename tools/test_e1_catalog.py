#!/usr/bin/env python3
"""Regression coverage for the E2-E4 room and overlay catalog."""

from __future__ import annotations

import unittest
import json
from pathlib import Path

from tools.catalog_e1_data import catalog_dataset
from tools.d64 import D64Image, SectorRef


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "extracted/e1/e1_new_game_ready_memory.bin"
SIDE_IMAGES = {
    2: D64Image.read(ROOT / "intake/NEUROMA1.D64"),
    3: D64Image.read(ROOT / "intake/NEUROMA2.D64"),
    4: D64Image.read(ROOT / "intake/NEUROMA3.D64"),
}


class E1CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = catalog_dataset(SNAPSHOT.read_bytes(), SIDE_IMAGES)

    def test_catalogs_room_table_and_side_runs(self) -> None:
        rooms = self.report["room_table"]

        self.assertEqual(rooms["entry_count"], 60)
        self.assertEqual(rooms["valid_count"], 56)
        self.assertEqual(rooms["invalid_entries"], [42, 47, 58, 59])
        self.assertEqual(
            rooms["entries"][0]["tuple"],
            {"side": 2, "track": 6, "sector": 0},
        )
        self.assertEqual(rooms["entries"][0]["encoded_length"], 5174)
        self.assertEqual(rooms["entries"][20]["tuple"], {
            "side": 3,
            "track": 24,
            "sector": 6,
        })
        self.assertEqual(
            rooms["side_runs"],
            [
                {"side": 2, "first_room": 0, "last_room": 19, "count": 20,
                 "rooms": list(range(0, 20))},
                {"side": 3, "first_room": 20, "last_room": 21, "count": 2,
                 "rooms": [20, 21]},
                {"side": 2, "first_room": 22, "last_room": 28, "count": 7,
                 "rooms": list(range(22, 29))},
                {"side": 3, "first_room": 29, "last_room": 29, "count": 1,
                 "rooms": [29]},
                {"side": 2, "first_room": 30, "last_room": 31, "count": 2,
                 "rooms": [30, 31]},
                {"side": 3, "first_room": 32, "last_room": 57, "count": 24,
                 "rooms": [*range(32, 42), *range(43, 47), *range(48, 58)]},
            ],
        )
        self.assertEqual(
            rooms["side_transitions"],
            [
                {"from_side": 2, "to_side": 3, "at_room": 20},
                {"from_side": 3, "to_side": 2, "at_room": 22},
                {"from_side": 2, "to_side": 3, "at_room": 29},
                {"from_side": 3, "to_side": 2, "at_room": 30},
                {"from_side": 2, "to_side": 3, "at_room": 32},
            ],
        )

    def test_catalogs_location_overlays_and_all_data_sides(self) -> None:
        overlays = self.report["location_overlays"]

        self.assertEqual(overlays["entry_count"], 30)
        self.assertEqual(overlays["side_counts"], {"2": 19, "3": 11})
        self.assertEqual(overlays["entries"][0]["room_id"], 0)
        self.assertEqual(overlays["entries"][0]["tuple"], {
            "side": 2,
            "track": 1,
            "sector": 17,
        })
        self.assertEqual(overlays["entries"][0]["encoded_length"], 1856)
        self.assertEqual(overlays["entries"][25]["room_id"], 45)
        self.assertEqual(overlays["entries"][25]["tuple"], {
            "side": 3,
            "track": 2,
            "sector": 2,
        })
        self.assertEqual(overlays["entries"][25]["encoded_length"], 1024)

        self.assertEqual(
            self.report["source_sides"],
            {
                "2": {
                    "label": "E2",
                    "marker": "2",
                    "image_sha256": "6bf683b9c688e3c999ec46657d18bbcc7268c5538d22440a8280110dcb1c30d0",
                    "room_modules": 29,
                    "overlay_modules": 19,
                },
                "3": {
                    "label": "E3",
                    "marker": "3",
                    "image_sha256": "80dbc6e5cba61c2aa8a92196a3b679ef10248d2ba33877461b70a24d9d7c1f51",
                    "room_modules": 27,
                    "overlay_modules": 11,
                },
                "4": {
                    "label": "E4",
                    "marker": "4",
                    "image_sha256": "5a2fe7886aafe8dc61e28ff43d56821854bd8c8aa46b37c6f4c635c894e27a1e",
                    "room_modules": 0,
                    "overlay_modules": 0,
                },
            },
        )

        self.assertEqual(
            overlays["entries"][25]["sectors"],
            ["T02/S02", "T02/S03", "T02/S04", "T02/S05", "T02/S06"],
        )
        self.assertEqual(
            overlays["entries"][25]["sha256"],
            "ee0f5e2f361d0cfa52c3282b853c0ced1b805d20c12366609b3bfd3436f42580",
        )

    def test_catalog_artifact_matches_fresh_report(self) -> None:
        artifact = json.loads(
            (ROOT / "extracted/e1/e1_data_catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(artifact, self.report)

    def test_rejects_invalid_room_side_marker(self) -> None:
        snapshot = bytearray(SNAPSHOT.read_bytes())
        snapshot[0xFE78] = ord("4")

        with self.assertRaisesRegex(ValueError, "room 0 has invalid side marker"):
            catalog_dataset(bytes(snapshot), SIDE_IMAGES)

    def test_rejects_invalid_source_side_markers(self) -> None:
        marker_offset = D64Image.sector_offset(SectorRef(18, 0)) + 0xDC
        for side in (2, 3, 4):
            corrupted = bytearray(SIDE_IMAGES[side].data)
            corrupted[marker_offset] = ord("9")
            images = dict(SIDE_IMAGES)
            images[side] = D64Image(bytes(corrupted))

            with self.subTest(side=side), self.assertRaisesRegex(
                ValueError, f"side {side} marker"
            ):
                catalog_dataset(SNAPSHOT.read_bytes(), images)


if __name__ == "__main__":
    unittest.main()
