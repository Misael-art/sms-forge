# ARCHITECTURE.md — framework .agent do SMSForge

```
.agent/
├── rules/SMS_GLOBAL.md     ← lei canônica sempre ativa (seções numeradas)
├── skills/                 ← conhecimento por domínio (leia o que a tarefa exige)
├── workflows/              ← runbooks passo-a-passo
└── pipelines/              ← sequências machine-readable com gates
```

## Como usar
1. AGENTS.md da raiz é o contrato de entrada; SMS_GLOBAL.md é a lei.
2. Antes de trabalhar num domínio, leia a skill correspondente.
3. Siga o workflow do tipo de tarefa; pipelines definem gates obrigatórios.
   Antes de produzir ou retomar arte, `workflows/artifact-organization.md`
   resolve um registro por projeto, separa candidata/aprovada e reserva saídas
   para o Harness. Tipos criativos ampliam esse índice sem abrir outra árvore.
   Projeto novo ou mecânica nova começa por `workflows/first-playable-slice.md`
   antes de ampliar elenco, fases ou conteúdo final. Pedido de arte autoral
   inicia `workflows/original-artwork.md`; conceito e validação usam
   `workflows/art-review.md`, antes de `new-visual-asset.md` para conversão.
   Use `workflows/artwork-to-rom-lifecycle.md` para os estados e limites de
   promoção entre concept, harmonia do elenco, animação, prova, ROM diagnóstica
   e produção.
4. Erro vira lição via workflow `curation-learning.md`.

## Princípios (herdados do SGDKForge)
- Decisão barata antes de arte cara; medição entre elas.
- Gate executável > confiança verbal.
- `.agent` local de projeto NÃO é sobrescrito pelo central (política de sobrescrita).
- Estado de sessão nunca substitui memory bank/GDD/TDD/evidência.
- Relatório não é entrega: `workflows/causal-persistence-loop.md`.
- Boot ≠ qualidade visual: `skills/sms-visual-excellence.md`.
- Até 3 ramos independentes: `skills/sms-harness-orchestration.md`.
- Review independente nos checkpoints: `workflows/independent-quality-review.md`.
  Experiência conjunta visual/áudio/input/fluidez segue
  `workflows/product-quality-checkpoint.md`: casos da cena real, público/GDD,
  alvo regional, worst-frame e reação observável. Review de agente não valida
  aceitação comercial; nenhuma técnica/fixture certifica AAA.
- Produção contínua: `workflows/production-loop.md`.
- Lição só no ledger é prosa: `audit_learning_capture.py` (§43).
  `doc/agent_learning/lesson_routes.json` liga cada ID emitido a skills/workflows
  atuais por SHA, inclusive correções de lições refutadas. Cobertura do mapa
  não equivale a domínio técnico; revisão independente testa decisões reais.
- Testes automatizados de emulador: `workflows/emulator-isolated-session.md`
  e `emulator_session.py isolated` (L057/L039/L065, §93). Display e controles
  privados; a rota histórica kdotool+ydotool depende do desktop e não isola.
- Diagnóstico complementar por hipótese: `skills/sms-emulator-diagnostics.md`
  e `workflows/blastem-sms-diagnostics.md` (§§108/110). Emulicious é produção;
  BlastEm SMS usa Z80 nativo, watchpoints de mudança RAM, breakpoints CPU nos
  OUT verificados, dumps/visores e APNG/WAVE/VGM diagnósticos. GDB Z2 M68K e
  hook vdpregbreak Genesis não são recursos Z80. `blastem_maintenance.py`
  consulta releases e instala candidatos em paralelo com hashes, sem mudar
  o pin qualificado. `audit_blastem_sms.py` valida consistência do pacote.
- QA por subagentes nativos em qualquer gênero/projeto: fonte central atual
  `workflows/subagent-emulator-qa.md`, `session_qa.py` e
  `audit_subagent_session.py` (§94). Planejamento/coleção não simulam reviewers;
  feedback vem do worker real e cada sessão pertence a um único revisor.
- Tamanho de símbolo e redundância PSG: `audit_symbol_size_sync.py`,
  `audit_psg_redundancy.py`. Não torcer a demo (L053).
- Tradução pixel: `prepare_sms_pixel_art.py` / `sms-pixel-translate.md`.
- Conversão de poses indexadas em metasprites e prova em ROM: `skills/sms-asset-to-rom.md` (L121); integração e entrega continuam separadas.
  Paleta de outro console é régua (L055).
- Arte final de personagem: paleta por papel, limpeza no tamanho de destino,
  geometria por quadro, autoridade das referências, recorte por material e
  harmonia/escala do roster são contratos já medidos (L100–L105); revisão
  anatômica e acabamento de pixel art seguem L106–L107 em
  `workflows/art-review.md` e `workflows/new-visual-asset.md`.
- Runtime de qualquer gênero: provar uma interação jogável de ponta a ponta
  antes de ampliar conteúdo; `workflows/first-playable-slice.md`. O workflow
  `mugen-engine-quality.md` continua uma especialização, não a rota geral.
- FSM e transferências entre telas/rounds: definir owners, teardown e estado
  persistente em `skills/sms-state-transitions.md`; métodos SGDK são adaptados,
  nunca importados como limites ou APIs do SMS.

Números de Mega Drive não entram. Método sim (§32).
Asserts ligados ao journal RAM e intervalos VDP: `skills/sms-observed-case-evidence.md`
e `audit_observed_cases.py` (§128). A rota distingue cache de apresentação,
prazo observado de primeira ocorrência e custódia de interpretação da mídia.
Otimização de runtime: `skills/sms-runtime-optimization.md`, contador na janela
`audit_counter_window.py` (§103); modelo/hipótese e ganho na ROM são distintos.

Engines MUGEN→SMS: `workflows/mugen-engine-quality.md`, pipeline
`pipelines/mugen_fighting_v1.json` e SMS_GLOBAL §68.
Intake/semântica e alcance dos dados: `skills/sms-mugen-source-semantics.md`.
Input/evidência/vídeo/áudio usam as skills atuais de sessão privada (§93),
não roteiros históricos de desktop; `audit_learning_capture.py` detecta
instruções explícitas supersedidas e encerramento global (§101).
