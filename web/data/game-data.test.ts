import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { parseGameData } from "./game-data.ts";


test("loads the generated room-zero text and entity record", () => {
  const source = readFileSync(new URL("../public/generated/room0.json", import.meta.url), "utf8");

  const data = parseGameData(JSON.parse(source));

  assert.equal(data.room.text.length, 0x21);
  assert.equal(data.room.text[1], "In the Chatsubo Bar.");
  assert.equal(data.room.sprites[0].pointer, 0x21);
  assert.deepEqual(data.room.sprites.map((sprite) => [sprite.x, sprite.y, sprite.color]), [
    [64, 88, 9],
    [64, 109, 2],
  ]);
  assert.deepEqual(data.room.entities[0], {
    sourceAddress: "0xC400",
    sourceBytes: [0x00, 0xc1, 0x14, 0x22, 0x29, 0xff, 0x00, 0x00],
    roomId: 0,
    slot: 1,
    packedRenderFlags: 0xc1,
    logicalX: 0x14,
    logicalY: 0x22,
    packedColors: 0x29,
    activationState: 0xff,
    scriptAddress: 0,
  });
});


test("rejects an incompatible generated-data schema", () => {
  assert.throws(
    () => parseGameData({ schemaVersion: 2 }),
    /schema version 2/,
  );
});
