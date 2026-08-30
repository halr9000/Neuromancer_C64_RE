export interface EntityDefinition {
  sourceAddress: string;
  sourceBytes: number[];
  roomId: number;
  slot: number;
  packedRenderFlags: number;
  logicalX: number;
  logicalY: number;
  packedColors: number;
  activationState: number;
  scriptAddress: number;
}

export interface GameData {
  schemaVersion: 1;
  source: {
    snapshotSha256: string;
    roomTextRoot: string;
  };
  room: {
    id: number;
    text: string[];
    entities: EntityDefinition[];
  };
}


type JsonObject = Record<string, unknown>;


function object(value: unknown, name: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${name} must be an object`);
  }
  return value as JsonObject;
}


function string(value: unknown, name: string): string {
  if (typeof value !== "string") {
    throw new TypeError(`${name} must be a string`);
  }
  return value;
}


function byte(value: unknown, name: string): number {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 0xff) {
    throw new TypeError(`${name} must be a byte`);
  }
  return value as number;
}


function word(value: unknown, name: string): number {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 0xffff) {
    throw new TypeError(`${name} must be a word`);
  }
  return value as number;
}


function entity(value: unknown, index: number): EntityDefinition {
  const item = object(value, `entity ${index}`);
  if (!Array.isArray(item.sourceBytes) || item.sourceBytes.length !== 8) {
    throw new TypeError(`entity ${index} sourceBytes must contain eight bytes`);
  }
  return {
    sourceAddress: string(item.sourceAddress, `entity ${index} sourceAddress`),
    sourceBytes: item.sourceBytes.map((value, byteIndex) =>
      byte(value, `entity ${index} source byte ${byteIndex}`)),
    roomId: byte(item.roomId, `entity ${index} roomId`),
    slot: byte(item.slot, `entity ${index} slot`),
    packedRenderFlags: byte(item.packedRenderFlags, `entity ${index} packedRenderFlags`),
    logicalX: byte(item.logicalX, `entity ${index} logicalX`),
    logicalY: byte(item.logicalY, `entity ${index} logicalY`),
    packedColors: byte(item.packedColors, `entity ${index} packedColors`),
    activationState: byte(item.activationState, `entity ${index} activationState`),
    scriptAddress: word(item.scriptAddress, `entity ${index} scriptAddress`),
  };
}


export function parseGameData(value: unknown): GameData {
  const root = object(value, "game data");
  if (root.schemaVersion !== 1) {
    throw new TypeError(`unsupported game-data schema version ${String(root.schemaVersion)}`);
  }
  const source = object(root.source, "source");
  const room = object(root.room, "room");
  if (!Array.isArray(room.text) || !room.text.every((value) => typeof value === "string")) {
    throw new TypeError("room text must be an array of strings");
  }
  if (!Array.isArray(room.entities)) {
    throw new TypeError("room entities must be an array");
  }
  return {
    schemaVersion: 1,
    source: {
      snapshotSha256: string(source.snapshotSha256, "snapshotSha256"),
      roomTextRoot: string(source.roomTextRoot, "roomTextRoot"),
    },
    room: {
      id: byte(room.id, "room id"),
      text: [...room.text] as string[],
      entities: room.entities.map(entity),
    },
  };
}
