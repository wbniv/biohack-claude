# Builder image for a signed APT repo on Cloudflare R2.
#
# Provides every tool the build/publish/sign pipeline needs:
#   - dpkg-buildpackage + debhelper + lintian   (package building)
#   - aptly + gnupg2 + rclone                   (repo management, signing, R2 upload)
#   - python3 + tailwindcss (via npx)           (gen-index.py, CSS build)
#
# Used both locally (`task apt:*` → scripts/in-docker.sh) and in CI
# (.github/workflows/publish.yml builds and runs this image).
#
# Image is layer-cached; rebuilds are near-instant after the first.
#
# Base = ubuntu:26.04 (the target distribution). MUST match the apt suite's
# Ubuntu release so dpkg-shlibdeps pins to the right library sonames. A
# Debian-base builder would silently pin to bookworm sonames (e.g.
# libavcodec59) and ship .debs that won't install on Ubuntu 26.04 —
# the exact failure mode we hit in vgmstream_2083-1foundry2 on 2026-05-20.

FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
        # Package building
        build-essential \
        debhelper \
        dpkg-dev \
        devscripts \
        fakeroot \
        lintian \
        # APT repo management + signing + upload
        aptly \
        gnupg2 \
        rclone \
        # gen-index.py
        python3 \
        # Utilities
        ca-certificates \
        curl \
        jq \
        git \
    && rm -rf /var/lib/apt/lists/*

# Tailwind CSS standalone binary — single executable, no Node.js required.
# Auto-selects arch (amd64 or arm64) based on the build platform.
ARG TARGETARCH
RUN set -eu; \
    case "${TARGETARCH:-amd64}" in \
        amd64) TW_ARCH=x64 ;; \
        arm64) TW_ARCH=arm64 ;; \
        *)     echo "Unsupported arch: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /usr/local/bin/tailwindcss \
        "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-${TW_ARCH}"; \
    chmod +x /usr/local/bin/tailwindcss; \
    /usr/local/bin/tailwindcss --help 2>&1 | head -3

# Aptly state goes under $HOME/.aptly — point HOME at a per-run-writable
# location so --user $(id -u):$(id -g) (set by scripts/in-docker.sh) works.
# /tmp is world-writable inside the container.
ENV HOME=/tmp

WORKDIR /work/apt

CMD ["bash"]
