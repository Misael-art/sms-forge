# workflow: production-loop

Pipeline de uma iteração SMS: design → arte → runtime → QA → evidência.
A jornada de cena vive em `pipelines/aaa_scene_v1.json`.
Projeto novo ou mecânica nova começa por `first-playable-slice.md`; não ampliar
elenco, fases ou telas enquanto a interação central não estiver comprovada.

Nenhum passo abaixo autoriza encerrar a execução após diagnóstico, correção
de ferramenta, relatório, build isolado, captura ou um único milestone.

## 0. Continuidade

- Pedido de produção contínua → `causal-persistence-loop.md`.
- Dois ramos independentes → `harness_orchestration.py` (máx. 3:
  visual / runtime / audio_qa). Claim permanece no coordenador.
- Checkpoints foundation / vertical_slice / RC → `independent-quality-review.md`.
  Antes de crescer o slice/RC, aplicar `product-quality-checkpoint.md` para
  conferir arte, mix/SFX, controles e pacing na mesma cena/ROM real.
- QA do delta em qualquer gênero → `subagent-emulator-qa.md`: sessões privadas
  por worker nativo, pedido/cobertura explícitos e feedback preso à ROM atual.

## 1. Escopo

GDD (`doc/11-gdd.md`) trava o que entra. Feature fora do GDD não entra.
Divergência GDD↔fork: registrar decisão e harmonizar GDD/TDD/spec/memory bank
**antes** de crescer.
O GDD também declara telas ausentes: não acrescentar cenário, menu, FX ou HUD
por convenção. Uma tela de menu, treino, abertura, luta ou resultado tem seu
próprio conjunto de recursos e budget.

## 2. Arte (visual-first)

Skill: `sms-visual-excellence.md`. Workflow: `new-visual-asset.md`.
PNG indexado válido ≠ qualidade. Epoch `probe`/`technical_d1` não promove.
Gate: `audit_visual_delivery.py --delivery` + `audit_rom_asset_binding.py --require`.

## 3. Runtime

Skill: hardware/budget + input. Build pelo wrapper. Pre-gates do `build_inner.py`.
Não tratar planejamento offline como `validado_budget`.
Medir separadamente loop do emulador (`measure_fps.py`), frame counter da ROM
(`measure_frame_advance.py`), estado runtime (`measure_runtime_probe.py`),
resposta de input/feedback visível e pior quadro (`measure_worst_frame.py`).
FPS estável não prova que a ação aparece a tempo; ROM compilada não prova
cadência de pose. Para ação com pose de impacto, comparar a pose mostrada, a
janela de colisão e a mudança de HUD. Não deixar a lógica aguardar upload por
centenas de ticks nem aplicar um acerto que a imagem não apresenta; medir a
causa e reduzir/reorganizar o custo visual ou rever o contrato com o dono
(L098–L099). Para trilha por tick, não amostrar lendo DAP com a emulação pausada
(L097); usar instrumentação que registra estado dentro da ROM quando aplicável.
Quando houver troca de tela, round ou modo, aplicar
`skills/sms-state-transitions.md`: reproduzir no emulador as arestas previstas,
incluindo retorno/reentrada, e conferir estado limpo, recursos e pior quadro da
transição. Vídeo prova a mudança visível; probe/trilha prova o estado interno.

## 4. Evidência

`evidence-protocol.md`. Captura de boot classifica no máximo
`runtime_probe_passed_visual_epoch_failed` até o gate visual passar.
SHA da ROM no bundle tem de ser o da ROM que rodou.
Gameplay: direção + identidade + escala nativa (§29). Scale da janela
é entrada do gate, não detalhe de UI (L040).

## 5. Áudio

`new-audio.md` + `audit_audio.py` / `capture_audio.py`. PSG, não XGM2.

## 6. Fechamento de iteração

Memory bank atualizado com: claim ativo, blocker folha, última rota, delta,
rotas encerradas, próxima ação causal, gate humano pendente.
Não declare `ready_for_aaa=true` enquanto visual delivery, binding, gameplay,
áudio, budget medido e regressão não estiverem pagos.
