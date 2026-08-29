#!/usr/bin/env python3
"""Reconstruct the destination record sent by the E1 bootstrap fastloader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image
except ImportError:  # Direct `python3 tools/decode_e1_fastload.py` invocation.
    from d64 import D64Image


BOOTSTRAP_SECTOR_COUNT = 3
EXPECTED_DESTINATION = 0x0801
EXPECTED_FIRST_FAST_SECTOR = "T13/S12"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_record(image: D64Image, filename: str) -> tuple[bytes, dict[str, object]]:
    entry = image.find_entry(filename)
    chain = image.follow_chain(entry.start)
    if len(chain.sectors) <= BOOTSTRAP_SECTOR_COUNT:
        raise ValueError("E1 chain ends before the fastloaded record")

    refs = chain.sectors[BOOTSTRAP_SECTOR_COUNT:]
    if str(refs[0]) != EXPECTED_FIRST_FAST_SECTOR:
        raise ValueError(f"unexpected first fastload sector: {refs[0]}")

    first = image.sector(refs[0])
    destination = first[2] | first[3] << 8
    if destination != EXPECTED_DESTINATION:
        raise ValueError(
            f"expected first fastload destination ${EXPECTED_DESTINATION:04X}, "
            f"got ${destination:04X}"
        )

    output = bytearray()
    for index, ref in enumerate(refs):
        sector = image.sector(ref)
        next_track, next_sector = sector[0], sector[1]
        if next_track:
            if index + 1 >= len(refs):
                raise ValueError(f"linked sector after recorded chain end: {ref}")
            expected = refs[index + 1]
            if (next_track, next_sector) != (expected.track, expected.sector):
                raise ValueError(
                    f"chain mismatch at {ref}: disk points to "
                    f"T{next_track:02d}/S{next_sector:02d}, expected {expected}"
                )
            data_end = 256
        else:
            if index != len(refs) - 1:
                raise ValueError(f"premature terminal sector: {ref}")
            used_data_bytes = next_sector - 1
            if not 0 <= used_data_bytes <= 254:
                raise ValueError(f"invalid terminal byte count at {ref}: {next_sector}")
            data_end = 2 + used_data_bytes

        data_start = 4 if index == 0 else 2
        if data_end < data_start:
            raise ValueError(f"record header exceeds terminal data at {ref}")
        output.extend(sector[data_start:data_end])

    raw_fastload_offset = BOOTSTRAP_SECTOR_COUNT * 254
    expected = chain.payload[raw_fastload_offset + 2 :]
    if bytes(output) != expected:
        raise ValueError("physical-sector reconstruction differs from directory payload")

    end_exclusive = destination + len(output)
    if end_exclusive > 0x10000:
        raise ValueError("fastloaded record wraps C64 address space")

    report: dict[str, object] = {
        "directory_name": filename,
        "directory_start": str(entry.start),
        "directory_sector_count": len(chain.sectors),
        "bootstrap_sectors": [str(ref) for ref in chain.sectors[:BOOTSTRAP_SECTOR_COUNT]],
        "fastload_sectors": [str(ref) for ref in refs],
        "fastload_sector_count": len(refs),
        "first_fastload_sector": str(refs[0]),
        "last_fastload_sector": str(refs[-1]),
        "directory_payload_offset_of_destination": f"0x{raw_fastload_offset:04X}",
        "directory_payload_offset_of_loaded_data": f"0x{raw_fastload_offset + 2:04X}",
        "destination": f"0x{destination:04X}",
        "end_exclusive": f"0x{end_exclusive:04X}",
        "loaded_bytes": len(output),
        "sha256": sha256(output),
    }
    return bytes(output), report


def parse_basic_sys(data: bytes, base: int) -> dict[str, object]:
    if len(data) < 10:
        raise ValueError("fastloaded data is too short for the BASIC launcher")
    next_line = data[0] | data[1] << 8
    line_number = data[2] | data[3] << 8
    if data[4] != 0x9E:
        raise ValueError("expected BASIC SYS token at fastload destination")
    terminator = data.find(b"\x00", 5)
    if terminator < 0:
        raise ValueError("unterminated BASIC launcher line")
    digits = data[5:terminator]
    if not digits.isdigit():
        raise ValueError("BASIC SYS argument is not decimal ASCII")
    sys_target = int(digits.decode("ascii"))
    return {
        "basic_start": f"0x{base:04X}",
        "next_line": f"0x{next_line:04X}",
        "line_number": line_number,
        "sys_target_decimal": sys_target,
        "sys_target": f"0x{sys_target:04X}",
        "line_bytes": data[: terminator + 1].hex(" ").upper(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    image = D64Image.read(args.image)
    data, report = decode_record(image, "NEUROMANCER")
    report["source_image"] = str(args.image)
    report["source_sha256"] = sha256(image.data)
    report["basic_launcher"] = parse_basic_sys(data, EXPECTED_DESTINATION)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.output_dir / "e1_fastload_0801_cf56.bin"
    map_path = args.output_dir / "e1_fastload_map.json"
    data_path.write_bytes(data)
    map_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"decoded {report['fastload_sector_count']} sectors to "
        f"${EXPECTED_DESTINATION:04X}-${int(str(report['end_exclusive']), 16) - 1:04X} "
        f"({len(data)} bytes)"
    )
    print(f"SHA-256 {report['sha256']}")
    print(f"wrote {data_path}")
    print(f"wrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
