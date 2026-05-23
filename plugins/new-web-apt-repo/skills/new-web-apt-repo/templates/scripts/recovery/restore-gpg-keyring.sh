#!/usr/bin/env bash
# Restore the GPG signing key into the local gpg keyring from R2 backup.
#
# Use when you need to sign locally (e.g. `task apt:publish-local` with
# GPG_KEY set) on a fresh machine. CI doesn't need this — it imports the
# key from the GPG_PRIVATE_KEY env var into an ephemeral keyring.
#
# Requires: {{BOOTSTRAP_CACHE}} with CF_API_TOKEN cached.
#
# Task: apt:restore-gpg-keyring

set -eo pipefail

CACHE={{BOOTSTRAP_CACHE}}
SECRETS_BUCKET={{SECRETS_BUCKET}}
KEY_EMAIL={{KEY_EMAIL}}

REPO_ROOT="$(git rev-parse --show-toplevel)"

if [[ ! -f "$CACHE" ]]; then
    echo "ERROR: $CACHE not found — run 'task apt:cache-cf-token' first" >&2
    exit 1
fi
source "$CACHE"

ACCOUNT_ID=$(awk -F= '/^CLOUDFLARE_ACCOUNT_ID=/{print $2}' "$REPO_ROOT/.env" | tr -d '"' | tr -d "'")

if gpg --list-secret-keys "$KEY_EMAIL" &>/dev/null; then
    echo "Secret key for $KEY_EMAIL is already in the keyring:"
    gpg --list-secret-keys "$KEY_EMAIL"
    exit 0
fi

curl -fsSL \
    "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/GPG_PRIVATE_KEY" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
  | gpg --batch --import

echo
gpg --list-secret-keys "$KEY_EMAIL"
