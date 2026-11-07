"""Report how much of a screenshot one flat colour covers.

Usage: uv run --no-project --with pillow python ground-share.py <image> [--levels 24]

Each RGB channel is cut into `levels` steps, so near-identical colours fall in one bucket.
The script prints the largest bucket's share of the frame and its colour. The prototype
quality gate in references/live-embed.md fails when that share is over 0.25.
"""

import argparse
import sys
from collections import Counter

from PIL import Image


def largest_bucket_share(image_path, levels):
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((640, 640))
    step = 256 // levels
    raw_bytes = image.tobytes()
    pixel_count = len(raw_bytes) // 3
    buckets = Counter(
        (raw_bytes[index] // step, raw_bytes[index + 1] // step, raw_bytes[index + 2] // step)
        for index in range(0, len(raw_bytes), 3)
    )
    bucket, count = buckets.most_common(1)[0]
    centre = tuple(channel * step + step // 2 for channel in bucket)
    return count / pixel_count, centre


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image")
    parser.add_argument("--levels", type=int, default=24)
    arguments = parser.parse_args()
    share, colour = largest_bucket_share(arguments.image, arguments.levels)
    verdict = "FAIL" if share > 0.25 else "PASS"
    print(f"{verdict} largest flat colour covers {share:.3f} of the frame, near #{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}")


if __name__ == "__main__":
    main()
