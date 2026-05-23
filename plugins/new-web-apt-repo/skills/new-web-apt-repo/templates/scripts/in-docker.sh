#!/usr/bin/env bash
# Host-side wrapper: build (cached) the apt-builder image and run the given
# command inside it with the repo bind-mounted at /work.
#
# Usage:
#   bash apt/scripts/in-docker.sh bash scripts/build-all.sh
#   bash apt/scripts/in-docker.sh bash scripts/publish-local.sh
#
# Mounts:
#   - $(pwd):/work                                    repo root
#   - $HOME/.gnupg:/tmp/.gnupg:ro   (if it exists)    host keyring for local signing
#
# Forwards GPG_PRIVATE_KEY / GPG_KEY / R2_* env vars if set, so CI and local
# runs use the same script invocation surface.

set -eo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

if ! command -v docker &>/dev/null; then
    echo "ERROR: docker not installed or not on PATH" >&2
    exit 1
fi

# Resolve repo root: this script lives at <repo>/apt/scripts/in-docker.sh,
# so two levels up is the repo root, one level up is apt/.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$APT_DIR/.." && pwd)"

IMG="apt-builder:local"

# Build image (silent — heavy on first run, ~instant after).
docker build -q -f "$APT_DIR/Dockerfile" -t "$IMG" "$APT_DIR" >/dev/null

# Conditional GPG keyring mount (skipped in CI, used locally).
gnupg_mount=()
if [[ -d "$HOME/.gnupg" ]]; then
    gnupg_mount=(-v "$HOME/.gnupg:/tmp/.gnupg:ro")
fi

# Forward CI-style env vars when present. The RCLONE_CONFIG_* family carries
# rclone's inline backend config (endpoint, keys, region) from the workflow
# into the container — rclone reads those env vars in lieu of a config file.
env_args=()
for var in GPG_PRIVATE_KEY GPG_KEY R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_ENDPOINT SUITE; do
    if [[ -n "${!var-}" ]]; then
        env_args+=(-e "$var")
    fi
done
while IFS= read -r var; do
    [[ -n "$var" ]] && env_args+=(-e "$var")
done < <(compgen -e | grep '^RCLONE_CONFIG_' || true)

# TTY for interactive shells, but only when stdin is a TTY (CI is not).
tty_args=()
if [[ -t 0 && -t 1 ]]; then
    tty_args=(-it)
fi

docker run --rm \
    --user "$(id -u):$(id -g)" \
    "${tty_args[@]}" \
    "${gnupg_mount[@]}" \
    "${env_args[@]}" \
    -v "$REPO_ROOT:/work" \
    -w /work/apt \
    "$IMG" "$@"
