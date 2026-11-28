# Alis × Hayato · comandos e provas da primeira família

## Round contínuo b11-r2

Captura da sessão `de180cf34ed04e0485e837df32434594` no Emulicious com a ROM de seis leituras, SHA `f76fe86f5b3d874a7317c7727f350aa8e750af7a1dba9d85b8d71722c3a126b7`. O vídeo preserva o tempo real registrado dos 846 quadros até o fim do round. Dura 32,579 s e inclui áudio do monitor privado da sessão. Os oito normais e os dois especiais acertaram e a cena chegou ao KO. As duas janelas contínuas mediram 15,1878595 e 20,5018315 atualizações/s em tempo real. A lógica nos mesmos trechos mediu 40,1135720 e 42,8019596 atualizações/s nominais NTSC. O piso de 58 segue reprovado. [ROM](../out/candidates/scene02_repertoire_hold6_20261119_b11_r2/rom/master_of_fighters.sms) · [Vídeo](../out/diagnostics/repertoire_20261119/scene02-actions-continuous6-b11-r2-v2/6-continuous/round-continuo.mp4) · [Recibo](../out/diagnostics/repertoire_20261119/scene02-actions-continuous6-b11-r2-v2/6-continuous/round-continuo.json).

| Tempo (s) | Lutador | Ação | Resultado observado |
|---:|---|---|---|
| 1,34 | Hayato | Recuo | 111 → 79 px. Exibiu 33–36. |
| 3,24 | Alis | Recuo | 144 → 176 px. Exibiu 41–44. |
| 5,01 | Hayato | Avanço | 79 → 111 px. Exibiu 29–32. |
| 6,61 | Alis | Avanço | 176 → 144 px. Exibiu 37–40. |
| 9,13 | Hayato | Soco da guarda | Alis 100 → 94. Pose 8 pedida, residente e exibida. |
| 10,81 | Alis | Soco de guarda | Hayato 100 → 94. Pose 21 exibida. |
| 12,56 | Hayato | Corte curto | Alis 94 → 82. Pose 3 exibida. |
| 14,57 | Alis | Estocada forte | Hayato 94 → 84. Pose 18 exibida. |
| 15,92 | Hayato | Chute de sondagem | Alis 82 → 74. Pose 11 exibida. |
| 17,33 | Alis | Chute de distância | Hayato 84 → 76. Pose 24 exibida. |
| 19,17 | Hayato | Chute de giro | Alis 74 → 61. Pose 14 exibida. |
| 20,97 | Alis | Chute de avanço | Hayato 76 → 64. Pose 27 exibida. |
| 22,67 | Hayato | Saque em passada | Alis 61 → 45. Pose 46 exibida. |
| 24,23 | Alis | Passo de escudo | Hayato 64 → 51. Pose 49 exibida. |
| 30,75 | Hayato | KO com corte curto | Alis 9 → 0. Pose 3 exibida. |

O round quadro a quadro do mesmo SHA confirmou o soco e a marcha. Nesse outro roteiro, o Saque de Hayato ainda mostrou a pose 45 no contato da pose 46 no VDP 674. A cena perdeu 192 épocas de VBlank, com zero envios encerrados na área ativa. [Trace por quadro](../out/diagnostics/repertoire_20261119/scene02-actions-qa6-b11-r2/6-round/round-trace.json).

**Atualização b08.** Os oito normais em pé foram integrados e acertaram no round de seis leituras até o KO. A cadência sob carga e a apresentação de todas as poses continuam reprovadas. [ROM b08](../out/candidates/scene02_repertoire_hold6_20261119_b08/rom/master_of_fighters.sms) · [Vídeo do round](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b08/6-round/round-completo.mp4) · [Decisão da família](decisions/alis-hayato-standing-normals_owner_20261119.json) · [Prova de contra-ataque do piloto](scene02_hayato_alis_qa.md).

## Regressão do primeiro soco de Hayato

O toque foi solto fora da janela de pressão longa. Após o impacto, os pivôs estão em x=116 e x=148 nas duas sessões. A b08 usa a pose de impacto para a colisão e reduz a vida no tick correto. A primeira divergência está antes da publicação: no quadro 1458, os tiles da pose 8 ainda estão incompletos. No 1459 eles ficam residentes, e o envio especulativo ocupa parte do orçamento que permitiria publicá-los.

| ROM | Tick lógico | Quadro VDP | Vida de Alis | Pose pedida | Pose residente | Pose apresentada |
|---|---:|---:|---|---:|---:|---:|
| b08, 6 leituras | 1384 | 1458 | 100 → 94 | 8 | 255 (incompleta) | 7 |
| b09, 6 leituras | 88 | 163 | 100 → 94 | 8 | 8 | 8 |

A b09 limita a especulação quando existe orçamento para publicar a pose atual e permite adiantar até 12 tiles nas fases de preparação. O caso `--impact-only` congela a geometria e o dano do teste e exige pose 8 no tick de contato. Foram medidas 55,0805015 atualizações por segundo nominal nesse recorte, com um atraso de apresentação na recuperação e zero envios concluídos na área ativa. [Vídeo b09](../out/diagnostics/repertoire_20261119/scene02-impact-qa6-b09/6-round/impacto-soco.mp4) · [Trace b09](../out/diagnostics/repertoire_20261119/scene02-impact-qa6-b09/6-round/round-trace.json).

O [framebuffer imediatamente após o selo da sonda](../out/diagnostics/repertoire_20261119/soco-hayato-b08-b09-primeiro-frame.png) mostra a b08 à esquerda, amostra de vídeo 42, e a b09 à direita, amostra 43. O golpe aparece na imagem da b09. Alis está ausente em ambos os quadros e na [janela adjacente de sete quadros](../out/diagnostics/repertoire_20261119/soco-hayato-b08-b09-janela.png). A pose registrada pela sonda, mesmo residente e publicada no código, não comprova a composição completa do duelo.

## Marcha e especiais em ensaio

A aprovação de Saque em passada e Passo de escudo está registrada no [recibo de decisão](decisions/scene02-first-specials_owner-trial_20261119.json). O comando é baixo, depois frente + 1 em até oito leituras. O especial consome a nova pressão de 1 antes do normal. A marcha seleciona a pose pela distância real percorrida, com quatro pixels por pose e quatro poses por direção. Os [comandos do duelo](scene02-comandos.md) incluem as duas sensibilidades preservadas.

## Índice do round de diagnóstico b10

ROM de seis leituras, SHA `57198fcbbf09be9a93afb820c7c4ba86de260b2d26ed7840f5b14efbfe209cb0`, sessão `1f3e8d50495342f5a6a14c376a75add3`. Tempos do framebuffer gravado por quadros, em segundos a partir do começo do vídeo. Os IDs e a vida são observações da sonda do jogo. [ROM](../out/candidates/scene02_repertoire_hold6_20261119_b10/rom/master_of_fighters.sms) · [Vídeo](../out/diagnostics/repertoire_20261119/scene02-actions-qa6-b10/6-round/round-completo.mp4) · [Trace](../out/diagnostics/repertoire_20261119/scene02-actions-qa6-b10/6-round/round-trace.json).

| Tempo (s) | Lutador | Ação | Comando | Situação e resultado |
|---:|---|---|---|---|
| 0,37–1,47 | Hayato | Recuo | Trás | Percurso livre de 111 a 79 px. Apresentadas 33 e 35 de 33–36. |
| 1,49–2,59 | Alis | Recuo | Trás | Percurso livre de 144 a 176 px. Apresentadas 41–44. |
| 2,60–3,70 | Hayato | Avanço | Frente | Percurso livre de 79 a 111 px. Apresentadas 30 e 31 de 29–32. |
| 3,72–4,81 | Alis | Avanço | Frente | Percurso livre de 176 a 144 px. Apresentadas 37–40. |
| 5,31 | Hayato | Soco da guarda | Toque em 1 | Acerto. Vida de Alis 100 → 94. Pediu 8 e publicou 7. |
| 5,89 | Alis | Soco de guarda | Toque em 1 | Acerto. Vida de Hayato 100 → 94. Pediu e publicou 21. |
| 6,68 | Hayato | Corte curto | Segurar 1 | Acerto. Vida de Alis 94 → 82. Pediu e publicou R03 (3). |
| 7,51 | Alis | Estocada forte | Segurar 1 | Acerto. Vida de Hayato 94 → 84. Pediu e publicou 18. |
| 8,19 | Hayato | Chute de sondagem | Toque em 2 | Acerto. Vida de Alis 82 → 74. Pediu e publicou 11. |
| 8,83 | Alis | Chute de distância | Toque em 2 | Acerto. Vida de Hayato 84 → 76. Pediu e publicou 24. |
| 9,71 | Hayato | Chute de giro | Segurar 2 | Acerto. Vida de Alis 74 → 61. Pediu e publicou 14. |
| 10,63 | Alis | Chute de avanço | Segurar 2 | Acerto. Vida de Hayato 76 → 64. Pediu e publicou 27. |
| 11,58 | Hayato | Saque em passada | Baixo, depois frente + 1 | Acerto. Vida de Alis 61 → 45. Pediu 46 e publicou 45. |
| 12,30 | Alis | Passo de escudo | Baixo, depois frente + 1 | Acerto. Vida de Hayato 64 → 51. Pediu e publicou 49. |
| 15,85 | Hayato | KO com corte curto | Segurar 1 | Quarto corte após os especiais. Vida de Alis 9 → 0. |

Primeiro desvio da marcha de Hayato no quadro VDP 146, tick lógico 75. Trás já foi consumido, o pivô passa a x=110, a pose 33 é pedida e ainda não está residente. A imagem segue com a pose lógica publicada 0. O primeiro soco volta a atrasar no quadro 438, tick 224. No primeiro Saque o atraso ocorre no quadro 814, tick 481. O round mede 39,2886856 atualizações/s nominais, 345 épocas de VBlank perdidas, 112 apresentações atrasadas e zero términos de envio na área ativa. O maior VCounter registrado foi 252. Defesa, bordas de alcance, punição e a geometria nas faces e controles invertidos ficam pendentes nesse SHA. [Recibo completo](../out/diagnostics/repertoire_20261119/scene02-actions-qa6-b10/6-round/round-completo.json).

Em dois trechos NTSC do trace quadro a quadro, medimos 41,1040306 atualizações/s nos normais (VDP 438–559) e 44,3126170 nos especiais (VDP 814–933). A dispersão foi de 3,2085864. Ambos ficam abaixo do piso de 58. A SAT lida diretamente no quadro de abertura contém 47 sprites com padrões preenchidos e pico de 7/linha. O limite calculado do plano é 58 na SAT e 8/linha. Falta medir o pico durante todo o round. [Trechos de cadência](../out/diagnostics/repertoire_20261119/scene02-b10-cadencia-vdp.json) · [SAT de abertura](../out/diagnostics/repertoire_20261119/scene02-actions-continuous6-b10/6-continuous/boot-sat.json) · [Amostras dos dois lutadores no framebuffer](../out/diagnostics/repertoire_20261119/scene02-b10-amostras-visuais.png).

A captura contínua com áudio foi interrompida pelo limite de tempo da automação. A sessão privada fechou e a captura de diagnóstico acima preserva o round inteiro em vídeo silencioso de 16,671 s. [Recibo da tentativa contínua](../out/diagnostics/repertoire_20261119/scene02-actions-continuous6-b10/comparison.json).

## Comandos em pé

Frente aponta para o rival e trás aponta para longe dele. Inverta as
direções quando os lados trocarem. Os normais abaixo usam o mesmo botão
em ambas as faces, em solo e com o lutador livre. Toque sai na soltura
antes do limiar; pressão sustenta o botão até o disparo e exige soltura
para rearmar. O piloto compara 6 e 8 leituras no forte de 1. Usar 6 e 8
nos testes de outros fortes serve à comparação de bancada; a calibração
de cada um permanece na própria ficha. Os normais da família não gastam
barra.

| ID | Personagem e golpe | Entrada | Objetivo, gesto e contrajogo |
|---|---|---|---|
| `hayato/pe_1_curto` | Hayato · Soco da guarda | Toque em 1 | Soco médio curto. Soltar o ombro da mão livre na entrada e voltar com a katana junto ao corpo. No erro, alcance inferior ao da lâmina dá espaço ao rival. |
| `hayato/pe_1_longo` | Hayato · Corte curto | Segurar 1 | Normal médio para controlar o espaço. Manter R01–R06, o apoio, a trajetória e 8/1/2/7/2/5. Ativo [9,11), volta livre no 25. Punir erro ou atraso na recuperação após defesa. |
| `hayato/pe_2_curto` | Hayato · Chute de sondagem | Toque em 2 | Médio de distância. Estender o pé dianteiro com o pé traseiro assentado. O rival pode sair do alcance e punir a perna exposta. |
| `hayato/pe_2_longo` | Hayato · Chute de giro | Segurar 2 | Médio comprometido. Mostrar a rotação primeiro no apoio e no quadril; o hakama acompanha e volta à base. A recuperação precisa aceitar punição a curta distância. |
| `alis_landale/pe_1_curto` | Alis · Soco de guarda | Toque em 1 | Médio curto. Punho e borda do escudo avançam juntos; a mão da espada continua legível. A defesa de perto pode gerar resposta. |
| `alis_landale/pe_1_longo` | Alis · Estocada forte | Segurar 1 | Médio de resposta. Registrar sola, escudo e projeção da ponta no mesmo quadro; conferir a sobreposição com Hayato. Ativo [5,7), volta livre no 18. |
| `alis_landale/pe_2_curto` | Alis · Chute de distância | Toque em 2 | Médio de sondagem. Apoio no pé traseiro, bota dianteira abre distância e escudo lê à frente do tronco. Testar resposta à extensão. |
| `alis_landale/pe_2_longo` | Alis · Chute de avanço | Segurar 2 | Médio comprometido. Transferir o peso para a frente, estender a bota sem cruzar a arma e recolher à guarda. Conferir a distância que sobra para punir após bloqueio. |

Fora dos normais de pé, cima e diagonais iniciam saltos no ensaio de
movimento. Trás após decolar assume guarda aérea quando livre. Baixo +
trás guarda abaixado e baixo puro é o contexto de teste da provocação.
Frente, neutro, frente dentro da janela de oito leituras de bancada inicia
dash, com corrida se frente permanecer. Trás, neutro, trás inicia
recuo rápido. São comportamentos exercitados fora da ROM do repertório.

## Índice de observação por ação

Por linha, repetir acerto próximo e limite, erro um pixel além, guarda
em pé com trás no primeiro tick ativo, recuperação e punição. Espelhar
face e P1/P2 e repetir no canto. Para os dois fortes de 1, coletar nos dois
SHAs da matriz original antes de promover uma sensibilidade.

**Primeiro acerto de cada normal na b08.** ROM `47a65c0988a0ac8a235b1c417df4b3eb4746d542ad595c3d3a3cc38df27011d4`, sessão `a321e6f5722b4252b42bffd057ee144e`. Tempo aproximado no [vídeo por avanço de quadro](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b08/6-round/round-completo.mp4), calculado a partir do VDP inicial e da taxa nominal do arquivo. A linha identifica o contato no [traço](../out/diagnostics/repertoire_20261119/scene02-repertoire-qa6-b08/6-round/round-trace.json); as duas últimas colunas permitem conferir dano e atraso visual separadamente.

| Ação | Tick lógico / quadro VDP | Instante | Vida do defensor | Pose pedida / apresentada |
|---|---:|---:|---:|---:|
| `hayato/pe_1_curto` | 1384 / 1458 | 0,70 s | 100 → 94 | 8 / 7 |
| `alis_landale/pe_1_curto` | 1408 / 1486 | 1,17 s | 100 → 94 | 21 / 20 |
| `hayato/pe_1_longo` | 1440 / 1526 | 1,84 s | 94 → 82 | 3 / 2 |
| `alis_landale/pe_1_longo` | 1474 / 1568 | 2,54 s | 94 → 84 | 18 / 18 |
| `hayato/pe_2_curto` | 1502 / 1600 | 3,07 s | 82 → 74 | 11 / 10 |
| `alis_landale/pe_2_curto` | 1529 / 1632 | 3,60 s | 84 → 76 | 24 / 24 |
| `hayato/pe_2_longo` | 1564 / 1672 | 4,27 s | 74 → 61 | 14 / 14 |
| `alis_landale/pe_2_longo` | 1604 / 1718 | 5,04 s | 76 → 64 | 27 / 27 |

O round contém 14 contatos com queda de vida e termina em 64 × 0. Quatro dos oito primeiros contatos usaram uma pose apresentada diferente da pedida. O roteiro aproxima os jogadores e alterna os golpes; não exercita deliberadamente guarda, punição no erro, controles invertidos nem caminhada animada para trás. Para esses casos manter resultado próprio, SHA e sessão. Para comparar comando de 6 e 8, conservar o [par b05](../out/diagnostics/repertoire_20261119/scene02-repertoire-b05-hold-comparison.json).

### Diagnóstico anterior à integração

Os seis golpes novos têm 18 poses laterais provisórias. Mesmo com liberdade
de alinhamento vertical, 63 dos 81 cruzamentos precisam de mais de oito
sprites numa linha para preservar as duas silhuetas completas. O pico é 13.
A simulação que move células
para o fundo, preservando a paleta, chega a 21 células do mapa na formação
de 33 px do piloto. O delineamento atual da estocada reserva sete.
Faltam uma composição que caiba no orçamento de VBlank, as caixas sobre
as poses em ambas as faces e a ligação aos IDs de apresentação. No corte
forte aprovado, conservar os 25 ticks e o arco original como controle.
[Medição](../out/diagnostics/repertoire_20261119/standing-art-b05/staging-report.json)
· [Limite inferior por linha](../out/diagnostics/repertoire_20261119/standing-art-b05/sat-scanline-lower-bound.json)
· [Fontes das poses](../data/source_art/sprite_studies/scene02_standing_20261119/generated-art-receipt.json).

## O que a bancada mediu

| Lutador | Caminhar 32 px frente / trás | Dash | Corrida | Freio até poder agir | Recuo rápido |
|---|---:|---:|---:|---:|---:|
| Hayato | 32 / 43 ticks | 12,5 px em 5 ticks | 2,75 px/tick | 4 ticks | 7 px em 4 ticks |
| Alis | 37 / 37 ticks | 11,25 px em 5 ticks | 2,5 px/tick | 2 ticks | 8 px em 4 ticks |

Os perfis acima são hipóteses testadas com Q12.4 e faces espelhadas.
Em bancada, o recuo rápido volta a liberar o comando no primeiro tick
após seus quatro ticks. No pouso, trás sozinho entra em guarda alta
e baixo + trás entra em guarda abaixada na mesma leitura de chão.
Frente e trás simultâneos são neutros no ensaio. A guarda aérea bloqueia
o ataque marcado como defendível no ar, exceto antiaéreo terrestre.
A decisão sobre protagonismo, aceleração e a sequência audiovisual
depende de replay em um binário.

O acorde estrito aceitou as duas bordas no mesmo tick. A tolerância
aceitou também 1→2 e 2→1 em leituras adjacentes. Um toque isolado em 2
saiu na primeira soltura em ambos. O teste excluiu baixo com lateral,
pressão no ar, bloqueio de estado e reativação na soltura parcial.
O comando alternativo `baixo, baixo, 1+2` fica em reserva até surgir
conflito com controle físico.

[Movimento](../out/diagnostics/repertoire_20261119/test-motion.txt)
· [Falha reproduzida antes da correção do pouso](../out/diagnostics/repertoire_20261119/test-motion-before-landing-fix.txt)
· [Comparação de input](../out/diagnostics/repertoire_20261119/test-commands.txt)
· [Normais em pé](../out/diagnostics/repertoire_20261119/test-standing.txt)
· [Regressão do piloto em C](../out/diagnostics/repertoire_20261119/test-rules.txt)
· [Compilação dos três objetos Z80](../out/diagnostics/repertoire_20261119/compile-z80-objects.txt).

## Histórico do bloqueio de ambiente antes das sessões b03–b08

[Tentativa com 6 leituras](../out/diagnostics/repertoire_20261119/scene02_hold6_20261119_b02-emulicious-start.txt)
e [tentativa com 8](../out/diagnostics/repertoire_20261119/scene02_hold8_20261119_b01-emulicious-start.txt)
retornaram `FAIL_AMBIENTE` em `pactl`. As sessões posteriores produziram os rounds acima. O vídeo b08 foi capturado sem áudio. O plano anterior identifica a dependência
manual de 83.187.032 bytes e seu SHA.
[Plano e dependência](scene02_hayato_alis_qa.md).
