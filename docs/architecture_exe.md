# Neuromancer C64 executable architecture

## Checkpoint status

The supplied Frontline/GameBase build is now reconstructed from the ordinary
E1 `LOAD` command through the first playable-room runtime. The chain is not a
flat PRG: it changes the KERNAL load destination, installs code in the 1541,
fastloads a packed record, executes three unpack/relocation layers, loads a
second disk-resident loader, and finally assembles the engine from hidden raw
sectors on sides E1 and E2.

Everything marked **verified** below is reproduced by the scripts and tests in
`tools/`. Names for higher-level gameplay routines are descriptive RE labels,
not original symbols.

## Complete startup chain

| Stage | Input | Output / transfer | Verification |
|---|---|---|---|
| DOS load | E1 file `NEUROMANCER`, T13/S09 | nominal PRG load `$02A7` | 204-sector directory chain, 51,794 bytes |
| Autostart | `$02A7` through overwritten `ISTOP` | redirects KERNAL load pointer to `$C000`; waits for `$C240` | handlers `$02A7` and `$02BD` |
| Loader install | runtime `$C000-$C23F` | 1541 `$0700-$07FF`; C64 client `$0100-$01B5` | eight `M-W` blocks and `M-E $079F` |
| Fastload record | T13/S12 through T30/S07 | `$0801-$CF56`, 51,030 bytes | 201 sectors; SHA-256 `3570ffb6d90d…` |
| BASIC launcher | line 1744, `SYS 2051` | `$0803`, then deliberate branch to `$080B` | launcher parsed structurally |
| Frontline depacker | `$080B` | unpacked entry `$080D` | 2,280,962 emulated instructions |
| Runtime relocation | `$080D` | relocated entry `$008E` | 288,375 emulated instructions |
| Zero-page decoder | `$008E`; stream begins `$242D` | handoff `$020A` | 558,474 emulated instructions |
| Self-erasing stub | `$020A-$0248` | stable startup `$03E7` | 596 instructions; crafted `RTI` frame |
| Game assembly | startup plus file `A` | vector table `$4300`; engine `$4836` | raw modules decoded and overlaid |
| First room | E1 and E2 raw modules | room runtime `$F000-$FBFF` | room 0 vectors and snapshot verified |

The important stable entry points are therefore:

- `$03E7`: first stable game-owned startup after all crack/depack stages;
- `$4300`: 55-entry engine jump table;
- `$4836`: engine initialization and main dispatcher;
- `$488D`: recurring gameplay tick;
- `$6158`: room/side loader;
- `$F00A/$F00D/$F010`: room-specific initialize, tick, and teardown vectors.

## Depack and relocation layers

### Fastloaded image

The fastloader reconstructs one record at `$0801-$CF56`. Its first bytes are a
valid BASIC V2 line, but `$0803` is a deliberate `BNE $080B`, so execution
skips the visible line text and enters the Frontline bootstrap directly.

### Frontline bootstrap and depacker

The `$080B` stage installs working code at `$00FA-$01F9` and `$0333-$03DD`,
shifts the packed stream from `$09B3` down to `$07E8`, and expands it until it
hands off at `$080D`. The resulting 64 KiB snapshot has SHA-256
`ff364efe1e15…`.

### Runtime relocation

The `$080D` code performs a large descending relocation:

- source `$0C50-$E922`;
- destination `$232D-$FFFF`;
- delta `$16DD`.

It also installs `$0A00-$0AFF` at `$0100-$01FF`, installs `$0900-$09FF` in zero
page, and initializes color memory from `$0B00/$0C00`. It then enters the
zero-page decoder at `$008E`.

### Final decoder and self-erasure

The decoder at `$008E` consumes a self-modifying stream beginning at `$242D`
and reaches `$020A`. The short `$020A` stub zeroes itself through `$0248`, then
uses the prepared stack bytes `$C7 $E0 $E7 $03` to reach `$03E7` through `RTI`.
That is the first stable address suitable for game-level analysis.

## File `A`: the runtime disk driver

Startup loads the normal DOS file `A` at `$3E00-$42F7`. Its first `$200` bytes
are a bus-decode lookup table; executable entries begin at `$4008`.

| Entry | Role |
|---|---|
| `$4008` | write a raw-sector module from `$FE/$FF` through end pointer `$FC/$FD` |
| `$400B` | read T18/S00 and return side marker byte `$02DC` |
| `$400E` | initialize the drive and execute hidden block T18/S02 |
| `$4011` | read a raw-sector module to destination `$FE/$FF` |

The drive bootstrap is installed with DOS command `B-E 2 0 18 02`. The four
game disks store ASCII side markers at T18/S00 byte `$DC`: `1`, `2`, `3`, and
`4`. The engine wrapper at `$4BEC` compares the requested side with that marker
and displays `Put side X in drive. Button or [space].` until it matches.

For `$4011`, X/Y are the initial track/sector. A hidden module is encoded as:

1. first-sector bytes 0-1: little-endian payload length;
2. first-sector bytes 2-255: the first 254 payload bytes;
3. continuation sectors: all 256 bytes;
4. traversal: increment sector using 1541 track geometry, advance track on
   wrap, and skip T18/S00 when entering track 18.

This is independent of CBM DOS file chains and explains why E2-E4 have no
usable directory.

## Initial hidden-module assembly

The stable `$03E7` startup loads these modules from E1. All ranges and hashes
are recorded exactly in `extracted/e1/e1_module_map.json`.

| Module | Raw start | Destination | Bytes | Role |
|---|---:|---:|---:|---|
| `core_4300` | T01/S02 | `$4300-$73FC` | 12,541 | engine, jump table, loader/UI/render helpers |
| `room_disk_tables_fe00` | T06/S19 | `$FE00-$FFFC` | 509 | parallel room track/sector/side arrays beneath KERNAL |
| `module_b800` | T03/S10 | `$B800-$C0FC` | 2,301 | high-memory engine module |
| `module_c700` | T03/S19 | `$C700-$C9FC` | 765 | high-memory engine module |
| `state_new` | T04/S01 | `$C100-$C6FC` | 1,533 | new-game state template |
| `state_slot_1` | T04/S07 | `$C100-$C9FC` | 2,301 | saved game 1 |
| `state_slot_2` | T04/S16 | `$C100-$C9FC` | 2,301 | saved game 2 |
| `state_slot_3` | T05/S04 | `$C100-$C9FC` | 2,301 | saved game 3 |
| `state_slot_4` | T05/S13 | `$C100-$C9FC` | 2,301 | saved game 4 |
| `module_0380` | T03/S09 | `$0380-$03FE` | 127 | low-memory engine/vector module |
| `module_a400` | T13/S00 | `$A400-$AC7F` | 2,176 | graphics/data beneath BASIC ROM |
| `module_8400` | T32/S10 | `$8400-$93FC` | 4,093 | main high-memory engine module |

Only one state module is selected. `N` at `OLD OR NEW GAME? (O/N)` records a
name and uses `state_new`. `O` requests slot 1-4 and selects the corresponding
2,301-byte state module. Startup then jumps `$4300`, whose first vector is
`JMP $4836`.

The corrected room-table module begins at **T06/S19**. The instruction is
`LDY #$13`; `$13` is hexadecimal 19. Treating it as decimal 13 produces a
plausible-length but invalid module, so the correct sector and hash are pinned
by regression tests.

## First playable room

The new-game state begins with room ID 0 at `$C330`. Two independent table sets
select its cross-disk overlays:

| Selection | Table evidence | Result |
|---|---|---|
| initial side-1 payload | direct call in `$4F23` | E1 T06/S06 -> `$CA00`, 3,264 bytes |
| location overlay | `$62C5/$62E3/$6301`, index 0 | E2 T01/S17 -> `$AC80`, 1,856 bytes |
| room logic/data | `$FE00/$FE3C/$FE78`, room 0 | E2 T06/S00 -> `$CA00`, 5,174 bytes |

`$6158` then copies `$CA00-$D5FF` to RAM `$F000-$FBFF`. The room-0 image exposes
three fixed vectors:

| Vector | Target | Verified behavior in room 0 |
|---|---|---|
| `$F00A` | `$F0F6` | initialize room animation/actor values |
| `$F00D` | `$F10E` | advance three timer-driven animation tables each tick |
| `$F010` | `$F10D` | teardown hook; room 0 currently returns immediately |

Bytes `$F002-$F003` point to `$F248`, the root of room-specific record/text
data consumed by the core entity dispatcher. The reproducible room snapshot is
`extracted/e1/e1_room0_ready_memory.bin`.

### Deterministic room-vector execution evidence

`tools/trace_e1_room0.py` executes those three vectors against the reconstructed
64 KiB room snapshot using synthetic RTS caller frames. This is instruction
execution in the project documented-opcode 6510 core, not a VIC-II/CIA/input or
VICE simulation.

The trace establishes the current labels with behavior rather than vector shape
alone:

| Call | Observed result |
|---|---|
| `$F00A -> $F0F6` | 13 instructions; sets `$03/$07/$14/$18` to `$22/$24/$33/$42` |
| 64 × `$F00D -> $F10E` | 1,276 instructions; changes timer bytes `$F17B-$F180` and drives zero-page values `$03/$04/$07/$08/$0C/$10` through multiple branches |
| `$F010 -> $F10D` | two instructions; immediate return |

The exact report is `extracted/e1/e1_room0_vector_trace.json`; its final memory
hash after init, 64 ticks, and teardown is
`f1006c2fa4c38ca6b6836d8a547f55b2779dc84c7ef65ddd077fcc912eff9387`.
VICE 3.10 captures now confirm initialize, 64 tick calls, and teardown against
the same reconstructed snapshot. Live main-loop and entity-dispatch captures
remain required before promoting entity-field names beyond the current evidence.

### Bounded entity-dispatcher evidence

The same trace uses a separate clone of the room snapshot to execute only the
safe, high-bit-inactive path of `$6429`. With synthetic `$FF` status bytes at
`$9D-$A0`, it completes in 24 instructions, saves `$F248` at `$6CBA-$6CBB`
through `$6C8C`, and invokes no entity script handler. Its self-modified operand
at `$6438` shows the visit order is slot 0 followed by slots 3, 2, and 1; a set
high bit skips a slot. The real snapshot has those four status bits clear, so
this proves dispatch control flow, not the semantics of the real room scripts.

## Core runtime map

| Address | Descriptive label | Evidence-backed behavior |
|---:|---|---|
| `$4836` | `e1_runtime_main_entry` | resets stack, installs engine state, initializes first room, enters dispatch |
| `$488D` | `e1_main_tick_loop` | calls entity scripts, room tick, sprite builder, UI/status and input updates |
| `$4B22` | `e1_runtime_initialize` | initializes zero-page state, interrupt vectors, memory banking and viewport |
| `$4BEC` | `e1_side_module_io` | validates disk marker, prompts for side, invokes file `A` read/write entry |
| `$5036` | `e1_begin_viewport` | consumes inline rectangle parameters and builds drawing bounds/state |
| `$5293` | `e1_render_inline_text` | consumes an inline string pointer and renders bounded text via `$54FA` |
| `$57B2` / `$57E7` | hit-region context / test | installs inline region lists and tests pointer coordinates against records |
| `$5B1E` | `e1_build_sprite_frame` | depth-sorts four actor records and builds VIC-II sprite-frame fields |
| `$6158` | `e1_load_room` | selects side modules, overlays room data and installs `$F000` runtime |
| `$6429` | `e1_dispatch_entity_scripts` | saves the room root, high-bit-tests four `$9D-$A0` status bytes, and dispatches qualifying `$C400` records |
| `$66B7` | `e1_select_entity_record` | maps entity index to `$C400 + index*8` and resolves its script pointer |
| `$6C8C` | `e1_set_room_data_root` | stores the `$F002/$F003` room-data root for record/text decoding |

The function roles above are cross-checked against call sites, self-modified
operands, table layout, and reconstructed RAM. A live emulator trace is still
needed before promoting all higher-level field names to final semantics.

## Reproduction

```bash
python3 tools/extract_e1.py intake/NEUROMA0.D64 extracted/e1
python3 tools/analyze_e1_boot.py extracted/e1/neuromancer_e1.prg extracted/e1
python3 tools/decode_e1_fastload.py intake/NEUROMA0.D64 extracted/e1
python3 tools/decode_e1_stage2.py extracted/e1/e1_fastload_0801_cf56.bin extracted/e1
python3 tools/analyze_e1_runtime_init.py extracted/e1/e1_unpacked_memory.bin extracted/e1
python3 tools/decode_e1_stage3.py extracted/e1/e1_runtime_memory.bin extracted/e1
python3 tools/finalize_e1_startup.py extracted/e1/e1_stage3_memory.bin extracted/e1
python3 tools/decode_e1_modules.py intake/NEUROMA0.D64 extracted/e1/e1_game_memory.bin extracted/e1/e1_file_a.prg extracted/e1
python3 tools/decode_e1_first_room.py intake/NEUROMA0.D64 intake/NEUROMA1.D64 extracted/e1/e1_new_game_ready_memory.bin extracted/e1
python3 tools/trace_e1_room0.py extracted/e1/e1_room0_ready_memory.bin extracted/e1 --ticks 64
python3 -m unittest tools.test_e1_boot tools.test_e1_fastload tools.test_e1_decode tools.test_e1_runtime_trace
```

## Remaining unknowns

- Confirm the named runtime functions and entity fields with a live VICE trace.
- Catalog every room/module tuple across E2-E4, including write/save paths.
- Decode the `$F248` room record tree and its text compression precisely.
- Identify graphics/sprite packing and produce the first pixel-checked asset set.
- Map side changes and end-to-end state transitions beyond room 0.

## External address references

- [C64 memory map and vectors](https://github.com/mist64/c64ref/blob/master/src/c64mem/c64mem_64map.txt)
- [Buildable 1541 DOS ROM reconstruction](https://github.com/mist64/dos1541)
- [1541 low-level sector-read source](https://github.com/mist64/dos1541/blob/master/lcc.read.s)
