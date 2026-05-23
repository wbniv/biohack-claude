---
name: Give full details when delegating
description: When telling the user to do something, include exact commands, paths, container names, and URLs — never "via your normal workflow" or "check the dashboard"
type: feedback
originSessionId: f6adfe21-ba43-4e9a-9b99-14458e233fa2
---
When asking the user to do something, include all concrete details: exact commands (with every argument), full file paths, full URLs, container names, AWS Console deep-links. Never say "via your normal task wrapper", "stop your services", "check the dashboard", or "see the docs" without the actual command/link.

**Why:** Vague delegation forces the user to mentally translate "your normal X" into specifics — which defeats the whole point of having a helpful collaborator. Especially painful when I already have the data (e.g., container names from a recent `docker ps`) but didn't surface it. The user explicitly called this out twice in one turn ("give me all the fucking details!" and again "URLs especially!") — strong corrective signal.

**How to apply:** Before delegating, ask: *would a stranger reading this know exactly what to type / click / open?* If not, expand. Examples:
- Bad: "stop your containers"  → Good: `docker stop splitledger-redis splitledger-redis-test splitledger-postgres splitledger-postgres-test`
- Bad: "check the AWS Console" → Good: full deep-link URL with region + service path
- Bad: "your normal task wrapper" → Good: actual `task <name>` from a Taskfile, or just the underlying command
- Bad: "see the docs" → Good: full URL to the specific page/anchor

Also surface anything I have on hand that saves the user a lookup (already-discovered container names, recent terminal output, paths from earlier in the session).
