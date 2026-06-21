---
name: package
description: Package a program as a Debian-policy-compliant .deb for a foundry-style apt repo. Accepts a program name, GitHub URL, release tarball URL, .dsc URL, or local source tree. Always checks Ubuntu universe first to avoid duplicate effort. Uses dh_make + debhelper + dpkg-buildpackage so binaries are auto-stripped, shared-lib deps are auto-resolved, builds get hardening flags, and the output is a proper Debian source package (exportable to a PPA). Trigger phrases — "package this", "package X as a deb", "build a deb for", "vendor and package", "/package".
version: 1.0.0
---

# /package — Debian-policy-compliant .deb builder

Generates a Debian source package (`debian/` source-format tree) for an upstream program, builds it with `dpkg-buildpackage`, and wires it into a foundry-style apt repo (e.g. `apt.foundrylinux.org`).

Why this and not a hand-rolled `build.sh` + `dpkg-deb`? See [the comparison](#why-debhelper) at the end. Short version: debhelper auto-strips debug info, resolves `${shlibs:Depends}` accurately, applies build hardening flags, generates a PPA-ready source package, and follows Debian Policy out of the box. A hand-rolled `dpkg-deb --build` ships 2-3× larger binaries with sloppy deps and no security baseline.

---

## Step 0 — Parse the input

The skill takes a single argument in one of these forms (auto-detect by shape):

| Shape | Example | Action |
|---|---|---|
| Bare name | `f9dasm`, `libvgm` | Search apt + GitHub; ask the user to confirm the upstream URL |
| `github.com/...` URL | `github.com/Arakula/f9dasm` | `gh api` to find latest tag/release; download the archive tarball |
| Tarball URL | `example.org/foo-1.2.3.tar.gz` | Download + sha256 pin |
| `.dsc` URL | `deb.debian.org/.../foo_1.2.3-1.dsc` | `dget` to fetch the existing source package; re-pack with Foundry packaging revision |
| Local tree | `/path/to/foo` | Treat as orig tree (must contain `Makefile` or autotools/cmake/cargo); skill will tar it up as the orig tarball |

Optional name/version overrides may follow as `key=value` tokens:

```
/package <input> [name=<deb-package-name>] [upstream=<X.Y.Z>] [revision=<1foundry1>] [section=<devel>]
```

Defaults: `name` derived from the URL or tarball; `upstream` is the latest tag or filename version; `revision` is `1foundry1`; `section` is `devel` unless overridden.

---

## Step 0.5 — Prior-attempt check

After resolving `<name>`, check whether a previous packaging attempt exists in the repo:

```bash
REPO_ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo ".")
PKG_DIR="$REPO_ROOT/foundry-apt/packages/$NAME"

if [[ -d "$PKG_DIR/debian" ]] && [[ "$FORCE" != "1" ]]; then
    echo "Found existing packaging attempt at foundry-apt/packages/$NAME/."
    echo "Skipping upstream fetch (Steps 2–3) and going directly to Step 4 (build & verify)."
    echo "Pass --force to start fresh instead (overwrites the existing debian/ tree)."
    SKIP_TO_BUILD=1
fi
```

If `SKIP_TO_BUILD=1`:
- Skip Steps 2 and 3 entirely.
- Use the existing `foundry-apt/packages/<name>/` tree as the source for Step 4.
- If `build.sh` exists there, run it; otherwise run `dpkg-buildpackage -us -uc -b` directly inside the Docker container.
- Surface what's in the existing `debian/changelog` (package name + version) so the user knows which attempt is being resumed.

If `--force` was passed, proceed with the normal flow and overwrite the existing tree.

---

### Naming gotcha: `-dev` is reserved

In Debian convention `pkg-dev` means "headers/`.so` symlinks for linking against `pkg`" (e.g. `libfoo-dev`). If you're packaging a metapackage that means "tools to develop the upstream *project* itself" — **don't call it `<project>-dev`**, that collides with the convention and confuses users + tooling. Use a full word: `<project>-development`, `<project>-contributor`, or `<project>-build`. Description still carries the meaning; the name shouldn't fight the convention. Real example: `worldfoundry-development` (engine contributor install) — not `worldfoundry-dev`.

### Renaming an already-published package

Sometimes you rename after publishing (e.g. to match the Repology slug). Renames are
welcome — the rule is **nothing breaks, all call-sites in one commit**:

1. `git mv packages/<old> packages/<new>` (preserves history; git shows renames, not
   delete+add).
2. In the moved tree: update `Source:` + `Package:` in `debian/control`, the
   `debian/changelog` (new top entry under the **new** name, bumped revision, with a
   rename note; leave old entries historical), `build.sh`'s `NAME=` (drives the `.deb`
   filename) + help text, the `debian/rules` DESTDIR (`debian/<new>/...`), and the
   per-package `debian/<new>.manpages` filename.
3. **The installed binary/command need not change** — package name ≠ binary name is fine
   (e.g. `python3-picire` ships `picire`; `asar-snes-assembler` ships `asar-snes`). Keep
   a good command name; renaming the package doesn't force renaming the command, man
   page, or `.desktop`.
4. Update every referrer in the *same* commit: dependent metapackage `Depends:` (+ bump
   its changelog), `LICENSES-VENDORED.md`, `README.md`, `CLAUDE.md`, `TODO.md` (ITP line).
5. **Pre-1.0 / no users → no transitional dummy package.** Otherwise ship a transitional
   `<old>` package that `Depends: <new>` for the upgrade path.
6. **Drop the old name from the live repo.** A fresh-`dist/` CI rebuild + `rclone sync`
   (which deletes extraneous R2 files) removes it. If the repo *caches* `dist/` across
   runs, `prune-dist.sh` must also drop orphaned `.debs` (package no longer in any
   `packages/*/debian/control`) or the old name lingers in the cache forever.

---

## Step 1 — Universe check (BLOCKING — do this first)

This is the lesson from packaging xa65: **xa65 was already in Ubuntu 26.04 universe at `2.4.1-0.1build1`** and we duplicated upstream effort by an entire commit before realising. We ultimately retired our copy and now consume xa65 from universe via the metapackage's `Depends:` chain. Always check first — saves the round trip.

```bash
docker run --rm ubuntu:26.04 bash -c "
    apt-get update -qq 2>/dev/null
    apt-cache policy <name>
    echo '---'
    apt-cache search '^<name>\$'
" 2>&1
```

If `Candidate:` is non-empty (i.e. Ubuntu ships the package), **STOP**. Print:

```
<name> is already in Ubuntu 26.04 universe as <ver>.
Add it to the apt-install list in install-<metapackage>.sh
and to the metapackage's Depends: line. Don't duplicate.
```

…and exit. Do *not* generate any `debian/` tree. Do *not* run `dh_make`.

If `apt-cache search` finds a near-match under a different name (e.g. `<name>-tools`), surface that and ask the user whether it covers their need.

### Universe presence is necessary, not sufficient — also check version, footprint, and the real command

Three follow-ups before you wire a universe package into a metapackage's `Depends:`. Each is a bug we've actually hit:

1. **Version floor.** "It's in universe" ≠ "it's new enough." A dependency may require a higher version than universe ships — e.g. `shrinkray` needs `textual >= 8.0.0`, but Ubuntu 26.04 universe froze `python3-textual` at `2.1.2`. Check the candidate against any required floor (`apt-cache policy <dep>`); if it's too old you're back to packaging a newer one (a cascade — see the Python transitive-deps note in Step 3).

2. **Footprint vs the target edition's size budget.** A tiny tool can drag a huge closure: `cvise` is 12 MiB itself but pulls `libllvm21`+`libclang-cpp21`+`clang-format-21` for a **326 MiB** install closure. That decides *which edition* it belongs in (Foundry's anvil targets a 4 GB stick, so LLVM-class mass goes in `foundry-atelier`, not `foundry-core`/anvil — exactly like `ghidra`). Measure the closure before choosing placement. Note `apt-get -s install` does **not** print an "After this operation…" line on apt 3.x (ubuntu:26.04), so sum `Installed-Size` yourself:

   ```bash
   docker run --rm ubuntu:26.04 bash -c '
     apt-get update -qq 2>/dev/null
     pkgs=$(apt-get install -s -y <name> | awk "/^Inst /{print \$2}")
     t=0; for p in $pkgs; do s=$(apt-cache show "$p" 2>/dev/null | awk -F": " "/^Installed-Size:/{print \$2; exit}"); t=$((t+${s:-0})); done
     echo "$((t/1024)) MiB install closure for <name>"'
   ```

   If a chunk of that closure is shared with packages already on the image (`libllvm21` is also pulled by `mesa-vulkan-drivers`/`yuzu`/`rust`), the *marginal* cost is smaller — measure against the real image, not just the bare container.

3. **The command is not always the package name.** Before writing install-summary lines, e2e tool-checks, or telling the user "run `<name>`", inspect what the package actually ships in `/usr/bin`:

   ```bash
   (cd "$(mktemp -d)" && apt-get download <name> >/dev/null 2>&1 && dpkg-deb -c <name>_*.deb | grep -E "usr/bin|usr/sbin")
   ```

   Real example: the `delta` reducer package ships **`singledelta`/`multidelta`/`topformflat`** — there is no `delta` command (that name belongs to the popular `git-delta`). Getting this wrong silently breaks the e2e harness and any `command -v` check. While you're here, eyeball those `/usr/bin` paths for collisions with already-shipped or popular packages (a real file conflict blocks `apt install`).

---

## Step 2 — Resolve upstream + fetch source

Set up the workspace:

```bash
WORKDIR=$(mktemp -d -t package-XXXXXX)
cd "$WORKDIR"
```

Per input shape, populate `$WORKDIR/<name>-<upstream>/` (the upstream tree) and `$WORKDIR/<name>_<upstream>.orig.tar.gz` (the orig tarball, gzipped, top-dir = `<name>-<upstream>/`).

**GitHub URL flow:**

```bash
# Find the latest tag (or use the one the user specified)
TAG=$(gh api repos/<owner>/<repo>/tags --jq '.[0].name')
URL="https://github.com/<owner>/<repo>/archive/refs/tags/${TAG}.tar.gz"
curl -fsSL -o upstream.tar.gz "$URL"
SHA256=$(sha256sum upstream.tar.gz | awk '{print $1}')
# Confirm the sha256 by re-fetching once; record both checksums match
```

> **Non-`v`-prefixed tag formats.** Some upstreams (e.g. vgmstream) use `r<number>` or `rel-<number>` rather than `v<number>`. The tarball URL and extracted top-dir will contain the full tag (e.g. `vgmstream-r2083/`). The Debian version in `debian/changelog` MUST start with a digit — strip any leading letter from the tag when constructing the version. So tag `r2083` → Debian version `2083-1foundry1`, not `r2083-1foundry1` (dpkg-buildpackage rejects versions that start with a non-digit). Also update `debian/watch` to match the non-standard prefix (see Step 3 §6).

> **Check the upstream's age and archived status — old C/C++ upstreams will likely need build patches.** `gh api repos/<owner>/<repo> --jq '{archived,pushed_at}'` shows both. A long-dormant or archived upstream (e.g. `halfempty`: last released 2020, repo archived 2026) was last built against an older toolchain; on Ubuntu 26.04 (GCC 15, glibc 2.41) expect `-Werror` trips, missing `#include`s the compiler now requires, or removed APIs. Budget for `debian/patches/`, and confirm the newest tag is still the one you want (an archived repo's "latest release" may predate community forks). These build-fix patches are exactly the upstreamable kind — see Step 7.

**Tarball URL flow:** as above, just curl + sha256.

**.dsc URL flow:**

```bash
dget -u <dsc-url>   # downloads .dsc + .orig.tar.gz + .debian.tar.xz
```

**Local tree flow:**

```bash
tar --transform "s,^,${NAME}-${UPSTREAM}/," -czf "${NAME}_${UPSTREAM}.orig.tar.gz" -C <local-tree> .
```

Pin the sha256 — save the value somewhere the build script will use (see Step 4's `packages/<name>/build.sh`).

**Pre-built binary upstream flow (zip, not source tarball):** Some upstreams (e.g. Ghidra) publish a pre-built binary zip rather than a source tarball. There is no compile step — the zip IS the package content.

```bash
# Download and pin sha256. Ghidra example:
ZIP="$WORKDIR/${NAME}_${UPSTREAM}.zip"
curl -fsSL -o "$ZIP" "$UPSTREAM_URL"
echo "$SHA256  $ZIP" | sha256sum -c -

# Extract; the zip top-dir may differ from the Debian convention.
# Rename so dpkg-buildpackage sees <name>-<version>/ as the source root.
unzip -q "$ZIP" -d "$WORKDIR"
EXTRACTED="$WORKDIR/<upstream-extracted-name>"   # e.g. ghidra_12.1_PUBLIC
SRC_DIR="$WORKDIR/${NAME}-${UPSTREAM}"           # e.g. ghidra-12.1
mv "$EXTRACTED" "$SRC_DIR"

cp -a "$PKG_DIR/debian" "$SRC_DIR/"
( cd "$SRC_DIR" && dpkg-buildpackage -us -uc -b )
```

For `dpkg-buildpackage -b` (binary-only), no `.orig.tar.gz` is required even with `3.0 (quilt)` source format. Use `unzip` in Build-Depends. Note: the zip sha256 is from GitHub's release page (look in the release body — NSA/upstream often publishes it there), not from a separate `.sha256` file.

> **Self-contained SDK keyed off an env var (devkitPro-style) — install to `/usr/lib/<name>` + `/etc/profile.d`, NOT `/usr/bin`.** Some pre-built upstreams (e.g. PVSnesLib) are whole toolchains whose internal build glue hard-references a root via an environment variable (`$PVSNESLIB_HOME/devkitsnes/bin/...`, `$DEVKITPRO/...`). The tools are never invoked from `$PATH` — the user writes a Makefile that `include`s the SDK's rules file and runs `make`. Package these by installing the entire tree under `/usr/lib/<name>/` and shipping `/etc/profile.d/<name>.sh` that `export`s the HOME var to that path (mode 0644). Do **not** symlink the SDK's binaries into `/usr/bin` — besides being unnecessary, an SDK often bundles its own pinned copy of a tool you already package standalone (PVSnesLib bundles `wla-65816`/`wla-spc700`/`wlalink` that would file-conflict with the `wla-dx` package). Keeping them under `/usr/lib/<name>/` means no conflict and no `Conflicts:` stanza. Bonus: nothing in `/usr/bin` ⇒ Policy §12.1 man-page mandate doesn't apply, so you skip writing man pages for a dozen internal tools.

> **Multi-binary split for a large pre-built SDK (`<name>-core` / `<name>-examples` / `<name>` meta).** When a pre-built upstream bundles a heavy examples/assets tree (PVSnesLib ships 47 MB of `snes-examples` vs a ~15 MB devkit), split one source into three `Package:` stanzas: `<name>-core` (`Architecture: amd64` — the toolchain ELFs) carrying the env-var + profile.d; `<name>-examples` (`Architecture: all`, `Depends: <name>-core (>= ${source:Version})`) carrying just the sample tree; and `<name>` (`Architecture: all` metapackage) `Depends`ing on both. `override_dh_auto_install` populates `debian/<name>-core/...` and `debian/<name>-examples/...` as separate trees (run the +x permission dance over **both**). The `build.sh` then moves THREE artifacts into `dist/` — and note the arch in each filename differs: `<name>-core_<ver>_${ARCH}.deb` but `<name>-examples_<ver>_all.deb` and `<name>_<ver>_all.deb` (hardcode `_all` for the arch:all ones, don't use `$ARCH`). Wire the lean `-core` (not the meta) into umbrella metapackages so a general install doesn't drag in the examples. dpkg auto-generates a `-dbgsym` `.ddeb` from `dh_strip`; leave it in the workdir (don't move it to `dist/`).

> **DEB_VERSION extraction — use `sed`, not `awk`.** The build template formerly used `awk 'NR==1 {match($0, /\(([^)]+)\)/, a); print a[1]}'` which requires gawk. Ubuntu containers ship mawk by default. Use:
>
> ```bash
> DEB_VERSION=$(sed -n '1s/.*(\(.*\)).*/\1/p' "$PKG_DIR/debian/changelog")
> ```

**npm package upstream flow (pure-JavaScript CLI tools):** Some tools are distributed exclusively via the npm registry and have no pre-built standalone binary. This is the right approach for pure-JS tools (no native addons). The pattern:

```bash
# Pin the sha256:
#   curl -fsSL https://registry.npmjs.org/@scope/pkg/-/pkg-X.Y.Z.tgz | sha256sum
UPSTREAM_VERSION=X.Y.Z
SHA256=<pinned>
NPM_URL="https://registry.npmjs.org/@scope/pkg/-/pkg-${UPSTREAM_VERSION}.tgz"

# npm tarballs ALWAYS extract to a top-level "package/" directory:
curl -fsSL -o "$ORIG_TARBALL" "$NPM_URL"
echo "$SHA256  $ORIG_TARBALL" | sha256sum -c -
tar -xzf "$ORIG_TARBALL" -C "$WORKDIR"
SRC_DIR="$WORKDIR/${NAME}-${UPSTREAM_VERSION}"
mv "$WORKDIR/package" "$SRC_DIR"        # ← always "package/", not the pkg name

# Install runtime deps (creates node_modules/):
( cd "$SRC_DIR" && npm install --omit=dev --ignore-scripts --legacy-peer-deps 2>&1 )
# --legacy-peer-deps: Ubuntu 26.04's npm 9.2.0 does strict peer-dep validation
# even for devDeps you're omitting; this flag reverts to npm v6 behavior.
# --ignore-scripts: skip lifecycle scripts (postinstall, etc.) for security.
```

Key `debian/control` fields for a pure-JS npm package:
- `Build-Depends: debhelper-compat (= 13), nodejs, npm`
- `Architecture: all` (no native code → one .deb for all arches)
- `Depends: ${misc:Depends}, nodejs (>= 22)` — Ubuntu 26.04 ships nodejs 22.22.1 in universe

Key `debian/rules` for an npm package:

```makefile
#!/usr/bin/make -f
export DEB_BUILD_MAINT_OPTIONS = hardening=+all

%:
	dh $@

override_dh_auto_configure:
override_dh_auto_build:
    # node_modules/ already populated by npm install in build.sh
override_dh_auto_test:

override_dh_auto_install:
	install -d $(CURDIR)/debian/<name>/usr/lib/<name>
	install -d $(CURDIR)/debian/<name>/usr/bin
	cp -r bin lib node_modules package.json $(CURDIR)/debian/<name>/usr/lib/<name>/
	printf '#!/bin/sh\nexec /usr/bin/node /usr/lib/<name>/bin/<entry>.mjs "$$@"\n' \
		> $(CURDIR)/debian/<name>/usr/bin/<name>
	chmod 755 $(CURDIR)/debian/<name>/usr/bin/<name>

override_dh_strip:
    # Pure JavaScript — no ELF binaries to strip
```

Installation layout:
- `/usr/lib/<name>/` — package files + node_modules (runtime module resolution works from here)
- `/usr/bin/<name>` — wrapper shell script: `exec /usr/bin/node /usr/lib/<name>/bin/<entry>.mjs "$@"`

The `Architecture: all` .deb filename is `<name>_<ver>_all.deb` — hardcode `_all` in `build.sh`'s DEB path (not `dpkg --print-architecture` which returns the host arch).

**Smoke test caveat:** Ubuntu's Docker image disables man page extraction via `/etc/dpkg/dpkg.cfg.d/excludes` (`path-exclude=/usr/share/man/*`). `dpkg -L <pkg>` will list the man page as installed, but `ls /usr/share/man/` won't show it. Verify with `dpkg -L` + `dpkg-deb -c`, not with `ls` after install.

**npm install creates empty scope dirs:** `@esbuild/`, `@rollup/`, etc. may appear as empty directories in `node_modules/` after install — these are scope-dir artifacts from Ubuntu's system npm package and contain no files. Harmless; lintian ignores empty dirs.

---

## Step 3 — Generate the `debian/` tree

```bash
cd <name>-<upstream>
DEBEMAIL="packages@<repo-domain>" DEBFULLNAME="Foundry Linux" \
  dh_make -y \
    --packagename "${NAME}_${UPSTREAM}" \
    --single \
    --copyright <license-shortname> \
    --createorig \
    ;
```

`<license-shortname>` is one of `gpl2`, `gpl3`, `lgpl2`, `lgpl3`, `apache`, `bsd`, `mit`. Detect from `COPYING` / `LICENSE` if present, otherwise ask.

`dh_make` generates `debian/{control,changelog,copyright,rules,compat,source/format,...}` plus several `*.ex` example files. Then patch the generated files using the templates shipped with this skill (`~/.claude/skills/package/templates/`):

1. **`debian/control`** — replace `<TEMPLATES>/control` substitutions:
   - `<NAME>` → package name
   - `<DESCRIPTION_SHORT>` → one-line description (≤ 60 chars, no trailing period)
   - `<DESCRIPTION_LONG>` → multi-line, each line starts with single space, period-only lines for paragraph breaks
   - `<HOMEPAGE>` → upstream URL
   - `<MAINTAINER>` → `Foundry Linux <packages@<domain>>`
   - `<BUILD_DEPS>` → extra build-time deps (e.g. `cmake`, `pkg-config`); always include `debhelper-compat (= 13)`
   - `<DEPENDS_EXTRA>` → extra runtime deps beyond `${shlibs:Depends}, ${misc:Depends}`
   - `<SECTION>` → e.g. `devel`, `utils`, `sound`
   - `<ARCHITECTURE>` → `any` (per-arch build) or `all` (pure metapackage)
   - **`X-Repology-Project`** (Source stanza) → the package's Repology project slug,
     which drives the apt-index version badge. **Required for every vendored package** —
     `scripts/check-repology-badges.sh` (a git pre-commit + Claude PostToolUse guard, and
     `task check-badges`) fails the commit if a `packages/*/build.sh` package omits it.
     The slug is frequently **not** the Debian package name — look it up at
     `https://repology.org/api/v1/projects/?search=<term>`: the bare name is often empty
     or a collision (e.g. `asar` is the Electron tool; the SNES assembler is
     `asar-snes-assembler`), and PyPI packages are `python:<name>` (so `python3-picire` →
     `python:picire`). If the upstream genuinely isn't on Repology (your own tool, too
     niche), set `X-Repology-Project: none` — the field stays present (so the choice is
     deliberate) and the index skips the badge. `task audit-badges` reports coverage;
     `task set-badge PKG=<pkg> PROJECT=<slug|none>` sets it without hand-editing control.
     **The field has a second consumer:** `scripts/generate-repology-ruleset.sh` (the Repology
     *producer* onboarding) derives the `repology-rules` YAML from it — a `setname` when the slug
     differs from the source name (`task`→`go-task`, `python3-picire`→`python:picire`), a `remove`
     for `none` + the un-fielded metapackages. After adding/renaming a vendored package, run
     `task gen-repology-ruleset` so `repology/foundry-linux.yaml` stays in sync for the eventual
     repology-rules PR.

2. **`debian/copyright`** — replace `<TEMPLATES>/copyright`:
   - DEP-5 format
   - Upstream copyright years + holders (from upstream's own COPYING / LICENSE / source-file headers)
   - License text — for GPL/LGPL/MIT/etc., reference `/usr/share/common-licenses/...`
   - **ISC / 0BSD / MIT-no-attribution:** `dh_make --copyright` doesn't accept `isc`. Use `--copyright bsd` to get a BSD-2-clause stub, then hand-rewrite `debian/copyright` with the actual ISC text. Name the block `License: ISC-<pkgname>` (not `BSD-2-Clause`) so it's unambiguous.

3. **`debian/changelog`** — replace with `<TEMPLATES>/changelog`:
   - Single initial entry, target distribution = the **codename of the repo's suite** (look up at `apt/public/dists/*/Release` → `Codename:` field). For `apt.foundrylinux.org` this is `resolute` — confirmed by inspecting existing package changelogs (f9dasm, vgmstream, foundry-retro-tools all use `resolute`). **Don't put `bookworm`/`noble`/`questing`/`stable` in the changelog distribution field** — aptly republishes under the repo's own codename regardless, and a mismatch is misleading.
   - Version = `<UPSTREAM>-<REVISION>` (e.g. `2.4.1-1foundry1`)
   - Author/date from `DEBEMAIL`/`DEBFULLNAME` + `date -R`
   - **Debian version must start with a digit.** If the upstream tag has a non-numeric prefix (e.g. `r2083`, `v1.2.3`), strip it: `r2083` → `2083`, `v1.2.3` → `1.2.3`. A version like `r2083-1foundry1` will fail `dpkg-buildpackage` with "version number does not start with digit". The `debian/watch` regex should capture only the numeric portion as the version.

4. **`debian/rules`** — use the right template for the upstream type:
   - **Source-compiled upstream (Makefile/autotools/cmake):** start from `templates/rules`. Typically `dh $@` is sufficient; add override targets only for quirks.
   - **Pre-built binary upstream (zip/tarball, no compile):** start from `templates/rules-prebuilt.mk`. See the pre-built section below for the full pattern.
   - **Python package upstream:** see the **Python packages** section below.
   - Common source-build overrides:
     - Source build root is not the package root → `override_dh_auto_build: dh_auto_build -- -C <subdir>`
     - Tests must be skipped → `override_dh_auto_test:` (empty body)
     - Custom install path → `override_dh_auto_install: make install DESTDIR=$(CURDIR)/debian/<NAME> prefix=/usr`
   - **Do NOT** add manual `strip` calls — `dh_strip` runs automatically.
   - **Do NOT** disable `dh_strip` unless the user explicitly wants debug symbols shipped.

   **Python packages (setuptools / hatchling / other pyproject.toml backends):**

   Always use `--buildsystem=pybuild` — never just `--with python3` bare. In debhelper compat 13, `dh_auto_clean` refuses to run `python setup.py clean` and exits with "This feature was removed in compat 12." The pybuild buildsystem handles clean, build, install, and test correctly for all Python build backends.

   ```makefile
   export DEB_BUILD_MAINT_OPTIONS = hardening=+all
   export PYBUILD_NAME = <pypi-import-name>   # e.g. "glfw", "mss", "librosa"

   %:
       dh $@ --with python3 --buildsystem=pybuild

   override_dh_auto_test:
       # skip — tests require display, network, or optional deps not in Build-Depends
   ```

   `PYBUILD_NAME` must match the Python import name (what you'd `import` in Python), not the PyPI package name — they differ when the PyPI name has hyphens (e.g. PyPI `my-pkg` → `PYBUILD_NAME = my_pkg`).

   **Build-Depends by backend:**

   | Build backend | Additional Build-Depends |
   |---|---|
   | `setuptools` (legacy `setup.py`/`setup.cfg`, no `[build-system]`) | `dh-python python3-all python3-setuptools` |
   | `setuptools` **with a `pyproject.toml [build-system]`** | `dh-python python3-all python3-setuptools pybuild-plugin-pyproject` — without the plugin, pybuild takes the PEP517 path on Ubuntu 26.04 and dies with `configure: plugin pyproject failed with: PEP517 plugin dependencies are not available`. If `[build-system].requires` lists `setuptools_scm`, also add `python3-setuptools-scm` **and** `export SETUPTOOLS_SCM_PRETEND_VERSION=<ver>` in `debian/rules` (release sdists carry no git tags, so version detection otherwise fails). |
   | `hatchling` | `dh-python python3-all pybuild-plugin-pyproject python3-hatchling` |
   | `flit` | `dh-python python3-all pybuild-plugin-pyproject python3-flit-core` |
   | `poetry` | `dh-python python3-all pybuild-plugin-pyproject python3-poetry-core` |

   Check `pyproject.toml → [build-system] → requires` and `build-backend` to identify which backend applies. All of these are in Ubuntu 26.04 universe.

   **Resolve the full *runtime* dep tree against universe FIRST — then recurse, or fall back to pipx.** A Python package's `Depends:` (its `requires_dist` / `[project].dependencies`) must each exist in universe *at a satisfying version*, or the `.deb` installs but is broken. Any runtime dep that's missing or too old must itself be packaged (recursively): `picire` pulls `inators` (not in universe → also package `python3-inators`). List the tree and check each before committing to `.deb`:

   ```bash
   for dep in <dep1> <dep2> ...; do printf "%-22s " "$dep"; apt-cache policy "python3-$dep" 2>/dev/null | awk "/Candidate/{print \$2}" | grep . || echo NOT-IN-UNIVERSE; done
   ```

   **When the cascade is deep, prefer `pipx` over `.deb`.** If a Python *application* needs several missing or too-new deps (e.g. `shrinkray` needs `textual>=8` vs universe's `2.1.2`, plus `textual-plotext` which isn't packaged at all), packaging the whole subtree is a maintenance sink. Install it via `pipx` in the Phase 0 script instead (precedent: `pipx install codemagic-cli-tools` in `install-foundry-ios-development.sh`). **Trade-off:** a pipx tool is *not* in any metapackage `Depends:` and therefore *not baked into the ISO* — it lands only on installed/booted systems. Use `.deb` when ISO presence matters and the subtree is shallow; use `pipx` when the subtree is deep and installed-system presence is enough.

   **Old package + much-newer dep → smoke-test the integration, not just the build.** A `.deb` can build cleanly yet fail at import: e.g. `picire` (2021) against `inators` (2.1.1, 2025) may hit API drift. Run the actual CLI (`<cmd> --help` plus a one-line real invocation) in the smoke-test container; if it breaks, pin a dep version contemporaneous with the package.

   **Python 3.13+ audioop removal:** `audioop` was removed from the Python stdlib in Python 3.13. Ubuntu 26.04 ships Python 3.14, so any package that does `import audioop` will fail. The fix is `python3-audioop-lts` (in Ubuntu universe at 0.2.2-2), which reinstates the `audioop` module. Add it to `Depends:` for any audio-manipulation package that uses audioop (check `grep -r audioop` in the source). Note: `pyaudioop` (the other common fallback name) does **not** exist on PyPI — `audioop-lts` is the correct package.

   **PyPI wheel binary extraction (pre-built Rust/native CLIs):** When packaging a tool like `ruff` that distributes a pre-built native binary inside a Python wheel, the binary lives at:
   ```
   <pkgname>-<version>.data/scripts/<binary>
   ```
   inside the wheel zip (not `<pkgname>/bin/<binary>` as sometimes assumed). Unzip the wheel flat into the source directory, then install the binary in `override_dh_auto_install`:
   ```makefile
   UPSTREAM = X.Y.Z
   override_dh_auto_install:
       install -D -m 0755 <pkgname>-$(UPSTREAM).data/scripts/<binary> \
           $(CURDIR)/debian/<pkg>/usr/bin/<binary>
   ```

   **cmake upstreams with a legacy Makefile or configure.ac alongside CMakeLists.txt:** debhelper may not auto-detect cmake if the source also contains `Makefile` or `configure.ac`. Specify `--buildsystem=cmake` explicitly on BOTH the configure AND build override targets, and add an empty `override_dh_autoreconf:` to skip the autotools regeneration step (autoreconf will likely fail if the `configure.ac` was written for an old autoconf):

   ```makefile
   override_dh_autoreconf:
       # upstream has configure.ac but cmake is the supported Linux build —
       # skip autoreconf so debhelper doesn't try to regenerate autotools.

   override_dh_auto_configure:
       dh_auto_configure --buildsystem=cmake -- \
           -DCMAKE_BUILD_TYPE=Release \
           ...

   override_dh_auto_build:
       dh_auto_build --buildsystem=cmake
   ```

   Also add `pkg-config` to `Build-Depends` in `debian/control` (and to the CI apt-get install list in `build.sh`) whenever cmake uses `find_package(PkgConfig)` to locate libraries — otherwise cmake's configure step silently skips all pkg-config–discovered deps (`-- Could NOT find PkgConfig`) and the link fails or builds without expected codecs.

   **cmake upstream with build root in a subdirectory:** if `CMakeLists.txt` lives in a subdirectory (e.g. `gtk/`), pass `--sourcedir=<subdir>` to both configure and build overrides:

   ```makefile
   override_dh_auto_configure:
       dh_auto_configure --buildsystem=cmake --sourcedir=gtk -- \
           -DCMAKE_BUILD_TYPE=Release \
           ...

   override_dh_auto_build:
       dh_auto_build --buildsystem=cmake
   ```

   **`-Werror=format-security` from system headers (glib-2.0 on ubuntu 26.04):** `hardening=+all` adds `-Werror=format-security`, which `/usr/include/glib-2.0/glib/gmessages.h` trips in ubuntu 26.04. Fix with `hardening=+all,-format` — this preserves PIE, relro, stack-protector, and fortify while dropping only the format-string strictness:

   ```makefile
   export DEB_BUILD_MAINT_OPTIONS = hardening=+all,-format
   ```

   Affects any package that includes GTK/glib headers. If the package's own code (not system headers) triggers the warning, fix the source instead.

   **`$` in sed patterns inside Makefile rules:** `$` is a Makefile metacharacter — `$E` expands variable `E` (empty), so `s/^Exec=FOO$/Exec=bar/` silently becomes `s/^Exec=FOOxec=bar/` (unterminated), causing "unterminated `s' command". Escape `$` as `$$` inside Makefile rule bodies:

   ```makefile
   # Wrong — $ eaten by make, produces "unterminated s command"
       sed -i 's/^Exec=PPSSPPSDL$/Exec=ppsspp %F/' ...
   # Correct
       sed -i 's/^Exec=PPSSPPSDL$$/Exec=ppsspp %F/' ...
   ```

   **cmake upstreams with no Linux `install()` target:** cmake's `CMAKE_INSTALL_PREFIX` may be wired only for Windows. Add `override_dh_auto_install` to manually copy the built binary:

   ```makefile
   DEB_HOST_GNU_TYPE ?= $(shell dpkg-architecture -qDEB_HOST_GNU_TYPE)
   BUILD_DIR = obj-$(DEB_HOST_GNU_TYPE)

   override_dh_auto_install:
       install -D -m 0755 $(BUILD_DIR)/cli/<binary> \
           $(CURDIR)/debian/<name>/usr/bin/<binary>
   ```

   **Pre-built binary upstream (zip/tarball, no source compile):** Use `templates/rules-prebuilt.mk` as the starting point. The pattern handles three non-obvious pitfalls unique to binary repacking:

   1. **Zip sets +x everywhere.** Upstream zip archives typically mark all files executable. The install override strips +x from everything (`chmod 644`), then selectively restores it to ELF binaries (via `file | grep ELF`) and scripts (via `head -c 2 | grep -qF "#!"`). Use `head -c 2`, not `grep -l "^#!"` — binary files (`.whl`, `.tar.gz`, `.fidbf`) can contain the byte sequence `#!` internally and will false-match a whole-file grep.

   2. **`dh_fixperms` does not actively set +x in `/usr/lib/`.** `dh_fixperms` applies `chmod go=rX,u+rw,a-s` — which only propagates existing +x, but does not add it. Files in non-standard dirs (anything outside `/usr/bin/`, `/usr/sbin/`) lose +x if they didn't already have it set at the time `dh_fixperms` runs. Re-run the ELF and shebang detection in `override_dh_fixperms` after calling `dh_fixperms`.

   3. **`dh_strip`/`objcopy` resets permissions after `override_dh_fixperms`.** `dh_strip` calls `objcopy --add-gnu-debuglink` which modifies (and resets to 0644) any ELF file it touches — and it runs *after* `override_dh_fixperms`. Add a final ELF chmod restore in `override_dh_strip` AFTER calling `dh_strip`. Exclude `.so` and `.so.*` — shared libraries must be 0644 per Debian Policy §8.1.

   The debhelper call order is: `override_dh_auto_install` → `override_dh_fixperms` → `override_dh_strip` → `dh_md5sums` → `dpkg-deb --build`. The permission dance must happen in that order.

   Key `debian/control` fields for a pre-built binary package:
   - `Build-Depends: debhelper-compat (= 13), unzip` (add `unzip` — it's not installed by default)
   - `Architecture: amd64` (not `any` — the zip is for a specific arch; build on amd64 for amd64 users)
   - `Depends: ${shlibs:Depends}, ${misc:Depends}, <runtime-dep>` — include `${shlibs:Depends}` even for pre-built packages so `dh_shlibdeps` can populate it from the native ELF binaries in `/usr/lib/<name>/`

5. **`debian/source/format`** — depends on whether there's an upstream:
   - Vendored upstream (the common case): `3.0 (quilt)`. dh_make defaults to this; verify.
   - Pure metapackage (no upstream tarball, packaging *is* the source): `3.0 (native)`. Version in `debian/changelog` has no `-revision` suffix (e.g. `1.0.1`, not `1.0.1-1foundry1`).

6. **`debian/watch`** — replace with `<TEMPLATES>/watch`, format:

    ```
    version=4
    <UPSTREAM_DOWNLOAD_PAGE_REGEX>
    ```

   For GitHub with standard `v`-prefixed tags: `github.com/<owner>/<repo>/tags .*archive/refs/tags/v?@ANY_VERSION@\.tar\.gz` (prefix with `https://` in the actual `debian/watch`).

   For non-standard prefixes (e.g. `r<number>`): write a custom pattern — e.g. for vgmstream:
   ```
   version=4
   https://github.com/vgmstream/vgmstream/tags .*/archive/refs/tags/r(\d+)\.tar\.gz
   ```
   The `@ANY_VERSION@` shorthand only works when the version part is a bare number (with or without `v`). For any other prefix, write the regex manually and capture the numeric part in parens.

7. **Man pages — non-negotiable.** Every binary that ships in `/usr/bin/` MUST have a section-1 man page (Debian Policy §12.1). Most upstreams ignore this. After running `dh_make`, run the binary with `-h`/`--help`/`-v` to capture its usage, then:

   - Author short `.1` files under `debian/man/<binary>.1` using standard troff (`.TH`, `.SH NAME`, `.SH SYNOPSIS`, `.SH DESCRIPTION`, `.SH OPTIONS`, `.SH SEE ALSO`, `.SH AUTHORS`, `.SH COPYRIGHT`). For a multi-binary package, cross-reference siblings via `.BR sibling (1)` in SEE ALSO.
   - List them in `debian/<package>.manpages`, one path per line. `dh_installman` picks the list up automatically and gzips them into `/usr/share/man/man1/`.
   - For tiny utilities whose `--help` is exhaustive, `help2man --no-info --no-discard-stderr -o debian/man/<binary>.1 ./<binary>` at build time in `override_dh_auto_build` is acceptable, but only if the `--help` output is rich enough to produce a useful page. Hand-written is better for the main binary; help2man is fine for thin sibling utilities. Don't ship the upstream HTML manual as a substitute — DEP-5 docs in `/usr/share/doc/` don't satisfy Policy §12.1.

8. **Delete dh_make's `*.ex` example files** (`postinst.ex`, `prerm.ex`, etc.) unless one is actually needed.

9. **`debian/patches/series`** — empty file. Quilt patches (if any) go in `debian/patches/*.patch` and listed here.

10. **Compat level** — `dh_make` sets `Build-Depends: debhelper-compat (= 13)` in `debian/control`. Drop any legacy `debian/compat` file.

---

## Step 4 — Build & verify

**Always build in a fresh Docker container** — not on the host system. Host packages can silently satisfy build dependencies and mask missing `Build-Depends:` entries that will break CI. Use the target distribution:

```bash
docker run --rm \
    -v "$REPO_ROOT:/repo" \
    ubuntu:26.04 bash -c '
set -euo pipefail
DEBIAN_FRONTEND=noninteractive apt-get update -qq 2>/dev/null
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    build-essential debhelper dpkg-dev lintian <extra-build-deps> 2>/dev/null
cd /repo
bash packages/<name>/build.sh
lintian dist/<name>_*.deb 2>&1
'
```

Inside the container (or for one-off debugging), the raw build command is:

```bash
dpkg-buildpackage -us -uc -b      # binary .deb
dpkg-buildpackage -us -uc -S -d   # source package (.dsc + tarballs) — ship this too
# -us/-uc  unsigned source/changes
# -b  binary-only · -S  source-only · -d  skip build-dep check (the source pass needs none)
```

**Build the source package too — don't ship a binary-only repo.** A real apt repo publishes a
`Sources` index so users can `apt-get source <pkg>` and rebuild (reproducibility), and it's how
Repology tracks Debian/Ubuntu derivatives (`DebianSourcesParser`). The source pass emits
`<name>_<ver>.dsc` + `…debian.tar.xz` (+ the `.orig.` tarball for quilt). Move all of them into
`dist/` alongside the `.deb` — aptly publishes a `Sources` index automatically once source
packages are in the repo.

- **`3.0 (quilt)` needs `<src>_<upstreamver>.orig.tar.{gz,xz}` in the *parent* dir.** The
  vendored `build.sh` pattern already stages this (it downloads the upstream tarball under
  exactly that name before extracting — see `packages/halfempty/build.sh`), so the source pass
  is essentially free: just add it after the `-b` build, before `WORKDIR` is cleaned, and move
  the `.dsc`/tarballs to `dist/`. `3.0 (native)` metapackages need nothing extra.
- **Run `lintian` on the `.dsc`, not just the `.deb`.** Source builds run source-level checks
  the binary build skips — e.g. `build-depends-on-obsolete-package: pkg-config => pkgconf`.
  Fix these (or override with justification) the same as binary lint.
- **Binary assets vendored under `debian/` (an icon `.png`, etc.) fail the source pass** with
  `dpkg-source: error: unwanted binary file: debian/<file>` — `3.0 (quilt)` refuses binaries
  under `debian/` unless allowlisted. The `-b` binary build doesn't check this; only `-S` does.
  Add a `debian/source/include-binaries` file listing each one (one path per line, e.g.
  `debian/<name>.png`). Real case: `mesen2` (vendors a desktop icon).
- **Patches applied *in-tree* (not via quilt) break the source pass** with `dpkg-source: the
  patch has fuzz`. Some upstreams are CRLF and GNU `patch`/quilt fuzz on them, so `build.sh`
  applies the fix with `perl -i` instead — but `dpkg-source -b` then re-applies the
  `debian/patches/series` patches itself against the pristine orig and they don't apply. Fix:
  after the in-tree patching and **before** the source pass, drop the staged pristine orig and
  empty the staged series so `emit_source_package` synthesises a self-contained orig from the
  already-patched tree and `dpkg-source` applies nothing:
  `rm -f "$WORKDIR/<name>_<ver>.orig.tar."* ; : > "$SRC_DIR/debian/patches/series"`. The binary
  build is unaffected (its `dpkg-source --before-build` then applies nothing; the tree is already
  patched). Real case: `tilemap-studio` (CRLF upstream, patched via perl).

The .deb lands in `$WORKDIR/<name>_<upstream>-<revision>_<arch>.deb`. Build-time output you should see (proof debhelper is doing its job):

| Line | What's happening |
|---|---|
| `dh_auto_build` | runs `make` (or cmake, etc.) with hardening flags |
| `dh_strip` | strips debug info from `usr/bin/*`, `usr/lib/*` |
| `dh_compress` | gzips man pages and changelog |
| `dh_fixperms` | normalizes permissions (man 0644, bin 0755) |
| `dh_installdocs` | copies README/NEWS/etc to `usr/share/doc/<pkg>/` |
| `dh_shlibdeps` | resolves `${shlibs:Depends}` from the actual linked sonames |
| `dh_gencontrol` | substitutes `${shlibs:Depends}`, `${misc:Depends}` into final `debian/control` |
| `dh_md5sums` | generates `DEBIAN/md5sums` |
| `dpkg-deb --build` | assembles the final .deb |

Verify the output:

```bash
dpkg-deb -I <name>_*.deb       # control fields — confirm Depends has resolved libc6 etc.
dpkg-deb -c <name>_*.deb       # file listing
file <name>-<upstream>/debian/<name>/usr/bin/*  # confirm "stripped" appears
lintian <name>_*.deb 2>&1 | grep -vE "^N:"      # warnings/errors — must be empty
```

### Metapackages — local dependency-chain verification

A pure metapackage builds in ~2 s but lintian alone won't tell you if the `Depends:` chain actually resolves on a clean target. Use `dpkg-scanpackages` to make your `dist/` a local apt source, then attempt the install inside a fresh container:

```bash
docker run --rm -v "$(pwd)/dist:/debs" ubuntu:26.04 bash -c '
  apt-get update -qq 2>&1 >/dev/null
  apt-get install -qq -y dpkg-dev lintian 2>&1 >/dev/null
  cd /debs && dpkg-scanpackages -m . > Packages 2>/dev/null
  echo "deb [trusted=yes] file:/debs ./" > /etc/apt/sources.list.d/local.list
  apt-get update -qq 2>&1 >/dev/null

  # Lintian (catches obsolete deps + license + section issues)
  lintian /debs/<metapackage>_*.deb && echo PASS || echo FAIL

  # Install with strict Depends (no Recommends/Suggests noise)
  DEBIAN_FRONTEND=noninteractive apt-get install -qq -y \
    --no-install-recommends <metapackage> 2>&1 | tail -5

  # apt-cache depends shows the resolved tree
  apt-cache depends <metapackage>
'
```

**Pin `ubuntu:26.04` explicitly, not `ubuntu:latest`.** `ubuntu:latest` currently resolves to **noble (24.04)** at Docker Hub, which is *not* our target distribution. For a Foundry/WorldFoundry-style apt repo whose suite is 26.04 "resolute", building or smoke-testing on `ubuntu:latest` silently pins shlibs to the wrong sonames (e.g. `libavcodec60` instead of `libavcodec62`) and ships an uninstallable artifact. The same rule applies to CI: the publish workflow's build step MUST run inside `ubuntu:26.04`, not on the GitHub-hosted runner — see the `new-web-apt-repo` skill's `in-docker.sh` wrapper.

Common failures and what they mean:
- `unable to correct problems, you have held broken packages` → a transitive Depends has an unsatisfiable version floor (e.g. `blender (>= 4.2.0)` when noble has `4.0.2`). Either widen the floor, range-pin, or pick a different target distro.
- `depends-on-obsolete-package` from lintian → see the obsolete-dep row in the Common warnings table above.
- Install succeeds but `apt-cache depends` shows your Recommends as `Depends` → check for typos; spaces vs commas in the control file.

> **Lintian gate — BLOCKING before commit/upload.** Lintian must come back clean. Both `E:` (errors) AND `W:` (warnings) must be addressed before Step 6. If `lintian` prints anything other than the "running with root privileges is not recommended!" advisory, **stop and fix it** — do not ship a `.deb` with open warnings.
>
> Common warnings and how to fix each (do not just suppress with overrides):
>
> | Warning tag | Cause | Fix |
> |---|---|---|
> | `no-manual-page` | Binary in `/usr/bin/` has no section-1 man page | Write `debian/man/<binary>.1` and list in `debian/<pkg>.manpages` (see Step 3 §7). Required by Policy §12.1. |
> | `binary-without-manpage` | Older wording of the same thing | Same fix. |
> | `hardening-no-bindnow` | Linker missing `-Wl,-z,now` | Set `export DEB_BUILD_MAINT_OPTIONS = hardening=+all` at the top of `debian/rules`. |
> | `hardening-no-pie` | Binary not PIE | Same fix; `gcc-12+` defaults to PIE so this usually appears only with custom `LDFLAGS` overrides. |
> | `command-with-path-in-maintainer-script` | Absolute path in `postinst`/`prerm` | Use the bare command; `PATH` is set. |
> | `non-standard-dir-perm` | `0700` or similar on a `/usr/...` dir | Use `0755`; let `dh_fixperms` normalize. |
> | `executable-not-elf-or-script` | `.dsp`/`.vcproj` MS-VS project file got installed | Don't install it; remove the line from `debian/<pkg>.docs` or the override target. |
> | `package-installs-python-bytecode` | `.pyc` / `__pycache__` in the package | Add `debian/<pkg>.maintscript` cleanup or fix `override_dh_auto_install`. |
> | `debian-changelog-line-too-long` | A line in `debian/changelog` > 80 chars | Wrap the offending line — typically a long URL in a `* Source:` bullet. Wrap at the last `/` before col 80; continue with 4-space indent on the next line. |
> | `depends-on-obsolete-package` | `Depends:` lists a transitional dummy that's been renamed | Use the real successor package. Most common case: `libgl1-mesa-dev` → `libgl-dev` on noble+ (the old name is a transitional dummy that just pulls `libgl-dev`). Likewise check `libglu1-mesa-dev` → `libglu-dev` (virtual; still real package on noble), `libpng12-dev` → `libpng-dev`, etc. Run `apt-cache show <oldname> \| grep -i transitional` to confirm. |
>
> A `debian/<pkg>.lintian-overrides` file is acceptable **only** for tags that are genuinely impossible to fix at this layer (e.g. `embedded-library` when the upstream truly vendors a known-good copy). Every line must include a one-sentence justification:
>
> ```
> # Upstream pins zlib 1.3 inline because their build system can't link
> # external; safe — version matches Debian's libz1, kept under review.
> <pkg>: embedded-library [usr/bin/<binary>: libz]
> ```
>
> Do **not** use `lintian-overrides` to silence `no-manual-page`, `hardening-*`, or any tag in the table above — those have real fixes.
>
> **Pre-built binary packages: tags that are genuinely irreducible.** The following tags appear for pre-built binary repacking and cannot be fixed at the packaging layer. Use `lintian-overrides` with a per-line justification:
>
> | Tag | Why it's irreducible | Override pattern |
> |---|---|---|
> | `hardening-no-pie` | Pre-built ELF binaries compiled without `-fPIE` by upstream CI; cannot recompile | `<pkg>: hardening-no-pie *` |
> | `hardening-no-bindnow` | Pre-built ELF binaries linked without `-Wl,-z,now` by upstream CI; cannot relink | `<pkg>: hardening-no-bindnow *` |
> | `embedded-library` | Upstream statically links a known library (e.g. zlib) because their cross-platform build can't use system libs | `<pkg>: embedded-library <libname> [path/to/binary]` |
> | `missing-dep-on-jarwrapper` | Self-contained Java app with its own launcher; doesn't use Debian jarwrapper | `<pkg>: missing-dep-on-jarwrapper` |
> | `codeless-jar` | Module-descriptor JARs (MANIFEST.MF only, no .class files) used by the app's plugin system | `<pkg>: codeless-jar *` |
> | `unknown-java-class-version` | Multi-release JAR with classes targeting a future Java version (e.g. Java 25 acceleration code in bcprov) | `<pkg>: unknown-java-class-version *` |
> | `unusual-interpreter` | upstream script uses `/usr/bin/python` (unversioned) — app's own launcher sets the venv correctly at runtime | `<pkg>: unusual-interpreter *` |
> | `jar-not-in-usr-share` | Internal application JARs live in `/usr/lib/<pkg>/` by design; they are not public shared libraries | `<pkg>: jar-not-in-usr-share *` |
> | `binary-from-other-architecture` | Upstream zip bundles Windows PE files (`.exe`/`.dll`) for cross-platform projects; inert on Linux | `<pkg>: binary-from-other-architecture *` |
> | `windows-devel-file-in-package` | `.sln`/`.vcproj` project files bundled as training/exercise material; inert on Linux | `<pkg>: windows-devel-file-in-package *` |
> | `privacy-breach-google-adsense`, `privacy-breach-logo`, `privacy-breach-uses-embedded-file`, `privacy-breach-generic` | External references in upstream HTML docs/license pages; only active if user opens them in a browser — patching upstream HTML is out of scope for binary repackaging | `<pkg>: privacy-breach-google-adsense *` (repeat for each subtype) |
> | `national-encoding` | Non-UTF-8 binary data file (e.g. processor index) generated by upstream's build — transcoding would break the tooling that reads it | `<pkg>: national-encoding *` |
> | `extra-license-file` | Upstream-mandated `licenses/` directory (e.g. Apache-required third-party notices) at a non-standard path | `<pkg>: extra-license-file *` |
> | `script-not-executable` | Template file with a shebang (e.g. Velocity `.vm` template for generating daemon scripts) — the shebang is in the template output, not for direct execution | `<pkg>: script-not-executable [path/to/template.vm]` |

**Smoke install in a clean container:**

```bash
docker run --rm -v "$WORKDIR:/debs" ubuntu:26.04 bash -c "
    apt-get update -qq 2>/dev/null
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq /debs/<name>_*.deb
    # Run the program's --version or equivalent — proof the binary actually runs
    <main-binary> --version || <main-binary> -v
"
```

---

## Step 5 — Wire into foundry-apt

Copy the build artifacts into the foundry-apt tree:

```
foundry-apt/packages/<name>/
├── build.sh                  # wrapper: fetch tarball, verify sha256, dpkg-buildpackage
└── debian/                   # Debian source-package format (canonical, only)
    ├── control
    ├── changelog
    ├── copyright
    ├── rules
    ├── source/format
    ├── watch
    └── patches/series
```

`build.sh` is the thin shim — see [`templates/build.sh`](templates/build.sh). It:
1. Fetches the upstream tarball (sha256-verified)
2. Extracts to a tmpdir
3. Installs Build-Depends via apt-get (see below)
4. Copies the `debian/` tree from `packages/<name>/debian/` into the upstream tree
5. Runs `dpkg-buildpackage -us -uc -b`
6. Moves the .deb into `$REPO_ROOT/dist/`

**Build-Depends must be installed by `build.sh` itself** — do not assume the CI runner has them pre-installed. GitHub Actions runners run as a non-root user with passwordless `sudo`; Docker containers run as root. Use the `_apt()` helper in `templates/build.sh` which handles both:

```bash
if command -v apt-get >/dev/null; then
    _apt() { [[ $EUID -eq 0 ]] && apt-get "$@" || sudo apt-get "$@"; }
    _apt install -y --no-install-recommends \
        cmake pkg-config libfoo-dev ...   # ← fill from debian/control Build-Depends
fi
```

Replace `<BUILD_DEPENDS_SPACE_SEPARATED>` in the template with the non-boilerplate deps from `debian/control`'s `Build-Depends:` field (omit `debhelper-compat` and `build-essential` — those are installed globally by the CI step; list only the package-specific ones like `cmake`, `libfoo-dev`, etc.).

Then update the metapackage that depends on this one. The metapackage's `debian/control`
and `debian/changelog` are also canonical Debian source format — add `<name>` to `Depends:`
(move it out of `Recommends:` if it was there), and add a new `debian/changelog` entry
via:

```
( cd foundry-apt/packages/<metapackage> && dch -v <new-version> -D resolute "Promote <name> from Recommends to Depends" )
```

(Or hand-edit the changelog and bump the version in the topmost stanza.)

> **Transitive-only deps must go in `out_of_catalogue`.** If `<name>` is pulled only
> *transitively* — a library dep that rides via another package's `Depends:` and is **not**
> added to any metapackage's direct `Depends:` (e.g. `python3-inators` arrives via
> `python3-picire`) — add it to the `out_of_catalogue` array in `data/categories.json`.
> Otherwise `task site-build`'s catalogue audit (`scripts/build-packages-data.js`) flags it as
> an **unowned package and fails the site build/deploy** (`✗ unowned packages — build FAIL`).
> User-facing packages don't need this — they're owned by the metapackage `Depends:` you just
> edited.

**Pure metapackages use the same `debian/` layout.** No special path. The only difference
is `debian/source/format` = `3.0 (native)` (vs `3.0 (quilt)` for vendored upstreams) and
the version has no Debian revision suffix (`1.0.2`, not `2.4.1-1foundry1`). Every package
in foundry-apt now uses this layout — the previous legacy `DEBIAN/control` + hand-rolled
`build.sh` path was retired with xa65.

---

## Step 6 — Commit, sync, release

From the monorepo root:

```bash
git add foundry-apt/packages/<name>/ foundry-apt/packages/<metapackage>/debian/ TODO.md docs/plans/...
git commit -m "feat(foundry-apt): package <name> as a .deb (debhelper)"
git push
task bump   # syncs foundry-apt/ to the publish repo and tags next patch version
```

> **Repo-publish conventions (set once in the repo's publish script, not per-package — but
> don't let a package land in a repo that lacks them):**
> 1. **Origin/Label.** The aptly publish must pass `-origin`/`-label` set to the repo's vendor
>    name (e.g. `Foundry Linux`), not aptly's `. <suite>` default — apt clients and Repology
>    surface these. foundry-apt enforces it via `scripts/check-publish-metadata.sh` + a Claude
>    PostToolUse hook on `publish-local.sh`.
> 2. **Publish source packages.** The repo must carry a `Sources` index (Step 4 builds the
>    `.dsc` + tarballs into `dist/`; aptly publishes them automatically). Binary-only is a
>    smell — it blocks `apt-get source` and the `DebianSourcesParser` path Repology uses for
>    derivatives.
>
> The `new-web-apt-repo` skill scaffolds both for a fresh repo.

**After committing**, add a Debian ITP tracking item to `TODO.md` under `### Deferred follow-ups`:

```
- [ ] **File Debian ITP for `<name>`** — `<upstream-license>`, `<upstream-url>`. Check [wnpp.debian.org](https://bugs.debian.org/cgi-bin/pkgreport.cgi?pkg=wnpp) for existing RFP/ITP first.
```

Use `/todo` to add it, or append manually. This ensures every package we vendor has a tracked path back to the Debian archive.

> **`task sync` uses `git archive`** — only committed files are exported to the mirror. Do NOT run `build-all.sh` locally and then sync without committing first: dpkg-buildpackage leaves `debian/.debhelper/`, `debhelper-build-stamp`, `*.buildinfo`, `*.changes`, and `*.deb` files in the source tree. These are gitignored but `rsync` would copy them blindly. `git archive` sidesteps the problem entirely. If you see build artifacts showing up in a sync commit, check that `Taskfile.yml` is using `git archive` (not `rsync`) and that `foundry-apt/.gitignore` covers `packages/**/.debhelper/` etc.

Watch the publish workflow (`gh run watch -R foundry-linux/foundry-apt $RUN_ID`). When it goes green, verify on the live site:

```bash
curl -sSL https://<apt-domain>/ | grep <name>
docker run --rm ubuntu:<LTS> bash -c "
    # set up apt source (see new-web-apt-repo skill's 'Consume this repo' section)
    apt-get install -y <name>
    dpkg -s <name> | grep -E 'Version|Maintainer'
"
```

---

## Step 7 — Upstream the patches (LAST step — don't skip)

If `debian/patches/` ended up non-empty, **every patch that is a genuine portability/build fix — not Debian packaging glue — should be offered back upstream.** A patch we carry forever is a maintenance tax and a smell; a patch upstream accepts disappears from our tree on the next release. This is the difference between *vendoring* a project and *forking* it.

**Triage each patch in `debian/patches/series` into one of two buckets:**

| Bucket | Examples | Action |
|---|---|---|
| **Upstreamable** (a real bug/portability fix that helps everyone) | missing `#include` the compiler now requires (`<cstring>`, `<cstdint>`, `<FL/platform.H>`); a missing link library (`-lz`/`-lpng`) the build needs on a stricter linker; a `-Werror` trip from a newer toolchain; a hard-coded path that breaks off-Windows | **Send upstream** (below). Keep carrying it in `debian/patches/` until a release includes it, then drop it. |
| **Debian-only** (meaningless or wrong upstream) | rewriting an install path to `$(DESTDIR)/usr`; forcing system libs over a vendored copy *because Debian policy wants system libs*; disabling a vendored-dependency download; `.desktop`/manpage we authored | **Keep**, do not send. Add a one-line comment in the patch header: `# Debian-specific; not for upstream.` |

**How to send an upstreamable patch:**

1. **Give every quilt patch a DEP-3 header** (it doubles as the PR description). This is required for upstreamable patches and good practice for all of them:

   ```
   Description: add missing <cstring> include for GCC 15 / FLTK 1.4.5
    preferences.cpp uses strcpy/strncpy/strrchr but relied on a transitive
    include that FLTK 1.4.5's cleaned-up headers no longer provide.
   Author: Foundry Linux <packages@foundrylinux.org>
   Forwarded: https://github.com/<owner>/<repo>/pull/<n>   # fill in once opened
   Last-Update: <YYYY-MM-DD>
   ```

   Until the PR exists, use `Forwarded: not-yet` (or `Forwarded: no` for a Debian-only patch).

2. **Open the PR with `gh`** from a clean upstream checkout (NOT the packaging tree). The combined patch in `debian/patches/` is your diff; apply it to a fresh clone, branch, commit with a clear message, push to a fork, and `gh pr create`:

   ```bash
   gh repo fork <owner>/<repo> --clone --remote
   cd <repo> && git checkout -b fix-<short-desc>
   # apply the upstreamable hunks (quilt push, or git apply the specific patch)
   git commit -am "fix: <what and why — newer toolchain/linker needs this>"
   git push -u origin fix-<short-desc>
   gh pr create --title "..." --body "<the DEP-3 Description, expanded; note the build env: Ubuntu 26.04, GCC 15, FLTK 1.4.5>"
   ```

3. **Record the PR URL** back in the patch's `Forwarded:` header and in the package's `debian/changelog` entry, so the next packager knows it's in flight and can drop the patch once a release ships the fix.

4. If you **can't** open the PR in this run (no auth, upstream archived, user not ready), don't silently skip — **tell the user** which patches are upstreamable, paste the ready-to-send `gh` commands, and leave `Forwarded: not-yet` in the headers so it's tracked.

Don't upstream: our `.desktop` file, our man pages, `debian/`-tree anything, or version pins — those are ours.

---

## Verification checklist

Before reporting the skill output as done:

- [ ] Step 1 (universe check) ran and didn't find a duplicate; OR it did find one and you stopped + told the user.
- [ ] Step 2 (vendoring): sha256 pinned, tarball reproducible across two fetches.
- [ ] Step 3 (`debian/` tree): `debian/control` has the right Maintainer; `debian/copyright` is DEP-5; `debian/rules` is minimal `dh $@` with at most a couple of overrides; `debian/source/format` = `3.0 (quilt)`; `debian/watch` populated; every binary in `/usr/bin/` has a `debian/man/<binary>.1` listed in `debian/<pkg>.manpages`.
- [ ] Step 4: `file usr/bin/<binary>` reports "stripped"; `dpkg-deb -I` shows resolved `${shlibs:Depends}` with version constraints; **`lintian` returns clean — zero E: lines AND zero W: lines** (the only line allowed is the root-privileges advisory). If a warning is irreducible, it's recorded in `debian/<pkg>.lintian-overrides` with a one-line justification.
- [ ] Step 5: foundry-apt build-all.sh still works end-to-end with the new layout.
- [ ] Step 6: live `apt install <name>` works in a fresh container.
- [ ] Step 7: every patch in `debian/patches/` has a DEP-3 header; each is triaged upstreamable-vs-Debian-only; upstreamable ones are sent (PR URL in `Forwarded:`) or the user is told with ready-to-run `gh` commands.

---

## <a name="why-debhelper"></a>Why debhelper (vs hand-rolled `dpkg-deb --build`)

Direct comparison from packaging xa65 first the manual way, then re-evaluating against Ubuntu's debhelper-built xa65 (which now serves as the canonical upstream — our hand-rolled xa65 has since been retired, see [docs/plans/2026-05-18-retire-xa65.md] in the foundrylinux.org repo for the post-mortem):

| Field | Hand-rolled build.sh | debhelper / dh_make | Cost of being wrong |
|---|---|---|---|
| `.deb` size | 223 KB (unstripped) | 95 KB | 2.3× pool bloat; CDN bandwidth waste |
| `xa` binary size | 322 KB | 109 KB | Same |
| `Depends: libc6` | bare | `libc6 (>= 2.38)` (auto-resolved) | Installs on old libc → SIGSEGV at runtime when missing symbol called |
| Hardening flags | none | PIE + stack-protector + FORTIFY_SOURCE | Security exposure |
| `debian/copyright` | one-line text | DEP-5 (machine-readable) | License-audit tooling can't parse ours |
| `debian/watch` | absent | uscan-trackable | Manual version bumps; can't automate |
| Source package | none | `.dsc` + `.orig.tar.gz` + `.debian.tar.xz` | Can't upload to a PPA without redoing the work |
| `lintian` status | many warnings | clean (with attention) | Repo looks unprofessional |
| Standards-Version conformance | none claimed | `4.7.0` | Drift accumulates |
| Cross-build | manual `CC=`/`LD=` | `dh_auto_configure --host=<triplet>` | Bring-up cost for arm64 |
| `dh_strip` (auto debug-strip) | manual `strip` calls | yes | Forgetting to strip = ↑↑ size |
| `dh_compress` (man/changelog gzip) | manual | yes | lintian errors otherwise |
| `dh_fixperms` | manual `chmod` | yes | Wrong perms = lintian errors |

A hand-rolled approach is fine as a one-off, but the moment you have 2+ packages, debhelper amortises every manual step into a single `dh $@` line and the templates ship with safe defaults.

If you have a reason you *must* hand-roll (truly weird upstream that resists debhelper), document it in `packages/<name>/build.sh` as a comment with the specific reason — don't just bypass.
