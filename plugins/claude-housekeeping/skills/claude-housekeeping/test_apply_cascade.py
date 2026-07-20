#!/usr/bin/env python3
"""Regression tests for apply-cascade.py's managed-block handling.

Run directly (`python3 test_apply_cascade.py`) or under pytest.

Context: on 2026-07-19 a repointed hook re-enabled cascade-heal.sh, which loops
over every project in projects.json and calls apply-cascade.py on each. `homedir`
is a registered project whose path is `~`, so the master memory store was handed
to itself as a destination. Each run re-suffixed the index headings
("## User (inherited from ~) (inherited from ~)") and appended another managed
block; that corrupted index was then cascaded verbatim into 27 project MEMORY.md
files, all of them git-tracked.

The tests below pin the two properties that were missing:
  1. the master store is never a cascade destination, and
  2. an already-malformed MEMORY.md converges to exactly one clean block.

Each test drives the real script in a subprocess with HOME pointed at a temp dir
(apply-cascade.py derives every path from Path.home()), so nothing here touches
the live store.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "apply-cascade.py"

BEGIN = "<!-- BEGIN GLOBAL MEMORY (managed by claude-housekeeping; do not edit) -->"
END = "<!-- END GLOBAL MEMORY -->"

MASTER_INDEX = """# Memory index

## User
- [User profile](user_profile.md) — role and preferences

## Feedback
- [Commit scope](feedback_commit_scope.md) — stage only what you touched
"""

# What a run of the old, unguarded code left behind: an orphan END ahead of the
# first BEGIN, three stacked blocks, and headings suffixed once per run.
CORRUPT_PROJECT_MEMORY = f"""# Memory Index

## Local
- [Project thing](project_thing.md) — a real project-local memory

{END}

{BEGIN}

## User (inherited from ~)

- [User profile](user_profile.md) — role and preferences

{BEGIN}

## User (inherited from ~) (inherited from ~)

- [User profile](user_profile.md) — role and preferences

{BEGIN}

## User (inherited from ~) (inherited from ~) (inherited from ~)

- [User profile](user_profile.md) — role and preferences

{END}
{END}
{END}
"""


def _fake_home(tmp: Path) -> Path:
    """A minimal but realistic home: master store, index, registry."""
    master = tmp / ".claude" / "memory"
    master.mkdir(parents=True)
    (master / "MEMORY.md").write_text(MASTER_INDEX)
    (tmp / ".claude" / "projects.json").write_text(
        json.dumps({"projects": [{"name": "proj", "path": "~/proj"}]})
    )
    return tmp


def _run(home: Path, target: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target)],
        env=env, capture_output=True, text=True,
    )


def test_malformed_memory_converges_to_one_block() -> None:
    """A MEMORY.md with stacked blocks and orphan END markers must heal.

    This is the assertion the old code failed. Its strip regex was non-greedy
    from BEGIN to the *first* following END, so against three stacked blocks it
    consumed the inner BEGINs and stranded the trailing ENDs — leaving 1 BEGIN
    and 4 ENDs, forever, on every subsequent run.
    """
    with tempfile.TemporaryDirectory() as td:
        home = _fake_home(Path(td))
        proj_mem = home / "proj" / ".claude" / "memory"
        proj_mem.mkdir(parents=True)
        (proj_mem / "MEMORY.md").write_text(CORRUPT_PROJECT_MEMORY)

        res = _run(home, home / "proj")
        assert res.returncode == 0, res.stderr

        out = (proj_mem / "MEMORY.md").read_text()
        assert out.count(BEGIN) == 1, f"expected 1 BEGIN, got {out.count(BEGIN)}"
        assert out.count(END) == 1, f"expected 1 END, got {out.count(END)}"
        assert "(inherited from ~) (inherited" not in out, "headings still compounding"
        # Project-local content outside the markers must survive untouched.
        assert "[Project thing](project_thing.md)" in out


def test_repeated_runs_are_idempotent() -> None:
    """Healing must be a fixed point, not a slow drift."""
    with tempfile.TemporaryDirectory() as td:
        home = _fake_home(Path(td))
        proj_mem = home / "proj" / ".claude" / "memory"
        proj_mem.mkdir(parents=True)
        (proj_mem / "MEMORY.md").write_text(CORRUPT_PROJECT_MEMORY)

        _run(home, home / "proj")
        first = (proj_mem / "MEMORY.md").read_text()
        for _ in range(3):
            _run(home, home / "proj")
        assert (proj_mem / "MEMORY.md").read_text() == first, "output drifts across runs"


def test_master_store_is_never_a_cascade_destination() -> None:
    """Cascading the master onto itself is what caused the corruption.

    cascade-heal.sh iterates projects.json, and `homedir` legitimately has
    path `~`, so the script itself has to refuse the self-projection.
    """
    with tempfile.TemporaryDirectory() as td:
        home = _fake_home(Path(td))
        before = (home / ".claude" / "memory" / "MEMORY.md").read_text()

        res = _run(home, home)
        assert res.returncode == 0, res.stderr
        assert "master memory store" in res.stdout, res.stdout

        after = (home / ".claude" / "memory" / "MEMORY.md").read_text()
        assert after == before, "master index was modified by a self-cascade"
        assert BEGIN not in after, "master must never carry a managed block"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
