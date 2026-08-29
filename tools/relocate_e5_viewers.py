#!/usr/bin/env python3
"""Reproduce the E5 viewers' relocation stages into 64 KiB memory images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MEMORY_SIZE = 0x10000


def load_prg(path: Path) -> tuple[bytearray, int, int]:
    prg = path.read_bytes()
    if len(prg) < 2:
        raise ValueError(f"truncated PRG: {path}")
    load = prg[0] | prg[1] << 8
    payload = prg[2:]
    end = load + len(payload)
    if end > MEMORY_SIZE:
        raise ValueError(f"PRG does not fit in 64 KiB: {path}")
    memory = bytearray(MEMORY_SIZE)
    memory[load:end] = payload
    return memory, load, end


def relocate_dox(path: Path) -> tuple[bytes, dict[str, object]]:
    memory, load, end = load_prg(path)

    # Stage 1 at $03B7 copies 248 pages using overlapping absolute,X windows:
    # source $088F..(wrap)..$008E -> destination $080B..(wrap)..$000A.
    source = 0x088F
    destination = 0x080B
    for page in range(0x100 - 0x08):
        for x in range(0x100):
            src = (source + (page << 8) + x) & 0xFFFF
            dst = (destination + (page << 8) + x) & 0xFFFF
            memory[dst] = memory[src]

    # Stage 2 starts at relocated $080B. The reverse-X loop copies all 256
    # bytes of the low-memory depacker plus X=$00..$AA of the $0333 block.
    low_source = bytes(memory[0x0831:0x0931])
    memory[0x00FA:0x01FA] = low_source
    high_source = bytes(memory[0x0922:0x09CD])
    memory[0x0333:0x03DE] = high_source

    return bytes(memory), {
        "source": str(path),
        "load_address": f"0x{load:04X}",
        "loaded_end_exclusive": f"0x{end:04X}",
        "stage1_source": "0x088F with 248 overlapping absolute-X pages",
        "stage1_destination": "0x080B with 248 overlapping absolute-X pages",
        "stage2_ranges": [
            {"source": "0x0831-0x0930", "destination": "0x00FA-0x01F9"},
            {"source": "0x0922-0x09CC", "destination": "0x0333-0x03DD"},
        ],
        "depacker_entry": "0x03AD",
    }


def relocate_solution(path: Path) -> tuple[bytes, dict[str, object]]:
    memory, load, end = load_prg(path)

    # Entry code copies $0769-$0A68 to $CD00-$CFFF and jumps to $CDC2.
    memory[0xCD00:0xD000] = bytes(memory[0x0769:0x0A69])

    # The relocated code then walks the compressed source backwards from the
    # loader-provided end pointer to $0A5B, placing it below $C700. Since source
    # and destination both decrement, byte order is retained.
    compressed = bytes(memory[0x0A5B:end])
    compressed_destination = 0xC700 - len(compressed)
    memory[compressed_destination:0xC700] = compressed

    return bytes(memory), {
        "source": str(path),
        "load_address": f"0x{load:04X}",
        "loaded_end_exclusive": f"0x{end:04X}",
        "code_relocation": {"source": "0x0769-0x0A68", "destination": "0xCD00-0xCFFF"},
        "compressed_source": f"0x0A5B-0x{end - 1:04X}",
        "compressed_destination": f"0x{compressed_destination:04X}-0xC6FF",
        "compressed_bytes": len(compressed),
        "depacker_entry": "0xCDC2",
        "get_symbol_entry": "0xCE50",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dox_prg", type=Path)
    parser.add_argument("solution_prg", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dox_memory, dox_map = relocate_dox(args.dox_prg)
    sol_memory, sol_map = relocate_solution(args.solution_prg)
    outputs = {
        "neuromancer_dox_relocated_memory.bin": dox_memory,
        "neuromancer_solution_relocated_memory.bin": sol_memory,
    }
    for name, data in outputs.items():
        path = args.output_dir / name
        path.write_bytes(data)
        print(f"wrote {path} ({len(data)} bytes)")
    map_path = args.output_dir / "e5_relocation_map.json"
    map_path.write_text(json.dumps({"dox": dox_map, "solution": sol_map}, indent=2) + "\n")
    print(f"wrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

