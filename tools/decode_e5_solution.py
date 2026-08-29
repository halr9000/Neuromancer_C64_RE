#!/usr/bin/env python3
"""Reproduce the E5 solution viewer's entropy decoder plus $F3 RLE layer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .basic_v2 import parse_program, render_listing
    from .relocate_e5_viewers import relocate_solution
except ImportError:  # Direct `python3 tools/decode_e5_solution.py` invocation.
    from basic_v2 import parse_program, render_listing
    from relocate_e5_viewers import relocate_solution


SOURCE_START = 0x0A5B
OUTPUT_START = 0x0801
OUTPUT_END_EXCLUSIVE = 0x8DEE
MARKER = 0xF3


class SymbolDecoder:
    """Instruction-for-instruction translation of the routine at $CE50."""

    def __init__(self, memory: bytearray, stream_pointer_before_first: int) -> None:
        self.memory = memory
        self.memory[0xFB] = stream_pointer_before_first & 0xFF
        self.memory[0xFC] = stream_pointer_before_first >> 8
        self.memory[0xFF] = 0
        self.symbol_count = 0
        self.refill_count = 0

    def _stream_pointer(self) -> int:
        return self.memory[0xFB] | self.memory[0xFC] << 8

    @staticmethod
    def _sbc(left: int, right: int, carry: int) -> tuple[int, int]:
        result = left - right - (1 - carry)
        return result & 0xFF, 1 if result >= 0 else 0

    def get(self) -> int:
        memory = self.memory
        x = 0xFF
        memory[0xF7] = x
        memory[0xF8] = x
        x = (x + 1) & 0xFF
        memory[0xFE] = 0x01
        memory[0xFD] = 0x7F

        steps = 0
        while True:
            steps += 1
            if steps > 100_000:
                raise ValueError("$CE50 symbol decoder exceeded its step guard")

            memory[0xFF] = (memory[0xFF] - 1) & 0xFF
            if memory[0xFF] & 0x80:
                pointer = (self._stream_pointer() + 1) & 0xFFFF
                memory[0xFB] = pointer & 0xFF
                memory[0xFC] = pointer >> 8
                memory[0xFF] = 0x07
                memory[0xF9] = memory[pointer]
                self.refill_count += 1

            carry = (memory[0xF9] >> 7) & 1
            memory[0xF9] = (memory[0xF9] << 1) & 0xFF
            if carry == 0:
                y = memory[0xFE]
                address = 0x00F7 + y
                memory[address] = memory[0xFD] & memory[address]

            y = (x << 1) & 0xFF
            _, carry = self._sbc(memory[0xF7], memory[0xCEE2 + y], 1)
            _, carry = self._sbc(memory[0xF8], memory[0xCEE3 + y], carry)
            if carry == 0 or x == 0x0F:
                break

            x = (x + 1) & 0xFF
            old = memory[0xFD]
            memory[0xFD] = 0x80 | (old >> 1)
            carry = old & 1
            if carry:
                continue
            memory[0xFE] = (memory[0xFE] - 1) & 0xFF
            if memory[0xFE] == 0:
                memory[0xFD] = 0x7F

        if x != 0:
            memory[0xF7], carry = self._sbc(memory[0xF7], memory[0xCEE0 + y], 1)
            memory[0xF8], _ = self._sbc(memory[0xF8], memory[0xCEE1 + y], carry)

        y = memory[0xFE]
        if y != 0:
            memory[0xF7] = memory[0xF8]
            y = (y - 1) & 0xFF
            memory[0xF8] = y

        accumulator = memory[0xFD]
        while True:
            carry = accumulator & 1
            accumulator >>= 1
            if carry == 0:
                break
            carry = memory[0xF8] & 1
            memory[0xF8] >>= 1
            old_f7 = memory[0xF7]
            memory[0xF7] = ((carry << 7) | (old_f7 >> 1)) & 0xFF

        y = (memory[0xCED2 + x] + memory[0xF7]) & 0xFF
        value = memory[0xCF00 + y]
        self.symbol_count += 1
        return value


def decode_rle(get_symbol, expected_size: int) -> tuple[bytes, dict[str, int]]:
    output = bytearray()
    literals = 0
    runs = 0
    escaped_markers = 0

    while len(output) < expected_size:
        value = get_symbol()
        if value != MARKER:
            output.append(value)
            literals += 1
            continue
        count = get_symbol()
        if count < 4:
            value = MARKER
            escaped_markers += 1
        else:
            value = get_symbol()
        if len(output) + count > expected_size:
            raise ValueError("run exceeds the traced output end address")
        output.extend([value] * count)
        runs += 1

    stats = {
        "literal_records": literals,
        "run_records": runs,
        "escaped_marker_records": escaped_markers,
    }
    return bytes(output), stats


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    prg = args.prg.read_bytes()
    if len(prg) < 2:
        raise ValueError("truncated PRG")
    load_address = prg[0] | prg[1] << 8
    if load_address != OUTPUT_START:
        raise ValueError(f"expected load address $0801, got ${load_address:04X}")
    payload = prg[2:]
    source_offset = SOURCE_START - load_address
    if source_offset < 0 or source_offset >= len(payload):
        raise ValueError("traced stream start is outside the PRG")
    relocated, relocation_map = relocate_solution(args.prg)
    memory = bytearray(relocated)
    stream_bytes = len(payload) - source_offset
    stream_start = 0xC700 - stream_bytes
    decoder = SymbolDecoder(memory, stream_start - 1)
    expected_size = OUTPUT_END_EXCLUSIVE - OUTPUT_START
    unpacked, stats = decode_rle(decoder.get, expected_size)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    unpacked_prg = args.output_dir / "neuromancer_solution_unpacked.prg"
    listing_path = args.output_dir / "neuromancer_solution_listing.txt"
    map_path = args.output_dir / "neuromancer_solution_decode.json"
    unpacked_prg.write_bytes(bytes((OUTPUT_START & 0xFF, OUTPUT_START >> 8)) + unpacked)
    basic_error = None
    try:
        lines = parse_program(unpacked, OUTPUT_START)
        listing_path.write_text(render_listing(lines, provenance=True), encoding="utf-8")
    except ValueError as error:
        lines = []
        basic_error = str(error)

    report = {
        "source_prg": str(args.prg),
        "source_sha256": sha256(prg),
        "algorithm": "$CE50 entropy decoder followed by $F3 RLE, translated from the relocated 6510 depacker",
        "compressed_source_address": f"0x{SOURCE_START:04X}",
        "compressed_source_file_offset": source_offset + 2,
        "compressed_bytes_available": stream_bytes,
        "relocated_stream_start": f"0x{stream_start:04X}",
        "relocated_stream_last_read": f"0x{decoder._stream_pointer():04X}",
        "entropy_symbols_decoded": decoder.symbol_count,
        "entropy_input_bytes_read": decoder.refill_count,
        "output_start": f"0x{OUTPUT_START:04X}",
        "output_end_exclusive": f"0x{OUTPUT_END_EXCLUSIVE:04X}",
        "output_bytes": len(unpacked),
        "output_sha256": sha256(unpacked),
        "basic_lines": len(lines),
        "basic_parse_error": basic_error,
        "relocation": relocation_map,
        **stats,
    }
    map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"decoded {decoder.refill_count} compressed bytes to {len(unpacked)} bytes; "
        f"listed {len(lines)} BASIC lines"
    )
    print(f"wrote {unpacked_prg}")
    if lines:
        print(f"wrote {listing_path}")
    else:
        print(f"BASIC listing deferred: {basic_error}")
    print(f"wrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
