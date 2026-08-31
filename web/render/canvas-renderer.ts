import type { Room0Frame } from "./room0-frame.ts";
import { composeRoom0Pixels } from "./frame-composer.ts";


export function drawRoom0Frame(
  context: CanvasRenderingContext2D,
  frame: Room0Frame,
  _tick: number,
): void {
  context.imageSmoothingEnabled = false;
  const image = context.createImageData(frame.width, frame.height);
  image.data.set(composeRoom0Pixels(frame));
  context.putImageData(image, 0, 0);
}
