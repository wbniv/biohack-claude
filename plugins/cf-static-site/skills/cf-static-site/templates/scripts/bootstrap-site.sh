#!/usr/bin/env bash
# Bootstrap https://<DOMAIN>/ on Cloudflare Pages.
# Creates the Pages project, attaches the custom domain, provisions a
# scoped CI deploy token, and wires it into GitHub Actions secrets.
#
# Prerequisite: scripts/bootstrap.sh must have run at least once —
# CF_ACCOUNT_ID and CF_API_TOKEN are loaded from the bootstrap cache.
#
# Usage:
#   bash scripts/bootstrap-site.sh [--dry-run] [-h]

set -euo pipefail

# ── config ────────────────────────────────────────────────────────────────────

GH_REPO="<GH_ORG>/<GH_REPO>"
PAGES_PROJECT="<PROJECT_NAME>"
CUSTOM_DOMAIN="<DOMAIN>"
CI_TOKEN_NAME="<SLUG>-site-ci"
BOOTSTRAP_CACHE="${BASH_SOURCE[0]%/scripts/*}/.creds/bootstrap.env"

DRY_RUN=false

# ── helpers ──────────────────────────────────────────────────────────────────

info() { echo "  [info]  $*"; }
ok()   { echo "  [ok]    $*"; }
warn() { echo "  [warn]  $*" >&2; }
err()  { echo "  [error] $*" >&2; }
die()  { err "$*"; exit 1; }

cache_set() {
    local key="$1" val="$2"
    { grep -v "^${key}=" "$BOOTSTRAP_CACHE" 2>/dev/null || true
      printf '%s=%q\n' "$key" "$val"
    } > "${BOOTSTRAP_CACHE}.tmp" && mv "${BOOTSTRAP_CACHE}.tmp" "$BOOTSTRAP_CACHE"
    chmod 600 "$BOOTSTRAP_CACHE"
}

usage() {
    sed -n '2,10p' "$0" | sed 's/^# //'
    exit 0
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

# Returns HTTP status code only (no -f, so 4xx/5xx don't abort).
cf_api_status() {
    local method="$1" path="$2"
    shift 2
    curl -sSo /dev/null -w "%{http_code}" -X "$method" \
        "https://api.cloudflare.com/client/v4${path}" \
        -H "Authorization: Bearer ${CF_API_TOKEN:-}" \
        -H "Content-Type: application/json" \
        "$@"
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

mkdir -p "$(dirname "$BOOTSTRAP_CACHE")"

if [[ -f "$BOOTSTRAP_CACHE" ]]; then
    # shellcheck source=/dev/null
    source "$BOOTSTRAP_CACHE"
    info "Loaded cached credentials from $BOOTSTRAP_CACHE"
fi

command -v curl &>/dev/null || die "curl not found"
command -v jq   &>/dev/null || die "jq not found"
command -v gh   &>/dev/null || die "gh CLI not found — https://cli.github.com"

if ! $DRY_RUN; then
    gh auth status &>/dev/null || die "gh not authenticated — run: gh auth login"
    [[ -n "${CF_API_TOKEN:-}" ]] || {
        err "CF_API_TOKEN not set."
        err "Create a token at https://dash.cloudflare.com/profile/api-tokens with:"
        err "  Zone     | Zone Settings | Read   (all zones)"
        err "  Zone     | DNS           | Edit   (all zones)"
        err "  Account  | Cloudflare Pages | Edit"
        err "Then: export CF_API_TOKEN=<token> && bash scripts/bootstrap-site.sh"
        exit 1
    }
    if [[ -z "${CF_ACCOUNT_ID:-}" ]]; then
        CF_ACCOUNT_ID=$(cf_api GET "/accounts?per_page=1" | jq -r '.result[0].id')
        [[ -n "$CF_ACCOUNT_ID" && "$CF_ACCOUNT_ID" != "null" ]] \
            || die "Could not retrieve CF_ACCOUNT_ID — check CF_API_TOKEN permissions"
        export CF_ACCOUNT_ID
        cache_set CF_ACCOUNT_ID "$CF_ACCOUNT_ID"
    fi

    # Verify the token has Cloudflare Pages access.
    PAGES_HTTP=$(cf_api_status GET "/accounts/${CF_ACCOUNT_ID}/pages/projects?per_page=1")
    if [[ "$PAGES_HTTP" == "403" ]]; then
        err "CF_API_TOKEN lacks Cloudflare Pages permission."
        err ""
        err "Add 'Pages Write' (Account scope) to your operator token:"
        err "  https://dash.cloudflare.com/profile/api-tokens"
        err "  Find '<SLUG>-operator', click Edit, add:"
        err "    Account | Cloudflare Pages | Edit"
        err ""
        err "Or create a dedicated Pages token and export CF_API_TOKEN=<new-token>, then re-run."
        exit 1
    fi
fi

CF_API_TOKEN="${CF_API_TOKEN:-DRY_RUN_TOKEN}"
CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-DRY_RUN_ACCOUNT_ID}"

echo ""
info "Bootstrap: Cloudflare Pages → https://${CUSTOM_DOMAIN}/"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# Step 0 — Remove www-redirect Page Rules
# Old hosting setups often leave a Cloudflare Page Rule forwarding the apex
# to www.<DOMAIN>. That rule wins over Pages and must be removed first.
# ════════════════════════════════════════════════════════════════════════════

info "[0] Looking for www-redirect Page Rules to remove"
if $DRY_RUN; then
    echo "  [dry-run] GET /zones/.../pagerules — check for www forwarding rules"
else
    CF_ZONE_ID=$(cf_api GET "/zones?name=${CUSTOM_DOMAIN}" | jq -r '.result[0].id')
    [[ -n "$CF_ZONE_ID" && "$CF_ZONE_ID" != "null" ]] \
        || die "[0] Zone for ${CUSTOM_DOMAIN} not found — check token has Zone:Read"
    export CF_ZONE_ID
    cache_set CF_ZONE_ID "$CF_ZONE_ID"
    info "[0] Zone ID: $CF_ZONE_ID"

    PAGE_RULES=$(cf_api GET "/zones/${CF_ZONE_ID}/pagerules?status=active" \
        | jq -r '.result[] | select(.actions[].id == "forwarding_url") | .id' || true)
    if [[ -n "$PAGE_RULES" ]]; then
        while IFS= read -r rule_id; do
            info "[0] Deleting Page Rule $rule_id (forwarding_url)"
            cf_api DELETE "/zones/${CF_ZONE_ID}/pagerules/${rule_id}" >/dev/null
            ok "[0] Deleted Page Rule $rule_id"
        done <<< "$PAGE_RULES"
    else
        ok "[0] No forwarding Page Rules found"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 1 — Create Pages project
# ════════════════════════════════════════════════════════════════════════════

info "[1] Ensuring Pages project '${PAGES_PROJECT}' exists"
if $DRY_RUN; then
    echo "  [dry-run] POST /accounts/.../pages/projects {name: ${PAGES_PROJECT}}"
else
    PROJ_RESP=$(cf_api GET "/accounts/${CF_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}" \
        2>/dev/null || echo '{}')
    if echo "$PROJ_RESP" | jq -e '.result.name' &>/dev/null; then
        ok "[1] Pages project '${PAGES_PROJECT}' already exists"
    else
        CREATE_RESP=$(cf_api POST \
            "/accounts/${CF_ACCOUNT_ID}/pages/projects" \
            -d "$(jq -n --arg n "$PAGES_PROJECT" '{name:$n,production_branch:"main"}')")
        echo "$CREATE_RESP" | jq -e '.success == true' &>/dev/null \
            || die "[1] Failed to create Pages project: $(echo "$CREATE_RESP" | jq -c '.errors')"
        ok "[1] Pages project '${PAGES_PROJECT}' created"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 2 — DNS CNAME for apex domain
# Pages does NOT auto-create DNS even when the zone is on the same account.
# Add a proxied CNAME (Cloudflare flattens it at the apex automatically).
# ════════════════════════════════════════════════════════════════════════════

info "[2] Creating DNS CNAME: ${CUSTOM_DOMAIN} → ${PAGES_PROJECT}.pages.dev"
if $DRY_RUN; then
    echo "  [dry-run] POST /zones/.../dns_records {type:CNAME, name:${CUSTOM_DOMAIN}}"
else
    CF_ZONE_ID=$(cf_api GET "/zones?name=${CUSTOM_DOMAIN}" | jq -r '.result[0].id')
    [[ -n "$CF_ZONE_ID" && "$CF_ZONE_ID" != "null" ]] \
        || die "[2] Zone for ${CUSTOM_DOMAIN} not found — check CF_API_TOKEN has DNS:Edit"

    CNAME_EXISTS=$(cf_api GET "/zones/${CF_ZONE_ID}/dns_records?type=CNAME&name=${CUSTOM_DOMAIN}" \
        | jq -r '.result[0].id // empty' || true)
    if [[ -n "$CNAME_EXISTS" ]]; then
        ok "[2] DNS CNAME already exists"
    else
        cf_api POST "/zones/${CF_ZONE_ID}/dns_records" -d "$(jq -n \
            --arg name    "$CUSTOM_DOMAIN" \
            --arg content "${PAGES_PROJECT}.pages.dev" \
            '{type:"CNAME",name:$name,content:$content,proxied:true,comment:"Cloudflare Pages site"}')" >/dev/null
        ok "[2] DNS CNAME created: ${CUSTOM_DOMAIN} → ${PAGES_PROJECT}.pages.dev"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 3 — Attach custom domain to Pages project
# ════════════════════════════════════════════════════════════════════════════

info "[3] Attaching custom domain ${CUSTOM_DOMAIN} to Pages project"
if $DRY_RUN; then
    echo "  [dry-run] POST /accounts/.../pages/projects/${PAGES_PROJECT}/domains {name: ${CUSTOM_DOMAIN}}"
else
    DOMAIN_RESP=$(curl -sS -X POST \
        "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}/domains" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg d "$CUSTOM_DOMAIN" '{name:$d}')" 2>/dev/null || echo '{}')
    if echo "$DOMAIN_RESP" | jq -e '.success == true' &>/dev/null; then
        ok "[3] Custom domain ${CUSTOM_DOMAIN} attached"
    elif echo "$DOMAIN_RESP" | jq -r '.errors[].message' 2>/dev/null \
            | grep -qi "already\|conflict\|exist"; then
        ok "[3] Custom domain ${CUSTOM_DOMAIN} already attached"
    else
        warn "[3] Domain attach response: $(echo "$DOMAIN_RESP" | jq -c '.')"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 3 — Create scoped CI token for Pages deploy
# ════════════════════════════════════════════════════════════════════════════

CI_TOKEN_VALUE=""
info "[3] Creating scoped CI token '${CI_TOKEN_NAME}'"

if $DRY_RUN; then
    CI_TOKEN_VALUE="DRY_RUN_CI_TOKEN"
    echo "  [dry-run] GET /user/tokens/permission_groups → Pages Write"
    echo "  [dry-run] POST /user/tokens {name: ${CI_TOKEN_NAME}}"
else
    PAGES_PERM_ID=$(cf_api GET "/user/tokens/permission_groups" 2>/dev/null \
        | jq -r '.result[] | select(.name == "Pages Write") | .id' 2>/dev/null \
        || true)

    if [[ -z "${PAGES_PERM_ID:-}" ]]; then
        warn "[3] Could not look up 'Pages Write' permission group automatically."
        warn "[3] Create the token manually at: https://dash.cloudflare.com/profile/api-tokens"
        warn "[3]   Name: ${CI_TOKEN_NAME}"
        warn "[3]   Permission: Pages Write (Account scope)"
        echo ""
        until [[ -n "${CI_TOKEN_VALUE:-}" ]]; do
            read -rsp "  Paste token value (input hidden): " CI_TOKEN_VALUE; echo
            [[ -z "${CI_TOKEN_VALUE:-}" ]] && echo "  (cannot be blank — try again)"
        done
    else
        TOKEN_RESP=$(cf_api POST "/user/tokens" -d "$(jq -n \
            --arg name   "$CI_TOKEN_NAME" \
            --arg acc_id "$CF_ACCOUNT_ID" \
            --arg perm   "$PAGES_PERM_ID" \
            '{
              name: $name,
              policies: [{
                effect: "allow",
                resources: { ("com.cloudflare.api.account." + $acc_id): "*" },
                permission_groups: [{ id: $perm }]
              }]
            }')")
        echo "$TOKEN_RESP" | jq -e '.success == true' &>/dev/null \
            || die "[3] Failed to create CI token: $(echo "$TOKEN_RESP" | jq -c '.errors')"
        CI_TOKEN_VALUE=$(echo "$TOKEN_RESP" | jq -r '.result.value')
        ok "[3] CI token '${CI_TOKEN_NAME}' created"
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Step 4 — Wire GitHub Actions secrets
# ════════════════════════════════════════════════════════════════════════════

info "[4] Setting GitHub Actions secrets on ${GH_REPO}"
if $DRY_RUN; then
    echo "  [dry-run] gh secret set CF_PAGES_API_TOKEN  --repo ${GH_REPO}"
    echo "  [dry-run] gh secret set CF_PAGES_ACCOUNT_ID --repo ${GH_REPO}"
else
    gh secret set CF_PAGES_API_TOKEN  --repo "${GH_REPO}" --body "${CI_TOKEN_VALUE}"
    gh secret set CF_PAGES_ACCOUNT_ID --repo "${GH_REPO}" --body "${CF_ACCOUNT_ID}"
    ok "[4] GitHub secrets set"
    gh secret list --repo "${GH_REPO}"
fi

# ════════════════════════════════════════════════════════════════════════════
# Done
# ════════════════════════════════════════════════════════════════════════════

echo ""
ok "Site bootstrap complete."
echo ""
info "Next: push a tag to deploy."
info "  git tag v0.1.0 && git push origin v0.1.0"
info "  Watch: https://github.com/${GH_REPO}/actions"
echo ""
info "Site will be live at: https://${CUSTOM_DOMAIN}/"
