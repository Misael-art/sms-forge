#!/usr/bin/env bash
# B.2b-3b: dois quadros consecutivos da politica alternada (v043).
# start -> step 900 (VDP frame 1020) -> capture + probes -> step 1
#       -> capture + probes (VDP frame 1021) -> close.
# Sessao privada unica; sem DAP na janela; nao sobrescreve capturas.
set -u
PROJ=/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2
WS=/mnt/sdcard/Projects/SMSForge
W=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2b
name="${1:-v043_pair}"
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
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated step "$sess" 900 2>&1 | tail -2
  echo "[driver] step900 exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated capture "$sess" \
    --name "shot_${name}_f1020.png" 2>&1 | tail -3
  echo "[driver] capture1020 exit=$?"
  python3 "$W/read_probes.py" "$sess" --out "$W/probes_${name}_f1020.json" > "$W/probes_${name}_f1020.log" 2>&1
  echo "[driver] probes1020 exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated step "$sess" 1 2>&1 | tail -2
  echo "[driver] step1 exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated capture "$sess" \
    --name "shot_${name}_f1021.png" 2>&1 | tail -3
  echo "[driver] capture1021 exit=$?"
  python3 "$W/read_probes.py" "$sess" --out "$W/probes_${name}_f1021.json" > "$W/probes_${name}_f1021.log" 2>&1
  echo "[driver] probes1021 exit=$?"
  cp "$sess_out/evidence/shot_${name}_f1020.png" "$sess_out/evidence/shot_${name}_f1020.json" \
     "$sess_out/evidence/shot_${name}_f1021.png" "$sess_out/evidence/shot_${name}_f1021.json" "$W/captures/" 2>&1
  echo "[driver] evidence-copy exit=$?"
  python3 "$WS/tools/sms_wrapper/capture_video.py" --session "$sess" --ticks 600 \
    --out "video_${name}" > "$W/video_${name}.json" 2> "$W/video_${name}.log"
  echo "[driver] video exit=$?"
  cp "$sess_out/evidence/video_${name}.mp4" "$sess_out/evidence/video_${name}.json" "$W/captures/" 2>&1
  echo "[driver] video-copy exit=$?"
  python3 "$WS/tools/sms_wrapper/emulator_session.py" isolated close "$sess" 2>&1 | tail -2
  echo "[driver] closed $sess"
} >> "$log" 2>&1
echo "[driver] $name: $(tail -1 "$log")"
