import assert from "node:assert/strict";
import test from "node:test";

import { encodePpm } from "./ppm.ts";


test("encodes RGBA pixels as a binary RGB PPM", () => {
  const result = encodePpm(2, 1, new Uint8ClampedArray([
    1, 2, 3, 255,
    4, 5, 6, 128,
  ]));

  assert.deepEqual(result, Buffer.concat([
    Buffer.from("P6\n2 1\n255\n", "ascii"),
    Buffer.from([1, 2, 3, 4, 5, 6]),
  ]));
});
