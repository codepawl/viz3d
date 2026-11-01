"""Check a house plan file and overlay it, or the built model, on the source drawing.

Run with: uv run --no-project --with pillow --with numpy --with scipy python plan_check.py <command> plan.json

Commands:
  check                  validate the plan file: walls, openings, rooms, circulation, printed dimensions, provenance
  overlay                draw the plan on the source image and score it against the ink
  asbuilt <section.json> score the wall section cut from the built Blender model, and draw it on the source image
Exit code 0 means every gate passed. Paths in the plan resolve from the plan file's folder.
"""

import json
import math
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

METRES_PER_UNIT = {"m": 1.0, "ft": 0.3048}
MINIMUM_SCORE = 0.70
MAXIMUM_BEST_OFFSET_METRES = 0.16
MAXIMUM_CALIBRATION_ERROR_METRES = 0.12
DIMENSION_TOLERANCE_METRES = 0.10
SWEEP_REACH_METRES = 0.60
SWEEP_STEP_METRES = 0.04
INK_TOLERANCE_METRES = 0.07


def load_plan(plan_path):
    plan_path = pathlib.Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["_folder"] = plan_path.parent
    plan["_scale"] = METRES_PER_UNIT[plan.get("units", "m")]
    return plan


def distance(point_a, point_b):
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def closest_on_segment(point, start, end):
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length_squared = delta_x * delta_x + delta_y * delta_y
    if length_squared == 0:
        return start, 0.0
    fraction = ((point[0] - start[0]) * delta_x + (point[1] - start[1]) * delta_y) / length_squared
    fraction = max(0.0, min(1.0, fraction))
    return (start[0] + fraction * delta_x, start[1] + fraction * delta_y), fraction


def point_in_polygon(point, polygon):
    inside = False
    count = len(polygon)
    for index in range(count):
        x_a, y_a = polygon[index]
        x_b, y_b = polygon[(index + 1) % count]
        crosses = (y_a > point[1]) != (y_b > point[1])
        if crosses and point[0] < (x_b - x_a) * (point[1] - y_a) / (y_b - y_a) + x_a:
            inside = not inside
    return inside


def polygon_area(polygon):
    total = 0.0
    count = len(polygon)
    for index in range(count):
        x_a, y_a = polygon[index]
        x_b, y_b = polygon[(index + 1) % count]
        total += x_a * y_b - x_b * y_a
    return abs(total) / 2


def wall_frame(wall):
    start, end = wall["a"], wall["b"]
    length = distance(start, end)
    direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    normal = (-direction[1], direction[0])
    return start, direction, normal, length


def opening_range(opening):
    if "from" in opening:
        return opening["from"], opening["to"]
    half_width = opening["width"] / 2
    return opening["at"] - half_width, opening["at"] + half_width


def wall_levels(wall):
    """Storeys a wall stands on: an outer wall may run through several, numbered from 1."""
    return wall.get("levels") or [wall.get("level", 1)]


def room_at(plan, point, level=1):
    for room in plan.get("rooms", []):
        if room.get("level", 1) == level and point_in_polygon(point, room["poly"]):
            return room["name"]
    return None


def check_walls(plan, faults):
    scale = plan["_scale"]
    walls = plan.get("walls", [])
    identifiers = [wall["id"] for wall in walls]
    for identifier in identifiers:
        if identifiers.count(identifier) > 1:
            faults.append(f"wall id {identifier} is used twice")
    for wall in walls:
        if distance(wall["a"], wall["b"]) * scale < 0.05:
            faults.append(f"wall {wall['id']} has no length")
        thickness = wall["t"] * scale
        if not 0.04 <= thickness <= 1.2:
            faults.append(f"wall {wall['id']} is {thickness:.2f} m thick; expected 0.04 to 1.2")
        if wall.get("free_end"):
            continue
        for end_name in ("a", "b"):
            joined = False
            for other in walls:
                if other is wall or not set(wall_levels(wall)) & set(wall_levels(other)):
                    continue
                nearest, _ = closest_on_segment(wall[end_name], other["a"], other["b"])
                reach = other["t"] / 2 + 0.12 / scale
                if distance(wall[end_name], nearest) <= reach:
                    joined = True
                    break
            if not joined:
                faults.append(f"wall {wall['id']} end {end_name} touches nothing (mark free_end if it stands alone)")


def check_openings(plan, faults):
    scale = plan["_scale"]
    walls = {wall["id"]: wall for wall in plan.get("walls", [])}
    per_wall = {}
    for opening in plan.get("openings", []):
        wall = walls.get(opening["wall"])
        if wall is None:
            faults.append(f"opening {opening['id']} names missing wall {opening['wall']}")
            continue
        start_along, end_along = opening_range(opening)
        length = distance(wall["a"], wall["b"])
        if start_along < -0.001 or end_along > length + 0.001 or end_along <= start_along:
            faults.append(f"opening {opening['id']} runs {start_along:.2f}..{end_along:.2f} on a wall {length:.2f} long")
        width_metres = (end_along - start_along) * scale
        head_metres = opening.get("head", 0) * scale
        sill_metres = opening.get("sill", 0) * scale
        kind = opening.get("kind")
        if kind == "door" and not 0.40 <= width_metres <= 2.2:
            faults.append(f"door {opening['id']} is {width_metres:.2f} m wide")
        if kind == "door" and not 1.45 <= head_metres - sill_metres <= 2.7:
            faults.append(f"door {opening['id']} is {head_metres - sill_metres:.2f} m tall")
        if kind == "window" and head_metres <= sill_metres:
            faults.append(f"window {opening['id']} head is at or under its sill")
        per_wall.setdefault(opening["wall"], []).append((start_along, end_along, opening["id"], opening.get("sill", 0), opening.get("head", 0)))
    for wall_id, spans in per_wall.items():
        for index, first in enumerate(spans):
            for second in spans[index + 1:]:
                overlap_along = first[0] < second[1] - 0.001 and second[0] < first[1] - 0.001
                overlap_height = first[3] < second[4] and second[3] < first[4]
                if overlap_along and overlap_height:
                    faults.append(f"openings {first[2]} and {second[2]} overlap on wall {wall_id}")


def check_rooms(plan, faults):
    scale = plan["_scale"]
    walls = plan.get("walls", [])
    for room in plan.get("rooms", []):
        polygon = room["poly"]
        area = polygon_area(polygon) * scale * scale
        if area < 0.15:
            faults.append(f"room {room['name']} has area {area:.2f} m2")
        printed = room.get("area_printed")
        if printed is not None and abs(area - printed * scale * scale) > 0.1 * printed * scale * scale:
            faults.append(f"room {room['name']} area {area:.1f} m2 differs from printed {printed}")
        open_edges = set(room.get("open_edges", []))
        count = len(polygon)
        for index in range(count):
            if index in open_edges:
                continue
            start, end = polygon[index], polygon[(index + 1) % count]
            middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            bounded = False
            for wall in walls:
                if room.get("level", 1) not in wall_levels(wall):
                    continue
                nearest, _ = closest_on_segment(middle, wall["a"], wall["b"])
                if distance(middle, nearest) <= wall["t"] / 2 + 0.2 / scale:
                    bounded = True
                    break
            if not bounded:
                faults.append(f"room {room['name']} edge {index} has no wall under it (list it in open_edges if open)")


def check_circulation(plan, faults):
    scale = plan["_scale"]
    rooms = plan.get("rooms", [])
    if not rooms:
        faults.append("plan has no rooms")
        return
    walls = {wall["id"]: wall for wall in plan.get("walls", [])}
    links = {room["name"]: set() for room in rooms}
    links["outside"] = set()
    for opening in plan.get("openings", []):
        if opening.get("kind") not in ("door", "cased") or opening["wall"] not in walls:
            continue
        wall = walls[opening["wall"]]
        start, direction, normal, _ = wall_frame(wall)
        start_along, end_along = opening_range(opening)
        middle_along = (start_along + end_along) / 2
        reach = wall["t"] / 2 + 0.25 / scale
        centre = (start[0] + direction[0] * middle_along, start[1] + direction[1] * middle_along)
        level = opening.get("level", wall_levels(wall)[0])
        left_room = room_at(plan, (centre[0] + normal[0] * reach, centre[1] + normal[1] * reach), level) or "outside"
        right_room = room_at(plan, (centre[0] - normal[0] * reach, centre[1] - normal[1] * reach), level) or "outside"
        links[left_room].add(right_room)
        links[right_room].add(left_room)
    for room in rooms:
        for neighbour in room.get("open_to", []):
            links[room["name"]].add(neighbour)
            links.setdefault(neighbour, set()).add(room["name"])
    reached = {"outside"}
    frontier = ["outside"]
    while frontier:
        current = frontier.pop()
        for neighbour in links.get(current, ()):
            if neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    for room in rooms:
        if room["name"] not in reached and not room.get("no_access"):
            faults.append(f"room {room['name']} cannot be reached from outside (mark no_access for a closed cupboard)")


def check_dimensions(plan, faults):
    scale = plan["_scale"]
    dimensions = plan.get("printed_dimensions", [])
    if len(dimensions) < 3:
        faults.append("list at least 3 printed_dimensions (or scale bar lengths) to tie the plan to the drawing")
    for dimension in dimensions:
        measured = distance(dimension["a"], dimension["b"]) * scale
        printed = dimension["value"] * scale
        if abs(measured - printed) > DIMENSION_TOLERANCE_METRES:
            faults.append(f"dimension {dimension.get('label')}: plan {measured:.2f} m, printed {printed:.2f} m")


def check_provenance(plan, faults):
    provenance = plan.get("provenance", {})
    if not provenance.get("sourced"):
        faults.append("provenance.sourced is empty: say what the drawing gave")
    if not provenance.get("inferred"):
        faults.append("provenance.inferred is empty: say what you inferred (roof, facade, heights, finishes)")
    source = plan.get("source", {})
    for key in ("image", "url", "license"):
        if not source.get(key):
            faults.append(f"source.{key} is missing")


def run_check(plan):
    faults = []
    check_walls(plan, faults)
    check_openings(plan, faults)
    check_rooms(plan, faults)
    check_circulation(plan, faults)
    check_dimensions(plan, faults)
    check_provenance(plan, faults)
    print(f"{len(plan.get('walls', []))} walls, {len(plan.get('openings', []))} openings, {len(plan.get('rooms', []))} rooms")
    for fault in faults:
        print("FAULT", fault)
    print("check", "FAILED" if faults else "passed")
    return not faults


def fit_affine(pairs):
    import numpy

    plan_points = numpy.array([[pair["plan"][0], pair["plan"][1], 1.0] for pair in pairs])
    pixel_points = numpy.array([pair["px"] for pair in pairs], dtype=float)
    solution, _, _, _ = numpy.linalg.lstsq(plan_points, pixel_points, rcond=None)
    residuals = plan_points @ solution - pixel_points
    return solution, numpy.sqrt((residuals ** 2).sum(axis=1).mean())


def to_pixels(matrix, point):
    return (
        matrix[0][0] * point[0] + matrix[1][0] * point[1] + matrix[2][0],
        matrix[0][1] * point[0] + matrix[1][1] * point[1] + matrix[2][1],
    )


def load_ink(plan):
    import numpy
    from PIL import Image
    from scipy import ndimage

    Image.MAX_IMAGE_PIXELS = None
    image = Image.open(plan["_folder"] / plan["source"]["image"]).convert("L")
    grey = numpy.asarray(image, dtype=float)
    threshold = plan.get("calibration", {}).get("ink_threshold")
    if threshold is None:
        threshold = (numpy.percentile(grey, 2) + numpy.percentile(grey, 60)) / 2
    ink = grey < threshold
    distance_to_ink = ndimage.distance_transform_edt(~ink)
    return image, ink, distance_to_ink


def score_samples(samples_by_group, matrix, distance_to_ink, pixels_per_metre, shift=(0.0, 0.0)):
    """Fraction of sample points with ink within the tolerance, per group and overall."""
    import numpy

    height, width = distance_to_ink.shape
    tolerance_pixels = INK_TOLERANCE_METRES * pixels_per_metre
    group_scores = {}
    total_hits = 0
    total_count = 0
    for group, points in samples_by_group.items():
        hits = 0
        for point in points:
            pixel = to_pixels(matrix, (point[0] + shift[0], point[1] + shift[1]))
            column = int(pixel[0])
            row = int(pixel[1])
            if 0 <= row < height and 0 <= column < width and distance_to_ink[row, column] <= tolerance_pixels:
                hits += 1
        group_scores[group] = hits / max(1, len(points))
        total_hits += hits
        total_count += len(points)
    return total_hits / max(1, total_count), group_scores


def sample_segment(start, end, step, offset=0.0):
    length = distance(start, end)
    count = max(2, int(length / step))
    normal = (-(end[1] - start[1]) / max(length, 1e-9), (end[0] - start[0]) / max(length, 1e-9))
    return [
        (
            start[0] + (end[0] - start[0]) * index / (count - 1) + normal[0] * offset,
            start[1] + (end[1] - start[1]) * index / (count - 1) + normal[1] * offset,
        )
        for index in range(count)
    ]


def sheet_offset(plan, wall):
    """Upper floors are drawn beside the first floor on the sheet: how far, in plan units."""
    offsets = plan.get("calibration", {}).get("level_offsets", {})
    return offsets.get(str(wall_levels(wall)[0]), [0.0, 0.0])


def wall_face_samples(plan):
    """Sample points on each wall's faces, skipping its openings, in plan units."""
    scale = plan["_scale"]
    step = 0.05 / scale
    openings_by_wall = {}
    for opening in plan.get("openings", []):
        openings_by_wall.setdefault(opening["wall"], []).append(opening_range(opening))
    samples = {}
    for wall in plan["walls"]:
        if wall.get("dashed"):
            continue
        start, direction, normal, length = wall_frame(wall)
        sheet_x, sheet_y = sheet_offset(plan, wall)
        start = (start[0] + sheet_x, start[1] + sheet_y)
        points = []
        along = 0.0
        while along <= length:
            blocked = any(left < along < right for left, right in openings_by_wall.get(wall["id"], []))
            if not blocked:
                for side in (-1, 1):
                    offset = side * wall["t"] / 2
                    points.append((start[0] + direction[0] * along + normal[0] * offset, start[1] + direction[1] * along + normal[1] * offset))
            along += step
        samples[wall["id"]] = points
    return samples


def sweep_best_offset(samples, matrix, distance_to_ink, pixels_per_metre, scale):
    best_score = -1.0
    best_shift = (0.0, 0.0)
    reach = int(SWEEP_REACH_METRES / SWEEP_STEP_METRES)
    thinned = {group: points[::3] for group, points in samples.items()}
    for step_x in range(-reach, reach + 1):
        for step_y in range(-reach, reach + 1):
            shift = (step_x * SWEEP_STEP_METRES / scale, step_y * SWEEP_STEP_METRES / scale)
            score, _ = score_samples(thinned, matrix, distance_to_ink, pixels_per_metre, shift)
            better = score > best_score + 1e-6
            nearer = abs(score - best_score) <= 1e-6 and math.hypot(*shift) < math.hypot(*best_shift)
            if better or nearer:
                best_score = score
                best_shift = shift
    return best_score, (best_shift[0] * scale, best_shift[1] * scale)


def report_score(label, samples, matrix, distance_to_ink, pixels_per_metre, plan):
    scale = plan["_scale"]
    score, group_scores = score_samples(samples, matrix, distance_to_ink, pixels_per_metre)
    best_score, best_offset = sweep_best_offset(samples, matrix, distance_to_ink, pixels_per_metre, scale)
    far_shift = (0.5 / scale, 0.5 / scale)
    shifted_score, _ = score_samples(samples, matrix, distance_to_ink, pixels_per_metre, far_shift)
    print(f"{label}: {score:.3f} of faces on ink; 0.5 m shifted control {shifted_score:.3f}")
    print(f"  best offset {best_offset[0]:+.2f}, {best_offset[1]:+.2f} m scoring {best_score:.3f}")
    worst = sorted(group_scores.items(), key=lambda item: item[1])[:6]
    print("  worst:", ", ".join(f"{group} {value:.2f}" for group, value in worst))
    passed = score >= MINIMUM_SCORE
    passed = passed and math.hypot(*best_offset) <= MAXIMUM_BEST_OFFSET_METRES
    passed = passed and score > shifted_score + 0.1
    print(f"  {label}", "passed" if passed else "FAILED")
    return passed


def calibrated(plan):
    scale = plan["_scale"]
    matrix, rms_pixels = fit_affine(plan["calibration"]["pairs"])
    pixels_per_metre = math.hypot(matrix[0][0], matrix[0][1]) / scale
    error_metres = rms_pixels / pixels_per_metre
    print(f"calibration: {pixels_per_metre:.1f} px per metre, error {error_metres * 100:.1f} cm")
    return matrix, pixels_per_metre, error_metres <= MAXIMUM_CALIBRATION_ERROR_METRES


def crop_box(plan, matrix, margin_units):
    corners = []
    for wall in plan["walls"]:
        corners.append(to_pixels(matrix, (wall["a"][0], wall["a"][1])))
        corners.append(to_pixels(matrix, (wall["b"][0], wall["b"][1])))
    margin = margin_units * math.hypot(matrix[0][0], matrix[0][1])
    return (
        int(min(corner[0] for corner in corners) - margin),
        int(min(corner[1] for corner in corners) - margin),
        int(max(corner[0] for corner in corners) + margin),
        int(max(corner[1] for corner in corners) + margin),
    )


def save_overlay(plan, image, layer, matrix, name):
    from PIL import Image

    base = image.convert("RGBA")
    merged = Image.alpha_composite(base, layer)
    box = crop_box(plan, matrix, 2.0 / plan["_scale"])
    box = (max(0, box[0]), max(0, box[1]), min(merged.width, box[2]), min(merged.height, box[3]))
    merged = merged.crop(box).convert("RGB")
    merged.thumbnail((2400, 2400))
    target = plan["_folder"] / name
    merged.save(target)
    print("wrote", target)


def run_overlay(plan):
    from PIL import Image, ImageDraw

    matrix, pixels_per_metre, calibration_ok = calibrated(plan)
    image, _, distance_to_ink = load_ink(plan)
    samples = wall_face_samples(plan)
    passed = report_score("plan overlay", samples, matrix, distance_to_ink, pixels_per_metre, plan) and calibration_ok
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for wall in plan["walls"]:
        start, direction, normal, _ = wall_frame(wall)
        half = wall["t"] / 2
        end = wall["b"]
        corners = [
            (start[0] + normal[0] * half, start[1] + normal[1] * half),
            (end[0] + normal[0] * half, end[1] + normal[1] * half),
            (end[0] - normal[0] * half, end[1] - normal[1] * half),
            (start[0] - normal[0] * half, start[1] - normal[1] * half),
        ]
        draw.polygon([to_pixels(matrix, corner) for corner in corners], fill=(230, 20, 120, 110))
    walls = {wall["id"]: wall for wall in plan["walls"]}
    for opening in plan.get("openings", []):
        wall = walls[opening["wall"]]
        start, direction, normal, _ = wall_frame(wall)
        left, right = opening_range(opening)
        half = wall["t"] / 2
        corners = []
        for along, side in ((left, 1), (right, 1), (right, -1), (left, -1)):
            corners.append((start[0] + direction[0] * along + normal[0] * side * half, start[1] + direction[1] * along + normal[1] * side * half))
        colour = (20, 110, 240, 170) if opening.get("kind") == "window" else (20, 200, 90, 170)
        draw.polygon([to_pixels(matrix, corner) for corner in corners], fill=colour)
    save_overlay(plan, image, layer, matrix, "check_plan_overlay.png")
    print("overlay", "passed" if passed else "FAILED")
    return passed


def run_asbuilt(plan, section_path):
    from PIL import Image, ImageDraw

    scale = plan["_scale"]
    matrix, pixels_per_metre, calibration_ok = calibrated(plan)
    image, _, distance_to_ink = load_ink(plan)
    section = json.loads(pathlib.Path(section_path).read_text(encoding="utf-8"))
    samples = {}
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    dashed = {f"wall_{wall['id']}" for wall in plan["walls"] if wall.get("dashed")}
    walls_by_group = {f"wall_{wall['id']}": wall for wall in plan["walls"]}
    for group, segments in section["segments"].items():
        if group in dashed:
            continue
        sheet_x, sheet_y = sheet_offset(plan, walls_by_group[group]) if group in walls_by_group else (0.0, 0.0)
        points = []
        for segment in segments:
            start = (segment[0] / scale + sheet_x, segment[1] / scale + sheet_y)
            end = (segment[2] / scale + sheet_x, segment[3] / scale + sheet_y)
            draw.line([to_pixels(matrix, start), to_pixels(matrix, end)], fill=(230, 20, 120, 255), width=max(3, int(pixels_per_metre * 0.02)))
            points.extend(sample_segment(start, end, 0.05 / scale))
        samples[group] = points
    passed = report_score("as-built section", samples, matrix, distance_to_ink, pixels_per_metre, plan) and calibration_ok
    save_overlay(plan, image, layer, matrix, "check_asbuilt_overlay.png")
    print("as-built", "passed" if passed else "FAILED")
    return passed


def main():
    command = sys.argv[1]
    plan = load_plan(sys.argv[2])
    if command == "check":
        passed = run_check(plan)
    elif command == "overlay":
        passed = run_overlay(plan)
    elif command == "asbuilt":
        passed = run_asbuilt(plan, sys.argv[3])
    else:
        print(__doc__)
        passed = False
    sys.exit(0 if passed else 1)


main()
