#!/usr/bin/env bash
# run.sh — abre a ROM no emulador gate. Sem ROM = falha honesta.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$(basename "$DIR")"
if [ "$#" -gt 1 ]; then
  echo "Uso: $0 [caminho-da-ROM.sms]" >&2
  exit 2
fi
if [ "$#" -eq 1 ]; then
  case "$1" in
    /*) ROM="$1" ;;
    *)  ROM="$PWD/$1" ;;
  esac
  if [ ! -f "$ROM" ]; then
    echo "[FAIL] ROM não encontrada: $ROM" >&2
    exit 1
  fi
else
  ROM="$DIR/out/rom/$NAME.sms"
  if [ ! -f "$ROM" ]; then
    echo "[FAIL] ROM nominal ausente. Passe o caminho da candidata .sms ao abrir um ensaio." >&2
    exit 1
  fi
fi
# Localiza a RAIZ do workspace subindo os diretorios ate achar tools/sms_wrapper.
# Profundidade fixa (../../) quebrava probes de laboratorio, que vivem um nivel
# mais fundo (SMS_projects/_laboratorio/<probe>/) — exatamente o que o runbook
# laboratory-mode.md manda criar.
ROOT="$DIR"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/tools/sms_wrapper" ]; do
  ROOT="$(dirname "$ROOT")"
done
[ -d "$ROOT/tools/sms_wrapper" ] || { echo "[FAIL] raiz do SMSForge nao encontrada acima de $DIR"; exit 2; }
EMU_JSON="$ROOT/tools/emuladores/emulators.json"
EMU=$(python3 - "$EMU_JSON" <<'EOF'
import json,sys,shutil
try:
    p=json.load(open(sys.argv[1])).get("default_emulator")
except Exception:
    p=None
print(p or shutil.which("openmsx") or shutil.which("emulicious") or "")
EOF
)
[ -n "$EMU" ] || { echo "[FAIL_AMBIENTE] nenhum emulador configurado (tools/emuladores/)"; exit 2; }
# default_emulator e relativo a ROOT (ex.: tools/emuladores/emulicious/Emulicious.jar).
# Executa-lo do CWD do projeto resolvia para <projeto>/tools/... e sempre falhava.
case "$EMU" in
  /*) ;;
  *) EMU="$ROOT/$EMU" ;;
esac
[ -f "$EMU" ] || { echo "[FAIL_AMBIENTE] emulador nao encontrado: $EMU"; exit 2; }
# Convencao canônica dos gates: jar vive em java; Update=0 suprime o auto-update.
case "$EMU" in
  *.jar) exec java -jar "$EMU" -set Update=0 "$ROM" ;;
  *)     exec "$EMU" "$ROM" ;;
esac
