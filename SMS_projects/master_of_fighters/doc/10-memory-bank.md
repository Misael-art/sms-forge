# 10-memory-bank — master_of_fighters

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-10-05 — o dono avaliou que as falhas estruturais mais graves do roster
foram corrigidas e listou polimento restante: clusters e cel shading suaves no
Shinobi/Alis, olhos/rosto, contornos de pés/capas/casaco, volume de escudos,
encaixe da espada-cana, arco/corda de Landau e fidelidade da arma/rosto de J.J.
O complemento do dono esclarece o padrão: contornos contínuos em degraus de
pixel, clusters e cel shading definidos, sem blur, antialiasing ou dithering;
a mão de Hayato também exige verificação de um dedo pouco legível.
O feedback textual hash-bound está em
`data/source_art/roster_harmony_review/harmony_sprites_owner_feedback_20261005.json`;
a checklist por personagem está em
`doc/roster_harmony_refinement_review_v1.json` e ainda bloqueia promoção.
O feedback não anexou a imagem pós-tratamento. A prancha atual
`data/source_art/roster_harmony_review/harmony_sprites_proportion_comparison_v2.png`
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
`data/source_art/roster_harmony_review/harmony_sprite_index8_reencodes_v1.json`.

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
  material, idle 72–88 px (refit dos ~104 px da referência), biotipo por
  classe de peso (proposta pendente de confirmação do dono). Referência é
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
  `data/source_art/concept_art/dr_social/dr_social_concept_sheet_v1.png`, com
  prompt e SHA em `dr_social_concept_prompt_v1.txt` e
  `asset_lineage_record.json`; estado `source_candidate`. Inspeção visual:
  duas poses de corpo inteiro, traços humanos, bengala/óculos/sobrecasaco/
  cravat visíveis, rapier e boomerang presentes, sem texto, marca-d'água ou
  pixel art. Revisão cega independente, medição formal de paleta/contorno e
  aprovação do dono continuam pendentes; não é sprite nem contrato visual.

- **Concept art Dr. Social — revisão 2 (2026-10-03)**: variante editada da
  folha anterior, com aparência um pouco mais jovem (~início dos 30) e
  expressão/postura voltadas a virtude, coragem e busca da justiça. Arquivo:
  `data/source_art/concept_art/dr_social/dr_social_concept_sheet_v2.png`;
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
  `data/source_art/concept_art/lord_of_the_sword/asset_lineage_record_v1.json`.

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
  `data/source_art/roster_harmony_review/harmony_sprites_frame00_candidate_v1.png`
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
  avaliação atual está em `data/source_art/roster_harmony_review/harmony_candidate_frame00_audit_v2.json`,
  status `owner_visual_revision_required`, e o board em
  `data/source_art/roster_harmony_review/harmony_sprites_frame00_review_v2.png`.
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
