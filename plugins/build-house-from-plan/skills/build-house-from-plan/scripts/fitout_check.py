"""Fit-out checks for a plan with equipment: mixed units across sheets, then each item against its room.

    fitout_check.py units plan.json    reconcile every written dimension to metres, flag conflicts
    fitout_check.py fit plan.json      place each equipment item with its clearances, rate fits / tight / clash
    fitout_check.py all plan.json      both, plus the coordination card (needs pillow)

Writes `fitout_units.md`, `fitout_coordination.md`, `fitout_report.json` and `fitout_card.png` next to the plan.
`build_house.py` reads `fitout_report.json` to build the equipment and colour each clearance zone by its status.
Exit code 1 when a dimension conflict or an equipment clash is found. Keys: references/fit-out.md.
"""

import json
import math
import pathlib
import re
import statistics
import sys

METRES_PER = {"m": 1.0, "mm": 0.001, "cm": 0.01, "ft": 0.3048, "in": 0.0254}
UNIT_WORDS = {
    "m": "m", "metre": "m", "metres": "m", "meter": "m", "meters": "m",
    "mm": "mm", "cm": "cm",
    "ft": "ft", "foot": "ft", "feet": "ft", "'": "ft", "′": "ft",
    "in": "in", "inch": "in", "inches": "in", '"': "in", "″": "in",
}
DEFAULT_TOLERANCE_M = 0.02
DEFAULT_TIGHT_M = 0.10
DOOR_APPROACH_M = 0.9
SAMPLE_STEP_M = 0.05
TOUCH_EPSILON_M = 0.0005  # a zone that only touches a wall reads -1e-16 from float noise

FEET_INCHES = re.compile(
    r"^(?P<feet>\d+(?:\.\d+)?)\s*(?:'|′|ft|feet|foot)\s*-?\s*"
    r"(?:(?P<inches>\d+(?:\.\d+)?)?(?:\s+(?P<num>\d+)/(?P<den>\d+))?\s*(?:\"|″|in|inch|inches)?)?$"
)
NUMBER_WITH_UNIT = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s*(?:(?P<num>\d+)/(?P<den>\d+))?\s*(?P<unit>[a-z'\"′″]*)$")
DUAL = re.compile(r"^(?P<first>[^(\[]+?)\s*[(\[](?P<second>[^)\]]+)[)\]]\s*$")


# ---------------------------------------------------------------- reading lengths


def parse_length(text, default_unit=None):
    """Metres from one written length: 6.10 m, 6100 mm, 20'-0", 13' 9 1/2", 165", 5 ft 6 in, or a bare number."""
    cleaned = text.strip().lower().replace("’", "'").replace("”", '"').replace(",", "")
    cleaned = re.sub(r"(\d)\s*ft\s+(\d)", r"\1' \2", cleaned)
    feet_match = FEET_INCHES.match(cleaned)
    if feet_match:
        feet = float(feet_match["feet"])
        inches = float(feet_match["inches"] or 0)
        if feet_match["num"]:
            inches += int(feet_match["num"]) / int(feet_match["den"])
        return (feet * 12 + inches) * METRES_PER["in"]
    number_match = NUMBER_WITH_UNIT.match(cleaned)
    if not number_match:
        raise ValueError(f"cannot read a length from {text!r}")
    value = float(number_match["value"])
    if number_match["num"]:
        value += int(number_match["num"]) / int(number_match["den"])
    unit_word = number_match["unit"]
    if not unit_word:
        if default_unit is None:
            raise ValueError(f"{text!r} has no unit and its sheet sets no default_unit")
        unit_word = default_unit
    if unit_word not in UNIT_WORDS:
        raise ValueError(f"unknown unit {unit_word!r} in {text!r}")
    return value * METRES_PER[UNIT_WORDS[unit_word]]


def read_dimension_text(text, default_unit):
    """One reading, or a primary value with its written conversion: `20'-0" (6.40 m)` or `6.10 m [20'-0"]`."""
    dual_match = DUAL.match(text.strip())
    if dual_match:
        return parse_length(dual_match["first"], default_unit), parse_length(dual_match["second"], default_unit)
    return parse_length(text, default_unit), None


def length_in_metres(value, plan_unit):
    """A plan value: a number in the plan's own units, or a string that carries its unit."""
    if isinstance(value, str):
        return parse_length(value, plan_unit)
    return value * METRES_PER[plan_unit]


def format_metres(metres):
    return f"{metres:.3f} m"


# ---------------------------------------------------------------- unit reconciliation


def reconcile_units(plan):
    """Group readings of the same dimension across sheets, drop wrong conversions, flag disagreements."""
    plan_unit = plan.get("units", "m")
    tolerance = plan.get("unit_tolerance_m", DEFAULT_TOLERANCE_M)
    default_unit_by_sheet = {sheet["id"]: sheet.get("default_unit") for sheet in plan.get("sheets", [])}
    readings_by_id = {}
    for dimension in plan.get("dimensions", []):
        default_unit = default_unit_by_sheet.get(dimension["sheet"])
        primary, written_conversion = read_dimension_text(dimension["text"], default_unit)
        reading = {
            "sheet": dimension["sheet"],
            "text": dimension["text"],
            "metres": primary,
            "label": dimension.get("label", dimension["id"]),
            "faults": [],
        }
        if written_conversion is not None and abs(written_conversion - primary) > tolerance:
            reading["faults"].append(
                f"wrong conversion on {dimension['sheet']}: {dimension['text']} is {format_metres(primary)}, "
                f"written as {format_metres(written_conversion)} ({(written_conversion - primary) * 1000:+.0f} mm)"
            )
        readings_by_id.setdefault(dimension["id"], {"readings": [], "measure": None})
        readings_by_id[dimension["id"]]["readings"].append(reading)
        if "a" in dimension and "b" in dimension:
            readings_by_id[dimension["id"]]["measure"] = (dimension["a"], dimension["b"])

    rows = []
    for dimension_id, group in readings_by_id.items():
        readings = group["readings"]
        values = [reading["metres"] for reading in readings]
        resolved = statistics.median(values)
        spread = max(values) - min(values)
        faults = [fault for reading in readings for fault in reading["faults"]]
        status = "ok"
        if faults:
            status = "wrong conversion"
        if spread > tolerance:
            status = "conflict"
            faults.append(
                "sheets disagree by " + f"{spread * 1000:.0f} mm: "
                + ", ".join(f"{reading['sheet']} {format_metres(reading['metres'])}" for reading in readings)
            )
            resolved = min(values)
        row = {
            "id": dimension_id,
            "label": readings[0]["label"],
            "readings": [{"sheet": r["sheet"], "text": r["text"], "metres": round(r["metres"], 4)} for r in readings],
            "resolved_m": round(resolved, 4),
            "status": status,
            "faults": faults,
        }
        if group["measure"]:
            start, end = group["measure"]
            modelled = math.dist(start, end) * METRES_PER[plan_unit]
            row["modelled_m"] = round(modelled, 4)
            if abs(modelled - resolved) > tolerance:
                row["status"] = "model off"
                row["faults"].append(
                    f"plan geometry measures {format_metres(modelled)}, drawings say {format_metres(resolved)} "
                    f"({(modelled - resolved) * 1000:+.0f} mm): rebuild the plan from the resolved value"
                )
        rows.append(row)
    return rows


def units_markdown(rows):
    lines = [
        "| Dimension | Readings | Resolved | Status | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        readings = "<br>".join(f"{r['sheet']}: `{r['text']}` = {r['metres']:.3f} m" for r in row["readings"])
        note = "<br>".join(row["faults"]) or "all sheets agree"
        lines.append(f"| {row['label']} | {readings} | {row['resolved_m']:.3f} m | {row['status']} | {note} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- geometry


def rectangle(centre, half_width, half_depth, angle, offset=(0.0, 0.0)):
    """Corners of a rectangle in local x (width) and y (depth), rotated about `centre`; `offset` moves it locally."""
    cosine = math.cos(angle)
    sine = math.sin(angle)
    corners = []
    for sign_x, sign_y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        local_x = offset[0] + sign_x * half_width
        local_y = offset[1] + sign_y * half_depth
        corners.append((centre[0] + local_x * cosine - local_y * sine, centre[1] + local_x * sine + local_y * cosine))
    return corners


def edges(polygon):
    return [(polygon[index], polygon[(index + 1) % len(polygon)]) for index in range(len(polygon))]


def segment_distance(point, start, end):
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    length_squared = delta_x * delta_x + delta_y * delta_y
    fraction = 0.0
    if length_squared > 0:
        fraction = ((point[0] - start[0]) * delta_x + (point[1] - start[1]) * delta_y) / length_squared
        fraction = max(0.0, min(1.0, fraction))
    return math.dist(point, (start[0] + fraction * delta_x, start[1] + fraction * delta_y))


def inside(point, polygon):
    crossings = False
    for start, end in edges(polygon):
        if (start[1] > point[1]) != (end[1] > point[1]):
            x_at = start[0] + (point[1] - start[1]) * (end[0] - start[0]) / (end[1] - start[1])
            if point[0] < x_at:
                crossings = not crossings
    return crossings


def outline_samples(polygon):
    samples = []
    for start, end in edges(polygon):
        steps = max(1, int(math.dist(start, end) / SAMPLE_STEP_M))
        for step in range(steps):
            fraction = step / steps
            samples.append((start[0] + fraction * (end[0] - start[0]), start[1] + fraction * (end[1] - start[1])))
    return samples


def signed_distance_to_outline(point, polygon):
    """Positive inside the polygon, negative outside, in the polygon's units."""
    nearest = min(segment_distance(point, start, end) for start, end in edges(polygon))
    return nearest if inside(point, polygon) else -nearest


def containment_margin(shape, room):
    """How far the shape stays inside the room: negative is how far it pokes out."""
    return min(signed_distance_to_outline(point, room) for point in outline_samples(shape))


def separation(shape_a, shape_b):
    """Gap between two convex shapes along the best separating axis; negative is the overlap depth."""
    best = -math.inf
    for polygon in (shape_a, shape_b):
        for start, end in edges(polygon):
            axis_x = -(end[1] - start[1])
            axis_y = end[0] - start[0]
            length = math.hypot(axis_x, axis_y)
            if length == 0:
                continue
            axis_x /= length
            axis_y /= length
            projections_a = [point[0] * axis_x + point[1] * axis_y for point in shape_a]
            projections_b = [point[0] * axis_x + point[1] * axis_y for point in shape_b]
            gap = max(min(projections_b) - max(projections_a), min(projections_a) - max(projections_b))
            best = max(best, gap)
    return best


# ---------------------------------------------------------------- equipment fit


def room_by_name(plan, name):
    for room in plan.get("rooms", []):
        if room["name"] == name:
            return room
    raise KeyError(f"equipment names room {name!r}, which the plan does not have")


def equipment_shapes(item, plan_unit):
    """Footprint and clearance zones in metres. At rot 0 the front faces -y, as for `furnish`."""
    width, depth, height = (length_in_metres(value, plan_unit) for value in item["size"])
    clear = {side: length_in_metres(value, plan_unit) for side, value in item.get("clear", {}).items()}
    centre = [length_in_metres(value, plan_unit) for value in item["at"]]
    angle = math.radians(item.get("rot", 0))
    half_width = width / 2
    half_depth = depth / 2
    zones = {}
    if clear.get("front"):
        zones["front"] = rectangle(centre, half_width, clear["front"] / 2, angle, (0, -half_depth - clear["front"] / 2))
    if clear.get("back"):
        zones["back"] = rectangle(centre, half_width, clear["back"] / 2, angle, (0, half_depth + clear["back"] / 2))
    if clear.get("left"):
        zones["left"] = rectangle(centre, clear["left"] / 2, half_depth, angle, (-half_width - clear["left"] / 2, 0))
    if clear.get("right"):
        zones["right"] = rectangle(centre, clear["right"] / 2, half_depth, angle, (half_width + clear["right"] / 2, 0))
    return {
        "footprint": rectangle(centre, half_width, half_depth, angle),
        "zones": zones,
        "size_m": [width, depth, height],
        "top_clear_m": clear.get("top", 0.0),
        "z0_m": length_in_metres(item.get("z0", 0), plan_unit),
    }


def door_zones(plan, plan_unit):
    """For each door: the leaf's swing square on its swing side and the approach strip on both faces."""
    walls = {wall["id"]: wall for wall in plan.get("walls", [])}
    zones = []
    for opening in plan.get("openings", []):
        if opening["kind"] not in ("door", "cased"):
            continue
        wall = walls[opening["wall"]]
        start = [length_in_metres(value, plan_unit) for value in wall["a"]]
        end = [length_in_metres(value, plan_unit) for value in wall["b"]]
        length = math.dist(start, end)
        direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
        normal = (-direction[1], direction[0])
        thickness = length_in_metres(wall.get("t", 0.1), plan_unit)
        low = length_in_metres(opening["from"], plan_unit)
        high = length_in_metres(opening["to"], plan_unit)
        leaf = (high - low) / max(1, opening.get("leaves", 1))
        middle = (low + high) / 2
        centre = (start[0] + direction[0] * middle, start[1] + direction[1] * middle)
        angle = math.atan2(direction[1], direction[0])
        for side in (1, -1):
            reach = DOOR_APPROACH_M
            if opening["kind"] == "door" and opening.get("swing", 1) == side:
                reach = max(reach, leaf)
            offset_along_normal = side * (thickness / 2 + reach / 2)
            zones.append({
                "door": opening["id"],
                "shape": rectangle(
                    (centre[0] + normal[0] * offset_along_normal, centre[1] + normal[1] * offset_along_normal),
                    (high - low) / 2, reach / 2, angle,
                ),
            })
    return zones


def ceiling_height(plan, room, plan_unit):
    value = room.get("ceiling", plan.get("levels", {}).get("ceiling"))
    if value is None:
        return None
    return length_in_metres(value, plan_unit)


def rate(margin, tight):
    if margin < -TOUCH_EPSILON_M:
        return "clash"
    if margin < tight:
        return "tight"
    return "fits"


def check_equipment(plan):
    plan_unit = plan.get("units", "m")
    tight = plan.get("fit_tight_m", DEFAULT_TIGHT_M)
    items = plan.get("equipment", [])
    shapes = {item["id"]: equipment_shapes(item, plan_unit) for item in items}
    doors = door_zones(plan, plan_unit)
    rows = []
    for item in items:
        shape = shapes[item["id"]]
        room = room_by_name(plan, item["room"])
        room_polygon = [[length_in_metres(value, plan_unit) for value in point] for point in room["poly"]]
        checks = []
        checks.append(("footprint inside the room", containment_margin(shape["footprint"], room_polygon)))
        for side, zone in shape["zones"].items():
            checks.append((f"{side} service zone inside the room", containment_margin(zone, room_polygon)))
        for door in doors:
            checks.append((f"footprint clear of door {door['door']} swing and approach", separation(shape["footprint"], door["shape"])))
        for other in items:
            if other["id"] == item["id"]:
                continue
            other_shape = shapes[other["id"]]
            checks.append((f"footprint clear of {other['id']}", separation(shape["footprint"], other_shape["footprint"])))
            for side, zone in shape["zones"].items():
                checks.append((f"{side} service zone clear of {other['id']}", separation(zone, other_shape["footprint"])))
        ceiling = ceiling_height(plan, room, plan_unit)
        if ceiling is not None:
            top = shape["z0_m"] + shape["size_m"][2] + shape["top_clear_m"]
            checks.append(("height with top clearance under the ceiling", ceiling - top))
        # Far-apart objects say nothing: keep what binds, then report the tightest.
        worst_name, worst_margin = min(checks, key=lambda check: check[1])
        problems = [
            {"check": name, "margin_m": round(margin, 3), "status": rate(margin, tight)}
            for name, margin in sorted(checks, key=lambda check: check[1])
            if margin < tight
        ]
        rows.append({
            "id": item["id"],
            "name": item.get("name", item["id"]),
            "room": item["room"],
            "status": rate(worst_margin, tight),
            "margin_m": round(worst_margin, 3),
            "binding": worst_name,
            "problems": problems,
            "footprint_m": [[round(value, 4) for value in point] for point in shape["footprint"]],
            "zones_m": {side: [[round(value, 4) for value in point] for point in zone] for side, zone in shape["zones"].items()},
            "z0_m": round(shape["z0_m"], 4),
            "size_m": [round(value, 4) for value in shape["size_m"]],
            "rot": item.get("rot", 0),
            "asset": item.get("asset"),
            "asset_rot": item.get("asset_rot", 0),
            "paint": item.get("paint"),
            "material": item.get("material"),
            "fit_size": item.get("fit_size", True),
        })
    return rows


def coordination_markdown(rows):
    marks = {"fits": "✓ fits", "tight": "▲ tight", "clash": "✕ clash"}
    lines = [
        "| Item | Room | Status | Margin | Binding check | Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        action = "none"
        if row["status"] == "clash":
            action = f"move or resize: {-row['margin_m'] * 1000:.0f} mm short"
        elif row["status"] == "tight":
            action = "confirm on site"
        lines.append(
            f"| {row['id']} {row['name']} | {row['room']} | {marks[row['status']]} | "
            f"{row['margin_m'] * 1000:+.0f} mm | {row['binding']} | {action} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- card


def draw_card(units_rows, equipment_rows, output_path, title):
    """A coordination card: unit faults first, then each item with a shape-coded status mark."""
    from PIL import Image, ImageDraw, ImageFont

    def font(size, bold=False):
        for name in (("arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("arial.ttf", "DejaVuSans.ttf")):
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        return ImageFont.load_default()

    ink = (28, 30, 34)
    muted = (110, 114, 122)
    paper = (246, 245, 241)
    row_fill = (236, 234, 228)
    colours = {"fits": (46, 125, 80), "tight": (196, 130, 20), "clash": (200, 50, 45)}
    width = 1600
    row_height = 64
    unit_faults = [row for row in units_rows if row["status"] != "ok"]
    height = 260 + row_height * (len(unit_faults) + len(equipment_rows)) + (120 if unit_faults else 0)
    image = Image.new("RGB", (width, height), paper)
    draw = ImageDraw.Draw(image)
    draw.text((72, 64), title, font=font(52, bold=True), fill=ink)
    cursor = 160

    def mark(status, x, y):
        colour = colours[status]
        if status == "fits":
            draw.ellipse((x, y, x + 30, y + 30), fill=colour)
            draw.line((x + 8, y + 16, x + 13, y + 22, x + 23, y + 9), fill=paper, width=4)
        elif status == "tight":
            draw.polygon((x + 15, y, x + 30, y + 30, x, y + 30), fill=colour)
        else:
            draw.rectangle((x, y, x + 30, y + 30), fill=colour)
            draw.line((x + 8, y + 8, x + 22, y + 22), fill=paper, width=4)
            draw.line((x + 22, y + 8, x + 8, y + 22), fill=paper, width=4)

    if unit_faults:
        draw.text((72, cursor), "Units", font=font(30, bold=True), fill=ink)
        cursor += 56
        for row in unit_faults:
            draw.rounded_rectangle((60, cursor, width - 60, cursor + row_height - 10), 12, fill=row_fill)
            mark("clash", 84, cursor + 13)
            draw.text((136, cursor + 14), row["label"], font=font(28, bold=True), fill=ink)
            draw.text((560, cursor + 16), row["faults"][0][:78], font=font(24), fill=muted)
            cursor += row_height
        cursor += 24
    draw.text((72, cursor), "Equipment", font=font(30, bold=True), fill=ink)
    cursor += 56
    for row in equipment_rows:
        draw.rounded_rectangle((60, cursor, width - 60, cursor + row_height - 10), 12, fill=row_fill)
        mark(row["status"], 84, cursor + 13)
        draw.text((136, cursor + 14), f"{row['id']}  {row['name']}", font=font(28, bold=True), fill=ink)
        draw.text((700, cursor + 14), f"{row['margin_m'] * 1000:+.0f} mm", font=font(28, bold=True), fill=colours[row["status"]])
        draw.text((860, cursor + 16), row["binding"][:52], font=font(24), fill=muted)
        cursor += row_height
    image.save(output_path)


# ---------------------------------------------------------------- entry


def main():
    command, plan_path = sys.argv[1], pathlib.Path(sys.argv[2])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    folder = plan_path.resolve().parent
    report_path = folder / "fitout_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    failed = False
    if command in ("units", "all"):
        units_rows = reconcile_units(plan)
        report["units"] = units_rows
        (folder / "fitout_units.md").write_text(units_markdown(units_rows), encoding="utf-8")
        for row in units_rows:
            print(f"UNITS {row['status']:<16} {row['label']}: {row['resolved_m']:.3f} m")
            for fault in row["faults"]:
                print(f"    {fault}")
        failed |= any(row["status"] != "ok" for row in units_rows)
    if command in ("fit", "all"):
        equipment_rows = check_equipment(plan)
        report["equipment"] = equipment_rows
        (folder / "fitout_coordination.md").write_text(coordination_markdown(equipment_rows), encoding="utf-8")
        for row in equipment_rows:
            print(f"FIT {row['status']:<6} {row['margin_m'] * 1000:+6.0f} mm  {row['id']} {row['name']}: {row['binding']}")
        failed |= any(row["status"] == "clash" for row in equipment_rows)
    if command == "all":
        draw_card(report["units"], report["equipment"], folder / "fitout_card.png", plan.get("fitout_title", "Coordination"))
    report_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
