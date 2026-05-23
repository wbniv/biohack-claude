---
name: Screenshot drop location
description: Where the user drops screenshots from their phone for Claude to read
type: feedback
originSessionId: 832b06fa-9a6a-4da4-ad2a-47d02651b631
---
Screenshots are synced from the user's phone via Syncthing to `~/SRC/screenshots/`. Always monitor that directory when the user says they'll provide a screenshot. Never look in ~/Desktop, ~/Downloads, or ~/Pictures.

**Why:** That's their established workflow — phone screenshots sync there automatically.

**How to apply:** When user says "in the usual place" or "I'll drop a screenshot", monitor `~/SRC/screenshots/` with `inotifywait` or check `ls -t ~/SRC/screenshots/ | head` immediately.
