#!/usr/bin/env python3
"""Execute the relocated DOX depacker until its verified $24BF handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .emu.cpu6502 import Cpu6502, FLAG_I, FLAG_U
    from .relocate_e5_viewers import relocate_dox
except ImportError:
    from emu.cpu6502 import Cpu6502, FLAG_I, FLAG_U
    from relocate_e5_viewers import relocate_dox


ENTRY = 0x03AD
FIRST_HANDOFF = 0x24BF
FINAL_HANDOFF = 0x0A00
BASIC_PRINT_STRING = 0xAB1E


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    relocated, relocation_map = relocate_dox(args.prg)
    memory = bytearray(relocated)
    before = bytes(memory)
    cpu = Cpu6502(memory)
    cpu.pc = ENTRY
    cpu.x = 0
    cpu.sp = 0xFF
    cpu.p = FLAG_I | FLAG_U
    first_stage_steps = cpu.run_until(FIRST_HANDOFF)

    # $24BF shows a short credit via BASIC ROM, delays, installs a third-stage
    # backwards RLE depacker, and hands off to the final viewer at $0A00. The
    # ROM print call does not affect decompressed bytes, so emulate its RTS.
    while cpu.pc != FINAL_HANDOFF:
        if cpu.steps >= 20_000_000:
            raise RuntimeError(f"step limit reached before ${FINAL_HANDOFF:04X}")
        if cpu.pc == BASIC_PRINT_STRING:
            low = cpu.pop()
            high = cpu.pop()
            cpu.pc = ((low | high << 8) + 1) & 0xFFFF
            continue
        cpu.step()
    final_steps = cpu.steps

    changed = [address for address in range(0x10000) if before[address] != memory[address]]
    changed_start = min(changed) if changed else None
    changed_end = max(changed) if changed else None

    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_path = args.output_dir / "neuromancer_dox_unpacked_memory.bin"
    report_path = args.output_dir / "neuromancer_dox_decode.json"
    memory_path.write_bytes(memory)
    report = {
        "source_prg": str(args.prg),
        "source_sha256": sha256(args.prg.read_bytes()),
        "method": "execute relocated 6502 depacker with documented opcodes plus verified DCP zp",
        "entry": f"0x{ENTRY:04X}",
        "first_handoff": f"0x{FIRST_HANDOFF:04X}",
        "final_handoff": f"0x{FINAL_HANDOFF:04X}",
        "first_stage_instructions": first_stage_steps,
        "instructions_executed": final_steps,
        "changed_address_start": f"0x{changed_start:04X}" if changed_start is not None else None,
        "changed_address_end": f"0x{changed_end:04X}" if changed_end is not None else None,
        "output_memory_sha256": sha256(memory),
        "registers_at_handoff": {
            "A": f"0x{cpu.a:02X}", "X": f"0x{cpu.x:02X}", "Y": f"0x{cpu.y:02X}",
            "SP": f"0x{cpu.sp:02X}", "P": f"0x{cpu.p:02X}",
        },
        "relocation": relocation_map,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"executed {final_steps} instructions "
        f"({first_stage_steps} to first handoff); reached ${FINAL_HANDOFF:04X}"
    )
    print(f"changed ${changed_start:04X}-${changed_end:04X}")
    print(f"wrote {memory_path}")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
