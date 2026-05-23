#!/usr/bin/env bash
# Vendored-upstream Debian package build wrapper.
#
# This script is the entry point that foundry-apt's `build-all.sh` invokes
# (see `foundry-apt/scripts/build-all.sh`). It:
#
#   1. Fetches the upstream source tarball (sha256-verified)
#   2. Extracts to a tmpdir
#   3. Copies our `debian/` tree into the upstream tree
#   4. Runs dpkg-buildpackage -us -uc -b
#   5. Moves the resulting .deb into $REPO_ROOT/dist/
#
# Bump the upstream version: change UPSTREAM_VERSION + SHA256 at the top,
# add a debian/changelog entry via `dch -v <NEW>-1foundry1`. Pin sha256 with:
#   curl -fsSL <UPSTREAM_URL> | sha256sum

set -euo pipefail

# -h / --help short-circuit before any work
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            cat <<EOF
Build <NAME> as a Debian .deb via dpkg-buildpackage.

Usage: build.sh [-h|--help]

Environment overrides:
  <NAME_UPPER>_VERSION  upstream version (default: <UPSTREAM_VERSION>)
  <NAME_UPPER>_SHA256   sha256 of upstream tarball (must match VERSION)

Output: \$REPO_ROOT/dist/<NAME>_<DEB_VERSION>_<arch>.deb
EOF
            exit 0
            ;;
    esac
done

UPSTREAM_VERSION="${<NAME_UPPER>_VERSION:-<UPSTREAM_VERSION>}"
SHA256="${<NAME_UPPER>_SHA256:-<SHA256_PINNED>}"
UPSTREAM_URL="<UPSTREAM_URL_TEMPLATE>"   # e.g. https://github.com/.../archive/refs/tags/v${UPSTREAM_VERSION}.tar.gz

cd "$(dirname "$0")"
PKG_DIR="$(pwd)"
NAME="$(basename "$PKG_DIR")"
REPO_ROOT="$(cd ../.. && pwd)"
mkdir -p "$REPO_ROOT/dist"

# Fail loudly if upstream is unreachable.
if ! curl -fsI -o /dev/null "${UPSTREAM_URL%/*}/"; then
    echo "ERROR: cannot reach upstream — skipping $NAME build" >&2
    exit 1
fi

WORKDIR=$(mktemp -d -t "${NAME}-build-XXXXXX")
# shellcheck disable=SC2064  # expand $WORKDIR now so the trap captures the value
trap "rm -rf '$WORKDIR'" EXIT

echo "=== Fetching $UPSTREAM_URL ==="
ORIG_TARBALL="$WORKDIR/${NAME}_${UPSTREAM_VERSION}.orig.tar.gz"
curl -fsSL -o "$ORIG_TARBALL" "$UPSTREAM_URL"

echo "=== Verifying sha256 ==="
echo "$SHA256  $ORIG_TARBALL" | sha256sum -c -

echo "=== Extracting ==="
tar -xzf "$ORIG_TARBALL" -C "$WORKDIR"
# Find the top-level dir created by the tarball (varies by upstream conventions)
SRC_DIR=$(find "$WORKDIR" -mindepth 1 -maxdepth 1 -type d ! -name "${NAME}_*" -print -quit)
[[ -n "$SRC_DIR" ]] || { echo "ERROR: could not find extracted source dir under $WORKDIR" >&2; exit 1; }

# Normalize the dir name to <name>-<version>/ (dpkg-buildpackage expects this)
EXPECTED="$WORKDIR/${NAME}-${UPSTREAM_VERSION}"
if [[ "$SRC_DIR" != "$EXPECTED" ]]; then
    mv "$SRC_DIR" "$EXPECTED"
    SRC_DIR="$EXPECTED"
fi

echo "=== Copying debian/ tree into source ==="
cp -a "$PKG_DIR/debian" "$SRC_DIR/"

echo "=== Installing Build-Depends ==="
# Install Build-Depends declared in debian/control. Works in both CI (non-root
# with passwordless sudo) and Docker containers (running as root, no sudo needed).
if command -v apt-get >/dev/null; then
    _apt() { [[ $EUID -eq 0 ]] && apt-get "$@" || sudo apt-get "$@"; }
    _apt install -y --no-install-recommends \
        <BUILD_DEPENDS_SPACE_SEPARATED>
fi

echo "=== dpkg-buildpackage -us -uc -b ==="
( cd "$SRC_DIR" && dpkg-buildpackage -us -uc -b )

ARCH=$(dpkg --print-architecture)
# Extract the full Debian version from changelog (e.g. "2083-1foundry1").
# Do NOT reconstruct it from UPSTREAM_VERSION + revision — upstream tag prefixes
# (e.g. "r2083") mean the Debian version may not literally contain the tag string.
DEB_VERSION=$(awk 'NR==1 {match($0, /\(([^)]+)\)/, a); print a[1]}' "$PKG_DIR/debian/changelog")
DEB="$WORKDIR/${NAME}_${DEB_VERSION}_${ARCH}.deb"
[[ -f "$DEB" ]] || { echo "ERROR: expected .deb not found: $DEB" >&2; ls -la "$WORKDIR"; exit 1; }

mv "$DEB" "$REPO_ROOT/dist/"
OUT="$REPO_ROOT/dist/$(basename "$DEB")"
echo "OK   $OUT  ($(stat -c%s "$OUT") bytes)"
