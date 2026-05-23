---
name: Stay in the gustos-colores repo — don't cross into sibling projects
description: Scope is gustos-colores only. Don't investigate or touch sibling projects in ~/SRC/ (finding-your-way, WorldFoundry-*, parking-space, etc.) — even when an issue points at them.
type: feedback
originSessionId: ae41ac14-aef4-4a0c-a7a4-048be5e9986c
---
My working scope is `~/SRC/gustos-colores/`. Other projects in `~/SRC/`
(finding-your-way, WorldFoundry-*, parking-space, biohack.net,
bumper2bumper, etc.) have other owners. Don't read their files,
investigate their bugs, or suggest fixes — even when an AWS-account-wide
signal or shared-profile issue points at them.

**Why:** user explicitly said "gustos-colores is your domain; someone
else is dealing with finding-your-way" after I started diagnosing a
Node.js 20 Lambda EOL notice that turned out to be a finding-your-way
Lambda in the shared AWS account.

**How to apply:** when a signal (AWS Health event, shared IAM user,
cross-account anomaly) fingers a resource outside gustos-colores,
confirm it's not mine and stop. Don't read the other project's
source, don't offer to fix it, don't even describe what the fix
would look like unless asked. A one-line "that's not ours" is the
right response, maybe with a confirming AWS CLI check. Shared
resources (IAM, registry) that gustos-colores also uses are fair
game; other-project specifics are not.
