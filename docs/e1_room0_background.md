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

## Remaining comparison

The structure and source bytes are verified. A crop-normalized pixel diff
between the VICE active display and browser canvas remains the next graphics
verification step.
