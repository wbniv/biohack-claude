#!/usr/bin/env python3
"""
apply-cascade.py — cascade global Claude memories into a project.

Invoked from the `missing-cascade` recommendation's command_block. Idempotent;
safe to re-run.

Usage:
    apply-cascade.py PROJECT_PATH

For the given project:
  1. Symlinks each .md in ~/.claude/memory/ (excluding MEMORY.md and
     memory-visualization.md) that is IN SCOPE for the project into
     <project>/.claude/memory/, using RELATIVE paths (e.g.
     ../../../../.claude/memory/<name>) so the symlinks survive being
     checked into a project repo and cloned at a different absolute path.
     In scope = the memory's `applies-to:` frontmatter is `universal` OR
     intersects the project's `tags` (projects.json). Untagged project →
     `universal` memories only.
  2. Removes stale symlinks (target no longer exists) AND prunes symlinks
     to memories that are no longer in scope for the project.
  3. Merges global MEMORY.md sections into <project>/.claude/memory/MEMORY.md
     between auto-managed markers, preserving everything outside the markers.
     Index source: ~/.claude/projects/-home-will/memory/MEMORY.md (the
     cwd=~ auto-memory dir, which now also serves as the de-facto global
     cascade index).

Exit codes:
  0 — clean
  1 — collisions (project had a real file with same name as a global; skipped)
  2 — setup error (project path / global memory dir missing)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
# Canonical global memory: cross-cutting feedback_*.md and user_*.md live here.
# Relative symlinks in per-project .claude/memory/ point at this dir.
GLOBAL_MEMORY_DIR = HOME / ".claude" / "memory"
# Index source for the cascade block in each project's MEMORY.md. The cwd=~
# auto-memory dir's MEMORY.md is the de-facto global index (its entries are
# the cross-cutting memories now living at GLOBAL_MEMORY_DIR via symlinks).
MEMORY_INDEX_SOURCE = HOME / ".claude" / "projects" / "-home-will" / "memory" / "MEMORY.md"
# Legacy global dir — sweep stale symlinks pointing here, from before the
# 2026-05-21 canonical migration. Keep this around until every project has
# been re-cascaded.
LEGACY_GLOBAL_MEMORY_DIR = HOME / ".claude" / "projects" / "-home-will" / "memory"
EXCLUDED_NAMES = {"MEMORY.md", "memory-visualization.md"}

MEMORY_BEGIN = "<!-- BEGIN GLOBAL MEMORY (managed by claude-housekeeping; do not edit) -->"
MEMORY_END = "<!-- END GLOBAL MEMORY -->"

PROJECTS_JSON = HOME / ".claude" / "projects.json"
_APPLIES_RE = re.compile(r"^applies-to:\s*\[([^\]]*)\]", re.MULTILINE)


def _load_project_tags(project_path: Path) -> set[str]:
    """Scope tags for this project from projects.json (empty set if unknown →
    the project receives only `universal` memories)."""
    try:
        data = json.loads(PROJECTS_JSON.read_text())
    except Exception:
        return set()
    rp = project_path.resolve()
    for entry in data.get("projects", []):
        ep = Path(os.path.expanduser(entry.get("path", ""))).resolve()
        if ep == rp or entry.get("name") == project_path.name:
            return set(entry.get("tags", []))
    return set()


def _memory_applies_to(md_file: Path) -> set[str]:
    """`applies-to: [a, b]` from a memory's frontmatter. Absent → {'universal'}
    (back-compat: an untagged memory still cascades everywhere)."""
    try:
        head = md_file.read_text()[:2000]
    except Exception:
        return {"universal"}
    m = _APPLIES_RE.search(head)
    if not m:
        return {"universal"}
    return {t.strip() for t in m.group(1).split(",") if t.strip()}


def _qualifies(applies_to: set[str], project_tags: set[str]) -> bool:
    """A memory belongs in a project if it's universal or their tags intersect."""
    return "universal" in applies_to or bool(applies_to & project_tags)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PROJECT_PATH", file=sys.stderr)
        return 2

    project_path = Path(sys.argv[1]).expanduser().resolve()
    if not project_path.is_dir():
        print(f"ERROR: project path not found: {project_path}", file=sys.stderr)
        return 2

    if not GLOBAL_MEMORY_DIR.is_dir():
        print(f"ERROR: global memory dir not found: {GLOBAL_MEMORY_DIR}", file=sys.stderr)
        return 2

    project_memory_dir = project_path / ".claude" / "memory"
    project_memory_dir.mkdir(parents=True, exist_ok=True)

    global_files = sorted(
        f for f in GLOBAL_MEMORY_DIR.glob("*.md")
        if f.name not in EXCLUDED_NAMES
    )

    # Scope filter: only cascade a memory into this project if it's `universal`
    # or its `applies-to:` tags intersect the project's `tags` (projects.json).
    # Memories that don't qualify are pruned from the project below.
    project_tags = _load_project_tags(project_path)
    qualifying = [f for f in global_files
                  if _qualifies(_memory_applies_to(f), project_tags)]
    disqualified = {f.name for f in global_files} - {f.name for f in qualifying}

    created: list[str] = []
    relinked: list[str] = []
    kept: list[str] = []
    collisions: list[str] = []
    removed: list[str] = []

    # Create / verify symlinks for each global memory file. Symlinks are
    # written in RELATIVE form (e.g. ../../../../.claude/memory/<name>) so
    # they survive being checked into a project repo and cloned at a
    # different absolute path.
    for gf in qualifying:
        target = project_memory_dir / gf.name
        relative_target = os.path.relpath(gf, target.parent)
        if target.is_symlink():
            if target.resolve() == gf.resolve():
                # Already points at the right canonical, but may still be
                # an absolute symlink from before the migration — convert.
                if os.readlink(target) != relative_target:
                    target.unlink()
                    target.symlink_to(relative_target)
                    relinked.append(gf.name)
                else:
                    kept.append(gf.name)
                continue
            target.unlink()
            target.symlink_to(relative_target)
            relinked.append(gf.name)
        elif target.exists():
            collisions.append(gf.name)
        else:
            target.symlink_to(relative_target)
            created.append(gf.name)

    # Sweep stale symlinks (point into either current or legacy global dir,
    # target gone). The legacy sweep cleans up post-migration leftovers.
    sweep_prefixes = (str(GLOBAL_MEMORY_DIR), str(LEGACY_GLOBAL_MEMORY_DIR))
    for entry in project_memory_dir.iterdir():
        if not entry.is_symlink():
            continue
        link_target = os.readlink(entry)
        # Resolve to detect relative-form symlinks whose absolute target is
        # one of the sweep dirs.
        try:
            resolved_parent = entry.resolve().parent
        except OSError:
            resolved_parent = None
        in_sweep_target = any(link_target.startswith(p) for p in sweep_prefixes) or (
            resolved_parent is not None and str(resolved_parent) in sweep_prefixes
        )
        if not in_sweep_target:
            continue
        if not entry.resolve().exists():
            entry.unlink()                       # stale: target deleted
            removed.append(entry.name)
        elif entry.name in disqualified:
            entry.unlink()                       # out of scope for this project now
            removed.append(entry.name)

    merge_memory_md(project_memory_dir / "MEMORY.md")

    # Summary
    project_name = project_path.name
    print(f"[{project_name}] created={len(created)} relinked={len(relinked)} "
          f"kept={len(kept)} removed={len(removed)} collisions={len(collisions)}")
    if collisions:
        print(f"[{project_name}] collisions (real files left untouched): "
              f"{', '.join(collisions)}", file=sys.stderr)
        return 1
    return 0


def merge_memory_md(memory_md: Path) -> None:
    """Rewrite the project's MEMORY.md so its global-inherited section matches
    the current global MEMORY.md. Preserves all content outside the markers."""
    if memory_md.exists():
        content = memory_md.read_text()
    else:
        content = "# Memory Index\n\n"

    # Strip any existing auto-managed block
    pattern = re.compile(
        rf"\n*{re.escape(MEMORY_BEGIN)}.*?{re.escape(MEMORY_END)}\n*",
        re.DOTALL,
    )
    content = pattern.sub("\n", content)

    sections = parse_sections(MEMORY_INDEX_SOURCE.read_text()) if MEMORY_INDEX_SOURCE.is_file() else {}

    block_lines: list[str] = [MEMORY_BEGIN, ""]
    for heading, bullets in sections.items():
        block_lines.append(f"## {heading} (inherited from ~)")
        block_lines.append("")
        block_lines.extend(bullets)
        block_lines.append("")
    block_lines.append(MEMORY_END)
    block = "\n".join(block_lines)

    new = content.rstrip() + "\n\n" + block + "\n"
    memory_md.write_text(new)


def parse_sections(md: str) -> dict[str, list[str]]:
    """Parse `## Heading\\n<bullets>` sections. Returns an ordered dict
    (insertion-ordered in py3.7+) of heading → list of non-blank lines."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in md.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None and line.strip():
            sections[current].append(line)
    return sections


if __name__ == "__main__":
    sys.exit(main())
