#!/bin/bash
# Telamon-generated shell for screen windows
# New screen windows exec into the claude container

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
exec docker compose exec -e LC_CTYPE=en_US.UTF-8 claude bash -l