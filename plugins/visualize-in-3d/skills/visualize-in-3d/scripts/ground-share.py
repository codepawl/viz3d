"""Report how much of a screenshot one flat colour covers.

Usage: uv run --no-project --with pillow python ground-share.py <image> [--levels 24] [--ignore "#f5f5eb"]

Each RGB channel is cut into `levels` steps, so near-identical colours fall in one bucket.
The script prints the largest bucket's share of the frame and its colour. The prototype
quality gate in references/live-embed.md fails when that share is over 0.25.
--ignore (repeatable) leaves out a look's own flat background, such as the paper of a cutaway
plate or the void of a point cloud, before measuring; the share is then of the remaining pixels.
"""

import argparse
import sys
from collections import Counter

from PIL import Image


def near(colour, other, distance=18):
    return all(abs(a - b) <= distance for a, b in zip(colour, other))


def parse_hex(text):
    text = text.lstrip("#")
    return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))


def largest_bucket_share(image_path, levels, ignored=()):
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((640, 640))
    step = 256 // levels
    raw_bytes = image.tobytes()
    pixels = [tuple(raw_bytes[index:index + 3]) for index in range(0, len(raw_bytes), 3)]
    pixels = [pixel for pixel in pixels if not any(near(pixel, colour) for colour in ignored)]
    pixel_count = max(len(pixels), 1)
    buckets = Counter((red // step, green // step, blue // step) for red, green, blue in pixels)
    if not buckets:
        return 0.0, (0, 0, 0)
    bucket, count = buckets.most_common(1)[0]
    centre = tuple(channel * step + step // 2 for channel in bucket)
    return count / pixel_count, centre


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image")
    parser.add_argument("--levels", type=int, default=24)
    parser.add_argument("--ignore", action="append", default=[], help="a look's own background colour as hex")
    arguments = parser.parse_args()
    ignored = [parse_hex(text) for text in arguments.ignore]
    share, colour = largest_bucket_share(arguments.image, arguments.levels, ignored)
    verdict = "FAIL" if share > 0.25 else "PASS"
    print(f"{verdict} largest flat colour covers {share:.3f} of the frame, near #{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}")


if __name__ == "__main__":
    main()
