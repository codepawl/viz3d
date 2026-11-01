"""Download Objaverse 1.0 objects by uid into <folder>/<uid>.glb (Hugging Face mirror, no login).

Run: uv run --no-project python fetch_objaverse.py <folder> <uid> [<uid> ...]
"""

import gzip
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPOSITORY_URL = "https://huggingface.co/datasets/allenai/objaverse/resolve/main/"


def main():
    folder = sys.argv[1]
    uids = sys.argv[2:]
    os.makedirs(folder, exist_ok=True)
    with urllib.request.urlopen(REPOSITORY_URL + "object-paths.json.gz", timeout=300) as response:
        object_paths = json.loads(gzip.decompress(response.read()))
    for uid in uids:
        relative_path = object_paths[uid]
        target_path = os.path.join(folder, uid + ".glb")
        urllib.request.urlretrieve(REPOSITORY_URL + relative_path, target_path)
        print(uid, relative_path, os.path.getsize(target_path))


main()
