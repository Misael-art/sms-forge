# Pacote para o curador — fechamento PB-13 a PB-18

Data: 2026-10-23. Estado: `awaiting_curator`. Este arquivo **não emite ID de lição**.

Escopo: registrar o fechamento medido de PB-13 a PB-18, os dez pares golpe×idle, o gate de composição, a correção da medida da sola do Ryu e o pior quadro. O pedido do dono foi registrar todos os pontos e o aprendizado para curadoria futura. Promoção a lei da fábrica continua sendo decisão humana separada.

`SMS_GLOBAL.md`, `doc/agent_learning/learning_ledger.json`, `doc/agent_learning/lesson_routes.json` e `doc/curation/id_registry.json` não foram alterados. O registro lido nesta data declara `issued_through` `L138`. Não reutilizar `L012` nem a faixa `L020`–`L034`.

Índice machine-readable: `doc/curation/2026-10-23_pose_budget_fechamento_pb13_pb18.json`.

Pacote anterior, que abriu PB-01 a PB-18: `doc/curation/2026-10-23_pose_budget_aguardando_curador.md` e o JSON de mesmo nome.

## Resultado em uma linha

PB-13 a PB-18 foram fechados como lote de medição com a ROM de prova `698e58ed…`: a pose residente foi provada no frame 500, a composição legal foi aplicada pelo gate, a sola do Ryu foi corrigida de 2 px para 1 px, e o pior quadro foi selado depois do fechamento do Ken. O orçamento **continua reprovado**: `derramou`, `vline_min=4`. Status do lote: `testado_emulador`. `validado_budget` permanece proibido.

## Inventário de evidência

Caminhos `out/...` são relativos a `SMS_projects/luta_mugem_rev2/`; caminhos que começam com `SMS_projects/` são relativos à raiz do workspace.

| Peça | Caminho | SHA-256 | Papel |
|---|---|---|---|
| ROM de prova | `SMS_projects/luta_mugem_rev2/out/rom/pose_budget_settled_20261023.sms` | `698e58ed5a0e9256cf2497783b5b0a4343464c15138ce5783c5b9fd98879b13a` | 458.752 B, 24 banks, `LUTA_PROFILE 1` |
| PNG residente | `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/resident_gate_frame500.png` | `7281231d65b1c13494bfa541b5ac792c268471669f73981ac1a9569a1ab4392c` | frame 500, 256×192, os dois corpos completos |
| SAT frame 500 | `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/sat_frame500.json` | `3b436a423f1e1c8dc02f39af84702de4d068e532a67be67c65087c238e939c41` | 32 entradas, 16 por lado |
| Manifesto da sessão | `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/evidence_manifest.json` | `6e12c88db94b8cf8529c0bccd9d9e32f4f96e3ff3d2021c0a5a59d138f87dd9d` | índice consolidado |
| Sessão | `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/session.json` | `ed6b498f732ac2b7c16329786abdce9b4fb5f0c64fa3f6a865d6cf064faac2a3` | `state=closed` |
| Dez pares | `out/logs/pose_budget_settled_20261023/ten_pairs/line_summary.json` | `3bddf292696a6b3c2ca95faef871f76f237437353ede91e0ddacf6f91a4fe70f` | self-check antes da leitura |
| Papéis derrubados | `out/logs/pose_budget_settled_20261023/composition_gate/dropped_from_composition.json` | `e2d047c17fa22eb242eff5d6946bd0c81540003db2077ae6cf98a4ace52d5ee6` | dez papéis, pico e frame |
| Header do gate | `out/logs/pose_budget_settled_20261023/composition_gate/versus_composition_gate.h` | `1da1e952eee6ee556abe24e1f3434a0d14bf65e283363de3e3f423f5e9e0f187` | derivado do META emitido |
| Diff do gate | `out/logs/pose_budget_settled_20261023/composition_gate/main_c_composition_gate.patch` | `07bf6771678f5ee463b4ccc4290b8ab66c97557093b5132042c8bbbdd3d6991b` | só cópia temporária |
| Header de origem | `out/generated/pose_budget_pair_20261023/versus_scene_runtime.h` | `1013b5b4d3160461725d1a4a377871bd19d9c6f57c255192b9933578ccdbbe8b` | corte não reautorado |
| Pior quadro | `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/worst_frame/worst_frame_gate_final.json` | `135d665fec4ab7af98addcfae3cc77f84b5506761eca40975bc092a32352fc46` | leitura única pós-selo |

ROMs protegidas, todas intactas:

| ROM | SHA-256 | Observação |
|---|---|---|
| Produção | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` | não substituída; 49 banks |
| Piloto da manhã | `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba` | não reaberta |
| Paleta reservada | `f9ef0e27eef5e29d530b0fa4e5c8325bd8df84a1ab6e7d93e77873f40a2b76cb` | continua recusada; sem captura |
| Par / luma | `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873` | base do ramo residente; não substituída |

## Mapa dos 18 pontos

| Ponto | Assunto | Estado após este lote |
|---|---|---|
| PB-01 | default `pose_budget` | histórico do piloto; não reaberto |
| PB-02 | origem obrigatória e alvos | histórico; não reaberto |
| PB-03 | amostragem e padding | histórico; a medida da sola reusa essa base |
| PB-04 | corpo, FX e retrato | histórico; não reaberto |
| PB-05 | porta de cerca de 70% | **substituído** pelo critério de composição |
| PB-06 | duas passadas | válido; a hurt foi escalada pelos mesmos dois passes |
| PB-07 | caso a caso | válido como dívida; PB-15 mostra que rótulo não remove pixel |
| PB-08 | corte e rótulo `downscale` | **substituído** onde a nota de 2026-10-23 indica |
| PB-09 | oito colunas de um lutador | **substituído** pela unidade célula/linha contra idle de 4 colunas |
| PB-10 | bytes de bank não são FPS | reforçado por PB-17 |
| PB-11 | boot não aceito | não reaberto; a captura nova é framebuffer, não janela |
| PB-12 | tetos que permanecem | não reaberto; `validado_budget` segue fechado |
| PB-13 | as duas capturas são o mesmo desenho | **fechado com correção de causa** |
| PB-14 | o zero do simulador não é a luta | **fechado com os dez pares** |
| PB-15 | golpe largo acima de 4 colunas | **fechado com gate e prova emulada** |
| PB-16 | hurtbox do idle do Ryu | **fechado com a medida corrigida em 1 px** |
| PB-17 | orçamento de VBlank sem número | **fechado como reprovação medida** |
| PB-18 | o parecer não promove | **mantido**; este pacote também não promove |

## Fechamento ponto a ponto

### PB-13 — captura igual não é desenho completo

Fato anterior: duas capturas 256×192 tinham a mesma ocupação opaca, diff de 14 pixels no Ken, e o Ken aparecia em listras. A causa estava aberta entre stream incompleto e ordem de tile; a orientação era não reordenar tiles antes de provar residência.

Fechamento: no frame **500**, com o ramo residente, as duas poses pedidas estavam residentes. P1 `desired/resident/submit/present = 5/5/5/5`; P2 `49/49/49/49`; `_SpriteNextFree=32`; **16 células SAT por lado**. A SAT ocupa x 69–100 (P1) e x 142–173 (P2), nos mesmos Y 105/121/137/153. O PNG do frame 500 foi reaberto e os dois corpos aparecem completos.

Causa: **pose não residente/upload incompleto**, não ordem de tile. Reordenar tiles antes de provar residência teria mascarado o defeito.

Limite: a prova é de um frame e de uma sessão. Não prova todas as poses, não promove entrega visual e não substitui a ROM de produção.

### PB-14 — o zero do simulador não é a luta

Fato anterior: os pares “incluídos” com pico 8 eram idle/idle, Ken idle + Ryu special e Ryu special + Ryu ko. Nenhum era golpe largo contra o outro lutador. O zero do simulador media uma composição que não era a luta.

Fechamento: dez pares reais golpe×idle, todos com self-check do simulador antes da leitura. O idle/idle fica em pico **8**, 32 sprites, zero violações. Os dez golpes largos ficam em pico **9–12**, com **5 violações cada**. Pico acima de 8 reprova a composição.

Aprendizado: o relatório de linha precisa nomear a composição. Par do lutador contra ele mesmo, ou dois idles, não autoriza golpe largo. `included_pair: false` não remove o papel da ROM.

Limite: o simulador mede o META emitido, não a SAT viva. A prova emulada do gate é do frame 500; cada par não foi capturado individualmente em emulador.

### PB-15 — caso a caso não tira o pixel da ROM

Fato anterior: os dez golpes largos continuavam no binário com 5–8 colunas; contra um idle de 4 colunas o pico seria 9–12. Marcar “caso a caso” não os removia da composição.

Fechamento: gate derivado do META emitido. Uma pose só é exibida ao lado do idle quando nenhuma linha dela carrega mais de **4 células 8×16**. Das 93 poses do corte, **25** passam de 4 células por linha. O gate age em `set_role()`; papel derrubado não altera o papel corrente, o dado continua no corte e a recusa é contada. Na prova emulada do frame 500: `dropped_from_composition=2`, `block_p1=1` (role 7, 6 células), `block_p2=1` (role 7, 7 células). O idle permanece em 4 colunas; nenhuma coluna foi omitida; o idle não encolheu.

Aprendizado: enforcement tem de agir sobre o dado emitido, não sobre a intenção do autor. Rótulo de dívida não é gate.

Limite: o gate derruba o papel da composição, não redesenha o golpe. Ryu special 1000 e Ryu ko 170 continuam legais (máximo 4 células/linha), mas não são os golpes largos deste lote.

### PB-16 — hurtbox do idle do Ryu

Fato anterior: a hurt do Ryu idle passava 2 px além da sola, atribuídos à linha de baixo não amostrada.

Fechamento: a medida anterior usou `sprite.axis_y` e ignorou `frame.y`. O `AXIS` gerado já é `frame.y - sprite.axis_y`. Refazendo com o `AXIS` emitido e a hurtbox escalada pelos mesmos dois passes:

| Quadro | `AXIS_y` | linha da sola | `AXIS_y + sola` | hurt bottom | hurt − sola |
|---|---:|---:|---:|---:|---:|
| Ryu idle F0 | −53 | 53 | 0 | 1 | **+1** |
| Ryu punch F0 | −56 | 59 | 3 | 0 | −3 |
| Ken idle F0 | −53 | 53 | 0 | −1 | −1 |
| Ken punch F0 | −57 | 60 | 3 | 1 | −2 |

A premissa de 2 px não se reproduz. O valor corrigido é **1 px**. Os quatro amostradores testados no pipeline real de dois passes (`current`, `ceil`, `full`, `src_len`) não movem a sola do Ryu; `full` move o Ken em 1 px e não fecha o Ryu. Sampler, eixo e hurtbox ficaram inalterados.

Aprendizado: erro de medida pode parecer bug de motor. Recomputar com o `AXIS` emitido, somar `sole_row` uma única vez e escalar a hurt pelos mesmos passes. Não somar `frame.y` duas vezes. Resultado negativo de quatro variantes também é evidência: não trocar sampler sem movimento medido.

Limite: o delta de +1 px permanece. Não foi declarado corrigido, não virou hitbox nova e não autoriza mudança de sampler.

### PB-17 — orçamento de VBlank sem número

Fato anterior: `measure_worst_frame.py` na sonda `0xC800` devolveu `sem_lastro` (frame 2035, `done` 0). Tamanho de ROM não é velocidade de quadro.

Fechamento: o pior quadro só rodou depois do fechamento do Ken. Na ROM final com gate: **`derramou`**, `vline_min=4`, `vovf_delta=1740`, `snapshot done=1`, `frames_rom_final=4079`. Na ROM pré-gate `c45dbd4a…`: `derramou`, `vline_min=2`, `vovf_delta=1770`, frame 3946.

O valor **144** do resumo anterior era o `vline` do snapshot, não o `vline_min` selado. O campo selado é `vline_min`.

Aprendizado: o veredito do pior quadro cita o campo selado, não o snapshot. Composição legal não compra orçamento de VBlank: o gate reduziu o pico de composição, e as duas ROMs continuam derramando.

Limite: uma leitura selada, host load alto, sem atribuição de FPS. `validado_budget` continua proibido; 24 banks continuam medindo tamanho, não FPS.

### PB-18 — o que este parecer não promove

A produção `087df676…` permanece. `src/main.c` e `.mddev/project.json` vivos seguem em `ryu_ken_cross`. O gate foi compilado em cópia temporária. Não houve commit nem push. Este pacote também não emite ID de lição, não edita `SMS_GLOBAL.md`, não edita o ledger e não promove entrega visual.

## Dez pares medidos

Self-check do simulador antes da leitura; mesmo Y, tall 8×16, transparente omitido.

| Par | Pico/linha | Violações | Células do atacante | Colunas | Veredito |
|---|---:|---:|---:|---:|---|
| idle / idle | 8 | 0 | 16 + 16 | 4 + 4 | legal, 32 sprites |
| Ken punch 250 + Ryu idle | 10 | 5 | 17 | 6 | derrubado |
| Ken hp 450 + Ryu idle | 11 | 5 | 16 | 7 | derrubado |
| Ken kick 200 + Ryu idle | 10 | 5 | 20 | 6 | derrubado |
| Ken hk 220 + Ryu idle | 10 | 5 | 18 | 7 | derrubado |
| Ken special 1000 + Ryu idle | 10 | 5 | 18 | 7 | derrubado |
| Ken ko 5080 + Ryu idle | 12 | 5 | 15 | 8 | derrubado |
| Ryu punch 260 + Ken idle | 9 | 5 | 17 | 6 | derrubado |
| Ryu hp 280 + Ken idle | 10 | 5 | 17 | 6 | derrubado |
| Ryu kick 200 + Ken idle | 10 | 5 | 20 | 6 | derrubado |
| Ryu hk 240 + Ken idle | 10 | 5 | 18 | 6 | derrubado |

## Papéis derrubados pela composição

Regra: pose legal se o máximo de células 8×16 em qualquer linha for ≤ 4.

| Papel | Ação | Frame medido | Pico | Máx. células/linha | Colunas |
|---|---:|---:|---:|---:|---:|
| P1_PUNCH | 260 | 2 | 9 | 5 | 6 |
| P1_HP | 280 | 2 | 10 | 6 | 6 |
| P1_KICK | 200 | 1 | 10 | 6 | 6 |
| P1_HK | 240 | 1 | 10 | 6 | 6 |
| P2_PUNCH | 250 | 2 | 10 | 6 | 6 |
| P2_HP | 450 | 1 | 11 | 7 | 7 |
| P2_KICK | 200 | 1 | 10 | 6 | 6 |
| P2_HK | 220 | 1 | 10 | 6 | 7 |
| P2_SPECIAL | 1000 | 3 | 10 | 6 | 7 |
| P2_KO | 5080 | 0 | 12 | 8 | 8 |

`P1_SPECIAL` 1000 e `P1_KO` 170 continuam legais no gate (máximo 4 células/linha), mas não são os dez golpes largos medidos neste lote.

## Aprendizados candidatos, sem ID

Cada candidato traz o que foi medido, o que já o contém hoje e o que precisaria de aprovação humana para virar lei. Nenhum recebeu ID.

### C1 — Residência antes de ordem de tile

Observação: sprite fragmentado pode ser pose não residente/upload incompleto. No frame 500, com as duas poses residentes, o Ken fechou o corpo sem reordenar tile.

Causa provável: a leitura anterior tratou fragmentação como problema de ordenação. A prova de residência veio antes.

Guarda atual: sondas `desired/resident/submit/present`, `_SpriteNextFree` e SAT; captura de framebuffer no mesmo frame.

Ação proposta: exigir prova de residência (contadores + SAT + PNG) antes de qualquer conclusão sobre ordem de tile.

Risco se promovido cegamente: transformar uma prova de um frame em regra universal de upload; poses diferentes podem ter caminhos diferentes.

### C2 — Zero do simulador não é composição legal

Observação: pico 8 em idle/idle, Ken idle + Ryu special e Ryu special + Ryu ko não é golpe largo contra o outro lutador. Os dez pares reais dão pico 9–12.

Causa: composição não nomeada; o simulador mede o que lhe é dado, não a cena que a ROM pode mostrar.

Guarda atual: `audit_sprite_line_sim.py` com composição explícita e self-check; `line_summary.json` nomeia atacante e idle.

Ação proposta: relatório de linha deve nomear a composição; par do lutador contra ele mesmo não conta como prova de golpe largo.

Risco: bloquear pares legítimos de treino/espelho se a regra for ampla demais. A restrição deve valer para claim de composição de luta.

### C3 — Rótulo “caso a caso” não remove pixel da ROM

Observação: os dez golpes largos continuavam no binário; marcar dívida não os tirava da cena. O gate derivado do META emitido derrubou os dez.

Causa: intenção de reautorar não é enforcement. O caminho quente precisa consultar o dado emitido.

Guarda atual: gate em `set_role()`, header `versus_composition_gate.h`, `dropped_from_composition.json`.

Ação proposta: toda composição que mistura pose larga com idle de 4 colunas passa por gate derivado do META; papel derrubado é contado e não altera o papel corrente.

Risco: o gate pode esconder arte que o autor queria mostrar, em vez de forçar revisão. O contador e o relatório precisam ser lidos, não só o exit.

### C4 — `AXIS` emitido já inclui `frame.y`

Observação: a medida anterior somou `frame.y` de novo e produziu 2 px; a correta é 1 px. Quatro amostradores não moveram a sola do Ryu.

Causa: dupla contagem de deslocamento e uso de `sprite.axis_y` em vez do `AXIS` emitido.

Guarda atual: tabela de sola no `doc/28-pose-budget-8.md`, com `AXIS_y + sole_row` e hurt escalada pelos dois passes.

Ação proposta: medir sola com `AXIS_y + sole_row` uma única vez; documentar a origem do `AXIS`; não trocar sampler sem movimento medido.

Risco: tolerar +1 px como “aceitável” sem decisão explícita. O número deve ficar visível; tolerância é política, não medição.

### C5 — `vline_min` é o campo selado; `vline` é snapshot

Observação: o resumo anterior citou 144 como pior quadro; 144 era o `vline` do snapshot. O `vline_min` selado é 4.

Causa: nomes de campo parecidos e relatório que não distingue snapshot de mínimo.

Guarda atual: `measure_worst_frame.py` grava `vline_min`; o JSON final traz os dois.

Ação proposta: todo resumo de pior quadro cita `vline_min` e marca `vline` como leitura de snapshot; gate de documento pode reprovar citação de `vline` como mínimo.

Risco: `vline_min` é extremal e sensível à fase; não promovê-lo a FPS nem a qualidade média.

### C6 — Gate de composição não compra orçamento de VBlank

Observação: a ROM final com gate continua `derramou` (`vline_min=4`, `vovf_delta=1740`). A pré-gate também (`vline_min=2`, 1770).

Causa: composição legal reduz pico de sprites por linha, mas o custo de emissão/VBlank é outro eixo.

Guarda atual: `measure_worst_frame.py` na sonda `0xC800`, leitura única pós-selo, `validado_budget` separado.

Ação proposta: nenhum claim de orçamento sem `measure_worst_frame.py`; composição legal e orçamento de VBlank são gates distintos.

Risco: usar a melhora de pico como se fosse melhora de frame; os dois números não são conversíveis sem medição.

### C7 — Evidência de emulador precisa de sessão, SHA e PNG legível

Observação: a prova do frame 500 tem sessão privada, ROM SHA, SAT, PNG 256×192 e `state=closed`. O PNG foi reaberto e mostra os dois corpos.

Causa: captura sem sessão/SHA não distingue binário nem instância.

Guarda atual: `emulator_session.py`, `capture_evidence.py`, manifesto de evidência, `audit_subagent_session.py` quando aplicável.

Ação proposta: manter o pacote mínimo (sessão + SHA da ROM + SAT/JSON + PNG legível) para qualquer claim de tela.

Risco: burocracia sem ganho se aplicada a sondas internas; o pacote é para claim de imagem, não para todo log.

## O que o curador precisa decidir

1. Quais de C1–C7 viram lei da fábrica e quais ficam como regra de projeto. A recomendação conservadora é promover C4, C5 e C6 como método de medição, e manter C1–C3 como gates de projeto até haver segundo caso.
2. Se o gate de composição vive no motor (`scene_cut.py`) ou é gerado por projeto. Hoje ele é derivado e compilado em cópia temporária; não há API pública.
3. Se o critério “idle de 4 colunas + pose ≤ 4 células/linha” é regra global ou específica deste par. A fábrica tem outros gêneros e outros idles.
4. O que fazer com os dez golpes largos: reautorar, manter derrubados na composição de duelo, ou separar em modo próprio. O lote não redesenhou nenhum.
5. Se o delta de +1 px da sola do Ryu é tolerância aceita ou defeito a corrigir em outro lote. Nenhum sampler foi trocado.
6. Se `vline_min` deve ser o único campo selado do pior quadro, com `vline` explicitamente marcado como snapshot.

## Propostas de medição para curadoria

As quatro ferramentas foram implementadas e testadas em 2026-10-23, depois de aprovação humana explícita para prosseguir com as propostas. A promoção a lei da fábrica continua pendente: `SMS_GLOBAL.md`, o ledger e o registro de IDs não foram alterados.

| Proposta | Entrada | O que mede | Self-check mínimo | Estado |
|---|---|---|---|---|
| `audit_composition_gate.py` | header de cena emitido | máximo de células 8×16 por linha; lista de papéis derrubados | reproduzir 25/93 e os dez papéis | implementada; self-check + teste de regressão |
| `audit_sole_alignment.py` | `AXIS`, `sole_row`, hurt escalada | `AXIS_y + sole_row` vs hurt bottom | quatro quadros Ryu/Ken idle/punch | implementada; self-check + teste de regressão |
| `measure_worst_frame.py` (schema/docs) | JSON selado | exigir `vline_min`; marcar `vline` como snapshot | caso 144 vs 4 | implementada; schema v2 + self-check |
| `audit_sprite_line_sim.py` (opção) | composição nomeada | rejeitar par do lutador contra ele mesmo em claim de duelo | idle/idle vs Ken punch | implementada (opt-in); self-check + teste de duelo |

## Implementação das propostas (2026-10-23)

As ferramentas vivem em `tools/sms_wrapper/` e foram exercitadas contra o corte `pose_budget_pair_20261023` sem alterar a ROM, o corte, os dez manifestos ou os JSONs de evidência.

| Ferramenta | SHA-256 | Resultado da verificação |
|---|---|---|
| `tools/sms_wrapper/audit_composition_gate.py` | `bf1a4813f43f7e3b285fa31f67774cae178584c1f80ec6a0784cb4f154c87c64` | `25/93` poses derrubadas; `P1 [6,7,8,9]`, `P2 [6,7,8,9,10,11]`; header gerado idêntico ao de prova exceto pelos comentários de origem |
| `tools/sms_wrapper/audit_sole_alignment.py` | `175d928bcee2d8e5bbf3060bdd2f71426551e90180d9fd6cc669ef4d9d5316b3` | quatro quadros: Ryu idle `+1`, Ryu punch `−3`, Ken idle `−1`, Ken punch `−2`; `max_abs_delta=3` no conjunto de referência |
| `tools/sms_wrapper/measure_worst_frame.py` | `968bb70a6bf54ec09bdda5b0132974274dd674df25cf026b4baf5ea06fac5be4` | schema `smsforge.worst_frame/v2`; `sealed_field=vline_min`; caso real `vline_min=4`, `vline=144` marcado como snapshot, `vovf=1740`, frame 4079, veredito `derramou` |
| `tools/sms_wrapper/audit_sprite_line_sim.py` | `7996f10115b62ef25d0dc6e60b4797131c946b6e47e61ad307a15fbfa2ece5d7` | opt-in `--require-distinct-fighters`: mesmo lutador reprova; lutadores distintos passam; sem opt-in, espelho técnico continua válido; dez pares medidos mantêm pico 9–12 e 5 violações |
| `tools/sms_wrapper/mugen2sms/tests/test_measurement_gates_pose_budget.py` | `0a29269ceaf8b4886c8a10f03a5e66b49a113d38184f056cee4bda4f253b03b0` | 8 testes passando, incluindo os quatro self-checks e as regressões de projeto |

Comandos executados:

```
python3 tools/sms_wrapper/audit_composition_gate.py --self-check
python3 tools/sms_wrapper/audit_sole_alignment.py --self-check
python3 tools/sms_wrapper/audit_sprite_line_sim.py --self-check
python3 tools/sms_wrapper/measure_worst_frame.py --self-check
python3 -m pytest tools/sms_wrapper/mugen2sms/tests/test_measurement_gates_pose_budget.py -q
python3 tools/sms_wrapper/validate_measurement_tools.py
```

Observações da varredura ampla: o modo default de `audit_sole_alignment.py` mede todos os 93 quadros, não só os quatro de referência. Nessa varredura, 92 quadros têm hurtbox e 1 (`P1_RYU_A170F0`) declara `CLSN=0`; o maior `|hurt − sola|` foi 14 em `P1_RYU_A41F4`. A ferramenta mede e reporta, mas não classifica esses quadros como defeito: o lote PB-13–PB-18 continua julgado pelos quatro quadros de referência. A varredura ampla é candidata a escopo de curadoria, não a nova lei.

`audit_sprite_line_sim.py` exige, no opt-in, `composition` estruturada com `p1` e `p2`; os dez manifestos antigos não carregam esse campo e não foram reescritos. O gate é fail-closed quando o opt-in é usado sem composição. A migração dos manifestos antigos fica para decisão do curador.

Essas ferramentas são medições estáticas de metadados/PNG; não reabriram emulador, não geraram novo `testado_emulador` e não autorizam `validado_budget`.

Em 2026-10-23, o dono autorizou criar a seção `FERRAMENTAS EM CURADORIA (NÃO PROMOVIDAS)` no `AGENTS.md` apenas para visibilidade. A seção não altera a tabela de gates, não promove as ferramentas e não edita `SMS_GLOBAL.md` nem o ledger; ela registra o estado `awaiting_curator`, a evidência deste pacote e as regras de uso diagnóstico. Com isso, o `audit_doc_sync.py --root .` deixou de acusar as duas ferramentas novas e mantém 10 derivas preexistentes de `luta_mugen` (EIO/ENOENT). O `validate_measurement_tools.py` passa com 75/75 ferramentas, incluindo as quatro, quando chamado com o diretório default (absoluto); a forma relativa `--dir tools/sms_wrapper` falha em cascata por um bug preexistente de caminho (`cwd=wrapper_dir` + path relativo), registrado para curadoria e não corrigido neste lote. A promoção a gate global continua pendente de aprovação humana explícita do curador.

## Verificação deste registro

- SHA-256 da ROM, PNG, SAT, manifesto, sessão, dez pares, relatório de derrubados, header do gate, patch e pior quadro reconferidos nesta data.
- PNG do frame 500 reaberto: os dois corpos aparecem completos.
- JSONs parseados; sessão `a40818af…` com `state=closed`; nenhum processo Emulicious vivo.
- ROMs protegidas com SHA inalterado.
- `id_registry.json` lido em `L138`; nenhum ID emitido.
- `learning_ledger.json` e `SMS_GLOBAL.md` com SHA inalterado.
- Quatro ferramentas novas/modificadas com `--self-check` rc=0; `pytest ...test_measurement_gates_pose_budget.py` com 8 testes passando; os dez pares antigos mantêm pico e violações no simulador sem opt-in.
- `validate_measurement_tools.py` (diretório default) passa com 75/75; a forma relativa `--dir tools/sms_wrapper` reproduz um bug preexistente de caminho e não foi usada como prova. `audit_learning_capture.py --root .` passa.
- O `audit_doc_sync.py --root .` mantém 10 derivas preexistentes de `luta_mugen` (EIO/ENOENT), sem as 2 derivas novas de visibilidade, resolvidas pela seção autorizada em `AGENTS.md`.
- Sem commit e sem push.

## Fronteiras mantidas

Status do lote: `testado_emulador`. Sem `validado_budget`, sem 60 fps, sem áudio, sem gameplay e sem entrega visual. Sem terceira paleta; `palette_reserve` continua recusada. Sem ID de lição, sem `SMS_GLOBAL.md`, sem ledger. Sem commit e sem push. A única alteração de doutrina é a seção de visibilidade autorizada em `AGENTS.md`, que não mudou a tabela de gates; o bug de caminho relativo do `validate_measurement_tools.py` fica aberto para curadoria e não foi corrigido aqui.
