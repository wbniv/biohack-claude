#!/usr/bin/env bash
# Restore GitHub Actions secrets from r2://{{SECRETS_BUCKET}}/ backup.
#
# Pulls R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, and
# GPG_PRIVATE_KEY out of the private secrets bucket and re-sets them as
# Actions secrets on {{GH_REPO}}.
#
# Recovers from: GH secrets accidentally deleted, GH org migration, or
# audit-rotation that needs the previously-stored values.
#
# Requires: {{BOOTSTRAP_CACHE}} with CF_API_TOKEN cached
# (run apt:cache-cf-token first if you don't have it).
#
# Task: apt:restore-gh-secrets

set -eo pipefail

CACHE={{BOOTSTRAP_CACHE}}
REPO={{GH_REPO}}
SECRETS_BUCKET={{SECRETS_BUCKET}}
KEYS=(R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_ENDPOINT GPG_PRIVATE_KEY)

REPO_ROOT="$(git rev-parse --show-toplevel)"

if [[ ! -f "$CACHE" ]]; then
    echo "ERROR: $CACHE not found — run 'task apt:cache-cf-token' first" >&2
    exit 1
fi
source "$CACHE"

ACCOUNT_ID=$(awk -F= '/^CLOUDFLARE_ACCOUNT_ID=/{print $2}' "$REPO_ROOT/.env" | tr -d '"' | tr -d "'")
if [[ -z "$ACCOUNT_ID" ]]; then
    echo "ERROR: CLOUDFLARE_ACCOUNT_ID not found in $REPO_ROOT/.env" >&2
    exit 1
fi

for K in "${KEYS[@]}"; do
    VAL=$(curl -fsSL \
        "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/${K}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" 2>/dev/null) || {
        echo "ERROR: failed to read $K from r2://${SECRETS_BUCKET}/" >&2
        exit 1
    }
    if [[ -z "$VAL" ]]; then
        echo "ERROR: $K is empty in R2 backup" >&2
        exit 1
    fi
    gh secret set "$K" --repo "$REPO" --body "$VAL"
done

echo
echo "Done. Current secrets:"
gh secret list --repo "$REPO" | grep -E 'GPG_PRIVATE_KEY|R2_'
