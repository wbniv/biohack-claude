---
name: Use task tracking proactively
description: User has flagged a recurring pattern of ignoring TaskCreate/TaskUpdate; reach for it on multi-step work without being prompted
type: feedback
originSessionId: 7a75d2d6-3cbc-48c2-b163-993638e3b490
---
When a request will span more than ~3 tool calls or includes multiple discrete
sub-asks (research + iterate + repeat), start with **TaskCreate** to lay out the
sub-tasks, then **TaskUpdate** as each completes. Don't wait for the
auto-reminder — by the time it fires, the task list is already overdue.

**Why:** User has explicitly called out the pattern of repeatedly ignoring the
harness's task-tool reminders. Treating those reminders as system noise instead
of course corrections is the bug; the fix is to make task creation a default at
the start of multi-step arcs, not a reaction.

**How to apply:**
- At the start of any task that will involve research + multiple file edits +
  iteration (e.g., the "find cheapest registrar" arc with 5+ rounds of plan
  edits), create a TaskList up front.
- Update tasks as I go — mark in_progress when starting, completed when done.
- For genuinely single-step requests (one edit, one lookup), skip it — task
  tracking should not become ceremony.
- If the user adds new sub-asks mid-flow ("also add worldfoundry.org", "also
  the email question"), append them to the task list rather than just absorbing
  them silently.
