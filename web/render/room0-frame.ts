import type { GameData } from "../data/game-data.ts";
import type { Room0State } from "../systems/room0.ts";


const C64_PALETTE = [
  "#000000", "#ffffff", "#af3c58", "#7ef3d6",
  "#b83fb8", "#73d057", "#2c3dec", "#ffff46",
  "#b97100", "#775300", "#e98396", "#949494",
  "#949494", "#b7ff86", "#7385ff", "#cdcdcd",
] as const;

export interface Room0Frame {
  width: 320;
  height: 200;
  screenCodes: number[];
  charset: number[];
  colorCodes: number[];
  backgroundColor: string;
  sprites: Array<{
    x: number;
    y: number;
    color: string;
    sharedColors: [string, string];
    rows: number[][];
  }>;
}


export function buildRoom0Frame(data: GameData, _state: Room0State): Room0Frame {
  return {
    width: 320,
    height: 200,
    screenCodes: data.room.display.screenCodes,
    charset: data.room.display.charset,
    colorCodes: data.room.display.colorCodes,
    backgroundColor: C64_PALETTE[data.room.display.backgroundColor & 0x0f],
    sprites: data.room.sprites.map((sprite) => ({
      x: sprite.x - 24,
      y: sprite.y - 50,
      color: C64_PALETTE[sprite.color & 0x0f],
      sharedColors: [
        C64_PALETTE[sprite.sharedColors[0] & 0x0f],
        C64_PALETTE[sprite.sharedColors[1] & 0x0f],
      ],
      rows: sprite.rows,
    })),
  };
}
