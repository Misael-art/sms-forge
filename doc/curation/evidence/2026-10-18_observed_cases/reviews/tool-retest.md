# Reteste adversarial independente — correções do gate observado

Data: 2026-10-18. Escopo somente leitura de fontes e testes focados em `/tmp`. Nenhum projeto alterado, build ou emulador. Relatório inicial preservado em `/tmp/curation-20261018-tool-review.md`, SHA `4f58017c551787c0416b74775f3042fb7a43a6b45b3b7731a50edabbbe8c13db`.

## Resultado

**Nenhum bloqueador restante encontrado no escopo revisado.** Os bypasses reproduzidos na primeira leitura foram fechados e os limites de claim continuam explícitos.

- 25 vetores independentes passaram conforme o esperado: 4 positivos aceitos e 21 negativos recusados.
- `audit_observed_cases.self_check()` e `report_output.self_check()` passaram nesta execução independente.
- CLI nova gravou destino exclusivo com hash correto do record e valores/seq/frames dos points; tentar usar o próprio record como destino falhou com rc1 e deixou seus bytes intactos.
- A lista da fase1 de `selftest.py` agora inclui `audit_observed_cases.py`; mantidos os dois controles externos de fase2. Não executei a suíte integral neste reteste.

## Correções confirmadas

1. Input com args vazios, máscara bool, máscara64, ACK divergente ou máscara bool no ACK falha; três masks/ACK coerentes passam.
2. ACK PID bool falha mesmo com metadata PID1; sessão diferente também falha.
3. Deadline sem assert RAM no endpoint, sem âncora input real ou maior que o teto observado falha. O caso101→106 é aceito com teto5: usa delta5, não frame absoluto106.
4. Read abaixo0xC000, len257, bloco atravessando0xE000 e campo atravessando0xE000 falham.
5. Operação desconhecida `load_state`, seq duplicado, frame regressivo e byte RAM bool falham.
6. Multiread no mesmo frame sem operações intermediárias passa; step intercalado que conserva o mesmo frame reportado falha.
7. Endpoint43 contra50 com assert delta0 falha; signed16 little-endian −32768→32767 é decodificado corretamente como diferença65535 (subtração normal, sem wrap disfarçado).
8. Condition string malformada retorna reprovação legível, sem traceback.

## Identidades do reteste

| Fonte | SHA256 |
|---|---|
| `tools/sms_wrapper/audit_observed_cases.py` | `8da7759e7d45eb9e39adcef2d33f30677d3b8527eb7e13fd8f65390167ae17bf` |
| `tools/sms_wrapper/report_output.py` | `ec7316303dbae1b7f44099dacba101d65e129a70eeeb976b669f918a430b422a` |
| `tools/sms_wrapper/selftest.py` | `0f4629492e453b0fe54043f25dbdc72e466ccf17df95e2617057c0ae159917e5` |

Vetor/resultados estruturados e fixtures: `/tmp/observed-retest-1xoqg40j/retest.json` e arquivos irmãos. Os fontes foram lidos em workspace compartilhado; a constatação original sobre ausência na fase1 antecede a correção concorrente, enquanto este relatório confirma a inclusão atual. O hash do selftest colhido ao final da primeira rodada já pode conter essa correção; não usar essa cifra isolada para reconstruir a ordem das edições.

## Limites preservados

O gate rederiva RAM e intervalos observados de ACKs hash-bound. Não autentica a semântica do layout, coletor/probe, ausência de adulteração anterior ao selo, pixels apresentados, FPS, consumo causal exclusivo do input ou primeira ocorrência do evento. A observação tardia pode falhar o prazo de coleta sem provar latência real tardia; delta líquido zero não prova ausência de dano/cura intermediários. Cleanup/native dispatch continuam sob os gates próprios.

Não repeti o dogfood OpenBOR real nesta rodada nem aprovei qualquer ROM/engine. A aprovação é do comportamento dos instrumentos no perfil estreito e nos vetores declarados.
