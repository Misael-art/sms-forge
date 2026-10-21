#!/usr/bin/env bash
# m3_audio_windows.sh — janelas de áudio na SESSÃO PRIVADA, com o ESTADO
# verificado por sonda antes de afirmar qualquer coisa sobre o que se ouviu.
#
# porque assim: a primeira rodada (2026-10-14) mediu "DAWN" que nunca existiu —
# o START antes do prompt envenena o attract (input_step: touched=1) e a ROM
# fica em ST_TITLE até o loop point (LOOP_TITLE=1536). Sem ler probe_state a
# métrica de áudio prova apenas "alguma música tocou".
#
# Nunca pkill/encerra emulador alheio; cada estágio abre e fecha a sua sessão.
# Necessita: python3 com numpy.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"
W="$PROJ/../../tools/sms_wrapper"
ROM="$PROJ/out/rom/pulso_de_cristal.sms"
LOG="$PROJ/out/logs"; ES="$PROJ/out/escuta"
mkdir -p "$LOG" "$ES"
WAVS="${WAVS:-W1 W2 W3}"
# seleção EXATA por token: `*W3*` casava com "W3B" e rodava os dois
LIST=",$(echo "$WAVS" | tr -s " " ","),"
has(){ [[ "$LIST" == *",$1,"* ]]; }

# ── helpers ────────────────────────────────────────────────────────────────
measure(){ python3 - "$1" "${2:-0}" <<'PY'
import sys, wave, numpy as np
w=wave.open(sys.argv[1]); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
skip=int(int(sys.argv[2])*sr); a=a[skip:] if skip < a.size else a[-sr:]
print(f"{sys.argv[1]}: samples={a.size} peak={int(np.abs(a).max())} "
      f"ativos={100*int((np.abs(a)>50).sum())/max(a.size,1):.1f}% "
      f"rms={float(np.sqrt((a.astype(float)**2).mean())):.1f}")
PY
}

SESS=""
start(){ SESS=$(python3 "$W/emulator_session.py" isolated start "$1" | tail -1); echo "[SESSAO] $SESS"; }
close(){ [ -n "$SESS" ] && python3 "$W/emulator_session.py" isolated close "$SESS" >/dev/null || true; SESS=""; }
trap close EXIT

# byte absoluto da RAM da sessão (read pausa; sempre volta a rodar depois)
peek(){ python3 "$W/emulator_session.py" isolated read "$SESS" "$1" 1 2>/dev/null \
        | python3 -c 'import sys,json;print(json.load(sys.stdin)["ram"][0])'; }
resume(){ python3 "$W/emulator_session.py" isolated run "$SESS" >/dev/null; }
# roteiro frame-atômico da ponte (a autoridade de tempo é o frame VDP, não a parede)
runscript(){ printf '%s' "$2" > "$LOG/$1.json"
             python3 "$W/emulator_input.py" --session "$SESS" --script "$LOG/$1.json" >/dev/null; }
hold(){ python3 "$W/emulator_session.py" isolated input "$SESS" --p1 "$1" >/dev/null; resume; }
# probe_frame é unsigned int em 0xC9F0: a palavra, não o byte baixo
framew(){ python3 "$W/emulator_session.py" isolated read "$SESS" 0xC9F0 2 2>/dev/null \
        | python3 -c 'import sys,json;b=json.load(sys.stdin)["ram"][0:2];print(b[0]|b[1]<<8)'; }
state(){ peek 0xC9F6; }   # 0 TITLE 1 FADE_DAWN 2 DAWN 3 CUT_STORM 4 STORM ...

# espera um estado sem input: em atração a ROM avança sozinha (t>=300 título,
# DAWN dura 480 f), e cada peek congela o orçamento — pausar NÃO gasta a cena.
wait_state(){ local want="$1" limit="${2:-30}" n=0 s
  while [ $n -lt "$limit" ]; do
    s=$(state); resume
    [ "$s" = "$want" ] && { echo "[estado=$s OK]"; return 0; }
    n=$((n+1)); sleep 1
  done
  echo "[FALHOU] estado esperado $want, observado $s após ${limit} sondas"; return 1; }

# publica nos DOIS destinos: out/escuta = cabine de escuta humana; out/evidence =
# ultimo lugar que reconcile_claims._audio_supported aceita para o eixo de audio
# (.wav POSTERIOR a ROM com peak>0). cp -p preserva a data em que a janela nasceu
# em vez de fingir que foi gravada agora.
grab(){ local n="$1"; local d="/tmp/smsforge-1000/$(basename "$SESS")"
        [ -d "$d" ] || d="$PROJ/out/evidence/sessions/$(basename "$SESS")"
        cp -p "$d/$n.wav" "$d/$n.audio.json" "$ES/" 2>/dev/null || true
        cp -p "$d/$n.wav" "$d/$n.audio.json" "$PROJ/out/evidence/" 2>/dev/null || true; }
capw(){ python3 "$W/capture_audio.py" --project "$PROJ" --session "$SESS" --rom "$1" --seconds "$2" --out "$3"; }

BASE="M2 selado na MESMA rota: title 64,6%/rms 763 · dawn 66,1%/759 · storm 79,3%/1413 · eco 52,7%/256"

if has W1; then
  echo "=== W1: atração (music_title) desde o boot — piano-forte inclusive ==="
  echo "[baseline] $BASE"
  start "$ROM"; sleep 6
  [ "$(state)" = 0 ] || echo "[aviso] W1 não está em TITLE"
  capw "$ROM" 12 w1_attract_continuous | tail -2; grab w1_attract_continuous
  measure "$ES/w1_attract_continuous.wav" 0
  measure "$ES/w1_attract_continuous.wav" 3    # janelas: swell 0–3 f de rampa
  measure "$ES/w1_attract_continuous.wav" 6
  close
fi

if has W2; then
  echo "=== W2: DAWN comprovada por sonda, música contínua, sem input no meio ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  echo "[entrada] state=$(state) track=$(peek 0xC9F2) playing=$(peek 0xC9F3)"
  capw "$ROM" 4 w2_dawn_continuous | tail -2; grab w2_dawn_continuous
  echo "[saída]   state=$(state) track=$(peek 0xC9F2) playing=$(peek 0xC9F3)"
  measure "$ES/w2_dawn_continuous.wav" 0
  close
fi

if has W3; then
  echo "=== W3: caso 4 — SELECT dispara sfx_crystal SOBRE music_dawn (canal 1) ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  c0=$(peek 0xC996); resume
  capw "$ROM" 4 w3_dawn_select >"$LOG/w3_capture.log" 2>&1 &
  APID=$!; sleep 1
  hold 32; sleep 1; hold 0; sleep 1
  hold 32; sleep 1; hold 0
  echo "[agenda] press1≈1s press2≈3s (relativo ao start da captura)"
  wait $APID || true
  tail -2 "$LOG/w3_capture.log"
  grab w3_dawn_select
  measure "$ES/w3_dawn_select.wav" 0
  c1=$(peek 0xC996); resume
  echo "[cnt_sfx_crystal] antes=$c0 depois=$c1 (esperado delta=2; fora de DAWN deve ser 0 — L041)"
  echo "[estado] state=$(state)"
  close
fi
if has W3B; then
  echo "=== W3B: controle do caso 4 — MESMA janela de DAWN, mesmos tempos, ZERO presses ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  capw "$ROM" 4 w3b_dawn_control >"$LOG/w3b_capture.log" 2>&1 &
  APID=$!; sleep 1
  hold 0; sleep 1; hold 0; sleep 1; hold 0; sleep 1
  wait $APID || true
  tail -2 "$LOG/w3b_capture.log"
  grab w3b_dawn_control
  measure "$ES/w3b_dawn_control.wav" 0
  echo "[cnt_sfx_crystal] $(peek 0xC996) (controle: esperado 0)"
  close
fi
if has W4; then
  # W4/W4B são o mesmo roteiro em FRAMES (não em segundos de parede): a única
  # diferença entre as duas corridas é o bit de SELECT. Com presses por
  # `input`+`run` interleavados a fase da música variava entre corridas e o
  # delta não se resumia ao SFX (visto 2026-10-14: 8 transientes para 2 presses).
  echo "=== W4: mix — SELECT em f60 e f164 (script frame-atômico) ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  c0=$(peek 0xC996); resume
  capw "$ROM" 4 w4_dawn_mix >"$LOG/w4_capture.log" 2>&1 &
  APID=$!
  runscript w4 '[{"p1":0,"frames":60},{"p1":32,"frames":4},{"p1":0,"frames":100},{"p1":32,"frames":4},{"p1":0,"frames":72}]'
  wait $APID || true
  tail -2 "$LOG/w4_capture.log"; grab w4_dawn_mix
  measure "$ES/w4_dawn_mix.wav" 0
  c1=$(peek 0xC996); resume
  echo "[cnt_sfx_crystal] antes=$c0 depois=$c1"; echo "[estado] state=$(state)"
  close
fi

if has W4B; then
  echo "=== W4B: controle — MESMO roteiro de frames, SELECT sempre 0 ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  capw "$ROM" 4 w4b_dawn_control >"$LOG/w4b_capture.log" 2>&1 &
  APID=$!
  runscript w4b '[{"p1":0,"frames":60},{"p1":0,"frames":4},{"p1":0,"frames":100},{"p1":0,"frames":4},{"p1":0,"frames":72}]'
  wait $APID || true
  tail -2 "$LOG/w4b_capture.log"; grab w4b_dawn_control
  measure "$ES/w4b_dawn_control.wav" 0
  echo "[cnt_sfx_crystal] $(peek 0xC996) (controle: esperado 0)"
  close
fi
if has W5; then
  # O Pause é tecla FÍSICA do console (bit0 de `console` = SMSKEY_PAUSE), não
  # botão de pad: a ROM o pega por NMI em SMS_queryPauseRequested(). O edge é
  # dado ANTES da janela de captura para que a própria captura não tenha input
  # nenhum — senão o silêncio do `input`/`run` (a armadilha de W3) se confunde
  # com o silêncio pedido.
  echo "=== W5: DAWN em SILENT (Pause acionado antes da janela, zero input dentro) ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  runscript w5_on '[{"console":1,"frames":2},{"console":0,"frames":2}]'
  echo "[SILENT] state=$(state) frame=$(framew) playing=$(peek 0xC9F3)"
  f0=$(framew); resume
  # capw devolve exit!=0 em silêncio adiantado: aqui o silêncio É o claim, não
  # um defeito do host. O par de probe_frame abaixo separa as duas coisas.
  capw "$ROM" 4 w5_dawn_silent >"$LOG/w5_capture.log" 2>&1 || true
  tail -2 "$LOG/w5_capture.log"
  f1=$(framew); resume
  grab w5_dawn_silent
  measure "$ES/w5_dawn_silent.wav" 0
  echo "[núcleo vivo] probe_frame $f0 -> $f1 (delta=$((f1 - f0)) f): a ROM rodou e mesmo assim saiu silêncio = silêncio autoral, não emulador congelado"
  echo "[saída SILENT] state=$(state)"
  close
fi
if has W6; then
  echo "=== W6: reprise — solta o Pause e a MESMA faixa continua (zero input na janela) ==="
  start "$ROM"
  wait_state 0 6 || true
  wait_state 2 40
  runscript w6_on '[{"console":1,"frames":2},{"console":0,"frames":2}]'
  runscript w6_off '[{"console":1,"frames":2},{"console":0,"frames":240}]'
  echo "[reprise] state=$(state) track=$(peek 0xC9F2) playing=$(peek 0xC9F3) frame=$(framew)"
  capw "$ROM" 4 w6_dawn_reprise >"$LOG/w6_capture.log" 2>&1 || true
  tail -2 "$LOG/w6_capture.log"
  grab w6_dawn_reprise
  measure "$ES/w6_dawn_reprise.wav" 0
  close
fi

echo "[FIM]"
