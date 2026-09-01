#!/usr/bin/env python3
"""Extract and execute the verified state-changing parts of the opening route."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image, SectorRef
    from .decode_e1_modules import ModuleSpec, decode_module, overlay
    from .emu.cpu6502 import Cpu6502
except ImportError:
    from d64 import D64Image, SectorRef
    from decode_e1_modules import ModuleSpec, decode_module, overlay
    from emu.cpu6502 import Cpu6502


PAX_ROOT = SectorRef(12, 3)
PAX_CHILDREN = (
    ("pax_messages", SectorRef(13, 11)),
    ("pax_bank", SectorRef(17, 14)),
    ("pax_directory", SectorRef(14, 5)),
    ("pax_send_message", SectorRef(34, 0)),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u24(memory: bytes | bytearray, address: int) -> int:
    return memory[address] | memory[address + 1] << 8 | memory[address + 2] << 16


def _put_u24(memory: bytearray, address: int, value: int) -> None:
    memory[address : address + 3] = value.to_bytes(3, "little")


def _run_slice(memory: bytearray, start: int, stop: int) -> int:
    cpu = Cpu6502(memory)
    cpu.pc = start
    return cpu.run_until(stop, 500)


def trace_opening(snapshot: bytes, side1: D64Image) -> tuple[dict[str, object], dict[str, bytes]]:
    root, root_report = decode_module(
        side1, ModuleSpec("pax_root", PAX_ROOT, 0x7400, "room PAX shell")
    )
    children: dict[str, bytes] = {}
    child_reports: list[dict[str, object]] = []
    for name, sector in PAX_CHILDREN:
        data, report = decode_module(
            side1, ModuleSpec(name, sector, 0x1000, "PAX child overlay")
        )
        children[name] = data
        child_reports.append(report)

    memory = bytearray(snapshot)
    initial = {"cash": _u24(memory, 0xC33A), "bank": _u24(memory, 0xC33D)}

    overlay(memory, 0x1000, children["pax_bank"])
    _put_u24(memory, 0x0057, 40)
    bank_steps = _run_slice(memory, 0x10E8, 0x1141)
    transferred = {"cash": _u24(memory, 0xC33A), "bank": _u24(memory, 0xC33D)}

    optional_memory = bytearray(memory)
    overlay(optional_memory, 0x1000, children["pax_send_message"])
    optional_memory[0x0048:0x004A] = (0x0200).to_bytes(2, "little")
    optional_memory[0x0200] = 0
    bonus_steps = _run_slice(optional_memory, 0x12EC, 0x1336)
    bonus = {
        "cash": _u24(optional_memory, 0xC33A),
        "bank": _u24(optional_memory, 0xC33D),
    }

    # GIVE debits cash before the room entity receives the amount in C112-C114.
    # Room 0's F0DA hook is the distinct conditional refund path.
    _put_u24(memory, 0x0057, 46)
    payment_steps = _run_slice(memory, 0x68A8, 0x68C5)
    paid = {"cash": _u24(memory, 0xC33A), "bank": _u24(memory, 0xC33D)}

    report: dict[str, object] = {
        "schema": 1,
        "sources": {
            "snapshot_sha256": _sha256(snapshot),
            "side1_sha256": _sha256(side1.data),
            "pax_root": root_report,
            "pax_children": child_reports,
        },
        "promoted_state": {
            "cash": {"address": "0xC33A", "width": 3},
            "bank": {"address": "0xC33D", "width": 3},
            "transfer_amount": {"address": "0x0057", "width": 3},
            "transfer_ring_index": {"address": "0xC348", "width": 1},
            "transfer_ring": {"address": "0xC34A", "records": 4, "record_bytes": 4},
            "room_id": {"address": "0xC330", "width": 1},
            "room_entity": {"address": "0xC400", "record_bytes": 8},
        },
        "routes": {
            "required": [
                {"event": "new_game", "cash": initial["cash"], "bank": initial["bank"]},
                {"event": "ratz_demands_payment", "room_string_id": 2, "amount": 46},
                {"event": "pax_activate", "module_entry": "0x7400"},
                {"event": "pax_transfer_to_cash", "amount": 40, **transferred},
                {"event": "pax_logoff", "module_exit": "0x74B5"},
                {"event": "pay_ratz", "amount": 46, **paid},
                {"event": "leave_chatsubo", "room_string_id": 28},
            ],
            "armitage_optional": [
                {"event": "send_bama_to_armitage", "bama_id": "056306118"},
                {"event": "armitage_deposit", "amount": 10000, **bonus},
            ],
        },
        "executed_code": {
            "bank_to_cash": {"start": "0x10E8", "stop": "0x1141", "steps": bank_steps},
            "armitage_deposit": {"start": "0x12EC", "stop": "0x1336", "steps": bonus_steps},
            "ratz_payment_debit": {"start": "0x68A8", "stop": "0x68C5", "steps": payment_steps},
            "ratz_conditional_refund": {"start": "0xF0DA", "stop": "0xF0F5"},
            "room0_teardown": {"address": "0xF10D", "bytes": snapshot[0xF10D:0xF10E].hex()},
        },
        "boundary": {
            "verified": "Chatsubo payment, leave dialogue, and no-op teardown",
            "open": "Exit enters the Chiba location selector; no destination room is automatic until the player chooses one.",
        },
    }
    return report, {"pax_root": root, **children}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("side1", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    report, modules = trace_opening(
        args.snapshot.read_bytes(), D64Image.read(args.side1)
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in modules.items():
        (args.output_dir / f"e1_{name}.bin").write_bytes(data)
    path = args.output_dir / "e1_opening_route_trace.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
