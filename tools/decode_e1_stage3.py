#!/usr/bin/env python3
"""Execute the E1 zero-page stream decoder through its $020A handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .dis import Image, disassemble
    from .emu.cpu6502 import Cpu6502, CpuError
except ImportError:  # Direct `python3 tools/decode_e1_stage3.py` invocation.
    from dis import Image, disassemble
    from emu.cpu6502 import Cpu6502, CpuError


ENTRY = 0x008E
RASTER_WAIT = 0x00A8
HANDOFF = 0x020A
MEMORY_SIZE = 0x10000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execute_stage3(path: Path) -> tuple[bytes, dict[str, object]]:
    source = path.read_bytes()
    if len(source) != MEMORY_SIZE:
        raise ValueError("E1 runtime snapshot must be exactly 64 KiB")
    memory = bytearray(source)
    cpu = Cpu6502(memory)
    cpu.pc = ENTRY
    cpu.a = 0x7F
    cpu.x = 0x06
    cpu.y = 0x00
    cpu.sp = 0xF9
    cpu.p = 0x27

    raster_stubbed = False
    max_steps = 20_000_000
    while cpu.pc != HANDOFF:
        if cpu.steps >= max_steps:
            raise CpuError(f"step limit reached before ${HANDOFF:04X}; PC=${cpu.pc:04X}")
        if cpu.pc == RASTER_WAIT:
            # The decoded bytes are already complete here. Supply the single
            # VIC-II raster value expected by the post-decode delay loop.
            memory[0xD012] = 0x80
            raster_stubbed = True
        cpu.step()
    if not raster_stubbed:
        raise ValueError("stage 3 never reached its raster synchronization loop")

    changed = [address for address in range(MEMORY_SIZE) if source[address] != memory[address]]
    result = bytes(memory)
    report: dict[str, object] = {
        "source": str(path),
        "source_sha256": sha256(source),
        "method": "execute zero-page stream decoder; supply VIC-II raster $80 at the post-decode wait",
        "entry": f"0x{ENTRY:04X}",
        "handoff": f"0x{HANDOFF:04X}",
        "instructions_executed": cpu.steps,
        "changed_address_start": f"0x{min(changed):04X}",
        "changed_address_end": f"0x{max(changed):04X}",
        "output_memory_sha256": sha256(result),
        "stream_source_initial": "0x242D (self-modifying LDA at $0060)",
        "runtime_entry_installed": memory[HANDOFF] != 0,
        "registers_at_handoff": {
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
        HANDOFF: ("e1_stage3_handoff", "Entry after zero-page stream decoder"),
    }
    lines = disassemble(Image(memory, 0), HANDOFF, 240, labels)
    return (
        f"===== E1 POST-STAGE3 ENTRY [${HANDOFF:04X}] =====\n"
        + "\n".join(lines)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    memory, report = execute_stage3(args.runtime_memory)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_path = args.output_dir / "e1_stage3_memory.bin"
    report_path = args.output_dir / "e1_stage3_decode.json"
    listing_path = args.output_dir / "e1_stage3_entry_listing.txt"
    memory_path.write_bytes(memory)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    listing_path.write_text(build_listing(memory), encoding="utf-8")

    print(
        f"executed {report['instructions_executed']} instructions; "
        f"reached ${HANDOFF:04X}"
    )
    print(f"memory SHA-256 {report['output_memory_sha256']}")
    print(f"wrote {memory_path}")
    print(f"wrote {report_path}")
    print(f"wrote {listing_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
