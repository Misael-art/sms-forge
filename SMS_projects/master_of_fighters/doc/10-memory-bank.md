# 10-memory-bank — master_of_fighters

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
