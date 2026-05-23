---
name: cf-static-site
description: Use this skill when setting up a new static site on Cloudflare. Two paths — (1) full stack: Astro + Cloudflare Workers + Terraform + GitHub Actions tag-driven deploys + SSM secrets; (2) plain static HTML + Cloudflare Pages + no-Terraform bootstrap script. Trigger phrases: "set up a new site", "bootstrap cloudflare site", "new cloudflare workers site", "reproduce the worldfoundry backend", "spin up a new domain".
version: 2.3.0
---

# Cloudflare Static Site Bootstrap

Two paths — choose before starting:

| | Path 1 — Astro + Workers | Path 2 — Static HTML + Pages |
|---|---|---|
| **When to use** | Full production site, SSR, CSP nonce, scroll animations | Placeholder or early-stage site before design is decided |
| **Framework** | Astro | None (raw HTML) |
| **Hosting** | Cloudflare Workers | Cloudflare Pages |
| **Infra** | Terraform (bootstrap → global → iam-self) | `scripts/bootstrap-site.sh` only |
| **Secrets** | AWS SSM | GitHub Actions secrets (no AWS) |
| **Deploy** | `wrangler deploy` | `wrangler pages deploy site/` |

For **Path 1**, continue with Phase A below.
For **Path 2**, jump directly to the [Pages path](#pages-path-plain-static-html) section.

---

All template files live in `templates/` alongside this skill file. For each file: read the template, substitute all `<PLACEHOLDER>` tokens with the user's values, write to the target project.

---

## Step 0 — Collect inputs (ask all at once before doing anything)

```
1. Domain         — apex domain, e.g. worldfoundry.org
2. Slug           — short kebab-case resource prefix, e.g. wf-org or sl
                    Used as: Worker name, S3 bucket prefix, SSM path prefix, token name
3. AWS region     — for Terraform state backend, e.g. us-west-2
4. Email dest     — forward hello@<domain> to this address, or "none" to skip email routing
5. GitHub username — your GitHub username or org, e.g. wbniv
                    Repo is derived as <GH_USER>/<DOMAIN>
```

Don't proceed until you have all five answers.

Derive these additional values from the inputs before starting:
- `<SLUG_UPPER>` — slug uppercased, hyphens → underscores (e.g. `wf-org` → `WF_ORG`)

---

## Placeholder reference

| Placeholder | Example | Source |
|-------------|---------|--------|
| `<DOMAIN>` | `worldfoundry.org` | input 1 |
| `<SLUG>` | `wf-org` | input 2 |
| `<SLUG_UPPER>` | `WF_ORG` | derived from slug |
| `<REGION>` | `us-west-2` | input 3 |
| `<EMAIL_DEST>` | `you@gmail.com` | input 4 |
| `<GH_USER>/<DOMAIN>` | `wbniv/worldfoundry.org` | input 5 |
| `<ACCOUNT_ID>` | `abc123…` (32-char hex) | output of `cloudflare-domain-setup` (Phase A) |
| `<ZONE_ID>` | `def456…` (32-char hex) | output of `cloudflare-domain-setup` (Phase A) |
| `<PROJECT_NAME>` | `foundrylinux-org` | slug with `.` replaced by `-` (Pages project name) |
| `<GH_ORG>` | `foundry-linux` | GitHub org or username |
| `<GH_REPO>` | `foundrylinux.org` | GitHub repo name (often same as `<DOMAIN>`) |

---

## Phase A — Cloudflare account + zone

**Invoke the `cloudflare-domain-setup` skill now.**

That skill handles everything: account setup, bootstrap token creation (automated via meta-token), zone creation, nameserver lookup, and polling for activation. It outputs the three values you need here.

When `cloudflare-domain-setup` completes, export its outputs:

```sh
export CLOUDFLARE_API_TOKEN=$CF_TOKEN     # bootstrap token
export TF_VAR_account_id=$CF_ACCOUNT_ID
export ZONE_ID=$ZONE_ID                   # needed for Phase D
```

Then continue to Phase B.

---

## Phase B — Terraform state backend

Read `templates/infrastructure/cloudflare/bootstrap/main.tf`, substitute placeholders, write to `infrastructure/cloudflare/bootstrap/main.tf`.

Apply:
```sh
cd infrastructure/cloudflare/bootstrap
terraform init && terraform apply
```

---

## Phase C — Zone, Workers, email routing

Read and substitute each file in `templates/infrastructure/cloudflare/global/`, write to `infrastructure/cloudflare/global/`.

If email dest is `none`: omit `email_routing.tf` entirely (don't copy it).

**Prerequisite — remove non-Cloudflare MX records.** Cloudflare Email Routing cannot be enabled while foreign MX records exist in the zone (API returns 409 code 2008). Before applying, run:

```sh
ZONE_ID=$(curl -sf \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=<DOMAIN>&account.id=$TF_VAR_account_id" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
../python-tui-lib/scripts/cf-remove-foreign-mx.sh "$ZONE_ID"
```

Or from a project that has the Taskfile wired: `task remove-foreign-mx`.

Apply:
```sh
cd infrastructure/cloudflare/global
terraform init
terraform apply -var="account_id=$TF_VAR_account_id"
```

The `zone_id` Terraform output should match `$ZONE_ID` from Phase A — if Terraform reports a different value, use the Terraform output.

> **Email routing note:** On first apply, Cloudflare emails a verification link to `<EMAIL_DEST>`. The user must click it before `hello@<DOMAIN>` forwarding goes live.

---

## Phase D — Self-narrowed API token

Read and substitute each file in `templates/infrastructure/cloudflare/iam-self/`, write to `infrastructure/cloudflare/iam-self/`. Replace the `zone_id` default with `$ZONE_ID` (from Phase A).

Apply (requires bootstrap token from Phase A):
```sh
cd infrastructure/cloudflare/iam-self
terraform init
terraform apply -var="account_id=$TF_VAR_account_id"
```

Push the narrow token to SSM and GitHub, then revoke the bootstrap token:
```sh
NEW_TOKEN=$(terraform output -raw token_value)

aws ssm put-parameter \
  --profile <SLUG>-terraform --region <REGION> \
  --name /<SLUG>/cloudflare/api_token \
  --type SecureString --value "$NEW_TOKEN" --overwrite

aws ssm put-parameter \
  --profile <SLUG>-terraform --region <REGION> \
  --name /<SLUG>/cloudflare/account_id \
  --type String --value "$TF_VAR_account_id" --overwrite

gh secret set CLOUDFLARE_API_TOKEN --repo <GH_USER>/<DOMAIN> --body "$NEW_TOKEN"
gh secret set CLOUDFLARE_ACCOUNT_ID --repo <GH_USER>/<DOMAIN> --body "$TF_VAR_account_id"
```

Revoke the bootstrap token via API (automated — uses the new narrow token):
```sh
curl -s -X DELETE \
  "https://api.cloudflare.com/client/v4/user/api-tokens/$BOOTSTRAP_TOKEN_ID" \
  -H "Authorization: Bearer $NEW_TOKEN"
```

Or revoke manually: https://dash.cloudflare.com/profile/api-tokens

---

## Phase E — Secrets scripts

Read and substitute `templates/scripts/secrets-pull.sh` and `templates/scripts/secrets-bootstrap.sh`, write to `scripts/`. Make both executable (`chmod +x`).

Also copy these scripts → `scripts/` (no substitution needed):
- `templates/scripts/lighthouse-threshold.sh`
- `templates/scripts/check-links.js`

---

## Phase F — Astro site + deploy pipeline

Copy and substitute these templates into the project root:

| Template | Destination | Notes |
|----------|-------------|-------|
| `templates/package.json` | `package.json` | |
| `templates/astro.config.mjs` | `astro.config.mjs` | |
| `templates/wrangler.toml` | `wrangler.toml` | |
| `templates/tsconfig.json` | `tsconfig.json` | |
| `templates/pnpm-workspace.yaml` | `pnpm-workspace.yaml` | Replaces `onlyBuiltDependencies` in package.json (pnpm 11+) |
| `templates/Taskfile.yml` | `Taskfile.yml` | |
| `templates/worker/index.ts` | `worker/index.ts` | CSP + nonce already wired — update `font-src` if adding external font origins |
| `templates/src/styles/global.css` | `src/styles/global.css` | Update `@theme` tokens for the new brand |
| `templates/src/layouts/Base.astro` | `src/layouts/Base.astro` | Update title, colors, footer |
| `templates/src/pages/index.astro` | `src/pages/index.astro` | |
| `templates/src/pages/404.astro` | `src/pages/404.astro` | |
| `templates/src/pages/colophon.astro` | `src/pages/colophon.astro` | Fill in typography section; update stack list as needed |
| `templates/.github/workflows/deploy.yml` | `.github/workflows/deploy.yml` | |

Create `.nvmrc` with `24`.

Install:
```sh
task install
```

---

## Phase G — First deploy

```sh
task build     # verify locally
task publish   # bumps patch tag → pushes → fires GitHub Actions deploy
```

If the zone isn't fully active yet, the first deploy may return "zone not active". Wait a few minutes and re-run from the Actions UI — no new tag needed.

Watch the deploy: https://github.com/<GH_USER>/<DOMAIN>/actions

---

## Pages path (plain static HTML)

Use this path for placeholder or early-stage sites before the design is decided. No Terraform, no AWS, no framework.

### Inputs

```
1. Domain         — apex domain, e.g. foundrylinux.org
2. Slug           — short kebab-case prefix, e.g. foundrylinux
3. GH org/repo    — e.g. foundry-linux/foundrylinux.org
```

Derive: `<PROJECT_NAME>` = domain with `.` → `-`, e.g. `foundrylinux-org`.

### Prerequisite

`scripts/bootstrap.sh` (Phase 1 APT repo bootstrap) must have run once so `CF_ACCOUNT_ID` and `CF_API_TOKEN` are cached in `/tmp/<SLUG>-bootstrap.env`. If bootstrapping a site without a Phase 1 APT repo, set those env vars manually before running `bootstrap-site.sh`.

The operator token **must** include `Account | Pages Write`. The `bootstrap.sh` token creation prompt now lists this permission; if the token predates that change, edit it at `https://dash.cloudflare.com/profile/api-tokens` to add it. `bootstrap-site.sh` checks for this and exits 1 with instructions if the permission is missing.

### Step 1 — Bootstrap (`templates/scripts/bootstrap-site.sh`)

Read `templates/scripts/bootstrap-site.sh`, substitute placeholders, write to `scripts/bootstrap-site.sh`, make executable.

Run:
```sh
bash scripts/bootstrap-site.sh [--dry-run]
```

This:
1. Creates the Cloudflare Pages project (`<PROJECT_NAME>`)
2. Attaches `<DOMAIN>` as a custom domain (Cloudflare auto-creates the DNS record)
3. Creates a `Cloudflare Pages:Edit`-scoped CI token (`<SLUG>-site-ci`); falls back to manual prompt if permission lookup fails
4. Wires `CF_PAGES_API_TOKEN` and `CF_PAGES_ACCOUNT_ID` into GitHub Actions secrets

### Step 2 — Placeholder page (`templates/site/index.html`)

Read `templates/site/index.html`, substitute `<DOMAIN>`, write to `site/index.html`.

### Step 3 — Deploy workflow (`templates/.github/workflows/deploy-static.yml`)

Read `templates/.github/workflows/deploy-static.yml`, substitute `<PROJECT_NAME>`, write to `.github/workflows/site-deploy.yml` (or `deploy.yml` if no other deploy exists).

### Step 4 — First deploy

Tag and push:
```sh
git add site/ .github/workflows/site-deploy.yml scripts/bootstrap-site.sh
git commit -m "feat: placeholder site for <DOMAIN>"
git tag v0.1.0 && git push origin main v0.1.0
```

Watch: `https://github.com/<GH_ORG>/<GH_REPO>/actions`

### Verification

```sh
curl -I https://<DOMAIN>/          # expect HTTP/2 200, content-type: text/html
curl -fsSL https://<DOMAIN>/       # expect body contains <DOMAIN>
```

---

## Cross-page header animation (scroll-shrink)

When the site has a sticky header that shrinks on scroll, cross-page navigation via Astro's `ClientRouter` must be wired up so the header height animates rather than jumping.

### CSS (`global.css`)

```css
/* Register as typed number so the value itself transitions */
@property --header-shrink {
  syntax: "<number>";
  inherits: false;
  initial-value: 0;
}
html {
  transition: --header-shrink 220ms ease-in-out;
}
@media (prefers-reduced-motion: reduce) {
  html { transition: none; }
}

/* Use --header-shrink to drive padding (or font-size, scale, etc.) */
.header-fx {
  /* Example: shrink py from 1.125rem → 0.125rem */
  padding-top: calc(1.125rem - 1rem * var(--header-shrink, 0));
  padding-bottom: calc(1.125rem - 1rem * var(--header-shrink, 0));
}
```

### `Base.astro`

```astro
import { ClientRouter } from "astro:transitions";
```

```astro
<ClientRouter />
<script>
  // --header-shrink: 0 → 1 as scrollY goes 0 → half viewport.
  // Gate update() during view transitions so the var stays at its
  // shrunk value through snapshot capture; re-run on astro:page-load
  // so the CSS transition fires from old → new on the new page.
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
    let pending = false;
    let inTransition = false;
    let firstLoad = true;
    const update = () => {
      pending = false;
      if (inTransition) return;
      const raw = Math.min(1, window.scrollY / (window.innerHeight / 2));
      const eased = 1 - (1 - raw) * (1 - raw);
      document.documentElement.style.setProperty("--header-shrink", eased.toFixed(3));
    };
    const tick = () => { if (pending) return; pending = true; requestAnimationFrame(update); };
    window.addEventListener("scroll", tick, { passive: true });
    window.addEventListener("resize", tick, { passive: true });
    document.addEventListener("astro:before-preparation", () => { inTransition = true; });
    document.addEventListener("astro:page-load", () => {
      inTransition = false;
      if (firstLoad) {
        firstLoad = false;
        if (window.scrollY === 0) return;
        const run = () => requestAnimationFrame(update);
        "requestIdleCallback" in window ? requestIdleCallback(run, { timeout: 250 }) : setTimeout(run, 0);
        return;
      }
      requestAnimationFrame(update);
    });
  }
</script>
```

Add `transition:persist` to the header element so it survives page swaps:

```astro
<header transition:persist class="header-fx sticky top-0 ...">
```

### Why the gate matters

Without `inTransition`, when the user navigates away from a scrolled page:
1. The new page's scroll position resets to 0 mid-transition
2. The scroll listener fires and sets `--header-shrink` to 0 immediately
3. Astro captures the "new page" snapshot with the header already at full height
4. No animation — just a jump

The gate holds the value through snapshot capture; `astro:page-load` triggers the transition on the now-visible new page.

---

## Persist CSS animations across page transitions

`ClientRouter` re-applies inlined `<style>` tags on every page swap, restarting CSS `@keyframe` animations from `t=0` — even on `transition:persist` elements. Fix with the Web Animations API: save `currentTime` values in `astro:before-preparation`, restore them in `astro:page-load` after the new CSS is live.

Filter animations by `pseudoElement` + `target` to be surgical — `document.getAnimations()` with `{subtree:true}` sweeps the whole page.

### `Base.astro`

```astro
<script>
  // Persist body::before + header::after animations across ClientRouter swaps.
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
    let savedBreathe: number[] = [];
    let savedStripe: number[] = [];

    const getBreatheAnims = () =>
      document.getAnimations().filter((a) => {
        const fx = a.effect as KeyframeEffect | null;
        return fx?.pseudoElement === "::after" &&
          (fx?.target as Element)?.matches?.(".header-fx");
      });

    const getStripeAnims = () =>
      document.getAnimations().filter((a) => {
        const fx = a.effect as KeyframeEffect | null;
        return fx?.pseudoElement === "::before" && fx?.target === document.body;
      });

    document.addEventListener("astro:before-preparation", () => {
      savedBreathe = getBreatheAnims().map((a) => (a.currentTime as number) ?? 0);
      savedStripe  = getStripeAnims().map((a)  => (a.currentTime as number) ?? 0);
    });

    document.addEventListener("astro:page-load", () => {
      getBreatheAnims().forEach((anim, i) => {
        if (savedBreathe[i] != null) anim.currentTime = savedBreathe[i];
      });
      getStripeAnims().forEach((anim, i) => {
        if (savedStripe[i] != null) anim.currentTime = savedStripe[i];
      });
      savedBreathe = [];
      savedStripe  = [];
    });
  }
</script>
```

For non-pseudo-element targets (e.g. an animated grid of cells): call `element.getAnimations()` per element and save as `number[][]` keyed by DOM position — stable across swaps for server-rendered elements. See worldfoundry.org commit `107cc9c` for that variant.

---

## Invariants

- Worker name in `wrangler.toml` must match `worker_name` in `global/variables.tf` — Cloudflare custom domain bindings reference it by name
- `[[routes]]` must NOT appear in `wrangler.toml` — Terraform owns domain bindings
- `run_worker_first = true` is required — without it the www→apex redirect doesn't intercept asset paths
- `prevent_destroy = true` on the zone and S3 bucket
- Permission group UUIDs in `iam-self/token.tf` are Cloudflare-managed and stable — don't look them up dynamically
- pnpm 11 requires `pnpm approve-builds --all` after install for native packages (esbuild, sharp, workerd) — `task install` handles this
