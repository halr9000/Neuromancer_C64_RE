# E1 Cheap Hotel destination assets

## Selection boundary

The verified Chatsubo teardown returns to the Chiba location selector; it does
not automatically load a destination. The opening solution's first recovered
destination link is `CHEAPO`, so this milestone selects room ID 6, Cheap Hotel,
as the first destination for the browser slice. This is a product-route choice
at the verified selector boundary, not a claim that the original executable
forces room 6.

## Verified extraction

`tools/extract_e1_room.py` generalizes the table-driven room-loader process.
For room 6 it reads side 2, track 11, sector 14 from the room tables at
`$FE00/$FE3C/$FE78`, decodes the 4,045-byte module to `$CA00`, copies the
runtime range to `$F000-$FBFF`, and retains the Chiba location overlay selected
from room 0. The room module SHA-256 is
`81b9263440aa2bd8da6a1260f9272955cf0368609f439f2f7beb017f8b902746`.

The generated `extracted/e1/room6/` directory contains the reconstructed 64 KiB
memory image, runtime, location overlay, room logic, decoded map and strings,
terminal metadata, hit regions, screen codes, charset, color RAM, sprite
workspace, VICE log, and native screenshot. Room 6 enables PAX through `$F027`
and has one promoted entity record at `$C430`.

`tools/vice_room6_background_probe.mon` reproduces the two display stages used
by the game: frontend shell decode followed by selected-room decode. It then
runs room initialization and the first sprite-frame transfer before exporting
the native buffers and screenshot.

## Public visual catalog

`tools/build_room_catalog.py` crops the active 320x200 display from the verified
VICE screenshots and emits a deterministic public catalog. The browser presents
Chatsubo and Cheap Hotel with their native frame, decoded location and
description, terminal/entity summary, disk track/sector, and module hash. This
keeps the raw evidence visible while making its meaning readable before the 4x
replacement-art pipeline is introduced.
