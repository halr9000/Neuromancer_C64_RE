#!/usr/bin/env python3
"""Targeted, label-aware 6502/6510 disassembler for PRG or flat binaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from .instruction_set import Instruction, OPCODES
except ImportError:  # Direct `python3 tools/dis.py` invocation.
    from instruction_set import Instruction, OPCODES


BRANCHES = {"BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BVC", "BVS"}


class Image:
    __slots__ = ("data", "base")

    def __init__(self, data: bytes, base: int) -> None:
        self.data = data
        self.base = base


def parse_number(value: str) -> int:
    if value.startswith("$"):
        return int(value[1:], 16)
    return int(value, 0)


def load_image(path: Path, flat_base: int | None) -> Image:
    data = path.read_bytes()
    if flat_base is not None:
        return Image(data, flat_base)
    if path.suffix.casefold() != ".prg" or len(data) < 2:
        raise ValueError("non-PRG input requires --base")
    return Image(data[2:], data[0] | data[1] << 8)


def load_labels(path: Path) -> dict[int, tuple[str, str]]:
    if not path.exists():
        return {}
    labels: dict[int, tuple[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("addr") or "").strip()
            if not raw:
                continue
            try:
                address = parse_number(raw)
            except ValueError:
                continue
            labels[address] = ((row.get("name") or "").strip(), (row.get("comment") or "").strip())
    return labels


def operand_text(
    instruction: Instruction,
    raw: bytes,
    address: int,
    labels: dict[int, tuple[str, str]],
) -> tuple[str, int | None]:
    mode = instruction.mode
    value8 = raw[1] if len(raw) > 1 else 0
    value16 = value8 | ((raw[2] if len(raw) > 2 else 0) << 8)
    target: int | None = None

    if mode == "imp": return "", None
    if mode == "acc": return "A", None
    if mode == "imm": return f"#${value8:02X}", None
    if mode == "zp": return f"${value8:02X}", value8
    if mode == "zpx": return f"${value8:02X},X", value8
    if mode == "zpy": return f"${value8:02X},Y", value8
    if mode == "indx": return f"(${value8:02X},X)", value8
    if mode == "indy": return f"(${value8:02X}),Y", value8
    if mode == "ind": return f"(${value16:04X})", value16
    if mode == "abs": target = value16; text = f"${value16:04X}"
    elif mode == "absx": target = value16; text = f"${value16:04X},X"
    elif mode == "absy": target = value16; text = f"${value16:04X},Y"
    elif mode == "rel":
        displacement = value8 if value8 < 0x80 else value8 - 0x100
        target = (address + 2 + displacement) & 0xFFFF
        text = f"${target:04X}"
    else:
        return "", None

    if target in labels and labels[target][0]:
        text += f" <{labels[target][0]}>"
    return text, target


def disassemble(
    image: Image,
    start: int,
    lines: int,
    labels: dict[int, tuple[str, str]],
) -> list[str]:
    output: list[str] = []
    address = start
    for _ in range(lines):
        offset = address - image.base
        if not 0 <= offset < len(image.data):
            break
        opcode = image.data[offset]
        instruction = OPCODES[opcode]
        raw = image.data[offset : offset + instruction.size]
        if len(raw) < instruction.size:
            break
        if address in labels and labels[address][0]:
            comment = f" ; {labels[address][1]}" if labels[address][1] else ""
            output.append(f"{labels[address][0]}:{comment}")
        operand, _ = operand_text(instruction, raw, address, labels)
        bytes_text = " ".join(f"{value:02X}" for value in raw)
        label_comment = ""
        if instruction.mnemonic == "???":
            operand = f"${opcode:02X}"
            instruction_text = ".byte"
            label_comment = " ; undocumented/unclassified opcode"
        else:
            instruction_text = instruction.mnemonic
        output.append(
            f"${address:04X}  {bytes_text:<8}  {instruction_text:<5} {operand}{label_comment}".rstrip()
        )
        address = (address + instruction.size) & 0xFFFF
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("addr", type=parse_number)
    parser.add_argument("lines", type=int, nargs="?", default=40)
    parser.add_argument("--base", type=parse_number, help="load address for a flat binary")
    parser.add_argument("--labels", type=Path, default=Path("labels.csv"))
    args = parser.parse_args()

    image = load_image(args.file, args.base)
    labels = load_labels(args.labels)
    for line in disassemble(image, args.addr, args.lines, labels):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
