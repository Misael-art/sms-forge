#!/usr/bin/env bash
# Compatibility entrypoint. Host installation now has one implementation.
set -euo pipefail
SMSFORGE_ENSURE_HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SMSFORGE_ENSURE_HERE/bootstrap_host.sh" "$@"
