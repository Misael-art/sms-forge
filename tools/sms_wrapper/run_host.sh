#!/usr/bin/env bash
# Use a project environment without editing shell startup files.
set -euo pipefail
SMSFORGE_RUN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$SMSFORGE_RUN_ROOT/tools/sms_wrapper/host_bootstrap.py" run -- "$@"
