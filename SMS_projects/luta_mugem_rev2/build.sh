#!/usr/bin/env bash
# build.sh do PROJETO — delega ao wrapper. Logica de build NUNCA aqui.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Localiza a RAIZ do workspace subindo os diretorios ate achar tools/sms_wrapper.
# Profundidade fixa (../../) quebrava probes de laboratorio, que vivem um nivel
# mais fundo (SMS_projects/_laboratorio/<probe>/) — exatamente o que o runbook
# laboratory-mode.md manda criar.
ROOT="$DIR"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/tools/sms_wrapper" ]; do
  ROOT="$(dirname "$ROOT")"
done
[ -d "$ROOT/tools/sms_wrapper" ] || { echo "[FAIL] raiz do SMSForge nao encontrada acima de $DIR"; exit 2; }
exec python3 "$ROOT/tools/sms_wrapper/build_inner.py" --project "$DIR" "$@"
