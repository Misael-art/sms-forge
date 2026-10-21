#!/usr/bin/env bash
# capture_m3_arc.sh — evidencia M3 de pulso_de_cristal (doc/17 casos 1–4).
# Rota: sessao privada isolada (workflow emulator-isolated-session), nunca
# foco no desktop nem pkill. ROM pinada por SHA em cada bundle.
# Ordem L062: publish (capture_evidence) ANTES do runtime probe — a pasta
# pre-criada faz publish() reprovar com "session already published".
# Publicar so uma vez por sessao: cada estagio abre a sua.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"                       # capture_evidence sem --project publica em CWD
W="$PROJ/../../tools/sms_wrapper"
ROM="$PROJ/out/rom/pulso_de_cristal.sms"
LOG="$PROJ/out/logs"; VID="$PROJ/out/evidence/m3"; ES="$PROJ/out/escuta"
mkdir -p "$LOG" "$VID" "$ES"
ROM_SHA=$(sha256sum "$ROM" | cut -d' ' -f1)
echo "[ROM] $ROM sha=$ROM_SHA"

SESS=""
STAGES="${STAGES:-ABC}"   # A=arco em atracao, B=jogador+spam, C=arbitracao de audio
start(){ SESS=$(python3 "$W/emulator_session.py" isolated start "$ROM" | tail -1)
         echo "[SESSAO] $SESS"; }
close(){ [ -n "$SESS" ] && python3 "$W/emulator_session.py" isolated close "$SESS" >/dev/null || true
         SESS=""; }
trap close EXIT

# um script de input em frames VDP (nada de sleep): p1=START(16) p2=SELECT(32)
runscript(){ local name="$1" json="$2"
  printf '%s' "$json" > "$LOG/$name.json"
  python3 "$W/emulator_input.py" --session "$SESS" --script "$LOG/$name.json" >/dev/null; }

# corredor: C990 gd_max C991 gd_state C992 gi_max C993 gi_state
#           C994 cnt_fade_dawn C995 cnt_cut_storm C996 cnt_sfx_crystal
readc(){ python3 "$W/emulator_session.py" isolated read "$SESS" 0xC990 7 | tr -d ' \n'; echo; }
read1(){ python3 "$W/emulator_session.py" isolated read "$SESS" "$1" 1 | tr -d ' \n'; echo; }
# valor puro do primeiro byte lido (read imprime JSON pretty-printed)
v1(){ python3 "$W/emulator_session.py" isolated read "$SESS" "$1" 1 \
     | python3 -c 'import sys,json;print(json.load(sys.stdin)["ram"][0])'; }

bundlepath(){ python3 -c "
import sys;sys.path.insert(0,'$W')
from session_bridge.isolated import load
print(load('$SESS')[0])"; }

if [[ "$STAGES" == *A* ]]; then
echo "=== A: arco em atracao (video por frame VDP, 4x900 = 3600 f) ==="
start
for n in a b c d; do
  python3 "$W/emulator_session.py" isolated video "$SESS" --frames 900 --name "m3_arc_$n" \
    | python3 -c "import json,sys; r=json.load(sys.stdin); print('[VIDEO] %s %df distintos=%d hz=%s sha=%s' % (r['path'], r['frames'], r['distinct_frames'], r['playback_hz'], r['sha256'][:12]))"
done
BUNDLE=$(bundlepath)
cp -f "$BUNDLE"/evidence/m3_arc_*.mp4 "$BUNDLE"/evidence/m3_arc_*.json "$VID/"
echo "[CONTADORES A] $(readc)"; echo "[A probe_state] $(read1 0xC9F6)"
close
fi

if [[ "$STAGES" == *E* ]]; then
# caso 1 em duas voltas: o arco tem ~1800 f por ciclo, logo 8x900 = 7200 f
# cobrem 2 voltas completas + entrada da terceira. A prova de "ciclo completo"
# e o contador cnt_fade_dawn (so avancou ao reentrar TITLE e disparar de novo),
# nao o tempo de relogio. Sondas por segmento registram a visita de estados.
SEGMENTS="${SEGMENTS:-8}"
FRAMES_PER="${FRAMES_PER:-900}"
echo "=== E: arco em atracao ${SEGMENTS}x${FRAMES_PER} = $((SEGMENTS * FRAMES_PER)) f (caso 1, duas voltas) ==="
start
for i in $(seq 1 "$SEGMENTS"); do
  python3 "$W/emulator_session.py" isolated video "$SESS" --frames "$FRAMES_PER" --name "m3_arc_e$i" \
    | python3 -c "import json,sys; r=json.load(sys.stdin); print('[VIDEO e%d] %s %df distintos=%d hz=%s sha=%s' % ($i, r['path'], r['frames'], r['distinct_frames'], r['playback_hz'], r['sha256'][:12]))"
  echo "[SONDA e$i] frame+contadores $(readc)"
  echo "[SONDA e$i] state=$(v1 0xC9F6) track=$(v1 0xC9F2) playing=$(v1 0xC9F3) attract=$(v1 0xC9F5)"
  # read pausa a instancia: devolva o run antes de gravar o proximo segmento,
  # senao o video sai congelado e distintos=1.
  python3 "$W/emulator_session.py" isolated run "$SESS" >/dev/null
done
BUNDLE=$(bundlepath)
cp -f "$BUNDLE"/evidence/m3_arc_e*.mp4 "$BUNDLE"/evidence/m3_arc_e*.json "$VID/" 2>/dev/null || true
close
fi

if [[ "$STAGES" == *F* ]]; then
# caso 2, cláusula "Pause em cada ato". A ponte injeta o Pause FISICO do
# console (bit0 de `console` = SMSKEY_PAUSE no ForgeSMS.java), que no SMS é
# NMI — a ROM le via SMS_queryPauseRequested(), não via registro de pad.
# Claim medido por ato: (i) SILENT congela a FSM (probe_state não muda) e
# (ii) não trava o framebuffer (probe_frame continua avançando) e (iii) ao
# soltar, o arco retoma sozinho. `step` é em frames VDP, sem relogio.
ACTS="${ACTS:-0 2 4 6}"
HOLD="${HOLD:-700}"
echo "=== F: matriz de PAUSE por ato ($ACTS; segurar $HOLD f) ==="
start
frame(){ python3 "$W/emulator_session.py" isolated read "$SESS" 0xC9F0 2 \
          | python3 -c 'import sys,json;b=json.load(sys.stdin)["ram"][0:2];print(b[0]|b[1]<<8)'; }
stepn(){ python3 "$W/emulator_session.py" isolated step "$SESS" "$1" >/dev/null; }
runing(){ python3 "$W/emulator_session.py" isolated run "$SESS" >/dev/null; }
pause_edge(){ runscript "f_pause" '[{"console":1,"frames":2},{"console":0,"frames":2}]'; }
# Cada peek congela um instante: 40 sondas de ~1,3 s só entregam ~2,4 mil
# frames de ROM, menos que a volta completa que separa STORM do DAWN. O teto
# largo e o sleep curto existem para a espera caber uma volta inteira.
wait_state(){ local want="$1" limit="${2:-160}" n=0 s
  while [ $n -lt "$limit" ]; do s=$(v1 0xC9F6); runing
    [ "$s" = "$want" ] && { echo "$s"; return 0; }
    n=$((n+1)); sleep 0.4; done
  echo "$s" >&2; return 1; }
for act in $ACTS; do
  got=$(wait_state "$act") || { echo "[F ato=$act] FALHOU ao chegar; observado $got"; continue; }
  f0=$(frame); s0=$(v1 0xC9F6)
  pause_edge
  stepn "$HOLD"
  f1=$(frame); s1=$(v1 0xC9F6); p1=$(v1 0xC9F3)
  pause_edge
  stepn 900
  f2=$(frame); s2=$(v1 0xC9F6)
  echo "[F ato=$act] antes state=$s0 frame=$f0 | em SILENT (${HOLD} f) state=$s1 frame=$f1 playing=$p1 | apos soltar (900 f) state=$s2 frame=$f2"
done
echo "[F contadores] $(readc)"
close
fi

if [[ "$STAGES" == *B* ]]; then
echo "=== B: arco do jogador + testes 2 (spam) + shot + probe de runtime ==="
# mascaras do PORT_A: KEY_1 (START) = 16, KEY_2 (SELECT) = 32 — ambas no p1 da
# ponte. `p2` na ponte e o JOGADOR 2, nao o botao SELECT (erro da tomada 1, que
# deixou a FSM cair em atracao e andar o arco sozinha).
start
runscript b1 '[{"p1":32,"frames":4},{"p1":0,"frames":1560}]'
echo "[B1 toque+prompt em TITLE] $(readc)"; echo "[B1 probe_state] $(read1 0xC9F6)"
runscript b2 '[{"p1":16,"frames":4},{"p1":0,"frames":10}]'
echo "[B2 START na titulo -> FADE_DAWN (cnt_fade_dawn=1)] $(readc)"; echo "[B2 probe_state] $(read1 0xC9F6)"
runscript b3 '[{"p1":16,"frames":2},{"p1":0,"frames":2},{"p1":16,"frames":2},{"p1":0,"frames":2},{"p1":16,"frames":2},{"p1":0,"frames":2},{"p1":16,"frames":2},{"p1":0,"frames":2},{"p1":16,"frames":2},{"p1":0,"frames":2},{"p1":16,"frames":2},{"p1":0,"frames":2}]'
echo "[B3 SPAM de 6 START durante o fade: cnt_fade_dawn continua 1 e state=1] $(readc)"
echo "[B3 probe_state] $(read1 0xC9F6)"
runscript b4 '[{"p1":0,"frames":160},{"p1":32,"frames":4},{"p1":0,"frames":30},{"p1":32,"frames":4},{"p1":0,"frames":30},{"p1":32,"frames":4},{"p1":0,"frames":6}]'
echo "[B4 DAWN + 3 SELECT: cnt_sfx_crystal=3] $(readc)"; echo "[B4 probe_state] $(read1 0xC9F6)"
python3 "$W/capture_evidence.py" --project "$PROJ" --session "$SESS" --rom "$ROM" \
  --frames 60 --out m3_dawn | tail -2
python3 "$W/measure_runtime_probe.py" --project "$PROJ" --session "$SESS" --rom "$ROM" \
  --seconds 8 --janelas 3 --probe-base 0xC900 --out runtime_probe_m3 | tail -6
runscript b5 '[{"p1":16,"frames":4},{"p1":0,"frames":30},{"p1":32,"frames":2},{"p1":0,"frames":2},{"p1":32,"frames":2},{"p1":0,"frames":2},{"p1":32,"frames":2},{"p1":0,"frames":2},{"p1":32,"frames":2},{"p1":0,"frames":2}]'
echo "[B5 START->CUT->STORM + SPAM de SELECT: cnt_sfx_crystal NAO cresce (3)] $(readc)"
echo "[B5 probe_state] $(read1 0xC9F6)"
BUNDLE=$(bundlepath)
python3 "$W/emulator_session.py" isolated check-bundle \
  "$PROJ/out/evidence/sessions/$(basename "$BUNDLE")"
close
fi

if [[ "$STAGES" == *C* ]]; then
echo "=== C: arbitracao SELECT sobre music_dawn (audio isolado) ==="
start
runscript c1 '[{"p1":32,"frames":4},{"p1":0,"frames":1560},{"p1":16,"frames":4},{"p1":0,"frames":170}]'
echo "[C1 em DAWN, music_dawn] $(readc)"; echo "[C1 probe_state] $(read1 0xC9F6)"
BUNDLE=$(bundlepath)
python3 "$W/capture_audio.py" --project "$PROJ" --session "$SESS" --rom "$ROM" \
  --seconds 16 --out audio_m3_dawn_select | tail -2 &
APID=$!
sleep 3
# `input` pausa; sem `run` de volta a ROM fica muda (peak=0 da tomada 1).
for m in 32 0 32 0; do
  python3 "$W/emulator_session.py" isolated input "$SESS" --p1 "$m" >/dev/null
  python3 "$W/emulator_session.py" isolated run "$SESS" >/dev/null
  sleep 2
done
wait $APID
echo "[C2 contadores apos os dois SELECT] $(readc)"
echo "[C2 probe_playing] $(read1 0xC9F3)"
cp -f "$BUNDLE"/audio_m3_dawn_select.wav "$BUNDLE"/audio_m3_dawn_select.audio.json "$ES/"
python3 "$W/audit_audio.py" --wav "$ES/audio_m3_dawn_select.wav" 2>&1 | tail -4
close
fi

echo "[FIM] ROM sha=$ROM_SHA"
