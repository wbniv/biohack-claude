---
name: feedback_read_prompts
description: Always wrap interactive read prompts in until loops to reject blank input
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98581e12-5331-42f2-81b3-9c1dc824689c
---

Any `read` prompt that expects a non-empty value must be wrapped in an `until` loop that re-prompts on blank input. Never let a bare Enter silently set an empty variable.

**Why:** User accidentally pressed Enter at an R2 credential prompt, setting a blank value and corrupting the bootstrap run — forcing a full restart.

**How to apply:** Any time you write a `read` call in a shell script for a credential, token, or required value, wrap it:

```bash
until [[ -n "${VAR:-}" ]]; do
    read -rsp "  Paste value (input hidden): " VAR; echo
    [[ -z "${VAR:-}" ]] && echo "  (cannot be blank — try again)"
done
```

This applies to all scripts in this repo, not just bootstrap.sh.
