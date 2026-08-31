import type { GameData } from "../data/game-data.ts";
import type { Room0State } from "../systems/room0.ts";


const C64_PALETTE = [
  "#000000", "#ffffff", "#883932", "#67b6bd",
  "#8b3f96", "#55a049", "#40318d", "#bfce72",
  "#8b5429", "#6d5412", "#b86962", "#505050",
  "#787878", "#94e089", "#7869c4", "#9f9f9f",
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
      x: sprite.x,
      y: sprite.y,
      color: C64_PALETTE[sprite.color & 0x0f],
      rows: sprite.rows,
    })),
  };
}
