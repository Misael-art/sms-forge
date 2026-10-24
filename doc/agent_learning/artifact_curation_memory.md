# Memória operacional — organização de artefatos e aplicação de lições

## 2026-10-10 — L125/L126, SMS_GLOBAL §§115–116

- Entrada de produção/retomada: workflow central `artifact-organization.md`,
  skill `sms-harness-orchestration.md` e ferramenta `artifact_registry.py`.
- Uma autoridade por projeto; catálogo `doc/artifact_registry_catalog.json`.
  Novo projeto recebe registro local; projeto antigo pode ser adotado no central
  sem sobrescrever `.agent`, mover imagens ou duplicar a árvore do personagem.
- Master of Fighters: nove papéis classificados/748 arquivos indexados,
  737 fontes ainda legadas sem aprovação. Fonte61 mantém declaração original
  source-only, prova2 é separada, candidata v10 e review ficam pendentes.
  V5 é histórico. Árvore J.J. aninhada/#13 continuam conflitos explícitos.
- Saídas novas são reservadas pelo coordenador e seladas depois de salvas;
  heads candidata/aprovada separados. Tipos criativos ampliam o mesmo índice.
  O Harness exige registro para visual/planilha explícita de qualquer kind.
  Preflight não é lock/sandbox; QA nativa usa seus pedidos/manifests próprios.
- Source export preflight: `audit_source_raster.py`; casos reais v5 alpha fail,
  v4 somente key-present pass, sem recorte/arte aprovados. Não impor limite SMS
  ao concept bruto; fonte livre e fonte pronta para conversão são distintas.
- Auditoria inicial de 108 lições cobriu todos os registros. Aplicados gaps
  L004/L009/L096, banking/SAT corrigidos sob L001/L069/L117. Mapa atual110IDs em
  `lesson_routes.json`; cobertura/hash exigidos pelo learning capture, sem
  transformar roteamento em domínio técnico comprovado.
- Revisões nativas reais: `/root/curation_coverage`, `/root/artifact_inventory`,
  `/root/harness_forward_test`. Auditorias/forward test são de contratos e
  organização; sem aprovação de arte/jogo nem nova execução de emulador.
- Parecer: `doc/curadoria-harness-arte-2026-10-10.md`. Curadoria JSON:
  `doc/curation/2026-10-10_l125_l126_harness_artifact_and_raster.json`.
  Evidência: `doc/curation/evidence/2026-10-10_harness_artifact_curation/`.
- Fechamento integral em `closure`; doc sync global permanece condicionado
  à legibilidade dos documentos Mugen. Nada foi commitado.
- Fechamento: selftest108/108, 65 ferramentas com self-check, learning capture,
  hardware doctrine e registry real passaram. Build probe opcional não rodado.
  Doc sync reconhece AGENTS + lei central sempre ativa; reteste mantém dez
  problemas documentais Mugen. Resultado inicial e focused reteste preservados.

## 2026-10-13 — coesão e qualidade conjunta, sem novos IDs

- 113 lições/rotas atuais revisadas. Aplicadas L003/L006/L128/L129 ao schema,
  packer e simulador strict; L013/L035 ao FPS regional; L078–L081 ao PSG;
  L124/L127 aos escopos revisados de edição, máscara/franja/ownership/contorno.
- Rota transversal: product-quality-checkpoint.md. Público/GDD, reação/impacto,
  leitura de poses, mix/SFX, IA/HUD/FX e worst-frame da mesma cena. Review de
  agente não é aceitação de mercado. Média de contador não prova deadline.
- Fonte v08.2 decision/fileSHA conferidos; memória/método/registry divergentes
  registrados como reconciliação central sem promover runtime. Nenhuma ROM
  v08.2 encontrada, nenhuma imagem/PSG de projeto regenerada.
- Ruído bit2=1 branco,0periódico; doutrina antiga supersedida com histórico.
  Rootgerador pitchdivisor32; previews aproximados;36PSGpreservados,11M4fail
  apóscorreção. GeradoreslocaisPulso/MSSF2T migração ainda pendente.
- Coletor atual mediu fixtureNTSC59,52/59,72FPS em2janelas8s; sessão própria
  1815a215835b47a2bdbcb852979e54c2 encerrada. PAL apenas controle sintético.
  Não é FPS de jogo alvo. Evidência em2026-10-13_quality_cohesion/native-fps-current.
- Relatório doc/curadoria-qualidade-coesao-2026-10-13.md; fechamento em
  doc/curation/evidence/2026-10-13_quality_cohesion/closure. EIO Mugen segue
  aberto; nenhum claim AAA/mercado/hardware. Nada foi commitado.
- Fechamento2026-10-13:113/113selftestfinal,65/65tools,learning/hardwarepass;
  fixtureXfora dobyte corrigida e falhainicialpreservada. Registry27records/
  1176files/1122legacy,371arquivosrecentesindexadossemaprovação. Doc sync
  continua dez problemasMugen; probe opcional debuildnão rodado.

## 2026-10-21 — aplicação de L137/L138 e custódia

- Sem novo ID: propagados perfil O3, composição bilateral, contato orientado
  e terminais de controle/apresentação às skills e workflows em uso.
- Projeção revalida bundle/consumo, métricas/WAV e QA/pedido/sessão/ROM; casos
  aprovados são derivados da cobertura. Saídas existentes e aliases recusados.
- Continuidade exige clone/build com recursos e executáveis preservados;
  snapshot/release não aprova jogo nem restauração em host não exercitado.
- HAMOOPIG reincluído pelo snapshot volta a ser retirado do índice nesta
  branch; cópia de trabalho original e lições históricas preservadas.
- Resultados e limites: `doc/curation/2026-10-21_composicao_projecao_continuidade.json`
  e `doc/curation/evidence/2026-10-21_composicao_projecao/summary.md`.
- Fechamento: selftest124/124, ferramentas73/73, learning capture e doc-sync
  da worktree PASS. No workspace original permanecem dez falhas documentais
  legadas; exclusões não incorporadas. Sem nova execução de emulador.

## 24/10/2026 — host vazio e continuidade

Autoinstalação e restauração seguem `skills/sms-host-continuity.md`,
`host_bootstrap.py` e `restore_handoff.py`; arquivo+manifest único em
`doc/continuity/20261024-mugen-resume.*`. Staging, hashes, saída nova e limpeza
somente de caches próprios. Estado de ambiente não fecha jogo. Diagnóstico
MUGEN 55 itens preservado, sem promover ferramentas limitadas nem engine.
Fechamento:134/134 selftest,75 ferramentas,63+1skip focados e16/16 na fixture
restaurada. Ubuntu vazio compila OpenBOR701379cc e MUGEN6de8c451; setup build
e repetição passam. QA completa recusada por namespaces/Pulse no container.
Xvfb/ponte/pin BlastEm provados no escopo; sem novo emulador ou jogo aprovado.
