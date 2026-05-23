---
name: WF Engine Running Milestone
description: The WF game engine successfully runs and renders the snowgoons level with moving objects
type: project
---

As of 2026-04-14, the WF game engine (`wftools/wf_engine/wf_game`) builds and runs on Linux 64-bit, loading the snowgoons level (L4 in cd.iff) with objects visibly moving on screen.

**Why:** Three runtime bugs were fixed in this session (see level-building.md and plan file for details). The engine reaches the render loop and runs the game loop including camera, physics, and animation.

**How to apply:** The engine is in a working state. Future work should focus on rendering quality, missing animations, and the remaining warnings rather than basic bring-up.

Run command:
```bash
cd wfsource/source/game
LD_LIBRARY_PATH=../../../wftools/wf_engine/libs DISPLAY=:0 ../../../wftools/wf_engine/wf_game
```
