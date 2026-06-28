#!/usr/bin/env bash
set -euo pipefail

# Sync personal Claude artifacts from ~/.claude/ into this repo.
# Does NOT touch plans/ (curated manually) or plugins/ (maintained here).
# Files/dirs matched by memories/.shareignore are excluded from memory sync.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="${HOME}/.claude"
MEMORIES_GLOBAL="${REPO_ROOT}/memories/global"
MEMORIES_PROJECTS="${REPO_ROOT}/memories/projects"
SHAREIGNORE="${REPO_ROOT}/memories/.shareignore"
PERSONAL_CONFIG="${REPO_ROOT}/personal-config"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [-h|--help]

Sync Claude artifacts from ~/.claude/ into the biohack-claude repo.

  --dry-run    Show what would be synced without making changes
  -h, --help   Show this message
EOF
  exit 0
}

DRY_RUN=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $arg" >&2; usage ;;
  esac
done

RSYNC_OPTS=(-aL --delete --exclude='*.pyc' --exclude='__pycache__')
if [[ -n "$DRY_RUN" ]]; then
  RSYNC_OPTS+=(--dry-run)
  echo "DRY RUN — no changes will be written"
fi

# ------------------------------------------------------------------
# Global memories (~/.claude/projects/-home-will/memory/)
# ------------------------------------------------------------------
GLOBAL_SRC="${CLAUDE_DIR}/projects/-home-will/memory"
if [[ -d "$GLOBAL_SRC" ]]; then
  mkdir -p "$MEMORIES_GLOBAL"
  EXCL=()
  if [[ -f "$SHAREIGNORE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
      EXCL+=(--exclude="$line")
    done < "$SHAREIGNORE"
  fi
  rsync "${RSYNC_OPTS[@]}" "${EXCL[@]}" "$GLOBAL_SRC/" "$MEMORIES_GLOBAL/"
  echo "synced global memories → memories/global/"
else
  echo "WARN: $GLOBAL_SRC not found, skipping global memories"
fi

# ------------------------------------------------------------------
# Per-project memories (~/.claude/projects/*/memory/, excluding -home-will)
# ------------------------------------------------------------------
shopt -s nullglob
for proj_dir in "${CLAUDE_DIR}/projects/"-home-will-SRC-*/; do
  proj_name="$(basename "$proj_dir")"
  # strip the -home-will-SRC- prefix for a readable dir name
  short="${proj_name#-home-will-SRC-}"
  mem_src="${proj_dir}memory"
  if [[ -d "$mem_src" ]]; then
    dest="${MEMORIES_PROJECTS}/${short}"
    mkdir -p "$dest"
    EXCL=()
    if [[ -f "$SHAREIGNORE" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        EXCL+=(--exclude="$line")
      done < "$SHAREIGNORE"
    fi
    rsync "${RSYNC_OPTS[@]}" "${EXCL[@]}" "$mem_src/" "$dest/"
    echo "synced project memories → memories/projects/${short}/"
  fi
done

# ------------------------------------------------------------------
# personal-config/settings.json
# ------------------------------------------------------------------
cp "${CLAUDE_DIR}/settings.json" "${PERSONAL_CONFIG}/settings.json"
echo "synced settings.json → personal-config/settings.json"

echo ""
echo "Done. Review changes with: git diff memories/ personal-config/"
echo "Then commit: git add memories/ personal-config/ && git commit -m 'chore: sync claude artifacts'"
