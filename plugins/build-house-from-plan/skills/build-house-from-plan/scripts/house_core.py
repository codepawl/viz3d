"""Materials and mesh batching for build_house.py. Runs inside Blender."""

import os
import pathlib
import random

import bmesh
import bpy
from mathutils import Vector

RESOLUTION_SUFFIX = "2k"
LIBRARY = pathlib.Path(os.environ.get("HOUSE_ASSET_LIBRARY", pathlib.Path.home() / "house-assets"))

# name: (Poly Haven or ambientCG folder, metres per tile, tint, desaturate, bump strength, roughness scale)
TEXTURED_MATERIALS = {
    "siding_white": ("distressed_painted_planks", 1.6, (1.45, 1.42, 1.34), 1.0, 0.25, 0.9),
    "board_redwood": ("oak_wood_planks", 2.0, (0.62, 0.47, 0.35), 0.65, 0.6, 1.0),
    "grass_path": ("grass_path_2", 3.0, (0.8, 0.76, 0.7), 0.0, 1.0, 1.0),
    "shingle_wood": ("weathered_planks", 2.0, (0.62, 0.60, 0.56), 0.75, 0.8, 1.0),
    "roll_roofing": ("roof_3", 2.0, (0.50, 0.50, 0.50), 0.5, 0.8, 1.0),
    "oak_floor": ("plank_flooring_04", 2.0, (0.95, 0.88, 0.80), 0.0, 0.3, 0.75),
    "old_floor": ("old_wood_floor", 2.5, (0.88, 0.78, 0.68), 0.0, 0.45, 0.85),
    "concrete_floor": ("concrete_floor_painted", 2.0, (0.75, 0.74, 0.72), 0.3, 0.3, 0.8),
    "wallboard": ("plastered_wall", 8.0, (0.86, 0.84, 0.78), 0.9, 0.01, 1.0),
    "plaster_old": ("plastered_wall_03", 8.0, (0.83, 0.80, 0.72), 0.9, 0.03, 1.0),
    "cabin_boards": ("raw_plank_wall", 2.0, (0.72, 0.62, 0.50), 0.4, 0.8, 1.0),
    "pine_boards": ("raw_plank_wall", 2.0, (0.92, 0.72, 0.52), 0.1, 0.4, 0.85),
    "dark_timber": ("dark_wooden_planks", 2.0, (0.55, 0.42, 0.32), 0.1, 0.5, 0.9),
    "tile_white": ("square_tiles", 1.2, (0.92, 0.92, 0.90), 1.0, 0.5, 0.5),
    "brick_painted": ("painted_worn_brick", 1.8, (0.88, 0.86, 0.82), 0.6, 0.8, 1.0),
    "brick_red": ("red_brick", 2.0, (0.75, 0.70, 0.66), 0.1, 0.8, 1.0),
    "brick_dark": ("red_brick", 2.0, (0.30, 0.25, 0.22), 0.3, 0.8, 1.0),
    "shingle_asphalt": ("roof_3", 1.6, (0.34, 0.34, 0.35), 0.8, 0.8, 1.6),
    "stucco_cream": ("painted_plaster_wall", 1.2, (0.88, 0.82, 0.70), 0.7, 0.9, 1.0),
    "boards_painted": ("distressed_painted_planks", 1.6, (0.88, 0.86, 0.78), 1.0, 0.2, 0.9),
    "stone_rubble": ("rustic_stone_wall_02", 2.0, (0.72, 0.70, 0.66), 0.3, 1.0, 1.0),
    "grass_ground": ("Grass004", 2.5, (0.50, 0.52, 0.36), 0.0, 0.6, 1.0),
    "road_asphalt": ("asphalt_02", 4.0, (0.62, 0.61, 0.6), 0.0, 1.0, 1.0),
    "pavement_concrete": ("concrete_floor_worn_001", 3.0, (0.8, 0.78, 0.74), 0.0, 0.9, 1.0),
    "gravel_path": ("gravel_ground_01", 2.0, (0.72, 0.68, 0.62), 0.0, 1.0, 1.0),
    "fabric_linen": ("hessian_230", 0.1, (1.0, 0.97, 0.90), 0.9, 0.12, 1.0),
    "fabric_rug": ("dirty_carpet", 1.0, (1.5, 1.15, 0.9), 0.2, 0.7, 1.0),
}

# name: (base colour, roughness, metallic)
PLAIN_MATERIALS = {
    "trim_white": ((0.78, 0.76, 0.71), 0.42, 0.0),
    "curtain_plain": ((0.70, 0.66, 0.56), 0.92, 0.0),
    "ceiling_paint": ((0.76, 0.74, 0.68), 0.75, 0.0),
    "wall_paint": ((0.74, 0.71, 0.63), 0.62, 0.0),
    "wall_paint_old": ((0.72, 0.67, 0.56), 0.7, 0.0),
    "chair_green": ((0.035, 0.07, 0.05), 0.42, 0.0),
    "trim_cream": ((0.70, 0.66, 0.56), 0.48, 0.0),
    "shutter_black": ((0.012, 0.014, 0.015), 0.42, 0.0),
    "door_green": ((0.03, 0.075, 0.055), 0.38, 0.0),
    "cabinet_birch": ((0.56, 0.40, 0.24), 0.40, 0.0),
    "counter_laminate": ((0.60, 0.58, 0.53), 0.30, 0.0),
    "porcelain": ((0.80, 0.80, 0.78), 0.12, 0.0),
    "chrome": ((0.78, 0.78, 0.78), 0.12, 1.0),
    "brass": ((0.62, 0.44, 0.18), 0.32, 1.0),
    "iron_black": ((0.02, 0.02, 0.02), 0.55, 0.9),
    "aluminium_dull": ((0.48, 0.48, 0.47), 0.48, 1.0),
    "wall_section": ((0.018, 0.018, 0.02), 0.8, 0.0),
    "lamp_shade": ((0.75, 0.70, 0.58), 0.6, 0.0),
    "bedding": ((0.62, 0.60, 0.55), 0.85, 0.0),
    "towel": ((0.42, 0.50, 0.50), 0.95, 0.0),
    "soot": ((0.008, 0.007, 0.007), 0.95, 0.0),
    "putty": ((0.40, 0.38, 0.34), 0.7, 0.0),
}


def find_texture(folder, kinds):
    """First file in a texture folder whose name carries one of the map kinds."""
    root = LIBRARY / "textures" / folder
    if not root.exists():
        return None
    candidates = [path for path in root.rglob("*") if path.suffix.lower() in (".jpg", ".png", ".exr")]
    for kind in kinds:
        for path in candidates:
            if kind in path.stem.lower():
                return path
    return None


def add_image_node(tree, path, colour):
    node = tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(str(path), check_existing=True)
    node.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return node


def make_textured_material(name):
    folder, tile_metres, tint, desaturate, bump_strength, roughness_scale = TEXTURED_MATERIALS[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    shader = tree.nodes["Principled BSDF"]
    coordinates = tree.nodes.new("ShaderNodeUVMap")
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / tile_metres, 1 / tile_metres, 1)
    tree.links.new(coordinates.outputs["UV"], mapping.inputs["Vector"])

    diffuse_path = find_texture(folder, ("_diff", "color"))
    if diffuse_path is None:
        print("MISSING TEXTURE", folder)
        shader.inputs["Base Color"].default_value = (*tint, 1)
        return material
    diffuse = add_image_node(tree, diffuse_path, True)
    tree.links.new(mapping.outputs["Vector"], diffuse.inputs["Vector"])

    saturation = tree.nodes.new("ShaderNodeHueSaturation")
    saturation.inputs["Saturation"].default_value = 1 - desaturate
    tree.links.new(diffuse.outputs["Color"], saturation.inputs["Color"])

    tint_node = tree.nodes.new("ShaderNodeMix")
    tint_node.data_type = "RGBA"
    tint_node.blend_type = "MULTIPLY"
    tint_node.inputs["Factor"].default_value = 1.0
    tint_node.inputs["B"].default_value = (*tint, 1)
    tree.links.new(saturation.outputs["Color"], tint_node.inputs["A"])

    # Large soft patches plus per-piece variation keep repeats from showing.
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    noise.inputs["Detail"].default_value = 5
    tree.links.new(coordinates.outputs["UV"], noise.inputs["Vector"])
    ramp = tree.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.3
    ramp.inputs["From Max"].default_value = 0.7
    ramp.inputs["To Min"].default_value = 0.86
    ramp.inputs["To Max"].default_value = 1.08
    tree.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    patches = tree.nodes.new("ShaderNodeVectorMath")
    patches.operation = "SCALE"
    tree.links.new(tint_node.outputs["Result"], patches.inputs[0])
    tree.links.new(ramp.outputs["Result"], patches.inputs["Scale"])

    variation = tree.nodes.new("ShaderNodeVertexColor")
    variation.layer_name = "variation"
    piece = tree.nodes.new("ShaderNodeVectorMath")
    piece.operation = "MULTIPLY"
    tree.links.new(patches.outputs["Vector"], piece.inputs[0])
    tree.links.new(variation.outputs["Color"], piece.inputs[1])
    tree.links.new(piece.outputs["Vector"], shader.inputs["Base Color"])

    rough_path = find_texture(folder, ("_rough", "roughness"))
    arm_path = find_texture(folder, ("_arm",))
    roughness_scale_node = tree.nodes.new("ShaderNodeMath")
    roughness_scale_node.operation = "MULTIPLY"
    roughness_scale_node.inputs[1].default_value = roughness_scale
    if rough_path is not None:
        rough = add_image_node(tree, rough_path, False)
        tree.links.new(mapping.outputs["Vector"], rough.inputs["Vector"])
        tree.links.new(rough.outputs["Color"], roughness_scale_node.inputs[0])
        tree.links.new(roughness_scale_node.outputs["Value"], shader.inputs["Roughness"])
    elif arm_path is not None:
        arm = add_image_node(tree, arm_path, False)
        tree.links.new(mapping.outputs["Vector"], arm.inputs["Vector"])
        split = tree.nodes.new("ShaderNodeSeparateColor")
        tree.links.new(arm.outputs["Color"], split.inputs["Color"])
        tree.links.new(split.outputs["Green"], roughness_scale_node.inputs[0])
        tree.links.new(roughness_scale_node.outputs["Value"], shader.inputs["Roughness"])

    normal_path = find_texture(folder, ("_nor_gl", "normalgl", "_nor"))
    if normal_path is not None:
        normal_image = add_image_node(tree, normal_path, False)
        tree.links.new(mapping.outputs["Vector"], normal_image.inputs["Vector"])
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = bump_strength
        tree.links.new(normal_image.outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_plain_material(name):
    colour, roughness, metallic = PLAIN_MATERIALS[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    shader = tree.nodes["Principled BSDF"]
    shader.inputs["Metallic"].default_value = metallic
    coordinates = tree.nodes.new("ShaderNodeTexCoord")
    # Scanned plaster reads as grey concrete from inside a room, so a painted wall is a colour that drifts a little.
    tone = tree.nodes.new("ShaderNodeTexNoise")
    tone.inputs["Scale"].default_value = 1.2
    tone.inputs["Detail"].default_value = 4
    tree.links.new(coordinates.outputs["Object"], tone.inputs["Vector"])
    tone_range = tree.nodes.new("ShaderNodeMapRange")
    tone_range.inputs["From Min"].default_value = 0.3
    tone_range.inputs["From Max"].default_value = 0.7
    tone_range.inputs["To Min"].default_value = 0.95
    tone_range.inputs["To Max"].default_value = 1.03
    tree.links.new(tone.outputs["Fac"], tone_range.inputs["Value"])
    tinted = tree.nodes.new("ShaderNodeVectorMath")
    tinted.operation = "SCALE"
    tinted.inputs[0].default_value = colour
    tree.links.new(tone_range.outputs["Result"], tinted.inputs["Scale"])
    tree.links.new(tinted.outputs["Vector"], shader.inputs["Base Color"])
    # Paint is never perfect: wide roughness drift and a fine orange peel.
    drift = tree.nodes.new("ShaderNodeTexNoise")
    drift.inputs["Scale"].default_value = 3.0
    drift.inputs["Detail"].default_value = 6
    tree.links.new(coordinates.outputs["Object"], drift.inputs["Vector"])
    ramp = tree.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.3
    ramp.inputs["From Max"].default_value = 0.7
    ramp.inputs["To Min"].default_value = roughness * 0.8
    ramp.inputs["To Max"].default_value = min(1.0, roughness * 1.25)
    tree.links.new(drift.outputs["Fac"], ramp.inputs["Value"])
    tree.links.new(ramp.outputs["Result"], shader.inputs["Roughness"])
    peel = tree.nodes.new("ShaderNodeTexNoise")
    peel.inputs["Scale"].default_value = 500.0
    peel.inputs["Detail"].default_value = 3
    tree.links.new(coordinates.outputs["Object"], peel.inputs["Vector"])
    bump = tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.03
    bump.inputs["Distance"].default_value = 0.002
    tree.links.new(peel.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_glass_material():
    material = bpy.data.materials.new("glass")
    material.use_nodes = True
    tree = material.node_tree
    output = tree.nodes["Material Output"]
    shader = tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.96, 0.98, 0.97, 1)
    shader.inputs["Roughness"].default_value = 0.0
    shader.inputs["IOR"].default_value = 1.5
    shader.inputs["Transmission Weight"].default_value = 1.0
    # Only the camera sees real glass. With caustics off, a bounce that crosses refractive glass is dropped,
    # which cost the rooms 10 times their daylight (measured on the cottage living room).
    path = tree.nodes.new("ShaderNodeLightPath")
    transparent = tree.nodes.new("ShaderNodeBsdfTransparent")
    transparent.inputs["Color"].default_value = (0.92, 0.93, 0.92, 1)
    mix = tree.nodes.new("ShaderNodeMixShader")
    tree.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    tree.links.new(transparent.outputs["BSDF"], mix.inputs[1])
    tree.links.new(shader.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], output.inputs["Surface"])
    return material


def make_lamp_material(strength):
    material = bpy.data.materials.new(f"lamp_{strength}")
    material.use_nodes = True
    tree = material.node_tree
    shader = tree.nodes["Principled BSDF"]
    shader.inputs["Emission Color"].default_value = (1.0, 0.78, 0.55, 1)
    shader.inputs["Emission Strength"].default_value = strength
    return material


_material_cache = {}


def get_material(name):
    if name in _material_cache:
        return _material_cache[name]
    if name in TEXTURED_MATERIALS:
        material = make_textured_material(name)
    elif name in PLAIN_MATERIALS:
        material = make_plain_material(name)
    elif name == "glass":
        material = make_glass_material()
    elif name.startswith("lamp_"):
        material = make_lamp_material(float(name.split("_")[1]))
    else:
        raise KeyError(f"unknown material {name}")
    _material_cache[name] = material
    return material


class MeshBatch:
    """Collects quads and boxes per material and turns them into one Blender object."""

    def __init__(self, name, seed=1):
        self.name = name
        self.vertices = []
        self.faces = []
        self.face_uvs = []
        self.face_materials = []
        self.face_variation = []
        self.material_names = []
        self.random = random.Random(seed)
        self.uv_offset = (0.0, 0.0)
        self.variation = 1.0

    def material_index(self, material_name):
        if material_name not in self.material_names:
            self.material_names.append(material_name)
        return self.material_names.index(material_name)

    def add_face(self, points, material_name, uvs=None, indices=None):
        if indices is None:
            start = len(self.vertices)
            self.vertices.extend(Vector(point) for point in points)
            indices = list(range(start, start + len(points)))
        if uvs is None:
            uvs = world_uvs(points)
        self.faces.append(indices)
        self.face_uvs.append([(uv[0] + self.uv_offset[0], uv[1] + self.uv_offset[1]) for uv in uvs])
        self.face_materials.append(self.material_index(material_name))
        self.face_variation.append(self.variation)

    def add_box(self, origin, axis_x, axis_y, axis_z, material_name, skip=()):
        """Box with one corner at origin and edges along the three axis vectors, sharing vertices so bevels work."""
        origin = Vector(origin)
        axis_x = Vector(axis_x)
        axis_y = Vector(axis_y)
        axis_z = Vector(axis_z)
        start = len(self.vertices)
        corners = [
            origin,
            origin + axis_x,
            origin + axis_x + axis_y,
            origin + axis_y,
            origin + axis_z,
            origin + axis_x + axis_z,
            origin + axis_x + axis_y + axis_z,
            origin + axis_y + axis_z,
        ]
        self.vertices.extend(corners)
        sides = {
            "bottom": (0, 3, 2, 1),
            "top": (4, 5, 6, 7),
            "front": (0, 1, 5, 4),
            "right": (1, 2, 6, 5),
            "back": (2, 3, 7, 6),
            "left": (3, 0, 4, 7),
        }
        # Grain follows the longest edge of each face.
        for side_name, side in sides.items():
            if side_name in skip:
                continue
            points = [corners[index] for index in side]
            self.add_face(points, material_name, uvs=long_edge_uvs(points), indices=[start + index for index in side])

    def add_prism(self, outline, z_bottom, z_top, material_name, material_top=None):
        """Vertical extrusion of a closed outline given as (x, y) points counter-clockwise."""
        start = len(self.vertices)
        count = len(outline)
        for point in outline:
            self.vertices.append(Vector((point[0], point[1], z_bottom)))
        for point in outline:
            self.vertices.append(Vector((point[0], point[1], z_top)))
        top_points = [Vector((point[0], point[1], z_top)) for point in outline]
        self.add_face(top_points, material_top or material_name, uvs=[(point[0], point[1]) for point in outline], indices=[start + count + index for index in range(count)])
        bottom_points = [Vector((point[0], point[1], z_bottom)) for point in reversed(outline)]
        bottom_indices = [start + count - 1 - index for index in range(count)]
        self.add_face(bottom_points, material_name, uvs=[(point[0], point[1]) for point in reversed(outline)], indices=bottom_indices)
        for index in range(count):
            following = (index + 1) % count
            points = [self.vertices[start + index], self.vertices[start + following], self.vertices[start + count + following], self.vertices[start + count + index]]
            self.add_face(points, material_name, indices=[start + index, start + following, start + count + following, start + count + index])

    def add_cylinder(self, base, top, radius, material_name, sides=20, cap=True, radius_top=None):
        base = Vector(base)
        top = Vector(top)
        axis = (top - base).normalized()
        helper = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
        side_x = axis.cross(helper).normalized()
        side_y = axis.cross(side_x).normalized()
        import math

        radius_end = radius if radius_top is None else radius_top
        start = len(self.vertices)
        for index in range(sides):
            angle = 2 * math.pi * index / sides
            radial = side_x * math.cos(angle) + side_y * math.sin(angle)
            self.vertices.append(base + radial * radius)
        for index in range(sides):
            angle = 2 * math.pi * index / sides
            radial = side_x * math.cos(angle) + side_y * math.sin(angle)
            self.vertices.append(top + radial * radius_end)
        for index in range(sides):
            following = (index + 1) % sides
            indices = [start + index, start + following, start + sides + following, start + sides + index]
            uvs = [(index / sides, 0), ((index + 1) / sides, 0), ((index + 1) / sides, 1), (index / sides, 1)]
            self.add_face([self.vertices[i] for i in indices], material_name, uvs=uvs, indices=indices)
        if cap:
            top_indices = [start + sides + index for index in range(sides)]
            self.add_face([self.vertices[i] for i in top_indices], material_name, uvs=[(0, 0)] * sides, indices=top_indices)
            bottom_indices = [start + sides - 1 - index for index in range(sides)]
            self.add_face([self.vertices[i] for i in bottom_indices], material_name, uvs=[(0, 0)] * sides, indices=bottom_indices)

    def finish(self, collection, bevel=0.0, smooth=False, segments=2):
        if not self.faces:
            return None
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata([tuple(vertex) for vertex in self.vertices], [], self.faces)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        variation_layer = mesh.color_attributes.new("variation", "FLOAT_COLOR", "CORNER")
        loop_index = 0
        for polygon_index, polygon in enumerate(mesh.polygons):
            polygon.material_index = self.face_materials[polygon_index]
            uvs = self.face_uvs[polygon_index]
            shade = self.face_variation[polygon_index]
            for corner, loop in enumerate(polygon.loop_indices):
                uv_layer.data[loop].uv = uvs[corner]
                variation_layer.data[loop].color = (shade, shade, shade, 1)
            polygon.use_smooth = smooth or bevel > 0
            loop_index += 1
        for material_name in self.material_names:
            mesh.materials.append(get_material(material_name))
        mesh.validate()
        mesh.update()
        created = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(created)
        if bevel > 0:
            modifier = created.modifiers.new("edge_wear", "BEVEL")
            modifier.width = bevel
            modifier.segments = segments
            modifier.limit_method = "ANGLE"
            modifier.angle_limit = 0.6
            modifier.harden_normals = True
            modifier.miter_outer = "MITER_ARC"
        return created


def world_uvs(points):
    """Metric UVs from the face plane, with the horizontal direction as U on walls."""
    a = Vector(points[0])
    b = Vector(points[1])
    c = Vector(points[-1])
    normal = (b - a).cross(c - a)
    if normal.length < 1e-9:
        return [(point[0], point[1]) for point in points]
    normal.normalize()
    if abs(normal.z) > 0.9:
        return [(point[0], point[1]) for point in points]
    horizontal = Vector((-normal.y, normal.x, 0))
    if horizontal.length < 1e-6:
        horizontal = Vector((1, 0, 0))
    horizontal.normalize()
    upward = normal.cross(horizontal).normalized()
    if upward.z < 0:
        upward = -upward
    return [(Vector(point).dot(horizontal), Vector(point).dot(upward)) for point in points]


def long_edge_uvs(points):
    """Metric UVs with U along the longer edge of a quad."""
    a = Vector(points[0])
    b = Vector(points[1])
    d = Vector(points[-1])
    if (b - a).length >= (d - a).length:
        axis_u = (b - a).normalized()
    else:
        axis_u = (d - a).normalized()
    normal = (b - a).cross(d - a)
    if normal.length < 1e-9:
        return [(0, 0)] * len(points)
    axis_v = normal.normalized().cross(axis_u).normalized()
    return [(Vector(point).dot(axis_u), Vector(point).dot(axis_v)) for point in points]


def section_segments(mesh_object, height):
    """Cut one object's final mesh with a horizontal plane and return its edges as (x0, y0, x1, y1)."""
    graph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh_object.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    work = bmesh.new()
    work.from_mesh(mesh)
    work.transform(mesh_object.matrix_world)
    result = bmesh.ops.bisect_plane(
        work,
        geom=work.verts[:] + work.edges[:] + work.faces[:],
        plane_co=(0, 0, height),
        plane_no=(0, 0, 1),
        clear_inner=False,
        clear_outer=False,
    )
    segments = []
    for element in result["geom_cut"]:
        if isinstance(element, bmesh.types.BMEdge):
            start = element.verts[0].co
            end = element.verts[1].co
            segments.append((round(start.x, 4), round(start.y, 4), round(end.x, 4), round(end.y, 4)))
    work.free()
    evaluated.to_mesh_clear()
    return segments
