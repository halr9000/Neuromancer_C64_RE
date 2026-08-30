# Browser runtime architecture

## Status and design rule

This document defines the browser implementation boundary. The first headless
system now exists at `web/systems/room0.ts`; the wider graph remains a design,
not evidence that rendering or a playable browser shell exists. The port models
verified game behavior directly and keeps C64-specific decoding in an import
layer; it does not ship a 6510 emulator as the game runtime.

The first implementation target is one vertically integrated Chatsubo slice:
load room 0, run its deterministic update logic, display its verified actors
and text, accept pointer/keyboard input, and preserve enough state to reload.
Expansion to the remaining rooms follows only as their data and transitions are
verified.

## Proposed module graph

```text
main.ts
  -> app/runtime.ts
       -> core/game-state.ts
       -> core/game-loop.ts
       -> data/game-data.ts
            -> data/room-text.ts
            -> data/room-records.ts
            -> data/assets.ts
       -> systems/room.ts
            -> systems/entity-scripts.ts
       -> systems/input.ts
       -> render/c64-renderer.ts
       -> audio/audio-system.ts
       -> persistence/save-store.ts
```

| Proposed module | Public exports | Dependencies and responsibility |
|---|---|---|
| `main.ts` | none | Creates the canvas and services, then starts `Runtime`. No game rules. |
| `app/runtime.ts` | `Runtime` | Owns lifecycle and coordinates loop, state, room, renderer, input, audio, and saves. |
| `core/game-state.ts` | `GameState`, `ActorState`, `UiState`, `createNewGame()` | Typed, serializable canonical state. It must not depend on DOM or rendering. |
| `core/game-loop.ts` | `FixedStepLoop`, `TickResult` | Fixed-step updates with rendering interpolation; invokes systems in verified `$488D` order where known. |
| `data/game-data.ts` | `GameData`, `loadGameData()` | Loads versioned generated JSON/binary assets and validates schema/source hashes. |
| `data/room-text.ts` | `RoomTextTable`, `getRoomString()` | Consumes predecoded strings; the build-time extractor retains the `$6CBC` codec. |
| `data/room-records.ts` | `RoomDefinition`, `EntityDefinition` | Converts verified room/entity records into stable runtime data. Unknown fields remain explicitly named. |
| `data/assets.ts` | `SpriteAtlas`, `Palette` | Loads pixel-checked sprites and later room graphics without embedding VIC memory layout in game logic. |
| `systems/room.ts` | `enterRoom()`, `tickRoom()`, `leaveRoom()` | Implements the room vector lifecycle and applies room transitions. |
| `systems/entity-scripts.ts` | `tickEntities()`, `ScriptHandler` | Dispatches typed script operations corresponding to the verified `$6429` path. Unsupported opcodes fail visibly in development. |
| `systems/input.ts` | `InputState`, `InputAction`, `mapInput()` | Normalizes pointer, keyboard, and controller actions; hit regions are game-space data. |
| `render/c64-renderer.ts` | `C64Renderer`, `ViewportTransform` | Draws the 320x200 game surface, palette, text, sprites, and cursor to Canvas 2D. |
| `audio/audio-system.ts` | `AudioSystem`, `AudioCue` | Web Audio boundary. Initially silent/placeholder until SID behavior is mapped. |
| `persistence/save-store.ts` | `SaveStore`, `SaveEnvelope` | Versioned IndexedDB/local-storage adapter; never leaks storage concerns into `GameState`. |

The module graph is deliberately acyclic: platform adapters depend on core
types, while core state and rules know nothing about the browser. This makes a
headless deterministic replay test possible for every verified trace.

## Executable-to-web mapping

| Verified C64 boundary | Browser owner | Porting contract |
|---|---|---|
| `$4836` runtime entry | `app/runtime.ts` | Construct services, choose new/load state, and enter the first room. |
| `$488D` recurring tick | `core/game-loop.ts` | Fixed-step orchestration; preserve verified entity, room, frame, UI, and input ordering as each stage is mapped. |
| `$6158` room loader | `systems/room.ts` + `data/game-data.ts` | Resolve a room definition and invoke leave/load/enter without disk-side prompts. |
| `$F00A/$F00D/$F010` room vectors | `enterRoom/tickRoom/leaveRoom` | Typed room hooks with deterministic state changes; room 0 trace becomes the first golden test. |
| `$6429` entity dispatcher | `systems/entity-scripts.ts` | Visit active entity slots and dispatch decoded operations; retain unknown operations as hard diagnostics. |
| `$6C8C/$6CBC` room text | build-time decoder + `data/room-text.ts` | Export source-hashed Unicode/line-break-preserving data; select by byte ID at runtime. |
| `$5B1E` sprite-frame builder | room/entity systems + renderer snapshot | Sort actors and emit immutable render data, separate from drawing. |
| `$4D46-$4D7E` VIC transfer | `render/c64-renderer.ts` | Map logical positions, frame slots, colors, and flags onto canvas draw calls. |
| `$5036/$5293` viewport/text | `render/c64-renderer.ts` | C64-coordinate clipping and text layout, tested against emulator captures. |
| `$57B2/$57E7` hit regions | `systems/input.ts` | Test normalized game-space pointer coordinates against decoded regions. |
| `$4BEC/$4011` side I/O | `data/game-data.ts` | Replaced by prebuilt assets; source side/track/sector remains provenance metadata. |
| `$C100-$C9FC` state records | `core/game-state.ts` + `persistence/save-store.ts` | Decode known fields into a versioned save schema and retain unmapped bytes until understood. |

## Update and render flow

The browser loop uses `requestAnimationFrame` for presentation and an
accumulator for fixed simulation steps. A step must be replayable without a DOM:

```text
sample normalized input
  -> dispatch active entity scripts
  -> run current room tick
  -> resolve requested room/state transition
  -> build immutable render snapshot
  -> update UI/input edge state
  -> render latest snapshot
```

Only the edges proven around `$488D` are commitments today. Any ordering inside
unmapped UI or script handlers remains provisional and must be promoted by a
trace or regression fixture. The renderer may interpolate presentation, but it
must not mutate simulation state.

## Application state machine

```text
BOOT -> TITLE -> NEW_GAME_SETUP -> ROOM_LOADING -> PLAYING
               LOAD_GAME ------^       |
                                       +-> MODAL_UI -> PLAYING
                                       +-> ROOM_LOADING
                                       +-> SAVE_GAME -> PLAYING
                                       +-> GAME_OVER -> TITLE
```

`BOOT`, new/load selection, and entry into room 0 are verified at the executable
level. The generic `ROOM_LOADING` lifecycle is supported by `$6158` and the
room vectors. `MODAL_UI`, `SAVE_GAME`, and `GAME_OVER` are required product
states but their complete original transitions remain hypotheses until traced.
They must therefore be implemented behind explicit events, not inferred from
rendering or arbitrary memory values.

Room changes use a strict transaction:

1. request a destination room without mutating the current room;
2. call the current room's teardown hook;
3. validate and load the destination definition and assets;
4. update canonical room state;
5. call the destination initialization hook;
6. publish the first render snapshot.

Failure before step 4 leaves the current room intact. Development builds report
the room ID and source record instead of silently continuing with partial data.

## Data and provenance

Generated web data should be deterministic and carry:

- source disk SHA-256 and side/track/sector provenance;
- extractor/schema version;
- stable room, entity, string, sprite, and script IDs;
- original numeric values beside promoted semantic fields where useful;
- an explicit `unknown` structure for bytes whose meaning is not verified.

Disk images stay immutable under `intake/`. Browser-consumable artifacts should
be generated from the existing Python tools, then checked by hash and semantic
fixtures. Runtime code never parses a D64 or performs emulated disk I/O.

## Verification gates

The first slice is ready to expand only when all of these hold:

- a headless room-0 test matches the checked 64-tick trace;
- room text IDs `$00-$20` match `e1_room0_text.json`, preserving `\r` breaks;
- actor positions, frame slots, and colors match the VICE entity/VIC capture;
- at least one browser screenshot is pixel-compared at the 320x200 game surface;
- new/load persistence round-trips a versioned `GameState` without losing
  retained unknown source fields;
- unsupported room records or script operations fail with actionable IDs.

This architecture intentionally leaves audio fidelity and full-session
coverage outside the first slice. They remain required for the finished port,
but neither should block proving the core room/data/render pipeline end to end.
