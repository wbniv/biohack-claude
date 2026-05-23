#!/usr/bin/env bash
set -euo pipefail
# Generate biohack.net/claude/index.html from this marketplace.
# Reads .claude-plugin/marketplace.json + each plugin's plugin.json.
# Writes to ~/SRC/biohack-net/claude/index.html (creates the directory if needed).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIOHACK_NET="${BIOHACK_NET_DIR:-${HOME}/SRC/biohack.net}"
OUT_DIR="${BIOHACK_NET}/claude"
OUT_FILE="${OUT_DIR}/index.html"

usage() {
  cat <<EOF
Usage: $(basename "$0") [-h|--help]

Generate ${OUT_FILE} from this marketplace.

Set BIOHACK_NET_DIR to override the default output path (~/SRC/biohack-net).
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage ;;
    *) echo "unknown argument: $arg" >&2; usage ;;
  esac
done

if [[ ! -d "$BIOHACK_NET" ]]; then
  echo "error: biohack-net dir not found at ${BIOHACK_NET}" >&2
  echo "       set BIOHACK_NET_DIR to override" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

python3 - << PYEOF
import json, os, html, sys
from collections import defaultdict

repo = "${REPO_ROOT}"
out  = "${OUT_FILE}"

with open(os.path.join(repo, ".claude-plugin", "marketplace.json")) as f:
    mp = json.load(f)

# Build per-category plugin list, enriching from plugin.json where available
by_category = defaultdict(list)
for entry in mp["plugins"]:
    cat = entry.get("category", "other")
    pdir = entry.get("source", "").lstrip("./")
    pj_path = os.path.join(repo, pdir, ".claude-plugin", "plugin.json")
    extra = {}
    if os.path.isfile(pj_path):
        with open(pj_path) as f:
            extra = json.load(f)
    by_category[cat].append({
        "name": entry["name"],
        "description": extra.get("description") or entry.get("description", ""),
    })

# TYPE_META glyphs for known categories
CATEGORY_META = {
    "techops": {"glyph": "⚒", "label": "techops"},
    "design":  {"glyph": "✦", "label": "design"},
    "personal":{"glyph": "◆", "label": "personal"},
}

INSTALL_BLOCK = """<pre class="install"><code>/plugin marketplace add wbniv/biohack-claude
/plugin install {name}@biohack-claude</code></pre>"""

def render_category(cat, plugins):
    meta = CATEGORY_META.get(cat, {"glyph": "▸", "label": cat})
    g = meta["glyph"]
    label = meta["label"]
    rows = ""
    for p in plugins:
        name_esc = html.escape(p["name"])
        desc_esc = html.escape(p["description"])
        install = INSTALL_BLOCK.format(name=name_esc)
        rows += f"""
      <div class="plugin">
        <h3>{name_esc}</h3>
        <p>{desc_esc}</p>
        {install}
      </div>"""
    return f"""
    <section class="category" id="{html.escape(cat)}">
      <h2>{g} {label}</h2>
      {rows}
    </section>"""

sections = ""
# Render techops first, then rest alphabetically
order = ["techops"] + sorted(k for k in by_category if k != "techops")
for cat in order:
    if cat in by_category:
        sections += render_category(cat, by_category[cat])

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claude plugins — biohack.net</title>
  <style>
    body {{ font-family: monospace; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
    h1 {{ font-size: 1.4rem; border-bottom: 1px solid #ccc; padding-bottom: .5rem; }}
    h2 {{ font-size: 1.1rem; margin-top: 2rem; color: #555; }}
    h3 {{ font-size: 1rem; margin-bottom: .25rem; }}
    .plugin {{ margin: 1.5rem 0; padding-left: 1rem; border-left: 3px solid #eee; }}
    pre.install {{ background: #f5f5f5; padding: .75rem 1rem; border-radius: 4px; overflow-x: auto; margin-top: .5rem; }}
    pre.install code {{ font-size: .85rem; }}
    a {{ color: inherit; }}
  </style>
</head>
<body>
  <h1>Claude plugins</h1>
  <p>
    Will's personal <a href="https://github.com/wbniv/biohack-claude">Claude Code marketplace</a>.
    Install via:
  </p>
  <pre class="install"><code>/plugin marketplace add wbniv/biohack-claude</code></pre>
  {sections}
</body>
</html>
"""

with open(out, "w") as f:
    f.write(page)
print(f"wrote {out}")
for cat, plugins in by_category.items():
    print(f"  {cat}: {len(plugins)} plugin(s)")
PYEOF
