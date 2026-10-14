#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m json.tool "$ROOT/models/catalog.json" >/dev/null
python3 - "$ROOT/models/catalog.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
ids=[m["id"] for m in d["models"]]
assert len(ids)==len(set(ids))
assert "qwen3-0.6b-q8" in ids
m=next(x for x in d["models"] if x["id"]=="qwen3-0.6b-q8")
assert m["status"] == "reference-validated"
assert m["dimensions"] == [1024] and m["quant"] == "Q8_0"
assert "Recherche sémantique FR/multilingue" in m["name"]
assert m["specialty"] == "Retrieval et indexation de documents FR/multilingues"
PY
C9EE_CATALOG="$ROOT/models/catalog.json" "$ROOT/bin/cloud9-embedding-engine" models | grep -F "qwen3-0.6b-q8" | grep -F "Recherche sémantique FR/multilingue"
echo "catalog and displayed model specialty ok"
