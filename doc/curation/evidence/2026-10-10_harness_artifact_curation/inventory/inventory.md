# Inventário somente leitura — Master of Fighters

Projeto: `/mnt/sdcard/Projects/SMSForge/SMS_projects/master_of_fighters`

Arquivos: **4679**; source_art: **744**; out: **3795**; doc: **116**; roots diagnósticos: **18**; root res vazio.

## Achados

### F01 — Estado atual diverge entre três pontos de entrada (high)

Linhas históricas são válidas como histórico; falta um ponteiro ativo único que evite reabrir v5 como se fosse atual. Não é motivo para reescrever a história ou promover v10.

- doc/10-memory-bank.md:12 aponta candidata v10
- doc/fluxo-criacao-curadoria-personagens.md:11,78,86 descreve v5 como atual/próxima revisão
- doc/dr_social_61_pose_source_lineage_v1.json conversion.output_directory e rom.path apontam v5

### F02 — Raiz de path não explícita causou um diretório projeto dentro do próprio projeto (high)

Registrar base workspace/project/record explicitamente e resolver uma única vez. Rejeitar saídas com duplicação literal do prefixo do projeto. Não deduplicar prompts diferentes pelo nome.

- SMS_projects/master_of_fighters/data/source_art/concept_art/jj_zillion_ii/review_drafts/prompts/jj_concept_prompt_v1.txt (relativo ao projeto) existe em árvore aninhada
- O prompt homônimo canônico data/source_art/concept_art/jj_zillion_ii/review_drafts/prompts/jj_concept_prompt_v1.txt possui hash diferente
- Manifesto de estilos mistura catalog.path doc/curation/... (workspace) e model_sheet SMS_projects/master_of_fighters/... (workspace), enquanto source_lineage usa paths relativos ao projeto

### F03 — Seleção de fonte precisa de papel e aprovação no escopo (high)

Registrar ponteiros distintos concept/model_sheet, fonte_animação, prova_conversão, candidata_conversão, ROM_diagnóstica e produção. Nunca escolher por maior versão ou aspecto mais polido.

- data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_owner_source_v1.json: owner_approved_art_source_for_production_conversion; SHA a95fc144...
- data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json: technical_candidate_visual_and_runtime_review_pending
- doc/dr_social_animation_contract_v2.json: fonte owner_source para identidade, v10 somente tratamento visual, model sheet14 candidata

### F04 — Histórico válido e tentativas falhas coexistem em 18 roots diagnósticos (medium)

18 diretórios de diagnóstico não são 18 linhas canônicas. Registry deve reconhecer attempts históricos e um ponteiro ativo v10; preservar descartes e hashes, sem mover/apagar ou chamar toda cópia derivada de duplicação errada.

- dr_social_61_pose_probe_v1
- dr_social_61_pose_probe_v2
- dr_social_61_pose_review_v10
- dr_social_61_pose_review_v3
- dr_social_61_pose_review_v4
- dr_social_61_pose_review_v5
- dr_social_61_pose_review_v6
- dr_social_61_pose_review_v7
- dr_social_61_pose_review_v8
- dr_social_61_pose_review_v9
- dr_social_61_pose_review_v9_first_pass
- dr_social_61_pose_review_v9_generation_attempt1
- dr_social_61_pose_review_v9_skin_anchor_alpha_attempt1
- dr_social_61_pose_review_v9_stale_build_attempt2
- dr_social_61_pose_review_v9_wide_face_attempt
- dr_social_asset_probe_v1
- dr_social_asset_probe_v2
- dr_social_asset_probe_v3

### F05 — Registro de assets de produção não indexa os estudos autorais (medium)

O manifesto de produção vazio condiz com ausência de promoção. Não usá-lo para localizar concepts e estudos. Acrescentar registro de navegação por etapa e ligar ao manifesto de produção quando houver promoção.

- doc/asset_provenance_manifest.json assets=[]
- res/ vazio
- 744 arquivos em data/source_art

### F06 — Ferramentas locais carregam versões e rótulos fixos (medium)

Não executar a ferramenta mais recente pelo nome. Registry/runbook deve declarar script+SHA+argumentos+input/output e distinguir legado de rota ativa. Centralização posterior deve preservar resultados e testar parametrização sem portar cegamente heurísticas do Dr.Social.

- tools/compose_sms_asset_conversion_proof.py defaults v1/96px e renderer antigo
- tools/compose_sms_keypose_proof.py --revision default v2 e texto frame do estudo v9 fixo na linha367
- tools/prepare_dr_social_61_pose_probe.py output default v7/filenames v7
- tools/refine_dr_social_61_pose_semantic_v10.py BASE_V9/V10 e imports locais fixos
- tools/capture_dr_social_61_pose_review.py default v8

### F07 — Catálogo #13 tem conflito já reconhecido (medium)

Registrar conflict/reconciliation_pending. Não promover status por narrativa antiga nem recomeçar gerações até reconciliar evidência.

- doc/10-memory-bank.md:79,81 histórico bloqueado vs manifesto not_started
- doc/dr_social_style_series_manifest_v1.json progress:1 aprovada referência,10 candidatas,3blocked,35not_started

### F08 — Falha raster nova está documentada localmente e pronta para curadoria criteriosa (high)

Prompt e preview não comprovam keycolor ou alpha binário. Registro deve obrigar preflight do arquivo salvo antes de conversão, com grid/poseIDs, dimensões, alfa, cores, base aprovada, tratamento visual e review por frame.

- doc/curation_candidates/2026-10-10_dr_social_sprite_sheet_generation_gate.json
- jabv4 83402RGB; alphaattemptv5 219818RGBA alpha0..254; nenhuma promoção

## Registro central mínimo proposto

`.mddev/artifact_registry.json`: ponteiros e lineage sem mover/apagar os arquivos atuais; não substitui as autoridades existentes.

- stage_routes keyed by role with one output-container and one producer
- approved_sources role-specific separate from active_candidates
- one active candidate pointer per asset/stage/variant with alternatives as versioned attempts
- version bound approvals never inherited by new SHA
- new creative need registers purpose/owner/route/contracts before writes; extends existing asset namespace
- reserve output path before generation and finalize hash after save; no overwrite immutable SHA-bound record

Cada artefato: ID estável, papel, path project-relative, SHA/bytes, inputs com papel+SHA, ferramenta+SHA+argumentos, reviews/evidências, supersedes/attempt_of. Sources aprovadas, candidatas ativas e derivados diagnósticos têm ponteiros diferentes.

A raiz atual mistura workspace-relative e project-relative; a árvore aninhada real é um sintoma verificável. Escolher uma base por referência e impedir dupla resolução. Novas necessidades criativas devem ampliar o namespace registrado antes de gravar, sem criar uma segunda autoridade ou um manifesto paralelo.

## Limites

Inventário e leitura de documentos/código somente; não decodifiquei imagens, não emulei, não rodei testes, não promovi arte. Hashes dos documentos lidos estão em `inventory.json`; hashes de PNGs aprovados são reproduzidos dos registros fonte.
