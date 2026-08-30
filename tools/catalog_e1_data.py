#!/usr/bin/env python3
"""Catalog the raw room and location modules selected by the E1 runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

try:
    from .d64 import D64Image, SectorRef
    from .decode_e1_modules import ModuleSpec, decode_module
except ImportError:  # Direct ``python3 tools/catalog_e1_data.py`` invocation.
    from d64 import D64Image, SectorRef
    from decode_e1_modules import ModuleSpec, decode_module


MEMORY_SIZE = 0x10000
ROOM_TABLE_COUNT = 60
ROOM_TRACK_TABLE = 0xFE00
ROOM_SECTOR_TABLE = 0xFE3C
ROOM_SIDE_TABLE = 0xFE78
LOCATION_ID_TABLE = 0x62C5
LOCATION_TRACK_TABLE = 0x62E3
LOCATION_SECTOR_TABLE = 0x6301
LOCATION_COUNT = 30
SIDE_MARKER_REF = SectorRef(18, 0)
SIDE_MARKER_OFFSET = 0xDC


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_snapshot(snapshot: bytes) -> None:
    if len(snapshot) != MEMORY_SIZE:
        raise ValueError("E1 snapshot must be exactly 64 KiB")


def _module_record(
    image: D64Image,
    *,
    name: str,
    role: str,
    side: int,
    track: int,
    sector: int,
    extra: dict[str, int],
) -> dict[str, object]:
    start = SectorRef(track, sector)
    data, report = decode_module(
        image,
        ModuleSpec(name, start, 0xCA00, role),
    )
    result: dict[str, object] = {
        **extra,
        "tuple": {"side": side, "track": track, "sector": sector},
        "start": str(start),
        "encoded_length": len(data),
        "sector_count": report["sector_count"],
        "sectors": report["sectors"],
        "sha256": sha256(data),
    }
    return result


def _side_runs(entries: list[dict[str, object]]) -> list[dict[str, int]]:
    runs: list[dict[str, int]] = []
    for entry in entries:
        room_id = int(entry["room_id"])
        side = int(entry["tuple"]["side"])
        if not runs or runs[-1]["side"] != side:
            runs.append({
                "side": side,
                "first_room": room_id,
                "last_room": room_id,
                "count": 1,
                "rooms": [room_id],
            })
        else:
            runs[-1]["last_room"] = room_id
            runs[-1]["count"] += 1
            runs[-1]["rooms"].append(room_id)
    return runs


def _side_transitions(runs: list[dict[str, int]]) -> list[dict[str, int]]:
    return [
        {
            "from_side": previous["side"],
            "to_side": current["side"],
            "at_room": current["first_room"],
        }
        for previous, current in zip(runs, runs[1:])
    ]


def catalog_dataset(
    snapshot: bytes,
    side_images: Mapping[int, D64Image],
) -> dict[str, object]:
    """Decode every room and location tuple represented in the E1 tables."""

    _validate_snapshot(snapshot)
    required_sides = {2, 3, 4}
    missing_sides = sorted(required_sides - set(side_images))
    if missing_sides:
        raise ValueError(f"missing side images: {missing_sides}")

    room_entries: list[dict[str, object]] = []
    invalid_entries: list[int] = []
    for room_id in range(ROOM_TABLE_COUNT):
        side_marker = snapshot[ROOM_SIDE_TABLE + room_id]
        track = snapshot[ROOM_TRACK_TABLE + room_id]
        sector = snapshot[ROOM_SECTOR_TABLE + room_id]
        if side_marker == 0xFF and track == 0xFF and sector == 0xFF:
            invalid_entries.append(room_id)
            continue
        if side_marker not in (ord("2"), ord("3")):
            raise ValueError(f"room {room_id} has invalid side marker ${side_marker:02X}")
        if track == 0xFF or sector == 0xFF:
            raise ValueError(f"room {room_id} has an incomplete sector tuple")
        side = side_marker - ord("0")
        room_entries.append(
            _module_record(
                side_images[side],
                name=f"room_{room_id:02d}",
                role="room logic/data selected by the E1 room tables",
                side=side,
                track=track,
                sector=sector,
                extra={"room_id": room_id},
            )
        )

    overlay_entries: list[dict[str, object]] = []
    for index in range(LOCATION_COUNT):
        room_id = snapshot[LOCATION_ID_TABLE + index]
        track = snapshot[LOCATION_TRACK_TABLE + index]
        sector = snapshot[LOCATION_SECTOR_TABLE + index]
        side = 2 if index < 0x13 else 3
        overlay_entries.append(
            _module_record(
                side_images[side],
                name=f"location_overlay_{index:02d}",
                role="location overlay selected by the E1 room-ID table",
                side=side,
                track=track,
                sector=sector,
                extra={"location_index": index, "room_id": room_id},
            )
        )

    source_sides: dict[str, dict[str, object]] = {}
    for side in sorted(required_sides):
        marker = side_images[side].sector(SIDE_MARKER_REF)[SIDE_MARKER_OFFSET]
        if marker != ord(str(side)):
            raise ValueError(
                f"side {side} marker is ${marker:02X}, expected ASCII {side}"
            )
        source_sides[str(side)] = {
            "label": f"E{side}",
            "marker": chr(marker),
            "image_sha256": sha256(side_images[side].data),
            "room_modules": sum(
                entry["tuple"]["side"] == side for entry in room_entries
            ),
            "overlay_modules": sum(
                entry["tuple"]["side"] == side for entry in overlay_entries
            ),
        }

    runs = _side_runs(room_entries)
    return {
        "snapshot_sha256": sha256(snapshot),
        "source_sides": source_sides,
        "room_table": {
            "track_table": "0xFE00",
            "sector_table": "0xFE3C",
            "side_table": "0xFE78",
            "entry_count": ROOM_TABLE_COUNT,
            "valid_count": len(room_entries),
            "invalid_entries": invalid_entries,
            "entries": room_entries,
            "side_runs": runs,
            "side_transitions": _side_transitions(runs),
        },
        "location_overlays": {
            "room_id_table": "0x62C5",
            "track_table": "0x62E3",
            "sector_table": "0x6301",
            "entry_count": LOCATION_COUNT,
            "side_rule": "indices 0x00-0x12 use E2; indices 0x13-0x1D use E3",
            "side_counts": {
                str(side): sum(
                    entry["tuple"]["side"] == side for entry in overlay_entries
                )
                for side in (2, 3)
            },
            "entries": overlay_entries,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("side2", type=Path, help="NEUROMA1.D64")
    parser.add_argument("side3", type=Path, help="NEUROMA2.D64")
    parser.add_argument("side4", type=Path, help="NEUROMA3.D64")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    report = catalog_dataset(
        args.snapshot.read_bytes(),
        {
            2: D64Image.read(args.side2),
            3: D64Image.read(args.side3),
            4: D64Image.read(args.side4),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"cataloged {report['room_table']['valid_count']} room modules and "
        f"{report['location_overlays']['entry_count']} location overlays"
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
