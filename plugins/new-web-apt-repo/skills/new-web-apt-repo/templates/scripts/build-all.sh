#!/usr/bin/env bash
# Build every package under packages/ into dist/.
#
# Two layouts supported:
#
#   1. Canonical Debian source-package layout (preferred):
#        packages/<name>/debian/{control,changelog,rules,source/format,copyright}
#      Built with dpkg-buildpackage from a tmp-staged copy of debian/.
#      Used by every metapackage (3.0 native) and by /package-skill-built
#      vendored upstreams (3.0 quilt).
#
#   2. Vendored upstream with a build.sh wrapper:
#        packages/<name>/{build.sh, debian/...}
#      build.sh is responsible for fetching the upstream tarball
#      (sha256-pinned), extracting it, overlaying debian/, running
#      dpkg-buildpackage, and moving the .deb into dist/. /package generates
#      this layout for vendored upstreams (f9dasm, future libvgm/vgmstream).

set -euo pipefail
cd "$(dirname "$0")/.."

REPO_ROOT="$(pwd)"
mkdir -p dist
rm -f dist/*.deb

build_canonical() {
    local pkgdir="$1" name="$2"
    local ver builddir deb

    if ! command -v dpkg-buildpackage >/dev/null; then
        echo "FAIL $name (dpkg-buildpackage not installed — apt install dpkg-dev debhelper)" >&2
        return 1
    fi

    ver=$(dpkg-parsechangelog -l "$pkgdir/debian/changelog" -SVersion)
    if [[ -z "$ver" ]]; then
        echo "FAIL $name (could not parse version from debian/changelog)" >&2
        return 1
    fi

    builddir=$(mktemp -d -t "${name}-build-XXXXXX")
    # shellcheck disable=SC2064  # expand $builddir now so trap captures the value
    trap "rm -rf '$builddir'" RETURN

    mkdir -p "${builddir}/${name}-${ver}"
    cp -a "${pkgdir}/debian" "${builddir}/${name}-${ver}/"

    if ! ( cd "${builddir}/${name}-${ver}" && dpkg-buildpackage -us -uc -b -d --no-sign ) >/dev/null 2>&1; then
        echo "FAIL $name (dpkg-buildpackage exited non-zero)" >&2
        ( cd "${builddir}/${name}-${ver}" && dpkg-buildpackage -us -uc -b -d --no-sign 2>&1 | tail -10 ) >&2
        return 1
    fi

    # The .deb may be amd64-arch'd or all-arch'd depending on debian/control
    for deb in "${builddir}/${name}_${ver}_"*.deb; do
        [[ -f "$deb" ]] || continue
        mv "$deb" "${REPO_ROOT}/dist/"
        echo "OK   dist/$(basename "$deb")  ($(stat -c%s "${REPO_ROOT}/dist/$(basename "$deb")") bytes)"
    done
}

fail=0
for pkgdir in packages/*/; do
    name=$(basename "$pkgdir")

    if [[ -x "$pkgdir/build.sh" ]]; then
        echo "=== Running $name/build.sh (legacy build.sh wrapper) ==="
        if ! bash "$pkgdir/build.sh"; then
            echo "FAIL $name (build.sh exited non-zero)" >&2
            fail=1
        fi
        continue
    fi

    if [[ -f "$pkgdir/debian/control" && -f "$pkgdir/debian/changelog" ]]; then
        echo "=== Building $name (canonical debian/ source format) ==="
        if ! build_canonical "$pkgdir" "$name"; then
            fail=1
        fi
        continue
    fi

    echo "SKIP $name (no debian/control and no build.sh)"
done

if (( fail )); then
    echo "ERROR: one or more builds failed" >&2
    exit 1
fi

echo
echo "=== dist/ ==="
ls -lh dist/
