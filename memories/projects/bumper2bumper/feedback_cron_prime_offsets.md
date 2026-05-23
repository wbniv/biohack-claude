---
name: cron jobs offset by prime minutes (5 < p < 59), never on the hour
description: When scheduling any cron, never use minute=0 (top of hour). Offset by a prime minute strictly between 5 and 59 to avoid the thundering-herd / common-time-collision pattern. Rule applies to the minute field only.
type: feedback
originSessionId: 7d73bad1-7ea7-4c96-a00e-df4732577a1f
---
When scheduling any cron expression — GitHub Actions, AWS EventBridge, system crontab, k8s CronJob, anywhere — never use `0 ...` (minute=0, top of hour). Use a prime-minute offset instead.

Rule applies to the **minute field only**. Hour, day, weekday fields can be whatever the schedule actually needs.

Acceptable primes (5 < p < 59): 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53. (2, 3, 5 are too close to the top of the current hour; 59 is too close to the top of the next hour. Both buckets land in or near the same thundering-herd window.)

Examples (good):
- `7 * * * *`        — every hour at :07
- `13 */8 * * *`     — every 8 hours at :13 of the hour
- `47 3 * * 1`       — Mondays at 03:47 (minute prime; hour can be anything)
- `*/13 * * * *`     — every 13 minutes (prime cadence is also fine)

Examples (bad):
- `0 * * * *`        — top of every hour, collides with every other "default" cron
- `0 12 * * 1`       — Mondays at noon
- `*/15 * * * *`     — every 15 min on the quarter-hour
- `3 * * * *`        — too close to the top (prime, but < 6)

**Why:** "on the hour" is the most common cron offset; everyone else's logging, backup, billing-rollup, scheduled-deploy, and `0 0 * * *` daily-job lands at minute 0. Stacking ours there competes for the same cloud capacity / API rate-limit / log-channel resources, hits provider throttles harder, and makes failures attributable across systems harder to disentangle. A prime > 5 is unlikely to collide with anything else's default.

**How to apply:** when adding any new cron-triggered job, pick a minute-field prime > 5. Mention the prime in a code comment if non-obvious. When editing an existing on-the-hour cron, take the opportunity to fix it. User stated this rule 2026-05-10 while reviewing a `0 */8 * * *` schedule, and clarified it's minute-field-only (hour/day/etc. unchanged) and primes > 5 only.
