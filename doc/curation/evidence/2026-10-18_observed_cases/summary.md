# Curadoria de evidência e produção de jogos SMS

## Resultado

Curadoria aplicada ao agente canônico em 18 de outubro de 2026: oito entradas
de skills/workflows, arquitetura, lei §128, memória e rotas atualizadas.
Foram reaplicadas 16 lições existentes; nenhum ID foi duplicado. O registry
permanece em L136. Código/arte dos jogos e suas evidências históricas foram
preservados.

O objetivo operacional é melhorar as decisões que preservam controle,
legibilidade, qualidade de imagem/som e cadência da cena completa. Nenhuma
ferramenta ou review de agente certifica acabamento AAA ou aceitação comercial.

## Melhorias concretas

| Área | Aplicação |
|---|---|
| Asserts de gameplay | `audit_observed_cases.py` rederiva valores/deltas dos reads originais e intervalos VDP dos ACKs; não confia no resumo do produtor |
| Tempo e apresentação | Skill separa ponte, VDP, lógica e elemento; distingue pose desejada, residente, submetida e apresentada |
| Cache e renderer | Deadlines/idade por ator, residência simultânea do par/FX/HUD, cancelamento e publicação; omissão permanente continua perda visual |
| Hardware | Paleta BG0/sprite0 corrigida na lei/matriz; gate passou a detectar a forma errada observada no acervo, preservando descrições de demanda antes dos cortes |
| VRAM e VBlank | Patterns, PNT e SAT separados; integridade de bytes de L136 não aprova tearing, prazo de commit ou ritmo do jogo |
| MUGEN | Fonte documental para game ticks AIR e CLSN por elemento/Default; bytes no binário não viram execução integral de CNS |
| Saída de relatórios | Quatro auditores usam criação exclusiva, recusando arquivo existente e aliases; `--report-out` e `--json` preservados como opções equivalentes |
| QA e crescimento | Casos negativos/terminal, custódia antes do cleanup e interação completa antes de ampliar elenco/UI; visual, áudio e fluidez julgados juntos |

Auditores migrados para saída exclusiva: `audit_learning_capture.py`,
`audit_hardware_constants.py`, `audit_header_claims.py` e
`audit_debug_markers.py`. Outras CLIs não foram migradas automaticamente.
O caminho de saída de cada nova execução deve ser novo; não apagar fontes ou
evidências para contornar uma recusa.

## Validação

| Verificação | Resultado |
|---|---|
| Selftest do wrapper | 120/120; probe opcional de build de jogo não solicitado/não executado |
| Ferramentas de medição | 70 com self-check passando |
| Captura de lições e rotas | Passou |
| Constantes de hardware e coerência com header | Passaram |
| Calibração em journals OpenBOR M6 | Dois controles coerentes aprovados; “whiff” com bytes de dano recusado |
| Reteste independente da ferramenta | 25/25 vetores, incluindo quatro positivos e 21 negativos |
| Teste independente da skill | Aplicou o gate aos três casos e recusou inferir latência, visual ou aprovação de slice a partir deles |
| Sincronia global de documentação | Reprovou os mesmos dez problemas anteriores do `luta_mugen` com EIO; nenhuma falha nova de referência de ferramenta |

As revisões iniciais estão preservadas. Seus achados de input inválido, PID
booleano, domínio de RAM e deadline sem assert no endpoint foram corrigidos e
retestados. O hash do gate retestado coincide com a implementação final.
Depois do reteste, foram acrescidas regressões dos quatro CLIs ao helper e ao
selftest; a bateria integral final cobre essas adições.

Não houve nova execução de emulador nem medição de hardware nesta curadoria.
A aplicação local está validada; o fechamento global de documentação permanece
bloqueado pelo EIO do legado, sem dispensa do gate.

## Limites e próximos usos

O perfil novo mede RAM e intervalos observados. Não autentica o significado
do layout/probe, não prova pixels apresentados, primeira ocorrência de evento,
FPS ou cleanup. Saldo zero de vida entre endpoints não exclui dano seguido de
cura. O review de vídeo e a validação nativa de sessão continuam necessários.

Hipóteses estáticas de publicação antiga de pose, trajetória TOSS, timers e
hitstop dos jogos permanecem pendentes de reprodução/correção em seus lotes.
Não foram promovidas a técnicas resolvidas. Os consumers usam os novos gates
quando exportam o perfil compatível; esta rodada não migrou todos os scripts.

Registro canônico:
`doc/curation/2026-10-18_runtime_evidence_workflow_application.json`.
Resultados executáveis e logs: `validation/`. Pareceres nativos: `reviews/`.
Exemplos do acervo: `negative_control/`, `positive_control/` e
`contradictory_whiff/`; todos estão limitados aos bytes/deltas observados.
