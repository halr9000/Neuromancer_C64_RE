import assert from "node:assert/strict";
import test from "node:test";

import { createRoom0State, enterRoom0, tickRoom0 } from "./room0.ts";


test("room 0 reproduces the verified initialization and 64-tick trace", () => {
  const state = createRoom0State();

  enterRoom0(state);
  assert.deepEqual(state, {
    primaryFrame1: 0x22,
    primaryFrame2: 0xb1,
    secondaryFrame1: 0x24,
    secondaryFrame2: 0x00,
    logicalX2: 0x00,
    logicalY2: 0x00,
    packedColor2: 0x33,
    renderFlags2: 0x42,
    animationIndices: [0, 0, 0],
    animationCountdowns: [1, 1, 1],
  });

  for (let frame = 0; frame < 64; frame += 1) {
    tickRoom0(state);
  }

  assert.deepEqual(state, {
    primaryFrame1: 0x23,
    primaryFrame2: 0x3e,
    secondaryFrame1: 0x27,
    secondaryFrame2: 0x3e,
    logicalX2: 0x97,
    logicalY2: 0x28,
    packedColor2: 0x33,
    renderFlags2: 0x42,
    animationIndices: [0, 4, 0x23],
    animationCountdowns: [0x11, 0x05, 0xf5],
  });
});
