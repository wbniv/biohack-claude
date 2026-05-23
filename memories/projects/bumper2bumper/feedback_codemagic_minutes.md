---
name: Mind Codemagic minutes — bundle pushes, fold docs into code commits
description: Every push to main/mvp triggers splitledger-android on mac_mini_m2 free tier. Doc-only commits waste minutes; bundle into the code commit they describe.
type: feedback
originSessionId: 9c6da41a-dbd8-4926-9c92-073cf1228f03
---
Every push to main (or mvp) triggers the `splitledger-android` Codemagic workflow on `mac_mini_m2`. Free tier has a monthly quota. Each rapid-fire push during a productive day burns through it.

**Why:** User pushback 2026-05-11 ("you need to stop using so many minutes on codemagic.io, heh") after ~16 commits in a single day, several of which were docs-only or audit-doc-bookkeeping that didn't touch anything Codemagic builds.

**How to apply:**
- **Bundle docs into the code commit they describe.** TODO.md / audit-doc updates ride with the code change, not in a separate commit afterward. Same for transcript tails when the transcript is just capturing the prompt that triggered the work.
- **Batch related code changes.** F-4 + F-5 + F-6 + F-7 could have been one mobile commit, not two pushes. A `mobile/` cluster (one push) costs the same Codemagic-wise as a single mobile commit; multiple pushes cost N times.
- **Defer push, not commit.** OK to commit at natural checkpoints during work; the "Commit at natural checkpoints" rule is about commits, not pushes. Pushes wait for an explicit user signal.
- **"Stop pushing until I say resume" is durable, not a one-session nudge.** User confirmed 2026-05-12 ("i still don't want you pushing to codemagic until i say to resume") after I misread it. Treat any pause-pushing signal as in effect across the whole multi-day budget period unless explicitly resumed. Don't push to main/mvp during a paused window — even when a logical chunk wraps. Wait for "push", "resume", "ok to push", or equivalent.
- **Push budget snapshot 2026-05-12:** 490/500 macOS minutes used (Codemagic personal free tier). 10 minutes remaining until calendar-month reset on 2026-06-01 UTC. User has explicitly gated pushes until then. Default assumption for any session before 2026-06-01: pushing remains paused unless the user says otherwise.
- **The "do work yourself, don't defer to user" rule is SEPARATE from the push gate.** Be autonomous about coding work and audit closures; gated only on the push. Both can be true at once: keep working AND don't push.
- **If `codemagic.yaml` has a path filter:** doc-only pushes wouldn't trigger builds. Check whether the current trigger is unfiltered — if so, propose a `mobile/**` + `backend/splitledger_client/**` + `codemagic.yaml` + `infrastructure/aws-lightsail/Caddyfile`-style path filter so doc + backend + infra pushes don't fire Codemagic.
- **Backend-only changes** (services / endpoints / tests under `backend/splitledger_server/`) don't need Codemagic. If the trigger is unfiltered, even those waste minutes — argue strongly for the path filter.
- **End-of-day cadence:** prefer one consolidated end-of-session push over many incremental ones.

The user phrased the pushback lightly ("heh") but it's a real ops cost — Codemagic free tier is finite per month, and a single audit-closure run can burn a meaningful chunk.
