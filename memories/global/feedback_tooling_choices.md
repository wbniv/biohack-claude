---
name: Prefer hand-rolled over integration libs when Will already does the manual pattern
applies-to: [universal]
description: When Will has built the manual version of a pattern across multiple projects, don't oversell integration-lib convenience; default to the hand-rolled version
type: feedback
originSessionId: c911fa94-81a4-4d65-856d-a010059f407c
---
**Rule:** When proposing tooling for a pattern Will already implements by hand
(PWA service workers + manifests being the canonical example), default to the
hand-rolled approach rather than reaching for an integration library. If the
integration library has real non-convenience advantages, state them honestly and
briefly — don't oversell.

**Why:** Will pushed back on `@vite-pwa/astro` with "we've made several PWA apps
together already and it didn't seem to be painful." Reference projects:
`~/SRC/parking-space` and `~/SRC/gustos-colores`. He finds framework-wrapper convenience
less valuable than a stable, portable, well-understood pattern across projects.

**How to apply:** Before recommending an integration library (vite plugins, framework
integrations, wrapper SDKs), ask: does Will already do this manually in another
project? If yes, lead with the hand-rolled path and only mention the lib if it
adds something real (auto-regenerated config, dev-mode features) — and name the
specific win, not "convenience."

**Related preference:** For content-migration tasks, convert to Markdown upfront
rather than starting with HTML and migrating later — avoid doing the conversion
twice. Established during the Parmenides/finding-your-way plan ("let's just start
with markdown from the beginning").
