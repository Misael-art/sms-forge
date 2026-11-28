#!/usr/bin/env bash
# A clean Ubuntu/Debian host needs only bash, Python 3 and git to start.
set -euo pipefail
SMSFORGE_BOOT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3 ausente. Ubuntu/WSL: sudo apt-get update && sudo apt-get install -y python3 python3-venv git ca-certificates' >&2
  exit 2
fi
exec python3 "$SMSFORGE_BOOT_ROOT/tools/sms_wrapper/host_bootstrap.py" install "$@"
