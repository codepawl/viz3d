"""Compose the "how pixel-splat art is made" film from the picture layers of plans/howto-layers.mjs.

Beats (notes/howto-video.md): finished piece, clay shapes, sparse to dense splats, colour ramps with swatches,
zoom into the 2x sample grid, before/after wipe of the ink pass, credit. Writes square frames, nearest-upscaled.

Usage: uv run --no-project --with pillow --with numpy python howto_compose.py <layers folder> <out folder> [--fps 24]
"""
import argparse
import os
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Layout is written in 600-unit coordinates; SCALE turns them into real pixels (2 for the 400-grid final), and
# ART_GRID is the art-pixel grid of the layers (200 preview, 400 final).
CANVAS = 600
SCALE = 1
ART_GRID = 200
OUTPUT_SIZE = 1200


def real(value):
    return round(value * SCALE)


class ScaledDraw:
    """ImageDraw that takes layout units and fonts made at SCALE times their layout size."""

    def __init__(self, image):
        self.draw = ImageDraw.Draw(image)

    def _points(self, values):
        return [value * SCALE for value in values]

    def text(self, position, value, font, fill):
        self.draw.text(tuple(self._points(position)), value, font=font, fill=fill)

    def textlength(self, value, font):
        return self.draw.textlength(value, font=font) / SCALE

    def textbbox(self, position, value, font):
        return tuple(number / SCALE for number in self.draw.textbbox(position, value, font=font))

    def rounded_rectangle(self, box, radius, fill):
        self.draw.rounded_rectangle(self._points(box), radius=radius * SCALE, fill=fill)

    def rectangle(self, box, fill, outline=None, width=1):
        self.draw.rectangle(self._points(box), fill=fill, outline=outline, width=max(1, real(width)))

    def line(self, points, fill, width=1):
        self.draw.line([tuple(self._points(point)) for point in points], fill=fill, width=max(1, real(width)))
DURATION = 36
FONT_FOLDERS = ["C:/Windows/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts", "/usr/share/fonts/truetype/dejavu"]


def find_font(environment_name, candidates):
    """Pick a font from HOWTO_FONT_* or the first candidate file that exists on this machine."""
    chosen = os.environ.get(environment_name)
    if chosen:
        return chosen
    for folder in FONT_FOLDERS:
        for name in candidates:
            if os.path.exists(os.path.join(folder, name)):
                return os.path.join(folder, name)
    return candidates[0]


FONT_BOLD = find_font("HOWTO_FONT_BOLD", ["segoeuib.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"])
FONT_REGULAR = find_font("HOWTO_FONT_REGULAR", ["segoeui.ttf", "Arial.ttf", "DejaVuSans.ttf"])
FONT_CODE = find_font("HOWTO_FONT_CODE", ["consola.ttf", "Courier New.ttf", "DejaVuSansMono.ttf"])
BACKGROUND = (8, 10, 22)
INK_TEXT = (240, 236, 220)

PALETTE_HEX = ['#080a16', '#141a33', '#232f5c', '#3a4d8a', '#6079b8', '#9fb2dc',
               '#4a2c18', '#7a4a22', '#a8692c', '#d39a32', '#f0c860', '#fff0c0', '#e0a070']
PALETTE = [tuple(int(value[index:index + 2], 16) for index in (1, 3, 5)) for value in PALETTE_HEX]
SWATCHES = [
    ("stone", [1, 2, 3, 4, 5]),
    ("wheat", [1, 6, 7, 8, 9]),
    ("hay", [6, 7, 8, 9, 10]),
    ("sail", [7, 8, 9, 10, 11]),
    ("water", [2, 3, 4, 5]),
]
LABELS = [
    (0.4, 3.0, "how this pixel art is made"),
    (3.0, 8.0, "1  shapes written as code"),
    (8.0, 13.0, "2  sampled into splats"),
    (13.0, 19.0, "3  one colour ramp per material"),
    (19.0, 22.6, "4  render small, 4 samples a pixel"),
    (22.6, 25.0, "4  each 2x2 block becomes 1 pixel"),
    (25.0, 31.0, "5  palette + body-coloured outline"),
]
CREDIT = "method: @JungleSilicon's ink studio  ·  rebuilt in Crucible"
ZOOM_CENTER = (0.6, 0.47)
EDGE_CENTER = (0.6, 0.42)
# Signed distance shapes from our windmill.js, shortened for the screen.
CODE_LINES = [
    "island = blob(r=1.0) + rock_noise",
    "tower  = taper(r=0.30 -> 0.17, h=1.05)",
    "cap    = cone(r=0.20, h=0.30)",
    "sail   = box(0.30, 0.085) - lattice",
    "field  = box(0.40, 0.27) + tufts",
    "house  = box | gable_roof",
]


def pill(draw, box, alpha=210):
    draw.rounded_rectangle(box, radius=8, fill=(20, 26, 51, alpha))


def draw_code(canvas, time, font):
    # Lines type out one after another from 3.3 s.
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ScaledDraw(overlay)
    line_height = 20
    x0 = 22
    y0 = CANVAS - 22 - len(CODE_LINES) * line_height
    pill(draw, (x0 - 10, y0 - 10, x0 + 330, CANVAS - 14), 200)
    characters = int((time - 3.3) * 55)
    for row, line in enumerate(CODE_LINES):
        visible = line[:max(characters, 0)]
        characters -= len(line) + 4
        if visible:
            name, _, rest = visible.partition("=")
            draw.text((x0, y0 + row * line_height), name, font=font, fill=(240, 200, 96, 255))
            if rest:
                width = draw.textlength(name + "=", font=font)
                draw.text((x0 + draw.textlength(name, font=font), y0 + row * line_height), "=", font=font, fill=(160, 178, 220, 255))
                draw.text((x0 + width, y0 + row * line_height), rest, font=font, fill=(240, 236, 220, 255))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))


def outline_mask(ink_image):
    """Art pixels on the silhouette of the ink image (filled pixel next to background), as a canvas-sized mask."""
    art = np.asarray(ink_image.resize((ART_GRID, ART_GRID), Image.NEAREST)).astype(int)
    filled = np.abs(art - np.array(BACKGROUND)).sum(axis=2) > 24
    padded = np.pad(filled, 1, constant_values=False)
    empty_neighbour = (~padded[:-2, 1:-1]) | (~padded[2:, 1:-1]) | (~padded[1:-1, :-2]) | (~padded[1:-1, 2:])
    edge = filled & empty_neighbour
    return Image.fromarray((edge * 255).astype(np.uint8)).resize((real(CANVAS), real(CANVAS)), Image.NEAREST)


def draw_caption(canvas, text, alpha, font):
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ScaledDraw(overlay)
    width = draw.textlength(text, font=font)
    x = (CANVAS - width) / 2
    y = CANVAS - 46
    pill(draw, (x - 12, y - 6, x + width + 12, y + 28), int(210 * alpha))
    draw.text((x, y), text, font=font, fill=(*INK_TEXT, int(255 * alpha)))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))


def smooth(amount):
    clamped = min(max(amount, 0.0), 1.0)
    return clamped * clamped * (3 - 2 * clamped)


class Layers:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.cache = {}

    def get(self, layer, frame_index):
        # A beat may lack a layer on its first frame; fall back to the nearest earlier frame of that layer.
        for candidate in range(frame_index, max(frame_index - 400, -1), -1):
            path = self.folder / layer / f"f_{candidate:04d}.png"
            if path.exists():
                return Image.open(path).convert("RGB")
        for candidate in range(frame_index, frame_index + 400):
            path = self.folder / layer / f"f_{candidate:04d}.png"
            if path.exists():
                return Image.open(path).convert("RGB")
        raise FileNotFoundError(f"no {layer} frame near {frame_index}")


def fit(image):
    size = real(CANVAS)
    if image.size == (size, size):
        return image
    return image.resize((size, size), Image.NEAREST)


def zoom_crop(image, zoom, center=ZOOM_CENTER):
    size = image.size[0]
    crop = size / zoom
    left = min(max(center[0] * size - crop / 2, 0), size - crop)
    top = min(max(center[1] * size - crop / 2, 0), size - crop)
    region = image.crop((round(left), round(top), round(left + crop), round(top + crop)))
    return region.resize((real(CANVAS), real(CANVAS)), Image.NEAREST), (left, top, crop)


def draw_grid(canvas, crop_box, source_size, cells, color, width):
    """Lines on the boundaries of a grid of `cells` across the source image, mapped through the zoom crop."""
    left, top, crop = crop_box
    draw = ScaledDraw(canvas)
    cell = source_size / cells
    scale = CANVAS / crop
    first = math.floor(left / cell)
    for index in range(first, first + int(crop / cell) + 2):
        position = (index * cell - left) * scale
        if 0 <= position <= CANVAS:
            draw.line([(position, 0), (position, CANVAS)], fill=color, width=width)
    first = math.floor(top / cell)
    for index in range(first, first + int(crop / cell) + 2):
        position = (index * cell - top) * scale
        if 0 <= position <= CANVAS:
            draw.line([(0, position), (CANVAS, position)], fill=color, width=width)


def draw_label(canvas, text, alpha, font):
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ScaledDraw(overlay)
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    x = 22
    y = 22
    draw.rounded_rectangle((x - 10, y - 8, x + width + 12, y + height + 14), radius=8, fill=(20, 26, 51, int(210 * alpha)))
    draw.text((x, y - box[1]), text, font=font, fill=(*INK_TEXT, int(255 * alpha)))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))


def draw_swatches(canvas, amount, font):
    draw = ScaledDraw(canvas)
    cell = 22
    x0 = 22
    y0 = CANVAS - 22 - len(SWATCHES) * (cell + 6)
    if amount > 0:
        draw.rounded_rectangle((x0 - 10, y0 - 10, x0 + 62 + 5 * (cell + 2) + 8, CANVAS - 12), radius=8, fill=(20, 26, 51))
    for row, (name, indices) in enumerate(SWATCHES):
        shown = int(round(len(indices) * smooth(amount * 1.6 - row * 0.15)))
        y = y0 + row * (cell + 6)
        if shown == 0:
            continue
        draw.text((x0, y + 2), name, font=font, fill=INK_TEXT)
        for column in range(shown):
            x = x0 + 62 + column * (cell + 2)
            draw.rectangle((x, y, x + cell, y + cell), fill=PALETTE[indices[column]], outline=(110, 120, 150), width=1)


def draw_credit(canvas, alpha, font):
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ScaledDraw(overlay)
    width = draw.textlength(CREDIT, font=font)
    x = (CANVAS - width) / 2
    pill(draw, (x - 12, CANVAS - 50, x + width + 12, CANVAS - 20), int(220 * alpha))
    draw.text((x, CANVAS - 46), CREDIT, font=font, fill=(*INK_TEXT, int(240 * alpha)))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))


def compose(layers, frame_index, time, fonts):
    if time < 3:
        canvas = fit(layers.get("ink", frame_index))
    elif time < 13:
        canvas = fit(layers.get("clay", frame_index))
        if time < 8:
            draw_code(canvas, time, fonts["code"])
    elif time < 19:
        canvas = fit(layers.get("raw", frame_index))
        draw_swatches(canvas, (time - 13.6) / 2.2, fonts["small"])
    elif time < 25:
        # Zoom into the sample grid: thin lines per sample, bold lines per art pixel (2x2 samples). Then the same
        # spot after the resolve, where each 2x2 block has become one pixel.
        zoom = 1 + 5 * smooth((time - 19.3) / 2.2) - 5 * smooth((time - 24.0) / 0.9)
        if time >= 22.6:
            source = layers.get("ink", frame_index)
            canvas, crop_box = zoom_crop(source, zoom)
            if zoom > 3:
                draw_grid(canvas, crop_box, source.size[0], ART_GRID, (8, 10, 22), 1)
        else:
            samples = layers.get("samples", frame_index)
            canvas, crop_box = zoom_crop(samples, zoom)
            if zoom > 3:
                fade = smooth((zoom - 3) / 1.5)
                thin = tuple(int(BACKGROUND[channel] * fade + 128 * (1 - fade)) for channel in range(3))
                draw_grid(canvas, crop_box, samples.size[0], ART_GRID * 2, thin, 1)
                draw_grid(canvas, crop_box, samples.size[0], ART_GRID, (240, 236, 220), 2)
    elif time < 31:
        edge_zoom = 1 + 1.8 * smooth((time - 25.2) / 0.8) - 1.8 * smooth((time - 29.6) / 0.9)
        raw = zoom_crop(fit(layers.get("raw", frame_index)), edge_zoom, EDGE_CENTER)[0]
        full_ink = fit(layers.get("ink", frame_index))
        ink = zoom_crop(full_ink, edge_zoom, EDGE_CENTER)[0]
        if 27.6 < time < 29.0 and int((time - 27.6) * 4) % 2 == 0:
            mask = zoom_crop(outline_mask(full_ink).convert("RGB"), edge_zoom, EDGE_CENTER)[0].convert("L")
            ink.paste(Image.new("RGB", ink.size, (255, 240, 192)), (0, 0), mask)
        # Wipe from right to left to reveal the ink look, hold on the split, then finish.
        split = CANVAS * (1 - 0.5 * smooth((time - 25.5) / 1.6) - 0.5 * smooth((time - 29.2) / 1.2))
        canvas = raw.copy()
        cut = real(split)
        if cut < real(CANVAS):
            canvas.paste(ink.crop((cut, 0, real(CANVAS), real(CANVAS))), (cut, 0))
            ScaledDraw(canvas).line([(split, 0), (split, CANVAS)], fill=INK_TEXT, width=2)
        if 27.6 < time < 29.0:
            draw_caption(canvas, "edge pixels take a darker tone of their own colour", 1.0, fonts["small"])
        elif 26.2 < time < 29.4:
            draw = ScaledDraw(canvas)
            for text_value, x in (("raw splats", 22), ("ink pass", CANVAS - 22 - draw.textlength("ink pass", font=fonts["label"]))):
                width = draw.textlength(text_value, font=fonts["label"])
                draw.rounded_rectangle((x - 10, CANVAS - 52, x + width + 10, CANVAS - 16), radius=8, fill=(20, 26, 51))
                draw.text((x, CANVAS - 50), text_value, font=fonts["label"], fill=INK_TEXT)
    else:
        canvas = fit(layers.get("ink", frame_index))
        draw_credit(canvas, smooth((time - 31.6) / 0.8), fonts["small"])
    for start, end, text in LABELS:
        if start <= time < end:
            alpha = smooth((time - start) / 0.3) * (1 - smooth((time - (end - 0.3)) / 0.3))
            draw_label(canvas, text, alpha, fonts["label"])
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("layers")
    parser.add_argument("out")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--scale", type=int, default=1, help="2 for layers rendered at the 400 grid")
    parser.add_argument("--grid", type=int, default=200, help="art-pixel grid of the layers")
    arguments = parser.parse_args()
    global SCALE, ART_GRID
    SCALE = arguments.scale
    ART_GRID = arguments.grid
    layers = Layers(arguments.layers)
    output = Path(arguments.out)
    output.mkdir(parents=True, exist_ok=True)
    fonts = {"label": ImageFont.truetype(FONT_BOLD, real(22)), "small": ImageFont.truetype(FONT_REGULAR, real(17)), "code": ImageFont.truetype(FONT_CODE, real(15))}
    total = DURATION * arguments.fps
    for frame_index in range(total):
        time = frame_index / arguments.fps
        canvas = compose(layers, frame_index, time, fonts)
        if canvas.size[0] != OUTPUT_SIZE:
            canvas = canvas.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.NEAREST)
        canvas.save(output / f"c_{frame_index:04d}.png")
    print("composed", total, "frames into", output)


if __name__ == "__main__":
    main()
