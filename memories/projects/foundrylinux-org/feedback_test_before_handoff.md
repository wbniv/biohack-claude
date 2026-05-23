---
name: feedback_test_before_handoff
description: Always run static checks and smoke tests on any artifact before handing off to Will
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 03faeb93-afb4-48a0-b1bd-f38075dca5f6
---

Before handing off any artifact, run every cheap static check available. Don't assume correctness from reading alone — actually invoke the validators.

**Why:** Caught a broken Taskfile task (KEEP=1 silently not exported as env var) only after Will ran it himself. A single test invocation would have caught it immediately. Applies to anything with a fast static checker, not just Taskfiles.

**How to apply — by artifact type:**

- **Bash scripts:** `bash -n script.sh` (syntax); `shellcheck script.sh` if available
- **Taskfile tasks:** `task <new-task>` with representative args; test both the error path (missing required vars) and happy path (dry-run or --help)
- **JS/Node files:** `node --check file.js`; if it renders HTML, open and visually verify
- **Python:** `python -m py_compile file.py`
- **JSON/YAML:** `python -m json.tool file.json` or `yq . file.yaml`
- **Debian packaging:** `dpkg-deb --info` on the built .deb
- **Docker builds:** at minimum verify the image builds; run with --rm if fast

The bar is: run the fastest check that catches the most likely failure. If it takes under 10 seconds, there's no excuse not to.
