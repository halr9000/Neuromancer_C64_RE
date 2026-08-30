# E1-selected room and location catalog

## Scope

This catalog decodes the raw-sector modules selected by the E1 resident
snapshot. It covers the room tables at `$FE00/$FE3C/$FE78` and the location
overlay tables at `$62C5/$62E3/$6301`; it does not claim to be a complete
catalog of every raw sector on E2-E4.

The source snapshot is
`extracted/e1/e1_new_game_ready_memory.bin`, and the machine-readable result
is `extracted/e1/e1_data_catalog.json`. Each valid tuple is decoded using the
length prefix in its first sector. The report retains the full sequential
sector chain and decoded-payload SHA-256.

## Room modules

The room table has 60 slots. Four slots are empty: room indices `42`, `47`,
`58`, and `59`. The remaining 56 entries select modules loaded to `$CA00`
before the runtime copy to `$F000`.

| Table-order room run | Side | Valid modules | Interpretation |
|---|---:|---:|---|
| 0-19 | E2 | 20 | E2 room data |
| 20-21 | E3 | 2 | E3 room data |
| 22-28 | E2 | 7 | E2 room data |
| 29 | E3 | 1 | E3 room data |
| 30-31 | E2 | 2 | E2 room data |
| 32-57 | E3 | 24 | E3 room data |

These are side runs in table order. They identify changes in the side byte
associated with room records; they are not, by themselves, a trace of the
player's runtime navigation or a proof that adjacent room IDs are visited in
that order.

## Location overlays

The 30-entry location table selects overlays loaded to `$AC80`:

- indices `$00-$12`: 19 E2 overlays;
- indices `$13-$1D`: 11 E3 overlays.

The first overlay is room ID `0` at E2 `T01/S17`, with a 1,856-byte decoded
payload. Room ID `45` at E3 `T02/S02` has a 1,024-byte payload. The remaining
entries and their sector provenance are in `e1_data_catalog.json`.

## E4 boundary

The E3 and E4 source images both pass the side-marker check at `T18/S00`,
offset `$DC`: the marker bytes are ASCII `3` and `4`, respectively. Neither
E1 table selects an E4 module, so E4 remains an open area for tracing other
loader call sites and cyberspace/database transitions.

## Reproduction

From the repository root, run:

```text
python tools/catalog_e1_data.py \
  extracted/e1/e1_new_game_ready_memory.bin \
  intake/NEUROMA1.D64 intake/NEUROMA2.D64 intake/NEUROMA3.D64 \
  extracted/e1/e1_data_catalog.json
```

The catalog is derived data; the original D64 images under `intake/` remain
unchanged.
