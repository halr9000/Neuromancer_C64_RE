#!/usr/bin/env python3
"""Execute the reconstructed E1 room-0 vectors in the project 6510 core."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    from .emu.cpu6502 import Cpu6502, CpuError, FLAG_U
except ImportError:  # Direct `python3 tools/trace_e1_room0.py` invocation.
    from emu.cpu6502 import Cpu6502, CpuError, FLAG_U


MEMORY_SIZE = 0x10000
RETURN_SENTINEL = 0x02F0
ROOM_INIT_VECTOR = 0xF00A
ROOM_TICK_VECTOR = 0xF00D
ROOM_TEARDOWN_VECTOR = 0xF010
ENTITY_DISPATCHER = 0x6429
WATCHED_ZERO_PAGE = (0x03, 0x04, 0x07, 0x08, 0x0C, 0x10, 0x14, 0x18)
WATCHED_COUNTERS = (0xF17B, 0xF17C, 0xF17D, 0xF17E, 0xF17F, 0xF180)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def state(memory: bytearray) -> dict[str, int]:
    watched = (*WATCHED_ZERO_PAGE, *WATCHED_COUNTERS)
    return {f"0x{address:04X}": memory[address] for address in watched}


def call_subroutine(memory: bytearray, entry: int, max_steps: int = 20_000) -> dict[str, object]:
    """Run an RTS-returning function with a synthetic caller frame."""
    cpu = Cpu6502(memory)
    cpu.pc = entry
    cpu.sp = 0xFD
    cpu.p = FLAG_U
    return_address = (RETURN_SENTINEL - 1) & 0xFFFF
    memory[0x01FE] = return_address & 0xFF
    memory[0x01FF] = return_address >> 8
    pcs: list[int] = []
    while cpu.pc != RETURN_SENTINEL:
        if cpu.steps >= max_steps:
            raise CpuError(f"step limit reached from ${entry:04X}; PC=${cpu.pc:04X}")
        pcs.append(cpu.pc)
        cpu.step()
    return {
        "entry": f"0x{entry:04X}",
        "instructions": cpu.steps,
        "final_registers": {
            "A": f"0x{cpu.a:02X}",
            "X": f"0x{cpu.x:02X}",
            "Y": f"0x{cpu.y:02X}",
            "SP": f"0x{cpu.sp:02X}",
            "P": f"0x{cpu.p:02X}",
        },
        "executed_addresses": [f"0x{address:04X}" for address in sorted(set(pcs))],
        "top_address_counts": [
            {"address": f"0x{address:04X}", "count": count}
            for address, count in Counter(pcs).most_common(12)
        ],
    }


def trace_dispatcher_inactive(source: bytes) -> dict[str, object]:
    """Prove `$6429`'s four-slot control path without invoking unknown scripts."""
    memory = bytearray(source)
    original_slot_flags = list(memory[0x009D:0x00A1])
    memory[0x009D:0x00A1] = b"\xFF" * 4
    trace = call_subroutine(memory, ENTITY_DISPATCHER)
    return {
        "entry": "0x6429",
        "source_slot_flags": [f"0x{value:02X}" for value in original_slot_flags],
        "synthetic_slot_flags": ["0xFF"] * 4,
        "purpose": "exercise only the high-bit inactive branch; no entity script handler is run",
        "instructions": trace["instructions"],
        "executed_addresses": trace["executed_addresses"],
        "room_data_root_saved": {
            "low": f"0x{memory[0x6CBA]:02X}",
            "high": f"0x{memory[0x6CBB]:02X}",
        },
    }


def trace_room0(path: Path, ticks: int) -> dict[str, object]:
    source = path.read_bytes()
    if len(source) != MEMORY_SIZE:
        raise ValueError("room-0 snapshot must be exactly 64 KiB")
    memory = bytearray(source)
    expected_vectors = bytes.fromhex("4C F6 F0 4C 0E F1 4C 0D F1")
    if memory[ROOM_INIT_VECTOR : ROOM_TEARDOWN_VECTOR + 3] != expected_vectors:
        raise ValueError("room-0 vector block does not match the reconstructed ABI")

    before_init = state(memory)
    init = call_subroutine(memory, ROOM_INIT_VECTOR)
    after_init = state(memory)
    init["before"] = before_init
    init["after"] = after_init
    init["changed"] = {
        address: value for address, value in after_init.items() if before_init[address] != value
    }

    timeline: list[dict[str, object]] = []
    previous = state(memory)
    tick_step_total = 0
    for frame in range(1, ticks + 1):
        trace = call_subroutine(memory, ROOM_TICK_VECTOR)
        tick_step_total += int(trace["instructions"])
        current = state(memory)
        changed = {address: value for address, value in current.items() if previous[address] != value}
        if changed:
            timeline.append(
                {
                    "frame": frame,
                    "instructions": trace["instructions"],
                    "changed": changed,
                    "state": current,
                    "executed_addresses": trace["executed_addresses"],
                }
            )
        previous = current

    teardown = call_subroutine(memory, ROOM_TEARDOWN_VECTOR)
    return {
        "source": str(path),
        "source_sha256": sha256(source),
        "execution_engine": "project documented-opcode 6510 core; no VICE executable available in workspace",
        "room_vectors": {
            "0xF00A": "0xF0F6",
            "0xF00D": "0xF10E",
            "0xF010": "0xF10D",
        },
        "init": init,
        "tick_count": ticks,
        "tick_instruction_total": tick_step_total,
        "tick_state_changes": timeline,
        "teardown": teardown,
        "entity_dispatcher_inactive_path": trace_dispatcher_inactive(source),
        "output_memory_sha256": sha256(memory),
    }


def build_timeline(report: dict[str, object]) -> str:
    lines = [
        "# E1 room-0 vector execution trace",
        "",
        "The trace executes the reconstructed room snapshot with synthetic RTS caller frames.",
        "No VIC-II, CIA, keyboard, or VICE behavior is simulated in this checkpoint.",
        "",
        f"Source SHA-256: `{report['source_sha256']}`",
        f"Ticks executed: {report['tick_count']}",
        f"Tick instructions: {report['tick_instruction_total']}",
        "",
        "## Initialize vector `$F00A -> $F0F6`",
        "",
        f"Instructions: {report['init']['instructions']}",
        f"Changed state: `{report['init']['changed']}`",
        "",
        "## Tick vector `$F00D -> $F10E`",
        "",
    ]
    for event in report["tick_state_changes"]:
        lines.append(
            f"- Frame {event['frame']}: {event['instructions']} instructions; "
            f"changed `{event['changed']}`"
        )
    lines.extend(
        [
            "",
        "## Teardown vector `$F010 -> $F10D`",
            "",
            f"Instructions: {report['teardown']['instructions']}",
            "",
            "## Entity dispatcher `$6429` inactive-slot control path",
            "",
            "A clone of the source snapshot sets `$9D-$A0` to `$FF` so no",
            "entity script handler executes. This proves the dispatcher structure only; it",
            "does not assert runtime entity behavior from this synthetic setup.",
            "",
            f"Instructions: {report['entity_dispatcher_inactive_path']['instructions']}",
            "Room data root saved: "
            f"`{report['entity_dispatcher_inactive_path']['room_data_root_saved']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("room_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--ticks", type=int, default=64)
    args = parser.parse_args()
    if args.ticks < 1:
        raise ValueError("--ticks must be positive")

    report = trace_room0(args.room_memory, args.ticks)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "e1_room0_vector_trace.json"
    text_path = args.output_dir / "e1_room0_vector_trace.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    text_path.write_text(build_timeline(report), encoding="utf-8")
    print(f"executed {report['tick_count']} room ticks ({report['tick_instruction_total']} instructions)")
    print(f"wrote {json_path}")
    print(f"wrote {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
