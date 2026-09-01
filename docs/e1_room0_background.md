# E1 Room-0 Background Recovery

## Verified path

The VIC-II setup routine at `$4B22` selects bank 0, screen RAM at `$0400`, and
character RAM at `$2000` (`$DD00=$03`, `$D018=$18`). The earlier room-ready
snapshot did not contain an initialized screen. Routine `$633D` is used twice:
first, `$91-$97 = 00 27 00 C0 C0 00 18` expands the side-1 frontend stream at
`$CA00` into the persistent display shell; then the room loader restores the
selected room module at `$CA00` and invokes `$633D` with
`$91-$97 = 01 26 08 78 70 01 0F` to overlay the room scene. Running only the
first decode produced the repetitive tile output previously published by the
web port. Running only the second left the lower shell uninitialized.

`tools/vice_room0_background_probe.mon` reproduces the decode in VICE before
room-0 entity and sprite initialization. It exports the exact buffers consumed
by the browser renderer:

- `e1_room0_screen.bin`: 1000 bytes, SHA-256 `9F308EBEA687B1B460DC60D3800811959B65A6E009E59805ED234884A86C2382`
- `e1_room0_charset.bin`: 2048 bytes, SHA-256 `11DDD2B5FC37B46F0BB91C64BB87D80A2B727602D2F39B256D399AC8503AA1B7`
- `e1_room0_color.bin`: 1000 bytes, SHA-256 `A88E8E6EC1E5B46AAD305B3A4C745CEC5A2B4BB943713591D6753F6B29A5A100`

The checked VICE screenshot is `extracted/e1/e1_vice_room0_background_probe.png`.
It shows a coherent Chatsubo bar frame. The web data generator preserves the
screen and charset bytes and masks color RAM to its low nybble. Canvas draws
each standard-text cell at native 320x200 resolution before overlaying the two
verified room sprites.

## Exact comparison

The complete VICE screenshot is 384x272; its active 320x200 display begins at
pixel `(32,35)`. The enabled sprites use multicolor mode (`$D01C=$FF`) and the
post-initialization `$0840-$08BF` workspace, whose SHA-256 is
`D6B13CCD516ACFC900FF78D83E3D4D304B3EB618341C9E557E81E5653EC6A8EC`.
The VIC positions `(64,88)/(64,109)` map to active-display coordinates
`(40,38)/(40,59)`.

`npm run compare:frame` exports the exact browser compositor buffer, crops the
VICE reference, and writes `e1_vice_room0_active.png`,
`e1_browser_room0.png`, `e1_room0_pixel_diff.png`, and
`e1_room0_pixel_diff.json`. The checked report records 541 mismatched pixels,
all confined to the animated sprite layer; the 40-by-25 character display is
byte-identical to the buffers exported from the same VICE run. Pixel-perfect
sprite timing remains separate from the corrected background decode.
