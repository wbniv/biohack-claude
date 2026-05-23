# Memory Index

- [Copy / pitch style defaults](copy-style-pitches.md) — when user delegates, prefer outcome-stated headlines, tight single-audience focus, aggressive artifact removal
- [Commit at confirmation](feedback-commit-at-confirmation.md) — "looks good"/"let's keep it"/"perfect" ends an iteration: commit that turn, don't ask
- [Illustration style: 3D Pixar, not flat vector](feedback-illustration-style.md) — for Indri character/mascot art, prefer Pixar-render aesthetic; flat-edge brand applies to UI only
- [Plan-first before code](feedback-plan-first-before-code.md) — write plan to `docs/plans/` even when user seems impatient; verbal-only plans vanish in crashes
- [Preview plans in browser, not terminal](feedback-plan-preview-in-browser.md) — write plan to `docs/plans/`, then `task md` to render; terminal ExitPlanMode preview is unreadable
- [Cloudflare _headers merges rules](feedback-cloudflare-headers-merge.md) — WSA _headers accumulates all matching rules; never use `/*` catch-all with specific path rules for same header; use Worker instead
- [Forced reflow on first paint](feedback-forced-reflow-first-paint.md) — scripts that read layout (scrollY/innerHeight/getBoundingClientRect) + write styles stall first paint; skip when default applies, else defer with requestIdleCallback
- [Render design artifacts, don't describe them](feedback-render-design-artifacts.md) — icons, swatches, type samples must be rendered as actual HTML in design docs; text substitutes (icon names, hex strings) are not acceptable
- [Project-scoped state, not GH-org-scoped](feedback-project-scoped-state.md) — secrets buckets, bootstrap caches, CF tokens scope off `<zone-slug>`/`<CUSTOM_DOMAIN>`, never off `${GH_ORG}` — wbniv hosts multiple projects that must not collide
- [Apt repos under wbniv](project-apt-repos-on-cloudflare.md) — current: apt.worldfoundry.org, apt.indri.studio; planned: apt.biohack.net — naming convention + cross-repo isolation rules

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
