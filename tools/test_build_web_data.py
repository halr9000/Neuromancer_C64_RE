from __future__ import annotations

import unittest

from tools.build_web_data import build_room0_data


class BuildWebDataTests(unittest.TestCase):
    def test_room_zero_keeps_entity_source_bytes_and_promoted_fields(self) -> None:
        memory = bytearray(0x10000)
        memory[0xC400:0xC408] = bytes.fromhex("00 C1 14 22 29 FF 00 00")
        text_report = {
            "source_sha256": "snapshot-hash",
            "string_count": 2,
            "strings": [
                {"id": 0, "id_hex": "0x00", "text": "Description"},
                {"id": 1, "id_hex": "0x01", "text": "Room name"},
            ],
        }

        result = build_room0_data(bytes(memory), text_report)

        self.assertEqual(1, result["schemaVersion"])
        self.assertEqual("snapshot-hash", result["source"]["snapshotSha256"])
        self.assertEqual(["Description", "Room name"], result["room"]["text"])
        self.assertEqual(
            {
                "sourceAddress": "0xC400",
                "sourceBytes": [0x00, 0xC1, 0x14, 0x22, 0x29, 0xFF, 0x00, 0x00],
                "roomId": 0,
                "slot": 1,
                "packedRenderFlags": 0xC1,
                "logicalX": 0x14,
                "logicalY": 0x22,
                "packedColors": 0x29,
                "activationState": 0xFF,
                "scriptAddress": 0,
            },
            result["room"]["entities"][0],
        )


if __name__ == "__main__":
    unittest.main()
