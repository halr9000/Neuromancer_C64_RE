#!/usr/bin/env python3
"""Compare normalized room-0 RGBA frames and report exact pixel deltas."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ComparisonResult:
    mismatched_pixels: int
    mismatched_channels: int
    maximum_channel_delta: int


def normalize_vice_frame(screenshot: Image.Image) -> Image.Image:
    if screenshot.size != (384, 272):
        raise ValueError("VICE screenshot must be exactly 384x272")
    return screenshot.convert("RGBA").crop((32, 35, 352, 235))


def compare_images(reference: Image.Image, candidate: Image.Image) -> ComparisonResult:
    reference_rgba = reference.convert("RGBA")
    candidate_rgba = candidate.convert("RGBA")
    if reference_rgba.size != candidate_rgba.size:
        raise ValueError("frame dimensions must match")

    mismatched_pixels = 0
    mismatched_channels = 0
    maximum_channel_delta = 0
    reference_bytes = reference_rgba.tobytes()
    candidate_bytes = candidate_rgba.tobytes()
    for offset in range(0, len(reference_bytes), 4):
        deltas = [
            abs(reference_bytes[offset + channel] - candidate_bytes[offset + channel])
            for channel in range(4)
        ]
        if any(deltas):
            mismatched_pixels += 1
        mismatched_channels += sum(delta != 0 for delta in deltas)
        maximum_channel_delta = max(maximum_channel_delta, *deltas)
    return ComparisonResult(
        mismatched_pixels=mismatched_pixels,
        mismatched_channels=mismatched_channels,
        maximum_channel_delta=maximum_channel_delta,
    )


def create_diff(reference: Image.Image, candidate: Image.Image) -> Image.Image:
    reference_rgba = reference.convert("RGBA")
    candidate_rgba = candidate.convert("RGBA")
    if reference_rgba.size != candidate_rgba.size:
        raise ValueError("frame dimensions must match")
    result = Image.new("RGBA", reference_rgba.size, (0, 0, 0, 255))
    for y in range(reference_rgba.height):
        for x in range(reference_rgba.width):
            if reference_rgba.getpixel((x, y)) != candidate_rgba.getpixel((x, y)):
                result.putpixel((x, y), (255, 0, 255, 255))
    return result


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vice_screenshot", type=Path)
    parser.add_argument("browser_frame", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    reference = normalize_vice_frame(Image.open(args.vice_screenshot))
    candidate = Image.open(args.browser_frame).convert("RGBA")
    comparison = compare_images(reference, candidate)
    reference_path = args.output_directory / "e1_vice_room0_active.png"
    candidate_path = args.output_directory / "e1_browser_room0.png"
    diff_path = args.output_directory / "e1_room0_pixel_diff.png"
    report_path = args.output_directory / "e1_room0_pixel_diff.json"
    reference.save(reference_path)
    candidate.save(candidate_path)
    create_diff(reference, candidate).save(diff_path)
    report = {
        "dimensions": [320, 200],
        "vice_crop": {"left": 32, "top": 35, "width": 320, "height": 200},
        "mismatched_pixels": comparison.mismatched_pixels,
        "mismatched_channels": comparison.mismatched_channels,
        "maximum_channel_delta": comparison.maximum_channel_delta,
        "source_sha256": {
            "vice_screenshot": file_sha256(args.vice_screenshot),
            "browser_frame": file_sha256(args.browser_frame),
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if comparison.mismatched_pixels == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
