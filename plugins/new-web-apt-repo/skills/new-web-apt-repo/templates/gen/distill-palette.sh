#!/usr/bin/env bash
# Extract parent site CSS palette tokens and update apt index style files.
#
# Usage: bash apt/gen/distill-palette.sh <domain>
#
# Tries, in order:
#   1) Astro monorepo: <repo-root>/src/styles/global.css
#   2) Live site:      https://<domain>/styles.css
#   3) Fallback:       keeps greyscale defaults (no changes)
#
# Updates: gen/src.css (@theme block) and gen/static/styles.css (:root block).
# Both files are committed alongside each other — run this once at bootstrap,
# or manually when the parent brand changes.
#
# PALETTE GENERATOR APIS (if no parent site exists):
#   The Color API — GET https://www.thecolorapi.com/scheme?hex=XXXXXX&mode=monochrome&count=5
#   Colormind     — POST http://colormind.io/api/ -d '{"model":"ui"}'

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$APT_DIR")"
SRC_CSS="${SCRIPT_DIR}/src.css"
STYLES_CSS="${SCRIPT_DIR}/static/styles.css"

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \?//'
    exit 0
}

for arg in "$@"; do
    case "$arg" in -h|--help) usage ;; esac
done

if [[ $# -lt 1 ]]; then
    echo "Usage: bash gen/distill-palette.sh <domain>" >&2
    echo "  e.g. bash gen/distill-palette.sh indri.studio" >&2
    exit 1
fi

DOMAIN="$1"

# ── Locate parent CSS ──────────────────────────────────────────────────────

CSS_SOURCE=""
CSS_TMPFILE=""

cleanup() { [[ -n "${CSS_TMPFILE}" ]] && rm -f "${CSS_TMPFILE}" || true; }
trap cleanup EXIT

# Try 1: Astro monorepo — repo-root/src/styles/global.css
ASTRO_CSS="${REPO_ROOT}/src/styles/global.css"
if [[ -f "${ASTRO_CSS}" ]]; then
    CSS_SOURCE="${ASTRO_CSS}"
    echo "[distill] Found Astro CSS: ${ASTRO_CSS}"
fi

# Try 2: live site /styles.css
if [[ -z "${CSS_SOURCE}" ]]; then
    CSS_TMPFILE="$(mktemp /tmp/distill-css-XXXXXX.css)"
    if curl -fsSL --max-time 15 "https://${DOMAIN}/styles.css" \
            -o "${CSS_TMPFILE}" 2>/dev/null && [[ -s "${CSS_TMPFILE}" ]]; then
        CSS_SOURCE="${CSS_TMPFILE}"
        echo "[distill] Fetched https://${DOMAIN}/styles.css"
    else
        rm -f "${CSS_TMPFILE}"
        CSS_TMPFILE=""
        echo "[distill] https://${DOMAIN}/styles.css not found"
    fi
fi

if [[ -z "${CSS_SOURCE}" ]]; then
    echo "[distill] No parent CSS found for ${DOMAIN} — greyscale defaults unchanged."
    exit 0
fi

# ── Extract a CSS custom property value ───────────────────────────────────
# Try each candidate property name in sequence; return first match found.
# Handles single-line values (hex, rgb, font-family); multi-line stacks
# yield only the first line (acceptable for the common monorepo case).

extract() {
    local file="$1"
    shift
    for prop in "$@"; do
        local val
        val=$(awk -v prop="--${prop}:" '
            {
                line = $0
                gsub(/\/\*.*\*\//, "", line)   # strip inline block comments
                if (line ~ ("^[[:space:]]*" prop)) {
                    sub(/^[^:]*:[[:space:]]*/, "", line)
                    sub(/[[:space:]]*;.*$/, "", line)
                    sub(/[[:space:]]+$/, "", line)
                    if (line != "") { print line; exit 0 }
                }
            }
        ' "${file}" 2>/dev/null || true)
        if [[ -n "${val}" ]]; then
            echo "${val}"
            return 0
        fi
    done
    return 1
}

# In-place sed replacement for a CSS custom property line.
# Replaces:  "  --token-name: old-value;[comment]"
# With:      "  --token-name: new-value;"
# Uses | as delimiter so / in font paths doesn't need escaping.
replace_token() {
    local token="$1" val="$2"
    # Escape & and \ in sed replacement string (| is safe as delimiter)
    local esc
    esc=$(printf '%s' "${val}" | sed 's/[\\&]/\\&/g')
    for f in "${SRC_CSS}" "${STYLES_CSS}"; do
        [[ -f "${f}" ]] || continue
        sed -i "s|^\( *--${token}:\).*|\1 ${esc};|" "${f}"
    done
}

# Detect if the current --color-surface in styles.css is dark (avg RGB < 128).
# Returns 0 (true) = dark, 1 (false) = light or indeterminate.
# Only handles hex colours (#rrggbb / #rgb); skips rgb(), hsl(), etc.
is_dark_palette() {
    local surface avg r g b hex
    surface=$(grep -m1 '^\s*--color-surface:' "${STYLES_CSS}" \
              | sed 's/.*:[[:space:]]*//; s/;.*//' | tr -d ' ' || true)
    [[ -z "${surface}" ]] && return 1
    if [[ "${surface}" =~ ^#([0-9a-fA-F]{6})$ ]]; then
        hex="${BASH_REMATCH[1]}"
        r=$((16#${hex:0:2}))
        g=$((16#${hex:2:2}))
        b=$((16#${hex:4:2}))
        avg=$(( (r + g + b) / 3 ))
        [[ $avg -lt 128 ]] && return 0
    elif [[ "${surface}" =~ ^#([0-9a-fA-F]{3})$ ]]; then
        hex="${BASH_REMATCH[1]}"
        r=$((16#${hex:0:1} * 17))
        g=$((16#${hex:1:1} * 17))
        b=$((16#${hex:2:1} * 17))
        avg=$(( (r + g + b) / 3 ))
        [[ $avg -lt 128 ]] && return 0
    fi
    return 1
}

# ── Token mappings ─────────────────────────────────────────────────────────
#
# Each call: apt-token-name  candidate-prop-1 candidate-prop-2 ...
# The first candidate found in the source CSS wins.
# Tokens not found keep the greyscale default from the template.

echo ""
echo "[distill] Scanning: $(basename "${CSS_SOURCE}")"
FOUND=0
MISSING=0

try_token() {
    local apt_token="$1"
    shift
    local val
    val=$(extract "${CSS_SOURCE}" "$@" || true)
    if [[ -n "${val}" ]]; then
        printf "  ✓  --%-34s %s\n" "${apt_token}:" "${val}"
        replace_token "${apt_token}" "${val}"
        FOUND=$((FOUND + 1))
    else
        printf "  -  --%-34s (greyscale default)\n" "${apt_token}:"
        MISSING=$((MISSING + 1))
    fi
}

try_token color-surface           color-surface background color-background bg
try_token color-surface-raised    color-surface-raised surface-raised color-card
try_token color-surface-sunken    color-surface-sunken surface-sunken color-code-bg
try_token color-on-surface        color-on-surface foreground color-foreground color-text
try_token color-on-surface-muted  color-on-surface-muted color-muted muted color-secondary
try_token color-on-surface-dim    color-on-surface-dim color-dim dim color-subtle color-placeholder
try_token color-accent            color-accent accent color-primary primary color-link color-brand
try_token color-accent-dim        color-accent-dim accent-dim color-primary-dim primary-dim
try_token color-on-accent         color-on-accent on-accent color-on-primary on-primary
try_token color-border            color-border border color-separator separator color-divider
try_token font-display            font-display font-heading font-title
try_token font-body               font-body font-sans font-base
try_token font-mono               font-mono font-code font-monospace

echo ""
echo "[distill] ${FOUND} token(s) extracted, ${MISSING} at template default."

# ── Light/dark detection ───────────────────────────────────────────────────
# After token extraction, check the resolved --color-surface and set
# color-scheme accordingly in :root. Forces dark for dark-palette sites
# regardless of the visitor's OS preference; light sites keep the
# @media (prefers-color-scheme: dark) fallback intact.
if is_dark_palette; then
    echo "[distill] Surface is DARK — setting color-scheme: dark on :root (OS preference overridden)"
    for f in "${SRC_CSS}" "${STYLES_CSS}"; do
        [[ -f "${f}" ]] || continue
        sed -i 's/color-scheme: *light;/color-scheme: dark;/g' "${f}"
    done
else
    echo "[distill] Surface is LIGHT — color-scheme: light; OS dark-mode preference preserved via @media"
fi

if [[ "${FOUND}" -gt 0 ]]; then
    echo "[distill] Review and commit: gen/src.css  gen/static/styles.css"
fi
