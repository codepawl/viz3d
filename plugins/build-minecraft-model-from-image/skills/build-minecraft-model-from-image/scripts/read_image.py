# /// script
# dependencies = ["numpy", "pillow", "opencv-python-headless"]
# ///
"""Turn a picture into what a builder reads: object mask, palette, and a blueprint in block coordinates.

  read_image.py picture.jpg --blocks 24 --out read/ [--box x0,y0,x1,y1] [--polygon "x,y x,y ..."] [--colours 14]
                [--clear-background 18]

--blocks is the object's height in model units; 16 to 32 is the Minecraft range. --box is the object's pixel rectangle (GrabCut starts from it);
without it the mask comes from the whole picture, which fails on busy backgrounds. --polygon overrides the mask by hand.
Writes mask.png, blueprint.png (pixelated at block resolution with a ruler), palette.png and rows.json.
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy
from PIL import Image, ImageDraw


def make_mask(picture, box, polygon):
    height, width = picture.shape[:2]
    if polygon:
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).polygon(polygon, fill=255)
        return numpy.asarray(mask) > 0
    if box is None:
        margin = max(min(width, height) // 40, 2)
        box = (margin, margin, width - margin, height - margin)
    labels = numpy.zeros((height, width), dtype=numpy.uint8)
    background_model = numpy.zeros((1, 65), dtype=numpy.float64)
    foreground_model = numpy.zeros((1, 65), dtype=numpy.float64)
    rectangle = (box[0], box[1], box[2] - box[0], box[3] - box[1])
    bgr = cv2.cvtColor(picture, cv2.COLOR_RGB2BGR)
    cv2.grabCut(bgr, labels, rectangle, background_model, foreground_model, 6, cv2.GC_INIT_WITH_RECT)
    mask = (labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD)
    count, components, statistics, _ = cv2.connectedComponentsWithStats(mask.astype(numpy.uint8), connectivity=8)
    if count > 1:
        largest = 1 + int(numpy.argmax(statistics[1:, cv2.CC_STAT_AREA]))
        mask = components == largest
    return mask


def clear_background(picture, mask, box, tolerance):
    """Drop mask pixels close to the colours on the box's own border. Opens holes GrabCut keeps: inside a handle, between slats."""
    height, width = picture.shape[:2]
    left, top, right, bottom = box if box else (0, 0, width, height)
    ring = numpy.concatenate([picture[top:top + 6, left:right].reshape(-1, 3), picture[bottom - 6:bottom, left:right].reshape(-1, 3),
                              picture[top:bottom, left:left + 6].reshape(-1, 3), picture[top:bottom, right - 6:right].reshape(-1, 3)])
    ring_lab = cv2.cvtColor(ring.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(numpy.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(ring_lab, 4, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    shares = numpy.bincount(labels.ravel(), minlength=4) / len(labels)
    centers = centers[shares >= 0.12]  # a thin object crossing the ring must not count as background
    picture_lab = cv2.cvtColor(picture, cv2.COLOR_RGB2LAB).astype(numpy.float32)
    distances = numpy.min(numpy.linalg.norm(picture_lab[:, :, None, :] - centers[None, None, :, :], axis=3), axis=2)
    cleared = mask & (distances > tolerance)
    count, components, statistics, _ = cv2.connectedComponentsWithStats(cleared.astype(numpy.uint8), connectivity=8)
    if count > 1:
        largest = 1 + int(numpy.argmax(statistics[1:, cv2.CC_STAT_AREA]))
        cleared = components == largest
    return cleared


def extract_palette(picture, mask, colour_count):
    pixels = picture[mask]
    if len(pixels) > 60000:
        step = len(pixels) // 60000
        pixels = pixels[::step]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(numpy.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5)
    _, labels, centers = cv2.kmeans(lab, colour_count, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
    coverage = numpy.bincount(labels.ravel(), minlength=colour_count) / len(labels)
    rgb = cv2.cvtColor(centers.astype(numpy.uint8).reshape(-1, 1, 3), cv2.COLOR_LAB2RGB).reshape(-1, 3)
    swatches = []
    for colour, share, center in zip(rgb, coverage, centers):
        swatches.append({"hex": "#%02x%02x%02x" % tuple(int(channel) for channel in colour),
                         "share": round(float(share), 3), "lightness": int(center[0])})
    swatches.sort(key=lambda swatch: -swatch["lightness"])
    return swatches


def draw_palette(swatches, path):
    sheet = Image.new("RGB", (120 * len(swatches), 90), "white")
    draw = ImageDraw.Draw(sheet)
    for index, swatch in enumerate(swatches):
        draw.rectangle((index * 120, 0, index * 120 + 119, 62), fill=swatch["hex"])
        draw.text((index * 120 + 4, 66), f'{swatch["hex"]} {swatch["share"]:.0%}', fill="black")
    sheet.save(path)


def draw_blueprint(picture, mask, blocks_high, path):
    rows_with_object = numpy.where(mask.any(axis=1))[0]
    columns_with_object = numpy.where(mask.any(axis=0))[0]
    top = int(rows_with_object[0])
    bottom = int(rows_with_object[-1]) + 1
    left = int(columns_with_object[0])
    right = int(columns_with_object[-1]) + 1
    pixels_per_block = (bottom - top) / blocks_high
    blocks_wide = max(int(round((right - left) / pixels_per_block)), 1)
    crop = picture[top:bottom, left:right]
    crop_mask = mask[top:bottom, left:right].astype(numpy.float32)
    small = cv2.resize(crop, (blocks_wide, blocks_high), interpolation=cv2.INTER_AREA)
    small_mask = cv2.resize(crop_mask, (blocks_wide, blocks_high), interpolation=cv2.INTER_AREA)
    cell = max(min(1100 // max(blocks_wide, blocks_high), 26), 8)
    margin = 34
    sheet = Image.new("RGB", (blocks_wide * cell + margin * 2, blocks_high * cell + margin * 2), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)
    for column in range(blocks_wide):
        for row in range(blocks_high):
            x0 = margin + column * cell
            y0 = margin + row * cell
            if small_mask[row, column] >= 0.5:
                draw.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=tuple(int(c) for c in small[row, column]))
            else:
                faded = tuple(int(c * 0.35 + 236 * 0.65) for c in small[row, column])
                draw.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=faded)
    for column in range(0, blocks_wide + 1, 5):
        x_position = margin + column * cell
        draw.line((x_position, margin, x_position, margin + blocks_high * cell), fill=(255, 0, 90), width=1)
        draw.text((x_position - 6, 16), str(column), fill="black")
        draw.text((x_position - 6, margin + blocks_high * cell + 6), str(column), fill="black")
    for height in range(0, blocks_high + 1, 5):
        y_position = margin + (blocks_high - height) * cell
        draw.line((margin, y_position, margin + blocks_wide * cell, y_position), fill=(255, 0, 90), width=1)
        draw.text((8, y_position - 6), str(height), fill="black")
        draw.text((margin + blocks_wide * cell + 6, y_position - 6), str(height), fill="black")
    sheet.save(path)
    rows = {}
    for height in range(blocks_high):
        row = blocks_high - 1 - height
        filled = numpy.where(small_mask[row] >= 0.5)[0]
        if len(filled) == 0:
            continue
        runs = []
        run_start = int(filled[0])
        previous = int(filled[0])
        for column in filled[1:]:
            column = int(column)
            if column != previous + 1:
                runs.append([run_start, previous])
                run_start = column
            previous = column
        runs.append([run_start, previous])
        rows[height] = runs
    return {"blocks_wide": blocks_wide, "blocks_high": blocks_high, "object_box": [left, top, right, bottom],
            "pixels_per_block": round(pixels_per_block, 2), "rows_from_ground": rows}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--blocks", type=int, default=24)
    parser.add_argument("--out", required=True)
    parser.add_argument("--box")
    parser.add_argument("--polygon")
    parser.add_argument("--colours", type=int, default=14)
    parser.add_argument("--clear-background", type=float, help="Lab distance, about 12 to 25; for plain backgrounds only")
    arguments = parser.parse_args()

    output_folder = Path(arguments.out)
    output_folder.mkdir(parents=True, exist_ok=True)
    picture = numpy.asarray(Image.open(arguments.image).convert("RGB"))
    box = [int(value) for value in arguments.box.split(",")] if arguments.box else None
    polygon = None
    if arguments.polygon:
        polygon = [tuple(int(value) for value in point.split(",")) for point in arguments.polygon.split()]
    mask = make_mask(picture, box, polygon)
    if arguments.clear_background:
        mask = clear_background(picture, mask, box, arguments.clear_background)
    if mask.sum() < 100:
        raise SystemExit("mask is empty: pass a tighter --box or a --polygon")
    Image.fromarray((mask * 255).astype(numpy.uint8)).save(output_folder / "mask.png")
    swatches = extract_palette(picture, mask, arguments.colours)
    draw_palette(swatches, output_folder / "palette.png")
    blueprint = draw_blueprint(picture, mask, arguments.blocks, output_folder / "blueprint.png")
    blueprint["palette"] = swatches
    (output_folder / "rows.json").write_text(json.dumps(blueprint, indent=1), encoding="utf-8")
    print(f'blocks {blueprint["blocks_wide"]} wide x {blueprint["blocks_high"]} high, '
          f'mask covers {mask.mean():.0%} of the picture')
    print("palette", " ".join(f'{swatch["hex"]}:{swatch["share"]:.0%}' for swatch in swatches))
    print("wrote", output_folder)


if __name__ == "__main__":
    main()
