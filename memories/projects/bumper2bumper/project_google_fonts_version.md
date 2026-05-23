---
name: google_fonts must be 8.x for Geist + Geist Mono
description: SplitLedger uses Geist + Geist Mono via google_fonts; the 6.x version doesn't ship them, runtime fails with 'No font family by name Geist was found'
type: project
originSessionId: 47825233-5074-4be9-84bc-31c52ada7d4e
---
The SplitLedger redesign uses **Geist** (UI), **Fraunces** (display), and **Geist Mono** (tabular money) via the `google_fonts` package. **Geist + Geist Mono only ship in `google_fonts: ^8.0.0` and later.**

**Why:** The `^6.2.1` constraint we initially picked installs 6.3.3, which predates Geist's addition to the package's `families_supported` list. The `analyze` step is happy because `GoogleFonts.getFont('Geist')` is dynamic — the failure is at runtime: a red screen with `Exception: No font family by name 'Geist' was found.`

**How to apply:** If `pubspec.yaml` shows `google_fonts: ^6.x`, bump to `^8.0.0`. If a future redesign adds another font, verify it's in `~/.pub-cache/hosted/pub.dev/google_fonts-<version>/generator/families_supported` before assuming it works. Fraunces has been supported since 6.x, so it's not a constraint.
