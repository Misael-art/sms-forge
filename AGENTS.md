# AGENTS.md — SMSForge

Convenção de shell portátil: leia `tools/sms_wrapper/RTK.md`. Em host novo,
comece por `doc/continuity/20261024-start-here.md` e pelo bootstrap ali indicado.

> **Ponto de entrada obrigatório para qualquer agente de IA neste workspace.**
> Diga `[Contexto SMS Carregado]` antes de propor qualquer ação.

---

## REGRA FINAL DE FERRO

**"Se não foi visto rodando no emulador, não existe."**
Intenção não é validação. ROM de Master System rodando a 60fps (NTSC) / 50fps (PAL) constantes, sim.

---

## O QUE É ESTE WORKSPACE

Fábrica metodológica de jogos para **Sega Master System** (e família SG-1000/Game Gear por extensão declarada), portada da filosofia do MegaDrive_DEV (SGDKForge). Dois objetivos:

1. Produzir ROMs reais usando **SDCC + devkitSMS (SMSlib/PSGlib)**, validadas em emulador;
2. Impedir que um agente trate "narrativa bonita" como evidência.

Não é um jogo: é a infraestrutura que produz jogos.

---

## FRAMEWORK CANÔNICO DE AGENTES

O framework `.agent` vive centralizado em `tools/sms_wrapper/.agent/`.
Cada projeto recebe materialização local via bootstrap (`tools/sms_wrapper/new_project.sh`).

```
tools/sms_wrapper/.agent/
  ARCHITECTURE.md          ← leia para entender o framework
  rules/SMS_GLOBAL.md      ← lei canônica sempre ativa
  skills/                  ← conhecimento por domínio
  workflows/               ← runbooks operacionais
  pipelines/               ← pipelines machine-readable
```

**Política de sobrescrita: `.agent` local existente não é sobrescrita.**

---

## MENU DE SESSÃO / MODOS DE OPERAÇÃO

Quando o usuário pedir `menu`, `modo`, `iniciar`, `abrir sessão` ou quando a intenção inicial estiver ambígua:

```
[CRIAR NOVO PROJETO DE JOGO DE MASTER SYSTEM] -> create_new_project
[ANALISAR PROJETO EXISTENTE]                  -> analyze_existing_project
[TREINAR AGENTE]                              -> train_agent
[LABORATÓRIO]                                 -> laboratory
[CURADORIA]                                   -> curation
```

Cada modo tem runbook executável em `tools/sms_wrapper/.agent/workflows/`:

| Modo | Workflow | Onde vive |
|------|----------|-----------|
| `create_new_project` | `new-project.md` | `SMS_projects/<slug>/` |
| `analyze_existing_project` | `analyze-existing-project.md` | projeto existente (não altera) |
| `train_agent` | `train-agent.md` | `SMS_projects/_treino/` |
| `laboratory` | `laboratory-mode.md` | `SMS_projects/_laboratorio/` |
| `curation` | `curation-mode.md` | `tools/sms_wrapper/` ou `doc/` |

Regras:
- pedido direto e claro não deve ser atrasado pelo menu;
- troca de modo exige consentimento humano;
- treino vive em `SMS_projects/_treino/`; laboratório em `SMS_projects/_laboratorio/`;
- curadoria só altera `tools/sms_wrapper/` ou `doc/` com aprovação humana explícita + testes + memória atualizada;
- estado de sessão nunca substitui memory bank, GDD, TDD, manifests ou evidência de emulador.

---

## HIERARQUIA DE VERDADE

| # | Fonte | Autoridade |
|---|-------|------------|
| 1 | `doc/10-memory-bank.md` do projeto | Estado operacional real |
| 2 | `doc/11-gdd.md` | Design e escopo ("se não está no GDD, não entra") |
| 3 | `doc/13-spec-cenas.md` | Budget real por cena |
| 4 | `doc/00-diretrizes-agente.md` | Regras de processo |
| 5 | `.mddev/project.json` | Manifesto estrutural |
| 6 | `doc/12-roteiro.md` | Roteiro e diálogos |
| 7 | `doc/15-tdd.md` | Arquitetura técnica |
| 8 | Headers devkitSMS `sdk/devkitSMS/SMSlib/SMSlib.h` e `PSGlib/PSGlib.h` | API definitiva |
| 9 | `sdk/README.md` | Procedimento de toolchain |
| 10 | Suposição / memória | Última prioridade — nunca especular |

---

## RESTRIÇÕES NÃO NEGOCIÁVEIS

```
❌ float/double em runtime quente   — SDCC Z80 faz float em software; use uint8/int16/Q8.8
❌ malloc / free                    — buffers estáticos; RAM = 8KB
❌ Inventar API SMSlib/PSGlib       — header é autoridade #8; verificar antes de usar
❌ >8 sprites numa scanline         — só depois do simulador aprovar
❌ >64 sprites na SAT               — limite físico do VDP
❌ Cor fora dos códigos 6-bit       — paleta mestra fixa; sem "gradiente suave"
❌ >15 cores úteis numa paleta sprite indexada — P1 índice 0 é transparente; BG índice 0 é visível
❌ VRAM em massa fora do VBlank     — sem DMA: orçamento worst-frame medido é contrato
❌ Lógica de build no projeto       — apenas em tools/sms_wrapper/
❌ Declarar "pronto" sem ROM rodando no emulador
❌ Pixel nascido de código como personagem, inimigo, boss ou cenário final
❌ Símbolo visual em res/ sem proveniência declarada
❌ Fechar orçamento sem medir o degrau seguinte — folga não medida é timidez
❌ Usar leitura de ferramenta de medição cujo --self-check não passa
❌ Promover captura de boot técnico a qualidade visual / AAA
❌ Encerrar execução após diagnóstico, relatório ou um único milestone quando ainda houver ramo causal seguro
```

---

## ORDEM DE TRABALHO DE CENA

Decisão barata antes de arte cara. Cada transição tem gate executável:

```
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```

| Gate | Ferramenta | O que reprova |
|------|-----------|---------------|
| Build | `sms_wrapper/build_inner.py` via SDCC + devkitSMS | erro de compilação/link |
| Recursos | `audit_validate_resources.py` | PNG fora do grid 8×8, cor fora do contrato, >15 úteis |
| Sprites/scanline | `audit_sprite_line_sim.py` | >8 sprites/linha, >64 na SAT, colisão com 0xD0 |
| Marcadores de depuração | `audit_debug_markers.py` | variável `__at()` sem `volatile` — o SDCC apaga a escrita e o diagnóstico se inverte (L009) |
| Geometria de sprite | `audit_sprite_mode.py` | arte mais larga que o modo sem metasprite (L006, §25) |
| Contraste | `audit_luma_floor.py` | contraste < 1 degrau efetivo da paleta mestra |
| Procedência | `audit_provenance.py` | pixel nascido de código como personagem/cenário |
| Fronteira de referências | `audit_reference_boundary.py` | fonte de jogo sem papéis explícitos, referência suplementar sem escopo/hash ou mídia externa promovida a identidade, paleta, mecânicas/lore (L103, §88); o gate mede os registros, revisão humana mede fidelidade |
| Recorte e cor por material | `audit_sprite_cutout.py` | componente opaco solto ou RGB incompatível com a região material declarada no contrato (L104, §89); revisar cada quadro também no tamanho nativo e em nearest-neighbor |
| Harmonia do elenco | `audit_roster_harmony.py` | mede altura/largura e relações (L105, §90), registra separadamente revisão visual pass/fail/pending e reprova candidatos com eixo visual `fail`; não classifica anatomia, recorte, clusters ou estilo automaticamente |
| Checklist de revisão artística | `audit_art_review_checklist.py` | exige eixos completos/hash-bound e bloqueia `fail`/`pending` ou falta de aprovação; para sprite sheets também exige micro-eixos de clusters, rosto, contorno, materiais, encaixes, equipamentos e integridade de quadros (L106–L107, §91–§92); valida cobertura, não verdade artística |
| Silhueta na composição | `audit_silhouette_integrity.py` | ataque do jogador >5 células nas linhas 1–2 (ceifa cabeça/tronco do inimigo), inimigo em pé <2 em cada linha crítica ou <5 no total, jogador <3 nas linhas 1–3 (L137, §129); mede células emitidas, não a ROM — QA viva lê SAT/`ec` no SHA e revisa o framebuffer |
| Prova técnica de poses-chave | `audit_asset_proof_sheet.py` | exige poses idle+ação, refaz transform nearest-neighbor declarado, confere previews pixel a pixel contra PNG convertido, exige canvas em tiles de 8×8 e borda transparente mínima, bloqueia arma/conteúdo tocando a borda, grade/overlay, paleta runtime inconsistente ou eixos ausentes para terminal e altura anatômica separada de equipamento (L109–L111, §§105–107); não julga anatomia, identidade visual, orçamento de runtime ou AAA |
| Proveniência de áudio | `audit_audio_provenance.py` | .psg sem entrada no manifest de áudio, sha256/bytes divergentes, faixa portada sem referência hasheada (L058, §47) |
| Evidência | `capture_evidence.py` | captura branca/sem informação, emulador ausente |
| Sessão do emulador | `emulator_session.py` | instância zumbi viva quando um gate vai buscar a janela por nome — sem isso o gate mede a ROM **errada** e emite veredito confiante sobre a sua (§46/L057) |
| Corredor de sondas | `audit_probe_corridor.py` | símbolo não-ABS do `.map` caindo dentro do corredor `__at` (a biblioteca escreve onde a sonda mora e o detector mente bonito) — exige folga medida entre topo do DATA/fim das variáveis e a base do corredor (L089) |
| Diagnóstico SMS complementar | `blastem_sms.py` + `audit_blastem_sms.py` | BlastEm privado para estados Z80/VDP/mapper; pin/SHA/dumps/relógio/cleanup; não promove stepping, CRAM interna ou aceitação MD a FPS/áudio/hardware SMS (L112, §108) |
| Diagnóstico BlastEm avançado e manutenção | `blastem_diagnostics.py` + `blastem_maintenance.py` | mudança RAM/OUT com opcode vivo; APNG bruto/derivado, PCM/VGM íntegros e visores SMS; candidato paralelo/hash divergente bloqueado; GDB Z2 M68K não vira suporte Z80 (L114–L120, §110) |
| Diferença entre estados SMS | `blastem_dump_diff.py` | snapshots auditados e labels da mesma ROM; delta líquido não vira escrita/transferência, blocos VRAM não viram tiles únicos de arte (L112/L120, §§108/110) |
| Evidência de estado transitório | `capture_video.py` | grava o **framebuffer** do emulador (256×192, sem compositor) para transição/animação/game feel, que screenshot não sustenta (§45/§36); reprova vídeo fora da canvas do VDP, curto demais ou de tela congelada |
| Fidelidade de render | `audit_render_fidelity.py` | tela que NÃO mostra a arte autoral (ruído, sprite errado, arte corrompida) — compara a estrutura da fonte com a captura |
| Semântica da captura | `screenshot_semantic_gate.py` | cor fora da paleta mestra (mockup/render), desktop não recortado, reuso da mesma imagem em dois claims, claim que screenshot não prova |
| Frescor da evidência | `seal_fresh_evidence_bundle.py` | artefato **anterior** à ROM (mostra outro binário) ou de outra sessão |
| Conciliação de claims | `reconcile_claims.py` | eixo declarado `true` sem lastro no artefato de evidência, ou evidência de outro binário sem `rom_sha256` da ROM atual (booleano sozinho não conta) |
| Projeção de eixos | `axis_projection.py` | fontes de outro SHA (ou sem SHA) projetando `evidence.json`/`fps.json`; projeção é `assigned_checks_only`, não medição nem delivery |
| Claims | `audit_claims.py` | claim acima do teto aprovado |
| Mudança significativa | `audit_meaningful_change.py` | mudança que não ataca o blocker dominante |
| Boot determinístico | `audit_deterministic_boot.py` | ROM animada sem estado inicial estável |
| Quarentena de placeholder | `audit_placeholder_quarantine.py` | placeholder promovido sem aprovação |
| Fixture canônica | `canonical_fixture_gate.py` | fixture sem escopo ou com claim amplo |
| Áudio (captura) | `capture_audio.py` | grava o áudio **isolado** do emulador (sink dedicado); repete se vier silêncio adiantado |
| Áudio (mix) | `audit_audio.py` | captura de áudio silenciosa/sem sinal; para ROM só-SFX declarar `--active-floor 5` (piso do M8); o default 90% é piso de música e reprova SFX esparso |
| Qualidade musical PSG | `audit_psg_quality.py` | "música" que é metralhadora de 16 Hz: uníssono total, volume estático, ruído periódico como percussão, loop < 2,5 s (L078, L079) |
| FPS (emulador) | `measure_fps.py` | <5 amostras ou fps fora de 50–60 — mede a velocidade de **emulação** relatada no título |
| FPS (loop da ROM) | `measure_frame_advance.py` | contador de frames da própria ROM parado ou em ritmo irregular; o título diria 60fps numa ROM travada (L013) |
| Runtime da ROM (memória) | `measure_runtime_probe.py` | probe sem magic/schema, frame parado, fps fora de 50–60 ou janelas divergentes — lê o estado na RAM via DAP, sem pixels nem foco de janela (L035, §37) |
| Limites e valor da name table | `audit_tilemap_bounds.py` | escrita em linha fora das 24 renderizadas (invisível) ou além da PNT, na SAT (L011); entrada de tilemap com bits 13–15 armados sem `--allow-tilemap-flags "<motivo>"` declarado no TDD (L132, §123) |
| Espelhamento de tilemap SMS1 | `audit_tilemap_mirror.py` | escrita ao reg2 com bit0=0 (mirror invisível no alvo SMS2/PC), sem exceção `--allow-sms1-mirror` motivada; valor não-literal nunca aprovado (L130, §121) |
| Wrap do scroll Y | `audit_vscroll_wrap.py --screen-h` | acumulador/literal de `SMS_setBGScrollY` sem wrap em 224 no modo 192 (tilemap de 224 px; >223 trata como 0..31); modo 224/240 validado contra 256; função/expressão = não provado, nunca aprovado (L131, §122) |
| Mapa de VRAM por plano | `measure_vram_map.py` | região de tiles invadindo PNT/SAT, tile de sprite fora da janela do reg6 (`$FB` 256 / `$FF` 192), name table extra sem motivo, sobra reclamada com guarda violada (`$D0` só em 192; linhas inferiores sem scroll); cross-check `vdp_regs.bin` de sessão contra o plano (L133, §124) |
| Matriz de maestria | `audit_mastery_registry.py` | técnica acima de `mapped` sem evidência |
| Especialização | `audit_specialization.py` | gênero declarado sem lastro no GDD |
| **Ferramentas de medição** | `validate_measurement_tools.py` | ferramenta de medição sem `--self-check` passando (§19) |
| **Grandezas de hardware** | `audit_hardware_constants.py` | número de outro console afirmado como lei do SMS — sprites/scanline, capacidade da SAT, subpaletas, largura da tela, VRAM/RAM, uso de DMA (L001) |
| **Sincronia doc↔repo** | `audit_doc_sync.py` | doc citando gate inexistente, gate invisível na doutrina, hierarquia de verdade incompleta |
| Persistência causal | `audit_causal_persistence.py` | duas falhas equivalentes repetidas; documento sem delta tratado como progresso; representação errada virando gate humano (L036, §38) |
| Época visual / entrega | `audit_visual_delivery.py` | D1/probe/branding/duplicata/escala/HUD promovidos a delivery; boot classificado como qualidade (L036, §39) |
| Vínculo asset→ROM | `audit_rom_asset_binding.py` | source/res/símbolo/SHA da ROM ausentes ou divergentes (L036, §40) |
| Review independente | `quality_review_router.py` | autoaprovação, parecer stale, review declarando AAA (L036, §41) |
| Orquestração | `harness_orchestration.py` | claim/promoção delegados; mais de 3 ramos; worker que promove (L036, §41) |
| QA de subagentes em sessão | `audit_subagent_session.py` | worker sem pedido/ROM/sessão/cleanup, mídia stale, testes omitidos ou contexto novo incompleto/ilegível; `session_qa.py` prepara contexto production/diagnostic explícito (§99); contrato e cobertura, sem julgar qualidade artística (§94) |
| Atribuição de etapa | `audit_stage_attribution.py` | perfil sem baseline, janela declarada, contagens coerentes ou identidade ROM/sessão; consistência de registros, sem autenticar congelamento do probe, duração CPU ou causa exclusiva (§97) |
| Contador na janela | `audit_counter_window.py` | contagem exata sem limite que exclua múltiplas voltas; `--require-exact` bloqueia ambiguidade; mede aritmética declarada, sem autenticar janela/limite/reset (§103) |
| Semântica importada | `audit_import_semantics.py` | coordenadas fora do perfil, AIR finito divergente ou cache stale; `--require-air-identity` exige IDs fonte/ROM em N+1 fronteiras, terminal incluso (§100); consistência de registros, sem provar runtime dinâmico (§98) |
| Animação semântica | `audit_animation_semantics.py` | frames reordenados, ação clonada com outro nome, ciclo idêntico, pivot oscilando, estado do GDD ausente (L037, §42) |
| Contrato de animação | `audit_animation_contract.py` | sequência sem pose inicial/final, track de personagem/objeto incompleto, contagem-fonte inconsistente, menos de 7 princípios aplicados ou custo de hardware tratado como medido (L113, §109); valida cobertura declarada, não pixels ou física |
| Captura de lição | `audit_learning_capture.py` | ledger sem JSON, furo de ID não declarado, ferramenta fantasma, persona ensinando doutrina supersedida (L038–L049, §43) |
| Canal de SFX | `audit_psg_channel_binding.py` | `PSGSFXPlay` em canal diferente do manifesto autorado (L041, §12) |
| H-scroll / 1ª coluna | `audit_hscroll_blank.py` | `SMS_setBGScrollX` ≠ 0 sem `VDPFEATURE_LEFTCOLBLANK` (L043, §6) |
| Tamanho de símbolo | `audit_symbol_size_sync.py` | `#define FOO_SIZE` diverge do array ou entre headers (L052, §44) |
| Redundância PSG | `audit_psg_redundancy.py` | stream com N cópias do mesmo frame; PSGlib já faz loop (L051, §12) |
| Canal de input | `emulator_input.py` | QA automatizada usa `--session ID --script` em frames VDP e controles privados (§93); ACK não prova consumo/ação da ROM; kdotool+ydotool é rota histórica, sem fallback automático ao desktop |
| Tradução pixel | `prepare_sms_pixel_art.py` | foto/conceito fora da paleta mestra; preset NES/SNES/PICO-8 (L055, §8) |
| Worst-frame | `measure_worst_frame.py` | orçamento de VBlank declarado e não medido; derrame sem número (L061, §49) |
| Header↔doutrina | `audit_header_claims.py` | doutrina afirmando lei do SG-1000 como lei do SMS (PNT de 1 byte, "sem flip", 256 tiles) ou §6 sem os valores dos defines do header (L069, §54) |
| Contrato de engine MUGEN | `audit_mugen_engine_contract.py` | perfil de probe promovido, capacidade sem prova/ROM ou técnica sem decisão e fallback (§68/L083) |
| Piloto de escala MUGEN | `mugen2sms/analysis/scale_pilot.py` | idle fora de 72–88 px, pivô espelhado fora da grade/metasprite divergente da máscara, índice/pool/meta de paleta P2 incompatível, current+next acima de VRAM ou stream maior que duração AIR; plano de slots idle não periódico entre voltas (L090); requer `--self-check` e vídeo fresco antes de promover escala |
| Glitch de render | `audit_render_glitch.py` | quadro do framebuffer fora das imagens legais: sprite perdido, tile residual, par trocado, omissão permanente no modo flicker, captura stale (L091, §76) |

## FERRAMENTAS EM CURADORIA (NÃO PROMOVIDAS)

Esta seção existe para **visibilidade**, não para promover ferramentas. As
ferramentas abaixo estão implementadas e com `--self-check`, mas **não entram
na tabela de gates** e nenhum claim pode citá-las como lei da fábrica até
homologação humana explícita.

| Ferramenta | O que mede hoje | Estado | Evidência |
|---|---|---|---|
| `audit_composition_gate.py` | pico por scanline dos intervalos 8×16 do META selecionado; política por ator, sem aprovar o par | revisada em 2026-10-24; diagnóstico limitado, não promovida | `doc/curation/2026-10-24_mugenesis_rev2.md` e pacote PB-13–PB-18 |
| `audit_sole_alignment.py` | `AXIS_y + última linha opaca` contra CLSN2, com hashes PNG/frames/header; não julga anatomia | revisada em 2026-10-24; diagnóstico limitado, não promovida | mesmo parecer de 2026-10-24 |

O lote que as exercitou também fez mudanças **aditivas** em gates já
existentes: `audit_sprite_line_sim.py` ganhou o opt-in
`--require-distinct-fighters`, e `measure_worst_frame.py` passou a declarar
`schema=v2` e `sealed_field=vline_min` (marcando `vline` como snapshot). Esses
dois continuam na tabela de gates; apenas as duas ferramentas novas estão em
curadoria.

Regras desta seção:

- uso permitido é **diagnóstico com `--self-check` antes da leitura**; o
  resultado deve ser registrado no pacote de curadoria, com fonte e SHA;
- o veredito dessas ferramentas **não** substitui gate, validação de orçamento,
  evidência de emulador ou aprovação humana;
- para homologar, o curador deve revisar contrato, testes e evidência,
  decidir se a ferramenta vira gate global ou regra de projeto, e só então
  movê-la para a tabela de gates e atualizar a memória;
- enquanto estiver aqui, a ferramenta pode ser aperfeiçoada ou rejeitada;
  remover a linha também é uma decisão válida de curadoria.

## MODO DE EXECUÇÃO: DESENVOLVIMENTO CONTÍNUO COM PROMOÇÃO ASSÍNCRONA

Runbook: `tools/sms_wrapper/.agent/workflows/async-promotion-loop.md`.

Trabalhe em **lotes verticais**: durante o lote, só testes focados da área
alterada; gates integrais uma única vez no fechamento. **Um push por lote
completo**; registre branch/SHA/run uma vez e **nunca faça polling do CI nem
narre gates longos em loop** — rode-os em background e use o tempo de espera
para o próximo trabalho independente seguro. Relato intermediário:
`Resultado / Bloqueio / Próxima ação`. Assincronia muda **quando** você
olha, nunca **se** mede — a regra final de ferro permanece.

---

## VOCABULÁRIO DE STATUS

```
documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget
```

Gate final de entrega exige os 7 eixos simultâneos: build, validation_report,
boot no emulador, gameplay, 60/50 fps, áudio, memory bank atualizado — **e**
época visual `delivery` com vínculo asset→ROM pago. Boot sozinho classifica
`runtime_probe_passed_visual_epoch_failed`. Relatórios são transições de
produção, não entregas finais (`causal-persistence-loop.md`).

---

## QA EM QUALQUER PROJETO

Antes de testes automatizados, leia os workflows centrais atuais
`tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md` e
`subagent-emulator-qa.md`, SMS_GLOBAL §§93–94. QA por subagentes usa a ferramenta
nativa, uma sessão privada por worker e feedback com cobertura/evidências;
`session_qa.py` prepara/coleta e `audit_subagent_session.py` valida o resultado.
Novos pedidos V2 seguem §§95–98: snapshots de contexto, relação independent
(um caso em sessão nova) ou chained (timeline cumulativa), baseline/precondição
da ROM. Integridade histórica não equivale à elegibilidade para a build atual.
O coordenador coteja IDs nativos e consolida; não simular subagentes em JSON.
Aplica-se aos projetos existentes sem sobrescrever suas `.agent` locais.

## APRENDIZADO INSTITUCIONAL

Quando algo dá errado: lição vira JSON canônico em `doc/curation/` +
seção numerada em `.agent/rules/SMS_GLOBAL.md` + ferramenta que mede.
**Regra vira medição, nunca só prosa.** Ver workflow `curation-learning.md`.
