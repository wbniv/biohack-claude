#!/usr/bin/env bash
# Import the signing key from the GPG_PRIVATE_KEY env var, sign the
# published Release file, then wipe the temp GPG home.
#
# Used by CI only; locally you'd use your own key.
#
# Env:
#   GPG_PRIVATE_KEY   — armored private key (from GitHub Actions secret)
#   PUBLISH_DIR       (default ./public/dists/{{SUITE}})

set -euo pipefail

PUBLISH_DIR="${PUBLISH_DIR:-./public/dists/{{SUITE}}}"

if [[ ! -f "$PUBLISH_DIR/Release" ]]; then
    echo "ERROR: $PUBLISH_DIR/Release not found. Did you run publish-local.sh?" >&2
    exit 1
fi

: "${GPG_PRIVATE_KEY:?GPG_PRIVATE_KEY is required}"

tmp_gnupg=$(mktemp -d)
trap 'rm -rf "$tmp_gnupg"' EXIT
export GNUPGHOME="$tmp_gnupg"
chmod 700 "$GNUPGHOME"

echo "Importing signing key..."
echo "${GPG_PRIVATE_KEY}" | gpg --batch --import

key_id=$(gpg --list-secret-keys --with-colons | awk -F: '/^sec/ {print $5; exit}')
if [[ -z "$key_id" ]]; then
    echo "ERROR: imported key but couldn't find key ID" >&2
    exit 1
fi

echo "Signing Release with key $key_id..."
gpg --batch --yes --default-key "$key_id" \
    --detach-sign --armor \
    -o "$PUBLISH_DIR/Release.gpg" \
    "$PUBLISH_DIR/Release"

gpg --batch --yes --default-key "$key_id" \
    --clearsign \
    -o "$PUBLISH_DIR/InRelease" \
    "$PUBLISH_DIR/Release"

echo "Signed: $PUBLISH_DIR/{Release.gpg,InRelease}"
