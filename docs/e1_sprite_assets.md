# E1 Sprite Assets

## Verified sources

The startup path loads `e1_module_0380.bin` at `$0380-$03FE`. The module is 127
bytes: two 63-byte high-resolution VIC-II sprites followed by one padding byte.
Startup then writes pointers `$0E/$0F` to `$07F8/$07F9`, which address `$0380`
and `$03C0` in VIC bank 0. The extracted shapes are complementary pointer-arrow
sprites.

`e1_module_a400.bin` is exactly 2,176 bytes, or 34 contiguous 64-byte sprite
slots. Each slot contains 63 bytes of MSB-first 24x21 pixel data and a padding
byte. The contact sheet clearly resolves humanoid standing and movement frames.
The first five slots were loaded unchanged at `$0800` in VICE, selected with
sprite pointers `$20-$24`, and rendered in high-resolution mode. Their hardware
pixels match the corresponding extractor output.

## Reproduction

```text
python tools/extract_e1_assets.py extracted/e1/e1_module_0380.bin extracted/e1/assets --scale 4 --sprite-bank extracted/e1/e1_module_a400.bin
```

The command writes individual PNG masks, contact sheets, and JSON provenance
reports under `extracted/e1/assets/`. It uses only the Python standard library.
`tools/vice_startup_sprites.mon` and `tools/vice_a400_sprites.mon` reproduce the
hardware screenshots with VICE 3.10.

## Limits

The PNG exports are one-bit masks rendered white on transparency. Runtime sprite
colors and per-slot multicolor flags are VIC state, not part of these source
modules, and should be attached only after a live gameplay trace identifies the
relevant frame-builder fields. Bytes found at `$07F8-$07FF` in the reconstructed
room snapshot were tested as possible live pointers and rejected: their target
blocks decode as unrelated code/data because that snapshot was captured before
a stable rendered frame.
