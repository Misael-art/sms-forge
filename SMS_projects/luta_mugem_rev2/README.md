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

A candidata de trabalho de 03/11 está em
`out/candidates/20261103_operational_baseline_m0`, SHA-256
`6dff700f83e3113c84ea3e6358df0d8b94306465060b37237d78008204cd792f`.
Seu recibo inclui insumos locais em andamento. O SDSC usa a data do build.
`./run.sh` abre manualmente a nominal histórica em `out/rom/`; seu recibo
divergente permanece preservado. Use o [memory bank](doc/10-memory-bank.md)
para os limites medidos e o [handoff](../../doc/continuity/20261024-next-agent.md)
para a seleção atual.
