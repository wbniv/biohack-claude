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
| `github.com/...` URL | `https://github.com/Arakula/f9dasm` | `gh api` to find latest tag/release; download the archive tarball |
| Tarball URL | `https://example.org/foo-1.2.3.tar.gz` | Download + sha256 pin |
| `.dsc` URL | `https://deb.debian.org/.../foo_1.2.3-1.dsc` | `dget` to fetch the existing source package; re-pack with Foundry packaging revision |
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

> **DEB_VERSION extraction — use `sed`, not `awk`.** The build template formerly used `awk 'NR==1 {match($0, /\(([^)]+)\)/, a); print a[1]}'` which requires gawk. Ubuntu containers ship mawk by default. Use:
>
> ```bash
> DEB_VERSION=$(sed -n '1s/.*(\(.*\)).*/\1/p' "$PKG_DIR/debian/changelog")
> ```

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

2. **`debian/copyright`** — replace `<TEMPLATES>/copyright`:
   - DEP-5 format
   - Upstream copyright years + holders (from upstream's own COPYING / LICENSE / source-file headers)
   - License text — for GPL/LGPL/MIT/etc., reference `/usr/share/common-licenses/...`
   - **ISC / 0BSD / MIT-no-attribution:** `dh_make --copyright` doesn't accept `isc`. Use `--copyright bsd` to get a BSD-2-clause stub, then hand-rewrite `debian/copyright` with the actual ISC text. Name the block `License: ISC-<pkgname>` (not `BSD-2-Clause`) so it's unambiguous.

3. **`debian/changelog`** — replace with `<TEMPLATES>/changelog`:
   - Single initial entry, target distribution = the **codename of the repo's suite** (look up at `apt/public/dists/*/Release` → `Codename:` field). For the foundry-style apt repo this is `stable` (Suite + Codename both = `stable`), not the Debian/Ubuntu release name. **Don't put `bookworm`/`noble`/`questing` in the changelog distribution field** — aptly republishes under the repo's own codename regardless, and a mismatch is misleading. Confirmed by inspecting `apt/public/dists/<codename>/Release` after the first publish.
   - Version = `<UPSTREAM>-<REVISION>` (e.g. `2.4.1-1foundry1`)
   - Author/date from `DEBEMAIL`/`DEBFULLNAME` + `date -R`
   - **Debian version must start with a digit.** If the upstream tag has a non-numeric prefix (e.g. `r2083`, `v1.2.3`), strip it: `r2083` → `2083`, `v1.2.3` → `1.2.3`. A version like `r2083-1foundry1` will fail `dpkg-buildpackage` with "version number does not start with digit". The `debian/watch` regex should capture only the numeric portion as the version.

4. **`debian/rules`** — use the right template for the upstream type:
   - **Source-compiled upstream (Makefile/autotools/cmake):** start from `templates/rules`. Typically `dh $@` is sufficient; add override targets only for quirks.
   - **Pre-built binary upstream (zip/tarball, no compile):** start from `templates/rules-prebuilt.mk`. See the pre-built section below for the full pattern.
   - Common source-build overrides:
     - Source build root is not the package root → `override_dh_auto_build: dh_auto_build -- -C <subdir>`
     - Tests must be skipped → `override_dh_auto_test:` (empty body)
     - Custom install path → `override_dh_auto_install: make install DESTDIR=$(CURDIR)/debian/<NAME> prefix=/usr`
   - **Do NOT** add manual `strip` calls — `dh_strip` runs automatically.
   - **Do NOT** disable `dh_strip` unless the user explicitly wants debug symbols shipped.

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

   For GitHub with standard `v`-prefixed tags: `https://github.com/<owner>/<repo>/tags .*archive/refs/tags/v?@ANY_VERSION@\.tar\.gz`.

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
dpkg-buildpackage -us -uc -b
# -us  unsigned source
# -uc  unsigned changes
# -b   binary-only (skip source-package generation locally; CI does -S separately)
```

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

## Verification checklist

Before reporting the skill output as done:

- [ ] Step 1 (universe check) ran and didn't find a duplicate; OR it did find one and you stopped + told the user.
- [ ] Step 2 (vendoring): sha256 pinned, tarball reproducible across two fetches.
- [ ] Step 3 (`debian/` tree): `debian/control` has the right Maintainer; `debian/copyright` is DEP-5; `debian/rules` is minimal `dh $@` with at most a couple of overrides; `debian/source/format` = `3.0 (quilt)`; `debian/watch` populated; every binary in `/usr/bin/` has a `debian/man/<binary>.1` listed in `debian/<pkg>.manpages`.
- [ ] Step 4: `file usr/bin/<binary>` reports "stripped"; `dpkg-deb -I` shows resolved `${shlibs:Depends}` with version constraints; **`lintian` returns clean — zero E: lines AND zero W: lines** (the only line allowed is the root-privileges advisory). If a warning is irreducible, it's recorded in `debian/<pkg>.lintian-overrides` with a one-line justification.
- [ ] Step 5: foundry-apt build-all.sh still works end-to-end with the new layout.
- [ ] Step 6: live `apt install <name>` works in a fresh container.

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
