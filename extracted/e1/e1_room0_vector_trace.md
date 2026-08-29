# E1 room-0 vector execution trace

The trace executes the reconstructed room snapshot with synthetic RTS caller frames.
No VIC-II, CIA, keyboard, or VICE behavior is simulated in this checkpoint.

Source SHA-256: `66316f2f3b0ccb2b03dfba6314978afbe665b470290cd51290db2f9837c32089`
Ticks executed: 64
Tick instructions: 1276

## Initialize vector `$F00A -> $F0F6`

Instructions: 13
Changed state: `{'0x0003': 34, '0x0007': 36, '0x0014': 51, '0x0018': 66}`

## Tick vector `$F00D -> $F10E`

- Frame 1: 41 instructions; changed `{'0x0004': 62, '0x0008': 62, '0x000C': 90, '0x0010': 50, '0xF17B': 1, '0xF17C': 1, '0xF17D': 1, '0xF17E': 20, '0xF17F': 5, '0xF180': 10}`
- Frame 2: 8 instructions; changed `{'0xF17E': 19, '0xF17F': 4, '0xF180': 9}`
- Frame 3: 8 instructions; changed `{'0xF17E': 18, '0xF17F': 3, '0xF180': 8}`
- Frame 4: 8 instructions; changed `{'0xF17E': 17, '0xF17F': 2, '0xF180': 7}`
- Frame 5: 8 instructions; changed `{'0xF17E': 16, '0xF17F': 1, '0xF180': 6}`
- Frame 6: 17 instructions; changed `{'0x0007': 37, '0xF17C': 2, '0xF17E': 15, '0xF17F': 2, '0xF180': 5}`
- Frame 7: 8 instructions; changed `{'0xF17E': 14, '0xF17F': 1, '0xF180': 4}`
- Frame 8: 17 instructions; changed `{'0x0007': 38, '0xF17C': 3, '0xF17E': 13, '0xF17F': 2, '0xF180': 3}`
- Frame 9: 8 instructions; changed `{'0xF17E': 12, '0xF17F': 1, '0xF180': 2}`
- Frame 10: 17 instructions; changed `{'0x0007': 39, '0xF17C': 4, '0xF17E': 11, '0xF17F': 5, '0xF180': 1}`
- Frame 11: 23 instructions; changed `{'0x0004': 40, '0x0008': 41, '0xF17D': 2, '0xF17E': 10, '0xF17F': 4, '0xF180': 3}`
- Frame 12: 8 instructions; changed `{'0xF17E': 9, '0xF17F': 3, '0xF180': 2}`
- Frame 13: 8 instructions; changed `{'0xF17E': 8, '0xF17F': 2, '0xF180': 1}`
- Frame 14: 23 instructions; changed `{'0x0004': 42, '0x0008': 43, '0xF17D': 3, '0xF17E': 7, '0xF17F': 1, '0xF180': 3}`
- Frame 15: 17 instructions; changed `{'0x0007': 38, '0xF17C': 5, '0xF17E': 6, '0xF17F': 2, '0xF180': 2}`
- Frame 16: 8 instructions; changed `{'0xF17E': 5, '0xF17F': 1, '0xF180': 1}`
- Frame 17: 33 instructions; changed `{'0x0004': 44, '0x0007': 37, '0x0008': 45, '0xF17C': 0, '0xF17D': 4, '0xF17E': 4, '0xF17F': 2, '0xF180': 3}`
- Frame 18: 8 instructions; changed `{'0xF17E': 3, '0xF17F': 1, '0xF180': 2}`
- Frame 19: 17 instructions; changed `{'0x0007': 36, '0xF17C': 1, '0xF17E': 2, '0xF17F': 5, '0xF180': 1}`
- Frame 20: 23 instructions; changed `{'0x0004': 46, '0x0008': 47, '0xF17D': 5, '0xF17E': 1, '0xF17F': 4, '0xF180': 3}`
- Frame 21: 18 instructions; changed `{'0x0003': 35, '0xF17B': 0, '0xF17E': 20, '0xF17F': 3, '0xF180': 2}`
- Frame 22: 8 instructions; changed `{'0xF17E': 19, '0xF17F': 2, '0xF180': 1}`
- Frame 23: 23 instructions; changed `{'0x0004': 48, '0x0008': 49, '0xF17D': 6, '0xF17E': 18, '0xF17F': 1, '0xF180': 2}`
- Frame 24: 17 instructions; changed `{'0x0007': 37, '0xF17C': 2, '0xF17E': 17, '0xF17F': 2, '0xF180': 1}`
- Frame 25: 23 instructions; changed `{'0x0004': 50, '0x0008': 51, '0x000C': 92, '0x0010': 48, '0xF17D': 7, '0xF17E': 16, '0xF17F': 1, '0xF180': 2}`
- Frame 26: 17 instructions; changed `{'0x0007': 38, '0xF17C': 3, '0xF17E': 15, '0xF17F': 2, '0xF180': 1}`
- Frame 27: 23 instructions; changed `{'0x0004': 52, '0x0008': 53, '0x000C': 94, '0x0010': 46, '0xF17D': 8, '0xF17E': 14, '0xF17F': 1}`
- Frame 28: 32 instructions; changed `{'0x0004': 54, '0x0007': 39, '0x0008': 55, '0x000C': 96, '0x0010': 44, '0xF17C': 4, '0xF17D': 9, '0xF17E': 13, '0xF17F': 5}`
- Frame 29: 23 instructions; changed `{'0x000C': 98, '0x0010': 42, '0xF17D': 10, '0xF17E': 12, '0xF17F': 4}`
- Frame 30: 23 instructions; changed `{'0x000C': 100, '0x0010': 40, '0xF17D': 11, '0xF17E': 11, '0xF17F': 3}`
- Frame 31: 23 instructions; changed `{'0x000C': 102, '0xF17D': 12, '0xF17E': 10, '0xF17F': 2}`
- Frame 32: 23 instructions; changed `{'0x000C': 104, '0xF17D': 13, '0xF17E': 9, '0xF17F': 1}`
- Frame 33: 32 instructions; changed `{'0x0007': 38, '0x000C': 106, '0xF17C': 5, '0xF17D': 14, '0xF17E': 8, '0xF17F': 2}`
- Frame 34: 23 instructions; changed `{'0x000C': 108, '0xF17D': 15, '0xF17E': 7, '0xF17F': 1}`
- Frame 35: 33 instructions; changed `{'0x0007': 37, '0x000C': 110, '0xF17C': 0, '0xF17D': 16, '0xF17E': 6, '0xF17F': 2}`
- Frame 36: 23 instructions; changed `{'0x000C': 112, '0xF17D': 17, '0xF17E': 5, '0xF17F': 1}`
- Frame 37: 32 instructions; changed `{'0x0007': 36, '0x000C': 114, '0xF17C': 1, '0xF17D': 18, '0xF17E': 4, '0xF17F': 5}`
- Frame 38: 23 instructions; changed `{'0x000C': 116, '0xF17D': 19, '0xF17E': 3, '0xF17F': 4}`
- Frame 39: 23 instructions; changed `{'0x000C': 118, '0xF17D': 20, '0xF17E': 2, '0xF17F': 3}`
- Frame 40: 23 instructions; changed `{'0x000C': 120, '0xF17D': 21, '0xF17E': 1, '0xF17F': 2}`
- Frame 41: 32 instructions; changed `{'0x0003': 34, '0x000C': 122, '0xF17B': 1, '0xF17D': 22, '0xF17E': 20, '0xF17F': 1}`
- Frame 42: 32 instructions; changed `{'0x0007': 37, '0x000C': 124, '0xF17C': 2, '0xF17D': 23, '0xF17E': 19, '0xF17F': 2}`
- Frame 43: 23 instructions; changed `{'0x000C': 126, '0xF17D': 24, '0xF17E': 18, '0xF17F': 1}`
- Frame 44: 32 instructions; changed `{'0x0007': 38, '0x000C': 128, '0xF17C': 3, '0xF17D': 25, '0xF17E': 17, '0xF17F': 2}`
- Frame 45: 23 instructions; changed `{'0x000C': 130, '0xF17D': 26, '0xF17E': 16, '0xF17F': 1}`
- Frame 46: 32 instructions; changed `{'0x0007': 39, '0x000C': 132, '0xF17C': 4, '0xF17D': 27, '0xF17E': 15, '0xF17F': 5}`
- Frame 47: 23 instructions; changed `{'0x000C': 134, '0xF17D': 28, '0xF17E': 14, '0xF17F': 4}`
- Frame 48: 23 instructions; changed `{'0x0008': 56, '0x000C': 136, '0xF17D': 29, '0xF17E': 13, '0xF17F': 3}`
- Frame 49: 23 instructions; changed `{'0x0008': 57, '0x000C': 139, '0xF17D': 30, '0xF17E': 12, '0xF17F': 2}`
- Frame 50: 23 instructions; changed `{'0x0008': 58, '0x000C': 142, '0xF17D': 31, '0xF17E': 11, '0xF17F': 1}`
- Frame 51: 32 instructions; changed `{'0x0007': 38, '0x0008': 62, '0x000C': 145, '0xF17C': 5, '0xF17D': 32, '0xF17E': 10, '0xF17F': 2}`
- Frame 52: 23 instructions; changed `{'0x0004': 59, '0x000C': 148, '0xF17D': 33, '0xF17E': 9, '0xF17F': 1}`
- Frame 53: 33 instructions; changed `{'0x0004': 60, '0x0007': 37, '0x000C': 151, '0xF17C': 0, '0xF17D': 34, '0xF17E': 8, '0xF17F': 2}`
- Frame 54: 23 instructions; changed `{'0x0004': 62, '0xF17D': 35, '0xF17E': 7, '0xF17F': 1, '0xF180': 255}`
- Frame 55: 17 instructions; changed `{'0x0007': 36, '0xF17C': 1, '0xF17E': 6, '0xF17F': 5, '0xF180': 254}`
- Frame 56: 8 instructions; changed `{'0xF17E': 5, '0xF17F': 4, '0xF180': 253}`
- Frame 57: 8 instructions; changed `{'0xF17E': 4, '0xF17F': 3, '0xF180': 252}`
- Frame 58: 8 instructions; changed `{'0xF17E': 3, '0xF17F': 2, '0xF180': 251}`
- Frame 59: 8 instructions; changed `{'0xF17E': 2, '0xF17F': 1, '0xF180': 250}`
- Frame 60: 17 instructions; changed `{'0x0007': 37, '0xF17C': 2, '0xF17E': 1, '0xF17F': 2, '0xF180': 249}`
- Frame 61: 18 instructions; changed `{'0x0003': 35, '0xF17B': 0, '0xF17E': 20, '0xF17F': 1, '0xF180': 248}`
- Frame 62: 17 instructions; changed `{'0x0007': 38, '0xF17C': 3, '0xF17E': 19, '0xF17F': 2, '0xF180': 247}`
- Frame 63: 8 instructions; changed `{'0xF17E': 18, '0xF17F': 1, '0xF180': 246}`
- Frame 64: 17 instructions; changed `{'0x0007': 39, '0xF17C': 4, '0xF17E': 17, '0xF17F': 5, '0xF180': 245}`

## Teardown vector `$F010 -> $F10D`

Instructions: 2

## Entity dispatcher `$6429` inactive-slot control path

A clone of the source snapshot sets `$9D-$A0` to `$FF` so no
entity script handler executes. This proves the dispatcher structure only; it
does not assert runtime entity behavior from this synthetic setup.

Instructions: 24
Room data root saved: `{'low': '0x48', 'high': '0xF2'}`
