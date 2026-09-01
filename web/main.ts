import { parseGameData } from "./data/game-data.ts";
import { parseRoomCatalog, type RoomCatalogEntry } from "./data/room-catalog.ts";
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
const catalogRoot = requiredElement<HTMLElement>("#room-catalog");

function roomCard(room: RoomCatalogEntry): HTMLElement {
  const article = document.createElement("article");
  article.className = "room-card";

  const image = document.createElement("img");
  image.src = room.frame;
  image.alt = `Verified native C64 frame for ${room.name}`;
  image.width = 320;
  image.height = 200;

  const copy = document.createElement("div");
  copy.className = "room-copy";
  const label = document.createElement("p");
  label.className = "room-number";
  label.textContent = `ROOM ${String(room.id).padStart(2, "0")} · SIDE ${room.provenance.side} · ${room.provenance.start}`;
  const heading = document.createElement("h3");
  heading.textContent = room.name;
  const location = document.createElement("p");
  location.className = "room-location";
  location.textContent = room.location;
  const description = document.createElement("p");
  description.textContent = room.description;
  const facts = document.createElement("p");
  facts.className = "room-facts";
  facts.textContent = `${room.entityCount} recovered ${room.entityCount === 1 ? "entity" : "entities"} · PAX ${room.terminalEnabled ? "available" : "unavailable"} · module ${room.provenance.moduleSha256.slice(0, 12)}`;
  copy.append(label, heading, location, description, facts);
  article.append(image, copy);
  return article;
}

const response = await fetch("./generated/room0.json");
if (!response.ok) throw new Error(`room data request failed: ${response.status}`);
const data = parseGameData(await response.json());
const catalogResponse = await fetch("./generated/room-catalog.json");
if (!catalogResponse.ok) throw new Error(`room catalog request failed: ${catalogResponse.status}`);
const catalog = parseRoomCatalog(await catalogResponse.json());
catalogRoot.replaceChildren(...catalog.rooms.map(roomCard));
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
