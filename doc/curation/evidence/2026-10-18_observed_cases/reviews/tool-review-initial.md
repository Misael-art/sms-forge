# Revisão adversarial — observed cases / saída imutável

Data: 2026-10-18. Escopo: novas implementações `audit_observed_cases.py`, `report_output.py`, quatro CLIs que adotaram o helper e delta de `selftest.py`. Nenhuma alteração ao repositório, build ou emulador. Testes focados autorais executados apenas com fixtures temporários; auditorias dos quatro CLIs foram mockadas ao testar somente o ramo novo de escrita.

## Snapshot revisado

- `audit_observed_cases.py`: SHA `21410e74ca7d2336f73268f3c8fc8d54cdd0919ed8653756e81683adedf818d5`.
- `report_output.py`: SHA `ec7316303dbae1b7f44099dacba101d65e129a70eeeb976b669f918a430b422a`.
- `selftest.py`: SHA `0f4629492e453b0fe54043f25dbdc72e466ccf17df95e2617057c0ae159917e5`.

Os hashes identificam o snapshot anterior às correções que o coordenador possa aplicar após receber estes achados. Parecer inicial: helper de escrita aprovado no escopo testado; gate observado requer os ajustes abaixo antes de promoção.

## Achados reproduzidos

### P2 — Âncora input aceita uma operação impossível no protocolo nativo

Em `audit_observed_cases.py`, o ramo `anchor == "input"` exige apenas uma row com operation `input`. Alterar seus args do fixture bom de `[16,0,0]` para `[]` conserva `ok:true`, inclusive o deadline5. Não há validação de aridade, masks inteiras/ranges, ou seleção explícita da máscara esperada.

Correção mínima: para âncora input, validar a gramática de três masks inteiras sem bool, P1/P2 0..63 e console0..3, e conferir o ACK/expectativa de input quando o contrato do caso declara uma máscara. Não chamar um nome de operação sozinho de injeção válida. Consumo pela ROM continua exigindo probe/caso separado; ACK não prova consumo.

### P2 — Deadline pode passar sem uma observação de evento no endpoint

Remover delta/field_eq do fixture e deixar apenas `eq before.hp==50` mais `vdp_deadline input→after` produz `ok:true`. A regra `ram_checks>0` é satisfeita por uma leitura anterior ao input. Também não há exigência de que `to` seja point de leitura; outro input posterior pode servir de endpoint se houver um assert RAM independente.

Isso mede um intervalo de ACK, mas a mensagem/documentação menciona deadline de input acompanhado de assertions. Para evitar uma promoção indevida a prazo de resposta/evento:

- exigir `to.anchor == "read"`;
- exigir condição RAM no mesmo caso que referencia o endpoint, por eq/field_eq ou delta que termine nele; ou
- separar explicitamente um operador de intervalo puro, sem chamá-lo prazo de evento.

Mesmo com o vínculo corrigido, manter o limite atual: janela de detecção observada não prova primeira ocorrência. Falha por observação esparsa tardia não autentica que o evento nasceu tarde.

### P2 — Perfil journal RAM aceita reads que o bridge real rejeitaria

Converter os reads do fixture para `[0,4]` e os fields para endereços0..3 produz `ok:true`. A validação atual permite até65536 e não limita length256. A gramática primária em `session_bridge/ForgeSMS.java:188` só aceita RAM em0xC000..0xDFFF, length1..256 e address+length<=0xE000.

Correção mínima: alinhar o perfil `journal_ram_v1` ao domínio da operação real, ou declarar outro perfil para outros espaços. A evidência layout hash-bound não torna um ACK impossível válido neste protocolo. Testar também bloco que atravessa0xE000 e length257.

### P3 — Bool passa como PID de ACK em comparação por igualdade

Metadata PID1 é inteiro válido; mudar todos os ACKs para `pid:true` conserva `ok:true`, pois Python compara `True==1`. O metadata passa por `integer`, mas o PID de cada ACK não.

Correção: validar ACK PID por `integer(..., minimum=1)` antes da igualdade. É um bypass de tipo, não demonstra confusão de processos reais nesta rodada.

### P3 — Self-check novo não foi adicionado à fase1 da suíte

O delta `selftest.py` adiciona good/whiff na fase2, mas a lista explícita de `--self-check` da fase1 ainda não inclui `audit_observed_cases.py`. Assim, os negativos de identidade, atomicidade e deadline que existem no self-check podem deixar de rodar na suíte integral.

Correção: registrar o novo self-check na lista existente. Manter adversariais externos da fase2; pelo menos um de atomicidade e um de protocolo não devem depender apenas do fixture positivo do próprio gate.

### P3 / limite a decidir — Operação desconhecida fora dos pontos é ignorada

Acrescentar uma row aceita `operation:"load_state"` no fim do journal, com seq/frame ordenados, conserva `ok:true`. O gate bloqueia `write`/`poke`, mas não possui allowlist de operações do perfil. Não há prova de que tal operação exista no bridge real — precisamente por isso o journal ficaria incompatível com o perfil conhecido.

Recomendação: allowlist das operações atuais e recusa de desconhecidas no perfil versionado; ou registrar explicitamente que o gate não valida o protocolo do journal inteiro. Como a ferramenta já rejeita operações de memória, a primeira opção é mais coerente e barata. Não ampliar a promessa a autenticação do coletor.

## O que passou nesta revisão

- `audit_observed_cases.self_check()` retornou0 no snapshot acima; os fixtures positivos e negativos incorporados passaram. Isso não substitui os novos adversariais descritos acima.
- `report_output.self_check()` retornou0: destino existente, symlink e hardlink não foram substituídos; serialização inválida não criou arquivo; destino novo escreveu JSON válido.
- Nos quatro CLIs `audit_debug_markers`, `audit_header_claims`, `audit_hardware_constants`, `audit_learning_capture`, ambos aliases `--json`/`--report-out` recusaram arquivo existente com rc3 e bytes intactos. Destino novo escreveu corretamente e retornou0. Executei os `main()` com `audit()` mockado para isolar somente esse ramo; não declarei sucesso dos respectivos audits reais.
- O helper serializa antes de `open("x")`; o uso de criação exclusiva protege contra sobrescrita e aliases existentes. Não constatei clobber. Falha de I/O durante escrita ainda pode deixar um arquivo novo parcial: isso não sobrescreve o input e não foi promovido a defeito bloqueante.
- Entrada field não objeto, case ID list, condition string, seq duplicado, RAM inválida e fonte/hash ausente retornam reprovação legível nos casos exercitados. Não foi observado traceback nesses adversariais.
- Multiread em frames distintos ou com operação não-read intermediária é reprovado pelo algoritmo atual. A proteção contra avanço CPU dentro do mesmo frame é conservadora e adequada; não afrouxá-la para exigir somente igualdade de frame.
- Intervalos exigem ordem de seq e frame; inteiros de seq/frame/deadline/width rejeitam bool. Delta RAM é subtração inteira, sem wrap silencioso. O teto declarado não afirma pixels apresentados, FPS ou primeira ocorrência.

## Artefatos temporários dos adversariais

- `/run/user/1000/codex-desktop/tmp/observed-adversarial-review-2_w54yaa/`: fixture e journals de PID bool, args input inválidos, caso sem assert no endpoint e entradas malformadas.
- `/run/user/1000/codex-desktop/tmp/observed-review-extra-qlyh3hcu/`: read fora do domínio RAM, operação desconhecida, fixtures dos quatro ramos CLI e arquivos de saída.

Nenhum dogfood real foi reexecutado por este revisor nesta rodada; o coordenador informou dois registros OpenBOR válidos e um contraditório corretamente reprovado. Os achados acima são testes independentes em fixtures sintéticos, não uma rejeição da evidência histórica OpenBOR.
