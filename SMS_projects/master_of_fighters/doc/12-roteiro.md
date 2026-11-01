# 12-roteiro — master_of_fighters

> Roteiro e diálogos. Autoridade #6.
> Primeiro degrau da ordem de trabalho de cena: **roteiro vem antes do
> storyboard, que vem antes da arte cara.**

## Premissa
Reunir o elenco registrado do Master System em duelos 1v1 nos quais identidade,
distância e leitura do adversário orientem a ação. O percurso funcional é
selecionar → lutar melhor-de-três rounds → compreender o resultado → continuar
o arcade ou retornar à seleção. Motivo narrativo do encontro, diálogos e finais
não foram decididos; este roteiro não inventa lore para preencher essa lacuna.

## Roteiro funcional — proposta de experiência, 2026-11-01

Vínculo: [GDD](11-gdd.md#contrato-de-experiência--revisão-de-design-de-2026-11-01),
[cenas](13-spec-cenas.md#contratos-de-experiência-das-cenas--2026-11-01) e
[movimentos de Social](dr_social_combat_design_proposal_v1.md#contratos-de-experiência-por-movimento--2026-11-01).
Os quatro beats desenvolvem o loop já previsto; controles, regras abertas e
destinos pendentes estão em GD01–GD07. Não são cenas novas ou aceite de jogo.

| Beat / cena | O que o jogador aprende e decide | Risco, pista e consequência | Saída e recuperação |
|---|---|---|---|
| 1. Escolher — 01 seleção | Reconhecer identidade e disponibilidade; escolher e conferir antes de confirmar. | Nome/imagem/foco coerentes; uma célula bloqueada não inicia luta nem engana com confirmação. | Escolha válida prepara o duelo; correção/reseleção precisa de comandos GD01. |
| 2. Ler e preparar — entrada da 02 | Reconhecer seu lutador, o oponente, chão e estado inicial; perceber quando o controle fica disponível. | Apresentação não é ataque; input mantido da seleção não deve causar golpe involuntário. | Neutro controlável. Não usar autoplay diagnóstico como comportamento do round. |
| 3. Ameaçar e responder — 02 | Administrar distância; ler preparação; escolher ataque, guarda ou evasão autorizada. | Comprometer alcance expõe ao contrajogo; hit, block e whiff têm resultados legíveis e distintos. | Recuperar a guarda/controle e tomar nova decisão; derrota parcial não deixa estado preso. |
| 4. Entender e continuar — fim da 02 / 03 arcade | Reconhecer vencedor, progresso e próximo desafio ou fim do percurso. | Resultado, pose e prêmio correspondem ao estado; empate/time-over dependem de GD04. | Próximo round, próximo adversário ou seleção conforme regra; derrota precisa destino definido, sem tela abandonada. |

## Atuação e intenção emocional

Seleção comunica reconhecimento e escolha; início do duelo oferece orientação;
neutro cria expectativa; comprometimento do golpe cria tensão; consequência
confirma a decisão; recuperação e resultado dão espaço para entender e retomar.
Isso é hipótese de ritmo, não sensação comprovada. Não inserir efeitos/música
extras como substituto de preparação legível.

Social observa e pune com precisão: bengala delimita distância, rapieira se
compromete em linha e bumerangue cria uma decisão de espaço. Hayato expressa
carga/liberação/absorção de um único corte, mantendo a katana aceita. J.J.
prepara/recolhe a Zillion proporcional ao corpo, sem emissão nesta amostra.
Atuação dos demais depende das fichas/decisões individuais do GDD; não aplicar
a mesma coreografia com roupa diferente.

## Texto, áudio e transições

Nenhuma fala canônica foi aprovada. Textos funcionais futuros devem nomear
escolha, resultado e destino sem introduzir história. Copy final, caracteres
únicos/tiles e duração em tela precisam orçamento antes da arte; quantidade de
caracteres não equivale automaticamente a padrões únicos residentes.

Navegação, confirmação, ataque, contato, guarda e resultado precisam de
feedback visual próprio. Áudio reforça essas diferenças, com prioridade e
restauração dos canais no TDD, sem exigir voz ou FM. Na ROM diagnóstica atual
não há áudio de gameplay validado. Ao transicionar, encerrar objetos/eventos
da cena anterior e limpar comandos mantidos conforme GD01; não carregar dano
ou tiro residual para o próximo round.

## Percurso experimentado e limites

D01 (`cena01_duel_read`) é a amostra da preparação visual do **duelo 02**,
não a seleção 01. Em 01/11, a QA privada da ROM `90ea0f98…` percorreu
autoplay inicial → desativação → entrada manual → S01–S05 → guarda → nova
entrada → guarda, com nomes/barras/chão simultâneos. Sessão, SHA completo e
relatório estão no memory bank. Isso exercita o ciclo de apresentação e a
reentrada, sem ameaça funcional ou consequência sobre Social.

Seleção, distância controlável, hit/block/whiff, round, arcade e encerramento
do jogo permanecem **não experimentados** neste consumidor. Critério de
fechamento: playtest do caminho completo e dos extremos descritos nas cenas,
com input/estados/mídia da mesma ROM. Opinião estética, defeito observado e
hipótese devem ser registrados separadamente; nenhum teste de poses os paga.
