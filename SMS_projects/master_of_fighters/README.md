# Master of Fighters

Jogo de luta autoral em desenvolvimento. O manifesto padrão compila o
esqueleto. Os manifestos de viewer são diagnósticos de arte e animação.

## Reproduzir o viewer da provocação de Dr. Social

Execute da raiz do SMSForge com o ambiente do [guia de continuidade](../../doc/continuity/20261024-start-here.md).
Os scripts v2/v3 conferem os JPEGs locais pelos recibos de registro e só
recolocam derivados ausentes após verificar a reprodução. Se faltar um
original, recupere pelo Git o arquivo indicado pela receita.

```sh
project="$PWD/SMS_projects/master_of_fighters"
art="$project/data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1"
host=tools/sms_wrapper/run_host.sh
wrapper=tools/sms_wrapper
rtk proxy "$host" python "$art/register_taunt_cycle_v2.py"
rtk proxy "$host" python "$art/register_taunt_cycle_v3.py"

converted="$project/out/diagnostics/social_taunt01_cycle_v3_20261101/converted"
# Em uma restauração, gere somente se este destino estiver ausente.
rtk proxy "$host" python "$wrapper/prepare_authored_sprite_sample.py" \
  --config "$art/proposals/TA01_cycle_v3_adapter_config.json" --out "$converted"
rtk proxy sha256sum "$converted/sample_data.h"
```

O SHA-256 esperado do header é
`2613029ccaff5ef12ad578988660e42f35950134a7581465ecc11819eabaa008`.
Com o header conferido, escolha um destino novo para o build e abra a sessão.

```sh
candidate="$project/out/candidates/rebuild_social_taunt_v3"
rtk proxy "$host" python "$wrapper/build_inner.py" --project "$project" \
  --manifest "$project/.mddev/dr_social_taunt01_cycle_v3_build.json" --build-dir "$candidate"
rtk proxy "$host" python "$wrapper/emulator_session.py" isolated start "$candidate/rom/master_of_fighters.sms"
```

Use o [workflow de sessão privada](../../tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md)
para input, captura, conciliação pelo recibo e fechamento por ID. `./run.sh`
abre manualmente uma ROM nominal quando ela existe. O viewer v3 histórico está
em `out/candidates/dr_social_taunt01_cycle_v3_src`, SHA-256
`47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`.
Suas medidas cobrem o viewer com Ken de construção. A integração do duelo,
os comandos competitivos e o aceite do pacote Social seguem no
[memory bank](doc/10-memory-bank.md).
