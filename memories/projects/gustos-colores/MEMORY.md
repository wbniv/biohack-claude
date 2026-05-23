# Memory Index

- [docs/ directory layout](feedback_docs_directory_layout.md) — Plans→`docs/plans/`, investigations→`docs/investigations/`, transcripts→`docs/transcripts/`, prompts→`docs/prompts/YYYY-MM-DD.md`
- [Screenshot drop location](feedback_screenshots.md) — Screenshots sync from phone via Syncthing to `~/SRC/screenshots/`; monitor that dir
- [Terraform state lock diagnosis](feedback_terraform_locks.md) — Never call a TF lock "stale" without `pgrep` first; force-unlocking an active lock corrupts state
- [Fix forward, not in place](feedback_fix_forward.md) — Debug on the instance if needed, but land the fix in source scripts/templates; then cycle the instance to verify
- [CLI-only for rare reverse flows](feedback_cli_for_rare_reverse_flows.md) — Reversals (undo-style) don't need TUI parity; rarity is the justification
- ["Task" means Taskfile](feedback_task_means_taskfile.md) — In this repo, "Task command" = `task <name>` Taskfile entry; default to that interpretation
- [Stay in the gustos-colores repo](feedback_stay_in_repo.md) — Don't investigate or touch sibling projects in ~/SRC/, even when a shared-account signal points at them
- [No j/k as arrow-key alternatives](feedback_no_vim_nav.md) — TUIs use arrow keys only; don't add vim j/k nav
- [Bump and report version on every deploy](feedback_deploy_version.md) — Increment build N in settings_screen.dart before every deploy; report the new version number after
- [TODO.md summary block](feedback_todo_summary_block.md) — Keep "AT A GLANCE" summary at top of TODO.md; refresh it whenever you touch any item below
- [DONE entries are one tight line](feedback_done_section_one_line.md) — Each DONE entry ~120-150 chars; compress long pre-existing entries retroactively when editing TODO.md
- [Give full details when delegating](feedback_full_details_when_delegating.md) — Every delegated step needs exact commands, paths, container names, and URLs — no "via your normal workflow"
- [Apply real engineering standards regardless of solo/dev context](feedback_real_engineering_standards.md) — Don't downgrade severity or defer fixes because "it's just a dev box"; the work is professional and going commercial
- [Reproducibility = "works on a fresh box without my system state"](feedback_reproducible_off_my_box.md) — Every fix must work after `rm -rf laptop && git clone`; daemon.json/keyring/etc-files don't count, prefer repo-level (Dockerfile, Taskfile, IaC)

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
