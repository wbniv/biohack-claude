#!/usr/bin/env bash
set -euo pipefail
# Regenerate the plugin-card sections of biohack.net's /claude/ page
# (src/pages/claude.astro) from this marketplace's plugins.
#
# It rewrites ONLY the region between these two markers in claude.astro:
#   <!-- @generated:plugin-cards start ... -->
#   <!-- @generated:plugin-cards end -->
# leaving the hand-authored styles, header, featured card, and footer intact.
#
# For each LOCAL, non-featured plugin it emits a styled card matching the page:
#   <div class="plugin"> name / description / install / source-link </div>
# grouped by category. Card order within a category is preserved from the
# existing page (curated); any new plugins are appended alphabetically.
# Source link -> the plugin's skills/<name>/SKILL.md if present, else the tree.
#
# Set BIOHACK_NET_DIR to override the biohack.net checkout (default ~/SRC/biohack.net).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIOHACK_NET="${BIOHACK_NET_DIR:-${HOME}/SRC/biohack.net}"
ASTRO="${BIOHACK_NET}/src/pages/claude.astro"

usage() {
  cat <<EOF
Usage: $(basename "$0") [-h|--help]

Regenerate the plugin-card sections of ${ASTRO}
from .claude-plugin/marketplace.json + each plugin's plugin.json.

Only the region between the @generated:plugin-cards markers is rewritten;
the hand-authored styles, header, featured card, and footer are left alone.

Set BIOHACK_NET_DIR to override the biohack.net checkout (default ~/SRC/biohack.net).
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage ;;
    *) echo "unknown argument: $arg" >&2; usage ;;
  esac
done

command -v python3 &>/dev/null || { echo "error: python3 required" >&2; exit 1; }
[[ -f "$ASTRO" ]] || { echo "error: ${ASTRO} not found (set BIOHACK_NET_DIR)" >&2; exit 1; }

REPO_ROOT="$REPO_ROOT" ASTRO="$ASTRO" python3 - <<'PYEOF'
import json, os, re, html, sys

repo  = os.environ["REPO_ROOT"]
astro = os.environ["ASTRO"]

START = "<!-- @generated:plugin-cards start"
END   = "<!-- @generated:plugin-cards end -->"

GITHUB = "https://github.com/wbniv/biohack-claude"
CATEGORY_GLYPH = {"techops": "⚒", "design": "✦", "meta": "⬡", "personal": "◆"}
CATEGORY_ORDER = ["techops", "design", "meta", "personal"]

# ── gather local, non-featured plugins from the marketplace ─────────────────
with open(os.path.join(repo, ".claude-plugin", "marketplace.json")) as f:
    mp = json.load(f)

plugins = []
for entry in mp["plugins"]:
    src = entry.get("source")
    if not (isinstance(src, str) and src.startswith("./plugins/")):
        continue                                  # skip vendored / external
    name = entry["name"]
    pj = {}
    pj_path = os.path.join(repo, src.lstrip("./"), ".claude-plugin", "plugin.json")
    if os.path.isfile(pj_path):
        with open(pj_path) as f:
            pj = json.load(f)
    if pj.get("featured"):
        continue                                  # owned by the hand-authored featured section
    skill = os.path.join(repo, "plugins", name, "skills", name, "SKILL.md")
    source = (f"{GITHUB}/blob/main/plugins/{name}/skills/{name}/SKILL.md"
              if os.path.isfile(skill)
              else f"{GITHUB}/tree/main/plugins/{name}")
    plugins.append({
        "name": name,
        "desc": pj.get("description") or entry.get("description", ""),
        "cat":  pj.get("category")    or entry.get("category", "other"),
        "source": source,
    })

# ── locate the generated region in claude.astro ─────────────────────────────
with open(astro) as f:
    page = f.read()

si, ei = page.find(START), page.find(END)
if si == -1 or ei == -1:
    sys.exit(f"error: @generated:plugin-cards markers not found in {astro}\n"
             f"       add '    {START} ... -->' and '    {END}'\n"
             f"       around the plugin-card <section> blocks, then re-run.")
region_start = page.index("\n", si) + 1            # just after the start-marker line
region_end   = page.rfind("\n", 0, ei) + 1         # just before the end-marker line
old_region   = page[region_start:region_end]

# preserve curated order: existing plugin-name order within the region
existing = re.findall(r'class="plugin-name">([^<]+)<', old_region)
order = {n: i for i, n in enumerate(existing)}

def esc(s):
    return html.escape(s, quote=False)

def card(p):
    return (
        '        <div class="plugin">\n'
        f'          <p class="plugin-name">{esc(p["name"])}</p>\n'
        f'          <p class="plugin-desc">{esc(p["desc"])}</p>\n'
        f'          <pre>/plugin install {esc(p["name"])}@biohack-claude</pre>\n'
        f'          <a class="source-link" href="{esc(p["source"])}" target="_blank" rel="noopener">source</a>\n'
        '        </div>'
    )

def section(cat, members):
    cards = "\n\n".join(card(p) for p in members)
    return (
        f'    <section class="category" id="{esc(cat)}">\n'
        f'      <h2>{CATEGORY_GLYPH.get(cat, "▸")} {esc(cat)}</h2>\n'
        '      <div class="plugin-grid">\n\n'
        f'{cards}\n\n'
        '      </div>\n'
        '    </section>'
    )

cats = CATEGORY_ORDER + sorted({p["cat"] for p in plugins} - set(CATEGORY_ORDER))
sections = []
for cat in cats:
    members = sorted((p for p in plugins if p["cat"] == cat),
                     key=lambda p: (order.get(p["name"], len(existing)), p["name"]))
    if members:
        sections.append(section(cat, members))

new_region = "\n\n".join(sections) + "\n"
new_page = page[:region_start] + new_region + page[region_end:]

if new_page == page:
    print(f"{astro} already up to date")
else:
    with open(astro, "w") as f:
        f.write(new_page)
    print(f"updated {astro}")
for cat in cats:
    n = sum(1 for p in plugins if p["cat"] == cat)
    if n:
        print(f"  {cat}: {n} card(s)")
PYEOF
