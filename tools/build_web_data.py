#!/usr/bin/env python3
"""Build versioned browser data from verified room-0 extraction artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MEMORY_SIZE = 0x10000
ROOM0_ENTITY_ADDRESS = 0xC400
ENTITY_RECORD_SIZE = 8
SCHEMA_VERSION = 1
SPRITE_WIDTH = 24
SPRITE_HEIGHT = 21


def decode_hires_sprite(data: bytes) -> list[list[int]]:
    if len(data) != SPRITE_WIDTH * SPRITE_HEIGHT // 8:
        raise ValueError("VIC sprite source must contain 63 bytes")
    return [
        [
            (data[row * 3 + column // 8] >> (7 - column % 8)) & 1
            for column in range(SPRITE_WIDTH)
        ]
        for row in range(SPRITE_HEIGHT)
    ]


def decode_multicolor_sprite(data: bytes) -> list[list[int]]:
    if len(data) != SPRITE_WIDTH * SPRITE_HEIGHT // 8:
        raise ValueError("VIC sprite source must contain 63 bytes")
    rows: list[list[int]] = []
    for row in range(SPRITE_HEIGHT):
        pixels: list[int] = []
        for value in data[row * 3 : row * 3 + 3]:
            for shift in (6, 4, 2, 0):
                color = (value >> shift) & 0x03
                pixels.extend((color, color))
        rows.append(pixels)
    return rows


def build_room0_data(
    memory: bytes,
    text_report: dict[str, Any],
    screen: bytes,
    charset: bytes,
    colors: bytes,
    sprite_workspace: bytes,
) -> dict[str, Any]:
    if len(memory) != MEMORY_SIZE:
        raise ValueError("room-0 snapshot must be exactly 64 KiB")
    if len(screen) != 1000 or len(charset) != 2048 or len(colors) != 1000:
        raise ValueError("room display must contain 1000 screen/color and 2048 charset bytes")
    if len(sprite_workspace) != 128:
        raise ValueError("room sprite workspace must contain two 64-byte slots")

    strings = text_report.get("strings")
    if not isinstance(strings, list) or text_report.get("string_count") != len(strings):
        raise ValueError("room text report has an invalid string count")
    text = []
    for expected_id, item in enumerate(strings):
        if not isinstance(item, dict) or item.get("id") != expected_id:
            raise ValueError("room text IDs must be contiguous from zero")
        value = item.get("text")
        if not isinstance(value, str):
            raise ValueError("room text entries must contain text")
        text.append(value)

    record = memory[ROOM0_ENTITY_ADDRESS : ROOM0_ENTITY_ADDRESS + ENTITY_RECORD_SIZE]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "source": {
            "snapshotSha256": text_report.get("source_sha256"),
            "roomTextRoot": "0xF248",
        },
        "room": {
            "id": 0,
            "text": text,
            "display": {
                "screenCodes": list(screen),
                "charset": list(charset),
                "colorCodes": [value & 0x0F for value in colors],
                "backgroundColor": 0,
                "borderColor": 0,
            },
            "sprites": [
                {
                    "pointer": pointer,
                    "sourceAddress": f"0x{pointer * 64:04X}",
                    "color": color,
                    "multicolor": True,
                    "sharedColors": [0, 0],
                    "x": 64,
                    "y": y,
                    "rows": decode_multicolor_sprite(
                        sprite_workspace[(pointer - 0x21) * 64 : (pointer - 0x21) * 64 + 63]
                    ),
                }
                for pointer, color, y in ((0x21, 0x09, 88), (0x22, 0x02, 109))
            ],
            "entities": [
                {
                    "sourceAddress": "0xC400",
                    "sourceBytes": list(record),
                    "roomId": record[0],
                    "slot": record[1] & 0x03,
                    "packedRenderFlags": record[1],
                    "logicalX": record[2],
                    "logicalY": record[3],
                    "packedColors": record[4],
                    "activationState": record[5],
                    "scriptAddress": record[6] | (record[7] << 8),
                }
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("room_text", type=Path)
    parser.add_argument("screen", type=Path)
    parser.add_argument("charset", type=Path)
    parser.add_argument("colors", type=Path)
    parser.add_argument("sprite_workspace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    text_report = json.loads(args.room_text.read_text(encoding="utf-8"))
    result = build_room0_data(
        args.snapshot.read_bytes(),
        text_report,
        args.screen.read_bytes(),
        args.charset.read_bytes(),
        args.colors.read_bytes(),
        args.sprite_workspace.read_bytes(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote room 0 web data to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
