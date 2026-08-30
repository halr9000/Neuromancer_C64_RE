# E1 Room Text

Room 0 stores its text tree at `$F248`. The checked-in decoder exports all 33
valid Chatsubo strings as JSON and plain text. IDs `$00-$20` are verified;
interpreting `$21` as another string crosses into the next packed structure.

## Format

`$6D0E` divides the room-text root into a 60-byte dictionary and a relative
pointer table at `root+$3C`. Each little-endian pointer selects a packed group
of four strings. The high six bits of the one-byte string ID select the group;
the low two bits select one of its four sequential NUL-terminated strings.

`$6D4E` reads five-bit tokens least-significant bit first. Most tokens index the
dictionary directly. Token `$1E` uppercases the next lowercase dictionary
character, while `$1F` adds `$1E` to the following token before lookup. A
dictionary value of zero terminates a string.

## Reproduction

```text
python tools/decode_e1_room_text.py extracted/e1/e1_room0_ready_memory.bin extracted/e1
```

The command writes `extracted/e1/e1_room0_text.json` and
`extracted/e1/e1_room0_text.txt`, including the source snapshot hash. The
synthetic fixture in `tools/test_e1_room_text.py` independently covers group
selection, capitalization, extended tokens, and invalid pointers.

`tools/vice_room0_text_probe.mon` invokes the original `$6C8C/$6CBC` routines
for string ID `$01`. Its output buffer at `$E700` contains the PETSCII bytes for
`In the Chatsubo Bar.` and a trailing NUL, matching the Python decoder.
