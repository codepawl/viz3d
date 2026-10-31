"""Runs inside Blender: blender -b -P render_blender.py -- model.glb out_folder views.json samples resolution [gpu|cpu]
views.json = [{"name": "front", "yaw": 0, "pitch": 8}, ...]. yaw 0 looks at the object's front (+z in the model);
positive yaw moves the camera to the object's right. Writes out_folder/<name>.png with a transparent background and the
shadow kept.
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index("--") + 1:]
model_path = arguments[0]
output_folder = Path(arguments[1])
views = json.loads(Path(arguments[2]).read_text(encoding="utf-8"))
samples = int(arguments[3])
resolution = int(arguments[4])
device_choice = arguments[5] if len(arguments) > 5 else "gpu"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=model_path)
meshes = [item for item in bpy.context.scene.objects if item.type == "MESH"]

# Pixels stay sharp: force Closest on every image node, whatever the importer chose.
for material in bpy.data.materials:
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Specular IOR Level"].default_value = 0.3

corners = []
for mesh in meshes:
    for corner in mesh.bound_box:
        corners.append(mesh.matrix_world @ Vector(corner))
low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
center = (low + high) / 2
radius = (high - low).length / 2

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.cycles.device = "GPU"
preferences = bpy.context.preferences.addons["cycles"].preferences
for backend in ("OPTIX", "CUDA", "NONE"):
    try:
        preferences.compute_device_type = backend
        break
    except TypeError:
        continue
preferences.get_devices()
for device in preferences.devices:
    device.use = device.type != "CPU"
if device_choice == "cpu" or not any(device.use for device in preferences.devices):
    scene.cycles.device = "CPU"
scene.render.resolution_x = resolution
scene.render.resolution_y = resolution
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

world = bpy.data.worlds.new("studio")
world.use_nodes = True
background = world.node_tree.nodes["Background"]
background.inputs["Color"].default_value = (1.0, 0.98, 0.95, 1.0)
background.inputs["Strength"].default_value = 0.72
scene.world = world

bpy.ops.mesh.primitive_plane_add(size=radius * 60, location=(center.x, center.y, low.z))
bpy.context.object.is_shadow_catcher = True

sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = 2.2
sun_data.angle = math.radians(18)
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), 0, math.radians(-35))

camera_data = bpy.data.cameras.new("camera")
camera_data.lens = 70
camera_data.sensor_width = 36
camera_data.clip_end = radius * 200
camera = bpy.data.objects.new("camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
half_view = math.atan(camera_data.sensor_width / 2 / camera_data.lens)
distance = radius * 1.08 / math.sin(half_view)

for view in views:
    yaw = math.radians(view["yaw"])
    pitch = math.radians(view["pitch"])
    # The glTF importer maps model +z (front) to Blender -y.
    direction = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    camera.location = center + direction * distance
    camera.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(output_folder / f'{view["name"]}.png')
    bpy.ops.render.render(write_still=True)
