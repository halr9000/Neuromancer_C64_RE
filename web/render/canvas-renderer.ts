import type { Room0Frame } from "./room0-frame.ts";


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


function wrapText(text: string, width: number): string[] {
  const words = text.replaceAll("\r", " ").split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length > width && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}


export function drawRoom0Frame(
  context: CanvasRenderingContext2D,
  frame: Room0Frame,
  tick: number,
): void {
  context.imageSmoothingEnabled = false;
  context.fillStyle = "#40318d";
  context.fillRect(0, 0, frame.width, frame.height);
  context.fillStyle = "#090a12";
  context.fillRect(8, 8, 304, 184);

  context.font = "8px monospace";
  context.textBaseline = "top";
  context.fillStyle = "#67b6bd";
  context.fillText(frame.title.toUpperCase(), 16, 16);
  context.fillStyle = "#505050";
  context.fillText(`ROOM 00  TICK ${String(tick).padStart(4, "0")}`, 184, 16);
  context.strokeStyle = "#40318d";
  context.strokeRect(15.5, 31.5, 288, 88);

  for (const sprite of frame.sprites) drawSprite(context, sprite);

  context.fillStyle = frame.actorProbe.color;
  context.fillRect(frame.actorProbe.x - 2, frame.actorProbe.y - 2, 5, 5);
  context.fillStyle = "#9f9f9f";
  context.fillText("ROOM LOGIC PROBE", 188, 108);

  context.fillStyle = "#40318d";
  context.fillRect(16, 127, 288, 1);
  context.fillStyle = "#ffffff";
  const lines = wrapText(frame.description, 45).slice(0, 6);
  lines.forEach((line, index) => context.fillText(line, 16, 136 + index * 9));
}
