export function encodePpm(
  width: number,
  height: number,
  rgba: Uint8ClampedArray,
): Buffer {
  if (rgba.length !== width * height * 4) {
    throw new RangeError("RGBA buffer length does not match PPM dimensions");
  }
  const rgb = Buffer.alloc(width * height * 3);
  for (let source = 0, target = 0; source < rgba.length; source += 4, target += 3) {
    rgb[target] = rgba[source];
    rgb[target + 1] = rgba[source + 1];
    rgb[target + 2] = rgba[source + 2];
  }
  return Buffer.concat([
    Buffer.from(`P6\n${width} ${height}\n255\n`, "ascii"),
    rgb,
  ]);
}
