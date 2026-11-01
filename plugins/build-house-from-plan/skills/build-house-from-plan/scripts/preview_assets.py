"""Render a labelled grid of candidate models and print their native sizes, to look at them before placing them.

Run: blender -b --factory-startup -P preview_assets.py -- <output.png> <objaverse-folder> <asset> [<asset> ...]
Assets are ph:<Poly Haven id> or obj:<Objaverse uid>. Cells read left to right, top to bottom, in the order given.
"""

import math
import os
import pathlib
import sys

import bpy
from mathutils import Vector

LIBRARY = pathlib.Path(os.environ.get("HOUSE_ASSET_LIBRARY", pathlib.Path.home() / "house-assets"))
CELL_SPACING = 2.4
COLUMNS = 5


def asset_file(asset, objaverse_folder):
    kind, name = asset.split(":", 1)
    if kind == "ph":
        matches = sorted((LIBRARY / "models" / name).glob("*.gltf"))
        return matches[0] if matches else None
    return pathlib.Path(objaverse_folder) / f"{name}.glb"


def place_in_cell(asset, index, objaverse_folder):
    path = asset_file(asset, objaverse_folder)
    if path is None or not path.exists():
        print(f"{index:2d} {asset} MISSING")
        return
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [item for item in bpy.data.objects if item not in existing]
    bpy.context.view_layer.update()
    corners = [item.matrix_world @ Vector(corner) for item in imported if item.type == "MESH" for corner in item.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    size = high - low
    triangles = sum(len(item.data.polygons) for item in imported if item.type == "MESH")
    print(f"{index:2d} {asset} size_m x={size.x:.2f} y={size.y:.2f} z={size.z:.2f} faces={triangles}")
    scale = 1.9 / max(size)
    holder = bpy.data.objects.new(f"holder_{index}", None)
    bpy.context.scene.collection.objects.link(holder)
    roots = [item for item in imported if item.parent is None]
    centre = (low + high) / 2
    for root in roots:
        root.parent = holder
        root.location = root.location - Vector((centre.x, centre.y, low.z))
    holder.scale = (scale, scale, scale)
    holder.location = ((index % COLUMNS) * CELL_SPACING, -(index // COLUMNS) * CELL_SPACING, 0)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    output = arguments[0]
    objaverse_folder = arguments[1]
    assets = arguments[2:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for index, asset in enumerate(assets):
        place_in_cell(asset, index, objaverse_folder)
    rows = math.ceil(len(assets) / COLUMNS)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(CELL_SPACING * 2, -CELL_SPACING * (rows - 1) / 2, 0))
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 2.5
    sun.angle = 0.3
    lamp = bpy.data.objects.new("sun", sun)
    bpy.context.scene.collection.objects.link(lamp)
    lamp.rotation_euler = (0.8, 0.2, 0.6)
    camera_data = bpy.data.cameras.new("camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(COLUMNS, rows * 4 / 3) * CELL_SPACING * 1.05
    camera = bpy.data.objects.new("camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    middle = Vector((CELL_SPACING * (COLUMNS - 1) / 2, -CELL_SPACING * (rows - 1) / 2, 0.7))
    camera.location = middle + Vector((-14, -24, 16))
    camera.rotation_euler = (middle - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "CYCLES"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.filepath = output
    bpy.ops.render.render(write_still=True)


main()
