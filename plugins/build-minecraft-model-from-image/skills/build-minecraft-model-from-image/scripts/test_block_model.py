# /// script
# dependencies = ["numpy", "pillow"]
# ///
"""Behaviour tests for the claims SKILL.md makes. Run: uv run --no-project test_block_model.py. No GPU or Blender needed."""

import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy

SCRIPT_FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_FOLDER))

import block_export  # noqa: E402
import block_kit  # noqa: E402

OBJECT_HEADER = """
def build(kit):
    materials = {"stone": kit.Material(["#aaaaaa", "#888888", "#666666"])}
    model = kit.BlockModel(materials)
"""


def run_object_script(folder, body):
    script = folder / "object.py"
    script.write_text(OBJECT_HEADER + body + "\n    return model\n", encoding="utf-8")
    output = folder / "output ảnh"  # non-ASCII and a space, on purpose
    result = subprocess.run([sys.executable, str(SCRIPT_FOLDER / "build_model.py"), str(script), "--out", str(output), "--no-render"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    checks_path = output / "checks.json"
    checks = json.loads(checks_path.read_text(encoding="utf-8")) if checks_path.exists() else {}
    return result.returncode, checks, output


def read_glb(path):
    data = Path(path).read_bytes()
    magic, version, total = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67 and version == 2 and total == len(data)
    json_length, json_type = struct.unpack("<II", data[12:20])
    assert json_type == 0x4E4F534A
    document = json.loads(data[20:20 + json_length])
    binary_start = 20 + json_length + 8
    return document, data[binary_start:]


def read_accessor(document, binary, index, component_count, dtype):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    values = numpy.frombuffer(binary, dtype=dtype, count=accessor["count"] * component_count, offset=view["byteOffset"])
    return values.reshape(-1, component_count) if component_count > 1 else values


def test_floating_part_fails():
    with tempfile.TemporaryDirectory() as folder:
        code, checks, _ = run_object_script(Path(folder), '    model.box((0, 0, 0), (4, 4, 4), "stone")\n    model.box((9, 9, 9), (2, 2, 2), "stone")')
        assert code == 1 and checks["groups"] == 2, checks


def test_extrusion_fails():
    with tempfile.TemporaryDirectory() as folder:
        code, checks, _ = run_object_script(Path(folder), '    model.box((0, 0, 0), (8, 3, 2), "stone")\n    model.box((3, 3, 0), (2, 6, 2), "stone")')
        assert code == 1 and checks["prism_fraction"] > 0.92, checks


def test_real_model_passes_and_writes_files():
    with tempfile.TemporaryDirectory() as folder:
        body = '    model.round(8, 8, 0, 4, 12, "stone", corner=3)\n    model.box((6, 4, 6), (4, 6, 4), "stone")\n    model.beam((8, 10, 8), (12, 14, 8), (1, 2), "stone")'
        code, checks, output = run_object_script(Path(folder), body)
        assert code == 0, checks
        assert not checks["warnings"], checks["warnings"]
        assert (output / "model.glb").exists() and (output / "viewer.html").exists()


def test_coplanar_overlap_warns():
    with tempfile.TemporaryDirectory() as folder:
        body = '    model.box((0, 0, 0), (6, 6, 6), "stone")\n    model.box((3, 3, 0), (6, 6, 3), "stone")'
        _, checks, _ = run_object_script(Path(folder), body)
        assert any("coplanar" in warning for warning in checks["warnings"]), checks


def test_tiny_boxes_warn():
    with tempfile.TemporaryDirectory() as folder:
        body = '    model.box((0, 0, 0), (8, 8, 8), "stone")\n    for index in range(4):\n        model.box((index * 2, 8, 0), (1, 1, 1), "stone")'
        _, checks, _ = run_object_script(Path(folder), body)
        assert any("tiny" in warning for warning in checks["warnings"]), checks


def test_winding_matches_normals_and_uvs_are_in_range():
    materials = {"stone": block_kit.Material(["#aaaaaa", "#888888"])}
    model = block_kit.BlockModel(materials)
    model.box((0, 0, 0), (3, 4, 5), "stone")
    model.box((0, 4, 0), (3, 2, 1), "stone", rotation=(10, 40, 20))
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "model.glb"
        block_export.write_glb(model, path)
        document, binary = read_glb(path)
    primitive = document["meshes"][0]["primitives"][0]
    positions = read_accessor(document, binary, primitive["attributes"]["POSITION"], 3, numpy.float32)
    normals = read_accessor(document, binary, primitive["attributes"]["NORMAL"], 3, numpy.float32)
    uvs = read_accessor(document, binary, primitive["attributes"]["TEXCOORD_0"], 2, numpy.float32)
    indices = read_accessor(document, binary, primitive["indices"], 1, numpy.uint32)
    assert document["samplers"][0]["magFilter"] == 9728
    assert uvs.min() >= 0 and uvs.max() <= 1
    for triangle in indices.reshape(-1, 3):
        first, second, third = positions[triangle]
        geometric = numpy.cross(second - first, third - first)
        assert numpy.dot(geometric, normals[triangle[0]]) > 0


def test_paint_lands_where_seen_from_outside():
    """Top-left of the front face as seen is low x, high y; on the right face, top-left as seen is high z."""
    materials = {"stone": block_kit.Material(["#808080"], noise=0.0, rim=False)}
    model = block_kit.BlockModel(materials)
    box = model.box((0, 0, 0), (4, 4, 4), "stone")
    box.paint("front", ["#"], {"#": "#ff0000"})
    box.paint("right", ["#"], {"#": "#00ff00"})
    frames = block_export.FACE_FRAMES
    assert tuple(box.textures["front"][0, 0]) == (255, 0, 0)
    assert frames["front"]["right"] == (1, 0, 0) and frames["front"]["origin"] == (0, 0, 1)
    assert tuple(box.textures["right"][0, 0]) == (0, 255, 0)
    assert frames["right"]["right"] == (0, 0, -1) and frames["right"]["origin"] == (1, 0, 1)


def test_round_fillers_do_not_overlap_the_core():
    materials = {"stone": block_kit.Material(["#808080"])}
    model = block_kit.BlockModel(materials)
    parts = model.round(10, 10, 0, 3, 20, "stone", corner=4)
    assert len(parts) == 9
    for first_index, first in enumerate(parts):
        for second in parts[first_index + 1:]:
            overlaps = all(first.low[axis] < second.low[axis] + second.size[axis] and second.low[axis] < first.low[axis] + first.size[axis]
                           for axis in range(3))
            assert not overlaps, (first.low, second.low)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print("ok  ", test.__name__)
        except Exception as error:  # report every test, not just the first failure
            failed += 1
            print("FAIL", test.__name__, repr(error)[:400])
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
