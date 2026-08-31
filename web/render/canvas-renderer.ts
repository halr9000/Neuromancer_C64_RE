import type { Room0Frame } from "./room0-frame.ts";

const C64_PALETTE = [
  "#000000", "#ffffff", "#883932", "#67b6bd",
  "#8b3f96", "#55a049", "#40318d", "#bfce72",
  "#8b5429", "#6d5412", "#b86962", "#505050",
  "#787878", "#94e089", "#7869c4", "#9f9f9f",
] as const;


function drawSprite(
  context: CanvasRenderingContext2D,
  sprite: Room0Frame["sprites"][number],
): void {
  context.fillStyle = sprite.color;
  for (let row = 0; row < sprite.rows.length; row += 1) {
    for (let column = 0; column < sprite.rows[row].length; column += 1) {
      if (sprite.rows[row][column]) {
        context.fillRect(sprite.x + column, sprite.y + row, 1, 1);
      }
    }
  }
}


export function drawRoom0Frame(
  context: CanvasRenderingContext2D,
  frame: Room0Frame,
  _tick: number,
): void {
  context.imageSmoothingEnabled = false;
  context.fillStyle = frame.backgroundColor;
  context.fillRect(0, 0, frame.width, frame.height);

  for (let cell = 0; cell < 1000; cell += 1) {
    const character = frame.screenCodes[cell];
    context.fillStyle = C64_PALETTE[frame.colorCodes[cell] & 0x0f];
    for (let row = 0; row < 8; row += 1) {
      const bits = frame.charset[character * 8 + row];
      for (let column = 0; column < 8; column += 1) {
        if (bits & (0x80 >> column)) {
          context.fillRect((cell % 40) * 8 + column, Math.floor(cell / 40) * 8 + row, 1, 1);
        }
      }
    }
  }

  for (const sprite of frame.sprites) drawSprite(context, sprite);
}
