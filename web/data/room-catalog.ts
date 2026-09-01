export interface RoomCatalogEntry {
  id: number;
  name: string;
  location: string;
  description: string;
  frame: string;
  frameSha256: string;
  terminalEnabled: boolean;
  entityCount: number;
  provenance: {
    side: number;
    start: string;
    moduleSha256: string;
  };
}

export interface RoomCatalog {
  schemaVersion: 1;
  rooms: RoomCatalogEntry[];
}

type JsonObject = Record<string, unknown>;

function object(value: unknown, name: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${name} must be an object`);
  }
  return value as JsonObject;
}

function text(value: unknown, name: string): string {
  if (typeof value !== "string") throw new TypeError(`${name} must be a string`);
  return value;
}

function integer(value: unknown, name: string): number {
  if (!Number.isInteger(value)) throw new TypeError(`${name} must be an integer`);
  return value as number;
}

export function parseRoomCatalog(value: unknown): RoomCatalog {
  const root = object(value, "room catalog");
  if (root.schemaVersion !== 1) {
    throw new TypeError(`unsupported room-catalog schema version ${String(root.schemaVersion)}`);
  }
  if (!Array.isArray(root.rooms)) throw new TypeError("room catalog rooms must be an array");
  return {
    schemaVersion: 1,
    rooms: root.rooms.map((value, index) => {
      const room = object(value, `room ${index}`);
      const provenance = object(room.provenance, `room ${index} provenance`);
      if (typeof room.terminalEnabled !== "boolean") {
        throw new TypeError(`room ${index} terminalEnabled must be a boolean`);
      }
      return {
        id: integer(room.id, `room ${index} id`),
        name: text(room.name, `room ${index} name`),
        location: text(room.location, `room ${index} location`),
        description: text(room.description, `room ${index} description`),
        frame: text(room.frame, `room ${index} frame`),
        frameSha256: text(room.frameSha256, `room ${index} frameSha256`),
        terminalEnabled: room.terminalEnabled,
        entityCount: integer(room.entityCount, `room ${index} entityCount`),
        provenance: {
          side: integer(provenance.side, `room ${index} side`),
          start: text(provenance.start, `room ${index} start`),
          moduleSha256: text(provenance.moduleSha256, `room ${index} moduleSha256`),
        },
      };
    }),
  };
}
