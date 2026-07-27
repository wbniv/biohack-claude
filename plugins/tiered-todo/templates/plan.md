# {{TITLE}}

## Context

Why this is being done — the problem or need it addresses, what prompted it, and the
intended outcome. Someone reading this in six months should understand the motivation
without reconstructing it from the diff.

State what is true *today* that makes this necessary, with evidence (a measurement, an
error, a file path) rather than an assertion.

## Approach

The recommended approach only — not a survey of alternatives. Name the one you rejected in
a line if the choice was close, then move on.

Name the critical files. For a change that repeats a pattern across many files, describe
the pattern once and list two or three representative paths; do not enumerate every file.

Reference existing helpers to reuse, with paths. In this workspace shared scripts and hooks
live in `~/python-tui-lib/` and are referenced by path, never copied.

## Out of scope

What this deliberately does not do, and why. Anything listed here is auto-captured into
`TODO.md`'s Inbox by `audit-plan-deferrals.sh` at commit time — so write these as real,
triageable items, not hand-waves.

## Verification

Numbered, runnable steps. These are the spec: keep them **exactly as written** when
recording results, paste the raw command output in a code block below each one, then a
PASS/FAIL note. Do not reorganise, rename, or summarise them.

1. …
2. …
3. …

<!--
When the work lands, this section becomes the permanent record:

1. **Step as originally written.**

```
$ the exact command
raw output, unedited
```

**PASS** — one line on what the output proves.

An item stays `[verify T<n>]` in TODO.md until every step here has recorded output.
-->
