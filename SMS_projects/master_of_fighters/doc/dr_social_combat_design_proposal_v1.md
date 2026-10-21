# Dr. Ferdinand Social — identidade de luta e proposta de moveset v1

**Status:** `design_approved_by_owner_2026-10-10; art_balance_and_hardware_pending`  
**Escopo:** decisão de design para revisão; não é moveset selado, frame data medida, sprite sheet nem autorização para integração em `res/` ou ROM.  
**Referências locais:** `11-gdd.md`, `dr_social_animation_contract_v1.md/.json` e a fonte aprovada das 61 poses básicas.

## Parecer de maturidade

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
