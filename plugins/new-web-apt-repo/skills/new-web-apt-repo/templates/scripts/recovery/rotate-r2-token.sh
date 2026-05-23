#!/usr/bin/env bash
# Rotate the R2 S3 CI credentials.
#
# Workflow: first create or roll the `{{R2_TOKEN_NAME}}` token at the
# Cloudflare dashboard (https://dash.cloudflare.com/?to=/:account/r2/api-tokens).
# Make sure it's "Object Read & Write" on bucket {{R2_BUCKET}} — not
# just Read, or CI publish will fail at the rclone step.
#
# Cloudflare only shows the Access Key + Secret on the result screen,
# once. Have them in hand before running this. Then this script:
#   - Prompts for AK + SK (input hidden)
#   - Sets both as GH Actions secrets on {{GH_REPO}}
#   - Refreshes the backup in r2://{{SECRETS_BUCKET}}/
#
# Task: apt:rotate-r2-token

set -eo pipefail

CACHE={{BOOTSTRAP_CACHE}}
REPO={{GH_REPO}}
SECRETS_BUCKET={{SECRETS_BUCKET}}

REPO_ROOT="$(git rev-parse --show-toplevel)"

if [[ ! -f "$CACHE" ]]; then
    echo "ERROR: $CACHE not found — run 'task apt:cache-cf-token' first" >&2
    exit 1
fi
source "$CACHE"

ACCOUNT_ID=$(awk -F= '/^CLOUDFLARE_ACCOUNT_ID=/{print $2}' "$REPO_ROOT/.env" | tr -d '"' | tr -d "'")

read -rsp "New R2 Access Key ID:     " AK; echo
read -rsp "New R2 Secret Access Key: " SK; echo

if [[ -z "$AK" || -z "$SK" ]]; then
    echo "ERROR: AK and SK cannot be blank" >&2
    exit 1
fi

gh secret set R2_ACCESS_KEY_ID     --repo "$REPO" --body "$AK"
gh secret set R2_SECRET_ACCESS_KEY --repo "$REPO" --body "$SK"

for entry in "R2_ACCESS_KEY_ID=$AK" "R2_SECRET_ACCESS_KEY=$SK"; do
    K="${entry%%=*}"
    V="${entry#*=}"
    printf '%s' "$V" | curl -fsSL -X PUT \
      "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/${K}" \
      -H "Authorization: Bearer ${CF_API_TOKEN}" \
      -H "Content-Type: text/plain; charset=utf-8" \
      --data-binary @- >/dev/null
done

unset AK SK
echo
echo "rotated. Verify with: task apt:bump   (tag a new release and watch the workflow)"
