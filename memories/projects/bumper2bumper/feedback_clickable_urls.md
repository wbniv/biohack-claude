---
name: Always make URLs clickable in markdown
description: Wrap http(s) URLs in markdown link syntax so the renderer makes them tappable; never paste bare http://... lines.
type: feedback
originSessionId: e3762679-c1b7-45bd-8a19-56279eef4d47
---
When sharing any URL in chat — localhost dev URLs, docs, dashboards, anything — wrap it in markdown link syntax: `[http://localhost:3000/](http://localhost:3000/)` or `<http://localhost:3000/>`. Never leave a bare `http://...` on its own line.

**Why:** The user reads chat in a renderer that doesn't auto-linkify bare URLs. A plain `http://localhost:3000/` is unclickable, forcing them to copy-paste it into the address bar. Reported with explicit annoyance ("you didn't make the link clickable!?! wtf?").

**How to apply:** Every URL in user-facing output gets the markdown wrap. Includes follow-ups like "open …", "the URL is …", or status replies that mention an endpoint. File paths in this codebase already use `[name](relative/path)` linking — same discipline applies to web URLs.
