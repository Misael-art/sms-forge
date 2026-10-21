#!/usr/bin/env bash
# B.2b-3b: build do candidato v041 (v040 + cap de 8 sprites por scanline).
# Base: main.c.satpolicy_v040. Delta: line_count[192], clear por frame,
# emissao so se todas as linhas visiveis tiverem < 8 entradas.
# NAO rodar com sessao de emulador viva. Preserva ROM/map/asm/lst do v041;
# restaura fonte E ROM de producao ao final (087df676 canonica).
set -u
PROJ=/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2
WS=/mnt/sdcard/Projects/SMSForge
W=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2b
PROD_SRC=/home/misael/.cache/phasezero/agent-tmp/opencode/loteB2/main.c.p1c8
PROD_SHA=087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65
BASE_SRC="$W/main.c.satpolicy_v040"
NEW_SRC="$W/main.c.linecap_v041"
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
  echo "[build] fonte v041 ausente — abortando"; exit 2
fi
if ! grep -q "line_count\[192\]" "$NEW_SRC"; then
  echo "[build] marcador do cap ausente — abortando"; exit 2
fi
cp "$PROD_SRC" "$W/main.c.b2b3b_v041_before"
cp "$NEW_SRC" src/main.c
echo "[build] fonte v041: $(sha256sum src/main.c | cut -c1-16)"
build_log=$(bash build.sh 2>&1)
build_rc=$?
printf '%s\n' "$build_log" | tail -14
if [ "$build_rc" -ne 0 ] || printf '%s' "$build_log" | grep -q "\[FAIL\]"; then
  echo "[build] BUILD FALHOU (rc=$build_rc) — ROM NAO sera custodiada"
  cp "$PROD_SRC" src/main.c
  bash build.sh >/dev/null 2>&1
  echo "[build] producao restaurada: $(sha256sum src/main.c | cut -c1-16)"
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
   [ "$sha" = "d998209b7f426485380e8584ef14fbda6bb7d4bbec6f7f639476c23c34f8f068" ]; then
  echo "[build] ROM igual a candidato anterior — patch nao entrou; restaurando"
  cp "$PROD_SRC" src/main.c; bash build.sh >/dev/null 2>&1; exit 6
fi
cp "$rom" "$W/v041_linecap_${addr}.sms"
cp out/obj/luta_mugem_rev2.map "$W/v041_luta_mugem_rev2_${addr}.map"
cp out/obj/main.asm "$W/v041_main_${addr}.asm"
cp out/obj/main.lst "$W/v041_main_${addr}.lst"
echo "$sha" > "$W/v041_sha.txt"
echo "[build] v041 rom sha256=$sha"
echo "[build] v041 map=$W/v041_luta_mugem_rev2_${addr}.map"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
echo "[build] corredor de sondas..."
python3 "$WS/tools/sms_wrapper/audit_probe_corridor.py" \
  --project "$PROJ" --src "$NEW_SRC" \
  --out "${stamp}_probe_corridor_v041_${addr}.json" 2>&1 | tail -6
corr_rc=${PIPESTATUS[0]}
echo "[build] corredor exit=$corr_rc"
# restaura fonte e ROM de producao
cp "$PROD_SRC" src/main.c
echo "[build] fonte de producao restaurada: $(sha256sum src/main.c | cut -c1-16)"
bash build.sh > "$W/build_prod_restore_v041.log" 2>&1
prod_sha=$(sha256sum "$rom" | cut -d' ' -f1)
echo "[build] ROM de producao restaurada: $prod_sha"
if [ "$prod_sha" != "$PROD_SHA" ]; then
  echo "[build] ERRO: ROM de producao divergente da canonica"; exit 7
fi
echo "[build] OK"
