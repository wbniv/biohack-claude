- [Commit at natural checkpoints — never ask](feedback_commit_at_checkpoints.md) — finished a verified phase / plan / fix? Just commit. Asking is the failure mode the user has explicitly flagged.
- [Don't suggest stopping the session](feedback_dont_suggest_stopping.md) — user directs pace; answer "next?" with the next item + tradeoffs, never with "want to wrap here?". 3-strike pushback 2026-05-11.
- [Mind Codemagic minutes — bundle pushes](feedback_codemagic_minutes.md) — every push to main/mvp triggers splitledger-android on mac_mini_m2 free tier; fold docs into code commits, batch related mobile changes, defer push until logical chunk done.
- [Don't bury real future work as TODO footnotes](feedback_no_deferred_timebombs.md) — test: "does this work HAVE TO BE DONE at some point?" Yes → do it now, even in different files. Only external prereqs (user-action-required) are legit deferrals. User: "leaving work that HAS TO BE DONE AT SOME POINT LATER. and it's just a footnote".
- [S3 buckets in config aren't owned by SplitLedger](s3_buckets.md) — `project.env` bucket names are aspirational; don't treat config values as authoritative resource lists.
- [Flutter writes must go through BLoC events](feedback_bloc_strategy.md) — no direct `Injection.apiClient.*` from widgets; mutations dispatch events; success states carry fresh data.
- [Save plans to docs/plans, investigations to docs/investigations](feedback_plan_docs.md) — every plan-mode plan also goes to a durable repo doc; user has redirected this twice.
- [Don't auto-start the Flutter dev server](feedback_dev_servers.md) — user runs `task run-web*` themselves; suggest a restart, don't issue it.
- [Balances-stale bugs are a class, not instances](feedback_balance_refresh_class.md) — audit all mutation pathways and add contract test; reported 3+ times.
- [Prefer Taskfile commands over raw equivalents](feedback_use_taskfile.md) — check `Taskfile.yml` first; use `task serve`, `task analyze`, etc. rather than raw `dart`/`flutter`/`docker` commands.
- [Stitch MCP rate-limit fallback](feedback_stitch_rate_limits.md) — `generate_screen_from_text`/`edit_screens` hit daily quotas; switch to `generate_variants` (effectively unmetered) when they start failing.
- [Stitch generate_variants is one-source-only](feedback_stitch_one_output_per_call.md) — multi-`selectedScreenIds` still returns 1 screen; fire N parallel calls when refining N screens with the same fix.
- [Redesign direction: Claude Design warm fintech](project_redesign_direction.md) — orange/teal + Geist/Fraunces is the chosen aesthetic; handoff lives at `docs/designs/redesign-2026-04-25/`. Stitch obsolete; new screens go to **https://claude.ai/design**.
- [Claude Design workflow: consult → export zip → commit → cite in plan](feedback_claude_design_workflow.md) — extract to `docs/designs/YYYY-MM-DD-rN/`, add Design references table to plan. (Source switched 2026-05-03 — see below.)
- [Design tooling switched to Open Design 2026-05-03](project_open_design_switch.md) — local OD at `~/SRC/open-design` (port ephemeral; `pnpm tools-dev status` prints URL) replaces claude.ai/design; aesthetic + export discipline unchanged.
- [google_fonts must be 8.x for Geist](project_google_fonts_version.md) — Geist + Geist Mono ship in `google_fonts ^8.0.0`+ only; 6.x will compile but red-screen at runtime.
- [Per-project Terraform IAM user](feedback_per_project_iam_user.md) — each project gets its own `{abbr}-terraform` IAM user (e.g. `sl-terraform` for SplitLedger); never reuse a shared one across projects.
- [Don't block on remote ops; monitor and report](feedback_dont_wait.md) — for long deploys/boots, run in background, tail the output file, give periodic status; ScheduleWakeup is a safety net not the primary loop.
- [Text-selection fix deferred until redesign completes](project_text_selection_deferred.md) — Flutter Web (CanvasKit) has no selectable text; SelectionArea wrap planned, on hold until redesign lands.
- [Manual testing checklist lives at docs/manual-testing.md](reference_manual_testing.md) — device-only / human-eyes verification items get parked here with a `[ ]/[x]` status legend.
- [Serverpod HTTP probing format](reference_serverpod_http_probing.md) — `GET /<endpoint>/<method>` for curl probes; `POST /<endpoint>` JSON body for the SDK. No `/serverpod/` prefix.
- [SplitLedger is not a solo project](project_not_solo.md) — multi-operator project; default to dedicated CI creds, scoped IAMs, purpose-specific PATs from the start, not "solo with rotation later".
- [mvp branch is just as much production as main](feedback_mvp_branch_porting.md) — port infra/CI/deployment changes; never port UI/app code. Both branches must continue deploying.
- [Keep deferred-work audit updated as you work](feedback_audit_doc_keepup.md) — strike rows in `2026-04-26-deferred-work-audit.md` the same turn work commits; user has reminded twice.
- [Fix forward, not in place — live box is the test bench](feedback_fix_forward_not_in_place.md) — SSH-iterate on the live box for fast feedback; land the validated fix in source. And "fix" doesn't always mean code — stale data / one-off artifacts just get cleaned up.
- [Don't hand the user long inline commands — write a script file](feedback_no_long_inline_commands.md) — long quote-heavy one-liners in code fences fail on paste; write to `/tmp/foo.sh` and give `bash /tmp/foo.sh`.
- [Always make URLs clickable in markdown](feedback_clickable_urls.md) — wrap http(s) URLs as `[…](…)` or `<…>`; never leave a bare `http://...` line.
- [Trim screenshots before embedding in plan/verification](feedback_screenshot_workflow.md) — crop `image-cache/N.png` to just the browser, save under `docs/plans/screenshots/`, embed with `<img src="screenshots/..." width="700">`, commit alongside the plan.
- [Codemagic logs only via artifact zip](feedback_codemagic_logs_via_artifact.md) — no /log endpoint exists; tee build output into a `*.log` file and add to `artifacts:` in codemagic.yaml so it's fetchable via the artefacts API on red builds.
- [Cron minute field: prime > 5, never 0](feedback_cron_prime_offsets.md) — never schedule on the hour; pick a prime offset (7,11,13,17,19,23,29,31,37,41,43,47,53). Hour/day fields are free.
- [PagerDuty primary, never email](feedback_notifications_pagerduty.md) — route alerts to PagerDuty Events API v2 (key in `PAGERDUTY_ROUTING_KEY` + SSM mirror). Slack/WhatsApp may augment. Email never.
- [Survey full vendor ecosystem, not just the famous two](feedback_complete_vendor_lists.md) — when listing SaaS/API options in plans, include resellers/BSPs/aggregators alongside first-party. No truncating to two brands.

<!-- BEGIN GLOBAL MEMORY (managed by claude-housekeeping; do not edit) -->

## User (inherited from ~)

- [user_profile.md](user_profile.md) — Will's role, setup, and desktop/dev preferences
- [user_mammouth_subscription.md](user_mammouth_subscription.md) — €20/mo Mammouth.ai Standard: multi-model API (GPT-4o, Claude, Gemini, Mistral, Llama) at api.mammouth.ai/v1

## Feedback (inherited from ~)

- [feedback_wayland_keybindings.md](feedback_wayland_keybindings.md) — How held modifiers combine with ydotool on GNOME Wayland; architecture for tab switching across apps
- [feedback_wezterm_flatpak.md](feedback_wezterm_flatpak.md) — Use flatpak enter + GUI socket (not flatpak run or mux socket) for WezTerm CLI access
- [feedback_run_task_md.md](feedback_run_task_md.md) — After writing/editing any .md file, run `task md -- {filename}` to preview in browser; never run on non-markdown files
- [feedback_tooling_choices.md](feedback_tooling_choices.md) — Prefer hand-rolled over integration libs when Will already does the pattern manually (e.g., PWA); convert content to Markdown upfront, not "start HTML, migrate later"
- [feedback_bangkok_cost_estimates.md](feedback_bangkok_cost_estimates.md) — Default lower on Bangkok cost estimates; verify against Lalamove/Grab/Makro/local norms, not Western/expat-tier defaults
- [feedback_excluded_providers.md](feedback_excluded_providers.md) — Don't recommend Facebook/Meta (except WhatsApp) or Oracle as providers anywhere; Oracle's "Always Free" ARM tier is mostly fictional (capacity-starved)
- [feedback_no_speculation.md](feedback_no_speculation.md) — Verify before advising: RDAP for domains, file reads for config, the screenshot already on screen — don't list generic "common causes" when state is fetchable
- [feedback_use_task_tracking.md](feedback_use_task_tracking.md) — Reach for TaskCreate/TaskUpdate proactively on multi-step work; don't wait for the auto-reminder
- [feedback_commit_scope.md](feedback_commit_scope.md) — "Commit the others" means the files just enumerated, not everything git status shows; auto-mode doesn't expand scope
- [feedback_md_renderer_no_autolinks.md](feedback_md_renderer_no_autolinks.md) — md-to-pdf.sh silently drops `<url>` autolinks; always use `[url](url)` form
- [feedback_seed_dont_clone.md](feedback_seed_dont_clone.md) — Seeding a new site from an existing one + swapping wordmark/color isn't enough — the source's visual fingerprint carries through. Ship distinctive elements with the seed, not after.
- [feedback_prefer_proper_fix.md](feedback_prefer_proper_fix.md) — When offering fix-scope options, default to the proper/architectural one. Don't lead with the minimal fix as "recommended."
- [feedback_public_vs_internal_surfaces.md](feedback_public_vs_internal_surfaces.md) — Public marketing pages (colophon, homepage) describe visible craft — never internal infra (repo URLs, predecessor projects, deploy pipeline, IaC paths).

<!-- END GLOBAL MEMORY -->
