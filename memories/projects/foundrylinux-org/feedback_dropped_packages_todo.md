---
name: feedback-dropped-packages-todo
description: "When dropping a package because it's no longer available in Ubuntu, add TODO entries to research why and whether to package it ourselves"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 880e268d-f572-4a85-9862-802108438961
---

When a dependency is dropped from a metapackage because it's no longer available in Ubuntu (e.g. removed from the archive), always add TODO items to research:
1. Why it was dropped from the Ubuntu archive
2. Whether we should package it ourselves in foundry-apt (often yes — if it's actively maintained upstream and useful to game devs)

**Why:** Dropping silently means the feature disappears from the distro with no plan to restore it. The drop should be a temporary workaround, not a permanent removal — unless the upstream is dead.

**How to apply:** In the same commit that removes the dep from `debian/control`, also add entries to `TODO.md` under a "Packaging — dropped packages to investigate" section, naming the package and noting it was dropped from 26.04 and linking to the metapackage version that removed it.
