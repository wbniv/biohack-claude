---
name: docs/ directory layout for session artifacts
description: Plans, investigations, transcripts, and prompts all live under docs/<type>/ — not the repo root
type: feedback
originSessionId: b8bd240a-7d30-4f62-a06d-d132661033d6
---
In this repo, save session/process artifacts under `docs/`:

- **Plans** → `docs/plans/<descriptive-name>.md` (e.g. `docs/plans/aws-deployment.md`)
- **Investigations** → `docs/investigations/<descriptive-name>.md`
- **Transcripts** → `docs/transcripts/<descriptive-name>.md`
- **Prompts** → `docs/prompts/YYYY-MM-DD.md` — one file per calendar day, prompts in order separated by `---`

**Why:** Earlier convention was top-level `plans/` and `prompts/` directories. Updated 2026-04-28 to consolidate all session/process artifacts under `docs/` so the repo root stays focused on code/config. The legacy `plans/` directory still contains historical files; do not write new plans there.

**How to apply:**
- After writing a plan, save it to `docs/plans/`. Do NOT also copy to legacy `plans/`.
- When writing an investigation writeup, save to `docs/investigations/`.
- When saving a transcript, save to `docs/transcripts/`.
- At end of session (or when reminded), append the day's user prompts to `docs/prompts/YYYY-MM-DD.md`.
