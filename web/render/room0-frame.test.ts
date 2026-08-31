import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { parseGameData } from "../data/game-data.ts";
import { createRoom0State, enterRoom0, tickRoom0 } from "../systems/room0.ts";
import { buildRoom0Frame } from "./room0-frame.ts";


test("builds a 320x200 frame from verified room-zero coordinates", () => {
  const source = readFileSync(new URL("../public/generated/room0.json", import.meta.url), "utf8");
  const data = parseGameData(JSON.parse(source));
  const state = createRoom0State();
  enterRoom0(state);
  tickRoom0(state);

  const frame = buildRoom0Frame(data, state);

  assert.equal(frame.width, 320);
  assert.equal(frame.height, 200);
  assert.equal(frame.screenCodes.length, 1000);
  assert.equal(frame.charset.length, 2048);
  assert.equal(frame.colorCodes.length, 1000);
  assert.deepEqual(frame.sprites.map((sprite) => [sprite.x, sprite.y, sprite.color]), [
    [64, 88, "#6d5412"],
    [64, 109, "#883932"],
  ]);
  assert.equal(frame.backgroundColor, "#000000");
});
