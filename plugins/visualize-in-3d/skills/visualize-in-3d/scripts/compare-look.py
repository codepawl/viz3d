"""Compare a render's brightness and colour strength with its style reference.

Usage: uv run --no-project --with pillow python compare-look.py <reference> <render> [--tolerance 0.10]

Both images are shrunk to 640 px. The script prints the median, 10th and 90th percentile
luminance and the mean saturation of each, then the render's ratio to the reference. It fails
when the median luminance or the mean saturation differs from the reference by more than the
tolerance. Crop UI out of both images first when the UI covers much of either frame.
"""

import argparse
import sys

from PIL import Image


def measure(image_path):
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((640, 640))
    luminance = sorted(image.convert("L").tobytes())
    saturation = image.convert("HSV").tobytes()[1::3]
    count = len(luminance)
    return {
        "median": luminance[count // 2],
        "p10": luminance[count // 10],
        "p90": luminance[(9 * count) // 10],
        "saturation": sum(saturation) / len(saturation),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reference")
    parser.add_argument("render")
    parser.add_argument("--tolerance", type=float, default=0.10)
    arguments = parser.parse_args()
    reference = measure(arguments.reference)
    render = measure(arguments.render)
    for name, values in (("reference", reference), ("render", render)):
        print(
            f"{name:9} luminance median {values['median']:3} p10 {values['p10']:3} p90 {values['p90']:3}"
            f"  saturation {values['saturation']:.0f}"
        )
    brightness_ratio = render["median"] / max(reference["median"], 1)
    saturation_ratio = render["saturation"] / max(reference["saturation"], 1)
    failures = []
    if abs(brightness_ratio - 1) > arguments.tolerance:
        failures.append("darker" if brightness_ratio < 1 else "brighter")
    if abs(saturation_ratio - 1) > arguments.tolerance:
        failures.append("duller" if saturation_ratio < 1 else "more saturated")
    verdict = "FAIL " + ", ".join(failures) if failures else "PASS"
    print(f"{verdict}: brightness x{brightness_ratio:.2f}, saturation x{saturation_ratio:.2f} of the reference")


if __name__ == "__main__":
    main()
