from __future__ import annotations

import unittest

from pathlib import Path

from tools.decode_e1_room_text import RoomTextDecoder, decode_room_strings


def fixture_root() -> bytes:
    dictionary = bytearray(60)
    dictionary[0] = ord(" ")
    dictionary[1] = ord("a")
    dictionary[2] = ord("b")
    dictionary[20] = 0
    dictionary[30] = ord("!")
    pointer_table = bytes.fromhex("02 00")
    # Tokens: [a, NUL], [b, NUL], [CAP, a, NUL], [ESC, 0, NUL].
    packed = bytes.fromhex("81 0A EA 03 FD 80 02")
    return bytes(dictionary) + pointer_table + packed


class RoomTextDecoderTests(unittest.TestCase):
    def test_decode_group_uses_low_two_string_id_bits(self) -> None:
        decoder = RoomTextDecoder(fixture_root())

        self.assertEqual(["a", "b", "A", "!"], [decoder.decode(i) for i in range(4)])

    def test_decode_rejects_pointer_outside_room_data(self) -> None:
        root = bytearray(fixture_root())
        root[60:62] = bytes.fromhex("FF 7F")

        with self.assertRaisesRegex(ValueError, "pointer"):
            RoomTextDecoder(bytes(root)).decode(0)

    def test_decode_real_room_zero_text(self) -> None:
        snapshot = Path("extracted/e1/e1_room0_ready_memory.bin")
        if not snapshot.exists():
            self.skipTest("room-0 snapshot has not been generated")

        report = decode_room_strings(snapshot.read_bytes(), 0x21)
        strings = [item["text"] for item in report["strings"]]

        self.assertEqual(0x21, report["string_count"])
        self.assertEqual("In the Chatsubo Bar.", strings[1])
        self.assertEqual("\r\rRatz refuses to take your credits.", strings[0x20])


if __name__ == "__main__":
    unittest.main()
