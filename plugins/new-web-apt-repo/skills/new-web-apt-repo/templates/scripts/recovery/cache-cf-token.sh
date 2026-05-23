#!/usr/bin/env bash
# Cache a freshly-minted CF operator token at {{BOOTSTRAP_CACHE}}
# and overwrite the backup at r2://{{SECRETS_BUCKET}}/CF_API_TOKEN.
#
# Use this on a fresh machine, after creating a new `{{CF_OPERATOR_TOKEN_NAME}}`
# token at https://dash.cloudflare.com/profile/api-tokens (see SKILL.md
# Step 3 for the three permissions required: Account → Workers R2 Storage
# Edit, Zone → DNS Edit, Zone → Transform Rules Edit, scoped to
# {{CF_ZONE_NAME}}).
#
# The operator token is the chicken-egg credential: it's the only thing
# that can read the secrets bucket, but it's also IN the secrets bucket.
# A fresh machine must mint a new operator token from the dashboard
# rather than trying to read the backup.
#
# Task: apt:cache-cf-token

set -eo pipefail

CACHE={{BOOTSTRAP_CACHE}}
SECRETS_BUCKET={{SECRETS_BUCKET}}

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Strip any existing CF_API_TOKEN line before appending the new one
if [[ -f "$CACHE" ]]; then
    grep -v '^CF_API_TOKEN=' "$CACHE" > "${CACHE}.tmp" || true
    mv "${CACHE}.tmp" "$CACHE"
fi

read -rsp "CF operator token: " T; echo
if [[ -z "$T" ]]; then
    echo "ERROR: token cannot be blank" >&2
    exit 1
fi

printf 'CF_API_TOKEN=%s\n' "$T" >> "$CACHE"
chmod 600 "$CACHE"

ACCOUNT_ID=$(awk -F= '/^CLOUDFLARE_ACCOUNT_ID=/{print $2}' "$REPO_ROOT/.env" | tr -d '"' | tr -d "'")

# Overwrite the R2 backup so future scripts can reach it (the operator
# token can read its own backup, but on a fresh machine you can't
# bootstrap until you have the token in hand).
printf '%s' "$T" | curl -fsSL -X PUT \
    "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/CF_API_TOKEN" \
    -H "Authorization: Bearer ${T}" \
    -H "Content-Type: text/plain; charset=utf-8" \
    --data-binary @- >/dev/null

unset T
echo "cached at $CACHE (mode 600) and backed up to r2://${SECRETS_BUCKET}/CF_API_TOKEN"
