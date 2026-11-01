"""Set finished houses along a street: one appended copy per house type, instanced per lot, each with its own paint.

Run: blender -b --factory-startup -P build_street.py -- <street.json> <output.blend>
The street format is in ../references/plan-format.md, section "Streets".
"""

import json
import math
import pathlib
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import build_house  # noqa: E402
import house_core  # noqa: E402
from house_core import MeshBatch  # noqa: E402

HOUSE_COLLECTIONS = ("walls", "floors", "ceilings", "facade", "roof", "frame", "fitted", "furnish")
# Paint per lot comes from Object Info > Random, which differs per collection instance.
DEFAULT_PAINTS = {
    "siding_white": [(0.0, (1.0, 1.0, 1.0)), (0.45, (1.0, 0.95, 0.82)), (0.62, (0.82, 0.90, 0.88)), (0.78, (0.98, 0.86, 0.72)), (0.9, (0.78, 0.82, 0.92))],
    "shingle_asphalt": [(0.0, (1.0, 1.0, 1.0)), (0.35, (0.72, 0.68, 0.64)), (0.7, (1.25, 1.2, 1.15))],
}


def append_house(blend_path, name, library):
    """One copy of a built house in a collection whose origin is the plan's origin."""
    with bpy.data.libraries.load(str(blend_path), link=False) as (source, target):
        target.collections = [item for item in source.collections if item in HOUSE_COLLECTIONS]
    house = bpy.data.collections.new(f"house_{name}")
    library.children.link(house)
    for collection in target.collections:
        if collection is not None:
            house.children.link(collection)
    return house


def add_paint_variation(material_name, stops):
    """Multiply a material's base colour by a colour picked per lot."""
    material = bpy.data.materials.get(material_name)
    if material is None or not material.use_nodes:
        return
    tree = material.node_tree
    surface = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if surface is None:
        return
    base_input = surface.inputs["Base Color"]
    if not base_input.links:
        return
    source_socket = base_input.links[0].from_socket
    info = tree.nodes.new("ShaderNodeObjectInfo")
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    elements = ramp.color_ramp.elements
    elements[0].position = stops[0][0]
    elements[0].color = (*stops[0][1], 1)
    elements[1].position = stops[1][0]
    elements[1].color = (*stops[1][1], 1)
    for position, colour in stops[2:]:
        extra = elements.new(position)
        extra.color = (*colour, 1)
    multiply = tree.nodes.new("ShaderNodeMix")
    multiply.data_type = "RGBA"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    tree.links.new(info.outputs["Random"], ramp.inputs["Fac"])
    tree.links.new(source_socket, multiply.inputs[6])
    tree.links.new(ramp.outputs["Color"], multiply.inputs[7])
    tree.links.new(multiply.outputs[2], base_input)


def place_house(house, name, lot, scale, target):
    instance = bpy.data.objects.new(name, None)
    instance.instance_type = "COLLECTION"
    instance.instance_collection = house
    instance.location = (lot["at"][0] * scale, lot["at"][1] * scale, 0.0)
    instance.rotation_euler = (0, 0, math.radians(lot.get("rot", 0)))
    target.objects.link(instance)
    return instance


def lot_footprints(plan_slabs, lot):
    """Slab outlines of one lot in street metres, for keeping grass out."""
    angle = math.radians(lot.get("rot", 0))
    rotation = Matrix.Rotation(angle, 2)
    origin = Vector(lot["at"])
    outlines = []
    for slab in plan_slabs:
        outlines.append([list(origin + rotation @ Vector(point)) for point in slab["poly"]])
    return outlines


SLAB_DEPTH = 1.5


def build_strips(street, collection):
    """Road, pavements and drives as slabs, so a kerb has a face and no gap shows black beside the road."""
    batch = MeshBatch("street_surfaces", 71)
    for surface in street.get("surfaces", []):
        height = surface.get("z", 0.0)
        batch.add_prism(surface["poly"], height - SLAB_DEPTH, height, surface["material"])
    batch.finish(collection)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    street_path = pathlib.Path(arguments[0]).resolve()
    output = pathlib.Path(arguments[1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.loads(street_path.read_text(encoding="utf-8"))
    scale = build_house.METRES_PER_UNIT[raw.get("units", "ft")]
    street = build_house.convert_lengths(raw, scale)
    street["levels"] = {"floor": 0.0, "ceiling": 2.4}
    street["_folder"] = street_path.parent
    bpy.ops.wm.read_factory_settings(use_empty=True)
    library = build_house.new_collection("library")
    site = build_house.new_collection("site")
    lots = build_house.new_collection("lots")
    keep_out = []
    for type_name, house_type in raw["house_types"].items():
        blend_path = (street_path.parent / house_type["blend"]).resolve()
        plan_path = (street_path.parent / house_type["plan"]).resolve()
        house_plan = build_house.load_plan(plan_path)
        house = append_house(blend_path, type_name, library)
        for index, lot in enumerate(raw["lots"]):
            if lot["type"] != type_name:
                continue
            place_house(house, f"lot_{type_name}_{index}", lot, scale, lots)
            metric_lot = {"at": [lot["at"][0] * scale, lot["at"][1] * scale], "rot": lot.get("rot", 0)}
            keep_out += lot_footprints(house_plan.get("slabs", []), metric_lot)
    for material_name, stops in raw.get("paints", DEFAULT_PAINTS).items():
        add_paint_variation(material_name, stops)
    street.setdefault("rooms", [])
    street["slabs"] = [{"poly": outline} for outline in keep_out]
    street["site"].setdefault("paths", [])
    street["site"]["no_grass"] = street["site"].get("no_grass", []) + [surface["poly"] for surface in street.get("surfaces", [])]
    report = {"placed": [], "clashes": [], "missing": []}
    for item in street["site"].get("plants", []) + build_house.treeline_items(street):
        build_house.place_asset(street, item, library, site, report, on_ground=True)
    build_strips(street, site)
    build_house.build_ground(street, site)
    build_house.scatter_grass(street, site, library)
    bpy.context.view_layer.layer_collection.children["library"].exclude = True
    for missing in report["missing"]:
        print("MISSING", missing)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print("saved", output, "lots", len(raw["lots"]))


if __name__ != "build_street":
    main()
