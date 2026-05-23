#!/usr/bin/env bash
# Bootstrap a new web-hosted signed APT repo on Cloudflare R2.
# Steps 1b–9: GPG key, GitHub repo, R2 bucket, DNS, public key upload.
#
# Usage:
#   bash scripts/bootstrap-apt.sh [--dry-run] [-h]
#
# After this script: push the first release tag to trigger the publish workflow.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── config ───────────────────────────────────────────────────────────────────

GH_ORG="{{GH_ORG}}"
PKG_NAME="{{PKG_NAME}}"
# {{GH_REPO}} defaults to ${GH_ORG}/${PKG_NAME} (dedicated layout); for a
# monorepo it should be the *parent* repo (e.g. wbniv/worldfoundry.org when
# apt content lives in worldfoundry.org/apt/). Skill instantiation sets this.
GH_REPO="{{GH_REPO}}"
SRC_DIR="${REPO_ROOT}/{{APT_SUBDIR}}"
REPO_DESC="{{REPO_DESC}}"

KEY_NAME="{{KEY_NAME}}"
KEY_EMAIL="{{KEY_EMAIL}}"
KEY_BITS=4096
KEY_EXPIRY="2y"
PUB_KEY="/tmp/{{REPO_NAME}}-packages.pub.gpg"
SEC_KEY="/tmp/{{REPO_NAME}}-packages.sec.gpg"

R2_BUCKET="{{R2_BUCKET}}"
SECRETS_BUCKET="{{SECRETS_BUCKET}}"
R2_TOKEN_NAME="{{R2_TOKEN_NAME}}"
BOOTSTRAP_CACHE="{{BOOTSTRAP_CACHE}}"
CUSTOM_DOMAIN="{{CUSTOM_DOMAIN}}"
DNS_CNAME="{{DNS_CNAME}}"
CF_OPERATOR_TOKEN_NAME="{{CF_OPERATOR_TOKEN_NAME}}"
CF_ZONE_NAME="{{CF_ZONE_NAME}}"

DRY_RUN=false

WORK_DIR=""
BATCH_FILE=""

# ── helpers ──────────────────────────────────────────────────────────────────

info() { echo "  [info]  $*"; }
ok()   { echo "  [ok]    $*"; }
warn() { echo "  [warn]  $*" >&2; }
err()  { echo "  [error] $*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
    sed -n '2,8p' "$0" | sed 's/^# //'
    exit 0
}

cleanup() {
    [[ -n "${WORK_DIR}"   && -d "${WORK_DIR}"   ]] && rm -rf "${WORK_DIR}"   || true
    [[ -n "${BATCH_FILE}" && -f "${BATCH_FILE}" ]] && rm -f  "${BATCH_FILE}" || true
}
trap cleanup EXIT

cache_set() {
    local key="$1" val="$2"
    { grep -v "^${key}=" "$BOOTSTRAP_CACHE" 2>/dev/null || true
      printf '%s=%q\n' "$key" "$val"
    } > "${BOOTSTRAP_CACHE}.tmp" && mv "${BOOTSTRAP_CACHE}.tmp" "$BOOTSTRAP_CACHE"
    chmod 600 "$BOOTSTRAP_CACHE"
}

cf_api() {
    local method="$1" path="$2"
    shift 2
    curl -fsSL -X "$method" \
        "https://api.cloudflare.com/client/v4${path}" \
        -H "Authorization: Bearer ${CF_API_TOKEN:-}" \
        -H "Content-Type: application/json" \
        "$@"
}

r2_put_secret() {
    local name="$1" value="$2"
    if $DRY_RUN; then
        echo "  [dry-run] PUT r2://${SECRETS_BUCKET}/${name}"
        return
    fi
    printf '%s' "${value}" | curl -fsSL -X PUT \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets/${SECRETS_BUCKET}/objects/${name}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: text/plain; charset=utf-8" \
        --data-binary @- \
        >/dev/null
}

# ── arg parse ────────────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        -h|--help)  usage ;;
        --dry-run)  DRY_RUN=true ;;
        *)          die "Unknown argument: $arg" ;;
    esac
done

# ── preflight ────────────────────────────────────────────────────────────────

if [[ -f "$BOOTSTRAP_CACHE" ]]; then
    # shellcheck source=/dev/null
    source "$BOOTSTRAP_CACHE"
    info "Loaded cached credentials from $BOOTSTRAP_CACHE"
fi

[[ -d "${SRC_DIR}" ]] || die "$(basename "${SRC_DIR}")/ not found under ${REPO_ROOT}"

command -v gpg   &>/dev/null || die "gpg not found — install gnupg2"
command -v shred &>/dev/null || die "shred not found (install util-linux)"
command -v curl  &>/dev/null || die "curl not found"
command -v jq    &>/dev/null || die "jq not found"
command -v gh    &>/dev/null || die "gh CLI not found — https://cli.github.com"

if ! $DRY_RUN; then
    gh auth status &>/dev/null || die "gh not authenticated — run: gh auth login"
    if [[ -z "${CF_API_TOKEN:-}" ]]; then
        echo "  Cloudflare operator token needed. Create '${CF_OPERATOR_TOKEN_NAME}' first:"
        echo ""
        echo "  https://dash.cloudflare.com/profile/api-tokens"
        echo "  Click '+ Create Token', then 'Get started' next to 'Create Custom Token'"
        echo "  Name: ${CF_OPERATOR_TOKEN_NAME}"
        echo "  Permissions:"
        echo "    Account | Workers R2 Storage | Edit"
        echo "    Zone    | DNS                | Edit  (Specific zone: ${CF_ZONE_NAME})"
        echo "    Zone    | Transform Rules    | Edit  (Specific zone: ${CF_ZONE_NAME})"
        echo "  Account Resources: Include → select your account"
        echo "  Zone Resources:    Include → Specific zone → ${CF_ZONE_NAME}"
        echo ""
        until [[ -n "${CF_API_TOKEN:-}" ]]; do
            read -rsp "  Paste token value (input hidden): " CF_API_TOKEN; echo
            [[ -z "${CF_API_TOKEN:-}" ]] && echo "  (token cannot be blank — try again)"
        done
        export CF_API_TOKEN
        cache_set CF_API_TOKEN "$CF_API_TOKEN"
    fi
fi

R2_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-}"
R2_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-}"
R2_DEV_HOSTNAME=""

echo ""
info "Bootstrap: Steps 0.5–9 for ${GH_REPO}"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# Step 0.5 — Palette distillation (non-fatal)
# Extracts CSS custom property tokens from the parent site and applies them
# to gen/src.css and gen/static/styles.css before the initial GitHub push.
# Falls back to greyscale defaults silently if no parent CSS is found.
# ════════════════════════════════════════════════════════════════════════════

DISTILL="${SRC_DIR}/gen/distill-palette.sh"
if [[ -f "${DISTILL}" ]]; then
    PARENT_DOMAIN="${CUSTOM_DOMAIN#*.}"  # strip subdomain: apt.foo.com → foo.com
    echo ""
    bash "${DISTILL}" "${PARENT_DOMAIN}" || warn "[0.5] Palette distillation failed — greyscale defaults kept"
    echo ""
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 1b — Resolve CF_ACCOUNT_ID and CF_ZONE_ID
# ════════════════════════════════════════════════════════════════════════════

if $DRY_RUN; then
    CF_API_TOKEN="${CF_API_TOKEN:-DRY_RUN_TOKEN}"
    CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-DRY_RUN_ACCOUNT_ID}"
    CF_ZONE_ID="${CF_ZONE_ID:-DRY_RUN_ZONE_ID}"
    echo "  [dry-run] GET /accounts → CF_ACCOUNT_ID"
    echo "  [dry-run] GET /zones?name=${CF_ZONE_NAME} → CF_ZONE_ID"
else
    if [[ -z "${CF_ACCOUNT_ID:-}" ]]; then
        CF_ACCOUNT_ID=$(cf_api GET "/accounts?per_page=1" | jq -r '.result[0].id')
        [[ -n "${CF_ACCOUNT_ID}" && "${CF_ACCOUNT_ID}" != "null" ]] \
            || die "[1b] Could not retrieve account ID — check CF_API_TOKEN permissions"
        ok "[1b] Account ID: ${CF_ACCOUNT_ID}"
        export CF_ACCOUNT_ID
    else
        ok "[1b] CF_ACCOUNT_ID already set: ${CF_ACCOUNT_ID}"
    fi

    if [[ -z "${CF_ZONE_ID:-}" ]]; then
        CF_ZONE_ID=$(cf_api GET "/zones?name=${CF_ZONE_NAME}" | jq -r '.result[0].id')
        [[ -n "${CF_ZONE_ID}" && "${CF_ZONE_ID}" != "null" ]] \
            || die "[1b] Zone ${CF_ZONE_NAME} not found — check CF_API_TOKEN has DNS:Edit for this zone"
        ok "[1b] Zone ID: ${CF_ZONE_ID}"
        export CF_ZONE_ID
    else
        ok "[1b] CF_ZONE_ID already set: ${CF_ZONE_ID}"
    fi

    info "[1b] Validating token permissions..."
    PERM_ERRORS=()
    cf_api GET "/accounts/${CF_ACCOUNT_ID}/r2/buckets?per_page=1" &>/dev/null \
        || PERM_ERRORS+=("  Account | Workers R2 Storage | Edit")
    cf_api GET "/zones/${CF_ZONE_ID}/dns_records?per_page=1" &>/dev/null \
        || PERM_ERRORS+=("  Zone    | DNS                | Edit  (zone: ${CF_ZONE_NAME})")
    cf_api GET "/zones/${CF_ZONE_ID}/rulesets" &>/dev/null \
        || PERM_ERRORS+=("  Zone    | Transform Rules    | Edit  (zone: ${CF_ZONE_NAME})")
    if [[ ${#PERM_ERRORS[@]} -gt 0 ]]; then
        err "[1b] Token is missing required permissions:"
        for e in "${PERM_ERRORS[@]}"; do err "$e"; done
        err ""
        err "  Edit your token at: https://dash.cloudflare.com/profile/api-tokens"
        die "[1b] Fix token permissions and re-run."
    fi
    ok "[1b] Token permissions verified"
fi

R2_ENDPOINT="https://${CF_ACCOUNT_ID:-DRY_RUN}.r2.cloudflarestorage.com"

# ════════════════════════════════════════════════════════════════════════════
# Step 1c — Create private secrets bucket and store operator token
# ════════════════════════════════════════════════════════════════════════════

info "[1c] Ensuring private secrets bucket '${SECRETS_BUCKET}' exists"
if $DRY_RUN; then
    echo "  [dry-run] POST /r2/buckets {name: ${SECRETS_BUCKET}}"
    echo "  [dry-run] PUT r2://${SECRETS_BUCKET}/CF_API_TOKEN"
else
    SEC_BUCKET_RESP=$(curl -sS -X POST \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg n "$SECRETS_BUCKET" '{name:$n,locationHint:"auto"}')")
    if echo "${SEC_BUCKET_RESP}" | jq -e '.success == true' &>/dev/null; then
        ok "[1c] Secrets bucket '${SECRETS_BUCKET}' created (no public access)"
    elif echo "${SEC_BUCKET_RESP}" | jq -r '.errors[].code' 2>/dev/null | grep -qE "10004|10006"; then
        ok "[1c] Secrets bucket '${SECRETS_BUCKET}' already exists"
    else
        die "[1c] Unexpected bucket response: $(echo "${SEC_BUCKET_RESP}" | jq -c '.errors')"
    fi
    r2_put_secret "CF_API_TOKEN" "${CF_API_TOKEN}"
    ok "[1c] CF_API_TOKEN stored in r2://${SECRETS_BUCKET}/CF_API_TOKEN"
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 2b — Push to standalone GitHub repo
# ════════════════════════════════════════════════════════════════════════════

if ! $DRY_RUN && gh repo view "${GH_REPO}" &>/dev/null; then
    ok "[2b] ${GH_REPO} already exists on GitHub"
else
    info "[2b] Creating https://github.com/${GH_REPO}"
    WORK_DIR="/tmp/${PKG_NAME}-push"
    if $DRY_RUN; then
        echo "  [dry-run] cp -r ${SRC_DIR} ${WORK_DIR}"
        echo "  [dry-run] git init && git add . && git commit -m 'feat: initial ${PKG_NAME} import'"
        echo "  [dry-run] gh repo create ${GH_REPO} --public --source=. --push"
    else
        rm -rf "${WORK_DIR}"
        cp -r "${SRC_DIR}" "${WORK_DIR}"
        git -C "${WORK_DIR}" init -q
        git -C "${WORK_DIR}" add .
        git -C "${WORK_DIR}" commit -q -m "feat: initial ${PKG_NAME} import"
        gh repo create "${GH_REPO}" \
            --public \
            --description "${REPO_DESC}" \
            --source="${WORK_DIR}" --remote=origin --push
        ok "[2b] Repo created: https://github.com/${GH_REPO}"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 3 — Generate GPG signing key
# ════════════════════════════════════════════════════════════════════════════

if gpg --list-keys "${KEY_EMAIL}" &>/dev/null; then
    ok "[3] GPG key for ${KEY_EMAIL} already in keyring"
else
    info "[3] Generating ${KEY_BITS}-bit RSA signing key (${KEY_EMAIL}, expiry: ${KEY_EXPIRY})"
    BATCH_FILE="$(mktemp /tmp/gpg-batch-XXXXXX)"
    cat > "${BATCH_FILE}" <<EOF
%no-protection
Key-Type: RSA
Key-Usage: sign
Key-Length: ${KEY_BITS}
Name-Real: ${KEY_NAME}
Name-Email: ${KEY_EMAIL}
Expire-Date: ${KEY_EXPIRY}
%commit
EOF
    if $DRY_RUN; then
        echo "  [dry-run] gpg --batch --gen-key <batch-file>"
    else
        gpg --batch --gen-key "${BATCH_FILE}"
        ok "[3] GPG key generated"
    fi
fi

if $DRY_RUN; then
    echo "  [dry-run] gpg --armor --export ${KEY_EMAIL} > ${PUB_KEY}"
    echo "  [dry-run] gpg --armor --export-secret-keys ${KEY_EMAIL} > ${SEC_KEY}"
else
    gpg --armor --export "${KEY_EMAIL}" > "${PUB_KEY}"
    gpg --armor --export-secret-keys "${KEY_EMAIL}" > "${SEC_KEY}"
    chmod 600 "${SEC_KEY}"

    # Patch gen/config.py with the real key ID and fingerprint
    CONFIG_PY="${SRC_DIR}/gen/config.py"
    if [[ -f "${CONFIG_PY}" ]]; then
        KEY_ID=$(gpg --list-keys --with-colons "${KEY_EMAIL}" | awk -F: '/^pub/{print $5}' | head -1 || true)
        FP=$(gpg --fingerprint --with-colons "${KEY_EMAIL}" | awk -F: '/^fpr/{print $10; exit}' || true)
        if [[ -n "${KEY_ID}" ]]; then
            sed -i "s|YOUR_KEY_ID_HERE|0x${KEY_ID}|g" "${CONFIG_PY}"
            info "[3] Patched gen/config.py: KEY_ID = 0x${KEY_ID}"
        fi
        if [[ -n "${FP}" ]]; then
            sed -i "s|YOUR_FINGERPRINT_HERE|${FP}|g" "${CONFIG_PY}"
            info "[3] Patched gen/config.py: FINGERPRINT"
        fi
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 4 — Set GPG_PRIVATE_KEY GitHub secret, shred local private key
# ════════════════════════════════════════════════════════════════════════════

GPG_SECRET_EXISTS=false
if ! $DRY_RUN && gh secret list --repo "${GH_REPO}" 2>/dev/null | grep -q "^GPG_PRIVATE_KEY"; then
    GPG_SECRET_EXISTS=true
fi

if $GPG_SECRET_EXISTS; then
    ok "[4] GPG_PRIVATE_KEY secret already exists on ${GH_REPO}"
    if ! $DRY_RUN && [[ -f "${SEC_KEY}" ]]; then
        r2_put_secret "GPG_PRIVATE_KEY" "$(cat "${SEC_KEY}")"
        ok "[4] GPG_PRIVATE_KEY stored in r2://${SECRETS_BUCKET}/GPG_PRIVATE_KEY"
        shred -u "${SEC_KEY}"
    fi
else
    info "[4] Setting GPG_PRIVATE_KEY secret on ${GH_REPO}"
    if $DRY_RUN; then
        echo "  [dry-run] gh secret set GPG_PRIVATE_KEY --repo ${GH_REPO} --body <private-key>"
        echo "  [dry-run] PUT r2://${SECRETS_BUCKET}/GPG_PRIVATE_KEY"
        echo "  [dry-run] shred -u ${SEC_KEY}"
    else
        gh secret set GPG_PRIVATE_KEY --repo "${GH_REPO}" --body "$(cat "${SEC_KEY}")"
        ok "[4] GPG_PRIVATE_KEY secret set"
        r2_put_secret "GPG_PRIVATE_KEY" "$(cat "${SEC_KEY}")"
        ok "[4] GPG_PRIVATE_KEY stored in r2://${SECRETS_BUCKET}/GPG_PRIVATE_KEY"
        shred -u "${SEC_KEY}"
        ok "[4] Private key shredded"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 6 — Cloudflare R2 bucket + scoped CI token
# ════════════════════════════════════════════════════════════════════════════

if $DRY_RUN; then
    echo "  [dry-run] POST /r2/buckets {name: ${R2_BUCKET}}"
else
    BUCKET_RESPONSE=$(curl -sS -X POST \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg n "$R2_BUCKET" '{name:$n,locationHint:"auto"}')")
    if echo "${BUCKET_RESPONSE}" | jq -e '.success == true' &>/dev/null; then
        ok "[6] R2 bucket '${R2_BUCKET}' created"
    elif echo "${BUCKET_RESPONSE}" | jq -r '.errors[].code' 2>/dev/null | grep -qE "10004|10006"; then
        ok "[6] R2 bucket '${R2_BUCKET}' already exists"
    else
        die "[6] Unexpected bucket response: $(echo "${BUCKET_RESPONSE}" | jq -c '.errors')"
    fi
fi

info "[6] Enabling r2.dev subdomain"
if $DRY_RUN; then
    R2_DEV_HOSTNAME="pub-dry-run.r2.dev"
    echo "  [dry-run] PUT /r2/buckets/${R2_BUCKET}/domains/managed {enabled: true}"
else
    R2_MANAGED=$(cf_api PUT \
        "/accounts/${CF_ACCOUNT_ID}/r2/buckets/${R2_BUCKET}/domains/managed" \
        -d '{"enabled":true}' 2>/dev/null || true)
    R2_DEV_HOSTNAME="$(echo "${R2_MANAGED}" | jq -r '.result.domain // empty' \
        | grep -o '[a-zA-Z0-9-]*\.r2\.dev' | head -1 || true)"
    if [[ -z "${R2_DEV_HOSTNAME}" ]]; then
        R2_MANAGED_GET=$(cf_api GET \
            "/accounts/${CF_ACCOUNT_ID}/r2/buckets/${R2_BUCKET}/domains/managed")
        R2_DEV_HOSTNAME="$(echo "${R2_MANAGED_GET}" | jq -r '.result.domain // empty' \
            | grep -o '[a-zA-Z0-9-]*\.r2\.dev' | head -1 || true)"
    fi
    [[ -n "${R2_DEV_HOSTNAME}" ]] \
        || die "[6] Could not determine r2.dev hostname — check the Cloudflare dashboard"
    ok "[6] r2.dev hostname: ${R2_DEV_HOSTNAME}"
fi

info "[6] R2 CI credentials needed (R2 S3 tokens must be created in the R2 dashboard)"
if $DRY_RUN; then
    R2_ACCESS_KEY_ID="DRY_RUN_KEY_ID"
    R2_SECRET_ACCESS_KEY="DRY_RUN_SECRET"
elif [[ -z "${R2_ACCESS_KEY_ID:-}" || -z "${R2_SECRET_ACCESS_KEY:-}" ]]; then
    echo ""
    echo "  Create an R2 API token at:"
    echo "  https://dash.cloudflare.com/${CF_ACCOUNT_ID}/r2/api-tokens"
    echo ""
    echo "  Click 'Create Account API token' (not User — Account tokens survive org changes)"
    echo "    Token name:  ${R2_TOKEN_NAME}"
    echo "    Permissions: Object Read & Write"
    echo "    Bucket:      Apply to specific bucket → ${R2_BUCKET}"
    echo ""
    until [[ -n "${R2_ACCESS_KEY_ID:-}" ]]; do
        read -rsp "  Paste Access Key ID (input hidden): " R2_ACCESS_KEY_ID; echo
        [[ -z "${R2_ACCESS_KEY_ID:-}" ]] && echo "  (cannot be blank — try again)"
    done
    until [[ -n "${R2_SECRET_ACCESS_KEY:-}" ]]; do
        read -rsp "  Paste Secret Access Key (input hidden): " R2_SECRET_ACCESS_KEY; echo
        [[ -z "${R2_SECRET_ACCESS_KEY:-}" ]] && echo "  (cannot be blank — try again)"
    done
    export R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY
    cache_set R2_ACCESS_KEY_ID     "$R2_ACCESS_KEY_ID"
    cache_set R2_SECRET_ACCESS_KEY "$R2_SECRET_ACCESS_KEY"
    ok "[6] R2 credentials captured"
fi

if ! $DRY_RUN && [[ -n "${R2_ACCESS_KEY_ID}" && -n "${R2_SECRET_ACCESS_KEY}" ]]; then
    r2_put_secret "R2_ACCESS_KEY_ID"     "${R2_ACCESS_KEY_ID}"
    r2_put_secret "R2_SECRET_ACCESS_KEY" "${R2_SECRET_ACCESS_KEY}"
    r2_put_secret "R2_ENDPOINT"          "${R2_ENDPOINT}"
    ok "[6] R2 credentials stored in r2://${SECRETS_BUCKET}/"
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 7 — DNS CNAME + attach custom domain to R2 bucket
# ════════════════════════════════════════════════════════════════════════════

CNAME_EXISTS=""
if ! $DRY_RUN; then
    CNAME_EXISTS=$(cf_api GET \
        "/zones/${CF_ZONE_ID}/dns_records?type=CNAME&name=${DNS_CNAME}.${CF_ZONE_NAME}" \
        | jq -r '.result[0].id // empty' || true)
fi

if [[ -n "${CNAME_EXISTS}" ]]; then
    ok "[7] DNS CNAME ${DNS_CNAME}.${CF_ZONE_NAME} already exists"
else
    info "[7] Creating DNS CNAME: ${DNS_CNAME}.${CF_ZONE_NAME} → ${R2_DEV_HOSTNAME}"
    if $DRY_RUN; then
        echo "  [dry-run] POST /zones/.../dns_records {type: CNAME, name: ${DNS_CNAME}}"
    else
        cf_api POST "/zones/${CF_ZONE_ID}/dns_records" -d "$(jq -n \
            --arg name    "$DNS_CNAME" \
            --arg content "$R2_DEV_HOSTNAME" \
            '{type:"CNAME",name:$name,content:$content,proxied:true,comment:"{{PKG_NAME}} R2 bucket"}')" >/dev/null
        ok "[7] DNS CNAME created"
    fi
fi

info "[7] Attaching custom domain ${CUSTOM_DOMAIN} to R2 bucket"
if $DRY_RUN; then
    echo "  [dry-run] POST /r2/buckets/${R2_BUCKET}/domains/custom"
else
    DOMAIN_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets/${R2_BUCKET}/domains/custom" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg d "$CUSTOM_DOMAIN" --arg z "$CF_ZONE_ID" '{domain:$d,zoneId:$z,enabled:true}')")
    if [[ "${DOMAIN_HTTP}" == "200" ]]; then
        ok "[7] Custom domain attached: ${CUSTOM_DOMAIN}"
    elif [[ "${DOMAIN_HTTP}" == "409" ]]; then
        ok "[7] Custom domain already attached: ${CUSTOM_DOMAIN}"
    else
        die "[7] Unexpected HTTP ${DOMAIN_HTTP} attaching custom domain — check Cloudflare dashboard"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 7.5 — Cloudflare URL rewrite: trailing / → index.html
# ════════════════════════════════════════════════════════════════════════════

info "[7.5] Creating URL rewrite rule: trailing / → /index.html on ${CUSTOM_DOMAIN}"

# Rewrites any path ending in / to the same path + index.html, enabling
# directory browsing for all repo subdirectories (not just root).
# http_request_redirect is not available on the free plan; http_request_transform
# (rewrite) is — it serves index.html transparently without a 301 round-trip.
REWRITE_EXPR="(http.host eq \"${CUSTOM_DOMAIN}\" and ends_with(http.request.uri.path, \"/\"))"
REWRITE_URI='concat(http.request.uri.path, "index.html")'

if $DRY_RUN; then
    echo "  [dry-run] PUT /zones/.../rulesets/phases/http_request_transform/entrypoint"
else
    PHASE_JSON=$(cf_api GET \
        "/zones/${CF_ZONE_ID}/rulesets/phases/http_request_transform/entrypoint" \
        2>/dev/null || echo '{}')
    RULESET_ID=$(echo "$PHASE_JSON" | jq -r '.result.id // empty' 2>/dev/null || true)
    EXISTING_RULE=$(echo "$PHASE_JSON" | jq -r \
        --arg expr "$REWRITE_EXPR" \
        '.result.rules[]? | select(.expression == $expr) | .id' 2>/dev/null || true)

    RULE_BODY=$(jq -n --arg expr "$REWRITE_EXPR" --arg uri "$REWRITE_URI" \
        '{action:"rewrite",action_parameters:{uri:{path:{expression:$uri}}},expression:$expr,enabled:true}')

    if [[ -n "$EXISTING_RULE" ]]; then
        ok "[7.5] URL rewrite rule already exists (id: ${EXISTING_RULE})"
    elif [[ -z "$RULESET_ID" ]]; then
        RESP=$(cf_api PUT \
            "/zones/${CF_ZONE_ID}/rulesets/phases/http_request_transform/entrypoint" \
            -d "$(jq -n --argjson rule "$RULE_BODY" '{name:"Zone Rewrite Rules",rules:[$rule]}')")
        echo "$RESP" | jq -e '.success == true' &>/dev/null \
            || { err "[7.5] $(echo "$RESP" | jq -r '.errors[0].message')"; exit 1; }
        ok "[7.5] URL rewrite rule created"
    else
        RESP=$(cf_api POST "/zones/${CF_ZONE_ID}/rulesets/${RULESET_ID}/rules" -d "$RULE_BODY")
        echo "$RESP" | jq -e '.success == true' &>/dev/null \
            || { err "[7.5] $(echo "$RESP" | jq -r '.errors[0].message')"; exit 1; }
        ok "[7.5] URL rewrite rule added"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 8 — Upload public signing key to R2, shred local copy
# ════════════════════════════════════════════════════════════════════════════

KEY_LIVE=false
if ! $DRY_RUN && curl -fsSL "https://${CUSTOM_DOMAIN}/key.gpg" 2>/dev/null \
        | gpg --show-keys &>/dev/null 2>&1; then
    KEY_LIVE=true
fi

if $KEY_LIVE; then
    ok "[8] key.gpg already reachable at https://${CUSTOM_DOMAIN}/key.gpg"
    [[ -f "${PUB_KEY}" ]] && shred -u "${PUB_KEY}"
else
    info "[8] Uploading public key → r2://${R2_BUCKET}/key.gpg"
    if $DRY_RUN; then
        echo "  [dry-run] PUT /r2/buckets/${R2_BUCKET}/objects/key.gpg"
        echo "  [dry-run] shred -u ${PUB_KEY}"
    else
        [[ -f "${PUB_KEY}" ]] \
            || die "[8] Public key missing — re-export: gpg --armor --export ${KEY_EMAIL} > ${PUB_KEY}"
        curl -fsSL -X PUT \
            "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/r2/buckets/${R2_BUCKET}/objects/key.gpg" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/octet-stream" \
            --data-binary @"${PUB_KEY}" \
            >/dev/null
        ok "[8] Public key uploaded"
        shred -u "${PUB_KEY}"
        ok "[8] Public key shredded"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 9 — Set GitHub Actions secrets
# ════════════════════════════════════════════════════════════════════════════

info "[9] Setting GitHub Actions secrets on ${GH_REPO}"

if $DRY_RUN; then
    echo "  [dry-run] gh secret set R2_ACCESS_KEY_ID     --repo ${GH_REPO}"
    echo "  [dry-run] gh secret set R2_SECRET_ACCESS_KEY --repo ${GH_REPO}"
    echo "  [dry-run] gh secret set R2_ENDPOINT          --repo ${GH_REPO}"
else
    [[ -n "${R2_SECRET_ACCESS_KEY}" ]] \
        || die "[9] R2_SECRET_ACCESS_KEY empty — see warning above"
    gh secret set R2_ACCESS_KEY_ID     --repo "${GH_REPO}" --body "${R2_ACCESS_KEY_ID}"
    gh secret set R2_SECRET_ACCESS_KEY --repo "${GH_REPO}" --body "${R2_SECRET_ACCESS_KEY}"
    gh secret set R2_ENDPOINT          --repo "${GH_REPO}" --body "${R2_ENDPOINT}"
    ok "[9] GitHub secrets set"
    gh secret list --repo "${GH_REPO}"
fi

# ════════════════════════════════════════════════════════════════════════════
# Done
# ════════════════════════════════════════════════════════════════════════════

echo ""
ok "Steps 1b–9 complete."
echo ""
info "Next: push the first release tag to trigger CI:"
info "  task bump"
info "  # Watch: https://github.com/${GH_REPO}/actions"
echo ""
info "Landing page: https://${CUSTOM_DOMAIN}/"
xdg-open "https://${CUSTOM_DOMAIN}/" 2>/dev/null || open "https://${CUSTOM_DOMAIN}/" 2>/dev/null || true
