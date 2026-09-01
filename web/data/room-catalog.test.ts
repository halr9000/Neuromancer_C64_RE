import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { parseRoomCatalog } from "./room-catalog.ts";

test("loads Chatsubo and Cheap Hotel evidence records", () => {
  const source = readFileSync(
    new URL("../public/generated/room-catalog.json", import.meta.url), "utf8");
  const catalog = parseRoomCatalog(JSON.parse(source));
  assert.deepEqual(catalog.rooms.map((room) => room.id), [0, 6]);
  assert.equal(catalog.rooms[1].name, "Cheap Hotel");
  assert.equal(catalog.rooms[1].provenance.start, "T11/S14");
  assert.match(catalog.rooms[1].description, /fiberglass coffins/);
});

test("rejects unsupported catalog data", () => {
  assert.throws(() => parseRoomCatalog({ schemaVersion: 2, rooms: [] }), /unsupported/);
});
