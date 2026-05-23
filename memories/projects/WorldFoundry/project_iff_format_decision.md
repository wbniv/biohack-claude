---
name: .iff.txt is first-class format
description: Decision that .iff.txt and binary .iff are equivalent, interchangeable, and round-trippable
type: project
originSessionId: c43d61b9-ad28-4de2-8df6-bd7d7eb0f22c
---
`.iff.txt` is a first-class storage format, not a debug artifact.

**Why:** The two formats are losslessly interchangeable: `iffcomp` compiles `.iff.txt` → `.iff`; `iffdump -f-` decompiles `.iff` → `.iff.txt`. This is already proven by the existing tools.

**How to apply:**
- Blender import must accept both `.iff.txt` and binary `.iff` as equivalent sources
- `wf_attr_serialize` should treat the two formats symmetrically
- Exporting `.iff.txt` from Blender is the primary path; binary `.iff` is either produced via `iffcomp` afterward or via a future native Rust writer (`wf_iff` crate)
- Do not treat `.iff.txt` as a lesser or transitional format
