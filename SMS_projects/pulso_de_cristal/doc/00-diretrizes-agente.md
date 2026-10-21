# 00-diretrizes-agente — pulso_de_cristal

> Regras de processo deste projeto. Autoridade #4.
> Não duplica a lei global: `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` continua
> sempre ativa. Aqui ficam só os desvios e decisões LOCAIS deste projeto.

## Ordem de leitura obrigatória
1. `AGENTS.md` da raiz do workspace
2. `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` da raiz (fonte central atual)
3. `doc/10-memory-bank.md` (este projeto — estado real)
4. este arquivo

## Regra de ferro
**"Se não foi visto rodando no emulador, não existe."**
Vocabulário obrigatório: `documentado ≠ implementado ≠ buildado ≠
testado_em_emulador ≠ validado_budget`. Nunca pule um degrau na fala.

## Desvios locais aprovados
> Todo desvio da lei global precisa estar AQUI, com data e justificativa.
> Desvio não registrado é violação, não exceção.

| Data | Desvio | Justificativa | Aprovado por |
|------|--------|---------------|--------------|
| — | nenhum até agora | — | — |

## Ordem de trabalho de cena (não negociável)
```
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```
Decisão barata antes de arte cara. Gate executável entre cada transição.

## Ao encerrar sessão
Atualize `doc/10-memory-bank.md` com o estado REAL (não o pretendido) e deixe
handoff explícito do próximo passo bloqueante.

## QA automatizada e feedback independente

Aplicar os workflows centrais `emulator-isolated-session.md` e
`subagent-emulator-qa.md` (§§93–94) ao delta do projeto. Cada subagente nativo
recebe pedido/casos, usa sessão própria, inspeciona mídias/probes e retorna
feedback hash-bound; `audit_subagent_session.py` valida cobertura e vínculo.
Não sobrescrever `.agent` local para receber esta regra. Coleta, build ou
boot não substituem gameplay/qualidade/FPS; casos sem prova ficam `not_run`.
