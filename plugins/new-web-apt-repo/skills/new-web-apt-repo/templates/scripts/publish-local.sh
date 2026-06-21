#!/usr/bin/env bash
# Add .deb files from dist/ to the aptly repo, publish to ./public/, build
# CSS via Tailwind, and generate index.html via gen-index.py.
#
# An empty dist/ is fine (Phase A — no packages yet). The publish step still
# produces a valid signed repo tree; index.html will show an empty package list.
#
# Usage:
#   bash scripts/build-all.sh        # optional — populates dist/*.deb
#   bash scripts/init-repo.sh
#   bash scripts/publish-local.sh
#   # Point apt at file://$(pwd)/public to verify locally.

set -euo pipefail
cd "$(dirname "$0")/.."

RUNTIME_CONFIG="/tmp/aptly-{{REPO_NAME}}.conf"
PUBLIC_DIR="$(pwd)/public"
jq --arg pub "$PUBLIC_DIR" \
    '.FileSystemPublishEndpoints = {"public": {"rootDir": $pub, "linkMethod": "copy", "verifyMethod": "md5"}}' \
    aptly/aptly.conf > "$RUNTIME_CONFIG"
export APTLY_CONFIG="${APTLY_CONFIG:-$RUNTIME_CONFIG}"
SUITE="${SUITE:-{{SUITE}}}"
GPG_KEY="${GPG_KEY:-}"

if ! command -v aptly &>/dev/null; then
    echo "ERROR: aptly not installed. Run: sudo apt install aptly" >&2
    exit 1
fi

if ls dist/*.deb &>/dev/null 2>&1; then
    echo "=== Adding dist/*.deb to repo '{{REPO_NAME}}' ==="
    aptly -config="$APTLY_CONFIG" repo add -force-replace {{REPO_NAME}} dist/
else
    echo "=== No .debs in dist/ — publishing empty repo ==="
fi

echo
echo "=== Dropping previous published snapshot (if any) ==="
aptly -config="$APTLY_CONFIG" publish drop "$SUITE" filesystem:public: 2>/dev/null || true

echo
echo "=== Publishing to ./public/ ==="
gpg_args=(-skip-signing)
if [[ -n "$GPG_KEY" ]]; then
    gpg_args=(-gpg-key="$GPG_KEY" -batch)
fi
# -origin/-label set the published Release's Origin/Label to a clean vendor name
# (apt clients + Repology surface them) instead of aptly's ". <suite>" default.
aptly -config="$APTLY_CONFIG" publish repo \
    "${gpg_args[@]}" \
    -origin="{{ORIGIN_LABEL}}" \
    -label="{{ORIGIN_LABEL}}" \
    -architectures=amd64,arm64,all,source \
    -distribution="$SUITE" \
    {{REPO_NAME}} filesystem:public:

# NOTE: gen/static/styles.css is the SHIPPED design CSS — hand-authored, with
# component classes (.site-header, .wordmark, etc.) used by gen-index.py.
# gen/src.css contains only @theme tokens as a Tailwind starting point but is
# NOT compiled here, because doing so would overwrite the design with bare
# Tailwind utilities. To customise the design, edit gen/static/styles.css
# directly. If you want Tailwind-driven utility classes, extend src.css with
# @layer components{} definitions and run tailwindcss manually.

echo
echo "=== Generating index.html ==="
python3 gen/gen-index.py \
    --root public/ --out public/ \
    --static gen/static/ --config gen/config.py --quiet

echo
echo "=== Published — apt sources line ==="
echo "deb [trusted=yes] file://$(pwd)/public $SUITE main"
