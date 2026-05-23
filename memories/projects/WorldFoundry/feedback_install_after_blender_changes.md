---
name: Run install.sh after wf_blender changes
description: Always run wftools/wf_blender/install.sh after editing any wf_blender Python file
type: feedback
originSessionId: c43d61b9-ad28-4de2-8df6-bd7d7eb0f22c
---
After editing any file in `wftools/wf_blender/` (panels.py, operators.py, etc.), run:

```bash
bash wftools/wf_blender/install.sh
```

**Why:** Blender reads from `~/.config/blender/5.1/scripts/addons/wf_blender/` — edits to the source tree aren't visible until installed. User expects this to happen automatically after code changes.

**How to apply:** Any time a wf_blender Python file is edited, run install.sh immediately after without being asked.
