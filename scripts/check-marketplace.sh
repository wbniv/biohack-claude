#!/usr/bin/env bash
set -euo pipefail
# Verify .claude-plugin/marketplace.json is in sync with the plugins/ tree.
#
# Catches the failure mode where a plugin is added under plugins/<name>/ but
# never registered in the manifest (so `/plugin install <name>@biohack-claude`
# returns "not found in marketplace"), and the inverse: a manifest entry whose
# source directory is missing or whose name disagrees with its plugin.json.
#
# Exits non-zero with a list of discrepancies. Run locally or in CI.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE="${REPO_ROOT}/.claude-plugin/marketplace.json"

if ! command -v python3 &>/dev/null; then
  echo "error: python3 required" >&2; exit 1
fi

python3 - "$REPO_ROOT" "$MARKETPLACE" << 'PYEOF'
import json, os, sys

repo, mp_path = sys.argv[1], sys.argv[2]
plugins_dir = os.path.join(repo, "plugins")

with open(mp_path) as f:
    mp = json.load(f)

# name -> source, as declared in the manifest
manifest = {}
problems = []
for p in mp.get("plugins", []):
    name = p.get("name")
    if not name:
        problems.append("manifest entry missing a 'name' field")
        continue
    if name in manifest:
        problems.append(f"manifest lists '{name}' more than once")
    manifest[name] = p.get("source", "")

# name -> dir, as found on disk (any plugins/<dir>/.claude-plugin/plugin.json)
on_disk = {}
for entry in sorted(os.listdir(plugins_dir)):
    pj_path = os.path.join(plugins_dir, entry, ".claude-plugin", "plugin.json")
    if not os.path.isfile(pj_path):
        continue
    with open(pj_path) as f:
        pj = json.load(f)
    name = pj.get("name")
    if not name:
        problems.append(f"plugins/{entry}/.claude-plugin/plugin.json missing a 'name' field")
        continue
    on_disk[name] = entry

# A plugin dir exists but isn't registered — the bug we are guarding against.
for name, entry in on_disk.items():
    if name not in manifest:
        problems.append(
            f"plugins/{entry}/ is not registered in marketplace.json "
            f"(add an entry with \"source\": \"./plugins/{entry}\")"
        )

# A manifest entry points at a directory that's missing or name-mismatched.
for name, source in manifest.items():
    if name not in on_disk:
        problems.append(
            f"manifest entry '{name}' has no matching plugins/*/ dir "
            f"whose plugin.json name is '{name}' (stale entry or rename?)"
        )
        continue
    expected = f"./plugins/{on_disk[name]}"
    if source != expected and not source.startswith("{"):
        problems.append(
            f"manifest entry '{name}' has source '{source}', expected '{expected}'"
        )

if problems:
    print("marketplace.json is out of sync with plugins/:", file=sys.stderr)
    for p in problems:
        print(f"  ✗ {p}", file=sys.stderr)
    print(f"\n{len(problems)} problem(s). Update .claude-plugin/marketplace.json.", file=sys.stderr)
    sys.exit(1)

print(f"marketplace.json in sync — {len(manifest)} plugin(s), all registered.")
PYEOF
