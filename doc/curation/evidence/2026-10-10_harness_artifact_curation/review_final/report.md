# Revisão independente focada — precisa de correções

4 selfchecks passaram. Adversariais encontraram4bugs concretos e3lacunas de contrato/política. Nenhum arquivo do projeto alterado; nenhum fullselftest/emulador executado.

## Bugs concretos

- **R1/P1:** duas locations apontando ao mesmo diretório via symlink passam; comparação de roots é lexical.
- **R2/P1:** arquivo pode sair do destino do kind via symlink interno ao projeto e passar; contenção do arquivo é lexical.
- **R3/P1:** dois artifacts podem possuir o mesmo inode via hardlinks; ownership usa só path.resolve.
- **R4/P2:** tasks={} /False/0/'' e id=0/False/[]/{} viram defaults e planos válidos.

Correções necessárias em results.json. Reproduza os bugs na versão congelada com:

```sh
rtk proxy python3 /tmp/smsforge-curation-coverage-20261010/review/reproduce.py
```

Para o reteste do código atual, acrescentar `--live` executando no workspace.

## Lacunas que precisam de regra explícita

1. legacy_inventory pode cadastrar qualquer arquivo managed como histórico e contornar scan; não há baseline congelada que diferencie adoção histórica de produção nova.
2. lineage mede ciclo/parent existente, mas aceita revision2 sem parent; não mede completude da derivação.
3. reserva registry só cobre kind visual_production; runtime_production pode escrever em source_art sem reserva. Classificação declarada não é enforcement universal da árvore.

## Pontos aprovados dentro do escopo

- audit_learning_capture audit_routes rejeita entriesNone/int/pathlist e exige SHA/caminho canônico; não foi achado bypass concreto na alteração. Ele declara corretamente não medir qualidade didática.
- audit_source_raster selfcheck35negativos passou; APNG foi rejeitado, saída symlink/hardlink não sobrescreveu input. Um slot em branco passa porque gate mede slots declarados, não reconhece poses: limite corretamente documentado.
- Aprovação de artifact é consistência owner/hash/role, não autenticação de ator: não foi tratada como falha a possibilidade de um emissor declarar owner em JSON.

Todos os casos e SHA dos quatro tools em results.json; cópias congeladas junto ao relatório. Evidências raster em raster_results.json.

## Reteste e achados adicionais

R1/R2/R4 corrigidos no reteste live; linhagem de revisão e checagem de output visual independente de kind também reforçadas. R3/hardlinks ainda aberto no último read.

- **R5/P1:** adapter sms_animation_source_lineage_v1 ignora character_id: registro hero aceita lineage de terry (legacy_adapter.json). Controle com fonte e lineage reais dr_social PASS, preservado em actual_legacy_control.json.
- **R6/P1:** audit_routes aceita skills/fake.md como symlink para rules/SMS_GLOBAL.md; SHA válido contorna requisito de aplicação fora da lei (routes_symlink_authority.json). Conferir destinoresolvido dentro de skills/workflows.

Legacy_inventory foi confirmado como exceção explícita de adoção histórica; esta revisão não exige autenticação temporal dessa declaração. A limitação deve permanecer visível.
