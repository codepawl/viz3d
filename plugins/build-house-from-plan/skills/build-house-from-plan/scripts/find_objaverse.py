"""Search Objaverse 1.0 metadata (Sketchfab models with their licenses, mirrored on Hugging Face, no login)
for objects whose name, tags or description match a pattern. Shards are streamed and not kept on disk.

Run: uv run --no-project python find_objaverse.py "godzilla|gojira|kaiju" results.json
"""

import gzip
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://huggingface.co/datasets/allenai/objaverse/resolve/main/metadata/000-{:03d}.json.gz"
SHARD_COUNT = 160
DOWNLOAD_ATTEMPTS = 4


def download_shard(shard_index):
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(BASE_URL.format(shard_index), timeout=120) as response:
                return json.loads(gzip.decompress(response.read()))
        except OSError:
            if attempt == DOWNLOAD_ATTEMPTS:
                raise
            time.sleep(attempt * 3)


def search_shard(shard_index, pattern):
    records = download_shard(shard_index)
    matches = []
    for uid, record in records.items():
        tags = " ".join(tag.get("name", "") for tag in record.get("tags", []))
        text = " ".join([record.get("name", ""), tags, record.get("description", "") or ""])
        if not pattern.search(text):
            continue
        matches.append({
            "uid": uid,
            "shard": shard_index,
            "name": record.get("name"),
            "author": (record.get("user") or {}).get("username"),
            "license": record.get("license"),
            "faces": record.get("faceCount"),
            "animations": record.get("animationCount"),
            "likes": record.get("likeCount"),
            "views": record.get("viewCount"),
            "url": record.get("viewerUrl"),
            "tags": tags,
        })
    return matches


def main():
    pattern = re.compile(sys.argv[1], re.IGNORECASE)
    output_path = sys.argv[2]
    found = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for shard_matches in pool.map(lambda index: search_shard(index, pattern), range(SHARD_COUNT)):
            found.extend(shard_matches)
    found.sort(key=lambda match: match["likes"] or 0, reverse=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(found, output_file, indent=1, ensure_ascii=False)
    for match in found[:60]:
        print(match["likes"], match["faces"], match["animations"], match["license"], match["name"], match["author"], match["url"])
    print("TOTAL", len(found))


main()
