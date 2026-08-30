# E1 Entity Records and Sprite-Frame Fields

## Room record initialization

The room loader scans up to 96 eight-byte records beginning at `$C400`. For a
record whose byte 0 matches the current room ID, byte 1 selects one of four
runtime slots through its low two bits and supplies that slot's packed render
flags. Bytes 2, 3, and 4 seed the slot arrays at `$0A`, `$0E`, and `$12`.

When byte 5 is `$FF`, first activation changes it to `$00` and resolves the
initial script pointer from the room table rooted at `$F002/$F003`, storing it in
bytes 6-7. In room 0, only `$C400` activates:

| Offset | Room-0 value | Verified use |
|---:|---:|---|
| 0 | `$00` | room ID |
| 1 | `$C1` | packed actor flags; low bits select slot 1 |
| 2 | `$14` | copied to slot array `$0A` |
| 3 | `$22` | copied to slot array `$0E` |
| 4 | `$29` | copied to slot array `$12` |
| 5 | `$FF -> $00` | first-activation state |
| 6-7 | `$0000 -> $F02D` | current script opcode pointer |

The other three records shown in the bounded capture retain `$FF` at byte 5 and
null script pointers.

The valid table terminates at the first negative room-ID byte, `$C518=$FF`
(record index 35). `$C400` is the only room-ID-0 record before that sentinel.
Faithful isolated execution must first reproduce the room loader's
`$9D-$A0=$FF` reset so only slot 1 (`$9E`) becomes active.

## Dispatcher evidence

`$6429` resolves active slot 1 to record `$C400` and script pointer `$F02D`.
Opcode `$01` selects handler `$64B5`. The dispatcher advances bytes 6-7 by the
handler's returned record length after a handler completes. The opcode-1 handler
first completes `$6CBC` and `$BCDC`, then enters input-release handshake `$5933`.
Its alternate `$3D!=0` path clears the flag and returns. `$BCDC` derives
`$BEF8/$BEF9 = $28/$05` before the final `$BE89` screen/sprite rebuild. The
isolated VICE process does not reach the checkpoint after `$BE89`, so its missing
live-frame dependency and higher-level semantics remain open.

## Sprite-frame evidence

`$5B1E` copies six parallel four-slot arrays into `$5E01-$5E18`, depth-sorts the
records using the `$0E` field, and builds VIC-II-facing fields at
`$5E19-$5E34`. The complete post-overlay path reaches its first initialized
frame in 192,477 VICE cycles. Applying that frame through the real IRQ transfer
loop `$4D46-$4D7E` produces this hardware state:

| Sprite | Enabled | X | Y | Pointer | Color |
|---:|:---:|---:|---:|---:|---:|
| 1 | yes | 64 | 88 | `$21` | `$9` |
| 2 | yes | 64 | 109 | `$22` | `$2` |

That transfer confirms the parallel-array meanings:

| Array | Confirmed meaning |
|---:|---|
| `$02-$05` | primary sprite-frame source |
| `$06-$09` | secondary sprite-frame source |
| `$0A-$0D` | logical X; rendered as `(X+$0C)*2` with carry in `$D010` |
| `$0E-$11` | logical Y; rendered as `Y+$36` |
| `$12-$15` | packed primary/secondary color nibbles |
| `$16-$19` | packed enable, composition, priority, expansion, and multicolor flags |

The captures are reproducible with `tools/vice_entity_dispatch_probe.mon` and
`tools/vice_entity_sprite_frame_probe.mon`. They intentionally distinguish
verified byte flow from higher-level gameplay interpretation. The checked-in
VICE screenshot includes incomplete background/screen RAM, so it proves sprite
register transfer and field names rather than final room composition.

`tools/vice_main_loop_entry_probe.mon` additionally enters `$488D`, verifies
that transient fields `$90/$CB` are cleared, and reaches `$6429` in 25 VICE
cycles. It establishes the live main-loop-to-dispatch edge without pretending
that the isolated opcode-1 UI handler constitutes a complete gameplay frame.
