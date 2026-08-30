#!/usr/bin/env python3
"""Decode E1 room strings rooted at the pointer stored in $F002/$F003."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DICTIONARY_SIZE = 0x3C
STRINGS_PER_GROUP = 4
TOKEN_CAPITALIZE = 0x1E
TOKEN_EXTEND = 0x1F
ROOM0_STRING_COUNT = 0x21


class BitReader:
    def __init__(self, data: bytes, offset: int) -> None:
        self.data = data
        self.bit_offset = offset * 8

    def read_five(self) -> int:
        value = 0
        for bit_index in range(5):
            byte_offset, source_bit = divmod(self.bit_offset, 8)
            if byte_offset >= len(self.data):
                raise ValueError("room text bitstream ended unexpectedly")
            value |= ((self.data[byte_offset] >> source_bit) & 1) << bit_index
            self.bit_offset += 1
        return value


class RoomTextDecoder:
    def __init__(self, root_data: bytes) -> None:
        if len(root_data) < DICTIONARY_SIZE + 2:
            raise ValueError("room text root is too short")
        self.data = root_data
        self.dictionary = root_data[:DICTIONARY_SIZE]

    def _group_offset(self, string_id: int) -> int:
        if not 0 <= string_id <= 0xFF:
            raise ValueError("room string ID must fit in one byte")
        pointer_offset = DICTIONARY_SIZE + (string_id >> 2) * 2
        if pointer_offset + 1 >= len(self.data):
            raise ValueError("room string pointer lies outside room data")
        relative = self.data[pointer_offset] | (self.data[pointer_offset + 1] << 8)
        target = DICTIONARY_SIZE + relative
        if not DICTIONARY_SIZE <= target < len(self.data):
            raise ValueError("room string pointer lies outside room data")
        return target

    def _decode_one(self, reader: BitReader) -> str:
        output: list[str] = []
        capitalize = False
        for _ in range(4096):
            token = reader.read_five()
            if token == TOKEN_CAPITALIZE:
                capitalize = True
                continue
            if token == TOKEN_EXTEND:
                token = reader.read_five() + TOKEN_CAPITALIZE
            if token >= len(self.dictionary):
                raise ValueError(f"room text dictionary index {token} is out of range")
            value = self.dictionary[token]
            if value == 0:
                return "".join(output)
            if capitalize and ord("a") <= value <= ord("z"):
                value -= 0x20
            output.append(chr(value))
            capitalize = False
        raise ValueError("room string exceeds 4096 decoded characters")

    def decode(self, string_id: int) -> str:
        reader = BitReader(self.data, self._group_offset(string_id))
        for _ in range(string_id & (STRINGS_PER_GROUP - 1)):
            self._decode_one(reader)
        return self._decode_one(reader)


def decode_room_strings(memory: bytes, count: int) -> dict[str, object]:
    if len(memory) != 0x10000:
        raise ValueError("room snapshot must be exactly 64 KiB")
    root_address = memory[0xF002] | (memory[0xF003] << 8)
    decoder = RoomTextDecoder(memory[root_address:])
    strings = [
        {"id": string_id, "id_hex": f"0x{string_id:02X}", "text": decoder.decode(string_id)}
        for string_id in range(count)
    ]
    return {
        "source_sha256": hashlib.sha256(memory).hexdigest(),
        "root_address": f"0x{root_address:04X}",
        "dictionary_size": DICTIONARY_SIZE,
        "string_count": count,
        "strings": strings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--count", type=int, default=ROOM0_STRING_COUNT)
    args = parser.parse_args()

    report = decode_room_strings(args.snapshot.read_bytes(), args.count)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "e1_room0_text.json"
    text_path = args.output_dir / "e1_room0_text.txt"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    text_path.write_text(
        "\n".join(f"{item['id_hex']}  {item['text']}" for item in report["strings"]) + "\n",
        encoding="utf-8",
    )
    print(f"decoded {report['string_count']} strings from {report['root_address']}")
    print(f"wrote {json_path}")
    print(f"wrote {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
