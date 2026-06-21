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
import json, os, re, sys

repo, mp_path = sys.argv[1], sys.argv[2]
plugins_dir = os.path.join(repo, "plugins")
vendor_dir = os.path.join(repo, "vendor")

with open(mp_path) as f:
    mp = json.load(f)


def is_external(p):
    """A vendored entry references an external repo (github/git-subdir object,
    or any source string that isn't a local ./plugins/ path)."""
    src = p.get("source")
    if isinstance(src, dict):
        return True
    return isinstance(src, str) and not src.startswith("./plugins/")


def parse_frontmatter(path):
    """Minimal YAML front-matter scalar reader (no yaml dep) — top-level key: value."""
    fm = {}
    try:
        with open(path) as f:
            text = f.read()
    except OSError:
        return fm
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return fm


# name -> entry, as declared in the manifest
manifest = {}
problems = []
for p in mp.get("plugins", []):
    name = p.get("name")
    if not name:
        problems.append("manifest entry missing a 'name' field")
        continue
    if name in manifest:
        problems.append(f"manifest lists '{name}' more than once")
    manifest[name] = p

# "Promoted" vendored skills back a marketplace entry: kept-reference (entry points at
# the upstream repo) or kept-fork (entry points at my fork — PR open or merged upstream).
PROMOTED = ("kept-reference", "kept-fork")
promoted = {}        # plugin -> (eval path, state)
vendor_states = {}   # vendor dir -> (state, plugin)
if os.path.isdir(vendor_dir):
    for entry in sorted(os.listdir(vendor_dir)):
        ev = os.path.join(vendor_dir, entry, "EVALUATION.md")
        if not os.path.isfile(ev):
            continue
        fm = parse_frontmatter(ev)
        state, plugin = fm.get("state"), fm.get("plugin")
        vendor_states[entry] = (state, plugin or entry)
        if state in PROMOTED and plugin:
            promoted[plugin] = (ev, state)

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

# A local plugin dir exists but isn't registered — the bug we are guarding against.
for name, entry in on_disk.items():
    if name not in manifest:
        problems.append(
            f"plugins/{entry}/ is not registered in marketplace.json "
            f"(add an entry with \"source\": \"./plugins/{entry}\")"
        )

# Each manifest entry resolves to EITHER a local plugins/ dir OR a promoted vendor eval.
for name, entry in manifest.items():
    if is_external(entry):
        if name not in promoted:
            problems.append(
                f"external entry '{name}' is not backed by a vendor/*/EVALUATION.md "
                f"with state=kept-reference|kept-fork and plugin={name} "
                f"(add/promote the evaluation, or remove the entry)"
            )
        continue
    source = entry.get("source", "")
    if name not in on_disk:
        problems.append(
            f"manifest entry '{name}' has no matching plugins/*/ dir "
            f"whose plugin.json name is '{name}' (stale entry or rename?)"
        )
        continue
    expected = f"./plugins/{on_disk[name]}"
    if source != expected and not (isinstance(source, str) and source.startswith("{")):
        problems.append(
            f"manifest entry '{name}' has source '{source}', expected '{expected}'"
        )

# A promoted eval (kept-reference/kept-fork) whose plugin was never added to the manifest.
for plugin, (ev, state) in promoted.items():
    if plugin not in manifest:
        rel = os.path.relpath(ev, repo)
        problems.append(
            f"{rel} is state={state} (plugin={plugin}) but no marketplace "
            f"entry '{plugin}' exists (add the entry or change the state)"
        )

# Advisory: vendored skills still mid-flight are expected to be absent from the manifest.
advisories = [
    f"vendor/{d}/ is state={st or '?'} (plugin={pl}) — not in marketplace (expected)"
    for d, (st, pl) in sorted(vendor_states.items())
    if st not in PROMOTED
]
for a in advisories:
    print(f"  · {a}", file=sys.stderr)

if problems:
    print("marketplace.json is out of sync:", file=sys.stderr)
    for p in problems:
        print(f"  ✗ {p}", file=sys.stderr)
    print(f"\n{len(problems)} problem(s). Update .claude-plugin/marketplace.json or the vendor evals.", file=sys.stderr)
    sys.exit(1)

n_ext = sum(1 for e in manifest.values() if is_external(e))
n_local = len(manifest) - n_ext
print(f"marketplace.json in sync — {n_local} local + {n_ext} vendored, all registered & backed.")
PYEOF
