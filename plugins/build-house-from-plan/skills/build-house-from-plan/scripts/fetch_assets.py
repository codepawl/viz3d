"""Download what a plan needs from Poly Haven and ambientCG (both CC0) into the asset library.

Run: uv run --no-project python fetch_assets.py plan.json
The library is HOUSE_ASSET_LIBRARY, or the default named in house_core.py. Objaverse models (`obj:`) use fetch_objaverse.py.
"""

import ast
import io
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = pathlib.Path(__file__).resolve().parent
HEADERS = {"User-Agent": "house-from-plan-fetch/1.0"}
TEXTURE_MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "Rough": "rough", "Displacement": "disp", "AO": "ao"}
DEFAULT_HDRI = "kloofendal_48d_partly_cloudy_puresky"


def library_folder():
    source = (SCRIPTS / "house_core.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        if line.startswith("LIBRARY = "):
            default_library = line
            break
    configured = os.environ.get("HOUSE_ASSET_LIBRARY")
    if configured:
        return pathlib.Path(configured)
    namespace = {"pathlib": pathlib, "os": os}
    exec(default_library, namespace)
    return namespace["LIBRARY"]


def texture_folders():
    tree = ast.parse((SCRIPTS / "house_core.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "TEXTURED_MATERIALS":
            table = ast.literal_eval(node.value)
            return sorted({entry[0] for entry in table.values()})
    raise SystemExit("TEXTURED_MATERIALS not found")


def fetch_bytes(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def fetch_json(url):
    return json.loads(fetch_bytes(url))


def save(url, target):
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(fetch_bytes(url))


def fetch_texture_ambientcg(name, folder):
    data = fetch_bytes(f"https://ambientcg.com/get?file={name}_2K-JPG.zip")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(folder)


def fetch_texture(name, library):
    folder = library / "textures" / name
    if folder.exists() and any(folder.iterdir()):
        return
    folder.mkdir(parents=True, exist_ok=True)
    try:
        files = fetch_json(f"https://api.polyhaven.com/files/{name}")
    except urllib.error.HTTPError:
        fetch_texture_ambientcg(name, folder)
        print("ambientCG", name)
        return
    for key, short in TEXTURE_MAPS.items():
        entry = files.get(key)
        if entry:
            save(entry["2k"]["jpg"]["url"], folder / f"{name}_{short}_2k.jpg")
    print("Poly Haven texture", name)


def fetch_model(name, library):
    folder = library / "models" / name
    if list(folder.glob("*.gltf")):
        return
    gltf = fetch_json(f"https://api.polyhaven.com/files/{name}")["gltf"]["2k"]["gltf"]
    save(gltf["url"], folder / f"{name}_2k.gltf")
    for relative, entry in gltf["include"].items():
        save(entry["url"], folder / relative)
    print("Poly Haven model", name)


def fetch_hdri(name, library):
    target = library / "hdri" / f"{name}_2k.hdr"
    if target.exists():
        return
    save(fetch_json(f"https://api.polyhaven.com/files/{name}")["hdri"]["2k"]["hdr"]["url"], target)
    print("Poly Haven HDRI", name)


def plan_models(plan):
    site = plan.get("site", {})
    items = plan.get("furnish", []) + site.get("plants", [])
    names = {item["asset"].split(":", 1)[1] for item in items if item["asset"].startswith("ph:")}
    for asset in site.get("treeline", {}).get("assets", []):
        if asset.startswith("ph:"):
            names.add(asset.split(":", 1)[1])
    return sorted(names)


def main():
    plan = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    library = library_folder()
    for name in texture_folders():
        fetch_texture(name, library)
    for name in plan_models(plan):
        fetch_model(name, library)
    fetch_hdri(plan.get("site", {}).get("hdri", DEFAULT_HDRI), library)
    print("library ready:", library)


main()
