---
name: Don't auto-start the Flutter dev server
description: User runs the Flutter dev server in their own terminal; Claude shouldn't preemptively kill/restart it
type: feedback
originSessionId: cdfc8cd0-590a-442d-90a0-d695bda66511
---
Don't preemptively kill or restart the Flutter dev server (`task run-web-lan`, `task run-web`, `task run-chrome`). The user runs it themselves so the foreground output is in their shell.

**Why:** User said "I thought I was starting the server now, heh" after Claude had been killing/restarting `flutter run` automatically across multiple turns. Owning the dev-server lifecycle is a workflow they want to keep.

**How to apply:**
- After making Flutter code changes, just say "restart the dev server when you're ready" — don't issue `task run-web-lan` yourself.
- Exception: if the user explicitly says "restart it" / "start it" / "kill the dev server", do it.
- The Serverpod backend (`task serve`) is different — it has historically been left running in a detached background, and restarting it for migration/model changes has been welcomed when needed. Ask if unsure, but treat it as separate from the Flutter dev-server rule.
- Also fine to *check* what's running (`ss -tlnp`, `pgrep`) — read-only inspection is welcome.
