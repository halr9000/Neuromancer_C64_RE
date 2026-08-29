#!/usr/bin/env python3
"""Decode Commodore BASIC V2 tokenized programs with address provenance."""

from __future__ import annotations

import argparse
from pathlib import Path


TOKENS = {
    0x80: "END", 0x81: "FOR", 0x82: "NEXT", 0x83: "DATA", 0x84: "INPUT#",
    0x85: "INPUT", 0x86: "DIM", 0x87: "READ", 0x88: "LET", 0x89: "GOTO",
    0x8A: "RUN", 0x8B: "IF", 0x8C: "RESTORE", 0x8D: "GOSUB", 0x8E: "RETURN",
    0x8F: "REM", 0x90: "STOP", 0x91: "ON", 0x92: "WAIT", 0x93: "LOAD",
    0x94: "SAVE", 0x95: "VERIFY", 0x96: "DEF", 0x97: "POKE", 0x98: "PRINT#",
    0x99: "PRINT", 0x9A: "CONT", 0x9B: "LIST", 0x9C: "CLR", 0x9D: "CMD",
    0x9E: "SYS", 0x9F: "OPEN", 0xA0: "CLOSE", 0xA1: "GET", 0xA2: "NEW",
    0xA3: "TAB(", 0xA4: "TO", 0xA5: "FN", 0xA6: "SPC(", 0xA7: "THEN",
    0xA8: "NOT", 0xA9: "STEP", 0xAA: "+", 0xAB: "-", 0xAC: "*", 0xAD: "/",
    0xAE: "^", 0xAF: "AND", 0xB0: "OR", 0xB1: ">", 0xB2: "=", 0xB3: "<",
    0xB4: "SGN", 0xB5: "INT", 0xB6: "ABS", 0xB7: "USR", 0xB8: "FRE",
    0xB9: "POS", 0xBA: "SQR", 0xBB: "RND", 0xBC: "LOG", 0xBD: "EXP",
    0xBE: "COS", 0xBF: "SIN", 0xC0: "TAN", 0xC1: "ATN", 0xC2: "PEEK",
    0xC3: "LEN", 0xC4: "STR$", 0xC5: "VAL", 0xC6: "ASC", 0xC7: "CHR$",
    0xC8: "LEFT$", 0xC9: "RIGHT$", 0xCA: "MID$", 0xCB: "GO",
}


CONTROL_NAMES = {
    0x05: "WHITE", 0x0D: "RETURN", 0x11: "DOWN", 0x12: "RVS ON",
    0x13: "HOME", 0x14: "DELETE", 0x1C: "RED", 0x1D: "RIGHT",
    0x1E: "GREEN", 0x1F: "BLUE", 0x81: "ORANGE", 0x90: "BLACK",
    0x91: "UP", 0x92: "RVS OFF", 0x93: "CLEAR", 0x94: "INSERT",
    0x95: "BROWN", 0x96: "LIGHT RED", 0x97: "DARK GREY", 0x98: "GREY",
    0x99: "LIGHT GREEN", 0x9A: "LIGHT BLUE", 0x9B: "LIGHT GREY",
    0x9C: "PURPLE", 0x9E: "YELLOW", 0x9F: "CYAN",
}


class BasicLine:
    __slots__ = ("address", "next_address", "number", "raw", "text")

    def __init__(
        self,
        address: int,
        next_address: int,
        number: int,
        raw: bytes,
        text: str,
    ) -> None:
        self.address = address
        self.next_address = next_address
        self.number = number
        self.raw = raw
        self.text = text


def petscii_char(value: int) -> str:
    if value in CONTROL_NAMES:
        return "{" + CONTROL_NAMES[value] + "}"
    if value == 0xFF:
        return "π"
    if 0x20 <= value <= 0x7E:
        return chr(value)
    if 0xA0 <= value <= 0xDF:
        return chr(value - 0x80)
    return f"{{${value:02X}}}"


def decode_line_body(raw: bytes) -> str:
    output: list[str] = []
    quoted = False
    literal_mode = False
    for value in raw:
        if value == 0x22:
            quoted = not quoted
            output.append('"')
            continue
        if value == 0x3A and literal_mode and not quoted:
            literal_mode = False
            output.append(":")
            continue
        if not quoted and not literal_mode and value in TOKENS:
            token = TOKENS[value]
            output.append(token)
            if value in (0x83, 0x8F):
                literal_mode = True
            continue
        output.append(petscii_char(value))
    return "".join(output)


def parse_program(memory: bytes, base: int = 0x0801) -> list[BasicLine]:
    lines: list[BasicLine] = []
    address = base
    visited: set[int] = set()
    while True:
        offset = address - base
        if not 0 <= offset + 1 < len(memory):
            raise ValueError(f"BASIC line pointer ${address:04X} is outside the image")
        if address in visited:
            raise ValueError(f"BASIC line-pointer loop at ${address:04X}")
        visited.add(address)
        next_address = memory[offset] | memory[offset + 1] << 8
        if next_address == 0:
            break
        if offset + 4 > len(memory):
            raise ValueError(f"truncated BASIC header at ${address:04X}")
        number = memory[offset + 2] | memory[offset + 3] << 8
        end = memory.find(b"\x00", offset + 4)
        if end < 0:
            raise ValueError(f"unterminated BASIC line {number} at ${address:04X}")
        raw = memory[offset + 4 : end]
        if next_address != base + end + 1:
            raise ValueError(
                f"line {number} at ${address:04X} points to ${next_address:04X}, "
                f"but its terminator implies ${base + end + 1:04X}"
            )
        lines.append(BasicLine(address, next_address, number, raw, decode_line_body(raw)))
        address = next_address
    return lines


def render_listing(lines: list[BasicLine], provenance: bool = False) -> str:
    output: list[str] = []
    for line in lines:
        prefix = f"[${line.address:04X}] " if provenance else ""
        output.append(f"{prefix}{line.number} {line.text}")
    return "\n".join(output) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prg", type=Path)
    parser.add_argument("--provenance", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = args.prg.read_bytes()
    if len(data) < 2:
        raise ValueError("truncated PRG")
    base = data[0] | data[1] << 8
    listing = render_listing(parse_program(data[2:], base), args.provenance)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(listing, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(listing, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
