---
name: Run task md on markdown files
description: After writing or editing any .md file, run task md to convert it to HTML and open in browser
type: feedback
originSessionId: 0f72211e-7e22-41ec-933b-0cee31cca321
---
After writing or modifying any `.md` file (plans, docs, investigations, reports, prompts), run `task md -- {filename}` on it. **Never run `task md` on non-markdown files** (`.py`, `.dart`, `.sh`, `.json`, etc.).

**Why:** User wants to preview markdown files in browser immediately after they're written. Running `task md` on Python or other source files is wrong — it passes non-markdown content to the markdown renderer.

**How to apply:** A PostToolUse hook on Write|Edit handles this automatically *only in projects that have it configured* (e.g. parking-space's `.claude/settings.local.json`). In the homedir context (or any project without that hook), run `task md -- {filename}` manually after editing a `.md` file. If manually triggering, only pass `.md` file paths. If you just edited a Python script that generates a `.md` file, run `task md` on the *output* `.md` file, not the script itself.
