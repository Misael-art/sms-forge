# Cena 02 · matriz Hayato × Alis

## Saltos combinados com espadada e guarda

O dono aprovou a altura e a velocidade do salto da b29. O novo relato
veio depois de alternar diagonais e vertical com **trás + 1** e
**cima + trás + 1**. A sequência foi reproduzida em sessão privada no
Emulicious com a b29 identificada por SHA.

| Caso | O que ocorreu na b29 | Alteração |
|---|---|---|
| Espadada sustentada, depois ↑ + trás + 1 | O primeiro ↑ chegou durante a recuperação. Alis ficou no chão nas 36 leituras da diagonal. Depois de soltar e apertar ↑ de novo, o salto vertical completou seus 20 ticks. | Guardar a nova pressão e o vetor. Consumir uma vez na primeira janela livre. Cobrir soltura curta, expiração e cancelamento. |
| Guarda no ar com ↑ + trás + 1 | O desenho #59 apareceu sozinho durante os 20 ticks aéreos. | Encadear extensão #55, escudo recolhido #59 e descida #57. A lógica de guarda acompanha o controle durante o arco. |
| Diagonal para a frente após marcha e espadada | A pose #58 foi solicitada por cinco ticks. O desenho ficou em #55 e pulou para #56 no ápice. | Antecipar o carregamento na flexão e na subida e reservar espaço antes das previsões de fases mais distantes. |

[Controle b29, com direção, estado, pivô e IDs por tick](../out/diagnostics/alis_20261121_salto/qa-b29-mixed/input.json) · [Diagnóstico e ações para curadoria](curation_candidates/2026-11-21_alis_salto_comandos_montagem.json).

### b30 · teste de entrada e diagnóstico da primeira espadada

A b30 exibiu oito saltos completos no replay contínuo. Cada salto chegou a
Y66, durou 20 ticks no ar e voltou a Y144. As duas travessias apresentaram
as chaves #55, #58, #56 e #57, nessa ordem. A guarda aérea sustentada
apresentou #55, #59 e #57. Em outro voo, soltar e reaplicar a guarda
mostrou #55, #58, #59 e #57. A nova pressão de ↑ durante esse voo
disparou um segundo salto após o pouso. Manter a pressão por mais tempo
encerrou a cadeia em dois saltos. O primeiro salto após a espadada
começou dois ticks depois da liberação do controle.

Os pixels de 27 exposições foram conferidos na captura por quadros.
Na execução contínua, as duas espadadas acertaram e levaram Hayato de
100 a 90 e depois a 80 de vida. No primeiro acerto, o jogo já pediu
#18 enquanto a tela ainda mostrava a preparação #17, e a recuperação
#19 também ficou ausente nesse primeiro golpe. No segundo acerto,
o pedido, a residência e a apresentação coincidiram em #18.

Essa sequência revelou que a previsão de ataque era interrompida
pela pose de guarda em pé antes de frente ou trás + 1 completar o limiar.
A proteção da guarda em pé também ocupava espaço enquanto a espadada
já estava em curso. A revisão seguinte antecipa as poses do botão 1
com a guarda na tela e permite reutilizar o espaço durante o golpe.
Na guarda aérea, os botões retidos deixam de ativar o caminho de
previsão dos normais em pé. As janelas nominais da b30 foram
34,95493365251551 e 40,44785179791081 atualizações por segundo.

[ROM b30](../out/candidates/scene02_alis_jump_mix_b30/rom/master_of_fighters.sms) · [Quadros e contatos](../out/diagnostics/alis_20261121_salto/qa-b30/continuous/probe.json) · [Conferência visual](../out/diagnostics/alis_20261121_salto/qa-b30/pixels.json) · [Replay com áudio](../out/diagnostics/alis_20261121_salto/qa-b30/continuous/round-continuo.mp4) · [Recibo e cadência](../out/diagnostics/alis_20261121_salto/qa-b30/continuous/round-continuo.json).

### b32 · sequência mista corrigida no Emulicious

[ROM b32](../out/candidates/scene02_alis_jump_mix_b32/rom/master_of_fighters.sms),
SHA-256 `201757c38220c8890bd1bb09b00f6b1fad2a0ace4e5b92184578fe3cfb57e03e`.
Pré-gates e 15 bancos conferidos. O corredor de sondas deixou 81 bytes
livres. As sessões privadas `0eff089ffae144cd97e855493e3fd9d9`
(por quadros) e `951e17d1d82d4fda8708aa174fffc7b4` (contínua)
foram encerradas após a coleta.

| Entrada e condição | Resultado observado | Trecho no vídeo |
|---|---|---|
| Segurar trás + 1 no primeiro golpe após boot | Preparação #17, acerto #18 com dez pontos de dano e recuperação #19. A recuperação foi pedida no tick 7 e exibida no tick 8 desse primeiro golpe. | 0:01–0:02 |
| Acrescentar ↑ com trás + 1 durante a espadada | Flexão na primeira janela livre, decolagem dois ticks depois, recuo até a borda e pouso. | 0:02–0:03 |
| ↑ e dois saltos para a frente a partir de lados opostos | Vertical em X fixo. Nas travessias, as fases #55, #58, #56 e #57 apareceram em ordem e a face virou junto ao rival. | 0:03, 0:08 e 0:11 |
| Manter guarda no ar e segurar ↑ até o chão | Guarda #55 → #59 → #57. Uma decolagem para a pressão sustentada. | 0:13–0:14 |
| Soltar e reaplicar guarda com nova pressão de ↑ | Alis abriu a guarda, voltou ao escudo recolhido e executou um segundo salto depois de pousar. | 0:14–0:16 |
| Nova espadada e novo salto vertical | Segundo acerto #18, com os mesmos IDs no pedido, na residência e na tela. Hayato ficou com 80 de vida. O salto seguinte completou o arco. | 0:19–0:20 |
| Baixo, depois frente + 1 após a sequência | Passo de Escudo #49 acertou com a pose publicada e reduziu a vida a 67. | Sonda por quadros após o replay |

A curva completa de cada salto ficou igual ao controle de física da b29.
As 33 exposições conferidas no framebuffer incluíram as três poses de
cada espadada. A faixa de vida ficou estável nos 269 quadros aéreos
conferidos. As 12 amostras de SAT por pose e face chegaram a 48 sprites
e oito por linha. O pior intervalo entre ticks foi quatro quadros do VDP.
O trecho medido registrou zero falhas do renderizador e zero términos
de transferência em área ativa.

As janelas de NTSC ficaram em **37,951070822731126** e
**43,943345163162356** atualizações/s pelo relógio nominal do VDP.
Em tempo de parede foram 29,857555292350206 e 37,66379235906076.
O piso de 58 segue aberto. A resposta de entrada e a ordem das poses
foram verificadas para a sequência mista. O acabamento de ritmo e
o veredito de produto continuam pendentes.

Os impactos registraram sinal no monitor privado. As janelas de cada
espadada, alinhadas pelos transientes na mídia de apresentação,
mediram 28,985507246376812% e 37,5% de atividade. O replay bruto
completo mediu 1,7191977077363896% de atividade com as marchas
e os saltos silenciosos. O vídeo de apresentação usa os mesmos
quadros e tempos de vídeo, com o áudio da captura adiantado em
0,57 s. A medição de cadência usa o registro bruto.
[Alinhamento de áudio e janelas de golpe](../out/diagnostics/alis_20261121_salto/qa-b32/continuous/alis-b32-saltos-e-espadada.json) ·
[Áudio do replay inteiro](../out/diagnostics/alis_20261121_salto/qa-b32/continuous/audio.json).

[Vídeo da sequência](../out/diagnostics/alis_20261121_salto/qa-b32/continuous/alis-b32-saltos-e-espadada.mp4) ·
[Gravação bruta](../out/diagnostics/alis_20261121_salto/qa-b32/continuous/round-continuo.mp4) ·
[Recibo contínuo e cadência](../out/diagnostics/alis_20261121_salto/qa-b32/continuous/round-continuo.json) ·
[Trajetórias](../out/diagnostics/alis_20261121_salto/qa-b32/flights.json) ·
[Pixels](../out/diagnostics/alis_20261121_salto/qa-b32/pixels.json) ·
[SAT e pior intervalo](../out/diagnostics/alis_20261121_salto/qa-b32/runtime.json) ·
[Passo de Escudo](../out/diagnostics/alis_20261121_salto/qa-b32/special-regression.json).

O teste focal é `tools/replay_alis_jump_mix.py`. A b32 usa o manifesto
`out/diagnostics/alis_20261121_salto/bound-b27/duel_repertoire_hold_6_build.json`,
os bancos `banks-b27` e a prancha `alis_20261121_posturas/staged-b25/postures-plan.json`.
No wrapper do host, forneça ROM, pasta de bancos e destino novo, com
`--plan` e `--continuous`. O teste em C cobre ainda toque expirado,
toque perto do fim da recuperação e cancelamento com baixo.

## Salto alto e cruzamento de lado

O dono relatou que o salto da b26 parecia lento e baixo. A b26 subia 26 px
em um arco de 28 ticks no ar e aplicava a separação horizontal do chão
também durante o voo. Os bancos selecionavam a face no início do duelo.

A b27 comprovou o cruzamento com ápice de 78 px e 24 ticks no ar. No
primeiro cruzamento contínuo, o tempo de parede ainda foi de 0,95 s. O
ensaio b28 de 82 px faria o topo da cabeça ocupar pixels da barra de
vida junto à borda. A revisão b29 mantém a compressão no chão e aplica
impulso vertical de 14,625 px/tick, gravidade de 1,5 px/tick² e velocidade
horizontal de 6 px/tick na diagonal. O ápice calculado é de 78 px e a
fase aérea tem 20 ticks. Sem troca de pose, somente as coordenadas
alteradas da SAT são atualizadas.

Alis conserva o vetor da decolagem quando o direcional é solto. O
cruzamento exige altura suficiente e espaço para completar a passagem.
Os sprites das duas faces compartilham a VRAM para que Alis e Hayato
possam virar durante a travessia. A orientação de um golpe já iniciado
continua ligada à sua pose e hitbox até o fim do golpe.

[Primeiro ensaio de cruzamento](../out/diagnostics/alis_20261121_salto/qa-b27/continuous/round-continuo.mp4).

O teto de composição por face soma 58 sprites na SAT, oito por linha
e 32 células dinâmicas P0. Esses limites também cobrem a janela em que
Hayato continua um ataque após Alis passar para o outro lado.

### b29 · prova no Emulicious

[ROM b29](../out/candidates/scene02_alis_crossing_b29/rom/master_of_fighters.sms), SHA-256 `3f0ee085a36c0a6249098a21682b747ea65dc427971a34adc13ddd03fcd56757`.
O build passou pelos pré-gates, verificou os 15 bancos e deixou 83 bytes
livres antes do corredor das sondas.

| Caso | Resultado na ROM |
|---|---|
| Salto vertical | Pivô X111 durante todo o ciclo. De Y144 a Y66, com dois ticks no ápice e 20 ticks no ar. O pouso volta a Y144. |
| Cruzamento da esquerda para a direita | X111→216. A virada em X150/Y66 mostra as duas faces corretas. |
| Cruzamento da direita para a esquerda | X174→68. A virada em X134/Y66 mostra as duas faces corretas. |
| Diagonal iniciada longe | X32→120 com Hayato em X144. A entrada tardia preserva a separação na queda. |
| Retomada do combate | Escudo do lado direito, espadada do lado esquerdo e novo escudo reduziram a vida de Hayato a 94, 84 e 78. |

O salto vertical ocupou 30 quadros do VDP entre a primeira pose no ar e
o retorno ao chão, ante 55 no primeiro vertical da b26. As duas
travessias ocuparam 40 e 39 quadros do VDP. Os seis quadros de virada e
pouso comparados com a arte conferiram pixel a pixel nas regiões
visíveis. A faixa das barras de vida permaneceu idêntica ao longo de
168 quadros dos quatro saltos. [Trajetórias e poses](../out/diagnostics/alis_20261121_salto/qa-b29/input.json) · [Framebuffer e HUD](../out/diagnostics/alis_20261121_salto/qa-b29/pixels.json) · [Comparação temporal](../out/diagnostics/alis_20261121_salto/qa-b29/flight-comparison.json).

O pior intervalo chegou a quatro VDP. A troca registrou zero falhas de
renderização e zero fins de transferência em área ativa. Na primeira
captura contínua, as janelas deram 37,951070822731126 e 53,43111286884514
atualizações/s pelo relógio nominal do VDP. O piso de 58 segue aberto.
[Captura com áudio](../out/diagnostics/alis_20261121_salto/qa-b29/continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_salto/qa-b29/continuous/round-continuo.json) · [Medição por quadros](../out/diagnostics/alis_20261121_salto/qa-b29/runtime.json).

Uma segunda captura em sessão nova repetiu os mesmos 30, 40 e 39 VDP
no salto vertical e nas duas travessias. Em tempo de parede, a primeira
travessia levou 1,055 s na primeira gravação e 0,830 s na segunda. O
cruzamento inverso levou 0,771 s e 0,766 s. As duas repetições registraram
os três contatos esperados e foram encerradas. [Segunda gravação](../out/diagnostics/alis_20261121_salto/qa-b29/continuous-repeat/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_salto/qa-b29/continuous-repeat/round-continuo.json).

## Posturas e salto de Alis

O pedido de 21/11 acrescentou agachamento, salto vertical, saltos diagonais
e as guardas em pé, abaixada e aérea ao ensaio da Cena 02. A marcha e o
áudio da b23-r3 são os controles. As lições de paleta, proporção,
sequenciamento, buffers, animação e som por material, junto à direção
futura para o timbre da espada, ficam no
[registro de curadoria](curation_candidates/2026-11-21_alis_paleta_movimento_audio.json).

| Ação | Coreografia no duelo |
|---|---|
| Agachar e levantar | Dois apoios no chão, flexão intermediária e base baixa. A cabeça acompanha o torso e o escudo permanece junto ao braço. |
| Salto vertical | Compressão no chão, extensão curta, joelho recolhido no ápice, busca do chão e flexão de pouso. O peso da espada e do escudo fica perto do centro do corpo. |
| Salto diagonal | Pés e tronco projetam o impulso horizontal no início. A trajetória preserva a separação mínima contra o rival e respeita as bordas. |
| Guarda em pé | A borda do escudo sobe durante a defesa e a base dos pés se abre para receber o impacto. |
| Guarda abaixada | O escudo cobre torso e rosto enquanto os dois pés sustentam o peso abaixo da altura em pé. |
| Guarda aérea | O escudo sobe diante do corpo e as botas se recolhem. A cabeça mantém o registro com o movimento de salto. |

A b24 comprovou as trajetórias, os três bloqueios lógicos e os acertos de
escudo e espadada. A revisão encontrou o Passo de Escudo interceptado pela
entrada de baixo, ausência da guarda em pé durante seu bloqueio, e queda de
14 px no topo da silhueta ao alternar para a guarda aérea no ápice. Também
localizou a flexão, a queda e a diagonal no framebuffer dois VDP após os
registros escolhidos. A revisão seguinte preserva a janela do comando
direcional, fixa a guarda em pé e a flexão inicial no atlas residente,
antecipa as próximas poses e registra a guarda aérea pelo torso. [Traço da b24](../out/diagnostics/alis_20261121_posturas/qa-b24/input.json) · [Fonte e direção visual](../data/source_art/sprite_studies/scene02_alis_postures_20261121/source.md).

A b25 confirmou as nove poses e os contatos de escudo, espada e Passo de
Escudo. Na guarda aérea, o estado e a pose #59 eram corretos, mas a
composição manteve o pivô visível em X120/Y129 enquanto a lógica já
publicava X117/Y127 e continuava o arco. O quadro 866 manteve 193 pixels
visíveis de #59 no pivô anterior e só 15 de 146 pixels comparáveis no novo.
A b26 permite atualizar a SAT de Alis usando a última pose publicada de
Hayato enquanto a próxima página P0 dele está carregando. A troca usa o
limite de cinco padrões junto à SAT e preserva a contagem de quadros
parcialmente entregues. [Prova de fronteira da b25](../out/diagnostics/alis_20261121_posturas/qa-b25/guard-contact-pixels.json).

### b26 · prova no Emulicious

[ROM b26](../out/candidates/scene02_alis_postures_b26/rom/master_of_fighters.sms), SHA-256 `57be8e489786c65cd3092c1bed86f3fc90c5dd20e900bd3d3c59d662d2a68cda`. O build passou pelos pré-gates, com 15 bancos de arte conferidos e corredor de sonda com 162 bytes de folga. As sessões usaram entrada privada, heap de até 512 MiB e gravação em disco. [Build](../out/candidates/scene02_alis_postures_b26/build_record.json) · [Lote de assets](../out/diagnostics/alis_20261121_posturas/staged-b25/art-receipt.json) · [Limites de sprites](../out/diagnostics/alis_20261121_posturas/staged-b25/hardware.json).

| Caso | Resultado observado |
|---|---|
| Agachar e levantar | Baixo manteve X58/Y144 e baixou o topo da hurtbox a Y111. A flexão #51 aparece na entrada e na saída. |
| Salto vertical | Duas leituras de compressão no chão, 28 ticks no ar e ponto mais alto Y118. X58 permanece fixo. Segurar ↑ e 1 até depois do pouso gera um salto e zero ataques. |
| Saltos diagonais | X58→116 para frente e X116→58 para trás, com subida de 26 px. Soltar a direção durante o voo conserva o impulso da decolagem até o pouso. |
| Guarda em pé | Escudo #54 diante do soco, vida 100. No VDP690, 175 de 175 pixels visíveis de Alis coincidem com a pose e o pivô publicados. |
| Guarda abaixada | #53 resolve o chute de sondagem, vida 100. No VDP759, 376 de 376 pixels visíveis conferem. |
| Guarda aérea | Trás no ápice ergue o escudo, a soltura abaixa e reaplicar trás volta a cobrir durante o mesmo voo. O bloqueio do soco ocorreu em X117/Y127, com 146 de 146 pixels conferidos no VDP833 e vida 100. |
| Regressão de comandos | Escudo #21, espadada #18 e Passo de Escudo #49 causam 6, 10 e 13 de dano em execução contínua. |

A [captura com áudio](../out/diagnostics/alis_20261121_posturas/qa-b26/continuous/round-continuo.mp4) tem 15,88 s e mostra as três defesas em 9,47 s, 10,62 s e 11,85 s. As nove poses têm comparação exata de pixels. O pico observado foi de oito sprites por linha. O pior intervalo foi de quatro VDP, com zero falhas de renderizador e zero fins de transferência na área ativa. A sessão por quadros `7c39436627204a1c83cf9f98401ac048` e a contínua `ab289e18e668441d85d1293256b7a943` foram encerradas. [Nove poses](../out/diagnostics/alis_20261121_posturas/qa-b26/poses.json) · [Pixels no bloqueio](../out/diagnostics/alis_20261121_posturas/qa-b26/guard-contact-pixels.json) · [Trajetórias](../out/diagnostics/alis_20261121_posturas/qa-b26/input.json) · [Pior intervalo](../out/diagnostics/alis_20261121_posturas/qa-b26/runtime.json).

O trecho de luta mediu 37,951070822731126 e 42,94463277309048 atualizações/s em NTSC nominal, ou 37,987818769051785 e 42,72023016817532 em tempo de parede. O piso de 58 e a dispersão máxima de 2 reprovaram. A face direita de Alis tem prova viva. A face esquerda tem conversão e empacotamento conferidos. [Janelas de medição](../out/diagnostics/alis_20261121_posturas/qa-b26/continuous/round-continuo.json).

O [round completo com áudio](../out/diagnostics/alis_20261121_posturas/b26-round-continuous/6-continuous/round-continuo.mp4) da mesma ROM chegou ao KO de Hayato com 16 acertos e todas as poses de contato solicitadas, residentes e submetidas. O Saque #46 foi registrado no contato e seu quadro seguinte, VDP824, tem o mesmo SHA da captura comparada pixel a pixel no controle b23-r3. O áudio do round passou com 9,55% de atividade. O pior intervalo ficou em quatro VDP e houve zero fins de transferência na área ativa. As janelas do round registraram 36,15173775632064 e 37,951070822731126 atualizações/s nominais, com 30,417060859101625 e 36,38274646214365 em tempo de parede. [Recibo do round contínuo](../out/diagnostics/alis_20261121_posturas/b26-round-continuous/6-continuous/round-continuo.json) · [Round por quadros](../out/diagnostics/alis_20261121_posturas/b26-round/6-round/round-completo.json) · [Áudio](../out/diagnostics/alis_20261121_posturas/b26-round-continuous/6-continuous/audio-audit.json).

## Marcha com transferência de peso e efeitos dos golpes

A revisão manual da b21 confirmou a melhora de identidade, porém mostrou as pernas se movendo sob um tronco rígido, com espada e escudo estáticos. No áudio, um único ruído de impacto atendia ao soco e à espadada. O controle é a b21 de SHA `6f7c86e65fa1e530d67e912353d33502b955a575bd26721757ff5d06af04ac48`.

| Fase | Movimento esperado na marcha |
|---|---|
| Contato | O pé recebe o peso com o tronco próximo à altura da guarda. |
| Compressão | O quadril cede dois pixels enquanto o pé de apoio se mantém na linha do chão. O escudo acompanha a carga. |
| Passagem | O corpo sobe dois pixels. A ponta da espada percorre um arco curto em relação à mão e o escudo recupera com atraso. |
| Novo apoio | A altura volta para perto do neutro e o equipamento percorre o restante do arco antes da repetição. |

O soco de escudo pede um impacto curto e grave. A espadada pede ataque mais brilhante e uma cauda tonal breve. Guarda usa um toque metálico próprio. Um golpe fora do alcance pode emitir o som do movimento e conserva o silêncio do impacto. Medir marcha em avanço e recuo, apoio no chão, escala de rosto e leitura em 1×. Conferir também o tempo de emissão, a distinção das três respostas e os efeitos junto a HUD e VDP no round.

A revisão independente encontrou deriva horizontal do apoio entre compressão e passagem. O ajuste compensou o deslocamento de quatro pixels do pivô entre as chaves. Na direção inicial da ROM a diferença de apoio ficou em 0,5 px no avanço e 0 px no recuo. Nas duas faces, a composição mantém o topo em Y92, Y94, Y90 e Y92, a sola em Y143 e até quatro sprites de Alis por linha. [Poses a 1×](../out/diagnostics/alis_20261121_marcha_e_sfx/marcha-alis-1x.png) · [Apoios](../out/diagnostics/alis_20261121_marcha_e_sfx/marcha-apoios.json) · [Composição nas duas faces](../out/diagnostics/alis_20261121_marcha_e_sfx/marcha-duas-faces.json).

A b23-r2 confirmou os contatos por quadros, mas na execução contínua a leitura MFD1 caiu durante a escrita nos dois quadros de contato. O contador de guarda do registro estava ímpar nos quadros 324 e 365 do vídeo. O dano apareceu em ambos os golpes. A ordem de publicação foi ajustada para selar o registro de pose e contato antes de processar o PSG no mesmo tick. [Leituras parciais da b23-r2](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r2-runtime/continuous/mfd1-contact-boundary.json).

As fontes do lote são `tools/revise_scene02_alis.py`, `inc/duel_sfx.h`, `src/duel_audio.c` e `src/duel_scene02.c`. A recomposição parte de `repertoire_20261119/scene02-actions-plan-v2.json`, SHA `1feab3854ae916b040390c8f70f8c0219239fdcf7ba1a6f03a71ace6d6094e92`, e usa o empacotador e o vínculo de bancos da Cena 02. [Plano da marcha](../out/diagnostics/alis_20261121_marcha_e_sfx/scene02-walk-sfx-apoio-plan.json) · [Manifesto de áudio](../out/diagnostics/alis_20261121_marcha_e_sfx/psg/audio-manifest.json) · [Manifesto de compilação](../out/diagnostics/alis_20261121_marcha_e_sfx/bound-apoio/duel_repertoire_hold_6_build.json).

### b23-r3 · prova no Emulicious

[ROM b23-r3](../out/candidates/scene02_repertoire_walk_sfx_b23_r3/rom/master_of_fighters.sms), SHA-256 `4b6a5b4847397cb7516850452e2fc0e47d67a379107093c14e91d188d64110c6`. O build passou pelos pré-gates, confirmou os bancos 02–16 e os seis efeitos no trecho fixo da ROM. O corredor da sonda tem 214 bytes livres. As sessões foram privadas, com entrada do controle SMS do próprio processo. A JVM usou até 512 MiB de heap, com as capturas temporárias em disco e uma sessão por vez. [Compilação](../out/candidates/scene02_repertoire_walk_sfx_b23_r3/build_record.json) · [Corredor](../out/candidates/scene02_repertoire_walk_sfx_b23_r3/probe-corridor.json) · [Bancos](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/mapper.json).

| Verificação | Resultado na b23-r3 | Evidência |
|---|---|---|
| Marcha e limite da arena | 15 poses de Alis conferidas pixel a pixel no framebuffer. As oito poses de marcha incluem toda a oscilação de 4 px. Recuo de X111 a X32 com esquerda ainda consumida e avanço até X120. | [Framebuffer](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/visible-poses.json) · [Canto e cadência por quadros](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/wall-and-pacing.json) |
| Soltura no alto do passo | Na passagem #43 do recuo e #39 do avanço, a direção foi consumida mais uma vez após o envio da soltura. Ambos os pivôs estabilizaram no primeiro tick que leu o direcional neutro. A volta à guarda desce 2 px num único tick, mantendo a sola em Y143. A revisão a 1× também registrou uma pequena mudança brusca de base ao parar comprimida contra Hayato. | [Capturas e consumo de entrada](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-release-isolated/release.json) · [Encerramento](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-release-isolated/closed.json) |
| Golpes no vazio e acertos | Dois erros fora de alcance, sem redução de vida. Na troca contínua, escudo #21 confirmado no quadro 320 com 6 de dano, espadada #18 no quadro 365 com 10. As duas poses estavam solicitadas, residentes e submetidas no contato. | [Traço por quadros](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/trace.json) · [Vídeo](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/round-continuo.json) |
| Timbres e dinâmica | O PCM do escudo tem picos iniciais na faixa de 377 a 431 Hz e decai abaixo de 325 Hz. A espadada tem pico de 1.723 Hz, com cauda em queda. O recorte dos efeitos passou o piso de atividade de 5%, com 16%. A gravação inteira da troca ficou com 2,85% devido ao intervalo de marcha e espera entre os golpes. O relógio da trilha capturada inclui atraso da rota de áudio. | [Áudio dos dois golpes](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/golpes-escudo-e-espada.wav) · [Medição](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/audio-audit.json) |
| Guarda e alcance | A semântica de guarda com resposta e o acerto de borda foram observados. Os dois ensaios ainda reprovam a cadência. | [Guarda com resposta](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/alis_guard_counter/6-alis_guard_counter.json) · [Último pixel válido](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/alis_hit_edge/6-alis_hit_edge.json) |
| Orçamento da troca | Pico de 47 sprites no canto e sete por linha. Zero transferências encerradas em área ativa e zero falhas do renderizador. O pior intervalo chegou a três VDP. As duas janelas deram 40,49230209081007 e 42,87143295565962 atualizações/s em tempo de parede, ou 51,433688088701395 e 52,43240047877327 pelo relógio nominal do VDP. O piso de 58 reprova nas duas. | [Pior intervalo e SAT](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/wall-and-pacing.json) · [Janelas](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-runtime/continuous/round-continuo.json) |

O [round completo com áudio](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round-continuous/6-continuous/round-continuo.mp4) exibiu as quatro marchas, os oito golpes em pé e os dois especiais de ensaio. O escudo acerta aos 4,09 s, a primeira espadada aos 5,68 s e o KO de Hayato ocorre aos 17,98 s. A sessão contínua `48bc92c3a78942b9a5cc83893b20a4a7` registrou os 16 contatos com as poses corretas e terminou com o controle de entrada encerrado. O áudio do round passou com 8,73% de atividade para piso de 5%. [Recibo do round](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round-continuous/6-continuous/round-continuo.json) · [Áudio](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round-continuous/6-continuous/audio-audit.json).

O Saque de Hayato teve contato no tick 509, VDP724, com #46 solicitada, residente e submetida. No VDP725 apareceram os 855 pixels distintos da preparação e livres da sobreposição de Alis. Os intervalos máximos do round chegaram a quatro VDP nos ticks 361 e 497, com transferências de 12 padrões em fila nos dois casos. Houve 230 épocas perdidas, zero falhas do renderizador e zero fins de transferência em área ativa. As janelas de parede mediram 28,158267907899965 e 30,069515139436792 atualizações/s, equivalentes a 39,94849560287487 e 40,44785179791081 pelo relógio nominal. O trecho continua abaixo do piso em ambas as janelas. [Pixels da pose #46](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round/6-round/hayato-saque-pixels.json) · [Traço e carga do round](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round/6-round/round-trace.json) · [Recibo por quadros](../out/diagnostics/alis_20261121_marcha_e_sfx/b23_r3-round/6-round/round-completo.json).

O SDCC registrou o aviso 357 na chamada de `PSGSFXPlay`, cuja assinatura no SDK recebe `void *`. Os efeitos residem no trecho fixo da ROM e foram reproduzidos na sessão de áudio privada. [Log de compilação](../out/candidates/scene02_repertoire_walk_sfx_b23_r3/logs_build.txt).

## Revisão de recuo, paleta e proporções de Alis

O dono reproduziu a marcha e os dois golpes do botão 1 na b18. Relatou recuo curto, mudança de paleta nos dois sentidos da marcha e alteração da escala da cabeça e da forma do corpo nos golpes. O [teste independente da b18](../out/diagnostics/alis_20261121_revisao_b18/qa-recuo-b18/run_5d9c3132987142588e8ae5d1489fc7e2/report.json) confirmou 48 px de recuo, com direcional ainda consumido no limite X63. Em quadro nativo isolado, 39 pixels do magenta principal da guarda passaram a 1 no recuo e 2 no avanço.

| Oportunidade | Correção aplicada | Controle de arte e engenharia |
|---|---|---|
| Recuo encerrado cedo pelo limite X63 | A margem é calculada pelas células e pelos pixels que o elenco emite em cada direção. A arena usa X32 a X223 no par em pé, observando 24 px de separação. | A partir de X111, o recuo esperado é 79 px. Conferir consumo de esquerda no limite, soltura, retorno à direita e ausência de pixels na borda oposta. |
| Túnica e escudo perdem as rampas da guarda na marcha | Os passos autorais mantêm as pernas e os apoios originais, registrados no quadril. O tronco, o rosto e os equipamentos vêm da guarda, com 1 px de balanço horizontal durante o ciclo. | O plano recompõe as poses com os mesmos RGB de túnica e escudo. A marcha mantém as quatro fases em cada sentido em sprites. |
| A cabeça cresce e a cintura ganha uma faixa ciano no golpe fraco | A preparação, a extensão e a recolha usam as proporções da guarda. O escudo mantém o painel magenta e a extensão usa o antebraço da pose autoral de contato. | Conferir o avanço do escudo em 1×, a mão junto ao equipamento, o dano 6 e a volta à guarda. |
| O perfil do rosto e do cabelo muda na espadada | O rosto e o cabelo da guarda são registrados no pescoço das três poses autorais. Os apoios e a ponta da espada em X55 da pose ativa são preservados. | Conferir a inclinação sem mudar tamanho aparente da cabeça, o contato por 1 sustentado, o dano 10 e a volta à guarda. |

O [comparativo a 1×](../out/diagnostics/alis_20261121_revisao_b18/comparacao-b18-b19-1x.png) mostra a primeira correção de composição. O [registro de cores](../out/diagnostics/alis_20261121_revisao_b18/comparacao-cores-planos.json) mede os rasters reconstruídos a partir das camadas. A revisão independente confirmou a continuidade de rosto, túnica e escudo e localizou dois pixels azul-escuros soltos nas emendas da preparação e da recolha da espadada. O teste vivo deve vincular cada pose esperada a um quadro do framebuffer da candidata.

### b21 · revisão dos pontos relatados

[ROM b21](../out/candidates/scene02_repertoire_alis_cohesion_b21/rom/master_of_fighters.sms), SHA-256 `6f7c86e65fa1e530d67e912353d33502b955a575bd26721757ff5d06af04ac48`. A b20 aumentou a diferença entre preparo e extensão do escudo e limpou os dois resíduos da espadada voltada à direita. A revisão estática encontrou dois pequenos grupos ciano e azul-escuro ainda separados à esquerda. A b21 removeu esses grupos na preparação e na recolha. A [prova de composição](../out/diagnostics/alis_20261121_revisao_b18/b21-plan-visual-check.json) conferiu guarda e 14 poses revistas nas duas faces, cada uma com uma massa de pixels conectada. [Comparativo a 1×, face direita](../out/diagnostics/alis_20261121_revisao_b18/comparacao-b18-b21-right-1x.png) · [Face esquerda](../out/diagnostics/alis_20261121_revisao_b18/comparacao-b18-b21-left-1x.png).

| Caso | Observado na b21 | Evidência |
|---|---|---|
| Recuar desde X111 e retomar o avanço | X32 após 79 px, com esquerda ainda consumida. Ao inverter, Alis chegou a X120 e preservou a separação de 24 px. A SAT no limite tinha 47 sprites e pico de 7 por linha. | Sessão `252e31e006974a1d9c6de60200e21e6d` · [Traço](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/trace.json) · [SAT](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/wall-and-pacing.json) |
| Reconhecer Alis em guarda, nas duas marchas e nas fases dos dois golpes de botão 1 | As 15 poses coincidiram pixel a pixel com o desenho na face direita. Todos os oito quadros da marcha preservaram 39 pixels de magenta e 18 de rosa escuro. | [Quadros nativos e SHAs](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/visible-poses.json) |
| Ver contato e consequência em execução contínua | Escudo com #21 em 0:05,30 e dano 6. Espadada com #18 em 0:05,97 e dano 10. As duas ações erraram quando acionadas com o adversário distante. | Sessão `c8fa39ee134a4975bfa701cc8e1448d8` · [Vídeo com áudio](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/continuous/round-continuo.mp4) |
| Testar a espadada na borda e a guarda com resposta | Na borda a 66 px, 1 px de interseção e 10 de dano. A 28 px, Hayato defendeu e acertou o soco em resposta. | [Borda](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/alis_hit_edge/6-alis_hit_edge.json) · [Guarda e resposta](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/alis_guard_counter/6-alis_guard_counter.json) |

O build conferiu os bancos 02–16 e o [corredor da sonda](../out/candidates/scene02_repertoire_alis_cohesion_b21/probe-corridor.json) manteve 263 bytes livres. Na troca focal, as duas janelas de parede deram 52,42232678200898 e 50,98397512481057 atualizações/s. O pior intervalo foi de três VDP, com zero envios encerrados em área ativa e zero falhas do renderizador. A cadência continua abaixo do piso de 58. [Recibo da captura e janelas](../out/diagnostics/alis_20261121_revisao_b18/b21-runtime/continuous/round-continuo.json).

No round completo, Alis e Hayato executaram as quatro marchas, os oito normais e os dois especiais de ensaio. Alis venceu com a espadada. Na sessão contínua `93891a7457ed418193597b4477125c5e`, as 16 poses de contato foram solicitadas, residentes e submetidas no tick registrado. O escudo aparece no primeiro contato em 0:04,43, a espadada em 0:06,51 e o KO em 0:18,51. As duas janelas de parede mediram 26,0488767488953 e 35,010753362898036 atualizações/s, equivalentes a 40,94720799294674 e 41,641228467403465 pelo relógio nominal do VDP. No stepping o pior intervalo foi de quatro VDP, com zero encerramentos de transferência na área ativa. [Round contínuo com áudio](../out/diagnostics/alis_20261121_revisao_b18/b21-round-continuous/6-continuous/round-continuo.mp4) · [Recibo com janelas](../out/diagnostics/alis_20261121_revisao_b18/b21-round-continuous/6-continuous/round-continuo.json) · [Round por quadros](../out/diagnostics/alis_20261121_revisao_b18/b21-round/6-round/round-completo.json).

O controle de identidade e material aplicado ao botão 1 também permite triar a arte restante. No plano, a pose ativa do chute forte conserva 14 pixels de magenta principal e zero de rosa escuro. O Passo de escudo de ensaio conserva 19 e 1 e sobe para 328 pixels brancos. Essas ações ficam na fila de revisão de material e proporção. A qualidade da face esquerda foi revisada na composição, com prova no emulador para a face direita.

### b19 · primeira correção em jogo

Na [b19](../out/candidates/scene02_repertoire_alis_cohesion_b19/rom/master_of_fighters.sms), SHA `5d432a0e181e9a65e700739f617d9037df6547a231573653baa3135fb002d63c`, Alis percorreu 79 px até X32, continuou lendo esquerda no limite e retomou o avanço até X120, a 24 px de Hayato. A guarda, os oito quadros de marcha e as seis poses dos golpes do botão 1 coincidiram pixel a pixel com o desenho esperado na face direita. O magenta principal manteve 39 pixels em todos os oito quadros de marcha. [Prova por pose](../out/diagnostics/alis_20261121_revisao_b18/b19-runtime/visible-poses.json) · [Traço](../out/diagnostics/alis_20261121_revisao_b18/b19-runtime/trace.json).

No [vídeo contínuo](../out/diagnostics/alis_20261121_revisao_b18/b19-runtime/continuous/round-continuo.mp4), o escudo mostrou #21 e tirou 6, e a espadada mostrou #18 e tirou 10. As janelas ficaram em 52,41069942705816 e 50,98037314261438 atualizações/s. O pior intervalo por quadros foi de três VDP e houve zero fins de transferência em área ativa. [Cadência](../out/diagnostics/alis_20261121_revisao_b18/b19-runtime/continuous/round-continuo.json) · [Pior intervalo](../out/diagnostics/alis_20261121_revisao_b18/b19-runtime/wall-and-pacing.json).

## b18 · Alis no controle principal

[ROM b18 com Alis no P1](../out/candidates/scene02_repertoire_alis_p1_b18/rom/master_of_fighters.sms), SHA-256 `e738daa7bf80875025cda66ea73d5e55803e4a034836427abc3175bf93fc27aa`. O perfil do Emulicious usado para abrir a b17 tinha o controle integrado ligado ao P1, onde a b17 colocava Hayato. A b18 começa com Alis à esquerda no P1 e Hayato à direita no P2. Cada direção usada para selecionar face ou controle no início é ignorada até sua própria soltura, deixando os demais comandos disponíveis.

- Build aprovado nos gates prévios com os bancos 02–16 conferidos e 263 bytes livres antes da sonda. [Recibo](../out/candidates/scene02_repertoire_alis_p1_b18/build_record.json) · [Corredor da sonda](../out/candidates/scene02_repertoire_alis_p1_b18/probe-corridor.json).
- Na sessão privada `14db838031d240e6a57f8cb1a4d04f7b`, só P1 recebeu comandos. Alis recuou de X111 para X96, avançou até X120, sustentou **1**, acertou e voltou a aceitar comandos. Hayato terminou com 90 de vida. Os dois sprites estão presentes na imagem nativa de abertura. [Traço](../out/diagnostics/alis_20261121_b18_p1/p1-check.json) · [Framebuffer inicial](../out/diagnostics/alis_20261121_b18_p1/inicial.png).
- Na sessão contínua `bc630885694145eebe1f64dfcebcf0a8`, Alis publicou as quatro poses de cada sentido de marcha e as três da espadada. O contato em 0:02,94 publicou #18 e tirou 10 de Hayato. As sessões fecharam. [Vídeo da b18 com áudio](../out/diagnostics/alis_20261121_b18_p1/continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_b18_p1/continuous/round-continuo.json).
- No P1 com a face direita, o toque e as duas pressões consecutivas produziram #20, #17 e #17 em 5, 6 e 6 leituras. A guarda a 28 px preservou a vida de Hayato, que respondeu com #8 e tirou 6 de Alis. A espadada a 66 px cruzou a caixa por 1 px e tirou 10 em t99/VDP177. Os três ensaios confirmaram a semântica e reprovaram a cadência por VDP. [Botões](../out/diagnostics/alis_20261121_b18_alis_buttons/6-alis_buttons.json) · [Guarda e resposta](../out/diagnostics/alis_20261121_b18_alis_guard_counter/6-alis_guard_counter.json) · [Limite](../out/diagnostics/alis_20261121_b18_alis_hit_edge/6-alis_hit_edge.json).

A prova cobre a entrada do controle virtual P1 e a apresentação na ROM. O botão físico do Steam Deck depende da sessão de abertura manual. O repouso usa a pose estática #16. O duelo continua local com dois jogadores e Alis no controle principal.

## b17 · reserva de padrões de sprites

[ROM de ensaio](../out/candidates/scene02_repertoire_hold6_20261121_b17/rom/master_of_fighters.sms), SHA-256 `1ee09f085f79d983da5595d0fdcad7048608171ae2917c275da8fa753578f900`. A busca da primeira faixa disponível passa a avançar por blocos com índices de 8 bits. Quando os pedidos já têm espaço atribuído, a preparação conserva as transferências e evita reconstruir a lista de faixas protegidas. A comparação de 20.000 tabelas sintéticas confirmou a primeira reserva do controle. O build passou pelos gates prévios e o [corredor da sonda](../out/candidates/scene02_repertoire_hold6_20261121_b17/probe-corridor.json) manteve 263 bytes de folga.

No [erro punido a 67 px](../out/diagnostics/alis_20261121_b17_alis_miss_punish/6-alis_miss_punish.json), sessão encerrada `e311433076ff4d62963a82bdb00b6241`, 82 intervalos lógicos cobriram 115 quadros VDP, ante 117 na b14. O pior intervalo continuou em quatro. A espadada errou com interseção zero em t100, como esperado. O Saque tirou 16 de vida em t111/VDP205, com local 2 → #46 solicitada, P1 residente e #0 submetida. Alis voltou a andar em t119. O roteiro reprovou a publicação da pose do Saque. O [patch da candidata](../out/candidates/scene02_repertoire_hold6_20261121_b17/renderer-experiment.patch) preserva o ensaio reproduzível.

| Espadada com botão 1 · esperado | Observado na b17 | Sessão encerrada e evidência |
|---|---|---|
| Acerto a 66 px, 1 px de interseção, dano 10 | Hayato 100→90 em t98/VDP178. Local 2 → #18 nas três etapas da sonda. Hayato volta a andar em t106, Alis em t111. A vantagem de Alis é −5 ticks. | `0e2201bdc49e4104a2caa5ea199aae83` · [Traço e PNGs](../out/diagnostics/alis_20261121_b17_alis_hit_edge/) |
| Guarda a 28 px, recuo de 3 px e resposta real | Guarda em t70/VDP150, vida 100. Hayato livre em t73 e acerta com soco curto em t78/VDP167, #8 publicada, Alis 100→94. Alis volta a andar em t86. | `3f5ece9a0a514b7ebae4bc48db68159f` · [Traço e PNGs](../out/diagnostics/alis_20261121_b17_alis_guard_counter/) |
| Frente na mesma posição recebe a espadada | Hayato 100→90 em t70/VDP150, recuo de 4 px. Retomada em t78 para Hayato e t83 para Alis. | `fce89f0172724441b26201550822200b` · [Traço e PNGs](../out/diagnostics/alis_20261121_b17_alis_wrong_guard/) |
| Toque de 5 leituras, pressão de 6, rearme após manter o forte | Uma ação por gesto. Poses iniciais #20, #17 e #17 nas leituras 5, 6 e 6. | `7adb1646b50c41d986363ea9d3ab0b6f` · [Traço](../out/diagnostics/alis_20261121_b17_alis_buttons/6-alis_buttons.json) |

Os quatro casos confirmaram a semântica e reprovaram a cadência por VDP.

- Na [sessão por quadros](../out/diagnostics/alis_20261121_b17_round_disk/6-round/round-completo.json) `6607e23469e74ab1847d8114eae5f4c1`, os quatro ciclos de marcha, os 14 contatos e o KO repetiram o controle. Os bancos 02–16 foram conferidos. As épocas perdidas passaram de 218 para 208 e a taxa do round passou de 44,95921755993649 para 45,4801818422069 atualizações por segundo nominal. Houve zero fins de transferência em área ativa. O pior intervalo permaneceu em quatro quadros VDP, nos ticks 334 e 468. Em t334 estavam em fila 8 padrões P1 e 4 P0. Em t468 estavam em fila 12 padrões P0. Foram 76.212 e 72.236 ciclos entre commits, respectivamente. O [traço](../out/diagnostics/alis_20261121_b17_round_disk/6-round/round-trace.json) e o [recibo dos piores intervalos](../out/diagnostics/alis_20261121_b17_round_disk/6-round/piores-intervalos.json) conservam etapas, cargas e quadros nativos.
- No nono contato, Saque local 2 → #46 solicitada, P1 residente e #46 submetida em t480/VDP669. A [imagem VDP670](../out/diagnostics/alis_20261121_b17_round_disk/6-round/hayato-saque-vdp-670.png) é idêntica, por SHA-256, à b14 VDP678. O [quadro anterior](../out/diagnostics/alis_20261121_b17_round_disk/6-round/hayato-saque-vdp-669.png) é idêntico à preparação b14 VDP677.
- Na [sessão contínua com áudio](../out/diagnostics/alis_20261121_b17_continuous/6-continuous/round-continuo.json) `14e4b5dceeda406ca82250dd7cf95757`, os mesmos resultados chegaram ao KO. O chute curto de Hayato publicou #10 no contato que pedia #11. As janelas de parede mediram 39,01123494727796 e 37,98667176447802 atualizações por segundo, ambas abaixo de 58. O [vídeo](../out/diagnostics/alis_20261121_b17_continuous/6-continuous/round-continuo.mp4) tem framebuffer 256×192 e áudio da rota privada. Guarda ociosa em 0:00, soco de Alis em 0:03,76, espadada em 0:05,36, chutes em 0:06,56 e 0:08,24, Saque em 0:09,05, Passo de escudo em 0:09,90 e KO em 0:13,69.
- Na [guarda com resposta em execução contínua](../out/diagnostics/alis_20261121_b17_alis_guard_counter/continuous-guard-counter/round-continuo.mp4), sessão encerrada `35f1d470cf084e52b75f48a9962816d4`, Hayato bloqueia em 0:00,49 (t69, vida 100) e acerta o soco curto em 0:00,81 (t78, Alis 94). O roteiro mantém trás por quatro quadros VDP e atrasa o toque de resposta até a primeira leitura livre. Hayato recua 1 px antes da guarda, elevando o gap no contato a 29 px. A primeira conversão do roteiro perdeu a guarda porque duas amostras lógicas ocuparam o mesmo quadro VDP. A segunda manteve a guarda e leu o toque ainda no bloqueio. As três tentativas e os roteiros estão [no diretório do caso](../out/diagnostics/alis_20261121_b17_alis_guard_counter/).
- No [erro punido em execução contínua](../out/diagnostics/alis_20261121_b17_alis_miss_punish/continuous/round-continuo.mp4), sessão encerrada `dba4139eb2dd4ca4826c6a6238929a9f`, a espadada erra a 67 px em 0:01,65 (t99). A punição ocorre em 0:02,07 (t110), com Alis 84 e Hayato ainda na pose #0. A trilha contém o impacto do Saque. A falha visual ocorre também fora do stepping.
- O [gate de áudio do round](../out/diagnostics/alis_20261121_b17_continuous/6-continuous/round-sfx-audit.json) conferiu 640.409 amostras mono, pico 1221 e 14% de atividade com piso de 5% para um recorte só de efeitos. O WAV usa cabeçalho PCM simples, compatível com o leitor. A [leitura inicial inválida](../out/diagnostics/alis_20261121_b17_continuous/6-continuous/round-sfx-audit-invalid-list.json) interpretou um bloco LIST como áudio e fica fora do aceite.
- Nas trilhas, a [guarda e o soco](../out/diagnostics/alis_20261121_b17_alis_guard_counter/continuous-guard-counter/audio-cues.json) têm picos ativos cerca de 0,18 s após os eventos no vídeo. O [erro e a punição](../out/diagnostics/alis_20261121_b17_alis_miss_punish/continuous/audio-cues.json) têm um único trecho ativo, cerca de 0,38 s após o contato de Hayato. Esses desvios são da mídia capturada. O sincronismo de áudio da ROM permanece sem prova.

O Emulicious rodou com sessões seriais, heap de 512 MiB e rota de áudio do PipeWire confirmada. A gravação do round e a contínua foram refeitas com a raiz da sessão no disco, sob a mesma reserva da fábrica. Todas as sessões fecharam. No [ensaio de espelho por Reset](../out/diagnostics/alis_20261121_b17_mirror_reset/mirror-reset.json), a ROM continuou de t50 a t105 e manteve as faces. A b17 começa direto no duelo local. A prova ainda carece de espelho, corte de cena para controle, camada de música e efeitos simultâneos, e revisão de entrega da b17.

## b14 · HUD e round completo

[ROM de seis leituras](../out/candidates/scene02_repertoire_hold6_20261121_b14/rom/master_of_fighters.sms), SHA-256 `e99ce3677559ea58907fbeee9cea1c8c530514f0803446bfd88a383a095a2fe1`. A preparação das células do HUD foi movida para antes do VBlank. A escrita usa apenas a faixa de células afetadas. Os bancos 02–16 foram verificados e o corredor da sonda tem 263 bytes de folga.

- Na sessão por quadros encerrada `aed93e6357b04414864b685794e81e6e`. Zero términos na área ativa, contra dez na b13-r2, sem erro do renderizador. No nono contato, Saque local 2→#46 solicitado/residente/submetido em t480/VDP677. O [framebuffer do VDP678](../out/diagnostics/alis_20261121_b14_round/6-round/hayato-saque-vdp-678.png) mostra o corte. Pior intervalo de quatro VDP, 218 épocas perdidas e 44,95921755993649 atualizações por segundo nominal no round por quadros. [Traço](../out/diagnostics/alis_20261121_b14_round/6-round/round-trace.json) · [Recibo](../out/diagnostics/alis_20261121_b14_round/6-round/round-completo.json).
- Na sessão contínua com áudio encerrada `712018970a994f608a7fbd58d6d52844`. Neutro em 0:00, soco de Alis em 0:05,48, espadada em 0:07,23, chute curto em 0:08,62, chute forte em 0:10,66, Saque em 0:11,60, Passo de escudo em 0:12,62, KO em 0:16,88. Os 14 contatos repetiram os IDs solicitados e o dano do stepping. O chute curto de Hayato, quinto contato, teve pose #10 publicada com #11 solicitada. [Vídeo de round com áudio](../out/diagnostics/alis_20261121_b14_continuous/6-continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_b14_continuous/6-continuous/round-continuo.json).
- A cadência registrou janelas de parede em 33,448850740457466 e 33,51973815559036 atualizações/s, ou 38,627884177986445 e 37,951070822731126 por segundo nominal do VDP. A dispersão passou dentro de 2 FPS, e cada janela reprovou o piso de 58. A b14 começa direto em duelo.

| Espadada com botão 1 · esperado | Observado na mesma b14 | Sessão encerrada e evidência |
|---|---|---|
| Acerto no último pixel válido a 66 px | Hayato 100→90 em t98/VDP179 com interseção de 1 px. A entrada de marcha volta para Hayato em t106 e Alis em t111. | `b6da0cfe3f3e4c2eb49f230b3f3e2b89` · [Traço](../out/diagnostics/alis_20261121_b14_alis_hit_edge/6-alis_hit_edge.json) |
| Erro um pixel além, seguido de punição com o Saque | Alis erra em t100/VDP184 com zero interseção. O Saque tira 16 de vida antes do retorno de Alis em t119. Há falha visual: no contato de Hayato a pose #46 foi solicitada e estava com P1 residente, mas a #0 permanecia publicada. | `d465897ec7724be68ca513b8518a64eb` · [Traço reprovado](../out/diagnostics/alis_20261121_b14_alis_miss_punish/6-alis_miss_punish.json) |
| Guarda a 28 px, seguida de resposta real com 1 curto | Guarda em t70 sem dano e com recuo de 3 px. Hayato pode pressionar em t73, inicia o soco ao soltar em t74 e acerta em t78 com local 2→#8 solicitado/residente/submetido. Alis perde 6 e volta a andar em t86. A atuação corporal da defesa segue pendente. | `51313d886597479da6da36bb51aea61b` · [Traço](../out/diagnostics/alis_20261121_b14_alis_guard_counter/6-alis_guard_counter.json) |

As pranchas registram [caixas e fronteiras](../out/candidates/scene02_repertoire_hold6_20261121_b14/alis-fronteiras-1x.png) e [proporções a 1× com o perfil da folha de Alis](../out/candidates/scene02_repertoire_hold6_20261121_b14/alis-proporcoes-1x.png). A punição a 67 px e o Saque aproximado no nono contato exercitam a mesma ação de Hayato a partir de pivôs distintos. A correção do caso aproximado se mantém. O caso distante exige preparar a camada de fundo enquanto o pivô ainda avança. A comparação de silhueta preserva o chão e deixa altura anatômica em aberto até anotar os landmarks atuais, separados de cabelo, arma e escudo.

### Revisão independente da b14

O revisor conferiu o SHA e os PNGs nativos das sessões encerradas da tabela.
No acerto de borda, a caixa ativa `[122,160) × [107,110)` cruza a região
vulnerável `[100,123) × [87,140)` por 1 px. O quadro VDP179 ainda mostra a
preparação e o HUD cheio. O VDP181 mostra a extensão, a vida menor e o
recuo. Ao descontar os 4 px de recuo, ainda sobram 5 px de fundo entre a
ponta da lâmina e o corpo na altura da caixa. Na guarda, Hayato permanece
na pose #0 e a sobreposição com a lâmina dificulta ler o bloqueio.

No Saque distante, o VDP184 e o VDP207 diferem em 72 pixels do HUD e em
zero pixels entre as linhas 24 e 143. Os PNGs do VDP207 e VDP213 são
idênticos. No nono contato do round, o VDP678 muda 1.924 pixels da arena
na mesma região em relação ao VDP677. Os dois resultados distinguem
o atraso persistente do Saque distante da exibição no primeiro quadro
após a submissão do Saque aproximado. [Punição e PNGs](../out/diagnostics/alis_20261121_b14_alis_miss_punish/) · [Round e PNGs](../out/diagnostics/alis_20261121_b14_round/6-round/).

No round por quadros, os piores intervalos foram de quatro VDP nos ticks
334 e 468. O primeiro prepara 8 padrões P1 e 4 P0. O segundo prepara
12 padrões P0. Os dois começam a transferência em VCount 195 e terminam
em 246, com os dois lutadores ainda em guarda. O preparo de P0 do tick
468 ocupa VCount 69 a 217 antes da entrega ao VDP. Esta revisão consultou
os arquivos das sessões existentes e mantém o aceite de produção pendente.

## b13-r2 · Saque e round completo

[ROM de seis leituras](../out/candidates/scene02_repertoire_hold6_20261121_b13_r2/rom/master_of_fighters.sms), SHA-256 `7e1b911741b8241a937a7e910a8d0e4cf04288ea195c0e425ea4891520bdf0fb`. O empacotador conferiu os bancos 02–16 sem diferença. A primeira tentativa da b13 encontrou erro interno `Unbalanced stack` no SDCC do host. A revisão r2 isolou o carregamento de uma camada pré-composta e compilou pelo mesmo wrapper.

- Na sessão por quadros `0be82bc97b284d58a913abf0f08b8034`. Quatro caminhadas de 32 px com os quatro quadros por sentido, 14 contatos e KO. No nono contato, o índice local 2 pediu #46. O P0 recebeu 12 e 11 células nos dois ticks anteriores. P1 residente e #46 submetida em t480/VDP666. O [framebuffer no VDP667](../out/diagnostics/alis_20261121_b13_r2_round/6-round/hayato-saque-vdp-667.png) exibiu 859 de 859 pixels distintos da #45 e livres da sobreposição de Alis. O VDP666 exibiu 0 de 859. A recolha #47 começou a ser publicada no VDP674. O pior intervalo foi 4 quadros VDP. Dez envios com alteração de vida terminaram em área ativa. [Traço](../out/diagnostics/alis_20261121_b13_r2_round/6-round/round-trace.json) · [Comparação de pixels](../out/diagnostics/alis_20261121_b13_r2_round/6-round/hayato-saque-pixels.json) · [Recibo](../out/diagnostics/alis_20261121_b13_r2_round/6-round/round-completo.json).
- Na sessão contínua `6bb2316bd8cb42e59d667ffe0d8c2c01`. Vídeo nativo 256×192, 853 quadros, 15,568 s e áudio do monitor privado. Os mesmos 14 contatos chegaram ao KO. O quinto contato registrou #11 solicitado/residente e #10 publicado. O Saque registrou #46 nos três campos. [Vídeo com áudio](../out/diagnostics/alis_20261121_b13_r2_continuous/6-continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/alis_20261121_b13_r2_continuous/6-continuous/round-continuo.json).
- A cadência registrou janelas de 39,93212859891641 e 30,567092934966677 atualizações/s em tempo de parede, com 39,94849560287487 e 39,277092315431595 por segundo nominal do VDP. A dispersão de parede foi 9,36503566394973. O piso de 58 FPS reprovou sob combate.
- O vídeo mostra o neutro inicial em 0:00, soco de Alis em 0:03,74, espadada em 0:05,33, chute curto em 0:06,51, chute forte em 0:08,20, Saque em 0:08,99, Passo de escudo em 0:09,83 e KO em 0:14,40. Defesa com resposta e erro de borda pertencem aos casos separados da b12 abaixo. A abertura da ROM salta diretamente para o duelo.

## b12 · primeira troca de Alis

**ROM** [b12, seis leituras](../out/candidates/scene02_repertoire_hold6_20261121_b12/rom/master_of_fighters.sms), SHA-256 `c30ed6cdd673a03148f8ca45218910f7e71facbb79846538e30b3b9cdbae761f`. P1 Hayato à esquerda, P2 Alis à direita. Ponte privada Emulicious, direção e botões lidos pela ROM, coleta quadro a quadro. Todos os IDs abaixo tiveram encerramento confirmado. A cadência por VDP reprovou em todos os casos. Janelas contínuas e áudio não foram medidos nessas sessões.

| Ação e esperado | Observado na b12 | Sessão e prova |
|---|---|---|
| `alis_landale/pe_1_curto` e `pe_1_longo`. Toque em 5, pressão até 6, pressão longa e soltura, com rearme | Leituras 5/6/6 iniciaram #20/#17/#17. Cada gesto disparou uma vez, inclusive mantendo 1 além do fim do forte. | `24fb1ae37e8043728763374207cf0696` · [Trace](../out/diagnostics/alis_20261121_b12_alis_buttons/6-alis_buttons.json) |
| `pe_1_longo`, acerto com 1 px de interseção a 66 px | Vida de Hayato 100→90 em t98/VDP180. Hayato anda de novo em t106 e Alis em t111. Pose local 2→#18 no registro. No VDP180 o HUD já muda, e a imagem da estocada aparece no VDP181. | `57823ef7ed8b429cb2f63ce5533bbac3` · [Trace](../out/diagnostics/alis_20261121_b12_alis_hit_edge/6-alis_hit_edge.json) |
| `pe_1_longo`, erro ao tocar a borda sem interseção a 67 px | Caixas ativas nos ticks de ação 5 e 6, erro único em t100/VDP182. Vida 100/100. Hayato permaneceu livre e Alis voltou a andar em t112. | `ddd2b50bca77421da35a289947567675` · [Trace](../out/diagnostics/alis_20261121_b12_alis_miss_edge/6-alis_miss_edge.json) |
| `pe_1_longo`, guarda a 28 px seguida de punição com 1 curto de Hayato | Guarda t70/VDP149, recuo 3 px, vida 100. Hayato volta a aceitar comandos em t73. O soco toca em t78/VDP167 (Alis 100→94) com #8 solicitado/residente e #7 publicado. Alis move no primeiro tick livre t86. A reação visual de guarda permanece pendente. | `1d1223eb51c443d4bf7ec31911a92f9d` · [Trace](../out/diagnostics/alis_20261121_b12_alis_guard_counter/6-alis_guard_counter.json) |
| `pe_1_longo`, direção de guarda invertida na mesma distância | Frente consumida em t70/VDP150. Hayato 100→90, recuo 4 px. Retomadas medidas com movimento em t78 e t83. | `4e5a2f21ad194970af60c21acffd6f0d` · [Trace](../out/diagnostics/alis_20261121_b12_alis_wrong_guard/6-alis_wrong_guard.json) |

**Função do forte.** Alis usa 1 sustentado para ameaçar a média distância, onde seu soco de guarda já perde alcance. Em chão livre, a ação prepara nos ticks 0–4, ameaça nos ticks 5–6 e recupera nos ticks 7–17. A opção gasta tempo de preparação e recuperação e tira 10 de vida no acerto. Em curta distância, o adversário consegue defender, voltar em três ticks e responder durante a recuperação. No erro a 67 px, a caixa não toca. A janela de resposta à distância precisa de alcance ou avanço suficiente do rival.

**Revisão a 1×.** A [prancha com as caixas e os quadros nativos](../out/candidates/scene02_repertoire_hold6_20261121_b12/alis-fronteiras-1x.png) mostra preparação e extensão. A interseção mede a caixa, e ainda havia cinco pixels de separação entre a ponta e o torso antes do recuo na altura do contato. O escudo lê-se na guarda ociosa e perde separação do torso durante a extensão. A silhueta baixa cerca de 5 px no alto da cabeça, com pés próximos à mesma linha do chão. Isso registra a flexão da pose. A estatura anatômica da régua do elenco exige landmarks próprios. No acerto leve da resposta, a barra de Alis perdeu quatro colunas verdes, mesmo com apenas seis pontos de dano. A cadência e o aceite temporal exigem a prova em execução contínua.

**Regressão preservada.** Na b11-r2, o Saque no VDP 674 pediu #46 (índice local 2), com P1 residente e #45 publicado. No pivô X=120, #46 precisava de 23 células de fundo e só 12 tinham sido transferidas nesse tick. Houve 16 ao fim da janela ativa e em seguida o alvo de upload mudou para #47. O gravador de round agora registra índice local, pedido, residência de P1, publicação e quatro imagens de VDP na fronteira do Saque.

**Limiar de oito leituras.** O controle b05/8 de SHA `ae34fa0fe797ff98bc2155f02379c47be425c7171af997e62f23a612657c5456` foi reexercitado na sessão encerrada `79f4e95d4a0948bb89468cff49536b83`. As leituras 7/8/8 iniciaram #20/#17/#17 uma vez cada. A cadência por VDP reprovou. [Traço](../out/diagnostics/alis_20261121_b05_hold8_buttons/8-alis_buttons.json).

**Contra após defesa comparado em Emulicious. A cadência e os demais casos seguem pendentes.**
A decisão do dono mantém ambas disponíveis para medir. [GD01/GD02 do piloto](decisions/hayato-alis-scene02_owner-comparison_20261119.json).

O ensaio b13 usou os dois binários da tabela em sessões privadas
independentes. O executor levou em conta a defasagem de um tick entre o
pedido de input e a leitura consumida pela ROM. Cada publicação observada
foi separada por dois quadros contados pela ponte. O ensaio registra
comportamento passo a passo e mantém o aceite de cadência pendente.
[Índice do repertório aprovado](repertorio_alis_hayato_provas.md).

| Pressão de 1 | ROM candidata | SHA-256 | Recibo |
|---|---|---|---|
| 6 leituras | [SMS](../out/candidates/scene02_hold6_20261119_b02/rom/master_of_fighters.sms) | `c1f08ccc607faf5656520e272288185569cdd63aa6da267987c3bd6f36084bc8` | [build](../out/candidates/scene02_hold6_20261119_b02/build_record.json) |
| 8 leituras | [SMS](../out/candidates/scene02_hold8_20261119_b01/rom/master_of_fighters.sms) | `d42ce2b4a61b60212ec619b13a3a7ca982c0015b1892e245b3696a69edf0af0d` | [build](../out/candidates/scene02_hold8_20261119_b01/build_record.json) |

Em NTSC, a abertura normal coloca Hayato no P1 à esquerda e Alis no P2.
O direcional horizontal anda e trás relativo assume guarda enquanto livre.
Segure 1 para a ação e solte para rearmar. O botão 2 está reservado durante
o duelo. Para testes de espelhamento, segure **direita no P1 durante o reset**
para pôr Hayato à direita, **cima** para trocar a atribuição P1/P2, ou os dois.

As posições abaixo são pivôs, com chão Y=144. O lado normal inicia H=111,
A=144, vida 100 para ambos. Os relógios nas linhas são relativos ao início
do corte. A posição de Alis antes do contato, a identidade do lutador e a
pose precisam ser lidas no probe para validar a pré-condição.

| Caso | Pré-condição e input | Esperado na candidata | Observado e veredito na ROM | SHA / sessão / vídeo / trace |
|---|---|---|---|---|
| Acerto próximo | Gap 33 px, Alis neutra. Hayato mantém 1 até disparo e depois solta. | R03 no tick 9, um único contato. Alis cai a 88 de vida, recua 4 px e fica livre no 17. Hayato livre no 25. | Pendente | Ambas acima / — / — / — |
| Acerto no limite | Gap 37 px, ambos neutros. Mesmo comando e temporização. | Último pixel com interseção nos limites semiabertos. Mesmo contato, vida e reação. | Pendente | Ambas acima / — / — / — |
| Erro e punição | Gap 38 px. Mesmo corte. Alis começa a segurar 1 no tick 11. | Erro ao fim do tick 10, vida de Alis intacta. A estocada passa à fase ativa nos ticks 21 e 23, respectivamente. Se alcançar, Hayato passa a 90 e interrompe a recuperação. | Pendente | Ambas acima / — / — / — |
| Defesa | Gap 33 px. Alis aplica trás relativo no tick 9. | O probe registra o input de trás no contato, guarda sem chip, recuo 3 px, Alis livre no 12. | Pendente | Ambas acima / — / — / — |
| Contra após defesa | Mesmo caso de defesa. Alis começa 1 no tick 12 e mantém até disparo. | Contato no tick 22 com 6 leituras e no 24 com 8. Primeiro tick livre de Hayato no 30 ou 32 após o hit. | Confirmado em ambas. Corte bloqueado no 9, sem chip, recuo de 3 px e Alis livre no 12. A estocada tira 10 de Hayato. | [Comparação](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/comparison.json) · [Trace 6](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/6-guard_counter.json) · [Trace 8](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/8-guard_counter.json) |
| Face, P1/P2 e canto | Repita com lados e controles trocados. Ponha Alis no limite X=63 ou X=192 e mantenha o gap antes do corte. | Recuo limita na parede, caixa espelhada, SAT e prioridade iguais por identidade. A lâmina, a mão e os corpos continuam legíveis. | Pendente | Ambas acima / — / — / — |
| R03 simultâneo | Atrase o início da pressão de Alis em 4 ou 7 ticks frente à de Hayato. Posicione ambos fora do alcance para não antecipar interrupção. | Estocada ou preparação, respectivamente, cruza R03. A publicação usa IDs válidos, mantém a lâmina por BG e fica dentro de oito sprites por linha nas duas faces. | Cruzamentos alcançados em C nativo. Arranjo verificado estaticamente. Execução na ROM pendente. | Ambas acima / — / — / — |

**Resultados fora da ROM.** Passaram 40 casos com caixas sintéticas
e quatro cruzamentos simultâneos na compilação nativa de `duel_rules.c`.
O serializador de 74 bytes e o leitor MFD1 passaram três testes de bancada,
incluindo pedido, residência, apresentação, pose usada no contato e
rejeição de amostra incompleta. Em sessão privada pausada, ler MFD1 em
`0xC770` com `tools/duel_probe.py --session ID --address 0xC770
--rom-sha256 SHA`. O registro lê o relógio lógico e os dados por controle.
O frame VDP vem da ponte. Stepping serve para fronteiras e o SMRT em
`0xC7E0` serve para a medição contínua.

[Executor de casos](../tools/replay_duel_scene02.py) recebe `--session`,
`--rom-sha256`, `--hold 6|8`, `--case` e `--out`. Usar sessão nova
por caso, conferir a guarda inicial e fechar por ID. O executor conserva
os bytes lidos se uma fronteira ou resultado falhar. No Windows, o
[executor WSL](../tools/compare_duel_pilots_wsl.sh) prepara o display
e o áudio privados para o comparativo.

[Layout fixo e regressões](../out/diagnostics/duel_execution_20261119/resident-layouts-hayato-priority.json)
· [Fonte, arrays C, mapas e ROM](../out/diagnostics/duel_execution_20261119/asset-symbol-rom-verified.json)
· [896 comparações dos tiles emitidos](../out/diagnostics/duel_execution_20261119/emitted-raster-audit.json)
· [Recorte 256×192 R03 × estocada em raster estático](../out/diagnostics/duel_execution_20261119/R03-x-estocada-cena02-raster.png)
· [Plano de VRAM](../out/diagnostics/duel_execution_20261119/vram-plan-audit.json)
· [Corredor da ROM de 6](../out/logs/scene02_hold6_20261119_b02-probe-corridor.json)
· [Corredor da ROM de 8](../out/logs/scene02_hold8_20261119_b01-probe-corridor.json)
· [Vídeo histórico do corte isolado](../out/diagnostics/hayato_short_cut_v2/timing_only_v7/performance/b346785d4d914ba299e5325b67419b4a/hayato_cut_realtime.mp4)

No recorte estático, a passada larga de Alis ainda aparece, mas a prioridade
de Hayato e a sobreposição junto ao corte escondem parte do escudo e a ponta
da estocada. A guarda foi reutilizada em deslocamento e reações nesta
candidata. O julgamento de peso, continuidade e reação precisa do duelo
em reprodução normal.

Faltam os demais casos da matriz, vídeo contínuo do duelo, WAV, pior
VBlank e duas janelas de FPS funcional por variante. O Debian WSL usou
Java e ECJ, com Xvfb, Bubblewrap, FFmpeg e PulseAudio. Os recibos b13
registram o SHA e o fechamento de cada sessão.
[Fechamento 6](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/6-closed-session.json)
· [Fechamento 8](../out/diagnostics/repertoire_20261119/pilot-comparison-b13/8-closed-session.json).
· [Metadados e SHA do pacote JDK](../out/diagnostics/duel_execution_20261119/wsl-jdk-package-metadata.txt)
· [Recibo da cópia local verificada](../out/diagnostics/duel_execution_20261119/recovery-receipt.json).
