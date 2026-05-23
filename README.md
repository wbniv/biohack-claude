# biohack-claude

Will Norris's personal [Claude Code](https://claude.ai/code) marketplace —
techops, design, and productivity plugins from [biohack.net](https://biohack.net).

## Install

```
/plugin marketplace add wbniv/biohack-claude
```

Then install any plugin individually:

```
/plugin install cf-static-site@biohack-claude
/plugin install new-web-apt-repo@biohack-claude
/plugin install package@biohack-claude
# etc.
```

## ⚒ techops

| Plugin | What it does |
|--------|-------------|
| [`cf-static-site`](plugins/cf-static-site/) | Bootstrap a static site on Cloudflare — Workers + Terraform + GH Actions, or plain Pages |
| [`new-web-apt-repo`](plugins/new-web-apt-repo/) | Provision a signed APT repo on Cloudflare R2, backed by aptly + GitHub Actions |
| [`claude-housekeeping`](plugins/claude-housekeeping/) | Audit Claude Code artifacts for drift — skills, hooks, memories, settings, plans |
| [`package`](plugins/package/) | Package a program as a Debian-policy-compliant .deb for a foundry-style apt repo |
| [`iam-bootstrap`](plugins/iam-bootstrap/) | Set up per-project AWS IAM — Terraform user, state backend, self-narrowing permissions |
| [`cf-domain-setup`](plugins/cf-domain-setup/) | Add a domain to Cloudflare — scoped token, zone creation, activation polling |
| [`aws-billing-tags`](plugins/aws-billing-tags/) | Set up AWS cost tracking, billing tags, budget alerts, and Cost Explorer |

## ✦ design

| Plugin | What it does |
|--------|-------------|
| [`import-claude-design`](plugins/import-claude-design/) | Import a Claude Design export zip into site/ and deploy via tag-triggered CI |

## 🐚 GNOME extensions

| Extension | What it does |
|-----------|-------------|
| [`Claude Usage Indicator`](gnome/) | Shows Claude.ai weekly usage % in the GNOME top panel and dock — [wbniv/claude-usage](https://github.com/wbniv/claude-usage) |

## ◆ personal (biohack-shell)

[`biohack-shell`](plugins/biohack-shell/) bundles the tab-colour hooks and slash
commands from Will's personal Claude Code setup. Install only if you want the same
terminal UX (orange tab on stop, reset on prompt submit).

## ◐ memories

[`memories/`](memories/) holds Will's personal Claude Code memories — feedback
patterns, user profile, per-project context. Published as reference; Claude Code
**does not** auto-load these from third-party repos. Copy anything useful into
your own `~/.claude/memory/` by hand.

## ◈ plans

[`plans/`](plans/) holds hand-picked exemplar plans that illustrate the plan-first
workflow. Not auto-synced; curated manually. See [plans/README.md](plans/README.md).

## Evaluating third-party plugins

Third-party plugins under evaluation live as git submodules in [`vendor/`](vendor/).
Each has an `EVALUATION.md` tracking status, optional tier/star rating, and
(when rejected) structured rejection reasons. See [vendor/README.md](vendor/README.md).

## Plugin families

Plugins cluster into families. `techops` is the first and largest — the eventual
plan is an umbrella `techops` plugin that orchestrates the individual skills as a
workflow. See [docs/plans/](docs/plans/) when that plan is written.

## Development

```bash
task sync            # pull memories + settings from ~/.claude/
task gen-marketplace # regenerate marketplace.json after plugin changes
task publish-site    # generate biohack.net/claude/index.html
task install-local   # install this marketplace locally for dogfooding
```
