# 10-memory-bank — master_of_fighters

## 27/11/2026 · Revisão da ficha de Alis e contagem de combo

A [ficha de construção](ficha_tecnica_alis_g6e_v1.docx) revê 15 poses e três planos do final. Nas marchas #01–08 e no Passo de Escudo #54–56, a revisão separa a saia rosa, as meias brancas e as botas e recupera o contorno das pernas. A altura visível passou de 48 para 51 px em #42, de 47 para 50 em #44, de 46 para 49 em #47 e de 43 para 40 em #66. O pé permanece registrado em Y143. Os planos de Alis e do corte laconiano usam o concept v4. Odin segue o retrato da Sega. As regras e os tempos da ficha continuam vinculados à G6e. [Atlas e medidas](../data/source_art/sprite_studies/alis_revisao_ficha/revisao.json) · [Planos e referências](../data/source_art/scenes/alis_guardioes/lineage.json)

O contador da [ROM de ensaio](../out/candidates/alis_combo_hits_v1/rom/master_of_fighters.sms) apareceu nos dois lados no Emulicious. A estocada forte e o soco curto tiraram 10 e 6 PV em sequência. O painel de cada atacante mostrou 2 e voltou ao fundo ao terminar a reação. Com a segunda entrada atrasada, a vítima recuperou o controle no tick 46 e o segundo contato no 47 iniciou nova contagem. A tabela de afastamento no repertório continua em discussão. O segmento fixo de código termina em 0x7F9C (exclusivo), com 100 bytes até 0x8000. As três janelas mistas registraram 50,434976, 48,437551, 48,936907 FPS, abaixo do piso de 58. A janela selada de 3.000 apresentações registrou 0 estouros de VBlank. [Medições do combo](decisions/2026-11-27_alis_combos_revisao.json)

## 27/11/2026 · Apresentação Alis × Alis e Battle em FM

A [candidata do Espaçoporto](../out/candidates/alis_versus_barlow_fm/rom/master_of_fighters.sms) usa Barlow SemiBold como padrão dos nomes no Versus. P1 e P2 usam o retrato de pré-luta voltado para o centro, com o traje de P2 na segunda paleta do combate. Em oito sessões privadas concluídas, o Emulicious exibiu os nomes com 59 × 20 pixels de tinta e reproduziu as 21 posições da pista dentro da moldura. As 20 atualizações do mapa terminaram com VCount 237. [Câmera capturada na ROM](../out/qa/alis_versus_barlow_fm/fm/versus.gif)

*Battle* tocou no YM2413 na História e no Versus contra Alis. O ensaio acompanhou a volta musical, a execução no PSG e a opção de música desligada. Fire na História reduziu a vida da CPU de 100 para 94. Com áudio FM, a carga mista e a de especiais encerraram as janelas de 3.000 apresentações com zero estouros de VBlank. A pior janela de especiais mediu 34,455577 FPS. O piso de 58 FPS continua reprovado. SHA-256 da ROM `1ada003a3cc1d6e2ac7f0501044bf3e1402eb97cd2a5a6a11b056820433dfcd0`. [Áudio FM da luta](../out/qa/alis_versus_barlow_fm/fm/battle.wav) · [Medições e sessões](decisions/2026-11-27_versus_palma_fm.json)

## 26/11/2026 · Ficha técnica de construção do elenco

O [modelo de personagem](ficha_tecnica_personagem_modelo_v1.docx) acompanha o registro de repertório. A [edição preenchida de Alis](ficha_tecnica_alis_g6e_v1.docx) usa os controles e os tempos do capítulo G6e, ilustra poses e efeitos e distingue regras de contato, hipóteses de combo e observações no emulador. Trata-se de documentação de construção; a cadência e o aceite do combate seguem no registro da candidata.

## 26/11/2026 · G6e · ROM do Espaçoporto de Palma

A G6e prepara a SAT por lutador, mantém os slots residentes nas trocas de pose e reaproveita a célula da magia quando só os pixels do efeito mudam. O teste de regras cobre a recuperação de golpes e a defesa em pé e agachada. A conferência do pacote de arte encontrou 376 poses, 3.008 fases e 1.834 células de fundo com coordenadas distintas dentro de cada fase. A comparação em software de 2.500 transições preservou as entradas da SAT e seu terminador. O Emulicious mostrou os dois lutadores na pista. Os 1.678 pixels verificados coincidiram com a arte do cartucho. [ROM G6e](../out/candidates/alis_guardioes_g6e/rom/master_of_fighters.sms)

O SHA-256 da G6e é `e3a98e8c1280545313a10998a958f9909fa693789670283f6aa13f2e1649b00f`. A guarda contra a CPU na História mediu 48,510449, 48,437409 e 43,821153 FPS. As três janelas mistas do Versus mediram 51,433688, 50,434976 e 48,936907 FPS. Com especiais simultâneos, as 24 janelas variaram de 35,454290 a 56,427250 FPS. As duas cargas selaram 3.000 apresentações com zero estouros de VBlank. O piso de 58 FPS segue reprovado. O ensaio do Versus confirmou Fire curto, chamas duplas e Chat nos dois controles. A reinicialização do host interrompeu o ensaio de impacto antes do veredito. [Recibo e medições sem arredondamento](decisions/2026-11-26_cadencia_g6.json)

Na G6e, os controles da História acionaram os 11 comandos de Alis contra a CPU. Com 16 PV de cada lado e 8 de Reiki, Alis atordoou a rival e terminou o round com os Guardiões de Algol. Os sete planos apareceram no emulador. Depois do epílogo “Depois do eco”, o botão 2 abriu a tela de vitória de Alis. Os 49.152 pixels da tela coincidem com a vitória de P1 no Versus. No Versus, P1 e P2 conseguiram a finalização. As chamas percorreram a pista em curvas distintas e, na troca simultânea de Fire forte, cada lutador perdeu 10 PV com 11 apresentações de pausa no impacto. A filmagem por passos registra 348 quadros, sem áudio. [Vídeo do final no Versus](../out/qa/alis_guardioes_g6e/versus-magias/guardioes.mp4)

## 26/11/2026 · Cadência dos especiais de Alis · G6 em teste

A G6d foi medida no Emulicious NTSC com a ROM de SHA-256 `643d67f72d295dc2eba234a7dd025fa136d9ef4b837c0076cd7fb7c009e1a61c`. O contador de apresentação selou duas cargas de 3.000 quadros, uma mista e outra de magias. As duas terminaram com zero estouros de VBlank. A guarda na História ficou entre 44,828340 e 46,509209 FPS. No Versus, as três janelas mistas ficaram entre 46,440126 e 51,433688 FPS e a pior janela de especiais mediu 35,454290 FPS. A G6d continua abaixo do piso de 58. O recibo conserva cada janela sem arredondamento, os SHAs das ROMs e as sessões das revisões G6 a G6d. [Recibo de cadência](decisions/2026-11-26_cadencia_g6.json)

Na G6 inicial, a CPU recebeu testes de Fire curto e forte, chamas duplas, Myau, Rest, onda, sabre, Chat e espelho pelos comandos do jogador. No Versus houve reflexão, troca simultânea e finalização pelos dois lados. A tontura e o fim cinematográfico contra a CPU ainda exigem confirmação por controle na mesma candidata submetida ao aceite. [Ensaios da G6 no emulador](../out/qa/alis_guardioes_g6)

## 26/11/2026 · Elenco, impacto comum e Odin · candidata G5

A G5 integra os gestos de Alis às fichas com comandos físicos, aparo e material de som. O motor recebe também os contatos dos projéteis. Os dois Fire fortes acertaram no mesmo passo lógico no Versus. Cada lutadora terminou com 90 PV e duas unidades de Reiki. O contador do cartucho mediu 11 publicações congeladas. História, finalização dos dois lados, revanche e filme com PSG passaram pela ROM de SHA-256 `c202314a04a192936206453359150d416c9f85f80be707851da1906d05e1ca96`. [ROM G5](../out/candidates/alis_guardioes_g5/Alis_Guardioes_de_Algol.sms) · [Troca de golpes](../out/qa/alis_guardioes_g5/trade/intervalo_de_impacto.json) · [Odin e os Guardiões no emulador](../out/qa/alis_guardioes_g5/sound/guardioes_com_som.mp4)

O impacto físico conservou 4/10 passos no leve, 11/20 no forte e 11/3 na defesa. A carga mista mediu 39,9485, 39,9485 e 37,9511 FPS. A fila do VDP terminou na área ativa 27 vezes em 3.000 apresentações mistas e 74 vezes no ensaio de magias. O aceite permanece reprovado. O corredor de sondas conserva 103 bytes de folga. [Impactos](../out/qa/alis_guardioes_g5/impact/observations.json) · [Recibo das dez sessões G5](decisions/2026-11-26_harmonizacao_g5.json) · [Cinemática e fontes de Odin](curadoria_guardioes_de_algol.md)

## 26/11/2026 · Especiais de Alis e F. Anime modular · G4

[ROM para jogar](../out/candidates/alis_guardioes_g4/Alis_Guardioes_de_Algol.sms), SHA-256 `21c43ff6fdb5f9241e33fb76f0ee6a624316d5078cf03b48cd292a2ed93ea9c0`. Fire de duas intensidades, chamas curvas duplas, Myau alado, Rest, onda da Espada Laconiana, Rising Saber, Chat, reflexão, atordoamento universal e Guardiões de Algol entram pelo capítulo do Espaçoporto. Os modos História e Versus chegaram à arena em sessões privadas. P1 e P2 confirmaram o final pelos controles. A reação é selecionada pelo ID da vítima. O ataque fornece o efeito sobreposto. [Ficha para o elenco](padrao_moveset_especiais.md) · [Curadoria, reprodução e resultados](curadoria_guardioes_de_algol.md) · [Vídeo com áudio](../out/qa/alis_guardioes_g4/som/guardioes_com_som.mp4)

**Estado de aceite.** Candidata testada no emulador, orçamento reprovado. Pior janela com magias dos dois jogadores, 21,472316 FPS. A guarda contra a CPU variou de 36,626440 a 39,759629 FPS. O piso do projeto é 58 em cada janela. A carga de magias selou 104 saídas de VBlank em 3.000 apresentações. O próximo confronto com outro personagem precisa validar o balanceamento e a identidade da reação dele. A próxima integração do motor deve repetir as mesmas entradas e confrontar o custo das composições de fundo, dos dois lutadores e do HUD. [Carga de magias](../out/qa/alis_guardioes_g4/spell-budget/observations.json) · [Vídeo da partida que termina em F. Anime](../out/qa/alis_guardioes_g4/versus2/guardioes.mp4).

## Camada de elenco, fase 2: capacidades · candidata r2 · 26/11/2026

A ficha de lutador ganhou capacidades: `owned` diz quais golpes ele tem e `vertical`, se pula e se agacha. O motor do espelho deixou de desviar por ID de personagem na leitura de comando, no contato, no andar e na caixa de dano. A validação da ficha cobra só o que o lutador usa. Um lutador sem pulo e com gravidade zero ficava suspenso depois de um knockdown e chegava a voltar ao estado livre no ar; por isso toda ficha exige gravidade, caixa aérea e caixa de dobra. O [TDD](15-tdd.md) descreve o contrato.

O teste `tools/test_duel_roster.c` põe uma ficha sintética só de pé, sob o ID do Hayato, contra a ficha de produção da Alis. Ele confere pulo e agachamento ausentes, golpe recusado, dano e força lidos da ficha da atacante, avanço do especial por ficha e 30 mil passos aleatórios em que o lutador limitado só sai do chão em queda. Os sete programas de teste do host passaram em dez combinações de flags. A equivalência da Alis contra a h1 repetiu os nove traços idênticos.

A candidata [r2](../out/candidates/espacoporto_de_palma_elenco_r2/rom/master_of_fighters.sms), SHA-256 `4e4f07197ef1c96c34dca88faba3ae5192d687657bf97ba655a081ba4dea5a4c`, repetiu a QA da h1 no Emulicious privado: impacto nos oito critérios com 4/10, 11/20 e 11/3; guarda contra a CPU a 37,565686073188175 / 40,02391077273003 / 38,50037361127023 FPS, reprovada como antes; carga mista 37,45 / 40,95 / 40,45 FPS; os mesmos 8 términos em área ativa. O código fixo cresceu 3 bytes e o banco das regras, 159. O corredor de sondas manteve 112 bytes de folga. [Impacto](../out/qa/alis_20261126/espacoporto_de_palma_elenco_r2/impact/observations.json) · [FPS na CPU](../out/evidence/sessions/0713a5ae40e744acb540de0d13d7fbc6/runtime/fps.json) · [Carga mista e pior quadro](../out/qa/alis_20261126/espacoporto_de_palma_elenco_r2/worst/observations.json)

A ficha de produção do Hayato não entrou. Os números da b32 usam outro pivô nos golpes (no espelho, as caixas da Alis ficam 12 px deslocadas), e ele não tem agachar, pulo, golpes aéreos nem Puxada. Para lutar no espelho ele também precisa de poses empacotadas no formato do renderizador, que é a fase 3. Os comandos como dados e a troca de `MOF_ALIS_CHAPTER`/`MOF_ALIS_RIPOSTE` por capacidades dependem do capítulo, ainda não commitado: o Super e o contragolpe só existem nele.

## Camada de elenco, fase 1 · candidata r1 · 26/11/2026

As regras do duelo em espelho deixaram de deduzir força, defesa aérea, anti-aéreo, empurrão e som pelo número do golpe. Agora leem uma ficha por lutador, a `MofFighterDef` descrita no [TDD](15-tdd.md). A ficha reúne também o perfil de pulo, as caixas por postura, a linha do pescoço, o alcance da Puxada e o avanço do especial. A ficha da Alis fica em `src/fighter_alis.inc` e o elenco em `src/duel_roster.inc`, indexado pelo ID do lutador. `MofAlisMotion`/`duel.alis[]` passaram a `MofDuelBody`/`duel.body[]`. Nenhum número de jogo mudou.

Um harness de migração no host rodou as regras antigas com a tabela da h1 e as novas com a ficha real. Cobriu as configurações espelho, capítulo e contragolpe, com três sementes cada e 40 mil passos aleatórios por traço, incluindo acerto, defesa, Puxada, queda, KO, congelamento e aparo. Os nove traços ficaram idênticos byte a byte. Os seis programas de teste do host passaram em nove combinações de flags, e `tools/test_duel_impact.c` passou a montar a ficha.

A candidata [r1](../out/candidates/espacoporto_de_palma_elenco_r1/rom/master_of_fighters.sms), 1 MiB, SHA-256 `dd8478e63097319eb81a5cd91dc611059d28c65b4a9a0a52ec1d36c335ed70ab`, compila a mesma base E2 da h1. No Emulicious privado, o caso `impact` passou nos oito critérios com os valores da h1: leve 4/10, forte 11/20 com tremor e forte defendido 11/3. Só a fase do contato mudou um tick, porque a entrada chega por quadro de vídeo. O código fixo cresceu 165 bytes, restando cerca de 2,8 KB, e o banco das regras cresceu 215 bytes. O corredor de sondas passou com 112 bytes de folga. [Impacto](../out/qa/alis_20261126/espacoporto_de_palma_elenco_r1/impact/observations.json)

**Desempenho reprovado, sem regressão.** A guarda contra a CPU mediu 37,61199191211526 / 40,036518298362125 / 38,550061297239054 FPS. A carga mista, 37,45 / 40,95 / 40,45 FPS. A janela selada registrou os mesmos 8 términos em área ativa da h1, com o mesmo primeiro estouro. [FPS na CPU](../out/evidence/sessions/4ca0bfb605a6411d8dd6be70cf372d2a/runtime/fps.json) · [Carga mista e pior quadro](../out/qa/alis_20261126/espacoporto_de_palma_elenco_r1/worst/observations.json)

Próximo: a fase 2 traz a ficha de Hayato a partir da b32, troca as flags com nome de personagem por capacidades da ficha e leva os comandos de especial, Super e contragolpe para dados. Antes da fase 3, o dono decide o tamanho do cartucho e a divisão da paleta entre dois lutadores diferentes.

## Impacto por força na base E2 · candidata h1 · 26/11/2026

A candidata [h1](../out/candidates/espacoporto_de_palma_impacto_h1/rom/master_of_fighters.sms), 1 MiB, SHA-256 `25b8625937efc686c8473c2aa9e67baa05df92758d872e9b0e816cffc1ee390c`, compila a E2 com o congelamento de impacto e a reação por força pedidos pelo dono em 25/11. Toque curto é leve: congela 4 passos e tira o controle por 10 ticks. Normal mantido, especial, Super, contragolpe e Puxada são fortes: congelam 11 passos, tiram o controle por 20 ticks e fazem a defensora tremer 1 px. A defesa recebe o congelamento da força, sem tremor, e mantém 3 ticks de bloqueio. O contrato está no [TDD](15-tdd.md) e no teste `tools/test_duel_impact.c`.

No Emulicious privado, o caso `impact` mediu leve 4/10, forte 11/20 com pivô alternando 147/145 e forte defendido 11/3. O contato apareceu uma vez e cada medidor subiu no máximo uma unidade por troca. Durante o congelamento, a ROM publica um quadro por VBlank: 11 passos levam ~183 ms. O forte tem filmagem do framebuffer. O corredor de sondas passou com 116 bytes de folga. Os sete testes de host passaram. [Impacto](../out/qa/alis_20261125/espacoporto_de_palma_impacto_h1/impact_r5/observations.json) · [Filmagem do forte](../out/qa/alis_20261125/espacoporto_de_palma_impacto_h1/impact_r4/forte_acerto.mp4)

**Desempenho reprovado.** A guarda contra a CPU mediu 37,61236470083433 / 40,03174650307009 / 38,54246999138509 FPS. A carga mista, 37,45 / 40,95 / 39,95 FPS. A janela selada de 3.000 publicações registrou 8 términos em área ativa, com VCount mínimo 0. O primeiro começou em VCount 196 com 7 tiles e SAT. A alta sobre a E2 não indica motor mais rápido: congelamentos baratos entram na média e a reação mais longa muda a carga dos mesmos roteiros. A captura final do `worst` caiu numa tela apagada depois de gravar a janela. [FPS na CPU](../out/evidence/sessions/4a39ed78c4b34cb2b8b93a5d5b0231a4/runtime/fps.json) · [Carga mista e pior quadro](../out/qa/alis_20261125/espacoporto_de_palma_impacto_h1/worst_r2/observations.json)

Próximo: o dono deve experimentar o impacto no controle físico e ajustar 4/10 e 11/20. Seguem pendentes em GD02 o empurrão com atrito, o chip, a trava de defesa por força e a cadência alvo60/piso58. Depois deste lote vem o plano da camada de elenco.

## Espaçoporto de Palma jogável · candidata E2 · 25/11/2026

[Espacoporto_de_Palma.sms](../out/candidates/espacoporto_de_palma_e2/Espacoporto_de_Palma.sms) aponta para o mesmo arquivo de 1 MiB do recibo E2, SHA-256 `bed67d64b2950bad2d545580e8c2d6c7b6c16c3bdc4d7d7b06fc59f500e56b01`. História e Versus chegam à pista pelo menu inicial. A introdução pede o passaporte e anuncia o embarque para Paseo. Em História, P1 venceu, passou pelas duas falas finais, perdeu a revanche e retornou ao menu. Ambas as capturas de áudio tiveram sinal. A C5r continua sendo a candidata de Camineet. [Recibo E2](../out/candidates/espacoporto_de_palma_e2/build_record.json) · [Percurso de História](../out/qa/alis_20261125/espacoporto_de_palma_e2/story/observations.json)

O Versus verificou os padrões das duas Alis em VRAM contra os pacotes do cartucho e 1.678 pixels opacos no framebuffer inicial, com zero divergências. Ao mover as duas jogadoras entre os pontos medidos, o HUD ficou fixo, a nave percorreu 5 px e as marcas da pista percorreram 11 px. A primeira tentativa E1 havia perdido as juntas da pista e corrompido os últimos padrões de P2 durante o carregamento. [Versus e paralaxe](../out/qa/alis_20261125/espacoporto_de_palma_e2/port-versus/observations.json)

**Desempenho reprovado.** Em História contra a CPU, as três janelas mediram 34,16230113318957 / 30,65477687784887 / 30,648492242083712 FPS. Sob carga mista no Versus, 33,95622126244364 / 35,45428984755144 / 34,45557745747957 FPS. A janela selada de 3.000 publicações registrou 33 términos em área ativa. O primeiro começou em VCount 196, com 8 tiles de sprites e 142 bytes de SAT, e terminou em VCount 0. A build passou nos pré-gates e deixou 120 bytes de folga até as sondas. [FPS na CPU](../out/evidence/sessions/5eef69af41c84ffeae2b13aa66cc3401/runtime/fps.json) · [Carga mista e pior quadro](../out/qa/alis_20261125/espacoporto_de_palma_e2/worst/observations.json)

Na [filmagem da História](../out/qa/alis_20261125/espacoporto_de_palma_e2/story/troca.mp4), 106 dos 112 quadros permitiram alinhar diretamente a silhueta da nave. Nesse trecho, a torre e o leitor alternaram duas exposições cada. A região da ave alta apresentou 15 imagens distintas e a da ave baixa, 18. [Amostras de animação do framebuffer](../out/qa/alis_20261125/espacoporto_de_palma_e2/story/movimento_ambiente.json)

## Estudo de seleção de arena anterior à E2 · 25/11/2026

O proprietário manteve a rua de Camineet como candidata. A ROM C5r continua disponível na entrada abaixo. O Espaçoporto de Palma é uma proposta visual paralela para o mesmo duelo, baseada na tela do passaporte que o proprietário enviou. A prévia reúne paralaxe em três planos, duas aves animadas, sinalização da torre e do leitor e as duas Alis em escala de luta. A decisão artística está aberta. A proposta do espaçoporto foi composta fora da ROM e seu desempenho no console segue sem medição. [Prévia animada](../out/diagnostics/alis_espacoporto_proposta/pista_em_movimento.gif) · [Arte-fonte e proveniência](../data/source_art/scenes/alis_espacoporto/lineage.json)

## Capítulo de Alis em Camineet · 25/11/2026

A [candidata para jogar](../out/candidates/alis_capitulo_01_c5r/rom/master_of_fighters.sms) é a **C5r**, 1 MiB, SHA-256 `2112971df3eb08339e93a2892a43fc38fd144b2df7c4a6134ec13640e20af9ea`. **Aceite de desempenho reprovado.** O Emulicious NTSC abriu a história em Camineet. P1 venceu com 11 de vida, leu as duas falas finais e abriu a revanche. P2 venceu a revanche por 100 a 0 e o botão 2 retornou ao mesmo menu inicial, verificado pixel a pixel. No versus local, os dois jogadores carregaram oito unidades e consumiram o medidor com o Super (ação 14). A escuta longa apresentou as poses 77, 78 e 79; no comando de saída a ROM já pediu a pose 5, mas a SAT ainda exibia 79 na primeira leitura. [História](../out/qa/alis_20261125/c5r-story/observations.json) · [Versus](../out/qa/alis_20261125/c5r-versus/observations.json) · [Escuta e retomada](../out/qa/alis_20261125/c5r-acting/observations.json)

Na C5r, as cúpulas vermelhas recuperaram o contorno e o piso cinza perdeu os seis frisos contrastantes. A revisão independente reconheceu o trio de lojas, as casas e a grade ciano em 256 × 192. O pote continua pequeno para identificação segura; reconhecimento sem legenda por um fã ainda precisa de teste. A saída alternou duas exposições na célula (29,9); a filmagem da troca de 112 quadros registra as mudanças nos índices 29 e 50. O título e a luta têm WAV distintos com sinal do PID verificado. A filmagem tem a cadência nominal do VDP e contém os quadros repetidos do jogo. [Quadro de luta](../out/qa/alis_20261125/c5r-story/arena.png) · [Filme](../out/qa/alis_20261125/c5r-story/troca.mp4) · [Tema](../out/qa/alis_20261125/c5r-story/tema_titulo.wav) · [Mix](../out/qa/alis_20261125/c5r-story/musica_e_golpes.wav) · [Revisão independente](../out/qa/alis_20261125/c5r-art-review/run_74f71820534043dfb5b1b0b0fa10990b/report.json)

| C5r, alvo 60 e piso 58 | Medidas no SHA acima |
|---|---|
| CPU contra guarda, três janelas de quatro segundos | 34,40142376212537 / 30,61250148252591 / 30,624874306066737 FPS |
| Dois controles em contato, três janelas de 120 VDP | 68, 73 e 70 publicações. 33,95622126244364 / 36,453002237623316 / 34,95493365251551 FPS |
| Pior quadro, selo de 3.000 publicações | 25 términos em área ativa, mínimo VCount 0. O primeiro começou na linha 196 com 8 tiles de padrão e 130 bytes de SAT, sem upload de tiles de fundo ou troca de PNT. Ao fim do envio, VCount 4. |
| Host e sondas | Emulicious privado, heap 256 MiB, cargas serializadas via Fôlego. Build e pré-gates passaram. Corredor com 126 bytes de folga. Três testes do leitor GD05 passaram. Cinco sessões do coordenador e uma de revisão encerradas. |

Próximo trabalho técnico: usar os seis marcadores da C5r e o perfil misto para separar o custo de entrada, regras, preparação da dupla e publicação. Comparar os lotes de SAT e tiles no primeiro derrame, preservar a antecipação das duas armas e conferir a primeira pose após o comando. Repetir os mesmos testes no novo SHA, inclusive acerto/guarda, áudio e brilho. O selo da C4 tinha 47 derrames. A redução para 25 na C5r deixa o gate aberto. O lote mantém o status de candidata local. [Medição de FPS](../out/evidence/sessions/fbe531b1c50841e998d4a95b65716dad/runtime/fps.json) · [Janelas mistas e pior quadro](../out/qa/alis_20261125/c5r-worst/observations.json) · [Folga das sondas](../out/logs/c5r-corridor.json)

A candidata B de 1 MiB, SHA-256 `6e0a579d0afd0eb0f68c8231aee8a359af63e64f18425e69a12e26f7b0d8566b`, abriu o título, o diálogo de Myau e o duelo da Alis rosa contra a verde no Emulicious privado. O diálogo chamava o cenário de “Portão ao Luar”. Era uma invenção do crossover. A sessão terminou no anúncio ROUND 1 e não mediu cadência funcional. [Revisão da candidata B](../out/qa/alis_20261125/baseline/run_4a0ce39c00374ccb9a173fdca707ddbc/report.json)

O dono reconheceu as três lojas de Camineet e pediu outra arquitetura para as casas e fachadas. A nova ilustração traz marquises arredondadas, escotilhas e juntas rebitadas de inspiração Hoi-Poi. A jarra alude a Nekise. A grade azul pertence à saída da cidade em Palma. A direção e a composição estão registradas no GDD e na especificação. [Arte-fonte e proveniência](../data/source_art/scenes/alis_palma/lineage.json)

A candidata histórica C4 (`ae6d7c83a370691752705efbbb27695ea1f621f688632432a6cf281e7b0416df`, 1 MiB) é a primeira deste lote com vitória da história, ambos os diálogos de encerramento, revanche, derrota e retorno ao mesmo menu confirmado pixel a pixel. O caso de versus atingiu carga nos dois medidores. O brilho da saída e os dois controles foram exercitados em sessão privada. A arte da rua reutilizou o trecho livre de cada um dos oito slots de sprites após medir o tamanho máximo dos pacotes dos dois trajes. [História e controles](../out/qa/alis_20261125/c4-story/observations.json) · [Versus local](../out/qa/alis_20261125/c4-versus/observations.json)

Na C4 a guarda contra a CPU mediu 31,8735372781772 / 29,91188963802255 / 29,666306533152028 FPS funcionais. Com golpes simultâneos, as três janelas de 120 VDP publicaram 66, 70 e 66 quadros completos. A ROM selou 47 términos de publicação em área ativa nos primeiros 3.000 quadros publicados. A cadência e o VBlank reprovaram. [FPS](../out/evidence/sessions/7714b004a96649dfae7cd9e4e017ece6/runtime/fps.json) · [Carga mista e pior quadro](../out/qa/alis_20261125/c4-worst/observations.json)

## Cena 02 · produção de Alis × Alis

O espelho implementa dois controles com traje rosa e verde, doze
normais, três alturas de guarda, reações de cabeça, abdômen e base
baixa, Puxada com Escudo, queda, levantada, KO e reinício do duelo.
Os comandos e os bancos da referência Hayato × Alis b32 permanecem
disponíveis. O arco conserva 78 px de altura, 20 ticks no ar e 6
px/tick de impulso diagonal livre.

A [matriz do espelho](scene02_alis_espelho_qa.md) guarda a ROM de cada
revisão, os quadros divergentes, as ações corretivas e os resultados.

A [b53](../out/candidates/scene02_alis_mirror_b53/rom/master_of_fighters.sms),
SHA-256 `a15313589a6d196553e3c1ba16548db948818e8639ac5b85f7fbe4c720ce6753`,
libera o controle quando um normal aéreo toca o chão. Os oito casos
da regressão responderam no próprio pouso e duas pressões novas na
leitura de contato foram aceitas. A b52 prendia o controle por 5 a
10 leituras. A b53 retoca saia, braços e braceletes dos chutes fortes,
calibra as duas posturas baixas e usa arte própria no recolhimento do
escudo. [QA](scene02_alis_espelho_qa.md#b53--pouso-paleta-e-recolhimento) ·
[Curadoria](curation_candidates/2026-11-22_alis_pouso_materiais_recolhimento.json).

A [b52](../out/candidates/scene02_alis_mirror_b52/rom/master_of_fighters.sms),
SHA-256 `47c0a4027d39b1d45bfe48a53ec819fb6ac3d046243c702fa848b3edd3ca8fe9`,
introduziu o chute aéreo forte com 12 ticks de reação e
até 7 px de recuo. A puxada mantém os pés no chão e o lado de origem,
aplica o escudo, faz a rival recuar em dois passos e só então cair.
As novas poses seguem o concept v4 com lâmina ciano separada do
peitoral índigo. O Emulicious confirmou os oito contatos da regressão
e uma defesa no replay, com 16 capturas de fase. A cadência funcional
ficou abaixo do piso de 58 FPS nas duas janelas.
[QA e vídeo](scene02_alis_espelho_qa.md#b52--chute-forte-puxada-e-model-sheet) ·
[Curadoria](curation_candidates/2026-11-22_alis_impacto_puxada_model_sheet.json).

A [b49](../out/candidates/scene02_alis_mirror_b49/rom/master_of_fighters.sms),
SHA-256 `2458fdecfccce8a33f29b7843860886893b6c205d8f2eda4bb6028a8c556e9da`,
é a candidata para revisar as proporções das cinco poses. Os contatos
aéreos de escudo e espada medem 53 px de altura. A queda cresceu de
32 × 27 para 42 × 36 px. O repouso mede 63 × 11 px e a elevação da
cabeça mede 56 × 18 px. As cinco poses foram vistas no framebuffer
do Emulicious. Os quatro contatos do roteiro se repetiram no vídeo
contínuo. O build integral e o aceite de cadência seguem pendentes.
[Comparação e diagnóstico](scene02_alis_espelho_qa.md#b49--escala-das-cinco-poses) ·
[Curadoria](curation_candidates/2026-11-21_alis_punho_tecido_contorno.json).

A sessão de jogo da b49 reproduziu a perda do botão 2 com o foco em
um componente interno do Emulicious. O lançador do Steam Deck mudou
a configuração de foco do controle virtual. Foram verificados os seis
chutes do P1 e o chute pela tecla **S**. O atalho local abre arquivos
`.sms` com o lançador e o `run.sh` está executável. Resta repetir com
o controle físico. [Diagnóstico e prova](scene02_alis_espelho_qa.md#b49--botão-de-chute-pelo-lançador).

A [b48](../out/candidates/scene02_alis_mirror_b48/rom/master_of_fighters.sms),
SHA-256 `90c77cf2e3cfe1c680ccf2c2399dcea4db2320c729a9c4f1000c60db41221772`,
foi a revisão de punho, tecido, contorno e repouso. A
conversão da b47 já produzia o branco que desbotava a túnica e o
bracelete. A revisão reserva a rampa do tecido, preserva o traço escuro
e distingue o punho do bracelete. A relincagem verificou o código da
b47 byte a byte e incorporou somente a tabela de quadros e os bancos
de arte revistos. A regressão no Emulicious confirmou os dois contatos
aéreos, o soco em pé e a queda com a cabeça apoiada antes da levantada.
Os quatro contatos se repetiram no vídeo contínuo. O build integral e
o piso de cadência permanecem pendentes.
[Quadros e diagnóstico](scene02_alis_espelho_qa.md#b48--punho-tecido-contorno-e-repouso) ·
[Curadoria](curation_candidates/2026-11-21_alis_punho_tecido_contorno.json).

A [b47](../out/candidates/scene02_alis_mirror_b47/rom/master_of_fighters.sms),
SHA-256 `baca9cde8fa4edf93cd823a6c649c39c16234379af71823fdc5217817179d45a`,
passou a compartilhar os descritores de geometria e manteve bancos
próprios por traje. O duelo aéreo
exibiu a fase ativa nos quatro acertos e no bloqueio, repetidos no vídeo.
A espada iniciou na primeira leitura e atingiu a parte alta da rival em
pé com os pés da atacante 21 px acima do chão em P1 e P2. Os seis chutes
por controle, a rasteira, o repouso e os dois passos da levantada passaram
no roteiro por leitura. Segurar o botão 2 através do pouso manteve uma
única ação aérea. O lançador Linux confirmou a emissão de 2 e das
combinações com ↓ e ↑ na porta A virtual.
As janelas nominais do duelo aéreo ficaram em 38,311262176527535 e
33,73801519402458 FPS. O piso de 58, o sincronismo de quatro reações
aéreas e a validação humana do controle físico seguem em aberto.
[Prova e diagnóstico](scene02_alis_espelho_qa.md#b47--fase-ativa-com-as-duas-alis-no-ar) ·
[Curadoria](curation_candidates/2026-11-21_alis_golpes_aereos_e_chao.json).

A [b43](../out/candidates/scene02_alis_mirror_b43/rom/master_of_fighters.sms),
SHA-256 `fbf9d94dce222317c65a51cfbf9a9d40c9cb702910827615960bb7f985150591`,
introduziu as poses revistas. A espadada em voo prepara no
primeiro toque e acertou a altura Y=95–106 com os pés 21 px acima do
chão. A queda exibe o corpo apoiado, a primeira elevação da cabeça e o
apoio do joelho. O Emulicious confirmou os seis chutes do botão 2 nos
dois controles. O lançador Linux foi corrigido para entregar o botão 2
do controle virtual do Steam Deck, inclusive com ↓ e ↑.
O ensaio contínuo de regressão mediu 52,43240047877327 e
48,93690711352171 FPS funcionais. O aceite permanece pendente pelo piso
de 58 FPS por janela. A correspondência com a pressão física no Deck
permanece para a avaliação do dono.
[Prova e diagnóstico](scene02_alis_espelho_qa.md#b43--acionamento-aéreo-queda-e-botão-2) ·
[Curadoria](curation_candidates/2026-11-21_alis_golpes_aereos_e_chao.json).

A [b37](../out/candidates/scene02_alis_mirror_b37/rom/master_of_fighters.sms),
SHA-256 `309999840297e72fee8fb5c4e36b54f6feaee6fc461797ea9a330d1bdadfd482`,
confirmou os 12 normais em ambos os controles por leitura. O misto
repetiu os 14 contatos terrestres no vídeo contínuo. Os giros centrais
de P1 e P2 e o giro no canto publicaram a soltura junto do dano.
O misto ficou em 37,14219632498696 e 38,949783212803 FPS pelo VDP,
com pico de 45 sprites, oito por linha e zero fins de envio em área
ativa. A espadada simultânea, as reações imediatas às guardas alta e
aérea e o piso de 58 FPS continuam critérios de aceite em aberto.

A [b38](../out/candidates/scene02_alis_mirror_b38/rom/master_of_fighters.sms),
SHA-256 `a062fcc0b5c363ce43adf83a6bbf6448b1ec2971caba5118332147260a6b1842`,
registrou o giro nas duas faces. Confirmou a
pega a 32 px, erro a 33 px, soltura dos dois controles e giro de P2
junto à parede. A reação da vítima abaixada chegou no contato e a
guarda aérea ganhou a pose de impacto um tick após bloquear. As
janelas mistas foram de 37,14219632498696 e 39,449139407838935 FPS
pelo VDP. O arco conservou a lógica aprovada e a cadência ainda
alonga o movimento na tela.

A [b39](../out/candidates/scene02_alis_mirror_b39/rom/master_of_fighters.sms),
SHA-256 `f978da58124869d303b384c6cb711fad552335e73d86c2a740205d4a421bb325`,
registrou no framebuffer os
14 contatos terrestres do misto e os quatro ataques e bloqueio do
roteiro aéreo. A espadada e o chute forte simultâneos exibiram as
duas poses ativas no contato e as duas reações no tick seguinte. As
janelas mistas foram de 37,637425609320125 e 39,94849560287487 FPS
pelo VDP. A guarda em pé durante recuo ainda reage visualmente com
dois ticks de atraso. A pose em pé de P2 volta três ticks após o
reinício lógico. As sessões dos 14 roteiros da matriz foram encerradas.
Os resultados incluem repetição dos saltos após espadada, 12 guardas compatíveis, limites
de alcance, dois contra-ataques antes da retomada e três giros com
pega e soltura sincronizadas. O encaixe artístico da pega e o piso
de 58 FPS seguem abertos.
[Comandos](scene02-comandos.md#perfil-alis--alis) ·
[Repertório](repertorio_alis_hayato.md#produção-do-espelho-de-alis) ·
[Curadoria futura](curation_candidates/2026-11-21_alis_espelho_producao.json).

## Cena 02 · retomada de salto e montagem da espadada na b32

O dono aprovou a física e a velocidade da b29 e relatou perda de salto e
poses repetidas ao combinar diagonais, guarda e espadada. A b29 confirmou
a perda da nova pressão de ↑ durante a recuperação, a guarda aérea fixa
em #59 e a exposição diagonal #58 ausente numa travessia.

A [ROM b32](../out/candidates/scene02_alis_jump_mix_b32/rom/master_of_fighters.sms),
SHA `201757c38220c8890bd1bb09b00f6b1fad2a0ace4e5b92184578fe3cfb57e03e`,
consome um salto por nova pressão e retoma a diagonal dois ticks após a
recuperação da espadada. Mantém 78 px e 20 ticks de voo. Foram verificados
os dois cruzamentos, a guarda com subida, recolhimento e descida e o
segundo salto preparado antes do pouso. A primeira espadada voltou a
exibir preparação, estocada e recuperação, com #18 presente no acerto.
O Passo de Escudo #49 acertou após a sequência mista.

O Emulicious conferiu 33 exposições no framebuffer e a faixa do HUD em
269 quadros aéreos. As amostras da SAT chegaram a 48 sprites e oito por
linha. O pior intervalo entre ticks foi quatro VDP, com zero falhas de
renderização e zero términos de envio em área ativa na sequência medida.
A cadência NTSC continua sendo o eixo de aceite pendente, com janelas
nominais de 37,951070822731126 e 43,943345163162356 atualizações/s.
A próxima avaliação de cadência deve conservar a primeira espadada
após boot, as duas travessias e a alternância de guarda no ar. A
recuperação visual do primeiro golpe ainda entrou um tick após o pedido.
[Matriz, ROM e recibos](scene02_hayato_alis_qa.md#saltos-combinados-com-espadada-e-guarda) ·
[Curadoria futura](curation_candidates/2026-11-21_alis_salto_comandos_montagem.json).

## Cena 02 · salto alto com cruzamento de Alis na b29

O dono relatou salto lento e baixo na b26. A [b29](../out/candidates/scene02_alis_crossing_b29/rom/master_of_fighters.sms), SHA `3f0ee085a36c0a6249098a21682b747ea65dc427971a34adc13ddd03fcd56757`, subiu de 26 para 78 px e reduziu a fase aérea de 28 para 20 ticks. Ela usa impulso inicial, gravidade e flexão de pouso. A diagonal mantém 6 px/tick e pode cruzar Hayato dentro da janela de altura com área de pouso livre.

Em Emulicious, Alis passou de X111 a X216 e, na volta, de X174 a X68. As duas faces viraram no ápice com pixels conferidos. A diagonal iniciada longe terminou em X120, respeitando a separação na descida. O teste contínuo registrou o escudo depois de virar à esquerda e a espadada depois de voltar à direita. A fase aérea vertical ocupou 30 VDP na b29 ante 55 na primeira captura da b26. As travessias ocuparam 40 e 39 VDP. O limite de 58 FPS continua aberto. [Matriz](scene02_hayato_alis_qa.md#salto-alto-e-cruzamento-de-lado) · [Comparação temporal](../out/diagnostics/alis_20261121_salto/qa-b29/flight-comparison.json).

## Cena 02 · posturas, salto e defesas de Alis na b26

O pedido de 21/11 registrou as lições de paleta por material, sequenciamento,
buffers, proporção, marcha e timbre. A espada de Phantasy Star ficou como
direção explícita para a curadoria futura do som de Alis. [Candidatos a curadoria](curation_candidates/2026-11-21_alis_paleta_movimento_audio.json).

A [b26](../out/candidates/scene02_alis_postures_b26/rom/master_of_fighters.sms),
SHA `57be8e489786c65cd3092c1bed86f3fc90c5dd20e900bd3d3c59d662d2a68cda`,
integra agachamento, salto vertical, diagonais e guardas em pé, baixa e
aérea para Alis no P1. O salto tem dois ticks de preparação e 28 no ar.
O ápice fica 26 px acima do chão e as diagonais percorrem 58 px livres.
A pose aérea e o pivô de Alis podem avançar enquanto a próxima página do
rival é preparada. O contraste com a b25 está no bloqueio #59, que saiu
com 146 de 146 pixels visíveis no pivô correto da b26.

No trecho contínuo, os três bloqueios preservaram vida e as três regressões
de ataque repetiram escudo #21, espada #18 e Passo de Escudo #49. O pior
intervalo foi quatro VDP, com zero fins de envio em área ativa. As janelas
nominais ficaram em 37,951070822731126 e 42,94463277309048 atualizações/s.
O aceite final de cadência segue aberto. [QA de posturas](scene02_hayato_alis_qa.md#posturas-e-salto-de-alis).

A regressão do [round completo b26](../out/diagnostics/alis_20261121_posturas/b26-round-continuous/6-continuous/round-continuo.mp4) repetiu os 16 acertos, o Saque #46 com arte confirmada e o KO de Hayato. O áudio passou com 9,55% de atividade. As duas janelas nominais sob round foram 36,15173775632064 e 37,951070822731126 atualizações/s. O trabalho seguinte de cadência usa essa carga e a troca focal de posturas como controles.

## Cena 02 · b23-r3 melhora a marcha e o som de Alis

O dono observou pernas animadas sob um tronco rígido, equipamento imóvel e o mesmo impacto nos dois golpes do botão 1. A [b23-r3](../out/candidates/scene02_repertoire_walk_sfx_b23_r3/rom/master_of_fighters.sms), SHA `4b6a5b4847397cb7516850452e2fc0e47d67a379107093c14e91d188d64110c6`, usa quatro chaves por direção. O tronco cede 2 px na compressão e sobe 2 px na passagem. A espada gira junto à pega, o escudo oscila em fase própria e a sola fica em Y143. A revisão independente confirmou o balanço no vídeo da b23-r2 e a igualdade dos 15 quadros nativos entre versões. Na b23-r3, o teste no framebuffer cobriu Alis voltada para a direita. A arte empacotada da outra face passou a checagem de composição.

O escudo usa impacto grave e curto. A espadada tem ataque mais agudo e cauda tonal em queda. Cada um tem som de preparação. A guarda tem um timbre próprio. A b23-r2 perdeu as duas leituras coerentes de contato na captura contínua. A b23-r3 conclui a publicação do registro antes do processamento do PSG no mesmo tick. A [troca contínua](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/round-continuo.mp4) registrou escudo #21 com 6 de dano e espadada #18 com 10 de dano, com ambas as poses já residentes e submetidas. O [recorte de áudio](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/golpes-escudo-e-espada.wav) teve 16% de atividade no piso de 5%. A trilha da troca inteira teve 2,85%.

O pior intervalo da troca permaneceu em três VDP, sem fim de transferência em área ativa. As janelas da troca em execução contínua mediram 51,433688088701395 e 52,43240047877327 atualizações/s pelo relógio nominal, com 40,49230209081007 e 42,87143295565962 em tempo de parede. O piso de 58 continua aberto. [Matriz da candidata](scene02_hayato_alis_qa.md#marcha-com-transferência-de-peso-e-efeitos-dos-golpes).

O [round completo](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round-continuous/6-continuous/round-continuo.mp4) chegou a 16 contatos e ao KO de Hayato. O áudio passou com 8,73% de atividade. As janelas sob luta registraram 39,94849560287487 e 40,44785179791081 atualizações por segundo pelo relógio nominal, com pior intervalo de quatro VDP. O [traço por quadros](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round/6-round/round-trace.json) mantém os ticks 361 e 497 com 12 padrões em fila. A preparação do renderizador é o próximo ponto de medição da cadência sob essa carga.

A [soltura durante a passagem](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-release-isolated/release.json) estabilizou o pivô assim que o direcional neutro foi consumido. A guarda recebe o corpo de uma vez, com uma descida de 2 px. A mudança de base na parada após compressão ainda pode ser percebida contra o rival.

## Cena 02 · b21 corrige recuo e coesão visual de Alis

O dono confirmou o controle físico na b18 e reprovou o recuo curto, a troca de materiais durante a marcha e a deriva de proporções nos dois golpes do botão 1. Na [b21](../out/candidates/scene02_repertoire_alis_cohesion_b21/rom/master_of_fighters.sms), SHA `6f7c86e65fa1e530d67e912353d33502b955a575bd26721757ff5d06af04ac48`, Alis recua de X111 a X32 em 79 px, ante 48 na b18. A margem X32–X223 deriva da extensão das poses dos dois atores e da separação mínima de 24 px. A reprise após o canto confirmou comandos consumidos e retorno a X120.

Os rasters da guarda fornecem o rosto, as massas do torso e os materiais usados nas marchas. As pernas preservam os apoios desenhados. O golpe curto mantém rosto e proporções e move o escudo da guarda. A espadada registra o rosto no pescoço de cada pose, preserva a ponta ativa e remove resíduos nas duas faces. A [matriz b21](scene02_hayato_alis_qa.md#b21--revisão-dos-pontos-relatados) vincula as 15 poses conferidas no framebuffer, a troca com áudio e as regressões de alcance e guarda. O [teste em execução contínua](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/continuous/round-continuo.json) registrou 52,42232678200898 e 50,98397512481057 atualizações/s. O piso segue reprovado, e a face esquerda foi conferida na composição empacotada.

O [round completo da b21](../out/diagnostics/alis_20261121_revisao_b18/b21-round-continuous/6-continuous/round-continuo.mp4) chegou ao KO de Hayato com 16 contatos e áudio. A próxima intervenção de cadência tem como controle o pior intervalo de quatro VDP do round por quadros e as janelas de 26,0488767488953 e 35,010753362898036 atualizações/s em tempo de parede. A lista de revisão ainda inclui material dos chutes e do Passo de escudo, além da prova ao vivo da face esquerda.

## Cena 02 · b18 com Alis no controle principal

Após relato de lutadores estáticos na abertura manual, o perfil do Emulicious mostrou a b17 como última ROM e o Deck ligado ao P1, atribuído a Hayato naquela candidata. A [b18](../out/candidates/scene02_repertoire_alis_p1_b18/rom/master_of_fighters.sms), SHA `e738daa7bf80875025cda66ea73d5e55803e4a034836427abc3175bf93fc27aa`, põe Alis à esquerda no P1 e Hayato no P2. Os seletores de boot ativos são mascarados individualmente até soltar, deixando livres os demais comandos. O lançador Linux aceita o caminho da candidata ao abrir o duelo.

A [matriz b18](scene02_hayato_alis_qa.md#b18--alis-no-controle-principal) vincula a ROM à imagem de abertura e ao vídeo contínuo. Alis recuou e avançou pelo P1 virtual e tirou 10 de Hayato com a espadada. Foram verificados 15 bancos e o corredor de 263 bytes. A prova do controle integrado físico e o aceite integral de cadência seguem pendentes. O piloto ainda usa poses estáticas enquanto os jogadores estão em repouso.

## Cena 02 · ciclo de reserva de sprites e primeira troca na b17

A [b17 de seis leituras](../out/candidates/scene02_repertoire_hold6_20261121_b17/rom/master_of_fighters.sms), SHA `1ee09f085f79d983da5595d0fdcad7048608171ae2917c275da8fa753578f900`, ensaiou o custo de reservar padrões no duelo. A reserva de padrões P1 percorre blocos com índices de 8 bits e pula o recálculo da proteção quando todos os pedidos já têm faixa. Build passou com os bancos 02–16 conferidos e 263 bytes de folga da sonda. O [round contínuo com áudio](../out/diagnostics/alis_20261121_b17_continuous/6-continuous/round-continuo.mp4) mostrou os 14 contatos e o KO. As janelas de parede ficaram em 39,01123494727796 e 37,98667176447802 atualizações/s. No round por quadros, a b17 perdeu 208 épocas contra 218 da b14 e voltou a levar quatro quadros VDP no pior intervalo, com zero fins de envio em área ativa.

No [ensaio da espadada](scene02_hayato_alis_qa.md#b17--reserva-de-padrões-de-sprites), acertar em 66 px tirou 10 de vida. Em 67 px, Hayato puniu com o Saque e tirou 16, mas seu sprite permaneceu em guarda no contato. Em 28 px, Hayato bloqueou e acertou o soco curto antes da retomada de Alis. O Saque aproximado #46 manteve a prova no framebuffer posterior à submissão. A revisão independente de arquivo na b14 confirmou a separação visível entre a ponta e o corpo no limite e a falta de gesto corporal de defesa. O aceite continua pendente na b17.

O próximo teste do renderizador deve separar o fundo da preparação #45 do trabalho de antecipar #46. O controle de pior intervalo pede 8 P1 + 4 P0 em t334 e 12 P0 em t468 com os atores ainda em guarda. O ensaio de reserva reduziu a perda no round, e esses dois intervalos continuam sem fechar o prazo. Antes de transportar a otimização para outra candidata, conservar os controles de guarda, alcance, Saque perto/distante e custo da troca de poses. O [inventário de design](repertorio_alis_hayato.md#alis--decisões-vigentes-e-cobertura-de-produção) registra as famílias autorizadas e as ações à espera de decisão. A b17 oferece duelo local desde o boot. Menu de comandos dentro da ROM, transição de cutscene e aceite integral seguem pendentes.

## Cena 02 · fila P0 da punição distante

A b16 de seis leituras, SHA `a3c28e21ac3e78e7c43abb19f56a660bfe01a713e23a1432e14e4adbf183fdfa`, transmitiu P0 de uma camada diretamente do banco. O round chegou ao KO com zero fins em área ativa e 220 épocas perdidas, contra 218 na b14. As duas janelas de parede ficaram em 38,31319758183483 e 37,7519264849066 atualizações/s. A comparação em VDP não mostrou ganho de cadência. A fonte de execução voltou à b14, conservando [ROM e patch experimental da b16](../out/candidates/scene02_repertoire_hold6_20261121_b16/renderer-experiment.patch).

A [leitura dos símbolos da b16](../out/diagnostics/alis_20261121_b16_alis_miss_punish/saque-background-trace.json) mostrou a fila #45 descartando a etapa anterior a cada incremento de X=111 até X=123. No contato t111/VDP206, #46 tinha 4 de 23 células P0 e #0 permanecia apresentado. O último tick ativo acumulou 8 células. #47 substituiu o alvo antes de #46 chegar à tela. O próximo ensaio de vídeo tem de preparar a fase de contato antes de estabilizar o pivô e preservar a apresentação de #45 durante a passada. O [orçamento estático candidato](../out/diagnostics/alis_20261121_b16_alis_miss_punish/saque-p0-residency-budget.json) confirmou 100 padrões P0 residentes por face de #45 e duas páginas dinâmicas de 32. A residência adicional P1 de #45 exige medir a troca com o espaço do chute forte, a composição com o oponente e o prazo de #47.

## Cena 02 · comparação de preparação de P0

A b15 de seis leituras, SHA `40251c63a533f66c42bb9f414ca53d8a93912ff09bb639f01dde73100ac6d420`, usou o caminho de camada única também no preparo do quadro corrente. Preservou todos os números de VDP do round b14, os 14 contatos, o KO e zero envios na área ativa. A cadência funcional continuou reprovada e o Saque distante repetiu a publicação de #0 no tick de dano, com #46 solicitado e P1 residente. [Traço da punição](../out/diagnostics/alis_20261121_b15_alis_miss_punish/6-alis_miss_punish.json) · [Round em execução contínua](../out/diagnostics/alis_20261121_b15_continuous/6-continuous/round-continuo.json). O próximo experimento transmite padrões de uma camada pré-composta diretamente da ROM e lê o estado real da fila P0 por símbolo para localizar o prazo perdido na passada longa.

## Cena 02 · HUD da b14 preparado antes do VBlank

A [b14](../out/candidates/scene02_repertoire_hold6_20261121_b14/rom/master_of_fighters.sms), SHA `e99ce3677559ea58907fbeee9cea1c8c530514f0803446bfd88a383a095a2fe1`, reduziu de dez para zero os envios encerrados na área ativa no roteiro comparável. A lógica manteve os 14 contatos e o KO. O Saque publicou #46 no contato VDP677, com a imagem seguinte no VDP678. A cadência continua reprovada e o pior intervalo permaneceu em quatro quadros VDP. O áudio do round completo foi gravado em uma sessão contínua do mesmo SHA. [Recibos e tempos](scene02_hayato_alis_qa.md#b14--hud-e-round-completo).

## Cena 02 · Saque na b13-r2 e round contínuo

A [b13-r2](../out/candidates/scene02_repertoire_hold6_20261121_b13_r2/rom/master_of_fighters.sms), SHA `7e1b911741b8241a937a7e910a8d0e4cf04288ea195c0e425ea4891520bdf0fb`, preparou as 23 células P0 do Saque em lotes 12+11 antes do contato. No stepping a pose #46 foi submetida no VDP666 e desenhada no VDP667. O round chegou ao KO em duas sessões privadas encerradas, uma com gravação contínua e áudio. O chute fraco de Hayato atrasou uma pose no vídeo contínuo. A cadência de parede ficou em 39,9321286 e 30,5670929 atualizações/s. Na coleta por quadros, o pior intervalo foi de quatro quadros VDP e dez envios com atualização de vida terminaram na área ativa. [Round e evidências](scene02_hayato_alis_qa.md#b13-r2--saque-e-round-completo).

## Cena 02 · primeira troca de Alis na b12

A [b12 de seis leituras](../out/candidates/scene02_repertoire_hold6_20261121_b12/rom/master_of_fighters.sms), SHA `c30ed6cdd673a03148f8ca45218910f7e71facbb79846538e30b3b9cdbae761f`, compilou com os gates prévios, 15 bancos conferidos e 543 bytes de folga no corredor. A caixa da estocada segue a ponta do desenho #18. Em sessões privadas encerradas, o golpe acertou a 66 px e errou a 67 px. Hayato bloqueou sem chip a 28 px e acertou Alis na recuperação. O controle com a direção errada recebeu dano. Toque, limiar e rearme produziram as poses iniciais #20/#17/#17 uma vez cada.

O comparativo independente em 256×192 confirmou mudança de vida e a lâmina no quadro seguinte. O torso ainda fica separado da ponta no acerto de borda. A defesa de Hayato carece de pose distinguível e a primeira marcha livre de Alis pode deixar o desenho anterior na tela. Os cinco casos registraram irregularidade entre ticks e quadros VDP. A [matriz, os números e os PNGs](scene02_hayato_alis_qa.md#b12--primeira-troca-de-alis) documentam o recorte. O [inventário de Alis](repertorio_alis_hayato.md#alis--decisões-vigentes-e-cobertura-de-produção) mantém em aberto as decisões de postura, especiais, magia, Super e agarrão.

## Cena 02 · auditoria de impacto, sistemas e pipeline

A [auditoria dos pilares V–VIII](curation_candidates/2026-11-21_auditoria_impacto_sistemas_pipeline.md) separa o impacto intencional, o hitstun e os atrasos de publicação, e cruza comandos, recursos, áudio, interface, IA e dados com o consumidor da b11-r2. Antes de expandir, a proposta é provar contato, comando e pose no mesmo trecho e fechar as decisões de GD01/GD02 que o piloto ainda não resolve. A [fila de curadoria](curation_candidates/2026-11-21_auditoria_impacto_sistemas_pipeline.json) registra os casos positivos/negativos e os responsáveis.

## Campanha · varredura de narrativa e cenas

A [auditoria de narrativa](curation_candidates/2026-11-21_auditoria_narrativa_e_cenas.md) cobre os quatro pontos do arco, seis técnicas de cena e sete grupos de referência do anexo. Há direção de campanha, roteiro e contratos de transição. A D01 e a b11-r2 provam recortes de composição e duelo. A passagem de apresentação à guarda e ao primeiro comando, incluindo skip, ainda precisa de prova própria. A [candidatura de curadoria](curation_candidates/2026-11-21_auditoria_narrativa_e_cenas.json) registra as decisões pendentes e os casos de validação.

## Cena 02 · auditoria da pose de guarda

O neutro inicial da b11-r2 manteve 21 imagens RGB iguais, com `#00/#16`, pivôs e hurtboxes estáveis. A guarda já serve como referência de identidade. Respiração, variantes e saídas em cada fase ainda precisam de ficha e prova em ROM. A [auditoria do idle](curation_candidates/2026-11-21_auditoria_idle_stance.md) e a [candidatura de curadoria](curation_candidates/2026-11-21_auditoria_idle_stance.json) priorizam a guarda em pé e seu vínculo com marcha, defesa e golpe, sem reabrir os controles aceitos do par.

## Cena 02 · auditoria da direção de personagens

A revisão identificou lacunas entre as decisões de design, o briefing que gera as poses e os artefatos que o build admite em modo de ensaio. Para o próximo recorte de produção, a proposta é fechar comando e categoria, função no duelo, identidade visual por pose e uma prova do contato com resposta do rival. A [auditoria em quatro pilares](curation_candidates/2026-11-21_auditoria_direcao_personagens.md) e a [fila de curadoria](curation_candidates/2026-11-21_auditoria_direcao_personagens.json) registram prioridades, responsáveis e exercícios de validação. A homologação canônica está pendente. O piso de 58 permanece reprovado no ensaio b11-r2.

## Cena 02 · correção da categoria dos normais

Em pé, toque em 1 é soco fraco, segurar 1 é soco forte, toque em 2 é chute fraco e segurar 2 é chute forte. Alis expressa `pe_1_longo` com uma espadada direta. A prova desse normal usa somente o botão 1 sustentado. O registro de `#45–50` continua como evidência do ensaio direcional da b11-r2. Corrigir o vínculo entre comando, ação e arte antes da próxima rodada de poses. [Decisão do proprietário](decisions/scene02-normais-dois-botoes_owner_20261121.json).

## Cena 02 · revisão de identidade por pose da b11-r2

O comparativo do framebuffer, dos sprites e das fontes localizou deriva de cabelo, roupa e leitura da katana em Hayato, compressão horizontal na marcha e perda de magenta na marcha de Alis. A pose `#46` do Saque ficou atrasada no stepping e apareceu no vídeo contínuo do mesmo SHA. A [matriz por pose e proposta de curadoria](curation_candidates/2026-11-21_scene02_identidade_por_pose.md) indexa os mosaicos e os controles. Próximo lote de correção por eixo: provar a rampa de Alis em `#38/#42/#43`, revisar a marcha de Hayato com escala uniforme e reproduzir o contato `#45→46→47` com posição publicada e framebuffer na mesma fronteira. O piso de 58 permanece reprovado.

## Cena 02 · b11-r2 em ensaio no Emulicious

A b11-r2 de seis leituras, SHA `f76fe86f5b3d874a7317c7727f350aa8e750af7a1dba9d85b8d71722c3a126b7`, contém os 15 bancos verificados. Na sessão contínua, os quatro ciclos exibiram todas as poses em 32 px e o soco de Hayato apresentou a pose 8 ao reduzir a vida de Alis a 94. O vídeo de 32,579 s com áudio chegou ao KO e está vinculado ao SHA. As duas janelas contínuas mediram 15,1878595 e 20,5018315 atualizações/s em tempo real, com 40,1135720 e 42,8019596 por segundo nominal do VDP. O piso de 58 permanece reprovado. [Índice e mídias](repertorio_alis_hayato_provas.md#round-contínuo-b11-r2).

## Cena 02 · sincronização do soco e integração de marcha e especiais

- A b09 de seis leituras, SHA `65ccd0810565b346e283f8792b6b7ae86422f0da5d3534e764c141332915a129`, reproduziu o primeiro soco no Emulicious e publicou a pose 8 no mesmo tick da queda de vida de 100 para 94. A amostra de impacto ficou em 55,0805015 atualizações/s nominais. O [recibo](../out/diagnostics/repertoire_20261119/scene02-impact-qa6-b09/6-round/impacto-soco.json) registra um atraso de apresentação e zero términos em área ativa.
- O proprietário aprovou os dois especiais para ensaio. As fontes de quatro ciclos de marcha e dois especiais foram preparadas a partir dos model sheets preservados. O empacotamento do lote acrescentou 22 poses às 29 existentes, verificou ambas as orientações e produziu 18 bancos para a candidata de 512 KiB. A prova de runtime é separada da decomposição estática. [Decisão](decisions/scene02-first-specials_owner-trial_20261119.json) · [Comandos](scene02-comandos.md) · [Plano e limites estáticos](../out/diagnostics/repertoire_20261119/scene02-actions-plan-v1.json).
- A b10 de seis leituras, SHA `57198fcbbf09be9a93afb820c7c4ba86de260b2d26ed7840f5b14efbfe209cb0`, executou os oito normais e os dois especiais até o KO. Cada sentido percorreu 32 px. A sonda viu todas as poses de marcha de Alis e duas de quatro em cada marcha de Hayato. O primeiro desvio foi a pose 33 solicitada no quadro VDP 146, com residência incompleta e pose 0 publicada. O ritmo medido no vídeo por quadros foi 39,2886856 atualizações/s nominais, com 345 épocas perdidas e zero envios encerrados na área ativa. O primeiro soco de Hayato e o Saque apresentaram a preparação no tick do dano. [Índice e fronteiras](repertorio_alis_hayato_provas.md#índice-do-round-de-diagnóstico-b10).
- A captura contínua da b10 excedeu o limite de tempo da automação com a rota de áudio verificada. A sessão fechou. A SAT no quadro inicial tinha 47 sprites e pico de 7 por linha. O round silencioso por quadros, o recibo da tentativa contínua e as duas janelas reprovadas de 41,1040306 e 44,3126170 estão no mesmo índice.

## Curadoria do round b08 · normais, marcha e especial

O [índice dos oito primeiros acertos](repertorio_alis_hayato_provas.md) identifica vida e pose por tick. Em quatro deles a pose apresentada divergiu da pedida. O [parecer](../../../doc/curation/2026-11-19_mof_revisao_b08.md) documenta a correção do gravador, verificada nos traços b05/6, b05/8 e b08/6. O [próximo lote](../../../doc/continuity/20261119-prompt-b08-marcha-normais-especiais.md) cobre a sincronização dos normais, quatro ciclos de caminhada e o primeiro especial de cada lutador. Esta revisão utilizou as ROMs e sessões arquivadas.

## 2026-11-19 · Bancos e cadência da Cena 02

- O motor do repertório usa os bancos 02–10 para as 58 poses e as 464 fases
  da camada de fundo. O renderizador monta a SAT fora da transferência e
  prepara padrões em páginas fora de exibição. Os oito normais usam o comando
  na soltura para o fraco e limiares separados para o forte. Os pilotos da
  [matriz da Cena 02](scene02_hayato_alis_qa.md) permanecem arquivados.
- O `makesms` descartou a nona mescla e retornou sucesso quando recebeu nove
  operações separadas. A receita passou a escrever os nove bancos com uma só
  operação e a comparar todos os bytes com as fontes. O binário diagnóstico
  `6658518cfc858998f841d50fbf833c443267b0735791c8b645eed9ac68ef9267`
  confirmou o boot e registrou 20,788312139702825 e 23,994781416502324 FPS.
  [Comparação no Emulicious](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-p01/comparison.json).
- O [traço por etapa](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-p02/6-round/round-trace.json)
  mostrou dois quadros VDP por tick neutro e perda do prazo ao soltar o
  primeiro golpe. A revisão reduziu o caminho neutro, a coleta da sonda e a
  busca do cache. A compilação de 6 leituras verificou os nove bancos no SHA
  `83cf8e506d54aca42b80183c953b14b52bb17ff43f47736071c3d27edf2e75b9`.
  [Recibo do build](../out/candidates/scene02_repertoire_hold6_20261119_b02/build_record.json).
- A revisão b02 registrou janelas de 54,27668136613763 e 58,69225848842861
  FPS. O trecho neutro acumulou zero escritas após o VBlank, e a sessão
  encerrou quando o primeiro golpe precisou de mais de três quadros VDP
  para publicar seu tick. O piso de 58 FPS segue pendente.
  [Cadência b02](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b02/6/cadence.json)
  · [Traço b02](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b02/6-round/round-trace.json).
- O formato b03 compõe sobre o cenário no empacotamento e só mescla em RAM
  quando duas células P0 se sobrepõem. O empacotador confere, em todas as
  fases, tanto os pixels autorais como os pixels de fundo descobertos.
  [Bancos b03](../out/diagnostics/repertoire_20261119/scene02-repertoire-banks-b03/repertoire-pages.json).
- As ROMs b03 têm 256 KiB e os nove bancos batem byte a byte com o recibo.
  [6 leituras · fbbef487…](../out/candidates/scene02_repertoire_hold6_20261119_b03/rom/master_of_fighters.sms)
  · [8 leituras · 4bdc93b6…](../out/candidates/scene02_repertoire_hold8_20261119_b03/rom/master_of_fighters.sms).
- Em b03, o replay de 6 leituras marcou os oito normais, apresentou os 29
  IDs de pose da orientação padrão e terminou com Hayato 64 e Alis 0. Os
  530 intervalos de lógica cobriram 813 quadros VDP. Houve 177 términos
  de envio na área ativa. As duas janelas neutras tiveram 232 e 293 avanços
  tanto da ROM como do VDP. Isso identificou limitação adicional de tempo de
  parede da sessão, que registrou 18,32655807007574 e 23,151949245368023 FPS
  no limite conservador da sonda. O streaming RGB perdeu a igualdade da
  contagem, então esta sessão preservou o traço do round e descartou o vídeo.
  [Traço b03](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b03/6-round/round-trace.json)
  · [Janelas do VDP](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b03/6/host-vdp-windows.jsonl).
- A candidata b04 de 6 leituras prepara endereços fora do VBlank, envia BG
  em bloco contíguo e limita o lote a seis padrões. O SHA
  `7f91b14ffd22985f0fcc6a8d0bd96efadc870e5fe96d077015c0782adbdbb6d2`
  passou no corredor de sondas com 709 bytes de folga. Na cena neutra a
  sonda SMRT registrou 59,043191119039854 e 58,50078254401529 FPS.
  [ROM b04](../out/candidates/scene02_repertoire_hold6_20261119_b04/rom/master_of_fighters.sms)
  · [Cadência b04](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b04/6/cadence.json).
- No round b04, os oito normais acertaram e Alis chegou a zero de vida.
  Foram 829 capturas de framebuffer, 256×192, com 13,834 s de reprodução NTSC.
  Em combate foram 38,310077206617 atualizações por segundo nominal, 262
  intervalos com avanço diferente de um quadro do VDP, 14 fins de envio na
  área ativa, 85 atrasos de pose e 25 de 29 IDs de pose na apresentação.
  O gargalo de cadência continua durante a preparação dos padrões P1.
  [Round b04](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b04/6-round/round-completo.mp4)
  · [Recibo](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b04/6-round/round-completo.json).
- O formato b05 guarda por pose as coordenadas SAT e os padrões P1 em
  trechos contínuos. O cache reutiliza a mesma alocação quando o conjunto
  de poses permanece estável e envia os padrões por banco em bloco.
  O round de 6 leituras registrou 710 quadros em 11,849 s, os oito normais,
  KO de Alis, 44,7310619778669 atualizações por segundo nominal, 25 fins de
  envio na área ativa e 45 atrasos de pose. A pose 11 de Hayato não apareceu
  nessa execução. Os quatro golpes fortes iniciaram na sexta leitura
  efetivamente consumida. As janelas neutras de parede reprovaram com
  52,602833413233334 e 56,94846967152801 FPS. Em ambas, ROM e VDP avançaram
  na mesma contagem de quadros.
  [Round b05](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b05/6-round/round-completo.mp4)
  · [Recibo](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b05/6-round/round-completo.json).
- Na candidata b05 de 8 leituras os mesmos quatro fortes começaram na
  oitava leitura consumida. O replay também confirmou os oito normais e KO.
  Registrou 730 quadros, 45,147272427906536 atualizações por segundo nominal,
  25 fins de envio na área ativa e 45 atrasos de pose. A comparação conserva
  os SHA e a sessão de cada limiar. A aceitação de combate segue pendente.
  [6 leituras](../out/candidates/scene02_repertoire_hold6_20261119_b05/rom/master_of_fighters.sms)
  · [8 leituras](../out/candidates/scene02_repertoire_hold8_20261119_b05/rom/master_of_fighters.sms)
  · [Comparação por comando](../out/diagnostics/repertoire_20261119/scene02-repertoire-b05-hold-comparison.json).
- A candidata b06 de 6 leituras antecipa a segunda pose enquanto o botão
  está pressionado, reutiliza as caixas nas mesmas coordenadas e reserva
  folga de envio para trocas de pose com muita PNT. Passaram as fixtures
  de regra, comandos, normais e movimento, e o corredor ficou com 687 bytes
  de folga. A ROM de SHA
  `6ef1e93a7421cf9b0f8a2a1b0df5106560f968e6fba0610b253d54ce79a6b707`
  confere com os nove bancos b05.
  [ROM b06](../out/candidates/scene02_repertoire_hold6_20261119_b06/rom/master_of_fighters.sms)
  · [Fixtures b06](../out/diagnostics/repertoire_20261119/scene02-repertoire-b06-host-fixtures.txt).
- O round b06 chegou ao KO e registrou 46,5675278655213 atualizações por
  segundo nominal. Os términos na área ativa caíram para quatro, três deles
  com apenas SAT e PNT no lote. O renderizador atrasou 124 apresentações e
  quatro IDs de pose não foram apresentados. As janelas neutras de parede
  ficaram em 38,486734727972305 e 52,8106096213658 FPS, com a mesma contagem
  de quadros na ROM e no VDP. A revisão b05 continua como o par comparável.
  [Recibo b06](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b06/6-round/round-completo.json).
- Em b07, a montagem da SAT em Z80 e o reaproveitamento da previsão entre
  poses estáveis elevaram a cadência do round para 49,2388434174969
  atualizações por segundo nominal. Houve quatro fins de envio na área
  ativa e 124 atrasos de apresentação. O round de 645 quadros chegou ao KO.
  O neutro passou nas duas janelas com 59,71062117279423 e
  58,75200150161137 FPS. A validação sob carga segue reprovada.
  [Recibo b07](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b07/6-round/round-completo.json)
  · [Cadência b07](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b07/6/cadence.json).
- A candidata b08 envia a SAT com a cópia contínua do SDK e escreve os
  endereços já preparados da PNT no trecho de submissão. O SHA
  `47a65c0988a0ac8a235b1c417df4b3eb4746d542ad595c3d3a3cc38df27011d4`
  confere com os nove bancos b05. O corredor de sondas ficou com 661 bytes
  de folga. A API de comando e o limiar continuam iguais.
  [Recibo do build b08](../out/candidates/scene02_repertoire_hold6_20261119_b08/build_record.json).
- A b08 confirmou os oito normais e KO no Emulicious. O round de 646
  quadros teve zero fins de envio na área ativa, linha mínima 205 e pico
  registrado 255. A cadência sob carga foi 49,1626222976556 atualizações
  por segundo nominal. Houve 167 intervalos diferentes de um quadro VDP,
  103 atrasos de apresentação e não apareceram os IDs 3, 8, 11 e 21. As
  janelas neutras de parede foram 53,53515731703253 e 52,005743870395996
  FPS, com a mesma contagem de quadros na ROM e no VDP. O VBlank do
  round passou na contagem de derrames. A cadência e a apresentação sob
  carga continuam reprovadas.
  [Round b08](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b08/6-round/round-completo.mp4)
  · [Recibo b08](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b08/6-round/round-completo.json).
- Para comparação de comandos, o par b05 tem ambas as ROMs, ambos os rounds
  e os limiares de 6/8 confirmados. O material de recuperação no NTFS está
  em `C:\Users\Deck\AppData\Local\SMSForge\recovery\master-of-fighters-integrated-20261119`.

## 2026-11-19 · Preparação do renderizador dos oito normais

- Os pilotos de 6 e 8 leituras continuam nos mesmos binários e SHA da
  [matriz da Cena 02](scene02_hayato_alis_qa.md). A tentativa de medir o
  controle de seis em tempo real expirou no boot do Emulicious. Ainda não
  há janela SMRT nova para distinguir o ritmo da ROM do stepping anterior.
  [Sessão de controle](../out/diagnostics/repertoire_20261119/scene02-control-realtime-6-b01/comparison.json).
- O caminho experimental `MOF_DUEL_FAST_SAT` arma o hook oficial de quadro
  para preservar a borda de VBlank até o envio, prepara o pacote SAT somente
  quando posição ou pose muda e envia apenas o trecho usado. A auditoria
  de marcadores passou. A [receita de seis](../out/diagnostics/repertoire_20261119/scene02-fast-sat-6-build.json)
  e a [receita de oito](../out/diagnostics/repertoire_20261119/scene02-fast-sat-8-build.json)
  são candidatas separadas. A cadência, distribuição VRAM e apresentação
  continuam sem validação nesse código.
- A decomposição preserva os pixels das 58 poses por fase e face, incluindo
  o piloto. O cruzamento no vão de 24 a 129 px projetou pico de oito por linha,
  57 objetos na SAT, 25 células P0 e até quatro células compartilhadas.
  No pior envio integral seriam 998 bytes de dados de padrões/PNT/SAT antes
  de comandos VDP, limpeza da PNT e HUD. O empacotamento em nove bancos
  refez os bytes das 58 poses e 464 fases P0 na leitura de retorno.
  [Plano de camadas](../out/diagnostics/repertoire_20261119/scene02-repertoire-layer-plan-b02.json)
  · [Bancos verificados](../out/diagnostics/repertoire_20261119/scene02-repertoire-banks-b02/repertoire-pages.json).
- O [trade-off de residência](../out/diagnostics/repertoire_20261119/scene02-repertoire-layer-plan-b03.json)
  comparou os tetos de P0 de 12 a 25 células para as poses de início.
  Com até 25 células ficam livres 43 slots de sprite em uma orientação
  e 41 na outra. Um par posterior pode pedir 57 objetos. A versão final
  precisa reutilizar parte dos slots de abertura durante a ação ou usar
  uma alocação mais econômica. Os experimentos preservam as durações do piloto.
- Permanecem pendentes a residência dos quadros posteriores, mescla das
  células compartilhadas, cronograma de upload, vínculo com `MOF_DUEL_REPERTOIRE`
  e round com KO em ROM. A próxima compilação/QA depende de uma vaga
  serializada no host. As amostras registraram outra suíte durante a
  tentativa de admissão.
  [Recibo de admissão](../out/diagnostics/repertoire_20261119/standing-renderer-build-admission.jsonl).

## 2026-11-19 · Emulicious no Windows e calibração das poses em pé

- A distribuição portátil oficial com Java foi instalada no perfil Deck. O
  comando efetivo para `.sms` aponta para Emulicious. A abertura via shell
  iniciou o Java incluído com o caminho completo da ROM de seis leituras.
  [Recibo](../out/diagnostics/repertoire_20261119/windows-emulicious-setup.json)
  · [Abertura pelo shell](../out/diagnostics/repertoire_20261119/windows-shell-launch.json).
- A configuração é repetível pelo bootstrap com `install --windows-emulicious`.
  O pacote oficial foi fixado em SHA-256
  `0a6737b4c709fe54dd88fb507bdf9d491205f240d68e83593e24f8414e0378b5`.
- No Debian WSL, o Xvfb recebeu um diretório privado porque o socket do WSLg
  impediu a alocação de display. A ponte ganhou espera que cobre as etapas
  de boot e coleta da publicação MFD1 completa. Em b13 o contra após
  defesa a 33 px entrou no tick 22 com 6 leituras e no 24 com 8. O replay
  registrou um tick lógico a cada dois quadros contados pela ponte.
  As duas sessões foram fechadas. Cadência em tempo real, demais casos
  e vídeo continuam pendentes.
  [Resultado b13](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/comparison.json).
- Foram calibradas 18 poses a partir dos model sheets do projeto. A composição
  inicial excedeu oito sprites por linha em 79 dos 81 pares e chegou a 13.
  Reservar quatro cores livres em P0 e mover todas as células compatíveis
  deixa pico teórico de quatro sprites por linha. Para cumprir oito, o par
  mais caro precisa mover pelo menos 13 objetos nessa contagem. A projeção
  do plano escolhido chega a 21 células de fundo na formação de 33 px.
  O patch atual comporta sete. Faltam composição e sobreposição, orçamento
  de VBlank e QA no emulador.
  [Procedência](../data/source_art/sprite_studies/scene02_standing_20261119/generated-art-receipt.json)
  · [Medição provisória](../out/diagnostics/repertoire_20261119/standing-art-b05/staging-report.json).

## 2026-11-19 — Primeira família do repertório em bancada

O dono autorizou produzir os quatro normais em pé por personagem,
com toque na soltura, sem buffer e sem cancelamento. Autorizou o ensaio
de guarda alta, abaixada e aérea. Os golpes abaixados/aéreos, especiais,
Super e agarrão aguardam a avaliação da primeira família.
[Decisão](decisions/alis-hayato-standing-normals_owner_20261119.json)
· [Comandos e índice de provas](repertorio_alis_hayato_provas.md).

As duas ROMs de 32 KiB mantiveram os SHA da
[matriz original](scene02_hayato_alis_qa.md). Tentativas pelo wrapper
com os dois binários voltaram a falhar em `pactl` ausente no Debian/WSL,
antes de abrir sessão. O contragolpe nos ticks 22 e 24 continua previsão
do piloto para verificar no framebuffer e no trace por SHA.

O núcleo C agora recebe fichas por normal em pé e separa o candidato de
input do comando que a máquina de estados aceita. A bancada cobre 256
casos de perto, limite, pixel além e guarda, com P1/P2, face e 6/8
invertidos, usando artefatos sintéticos para os seis novos golpes.
Passe de toque, carga e acorde estrito/uma leitura inclui soltura
parcial, tentativa bloqueada e rearmamento. Movimento Q12.4 mede 32/43
ticks de caminhada para Hayato e 37/37 para Alis no avanço/recuo de
32 px. Dash, freio, salto e guardas são ensaios independentes do
renderizador. A guarda abaixada no primeiro tick de chão foi corrigida
e ganhou regressão.

Próximo elo: qualificar Emulicious e reproduzir a matriz dos dois
pilotos; produzir as seis sequências laterais em pé que faltam antes
de ligar os novos IDs ao renderizador. Sem candidata nova, vídeo
contínuo, timestamps, VBlank ou FPS deste incremento.

## 2026-11-19 — Cena 02, comparação de 6 e 8 leituras com ROMs candidatas

O dono pediu manter as duas durações de pressão para comparação e seleção
posterior. A [decisão de piloto](decisions/hayato-alis-scene02_owner-comparison_20261119.json)
registra os parâmetros comuns e preserva o corte v4/v7. A
[matriz de QA](scene02_hayato_alis_qa.md) identifica os dois binários de
32 KiB, o SHA de cada um, controles, casos previstos e limite de validação.

GD05 entrou no consumidor com combate pelos dois controles, guarda, recuo,
vida, contato único por golpe e recuperação. As duas durações passaram
40 casos de regras nativas com caixas sintéticas e quatro cruzamentos
simultâneos. MFD1 separa pose de contato, solicitada, residente e apresentada,
e registra o tick livre e as caixas antes da resolução. Três testes nativos
confirmaram a serialização/decodificação. O mapa coloca o bloco em `0xC770`.

R03 simultâneo com preparação e estocada de Alis é alcançável nas duas
variantes. A correção usa uma disposição fixa por pose, com Hayato à frente
na SAT e partes de Alis no BG, limitando a 8 por linha e 50 na SAT nos
56 cruzamentos estáticos. São 249 padrões residentes e 7 alternados para
Alis, com até 7 células de BG dinâmico. A área de jogo compartilha o chão
da placa diagnóstica e usa HUD de vida dos dois jogadores. Os símbolos
em 65 arrays foram conferidos byte por byte com cada ROM.

O SDK nativo passou no smoke de 16 KiB com um job. O compilador portátil
ficou em NTFS após a promoção por rename falhar nos dois volumes.
Usou-se o `cc1` do arquivo oficial do SDCC e um makefile de ambiente
privado para assegurar a interpretação POSIX do make. Corrigida a
normalização de separadores no gate de procedência do wrapper; os
pre-gates das duas builds passaram. O Debian do WSL lê a raiz registrada,
mas o inventário atual indica Java/Javac, Xvfb, Bubblewrap, FFmpeg e
PulseAudio ausentes. Gameplay em ROM, vídeo do par, áudio capturado,
VBlank e FPS funcional permanecem pendentes, assim como provas da
reação visual e da qualidade artística em 1× durante a partida.

## 2026-11-19 — Cena 02, preparação do piloto Hayato × Alis

**Estado: contrato de combate pendente.** Hayato é o foco e Alis é a rival
proposta para a Cena 02. O confronto já tem uma régua de alcance e uma
direção do proprietário para a estocada forte de Alis no botão 1 segurado.
A resposta a testar é a estocada após defender ou provocar o erro do corte,
com tempo e alcance suficientes depois do recuo. O comando do corte curto
continua sem decisão aplicável à luta. O limiar de 12 leituras é do viewer.
J.J. permanece controle artístico independente: a amostra aceita usa a
fonte v6 e 7/4/2/3/6, sem emissão, hit ou defesa. O congelamento do Social
permanece vigente. [Régua e comando de Alis](duel_reach_reference_v2.md).

### Material conferido neste checkout

| Papel | Arquivo e SHA-256 verificado | Limite do aceite |
|---|---|---|
| Identidade de Hayato | [Concept v2](../data/source_art/concept_art/hayato/hayato_concept_sheet_v2_harmony_proposal.png) `a8dc147836a8c703ecdda0a4bce87d2cd41efa6abaff6f55340a04bb3fccdf95` | Referência visual do personagem. |
| Atuação e exposição do corte | [Fonte v4](../data/source_art/sprite_studies/hayato/review_drafts/cps2_short_cut_v2/sequence_v4/cut_source.png) `9302a78a9624080aace9234cd5960d43bb8c241d4c498c47a7e628ce0d9ba09d` | Desenhos e tempos v7 `8/1/2/7/2/5`, com trajetória original da lâmina. [Decisão](decisions/hayato-short-cut-timing-only_owner_approval.json). |
| Régua comum | [Página 1](../data/source_art/roster_harmony_review/waku_waku_7/harmony_waku_waku_7_lineup_v1_part_01.png) `b48e9e5b894751a3a2dfd332977703de9a456155457f474a94428f16a7c1f8ba`, [página 2](../data/source_art/roster_harmony_review/waku_waku_7/harmony_waku_waku_7_lineup_v1_part_02.png) `602721b493d6a5a964e3055d840f4117425aced9e97df3063637bf669c1ab5ce` | Comparação visual. A régua v2 usa 75 U para ambos; a guarda de Hayato tem 58 px da coroa ao chão. Os 68 px de Alis são um alvo de calibração ainda pendente no sprite lateral. |
| Identidade de Alis | [Concept v4](../data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png) `b7b01f18ae71b5538404935f4ce2e1cf6b10991dde6522c6697c0b52ab6ede95` | Referência de identidade visual, figurino e equipamento. O sprite lateral da Rodada 1 ainda precisa de validação de escala e leitura. |

`audit_animation_contract.py --self-check` passou. A [folha de exposição](../out/diagnostics/duel_readiness_20261119/hayato-short-cut-exposure.json)
confere `hayato_short_cut` no contrato v4 SHA `fc54e2068f71a6c63c8acef0909fa8148aa99dc8e1eb2a016e3eb6445e6542ec`.
Os intervalos de R01–R06 são `[0,8)`, `[8,9)`, `[9,11)`, `[11,18)`,
`[18,20)` e `[20,25)`. A janela ativa segue aberta em GD02. A guarda, os
desenhos, as exposições e os controles históricos continuam disponíveis.

### Composição estática e primeira divergência de hardware

`audit_sprite_line_sim.py --self-check` passou. Foram combinados os metasprites
existentes das duas faces, no mesmo piso, com 52/60/68 px entre pivôs, sem
alterar pixels. As distâncias vêm da sonda e servem apenas à amostragem.
Os headers e registros de conversão foram identificados por SHA na
[medição estática](../out/diagnostics/duel_readiness_20261119/static-composition.json).

| Par | Combinações com mais de 8 sprites por linha | Pico por linha / SAT | Paleta P1 opaca | Atlas / atual + próxima |
|---|---:|---:|---:|---:|
| Hayato × Alis, lâmina de Alis dividida com BG conforme a sonda | 96/168 | 10 / 54 | 15 códigos | 578 / 107 padrões |
| Hayato × J.J., conversões v5 com equivalência v6 por recibo | 126/252 | 10 / 57 | 16 códigos | 701 / 113 padrões |

Os atlas contam as duas faces e um padrão vazio, após deduplicação em códigos
SMS. A residência de atual + próxima é uma estimativa para avanço na mesma
face. Para Hayato × Alis, o máximo de padrões novos numa transição ensaiada
é 1.728 bytes; a decomposição existente de Alis também reserva 15 padrões
de BG incluindo seu HUD diagnóstico. Faltam cenário e HUD do duelo, agenda
de streaming, mapa de VRAM do par e medição de VBlank. Com J.J., a união de
16 códigos opacos exigiria remapeamento para caber na P1 compartilhada.

Com a rival em guarda, R02 já excede oito na montagem com Hayato à direita.
R03, nos ticks de exposição 9–10, chega a 10 por linha nas duas faces.
Testar as [64 fases de Hayato](../out/diagnostics/duel_readiness_20261119/phase-search.json)
reduziu as violações a 87/168 e conservou o pico. Permitir também outra
[fase para Alis](../out/diagnostics/duel_readiness_20261119/r03-joint-phase.json)
reduziu o mínimo de R03 × guarda a 9. Com
[grades horizontais independentes por faixa de 8 px](../out/diagnostics/duel_readiness_20261119/horizontal-band-packing.json),
R03 × guarda chegou a 8 por linha e 47 na SAT em ambas as faces, com igualdade
de pixels verificada. Quatro das 56 composições a 60 px ainda chegam a 9
no melhor arranjo ensaiado: R03 × preparação e R03 × estocada nas duas faces.
O ensaio muda a grade por combinação, sem demonstrar layout único por pose,
prioridade no framebuffer ou alcance dessas combinações pelas regras da luta.

### Retomada e matriz de observação

O primeiro elo sem prova é **input consumido → ação autorizada → contato**.
Fechar GD01/GD02 para este recorte com o dono: comando do corte, limiar e
precedência da estocada, regra de guarda, janela e caixas do corte, dano,
recuo e condição de volta ao controle para ambos. Vincular a pose de guarda,
de reação ao hit e de resposta de Alis à direção aprovada antes de integrá-las.
Em GD05, tornar observáveis input consumido, estado/tick lógico, pose
solicitada, residente e apresentada, caixas, resultado de contato, reação e
primeiro tick livre de cada ator. Comparar em imagens nativas e em velocidade
normal a altura anatômica, apoio, materiais, mão e equipamento nas duas faces.

| Caso | Pré-condição e esperado | Observado na ROM do duelo |
|---|---|---|
| Acerto perto e no limite | Ambos livres, sem defesa, no ponto interno e no último pixel válido das caixas decididas. A pose ativa aparece, o contato ocorre uma vez e causa dano e reação no tick estabelecido. | Pendente. |
| Erro a 1 px além | Repetir com diferença de um pixel fora do alcance aprovado. Sem dano ou hitstun; corte recupera e uma resposta executável pode punir. | Pendente. |
| Defesa e resposta | Repetir a distância de contato com guarda legal. Registrar recuo e primeiro tick livre dos dois; começar a estocada no primeiro comando permitido e verificar alcance após o recuo. | Pendente. |
| Face/P1/P2 e canto | Repetir o caso crítico invertendo lado e controle, com o defensor junto ao limite da arena. Comparar caixas e consequência espelhadas, clamping, prioridade visual e SAT. | Pendente. |

Os checks deste lote foram leves, no Python nativo do Windows. A amostra do
host registrou 61% de CPU, 7,01 GiB disponíveis, 1.546 páginas lidas/s e
zero escritas/s, fila de disco zero, 47,49 GiB livres no Btrfs e 43,41 GiB no
temporário NTFS, sensor disponível a 52,85 °C e trip de 99,85 °C. O Debian
estava parado e a toolchain nativa sem SDCC na rota registrada. A QA privada
requer Linux qualificado; o handoff anterior registra a ausência de `pactl`
no último uso do Debian. Nenhuma build, ROM candidata, trace, mídia de runtime,
medição de FPS/VBlank ou sessão para limpar foi criada. Ao retomar, confirmar
capacidade e toolchain com um job, reservar destino novo e vincular fonte,
conversão, símbolo, ROM e sessões pela mesma cadeia de SHA. Em execução
contínua medir ao menos duas janelas NTSC válidas de pelo menos 58 FPS, dispersão
máxima de 2 e pior frame com duelo, HUD, cenário e áudio ativos.

## 2026-11-04 — decisão do proprietário: congelar Social e recomeçar o sprite do zero

> **DECISÃO VIGENTE DO PROPRIETÁRIO — 04/11/2026: SOCIAL IN-GAME CONGELADO.**
> Os sprites e animações atuais do Dr. Social não devem ser continuados,
> retocados, convertidos, integrados ou promovidos. Retomada futura: novo desenho
> do zero, a partir do concept/model sheet e das referências de tamanho mantidos.
> A cena D01 fica experimental. J.J. e Hayato/Kenseiden permanecem validados no
> recorte realizado. [Registro do congelamento](dr_social_ingame_freeze_20261104.md).
> As orientações anteriores para produzir o Social ficam históricas/suspensas.

Estado operacional: `frozen`. A referência de identidade mantida é o model sheet
CPS2 v4; imagens de tamanho e a cena experimental estão listadas por hash na
[decisão original](decisions/dr-social-ingame-freeze_owner_direction_20261104.json).
Fontes e derivados anteriores ficam preservados como histórico; seus ponteiros
ativos de produção são retirados do catálogo. Não apagar/mover imagens.
A matriz antiga é uma fotografia do pacote congelado, não um backlog autorizado.
J.J.: fonte v6 e tempos 7/4/2/3/6. Hayato: fonte v4, perfil de tempos v7
8/1/2/7/2/5, sem deformação de lâmina. Ambos reafirmados no recorte existente.
Nenhum runtime/ROM/asset foi modificado e nenhuma medição foi refeita.

## Régua de duelo — Alis frente a Hayato

[Prancha v2 e salvaguardas](duel_reach_reference_v2.md). O proprietário
rejeitou a escala do primeiro estudo porque a projeção do pé avançado
da Alis foi usada na comparação com a guarda lateral de Hayato.
A régua agora usa os 75 U de ambos na prancha aprovada do elenco.
Corpo, lâmina e escudo têm medidas próprias, e os 36 px de alcance da
versão anterior foram retirados. A categoria é normal forte de espada no
botão 1 segurado. Próximo passo: conferir corpo e equipamento em vistas
equivalentes, desenhar o par lateral e medir a estocada por pose. Limiar
de controle e validação na ROM continuam pendentes.

O proprietário autorizou a rodada 1 com sprites, botão 1 segurado, Hayato
em guarda e ROM para validação. O [prompt da rodada](alis_strong_thrust_round1_agent_prompt.md)
define a entrega e a captura no mesmo SHA. O
[registro candidato de curadoria](curation_candidates/2026-11-15_alis_duel_reach_projection.json)
guarda o erro da primeira régua, o que foi conferido na revisão e os pontos
para testar com a implementação. As observações desta rodada serão preenchidas
a partir do material do agente.

### Rodada 1 — estudos iniciais, ainda sem candidata

Duas tentativas exploratórias de arte estão preservadas com prompts, hashes e
limitações em [strong_thrust_round1](../data/source_art/sprite_studies/alis/strong_thrust_round1/README.md).
A segunda removeu a linha de chão, mas não os resíduos de cor; ambas seguem
reprovadas para integração e sem calibração ou revisão de animação. O caminho
diagnóstico atual de `src/main.c` dispara pose no toque e não demonstra a
resolução de contato neste recorte. Não houve mudança no runtime, build, ROM,
sessão de emulador ou teste de FPS nesta etapa. Permanecem todos pendentes:
arte nativa, comando segurado e rearme, distâncias/espelho, recursos, vídeo,
pior frame e FPS funcional §133. Retomar pelo tratamento das fontes e pelos
gates do pedido, sem promover os estudos como sprite ou prova de jogo.

Retomada: `keyposes_01`, `keyposes_02_shield`, `sequence_01` e
`sequence_02_shield` foram geradas
e preservadas no mesmo diretório com prompts e hashes. A edição expôs a pega
do escudo; a segunda sequência a incorporou, mas apresenta interior marrom
inconsistente e resíduos de cor. Continuidade de equipamento, escala e recorte
permanece pendente. Uma VM de outro trabalho estava ativa
ao medir o host (aprox. 2 GiB RSS; CPU PSI avg10 34,83%, 6,0 GiB disponíveis,
swap sem atividade na amostra; 40 GiB livres). Pelo contrato de uma carga
pesada por vez, build e sessão Emulicious foram adiados, sem encerrar a VM.
Não há ROM nem SHA desta rodada; retomar arte/integração e reavaliar o host
antes da build e QA. Nenhum resultado de FPS ou pior frame foi medido.

Retomada após o segundo parecer: o visualizador recebeu, sob
`MOF_ALIS_STRONG_HOLD`, contagem provisória de 12 leituras, disparo único e
rearme na soltura, com sondas de contagem/latch/disparos. Nenhum manifesto da
Alis ou fonte nativa foi ligado; o código não foi compilado nem testado em
ROM e o corredor de probes deve ser auditado. Casos e limites em
[alis_strong_thrust_round1_qa.md](alis_strong_thrust_round1_qa.md).
A tentativa de edição localizada voltou a alterar regiões fora do alvo;
foi preservada com comparação negativa. Criados estudo hipotético do escudo
e esboços temporais normal/lento, ainda sem avaliação contínua e sem registro
de pivôs: detalhes e hashes no README da rodada. A VM concorrente permanecia
ativa; não houve build, emulador ou medição de desempenho desta rodada.

Nova retomada: `C7F9` voltou a ser tempo decorrido da pose e `C7FC` registra
pressão; `C7FA/FB` continuam latch/contador. A bancada relatada pelo
coordenador aprovou o ramo anterior nos casos 11/12/13, longo, soltura e
reentrada; após separar probes ainda faltam compilação SDCC, auditoria do
corredor e QA da fronteira do último tick da recuperação na ROM. Uma edição
de alpha por máscara alterou 2.224 pixels e nenhum fora da máscara; a revisão
artística permanece pendente. Esboço refeito pelo apoio traseiro diminuiu o
recuo aparente de 27 para 1 px no vídeo. Pranchas 1×/4× com Hayato usam
escala provisória não calibrada. Métodos, hashes e limites no README da
rodada. O wrapper falhou `FAIL_AMBIENTE` ao procurar `pulseaudio` após
`pactl info` retornar conexão recusada; operações leves sem áudio usaram a
`.venv` existente. VM concorrente continua ativa e a pressão de I/O aumentou;
build/Emulicious não executados, nenhum SHA de ROM ou FPS novo.
O self-check e a auditoria estática de `audit_debug_markers.py` passaram
para o projeto; `audit_probe_corridor.py --self-check` também passou, mas
nenhum `.map` da candidata foi auditado porque a build ainda não existe.

Quarta revisão: a edição limitada de alpha preserva o exterior, mas a máscara
binarizada antes/depois é idêntica para limiares 25, 64, 128 e 224. Não há
melhora demonstrada na saída convertida. O registro pelo apoio traseiro
melhorou o enquadramento, sem aprovar movimento, e a escala de Alis continua
provisória. Direcionamento completo em
[parecer](alis_strong_thrust_round1_coordinator_review.md) e na continuação
do [prompt](alis_strong_thrust_round1_agent_prompt.md); hipóteses de execução
e auditoria estão no registro candidato de curadoria. O marco segue ROM com
SHA e provas, não uma nova folha estática.

### Rodada 1 — integração preparada, ainda sem ROM (2026-11-15)

Foram criados fontes indexados diagnósticos, paleta explícita e um ramo
`MOF_ALIS_ROUND1` no consumidor. A conversão com compensação de aspecto
expôs pico de dez sprites/linha; a tentativa de abaixar a lâmina foi a onze
e permanece preservada. A divisão experimental de fragmentos da lâmina para
BG produziu 24 manifestos estáticos para quatro poses, três distâncias e
duas faces: máximo 53 na SAT e oito/linha. Reconstrução dos dez metasprites
e quatro mapas BG por índices passou, com 246 padrões SAT e 14 BG mais HUD.
Hayato convertido coincide em RGBA com sua guarda v7 nas duas faces. A
escala corporal, a arte, a prioridade da lâmina sobre o rival e as escritas
dinâmicas continuam pendentes; BG e rival se sobrepõem em 25/2/0 pixels
perto/limite/fora na inspeção estática. `audit_tilemap_bounds` registra
entradas dinâmicas não provadas. A sequência usada ainda é o estudo
`sequence_01`, com quatro poses, não a arte final corrigida.

O manifesto candidato é `.mddev/alis_strong_round1_diagnostic_build.json`;
o header gerado tem SHA-256
`c93fc4ebcd4a11b86e521758058394796aa76b6e46a9f35520ad346dc0e17a46`.
[Roteiro de QA](alis_strong_thrust_round1_qa.md) inclui controles, probes,
limites e casos. Pranchas/vídeo **offline, não framebuffer** em
`out/diagnostics/alis_strong_thrust_round1/converted_grounded_preview/`;
receitas e comparativos no README do estudo. O wrapper passou ao apontar
`XDG_RUNTIME_DIR=/run/user/1000` para o servidor de áudio já existente,
sem reiniciá-lo. A VM concorrente mudou de PID e continuou ativa (~2 GiB
RSS); não se compilou nem abriu Emulicious. Não existe SHA de ROM desta
rodada e nenhum teste de runtime, pior frame, FPS ou qualidade foi aprovado.
Próximo: com margem e wrapper apto, compilar sem afrouxar gates, corrigir
eventuais falhas e validar corredor, input, BG/PNT, captura, FPS e pior frame
no SHA; em paralelo, fechar calibração 68 px e revisão artística temporal.

Proteção local desta fotografia de trabalho: `.runtime/backups/alis-strong-round1-20261115-wip.zip`,
10.993.754 bytes, SHA-256
`4250af5ea1209f1632e7daf7755f06cfbe5bbe0f62c78787a173b8757c720888`;
460 arquivos verificados por SHA e CRC no recibo JSON homônimo. Revisados tamanho,
escopo e nomes; arquivo acima de 10 MiB, fora do Git, no mesmo disco e sem cópia
externa. Abrange as fontes e diagnósticos listados no recibo, não o projeto inteiro;
esta anotação é posterior à fotografia arquivada.

Retomada posterior: a VM anterior deixou de aparecer, mas a amostragem do host
mostrou pressão de CPU sustentada (PSI `some` avg60 21–28%, CPU frequentemente
sem folga); build e sessão continuam adiadas por estabilidade. Preparados cinco
roteiros da ponte para toque, 11/12/13 frames e pressão longa/rearme, sem
confundir frames VDP com leituras da ROM. Uma tentativa adicional de limpar a
franja alterou pixels fora da área pedida e não demonstrou melhora; preservada
no README da rodada. A comparação convertida recebeu marcas dos intervalos
opacos dos dois pés, em 1×/4×; avanço zero e escala corporal continuam
provisórios. Nenhum SHA de ROM, vídeo de framebuffer ou FPS foi produzido.
Fotografia incremental local no mesmo disco:
`.runtime/backups/alis-strong-round1-20261115-followup.zip`, 726.109 bytes,
SHA-256 `cd22ba29edc3dfab94da42988120c03b2f3867b52a0bc24a607604b297366182`;
15 arquivos verificados por SHA e CRC, recibo JSON homônimo. Não substitui a
fotografia anterior nem cópia externa; esta anotação é posterior ao arquivo.

Retomada seguinte: uma máscara retangular da tentativa gerada preservou os
pixels externos e, com a paleta de material fixada, removeu um único pixel
cinza da guarda **convertida**; extensão e Hayato ficaram idênticos. A paleta
automática havia alterado cores fora da região, por isso foi feito controle
com paleta fixa antes do comparativo. Pranchas e receitas no README da rodada,
em `fringe_converted_comparison_01/`. Isso é um ganho local nas chaves
exploratórias, não uma correção da sequência `sequence_01` ligada ao ramo
experimental e não aprova escala ou atuação. O host reiniciado manteve pressão
de CPU sustentada (PSI avg60 entre 23% e 28% nas amostras); build e Emulicious
não foram executados. Ainda não há SHA de ROM, resultado de input ou FPS.
Foi preparado também `tools/alis_input_trace.py` para ler as sondas a cada
frame em sessão privada de SHA informado, inclusive a tentativa de alinhar o
limiar ao último tick; somente o self-check de offsets passou. O coletor não
foi executado em emulador, e stepping não mede FPS. Instruções e limitações
estão no roteiro de QA.
Fotografia incremental local no mesmo disco:
`.runtime/backups/alis-strong-round1-20261115-mask-conversion.zip`, 781.302 B,
SHA-256 `533e5b6313a8117ebb71d2e433506316e724184cbc66649a894cdf5cde5b0ab5`;
39 arquivos verificados em SHA e CRC, recibo JSON homônimo. Depende das
fotografias anteriores, não é cópia externa e antecede esta anotação.

Em 2026-11-16, teste do coletor com ponte simulada conferiu ordenação das
amostras, soltura e preparação para o último tick, sem executar ROM. Estudo
manual de segmentos em `scale_landmarks_01/` aponta possível disparidade:
torso da guarda cerca de 18,34 px contra 18,76 da referência, mas segmentos
da perna cerca de 8,71/10,77 contra 13,47/15,45 px. Marcos são estimados e
quadril/ombro estão parcialmente ocultos; revisar antes de decidir escala ou
redesenho. A amostragem do host encontrou CPU PSI sustentada em torno de 20%
na janela de 60 s, sem VM concorrente; build e QA reais seguem adiadas.
Em `weapon_landmarks_01/`, marcas manuais de mão/base/ponta da sequência
sugerem lâmina projetada de 18,0/12,7/14,7/14,3 px nas quatro poses, contra
27,3 px na referência neutra lateral projetada. Perspectivas diferem e os
pontos são estimados; é diagnóstico de possível variação de equipamento, não
comprimento aprovado ou comparação de katana no mesmo ângulo.
Redesenho `keyposes_redraw_proportions_01.png` e receitas preservadas no README
da rodada. Após registro de chão, o conversor reprovou extensão com nove
objetos por linha; a busca geométrica de fases dos dois atores não encontrou
solução na posição testada. Uma divisão experimental de 12 pixels da ponta
para BG reduziu o pico a oito para as duas poses estáticas nessa posição;
outras faces/distâncias, camadas, transições e runtime continuam pendentes.
O redesenho não tem sequência nem foi integrado à build experimental.
Na projeção offline `redraw_reach_preview_01/`, o limite provisório por
contorno na altura Y=109 gera deltas 8/0/−8 px. A parte da ponta transferida
para BG se sobrepõe ao alvo em 11/2/0 pixels perto/limite/fora: a camada de
fundo pode ocultá-la. A vista esquerda é espelho offline, não asset validado.
Incremento da projeção preservado no mesmo disco em
`.runtime/backups/alis-strong-round1-20261116-reach.zip`, 116.571 B, SHA-256
`277b936dbf3ca0cd44c79fcae955dec5f02513df277bb686a1e838f457b6f82a`;
seis arquivos conferidos em SHA e CRC, recibo JSON homônimo. Depende das
fotografias anteriores, não é backup externo e antecede esta anotação.
Reprodução do split em diretório novo foi byte a byte idêntica para imagens,
manifestos e recibo. Incremento local no mesmo disco:
`.runtime/backups/alis-strong-round1-20261116-split-repro.zip`, 110.998 B,
SHA-256 `3123d505de938d500b0cd508ac683504f115b5bc3be988762a89aab224ba206c`,
11 arquivos verificados, recibo JSON homônimo; depende das cópias anteriores.
Fotografia incremental no mesmo disco
`.runtime/backups/alis-strong-round1-20261116-redraw.zip`, 3.376.842 B,
SHA-256 `605e19f331e95be1371ac30765c017de0db57d095ebac9cc924993aae878a9c3`;
70 arquivos conferidos por SHA e CRC, recibo JSON homônimo. Não é backup externo
nem pacote completo; esta anotação é posterior à fotografia.

Quinta revisão (2026-11-16) no [parecer de coordenação](alis_strong_thrust_round1_coordinator_review.md).
Reexecutados simulador, dados das 24 cenas estáticas e coletor com ponte
simulada. O redesenho melhora expressão, apoio e identidade do escudo, mas
tem duas chaves e toma 9 sprites/linha na extensão só em SAT. O split
estático cai a 8 e pode ocultar até 4 px da ponta na linha da estocada
próxima. O manifesto experimental ainda usa `sequence_01`. Prioridade:
calibrar corpo neutro, completar a sequência do mesmo desenho e testar
camada e timing em ROM com fonte identificada. Sem ROM da Alis na revisão.
O candidato de curadoria registra implementação, coordenação e auditoria.

[Parecer de coordenação da rodada 1](alis_strong_thrust_round1_coordinator_review.md).
A tarefa do produtor encerrou com a entrega parcial. A pose de extensão é
aproveitável como referência gestual. Corrigir primeiro as duas chaves de
guarda e extensão, com escala lateral, apoios e equipamento cotejados com
Hayato. Depois continuar a mesma rodada até a candidata e as provas. As
observações e a medição de alfa foram acrescentadas ao registro de curadoria.

Segunda revisão no mesmo parecer: quatro PNGs adicionais inspecionados,
com delta medido e escopo técnico inalterado. A correção da pega mudou o
material do escudo e pixels na área da guarda que devia ser preservada.
Próximo passo: edição localizada e prova de duas chaves comparadas a Hayato,
esboço temporizado antes do acabamento e input trabalhado de forma
independente da build. O candidato de curadoria agora registra também as
lacunas do direcionamento e do método de auditoria.

Terceira revisão no [mesmo parecer](alis_strong_thrust_round1_coordinator_review.md):
ramo de pressão passou em teste de bancada do C. Sem build da Alis.
`C7F9` foi reaproveitado para pressão e precisa de prova distinta de
exposição de pose. O esboço tem 8/7/3/6/12 quadros por ciclo, mas a
centralização faz ambos os apoios irem para trás na extensão. A edição
local voltou a alterar regiões protegidas. Próxima ação: trocar o método
de correção, registrar as chaves e o esboço pelo pivô, preservar ambas
as observações de input/timing e ligar a candidata Alis/Hayato.

## 2026-11-03 — reprodução local do viewer da provocação v3

Os registros v2/v3 verificam os JPEGs locais, a guarda e a paleta pelo
histórico versionado. Staging reproduziu cinco PNGs lógicos e dois
intermediários byte a byte. Originais ausentes/adulterados e derivados
preexistentes divergentes foram recusados sem sobrescrita. A execução do
adaptador em staging reproduziu o header, nove PNGs e oito manifests de cena.
Pico oito no par fixo de construção.

A candidata `out/candidates/20261103_operational_social_taunt_v3`, SHA-256
`1fa0dfed9df315760362a4cef562150b85e0021791cfc4111caac9cef95c869d`,
conciliou com o recibo da árvore atual. Só o dia SDSC e o byte alto do
checksum SEGA mudaram em relação à ROM v3 histórica. Corredor 1784 B.
Na sessão privada `7489ee568a9f49c7a37c214f9e3a431b`, o botão 1 foi
consumido, a ROM entrou na pose 1 e voltou à guarda de framebuffer
idêntico. O vídeo por stepping tem 88 quadros nativos e oito imagens
distintas. Bundle válido e processos próprios encerrados. Provas em
`out/evidence/20261103_operational_social_taunt_v3_replay/`; a primeira
coleta, que encontrou a animação automática em curso no baseline, fica em
`out/evidence/20261103_operational_social_taunt_v3/`.

O gesto é o controle diagnóstico do viewer. FPS e VBlank da ROM nova
seguem sem medição. Decisões de arte, comandos e Social61v5 seguem abertas.

## Parecer atualizado e contexto integral para agente substituto — 2026-11-02

Reavaliado `587763cf1e192ada7bfbed4510d27fde240017b5`: terminal da provocação
medido, sem novos pixels/build/ROM. Prancha 1×/8× inspecionada; hashes de prancha,
ROM, vídeo, model sheet e jab conferidos. Nenhuma nova sessão nesta revisão,
pois a ROM v3 permanece a mesma e os testes anteriores conservam seu escopo.

[Prompt integral vigente para outro agente](dr_social_complete_character_artist_prompt_v1.md)
agora reúne missão/identidade/método, fontes aprovadas por hash, arte histórica,
receitas, baseline e evidências, cobertura completa, controles/cena 10, próximas
ações e proteção do WIP. [Parecer atual](character_move_showcase_standard_v1.md).
Prompts de checkpoint históricos deixam de ser a entrada para o sucessor.

Parecer: não há justificativa demonstrada para adicionar quadro apenas para
os 3 px/2,5 px da mão. Apresentar candidata v3 para julgamento artístico;
a continuidade global de cabeça/corpo/material entre bloco final e GQ03 segue
pendente. Medidas de grupos brancos/larguras não aprovam anatomia ou fluidez.
Se houver correção, tratar o conjunto afetado, não deslocar o salto entre poses.
Personagem ainda incompleto: 20 not_started e sete lacunas, além dos candidatos.
Produção independente autorizada continua enquanto houver decisão específica.

Scripts de registro contêm caminhos pessoais da sessão do produtor; originais
estão preservados no projeto. Sucessor deve usar fontes/hash locais e reparar
só ingestão/reprodutibilidade necessária, sem depender dos créditos anteriores
ou inventar outro pipeline. Recibo desta revisão:
`out/diagnostics/social_new_agent_handoff_20261102/review_receipt.json`.


## Provocação 1, terminal medido, candidata sem pose nova — 2026-11-02

A passagem TA08→guarda foi lida no vídeo da ROM v3
`47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`,
quadros 58, 70 e 78. As solas encostam em y=151. A luva livre sobe de y=112
na TA07 para y=101,8 na TA08. Até a guarda faltam 3 px para cima e 2,5 px
em direção ao rival; as caixas se tocam em y=100. A luva da bengala fica
em y=111 nos dois quadros. A coroa da TA08 está em y=81 e a da guarda em
y=83. A 10% da altura da fonte a largura relativa é 0,21 nas quatro poses.
A 15% as chaves geradas medem cerca de 0,25 e a guarda 0,18; TA06 e TA07
já têm essa largura, então corrigir só a TA08 mudaria o corte de lugar.
O corpo novo continua 877 px. A guarda oficial permanece 836 px no magenta
estrito; a chave de canto desta leitura deu 834.

No tronco do framebuffer a TA08 mistura o código 20 (120 px), o 57 (95) e
o 56 (72). A guarda concentra o 56 (204) e o 20 (106). O claro 57 volta ao
56. O colapso antigo, sem nenhum 56, não voltou. Não desenhei outro quadro
e não recompilei. A hipótese segue 8/8/10/20/10/12/8. O VBlank selado desta
ROM, medido pelo designer, continua 3000 frames, vline_min 207, derrame
zero. As janelas 59,64763127522857 e 59,62493848380926 permanecem. Arte,
GQ03, jab, comando, áudio, pacing e pacote aguardam o proprietário.
Prancha 1× e 8×: `cps2_keys_v1/preview/TA01_cycle_v3_terminal_sms_8x.png`.
Recibo: `cps2_keys_v1/proposals/TA01_cycle_v3_terminal.json`.

## Revisão dab0181: VBlank selado medido e terminal em revisão — 2026-11-02

ROM v3 `47ab4663…` e vídeo conferidos; direção ao rival e retirada do azul escuro
constatadas em fontes/quadros capturados. TA08 acrescenta recolha. Não aprova
arte, GQ03, ligação com jab, comandos ou pacote. Prioridade agora é revisão
localizada TA08→GQ03, não outra rodada inteira de poses. Altura 72 px dentro
da faixa não prova constância anatômica: fonte 877 px vs 836 da guarda exige
comparação de âncoras, sem esmagar poses ou inventar limite por quadro.

Nova sessão própria `dddf8c438ced42aba3f83c1434664419`, encerrada. Mesma ROM,
sem rebuild ou alteração de pixels/código. Self-checks passaram; fonte do commit
confere com input do build, mapa correspondente passou corredor de sondas
(folga 1784 bytes). `measure_worst_frame.py`: 90 s sem leituras, selo 3000 frames,
PASS, vline_min=207, vovf_delta=0, done=1. Não aprova streaming/duelo/CPU inteira.
O rótulo genérico TITLE do snapshot é estado 0, guarda neste viewer, sem série
individual de poses. Bundle passou. As duas janelas FPS do produtor nesta ROM
foram conferidas, não repetidas. Áudio e pacing percebido continuam pendentes.

[Revisão e prompt vigentes](character_move_showcase_standard_v1.md).
Recibo: `out/diagnostics/social_taunt01_cycle_v3_review_20261102/review_receipt.json`;
relatório: `out/evidence/sessions/dddf8c438ced42aba3f83c1434664419/worst_frame/taunt_v3_designer_worst.json`.
Não repetir testes sem mudança nem adicionar quadros por rotina: identificar
defeito terminal concreto e corrigir o delta, ou apresentar candidata para
julgamento artístico. Resultados de v3 não são herdados por nova ROM.


## Provocação 1, continuidade do assentamento — 2026-11-01

O assentamento v1 olhava para o lado oposto já no JPEG, e o azul escuro
caía no código SMS 20. A altura 73 vinha de um corpo gerado 6% maior, com
as mesmas razões de ombro, quadril e sola. Não foi esmagado. O ciclo v3
troca esse quadro por um punho na cintura, olhar para o rival e casaco
ciano, e acrescenta a subida da mão até o peito. A guarda continua a GQ03.
A hipótese de tempo passou a 8/8/10/20/10/12/8. Não é frame-data.

ROM `47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`,
32 KiB, viewer `MOF_CPS2_SAMPLE 10`. Sessão
`909ac83e4a4e476e91d6676aba3be58c` fechada. Vídeo de 360 quadros, SHA
`66a98981cd85f175586613d3ee444e798dfa57937f087d7cc4b7e11c712f31f4`,
6,007736 s codificados e 6,019422882 s de coleta. O vídeo v2 permanece com
os dois relógios antigos. Pressão de seis frames: o botão 2 devolveu o
estado a 0; o botão 1 chegou ao estado 4, voltou a 0 e um segundo toque
chegou de novo ao estado 4. São acionadores de revisão.

As poses novas ficaram em pico 8 e overflow zero, na face normal, no
espelho e no packing x=4. As janelas desta ROM foram 59,65 e 59,62, com
carga do host em torno de 8,5. As falhas da ROM v2 continuam no recibo
antigo. Não há aceite de pior quadro, de áudio, de arte, de GQ03, do jab
nem do pacote. O viewer não chama o PSG. Recibo:
`cps2_keys_v1/proposals/TA01_cycle_v3.json`.

## Revisão f4c5043: nova QA da mesma ROM e correção de TA07 — 2026-11-01

Provocação v2 integrada no viewer; ROM SHA `8f7687b8…` conferido, sem rebuild ou
mudança de pixels/código nesta revisão. Sessão própria do designer
`e6c6db7a8d0d4708adf4e5ee41e64116`, encerrada: medidor com self-check passou
59.652563933294665 / 59.67934459451107 FPS em duas janelas de 8 s. Carga 1 min
2.0244, contra cerca de 34 nas medições antigas. Falhas anteriores preservadas;
isso não identifica causa exclusiva nem aprova pior frame, pacing ou gameplay.
Sequências atômicas com pressões de seis frames observaram keys=16, 0→1→4→0 e
segunda execução 0→1→0. Não é teste de comando/latência competitiva. Bundle passou.
Uma tentativa inicial de pressão de um frame não estabeleceu a precondição;
registro preservado, sem claim de resposta de um frame. Recibo em
`out/diagnostics/social_taunt01_cycle_v2_review_20261101/review_receipt.json`.

[Parecer e prompt vigentes](character_move_showcase_standard_v1.md): prioridade
TA07 olha para o lado oposto ao rival e escurece amplamente corpo/casaco no SMS,
visível em quadros da captura. Resolver continuidade de fonte/cor e recuperação
antes de outra ação. TA07 73 px exige diagnóstico de proporção/pose, sem esmagar
nem aprovar exceção ao GDD. Vídeo anterior: 228 quadros, 3.804899 s codificados,
5.157165914 s de coleta; apresentação nominal não é prova de fluidez real.
68 ticks são hipótese diagnóstica, não substituem o contrato de 22 ticks.
GQ03, arte, pior frame, áudio, comandos e pacote seguem sem aceite. Portraits
independentes podem avançar durante dependência concreta; não substituem este
fechamento. Não há motivo demonstrado para reduzir conteúdo devido ao FPS antigo.


## Provocação 1 vista em movimento — 2026-11-01

O exame, o atraso curto do casaco e o assentamento rodaram no viewer
diagnóstico `MOF_CPS2_SAMPLE 9`. A guarda continua a GQ03. TA02, TA03 e TA04
foram reaproveitadas. O olhar antigo, com a mão na armação, ficou fora do
ciclo. A hipótese de tempo é 8/8/10/20/10/12. Não é frame-data e não substitui
os 22 ticks do contrato.

ROM `8f7687b85d68db923f9f3e36f4e1363c9be7136bc5438f880be7e0562e4f3f5d`, 32 KiB.
Sessão `f23c4ec169354eef89472e9500461029` fechada. O vídeo normal tem 228
quadros, SHA `b91b26a18c4717ea619f3c670d67d3d5ebf45c5b1f75da1f8ed0fb318f6fdec1`,
ligado a essa ROM. O botão 2 desligou a repetição e o estado voltou a 0. O
botão 1 abriu o ciclo, o estado passou por 2, voltou a 0 e um segundo toque
chegou ao estado 4, o exame. São acionadores de revisão. A cena 10 continua
com comando em definição.

O par das poses novas ficou em pico 8 e overflow zero, na face normal, no
espelho e no packing x=4. A cauda larga mediu pico local 5 e altura 74 e não
entrou. TA07 mede 73 px, um acima da faixa 66–72, com a sola no mesmo y=112
da guarda. Não foi esmagada de volta a 69.

Duas leituras de FPS ficaram abaixo do piso em alguma janela: 58,59/44,27 e
49,33/45,14. A carga do host estava em torno de 34. Magic SMRT e avanço de
frame passaram. Não há aceite de FPS, de pior quadro, de arte, de GQ03, do
jab nem do pacote. Recibo: `cps2_keys_v1/proposals/TA01_cycle_v2.json`.

## Revisão do designer: concluir provocação 1 — 2075484, 2026-11-01

Quatro chaves TA02–TA05 e retorno por reuso são avanço, ainda sem animação
completa observada. Pranchas lógica/SMS inspecionadas; TA05 não separa bem o
olhar avaliativo do ajuste, TA06 não foi desenhada, TA07 repete TA05. Prompts
congelam a barra do casaco; remover essa restrição para permitir a ação secundária
contratada. Retorno ao PNG GQ03 não prova recuperação natural. Exposições do
adapter 2/2/2/3 cobrem só quatro poses, não a timeline de nove entradas.

Self-checks do adaptador/simulador passaram; reavaliados 15 manifests (base,
espelho, packing x=4), todos pico 8, overflow zero, SAT 32–35. Quatro hashes
lógicos conferidos. Sem reconversão, build, vídeo, sessão de emulador ou aceite
artístico/funcional nesta revisão. Recibo em
`out/diagnostics/social_taunt01_review_20261101/review_receipt.json`.

[Parecer e prompt vigentes](character_move_showcase_standard_v1.md): concluir
esta provocação e demonstrar o ciclo no viewer oficial antes de nova ação.
Comando de revisão identificado não decide GD01/GD02, mas permite observar
animação. Handoff de conflitos recebido; não é decisão nem motivo para bloquear
playback diagnóstico. Não normalizar inclinações para altura constante; verificar
escala/âncoras comuns. GQ03 permanece candidata, jab preservado, personagem
incompleto. Depois deste checkpoint, continuar o pacote e suas pendências.


## Provocação 1 em chaves — 2026-11-01

O toque segue sem chave legal. A correção r2 da guarda abriu o vão das solas
e engrossou os óculos, mas a faixa da sola ficou em cinco colunas e o par foi
recusado. O encaixe do pé da frente continuou em cinco colunas. As duas ficam
como estudo. A guarda medida continua a GQ03, com a sola SMS fundida nas
linhas 107–109.

A provocação prevista tem quatro desenhos novos. A cabeça inclina, o punho
sobe à bochecha, a luva segura a armação e uma variação ainda se lê como a
mesma mão na armação. O retorno é o PNG exato da GQ03, passando de novo pelos
mesmos desenhos. Corpo 69 px. Par com o Ken de construção, espelho e packing
x=4: pico 8, overflow zero, SAT 32–35. Não há folga nas linhas saturadas.
TA06, a cauda, não foi desenhada. As durações são a proposta do contrato, não
frame-data. Sem ROM, sem emulador e sem comando. Jab v8 intacto. Recibo:
`cps2_keys_v1/proposals/TA01_cycle_v1.json`.

Os conflitos de GD01 estão listados para o designer, sem decisão, em
`doc/dr_social_gd01_open_conflicts_for_designer_v1.json`. A cena 10 continua
com comando em definição.

## Revisão do designer sobre GQ03 / 07e4bce — 2026-11-01

GQ03 corrigiu o shear: script de registro inspecionado só recorta/escala/
quantiza; autoria permanece no original de edição de imagem. Self-checks do
adaptador/simulador passaram. Cinco manifests reavaliados: base/espelho 32
sprites, packing x=1/4/7 34; todos pico 8 e zero overflow. Sem reconversão,
ROM ou emulador nesta revisão. Translação X não muda orçamento por linha;
cantos, FX e elenco continuam sem aceite real. Recibo em
`out/diagnostics/social_gq03_review_20261101/simulation_review.json`.

[Parecer e prompt vigentes](character_move_showcase_standard_v1.md) pedem
comparação de identidade GQ03/J01 antes de animar: quadro intermediário não
corrige deriva de cabelo/colete/proporção. Não há aprovação de substituição do
jab. Próximo resultado é ciclo completo de toque ou estado independente previsto,
com retorno; evitar outro checkpoint apenas de guarda estática.

Controles v2 permanecem proposta. Corrigir baixo-trás, bordas/hold do Super,
precedência quarto de lua+1+2 sem barra, hipótese de cancelamento do dash e
recuo/guarda temporal. Frente-frente para dash não foi localizado como decisão
aprovada nesses contratos. Recomendações de design não aprovam GD01/GD02.
Sem aceite de arte final, gameplay, animação, áudio, FPS ou personagem completo.


## Revisão do designer sobre 4f86572 — 2026-11-01

Social continua incompleto. Self-checks do adaptador/simulador passaram nesta
revisão; simulador reexecutado no manifest GQ02 confirmou 35 sprites/pico 8/
zero overflow. PNG convertido tem bbox 27×69. Não houve reconversão ou ROM.
A leitura dos scripts revelou deformação por linha de pernas/cauda e expressão
de derrota pintada por coordenadas. Permanecem estudos diagnósticos; não
satisfazem autoria visual final. Não substituir J01/jab nem alimentar a produção
com anatomia procedural. Nova candidata autoral exige nova medição.

[Parecer, avaliação dos controles e prompt vigente](character_move_showcase_standard_v1.md)
substituem os checkpoints anteriores. Matriz registra 21 estados não iniciados;
cena 10 é planta sem ator, GD01/GD02 continuam propostas. Próximo resultado:
guarda/toque autorais com composição medida e uma ação completa, avançando
estados e portraits independentes até o pacote revisável. Não basta aceitar o
contorno em escada nem declarar o alcance causa única sem discriminar as células.
Revisão documental/visual e simulação; sem aceite de gameplay, animação, áudio,
FPS ou AAA. Recibo: `out/diagnostics/social_gq02_review_20261101/`.


## Guarda autoral GQ03 medida — 2026-11-01

GQ03 é desenho de edição sobre J01, assentado a 104 px e convertido com
2/3×6/7 e depois extra 7/9. Corpo SMS 69×25. Self-checks passaram antes da
leitura. Par com o Ken de construção: 32 sprites, pico 8, zero overflow.
Oito fases de posição, os dois cantos, a face espelhada e as packing phases
x=1, 4 e 7 continuam em pico 8. Não há folga. Não liga ao jab v8: a transição
pede um quadro intermediário, sem substituir J01–J06. GQ02 fica diagnóstico.
O toque de BC04, na mesma escala, tem seis colunas na faixa da haste — casaco
à esquerda e latão/contorno à direita — e cinco na sola, bota nas duas pontas.
Uma tentativa de toque atravessou o corpo e não foi medida. Sem ROM, sem FPS,
sem comando aprovado. Proposta única de botões, ainda não decidida:
`doc/dr_social_two_button_proposal_v2.json`. A cena 10 segue com comando em
definição.

## Guarda GQ02 medida e cena 10 ainda sem comando — 2026-11-01

A causa da guarda não era a altura. No extra 7/9 só o bloco da sola tinha
cinco colunas. GQ02 dobra a cauda e a bota de trás para a haste, a partir de
J01, e recua a bota da frente o mínimo da ponta. Corpo 69 px, largura 27.
Self-check do adaptador e do simulador passaram. Par com o Ken de construção:
35 sprites, pico 8, sem overflow. Receita e resultado em
`cps2_keys_v1/proposals/GQ02_pair_result.json`. A borda da cauda ficou em
escada. Não há ROM, não há intervalo de bengala e o alvo 66–72 não mudou.

Derrota versus ganhou franzir de sete pixels e as três placas perderam o sal
do casaco; os originais continuam no Git. A cena 10 tem storyboard 256×192,
`preview/cena10_storyboard_v1.png`, com o texto “comando em definição”,
direcional à esquerda e botões 1/2. A proposta de controles está em
`doc/dr_social_two_button_proposal_v1.json` e não está aprovada. GD01/GD02
seguem abertos. Toque, bota, estocada e o restante do pacote continuam por fazer.

## Avaliação do pacote e padrão de apresentação de golpes — 2026-11-01

Avaliado incremento `d7a3a2d`: Social segue incompleto. Matriz mantém jab como
reuso, três chaves isoladas, estados/efeitos não iniciados, conversa atenção/
fala e três placas versus candidatas. Não foi encontrada ROM do pacote novo;
nenhuma animação completa nova foi validada nesta revisão. Inspeção estática
das cinco placas aponta progresso de texto/expressão e pendências de clusters,
volumes e estabilidade de rosto/crop. Não há aceite artístico integral.

O proprietário propôs padrão com nome do golpe, representação gráfica do
controle SMS, botões/direções/forma de executar e animação em velocidade correta;
possível desbloqueável no futuro. [Padrão, avaliação e prompt](character_move_showcase_standard_v1.md)
e [registro de direção](decisions/character-move-showcase_owner_direction_20261101.json)
ligados a GDD, roteiro, spec cena 10 e TDD. Comandos/timing competitivos ainda
precisam GD01/GD02; não converter atalhos do viewer em instruções de jogo.

Próximo passo: continuar personagem completo, resolver composição sem repetir
hipóteses reprovadas, refinar portraits e preparar a apresentação ligada aos
dados reais. Piloto parcial não substitui pacote completo nem prova o duelo.
Desbloqueio é ideia futura, sem sistema de recompensa autorizado neste lote.
Mudanças deste recorte são somente documentação; sem C/assets/ROM/emulador
novos. Revisados referências, autoridade, cobertura e diff. Base `d7a3a2d`,
registro local em `out/diagnostics/move_showcase_design_20261101/`. Produção e
placa preexistentes preservadas, fora do incremento documental.

## Revisão do retorno: faixa GDD alcançável, par reprovado — 2026-11-01

O retorno do artista foi conferido. O adaptador v2 aceita razões configuráveis,
não só 1/1 e 4/6. Testes do coordenador, self-checks prévios OK, sem mudança de
fonte/ferramenta: extra 7/9 gera guarda de 69 px e 4/5 gera 71 px; no mesmo
par Ken, picos 9 guarda / 10 bengala nas duas. Modo 8×8 a 69 px deu 10/10;
fase tall (3,9) deu 9/10. Todos reprovados pelo adaptador/simulador, sem ROM.
Não é prova de inviabilidade universal da faixa, nem aprovação de 60 px.
[Revisão e prompt de continuação vigentes](dr_social_artist_followup_review_20261101.md)
registram próxima investigação de atuação/composição e progresso independente.
Receitas/relatórios em `out/diagnostics/social_scale_review_20261101/`.
Portraits atenção/fala foram vistos como estudos de layout, não paleta/arte SMS
ou cena implementada. GDD e fontes permanecem intactos; aceite pendente.

## Medição do par e retrato da conversa — 2026-11-01

A seção acima é a conferência do coordenador. O que segue é o que este
produtor fez depois dela. A bengala não ganhou intervalos. O adaptador aceita qualquer razão extra
entre 0 e 1, depois do encaixe CPS2→SMS. 1/1 e 4/6 foram dois casos, não
o limite da ferramenta. 35/52 direto não é essa razão aplicada por cima
do encaixe.

O coordenador mediu a faixa do GDD sem que este produtor repetisse o
teste: extra 7/9 dá 69 px e extra 4/5 dá 71 px; guarda e toque falham no
par com o Ken de construção (picos 9/10). Modo 8×8 e fase (3,9) também
falham. Isso não torna 66–72 impossível e não aceita baixar o corpo para
60 px. Na leitura dos pixels de 7/9, a sola da guarda tem três linhas de
33–34 px e a bengala chega a 39 px; nenhuma fase coloca todas as linhas
em quatro colunas. O Ken ocupa quatro nas mesmas faixas. Pico de
simulador não é sprite visto caindo no emulador. Não há ROM.

A proposta de guarda em três quartos foi desenhada duas vezes e fechada:
o corpo vira, mas a cauda do casaco continua aberta. Não foi medida.
As placas de tiles da conversa estão em `preview/conversa07_sms_attention_256.png`
(`62a084cd…`) e na fala (`7b6e1d80…`), com glifos de 8×8, ç/ã/í e sonda
de palco. Não provam texto de runtime. BC04, K04 e RL05 permanecem chaves.

O comparativo do par está em `proposals/pair_conflict_comparative_v1.json`:
a função de guarda e o alcance da bengala ficam como estão; a guarda em três
quartos não empilhou a cauda e não foi medida. O dono decide alvo, alcance e
identidade. A placa versus neutra é `preview/versus_neutral_sms_256.png`
(`48c1ff4f…`), 182 tiles, 5824 bytes se cada um for 4bpp, sem ROM. Vitória
(`d089c087…`) e derrota (`357f1c39…`) usam o mesmo layout e o mesmo vão vazio.
O sorriso ainda se lê no 4×. A derrota fica mais fechada que o neutro e não é
sequência. Seleção e as quatro expressões de conversa que faltam continuam
por fazer.

## Revisão das primeiras chaves e novo direcionamento — 2026-11-01

O proprietário pediu conferir a compreensão do artista e possíveis referências
fracas herdadas da curadoria. O anexo recebido nesta solicitação é MT5X/Super
ATR, não o relato artístico; avaliação feita sobre os artefatos locais,
sem atribuir aquele texto ao artista. Parecer e prompt de continuação:
[revisão da produção inicial](dr_social_artist_followup_review_20261101.md).

Matriz, lineage, prompts e hashes de jab/BC04/K04/RL05 conferidos; model sheet,
prancha ampliada e fontes BC04/RL05 inspecionados. J01 v8 é a âncora registrada;
não há evidência nesses registros de substituir a rota atual por folha antiga.
Compreensão de kit/escopo/status demonstrada; pacote ainda incompleto, como
admitido pelo próprio produtor. Falta atuação contínua: prompts que limitam
movimento à arma/pernas não devem reger a sequência inteira. Os picos 7/5/15
são declarações do produtor sem recibo oficial localizado neste pacote; medir
par/packing antes de derivar intervalos da estocada. Outro objeto não remove
o limite por scanline. Escala 35/52 e previews ainda são estudos.

Próximo passo: ação de bengala completa com composição comprovada, resolver
estocada sem mutilar arte/afrouxar gates, seguir estados/retratos independentes
até o pacote integral. Completar receita/proveniência, distinguir papéis de
portraits e corrigir o cabeçalho duplicado do prompt original. Nenhuma imagem
foi alterada nem aprovada nesta revisão; sem nova ROM/emulador ou medição FPS.
Mudanças e artefatos do produtor permanecem no checkout, fora deste commit
documental. Designer/proprietário revisam antes de novo personagem.

## Incumbência artística de personagem completo — 2026-11-01

Pedido do proprietário: preparar contexto e prompt para um agente artista novo
produzir um personagem completo, seguido de revisão pelo designer antes de
novas tarefas de elenco. Escolhido Dr. Ferdinand Social: lista de três normais,
dois especiais e Super aprovada em design; balanceamento/arte completa pendentes.
[Prompt autossuficiente](dr_social_complete_character_artist_prompt_v1.md)
reúne autoridades, três fontes com hashes conferidos, método CPS2 aprovado em
29/10, reparo v8, 28 IDs obrigatórios, respostas visuais, objetos/FX, atuação e
portraits de conversa. Distingue fonte ~104 px do alvo corporal SMS 66–72 px;
proíbe encolher poses largas, promover fonte histórica por nome ou autoaprovar.

O pedido autoriza a produção candidata integral de um personagem; não é aceite
de pixels, orçamento, balanceamento ou personagem pronto. Em 2026-11-01 a
produção começou e não terminou. Três fontes conferidas pelo SHA do prompt.
J01–J06 v8 não foram refeitos. Chaves novas, ainda sem intervalos e sem ROM:
toque de bengala `BC04` (`ee6d3259…`), checagem de bota `K04` (`98d72ee5…`) e
estocada `RL05` (`14944cc0…`), em
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1/`.
A primeira tentativa da bengala, com o cabo na ponta, está preservada e
rejeitada. Corpo da fonte J01: 104 px. A razão comum 35/52 põe a guarda, o
toque e a bota em 70 px de coroa a sola, sola em Y77. O derivado SMS antigo da
amostra continua em 59 px e não fecha o alvo. Na mesma razão, a estocada
sozinha marcava 15 colunas exploratórias; o toque 7 e a bota 5, cada um
sem adversário. Essa contagem não é o simulador. A medição oficial posterior
está na seção do topo. Não houve ROM nem FPS. Outro personagem espera o
coordenador e o dono.

## Direção de fã, campanha e carisma — proprietário, 2026-11-01

**Estado: documentado para desenvolvimento futuro; implementação e interação
prevista explicitamente pendentes.** Pedido do dono amplia o design com
História/Versus, evolução de Alis, entradas/vitórias contextuais, arena Kenseiden,
três magias/voz de Shadow Dancer SMS, cameo de Alex Kidd, abertura/título/opções
e encerramento. Ambição AAA permanece objetivo; não se declara qualidade atingida.
Registro de autoridade e alternativas:
[decisão FD01–FD07 / FC01–FC06](decisions/fan-campaign-and-character-expression_owner_direction_20261101.json).

- GDD separa direção do dono, alternativas em discussão e propostas do designer;
  Alis não recebe números ou fragilidade definitiva por inferência de biotipo.
  Escudo já aprovado versus desbloqueio posterior permanece questão aberta.
- Roteiro contém beats de abertura, piloto Hayato/visitante, cameo e intenção
  de entrada/vitória/derrota para os 13 integrantes registrados. Falas são
  rascunhos; visitante/monstro/causador e finais não foram escolhidos.
- Spec mantém IDs 01–03 e contrata 04 abertura, 05 título, 06 opções, 07 narrativa,
  08 evolução de Alis, 09 final, além da arena Kenseiden/fases da 02. Budgets
  de todas as novas composições ficam pendentes, sem números fictícios.
- TDD define invariantes propostas de modo/skip/endpoint, transação de pontos,
  isolamento do Versus, residência de cena e investigação PCM com retorno e
  FPS funcional. Tela parada não aprova CPU bloqueado nem contador ISR.
- Ficha J.J. recebe moto como apresentação contextual futura; seis desenhos
  sem FX, arma e aceite anteriores continuam intactos. Alex é cameo/easter egg,
  não décimo personagem. Três magias de Shinobi não aprovam o draft inteiro.

Pesquisa textual: manual Phantasy Star SMS, material Shadow Dancer SMS/review
de época e sample playback; URLs/limites na decisão. Não foram baixados assets
ou ouvidos cues novos. Fonte exata de voz/música e captura do easter egg ainda
faltam; links não são proveniência de arte pronta.

**Verificação do lote:** revisão de diferenças, JSON/referências locais e
coerência de autoridade/estado. Sem alteração de C/assets, build ou sessão de
emulador nova; evidência antiga `90ea0f98…` não valida nenhum item novo. Registro
local do lote em `out/diagnostics/fan_direction_20261101/`; base Git
`082e52ad3acc6143ffcdd6e4a7d1ff2db6310f6b`. Commit de fechamento identifica o
incremento; recibo de publicação no mesmo diretório. Alterações preexistentes
da placa/consumidor e de luta_mugem_rev2 não pertencem a este lote.

**Próximo passo:** fechar FC01/FC03/FC04 com as propostas concretas no GDD;
continuar a integração funcional GD01/GD02/GD05 antes de prometer campanha
jogável. Depois pilotar encenação → conversa → duelo → resultado/evolução →
próximo nó, com vídeo/input/áudio/estados e medições do mesmo SHA. Nome/fonte do
ninja: versão já resolvida como Shadow Dancer SMS; nome exibido ainda pendente.
Não pedir aprovação novamente da direção explícita para registrar estes contratos.

## Revisão de game design — 2026-11-01

**Estado: contratos documentados; aceite de combate e experiência completa
pendente.** Pedido atual: atuar como game designer no consumidor existente,
preservando decisões do dono. Resultado nos documentos canônicos:

- GDD: identidade/fonte/arsenal/papel dos nove heróis e quatro chefes;
  separação de decisões, hipóteses e evidência; seis ações de Social e duas
  amostras diagnósticas, sem promover os 44 golpes do draft.
- Proposta individual de Social: intenção, ameaça, trajetória, resposta,
  vulnerabilidade, hit/block/whiff e retorno de cada ação; Super mantém três
  ramos e não cria terceiro especial; estados comuns ligados às transições.
- Roteiro: escolha → preparação → decisão/consequência → encerramento.
- Spec: contratos de seleção 01, duelo 02, arcade 03 e diagnóstico D01,
  incluindo extremos, simultaneidade, informação e critérios de legibilidade.
- TDD: interface entre pose/regra/resultado e ownership/transições a integrar.
- Ficha J.J.: corrigidas precedências de arma, fonte e escala histórica;
  concept v5/fonte v6 sem FX e tempos aceitos permanecem preservados.

Não há alteração de C, arte, dados de runtime ou ROM neste lote. Mudanças
locais preexistentes da placa e do motor rev2 foram preservadas e não fazem
parte do incremento de design. `cena01_duel_read`/`MOF_CENA01` é o nome
técnico histórico de D01, uma amostra de **duelo 02**, não seleção 01.
Históricos abaixo permanecem com seus aceites e limites; esta seção é a
consulta atual do trabalho de design, sem reescrever evidência antiga.

### Interação realmente experimentada

ROM existente `90ea0f98febf4e047e6ca4637af1c454dd9ac7971e5b0bd00fec058c5ebf2405`
(32 KiB), perfil J.J. à direita/Social à esquerda com placa. QA nativa
`/root/design_runtime_qa`, pedido `2d7e9e80c82345da8f030fa1dd7bf5a4`, sessão
`d4d91c97840f45d1b46f85dab83e6db6`: **2/2 casos diagnósticos passaram**,
174/174 framebuffers iguais às seis composições legais. Input2 desativa
autoplay; duas novas pressões de input1 apresentam S01–S05 e retornam à guarda.
No vídeo zero-based: primeira ação 80–101, guarda 102–131; segunda 132–153,
guarda 154–173. Exposições 7/4/2/3/6 preservadas. Primeiro ciclo automático
nos índices 1–22 está registrado separado e não foi contado como input manual.

Input aplicado na ponte em VDP198/250, preparação apresentada em VDP201/253:
três avanços ponte→imagem, sem timestamp de aceite interno; não é latência
competitiva ou tempo de parede. Terminal VDP294 confirma pose0/keys0/hold0;
C7F7 não integra esse contrato e foi ignorado. Social, nomes, barras e chão
continuam estáticos e sem FX. Conferência do coordenador incluiu relatório,
timeline e quadro nativo de ação; sem alegar percepção de playback contínuo.

Self-checks de captura/corredor/auditor passaram; corredor tem 14 sondas e
folga 1.784 B no map da ROM. Auditoria do relatório, incluindo `--require-passed`
e `--current-rom`, passou. Sessão fechada, quatro processos próprios ausentes
por PID/start_ticks. Não houve build repetida nem medição FPS/VBlank/áudio.

Evidência primária em
`out/diagnostics/game_design_contracts_20261101/qa/run_8bd9c1a8e4064222ad58f195847c3033/`:
`report.json`, `case_0.mp4`/frames, `frame_comparison.json`, `commands.jsonl`,
`case_1_probe.json`, `audit_report.json` e `cleanup_confirmation.json`.
Índice durável, hashes, retenção e limites em
`doc/game_design_contracts_review_v1.json`. Vídeo stepped prova sequência,
não FPS, pacing ou compreensão humana. Essa QA não aprova a placa como arte
final nem reabre os aceites existentes de Hayato/J.J.

### Blocker e handoff deste recorte

Defeitos documentais corrigidos: numeração ambígua de cena, ficha de J.J.
com arma/escala superadas e falta de ligação entre ação, consequência e retorno.
Nenhum defeito de ROM foi encontrado contra os dois casos atribuídos. Barras
estáticas e rival sem resposta são **limitações diagnósticas**, não evidência
de gameplay nem nova regressão. Não foi registrado gosto estético como defeito.

O principal limite da experiência é a ausência do ciclo de combate neste
consumidor. Próximo passo: dono/design resolvem GD01/GD02 (comandos, regras de
contato/recuperação e valores ainda abertos) para o kit já aprovado de Social;
engenharia fecha GD05 na integração oficial e mede GD06 antes de arte extra.
Não implementar o disparo de J.J. ou outro moveset por inferência deste pedido.
GD03 mantém decisões individuais/identidade; GD04 fecha resultado/arcade;
GD07 exige teste com público. Responsáveis, condições e casos estão no GDD.

Não experimentados: seleção/arcade, deslocamento/guarda, hit/block/whiff,
objetos, rounds, economia de Super e playtest de compreensão. Aceite funcional
alvo60/piso58, pior frame integrado, áudio e época visual delivery continuam
pendentes; números históricos de pares não se transferem para esta ROM.
Não ampliar elenco, golpes, cenários ou sistemas para contornar essa ausência.

Continuidade: branch `codex/host-bootstrap-continuity-20261024`, base
`d7f1eff952f48a7705c4e7b765addb13df783df6`, PR4 existente. SHA final,
verificações documentais e confirmação remota ficam no recibo
`out/diagnostics/game_design_contracts_20261101/publication.json`.
Retenção privada local usa o destino de recuperação existente; não é release
nem backup fora deste host. Relatório histórico Social61v5 ausente permanece
pendência preexistente da curadoria, sem relatório fabricado neste lote.

## Cena 01 — placa de leitura, sprites aprovados intactos

A cena do par J.J./Social era um campo cinza. A placa P0 acrescenta nomes
`DR`/`JJ`, dois medidores contínuos, fio dourado e chão. Não redesenha
personagem, não muda origem, tempo nem bytes de sprite. A primeira placa
(`3a4a83ea…`) deixava uma linha de backdrop entre a sola de J.J. e o chão;
a linha de contato passou para Y143. ROM corrigida
`90ea0f98febf4e047e6ca4637af1c454dd9ac7971e5b0bd00fec058c5ebf2405`,
32 KiB, sessão `e99a50ec2298424787a94de432ae5e50` fechada, quadro 150
`9126950e…`. Sola e linha encostam nas duas colunas de apoio. FPS e VBlank
desta ROM não foram medidos de novo. Não é cenário final, não está em `res/`,
e não herda o aceite de J.J. Checkpoint:
`doc/cena01_duel_read_checkpoint_v1.json`.

## Aceite do proprietário — J.J. fechado neste recorte

O proprietário respondeu **“aprovado”** à entrega6677d5d, que apresentou o
conceptv5, as seis poses da fontev6 sem FX e o vídeo real da ROM direita,
e perguntou sobre proporção corrigida e retorno à guarda. Decisão em
`decisions/jj-zillion-character_owner_approval.json`: correção e amostra
aprovadas com tempos existentes7/4/2/3/6. Conceptv5 e fontev6 passam a
aprovados no registro; conceptv4 permanece histórico/supersedido, intacto.
Não pedir novamente este aceite nem ampliar conteúdo por inferência.

Checkpoint atual `jj_zillion_character_checkpoint_v7.json` preserva v6 imutável
e registra owner_acceptance pass. Continuous_motion segue needs_evidence
quanto à percepção contínua verificável: “aprovado” não descreve uma sessão
assistida. Isso não reabre a decisão do dono, que encerra este recorte.
Não gerar arte, mudar tempos ou repetir build/captura/review sem defeito novo.
Fonte,14PNGs,headers,trêsROMs,vídeo e QA são os mesmos do lote anterior.

A rota curta com terceiro personagem agora tem aceite do dono e evidência
técnica preservada; não foi passagem artística única, conforme histórico de
seis gerações. Curadoria global continua não homologada e bloqueada pelo
relatório históricoSocial61v5 ausente. Próximo passo: recuperar os bytes
originais pelo pacote manual já solicitado e encaminhar o material existente
para futura curadoria, sem ampliar elenco, movimentos, objetos ou sistemas.
Commit/PR deste aceite: recibo separado em
`out/diagnostics/jj_zillion_owner_acceptance_v1/publication.json`.

## Histórico anterior ao aceite de J.J.

## Estado atual J.J. — fidelidade corrigida, execução comprovada, aceite pendente

Concept candidato v5 e fonte candidata v6 reduzem a Zillion mantendo forma
navy/cyan, pega e os seis desenhos I00/S01–S05. Nenhuma bala, tiro, spark,
flash, FX ou objeto foi incorporado. Corpo/poses v3 ficam preservados fora das
ROIs de arma/pega, com uma única limpeza adicional de ponto órfão em I00
(105,99). Review v5 + adendo v6 fecham o escopo estático independente. Não há
aceite humano da correção nem percepção contínua estabelecida nesta interface.

Fonte6: `0d4b12d236530063340c59f68b77219e3159940e0413e9cf284d04ddf7a6bf2b`.
Concept5: `e81e0f9cc81b1552ff2ace0e046ecb5c36be00119e6b6f5d60d17a7b17f518e9`.
O reparo fonte6 não muda nenhum índice SMS: 14 PNGs, 12 cenas e dois headers
v5 reutilizados por identidade; não houve conversão/build repetidos por isso.
Par normal8×8:180padrões/5.760B,max50SAT,pico8,canvas104×88,pivô48,80,
origens16/128,64 e última sola visívelY143. P1 única15cores úteis;902pixels
opacos/índices/RGBA de Social exatos em ambas as faces. Apenas slots PLTE não
usados por Social11/14/15 mudam. Sem folga presumida para futuros FX.

Três ROMs de32KiB buildadas pelo wrapper, com gates pertinentes e vínculos:

- esquerda: `57b0d4e9b8c0acb005814f2c841baff07b75dbc4138ab97a62353d647dc87cc1`;
- direita: `aed6db173058ccad03d84ff36eaf088a33235bc7f57cef96025d30e0e510eab4`;
- direita stress128: `fc036bd50c000a403e1cf7ac08d30319f5e1f764260e137ee09d8b1936464699`.

QA independente2/2casos,260/260RGBexatos: S01–S05 manuais em80–86/87–90/
91–92/93–95/96–101, guarda102–129; tempos propostos7/4/2/3/6. Autoplay
inicial0–21, guarda22–79. O still `case_0_frame.png` foi obtido antes do vídeo;
o terminal foi conferido no RAW129. Sessõesa038803d…/b8888ff2… encerradas.
Vídeo real da ROM direita tem480/480quadros exatos em8,023643s,11ações completas,
10com guarda integral, decodeMP4lossless igual ao RGB. Não é avaliação de força,
fluidez ou aceite temporal. Mídias em `out/diagnostics/jj_zillion_single_shot_v5/
performance/5f94496d541d4b8ea7656756cd63acd8/`: `jj_character_realtime.mp4`,
`rom_normal.apng` e `rom_slow.apng`. Fonte6 separada em seu `poses_and_times.png`
e comparações `source_normal.apng`/`source_slow.apng`; a coluna anterior v3
conserva o pulso histórico, a coluna atual não tem efeitos. `SMS_review.png` é
preview convertido, não captura da ROM. Concept5 permanece fonte RGBA truecolor,
sem se aplicar o teto de15cores de recurso runtime.

VBlank base3.000frames,0derrame,mínimo213; stress1283.000frames,0derrame,mínimo224.
Primeira janelaFPS8s falhou59,32/58,36; mantida. Uma confirmação20s passou
59,79/59,84 no mesmo SHA, sem alterar critério. Causa da oscilação não isolada;
não declarar pacing constante por frame. Sessões root5f94496d…/7137a0f1…/
a03f5ed2… encerradas. Na leitura imediata da primeira o supervisor ainda saía;
`cleanup_confirmation.json` confirma todos os PID/start_ticks próprios ausentes.

Checkpoint `doc/jj_zillion_character_checkpoint_v6.json`: quatro eixos técnicos/
estáticos pass; continuous_motion e owner_acceptance needs_evidence. Próximo:
o proprietário julgar proporção/forma no concept e seis poses e assistir o vídeo
normal para aceitar a correção/retorno. Preservar controle até defeito concreto.
Não gerar arte adicional para suprir a ausência de percepção contínua.

Histórico completo no campo `followup_jj_zillion_short_route` do candidato de
curadoria existente `curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`.
Custos reais:6ImageGen(2concept/4sprites),6variantesfonte,6conversões oficiais
(4falhas/2pass),3builds,5sessões novas(2QA/3performance). As buscas de fase
v2–v4 não são conversões oficiais; v4/três poses foi descartada por direção do
dono. O plano v5 ficou congelado antes da QA; resultados posteriores estão
separados em `runtime_evidence.json`. Rota técnica reutilizada demonstrada,
previsibilidade artística em passagem única não demonstrada.

Registro limitado J.J.+ancestrais:26artefatos/161arquivos pass;73arquivos novos
de fonte sob ownership canônico, sem arquivo solto. Auditoria global continua
falhando no relatório históricoSocial61v5 ausente. Pacote72355032bytes solicitado
para download manual pela regra>70MB, ainda não recebido; não inventar relatório.
Nada em res/, sem projétil, gameplay, áudio, PAL, produção ou curadoria global
homologada. Hayato permanece fechado/aprovado e intacto. Retenção verificada:777arquivos/102.900.955bytes no ZIP28.128.259bytes, SHA
`937b886f83cc50f71987b14f38adf3941aacc80837ed9b8b432865bd7825557a`,
com cópia no destino local de recuperação. Recibo
`jj_zillion_character_retention_v6.json`; SHA de publicação no
`out/diagnostics/jj_zillion_single_shot_v5/publication.json`.

## Histórico do lote J.J. — decisões anteriores preservadas

## Direção vigente do dono — proporção da Zillion, seis poses, sem FX

O proprietário corrigiu explicitamente o escopo: a Zillion está grande demais
em relação a J.J.; corrigir a proporção no concept/model sheet mantendo a forma.
**Preservar os seis quadros e as poses. Não incluir bala, tiro, sparks, flash,
FX ou objetos na folha do personagem; esses elementos serão separados depois.**
A experiência de três poses e pulso composto v4 fica histórica/supersedida,
sem ROM ou aprovação. Fonte corporal para preservar: seis poses v3. Atual:
`jj_zillion_single_shot_route_v5.json`, contrato de animação v5, equipamento v2
e `decisions/jj-zillion-proportion-and-no-fx_owner-feedback.json`. Corrigir
somente arma/encaixe da pega por ROIs, sem regenerar atuação, rosto ou figurino.
Concept individual v4 aprovado permanece intacto como controle histórico;
a correção candidata v5 terá review/aceite próprios. Nenhuma ROM de J.J. foi
construída até esta direção. Hayato permanece aprovado e intacto.

## Lote J.J. — correção de autoridade da arma antes de continuar

O proprietário pediu outro personagem e uma ação curta repetível para futura
curadoria canônica, além da recuperação do relatório histórico Social61v5.
Selecionado J.J. / tiro único Zillion. Primeiro resultado v1 tem arma errada:
blaster compacto branco/azul herdado do concept individual v4. O dono apontou
explicitamente a diferença. A referência anexada é byte-idêntica à de08/10
(`7f994afdab1c2e9912c024f4c81b72f3f40327f849aa92d50873a290f859dc49`),
e a prancha WakuWaku7 aprovada já corrigia a pistola longa navy/cyan. Falha do
coordenador: não conciliar correção específica de equipamento ao retomar pelo
concept mais antigo. Preservar a aprovação histórica e não reutilizar sua arma
como autoridade atual.

Contrato atual `jj_zillion_weapon_identity_contract_v1.json`: conceptv4 rege
corpo/figurino, prancha aprovada e referência do dono regem a Zillion. Plano
atual `jj_zillion_single_shot_route_v2.json`, contrato de animação v2; v1 fonte,
configurações e conversões falhas preservadas. Uma geração, quatro conversões,
zero builds/ROMs/sessões de J.J. até esta reconciliação. O gate de sola detectou
79vs80 antes de build; após pivô medido, o par ainda excede scanline na pose do
pulso avançado. Nenhum resultado ilegal foi integrado. A fonte v2 corrigirá
arma e encenação compacta; pulso curto somente na emissão, sem trajetória lenta
ou sistema de projéteis. Review independente estático v1 é evidência histórica,
não aceite de arma ou movimento. Hayato permanece fechado/aprovado e intacto.

Relatório ausente: SHA esperado `f288f3f113d33ed9c898acfb92476f28f858292e8f403c2c410c8fc2f0403bac`.
Solicitado download manual de `smsforge-generated-other-20261021.tar.zst`
(72.355.032bytes; SHA85750979…) conforme regra acima de70MB. Não recriar relatório
histórico para obter registro verde. Prosseguir com o lote independente e
preservar a pendência se o pacote não chegar.

## Aceite final do proprietário — corte de Hayato fechado

Após o fechamento publicado em `15305168ff9c46a9ea1f373354c988ba9c099abd`,
o proprietário respondeu literalmente **“aprovado”**. Registrar este aceite
como confirmação final do corte apresentado: arte original da v4, lâmina sem
distorção e exposições **8/1/2/7/2/5** no perfil de runtime v7.
A entrega à qual respondeu incluía o vídeo real
`out/diagnostics/hayato_short_cut_v2/timing_only_v7/performance/b346785d4d914ba299e5325b67419b4a/hayato_cut_realtime.mp4`
(SHA-256 `2ef761100855f5fbebcba533515ae443af9e65a2484a378714aa6086b11b1204`),
da ROM direita `2d5afcbb497fdedd61dc1498782d3d97508cac7553cc024a14f5650ee0d03022`.
O aceite não descreve uma sessão assistida nem acrescenta observações de
movimento; os registros técnicos e a decisão detalhada anterior permanecem
inalterados. O checkpoint formal abaixo conserva o escopo da seleção anterior
do preview; esta seção registra a confirmação posterior à entrega.

**Estado: revisão deste corte encerrada e aprovada pelo proprietário.**
Manter a seleção e preservar a tentativa com distorção no histórico rejeitado.
Nenhuma mudança de pixels, tempos, ROM ou evidência neste fechamento; não há
motivo novo para build, captura ou revisão equivalente. Próximo lote depende
de um novo objetivo; não ampliar movimentos, elenco ou sistemas a partir deste
aceite, nem interpretá-lo como autorização de merge, release ou entrega completa.

## Escolha aprovada — somente tempos, perfil v7

O dono aprovou a coluna **somente tempos 8/1/2/7/2/5**. Rejeitou a distorção
da lâmina por perceber outra trajetória e piora do movimento. Decisão atual em
`decisions/hayato-short-cut-timing-only_owner_approval.json`: aceite artístico
e temporal do preview escolhido, sem inferir que o dono assistiu a uma ROM nova.
Não pedir novamente a mesma escolha ou outro aceite desse preview.

Reutilizar a fonte v4, hash9302a78a…, com katana original em todas as poses.
Nenhuma geração, pintura ou folha duplicada. Fonte v4 aprovada no registro;
v6 rejeitada pelo dono e preservada com sua evidência. V5 continua histórica.
Perfil de runtime v7 usa configs `hayato_short_cut_timing_only_v7_{left,right}.json`
e seletores15/16 no mesmo consumidor. Somente as seis exposições mudam em
relação à v4:8/1/2/7/2/5. A opção de amostragem da experiência de distorção não
é necessária nesta seleção; o adaptador permanece com sua função opt-in testada.
16 PNGs e14manifestos de cena são byte-exatos à v4; o header inteiro só difere
na tabela de exposições. Recursos/geometria anteriores são reutilizados por
identidade de conteúdo, sem repetir auditoria artística. Perfil219patterns,
7.008B,max53SAT,pico8. Builds32KiB passaram: left67ed85a8db15aca6cdf65771044fc23e3eb09f6984d4103b74ce6d0d3b66997e;
right2d5afcbb497fdedd61dc1498782d3d97508cac7553cc024a14f5650ee0d03022;
stress128dd8e79cb282a267aee3822d5120a1fe99c8c5d6da991657ce104b52c0cd51ae0.
QA v7 passou2/2casos,20checks,260/260quadros exatos; R01–R06 apresentados em
8/1/2/7/2/5, guarda original105–129, R02sempreoriginal. Sessões6a127439…
e00af693d… encerradas com PIDs/start_ticks próprios ausentes.
Gravação real da ROM direita:480/480quadros exatos em8,0195s,10cortes completos,
decode lossless igual ao RGB nativo. Sessãob346785d4d914ba299e5325b67419b4a:
FPS59,71/59,46 em duas janelas8s; VBlank3.000frames,0derrame,mínimo213.
Stress128 sessãodaec1cf5b1b94705a0e6ae7a24ae1741:3.000frames,0derrame,mínimo223.
Ambas encerradas; quatro processos próprios de cada sessão ausentes por identidade.
Onze checks focados passaram, incluindo reutilização de recursos/geometria por
hash; nenhuma suíte de conversor inalterado ou revisão artística equivalente foi repetida.

Contrato atual `hayato_animation_contract_v4.json`; checkpoint
`hayato_short_cut_timing_only_v7_checkpoint.json` e checklistv7 passaram no
escopo declarado: aceite humano do preview fonte escolhido, revisão estática
inalterada e reprodução técnica da nova ROM. Isso não afirma que o dono viu
a nova ROM nem aprova entrega de produto, áudio, PAL ou combate completo.
O julgamento artístico/temporal pedido está fechado por sua decisão explícita.

Mídias atuais em `out/diagnostics/hayato_short_cut_v2/timing_only_v7/`:
`approved_source_normal.apng`/`approved_source_slow.apng` são extrações exatas
da coluna aprovada, sem novo desenho ou retiming. Vídeo novo em
`performance/b346785d4d914ba299e5325b67419b4a/hayato_cut_realtime.mp4`; APNGs
normal/lenta no mesmo diretório derivam do framebuffer gravado. Resultado em
`result.json`, identidade em `identity_to_v4.json`. V6 e seus pareceres técnicos
continuam preservados como tentativa rejeitada; não usar deformação neste corte.
Próximo passo operacional: partir deste corte aceito quando houver novo lote
definido, sem reabrir sua aprovação nem ampliar conteúdo por conta própria.
Implementação do perfil selecionado: `8ed21d7e593fb8111c6a314fe125ccc12d21a8bf`. Documentação/recibos em commit separado e um push do lote; PR4 reutilizado.
Retenção: `out/diagnostics/hayato_short_cut_v2/timing_only_v7/hayato_timing_only_v7_approved_review.zip`, recibo `doc/hayato_short_cut_timing_only_v7_retention.json`, manifesto por arquivo e cópia local verificada no destino existente.
SHA final e confirmação remota em `out/diagnostics/hayato_short_cut_v2/timing_only_v7/publication.json`. Retenção no mesmo disco; sem release ou backup remoto novo.
Registro: recorte Hayato+ancestrais30artefatos/437arquivos passou; global segue falhando no relatório histórico Social61v5 ausente.
As seções abaixo são históricas.

## Histórico — feedback temporal do dono, candidata v6 rejeitada

O proprietário assistiu à comparação: considera satisfatórias a arte e as
poses completas, mas identifica preparação e final baixo breves demais para
ler armar→executar→retornar. Solicitou tempos contextuais e squash/stretch na
espada durante a maior velocidade. Decisão em
`decisions/hayato-short-cut-v4_owner-motion-feedback.json`; controle v4 intacto.
Isto substitui a espera por observação do checkpoint abaixo; não é aceite da
nova candidata ou promoção a produção.

Contrato v3 propõe R01–R06 em 8/1/2/7/2/5 ticks (25 no total). R01 e R04 têm
mais exposição; R02/R03 continuam rápidos, retorno R05/R06 distinto. Somente
R02 recebe deformação gráfica transitória de lâmina ao longo do arco, voltando
à katana normal em R03. Corpo, pega, bainha e cinco desenhos restantes são
invariantes por pixel. Fonte v5 reservada no registro canônico; autoria do delta
por ImageGen, composição mecânica delimitada, sem pintura de personagem por código.
V5 passou revisão de fonte; SMS revelou componente solto de 2 pixels na ponta.
V6 corrige apenas esse trecho por segundo patch ImageGen, preservando as
tentativas e os cinco outros desenhos. Configs v6 e seletores 13/14 são atuais;
11/12 guardam v5 como controle negativo não elegível para ROM de entrega.
Retângulo explícito `sample_rect_px` fixa a amostragem quando muda o extremo
da arma; sem ele, a conversão detectou sola uma linha abaixo e foi preservada
como falha. Com o retângulo [50,53,169,159], sete PNGs por face são byte-exatos
à v4 e R02 muda somente 110 pixels de lâmina. Ambos os pares medem 220 padrões,
7.040B, máximo 53 SAT/pico8; componentes dos 16 PNGs passam. Revisão da ponta e
saída SMS nova passou no parecer independente v6. Builds de 32 KiB pelo wrapper:
left `76792bb8e9c48c6efdf402eb4d470f171bc76c9283416cebb33dddfaba2ab122`,
right `c9f38130654cdac79738985b566bf8a68b01bcf4b30a40c6ef0f07f6e36a124e`,
stress128 `4c796502ad3590db5564d70a2beaae56222a315aabfeec320b5ddc3e0d6f83d8`.
QA independente v6 passou 2/2 casos, 20 checks e 260/260 quadros RGB exatos.
Manual: R01 quadros80–87, R02 88, R03 89–90, R04 91–97, R05 98–99,
R06 100–104, guarda105–129: 8/1/2/7/2/5 apresentados. Espada transitória
em R02 por um quadro e katana normal restaurada em R03. Social902/PLTE,
corpo/pega/equipamento/solaY143 preservados. Sessões b946f452… e61b3bbb4…
encerradas, quatro processos próprios de cada uma ausentes por PID/start_ticks.

Gravação real da ROM direita: sessão99efc557f6c3483ba5bfb8b74d048f4d,
480/480 quadros exatos em8,0194s,10ações completas e9ciclos com pausa integral.
MP4 lossless decodifica no SHA do RGB nativo; frames/holds não provam efeito
percebido. FPS em duas janelas8s:59,74/59,42, alvo regional NTSC passou com
tolerância explícita1FPS; não é promessa de zero variação por frame.
VBlank base e stress128:3.000frames cada,0derrame,mínimos213/223. Stress
sessãoaa8c9d6f382d45f69bd9a63c910f9d39 encerrada. Cleanup verificado para
todos os processos próprios.26testes do adaptador e30checks focados passaram;
raster, semântica, vínculo e contrato atuais passaram no seu escopo.

Resultado e mídias em `out/diagnostics/hayato_short_cut_v2/sword_stretch_v6/`:
`comparison_source_normal.apng` e `comparison_source_slow.apng` mostram três
colunas: controle v4, somente novos tempos, novos tempos+espada. São previews
de fonte, não framebuffer. A trilha v4 recebe11ticks extras de guarda terminal
para alinhar o loop de comparação, sem retimar seu golpe. `performance_v6/99efc557f6c3483ba5bfb8b74d048f4d/hayato_cut_realtime.mp4`
é o framebuffer real256×192; `rom_slow.apng` no mesmo diretório é sua derivada4×lenta.
`source_sequence_v6.png` e `SMS_both_facings.png` são pranchas estáticas.

Contrato atual `hayato_animation_contract_v3.json`; checkpoint formal
`hayato_short_cut_body_temporal_checkpoint_v6.json` e checklistv6 marcam
continuous_motion/owner_acceptance pendentes, sem erro de custódia. A avaliação
do dono da v4 autoriza estas correções e valida a base artística; não é aceite
antecipado do novo ritmo/efeito. Próximo checkpoint: dono assistir à candidata
e decidir se preparação, final baixo e impressão de velocidade resolvem seu
feedback. Não convocar revisão temporal equivalente nem gerar novas poses
sem outro defeito observado. Áudio/PAL/hitboxes/dano/combate completo e produção
continuam fora desta amostra. V4, falha inicial de amostragem e ponta v5 estão
preservadas; nenhuma skill/doutrina/gate global foi promovido.
Implementação deste lote no commit `583da6186d2e8ec67483ecb088502659c68c870e`; documentação
e recibos fecham em commit separado, um push do lote. PR4 reutilizado na branch
de continuidade. Publicação final em `out/diagnostics/hayato_short_cut_v2/sword_stretch_v6/publication.json`.
Pacote `hayato_timing_stretch_v6_review.zip` no mesmo diretório, recibo em
`doc/hayato_short_cut_body_retention_v6.json`, manifesto interno por arquivo e
cópia local verificada no destino de recuperação existente. É retenção no mesmo
disco, sem release ou backup remoto novo. Registro canônico: recorte em memória
Hayato+ancestrais passou (28artefatos/362arquivos); global continua reprovado pelo
relatório histórico Social61v5 ausente. Não confundir os dois escopos.

## Checkpoint temporal do proprietário — v4 preservada

Pedido atual: decidir este corte antes de ampliar conteúdo. Controle no commit
`e67360735f7438091893eb38522211d32d091eea`; fontes, ROMs, exposições e evidências
preservadas. Conferência de identidade: 26 referências do parecer/manifesto,
três ROMs e SHA do RGB nativo coincidem. Índice com hashes e intervalos em
`out/diagnostics/hayato_short_cut_v2/final_review_v4/owner_checkpoint.json`.
Não houve build, captura, geração ou nova revisão equivalente neste checkpoint.

Mídias para assistir, distinguindo sua origem:

- Framebuffer real, velocidade normal: `out/diagnostics/hayato_short_cut_v2/performance_v4/1b1f33e71f704e05bd064e688d3378cf/hayato_cut_realtime.mp4` (256×192; Hayato à direita).
- Mesmo framebuffer, reprodução lenta 4×: `rom_slow.apng` no mesmo diretório. É um derivado da gravação existente, não outra execução da ROM.
- Comparação da fonte anterior/atual: `out/diagnostics/hayato_short_cut_v2/final_review_v4/before_after_normal.apng` e `before_after_slow.apng`. Mostram arte-fonte, não framebuffer.
- Poses convertidas identificadas, ambos os sentidos: `out/diagnostics/hayato_short_cut_v2/sms_v4_review.png`. É prancha estática da conversão.

Exposições apresentadas em frames: R01 preparação 4, R02 liberação 1,
R03 execução 2, R04 absorção 3, R05 retorno 1, R06 recuperação 3 e guarda 21
entre ações. No primeiro ciclo completo do MP4, R03 ocupa quadros 38–39,
R04 40–42, R05 43, R06 44–46 e guarda 47–67 (índices começando em 0).
Tempos aproximados: absorção 0,634–0,718 s; retorno 0,668–0,784 s. São posições
no arquivo, não medição de pacing por frame.

| Questão | Observado em quadros | Hipótese a julgar continuamente | Menor intervenção se o dono identificar falha |
|---|---|---|---|
| A: R03→R04 | R04 é mais baixa e tem 3 ticks após 2 de R03 | Absorção/desaceleração pode ler como repetição | Testar holds com desenhos atuais somente se for exposição; corrigir a pose responsável se for trajetória/postura |
| B: R04→R05→R06→guarda | Retorno cruzado de 1 tick, recuperação alta de 3 ticks e guarda original presentes | Retorno pode parecer outro movimento de espada | Isolar a transição apontada; holds se ritmo, pose responsável se trajetória |
| C: apoios, peso, arma e preparação | Equipamento inteiro e chão comum; R01 difere da guarda | Contato, transferência de peso, continuidade e anúncio de um único corte ainda exigem playback | Corrigir apenas pose responsável se houver apoio/arma incorretos; não esconder construção com duração |

Recomendação atual: **manter v4 como controle, sem delta artístico ou de timing**.
Isto preserva a candidata; não é aceite temporal. Nenhum defeito concreto em
movimento foi observado por este agente, cuja interface não oferece percepção
contínua. O parecer independente existente continua `needs_evidence`, sem novo
defeito estático identificado. Igualdade de framebuffer/FPS não fecha A/B/C.

Única solicitação ao proprietário: assistir às mídias exatas e responder A
absorve/repete, B recupera/parece outro corte e C apoios/arma/preparação
convincentes ou não, citando a transição que falhar. Só depois escolher manter,
ajustar exposições ou corrigir pose específica. Não regenerar, acrescentar
quadros/efeitos ou convocar revisões equivalentes para preencher esta limitação.

## Lote corrente — corte corporal, fonte v4 e ROMs novas

Fonte atual: `data/source_art/sprite_studies/hayato/review_drafts/cps2_short_cut_v2/sequence_v4/cut_source.png`. Seis poses R01–R06,14ticks provisórios
4/1/2/3/1/3 e guarda original. R03novo antecede R04absorção mais baixa; R06reusa
C04antiga no mesmo papel de recuperação. Cinco desenhos do conjunto pertencem
à nova coreografia.192px é margem transparente; originais144px preservados.
Não há fit individual do corpo/arma. Onze gerações de reformulação e um patch
local de franja foram preservados com prompts/receitas; não alegar economia.

Fonte v3 passou estática após reparo de R02katana curta/larga. Adendo v4 passou
fonte/SMS: R02transladada exatamente(0,+1); R03recebe8pixels ImageGen somente
no ROI[109,77,114,82], foraROI/face/corpo/equip exatos; derivada remove1ponto
solto da franja.16PNGs terminam79/boundary80; gatecomponentes(min4,c8)passou,
regiões materiais automatizadas ainda pending e materiais têm review separado.
Percepção contínua/timing percebido/dono/produção continuam pendentes.

Adaptador oficial v2 opt-in8×8 chama packer existente, sem segundo consumidor.
219padrões/7008B residentes, max53SAT/pico8;14composições. Defaults tall: header/
3PNGs reais byte-idênticos.20testes do adaptador e selfcheck128tall+64normal;
7testes puros da captura realtime. Novo campo expected_opaque_bottom_px=80
bloqueia pivô stale antes de publicar header. CanvasSMS88/pivô40,80, origens
24/136,64 mantêm posições mundiais/solo144. Social902pixels/índices/RGBA/PLTE
preservados nos2sentidos.8×16 completo reprovou residência; não reduzir atores.

Configsativas `hayato_short_cut_body_sequence_v4_{left,right}.json`, headers
`out/diagnostics/hayato_short_cut_v2/converted_v4_{left,right}`, seletores9/10.
7/8 preservam controle negativo v3;5/6 preservam tentativa antiga. ROMs32KiB:
left3019e59281b0ca9638f8ab47375e47703b5314e50107ed05495b9802946fe2a7;
rightf531f7064f5c0293fe39d298e599e3e0a9871bad8865fca07e7f475e76939517;
stress1284f7b340a19075183542c318352457ab1d5adca78d09037af9060f991bffd497a.
Builds passaram. QA independente atual: duas sessões fechadas, 236/236 quadros
exatos, 20 checks; entrada manual apresenta 4/1/2/3/1/3 e guarda terminal.
Vídeo nativo em run livre: 480/480 quadros exatos em 8,0187 s, sete apresentações;
ordem e holds completos conferidos, MP4 lossless decodifica no mesmo SHA RGB.
O callback usa DisplayWindow original, sem stepping nem compositor. Sessão
1b1f33e71f704e05bd064e688d3378cf: FPS 59,78/59,67 em duas janelas de 8 s;
VBlank selado em 3.000 frames, zero derrame, mínimo 213. Stress128 sessão
30406ea2f3a9418493c66f6d60ffeddd: 3.000 frames, zero derrame, mínimo 223.
As quatro sessões deste fechamento estão encerradas; PIDs/start_ticks próprios
ausentes. Métricas qualificam este par diagnóstico, não cada frame ou game feel.

Evidências: `out/diagnostics/hayato_short_cut_v2/performance_v4/`, QA em
`independent_qa/`, comparação final normal/lenta e fonte em `final_review_v4/`.
27 testes focados passaram (20 adaptador + 7 captura); 28 checks de recursos,
14 composições, corredor e vínculos passaram; raster, semântica e contrato
atuais passaram. Checklist artístico bloqueia promoção por percepção contínua
e aceite do dono pendentes. Próximo checkpoint: observar o vídeo real em tamanho
SMS e a comparação normal/lenta; julgar intenção, força, trajetória e recuperação.
Não pedir novamente qual ação produzir. Registro do método atualizado no candidato
existente para curadoria futura; nenhuma skill, doutrina ou gate global promovido.
Parecer final `hayato_short_cut_body_temporal_independent_review_v4.json`:
`needs_evidence`. O revisor verificou todos os480quadros,13ações completas e12
ciclos com pausa integral; não percebeu playback contínuo. Sem novo defeito
estático/render identificado; absorção R03→R04, retorno R05→R06→guarda e apoios
são os intervalos prioritários para observação contínua, não defeitos provados.
Auditoria em memória do recorte Hayato+ancestrais:23artefatos/260arquivos passou;
auditoria global segue falhando no relatório Social61v5 histórico ausente.
Pacote privado `out/diagnostics/hayato_short_cut_v2/hayato_body_cut_v4_review.zip`
e recibo `doc/hayato_short_cut_body_retention_v4.json` preservam os insumos e
evidências com manifesto interno. Cópia de recuperação é local no mesmo disco.
Branch `codex/host-bootstrap-continuity-20261024`, base284b15be9bf1898219518973a366d3930deed2f2,
PR4 reutilizado; SHA final/testes/estado remoto em `out/diagnostics/hayato_short_cut_v2/publication.json`.
Sem hitboxes/dano/áudio/PAL/gameplay/AAA aprovados. Seções abaixo são históricas.

## Histórico da reformulação de coreografia — 2026-10-29

O dono aprovou identidade/acabamento, mas rejeitou a força e construção temporal
do corte v1. A escolha continua corte curto; C01–C04 e3/2/2/5 podem ser revistos.
Causa no prompt preservado: cabeça/pés/hakama fixos, punhos1–2px/recuo3px;
identidade foi traduzida incorretamente em corpo congelado. Parecer estático
pass não prova movimento. Nenhuma fonte, ROM ou evidência anterior foi apagada.
Contrato atual em `hayato_animation_contract_v2.json`, direção/defeitos/estudo de
referências em `hayato_short_cut_choreography_v2.json`. Diagrama gestual em
`out/diagnostics/hayato_short_cut_v2/rough/`:6desenhos,4/1/2/3/1/3 provisórios,
transferência de peso sem deslocamento da raiz. Esquema não é arte final.
Revisão independente do gesto2 sem blocker estático; percepção temporal pending.
Primeira chave acabada R03 em revisão; ainda não há sequência acabada ou ROMv2.
APNG iniciado no navegador e observado por snapshots; sem alegar percepção
contínua. Nenhuma leitura de contrato/FPS certifica coreografia/AAA.

O fechamento técnico da tentativa anterior existe: QA2/2,236framebuffers exatos,
10checks por orientação, holds apresentados3/2/2/5. Base27da9585…: janelas8s
59,69/59,82fps; selo3000frames,0derrame,mínimo207. Degrau128B63f72cfe…:
3000frames,0derrame,mínimo217. Sessões137aba3e… e66263eef… encerradas.
Esses dados qualificam somente aqueles pixels/tempos, não a nova ação.
O snapshot “Lote em andamento” abaixo é histórico e foi superado por esta seção.

## Lote em andamento — corte curto escolhido, 2026-10-29

O dono escolheu o corte curto como amostra artística e pediu prova antecipada
com guarda+execução. Direção textual em decisions/hayato-short-cut-diagnostic_owner_direction.json;
não é dano/hitboxes/frame-data, produção ou nova QA executada pelo dono.
Contrato diagnóstico hayato_animation_contract_v1.json: C01preparação,
C02execução,C03acompanhamento,C04recuperação, tempos provisórios3/2/2/5.
A escolha deixou de ser blocker; não perguntar de novo.

Primeira C02 foi preservada: coroa/apoio alterados e par mínimo10 nas128fases
por sentido com grade de referência fixa. Não foi buildada. Parecer independente
v1reprovou continuidade. A v2 restaurou apoios/estatura, passou revisão da chave
e materiais SMS e a prova guarda+execução nos dois sentidos (98patterns,pico8).
Foi necessário medir fases dos DOIS atores, sem mudar pixels/P1 do Social.

Fonte completa candidata em data/source_art/sprite_studies/hayato/review_drafts/
cps2_short_cut_v1/sequence_v1/cut_source.png:4poses144×144. C02 copiada byte-idêntica
à chavev2; só3poses de apoio foram geradas na terceira chamada deste lote.
Folha bruta1254×1254 traduzida num único2/9nearest para todas as3poses de apoio,
sem fit individual; originalguard/C02 preservados. Os shifts/pivôs são declarados,
não pintura/recorte da arma. Revisão integral de corpo/volume/arma/movimento e
materiais está pendente em hayato_short_cut_sequence_review_request_v1.json.

Configs ativas hayato_short_cut_sequence_v1_registered_{left,right}.json,
saídas out/diagnostics/hayato_short_cut_v1/registered_{left,right}/.
Todos os12PNGs têm última opacay71(boundary72), portanto tela143(boundary144).
C01/C04 precisaram inputanchorY126 antes de build: o nearest eliminava a última
linha esparsa de sola na projeção; C03 usa126 por sua sola-fonte,guard/C02usam127.
Uma única escala de corpo no par; não houve redução de alcance/omissão de células.
202patterns/6464B, máximo33SAT,pico8 nas10composições, tudo residente.

Três ROMs buildadas32KiB, ainda sem QA nesta atualização:
left a9e6ef0077e551af2652d42e332c66683fdd610ed3a1aafa9357249c0cdfa5aa;
right 27da9585d5ebd9f73b6969259213994d1faf85f5e62036cf116c90dbd6e0bc51;
stress128 63f72cfead2be96c0f35da41c0943b3b957da7d646c20d7c0538c0d0da59bb33.
Mesmo main e FSM, seleções MOF_HAYATO_SAMPLE5/6;3/2/2/5nos dados, não hitbox.
Corredor14sondas,C7D2..C7F9,folga1784B passou nos mapas atuais.
Previews normais/lentos em cut_cycle_nominal_4x.apng,cut_cycle_slow_4x.apng,
pair_cycle_nominal.apng; não são evidência do emulador nem fluidez certificada.
Próximo: terminar revisão integral, QAprivada nos2sentidos, ler holds reais,
FPS/VBlank e degrau128B neste SHA, preservar evidências/curadoria/commit/pacote.
Estado abaixo descreve o checkpoint estático anterior, sem herdar seus PASS.

## Continuidade corrente — Hayato, 2026-10-29

**Checkpoint da guarda concluído; ação própria pendente de escolha do dono.**
O pedido novo autoriza testar a repetibilidade no segundo personagem, não
promove automaticamente Hayato ou o Social. Concept Hayato v2 aprovado
`a8dc1478…`; fonte nova `hayato-cps2-idle-v02`, SHA
`0b72e603bbdebe50f81a62087ea2d070fab644641b8b70b1599c3dbe4ff6a8c1`.
Uma guarda estática,144×144,32RGBs salvos incluindo transparente, corpo~102px
incluindo cabelo,116px incluindo katana. Identidade jovem/esguia, quimono
branco, faixa vermelha, hakama laranja-vermelho e katana/bainha completas.
Duas gerações registradas: guarda diagonal v1 e edição v2 mais vertical;
não reutilizou estudo antigo como resultado novo. A fonte v2 passou14eixos
estáticos independentes; não houve pintura de personagem por código.

O teste cedo reprovou a diagonal:5sprites/linha+4Social=9 nas128fases dos dois
sentidos. Guarda v2 usa fase[0,1], mesma escala global nos dois atores, sem
encurtar espada/corpo ou omitir células. A P1 é exatamente a do Socialv8,
com15códigos, mapeada diretamente dos dois originais. O review da primeira
ROM achou branco amarelado e contorno de lâmina bordô: correção explícita no
adaptador oficial dos índices-fonte5→42,13→21,26→0;71pixelsSMS,0Social.
Índice13 também existe no pescoço/cabelo: review v2 aprovou a regressão focada,
sem aprová-lo para poses futuras. Fonte,alpha e geometria permaneceram intactos.

Registro final usa pivô-fonte Hayato(68,127), a sola realmente salva; o nominal
128 arredondava para um pixel acima do chãoSMS. Só translação(0,+1) na derivada;
os dois atores terminam emy143(boundary144). SocialJ04 espelhado usa fase[5,9]
medida, pois copiar[3,9] após esse ajuste gerava9; PNGSocial intacto. Parecer
v3 passou o adendo de alinhamento/recorte/material. Fonte/model/61posesv08.2
aprovadas do Social preservadas. Default do conversor reproduz seu header e
8PNGs v8 byte a byte; na nova P1 suas cores/pixels/PLTE também são idênticos,
compensados pivô e reflexão.

Ativos: `.mddev/hayato_cps2_guard_{left,right}_baseline_v3.json`,
`hayato_pair_social_jab_left_baseline_v3.json` e
`hayato_pair_social_jab_right_baseline_v3_mirrorphase.json`.
Manifestos `*_build.json` selecionam1..4 no mesmo consumidor por
MOF_HAYATO_SAMPLE; default e seleçõesSocial1/5/8 mantidos. Dados atuais em
`out/diagnostics/hayato_cps2_sample_v1/*baseline_v3*/`; configurações anteriores
são controles congelados históricos, não outras candidatas ativas.
Guardas:66patterns/2112B,32SAT, pico8. Socialjab contra guardaHayato:
222patterns/7104B, máximo35SAT e pico8 nos dois lados. Todas as poses residentes;
CRAM/patterns carregados com displayoff, somente SAT por tick na base.

QA nativa atual4/4casos,18checks exact-indexed;2/2capturas por guarda e
118/118framebuffers do jabSocial em cada lado. Últimaopaca143 confirmada.
Manual Button2/1 observado em vídeo; idle/J01 iguais emRGB não identificam IDs
por pixels. Não há jab nem outra ação de Hayato. Performance atual ROM direita
`035060f99e7763f898354238f81f5d6a9c588f03e7ff6d505538318c95011116`:
59,67/59,81fps em duas janelas8s; selo3000frames,0derrame,mínimo207.
Degrau128B, ROM `3540539e…`:0derrame,mínimo218. Sessões finais
442f14c70b3549a5bb3e8abaf0bf2147 e eca166b6c62a424b8775104fdf86d067,
encerradas/bundles válidos. Todos os12workersessions e6rootsessions deste lote
foram encerrados; as evidências anteriores ficaram históricas com seus SHAs.
Não transportar medições de variantes anteriores para estes binários.

Síntese/índice: `out/diagnostics/hayato_cps2_sample_v1/result.json`,
`comparison_guard_baseline_v3.png`, QA e pacote/recibo no mesmo diretório.
`doc/hayato_cps2_sample_v1.md` é o brief congelado de entrada do review; não
reescrever seus fatos iniciais como se fossem resultados finais. Pareceres
`hayato_cps2_idle_independent_review_v2.json` e
`hayato_cps2_pair_derivative_review_v{1,2,3}.json` preservam falha e correções.
Checklist:14eixos estáticos pass, ação/animação/owner pending, bloqueia promoção.
Registro global ainda falha pelo relatório histórico Socialv5 ausente; não
foi fabricado. Receita específica anotada no candidato existente de curadoria,
sem doutrina global/gate/ID novo. A escala absoluta legada68–72pxSMS não é
reclamada: este diagnóstico preserva a transformação do Social e corpos
aparentes~58–60px; equipamentos são medidos separadamente.

Próxima dependência irredutível: dono escolher corte curto de katana (proposta)
ou desembainhar/retornar à guarda. Pergunta já enviada, sem resposta recebida.
Depois contratar poses/durações como amostra artística diagnóstica, sem
aprovar dano/hitbox/frame-data competitiva, converter chave de execução cedo
junto ao idle, produzir/revisar sequência e renovar ROM/evidência. Não ampliar
atlas, elenco, cenários ou sistemas. Sem ação/continuidade animada não se
responde positivamente à repetibilidade completa. Sem áudio/PAL/gameplay,
owner ou entrega/AAA. Commit/SHA remoto e recuperação final no recibo do lote.

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-10-29 — Novo lote da mesma amostra: candidata de sequência v8, SHA
`877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41`.
Montagem indexada sem alterar pixels: cinco quadros da v5 e J04 reto da v6;
idle continua sendo o J01/v5 exato. Revisão integral da fonte/contato concluída no parecer v8,
sem herdar o PASS facial da v5 como aprovação automática. O adaptador oficial ganhou
fase explícita da grade tall por pose: padding transparente compensado no META,
sem mudar PNG/pivô/escala. J04 `[3,9]`: pico do par9→8, SAT33→34, PNG idêntico
à conversão da v6 antes reprovada; pool conjunto220 padrões/7.040B. Os outros
seis PNGs e Ken são idênticos à v5; defaults da v5 refazem header/PNGs idênticos.
Self-check reconstruiu pixels nas128fases; nove testes passaram, incluindo
largura realmente impossível e recusa de offsets negativos neste emissor unsigned.
Replay com o guard final refaz header/PNGs idênticos aos ligados na ROM.
ROM32.768B, SHA `452cd56594db3764da4b3d1c61e8e5f2e9d66714907b2edd3fbc453da3be240f`.
Parecer independente v8 passou os13eixos da fonte e chaves estáticas, inclusive
J04/rosto/equipamento. Não certifica percepção temporal nem aceite do dono.
QA nativa120/120 framebuffers exatos e7checks de fidelidade; sessão
`80cebe97316e468bbbcc2eec8ddac9fd` encerrada. Braço/punho/luva do J04 e Ken
inteiros, recuperação sem resíduos. SMRT:59,62/59,74fps em duas janelas8s;
selo3000frames0derrame/mínimo207, sessão `b3bc1620274a4f1faf3752275b533299`.
Degrau128B:0derrame/mínimo217, SHA `7ce342bc…`, sessão
`8905b516d2f445f8a8f15bd8adb30848`. Ambas encerradas.
Rastreio manual em sessão própria `b80042e52b4847d8a678693a7eee819e`, encerrada:
13casos RAM/journal passaram, ordem/holds2/1/1/1/1/3,21framebuffers exatos e
lag1VDP entre pose submetida/apresentada. Idle/J01 iguais emRGB dependem também
do probe. A coleta anterior após performance, com teclas0 na amostra de2VDP,
foi preservada como cobertura falha; nova linha lê cacheSDK e probe a cadaVDP.
Não houve correção de SDK/ABI: ROM e input funcionaram no traço controlado.
As quatro sessões foram encerradas; sem herdar evidência das ROMs anteriores.
Os microdetalhes SMS e o julgamento de playback contínuo permanecem para aceite
humano; checklist revisado bloqueia promoção. A fonte61poses v08.2 continua
aprovada separadamente. Relatório histórico v5 ausente ainda bloqueia auditoria
global do registro; não há relatório fabricado. Publicação/recuperação do lote
ficam em `contact_grid_v8/publication_receipt.json` e `archive_receipt.json`.
Sem ampliar desenhos/timing, atlas, personagens ou movimentos. Fonte e prova
em `jab_revision_v8/` e `out/diagnostics/dr_social_cps2_sample_v1/contact_grid_v8/`.

2026-10-29 — Continuidade da amostra: fonte **v5** selecionada como candidata
para diagnóstico, SHA `44ae0342e9db909d467907c1c21633165f5ee8dd1034b90d596d38498abd9c05`.
A revisão independente v5 passou **somente o reparo facial**: aro/lente de latão
reconhecíveis nos seis rostos, sem regressão corporal material observada. Não é
aceite artístico completo, animação, SMS, ROM ou aprovação do dono. A v4 não
fechou o rosto; v6 alongou J04 e o conversor reprovou o par; v7 permaneceu com
articulação de contato insuficiente e não foi selecionada. Tentativas preservadas.
O ramo seguinte usa v5 na ROM para conferir sobrevivência facial e registrar o
gesto compacto para julgamento temporal, sem mais gerações genéricas do braço.
Conversão v5: 216 padrões/6.912 B, SAT31 nas poses salvo J04=32, pico8 em todos
os sete pares. Seleção diagnóstica `MOF_CPS2_SAMPLE=5`; valor1 preserva os dados
anteriores. Build v5:32.768 B, SHA `fc46d77b9fea6ffd63c262aa085de3e1e623409c1db3e706e163d9d2439cf24b`.
QA nativa independente:1/1 caso,120/120 framebuffers exatos e seis checks de
fidelidade, sessão `b2f3d33e89d84c9f8c68e089eacb6059` encerrada. A assinatura dos
óculos ainda se comprime em poucos pixels e lapela/colete perdem definição no
SMS; review técnico não os aprova artisticamente. Performance própria:
`93578b87ccbe4375931aec912dc9cd8d`,59,62/59,79fps em janelas8s, selo3000frames
sem derrame (`vline_min=207`). Stress+128B, SHA `a5c013a8…`, sessão
`c3161d84042a4bda9367fa521597b810`,sem derrame (`vline_min=217`). As três sessões
foram encerradas e bundles conferidos. Seis testes do adaptador e gates de
recurso/scanline/semântica/contrato/corredor/vínculo/QA passaram; checklist
artístico permanece pending/bloqueia promoção. Não transportar estes PASS para
outras ROMs, gameplay, áudio, PAL ou produção. Contato J04 requer julgamento
temporal da mídia nova; óculos na escala SMS e aceite do dono continuam abertos.
Handoff e mídias: `doc/dr_social_cps2_sample_v1.md`, seção de2026-10-29, e
`out/diagnostics/dr_social_cps2_sample_v1/face_revision_v5/`. Publicação/commit
final são registrados no `publication_receipt.json` desse diagnóstico.

2026-10-29 — O dono aprovou explicitamente **o método** da amostra CPS2 e
pediu registro para curadoria futura e avanço ao próximo passo. Decisão, receita,
fontes/ROM/pacote por SHA, resultados e limites registrados em
`doc/curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`.
Método aprovado para continuidade; homologação global permanece futura, sem
novo ID de lição, mudança de doutrina ou promoção de arte inferida. A revisão
v2 continua `revise_before_growth`: próximo delta é rosto/óculos e clareza do
contato J04, mantendo o mesmo escopo idle + jab. A v08.2 permanece aprovada
separadamente. Os números abaixo são da ROM v3 já medida, não de arte futura.

2026-10-28 — Amostra autoral CPS2 v3 produzida como candidata: uma pose idle
(cópia de J01) e `social_light_jab` J01–J06, sem expansão do atlas. Fonte
384×256/30 cores, seis células 128×128, corpo ~104 px, alpha binário; SHA
`04d21085…`. Receitas, prompts, originais e tentativas preservados no Git;
implementação/arte em `ba706e8`. Relatório/handoff: `doc/dr_social_cps2_sample_v1.md`.
ROM diagnóstica 32.768 B, SHA `f5d54b15…`, observada no Emulicious: par
Social/Ken íntegro, 31 SAT/pico8, pool212 padrões. Fontes→SMS→header→ROM ligados
por hashes; dados buildados conferem com o fonte/header atuais. QA nativa
independente `/root/social_runtime_qa`: 1/1 caso passou, 120 framebuffers
exatos, sessão encerrada. J02–J06 apresentam holds1/1/1/1/3; J01/idle têm
pixels iguais e seus IDs dependem também da sonda, com latência observada de
um frame entre submissão SAT e framebuffer. FPS em janelas8s:59,43/59,56;
janelas curtas anteriores58,8/59,23 falharam. Worst-frame autônomo3000frames
passou, zero derrames, `vline_min=207`; degrau+128B passou, mínimo217.
As quatro sessões do lote foram encerradas. Seis testes do adaptador e gates
de recurso, scanline, semântica/contrato, fonte raster, vínculo, tilemap,
debug/corredor passaram após self-checks. Isso paga apenas o trecho diagnóstico
NTSC; sem gameplay, cenário/HUD, áudio novo ou entrega de produção.

Revisão artística v2: `revise_before_growth`. Cabelo cinza/abas/J03 melhoraram,
mas óculos variam entre poses, contato J04 precisa leitura mais inequívoca e a
conversão enfraquece rosto/lapela/colete. Checklist bloqueia promoção; dono
ainda não aprovou esta fonte CPS2. Próximo delta: rosto/óculos e contato,
revisão hash-bound antes de qualquer ampliação. Comparativos/animação/ROM e
evidência estão em `out/diagnostics/dr_social_cps2_sample_v1/` e `out/candidates/`.

Pacote de revisão `dr_social_cps2_sample_review.zip` no diagnóstico: 263 arquivos
verificados pelo manifest interno, SHA `9536b5a5…`, 3.165.950 B. Cópia local de
recuperação idêntica e recibo em
`/home/misael/.local/share/project-recovery/SMSForge/artifacts/dr_social_cps2_sample_v1.zip`.
Fontes/receitas ficam no Git; esse arquivo protege os gerados fora de `out/`,
mas não é backup em outro host nem release de produto.

Foi conferida a decisão artística v08.2 existente e o PNG aprovado em
`res/approved_art/dr_social/`, SHA `4e557095…`. As afirmações históricas abaixo
de aprovação pendente estão superadas somente nesse escopo. A aprovação foi
preservada sem inferir conversão/runtime/budget; identidade segue no model v4.
Variantes `cps2-idle`/`cps2-light-jab` são candidatas distintas. Bloqueio
organizacional preexistente: relatório histórico v5 ausente impede PASS global
do registro. Seu kind também não representa no head genérico a fonte artística
aprovada em res/; a decisão/hash exatos permanecem na reconciliação. Nenhuma
aprovação ou relatório histórico foi fabricado.

2026-10-12 — Diretriz v08.2 executada como candidata determinística. A reclassificação autorizada atravessou fronteiras de materiais/contorno, preservando alpha e grade; o casaco foi limitado aos índices 5/6. Uma auditoria independente por célula encontrou zero singletons e zero componentes sem bloco sólido 2×2 em cabelo, casaco e pele. Permanecem 11 cores úteis, zero vazamentos semânticos, 85 pixels de óculos dourados, haste branca de 1.245 pixels e zero pixels não cinza na máscara do cabelo em 61/61 poses. Foram adicionados 863 pixels ao contorno por voto de vizinhança, sem modificar nenhum pixel do contorno original. A candidata ainda aguarda revisão visual do dono; não foi promovida, integrada em `res/` nem compilada em ROM. Amostras, relatório, máscaras e log estão em `data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_2_final_candidate/`; contrato, diretriz e registro de curadoria estão em `doc/dr_social_sprite_mask_contract_v08_2.json`, `doc/dr_social_sprite_rebuild_directive_v08_2.md` e `doc/curation_candidates/2026-10-12_dr_social_v08_2_cluster_consolidation.json`. A matriz v07 permanece congelada como geometria; model sheet CPS2-Alpha-Cel v4 continua a referência aprovada de identidade.

2026-10-12 — Diretriz v08.1 e candidata de cor: o dono autorizou os óculos de latão na zona amarela e confirmou a preservação de 85 pixels faciais. O passe determinístico classificou os 36 resíduos da auditoria v08, zerou vazamentos branco/amarelo/bordô/cinza e deixou 1.245 pixels da haste da bengala brancos e uniformes; alpha, grade 8×9, 61 poses e paleta indexada foram preservados. A inspeção também localizou e corrigiu a sombra avermelhada da franja: 1.014 pixels avermelhados foram recuperados como cabelo cinza e há zero pixels não cinza dentro das máscaras de cabelo em 61/61 poses. A limpeza 2×2 ainda falha: restam 73 singletons de cabelo, 96 do casaco e 341 da pele (102/139/553 componentes abaixo de 2×2). A candidata não foi promovida, integrada em `res/` nem compilada em ROM. Arquivos: `doc/dr_social_sprite_mask_contract_v08_1.json`, `doc/dr_social_sprite_rebuild_directive_v08_1.md` e `doc/curation_candidates/2026-10-12_dr_social_v08_1_cluster_consolidation.json`; amostras e relatório estão em `data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_1_masks_candidate/`. A matriz v07 segue congelada como geometria; model sheet CPS2-Alpha-Cel v4 segue como única referência de identidade.

2026-10-12 — Registro-base v08: o dono rejeitou artisticamente a sprite sheet v07 de 61 poses, SHA-256 `f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`: o casaco perdeu hierarquia, o cabelo varia entre cinza e avermelhado/castanho e o cel shading ficou granulado. A diretriz v08 congelou paleta indexada, papéis de material, cabelo exclusivamente cinza e planos contíguos; o dono autorizou máscaras explícitas por material e clustering determinístico apenas dentro delas, com ImageGen/difusão proibidos. A tentativa generativa anterior falhou (1182×1330, fundo opaco, 287.407 valores RGBA) e está arquivada em `doc/curation_candidates/2026-10-12_dr_social_v08_imagegen_trial_rejection.json`. Contrato base: `doc/dr_social_sprite_mask_contract_v08.json`.

2026-10-11 — O proprietário aprovou a model sheet CPS2-Alpha-Cel v4 do Dr. Social depois de a revisão independente passar sem blockers. A candidata foi promovida no índice central como head `approved` do papel `model_sheet/main`; v2 foi marcada `superseded` e arquivada, enquanto a concept sheet v3 continua aprovada apenas como referência separada de identidade. A raiz `data/source_art/concept_art/dr_social/` contém agora somente a folha v4, metadata, lineage e prompt canonizados. A cópia exata usada na revisão independente permanece em `review_drafts/model_sheet_cps2_alpha_cel_v4_candidate/` como evidência; nenhuma imagem foi apagada ou teve pixels alterados. O mapa de relocação e hashes está em `doc/curation/dr_social_model_sheet_v4_promotion_organization_2026-10-11.json`. L127/§117 registra o fluxo de delta explícito, invariantes, dupla checagem, decisão com escopo e arquivamento. A aprovação cobre somente model sheet: sprite, moveset, animação, conversão SMS, integração e ROM seguem separados.

### Registro da organização inicial (2026-10-11)

Na organização inicial, ficaram como referências estritamente aprovadas as concept sheets já marcadas como owner-approved nas linhagens do elenco (Alis v4, Golden Axe Warrior v2 com paleta SMS, Hayato v2, Dr. Social v3, J.J. v4 e Landau v1), o model sheet CPS2-Alpha-Cel v2 do Dr. Social e a prancha de harmonização Waku Waku 7 em duas páginas (Landau 80 U, J.J. 75 U e pistola Zillion corrigida). As decisões do dono e hashes estão em `doc/decisions/`; o índice é `../../doc/artifact_registries/master_of_fighters.json` (catálogo central). A aprovação da prancha é apenas para comparação visual do elenco; revisão artística independente permanece pendente e nenhuma sprite sheet, animação, conversão SMS, integração ou ROM foi aprovada por esse registro. Rascunhos e estudos de concept/model foram movidos para subpastas `review_drafts/`; o model sheet CPS2 v1 permanece em `historical_approved/` como baseline anterior aprovada. O mapa reversível de movimentações está em `doc/curation/artifact_organization_2026-10-11.json`.

2026-10-10 — O dono aprovou a direção do moveset do Dr. Social e autorizou a produção sequencial das folhas de golpes. O contrato v2 contém 20 estados comuns e 8 sequências ativas de combate; `audit_animation_contract.py` reportou 29 sequências/224 poses-fonte propostas, mantendo objetos VDP e custos de hardware separados. O primeiro jab continua em arte candidata. A v4, arquivada em `data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v4/`, deixou os óculos redondos legíveis e mantém seis poses organizadas em 3×2, mas o preflight mediu 1536×1024 RGB e 83.402 cores; o fundo visualmente preto não é chave uniforme. O checklist hash-bound bloqueou promoção com 3 eixos em fail e 7 pendentes. A tentativa v5 com `transparent_background: true` também falhou: 219.818 valores RGBA, alpha 0–254 e halo luminoso; foi arquivada apenas como evidência em `review_drafts/2026-10-10_social_light_jab_v5_alpha_attempt/`. Nenhuma versão foi aprovada, quantizada, colocada em `res/` ou compilada em ROM. Aprovação do dono e revisão independente seguem pendentes. Lições locais estão em `doc/curation_candidates/2026-10-10_dr_social_sprite_sheet_generation_gate.json`; o agente canônico não foi alterado.

2026-10-10 — Foi registrada a estrutura canônica de sequência animada com L113/§109. O contrato inicial do Dr. Social lista 20 estados comuns e 4 ciclos de combate candidatos: 24 sequências e 191 poses-fonte propostas. `audit_animation_contract.py --self-check` e a validação do contrato passaram. Ainda não há PNGs de animação promovidos: moveset/frame-data, aprovação humana, decomposição metasprite, mapa P1, orçamento de runtime e validação em emulador continuam pendentes. A pesquisa de armas do jogo original tem conflito entre fontes comunitárias e fica aberta até confronto com manual/ROM. A primeira tentativa visual de atlas básico (9 sequências/61 poses) ficou em `data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_basic_sequences_atlas_v1/`; duas revisões não removeram halos azul/ciano nem alpha/paleta fora do contrato, portanto aquele rascunho gerado não entrou na linhagem canônica nem em `res/`. A rejeição não se aplica à imagem diferente anexada depois pelo dono, agora registrada por SHA como fonte aprovada para conversão.

O fluxo consolidado de criação, revisão, harmonia do elenco, prova técnica, conversão e promoção está em [`fluxo-criacao-curadoria-personagens.md`](fluxo-criacao-curadoria-personagens.md). A conversão v10 das 61 poses é histórica: ROM diagnóstica e comparação exata 61/61 permanecem evidência da antiga fonte v1. V10 não é a fonte visual atual nem foi promovida a `res/`. A v2 falhou no preflight, v6/v7 foram tentativas de reconstrução derivadas e v07 foi rejeitada artisticamente pelo dono em 2026-10-12. A diretiva ativa é v08; ainda não há nova sprite sheet. A síntese canônica transversal foi registrada como L123/§113 em `doc/curation/2026-10-10_l123_ciclo_arte_autoral_ate_rom.json`.

### Síntese de refinamento do sprite — L124 (2026-10-10)

A revisão v6–v10 confirmou que converter as cores para uma paleta legal não
resolve a continuidade de luz nem o papel semântico de cada pixel. A v6 testou
média de área dentro do tecido (6.145 pixels); v7 ordenou a rampa por luminância
(15.690 mudanças), mas foi rejeitada e só teve três poses comparadas no
framebuffer. V8 reorganizou 927 clusters e passou a comparação integral 61/61,
mas a máscara limitada a pixels internos deixou vazamentos de borda. V9 ancorou
amarelos a cabelo/face e à junção luva-haste (249 pixels), e a inspeção posterior
encontrou 70 brancos isolados/pares. V10 removeu esses 70 sem alterar alpha,
paleta ou geometria e passou comparação exata 61/61; clusters maiores, revisão
independente e aprovação do dono continuam pendentes. A rotina reutilizável e
seus limites estão em `doc/curation/2026-10-10_l124_fluxo_sombra_material_sprite.json`
e SMS_GLOBAL §114.

### Contrato de animação Dr. Social — proposta v1 (2026-10-10)

Arquivos: `doc/dr_social_animation_contract_v1.md` e `.json`. A proposta
documenta idle, avanço/recuo, pulo/aterrissagem, crouch, dash, queda, rolagem,
guard, duas vitórias, derrota por tempo, empate, duas provocações, duas
apresentações e três retratos versus, além de quatro candidatos (toque de
bengala, lunge de rapieira, riposte, bumerangue). Cada track de objeto tem
estados inicial/final e contagem de poses separada. Cada sequência revê os 12
princípios e planeja aplicar pelo menos sete, ligados a IDs de quadro; essas
pistas ainda não são evidência visual.

O campo `source_pose_count` conta desenhos planejados, não objetos VDP. Os
valores candidatos de startup/active/recovery, alcance e dano estão marcados
`proposal_unmeasured`; não foram testados nem aprovados. Um guia de SMS relata
Button 1 para ataque, Up+1 para subarma, Button 2 para pulo e armas de curto e
longo alcance; há divergência entre fontes nos nomes das armas primárias. Não
cristalizar nomes ou mecânicas antes de revisar o manual e a ROM original.

### Histórico: fonte aprovada de animação v1 — 61 poses; janela VDP corrigida (2026-10-10)

O dono havia designado `data/source_art/sprite_studies/dr_social/
historical_approved/basic_sequences_61f_owner_source_v1/
dr_social_basic_sequences_61f_owner_source_v1.png` como fonte aprovada para
conversão de produção, SHA-256
`a95fc144f6d2574a9dfb43028b7b1d1fc91108b442f03fcfebac2df3f6d56057`.
Essa aprovação permanece histórica; a folha foi arquivada em 2026-10-11 e
deixou de ser referência visual ativa. Na época, ela continha 9 sequências com contagens
`4+8+8+8+5+8+8+8+4 = 61`; a aprovação da fonte não promove automaticamente a
quantização/conversão nem o runtime.

A primeira conversão tratou os 256 índices lógicos como 256 padrões residentes
seguros. Com sprites na base 0x2000, PNT em 0x3800 e tile base 257, o espaço
real antes da name table é 191 padrões. Pools de 200/246 padrões sobrepuseram
a name table e corromperam rótulos. `pack_sms_metasprite.py` agora deriva o
limite físico pelas bases do layout; `--self-check` verifica a capacidade 191
e reprova 192. No viewer v5, idle (169) e defesa (182) usam pool compartilhado;
os outros sete estados carregam um quadro por vez. A ROM diagnóstica usa a
fonte aprovada, contém 61 PNGs 80×80, mede pico de 8 sprites/scanline e 51
entradas SAT, e foi vista no Emulicious com as nove sequências e endpoints
CR05/GU04. Build: 114.688 bytes; SHA e captura estão nos registros vinculados.

Esses resultados provam navegação e renderização dos quadros no viewer; não
provam gameplay, animação contínua, FPS, áudio, VBlank de produção, cenário/HUD,
paleta P1 global ou hardware físico. O atlas convertido fica em
`out/diagnostics/`, não em `res/`; conversão pixel-a-pixel e aprovação técnica
permanecem pendentes.

Prova técnica v4: `data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.png` e JSON homônimo. Canvas 80×80, nearest-neighbor 5/6; pose idle frame-fonte 01 e ação frame-fonte 06. Contagem: 42 padrões únicos idle, 47 ação, união de 89 (2.848 bytes 4bpp). A ponta arredondada foi conferida visualmente na amostra e requer novo aceite do dono/revisor; a forma correta da bengala, altura anatômica sem equipamento, regiões de material, anatomia e orçamento de runtime continuam gates. `audit_asset_proof_sheet.py` confere a reprodução de pixels e exige eixos explícitos para geometria do terminal e altura do corpo separada de equipamento, mas não decide identidade visual sozinho. `doc/palette_runtime_contract_v1.json` define propriedade das tabelas CRAM; a seleção final da paleta P1 continua sem mapeamento. Nada foi integrado em `res/`, ROM ou emulador.

Folha #14 `Gouache-Fantasy-Art` v3 corrige a pose de ação: braço do boomerang dobrado junto ao quadril, cotovelo e pegada legíveis, espaço negativo separando-o do braço da rapieira. Quatro vistas, identidade, paleta e folha padrão foram preservadas. A ficha traz índice #14, Shinichi Kameoka, papel de designer de personagens e assinatura visual. Casaco/lapela ainda diferem da referência aprovada; 17 eixos, revisão independente e aprovação do dono continuam pendentes. Arte-fonte v7, prompt, composição v3, metadata, lineage, checklist, pedido de revisão e relatório estão registrados.

As folhas atuais #01–#05, #07–#10, #14 e #15 exibem índice estável e referência de estilo; #03 (Eisuke Ogura) e #05 (Toshiaki Mori/Shinkiro) explicitam assinaturas diferentes, e #08 declara crédito individual não confirmado. Uma revisão de composição com coordenadas antigas foi reprovada visualmente e isolada em `data/source_art/concept_art/dr_social/review_drafts/2026-10-08_bad_metadata_recomposition/`; nenhuma dessas imagens foi promovida. Estado do manifesto: 1 referência aprovada, 10 candidatas pendentes, 3 bloqueadas, 35 não iniciadas (49 estilos). A anotação de estilo #13 no histórico deste arquivo diverge do status atual `not_started` do manifesto; exige reconciliação de evidência antes de alterar o status.

A sequência avançou até o estilo 14. `Gothic-Ayami-Art` (#11) e `Detailed-Military-Caricature` (#12) ficaram bloqueados após quatro gerações cada: não alcançaram distinção estilística consistente, apesar dos prompts/revisões preservados. `Fairytale-Storybook-2D` (#13) tem uma nota histórica de bloqueio após quatro gerações, mas o manifesto ativo marca `not_started` e o source atual contém somente um prompt; status exige reconciliação do material antes de classificar ou gerar novamente. `Gouache-Fantasy-Art` (#14) permanece candidata: após seis tentativas, v7 reposiciona o braço que lança o boomerang baixo junto ao quadril, com cotovelo/pegada legíveis e separação visível do braço da rapieira; a v3 composta em 2400×1440 registra Kameoka/assinatura visual. A variação de casaco/lapela ainda aguarda decisão do dono. Checklist v3/hash-bound tem 17 eixos pendentes, revisão independente e aprovação do dono. Contagens do manifesto: 1 referência aprovada, 9 candidatas pendentes, 3 bloqueadas, 36 não iniciadas (49 total). A prancha visual final com folhas individuais ainda não foi produzida.

A folha 10 `Digicel-Handdrawn` foi registrada em 2026-10-08 como candidata após três tentativas preservadas. V1–V2 foram descartadas por acabamento brilhante/fighter e efeito violeta; v3 apresenta contorno orgânico mais leve e planos cel amplos. Face, identidade, traje e armas permanecem pendentes de review; não é arte pixel/SMS. Arte, prompts, metadata, checklist, pedido/plano e lineage ligados ao manifesto; owner e revisão independente pendentes.
A folha 09 `Extreme-SD-Parody` foi registrada em 2026-10-08 como candidata a partir da segunda tentativa. A primeira repetia o acabamento sério e inseriu efeito violeta grande; a segunda usa contorno arredondado, expressão brincalhona adulta e gesto elástico, sem encurtar o biotipo. Vestuário contém detalhes dourados extras para revisão. Arte-fonte, prompts, metadata, checklist, pedido/plano e lineage hash-bound; owner e independent review pendentes.
A folha 08 `32Bit-Mecha-Chibi` foi registrada como candidata após quatro gerações preservadas; v1–v3 tinham uma lâmina solta, e v4 separa visualmente a bengala das vistas ortográficas e rapieira/bumerangue da pose final. O acabamento de cel de animação é mais simples; figurino ainda contém colete/botões divergentes. Cinco vistas, composição 2400×1440 e registro hash-bound; eixos, revisão independente e dono pendentes.
A folha 07 `HiDrive-Anime-Vector` foi composta como candidata a partir da quarta geração: cinco vistas e tratamento de contornos/sombras geométricas, com uniform scale 0.78 para manter separação das legendas. As três primeiras tentativas foram preservadas e descartadas por semelhança com o acabamento anterior. Cabelo, óculos, casaco azul/ciano, rapieira, bengala e bumerangue estão visíveis; detalhes de figurino e distinção estilística precisam review. Checklist, request/plan e lineage hash-bound permanecem pendentes.
A sequência 06 `Classic-Arcade-Heroic` permanece bloqueada: quatro imagens foram geradas e preservadas (inicial + três revisões), mas todas repetem acabamento de mangá polido e não atingem a distinção visual clássica plana exigida. Nenhuma foi registrada como folha candidata. Prompts, hashes e causa estão em `data/source_art/concept_art/dr_social/review_drafts/style_series/style_06_classic_arcade_heroic/dr_social_model_sheet_06_classic_arcade_heroic_blocked_record_v1.json`; revisitar após avançar estilos independentes.
2026-10-08 — folha 05 `Urban-Seinen-KOF` gerada em três tentativas preservadas; as duas primeiras foram descartadas por cabelo, traje e arma divergentes. A terceira foi composta em 2400×1440, com cinco vistas, close, pose, régua 7.5H, fichas, fundo creme e selo CANDIDATE. Cabelo grisalho, óculos, casaco longo azul/ciano, bengala, rapieira e bumerangue de aço estão visíveis; o figurino ainda difere parcialmente da referência aprovada. Todas as 13 axes artísticas, revisão independente e aprovação do dono permanecem pendentes. A folha é concept candidate; não é sprite art nem asset SMS. Arte-fonte, prompt, metadata, checklist, pedido/plano de review e lineage vinculados em `dr_social_style_series_manifest_v1.json`. Restam 44 estilos sem folha registrada.

2026-10-07 — primeira folha de model sheet do Dr. Social foi aprovada pelo dono
como documento-base da série de estilos, usando o estilo inicial `CPS2-Alpha-Cel`. A
folha contém frente, perfil, costas, close do rosto e pose de identidade, com
régua relativa, linha de base, fundo creme e campos de estilo diagramados.
O desenho segue a concept v3 aprovada e o contrato de paleta. O formulário
permanece experimental, sem promoção a skill/workflow ou validação de sprites
derivados. O catálogo inicial tem 49 estilos; a primeira referência está
aprovada pelo dono.
A segunda folha, `Dark-Gothic-Pop`, a terceira, `Late-SNK-Realism`, e a quarta,
`CPS3-Fluid-Mastery` (`Street Fighter III: 3rd Strike`), estão registradas como
candidatas; aguardam revisão do dono e revisão independente. As folhas 02–04
agora exibem os cinco títulos de vista pelo compositor e usam amostras da paleta
oficial. As checklists 02–04 passaram a verificação de cobertura e hashes; os 13
eixos artísticos de cada uma continuam pendentes. Os planos de revisão independente
foram registrados, sem parecer atribuído. Restam 45 estilos sem geração. Estas
ilustrações são concept sheets, não sprite sheets nem recursos SMS. Lineages,
checklists, pedidos e planos estão nos diretórios `data/source_art/concept_art/dr_social/`
e `doc/` do projeto.
Especificação, prompt, arte gerada e lineage ficam em
`data/source_art/concept_art/dr_social/` e
`doc/curation/2026-10-07_model_sheet_formulario_dr_social_cps2.json`. A revisão
hash-bound em `doc/dr_social_model_sheet_review_v1.json` foi atualizada: esquema
e hashes consistentes, aprovação do dono registrada, 13 eixos e revisão
independente pendentes; a folha é referência aprovada para a série, sem promoção
ao skill.

2026-10-05 — o dono avaliou que as falhas estruturais mais graves do roster
foram corrigidas e listou polimento restante: clusters e cel shading suaves no
Shinobi/Alis, olhos/rosto, contornos de pés/capas/casaco, volume de escudos,
encaixe da espada-cana, arco/corda de Landau e fidelidade da arma/rosto de J.J.
O complemento do dono esclarece o padrão: contornos contínuos em degraus de
pixel, clusters e cel shading definidos, sem blur, antialiasing ou dithering;
a mão de Hayato também exige verificação de um dedo pouco legível.
O feedback textual hash-bound está em
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_owner_feedback_20261005.json`;
a checklist por personagem está em
`doc/roster_harmony_refinement_review_v1.json` e ainda bloqueia promoção.
O feedback não anexou a imagem pós-tratamento. A prancha atual
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_proportion_comparison_v2.png`
compara os sete candidatos hash-bound no frame 00, ampliados 3× nearest-neighbor,
sem reescala individual e com baseline comum. A v1, com 3000 px, era reduzida
fracionariamente no visualizador; a v2 tem 2048 px para preservar degraus de
pixel na exibição. As alturas opacas vão de 73 a 80 px; 7/7 ficam nas bandas
métricas de trabalho do contrato. O dono apontou ruído no contorno do Shinobi:
o frame 00 tem alfa binário e um componente conectado, sem ilha solta, mas o
contorno da arte-fonte segue em `fail`. A prancha mede escala/silhueta, não
aprova estilo ou anatomia nem confirma que estes candidatos são a versão
pós-tratamento exata. Nenhum PNG-fonte foi alterado. Medidas e hashes estão no
JSON companheiro.
L107 tornou os oito micro-eixos obrigatórios para folhas/pranchas de pixel
sprite e registrou que uma edição generativa de folha pode mudar poses/ações.
Quatro testes de geração foram descartados após alterar escala/poses ou trocar
idle por gesto/ataque; nenhum PNG de origem foi substituído, nenhuma folha foi
aprovada e nada foi integrado em `res`/ROM.
As auditorias de recurso dos sete candidatos passam agora com os IDs canônicos
de paleta. Alis, Landau e J.J. tinham PNGs indexados em 4 bits; cópias v1 em
8 bits foram feitas com `prepare_sms_pixel_art.py`, compararam `AE=0` com as
fontes e preservaram os originais. Lineage em
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprite_index8_reencodes_v1.json`.

2026-10-04 — o dono identificou falhas anatômicas e de encaixe de armas nos
sete personagens da prancha: olhos/rosto, mãos e polegares, empunhaduras, guarda
e lâmina, articulações, tiras/perspectiva de equipamento, pés/baseline, outline,
ruído de recorte e coerência de luz. O fluxo de revisão independente já existia,
mas não exigia esses eixos por personagem. L106 adiciona o runbook
`tools/sms_wrapper/.agent/workflows/art-review.md`, o gate
`audit_art_review_checklist.py` e a regra §91. O quadro corrigido v2 está em
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v2_review_candidate.png`,
com lineage e checklist ao lado. É uma ilustração RGB 2172×724, não sprite SMS;
está pendente de revisão independente e aprovação do dono. Nenhuma folha de
sprites foi substituída ou aprovada nesta revisão.

2026-10-04 — concept art J.J. v4 aprovada pelo dono. O sprite de Zillion II
continua fonte de identidade, paleta e comportamento; a pedido do dono, a ficha
e a arte colorida do anime foram consultadas apenas para construir/mapear o
figurino. Essa fronteira foi registrada como L103, no contrato e no lineage;
nenhum pixel, pose ou composição foi copiado. Concept v4 1536×1024: 13 cores
úteis, índice 0 transparente, sem dithering, gate de recursos aprovado.
L104 registra o defeito seguinte: 13 pixels #AA5555 no topo do cabelo passavam
conectados ao contorno e davam ruído no recorte. A folha
`data/source_art/sprite_studies/jj_zillion_ii/jj_idle_12f_sms_96px_v5.png`
remove esses 13 pixels sem mudar outros pixels, escala ou poses. Tem 12 quadros
únicos em células 96×96, 13 cores úteis, altura visível 72–76 px, largura
61–66 px e baseline y=95. Passaram os gates de recursos, semântica/geometria e
recorte por região de material. A folha aguarda sua própria revisão visual;
nada está em `res/` nem foi visto em ROM/emulador. Qualidade AAA fica registrada
como alvo do trabalho, sem claim ou certificação.

2026-10-04 — o dono confirmou a harmonia das concepts do elenco e pediu que a
revisão conjunta de escala, estilo e morfologia passe a ser atenção permanente
do agente. A montagem frame00 v1 continua preliminar, não é sprite oficial: a
medição encontrou Golden Axe 78×88 contra Alis 60×73, Dr. Social 44×81 contra
Joe 62×80, Landau 63×87, Alis 60×73 e J.J. 63×76. O perfil e a auditoria
`doc/roster_harmony_contract_v1.json` / `audit_roster_harmony.py` registram
limites de trabalho e evidência; L105 acrescenta a prática ao agente canônico.

2026-10-03 — paleta SMS Hayato aprovada (L100), limpeza Hayato aprovada pelo
dono (L101), geometria por quadro registrada e medida (L102). L101 aplicada ao estudo Dr. Social; variante v5 indexada recebeu
aprovação visual provisória do dono, com revisão futura do design. Conceito
Alis v4 recebeu aprovação visual explícita, incluindo a família cromática
original; fidelidade de cor está registrada como candidata a curadoria. A
concept art Landau v1, rejuvenescida, foi aprovada integralmente pelo dono
como referência visual para o estudo de sprites. Mantém o jovem adulto sem
barba ou bigode, roupa, acessórios e armas aprovados, usa 14 cores úteis da
paleta SMS corrigida e passou no gate de recursos. A aprovação da concept art
não aprova a folha de sprites nem sua integração em ROM. A folha idle v3 tem
12 quadros indexados, passou nos gates de recursos e semântica/geometria e foi
aprovada visualmente pelo dono em 2026-10-03 como estudo de referência. Continua
fora de `res`, sem vínculo com ROM ou validação em emulador.
Revisão Dr. Social v9 (2026-10-03): a conferência do sprite original SMS
mostrou que o contrato anterior de roupa cinza não correspondia ao jogo. A
fonte `doc/build_palettes_manifest.py` e o manifesto foram atualizados para
azul/ciano, sombra teal, cabelo grisalho e botas castanhas; o contorno opaco é
navy #000055 para manter o índice 0 transparente. A folha nova
`data/source_art/sprite_studies/dr_social/dr_social_idle_guard_12f_sms_96px_v9_clean.png`
tem 12 quadros distintos em células 96×96, 12 cores úteis, zero dithering,
um componente conectado por quadro e medidas de largura 44–84 px, altura
72–84 px e linha de base 84–88 px. Passou nos gates de recursos e semântica de
animação. Estado `source_candidate`, aguardando revisão visual do dono; a v5
permanece apenas como referência histórica provisória sob o contrato cromático
anterior. Nada integrado em `res` ou validado em ROM/emulador.
Concept art Golden Axe Warrior v1 também foi criada em duas poses, com paleta
SMS regenerada e gate de recursos aprovado; segue `source_candidate`, aguardando
revisão visual do dono.
A folha guard-motion de 12 quadros foi criada como `source_candidate` e passou
nos gates de recurso e semântica de quadros.
Correção de lore: **Dr. Social NÃO vira vampiro**; sweep aplicado em
GDD, paletas, moveset draft e directive de concept art (detalhes em Decisões).
Bootstrap: 2026-10-02 via `tools/sms_wrapper/new_project.sh
master_of_fighters` (prova: saída `[OK] projeto instanciado` + 9 arquivos da
hierarquia verificados pelo próprio script).

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | não iniciado | — |
| validation_report | não iniciado | — |
| boot no emulador | não iniciado | — |
| gameplay | não iniciado | — |
| 60/50 fps | não iniciado | — |
| áudio | não iniciado | — |
| memory bank atualizado | documentado | este arquivo, 2026-10-02 |

> Status válidos: `não iniciado`, `documentado`, `implementado`, `buildado`,
> `testado_em_emulador`, `validado_budget`. Toda linha diferente de
> "não iniciado" EXIGE prova citada (caminho de arquivo/captura), não prosa.

## Decisões registradas
- **Nome provisório: `Master of Fighters`** (slug/diretório: `master_of_fighters`) —
  decisão do dono, 2026-10-02.
- **Projeto apartado** (não é extensão de `luta_mugen`): consome o motor
  MUGEN→SMS de `SMS_projects/luta_mugen` + `tools/sms_wrapper/mugen2sms/`
  via tabelas compiladas; sem fork, sem compilar cross-workspace — mesma
  regra que valeu para o MD forge ser doador de técnica apenas.
- **Escalação registrada** (GDD §Escalação, 2026-10-02): hall = Guerreiro de
  Golden Axe (versão estilizada), Hayato (Kenseiden), Joe Musashi (Shinobi,
  traje clássico do 1º Shinobi como alterno desbloqueável), Dr. Ferdinand
  Social (Master of Darkness), karateca de Black Belt, bruxa de Psychic
  World, Alis Landale (Phantasy Star), Landau (Lord of the Sword). Chefes =
  Ninja Master (Shinobi), Count Dracula (MoD), Luter (PS1), Dark Force /
  Dark Falz (a confirmar: chefe final de **PS2**, não PS1).
- **Adição de J.J.** (decisão do dono, 2026-10-04): novo 9º herói jogável,
  referenciado especificamente ao sprite `J.J - Standing` em *Zillion II:
  The Tri Formation* para Master System para identidade, cores e mecânicas. A
  pedido posterior do dono, o anime *Akai Kōdan Zillion* foi consultado somente
  para o corte do uniforme e acessórios visíveis.
  Identidade, moveset conceitual e contrato visual estão em `doc/jj/` e
  `data/source_art/concept_art/jj_zillion_ii/`; a escala leve e os golpes
  especiais continuam em proposta. Concept art v4 aprovada pelo dono foi
  indexada na paleta `jj_zillion_ii`; `audit_validate_resources.py --kind
  sheet --character jj_zillion_ii` passou. A fronteira entre sprite SMS e
  referências de figurino do anime está declarada em contrato/lineage e passa
  `audit_reference_boundary.py`. A folha idle v5 de 12 quadros substitui a v4
  como `source_candidate` após a limpeza L104: gates de recursos,
  `audit_animation_semantics.py` e `audit_sprite_cutout.py` passaram, mas a
  folha aguarda aprovação visual própria, não está integrada em `res` nem
  validada em ROM/emulador. O contrato, lineage, prompts, notas, hashes e
  tentativas descartadas estão em `data/source_art/`. A linha de seleção do
  GDD declara 9 heróis + 4 chefes.
- Alex Kidd e Psycho Fox foram **sugeridos e não adotados** — fora do escopo
  até decisão nova.
- `specialization: fighting` declarado em `.mddev/project.json` (pendente de
  `audit_specialization.py` no primeiro ciclo de gates).

- **Direção de arte registrada (2026-10-02, decisão humana)**: traço anime
  90s estilo SFZ2 — referência medida: folha Ryu
  `/mnt/sdcard/SGDKForge/.../res/mugen/ryu/sheets/g0.png` (288×104, 15 cores
  úteis + fundo = 1 sub-paleta; contorno 1 px; 3 tons/material). Contratos no
  GDD §Direção de arte: ≤15 cores/sub-paleta, contorno 1 px, 3 tons por
  material, idle 72–88 px (refit dos ~104 px da referência, orientação histórica
  do scale_pilot; supersedida em 2026-10-09 pela faixa de corpo 66–72 px derivada
  de Fatal Fury Special Game Gear), biotipo por classe de peso. Referência é
  `inspiration_only` — risco de clone delimitado por política de prompt
  (descritores neutros, sem "in the style of") e proveniência de asset.
- **Blocker dominante atualizado**: direção de arte agora declarada → o
  blocker segue sendo o TDD (interface de tabelas do motor), que fecha o
  contrato de asset por personagem.

- **Paletas exatas registradas (2026-10-02)**: 12 personagens (8 hall + 4
  chefes) em `doc/palettes_manifest.json`, validadas por
  `doc/build_palettes_manifest.py` (importa `sms_palette.py`): códigos 6-bit,
  rampas ΔY≥17, ≤15 úteis. Primeira rodada do validator reprova 3 defeitos
  reais: rampas azuis de Hayato/Joe abaixo do piso (canal B tem luma 0.11 —
  azul "escuro vs médio" não separa) e slot duplicado em Black Belt;
  corrigidos. Alternos Joe-clássico e Dracula-vampiro = troca de roles no
  mesmo pool. Pendências de política: distribuição das 4 paletas CRAM em
  duelo (P1/P2/SP extras/HUD) e paleta de estágio — fechar no TDD.

- **Correção de paleta Golden Axe Warrior (2026-10-03)**: a entrada antiga
  `ga_warrior` não continha os azuis/cianos observados no sheet original do
  personagem. `doc/build_palettes_manifest.py` foi corrigido e regenerou o
  manifesto com 12 tons do sprite sheet SMS (azul/ciano, ouro, vermelho, pele,
  branco e contorno bordô), aproximados para RGB canal×85; preto é reservado ao
  índice transparente 0 e o fundo teal da referência foi excluído. Fonte usada somente para estudar cores/silhueta, sem pixels na
  arte. O GDD agora separa peso de jogo da morfologia: o guerreiro terá aspecto
  jovem e ágil, com elmo de chifres e capa. A arte v1 está em
  `data/source_art/concept_art/ga_warrior/`, como `source_candidate`; aguarda
  revisão visual e não foi integrada.

- **Concept art Golden Axe Warrior — v1 (2026-10-03)**: duas poses completas
  do mesmo jovem guerreiro, esguio e ágil, com elmo de chifres azul/dourado,
  armadura azul/ciano, capa vermelha, espada e escudo. PNG indexado 1536×1024,
  12 tons exatos do manifesto `ga_warrior`, índice 0 transparente, sem dithering;
  gate de recursos passou. A arte original de referência foi usada para mapear
  cores e silhueta, nenhum pixel foi copiado. Prompt, contrato, máscara, hashes
  e proveniência em `data/source_art/concept_art/ga_warrior/`. Estado
  `source_candidate`, ainda sem aprovação do dono, integração em `res` ou
  validação de ROM/emulador.

- **Concept art Golden Axe Warrior — variante v2 (2026-10-03)**: edição da folha
  v1 mantendo as duas composições, o traço, o elmo de chifres, espada e escudo;
  figurino alterado para torso descoberto, capa de pelo azul, calça e botas,
  conforme pedido do dono. PNG indexado 1536×1024, 11 cores úteis da paleta
  declarada para `ga_warrior`, índice 0 transparente e sem dithering; o gate
  `audit_validate_resources.py --kind sheet --character ga_warrior` passou.
  Artefatos, prompt, contrato e proveniência estão em
  `data/source_art/concept_art/ga_warrior/`. O dono aprovou v2 em 2026-10-03
  como referência visual para sprites. A variante não substitui a v1 e não está
  integrada em `res` nem validada em ROM/emulador.

- **Estudo de sprites Golden Axe Warrior — idle 12f (2026-10-03)**: folha
  candidata em `data/source_art/sprite_studies/ga_warrior/ga_warrior_idle_12f_sms_96px_v1.png`,
  384×288, grade 4×3 com células 96×96. Usa 11 cores úteis da paleta
  `ga_warrior`, índice 0 transparente, sem dithering e pivô `[48,95]` comum;
  altura visível medida em 87–88 px e largura em 77–88 px. Os 12 quadros têm
  pixels distintos após tradução. `audit_validate_resources.py` e
  `audit_animation_semantics.py` passaram. A primeira geração foi descartada
  por variação insuficiente após redução; a segunda usou chaves de pose mais
  explícitas. A escala próxima de 88 px é provisória e aguarda medição por
  `scale_pilot`. Estado `source_candidate`, aguardando revisão visual desta folha;
  a aprovação da concept art não aprova sprites, metasprite, orçamento de
  scanline, integração ou validação em ROM/emulador. Prompt, contrato, quadro
  semântico e hashes estão em `data/source_art/sprite_studies/ga_warrior/`.

- **Movesets: proposta temporária, NÃO aprovada (2026-10-02)**: rascunho em
  `doc/movesets_draft.json` (44 golpes, janelas startup/active/recovery em
  frames ancoradas no molde MSSF2T/hamoopig). Dono decidiu: cada moveset será
  discutido e fechado na construção do respectivo personagem. Não tratar o
  draft como contrato de FSM/asset.

- **Correção de lore (dono, 2026-10-03): Dr. Social não vira vampiro no
  jogo.** A transformação é premissa de *Vampire: Master of Darkness* (Game
  Gear, 1993), não do SMS *Master of Darkness* — verificado na Wikipedia: no
  SMS ele é psicólogo/vampiro-caçador humano com arsenal de bengala, rapier,
  faca, machado, pistola, bombas e boomerang. Docs corrigidos: GDD (roster,
  exemplo de specials, nota de alternos), `build_palettes_manifest.py` +
  `palettes_manifest.json` (roles `vamp_*` renomeados `accent_red`/
  `arcane_violet` = FX do arsenal; regenerado `[OK] 12 paletas validadas`),
  `movesets_draft.json` (kits vamp_regen etc. substituídos por cane_jab,
  rapier_thrust, occult_boomerang, duel_pistol com carimbo
  `correcao_2026-10-03`), e `successor_asset_directive_dr_social_concept.json`
  v2 (prompt corrigido: "remains fully human — no fangs, no wings, no
  transformation"; R3 reprova qualquer traço vampírico).

- **Concept art Dr. Social (2026-10-03)**: após duas tentativas nativas
  anteriores com 403/billing, o retry do prompt corrigido v2 gerou uma folha
  horizontal 1536×1024 pelo ImageGen nativo. Está em
  `data/source_art/concept_art/dr_social/review_drafts/concept_direction_explorations/dr_social_concept_sheet_v1.png`, com
  prompt e SHA em `dr_social_concept_prompt_v1.txt` e
  `asset_lineage_record.json`; estado `source_candidate`. Inspeção visual:
  duas poses de corpo inteiro, traços humanos, bengala/óculos/sobrecasaco/
  cravat visíveis, rapier e boomerang presentes, sem texto, marca-d'água ou
  pixel art. Revisão cega independente, medição formal de paleta/contorno e
  aprovação do dono continuam pendentes; não é sprite nem contrato visual.

- **Concept art Dr. Social — revisão 2 (2026-10-03)**: variante editada da
  folha anterior, com aparência um pouco mais jovem (~início dos 30) e
  expressão/postura voltadas a virtude, coragem e busca da justiça. Arquivo:
  `data/source_art/concept_art/dr_social/review_drafts/concept_direction_explorations/dr_social_concept_sheet_v2.png`;
  prompt e lineage v2 no mesmo diretório. Mantém duas poses completas, armas e
  identidade humana. Continua `source_candidate`; revisão cega, medição formal
  e aprovação do dono seguem pendentes.

- **Estudo de sprite idle Dr. Social (2026-10-03)**: gerada folha horizontal
  com quatro poses idle; anexo do dono usado só como inspiração de layout e
  cadência, sem copiar pixels. v1 e tentativa de limpeza de paleta v2 em
  `data/source_art/sprite_studies/dr_social/`, fora de `res`. O dono rejeitou
  v2 (2026-10-03): morfologia larga/forte demais e quadros repetindo a mesma
  pose. Estado: `rejected_by_owner`; correção pedida: perfil esguio e sequência
  de 12 etapas com delta visível, aplicando os princípios de animação. A folha
  v2 continua com 261 cores RGB opacas (limite 12) e não foi normalizada para
  ~80 px lógicos; nenhuma integração ou validação em emulador.

- **Estudo de animação Dr. Social — v3 (2026-10-03)**: nova folha 4×3 com 12
  poses de um ajuste de guarda com bengala, fora de `res`:
  `data/source_art/sprite_studies/dr_social/dr_social_idle_guard_12f_v3.png`.
  Reduz a largura do corpo e diferencia as poses por antecipação, transferência
  de peso, arco da bengala, guarda, seguimento do casaco/cravat e recuperação.
  Usa a referência anexada só para agrupamento visual. Dono aprovou v3 como
  direção visual/estudo de animação; status `owner_approved_visual_reference`.
 Escala lógica de 80 px, paleta exata e review independente ainda não
 validados. Lineage registra prompt, entradas e 12 key poses.

- **Aplicação L101 ao estudo Dr. Social (2026-10-03)**: variante em
  `data/source_art/sprite_studies/dr_social/dr_social_idle_guard_12f_sms_80px_v5_clean.png`,
  fora de `res`, com 4×3 células de 80×80, índice 0 transparente e 9 cores úteis
  da paleta `dr_ferdinand_social`. Contorno/sombra usa o azul-marinho declarado
  para manter pixels opacos no SMS; casaco charcoal usa `#555555`. Conversão
  sem dithering, máscara por célula e revisão sobre fundo não preto fecharam
  furos de transparência. No comparativo indexado sem limpeza havia 8
  componentes opacos menores que 12 px; o filtro por célula deixou 3 na etapa
  pré-contorno e a variante final ficou com 0. O gate de recursos
  passou. Fonte, prompts, parâmetros e SHA em
  `asset_lineage_record_sms_v5.json`. O dono aprovou provisoriamente a tradução
  v5 como referência visual e pediu revisitar o design no futuro. A aprovação
  não libera integração: altura visível exata, review independente, vínculo
  com ROM e validação em emulador seguem pendentes. A interação entre contorno
  preto e índice 0 transparente foi registrada como candidata a curadoria futura
  em `doc/curation/2026-10-03_l101_limpeza_granulacao_sprite.json`.

- **Concept art Hayato / Kenseiden (2026-10-03)**: folha v1 com duas poses
  completas, katana e magia de pergaminho em
  `data/source_art/concept_art/hayato/`. O GDD dá lastro para samurai, katana,
  pergaminhos e classe média (~80 px); traje específico e detalhes visuais da
  folha seguem provisórios até aprovação do dono. Referência de inventário de
  sprites consultada: SMS Power; nenhum pixel externo foi usado. Estado
  `source_candidate`, ainda não sprite nem validação de paleta/escala.

- **Concept art Alis Landale / Phantasy Star (2026-10-03)**: a folha v2 foi
  preservada historicamente, mas o dono gostou da composição e pediu correção
  das cores. A v4 em `data/source_art/concept_art/alis_landale/` usa cabelo
  castanho-dourado, roupa magenta/rosa e índigo, peças marfim/brancas e cinza,
  dourado, pele pêssego e lâminas azul/ciano conforme retrato original. A
  tradução indexada usa 13 cores úteis exatas do manifesto Alis, sem dithering,
  com índice 0 transparente e contorno opaco marrom profundo `#550000`. O corte
  alfa em 90% removeu halo; ruído granuloso foi limpo antes da conversão. O gate
  de recursos passou. A referência do retrato SMS Power foi usada apenas para
  mapear cores; nenhum pixel externo foi usado. Manual SMS Power consultado para
  espada curta e escudo leve. A classe leve (~72–76 px) segue proposta do GDD e
  ainda precisa confirmação/medição. O dono aprovou visualmente a v4 e a
  direção cromática; lineage registra hashes, prompts, referência e ferramentas.
  Essa aprovação é da concept art e não aprova a futura folha de sprite nem
  vínculo/validação em ROM.

- **Concept art Landau / Lord of the Sword (2026-10-03)**: folha v1 em
  `data/source_art/concept_art/lord_of_the_sword/`, com duas poses completas,
  jovem adulto sem bigode/barba, túnica verde, couro, calça azul, espada, arco
  e aljava. O dono corrigiu a primeira versão madura para um jovem e aprovou a
  versão rejuvenescida completa como referência visual para o estudo de sprites.
  A paleta antiga do manifesto (roxo/coroa) foi substituída por 15 papéis
  derivados dos tons do sprite SMS e degraus de cel shading; a folha usa 14
  cores úteis, índice 0 transparente, sem dithering. O corte alfa em 90% e a
  limpeza de componentes pequenos removeram halos e pontilhado; o gate de
  recursos passou. O manual US identifica o herói como Landau e descreve espada
  e arco; a página de sprites SMS Power mostra as poses laterais originais.
  Nenhum pixel externo foi usado. A classe pesada permanece proposta no GDD;
  escala/geometry de runtime, scanline, integração em ROM e validação no
  emulador não foram feitos. Prompt, proveniência, fontes e hashes estão em
  `data/source_art/concept_art/lord_of_the_sword/approved_records/asset_lineage_record_v1.json`.

- **Estudo de sprite Landau — idle (2026-10-03)**: folha aprovada visualmente
  pelo dono em 2026-10-03 como referência provisória; v3 em
  `data/source_art/sprite_studies/lord_of_the_sword/landau_idle_12f_sms_96px_v3.png`,
  384×288, 4×3 quadros de 96×96, leitura esquerda-direita/cima-baixo, pivô
  comum `[48,95]` e linha dos pés alinhada. Altura visível medida entre 83 e
  87 px; largura entre 63 e 70 px, com margem horizontal mínima de 6 px. Usa
  somente os 15 papéis permitidos da paleta Landau, índice 0 transparente,
  sem dithering. Corte alfa a 90%, limpeza por célula e escala nearest uniforme
  removeram halo/granulação sem distorcer a morfologia. Os 12 quadros têm hashes
  distintos; `audit_validate_resources.py` e `audit_animation_semantics.py`
  passaram, incluindo a medição de largura, altura e baseline por quadro. Não está
  em `res/`; geometria de runtime, orçamento de scanline e ROM/emulador ainda
  não foram validados. Prompt, contrato, manifest semântico e hashes estão em
  `data/source_art/sprite_studies/lord_of_the_sword/asset_lineage_record_v1.json`.

- **Estudo de sprite Alis — guard motion (2026-10-03)**: folha indexada v1 em
  `data/source_art/sprite_studies/alis/alis_guard_motion_12f_sms_80px_v1.png`,
  320×240, 4×3 quadros de 80×80, 12 hashes de quadro únicos e pivô comum
  `[40,79]`. Usa as 13 cores úteis exatas do manifesto Alis, índice 0
  transparente, sem dithering e com limpeza por célula. O alinhamento das
  linhas corrigiu uma deriva vertical do gerador. `audit_validate_resources.py`
  e `audit_animation_semantics.py` passaram. A geração produziu poses de
  transição de guarda, não foi promovida como idle final; altura de caixa visível
  observada varia de 64 a 73 px. Estado `source_candidate`, fora de `res`, sem
  revisão independente, contrato de metasprite, vínculo com ROM ou validação em
  emulador. Prompt, fonte, hashes e decisões estão em
  `data/source_art/sprite_studies/alis/asset_lineage_record.json`.

- **Estudo de sprite idle Hayato (2026-10-03)**: folha gerada com 12 poses
  corpo inteiro em grade 4×3, guardas laterais voltadas à esquerda, katana
  embainhada e pequenos ajustes de peso, mão e tecido. PNG e prompt em
  `data/source_art/sprite_studies/hayato/`, fora de `res`; usa a concept art
  Hayato v1 como referência visual a pedido do dono. Estado
  `source_candidate`: escala lógica de 80 px, paleta exata, revisão independente
  da animação e vínculo com ROM não validados. Não promover para runtime ainda.

- **Revisão de cores do idle Hayato (2026-10-03)**: o dono forneceu captura de
  Kenseiden SMS e corrigiu o figurino para quimono claro com hakama vermelho-
  alaranjado. A fonte v2 de alta resolução em
  `data/source_art/sprite_studies/hayato/` permanece truecolor (130.557 RGBs
  opacos distintos e 256 valores alfa); ela é referência de produção, não arte
  nativa do hardware. A paleta do personagem no manifesto foi alinhada às 15
  cores da versão indexada aprovada.

- **Tradução SMS do idle Hayato (2026-10-03)**: derivada de v2 pela ferramenta
  `prepare_sms_pixel_art.py`, folha indexada 320×240 em
  `data/source_art/sprite_studies/hayato/hayato_idle_12f_sms_80px_v1.png`, com
  grade 4×3 de células 80×80, índice 0 transparente e 15 cores úteis da grade
  6-bit SMS, exatamente iguais à paleta Hayato em `doc/palettes_manifest.json`.
  `build_palettes_manifest.py` foi alinhado e validou as 12 paletas; as rampas
  Hayato passaram no piso ΔY≥17. O gate de recursos aprovou o PNG contra a
  paleta declarada.
  O dono aprovou a folha como referência de paleta (L100), depois apontou a
  granulação ao redor das silhuetas. A v1 fica preservada como registro do
  defeito e não deve ser promovida para integração.

- **Limpeza da folha idle Hayato (2026-10-03, L101)**: edição visual seguida de
  quantização sem dithering e remoção de componentes pequenos por célula.
  `hayato_idle_12f_sms_80px_v2_cleanup.png` é 320×240, 4×3 células de 80×80,
  índice 0 transparente e 15 cores da paleta declarada. Componentes conectados
  opacos menores que 12 px caíram de 201 para 0; o gate de recursos passou.
  Fonte, prompt, SHA e parâmetros em `data/source_art/sprite_studies/hayato/`
  e `asset_lineage_record_sms_v2.json`. O dono aprovou a variante limpa como
  referência visual de paleta/limpeza (2026-10-03); altura visível exata,
  revisão independente da animação, integração/vínculo com ROM e validação em
  emulador seguem pendentes.

- **Conceito Joe/Takashi — Shadow Dancer SMS (2026-10-03)**: o dono aprovou a
  imagem anexada de duas vistas com os acentos amarelos. O original aprovado
  está preservado em RGBA; o derivado técnico da paleta SMS usa 7 cores úteis,
  índice 0 transparente e passou `audit_validate_resources.py`. O arquivo de
  paleta é uma derivação do rascunho relacionado v1, não foi aprovado
  separadamente. A alternativa v2 com amarelo reduzido foi supersedida pela
  escolha do dono. Registro e hashes em
  `data/source_art/sprite_studies/joe_musashi_shadow_dancer_sms/asset_lineage_record_concept_v1.json`.

- **Idle Joe/Takashi — Shadow Dancer SMS (2026-10-04)**: folha candidata
  `joe_musashi_idle_12f_sms_80px_v2.png`, 320×240, grade 4×3 de quadros 80×80,
  paleta individual de 7 cores e índice 0 transparente. A primeira geração foi
  rejeitada internamente porque muitas poses pareciam a mesma após a redução;
  v2 passou os gates de recursos e semântica: 12 hashes distintos, pivô e
  baseline comuns y=79 e geometria por quadro dentro do contrato. O dono ainda
  precisa revisar visualmente esta animação. Não está em `res/`, não tem vínculo
  com ROM e não foi vista no emulador. Prévia, métricas e lineage em
  `data/source_art/sprite_studies/joe_musashi_shadow_dancer_sms/asset_lineage_record_idle_v2.json`.

- **J.J. — Zillion II: The Tri Formation (2026-10-04)**: referência de roupa e
  cores baseada no sprite `J.J - Standing` do próprio jogo SMS Power; sem
  material do anime e sem copiar pixels. A paleta candidata foi adicionada ao
  gerador e manifesto: 13 cores SMS úteis, índice 0 transparente, classe leve
  proposta. Concept art de duas poses, contrato, lineage e fontes estão em
  `data/source_art/concept_art/jj_zillion_ii/`; aguardam revisão visual do
  dono. O moveset conceitual em `doc/jj/` não fecha frame data. Nada em `res/`,
  sem vínculo com ROM e sem validação em emulador.

- **Revisão visual preliminar de harmonia do elenco (2026-10-04)**: as pranchas
  originais estão em `data/source_art/roster_harmony_review/`.
  `harmony_sprites_frame00_7char_v1.png` é comparação de origem, não sprite
  oficial nem aprovação de folha: seleciona um quadro por sheet e preserva
  pixels/paletas, mas mistura estados de revisão e precede os alvos agora
  registrados em `doc/roster_harmony_contract_v1.json`. A medição L105 mostra
  falha de tamanho no Guerreiro de Golden Axe e Landau, largura visual estreita
  no Dr. Social e necessidade de revisão morfológica em Alis e J.J. O dono
  confirmou a harmonia das concepts e definiu Hayato como referência de
  acabamento; sprites continuam exigindo correção/revisão própria. Nada foi
  movido para `res/` ou vinculado a ROM. A prancha
  `data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_candidate_v1.png`
  mostra cinco propostas frame 00 ao lado das referências Hayato/Joe; todas as
  relações dimensionais declaradas passam, mas o dono rejeitou a estética. Joe é
  referência de morfologia esguia, porém seu recorte apresenta halo/sujeira e
  precisa de revisão. Os demais candidatos leem atarracados/chibi, com membros
  largos e proporções de cabeça/rosto menos humanas. Os valores da paleta estão
  em direção correta, mas alguns agrupamentos de cor poluem a imagem e o
  acabamento caiu frente às concepts iniciais. A escala não está aprovada como
  atalho para anatomia. Novo parecer é obrigatório nos eixos anotados no perfil
  de harmonia; board rejeitado continua em source_art, sem promoção para `res/`.
  A nova proposta de direção morfológica está em
  `data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v1_finish.png`;
  ela aproxima os biotipos de proporções humanas e usa Hayato/Joe por papéis
  separados. É estudo para avaliação, não passa como sprite: a paleta ainda não
  foi validada contra o manifesto. A tentativa de recorte transparente gerou
  franja cromática e foi arquivada como exemplo reprovado.

- **Concepts harmonizadas Hayato e Dr. Social (2026-10-04)**: o dono confirmou
  que o conjunto conceitual está harmonizado. Hayato v2 usa kimono branco, faixa
  vermelha e hakama laranja/vermelha; Dr. Social v3 usa casaco azul/ciano,
  sombras teal, cabelo grisalho, camisa branca, cravat burgundy e efeito violeta
  somente no boomerang. As folhas SMS mantêm autoridade de identidade/paleta;
  Alis v4 + Guerreiro de Golden Axe v2 servem apenas como acabamento. Lineage
  e prompts registram hashes. A aprovação conceitual define referência visual,
  não aprova sprite, animação, integração ou ROM.

## Blocker dominante atual
Interface de consumo do motor: definir COMO este projeto recebe as tabelas
compiladas do pipeline mugen2sms (esquema de tabelas, pools VRAM/RAM,
banking) — sem isso o TDD (doc/15-tdd.md) não pode ser escrito e nenhum
personagem tem contrato de asset. Atacar cedo, igual à decisão de projeto
que originou luta_mugen.

## Lições abertas

- L105, promovida a regra canônica em 2026-10-04: revisar concepts e sprites do
  roster em pranchas separadas, preservar quadros-fonte, medir escalas/relações
  por personagem e exigir inspeção humana de anatomia/estilo em conjunto. O audit
  agora mede relações `width_near`; largura de bbox inclui cabelo/equipamentos e
  é só ocupação visual, não biotipo. JSON
  `doc/curation/2026-10-04_l105_harmonia_escala_roster.json`, regra SMS_GLOBAL
  §90, ferramenta `audit_roster_harmony.py`; a ficha de alvos do projeto está em
  `doc/roster_harmony_contract_v1.json`; comparação de candidatos em
  `doc/roster_harmony_candidate_review_v1.json`. Hayato/Kenseiden ancora
  acabamento; Joe ancora apenas biotipo e massa dos membros. A ferramenta não
  julga pixels de anatomia, recorte ou paleta, mas agora distingue revisão visual
  pendente de reprovação humana registrada. O relatório v1 segue histórico; a
  avaliação atual está em `data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_candidate_frame00_audit_v2.json`,
  status `owner_visual_revision_required`, e o board em
  `data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_review_v2.png`.
  Não é aprovação de folha.
- Candidato para curadoria futura: quando preto é índice transparente 0, usar
  para o contorno opaco um tom profundo não preto declarado na paleta e revisar
  a silhueta sobre fundo não preto. Registro/evidência em
  `doc/curation/2026-10-03_l101_limpeza_granulacao_sprite.json`; ainda sem nova
  seção numerada ou ferramenta própria.
- Candidato para curadoria futura (L100): a conformidade com a paleta SMS e o
  manifesto do projeto não garante fidelidade às cores canônicas do personagem.
  Conferir os papéis cromáticos com referência original autorizada antes de
  aceitar/fechar a paleta individual. Evidência: Alis v2 passou no contrato da
  paleta anterior, mas o dono apontou as cores como incorretas; a v4 mapeia o
  retrato original e passa no contrato regenerado. Registro em
  `doc/curation/2026-10-03_l100_paleta_sms_no_conceito.json`; sem nova regra ou
  ferramenta até avaliação de curadoria.

## Handoff
1. Dono revisa/aprova o GDD rascunhado (autoridade #2 exige aprovação humana).
2. Escrever `doc/15-tdd.md`: layout de pools, esquema de tabelas herdado do
   mugen2sms, banking — resolver o blocker dominante.
3. Decidir pipeline de origem de arte (fan game: redesenho autoral;
   `audit_provenance.py` exige proveniência declarada por símbolo).
4. Primeiro ciclo honesto de `./build.sh` e registro do status real dos 7
   eixos (provavelmente falho se a toolchain não estiver no PATH).


## Fluxo oficial de arte autoral

Desde 2026-10-08, pedidos de arte autoral seguem o workflow compartilhado
`tools/sms_wrapper/.agent/workflows/original-artwork.md`: consultar o catálogo
central `doc/curation/2026-10-07_catalogo_inicial_estilos_visuais.json`, trabalhar
por ciclos incrementais e usar o concept/model sheet aprovado com cinco vistas,
régua relativa, fundo neutro e fichas de estilo. Guardar prompt, fonte gerada,
composição, metadados, lineage e validação sob `data/source_art/`; não tratar
concept como arte integrada em `res/`. O catálogo contém 49 referências, mas
seus estilos são individualmente não validados até revisão própria. Evitar
geração simultânea dos 48 candidatos por custo e baixa viabilidade de revisão.

### Prancha conceitual consolidada do elenco — avaliação pendente (2026-10-08)

Foram compostas duas pranchas comparativas a partir das sete referências
confirmadas no contrato atual, distribuídas em grupos de quatro e três. Os
personagens aparecem lado a lado, com fundo neutro, baseline compartilhada e
régua relativa; as imagens de origem foram preservadas sem redesenho, alteração
de cor ou deformação não uniforme. Arquivos e hashes das fontes/saídas estão em
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_concept_lineup_v2_manifest.json`;
as imagens são `harmony_concept_lineup_v2_part_01.png` e
`harmony_concept_lineup_v2_part_02.png` no mesmo diretório. Estado:
`candidate_pending_owner_visual_review`; a composição foi inspecionada, mas não
há aprovação humana inferida.

A régua usa U derivados dos alvos de altura de trabalho do contrato, em escala
de apresentação 8 px/U, e dimensiona a caixa visível inteira da pose escolhida.
Ela inclui cabelo/capacete e equipamento que se estende além do corpo; portanto,
é uma comparação de ocupação visual da referência, não uma medida anatômica
ortográfica ou altura canônica. Joe Musashi usa a referência aprovada em pixel
art do Master System, de meio visual diferente dos conceitos ilustrados. Black
Belt e a Bruxa de Psychic World não foram incluídos porque ainda não há conceito
aprovado registrado para eles. Os eixos de coesão artística, morfologia, escala
e legibilidade de identidade permanecem para avaliação do dono.

### Harmonização Waku Waku 7 — revisão de escala e pistola Zillion (2026-10-08)

Foi criada uma nova candidata do elenco com acabamento unificado inspirado em
Waku Waku 7. As duas folhas e a procedência estão em
`data/source_art/roster_harmony_review/waku_waku_7/`: `harmony_waku_waku_7_lineup_v1_part_01.png`,
`harmony_waku_waku_7_lineup_v1_part_02.png`, manifesto JSON, prompts, fontes
geradas e referência da pistola anexada pelo dono. A composição usa grupos de
quatro e três personagens, baseline e régua comuns.

Alvos de altura da cabeça à sola, com 1 U = 8 px na prancha: Guerreiro de Golden
Axe 74 U; Hayato e J.J. 75 U; Alis 75 U; Joe Musashi, Dr. Social e Landau 80 U.
Assim, Landau iguala Dr. Social/Joe Musashi e J.J. iguala Hayato. A escala é
uniforme por personagem, sem deformação não uniforme. A arma de J.J. segue a
referência fornecida: perfil horizontal alongado, azul-marinho com inserções
ciano. A segmentação final separa as silhuetas conectadas para evitar que
equipamento/contorno de Dr. Social invada a coluna de Joe.

Estado: `candidate_pending_owner_visual_review`. A composição e hashes foram
conferidos; continuam pendentes a avaliação humana de coesão estilística,
fidelidade dos detalhes, anatomia e encaixe das mãos/equipamentos. Isto não
aprova sprite, animação, paleta SMS ou ROM.

### Prova técnica de conversão de asset SMS — piloto v1 (2026-10-09)

Foi criado um padrão de contrato visual/inventário de tiles em
doc/asset_conversion_proof_standard_v1.md, com modelo copiável em
doc/asset_conversion_contract_template_v1.json e compositor determinístico em
tools/compose_sms_asset_conversion_proof.py. O fluxo do projeto também aponta
para esse padrão em doc/00-diretrizes-agente.md. Este contrato cobre proveniência,
resolução, escala de trabalho, paleta indexada, recorte e contagem exata de
padrões 8×8; não substitui o contrato de runtime, VRAM/RAM, metasprite,
banking, ROM binding ou validação no emulador.

O piloto usa a folha Dr. Social
data/source_art/sprite_studies/dr_social/dr_social_idle_guard_12f_sms_96px_v9_clean.png
e a referência de escala/identidade CPS2-Alpha-Cel #01. A prancha e seu relatório
estão em
data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_conversion_proof_v1.png
e .json. SHA-256 da prancha:
011e9b49e34befcd37d8d3323845916667773e9e4fef1f25dc3673cff7e08671.

Medições: 12 quadros de 96×96 px; cada quadro tem 144 posições 8×8. O quadro
09/12 tem bbox opaca 65×82 px (inclui equipamento), 62 células ocupadas, 62
padrões únicos e 1.984 bytes brutos de padrões 4bpp. A folha soma 706 colocações
ocupadas, 690 padrões únicos exatos e 22.080 bytes brutos se todos forem
representados em 4bpp. O PNG indexado usa 12 cores úteis, índice 0 transparente
e RGB na grade de 6 bits. O fundo de inspeção é verde puro #00FF00, ausente da
paleta do asset. audit_validate_resources.py passou para a folha-fonte.

O board v1 foi **rejeitado** pelo dono em 2026-10-09: a grade 8×8 foi
composicionada sobre o sprite ampliado e alterou a imagem que deveria provar.
A fonte permaneceu intacta; a prancha não é válida para julgar pixels. Artefato
e relatório foram preservados com status `rejected_invalid_proof_overlay`.

### Prova técnica de asset SMS — duas poses v2 (2026-10-09)

O padrão atual está em `doc/asset_conversion_proof_standard_v2.md`, com template
`doc/asset_conversion_contract_template_v2.json`. A prancha v2 contém somente
dois estudos separados: idle (frame-fonte 01) e ação (frame-fonte 07). A grade
8×8 foi movida para mapas independentes. `audit_asset_proof_sheet.py` compara os
recortes ampliado e 1× pixel a pixel com PNGs indexados; `--self-check` aprovou
uma fixture limpa e reprovou uma linha de overlay injetada.

Prancha e relatório:
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v2.png`
e `.json`. Fonte pai SHA-256:
`3ca568e5a51cff4cd37a4d618274a902422e3ecc5f740a09d1b614f5eb3f303b`.
Inventário: idle 54 padrões únicos; ação 57; união do par 111 padrões/3.552 B
brutos 4bpp. São números da arte, não alocação residente. Paleta tem 12 cores
úteis, índice 0 transparente, canais RGB 6-bit e fundo verde puro fora do
asset. A auditoria mecânica de preview/paleta/tiles passou. O scan de
componentes do `audit_sprite_cutout.py` encontrou zero ilhas abaixo de 2 px nas
duas poses; o perfil está em `components_only`, então o comando retorna pending
até que regiões de cor por material sejam declaradas e revisadas.

Status continua candidato: revisão de anatomia, clusters, face, recorte e
fidelidade pendente de revisor independente e dono. A pose de ação usa bengala
do estudo de jogo e precisa ser reconciliada com rapier/boomerang do concept.
O TDD ainda não fecha pools, residência, metasprite, SAT/scanline, banking,
VBlank ou máximo de quadros por folha; hardware não define um máximo universal.
Nada entrou em `res/`, tem vínculo ROM ou foi validado em emulador. L109 registra
a regra canônica em `doc/curation/2026-10-09_l109_prova_pose_pixels_hardware_animacao.json`.

### Prova de asset v3 e escala GG→SMS (2026-10-09)

O dono rejeitou como amostra a v2: a arma tocava a borda do frame e 96×96
estava grande para a direção de luta pretendida. A referência adotada é Fatal
Fury Special no Game Gear, tela 160×144; a captura consultada mostra cerca de
53 px para um lutador em pé. Projetando proporção para SMS 256×192 resulta em
aprox. 71 px; GDD/TDD agora usam faixa visual 66–72, centro 70. Não é lei de
hardware. Mantêm-se o vínculo Landau≈Dr. Social≈Shinobi e JJ≈Hayato.

A proposta v3 está em
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v3.png`
e JSON homônimo. Duas poses 80×80 (10×10 tiles), nearest-neighbor uniforme
5/6; fonte frame 01 idle e frame 08 ação. Bbox opaca: 37×67 e 68×70; células
ocupadas 43/52, padrões únicos 42/52, união 94/3.008 B brutos 4bpp. A arma da
ação permanece dentro do canvas; margens vazias L/T/R/B: 20/7/23/6 e 7/4/5/6.
O auditor agora reconstitui a escala declarada e reprova pixels encostados na
borda, preview divergente ou canvas que não seja múltiplo de 8. Self-check e
auditoria mecânica passaram. Componentes por material, anatomia/concept,
review independente, decisão do dono, metasprite/SAT/scanline e budget de
runtime seguem pendentes; não houve promoção para `res/` ou ROM.

### Prova estática de conversão em ROM diagnóstica (2026-10-10)

O usuário pediu avanço no fluxo técnico de conversão ao Master System. A lição
L121 foi registrada em `doc/curation/2026-10-10_l121_sms_asset_to_rom_conversion.json`,
no ledger e em SMS_GLOBAL §111; a skill executável é
`tools/sms_wrapper/.agent/skills/sms-asset-to-rom.md`. A rota normaliza PNG
indexado sem alterar pixels, valida contrato/proveniência/geometria, empacota
poses como tiles 4bpp compartilhados, simula SAT/scanline, inicializa o mapa BG,
constrói ROM diagnóstica, vincula asset→ROM por SHA e compara cada captura de
framebuffer com a fonte indexada.

Dr. Social v4: idle e ação, 80×80; 89 padrões 8×8 únicos + 1 padrão vazio = 90
carregados/2.880 B brutos. Simulação: 43/49 objetos, pico 6/7 por scanline.
ROM diagnóstica: 16.384 B, SHA-256
`6ec05a9b4caae97b36833eddcffb5536d4e63b4a64f75cff681fd998720fcc14`. Duas
sessões Emulicious privadas e isoladas mostraram, respectivamente, 1.483 e
1.556 pixels opacos exatos e zero discrepâncias nos 4.917 e 4.844 pixels
transparentes inspecionados. O binding SHA também passou. Relatório:
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_conversion_verification_v3.json`;
capturas e relatórios individuais ficam em
`out/diagnostics/dr_social_asset_probe_v3/project/out/evidence/`.

As tentativas anteriores foram mantidas para auditoria: v1 deixou o tilemap de
fundo sem inicialização completa; v2 não capturou a mudança para ação no limite
da sessão. A v3 corrigiu a tabela de nomes, reservou o padrão vazio e usou
entrada aplicada por quadros VDP. O valor nominal de clock informado pelo
emulador não é medição de FPS da ROM. Estas são duas poses estáticas; a prova
não fecha paleta P1 do elenco, budgets de cena/RAM/VBlank/banking, animação,
gameplay, áudio ou aprovação visual. O material continua em
`out/diagnostics/`, fora de `res/`, e não é entrega de produção.

### Fonte de animação aprovada e viewer ROM de 61 poses (2026-10-10)

O dono corrigiu a seleção da fonte: a folha de prova técnica de duas poses é
somente referência de conversão; a folha aprovada de 61 poses é a origem para
as nove sequências básicas. Fonte e papel estão presos por SHA em
`data/source_art/sprite_studies/dr_social/
dr_social_basic_sequences_61f_owner_source_v1.json`; SHA-256 da PNG:
`a95fc144f6d2574a9dfb43028b7b1d1fc91108b442f03fcfebac2df3f6d56057`.
`prepare_dr_social_61_pose_probe.py --self-check` confirma o caminho e SHA
aprovados e rejeita a prova técnica de duas poses como fonte de animação.

A revisão v5 converteu e incluiu idle (4), avanço (8), recuo (8), pulo (8),
abaixar (5), dash (8), queda (8), rolagem/levantada (8) e defesa (4): 61/61.
Os 61 PNGs passam gates de recurso, proveniência, geometria, SAT/scanline; o
empacotador limitou padrões residentes a 191 antes da name table. O primeiro
candidato com pool de 200/246 patterns atravessava esse limite e corrompia a
name table. Na v5, idle (169) e defesa (182) compartilham pool; as outras sete
sequências carregam uma pose por vez. Esse modo é para inspeção manual, não
mede reprodução contínua nem upload dentro do VBlank de uma cena de jogo.

ROM diagnóstica: `out/diagnostics/dr_social_61_pose_review_v5/project/out/rom/
dr_social_61_pose_review_v5.sms`, 114.688 bytes, SHA-256
`501161271e6cc51a7666520128375af04f6b8dde04cfa96071a410f09a78e6db`. O mapa
asset→ROM lista os 61 PNGs e passou no auditor com `--require`. A sessão
Emulicious privada `c9709fd01c0742eb8c0eaebaa01f79d6` percorreu cada ID e
comparou exatamente o framebuffer com o PNG indexado: 61/61, zero divergências
em 100.333 pixels opacos e 290.067 transparentes. Evidência completa e resumo:
`out/diagnostics/dr_social_61_pose_review_v5/project/out/evidence/`; amostra
visual de uma pose por sequência:
`out/diagnostics/dr_social_61_pose_review_v5/
dr_social_61_pose_emulicious_9_sequence_review_v5.png`.

O resultado fecha conversão e exibição pixel a pixel nesta ROM de revisão. Não
é gameplay nem promoção para `res/`: revisão artística humana, timing real das
sete sequências em passo manual, FPS, áudio, paleta P1 compartilhada, VBlank,
residência com cenário/HUD, banking de produção e ROM final continuam pendentes.
O lineage técnico completo da fonte histórica está em
`data/source_art/sprite_studies/dr_social/historical_approved/basic_sequences_61f_owner_source_v1/dr_social_61_pose_source_lineage_v1.json`.

### Revisão de continuidade da sombra azul — candidato v7 (2026-10-10)

O dono observou que azul e ciano estavam dispersos pelo tecido e não formavam
uma progressão de sombra coerente. A conversão v5 obedecia à paleta, mas a
correspondência RGB por pixel não preservava os planos de luz depois da redução.
O conversor v7 aplica amostragem média dentro do footprint do material azul já
classificado e remapeia pela luminância para a rampa existente:
`#005555` sombra → `#00AAAA` base → `#55AAFF` luz. A silhueta nearest-neighbor,
alpha e cores fora dessa rampa ficaram intactos. A comparação v5→v7 mediu
15.690 remapeamentos em 61/61 quadros, zero mudanças de alpha e zero mudanças
fora dos três tons da roupa.

ROM diagnóstica candidata: `out/diagnostics/dr_social_61_pose_review_v7/project/out/rom/dr_social_61_pose_review_v7.sms`,
SHA-256 `b27c328d11c58ba96474b83368d8a0afcda79600b388d21cb510b812632f53c`.
Build passou; ID01, ID02 e ID03 passaram comparação exata do framebuffer em
Emulicious privado. Isso confirma render da ROM, não aprovação da arte. A folha
4× e comparação estão em `out/diagnostics/dr_social_61_pose_review_v7/`; o
checklist vinculado ao hash segue pendente de revisão artística independente
e aprovação do dono. Os outros 58 quadros não foram conferidos individualmente
no framebuffer nesta versão. P1 do elenco, timing contínuo, VBlank, produção e
entrega continuam pendentes.

### Rejeição da v7 e refinamento de cel shading — candidata v8 (2026-10-10)

O dono rejeitou v7 porque ainda viu pixels azuis dispersos, sombras sem planos
contíguos e acentos brancos/amarelos com risco de vazamento. A v7 permanece
histórica e não aprovada. A v8 usa a linha inferior/v7 como base cromática,
preserva os 61 IDs, a geometria, a alpha e a paleta, e reorganiza 927 pixels:
438 pequenas ilhas dos três tons de tecido e 489 marcas navy interiores,
substituídas pelo teal de sombra existente. Nenhum branco/amarelo foi alterado
porque o detector conservador não encontrou singleton desses tons totalmente
cercado por tecido; o eixo semântico continua pendente para revisão visual.

ROM de revisão v8, SHA-256
`e641d2a44a1da2ef4c8aa1b2d768bf54822df27f7e023036cf81d3f1dfc0e50d`, passou
render exato nos 61 quadros em Emulicious privado (zero divergências), sessão
`ff0b89a1501b4237aa738f299ad3ee70`. Checklist v8 tem 10 eixos pending, revisão
independente ainda sem atribuição e aprovação do dono `false`. O novo eixo
obrigatório `semantic_palette_role_confinement` pede que acentos permaneçam nas
regiões do concept; o checklist mede cobertura, não estética. V8 segue
candidata de diagnóstico em `out/diagnostics`, não entrou em `res/` nem prova
gameplay, FPS, áudio, VBlank ou orçamento de produção.


### Refinamento semântico de acentos — candidata v9 (2026-10-10)

A revisão v8 revelou um furo: procurar somente pixels de acento totalmente
cercados pelo tecido não detecta vazamentos na borda. A candidata v9 usa o
cluster de cabelo para localizar rosto/óculos e a junção entre luva e haste
para localizar o pomo da bengala; 249 pixels amarelos fora dessas regiões foram
reclassificados usando cores vizinhas já existentes. Nenhum pixel branco, alpha
ou cor nova foi alterado. V9 permanece preservada como histórico e foi supersedida pela v10 após a
revisão encontrar brancos isolados. A aprovação artística continua pendente.

Preview: `out/diagnostics/dr_social_61_pose_review_v9/
dr_social_61_pose_converted_preview_4x.png`, SHA-256
`99dd4a592ad223840a3d2b4cd64788239ccf0a48da6f7619c89b9537ddaf2f40`. ROM
diagnóstica: 114.688 bytes, SHA-256
`81c2e47f684b307de6d2bfa803dc7e56a6b22402f06d7ecc8d8250f2b059bfd2`. A sessão
Emulicious `bfb478dfae0044d4a679db5df6bce018` comparou 61/61 framebuffers com
zero divergências; índice
`out/diagnostics/dr_social_61_pose_review_v9/project/out/evidence/
dr_social_61_framebuffer_v9/framebuffer_capture_index_v9.json`. Isso confirma
render exato nesta ROM de diagnóstico, não qualidade artística ou promoção.



### Dupla checagem de branco — candidata v10 (2026-10-10)

A inspeção ampliada da v9 encontrou 70 pixels brancos isolados/em pares em
regiões fora de luvas e bengala. A v10 usa máscaras geométricas para segmentos lineares candidatos à haste,
mantém clusters brancos maiores para review humano e reclassifica singles/pares
fora da haste com o material local. O scan não encontrou singles/pares sem
âncora; clusters maiores continuam sujeitos a review. Nenhuma cor nova, alpha
ou geometria foi alterada.

Preview v10: `out/diagnostics/dr_social_61_pose_review_v10/
dr_social_61_pose_converted_preview_4x.png`. ROM diagnóstica: 114.688 bytes,
SHA-256 `41879e38c8a83caec07bd97e9208ca08f00fe35ec1e927ff31feab4eb7a3c8cc`.
Emulicious `5e5ba2973da44f6293ef27b79429b050` conferiu 61/61 poses sem
divergências. Checklist v10 ainda tem dez eixos artísticos pendentes, revisão
independente sem atribuição e aprovação do dono `false`.

### Identidade de luta do Dr. Social — proposta v1 (2026-10-10)

Foi criada `doc/dr_social_combat_design_proposal_v1.md`, ainda
`proposal_pending_owner`. O perfil recomendado é duelista investigativo de
médio alcance: normais leves de luva/bota, bengala como assinatura, rapieira
linear e bumerangue em arco. A proposta limita a dois especiais conforme o
GDD, incorpora o contragolpe de bengala no Super candidato “Laudo Final”, e
descreve-o como contra-leitura. O GDD/TDD ainda não define
medidor compartilhado de Super; a folha conceitual #14 também segue candidata.
Não foram produzidas folhas de golpes nesta etapa; é necessária decisão do
dono e atualização do contrato antes do primeiro sprite. Pesquisa confirmou
que o jogo original é plataforma/ação e não fornece frame data de luta; a
estrutura M.U.G.E.N foi usada apenas como organização de comandos, estados e
animações. Foram consultados
`SMS_projects/luta_mugen/rascunho/character/ryu.zip` e
`SMS_projects/luta_mugen/rascunho/character/Ken_Majik_.zip`: os exemplos separam sequência de entrada,
transição de estado, hit definition e quadros/caixas de colisão; Ken também
mostra cancelamento explícito após `MoveContact` e exigência de `Power` para
Super. Esses arquivos de terceiros são referência estrutural, não fonte de
movimentos a copiar nem autoridade para controles do SMS.

### Revisão da matriz CPS2 do Dr. Social — v3 supersedida (2026-10-11)

A candidata v3 foi preservada em
`data/source_art/concept_art/dr_social/review_drafts/model_sheet_cps2_alpha_cel_v3_candidate/`.
SHA-256 real da imagem:
`7861f4ca4ad308856cc51a2f8c098e497b0ec3b93eb41498b377871016b07f6e`.
A revisão independente marcou `revise_before_growth`: o braço da bengala ainda
podia parecer sair de trás do casaco; os efeitos violetas competiam com a
silhueta do bumerangue; e a lista de arsenal de referência exigia uma fronteira
mais explícita diante da divergência entre GDD e proposta de combate. A v3 foi
supersedida pela v4 e não substitui a matriz aprovada v2.

Durante a checagem da v4 foi detectado um hash antigo incorreto da imagem v3 no
pedido de revisão. O valor real foi conferido diretamente no arquivo, corrigido
nos pedidos e referências de linhagem, e os artefatos hash-bound foram
revalidados. Essa falha reforça uma prática obrigatória: confirmar o digest dos
arquivos reais, incluindo referências herdadas, antes de selar qualquer parecer.

### Revisão da matriz CPS2 do Dr. Social — candidata v4 (2026-10-11)

Atualização posterior no mesmo dia: este registro descreve o estado anterior à
decisão do proprietário. A v4 foi aprovada e é agora a matriz ativa em
`data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`;
a v2 está `superseded` e foi movida para `historical_approved/`. O parágrafo
abaixo permanece como histórico da revisão pré-aprovação, não como estado atual.

A candidata v4 está registrada em
`data/source_art/concept_art/dr_social/review_drafts/model_sheet_cps2_alpha_cel_v4_candidate/`.
SHA-256 da imagem:
`ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644`.
Ela mantém rosto, cabelo, óculos, biotipo esguio, paleta, escala 7.5H e pose de
perfil da v2; torna o vestuário legível como Londres no fim do século XIX; e
separa a bengala romba da rapieira. Na pose de ação, a bengala fica à frente do
torso com o braço ligado de ombro a mão; o braço lançador é independente, e o
bumerangue aparece separado dos efeitos violetas. A folha mostra bengala,
rapieira e bumerangue como equipamento do conceito; faca, martelo, machado,
pistola, bomba e estaca aparecem como referências do jogo-fonte com termos em
aberto, sem aprovação de moveset.

A revisão independente concluiu `ready_for_owner_review`. O checklist v4 tem
17 eixos aprovados, nenhum eixo reprovado e apenas a aprovação do dono pendente.
A v2 segue como matriz aprovada ativa até decisão explícita do usuário. A
checagem de registro dos artefatos passou sem problemas estruturais; alertas de
histórico legado não são aprovação. GDD/TDD e moveset não foram alterados; a
divergência dos nomes/itens do jogo-fonte ainda deve ser reconciliada antes de
promover esses objetos a equipamento canônico do fan game.

Fluxo aprendido nesta revisão: congelar a matriz aprovada; comparar candidato
com imagem e documentos hash-bound; expor toda a cadeia anatômica do braço e a
pegada do objeto; manter arma contundente visualmente distinta de lâmina; isolar
silhueta do projétil dos efeitos; separar equipamento de identidade de
referências do jogo-fonte; e repetir a checagem de hashes após qualquer ajuste de
metadata/linhagem. A revisão aprova apenas a folha conceitual para avaliação do
dono, não sprites, animação, conversão SMS, ROM ou qualidade final.


## 2026-11-04 — montagem de marcos de sprites para revisão do proprietário

Pedido do proprietário: organizar visualmente a primeira prova de Social até a produção pós-J.J.
Artefato candidato `sprite-production-milestones-review-v01`, no registro central existente.
Saída: `SMS_projects/master_of_fighters/out/diagnostics/sprite_milestones_20261104/`.

São 28 marcos (MOF-S001 a MOF-S028), sete pranchas gerais, 28 detalhadas,
PDF de 35 páginas, painel `index.html` com notas e exportação, metodologia e
índice de 140 arquivos de entrada por SHA. J.J. animado é a referência S014;
a produção pós-J.J. ocupa S017 a S028. O último marco visual localizado é a
reprodução técnica de 03/11 da mesma arte da provocação v3.

Verificação: PDF renderizado em 35 páginas, pranchas inspecionadas, filtros e
formulário do painel exercitados; 236 links locais conferidos antes do ajuste
final que retirou a memória mutável dos fingerprints; 41 saídas registradas.
Nenhuma arte de personagem, ROM ou runtime alterados. Sem nova QA de ROM ou
promoção de arte, FPS ou AAA. O catálogo global permanece bloqueado pelo
relatório Social61v5. O recorte de ancestralidade também expõe papel duplicado
preexistente em `dr-social-cps2-light-jab-v05`. Aceites anteriores preservados.

Proteção local: `.runtime/backups/mof-sprite-milestones-20261104.zip`,
5.438.864 bytes, 41 entradas verificadas; SHA-256
`92787c0b2731c8945551d64f64e19c1fbceb2eb45c56b77b62673263de5c8b73`.
Recibo JSON homônimo. Somente saídas da revisão; fontes e vídeos originais
permanecem com seus owners. Cópia no mesmo disco, não GitHub ou backup externo.

Próximo: proprietário revisar por ID e exportar a checagem. Não modificar
pixels nem reabrir aceites com base apenas na ordem das versões.
