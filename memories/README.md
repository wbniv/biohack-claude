# memories/ — Personal Claude Code memories (reference only)

These are Will's personal memories from `~/.claude/projects/-home-will/memory/`
and per-project `~/.claude/projects/*/memory/` directories.

**Claude Code does not auto-load memories from third-party repos.**
They are published here as reference — patterns and preferences that may inspire
your own setup. To adopt any of them, copy the content into your own
`~/.claude/memory/<name>.md` and add a pointer in your `MEMORY.md` index.

## Structure

```
memories/
├── global/         # ~/.claude/projects/-home-will/memory/ — cross-project feedback,
│                   #   user profile, tooling preferences
└── projects/
    └── <project>/  # per-project memory dirs, e.g. WorldFoundry, linuxfoundry-org
```

## Sync

`scripts/sync-from-claude.sh` rsyncs memories from `~/.claude/` into this directory.
Files matched by `.shareignore` in this directory are excluded from the sync
(use it to skip memories that contain project-specific secrets or client context).

Memories are **not** auto-committed — run `task sync` then review and commit manually.
