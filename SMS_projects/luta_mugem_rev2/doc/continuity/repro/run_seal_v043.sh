#!/usr/bin/env bash
# B.2b-3b: selo de 300 s do candidato v043 (cap de 8/scanline).
# Sessao privada unica, sem DAP na janela; le probes depois do selo, captura
# o framebuffer 256x192 e fecha. Nunca sobrescreve: nome unico por run.
set -u
PROJ=/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2
WS=/mnt/sdcard/Projects/SMSForge
W=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2b
name="${1:-v043_rowquota}"
rom="${2:-$W/v043_rowquota_13b78bd2435673df.sms}"
cd "$PROJ" || exit 2
log="$W/run_${name}.log"
{
  echo "=== $name rom $(sha256sum "$rom" | cut -c1-16) em $(date -u +%FT%TZ)"
  sess_out=$(python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated start "$rom" 2>&1 | tail -1)
  sess=$(basename "$sess_out")
  echo "session $sess (root $sess_out)"
  if ! printf '%s' "$sess" | grep -Eq '^[0-9a-f]{32}$'; then
    echo "[driver] start falhou"; exit 1
  fi
  printf '%s' "$sess" > "$W/session_${name}.txt"
  python3 "$WS/tools/sms_wrapper/measure_worst_frame.py" \
    --project "$PROJ" --session "$sess" --probe-base 0xC800 \
    --wait-seconds 300 --out "worst_frame_${name}"
  echo "[driver] measure exit=$?"
  python3 "$W/read_probes.py" "$sess" --out "$W/probes_${name}.json" > "$W/probes_${name}.log" 2>&1
  echo "[driver] probes exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated capture "$sess" \
    --name "shot_${name}.png" 2>&1 | tail -3
  echo "[driver] capture exit=$?"
  cp "$sess_out/evidence/shot_${name}.png" "$sess_out/evidence/shot_${name}.json" \
     "$W/captures/" 2>&1
  echo "[driver] evidence-copy exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated close "$sess" 2>&1 | tail -2
  echo "[driver] closed $sess"
} >> "$log" 2>&1
echo "[driver] $name: $(tail -1 "$log")"
