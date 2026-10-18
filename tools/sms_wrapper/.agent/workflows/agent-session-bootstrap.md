# workflow: agent-session-bootstrap

1. Diga `[Contexto SMS Carregado]`.
2. Leia `AGENTS.md` (raiz) + `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md`.
3. Se intenção ambígua → apresentar menu de modos (create/analyze/train/lab/curation).
4. Projeto em foco: ler `doc/10-memory-bank.md` do projeto PRIMEIRO.
5. Nunca substituir memory bank/GDD/TDD por estado de sessão.
   Ao criar/retomar visual, aplicar `artifact-organization.md` central: resolver
   papel e ID no registro, confrontar candidata/aprovada com a memória e
   reconciliar divergências antes da próxima escrita.
6. Pedido de produção contínua / "não pare no diagnóstico" →
   `workflows/causal-persistence-loop.md` + `workflows/production-loop.md`.
7. Dois ou mais ramos independentes → `harness_orchestration.py` (máx. 3).
8. Relatório é transição. Depois de registrar, avance a lacuna causal.
9. Lição só no ledger é prosa. JSON + seção + ferramenta
   (`audit_learning_capture.py`, §43) ou não foi capturada.
