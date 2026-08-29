#!/usr/bin/env python3
"""Small, dependency-free reader for standard 35-track D64 images.

The game data sides deliberately do not use a DOS directory, but the boot and
documentation disks do. This module keeps physical track/sector locations in
every result so derived artifacts can be traced back to the source image.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator


SECTORS_PER_TRACK = (
    0,
    *([21] * 17),
    *([19] * 7),
    *([18] * 6),
    *([17] * 5),
)
STANDARD_D64_SIZE = 174_848


class D64Error(ValueError):
    """Raised when a D64 structure is invalid or unsupported."""


class SectorRef:
    __slots__ = ("track", "sector")

    def __init__(self, track: int, sector: int) -> None:
        self.track = track
        self.sector = sector

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SectorRef) and (self.track, self.sector) == (other.track, other.sector)

    def __hash__(self) -> int:
        return hash((self.track, self.sector))

    def __repr__(self) -> str:
        return f"SectorRef(track={self.track}, sector={self.sector})"

    def __str__(self) -> str:
        return f"T{self.track:02d}/S{self.sector:02d}"


class DirectoryEntry:
    __slots__ = (
        "filename", "file_type", "closed", "locked", "start", "blocks",
        "directory_sector", "slot",
    )

    def __init__(
        self,
        filename: str,
        file_type: str,
        closed: bool,
        locked: bool,
        start: SectorRef,
        blocks: int,
        directory_sector: SectorRef,
        slot: int,
    ) -> None:
        self.filename = filename
        self.file_type = file_type
        self.closed = closed
        self.locked = locked
        self.start = start
        self.blocks = blocks
        self.directory_sector = directory_sector
        self.slot = slot


class FileChain:
    __slots__ = ("payload", "sectors")

    def __init__(self, payload: bytes, sectors: tuple[SectorRef, ...]) -> None:
        self.payload = payload
        self.sectors = sectors


def decode_petscii_filename(data: bytes) -> str:
    """Decode the subset of PETSCII used by CBM DOS filenames."""
    chars: list[str] = []
    for value in data:
        if value == 0xA0:
            break
        if 0x20 <= value <= 0x7E:
            chars.append(chr(value))
        elif 0xC1 <= value <= 0xDA:
            chars.append(chr(value - 0x80))
        else:
            chars.append(f"\\x{value:02x}")
    return "".join(chars).rstrip()


class D64Image:
    def __init__(self, data: bytes, source: Path | None = None) -> None:
        if len(data) != STANDARD_D64_SIZE:
            raise D64Error(
                f"expected a 35-track {STANDARD_D64_SIZE}-byte D64, got {len(data)} bytes"
            )
        self.data = data
        self.source = source

    @classmethod
    def read(cls, path: str | Path) -> "D64Image":
        source = Path(path)
        return cls(source.read_bytes(), source)

    @staticmethod
    def sector_offset(ref: SectorRef) -> int:
        if not 1 <= ref.track <= 35:
            raise D64Error(f"invalid track: {ref.track}")
        count = SECTORS_PER_TRACK[ref.track]
        if not 0 <= ref.sector < count:
            raise D64Error(
                f"invalid sector {ref.sector} for track {ref.track} (has {count})"
            )
        preceding = sum(SECTORS_PER_TRACK[1 : ref.track])
        return (preceding + ref.sector) * 256

    def sector(self, ref: SectorRef) -> bytes:
        offset = self.sector_offset(ref)
        return self.data[offset : offset + 256]

    def follow_chain(self, start: SectorRef) -> FileChain:
        ref = start
        seen: set[SectorRef] = set()
        refs: list[SectorRef] = []
        payload = bytearray()

        while ref.track:
            if ref in seen:
                raise D64Error(f"sector-chain loop at {ref}")
            seen.add(ref)
            refs.append(ref)
            sector = self.sector(ref)
            next_track, next_sector = sector[0], sector[1]
            if next_track == 0:
                used_data_bytes = next_sector - 1
                if not 0 <= used_data_bytes <= 254:
                    raise D64Error(
                        f"invalid final-sector byte count {next_sector} at {ref}"
                    )
                payload.extend(sector[2 : 2 + used_data_bytes])
                break
            payload.extend(sector[2:])
            ref = SectorRef(next_track, next_sector)

        return FileChain(bytes(payload), tuple(refs))

    def directory_entries(self) -> Iterator[DirectoryEntry]:
        ref = SectorRef(18, 1)
        seen: set[SectorRef] = set()
        type_names = {0: "DEL", 1: "SEQ", 2: "PRG", 3: "USR", 4: "REL"}

        while ref.track:
            if ref in seen:
                raise D64Error(f"directory-chain loop at {ref}")
            seen.add(ref)
            sector = self.sector(ref)
            for slot in range(8):
                start = 2 + slot * 32
                raw = sector[start : start + 32]
                type_byte = raw[0]
                if type_byte == 0:
                    continue
                low_type = type_byte & 0x07
                yield DirectoryEntry(
                    filename=decode_petscii_filename(raw[3:19]),
                    file_type=type_names.get(low_type, f"${low_type:02X}"),
                    closed=bool(type_byte & 0x80),
                    locked=bool(type_byte & 0x40),
                    start=SectorRef(raw[1], raw[2]),
                    blocks=raw[28] | raw[29] << 8,
                    directory_sector=ref,
                    slot=slot,
                )
            next_track, next_sector = sector[0], sector[1]
            if next_track == 0:
                break
            ref = SectorRef(next_track, next_sector)

    def find_entry(self, filename: str) -> DirectoryEntry:
        wanted = filename.casefold()
        matches = [e for e in self.directory_entries() if e.filename.casefold() == wanted]
        if not matches:
            raise D64Error(f"file not found: {filename}")
        if len(matches) > 1:
            raise D64Error(f"ambiguous filename: {filename}")
        return matches[0]


def command_list(args: argparse.Namespace) -> int:
    image = D64Image.read(args.image)
    for entry in image.directory_entries():
        state = "closed" if entry.closed else "open"
        lock = ",locked" if entry.locked else ""
        print(
            f"{entry.file_type:<3} {state}{lock:<7} {entry.start} "
            f"{entry.blocks:4d}  {entry.filename}"
        )
    return 0


def command_extract(args: argparse.Namespace) -> int:
    image = D64Image.read(args.image)
    entry = image.find_entry(args.filename)
    chain = image.follow_chain(entry.start)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(chain.payload)
    print(
        f"wrote {len(chain.payload)} bytes from {len(chain.sectors)} sectors "
        f"({chain.sectors[0]}..{chain.sectors[-1]}) to {output}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list a standard CBM DOS directory")
    list_parser.add_argument("image")
    list_parser.set_defaults(func=command_list)

    extract_parser = subparsers.add_parser("extract", help="extract one directory file")
    extract_parser.add_argument("image")
    extract_parser.add_argument("filename")
    extract_parser.add_argument("output")
    extract_parser.set_defaults(func=command_extract)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
