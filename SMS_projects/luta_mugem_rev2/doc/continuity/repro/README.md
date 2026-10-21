# Repro — `luta_mugem_rev2` (continuidade 2026-10-21)

Este diretório preserva as fontes e receitas dos candidatos do lote B.2b-3b.
Os scripts históricos `build_v041.sh`/`build_v042.sh`/`build_v043.sh` contêm
caminhos absolutos do host antigo (`/mnt/sdcard/...`, `/home/misael/...`); eles
são **registro histórico**, não o caminho recomendado em um host novo.

## Caminho recomendado (host novo)

```sh
cd /path/to/sms-forge
bash SMS_projects/luta_mugem_rev2/doc/continuity/validate_after_reinstall.sh
```

Isso reconstrói produção e v043 a partir do tarball gerado versionado e
canonicaliza contra as ROMs de referência. Não precisa de emulador.

## Fontes preservadas

| Arquivo | Papel | SHA-256 |
|---|---|---|
| `main.c.satpolicy_v040` | v040 — ordem alternada | ver `ASSETS.sha256` |
| `main.c.linecap_v041` | v041 — cap whole-cell | ver `ASSETS.sha256` |
| `main.c.rowquota_v042` | v042 — quota 6+2 | ver `ASSETS.sha256` |
| `main.c.rowquota_v043` | v043 — quota 5+3 | `eb5576ad73e5e79b3ec94a217e13b57faf38a264631ba65aaec3f7642a54cb59` |
| `apply_*.py` | geradores dos patches | ver `ASSETS.sha256` |
| `build_v0*.sh` | builds históricos (caminhos absolutos) | ver `ASSETS.sha256` |
| `run_seal_v043.sh` / `run_pair_v043.sh` | selo/pareamento v043 | ver `ASSETS.sha256` |
| `silhouette_luta.py` | medição §129 | ver `ASSETS.sha256` |
| `read_probes.py` / `render_pose.py` | leitura de sonda/render | ver `ASSETS.sha256` |
| `make_shadow_manifest.py` | shadow SAT | ver `ASSETS.sha256` |

## Gerador MUGEN

```sh
cd /path/to/sms-forge
rm -rf /tmp/ryu_ken_cross_check
PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms versus-cut \
  --p1-source SMS_projects/luta_mugem_rev2/data/source_mugen/ryu/ryu.zip \
  --p1-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ryu_pilot_diag.json \
  --p2-source SMS_projects/luta_mugem_rev2/data/source_mugen/ken/Ken_Majik_.zip \
  --p2-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ken_pilot_diag.json \
  --out /tmp/ryu_ken_cross_check
sha256sum /tmp/ryu_ken_cross_check/versus_scene_runtime.h
# 19edb320606f660a6a13c67933b99a3d5d19e0501acd2995e2250370cac98949
```

Diferença esperada: apenas o caminho do manifesto de saída. O tarball
`doc/continuity/assets/ryu_ken_cross_generated_20261021.tar.gz` já contém o
resultado usado pela build; o gerador serve para auditoria/regeneração.

## Build manual (equivalente ao script)

```sh
PROJ=SMS_projects/luta_mugem_rev2
TMP=$(mktemp -d SMS_projects/_continuity_validate.XXXXXX)
cp -a "$PROJ"/{src,inc,.mddev,build.sh,run.sh,README.md} "$TMP"/
mkdir -p "$TMP"/{out,res}
tar -xzf "$PROJ/doc/continuity/assets/ryu_ken_cross_generated_20261021.tar.gz" -C "$TMP"
( cd "$TMP" && bash build.sh )
python3 "$PROJ/doc/continuity/verify_canonical.py" \
  --built "$TMP/out/rom/luta_mugem_rev2.sms" \
  --canonical "$PROJ/doc/continuity/assets/luta_mugem_rev2_canonical_087df676.sms"

# v043
cp "$PROJ/doc/continuity/repro/main.c.rowquota_v043" "$TMP/src/main.c"
( cd "$TMP" && bash build.sh )
python3 "$PROJ/doc/continuity/verify_canonical.py" \
  --built "$TMP/out/rom/luta_mugem_rev2.sms" \
  --canonical "$PROJ/doc/continuity/assets/candidate_v043_13b78bd2435673df.sms" \
  --expect-sha 13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7
```

O `verify_canonical.py` aceita apenas diferenças em `0x7FE6` (data SDSC) e
`0x7FFA` (checksum SEGA); qualquer outra diferença é FAIL.

## Medição viva (não executada na validação de build)

Os scripts `run_seal_v043.sh`/`run_pair_v043.sh` dependem de sessão de
emulador, display privado, `bridge.jar` e caminhos do host antigo. Antes de
rodar:

1. leia `tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md`;
2. confirme que não há sessão zumbi;
3. use `emulator_session.py` e input scriptado, não foco de janela;
4. grave framebuffer/vídeo 256×192;
5. meça SAT real/linha e §129 no mesmo SHA.

Sem isso, o v043 continua **não promovido** (pacing 5033 < 5745).
