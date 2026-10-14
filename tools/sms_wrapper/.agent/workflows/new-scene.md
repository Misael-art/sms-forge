# workflow: new-scene

Pipeline obrigatório: `.agent/pipelines/aaa_scene_v1.json`.

Cena inclui qualquer tela com orçamento próprio: menu, abertura, treino,
combate, resultado ou créditos. Só criar telas/cenários listados no GDD; se o
escopo exclui cenário, não inserir um para preencher a composição.

Ordem NÃO negociável:
roteiro → storyboard (grid 8×8) → coreografia → **simulador de sprites** →
orçamento (`scene_budget_v1`) → contrato de asset → model sheet → assets
(gates de recursos/luma/procedência) → runtime (build gate) → evidência.

No simulador e no pior quadro, somar todos os atores, HUD, projéteis e efeitos
que aparecem juntos, incluindo a pose de maior largura e os pontos de contato;
um idle isolado não representa a cena completa. Se a tela não usa sprites,
registrar os recursos que de fato coexistem e não inventar um orçamento de ator.

Se esta cena tem entradas/saídas ou compartilha estado com outra, registrar
arestas, input, owners, teardown, persistência e recuperação conforme
`skills/sms-state-transitions.md`; orçar também o pior quadro da troca.

Medir DEPOIS da arte cara é a regressão histórica que este workspace existe
para impedir.
