# Memória operacional — sessões privadas de emulador

Atualização: 2026-10-05. Autorização: pedido do dono para adaptar e implementar
o isolamento do plano SGDKForge no SMSForge. Escopo: fábrica e documentação.

## Curadoria — 2026-10-08, §§103–104

- Novo audit_counter_window.py verifica unicidade de delta sob limite declarado.
  Byte155→184 é29mod256; não é incidênciaexata sem excluir outras voltas/reset.
  Com limite358 há candidatos29/285. Gate não autentica limite/janela/ROM.
- Nova sms-runtime-optimization.md preserva baseline, carga, invalidação,
  custo fallback, incidênciaativa e tetos: VCounter não éCPU, controles
  renderer-off/P2passivo não aprovam o jogo. Trials drawfast/drawdirty continuam
  rejeitados; slots SATmodelo estático continua blocked/not_run.
- Concept model sheet exige document_and_layout; N/A não é dispensa. L108
  evidence.validator_self_check alinhado ao gate atual, sem novo ID.
  Calibração DrSocial14v3: cobertura/hash íntegros, promoção continua pending.
- Registro doc/curation/2026-10-08_runtime_counter_layout.json e snapshots
  próprios. Selftest95/95, instrumentos55/55, learning capturePASS; review nativo
  passed_with_limits. Doc_sync globalFAIL pelos10registros luta_mugen.
  RegistryL108 permanece; nenhuma promoção global de produto.
  Não executou ROM nova nem recuperou docsMUGEN afetados.

## Propagação às skills — 2026-10-07, §101

- Skills de evidência/input/luta/vídeo/animação/áudio e release-rom agora ensinam
  sessão privada, roteiro VDP, cleanup por ID, consequência ROM e limites de
  vídeo stepped. Legado é histórico; orientação de encerramento global removida.
- `audit_learning_capture.py` detectou sete instruções supersedidas antes da
  correção; selfcheck cobre positivo/negativo e proibição sem falso positivo.
  Gate textual mede frases reconhecidas, não semântica completa.
- Nova `sms-mugen-source-semantics.md`: DEF/SHA, parse/generated/consumed/runtime,
  perfis próximos/distantes e sua ordem/limitações, fronteira racional, AIR com
  IDs, states vs actions, hold/loop local, expressões e pacote RAR delimitados.
- Suíte focada importer 45/45; nenhuma nova execuçãoROM nesta rodada. README e
  manifests acessíveis são evidência offline específica; docs MUGEN seguem EIO.
- Curadoria `doc/curation/2026-10-07_skills_propagation.json`: selftest90/90,
  instrumentos54/54, importer45/45 e learning capturePASS. Review nativo final
  passed_with_limits; doc_sync globalFAIL por leituras luta_mugen. Sem claim
  de produto; IDs existentes reaplicados, registryL107. Export real Ryo221 é
  source-only: cinco elementos/seis IDs e nenhum timestampROM.

## Curadoria — 2026-10-07, §§99–100

- Contexto novo `readable_project_context_v1`: production exige memory/GDD/spec/TDD;
  diagnostic exige motivo e ausências ENOENT explícitas. EIO/EACCES/UTF8 inválido
  ou texto vazio abortam antes de abrir sessão. Histórico íntegro continua
  auditável, mas pedido V2 sem contrato não pode ser coletado novamente.
- `air_identity_timing` e `--require-air-identity` exigem IDs fonte/ROM por N+1
  fronteiras, terminal incluso. Permutação com durações iguais reprova; rollover
  finito válido passa. Trace real action221 permanece duração apenas, sem IDs.
- `luta_mugen/doc` retornou EIO nos quatro documentos essenciais. Projeto atual
  não pôde ser curado integralmente; nenhum arquivo afetado foi reescrito e
  nenhuma recuperação de armazenamento foi tentada.
- QA usa fixture SMI1 arquivada e sessão privada. Primeiro parecer encontrou
  descrição errada de offsets no TDD diagnóstico; pedido histórico preservado,
  contexto corrigido e coleta nova. Contrato mede bytes, revisão mede semântica.
- Registro: `doc/curation/2026-10-07_context_air_identity.json`;
  evidências em `doc/curation/evidence/2026-10-07_context_air_identity/`.
- Fechamento: selftest 88/88, instrumentos 54/54, learning capture PASS;
  revisão independente passed_with_limits e dois casos diagnósticos nativos
  PASS, sessões encerradas. Doc sync global FAIL (10 registros em luta_mugen,
  com EIO/ENOENT observados); promoção global bloqueada. Sem aprovação de
  gameplay, FPS, ausência de flicker ou AAA. Registry continua L107.

## Curadoria de expertise — 2026-10-06, §§95–98

- Novos pedidos `session_qa.py prepare` são V2: snapshots de ROM/memory/GDD/TDD
  com origem/roles e hash próprios; auditoria histórica não depende do caminho
  ativo. `--current-rom` separa elegibilidade da build atual. V1 permanece
  histórico, sem alterar SHA, mas não pode ser coletado como pedido novo.
- `case_relation independent` exige um caso aplicável em sessão nova;
  `chained` é timeline cumulativa. Baseline capturada antes do gesto; guard
  ROM opcional `precondition` compara bytes reais e recusa execução se divergir.
- QA nativa SMI1: caso independente passou, P1 right 7 frames e P2 zerado;
  timeline P1/P2+cauda passou em outro worker/sessão. Baseline deliberadamente
  errada produziu blocked/not_run válido e gesto não executado; strict recusou.
- `audit_stage_attribution.py` exige baseline, mesma janela/ROM/sessão e
  contagens coerentes. Perfis reais v081–v083 passam consistência, mas continuam
  budget FAIL (442/106/106 derrames). Não promover banda/cota como solução.
- Vídeo action220 real: 694 quadros, endpoints iguais, 20 transições com luma
  variável e pico 4,718% contra quadro inicial. `capture_video.py` agora mede
  timeline inteira; contador/HUD mudando não prova ação de lutador ou FPS.
- `audit_import_semantics.py` mede registros fonte/racionais, fronteiras AIR
  finitas de ROM e revisões de cache. Fronteira 45/46 e AIR action221 calibrados;
  cache stale é negativo offline, não implementação dinâmica do jogo.
- Reutilizadas lições existentes; registry continua L107. Documentação/regras
  ensinadas por workflows QA/MUGEN e skills de harness/VBlank. Curadoria e
  evidência: `doc/curation/2026-10-06_expertise_promotion.json` e
  `doc/curation/evidence/2026-10-06_expertise_promotion/`.
- Fechamento deste lote: selftest 85/85; 54 ferramentas com self-check; doc
  sync e learning capture aprovados. Dois casos nativos positivos e um
  controle negativo de baseline, com sessões próprias encerradas. Nenhuma
  promoção de produto, gameplay, 60/50 FPS ou AAA.

## Estado pago

- Implementado e testado em duas ROMs diagnósticas simultâneas: Xvfb privado,
  Xauthority, JVM em Bubblewrap, dois SMSJoypad locais ao processo, input em
  frames do VDP, SRAM/configuração separadas, captura nativa e encerramento
  restrito à sessão. 16 verificações de integração passaram na rodada run05.
- Recebido/aplicado na ponte e observado na ROM são eixos diferentes. A ROM
  registrou exatamente 17/29 frames dos controles enviados em paralelo.
- JAR original preservado; SHA suportado:
  `db185a1ed0af3bdab5ebdeb254612d02d3848bac155dbc89333d1b04e21c371d`.
- Runtime privado preparado em `out/session_bridge/runtime/`; sem instalação
  global. Pode ser recriado com `isolated prepare-runtime`.
- Fábrica: selftest 71/71, instrumentos 51/51, doc sync e learning capture
  passaram. Evidências persistidas em
  `doc/curation/evidence/2026-10-05_emulicious_isolated/`.
- Política KILL global removida do guard e do retry de áudio. Fechar por ID,
  nunca por descoberta de nome/PID. Rota histórica de desktop continua com
  ABORT quando há outra instância; não oferece isolamento.
- Boot agora é muted desde a entrada no emulador; somente zeros primam o
  fluxo, antes de confirmar a rota e liberar som. ROM sonora em mute produziu
  pico 0 no monitor privado; MSSF2T e controle silencioso capturados em paralelo
  por ≥8 s. `audio_acceptance.py` registra os eixos de isolamento em emulador.
- Lição do host: ALSA/PipeWire recria o stream em stop/start/flush. Apenas
  mover antes de desmutar era insuficiente. A ponte mantém a linha aberta,
  descarta o buffer do boot e conserva a identidade do stream nas pausas.
  Manter a linha aberta sozinho reprovou em repetição; keepalive de zeros
  durante mute/pausa passou na rodada seguinte. Mudança da rota recusa avanço.
- Startup Xvfb corrigido: aguardar a linha completa de displayfd antes de
  fechar o pipe; uma leitura parcial seguida de close matou o servidor numa
  rodada concorrente. Logs negativos são preservados na curadoria.
- `close_session` aguarda saída dos processos próprios e exige remoção do
  sink da sessão. A captura usa leitura limitada por prazo e pausa ao terminar.
- Rodada final deste lote: 8 verificações de áudio e 17 de controles aprovadas.
  MSSF2T pico 6012 e controle silencioso pico 0, ambos 8,173 s para 8 s pedidos;
  ROM sonora em mute pico 0 durante 2,229 s. Pacote final e rodadas negativas:
  `doc/curation/evidence/2026-10-05_emulicious_isolated/boot_audio_followup/`.

## Limites e próxima integração

- Sessão tem sink nulo privado; fluxo do PID exato movido antes de `start`
  retornar (`audio_route` no session.json). `capture_audio.py --session` prova
  sinal, exige duração efetiva ≥95% e recusa sem rota. Não prova música certa.
  Não há captura do monitor padrão nem claim sobre políticas futuras do host;
  mudanças do JAR/backend exigem nova prova de compatibilidade e aceitação.
- Ocultação de `/dev/input` e `/dev/uinput` foi observada em cada namespace.
  Hotplug de joystick físico real e comparação completa com referência ainda
  não foram exercitados. Teclas de interferência foram enviadas somente à
  tela de teste; nenhuma digitação foi injetada no desktop do dono.
- Na rodada inicial, a trilha Mugen foi bloqueada pela sobreposição
  `trace_buf C800-D000` com telemetria/caches novos. O produtor exige o gate
  de RAM com fontes **e headers** antes de abrir o emulador. A integração
  posterior moveu a trilha; ver atualização dos consumidores abaixo.
- OpenBOR não tem consumidor localizado neste wrapper. Scripts locais dos
  projetos precisam adotar o ID conforme seus lotes, sem sobrescrever `.agent`.
- FPS medido aqui pertence à ROM diagnóstica. Vídeo por stepping não mede
  throughput. Não há claim de qualidade visual, AAA ou gameplay do jogo alvo.

Plano e prompt: `doc/plano-sessoes-emulicious-isoladas.md`.
Runbook canônico: `workflows/emulator-isolated-session.md`, SMS_GLOBAL §93.
Curadoria: `doc/curation/2026-10-05_l057_sessoes_privadas_emulicious.json`.

## QA nativa em qualquer projeto — §94

- Fonte central `workflows/subagent-emulator-qa.md` obrigatória em cada lote de
  testes, inclusive quando a `.agent` local estiver antiga. Template de projeto
  aponta para a fonte central; cópias locais existentes não foram sobrescritas.
- `session_qa.py prepare/collect` congela pedido/ROM e coleta em sessão própria;
  draft requer inspeção pelo subagente nativo antes de virar report.
- `audit_subagent_session.py` verifica hashes, pedido, cobertura, ROM/sessão,
  mídias e cleanup; `--require-passed` separa relatório válido de aprovação.
  Harness/router integrados; checkpoint recusa outra ROM/projeto/produtor/tasks.
- 3 subagentes reais deram feedback de controles diagnósticos, título MSSF2T
  e sinal de áudio. Reteste de vídeo durante input e falha parcial também
  exercitados. Evidência em `doc/curation/evidence/2026-10-05_native_subagent_qa/`.
- Video deve registrar o gesto durante os comandos; cauda neutra explícita
  cobre reação/recuperação. Fixture observada tem atraso visual de um frame.
- Achado visual falso foi retratado após conferir os mesmos quadros; parecer
  inicial e correção preservados. Gate de vínculo não julga verdade perceptiva.
- Fechamento desta curadoria: selftest 74/74; 52 ferramentas com self-check;
  doc sync e learning capture aprovados. Sete casos atribuídos passaram e
  uma coleta interrompida produziu feedback `blocked/not_run` válido, com
  encerramento próprio; `--require-passed` a recusou como aprovação.
- Migração restante dos scripts segue a matriz de consumidores atual; hotplug
  físico permanece aberto. QA nativa não equivale a promoção automática de
  gameplay, música ou AAA. Relatório: evidência acima, `report.md`.

- Consumidores (2026-10-05): `tools/sms_wrapper/session_consumer.py` é a API para validação automatizada. Migrados: luta_mugen
  `prove_input`/`prove_round_lifecycle`, hamoopig `prove_walk`/`prove_punch`, trilha Mugen. Pendentes e matriz:
  `doc/matriz-consumidores-sessoes-privadas.md`. Duração de golpe = frames; dano do soco chega só no fim da animação.
- Trilha Mugen agora em 0xD200 + canário 0xDA00 (ver curadoria L057, `mugen_integration`).
- `measure_worst_frame.py --session ID`: tempo real sem leituras na janela + uma leitura após o selo; sem DAP. Mugen: pass, vovf_delta=0, vline_min=200, ~57,3 fps médios (atração/IDLE apenas).

## BlastEm SMS complementar — 2026-10-10, §§108/110, L112/L114–L120

- Emulicious permanece produção/QA/FPS real/PAL/áudio final. BlastEm 1.0.0
  Linux64 usa máquina SMS, display/PTY/config/ROM/SRAM privados e áudio dummy.
  `blastem_sms.py` + `audit_blastem_sms.py` vinculam ROM, fonte/helper, baseline,
  dumps, eventos, mídias e cleanup; não reutilizar session ID Emulicious.
- `blastem_maintenance.py` consulta releases, instala candidatos paralelos e
  verifica hashes/arquivos/links. Consulta não troca pin. Tamper real do
  candidato foi recusado e restauração passou; runtime principal conservado.
- Watchpoint nativo de mudança RAM foi observado. Breakpoints de OUT exigem
  PC/opcode congelado e vivo, porta e escopo 0000–03FE. Campo observed_pc pode
  estar stale; campos VDP são estado interno, sem prova de bus/VBlank.
  Watchpoint VDP nativo direto não qualificado; vdpregbreak e GDB Z2 são M68K.
- Subagente `/root/native_audio_qa` fez três sessões atuais: RAM0→8→0,
  contagens2/280/280, APNG120/240, WAVE silencioso2,005s pico0 e sonoro4,011s
  pico4026. Cinco imagens inspecionadas; três auditorias e cleanup passaram.
- APNG bruto tem CRC acTL incorreto; derivado corrige somente o checksum
  identificado e preserva bruto. PCM efetivo/RIFF/data e comandos/EOF/waits VGM
  agora são validados após negativos da revisão independente. VGM silencioso
  omite o silêncio final; WAVE assíncrono não tem alinhamento exato com APNG.
- Visores derivados de paleta/tiles/name table são diagnósticos. Teste64cores
  passou e name table superior128linhas coincidiu com framebuffer da fixture.
  Captura automatizada das janelas nativas Mode4 ainda não foi qualificada.
- `/root/review_qa_contract` corrigiu/retestou cinco achados e fez forward test
  de skill para life/FPS/SFX. Framework/skill/workflow atualizados, sem
  sobrescrever `.agent` dos jogos. Parecer não é aprovação de gameplay/AAA.
- Registros originais e atuais: `doc/curation/evidence/2026-10-10_blastem_advanced/`.
  Avaliação: `doc/avaliacao-blastem-sms-2026-10-10.md`. Encerramento integral
  registrado no subdiretório `closure`; EIO nos docs Mugen continua impedindo
  validar o jogo. Nenhum claim de FPS/fidelidade/hardware real por estas provas.
- Fechamento: selftest101/101 (probe opcional de build não rodado), 61/61
  ferramentas com self-check, learning capture limpo. Doc sync reprova seis
  documentos EIO e quatro referências de autoridade não resolvidas no Mugen;
  promoção global permanece aberta. Três bundles nativos arquivados foram
  reauditados com ROM/helper atuais sem reescrever relatórios históricos.
- Lote seguinte: `blastem_dump_diff.py` mede delta líquido por fronteira e
  labels ROM-bound, sem contar writes/transferências/tiles gráficos. Na sessão
  nativa RAM14bytesativo/5bytesfinal, keys0→8→0. Guarda contra hardlink de saída
  descoberta em review e corrigida com rejeição + escrita atômica. Novo
  fechamento em `closure_diff`, preservando o anterior em `closure`.
- Fechamento do comparador: selftest102/102, 62/62 ferramentas com self-check
  e learning capture limpo. Revisão independente final aprovou o escopo
  focado após retestar hardlink/symlink/corrida e integridade das entradas.
  Probe opcional de build não rodado; doc sync mantém os dez problemas Mugen.
  `closure_diff/summary.json` registra este lote; promoção global permanece aberta.
