---
name: new-web-apt-repo
description: Provision a new web-hosted signed APT repo on Cloudflare R2, backed by aptly + GitHub Actions.
version: 1.0.0
---

Provision a new web-hosted signed APT repo on Cloudflare R2, backed by aptly + GitHub Actions.

Usage: `/new-web-apt-repo [gh-org/repo zone-name [subdomain [key-email [suite]]]]`

Examples:
- `/new-web-apt-repo worldfoundry/worldfoundry-apt worldfoundry.org apt packages@worldfoundry.org stable`
- `/new-web-apt-repo myCo/myco-apt myco.org` — subdomain defaults to `apt`, email to `packages@<zone>`, suite to `stable`
- `/new-web-apt-repo` — reads config from existing `scripts/bootstrap-apt.sh` in cwd

## Step 0 — Derive config and instantiate templates

If `$ARGUMENTS` were provided, parse them as:
```
<gh-org/repo>  <zone-name>  [subdomain=apt]  [key-email=packages@<zone-name>]  [suite=stable]
```

Derive the full config:

| Var | Derived from |
|---|---|
| `GH_ORG` | org part of gh-org/repo |
| `PKG_NAME` | repo part of gh-org/repo |
| `GH_REPO` | Default: `${GH_ORG}/${PKG_NAME}` (dedicated layout). **Monorepo:** the *parent* repo name — e.g. `wbniv/worldfoundry.org` when apt content lives in `wbniv/worldfoundry.org/apt/`. Override before instantiation if monorepo. |
| `APT_SUBDIR` | `apt` if current repo is a monorepo (has other top-level dirs not named after PKG_NAME); else PKG_NAME — ask if ambiguous |
| `REPO_NAME` | first component of GH_ORG (e.g. `worldfoundry` from `worldfoundry-org`) |
| `SUITE` | argument or `stable` |
| `R2_BUCKET` | PKG_NAME |
| `SECRETS_BUCKET` | `<zone-slug>-secrets` where zone-slug is `zone-name` with `.` → `-` (e.g. `indri-studio-secrets`, `worldfoundry-org-secrets`). Project-scoped: one GH_ORG often hosts multiple apt repos, and they must not share a secrets bucket. |
| `CUSTOM_DOMAIN` | `subdomain.zone-name` |
| `DNS_CNAME` | subdomain |
| `CF_ZONE_NAME` | zone-name |
| `CF_OPERATOR_TOKEN_NAME` | `<CUSTOM_DOMAIN>` (e.g. `apt.indri.studio`) — but treat as a suggestion only; the token name is a UI label, not referenced programmatically. Project-scoped so the dashboard list stays self-explanatory across multiple apt repos on the same CF account. |
| `R2_TOKEN_NAME` | `PKG_NAME-ci` |
| `BOOTSTRAP_CACHE` | `/tmp/<zone-slug>-bootstrap.env` (project-scoped — see SECRETS_BUCKET). |
| `KEY_NAME` | title-cased GH_ORG + " Packages" |
| `KEY_EMAIL` | argument or `packages@zone-name` |
| `REPO_DESC` | `GH_ORG signed APT repo and packages` |
| `TAG_PREFIX` | empty for dedicated repo (`v*` tags); `apt-` for monorepo (`apt-v*` tags) — prevents collision with the parent project's release tags. If the host repo already uses `v*` for deploys, MUST be `apt-`, and the parent workflow's `on.push.tags` must exclude `apt-v*`. |

Show the derived values and ask for confirmation before touching any files.

### Template instantiation

Copy skill templates into the repo, substituting all `{{PLACEHOLDER}}` tokens:

```bash
SKILL_DIR=~/.claude/skills/new-web-apt-repo/templates
DEST="$(pwd)/${APT_SUBDIR}"
mkdir -p "$DEST"/{scripts,scripts/recovery,aptly,gen/static} "$(pwd)/scripts" "$(pwd)/.github/workflows"

cp -r "$SKILL_DIR/scripts/"*         "$DEST/scripts/"
cp    "$SKILL_DIR/aptly/aptly.conf"  "$DEST/aptly/aptly.conf"
cp    "$SKILL_DIR/Taskfile.yml"      "$DEST/Taskfile.yml"
cp    "$SKILL_DIR/Dockerfile"        "$DEST/Dockerfile"
cp    "$SKILL_DIR/.dockerignore"     "$DEST/.dockerignore"
# Workflow lives at the REPO root regardless of APT_SUBDIR — GitHub only
# looks for workflows under .github/workflows/ at the repository root.
cp    "$SKILL_DIR/.github/workflows/publish.yml" "$(pwd)/.github/workflows/publish.yml"
cp -r "$SKILL_DIR/gen/"*             "$DEST/gen/"
cp    "$SKILL_DIR/bootstrap.sh"      "$(pwd)/scripts/bootstrap-apt.sh"
chmod +x "$DEST/scripts/"*.sh "$DEST/scripts/recovery/"*.sh "$(pwd)/scripts/bootstrap-apt.sh"

find "$DEST" "$(pwd)/scripts/bootstrap-apt.sh" "$(pwd)/.github/workflows/publish.yml" -type f | while read -r f; do
  sed -i \
    -e "s|{{GH_ORG}}|${GH_ORG}|g" \
    -e "s|{{PKG_NAME}}|${PKG_NAME}|g" \
    -e "s|{{APT_SUBDIR}}|${APT_SUBDIR}|g" \
    -e "s|{{REPO_NAME}}|${REPO_NAME}|g" \
    -e "s|{{SUITE}}|${SUITE}|g" \
    -e "s|{{CUSTOM_DOMAIN}}|${CUSTOM_DOMAIN}|g" \
    -e "s|{{DNS_CNAME}}|${DNS_CNAME}|g" \
    -e "s|{{CF_ZONE_NAME}}|${CF_ZONE_NAME}|g" \
    -e "s|{{CF_OPERATOR_TOKEN_NAME}}|${CF_OPERATOR_TOKEN_NAME}|g" \
    -e "s|{{R2_BUCKET}}|${R2_BUCKET}|g" \
    -e "s|{{SECRETS_BUCKET}}|${SECRETS_BUCKET}|g" \
    -e "s|{{R2_TOKEN_NAME}}|${R2_TOKEN_NAME}|g" \
    -e "s|{{BOOTSTRAP_CACHE}}|${BOOTSTRAP_CACHE}|g" \
    -e "s|{{KEY_NAME}}|${KEY_NAME}|g" \
    -e "s|{{KEY_EMAIL}}|${KEY_EMAIL}|g" \
    -e "s|{{REPO_DESC}}|${REPO_DESC}|g" \
    -e "s|{{TAG_PREFIX}}|${TAG_PREFIX}|g" \
    -e "s|{{GH_REPO}}|${GH_REPO}|g" \
    "$f"
done
```

Also create `${APT_SUBDIR}/packages/` (empty — placeholder for future .deb sources) and
`${APT_SUBDIR}/dist/` (git-ignored).

**Also seed `gen/config.py` from `config.example.py`** with the project's real
identity (HOST, WORDMARK, HOME_URL, CONTACT_EMAIL, INSTALL_SLUG, etc.), leaving
the `YOUR_KEY_ID_HERE` / `YOUR_FINGERPRINT_HERE` placeholders intact —
`bootstrap-apt.sh` patches those after GPG key generation. The patch step is a
silent no-op if `config.py` doesn't exist, so skipping this leaves the
generated landing page showing example-org defaults. Ask the user for: project
WORDMARK, HOME_URL, INSTALL_SLUG (e.g. `indri`), CONTACT_EMAIL, and the lede
copy. Do this BEFORE running bootstrap so the fingerprint patching takes
effect on the first run.

If no arguments were provided, check for an existing `scripts/bootstrap-apt.sh` — read its
config block, confirm values with the user, and skip template instantiation.

## Step 1 — Preflight

The build/publish/sign pipeline runs entirely inside the apt-builder Docker
image (see `Dockerfile` + `scripts/in-docker.sh`). The host only needs the
bootstrap tools + `docker`.

```bash
command -v gpg    || echo "missing: install gnupg2"
command -v shred  || echo "missing: install util-linux"
command -v curl   || echo "missing"
command -v jq     || echo "missing"
command -v gh     || echo "missing: https://cli.github.com"
command -v docker || echo "missing: install docker (https://docs.docker.com/engine/install/)"
docker info >/dev/null || echo "missing: docker daemon not reachable"
gh auth status
```

Stop and help the user install anything missing before continuing.

**Note:** `aptly`, `debhelper`, `dpkg-buildpackage`, `rclone`, etc. are NOT
installed on the host — they live inside the `apt-builder:local` image built
from `${APT_SUBDIR}/Dockerfile`.

## Step 2 — Dry run

```bash
bash scripts/bootstrap-apt.sh --dry-run
```

Show the output and ask "Looks good — run for real?" before proceeding.

**Dry-run cosmetic bug:** the dry-run always prints `[2b] Creating https://github.com/<GH_REPO>`
even when the repo already exists on GitHub — the existence check is wrapped in
`if ! $DRY_RUN && gh repo view ...` (real-run handles it correctly). Tell the
user not to panic; the real-run will detect the existing repo and skip step 2b.

## Step 3 — Create the Cloudflare operator token (if needed)

Even if a `<GH_ORG>-operator` token *appears* to exist from a prior bootstrap of
a different project under the same GH_ORG, **do not assume it has the new zone in
Zone Resources** — operator tokens are zone-scoped, so a token created for
`worldfoundry.org` won't have `indri.studio` listed. Cached tokens at
`BOOTSTRAP_CACHE` reload silently and then fail at step 1b with
`Zone <CF_ZONE_NAME> not found`.

Three paths, in order of preference:

1. **Edit the existing token to add the new zone** (least new state). Dashboard →
   Tokens → click the token → Edit → Zone Resources → + Add row → Include →
   Specific zone → `CF_ZONE_NAME`. Save. The cached token value stays valid.
2. **Create a fresh token** scoped only to the new zone. Cleaner blast radius;
   user pastes it when prompted; the script re-caches it.
3. The script also self-modifies: if you already have a CF API token with
   `User → API Tokens → Edit` permission, you could in theory PUT the new
   policy via the API — but in practice operator tokens never have that
   permission, so this path is closed. Don't promise it; tell the user this
   is one irreducible manual step.

If `CF_API_TOKEN` is not already exported, the script will print instructions and prompt for it:

1. Go to <https://dash.cloudflare.com/profile/api-tokens>
2. Click **+ Create Token** → **Get started** next to **Create Custom Token**
3. Fill in:
   - **Name:** the suggested value of `CF_OPERATOR_TOKEN_NAME`, or whatever the user
     prefers — the name is a UI label only, the script doesn't read it. Users
     hosting multiple apt repos on one CF account often prefer the
     `<CUSTOM_DOMAIN>` form (e.g. `apt.indri.studio`) since the dashboard list
     becomes self-explanatory.
   - **Permissions** — each row is *three* dropdowns: **Scope | Permission | Access**.
     The permission column filters as you type; type "r2" and pick **Workers R2 Storage**
     (NOT Data Catalog or SQL).

     | Scope (col 1) | Permission (col 2) | Access (col 3) |
     |---|---|---|
     | Account | Workers R2 Storage | Edit |
     | Zone | DNS | Edit |
     | Zone | Transform Rules | Edit |

   - **Account Resources:** Include → select your account
   - **Zone Resources:** Include → Specific zone → `CF_ZONE_NAME`
4. Continue to summary → **Create Token** → copy the value, paste at the script prompt

`CF_ACCOUNT_ID` and `CF_ZONE_ID` are fetched automatically.

The script validates all three permissions in step 1b before touching anything.

## Step 4 — Run for real

```bash
bash scripts/bootstrap-apt.sh
```

The script caches `CF_API_TOKEN` and R2 credentials to `BOOTSTRAP_CACHE` (mode 600) on first
entry and reloads them on subsequent runs — no re-typing on restarts.

When prompted for R2 S3 credentials (step 6), the dashboard page is printed automatically.
Create an **Account API token** (not User):
- **Token name:** value of `R2_TOKEN_NAME` from config
- **Permissions:** Object Read & Write
- **Bucket:** Apply to specific buckets only → `R2_BUCKET`

## Known failure modes

If step 1b reports missing permissions, edit the token at
<https://dash.cloudflare.com/profile/api-tokens> and re-run (cached token reloads
automatically, no re-paste needed).

| Pattern in output | What it means | Fix |
|---|---|---|
| `[1b] Token is missing required permissions` | Operator token incomplete | Edit token — the output lists which permissions are missing |
| `[1b] Could not retrieve account ID` | Token can't read account | Verify Account Resources → your account is selected |
| `[7.5]` error on transform rule | Zone may already have a conflicting rewrite rule | Check Cloudflare dashboard → Rules → Transform Rules |

## Step 5 — Push first tag

After the script completes, trigger the first publish workflow:

```bash
task bump    # auto-increments patch version and triggers publish.yml
```

Confirm the publish job goes green before calling bootstrap complete.

## Step 5.5 — Verify landing page

```bash
curl -sI https://<CUSTOM_DOMAIN>/
# expect: HTTP/2 200  content-type: text/html
```

The root URL is served via a Cloudflare URL rewrite rule (`http_request_transform` phase)
that transparently maps trailing-`/` URLs → `index.html`. The free plan does not support
`http_request_redirect`, so this is a rewrite, not a 301.

### Design customisation

The site is styled from `gen/src.css` (Tailwind v4 `@theme` tokens + all
component CSS) compiled to `gen/static/styles.css`. To customise:

```bash
# Automated: extract tokens from the parent site (bootstrap.sh runs this automatically)
bash apt/gen/distill-palette.sh <parent-domain>     # updates src.css + styles.css
# commit both files

# Manual: edit tokens directly in gen/src.css @theme block, then recompile
task apt:publish-local   # runs inside apt-builder container:
                         #   - tailwindcss -i gen/src.css -o gen/static/styles.css
                         #   - regenerates public/index.html
open <APT_SUBDIR>/public/index.html
# commit both gen/src.css and gen/static/styles.css
```

All tooling (Tailwind CLI, aptly, python3, dpkg-buildpackage) lives inside the
container; the host only needs `docker` to be running.

If the parent site has no detectable CSS and you need palette generation from
a seed colour, see the API references in `gen/src.css` header comment:
- **The Color API**: `GET https://www.thecolorapi.com/scheme?hex=XXXXXX&mode=monochrome&count=5`
- **Colormind**: `POST http://colormind.io/api/ -d '{"model":"ui"}'`

The `gen/gen-index.py` script generates `public/index.html` on every publish run, pulling
repo metadata from `gen/config.py`. Update `gen/config.py` after bootstrap (it starts with
GPG placeholder values that `bootstrap-apt.sh` patches in automatically).

The generator auto-flattens the `/pool/<component>/` listing when the total `.deb` count
is below `FLAT_POOL_THRESHOLD` (default 30): browser users see one table of packages
instead of clicking through Debian's `c/`/`i/`/`l/`/… shard directories. Above the
threshold, the standard sharded view returns. The on-disk layout stays Debian Policy
§2.4-conformant in all cases — only the HTML presentation changes, so apt clients are
unaffected. Set `FLAT_POOL_THRESHOLD = 0` in `gen/config.py` to always shard.

Inside the flat-pool listing, packages declaring `Section: metapackages` in their
`debian/control` get a yellow `META` chip in the Arch column and are surfaced in their
own "Install this — umbrella metapackages" section above a "Constituent packages"
section. Helps first-time visitors find the install-this entries without scanning the
whole alphabetic table. Detection is automatic from the published `Packages` files
(with a `dpkg-deb --field` fallback for pre-publish runs).

Clicking a metapackage row expands a panel showing the long `Description` body plus
clickable `Depends:` / `Recommends:` lists. Same-repo deps link to their `.deb` in
this pool; external deps link to `packages.ubuntu.com/<UPSTREAM_UBUNTU_SUITE>/<pkg>`
(default: `resolute`; configurable in `gen/config.py`). Keyboard-accessible via Tab +
Enter/Space; the row gets `role="button"` + `aria-expanded` tracking automatically.

### Builder image (`Dockerfile` + `scripts/in-docker.sh`)

The build/publish/sign pipeline runs entirely inside a per-project
`ubuntu:26.04`-based image (`apt-builder:local`), built from
`${APT_SUBDIR}/Dockerfile` on first use and layer-cached thereafter.

**The base MUST match the target Ubuntu release.** dpkg-shlibdeps pins to
the build host's library sonames; building inside Debian bookworm (or
`ubuntu:latest`, currently noble/24.04) for an Ubuntu 26.04 target silently
produces .debs that won't install — caught the hard way on 2026-05-20 when
`vgmstream_2083-1foundry2` shipped with `libavcodec60` deps after the 26.04
SRU to ffmpeg 8 / libavcodec62. If you're updating an older apt repo whose
publish.yml builds on `runs-on: ubuntu-latest` without an `in-docker.sh`
wrapper or whose Dockerfile uses a Debian base, migrate it.

- `scripts/in-docker.sh` is the host-side wrapper. It builds the image
  (silent / cached), then `docker run`s with the repo bind-mounted at `/work`,
  `--user $(id -u):$(id -g)` for correct file ownership, and conditional
  mounts/env-forwards for `$HOME/.gnupg` (local) and `GPG_PRIVATE_KEY` /
  `R2_*` (CI).
- Every task in `${APT_SUBDIR}/Taskfile.yml` (`build`, `publish-local`,
  `verify`, `shell`) goes through `in-docker.sh`. The original
  `scripts/{build-all,init-repo,publish-local,sign}.sh` are environment-agnostic
  and run identically locally and in CI.
- CI uses `docker/build-push-action@v7` with GHA cache (`type=gha,scope=apt-builder`)
  so the image rebuild is near-zero after the first workflow run.

Trade-off: ~500 MB image (build deps + aptly + node + python). For higher
throughput, split into a smaller `apt-publisher` (aptly + gnupg + rclone, ~80 MB)
and `apt-package-builder` (full build deps) image pair — not done by default.

## Step 6 — How users consume this repo

```bash
sudo install -d /etc/apt/keyrings
curl -fsSL https://<CUSTOM_DOMAIN>/key.gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/<REPO_NAME>.gpg
echo "deb [signed-by=/etc/apt/keyrings/<REPO_NAME>.gpg] https://<CUSTOM_DOMAIN> <SUITE> main" \
  | sudo tee /etc/apt/sources.list.d/<REPO_NAME>.list
sudo apt-get update
sudo apt-get install <pkg>
```

- `key.gpg` lives at exactly `/key.gpg` — no other path. Don't invent `/pubkey.asc` etc.
- `<SUITE>` is the distribution (e.g. `stable`) — not the hostname.

Add this snippet to the repo's README.md.

## Credential storage

`bootstrap-apt.sh` automatically stores all secrets to a private `<SECRETS_BUCKET>` R2 bucket
(no public access, no custom domain) using the operator token:

| Secret | GitHub Actions secret | R2 backup |
|---|---|---|
| GPG signing key | `GPG_PRIVATE_KEY` | `r2://<SECRETS_BUCKET>/GPG_PRIVATE_KEY` |
| R2 access key | `R2_ACCESS_KEY_ID` | `r2://<SECRETS_BUCKET>/R2_ACCESS_KEY_ID` |
| R2 secret | `R2_SECRET_ACCESS_KEY` | `r2://<SECRETS_BUCKET>/R2_SECRET_ACCESS_KEY` |
| CF operator token | (not in GitHub) | `r2://<SECRETS_BUCKET>/CF_API_TOKEN` |

A local session cache (mode 600, cleared on reboot) holds credentials so re-runs within
the same session don't re-prompt. Retrieve any value from R2 backup if needed:

```bash
curl -fsSL "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/r2/buckets/<SECRETS_BUCKET>/objects/<KEY>" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

## Recovery toolkit

Five recovery scenarios are scripted at `${APT_SUBDIR}/scripts/recovery/*.sh`
and wired into the apt Taskfile. Each is idempotent and prompts for any
missing input (token values use `read -rsp` for hidden entry).

| Scenario | Task | Script |
|---|---|---|
| Cache a new operator token (fresh machine) | `task apt:cache-cf-token` | `cache-cf-token.sh` |
| Restore all GH secrets from R2 backup | `task apt:restore-gh-secrets` | `restore-gh-secrets.sh` |
| Import GPG signing key into local keyring | `task apt:restore-gpg-keyring` | `restore-gpg-keyring.sh` |
| Rotate R2 S3 CI credentials | `task apt:rotate-r2-token` | `rotate-r2-token.sh` |
| Rotate GPG signing key (2-yr expiry) | `task apt:rotate-gpg-key` | `rotate-gpg-key.sh` |

After bootstrap, encourage projects to write a `docs/runbooks/apt-secrets-recovery.md`
(per-project, with concrete names) that links each scenario to its `task` command
and inlines the manual-equivalent shell — the worldfoundry.org project's runbook
is a complete reference example.

The `rotate-gpg-key` script aborts if a secret key for `${KEY_EMAIL}` is already
in the local keyring, forcing an explicit `gpg --delete-secret-keys` first.
This prevents accidental invocations from clobbering a working key — the cost
is two extra commands during planned rotation, which is the right trade-off.

## Lessons learned (from real bootstrap runs)

These gotchas have been folded into the templates; documenting here so future skill
edits don't accidentally undo them.

1. **Aptly state must live on the bind-mounted volume, not in `/tmp` or `$HOME`.**
   CI runs each pipeline step (`init-repo.sh`, `publish-local.sh`, `sign.sh`) in a
   *separate* `docker run` — `/tmp` is fresh every time, so the repo created by
   `init-repo.sh` vanishes before `publish-local.sh` runs. `aptly.conf` sets
   `rootDir: "/work/apt/.aptly"` (or `/work/.aptly` for dedicated layouts) so state
   persists across containers via the bind mount. Host-side `.aptly/` is gitignored.

   Symptom if regressed: `ERROR: unable to publish: local repo with name <REPO_NAME> not found`.

2. **rclone reads `RCLONE_CONFIG_*` env vars, not a config file.** `in-docker.sh`
   forwards them with a `compgen -e | grep '^RCLONE_CONFIG_'` loop so the workflow's
   inline backend config (endpoint, keys, region) reaches the container. The fixed
   allow-list (`R2_ACCESS_KEY_ID`, etc.) is *not* enough on its own.

   Symptom if regressed: `Failed to create file system for "R2:<bucket>/": didn't find section in config file`.

3. **Tailwind v4 workflow: `src.css` is the source, `styles.css` is the output.**
   `gen/src.css` uses `@import "tailwindcss"` + `@theme { }` for tokens + all
   component CSS. `gen/static/styles.css` ships the pre-compiled standalone
   equivalent (`:root { }` tokens + same component CSS, no Tailwind import).
   Both files are committed — the published site serves the pre-compiled
   `styles.css` without recompiling on every publish. Edit tokens in `src.css`
   (and `styles.css`) and recompile with:
   ```bash
   tailwindcss -i apt/gen/src.css -o apt/gen/static/styles.css
   ```
   The Tailwind CLI lives in the `apt-builder:local` container — run via:
   ```bash
   task apt:publish-local   # rebuilds styles.css + regenerates index.html
   ```
   **Don't run Tailwind on `src.css` directly from `publish-local.sh` in CI**
   — CI serves the pre-committed `styles.css`. Only recompile locally after
   editing tokens, and commit both files together.

4. **Public key path is `/key.gpg`, not `/pubkey.asc`.** `bootstrap-apt.sh` uploads
   the public key to `r2://<bucket>/key.gpg`. `gen-index.py`'s install snippets and
   icon map must match. Don't reintroduce `/pubkey.asc`.

5. **Static asset filename is `logo.png` (generic), not `wflogo.png` (worldfoundry-specific).**
   `gen-index.py` references `logo.png` so the same template works for any project.
   `gen/static/logo.png` is the shipped placeholder; users replace with their own.

6. **Tailwind in the Docker image: use the standalone Linux binary, not `npx`.**
   The standalone `tailwindcss-linux-x64` binary is a single executable with no Node
   dependency. The Tailwind v4 npm package ships a native `@tailwindcss/oxide` binary
   that fails to resolve under multi-arch `docker buildx`, even when only one arch is
   actually used. The standalone binary is downloaded in the Dockerfile, ~50 MB, works.

7. **Monorepo tag namespace must be distinct from the parent project.** If the
   host repo's deploy workflow triggers on `v*`, set `TAG_PREFIX=apt-` so apt
   tags are `apt-v0.1.0` and don't fire the website deploy. Update the parent
   workflow's `on.push.tags` with `'!apt-v*'` to be doubly safe.

8. **rclone needs `--s3-no-check-bucket` on R2 with least-privilege tokens.**
   Before its first upload, rclone does a `HEAD <bucket>/<object>` probe; if
   that 404s (which it does for the first object in an empty bucket), rclone
   tries to *create the bucket* via `PUT /<bucket>`. A bucket-scoped Object
   Read & Write token correctly refuses CreateBucket — and the whole sync
   fails with `AccessDenied` even though Object PUT would have worked. The
   `--s3-no-check-bucket` flag suppresses the probe. The publish.yml template
   sets it on both `rclone sync` and `rclone copy`.

   Symptom if regressed: `Failed to copy: AccessDenied: Access Denied` with
   `PUT /<bucket>` (no object path) in `--dump headers` output. Misleading
   because read operations work fine.

9. **`task bump` triggers a full .deb rebuild even for index-only changes.**
   The publish workflow runs `scripts/build-all.sh` unconditionally before the
   aptly + sign + sync stages, so a favicon edit (touching only `apt/gen/`)
   spends ~7 min rebuilding all packages. The .debs end up byte-identical to
   the previous run (same source SHA → same output), so R2 sees no-ops — the
   cost is CI minutes, not correctness.

   Real fix (non-trivial, not in the template yet): a two-step "skip if no
   `apt/packages/**` diff" pattern. Either (a) `dorny/paths-filter` + restore
   prior `apt/dist/` from R2 before init-repo.sh runs, or (b) split into
   `publish-debs.yml` and `publish-index.yml` workflows triggered on different
   path-filters. Both require persisting the existing `apt/dist/` somewhere
   the index-only run can pull from, so it's a refactor not a one-liner.

   Live with it for now — 7 min for a favicon edit is annoying but not
   broken. Open a follow-up when index-only edits become common enough that
   the CI time hurts.

10. **`find -name '<pkg>-*'` in vendored-upstream `build.sh` also matches the workdir.**
    When you write a `packages/<pkg>/build.sh` that fetches a tarball into
    `$(mktemp -d -t <pkg>-build-XXXXXX)` and then locates the extracted source
    with `find "$WORKDIR" -maxdepth 1 -type d -name "<pkg>-*"`, the workdir
    itself (`<pkg>-build-qog0lH`) matches the glob — `head -1` picks it,
    breaking the build with `<file>: No such file or directory`. Fix: extract
    into a `$WORKDIR/src/` subdir and `find "$WORKDIR/src" -mindepth 1
    -maxdepth 1 -type d`. This is a build.sh pattern, not a template issue —
    document in the migration notes for any new vendored package.

11. **Wrapping an upstream `build-deb.sh` is a valid first-package strategy.**
    Packages whose install logic lives in a multi-component `packaging/build-deb.sh`
    (icons, systemd units, Chrome extension bundle, GNOME extension, Python
    server) don't need a same-day port to canonical `debian/{control,rules,install}`
    layout. A `build.sh` wrapper that fetches a sha256-pinned GitHub tarball
    and delegates to the upstream's script gets to a working repo immediately.
    Tracked as a follow-up to port when PPA distribution, `apt source`, or
    lintian becomes worth it. The `/package` skill is the right tool for that
    port when it happens.

12. **Upstream build scripts that bake icons from an existing install fail in
    fresh containers.** `claude-usage`'s `generate-icon.py --baseline` reads
    the project's base star icon from `~/.local/share/claude-usage` or
    `/usr/share/claude-usage`. In an `apt-builder:local` container, neither
    path exists, so the bake fails and `packaging/build-deb.sh` falls back to
    shipping the raw star PNG. Functionally correct, cosmetically degraded.
    When wrapping a build script that depends on existing-install artifacts,
    vendor those artifacts (icon source, asset templates) into
    `apt/packages/<pkg>/` so the build is self-contained. Surface this as a
    known regression in the package's plan, not as a build failure.

13. **`python3-cairo`, `python3-pil`, `rsync` aren't in the default builder
    image.** Packages whose `packaging/build-deb.sh` bakes icons (cairo + PIL)
    or copies payload (rsync) need these added to `apt/Dockerfile`. Audit any
    new wrapped package's tool dependencies and extend the apt-get install
    list — the only way to find out is a failed build, so flag this
    proactively when reading the upstream's script.

14. **The smoke-check job runs in `ubuntu:latest` under `sh`, not bash, by
    default.** `run:` steps in `container:` jobs use whatever the container
    provides as `/bin/sh` — for ubuntu:latest that's dash. `[[ ]]`, `<<<`
    here-strings, and other bashisms fail silently with `not found` and let
    the rest of the script run with broken state. Fix: explicitly set
    `shell: bash` on the step (or `defaults.run.shell: bash` on the job).
    The default template now does this.

15. **The smoke-check must use `apt-cache show`, not `apt-get install`, as the
    verification.** The first .deb in the repo often has transitive
    dependencies (gnome-shell, libwebkit2gtk, kernel modules) that don't
    install in a bare `ubuntu:latest` container. The smoke check's purpose is
    to verify signing chain + metadata serving, not Ubuntu's dependency
    resolver. `apt-cache show` proves both without depending on installability.
    Updated default in template.

16. **Discovering packages "from our repo" by filtering apt-cache policy
    against the custom domain runs apt-cache policy against EVERY package on
    the host — slow on a clean Ubuntu (~30k packages) and likely to silently
    truncate output.** Far simpler: glob `/var/lib/apt/lists/<custom-domain>_*_Packages`
    directly. apt encodes the URL→filename mapping so the hostname is the
    file prefix. Pattern: `grep -hE '^Package: ' /var/lib/apt/lists/<custom-domain>_*_Packages`.

17. **`gen/static/logo.png` is ALSO non-generic.** The shipped template
    contains worldfoundry's wordmark sticker. Replace with the new project's
    own icon (typically `public/icon-192.png` from an existing marketing
    site) before tagging, or the apt page's top-right will show the previous
    project's brand. The skill's bundled file is named `logo.png` (not
    `wflogo.png`) per lesson #5 — but contents are still worldfoundry-specific.

18. **`gen/static/styles.css` ships with a neutral greyscale default palette
    (system-ui fonts, #111111 surface, #888888 accent, no Google Fonts).**
    When bootstrapping for a project that already has an existing domain,
    run the automated distillation step — `bootstrap.sh` calls it automatically
    as Step 0.5:
    ```bash
    bash apt/gen/distill-palette.sh <parent-domain>
    ```
    The script tries (in order):
    1. `<repo-root>/src/styles/global.css` — Astro monorepo sibling
    2. `https://<domain>/styles.css` — live site fetch
    3. Keeps greyscale defaults if neither is found
    It maps common CSS custom property naming conventions onto apt's 10 token
    names, and writes both `gen/src.css` and `gen/static/styles.css` in place.
    Commit both files after running.
    If manual tuning is needed after distillation, grep for hex literals:
    ```bash
    grep -nE '#[0-9a-fA-F]{3,8}|rgba?\(' gen/static/styles.css
    ```
    Two structural hex values remain intentionally: `#1e1e1e` (table row border)
    and `#161616` (table row hover) — these stay near-black on all palettes and
    don't need to change unless the surface token is very light.

19. **The `@media (max-width: 639px)` card layout ships in both `src.css` and
    `styles.css` and is brand-neutral.** It converts the listing table from a
    wide multi-column layout to per-row CSS-grid cards (name / arch+size / desc)
    that fit 375 px viewports without breaking. Key behaviours:
    - Hides `col-mod` and `col-hash` on mobile (lowest-value metadata)
    - Resets `col-name td` from `width: 1px` (desktop shrink hack) to `auto`
    - Makes `.entry` block-flex so long `.deb` filenames wrap at row width
    - Tightens the header wordmark and drops the nav text label at 375 px
    - Keeps `.meta-details-cell` as full-width block with prose wrapping
    When porting CSS to a new brand, **keep the entire `@media` block verbatim**
    — it uses only CSS custom properties and structural selectors, no hardcoded
    colours. Only the `:root`/`@theme` token block needs to change.
    The block lives in both `src.css` (Tailwind source) and `styles.css`
    (pre-compiled). Edit both together, or recompile via `tailwindcss` after
    editing only `src.css` (see lesson 3).

## Updating this skill

Per convention: after each real bootstrap run, review what differed from this description
and commit updates to `~/.claude/skills/new-web-apt-repo/SKILL.md`.
