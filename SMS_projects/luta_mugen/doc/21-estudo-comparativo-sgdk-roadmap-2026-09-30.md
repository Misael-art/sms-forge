# Estudo comparativo MUGEN→SMS vs MUGEN→SGDK e roadmap de assimilação — 2026-09-30

Método: leitura de documentos e código nos dois workspaces. Nada foi
recompilado nem re-medido; números são registros dos memory banks, salvo onde
indicado. Este arquivo **não** altera a hierarquia de verdade: o estado
operacional continua em `doc/10-memory-bank.md`.

## 1. Diagnóstico do estágio SMS

Classe: protótipo técnico integrado (`technical_demo`), não entrega.

Provado (ROM `c958278f…`, Lote C): palco estático, HUD em tiles, PSG, round
manager melhor-de-três fechado por timeout; dois lutadores de 78–80 px a
59,6–59,75 fps NTSC; L091 v2 passa com flicker mínimo aceito (Ryu ainda com
omissões perceptíveis, sem aprovação humana).

Não provado: KO nunca alcançado; chute, caminhada, pulo, hitstop completo e
direções sem medição; PAL; cadência AIR; worst-frame só com um soco que
conecta; especial QCF+B1 sem budget (pool 125/128 pares, SAT 63/64).
Latência do soco P1: pose visível em 26 quadros, hitbox em 125 — não aprovada.

**Lacuna estrutural:** o GDD promete núcleo sem nomes e a "prova do contrato"
(trocar o `.def` sem editar `.c`). `integrada/src/fight.c` tem `ken_states[]`,
`ryu_states[]` e o enum `ST_*` (10 estados) escritos à mão, com IDs MUGEN
fixos. A prova do contrato hoje é falsa. O conversor SMS tem ~1,3 kLOC e 11
arquivos de teste; não tinha matriz de golpes, contrato de tempo nem
comparação de trilhas.

## 2. Comparação

O Mega Drive está à frente em **infraestrutura de verificação**; o SMS está à
frente no **problema de render** (dois lutadores de ~80 px com 8 sprites/linha,
streaming em assembly). O MD também não tem ROM aprovada (16 blockers, teto
`technical_demo`); copiar o método não garante entrega, garante que falhas
apareçam em teste de host.

| Eixo | SMS | MD (Mugenesis_Demo) |
|---|---|---|
| Runtime | `fight.c` 1,1 kLOC, estados hardcoded | `mg_vm/mg_fight/mg_char` ~2,5 kLOC, dados gerados por personagem |
| Conversor | ~1,3 kLOC, 11 arquivos de teste | ~8,5 kLOC, 238 testes, `source_audit` com schema |
| Semântica | gates de render/FPS/glitch | `move_checklist`, `duel_matrix`, `test_anim_time_contract`, `runtime_trace` |
| Palco | 1 tela estática técnica | ~15 módulos `stage_*`, parallax A/B, sem ROM aprovada |
| Paleta | 2×15 sem contrato conjunto P1/P2/FX | `palette_contract` + remap compartilhado medido em ΔE |
| Observabilidade | DAP, sem A/B on/off | `runtime_probe` com A/B, PC sampling |

## 3. Roadmap de assimilação (ordem)

Critério: custo baixo, independente de capacidade do 68000, ataca gap medido.

| # | Iniciativa | Fonte MD | Aplicação SMS | Estado |
|---|---|---|---|---|
| 1 | Matriz de golpes | `move_checklist.py`, `duel_matrix.py` | `mugen2sms/analysis/move_checklist.py`: comando→estado→alcançáveis→fidelidade + suporte ao pad SMS (2 botões, sem diagonal) | **implementado (host)** |
| 2 | Contrato de tempo | `tests/test_anim_time_contract.py` | `mugen2sms/analysis/anim_time_contract.py`: linha do tempo AIR de referência vs modelo do runtime SMS (`tick_anim` + destilação de `dur`) e janela de hit | **implementado (host)** |
| 1b | Mapa de controle por tempo de pressão | (ideia do usuário; sem equivalente no MD, que tem 6 botões) | `converters/sms_controls.py` + `doc/22`: 2 botões físicos × tiers fraco/forte; custo de latência explícito | **proposta implementada (host); aguarda decisão humana** |
| 3 | Trilha de execução | `runtime_trace.py` | `analysis/trace_compare.py`: juiz com igualdade de comprimento, chaves e cenários (o doador usa `zip`, L096). Produtor: ROM clone com gravador por tick + despejo via DAP | **juiz + produtor implementados** (`luta_mugen_trace_dap.py`, L097); só o cenário `soco` foi executado |
| 4 | Estados por `.def` | `mg_ken.c`/`mg_ryu.c` gerados | gerar `StateDef[]` e mapa estado→anim; provar o contrato trocando o 2º lutador. Sem VM em runtime (recusada em 2026-09-25) | pendente |
| 5 | Auditoria de fonte | `source_audit.py` + schema | classes `direct/approximate/manual/unsupported` por recurso; `unsupported` é número | pendente |
| 6 | Contrato de paleta | `palette_contract.py`, `equal_fighter_mean` | contrato conjunto P1/P2/FX na sprite palette única; reaproveitar o método, não os números | pendente |
| 7 | Sonda A/B | `perf/observer_ab.py` | telemetria ligada/desligada em roteiro idêntico; custo do observador | pendente |
| 8 | Palco/HUD | `stage_*`, cache de HUD por bordas | só quando o golden slice pedir arte final; sem parallax antes da cena limpa | adiado |

Não trazer: DMA, 4 paletas, planos BG_A/B/WINDOW, flip de sprite, pools
grandes, `fight_stage_stream` como está (assume DMA; o SMS tem `stream.c`),
classificação de suporte do MD como capacidade do SMS, nem a burocracia de
blockers do MD.

Ordem de execução recomendada: (a) fechar buracos de medição da ROM atual
(KO alcançável, chute, pulo, caminhada, hitstop); (b) itens 1 e 2; (c) item 4
(prova do contrato); (d) só então trocar o Ryu por modelo coerente com o Ken.
A latência de input (26/125 quadros) precisa de atenção própria.

## 4. Itens 1 e 2 — o que foi feito e o que NÃO prova

Implementados como análise de host, com `--self-check`/testes. Medem o que o
**conversor e o modelo do runtime** prometem; não substituem emulador
(`documentado ≠ implementado ≠ buildado ≠ testado_em_emulador`).

Ver resultados e limites no memory bank (seção "Estudo SMS×SGDK — itens 1 e 2").
