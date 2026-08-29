# E5 documentation-disk format

## Result

The auxiliary `NEUROMA4.D64` image has been fully extracted and both packed PRGs have readable exports.

| Disk entry | Raw PRG | Decoded result |
|---|---:|---|
| `NEUROMANCER DOX` | 5,577 bytes | 11 fixed 40x25 screen-code pages |
| `NEUROMANCER SOL` | 22,655 bytes | 34,285-byte native reader image with a 26,094-byte PETSCII/control stream |

The disk is Frontline package material, not an original E1-E4 game side.

## DOX contents

The DOX is a short scene-style hint file credited to INJUN. Its 11 screens contain:

- opening and early-game guidance;
- link codes, passwords, and required COMLINK versions;
- software available from particular bases;
- cryptology encoded/decoded-word mappings;
- NPC conversation keywords;
- a C64 memory-edit cash/bank cheat;
- author/contact and closing screens.

Readable export: `extracted/e5/neuromancer_dox_readable.txt`.

## DOX unpacking

The DOX PRG loads at `$0801` and uses three nested relocation/decompression stages.

1. `$080D` installs a page-copy relocator at `$03B7`.
2. Relocated `$080B` installs a backwards LZ-style depacker in low memory. Its main entry is `$0100`; it hands off at `$24BF` after 314,526 instructions in the project 6502 core.
3. `$080B` then installs a small backwards RLE stage at `$00D4/$00E4`. This stage uses the undocumented `DCP zp` instruction at `$00DA` as part of its self-modifying source pointer and hands off to the final viewer at `$0A00`.

The complete chain executes 1,119,310 instructions from the first relocated entry `$03AD` to final viewer entry `$0A00`.

The viewer starts page data at `$1000`. Byte `$0D06` contains `$3C`, the exclusive high-byte limit. Page starts therefore run `$1000, $1400, ... $3800`, giving 11 pages. Each page contributes the first 1,000 bytes as a 40-column by 25-row C64 screen-code matrix. The final viewer permutes copy order with a table at `$0F00`, but that animation does not change the final screen matrix.

## Solution contents

The solution is a large walkthrough credited to “The Annihilator” and dated May 2, 1989. It includes:

- the opening Chiba/PAX sequence and main progression;
- where to acquire COMLINK versions and skill chips;
- location and NPC guidance;
- useful IDs, accounts, authorization codes, and passwords;
- cyberspace entry zones and PAX locations;
- ware levels and ICE-combat guidance;
- database link codes, coordinates, downloadable warez, AI identities, and weaknesses;
- late-game database and AI order guidance.

Readable export: `extracted/e5/neuromancer_solution_readable.txt`.

The source is a recorded PETSCII screen-edit stream rather than paragraphs stored as plain text. It intentionally contains cursor movement, INSERT/DELETE corrections, colors, clears, and viewer commands. The extractor models the C64 KERNAL screen editor's one- or two-row logical lines and replays all 26,094 stream bytes against a 40x25 screen. The implementation was checked against the reconstructed [C64 KERNAL editor source](https://github.com/mist64/c64rom/blob/master/kernal/editor.1.s).

Two forms are retained:

- `neuromancer_solution_terminal_replay.txt` is the unedited terminal result;
- `neuromancer_solution_readable.txt` applies six deterministic repairs to text damaged by elaborate cursor-overwrite layouts: the title card, one COMLINK line, the useful-numbers table, a dropped section initial, and two closing fragments.

Every repair is asserted by exact source-block matching and listed in `e5_readable_map.json`. All repaired characters and values occur in the decoded stream; the useful-numbers interpretation was also cross-checked against the independent [C64-Wiki Neuromancer tables](https://www.c64-wiki.com/wiki/Neuromancer/Tables). Original spelling and factual errors otherwise remain untouched.

## Solution unpacking

The solution PRG loads at `$0801`.

1. `$0811` copies the decoder from `$0769-$0A68` to `$CD00-$CFFF` and jumps to `$CDC2`.
2. `$CDC2` relocates the compressed source `$0A5B-$607D` to `$70DD-$C6FF`.
3. `$CE50` decodes entropy symbols using range tables at `$CED2-$CEFF` and a 256-byte output-symbol table at `$CF00`.
4. The outer layer treats `$F3` as an RLE marker: counts below four escape literal `$F3`; counts four or greater are followed by the repeated byte.
5. Exactly 22,051 compressed bytes produce `$0801-$8DED` (34,285 bytes). The decoded PETSCII/control stream begins at `$2800` and ends with viewer marker `$8C` at `$8DED`.

The decoded memory SHA-256 is `9ed31ff35ac9cd69182fc8b5a88b987e7a545aaa39ccd85336e4233e32fb8446`.

## Reproduction

From the project root:

```sh
python3 tools/extract_e5.py intake/NEUROMA4.D64 extracted/e5
python3 tools/relocate_e5_viewers.py \
  extracted/e5/neuromancer_dox.prg \
  extracted/e5/neuromancer_sol.prg \
  extracted/e5
python3 tools/decode_e5_dox.py extracted/e5/neuromancer_dox.prg extracted/e5
python3 tools/decode_e5_solution.py extracted/e5/neuromancer_sol.prg extracted/e5
python3 tools/extract_e5_readable.py \
  extracted/e5/neuromancer_dox_unpacked_memory.bin \
  extracted/e5/neuromancer_solution_unpacked.prg \
  extracted/e5
```

Every raw extraction and decoded layer has a JSON provenance map under `extracted/e5/`. The map includes hashes for both the terminal replay and cleaned transcript.
