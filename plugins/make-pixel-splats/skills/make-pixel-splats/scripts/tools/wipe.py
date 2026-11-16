# Season wipe for Pocket Seasons: where a next_NNNN.png exists beside frame_NNNN.png, replace the frame with a
# diagonal wipe from the current season to the next one. The wipe edge moves on the 200 px pixel grid, so it stays a
# crisp stair-step line after the 8x upscale.
#   uv run --no-project --with numpy --with pillow python tools/wipe.py <clip folder> [grid 200]
import sys
from pathlib import Path

import numpy
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
folder = Path(sys.argv[1])
grid = int(sys.argv[2]) if len(sys.argv) > 2 else 200
next_frames = sorted(folder.glob("next_*.png"))
runs = []
for path in next_frames:
    index = int(path.stem.split("_")[1])
    if runs and runs[-1][-1] == index - 1:
        runs[-1].append(index)
    else:
        runs.append([index])
for run in runs:
    for position, index in enumerate(run):
        progress = (position + 1) / (len(run) + 1)
        current = numpy.asarray(Image.open(folder / f"frame_{index:04d}.png").convert("RGB"))
        upcoming = numpy.asarray(Image.open(folder / f"next_{index:04d}.png").convert("RGB"))
        size = current.shape[0]
        cell = size // grid
        rows, columns = numpy.mgrid[0:grid, 0:grid]
        # Top-left to bottom-right: a cell flips once its diagonal position passes the progress line.
        flipped = (rows + columns) / (2 * (grid - 1)) < progress
        mask = numpy.kron(flipped, numpy.ones((cell, cell), dtype=bool))[:size, :size]
        blended = numpy.where(mask[..., None], upcoming, current)
        Image.fromarray(blended.astype(numpy.uint8)).save(folder / f"frame_{index:04d}.png")
        (folder / f"next_{index:04d}.png").unlink()
print(f"wiped {sum(len(run) for run in runs)} frames in {len(runs)} changes")
