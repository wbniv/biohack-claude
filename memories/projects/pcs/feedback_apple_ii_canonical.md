---
name: feedback-apple-ii-canonical
description: "Always write \"Apple II\" (not \"Apple ][\" or \"Apple 2\") in prose; use \"apple-ii\" for identifiers, paths, and slugs."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8887cdb3-0b75-4440-acab-258805586b3d
---

Always write **Apple II** in prose, docs, comments, and commit messages. Never `Apple ][`, `Apple 2`, `Apple //`, or `Apple 2e/IIe` mixed forms (except when referring to specific models that genuinely had those names in branding, like "Apple //e" on its keyboard).

For identifiers, file paths, directory names, and URL slugs: use lowercase kebab `apple-ii` (e.g. `apple-ii-tables/`, `2026-05-17-apple-ii-dos-33-disk-format.md`). The "ii" form is the canonical transliteration of "II".

**Why:** User asked for consistency after seeing `Apple ][` and `Apple 2` variants drift in. They want one canonical form everywhere.

**How to apply:** When writing or editing any text in this project, normalize to "Apple II" / `apple-ii`. Don't silently rewrite the user's own past messages or quoted material, but everything else should conform.
