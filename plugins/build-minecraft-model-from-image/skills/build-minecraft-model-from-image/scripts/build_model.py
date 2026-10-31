# /// script
# dependencies = ["numpy", "pillow"]
# ///
"""Runs an object script, then checks, exports and renders it.

  build_model.py object.py --out folder [--no-render] [--samples 64] [--turntable 48] [--resolution 800]

The object script defines:
  SOURCE = {"image": "source.jpg", "mask": "read/mask.png", "yaw": 30, "pitch": 10}  # the view the picture was taken from
  def build(kit): ... return model   # kit has BlockModel and Material; see block_kit.py

Writes model.glb, viewer.html, checks.json, overlay.png (picture mask vs model), compare.png (picture beside renders) and
views/*.png with transparent backgrounds. Exit code 1 when a hard check fails: floating parts or an extruded model.
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy
from PIL import Image, ImageDraw

SCRIPT_FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_FOLDER))

import block_export  # noqa: E402
import block_kit  # noqa: E402


def find_blender():
    """BLENDER_PATH wins, then PATH, then the installer's default folder on Windows and macOS."""
    from_environment = os.environ.get("BLENDER_PATH") or shutil.which("blender")
    if from_environment:
        return from_environment
    program_files = Path(os.environ.get("ProgramFiles", "Program Files"))
    installed = sorted(program_files.glob("Blender Foundation/Blender */blender.exe"))
    if installed:
        return str(installed[-1])
    mac_application = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if mac_application.exists():
        return str(mac_application)
    return "blender"


BLENDER_PATH = find_blender()
GPU_BUSY_PERCENT = 40
BELOW_NORMAL_PRIORITY = 0x00004000
BACKDROP = (230, 226, 216)
TOUCH_TOLERANCE = 0.02
MOST_PARTS = 120
TINY_SHARE = 0.35


def find_groups(bounds):
    """Boxes whose bounds touch are one group. Rotated boxes use their bounds, so this errs toward 'connected'."""
    parents = list(range(len(bounds)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for first in range(len(bounds)):
        for second in range(first + 1, len(bounds)):
            low_a, high_a = bounds[first]
            low_b, high_b = bounds[second]
            if numpy.all(low_a <= high_b + TOUCH_TOLERANCE) and numpy.all(low_b <= high_a + TOUCH_TOLERANCE):
                parents[find(first)] = find(second)
    groups = {}
    for index in range(len(bounds)):
        groups.setdefault(find(index), []).append(index)
    return sorted(groups.values(), key=len, reverse=True)


def find_coplanar_overlaps(boxes):
    """Same-facing faces in one plane that overlap flicker in any viewer. Only unrotated boxes are compared."""
    clashes = []
    plain = [box for box in boxes if box.rotation is None]
    for first_index, first in enumerate(plain):
        for second in plain[first_index + 1:]:
            for axis in range(3):
                others = [index for index in range(3) if index != axis]
                overlap = all(
                    min(first.low[other] + first.size[other], second.low[other] + second.size[other])
                    - max(first.low[other], second.low[other]) > 0.01
                    for other in others)
                if not overlap:
                    continue
                same_low = abs(first.low[axis] - second.low[axis]) < 0.01
                same_high = abs(first.low[axis] + first.size[axis] - second.low[axis] - second.size[axis]) < 0.01
                if same_low or same_high:
                    clashes.append(f'{first.name or first.low} / {second.name or second.low} on axis {"xyz"[axis]}')
    return clashes


def convex_hull(points):
    ordered = sorted(set(map(tuple, points)))
    if len(ordered) < 3:
        return ordered

    def cross(origin, first, second):
        return (first[0] - origin[0]) * (second[1] - origin[1]) - (first[1] - origin[1]) * (second[0] - origin[0])

    lower = []
    for point in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def project(points, yaw_degrees, pitch_degrees):
    """Orthographic screen position for a camera at this yaw and pitch; screen y grows downward."""
    yaw = numpy.radians(yaw_degrees)
    pitch = numpy.radians(pitch_degrees)
    screen_x = points[:, 0] * numpy.cos(yaw) - points[:, 2] * numpy.sin(yaw)
    forward = points[:, 0] * numpy.sin(yaw) + points[:, 2] * numpy.cos(yaw)
    screen_y = points[:, 1] * numpy.cos(pitch) - forward * numpy.sin(pitch)
    return numpy.stack([screen_x, -screen_y], axis=1)


def compare_silhouette(boxes, mask, yaw, pitch, overlay_path):
    """Fit the model's silhouette into the mask's box. Overlay: grey = both, red = picture only, blue = model only."""
    rows = numpy.where(mask.any(axis=1))[0]
    columns = numpy.where(mask.any(axis=0))[0]
    crop = mask[rows[0]:rows[-1] + 1, columns[0]:columns[-1] + 1]
    scale = 400 / max(crop.shape)
    width = max(int(crop.shape[1] * scale), 1)
    height = max(int(crop.shape[0] * scale), 1)
    target = numpy.asarray(Image.fromarray((crop * 255).astype(numpy.uint8)).resize((width, height))) > 127
    projected = [project(box.corners(), yaw, pitch) for box in boxes]
    together = numpy.vstack(projected)
    low = together.min(axis=0)
    extent = together.max(axis=0) - low
    fit = min(width / max(extent[0], 1e-6), height / max(extent[1], 1e-6))
    offset = numpy.array([(width - extent[0] * fit) / 2, (height - extent[1] * fit) / 2])
    canvas = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(canvas)
    for points in projected:
        hull = convex_hull(((points - low) * fit + offset).tolist())
        draw.polygon([tuple(point) for point in hull], fill=1)
    model = numpy.asarray(canvas, dtype=bool)
    overlap = float((model & target).sum() / max((model | target).sum(), 1))
    overlay = numpy.full((height, width, 3), 255, dtype=numpy.uint8)
    overlay[model & target] = (190, 190, 190)
    overlay[target & ~model] = (230, 40, 40)
    overlay[model & ~target] = (40, 90, 230)
    Image.fromarray(overlay).save(overlay_path)
    return overlap


def run_checks(model, source, output_folder):
    boxes = model.boxes
    bounds = [(box.corners().min(axis=0), box.corners().max(axis=0)) for box in boxes]
    groups = find_groups(bounds)
    everything = numpy.vstack([box.corners() for box in boxes])
    extents = everything.max(axis=0) - everything.min(axis=0)
    front_areas = {}
    for box in boxes:
        key = (round(box.low[2], 2), box.size[2])
        front_areas[key] = front_areas.get(key, 0) + box.size[0] * box.size[1]
    prism = max(front_areas.values()) / sum(front_areas.values())
    tiny = sum(1 for box in boxes if box.size[0] * box.size[1] * box.size[2] <= 2)
    checks = {
        "extent_units_xyz": [round(float(value), 1) for value in extents],
        "boxes": len(boxes),
        "groups": len(groups),
        "prism_fraction": round(float(prism), 3),
        "tiny_box_share": round(tiny / len(boxes), 3),
        "depth_to_size": round(float(extents[2] / max(extents[0], extents[1])), 3),
    }
    if source and source.get("mask"):
        mask = numpy.asarray(Image.open(source["mask"]).convert("L")) > 127
        checks["silhouette_overlap"] = round(compare_silhouette(
            boxes, mask, source.get("yaw", 0), source.get("pitch", 0), output_folder / "overlay.png"), 3)
    failures = []
    if len(groups) > 1:
        names = [[boxes[index].name or str(boxes[index].low) for index in group][:4] for group in groups[1:]]
        failures.append(f"{len(groups) - 1} floating part group(s): {names}")
    if prism > 0.92:
        failures.append(f"prism_fraction {prism:.2f}: every part shares one depth, the model is an extrusion")
    warnings = []
    if len(boxes) > MOST_PARTS:
        warnings.append(f"{len(boxes)} boxes: heading back toward voxels, merge parts and paint the detail instead")
    if tiny / len(boxes) > TINY_SHARE:
        warnings.append("over a third of the boxes are tiny: paint that detail on a face instead")
    clashes = find_coplanar_overlaps(boxes)
    if clashes:
        warnings.append(f"{len(clashes)} coplanar overlap(s) will flicker: {clashes[:6]}")
    if checks["depth_to_size"] < 0.2:
        warnings.append("depth is under a fifth of the size: check it against the object's real depth")
    if checks.get("silhouette_overlap", 1.0) < 0.65:
        warnings.append("silhouette_overlap under 0.65: open overlay.png, proportions or yaw/pitch are off (thin frames score low anyway)")
    checks["failures"] = failures
    checks["warnings"] = warnings
    return checks


def choose_device(requested):
    """auto stays off the GPU while someone else is using it, so a render never fights another job."""
    if requested != "auto":
        return requested
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return "cpu"
    result = subprocess.run([nvidia_smi, "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True)
    try:
        return "cpu" if int(result.stdout.split()[0]) >= GPU_BUSY_PERCENT else "gpu"
    except (IndexError, ValueError):
        return "cpu"


def render_views(glb_path, render_folder, views, samples, resolution, device="auto"):
    if not Path(BLENDER_PATH).exists():
        raise SystemExit(f"Blender not found at {BLENDER_PATH}; set BLENDER_PATH")
    render_folder.mkdir(parents=True, exist_ok=True)
    views_path = render_folder / "views.json"
    views_path.write_text(json.dumps(views), encoding="utf-8")
    command = [BLENDER_PATH, "-b", "--factory-startup", "-t", "6", "-P", str(SCRIPT_FOLDER / "render_blender.py"), "--",
               str(glb_path), str(render_folder), str(views_path), str(samples), str(resolution), choose_device(device)]
    flags = BELOW_NORMAL_PRIORITY if os.name == "nt" else 0
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=flags)
    missing = [view["name"] for view in views if not (render_folder / f'{view["name"]}.png').exists()]
    if result.returncode != 0 or missing:
        print(result.stdout[-2500:])
        print(result.stderr[-1500:])
        raise SystemExit(f"Blender render failed, missing: {missing}")


def flatten_on_backdrop(path):
    render = Image.open(path).convert("RGBA")
    backdrop = Image.new("RGBA", render.size, BACKDROP + (255,))
    return Image.alpha_composite(backdrop, render).convert("RGB")


def crop_source(source, panel_size):
    picture = Image.open(source["image"]).convert("RGB")
    if source.get("mask"):
        mask = numpy.asarray(Image.open(source["mask"]).convert("L")) > 127
        rows = numpy.where(mask.any(axis=1))[0]
        columns = numpy.where(mask.any(axis=0))[0]
        margin = int(max(rows[-1] - rows[0], columns[-1] - columns[0]) * 0.12)
        picture = picture.crop((max(columns[0] - margin, 0), max(rows[0] - margin, 0),
                                min(columns[-1] + margin, picture.width), min(rows[-1] + margin, picture.height)))
    picture.thumbnail((panel_size, panel_size))
    panel = Image.new("RGB", (panel_size, panel_size), BACKDROP)
    panel.paste(picture, ((panel_size - picture.width) // 2, (panel_size - picture.height) // 2))
    return panel


def compose_comparison(source, render_folder, views, path, panel_size=420):
    panels = []
    if source and source.get("image"):
        panels.append(("picture", crop_source(source, panel_size)))
    for view in views:
        panels.append((view["name"], flatten_on_backdrop(render_folder / f'{view["name"]}.png').resize((panel_size, panel_size))))
    columns = 3
    rows = (len(panels) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * panel_size, rows * panel_size), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, panel) in enumerate(panels):
        position = ((index % columns) * panel_size, (index // columns) * panel_size)
        sheet.paste(panel, position)
        draw.text((position[0] + 8, position[1] + 6), label, fill=(30, 30, 30))
    sheet.save(path)


def render_turntable(glb_path, output_folder, frame_count, samples, resolution, pitch, device="auto"):
    frames_folder = output_folder / "turntable_frames"
    if frames_folder.exists():
        shutil.rmtree(frames_folder)
    views = [{"name": f"frame_{index:04d}", "yaw": 360 * index / frame_count, "pitch": pitch} for index in range(frame_count)]
    render_views(glb_path, frames_folder, views, samples, resolution, device)
    for view in views:
        frame_path = frames_folder / f'{view["name"]}.png'
        flatten_on_backdrop(frame_path).save(frame_path)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("ffmpeg not found: frames stay in", frames_folder)
        return
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "24", "-i", str(frames_folder / "frame_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(output_folder / "turntable.mp4")], check=True)
    shutil.rmtree(frames_folder)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("object_script")
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--resolution", type=int, default=800)
    parser.add_argument("--device", choices=["auto", "gpu", "cpu"], default="auto", help="auto uses the CPU while the GPU is busy")
    parser.add_argument("--turntable", type=int, default=0, help="frames of a turntable.mp4 at 24 fps")
    arguments = parser.parse_args()

    object_path = Path(arguments.object_script).resolve()
    output_folder = Path(arguments.out)
    output_folder.mkdir(parents=True, exist_ok=True)
    specification = importlib.util.spec_from_file_location("block_object_script", object_path)
    object_module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(object_module)
    source = dict(getattr(object_module, "SOURCE", {}))
    for key in ("image", "mask"):
        if key in source and not Path(source[key]).is_absolute():
            source[key] = str(object_path.parent / source[key])
    model = object_module.build(block_kit)

    glb_path = output_folder / "model.glb"
    export_stats = block_export.write_glb(model, glb_path)
    block_export.write_viewer(glb_path, output_folder / "viewer.html", object_path.stem)
    checks = run_checks(model, source, output_folder)
    checks.update(export_stats)
    (output_folder / "checks.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")
    print(json.dumps(checks))

    if not arguments.no_render:
        yaw = source.get("yaw", 30)
        pitch = source.get("pitch", 12)
        views = [
            {"name": "same_view", "yaw": yaw, "pitch": pitch},
            {"name": "front", "yaw": 0, "pitch": 6},
            {"name": "right", "yaw": 90, "pitch": 6},
            {"name": "back", "yaw": 180, "pitch": 12},
            {"name": "left_above", "yaw": -55, "pitch": 38},
        ]
        render_folder = output_folder / "views"
        render_views(glb_path, render_folder, views, arguments.samples, arguments.resolution, arguments.device)
        compose_comparison(source, render_folder, views, output_folder / "compare.png")
        if arguments.turntable:
            render_turntable(glb_path, output_folder, arguments.turntable, arguments.samples, arguments.resolution, 16, arguments.device)
    if checks["failures"]:
        print("FAILED:", "; ".join(checks["failures"]))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
