# vendor/ — Third-party plugin evaluation

This directory holds third-party Claude Code plugins under evaluation as git submodules.
Each submodule has an `EVALUATION.md` at its root tracking status and notes.

## Lifecycle

```
state             meaning
──────────────    ──────────────────────────────────────────────────────────
evaluating        submodule added, actively reading and trying it
kept-reference    good as-is — promoted to marketplace.json as upstream ref
kept-fork         useful with my changes — files copied to plugins/<name>/;
                  upstream PR open or merged
rejected          not useful — submodule removed; EVALUATION.md archived in
                  vendor/_rejected/ to avoid re-evaluating later
```

## Rating axes (both optional — use either, both, or neither)

| Field    | Values                                          |
|----------|-------------------------------------------------|
| `tier`   | `essential` · `recommended` · `niche` · `curious` · `avoid` |
| `stars`  | 1–5                                             |

Tier answers "would I recommend this to someone in my position?" — Stars answer "how good is the execution?" A skill can be 5-star but `niche`, or 3-star but `essential`.

## EVALUATION.md schema

```yaml
---
plugin: their-skill
upstream: https://github.com/them/their-skill
state: kept-reference      # see lifecycle table above
tier: recommended          # optional
stars: 4                   # optional
last-reviewed: 2026-05-23
last-upstream-commit: abc1234
---

## What it does
[1-2 sentences]

## Notes
- ✓ [strengths]
- ✗ [weaknesses or caveats]

## My modifications
[empty unless state=kept-fork; link the upstream PR if open]

## Re-review trigger
[e.g. "next major upstream version" | "2026-11" | "if I start using X again"]
```

For `state: rejected`, replace `## Notes` with `rejection-reasons` in the frontmatter:

```yaml
rejection-reasons:
  - "reason one"
  - "reason two"
```

## Operations

```bash
# Add for evaluation
git submodule add https://github.com/them/their-skill vendor/their-skill
$EDITOR vendor/their-skill/EVALUATION.md     # state: evaluating

# Promote to kept-reference
# 1. Set state/tier/stars/last-reviewed in EVALUATION.md
# 2. Add to .claude-plugin/marketplace.json:
#    { "name": "their-skill", "source": { "source": "github", "repo": "them/their-skill" }, ... }
# 3. Run: task gen-marketplace

# Promote to kept-fork
# 1. Copy plugin files to plugins/<name>/
# 2. Attribute upstream in plugins/<name>/README.md
# 3. Open upstream PR with improvements
# 4. Set state: kept-fork in EVALUATION.md, link the PR

# Reject
# 1. Set state: rejected, fill rejection-reasons in frontmatter
# 2. mv vendor/<name>/EVALUATION.md vendor/_rejected/<name>.md
# 3. git submodule deinit vendor/<name> && git rm vendor/<name>
# 4. git commit
```

## _rejected/

Archived EVALUATION.md files from rejected plugins.
Not included in marketplace.json — kept so you don't re-evaluate the same skill later.
Run `grep -l "hardcoded paths" vendor/_rejected/*.md` to find rejection patterns.
