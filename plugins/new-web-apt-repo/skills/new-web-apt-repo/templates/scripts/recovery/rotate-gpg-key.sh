#!/usr/bin/env bash
# Rotate the GPG signing key for {{CUSTOM_DOMAIN}}.
#
# Generates a new RSA-4096 key with 2-year expiry, uploads the public key
# to r2://{{R2_BUCKET}}/key.gpg (Cloudflare-cached; users see it on
# next `apt-get update`), sets the GPG_PRIVATE_KEY GH secret + R2 backup,
# and patches {{APT_SUBDIR}}/gen/config.py with the new KEY_ID + FINGERPRINT.
#
# After this: commit {{APT_SUBDIR}}/gen/config.py, then run `task apt:bump` to
# tag + push and have CI re-sign the Release file with the new key.
#
# Note: this script aborts if a secret key for {{KEY_EMAIL}}
# is already in the local keyring. To rotate, first remove the old key:
#     gpg --delete-secret-keys {{KEY_EMAIL}}
#     gpg --delete-keys        {{KEY_EMAIL}}
# (The old GH secret remains valid for in-flight CI runs until you push
# a new tag, so there is no window where signing breaks.)
#
# Task: apt:rotate-gpg-key

set -eo pipefail

CACHE={{BOOTSTRAP_CACHE}}
REPO={{GH_REPO}}
APT_BUCKET={{R2_BUCKET}}
SECRETS_BUCKET={{SECRETS_BUCKET}}
KEY_NAME="{{KEY_NAME}}"
KEY_EMAIL={{KEY_EMAIL}}
KEY_BITS=4096
KEY_EXPIRY=2y

REPO_ROOT="$(git rev-parse --show-toplevel)"
CONFIG_PY="$REPO_ROOT/{{APT_SUBDIR}}/gen/config.py"

if [[ ! -f "$CACHE" ]]; then
    echo "ERROR: $CACHE not found — run 'task apt:cache-cf-token' first" >&2
    exit 1
fi
source "$CACHE"
ACCOUNT_ID=$(awk -F= '/^CLOUDFLARE_ACCOUNT_ID=/{print $2}' "$REPO_ROOT/.env" | tr -d '"' | tr -d "'")

if gpg --list-secret-keys "$KEY_EMAIL" &>/dev/null; then
    echo "ERROR: a secret key for $KEY_EMAIL is already in the keyring." >&2
    echo "       Delete it first (see comment at top of this script)." >&2
    exit 1
fi

BATCH=$(mktemp /tmp/gpg-batch-XXXXXX)
PUB=/tmp/new-key-pub.gpg
PRIV=/tmp/new-key-priv.gpg
cleanup() {
    rm -f "$BATCH" "$PUB"
    [[ -f "$PRIV" ]] && shred -u "$PRIV" 2>/dev/null
    rm -f "$PRIV"
}
trap cleanup EXIT

cat > "$BATCH" <<EOF
%no-protection
Key-Type: RSA
Key-Usage: sign
Key-Length: ${KEY_BITS}
Name-Real: ${KEY_NAME}
Name-Email: ${KEY_EMAIL}
Expire-Date: ${KEY_EXPIRY}
EOF

echo "Generating new ${KEY_BITS}-bit RSA key for ${KEY_EMAIL} (expiry ${KEY_EXPIRY})..."
gpg --batch --gen-key "$BATCH"

KEY_ID=$(gpg --list-keys --with-colons "$KEY_EMAIL" | awk -F: '/^pub/{print $5}' | head -1)
FP=$(gpg --list-keys --with-colons "$KEY_EMAIL" | awk -F: '/^fpr/{print $10}' | head -1)
echo "  key id:      0x${KEY_ID}"
echo "  fingerprint: ${FP}"

gpg --armor --export             "$KEY_EMAIL" > "$PUB"
gpg --armor --export-secret-keys "$KEY_EMAIL" > "$PRIV"

echo
echo "Uploading public key to r2://${APT_BUCKET}/key.gpg..."
curl -fsSL -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${APT_BUCKET}/objects/key.gpg" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @"$PUB" >/dev/null

echo "Setting GPG_PRIVATE_KEY GH secret + R2 backup..."
gh secret set GPG_PRIVATE_KEY --repo "$REPO" --body "$(cat "$PRIV")"
curl -fsSL -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/GPG_PRIVATE_KEY" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: text/plain; charset=utf-8" \
  --data-binary @"$PRIV" >/dev/null

echo "Patching ${CONFIG_PY} with new KEY_ID + FINGERPRINT..."
sed -i "s|^KEY_ID *=.*|KEY_ID          = \"0x${KEY_ID}\"|" "$CONFIG_PY"
sed -i "s|^FINGERPRINT *=.*|FINGERPRINT     = \"${FP}\"|" "$CONFIG_PY"

echo
echo "Done. Next:"
echo "  git add {{APT_SUBDIR}}/gen/config.py"
echo "  git commit -m \"feat(apt): rotate GPG signing key (id 0x${KEY_ID})\""
echo "  task apt:bump   # tag + push → CI signs Release with the new key"
