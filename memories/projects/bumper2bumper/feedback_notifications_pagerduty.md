---
name: notification channel preferences — PagerDuty primary, never email
description: Use PagerDuty for production alerts (free account exists). Slack/WhatsApp/Teams may augment. Never use email as a notification channel unless literally no other option exists.
type: feedback
originSessionId: 7d73bad1-7ea7-4c96-a00e-df4732577a1f
---
Notification channel hierarchy for prod alerts (uptime, deploy failures, secret rotation issues, etc.):

- **Primary**: PagerDuty. User already has a free PagerDuty account. All new alerting integrations should target PagerDuty's Events API v2 first (post to a routing-key URL, get visible incidents in PD's interface, escalation policies, on-call rotation, etc.). The PagerDuty Terraform provider exists; service + integration definitions are codifiable end-to-end.
- **Optional augmentation channels** (NOT requested today, can layer later):
  - Slack — outgoing webhook from PagerDuty integration, or direct Slack webhook
  - WhatsApp — interactive (see follow-up plan in `docs/plans/`)
  - Microsoft Teams — webhook integration
  - Discord — webhook integration
- **Never use email as a notification channel** unless there is literally no other option (e.g. one-off legacy integration that can't be upgraded). GitHub Actions' default "send email on workflow failure" doesn't count as a notification channel — explicitly route failures to PagerDuty in the workflow instead.

**Why:** email is high-noise and low-priority for the user. PagerDuty has the right ergonomics for "wake me up when prod is on fire" (severity, ack/resolve, on-call schedules, mobile push). Email gets buried alongside marketing, GitHub default mentions, and routine notifications.

**How to apply:**
- Any new GH Actions workflow that has a "fail loudly" step → POST to PagerDuty Events API v2 on failure, not just rely on GHA email defaults.
- Routing key lives in repo secret `PAGERDUTY_ROUTING_KEY` + mirrored to SSM at `/splitledger/notifications/pagerduty_routing_key` per the SSM-as-backup-of-record rule.
- Define the PagerDuty service + integration via the [`PagerDuty/pagerduty` Terraform provider](https://registry.terraform.io/providers/PagerDuty/pagerduty/latest/docs) (codifiable; no manual dashboard setup beyond the initial account).
- For interactive channels (WhatsApp etc.), the user wants two-way: notification + reply-to-affect-repairs. Track in a separate plan.

User stated this rule 2026-05-10 while reviewing a "GitHub email on workflow failure" mention in the mvp-breakage detection plan.
