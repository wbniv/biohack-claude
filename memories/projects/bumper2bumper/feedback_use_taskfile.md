---
name: Prefer Taskfile commands over raw equivalents
description: When suggesting or running commands in this repo, use `task <name>` if one exists in Taskfile.yml; only fall back to raw commands when there's no Task entry.
type: feedback
originSessionId: a0418b09-bf1e-421e-a247-052dab88c63a
---
When giving the user shell directives or running commands in this repo, check `Taskfile.yml` (or `task --list`) first and use the Task entry if one exists. Examples:

- `task serve` instead of `cd backend/splitledger_server && dart bin/main.dart --apply-migrations`
- `task analyze` / `task analyze-frontend` / `task analyze-backend` instead of `flutter analyze` / `dart analyze`
- `task generate` instead of raw `serverpod generate`
- `task run-web` / `task run-chrome` / `task run-web-lan` instead of raw `flutter run`
- `task up` / `task down` instead of `docker compose up -d` / `down`
- `task test` / `task test-backend` / `task test-frontend` / `task test-e2e`
- `task build-web`, `task build-docker`, `task migrate`, `task health`, `task deps`, `task tui`, `task tf-plan`, `task tf-apply`, `task caddy-dev`, `task caddy-validate`, `task lan-ip`, `task clear-ledger`

**Why:** The user maintains the Taskfile as the source-of-truth way to invoke project commands — it captures correct cwd, env, flags, and ordering. Raw commands work but bypass that single source of truth and drift from how the user actually runs things.

**How to apply:**
- Before recommending or running a build/test/serve/generate command, check `Taskfile.yml` for an equivalent.
- If a Task entry exists, use it (and reference it by name in user-facing text).
- If none exists, the raw command is fine — and it's worth mentioning that no Task wraps it (in case the user wants to add one).
- Re-check the Taskfile periodically; new tasks get added.
