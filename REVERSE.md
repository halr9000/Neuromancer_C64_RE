# Neuromancer (Commodore 64) — Reverse Engineering Notes

## Binary Identification

| Field | Value |
|---|---|
| Source archive | `Neuromancer_C64_EN.zip` |
| Format | Five 35-track D64 images; 174,848 bytes each; no error maps |
| Platform | Commodore 64 |
| CPU | MOS 6510 |
| Canonical build | Supplied Frontline/GameBase cracked build |
| Game sides | `NEUROMA0.D64`-`NEUROMA3.D64`, marked E1-E4 |
| Auxiliary disk | `NEUROMA4.D64`, Frontline DOX and solution programs |
| Boot entry | `LOAD"NEUROMANCER",8,1`; autostart through `ISTOP` at `$0328-$0329` |

The immutable hashes and intake details are recorded in `Neuromancer_C64_RE_Intake.md`.

---

## Memory Map

| Address Range | Purpose |
|---|---|
| `$0000-$00FF` | Zero page; `$0000-$0001` include the 6510 data-direction/I/O port |
| `$0100-$01FF` | Hardware stack; temporarily replaced by the E1 C64 fastloader client |
| `$0200-$03FF` | OS workspace, buffers, and vectors; E1 initially loads `$02A7-$0329` here |
| `$0400-$07E7` | Default text screen RAM |
| `$0800-$9FFF` | General RAM / BASIC program area when ROM is mapped out or unused |
| `$A000-$BFFF` | BASIC ROM or underlying RAM |
| `$C000-$C23F` | Redirected E1 bootstrap: drive image, host installer, and client source |
| `$C240-$CFFF` | RAM |
| `$D000-$DFFF` | VIC-II/SID/CIA/color RAM/I/O, character ROM, or underlying RAM depending on banking |
| `$E000-$FFFF` | KERNAL ROM or underlying RAM |

---

## Data-Range Map

| Start | End | Size | Classification | Notes |
|---|---|---:|---|---|
| E1 `T13/S09` chain | E1 `T30/S07` | 51,794-byte PRG | Hybrid autostart/fastload stream | Declares `$02A7`; only the initial bytes load literally, then the stream redirects to `$C000` and framed destinations |
| E1 `T18/S05` chain | E1 `T18/S10` | 1,274-byte PRG | Runtime raw-sector driver | File `A`; loads `$3E00-$42F7`, installs hidden T18/S02 drive code |
| E2 full image | — | 174,848 | Custom raw-sector game data | DOS directory interpretation is invalid |
| E3 full image | — | 174,848 | Custom raw-sector game data | DOS directory interpretation is invalid |
| E4 full image | — | 174,848 | Custom raw-sector cyberspace/database data | DOS directory interpretation is invalid |
| E5 `T17/S00` chain | — | 5,577-byte PRG | Frontline documentation viewer | `NEUROMANCER DOX`, load `$0801` |
| E5 `T19/S00` chain | — | 22,655-byte PRG | Frontline solution viewer | `NEUROMANCER SOL`, load `$0801` |

---

## Key Findings

### Architecture

- **Verified:** E1 contains two valid PRG chains and a decorative crack directory.
- **Verified:** the main E1 PRG is not a flat resident image. Its `$02A7` handler replaces the KERNAL `ISTOP` vector, redirects the load pointer at `$AE-$AF` to `$C000`, and transfers when that pointer reaches `$C240`.
- **Verified:** directory-stream bytes associated with nominal PRG addresses `$032A-$0569` become runtime `$C000-$C23F`; `$C100` uploads a 256-byte 1541 fastloader to `$0700-$07FF` with eight `M-W` commands and starts `$079F` with `M-E`.
- **Verified:** the host copies a C64 receiver from `$C173-$C272` to `$0100-$01FF`. Its executable portion at `$0100-$01B5` reconstructs destination-addressed records from linked sectors and writes with RAM exposed beneath ROM/I/O.
- **Verified:** `tools/extract_e1.py`, `tools/analyze_e1_boot.py`, and `tools/test_e1_boot.py` reproduce and validate the E1 bootstrap layers; `docs/e1_boot_chain.md` documents the transformation and protocol.
- **Verified:** the first fastload record begins at T13/S12, ends at T30/S07, spans 201 sectors, and reconstructs 51,030 bytes at `$0801-$CF56`.
- **Verified:** BASIC line 1744 executes `SYS 2051`; `$0803` branches to the Frontline bootstrap at `$080B`.
- **Verified:** executed decode/relocation stages reach `$080D`, then `$008E`, then `$020A`, and finally the stable game startup at `$03E7`.
- **Verified:** `$03E7` loads file `A` at `$3E00-$42F7`; its `$400E` entry installs/executes hidden 1541 code from T18/S02 and `$4011` reads length-prefixed raw-sector modules.
- **Verified:** initial E1 modules assemble the core at `$4300-$73FC`, room-side tables beneath KERNAL at `$FE00-$FFFC`, state at `$C100`, and several low/high-memory overlays. `$4300` is a 55-entry jump table whose first vector enters `$4836`.
- **Verified:** `$4BEC` validates disk side by reading T18/S00 byte `$DC`. E1-E4 hold ASCII `1`-`4`; E2-E4 are raw overlay/data sides, not DOS filesystems.
- **Verified:** new-game room ID 0 selects E2 T01/S17 at `$AC80` and E2 T06/S00 at `$CA00`; `$6158` copies `$CA00-$D5FF` to room runtime `$F000-$FBFF`.
- **Verified:** room 0 exposes initialize/tick/teardown vectors at `$F00A/$F00D/$F010`; the recurring engine loop begins at `$488D`.
- **Verified (deterministic 6510 trace):** the reconstructed room-0 snapshot executes `$F00A -> $F0F6` in 13 instructions, changing `$03/$07/$14/$18` to `$22/$24/$33/$42`; 64 calls through `$F00D -> $F10E` execute 1,276 instructions and exercise the counter-driven tick branches; `$F010 -> $F10D` returns in two instructions. The checked final memory hash is `f1006c2fa4c38ca6b6836d8a547f55b2779dc84c7ef65ddd077fcc912eff9387`.
- **Verified (bounded dispatcher trace):** `$6429` first saves room-data root `$F248` through `$6C8C`, then uses a self-modified `LDX #$03` operand at `$6438` to inspect four status bytes `$9D-$A0`; a controlled all-`$FF` high-bit-inactive run returns in 24 instructions without entering any script handler. The supplied room snapshot has all four corresponding status bytes clear, so its real scripts still require hardware-accurate tracing before their field semantics are claimed.
- **Verified:** `docs/architecture_exe.md` records the executable architecture, complete initial module map, first-room reconstruction, and current core-function labels.
- **Environment finding:** no VICE/x64 executable is present in this workspace. The next checkpoint uses the project 6510 core against the reconstructed room-0 snapshot; it is deterministic execution evidence, but does not replace a future hardware-accurate VICE capture.
- **Decision:** after the E5 documentation spike, proceed with option 1: faithfully analyze and document this exact Frontline build with a web port as the long-term target.

### E5 Documentation Disk

- **Verified:** E5 has a normal DOS directory with `NEUROMANCER DOX` and `NEUROMANCER SOL`.
- **Verified:** both files are `$0801` PRGs with a one-line BASIC `SYS` launcher followed by native 6510 viewer/depacker code and encoded payload.
- **Verified:** `NEUROMANCER DOX` is 5,577 bytes over 22 sectors and has SHA-256 `912fc7a88771f662f8ba3527fc85549893182e5246f34d6b118cf72143eb00bc`.
- **Verified:** `NEUROMANCER SOL` is 22,655 bytes over 90 sectors and has SHA-256 `c6eeb3149b548cf40b90d4945dacc91151a1b12683df4349085f2f1f0cb3367e`.
- **Verified:** `tools/d64.py` and `tools/extract_e5.py` reproduce the extraction; `tools/test_d64.py` checks geometry, directory names, chain lengths, payload sizes, and load addresses.
- **Verified:** DOX uses nested relocation, backwards LZ-style expansion, and a final backwards RLE stage. The project 6502 core reaches final viewer entry `$0A00` after 1,119,310 instructions.
- **Verified:** DOX stores 11 fixed 40x25 screen-code pages from `$1000` through `$3BE7`; `$0D06=$3C` is the exclusive page limit.
- **Verified:** solution routine `$CE50` entropy-decodes 22,051 bytes, then an outer `$F3` RLE layer expands the result to 34,285 bytes at `$0801-$8DED`.
- **Verified:** the solution's PETSCII/control replay begins at `$2800` and terminates with `$8C` at `$8DED`.
- **Verified:** the solution export models C64 one-/two-row logical lines plus INSERT and DELETE; it yields 11 sections and retains both the terminal replay and a six-repair readable transcription.
- **Verified:** readable exports and JSON address/provenance maps exist under `extracted/e5/`; the format is documented in `docs/e5_dox_format.md`.

### Data Structures

- **Raw module:** first-sector bytes 0-1 are a little-endian payload length; bytes 2-255 are the first 254 payload bytes; continuation sectors contribute 256 bytes each.
- **Room disk arrays:** `$FE00+room` is track, `$FE3C+room` is sector, and `$FE78+room` is the ASCII side number while KERNAL ROM is banked out.
- **Location overlay arrays:** `$62C5` stores room IDs; parallel `$62E3` and `$6301` arrays store track and sector. Index below `$13` selects side 2; later entries select side 3.
- **Entity slots:** `$C400 + index*8` holds a candidate entity record; offsets 6-7 point to its current script record. `$6429` uses four status-controlled slots and dispatches qualifying records through an opcode table.
- **Entity dispatch status:** `$9D-$A0` are four high-bit-tested slot-status bytes. `$6429` processes slot 0 before its self-modified loop visits 3, 2, and 1; a set high bit skips the script handler.
- **Room ABI:** `$F002-$F003` point to the room data root; `$F00A`, `$F00D`, and `$F010` are initialize, tick, and teardown vectors installed from the `$CA00` staging module.

### State Machine

- `$03E7` asks `OLD OR NEW GAME? (O/N)`.
- New game collects a player name and loads state template T04/S01 to `$C100`.
- Old game collects slot 1-4 and loads T04/S07, T04/S16, T05/S04, or T05/S13 to `$C100`.
- `$4836` initializes the engine; `$6158` selects cross-side room overlays from the state room ID, installs room code at `$F000`, and returns to the `$488D` tick loop.
- Each tick dispatches entity scripts (`$6429`), invokes the room tick vector (`$F00D`), builds the sprite frame (`$5B1E`), and updates input/UI state.

---

## Intermediate Output Files

| File | Contents |
|---|---|
| `Neuromancer_C64_RE_Intake.md` | Hashes, image roles, boot-chain intake |
| `extracted/e1/manifest.json` | E1 PRG hashes and complete directory-sector chains |
| `extracted/e1/neuromancer_e1.prg` | Raw 51,794-byte E1 directory stream |
| `extracted/e1/e1_file_a.prg` | Raw auxiliary `A` PRG |
| `extracted/e1/e1_bootstrap_runtime_c000.bin` | Reconstructed 576-byte `$C000-$C23F` stage |
| `extracted/e1/e1_drive_fastloader_0700.bin` | Uploaded 1541 `$0700-$07FF` image |
| `extracted/e1/e1_client_fastloader_0100.bin` | Executable C64 receiver `$0100-$01B5` |
| `extracted/e1/e1_boot_listing.txt` | Context-aware disassembly of all boot layers |
| `extracted/e1/e1_boot_map.json` | Machine-readable mappings, hashes, and entries |
| `docs/e1_boot_chain.md` | E1 autostart address transform and sector-record protocol |
| `extracted/e1/e1_fastload_0801_cf56.bin` | Reconstructed first fastload record at `$0801-$CF56` |
| `extracted/e1/e1_fastload_map.json` | Fastload sector provenance, launcher fields, ranges, and hash |
| `extracted/e1/e1_unpacked_memory.bin` | 64 KiB snapshot at depacker handoff `$080D` |
| `extracted/e1/e1_runtime_memory.bin` | Snapshot at zero-page decoder entry `$008E` |
| `extracted/e1/e1_stage3_memory.bin` | Snapshot at final self-erasing stub `$020A` |
| `extracted/e1/e1_game_memory.bin` | Stable pre-loader game snapshot at `$03E7` |
| `extracted/e1/e1_module_map.json` | Initial hidden E1 module ranges, sectors, hashes and state slots |
| `extracted/e1/e1_new_game_ready_memory.bin` | Initial new-game modules overlaid before `$4300` |
| `extracted/e1/e1_room0_map.json` | Cross-side derivation and hashes for the first playable room |
| `extracted/e1/e1_room0_ready_memory.bin` | Room-0 runtime assembled through `$F000-$FBFF` |
| `extracted/e1/e1_room0_runtime_listing.txt` | Labeled room vectors, animation tick, and room-data root |
| `extracted/e1/e1_room0_vector_trace.json` | Machine-readable 64-tick deterministic execution report |
| `extracted/e1/e1_room0_vector_trace.md` | Readable room-vector state-change timeline |
| `docs/architecture_exe.md` | Executable architecture from `LOAD` through first-room runtime |
| `extracted/e5/manifest.json` | E5 source hash, PRG hashes, and complete sector-chain provenance |
| `extracted/e5/neuromancer_dox.prg` | Raw extracted DOX PRG |
| `extracted/e5/neuromancer_sol.prg` | Raw extracted solution PRG |
| `extracted/e5/neuromancer_dox_readable.txt` | 11 decoded fixed-screen hint pages |
| `extracted/e5/neuromancer_solution_terminal_replay.txt` | Unedited C64 screen-editor replay |
| `extracted/e5/neuromancer_solution_readable.txt` | Six-repair readable walkthrough transcription |
| `extracted/e5/e5_readable_map.json` | Readable-output source ranges and control statistics |
| `docs/e5_dox_format.md` | Both viewer/depacker formats and reproduction commands |

---

## Verification Checklist

- [x] Ph3: execute and regression-test room-0 initialize, tick, and teardown vectors with the project 6510 core
- [ ] Ph3: cross-check the three room-vector traces against a hardware-accurate VICE capture
- [ ] Ph4: 5+ sprites/tiles extracted and visually compared to emulator
- [ ] Ph5: key data struct confirmed in emulator memory dump, all fields match
- [ ] Ph6: full game session played, no major logic gaps found
- [ ] Ph7: web port pixel-compared against emulator screenshots

---

## Reference Resources

- `Neuromancer_C64_RE_Intake.md`
- `intake/VERSION.NFO`
- [C64 memory map and vectors](https://github.com/mist64/c64ref/blob/master/src/c64mem/c64mem_64map.txt)
- [1541 DOS ROM reconstruction](https://github.com/mist64/dos1541)

---

## Next Tasks

### RE Investigation

- [x] E5 spike: extract both PRGs and decode their documentation payloads to readable text
- [x] E5 spike: document viewer/depacker layout and retain raw/source offsets
- [x] Ph3: extract the E1 PRGs reproducibly and build the 6510 opcode database/disassembler
- [x] Ph3: locate and trace the E1 autostart transfer point
- [x] Ph3: reconstruct the E1 fastloader sector stream into destination-addressed memory ranges
- [x] Ph3: locate the final game entry point and identify the first major runtime modules
- [x] Ph3: identify E1 disk-sector I/O and E1-E4 side-validation routines
- [x] Ph3: deterministically execute room-0 initialize, tick, and teardown vectors
- [ ] Ph3: live-trace the named main-loop routines and confirm entity fields in VICE
- [ ] Ph3: catalog all E2-E4 room/module tuples and side transitions
- [ ] Ph4: extract and pixel-check the first sprite/tile set

### Web Port Fixes

### Documentation

- [x] Create `docs/architecture_exe.md` once the resident architecture is mapped
- [ ] Create `docs/architecture_web.md` before implementation of the web port

SESSION_SUMMARY: E5 is fully readable; E1 is reconstructed from LOAD through stable startup `$03E7`, hidden module assembly, engine `$4836`, and the first cross-side room runtime at `$F000`.
