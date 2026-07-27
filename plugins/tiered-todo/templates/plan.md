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

## Mockups

**Required for any change with a visible surface** — UI, a rendered page, a CLI's
on-screen output, a TUI pane, a generated document. Prose describing a layout is not
reviewable; a picture is. If the change has genuinely no visible surface (a parser, a
hook, a build step), delete this section and say so in one line under **Approach**.

Mockups live in this plan's **co-named bundle directory** — the sibling folder with the
same basename as this file:

```
docs/plans/2026-07-27-my-topic.md      ← this plan
docs/plans/2026-07-27-my-topic/        ← its bundle
    settings-dark.html                 ← interactive, self-contained
    settings-dark.png                  ← static thumbnail, same basename
```

`md-to-html.sh` gives any `FOO.md` with a co-named `FOO/` an asset panel at the bottom
of the rendered page, and embeds each self-contained `.html` as a **live sandboxed
iframe** — so the reader sees the mockup running, not its source.

Rules that make it actually render:

- **Self-contained only.** Inline CSS and JS. No external stylesheets, fonts, scripts, or
  images — relative asset references are *not* inlined and come out blank.
- **Design to a 1440×900 logical canvas.** The viewer scales it to fit.
- **Ship a `.png` beside each `.html`** with the same basename, so the plan body can show
  a thumbnail that links through to the interactive version.
- **Budget:** under 512 KB per HTML file, 2 MB per image, 8 MB across the whole bundle.
- Start from [`~/python-tui-lib/templates/todo/mockup.html`](../../../python-tui-lib/templates/todo/mockup.html).

Reference each one in the body as a linked thumbnail, so it reads inline *and* opens:

```markdown
[![Dark settings panel](2026-07-27-my-topic/settings-dark.png)](2026-07-27-my-topic/settings-dark.html)

What this shows, and the decision it is asking you to make.
[Open the interactive mockup](2026-07-27-my-topic/settings-dark.html).
```

Show the **real states** — empty, loaded, error, narrow — not just the happy path. A
mockup that only shows the good case hides exactly the decisions worth reviewing.

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
