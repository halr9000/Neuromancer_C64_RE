# Dead Ends & Investigation Notes

Read before starting a session. Append after 10 or more unproductive tool calls on one task.

Lifecycle: **Active** -> **Resolved** (prefix with date once understood) -> delete after 20 or more sessions.

## Entry format

## Subsystem or Function Name
- **Tried**: approach attempted
- **Failed because**: root cause
- **Better approach**: next method
- **Session**: number

## 2026-08-29 — Treating the E1 PRG as a flat resident image

- **Tried**: map every byte after the `$02A7` PRG header directly through
  `$CCF6` and disassemble nominal addresses such as `$C100`.
- **Failed because**: the first-stage `ISTOP` hook changes the KERNAL load
  pointer to `$C000`. Directory-stream bytes nominally associated with
  `$032A-$0569` are actually placed at `$C000-$C23F`, and later sectors carry
  fastloader destination records rather than a flat image.
- **Better approach**: retain both file-stream offsets and runtime addresses;
  reconstruct the `$C000` stage first, then parse the remaining linked sectors
  with the verified `$0100` client protocol.
- **Session**: option-1 E1 boot-chain checkpoint
