#!/usr/bin/env bash
# B.2b-3b: build do candidato v043 (v040 + quota escalar 5/3 por banda de 16 px).
# Base: main.c.satpolicy_v040. Delta: last_dy/row_n, quota 5/3, sem line_count.
# NAO rodar com sessao de emulador viva. Preserva ROM/map/asm/lst do v043;
# restaura fonte de producao e a ROM canonica 087df676 (o rebuild do dia
# difere apenas no byte de data do SDSC AUTO_DATE; ver relatorio B.2b-3b).
set -u
PROJ=/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2
WS=/mnt/sdcard/Projects/SMSForge
W=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2b
PROD_SRC=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2/main.c.p1c8
PROD_SHA=087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65
CANON="$W/prod_reconstructed_087.sms"
BASE_SRC="$W/main.c.satpolicy_v040"
NEW_SRC="$W/main.c.rowquota_v043"
cd "$PROJ" || exit 2

before=$(sha256sum src/main.c | cut -c1-16)
echo "[build] main.c antes: $before (esperado 042ba22e...)"
if [ "$before" != "042ba22e4a0763da" ]; then
  echo "[build] fonte de producao inesperada — abortando"; exit 2
fi
if [ "$(sha256sum "$BASE_SRC" | cut -d' ' -f1)" != "ddc947a11881c141f50dac446f4167522b82fbc29bd3eaac5ccd8488a84cc669" ]; then
  echo "[build] fonte base v040 inesperada — abortando"; exit 2
fi
if [ ! -f "$NEW_SRC" ]; then
  echo "[build] fonte v043 ausente — abortando"; exit 2
fi
if ! grep -q "last_dy" "$NEW_SRC"; then
  echo "[build] marcador da quota ausente — abortando"; exit 2
fi
if [ "$(sha256sum "$CANON" | cut -d' ' -f1)" != "$PROD_SHA" ]; then
  echo "[build] ROM canonica reconstruida ausente/divergente — abortando"; exit 2
fi
cp "$PROD_SRC" "$W/main.c.b2b3b_v043_before"
cp "$NEW_SRC" src/main.c
echo "[build] fonte v043: $(sha256sum src/main.c | cut -c1-16)"
build_log=$(bash build.sh 2>&1)
build_rc=$?
printf '%s\n' "$build_log" | tail -14
if [ "$build_rc" -ne 0 ] || printf '%s' "$build_log" | grep -q "\[FAIL\]"; then
  echo "[build] BUILD FALHOU (rc=$build_rc) — ROM NAO sera custodiada"
  cp "$PROD_SRC" src/main.c
  cp "$CANON" "$PROJ/out/rom/luta_mugem_rev2.sms"
  echo "[build] producao restaurada: $(sha256sum src/main.c | cut -c1-16) / $(sha256sum out/rom/luta_mugem_rev2.sms | cut -c1-16)"
  exit 5
fi
rom=out/rom/luta_mugem_rev2.sms
if [ ! -f "$rom" ]; then echo "[build] ROM ausente apos build"; exit 4; fi
sha=$(sha256sum "$rom" | cut -d' ' -f1)
addr=$(printf '%s' "$sha" | cut -c1-16)
if [ "$sha" = "7002b0ba44e7d211476c096c511fe45c35184e3c3b815b9b486e09c765191926" ] || \
   [ "$sha" = "b68061ced34c19d1a24bf1c531dc893e136dbe6711a38d89d74c94ddbed9d480" ] || \
   [ "$sha" = "07f4abce922abfeee74824bce0bbeca2369336c11d7b28d634d5923155797fc0" ] || \
   [ "$sha" = "d5f10d043f322d7e2a785e5ca419f1997dbf808c9a7a1d6f23dedd7265ecfcd5" ] || \
   [ "$sha" = "d998209b7f426485380e8584ef14fbda6bb7d4bbec6f7f639476c23c34f8f068" ] || \
   [ "$sha" = "3f3dce97d7afd9c3dd5fadef972e71222c57e877cf52382fdccffaec501f58e9" ] || \
   [ "$sha" = "4431533947b96c8443ca335e198e4e5922445e8cf006f488b87bdd6f85adb00c" ]; then
  echo "[build] ROM igual a candidato anterior — patch nao entrou; restaurando"
  cp "$PROD_SRC" src/main.c; cp "$CANON" "$PROJ/out/rom/luta_mugem_rev2.sms"; exit 6
fi
cp "$rom" "$W/v043_rowquota_${addr}.sms"
cp out/obj/luta_mugem_rev2.map "$W/v043_luta_mugem_rev2_${addr}.map"
cp out/obj/main.asm "$W/v043_main_${addr}.asm"
cp out/obj/main.lst "$W/v043_main_${addr}.lst"
echo "$sha" > "$W/v043_sha.txt"
echo "[build] v043 rom sha256=$sha"
echo "[build] v043 map=$W/v043_luta_mugem_rev2_${addr}.map"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
echo "[build] corredor de sondas..."
python3 "$WS/tools/sms_wrapper/audit_probe_corridor.py" \
  --project "$PROJ" --src "$NEW_SRC" \
  --out "${stamp}_probe_corridor_v043_${addr}.json" 2>&1 | tail -6
corr_rc=${PIPESTATUS[0]}
echo "[build] corredor exit=$corr_rc"
# restaura fonte e ROM canonica; o rebuild do dia e' preservado como prova
# da data AUTO_DATE, nao como producao.
cp "$PROD_SRC" src/main.c
echo "[build] fonte de producao restaurada: $(sha256sum src/main.c | cut -c1-16)"
bash build.sh > "$W/build_prod_restore_v043.log" 2>&1
rebuilt_sha=$(sha256sum "$rom" | cut -d' ' -f1)
cp "$rom" "$W/prod_rebuild_day_${rebuilt_sha:0:8}.sms"
cp "$CANON" "$rom"
prod_sha=$(sha256sum "$rom" | cut -d' ' -f1)
echo "[build] rebuild do dia (SO data SDSC): $rebuilt_sha"
echo "[build] ROM de producao restaurada (canonica): $prod_sha"
if [ "$prod_sha" != "$PROD_SHA" ]; then
  echo "[build] ERRO: ROM de producao divergente da canonica"; exit 7
fi
echo "[build] OK"
