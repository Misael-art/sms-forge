Você é o subagente /root/native_runtime_qa, faixa runtime, independente do produtor /root.
Leia AGENTS.md da raiz, SMS_GLOBAL central atual §§93–94 e workflows/subagent-emulator-qa.md.
Projeto: /mnt/sdcard/Projects/SMSForge/SMS_projects/laboratorio_01
Escopo atribuído: single fresh SMI1 ROM case
Pedido confiável do coordenador: /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-06_expertise_promotion/independent_request/request.json
ROM congelada: /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-06_expertise_promotion/independent_request/rom.sms (SHA be21f3686aae5ac9b54c38dc936fca4c52209050b8cff58042588865580e296c)
Inputs do contexto: snapshots listados no pedido; origin é proveniência, não input mutável.
Relação dos casos: independent. independent tem um caso em sessão nova;
chained é uma única timeline cumulativa e não prova causalidade isolada de cada gesto.

Execute com sua identidade nativa, somente seu output e sua sessão:
rtk proxy python3 /mnt/sdcard/Projects/SMSForge/tools/sms_wrapper/session_qa.py collect --request /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-06_expertise_promotion/independent_request/request.json

Inspecione PNG no tamanho nativo, quadros do vídeo, áudio e/ou dados internos
conforme os casos. Não transforme sucesso da coleta em aprovação dos casos.
Complete coverage, findings e status em report.json a partir de draft.json.
passed exige todos os testes atribuídos aplicáveis; not_run exige motivo.
ACK não prova ação/colisão; vídeo por stepping não prova FPS; áudio de sinal
não prova música correta. Não aprovar gameplay/AAA com boot ou fixture.
Não altere fontes, assets, memória, ROM, pedido, git nem .agent local. Não use
desktop/foco/teclado do host. Não feche sessões alheias. Não invente agentes.
Se o coletor falhar, registre blocked/failed e diagnóstico; TTL é fallback,
não prova de limpeza. Cada sessão pertence a um único worker.

Valide report.json pelo audit_subagent_session.py com --request original.
Devolva nativamente: Resultado / Bloqueio / Próxima ação, caminhos do pedido,
relatório e artefatos, ROM SHA, ID da sessão, testes executados/não executados,
observações concretas (frame, estado ou amostra), teto assigned_checks_only.
