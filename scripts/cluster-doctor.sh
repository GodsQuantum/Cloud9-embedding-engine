#!/usr/bin/env bash
set -Eeuo pipefail
nodes=${C9EE_CLUSTER_NODES:-${1:-}}
[[ -n "$nodes" ]] || { echo "Usage: C9EE_CLUSTER_NODES=http://node1:8091,http://node2:8091 $0" >&2; exit 64; }

IFS=',' read -r -a list <<<"$nodes"
fail=0
for base in "${list[@]}"; do
  base=${base%/}
  echo "== $base =="
  if ! curl -fsS --connect-timeout 2 --max-time 5 "$base/health" >/tmp/c9ee-health.$$; then
    echo "health: FAIL" >&2; fail=1; continue
  fi
  echo "health: OK"
  if curl -fsS --connect-timeout 2 --max-time 5 "$base/v1/models" >/tmp/c9ee-models.$$; then
    python3 - /tmp/c9ee-models.$$ <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    ids=[x.get("id","?") for x in d.get("data",[])]
    print("models:", ", ".join(ids) if ids else "(none reported)")
except Exception as e:
    print("models: unreadable:", e)
PY
  else
    echo "models: probe unavailable"
  fi
done
rm -f /tmp/c9ee-health.$$ /tmp/c9ee-models.$$
exit "$fail"
