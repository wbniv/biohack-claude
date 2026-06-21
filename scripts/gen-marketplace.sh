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
local = []
local_names = set()

for entry in sorted(os.listdir(plugins_dir)):
    pj_path = os.path.join(plugins_dir, entry, ".claude-plugin", "plugin.json")
    if not os.path.isfile(pj_path):
        print(f"WARN: {entry}/.claude-plugin/plugin.json missing — skipping", file=sys.stderr)
        continue
    with open(pj_path) as f:
        pj = json.load(f)

    existing = next((p for p in mp.get("plugins", []) if p.get("name") == pj["name"]), None)

    record = {
        "name": pj["name"],
        "description": pj.get("description", ""),
        "author": pj.get("author", {}),
    }
    # Category lives in the plugin's own plugin.json; fall back to the existing
    # manifest entry so a hand-set category is never silently dropped.
    category = pj.get("category") or (existing.get("category") if existing else None)
    if category:
        record["category"] = category
        if "category" not in pj:
            print(f"WARN: {entry}/.claude-plugin/plugin.json has no 'category'; "
                  f"kept '{category}' from existing manifest", file=sys.stderr)
    record["source"] = f"./plugins/{entry}"

    # Preserve any MCP or extra source metadata from existing entry
    if existing and isinstance(existing.get("source"), str) and existing["source"].startswith("{"):
        record["source"] = existing["source"]
    if existing and "homepage" in existing:
        record["homepage"] = existing["homepage"]

    local.append(record)
    local_names.add(pj["name"])

# Preserve vendored "kept-reference" entries. These point at an external repo
# (source is a github/git-subdir object, not a local "./plugins/…" path) and
# have no plugins/<name>/ dir on disk, so the loop above never produces them.
# They are added by hand when a vendored skill is promoted; carry them through
# verbatim so a regen never silently drops them. check-marketplace.sh enforces
# that each external entry is backed by a vendor/*/EVALUATION.md (kept-reference).
def is_external(p):
    src = p.get("source")
    if isinstance(src, dict):
        return True
    return isinstance(src, str) and not src.startswith("./plugins/")

external = [p for p in mp.get("plugins", [])
            if is_external(p) and p.get("name") not in local_names]
external.sort(key=lambda p: p.get("name", ""))

mp["plugins"] = local + external
with open(mp_path, "w") as f:
    json.dump(mp, f, indent=2)
    f.write("\n")

print(f"marketplace.json updated — {len(local)} local + {len(external)} vendored")
for p in local:
    print(f"  {p['name']}  [{p.get('category', '—')}]")
for p in external:
    src = p.get("source", {})
    origin = (src.get("repo") or src.get("url")) if isinstance(src, dict) else src
    print(f"  {p['name']}  [vendored ← {origin}]")
PYEOF
