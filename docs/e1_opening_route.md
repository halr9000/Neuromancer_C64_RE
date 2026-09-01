# Verified opening route

The opening route crosses three independently recovered systems: room-0 entity
bytecode, the resident item/GIVE handler, and PAX overlays loaded from game side
1. `tools/trace_e1_opening.py` extracts the overlay chain, executes the isolated
state-changing 6510 slices, and writes
`extracted/e1/e1_opening_route_trace.json`. The matching VICE run is retained in
`extracted/e1/e1_vice_opening_state_probe.log`.

## PAX overlay chain

Room 0 enables PAX through `$F027 = $01`. The resident entry at `$49CB` loads
T12/S03 to `$7400`; its option table then loads four child overlays to `$1000`:

| Overlay | Side-1 sector | Length | Verified role |
|---|---:|---:|---|
| PAX shell | T12/S03 | 2,486 | Login and option dispatch |
| messages | T13/S11 | 3,085 | Inbox/message reader |
| bank | T17/S14 | 1,064 | 24-bit cash/bank transfer and history |
| directory | T14/S05 | 1,948 | PAX directory |
| send message | T34/S00 | 2,909 | Composition and Armitage response |

The bank-to-cash routine at `$10E8-$1140` subtracts the amount in `$57-$59`
from `$C33D-$C33F`, adds it to cash at `$C33A-$C33C`, and records a four-byte
history entry in the ring at `$C34A`. VICE confirms the required transfer:

`cash 6, bank 2000 -> cash 46, bank 1960`

The accepted Armitage/BAMA path at `$12EC-$1335` first checks a one-shot record,
then adds little-endian `$002710` (10,000) to the bank. Starting after the
required transfer, VICE confirms bank 11,960. The decoded solution independently
identifies the submitted BAMA ID as `056306118`; this prose evidence is not used
as a substitute for the executable deposit trace.

## Ratz and payment

Room entity `$C400` begins at script `$F02D`. Its first opcode displays room
string `$02`, Ratz's 46-credit demand, and the script contains the recovered
dialogue IDs through `$20`. The resident GIVE debit at `$68A8-$68C4` subtracts
the 24-bit amount before publishing the event in `$C112-$C114`. Both execution
engines confirm that giving 46 changes cash from 46 to 0 while retaining bank
1960.

Room routine `$F0DA-$F0F5` is a conditional refund hook, not the debit. This
distinction is regression-tested after an earlier incorrect interpretation
would have produced 65,536 credits. Room-0 teardown `$F10D` is a single `RTS`.

## Exit boundary

String `$1C` is `That's it. I'm leaving.` and the solution confirms Chatsubo is
closed after departure. Leaving returns to the Chiba location selector; it does
not automatically choose or load another room. Therefore no destination room ID
is promoted as verified opening behavior at this milestone. The next milestone
will extract a deliberately selected first destination and keep that player
choice distinct from the original automatic state transitions.

## Reproduce

```text
python tools/trace_e1_opening.py extracted/e1/e1_room0_ready_memory.bin intake/NEUROMA0.D64 extracted/e1
x64sc -default -sounddev dummy -moncommands tools/vice_opening_state_probe.mon
python -m unittest tools.test_e1_opening
```
