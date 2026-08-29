#!/usr/bin/env python3
"""Reconstruct and disassemble the E1 autostart/fastloader bootstrap layers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .dis import Image, disassemble
    from .instruction_set import OPCODES
except ImportError:  # Direct `python3 tools/analyze_e1_boot.py` invocation.
    from dis import Image, disassemble
    from instruction_set import OPCODES


PRG_LOAD = 0x02A7
ISTOP_VECTOR = 0x0328
REDIRECT_SOURCE = 0x032A
REDIRECT_DESTINATION = 0xC000
REDIRECT_END_EXCLUSIVE = 0xC240
STAGE1_SOURCE_END_EXCLUSIVE = REDIRECT_SOURCE + (
    REDIRECT_END_EXCLUSIVE - REDIRECT_DESTINATION
)
STAGE1_ENTRY = 0xC100
DRIVE_DESTINATION = 0x0700
DRIVE_ENTRY = 0x079F
CLIENT_SOURCE = 0xC173
CLIENT_DESTINATION = 0x0100
CLIENT_CODE_END_EXCLUSIVE = 0xC229


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def address_slice(data: bytes, base: int, start: int, end: int) -> bytes:
    first = start - base
    last = end - base
    if first < 0 or last > len(data) or first > last:
        raise ValueError(f"address range ${start:04X}-${end - 1:04X} is outside PRG")
    return data[first:last]


def instruction_count(image: Image, start: int, end: int) -> int:
    count = 0
    address = start
    while address < end:
        offset = address - image.base
        if not 0 <= offset < len(image.data):
            raise ValueError(f"listing address ${address:04X} is outside image")
        address += OPCODES[image.data[offset]].size
        count += 1
    if address != end:
        raise ValueError(f"listing range ${start:04X}-${end - 1:04X} ends mid-instruction")
    return count


def listing_section(
    title: str,
    image: Image,
    start: int,
    end: int,
    labels: dict[int, tuple[str, str]],
) -> str:
    lines = disassemble(image, start, instruction_count(image, start, end), labels)
    return f"===== {title} [${start:04X}-${end - 1:04X}] =====\n" + "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    prg = args.prg.read_bytes()
    if len(prg) < 2:
        raise ValueError("truncated E1 PRG")
    load = prg[0] | prg[1] << 8
    if load != PRG_LOAD:
        raise ValueError(f"expected E1 load address ${PRG_LOAD:04X}, got ${load:04X}")
    payload = prg[2:]

    if address_slice(payload, load, ISTOP_VECTOR, ISTOP_VECTOR + 2) != b"\xA7\x02":
        raise ValueError("E1 does not install $02A7 in the KERNAL ISTOP vector")
    expected_hook = bytes.fromhex(
        "A9 0B 8D 11 D0 8D 20 D0 A2 BD 8E 28 03 A2 00 A0 C0 "
        "86 AE 84 AF 60"
    )
    if address_slice(payload, load, PRG_LOAD, PRG_LOAD + len(expected_hook)) != expected_hook:
        raise ValueError("unexpected E1 first-stage autostart hook")

    stage = address_slice(payload, load, REDIRECT_SOURCE, STAGE1_SOURCE_END_EXCLUSIVE)
    if len(stage) != REDIRECT_END_EXCLUSIVE - REDIRECT_DESTINATION:
        raise AssertionError("incorrect reconstructed stage size")
    if stage[STAGE1_ENTRY - REDIRECT_DESTINATION :][:3] != bytes.fromhex("20 E7 FF"):
        raise ValueError("redirected $C100 stage entry did not align to KERNAL CLALL call")

    drive = stage[:0x100]
    if drive[DRIVE_ENTRY - DRIVE_DESTINATION :][:2] != bytes.fromhex("A9 10"):
        raise ValueError("drive fastloader entry did not align at $079F")
    client = stage[CLIENT_SOURCE - REDIRECT_DESTINATION : CLIENT_CODE_END_EXCLUSIVE - REDIRECT_DESTINATION]
    if client[:5] != bytes.fromhex("A0 FC 84 22 20") or client[-1] != 0x60:
        raise ValueError("computer fastloader code did not align at $0100")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stage_path = args.output_dir / "e1_bootstrap_runtime_c000.bin"
    drive_path = args.output_dir / "e1_drive_fastloader_0700.bin"
    client_path = args.output_dir / "e1_client_fastloader_0100.bin"
    listing_path = args.output_dir / "e1_boot_listing.txt"
    map_path = args.output_dir / "e1_boot_map.json"
    stage_path.write_bytes(stage)
    drive_path.write_bytes(drive)
    client_path.write_bytes(client)

    autostart_labels = {
        0x02A7: ("e1_istop_first_hit", "Redirect KERNAL load pointer to $C000"),
        0x02BD: ("e1_istop_wait_for_c240", "Transfer to relocated bootstrap at $C100"),
    }
    stage_labels = {
        0xC100: ("e1_stage1_entry", "Upload and execute the 1541 fastloader"),
        0xC15F: ("e1_send_memory_command_prefix", "Send DOS command-channel prefix M-"),
        0xC173: ("e1_client_loader_source", "Copied to C64 $0100"),
        0xC1FA: ("e1_serial_get_byte_source", "Relocates to C64 $0187"),
    }
    drive_labels = {
        0x0700: ("e1_drive_fastloader_base", "Uploaded to 1541 RAM with M-W"),
        0x0749: ("e1_drive_send_byte", "Bit-bang one byte to the C64"),
        0x079F: ("e1_drive_fastloader_entry", "Started with DOS M-E"),
    }
    client_labels = {
        0x0100: ("e1_client_fastloader_entry", "Receive destination records from drive"),
        0x0187: ("e1_client_serial_get_byte", "Read one byte from CIA2 serial lines"),
    }
    source_image = Image(payload, load)
    stage_image = Image(stage, REDIRECT_DESTINATION)
    drive_image = Image(drive, DRIVE_DESTINATION)
    client_image = Image(client, CLIENT_DESTINATION)
    sections = [
        listing_section("E1 AUTOSTART HOOK", source_image, 0x02A7, 0x02D1, autostart_labels),
        listing_section("C64 STAGE 1", stage_image, 0xC100, 0xC173, stage_labels),
        listing_section("1541 UPLOAD", drive_image, 0x0700, 0x0800, drive_labels),
        listing_section("C64 CLIENT FASTLOADER", client_image, 0x0100, 0x01B6, client_labels),
    ]
    listing_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")

    report = {
        "source_prg": str(args.prg),
        "source_sha256": sha256(prg),
        "autostart": {
            "load_address": "0x02A7",
            "istop_vector": "0x0328-0x0329",
            "first_vector_value": "0x02A7",
            "steady_vector_value": "0x02BD",
            "load_pointer": "0x00AE-0x00AF",
            "redirected_to": "0xC000",
            "trigger_value": "0xC240",
            "transfer": "JSR $FD15; JMP $C100",
        },
        "redirected_stage": {
            "file_source": "0x032A-0x0569",
            "runtime_destination": "0xC000-0xC23F",
            "bytes": len(stage),
            "sha256": sha256(stage),
            "entry": "0xC100",
            "entry_file_source": "0x042A",
        },
        "drive_fastloader": {
            "runtime_source": "0xC000-0xC0FF",
            "drive_destination": "0x0700-0x07FF",
            "bytes": len(drive),
            "sha256": sha256(drive),
            "upload_command": "M-W in eight 32-byte blocks",
            "execute_command": "M-E $079F",
            "entry": "0x079F",
        },
        "client_fastloader": {
            "runtime_source_code": "0xC173-0xC228",
            "c64_destination_code": "0x0100-0x01B5",
            "bytes": len(client),
            "sha256": sha256(client),
            "copy_loop": "0xC173-0xC272 -> 0x0100-0x01FF; bytes after code are padding",
            "entry": "0x0100",
            "serial_get_byte": "0x0187",
        },
    }
    map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"reconstructed ${REDIRECT_DESTINATION:04X}-${REDIRECT_END_EXCLUSIVE - 1:04X}")
    print(f"wrote {stage_path}")
    print(f"wrote {drive_path}")
    print(f"wrote {client_path}")
    print(f"wrote {listing_path}")
    print(f"wrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
