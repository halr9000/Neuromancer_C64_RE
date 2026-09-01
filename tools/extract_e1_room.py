#!/usr/bin/env python3
"""Reconstruct one selected E1 room and export native evidence assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image, SectorRef
    from .decode_e1_modules import ModuleSpec, decode_module, overlay
    from .decode_e1_room_text import RoomTextDecoder
except ImportError:
    from d64 import D64Image, SectorRef
    from decode_e1_modules import ModuleSpec, decode_module, overlay
    from decode_e1_room_text import RoomTextDecoder


MEMORY_SIZE = 0x10000
ROOM_ID_ADDRESS = 0xC330
ROOM_TRACK_TABLE = 0xFE00
ROOM_SECTOR_TABLE = 0xFE3C
ROOM_SIDE_TABLE = 0xFE78
LOCATION_ID_TABLE = 0x62C5
LOCATION_TRACK_TABLE = 0x62E3
LOCATION_SECTOR_TABLE = 0x6301
LOCATION_COUNT = 30
RUNTIME_LENGTH = 0x0C00


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _module(
    image: D64Image, name: str, ref: SectorRef, destination: int, role: str
) -> tuple[bytes, dict[str, object]]:
    data, report = decode_module(image, ModuleSpec(name, ref, destination, role))
    report["source_image_sha256"] = sha256(image.data)
    return data, report


def _location_tuple(memory: bytes, room_id: int) -> tuple[int, int, int, int] | None:
    ids = memory[LOCATION_ID_TABLE : LOCATION_ID_TABLE + LOCATION_COUNT]
    try:
        index = ids.index(room_id)
    except ValueError:
        return None
    side = 2 if index < 0x13 else 3
    return (
        index,
        side,
        memory[LOCATION_TRACK_TABLE + index],
        memory[LOCATION_SECTOR_TABLE + index],
    )


def _decode_strings(runtime: bytes, count: int) -> tuple[int, list[str]]:
    root = runtime[2] | runtime[3] << 8
    offset = root - 0xF000
    if not 0 <= offset < len(runtime):
        raise ValueError(f"room text root ${root:04X} lies outside the runtime")
    decoder = RoomTextDecoder(runtime[offset:])
    return root, [decoder.decode(index) for index in range(count)]


def _entity_records(memory: bytes, room_id: int) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index in range(96):
        address = 0xC400 + index * 8
        raw = memory[address : address + 8]
        if raw[0] & 0x80:
            break
        if raw[0] == room_id:
            records.append(
                {
                    "index": index,
                    "address": f"0x{address:04X}",
                    "raw": raw.hex(),
                    "slot": raw[1] & 3,
                    "render_flags": raw[1],
                    "logical_x": raw[2],
                    "logical_y": raw[3],
                    "colors": raw[4],
                    "activation": raw[5],
                }
            )
    return records


def extract_room(
    memory_data: bytes,
    images: dict[int, D64Image],
    room_id: int,
    location_room_id: int,
    text_count: int,
) -> tuple[dict[str, object], dict[str, bytes]]:
    if len(memory_data) != MEMORY_SIZE:
        raise ValueError("source memory must be exactly 64 KiB")
    if not 0 <= room_id < 60:
        raise ValueError("room ID must be in the 60-entry room table")
    memory = bytearray(memory_data)
    side_byte = memory[ROOM_SIDE_TABLE + room_id]
    if side_byte not in (ord("2"), ord("3"), ord("4")):
        raise ValueError(f"room {room_id} has no valid side mapping")
    side = side_byte - ord("0")
    if side not in images:
        raise ValueError(f"game side {side} image was not provided")

    location = _location_tuple(memory, location_room_id)
    if location is None:
        raise ValueError(f"room {location_room_id} does not select a location overlay")
    location_index, location_side, location_track, location_sector = location
    if location_side not in images:
        raise ValueError(f"location side {location_side} image was not provided")

    location_data, location_report = _module(
        images[location_side],
        f"location_room{location_room_id}_ac80",
        SectorRef(location_track, location_sector),
        0xAC80,
        "selected location overlay retained while entering the room",
    )
    room_track = memory[ROOM_TRACK_TABLE + room_id]
    room_sector = memory[ROOM_SECTOR_TABLE + room_id]
    room_data, room_report = _module(
        images[side],
        f"room{room_id}_logic_ca00",
        SectorRef(room_track, room_sector),
        0xCA00,
        "room logic, compressed display, strings, and sprite data",
    )
    overlay(memory, 0xAC80, location_data)
    overlay(memory, 0xCA00, room_data)
    memory[ROOM_ID_ADDRESS] = room_id
    memory[0xF000:0xFC00] = memory[0xCA00:0xD600]
    runtime = bytes(memory[0xF000:0xFC00])
    text_root, strings = _decode_strings(runtime, text_count)

    terminal_enabled = runtime[0x27] == 1
    terminal = {
        "pax_enabled": terminal_enabled,
        "room_flag_address": "0xF027",
        "room_flag_value": runtime[0x27],
        "resident_entry": "0x49CB" if terminal_enabled else None,
        "shell_entry": "0x7400" if terminal_enabled else None,
    }
    # PAX shell $7451 calls $57B2 with inline pointer $774D. The target uses
    # one count byte followed by five-byte x/y/width/height/event records.
    hit_regions = {
        "format": ["x", "y", "width", "height", "event"],
        "source": "PAX shell inline pointer at 0x7454 -> 0x774D",
        "sets": [
            {
                "name": "pax_primary",
                "address": "0x774D",
                "regions": [
                    {"x": 4, "y": 5, "width": 2, "height": 25, "event": 1}
                ],
            }
        ] if terminal_enabled else [],
    }
    report: dict[str, object] = {
        "schema": 1,
        "room_id": room_id,
        "display_name": strings[1] if len(strings) > 1 else strings[0],
        "source_memory_sha256": sha256(memory_data),
        "selection": {
            "room": {"side": side, "track": room_track, "sector": room_sector},
            "location": {
                "room_id": location_room_id,
                "index": location_index,
                "side": location_side,
                "track": location_track,
                "sector": location_sector,
            },
        },
        "modules": [location_report, room_report],
        "runtime": {
            "address": "0xF000",
            "length": len(runtime),
            "sha256": sha256(runtime),
            "text_root": f"0x{text_root:04X}",
        },
        "strings": [{"id": index, "text": text} for index, text in enumerate(strings)],
        "entities": _entity_records(memory, room_id),
        "terminal": terminal,
        "hit_regions": hit_regions,
        "native_assets": {
            "screen": {"address": "0x0400", "length": 1000},
            "charset": {"address": "0x2000", "length": 2048},
            "color": {"address": "0xD800", "length": 1000},
            "sprite_workspace": {"address": "0x0840", "length": 128},
            "logical_dimensions": [320, 200],
        },
    }
    return report, {
        "memory": bytes(memory),
        "runtime": runtime,
        "location_overlay": location_data,
        "room_logic": room_data,
        "terminal": json.dumps(terminal, indent=2).encode() + b"\n",
        "hit_regions": json.dumps(hit_regions, indent=2).encode() + b"\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("side2", type=Path)
    parser.add_argument("side3", type=Path)
    parser.add_argument("side4", type=Path)
    parser.add_argument("room_id", type=int)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--location-room", type=int, default=0)
    parser.add_argument("--text-count", type=int, default=5)
    args = parser.parse_args()
    report, assets = extract_room(
        args.snapshot.read_bytes(),
        {
            2: D64Image.read(args.side2),
            3: D64Image.read(args.side3),
            4: D64Image.read(args.side4),
        },
        args.room_id,
        args.location_room,
        args.text_count,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"e1_room{args.room_id}"
    suffixes = {
        "memory": "ready_memory.bin",
        "runtime": "runtime.bin",
        "location_overlay": "location_overlay_ac80.bin",
        "room_logic": "logic_ca00.bin",
        "terminal": "terminal.json",
        "hit_regions": "hit_regions.json",
    }
    for key, data in assets.items():
        (args.output_dir / f"{stem}_{suffixes[key]}").write_bytes(data)
    (args.output_dir / f"{stem}_map.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(f"extracted room {args.room_id}: {report['display_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
