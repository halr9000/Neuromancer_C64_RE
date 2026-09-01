#!/usr/bin/env python3
"""Build a readable public catalog from verified native VICE room captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


ACTIVE_DISPLAY = (32, 35, 352, 235)
ROOM_NAMES = {0: "Chatsubo", 6: "Cheap Hotel"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_catalog(
    sources: list[tuple[dict[str, Any], Image.Image]], output_dir: Path
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rooms: list[dict[str, object]] = []
    for report, screenshot in sources:
        room_id = int(report["room_id"])
        strings = report.get("strings", [])
        if not isinstance(strings, list) or len(strings) < 2:
            raise ValueError(f"room {room_id} requires at least two decoded strings")
        selection = report["selection"]["room"]
        modules = report.get("modules", [])
        room_module = modules[-1]
        crop = screenshot.crop(ACTIVE_DISPLAY)
        if crop.size != (320, 200):
            raise ValueError(f"room {room_id} VICE capture has no 320x200 active display")
        frame_name = f"room{room_id}.png"
        frame_path = output_dir / frame_name
        crop.save(frame_path, optimize=True)
        rooms.append(
            {
                "id": room_id,
                "name": ROOM_NAMES.get(room_id, f"Room {room_id}"),
                "location": strings[1]["text"],
                "description": strings[0]["text"],
                "frame": f"./generated/catalog/{frame_name}",
                "frameSha256": _sha256(frame_path),
                "terminalEnabled": bool(report.get("terminal", {}).get("pax_enabled")),
                "entityCount": len(report.get("entities", [])),
                "provenance": {
                    "side": selection["side"],
                    "start": f"T{selection['track']:02d}/S{selection['sector']:02d}",
                    "moduleSha256": room_module.get("sha256", ""),
                },
            }
        )
    return {"schemaVersion": 1, "rooms": rooms}


def _legacy_room0_report(room_map: dict[str, Any], text: dict[str, Any]) -> dict[str, Any]:
    selection = room_map["table_derivation"]["room_logic"]
    module = next(
        item for item in room_map["modules"] if item["name"] == "side2_room0_logic_ca00"
    )
    return {
        "room_id": 0,
        "selection": {
            "room": {
                "side": int(selection["selected_side"]),
                "track": selection["selected_track"],
                "sector": selection["selected_sector"],
            }
        },
        "modules": [module],
        "strings": text["strings"],
        "entities": [{}, {}],
        "terminal": {"pax_enabled": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("room0_map", type=Path)
    parser.add_argument("room0_text", type=Path)
    parser.add_argument("room0_screenshot", type=Path)
    parser.add_argument("room6_map", type=Path)
    parser.add_argument("room6_screenshot", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    room0 = _legacy_room0_report(
        json.loads(args.room0_map.read_text(encoding="utf-8")),
        json.loads(args.room0_text.read_text(encoding="utf-8")),
    )
    room6 = json.loads(args.room6_map.read_text(encoding="utf-8"))
    catalog = build_catalog(
        [
            (room0, Image.open(args.room0_screenshot).convert("RGB")),
            (room6, Image.open(args.room6_screenshot).convert("RGB")),
        ],
        args.output_dir,
    )
    catalog_path = args.output_dir.parent / "room-catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(catalog['rooms'])} verified room records to {catalog_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
