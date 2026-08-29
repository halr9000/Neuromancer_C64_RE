#!/usr/bin/env python3
"""Extract the two real E1 PRG chains with complete sector provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .d64 import D64Image
except ImportError:  # Direct `python3 tools/extract_e1.py` invocation.
    from d64 import D64Image


FILES = {
    "NEUROMANCER": "neuromancer_e1.prg",
    "A": "e1_file_a.prg",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    image = D64Image.read(args.image)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "source_image": str(args.image),
        "source_sha256": sha256(image.data),
        "files": [],
    }

    for disk_name, output_name in FILES.items():
        entry = image.find_entry(disk_name)
        chain = image.follow_chain(entry.start)
        if len(chain.payload) < 2:
            raise ValueError(f"truncated PRG chain: {disk_name}")
        load_address = chain.payload[0] | chain.payload[1] << 8
        loaded_bytes = len(chain.payload) - 2
        end_exclusive = load_address + loaded_bytes
        output = args.output_dir / output_name
        output.write_bytes(chain.payload)
        record = {
            "disk_name": disk_name,
            "output": output_name,
            "sha256": sha256(chain.payload),
            "bytes": len(chain.payload),
            "load_address": f"0x{load_address:04X}",
            "loaded_end_exclusive": f"0x{end_exclusive:04X}",
            "directory_start": str(entry.start),
            "sector_count": len(chain.sectors),
            "sector_chain": [str(ref) for ref in chain.sectors],
        }
        manifest["files"].append(record)
        print(
            f"{disk_name}: {len(chain.payload)} bytes, {len(chain.sectors)} sectors, "
            f"load ${load_address:04X}-${end_exclusive - 1:04X}, SHA-256 {record['sha256']}"
        )

    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
