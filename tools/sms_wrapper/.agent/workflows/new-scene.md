# workflow: new-scene

Pipeline obrigatório: `.agent/pipelines/aaa_scene_v1.json`.

Cena inclui qualquer tela com orçamento próprio: menu, abertura, treino,
combate, resultado ou créditos. Só criar telas/cenários listados no GDD; se o
escopo exclui cenário, não inserir um para preencher a composição.

Ordem NÃO negociável:
roteiro → storyboard (grid 8×8) → coreografia → **simulador de sprites** →
orçamento (`scene_budget_v1`) → contrato de asset → model sheet → assets
(gates de recursos/luma/procedência) → runtime (build gate) → evidência.

Identifique no storyboard o beat e o caso do roteiro que esta cena realiza.
Para uma nova família de ações ou transição, use os [ensaios por família](first-playable-slice.md#do-beat-ao-caso-observável)
ao planejar a coreografia e repita esses casos na ROM. Uma família adiada no
primeiro trecho volta ao planejamento quando chegar a sua cena.

Com a [direção visual](../skills/sms-visual-excellence.md) e a bíblia do projeto,
esboce a cena à resolução de jogo no momento em que o jogador precisa decidir.
Posicione o foco, a ação concorrente e um sinal que identifica o lugar.
Reserve no mapa de tiles os contornos que precisam sobreviver à conversão.
Se houver movimento de câmera ou luz, marque uma região ativa e outra estável.
No retorno do jogador, confira as emendas e o HUD durante a ação mais custosa.
Em tela fixa, use a mudança que de fato existe, como seleção e confirmação.

No simulador e no pior quadro, somar todos os atores, HUD, projéteis e efeitos
que aparecem juntos, incluindo a pose de maior largura e os pontos de contato;
um idle isolado não representa a cena completa. Se a tela não usa sprites,
registrar os recursos que de fato coexistem e não inventar um orçamento de ator.

Se esta cena tem entradas/saídas ou compartilha estado com outra, registrar
arestas, input, owners, teardown, persistência e recuperação conforme
`skills/sms-state-transitions.md`; orçar também o pior quadro da troca.

Medir DEPOIS da arte cara é a regressão histórica que este workspace existe
para impedir.
