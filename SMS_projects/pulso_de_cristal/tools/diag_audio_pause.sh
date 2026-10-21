#!/usr/bin/env bash
# diag_audio_pause.sh — diagnostico de uma pergunta: o ciclo pause/run da ponte
# mata o stream de musica no capturador de audio, sem matar o de SFX?
# Nao e evidencia de milestone: e sonda de ferramenta. Duas janelas de 5 s na
# mesma sessao, sem nenhum botao entre elas (o estado da FSM avanca sozinho em
# atracao; `state antes` de cada janela registra onde ela caiu):
#   J1 sem interleaving -> baseline (M2 mediu 94-100% ativo em title/dawn/storm)
#   J2 com um pause+run no meio -> se a musica sumir depois do `run`, o defeito
#      e o ciclo pause/run, nao o botao.
# Contadores do corredor (0xC990..) separam "ROM muda" de "host mudo":
# probe_playing em 0xC9F3 diz se o stream da ROM esta vivo na janela.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"
W="$PROJ/../../tools/sms_wrapper"
ROM="$PROJ/out/rom/pulso_de_cristal.sms"
LOG="$PROJ/out/logs"; ES="$PROJ/out/escuta"
mkdir -p "$LOG" "$ES"
SESS=""
start(){ SESS=$(python3 "$W/emulator_session.py" isolated start "$ROM" | tail -1)
         echo "[SESSAO] $SESS"; }
close(){ [ -n "$SESS" ] && python3 "$W/emulator_session.py" isolated close "$SESS" >/dev/null || true
         SESS=""; }
trap close EXIT
read1(){ python3 "$W/emulator_session.py" isolated read "$SESS" "$1" 1 \
         | python3 -c "import json,sys; print(json.load(sys.stdin)['ram'][0])"; }
bundle(){ python3 -c "
import sys;sys.path.insert(0,'$W')
from session_bridge.isolated import load
print(load('$SESS')[0])"; }

start
B=$(bundle)

echo "=== J1: 5 s SEM interleaving ==="
echo "[J1 state antes] $(read1 0xC9F6)"
python3 "$W/capture_audio.py" --project "$PROJ" --session "$SESS" --rom "$ROM" \
  --seconds 5 --out diag_j1_sem_pause | tail -1
cp -f "$B"/diag_j1_sem_pause.wav "$ES/"
python3 "$W/audit_audio.py" --wav "$ES/diag_j1_sem_pause.wav" 2>&1 | tail -2

echo "=== J2: 5 s com um pause+run no meio (nenhum botao) ==="
echo "[J2 state antes] $(read1 0xC9F6)"
python3 "$W/capture_audio.py" --project "$PROJ" --session "$SESS" --rom "$ROM" \
  --seconds 5 --out diag_j2_pause_run | tail -1 &
APID=$!
sleep 3
python3 "$W/emulator_session.py" isolated pause "$SESS" >/dev/null
sleep 1
python3 "$W/emulator_session.py" isolated run   "$SESS" >/dev/null
wait $APID
cp -f "$B"/diag_j2_pause_run.wav "$ES/"
python3 "$W/audit_audio.py" --wav "$ES/diag_j2_pause_run.wav" 2>&1 | tail -2
echo "[probe_playing apos J2] $(read1 0xC9F3)"

echo "=== perfil de pico por janela de 0,5 s (J1 vs J2) ==="
python3 - "$ES/diag_j1_sem_pause.wav" "$ES/diag_j2_pause_run.wav" <<'EOF'
import sys, wave, array
for p in sys.argv[1:]:
    w = wave.open(p); a = array.array('h'); a.frombytes(w.readframes(w.getnframes()))
    win = 44100 // 2
    hs = [max((abs(x) for x in a[i:i+win]), default=0) for i in range(0, len(a), win)]
    print(p.split('/')[-1], " ".join(str(h) for h in hs))
EOF
close
