from __future__ import annotations

import unittest

from PIL import Image

from tools.compare_room0_frames import compare_images, normalize_vice_frame


class CompareRoom0FramesTests(unittest.TestCase):
    def test_counts_pixels_and_channels_that_differ(self) -> None:
        reference = Image.new("RGBA", (2, 1), (0, 0, 0, 255))
        candidate = Image.new("RGBA", (2, 1), (0, 0, 0, 255))
        candidate.putpixel((1, 0), (1, 2, 0, 255))

        result = compare_images(reference, candidate)

        self.assertEqual(1, result.mismatched_pixels)
        self.assertEqual(2, result.mismatched_channels)
        self.assertEqual(2, result.maximum_channel_delta)

    def test_rejects_different_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions"):
            compare_images(
                Image.new("RGBA", (2, 1)),
                Image.new("RGBA", (1, 1)),
            )

    def test_crops_the_vice_active_display_at_verified_offsets(self) -> None:
        screenshot = Image.new("RGBA", (384, 272), (0, 0, 0, 255))
        screenshot.putpixel((32, 35), (1, 2, 3, 255))

        result = normalize_vice_frame(screenshot)

        self.assertEqual((320, 200), result.size)
        self.assertEqual((1, 2, 3, 255), result.getpixel((0, 0)))


if __name__ == "__main__":
    unittest.main()
