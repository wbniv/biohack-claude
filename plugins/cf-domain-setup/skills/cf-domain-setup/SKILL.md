---
name: cf-domain-setup
description: Use this skill when adding a domain to Cloudflare on the free plan, creating a scoped bootstrap API token, and verifying the zone is active. Automates zone creation, nameserver lookup, and activation polling via curl. Trigger phrases: "set up cloudflare domain", "add domain to cloudflare", "cloudflare zone setup", "get domain into cloudflare", "cloudflare free domain setup".
version: 1.0.0
---

# Cloudflare Domain Setup

Gets a domain into Cloudflare (free plan) and active, with maximum automation via the Cloudflare API. The only unavoidable manual steps are: creating the account (once, if needed), creating one meta-token (2 min in UI), and updating nameservers at your registrar.

Outputs: `CF_TOKEN`, `CF_ACCOUNT_ID`, `ZONE_ID` — consumed directly by `cloudflare-static-site`.

Requires: `curl`, `jq`

---

## Step 0 — Collect inputs

Ask for all at once before doing anything:

```
1. Domain      — apex domain, e.g. worldfoundry.org
2. Account ID  — 32-char hex from your Cloudflare dashboard URL after login:
                   https://dash.cloudflare.com → URL becomes
                   dash.cloudflare.com/<ACCOUNT_ID>/home/overview
                 If you don't have a Cloudflare account yet, say "new account".
```

If user says "new account":
> Sign up at https://dash.cloudflare.com/sign-up — it's free. Come back with your Account ID once logged in.

Wait for both answers before Phase A.

---

## Phase A — Create meta-token (one manual step, ~2 min)

This token's only job is creating the real bootstrap token. It has a narrow single permission and expires in 1 day.

Tell the user:

> **One manual step** — create a short-lived "token creator" token:
>
> 1. Go to: https://dash.cloudflare.com/profile/api-tokens
> 2. Click **Create Token** → **Create Custom Token** (bottom of the template list)
> 3. Name it: `<DOMAIN>-meta` (or anything; it's temporary)
> 4. Under **Permissions**, add exactly one:
>    - **User** → **API Tokens** → **Edit**
>    *(No account or zone resources needed — this permission is user-scoped.)*
> 5. Under **TTL**, set expiry to **tomorrow** (1-day safety net).
> 6. Click **Continue to Summary** → **Create Token** — copy it now (shown once).
>
> Paste the meta-token when ready.

Wait for the meta-token before Phase B.

---

## Phase B — Create bootstrap token (automated)

Using the meta-token, create a scoped bootstrap token via API. This avoids entering permissions by hand for the real token.

```bash
export CF_META_TOKEN=<paste-meta-token>
export CF_ACCOUNT_ID=<ACCOUNT_ID>
export DOMAIN=<DOMAIN>

# Create bootstrap token with all permissions needed for Terraform phases
BOOTSTRAP_RESP=$(curl -s -X POST "https://api.cloudflare.com/client/v4/user/api-tokens" \
  -H "Authorization: Bearer $CF_META_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'"$DOMAIN"'-bootstrap",
    "policies": [
      {
        "effect": "allow",
        "resources": {
          "com.cloudflare.api.account.'"$CF_ACCOUNT_ID"'": "*"
        },
        "permission_groups": [
          {"id": "c1fde68c7bcc44588cbb6ddbc16d6480", "name": "Zone Write"},
          {"id": "e17beae8b8cb423197ce817ed5c2c4a8", "name": "DNS Write"},
          {"id": "28f4b596e7d643029c524985477ae49a", "name": "Workers Scripts Write"},
          {"id": "e6d2e7cdb03a4b5cbfcb0a35d2d3b022", "name": "Workers Routes Write"},
          {"id": "3030687196b94b638145a3953da2b699", "name": "Email Routing Write"},
          {"id": "0f72891705e44b8ca3be9e2c5b97fc08", "name": "Account Settings Read"}
        ]
      },
      {
        "effect": "allow",
        "resources": {
          "com.cloudflare.api.user.'"$(curl -s https://api.cloudflare.com/client/v4/user -H "Authorization: Bearer $CF_META_TOKEN" | jq -r '.result.id')"'": "*"
        },
        "permission_groups": [
          {"id": "0cecf0c89b394f78a2f2f2db5c6e5a40", "name": "API Tokens Write"}
        ]
      }
    ],
    "not_before": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
    "expires_on": "'"$(date -u -d '+2 days' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+2d +%Y-%m-%dT%H:%M:%SZ)"'"
  }')

export CF_TOKEN=$(echo "$BOOTSTRAP_RESP" | jq -r '.result.value')
BOOTSTRAP_TOKEN_ID=$(echo "$BOOTSTRAP_RESP" | jq -r '.result.id')

echo "Bootstrap token: $CF_TOKEN"
echo "Bootstrap token ID (save for revocation): $BOOTSTRAP_TOKEN_ID"
```

If the token value is `null`, show the full response for debugging:
```bash
echo "$BOOTSTRAP_RESP" | jq .
```

> **Permission group UUIDs** above are Cloudflare-managed stable identifiers — do not look them up dynamically.
> If any UUID has changed (rare), look up current IDs at:
> https://api.cloudflare.com/client/v4/user/tokens/permission_groups

---

## Phase C — Add zone (automated)

Check if the zone already exists, then create or fetch it:

```bash
# Check for existing zone
EXISTING_ZONE=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN&account.id=$CF_ACCOUNT_ID" \
  -H "Authorization: Bearer $CF_TOKEN" | jq -r '.result[0].id // empty')

if [ -n "$EXISTING_ZONE" ]; then
  export ZONE_ID=$EXISTING_ZONE
  echo "Zone already exists: $ZONE_ID"
  ZONE_RESP=$(curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" \
    -H "Authorization: Bearer $CF_TOKEN")
else
  # Create zone on free plan
  ZONE_RESP=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones" \
    -H "Authorization: Bearer $CF_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$DOMAIN\",\"account\":{\"id\":\"$CF_ACCOUNT_ID\"},\"jump_start\":true}")

  export ZONE_ID=$(echo "$ZONE_RESP" | jq -r '.result.id')
  echo "Zone created: $ZONE_ID"
fi

# Extract nameservers
NS1=$(echo "$ZONE_RESP" | jq -r '.result.name_servers[0]')
NS2=$(echo "$ZONE_RESP" | jq -r '.result.name_servers[1]')
echo ""
echo "Nameservers to set at your registrar:"
echo "  $NS1"
echo "  $NS2"
```

---

## Phase D — Update nameservers at registrar (manual, ~2 min)

Tell the user both nameserver values, then:

> Log in to your domain registrar and update the nameservers to Cloudflare's:
>
> | Registrar | Direct link |
> |-----------|------------|
> | **Namecheap** | https://ap.www.namecheap.com/Domains/DomainControlPanel/<DOMAIN>/domain/ |
> | **GoDaddy** | https://dcc.godaddy.com/manage/<DOMAIN>/dns |
> | **Squarespace / Google Domains** | https://domains.squarespace.com/ → select domain → DNS |
> | **Porkbun** | https://porkbun.com/account/domainsSpeedy → click domain → NS |
> | **Cloudflare Registrar** | Already there — skip this step |
> | **Other** | Log in → find "Nameservers" or "DNS" section for `<DOMAIN>` |
>
> Replace any existing nameservers with:
> ```
> <NS1>
> <NS2>
> ```
>
> Tell me when changed. Propagation is seconds (Cloudflare registrar) to 48 h (others) — we'll poll.

---

## Phase E — Poll for zone activation (automated)

```bash
echo "Polling zone status every 30 s — Ctrl-C to stop and resume later…"
while true; do
  STATUS=$(curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" \
    -H "Authorization: Bearer $CF_TOKEN" | jq -r '.result.status')
  echo "$(date '+%H:%M:%S')  $DOMAIN  →  $STATUS"
  [ "$STATUS" = "active" ] && echo "" && echo "Zone is active — ready for Terraform." && break
  sleep 30
done
```

To check status manually at any time:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" | jq -r '.result.status'
```

---

## Phase F — Save outputs

```bash
# Persist for Terraform phases
cat >> .env <<EOF
CF_TOKEN=$CF_TOKEN
CF_ACCOUNT_ID=$CF_ACCOUNT_ID
ZONE_ID=$ZONE_ID
BOOTSTRAP_TOKEN_ID=$BOOTSTRAP_TOKEN_ID
EOF

echo ""
echo "=== Outputs for cloudflare-static-site ==="
echo "export CLOUDFLARE_API_TOKEN=$CF_TOKEN"
echo "export TF_VAR_account_id=$CF_ACCOUNT_ID"
echo "export ZONE_ID=$ZONE_ID"
```

The meta-token (`CF_META_TOKEN`) can be revoked now — it has served its purpose:
> https://dash.cloudflare.com/profile/api-tokens — click **×** next to `<DOMAIN>-meta`.

The bootstrap token (`CF_TOKEN`) stays active and is passed to `cloudflare-static-site`. It is revoked at the end of that skill's Phase D.

---

## Summary of manual steps

| Step | What | Why unavoidable |
|------|------|----------------|
| Account creation | https://dash.cloudflare.com/sign-up | No API without an account |
| Meta-token (Phase A) | 1 permission in UI, 2 min | Can't create a token without an existing token |
| Nameservers (Phase D) | Update at registrar | Registrar auth is outside Cloudflare's API |

Everything else is automated.

---

## First-run: verify permission group UUIDs

The UUIDs in Phase B are Cloudflare-managed stable identifiers, but they can drift on rare occasions. On your first run of this skill, verify them before trusting the bootstrap token creation:

```bash
curl -s "https://api.cloudflare.com/client/v4/user/tokens/permission_groups" \
  -H "Authorization: Bearer $CF_META_TOKEN" \
  | jq '.result[] | {name, id}' | grep -A1 -E '"(Zone Write|DNS Write|Workers Scripts Write|Workers Routes Write|Email Routing Write|Account Settings Read|API Tokens Write)"'
```

Cross-check against the IDs in Phase B. If any have changed, update Phase B in this file and commit.
