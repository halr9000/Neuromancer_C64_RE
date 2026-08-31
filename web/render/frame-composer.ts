import type { Room0Frame } from "./room0-frame.ts";


const C64_PALETTE_RGB = [
  [0x00, 0x00, 0x00], [0xff, 0xff, 0xff], [0xaf, 0x3c, 0x58], [0x7e, 0xf3, 0xd6],
  [0xb8, 0x3f, 0xb8], [0x73, 0xd0, 0x57], [0x2c, 0x3d, 0xec], [0xff, 0xff, 0x46],
  [0xb9, 0x71, 0x00], [0x77, 0x53, 0x00], [0xe9, 0x83, 0x96], [0x94, 0x94, 0x94],
  [0x94, 0x94, 0x94], [0xb7, 0xff, 0x86], [0x73, 0x85, 0xff], [0xcd, 0xcd, 0xcd],
] as const;


function hexColor(value: string): readonly [number, number, number] {
  if (!/^#[0-9a-f]{6}$/i.test(value)) throw new TypeError(`invalid RGB color ${value}`);
  return [
    Number.parseInt(value.slice(1, 3), 16),
    Number.parseInt(value.slice(3, 5), 16),
    Number.parseInt(value.slice(5, 7), 16),
  ];
}


function setPixel(
  pixels: Uint8ClampedArray,
  width: number,
  x: number,
  y: number,
  color: readonly [number, number, number],
): void {
  if (x < 0 || y < 0 || x >= width || y * width * 4 >= pixels.length) return;
  const offset = (y * width + x) * 4;
  pixels[offset] = color[0];
  pixels[offset + 1] = color[1];
  pixels[offset + 2] = color[2];
  pixels[offset + 3] = 0xff;
}


export function composeRoom0Pixels(frame: Room0Frame): Uint8ClampedArray {
  const pixels = new Uint8ClampedArray(frame.width * frame.height * 4);
  const background = hexColor(frame.backgroundColor);
  for (let offset = 0; offset < pixels.length; offset += 4) {
    pixels.set([...background, 0xff], offset);
  }

  for (let cell = 0; cell < 1000; cell += 1) {
    const character = frame.screenCodes[cell];
    const color = C64_PALETTE_RGB[frame.colorCodes[cell] & 0x0f];
    for (let row = 0; row < 8; row += 1) {
      const bits = frame.charset[character * 8 + row];
      for (let column = 0; column < 8; column += 1) {
        if (bits & (0x80 >> column)) {
          setPixel(pixels, frame.width, (cell % 40) * 8 + column,
            Math.floor(cell / 40) * 8 + row, color);
        }
      }
    }
  }

  for (const sprite of frame.sprites) {
    const colors = [
      undefined,
      hexColor(sprite.sharedColors[0]),
      hexColor(sprite.color),
      hexColor(sprite.sharedColors[1]),
    ] as const;
    for (let row = 0; row < sprite.rows.length; row += 1) {
      for (let column = 0; column < sprite.rows[row].length; column += 1) {
        const color = colors[sprite.rows[row][column]];
        if (color) {
          setPixel(pixels, frame.width, sprite.x + column, sprite.y + row, color);
        }
      }
    }
  }
  return pixels;
}
