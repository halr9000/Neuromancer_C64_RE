# Repository Guidelines

## Project Structure & Module Organization

- `tools/` contains Python extraction, decoding, disassembly, and analysis scripts; `tools/emu/` contains the 6510 emulator core.
- `tools/test_*.py` holds regression tests for the D64 reader, CPU, boot chain, runtime traces, and E5 text decoding.
- `docs/` contains architecture and binary-format notes. `extracted/e1/` and `extracted/e5/` contain generated binaries, listings, maps, and reports.
- Root Markdown files (`Neuromancer_C64_RE_Intake.md`, `REVERSE.md`, and `dead_ends.md`) record provenance, findings, and rejected approaches. Keep original disk images under `intake/` immutable when present.

## Build, Test, and Development Commands

This repository has no separate build system; use Python 3 from the repository root.

```text
python -m unittest discover -s tools -p "test_*.py"
python -m unittest tools.test_e1_boot tools.test_e1_fastload
python tools/<script>.py --help
```

The first command runs the complete suite, the second runs focused boot-chain tests, and the third shows the arguments for an extraction or analysis script before running it. Generated output should remain in the established `extracted/` directories.

## Coding Style & Naming Conventions

Use four-space indentation, typed Python, `pathlib.Path` for filesystem paths, and `from __future__ import annotations` in new modules. Name functions, variables, and test files with `snake_case`; use `PascalCase` for classes. Prefer small, composable functions, explicit exceptions, and deterministic output. No formatter or linter configuration is currently checked in, so preserve the surrounding style and review imports and type hints manually.

## Testing Guidelines

Tests use the standard-library `unittest` framework. Name files `test_<area>.py`, classes descriptively, and methods `test_<behavior>`. Add regression coverage for newly decoded structures or traces, including stable addresses, lengths, hashes, or state changes where those are part of the evidence. No formal coverage threshold is currently documented.

## Commit & Pull Request Guidelines

No Git history is available in this workspace, so there is no established message convention to follow. Use a short imperative subject (for example, `Document E1 room loader`) and keep each commit focused. Pull requests should explain the evidence or behavior changed, list test commands and results, identify regenerated artifacts and source hashes, and link an issue when applicable. Include emulator screenshots or trace excerpts when they materially support a reverse-engineering claim.

## Provenance & Analysis Practices

Distinguish verified observations from hypotheses in code comments and documentation. Do not patch supplied disk images in place; preserve hashes and retain reproducible extraction steps. Treat generated binaries and reports as derived artifacts, and update the relevant `docs/` or root notes when their interpretation changes.
