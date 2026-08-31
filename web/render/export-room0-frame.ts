import { readFileSync, writeFileSync } from "node:fs";

import { parseGameData } from "../data/game-data.ts";
import { createRoom0State, enterRoom0 } from "../systems/room0.ts";
import { composeRoom0Pixels } from "./frame-composer.ts";
import { encodePpm } from "./ppm.ts";
import { buildRoom0Frame } from "./room0-frame.ts";


const output = process.argv[2];
if (!output) throw new Error("usage: export-room0-frame.ts OUTPUT.ppm");
const source = readFileSync(
  new URL("../public/generated/room0.json", import.meta.url),
  "utf8",
);
const data = parseGameData(JSON.parse(source));
const state = createRoom0State();
enterRoom0(state);
const frame = buildRoom0Frame(data, state);
writeFileSync(output, encodePpm(frame.width, frame.height, composeRoom0Pixels(frame)));
console.log(`wrote ${frame.width}x${frame.height} room-0 frame to ${output}`);
