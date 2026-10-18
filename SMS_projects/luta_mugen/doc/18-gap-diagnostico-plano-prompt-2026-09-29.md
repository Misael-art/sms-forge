# Diagnóstico de gaps, plano de fechamento e prompt — 2026-09-29

## Decisão de qualidade vigente

O pedido humano mais recente fixa como alvo de entrega: idle opaco entre
72 e 88 px, proporções/pivôs/CLSN/AIR preservados, imagem sem glitches e sem
flicker visível, e loop estável a 50/60 Hz conforme a região. Isso atualiza a
decisão anterior de usar flicker controlado como base de entrega. O clone
`scale_pilot_rom_fast_render` continua sendo a melhor referência de desempenho
medida, mas seu flicker visível e um fragmento isolado no pé do Ryu impedem
promoção.

**Não iniciar a produção completa de arte antes do gate sem flicker.** O Ryu de
bootleg NES segue útil para ensaio técnico de paleta/cache, mas Ken CPS2/ADV é a
referência visual. Substituir Ryu por modelo coerente com Ken/CPS2 antes de
fechar o golden slice e repetir as medições com o novo par.

## Estado observado

| Área | Evidência disponível | Diagnóstico |
|---|---|---|
| ROM T10 registrada | ROM `af9eb127…dc97`, 131.072 B; mediana de frame advance 58,6 fps, título do emulador ~59,8; 3.000 frames sem overflow; input de movimento, pulo, soco/dano, agachar, guarda e QCF+B1 parcial PASS | Prova útil do runtime antigo (`legacy_probe_quarter`), não prova o novo corte 72–88 px, combate completo, KO/reset ou melhor de três |
| Escala do corte selecionado | Manifestos locais `out/local_study/generated/scale_pilot_80px_regenerated/{p1_ken,p2_ryu}/ken_scene_manifest.json`; 44 poses selecionadas de Ken e 32 de Ryu | Escala uniforme foi aplicada; os máximos abaixo são deste corte de ações, não de todos os 934 frames parseados do Ken no acervo |
| Tamanho de idle | Ken: 93 px opacos na fonte → 81 px runtime; Ryu: 62 → 80 px. Idle frame 0 renderizado: Ken 51×77 px; Ryu 31×77 px | Passa o alvo de altura idle. O intervalo 72–88 px é contrato de idle, não limite automático de toda pose de ação |
| Maior pose do corte | Ken: maior largura 107×41 px (KO 5050, frame 0); maior altura 51×108 px (special 1000, frame 2). Ryu: maior largura 71×40 px (KO 5050, frame 0); maior altura 30×83 px (special 1300, frame 0) | Dimensões de bounds/canvas escalados; largura e altura máximas ocorrem em poses distintas. A pose de 108 px precisa de validação contra HUD, piso/câmera e área útil antes de congelar o storyboard |
| Ocupação VDP do par | `out/local_study/generated/scale_pilot_80px_regenerated/scale_pilot_dedup_emulator_audit.json`: Ken sozinho até 49 entradas SAT/7 por linha; Ryu até 42/7; idle simultâneo 55 SAT/11 por linha; par conservador especial/especial 91/14; par conservador KO/KO 69/23 | O idle combinado já excede o teto físico de 8 sprites por scanline, apesar de caber na SAT. Os pares especiais/KO são combinações geométricas conservadoras, não prova de que essas poses coincidam em gameplay; precisam ser filtradas pela coreografia/FSM |
| Desempenho do corte 72–88 | Clone `out/local_study/scale_pilot_rom_fast_render/`, ROM SHA-256 `34025741996b6b421aaddbae98ea4e044d119687f1c2444ac1e99c45ee548393`; probe 59,57/59,81 fps, vídeo 59,2/s, worst-frame 3.000 frames com `vovf_delta=0` | Loop estável no clone. Ken troca pose a cada 5,37 frames contra AIR=4 (~25% abaixo da cadência); Ryu a cada 7,25 contra AIR=7–8. O renderer usa `SMS_VRAMmemcpy` durante display ativo em slots programados; isso não demonstra aderência à regra de VRAM no VBlank, nem ausência de glitch |
| Render limpo | Vídeo `out/local_study/scale_pilot_rom_fast_render/out/evidence/l70.mp4.mp4`; partes da silhueta são multiplexadas; existe um fragmento isolado no pé do Ryu, ainda sem causa determinada | Reprova o novo alvo visual. Ainda faltam comparação de máscara em todas as poses, input real, combate, HUD e áudio dentro deste clone |
| FSM | `src/fight.c` possui 10 estados simplificados (idle, avanço/recuo, salto, agachamento, guarda, soco, chute, especial, KO), tabelas C separadas para Ken/Ryu, colisão por CLSN e física Q8.8. `main.c` inclui timer, KO, placar e código de melhor de três | Protótipo funcional parcialmente provado, não uma FSM MUGEN genérica: `fight_step` ainda mapeia estados/comandos no C. KO/reset, partida longa e ciclo melhor-de-três não têm prova de emulador consolidada |
| Cenário | A ROM T10 usa fundo vazio e piso plano na linha Y=128; HUD vai ao BG. O storyboard do palco final está vazio e não há cenário autoral integrado | Sem base para julgar arte, câmera, parallax, oclusão ou ausência de glitches em cenário final. Começar estático; rolagem/parallax é etapa posterior, opcional e medida |
| Ferramentas de aceite | `audit_sprite_line_sim.py` e `scale_pilot.py` cobrem limites/relatórios por pose; captura dinâmica existe no piloto | Ainda falta um gate que compare poses esperadas com vídeo fresco da ROM e reprove automaticamente qualquer omissão/flicker/glitch ao longo das animações |

### Limite físico e consequência

O SMS limita a SAT a 64 sprites e processa no máximo 8 entradas por scanline;
excesso causa perda/corrupção de sprites na linha. No idle atual, 11 entradas
na mesma linha não podem ser corrigidas apenas acelerando o Z80, deduplicando
patterns na ROM ou aumentando o cartucho: essas técnicas reduzem custo de
dados/CPU, mas não reduzem quantas entradas de sprite o VDP examina naquela
linha. Interrupções de raster também não removem esse limite.

Para entregar a 72–88 px sem omissões visíveis, primeiro testar compactação de
metasprite e reautoria de detalhe mantendo proporção, pivô, eixo e caixas de
colisão. Se isso não fechar o orçamento dos dois lutadores simultâneos, comparar
um compositor híbrido BG/sprites em clone isolado: BG não tem transparência de
sprite nem um segundo plano, então custo de composição, paleta, oclusão, VRAM e
escrita por frame precisam ser medidos antes de assumir que funciona. Não
reduzir silenciosamente a altura nem aceitar flicker como “inteligente” para
chamar a cena de limpa. Se nenhuma rota cumprir escala e imagem, registrar o
conflito de hardware e bloquear a arte final até uma decisão de escopo.

## Plano de execução por gates

### G0 — congelar a referência de entrega

- Atualizar GDD/contrato: idle 72–88 px; zero sprites omitidos visivelmente;
  sem corrupção/fragmento de tiles; <=8 sprites/scanline e <=64 na SAT;
  FPS estável 50/60 por região; AIR/pivô/CLSN preservados.
- Manter o clone rápido como baseline de medição; não substituir nem regravar a
  ROM T10 canônica durante os experimentos.
- Tratar a escrita de VRAM no display ativo do clone como hipótese não promovida.
  O candidato precisa caber no VBlank conforme a regra SMS ou apresentar uma
  exceção de engenharia com prova de slots invisíveis, sem artefatos e sem
  regressão de worst-frame antes de integrar.
- Tratar `out/local_study` como diagnóstico local: build falho, SHA divergente
  ou captura stale não produz evidência.
- Fechar a lacuna de tooling: implementar ou estender um gate com `--self-check`
  que vincule fonte/pose esperada, SAT emitida, captura de framebuffer e SHA da
  ROM. Ele deve sinalizar sprite omitido, tiles residuais e frames sem
  correspondência; o simulador estático sozinho não prova a imagem renderizada.

### G1 — fechar geometria máxima e orçamento antes de arte

- Gerar tabela por pose/frame, lado/facing e ator com bounds, altura opaca,
  contagem SAT, pico por scanline, paleta, bytes atuais/próximos, duração AIR,
  offsets, pivô e CLSN.
- Separar limites por idle, locomoção, salto, ataque, especial e KO. Calcular
  pares simultâneos que a FSM realmente permite, mais FX e posições de borda;
  manter também o pior caso geométrico como alerta, não como coreografia válida
  sem prova.
- Não iniciar model sheet final enquanto o corte completo não tiver resultado
  PASS ou blocker explícito para todas as classes de ação.

### G2 — provar renderer sem flicker no clone

- Comparar em etapas: remoção de pares 8×16 100% vazios, reaproveitamento exato
  de patterns/slots, compactação de META/METAL e lista de render pré-gerada.
- Medir de novo SAT/scanline depois de cada transformação. Metadados mais rápidos
  ou menos bytes de ROM não contam como redução de ocupação física.
- Medir upload e SAT dentro do VBlank; não copiar a rota de display ativo do
  clone rápido para o runtime de entrega sem fechar a regra de VRAM do SMSForge.
- Se sprite-only continuar excedendo 8/linha, prototipar composição BG/sprite
  num clone independente, com uma pose e depois o par idle. Medir custo de
  atualizar patterns/name table, consumo das duas paletas, oclusão, fronteiras
  de câmera, VRAM e pior frame. Abortar essa rota quando produzir resíduos,
  exigir escrita insegura na tela ativa ou exceder orçamento.
- Saída do gate: vídeo fresco de idle + transições, máscara esperada por frame,
  nenhuma célula ausente/corrompida, zero flicker de scheduler, <=8/linha,
  <=64/SAT e worst-frame sem overflow.

### G3 — cadência AIR e estabilidade

- Reproduzir as ações selecionadas completas no emulador; comparar ticks de
  entrada, cada pose visível, hitbox/pose e duração total com AIR.
- Corrigir starvation e prefetch de poses sem apresentar pattern parcial nem
  trocar CLSN antes da pose visível.
- Exigir loop ROM estável em 50/60 Hz na região correspondente e cadência AIR
  dentro de 1 tick do contrato em cada transição. Medir pior coreografia, não
  idle sozinho. Medir NTSC e PAL antes de declarar suporte aos dois.

### G4 — palco e HUD como cena real

- Fazer storyboard em pixel para um palco: plano de fundo, piso/faixa de luta,
  linha de chão, limites de câmera, altura útil após HUD e zonas de oclusão.
- Medir orçamento antes do asset; manter cenário e HUD no BG, com mudanças
  coalescidas em VBlank. Primeiro palco estático, câmera fixa e sem paralaxe.
- Só depois da cena limpa, experimentar scroll/parallax ou raster em clone
  separado; cada efeito precisa de fallback estático e prova de ciclos/VRAM.

### G5 — integrar FSM e dados MUGEN

- Preservar a arquitetura offline: `.air/.sff/.act/.cns/.cmd` destilados em
  tabelas com fidelidade `direct/approximate/manual/unsupported`; sem VM CNS em
  runtime.
- Mover as associações de estado/animação/duração para descritores por lutador;
  tirar dependência de nomes/símbolos Ken/Ryu de `fight.c` sem expandir trabalho
  quente ou RAM sem orçamento medido.
- Provar transições de input, startup/ativo/recovery, hit/guard/hitstop, cancel,
  salto, knockback, KO/reset, timer e melhor de três com input físico e vídeo.
- Repetir paleta, render e orçamento com um segundo modelo CPS2-coerente antes
  de validar a fatia golden.

### G6 — promoção para delivery

- Integrar cenário, dois lutadores, HUD, FX, áudio e round loop numa ROM; medir
  ROM/mapper/bancos, RAM, VRAM, pior quadro, FPS NTSC/PAL, input, áudio e
  proveniência asset→ROM.
- Capturar vídeo de framebuffer fresco da mesma SHA da ROM, passar fidelidade
  visual, semântica, determinismo, vínculo e revisão independente.
- Atualizar memory bank e claims com a evidência exata. Só então considerar
  `delivery`; sem emulador e os sete eixos, o status permanece parcial.

## Prompt para a próxima etapa

```text
[Contexto SMS Carregado]

Continue o projeto em /mnt/sdcard/Projects/SMSForge, cena luta_mugen. Leia
AGENTS.md, doc/05_technical/mugen_engine_standard.md, GDD/TDD/memory bank e
SMS_projects/luta_mugen/doc/18-gap-diagnostico-plano-prompt-2026-09-29.md.
O objetivo deste lote é provar ou refutar um renderer de 2 lutadores a 72–88 px
sem flicker visível, sem glitches, com <=8 sprites/scanline, <=64 na SAT, AIR,
pivôs e CLSN preservados, e cadência ROM 50/60 Hz.

Referência: clone
SMS_projects/luta_mugen/out/local_study/scale_pilot_rom_fast_render/ (ROM SHA
34025741996b6b421aaddbae98ea4e044d119687f1c2444ac1e99c45ee548393). Seu
resultado de ~59,6 fps é útil para desempenho, mas flicker visível, cadência Ken
5,37 frames/pose contra AIR 4 e fragmento não explicado no pé do Ryu reprovam
imagem/cadência. Ele não contém input, combate, HUD ou áudio. Não o chame de
delivery e não substitua a T10 canônica.

Contexto geométrico do corte (44 poses Ken, 32 Ryu): Ken idle opaco 81 px; Ryu
idle 80 px. Bounds máximos separados: Ken 107×41 (KO) e 51×108 (special); Ryu
71×40 (KO) e 30×83 (special). Individualmente o relatório mediu Ken 49 SAT/7
por linha e Ryu 42/7; o par idle dá 55 SAT/11 por linha. Os piores pares
arbitrários especiais e KO deram 91/14 e 69/23; validar quais são alcançáveis
pela coreografia. O idle do par já prova o bloqueio atual de flicker zero.

Regras:
- mantenha T10 e arte fonte intactas; experimente primeiro em clone em
  out/local_study; altere somente o ramo do piloto e documentos luta_mugen;
- não produza o roster/arte final ainda. Preserve a altura de idle 72–88 px,
  proporções, pivôs, offsets, duração AIR e caixas de colisão;
- culling de cells vazias, dedup, cache ou assembly só contam para flicker se
  reduzirem a ocupação real da SAT/scanline. H-blank/raster não remove o limite
  de 8 sprites/linha;
- não assuma que o streaming em display ativo do clone rápido é aceitável; prove
  cumprimento do contrato VBlank ou registre a exceção com medição e artefatos;
- implemente/estenda o gate de zero-flicker descrito no plano, com `--self-check`
  e JSON ligado à SHA; passe-o também em fixtures negativas (sprite omitido,
  resíduo de tile e captura stale) antes de usar o veredito no piloto;
- compare sprite-only compacto/reautorizado. Se não fechar, construa um teste
  mínimo BG/sprite em clone separado e meça transparência/composição, paleta,
  VRAM, bytes/ciclos por frame, oclusão e bordas; não presuma que BG-as-sprite
  funciona;
- se nenhuma rota cumprir simultaneamente escala e zero flicker, pare antes de
  reduzir personagem ou aceitar omissão. Entregue o blocker de hardware e as
  opções de escopo com custo medido;
- só use métricas de ROM cujo build da mesma invocação passou. Faça vídeo fresco
  comparável à mesma SHA; explique o fragmento do Ryu antes de classificar a
  imagem como limpa.

Entrega deste lote: clone candidato com fonte/build/evidência identificados;
tabela por pose/facing de bounds, SAT, pico de linha e AIR; medição de 3000
frames sem overflow; FPS do loop e da animação; vídeo que mostre idle,
locomoção, salto, ataques, especial e KO; decisão PASS/BLOCKED por critério;
atualização do memory bank e próxima ação. Não integre à ROM canônica até o
renderer passar esses critérios.
```
