# 00-diretrizes-agente — luta_mugen

> Regras de processo deste projeto. Autoridade #4.
> Não duplica a lei global: `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` continua
> sempre ativa. Aqui ficam só os desvios e decisões LOCAIS deste projeto.

## Ordem de leitura obrigatória
1. `AGENTS.md` da raiz do workspace
2. `.agent/rules/SMS_GLOBAL.md`
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
