# Telamon-generated Dockerfile for latu-club
# Stages: base → claude (development with Claude Code)
# Hugo extended static site. The site is built and published by the Gitea
# Actions workflow (.gitea/workflows/deploy.yml), not from this image.

ARG HUGO_VERSION=0.141.0
ARG UID=1000
ARG GID=1000

# ==============================================================================
# BASE - Hugo extended + maintenance utilities
# ==============================================================================
FROM debian:bookworm-slim AS base

ARG HUGO_VERSION
ARG UID=1000
ARG GID=1000

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    ca-certificates \
    git \
    openssh-client \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

# Hugo extended (SCSS/SASS support built in). dpkg arch (amd64/arm64)
# matches Hugo's release asset naming.
RUN ARCH=$(dpkg --print-architecture) \
    && curl -fsSL "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-${ARCH}.tar.gz" \
       | tar -xz -C /usr/local/bin hugo

# Create non-root user
RUN groupadd -g ${GID} dev \
    && useradd -m -u ${UID} -g ${GID} -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

USER dev
WORKDIR /home/dev

ENV BASH_ENV=/home/dev/.bash_env
RUN touch "$BASH_ENV" && echo '. "$BASH_ENV"' >> "$HOME/.bashrc"

WORKDIR /src

EXPOSE 8020

CMD ["hugo", "server", "--bind", "0.0.0.0", "--port", "8020"]

# ==============================================================================
# CLAUDE - Development + Claude Code for LLM-assisted work
# ==============================================================================
FROM base AS claude

# Node.js via nvm (for Claude Code and optional asset pipelines)
ENV NODE_VERSION=24.11.1
ENV NVM_DIR=/home/dev/.nvm

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION

RUN echo 'export NVM_DIR="$HOME/.nvm"' >> "$BASH_ENV" \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"' >> "$BASH_ENV"

# Install Claude Code natively
RUN curl -fsSL https://claude.ai/install.sh | bash \
    && echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$BASH_ENV"

# Git configuration
RUN echo 'git config --global core.sshCommand "ssh -i /home/dev/.ssh/id_ed25519"' >> "$BASH_ENV" \
    && echo 'git config --global --add safe.directory /src' >> "$BASH_ENV"

# ------------------------------------------------------------------------------
# tulisalama platform toolbelt (shared include: templates/_shared/private-cli.j2)
#
# Installs the tulisalama-tools meta-package — `secret`, `brain-cli` and the
# forge-generic `issues` CLI — over git+ssh from the tulisalama Gitea. The
# compose file forwards the build key (build.ssh); see the compose template.
#
# Self-sufficient across base images: python-slim already has python3+pip in
# /usr/local, debian-slim and temurin get git/ssh/python3/pip from apt first.
# PIP_BREAK_SYSTEM_PACKAGES is for bookworm's PEP-668 guard (pip >= 23 honours
# it, jammy's older pip ignores it); scoped to the one RUN, not the image.
#
# PRIVATE_CLI_BUST busts only this layer, so the @main install refreshes on
# rebuild rather than caching forever; `tl build` sets it to the day's UTC
# date. Include this at the END of a claude stage that runs as user `dev`.
# ------------------------------------------------------------------------------
USER root
ARG PRIVATE_CLI_BUST=static
RUN --mount=type=ssh set -eux \
    && echo "private-cli cache: ${PRIVATE_CLI_BUST}" \
    && { command -v git && command -v ssh-keyscan && python3 -m pip --version; } >/dev/null 2>&1 \
       || { apt-get update \
            && apt-get install --no-install-recommends -y \
                 git openssh-client ca-certificates python3 python3-pip \
            && rm -rf /var/lib/apt/lists/*; } \
    && mkdir -p /root/.ssh \
    && ssh-keyscan -p 2222 git.tulisalama.com >> /root/.ssh/known_hosts 2>/dev/null \
    && PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install --no-cache-dir \
        "git+ssh://git@git.tulisalama.com:2222/tulisalama-tools/tulisalama-tools.git@main" \
    && printf '#!/bin/sh\n# secret finds its store relative to cwd; the project is always at /src\nexport SECRETS_FILE="${SECRETS_FILE:-/src/secrets.sops.json}"\nexec secret exec BRAIN_API_TOKEN -- brain-cli "$@"\n' \
        > /usr/local/bin/brain \
    && chmod 0755 /usr/local/bin/brain
USER dev
CMD ["bash"]