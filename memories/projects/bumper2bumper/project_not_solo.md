---
name: SplitLedger is not a solo project
description: Project will have multiple operators; security trade-offs must assume multi-collaborator from the start, not "solo with rotation later"
type: project
originSessionId: 9967ca36-ed6d-4d31-aa2b-fbc7b2722397
---
SplitLedger should be treated as a multi-operator project in development,
not a solo project, even before the second collaborator joins.

**Why:** The user has corrected this framing TWICE now:
- 2026-04-30 (original): "this is not a solo project; it is a project
  in development" — when I tried to defer dedicated CI credentials.
- 2026-05-09: "stop saying 'single operator' --- wtf? we JUST talked
  about this today, smh" — when I used "single operator + admin-bypass
  makes branch protection symbolic" as the rationale to defer it in I-2.

A personal SSH key in repo secrets means anyone with workflow-edit
access can impersonate that human against any host that trusts the
key — including hosts unrelated to this project. And designing
"rotate later, manually" turns secret rotation into permanent debt
the second operator inherits.

**How to apply:** Banned framings — never say or imply any of these
when proposing infra/security shapes:
- "single operator" / "solo operator" / "team-of-one"
- "manual rotation is fine for now"
- "admin-bypass makes [protection] symbolic"
- "we can add [rotation/protection/scoping] later"

Default to the multi-operator-safe AND auto-rotating option as the
*baseline*, even if it costs more setup:
- Mint dedicated CI keypairs, never reuse personal `~/.ssh/id_rsa`
- Use scoped IAM users / OIDC-assumed roles, not personal access keys
- For GitHub auth: GitHub App (mints short-lived installation tokens —
  no PAT to rotate) is the default, NOT Classic PAT. PATs are
  acceptable only with a scheduled rotation workflow that handles
  renewal end-to-end.
- For any long-lived secret (SSH keys, API keys), ship the rotation
  automation in the same PR, not "follow-up TODO." Storage in SSM is
  table stakes; rotation is the actual feature.
- Branch protection / required-status-checks: ship them on by default,
  not "when a 2nd operator joins."

The team-of-one-today framing is wrong; the durable shape is the one
the project will need when there's a second operator, and the cost of
doing it right up front is low. Stop relitigating this each turn.
