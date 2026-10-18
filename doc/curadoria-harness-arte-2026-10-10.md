# Curadoria de Harness, arte e aplicação das lições — 2026-10-10

## Resultado aplicado

O framework central agora resolve uma autoridade de artefatos por projeto antes
de criar ou retomar peças. `artifact_registry.py` é índice e preflight, sem
criar outra árvore. O Harness exige destinos reservados para produção visual
e arquivos visuais/planilhas explícitos, independentemente do kind da tarefa.
Necessidades criativas ampliam tipos, procedimentos e variantes no mesmo índice.

Entradas de produção: `tools/sms_wrapper/.agent/workflows/artifact-organization.md`,
`original-artwork.md`, `artwork-to-rom-lifecycle.md` e
`skills/sms-harness-orchestration.md`. O bootstrap de projetos novos inclui
registro local. Projetos existentes mantêm sua `.agent`; o catálogo central
localiza registros adotados sem sobrescrever cópias locais.

## Auditoria do acervo e das lições

- Inventário inicial: 4.679 arquivos no Master of Fighters; 744 em source_art,
  3.795 em out, 18 raízes diagnósticas e 40 arquivos em review_drafts.
- Memory bank aponta v10; fluxo consolidado e lineage mais antigos apontam v5.
  O registro marca v5 como histórico e v10 como candidata; a memória continua
  autoridade operacional. Não reescrevemos relatórios antigos como atuais.
- Existe árvore `SMS_projects/master_of_fighters` dentro do próprio projeto,
  com prompt J.J. diferente do homônimo canônico. Foi preservada e registrada
  como conflito fora das rotas de saída; o gate rejeita repetição desse prefixo.
- 63 registros de curadoria e 77 entradas do ledger iniciais foram auditados:
  108 lições emitidas até L124, descontados 16 furos declarados. Nenhuma
  definição de ID/dedup_key duplicada ou ferramenta citada ausente.
- Três lacunas de aplicação foram fechadas: L004 (ABI/rebuild das bibliotecas),
  L009 (volatile/mapa pós-link/DAP hexadecimal), L096 (trilhas, chaves e caudas).
- Corrigidas duas skills de banking: somente o primeiro 1KiB é fixo no mapper
  Sega; `SMS_mapROMBank` controla slot 2. Corrigida a skill de budget: SAT Mode4
  tem 64 bytes Y e 128 bytes X/tile, com intervalo entre eles; reserva de 256B
  não equivale a quatro atributos por sprite. Patterns são espaço compartilhado
  conforme layout, não pools BG/sprite independentes.
- `audit_hardware_constants.py` agora cobre essas regressões e separa doutrina
  ativa de snapshots históricos em `doc/curation/evidence`. A auditoria focada
  passou após corrigir um falso positivo num README histórico que relatava um
  gate reprovado; o snapshot não foi alterado.

## Registro real adotado

`doc/artifact_registry_catalog.json` aponta a única autoridade de navegação:
`doc/artifact_registries/master_of_fighters.json`. Foram classificados nove
artefatos e indexados 748 arquivos: 744 do source_art mais quatro arquivos
selecionados de reviews/diagnóstico. Dos arquivos fonte, 737 permanecem como
baseline histórico sem classificação/aprovação. `doc/` e diagnóstico têm
cobertura parcial explicitamente marcada legacy; `res/` continua sem promoção.

Fonte original aprovada, prova de duas poses, model sheet candidato, conversão
v10, review pendente e tentativas de jab têm papéis diferentes. A aprovação
source-only existente foi importada do lineage original sem inventar decisão
nova. O adaptador confere personagem, arquivo, hash e escopo literal; não
autentica a declaração. A candidata v10 continua sem aceite artístico.

O registro bloqueia paths/IDs/heads duplicados, SHA stale, aliases por
symlink/hardlink, destinos concorrentes, ciclos e continuidade ausente entre
revisões. `parents` aponta inputs; `supersedes` é continuidade de escolha, não
prova de derivação dos pixels. Preflight não oferece lock ou sandbox; não
classifica finalidade artística nem conteúdo futuro de diretórios genéricos.
QA nativa conserva pedido, diretório privado e manifests próprios.

## Raster e revisão artística

`audit_source_raster.py` valida contrato de exportação contra o arquivo salvo:
hash, dimensões, IDs/slots/retângulos, grade opcional, alpha binário ou chave
opaca presente e teto cromático opcional. Concepts e arte bruta livre não
recebem automaticamente um contrato de 15 cores SMS.

No caso real, jab v5 reprovou por 600.866 pixels com alpha parcial e nenhum
pixel opaco. Jab v4 tem 83.402 RGB e passa apenas o predicado de chave presente,
sem provar fundo uniforme, recorte limpo ou qualidade. Ambos permaneceram
intactos; nenhum PASS técnico remove bloqueio visual. Contagem de slots não
conta desenhos semanticamente diferentes. Anatomia, identidade, clusters,
fluxo espacial da sombra e confinamento semântico das cores continuam nos
eixos e revisões já canonizados por L103–L124.

## Absorção e teste independente

`doc/agent_learning/lesson_routes.json` liga as 110 lições atuais (L125/L126
incluídas) a entrypoints concretos com SHA. `audit_learning_capture.py` exige
cobertura para todos os IDs, rejeita rotas stale/ausentes/duplicadas e alias da
lei como skill. O mapa mede cobertura/frescor, não compreensão nem execução de
cada técnica. Histórico/refutação e limites locais não foram promovidos.

Revisão independente encontrou seis falhas de contratos/caminhos e confirmou
as correções com 21 regressões, mais 29 casos do delta final. Um bypass
adicional por alias ativo para snapshot histórico também foi corrigido e retestado. Outro subagente aplicou a skill em duas sessões:
seis artefatos/18 arquivos, detalhe de pega e comparação de sombras como tipos
novos, mantendo fonte61/prova2/conversão rejeitada separados. Onze negativos
iniciais foram recusados. O forward test encontrou classificação incorreta de
planilhas como escape; após correção, 30 negativos e quatro rotas válidas
passaram. Decisões do exercício são fixtures, não aprovações de arte real.

Evidência preservada em
`doc/curation/evidence/2026-10-10_harness_artifact_curation/`; relatórios dos
subagentes conservam paths originais e resultados anteriores. A cópia não
transforma evidência histórica em elegibilidade para fonte futura.

## Fechamento e limites

O fechamento integral deste lote fica no subdiretório `closure` da evidência.
**108/108 verificações**, **65/65 ferramentas com self-check**, learning capture,
doutrina de hardware e registro real aprovados. Probe opcional de build de
projeto não foi rodado. Doc sync inicial encontrou uma citação invisível:
o gate consultava só AGENTS apesar da ferramenta ensinada na lei sempre ativa.
Após corrigir o lookup para AGENTS + SMS_GLOBAL e retestar positivos/negativos,
o gate mantém apenas os dez problemas documentais do Mugen. O resultado inicial
foi preservado e o reteste está em `closure/doc_sync_final.json`. Revisão
independente desse último ajuste passou em 13 casos, incluindo lei ilegível,
citação duplicada e ferramenta fantasma.
Nenhuma ROM/jogabilidade/arte foi modificada ou promovida neste lote, e não foi
executado novo teste de emulador. Testes de fábrica e organização não sustentam
60FPS, budget, música, animação executada ou qualidade AAA do jogo.

Os erros EIO dos documentos Mugen continuam impedindo sincronização global.
Conflitos #13, árvore J.J. e classificação dos 737 arquivos legados permanecem
declarados para adoção gradual. `sdk/README.md` ainda contém orientação antiga
de openMSX; a rota canônica atual usa Emulicious (§93). O SDK não foi alterado
por esta curadoria restrita a wrapper/doc. Nada foi commitado.
