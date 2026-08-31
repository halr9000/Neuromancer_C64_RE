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
  title: string;
  description: string;
  sprites: Array<{
    x: number;
    y: number;
    color: string;
    rows: number[][];
  }>;
  actorProbe: {
    x: number;
    y: number;
    color: string;
  };
}


export function buildRoom0Frame(data: GameData, state: Room0State): Room0Frame {
  return {
    width: 320,
    height: 200,
    title: data.room.text[1],
    description: data.room.text[0],
    sprites: data.room.sprites.map((sprite) => ({
      x: sprite.x,
      y: sprite.y,
      color: C64_PALETTE[sprite.color & 0x0f],
      rows: sprite.rows,
    })),
    actorProbe: {
      x: (state.logicalX2 + 0x0c) * 2,
      y: state.logicalY2 + 0x36,
      color: C64_PALETTE[4],
    },
  };
}
