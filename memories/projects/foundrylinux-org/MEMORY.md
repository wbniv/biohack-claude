# Memory Index

- [site/index.html is generated — never edit directly](feedback_site_generated_file.md) — edit site/*.jsx or scripts/ssr-render.js, then run task site-build.
- [Iterate the /package skill as we package](feedback_package_skill_iterate.md) — every real /package run is a feedback loop for the skill itself; commit the refinement alongside the package.
- [Always build packages in Docker containers](feedback_build_in_containers.md) — never on the host; host deps silently satisfy Build-Depends and mask CI failures.
- [Update new-web-apt-repo skill during each run](feedback_update_skill_during_run.md) — every real apt repo bootstrap is a feedback loop; update SKILL.md with gaps/corrections found.
- [Say "non-redistributable", not "copyrighted"](feedback_copyright_vs_redistributable.md) — GPL code is copyrighted too; the multiverse/image issue is redistribution rights, not copyright.
- [Cloudflare token/credential names](project_cloudflare_credentials.md) — actual names unknown; never assert from script defaults — ask Will and record here.
- [Don't assert infra names from script defaults](feedback_verify_infra_names.md) — script defaults mean nothing; record actual names as Will confirms them.
- [Dropped packages → add TODO to research + repackage](feedback_dropped_packages_todo.md) — when removing a dep because it's gone from Ubuntu, add TODO entries for why it was dropped and whether to package it ourselves.
- [Smoke-test tasks and scripts before handoff](feedback_test_before_handoff.md) — run every new task/script at least once before committing; catch wiring bugs before Will does.
- [Always smoke-test after uploads automatically](feedback_smoke_test_after_upload.md) — never ask; curl remote checksum, compare to local, verify size. PASS before proceeding.
- [Foundry Linux audience: game devs new to Linux](project_foundry_audience.md) — NOT traditional Linux users; they don't care about Linux, it's just the platform. Frame UX/hosting as "downloading a game tool", not "downloading a distro".
- [VM downloads are a planned distribution channel](project_vm_distribution.md) — VirtualBox/VMware/QEMU rows are intentional strategy, not placeholders. Add alongside, never replace.

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
