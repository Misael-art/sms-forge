# 00-diretrizes-agente — openbor_sms_rev1

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
| 2026-10-15 | Doador SGDK-Forge é **read-only**; todo arquivo portado leva banner com SHA-256 do doador; hashes revalidados antes de ler/copiar | reuso saudável sem corromper a fonte; porte auditável | plano `doc/planejamento/openbor_sms/01` + prompt `02` |
| 2026-10-15 | **Nenhuma medição MD do doador vira aprovação SMS**; todo comportamento/custo SMS exige prova própria | contratos de console diferentes; MD ≠ SMS | plano §6 §8 + SMS_GLOBAL (L001) |
| 2026-10-15 | `data/source_openbor/` e `data/generated/` são locations **managed** do registro único, distintas de `res/`; todo arquivo nelas é registrado com SHA-256 | organização de artefatos; intermediário não é recurso de ROM | workflow `artifact-organization.md` |
| 2026-10-15 | Fila de fase é tipada e **não avança saltando evento**: TEXT/ITEM sem owner bloqueiam a fase (fail-closed); retry não duplica entidade | O4/O5 do plano; omissão silenciosa é proibida | plano §5/§6 + prompt `02` |
| 2026-10-15 | Ferramental de intake/import **não exige nenhum path do projeto MUGEN** nem toca mídia com EIO de terceiros; todo caminho é explícito (`--path/--file/--dir`) e validado por hash | gate O0 "sem paths obrigatórios no MUGEN/EIO" | plano O0 |

## Ordem de trabalho de cena (não negociável)
```
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```
Decisão barata antes de arte cara. Gate executável entre cada transição.
O produto OpenBOR inclui cenários/scroll do módulo: fundo neutro é só controle
técnico inicial; mudança visual/escala/paleta que altere identidade exige
decisão e revisão próprias.

## Regras de conversão local (OpenBOR → SMS)
- Vocabulário de feature: `exact`, `adapted`, `blocked`, `dropped_by_owner` —
  com parser, lowering, consumidor, teste e prova por hash.
- `@script` em texto **não é implementação**; script desconhecido alcançável
  bloqueia aceite (nunca noop silencioso).
- `delay` OpenBOR não vira frame VDP por suposição: conversão racional e
  política NTSC/PAL registradas no TDD; fronteira de equivalência declarada.
- Movimento fixado nas dimensões corretas: horizontal do mundo, profundidade no
  chão e altura de salto **separadas**; caixas/ataques usam profundidade,
  facing e frame ativo; sort visual não define colisão.
- Pools/handles estáticos com geração, cleanup e invalidação de alvo/hit.

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
Emulicious é produção/QA SMS; BlastEm complementa diagnóstico RAM/VDP/mapper.
GDB M68K e capturas MD **não** provam nada sobre o SMS.
