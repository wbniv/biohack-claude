---
name: Reproducibility = "works on a fresh box without my system state"
description: Every fix must work when checked out by someone else / on CI / on a fresh laptop — local-machine state (daemon.json, /etc, GUI keyring, system packages) is not "the fix"
type: feedback
originSessionId: f6adfe21-ba43-4e9a-9b99-14458e233fa2
---
The reproducibility bar is not "works on this dev box" — it's "works after `git clone` on a fresh machine with only a handful of documented secrets." Anything that lives outside the repo (`/etc/docker/daemon.json`, GUI keyring, host-level systemd config, IDE settings, manually-installed system packages) does not count as "the fix" — it's a dependency that, if undocumented, will silently break for the next dev / CI / a wiped laptop / a teammate.

**Why:** The user explicitly said "everything needs to be reproducible NOT ON MY SYSTEM" — emphatic, twice in one turn. This builds on `~/SRC/CLAUDE.md`'s "Everything must be reproducible" rule but is a sharper version: I keep treating the user's box as the deployment target instead of one instance of N future environments. Specific failures from this session: I reverted `--network=host` from the Taskfile after fixing daemon.json MTU on the user's box, which is exactly backwards — daemon.json is local state, the Taskfile flag is repo state.

**How to apply:**
- When weighing fix locations: prefer repo-level (Dockerfile / Taskfile / config-as-code / IaC) over host-level (daemon.json, /etc/*, dotfiles, OS-managed services).
- If a fix *must* live on the host (driver install, kernel module, OS-level package), encode it in a `scripts/setup-*.sh` that's idempotent + version-controlled, and reference it from CLAUDE.md.
- Before declaring a fix "done", mentally run the question: *would this still work after `rm -rf` on the laptop, fresh OS, fresh `git clone`?* If not, name the missing reproducibility surface and either commit a setup script or document the manual step.
- Local-state fixes are valid as defense-in-depth or convenience layered *on top of* the reproducible fix — not as the primary fix.
- This is distinct from the "real engineering standards" rule but compounds with it: solo-dev-now is not an excuse, AND working-on-this-box is not enough.
