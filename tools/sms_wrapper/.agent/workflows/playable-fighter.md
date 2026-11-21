# Produzir um lutador do concept ao duelo jogável

**Unidade de trabalho:** um personagem, um oponente de referência, uma ação
distintiva e uma resposta jogável, dentro de uma cena autorizada. Ao fim do
piloto, ampliar por família de ações até cobrir os estados e confrontos do GDD.
O [ciclo de arte até ROM](artwork-to-rom-lifecycle.md) continua sendo a fonte
dos estados de promoção, aprovações e papéis de arte.

## Entrada que o próximo agente deve resolver

Leia memória, GDD, spec da cena e TDD do consumidor. No registro de arte
localize os heads de identidade, escala, pixel e timing com decisão e hash.
Classifique material congelado, rejeitado, experimental ou aceito no seu
recorte. Escolha o primeiro elo sem prova na ação pedida. Para um personagem
novo, comece no brief. Para um retomado, use o último controle aceito.

Preencha este bloco **no contrato, registro ou handoff que já é dono da
informação**, por referência quando o dado já existir:

```text
Personagem / oponente / cena / ação / versão do GDD:
Lore que deve aparecer no gesto / função tática / resposta que o rival terá:
Model sheet e controle aceitos (papel, caminho, SHA e decisão):
Régua do elenco / altura anatômica / equipamento / materiais / exceção de estilo:
Estados de origem, destino e interrupção / comando autorizado / faces:
IDs de poses / relógio / exposição / trajetórias da raiz, pés, mão e objeto:
Fase ativa proposta / contato previsto / vulnerabilidade / vantagem esperada:
Orçamento da composição do par / pico previsto / pior caso a medir:
Hipótese em teste / condição de reprovação / artefato que decidirá:
```

O TDD possui lógica e relógios. O contrato de animação possui IDs, exposições
e trilhas. O registro de arte possui versões e decisões. O relatório de
sessão possui observações do binário. O handoff aponta para esses owners.

## Ordem de execução e destinos das falhas

| Etapa | Trabalho do agente e saída inspecionável | Para seguir ou corrigir |
|---|---|---|
| 1. Cena e regras | No roteiro e storyboard, colocar os dois corpos, chão, HUD, câmera e distância da ameaça. Explicitar o que o jogador quer, como aciona, o que vê e como o rival responde. Fazer coreografia barata e medir a composição mais larga com os dois atores antes do contrato de asset. | Se o rival some atrás da arma ou o golpe depende de um comando indisponível, voltar à coreografia/design. Registrar o limite do próximo degrau medido. |
| 2. Concept e elenco | Produzir ou selecionar o sheet segundo `original-artwork.md`. Usar a régua e a ficha de [direção de lutador](../skills/sms-fighter-direction.md). Mostrar o par no mesmo chão, verificar escala corporal, rosto, arma e materiais e obter revisão no hash correto. | Proporção divergente volta ao desenho/escala. Mudança de identidade volta ao GDD e à direção visual. Preservar assimetria aprovada entre biotipos. |
| 3. Ação em rascunho | Registrar a sequência no contrato existente. Desenhar poses-chave, passagens necessárias e retorno. Traçar apoios, trajetória de raiz, mão, arma e efeito. Reproduzir os desenhos com as exposições propostas, sem pintura final. Incluir saída de locomoção e retorno ao controle. | Se o impacto depende só da arma ou a leitura desaparece em 1×, corrigir a chave ou o espaçamento. Se o desenho funciona e o gesto demora, variar apenas as exposições e comparar com o controle. |
| 4. Aprovação temporal e pixel | Reproduzir a velocidade normal e lenta, rever a emenda, comparar com o sheet e o par. Finalizar clusters, luz, contorno e recorte na fonte autoral. Fazer a prova técnica de idle+ação, depois converter a fonte completa aprovada na ordem e paleta do contrato. | Registrar versão de arte **e** timing, preview e decisão. Se faltou percepção contínua, registrar `needs_evidence`. Erro de conversão volta à receita de conversão; a fonte aprovada segue como controle. |
| 5. Composição no SMS | Emitir tiles/metasprites e mapa de paleta. Medir linha crítica, SAT total, poses atual e seguinte, coexistência P1/P2, HUD, PNT e bytes a transferir antes da troca. Testar a pose extrema nos dois lados. | Usar `audit_sprite_line_sim.py`, `measure_vram_map.py` e a cena mais cara. O VDP admite 8 sprites por linha e 64 na SAT. Se houver excesso, localizar ator/linha/pose, reprojetar e repetir também a revisão visual. |
| 6. Runtime diagnóstico | Implementar no owner oficial do consumidor o vínculo estado→ação→elemento→pose residente→pose apresentada. Manter os pontos de origem e de colisão no mesmo sistema de coordenadas. Reservar o build candidato; vincular fonte e símbolo ao SHA da ROM. | Em sessão privada, ler input consumido, transição, pose, boxes e estado do defensor. Cruzar com framebuffer nas fronteiras e vídeo em execução. Se a lógica avançar e o desenho ficar velho, investigar upload, residência, seleção de face e publicação no VBlank. |
| 7. Duelo e equilíbrio | No par real, verificar alcance, bloqueio, dano, erro, punição e volta ao controle. Executar a matriz da skill, posições trocadas e eventual projétil após recuperação do emissor. Repetir sob carga de HUD, áudio e cena. | Caixa ativa antes da pose pede correção de relógio ou desenho. Rival sem resposta no alcance previsto pede ajuste e novo ensaio de balanceamento. Conservar o caso que falhou como regressão. |
| 8. Produção e expansão | Cotejar a arte presente na ROM com a aprovada. Rodar o checkpoint de qualidade da cena com os sete eixos, áudio, pior frame e vínculo visual. Atualizar a memória com SHA, caso observado e limitações. | Só ampliar o piloto após o trecho jogar como previsto. Cobrir cada estado previsto no GDD e suas transições legais; depois acrescentar confrontos na matriz. Um novo hash de ROM pede evidência fresca para os eixos afetados e conciliação completa antes da entrega. |

Use revisão independente e aprovação do dono nos pontos já definidos em
[`art-review.md`](art-review.md). Para cada defeito registre pose/tick/face,
efeito observado, hipótese, alteração mínima, comparação com o controle e
reteste. A ficha do personagem deve indicar em qual ação e em qual adversário
a decisão foi exercitada.

## Folha de exposição e ligação ao runtime

Execute os self-checks dos medidores usados. Este exercício **somente lê**
o contrato preservado do Hayato. Na raiz, com o Python do projeto:

```sh
python tools/sms_wrapper/audit_animation_contract.py --self-check
python tools/sms_wrapper/audit_animation_contract.py --manifest SMS_projects/master_of_fighters/doc/hayato_animation_contract_v4.json --exposure-sheet hayato_short_cut
```

As seis exposições declaradas ocupam **[0,8), [8,9), [9,11), [11,18),
[18,20) e [20,25)** no relógio da ação. O agente consegue apontar, por
exemplo, o desenho de passagem que dura um tick e verificar na futura
captura se ele chegou à tela. Para confrontar uma **hipótese** de atividade
com essas poses, acrescente `--active-window INICIO FIM`. Várias janelas
podem ser declaradas. Sem uma hipótese autorizada, omita a opção. A folha
reproduz o contrato, seu SHA e os relógios próprios dos objetos.

Na integração, programe e observe a ordem que o TDD definir. Um registro de
fronteira precisa permitir reconstruir esta trajetória:

```text
input entregue → input consumido → transição lógica
    trilha visual: elemento solicitado → tiles residentes → pose apresentada
    trilha de combate: janela e boxes → contato resolvido → reação → próximo controle
```

Guardar tick lógico e frame VDP para as duas pontas do intervalo, ID dos
atores, estado/face/posição, pose e resultado. Histórias com hitstop, atraso
de streaming, reuso de RGB ou projétil com vida própria exigem relógios
explícitos. A ordem real entre apresentação e contato deve ser medida.

Quando houver `combat_proposals`, siga `animation_id` até a sequência.
Leia `frame_data_candidate`, `balance_rationale`, `risk_and_counterplay` e
`test_plan` do movimento. Num golpe de janela única e relógio comum, os
limites propostos são `startup_ticks` e `startup_ticks + active_ticks`.
Exemplo didático: [3,5) pode atravessar dois desenhos consecutivos. Um
print de uma dessas poses não informa em qual tick houve contato. Em golpe
de múltiplas janelas, use as fronteiras específicas do TDD. No disparo,
o evento de emissão e a atividade do projétil têm cronologias distintas.

## Exercício de decisão com Master of Fighters

- **Hayato:** o contrato v4 e a coreografia documentam carga da perna traseira,
  condução pelo quadril, arma rígida e absorção. Usar essa sequência como
  controle de atuação e timing apenas no recorte aceito. Para produzir uma
  defesa ou outra ação, voltar à intenção, aos apoios e ao adversário.
- **J.J.:** o contrato v5 do disparo separa gesto do corpo e evento da arma.
  No confronto, observar emissão única, trajetória e encerramento do objeto,
  inclusive se ele sobreviver ao retorno do emissor. A duração das poses do
  corpo por si só deixa a vida e o contato do pulso em aberto.
- **Alis:** o roteiro da estocada registra 24 composições estáticas, máximo
  de 53 objetos totais e oito por linha. O seletor indica interseção geométrica.
  O próximo tipo de prova seria a ligação entre ponta apresentada, janela
  lógica, prioridade do BG e reação do rival em perto/limite/fora, nas duas
  faces. O diagnóstico existente ainda não resolve bloqueio ou dano. O
  limiar provisório de input pertence ao experimento.
- **Dr. Social:** a decisão de congelamento preserva o concept e a referência
  de tamanho. O estado impede usar sprites in-game históricos como matéria
  de produção. Consultar o registro vigente antes de qualquer tarefa futura.

Fontes do exercício no consumidor:
[contrato do Hayato](../../../../SMS_projects/master_of_fighters/doc/hayato_animation_contract_v4.json),
[coreografia do corte](../../../../SMS_projects/master_of_fighters/doc/hayato_short_cut_choreography_v2.json),
[contrato do J.J.](../../../../SMS_projects/master_of_fighters/doc/jj_zillion_single_shot_animation_contract_v5.json),
[roteiro da estocada](../../../../SMS_projects/master_of_fighters/doc/alis_strong_thrust_round1_qa.md)
e [decisão sobre o Dr. Social](../../../../SMS_projects/master_of_fighters/doc/dr_social_ingame_freeze_20261104.md).
Esses caminhos são exemplos da fábrica central. Em projeto materializado,
consultar a raiz central do SMSForge para abrir o exercício.

## Ensaio de uma troca completa

Direção escolhe um ataque do GDD e especifica o que o jogador deve perceber
ao acertar, bloquear ou errar. O executor registra comando, face, distância e
primeiro tick livre de cada lado. Arte, áudio e QA usam os mesmos três casos.
Para cada linha aplicável abaixo, anote na ficha do golpe a decisão vigente,
o responsável, o controle que deve passar e a variação que deve falhar.
Uma mecânica em estudo volta à direção antes de entrar no orçamento da cena.

| Decisão do recorte | Exercício e critério de revisão |
|---|---|
| Comando e conflitos | No reconhecedor do modo, exercitar pressão e soltura em n−1/n/n+1, acorde, virada, L+R e U+D. Registrar máscara recebida, candidatos, comando consumido e decisão do resolvedor inclusive em contato simultâneo. |
| Fases e caixas | Na tabela usada pelo combate, observar antes, primeiro e último tick ativo e primeiro livre. Testar último pixel dentro, primeiro fora, canto e espelho. Um overlay de treino autorizado lê a mesma caixa consumida pelo resolvedor. |
| Contato e relógios | No tick que altera vida ou guarda, juntar posição, caixa, reação e pose solicitada/residente/submetida ao framebuffer. Para hitstop autorizado, escrever quais relógios avançam durante a pausa e testar o primeiro input livre. A receita de impacto abaixo inclui um caso de dano com pose atrasada. |
| Reação, queda e retomada | No mudo e a 1×, verificar se a postura distingue hit, block e whiff. Se houver tremor, manter a caixa física no lugar previsto. Para queda autorizada, seguir lançamento, chão e primeiro tick vulnerável. Exercitar erro sem faísca e tentativa de atingir durante a levantada. |
| Âncora e materiais | Comparar pé de apoio, ponta da arma, caixa e cor por material antes, durante e após o golpe nas duas faces. Na composição que divide o ator entre BG e sprites, conferir P0 e P1 sobre o pior fundo com o HUD visível. |
| Câmera e cenário | Levar os dois atores do centro ao canto. Quando houver reação ambiental, verificar gatilho, oclusão, fim e reset ao trocar de round. Medir SAT, pico por linha e pior VBlank na composição mais cara. |
| Recurso, defesa e abuso | Registrar saldo antes/depois de hit, guarda, erro e reset. Testar custo exato, insuficiente, saturação e evento repetido. Para combo ou juggle aprovado, demonstrar a saída defensiva e a fronteira que encerra a sequência. |
| Áudio | Repetir hit/guarda/erro com música e SFX disputando canal. Capturar início, prioridade e restauração na interrupção, pausa e fim do round. Conferir se a reação visual ainda comunica o resultado com o som desligado. |
| HUD, rematch e treino | Aplicar o menor dano autorizado perto de uma fronteira da barra. Confrontar vida, barra e feedback transitório. No rematch, verificar limpeza de input e primeira ação legal. Se houver dummy, o replay passa pelo reconhecedor do jogo. |
| CPU | Partir da mesma posição, estado visível e semente, variar só o input oculto do rival. Comparar decisão e tick de reação até o primeiro estímulo perceptível. Repetir por dificuldade autorizada. |
| Repetição e restauração | Repetir a entrada por tick a partir da mesma configuração e comparar o estado autoritativo a cada tick. Localizar o primeiro campo divergente. Se o GDD pedir restauração, exercitar salvar, avançar, restaurar e reexecutar, incluindo parser, timers e objetos. |

Os exercícios vieram da [auditoria dos 35 aspectos e seus controles](../../../../SMS_projects/master_of_fighters/doc/curation_candidates/2026-11-21_auditoria_impacto_sistemas_pipeline.md).
Para executar o caso de regressão dos recibos, siga a
[receita de impacto](../skills/sms-recipe-animacao-impacto.md#comparar-os-contatos-de-duas-gravações).

## Fechamento e passagem ao próximo agente

Entregar uma linha por caso com **esperado, observado, veredito, ROM SHA,
sessão, caminho da mídia/trace e pendência**. Uma captura em stepping decide
ordem e composição; a prova de cadência usa execução contínua. Para o aceite
SMS_GLOBAL §133, o objetivo é 60 FPS, mínimo de 58 em **cada** janela válida,
sem arredondamento, com pelo menos duas janelas, dispersão ≤2, input/lógica/
apresentação coerentes e pior frame medido. PAL50 serve ao diagnóstico regional.
Fechar a sessão e conferir limpeza por ID. Os comandos e os contratos de
evidência vêm de [sessão isolada](emulator-isolated-session.md) e
[checkpoint de qualidade](product-quality-checkpoint.md).

**Instrução de retomada para o executor:** “Localize o último controle aceito
e o primeiro elo sem prova. Reproduza esse elo com um par e uma ação do GDD.
Se falhar, corrija no owner da causa e repita o caso. Depois amplie por estado
e confronto. Registre precisamente o que outro agente conseguirá reproduzir.”
