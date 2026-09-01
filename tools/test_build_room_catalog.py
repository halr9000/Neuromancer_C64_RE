#!/usr/bin/env python3
"""Tests for the public native-room evidence catalog."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.build_room_catalog import build_catalog


class BuildRoomCatalogTests(unittest.TestCase):
    def test_builds_readable_room_records_and_native_crops(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            frame = Image.new("RGB", (384, 272), "black")
            frame.paste((12, 34, 56), (32, 35, 352, 235))
            room0 = {
                "room_id": 0,
                "selection": {"room": {"side": 2, "track": 6, "sector": 0}},
                "modules": [{"name": "room0", "sha256": "0" * 64}],
                "strings": [
                    {"id": 0, "text": "A bar called the Chatsubo."},
                    {"id": 1, "text": "In the Chatsubo Bar."},
                ],
                "entities": [{}, {}],
                "terminal": {"pax_enabled": True},
            }
            room6 = {
                "room_id": 6,
                "selection": {"room": {"side": 2, "track": 11, "sector": 14}},
                "modules": [{}, {"name": "room6", "sha256": "6" * 64}],
                "strings": [
                    {"id": 0, "text": "Cheap Hotel smells of cigarettes."},
                    {"id": 1, "text": "You're at the Cheap Hotel."},
                ],
                "entities": [{}],
                "terminal": {"pax_enabled": True},
            }

            catalog = build_catalog(
                [(room0, frame), (room6, frame)], output
            )

            self.assertEqual(catalog["schemaVersion"], 1)
            self.assertEqual([0, 6], [room["id"] for room in catalog["rooms"]])
            self.assertEqual("Chatsubo", catalog["rooms"][0]["name"])
            self.assertEqual("Cheap Hotel", catalog["rooms"][1]["name"])
            self.assertEqual("T11/S14", catalog["rooms"][1]["provenance"]["start"])
            with Image.open(output / "room6.png") as result:
                self.assertEqual((320, 200), result.size)

    def test_rejects_missing_room_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "at least two decoded strings"):
                build_catalog(
                    [({"room_id": 0, "strings": []}, Image.new("RGB", (384, 272)))],
                    Path(temporary),
                )


if __name__ == "__main__":
    unittest.main()
