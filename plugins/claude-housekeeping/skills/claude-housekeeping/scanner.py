#!/usr/bin/env python3
"""
housekeeping scanner — read ~/.claude/projects.json, scan global + per-project
Claude artifacts (memories, hooks, commands, plans, settings.json), emit a
numbered recommendation list grouped by category + executable command blocks +
state-visualization table + mermaid graphs.

Standard library only. Python ≥ 3.10.

Usage:
    scanner.py --report-only [--threshold-days=7] [--include-dormant]
    scanner.py --diff before=<path> after=<path>     # before/after delta report

Output: a single markdown report written to
~/.claude/housekeeping/reports/YYYY-MM-DD-HHMM[-tag].md, with the path printed
on stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

HOME = Path(os.path.expanduser("~"))
GLOBAL_CLAUDE = HOME / ".claude"
PROJECTS_JSON = GLOBAL_CLAUDE / "projects.json"
REPORTS_DIR = GLOBAL_CLAUDE / "housekeeping" / "reports"
PLANS_DIR = GLOBAL_CLAUDE / "plans"

# Categories, in the order they appear in the report
CATEGORIES_ORDER = [
    ("global-hooks",   "Global hook chain"),
    ("missing-settings", "Projects without `.claude/settings.json`"),
    ("config-drift",   "Config drift (per-project duplicates global)"),
    ("broken-hook-paths", "Hook commands referencing missing scripts"),
    ("uncommitted",    "Uncommitted/untracked `.claude/` changes"),
    ("orphan-plans",   "Orphan plans in `~/.claude/plans/`"),
    ("dup-memories",   "Cross-project duplicate memories"),
    ("missing-cascade","Missing global memory cascade"),
    ("leaked-project-memories", "Project-scope memories in a global dir"),
    ("dup-commands",   "Cross-project duplicate commands"),
    ("skill-frontmatter", "Skills with missing required frontmatter fields"),
    ("missing-md-history", "Durable docs missing HISTORY.md sidecar"),
]
CATEGORY_DESC = dict(CATEGORIES_ORDER)
CATEGORY_RANK = {k: i for i, (k, _) in enumerate(CATEGORIES_ORDER)}

# Per-category column headers for the consolidated-table rendering.
# A category with an entry here gets rendered as one table per category.
# A category without an entry falls back to per-recommendation prose (rare).
CATEGORY_COLUMNS: dict[str, list[str]] = {
    "missing-settings":  ["#", "Project"],
    "config-drift":      ["#", "Project", "Duplicate hooks"],
    "broken-hook-paths": ["#", "Scope", "Event", "Hook command", "Resolves to"],
    "uncommitted":       ["#", "Scope", "Status", "File"],
    "orphan-plans":      ["#", "File", "Size", "Age", "Action"],
    "dup-memories":      ["#", "Memory", "Projects (≥3)", "Action"],
    "missing-cascade":   ["#", "Project", "Missing", "Stale", "Collisions"],
    "leaked-project-memories": ["#", "Memory", "Found in", "Recommended destination"],
    "dup-commands":      ["#", "Command", "Projects", "Action"],
    "skill-frontmatter": ["#", "Skill", "Missing"],
    "missing-md-history": ["#", "Project", "Missing total", "Breakdown"],
}

# A short note rendered below each category's table explaining the path pattern
# for items in that category (so we don't repeat the same path in every row).
CATEGORY_PATH_PATTERNS: dict[str, str] = {
    "missing-settings":  "Stub path: `~/SRC/<project>/.claude/settings.json`",
    "config-drift":      "Project settings: `~/SRC/<project>/.claude/settings.json`",
    "broken-hook-paths": "Scope `~` = global `~/.claude/settings.json`; other scopes = `~/SRC/<project>/.claude/settings.json`. Resolves-to column shows the path after expanding `$HOME`, `${SRC_ROOT:-…}`, `$CLAUDE_PROJECT_DIR`.",
    "uncommitted":       "Scope `~` = homedir git repo (covers global `~/.claude/`); other scopes = each project's repo (covers `~/SRC/<project>/.claude/`). Run `cd <scope> && git status -- .claude/` to inspect.",
    "orphan-plans":      "Source: `~/.claude/plans/<file>`",
    "dup-memories":      "Per-project: `~/SRC/<project>/.claude/memory/<name>` — promote to `~/.claude/memory/<name>`",
    "missing-cascade":   "Globals at `~/.claude/projects/-home-will/memory/<name>` → symlinks at `~/SRC/<project>/.claude/memory/<name>`. Apply via the recommendation's command block.",
    "leaked-project-memories": "Source: `~/.claude/memory/<name>` or `~/.claude/projects/-home-will/memory/<name>`. Destination: `~/SRC/<owner>/.claude/memory/<name>` as a real file (not a cascade symlink).",
    "dup-commands":      "Per-project: `~/SRC/<project>/.claude/commands/<name>` — global at `~/.claude/commands/<name>`",
    "skill-frontmatter": "Global skills: `~/.claude/skills/<name>/SKILL.md`. Project-scope: `~/SRC/<project>/.claude/skills/<name>/SKILL.md`.",
    "missing-md-history": "Per project. Scans `docs/plans/*.md`, `docs/investigations/*.md`, `CLAUDE.md`, `README.md`. Excludes HISTORY/MEMORY/TODO/memory-visualization basenames. Run `~/SRC/python-tui-lib/scripts/regen-md-history.sh <file>` per item, or use the command block to bulk-fix a project.",
}

# One-line description of what each scan looks for — surfaced in the
# "What we scanned for" section of every report.
SCAN_DESCRIPTIONS: dict[str, str] = {
    "global-hooks":      "Global ~/.claude/settings.json has the expected baseline hooks (transcript-logger, plan-first, plan-migrate, md-preview, etc.)",
    "missing-settings":  "Active projects without their own `.claude/settings.json` (they get the global chain, but can't add their own hooks).",
    "config-drift":      "Per-project settings.json entries that duplicate hooks already fired globally.",
    "broken-hook-paths": "Hook commands in global or per-project settings.json whose referenced `.sh` script doesn't exist on disk after env-var expansion — catches stale paths left after refactors or env-var typos.",
    "uncommitted":       "Modified or untracked Claude artifacts (skills, commands, memory, hooks, settings) sitting uncommitted in the homedir repo or any project repo — surfaces in-flight work that didn't get a commit.",
    "orphan-plans":      "Markdown files in `~/.claude/plans/` older than the threshold (default 1 day) that look like real plans worth routing.",
    "dup-memories":      "Same-filename `feedback_*.md` across ≥3 real project memory dirs (worktrees excluded) — candidates for promotion to global.",
    "missing-cascade":   "Per active project: global memory files at `~/.claude/projects/-home-will/memory/` not yet symlinked into the project's `.claude/memory/`. Also flags stale symlinks (target gone) and real-file collisions.",
    "leaked-project-memories": "Files matching `project_*.md` or `reference_*.md` (the project-scope naming convention) found in a global memory dir. They should live in their owning project's `.claude/memory/` as a real file, not in global.",
    "dup-commands":      "Commands at `~/.claude/commands/*.md` that also appear in real project dirs (worktrees excluded).",
    "skill-frontmatter": "SKILL.md files missing YAML frontmatter, or whose frontmatter is missing any of name/description/version. Catches skills that slipped in before formalization.",
    "missing-md-history": "Durable markdown docs (plans, investigations, CLAUDE.md, README.md) without a sibling `HISTORY.md`. The pre-commit hook seeds them on next edit; this scan lets you bulk-fix dormant docs on demand.",
}

SEVERITY_RANK = {"regress": 0, "warn": 1, "info": 2}


# ─── data model ────────────────────────────────────────────────────────


@dataclass
class Project:
    name: str
    path: Path
    status: str            # "active" | "dormant"
    notes: str = ""
    summary: str = ""

    @property
    def claude_dir(self) -> Path:     return self.path / ".claude"
    @property
    def settings_json(self) -> Path:  return self.claude_dir / "settings.json"
    @property
    def memory_dir(self) -> Path:     return self.claude_dir / "memory"
    @property
    def commands_dir(self) -> Path:   return self.claude_dir / "commands"
    @property
    def skills_dir(self) -> Path:     return self.claude_dir / "skills"
    @property
    def docs_plans_dir(self) -> Path: return self.path / "docs" / "plans"
    @property
    def hook_runner(self) -> Path:    return self.claude_dir / "hook-runner.sh"


@dataclass
class Recommendation:
    category: str               # see CATEGORIES_ORDER
    title: str                  # one-line summary (used in command-block headings + non-tabular fallback)
    details: str                # multi-line markdown (fallback when no row cells)
    command_block: str          # bash to apply (or instructional comment)
    severity: str = "info"      # "info" | "warn" | "regress"
    row: list[str] = field(default_factory=list)   # cells for the category's table (excludes leading "#")


# ─── project list ──────────────────────────────────────────────────────


def load_projects() -> list[Project]:
    """Always returns ALL projects (active + dormant). Filtering happens
    at scan time, not load time, so the visualization table can show every
    project (dormants ghosted) while scans only run on actives."""
    raw = json.loads(PROJECTS_JSON.read_text())
    out = []
    for entry in raw["projects"]:
        p = Project(
            name=entry["name"],
            path=Path(os.path.expanduser(entry["path"])),
            status=entry.get("status", "active"),
            notes=entry.get("notes", ""),
            summary=entry.get("summary", ""),
        )
        out.append(p)
    return out


def active(projects: list[Project]) -> list[Project]:
    return [p for p in projects if p.status != "dormant"]


# ─── helpers ───────────────────────────────────────────────────────────


def _normalize_hook_cmd(cmd: str) -> str:
    """Strip variable preludes so direct-path vs hook-runner.sh forms compare equal.

    The trailing token may be a bare basename (`md-preview.sh`, as in the
    hook-runner form `bash $HOME/.claude/hook-runner.sh md-preview.sh`) or a
    full path (`bash $HOME/python-tui-lib/hooks/md-preview.sh`). Both should
    reduce to `md-preview.sh` so config-drift can detect them as the same
    hook regardless of invocation form.
    """
    m = re.search(r"(\S+\.sh)\s*$", cmd.strip())
    if not m:
        return cmd.strip()
    return Path(m.group(1)).name


def _expand_hook_path(token: str, project: Optional["Project"] = None) -> Optional[str]:
    """Expand env vars in a hook-script path token. Returns None if the
    token contains an unresolved variable reference (i.e. one we can't
    confidently substitute at scan time)."""
    s = token
    # ${VAR:-default} → env value or the literal default string
    s = re.sub(
        r"\$\{(\w+):-([^}]*)\}",
        lambda m: os.environ.get(m.group(1), m.group(2)),
        s,
    )
    # $CLAUDE_PROJECT_DIR is set by Claude Code at hook-fire time. For
    # project-local hooks we know it equals the project's own path.
    if project is not None:
        s = re.sub(r"\$\{?CLAUDE_PROJECT_DIR\}?", str(project.path), s)
    # Standard $VAR / ${VAR}
    s = os.path.expandvars(s)
    if "$" in s:
        return None  # unresolved — don't flag, we'd be guessing
    return s


def sha256_of(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def age_days(mtime: float) -> int:
    return int((datetime.now().timestamp() - mtime) / 86400)


def pluralize(n: int, singular: str, plural: Optional[str] = None) -> str:
    plural = plural or f"{singular}s"
    return f"{n} {singular if n == 1 else plural}"


def is_worktree_path(p: Path) -> bool:
    return ".worktrees" in p.parts


# Atomic-token formatters (per ~/SRC/CLAUDE.md: NBSP between number+unit;
# U+2011 non-breaking hyphen in dates / hyphenated identifiers)
NBSP = " "
NBHY = "‑"


def fmt_age_days(days: int) -> str:
    return f"{days}{NBSP}d"


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n}{NBSP}B"
    if n < 1024 * 1024:
        return f"{n // 1024}{NBSP}kB"
    return f"{n // (1024 * 1024)}{NBSP}MB"


def fmt_date_iso(s: str) -> str:
    """Replace regular hyphens with non-breaking hyphens in an ISO date."""
    return s.replace("-", NBHY)


def discover_repo_url(project_path: Path) -> Optional[str]:
    """Run `git remote get-url origin` and normalize to https://github.com/<owner>/<repo>.
    Returns None if not a git repo, no origin, or git unavailable."""
    if not project_path.is_dir():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=2,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    if not url:
        return None
    # SSH form → HTTPS web form
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.split(":", 1)[1]
    if url.endswith(".git"):
        url = url[:-4]
    return url


# ─── scans ─────────────────────────────────────────────────────────────


def scan_global_hooks_sanity() -> list[Recommendation]:
    """Global ~/.claude/settings.json should have the expected baseline hooks."""
    global_settings = GLOBAL_CLAUDE / "settings.json"
    if not global_settings.is_file():
        return [Recommendation(
            category="global-hooks",
            title="Global ~/.claude/settings.json missing",
            details="No global hook chain exists. See plan Parts A, D, E.",
            command_block=(
                "# Create ~/.claude/settings.json per the plan's Part A wiring.\n"
                "# Reference: ~/SRC/docs/plans/2026-05-19-globalize-hooks-housekeeping-skill.md"
            ),
            severity="regress",
        )]

    try:
        cfg = json.loads(global_settings.read_text())
    except Exception as e:
        return [Recommendation(
            category="global-hooks",
            title="Global settings.json is unparseable JSON",
            details=f"Error: `{e}`",
            command_block=f"# Hand-fix {global_settings} — it's not valid JSON.",
            severity="regress",
        )]

    expected = {
        "UserPromptSubmit": ["transcript-logger.sh"],
        "PreToolUse":       ["plan-first.sh", "commit-checklist.sh", "tf-blocker.sh"],
        "PostToolUse":      ["plan-migrate.sh", "md-preview.sh"],
        "Stop":             ["todo-reminder.sh"],
    }

    found: set[str] = set()
    for event, blocks in (cfg.get("hooks") or {}).items():
        for block in blocks:
            for hook in block.get("hooks") or []:
                found.add(_normalize_hook_cmd(hook.get("command", "")))

    # Build a full row for each expected hook with present/missing status.
    all_expected = [(event, name) for event, names in expected.items() for name in names]
    status_rows = []
    for event, name in all_expected:
        is_present = any(name in c for c in found)
        status_rows.append((event, name, "✓" if is_present else "✗"))

    missing_count = sum(1 for _, _, s in status_rows if s == "✗")
    if missing_count == 0:
        return []

    def _marker(s: str) -> str:
        return "✅" if s == "✓" else "❌"
    table = "| Event | Hook | Present |\n|---|---|---|\n" + \
            "\n".join(f"| `{e}` | `{n}` | {_marker(s)} |" for e, n, s in status_rows)
    return [Recommendation(
        category="global-hooks",
        title=f"Baseline hooks: {missing_count} of {len(all_expected)} missing",
        details=(
            f"{table}\n\n"
            "**Runbook**: [`~/.claude/skills/claude-housekeeping/runbooks/global-hooks-baseline.md`]"
            "(file:///home/will/.claude/skills/claude-housekeeping/runbooks/global-hooks-baseline.md) — "
            "copy-paste-ready JSON snippet, merge instructions, validation steps, rollback."
        ),
        command_block=(
            "# See the runbook for the exact JSON to merge:\n"
            "#   cat $HOME/.claude/skills/claude-housekeeping/runbooks/global-hooks-baseline.md\n"
            "#   (or: task md -- $HOME/.claude/skills/claude-housekeeping/runbooks/global-hooks-baseline.md)\n"
            "#\n"
            "# Backup → edit → validate, all per runbook:\n"
            "cp -a $HOME/.claude/settings.json /tmp/settings.json.bak-$(date +%Y%m%d-%H%M)\n"
            "${EDITOR:-vi} $HOME/.claude/settings.json\n"
            "jq . $HOME/.claude/settings.json > /dev/null && echo 'valid JSON'"
        ),
        severity="warn",
    )]


def scan_missing_project_settings(projects: list[Project]) -> list[Recommendation]:
    """Active projects without .claude/settings.json — won't get the global hook chain bonuses
       (well, technically global fires regardless — but project-specific hooks have no home)."""
    recs = []
    for p in projects:
        if p.settings_json.is_file():
            continue
        if not p.path.is_dir():
            continue
        # Has the project ever started using Claude artifacts at all?
        has_any = (p.memory_dir.exists() or p.commands_dir.exists() or
                   p.skills_dir.exists() or p.docs_plans_dir.exists())
        if not has_any:
            continue  # genuinely empty — leave alone

        recs.append(Recommendation(
            category="missing-settings",
            title=f"{p.name}: no .claude/settings.json yet",
            details="",  # rendered as a row in the consolidated table
            row=[p.name],
            command_block=(
                f"# Create a stub settings.json for {p.name}\n"
                f"mkdir -p {p.claude_dir}\n"
                f'cat > {p.settings_json} <<\'EOF\'\n'
                "{\n"
                '  "hooks": {}\n'
                "}\n"
                "EOF\n"
                f"# Verify\n"
                f"jq . {p.settings_json}"
            ),
        ))
    return recs


def scan_orphan_plans(threshold_days: int) -> list[Recommendation]:
    """Plans in ~/.claude/plans/*.md older than threshold."""
    if not PLANS_DIR.is_dir():
        return []
    cutoff = datetime.now().timestamp() - (threshold_days * 86400)
    recs = []
    for md in sorted(PLANS_DIR.glob("*.md")):
        st = md.stat()
        if st.st_mtime > cutoff:
            continue
        if st.st_size < 200:
            recs.append(Recommendation(
                category="orphan-plans",
                title=f"Delete trivial scratch plan {md.name}",
                details="",
                row=[md.name, fmt_bytes(st.st_size), fmt_age_days(age_days(st.st_mtime)), "delete (trivial)"],
                command_block=cmd_block_delete(md),
            ))
            continue
        recs.append(Recommendation(
            category="orphan-plans",
            title=f"Route {md.name}",
            details="",
            row=[md.name, fmt_bytes(st.st_size), fmt_age_days(age_days(st.st_mtime)), "route to docs/plans/"],
            command_block=cmd_block_route_plan_manual(md),
        ))
    return recs


def scan_duplicate_memories(projects: list[Project]) -> list[Recommendation]:
    """Same-filename feedback_*.md across ≥3 real (non-worktree) project memory dirs."""
    by_name: dict[str, list[tuple[Project, Path]]] = defaultdict(list)
    for p in projects:
        if not p.memory_dir.is_dir():
            continue
        for f in p.memory_dir.glob("feedback_*.md"):
            if is_worktree_path(f):
                continue
            # Skip cascade symlinks — they're already global, not per-project copies.
            # Accept resolve() ending at either the current or legacy global dir, so
            # not-yet-migrated absolute symlinks still get correctly excluded.
            if f.is_symlink():
                try:
                    resolved_parent = f.resolve().parent.resolve()
                except OSError:
                    resolved_parent = None
                if resolved_parent in (
                    GLOBAL_USER_MEMORY_DIR.resolve(),
                    LEGACY_GLOBAL_USER_MEMORY_DIR.resolve(),
                ):
                    continue
            by_name[f.name].append((p, f))

    recs = []
    for name, locations in sorted(by_name.items()):
        if len(locations) < 3:
            continue
        proj_names = ", ".join(p.name for p, _ in locations)
        hashes = {sha256_of(f) for _, f in locations}
        same = len(hashes) == 1
        recs.append(Recommendation(
            category="dup-memories",
            title=f"Promote {name} to global",
            details="",
            row=[f"`{name}`", proj_names, "✅ safe to promote" if same else "**❌ review diffs first**"],
            command_block=cmd_block_promote_memory(name, locations, content_identical=same),
            severity="warn" if not same else "info",
        ))
    return recs


GLOBAL_USER_MEMORY_DIR = GLOBAL_CLAUDE / "memory"
# Legacy path retained for stale-symlink detection across not-yet-migrated projects.
LEGACY_GLOBAL_USER_MEMORY_DIR = GLOBAL_CLAUDE / "projects" / "-home-will" / "memory"
CASCADE_EXCLUDED_NAMES = {"MEMORY.md", "memory-visualization.md"}


def _global_cascade_sources() -> list[Path]:
    if not GLOBAL_USER_MEMORY_DIR.is_dir():
        return []
    return sorted(
        f for f in GLOBAL_USER_MEMORY_DIR.glob("*.md")
        if f.name not in CASCADE_EXCLUDED_NAMES
    )


def _classify_cascade_state(project: Project, sources: list[Path]) -> tuple[list[str], list[str], list[str]]:
    """Return (missing, stale, collisions) filenames for one project.
    - missing: a source exists but the project has no entry of that name
    - stale: project has a symlink into the global memory dir whose target is gone
    - collisions: project has a real (non-symlink) file with the same name as a source
    """
    missing: list[str] = []
    collisions: list[str] = []
    mem_dir = project.memory_dir

    if mem_dir.is_dir():
        source_names = {s.name for s in sources}
        for src in sources:
            target = mem_dir / src.name
            if target.is_symlink():
                try:
                    if target.resolve() == src.resolve():
                        continue
                except OSError:
                    pass
                missing.append(src.name)
            elif target.exists():
                collisions.append(src.name)
            else:
                missing.append(src.name)
        stale = _find_stale_cascade_symlinks(mem_dir)
    else:
        # Memory dir doesn't exist yet — every source is "missing"
        missing = [s.name for s in sources]
        stale = []

    return missing, stale, collisions


def _find_stale_cascade_symlinks(mem_dir: Path) -> list[str]:
    stale: list[str] = []
    global_str = str(GLOBAL_USER_MEMORY_DIR)
    if not mem_dir.is_dir():
        return stale
    for entry in mem_dir.iterdir():
        if not entry.is_symlink():
            continue
        try:
            link_target = os.readlink(entry)
        except OSError:
            continue
        if not link_target.startswith(global_str):
            continue
        if not Path(link_target).exists():
            stale.append(entry.name)
    return stale


def scan_missing_global_cascade(projects: list[Project]) -> list[Recommendation]:
    """Per active project, detect global memories not yet symlinked in,
    stale symlinks pointing into a deleted global file, and real-file
    collisions. Emit one recommendation per affected project."""
    sources = _global_cascade_sources()
    if not sources:
        return []

    recs = []
    for p in projects:
        missing, stale, collisions = _classify_cascade_state(p, sources)
        if not (missing or stale or collisions):
            continue
        collisions_cell = f"**{len(collisions)}**" if collisions else "—"
        details_extra = ""
        if collisions:
            details_extra = ("\nCollisions (real local files with same name as a global memory — "
                             "the recommendation will skip these): "
                             + ", ".join(f"`{n}`" for n in collisions))
        recs.append(Recommendation(
            category="missing-cascade",
            title=f"Cascade {len(missing)} global memories into {p.name}",
            details=(f"Project `.claude/memory/` will gain {len(missing)} symlink(s) into "
                     f"`{GLOBAL_USER_MEMORY_DIR}/`. {len(stale)} stale symlink(s) will be removed."
                     + details_extra),
            row=[p.name, str(len(missing)), str(len(stale)) if stale else "—", collisions_cell],
            command_block=cmd_block_cascade_globals(p, missing, stale, collisions),
            severity="warn" if collisions else "info",
        ))
    return recs


def _guess_owner_project(filename: str, projects: list[Project]) -> Optional[str]:
    """Heuristic: from a `project_*.md` / `reference_*.md` filename, find the
    one active project whose normalized name appears in the rest of the
    filename. Returns None unless exactly one project matches."""
    stem = filename
    if stem.endswith(".md"):
        stem = stem[:-3]
    for prefix in ("project_", "reference_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
            break
    needle = stem.replace("_", "").replace("-", "").lower()
    candidates = []
    for p in projects:
        normalized = p.name.replace(".", "").replace("-", "").replace("_", "").lower()
        if normalized and normalized in needle:
            candidates.append(p.name)
    return candidates[0] if len(candidates) == 1 else None


def scan_leaked_project_memories(projects: list[Project]) -> list[Recommendation]:
    """Project-scope memories (`project_*.md`, `reference_*.md`) sitting in a
    global memory dir instead of the named project's `.claude/memory/`.

    Per the naming-convention principle (see plan
    2026-05-21-migrate-global-memory-canonical.md Phase 1), these prefixes
    mark memories that should live in `~/SRC/<project>/.claude/memory/` as
    real files, not in `~/.claude/memory/` or the cwd=~ auto-memory dir.

    Skips symlinks — those are legitimate cascade artifacts."""
    recs: list[Recommendation] = []
    targets = [
        ("global canonical", GLOBAL_USER_MEMORY_DIR),
        ("cwd=~ auto-memory", LEGACY_GLOBAL_USER_MEMORY_DIR),
    ]
    for label, dir_path in targets:
        if not dir_path.is_dir():
            continue
        for f in sorted(dir_path.iterdir()):
            if f.is_symlink() or not f.is_file():
                continue
            if not (f.name.startswith("project_") or f.name.startswith("reference_")):
                continue
            owner = _guess_owner_project(f.name, projects)
            dest_cell = (
                f"→ ~/SRC/{owner}/.claude/memory/"
                if owner else "→ owner unclear; inspect manually"
            )
            recs.append(Recommendation(
                category="leaked-project-memories",
                title=f"Relocate {f.name} out of {label}",
                details="",
                row=[f"`{f.name}`", label, dest_cell],
                command_block=cmd_block_relocate_project_memory(f, owner),
                severity="warn",
            ))
    return recs


# Basenames excluded from missing-md-history scan: same set the pre-commit
# hook excludes (avoids recursion / churn / auto-generated files).
_MD_HISTORY_EXCLUDED_BASENAMES = {
    "HISTORY.md", "MEMORY.md", "TODO.md", "memory-visualization.md",
}
# Path substrings that mark ephemeral / non-source-tree / vendored dirs.
# Anything matching these gets skipped — including the rglob walk for
# README.md/CLAUDE.md (the dominant noise source — vendored third-party
# READMEs under from-dreamhost/, wp-content/, vendor/, etc.).
_MD_HISTORY_EXCLUDED_PATH_SUBSTRINGS = (
    "/node_modules/", "/.worktrees/", "/.cache/", "/.git/",
    "/.pytest_cache/", "/target/", "/build/", "/dist/", "/tmp/",
    "/__pycache__/", "/.pub-cache/",
    "/from-dreamhost/",   # biohack.net imported third-party dump
    "/vendor/",           # generic vendored code
    "/wp-content/",       # WordPress imports
    "/site-packages/",    # Python venv contents
    "/.history/",         # don't recursively scan our own sidecar dir
)
# CLAUDE.md/README.md beyond this depth from the project root are almost
# always vendored (e.g. `tools/foo/bar/baz/README.md`). Project-level docs
# and major-subdir docs live at depth <= 3.
_MD_HISTORY_MAX_DEPTH = 3


def _git_tracked_files(repo: Path) -> Optional[set[str]]:
    """Return the set of repo-relative paths git tracks in this repo,
    or None if the path isn't a git repo (or git is unavailable). Used to
    filter out untracked files from the missing-md-history scan — regen
    can't produce a HISTORY.md for a file with no commits."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "ls-files"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return set(result.stdout.splitlines())


def _iter_durable_md_for_project(p: Project):
    """Yield durable-doc markdown paths under project p. Mirrors the
    pre-commit hook's INCLUDE_RE scope, plus path-substring + depth filters
    (no vendored third-party READMEs) and a tracked-only filter (untracked
    files have no git history — regen would skip them anyway)."""
    if not p.path.is_dir():
        return
    tracked = _git_tracked_files(p.path)
    if tracked is None:
        return  # not a git repo, or git failed — scan is meaningless here

    def is_tracked(f: Path) -> bool:
        try:
            return str(f.relative_to(p.path)) in tracked
        except ValueError:
            return False

    # docs/plans and docs/investigations: single-level glob
    for sub in ("docs/plans", "docs/investigations"):
        sub_dir = p.path / sub
        if sub_dir.is_dir():
            for f in sub_dir.glob("*.md"):
                if f.name in _MD_HISTORY_EXCLUDED_BASENAMES:
                    continue
                if not is_tracked(f):
                    continue
                yield ("plans" if sub == "docs/plans" else "investigations", f)
    # CLAUDE.md and README.md: recursive, bounded by exclusion list + depth.
    for name in ("CLAUDE.md", "README.md"):
        for f in p.path.rglob(name):
            s = str(f)
            if any(seg in s for seg in _MD_HISTORY_EXCLUDED_PATH_SUBSTRINGS):
                continue
            # Depth from project root (excluding the filename itself)
            try:
                depth = len(f.relative_to(p.path).parts) - 1
            except ValueError:
                depth = _MD_HISTORY_MAX_DEPTH + 1  # outside project, skip
            if depth > _MD_HISTORY_MAX_DEPTH:
                continue
            if not is_tracked(f):
                continue
            yield (name, f)


def scan_missing_md_history(projects: list[Project]) -> list[Recommendation]:
    """Per project: durable-doc markdown files (plans, investigations, CLAUDE.md,
    README.md) without a sibling HISTORY.md. The pre-commit hook seeds these on
    next edit; this scan lets the user bulk-fix dormant docs on demand.

    Aggregated to one rec per project — flagging individual files would
    explode the report on projects with hundreds of plans."""
    recs: list[Recommendation] = []
    for p in projects:
        missing_by_kind: dict[str, list[Path]] = defaultdict(list)
        for kind, f in _iter_durable_md_for_project(p):
            # Per-file sidecar at <dir>/.history/<basename>. Legacy
            # <dir>/HISTORY.md sibling is migration leftover — not counted
            # here (the new convention is per-file, so a sibling HISTORY.md
            # doesn't satisfy this file).
            sidecar = f.parent / ".history" / f.name
            if sidecar.exists():
                continue
            missing_by_kind[kind].append(f)
        total = sum(len(v) for v in missing_by_kind.values())
        if total == 0:
            continue
        breakdown = ", ".join(
            f"{len(v)} {k}" for k, v in missing_by_kind.items() if v
        )
        recs.append(Recommendation(
            category="missing-md-history",
            title=f"{p.name}: {total} durable doc(s) missing HISTORY.md sidecar",
            details="",
            row=[p.name, str(total), breakdown],
            command_block=cmd_block_seed_md_history(p, missing_by_kind),
            severity="info",
        ))
    return recs


def scan_duplicate_commands(projects: list[Project]) -> list[Recommendation]:
    """Commands at ~/.claude/commands/*.md that ALSO appear in real project dirs (no worktrees)."""
    global_cmds_dir = GLOBAL_CLAUDE / "commands"
    if not global_cmds_dir.is_dir():
        return []
    recs = []
    for global_md in sorted(global_cmds_dir.glob("*.md")):
        name = global_md.name
        duplicates: list[Path] = []
        for p in projects:
            cmd = p.commands_dir / name
            if cmd.is_file() and not is_worktree_path(cmd):
                duplicates.append(cmd)
        if not duplicates:
            continue
        global_hash = sha256_of(global_md)
        identical = all(sha256_of(d) == global_hash for d in duplicates)
        proj_paths = ", ".join(d.parts[-4] for d in duplicates)  # just project names
        n_dups = len(duplicates)
        recs.append(Recommendation(
            category="dup-commands",
            title=f"Remove project copies of {name}",
            details="",
            row=[f"`{name}`", proj_paths, "✅ safe to delete" if identical else "**❌ review diff first**"],
            command_block=cmd_block_remove_dup_commands(name, global_md, duplicates, identical),
            severity="info" if identical else "warn",
        ))
    return recs


def _parse_skill_frontmatter_keys(text: str) -> Optional[set[str]]:
    """Return the set of top-level YAML keys in a SKILL.md's frontmatter,
    or None if there's no frontmatter block at all. Nested keys are ignored
    (we only need to verify the top-level shape)."""
    if not text.startswith("---\n"):
        return None
    m = re.match(r"\A---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    keys: set[str] = set()
    for line in m.group(1).splitlines():
        if not line or line.startswith((" ", "\t")):
            continue
        km = re.match(r"^([\w-]+)\s*:", line)
        if km:
            keys.add(km.group(1))
    return keys


def scan_skill_frontmatter(projects: list[Project]) -> list[Recommendation]:
    """SKILL.md files missing YAML frontmatter, or missing any of
    name/description/version. Walks global ~/.claude/skills/ plus each
    active project's .claude/skills/."""
    required = ("name", "description", "version")
    recs: list[Recommendation] = []

    skill_paths: list[tuple[str, Path]] = []
    global_skills = GLOBAL_CLAUDE / "skills"
    if global_skills.is_dir():
        for s in sorted(global_skills.glob("*/SKILL.md")):
            if is_worktree_path(s):
                continue
            skill_paths.append(("~", s))
    for p in projects:
        if p.skills_dir.is_dir():
            for s in sorted(p.skills_dir.glob("*/SKILL.md")):
                if is_worktree_path(s):
                    continue
                skill_paths.append((p.name, s))

    for scope_label, path in skill_paths:
        try:
            text = path.read_text()
        except OSError:
            continue
        keys = _parse_skill_frontmatter_keys(text)
        if keys is None:
            missing = list(required)
        else:
            missing = [k for k in required if k not in keys]
        if not missing:
            continue
        skill_name = path.parent.name
        recs.append(Recommendation(
            category="skill-frontmatter",
            title=f"Add {', '.join(missing)} to {scope_label}:{skill_name}/SKILL.md",
            details="",
            row=[f"{scope_label}:`{skill_name}`", ", ".join(f"`{k}`" for k in missing)],
            command_block=cmd_block_fix_skill_frontmatter(path, skill_name, missing),
            severity="warn",
        ))
    return recs


def scan_config_drift(projects: list[Project]) -> list[Recommendation]:
    """Project settings.json hook entries that duplicate the global settings.json."""
    global_settings = GLOBAL_CLAUDE / "settings.json"
    if not global_settings.is_file():
        return []
    try:
        global_cfg = json.loads(global_settings.read_text())
    except Exception:
        return []

    global_hook_cmds: set[str] = set()
    for event, blocks in (global_cfg.get("hooks") or {}).items():
        for block in blocks:
            for hook in block.get("hooks") or []:
                cmd = hook.get("command", "")
                if cmd:
                    global_hook_cmds.add(_normalize_hook_cmd(cmd))

    recs = []
    for p in projects:
        if not p.settings_json.is_file():
            continue
        try:
            cfg = json.loads(p.settings_json.read_text())
        except Exception:
            continue
        dup_lines = []
        for event, blocks in (cfg.get("hooks") or {}).items():
            for block in blocks:
                for hook in block.get("hooks") or []:
                    cmd = hook.get("command", "")
                    if _normalize_hook_cmd(cmd) in global_hook_cmds:
                        dup_lines.append((event, cmd))
        if not dup_lines:
            continue
        hook_summary = ", ".join(_normalize_hook_cmd(c) for _, c in dup_lines)
        recs.append(Recommendation(
            category="config-drift",
            title=f"{p.name}: {pluralize(len(dup_lines), 'hook')} duplicate global",
            details="",
            row=[p.name, f"{len(dup_lines)}× — {hook_summary}"],
            command_block=cmd_block_trim_settings(p, dup_lines),
        ))
    return recs


def scan_broken_hook_paths(projects: list[Project]) -> list[Recommendation]:
    """Hook commands in global/per-project settings.json whose referenced
    .sh script doesn't exist on disk after env-var expansion.

    Logic: for each settings.json, walk every hook command, extract any
    whitespace-separated `.sh` tokens that contain `/` (so the bare
    `md-preview.sh` arg to `hook-runner.sh` is skipped — that arg is
    resolved internally by the runner, not as a filesystem path),
    expand env vars, and flag tokens that resolve to a missing file.
    Tokens with unresolved vars after expansion are skipped (we'd be
    guessing)."""
    recs: list[Recommendation] = []
    targets: list[tuple[str, Path, Optional[Project]]] = []
    global_settings = GLOBAL_CLAUDE / "settings.json"
    if global_settings.is_file():
        targets.append(("~", global_settings, None))
    for p in projects:
        if p.settings_json.is_file():
            targets.append((p.name, p.settings_json, p))

    for scope_label, settings_path, project in targets:
        try:
            cfg = json.loads(settings_path.read_text())
        except Exception:
            continue
        for event, blocks in (cfg.get("hooks") or {}).items():
            for block in blocks:
                for hook in block.get("hooks") or []:
                    cmd = hook.get("command", "")
                    if not cmd:
                        continue
                    for tok in re.findall(r"\S+\.sh", cmd):
                        if "/" not in tok:
                            continue  # bare arg name (e.g. hook-runner.sh's arg)
                        expanded = _expand_hook_path(tok, project)
                        if expanded is None:
                            continue  # unresolved var refs — skip
                        if Path(expanded).is_file():
                            continue  # exists
                        recs.append(Recommendation(
                            category="broken-hook-paths",
                            title=f"{scope_label}: hook references missing `{Path(expanded).name}`",
                            details="",
                            row=[scope_label, event, f"`{cmd}`", f"`{expanded}`"],
                            command_block=cmd_block_fix_broken_hook(
                                scope_label, settings_path, event, cmd, expanded,
                            ),
                            severity="warn",
                        ))
    return recs


# Patterns considered "real artifacts" vs ephemeral cache/session/log dirs.
# Substring match against the path's slash-form relative-to-repo string.
RELEVANT_CLAUDE_SUBPATHS = (
    "/skills/",
    "/commands/",
    "/memory/",
    "/hooks/",
    "/settings.json",
    "/settings.local.json",
    "/CLAUDE.md",
)

EPHEMERAL_CLAUDE_SUBPATHS = (
    "/__pycache__/",
    "/housekeeping/reports/",   # the scanner's own output
    "/sessions/",
    "/cache/",
    "/daemon/",
    "/backups/",
    "/file-history/",
    "/image-cache/",
    "/paste-cache/",
    "/shell-snapshots/",
    "/statsig/",
    "/telemetry/",
    "/tab-status/",
    "/usage-data/",
    "/debug/",
    "/jobs/",
    "/tasks/",
    "/todos/",
    "/plugins/",
    "/.last-cleanup",
    "/stats-cache.json",
    "/history.jsonl",
    "/daemon.log",
    "/mcp-needs-auth-cache.json",
)


def _is_relevant_claude_change(rel_path: str) -> bool:
    """True if a git-status path under `.claude/` represents a real artifact
    (skill/command/memory/hook/settings/CLAUDE.md) worth surfacing.
    False for ephemeral cache/session/log entries, backups, and tilde-files.
    Auto-memory under `.claude/projects/<dir>/memory/` counts; the rest of
    `.claude/projects/` (sessions, etc.) does not."""
    # Backup/temp file suffixes — never artifacts.
    if rel_path.endswith((".bak", ".tmp", "~", ".swp", ".swo")):
        return False
    p = "/" + rel_path  # normalize so leading-segment substring matches work
    for s in EPHEMERAL_CLAUDE_SUBPATHS:
        if s in p:
            return False
    if "/projects/" in p:
        return "/memory/" in p
    return any(s in p for s in RELEVANT_CLAUDE_SUBPATHS)


def _git_status_porcelain(repo: Path, scope: str) -> list[tuple[str, str]]:
    """Run `git status --porcelain -- <scope>` in `repo`.
    Returns list of (status_code, relpath). Returns [] if not a git repo
    or git is unavailable. Renames keep the new path."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain", "--", scope],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    out = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        out.append((code, path))
    return out


def scan_uncommitted_claude_changes(projects: list[Project]) -> list[Recommendation]:
    """Modified or untracked files under `.claude/` in any git-tracked repo.
    Two scopes: homedir repo (covers global `~/.claude/`) and each project's
    own repo (covers `~/SRC/<project>/.claude/`)."""
    recs: list[Recommendation] = []
    scopes: list[tuple[str, Path]] = []
    if (HOME / ".claude").is_dir():
        scopes.append(("~", HOME))
    for p in projects:
        if p.path.is_dir() and p.claude_dir.is_dir():
            scopes.append((p.name, p.path))

    for scope_label, repo_root in scopes:
        for code, rel in _git_status_porcelain(repo_root, ".claude/"):
            if not _is_relevant_claude_change(rel):
                continue
            stripped = code.strip()
            if stripped == "??":
                status = "untracked"
                severity = "info"
            elif "M" in code:
                status = "modified"
                severity = "warn"
            elif "D" in code:
                status = "deleted"
                severity = "warn"
            elif "A" in code:
                status = "added (staged)"
                severity = "info"
            elif "R" in code:
                status = "renamed"
                severity = "info"
            else:
                status = stripped or "?"
                severity = "info"
            recs.append(Recommendation(
                category="uncommitted",
                title=f"{scope_label}: {status} `{rel}`",
                details="",
                row=[scope_label, status, f"`{rel}`"],
                command_block=cmd_block_review_uncommitted(repo_root, rel, status),
                severity=severity,
            ))
    return recs


def cmd_block_review_uncommitted(repo_root: Path, rel_path: str, status: str) -> str:
    full = f"{repo_root}/{rel_path}"
    if status == "untracked":
        return f"""# Untracked under .claude/: {rel_path}
# Inspect — is this a real artifact you want to keep, or scratch?
ls -la '{full}'
[ -f '{full}' ] && head -40 '{full}'

# If keeping → stage + commit in the right repo:
cd '{repo_root}'
git add '{rel_path}'
git commit -m "<topic>: <one-line summary>"

# If scratch → remove:
# rm -r '{full}'"""
    if status == "deleted":
        return f"""# Deleted (not staged): {rel_path}
# If the deletion is intentional → stage and commit:
cd '{repo_root}'
git rm '{rel_path}' 2>/dev/null || git add -u -- '{rel_path}'
git commit -m "<topic>: remove {rel_path}"

# If unintentional → restore:
# git restore -- '{rel_path}'"""
    return f"""# Modified under .claude/: {rel_path}
# Review the diff and decide:
cd '{repo_root}'
git diff -- '{rel_path}'

# If intentional → commit:
git add '{rel_path}'
git commit -m "<topic>: <one-line summary>"

# If unintentional → restore:
# git restore -- '{rel_path}'"""


def scan_stale_verify_todos(projects: list[Project]) -> list[Recommendation]:
    """TODO.md [verify] entries linking to a plan >14 days old."""
    recs = []
    cutoff = datetime.now().timestamp() - (14 * 86400)
    plan_date_re = re.compile(r"(\d{4}-\d{2}-\d{2})")
    for p in projects:
        todo = p.path / "TODO.md"
        if not todo.is_file():
            continue
        try:
            content = todo.read_text(errors="replace")
        except Exception:
            continue
        for ln_no, line in enumerate(content.splitlines(), 1):
            if "[verify]" not in line:
                continue
            m = plan_date_re.search(line)
            if not m:
                continue
            try:
                plan_dt = datetime.strptime(m.group(1), "%Y-%m-%d")
            except ValueError:
                continue
            if plan_dt.timestamp() >= cutoff:
                continue
            age = age_days(plan_dt.timestamp())
            # Tighten the line preview — only the [verify] sentence
            preview = line.strip()
            # Shorter preview for table cell
            short = preview.replace("`", "")
            if len(short) > 80:
                short = short[:77] + "..."
            recs.append(Recommendation(
                category="stale-verify",
                title=f"{p.name} TODO L{ln_no}: stale [verify]",
                details="",
                row=[f"{p.name}/TODO.md:{ln_no}", fmt_date_iso(m.group(1)), fmt_age_days(age), short],
                command_block=(
                    f"# Stale [verify] in {todo}:{ln_no}\n"
                    f"# Open the project and run /verify (no shell equivalent — it's a skill):\n"
                    f"#   cd {p.path}\n"
                    f"#   claude   # then type /verify\n"
                    f"# Or hand-edit the TODO line to push the verification.\n"
                    f"${{EDITOR:-vi}} +{ln_no} '{todo}'"
                ),
            ))
    return recs


# ─── command-block emitters ────────────────────────────────────────────


def cmd_block_delete(path: Path) -> str:
    return f"""# Backup + delete trivial scratch
BACKUP="$BACKUP_ROOT/orphan-{path.stem}"
mkdir -p "$BACKUP"
cp -a '{path}' "$BACKUP/"
test -f "$BACKUP/{path.name}"
rm '{path}'
test ! -e '{path}'
echo "OK: deleted {path.name}"
# Rollback: cp -a "$BACKUP/{path.name}" '{path}'"""


def cmd_block_route_plan_manual(path: Path) -> str:
    return f"""# Route {path.name} to the right project's docs/plans/
# 1) Inspect content to identify the project
head -30 '{path}'
# 2) mv with proper YYYY-MM-DD-<slug>.md naming, e.g.:
#    mv '{path}' ~/SRC/<project>/docs/plans/$(date +%Y-%m-%d -d @$(stat -c %Y '{path}'))-<slug>.md
# Rollback: mv it back to '{path}'"""


def cmd_block_seed_md_history(p: Project, missing_by_kind: dict) -> str:
    """Emit bash that loops over each missing-HISTORY.md file in a project
    and runs regen-md-history.sh against it. The regen script writes
    sidecar HISTORY.md files; user reviews + commits in that project repo."""
    all_files = []
    for kind in ("plans", "investigations", "CLAUDE.md", "README.md"):
        all_files.extend(missing_by_kind.get(kind, []))
    file_args = " \\\n  ".join(f"'{f}'" for f in all_files)
    summary = ", ".join(
        f"{len(missing_by_kind.get(k, []))} {k}"
        for k in ("plans", "investigations", "CLAUDE.md", "README.md")
        if missing_by_kind.get(k)
    )
    return f"""# Seed HISTORY.md sidecars in {p.name}: {summary}
# Calls ~/SRC/python-tui-lib/scripts/regen-md-history.sh per file.
# Files with no git history yet are skipped silently by the regen script.
REGEN="$HOME/SRC/python-tui-lib/scripts/regen-md-history.sh"
test -x "$REGEN"

for f in \\
  {file_args}
do
  bash "$REGEN" "$f"
done

# Review the new HISTORY.md files, then commit in {p.path}:
#   cd '{p.path}'
#   git add **/HISTORY.md
#   git commit -m "chore(history): seed HISTORY.md sidecars"
# Rollback: rm any HISTORY.md files this run created (cd {p.path} && git status to spot them)."""


def cmd_block_relocate_project_memory(f: Path, owner: Optional[str]) -> str:
    """Emit bash to move a leaked project_*.md / reference_*.md out of a
    global memory dir into its owning project's .claude/memory/. If the
    owning project couldn't be guessed, emit a no-op stub that prints the
    file's content for the user to inspect and place manually."""
    if owner:
        dest = f"$HOME/SRC/{owner}/.claude/memory/{f.name}"
        return f"""# Relocate project-scope memory {f.name} to its owning project.
# Source:      {f}
# Destination: {dest}
BACKUP="$BACKUP_ROOT/relocate-{f.stem}"
mkdir -p "$BACKUP"
cp -a '{f}' "$BACKUP/{f.name}"

mkdir -p "$(dirname '{dest}')"
mv '{f}' '{dest}'

test -f '{dest}'
test ! -e '{f}'
echo "OK: moved {f.name} → {dest}"
# Rollback: mv '{dest}' '{f}'"""
    return f"""# {f.name} looks project-scope (per naming convention) but no active
# project's name matches it via the housekeeping heuristic. Inspect the
# content and decide where it belongs, then mv it manually.
head -30 '{f}'
# Suggested action once you've identified the owner:
#   mv '{f}' $HOME/SRC/<project>/.claude/memory/{f.name}"""


def cmd_block_promote_memory(name: str, locations: list[tuple[Project, Path]], content_identical: bool) -> str:
    """Emit bash that promotes a duplicated per-project memory to the global
    canonical and replaces every per-project copy with a relative symlink.

    Critically does NOT delete copies — Claude Code doesn't load memories up
    the directory tree, so each project needs the file present (as a symlink
    to the canonical) to keep loading it."""
    canonical = f"$HOME/.claude/memory/{name}"

    if not content_identical:
        diff_lines = "\n".join(f'  diff "{locations[0][1]}" "{f}"' for _, f in locations[1:])
        return f"""# Copies of {name} DIFFER across projects — inspect before promoting.
{diff_lines}
# Pick canonical version, place at {canonical}, then re-run this recommendation
# (which will then convert each per-project copy to a relative symlink)."""

    cp_lines = "\n".join(f'cp -a "{f}" "$BACKUP/{p.name}.md"' for p, f in locations)
    # For each project copy: rm regular file, then create a RELATIVE symlink
    # using realpath --relative-to so the target text is portable across
    # absolute home dirs (no /home/will/ in the symlink text).
    symlink_lines = "\n".join(
        f'rm "{f}"\n'
        f'ln -s "$(realpath --relative-to="$(dirname \'{f}\')" "{canonical}")" "{f}"'
        for _, f in locations
    )
    symlink_check_lines = "\n".join(
        f'test -L "{f}"\n'
        f'test "$(readlink -f "{f}")" = "$(readlink -f "{canonical}")"'
        for _, f in locations
    )
    return f"""# Promote {name} to {canonical} and convert per-project copies to relative symlinks.
# Each project keeps a SYMLINK so Claude Code at that cwd can still load the memory.
BACKUP="$BACKUP_ROOT/promote-{name}"
mkdir -p "$BACKUP"
{cp_lines}

# Pre-check: backups present
test "$(ls "$BACKUP" | wc -l)" -eq {len(locations)}

# Action 1: seed canonical if missing (identical content across copies confirmed)
mkdir -p "$HOME/.claude/memory"
[ -e "{canonical}" ] || cp -a "$BACKUP/{locations[0][0].name}.md" "{canonical}"

# Action 2: replace each per-project copy with a relative symlink to canonical
{symlink_lines}

# Post-check: canonical exists and every project path now resolves to it
test -f "{canonical}"
{symlink_check_lines}
echo "OK: promoted {name} (canonical + {len(locations)} symlink(s))"
# Rollback: for f in "$BACKUP"/*.md; do project=$(basename "$f" .md); rm "$HOME/SRC/$project/.claude/memory/{name}"; cp -a "$f" "$HOME/SRC/$project/.claude/memory/{name}"; done"""


def cmd_block_cascade_globals(project: Project, missing: list[str], stale: list[str],
                              collisions: list[str]) -> str:
    helper = GLOBAL_CLAUDE / "skills" / "claude-housekeeping" / "apply-cascade.py"
    mem_dir = project.memory_dir
    missing_preview = ", ".join(f"`{n}`" for n in missing[:5])
    if len(missing) > 5:
        missing_preview += f", … (+{len(missing) - 5} more)"
    stale_comment = ""
    if stale:
        stale_comment = f"# Will also remove {len(stale)} stale symlink(s): {', '.join(stale)}\n"
    collisions_comment = ""
    if collisions:
        collisions_comment = (f"# Collisions (real files left untouched): "
                              f"{', '.join(collisions)}\n")
    return f"""# Cascade {len(missing)} global memor{'y' if len(missing) == 1 else 'ies'} into {project.name}
# Will create symlinks for: {missing_preview}
{stale_comment}{collisions_comment}BACKUP="$BACKUP_ROOT/cascade-{project.name}"
mkdir -p "$BACKUP"
if [ -f "{mem_dir}/MEMORY.md" ]; then cp -a "{mem_dir}/MEMORY.md" "$BACKUP/"; fi
if [ -f "{mem_dir}/.gitignore" ]; then cp -a "{mem_dir}/.gitignore" "$BACKUP/"; fi

# Action
python3 "{helper}" "{project.path}"

# Post-check: every expected symlink exists and points into the global memory dir
for name in {' '.join(f'"{n}"' for n in missing)}; do
  test -L "{mem_dir}/$name" || {{ echo "MISSING: {mem_dir}/$name" >&2; exit 1; }}
done
echo "OK: cascaded {len(missing)} memor{'y' if len(missing) == 1 else 'ies'} into {project.name}"
# Rollback: cp -a "$BACKUP/MEMORY.md" "{mem_dir}/MEMORY.md" 2>/dev/null; [ -f "$BACKUP/.gitignore" ] && cp -a "$BACKUP/.gitignore" "{mem_dir}/.gitignore"; for name in {' '.join(f'"{n}"' for n in missing)}; do rm -f "{mem_dir}/$name"; done"""


def cmd_block_remove_dup_commands(name: str, global_md: Path, duplicates: list[Path], identical: bool) -> str:
    if not identical:
        diff_lines = "\n".join(f'  diff "{global_md}" "{d}"' for d in duplicates)
        return f"""# Project copies of {name} DIFFER from global — review:
{diff_lines}
# Then either delete project copies (if diffs are stale) or update global before removing."""
    def proj_of(p: Path) -> str:
        # ~/SRC/<project>/.claude/commands/<file> → <project>
        return p.parts[-4] if len(p.parts) >= 4 else p.stem
    cp_lines = "\n".join(f'cp -a "{d}" "$BACKUP/{proj_of(d)}.md"' for d in duplicates)
    rm_lines = "\n".join(f'rm "{d}"' for d in duplicates)
    test_lines = "\n".join(f'test ! -e "{d}"' for d in duplicates)
    return f"""# Remove project duplicates of {name} (identical to global)
BACKUP="$BACKUP_ROOT/dup-cmd-{name}"
mkdir -p "$BACKUP"
{cp_lines}

{rm_lines}

# Post-check
{test_lines}
echo "OK: removed {len(duplicates)} duplicate(s) of {name}"
# Rollback: for f in "$BACKUP"/*.md; do project=$(basename "$f" .md); cp -a "$f" "$HOME/SRC/$project/.claude/commands/{name}"; done"""


def cmd_block_fix_skill_frontmatter(path: Path, skill_name: str, missing: list[str]) -> str:
    """Idempotent: add only the missing top-level frontmatter keys to the
    SKILL.md, preserving any existing frontmatter. Falls back to inserting a
    fresh frontmatter block if there's none. Description defaults to a
    placeholder the user must edit; name defaults to the directory name;
    version defaults to 1.0.0."""
    return f"""# Add missing frontmatter ({', '.join(missing)}) to {path.parent.name}/SKILL.md
BACKUP="$BACKUP_ROOT/skill-frontmatter-{skill_name}"
mkdir -p "$BACKUP"
cp -a '{path}' "$BACKUP/SKILL.md.before"

python3 - <<'PYEOF'
import pathlib, re
p = pathlib.Path({str(path)!r})
text = p.read_text()
defaults = {{
    'name': {skill_name!r},
    'description': '<edit me — one-line trigger description>',
    'version': '1.0.0',
}}
need = {missing!r}
m = re.match(r'\\A---\\n(.*?)\\n---\\n?(.*)\\Z', text, re.S)
if m:
    fm_body, body = m.group(1), m.group(2)
    existing = set()
    for line in fm_body.splitlines():
        if line and not line.startswith((' ', '\\t')):
            km = re.match(r'^([\\w-]+)\\s*:', line)
            if km:
                existing.add(km.group(1))
    add = ''.join(f'{{k}}: {{defaults[k]}}\\n' for k in need if k not in existing)
    new = '---\\n' + fm_body.rstrip() + '\\n' + add + '---\\n' + body
else:
    fm = ''.join(f'{{k}}: {{defaults[k]}}\\n' for k in need)
    new = '---\\n' + fm + '---\\n\\n' + text
p.write_text(new)
PYEOF

# Post-check: frontmatter now has every required key
python3 - <<'PYEOF'
import pathlib, re, sys
t = pathlib.Path({str(path)!r}).read_text()
m = re.match(r'\\A---\\n(.*?)\\n---', t, re.S)
assert m, 'no frontmatter'
keys = set(re.findall(r'(?m)^([\\w-]+):', m.group(1)))
gap = {{'name', 'description', 'version'}} - keys
assert not gap, f'still missing: {{gap}}'
print('OK: frontmatter complete')
PYEOF
# Reminder: if description was inserted, edit '{path}' to replace the placeholder.
# Rollback: cp -a "$BACKUP/SKILL.md.before" '{path}'"""


def cmd_block_trim_settings(project: Project, dup_lines: list[tuple[str, str]]) -> str:
    hits = "\n".join(f"#   - {e}: {c}" for e, c in dup_lines)
    return f"""# Trim duplicate hook lines from {project.settings_json}
BACKUP="$BACKUP_ROOT/settings-{project.name}"
mkdir -p "$BACKUP"
cp -a '{project.settings_json}' "$BACKUP/settings.json"

# Hand-edit needed — jq-only diff is tricky with array-of-block-of-hooks. Remove:
{hits}
${{EDITOR:-vi}} '{project.settings_json}'

# Validate JSON after edit
jq . '{project.settings_json}' >/dev/null
# Rollback: cp -a "$BACKUP/settings.json" '{project.settings_json}'"""


def cmd_block_fix_broken_hook(scope_label: str, settings_path: Path,
                              event: str, cmd: str, expanded: str) -> str:
    backup_tag = "global" if scope_label == "~" else scope_label
    return f"""# Broken hook path in {settings_path}
# Event:     {event}
# Command:   {cmd}
# Resolves:  {expanded}   ← does not exist
#
# Decide:
#   1) Dead entry — remove the hook block from settings.json.
#   2) Wrong path — fix it (e.g. ${{SRC_ROOT:-$HOME/SRC}}/python-tui-lib/hooks/<name>.sh).
#
# jq-only edit is brittle on nested hook arrays, so hand-edit:
BACKUP="$BACKUP_ROOT/broken-hook-{backup_tag}"
mkdir -p "$BACKUP"
cp -a '{settings_path}' "$BACKUP/settings.json"
${{EDITOR:-vi}} '{settings_path}'
jq . '{settings_path}' >/dev/null && echo 'valid JSON'
# Rollback: cp -a "$BACKUP/settings.json" '{settings_path}'"""


# ─── state visualization ───────────────────────────────────────────────


def render_state_table(projects: list[Project]) -> str:
    rows = []

    # Global row — ~/.claude/ contents + the homedir repo's docs/plans/
    g_mem = memory_split(GLOBAL_CLAUDE / "memory")
    rows.append([
        "~ (global ~/.claude/)",
        present(GLOBAL_CLAUDE / "settings.json"),
        count_hooks_in_settings(GLOBAL_CLAUDE / "settings.json"),
        g_mem[0],
        g_mem[1],
        count_dirs(GLOBAL_CLAUDE / "skills"),
        count_files(GLOBAL_CLAUDE / "commands", "*.md"),
        count_files(HOME / "docs" / "plans", "*.md", default="0"),
    ])

    # Per-project rows
    for p in projects:
        settings_marker = present(p.settings_json)
        if settings_marker == "✅" and p.hook_runner.is_file():
            settings_marker = "✅ (hr)"
        mem = memory_split(p.memory_dir)
        rows.append([
            p.name,
            settings_marker,
            count_hooks_in_settings(p.settings_json) if p.settings_json.is_file() else "—",
            mem[0],
            mem[1],
            count_dirs(p.skills_dir),
            count_files(p.commands_dir, "*.md"),
            count_files(p.docs_plans_dir, "*.md"),
        ])

    return _render_box_table(
        headers=["Project", "settings", "hooks", "MEMORY", "feedback", "skills", "commands", "docs/plans"],
        rows=rows,
    )


def memory_split(d: Path) -> tuple[str, str]:
    """Return (MEMORY.md marker, feedback count) for the memory dir."""
    if not d.is_dir():
        return ("—", "—")
    has_index = (d / "MEMORY.md").is_file()
    feedback_count = sum(1 for f in d.glob("feedback_*.md"))
    mem_marker = "✅" if has_index else "—"
    fb_marker = str(feedback_count) if feedback_count else "—"
    return (mem_marker, fb_marker)


def present(path: Path) -> str:
    return "✅" if path.exists() else "❌"


def count_files(d: Path, pattern: str, default: str = "—") -> str:
    if not d.is_dir():
        return default
    n = len(list(d.glob(pattern)))
    return str(n) if n > 0 else "0"


def count_dirs(d: Path, default: str = "—") -> str:
    if not d.is_dir():
        return default
    n = len([x for x in d.iterdir() if x.is_dir()])
    return str(n) if n > 0 else "0"


def memory_summary(d: Path) -> str:
    if not d.is_dir():
        return "—"
    md_files = list(d.glob("*.md"))
    if not md_files:
        return "0"
    has_index = (d / "MEMORY.md").is_file()
    feedback_count = sum(1 for f in md_files if f.name.startswith("feedback_"))
    other = len(md_files) - feedback_count - (1 if has_index else 0)
    parts = []
    if has_index:
        parts.append("M")
    if feedback_count:
        parts.append(f"{feedback_count}fb")
    if other > 0:
        parts.append(f"{other}o")
    return " ".join(parts) if parts else "0"


def count_hooks_in_settings(path: Path) -> str:
    if not path.is_file():
        return "—"
    try:
        cfg = json.loads(path.read_text())
    except Exception:
        return "?"
    total = 0
    for event, blocks in (cfg.get("hooks") or {}).items():
        for block in blocks:
            total += len(block.get("hooks") or [])
    return str(total)


def _render_box_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(cells: list[str]) -> str:
        return "│ " + " │ ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " │"

    top = "┌─" + "─┬─".join("─" * w for w in widths) + "─┐"
    sep = "├─" + "─┼─".join("─" * w for w in widths) + "─┤"
    bot = "└─" + "─┴─".join("─" * w for w in widths) + "─┘"
    out = [top, fmt_row(headers), sep]
    out.extend(fmt_row(r) for r in rows)
    out.append(bot)
    return "\n".join(out)


# ─── mermaid graphs (only when they add info) ──────────────────────────


def render_mermaid_dependency(projects: list[Project]) -> str:
    """Only emit nodes for projects that diverge from the uniform baseline:
    missing settings.json, OR shipping their own hook-runner. Boring nodes
    (project has settings.json + no hook-runner) get suppressed entirely —
    the full state is in the merged table above.
    """
    no_settings = [p for p in projects if not p.settings_json.is_file()]
    uses_hr     = [p for p in projects if p.hook_runner.is_file()]

    if not no_settings and not uses_hr:
        return ""

    lines = ["```mermaid", "graph LR"]
    lines.append("    PTL[python-tui-lib]")
    lines.append("    GLOBAL[~/.claude<br/>global]")
    lines.append("    PTL ==> GLOBAL")
    for p in uses_hr:
        nid = _mermaid_id(p.name)
        lines.append(f"    GLOBAL -.-> {nid}[{p.name}<br/>+hook-runner]")
    for p in no_settings:
        nid = _mermaid_id(p.name)
        lines.append(f"    GLOBAL -.->|no settings.json| {nid}[{p.name}]")
    lines.append("```")
    return "\n".join(lines)


def _mermaid_id(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _category_counts(recs: list[Recommendation]) -> list[tuple[str, int]]:
    """Sorted (label, count) tuples for the recommendation categories."""
    by_category = Counter(r.category for r in recs)
    return [(CATEGORY_DESC.get(cat, cat).replace("`", ""), count)
            for cat, count in by_category.most_common()]


def render_mermaid_pie(recs: list[Recommendation]) -> str:
    """Mermaid pie chart, side-by-side with the summary table."""
    if not recs:
        return ""
    items = _category_counts(recs)
    lines = ["```mermaid", "pie"]
    for label, count in items:
        lines.append(f'    "{label}" : {count}')
    lines.append("```")
    return "\n".join(lines)


def render_chart_variations(recs: list[Recommendation]) -> str:
    """Five alternate visualizations of the same recommendation-category data.

    Emitted under <details> as a 'pick your favourite' section. The primary
    chart (treemap-beta) is already in the Overview; these are for comparison.
    """
    if not recs:
        return ""
    items = _category_counts(recs)
    if len(items) <= 1:
        return ""

    out = []
    out.append("<details>")
    out.append("<summary>Five alternate visualizations of the same data — pick a favourite.</summary>")
    out.append("")

    # ── 1. Mermaid pie chart (classic) ────────────────────────────────
    out.append("### Variation 1 — mermaid `pie`")
    out.append("")
    out.append("```mermaid")
    out.append("pie")
    for label, count in items:
        out.append(f'    "{label}" : {count}')
    out.append("```")
    out.append("")

    # ── 2. Mermaid horizontal bar chart (xychart-beta) ────────────────
    out.append("### Variation 2 — mermaid `xychart-beta` (horizontal bars)")
    out.append("")
    # xychart-beta wants short labels; abbreviate aggressively.
    short_labels = [_short_label(label, 24) for label, _ in items]
    counts = [count for _, count in items]
    max_count = max(counts)
    labels_csv = ",".join(f'"{l}"' for l in short_labels)
    counts_csv = ",".join(str(c) for c in counts)
    out.append("```mermaid")
    out.append("xychart-beta horizontal")
    out.append(f"    y-axis [{labels_csv}]")
    out.append(f'    x-axis "Count" 0 --> {max_count + 1}')
    out.append(f"    bar [{counts_csv}]")
    out.append("```")
    out.append("")

    # ── 3. Mermaid sankey-beta (Recommendations → categories) ─────────
    # Sankey CSV format: source,target,value. Labels with commas or quotes
    # need double-quoting; using simplified labels for safety.
    out.append("### Variation 3 — mermaid `sankey-beta`")
    out.append("")
    out.append("```mermaid")
    out.append("sankey-beta")
    out.append("")
    for label, count in items:
        safe_label = _short_label(label, 40).replace('"', "'")
        out.append(f'Recommendations,"{safe_label}",{count}')
    out.append("```")
    out.append("")

    # ── 4. Mermaid xychart-beta vertical bars ─────────────────────────
    out.append("### Variation 4 — mermaid `xychart-beta` (vertical bars)")
    out.append("")
    out.append("```mermaid")
    out.append("xychart-beta")
    out.append(f"    x-axis [{labels_csv}]")
    out.append(f'    y-axis "Count" 0 --> {max_count + 1}')
    out.append(f"    bar [{counts_csv}]")
    out.append("```")
    out.append("")

    # ── 5. Mermaid mindmap (radial) ───────────────────────────────────
    # mindmap uses (), [], (()), {{}} as shape syntax — strip those from
    # labels to avoid parser confusion.
    out.append("### Variation 5 — mermaid `mindmap` (radial)")
    out.append("")
    out.append("```mermaid")
    out.append("mindmap")
    out.append("    root((Recommendations))")
    for label, count in items:
        safe = label.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
        out.append(f"        {safe} — {count}")
    out.append("```")
    out.append("")
    out.append("</details>")
    return "\n".join(out)


def _short_label(s: str, maxlen: int) -> str:
    """Truncate to maxlen chars with ellipsis."""
    return s if len(s) <= maxlen else s[:maxlen - 1] + "…"


def collapse_paths(names: list[str]) -> str:
    """Render a list of project names with brace-expansion when ≥2."""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return "{" + ",".join(names) + "}"


def render_md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Standard pipe-delimited markdown table."""
    if not rows:
        return ""
    head = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join("---" for _ in headers) + "|"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join([head, sep, body])


# ─── report assembly ───────────────────────────────────────────────────


def build_report(
    recs: list[Recommendation],
    projects: list[Project],
    *,
    threshold_days: int,
    include_dormant: bool,
) -> str:
    now = datetime.now()
    by_category = Counter(r.category for r in recs)
    recs_sorted = sorted(recs, key=lambda r: (
        CATEGORY_RANK.get(r.category, 99),
        SEVERITY_RANK.get(r.severity, 99),
    ))
    backup_root = f"/tmp/housekeeping-backup-{now.strftime('%Y-%m-%d-%H%M')}"

    P: list[str] = []
    P.append(f"# Housekeeping report — {now.strftime('%Y-%m-%d %H:%M')}")
    P.append("")

    # ── Summary + Pie side-by-side (HTML-in-markdown trick) ────────────
    summary_md = render_md_table(
        ["Field", "Value"],
        [
            ["Recommendations",     f"**{len(recs)}** across **{len(by_category)}** "
                                    f"categor{'y' if len(by_category) == 1 else 'ies'}"],
            ["Projects scanned",    f"**{len(projects)}** "
                                    f"({'including' if include_dormant else 'excluding'} dormant)"],
            ["Orphan-plan threshold", f"**{threshold_days}{NBSP}d**"],
            ["Run time",            fmt_date_iso(now.strftime("%Y-%m-%d")) + " " + now.strftime("%H:%M %Z").strip()],
        ],
    )
    pie = render_mermaid_pie(recs)

    P.append("## Overview")
    P.append("")
    if pie:
        # Two-column: summary left, pie right.
        P.append('<table><tr>')
        P.append('<td valign="top">')
        P.append('')
        P.append("**Summary**")
        P.append('')
        P.append(summary_md)
        P.append('')
        P.append('</td>')
        P.append('<td valign="top">')
        P.append('')
        P.append("**Recommendation category breakdown**")
        P.append('')
        P.append(pie)
        P.append('')
        P.append('</td>')
        P.append('</tr></table>')
        P.append("")
    else:
        P.append("**Summary**")
        P.append("")
        P.append(summary_md)
        P.append("")

    # ── Projects + state (merged) ─────────────────────────────────────
    P.append("## Projects and state")
    P.append("")
    P.append("Legend: ✅ present · ❌ missing · — n/a · `(hr)` = project's own hook-runner.sh wrapper. "
             "`MEMORY` = `MEMORY.md` present · `fb` = count of `feedback_*.md` files. "
             '<span style="opacity:0.45">Dormant projects are greyed out</span>; scans skip them unless `--include-dormant`.')
    P.append("")

    headers = ["Project", "settings", "hooks", "MEMORY", "fb", "skills", "commands", "docs/plans"]
    rows = []

    # Global row pinned at top
    g_mem = memory_split(GLOBAL_CLAUDE / "memory")
    rows.append([
        "**~/.claude** (global)",
        present(GLOBAL_CLAUDE / "settings.json"),
        count_hooks_in_settings(GLOBAL_CLAUDE / "settings.json"),
        g_mem[0],
        g_mem[1],
        count_dirs(GLOBAL_CLAUDE / "skills"),
        count_files(GLOBAL_CLAUDE / "commands", "*.md"),
        count_files(HOME / "docs" / "plans", "*.md", default="0"),
    ])

    # Per-project rows
    for p in projects:
        repo = discover_repo_url(p.path)
        is_dormant = (p.status == "dormant")
        name_inner = f"[{p.name}]({repo})" if repo else p.name

        settings_marker = present(p.settings_json)
        if settings_marker == "✅" and p.hook_runner.is_file():
            settings_marker = "✅ (hr)"
        mem = memory_split(p.memory_dir)
        cells = [
            name_inner,
            settings_marker,
            count_hooks_in_settings(p.settings_json) if p.settings_json.is_file() else "—",
            mem[0],
            mem[1],
            count_dirs(p.skills_dir),
            count_files(p.commands_dir, "*.md"),
            count_files(p.docs_plans_dir, "*.md"),
        ]
        # Grey out the entire row when dormant
        if is_dormant:
            cells = [f'<span style="opacity:0.45">{c}</span>' for c in cells]
        rows.append(cells)

    P.append(render_md_table(headers, rows))
    P.append("")
    P.append(f"All project paths: `~/SRC/{collapse_paths([p.name for p in projects])}/`")
    P.append("")

    # ── What we scanned for ───────────────────────────────────────────
    P.append("## What we scanned for")
    P.append("")
    P.append(render_md_table(
        ["Category", "Description", "Hits"],
        [
            [CATEGORY_DESC[cat], SCAN_DESCRIPTIONS[cat], str(by_category.get(cat, 0))]
            for cat, _ in CATEGORIES_ORDER
        ],
    ))
    P.append("")

    # ── Recommendations grouped by category (tables) ──────────────────
    if recs:
        P.append("## Recommendations")
        P.append("")
        grouped: dict[str, list[tuple[int, Recommendation]]] = defaultdict(list)
        for i, r in enumerate(recs_sorted, 1):
            grouped[r.category].append((i, r))
        for cat, label in CATEGORIES_ORDER:
            items = grouped.get(cat, [])
            if not items:
                continue
            P.append(f"### {label} ({len(items)})")
            P.append("")
            cols = CATEGORY_COLUMNS.get(cat)
            if cols:
                # Render as a consolidated category table
                table_rows = []
                for idx, r in items:
                    sev_marker = "" if r.severity == "info" else f" ⚠️"
                    table_rows.append([str(idx) + sev_marker, *r.row])
                P.append(render_md_table(cols, table_rows))
                pattern = CATEGORY_PATH_PATTERNS.get(cat)
                if pattern:
                    P.append("")
                    P.append(pattern)
            else:
                # Fallback to prose for categories without a column schema
                for idx, r in items:
                    sev = "" if r.severity == "info" else f" `[{r.severity}]`"
                    P.append(f"**#{idx}. {r.title}**{sev}")
                    P.append("")
                    if r.details.strip():
                        P.append(r.details)
                        P.append("")
            P.append("")
    else:
        P.append("## Recommendations")
        P.append("")
        P.append("**None.** No drift detected — everything matches the expected baseline.")
        P.append("")

    # State table merged with Projects section above.
    deps = render_mermaid_dependency(active(projects))
    if deps:
        P.append("## Project ↔ global hook chain (drift)")
        P.append("")
        P.append(deps)
        P.append("")

    # ── Executable command list (collapsed by default) ────────────────
    if recs:
        P.append("## Executable command list")
        P.append("")
        P.append("<details>")
        P.append("<summary>Click to expand — copy-paste fallback if you'd rather run by hand than use the interactive <code>/claude-housekeeping</code> flow.</summary>")
        P.append("")
        P.append("Each block is one recommendation. Run the top-of-file prelude first, then "
                 "individual blocks in any order. Every block: backup → action → post-check. "
                 "Backups land in `$BACKUP_ROOT`; rollback hints in each block's trailing comment.")
        P.append("")
        P.append("```bash")
        P.append("set -eo pipefail")
        P.append(f"BACKUP_ROOT={backup_root}")
        P.append('mkdir -p "$BACKUP_ROOT"')
        P.append('echo "Backups for this run land in $BACKUP_ROOT"')
        P.append("```")
        P.append("")
        for i, r in enumerate(recs_sorted, 1):
            P.append(f"**Block for #{i} — {r.title}**")
            P.append("")
            P.append("```bash")
            P.append(r.command_block.strip())
            P.append("```")
            P.append("")
        P.append("```bash")
        P.append('echo "Approved recommendations applied. Backups: $BACKUP_ROOT"')
        P.append("```")
        P.append("")
        P.append("</details>")
        P.append("")

    # ── /schedule reminder (GitHub-style [!TIP] callout) ─────────
    P.append("> [!TIP]")
    P.append("> **Run this daily**")
    P.append("> ")
    P.append('> `/schedule "every day at 8am" /claude-housekeeping --report-only --quiet`')
    P.append(">")
    P.append("> Writes to `~/.claude/housekeeping/reports/` each morning; only notifies if drift exceeds the threshold.")
    P.append("> Run `task md -- ~/.claude/housekeeping/reports/latest.md` to render in the browser.")
    P.append("")

    return "\n".join(P)


# ─── diff mode ─────────────────────────────────────────────────────────


def _norm_category(title: str) -> str:
    """Normalize a category heading so cross-version reports match (the title
    string occasionally gains/loses backticks or .md suffixes between scanner
    versions)."""
    t = re.sub(r'[`*_]', '', title)
    t = re.sub(r'\bTODO\.md\b', 'TODO', t)
    t = re.sub(r'\.\s*claude/settings\.json', '.claude/settings.json', t)
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t


def _parse_report_recommendations(path: Path) -> dict[str, set[str]]:
    """Return {category_title: set(stable_identifiers)} from a report markdown file.

    Stable identifier per category is the *second* table column value (after
    the recommendation number). That column happens to be the natural key in
    every category: project name, command filename, TODO.md location, etc.
    """
    text = path.read_text(errors="replace")
    out: dict[str, set[str]] = {}
    current: Optional[str] = None
    cat_re = re.compile(r'^###\s+(.+?)\s*\(\s*\d+(?:\s+items?)?\s*\)\s*$')
    row_re = re.compile(r'^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|')
    # Legacy format: "**#N. Title body**" — one rec per block.
    legacy_re = re.compile(r'^\*\*#(\d+)\.\s+([^*]+?)\*\*')
    for line in text.splitlines():
        m = cat_re.match(line)
        if m:
            current = _norm_category(m.group(1))
            out.setdefault(current, set())
            continue
        if current is None:
            continue
        row = row_re.match(line)
        if row:
            ident = row.group(2).strip().strip('`')
            link = re.match(r'^\[([^\]]+)\]\([^)]+\)$', ident)
            if link:
                ident = link.group(1)
            out[current].add(ident)
            continue
        leg = legacy_re.match(line)
        if leg:
            ident = leg.group(2).strip().strip('`')
            out[current].add(ident)
    return out


def _parse_state_table(path: Path) -> dict[str, str]:
    """Return {project_name: full_table_row_text} for the state-vis table.

    Used to produce a side-by-side before/after comparison of per-project state.
    """
    text = path.read_text(errors="replace")
    rows: dict[str, str] = {}
    in_state = False
    for line in text.splitlines():
        if line.startswith("| Project | settings | hooks"):
            in_state = True
            continue
        if not in_state:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            break  # end of table
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if not cells:
            continue
        first = cells[0]
        # Extract from a markdown link "[name](url)" first; then strip any
        # remaining HTML/markdown decoration.
        link = re.search(r'\[([^\]]+)\]\([^)]+\)', first)
        if link:
            proj = link.group(1).strip()
        else:
            proj = re.sub(r'<[^>]+>', '', first)
            proj = re.sub(r'[*_`]', '', proj).strip()
        if proj:
            rows[proj] = line
    return rows


def build_diff_report(before_path: Path, after_path: Path) -> str:
    before = _parse_report_recommendations(before_path)
    after = _parse_report_recommendations(after_path)

    all_categories = sorted(set(before) | set(after))

    P: list[str] = []
    P.append(f"# Housekeeping diff — {before_path.name} → {after_path.name}\n")
    before_total = sum(len(v) for v in before.values())
    after_total = sum(len(v) for v in after.values())
    delta = after_total - before_total
    sign = "+" if delta > 0 else ""
    P.append(f"**Before:** {before_total} recommendations  ·  "
             f"**After:** {after_total}  ·  **Delta:** {sign}{delta}\n")

    # Per-category summary
    P.append("## Per-category counts\n")
    P.append("| Category | Before | After | Δ |")
    P.append("|---|---:|---:|---:|")
    for cat in all_categories:
        b = len(before.get(cat, set()))
        a = len(after.get(cat, set()))
        d = a - b
        marker = "✅" if d < 0 else ("⚠️" if d > 0 else "—")
        P.append(f"| {cat} | {b} | {a} | {marker} {'+' if d > 0 else ''}{d} |")
    P.append("")

    # Resolved
    P.append("## Resolved (in before, gone in after)\n")
    any_resolved = False
    for cat in all_categories:
        gone = sorted(before.get(cat, set()) - after.get(cat, set()))
        if gone:
            any_resolved = True
            P.append(f"### {cat} ({len(gone)})\n")
            for g in gone:
                P.append(f"- ✅ `{g}`")
            P.append("")
    if not any_resolved:
        P.append("_(none)_\n")

    # New
    P.append("## New (in after, not in before)\n")
    any_new = False
    for cat in all_categories:
        new = sorted(after.get(cat, set()) - before.get(cat, set()))
        if new:
            any_new = True
            P.append(f"### {cat} ({len(new)})\n")
            for n in new:
                P.append(f"- ⚠️ `{n}`")
            P.append("")
    if not any_new:
        P.append("_(none — no regressions or newly-discovered drift)_\n")

    # Unchanged
    P.append("## Unchanged (in both — deferred or skipped)\n")
    any_unchanged = False
    for cat in all_categories:
        same = sorted(before.get(cat, set()) & after.get(cat, set()))
        if same:
            any_unchanged = True
            P.append(f"### {cat} ({len(same)})\n")
            for s in same:
                P.append(f"- `{s}`")
            P.append("")
    if not any_unchanged:
        P.append("_(none)_\n")

    # State-table diff
    before_rows = _parse_state_table(before_path)
    after_rows = _parse_state_table(after_path)
    changed_rows = sorted(
        p for p in set(before_rows) | set(after_rows)
        if before_rows.get(p) != after_rows.get(p)
    )
    if changed_rows:
        P.append("## State-table rows that changed\n")
        P.append("| Project | Before | After |")
        P.append("|---|---|---|")
        for p in changed_rows:
            b = before_rows.get(p, "_(absent)_").replace("|", "\\|")
            a = after_rows.get(p, "_(absent)_").replace("|", "\\|")
            P.append(f"| **{p}** | <pre>{b}</pre> | <pre>{a}</pre> |")
        P.append("")

    # Embed both reports under collapsed details
    for label, p in (("Before-report (full)", before_path), ("After-report (full)", after_path)):
        P.append(f"<details><summary><b>{label}</b> — <code>{p.name}</code></summary>\n")
        P.append(p.read_text(errors="replace"))
        P.append("\n</details>\n")

    return "\n".join(P)


# ─── entry ─────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--threshold-days", type=int, default=1)
    ap.add_argument("--include-dormant", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--tag", default="",
                    help="Suffix for the output filename (e.g. 'before', 'after').")
    ap.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"),
                    help="Generate a delta report from two prior snapshots. "
                         "Each arg may be 'before=<path>' / 'after=<path>' or a bare path.")
    args = ap.parse_args()

    # ── --diff mode ────────────────────────────────────────────────────
    if args.diff:
        def resolve(s: str) -> Path:
            if "=" in s:
                s = s.split("=", 1)[1]
            return Path(os.path.expanduser(s)).resolve()
        before_path = resolve(args.diff[0])
        after_path = resolve(args.diff[1])
        for p in (before_path, after_path):
            if not p.is_file():
                print(f"ERROR: report not found: {p}", file=sys.stderr)
                return 2
        diff_md = build_diff_report(before_path, after_path)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        out_path = REPORTS_DIR / f"{now.strftime('%Y-%m-%d-%H%M')}-diff.md"
        out_path.write_text(diff_md)
        latest = REPORTS_DIR / "latest-diff.md"
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(out_path.name)
        print(str(out_path))
        return 0

    if not PROJECTS_JSON.is_file():
        print(f"ERROR: {PROJECTS_JSON} missing", file=sys.stderr)
        return 2

    all_projects = load_projects()
    scan_set = all_projects if args.include_dormant else active(all_projects)

    recs: list[Recommendation] = []
    recs.extend(scan_global_hooks_sanity())
    recs.extend(scan_missing_project_settings(scan_set))
    recs.extend(scan_config_drift(scan_set))
    recs.extend(scan_broken_hook_paths(scan_set))
    recs.extend(scan_uncommitted_claude_changes(scan_set))
    recs.extend(scan_orphan_plans(args.threshold_days))
    recs.extend(scan_duplicate_memories(scan_set))
    recs.extend(scan_missing_global_cascade(scan_set))
    recs.extend(scan_leaked_project_memories(scan_set))
    recs.extend(scan_duplicate_commands(scan_set))
    recs.extend(scan_missing_md_history(scan_set))
    recs.extend(scan_skill_frontmatter(scan_set))

    report_md = build_report(
        recs, all_projects,
        threshold_days=args.threshold_days,
        include_dormant=args.include_dormant,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    suffix = f"-{args.tag}" if args.tag else ""
    out_path = REPORTS_DIR / f"{now.strftime('%Y-%m-%d-%H%M')}{suffix}.md"
    out_path.write_text(report_md)

    latest_name = f"latest{suffix}.md" if args.tag else "latest.md"
    latest = REPORTS_DIR / latest_name
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(out_path.name)

    print(str(out_path))
    if not args.quiet:
        print(f"\n{pluralize(len(recs), 'recommendation')}. View: cat {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
