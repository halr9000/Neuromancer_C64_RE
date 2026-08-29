#!/usr/bin/env python3
"""Reconstruct the first playable room reached by a new E1 game."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image, SectorRef
    from .decode_e1_modules import ModuleSpec, decode_module, overlay
    from .dis import Image, disassemble, load_labels
except ImportError:  # Direct `python3 tools/decode_e1_first_room.py` invocation.
    from d64 import D64Image, SectorRef
    from decode_e1_modules import ModuleSpec, decode_module, overlay
    from dis import Image, disassemble, load_labels


MEMORY_SIZE = 0x10000
ROOM_ID_ADDRESS = 0xC330
ROOM_TRACK_TABLE = 0xFE00
ROOM_SECTOR_TABLE = 0xFE3C
ROOM_SIDE_TABLE = 0xFE78
LOCATION_ID_TABLE = 0x62C5
LOCATION_TRACK_TABLE = 0x62E3
LOCATION_SECTOR_TABLE = 0x6301
LOCATION_COUNT = 30
ROOM_STAGING_START = 0xCA00
ROOM_RUNTIME_START = 0xF000
ROOM_RUNTIME_LENGTH = 0x0C00


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def report_module(
    image: D64Image,
    spec: ModuleSpec,
    output_dir: Path,
) -> tuple[bytes, dict[str, object]]:
    data, report = decode_module(image, spec)
    output_path = output_dir / f"e1_{spec.name}.bin"
    output_path.write_bytes(data)
    report["source_image_sha256"] = sha256(image.data)
    report["output_file"] = output_path.name
    return data, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("side1", type=Path, help="NEUROMA0.D64 (game side 1)")
    parser.add_argument("side2", type=Path, help="NEUROMA1.D64 (game side 2)")
    parser.add_argument("new_game_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--labels", type=Path, default=Path("labels.csv"))
    args = parser.parse_args()

    memory_data = args.new_game_memory.read_bytes()
    if len(memory_data) != MEMORY_SIZE:
        raise ValueError("new-game snapshot must be exactly 64 KiB")
    memory = bytearray(memory_data)
    side1 = D64Image.read(args.side1)
    side2 = D64Image.read(args.side2)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    room_id = memory[ROOM_ID_ADDRESS]
    if room_id != 0:
        raise ValueError(f"expected new-game room 0, found {room_id}")
    room_track = memory[ROOM_TRACK_TABLE + room_id]
    room_sector = memory[ROOM_SECTOR_TABLE + room_id]
    room_side_ascii = memory[ROOM_SIDE_TABLE + room_id]
    if room_side_ascii != ord("2"):
        raise ValueError(f"room 0 unexpectedly maps to side byte ${room_side_ascii:02X}")

    try:
        location_index = memory[
            LOCATION_ID_TABLE : LOCATION_ID_TABLE + LOCATION_COUNT
        ].index(room_id)
    except ValueError as error:
        raise ValueError("new-game room has no location-overlay entry") from error
    location_track = memory[LOCATION_TRACK_TABLE + location_index]
    location_sector = memory[LOCATION_SECTOR_TABLE + location_index]
    location_side = 2 if location_index < 0x13 else 3
    if location_side != 2:
        raise ValueError("new-game location overlay unexpectedly maps away from side 2")

    specs = (
        (
            side1,
            ModuleSpec(
                "side1_frontend_ca00",
                SectorRef(6, 6),
                0xCA00,
                "side-1 location/graphics payload loaded during first-time initialization",
            ),
        ),
        (
            side2,
            ModuleSpec(
                "side2_room0_overlay_ac80",
                SectorRef(location_track, location_sector),
                0xAC80,
                "room-0 overlay selected by the core room-ID table",
            ),
        ),
        (
            side2,
            ModuleSpec(
                "side2_room0_logic_ca00",
                SectorRef(room_track, room_sector),
                ROOM_STAGING_START,
                "room-0 logic/data selected by the tables at $FE00/$FE3C/$FE78",
            ),
        ),
    )

    reports: list[dict[str, object]] = []
    decoded: dict[str, bytes] = {}
    for image, spec in specs:
        data, report = report_module(image, spec, args.output_dir)
        decoded[spec.name] = data
        reports.append(report)
        overlay(memory, spec.destination, data)
        print(
            f"{spec.name}: {spec.start} -> ${spec.destination:04X}, "
            f"{len(data)} bytes over {report['sector_count']} sectors"
        )

    memory[
        ROOM_RUNTIME_START : ROOM_RUNTIME_START + ROOM_RUNTIME_LENGTH
    ] = memory[ROOM_STAGING_START : ROOM_STAGING_START + ROOM_RUNTIME_LENGTH]
    runtime = bytes(memory[ROOM_RUNTIME_START : ROOM_RUNTIME_START + ROOM_RUNTIME_LENGTH])
    if runtime[0x0A:0x13] != bytes.fromhex("4C F6 F0 4C 0E F1 4C 0D F1"):
        raise ValueError("room-0 runtime jump vectors were not reconstructed")

    snapshot_path = args.output_dir / "e1_room0_ready_memory.bin"
    snapshot_path.write_bytes(memory)

    labels = load_labels(args.labels)
    listing_sections: list[str] = []
    for title, start, lines in (
        ("ROOM RUNTIME VECTORS", 0xF000, 28),
        ("ROOM TICK/STATE ROUTINES", 0xF0F6, 72),
        ("ROOM DATA ROOT", 0xF248, 48),
    ):
        listing_sections.append(f"===== {title} [${start:04X}] =====")
        listing_sections.extend(disassemble(Image(bytes(memory), 0), start, lines, labels))
        listing_sections.append("")
    listing_path = args.output_dir / "e1_room0_runtime_listing.txt"
    listing_path.write_text("\n".join(listing_sections), encoding="utf-8")

    report = {
        "new_game_snapshot": str(args.new_game_memory),
        "new_game_snapshot_sha256": sha256(memory_data),
        "room_id": room_id,
        "table_derivation": {
            "room_logic": {
                "side_table": "0xFE78",
                "track_table": "0xFE00",
                "sector_table": "0xFE3C",
                "selected_side": chr(room_side_ascii),
                "selected_track": room_track,
                "selected_sector": room_sector,
            },
            "room_overlay": {
                "room_id_table": "0x62C5",
                "track_table": "0x62E3",
                "sector_table": "0x6301",
                "selected_index": location_index,
                "selected_side": location_side,
                "selected_track": location_track,
                "selected_sector": location_sector,
            },
        },
        "modules": reports,
        "runtime_copy": {
            "source": "0xCA00-0xD5FF",
            "destination": "0xF000-0xFBFF",
            "bytes": ROOM_RUNTIME_LENGTH,
            "sha256": sha256(runtime),
            "jump_vectors": {
                "0xF00A": "0xF0F6",
                "0xF00D": "0xF10E",
                "0xF010": "0xF10D",
            },
        },
        "room0_ready_snapshot": {
            "file": snapshot_path.name,
            "sha256": sha256(memory),
        },
        "listing": listing_path.name,
    }
    map_path = args.output_dir / "e1_room0_map.json"
    map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"room runtime SHA-256 {sha256(runtime)}")
    print(f"room-0 snapshot SHA-256 {sha256(memory)}")
    print(f"wrote {map_path}")
    print(f"wrote {snapshot_path}")
    print(f"wrote {listing_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
