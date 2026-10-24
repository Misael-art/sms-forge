#!/usr/bin/env bash
# Compatibility entry point: pinned SDK + isolated Python; no implicit OS mutation.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$here/bootstrap_host.sh" --apply --profile build "$@"
