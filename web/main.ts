import { parseGameData } from "./data/game-data.ts";
import { buildRoom0Frame } from "./render/room0-frame.ts";
import { drawRoom0Frame } from "./render/canvas-renderer.ts";
import { createRoom0State, enterRoom0, tickRoom0 } from "./systems/room0.ts";


function requiredElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`required display element ${selector} is missing`);
  return element;
}


function requiredContext(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const value = canvas.getContext("2d");
  if (!value) throw new Error("2D canvas is unavailable");
  return value;
}


const canvas = requiredElement<HTMLCanvasElement>("#game");
const tickLabel = requiredElement<HTMLElement>("#tick");
const context = requiredContext(canvas);

const response = await fetch("./generated/room0.json");
if (!response.ok) throw new Error(`room data request failed: ${response.status}`);
const data = parseGameData(await response.json());
const state = createRoom0State();
enterRoom0(state);

let tick = 0;
function render(): void {
  drawRoom0Frame(context, buildRoom0Frame(data, state), tick);
  tickLabel.textContent = String(tick).padStart(4, "0");
}

render();
window.setInterval(() => {
  tickRoom0(state);
  tick += 1;
  render();
}, 50);
