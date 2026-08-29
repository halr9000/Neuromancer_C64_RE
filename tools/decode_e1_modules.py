#!/usr/bin/env python3
"""Decode the raw-sector modules loaded by E1 file A's fastloader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image, SECTORS_PER_TRACK, SectorRef
except ImportError:  # Direct `python3 tools/decode_e1_modules.py` invocation.
    from d64 import D64Image, SECTORS_PER_TRACK, SectorRef


MEMORY_SIZE = 0x10000
FILE_A_LOAD = 0x3E00


class ModuleSpec:
    __slots__ = ("name", "start", "destination", "role")

    def __init__(self, name: str, start: SectorRef, destination: int, role: str) -> None:
        self.name = name
        self.start = start
        self.destination = destination
        self.role = role


COMMON_MODULES = (
    ModuleSpec("core_4300", SectorRef(1, 2), 0x4300, "main runtime and entry"),
    # Startup uses LDY #$13: hexadecimal $13 is sector 19, not sector 13.
    ModuleSpec(
        "room_disk_tables_fe00",
        SectorRef(6, 19),
        0xFE00,
        "room-to-side/track/sector tables in RAM beneath KERNAL",
    ),
    ModuleSpec("module_b800", SectorRef(3, 10), 0xB800, "high-memory runtime module"),
    ModuleSpec("module_c700", SectorRef(3, 19), 0xC700, "high-memory runtime module"),
)

STATE_MODULES = (
    ModuleSpec("state_new", SectorRef(4, 1), 0xC100, "new-game template"),
    ModuleSpec("state_slot_1", SectorRef(4, 7), 0xC100, "old-game slot 1"),
    ModuleSpec("state_slot_2", SectorRef(4, 16), 0xC100, "old-game slot 2"),
    ModuleSpec("state_slot_3", SectorRef(5, 4), 0xC100, "old-game slot 3"),
    ModuleSpec("state_slot_4", SectorRef(5, 13), 0xC100, "old-game slot 4"),
)

TAIL_MODULES = (
    ModuleSpec("module_0380", SectorRef(3, 9), 0x0380, "low-memory runtime module"),
    ModuleSpec("module_a400", SectorRef(13, 0), 0xA400, "BASIC-ROM underlay module"),
    ModuleSpec("module_8400", SectorRef(32, 10), 0x8400, "main high-memory module"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def next_loader_sector(ref: SectorRef) -> SectorRef:
    sector = ref.sector + 1
    track = ref.track
    if sector == SECTORS_PER_TRACK[track]:
        sector = 0
        track += 1
        if track == 18:
            sector = 1  # The loader deliberately skips the BAM at T18/S00.
    if track > 35:
        raise ValueError(f"module beginning at {ref} runs beyond track 35")
    return SectorRef(track, sector)


def decode_module(image: D64Image, spec: ModuleSpec) -> tuple[bytes, dict[str, object]]:
    first = image.sector(spec.start)
    length = first[0] | first[1] << 8
    if length == 0:
        raise ValueError(f"zero-length module at {spec.start}")
    output = bytearray(first[2:])
    refs = [spec.start]
    ref = spec.start
    while len(output) < length:
        ref = next_loader_sector(ref)
        refs.append(ref)
        output.extend(image.sector(ref))
    data = bytes(output[:length])
    absolute_end = spec.destination + len(data)
    if len(data) > MEMORY_SIZE:
        raise ValueError(f"{spec.name} exceeds the complete C64 address space")
    end_exclusive = absolute_end & 0xFFFF
    if absolute_end <= MEMORY_SIZE:
        address_ranges = [f"0x{spec.destination:04X}-0x{absolute_end - 1:04X}"]
    else:
        address_ranges = [
            f"0x{spec.destination:04X}-0xFFFF",
            f"0x0000-0x{end_exclusive - 1:04X}",
        ]
    report: dict[str, object] = {
        "name": spec.name,
        "role": spec.role,
        "start": str(spec.start),
        "sectors": [str(item) for item in refs],
        "sector_count": len(refs),
        "encoded_length": length,
        "destination": f"0x{spec.destination:04X}",
        "end_exclusive": f"0x{end_exclusive:04X}",
        "wraps_address_space": absolute_end > MEMORY_SIZE,
        "address_ranges": address_ranges,
        "sha256": sha256(data),
    }
    return data, report


def overlay(memory: bytearray, destination: int, data: bytes) -> None:
    if len(data) > len(memory):
        raise ValueError("overlay exceeds complete memory")
    first = min(len(data), len(memory) - destination)
    memory[destination : destination + first] = data[:first]
    remaining = data[first:]
    if remaining:
        memory[: len(remaining)] = remaining


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("game_memory", type=Path)
    parser.add_argument("file_a", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    image = D64Image.read(args.image)
    base_memory = args.game_memory.read_bytes()
    if len(base_memory) != MEMORY_SIZE:
        raise ValueError("stable E1 game snapshot must be exactly 64 KiB")
    file_a = args.file_a.read_bytes()
    if len(file_a) < 2 or (file_a[0] | file_a[1] << 8) != FILE_A_LOAD:
        raise ValueError("unexpected E1 file A load address")
    file_a_payload = file_a[2:]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    decoded: dict[str, tuple[ModuleSpec, bytes, dict[str, object]]] = {}
    reports: list[dict[str, object]] = []
    for spec in (*COMMON_MODULES, *STATE_MODULES, *TAIL_MODULES):
        data, report = decode_module(image, spec)
        decoded[spec.name] = (spec, data, report)
        reports.append(report)
        output_path = args.output_dir / f"e1_{spec.name}.bin"
        output_path.write_bytes(data)
        print(
            f"{spec.name}: {spec.start} -> ${spec.destination:04X}, "
            f"{len(data)} bytes over {report['sector_count']} sectors"
        )

    drive_block = image.sector(SectorRef(18, 2))
    drive_path = args.output_dir / "e1_drive_block_execute_t18_s02.bin"
    drive_path.write_bytes(drive_block)

    new_memory = bytearray(base_memory)
    overlay(new_memory, FILE_A_LOAD, file_a_payload)
    for spec in COMMON_MODULES:
        overlay(new_memory, spec.destination, decoded[spec.name][1])
    new_state = STATE_MODULES[0]
    overlay(new_memory, new_state.destination, decoded[new_state.name][1])
    for spec in TAIL_MODULES:
        overlay(new_memory, spec.destination, decoded[spec.name][1])
    new_memory_path = args.output_dir / "e1_new_game_ready_memory.bin"
    new_memory_path.write_bytes(new_memory)

    report = {
        "source_image": str(args.image),
        "source_sha256": sha256(image.data),
        "loader_file": str(args.file_a),
        "loader_file_sha256": sha256(file_a),
        "loader_entries": {
            "initialize_drive": "0x400E -> 0x42B1",
            "load_module": "0x4011",
            "drive_command": "B-E 2 0 18 02",
            "final_handoff": "0x4300",
        },
        "drive_block_execute": {
            "source": "T18/S02",
            "bytes": len(drive_block),
            "sha256": sha256(drive_block),
        },
        "modules": reports,
        "state_selection": {
            "new_game": "T04/S01",
            "old_game_slots": ["T04/S07", "T04/S16", "T05/S04", "T05/S13"],
        },
        "new_game_ready_snapshot": {
            "file": new_memory_path.name,
            "entry": "0x4300",
            "sha256": sha256(new_memory),
        },
    }
    map_path = args.output_dir / "e1_module_map.json"
    map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"drive block T18/S02 SHA-256 {sha256(drive_block)}")
    print(f"new-game snapshot SHA-256 {sha256(new_memory)}")
    print(f"wrote {map_path}")
    print(f"wrote {new_memory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
