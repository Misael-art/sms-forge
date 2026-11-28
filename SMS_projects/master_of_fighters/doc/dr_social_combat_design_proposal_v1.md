# Dr. Ferdinand Social — identidade de luta e proposta de moveset v1

**Status:** `design_approved_by_owner_2026-10-10; art_balance_and_hardware_pending`  
**Escopo:** decisão de design para revisão; não é moveset selado, frame data medida, sprite sheet nem autorização para integração em `res/` ou ROM.  
**Referências locais:** `11-gdd.md`, `dr_social_animation_contract_v1.md/.json` e a fonte aprovada das 61 poses básicas.

## Consulta vigente

Consulta atual: [GDD — contrato de experiência](11-gdd.md#contrato-de-experiência--revisão-de-design-de-2026-11-01).
O estado da arte/ROM segue o memory bank; menções abaixo à primeira fonte de
61 poses e conversão v10 são históricas, não seleção atual. A direção de
combate aprovada em 10/10 é preservada; detalhamento de consequências a seguir
é **hipótese de design para testar**, sem novos golpes, números ou cancels
aprovados. `cane_riposte` continua absorvido pelo Super.

## Contratos de experiência por movimento — 2026-11-01

Fonte de identidade: model sheet CPS2-Alpha-Cel v4, correções de grisalho/óculos
e direção individual registrada no GDD. Fonte dos IDs/tracks: contrato de
animação v2. O artista pode propor atuação e distribuição de poses preservando
essa identidade; não fixar cabeça, quadril, pés ou deslocamentos mínimos para
“caber no SMS”. Medir a composição antes de encomendar a folha completa.
Desenhos e exposições já aceitos não se reabrem por hipótese de balanceamento.

### `social_light_jab` — aproximação curta

- **Intenção/uso:** verificar um rival que entrou perto e criar confirmação
  curta. O punho é apoio ao duelista, não sua principal ferramenta de alcance.
- **Preparação/ameaça:** pequeno carregamento corporal legível e foco do olhar;
  luva sai da guarda pela cadeia ombro–cotovelo–punho. A bengala mantém sua
  identidade e não ganha hitbox só por estar desenhada.
- **Direção/alcance/trajetória:** direto frontal curto; extensão do punho
  delimita o contato proposto. Não alongar braço/caixa para alcançar o rival.
- **Resposta/contrajogo:** rival administra distância ou defende; fora da
  extensão, o jab erra. Social se expõe ao comprometer a mão; janela de punição
  e classificação alto/médio ainda precisam teste, não são vantagem garantida.
- **Acerto/bloqueio/erro:** hipótese de reação curta e confirmação no acerto;
  bloqueio com pose/som distintos e sem confirmação de hit; no erro não há
  reação, spark nem perda de vida. Combo com bengala continua proposta,
  dependente de cancel/advantage medidos.
- **Recuperação:** recolher a mão e recuperar a guarda antes de nova ação,
  salvo cancel explicitamente aprovado. Testar apertar, manter, soltar e
  apertar novamente. Os 2/1/1/1/1/3 da amostra não definem frame-data.
- **Aceite:** jogador distingue alcance curto, contato e retorno; prova futura
  registra input, pose, caixas, estado do rival e vida. Hoje a ROM de poses
  comprova apresentação limitada, não hit/block/whiff.

### `basic_cane_tap` — assinatura de distância média

- **Intenção/uso:** ocupar o espaço diante do corpo e punir aproximação/erro.
- **Preparação/ameaça:** mão e bengala se organizam à frente do torso; ponta
  romba e empunhadura permanecem distintas da rapieira.
- **Direção/alcance/trajetória:** toque frontal com arco de preparação/recolha,
  sem varrer a tela; contato limitado à arma visível. Alcance absoluto pendente.
- **Resposta/contrajogo:** defender ou ficar fora da ponta; Social compromete
  o braço e pode ser punido durante recolha no erro. Não declarar segurança
  universal por pushback nem rastreamento automático do alvo.
- **Acerto/bloqueio/erro:** hipótese de pequeno afastamento que restaura a
  distância de bengala; bloqueio informa defesa, sem liberar automaticamente
  a estocada; erro mostra extensão vazia e recolha. Dano/chip/empurrão em aberto.
- **Recuperação:** recompor pegada e guarda, sem arma atravessar o corpo.
  A rota bengala→rapieira só é candidata em hit confirmado; testar separadamente
  hit, block e whiff antes de selar qualquer cancel.
- **Aceite:** reconhecível como golpe de bengala em ambas as faces, com ponta,
  ameaça e exposição visíveis no par. Arte, colisão e runtime pendentes.

### `social_low_boot_check` — interrupção baixa próxima

- **Intenção/uso:** contestar avanço próximo pela linha baixa, sem lançar o rival.
- **Preparação/ameaça:** transferência de peso e joelho anunciam a bota; torso
  e bengala equilibram o apoio sem esconder a perna atacante.
- **Direção/alcance/trajetória:** arco curto baixo, à frente; não cobre distância
  de bengala nem vira rasteira de tela inteira.
- **Resposta/contrajogo:** guarda baixa é a resposta proposta; permanecer fora
  do alcance ou punir a recolha. Guarda alta deve perder para baixo conforme a
  regra do GDD. Duração/possibilidade real dessa punição aguardam medição.
- **Acerto/bloqueio/erro:** hipótese de interrupção baixa curta no hit, sem
  knockdown automático; no block o rival conserva oportunidade de responder;
  whiff não reage no adversário. Sem vantagem/dano numéricos aprovados.
- **Recuperação:** recolher e plantar o pé, regressar à guarda com apoio
  coerente. Não permitir deslizar ou responder ainda suspenso sem regra.
- **Aceite:** a ameaça baixa pode ser distinguida antes do contato e a guarda
  correta altera a consequência. Comparar baixo/alto e alcance limite na ROM.

### `rapier_lunge` — punição linear de compromisso maior

- **Intenção/uso:** converter leitura de distância/erro em estocada precisa.
- **Preparação/ameaça:** organizar arma, apoio e linha do ombro; a lâmina deve
  ler como rapieira, sem virar bengala afiada ou feixe mágico.
- **Direção/alcance/trajetória:** avanço e extensão frontais em linha, alcance
  na ponta visível; deslocamento contínuo. Não prometer alcance maior por
  hitbox invisível nem perseguir mudança de lado durante a ação.
- **Resposta/contrajogo:** defender, evitar pela distância ou saltar se a
  geometria aprovada permitir. Sem invulnerabilidade; erro deixa a extensão
  comprometida. Não classificar como anti-aéreo ou overhead por conveniência.
- **Acerto/bloqueio/erro:** hipótese de recompensa de punição mais clara que
  jab; guard deve ter leitura e recuperação próprias; whiff mostra estocada
  vazia com oportunidade de resposta. Valores/knockback/chip pendentes.
- **Recuperação:** recolher lâmina e corpo, recuperar base e guarda; ataque
  interrompido precisa finalizar seus objetos/caixas sem teleporte de arma.
- **Aceite:** testar em perto/médio/fora do alcance e nas bordas, com hit,
  block e whiff. Recovery competitivo não deriva das doze poses propostas.

### `boomerang_throw` — escolha de aproximação à distância

- **Intenção/uso:** exigir decisão espacial do rival, dando a Social uma
  escolha de avanço/recuo; não sustentar projéteis sem risco.
- **Preparação/ameaça:** carga do braço e objeto de aço legível antes da
  soltura. Violeta, quando autorizado como efeito, não substitui o objeto.
- **Direção/alcance/trajetória:** arco determinístico de ida; retorno em erro,
  uma instância ativa por vez, sem mira automática. Dimensões, velocidade,
  alcance, colisão no retorno e regra após hit/block continuam pendentes.
- **Resposta/contrajogo:** escolher avanço, guarda ou salto compatível com o
  arco; pressionar a abertura do lançador. Não atribuir invulnerabilidade à
  preparação nem afirmar vantagem enquanto o objeto retorna.
- **Acerto/bloqueio/erro:** hit tem feedback no ponto de contato; block é
  reconhecível e não se confunde com hit; whiff mantém arco/retorno legíveis.
  Destino do objeto em hit/block e eventual segundo acerto precisam de decisão
  explícita antes de implementar; não resolver multi-hit implicitamente.
- **Recuperação:** distinguir liberação do controle corporal de disponibilidade
  do objeto; segundo arremesso só quando a instância anterior terminou segundo
  regra selada. Recepção/desaparecimento/interrupção exigem endpoint visível.
- **Aceite:** nenhuma instância duplicada, acerto repetido indevido ou projétil
  órfão após round; testar ida, erro, retorno, canto e interrupção com ambos os
  lutadores/HUD/PSG. Arte/objeto/runtime e budget conjunto pendentes.

### `social_read_super` — Laudo Final, três ramos de uma ação

- **Intenção/uso:** arriscar uma leitura de ataque físico alto/médio e gastar
  uma barra cheia própria do medidor comum. Não é resposta universal.
- **Preparação/ameaça (`attempt`, LC):** guarda de bengala deliberadamente
  armada e janela curta reconhecível; rival percebe que pode atrasar/fintar.
  Sem transformação, aura vampírica, teleporte ou violeta de bumerangue.
- **Direção/alcance/trajetória (`hit`, LCH):** captura elegível → desvio de
  bengala → pivô/saque → estocada de rapieira → recolha. Distância e geometria
  da captura pendentes; não puxar rival distante através da tela para encaixar
  a coreografia. Clarão comum é proposta sujeita a budget, não objeto liberado.
- **Resposta/contrajogo:** baixo, agarrão, projétil, atraso e finta vencem a
  contra-leitura. A janela não autoriza ignorar dano ou agarrões fora dessa
  condição. Regra exata de disputa simultânea/interrupção precisa decisão.
- **Acerto/bloqueio/erro:** sucesso apenas após captura física válida; falta de
  alvo/janela expirada vai a `whiff` LCW, com recuperação vulnerável. Se a
  estocada posterior pode ser bloqueada ou é consequência garantida da captura
  permanece pendente; não inventar ramo de block no runtime. Dano, devolução
  de barra e momento exato do débito também não estão aprovados.
- **Recuperação:** sucesso termina com armas/guarda recompostas; erro mostra
  bengala sem contato e retorno exposto. Todos os ramos devem terminar e
  liberar controle; nenhum cancel universal vem desta decisão.
- **Aceite:** matriz de elegíveis e negativos (alto/médio, baixo, projétil,
  agarrão, atraso, ausência de ataque), barra vazia/cheia, interrupção e round
  encerrado. Evidência identifica qual ramo ocorreu e o estado do rival.
  Conceito aprovado; produção e balanceamento dos três ramos pendentes.

### Movimentos e estados comuns já documentados

O contrato de animação v2 também prevê estados que sustentam a experiência.
As descrições abaixo orientam revisão, sem aprovar valores ou acrescentar ações.

| Estado | Intenção, preparação/direção e risco | Consequência, recuperação e critério |
|---|---|---|
| Idle/guarda neutra | Observar e tornar prontidão reconhecível; não ameaçar dano sem input. | Soltar direção termina deslocamento conforme regra futura; não disparar ação sozinho no jogo. Autoplay é exclusivo do diagnóstico. |
| Avanço/recuo | Escolher distância de bengala; passos com apoio e orientação para o rival. Aproximar expõe ao ataque, recuar cede espaço. | Deslocamento e apoio precisam concordar; borda limita posição sem atravessar rival ou trocar lado sem regra. Guard/ataque após soltar testados. |
| Pulo/aterrissagem | Comprometer trajetória aérea para mudar distância/evitar ameaça compatível; impulso antes do voo. | Sem invulnerabilidade presumida. Hit no ar deve continuar física de queda; pouso recompõe apoio/controle. Trajetória e vulnerabilidade pendentes. |
| Abaixar/defesa | Sinalizar mudança de altura e guarda; não sumir em um frame nem mascarar baixa/alta. | Hit/block distintos, vida/chip coerentes e saída para neutro; defesa não prova cancel ou parry. |
| Dash | Reposicionamento comprometido previsto no exercício; impulso e chegada legíveis. | Sem teleporte/invulnerabilidade automática; distância, cancel e recuperação dependem de decisão/teste. |
| Queda/rolagem/levantada | Mostrar perda de controle e recuperação, com corpo e arma conectados. | Sem escolha de direção ou invulnerabilidade presumidas. Definir janela de retorno; testar borda, interrupção e ausência de estado preso. |
| Apresentações/provocações | Expressar frieza, investigação e confiança por olhar/atuação; não atribuir buff ou captura. | Entrada, duração/skip e exposição das provocações pendentes; não consumir input de início como golpe. |
| Vitórias/derrota por tempo/empate/retratos versus | Dar encerramento coerente ao resultado do round/duelo; postura corresponde ao desfecho. | Sem hitbox residual ou repetição de prêmio. Duas vitórias/duas apresentações etc. permanecem no contrato existente; não exigem novas telas. |

Para os estados sem ataque, hit/block/whiff não são resultados próprios:
avaliar **receber ataque, interromper, sair e retomar**. Cada ação competitiva
aguarda layout de dois botões, colisões e budget no consumidor. Não usar o
viewer de 61 poses como prova dessa interação.

## Parecer de maturidade da direção aprovada

A direção narrativa foi organizada como duelista metódico que observa,
controla a distância e pune erros com armas precisas. A aprovação do dono
resolveu a seleção dos golpes e o papel do Super. Permanecem quatro fronteiras
explícitas para a produção:

1. O conjunto é adaptação autoral para fighting game; o original não documenta
   estes golpes nem frame data competitiva.
2. O Super usa o medidor comum do jogo; seus números, HUD e regras entre rounds
   precisam ser especificados antes de implementação.
3. Os nomes e propriedades de algumas armas primárias de *Master of Darkness*
   divergem entre fontes comunitárias. O manual e a ROM original ainda precisam
   desempatar essa nomenclatura histórica.
4. A folha conceitual #14 continua candidata. A folha de jab parte da fonte
   aprovada de 61 poses e do tratamento de pixel aprovado na conversão v10,
   sem importar detalhes exclusivos de uma concept sheet pendente.

O dono aprovou esta direção em 2026-10-10 e autorizou iniciar a produção das
folhas, começando por `social_light_jab`. A aprovação fecha o papel do
personagem, a lista de ações, os dois especiais e a ideia de Super; ela não
aprova pixels, frame data, hitboxes, balanceamento nem orçamento de hardware.
Os valores de frames, alcance, dano, recurso e vantagens continuam pendentes de
medição e teste hit/block/whiff.

## Fatos do jogo original e fronteira de autoria

*Master of Darkness* é um jogo de ação/plataforma, não um jogo de luta. O guia
consultado descreve ataque primário no botão 1, subarma com cima + botão 1,
pulo no botão 2 e deslocamento direcional. Ele lista faca, espada, martelo e
machado como armas primárias; pistola, bomba, bumerangue e estaca como
secundárias. O bumerangue percorre um arco e retorna quando erra o alvo.
O arquivo de sprites de SMS Power registra animações de ataque com espada e
adaga e separa os itens/armas do protagonista. Nenhuma dessas fontes documenta
combos, especiais ou frame data competitiva. As técnicas abaixo são autoria do
projeto, não golpes oficiais do jogo original.

O jogo apresenta Ferdinand Social como psicólogo que investiga acontecimentos
sobrenaturais em Londres. Para o projeto, permanece humano: sem transformação
ou traços de monstro. A arte aprovada estabelece bengala,
rapieira e bumerangue de aço como elementos visuais; a trilha violeta pertence
somente ao bumerangue.

Fontes consultadas:

- [Guia de *Master of Darkness* para Master System — controles e armas](https://gamefaqs.gamespot.com/sms/588099-master-of-darkness/faqs/44643)
- [Arquivo de sprites e armas de *Master of Darkness* — SMS Power!](https://www.smspower.org/Sprites/MasterOfDarkness-SMS)
- [Sinopse de Ferdinand Social — Giant Bomb](https://wiki-origin.giantbomb.com/wiki/Games/Vampire_Master_of_Darkness)
- [M.U.G.E.N Tutorial 1 — separação entre `.cmd`, `.cns` e `.air`](https://network.mugenguild.com/justnopoint/1.0docs/tutorial1.html)

## Arquétipo proposto

**Duelista investigativo de médio alcance / whiff-punisher.** Ele cria uma
ameaça legível com a bengala, converte aproximações previsíveis em estocadas de
rapieira e usa o bumerangue para obrigar o adversário a escolher entre avançar,
defender ou saltar. Sua vantagem vem de alcance, precisão e leitura; não de
força bruta, agarrões ou pressão de projéteis sem risco.

| Eixo | Proposta | Limite/contrajogo |
|---|---|---|
| Força | Controle de distância média e punição de golpes que erram | Pressão curta e dano inicial baixos |
| Mobilidade | Avanço normal e reposicionamento disciplinado | Sem dash ofensivo invulnerável ou teleporte |
| Defesa | Guarda metódica e Super de contra-leitura, se aprovado | A resposta especial não captura baixo, agarrão, projétil ou golpe atrasado |
| Alcance | Bengala no neutro, rapieira em linha reta, bumerangue em arco | Estocada previsível; bumerangue tem recuperação e só pode existir um por vez |
| Identidade | Frieza e leitura de padrões, representadas por fintas e contra-ataques | Não transformar psicologia em controle mental ou magia de combate |

Ele não é grappler, tanque nem zoner de tela inteira. Socos e chutes existem
como normais rápidos e de baixo dano, para tornar o conjunto funcional em jogo
de luta; a bengala é sua assinatura de curta/média distância. Rapieira e
bumerangue são as duas ferramentas de maior compromisso.

## Lista candidata de ações

| ID | Categoria | Ação e função | Relação e contrajogo | Poses-fonte iniciais |
|---|---|---|---|---:|
| `social_light_jab` | Normal leve | Jab curto de luva; confirma a curta distância | Dano baixo; alcance curto; permite seguir para toque de bengala | 6 propostas |
| `basic_cane_tap` | Normal médio | Toque direto de bengala; controle principal do neutro | Só alcança a extensão desenhada; punição se errar | 8 já propostas no contrato: BC01–BC08 |
| `social_low_boot_check` | Normal baixo | Chute curto para interromper avanço próximo | Sem lançamento; alcance mínimo; vulnerável se defendido | 7 propostas |
| `rapier_lunge` | Especial 1 | Estocada linear de precisão | Pode ser defendida, saltada ou evitada; sem invulnerabilidade; recovery no erro | 12 já propostas: RL01–RL12 |
| `boomerang_throw` | Especial 2 | Bumerangue de aço em arco; pressiona distância e força resposta | Um ativo por vez; trajetória previsível; retorno em erro e recuperação; sem mira automática | 14 do ator: BT01–BT14; track próprio do objeto |
| `cane_riposte` | Fase-base do Super | Contragolpe com bengala, incorporado à contra-leitura de “Laudo Final” | Não ocupa espaço de terceiro especial; os ramos de acerto/erro são parte do Super | 10 no contrato atual, ainda candidato |
| `social_read_super` | Super candidato | “Laudo Final”: contra-leitura com bengala e finalização precisa de rapieira | Só captura ataque físico alto/médio no tempo certo; perde para baixo, agarrão, projétil, atraso ou finta | 6 de tentativa + 8 de sucesso + 6 de erro, propostas |

Os golpes com punhos e botas não substituem as armas no plano de identidade.
Pistola, bomba e estaca ficam fora do primeiro moveset: aumentariam a carga de
projéteis, recursos e sprites sem reforçar tanto o perfil de duelista. Podem
ser reconsideradas depois de testar o papel do bumerangue.

## Super candidato: “Laudo Final”

O Super expressa a especialidade do personagem: interpretar uma intenção e
responder com precisão. Em vez de uma explosão mágica, Social arma uma guarda
curta, desvia um ataque elegível com a bengala, saca a rapieira e executa uma
estocada limpa. A confirmação é um clarão de impacto compartilhado pelo jogo;
não há aura de transformação. O efeito violeta continua exclusivo do
bumerangue.

**Ativação aprovada como direção:** gastar a barra cheia do medidor comum de
Super do sistema. Cada lutador mantém sua própria carga sob as mesmas regras;
ganho, capacidade numérica, persistência entre rounds e HUD permanecem pendentes
de especificação/implementação no GDD/TDD. A janela de contra-ataque é curta e
visível. Um sucesso exige ataque
físico alto/médio dentro da janela; agarrões, golpes baixos, projéteis, ataques
atrasados e fintas vencem a leitura. Se nada for capturado, Social fica exposto
na recuperação.

**Sequências e endpoints propostos:**

- `social_read_super_attempt` (LC01–LC06): começa na guarda neutra; arma a
  bengala e abre a janela; termina no ramo de sucesso ou de erro.
- `social_read_super_hit` (LCH01–LCH08): desvio → pivô → saque da rapieira →
  estocada → contato → recolha → guarda; só inicia após captura válida.
- `social_read_super_whiff` (LCW01–LCW06): a leitura falha, a bengala não
  encontra contato, e Social retorna à guarda depois de uma recuperação
  vulnerável.

Trilhas próprias devem ser registradas para corpo, bengala e rapieira. O clarão
de impacto usa o efeito comum do jogo, sem sprite independente até a direção
visual global de efeitos ser aprovada. Os três ramos não compartilham
artificialmente quadros só para reduzir a contagem.

| Sequência | Aplicações planejadas dos 12 princípios (vincular aos IDs no JSON) |
|---|---|
| `attempt` | Antecipação LC02–LC04; staging LC01–LC05; pose a pose LC01–LC06; follow-through do punho/manga LC04–LC06; slow in/out LC02 e LC05–LC06; arco da bengala LC03–LC04; ação secundária do olhar LC02; timing da janela LC05; exagero contido LC04 pela silhueta; desenho sólido da cadeia ombro–cotovelo–punho–bengala LC01–LC06; appeal na guarda LC01/LC06. |
| `hit` | Squash/stretch sutil no carregamento LCH02, sem deformar lâmina; antecipação LCH02; staging LCH01–LCH04; pose a pose LCH01–LCH08; follow-through do casaco/cravat LCH05–LCH07; slow in/out LCH02/LCH07–LCH08; arco do desvio e estocada LCH02–LCH05; ação secundária do olhar LCH01/LCH06; timing do contato LCH05; exagero controlado LCH04–LCH05; desenho sólido em todos os quadros; appeal na guarda final LCH08. |
| `whiff` | Antecipação LCW01; staging LCW01–LCW03; pose a pose LCW01–LCW06; follow-through do casaco LCW03–LCW04; slow-out LCW04–LCW06; arco da bengala que não encontra alvo LCW02–LCW03; ação secundária do olhar LCW03–LCW04; timing da recuperação vulnerável LCW03–LCW05; exagero da silhueta exposta LCW03; desenho sólido da bengala sem atravessar mão/corpo; appeal na volta à guarda LCW06. |

Nos ramos `attempt` e `whiff`, squash/stretch não foi planejado: tronco e armas
preservam anatomia e eixo rígido. No ramo `hit`, há somente compressão de apoio
corporal, sem deformar a lâmina ou alongar membros.

## Combos e plano de jogo propostos

1. `social_light_jab → basic_cane_tap`: confirmação curta; dano modesto e
   empurrão suficiente para recolocar Social na distância da bengala.
2. `social_low_boot_check → social_light_jab → basic_cane_tap`: rota baixa de
   curto alcance; sem loop e sem derrubada automática.
3. `basic_cane_tap (hit confirm) → rapier_lunge`: conversão principal; apenas
   no acerto confirmado, não no bloqueio ou erro.
4. `boomerang_throw → avanço ou recuo medido`: ferramenta de espaço, não
   extensão automática de combo; não permitir segundo bumerangue enquanto o
   primeiro estiver em voo/retorno.
5. `social_read_super`: opção de leitura e punição, não cancelamento garantido
   de qualquer normal. O dano, hitstop, custo e duração ficam sem números até
   existir escala de vida/medidor aprovada.

Uma sequência não pode prender o rival em pressão sem saída. Para cada rota,
medir hit, bloqueio e erro; explicitar janela de cancelamento, vantagem,
hitstop e resposta. O alcance real da hitbox termina na ponta visível da arma.

## Animação, pixels e SMS

Antes de cada folha, atualizar o contrato versionado com gatilho, estados
inicial/final, IDs de pose, duração provisória, tracks independentes de corpo,
arma e efeito, trajetória, hitbox e startup/active/recovery. Cada sequência,
inclusive ramos de acerto/erro, deve aplicar ao menos sete dos 12 princípios
com evidência contextual ligada a IDs de quadro; a auditoria estrutural não
substitui revisão do movimento desenhado.

Primeira folha recomendada: `social_light_jab`, seis poses únicas, para validar
punho, cotovelo, ombro, silhueta e retorno à guarda. Depois: toque de bengala
BC01–BC08, chute baixo, rapieira RL01–RL12, bumerangue BT01–BT14 e, por último,
os ramos do Super. Em toda sequência: arma inteira dentro do canvas, pegada
contínua, contorno limpo, cluster de cor por material e nenhum pixel órfão.

Mapa planejado de princípios para as sequências de golpes. Os vínculos são
propostas semânticas; ao selar o moveset, cada linha vira `principle_evidence`
no JSON e será revisada contra os PNGs reais:

| Sequência e chaves | Aplicações planejadas (7 ou mais) | Princípios sem aplicação forte |
|---|---|---|
| Jab `J01–J06`: guarda, carga, extensão, contato, recolha, guarda | Antecipação J02; staging J01–J04; pose a pose J01–J06; follow-through J04–J05 na manga; slow in/out J02 e J05–J06; timing J04; desenho sólido na cadeia ombro–cotovelo–punho; appeal J01/J06 | Sem squash/stretch para não deformar o biotipo; sem arco enfatizado por ser golpe direto; sem ação secundária para manter a leitura do punho; exagero reduzido para preservar precisão |
| Bengala `BC01–BC08` (contrato atual): guarda, carrega, estende, contato, recolhe, recompõe pegada, estabiliza, guarda | Antecipação BC02; staging BC01–BC04; pose a pose BC01–BC08; follow-through BC04–BC06 na manga/cravat; slow in/out BC02 e BC06–BC08; arco BC02–BC05; secundária no olhar BC02; timing BC04; desenho sólido da pegada e eixo da bengala; appeal BC01/BC08 | Sem squash/stretch no corpo ou na bengala rígida; exagero restrito para manter o toque leve; pose a pose protege pegada e ponta |
| Chute baixo `K01–K07`: guarda, transfere peso, carrega joelho, contato, recolhe, planta, guarda | Squash/stretch sutil de apoio K02/K06; antecipação K02–K03; staging K01–K04; pose a pose K01–K07; follow-through K04–K05 no casaco; slow in/out K02 e K05–K07; arco K03–K05; ação secundária na barra do casaco K02/K05; timing K04; desenho sólido quadril–joelho–tornozelo; appeal K01/K07 | Exagero fica baixo porque é interrupção curta, não golpe de força |
| Rapieira `RL01–RL12` (contrato atual) | Squash/stretch sutil RL02–RL03 no carregamento corporal; antecipação RL02–RL03; staging RL01–RL06; pose a pose RL01–RL12; follow-through RL06–RL08/RL11 no casaco; slow in/out RL02–RL03 e RL07–RL10; arco RL03–RL05; ação secundária no casaco/olhar RL11; timing RL06; exagero controlado RL05; desenho sólido em mão, guarda e lâmina; appeal RL01/RL10–RL12 | Nenhum princípio omitido; a arma nunca se deforma |
| Bumerangue `BT01–BT14` (contrato atual) | Squash/stretch BT03–BT05 apenas na carga corporal; antecipação BT02–BT04; staging BT01–BT08; pose a pose BT01–BT14; follow-through BT05–BT07 no braço/casaco; slow in/out BT04–BT05 e BT11–BT12; arco BT05–BT10 na trilha do objeto; secundária BT07–BT08 no olhar/mão livre; timing BT08–BT11 durante a abertura da guarda; exagero controlado BT05/BT10 pela silhueta; desenho sólido na pegada/eixo; appeal BT01/BT12–BT14 | Nenhum princípio omitido; o objeto de aço não se deforma |

No Super, os ramos LC01–LC06, LCH01–LCH08 e LCW01–LCW06 já têm mapas
separados acima; cada ramo mantém no mínimo sete aplicações contextualizadas.
O contato/hitstop não pode ser tratado como duração final até a escala de tick e
os timings serem medidos.

`source_pose_count` é quantidade de desenhos, não de objetos SMS. Tile único,
P1 compartilhada, padrões residentes, SAT/scanline, RAM/ROM e pior VBlank
ficam `pending` até converter e medir. Não definir números de hardware a partir
de concept sheets ou estimativa visual.

## Método de referência M.U.G.E.N e limites

O tutorial M.U.G.E.N consultado separa comandos de entrada (`.cmd`), estado e
regras do personagem (`.cns`) e animações (`.air`). Essa separação é útil para
organizar o contrato e os estados de luta, mas não transfere limites nem APIs
para o Master System. Foram consultados
`SMS_projects/luta_mugen/rascunho/character/ryu.zip` e
`SMS_projects/luta_mugen/rascunho/character/Ken_Majik_.zip` (arquivos de
personagens M.U.G.E.N de terceiros), além dos perfis locais
`ryu_scale_pilot_80px.json` e `ken_scale_pilot_80px.json`:

- Em Ryu, `.cmd` separa a sequência de botões do `ChangeState`; o Super verifica
  `Power` e permite cancelamento só em estados/janelas listados. `.cns` declara
  `StateDef`, animação e `HitDef`; `.air` mantém os quadros e as caixas
  `Clsn1/Clsn2` por elemento.
- Em Ken, o comando `Reppa` exige `Power >= 1000`; as transições permitem iniciar
  em neutro ou cancelar após `MoveContact` de golpes específicos. Isso é um
  exemplo útil de confirmação de acerto explícita, não uma regra automática de
  balanceamento.
- Os arquivos de referência também usam combinações com mais botões que o
  Master System. Não importar essas combinações nem seus movimentos para Dr.
  Social; usar apenas a separação de comando, estado, animação e condição de
  cancelamento.

Os perfis e arquivos M.U.G.E.N orientam a organização, não definem a interface
SMS. Os controles concretos do moveset permanecem abstratos até o layout SMS de
dois botões e a adaptação MUGEN→SMS serem conciliados. Não copiar comandos de
três ou quatro botões sem decisão de mapeamento. A janela de tick deve obedecer
ao TDD do jogo e os custos de render devem ser medidos na ROM de Master System.

## Decisões aprovadas e limites ainda abertos

- Aprovados pelo dono em 2026-10-10: duelista investigativo de médio alcance;
  jab e chute como normais de suporte; toque de bengala como normal de
  assinatura; `rapier_lunge` e `boomerang_throw` como os dois especiais;
  contragolpe de bengala incorporado ao Super `Laudo Final`; barra cheia do
  medidor comum de Super como custo conceitual.
- Continuam pendentes: frame data e escala de dano; controles exatos de dois
  botões; economia numérica do medidor; hitboxes/hurtboxes; timings; revisão
  independente de cada folha; limites reais de tiles, SAT, scanline, VRAM, RAM,
  ROM/banking e VBlank.

Após a aprovação da direção, o GDD e o contrato machine-readable devem refletir
as decisões acima. A produção visual segue golpe a golpe: primeira candidata
`social_light_jab`, com revisão de anatomia, rosto, punho/pegada, roupa,
clusters de cor e recorte antes de qualquer conversão para SMS. Cada folha
permanece candidata até review independente e aprovação do dono.
