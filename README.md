# Neuromancer C64 Web Port

This project aims to produce a functional browser-based port of the Commodore 64 version of *Neuromancer* (1988, Electronic Arts/Interplay). Reverse engineering is the foundation for recreating the original game logic, data, presentation, and interaction in a web runtime—not the final deliverable.

The target is the supplied English Frontline/GameBase build: a cracked/crunched release whose loader differs from a pristine retail disk. The port should faithfully reproduce this build’s playable experience while keeping the original disk images and derived evidence traceable.

## What is here

- `tools/` — Python 3 extraction, decoding, disassembly, and a small 6510 emulator.
- `web/` — headless TypeScript game systems, beginning with the verified room-0 lifecycle.
- `docs/` — boot-chain, executable-architecture, and E5 documentation-format notes.
- `extracted/e1/` — reconstructed boot/runtime layers and the first-room snapshot.
- `extracted/e5/` — decoded documentation and solution-disk exports.
- `REVERSE.md` — consolidated findings, memory maps, evidence, and open work.
- `Neuromancer_C64_RE_Intake.md` — source identity, hashes, disk roles, and provenance.

The repository now bridges its reverse-engineering foundation into a headless
browser runtime: stable game startup and room-0 traces are reconstructed, and
the first TypeScript room hook reproduces the verified 64-tick state. Rendering,
input, complete room/data cataloging, and a full playable session remain open.

## Port roadmap

1. Complete the executable, room, graphics, text, input, and state-data maps.
2. Implement the game loop and browser-facing systems from verified behavior.
3. Recreate the C64 presentation and controls, then compare browser output against emulator captures.
4. Exercise a complete playable session and document any intentional differences.

## Source disk images

The repository does not redistribute the source package. Obtain `Neuromancer_C64_EN.zip` from the [My Abandonware Neuromancer page](https://www.myabandonware.com/game/neuromancer-pt), or use a legally obtained copy. The supplied archive contains five standard 35-track D64 images and `VERSION.NFO`.

From the repository root, extract the archive into `intake/`:

```text
python -m zipfile -e C:\path\to\Neuromancer_C64_EN.zip intake
```

The expected files are `NEUROMA0.D64` through `NEUROMA4.D64`. Verify the archive SHA-256 against `Neuromancer_C64_RE_Intake.md` before analysis; keep the original images unchanged.

## Reproduce the analysis

```text
python -m unittest discover -s tools -p "test_*.py"
python tools/extract_e1.py intake/NEUROMA0.D64 extracted/e1
python tools/extract_e5.py intake/NEUROMA4.D64 extracted/e5
```

The test suite uses Python’s standard `unittest` library. Extraction commands regenerate derived artifacts; review their hashes and update the relevant documentation when interpretations change.

The headless browser-port checks use Node.js and TypeScript:

```text
npm install
npm run build:data
npm run typecheck
npm run test:web
```

## Contributing

Separate verified observations from hypotheses, preserve source offsets and hashes, and include reproducible commands with new findings. Port code should be kept distinct from extraction tooling and should link implementation decisions to verified traces or documented evidence. See [AGENTS.md](AGENTS.md) for contributor conventions and [REVERSE.md](REVERSE.md) for the technical roadmap.
