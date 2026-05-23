---
name: "Task" in this repo means Taskfile, not CLI subcommand
description: When user says "Task command" in gustos-colores, they mean a Taskfile.yml entry callable via `task <name>`. Capitalized "Task" is the specific hint.
type: feedback
originSessionId: ae41ac14-aef4-4a0c-a7a4-048be5e9986c
---
In gustos-colores, when the user says "Task command" or "a Task to do
X", they mean a `Taskfile.yml` entry (https://taskfile.dev) callable
via `task <name>` — not a cobrand.py subcommand, not an Agent tool
TaskCreate entry. The capital T in "Task" is the specific hint.

**Why:** CLAUDE.md says "All commands use [Task](https://taskfile.dev).
Run from the repo root." Every user-facing entry point in this repo
is exposed as a `task` target. User confirmed this reading explicitly:
"your comment note was correct; that IS what i asked for."

**How to apply:** when user requests a "Task command" to run something
in this repo, default to adding a `Taskfile.yml` entry — that's what
they literally mean. In some cases they may accept a CLI-only
alternative (e.g., the `./cobrands/cobrand.py decommissioned` subcommand
instead of `task decommissioned` — user preferred the script-only
approach for rare-access listings). But the default interpretation of
the request is the Taskfile entry; don't silently substitute.

Generalising outside this repo: don't assume — check for a Taskfile.yml
before interpreting "task" lowercase-ly.
