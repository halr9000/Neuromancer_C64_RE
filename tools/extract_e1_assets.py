#!/usr/bin/env python3
"""Extract the two startup VIC-II sprites loaded at $0380-$03FE."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


SPRITE_BYTES = 63
SPRITE_WIDTH = 24
SPRITE_HEIGHT = 21
SPRITE_POINTERS = (0x0E, 0x0F)
SPRITE_ADDRESSES = (0x0380, 0x03C0)


def decode_hires_sprite(data: bytes) -> list[list[int]]:
    """Decode one 63-byte, MSB-first VIC-II high-resolution sprite."""
    if len(data) != SPRITE_BYTES:
        raise ValueError("a VIC-II high-resolution sprite must be exactly 63 bytes")
    rows: list[list[int]] = []
    for row in range(SPRITE_HEIGHT):
        row_bytes = data[row * 3 : row * 3 + 3]
        rows.append(
            [
                (row_bytes[column // 8] >> (7 - column % 8)) & 1
                for column in range(SPRITE_WIDTH)
            ]
        )
    return rows


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_mask_png(path: Path, pixels: list[list[int]], scale: int) -> None:
    """Write a nearest-neighbor RGBA sprite mask without external packages."""
    if scale < 1:
        raise ValueError("PNG scale must be at least 1")
    source_height = len(pixels)
    source_width = len(pixels[0]) if pixels else 0
    width = source_width * scale
    height = source_height * scale
    scanlines = bytearray()
    for source_row in pixels:
        rgba_row = bytearray()
        for value in source_row:
            color = (255, 255, 255, 255) if value else (0, 0, 0, 0)
            rgba_row.extend(bytes(color) * scale)
        for _ in range(scale):
            scanlines.append(0)
            scanlines.extend(rgba_row)
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(_png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    png.extend(_png_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9)))
    png.extend(_png_chunk(b"IEND", b""))
    path.write_bytes(png)


def _compose_sheet(sprites: list[list[list[int]]], gap: int = 4) -> list[list[int]]:
    rows: list[list[int]] = []
    for row_index in range(SPRITE_HEIGHT):
        row: list[int] = []
        for sprite_index, sprite in enumerate(sprites):
            if sprite_index:
                row.extend([0] * gap)
            row.extend(sprite[row_index])
        rows.append(row)
    return rows


def _compose_grid(
    sprites: list[list[list[int]]], columns: int, gap: int = 4
) -> list[list[int]]:
    if columns < 1:
        raise ValueError("sprite sheet columns must be at least 1")
    row_count = (len(sprites) + columns - 1) // columns
    width = columns * SPRITE_WIDTH + (columns - 1) * gap
    grid = [[0] * width for _ in range(row_count * SPRITE_HEIGHT + (row_count - 1) * gap)]
    for index, sprite in enumerate(sprites):
        grid_row, grid_column = divmod(index, columns)
        top = grid_row * (SPRITE_HEIGHT + gap)
        left = grid_column * (SPRITE_WIDTH + gap)
        for row_index, row in enumerate(sprite):
            grid[top + row_index][left : left + SPRITE_WIDTH] = row
    return grid


def extract_startup_sprites(source: Path, output_dir: Path, scale: int = 8) -> dict[str, object]:
    module = source.read_bytes()
    expected_size = SPRITE_BYTES * 2 + 1
    if len(module) != expected_size:
        raise ValueError(f"startup sprite module must be exactly {expected_size} bytes")
    output_dir.mkdir(parents=True, exist_ok=True)

    decoded = [
        decode_hires_sprite(module[index * SPRITE_BYTES : (index + 1) * SPRITE_BYTES])
        for index in range(2)
    ]
    sprites: list[dict[str, object]] = []
    for index, (pointer, address, pixels) in enumerate(
        zip(SPRITE_POINTERS, SPRITE_ADDRESSES, decoded, strict=True)
    ):
        filename = f"startup_sprite_{pointer:02x}.png"
        write_mask_png(output_dir / filename, pixels, scale)
        sprites.append(
            {
                "index": index,
                "pointer": f"0x{pointer:02X}",
                "address": f"0x{address:04X}",
                "source_offset": f"0x{index * SPRITE_BYTES:02X}",
                "foreground_pixel_count": sum(sum(row) for row in pixels),
                "png": filename,
            }
        )

    sheet_name = "startup_sprites_0e_0f.png"
    write_mask_png(output_dir / sheet_name, _compose_sheet(decoded), scale)
    return {
        "source": str(source),
        "source_sha256": hashlib.sha256(module).hexdigest(),
        "format": "VIC-II high-resolution sprite, 24x21, MSB first",
        "module_layout": "two 63-byte sprites followed by one padding byte",
        "runtime_evidence": "$051B-$0521 stores pointers $0E/$0F at $07F8/$07F9",
        "rendering": "white RGBA mask on transparent background; nearest-neighbor scaling",
        "sheet": sheet_name,
        "sprites": sprites,
    }


def extract_sprite_bank(
    source: Path, output_dir: Path, scale: int = 4, columns: int = 8
) -> dict[str, object]:
    """Decode a module made of 64-byte VIC-II sprite slots."""
    bank = source.read_bytes()
    if not bank or len(bank) % 64:
        raise ValueError("sprite bank length must be a non-zero multiple of 64 bytes")
    output_dir.mkdir(parents=True, exist_ok=True)
    decoded = [
        decode_hires_sprite(bank[offset : offset + SPRITE_BYTES])
        for offset in range(0, len(bank), 64)
    ]
    sprites: list[dict[str, object]] = []
    for index, pixels in enumerate(decoded):
        filename = f"{source.stem}_sprite_{index:02d}.png"
        write_mask_png(output_dir / filename, pixels, scale)
        sprites.append(
            {
                "index": index,
                "source_offset": f"0x{index * 64:02X}",
                "foreground_pixel_count": sum(sum(row) for row in pixels),
                "png": filename,
            }
        )
    sheet_name = f"{source.stem}_sprite_bank.png"
    write_mask_png(output_dir / sheet_name, _compose_grid(decoded, columns), scale)
    return {
        "source": str(source),
        "source_sha256": hashlib.sha256(bank).hexdigest(),
        "slot_count": len(decoded),
        "slot_layout": "63 bytes of MSB-first high-resolution pixels plus one padding byte",
        "interpretation": "candidate sprite bank; visual and runtime-reference checks required",
        "sheet": sheet_name,
        "sprites": sprites,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--scale", type=int, default=8)
    parser.add_argument("--sprite-bank", type=Path)
    args = parser.parse_args()

    report = extract_startup_sprites(args.source, args.output_dir, args.scale)
    report_path = args.output_dir / "startup_sprites_0e_0f.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(report['sprites'])} sprites and {report['sheet']}")
    print(f"wrote {report_path}")
    if args.sprite_bank is not None:
        bank_report = extract_sprite_bank(args.sprite_bank, args.output_dir, args.scale)
        bank_report_path = args.output_dir / f"{args.sprite_bank.stem}_sprite_bank.json"
        bank_report_path.write_text(json.dumps(bank_report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {bank_report['slot_count']} candidate sprite slots and {bank_report['sheet']}")
        print(f"wrote {bank_report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
