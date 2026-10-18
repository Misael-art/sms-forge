#!/usr/bin/env bash
# Fontes canonicas do estudo integrado. A logica de build esta no wrapper.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$DIR"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/tools/sms_wrapper" ]; do
  ROOT="$(dirname "$ROOT")"
done
[ -d "$ROOT/tools/sms_wrapper" ] || { echo "[FAIL] raiz do SMSForge nao encontrada acima de $DIR"; exit 2; }
exec python3 "$ROOT/tools/sms_wrapper/build_luta_integrada.py" "$@"
