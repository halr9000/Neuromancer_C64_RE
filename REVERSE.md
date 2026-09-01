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
- **Verified (VICE entity initialization):** the post-overlay scan at `$621B-$628B` activates room-0 record `$C400`: offset 5 changes `$FF->$00`, offsets 6-7 become script pointer `$F02D`, and packed byte `$C1` selects status slot 1 (`$9E=$00`). Slots 0, 2, and 3 remain `$FF`. Dispatch resolves slot 1 to `$C400/$F02D`, reads opcode `$01`, and selects handler `$64B5`; running that UI-bearing handler in isolation still blocks without the rest of the live frame state.
- **Verified (entity-table bound):** the `$C400` record list reaches its first negative sentinel at `$C518` (record index 35). `$C400` is the only room-ID-0 record before that sentinel. The loader's prerequisite `$9D-$A0=$FF` reset is therefore required for a faithful isolated scan: it reactivates only slot 1 and keeps slots 0, 2, and 3 inactive.
- **Verified (VICE sprite-frame data flow):** after that record scan, `$5B1E` copies the six four-slot arrays into `$5E01-$5E18`, depth-sorts them, and emits the hardware-frame workspace at `$5E19-$5E34`. Room-0 record values `$14/$22/$29` flow through the active slot into the builder output, and the routine returns in 13,772 VICE cycles. See `docs/e1_entity_records.md`; exact gameplay coordinate/color names remain provisional until paired with a live screenshot.
- **Verified (VICE VIC transfer and field names):** the complete post-overlay path (`$621B-$6297`) reaches its first initialized sprite frame in 192,477 cycles. The real IRQ transfer loop `$4D46-$4D7E` then enables sprites 1-2 at `(64,88)` and `(64,109)`, pointers `$21/$22`, colors `$9/$2`. This confirms `$0A` as logical X (rendered as `(X+$0C)*2`), `$0E` as logical Y (rendered as `Y+$36`), `$12` as packed primary/secondary color nibbles, `$02/$06` as primary/secondary frame-source values, and `$16` as packed render flags. The screen/background RAM in this reconstructed snapshot is not a complete gameplay scene, so the capture proves entity/VIC fields rather than final room composition.
- **Verified (room text format):** `$F248` begins with a 60-byte decode dictionary; `$6D0E` treats `$F284` (`root+$3C`) as a relative-pointer table. Each little-endian pointer selects one group of four NUL-terminated strings, while an input string ID's low two bits select which string in that group. `$6D4E` reads packed 5-bit tokens LSB-first; token `$1E` uppercases the next lowercase dictionary character and `$1F` extends the next token by `$1E`. The room-0 tree contains 33 valid strings (`$00-$20`); `tools/decode_e1_room_text.py` reproduces them, and the original `$6C8C/$6CBC` path in VICE decodes ID `$01` to `In the Chatsubo Bar.` at `$E700`.
- **Verified (VICE main-loop entry):** a bounded iteration from `$488D` clears transient bytes `$90/$CB` and reaches entity dispatcher `$6429` in 25 hardware cycles with a balanced synthetic caller frame. The remainder of the real iteration is blocked specifically inside opcode-1 handler `$64B5`, whose UI/input dependencies require a later full-frame capture.
- **Verified (opcode-1 handler stages):** handler `$64B5` completes `$6CBC` after 113,577 VICE cycles and `$BCDC` after 406,888 cumulative cycles. `$5933` is an input-release handshake; setting its alternate-path flag `$3D!=0` clears the flag and returns. `$BCDC` derives `$BEF8/$BEF9 = $28/$05` before the final `$BE89` screen/sprite rebuild. The isolated VICE process does not reach the post-`$BE89` checkpoint, so that final dependency remains unresolved rather than attributed to zero counters.
- **Verified (VICE 3.10):** `tools/vice_room0_probe.mon` loads the reconstructed snapshot into the RAM bank, restores processor-port DDR `$00=$2F`, selects RAM-under-ROM with `$01=$35`, and executes `$F00A` to a synthetic `$0400` return. The hardware-accurate core changes `$03/$07/$14/$18` to `$22/$24/$33/$42`, exactly matching the deterministic project-6510 trace; the VICE monitor reports 43 cycles at the return. Restoring `$00` is essential because setting `$01` alone leaves the reset-time input pins effective and executes KERNAL ROM instead.
- **Verified (VICE 64-tick room trace):** `tools/vice_room0_64tick_probe.mon` executes initialize, exactly 64 tick calls, and teardown in one 6510 harness. VICE finishes with `$03/$04/$07/$08/$0C/$10/$14/$18 = $23/$3E/$27/$3E/$97/$28/$33/$42` and `$F17B-$F180 = $00/$04/$23/$11/$05/$F5`, exactly matching frame 64 of the deterministic trace. The combined harness reaches its sentinel in 5,833 hardware cycles.
- **Verified:** the E1 room table contains 60 slots: 56 valid room modules and four empty entries (`42`, `47`, `58`, and `59`). Valid room modules select 29 E2 records and 27 E3 records; the table-order side runs are E2 rooms `0-19`, E3 `20-21`, E2 `22-28`, E3 `29`, E2 `30-31`, and E3 `32-57`.
- **Verified:** the E1 location table contains 30 overlay tuples. Indices `$00-$12` select 19 E2 overlays and `$13-$1D` select 11 E3 overlays. E4's side marker is valid, but E1's room and location tables select no E4 module in this catalog.
- **Verified:** `docs/architecture_exe.md` records the executable architecture, complete initial module map, first-room reconstruction, and current core-function labels.
- **Decision:** `docs/architecture_web.md` maps verified executable boundaries to a headless-testable browser runtime. The first implementation target is a vertically integrated room-0 slice; planned UI, save, game-over, and audio behavior remains explicitly provisional until traced.
- **Verified (first web runtime):** `web/systems/room0.ts` ports `$F0F6/$F10E` as typed, table-driven room hooks rather than emulating 6510 instructions. Its headless golden test starts from the reconstructed snapshot values and matches the verified post-init and 64-tick entity fields and animation counters exactly.
- **Verified (web data boundary):** `tools/build_web_data.py` deterministically converts the checked room-0 snapshot and text report into schema-versioned `web/public/generated/room0.json`. `web/data/game-data.ts` validates the schema and byte ranges before exposing all 33 strings and the `$C400` entity record, retaining its original bytes beside promoted slot, position, color, and flag fields.
- **Verified (visible web slice):** `web/index.html` connects the room-0 data and tick runtime to a native 320x200 Canvas 2D frame. The generated artifact carries the recovered 40x25 screen, 2 KiB charset, color RAM, and VIC pointers `$21/$22`; the renderer draws the decoded Chatsubo frame and places the sprites at captured coordinates `(64,88)/(64,109)` with colors `$9/$2`. Browser inspection confirms the coherent frame renders without a current console error. Exact emulator-to-browser pixel comparison remains open.
- **Verified (opening PAX/payment route):** room 0 enters the side-1 PAX shell at T12/S03. Its bank child at T17/S14 transfers 40 from bank to cash (`6/2000 -> 46/1960`); its send-message child at T34/S00 applies a one-shot `$002710` Armitage deposit after the BAMA response; and resident GIVE `$68A8-$68C4` debits Ratz's 46 credits to leave cash zero. The project CPU and VICE agree byte-for-byte on these balances. `$F0DA` is the conditional refund hook, `$F10D` is the no-op room teardown, and leaving returns to the Chiba selector rather than automatically loading a destination room. See `docs/e1_opening_route.md`.
- **Verified (room-0 background recovery):** `$4B22` confirms VIC shadows `$D018=$18`, `$DD00=$03`, selecting screen `$0400`, charset `$2000`, and sprite-pointer space in bank 0. The ready snapshot still held the erased startup stub at `$0400`; `$633D` was the missing stage. With `$91-$97 = $00/$27/$00/$C0/$C0/$00/$18`, it expands `e1_side1_frontend_ca00.bin` first into `$0400` screen RAM and then `$D800` color RAM. `tools/vice_room0_background_probe.mon` runs that decoder before room/entity initialization and produces the first coherent bar frame; the earlier noisy capture is rejected as uninitialized screen/color evidence.
- **Verified (exact room-0 frame):** the VICE 384x272 screenshot's active display is `$320x200` at crop `(32,35)`. `$D01C=$FF` makes the two enabled room sprites multicolor, and their post-initialization `$0840-$08BF` workspace differs from the pre-room snapshot. The browser now preserves two-bit sprite pixels, shared colors, VIC-to-active-display offsets `(-24,-50)`, and the capture's RGB palette. `npm run compare:frame` reports zero mismatched pixels and retains normalized reference, browser, diff, and JSON evidence under `extracted/e1/`.
- **Environment finding (2026-08-29):** VICE 3.10 GTK3 is installed through Winget (`VICE-Team.VICE.GTK3`), including `x64sc`, `c1541`, and `petcat`. The first scripted hardware-accurate room-vector capture is checked in at `extracted/e1/e1_vice_room0_probe.log`; tick/dispatcher tracing remains open.
- **Verified (first sprite assets):** the 127-byte module loaded at `$0380-$03FE` contains two 63-byte, MSB-first, high-resolution VIC-II sprites plus one padding byte. Startup writes pointers `$0E/$0F` to `$07F8/$07F9`; `tools/extract_e1_assets.py` reproducibly exports both 24x21 masks and their combined sheet under `extracted/e1/assets/`. The shapes are complementary pointer-arrow sprites with 58 and 53 set pixels.
- **Verified (sprite bank and VICE pixel check):** `e1_module_a400.bin` is 34 contiguous 64-byte sprite slots. Its contact sheet resolves humanoid standing/movement frames; VICE 3.10 renders the first five unchanged slots at native 24x21 high-resolution geometry with pixels matching the extractor masks. See `docs/e1_sprite_assets.md` and `extracted/e1/assets/vice_a400_sprites.png`. The apparent `$07F8-$07FF` pointers in the pre-frame room snapshot were rejected after their targets decoded as unrelated code/data.
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
- **Entity slots:** `$C400 + index*8` holds a room entity record: offset 0 is room ID; offset 1 combines actor flags with the low-two-bit active slot index; offsets 2-4 seed the slot's `$0A/$0E/$12` render fields; offset 5 is initialized from `$FF` to `$00` when first activated; offsets 6-7 point to the current script opcode record. `$6429` uses four status-controlled slots and dispatches qualifying records through an opcode table.
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
| `extracted/e1/e1_data_catalog.json` | All E1-selected room and location-overlay tuples across E2-E4, with decoded lengths, sector chains, hashes, and side runs |
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
- [x] Ph3: cross-check the three room-vector traces against a hardware-accurate VICE capture
- [x] Ph4: 5+ sprites/tiles extracted and visually compared to emulator
- [ ] Ph5: key data struct confirmed in emulator memory dump, all fields match
- [ ] Ph6: full game session played, no major logic gaps found
- [x] Ph7: web port pixel-compared against emulator screenshots

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
- [x] Ph3: catalog E1-selected room/module tuples and side transitions across E2-E4
- [x] Ph3: live-trace the named main-loop routines and confirm entity fields in VICE
- [x] Ph4: extract and pixel-check the first sprite/tile set

### Web Port Fixes

### Documentation

- [x] Create `docs/architecture_exe.md` once the resident architecture is mapped
- [x] Create `docs/architecture_web.md` before implementation of the web port

### Web port

- [x] Port the room-0 initialize and tick hooks and match the 64-tick trace
- [x] Load decoded room-0 text and entity data through a versioned game-data boundary
- [x] Render the verified room-0 actor frame at native 320x200 coordinates
- [x] Recover room-0 screen, character, and color RAM for a real Chatsubo background
- [x] Pixel-compare the reconstructed browser room against a complete VICE capture
- [x] Trace the Chatsubo/PAX/payment/exit opening route through the Chiba selector boundary in VICE

SESSION_SUMMARY: Room 0 now matches a normalized VICE frame exactly at all 64,000 pixels; the next milestone is the complete opening-route trace.
