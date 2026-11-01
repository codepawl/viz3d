"""Render stills, a cutaway or a walkthrough from a house .blend made by build_house.py.

Run: blender -b <house.blend> -P render_house.py -- <plan.json> <output-folder> [--shots a,b] [--samples N]
     [--scale 50] [--film name] [--frames N]
Shots and walks are listed in the plan. Paths are written by Cycles with OptiX, denoised with OIDN.
"""

import json
import math
import os
import pathlib
import sys
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector

METRES_PER_UNIT = {"m": 1.0, "ft": 0.3048}
LIBRARY = pathlib.Path(os.environ.get("HOUSE_ASSET_LIBRARY", pathlib.Path.home() / "house-assets"))
# Scene-linear median an interior shot is metered to: a little above mid grey, because rooms are mostly pale.
INTERIOR_METER_TARGET = 0.2


options_plan_folder = "."


def read_arguments():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    options = {"plan": arguments[0], "out": arguments[1], "shots": None, "samples": 512, "scale": 100, "film": None, "frames": None}
    index = 2
    while index < len(arguments):
        name = arguments[index].lstrip("-")
        value = arguments[index + 1]
        options[name] = value
        index += 2
    return options


def setup_cycles(samples, scale_percent):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    cycles = scene.cycles
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    cycles.device = "GPU"
    cycles.samples = samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.012
    cycles.use_denoising = True
    cycles.denoiser = "OPENIMAGEDENOISE"
    cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    cycles.denoising_use_gpu = True
    cycles.max_bounces = 10
    cycles.diffuse_bounces = 8
    cycles.glossy_bounces = 4
    cycles.transmission_bounces = 8
    cycles.transparent_max_bounces = 8
    cycles.sample_clamp_indirect = 8.0
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.blur_glossy = 0.5
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = scale_percent
    # Grass and scanned trees take minutes to sync; keep them between shots.
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


def find_sun_azimuth(image):
    """Azimuth of the brightest spot in an equirectangular sky, in radians, measured as world rotation zero sees it."""
    import numpy

    width, height = image.size
    pixels = numpy.empty(width * height * 4, dtype=numpy.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, 4)
    luminance = pixels[:, :, 0] * 0.2 + pixels[:, :, 1] * 0.7 + pixels[:, :, 2] * 0.1
    row, column = numpy.unravel_index(numpy.argmax(luminance), luminance.shape)
    return (column / width) * 2 * math.pi


def setup_world(site):
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    coordinates = tree.nodes.new("ShaderNodeTexCoord")
    mapping = tree.nodes.new("ShaderNodeMapping")
    environment = tree.nodes.new("ShaderNodeTexEnvironment")
    hdri = site.get("hdri", "kloofendal_48d_partly_cloudy_puresky")
    matches = sorted((LIBRARY / "hdri").glob(f"{hdri}_*k.hdr"))
    environment.image = bpy.data.images.load(str(matches[-1]), check_existing=True)
    tree.links.new(coordinates.outputs["Generated"], mapping.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], environment.inputs["Vector"])
    # The sky's own sun is clamped away so that the sun lamp alone casts the sharp shadow.
    clamp = tree.nodes.new("ShaderNodeVectorMath")
    clamp.operation = "MINIMUM"
    clamp.inputs[1].default_value = (site.get("sky_clamp", 12.0),) * 3
    tree.links.new(environment.outputs["Color"], clamp.inputs[0])
    tree.links.new(clamp.outputs["Vector"], background.inputs["Color"])
    background.inputs["Strength"].default_value = site.get("sky_strength", 1.0)

    sun_data = site.get("sun", {})
    azimuth = math.radians(sun_data.get("azimuth", 135.0))
    elevation = math.radians(sun_data.get("elevation", 40.0))
    hdri_sun = find_sun_azimuth(environment.image)
    # In Blender's equirect mapping, u = 0.5 looks along -Y; the texture rotates opposite the world.
    sky_azimuth = hdri_sun - math.pi / 2
    mapping.inputs["Rotation"].default_value[2] = sky_azimuth - azimuth
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = sun_data.get("strength", 4.5)
    sun.angle = math.radians(sun_data.get("angle", 1.2))
    sun.color = sun_data.get("colour", (1.0, 0.93, 0.84))
    lamp = bpy.data.objects.new("sun", sun)
    bpy.context.scene.collection.objects.link(lamp)
    direction = Vector((math.cos(elevation) * math.cos(azimuth), math.cos(elevation) * math.sin(azimuth), math.sin(elevation)))
    lamp.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def add_lamps(plan, scale):
    floor = plan["levels"].get("floor", 0.0) * scale
    for index, lamp in enumerate(plan.get("lamps", [])):
        kind = lamp.get("kind", "POINT")
        data = bpy.data.lights.new(f"lamp_{index}", kind)
        data.energy = lamp.get("watts", 25)
        data.color = lamp.get("colour", (1.0, 0.72, 0.46))
        if kind == "POINT":
            data.shadow_soft_size = lamp.get("soft", 0.06)
        created = bpy.data.objects.new(f"lamp_{index}", data)
        bpy.context.scene.collection.objects.link(created)
        created.location = (lamp["at"][0] * scale, lamp["at"][1] * scale, floor + lamp["z"] * scale)


DEFAULT_WINDOW_SKY = 1.0


def add_window_portals(plan, scale):
    """A soft lamp filling each window with the sky's brightness, seen only by what the window lights.

    Sky portals changed nothing here, even flipped (measured on the Holten hall), so rooms depended on stray bounces
    finding a window: 1 pixel in 2 stayed black at 32 samples and the denoiser smeared walls into foil.
    """
    sky_radiance = plan.get("site", {}).get("window_sky", DEFAULT_WINDOW_SKY)
    walls = {wall["id"]: wall for wall in plan["walls"]}
    floor = plan["levels"].get("floor", 0.0) * scale
    created = []
    for opening in plan.get("openings", []):
        if opening.get("kind") != "window":
            continue
        wall = walls[opening["wall"]]
        side = wall.get("outside")
        if not side:
            continue
        start = Vector(wall["a"]) * scale
        end = Vector(wall["b"]) * scale
        direction = (end - start).normalized()
        normal = Vector((-direction.y, direction.x))
        left = opening["from"] if "from" in opening else opening["at"] - opening["width"] / 2
        right = opening["to"] if "to" in opening else opening["at"] + opening["width"] / 2
        middle = start + direction * ((left + right) / 2 * scale)
        sill = opening.get("sill", 0.0) * scale + floor
        head = opening["head"] * scale + floor
        data = bpy.data.lights.new(f"portal_{opening['id']}", "AREA")
        data.shape = "RECTANGLE"
        data.size = (right - left) * scale
        data.size_y = head - sill
        data.energy = sky_radiance * (right - left) * scale * (head - sill) * math.pi
        data.color = (0.95, 0.97, 1.0)
        portal = bpy.data.objects.new(data.name, data)
        bpy.context.scene.collection.objects.link(portal)
        outward = normal * side
        position = middle - outward * (wall["t"] * scale / 2 + 0.03)
        portal.location = (position.x, position.y, (sill + head) / 2)
        inward = Vector((-outward.x, -outward.y, 0))
        portal.rotation_euler = (-inward).to_track_quat("Z", "Y").to_euler()
        portal.visible_camera = False
        # Seen in the panes, these show as white rectangles over the view outside.
        portal.visible_glossy = False
        portal.visible_transmission = False
        created.append(portal)
    return created


def apply_cut(height, plan):
    """Slice everything at a height, cap the wall cuts in dark poché, hide what stands above."""
    section_material = bpy.data.materials.get("wall_section")
    if section_material is None:
        section_material = bpy.data.materials.new("wall_section")
        section_material.use_nodes = True
        section_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
    graph = bpy.context.evaluated_depsgraph_get()
    # Upper storeys' floors go too, or they lie over the rooms the cut is meant to show.
    names = ("walls", "floors", "facade", "frame", "fitted")
    for name in names:
        for item in list(bpy.data.collections[name].objects):
            if item.type != "MESH":
                continue
            evaluated = item.evaluated_get(graph)
            mesh = bpy.data.meshes.new_from_object(evaluated)
            work = bmesh.new()
            work.from_mesh(mesh)
            result = bmesh.ops.bisect_plane(
                work,
                geom=work.verts[:] + work.edges[:] + work.faces[:],
                plane_co=(0, 0, height),
                plane_no=(0, 0, 1),
                clear_outer=True,
            )
            if name == "walls":
                cut_edges = [element for element in result["geom_cut"] if isinstance(element, bmesh.types.BMEdge)]
                filled = bmesh.ops.holes_fill(work, edges=cut_edges, sides=64)
                if section_material.name not in [slot.name for slot in mesh.materials if slot]:
                    mesh.materials.append(section_material)
                index = len(mesh.materials) - 1
                for face in filled["faces"]:
                    face.material_index = index
            work.to_mesh(mesh)
            work.free()
            item.modifiers.clear()
            item.data = mesh
    for name in ("roof", "ceilings"):
        bpy.data.collections[name].hide_render = True
    for item in bpy.data.collections["furnish"].objects:
        if item.location.z > height:
            item.hide_render = True
    for item in bpy.data.objects:
        if item.type == "LIGHT" and item.name.startswith("lamp_"):
            item.hide_render = True


def camera_for(shot, scale, name="camera"):
    data = bpy.data.cameras.new(name)
    data.lens = shot.get("lens", 28)
    data.sensor_width = 36
    data.clip_start = 0.05
    data.clip_end = 900
    created = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(created)
    aim_camera(created, shot, scale)
    bpy.context.scene.camera = created
    return created


def aim_camera(camera, shot, scale):
    """Point a camera; with level on, verticals stay vertical and the view height comes from lens shift."""
    position = Vector(shot["pos"]) * scale
    target = Vector(shot["look"]) * scale
    camera.location = position
    view = target - position
    data = camera.data
    if shot.get("level", True):
        flat = Vector((view.x, view.y, 0))
        distance = flat.length
        aspect = 16 / 9
        data.shift_y = (view.z / distance) * data.lens / data.sensor_width * aspect / aspect
        view = flat
    else:
        data.shift_y = 0
    camera.rotation_euler = view.to_track_quat("-Z", "Y").to_euler()


def meter_pixels():
    """A small, fast, linear render of the current view."""
    import numpy

    scene = bpy.context.scene
    settings = scene.render.image_settings
    saved = (scene.render.resolution_percentage, scene.cycles.samples, scene.cycles.use_denoising, settings.file_format, settings.color_mode, settings.color_depth, scene.render.filepath)
    scene.render.resolution_percentage = 12
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    settings.file_format = "OPEN_EXR"
    settings.color_mode = "RGB"
    settings.color_depth = "32"
    meter_path = pathlib.Path(tempfile.gettempdir()) / f"house_meter_{os.getpid()}.exr"
    scene.render.filepath = str(meter_path)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(meter_path))
    width, height = image.size
    pixels = numpy.empty(width * height * image.channels, dtype=numpy.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, image.channels)
    bpy.data.images.remove(image)
    meter_path.unlink(missing_ok=True)
    scene.render.resolution_percentage, scene.cycles.samples, scene.cycles.use_denoising, settings.file_format, settings.color_mode, settings.color_depth, scene.render.filepath = saved
    return pixels


def meter_exposure(target):
    """Stops that bring the median of the view to a target level, the way a camera meters a room."""
    import numpy

    pixels = meter_pixels()
    luminance = pixels[:, :, 0] * 0.2126 + pixels[:, :, 1] * 0.7152 + pixels[:, :, 2] * 0.0722
    median = max(float(numpy.median(luminance)), 1e-4)
    stops = max(-3.0, min(8.0, math.log2(target / median)))
    print(f"metered median {median:.4f}, {stops:+.2f} stops", flush=True)
    return stops


def render_to(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("rendered", path, flush=True)


def catmull(points, fraction):
    count = len(points)
    position = fraction * (count - 1)
    index = min(int(position), count - 2)
    local = position - index
    p0 = points[max(0, index - 1)]
    p1 = points[index]
    p2 = points[index + 1]
    p3 = points[min(count - 1, index + 2)]
    return 0.5 * ((2 * p1) + (p2 - p0) * local + (2 * p0 - 5 * p1 + 4 * p2 - p3) * local ** 2 + (3 * p1 - p0 - 3 * p2 + p3) * local ** 3)


def eased(fraction):
    return fraction * fraction * (3 - 2 * fraction)


SHEET_MAX_PIXELS = 6000


def plan_sheet_corners(plan, scale):
    """World corners of the source sheet, from the same pixel-to-plan pairs the overlay check uses."""
    import numpy

    pairs = plan["calibration"]["pairs"]
    plan_points = numpy.array([[pair["plan"][0], pair["plan"][1], 1.0] for pair in pairs])
    pixel_points = numpy.array([pair["px"] for pair in pairs], dtype=float)
    to_pixels, _, _, _ = numpy.linalg.lstsq(plan_points, pixel_points, rcond=None)
    linear = to_pixels[:2, :2].T
    offset = to_pixels[2, :2]
    inverse = numpy.linalg.inv(linear)
    source = pathlib.Path(options_plan_folder) / plan["source"]["image"]
    image = bpy.data.images.load(str(source), check_existing=True)
    width, height = image.size
    if max(width, height) > SHEET_MAX_PIXELS:
        shrink = SHEET_MAX_PIXELS / max(width, height)
        image.scale(int(width * shrink), int(height * shrink))
    # The fit above is in the original pixels, so corners stay computed from the original size.
    # Image rows run down, UV rows run up.
    corners = []
    for pixel, uv in (((0, height), (0, 0)), ((width, height), (1, 0)), ((width, 0), (1, 1)), ((0, 0), (0, 1))):
        planned = inverse @ (numpy.array(pixel, dtype=float) - offset)
        corners.append((Vector((planned[0] * scale, planned[1] * scale, 0.0)), uv))
    return image, corners


def add_plan_sheet(plan, scale, shift=(0.0, 0.0)):
    """The drawing itself lying on a clean floor, lined up with the walls that will rise from it."""
    image, corners = plan_sheet_corners(plan, scale)
    floor_level = plan["levels"].get("floor", 0.0) * scale + 0.004
    shifted = [(corner + Vector((shift[0], shift[1], floor_level)), uv) for corner, uv in corners]
    mesh = bpy.data.meshes.new("plan_sheet")
    mesh.from_pydata([tuple(corner) for corner, _ in shifted], [], [(0, 1, 2, 3)])
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for index, (_, uv) in enumerate(shifted):
        uv_layer.data[index].uv = uv
    material = bpy.data.materials.new("plan_paper")
    material.use_nodes = True
    tree = material.node_tree
    surface = tree.nodes["Principled BSDF"]
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    tree.links.new(texture.outputs["Color"], surface.inputs["Base Color"])
    surface.inputs["Roughness"].default_value = 0.85
    surface.inputs["Specular IOR Level"].default_value = 0.2
    mesh.materials.append(material)
    sheet = bpy.data.objects.new("plan_sheet", mesh)
    bpy.context.scene.collection.objects.link(sheet)
    table_mesh = bpy.data.meshes.new("studio_floor")
    size = 500.0
    # Below the plinth, so concrete slabs and porches do not melt into a pale floor at the same height.
    table_level = plan.get("site", {}).get("ground_level", -1.0) * scale
    table_mesh.from_pydata([(-size, -size, table_level), (size, -size, table_level), (size, size, table_level), (-size, size, table_level)], [], [(0, 1, 2, 3)])
    table_material = bpy.data.materials.new("studio_white")
    table_material.use_nodes = True
    table_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.82, 0.81, 0.79, 1)
    table_material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    table_mesh.materials.append(table_material)
    table = bpy.data.objects.new("studio_floor", table_mesh)
    bpy.context.scene.collection.objects.link(table)


FLOOR_FADE_METRES = (35.0, 120.0)
FLOOR_PROBE_POSITION = (150.0, 150.0, 12.0)


def measure_floor_colour(camera):
    """The colour the studio floor renders to, read straight down at an empty patch of it."""
    import numpy

    saved_location = camera.location.copy()
    saved_rotation = camera.rotation_euler.copy()
    camera.location = FLOOR_PROBE_POSITION
    camera.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    pixels = meter_pixels()
    camera.location = saved_location
    camera.rotation_euler = saved_rotation
    colour = [float(numpy.median(pixels[:, :, channel])) for channel in range(3)]
    print("studio floor colour", colour, flush=True)
    return colour


def camera_only_colour(tree, shader_output, surface_input, colour, fade_output=None):
    """Replace what the camera sees with a flat colour, keeping the same light for everything else."""
    is_camera = tree.nodes.new("ShaderNodeLightPath")
    mix = tree.nodes.new("ShaderNodeMixShader")
    flat = tree.nodes.new("ShaderNodeEmission")
    flat.inputs["Color"].default_value = (*colour, 1.0)
    if fade_output is None:
        tree.links.new(is_camera.outputs["Is Camera Ray"], mix.inputs[0])
    else:
        both = tree.nodes.new("ShaderNodeMath")
        both.operation = "MULTIPLY"
        tree.links.new(is_camera.outputs["Is Camera Ray"], both.inputs[0])
        tree.links.new(fade_output, both.inputs[1])
        tree.links.new(both.outputs[0], mix.inputs[0])
    tree.links.new(shader_output, mix.inputs[1])
    tree.links.new(flat.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], surface_input)


def melt_studio_horizon(colour):
    """No horizon in the build-up: the floor fades into a background of its own colour, so no sky strip cuts the frame."""
    floor_tree = bpy.data.materials["studio_white"].node_tree
    geometry = floor_tree.nodes.new("ShaderNodeNewGeometry")
    distance = floor_tree.nodes.new("ShaderNodeVectorMath")
    distance.operation = "LENGTH"
    floor_tree.links.new(geometry.outputs["Position"], distance.inputs[0])
    fade = floor_tree.nodes.new("ShaderNodeMapRange")
    fade.interpolation_type = "SMOOTHSTEP"
    fade.inputs["From Min"].default_value = FLOOR_FADE_METRES[0]
    fade.inputs["From Max"].default_value = FLOOR_FADE_METRES[1]
    floor_tree.links.new(distance.outputs["Value"], fade.inputs["Value"])
    floor_output = floor_tree.nodes["Material Output"]
    floor_surface = floor_tree.nodes["Principled BSDF"]
    camera_only_colour(floor_tree, floor_surface.outputs[0], floor_output.inputs["Surface"], colour, fade.outputs[0])
    world_tree = bpy.context.scene.world.node_tree
    world_output = world_tree.nodes["World Output"]
    world_background = world_tree.nodes["Background"]
    camera_only_colour(world_tree, world_background.outputs[0], world_output.inputs["Surface"], colour)


def smooth_window(value, start, end):
    fraction = max(0.0, min(1.0, (value - start) / max(end - start, 1e-5)))
    return fraction * fraction * (3 - 2 * fraction)


TRACE_WIDTH_METRES = 0.14


def set_hidden(item, hidden):
    # Writing these unchanged still tags the depsgraph, and Cycles then rebuilds the scene for the frame.
    if item.hide_render != hidden:
        item.hide_render = hidden


def set_scale_z(item, value):
    if abs(item.scale.z - value) > 1e-5:
        item.scale.z = value


def set_location_z(item, value):
    if abs(item.location.z - value) > 1e-5:
        item.location.z = value


RISING_ORDER = ("walls", "facade", "frame", "fitted")
ROOF_DROP_METRES = 4.0
DEFAULT_STAGES = {"trace": [0.06, 0.24], "walls": [0.24, 0.46], "sheet": [0.46, 0.56], "furnish": [0.56, 0.76], "roof": [0.78, 0.92]}


def add_trace_line(wall, scale, height, material):
    """A glowing strip along one wall's centreline, grown from its start by scaling along x."""
    start = Vector(wall["a"]) * scale
    end = Vector(wall["b"]) * scale
    length = (end - start).length
    half_width = TRACE_WIDTH_METRES / 2
    mesh = bpy.data.meshes.new(f"trace_{wall['id']}")
    mesh.from_pydata([(0, -half_width, 0), (length, -half_width, 0), (length, half_width, 0), (0, half_width, 0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    line = bpy.data.objects.new(mesh.name, mesh)
    line.location = (start.x, start.y, height)
    line.rotation_euler = (0, 0, math.atan2(end.y - start.y, end.x - start.x))
    bpy.context.scene.collection.objects.link(line)
    return line


class BuildUp:
    """Lines trace over the drawing, walls grow off them, the paper fades to floor, furniture arrives, the roof lands."""

    def __init__(self, plan, scale, stages):
        self.stages = {**DEFAULT_STAGES, **stages}
        floor = plan["levels"].get("floor", 0.0) * scale
        bpy.context.view_layer.layer_collection.children["site"].exclude = True
        self.rising = []
        for order, name in enumerate(RISING_ORDER):
            members = [item for item in bpy.data.collections[name].all_objects if item.name != "fabric"]
            for index, item in enumerate(members):
                self.rising.append((item, (order + index / max(1, len(members))) / len(RISING_ORDER)))
        self.floors = list(bpy.data.collections["floors"].all_objects)
        self.roof = [(item, item.location.z) for item in bpy.data.collections["roof"].all_objects]
        self.ceilings = list(bpy.data.collections["ceilings"].all_objects)
        self.furnish = list(bpy.data.collections["furnish"].all_objects)
        # Rugs and curtains share one mesh and arrive with the furniture, not with the walls.
        self.fabric = bpy.data.objects.get("fabric")
        self.furnish_scale = {item.name: item.scale.copy() for item in self.furnish}
        self.sheet_surface = bpy.data.materials["plan_paper"].node_tree.nodes["Principled BSDF"]
        self.sheet = bpy.data.objects["plan_sheet"]
        trace_material = bpy.data.materials.new("trace_glow")
        trace_material.use_nodes = True
        surface = trace_material.node_tree.nodes["Principled BSDF"]
        surface.inputs["Base Color"].default_value = (1.0, 0.14, 0.01, 1)
        surface.inputs["Emission Color"].default_value = (1.0, 0.14, 0.01, 1)
        surface.inputs["Emission Strength"].default_value = 2.4
        ground_floor_walls = [wall for wall in plan["walls"] if wall.get("level", 1) == 1 and not wall.get("dashed")]
        self.traces = [add_trace_line(wall, scale, floor + 0.012, trace_material) for wall in ground_floor_walls]

    def apply_trace(self, value):
        start, end = self.stages["trace"]
        walls_start, walls_end = self.stages["walls"]
        count = len(self.traces)
        for index, line in enumerate(self.traces):
            line_start = start + (end - start) * 0.7 * index / max(1, count - 1)
            growth = smooth_window(value, line_start, line_start + (end - start) * 0.3)
            if abs(line.scale.x - max(growth, 0.001)) > 1e-5:
                line.scale.x = max(growth, 0.001)
            set_hidden(line, growth <= 0.001 or value > walls_start + (walls_end - walls_start) * 0.5)

    def apply_walls(self, value):
        start, end = self.stages["walls"]
        local = (value - start) / max(end - start, 1e-5)
        stagger = 0.35
        for item, delay in self.rising:
            growth = smooth_window(local, delay * stagger, delay * stagger + (1 - stagger))
            set_hidden(item, growth <= 0.001)
            set_scale_z(item, max(growth, 0.001))

    def apply_sheet(self, value):
        start, end = self.stages["sheet"]
        opacity = 1.0 - smooth_window(value, start, end)
        if abs(self.sheet_surface.inputs["Alpha"].default_value - opacity) > 1e-5:
            self.sheet_surface.inputs["Alpha"].default_value = opacity
        set_hidden(self.sheet, opacity <= 0.001)
        for item in self.floors:
            set_hidden(item, value < start)

    def apply_furnish(self, value):
        start, end = self.stages["furnish"]
        count = max(1, len(self.furnish) - 1)
        if self.fabric is not None:
            set_hidden(self.fabric, value < start)
        for index, item in enumerate(self.furnish):
            item_start = start + (end - start) * 0.7 * index / count
            growth = smooth_window(value, item_start, item_start + (end - start) * 0.3)
            set_hidden(item, growth <= 0.001)
            wanted = self.furnish_scale[item.name] * max(growth, 0.001)
            if (item.scale - wanted).length > 1e-5:
                item.scale = wanted

    def apply_roof(self, value):
        start, end = self.stages["roof"]
        drop = 1.0 - smooth_window(value, start, end)
        for item, resting_height in self.roof:
            set_hidden(item, value < start)
            set_location_z(item, resting_height + drop * drop * ROOF_DROP_METRES)
        for item in self.ceilings:
            set_hidden(item, value < end)

    def apply(self, value):
        self.apply_trace(value)
        self.apply_walls(value)
        self.apply_sheet(value)
        self.apply_furnish(value)
        self.apply_roof(value)


def render_film(plan, film, scale, out_folder, frame_limit):
    frames = int(frame_limit or film["frames"])
    folder = out_folder / film["name"]
    folder.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.cycles.use_animated_seed = False
    bpy.context.scene.render.use_persistent_data = True
    positions = [Vector(point["pos"]) for point in film["path"]]
    targets = [Vector(point["look"]) for point in film["path"]]
    shot = {"pos": film["path"][0]["pos"], "look": film["path"][0]["look"], "lens": film.get("lens", 24), "level": film.get("level", True)}
    camera = camera_for(shot, scale)
    stops_at_points = None
    if film.get("interior"):
        stops_at_points = []
        for point in film["path"]:
            aim_camera(camera, {"pos": point["pos"], "look": point["look"], "level": film.get("level", True)}, scale)
            bpy.context.view_layer.update()
            stops_at_points.append(meter_exposure(film.get("meter_target", INTERIOR_METER_TARGET)) + film.get("exposure", 0.0))
    build_up = None
    if film.get("build_up") is not None:
        add_plan_sheet(plan, scale)
        build_up = BuildUp(plan, scale, film["build_up"])
        melt_studio_horizon(measure_floor_colour(camera))
    for frame in range(frames):
        target_path = folder / f"f{frame:04d}.png"
        if target_path.exists():
            continue
        if build_up is not None:
            build_up.apply(frame / max(1, frames - 1))
        fraction = eased(frame / max(1, frames - 1))
        now = {"pos": list(catmull(positions, fraction)), "look": list(catmull(targets, fraction)), "level": film.get("level", True)}
        aim_camera(camera, now, scale)
        bpy.context.view_layer.update()
        if stops_at_points:
            place = fraction * (len(stops_at_points) - 1)
            index = min(int(place), len(stops_at_points) - 2)
            local = place - index
            bpy.context.scene.view_settings.exposure = stops_at_points[index] * (1 - local) + stops_at_points[index + 1] * local
        render_to(target_path)


def main():
    options = read_arguments()
    plan_path = pathlib.Path(options["plan"])
    global options_plan_folder
    options_plan_folder = str(plan_path.resolve().parent)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    scale = METRES_PER_UNIT[plan.get("units", "m")]
    out_folder = pathlib.Path(options["out"])
    out_folder.mkdir(parents=True, exist_ok=True)
    setup_cycles(int(options["samples"]), int(options["scale"]))
    site = plan.get("site", {})
    setup_world(site)
    add_lamps(plan, scale)
    portals = add_window_portals(plan, scale)
    wanted = options["shots"].split(",") if options["shots"] else None
    cut_applied = None
    if options["film"]:
        film = next(item for item in plan["films"] if item["name"] == options["film"])
        if film.get("cut"):
            apply_cut(plan["levels"].get("floor", 0.0) * scale + film["cut"] * scale, plan)
        for portal in portals:
            portal.hide_render = not film.get("interior", False)
        bpy.context.scene.view_settings.exposure = film.get("exposure", 0.0)
        render_film(plan, film, scale, out_folder, options["frames"])
        return
    shots = plan.get("shots", [])
    # Cuts only remove, so uncut shots go first and then the highest cut down.
    shots = sorted(shots, key=lambda shot: -shot["cut"] if shot.get("cut") else float("-inf"))
    for shot in shots:
        if wanted and shot["name"] not in wanted:
            continue
        kind = shot.get("kind", "exterior")
        for portal in portals:
            # Outside too: a dark room behind the glass or an open door reads as a black hole in the wall.
            portal.hide_render = False
        if shot.get("cut") and shot["cut"] != cut_applied:
            apply_cut(plan["levels"].get("floor", 0.0) * scale + shot["cut"] * scale, plan)
            cut_applied = shot["cut"]
        camera_for(shot, scale, shot["name"])
        bpy.context.view_layer.update()
        bpy.context.scene.view_settings.exposure = 0.0
        stops = shot.get("exposure", 0.0)
        if shot.get("meter", kind == "interior"):
            stops += meter_exposure(shot.get("meter_target", INTERIOR_METER_TARGET))
        bpy.context.scene.view_settings.exposure = stops
        render_to(out_folder / f"{shot['name']}.png")


main()
