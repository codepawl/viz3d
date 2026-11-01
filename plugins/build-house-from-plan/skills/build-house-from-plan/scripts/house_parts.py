"""Walls, openings, siding, roof, stairs and casework for build_house.py. All sizes in metres. Runs inside Blender."""

import math

from mathutils import Vector

from house_core import MeshBatch

BOARD_EXPOSURE_CLAPBOARD = 0.093
JOINT_GAP = 0.0015


def v2(point):
    return Vector((point[0], point[1]))


def inside_polygon(point, polygon):
    inside = False
    count = len(polygon)
    for index in range(count):
        x_a, y_a = polygon[index][0], polygon[index][1]
        x_b, y_b = polygon[(index + 1) % count][0], polygon[(index + 1) % count][1]
        if (y_a > point[1]) != (y_b > point[1]) and point[0] < (x_b - x_a) * (point[1] - y_a) / (y_b - y_a) + x_a:
            inside = not inside
    return inside


class RoofPlane:
    def __init__(self, data):
        self.data = data
        self.corners = [Vector(corner) for corner in data["corners"]]
        edge_one = self.corners[1] - self.corners[0]
        edge_two = self.corners[3] - self.corners[0]
        self.normal = edge_one.cross(edge_two).normalized()
        if self.normal.z < 0:
            self.normal = -self.normal

    def height_at(self, x, y):
        """Underside height at a point, or None when the point is outside this plane."""
        if not inside_polygon((x, y), self.corners):
            return None
        origin = self.corners[0]
        return origin.z - (self.normal.x * (x - origin.x) + self.normal.y * (y - origin.y)) / self.normal.z


class Wall:
    def __init__(self, data):
        self.data = data
        self.id = data["id"]
        self.a = v2(data["a"])
        self.b = v2(data["b"])
        self.t = data["t"]
        self.kind = data.get("kind", "int")
        self.length = (self.b - self.a).length
        self.direction = (self.b - self.a).normalized()
        self.normal = Vector((-self.direction.y, self.direction.x))
        self.s0 = 0.0
        self.s1 = self.length
        self.openings = []
        self.outside_side = data.get("outside")

    def at(self, along, offset=0.0, z=0.0):
        flat = self.a + self.direction * along + self.normal * offset
        return Vector((flat.x, flat.y, z))


def resolve_junctions(walls):
    """Each wall end runs through to the far face of the wall it meets, or stops at the near face."""
    for index, wall in enumerate(walls):
        for end_name in ("a", "b"):
            point = wall.a if end_name == "a" else wall.b
            for other_index, other in enumerate(walls):
                if other is wall:
                    continue
                to_point = point - other.a
                along = to_point.dot(other.direction)
                across = abs(to_point.dot(other.normal))
                if along < -0.08 or along > other.length + 0.08 or across > other.t / 2 + 0.05:
                    continue
                sine = abs(wall.direction.x * other.direction.y - wall.direction.y * other.direction.x)
                if sine < 0.2:
                    continue
                at_other_end = along < 0.08 or along > other.length - 0.08
                signed = to_point.dot(other.normal)
                runs_through = at_other_end and index < other_index
                facing = -wall.direction if end_name == "b" else wall.direction
                # Distance from this wall's end to the plane of the other wall's face along this wall's axis.
                heading = facing.dot(other.normal)
                near_plane = other.t / 2 if heading < 0 else -other.t / 2
                far_plane = -near_plane
                target_plane = far_plane if runs_through else near_plane
                travel = (target_plane - signed) / heading if abs(heading) > 1e-6 else 0.0
                if end_name == "a":
                    wall.s0 = min(wall.s0, travel) if runs_through else max(wall.s0, travel)
                else:
                    wall.s1 = max(wall.s1, wall.length - travel) if runs_through else min(wall.s1, wall.length - travel)


class Structure:
    """Plan geometry shared by the part builders."""

    def __init__(self, plan):
        self.plan = plan
        self.walls = [Wall(data) for data in plan["walls"]]
        self.by_id = {wall.id: wall for wall in self.walls}
        self.roof_planes = [RoofPlane(data) for data in plan.get("roof", {}).get("planes", [])]
        resolve_junctions(self.walls)
        for opening in plan.get("openings", []):
            wall = self.by_id[opening["wall"]]
            if "from" not in opening:
                opening["from"] = opening["at"] - opening["width"] / 2
                opening["to"] = opening["at"] + opening["width"] / 2
            wall.openings.append(opening)
        for wall in self.walls:
            wall.openings.sort(key=lambda opening: opening["from"])
        self.rooms = plan.get("rooms", [])

    def room_at(self, point):
        for room in self.rooms:
            if inside_polygon(point, room["poly"]):
                return room
        return None

    def roof_under(self, x, y):
        heights = []
        for plane in self.roof_planes:
            height = plane.height_at(x, y)
            if height is not None:
                heights.append(height)
        if not heights:
            return None
        # Crossing roofs enclose their union; a stepped roof like a lean-to closes under the lowest plane.
        return max(heights) if self.plan["style"].get("roof_union") else min(heights)

    def wall_top(self, wall, along):
        fallback = wall.data.get("h", self.plan["levels"]["ceiling"])
        if wall.data.get("top") != "roof":
            return fallback
        point = wall.at(along)
        height = self.roof_under(point.x, point.y)
        return (height - 0.005) if height is not None else fallback

    def side_material(self, wall, along, side):
        """Finish on one face of a wall, from the room behind that face or the wall's exterior finish."""
        offset = side * (wall.t / 2 + 0.12)
        point = wall.at(along, offset)
        room = self.room_at((point.x, point.y))
        if room is not None:
            return room.get("wall", self.plan["style"]["interior_wall"]), room
        return self.plan["style"].get("wall_base", "putty"), None


def top_breaks(structure, wall):
    """Places along a wall where its top height changes slope."""
    breaks = {wall.s0, wall.s1}
    if wall.data.get("top") != "roof":
        return breaks
    step = 0.05
    along = wall.s0
    previous_slope = None
    while along + step < wall.s1:
        slope = structure.wall_top(wall, along + step) - structure.wall_top(wall, along)
        if previous_slope is not None and abs(slope - previous_slope) > 1e-4:
            breaks.add(along)
        previous_slope = slope
        along += step
    return breaks


def build_wall(structure, wall, batch, reveal_material):
    floor_z = structure.plan["levels"].get("floor", 0.0)
    base_z = wall.data.get("z0", floor_z)
    breaks = top_breaks(structure, wall)
    for opening in wall.openings:
        breaks.add(max(wall.s0, opening["from"]))
        breaks.add(min(wall.s1, opening["to"]))
    stations = sorted(breaks)
    half = wall.t / 2
    for left, right in zip(stations, stations[1:]):
        if right - left < 1e-4:
            continue
        middle = (left + right) / 2
        top_left = structure.wall_top(wall, left)
        top_right = structure.wall_top(wall, right)
        cells = []
        holes = sorted(
            (opening for opening in wall.openings if opening["from"] <= middle <= opening["to"]),
            key=lambda opening: opening.get("sill", 0.0),
        )
        if not holes:
            cells.append((base_z, base_z, top_left, top_right))
        else:
            cursor = base_z
            for hole in holes:
                sill = hole.get("sill", 0.0) + floor_z
                if sill > cursor + 1e-4:
                    cells.append((cursor, cursor, sill, sill))
                cursor = hole["head"] + floor_z
            if cursor < min(top_left, top_right) - 1e-4:
                cells.append((cursor, cursor, top_left, top_right))
        material_positive, _ = structure.side_material(wall, middle, 1)
        material_negative, _ = structure.side_material(wall, middle, -1)
        for bottom_left, bottom_right, upper_left, upper_right in cells:
            batch.add_face(
                [
                    wall.at(left, -half, bottom_left),
                    wall.at(right, -half, bottom_right),
                    wall.at(right, -half, upper_right),
                    wall.at(left, -half, upper_left),
                ],
                material_negative,
            )
            batch.add_face(
                [
                    wall.at(right, half, bottom_right),
                    wall.at(left, half, bottom_left),
                    wall.at(left, half, upper_left),
                    wall.at(right, half, upper_right),
                ],
                material_positive,
            )
            batch.add_face(
                [wall.at(left, -half, upper_left), wall.at(right, -half, upper_right), wall.at(right, half, upper_right), wall.at(left, half, upper_left)],
                reveal_material,
            )
            batch.add_face(
                [wall.at(left, half, bottom_left), wall.at(right, half, bottom_right), wall.at(right, -half, bottom_right), wall.at(left, -half, bottom_left)],
                reveal_material,
            )
    # Ends of the wall.
    end_material = material_for_end(structure, wall)
    top_start = structure.wall_top(wall, wall.s0)
    top_end = structure.wall_top(wall, wall.s1)
    batch.add_face([wall.at(wall.s0, half, base_z), wall.at(wall.s0, -half, base_z), wall.at(wall.s0, -half, top_start), wall.at(wall.s0, half, top_start)], end_material)
    batch.add_face([wall.at(wall.s1, -half, base_z), wall.at(wall.s1, half, base_z), wall.at(wall.s1, half, top_end), wall.at(wall.s1, -half, top_end)], end_material)
    # Jambs of each opening.
    for opening in wall.openings:
        sill = opening.get("sill", 0.0) + floor_z
        head = opening["head"] + floor_z
        start = max(wall.s0, opening["from"])
        finish = min(wall.s1, opening["to"])
        batch.add_face([wall.at(start, -half, sill), wall.at(start, half, sill), wall.at(start, half, head), wall.at(start, -half, head)], reveal_material)
        batch.add_face([wall.at(finish, half, sill), wall.at(finish, -half, sill), wall.at(finish, -half, head), wall.at(finish, half, head)], reveal_material)


def material_for_end(structure, wall):
    return structure.plan["style"].get("end_cap", structure.plan["style"]["interior_wall"])


def outer_offset(wall):
    return wall.outside_side * wall.t / 2


def open_spans(wall, z_low, z_high, floor_z, margin, start=None, finish=None):
    """Stretches of a wall's length not interrupted by an opening within a band of height."""
    start = wall.s0 if start is None else start
    finish = wall.s1 if finish is None else finish
    spans = []
    cursor = start
    for opening in wall.openings:
        sill = opening.get("sill", 0.0) + floor_z
        head = opening["head"] + floor_z
        if z_high <= sill - margin or z_low >= head + margin:
            continue
        left = opening["from"] - margin
        right = opening["to"] + margin
        if left > cursor:
            spans.append((cursor, min(left, finish)))
        cursor = max(cursor, right)
    if cursor < finish:
        spans.append((cursor, finish))
    return [span for span in spans if span[1] - span[0] > 0.015]


def siding_clapboard(structure, wall, batch, material, exposure=BOARD_EXPOSURE_CLAPBOARD, thickness=0.014):
    floor_z = structure.plan["levels"].get("floor", 0.0)
    side = wall.outside_side
    outer = outer_offset(wall)
    base = wall.data.get("z0", floor_z)
    casing_margin = structure.plan["style"].get("exterior_casing", 0.09)
    highest = max(structure.wall_top(wall, wall.s0 + fraction * (wall.s1 - wall.s0)) for fraction in (0, 0.25, 0.5, 0.75, 1))
    z_low = base
    while z_low < highest:
        z_high = z_low + exposure
        for span_start, span_end in open_spans(wall, z_low, z_high, floor_z, casing_margin):
            along = span_start
            while along < span_end:
                piece = batch.random.uniform(1.8, 4.2)
                piece_end = min(span_end, along + piece)
                if span_end - piece_end < 0.5:
                    piece_end = span_end
                clip_start, clip_end = clip_under_top(structure, wall, along, piece_end, z_high)
                if clip_end - clip_start > 0.02:
                    batch.uv_offset = (batch.random.uniform(0, 8), batch.random.uniform(0, 8))
                    batch.variation = batch.random.uniform(0.93, 1.04)
                    butt = side * thickness
                    feather = side * 0.003
                    bottom_a = wall.at(clip_start + JOINT_GAP, outer + butt, z_low)
                    bottom_b = wall.at(clip_end - JOINT_GAP, outer + butt, z_low)
                    top_a = wall.at(clip_start + JOINT_GAP, outer + feather, z_high + 0.002)
                    top_b = wall.at(clip_end - JOINT_GAP, outer + feather, z_high + 0.002)
                    under_a = wall.at(clip_start + JOINT_GAP, outer, z_low)
                    under_b = wall.at(clip_end - JOINT_GAP, outer, z_low)
                    face = [bottom_a, bottom_b, top_b, top_a] if side < 0 else [bottom_b, bottom_a, top_a, top_b]
                    lip = [under_a, under_b, bottom_b, bottom_a] if side < 0 else [under_b, under_a, bottom_a, bottom_b]
                    batch.add_face(face, material)
                    batch.add_face(lip, material)
                    end_face = [under_a, bottom_a, top_a] if side < 0 else [bottom_a, under_a, top_a]
                    batch.add_face(end_face, material)
                    end_face = [bottom_b, under_b, top_b] if side < 0 else [under_b, bottom_b, top_b]
                    batch.add_face(end_face, material)
                along = piece_end
        z_low = z_high
    batch.variation = 1.0
    batch.uv_offset = (0, 0)


def clip_under_top(structure, wall, start, finish, z_high):
    """Shorten a horizontal board so its top stays under a sloped wall top."""
    if wall.data.get("top") != "roof":
        return start, finish
    step = 0.04
    clipped_start = start
    while clipped_start < finish and structure.wall_top(wall, clipped_start) < z_high:
        clipped_start += step
    clipped_end = finish
    while clipped_end > clipped_start and structure.wall_top(wall, clipped_end) < z_high:
        clipped_end -= step
    return clipped_start, clipped_end


def siding_board_batten(structure, wall, batch, board_material, batten_material, spacing=0.3, batten_width=0.05, batten_depth=0.019):
    floor_z = structure.plan["levels"].get("floor", 0.0)
    side = wall.outside_side
    outer = outer_offset(wall)
    base = wall.data.get("z0", floor_z) - 0.12
    casing_margin = structure.plan["style"].get("exterior_casing", 0.09)
    along = wall.s0 + spacing / 2
    while along < wall.s1:
        top = structure.wall_top(wall, along)
        z_low = base
        bands = [(z_low, top)]
        for opening in wall.openings:
            if opening["from"] - casing_margin - batten_width < along < opening["to"] + casing_margin + batten_width:
                sill = opening.get("sill", 0.0) + floor_z - casing_margin
                head = opening["head"] + floor_z + casing_margin
                updated = []
                for band_low, band_high in bands:
                    if band_low < sill:
                        updated.append((band_low, min(band_high, sill)))
                    if band_high > head:
                        updated.append((max(band_low, head), band_high))
                bands = updated
        for band_low, band_high in bands:
            if band_high - band_low < 0.03:
                continue
            batch.uv_offset = (batch.random.uniform(0, 8), batch.random.uniform(0, 8))
            batch.variation = batch.random.uniform(0.88, 1.08)
            origin = wall.at(along - batten_width / 2, outer, band_low)
            axis_x = wall.at(along + batten_width / 2, outer, band_low) - origin
            axis_y = Vector((wall.normal.x * side * batten_depth, wall.normal.y * side * batten_depth, 0))
            axis_z = Vector((0, 0, band_high - band_low))
            if side > 0:
                batch.add_box(origin, axis_x, axis_y, axis_z, batten_material, skip=("bottom",))
            else:
                batch.add_box(origin + axis_y, axis_x, -axis_y, axis_z, batten_material, skip=("bottom",))
        along += spacing
    batch.variation = 1.0
    batch.uv_offset = (0, 0)


def add_rail(batch, wall, start, finish, offset, depth_from, depth_to, z_low, z_high, material):
    """Box aligned with a wall: along start..finish, across offset+depth_from..offset+depth_to, between two heights."""
    origin = wall.at(start, offset + min(depth_from, depth_to), z_low)
    axis_x = wall.at(finish, 0, 0) - wall.at(start, 0, 0)
    span = abs(depth_to - depth_from)
    axis_y = Vector((wall.normal.x * span, wall.normal.y * span, 0))
    axis_z = Vector((0, 0, z_high - z_low))
    batch.add_box(origin, axis_x, axis_y, axis_z, material)


def build_window(structure, wall, opening, trim, glass):
    style = structure.plan["style"]
    floor_z = structure.plan["levels"].get("floor", 0.0)
    material = opening.get("frame_material", style.get("window_material", "trim_white"))
    sill = opening.get("sill", 0.0) + floor_z
    head = opening["head"] + floor_z
    start = opening["from"]
    finish = opening["to"]
    side = wall.outside_side if wall.outside_side else -1
    half = wall.t / 2
    frame_thickness = 0.035
    plane_outer = side * (half - 0.03)
    # Frame lining the whole reveal.
    add_rail(trim, wall, start, start + frame_thickness, 0, -half, half, sill, head, material)
    add_rail(trim, wall, finish - frame_thickness, finish, 0, -half, half, sill, head, material)
    add_rail(trim, wall, start, finish, 0, -half, half, head - frame_thickness, head, material)
    add_rail(trim, wall, start, finish, 0, -half, half, sill, sill + frame_thickness, material)
    # Sill with a nose past the wall face on both sides.
    casing = style.get("exterior_casing", 0.09)
    add_rail(trim, wall, start - casing - 0.02, finish + casing + 0.02, side * half, 0, side * 0.045, sill - 0.04, sill, material)
    # Casing outside and inside.
    outside_depth = side * 0.022
    add_rail(trim, wall, start - casing, start, side * half, 0, outside_depth + side * 0.01, sill, head + casing, material)
    add_rail(trim, wall, finish, finish + casing, side * half, 0, outside_depth + side * 0.01, sill, head + casing, material)
    add_rail(trim, wall, start - casing - 0.015, finish + casing + 0.015, side * half, 0, outside_depth + side * 0.03, head + casing - 0.02, head + casing + 0.03, material)
    inside_material = opening.get("casing_material", style.get("interior_trim", material))
    inside_casing = style.get("interior_casing", 0.075)
    add_rail(trim, wall, start - inside_casing, start, -side * half, 0, -side * 0.018, sill, head + inside_casing, inside_material)
    add_rail(trim, wall, finish, finish + inside_casing, -side * half, 0, -side * 0.018, sill, head + inside_casing, inside_material)
    add_rail(trim, wall, start - inside_casing, finish + inside_casing, -side * half, 0, -side * 0.018, head, head + inside_casing, inside_material)
    add_rail(trim, wall, start - inside_casing - 0.02, finish + inside_casing + 0.02, -side * half, 0, -side * 0.035, sill - 0.025, sill, inside_material)

    sash_kind = opening.get("sash", "fixed")
    inner_start = start + frame_thickness
    inner_finish = finish - frame_thickness
    inner_sill = sill + frame_thickness
    inner_head = head - frame_thickness
    panes_across = opening.get("panes_x", 1)
    panes_up = opening.get("panes_y", 1)
    sections = opening.get("sections", 1)
    section_width = (inner_finish - inner_start) / sections
    for section in range(sections):
        left = inner_start + section * section_width
        right = left + section_width
        if sash_kind == "double_hung":
            meeting = (inner_sill + inner_head) / 2
            add_sash(trim, glass, wall, left, right, inner_sill, meeting + 0.015, plane_outer - side * 0.075, panes_across, panes_up, material)
            add_sash(trim, glass, wall, left, right, meeting - 0.015, inner_head, plane_outer - side * 0.03, panes_across, panes_up, material)
        else:
            add_sash(trim, glass, wall, left, right, inner_sill, inner_head, plane_outer - side * 0.04, panes_across, panes_up, material)
    if opening.get("transom_at") is not None:
        rail_z = opening["transom_at"] + floor_z
        add_rail(trim, wall, inner_start, inner_finish, plane_outer - side * 0.04, -0.022, 0.022, rail_z - 0.02, rail_z + 0.02, material)
    if opening.get("shutters"):
        build_shutter(trim, wall, start - casing - opening["shutters"], start - casing - 0.005, side * half + side * 0.012, sill, head + casing * 0.4, style.get("shutter_material", "shutter_black"), side)
        build_shutter(trim, wall, finish + casing + 0.005, finish + casing + opening["shutters"], side * half + side * 0.012, sill, head + casing * 0.4, style.get("shutter_material", "shutter_black"), side)


def add_sash(trim, glass, wall, left, right, bottom, top, plane, panes_across, panes_up, material):
    stile = 0.042
    depth = 0.032
    add_rail(trim, wall, left, left + stile, plane, -depth / 2, depth / 2, bottom, top, material)
    add_rail(trim, wall, right - stile, right, plane, -depth / 2, depth / 2, bottom, top, material)
    add_rail(trim, wall, left + stile, right - stile, plane, -depth / 2, depth / 2, top - stile, top, material)
    add_rail(trim, wall, left + stile, right - stile, plane, -depth / 2, depth / 2, bottom, bottom + stile * 1.3, material)
    glass_left = left + stile
    glass_right = right - stile
    glass_bottom = bottom + stile * 1.3
    glass_top = top - stile
    muntin = 0.016
    for index in range(1, panes_across):
        along = glass_left + (glass_right - glass_left) * index / panes_across
        add_rail(trim, wall, along - muntin / 2, along + muntin / 2, plane, -0.011, 0.011, glass_bottom, glass_top, material)
    for index in range(1, panes_up):
        height = glass_bottom + (glass_top - glass_bottom) * index / panes_up
        add_rail(trim, wall, glass_left, glass_right, plane, -0.011, 0.011, height - muntin / 2, height + muntin / 2, material)
    add_rail(glass, wall, glass_left - 0.004, glass_right + 0.004, plane, -0.002, 0.002, glass_bottom - 0.004, glass_top + 0.004, "glass")


def build_shutter(trim, wall, start, finish, offset, bottom, top, material, side):
    stile = 0.038
    depth = 0.024
    add_rail(trim, wall, start, start + stile, offset, 0, side * depth, bottom, top, material)
    add_rail(trim, wall, finish - stile, finish, offset, 0, side * depth, bottom, top, material)
    add_rail(trim, wall, start + stile, finish - stile, offset, 0, side * depth, bottom, bottom + stile * 1.5, material)
    add_rail(trim, wall, start + stile, finish - stile, offset, 0, side * depth, top - stile * 1.5, top, material)
    middle = (bottom + top) / 2
    add_rail(trim, wall, start + stile, finish - stile, offset, 0, side * depth, middle - stile * 0.7, middle + stile * 0.7, material)
    # Louvres: thin slats tilted out of plumb.
    slat_pitch = 0.038
    height = bottom + stile * 1.5
    while height < top - stile * 1.5 - slat_pitch:
        if abs(height + slat_pitch / 2 - middle) > stile * 0.7 + slat_pitch / 2:
            lean = Vector((wall.normal.x * side * 0.012, wall.normal.y * side * 0.012, 0))
            origin = wall.at(start + stile, offset + side * 0.006, height)
            axis_x = wall.at(finish - stile, 0, 0) - wall.at(start + stile, 0, 0)
            axis_y = lean + Vector((0, 0, slat_pitch * 0.9))
            axis_z = Vector((0, 0, 0.006))
            trim.add_box(origin, axis_x, axis_y, axis_z, material)
        height += slat_pitch


def build_door(structure, wall, opening, trim, hardware):
    style = structure.plan["style"]
    floor_z = structure.plan["levels"].get("floor", 0.0)
    start = opening["from"]
    finish = opening["to"]
    head = opening["head"] + floor_z
    half = wall.t / 2
    lining = 0.02
    frame_material = opening.get("frame_material", style.get("interior_trim", "trim_white"))
    add_rail(trim, wall, start, start + lining, 0, -half, half, floor_z, head, frame_material)
    add_rail(trim, wall, finish - lining, finish, 0, -half, half, floor_z, head, frame_material)
    add_rail(trim, wall, start, finish, 0, -half, half, head - lining, head, frame_material)
    casing = style.get("interior_casing", 0.075)
    for side in (-1, 1):
        is_outer = wall.outside_side == side
        material = style.get("window_material", frame_material) if is_outer else frame_material
        width = style.get("exterior_casing", 0.09) if is_outer else casing
        add_rail(trim, wall, start - width, start, side * half, 0, side * 0.018, floor_z, head + width, material)
        add_rail(trim, wall, finish, finish + width, side * half, 0, side * 0.018, floor_z, head + width, material)
        add_rail(trim, wall, start - width, finish + width, side * half, 0, side * 0.018, head, head + width, material)
    if opening.get("kind") != "door" or opening.get("leaf") == "none":
        return
    leaves = opening.get("leaves", 1)
    clear_start = start + lining
    clear_finish = finish - lining
    leaf_width = (clear_finish - clear_start) / leaves
    for leaf_index in range(leaves):
        leaf_start = clear_start + leaf_index * leaf_width
        hinge_at_start = opening.get("hinge", "start") == "start" if leaves == 1 else leaf_index == 0
        swing_side = opening.get("swing", -1 if wall.outside_side is None else -wall.outside_side)
        open_degrees = opening.get("open", 0)
        build_door_leaf(structure, wall, opening, trim, hardware, leaf_start, leaf_width - 0.003, floor_z + 0.005, head - lining - 0.003, hinge_at_start, swing_side, open_degrees)


def build_door_leaf(structure, wall, opening, trim, hardware, start, width, bottom, top, hinge_at_start, swing_side, open_degrees):
    style = structure.plan["style"]
    material = opening.get("material", style.get("door_material", "trim_white"))
    thickness = 0.038
    plane = swing_side * (wall.t / 2 - thickness)
    hinge_along = start if hinge_at_start else start + width
    hinge = wall.at(hinge_along, plane, 0)
    angle = math.radians(open_degrees) * swing_side * (1 if hinge_at_start else -1)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    direction_along = wall.direction * (1 if hinge_at_start else -1)
    normal = wall.normal

    def rotate(flat):
        return Vector((flat.x * cosine - flat.y * sine, flat.x * sine + flat.y * cosine, 0))

    axis_width = rotate(Vector((direction_along.x, direction_along.y, 0)))
    axis_depth = rotate(Vector((normal.x, normal.y, 0)))

    def box(u_low, u_high, depth_low, depth_high, z_low, z_high, box_material):
        origin = hinge + axis_width * u_low + axis_depth * depth_low + Vector((0, 0, z_low))
        trim.add_box(origin, axis_width * (u_high - u_low), axis_depth * (depth_high - depth_low), Vector((0, 0, z_high - z_low)), box_material)

    kind = opening.get("panels", "slab")
    total_height = top - bottom
    depth_low = -thickness / 2
    depth_high = thickness / 2
    if kind == "slab":
        box(0, width, depth_low, depth_high, bottom, top, material)
    elif kind == "sheathing":
        boards = max(3, int(width / 0.12))
        for index in range(boards):
            u_low = width * index / boards + 0.001
            u_high = width * (index + 1) / boards - 0.001
            trim.variation = trim.random.uniform(0.9, 1.05)
            trim.uv_offset = (trim.random.uniform(0, 5), trim.random.uniform(0, 5))
            box(u_low, u_high, depth_low, depth_high, bottom, top, material)
        trim.variation = 1.0
        trim.uv_offset = (0, 0)
        box(0.02, width - 0.02, depth_high, depth_high + 0.02, bottom + total_height * 0.18, bottom + total_height * 0.18 + 0.13, material)
        box(0.02, width - 0.02, depth_high, depth_high + 0.02, bottom + total_height * 0.78, bottom + total_height * 0.78 + 0.13, material)
    else:
        rows = {"six": [(0.0, 0.33), (0.33, 0.78), (0.78, 1.0)], "four": [(0.0, 0.42), (0.42, 1.0)], "two": [(0.0, 0.5), (0.5, 1.0)]}[kind]
        columns = 1 if kind == "two" else 2
        stile = 0.105
        rail = 0.105
        muntin = 0.09
        box(0, stile, depth_low, depth_high, bottom, top, material)
        box(width - stile, width, depth_low, depth_high, bottom, top, material)
        inner_width = width - 2 * stile
        inner_height = total_height - rail * (len(rows) + 1)
        pane_width = (inner_width - muntin * (columns - 1)) / columns
        height = bottom
        box(stile, width - stile, depth_low, depth_high, height, height + rail * 1.35, material)
        height += rail * 1.35
        for row_index, (low, high) in enumerate(rows):
            pane_height = inner_height * (high - low) - (rail * 0.35 if row_index == 0 else 0)
            for column in range(columns):
                u_low = stile + column * (pane_width + muntin)
                u_high = u_low + pane_width
                if column < columns - 1:
                    box(u_high, u_high + muntin, depth_low, depth_high, height, height + pane_height, material)
                add_raised_panel(trim, hinge, axis_width, axis_depth, u_low, u_high, height, height + pane_height, thickness, material)
            height += pane_height
            box(stile, width - stile, depth_low, depth_high, height, height + rail, material)
            height += rail
    # Knob on both faces.
    knob_u = width - 0.06
    knob_z = bottom + 0.95
    for face in (-1, 1):
        rose = hinge + axis_width * knob_u + axis_depth * (face * thickness / 2) + Vector((0, 0, knob_z))
        outward = axis_depth * face
        hardware.add_cylinder(rose, rose + outward * 0.008, 0.028, opening.get("hardware", "brass"), sides=20)
        hardware.add_cylinder(rose + outward * 0.008, rose + outward * 0.045, 0.009, opening.get("hardware", "brass"), sides=14)
        hardware.add_cylinder(rose + outward * 0.045, rose + outward * 0.068, 0.024, opening.get("hardware", "brass"), sides=20, radius_top=0.019)
    for fraction in (0.12, 0.5, 0.88):
        hinge_centre = hinge + axis_depth * (swing_side * 0.019) + Vector((0, 0, bottom + total_height * fraction))
        hardware.add_cylinder(hinge_centre - Vector((0, 0, 0.045)), hinge_centre + Vector((0, 0, 0.045)), 0.007, opening.get("hardware", "brass"), sides=10)


def add_raised_panel(trim, hinge, axis_width, axis_depth, u_low, u_high, z_low, z_high, thickness, material):
    """Fielded door panel: flat field standing proud of a sloped margin, on both faces."""
    margin = 0.035
    for face in (-1, 1):
        def point(u, z, depth):
            return hinge + axis_width * u + axis_depth * (face * depth) + Vector((0, 0, z))

        groove = thickness / 2 - 0.012
        field = thickness / 2 - 0.004
        outer = [point(u_low, z_low, groove), point(u_high, z_low, groove), point(u_high, z_high, groove), point(u_low, z_high, groove)]
        inner = [
            point(u_low + margin, z_low + margin, field),
            point(u_high - margin, z_low + margin, field),
            point(u_high - margin, z_high - margin, field),
            point(u_low + margin, z_high - margin, field),
        ]
        order = [0, 1, 2, 3] if face * axis_depth.dot(axis_width.cross(Vector((0, 0, 1)))) < 0 else [3, 2, 1, 0]
        for index in range(4):
            first = order[index]
            second = order[(index + 1) % 4]
            trim.add_face([outer[first], outer[second], inner[second], inner[first]], material)
        trim.add_face([inner[order[0]], inner[order[1]], inner[order[2]], inner[order[3]]], material)


def build_baseboards(structure, wall, trim):
    floor_z = wall.data.get("z0", structure.plan["levels"].get("floor", 0.0))
    half = wall.t / 2
    style = structure.plan["style"]
    for side in (-1, 1):
        if wall.outside_side == side:
            continue
        spans = open_spans(wall, floor_z, floor_z + 0.1, floor_z, 0.0)
        for span_start, span_end in spans:
            door_margin_low = span_start
            door_margin_high = span_end
            for opening in wall.openings:
                if abs(opening["to"] - span_start) < 0.001:
                    door_margin_low = span_start + style.get("interior_casing", 0.075)
                if abs(opening["from"] - span_end) < 0.001:
                    door_margin_high = span_end - style.get("interior_casing", 0.075)
            middle = (door_margin_low + door_margin_high) / 2
            _, room = structure.side_material(wall, middle, side)
            if room is None or door_margin_high - door_margin_low < 0.02:
                continue
            height = room.get("baseboard", style.get("baseboard", 0.1))
            if height <= 0:
                continue
            material = room.get("trim", style.get("interior_trim", "trim_white"))
            add_rail(trim, wall, door_margin_low, door_margin_high, side * half, 0, side * 0.016, floor_z, floor_z + height, material)
            crown = room.get("crown", 0.0)
            ceiling = room.get("ceiling")
            if crown > 0 and ceiling is not None:
                add_rail(trim, wall, door_margin_low, door_margin_high, side * half, 0, side * 0.03, floor_z + ceiling - crown, floor_z + ceiling, material)
            rail_height = room.get("chair_rail", 0.0)
            if rail_height > 0:
                for rail_start, rail_end in open_spans(wall, floor_z + rail_height, floor_z + rail_height + 0.07, floor_z, 0.08, door_margin_low, door_margin_high):
                    add_rail(trim, wall, rail_start, rail_end, side * half, 0, side * 0.022, floor_z + rail_height, floor_z + rail_height + 0.07, material)


def build_corner_boards(structure, wall, trim, material):
    width = structure.plan["style"].get("corner_board", 0.11)
    if width <= 0 or not wall.outside_side:
        return
    outer = outer_offset(wall)
    floor_z = structure.plan["levels"].get("floor", 0.0)
    side = wall.outside_side
    base = wall.data.get("z0", floor_z)
    for start, finish in ((wall.s0, wall.s0 + width), (wall.s1 - width, wall.s1)):
        top = min(structure.wall_top(wall, start), structure.wall_top(wall, finish))
        add_rail(trim, wall, start, finish, outer, 0, side * 0.026, base - 0.02, top, material)


def build_roof_plane(plane_data, roof_plane, deck, covering, carpentry, style):
    corners = roof_plane.corners
    normal = roof_plane.normal
    thickness = plane_data.get("thickness", 0.04)
    cover = plane_data.get("cover", "shingle")
    material_under = plane_data.get("under", style.get("soffit", "pine_boards"))
    lower = list(corners)
    upper = [corner + normal * thickness for corner in corners]
    deck.add_face(list(reversed(lower)), material_under)
    deck.add_face(upper, plane_data.get("top", "putty"))
    count = len(corners)
    for index in range(count):
        following = (index + 1) % count
        deck.add_face([lower[index], lower[following], upper[following], upper[index]], material_under)

    eave_a, eave_b, ridge_b, ridge_a = corners
    fascia_material = plane_data.get("fascia", style.get("fascia", style.get("window_material", "trim_white")))
    fascia_depth = plane_data.get("fascia_depth", 0.14)
    if fascia_depth > 0:
        drop = Vector((0, 0, -fascia_depth + thickness))
        run = eave_b - eave_a
        out = (eave_a - ridge_a).normalized()
        out.z = 0
        out.normalize()
        carpentry.add_box(eave_a + drop + out * 0.0, run, out * 0.03, Vector((0, 0, fascia_depth + 0.012)), fascia_material)
        for start, finish in ((eave_a, ridge_a), (eave_b, ridge_b)):
            rake_run = finish - start
            side_out = (start - (eave_b if start == eave_a else eave_a))
            side_out.z = 0
            side_out.normalize()
            carpentry.add_box(start + Vector((0, 0, -fascia_depth + thickness)), rake_run, side_out * 0.03, Vector((0, 0, fascia_depth + 0.012)), fascia_material)
    if cover == "shingle":
        cover_shingles(eave_a, eave_b, ridge_a, ridge_b, normal, thickness, covering, plane_data)
    elif cover == "roll":
        cover_roll(eave_a, eave_b, ridge_a, ridge_b, normal, thickness, covering, plane_data)

    rafters = plane_data.get("rafters")
    if rafters:
        spacing = rafters["spacing"]
        width = rafters.get("w", 0.05)
        depth = rafters.get("d", 0.14)
        material = rafters.get("material", "pine_boards")
        run_x = eave_b - eave_a
        total = run_x.length
        axis_along = run_x.normalized()
        along = rafters.get("first", spacing / 2)
        while along < total:
            start_point = eave_a + axis_along * along
            end_point = ridge_a + (ridge_b - ridge_a).normalized() * along
            start_point = start_point + (end_point - start_point).normalized() * rafters.get("start_inset", 0.0)
            if rafters.get("x_min", -1e9) <= start_point.x <= rafters.get("x_max", 1e9):
                carpentry.uv_offset = (carpentry.random.uniform(0, 6), carpentry.random.uniform(0, 6))
                carpentry.variation = carpentry.random.uniform(0.9, 1.05)
                carpentry.add_box(start_point - axis_along * (width / 2) - normal * depth, end_point - start_point, axis_along * width, normal * depth, material)
            along += spacing
        carpentry.variation = 1.0
        carpentry.uv_offset = (0, 0)


def cover_shingles(eave_a, eave_b, ridge_a, ridge_b, normal, thickness, covering, plane_data):
    material = plane_data.get("top_material", "shingle_wood")
    exposure = plane_data.get("exposure", 0.125)
    length_along = (eave_b - eave_a).length
    axis_along = (eave_b - eave_a).normalized()
    slope = (ridge_a - eave_a).length
    axis_up = (ridge_a - eave_a).normalized()
    base = eave_a + normal * thickness - axis_up * 0.03
    row = 0
    height = 0.0
    while height < slope:
        along = -covering.random.uniform(0, 0.12)
        while along < length_along:
            width = covering.random.uniform(0.09, 0.26)
            end_along = min(length_along, along + width)
            start_along = max(0.0, along)
            if end_along - start_along > 0.01:
                lift = covering.random.uniform(0.008, 0.016)
                skew = covering.random.uniform(-0.006, 0.006)
                bottom = height + covering.random.uniform(-0.006, 0.006)
                top = min(slope + 0.02, height + exposure * 2.2)
                covering.uv_offset = (covering.random.uniform(0, 8), covering.random.uniform(0, 8))
                covering.variation = covering.random.uniform(0.62, 1.15)
                gap = 0.0025
                lower_left = base + axis_along * (start_along + gap) + axis_up * bottom + normal * lift
                lower_right = base + axis_along * (end_along - gap) + axis_up * (bottom + skew) + normal * lift
                upper_left = base + axis_along * (start_along + gap) + axis_up * top + normal * 0.002
                upper_right = base + axis_along * (end_along - gap) + axis_up * top + normal * 0.002
                under_left = base + axis_along * (start_along + gap) + axis_up * bottom
                under_right = base + axis_along * (end_along - gap) + axis_up * (bottom + skew)
                covering.add_face([lower_left, lower_right, upper_right, upper_left], material, uvs=[(0, 0), (end_along - start_along, 0), (end_along - start_along, top - bottom), (0, top - bottom)])
                covering.add_face([under_left, under_right, lower_right, lower_left], material, uvs=[(0, 0), (end_along - start_along, 0), (end_along - start_along, 0.015), (0, 0.015)])
                covering.add_face([under_left, lower_left, upper_left], material, uvs=[(0, 0), (0, 0.015), (0.2, 0.015)])
                covering.add_face([lower_right, under_right, upper_right], material, uvs=[(0, 0), (0, 0.015), (0.2, 0.015)])
            along += width
        row += 1
        height += exposure
    covering.variation = 1.0
    covering.uv_offset = (0, 0)


def cover_roll(eave_a, eave_b, ridge_a, ridge_b, normal, thickness, covering, plane_data):
    material = plane_data.get("top_material", "roll_roofing")
    course = plane_data.get("course", 0.86)
    length_along = (eave_b - eave_a).length
    axis_along = (eave_b - eave_a).normalized()
    slope = (ridge_a - eave_a).length
    axis_up = (ridge_a - eave_a).normalized()
    base = eave_a + normal * thickness
    height = -0.02
    while height < slope:
        top = min(slope + 0.02, height + course + 0.08)
        covering.uv_offset = (covering.random.uniform(0, 8), covering.random.uniform(0, 8))
        covering.variation = covering.random.uniform(0.85, 1.05)
        lower_left = base + axis_up * height + normal * 0.006
        lower_right = lower_left + axis_along * length_along
        upper_left = base + axis_up * top + normal * 0.003
        upper_right = upper_left + axis_along * length_along
        under_left = base + axis_up * height
        under_right = under_left + axis_along * length_along
        covering.add_face([lower_left, lower_right, upper_right, upper_left], material)
        covering.add_face([under_left, under_right, lower_right, lower_left], material)
        height += course
    covering.variation = 1.0
    covering.uv_offset = (0, 0)


def build_beam(batch, data):
    start = Vector(data["a"])
    end = Vector(data["b"])
    width = data.get("w", 0.1)
    depth = data.get("d", 0.2)
    material = data.get("material", "pine_boards")
    run = end - start
    side = run.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(run).normalized()
    if up.z < 0:
        up = -up
    batch.uv_offset = (batch.random.uniform(0, 6), batch.random.uniform(0, 6))
    batch.add_box(start - side * (width / 2), run, side * width, up * depth, material)
    batch.uv_offset = (0, 0)


def build_post(batch, data):
    x_size = data.get("w", 0.1)
    y_size = data.get("d", x_size)
    x, y = data["at"]
    origin = Vector((x - x_size / 2, y - y_size / 2, data["z0"]))
    batch.uv_offset = (batch.random.uniform(0, 6), batch.random.uniform(0, 6))
    batch.add_box(origin, Vector((x_size, 0, 0)), Vector((0, y_size, 0)), Vector((0, 0, data["z1"] - data["z0"])), data.get("material", "pine_boards"))
    batch.uv_offset = (0, 0)


def build_stairs(batch, data, default_material):
    start = Vector((data["start"][0], data["start"][1], data["z0"]))
    heading = math.radians(data["heading"])
    forward = Vector((math.cos(heading), math.sin(heading), 0))
    across = Vector((-forward.y, forward.x, 0))
    width = data["width"]
    run = data["run"]
    rise = data["rise"]
    material = data.get("material", default_material)
    riser_material = data.get("riser_material", material)
    for step in range(data["steps"]):
        tread_origin = start + forward * (run * step) + across * 0 + Vector((0, 0, rise * (step + 1)))
        batch.add_box(tread_origin - Vector((0, 0, 0.022)) - forward * 0.02, forward * (run + 0.02), across * width, Vector((0, 0, 0.026)), material)
        batch.add_box(start + forward * (run * step) + Vector((0, 0, rise * step)), forward * 0.018, across * width, Vector((0, 0, rise - 0.022)), riser_material)
    length = run * data["steps"]
    height = rise * data["steps"]
    for side in (0, width - 0.03):
        stringer_origin = start + across * side
        outline = [
            stringer_origin,
            stringer_origin + forward * length,
            stringer_origin + forward * length + Vector((0, 0, height + 0.1)),
            stringer_origin + Vector((0, 0, 0.12)),
        ]
        thick = across * 0.03
        batch.add_face([outline[0], outline[1], outline[2], outline[3]], material)
        batch.add_face([point + thick for point in reversed(outline)], material)


def build_casework(batch, hardware, data, style):
    start = Vector((data["a"][0], data["a"][1], 0))
    end = Vector((data["b"][0], data["b"][1], 0))
    run = end - start
    length = run.length
    along = run.normalized()
    outward = Vector((-along.y, along.x, 0)) * data.get("side", 1)
    depth = data.get("depth", 0.58)
    bottom = data.get("z0", 0.0)
    top = data.get("z1", 0.86)
    material = data.get("material", "cabinet_birch")
    doors = data.get("doors", max(1, round(length / 0.5)))
    toe = data.get("toe", 0.1 if data.get("kind") == "base" else 0.0)
    carcass_depth = depth - 0.022
    batch.uv_offset = (batch.random.uniform(0, 6), batch.random.uniform(0, 6))
    batch.add_box(start + Vector((0, 0, bottom + toe)), along * length, outward * carcass_depth, Vector((0, 0, top - bottom - toe)), material)
    if toe > 0:
        batch.add_box(start + Vector((0, 0, bottom)), along * length, outward * (carcass_depth - 0.05), Vector((0, 0, toe)), "soot")
    door_width = length / doors
    gap = 0.003
    frame = 0.055
    for index in range(doors):
        door_start = start + along * (door_width * index + gap)
        width = door_width - 2 * gap
        low = bottom + toe + gap
        high = top - gap
        plane = outward * carcass_depth
        thick = outward * 0.018
        z_size = Vector((0, 0, high - low))
        origin = door_start + plane + Vector((0, 0, low))
        batch.variation = batch.random.uniform(0.92, 1.05)
        batch.add_box(origin, along * frame, thick, z_size, material)
        batch.add_box(origin + along * (width - frame), along * frame, thick, z_size, material)
        batch.add_box(origin + along * frame, along * (width - 2 * frame), thick, Vector((0, 0, frame)), material)
        batch.add_box(origin + along * frame + Vector((0, 0, high - low - frame)), along * (width - 2 * frame), thick, Vector((0, 0, frame)), material)
        batch.add_box(origin + along * frame + Vector((0, 0, frame)), along * (width - 2 * frame), outward * 0.008, Vector((0, 0, high - low - 2 * frame)), material)
        batch.variation = 1.0
        pull_along = width - 0.03 if index % 2 == 0 else 0.03
        pull_height = low + (0.75 * (high - low) if data.get("kind") == "base" else 0.2 * (high - low))
        pull_low = origin + along * pull_along + thick + Vector((0, 0, pull_height - low - 0.05))
        pull_high = pull_low + Vector((0, 0, 0.1))
        hardware.add_cylinder(pull_low + outward * 0.022, pull_high + outward * 0.022, 0.005, data.get("hardware", "aluminium_dull"), sides=10)
        hardware.add_cylinder(pull_low, pull_low + outward * 0.024, 0.004, data.get("hardware", "aluminium_dull"), sides=8)
        hardware.add_cylinder(pull_high, pull_high + outward * 0.024, 0.004, data.get("hardware", "aluminium_dull"), sides=8)
    batch.uv_offset = (0, 0)
    if data.get("counter"):
        nose = 0.03
        counter_material = data.get("counter_material", style.get("counter", "counter_laminate"))
        batch.add_box(start - along * data.get("nose_start", 0.0) + Vector((0, 0, top)), along * (length + data.get("nose_start", 0.0) + data.get("nose_end", 0.0)), outward * (depth + nose), Vector((0, 0, 0.032)), counter_material)
        splash_thickness = -outward * 0.0 + outward * 0.012
        batch.add_box(start + Vector((0, 0, top + 0.032)), along * length, splash_thickness, Vector((0, 0, 0.1)), counter_material)


def build_curtain(batch, data, material):
    start = Vector((data["a"][0], data["a"][1], 0))
    end = Vector((data["b"][0], data["b"][1], 0))
    run = end - start
    along = run.normalized()
    across = Vector((-along.y, along.x, 0))
    length = run.length
    folds = data.get("folds", max(3, int(length / 0.14)))
    depth = data.get("depth", 0.045)
    z_low = data["z0"]
    z_high = data["z1"]
    steps = folds * 8
    rows = 10
    grid = []
    for row in range(rows + 1):
        fraction = row / rows
        height = z_low + (z_high - z_low) * fraction
        points = []
        for step in range(steps + 1):
            position = step / steps
            wobble = math.sin(position * folds * 2 * math.pi + 0.8 * math.sin(position * 13.0))
            flare = depth * (1.0 + 0.5 * (1 - fraction)) * (0.75 + 0.25 * math.sin(position * 7.0 + fraction * 1.4))
            points.append(start + along * (length * position) + across * (wobble * flare) + Vector((0, 0, height)))
        grid.append(points)
    for row in range(rows):
        for step in range(steps):
            uvs = [(step * length / steps, row * 0.25), ((step + 1) * length / steps, row * 0.25), ((step + 1) * length / steps, (row + 1) * 0.25), (step * length / steps, (row + 1) * 0.25)]
            batch.add_face([grid[row][step], grid[row][step + 1], grid[row + 1][step + 1], grid[row + 1][step]], material, uvs=uvs)


def build_chimney(batch, data):
    x_centre, y_centre = data["at"]
    half_x = data["w"] / 2
    half_y = data["d"] / 2
    outline = [(x_centre - half_x, y_centre - half_y), (x_centre + half_x, y_centre - half_y), (x_centre + half_x, y_centre + half_y), (x_centre - half_x, y_centre + half_y)]
    material = data.get("material", "brick_red")
    batch.add_prism(outline, data["z0"], data["z1"], material, material_top="soot")
    cap = data.get("cap", 0.05)
    grow = 0.035
    outline_cap = [(x_centre - half_x - grow, y_centre - half_y - grow), (x_centre + half_x + grow, y_centre - half_y - grow), (x_centre + half_x + grow, y_centre + half_y + grow), (x_centre - half_x - grow, y_centre + half_y + grow)]
    batch.add_prism(outline_cap, data["z1"] - cap * 3, data["z1"] - cap, data.get("cap_material", material), material_top="soot")
    flue = data.get("flue", 0.18)
    outline_flue = [(x_centre - flue, y_centre - flue), (x_centre + flue, y_centre - flue), (x_centre + flue, y_centre + flue), (x_centre - flue, y_centre + flue)]
    batch.add_prism(outline_flue, data["z1"], data["z1"] + 0.09, data.get("flue_material", "soot"), material_top="soot")


def build_panelling(batch, data):
    """Raised wall panels on a flat stretch: rails, stiles and fields sitting proud of the wall."""
    start = Vector((data["a"][0], data["a"][1], 0))
    end = Vector((data["b"][0], data["b"][1], 0))
    along = (end - start).normalized()
    length = (end - start).length
    outward = Vector((-along.y, along.x, 0)) * data.get("side", 1)
    material = data.get("material", "trim_cream")
    z_low = data["z0"]
    z_high = data["z1"]
    columns = data.get("cols", 3)
    rows = data.get("rows", 2)
    stile = data.get("stile", 0.09)
    depth = 0.018
    origin = start + Vector((0, 0, z_low)) + outward * data.get("offset", 0.0)
    pane_width = (length - stile * (columns + 1)) / columns
    pane_height = (z_high - z_low - stile * (rows + 1)) / rows
    for column in range(columns + 1):
        batch.add_box(origin + along * (column * (pane_width + stile)), along * stile, outward * depth, Vector((0, 0, z_high - z_low)), material)
    for row in range(rows + 1):
        batch.add_box(origin + Vector((0, 0, row * (pane_height + stile))), along * length, outward * depth, Vector((0, 0, stile)), material)
    for column in range(columns):
        for row in range(rows):
            low = origin + along * (stile + column * (pane_width + stile)) + Vector((0, 0, stile + row * (pane_height + stile)))
            margin = 0.03
            corners_outer = [low, low + along * pane_width, low + along * pane_width + Vector((0, 0, pane_height)), low + Vector((0, 0, pane_height))]
            field_origin = low + along * margin + Vector((0, 0, margin)) + outward * (depth * 0.8)
            corners_inner = [field_origin, field_origin + along * (pane_width - 2 * margin), field_origin + along * (pane_width - 2 * margin) + Vector((0, 0, pane_height - 2 * margin)), field_origin + Vector((0, 0, pane_height - 2 * margin))]
            order = (0, 1, 2, 3) if data.get("side", 1) < 0 else (3, 2, 1, 0)
            for index in range(4):
                first = order[index]
                second = order[(index + 1) % 4]
                batch.add_face([corners_outer[first], corners_outer[second], corners_inner[second], corners_inner[first]], material)
            batch.add_face([corners_inner[index] for index in order], material)


def build_fireplace(structure, wall, opening, batch):
    """Firebox behind a wall opening: brick back and cheeks, soot inside, hearth stone on the floor, plain surround."""
    floor_z = structure.plan["levels"].get("floor", 0.0)
    side = opening.get("room_side", 1)
    depth = opening.get("depth", 0.55)
    start = opening["from"]
    finish = opening["to"]
    head = opening["head"] + floor_z
    half = wall.t / 2
    material = opening.get("brick", "brick_red")
    firebox = opening.get("firebox", 0.5)
    add_rail(batch, wall, start, finish, -side * firebox, 0, -side * 0.08, floor_z, head + 0.25, material)
    add_rail(batch, wall, start, start + 0.08, 0, -side * firebox, side * half, floor_z, head, material)
    add_rail(batch, wall, finish - 0.08, finish, 0, -side * firebox, side * half, floor_z, head, material)
    add_rail(batch, wall, start, finish, 0, -side * firebox, side * half, head - 0.1, head, "soot")
    add_rail(batch, wall, start, finish, 0, -side * firebox, side * half, floor_z, floor_z + 0.03, opening.get("hearth", "stone_rubble"))
    add_rail(batch, wall, start - 0.25, finish + 0.25, side * half, 0, side * depth, floor_z, floor_z + 0.03, opening.get("hearth", "stone_rubble"))
    add_rail(batch, wall, start, finish, 0, -side * half, side * half, floor_z, floor_z + 0.03, opening.get("hearth", "stone_rubble"))
    trim_material = opening.get("surround", "trim_cream")
    add_rail(batch, wall, start - 0.14, start, side * half, 0, side * 0.03, floor_z, head + 0.14, trim_material)
    add_rail(batch, wall, finish, finish + 0.14, side * half, 0, side * 0.03, floor_z, head + 0.14, trim_material)
    add_rail(batch, wall, start - 0.14, finish + 0.14, side * half, 0, side * 0.03, head, head + 0.14, trim_material)
