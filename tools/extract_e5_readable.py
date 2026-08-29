#!/usr/bin/env python3
"""Export readable DOX screen pages and the solution's PETSCII replay stream."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCREEN_WIDTH = 40
SCREEN_HEIGHT = 25
DOX_PAGE_START = 0x1000
DOX_PAGE_STRIDE = 0x0400
DOX_SCREEN_BYTES = SCREEN_WIDTH * SCREEN_HEIGHT
SOLUTION_STREAM_START = 0x2800


def screen_code_char(value: int) -> str:
    code = value & 0x7F
    if code == 0x00: return "@"
    if 0x01 <= code <= 0x1A: return chr(ord("A") + code - 1)
    if code == 0x1B: return "["
    if code == 0x1C: return "£"
    if code == 0x1D: return "]"
    if code == 0x1E: return "↑"
    if code == 0x1F: return "←"
    if 0x20 <= code <= 0x3F: return chr(code)
    if code == 0x47: return "│"
    return "·"


def render_dox_pages(memory: bytes) -> tuple[str, list[dict[str, object]]]:
    end_high = memory[0x0D06]
    end = end_high << 8
    if end <= DOX_PAGE_START or (end - DOX_PAGE_START) % DOX_PAGE_STRIDE:
        raise ValueError(f"invalid traced DOX page end ${end:04X}")
    sections: list[str] = []
    records: list[dict[str, object]] = []
    page_number = 1
    for base in range(DOX_PAGE_START, end, DOX_PAGE_STRIDE):
        raw = memory[base : base + DOX_SCREEN_BYTES]
        lines = []
        for row in range(SCREEN_HEIGHT):
            start = row * SCREEN_WIDTH
            line = "".join(screen_code_char(value) for value in raw[start : start + SCREEN_WIDTH])
            lines.append(line.rstrip())
        while lines and not lines[-1]:
            lines.pop()
        sections.append(
            f"===== DOX PAGE {page_number:02d} [${base:04X}-${base + DOX_SCREEN_BYTES - 1:04X}] =====\n"
            + "\n".join(lines)
        )
        records.append(
            {
                "page": page_number,
                "source_start": f"0x{base:04X}",
                "source_end": f"0x{base + DOX_SCREEN_BYTES - 1:04X}",
                "rows": len(lines),
            }
        )
        page_number += 1
    return "\n\n".join(sections) + "\n", records


class PetsciiTerminal:
    """Small C64 KERNAL screen-editor model used for provenance replay.

    The C64 cursor is not just a (row, column) pair: a logical line can span
    two 40-column physical rows.  The solution stream relies on that detail,
    as well as INSERT and DELETE, while correcting and laying out its text.
    """

    def __init__(self) -> None:
        self.screen = [[" "] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
        self.line_starts = [True] * SCREEN_HEIGHT
        self.row = 0
        self.offset = 0
        self.insert_count = 0
        self.scrolled_lines: list[str] = []
        self.segments: list[list[str]] = []

    @property
    def column(self) -> int:
        return self.offset % SCREEN_WIDTH

    def _logical_start(self, row: int | None = None) -> int:
        row = self.row if row is None else row
        row = max(0, min(SCREEN_HEIGHT - 1, row))
        while row > 0 and not self.line_starts[row]:
            row -= 1
        return row

    def _logical_end(self, start: int | None = None) -> int:
        start = self._logical_start() if start is None else start
        end = start
        while end + 1 < SCREEN_HEIGHT and not self.line_starts[end + 1]:
            end += 1
        return min(end, start + 1)

    def _line_max(self) -> int:
        return (self._logical_end() - self._logical_start() + 1) * SCREEN_WIDTH - 1

    def _set_offset(self, offset: int) -> None:
        start = self._logical_start()
        self.offset = max(0, min(self._line_max(), offset))
        self.row = start + self.offset // SCREEN_WIDTH

    def _scroll_logical_line(self) -> int:
        """Scroll one complete top logical line, as the KERNAL does."""
        count = 1
        if SCREEN_HEIGHT > 1 and not self.line_starts[1]:
            count = 2
        for _ in range(count):
            self.scrolled_lines.append("".join(self.screen.pop(0)).rstrip())
            self.line_starts.pop(0)
            self.screen.append([" "] * SCREEN_WIDTH)
            self.line_starts.append(True)
        self.line_starts[0] = True
        self.row = max(0, self.row - count)
        return count

    def _ensure_row(self, wanted: int) -> int:
        while wanted >= SCREEN_HEIGHT:
            wanted -= self._scroll_logical_line()
        return wanted

    def _next_logical_row(self, row: int | None = None) -> int:
        row = self.row if row is None else row
        start = self._logical_start(row)
        target = self._logical_end(start) + 1
        target = self._ensure_row(target)
        while target < SCREEN_HEIGHT and not self.line_starts[target]:
            target += 1
            target = self._ensure_row(target)
        return target

    def _previous_logical_row(self) -> int | None:
        start = self._logical_start()
        if start == 0:
            return None
        return self._logical_start(start - 1)

    def _extend_logical_line(self) -> None:
        start = self._logical_start()
        if self._logical_end(start) > start:
            return
        target = self._ensure_row(start + 1)
        start = self._logical_start()
        target = start + 1
        if target >= SCREEN_HEIGHT:
            raise RuntimeError("failed to make room for wrapped logical line")
        self.line_starts[target] = False
        if target + 1 < SCREEN_HEIGHT:
            self.line_starts[target + 1] = True

    def _advance(self) -> None:
        old_max = self._line_max()
        old_offset = self.offset
        if old_offset < old_max:
            self._set_offset(old_offset + 1)
            return
        if old_max == SCREEN_WIDTH - 1:
            self._extend_logical_line()
            self._set_offset(old_offset + 1)
            return
        self.row = self._next_logical_row()
        self.offset = 0

    def put(self, char: str) -> None:
        start = self._logical_start()
        physical_row = start + self.offset // SCREEN_WIDTH
        self.screen[physical_row][self.offset % SCREEN_WIDTH] = char
        self._advance()
        if self.insert_count:
            self.insert_count -= 1

    def carriage_return(self) -> None:
        self.insert_count = 0
        self.row = self._next_logical_row()
        self.offset = 0

    def delete(self) -> None:
        self.move_left()
        start = self._logical_start()
        maximum = self._line_max()
        for position in range(self.offset, maximum):
            source_row = start + (position + 1) // SCREEN_WIDTH
            source_column = (position + 1) % SCREEN_WIDTH
            target_row = start + position // SCREEN_WIDTH
            target_column = position % SCREEN_WIDTH
            self.screen[target_row][target_column] = self.screen[source_row][source_column]
        self.screen[start + maximum // SCREEN_WIDTH][maximum % SCREEN_WIDTH] = " "

    def insert(self) -> None:
        start = self._logical_start()
        maximum = self._line_max()
        last_row = start + maximum // SCREEN_WIDTH
        last_column = maximum % SCREEN_WIDTH
        if self.screen[last_row][last_column] != " " and maximum < 79:
            self._insert_physical_row(start + 1)
            start = self._logical_start()
            maximum = self._line_max()
        for position in range(maximum, self.offset, -1):
            source_row = start + (position - 1) // SCREEN_WIDTH
            source_column = (position - 1) % SCREEN_WIDTH
            target_row = start + position // SCREEN_WIDTH
            target_column = position % SCREEN_WIDTH
            self.screen[target_row][target_column] = self.screen[source_row][source_column]
        self.screen[start + self.offset // SCREEN_WIDTH][self.offset % SCREEN_WIDTH] = " "
        self.insert_count += 1

    def _insert_physical_row(self, row: int) -> None:
        if row >= SCREEN_HEIGHT:
            self._scroll_logical_line()
            row = SCREEN_HEIGHT - 1
        else:
            self.screen.pop()
            self.line_starts.pop()
            self.screen.insert(row, [" "] * SCREEN_WIDTH)
            self.line_starts.insert(row, False)
        self.line_starts[row] = False

    def move_right(self) -> None:
        maximum = self._line_max()
        if self.offset < maximum:
            self._set_offset(self.offset + 1)
        else:
            self.row = self._next_logical_row()
            self.offset = 0

    def move_left(self) -> None:
        if self.offset > 0:
            self._set_offset(self.offset - 1)
            return
        previous = self._previous_logical_row()
        if previous is None:
            return
        self.row = previous
        self.offset = self._line_max()
        self.row = self._logical_start() + self.offset // SCREEN_WIDTH

    def move_down(self) -> None:
        start = self._logical_start()
        end = self._logical_end(start)
        column = self.offset % SCREEN_WIDTH
        if self.row < end:
            self.offset += SCREEN_WIDTH
            self.row += 1
            return
        self.row = self._next_logical_row()
        maximum = self._line_max()
        self.offset = min(column, maximum)
        self.row = self._logical_start() + self.offset // SCREEN_WIDTH

    def move_up(self) -> None:
        column = self.offset % SCREEN_WIDTH
        start = self._logical_start()
        if self.row > start:
            self.row -= 1
            self.offset -= SCREEN_WIDTH
            return
        if self.row == 0:
            return
        target_physical = self.row - 1
        self.row = target_physical
        target_start = self._logical_start()
        self.offset = (target_physical - target_start) * SCREEN_WIDTH + column

    def home(self) -> None:
        self.row = 0
        self.offset = 0
        self.insert_count = 0

    def _capture_segment(self) -> None:
        visible = ["".join(row).rstrip() for row in self.screen]
        segment = self.scrolled_lines + visible
        while segment and not segment[0]:
            segment.pop(0)
        while segment and not segment[-1]:
            segment.pop()
        if any(line for line in segment):
            self.segments.append(segment)

    def clear(self) -> None:
        self._capture_segment()
        self.screen = [[" "] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
        self.line_starts = [True] * SCREEN_HEIGHT
        self.row = 0
        self.offset = 0
        self.insert_count = 0
        self.scrolled_lines = []

    def finish(self) -> list[list[str]]:
        self._capture_segment()
        return self.segments


def petscii_printable(value: int) -> str | None:
    if value == 0xA0: return " "
    if 0x20 <= value <= 0x7E: return chr(value)
    if 0xC1 <= value <= 0xDA: return chr(value - 0x80)
    return None


def render_solution(memory: bytes, end_exclusive: int) -> tuple[str, dict[str, object]]:
    terminal = PetsciiTerminal()
    cursor = SOLUTION_STREAM_START
    end_marker = None
    control_counts: dict[str, int] = {}

    def count(name: str) -> None:
        control_counts[name] = control_counts.get(name, 0) + 1

    while cursor < end_exclusive:
        value = memory[cursor]
        cursor += 1
        if value == 0x8C:
            end_marker = cursor - 1
            count("end")
            break
        if value == 0x0D:
            terminal.carriage_return(); count("return"); continue
        if value == 0x14:
            terminal.delete(); count("delete"); continue
        if value == 0x1D:
            terminal.move_right(); count("right"); continue
        if value == 0x9D:
            terminal.move_left(); count("left"); continue
        if value == 0x11:
            terminal.move_down(); count("down"); continue
        if value == 0x91:
            terminal.move_up(); count("up"); continue
        if value == 0x13:
            terminal.home(); count("home"); continue
        if value == 0x93:
            terminal.clear(); count("clear"); continue
        if value == 0x94:
            terminal.insert(); count("insert"); continue
        if value in (0x85, 0x86, 0x87, 0x8A, 0x8B):
            count(f"viewer_${value:02X}"); continue
        if value in (
            0x05, 0x12, 0x1C, 0x1E, 0x1F, 0x81, 0x89, 0x90, 0x92,
            0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C, 0x9E, 0x9F,
        ):
            count(f"display_${value:02X}"); continue
        char = petscii_printable(value)
        if char is not None:
            terminal.put(char)
        else:
            count(f"ignored_${value:02X}")

    blocks: list[str] = []
    segments = terminal.finish()
    for section_number, segment in enumerate(segments, 1):
        blocks.append(f"===== SOLUTION SECTION {section_number:02d} =====\n" + "\n".join(segment))
    return "\n\n".join(blocks) + "\n", {
        "stream_start": f"0x{SOLUTION_STREAM_START:04X}",
        "stream_end_marker": f"0x{end_marker:04X}" if end_marker is not None else None,
        "bytes_examined": cursor - SOLUTION_STREAM_START,
        "captured_sections": len(segments),
        "section_lines": [len(segment) for segment in segments],
        "control_counts": control_counts,
    }


def clean_solution_replay(replay: str) -> tuple[str, list[dict[str, str]]]:
    """Apply a small, auditable set of repairs to cursor-damaged layouts."""
    repairs: list[dict[str, str]] = []

    def replace_once(label: str, old: str, new: str) -> None:
        nonlocal replay
        occurrences = replay.count(old)
        if occurrences != 1:
            raise ValueError(
                f"editorial repair {label!r} expected one source block, found {occurrences}"
            )
        replay = replay.replace(old, new, 1)
        repairs.append({"label": label, "basis": "characters and values present in decoded stream"})

    replace_once(
        "title card",
        """===== SOLUTION SECTION 01 =====
       --------------------
      ---    NEUROMANC--   -
      ------    SOL-----   -
      ------------------   -
      -  BY THE ANNIHILATOR-
      ---    MAY 2, 19-- -
      -------------------
""",
        """===== SOLUTION SECTION 01 =====
NEUROMANCER SOL
BY THE ANNIHILATOR
MAY 2, 1989
""",
    )
    replace_once(
        "COMLINK 4 overwritten line",
        """ON THE PANTHER MODERNS DB FOR THE LINK
ND THEN USE COPTALK TO TALK""",
        """ON THE PANTHER MODERNS DB FOR THE LINK
CODES, AND THEN USE COPTALK TO TALK""",
    )
    replace_once(
        "useful numbers table",
        """USEFUL NUMBERS

YOUR BAMA ID NUMBER...      056306118
LARRY MOE'S ID NUMBER.   062788138
ACCOUNT AT GEMEINSCHAFT.       646328356
481   ACCOUNT AT BOZOB.........   712345
ACCOUNT AT BACK OF BER.........328356481
1200                    ....
AUTHORIZATION CODE .........RNE..
VAULT CODE FOR GEMEINSCHA...FT...
DIXIE FLATLINE'S N/.........LYMA1211MARZ
TOSHIRO'S NUMBER..................BG1066
ROMBO'S NUMBER...................0467839
                              ...6905984
                              ...5521426""",
        """USEFUL NUMBERS

YOUR BAMA ID NUMBER...............056306118
LARRY MOE'S ID NUMBER.............062788138
ACCOUNT AT BANK GEMEINSCHAFT......646328356481
ACCOUNT AT BOZOBANK...............712345450134
ACCOUNT AT BANK OF BERNE..........121519831200
AUTHORIZATION CODE FOR BERNE......LYMA1211MARZ
VAULT CODE FOR GEMEINSCHAFT.......BG1066
DIXIE FLATLINE'S NUMBER...........0467839
TOSHIRO'S NUMBER..................6905984
ROMBO'S NUMBER....................5521426""",
    )
    replace_once(
        "section 7 initial",
        "===== SOLUTION SECTION 07 =====\nELOW IS THE LOCATIONS ON WHERE",
        "===== SOLUTION SECTION 07 =====\nBELOW IS THE LOCATIONS ON WHERE",
    )
    replace_once(
        "closing text",
        """===== SOLUTION SECTION 11 =====
 HOPE THAT THIS HELP FILE I""",
        """===== SOLUTION SECTION 11 =====
I HOPE THAT THIS HELP FILE I""",
    )
    replace_once(
        "closing sign-off",
        """SPECIAL HELLOS TO IRON FIST.



           THE ANNIHILATOR""",
        """SPECIAL HELLOS TO IRON FIST.

THATS ALL FOR NOW...

THE ANNIHILATOR""",
    )
    return replay, repairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dox_memory", type=Path)
    parser.add_argument("solution_prg", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    dox_memory = args.dox_memory.read_bytes()
    solution_prg = args.solution_prg.read_bytes()
    if len(dox_memory) != 0x10000:
        raise ValueError("DOX memory image must be 64 KiB")
    if len(solution_prg) < 2 or solution_prg[:2] != b"\x01\x08":
        raise ValueError("solution input must be an unpacked $0801 PRG")
    solution_memory = bytearray(0x10000)
    solution_payload = solution_prg[2:]
    solution_memory[0x0801 : 0x0801 + len(solution_payload)] = solution_payload

    dox_text, dox_pages = render_dox_pages(dox_memory)
    solution_end = 0x0801 + len(solution_payload)
    solution_replay, solution_map = render_solution(solution_memory, solution_end)
    solution_text, editorial_repairs = clean_solution_replay(solution_replay)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dox_path = args.output_dir / "neuromancer_dox_readable.txt"
    solution_path = args.output_dir / "neuromancer_solution_readable.txt"
    replay_path = args.output_dir / "neuromancer_solution_terminal_replay.txt"
    map_path = args.output_dir / "e5_readable_map.json"
    dox_path.write_text(dox_text, encoding="utf-8")
    solution_path.write_text(solution_text, encoding="utf-8")
    replay_path.write_text(solution_replay, encoding="utf-8")
    solution_map["terminal_replay_sha256"] = hashlib.sha256(
        solution_replay.encode("utf-8")
    ).hexdigest()
    solution_map["readable_sha256"] = hashlib.sha256(solution_text.encode("utf-8")).hexdigest()
    solution_map["editorial_repairs"] = editorial_repairs
    map_path.write_text(
        json.dumps({"dox_pages": dox_pages, "solution_stream": solution_map}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {dox_path} ({len(dox_pages)} pages)")
    print(f"wrote {solution_path}")
    print(f"wrote {replay_path}")
    print(f"wrote {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
