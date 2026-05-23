---
name: auto-open md files in browser
description: After writing or editing any .md file, always open it in the browser with xdg-open. Also responds to explicit "md <filename>" command.
type: feedback
originSessionId: eb231410-0aea-40fe-ae32-0051d1fe1e55
---
After writing or editing any `.md` file as part of a prompt, always open it using `md-to-pdf.sh` (at `/home/will/.local/bin/md-to-pdf.sh`) — without waiting to be asked. This script converts markdown to self-contained HTML (with rendered mermaid diagrams via mermaid.ink and embedded images) and opens it in the browser. If multiple `.md` files were written, open the primary one. `md <filename>` typed explicitly also runs this script.

**Why:** `md-to-pdf.sh` renders mermaid diagrams and embeds images; plain `xdg-open` on a `.md` file does not. User wants fully rendered output in the browser after every write.

**How to apply:** Any prompt that writes or edits a `.md` file → finish the work → `cd /path/to/file/dir && /home/will/.local/bin/md-to-pdf.sh <filename>` as the last step. Run from the file's directory so relative image paths resolve correctly.
