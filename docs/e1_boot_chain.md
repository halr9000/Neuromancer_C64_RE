# E1 boot and fastloader chain

## Scope

This note describes the verified startup path of the supplied Frontline/GameBase
E1 disk. It corrects the initial interpretation of the 51,794-byte
`NEUROMANCER` directory file as one flat C64 memory image.

The file is started with the ordinary command:

```text
LOAD"NEUROMANCER",8,1
```

There is no BASIC `SYS` stub. Autostart happens while the KERNAL loader is still
reading the file.

## Address transformation

The PRG header declares `$02A7`, but only the first part of the directory stream
uses that address literally.

| Directory-stream bytes | Initial PRG address | Runtime destination | Purpose |
|---|---:|---:|---|
| first two bytes | — | — | PRG load address `$02A7` |
| payload `$02A7-$0329` | `$02A7-$0329` | same | autostart code plus overwritten KERNAL vector |
| payload `$032A-$0569` | nominally `$032A-$0569` | `$C000-$C23F` | drive image, host installer, and C64 client image |
| remaining chain | nominally `$056A+` | destinations encoded in sector records | game/bootstrap payload loaded by the fastloader |

The load-address arithmetic in a naïve PRG extractor is therefore useful only
as a file-offset coordinate after `$0329`; it is not a runtime memory map.

## Autostart through `ISTOP`

The file places `$02A7` in the KERNAL `ISTOP` vector at `$0328-$0329`. Once the
vector has been loaded, the KERNAL's ongoing load reaches the new handler:

1. `$02A7` blanks the display (`$D011=$0B`) and sets the border to dark grey.
2. It changes the low byte of `ISTOP`, making subsequent calls enter `$02BD`.
3. It rewrites the KERNAL load pointer at `$AE-$AF` from the normal destination
   to `$C000`.
4. The loader consequently writes the next 576 bytes to `$C000-$C23F`.
5. `$02BD` waits for `$AE-$AF=$C240`, restores the standard vectors through
   `JSR $FD15`, and transfers to `$C100`.

This makes the file self-starting without placing executable text at a BASIC
program address.

## Host installer at `$C100`

The relocated host stage closes open channels and uploads `$C000-$C0FF` to the
1541's RAM at `$0700-$07FF`. It uses the DOS command channel exactly as follows:

- eight `M-W` commands, each carrying 32 bytes;
- one `M-E` command with entry address `$079F`.

It then copies the 256-byte image at `$C173-$C272` to C64 `$0100-$01FF` and
jumps to `$0100`. Executable client code occupies `$0100-$01B5`; the remaining
bytes are padding.

## 1541 side at `$0700`

The drive image reads linked data sectors directly, validates the decoded block
ID/checksum through 1541 ROM helpers, and sends each byte over a custom
two-bit-at-a-time serial protocol. `$0749` is the byte sender and `$079F` is the
entry installed by `M-E`.

The sector link bytes are part of the protocol rather than discarded:

- byte 0 is the next track, or zero for the final sector;
- byte 1 is the next sector, or the final-sector byte count;
- the first fastloaded sector reserves data bytes 2-3 for a C64 destination;
- linked continuation sectors contribute all 254 data bytes.

For a final sector, the drive increments its count byte before sending it. The
C64 client compensates for that adjustment when calculating the last transfer
length.

## C64 client at `$0100`

`$0100` reconstructs one contiguous destination record from the linked sectors:

| Sector position | Header received | Bytes written |
|---|---|---:|
| first sector | next track, next sector/count, destination low, destination high | up to 252 |
| continuation sector | next track, next sector/count | up to 254 |
| final sector | zero, adjusted count | exact remaining length |

Each data byte is written with the 6510 port set to `$34`, exposing RAM beneath
BASIC, KERNAL, and I/O. The client restores `$01=$37` after every byte. A leading
`$FF` from the drive aborts through the KERNAL reset path.

After the record terminates, the client restores the display and calls standard
KERNAL/BASIC routines before jumping to `$A7B1`.

That next layer is now reconstructed. The first fastload record spans 201
sectors from T13/S12 through T30/S07 and fills `$0801-$CF56`. Its BASIC line
executes `SYS 2051`; `$0803` branches to the Frontline depacker at `$080B`.
Three executed decode/relocation layers reach stable game startup `$03E7`,
which loads file `A`, the hidden raw modules, and engine entry `$4300->$4836`.
The complete continuation, including the first E2 room overlay, is documented
in `docs/architecture_exe.md`.

## Reproduction

```bash
python3 tools/extract_e1.py intake/NEUROMA0.D64 extracted/e1
python3 tools/analyze_e1_boot.py extracted/e1/neuromancer_e1.prg extracted/e1
python3 tools/decode_e1_fastload.py intake/NEUROMA0.D64 extracted/e1
python3 -m unittest tools.test_e1_boot tools.test_e1_fastload tools.test_e1_decode
```

Generated evidence:

- `extracted/e1/e1_bootstrap_runtime_c000.bin`
- `extracted/e1/e1_drive_fastloader_0700.bin`
- `extracted/e1/e1_client_fastloader_0100.bin`
- `extracted/e1/e1_boot_listing.txt`
- `extracted/e1/e1_boot_map.json`
- `extracted/e1/e1_fastload_0801_cf56.bin`
- `extracted/e1/e1_fastload_map.json`
- `docs/architecture_exe.md`

## External address references

- [C64 KERNAL/BASIC memory map and vectors](https://github.com/mist64/c64ref/blob/master/src/c64mem/c64mem_64map.txt)
- [Buildable 1541 DOS ROM reconstruction](https://github.com/mist64/dos1541)
- [1541 low-level sector-read source](https://github.com/mist64/dos1541/blob/master/lcc.read.s)
