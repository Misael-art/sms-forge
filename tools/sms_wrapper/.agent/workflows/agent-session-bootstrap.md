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

## Seleção de conhecimento por tarefa

Após a leitura obrigatória, carregar somente as skills da decisão ativa.
O alvo vem do manifesto/GDD: SDCC + devkitSMS, sem fallback para outra engine.

| Decisão | Entrada canônica |
|---|---|
| Loop, fases, encontros e dificuldade | `skills/game-design-core-loop.md` → `first-playable-slice.md` |
| Arte nova ou revisão | `original-artwork.md` / `art-review.md` → `skills/sms-asset-to-rom.md` |
| CPU, streaming, SAT e VRAM | `skills/sms-runtime-optimization.md` + `skills/sms-vram-vblank-budget.md` |
| Música e efeitos | `skills/sms-psg-composition.md` → `new-audio.md` |
| Resposta e experiência conjunta | `skills/sms-gameplay-experience-review.md` → `product-quality-checkpoint.md` |
| Técnica experimental | `laboratory-mode.md` + matriz em `doc/05_technical/` |

As rotas são atalhos de leitura, não novas skills instaladas ou execução
automática. `.agent` local existente continua preservada; consultar a rota
central atual antes de aplicar uma cópia histórica.
