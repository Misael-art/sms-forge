# 11-gdd — master_of_fighters

## Continuidade da amostra v8 — 2026-10-29

Somente idle + social_light_jab em seis desenhos: cinco quadros v5 e contato
reto J04 já autorado na v6, montados sem editar pixels. Fonte/chaves estáticas
passaram na revisão integral; fluxo temporal, simplificação SMS e dono seguem
em checkpoint humano. Sem novos personagens, estados, golpes ou atlas.
`dr_social_cps2_sample_v1.md` conserva fontes, receita selecionada e limites.

## Continuidade de 2026-10-29

O dono aprovou o método e seu encaminhamento à curadoria futura. A candidata
corrente é v5, com reparo facial aprovado em review independente no escopo da
fonte. Isso não aprova o contato J04, a simplificação SMS ou a arte completa;
o escopo continua uma pose idle + jab, sem novos movimentos ou atlas.
Detalhes, fonte/ROM e limites: `dr_social_cps2_sample_v1.md`.

## Recorte autoral CPS2 em revisão — 2026-10-28

O pedido atual autoriza somente uma pose idle e `social_light_jab` J01–J06,
com fonte em escala CPS2 e conversão posterior. O canvas 80×80 descrito no
histórico abaixo não limita a nova fonte: a candidata usa células 128×128,
corpo de aproximadamente 104 px e paleta-fonte própria. J01–J06 mantêm os
tempos propostos 2/1/1/1/1/3 ticks; balanceamento continua não aprovado.

A identidade permanece no model sheet v4, com decisões posteriores de cabelo
cinza e óculos de latão. A aprovação artística v08.2 de 61 poses existe e foi
conferida pelo SHA `4e557095…`; notas históricas de aprovação pendente estão
superadas nesse escopo. A nova variante não substitui a fonte aprovada.
Fontes, receita, revisão e limites estão em `dr_social_cps2_sample_v1.md`.
Conversão e ROM desta amostra são diagnósticas, sem promoção ao elenco,
gameplay, cenário/HUD ou entrega visual de produção.

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**
> **REGISTRO INICIAL (2026-10-02)** — nome provisório: **Master of Fighters**.
> GDD em construção; revisão humana pendente (workflow new-project passo 2).

## Pitch (1 frase)
Jogo de luta 1v1 fan-made para Master System com a escalação mais icônica do
console — heróis do hall e chefes lendários — rodando sobre o motor de luta
dirigido por dados MUGEN→SMS (`SMS_projects/luta_mugen` +
`tools/sms_wrapper/mugen2sms/`), com toda a arte redesenhada em pixel art SMS
e paletas CRAM compartilhadas por sprites, cenário e HUD conforme o contrato
`doc/palette_runtime_contract_v1.json`.

## Gênero declarado
`fighting` (deve bater com `specialization` em `.mddev/project.json` —
`audit_specialization.py` compara os dois.)

## Loop central
Escolher personagem → duelo 1v1 melhor-de-3-rounds → punzir/bloquear/esquivar
conforme o padrão de IA do oponente → vencer → desbloquear chefe/alterno →
escolher de novo com roster e oponentes mais duros.

## Escalação registrada (2026-10-02; expansão aprovada pelo dono em 2026-10-04)

### Hall de personagens (jogáveis)
| # | Nome | Fonte (jogo SMS) | Nota de direção |
|---|------|------------------|-----------------|
| 01 | Guerreiro de Golden Axe | Golden Axe Warrior (SMS) | **versão estilizada** — jovem aventureiro ágil, elmo com chifres e capa; sem proporção de brutamontes/tanque. Classe de jogo pesada permanece separada da morfologia visual. |
| 02 | Hayato | Kenseiden | samurai; katana + magias de pergaminho |
| 03 | Joe Musashi | Shinobi | ninja; traje clássico do 1º Shinobi como **alterno desbloqueável** |
| 04 | Dr. Ferdinand Social | Master of Darkness (US: Demon Sword) | psicólogo vitoriano caça-vampiros; NÃO se transforma em vampiro (correção do dono 2026-10-03) — arsenal do original: bengala, rapier, faca, machado + pistola, bombas, boomerang |
| 05 | Karateca de Black Belt | Black Belt (JP: Geki Shitou) | sem nome oficial — o projeto pode batizá-lo |
| 06 | Bruxa de Psychic World | Psychic World | artes marciais + magia psíquica |
| 07 | Alis Landale | Phantasy Star | heroína; side sci-fi/fantasy do roster |
| 08 | Landau | Lord of the Sword | jovem adulto; guerreiro do norte com espada e arco (manual US); sprites originais em vista lateral, poses devem ser retrabalhadas para luta |
| 09 | J.J. | Zillion II: The Tri Formation (Master System) | jogo ancora identidade, cores e mecânicas; model sheet do anime foi consultado apenas para corrigir o figurino, por pedido do dono; lutador ágil com pistola laser Zillion; Tri-Formation/Armorater pode inspirar mobilidade, ainda em proposta |

O dono adicionou J.J. à escalação em 2026-10-04 e especificou **Zillion II para Master System** como fonte de identidade, paleta e mecânicas. Como o sprite é pequeno e o figurino difere na versão anime, referências do anime são usadas somente para a construção visual da roupa, por pedido do dono; não definem golpes, lore do fan game ou pose copiada. A classe leve e a conversão de equipamento/veículo em mecânica de luta continuam propostas, sujeitas à revisão do dono e a medição.

### Chefes (não-jogáveis por padrão; desbloqueáveis a decidir no GDD completo)
| # | Nome | Fonte | Nota |
|---|------|-------|------|
| B1 | Ninja Master | Shinobi | chefe final |
| B2 | Count Dracula | Master of Darkness | chefe final |
| B3 | Luter | Phantasy Star | chefe final de PS1 |
| B4 | Dark Force (Dark Falz) | Phantasy Star II | a confirmar: Dark Falz é o chefe final de **PS2**, não de PS1 |

## Personagens explicitamente NÃO registrados (fora até nova decisão)
- Alex Kidd e Psycho Fox: sugeridos no brainstorming de 2026-10-02, **não
  entraram** na escalação registrada pelo dono — não adicionar sem decisão nova.

## Eixos de fighting (lastro de gênero — `audit_specialization.py`)
- **hitboxes**: ataque e corpo definidos por retângulos em dados (tabelas
  compiladas do pipeline mugen2sms), nunca colisão de bounding-box única;
  hitboxes desenhadas em overlay de debug durante coreografia.
- **startup_active_recovery**: cada golpe autoral documenta as três fases em
  frames (60fps NTSC / 50fps PAL) na tabela do personagem; frame data é
  contrato de balanceamento, revisado por medição, não por sensação.
- **hitstop**: congelamento curto em frames na confirmação de hit (parâmetro
  por tipo de golpe na tabela; valor inicial a medir no lote de pilotagem —
  nada é fechado sem medir o degrau seguinte).
- **specials**: cada personagem do hall tem 2 especiais registrados no GDD
  completo (ex.: arsenal ocultista do Dr. Social — boomerang/rapier, magia de pergaminho de Hayato,
  psíquico da bruxa); especiais viram comandos nas tabelas, com orçamento de
  sprite/scanline aprovado pelo simulador.
- **guard**: defesa alta/baixa com bloqueio visível (faísca de guard),
  dano de chip-documentado; Ninja Master e demais chefes usam guard IA para
  pressão legível.

### Movesets — status
Proposta temporária em `doc/movesets_draft.json` (12 entradas da escalação
anterior — 8 heróis e 4 chefes —, 44 golpes; não contém o J.J. adicionado em
2026-10-04). Seu arquivo de personagem terá uma proposta separada sem frame
data até revisão. Frame data existente ancorada no molde medido
MSSF2T/hamoopig; `balance: nao-testado`.
**O dono NÃO aprovou esta proposta** — política vigente: **cada moveset é
discutido e fechado individualmente na construção daquele personagem**, e só
o arquivo de personagem selado na discussão vale como contrato. Pendências
abertas no draft: cláusula multi-hit vs um-golpe-um-acerto, e golpes
tela-cheia condicionados a `measure_worst_frame.py`.

#### Dr. Ferdinand Social — moveset autoral aprovado (2026-10-10)

O dono aprovou individualmente a direção de luta e autorizou a produção
progressiva das folhas de golpes. Social é um duelista investigativo de alcance
médio/whiff-punisher: jab e chute baixo são normais de apoio; o toque de bengala
é seu normal de assinatura; os dois especiais são estocada de rapieira e
arremesso de bumerangue. O contragolpe de bengala integra o Super **Laudo
Final**, não ocupa um terceiro espaço de especial.

O Laudo Final consome uma barra cheia do medidor comum de Super. O sistema terá
uma carga por lutador sob regras comuns ao elenco. Ganho numérico, HUD,
persistência entre rounds, escala de dano e janela em ticks seguem pendentes de
especificação e medição; não implementar números da proposta como valores
aprovados. A captura é uma leitura curta contra ataques físicos altos/médios;
perde para baixo, agarrão, projétil, atraso ou finta. Não há transformação,
teleporte ou invulnerabilidade universal.

Os números de startup/active/recovery, alcance e dano continuam
`proposal_unmeasured`. Cada folha é produzida uma por vez, inicia em
`data/source_art/` como candidata, e precisa de revisão independente, aprovação
humana e conversão/prova SMS antes de integrar em `res/` ou ROM. A primeira
sequência autorizada para desenho é `social_light_jab`; os ramos seguintes
permanecem documentados no contrato de animação e serão desenhados na ordem
registrada na proposta.

A primeira candidata visual do jab tem seis poses legíveis em sequência, mas a
versão v2 falhou no preflight de transparência e paleta: PNG RGBA 1536×1024,
alpha parcial sem pixels totalmente opacos, sem export 80×80 ou paleta SMS
indexada. Permanece em `review_drafts`; não é arte aprovada nem recurso de ROM.

### Contrato de animação e sprite sheet — exercício Dr. Social

O contrato corrente aprovado em design está em
`doc/dr_social_animation_contract_v2.md` e no JSON vinculado; v1 permanece como
registro histórico da proposta. Ele cobre 20 estados comuns: idle, avanço, recuo, pulo/aterrissagem,
abaixar, dash, queda, rolagem/levantada, defesa, duas vitórias, derrota por
tempo, empate, duas provocações, duas apresentações e três retratos versus
(neutro, vitória e derrota). As sequências ativas de combate são jab, toque de
bengala, chute baixo, estocada de rapieira, arremesso de bumerangue e três ramos
do Super (tentativa, acerto e erro). `cane_riposte` fica apenas como registro
histórico: a ação foi absorvida pelo Super e não é um terceiro especial.

Para cada sequência, declarar estado inicial/final, loop/transição, IDs e
contagem proposta de poses-fonte, duração por pose, trilha do personagem e de
cada objeto/efeito animado, e os 12 princípios. Pelo menos sete princípios
devem ser aplicados com pista visual planejada ligada a quadros; os demais
recebem justificativa. Pista planejada não é evidência de animação renderizada.
`source_pose_count` conta desenhos de pose distintos; objetos 8×8/8×16,
metasprite, tiles únicos, SAT/scanline e custo VBlank são campos separados e
ficam pending até converter e medir os pixels.

Atualização de fonte (2026-10-12): a folha v1 anteriormente selecionada para
conversão foi arquivada em
`data/source_art/sprite_studies/dr_social/historical_approved/basic_sequences_61f_owner_source_v1/`;
serve somente como histórico. A v07, SHA-256
`f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`, foi
rejeitada artisticamente pelo dono: o casaco perdeu sua hierarquia, o cabelo
varia entre cinza e tons avermelhados/castanhos e as sombras ficaram granuladas.
A identidade permanece ancorada exclusivamente no model sheet aprovado
`data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`.
Não existe sprite sheet de movimentos básicos aprovada. A v08.1 falhou no gate
de clusters. A candidata v08.2 passou a auditoria quantitativa de clusters, mas
aguarda revisão visual do dono e ainda não é fonte de gameplay.

A reconstrução v08 foi iniciada como diretriz. A tentativa exploratória de
geração de imagem foi reprovada tecnicamente: alterou o canvas para 1182×1330,
produziu fundo opaco e 287.407 valores RGBA distintos; portanto não é arte v08,
não permite comprovar os limites dos 61 quadros nem conformidade semântica. O
experimento e as métricas estão em
`doc/curation_candidates/2026-10-12_dr_social_v08_imagegen_trial_rejection.json`.
Não foram produzidos previews 1×/4× válidos. O arquivo
`doc/dr_social_sprite_rebuild_directive_v08.md` fixa uma paleta indexada, papéis
por material, cabelo em cinzas constantes e sombras de cel shading em blocos
contíguos. Blur, média, distância cromática/espacial, luminância, nearest-RGB,
ImageGen e difusão são proibidos. O dono autorizou máscaras explícitas por
quadro/material e reassociação determinística de clusters dentro dessas máscaras,
com delta rastreável. O feedback para curadoria está em
`doc/curation_candidates/2026-10-12_dr_social_v07_artistic_rejection.json`.

Em 12/10/2026, a diretriz v08.1 incorporou a autorização explícita dos óculos de
latão como zona amarela: a candidata preserva os 85 pixels faciais autorizados.
O relatório registra zero vazamentos semânticos branco/amarelo/bordô/cinza, zero
pixels pendentes e haste da bengala com 1.245 pixels brancos uniformes; alpha,
grade 8×9, paleta e 61 poses permanecem intactos. A limpeza 2×2 ainda não passou:
restam 73 singletons no cabelo, 96 no casaco e 341 na pele, além de 102/139/553
componentes abaixo de 2×2. Uma revisão da franja encontrou sombra avermelhada
fora da máscara do cabelo; a máscara recuperou 1.014 pixels dessa sombra e agora
mede zero pixels não cinza em 61/61 poses. Portanto a candidata está reprovada pelo próprio
gate de clusters e não pode ser promovida. Contrato delta:
`doc/dr_social_sprite_mask_contract_v08_1.json`; diretriz:
`doc/dr_social_sprite_rebuild_directive_v08_1.md`; relatório e amostras estão em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_1_masks_candidate/`.

Em 12/10/2026, a v08.2 executou a reclassificação de fronteira autorizada pelo
dono. Cada componente sem quadrado sólido 2×2 recebeu a cor dominante do anel
8-conectado opaco imediato; o algoritmo processa um componente por vez e mede de
novo até ponto fixo. O contorno original e a geometria alfa foram preservados;
863 pixels de material receberam índice de contorno por essa regra explícita.
O casaco usa somente os índices 5/6 (ciano `#00AAAA` e sombra escura `#005555`).
A auditoria independente por célula confirmou zero singletons e zero clusters
sem bloco 2×2 em cabelo, casaco e pele; 61 poses, canvas 640×720, grade 8×9,
11 cores úteis, vazamentos semânticos zero, cabelo cinza em 61/61 e óculos 85/85.
A candidata e as amostras 1×/4× estão em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_2_final_candidate/`;
contrato e registro estão em `doc/dr_social_sprite_mask_contract_v08_2.json` e
`doc/curation_candidates/2026-10-12_dr_social_v08_2_cluster_consolidation.json`.
O passe quantitativo não substitui revisão artística humana. A v08.2 não foi
promovida a `res/` nem compilada em ROM.

A folha histórica v1 contém 61 poses: idle (4), avanço (8), recuo (8), pulo (8),
abaixar (5), dash (8), queda (8), rolagem/levantada (8) e defesa (4). Esses
IDs/contagens continuam como contrato do exercício, mas não promovem a arte
histórica como fonte visual ativa. A prova técnica idle+ação de duas poses
continua validando somente o método de conversão; nunca substitui a folha
completa de animação. A ROM de inspeção v5 deriva da fonte histórica e é apenas
diagnóstica, fora de `res/`.

A aprovação de uma nova folha exige previews 1×/4× de idle quadro 1, avanço
quadro 1 e queda quadro 2; inspeção humana de cabelo em 61/61; zero ocorrências
fora das regiões semânticas; zero clusters sem bloco 2×2 em cabelo, casaco e
pele (a haste branca de 1 px é exceção semântica); revisão de casaco, anatomia e
bengala; revisão independente e aceite explícito do dono. Integração, alocação
P1 comum, tiles/SAT/scanline/VBlank, runtime e ROM permanecem gates separados e
ainda não medidos para a candidata v08.2.
A ROM de inspeção v5 deriva somente da fonte v1, hoje arquivada, e preserva
evidência histórica navegável. Ela é diagnóstica, fora de `res/`, e não valida a
candidata v2 nem fecha paleta P1 global, orçamento por cena, pior VBlank, timing
contínuo ou aprovação de asset final. Consultar os valores medidos e limites
exatos no TDD antes de qualquer integração.

Pesquisa de *Master of Darkness* separa fatos do original de adaptação: um guia
de SMS relata ataque primário, subarma com `Up + Button 1`, salto com `Button 2`
e armas primárias/secundárias. Outra fonte diverge nos nomes de algumas armas
primárias; o manual escaneado e a ROM original precisam desempatar. O original
não documenta golpes de fighting game nem frame-data competitiva. Os quatro
ciclos listados são propostas autorais; valores de startup/active/recovery,
alcance e dano são hipótese sem teste e não selam o moveset.

Regra de coerência física: deslocamento contínuo a partir de apoio/impulso,
trajetória da arma ligada à mão e alcance de hitbox limitado à silhueta real.
Quanto maior alcance/dano/cobertura, maior startup, recovery, custo de recurso
ou exposição; cada golpe deve ter contrajogo explícito. Física em runtime Z80
usa inteiros/Q8.8, sem `float`/`double`; pulo/queda usam posição, velocidade e
gravidade por tick, e bumerangue usa arco inteiro determinístico. O JSON inclui
distâncias/durações iniciais de marcha, dash, pulo e arremesso como
`proposal_unmeasured`, além de quatro linhas hipotéticas de frame data. Escala
de vida e dano continua pendente; não tratar pontos de dano como porcentagem
aprovada. A folha completa só pode ser desenhada após revisão das chaves e
orçamento TDD/spec; aprovação de contrato não prova pixel art, física,
equilíbrio ou ROM.

## Direção de arte — estilo visual (decisão humana, 2026-10-02)
**Estilo escolhido**: anime de luta anos 90 com traço e cores do exemplo
fornecido — folha SFZ2-style de Ryu,
`/mnt/sdcard/SGDKForge/SGDK_projects/Mugenesis_Demo .../res/mugen/ryu/sheets/g0.png`
(medida: 288×104, 4 frames ~72×104, **15 cores úteis + fundo magenta** —
exatamente 1 sub-paleta). Dimensão de Ryu documenta o exemplo de traço; não é
escala-alvo deste roster. Referência é `inspiration_only=true`: âncora
técnica de traço/escala de sombra, **nunca fonte de pixels** (sprites Capcom
e ROMs Sega não viram asset — proveniência manda).

### Contratos mensuráveis (tradução SMS)
| Eixo | Piso numérico | Origem |
|------|---------------|--------|
| Paleta de sprites em combate | Uma P1 compartilhada por todos os sprites, até 15 cores úteis; P0 para cenário/HUD | TDD + contrato de paletas |
| Contorno | 1 px, quase-preto da própria sub-paleta | referência |
| Sombras de material | 3 tons por material (base + sombra + sombra profunda/highlight), sem dithering em pele | referência |
| Saturação | primárias saturadas; sem "gradiente suave" (ilegal na paleta mestra) | SFZ2 + SMS_GLOBAL |
| Escala corporal de luta | **66–72 px**, centro 70 (referência Fatal Fury Special GG projetada para SMS) | `doc/11-gdd.md` + `doc/15-tdd.md` |
| Line weight | constante entre frames e entre personagens; drift = reprovação | style_drift_policy |

### Escala e morfologia do elenco (direção do dono, 2026-10-04)
O peso de gameplay não determina altura de tela. A folha aprovada de Hayato em
Kenseiden é a referência do projeto para clareza de pixel clusters, contorno e
acabamento; identidade, roupa e cores de cada personagem continuam vindo do
respectivo jogo e conceito harmonizado. O elenco deve ser revisto em conjunto,
com baseline comum e sem normalizar cada figura para a mesma altura.
Joe Musashi é uma referência separada de proporção humana esguia e massa dos
membros; o uso como âncora morfológica não aprova seu recorte atual nem autoriza
copiar identidade, roupa ou paleta. Cada âncora deve ter escopo explícito.

| Personagem | Altura de corpo-alvo SMS (px) | Direção morfológica/visual |
|-------------|-----------------------------|----------------------------|
| Guerreiro de Golden Axe | 64–68; nunca acima de Alis | Jovem e ágil; reduzir a escala anterior e seguir o conceito aprovado v2 |
| Hayato / Kenseiden | 68–72 | Âncora de escala e acabamento do roster |
| Joe Musashi / Shinobi | 68–72 | Lutador médio; proporção humana esguia, não referência de recorte |
| Dr. Ferdinand Social | 66–72; centro 70 | Mesma escala de Joe; silhueta esguia, sem parecer menor |
| Alis Landale | 66–70 | Jovem heroína; proporção de cabeça, torso e pernas sem leitura chibi |
| Landau / Lord of the Sword | 68–72 | Igualar Joe e Dr. Social; preservar design aprovado e acabamento de Hayato |
| J.J. / Zillion II | 68–72 | Igualar Hayato; jovem ágil, não chibi, proporcional ao conceito aprovado |
| Demais heróis e chefes | faixa individual no contrato visual | Medir exceções e manter os mesmos critérios de roster |

As faixas são alvos visuais do projeto, não lei de hardware. A referência de
escala é *Fatal Fury Special* para Game Gear: uma captura de gameplay foi
inspecionada em viewport nativa 160×144; uma figura em pé ocupa cerca de 53 px
de altura no quadro consultado. Projetar essa fração para a tela SMS 256×192
resulta em `53 × 192 / 144 ≈ 71 px`; o centro de trabalho fica em 70 px com
tolerância de roster. A estimativa é visual e aproximada, não uma medida de
tile ou limite físico; o jogo varia tamanho aparente por pose/profundidade.
Referências: [capturas originais Game Gear de Fatal Fury Special (160×144)]
(https://www.mobygames.com/game/10591/fatal-fury-special/screenshots/game-gear/66969/),
[galeria de gameplay](https://www.gamestar.de/galerien/fatal_fury_special_game_gear,46053.html)
e [documentação técnica da resolução Game Gear](https://docs.retrogamecoders.com/platforms/sega/).

Comparar altura corporal de coroa a sola; arma, cabelo solto, capa e efeitos
ficam registrados separadamente como extensão da silhueta. A tela não determina
canvas do PNG: escolher por pose, acrescentar borda transparente e manter
largura/altura em múltiplos de 8 para o inventário de tiles. 96×96 não é mais o
alvo padrão; canvas maior exige justificativa visual e orçamento de
tiles/runtime. O primeiro estudo técnico de Dr. Social usa 80×80, convertido em
nearest-neighbor 5/6, para aproximar a faixa de 70 px sem interpolação.

Os vínculos explícitos continuam: Guerreiro de Golden Axe ≤ Alis; Dr. Social,
Joe Musashi e Landau na mesma faixa; J.J. e Hayato na mesma faixa. Diferença de
altura não substitui a revisão humana de cabeça/torso/pernas, morfologia,
clusters, contorno, paleta e fidelidade. `audit_roster_harmony.py` mede apenas
dimensões e relações declaradas; a prancha comparativa recebe revisão artística
separada.

Contrato corrente, fontes e medidas do primeiro quadro comparativo em
`doc/roster_harmony_contract_v1.json`. O board
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_candidate_v1.png`
atinge as relações dimensionais declaradas, mas o dono rejeitou sua decisão
estética: Joe tem defeito de recorte; os demais candidatos leem atarracados/chibi;
e alguns agrupamentos de cor poluem a pintura apesar dos valores de paleta
corretos. A próxima proposta precisa passar os eixos humanos registrados em
`doc/roster_harmony_candidate_review_v1.json`: morfologia, massa dos membros,
recorte, agrupamento cromático, acabamento e leitura nativa. O board de revisão
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_review_v2.png`
registra a reprovação e continua fonte de estudo, não sprite aprovado. Um frame
00 não aprova animação ou integração.
Uma direção morfológica alternativa em
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v1_finish.png`
é apenas referência para discutir corpo/finish: seus valores cromáticos ainda
não foram validados pela paleta mestra, e a tentativa de fundo transparente foi
rejeitada por franja. Não promover esses PNGs como personagem, folha ou recurso.

Em 2026-10-04, o dono apontou defeitos construtivos na prancha de sete
personagens: olhos, mãos/handedness, conexão mão→arma, articulações, fixação e
perspectiva de equipamento, pés/baseline, contorno e agrupamento de luz/material.
L106 acrescenta o workflow `tools/sms_wrapper/.agent/workflows/art-review.md`
e o checklist obrigatório `audit_art_review_checklist.py`. A nova ilustração
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v2_review_candidate.png`
propõe as correções, mas não é pixel art SMS e aguarda parecer de arte
independente e decisão do dono; o checklist
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v2_review_checklist.json`
mantém todos os eixos como pending. A proposta não altera nem aprova folhas de
sprites já existentes. Em sprites reais, a inspeção de cada quadro ocorre em
1× e nearest-neighbor 4×, com paleta, recorte, animação e roster verificados em
gates próprios.

### Política de prompt/geração
- Descritores técnicos neutros apenas ("90s anime fighting pixel sprite,
  1px dark outline, 3-tone shading, saturated primaries"); proibido
  "in the style of Street Fighter/Capcom/Zero 2" em prompt de geração.
- `source_kind` de todo asset final: redesenho autoral (hand_authored ou
  ai_generated pós-tradução) — ROM rip só como estudo em `out/local_study/`
  gitignored.

### Paletas de referência por personagem e alocação CRAM (2026-10-02; alocação atualizada em 2026-10-09)
Manifesto machine-readable: `doc/palettes_manifest.json`, gerado e validado por
`doc/build_palettes_manifest.py` contra `tools/sms_wrapper/sms_palette.py`
(códigos 6-bit, rampas de material ΔY ≥ 17, ≤15 úteis, índice 0 transparente).
As entradas por personagem descrevem cores de identidade e estudo de autoria;
elas não são tabelas CRAM separadas que possam ser carregadas simultaneamente.
No SMS, P1 é a única tabela de cores de sprite e todos os objetos de sprite
compartilham seus índices. As 14 entradas atuais do manifesto somam 43 RGBs
distintos; é necessário harmonizá-las numa tabela de combate P1 de até 15 cores
úteis antes de promover sprites. Esse mapeamento permanece `pending`.
P0 atende cenário e HUD. Suas cores de HUD precisam manter papéis consistentes
entre estágios, deixando as demais entradas para cenário. Tiles de fundo podem
selecionar P1 com `TILE_USE_SPRITE_PALETTE` para reutilizar cores já carregadas;
isso não adiciona cores à CRAM nem altera a tabela global de sprites.
P1 índice 0 é transparente somente para pixels de sprite. Índice 0 de BG sempre
exibe uma cor da tabela escolhida, inclusive quando um tile usa P1. P0 índice 0
é a cor visível de backdrop, não alpha; o orçamento visual do projeto o reserva
como fundo.
Composição, slots fixos do HUD e cores de cenário são definidos na tabela de
paleta do scene contract, sem carregar uma paleta nova por personagem durante
o round. A referência machine-readable é `doc/palette_runtime_contract_v1.json`.

Pares de mesma luminância e matiz diferente são aceitos **somente** separados
por contorno 1 px (política do traço SFZ2). Joe (traje clássico) é **alterno
por troca de roles no mesmo pool** — não gasta paleta extra. Dr. Social NÃO
tem forma vampira (correção do dono, 2026-10-03: a transformação é premissa
de *Vampire: Master of Darkness*, Game Gear 1993 — não do SMS).
Revisão cromática Dr. Social (2026-10-03): traje azul/ciano com sombra teal,
cabelo grisalho e botas castanhas foram conferidos no sprite original SMS;
camisa branca, cravat burgundy e óculos de latão permanecem detalhes autorais.
Contorno opaco usa navy #000055 para preservar o índice 0 transparente. Esta
paleta substitui o traje cinza da revisão anterior.

Na roupa de Dr. Social, a rampa do tecido mantém os tons SMS em ordem
sombra/base/luz: teal `#005555`, ciano `#00AAAA`, azul `#55AAFF`. A revisão da
arte convertida deve conferir a continuidade espacial desses tons pelas faces
e dobras do casaco/calça em todos os quadros. A conformidade de RGB com a
paleta não basta: azul claro isolado numa região de sombra é defeito de
`material_shadow_flow_coherence`. Este é um contrato de material para a
conversão candidata, não uma decisão sobre a paleta P1 compartilhada do jogo.
Sombras, base e luz devem aparecer em blocos contíguos de cel shading, sem
dithering ou pixels-confete. Branco, amarelo e demais acentos ficam limitados
às regiões semânticas aprovadas no concept e no contrato de paleta; pixels
isolados na roupa, cabelo ou contorno reprovam
`semantic_palette_role_confinement`. A limpeza deve preservar olhos, luvas,
gola, bengala e os demais detalhes legítimos de identidade.

Paleta candidata de J.J. (2026-10-04): derivada do sprite `J.J - Standing`
de *Zillion II: The Tri Formation* no Master System. Azul-violeta, vermelho
magenta, laranja, pele e branco foram aproximados à grade RGB canal×85; rampas
extras de sombra cel mantêm até 15 cores úteis. Preto do sprite-fonte é
substituído por navy #000055 no contorno, pois índice 0 permanece transparente.
O gerador validou a paleta individual `jj_zillion_ii` com 13 cores úteis.
Concept art v4 em duas poses completas foi aprovada visualmente pelo dono em
2026-10-04. O jogo Master System permanece como fonte de identidade, paleta e
comportamento; as referências do anime, pedidas pelo dono, só esclareceram a
construção e o mapeamento do figurino. Nenhum pixel, pose ou composição externa
foi copiado. O PNG usa os 13 tons SMS declarados para J.J., índice 0
transparente e sem dithering; os gates de recursos passaram. A aprovação libera
o estudo separado de sprites, não aprova a folha, moveset, integração em `res`
ou ROM. O estudo idle de 12 quadros segue candidato e passa por seus gates
próprios antes de revisão visual.

## Prova de conversão e regra de animação

Após o concept/model sheet aprovado, a primeira prova técnica por personagem
mostra exatamente duas poses-chave separadas: idle e uma pose de ação. Esta é
uma referência visual e um inventário de pixel/paleta/tiles; **não** é uma
animação de dois quadros nem uma folha final. A folha de animação só começa
depois da revisão humana, da semântica de movimentos e do orçamento explícito
de ROM, VRAM/RAM, SAT/scanline e VBlank no TDD e em `13-spec-cenas.md`.

Toda animação do jogo deve considerar os doze princípios: squash and stretch,
anticipation, staging, straight ahead/pose to pose, follow through/overlap,
slow in/slow out, arcs, secondary action, timing, exaggeration, solid drawing e
appeal. O contrato de cada animação registra status e evidência de cada
princípio. Uma pose estática não demonstra timing, aceleração/desaceleração,
intervalos, follow-through ou ciclo; esses eixos ficam pendentes até haver
quadros e revisão adequados.

O proof sheet técnico segue
`doc/asset_conversion_proof_standard_v4.md`; a prancha é mantida em
`data/source_art/asset_conversion_proofs/`, nunca promovida automaticamente a
`res/`. A grade de tiles aparece em mapa separado. O gate
`audit_asset_proof_sheet.py` exige correspondência exata entre recorte de
preview e PNG-fonte, e verifica cobertura de limites/paleta; revisão humana
independente julga anatomia, acabamento, fidelidade e apelo. Número de quadros
por sheet não é constante física do Master System: o teto do projeto depende
da medição de padrões residentes, pools, ROM/banking e uploads no VBlank.

### Limites de hardware que afetam os assets

- Tela 256×192; VRAM 16 KB = 512 padrões gráficos de 8×8 (32 bytes cada), com
  janela selecionada para sprites de 256 padrões.
- SAT até 64 objetos e até 8 sprites por scanline; objeto mede 8 px de largura
  por 8 ou 16 px de altura. Arte do lutador exige layout metasprite e simulação.
- CRAM tem 32 entradas em duas tabelas de 16. A tabela P1 é compartilhada por
  todos os sprites: índice 0 transparente e até 15 cores úteis comuns a todo o
  elenco ativo. P0 alimenta BG/HUD; seu índice 0 é backdrop visível. Tiles BG
  podem usar P1 via `TILE_USE_SPRITE_PALETTE`. O RGB usa canais
  `{0,85,170,255}`.
- RAM 8 KB, ROM sem mapper 48 KB, sem DMA; custo do pior frame de VBlank deve
  ser medido. Inventário de tiles não prova residência, scanline ou tempo de
  carregamento.
- O hardware não fixa um número geral de quadros por folha. Enquanto pools e
  política de carga não estiverem mensurados no TDD, registrar esse teto como
  `pending`; não inventar uma contagem máxima.

O piloto v2 foi rejeitado por arma junto à borda e canvas 96×96. A v3 também foi
retirada como proposta atual: sua reamostragem achatava o terminal da bengala e
deixava a forma ambígua. A v4 preserva duas poses independentes em 80×80 (10×10
tiles), reamostradas em nearest-neighbor a 5/6; usa o frame-fonte 01 para idle
e o 06 para ação, cujo terminal arredondado é legível no original. A bbox opaca
mede 37×67 px no idle e 58×64 px na ação, incluindo equipamento. A faixa visual
66–72 px é para altura anatômica em pé, coroa–sola e sem equipamento; a ação
agachada varia por encenação e não é um teste direto dessa altura. As caixas
totais atuais incluem itens e não provam conformidade; a altura anatômica ainda
requer medição/revisão humana. O par usa 89 padrões únicos (2.848 bytes brutos
em 4bpp). Ver
prancha e relatório
em `data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.png`
e `.json`. A amostra mostra 12 cores no estudo-fonte, mas isso não prova o
mapeamento para a tabela global P1 de até 15 cores; essa harmonização está
pendente. O terminal da bengala também precisa de revisão humana específica,
além de anatomia, fidelidade do concept, pintura, regiões materiais, orçamento
runtime e decisão do dono. A rota de conversão está registrada em
`tools/sms_wrapper/.agent/skills/sms-asset-to-rom.md` (L121). Em 2026-10-10,
idle e ação foram empacotados como 89 padrões 8×8 únicos mais um padrão vazio
(2.880 B carregados), construídos em ROM diagnóstica de 16 KiB e exibidos em
sessões Emulicious isoladas. A comparação exata encontrou zero divergências
nos 1.483/1.556 pixels opacos e nos fundos transparentes examinados. Esse
resultado prova a conversão estática e o vínculo por SHA desta amostra; não é
integração em `res/`, aprovação visual final, animação, gameplay ou orçamento de
produção. Paleta P1 do elenco, revisão humana, orçamento completo de cena,
VBlank, áudio e aceitação de release continuam pendentes.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | tela de seleção | grid 9 heróis + 4 chefes desbloqueáveis | documentado |
| 02 | duelo 1v1 | round com HUD de vida/timer sobre tables do motor | documentado |
| 03 | rolagem de arcade | hall → chefes em sequência, dificuldade crescente | documentado |

## Fora de escopo (explícito)
- Paridade com MUGEN real — o teto é "motor de luta MUGEN→SMS dirigida por dados".
- Tag-team, itens de arena, estágios interativos, online/link cable.
- Uso direto de sprites extraídos das ROMs Sega como arte final (proveniência bloqueia).
- Mexer em `MSSF2T` (intocável) — engine compartilhada via tabelas compiladas, não via fork.

## Teto de claims aprovado
"protótipo jogável de jogo de luta fan Master System sobre motor MUGEN→SMS" —
nada acima disso sem medição + evidência de emulador.
