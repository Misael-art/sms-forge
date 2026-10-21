# Revisão independente de fechamento — final2

**PASS no escopo focado atual.**

- 21casos de regressão das6falhas anteriores passaram.
- 29casos focados no delta passaram: substituição/derivação, reserva PNG/XLSX/ODS por tipo de tarefa, contrato de diretório QA e exclusão de snapshot histórico.
- 5selfchecks atuais passaram; regressões symlink/hardlink/identity/routealias estão no código permanente.
- Registry real foi auditado com hashes e scan managed:9registros,11arquivos classificados e737arquivos legados, total748indexados. Legacy continua não classificado/não aprovado.

`parents` representa derivação real; `supersedes` aceita substituição por revisão anterior da mesma chave sem inventar parentalidade. Supersedes ausente/inexistente/próprio/outra-chave é reprovado nos casos medidos. Declaração de aprovação da fonte61poses preserva character_id, SHA e approval_scope literal, sem autenticar ator ou converter esse aceite em aprovação de produção.

O reteste encontrou e confirmou a correção de um bypass no delta hardware: skill ativa symlink para snapshot errado não pode sumir da auditoria. Agora só o caminho lógico do arquivo arquivado é excluído; assertiva errada ativa e alias ativo são reprovados.

Reserva de qualquer extensão visual/planilha é exigida independentemente do tipo de tarefa. O diretório genérico QA continua usando seu contrato próprio; não foi criada árvore duplicada de screenshots para escapar do gate.

Todos os hashes dos5tools e artefatos em final2_report.json; evidências em final2_delta.json, final2_six_regression.json e final2_selfchecks.json. Regressão reproduzível em regression_six_final2.py. Relatórios anteriores preservados.

Nenhum arquivo do projeto alterado pelo revisor. Nenhuma suíte integral ou emulador executado. Este parecer não aprova gameplay, arte, capacidade de hardware ou entrega do jogo.
