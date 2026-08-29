#!/usr/bin/env python3
"""Execute the unpacked E1 relocation/hardware setup to its runtime entry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .dis import Image, disassemble
    from .emu.cpu6502 import Cpu6502
except ImportError:  # Direct `python3 tools/analyze_e1_runtime_init.py` invocation.
    from dis import Image, disassemble
    from emu.cpu6502 import Cpu6502


INIT_ENTRY = 0x080D
RUNTIME_ENTRY = 0x008E
MEMORY_SIZE = 0x10000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execute_runtime_init(path: Path) -> tuple[bytes, dict[str, object]]:
    source = path.read_bytes()
    if len(source) != MEMORY_SIZE:
        raise ValueError("E1 unpacked snapshot must be exactly 64 KiB")
    memory = bytearray(source)
    cpu = Cpu6502(memory)
    cpu.pc = INIT_ENTRY
    cpu.a = 0x37
    cpu.x = 0x02
    cpu.y = 0x07
    cpu.sp = 0xFC
    cpu.p = 0x21
    steps = cpu.run_until(RUNTIME_ENTRY, max_steps=2_000_000)

    if memory[0x008E] == 0:
        raise ValueError("zero-page runtime entry was not installed")
    if memory[0x0100:0x0200] != memory[0x0A00:0x0B00]:
        raise ValueError("stack-page runtime block differs from its source")
    # Startup deliberately modifies the 6510 port and two freshly installed
    # zero-page state bytes after the copy, so compare every other byte.
    for offset in range(0x100):
        if offset in {0x01, 0xC3, 0xC8}:
            continue
        if memory[offset] != source[0x0900 + offset]:
            raise ValueError(f"zero-page runtime copy differs at ${offset:02X}")

    changed = [address for address in range(MEMORY_SIZE) if source[address] != memory[address]]
    result = bytes(memory)
    report: dict[str, object] = {
        "source": str(path),
        "source_sha256": sha256(source),
        "entry": f"0x{INIT_ENTRY:04X}",
        "runtime_entry": f"0x{RUNTIME_ENTRY:04X}",
        "instructions_executed": steps,
        "changed_address_start": f"0x{min(changed):04X}",
        "changed_address_end": f"0x{max(changed):04X}",
        "output_memory_sha256": sha256(result),
        "large_relocation": {
            "source": "0x0C50-0xE922 (descending overlapping pages)",
            "destination": "0x232D-0xFFFF (descending overlapping pages)",
            "delta": "0x16DD",
        },
        "low_memory_install": [
            {"source": "0x0A00-0x0AFF", "destination": "0x0100-0x01FF"},
            {"source": "0x0900-0x09FF", "destination": "0x0000-0x00FF"},
        ],
        "color_initialization": [
            {"source": "0x0B00-0x0BFF", "destination": "0xD800-0xD8FF"},
            {"source": "0x0C00-0x0CFF", "destination": "0xD900-0xD9FF"},
            {"derived_high_nibbles": "0xDA00-0xDBFF"},
        ],
        "registers_at_entry": {
            "A": f"0x{cpu.a:02X}",
            "X": f"0x{cpu.x:02X}",
            "Y": f"0x{cpu.y:02X}",
            "SP": f"0x{cpu.sp:02X}",
            "P": f"0x{cpu.p:02X}",
        },
    }
    return result, report


def build_listing(memory: bytes) -> str:
    labels = {
        0x008E: ("e1_runtime_entry", "Entry after unpacking and hardware setup"),
    }
    lines = disassemble(Image(memory, 0), RUNTIME_ENTRY, 220, labels)
    return (
        f"===== E1 RUNTIME ENTRY [${RUNTIME_ENTRY:04X}] =====\n"
        + "\n".join(lines)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unpacked_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    memory, report = execute_runtime_init(args.unpacked_memory)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_path = args.output_dir / "e1_runtime_memory.bin"
    report_path = args.output_dir / "e1_runtime_init.json"
    listing_path = args.output_dir / "e1_runtime_entry_listing.txt"
    memory_path.write_bytes(memory)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    listing_path.write_text(build_listing(memory), encoding="utf-8")

    print(
        f"executed {report['instructions_executed']} instructions; "
        f"reached ${RUNTIME_ENTRY:04X}"
    )
    print(f"memory SHA-256 {report['output_memory_sha256']}")
    print(f"wrote {memory_path}")
    print(f"wrote {report_path}")
    print(f"wrote {listing_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
