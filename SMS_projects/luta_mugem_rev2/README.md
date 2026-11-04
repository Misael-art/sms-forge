# luta_mugem_rev2

Consumidor do motor de luta MUGEN → SMS. O manifesto usa Ryu em P1 e Ken8
em P2, apesar dos nomes históricos de alguns slots. O perfil ativo consome
schema 5 de `out/generated/pose_budget_facing_20261027`, com 24 bancos de
dados em uma ROM preenchida até 32 bancos. O perfil exercita a luta diagnóstica
em fundo sólido, sem HUD, FX e PSG da partida completa.

## Compilação e sessão privada

Execute da raiz do SMSForge com o ambiente do [guia de continuidade](../../doc/continuity/20261024-start-here.md).
Escolha um destino novo para cada compilação candidata.

```sh
project="$PWD/SMS_projects/luta_mugem_rev2"
candidate="$project/out/candidates/rebuild_m0"
host=tools/sms_wrapper/run_host.sh
wrapper=tools/sms_wrapper
rtk proxy "$host" python "$wrapper/build_inner.py" --project "$project" --build-dir "$candidate"
rtk proxy "$host" python "$wrapper/reconcile_claims.py" --project "$project" \
  --build-record "$candidate/build_record.json" --current-rom "$candidate/rom/luta_mugem_rev2.sms"
rtk proxy "$host" python "$wrapper/emulator_session.py" isolated start "$candidate/rom/luta_mugem_rev2.sms"
```

A sessão começa pausada. Use o ID retornado para executar o roteiro de input,
capturar o framebuffer e fechar a sessão. Para conciliar evidência de runtime,
passe também `--session ID` com o bundle correspondente. Veja o
[workflow de sessão privada](../../tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md).

A candidata de trabalho de 04/11 está em
`out/candidates/20261104_worst_seal_wrap_m0`, SHA-256
`73cf4ed6405969e34aee5d2caae682b8bbb8f1da9c7f52b5669c0fdee5bb10ba`.
Seu recibo inclui insumos locais em andamento. O SDSC usa a data do build.
`./run.sh` abre manualmente a nominal histórica em `out/rom/`; seu recibo
divergente permanece preservado. Use o [memory bank](doc/10-memory-bank.md)
para os limites medidos e o [handoff](../../doc/continuity/20261024-next-agent.md)
para a seleção atual.

O perfil diagnóstico HitDef pode ser refeito com
`rtk proxy tools/sms_wrapper/run_host.sh python -m mugen2sms.generators.fight_runtime_data --help`.
O CLI requer `--out-dir` novo e publica somente o conjunto completo validado
como schema 7. O manifesto padrão acima seleciona schema 5.

## Diagnóstico de reúso de patterns

A receita abaixo regenera o pacote opcional de CRCs compartilhados. Use
os ZIPs restaurados do rev2 e mantenha o destino histórico preservado.

```sh
generated="$project/out/generated/pair_hash_dedup_20261104"
cfg="$project/doc/continuity/config"
if [ ! -e "$generated" ]; then
  rtk proxy "$host" python -m mugen2sms.generators.versus_scene_cut \
    --p1-source "$project/data/source_mugen/ryu/ryu.zip" --p1-config "$cfg/ryu_pose_budget.json" \
    --p2-source "$project/data/source_mugen/ken/Ken_Majik_.zip" --p2-config "$cfg/ken_pose_budget.json" \
    --out "$generated"
fi
rtk proxy "$host" python "$wrapper/build_inner.py" --project "$project" \
  --manifest "$project/.mddev/candidates/pair_hash_dedup_20261104.json" \
  --build-dir "$project/out/candidates/rebuild_pair_hash_dedup"
```

O manifesto opcional recupera espaço no banco fixo para testar reúso.
O SHA-256 do header `versus_scene_runtime.h` medido é
`ca12e2a2e056c5b2a530cbf329fbba4a0336d9cd0fd7756ce7f3da8919a54133`.
O perfil de trabalho M0 segue separado. Cadência e orçamento do perfil
opcional permanecem reprovados.
