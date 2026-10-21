#!/usr/bin/env bash
# capture_m2_jukebox.sh — evidencia M2 da jukebox: 1 sessao privada isolada,
# botao 1 (mask 16, borda de subida na ROM) avanca title->dawn->storm->eco e
# cada faixa em PSGPlay(loop) e gravada em janela >= duracao+2s de margem.
# Ordem obrigatoria (L062/M1): publish do bundle ANTES do runtime probe —
# measure_runtime_probe escreve em out/evidence/sessions/<id>/runtime e uma
# pasta pre-criada faz publish() reprovar ("session already published").
# SFX: audicao apenas por pre-escuta neste marco; prova de emulador com
# arbitracao sobre a musica e do M3 (declarado, nao omitido).
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"  # capture_evidence sem --project publica em CWD — cair na raiz do
             # workspace foi o defeito real da primeira tomada desta evidência.
W="$PROJ/../../tools/sms_wrapper"
ROM="$PROJ/out/rom/pulso_de_cristal.sms"
ES="$PROJ/out/escuta"; LOG="$PROJ/out/logs"
mkdir -p "$ES" "$LOG"
ROM_SHA=$(sha256sum "$ROM" | cut -d' ' -f1)
echo "[ROM] $ROM sha=$ROM_SHA"

ROOT=$(python3 "$W/emulator_session.py" isolated start "$ROM" | tail -1)
echo "[SESSAO] $ROOT"
cleanup(){ python3 "$W/emulator_session.py" isolated close "$ROOT" || true; }
trap cleanup EXIT

press1(){ # um avanco de faixa: silencia 20f, segura KEY_1 6f, solta 8f
  local f="$LOG/seq_press.json"
  printf '[{"p1":0,"frames":20},{"p1":16,"frames":6},{"p1":0,"frames":8}]' > "$f"
  python3 "$W/emulator_session.py" isolated sequence "$ROOT" "$f" >/dev/null
}

press1
python3 "$W/capture_evidence.py" --session "$ROOT" --rom "$ROM" \
  --out evidence_m2_jukebox --frames 120 | tail -3
python3 "$W/measure_runtime_probe.py" --project "$PROJ" --session "$ROOT" \
  --rom "$ROM" --seconds 8 --janelas 2 --out runtime_probe_m2 | tail -5

for spec in music_title:30 music_dawn:35 music_storm:17 music_eco:32; do
  nome="${spec%%:*}"; seg="${spec##*:}"
  python3 "$W/capture_audio.py" --session "$ROOT" --rom "$ROM" \
    --seconds "$seg" --out "audio_$nome" | tail -1
  cp "$ROOT/audio_$nome.wav" "$ROOT/audio_$nome.audio.json" "$ES/"
  echo "[COPIA] $ES/audio_$nome.{wav,audio.json}"
  case "$nome" in music_eco) : ;; *) press1 ;; esac
done

python3 "$W/emulator_session.py" isolated check-bundle \
  "$PROJ/out/evidence/sessions/$(basename "$ROOT")"
