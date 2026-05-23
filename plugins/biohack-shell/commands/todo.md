---
description: Add a new item to TODO.md
argument-hint: <description of the TODO item>
allowed-tools: Read, Edit, Write, Glob, Grep
---

## Context

Current TODO.md:
!`cat TODO.md`

Existing plans:
!`ls plans/ 2>/dev/null`

## Your task

Add a new TODO item to `TODO.md` based on: **$ARGUMENTS**

### How to write the item

1. **Summarize** the user's words into a clear, scannable entry with enough context to understand later. Match the style of existing entries — a short title, then a dash-separated explanation if needed.
2. **Find references**: search `plans/` and `docs/` for related files. If a relevant plan or doc exists, link it.
3. **If there's an in-progress plan** (in the current conversation or at the `.claude/plans/` path) that hasn't been saved to `plans/` yet, **write it to disk** at `plans/YYYY-MM-DD-<topic>.md` first, then link it.
4. Format: `- [ ] Title — explanation with context. [plan](plans/...) or [docs/path/to/file.md](docs/path/to/file.md)`
   - Plans get link text `plan`: `[plan](plans/2026-03-21-foo.md)`
   - Other docs get the relative filename as link text: `[docs/investigations/foo.md](docs/investigations/foo.md)`
5. Place under the most appropriate section (`## OPS`, `## DOCS`, `## BUILD & RELEASE`, `## TBD?`, `## Later`). Default to `## OPS`.
6. Append after the last unchecked `- [ ]` item in that section (before any `- [x]` items or the next `##` header).
7. Use backtick formatting for code, paths, and commands. Use `[text](path)` relative links, not backtick-quoted paths.
8. Do NOT create new sections or modify existing items.

Make the edit and confirm what was added and where.
