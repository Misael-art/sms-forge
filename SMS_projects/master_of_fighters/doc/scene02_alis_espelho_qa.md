# Cena 02 · Alis × Alis

O controle histórico é Hayato × Alis na b32, SHA-256
`201757c38220c8890bd1bb09b00f6b1fad2a0ace4e5b92184578fe3cfb57e03e`.
O novo perfil entra pelo mesmo duelo local e usa dois controles com
estado independente. A tabela de ações e os tempos planejados estão
no [repertório](repertorio_alis_hayato.md#produção-do-espelho-de-alis).

## Primeiro ensaio jogável

[ROM b33-r3](../out/candidates/scene02_alis_mirror_b33_r3/rom/master_of_fighters.sms),
SHA-256 `e307ae2a68bbd303c15fcb92daa19ee39db39f2d233d6e281e1419f2a100f799`.
17 bancos, corredor de sondas com 333 bytes livres. As sessões
`2f2ea69b83964e358c994969d144fd8b` e
`17a8e6cd353e44178127e913e0ce6ddf` encerraram após a prova
por quadros e a gravação contínua, respectivamente.

| Eixo | Observação b33-r3 | Ação seguinte |
|---|---|---|
| Dois controles e trajes | A b33-r3 iniciou Alis nos dois controles. P1 e P2 acertaram em sequência e a vida mudou apenas no alvo. As entradas simultâneas moveram as duas atrizes. O rosa e o verde seguiram os controles após cruzar. | Repetir os mesmos casos com as posições registradas pelo centro do quadril. |
| Contato em pé | A espadada #22, o soco #19 e o chute curto #25 apareceram no tick do contato nos dois controles. O chute forte pediu #28 e ainda mostrava #27. Na gravação contínua, as duas ocorrências divergentes estão nos quadros 687 e 968. | Preparar a faixa P0 da fase ativa antes do contato. |
| Ataques abaixados | O P1 acertou os quatro, com #31, #34, #37 e #40 publicados. Hayato já não participa dessa medição. | Repetir no espelho corrigido e cobrir defesa, distância limite e P2 baixo. |
| Reação | A primeira espadada pediu a reação alta #62 no VDP 155. Ela apareceu no VDP 163, quatro ticks lógicos depois. | Preparar a reação provável no início do ataque e conservar a reação alta inicial no atlas. |
| Montagem | No boot, as duas silhuetas formaram um bloco estreito em X111/X144. O pivô herdado ficava ao lado do quadril. | Transladar as duas faces e suas caixas a partir do mesmo centro anatômico. |
| Runtime | 14 contatos reproduzidos na gravação contínua. A prova por quadros registrou sete fins de envio em área ativa e zero erros de composição sinalizados. As janelas nominais deram 32,18990348165537 e 38,45042701776706 FPS. | Limitar transferências junto da SAT e atualizar somente os trechos alterados em translação. Medir novamente. |

[Quadros de entrada](../out/diagnostics/alis_mirror_20261121/qa-b33-mixed/input.json) ·
[Trajes no boot e após virar](../out/diagnostics/alis_mirror_20261121/qa-b33-mixed/costumes.json) ·
[Replay bruto](../out/diagnostics/alis_mirror_20261121/qa-b33-mixed/continuous/round-continuo.mp4) ·
[Recibo contínuo](../out/diagnostics/alis_mirror_20261121/qa-b33-mixed/continuous/round-continuo.json).

## Segunda revisão · pivô anatômico, guarda e rastreio da queda

[ROM b34](../out/candidates/scene02_alis_mirror_b34/rom/master_of_fighters.sms),
SHA-256 `582eeba2ca1806e4d71638c739060b0918e3d848a52da37ffe628c86c0f700a6`.
Os pivôs móveis das duas faces foram deslocados 12 pixels para registrar
o quadril. As caixas ofensivas e as vulneráveis em nível baixo e no ar
acompanharam esse registro. A margem da arena passou a 43 px conforme
o alcance dos quadros do novo par. A trajetória vertical e a velocidade
livre do impulso diagonal continuam as da b32.

| Caso | Achado na b34 | Correção em ensaio na b35 |
|---|---|---|
| Espadada e soco em cache frio | O primeiro #22 de cada controle e um soco #19 de P2 ficaram com a preparação exibida no contato. A reação alta dos dois primeiros contatos entrou no tick do impacto. | Antecipar a pose ativa ainda durante a pressão do botão e manter a previsão de reação enquanto o golpe amadurece. |
| Chute forte em pé | Ambos exibiram #28 no contato, com preparação prévia da faixa P0. | Conservar o caso no roteiro de regressão. |
| Quatro ataques aéreos | As quatro entradas de P1 acertaram. O soco, a estocada e o chute curto pediram a fase ativa uma leitura antes de ela aparecer. O mergulho mostrou #52 no acerto e derrubou. | Dar duas leituras adicionais à preparação dessas coreografias e antecipar a fase ativa. |
| Guarda por postura | O soco aéreo foi defendido no VDP 666. A espadada contra guarda alta e a rasteira contra guarda baixa registraram defesa nos VDP 183 e 286 do teste terrestre. | Conferir as poses de impacto em vez de contar a vida preservada como prova visual. |
| Três giros e duas negações | P1, P2 e P1 junto à parede aplicaram 16 de dano por soltura. Fora de alcance e contra alvo aéreo deram erro. Na primeira soltura, a tela ainda mostrava a posição de guarda da atacante e parte da trilha da vítima ficou ausente. | Expor o alcance, a pega, o giro e a soltura nos ticks próprios de cada trilha. Antecipar a pose seguinte da vítima. |
| Cadência e VBlank | No roteiro misto, 11 de 14 contatos conferidos no framebuffer. Pico de 45 sprites nas amostras, oito por linha e três fins em área ativa. Os três principais casos de piora foram a troca no primeiro acerto, a pose no chão e a passagem para levantada. | Usar o envio de PNT já medido no renderizador da Cena 02 e atualizar apenas a faixa móvel da SAT. A otimização mantém os dois corpos, HUD e áudio reais. |

As janelas mistas da b34 deram 35,16127918765432 e
35,24867259077194 FPS funcionais pelo relógio do VDP. A gravação
contínua reproduziu os 14 contatos do roteiro misto. Os quatro
contatos aéreos e os três giros também foram reproduzidos em seus
replays brutos. O piso de 58 FPS continua pendente.

[Roteiro misto](../out/diagnostics/alis_mirror_20261121/qa-b34-mixed/continuous/round-continuo.json) ·
[Pixels do contato](../out/diagnostics/alis_mirror_20261121/qa-b34-mixed/contact-pixels.json) ·
[Ataques aéreos](../out/diagnostics/alis_mirror_20261121/qa-b34-air/input.json) ·
[Guarda terrestre](../out/diagnostics/alis_mirror_20261121/qa-b34-guard/input.json) ·
[Pegas, soltura e chão](../out/diagnostics/alis_mirror_20261121/qa-b34-throw/input.json).

## Terceira revisão · publicação e comandos na b35

[ROM b35](../out/candidates/scene02_alis_mirror_b35/rom/master_of_fighters.sms),
SHA-256 `3306ae230ba58d37a1365a56233c872f8930f1aa1988b0a48fc5a53b6ccdee78`.
O envio da faixa móvel da SAT e o envio consecutivo de entradas P0
reduziram os fins em área ativa. Os sete roteiros por leitura terminaram
com zero fins em área ativa, zero falhas de composição sinalizadas e
sessões fechadas. A maior distância entre publicações foi de quatro VDP
no roteiro do agarrão. O corredor de sondas ficou com 319 bytes livres.

- **Ritmo.** Roteiro misto de 36,646967040653806 e 36,95235843265925
  atualizações/s pelo VDP. Aéreo de 38,627884177986445 e
  31,459440287263963. Giro de 33,675591334654854 e
  35,45428984755144. O tempo de parede do giro também ficou abaixo do
  piso. O replay contínuo repetiu os quatro acertos aéreos, os três
  giros e 13 dos 14 contatos mistos.
- **Comando.** P1 com 1 e P2 com 2 dispararam toque após cinco leituras,
  forte na sexta leitura e o mesmo forte com sete. A nova pressão depois
  de soltar disparou cada entrada seguinte. O Passo de Escudo continuou
  acessível (VDP 573), com a preparação #54 ainda visível no acerto #55.
- **Defesa e KO.** A guarda em pé no VDP 183, a baixa no 285 e a aérea
  no 667 preservaram a vida do alvo e resolveram reações 3, 4 e 5.
  Sete giros levaram P2 ao KO no roteiro de reinício. O botão 1 de P2
  restaurou ambas as vidas a 100 e P1 voltou a andar.
- **Primeira divergência no giro.** O alcance #57 foi encoberto no
  primeiro erro de alcance. A primeira soltura de P1 publicou #60/#74
  no VDP 409. A soltura de P2 pediu #60/#74 no 555 e mostrou #59/#73.
  Para a próxima correção, preservar o pacote P0 da pose atual pendente
  e alternar prioridade de pré-carga entre os controles.
- **Troca simultânea.** Duas espadadas baixaram ambas as vidas para 90
  no VDP 182 e os chutes fortes baixaram para 78 no 267. Nas duas
  trocas a reação #62 substituiu as duas poses ativas na primeira
  publicação. A correção preserva o gesto ofensivo no contato e
  publica a reação de cada atriz no tick seguinte. O replay contínuo
  desse caso deixou escapar os eventos de contato da sonda, mesmo
  mostrando as transições de vida.

[Comandos no limiar](../out/diagnostics/alis_mirror_20261121/qa-b35-controls/input.json) ·
[Impactos terrestres](../out/diagnostics/alis_mirror_20261121/qa-b35-guard/input.json) ·
[KO e retomada](../out/diagnostics/alis_mirror_20261121/qa-b35-reset/input.json) ·
[Trocas no mesmo tick](../out/diagnostics/alis_mirror_20261121/qa-b35-simultaneous/input.json) ·
[Giro e queda no vídeo](../out/diagnostics/alis_mirror_20261121/qa-b35-throw/continuous/round-continuo.mp4).

O primeiro link da b36 gerou um segmento fixo de 32.397 bytes a partir
de `0x0200`, terminando em `0x808D` antes do inicializador. O conversor
rejeitou o cartucho por invadir a janela de bancos de arte iniciada
em `0x8000`. A revisão r2 seleciona na compilação do espelho apenas
as entradas usadas pelo perfil, incluindo o caminho local que resolve
fase e caixa no mesmo passo. Os alvos legados e os testes de host
continuam compilando suas entradas históricas.
[Mapa do link recusado](../out/candidates/scene02_alis_mirror_b36/obj/master_of_fighters.map).

## Quarta revisão · b36-r2

[ROM b36-r2](../out/candidates/scene02_alis_mirror_b36_r2/rom/master_of_fighters.sms),
SHA-256 `c1d2e85ce5bca265bbad6f7db8cfdd8b7f76f70305d58185de8159a16c11954f`.
O build local passou com 319 bytes livres no corredor de sondas e
`0x7C8D` como fim do segmento fixo. A b36-r2 preservou o toque e o forte
da espada em cache frio com #22 no primeiro acerto de ambos os controles.
Os doze golpes acertaram nos dois roteiros. A comparação contínua do
misto divergiu da ordem completa dos acertos por leitura.

| Caso | Primeiro quadro divergente ou prova | Ação do ciclo seguinte |
|---|---|---|
| Duas espadadas e dois chutes fortes | VDP 185, tick 92, as duas vidas passaram a 90. As Alis pediram #22, com #0 ainda visível. No VDP 271, ambas as vidas foram a 78, com #27 exibido e #28 residente. O replay contínuo repetiu os quatro contatos. | Dar o orçamento de padrões às poses pendentes antes de consumir o restante com previsão. No tick da troca simultânea, montar ambas a partir do pivô anterior ao recuo. |
| Guarda alta, baixa e aérea | O VDP 185 do roteiro de guarda resolveu bloqueio alto, com #21 e #0 visíveis. No VDP 291, #40 e #66 chegaram no contato de guarda baixa. O impacto aéreo resolveu #67 com #17 exibido. | Conservar na matriz a distinção entre vida preservada e pose de impacto visível. |
| Vítima abaixada | VDP 371, soco rente baixou P2 a 95, pediu #64 na vítima e mostrou #10. No VDP 462, a mesma rasteira defendida antes atingiu a guarda alta e derrubou. | Repetir essas duas alturas com prioridade visual do contato. |
| Giro | VDP 416 e 857, P1 expôs #60/#74 na soltura. VDP 569, P2 soltou com #59/#73 enquanto pedia #60/#74. Gap de 33 px e alvo no ar continuaram inelegíveis. | Favorecer o carregamento do par pendente durante a pega e reservar a troca de PNT/SAT para um lote compatível. |
| Cadência e prazo | O misto mediu 35,45428984755144 nas duas janelas pelo VDP. O aéreo mediu 37,45171462769519 e 30,46072789719209. No giro houve três publicações que terminaram em linha ativa. A pior, tick 320, saiu de 196 a 5 com cinco padrões, 115 bytes de SAT e 23 entradas de PNT. | Usar a carga real para variar o limite inicial, evitar acumular atualização de PNT e pacotes especulativos no mesmo VBlank e eliminar o laço de busca de cache gerado com acessos à pilha. |

O teste de regras em C exercitou os 12 normais nas duas faces, no
último pixel válido e no primeiro pixel inválido, num total de 48
condições de alcance. Também verificou dois arcos de 20 ticks, guarda,
zonas e dois papéis do giro. Esses casos medem a lógica local.

Na sessão `1264c299e8464fe6a1be7a03f7d87898`, cada controle repetiu
dois saltos após espadada com diagonal mantida. As quatro sequências
chegaram a Y66 e voltaram a Y144. Segurar 1 desde a decolagem até o
pouso preservou o rearme por soltura. No vídeo de reinício, sete
solturas zeraram a vida de P2, a segunda jogadora reiniciou com 1,
e as duas voltaram a 100.

[Fonte da revisão](../out/candidates/scene02_alis_mirror_b36_r2/mirror-source-b36-r2.json) ·
[Teste de regras](../out/diagnostics/alis_mirror_20261121/b36-host-rules.txt) ·
[Matriz por contato, sessão e SHA](../out/diagnostics/alis_mirror_20261121/matriz-b36.json) ·
[Saltos consecutivos](../out/diagnostics/alis_mirror_20261121/qa-b36-motion/input.json) ·
[Reinício em vídeo](../out/diagnostics/alis_mirror_20261121/qa-b36-reset/continuous/round-continuo.mp4) ·
[Vídeo da troca simultânea](../out/diagnostics/alis_mirror_20261121/qa-b36-simultaneous/continuous/round-continuo.mp4) ·
[Misto com os oito normais terrestres e trocas de lado](../out/diagnostics/alis_mirror_20261121/qa-b36-mixed/input.json) ·
[Quatro normais aéreos e guarda](../out/diagnostics/alis_mirror_20261121/qa-b36-air/input.json) ·
[Giro, quedas e canto](../out/diagnostics/alis_mirror_20261121/qa-b36-throw/input.json).

## Quinta revisão · b37

[ROM b37](../out/candidates/scene02_alis_mirror_b37/rom/master_of_fighters.sms),
SHA-256 `309999840297e72fee8fb5c4e36b54f6feaee6fc461797ea9a330d1bdadfd482`.
Nesta revisão, os 14 contatos mistos chegaram com as poses solicitadas
das duas Alis e tiveram os pixels confrontados com os bancos. A
gravação contínua reproduziu os 14. O teste aéreo repetiu quatro acertos
e a guarda contra escudo. Por leitura, as quatro poses ativas saíram no
contato. No vídeo contínuo, o chute de interceptação ainda exibiu #48
quando pediu #49. A falta de sincronia nas reações aéreas segue abaixo.

| Normal | Dano | Primeiro VDP do caso principal | Pose de ataque esperada / exibida | Reação pedida / exibida |
|---|---:|---|---|---|
| Soco de guarda | 6 | 542 P1 e 784 P2 | #19 / #19 | #62 / #62 |
| Estocada forte | 10 | 155 P1 e 203 P2 | #22 / #22 | #62 / #62 |
| Chute de distância | 8 | 664 P1 e 905 P2 | #25 / #25 | #63 / #63 |
| Chute de avanço | 12 | 734 P1 e 976 P2 | #28 / #28 | #62 / #62 |
| Soco rente | 5 | 1032 P1 | #31 / #31 | #63 / #63 |
| Estocada ascendente | 11 | 1142 P1 | #34 / #34 | #62 / #62 |
| Chute baixo curto | 6 | 1242 P1 | #37 / #37 | #63 / #63 |
| Rasteira lateral | 10 | 1354 P1 | #40 / #40 | #68 / #68 |
| Soco aéreo | 5 | 193 P1 | #43 / #43 | #62 / #62 |
| Estocada em descida | 11 | 305 P1 | #46 / #46 | #63 / #15 |
| Chute de interceptação | 7 | 400 P1 | #49 / #49 | #63 / #15 |
| Chute em mergulho | 12 | 514 P1 | #52 / #52 | #68 / #15 |

Os quadros acima partem dos replays por leitura. As gravações contínuas
têm relógio próprio. A matriz inclui a defesa e a retomada junto a
cada dano. A espadada dupla derrubou ambas as vidas a 90 no VDP 182
e ainda mostrou #21 no contato #22. Os chutes fortes simultâneos
publicaram #28 nos dois lados no VDP 268. Em preparação para a correção,
o primeiro caso deixou documentados os pacotes ativos que ainda não
estavam residentes. Os três giros, nos VDP 401, 544 e 825, publicaram
#60/#74 no contato em ambos os papéis e junto à parede. Cada soltura
tirou 16 de vida. Os dois erros continuaram preservando a vida.
Na primeira pega de P1, VDP 361, o par ainda mostrava #57/#0 e
solicitava #58/#71. A volta do chão também atrasou no centro. O
quadro deitado #69 de P2 foi pedido no VDP 421 e apareceu no 423,
durante o estado de chão.

O roteiro de P2 repetiu as quatro entradas abaixadas e as quatro
aéreas na sessão `81117c60c31c412cbe8ca1f9f63cc297`. Os oito
acertos tiveram a pose ativa no framebuffer por leitura. O replay
contínuo registrou as oito quedas de vida e sete sinais de contato.
Na estocada ascendente, o primeiro quadro amostrado com a vida já
reduzida mostrou #34 no quadro 168 do vídeo. A guarda alta e o
soco contra vítima abaixada resolveram os eventos esperados nos VDP
183 e 357 do roteiro de defesa, com as primeiras poses de impacto
ainda atrasadas. A guarda baixa exibiu #66 no VDP 289.

| Reação | Leitura na b37 | Primeira publicação verificada |
|---|---|---|
| Cabeça #62 | Espadada em pé | VDP 155 do misto |
| Abdômen #63 | Chute de distância em pé | VDP 664 do misto |
| Base baixa #64 | Soco rente contra vítima abaixada | VDP 361 da defesa, dois ticks após o contato |
| Impacto de guarda em pé #65 | Vida preservada, #65 pedida | Ausente no roteiro de defesa |
| Impacto de guarda baixa #66 | Vida preservada, #66 no contato | VDP 289 da defesa |
| Impacto de guarda aérea #67 | Vida preservada, #67 pedida | Ausente no roteiro aéreo |
| Queda #68 | Rasteira conecta e desarma o apoio | VDP 1354 do misto |
| Chão #69 | Após a primeira soltura central | VDP 423 do giro, dentro dos 18 ticks no chão |
| Levantada #70 | Retomada após o chão | VDP 450 do giro |

Os doze golpes também emitiram erro no primeiro pixel fora da caixa
ofensiva, alternando P1 e P2, sem reduzir nenhuma vida. A prova por
leitura está na sessão `62847b7ec2ad4573a814df2424312506`.
[Limites de alcance no emulador](../out/diagnostics/alis_mirror_20261121/qa-b37-edges/input.json).

O roteiro misto mediu 37,14219632498696 e 38,949783212803 FPS funcionais
pelo VDP, 36,943205327331974 e 38,979453968792505 no relógio de parede,
pico de 45 sprites com oito por linha, zero fins de envio em área ativa
e maior intervalo de quatro VDP. O giro passou de três fins em área
ativa a zero. A cadência funcional e a sincronização de todos os
impactos continuam abaixo do aceite.

As dez sessões de teste por leitura da b37 foram encerradas. O pico
das amostras de SAT no giro e no reinício foi de 50 sprites, com oito
por linha. No VDP 1158 do roteiro de KO e reinício, a criação do novo
round ocupou um intervalo de cinco VDP, o pior observado da candidata.
O perfil de publicação, desde a linha 196 a 227 nesse caso, ainda
terminou no VBlank. O script verificou o bloqueio de movimento no
KO, o novo comando de P2, a vida de ambas em 100 e a retomada de P1.
[Matriz b37 com sessões, caixas e retomada](../out/diagnostics/alis_mirror_20261121/matriz-b37.json) ·
[Trajes b37 no boot e após cruzar](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/costumes.json) ·
[Reinício b37 em vídeo](../out/diagnostics/alis_mirror_20261121/qa-b37-reset/continuous/round-continuo.mp4).

[Misto com cabeça, abdômen e rasteira](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/continuous/round-continuo.mp4) ·
[Pixels dos contatos do misto](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/contact-pixels.json) ·
[Quatro golpes aéreos](../out/diagnostics/alis_mirror_20261121/qa-b37-air/continuous/round-continuo.mp4) ·
[Normais baixos e aéreos de P2](../out/diagnostics/alis_mirror_20261121/qa-b37-reverse/input.json) ·
[Giro dos dois controles e canto](../out/diagnostics/alis_mirror_20261121/qa-b37-throw/continuous/round-continuo.mp4) ·
[PCM bruto do misto](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/continuous/round-continuo.pcm) ·
[Fonte arquivada](../out/candidates/scene02_alis_mirror_b37/mirror-source-b37.json).

| Momento | Vídeo | Posição aproximada |
|---|---|---|
| Espadada e reação da cabeça | Misto | 0,552 s |
| Chute de distância e reação do abdômen | Misto | 9,049 s |
| Chute de avanço | Misto | 10,216 s |
| Chute baixo curto | Misto | 18,702 s |
| Rasteira lateral e queda | Misto | 20,570 s |
| Chute de interceptação | Aéreo | 4,647 s |
| Chute em mergulho e queda | Aéreo | 6,549 s |
| Soltura do giro de P1, de P2 e no canto | Giro | 4,642 s, 7,024 s e 11,713 s |

O mesmo misto da b37 mostra a espada no quadro 34 do vídeo e o
primeiro impacto do escudo no 421. Os dois trechos do PCM isolado
apresentam picos distintos, em torno de 1.720 Hz na espada e 430 Hz no
escudo. O recorte analítico usa a janela de 25 ms a partir de 120 ms
após cada marcador visual. Essa diferença de tempo inclui a latência
do caminho de captura. A comparação de timbre está coberta, e a
calibração da latência do monitor privado permanece aberta.
[Cabeça](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/contact-p1-77.png) ·
[Abdômen](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/contact-p1-379.png) ·
[Espada em WAV](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/continuous/contato-estocada.wav) ·
[Escudo em WAV](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/continuous/contato-escudo.wav) ·
[Recibo da comparação de timbre](../out/diagnostics/alis_mirror_20261121/qa-b37-mixed/continuous/psg-materiais.json).

## Sexta revisão · b38

[ROM b38](../out/candidates/scene02_alis_mirror_b38/rom/master_of_fighters.sms),
SHA-256 `a062fcc0b5c363ce43adf83a6bbf6448b1ec2971caba5118332147260a6b1842`.
A carga de padrões a cada VBlank sem mudança de SAT ou PNT pode chegar
a 14 tiles, com oito no lote normal. O deslocamento de SAT usa uma
rotina de adição que conserva os mesmos destinos. A reação prevista
pode ser antecipada junto com o próximo quadro do arco ou recuo.

| Caso | Prova e diagnóstico |
|---|---|
| Giro nos dois sentidos | P1, voltada à direita, engatou a pega #58/#71 no VDP 382 a 32 px de P2. P2, voltada à esquerda, engatou o mesmo par no VDP 671. As três solturas publicaram #60/#74 nos VDP 422, 711 e 1048, incluindo P2 no canto. A tentativa a 33 px e o alvo aéreo preservaram a vida. |
| Reações aéreas | A estocada em descida publicou #63 na vítima no contato e o mergulho publicou #68. A interceptação pediu #63 com #15 exibido. A guarda pediu #67 no VDP 661 e exibiu no 663, um tick lógico depois. |
| Espadadas simultâneas | VDP 182, #22 já residente para ambas após carregar 12 padrões. A preparação #21 ficou na tela quando as vidas baixaram. A publicação das duas poses de ataque e das lâminas precisa da residência completa antes do contato. O ciclo seguinte adianta a previsão do forte em uma leitura, mantendo a sexta leitura como disparo do comando. |
| Reinício | O pior intervalo da b37 foi a reconstrução e validação do perfil na retomada. A revisão seguinte conserva o estado inicial validado e restaura essa cópia no reinício, com vida, posição, face e comandos limpos. |

A b38 repetiu os contatos no contínuo aéreo e do giro. O aéreo mediu
38,627884177986445 e 32,95750887237177 FPS pelo VDP. O giro mediu
34,45557745747957 e 32,45815267733583. Os casos de troca simultânea,
quatro ataques aéreos e giro tiveram zero fins de envio em área ativa.
O roteiro misto confirmou novamente as 14 exposições por leitura. No
contínuo, a sonda leu 12 sinais de contato e os dois controles chegaram
às mesmas vidas do teste por leitura, 54 e 22. As duas janelas mistas
mediram 37,14219632498696 e 39,449139407838935 FPS pelo VDP.

A vítima abaixada mostrou #64 no contato. A rasteira contra guarda
em pé mostrou #40/#68. O impacto alto de guarda continuou atrasado.
No primeiro ensaio de punição, o chute de resposta acertou no VDP 222,
quando a atacante já estava livre. A trajetória da resposta seguinte
mantém o avanço enquanto o segundo controle toca 2, para disputar a
janela antes da retomada da atacante.
[Giro e saída de ambos os lados](../out/diagnostics/alis_mirror_20261121/qa-b38-throw/input.json) ·
[Vídeo e PCM do giro](../out/diagnostics/alis_mirror_20261121/qa-b38-throw/continuous/round-continuo.json) ·
[Reações aéreas com registro nativo](../out/diagnostics/alis_mirror_20261121/qa-b38-air/contact-pixels.json) ·
[Matriz b38](../out/diagnostics/alis_mirror_20261121/matriz-b38.json) ·
[Primeiro ensaio de punição](../out/diagnostics/alis_mirror_20261121/qa-b38-punish/input.json) ·
[Auditoria de áudio b38](../out/diagnostics/alis_mirror_20261121/b38-audio-audit.json) ·
[Fonte da b38](../out/candidates/scene02_alis_mirror_b38/mirror-source-b38.json).

## Sétima revisão · b39

[ROM b39](../out/candidates/scene02_alis_mirror_b39/rom/master_of_fighters.sms),
SHA-256 `f978da58124869d303b384c6cb711fad552335e73d86c2a740205d4a421bb325`.
O build passou com 164 bytes livres no corredor de sondas. A validação
do perfil ocorre no boot, e o reinício copia os 141 bytes do estado
inicial validado. O botão forte continua disparando na sexta leitura.
O carregamento previsto começa uma leitura antes da b38 e a previsão
de impacto recebe a primeira vaga de antecipação do defensor.

Na sessão `d49623f65ea24d0c9a21975cb56fa1ff`, as duas espadadas
exibiram #22 no contato do VDP 182. As duas vidas foram a 90.
No VDP 268, os chutes simultâneos exibiram #28 e as vidas foram a 78.
Os dois pares tiveram correspondência em pixels e a sessão por
leitura registrou zero fins de envio em área ativa. Ambas as reações
#62 apareceram no tick seguinte a cada troca. A gravação contínua
repetiu os quatro contatos com as duas poses ativas. A sobreposição
dos rostos na estocada dupla continua perceptível em tamanho nativo.
A guarda alta bloqueou no VDP 182 do roteiro de defesa com #21/#0
enquanto pedia #22/#65. A reação #65 apareceu no VDP 186, dois ticks
depois. A guarda baixa, a reação em base baixa e a rasteira contra
guarda alta publicaram as poses no contato. No caso que segue
atrasado, a vítima começara a recuar dois ticks antes do impacto. A
mesma janela teve translação da SAT, preparação dos pés em recuo,
carregamento da reação e preparação da lâmina da atacante.
[Exposição simultânea b39](../out/diagnostics/alis_mirror_20261121/qa-b39-simultaneous/contact-pixels.json) ·
[Trocas simultâneas em vídeo](../out/diagnostics/alis_mirror_20261121/qa-b39-simultaneous/continuous/round-continuo.mp4) ·
[Roteiro de defesa b39](../out/diagnostics/alis_mirror_20261121/qa-b39-guard/input.json) ·
[Fonte da b39](../out/candidates/scene02_alis_mirror_b39/mirror-source-b39.json).

Na sessão aérea `4b1784e068f7422d8041c852413f055e`, os quatro normais
mostraram #43, #46, #49 e #52 no contato, com as respectivas reações
#62, #63, #63 e #68 verificadas em pixels. O bloqueio com #67 apareceu
no contato da guarda aérea e preservou a vida. A gravação contínua
repetiu os quatro acertos com as poses ativas e registrou o bloqueio.
As janelas nominais mediram 38,627884177986445 e
32,45815267733583 FPS. Essa carga ainda perde épocas de publicação.
O soco aéreo aparece em 2,241 s, a estocada em 4,908 s, o chute
de interceptação em 6,957 s e o mergulho em 9,246 s.
[Contatos aéreos b39](../out/diagnostics/alis_mirror_20261121/qa-b39-air/contact-pixels.json) ·
[Duelo aéreo b39 em tempo real](../out/diagnostics/alis_mirror_20261121/qa-b39-air/continuous/round-continuo.mp4).

O misto confirmou os 14 contatos no framebuffer, com pose ofensiva e
reação publicadas em todos eles. O contínuo registrou as 14 quedas de
vida e 13 sinais de contato. Na queda de vida que ficou sem o sinal
na amostragem, o primeiro quadro lido mostrou #31 no quadro 882 do
vídeo. As janelas NTSC deram 37,637425609320125 e 39,94849560287487
FPS pelo VDP, e 37,42084482556815 e 37,08325521996706 no relógio de
parede. A sessão por leitura mostrou zero fins de envio em área
ativa, zero falhas sinalizadas de composição e intervalo máximo
de quatro VDP.

No misto b39, a cabeça aparece na primeira espadada em 0,550 s.
O chute de distância e a reação de abdômen aparecem em 8,650 s.
O chute de avanço aparece em 9,798 s, o chute baixo curto em
17,966 s e a rasteira com queda em 19,857 s.
[Contato misto b39](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/contact-pixels.json) ·
[Misto b39 em tempo real](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/continuous/round-continuo.mp4) ·
[Misto b39 em PCM bruto](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/continuous/round-continuo.pcm).

O PCM desse misto teve 6,450094161958568% de atividade frente ao
piso de 5%. A janela de 25 ms de cada impacto voltou a mostrar
picos de 1.720 Hz na espada e 430 Hz no escudo.
[Espada b39](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/continuous/contato-estocada.wav) ·
[Escudo b39](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/continuous/contato-escudo.wav) ·
[Auditoria de timbre b39](../out/diagnostics/alis_mirror_20261121/qa-b39-mixed/continuous/psg-materiais.json) ·
[Atividade do áudio nas gravações completas](../out/diagnostics/alis_mirror_20261121/b39-audio-audit.json).

No giro b39, P1 agarrou voltada à direita a 32 px de distância e
P2 agarrou voltada à esquerda. As pegas mostraram #58/#71 nos VDP
380, 668 e 1003, incluindo P2 junto à parede. As solturas mostraram
#60/#74 nos VDP 420, 708 e 1043, com 16 de dano por execução. No
canto, os pivôs permaneceram em X43 e X67 durante a soltura. O erro
a 33 px e a tentativa contra alvo no ar conservaram as vidas.
As três solturas aparecem no vídeo em 6,817 s, 12,109 s e
18,385 s, seguidas de queda, chão e levantada.
[Giro b39 por leitura](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/input.json) ·
[Giro b39 no framebuffer](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/throw-exposures.json) ·
[Folha com os 15 quadros nativos do giro](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/giro-b39-exposicao-nativa.png) ·
[Giro b39 em tempo real](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/continuous/round-continuo.mp4).

As réguas identificam as marcas de pega a revisar. No quadro 381, a
mão ativa de P1 chega aproximadamente a (132, 113) e a mão da
vítima está perto de (140, 117), com o tronco em torno de (149, 122).
No quadro 669, a mão ativa de P2 está perto de (116, 113), a mão da
vítima em torno de (115, 117) e o tronco perto de (105, 121).
O primeiro caso ainda deixa espaço visível entre as mãos. As poses
presas compactas também precisam conservar o tamanho da cabeça em
relação à guarda.
[Régua de pega P1](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/giro-pega-p1-regua.png) ·
[Régua de pega P2](../out/diagnostics/alis_mirror_20261121/qa-b39-throw/giro-pega-p2-regua.png).

As doze defesas compatíveis foram conferidas com P2 junto à parede
direita. A sessão por leitura `7c7c88a42fe04dc4ab262fb5bcdf628c`
verificou os 12 pares de ataque e impacto com a vida de P2 em 100.
O contínuo registrou dez sinais de contato e as doze entradas no
estado de bloqueio. O primeiro quadro lido de cada entrada mostra a
pose ativa e o impacto de guarda. O roteiro de P2 fez os oito
contatos baixos e aéreos por leitura e repetiu as oito perdas de vida
com os quadros ativos no contínuo. O reinício após o KO em sete giros
custou quatro VDP do último quadro ao primeiro do round novo,
ante cinco na b37. O teste de movimento bloqueado e de volta do
controle de P1 passou. No tick 0 do novo round, as vidas e os pivôs
já estavam na condição inicial e P2 ainda exibia #69. A pose em pé
voltou no tick 3. A correção visual desse caso precisa reservar a
pose de boot da vítima enquanto ela permanece no estado de KO.
[Todos os bloqueios](../out/diagnostics/alis_mirror_20261121/qa-b39-guards_all/continuous/round-continuo.mp4) ·
[Oito contatos baixos e aéreos de P2](../out/diagnostics/alis_mirror_20261121/qa-b39-reverse/continuous/round-continuo.mp4) ·
[KO, reinício e retomada](../out/diagnostics/alis_mirror_20261121/qa-b39-reset/continuous/round-continuo.mp4).

O primeiro roteiro de punição acertou o chute de avanço ainda na
recuperação e atingiu a rasteira no tick em que a atacante já estava
livre. O roteiro focado repetiu a primeira janela e começou a
aproximação de P2 na exposição ativa da rasteira fora de alcance.
Na sessão `a3b3d7d4816e4f66ad5280f99f3ba4a0`, a resposta chegou
antes da retomada nos dois casos, nos VDP 218 e 329. A pose ofensiva
#25 foi pedida no contato, com #24 exibida. A punição de lógica está
demonstrada e a primeira exposição visual dessa resposta segue
aberta.
[Primeiro ensaio b39](../out/diagnostics/alis_mirror_20261121/qa-b39-punish/input.json) ·
[Punição antes da retomada b39](../out/diagnostics/alis_mirror_20261121/qa-b39-punish-r2/input.json).

A matriz final da b39 reúne 14 roteiros com as respectivas sessões
fechadas. Os dois controles registraram dano com os 12 normais.
Os 12 ataques também erraram no primeiro pixel fora do alcance sem
reduzir a vida. O Passo de Escudo entrou após a sequência de limiar
e soltura dos botões. Nas amostras de todos esses roteiros, o pico
foi de 47 sprites na SAT e oito por linha, com zero fins de envio em
área ativa. O intervalo máximo entre registros consecutivos da ROM foi
quatro VDP.

Os dois controles repetiram o salto após a espadada com frente ou
trás na diagonal. O ensaio no centro registrou ápice de 78 px,
20 ticks no ar e 6 px/tick no primeiro arco livre em cada uma das
quatro combinações. O segundo salto voltou a sair. O teste anterior
junto às bordas também repetiu as decolagens com o avanço horizontal
limitado pela arena.
[Matriz b39 por sessão, ação e reação](../out/diagnostics/alis_mirror_20261121/matriz-b39.json) ·
[Erros no primeiro pixel fora do alcance](../out/diagnostics/alis_mirror_20261121/qa-b39-edges/input.json) ·
[Limiar, soltura e Passo de Escudo](../out/diagnostics/alis_mirror_20261121/qa-b39-controls/input.json) ·
[Medição dos saltos livres](../out/diagnostics/alis_mirror_20261121/qa-b39-motion-open/flights.json) ·
[Saltos com espadada em vídeo](../out/diagnostics/alis_mirror_20261121/qa-b39-motion/continuous/round-continuo.mp4).

## Arte, físico e reprodução

O perfil usa o impulso da b32: ápice de 78 px, voo de 20 ticks e
passo diagonal de 6 px/tick quando o caminho está livre. O avanço
horizontal usa o resolvedor de separação e de cruzamento; o salto
vertical usa o mesmo arco. A nova pressão durante recuperação tem
armazenamento por controle. As imagens nativas de boot e troca
confirmam a prisão das cores aos controles e a saída do HUD da área
das silhuetas. Em tamanho nativo, a espadada aérea e a rasteira
têm alturas e perfis diferentes. Na soltura central do giro, a
vítima ainda se mistura ao contorno da atacante por alguns pixels.
Esse encontro, a visibilidade da guarda baixa em movimento e os
encaixes de mão e equipamento seguem abertos à revisão artística.
Na prancha do giro, a vítima presa aparece compacta em relação ao
idle. A redução uniforme viabilizou a faixa de quatro sprites por
atriz. A revisão de arte deve preservar a anatomia no recolhimento.

[Boot em tamanho nativo](../out/diagnostics/alis_mirror_20261121/qa-b35-mixed/boot.png) ·
[Trajes após a troca de lado](../out/diagnostics/alis_mirror_20261121/qa-b35-mixed/swapped.png) ·
[Rasteira e queda](../out/diagnostics/alis_mirror_20261121/qa-b35-mixed/contact-p1-842.png) ·
[Soltura central](../out/diagnostics/alis_mirror_20261121/qa-b35-throw/contact-p1-221.png).

As pranchas extraem os pixels dos pacotes convertidos e mostram as
trilhas lado a lado para inspeção. Os replays documentam a montagem
dessas trilhas durante o combate.
[Giro a 1×](../out/diagnostics/alis_mirror_20261121/giro-exposicao-1x.png) ·
[Giro a 2×](../out/diagnostics/alis_mirror_20261121/giro-exposicao-2x.png) ·
[Reações a 1×](../out/diagnostics/alis_mirror_20261121/reacoes-exposicao-1x.png) ·
[Reações a 2×](../out/diagnostics/alis_mirror_20261121/reacoes-exposicao-2x.png).

As fontes vêm do [estudo de arte](../data/source_art/sprite_studies/scene02_alis_mirror_20261121/source.md)
e do [plano de posturas preservado](../out/diagnostics/alis_20261121_posturas/staged-b25/postures-plan.json),
SHA-256 `2f5a66eb1dcd5b23736a5342cf427daec6c54fce2742c0c8c3282156b19177a0`.
O conversor confere cada pose de volta aos pixels autorais. São 76
poses, quatro combinações de face/traje, 304 pacotes em 17 bancos
e oito alinhamentos de fundo por pacote. O limite de 32 padrões por
slot comporta o pico de 30. A faixa P0 de cada atriz usa até 11
entradas, somente em poses no chão. O caminho de reprodução é
`tools/stage_alis_mirror.py` → `mirror_build.json` pelo wrapper →
`tools/replay_alis_mirror.py`. O replay confere os mesmos 17 bancos
no cartucho antes de abrir a sessão.

[Conversão, paleta e hashes de arte](../out/diagnostics/alis_mirror_20261121/complete-v3/repertoire-pages.json) ·
[Limites estáticos dos 304 pacotes](../out/diagnostics/alis_mirror_20261121/mirror-static-packet-audit.json) ·
[Manifesto do perfil](../out/diagnostics/alis_mirror_20261121/complete-v3/mirror_build.json).

O PCM isolado da b36-r2 foi preservado sem corte, em 44.100 Hz, mono,
PCM s16le. A forma alinhada do roteiro misto teve 6,8053749458170785%
de atividade e passou pelo piso de 5% de efeitos esparsos. O trecho
aéreo teve 4,932301740812379% e o do giro, 2,19941348973607%. Esses
trechos conservam o sinal e ficam abertos no gate de atividade. O
efeito autoral de escudo continua com ataque grave e ruído curto.
A lâmina usa um tom inicial mais alto e uma cauda tonal. A fonte é
o mesmo `duel_sfx.h` da b32. A direção sonora da espada de Phantasy
Star permanece para curadoria.

[Áudio bruto do misto](../out/diagnostics/alis_mirror_20261121/qa-b36-mixed/continuous/round-continuo.pcm) ·
[Misto alinhado para escuta](../out/diagnostics/alis_mirror_20261121/qa-b36-mixed/continuous/round-aligned.wav) ·
[Auditoria das capturas](../out/diagnostics/alis_mirror_20261121/b36-audio-audit.json) ·
[Manifesto dos efeitos autorais](../out/diagnostics/alis_20261121_marcha_e_sfx/psg/audio-manifest.json).

## b43 · Acionamento aéreo, queda e botão 2

[ROM b43](../out/candidates/scene02_alis_mirror_b43/rom/master_of_fighters.sms),
SHA-256 `fbf9d94dce222317c65a51cfbf9a9d40c9cb702910827615960bb7f985150591`.

| Relato da b39 | Correção na b43 | Evidência |
|---|---|---|
| A preparação aérea aguardava a intensidade e somava mais seis a nove ticks. A compressão eliminava pressões simultâneas ao salto. | Começar o gesto no toque em voo, reter a pressão durante a compressão, usar quatro leituras para a intensidade no ar e dois ticks internos antes da fase ativa. | Em P1/P2, a preparação da espada foi publicada na primeira leitura de 1, com os pés em Y=76. A lâmina acertou cinco ticks depois com os pés em Y=123 e caixa Y=95–106, antes da aterrissagem em Y=144. Cima + 2 entrou no ar em ambos os controles e teve fase ativa quatro ou seis ticks após a primeira leitura, conforme a intensidade. |
| O chute aéreo curto era encolhido para caber no limite de sprites. | Redesenhar as silhuetas de corpo inteiro, preservar as proporções em escala uniforme e registrar as caixas nas extremidades que realmente se movem. | Fase ativa da espada com 49 px de altura, pose neutra com 52 px. As poses aéreas mantêm o limite de quatro sprites por scanline por atriz. |
| A primeira pose do chão já levantava a cabeça. | Inserir o corpo estendido com cabeça apoiada. Usar a pose anterior durante três ticks de início da levantada. | Em ambos os controles o framebuffer registrou queda, corpo deitado, elevação da cabeça e apoio do joelho na sequência. |
| O botão 2 falhava para o jogador enquanto a injeção de portas da b39 passava. | Corrigir o lançador Linux com ligação explícita de direções e ataques do dispositivo virtual. | O JInput isolado recebeu B1, B2, ↓ + B2 e ↑ + B2 com máscaras `0x10`, `0x20`, `0x22` e `0x21`. A ROM executou os seis chutes por controle. Os oito chutes terrestres do roteiro e as duas espadadas aéreas tiveram contato e pose ativa no framebuffer. |

As janelas NTSC do roteiro de regressão mediram
52,43240047877327 e 48,93690711352171 FPS funcionais. Os dez contatos
repetiram no vídeo contínuo com PCM isolado. Foram zero envios encerrados
fora do VBlank na trilha da regressão, com pior intervalo de quatro quadros
VDP. O piso de 58 FPS mantém o aceite pendente. O controle físico do Steam
Deck ainda precisa de validação humana.

Com as duas atrizes no ar e o cache frio, houve quatro contatos e um
bloqueio por leitura na b43. A espadada expôs a fase ativa no acerto.
O golpe de escudo aos ticks 94 e 396 e os chutes aos ticks 234 e 302
ainda exibiam preparação. Nessa trilha, as janelas nominais mediram
38,627884177986445 e 33,95622126244364 FPS. A primeira tentativa de
aumentar o lote aéreo, b44, excedeu o banco fixo e parou na conversão.
A restauração do orçamento de oito padrões com a SAT conserva a margem
de envio para testar uma mudança de ordem de carregamento.
[Primeiros quadros divergentes](../out/diagnostics/alis_mirror_20261121/qa-b43-air-r2/contact-pixels.json) ·
[Falha de montagem b44](../out/candidates/scene02_alis_mirror_b44/logs_build.txt).

[Comandos](scene02-comandos.md#perfil-alis--alis) ·
[Entrada observada e caixas](../out/diagnostics/alis_mirror_20261121/qa-b43-retouch/input.json) ·
[Vídeo contínuo com som](../out/diagnostics/alis_mirror_20261121/qa-b43-retouch/continuous/round-continuo.mp4) ·
[Quadros do framebuffer](../out/diagnostics/alis_mirror_20261121/qa-b43-retouch/pose-frames.json) ·
[Porta A pelo JInput](../out/diagnostics/alis_mirror_20261121/complete-b40/deck-jinput.txt) ·
[Arquivo-fonte](../out/candidates/scene02_alis_mirror_b43/mirror-source-b43.json).

## b47 · Fase ativa com as duas Alis no ar

[ROM b47](../out/candidates/scene02_alis_mirror_b47/rom/master_of_fighters.sms),
SHA-256 `baca9cde8fa4edf93cd823a6c649c39c16234379af71823fdc5217817179d45a`.

A b45 também excedeu o banco fixo ao acrescentar a prioridade de
carregamento. A b47 compartilha as coordenadas, contagem e endereços
relativos dos quadros entre os trajes. A montagem confirmou os 308
quadros com os mesmos pixels da b43 e empacotou nove bancos por traje.
A preparação com ataque aéreo pede sua fase ativa antes de antecipar
outros desenhos. A janela com SAT conserva o limite de oito padrões.

| Ação | Tick | Pose apresentada | Prova |
|---|---:|---:|---|
| Soco aéreo | 94 | 43 | Acerto com escudo à frente |
| Espadada em descida | 162 | 46 | Acerto com lâmina visível |
| Chute de interceptação | 234 | 49 | Acerto com bota estendida |
| Chute em mergulho | 302 | 52 | Acerto com bota em diagonal |
| Soco aéreo contra guarda | 396 | 43 | Bloqueio com fase ativa visível |

Os cinco contatos foram encontrados no framebuffer e se repetiram no
vídeo contínuo. A reação da vítima ainda apresentou atraso em quatro
desses contatos. O roteiro registrou 42 sprites no pico observado,
oito por scanline, zero falhas e zero envios encerrados fora do VBlank.
O pior intervalo foi de três quadros VDP. As janelas NTSC mediram
38,311262176527535 e 33,73801519402458 FPS funcionais, abaixo do piso de 58.

Na regressão dos dois controles, a espadada mostrou #42 na primeira
leitura de 1 e #46 no contato cinco ticks depois. O corte atingiu
Y=95–106 com os pés da atacante em Y=123. A preparação ocorreu no tick 98
de P1 e no tick 823 de P2. Cada controle acionou os seis chutes, incluindo
o mergulho sustentado até depois do pouso, com uma única ação aérea.
Os quatro saltos com 2 mantiveram ápice de 78 px e 20 ticks de voo.
Os oito contatos terrestres de chute e os dois contatos da espadada
corresponderam aos pixels da fase ativa. A rasteira expôs queda #68,
corpo apoiado #69, cabeça erguendo #76 e apoio do joelho #70 nas duas
direções. A regressão por leitura registrou pico de 43 sprites, oito por
scanline, zero falhas e zero envios fora do VBlank.

O vídeo aéreo contém áudio isolado e passou o piso de atividade de
5% para a cena de efeitos. A trilha dos dois controles com todas as
esperas excedeu a capacidade de uma captura contínua, de 1.800 VDP.
A repetição complementar foi encerrada durante um backup concorrente
do host. As sessões respectivas foram fechadas e a trilha completa
por leitura foi preservada.

[Espadada, chutes e pouso nos dois controles](../out/diagnostics/alis_mirror_20261121/qa-b47-retouch/input.json) ·
[Quadros da espada e da queda](../out/diagnostics/alis_mirror_20261121/qa-b47-retouch/pose-frames.json) ·
[Matriz dos dois roteiros](../out/diagnostics/alis_mirror_20261121/matriz-b47.json) ·
[Contatos e pixels](../out/diagnostics/alis_mirror_20261121/qa-b47-air/contact-pixels.json) ·
[Vídeo com áudio](../out/diagnostics/alis_mirror_20261121/qa-b47-air/continuous/round-continuo.mp4) ·
[Dados do vídeo e PCM](../out/diagnostics/alis_mirror_20261121/qa-b47-air/continuous/round-continuo.json) ·
[Auditoria de áudio](../out/diagnostics/alis_mirror_20261121/qa-b47-air/continuous/audio-audit.txt) ·
[Corredor de sondas](../out/candidates/scene02_alis_mirror_b47/probe-corridor.json) ·
[Arquivo-fonte](../out/candidates/scene02_alis_mirror_b47/mirror-source-b47.json).

## b48 · Punho, tecido, contorno e repouso

[ROM b48](../out/candidates/scene02_alis_mirror_b48/rom/master_of_fighters.sms),
SHA-256 `90c77cf2e3cfe1c680ccf2c2399dcea4db2320c729a9c4f1000c60db41221772`.

A b47 já continha branco no bracelete e em amostras rosadas antes de o
VDP receber os padrões. A b48 encaminha o rosa para a rampa do tecido
e recupera o traço da fonte ao reduzir a imagem. Os dois trajes
continuam compartilhando a paleta física e diferem somente nos índices
de tecido. Os contatos do escudo e da espada receberam poses retocadas
com empunhaduras mais legíveis. O soco em pé recuperou seis pixels
dourados do bracelete em cada face e traje. A queda conserva a figura
inteira no piso, com 58 × 10 pixels e Y=143 junto à cabeça apoiada.

| Evento | Controle | Tick | Resultado observado |
|---|---|---:|---|
| Espadada no ar | P1 | 95 | Lâmina e punho da pose ativa no contato |
| Escudo no ar | P1 | 135 | Escudo projetado e fase ativa no contato |
| Soco de guarda | P2 | 173 | Bracelete dourado e traje verde no contato |
| Rasteira e queda | P1 e P2 | 209–236 | Queda, corpo no chão, cabeça erguendo e apoio do joelho |

A montagem incremental reassemblou a tabela de quadros com SDCC e
ligou os bancos com o conversor do SDK. A comparação verificou todos
os bytes de código anteriores, com mudanças limitadas aos descritores,
aos novos bancos e ao checksum. O corredor de sondas conservou 162 bytes
de folga. Um backup concorrente do host impediu a recompilação integral.

Os quatro contatos se repetiram no vídeo contínuo de 328 quadros. A
queda e a levantada apareceram em sequência nos quadros 257, 270, 305
e 311 do replay. A trilha por leitura registrou oito sprites por linha
no pico amostrado, zero falhas e zero fins de envio fora do VBlank. O
recorte ficou sem janelas válidas para julgar a cadência NTSC.

[Comparação de materiais](../out/diagnostics/alis_mirror_20261121/b48-art/material-check.json) ·
[Quadros do Emulicious](../out/diagnostics/alis_mirror_20261121/qa-b48-materials/material-framebuffer.png) ·
[Recibo dos quadros](../out/diagnostics/alis_mirror_20261121/qa-b48-materials/pose-frames.json) ·
[Vídeo contínuo](../out/diagnostics/alis_mirror_20261121/qa-b48-materials/continuous/round-continuo.mp4) ·
[Matriz de validação](../out/diagnostics/alis_mirror_20261121/matriz-b48.json) ·
[Recibo da relincagem](../out/candidates/scene02_alis_mirror_b48/asset-relink.json) ·
[Fontes da revisão](../out/candidates/scene02_alis_mirror_b48/mirror-source-b48-delta.json) ·
[Registro de curadoria](curation_candidates/2026-11-21_alis_punho_tecido_contorno.json).

## b49 · Escala das cinco poses

[ROM b49](../out/candidates/scene02_alis_mirror_b49/rom/master_of_fighters.sms),
SHA-256 `2458fdecfccce8a33f29b7843860886893b6c205d8f2eda4bb6028a8c556e9da`.

| Pose | b48 | b49 | Tick verificado em pixels |
|---|---:|---:|---:|
| Escudo no ar | 31 × 49 px | 34 × 53 px | 135 |
| Espada no ar | 26 × 50 px | 28 × 53 px | 95 |
| Queda | 32 × 27 px | 42 × 36 px | 209 |
| Repouso | 58 × 10 px | 63 × 11 px | 215 |
| Cabeça sobe | 52 × 17 px | 56 × 18 px | 233 |

A guarda mede 52 px de altura e serviu de régua para os contatos em
voo. O teto de 32 px de largura encolhia a figura inteira durante a
queda. A b49 empacota a diagonal maior com 16 sprites e pico de até
quatro por linha por atriz. O repouso e a primeira levantada mantêm a
linha de apoio Y=143. A comparação dos bancos confirmou o ajuste nas
duas faces e nos dois trajes e isolou o delta a 20 das 308 variantes.

Os quatro contatos da regressão se repetiram no vídeo contínuo. A
captura por leitura registrou pico de 44 sprites, oito por linha e
zero fins de envio fora do VBlank. A relincagem verificou o código
byte a byte com as duas ROMs anteriores. O backup concorrente
manteve a recompilação integral pendente. O roteiro curto ficou sem
janelas válidas para julgar a cadência de 58 FPS.

[Comparação em escala comum](../out/diagnostics/alis_mirror_20261121/staged-b49/proportion-comparison.png) ·
[Medidas por face e traje](../out/diagnostics/alis_mirror_20261121/staged-b49/proportion-check.json) ·
[Cinco poses no framebuffer](../out/diagnostics/alis_mirror_20261121/qa-b49-proportions/pose-frames.json) ·
[Vídeo contínuo](../out/diagnostics/alis_mirror_20261121/qa-b49-proportions/continuous/round-continuo.mp4) ·
[Matriz de validação](../out/diagnostics/alis_mirror_20261121/matriz-b49.json) ·
[Recibo da relincagem](../out/candidates/scene02_alis_mirror_b49/asset-relink.json) ·
[Fontes da revisão](../out/candidates/scene02_alis_mirror_b49/mirror-source-b49-delta.json).

## b49 · Botão de chute pelo lançador

O controle virtual passou a ser testado pelo Emulicious de jogo com a
b49 de SHA-256 `2458fdecfccce8a33f29b7843860886893b6c205d8f2eda4bb6028a8c556e9da`.
O perfil padrão filtrava o botão 2 quando o componente interno da janela
recebia foco. O lançador desativa esse filtro na sessão com o controle
virtual dedicado. O atalho local reconhece a extensão `.sms` e o
comando `run.sh` voltou a abrir diretamente como executável.

Na sessão privada, o encaminhamento do lançador passou pelo dispositivo
virtual, pelo JInput e pela porta A do Emulicious. A leitura da ROM
confirmou pressão, soltura e execução dos seis chutes e do escudo.
O botão 2 e a tecla **S** também executaram o chute após transferir o
foco para um componente interno da janela. A validação humana do
controle físico segue pendente. A ROM b49 conserva o mesmo SHA.
[Antes](../out/diagnostics/alis_mirror_20261121/deck-launch-b49/baseline.json) ·
[Depois](../out/diagnostics/alis_mirror_20261121/deck-launch-b49/launcher.json) ·
[Registro para curadoria](curation_candidates/2026-11-21_alis_golpes_aereos_e_chao.json).

## b52 · Chute forte, puxada e model sheet

A [ROM b52](../out/candidates/scene02_alis_mirror_b52/rom/master_of_fighters.sms)
tem SHA-256 `47c0a4027d39b1d45bfe48a53ec819fb6ac3d046243c702fa848b3edd3ca8fe9`.
O build integral passou pelo wrapper e o corredor de sondas tem
166 bytes de folga.

| Caso | Diagnóstico e correção | Observação na b52 |
|---|---|---|
| Chute aéreo forte | A b49 marcava queda. O teste anterior só exigia ação e acerto. | P1 e P2 causaram 12 ticks de impacto no ar. O alvo em pé recuou 7 px e retomou o controle. A guarda aérea manteve a vida. O leve conservou 8 ticks. |
| Escala da pega | A atacante da b49 media 55–60 px e a rival, 25–37 px, contra 52 px neutros. | Atacante 49–52 px. A rival fica entre 47 e 52 px até o primeiro tropeço e flexiona a 46 px no último. |
| Leitura da Puxada com Escudo | A b49 elevava e girava a rival. A b50 ainda atrasava o escudo enquanto o fundo era recomposto a cada passo. | O quadro da mão precede a puxada de 32 a 24 px. O escudo aparece no dano no centro e no canto. A rival recua 14 px no centro, cai e se levanta. A parede absorve o recuo. |
| Paleta e arma | A b50 herdou a faixa azul de uma referência intermediária. A paleta válida, por si só, aceitava o desvio. | As 64 variantes do recorte passaram no controle de altura, apoio, índigo no peitoral, ciano fora dessa região e túnica por traje. O framebuffer mostrou a arma na mão e separada do tronco. |

O replay NTSC repetiu os oito contatos e a guarda do roteiro quadro a
quadro. A captura inclui áudio PSG isolado. As sessões privadas foram
encerradas por ID. A regressão de KO confirmou sete puxadas, o bloqueio
dos movimentos após a derrota e o reinício com o controle 2. O pico
amostrado foi de 47 sprites na SAT, oito por
linha, zero falhas e zero finais de envio fora do VBlank no roteiro por
leitura. O pior intervalo foi de três quadros VDP. As janelas úteis
mediram 33,675591334654854 e 39,78064478101405 FPS funcionais e
reprovam o piso de 58. Doze intervalos atrasados ocorreram com a carga
de envio zerada. O próximo diagnóstico de desempenho precisa atribuir
as épocas perdidas à lógica ou à preparação antes de trocar o orçamento
do VBlank.

Das 308 variantes, 64 foram revisadas e 244 mantiveram os mesmos
pixels da b49. As fontes e a receita estão preservadas no workspace.
O envio conjunto da branch publicaria outros 22 commits além do lote.
O [recibo de recuperação local](../out/candidates/scene02_alis_mirror_b52/mirror-source-b52-delta.json)
identifica o arquivo com os deltas e a ROM à qual se referem.

[Vídeo em tempo real](../out/diagnostics/alis_mirror_20261122/qa-b52-shield-shove/continuous/round-continuo.mp4) ·
[Prancha do framebuffer](../out/diagnostics/alis_mirror_20261122/qa-b52-shield-shove/revisao-do-framebuffer.png) ·
[Fases no framebuffer](../out/diagnostics/alis_mirror_20261122/qa-b52-shield-shove/shove-phases.json) ·
[Comparação das duas faces e trajes](../out/diagnostics/alis_mirror_20261122/art-b52-final/review-2x.png) ·
[Regressão de KO](../out/diagnostics/alis_mirror_20261122/qa-b52-reset/input.json) ·
[Curadoria e próximo executor](curation_candidates/2026-11-22_alis_impacto_puxada_model_sheet.json).

## b53 · Pouso, paleta e recolhimento

A [ROM b53](../out/candidates/scene02_alis_mirror_b53/rom/master_of_fighters.sms)
tem SHA-256 `a15313589a6d196553e3c1ba16548db948818e8639ac5b85f7fbe4c720ce6753`.
O build integral passou pelo wrapper e a auditoria encontrou 166 bytes
de folga no corredor de sondas.

| Ponto | Evidência da revisão |
|---|---|
| Entrada no pouso | A b52 manteve os quatro ataques aéreos em estado de golpe por 5, 10, 6 e 10 leituras após o contato, respectivamente. Na b53 os oito casos entraram em agachamento no contato com o chão e executaram o normal baixo na soltura consumida. P1 e P2 executaram um golpe baixo após receber um botão novo na própria leitura do pouso, com o botão aéreo anterior ainda mantido. |
| Cinza no chute forte | A correção abrange o chute em pé, o aéreo e a preparação compartilhada. A auditoria encontrou um pixel de punho no fundo e a conversão passou a tratar esse plano junto dos sprites. O teste comparou as faces e os trajes. |
| Posturas baixas | O agachamento passou de 34 a 33 px e a guarda baixa de 36 a 34 px, com a sola na linha 143. |
| Recolhimento | A pose própria mantém 52 px. Foi registrada nos VDP 398 e 709 do teste por leitura, com a rival já no chão nas duas capturas. |

A revisão alterou 40 variantes de arte. As outras 268 conservaram os
mesmos pixels da b52. O roteiro de luta por leitura registrou zero
falhas e zero finais de envio fora do VBlank, com pior intervalo de
três quadros VDP.

O replay visual contínuo conservou dez contatos e uma defesa em
1266 quadros. Confirmou os dois chutes fortes por controle e a fase
do escudo no impacto. As janelas NTSC mediram 33,675591334654854
e 40,284197246596506 FPS funcionais. O aceite de cadência segue aberto
pelo piso de 58. O monitor de áudio isolado entregou silêncio em
duas sessões. O replay foi verificado como prova visual, com a
verificação de áudio pendente. As sessões foram encerradas por ID.

[Pouso por leitura](../out/diagnostics/alis_mirror_20261122/followup-b53/pouso-leitura-por-leitura.json) ·
[Comparação da arte](../out/diagnostics/alis_mirror_20261122/followup-b53/comparacao-art-b52-b53.png) ·
[Quadros do emulador](../out/diagnostics/alis_mirror_20261122/followup-b53/qa-b53-escudo-chutes/shove-phases.json) ·
[Replay visual](../out/diagnostics/alis_mirror_20261122/followup-b53/qa-b53-escudo-chutes/replay-visual-b53.mp4) ·
[Curadoria](curation_candidates/2026-11-22_alis_pouso_materiais_recolhimento.json).

## Estado do aceite

| Eixo | Evidência atual |
|---|---|
| Build | O wrapper gerou as ROMs candidatas com 524.288 bytes e o corredor de sondas foi auditado por SHA. |
| Relatório de validação | Pré-gates passaram. Os recibos por sessão registram caixas, publicação, SAT e carga de envio. |
| Boot | Observado no Emulicious privado com dois controles e os dois trajes, inclusive após cruzar. |
| Gameplay | Os 12 normais conectaram nos dois controles. A matriz diferencia acerto, guarda, erro, giro e retomada. As primeiras exposições de alguns impactos, entre elas a guarda em pé durante o recuo, mantêm o eixo em aberto. |
| FPS | As janelas mistas ficaram abaixo de 58. A preparação do par ainda perde épocas de publicação, inclusive em trechos sem término de envio em área ativa. |
| Áudio | Escudo e espada têm timbre distinto verificado em PCM. A calibração de sincronismo e os roteiros esparsos ainda têm verificações abertas. |
| Memória | [Memória do projeto](10-memory-bank.md) e [registro para curadoria](curation_candidates/2026-11-21_alis_espelho_producao.json) atualizados. |

A origem e o vínculo de cada banco foram conferidos. A revisão da
época visual continua aberta no encaixe da mão com a vítima na pega e
na proporção das poses presas. A aceitação de movimento exige os
mesmos 78 px e 20 ticks de voo, com fase ativa, reação e retomada
visíveis sob a cadência exigida. A medição seguinte deve conservar
o primeiro golpe frio, o par de lâminas, o giro na parede, o HUD e
o PSG em carga. Cada janela válida deve chegar a 58 FPS, com
dispersão de até dois e sem arredondamento do resultado.
No NTSC de 59,92274340431231 Hz medido aqui, uma janela de exatamente
120 VDP exige pelo menos 117 avanços para atingir o piso. A segunda
janela mista da b39 teve 80. O ganho restante precisa vir da lógica e
da preparação de poses antes da janela de envio, com a composição dos
dois corpos e o áudio preservados.
