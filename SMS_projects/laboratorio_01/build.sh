#!/usr/bin/env bash
# build.sh do PROJETO — delega ao wrapper. Logica de build NUNCA aqui.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/../../tools/sms_wrapper/build_inner.py" --project "$DIR" "$@"
