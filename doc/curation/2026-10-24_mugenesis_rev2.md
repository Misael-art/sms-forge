# Curadoria Mugenesis → motor de luta SMS, 2026-10-24

Pedido humano desta sessão: analisar o doador Mugenesis, identificar portes
úteis, atuar como curador das skills/ferramentas e preparar as pendências e um
prompt para concluir a engine. A autorização cobre esta curadoria. Owner das
alterações: fábrica `tools/sms_wrapper/` e documentação `doc/`; AGENTS recebe
somente a disposição das ferramentas candidatas. Os jogos foram auditados sem
editar seu runtime, recursos, ROM de produção ou `.agent` local.

## Veredito

O blocker dominante do `luta_mugem_rev2` é **publicar uma apresentação completa
dos dois atores e movimentos exigidos dentro do prazo e do orçamento VDP**.
Há dois problemas separados: geometria de composições acima de 8 entradas por
linha e custo/latência do streaming. Proibir golpes largos não conclui o motor.
Fechar composição também não fecha VBlank.

A engine atual é um consumidor diagnóstico com FSM de papéis, input e combate
parcial; não há demonstração de um compilador CNS completo em C/Z80. A versão
de produção no disco continua `087df676…`, 851968 B, enquanto a candidata
`698e58ed…`, 458752 B, é uma prova limitada com bloqueio de papéis. Nenhuma
das duas reúne os sete eixos de entrega, budget aprovado ou qualidade AAA.

O escopo vigente mantém **fundo sólido em todas as telas**, Ken/Ryu como
pilotos, quatro pareamentos, controles SMS de dois botões e meta regional.
Reutilização autoral é uma capacidade da fábrica a demonstrar com adaptador e
consumidor separado; não amplia automaticamente o conteúdo deste jogo.

## Fontes congeladas e método

- Doador: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/Mugenesis_Demo [VER.001] [SGDK 211] [GEN] [GAME] [FIGHTING]/`.
- Destino: `/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2/`.
- Cópias dos contratos/código consultados e SHA completos:
  [inventário](evidence/2026-10-24_mugenesis/source_inventory.json), subárvores
  `donor/` e `rev2/`. As cópias são evidência de leitura, sem autoridade para
  sobrescrever a origem.
- O estado recente do doador está em `doc/engine_current_state.json`, atualizado
  em 2026-10-24, e no backlog M4; o final do seu memory bank ainda narra lotes
  anteriores. Essa divergência precisa ser conhecida ao usar o doador.
- Auditoria estática, self-checks, calibração em artefatos reais, build em cópia
  isolada e duas sessões novas de Emulicious. Não foi executada novamente a
  suíte SGDK nem medido FPS/áudio do doador. Resultados M4 abaixo são registros
  consultados, com seus limites preservados.

O arquivo `out/build_record.json` do rev2 declara SHA `e697e906…`, divergente da
ROM nominal `087df676…`. `reconcile_claims` passa porque só build e pre-gates
estão declarados verdadeiros. Esse PASS mede coerência dos booleanos que ele
conhece; não resolve a identidade da build nem prova o jogo.

## O que aproveitar do doador

| Método observado | Evidência no snapshot do doador | Adaptação SMS e aceitação |
|---|---|---|
| Separar conversor/runtime/ABI/features | `inc/mg/mg_types.h`; M4 A02/A04 | Contrato neutro, limites de tipos Z80 e C gerado incluindo o próprio header; ABI/feature errada deve falhar na compilação real |
| Geração e instalação recuperáveis | M4 A03/A05/A06; candidatos m4e_003/007/008/009 | Staging com imagens/dados/proveniência/recibos, ancestral instalado e rollback; testar falha, concorrência e pacote fora do checkout. O doador declara limites de atomicidade |
| Personagem/roster por dados | `MgCharDef`, `MgAnimFrame`, `MgState`; M4 A07/A10/C18 | Pacote por slot, lowering AOT do subconjunto alcançável, segundo consumidor sem editar C; não copiar structs 24.8/ponteiros M68K |
| Semântica executável e fidelidade por campo | `src/mg/mg_char.c`, `mg_fight.c`; M4 C01–C09/C16/C17/C22 | Ordem e predicados CNS, AIR/CMD/CLSN, efeitos de controllers e limites explícitos; cada feature passa por fonte→IR→C→ROM; unsupported não vira noop |
| Apresentação com ownership e teardown | `MG_fightHideActors`, `MG_fightEnd`, `MG_fightQueueVisuals`; `fight_pause.c` | Separar simulação e apresentação, invalidar caches ao ocultar/reentrar, restaurar paleta/PNT/SAT/PSG/mapper/input; medir trocas no SMS |
| Input físico separado do lógico | `src/system/input.c`; M4 F03/F05/F08 | Dois pads SMS, supressão até soltura, perfis por personagem e UI derivada do CMD. Seis botões MD não cabem por simples máscara |
| Filas limitadas, expiração e categorias por adaptador | `mg_fight.c`, `src/system/audio.c`; M4 P07/P08/C21/F10 | Pools estáticos; rejeição explícita e contadores; TTL em relógio declarado; catálogo real e vazio seguro. Dimensionar PSG e latência no Z80 |
| Medir otimização com trabalho equivalente | M4 P01/P11/P12/P13/P14 e memória FAST/NONE | Isolar observador/renderer/compressão, parear inputs/carga/SHA e depois medir produto completo; ROM menor ou crop não provam fluidez |
| Transformação identificada e repetível | candidatos m4e_001/008; M4 C12/C13 | Fonte+perfil+saída hasheados; preservar pivô externo, flips e offsets; distinguir regeneração da segunda transformação |
| Segundo consumidor e distribuição independente | M4 A06/A10/C23/Q07 | Rebuild limpo e adaptação autoral usando o mesmo core; incluir dependências/recursos reais, não apenas fixture de instalação |

O doador **não é uma engine final aprovada**. Seu backlog M4 tem 69 itens:
55 `open_acceptance`, 9 `host_acceptance_met` e 5 `scoped_implementation`.
`engine_complete=false`, `best_proven=null`, principal `f225d28b…` com
`source_binding=unknown`; candidata `ddb75ae4…` com runtime observado de escopo
limitado e budget não aprovado. P01 registra controle a 39,812 updates/s e
trace a 28,401; a requalificação a 60 não está concluída. Esses são números MD
registrados, sem extrapolação de capacidade ou performance para o SMS.

Não portar DMA, WINDOW/BG_A/BG_B/VSRAM, PAL0–3, XGM2, compressão SGDK, structs
24.8 indiscriminadas, limites H40, seis botões ou resultados de BlastEm MD.
Portar método, contratos e casos de teste; reimplementar o mecanismo com os
headers SMS e orçamento medido. BG/híbrido continua alternativa a comparar,
sem escolher o backend por autoridade do doador.

## Estado dos sete eixos do rev2

| Eixo | Estado desta análise | Evidência e limite |
|---|---|---|
| build | ROMs existentes e rebuild isolado registrado | `out/curation/20261024_mugenesis/build_snapshot.log`; não substitui release |
| validation_report | parcial | planning do contrato passa; escala e perfil documentais ainda refletem B.2a/72–88 px; não há budget aprovado |
| boot | observado novamente nas duas ROMs | sessões privadas abaixo, capturas nativas; conteúdo presente não aprova a imagem |
| gameplay | parcial histórico; não requalificado aqui | colisão/guard/dano/input têm evidência anterior; especiais/projéteis e fluxo completo não fechados |
| FPS | sem prova atual de meta regional | stepping não mede FPS; ROM/VDP avançam em relógios distintos |
| áudio | pendente | consumidor ativo sem PSG integrado; não houve audição/captura nesta análise |
| memória | lida e congelada; análise nova na memória da fábrica | memória/TDD/contrato/manifest do projeto precisam ser conciliados na execução da engine |

Sessões novas (encerradas; sem captura de áudio, sem FPS):

| ROM | Sessão | Frame VDP da captura / contador ROM | Observação |
|---|---|---|---|
| produção `087df676…` | `e2dcd8e852cb46fab19e19b5bdc44ae5` | 620 / 191 | P1 completo, P2 fragmentado, fundo com padrão repetido; contador acumulado de omissões SAT = 88 |
| candidata `698e58ed…` | `c41656ddb952494e8ecdf62d60740a9e` | 620 / 216 | dois corpos completos em fundo preto no quadro inspecionado; omissões SAT acumuladas = 0; pose desejada difere da residente |

Capturas e RAM/journal:
[emulator_review.json](evidence/2026-10-24_mugenesis/emulator_review.json).
O passo solicitado foi 500 frames VDP depois da preparação da ponte; **não é
frame 500 da ROM**. Não atribuir a esta captura o selo histórico do pacote PB.
O probe `present` registra a política do consumidor, não autentica sozinho a
SAT que o VDP apresentou. `probe_max_line=0` nesta configuração não é prova
de zero excesso: a telemetria correspondente está desativada.

O padrão no fundo da produção viola o contrato visual de fundo sólido no
quadro observado. O código inicializa PNT com tile 255 e o pool de sprites
usa a primeira metade da VRAM. A colisão de residência é uma hipótese concreta
a testar por dump VRAM/PNT/SAT; esta análise não atribui causa exclusiva sem
essa leitura.

O selo histórico da candidata `698e58ed…` foi rehashado no pacote PB:
`vline_min=4`, `vovf_delta=1740`, `done=1`, veredito `derramou`. Dez composições
golpe×idle do mesmo corte dão picos 9–12. O bloqueio diagnóstico retira dez
papéis/25 poses; isso não os torna implementados. O delta correto da última
linha opaca/hurt do Ryu idle F0 é +1, não +2, sem propor correção artística.

## Decisão de curadoria aplicada

Aplicação de lições existentes, sem novo ID e sem renumerar SMS_GLOBAL:
L002/L006/L041/L058/L061/L083/L086/L088–L091/L093–L099/L137/L138. O registro
canônico continua emitido até L138. Não é qualificação de técnica nova SMS.

1. **Composição: diagnóstico mantido; promoção global recusada.**
   Corrigido pico por scanline com intervalos [dy,dy+16), inclusive sobreposição
   de dy diferentes, sinal de dy igual ao runtime e sentinela antecipada.
   Restringidos campos a META/METAL, bytes literais e índice gerado; relatório
   v2 declara seu teto. Proteção de saída existente inclui aliases e rollback
   dos arquivos criados na operação. A ferramenta não mede o par, facing
   dinâmico, cobertura de movimentos, SAT viva, qualidade ou VBlank.
2. **Sola: diagnóstico mantido; promoção global recusada.** Corrigida leitura
   de tRNS: alpha 255 é valor de opacidade, não índice transparente. Alpha
   parcial é recusado. Acrescentados hashes do PNG e frames.json e teto
   `geometry_diagnostic_only`. Saída existente é preservada. Última linha opaca
   não é necessariamente sola anatômica; parser de header e vínculo visual
   completo ainda precisam de qualificação antes de um gate de produção.
3. **Extensões existentes:** `require-distinct-fighters` fica opt-in; espelhos
   legítimos continuam válidos. `measure_worst_frame` v2 mantém `vline_min`
   selado e `vline` snapshot. Não generalizar a ROM anterior a partir do schema.
4. **Skills e workflow:** reforçados source-semantics, runtime-optimization e
   psg-audio com receitas delimitadas do doador; removida dependência operacional
   de `integrada/tools/line_lower_bound.py` no legado com EIO. A regra/medição
   física continua nos gates existentes. `.agent` de projeto não sobrescrita.
5. **Sem promoção do jogo:** produzir o diagnóstico sem slots omitidos é
   diferente de concluir os movimentos/fontes e obter budget/fluidez/áudio.

As candidatas C1–C7 do pacote PB ficam assim: C1 aplicado ao diagnóstico de
residência sob L090/L091/L098; C2 composição nomeada sob L006/L137, opt-in
somente; C3 bloqueio registrado como dívida sob L083/L094; C4 fórmula AXIS
medida sob L086, sem tolerância universal; C5 mínimo selado sob L061/L082/L089;
C6/C7 limites de promoção/custódia sob L036/L138. Não emitir IDs duplicados.

## Pendências e execução

Inventário detalhado, prioridades, dependências, evidência e critérios:
[backlog completo](2026-10-24_luta_mugem_rev2_backlog.json).
Lista legível com todos os 55 itens:
[pendências](2026-10-24_luta_mugem_rev2_pendencias.md).
Prompt pronto para o próximo agente:
[prompt de conclusão](2026-10-24_prompt_concluir_engine_sms.md).

A ordem sugerida começa por identidade da build e renderer/streaming, fecha
um golpe completo e a semântica alcançável, amplia para os quatro pares,
objetos/rounds/HUD/PSG, front-end e depois comprova reuso em outro consumidor.
Testes devem preservar negativos, movimentos exigidos e carga representativa.

Não ampliar para cenário, online, save, elenco extra ou compatibilidade MUGEN
irrestrita para chamar o motor de genérico. O produto robusto declara perfis,
admite/rejeita dados antes do runtime e recupera estados válidos sem esconder
perigo, apagar golpes ou baixar a escala silenciosamente. AAA é direção de
qualidade artística/jogável e aprovação humana, sem veredito automático.

## Validação do lote

Resultados executáveis finais e hashes são registrados em
`doc/curation/evidence/2026-10-24_mugenesis/validation.json`.
A bateria integral é rodada uma vez no fechamento da composição estável;
EIO legado permanece falha, nunca exclusão silenciosa para declarar verde.

- `selftest.py`: **130/130 base verdes**; probe opcional não solicitado.
- `validate_measurement_tools.py`: **75 ferramentas aprovadas** no self-check.
  Isso não constitui revisão semântica integral de todos os instrumentos.
- Regressão focada de composição/sola/simulador/worst-frame: **16 passed**, sem skips.
- `audit_learning_capture.py --root .`: **PASS**.
- `audit_doc_sync.py`: **FAIL**, dez registros do legado `luta_mugen`:
  seis leituras EIO e quatro referências ENOENT, sem falha nova neste escopo.
- Build central em cópia isolada: **PASS**, 851968 B,
  SHA `6de8c451fa39ff49670d242f8a3f3946bf67fea1830566fa4fe901517493b983`.
  Esse rebuild não reproduziu a SHA nominal; a causa não foi atribuída a data,
  toolchain ou fontes sem um experimento pareado. Não foi testado no emulador.
- Sete referências primárias do pacote PB rehashadas: **7/7 coincidem**.
- ROMs e documentos do consumidor conferem com o snapshot inicial; as duas
  sessões próprias ficaram `closed`. Não houve commit/push ou promoção.

Disposição final: curadoria aplicada e testada no escopo declarado;
**fechamento global da fábrica bloqueado por doc_sync legado**. A conclusão
da engine é trabalho futuro do prompt, com os 55 itens ainda abertos.
