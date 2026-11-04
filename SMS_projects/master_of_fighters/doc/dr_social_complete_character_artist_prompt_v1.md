# Prompt de produção artística — Dr. Ferdinand Social completo

Atualizado em **2026-11-02**, após reavaliação do commit
`587763cf1e192ada7bfbed4510d27fde240017b5`. Este é o **prompt integral vigente
para um agente substituto**, sem necessidade de acesso à conversa anterior.
Copie de “Prompt” até o fim. Inclui missão, estado real, referências, método,
artefatos, trabalho pendente e aceite. O nome v1 identifica esta incumbência;
o histórico anterior permanece no Git. Não é aprovação artística ou de produto.

## Prompt

Você é o artista de personagens e animador de **Master of Fighters**, jogo de
luta autoral de fã para Sega Master System, dentro do SMSForge. Sua missão é
produzir **um pacote artístico completo e coerente do Dr. Ferdinand Social**,
com sprites corporais, animações, armas/objetos/efeitos autorizados, retratos
de interface e de conversa, derivados SMS e evidência revisável. O designer
coordenador e o proprietário validarão este personagem antes de novas tarefas
de elenco. Não comece outro personagem.

Trabalhe na raiz existente `/home/misael/Projects/SMSForge`, consumidor
`SMS_projects/master_of_fighters`. Os caminhos abaixo são relativos a essa
raiz; quando indicados como `doc/...`, `data/...`, `.mddev/...`, `res/...` ou
`out/...` sem prefixo, são relativos ao consumidor, salvo indicação expressa.
Não crie clone, worktree, projeto paralelo, outro motor ou outro conversor.

### 0. Handoff do agente anterior — situação para começar

Você assume um trabalho já em produção. O agente anterior encerrou a sessão
por esgotamento de créditos; não há motivo para regenerar seus arquivos.
O trabalho está na raiz única e foi publicado até o commit-base acima na branch
`codex/host-bootstrap-continuity-20261024`, remoto `Misael-art/sms-forge`, PR #4.
Confira novamente HEAD/remoto ao iniciar; este handoff também receberá commit.
Não crie outra tarefa/thread, clone ou worktree por inferência.

**Objetivo integral:** um Dr. Social completo, expressivo, fiel à identidade e
revisável na interação prevista. **Estado atual:** pacote incompleto; uma
provocação diagnóstica integrada, um jab preservado, chaves e portraits em
estágios diferentes. Nem tudo está aprovado, nem tudo precisa ser refeito.

| Parte | O que existe | O que falta / não inferir |
|---|---|---|
| Jab v8 | Fonte J01–J06 preservada, revisão e demonstrações históricas próprias. | Não se conecta automaticamente à guarda nova nem prova duelo completo na escala GDD. |
| Guarda GQ03 | Autoral, 69 px, composição com Ken medida. | Candidata; identidade/arte ainda sem aceite. Não é ciclo idle completo. |
| Provocação 1 | Ciclo v3 no viewer, ajuste dos óculos/exame/assentamento/retorno. | Candidata para julgamento artístico, comandos competitivos/pacing/áudio pendentes. |
| Toque BC04 / bota K04 / rapieira RL05 | Chaves autorais preservadas. | Composição ofensiva/intervalos e integração não fechados. Toque ainda excede o par testado. |
| Portraits | Atenção/fala e três placas versus candidatas, algumas indexadas SMS. | Consistência/volume/expressões/ciclos; quatro expressões de conversa ainda faltam. |
| Cobertura restante | Matriz atual: 20 `not_started`, sete `gap_recorded_not_drawn`, além dos candidatos. | Não confundir essas contagens de linhas com número final de animações aprovadas. |
| Cena 10 | Contrato de apresentação de golpes e storyboard. | Atores/arte final/integração funcional; texto atual “comando em definição”. |

#### Baseline concreta: provocação 1 v3

Diretório de arte e recibos, relativo ao consumidor:
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1/`.
Neste diretório, ler `proposals/TA01_cycle_v3.json`,
`proposals/TA01_cycle_v3_terminal.json`, `proposals/TA01_cycle_v3_registration.json`,
`proposals/TA01_cycle_v3_adapter_config.json`, `lineage_v1.json` e
`generation_feeds_v2.json`. Os recibos v1/v2 são históricos, não receita atual.

- ROM existente: `out/candidates/dr_social_taunt01_cycle_v3_src/rom/master_of_fighters.sms`.
  SHA-256: `47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`.
  32768 bytes; viewer `MOF_CPS2_SAMPLE=10`.
- Build: `.mddev/dr_social_taunt01_cycle_v3_build.json`; recibo de build/mapa em
  `out/candidates/dr_social_taunt01_cycle_v3_src/`. O slot 9 e ROM v2 continuam
  preservados. Slots são identificadores técnicos, não ações novas do personagem.
- Vídeo: `out/diagnostics/social_taunt01_cycle_v3_20261101/emulator/taunt_v3_normal.mp4`.
  SHA: `66a98981cd85f175586613d3ee444e798dfa57937f087d7cc4b7e11c712f31f4`.
  360 quadros, 6.007736 s de reprodução nominal, 6.019422882 s de coleta.
- Prancha atual do terminal: no diretório de arte,
  `preview/TA01_cycle_v3_terminal_sms_8x.png`, SHA
  `e1dd5b72e115877ff61778b0b0fdb6f402448c732950e7928698d1776da4829e`.
  Ordem TA06 / TA07 nova / TA08 / GQ03, com faixa 1× e faixa 8×.
- Fonte da guarda: `logical/GQ03_authored_guard.png`, SHA
  `44c64bc957d24127d056ce0437c270814838616e8b0e04357d9c1ede5cb7819b`.
- Timeline do viewer: guarda → TA02_lean → TA03_reach → TA04_glasses →
  TA05_examine → TA06_coat_lag → TA07_settle_v2 → TA08_hand_rise → guarda.
  Exposições do gesto: 8/8/10/20/10/12/8, total **76 ticks**, aproximadamente
  1,27 s a 60 Hz. Espera de UI: 60 no arranque e 21 entre repetições.
  É hipótese diagnóstica; os 22 ticks do contrato continuam proposta, não houve
  decisão competitiva de duração/cancelamento/vulnerabilidade.
- Botão 1 dispara a revisão; botão 2 alterna autoplay. Nas verificações de seis
  frames, foram observados exame, retorno e nova execução. **Não são comandos
  competitivos** nem prova de latência de um frame. Estado 0 = guarda; 4 = exame.
- Sessão do produtor `909ac83e4a4e476e91d6676aba3be58c`, encerrada: janelas
  59.64763127522857 / 59.62493848380926 FPS. Dados em
  `out/diagnostics/social_taunt01_cycle_v3_20261101/emulator/taunt_v3_runtime.json`.
- Sessão do designer `dddf8c438ced42aba3f83c1434664419`, encerrada: VBlank selado
  de 3000 frames, zero derrame, `vline_min=207`, medidor com self-check. Relatório:
  `out/evidence/sessions/dddf8c438ced42aba3f83c1434664419/worst_frame/taunt_v3_designer_worst.json`.
  Fonte do build e mapa conferidos; corredor de sondas passou, folga 1784 bytes.
  Relatório usa rótulo genérico TITLE para snapshot 0; aqui significa guarda,
  não prova de tela de título. Sem série de estados individuais nesse relatório.
- Esses passes são do **viewer residente desse SHA**: não aprovam streaming,
  combate, elenco inteiro, arte, áudio ou pacing percebido. Viewer não chama PSG;
  silêncio intencional não equivale à trilha/SFX do personagem concluídos.

#### Parecer mais recente do designer — não reabrir por rotina

Orientação de TA07 para o rival e a troca indevida para azul escuro foram
corrigidas. TA08 já desenha a subida da mão. O commit 587763c mediu o terminal
sem nova pose/ROM: a luva livre chega à guarda com deslocamento descrito de
3 px para cima/2,5 px para o rival; caixas se tocam. Isso **não demonstra a
necessidade de acrescentar outro quadro só para a luva**.

A coerência global ainda merece julgamento artístico: cabeça/proporção e
material mudam entre o bloco final e a guarda. Os 877 px das fontes novas contra
836 de GQ03 e as larguras relativas registradas ajudam a localizar diferenças;
não são, por si, veredito anatômico. O recibo usa grupos brancos/recortes e limiares
de chave: são medidas exploratórias declaradas pelo produtor, não um gate de
anatomia homologado. Não usar largura em 10%/15% da altura como substituto de
crânio, ombro e perspectiva. A luva da bengala mantém aproximadamente o Y, mas
isso não comprova posição X constante. Mesma sola não prova corpo idêntico.

**Próxima ação:** apresentar a candidata atual com vídeo/1× e limitações para
julgamento artístico; só corrigir outra vez se houver defeito identificável
na sequência. Se houver deriva no bloco TA05–TA08, harmonizar o bloco necessário
com identidade/luz/escala, em vez de empurrar o salto de um quadro para outro.
Preservar GQ03 como candidata e o jab v8 como fonte existente. Não interpretar
esse parecer como aprovação do dono ou como ordem de mudar a guarda/moveset.
Durante dependência de decisão, continuar portraits/estados independentes já
previstos. Não passar a outra ação como pretexto para esconder o problema, nem
paralisar o pacote inteiro num ajuste indefinido de poucos pixels.

#### Armadilhas já investigadas — poupe as próximas tentativas

- O adaptador aceita razões extras configuráveis, não só 1/1 e 4/6. A receita
  atual aplica encaixe CPS2→SMS 2/3×6/7, **depois** extra 7/9. Não equivale a
  escala direta 35/52. Guarda chegou a 69 px; não reduzir o GDD para 60 px.
- GQ02 coube, mas nasceu de shear por linha em script: **somente diagnóstico**.
  Não alimentar autoria com sua anatomia. GQ03 é a alternativa autoral candidata.
- J01 largo, BC04 e alternativas 69/71 px já foram medidos. Os conflitos de BC04
  incluem haste/casaco e sola; não declarar só “arma longa demais”. Separar arma
  em objeto não aumenta o limite por linha. Rapieira em 256×128 não pode ser
  cortada para caber num canvas arbitrário.
- Pico 8 é zero folga nas linhas saturadas. Ken de construção não é o elenco;
  possui proporção/altura diferentes. Transladar o grupo em X com mesmos Y não
  é nova prova de orçamento; clipping/cantos exigem runtime próprio.
- Ponta alta da bengala gerou bastão dourado/cabo na ponta: tentativas rejeitadas.
  Não repetir essa instrução sem hipótese de atuação que preserve a arma.
- TA07 antiga era escura/virada na fonte e não está no ciclo atual. Preservá-la
  no histórico não é incluí-la no runtime. Diferença 56/57 de ciano não é defeito
  automático; mudança perceptível de material/iluminação precisa revisão.
- Não normalizar cada quadro para a mesma bbox: isso pode apagar inclinação e
  fazer o corpo crescer. Transformação comum também não corrige deriva entre
  gerações; usar âncoras e autoria coerentes.
- Limpeza técnica de fundo/quantização não autoriza desenhar expressão por
  coordenadas. O franzir procedural de sete pixels nas placas versus é estudo,
  não referência de atuação final.
- As quedas de FPS da ROM v2 e posterior passe na mesma ROM permanecem. Não
  escolher só medições favoráveis, nem cortar conteúdo supondo gargalo não isolado.
  O MP4 v2 tinha relógio de reprodução diferente da coleta; distinguir ambos.

#### Trabalho alheio e recuperação de outro agente

Há WIP fora deste lote em `SMS_projects/luta_mugem_rev2` (docs, headers e C),
no consumidor (GDD/spec/TDD/memória/main.c e arquivos Cena 01), e no handoff
central. Confira `git status` atual; não editar, descartar ou incluir no commit
por conveniência. Memória pode conter blocos de owners diferentes: stage apenas
os hunks próprios. O build v3 já existe; não retire ifdefs nem substitua main.c
para reproduzi-lo. Novo build deve preservar WIP, usar manifesto/flags oficiais,
comparar recibo de entradas e manter o binário anterior imutável.

Os originais/prompts/derivados úteis estão no repositório; consulte seus hashes.
Scripts `register_taunt_cycle_v2.py`/`v3.py` usam os JPEGs preservados e
verificam os hashes dos recibos históricos, da guarda e da paleta de J01.
Reproduzem os derivados e recusam divergência antes de recolocar arquivos
ausentes. Os recibos de registro ficam preservados. Siga o
[README do consumidor](../README.md) para gerar o header e compilar o viewer.

Use a ferramenta de autoria visual autorizada disponível à nova sessão,
lendo sua skill. A continuidade exige o método e fidelidade, não acesso à conta
do agente anterior. Se faltar capacidade essencial, relatar exatamente qual e
avançar o trabalho independente; não substituir o artista por desenho procedural.

### 1. Entrada obrigatória e autoridade

Diga **[Contexto SMS Carregado]** antes de propor ações. Leia:

1. `../AGENTS.md`, `AGENTS.md`, `/home/misael/.codex/RTK.md` e
   `tools/sms_wrapper/RTK.md`; procure também instruções locais aplicáveis.
2. `doc/continuity/20261024-start-here.md` e
   `doc/continuity/20261024-next-agent.md` **da raiz SMSForge**. No host já
   preparado, confira o ambiente; não reinstale nem restaure sobre dados vivos.
3. `tools/sms_wrapper/.agent/ARCHITECTURE.md` e
   `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md`, nas versões centrais atuais.
4. No consumidor: `doc/10-memory-bank.md`, `doc/11-gdd.md`,
   `doc/12-roteiro.md`, `doc/13-spec-cenas.md`, `doc/00-diretrizes-agente.md`,
   `.mddev/project.json` e `doc/15-tdd.md`. Memória descreve estado real; GDD
   define identidade/escopo; spec define orçamento de cena; TDD, execução.
5. `doc/dr_social_combat_design_proposal_v1.md` e
   `doc/dr_social_animation_contract_v2.json`. O v1 é histórico onde diverge
   do v2 e das decisões posteriores. Leia também `doc/dr_social_coverage_matrix_v1.json`,
   `doc/character_move_showcase_standard_v1.md` (contrato da cena 10 e parecer
   vigente) e `doc/dr_social_gd01_open_conflicts_for_designer_v1.json`.
   Leia as seções vigentes, não apenas o topo
   de um registro antigo ou o arquivo com maior número no nome.
6. `doc/dr_social_cps2_sample_v1.md`, incluindo os reparos v5 e v8;
   `doc/curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`;
   `doc/dr_social_cps2_sample_independent_review_v8.json` e
   `doc/dr_social_cps2_sample_art_checklist_v8_reviewed.json`.
7. Workflows centrais `original-artwork.md`, `artifact-organization.md`,
   `art-review.md`, `artwork-to-rom-lifecycle.md`; skills centrais
   `sms-sprite-animation.md`, `sms-asset-pipeline.md`, `sms-asset-to-rom.md`,
   `sms-visual-excellence.md`, `sms-pixel-strict-rules.md` e
   `sms-sprites-metasprite.md`, dentro de `tools/sms_wrapper/.agent/`.
   Leia a skill da ferramenta de geração/edição de imagem disponível ao usá-la.

Confira Git/branch/remoto e alterações locais antes de escrever. Preserve o
trabalho alheio de motor, placa de duelo e continuidade. Shell sempre com
`rtk`; use `rtk proxy tools/sms_wrapper/run_host.sh ...`. Fontes/receitas/docs
no Git; builds e evidências nos destinos `out/` do consumidor. Antes de geração
em volume/build, confira disco/RAM/carga. Uma operação pesada/sessão por vez.

### 2. Personagem escolhido e limite da aprovação

Social é o personagem com o **conjunto de ações ofensivas aprovado em design**:
três normais, dois especiais e um Super com três ramos. Isso não significa
combate integral implementado, frame-data fechado ou pacote artístico pronto.
J.J. e Hayato têm amostras aprovadas, não movesets completos equivalentes.

Identidade: investigador/psicólogo humano, adulto esguio e grisalho, metódico,
atento e preciso; óculos de latão, casaco azul/ciano, colete separado, cravat
bordô, luvas claras, botas de couro marrom. Preserve o rosto, biotipo, silhueta,
proporções, roupa e equipamentos das fontes. Cabelo exclusivamente cinza
conforme correções posteriores. Sem corpo de tanque, aparência chibi, poderes
mentais, vampirismo, presas, asas, teleporte ou transformação.

Bengala romba é sua assinatura; rapieira é lâmina de estocada; bumerangue é
objeto de aço. Luva/bota apoiam esse kit. Não adicionar pistola, bomba, faca,
machado ou estaca por constarem em inventário de outra fonte. Rastro violeta
pertence somente ao bumerangue; não transformar toda ação em magia violeta.

Fontes a **abrir visualmente e conferir por SHA**, não apenas citar:

| Papel | Arquivo no consumidor | SHA-256 |
|---|---|---|
| Model sheet aprovado, identidade | `data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png` | `ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644` |
| Amostra autoral atual, seis desenhos do jab | `data/source_art/sprite_studies/dr_social/review_drafts/cps2_sample_v1/jab_revision_v8/jab_source.png` | `877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41` |
| Fonte histórica aprovada de 61 poses, escopo próprio | `res/approved_art/dr_social/dr_social_basic_sequences_61f_cps2_alpha_cel_v08_2_approved.png` | `4e557095dcafd4f11a0369e6e993ad4fa99497ab529509dedd2445f83bcf89d8` |

Decisões: `doc/decisions/dr_social_model_sheet_cps2_alpha_cel_v04_owner_approval.json`
e `doc/decisions/dr-social-animation-source-v08_2_owner_approval.json`.
A v8 tem revisão de fonte/poses-chave; percepção contínua, tradução SMS e
aprovação do dono são eixos separados. As 61 poses são referência histórica
com aprovação preservada, não ordem para abandonar a rota CPS2 atual.
Não retomar v07 rejeitada, v02 bloqueada ou conversões antigas como fonte atual.

Ken/Ryu locais são referências autorizadas de construção/composição e receita,
sem empréstimo de pixels, roupa, anatomia musculosa ou golpes. Não redistribua
seus arquivos privados. Referências externas precisam papel, versão, origem e
hash; não ampliar o escopo de uma fonte aprovada apenas para cores ou ritmo.

### 3. Método aprovado: reaplicar sem congelar seus defeitos

O proprietário aprovou o método em 29/10: “APROVADO O METODO REGISTRE PARA
CURADORIA FUTURA E VAMOS PARA O PROXIMO PASSO”. É aprovação do método no
projeto; não é homologação global nem aprovação automática de cada imagem.

Execute **identidade → intenção/coreografia → poses gestuais → prova temporal
→ fonte autoral limpa → tradução SMS pelo pipeline existente → composição
medida → ROM → evidência e revisão**. Produza uma sequência por vez e prossiga
até cobrir o personagem. Não gere um atlas gigante numa única chamada.

- Use geração/edição de imagem autorizada para autoria visual. Preserve prompts,
  referências, original intacto e revisões. Código pode extrair, registrar,
  converter, organizar e medir; não desenhar o personagem final proceduralmente.
- Primeiro valide linha de ação, apoio, transferência de peso, quadril/tronco,
  ombros e cadeias até mãos/armas. Depois finalize contorno e materiais.
- A fonte CPS2 da amostra usa células 128×128, corpo ereto aproximadamente
  100–108 px, centro próximo de 104 px, cerca de 7,5 cabeças; pivô da receita
  v8 em (64,116). São referências verificadas da amostra, não limites físicos
  universais nem ordem de recortar uma rapieira longa para caber na célula.
- A arte-fonte pode usar mais cores que o SMS: a amostra tem 30 RGBs opacos.
  Não imponha 15 cores à concept ou ao original grande. O derivado de runtime
  precisa da paleta SMS contratada, transparência binária e índices corretos.
- Faça uma escala comum para o personagem e registro por pivô/solo; nunca
  normalize cada pose pela bbox, estique eixo isolado ou encolha só o ataque largo.
- Para edição localizada, entrada nativa ampliada por nearest e extração
  declarada ajudaram o reparo facial v5. Isso não garante edição local: compare
  o delta real de todos os quadros e preserve os que já estavam corretos.
- O contato v8 resolveu sobreposição de células por fase de packing/padding
  transparente compensada no META. Não mudou pixel/escala/pivô visível.
  Estude `.mddev/dr_social_cps2_sample_v8.json` e o adaptador vigente
  `tools/sms_wrapper/prepare_authored_sprite_sample.py`; não copie snapshots
  históricos como outro conversor nem use padding para disfarçar overflow real.
- Efeitos não consertam atuação ruim. Corrija a pose/traçado responsável antes
  de acrescentar smear, brilho ou desenhos. Variação de hold não prova arco ou
  aceleração. Não falsifique movimento com translação de um único desenho.

### 4. Tamanho, qualidade e orçamento

Diferencie concept, fonte autoral, derivado SMS e framebuffer. Tela do jogo:
256×192. GDD mantém alvo corporal em pé de **66–72 px, centro 70**, medido
coroa–sola e separado de arma/capa/cabelo solto. A amostra diagnóstica CPS2 usa
uma receita própria e não fecha esse alvo de produção. Não apresente 104 px da
fonte ou bbox de equipamento como altura SMS aprovada.

Antes de expandir derivados, compare Social com o par atual e as referências
de escala do GDD, em composição real e baseline comum. Registre altura
anatômica, bbox, escala e custo; se receita diagnóstica e alvo GDD divergirem,
explicite a diferença e teste uma transformação comum compatível. Mudança de
alvo/biotipo exige dono; produção de fontes independentes pode continuar.
Nenhuma pose pode ter arma cortada ou membro removido para fechar scanline.

Acabamento: contorno navy consistente, clusters intencionais, planos de
sombra/base/luz por material, luz superior esquerda, rosto/óculos reconhecíveis,
pegas contínuas, bengala romba inteira e rapieira rígida. Sem halo, blur,
dithering ornamental, confete, peças soltas, vazamento de branco/latão ou
textura que destrua a leitura nativa. Reinspecione cada quadro em 1× e 4×
nearest, sobre fundos claro/escuro, e no palco com o adversário.

SMS: 8 sprites físicos por scanline, 64 na SAT; P1 é compartilhada por todos
os sprites e tem até 15 cores úteis + índice transparente. Não atribua 15
cores exclusivas a cada lutador/FX. Paletas de retratos em BG exigem plano da
cena; não herdam automaticamente a paleta da luta. Medir VRAM, RAM/ROM,
residência atual/próxima, upload, scanline e pior VBlank antes de prometer
capacidade. O hardware não fixa número universal de desenhos por animação.

### 5. Cobertura obrigatória do pacote

Faça uma matriz de cobertura vinculada aos IDs de
`doc/dr_social_animation_contract_v2.json`. Cada linha terá fonte, quadros,
tracks, início/fim, ritmo, derivado, evidência e estado de revisão. Não reduza
“personagem completo” à folha de ataques.

**Ações ofensivas — preservar estas funções:**

| ID | Atuação e função a tornar visíveis |
|---|---|
| `social_light_jab` | Direto curto de luva: guarda → carga → extensão → contato → recolha → guarda. Use J01–J06 v8 como referência/controle; não refaça por mero desejo de novidade. |
| `basic_cane_tap` | Toque frontal de bengala para controlar distância média; ponta romba, pegada firme, extensão e retorno legíveis. |
| `social_low_boot_check` | Chute curto baixo com transferência de peso e recomposição do apoio; sem virar lançamento ou varredura longa. |
| `rapier_lunge` | Estocada linear comprometida, impulso e frenagem corporal, lâmina inteira ligada à mão; recuperação após extensão. |
| `boomerang_throw` | Carga, soltura, atuação corporal e recepção/endpoint; objeto com rotação/arco próprios, uma instância; rastro separado e breve. Regra após hit/block e colisão na volta ainda pendentes. |
| `social_read_super_attempt` | Preparação de contra-leitura de bengala, deliberada e reconhecível; espera finita. |
| `social_read_super_hit` | Captura física elegível → desvio → pivô/saque → estocada → recolha. Não criar teleporte, voo ou puxão de rival distante. |
| `social_read_super_whiff` | Tentativa falha e retorno exposto, distintos do sucesso. |

Os três últimos são ramos de **um Super, “Laudo Final”**, que usa barra cheia
individual do medidor comum. Captura alto/médio físico; baixo, agarrão,
projétil, atraso/finta o vencem. `cane_riposte` foi absorvido pelo Super: não
produzir um terceiro especial independente por aparecer no histórico JSON.
Valores de dano, vantagem, alcance, cancel e comandos não são decisão do artista.
Holds de amostra e contagens propostas não são frame-data competitiva.

**Locomoção e estados:** `idle`, `walk_forward`, `walk_backward`, `jump`
(com impulso, voo e aterrissagem), `crouch` (entrada/saída), `dash_run`,
`guard`, `knockdown_fall` e `tech_roll_getup`. A pose idle estática da amostra
não satisfaz sozinha o ciclo idle completo. Complete também a apresentação de
receber hit alto/baixo/no ar, impacto de guarda e guarda baixa, KO/repouso e
retorno, compatíveis com regras existentes. Registre essas lacunas de cobertura
no contrato: são respostas visuais, não novos ataques, invulnerabilidades,
parries, agarrões ou comandos. Não invente comportamento faltante do motor.

**Atuação/encerramento:** `intro_01`, `intro_02`, `taunt_01`, `taunt_02`,
`victory_01`, `victory_02`, `defeat_timeout`, `draw`. Use as intenções do contrato
e do roteiro: investigar, recompor compostura, ajustar óculos/luva, observar
rival/ameaça. Duas variantes precisam encenação distinta, não frames invertidos.
Distinguir KO de derrota por tempo e empate. Final limpo para controle/skip,
sem arma/efeito residual nem buff inventado. Falas existentes são rascunhos.

**Retratos e gráficos de personagem:** `versus_neutral`, `versus_win`,
`versus_loss`; retrato para seleção e derivado pequeno para HUD se exigido pela
cena; bustos de conversa ilustrados, não fotografias realistas. Para conversa,
proponha conjunto mínimo coerente de atenção, fala, suspeita, determinação,
surpresa e alívio, reutilizando variantes que realmente atendam à intenção.
Não são seis novos poderes/personas nem obrigação de seis animações completas.
Dimensões e crop devem ser contratados no layout real da cena 07: rosto, nome,
caixa/texto e palco em 256×192. Preserve cabeça/óculos/figurino entre todos os
retratos e sprites. Não reduzir automaticamente o sprite de luta para criar
portrait nem colocar texto gerado dentro da arte. Expressões precisam funcionar
sem voz; blink/boca animados somente se melhorarem a atuação e couberem no budget.

**Armas/objetos/FX:** corpo, arma acoplada, bumerangue livre e rastro em tracks
coerentes; ancoragem, orientação, origem, lifetime e encerramento documentados.
Separar por responsabilidade, sem duplicar arma no corpo e objeto. Sparks de
hit/guard e sinal comum de Super devem reutilizar o contrato visual comum;
se ausente, preparar proposta identificada, sem impor linguagem global. Smear
ou acento preserva arma/traçado e não acrescenta alcance lógico. Não desenhar
cenário completo, logo, outro herói ou monstro para preencher este pacote.

### 6. Sequenciamento, autonomia e pontos de decisão

Este pedido autoriza **produzir o pacote candidato completo de um personagem**.
A restrição antiga de permanecer somente no primeiro jab não deve reduzir
esta incumbência a outra amostra. Ela continua como referência de risco e
qualidade. Não é autorização para promover todas as imagens nem para saltar
revisão de identidade, orçamento ou aprovação final.

Comece pela baseline e pelo parecer da seção 0, sem retornar à produção inicial.
Depois estabilize chaves novas de bengala/rapieira antes dos intervalos caros.
Faça teste cedo da pose mais larga, rosto e empunhadura na escala SMS; corrija
causas dominantes. Siga em lotes coerentes: ações,
estados comuns, atuação, objetos/efeitos e retratos, reaproveitando o que já
está correto. Não pare no plano, numa única folha ou numa aprovação técnica
parcial se houver produção autorizada independente por concluir.

Para cada sequência, declare estados inicial/final, IDs/contagem de desenhos,
durações provisórias, apoios/traçado, tracks e os 12 princípios de animação;
aplique pelo menos sete com pistas concretas, justificando os demais.
Os números históricos (por exemplo, 8 ou 12 poses) são propostas a conferir,
não uma cota estética. Proponha ajustes motivados antes de inventar movimento
ou mudar uma animação cujo desenho/timing já tenha aceite explícito.

Mantenha as revisões em `data/source_art/.../dr_social/review_drafts/` conforme
registro existente, com IDs e lineage. Não sobrescreva aprovações nem crie
registro concorrente. Nova pasta só para função/revisão real, não “pasta do agente”.
Se faltar decisão indispensável, formule a escolha concreta e siga nas peças
independentes. Não transforme falta de buffer de input/dano selado em licença
para inventar regra, nem em razão para abandonar portraits e animações neutras.

### 6A. Comandos e apresentação — o que o novo agente não pode presumir

GD01/GD02 estão abertos. `doc/dr_social_two_button_proposal_v2.json` contém
**uma proposta, não uma decisão**: 1 jab, baixo/baixo-frente+1 checagem,
2 toque, quarto de lua frente+1 rapieira e +2 bumerangue, 1+2 na mesma leitura
com barra cheia para Laudo Final. A revisão apontou problemas: baixo-trás,
recuo/guarda separados por espera temporal, precisão de uma leitura no Super,
prioridade de quarto de lua+1+2 sem barra, cancelamento de dash e afirmação não
comprovada de que frente-frente já seria comando aprovado de `dash_run`.

O handoff de conflitos está em `doc/dr_social_gd01_open_conflicts_for_designer_v1.json`.
Designer/engenharia propõem, proprietário registra decisões; não transformar
silêncio em aceite. Não reproduzir a tabela proposta como tutorial. Animações
neutras, portraits e viewer diagnóstico podem avançar sem essas decisões.

A direção do dono para **cena 10 — Apresentação de golpes** está documentada:
mostrar nome, execução em velocidade real da luta, controle SMS com D-pad e
botões 1/2, etapas claras de apertar/manter/soltar/simultaneidade quando usadas.
A referência Neo Geo é de clareza/apresentação, não de arte copiada ou quatro
botões. UI deve ter acabamento coerente, fonte/acentos legíveis em 256×192 e
não cobrir corpo/arma/FX/rival. Controle físico não se espelha; setas respeitam
frente/trás relativos. Demonstração futura passa pelo reconhecedor real e usa
os mesmos dados/tempos da luta; não criar tabela paralela de animação bonita.
Enquanto faltam decisões, escrever “comando em definição”. Galeria de revisão
não ensina comando competitivo. Possível item desbloqueável é ideia futura:
sem save, moeda ou recompensas para implementar neste lote.

### 6B. Rota de execução e limites operacionais

- Autoria → registro → `tools/sms_wrapper/prepare_authored_sprite_sample.py` →
  derivados/headers/manifests → viewer em `src/main.c` → build candidato pelo
  wrapper. Consulte `--help`; a interface existente oferece `--config` e `--out`
  no adaptador, `--manifest`/`--build-dir` no build. Use saída nova de revisão
  quando necessário, nunca sobrescreva a baseline ou crie consumidor paralelo.
- Slot 10 inclui o header em
  `out/diagnostics/social_taunt01_cycle_v3_20261101/converted/sample_data.h`.
  Esse arquivo é gerado. Se faltar após checkout, regenerar pela receita e
  conferir hash; não escrever arrays à mão nem usar header de outra versão.
- Toda mudança em fonte/receita/timing/runtime requer vínculo atualizado e
  validação pertinente. Sem mudança, reutilizar prova íntegra do mesmo SHA,
  explicitando o escopo; não repetir gates completos por rotina.
- Uma sessão privada por vez. `emulator_session.py isolated start ROM` cria ID;
  inputs pelo canal oficial em frames, coleta por SHA, fechamento por ID.
  Não reutilizar IDs encerrados, encerrar processos alheios ou usar teclado
  do desktop como atalho. Antes de testes, ler workflows de isolamento.
- Os testes de FPS e pior frame são diferentes. `measure_runtime_probe.py`
  mede janelas funcionais; `measure_worst_frame.py` usa o selo VBlank da ROM.
  O piloto atual sela 3000 frames; amostra depois do selo não é benchmark de
  todas as ações do jogo. Validar instrumentos e mapa de sondas antes de claim.
- Fazer commit/push somente do lote próprio. Na branch registrada, preferir
  refspec completa `refs/heads/codex/host-bootstrap-continuity-20261024` nos
  dois lados do push; o hook já recusou aliases. Não desativar hook ou mudar
  registro para contornar falha. Confirmar SHA remoto sem polling de CI.

### 7. Prova, revisão e entrega ao coordenador

Antes de QA automatizada leia os workflows centrais
`emulator-isolated-session.md` e `subagent-emulator-qa.md`, SMS_GLOBAL §§93–94.
Reutilize pipeline e consumidor, sem editar outro jogo. A conversão/ROM de
revisão é diagnóstica e não promove `res/` de produção. Consulte `--help` dos
comandos vigentes; execute `--self-check` antes de confiar em ferramenta de
medição. Não copie argumentos antigos sem conferir a interface.

Conforme etapa, aplicar gates de contrato/semântica, raster, referência,
proveniência, paleta/recorte/material, harmonia, prova de poses, revisão artística,
metasprite/scanline e vínculo asset→ROM. Os workflows especificam os gates
completos; um PASS estrutural não decide beleza, anatomia ou game feel.
Revisão independente precisa autor real e SHA; nunca assine aprovação em nome
do dono ou do coordenador. Não simule subagentes/pareceres em JSON.

No Emulicious oficial, sessão privada no SHA exato: conferir ambas as faces,
par de lutadores, distância/cantos, objetos e maior carga; entrada manual,
sequência, terminal e nova entrada; portraits com texto/palco e transições.
Capture framebuffer/vídeo e registre limitações. Viewer de poses prova apenas
apresentação: sem motor integrado, hit/block/whiff, balanceamento e experiência
de conversa continuam pendentes, sem fabricar PASS. Se uma parte não puder
ser integrada com segurança, entregue fonte/derivado/contrato íntegros e a
pendência exata; o personagem não estará validado integralmente.

Alvo 60 FPS, piso 58 em cada janela válida sem arredondamento; input, lógica,
apresentação e pior frame precisam ser medidos. Não acelerar emulador, esconder
stalls, cortar arte, mudar testes ou promover contador ISR. Som/áudio de jogo
não são produção deste artista; se não presentes, declarar eixo pendente.

Entregue:

1. Matriz de cobertura sem lacunas ocultas: cada ação/estado/portrait/objeto
   com ID, arquivo, SHA, versão, propósito, dimensões/pivô, duração/tracks,
   status e dependências. Reuso legítimo apontado, não contado como arte nova.
2. Fontes, prompts/originais, lineage, frames individuais e folhas por sequência;
   derivados indexados SMS, receitas de transformação e orçamento medido.
3. Pranchas 1×/4×, comparação de identidade e escala, ciclos em velocidade normal
   e lenta, início/contato/erro/retorno e prova das expressões no layout de diálogo.
   Overlays/guias em painéis separados, nunca sobre pixels apresentados como arte.
4. ROM(s) diagnóstica(s), recibos/SHA, mídia e relatórios da sessão própria,
   inputs observados, falhas/limites e cleanup; sem reusar captura de outro binário.
5. Pacote organizado para o designer revisar identidade, atuação, movimento,
   leitura SMS, equipamento, efeitos, portraits e completude. Indique exatamente
   o que falta para aprovação; não certifique AAA nem personagem pronto sozinho.
6. Memory bank/handoff atualizados e proteção verificável de fontes/evidência;
   commit/push apenas dos arquivos próprios revisados conforme política vigente,
   sem publicar referência privada, ROM/caches ou stage global da árvore alheia.

Ao terminar, **aguarde a revisão do designer coordenador e a decisão do
proprietário antes de iniciar outro personagem**. O resultado esperado é um
personagem completo para avaliação, com distinção explícita entre produzido,
convertido, observado no emulador e aprovado. Nenhuma pendência desaparece por
estar descrita num relatório.
