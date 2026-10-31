"""Packs a BlockModel's face textures into one atlas and writes a GLB with nearest-neighbour sampling, plus a three.js viewer."""

import base64
import io
import json
import struct

import numpy
from PIL import Image

from block_kit import FACES

VIEWER_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  html, body { margin: 0; height: 100%; background: #e6e2d8; }
  canvas { display: block; width: 100%; height: 100%; }
</style>
<script type="importmap">
{ "imports": {
  "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
} }
</script>
</head>
<body>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const modelBase64 = "__MODEL__";

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe6e2d8);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffffff, 0xa89f90, 1.9));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.2);
sun.position.set(-1.5, 3, 2.5);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.normalBias = 0.02;
scene.add(sun);

const camera = new THREE.PerspectiveCamera(24, 1, 0.01, 200);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.4;

const modelBytes = Uint8Array.from(atob(modelBase64), (character) => character.charCodeAt(0));
new GLTFLoader().parse(modelBytes.buffer, "", (gltf) => {
  gltf.scene.traverse((node) => {
    if (node.isMesh) {
      node.castShadow = true;
      node.receiveShadow = true;
    }
  });
  scene.add(gltf.scene);
  const bounds = new THREE.Box3().setFromObject(gltf.scene);
  const center = bounds.getCenter(new THREE.Vector3());
  const radius = bounds.getSize(new THREE.Vector3()).length() / 2;
  controls.target.copy(center);
  camera.position.set(center.x + radius * 2.2, center.y + radius * 1.6, center.z + radius * 4.2);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(radius * 12, 64), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = bounds.min.y;
  ground.receiveShadow = true;
  scene.add(ground);
  sun.shadow.camera.left = -radius * 2;
  sun.shadow.camera.right = radius * 2;
  sun.shadow.camera.top = radius * 2;
  sun.shadow.camera.bottom = -radius * 2;
  sun.position.multiplyScalar(radius * 1.5);
  window.viewerReady = true;
});

function resize() {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();
renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});
</script>
</body>
</html>
"""

# For each face: bottom-left corner and the directions of "right" and "up" as seen from outside, in terms of box size.
FACE_FRAMES = {
    "front": {"origin": (0, 0, 1), "right": (1, 0, 0), "up": (0, 1, 0), "normal": (0, 0, 1)},
    "back": {"origin": (1, 0, 0), "right": (-1, 0, 0), "up": (0, 1, 0), "normal": (0, 0, -1)},
    "right": {"origin": (1, 0, 1), "right": (0, 0, -1), "up": (0, 1, 0), "normal": (1, 0, 0)},
    "left": {"origin": (0, 0, 0), "right": (0, 0, 1), "up": (0, 1, 0), "normal": (-1, 0, 0)},
    "top": {"origin": (0, 1, 1), "right": (1, 0, 0), "up": (0, 0, -1), "normal": (0, 1, 0)},
    "bottom": {"origin": (0, 0, 0), "right": (1, 0, 0), "up": (0, 0, 1), "normal": (0, -1, 0)},
}


def pack_atlas(model):
    """Shelf packing with one texel of padding; edges are repeated into the padding so nearest sampling never bleeds."""
    textures = []
    for box in model.boxes:
        for face in FACES:
            textures.append((box, face, box.textures[face]))
    textures.sort(key=lambda item: -item[2].shape[0])
    total_area = sum((item[2].shape[0] + 2) * (item[2].shape[1] + 2) for item in textures)
    atlas_width = max(int(numpy.ceil(numpy.sqrt(total_area * 1.3))), max(item[2].shape[1] for item in textures) + 2)
    placements = {}
    cursor_x = 0
    cursor_y = 0
    shelf_height = 0
    laid_out = []
    for box, face, texture in textures:
        height, width = texture.shape[:2]
        if cursor_x + width + 2 > atlas_width:
            cursor_x = 0
            cursor_y += shelf_height
            shelf_height = 0
        laid_out.append((box, face, texture, cursor_x + 1, cursor_y + 1))
        cursor_x += width + 2
        shelf_height = max(shelf_height, height + 2)
    atlas_height = cursor_y + shelf_height
    atlas = numpy.zeros((atlas_height, atlas_width, 3), dtype=numpy.uint8)
    for box, face, texture, x, y in laid_out:
        height, width = texture.shape[:2]
        padded = numpy.pad(texture, ((1, 1), (1, 1), (0, 0)), mode="edge")
        atlas[y - 1:y + height + 1, x - 1:x + width + 1] = padded
        placements[(id(box), face)] = (x, y, width, height)
    return atlas, placements


def write_glb(model, path, unit_size=1 / 16):
    """One primitive per (roughness, metallic). Origin: bottom centre of the model's bounds."""
    atlas, placements = pack_atlas(model)
    atlas_height, atlas_width = atlas.shape[:2]
    all_corners = numpy.vstack([box.corners() for box in model.boxes])
    center = (all_corners.min(axis=0) + all_corners.max(axis=0)) / 2
    origin = numpy.array([center[0], all_corners[:, 1].min(), center[2]])
    buckets = {}
    for box in model.boxes:
        rotation = box.rotation_matrix()
        size = numpy.asarray(box.size, dtype=float)
        low = numpy.asarray(box.low, dtype=float)
        for face in FACES:
            material = box.materials_by_face[face]
            key = (material.roughness, material.metallic)
            bucket = buckets.setdefault(key, {"positions": [], "normals": [], "uvs": []})
            frame = FACE_FRAMES[face]
            corner_origin = low + numpy.asarray(frame["origin"], dtype=float) * size
            right = numpy.asarray(frame["right"], dtype=float) * size
            up = numpy.asarray(frame["up"], dtype=float) * size
            corners = numpy.array([corner_origin, corner_origin + right, corner_origin + right + up, corner_origin + up])
            corners = box.transform(corners)
            normal = rotation @ numpy.asarray(frame["normal"], dtype=float)
            x, y, width, height = placements[(id(box), face)]
            uvs = [(x / atlas_width, (y + height) / atlas_height), ((x + width) / atlas_width, (y + height) / atlas_height),
                   ((x + width) / atlas_width, y / atlas_height), (x / atlas_width, y / atlas_height)]
            for corner, uv in zip(corners, uvs):
                bucket["positions"].append((corner - origin) * unit_size)
                bucket["normals"].append(normal)
                bucket["uvs"].append(uv)

    binary = bytearray()
    buffer_views = []
    accessors = []
    primitives = []
    gltf_materials = []

    def add_view(data, target=None):
        while len(binary) % 4:
            binary.append(0)
        view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)}
        if target:
            view["target"] = target
        buffer_views.append(view)
        binary.extend(data)
        return len(buffer_views) - 1

    def add_accessor(data, target, component_type, count, accessor_type, bounds=None):
        accessor = {"bufferView": add_view(data, target), "componentType": component_type, "count": count, "type": accessor_type}
        if bounds:
            accessor["min"] = bounds[0]
            accessor["max"] = bounds[1]
        accessors.append(accessor)
        return len(accessors) - 1

    for (roughness, metallic), bucket in buckets.items():
        positions = numpy.asarray(bucket["positions"], dtype=numpy.float32)
        normals = numpy.asarray(bucket["normals"], dtype=numpy.float32)
        uvs = numpy.asarray(bucket["uvs"], dtype=numpy.float32)
        quad_count = len(positions) // 4
        indices = numpy.zeros(quad_count * 6, dtype=numpy.uint32)
        for quad_index in range(quad_count):
            base = quad_index * 4
            indices[quad_index * 6:quad_index * 6 + 6] = [base, base + 1, base + 2, base, base + 2, base + 3]
        bounds = (positions.min(axis=0).tolist(), positions.max(axis=0).tolist())
        position_accessor = add_accessor(positions.tobytes(), 34962, 5126, len(positions), "VEC3", bounds)
        normal_accessor = add_accessor(normals.tobytes(), 34962, 5126, len(normals), "VEC3")
        uv_accessor = add_accessor(uvs.tobytes(), 34962, 5126, len(uvs), "VEC2")
        index_accessor = add_accessor(indices.tobytes(), 34963, 5125, len(indices), "SCALAR")
        gltf_materials.append({
            "name": f"block_r{roughness}_m{metallic}",
            "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "roughnessFactor": roughness, "metallicFactor": metallic},
        })
        primitives.append({"attributes": {"POSITION": position_accessor, "NORMAL": normal_accessor, "TEXCOORD_0": uv_accessor},
                           "indices": index_accessor, "material": len(gltf_materials) - 1})

    png_buffer = io.BytesIO()
    Image.fromarray(atlas).save(png_buffer, format="PNG")
    image_view = add_view(png_buffer.getvalue())
    while len(binary) % 4:
        binary.append(0)
    document = {
        "asset": {"version": "2.0", "generator": "build-minecraft-model-from-image"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "block_model"}],
        "meshes": [{"primitives": primitives, "name": "block_model"}],
        "materials": gltf_materials,
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 33071, "wrapT": 33071}],
        "images": [{"bufferView": image_view, "mimeType": "image/png"}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    json_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_bytes = json_bytes + b" " * ((4 - len(json_bytes) % 4) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary)
    with open(path, "wb") as file:
        file.write(struct.pack("<III", 0x46546C67, 2, total_length))
        file.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        file.write(json_bytes)
        file.write(struct.pack("<II", len(binary), 0x004E4942))
        file.write(bytes(binary))
    return {"atlas": [atlas_width, atlas_height], "triangles": 12 * len(model.boxes), "unit_size": unit_size}


def write_viewer(glb_path, viewer_path, title):
    with open(glb_path, "rb") as file:
        encoded_model = base64.b64encode(file.read()).decode("ascii")
    page = VIEWER_TEMPLATE.replace("__MODEL__", encoded_model).replace("__TITLE__", title)
    with open(viewer_path, "w", encoding="utf-8") as file:
        file.write(page)
