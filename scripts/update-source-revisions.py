#!/usr/bin/env python3
import json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "models/source-revisions.json"
data = json.loads(LOCK.read_text())
old = data.get("huggingface", {})
new = {}
for repo in old:
    req = urllib.request.Request(
        "https://huggingface.co/api/models/" + repo,
        headers={"User-Agent": "cloud9-embedding-engine-source-watch/1"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        new[repo] = json.load(r).get("sha")
changed = {k: {"old": old.get(k), "new": v} for k, v in new.items() if old.get(k) != v}
print(json.dumps({"changed": changed, "current": new}, indent=2))
sys.exit(2 if changed else 0)
