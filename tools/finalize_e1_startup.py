#!/usr/bin/env python3
"""Execute E1's self-erasing $020A stub to the stable game entry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .dis import Image, disassemble
    from .emu.cpu6502 import Cpu6502
except ImportError:  # Direct `python3 tools/finalize_e1_startup.py` invocation.
    from dis import Image, disassemble
    from emu.cpu6502 import Cpu6502


ENTRY = 0x020A
GAME_ENTRY = 0x03E7
MEMORY_SIZE = 0x10000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execute_final_stub(path: Path) -> tuple[bytes, dict[str, object]]:
    source = path.read_bytes()
    if len(source) != MEMORY_SIZE:
        raise ValueError("E1 stage-3 snapshot must be exactly 64 KiB")
    memory = bytearray(source)
    cpu = Cpu6502(memory)
    cpu.pc = ENTRY
    cpu.a = 0x00
    cpu.x = 0x00
    cpu.y = 0xFF
    cpu.sp = 0xF9
    cpu.p = 0x27
    steps = cpu.run_until(GAME_ENTRY, max_steps=10_000)

    if any(memory[0x020A:0x0249]):
        raise ValueError("self-erasing startup range $020A-$0248 is not zero")
    if source[0x01FA:0x01FE] != bytes.fromhex("C7 E0 E7 03"):
        raise ValueError("unexpected crafted stack return frame")

    result = bytes(memory)
    report: dict[str, object] = {
        "source": str(path),
        "source_sha256": sha256(source),
        "entry": f"0x{ENTRY:04X}",
        "game_entry": f"0x{GAME_ENTRY:04X}",
        "instructions_executed": steps,
        "self_erased_range": "0x020A-0x0248",
        "crafted_stack_frame": {
            "initial_sp": "0xF9",
            "pla_value_at_0x01FA": "0xC7",
            "rti_status_at_0x01FB": "0xE0",
            "rti_pc_low_at_0x01FC": "0xE7",
            "rti_pc_high_at_0x01FD": "0x03",
        },
        "output_memory_sha256": sha256(result),
        "registers_at_game_entry": {
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
        GAME_ENTRY: ("e1_game_entry", "Stable entry after all crack/depack stages"),
    }
    lines = disassemble(Image(memory, 0), GAME_ENTRY, 260, labels)
    return (
        f"===== E1 STABLE GAME ENTRY [${GAME_ENTRY:04X}] =====\n"
        + "\n".join(lines)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage3_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    memory, report = execute_final_stub(args.stage3_memory)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_path = args.output_dir / "e1_game_memory.bin"
    report_path = args.output_dir / "e1_game_entry.json"
    listing_path = args.output_dir / "e1_game_entry_listing.txt"
    memory_path.write_bytes(memory)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    listing_path.write_text(build_listing(memory), encoding="utf-8")

    print(
        f"executed {report['instructions_executed']} instructions; "
        f"reached stable game entry ${GAME_ENTRY:04X}"
    )
    print(f"memory SHA-256 {report['output_memory_sha256']}")
    print(f"wrote {memory_path}")
    print(f"wrote {report_path}")
    print(f"wrote {listing_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
