import assert from "node:assert/strict";
import test from "node:test";

import type { Room0Frame } from "./room0-frame.ts";
import { composeRoom0Pixels } from "./frame-composer.ts";


test("composes standard-text foreground bits into an RGBA frame", () => {
  const frame: Room0Frame = {
    width: 320,
    height: 200,
    screenCodes: Array(1000).fill(0),
    charset: Array(2048).fill(0),
    colorCodes: Array(1000).fill(2),
    backgroundColor: "#000000",
    sprites: [],
  };
  frame.charset[0] = 0x81;

  const pixels = composeRoom0Pixels(frame);

  assert.deepEqual(Array.from(pixels.slice(0, 32)), [
    0xaf, 0x3c, 0x58, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0x00, 0x00, 0x00, 0xff,
    0xaf, 0x3c, 0x58, 0xff,
  ]);
});


test("uses the VICE capture RGB value for color RAM gray", () => {
  const frame: Room0Frame = {
    width: 320,
    height: 200,
    screenCodes: Array(1000).fill(0),
    charset: Array(2048).fill(0),
    colorCodes: Array(1000).fill(12),
    backgroundColor: "#000000",
    sprites: [],
  };
  frame.charset[0] = 0x80;

  assert.deepEqual(Array.from(composeRoom0Pixels(frame).slice(0, 4)), [
    0x94, 0x94, 0x94, 0xff,
  ]);
});


test("composes two-bit multicolor sprite pixels at double width", () => {
  const rows = Array.from({ length: 21 }, () => Array(24).fill(0));
  rows[0].splice(0, 6, 1, 1, 2, 2, 3, 3);
  const frame: Room0Frame = {
    width: 320,
    height: 200,
    screenCodes: Array(1000).fill(0),
    charset: Array(2048).fill(0),
    colorCodes: Array(1000).fill(0),
    backgroundColor: "#000000",
    sprites: [{
      x: 0,
      y: 0,
      color: "#af3c58",
      sharedColors: ["#2c3dec", "#ffff46"],
      rows,
    }],
  };

  const pixels = composeRoom0Pixels(frame);

  assert.deepEqual(Array.from(pixels.slice(0, 24)), [
    0x2c, 0x3d, 0xec, 0xff, 0x2c, 0x3d, 0xec, 0xff,
    0xaf, 0x3c, 0x58, 0xff, 0xaf, 0x3c, 0x58, 0xff,
    0xff, 0xff, 0x46, 0xff, 0xff, 0xff, 0x46, 0xff,
  ]);
});
