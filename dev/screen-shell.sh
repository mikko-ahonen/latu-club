#!/bin/bash
# Telamon-generated shell for screen windows
# New screen windows exec into the claude container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# The human approve credential, ONLY when `tl work --with-authorization`
# started this session (it exports TELAMON_AUTHORIZE). Injected here, at exec
# time, rather than through the container's environment on purpose:
#
#   * `docker compose up -d` does not recreate a container whose spec is
#     unchanged, so passing it at container-creation would silently do
#     nothing for an already-running project.
#   * It would then live in the container's base env for the container's
#     whole life, visible to every later process including `tl wake` — the
#     standing credential this whole gate exists to avoid.
#
# At exec time it belongs to this shell process alone: not the container, not
# other windows unless they opt in too, gone when the session ends.
#
# `-e VAR` with no value passes it from THIS process's environment, so the
# value never appears in argv and `ps` on the node shows only the name.
# See brain req_01M26GP4877GGRVMGBC4KNEA0M.
AUTH_PASS=()
if [ -n "${TELAMON_AUTHORIZE:-}" ]; then
    BRAIN_API_AUTHORIZE_TOKEN=$(
        SECRETS_FILE="$HOME/.telamon/secrets.sops.json" \
            secret get ADMIN_BRAIN_API_AUTHORIZE_TOKEN 2>/dev/null
    )
    if [ -n "$BRAIN_API_AUTHORIZE_TOKEN" ]; then
        export BRAIN_API_AUTHORIZE_TOKEN
        AUTH_PASS=(-e BRAIN_API_AUTHORIZE_TOKEN)
    else
        echo "tl work --with-authorization: no ADMIN_BRAIN_API_AUTHORIZE_TOKEN" \
             "in ~/.telamon/secrets.sops.json on this host; continuing without it." >&2
    fi
fi

exec docker compose exec "${AUTH_PASS[@]}" -e LC_CTYPE=en_US.UTF-8 claude bash -l