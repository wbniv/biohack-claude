---
name: Don't hand the user long quoted command lines — write a script file instead
description: When the user needs to run a command, write it to a script file and give them a one-word `bash <path>` invocation; never paste long quote-heavy one-liners
type: feedback
originSessionId: 11d5d0e4-4efa-48be-a468-40eb56d4cd62
---
When the user needs to run a shell command themselves (because the sandbox blocks me, or they need to do it interactively), do **not** hand back a long quote-heavy one-liner inside a markdown code fence. They consistently fail to paste-and-run cleanly:
- Code-fence whitespace gets copied along with the command and breaks the `!` shell-mode prefix.
- Terminal wrap splits the line at column boundaries, breaking shell parsing.
- Nested single/double quotes (especially around JSON or jq filters) silently mis-parse.
- Backticks inside the command get interpreted by the outer shell.

Instead: write the command to a file (e.g. `/tmp/<topic>.sh`) using the Write tool, then give the user a single short invocation like `! bash /tmp/<topic>.sh`. The script file holds the gnarly quoting; the user copies one trivially-correct line.

**Why:** User explicit feedback 2026-05-03 — "you always give me command lines that don't work, that's why i rarely ask you for them." Pattern observed across multiple sessions: jq pipelines, gcloud commands, multi-stage shell with `&&` chains. When given as inline code blocks they fail. When given as `bash /tmp/foo.sh` they succeed.

**How to apply:**
- Threshold: anything over ~80 characters, anything with nested quotes, anything with `$(...)` or backticks, anything with embedded JSON, anything that wraps in the chat display.
- Always include `set -euo pipefail` at the top of the script (per `~/SRC/CLAUDE.md`).
- Echo a confirmation at the end of the script so the user can see it succeeded.
- Don't bother with the script-file pattern for trivial commands like `git status` or `task serve` — just give those as inline.
