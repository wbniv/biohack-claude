#!/usr/bin/env bash
set -euo pipefail
# Regenerate .claude-plugin/marketplace.json from the current plugins/ tree.
# Run after adding, removing, or renaming a plugin.
# Preserves the existing owner/description fields; rewrites the plugins[] array.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE="${REPO_ROOT}/.claude-plugin/marketplace.json"

usage() {
  cat <<EOF
Usage: $(basename "$0") [-h|--help]

Regenerate .claude-plugin/marketplace.json from plugins/*/

Each plugin must have .claude-plugin/plugin.json with at least:
  { "name": "...", "description": "...", "author": {...} }

The plugin's category is inferred from a "category" field in plugin.json if present.
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage ;;
    *) echo "unknown argument: $arg" >&2; usage ;;
  esac
done

if ! command -v python3 &>/dev/null; then
  echo "error: python3 required" >&2; exit 1
fi

python3 - << PYEOF
import json, os, sys

repo = "${REPO_ROOT}"
mp_path = "${MARKETPLACE}"

# Load existing marketplace.json for owner/description/schema
with open(mp_path) as f:
    mp = json.load(f)

plugins_dir = os.path.join(repo, "plugins")
plugins = []

for entry in sorted(os.listdir(plugins_dir)):
    pj_path = os.path.join(plugins_dir, entry, ".claude-plugin", "plugin.json")
    if not os.path.isfile(pj_path):
        print(f"WARN: {entry}/.claude-plugin/plugin.json missing — skipping", file=sys.stderr)
        continue
    with open(pj_path) as f:
        pj = json.load(f)

    record = {
        "name": pj["name"],
        "description": pj.get("description", ""),
        "author": pj.get("author", {}),
    }
    if "category" in pj:
        record["category"] = pj["category"]
    record["source"] = f"./plugins/{entry}"

    # Preserve any MCP or extra source metadata from existing entry
    existing = next((p for p in mp.get("plugins", []) if p["name"] == record["name"]), None)
    if existing and existing.get("source", "").startswith("{"):
        record["source"] = existing["source"]
    if existing and "homepage" in existing:
        record["homepage"] = existing["homepage"]

    plugins.append(record)

mp["plugins"] = plugins
with open(mp_path, "w") as f:
    json.dump(mp, f, indent=2)
    f.write("\n")

print(f"marketplace.json updated — {len(plugins)} plugin(s)")
for p in plugins:
    print(f"  {p['name']}  [{p.get('category', '—')}]")
PYEOF
