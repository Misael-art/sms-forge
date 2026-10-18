# 13-spec-cenas — luta_mugen

> **Revisão vigente 2026-09-26:** `engine_quality_contract.json` e
> `16-engine-review-2026-09-26.md` supersedem a escala 1:4/48 px como limite do
> motor. Números e tarefas T10 abaixo são histórico do perfil
> `legacy_probe_quarter`, sem aceite no novo piso. Próxima cena precisa medir
> corpo idle 45–55% da área útil (perfil inicial: 72–88 px), custos simultâneos
> e capacidade expansível. Técnicas opcionais exigem A/B; não estão implementadas
> por constarem no contrato.

> Histórico de critério, 2026-09-29: uma revisão anterior exigiu zero flicker
> visível, além de zero corrupção gráfica, <=8 sprites/scanline e <=64/SAT.
> Essa exigência de flicker foi supersedida pela decisão humana posterior
> registrada no GDD: opção 3, flicker mínimo e sem glitch. A linha fica aqui
> para rastreabilidade; ela não define o aceite vigente.
>
> Lote C, 2026-09-30: a planta técnica do palco fixo é
> `res/stage/planta_arena.png` e o contrato (HUD nas linhas 0–1, piso em
> y=128, âncoras 96/152, tiles a partir de 256) está no GDD. O critério de
> flicker deste projeto é a opção 3 já registrada no GDD. Esta spec não
> separa custo de CPU/VDP atribuído ao palco; o Lote C mede somente o quadro
> integrado com os sistemas juntos.

## Lote C — estudo integrado da arena técnica (2026-09-30)

Estado: `testado_em_emulador`, época visual `probe`, não é entrega de arte.
ROM de 655360 B, SHA-256
`c958278fa0196e84deecab1fef01f976100072cd9851e9c233f82a694a882999`.

| Grandeza | Medição | Limite da conclusão |
|----------|---------|---------------------|
| FPS da ROM NTSC | 59,59 e 59,75 em janelas independentes de 30,14/30,09 s; spread 0,16; delta 3594 frames | PAL separado; não mede duração AIR |
| VBlank worst-frame | 3000 frames; `vovf_delta=0`; `vline_min=211`; DAP confirmou 1 entrada P1 e 1 dano antes do selo | inclui um soco que conecta; não cobre todas as ações/poses |
| RAM estática | `_DATA` até `0xC720`, `_INITIALIZED` até `0xC726`; SAT própria até `0xD1F0`; SP `0xDFF0`; reserva 3584 B | profundidade de stack não medida |
| Glitch no vídeo final, L091 v1 | 0/14960 reprovados, extra máximo 0; `images_seen` só `ken0_ryu0` | inválido como prova visual: a máscara luma contou palco/HUD claro como ator; não usar esse PASS para ausência de glitch/cobertura |
| Glitch no idle, L091 v2 | captura fresca 781 quadros; placa RGB (SHA em evidência), HUD ignorado; 0/781 reprovados, extra máximo 0, ausência instantânea máxima 901 px | toda pose legal coberta em janela de 8; só idle, não prova combate nem zero flicker |
| Visibilidade por região, L091 v2 | Ken duty 87,292%, P05 67,135%, mínimo 65,262%; Ryu duty 78,048%, P05 48,262%, mínimo 47%; ausência total máxima 0 frames, Ryu abaixo de 50% por até 3 frames | métrica usa limiar RGB 32 e tolerância de borda 1 px; Ryu tem omissões visíveis; julgamento humano de “flicker mínimo” não foi promovido |
| Round/match | vídeo 14960 quadros/249,66 s termina em `WIN 1`, placar 2–0 após timeouts; trace DAP chega ao round 2 | 25 socos aceitos, 10 causam dano, 15 erram; KO não alcançado; chute/rematch não exercitados |
| Áudio isolado | 11,1 s durante entrada de soco, peak 5887, ativo 100%; `audit_audio.py` PASS | não é revisão musical subjetiva nem separação por canal |

Manifesto asset→ROM: `doc/rom_asset_binding_lote_c.json`; evidência primária
em `out/local_study/luta_integrada/out/evidence/`. O vídeo L091 permanece
opção 3 com janela 8; não declarar ausência de flicker.


> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Subpaletas | 2 × 16 (índice 0 transparente nas duas) |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |

## Cena 01 — `probe_import` (fixture sintético `mini`; ROM 16 KB)

Estado operacional: **testado_em_emulador** — evidência `out/evidence/cena01_probe.png`
(variancia janela 5347.5 / viewport 818.2, `capture_evidence.py` PASS), boot
determinístico 2 execuções idênticas (`audit_deterministic_boot.py` PASS), arte
confirmada 100% (`audit_render_fidelity.py` PASS em [90,131]).

### Leis de hardware MEDIDAS nesta cena (não assumidas)
| Contratos | Medição |
|-----------|---------|
| Par TALL `(pattern, pattern+1)` = (topo, base) | probe 8×16 metade branca(idx1)/preta(idx2): captura do phase 0..3 s mostrou **branco em cima** — `pack_tiles_tall` confirmado, sem inversão |
| `SMS_addMetaSprite` origem y = 1ª linha visível do topo | ego passado y=112 ocupa linhas 112..127 na captura |
| `SMS_useFirstHalfTilesforSprites(1)` + `SPRITEMODE_TALL` | poses renderizam limpas (sem ruido) — L006 não disparou |
| espelho-h como OUTRO padrão (sem flip no SMS) | METAL carregado e renderizado no oponente (x=152..167) |

### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | 12 (64 B) + 14 (32 B) | 3 | rodapé cinza + vazio |
| patterns sprite | 0..11 e 12..13 (3 pools de 64 B + probe) | 9 tiles = 288 B | 3 poses com espelho |
| name table | 32×24 = 768 B escritos no boot | — | céu vazio + chão linha 16 |
| SAT | 8 entradas de 64 | — | 4 colunas TALL × 2 meias-linhas |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| cópia SAT (8 entradas × 2 B) | 16 B | contagem estática do loop de frame (`SMS_copySpritestoSAT`), confirmada por capture |
| name table por frame | 0 B | NT escrita só no boot (código lido) |
| tiles por frame | 0 B | streaming é Task 6; carga única no boot |
| CRAM (amortizado) | 16 palavras a cada 30 frames | `load_pose_pal` no switch de pose |

- **Total worst-frame**: 16 B de VRAM/VBlank (nada de tile streaming ainda)
- **Headroom**: >98% da janela de VBlank — mas NUNCA medido em ciclo de CPU;
  o contrato real de worst-frame chega com Ken (Task 6/`measure_worst_frame.py`)
- **Método**: contagem instrumentada do código de frame + captura de evidência
- **Validação seguinte**: Task 6 mediu o bloco VDP bancado na ROM de fixture
  (seção abaixo). O corte de arte do Ken real continua sujeito a orçamento e
  medição próprios.

### Sprites por scanline (pico)
`audit_sprite_line_sim.py` sobre `out/evidence/cena01_line_sim_scene.json`
(4 colunas TALL 8×16 modeladas como 8 entradas 8×8): **pico 4/linha, SAT 8/64,
zero violações** — dentro do contrato GDD de lutador (≤4/linha).

### fps observado
`measure_fps.py` — 6 amostras a **59,9 quadros/s** (atualização nominal de
60 Hz, `constante_50_60: true`), janela `Emulicious - 100%`:
`out/evidence/cena01_fps.json`.

## Loop T6 — arena de fixture sintético bancária (2026-09-26)

Esta medição valida o loop e o transporte de poses do fixture; não declara
entrega visual do Ken real.

| Grandeza | Resultado medido | Evidência |
|----------|------------------|-----------|
| ROM | 65.536 B, SHA `b5d5db7b6295e8c6947b0125f0d4ef468fc179fb4e4d72215b5b5573227fafc5` | `out/build_record.json` |
| VDP/VBlank | 3.000 frames, `vovf_delta=0`, `vline_min=0xC8`; PASS | `out/evidence/t6_vblank_cpu_split_byte_addr.json` |
| Frame advance da ROM | 59,9 fps; 27 estados completos; 0 fora da tolerância; PASS | `out/evidence/t6_vblank_cpu_split_byte_addr_frame_advance_60s.json` |
| FPS do emulador | 6/6 a 59,9 quadros/s; PASS | `out/evidence/t6_vblank_cpu_split_fps.json` |
| FPS via probe na RAM | 59,29 e 59,43 em duas janelas de 8 s; PASS | `out/evidence/t6_vblank_cpu_split_byte_addr_runtime_probe.json` |
| Input ao vivo | direções, pulo, soco com dano, agachar e padrões; PASS | `out/evidence/t5_input_memory.json` |
| Captura de boot | informativa, paleta 100%, lixo VRAM 0%; PASS sem claim de gameplay | `out/evidence/t6_vblank_cpu_split_byte_addr.png` + `_semantic.json` |

O perfil por etapa não foi capturado porque não houve derrame; os campos do
perfil são inválidos quando `vovf_delta=0`. Input, física e preparo de
metasprites rodam fora do bloco VDP. Arte do Ken real e áudio seguem abertos.

## Cena 02 / Cena 03 parcial — T10 Ken vs Ryu dummy (2026-09-26)

Build T10 integra dois cortes distintos no mesmo runtime: Ken P1 (44 poses,
banks 2–4) e Ryu P2 (32 poses, banks 5–6). P2 segue dummy determinístico;
esta ROM não fecha a troca de `.def` sem C editado, especial de Ryu ou o ciclo
completo de KO/reset.

| Grandeza | Resultado medido | Evidência |
|----------|------------------|-----------|
| ROM | 131.072 B, SHA `af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97` | `out/build_record.json` |
| Cortes e bancos | Ken 44 poses (2–4); Ryu 32 poses (5–6) | `out/local_study/generated/versus_cut/versus_scene_manifest.json` |
| Sprite budget combinado | PASS, 16 sprites no pior par medido, pico 8/linha | `out/evidence/t10_ken_ryu_line_sim.json` |
| Worst-frame | PASS, 3.000 frames, `vovf_delta=0`, `vline_min=200`; perfil por etapa inválido sem derrame | `out/evidence/t10_current_worst_frame.json` |
| Frame advance | PASS, 27 transições em 59,81 s, mediana 58,6 fps, `constante=true` | `out/evidence/t10_current_frame_advance.json` |
| FPS do emulador | PASS, 6/6 entre 59 e 60 quadros/s, média 59,8 | `out/evidence/t10_current_fps.json` |
| Runtime probe DAP | PASS, duas janelas de 120 s: 58,10/59,78 fps, spread 1,68; boot e avanço PASS. Tentativa 2×240 s quebrou o canal antes da 2ª janela | `out/evidence/t10_current_runtime_probe_120.json` |
| Input/gameplay | PASS parcial range-synced: direções, pulo, soco/dano (vida 152→102), agachar, guard e QCF+B1; reteste anterior de whiff preservado; KO/reset e partida longa pendem | `out/evidence/t10_input_memory_range_sync_pass.json`, `out/evidence/t10_input_memory_idle_wait_retry_whiff.json` |
| Boot/semântica | captura 256×192 e gate semântico PASS; duas execuções determinísticas; imagem permanece época `probe` | `out/evidence/t10_ken_ryu_pair.png` + `_semantic.json` |
| Áudio | sinal isolado por 15,6 s, peak 5853, 100% ativo, `audit_audio.py` PASS; 0/7 streams reprovados no piso PSG | `out/evidence/t10_current_audio.wav`, `t10_current_audio_audit.log`, `t10_psg_quality.json` |
| Vínculo asset→ROM | PASS, cinco bancos e fontes SHA vinculados à ROM atual | `doc/rom_asset_binding.json`, `out/evidence/t10_rom_asset_binding.json` |
| Claims | PASS, nenhum claim acima do teto | `out/evidence/t10_audit_claims.log` |
| Evidência fresca | PASS, bundle selado com 38 artefatos posteriores à ROM | `out/evidence/t10_fresh_bundle.json` |

`audit_visual_delivery.py --delivery` reprova `wrong_visual_epoch`: o contrato
de entrega visual ainda não existe. A captura mostra lutadores pequenos numa
arena vazia, portanto é evidência de `probe`, não de entrega. T10 permanece o
perfil histórico 1:4. O critério vigente de flicker é a opção 3 do GDD
(2026-09-29). A planta do Lote C está em `res/stage/planta_arena.png`;
os números T10 acima não a medem.

## Histórico — Cena 02 T7 Ken vs dummy (2026-09-26)

Esta build exercita o runtime com o corte Ken local. O P2 ainda usa o mesmo
conjunto de animações do Ken, ACT alternativa e dummy determinístico; não é a
partida Ken-vs-Ryu prevista na fatia golden.

| Grandeza | Resultado medido | Evidência |
|----------|------------------|-----------|
| ROM | 131.072 B, SHA `2210b0161dd2d40f1574f8664cb54b56527f5ea85e882d41f94b1482b7ebf21f` | `out/build_record.json` |
| Corte Ken | 44 poses/fighter, banks 2–4 | `out/local_study/generated/scene_cut/ken_scene_manifest.json` |
| Sprite budget | PASS, pico 8/linha no corte versus, sem violação | `out/evidence/t8_ken_line_sim.json` |
| Worst-frame | PASS, 3.000 frames, `vovf_delta=0`, `vline_min=201`; perfil por etapa inválido sem derrame | `out/evidence/t9_current_worst_frame.json` |
| Frame advance | PASS, 27 transições em 59,96 s, 57,8 fps, `constante=true` | `out/evidence/t9_current_frame_advance.json` |
| FPS do emulador | PASS, 6/6 amostras entre 59–60, média 59,8 | `out/evidence/t9_current_fps.json` |
| Runtime probe DAP | PASS em janelas de 240 s: 58,87 e 59,86 fps, spread 0,99; a tentativa de 120 s teve spread 2,05 e ficou como diagnóstico | `out/evidence/t9_current_runtime_probe_240.json` + `t9_current_runtime_probe_120.json` |
| Input/gameplay | PASS parcial: movimento, pulo, dano, agachar, guard e especial provados via RAM; Ken vs dummy | `out/evidence/t9_ken_input_memory.json` |
| Boot/semântica | captura e gate semântico PASS; imagem permanece época `probe`, com lutadores pequenos | `out/evidence/t9_ken_restored.png` + `_semantic.json` |
| Áudio | sinal presente por 11,146 s, 100% ativo; audit de captura PASS; qualidade musical ainda precisa de escuta | `out/evidence/t9_current_audio.json` + `.wav` |

O worst-frame acima é o veredito do gate da ROM. A ausência de quadros com
derrame invalida apenas o perfil opcional por etapas, não o PASS do contador
de overflow. A observação de tela também não promove a época visual além de
`probe`; a cena ainda precisa de arte com silhueta legível antes de qualquer
claim de entrega.

Experimento independente de troca de dados: `t9_ryu_def_switch.json` registra
uma build Ryu de 65.536 B com 32 poses e dois banks. `src/main.c`,
`src/fight.c` e `inc/fight.h` mantiveram os mesmos SHA nas builds Ken e Ryu.
Isso comprova a troca de piloto no build, não dois `.def` distintos na mesma
partida.
