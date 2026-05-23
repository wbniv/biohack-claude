---
name: Level files with mesh geometry
description: Which .lev files have actual mesh .iff references (not just bounding boxes)
type: project
originSessionId: c2a51ce3-3e14-44b4-99c9-977b15ecd216
---
Levels with real mesh geometry (non-empty Mesh Name fields):

- `wflevels/primitives/primitives.lev` — 1 mesh ref: `geosphere01.iff` (last object, line 3223)
- `wflevels/whitestar/whitestar.lev` — 1 mesh ref: `whitestar.iff` (confirmed working in Blender)
- `wflevels/snowgoons/snowgoons.lev` — 5 mesh refs (box01.iff, house.iff, player.iff, etc.)
- `wflevels/superhero/superhero.lev` — 21 mesh refs
- `wflevels/bubba/bubba.lev` — 766 mesh refs (very dense)
- `wflevels/3dtext/3dtext.lev` — 4 mesh refs
- `wflevels/cubemenu/cubemenu.lev` — 1 mesh ref

**Why:** Mesh geometry import (Phase 2) was verified working using whitestar.lev.
Objects without a Mesh Name fall back to bounding-box geometry.
</content>
</invoke>