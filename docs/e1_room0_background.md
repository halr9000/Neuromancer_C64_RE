# E1 Room-0 Background Recovery

## Verified path

The VIC-II setup routine at `$4B22` selects bank 0, screen RAM at `$0400`, and
character RAM at `$2000` (`$DD00=$03`, `$D018=$18`). The earlier room-ready
snapshot did not contain an initialized screen. Routine `$633D` is the missing
frontend decoder: with `$91-$97 = 00 27 00 C0 C0 00 18`, it expands the side-1
frontend stream at `$CA00` into screen RAM and color RAM.

`tools/vice_room0_background_probe.mon` reproduces the decode in VICE before
room-0 entity and sprite initialization. It exports the exact buffers consumed
by the browser renderer:

- `e1_room0_screen.bin`: 1000 bytes, SHA-256 `2B96F5BB67AEB10806D6506CF2D306E798EEBE054563B9B7CBAAA66832AFD05D`
- `e1_room0_charset.bin`: 2048 bytes, SHA-256 `D557BF10B0037D946C78978983C24D7F264CEC65B3CC173916C32D95AA759707`
- `e1_room0_color.bin`: 1000 bytes, SHA-256 `E27A4B66BDDFA8AD0D8CF69BBC764CF5DC3B38A9CE838CFC46236FF9DBB5FF66`

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
`e1_room0_pixel_diff.json`. The checked report records zero mismatched pixels,
zero mismatched channels, and a maximum channel delta of zero across all
64,000 pixels.
