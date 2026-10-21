# Parecer final da revisão independente focada

**PASS no escopo focado.** Os6bugs concretos encontrados foram corrigidos e retestados com21casos persistidos, incluindo positivos e controle com fonte/lineage reais das61poses do Dr.Social.

- R1: locations aliased por symlink rejeitadas.
- R2: arquivo fora do destino resolvido de seu kind rejeitado.
- R3: ownership duplicado via hardlink rejeitado.
- R4: tasks/IDs explícitos de tipos inválidos rejeitados.
- R5: adapter de aprovação original confere character_id, kind/status, sourcepath/SHA e cópia literal de approval_scope; mutações rejeitadas.
- R6: skill alias para SMS_GLOBAL rejeitada; destino deve ser skill/workflow real.

Os4selfchecks atuais passaram. Raster adicional: APNG rejeitado, outputs symlink/hardlink não alteram inputs; slot em branco é permitido apenas como slot declarado, sem reconhecimento de pose.

A exceção QA screenshot em out é preservada; source_art permanece protegida mesmo sob taskkind QA. Legacy_inventory é adoção explicitamente não classificada/não aprovada; gate estrutural não autentica data ou ator.

Reprodução:

```sh
rtk proxy python3 /tmp/smsforge-curation-coverage-20261010/review/regression_six.py --root /mnt/sdcard/Projects/SMSForge --output /tmp/reteste-curadoria.json
```

SHA dos tools,21resultados,controle real e limites em final_regression.json;4selfchecks em final_selfchecks.json. Relatórios anteriores preservam falhas históricas. Nenhum arquivo do projeto foi alterado por este revisor. Nenhum emulador ou suíte integral executado; não é aprovação gráfica, de gameplay ou produção.
