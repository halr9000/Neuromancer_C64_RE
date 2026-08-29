# Neuromancer C64 reverse-engineering intake

Date: 2026-08-29

## Scope

This checkpoint records the first read-only inspection of `Neuromancer_C64_EN.zip`. No disk image has been patched. The extracted `.D64` files are working copies; the archive and its hashes are the immutable baseline.

## Source identity

- Archive: `Neuromancer_C64_EN.zip`
- Archive SHA-256: `f95e4c2b39760806f376513eabdc100062330f558be42f30bcd5d1218d9be2a4`
- ZIP integrity: valid; six entries; 875,921 bytes uncompressed
- Package metadata: GameBase entry 5183, English C64 release, marked `Cracked/Crunched: Frontline`
- Game metadata in package: 1988 Electronic Arts / Interplay; programmer Troy A. Miles; music Dave Warhol

### Disk-image hashes

| Image | SHA-256 |
|---|---|
| `NEUROMA0.D64` | `a3deff9c8206173489afdd8c33b537a168ecd16a52a960b94b3cdd4e8f6dc5ad` |
| `NEUROMA1.D64` | `6bf683b9c688e3c999ec46657d18bbcc7268c5538d22440a8280110dcb1c30d0` |
| `NEUROMA2.D64` | `80dbc6e5cba61c2aa8a92196a3b679ef10248d2ba33877461b70a24d9d7c1f51` |
| `NEUROMA3.D64` | `5a2fe7886aafe8dc61e28ff43d56821854bd8c8aa46b37c6f4c635c894e27a1e` |
| `NEUROMA4.D64` | `997bca85c1df3b315222a8c687d5fd46a6caaf847b00f363892b1c1f7731bb26` |

All five images are standard 174,848-byte, 35-track D64 containers without appended error maps.

## Disk roles

| Image | Header marker | Initial classification |
|---|---:|---|
| `NEUROMA0.D64` | `E1` | Boot/runtime side. Contains a deliberately nonstandard directory plus two real PRG chains. |
| `NEUROMA1.D64` | `E2` | Raw game-data side. Track 18/sector 1 is data, not a CBM DOS directory. Contains inventory, skills, body-parts, software, repair, code-word, and related strings. |
| `NEUROMA2.D64` | `E3` | Raw game-data side. Also has a custom sector layout and many strings shared semantically with E2. |
| `NEUROMA3.D64` | `E4` | Raw game-data/cyberspace side. Exposes link codes, passwords, BAMA records, mail/database UI, and cyberspace strings. |
| `NEUROMA4.D64` | none | Frontline documentation disk, not an original E1-E4 game side. DOS directory contains `NEUROMANCER DOX` and `NEUROMANCER SOL`. |

The `E1` through `E4` markers strongly indicate four original logical game sides. The fifth image is crack-package documentation and solution material.

## Boot-side findings

The first directory sector on E1 contains two real PRG entries followed by decorative entries announcing that the version is compatible with the original except for the fastload system.

| Entry | Start T/S | Chain | Payload | Load address | Loaded range |
|---|---:|---:|---:|---:|---:|
| `NEUROMANCER,8,1` | 13/9 | 204 sectors | 51,794 bytes including load address | `$02A7` | `$02A7-$CCF6` |
| `A` | 18/5 | 6 sectors | 1,274 bytes including load address | `$3E00` | `$3E00-$42F7` |

The main file is effectively a large C64 memory image rather than a conventional small BASIC launcher. Its first instructions blank the VIC-II display and alter system vectors/state, consistent with an autostart/bootstrap path. The `A` file begins with a dense byte table and is likely loader support or a data/graphics overlay; its exact role remains unverified.

## Architecture hypothesis

Current evidence supports this provisional model:

1. E1 loads most of the resident 6510 runtime into `$02A7-$CCF6`.
2. The runtime uses custom sector I/O and identifies requested sides using the E1-E4 header markers.
3. E2 and E3 hold physical-world/UI data and overlays in a proprietary layout.
4. E4 holds cyberspace, network, mail, and database content/overlays.
5. E5 is unrelated to the original runtime and can be analyzed separately as crack documentation.

This is a hypothesis, not yet a verified call graph. The next milestone is to locate the E1 disk-read and side-validation routines, then use their sector-addressing logic to decode E2-E4.

## Important provenance caveat

This is not a pristine retail dump. The package explicitly identifies Frontline cracking/crunching, and the E1 directory says the fastload system differs from the original. We can faithfully reverse engineer this supplied build, but a byte-faithful reconstruction of the retail loader or copy protection will require an unmodified preservation image. Game logic and data may still be largely intact, but that must be verified rather than assumed.

## Next tasks

- Extract both E1 PRG chains with reproducible tooling and hashes.
- Build the C64 6510 opcode table and address-aware disassembler.
- Identify the autostart transfer point, reset/IRQ vectors, and resident memory regions.
- Find calls into KERNAL/drive I/O and the E1-E4 side-check routine.
- Convert custom sector reads into named overlay/data ranges.
- Decode text, tables, graphics, and music into catalogs with source offsets.
- Validate static findings against a cycle-accurate C64 emulator before changing any interpretation from provisional to verified.

## Open project decision

Choose the primary target before the implementation phase branches:

1. Faithful analysis and web-port-ready documentation of this exact Frontline build.
2. Retail-faithful analysis, using this build provisionally while obtaining a pristine dump for loader/protection comparison.
3. Data/mechanics extraction first, deferring a complete executable reconstruction.

