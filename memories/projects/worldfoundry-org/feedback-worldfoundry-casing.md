---
name: worldfoundry-casing
description: "Use \"WorldFoundry\" (camelcase) not \"Worldfoundry\" when a space won't fit; brand convention"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0528273f-09be-4fa8-bbdb-9087f55afc36
---

When the brand name appears without a space, case it as **WorldFoundry**
(capital W, capital F), not "Worldfoundry" or "worldfoundry". The
project's preferred spacing is "World Foundry" (two words); if that
won't fit a slot — package maintainer string, identifier, filename
— camelcase the two words rather than lowercase the second.

**Why:** Brand consistency. The user surfaced this after spotting
"Worldfoundry Packages" in the wf-blender deb maintainer field; they
explicitly said "remember this".

**How to apply:**
- Maintainer fields: `WorldFoundry Packages <packages@worldfoundry.org>`
  (the domain stays lowercase — DNS doesn't care, but the
  human-readable name is camelcase).
- `gen-index.py` `WORDMARK` is already correct: `"WorldFoundry"`.
- Identifiers that already exist lowercase (`worldfoundry.org` the
  domain, `worldfoundry-apt` the R2 bucket, `worldfoundry.gpg` the
  keyring filename) are fine as-is — DNS / S3 / file paths conventionally
  use lowercase. The rule is about the human-readable brand name.
- When writing new commit messages, READMEs, manpages, or
  `debian/control` Description fields, write `World Foundry` if there's
  room or `WorldFoundry` if there isn't (e.g. as a single identifier).

Audit targets where the typo is likely to recur:
- `apt/packages/*/debian/{control,changelog,copyright}` Maintainer
  lines
- `docs/plans/*.md` prose
- `apt/gen/config.py` already correct
