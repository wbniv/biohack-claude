---
name: feedback-vendor-external-source
description: "Vendor third-party source code (e.g. Bill Budge's PCS_AppleII / PCS_Atari800) as git submodules under vendor/, not by repeated curl from raw.githubusercontent.com."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8887cdb3-0b75-4440-acab-258805586b3d
---

When doing reverse engineering against an external open-source codebase, **vendor it as a git submodule under `vendor/`** instead of `curl`-ing raw GitHub URLs over and over.

**Why:** User pushed back on me curling `raw.githubusercontent.com/billbudge/PCS_AppleII/...` for the Nth time during PCS RE work. `curl` is slow per-query, doesn't work offline, can't be cross-grep'd, and every grep is one-shot. Submodules pin a known commit SHA for reproducibility, allow local `grep -rn` across all source files at once, and survive network outages.

**How to apply:**
- For any project that needs sustained RE / reference against an external repo, add `git submodule add <url> vendor/<name>` early in the work.
- If the existing project doesn't have a `vendor/` dir yet, create it.
- Use `grep -rn "PATTERN" vendor/<name>/` for searches.
- Document in README that contributors need `git submodule update --init --recursive` after cloning.
- For Bill Budge's PCS specifically: `vendor/PCS_AppleII` (Apple II source) and `vendor/PCS_Atari800` (Atari 800 source) — both MIT-licensed.
