#!/usr/bin/env bash
#
# scripts/secrets-bootstrap.sh
#
# One-time: read local .env and write each known key to AWS SSM:
#
#     CLOUDFLARE_API_TOKEN  → /<SLUG>/cloudflare/api_token  (SecureString)
#     CLOUDFLARE_ACCOUNT_ID → /<SLUG>/cloudflare/account_id (String)
#
# Idempotent: --no-overwrite preserves existing SSM values. Use
# `aws ssm put-parameter --overwrite ...` directly to rotate.
#
# Usage:
#     scripts/secrets-bootstrap.sh                  # bootstrap from .env
#     scripts/secrets-bootstrap.sh --dry-run        # show what would put
#     scripts/secrets-bootstrap.sh -h | --help      # this help

set -euo pipefail

PROFILE="${<SLUG_UPPER>_AWS_PROFILE:-<SLUG>-terraform}"
REGION="${<SLUG_UPPER>_AWS_REGION:-<REGION>}"
ENV_FILE="${<SLUG_UPPER>_ENV_FILE:-.env}"
DRY_RUN=0

case "${1:-}" in
  -h|--help) sed -n '3,/^$/p' "$0" | sed 's|^# \{0,1\}||'; exit 0 ;;
  --dry-run) DRY_RUN=1 ;;
  '') ;;
  *) echo "unknown arg: $1" >&2; exit 2 ;;
esac

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERR: $ENV_FILE not found." >&2
  exit 1
fi

if ! aws sts get-caller-identity --profile "$PROFILE" --region "$REGION" \
    >/dev/null 2>&1; then
  echo "ERR: aws creds for profile '$PROFILE' don't work." >&2
  exit 1
fi

# Read CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID from .env. Strip
# surrounding quotes if present. Other env keys are ignored.
TOKEN=$(grep -E '^CLOUDFLARE_API_TOKEN=' "$ENV_FILE" \
        | head -1 | cut -d= -f2- | sed 's/^["'\'']//;s/["'\'']$//' || true)
ACCOUNT=$(grep -E '^CLOUDFLARE_ACCOUNT_ID=' "$ENV_FILE" \
          | head -1 | cut -d= -f2- | sed 's/^["'\'']//;s/["'\'']$//' || true)

if [[ -z "$TOKEN" && -z "$ACCOUNT" ]]; then
  echo "ERR: neither CLOUDFLARE_API_TOKEN nor CLOUDFLARE_ACCOUNT_ID in $ENV_FILE." >&2
  exit 1
fi

put_one() {
  local name="$1" value="$2" type="$3"
  if [[ -z "$value" ]]; then
    printf "  - skip %s (empty)\n" "$name"
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf "  ? %s\n" "$name"
    return 0
  fi
  if aws ssm put-parameter \
        --profile "$PROFILE" --region "$REGION" \
        --name "$name" --type "$type" --value "$value" --no-overwrite \
        >/dev/null 2>/tmp/secrets-bootstrap.err; then
    printf "  + %s\n" "$name"
  else
    if grep -q ParameterAlreadyExists /tmp/secrets-bootstrap.err 2>/dev/null; then
      printf "  = %s (kept existing — use --overwrite to rotate)\n" "$name"
    else
      cat /tmp/secrets-bootstrap.err >&2
      rm -f /tmp/secrets-bootstrap.err
      exit 1
    fi
  fi
  rm -f /tmp/secrets-bootstrap.err
}

echo "Bootstrapping SSM from $ENV_FILE (profile=$PROFILE region=$REGION)"
[[ $DRY_RUN -eq 1 ]] && echo "  (dry-run — no puts)"
put_one /<SLUG>/cloudflare/api_token  "$TOKEN"   SecureString
put_one /<SLUG>/cloudflare/account_id "$ACCOUNT" String

if [[ $DRY_RUN -eq 0 ]]; then
  echo "Done."
fi
