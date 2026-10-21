Você é o subagente /root/review_qa_contract, faixa visual, independente do produtor /root.
Leia AGENTS.md da raiz, SMS_GLOBAL central atual §§93–94 e workflows/subagent-emulator-qa.md.
Projeto: /mnt/sdcard/Projects/SMSForge/SMS_projects/MSSF2T
Escopo atribuído: MSSF2T title inspection only, existing ROM; not quality/AAA/gameplay approval
Pedido confiável do coordenador: /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-05_native_subagent_qa/visual_request/request.json
ROM congelada: /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-05_native_subagent_qa/visual_request/rom.sms (SHA 71af64d1cad938dd49a45a9d1cf93ae2203d3e80d19b4d1b546120f4a008beb3)

Execute com sua identidade nativa, somente seu output e sua sessão:
rtk proxy python3 /mnt/sdcard/Projects/SMSForge/tools/sms_wrapper/session_qa.py collect --request /mnt/sdcard/Projects/SMSForge/doc/curation/evidence/2026-10-05_native_subagent_qa/visual_request/request.json

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
