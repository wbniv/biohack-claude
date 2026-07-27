# tiered-todo

Rank every task 0–5 by how much *thinking* it needs, then dispatch it to the cheapest
model that can actually do it.

Running every task on the biggest model burns a weekly limit in a few days. Running
everything on the smallest produces confident garbage. This plugin makes the rank an
explicit, written-down property of each TODO item, and makes dispatch follow it.

In practice most implementation lands on Opus, grunt work on Sonnet, and Haiku does
little beyond greps — with **less token usage and fewer omissions** than running one big
model on everything, because an agent handed one bounded job does it more reliably than a
session juggling twelve.

---

## The tier scale

| Tier | Kind of work | Agent | Model |
|---|---|---|---|
| **T0** | Mechanical lookup — grep, find, count, "which file defines X". No judgment. | `t0-lookup` | Haiku 4.5, **read-only** |
| **T1** | Mechanical edit with a known recipe — rename, version bump, apply a diagnosed fix. | `t1-sonnet-med` | Sonnet 5 @ medium |
| **T2** | Bounded implementation — one file or module, clear spec, judgment about *how* not *what*. | `t2-sonnet-high` | Sonnet 5 @ high |
| **T3** | Multi-file work against a settled plan. **Default for unranked items.** | `t3-opus-med` | Opus 5 @ medium |
| **T4** | Design *and* implementation — non-obvious architecture, unknown root cause. | `t4-opus-high` | Opus 5 @ high |
| **T5** | Do it yourself, inline. No subagent. | — | — |

**T0 has no `Write`/`Edit` tool.** That is deliberate: a mis-ranked T0 costs a bad report,
never a bad commit.

**T5 is a category, not a fallback.** Judgment calls the user cares about, work that
depends on the whole session's history, decisions about the plan itself, final
integration and review — and anything cheaper to finish than to brief.

---

## The two things that don't happen by default

**Spawn cost is real.** A subagent costs a full written brief plus a cold read of
everything it needs. Don't dispatch anything you could finish in under ~3 tool calls. When
a T0/T1 item sits adjacent to work already in progress, absorb it instead of spawning.

**Agents get thrown away too eagerly.** The default is one agent per task. When a live
agent already holds the relevant context, re-messaging it is dramatically cheaper than
briefing a fresh one. `/next` therefore stamps the dispatched agent's id onto the in-flight
item and checks those stamps before spawning anything new.

---

## Marker grammar

The tier lives in the status bracket, tier last, both parts optional:

```markdown
## Open

### M1 — Far Pointers

- [T4] **Far-pointer codegen** — lower 24-bit pointers through the DAG. [plan](docs/plans/2026-07-20-far-ptr.md)
- [wip T2] **Bank-cross test harness** — table-driven cases.  <!-- agent:a7a12a1f88b6840b4 -->
- [T0] **Audit stale symlinks** — grep for broken links.
- [verify T3] **KDE config stack assertion** — run plan steps 1–4.
- [ ] **(triage)** unranked legacy item — dispatched at the T3 default.

## Done

- [x] 2026-07-26 — [tiered-todo] Rank TODO items 0–5 and route each to its tier agent.
```

| Marker | Meaning |
|---|---|
| `- [ ]` | open, unranked — dispatched at `T3` |
| `- [T4]` | open, tier 4 |
| `- [wip T2]` | in progress, tier 2 |
| `- [verify T3]` | implemented, verification not yet run + recorded |
| `- [x]` | done — `## Done` only, **no tier** |

Done lines drop the tier: it is a dispatch input, not a historical record.

The `<!-- agent:… -->` stamp renders invisibly, greps cleanly, and survives context
compaction — which is what makes agent reuse possible across a long run.

`lib/todo_format.py` is the canonical parser (`TASK_RE`, `parse_marker`, `render_marker`).
Import it rather than writing another regex.

---

## Commands

| Command | What it does |
|---|---|
| `/todo <description>` | Add an item, ranked. Reports the rank and why. |
| `/todo done: <title>` | Move it to `## Done`, dropping tier and agent stamp. |
| `/todo rank` | Assign tiers to every unranked open item. Additive; never re-ranks. |
| `/todo sweep` | Migrate a legacy TODO into the four-bucket model, ranking as it goes. |
| `/next [title]` | Pick the next item, rank it if needed, reuse or spawn its tier agent. |
| `/verify [title]` | Run a `[verify T<n>]` item's plan steps, record evidence, promote on pass. |

The loop is `/todo` → `/next` → `/verify` → `/todo done:`.

---

## Hooks

- **`no-fable-subagent.sh`** (`PreToolUse[Agent]`) — hard-denies dispatching the
  orchestrator model as a subagent. T5 means *do it yourself*, not *spawn a copy of
  yourself*. Matcher is `Agent` rather than `Task` because some plugins rewrite `Task`
  matchers on the fly.
- **`todo-reminder.sh`** (`Stop`) — injects up to five open items, with their tiers, so
  "what's next?" pulls from the backlog instead of prompting open-ended.

---

## Retuning for a different budget

Everything cost-related is in the agent frontmatter. To shift the whole system cheaper,
edit `model:`/`effort:` in `agents/t*.md` — the rubric, the commands, and the marker
grammar are unchanged. Two sensible variants:

- **Cheaper:** T3 → `sonnet`/`high`, T4 → `opus`/`medium`. Keeps five tiers, moves the
  Opus boundary up one rung.
- **Fewer tiers:** delete T1 and T3, leaving lookup / bounded / hard / inline. The
  rubric's edges are where most mis-ranking happens, so fewer edges can mean fewer misses.

If you change the tier→agent mapping, update the dispatch table in `commands/next.md` to
match — that table is what actually routes.

---

## Generated content

Everything except this README is generated by
`~/python-tui-lib/scripts/bundle-tiered-todo.sh` from the live files under `~/.claude/`
and `~/python-tui-lib/`. `MANIFEST.md` lists each bundled path and its source.

**Do not edit the generated copies.** Edit the source, then re-run the bundler
(`task bundle-todo`, or `bundle-tiered-todo.sh --check` to see whether the bundle is
stale). A second editable copy is the exact drift this system exists to eliminate.
