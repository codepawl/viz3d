"""Build a house from a checked plan file into a .blend, with an as-built wall section for the overlay check.

Run: blender -b --factory-startup -P build_house.py -- <plan.json> <output.blend>
The plan format is in ../references/plan-format.md.
"""

import json
import math
import pathlib
import random
import sys
import time

import bpy
from mathutils import Vector, noise

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import house_core  # noqa: E402
import house_parts  # noqa: E402
from house_core import MeshBatch, section_segments  # noqa: E402

METRES_PER_UNIT = {"m": 1.0, "ft": 0.3048}
SECTION_HEIGHT_METRES = 1.6
LENGTH_KEYS = {
    "a", "b", "t", "h", "z0", "z1", "from", "to", "at", "width", "sill", "head", "poly", "corners", "thickness",
    "spacing", "w", "d", "first", "start_inset", "x_min", "x_max", "start", "run", "rise", "depth", "ceiling", "floor_z",
    "baseboard", "crown", "chair_rail", "transom_at", "shutters", "fascia_depth", "exposure", "course", "cap", "flue",
    "nose_start", "nose_end", "toe", "stile", "offset", "fit_w", "fit_h", "fit_max", "z", "pos", "look", "grass_radius",
    "radius", "path", "no_grass", "fit_size", "ground_level", "heights", "ground_size", "reach", "side_offset", "section_z", "centre", "flat_radius", "origin", "x", "y",
}
KEEP_AS_IS = {"px", "plan_px", "sun", "pairs", "printed_dimensions", "calibration", "source", "provenance", "furnish_notes", "style"}


def convert_lengths(value, scale, key=None):
    """Turn every length in the plan into metres, leaving counts, names and angles alone."""
    if isinstance(value, dict):
        return {name: (item if name in KEEP_AS_IS else convert_lengths(item, scale, name)) for name, item in value.items()}
    if isinstance(value, list):
        return [convert_lengths(item, scale, key) for item in value]
    if isinstance(value, (int, float)) and not isinstance(value, bool) and key in LENGTH_KEYS:
        return value * scale
    return value


def load_plan(path):
    raw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    scale = METRES_PER_UNIT[raw.get("units", "m")]
    plan = convert_lengths(raw, scale)
    plan["levels"] = {name: length * scale for name, length in raw["levels"].items()}
    style = dict(raw.get("style", {}))
    for key in ("exterior_casing", "interior_casing", "corner_board", "baseboard"):
        if key in style:
            style[key] = style[key] * scale
    plan["style"] = style
    plan["_folder"] = pathlib.Path(path).resolve().parent
    return plan


def new_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def build_floors(plan, collection):
    batch = MeshBatch("floors", 11)
    levels = plan["levels"]
    style = plan["style"]
    floor_z = levels.get("floor", 0.0)
    for room in plan["rooms"]:
        material = room.get("floor", style.get("floor", "oak_floor"))
        outline = room["poly"]
        points = [Vector((point[0], point[1], floor_z + room.get("floor_z", 0.0))) for point in outline]
        batch.uv_offset = (batch.random.uniform(0, 9), batch.random.uniform(0, 9))
        batch.add_face(points, material, uvs=[(point[0], point[1]) for point in outline])
    batch.uv_offset = (0, 0)
    for slab in plan.get("slabs", []):
        batch.add_prism(slab["poly"], slab["z"] - slab.get("t", 0.1), slab["z"], slab.get("side_material", slab["material"]), material_top=slab["material"])
    batch.finish(collection)


def build_ceilings(plan, collection):
    batch = MeshBatch("ceilings", 12)
    floor_z = plan["levels"].get("floor", 0.0)
    for room in plan["rooms"]:
        height = room.get("ceiling")
        if height is None:
            continue
        points = [Vector((point[0], point[1], floor_z + height)) for point in reversed(room["poly"])]
        batch.add_face(points, room.get("ceiling_material", plan["style"].get("ceiling", "ceiling_paint")), uvs=[(point[0], point[1]) for point in reversed(room["poly"])])
    batch.finish(collection)


def build_structure(plan, structure, collections):
    style = plan["style"]
    reveal = style.get("reveal", style["interior_wall"])
    for wall in structure.walls:
        batch = MeshBatch(f"wall_{wall.id}", hash(wall.id) & 0xffff)
        house_parts.build_wall(structure, wall, batch, reveal)
        batch.finish(collections["walls"])

    siding = MeshBatch("siding", 21)
    trim = MeshBatch("trim", 22)
    glass = MeshBatch("glazing", 23)
    hardware = MeshBatch("hardware", 24)
    siding_kind = style.get("siding", "clapboard")
    siding_material = style.get("siding_material", "siding_white")
    for wall in structure.walls:
        if not wall.outside_side:
            house_parts.build_baseboards(structure, wall, trim)
            continue
        house_parts.build_baseboards(structure, wall, trim)
        if siding_kind == "clapboard":
            house_parts.siding_clapboard(structure, wall, siding, siding_material, style.get("exposure", house_parts.BOARD_EXPOSURE_CLAPBOARD))
        elif siding_kind == "batten":
            house_parts.siding_board_batten(structure, wall, siding, siding_material, style.get("batten_material", siding_material))
        house_parts.build_corner_boards(structure, wall, trim, style.get("corner_material", style.get("window_material", "trim_white")))
    for wall in structure.walls:
        for opening in wall.openings:
            kind = opening.get("kind")
            if kind == "window":
                house_parts.build_window(structure, wall, opening, trim, glass)
            elif kind in ("door", "cased"):
                house_parts.build_door(structure, wall, opening, trim, hardware)
            elif kind == "fireplace":
                house_parts.build_fireplace(structure, wall, opening, trim)
    siding.finish(collections["facade"])
    trim.finish(collections["facade"], bevel=0.0022)
    glass.finish(collections["facade"])
    hardware.finish(collections["facade"], smooth=True)

    roof_collection = collections["roof"]
    deck = MeshBatch("roof_deck", 31)
    covering = MeshBatch("roof_cover", 32)
    carpentry = MeshBatch("roof_carpentry", 33)
    for plane in structure.roof_planes:
        house_parts.build_roof_plane(plane.data, plane, deck, covering, carpentry, style)
    deck.finish(roof_collection)
    covering.finish(roof_collection)
    carpentry.finish(roof_collection, bevel=0.003)

    timber = MeshBatch("timber", 34)
    for beam in plan.get("beams", []):
        house_parts.build_beam(timber, beam)
    for post in plan.get("posts", []):
        house_parts.build_post(timber, post)
    timber.finish(collections["frame"], bevel=0.003)

    upper = MeshBatch("chimneys", 35)
    for chimney in plan.get("chimneys", []):
        house_parts.build_chimney(upper, chimney)
    upper.finish(roof_collection)

    fitted = MeshBatch("casework", 41)
    fitted_hardware = MeshBatch("casework_hardware", 42)
    for unit in plan.get("casework", []):
        house_parts.build_casework(fitted, fitted_hardware, unit, style)
    for stair in plan.get("stairs", []):
        house_parts.build_stairs(fitted, stair, style.get("stair", "old_floor"))
    for panel in plan.get("panelling", []):
        house_parts.build_panelling(fitted, panel)
    for shelf in plan.get("boxes", []):
        fitted.uv_offset = (fitted.random.uniform(0, 6), fitted.random.uniform(0, 6))
        origin = Vector(shelf["origin"])
        fitted.add_box(origin, Vector(shelf["x"]), Vector(shelf["y"]), Vector(shelf["z"]), shelf["material"])
    fitted.uv_offset = (0, 0)
    fitted.finish(collections["fitted"], bevel=0.0015)
    fitted_hardware.finish(collections["fitted"], smooth=True)

    fabric = MeshBatch("fabric", 51)
    for curtain in plan.get("curtains", []):
        house_parts.build_curtain(fabric, curtain, curtain.get("material", "curtain_plain"))
    for rug in plan.get("rugs", []):
        x0, y0 = rug["a"]
        x1, y1 = rug["b"]
        z = plan["levels"].get("floor", 0.0)
        outline = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        fabric.add_prism(outline, z, z + 0.012, rug.get("material", "fabric_rug"))
    fabric_object = fabric.finish(collections["fitted"], smooth=True)
    return fabric_object


def asset_path(plan, asset):
    kind, name = asset.split(":", 1)
    if kind == "ph":
        root = house_core.LIBRARY / "models" / name
        matches = sorted(root.glob("*.gltf"))
        return matches[0] if matches else None
    if kind == "obj":
        library = plan.get("site", {}).get("objaverse_folder", "../_lib/objaverse")
        return plan["_folder"] / library / f"{name}.glb"
    raise KeyError(asset)


_asset_cache = {}


def bounding_box(objects):
    corners = []
    for item in objects:
        if item.type != "MESH":
            continue
        for corner in item.bound_box:
            corners.append(item.matrix_world @ Vector(corner))
    if not corners:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return low, high


def keep_one_part(imported, part):
    """Poly Haven plant sets lay their variants out in a row: keep one mesh, numbered from low x to high x."""
    meshes = [item for item in imported if item.type == "MESH"]
    meshes.sort(key=lambda item: bounding_box([item])[0].x)
    chosen = meshes[part % len(meshes)]
    world = chosen.matrix_world.copy()
    chosen.parent = None
    chosen.matrix_world = world
    for item in imported:
        if item is not chosen:
            bpy.data.objects.remove(item)
    bpy.context.view_layer.update()
    return [chosen]


def cache_file(asset, part):
    return house_core.LIBRARY / "blender_cache" / f"{asset.replace(':', '_')}_{part}.blend"


def write_asset_cache(path, cached):
    """A glTF import takes minutes for a scanned tree; a linked .blend takes a moment and adds nothing to the house file."""
    existing = set(bpy.data.objects)
    started = time.perf_counter()
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [item for item in bpy.data.objects if item not in existing]
    bpy.context.view_layer.update()
    print(f"imported {path.name}: {sum(1 for item in imported if item.type == 'MESH')} meshes, {time.perf_counter() - started:.1f} s", flush=True)
    return imported


def load_asset(plan, asset, library_collection, part=None):
    cache_key = (asset, part)
    if cache_key in _asset_cache:
        return _asset_cache[cache_key]
    path = asset_path(plan, asset)
    if path is None or not path.exists():
        print("MISSING ASSET", asset)
        _asset_cache[cache_key] = None
        return None
    cached = cache_file(asset, part)
    if not cached.exists():
        imported = write_asset_cache(path, cached)
        if part is not None:
            imported = keep_one_part(imported, part)
        cached.parent.mkdir(parents=True, exist_ok=True)
        bpy.data.libraries.write(str(cached), set(imported), fake_user=True)
        for item in imported:
            bpy.data.objects.remove(item)
        bpy.data.batch_remove([block for block in bpy.data.meshes if block.users == 0])
    with bpy.data.libraries.load(str(cached), link=True) as (source, target):
        target.objects = source.objects
    linked = [item for item in target.objects if item is not None]
    collection = bpy.data.collections.new(f"asset_{asset.replace(':', '_')}_{part}")
    library_collection.children.link(collection)
    for item in linked:
        collection.objects.link(item)
    # Linked objects keep stale world matrices until the depsgraph runs; without this, sizes come out wrong and beds float.
    bpy.context.view_layer.update()
    low, high = bounding_box(linked)
    collection.instance_offset = ((low.x + high.x) / 2, (low.y + high.y) / 2, low.z)
    _asset_cache[cache_key] = (collection, high - low)
    return _asset_cache[cache_key]


def overhead_height(plan, x, y):
    """Lowest ceiling or roof underside above a point, for hanging a lamp from it."""
    heights = []
    for plane in plan.get("roof", {}).get("planes", []):
        height = house_parts.RoofPlane(plane).height_at(x, y)
        if height is not None:
            heights.append(height)
    for room in plan["rooms"]:
        if room.get("ceiling") and house_parts.inside_polygon((x, y), room["poly"]):
            heights.append(plan["levels"].get("floor", 0.0) + room["ceiling"])
    return min(heights) if heights else plan["levels"].get("floor", 0.0) + plan["levels"].get("ceiling", 2.4)


_painted_cache = {}


def painted_copy(collection, material_name, library_collection):
    """A model whose own materials are bad or missing, every part in one of ours. The linked data stays untouched."""
    cache_key = (collection.name, material_name)
    if cache_key in _painted_cache:
        return _painted_cache[cache_key]
    painted = bpy.data.collections.new(f"{collection.name}_{material_name}")
    library_collection.children.link(painted)
    material = house_core.get_material(material_name)
    for source in collection.objects:
        part = source.copy()
        painted.objects.link(part)
        for slot in part.material_slots:
            slot.link = "OBJECT"
            slot.material = material
    painted.instance_offset = collection.instance_offset
    _painted_cache[cache_key] = painted
    return painted


def place_asset(plan, item, library_collection, target_collection, report, on_ground=False):
    loaded = load_asset(plan, item["asset"], library_collection, item.get("part"))
    if loaded is None:
        return None
    collection, size = loaded
    if "paint" in item:
        collection = painted_copy(collection, item["paint"], library_collection)
    scale = item.get("scale", 1.0)
    if "fit_w" in item and max(size.x, size.y) > 0:
        scale = item["fit_w"] / max(size.x, size.y)
    if "fit_h" in item and size.z > 0:
        scale = item["fit_h"] / size.z
    if "fit_max" in item and max(size) > 0:
        scale = item["fit_max"] / max(size)
    scales = Vector((scale, scale, scale))
    if "fit_size" in item:
        scales = Vector((item["fit_size"][axis] / size[axis] for axis in range(3)))
    instance = bpy.data.objects.new(item.get("name", collection.name), None)
    instance.instance_type = "COLLECTION"
    instance.instance_collection = collection
    x, y = item["at"]
    height = item.get("z", plan["levels"].get("floor", 0.0))
    if on_ground:
        height = site_ground_z(plan, x, y) + item.get("z", 0.0)
    if item.get("hang"):
        height = overhead_height(plan, x, y) - size.z * scales.z
    instance.location = (x, y, height)
    instance.rotation_euler = (0, 0, math.radians(item.get("rot", 0)))
    instance.scale = scales
    target_collection.objects.link(instance)
    placed_size = Vector((size[axis] * scales[axis] for axis in range(3)))
    report["placed"].append({"asset": item["asset"], "at": [round(x, 2), round(y, 2)], "z": round(height, 2), "size_m": [round(value, 2) for value in placed_size]})
    return instance, placed_size


def footprint_corners(item, size):
    x, y = item["at"]
    angle = math.radians(item.get("rot", 0))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    corners = []
    for sign_x, sign_y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        local_x = sign_x * size.x / 2
        local_y = sign_y * size.y / 2
        corners.append((x + local_x * cosine - local_y * sine, y + local_x * sine + local_y * cosine))
    return corners


def furniture_clashes(structure, item, size):
    """Walls the footprint of a floor-standing piece runs through, ignoring anything under 8 cm of overlap."""
    corners = footprint_corners(item, size)
    clashes = []
    for wall in structure.walls:
        inside_points = 0
        for corner in corners:
            along = (Vector(corner) - wall.a).dot(wall.direction)
            across = abs((Vector(corner) - wall.a).dot(wall.normal))
            if wall.s0 <= along <= wall.s1 and across < wall.t / 2 - 0.08:
                inside_points += 1
        if inside_points:
            clashes.append(wall.id)
    return clashes


def furnish(plan, structure, collections, report):
    library_collection = collections["library"]
    for item in plan.get("furnish", []):
        placed = place_asset(plan, item, library_collection, collections["furnish"], report)
        if placed is None:
            report["missing"].append(item["asset"])
            continue
        _, size = placed
        if item.get("z") is None or item.get("z", 0) < 0.05:
            clashes = furniture_clashes(structure, item, size)
            if clashes:
                report["clashes"].append({"asset": item["asset"], "walls": clashes})
    for item in plan.get("site", {}).get("plants", []):
        placed = place_asset(plan, item, library_collection, collections["site"], report, on_ground=True)
        if placed is None:
            report["missing"].append(item["asset"])
    for item in treeline_items(plan):
        place_asset(plan, item, library_collection, collections["site"], report, on_ground=True)


def treeline_items(plan):
    """A ring of trees far enough out to close the horizon; azimuths in `skip` stay open as views."""
    line = plan.get("site", {}).get("treeline")
    if not line:
        return []
    if isinstance(line, list):
        return [item for ring in line for item in treeline_ring(plan, ring)]
    return treeline_ring(plan, line)


def treeline_ring(plan, line):
    generator = random.Random(11 + int(line["radius"]))
    centre = plan["site"].get("centre", [0, 0])
    low_height, high_height = line.get("heights", [10.0, 20.0])
    items = []
    for index in range(line.get("count", 60)):
        azimuth = 360.0 * (index + generator.uniform(-0.3, 0.3)) / line.get("count", 60)
        if any(start <= azimuth % 360 <= end for start, end in line.get("skip", [])):
            continue
        reach = line["radius"] * generator.uniform(0.9, 1.45)
        items.append({
            "asset": generator.choice(line["assets"]),
            "at": [centre[0] + reach * math.cos(math.radians(azimuth)), centre[1] + reach * math.sin(math.radians(azimuth))],
            "rot": generator.uniform(0, 360),
            "fit_h": generator.uniform(low_height, high_height),
        })
    return items


def ground_height(x, y, keep_flat_polygon_centre, flat_radius):
    distance_from_house = math.hypot(x - keep_flat_polygon_centre[0], y - keep_flat_polygon_centre[1])
    fade = min(1.0, max(0.0, (distance_from_house - flat_radius) / 30.0))
    rolling = noise.noise(Vector((x * 0.035, y * 0.035, 3.1))) * 1.6
    lumps = noise.noise(Vector((x * 0.6, y * 0.6, 9.4))) * 0.035
    return rolling * fade + lumps


def site_ground_z(plan, x, y):
    site = plan.get("site", {})
    level = site.get("ground_level", -0.03)
    return level + ground_height(x, y, site.get("centre", [0, 0]), site.get("flat_radius", 14.0))


def build_path(path, plan, batch):
    """A four-cornered path follows the ground in short strips, with slightly uneven edges."""
    corners = [Vector((point[0], point[1])) for point in path["poly"]]
    length = max((corners[1] - corners[2]).length, (corners[0] - corners[3]).length)
    strips = max(2, int(length / 0.5))
    material = path.get("material", "gravel_path")
    rows = []
    for strip in range(strips + 1):
        fraction = strip / strips
        left = corners[0].lerp(corners[3], fraction)
        right = corners[1].lerp(corners[2], fraction)
        wobble_left = noise.noise(Vector((left.x * 1.3, left.y * 1.3, 4.0))) * 0.08
        wobble_right = noise.noise(Vector((right.x * 1.3, right.y * 1.3, 7.0))) * 0.08
        across = (right - left).normalized()
        left = left + across * wobble_left
        right = right + across * wobble_right
        rows.append([Vector((point.x, point.y, site_ground_z(plan, point.x, point.y) + path.get("rise", 0.035))) for point in (left, right)])
    for strip in range(strips):
        quad = [rows[strip][0], rows[strip][1], rows[strip + 1][1], rows[strip + 1][0]]
        batch.add_face(quad, material, uvs=[(point.x, point.y) for point in quad])


def matte_ground(ground):
    """Soil has no sheen. A scanned roughness map left in place mirrors the sky at grazing angles as white patches."""
    for material in ground.data.materials:
        surface = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if surface is None:
            continue
        for link in list(surface.inputs["Roughness"].links):
            material.node_tree.links.remove(link)
        surface.inputs["Roughness"].default_value = 0.95
        surface.inputs["Specular IOR Level"].default_value = 0.15


def build_ground(plan, collection):
    site = plan.get("site", {})
    size = site.get("ground_size", 180.0)
    centre = site.get("centre", [0, 0])
    resolution = 260
    batch = MeshBatch("ground", 61)
    material = site.get("ground", "grass_ground")
    grid = []
    start = len(batch.vertices)
    for row in range(resolution + 1):
        for column in range(resolution + 1):
            x = centre[0] - size / 2 + size * column / resolution
            y = centre[1] - size / 2 + size * row / resolution
            batch.vertices.append(Vector((x, y, site_ground_z(plan, x, y))))
            grid.append((x, y))
    for row in range(resolution):
        for column in range(resolution):
            first = start + row * (resolution + 1) + column
            indices = [first, first + 1, first + resolution + 2, first + resolution + 1]
            uvs = [grid[index - start] for index in indices]
            batch.add_face([batch.vertices[index] for index in indices], material, uvs=uvs, indices=indices)
    ground = batch.finish(collection, smooth=True)
    matte_ground(ground)

    paths = MeshBatch("paths", 62)
    for path in site.get("paths", []):
        build_path(path, plan, paths)
    paths.finish(collection)
    return ground


def make_grass_material():
    """Blades get their colour per tuft plus a slow patchy drift, and let some light through."""
    material = bpy.data.materials.new("grass_blade")
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    info = tree.nodes.new("ShaderNodeObjectInfo")
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    stops = ramp.color_ramp.elements
    stops[0].position = 0.0
    stops[0].color = (0.045, 0.075, 0.022, 1)
    stops[1].position = 1.0
    stops[1].color = (0.19, 0.16, 0.06, 1)
    middle = stops.new(0.55)
    middle.color = (0.085, 0.115, 0.035, 1)
    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    patches = tree.nodes.new("ShaderNodeTexNoise")
    patches.inputs["Scale"].default_value = 0.22
    patches.inputs["Detail"].default_value = 3.0
    blend = tree.nodes.new("ShaderNodeMath")
    blend.operation = "MULTIPLY_ADD"
    blend.inputs[1].default_value = 0.45
    tree.links.new(geometry.outputs["Position"], patches.inputs["Vector"])
    tree.links.new(info.outputs["Random"], blend.inputs[0])
    tree.links.new(patches.outputs["Fac"], blend.inputs[2])
    tree.links.new(blend.outputs[0], ramp.inputs["Fac"])
    surface = tree.nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Roughness"].default_value = 0.5
    surface.inputs["Specular IOR Level"].default_value = 0.35
    through = tree.nodes.new("ShaderNodeBsdfTranslucent")
    mix = tree.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.3
    tree.links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    tree.links.new(ramp.outputs["Color"], through.inputs["Color"])
    tree.links.new(surface.outputs[0], mix.inputs[1])
    tree.links.new(through.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs["Surface"])
    return material


def make_grass_tuft(name, seed, material, collection):
    """One tuft of curved tapered blades about 10 cm tall; the tuft is repeated, never the single blade."""
    generator = random.Random(seed)
    vertices = []
    faces = []
    for _ in range(26):
        base_angle = generator.uniform(0, 2 * math.pi)
        base_reach = generator.uniform(0.0, 0.075)
        root = Vector((math.cos(base_angle) * base_reach, math.sin(base_angle) * base_reach, 0.0))
        bend_angle = generator.uniform(0, 2 * math.pi)
        bend = Vector((math.cos(bend_angle), math.sin(bend_angle), 0.0))
        side = Vector((-bend.y, bend.x, 0.0))
        height = generator.uniform(0.06, 0.15)
        lean = generator.uniform(0.2, 0.7) * height
        half_width = generator.uniform(0.0022, 0.0042)
        first = len(vertices)
        segments = 4
        for segment in range(segments + 1):
            fraction = segment / segments
            centre = root + Vector((0, 0, height * fraction)) + bend * (lean * fraction * fraction)
            width = half_width * (1.0 - fraction ** 2.2)
            vertices.append(centre + side * width)
            vertices.append(centre - side * width)
        for segment in range(segments):
            low = first + segment * 2
            faces.append((low, low + 1, low + 3, low + 2))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(vertex) for vertex in vertices], [], faces)
    mesh.polygons.foreach_set("use_smooth", [True] * len(faces))
    mesh.materials.append(material)
    tuft = bpy.data.objects.new(name, mesh)
    collection.objects.link(tuft)
    return tuft


GRASS_GRID_METRES = 4.0


def polygon_grid(polygons):
    """Polygons by the grid cells their bounds touch: testing a whole street's outlines per tuft took 20 minutes."""
    grid = {}
    for polygon in polygons:
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        for column in range(int(min(xs) // GRASS_GRID_METRES), int(max(xs) // GRASS_GRID_METRES) + 1):
            for row in range(int(min(ys) // GRASS_GRID_METRES), int(max(ys) // GRASS_GRID_METRES) + 1):
                grid.setdefault((column, row), []).append(polygon)
    return grid


def scatter_grass(plan, collection, library_collection):
    site = plan.get("site", {})
    radius = site.get("grass_radius", 0.0)
    if radius <= 0:
        return
    prototypes = bpy.data.collections.new("grass_prototypes")
    library_collection.children.link(prototypes)
    grass_material = make_grass_material()
    for seed in range(4):
        make_grass_tuft(f"tuft_{seed}", seed, grass_material, prototypes)
    exclusions = [room["poly"] for room in plan["rooms"]]
    exclusions += [slab["poly"] for slab in plan.get("slabs", [])]
    exclusions += [path["poly"] for path in site.get("paths", [])]
    exclusions += site.get("no_grass", [])
    keep_out = polygon_grid(exclusions)
    centre = site.get("centre", [0, 0])
    density = site.get("grass_density", 90.0)
    full_density_reach = radius * 0.4
    generator = random.Random(5)
    wanted = int(math.pi * radius * radius * density)
    points = []
    rotations = []
    scales = []
    for _ in range(wanted):
        reach = radius * math.sqrt(generator.random())
        # Further out fewer tufts stand in for more grass, each one bigger.
        spread = max(1.0, reach / full_density_reach)
        if generator.random() > 1.0 / (spread * spread):
            continue
        angle = generator.random() * 2 * math.pi
        x = centre[0] + reach * math.cos(angle)
        y = centre[1] + reach * math.sin(angle)
        cell = (int(x // GRASS_GRID_METRES), int(y // GRASS_GRID_METRES))
        if any(house_parts.inside_polygon((x, y), polygon) for polygon in keep_out.get(cell, ())):
            continue
        points.append((x, y, site_ground_z(plan, x, y) - 0.005))
        rotations.append((generator.uniform(-0.15, 0.15), generator.uniform(-0.15, 0.15), generator.random() * 6.283))
        scale = generator.uniform(0.75, 1.3) * site.get("grass_scale", 1.0) * spread
        scales.append((scale, scale, generator.uniform(0.85, 1.25) * site.get("grass_scale", 1.0) * math.sqrt(spread)))
    mesh = bpy.data.meshes.new("grass_points")
    mesh.from_pydata(points, [], [])
    rotation_attribute = mesh.attributes.new("grass_rotation", "FLOAT_VECTOR", "POINT")
    scale_attribute = mesh.attributes.new("grass_scale", "FLOAT_VECTOR", "POINT")
    for index in range(len(points)):
        rotation_attribute.data[index].vector = rotations[index]
        scale_attribute.data[index].vector = scales[index]
    carrier = bpy.data.objects.new("grass", mesh)
    collection.objects.link(carrier)
    tree = bpy.data.node_groups.new("grass_scatter", "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    group_in = tree.nodes.new("NodeGroupInput")
    group_out = tree.nodes.new("NodeGroupOutput")
    on_points = tree.nodes.new("GeometryNodeInstanceOnPoints")
    on_points.inputs["Pick Instance"].default_value = True
    info = tree.nodes.new("GeometryNodeCollectionInfo")
    info.inputs["Collection"].default_value = prototypes
    info.inputs["Separate Children"].default_value = True
    info.inputs["Reset Children"].default_value = True
    random_index = tree.nodes.new("FunctionNodeRandomValue")
    random_index.data_type = "INT"
    random_index.inputs["Min"].default_value = 0
    random_index.inputs["Max"].default_value = 100
    rotation = tree.nodes.new("GeometryNodeInputNamedAttribute")
    rotation.data_type = "FLOAT_VECTOR"
    rotation.inputs["Name"].default_value = "grass_rotation"
    scale_node = tree.nodes.new("GeometryNodeInputNamedAttribute")
    scale_node.data_type = "FLOAT_VECTOR"
    scale_node.inputs["Name"].default_value = "grass_scale"
    tree.links.new(group_in.outputs[0], on_points.inputs["Points"])
    tree.links.new(info.outputs[0], on_points.inputs["Instance"])
    tree.links.new(random_index.outputs[0], on_points.inputs["Instance Index"])
    tree.links.new(rotation.outputs["Attribute"], on_points.inputs["Rotation"])
    tree.links.new(scale_node.outputs["Attribute"], on_points.inputs["Scale"])
    tree.links.new(on_points.outputs[0], group_out.inputs[0])
    modifier = carrier.modifiers.new("scatter", "NODES")
    modifier.node_group = tree
    print(f"grass: {len(points)} tufts")


def write_section(plan, collections, output_path):
    segments = {}
    bpy.context.view_layer.update()
    base_by_object = {f"wall_{wall['id']}": wall.get("z0", plan["levels"].get("floor", 0.0)) for wall in plan["walls"]}
    for item in collections["walls"].objects:
        found = section_segments(item, base_by_object.get(item.name, 0.0) + SECTION_HEIGHT_METRES)
        if found:
            segments[item.name] = found
    output_path.write_text(json.dumps({"height": SECTION_HEIGHT_METRES, "segments": segments}), encoding="utf-8")
    print("wrote", output_path)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    plan = load_plan(arguments[0])
    output = pathlib.Path(arguments[1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collections = {name: new_collection(name) for name in ("walls", "floors", "ceilings", "facade", "roof", "frame", "fitted", "furnish", "site", "library")}
    structure = house_parts.Structure(plan)
    clock = time.perf_counter()

    def phase_done(name):
        nonlocal clock
        print(f"phase {name}: {time.perf_counter() - clock:.1f} s", flush=True)
        clock = time.perf_counter()

    build_floors(plan, collections["floors"])
    build_ceilings(plan, collections["ceilings"])
    build_structure(plan, structure, collections)
    phase_done("structure")
    report = {"placed": [], "clashes": [], "missing": []}
    furnish(plan, structure, collections, report)
    phase_done("furnish")
    build_ground(plan, collections["site"])
    phase_done("ground")
    scatter_grass(plan, collections["site"], collections["library"])
    phase_done("grass")
    layer_collection = bpy.context.view_layer.layer_collection.children["library"]
    layer_collection.exclude = True
    write_section(plan, collections, output.with_name(output.stem + "_section.json"))
    output.with_name(output.stem + "_build_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for clash in report["clashes"]:
        print("CLASH", clash)
    for missing in report["missing"]:
        print("MISSING", missing)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    phase_done("save")
    print("saved", output)



# build_street.py imports this module; every other way in is a build.
if __name__ != "build_house":
    main()
