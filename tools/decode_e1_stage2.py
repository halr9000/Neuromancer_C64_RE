#!/usr/bin/env python3
"""Execute the E1 Frontline packer through the unpacked-game handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .dis import Image, disassemble
    from .emu.cpu6502 import Cpu6502, FLAG_U
except ImportError:  # Direct `python3 tools/decode_e1_stage2.py` invocation.
    from dis import Image, disassemble
    from emu.cpu6502 import Cpu6502, FLAG_U


LOAD_ADDRESS = 0x0801
BOOTSTRAP_ENTRY = 0x080B
RELOCATED_COPY_ENTRY = 0x03AD
UNPACKED_ENTRY = 0x080D
MEMORY_SIZE = 0x10000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_fastload(path: Path) -> bytearray:
    data = path.read_bytes()
    end = LOAD_ADDRESS + len(data)
    if end > MEMORY_SIZE:
        raise ValueError("E1 fastload image does not fit in 64 KiB")
    memory = bytearray(MEMORY_SIZE)
    memory[LOAD_ADDRESS:end] = data
    return memory


def execute_stage2(data_path: Path) -> tuple[bytes, dict[str, object]]:
    memory = load_fastload(data_path)
    loaded = bytes(memory)
    cpu = Cpu6502(memory)
    cpu.pc = BOOTSTRAP_ENTRY
    cpu.x = 0
    cpu.sp = 0xFF
    cpu.p = FLAG_U

    bootstrap_steps = cpu.run_until(RELOCATED_COPY_ENTRY, max_steps=2_000_000)
    if memory[0x00FA] != 0xC7:
        raise ValueError("unexpected E1 relocation page count")
    if memory[0x0100:0x0103] != bytes.fromhex("20 77 03"):
        raise ValueError("low-memory depacker did not relocate to $0100")

    total_steps = cpu.run_until(UNPACKED_ENTRY, max_steps=30_000_000)
    unpack_steps = total_steps - bootstrap_steps

    changed = [address for address in range(MEMORY_SIZE) if loaded[address] != memory[address]]
    changed_start = min(changed) if changed else None
    changed_end = max(changed) if changed else None
    result = bytes(memory)
    report: dict[str, object] = {
        "source": str(data_path),
        "source_sha256": sha256(data_path.read_bytes()),
        "method": "execute the relocated 6502 depacker with the project CPU core",
        "loaded_range": "0x0801-0xCF56",
        "bootstrap_entry": f"0x{BOOTSTRAP_ENTRY:04X}",
        "relocated_copy_entry": f"0x{RELOCATED_COPY_ENTRY:04X}",
        "unpacked_entry": f"0x{UNPACKED_ENTRY:04X}",
        "bootstrap_instructions": bootstrap_steps,
        "unpack_instructions": unpack_steps,
        "instructions_executed": total_steps,
        "changed_address_start": f"0x{changed_start:04X}" if changed_start is not None else None,
        "changed_address_end": f"0x{changed_end:04X}" if changed_end is not None else None,
        "output_memory_sha256": sha256(result),
        "registers_at_handoff": {
            "A": f"0x{cpu.a:02X}",
            "X": f"0x{cpu.x:02X}",
            "Y": f"0x{cpu.y:02X}",
            "SP": f"0x{cpu.sp:02X}",
            "P": f"0x{cpu.p:02X}",
        },
        "relocation": {
            "low_source": "0x0831-0x0930",
            "low_destination": "0x00FA-0x01F9",
            "workspace_source": "0x0922-0x09CC",
            "workspace_destination": "0x0333-0x03DD",
            "packed_shift_source": "0x09B3 in 199 overlapping 256-byte pages",
            "packed_shift_destination": "0x07E8 in 199 overlapping 256-byte pages",
        },
    }
    return result, report


def build_listing(memory: bytes) -> str:
    labels = {
        0x0803: ("e1_basic_sys_2051", "BNE over the BASIC line text"),
        0x080B: ("e1_frontline_bootstrap", "Install and run low-memory depacker"),
        0x080D: ("e1_unpacked_entry", "First instruction after packer handoff"),
    }
    image = Image(memory, 0)
    lines = disassemble(image, UNPACKED_ENTRY, 160, labels)
    return (
        f"===== E1 UNPACKED ENTRY [${UNPACKED_ENTRY:04X}] =====\n"
        + "\n".join(lines)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fastload", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    memory, report = execute_stage2(args.fastload)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_path = args.output_dir / "e1_unpacked_memory.bin"
    report_path = args.output_dir / "e1_stage2_decode.json"
    listing_path = args.output_dir / "e1_unpacked_entry_listing.txt"
    memory_path.write_bytes(memory)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    listing_path.write_text(build_listing(memory), encoding="utf-8")

    print(
        f"executed {report['instructions_executed']} instructions; "
        f"reached ${UNPACKED_ENTRY:04X}"
    )
    print(f"memory SHA-256 {report['output_memory_sha256']}")
    print(f"wrote {memory_path}")
    print(f"wrote {report_path}")
    print(f"wrote {listing_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
