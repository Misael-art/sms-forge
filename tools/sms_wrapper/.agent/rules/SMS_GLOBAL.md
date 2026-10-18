# SMS_GLOBAL — Lei canônica do SMSForge (sempre ativa)

> Porte da SGDK_GLOBAL (MegaDrive_DEV) para Master System. Seções numeradas;
> lições novas APENDAM seção; regra vira medição, nunca só prosa.

## 1. Fonte de verdade
Hierarquia em `AGENTS.md` da raiz. Estado operacional (`10-memory-bank.md`) >
design (GDD) > processo > headers devkitSMS (API definitiva) > suposição.
Suposição nunca vira resposta; vira pergunta.

## 2. Restrições não negociáveis
Lista ❌ completa vive no AGENTS.md e é espelho desta seção. Violar qualquer
item invalida a entrega inteira — não "com exceção".

## 3. Governança e vocabulário de status
```
documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget
```
Um agente que diz "pronto" sem ROM rodando no emulador comete autoengano —
o crime fundador deste workspace. Claims têm teto aprovado (§17).

## 4. Operação do wrapper
Toda lógica de build/validação vive em `tools/sms_wrapper/`. Projetos têm shims
que delegam. Duplicar lógica = regressão estrutural.

## 5. Handoff
Fim de sessão: memory bank atualizado + handoff curto (o que mudou, próximo passo,
bloqueios). Handoff nunca substitui memory bank nem evidência.

## 6. Lei do VDP (tiles BG)
- Grid 8×8; pattern table 32 bytes/tile (4bpp); espaço de pattern do BG são os
  primeiros 14KB = **448 tiles (índices 0–447)**; acima disso a leitura cai na
  própria name table. A metade alta é dos sprites conforme a base do reg 6 (§27).
- Name table = **entrada de 16 bits por tile** (stride 2 em `XYtoADDR`,
  `SMSlib.h:112`). Flags da entrada: `TILE_FLIPPED_X` 0x0200, `TILE_FLIPPED_Y`
  0x0400, `TILE_USE_SPRITE_PALETTE` 0x0800, `TILE_PRIORITY` 0x1000
  (`SMSlib.h:124-127`). **Provado no framebuffer do emulador** (probe
  `_laboratorio/pnt_16bit`, L069): flip X/Y renderiza, subpaleta de sprite por
  tile funciona, índice 300 (>255) renderiza. "1 byte por tile, sem flip" é
  lei do **SG-1000**, não do SMS — a doutrina teve isso invertido até 2026-09-24.
  `TILE_PRIORITY` só tem efeito com sprite sobreposto: permanece `mapped`.
  **Selo Tier-1 (L132):** a tabela do SMSPower confirma a geometria bit a bit —
  bits 0–8 índice (0–511), 9 flip H ($200), 10 flip V ($400), 11 subpaleta
  sprite ($800), 12 prioridade ($1000) e "13 - 15 Unused — Some games use these
  bits as flags for collision and damage zones" (`Tilemap.txt`, sha256
  `2168bc88…`); tile = 32 bytes de bitplanes por linha, "lowest bit to highest
  bit" (`Tiles.txt`, sha256 `ae995fd6…`). Política dos bits 13–15 na §123.
- Scroll global X/Y. A trava da 1ª coluna **deixa de ser opcional** quando o
  H-scroll está ao vivo: `SMS_setBGScrollX` ≠ 0 exige
  `VDPFEATURE_LEFTCOLBLANK`. Sem isso os 8 px da esquerda mostram lixo do
  tile que ainda não foi buscado (L043). Gate: `audit_hscroll_blank.py`.
- Sinal e janela do h-scroll de PNT parcial: `N = (-cam) & 0xFF` e anel
  mod-32 de colunas reescrito a cada passo de 8 px, inclusive voltando —
  evidência e limites na §126 (L135).
- O split de scroll por line interrupt é **horizontal**: o reg9 vertical é
  lido uma vez por frame e o wrap em modo 192 é 224 — lei, gate e técnica
  Sylvan Tale na §122 (L131).
- Split de scroll exige line interrupt e é técnica medida, não gratuita.
  O contador de linha dispara na linha N **depois** de recarregar no VBlank:
  armar 47 querendo a linha 64 desloca todas as bandas 16 linhas. Banda
  vazia não prova a quebra — ponha forma reconhecível nela (L046).
- Base da name table é o registrador 2; a SMSlib inicializa com `0xFF`.
  No SMS1, reg2 com bit0=0 espelha a tilemap (bit10 do endereço forçado a 0)
  — invisível no emulador SMS2/PC. Lei, medição e exceção: §121 (L130).
  Gate: `audit_tilemap_mirror.py`.

## 7. Lei de sprites
- SAT: máx **64 sprites**; terminador Y=0xD0 corta o processamento
  **somente no modo 192 linhas** (§118, L128).
- Máx **8 sprites por scanline**. O limite é do buffer de parsing: as 8
  primeiras entradas da SAT que caem na linha entram, da 9ª em diante são
  descartadas, e entrada transparente ou fora da tela conta igual (§119, L129).
  "No SMS1 corrompe a linha" constava aqui sem lastro no corpus nem em
  medição: não é lei até ser provado (§23). O simulador
  (`audit_sprite_line_sim.py`) aprova antes do runtime.
- Tamanho global **8×8 ou 8×16**. Zoom ×2 dobra o PIXEL (16×16 / 16×32 na
  tela), não a arte. Nenhum modo é mais largo que 8 px; arte 16×16 exige
  metasprite (§25, L006). "8×8 ou 16×16" como modo VDP é número do Mega Drive.
- X é armazenado **sem offset**: `SMS_addSprite(0, …)` desenha na borda
  esquerda. `VDPFEATURE_SHIFTSPRITES` desloca **8 px**, não 32.
  "X+32" / "X<32 esconde" é número do Mega Drive, refutado (L003, S05).
- Comportamento dependente de revisão (early clock, flips) não vira lei sem
  evidência de emulador/console (§23).

## 8. Lei de paleta
- CRAM tem duas tabelas de 16 entradas: P0 pode ser selecionada por tiles de
  BG; sprites usam P1. Índice 0 é transparente para pixels de sprite em P1,
  mas índice 0 de BG é cor visível (incluindo o backdrop), não alpha — mesmo
  quando um tile BG seleciona P1. Não
  afirmar que os dois índices 0 são transparentes.
- Assets de personagem em PNG indexado usam índice 0 como transparência e até
  15 cores úteis. Isso não significa uma tabela CRAM própria por personagem:
  todos os sprites ativos compartilham P1. Tiles BG podem selecionar P1 para
  reutilizar cores, sem criar entradas CRAM adicionais. A política de runtime
  por jogo deve declarar slots compartilhados e cores ainda não mapeadas.
- Cor = código 6-bit. Contrato de assets: canal×85. Sem gradiente suave;
  fade = recarga de paleta sincronizada ao VBlank.
- Contraste medido em degraus de luma derivada (`audit_luma_floor.py`).
  Adjetivo visual sem piso numérico não entra em spec.
- Traduzir foto/conceito: downscale NEAREST + Floyd-Steinberg **na paleta
  mestra**. Paleta NES/SNES/PICO-8/Game Boy é régua, não CRAM (L055, §32).
  MP4/GIF de partículas não é evidência. Ferramenta:
  `prepare_sms_pixel_art.py`. Skill: `sms-pixel-translate.md`.

## 9. Orçamento VRAM/VBlank (não existe DMA)
- Transferência em massa SÓ dentro do VBlank (janela ≈4.5ms NTSC).
- Orçamento worst-frame POR CENA é contrato em `13-spec-cenas.md`, medido
  ("estimado" é proibido no schema). Folga não medida é timidez (§18).
- Transição de tela que reescreve name table em massa: **desligar o display,
  redesenhar o mapa inteiro, religar**. O resíduo visual de redesenho a meio
  quadro é real e não se limpa linha a linha (L047); não confundir com perda de
  dado — escrita na VRAM fora da janela do VBlank chega íntegra, medido em dois
  emuladores (L136, §127).

## 10. Armadilhas Z80/SDCC (assumir como suspeita até provado)
- `int` = 16-bit signed; multiplicação/divisão caras; float proibido em runtime quente.
- RAM 8KB total (`--data-loc 0xC000`): sem malloc, pools estáticos.
- ISR/NMI curtos; pause = NMI.
- Locais no SDCC-Z80 recarregam via IX; ponteiros `static` no hot path.
  Espelhar tile em runtime (bitrev) troca ROM por CPU — medir o frame.
  Curva paga: STREAM_BYTES 32→59.5 fps, 64→58.3, 96→57.5, 128→55.5,
  256→40 (L045). Folga de ROM comprada com flip não é grátis.
- Física de queda/integração vale por **condição** (altura, flag airborne),
  não pelo rótulo do estado. `y` só dentro de `ST_JUMP` deixa o lutador
  pendurado quando um golpe o tira desse estado (L050).

## 11. Banking e header
- ≤48KB linear sem mapper. Mapper Sega: páginas 16KB nos slots 0x4000/0x8000;
  código não-bancado restrito aos primeiros 32KB.
- Header SEGA em 0x7FF0 exigido pela BIOS regional; `makesms` gera/checksum.

## 12. Áudio
- PSG SN76489: 3 tone + noise. PSGlib é o driver padrão. Arbitração música×SFX
  declarada no TDD. YM2413 é opcional — o jogo precisa funcionar sem FM.
- SFX toca no canal **autorado** no manifesto
  (`doc/audio_provenance_manifest.json`). `PSGSFXPlay(sfx_shot, SFX_CHANNEL3)`
  quando o asset nasceu para `SFX_CHANNEL2` derruba o mix; cooldown não
  recupera (L041). Gate: `audit_psg_channel_binding.py`.
- PSGlib volta ao início no `PSGEnd`. N cópias byte a byte do mesmo frame
  não tocam nada extra e comem ROM. Antes de sacrificar feature por espaço,
  meça a redundância do stream (L051). Gate: `audit_psg_redundancy.py`.

## 13. Timing NTSC/PAL
60 vs 50 Hz: velocidade normalizada via frame counter. Nada de delay loops.
Claim de fps constante exige medição (§17).

## 14. Anti-alucinação devkitSMS
Headers = autoridade #8. Antes de usar API: abrir `SMSlib.h`/`PSGlib.h`.
Mapa conceitual SGDK→SMSlib (NÃO é 1:1):
| Conceito MD | Equivalente SMS |
|---|---|
| DMA queue | transferências manuais dentro do VBlank |
| PAL_setPalette | SMS_loadBGPalette / SMS_loadSpritePalette |
| VDP_setTileMapXY | SMS_setTileatXY (entrada 16-bit com flags — §6) |
| flip por atributo | BG: flag na entrada da name table (§6, L069); sprites: revisão-dependente (§7) |
| XGM2 | PSGlib (+ PSG samples) |
Função que não estiver no header não existe.

## 15. Estética doutrinária
Dark Deco adaptado: contraste alto, luz escassa, silhueta legível a 256×192.
Pixel art autoral obrigatória. Proveniência por asset (`audit_provenance.py`);
pixel nascido de código como personagem/inimigo/boss/cenário final é bloqueado.

## 16. Ciclo de produção de cena
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA.
Medir depois de arte cara foi a lição mais cara da história da metodologia-mãe
(curadoria 2026-08-17): aqui isso é gate, não conselho.

## 17. Claim ceiling executável
Tokens AAA / 60fps / 50fps / pixel-perfect / release só existem com teto aprovado
(`doc/promotion_claims/<token>.json`). `audit_claims.py` reprova o resto.

## 18. Doutrina de audácia
Fechar orçamento sem medir o degrau seguinte é timidity disfarçada de prudência.
Sempre medir o próximo degrau antes de declarar folga.

## 19. Self-check obrigatório
Ferramenta de medição cujo `--self-check` falha não é fonte. Ler saída de
ferramenta sem self-check verde é violação.

## 20. Gate calibrado contra falso positivo
Todo gate precisa reprovar um caso inválido conhecido E aprovar um válido
(`selftest.py`). Gate que nunca reprovou não está calibrado.

## 21. Learning capture obrigatório
Erro → JSON canônico em `doc/curation/` + seção numerada AQUI + ferramenta que mede.
Dedup por chave canônica no ledger. Ledger sem JSON, JSON `fechada_com_ferramenta`
sem `.py` existente, ID fantasma e persona ensinando doutrina supersedida
reprovam. IDs L020–L034 nunca foram emitidos neste repo; L012 é furo
declarado (`doc/curation/id_registry.json`). Gate: `audit_learning_capture.py`
(§43).

## 22. Capacidade declarada com prova antes de promessa
Só declare capacidade que já pagou com build/evidência. "Devo conseguir" não
entra em doc de projeto; entra como risco.

## 23. Fatos pagos com evidência
Fato hardware/software só vira lei quando pago com build + emulador. Enquanto
isso: hipótese marcada, teste agendado.

**Primeiro fato pago (2026-09-01, L003):** `VDPFEATURE_SHIFTSPRITES` desloca
**8 px** (medido 114→106 em duas ROMs idênticas exceto pelo bit) e **não existe
offset +32** — X=0 e X=16 desenham visíveis. A matriz afirmava "32px" e
"X<32 esconde": números do **Mega Drive**, refutados. Probe:
`_laboratorio/early_clock`. Ainda não testado em console real nem entre
revisões SMS1/SMS2 — para isso a lei continua valendo.

**A brecha que permitia isso:** o registry mantinha as duas técnicas
honestamente em `mapped` ("provar em emulador"), mas a matriz `.md` afirmava os
números como NOTA DURA e nenhum gate lia o `.md`. Fato afirmado na leitura
humana sem entrada no registry é claim invisível.
Gate: `audit_mastery_registry.cross_check`.

## 24. Deterministic boot
Boot determinístico obrigatório: mesmo estado inicial toda execução; RNG semeado
por input/frame counter documentado. Evidência comparável exige boot estável.

## 25. Geometria de sprite: nenhum modo é mais largo que 8px
`SPRITEMODE_TALL` é **8×16**, não 16×16. `ZOOMED` dobra o PIXEL, não a arte.
Entidade com arte mais larga que 8px exige **metasprite**, em qualquer modo.
Lição L006 (laboratorio_01): a matriz de maestria S03 afirmava "8×8 ou 16×16" e
custou dias de sprite invisível — doutrina errada gera bug, não só confusão.
Corolário: fato de hardware citado na matriz é lei operante; errá-lo é defeito
de gate, não detalhe de redação.
Gate: `audit_sprite_mode.py` (cruza modo declarado no fonte com largura do asset).

## 26. Binário novo invalida evidência velha
Relinkou a ROM? Toda prova de runtime (boot/gameplay/fps/áudio) volta a `false`
até ser recapturada contra o binário novo. `build_inner.py` rebaixa sozinho:
eixo só sobrevive se a evidência for POSTERIOR à ROM.
Corolário: `--skip-pre-gates` nunca produz `validation_report: true`.
Herança de eixo entre builds vale só para eixos de runtime; `build` e
`validation_report` descrevem a execução atual e não se herdam.
Gate: `build_inner.demote_stale_axes` + `reconcile_claims.py` como pós-gate.

## 27. Base de tiles de sprite: o VDP lê na metade que VOCÊ escolher
Sprite não lê o tile que você cita, e sim o tile que a **base do reg 6** manda.
Sem `SMS_useFirstHalfTilesforSprites(1)`, `SMS_addSprite(...,128)` lê o tile
**384** — VRAM nunca escrita = ruído colorido. BG sai limpo porque usa outra base:
**"BG certo + sprite corrompido" é assinatura deste erro.**
Corolário do L006: a causa-raiz REAL era esta, provada em emulador em 2026-08-31.
As duas leis anteriores estavam certas mas eram camadas de cima:
§25 (geometria/metasprite) e o conversor 4bpp. Três defeitos empilhados sobre o
mesmo sintoma — por isso "corrigir a causa" não resolvia.
Gate: `audit_sprite_mode.py` (sprite citando tile < 256 exige a base declarada).

## 28. Tela de emulador com informação não é tela CORRETA
Variância de luma alta e conformidade de paleta **não distinguem arte de ruído**:
lixo de VRAM usa as mesmas cores da CRAM e tem variância altíssima.
`capture_evidence.py` e `screenshot_semantic_gate.py` provam **origem e
não-vacuidade**, nunca correção. Toda captura que sustente claim visual exige
inspeção do conteúdo — humana ou por comparação com referência esperada.
Fato pago: a evidência da F6 (`cena04_sprites.png`) era uma tela de ruído
aprovada por dois gates e aceita como entrega de "7 eixos true".

**Atualização 2026-09-01 (L016 fechada em parte):** o que a COR não denuncia, a
estrutura de TILE denuncia. Arte real usa poucas cores por bloco 8×8; lixo de
VRAM enche cada bloco. `screenshot_semantic_gate` mede a fração de blocos com
≥8 cores — 0,000 em toda captura limpa do acervo, 0,132–0,274 nas telas de
ruído (a evidência da F6 dá 0,149 e agora REPROVA).
**Cuidado:** esse limiar é ESPECÍFICO DE CENA ESPARSA. Arte autoral detalhada
(120 tiles de 8–15 cores) mede 1,000 na mesma métrica — usá-la como detector
universal reprovaria o jogo inteiro. Experimento registrado em L016.

**Corretude, essa sim, se prova (L016 fechada 2026-09-01):** compare a captura
com a FONTE. `audit_render_fidelity.py` extrai a ESTRUTURA da arte autoral
(quais pixels compartilham cor, independente de qual cor a paleta atribuiu) e a
procura na tela. Índice 0 é transparente e fica FORA da comparação — ali a tela
mostra o cenário, não o sprite. Medido: 100,0% nas capturas limpas, 46–57% nas
telas de ruído. Isso independe da densidade da cena.

## 29. Interação se prova pelo DESLOCAMENTO do objeto controlado
"Fração da tela que mudou" não distingue o jogador obedecendo de um inimigo
caindo, de uma morte, nem (antes do §30) do desktop do usuário. Prova de
gameplay = **o sprite controlado se deslocou na direção comandada**, medido em
pixels nativos (canvas 256×192), não em pixels da janela. Sinal fraco (luma
global) só complementa; nunca fecha o eixo sozinho.
O gate mede o que esta seção já exigia (L038–L040):
1. **Direção:** `sign(dx)` / `sign(dy)` coerente com a tecla. `Right` com
   blob andando para a esquerda é FAIL — abs(dx)≥8 sozinho mentia.
2. **Identidade:** a área do blob rastreado não salta para outro objeto
   (dois lutadores do mesmo tamanho; barril saturado sequestrando).
3. **Eco de input:** se `probe_keys` foi observado e permanece 0x00, o
   canal de teclado não chegou na ROM (L039). Fail-closed. Ausência do
   campo = não observado, não é prova de agência.
4. **Escala:** limiares de forma (6–48 × 6–80) aplicam-se em pixels
   nativos. Scale=2.25 no `.ini` do Emulicious não pode inverter o
   veredito (L040). A escala da janela entra no bundle.
5. **Canal deste host:** em KDE/Wayland, XTEST/xdotool **não** atravessa
   o KWin. O canal é kdotool (foco) + ydotool (uinput). `emulator_input.py`
   escolhe o backend. Canário: reset Ctrl+BackSpace zera `probe_frame`.
   Prova de gameplay por RAM (`input_memory.json` com SHA da ROM) é lastro
   do eixo — pixels aqui são ambíguos (L038). `reconcile_claims` aceita os
   dois lastros.
Gate: `capture_evidence.interaction_verdict` + `emulator_input.py` +
`input_memory.json` (quando a prova for por memória).
Fato pago: no laboratorio_01 o d-pad mexe ~8px/frame e a mudança global máxima
teórica da cena é ~1,2% — abaixo do limiar de 2% que existia. O eixo gameplay
ficou reprovado por meses por limiar mal calibrado, não por bug de jogo.

## 30. Captura tem que provar QUE JANELA fotografou
`spectacle -a` fotografa a janela ATIVA. Emulador sem foco (ou instância zumbi)
produz screenshot do DESKTOP — que passa no detector de vacuidade, pode conter
conteúdo pessoal do usuário e, comparado com outro screenshot de desktop, gera
"interação provada" medindo a área de trabalho mudando.
Regra: toda captura valida o tamanho contra a janela do emulador, descarta o
arquivo se for desktop e refaz com re-foco; `capture_evidence` recusa iniciar
com outra instância viva. Foram encontradas **15 capturas de desktop** no
acervo do laboratorio_01, de sessões anteriores — todas apagadas.

## 31. Evidência de áudio: isolada do usuário e datada pela ROM
Gravar o monitor do sink padrão captura TODO o áudio da máquina — música,
chamadas, notificações do usuário. Proibido. `capture_audio.py` move o fluxo do
emulador para um sink NULO dedicado, grava só esse monitor e o remove ao final.
`.wav` ANTERIOR à ROM não prova o binário atual (§26): `reconcile_claims`
passou a exigir captura posterior — existir um wav no acervo não basta.
**Falso negativo conhecido:** gravar antes de a música entrar em regime produz
WAV 100% silencioso, indistinguível de "o jogo é mudo". Isso quase levou a
"consertar" um bug inexistente. O gate repete com warmup crescente e, se
insistir em silêncio, manda confirmar contra uma ROM histórica com som antes de
tocar no código de áudio.
**Corrida de ambiente (L048):** `peak=0` depois do warmup não autoriza editar
a ROM. Matar Java zumbis do Emulicious e repetir; na mesma rodada, gravar um
controle histórico (binário congelado que já teve som). Se o congelado também
sai mudo, o canal é o host; se o congelado tem som e o atual não, aí sim a
ROM. Recorrência da L019: a mensagem sozinha não impediu a segunda ocorrência.

## 32. Grandeza do SMS se re-deriva, não se traduz
Portar metodologia de outro console é portar **método**, nunca número. Cada
grandeza — 8 sprites/scanline, SAT de 64, 2 subpaletas, 256×192, VRAM 16 KB,
RAM 8 KB, **sem DMA** — vale porque foi re-derivada do Master System.
A L001 dizia isso desde a fundação e mesmo assim recorreu duas vezes: a matriz
afirmou sprite "16×16" (L006, dias de sprite invisível) e "X+32 / early clock
32px" (L003, refutado em emulador). As duas eram números do Mega Drive.
Prosa não impediu; agora um gate lê os documentos e confere as grandezas.
Gate: `audit_hardware_constants.py`.

## 33. Instrumento quebrado inverte o diagnóstico
Antes de acusar a função sob teste, prove o INSTRUMENTO contra um caso conhecido.
L009 concluiu que `SMS_loadTiles` travava; em 2026-09-01 o probe
`_laboratorio/loadtiles_hang` mostrou que a função completa nas duas condições
(display ligado e desligado, 4 chamadas seguidas). O que falhava era a medição:
marcador `__at()` **sem `volatile`** é eliminado pelo SDCC (a escrita não é lida
em lugar nenhum do C) e a leitura DAP do Emulicious vem prefixada com `$`.
Mesmo padrão do falso negativo de áudio (§31) e do "sprite invisível" (§27).
Corolário (L035): "ler na tela" era a resposta certa quando o único canal
disponível era o depurador mal usado — não vire doutrina permanente. Quando
a medição é de estado/taxa, o canal certo é memória viva; construir o canal
vale mais que compensá-lo com heurística de pixels (§37).
Antes de teorizar estouro de VBlank, corrida de latch ou VDP "quebrado",
inspecione o **conteúdo que já está no asset/VRAM**. Alfabeto embutido no
tileset + fonte nova = "KKEN" na tela, não bug de hardware (L044). Classe
causal: `asset_content_mismatch`.
Gate: `audit_debug_markers.py`, no pré-gate do build.

## 34. Captura alveja a JANELA; foco se verifica, não se supõe
`spectacle -a` fotografa a janela **ativa** — e já fotografou o desktop do
usuário (§30/L017). `import -window <id>` alveja por ID: capturar outra coisa
deixa de ser possível, em vez de ser detectável depois. É também mais limpo
(256×217, sem barra de título) e dispensa o shim de libavcodec, que passa a
valer só para o fallback.
`xdotool windowactivate` **não garante foco**: verifique com
`getwindowfocus` antes de CADA tecla e reative até concordar; se não conseguir,
falhe alto — tecla enviada para outra janela vira "input que não mudou nada".
**Neste host (KDE/Wayland) xdotool fica cego** (`getwindowfocus` vazio) e o
XTEST não entrega evento ao cliente Xwayland (L039). Canal: kdotool +
ydotool via `emulator_input.py`. O fallback xdotool só vale em sessão X11.
**Área de jogo se deriva do hardware, não se chuta:** a canvas é 256×192,
ancorada embaixo da moldura e centrada na horizontal. A fração fixa de 28% que
existia antes cortava 60px de jogo na captura sem moldura.
Gate: `capture_evidence.game_area` + `_shoot_window` + `emulator_input.py`.

## 35. Coordenada de tile não é checada por ninguém — XYtoADDR é aritmética pura
`XYtoADDR(x,y) = SMS_PNTAddress|((((y)<<5)+(x))<<1)`. Não satura, não valida,
não avisa. Escrever fora dos limites falha de **duas** maneiras diferentes, e
tratá-las como uma só custou a L011:
- `y` em **24..27** → cai na cauda da PNT que o modo 192 linhas não renderiza.
  Nada quebra e nada aparece. Foi o `"VITORIA!"` da linha 26.
- `y >= 28` → passa de `0x3EFF` e invade `0x3F00`, a **SAT**. O "texto"
  reposiciona sprites.
- `x >= 32` → `<<5` não satura: `x=33,y=3` é o mesmo endereço que `x=1,y=4`.
As 24 linhas valem para o modo padrão; só com `VDPFEATURE_224LINES` a linha 26
passa a ser legítima. Coordenada vinda de variável **não** é aprovada em
silêncio: é reportada como não provada.
Gate: `audit_tilemap_bounds.py`, no pré-gate do build.

## 36. FPS do título prova o EMULADOR; o eixo é sobre o JOGO
`Emulicious - 100% (60 fps)` é velocidade de **emulação**: o quanto o host deu
conta. Uma ROM parada num laço vazio mantém o título em 60 fps, porque o Z80
emulado continua girando — só não desenha nada novo. Fechar `fps_constante` só
com o título é medir o instrumento, não o jogo.
Prova independente: o contador de frames que a própria ROM desenha na tela. Não
é preciso **ler** o dígito (isso exigiria a fonte, que só existe dentro do
`SMSlib.lib`); basta cronometrar quando o bloco 8×8 **muda**.
Quatro armadilhas, todas encontradas medindo e nenhuma prevista:
1. **Folga de Nyquist se confere no intervalo medido, não no pedido.** Cada
   captura leva ~1,5s se a janela for reativada a cada tiro; um `--interval
   0.3` virava 1,5s real, e a folga declarada de 7,1× era de 1,4×.
2. **Assinar RGB conta o cenário.** O backdrop piscando muda os pixels de cor 0
   do tile. Assine a **forma** (pixel ≠ cor dominante da célula): fundo trocando
   de cor inteiro continua dominante e a máscara não se mexe.
3. **`import` fotografa durante o repaint** e o dígito sai rasgado — um estado
   de 1 amostra que transforma uma troca em duas.
4. **Contar transições e dividir pela janela quantiza nas bordas** (±8 fps com
   período 128 numa janela de 16s) e um único rasgo sobrevivente contamina tudo.
   Use a **mediana das durações de estado**: robusta a outlier, e a dispersão
   em volta dela é literalmente o que o eixo se chama — constante, não médio.
Estimar o período e classificar artefato com o mesmo limiar é circular.
Gate: `measure_frame_advance.py`, ao lado (não no lugar) de `measure_fps.py`.

## 37. Escrita sem leitor não é canal — e canal condenado por instrumento só reabre com fato pago
Os probes de `0xC7F0` existiam no fonte e NENHUMA ferramenta lia: o
diagnóstico de runtime corria por pixels — foco do gerenciador de janelas
(§34), rasgo de captura e Nyquist de screenshot (§36) — enquanto o estado
completo do jogo estava a um read de distância. A L010 condenara o canal
DAP inteiro porque `evaluate` "retornava `$0` para qualquer endereço"; o
que avaliava mal era a EXPRESSÃO: `0xC7F0` avalia ao próprio número, ler
memória é `@0xC7F0` (byte) ou `word.ram@@0xC7F0` (word) — a
`Expressions.txt` do emulador documentava tudo. O §33 já tinha o nome para
isso (instrumento quebrado inverte o diagnóstico) e mesmo assim o canal
morreu condenado. Fatos operacionais pagos 2026-09-04 contra
Emulicious 2026-03-27:
1. UM pedido não-suportado MATA a thread do adaptador (`Unhandled request`
   no log) e todo pedido seguinte pende — cliente DAP com whitelist
   fechada e timeout em toda espera;
2. sessão aberta antes do boot da ROM fica stale: initialize/attach
   respondem, evaluate pende. Canário `@addr` decide; sem resposta,
   reconecta (reconectar é seguro);
3. este build NÃO TEM rota de escrita (readMemory/writeMemory/
   setVariable/setExpression ausentes; `=` é comparação, provado por
   readback) — input segue por teclado com eco em `probe_keys`; agência
   por escrita em memória é finding aberto, não promessa (§22).
Leitura de memória só com a emulação pausada; o relógio da janela de fps é
conservador (marca antes do continue e antes do pause) para nunca inflar o
fps acima do real.
Estado que dura ~20 frames não se prova por screenshot: a mesma chamada
cai na luta numa execução e no título em outra (L054). Exponha a pose/
facing no probe (custo zero de RAM) e leia a variável. Fotografar a
"pose certa" é sorteio; ler `probe_pose` é medição.
Gate: `measure_runtime_probe.py` — magic "SMRT" + schema antes de qualquer
métrica (o §26 visto pelo consumidor); fps por delta de `probe_frame`
sobre o tempo de EXECUÇÃO.

## 38. Persistência causal: relatório não é entrega
Diagnóstico, correção de ferramenta, build isolado, captura ou um único
milestone são transições, não o fim da execução. Depois de registrar o
resultado, escolha a próxima lacuna causal e continue.
Duas tentativas equivalentes sem evidência nova encerram a **rota**, não o
projeto. Documento/build com `blockers_removed=0` não é progresso.
Mismatch de representação (dimensão, indexação, grid) não é gate humano:
mude a representação ou o produtor. Escala `locked` reautoriza no grid;
probe maior é evidência, nunca substituto. GUI por ponteiro é
`interaction_channel_mismatch`. Conteúdo já presente no asset/VRAM que o
agente teorizou como bug de VDP é `asset_content_mismatch` (L044).
Afinar o roteiro da atração/demo para o próprio teste passar é
`evidence_script_tuned_to_pass` (L053): reporte o caminho como não
observado; não fabrique a evidência.
Um blocker de arte não paralisa gameplay/áudio/QA; um blocker de captura não
paralisa produção visual. Gate humano registra a pergunta e continua só os
ramos independentes — aprovação humana não se simula.
Pare somente por ação destrutiva/externa sem autorização, licença ausente,
contradição de autoridades, decisão humana irredutível sem ramo independente,
impossibilidade de hardware medida, ou rotas seguras esgotadas.
Gate: `audit_causal_persistence.py`. Workflow: `causal-persistence-loop.md`.

## 39. Época visual: boot não é qualidade
Captura que prova boot, foco de janela e rota Linux classifica no máximo
`runtime_probe_passed_visual_epoch_failed`. Não prova cena final, escala,
gameplay completo nem AAA. PNG indexado, ≤15 úteis e 6-bit são **sintaxe**;
qualidade é época `delivery` com personagens distintos, palco autoral sem
branding de engine, HUD sem overlap e escala contratada no GDD.
Blockers permanentes: `wrong_visual_epoch`,
`placeholder_or_probe_in_delivery_scene`, `duplicate_character_asset`,
`entity_scale_below_contract`, `stage_contains_branding_or_reference_screen`,
`hud_overlap_or_clipping`, `rom_asset_binding_unproven`.
Canvas da composição é 256×192 (224 só com `VDPFEATURE_224LINES`). Copiar
320×224 do Mega Drive é violação do §32, não "benchmark".
Não promover `probe`, `reference_only`, `negative_case_evidence`,
`technical_candidate`, `visual_lab_control` nem tela HAMOOPIG/splash como palco.
Não reutilizar o mesmo PNG para dois personagens. Não reduzir personagem só
para economizar tiles.
BG e HUD não podem ser o objeto mais saturado com forma de sprite — isso
sequestra o detector de gameplay e some com o jogador (L042). Lutador/
jogador é o pico de leitura. Com ROM cheia, composição (paleta, pose, fonte
já carregada) precede asset novo (L049).
Gate: `audit_visual_delivery.py`. Skill: `sms-visual-excellence.md`.

## 40. Vínculo asset → ROM é prova, não convenção
Source PNG → caminho em `res/` → símbolo gerado → SHA-256 da ROM. Boot de
uma ROM não prova que a arte autoral está naquele binário. Mapa ausente,
SHA divergente ou símbolo duplicado = `rom_asset_binding_unproven`.
Entrega (`--require` / `--delivery`) falha fechado sem o mapa.
Gate: `audit_rom_asset_binding.py`. Schema: `rom_asset_binding_v1`.

## 41. Review independente e orquestração limitada
Checkpoints `foundation` / `pre_growth` / `vertical_slice` / `release_candidate`
exigem review read-only, no máximo três domínios, hash-bound, sem autoaprovação
e sem declarar `ready_for_aaa`. Parecer stale (SHA divergente) cai.
Trabalho realmente independente pode ir em paralelo em até **três** ramos
(`visual`, `runtime`, `audio_qa`). Claim, promoção, git e memória ficam no
coordenador. Worker que promove ou eleva teto é contrato violado.
Gates: `quality_review_router.py`, `harness_orchestration.py`.
Workflows: `independent-quality-review.md`, `production-loop.md`.

## 42. Animação semântica não é rename de frame
Strip reordenado, ação clonada com outro nome, ciclo de um único frame
repetido ou pivot oscilando não são animação. Roster exigido pelo GDD
ausente reprova. Sintaxe de PNG e SAT não medem isso.
Gate: `audit_animation_semantics.py`. Skill: `sms-sprite-animation.md`.

## 43. Captura de lição é medida, não caderno
§21 exigia JSON + seção + ferramenta. O agente passou a gravar L038–L049
só no ledger: prosa com `dedup_key`. Recorrência da própria regra de
aprendizado. Relatório de lição sem JSON canônico não é captura.
IDs L020–L034 nunca foram emitidos neste repo; L012 é furo declarado.
Citar L023/L025 como lições SMSForge é número da fábrica-mãe, não ID
deste acervo (aliases reais: L007, L013/§36).
Persona/skill que ensina doutrina supersedida — X+32, TALL=16×16, DAP
"retorna $0", monitor do sink default como captura, openMSX como gate
SMS — é regressão, mesmo que a matriz/lei já tenham sido corrigidas.
Gate: `audit_learning_capture.py`. Registro: `doc/curation/id_registry.json`.

## 44. Tamanho de símbolo tem uma fonte
`#define FOO_SIZE` e `foo[N]` (e o mesmo define em dois headers) têm de
coincidir. Escrever o tamanho à mão num header-índice enquanto a folha
encolhe faz o consumidor ler além do array — sem sintoma visível, porque
o metasprite não referencia os tiles extras (L052). Header gerado a partir
da folha; `--check` no gerador. Gate: `audit_symbol_size_sync.py`.

## 45. Estado transitório se grava; screenshot dele é sorteio
O §36 (Nyquist de screenshot) e a L054 (pose no probe) dizem o mesmo defeito por
dois ângulos: um PNG não tem eixo do tempo, então transição, animação e game
feel ficam sem lastro. O canal que faltava não era outra heurística de pixel —
era **gravar**. O Emulicious grava do FRAMEBUFFER (256×192 exatos, sem moldura,
sem menu, sem desktop), o que também torna impossível vazar a tela do usuário
(§30/L017) em vez de detectá-lo depois.
Atalho instalado em `Emulicious.ini` com prefixo `Keys` (F7 inicia, F8 para);
encode por FFMPEG externo (`FFMPEGPath`). Gate: `capture_video.py`.
**Não confunda com a L055:** o que ela recusa é MP4/GIF de *mood* gerado por
ferramenta de arte apresentado como prova de ROM. Vídeo do framebuffer do
emulador rodando a ROM selada é o oposto disso — tem cadeia de custódia.
Três falhas MUDAS que o gate agora fecha (cada uma custou uma execução):
1. Instância zumbi do emulador rouba o foco **e reescreve o `.ini` ao morrer**,
   apagando o atalho recém-instalado. Abortar se já houver Emulicious vivo.
2. F10 não para a gravação: no Swing/AWT é o atalho da barra de menus. A
   gravação seguia aberta e era finalizada **ao morrer o processo** — saía um
   `.mp4` válido que parecia prova de que o atalho pegou.
3. Mover o `.mp4` quando o tamanho para de crescer o corrompe: o FFMPEG ainda
   reabre o arquivo para escrever o atom `moov`. Critério = ffprobe consegue ler.
A trilha de áudio é anexada pelo gate: o `temp.wav` do emulador declara no
chunk `data` o DOBRO dos bytes que existem, o FFMPEG batia em EOF na metade e
descartava o som. Formato lido do `fmt `, nunca constante; payload mudo não é
anexado (L048); e o remux **não pode encurtar o vídeo** — `-shortest` cortou
455 → 452 frames e o guard recusou.
Limite honesto: o vídeo prova que a ROM renderizou, que a imagem mudou e que
havia som. Não prova mecânica correta nem que a música é a certa (§28/§31).

## 46. Busca de janela por NOME exige campo livre — senão o gate mede outra ROM
`xdotool/kdotool search --name Emulicious` devolve a janela de **qualquer**
instância, e todo ponto de captura pega a primeira. Com um zumbi vivo o gate não
falha: ele mede o binário errado e emite **veredito confiante sobre o seu**.
**Demonstrado 2026-09-07:** com um Emulicious de MSSF2T rodando,
`audit_deterministic_boot --rom laboratorio_01.sms` respondeu
`[FAIL] boot NAO deterministico` — e o PNG que ele julgou mostra Ken × Guile,
"ROUND 1". Determinismo é o eixo mais exposto: zumbi PARADO dá hashes idênticos
(falso PASS), zumbi ANIMANDO dá divergentes (falso FAIL).
O perigo já tinha lei (§34/L017) e mesmo assim tinha **três tratamentos**: dois
gates abortavam, um matava, e dois não faziam nada. Lei sem enforcement uniforme
é lei só onde alguém lembrou.
Política histórica: ABORT por padrão e KILL na retentativa de áudio (L048).
**Supersedida pelo §93:** descobrir um PID não prova propriedade; KILL global
foi removido. A rota antiga aborta em presença de outra instância; a privada
permite concorrência e encerra apenas seus filhos identificados.
**Detecção é por JVM, não por linha de comando:** `pgrep -f` casa também o SHELL
que invocou a ferramenta — medido, 3 PIDs onde havia 1 emulador. Confirme
`argv[0]` ser `java`, senão o gate aborta por causa de quem o chamou.

## 47. Proveniência de áudio tem gate próprio
O `audit_provenance.py` cobre só PNG — e foi por esse furo que um `.psg`
entrou na ROM sem entrada no manifest: `music_ken_stage.psg` (MSSF2T,
2026-09-07) foi parar no `res/audio/` e nenhum gate tinha o que reprovar
(L058). O `audit_psg_channel_binding.py` lê o mesmo manifest, mas só amarra
canal de SFX: arquivo coberto por UM gate não fica coberto nos outros eixos.
Manifest: `doc/audio_provenance_manifest.json`, mesma estrutura
`{"assets": [...]}` com `file` relativo (ex.: `res/audio/x.psg`) que o gate
de canal já consome — o gate novo é aditivo, não substitui ninguém.
Três eixos, todos executáveis:
1. **Cobertura:** todo `.psg` em `res/audio/` tem entrada no manifest.
   Órfão reprova — "está na ROM" não é procedência.
2. **Integridade:** `sha256` e `bytes` declarados batem com o blob em disco;
   asset que mudou sem re-declarar reprova (mesmo princípio do visual).
3. **Referência de port:** `origin` com transcrição/port/arranjo exige
   `reference` `{file, sha256}` — o arquivo referenciado existe e o hash
   bate. Jogo portado de referência comercial com trilha "autoral genérica"
   no lugar do porte é troca silenciosa de obra (L059); port sem referência
   hasheada não é port provado, é intenção. Autoral pura não deve reference.
Gate: `audit_audio_provenance.py`.


## 48. Prova de golpe contra a IA lê o estado do oponente (L060)
Whiff não é defeito de colisão enquanto o defensor não estiver na prova. O
"soco conecta às vezes" do MSSF2T virou três semanas de teoria errada
("janela de 4 px" entre `PUSH_W` e a caixa) porque a leitura de código não
era instrumentada. Os probes dataram a causa real: a IA recua ANDANDO com
guarda quando o jogador ataca e `(g_frame & 8)` (ST_WALK_B, gap 20->28
dentro da janela ativa), contra-ataca antes do nosso ativo e acerta chute em
quem agacha. Regra executável:
1. Prova de golpe carrega `P[1].state`/`P[1].guard` (byte do oponente) junto
   com o resultado — whiff sem estado do defensor não tem causa.
2. Cronometragem contra IA é por TEMPO DE RELÓGIO com o emulador rodando
   contínuo; polling DAP pausado tem granularidade de 2-4 frames e janela
   fixa de frames erra por ±8 px (medido).
3. Atribuição de dano a golpe exige dano compatível (soco 7, chute 10,
   projétil 12, chip 2) — queda de 10 com "pose de soco por perto" é chute,
   não soco.
Gate: `prove_input_memory.py` (punch_window, linha_tempo_b1, P1_STATES).

## 49. Orçamento de frame se mede com instrumento na ROM (L061)
Orçamento "declarado" em spec não fecha eixo nenhum — e o degrau seguinte é
um instrumento que mora na ROM, não na bancada. Padrão do probe SMRT:
`probe_vline` (VCounter lido NO FIM do trabalho do frame, antes do wait de
VBlank) + `probe_vovf` (word não saturante de frames que terminaram fora do
VBlank). `0xC0` é a ENTRADA do VBlank em NTSC; o período seguro continua pelas
linhas de contador `0xC0–0xDA, 0xD5–0xFF`. O trabalho derramou quando o contador
deu a volta e a leitura caiu abaixo de `0xC0`. O contador é a evidência dura
(imune a amostragem); o vline é o contexto. Derrame não derruba fps — espreme
o streaming de VRAM, então "fps 60" não absolve orçamento estourado. Pior caso declarado é o que a
medição usa (troca de pose + HUD + projéteis), não o caminho vazio.
Gate: `measure_worst_frame.py` (por projeto; molde com `--self-check`).

## 50. Estado raro de UI se captura com roteiro que o força (L062)
Banner de 120 frames não cai em keyframe uniforme — três gravações de 100s
perderam o "K.O." com 8/12 frames. Roteiro executável: (1) input que tira a
ROM do modo atração e FORÇA o estado (pressão contínua em direção ao
oponente esvazia hp antes do TIME UP); (2) gravação com folga (o round é
mais longo que o palpite); (3) extração densa (fps=1) para localizar o
frame; (4) frame extraído vira artefato nomeado, o vídeo selado prova a
cadeia. Sorte de keyframe não é método; roteiro é.
Gate: `capture_video.py` (--press com roteiro de força).

## 51. Falha total de canal DAP: suspeitar de diálogo modal e de vão de sessão (L063, L064)
Dois modos de falha total, ambos com cara de "ambiente instável":
1. **Diálogo modal bloqueia o carregamento da ROM** (L063): o Emulicious
   abriu "Update Behaviour" no boot; a ROM da linha de comando nunca carrega,
   o debugger interno nasce null e TODO `evaluate` NPE-ia
   ("DAPDebugger.debugger is null") com a porta TCP VIVA — as ferramentas
   diziam "canal DAP não ficou vivo" e a culpa caía no jogo/medição.
   Diagnóstico executável: título da janela sem o nome da ROM + janela de
   diálogo via `kdotool search`. Correção persistente no ini (`Update=0`);
   config do emulador é suspeita padrão quando o canário NPE-ia com porta
   respondendo.
2. **Evidência fresca morre em vão entre turnos** (L064): a janela de frescor
   do selo (120 min) atravessa vãos de horas entre turnos do agente — a
   cadeia completa (capturas -> selo) roda em UM único comando, sem depender
   de turno. E `rom_asset_binding.json` é escrito à mão: atualizar no mesmo
   ciclo do rebuild — defasou duas gerações (09ed345a -> 1800c79c ->
   0f4963c0) antes de alguém reparar.
Gate: `emulator_session.py` + `seal_fresh_evidence_bundle.py`.

## 52. Gesto de comando nao paga delay de harness (L065, L066, L067)
Um buffer de 8 ticks a 60 Hz é ~133 ms. `press_spec()` que chama
`focus_wayland()` (~300 ms) **antes de cada tecla** espalha Down→Right→A
por ~18 frames e o Down sai do hist antes do A. Isso nao prova que o QCF
da ROM esta quebrado.

Regras executaveis:
1. Gestos encadeados usam **um unico foco** e `press_spec(..., refocus=False)`.
   Default `refocus=True` permanece para teclas isoladas (andar, soco).
2. Prova de QCF le hist/qcf/SP/estado no maximo alguns frames apos o botao,
   nao 0,9 s depois (a janela de 8 ticks ja e so neutro).
3. Se `qcf==1` e o especial nao entra, suspeitar da **borda** de B1
   (KEY_PRESSED) atrasada 1-3 frames — aceitar HOLD na mesma janela de 8.
   Nao alargar `hist[]` para caber o harness.
Gate: `emulator_input.py` (`refocus`, `qcf_fits` no `--self-check`).
HAMOOPIG: `tools/prove_special.py` + probe `0xC7D0`.

## 53. build_record nao e memory bank (L068)
`out/build_record.json` grava eixos no compile. Runtime nasce `false` e so
sobe no **proximo** build se `axis_support()` achar artefato no contrato da
fabrica (`evidence.json` informative, `fps.json`, `input_memory.json`).
Editar `axes` a mao e proibido (release-rom). Divergencia "memory bank diz
testado / build_record diz false" e esperada ate o rebuild com evidencias
mais novas que a ROM — autoridade #1 continua o memory bank.
Gate: `reconcile_claims.py` (reprova `true` sem lastro; nao promove a mao).

## 54. Doutrina de hardware é claim medido contra o header (L069)
Até 2026-09-24 o §6 ensinava a name table do **SG-1000** (1 byte/tile, sem
flip, 256 tiles) como lei do SMS — em 7 arquivos. Os testes de host passaram
59/59 com a doutrina errada porque nenhum gate lia `SMSlib.h` contra a prosa:
`audit_hardware_constants` confere número entre consoles, `audit_doc_sync`
casa gate↔doc. Nenhum casava **doc↔API**.

Regra: a autoridade #8 vira **dado**, não comentário.
1. `audit_header_claims.py` parseia os defines reais (`TILE_FLIPPED_X/Y`,
   `TILE_USE_SPRITE_PALETTE`, `TILE_PRIORITY`, stride de `XYtoADDR`) e
   reprova as formas erradas na doutrina — nota de correção e fixture
   reprovada podem citar o errado (mesma política de contexto do §L001).
2. O §6 é obrigado a citar os quatro defines **com os valores do header**:
   se o SDK mudar e a prosa não acompanhar, o gate pega em flagrante.
3. A lei nova é provada em pixel, não em man page: probe
   `_laboratorio/pnt_16bit` (flip X/Y, subpaleta de sprite por tile e índice
   300 renderizados no framebuffer 256×192 do Emulicious). Entrada da PNT é
   16-bit; espaço de pattern do BG são 448 tiles (0–447).
Gate: `audit_header_claims.py` (--self-check com as 5 formas que o acervo
carregou como regressão).

## 55. SMS_init não limpa VRAM; evidência estática precisa de pulso (L070)
Observado na primeira captura do probe `pnt_16bit`: com a name table zerada e
tile 0 nunca carregado, o "fundo preto" saiu como ruído colorido — o padrão de
tile 0 era lixo de power-on. Consequências executáveis:
1. Toda cena/probe que confia em "tile 0 = apagado" **carrega** o padrão zero
   (`SMS_loadTiles(zeros, 0, 32)`) — VRAM não nasce limpa.
2. `capture_video.py` reprova tela congelada por design (§45). Um probe de
   padrão estático precisa de um elemento **incidental** animado (faixa
   piscante fora da área medida) para a gravação existir; a animação não é o
   objeto da leitura e o veredito continua vindo da comparação entre células.
Gate: leitura mecânica `SMS_projects/_laboratorio/pnt_16bit/probe_read.py`
(predicados relacionais espelhoX/espelhoY/cor-forma entre células — não
depende de interpretar o formato planar).

## 56. RAM fixa é contrato: um endereço, um mapa, todas as ferramentas (L071)
Observado na reconciliação do kage_matsuri (2026-09-25): o probe local vivia
`s0_x/s1_x` em 0xC7EC/0xC7ED — exatamente onde o `measure_worst_frame.py`
canônico lê o byte ALTO da word `vovf` (0xC7EB) e a `phase` (0xC7ED). Duas
ferramentas liam a mesma RAM com mapas diferentes: os números de worst-frame
do kage misturavam coordenada de samurai com contador de derrame. E o
contador era byte com guarda `!= 0xFF` — saturação, reset e estouro
indistinguíveis, o defeito que o curador apontou.

Regra:
1. O esquema SMRT é canônico e aditivo: magic 0xC7E0–E3, schema 0xC7E4,
   vline 0xC7EA, **vovf como word em 0xC7EB**, phase 0xC7ED,
   `worst_done` 0xC7EE, `vline_min` 0xC7EF, frame 0xC7F0, state 0xC7F6.
   Esses endereços são reservados pelo contrato comum; nenhum probe local os
   reutiliza para coordenadas.
2. Acumulador de evidência (`vovf`) é word, sem guarda de saturação, e zera
   **só no boot** — reset de partida não pode comer a contagem no meio da
   janela de medida.
3. A folga do banco manda: cada `__at` guardado custa ~5–7 B; contador
   redundante (incrementado sob a mesma condição de outro e nunca consumido)
   é removido antes de pedir banking (o `probe_missed` comeu o build do
   MSSF2T inteiro: Bank 1 overflow por 16 B).
Correção L082: números históricos de `vovf_delta` e `vline_max` colhidos pela
condição antiga (`vline >= 0xC0`) não provam derrame; a condição contava frames
que ainda estavam no VBlank. Repetir essas medições com o critério corrigido.
Gate: `measure_worst_frame.py --self-check` (vline-baixo-sem-contador =
sem_lastro) + fixture de fonte com janela selada.

## 57. Gate calibrado em captura escalada não vale em escala nativa (L072)
Observado na reconciliação do kage: o boot em 256×217 (escala 1) reprovava o
`screenshot_semantic_gate` com "6,7% dos blocos 8×8 ≥8 cores — lixo de VRAM",
limiar 5% calibrado em 2026-09-01 sobre capturas de janela escalada, onde o
bloco 8×8 da janela cobre só parte do tile. Em escala nativa o bloco **é** o
tile: arte densa legítima passa de 5% fácil. Separação medida no acervo:
arte autoral nativa 2,3–6,7%; ruído de VRAM sintético em escala nativa
**100%**.

Regra: a unidade de forma de um gate de pixel é o TILE, não o pixel da
janela. Onde isso não puder ser normalizado, o limiar declara a escala a que
pertence. O gate agora escolhe o teto por escala (5% escalada / 30% nativa)
e o `--self-check` carrega as duas fixtures da fronteira: arte densa nativa
aprova, ruído nativo reprova. Consequência geral: ao trocar o ambiente de
captura (ini do Emulicious, scale, moldura), revalidar todo gate cujo
veredito dependa de geometria de pixel — a troca é mudança de unidade de
medida, não detalhe de UI.

## 58. ROM com SHA que muda com o calendário não sustenta selo (L073)
Recorrência declarada: o MSSF2T perdeu o selo em 2026-09-09 por
`SMS_EMBED_SDSC_HEADER_AUTO_DATE` (2 bytes de data no SDSC); o kage_matsuri
chegou 2026-09-25 com o mesmo macro e o mesmo sintoma — bank anunciando SHA
de outro dia (`283e250a…` vs `1e6c4e9b…` em disco), o que o curador leu
corretamente como "memória operacional vencida". Pinado nos dois
(`SMS_EMBED_SDSC_HEADER[_16KB](...,data fixa)`), provado por dois rebuilds
byte-idênticos.

Regra: projeto que sela evidência por SHA usa SDSC pinado; rebuild não pode
mudar o binário sem mudar código. Ainda usam AUTO_DATE no acervo:
`arena_nocturna`, `laboratorio_01` — ao selar evidência neles, pinar primeiro
e registrar a SHA nova no bank. Degrau aberto (handoff curadoria): gate que
casa "bank anuncia SHA X" contra "rebuild produz X" e contra AUTO_DATE no
fonte; enquanto não existe, a recorrência fica registrada aqui e no ledger.

## 59. Receita de combate: o contrato do golpe é datado do fonte, não do relato (L074)

A capacidade de combate do MSSF2T vivia só no memory bank ("soco −7 provado").
Regra: capacidade de gameplay promovida ao agente canônico sai como **receita
de seis partes** — contrato, exemplo mínimo (código real, com arquivo e linha),
comando de reprodução, caso válido/inválido (com a fixture que reprova), vídeo
nativo e SHA da ROM — e a evidência nativa é re-gerada contra a ROM selada,
nunca reutilizada de binário antigo. O contrato do golpe: janela
startup/active/recovery por movimento, um-golpe-um-acerto (`hit_used`), dano
atribuível por movimento (soco 7, chute 10, projétil 12, chip 2), guarda
posicional (trás + de frente + no chão), snapshot de contatos antes do
veredito (trade/duplo-KO não dependem de ordem P0/P1), impacto com hitstop +
shake + pose. Skill: `skills/sms-recipe-combate-1v1.md`.

## 60. Receita de animação: pose não mente, dívida não some — entra escrita (L075)

A receita de animação/impacto só vale com a limitação dentro dela: hoje cada
golpe é UM frame estático e o chute reusa a pose do soco; animação por
movimento (2–4 frames/golpe) depende de banking aprovado e **não pode ser
claimada antes**. O que está pago e é claimável: folha própria por pose (8 no
molde), convenção única de orientação (folhas face-left) com flip em runtime,
upload de pose medido no orçamento de VBlank (worst-frame com contador WORD:
181/235 no MSSF2T, 67/245 no ciclo kage — números selados, não promessa),
física por altura (`airborne()`) e não por estado. Skill:
`skills/sms-recipe-animacao-impacto.md`.

## 61. Receita de asset→ROM: todo pixel com gate por arco e vínculo por hash (L076)

"Tenho um PNG" e "este pixel está nesta ROM" são afirmações de mundos
diferentes. A receita canônica da cadeia: fonte com proveniência → PNG no
contrato (mestra 6-bit, índice 0, ≤15 úteis, grid 8) → tiles 4bpp de 32 B
(caminho 2bpp é outro: `SMS_load2bppTiles`) → símbolo com tamanho derivado da
folha → build com pré-gates → binding asset→ROM **por hash** → SHA invariante
de fonte (SDSC pinado). Cada furo da cadeia já existiu no acervo e tem gate
nomeado na skill: L006, L051, L052, L058, L065/L073. Skill:
`skills/sms-recipe-asset-a-rom.md`.

## 62. Gate mede contrato de instrumentação, não endereço (L077)

Auditoria do corpus (25/09): `measure_worst_frame.py` deu **pass** a uma ROM
sem probe nenhum (`laboratorio_01`) — lia 0xEA/0xEB sem autenticar nada, e
RAM sem dono tem exatamente a assinatura de "orçamento folgado": lixo baixo e
contador parado. `arena_nocturna` reprovara por sorte (lixo ≥ 0xC0 gerou a
contradição do `sem_lastro`), não por desenho. O header `SMRT` na RAM também
não basta: arena escreve magic+schema e não instrumenta worst-frame —
identidade sem instrumentação não é medição.

Regra: gate de leitura de RAM responde **"quem escreve este byte?"** com
verificação, não com suposição. `measure_worst_frame` agora exige (a) fonte
da ROM declarando a triade canônica — vline 0xEA, **vovf WORD** 0xEB (rejeita
byte: é a regressão L071), phase 0xED — antes de abrir emulador, e (b) header
SMRT+schema na RAM. Veredito novo `sem_contrato` (exit 1): ROM sem
instrumentação não tem orçamento — nem "pass", nem "derramou" — e não entra
no ledger. Generaliza §56: um endereço só vale onde uma ferramenta provou que
a ROM o escreve.

## 63. Presença e política de eventos não aprovam composição sozinhas (L078)
O feedback auditivo de 2026-09-25 motivou análise do stream além de presença.
Seu ledger é histórico: a interpretação do bit de ruído foi corrigida em
2026-10-13 (§64). `audit_psg_quality.py` mede políticas de eventos PSGlib
simples na primeira passagem, não timbre percebido ou qualidade musical.
Gap médio entre escritas não é gap mínimo entre notas nem andamento audível;
reescrever o mesmo período não necessariamente produz nota nova.
O piso atual e limites de M1–M7/S1–S2 estão em `skills/sms-psg-composition.md`.
Stream comprimido sem decoder qualificado reprova, não é ignorado como silêncio.
Captura privada, mix de música/SFX, restauração dos canais, audição/review e
comparação alinhada de referência continuam necessários ao eixo de áudio.
Nenhum PASS de heurística mede adequação comercial ou garante composição boa.

## 64. Registrador mal lido vira defeito audível; arranjo declarado é o do STREAM (L079)
Correção 2026-10-13: a codificação anterior desta seção estava invertida.
No latch `0xE0|fb|per`, bit2=1 é branco (4–7), bit2=0 é periódico (0–3);
bits1..0=3 usam tone ch2. Fonte primária local BlastEm `psg.c`/`sms.c` e
PSGlib foram hasheadas na evidência de curadoria. A afirmação antiga sobre
"99% periódico" não é prova válida e fica supersedida, preservada no histórico.
Arranjo declarado é o stream medido, não comentário ou número de papéis.
O achado histórico de ch1 ausente/cópia idêntica não autoriza inferir o estado
de uma versão posterior sem medir seu SHA.

Regra: claim de arranjo é claim sobre o stream medido (canais ativos, modos
de ruído, envelopes), nunca sobre o fonte do gerador ou o comentário do
manifesto. `audit_psg_quality.py` decodifica o `.psg` simples; o gerador root
usa clock/(32*Hz) para período de tone, e arrange seleciona branco sem apagar
os bits de taxa. Preview offline modela LFSR nominal: não é captura do chip,
não prova clock/counter compartilhado, analógico ou fidelidade de mix.

## 65. Andamento percebido e identidade são medidos; com referência, o arranjo é transcrição (L080)
O piso L078 deixa passar faixa que "soa acelerada": todas as camadas escrevendo
todo frame não é andamento, é metralhadora — o ouvido chama de rápido o que
nunca respira. E "tema X" portado de memória por compositor-de-código não é o
tema X: quando o acervo tem referência hasheada (MID com sha256 no manifesto de
áudio), identidade é claim verificável.

Regra: (a) M7 — a camada de maior intervalo médio entre notas precisa de gap ≥
8 frames; LOOP_MIN = 250 frames. (b) Havendo referência hasheada, o stream é
TRANSCRIDO dela por script determinístico com `--self-check` (parse SMF →
grade de semicolcheias → colapso de uníssonos → fusão de runs de acompanhamento
→ percussão com simultaneidades a 1 frame), nunca escrito "de memória" à mão.
(c) Claim de voz/anúncio ("FIGHT") é síntese por formantes em stream SFX ≤ 45
frames com decaimento (S1), tocada via `PSGSFXPlay` em canal declarado no
manifesto. (d) Economia PSG: só se escreve latch de registro que MUDA —
re-articulação em mesma nota custa mute-de-1-frame (2–3 B), não par de tone;
um arranjo que não respeita isso paga o dobro de bytes e soa igual.
`audit_psg_quality.py` mede tudo; a transcrição de 8 compassos do Ken (750 B)
coube na ROM onde o arranjo-de-memória de 7 compassos (919 B) estourava.

## 66. Gate que não conhece a sintaxe da API que audita aprova em silêncio o que não enxerga (L081)
`audit_psg_channel_binding.py` casava canal por literal único
(`SFX_CHANNEL[A-Z0-9]+`). Máscaras compostas — `SFX_CHANNEL1 | SFX_CHANNEL2 |
SFX_CHANNEL3`, forma legítima dos defines do PSGlib.h (autoridade #8: masks
são bits) — não casavam com NENHUMA regex do gate: a chamada ficava invisível,
e símbolo ausente do mapeamento é comparado com nada: [PASS] fabricado por
cegueira. Recorrência da família L069/L041.

Regra: gate que valida sintaxe de API casa a forma REAL do header, não a que o
regex autor lembra. Um único classificador cobre toda chamada do padrão; todo
2º-argumento não-literal para símbolo declarado vira "não provado" (nunca
skip); comparação de máscara é por conjunto ordenado de tokens (ordem dos
termos não é arranjo). O `--self-check` da ferramenta inclui o escape que ela
fechou (mascara+variavel no rabo reprova) — gate sem caso-cego testado é gate
que ainda não caiu.

## 67. VCounter marca o início do VBlank; o derrame é detectado depois da volta (L082)
O pior-frame lia `vline >= 0xC0` como derrame, mas `0xC0` é a entrada do
VBlank. No NTSC 192 linhas, as 70 linhas seguras do VDP aparecem no contador
como `0xC0–0xDA, 0xD5–0xFF`; após `0xFF` ele volta a zero e o display ativo
recomeça. Assim, o contrato antigo contou frames dentro do blank e ignorou
frames que terminavam em `0x00–0xBF`. A documentação do VDP lista a sequência
e o fórum de desenvolvimento confirma o teto seguro antes da volta ao ativo
(Charles MacDonald VDP notes; SMS Power HOW-TO, fontes referenciadas em
`doc/curation/2026-09-26_l082_vcounter_vblank_deadline.json`).

Regra: `probe_vovf` incrementa quando `vline < 0xC0`; `probe_vline_min` guarda
o mínimo observado. Para excluir atraso do depurador, a ROM mede uma janela
contínua, sela `vovf`/mínimo com `worst_done` e só então o gate anexa o DAP.
Saída antiga com predicado `>= 0xC0` não é evidência de derrame e deve ser
recolhida antes de fechar orçamento. Gate: `measure_worst_frame.py` e seu
`--self-check` (limite 0xC0 nos dois lados, janela curta e selo ausente).

## 68. Referência de excelência não é teto de probe nem promessa de técnica (L083)

Para engines MUGEN→SMS, usar `doc/05_technical/mugen_engine_standard.md`,
`mugen_engine_contract_v1.json` e workflow `mugen-engine-quality.md`.
Decisão humana de 2026-09-26: Sangokushi III é piso de ambição; 1:4/48 px do
luta_mugen é perfil histórico e não limite universal. Área útil e corpo opaco
idle definem a escala. Portfólio registra baseline/candidata/rejeitada como descrita,
prova e fallback; técnicas não testadas não são capacidades entregues.
Gate `audit_mugen_engine_contract.py`: planning valida contrato; delivery exige
aceites e artefatos próprios vinculados à ROM. Não substitui visual, orçamento,
input, áudio, frescor ou revisão independente e nunca declara AAA.
A CLI copiada de outro console deve executar --help e suas rotas reais antes de
ser anunciada como motor. O fork SMS remove comandos dependentes de módulos MD
ausentes. Método é doável; hardware, status e API precisam de prova local.

## 69. makesms ignora mapas bancários além de oito; agrupe páginas contíguas (L084)
O `makesms` do devkitSMS declara `MAX_MERGES=8`; depois de oito `-mbank`,
`addMerge()` retorna erro, mas o parser não verifica o retorno. A ROM pode
buildar sem os mapas restantes. No piloto 80 px, 35 entradas produziram ROM de
192 KiB e omitiram o banco 25 de Ryu, apesar do build registrar sucesso.

Regra: consolidar cada sequência contígua de páginas de 16 KiB num único arquivo
e mapear com `-mbank arquivo:0:quantidade:banco_inicial`. `audit_mugen_engine_contract.py`
reprova manifest com mais de oito entradas ou argumento incompleto. `makesms`
deve continuar recebendo no máximo oito mapas, e o build/ROM deve provar os
bancos-limite; tamanho alegado no JSON não prova presença dos dados.

## 70. Ferramentas de medição em subdiretórios também entram no self-check (L085)

`validate_measurement_tools.py` deve descobrir ferramentas de medição na raiz
e em subdiretórios do wrapper. Uma ferramenta de análise não deixa de ser gate
por viver em `mugen2sms/analysis/`.

Regra: prefixos `audit_`, `measure_`, `validate_`, `capture_`, `seal_` e
`reconcile_`, sufixos de gate e ferramentas doutrinárias registradas são
descobertos recursivamente, exceto diretórios de cache. Cada uma expõe e passa
`--self-check`; o autocheck do validador inclui uma fixture nested para provar
que a busca não parou na raiz. Gate: `validate_measurement_tools.py`.

## 71. Pivô espelhado usa a grade arredondada; máscara mede o pixel visível (L086)

Metasprites SMS espelhados são montados sobre colunas de 8 px. Uma pose com
largura não múltipla de 8 ganha padding na grade; no facing esquerdo, esse
padding aparece como uma coluna transparente antes da imagem visível. Ancorar
pela largura exata desloca o pivô, e comparar a imagem contra a origem da grade
cria um falso erro de máscara.

Regra: origem de METAL usa `ceil(width/8)*8`; a origem raster visível inclui o
padding transparente à esquerda. O renderer canônico, o diagnóstico e o
orçamento usam a mesma geometria. `scale_pilot.py --self-check` cobre largura
31/51 px; `--video` acumula o framebuffer e compara a máscara alfa do frame 0,
incluindo origem e IoU. A captura mede silhueta/pivô dessa pose, não AIR,
flicker por frame ou gameplay.

## 72. Lições podem apontar ferramenta nested pelo caminho relativo (L087)

`audit_learning_capture.py` rejeitou a lição L086 porque extraía apenas
`scale_pilot.py` e procurava na raiz, apesar de o medidor existir em
`mugen2sms/analysis/`. O inventário de ferramentas (§70/L085) já aceita essa
estrutura, mas a captura de lições não.

Regra: `tool_that_measures` pode usar caminho relativo ao wrapper; resolver e
validar esse caminho integral, sem truncar o diretório. O `--self-check` mede
uma ferramenta nested existente e deve reprovar a mesma referência quando o
arquivo falta. Gate: `audit_learning_capture.py`.

## 73. Metadados e tiles devem pertencer ao mesmo pool de paleta/facing (L088)

Um metasprite guarda índices absolutos do pool de padrões. Gerar `_TILES` e
`_P2_TILES` independentemente pode mudar a ordem ou a quantidade de padrões
deduplicados; a paleta alternativa não pode herdar `META/METAL` por suposição.
No corte legado, Ken P2 referenciava tile 114 embora seu blob tivesse 57 pares,
e o header não exportava metadata própria de Ryu P2. Os ZIPs fonte agora foram
localizados no acervo de estudo e o corte 72–88 px foi regenerado com metadata
por paleta em todas as 44/32 poses. Uma ROM clone-only provou o binding do idle
Ryu P2 frame 0 com IoU 1,0; isso ainda não prova AIR nem integração do header
integral. O probe de reconstrução confirma a razão da regra: apenas 88/2.660
pares referidos do Ken e 50/1.404 do Ryu coincidem byte-a-byte; máscara parecida
não autoriza recuperar índices.

Regra: para cada pose, facing e paleta, todo ID par da SAT precisa endereçar um
par 8×16 dentro do blob selecionado. P2 usa seus próprios `META/METAL`, ou o
gerador prova igualdade exata do layout e do mapeamento de padrões. Arrays de
metadata podem compartilhar armazenamento somente por igualdade byte a byte:
preservar um alias por símbolo e `_SIZE`, ensinar parser e auditor a resolver
aliases, e medir o objeto depois do link. No corte Ken/Ryu, 196 aliases exatos
retiraram 18.055 B: `_CODE` ficou em 16.669 B e o header integral linkou com
15.550 B livres no banco 1. O build/emulador provou inclusão das tabelas e
somente a máscara/pivô dos idles frame 0; não provou reprodução AIR. O metadata
continua no segmento fixo deste corte e elenco maior pode precisar de bancos.
O medidor deve falhar em índice fora do blob, ausência de metadata por paleta
sem prova, pool current+next acima da VRAM reservada ou stream acima do AIR. Gates:
`mugen2sms/analysis/scale_pilot.py` e `audit_symbol_size_sync.py`; os self-checks
cobrem alias válido, destino ausente/ciclo, metadata P2 e tamanho divergente.
O mesmo analisador soma pares 8×16 novos por transição e divide por AIR ticks;
Ken idle 0→1 pede 480 B/VBlank e Ryu P2 idle 0→1 pede 183 B/VBlank neste
corte. Isso é demanda derivada dos bytes, não throughput do VDP: aceitar exige
ROM e probe de pior quadro. VRAM current+next caber não significa prefetch a
tempo. Build, vídeo de todas as poses AIR, gameplay e budget de cena continuam
gates distintos. O relatório pré-arte também emite `idle_cache_plan` cíclico:
slot por padrão físico, metadata remapeada por quadro e origem bank/offset de
carga, preservando eixo, dx/dy, terminador e AIR. No corte Ken/Ryu, os slots
0–63 e 64–127 produzem 6.464 B de idle current+next. É um mapa-fonte para a
integração, não throughput nem prova de VRAM; aceite requer repetir as cargas
na ROM e provar a cadência em todas as poses.

## 74. Janela DAP do pior quadro precisa cobrir o selo em ROM lenta (L089)

Um timeout fixo de 90 s classificou como `sem_lastro` uma ROM de 2,35 FPS após
218/3.000 frames: o probe não havia selado a janela, então esse resultado não
era PASS nem FAIL de VDP. A ROM piloto de 25,2 FPS também excedia o tempo
estimado no comentário do runner; com espera de 150 s, o selo fechou 3.000
frames e mediu `vovf_delta=3000`.

Regra: separar janela medida (3.000 frames contínuos sem DAP) da espera de
pareamento. `measure_worst_frame.py --wait-seconds` aceita 90–1.800 s, mantendo
90 s como padrão e recusando encurtamento que possa ocultar o selo. Timeout ou
snapshot parcial permanece `sem_lastro`; somente `done=1` fecha veredito. O
self-check cobre limites da espera e janela incompleta. Medir o tempo real da
ROM antes de aumentar a espera; não extrapolar aprovação de budget de um probe
parcial.

## 75. Plano de slots de animação em loop precisa ser periódico (L090)

Uma passada gulosa de alocação (reusar pares iguais, novos nos slots livres)
não fecha o ciclo: na volta última→0 os pares da pose 0 podem ir para outros
slots, a ROM continua com uma META por pose e o upload 0→1 seguinte grava em
slots exibidos. O glitch só aparece a partir da 2ª volta, sempre nas mesmas
peças — screenshot do 1º ciclo não pega.

Regra: todo plano de cache de animação cíclica é verificado simulando dois
ciclos como a ROM executa (pose 0 com a META inicial): cada pose mostra os
mesmos pares em toda volta e nenhum upload toca slot exibido.
`scale_pilot.py` itera o layout até ponto fixo e cai em ping-pong par/ímpar;
sem layout periódico, erro explícito. O self-check reproduz o defeito.

## 76. Imagem renderizada se prova contra imagens legais, quadro a quadro (L091)

Simulador de scanline, contagem de SAT e vídeo "com conteúdo" não provam a
imagem. `audit_render_glitch.py` compara cada quadro do framebuffer com as
imagens legais que o projeto rasteriza dos mesmos padrões e posições da ROM.
Modo `strict` (zero flicker): quadro = imagem legal. Modo `flicker`: nenhum
pixel aceso fora da imagem casada (resíduo, sprite perdido, par trocado) e,
em cada janela de N quadros da mesma imagem, a união cobre tudo (nada omitido
para sempre). No modo flicker o casamento minimiza primeiro o "sobrando":
casar por faltando+sobrando escolhe a pose menor e fabrica falso positivo.
O julgamento começa no primeiro conteúdo sustentado; o que acende antes é
registrado (`pre_content_lit_pixels`), nunca apagado. Tolerância de borda de
1 px (h264): glitch mais estreito não é detectado. Ligar o display só depois
da 1ª SAT e dentro do VBlank.

## 77. Fundo claro não conta como cobertura de sprite (L092)

Uma máscara por luminância trata céu, piso e HUD claro como pixels do ator. A
união desses pixels permanentes pode aprovar uma janela mesmo quando peças ou
lutadores estão ausentes. `audit_render_glitch.py` deve falhar fechado quando
mais de 20% da imagem legal estiver acesa sem placa de fundo. Para palco claro
ou detalhado, passe uma placa RGB 256×192 sem atores; o gate subtrai essa mesma
placa das referências legais e do framebuffer. Exclua HUD ou outras áreas
dinâmicas com `--ignore-rect`, sem remover a região dos lutadores.

Quando solicitado por `--region`, o relatório mede cobertura/duty cycle por
retângulo, ausência máxima no quadro e sequências com cobertura abaixo de 50%,
25% ou zero. O SHA da placa, o limiar RGB, as regiões e as exclusões ficam no
veredito. `--mode flicker --window 8` continua significando que a união cobre
a pose em até oito quadros; não significa flicker zero nem substitui a leitura
da visibilidade por região. O self-check reproduz fundo azul/verde com ambos
os atores ausentes, testa uma captura válida, rejeita palco claro sem placa e
exercita HUD dinâmico e regiões nomeadas.

## 78. Premissa de hardware herdada se re-deriva do header, não do texto do doador (L093)

Ao assimilar técnica de outro workspace (ex.: `mugen2sgdk_forge`), copie o
método e re-derive cada premissa de hardware do header do alvo (autoridade #8)
antes de herdar o texto. `converters/sms_cmd.py` dizia "1 botão" e "diagonal
mecanicamente impossível"; `SMSlib.h:296-302` tem `KEY_1` e `KEY_2` e a
diagonal é a união de duas direções (só direções opostas são impossíveis). A
premissa errada bloqueou 64 de 70 comandos do Ken. `audit_hardware_constants.py`
reprova essas duas frases em doutrina e em `mugen2sms/**/*.py` (só essa regra
lê código; contagens medidas em docstrings continuam legítimas). Nota de
correção que cita a frase antiga ("corrigido", "dizia") passa.

## 79. Decisão registrada não é falha: DROPPED ≠ BLOCKED (L094)

Uma matriz de capacidade deve separar o que foi descartado por decisão
declarada (`ControlMap.dropped`, ex.: golpes médios) do que falhou
(`BLOCKED`). Sem essa separação o número mede a falta de decisão, não a
qualidade do conversor. `mugen2sms/analysis/move_checklist.py` emite OK,
DEGRADED, DROPPED e BLOCKED; o relatório imprime o mapa e os botões
inalcançáveis. É leitura estática de digitabilidade e fidelidade, não
emulador.

## 80. Temporização se prova por teste diferencial e mutação (L095)

Latência derivada de prosa erra por um tick. Defina o relógio com precisão (T
conta ticks de pressão a partir do toque, inclusive; forte no tick T−1, fraco
no 1º tick solto; pior caso T−1 nos dois tiers) e compare a implementação C
com uma referência independente em traces aleatórios
(`mugen2sms/tests/test_input_tier_c.py`). Exija que uma mutação de um tick
quebre o teste. `input_tier.c` não está ligado à ROM: sem build SDCC, sem custo
Z80 e sem medição em emulador, o resultado vale só para a semântica.

## 81. Comparar trilhas exige comprimento, chaves e cenários (L096)

Comparar duas trilhas por tick com `zip` descarta a cauda mais longa: uma
otimização que perde ticks no fim, ou que deixa de gravar um campo, parece
equivalente. `mugen2sms/analysis/trace_compare.py` reprova diferença de
comprimento, chaves divergentes, trilha vazia, cenário ausente e tick
diferente. Equivalência prova só o estado gravado; não prova render, tempo de
Z80 nem campos não gravados. Ainda não existe produtor de trilha SMS (host ou
DAP): o comparador é o juiz, não a medição.

## 82. Trilha por tick vem de gravador na ROM, não de laço de leitura do DAP (L097)

O DAP só lê com a emulação pausada e pausa em tempo de parede: um laço de
leitura não amostra tick a tick e não se reproduz. Para uma trilha
determinística, use uma ROM clone que grava o próprio estado por tick em RAM a
partir de um roteiro de entrada embutido (o pad real é ignorado) e despeje o
buffer pelo DAP só depois de `done=1` (`luta_mugen_trace_dap.py`). Os ganchos
na fonte canônica devem custar zero: prove por ROM idêntica byte a byte com e
sem eles (`--check-canonical`), nunca por leitura de código. Determinismo se
prova com duas construções independentes e despejo idêntico. A trilha grava
estado, não render, SAT, FPS nem latência de input humano.

## 83. Atraso de animação se atribui por trilha: tempo em tela × AIR, contador parado (L098)

Para saber de onde vem a lentidão de uma ação, meça por tick quanto cada quadro
ficou em tela (descontando hitstop) e compare com o `time` do AIR
(`mugen2sms/analysis/trace_vs_air.py`). Se em todo quadro atrasado o contador
`tick` ficou parado em 0 pelo menos o atraso, a causa é a espera de pose
visível (streaming), não o dado do AIR, a tabela destilada nem a entrada; se o
contador anda e há atraso, a ferramenta recusa essa explicação. É inferência
de trilha + código, não medida direta da pose visível. Não generalize de um
golpe com poses não residentes para golpes com poses em cache.

## 84. Banda de upload manda na cadência: meça pares por pose e por tick antes de otimizar a ordem (L099)

Antes de mexer em prioridade ou prefetch de streaming, meça (1) pares de 64 B
por pose e quantos são novos em relação à pose anterior, (2) pares realmente
copiados por tick e como se dividem entre os lutadores (perfil de fase +
progresso do upload: `luta_mugen_trace_dap.py --profile`) e (3) a banda
necessária para o `time` do AIR (pares ÷ ticks). Se a necessária for várias
vezes a medida, prioridade só redistribui a escassez: testou-se "ação primeiro"
(-34% no hit) e a pose ainda levou ~1,5 s. A saída é de escopo (menos pares por
pose, desacoplar hit de arte, residência seletiva), não de ordem de upload.
Experimentos de variante rodam só na cópia isolada, com trechos auditáveis por
hash e sem tocar a fonte canônica; repita a execução antes de adotar.

## 85. Cor de personagem SMS é contrato de paleta, não sugestão de prompt (L100)

Conceito destinado ao Master System deve partir da paleta mestra 6-bit e da
paleta declarada para o personagem no `doc/palettes_manifest.json`. Texto de
prompt ou aprovação visual não prova cor de hardware. Para pixel art de sprite,
se a origem vier em truecolor, converta para PNG indexado com índice 0
transparente, grid 8×8, ≤15 cores úteis e RGB canal×85; as cores usadas também
devem estar contidas na paleta de autoria do personagem. Essa paleta de autoria
não representa uma tabela CRAM por lutador: todos os sprites compartilham P1 e
precisam ser mapeados para a tabela comum antes da promoção. Para folhas de animação use
`audit_validate_resources.py --kind sheet --character <id> --project <projeto>`.
Se a paleta visual aprovada precisar de papéis diferentes, atualize a fonte
geradora do manifesto e regenere-o antes de integrar; editar apenas JSON gerado
não é reproduzível. Aprovação visual não fecha animação, escala, proveniência,
vínculo asset→ROM nem validação em emulador (L100).

## 86. Granulação em volta do sprite é defeito a limpar antes da promoção (L101)

Inspecione cada folha no tamanho de destino: ruído RGB quase preto pode virar
pixels opacos quando quantizado para uma paleta de personagem; Floyd–Steinberg
também difunde erro para pixels vizinhos. Para uma folha de sprite com esse
defeito, use:
```
prepare_sms_pixel_art.py IN.png OUT.png --size 320x240 --dither none \
  --project <projeto> --character <id> --speckle-cleanup --cell-size 80x80
```
Depois rode
`audit_validate_resources.py --kind sheet --character <id> --project <projeto>`.
A limpeza conserva componentes conectados com pelo menos 12 pixels (RGB máx.
acima de 32) e expande o contorno um pixel. Inspecione o resultado: detalhe
pequeno significativo pode precisar de edição manual. Não altere o padrão de
Floyd–Steinberg para conversões gerais de foto/conceito (L055).

## 87. Escala visível e linha dos pés são contratos por quadro (L102)

Uma folha com células do mesmo tamanho e pivô comum ainda pode variar de escala
ou saltar na linha de base. Para cada ação, declare em `geometry_contract` o
canvas, a faixa de largura/altura visível e `baseline_y_px`; rode
`audit_animation_semantics.py --manifest <json> --project <projeto>`. O gate
mede cada quadro pelo índice opaco, reprova bbox fora da faixa, baseline fora
da tolerância ou canvas divergente e mantém as verificações de hash e pivô.
Quando cada chave precisa de pose própria, marque `unique_frames_required: true`
na ação para reprovar hash repetido dentro dela. Use junto com revisão das
poses: hash diferente não prova movimento legível; o
gate também não prova identidade, orçamento de scanline, metasprite, fidelidade
em ROM ou aprovação humana (L102).

## 88. Fonte suplementar só resolve lacuna autorizada; o jogo mantém autoridade (L103)

Em personagem com versões em mais de uma mídia, registre no contrato quais
papéis pertencem ao jogo Master System — identidade, paleta e comportamento —
e quais detalhes uma fonte suplementar pode esclarecer. Material do anime só
preenche a lacuna explicitamente autorizada pelo dono, como construção do
figurino; não redefine identidade, paleta SMS, gameplay ou lore e não fornece
pixels, poses ou composição copiados. Prenda cada referência a papel, URL e
SHA-256 no lineage. `audit_reference_boundary.py` mede a presença e consistência
desses campos e limites; `audit_validate_resources.py` mede a paleta SMS do
asset. Nenhum desses gates prova fidelidade visual: a revisão humana continua
obrigatória (L103).

## 89. Pixel conectado ainda pode estar errado; AAA é alvo de trabalho, não claim (L104)

Um componente único não prova um recorte limpo: um pixel de pele pode tocar por
diagonal o cabelo e sobreviver ao filtro de componentes. Revise cada quadro no
tamanho nativo e em ampliação nearest-neighbor; declare no contrato cores por
material nas regiões críticas e rode `audit_sprite_cutout.py`. O gate reprova
componentes opacos menores que o limite e RGB fora da região declarada; não
julga o restante da fidelidade, por isso a revisão humana continua obrigatória.
Ao remover fundo quadriculado, identifique amostras conectadas ao exterior e
preserve tons iguais que pertençam à roupa; chave global por cor pode apagar
detalhes legítimos. Busque qualidade AAA em cada função do agente, mas só use
claim AAA com claim token e evidência dos gates de entrega (§17/L036); objetivo
aspiracional não é certificação (L104).

## 90. Harmonia visual do elenco é um gate de escala e proporção, não um pós-ajuste (L105)

Em jogo com vários personagens, avalie a escalação como uma imagem única antes
de promover folhas. Use as concepts/model sheets aceitas para identidade e
biotipo; compare uma pose-fonte de cada sprite na escala nativa, com baseline
comum e nearest-neighbor inteiro, sem normalizar cada figura para a mesma
altura e esconder diferenças. A altura vem do contrato visual do projeto, não
da classe de peso do gameplay. Registre por personagem as faixas-alvo de altura
e largura e relações explícitas entre personagens; rode
`audit_roster_harmony.py --manifest <perfil>` para medir bbox e relações de
altura/largura. A largura inclui cabelo, capa e equipamentos; defina faixas de
ocupação e relações específicas quando isso afetar a escala percebida, como
Dr. Social ≈ Joe Musashi em largura (L105).

O gate não detecta chibi, anatomia, leitura de silhueta, fidelidade ao conceito,
densidade de clusters ou equivalência de acabamento. A revisão humana deve
comparar cabeça/torso/pernas, volume aparente, contorno, agrupamentos de sombra,
papéis de paleta e leitura em 1× e nearest-neighbor 4× ou maior. Se qualquer eixo
destoar, ajuste o model sheet no grid de pixels e revise a prancha completa;
não corrija a discrepância só ampliando ou encolhendo a figura final. Registre
na prancha fontes, hashes, medidas e estado de revisão. Aprovação do conceito
não aprova sprite, animação, integração ou ROM (L105).

Em uma mesma prancha, declare o papel de cada referência sem misturar
autoridades: para Master of Fighters, Hayato/Kenseiden ancora acabamento e
economia de clusters; Joe Musashi ancora proporção humana esguia, massa corporal
e espessura relativa dos membros. Não copie a roupa/paleta do outro jogo nem
transfira defeitos de recorte do sprite usado como referência. Reprove silhuetas
atarracadas/chibi quando não previstas no conceito, membros engrossados e
rosto/cabeça sem leitura humana. Use Joe para a anatomia, mas exija dele também
um recorte limpo.

Valores de cor corretos não garantem pintura limpa: mantenha a paleta exata do
personagem e agrupe tons por material em blocos coerentes, sem dithering,
halos, pontilhado decorativo ou dispersão cromática que diminua a leitura da
primeira proposta de conceito. Inspecione exportação transparente no tamanho
nativo e em nearest-neighbor 4×, sobre fundos claro e escuro; rode
`audit_sprite_cutout.py` com perfil de materiais válido e o gate de recursos.
Uma aprovação de escala não aprova anatomia, recorte, agrupamento cromático ou
acabamento. Registre cada eixo como pass/fail/pending; qualquer `fail` bloqueia
a prancha até a revisão da arte-fonte (L101/L104/L105).

## 91. Integridade anatômica e encaixe de equipamento precisam de revisão própria (L106)

O fluxo genérico de revisão independente já existia, mas faltava uma lista
obrigatória por personagem para rosto, mãos, articulações, empunhadura,
equipamento e contato com o chão. Em cada conceito/model sheet e prancha inicial
de roster, congele candidato e referências por SHA-256; confira cada personagem
separadamente e depois o elenco inteiro. Use `art-review.md` e registre todos os
eixos em `audit_art_review_checklist.py`. O gate verifica cobertura, notas,
estados e hashes, não infere correção anatômica nem qualidade a partir de pixels.

Revise olhos/rosto; orientação e anatomia das duas mãos; continuidade
mão→empunhadura→guarda→lâmina/cano; articulação de punho, cotovelo, joelho e
tornozelo; tiras e pontos de fixação de escudo, bainha, arco, aljava, coldre e
armadura; perspectiva dos acessórios; alinhamento da linha de base; recorte,
contorno e partículas soltas; agrupamento de cor por material e luz coerente.
Para pixel art, veja todos os quadros no tamanho nativo e em nearest-neighbor
4×, sem antialiasing, e rode os gates de cor, recurso, recorte e animação. Uma
concept illustration não prova paleta SMS nem limpeza em grade de pixels.

Cada eixo recebe `pass`, `fail`, `pending` ou `not_applicable` com nota concreta;
`not_applicable` exige justificativa. `fail` reprova e `pending` impede promoção.
Após qualquer correção, atualize hash e repita os eixos afetados e a prancha
completa. O produtor não aprova a própria arte: no checkpoint aplicável, use
`quality_review_router.py` para revisão read-only independente e exija aprovação
explícita do dono. Conceito, frame isolado, folha, integração e ROM continuam
sendo aprovações separadas (L106).

## 92. Refinamento de pixel art precisa de micro-eixos e conferência quadro a quadro (L107)

Uma folha pode estar anatomicamente corrigida e ainda destoar por clusters
suaves, sombra sem blocos, rosto ilegível, outline quebrado, pixels órfãos ou
encaixe de equipamento. Em sprite sheets e pranchas de sprites, registre por
personagem os eixos `pixel_clusters`, `face_detail_readability`,
`outline_and_cutout`, `material_shading`, `hand_weapon_attachment`,
`equipment_geometry`, `frame_pose_integrity` e `native_size_readability`.
`audit_art_review_checklist.py` reprova manifestos desses tipos sem os oito
micro-eixos, notas e hashes atuais; tipo não reconhecido na família
`pixel_sprite_*` também reprova, para que erro de nome não desative o requisito.
`fail` reprova e `pending` bloqueia promoção. O gate mede cobertura e frescor
do registro, não a verdade visual.

Revise na escala nativa e em nearest-neighbor 4×: clusters duros e intencionais,
olhos/rosto, contorno em botas e pontas de capa/casaco, mão envolvendo cabo,
materiais metálicos com blocos de luz/sombra e coerência entre frames. Use a
paleta exata, sem blur, antialiasing, dithering decorativo, glow ou pontilhado.
Pontos específicos do elenco — textura cinza do Shinobi, pernas/roupa rosa e
escudo de Alis, cabo e barra do Dr. Social, arco/corda/olhos de Landau, capa,
escudo e pés do Golden Axe Warrior, mão/olho de Hayato e identidade da arma e
rosto de J.J. — devem virar notas explícitas do checklist daquela revisão.

Uma edição generativa de folha inteira é uma proposta nova, não prova de edição
pixel a pixel: pode mudar gesto, pose ou estado de animação mesmo quando o
prompt pede preservação. Compare cada quadro com a semântica autorada e descarte
qualquer mudança de ação, duplicação, quebra de grid, contorno/halo ou cor fora
do contrato. Meça paleta/recursos com `audit_validate_resources.py`, recorte e
cores por material com `audit_sprite_cutout.py`, poses/grade com
`audit_animation_semantics.py` e escala/relacionamento com
`audit_roster_harmony.py`; confira visualmente o que esses gates não inferem.
Só reabra promoção após revisão independente e aprovação explícita do dono
(L106/L107).

## 93. Sessão privada isola controle e evidência; descoberta de PID não autoriza encerramento
Aplicação operacional de L057/L039/L065, sem novo ID. No host com vários
agentes, os testes automatizados usam `emulator_session.py isolated` e
`workflows/emulator-isolated-session.md`. Cada sessão tem ROM SHA, display
Xvfb autenticado, configuração/SRAM/cache privados e socket Unix com
ID/token/sequência. A JVM enxerga dispositivos SMSJoypad locais ao processo;
JInput físico é desativado e `/dev/input`/`/dev/uinput` ficam ocultos.

Não procurar primeira janela por nome, disputar foco, injetar teclado do host
ou encerrar processos por pgrep/pkill. Supervisor e processo são identificados
por PID e start ticks. Falha de isolamento reprova sem fallback ao desktop.
Mudança do SHA do JAR original exige nova prova da ponte; não atualizar
silenciosamente o emulador usado pela medição.

Comandos têm três evidências distintas: recebimento pela ponte, estado aplicado
às portas do emulador e botão/consequência observado pela ROM. Somente o terceiro
paga gameplay. `emulator_input.py --session --script` executa sequências
atômicas em frames do VDP, soltando tudo ao concluir/falhar. Sleep/poll de input
não mede duração de golpe. Pause/Reset são controles do console; não importar
masks de seis botões do Mega Drive para o SMS.

`capture_evidence.py --session` captura o framebuffer da própria instância.
`capture_video.py --session --ticks` grava um framebuffer por frame do VDP:
ordem/quadros reais, sem claim de throughput ou áudio. A publicação é exclusiva
por sessão, com lock e rename atômico. `emulator_session.py isolated
check-bundle` confere ROM, ponte/fonte, configurações e imagem; captura preta ou
ROM trocada reprova. `session_bridge/acceptance.py` executa duas ROMs
diagnósticas e testa controles, duração, SRAM, mensagens inválidas, captura e
shutdown. Selftest offline de vínculo não substitui essa integração real.

`measure_runtime_probe.py --session` lê SMRT da ROM com runner original em tempo
real; reserva global serializa medições cooperativas e registra carga do host.
Janelas de FPS do fixture não provam 60fps no jogo alvo. A sessão cria um sink nulo
privado e move SÓ o fluxo do PID exato antes de `start` retornar (a política de
áudio do host reroteia fluxos no nascimento; `PULSE_SINK` é ignorado). Sem rota
a captura é recusada; `capture_audio.py --session` exige duração efetiva ≥95%
da pedida e prova apenas SINAL do PID, não música correta. Boot exige `-muted`
desde `Emulicious.main`; a ponte prima a linha com zeros, confirma o sink real
e descarta buffers de boot antes de liberar PCM. Na versão fixada deste host,
stop/start/flush da linha Java recriam o stream e perdem a rota: a ponte mantém
a linha aberta durante pausas e bloqueia amostras enquanto está em mute.
Manter a linha aberta sozinho reprovou em repetição: um keepalive de zeros
durante mute/pausa preserva o fluxo no cenário testado. Verificar a rota real
antes de run/step/sequence/video e recusar avanço se ela mudar; testes incluem
divergência deliberada entre contrato e sink real, sem mover fluxos alheios.
`session_bridge/audio_acceptance.py` mede ROM sonora em mute, ativação recusada
sem rota, identidade do stream após pausas, controles sonoro/silencioso em
paralelo e limpeza. Nunca gravar o monitor padrão para provar isolamento.
O sink só é removido após o emulador sair. Hotplug de controle físico e comparação
com a referência permanecem testes explícitos conforme o plano em `doc/`.

No startup do Xvfb, aguardar a linha completa de `-displayfd` antes de fechar
o pipe: a leitura só dos dígitos seguida de close pode matar a escrita final
do servidor e deixar a sessão sem seu socket. Falhar sem fallback ao desktop.

Builds e revisões automatizadas permanecem ocultos em sessão isolada por
padrão. Só abrir uma janela visível quando o dono pedir explicitamente para ver
a ROM; identificar caminho e SHA exatos e deixar claro se é candidata. A
visualização manual não substitui a sessão isolada, captura hash-bound nem
aprovação artística. Validar a abertura da janela ou observar o título/FPS não
promove a arte nem prova gameplay.

## 94. QA nativa por subagentes: cada resultado pertence a um pedido, ROM e sessão

Aplicação de L036/L057/L065; vale para qualquer projeto/gênero trabalhado.
Ler a fonte central atual antes de testar; materialização `.agent` antiga não
substitui esta lei e não é sobrescrita para adotá-la.

O coordenador congela ROM/SHA e casos do delta/contrato. Dispara até três
workers independentes por ferramenta nativa (`spawn_agent` quando disponível),
sem subdelegação, com outputs separados. Não chamar um JSON de subagente:
registrar ID retornado e receber feedback real. Sem ferramenta, registrar
delegação não executada. Não autoaprovar nem delegar promoção/claim/git/memória.

`session_qa.py prepare` gera pedido/prompt; `collect` inicia/encerra sessão
própria e coleta evidências, mas não julga qualidade. Revisor inspeciona PNG,
frames, ROM probe e/ou áudio conforme capacidade e caso atribuído. Cada worker
tem uma sessão exclusiva; pares de leitores que pausam o mesmo emulador não
são independentes. Fontes/arte read-only, writes somente nos outputs próprios.
Funcional em paralelo; performance em tempo real com reserva serializada.

`audit_subagent_session.py` exige identidade distinta do produtor, pedido
confiável, bytes/hashes/ROM/sessão, bundle, limpeza e cobertura exata. Resultado
válido não significa testes aprovados; `--require-passed` recusa falhas e
`not_run`. N/A somente quando o coordenador justificou no pedido. Metadata de
áudio/vídeo/probe é validada separadamente do bundle de screenshot. Gate mede
vínculos/cobertura, não verdade artística nem autenticidade de um chat: IDs
devem ser cotejados com os recibos e retornos nativos pelo coordenador.
Achado perceptivo exige conferência nos artefatos antes de virar blocker;
leitura errada do revisor é corrigida com parecer inicial e retificação
preservados, sem editar ROM/arte para satisfazer falso defeito.

Retorno nativo: Resultado / Bloqueio / Próxima ação, relatório, casos,
artefatos, ROM SHA/session ID, observação concreta e teto `assigned_checks_only`.
ACK não prova golpe, vídeo stepped não prova FPS, áudio de sinal não prova
música certa. Revisor sem percepção necessária declara `not_run`; fixture e
boot nunca viram gameplay/AAA. Novo binário/pedido invalida aprovação anterior.

`harness_orchestration.py validate-result` aceita envelope vinculado; review
consolidado usa `execution_mode: isolated_native_subagents` e `session_reports`
no `quality_review_router.py`. Detalhes e contrato no workflow
`subagent-emulator-qa.md`. Consumers antigos migram no lote de seu projeto;
esta regra central não afirma que todos os scripts já foram migrados.
Checkpoint nativo também prende projeto, produtor, ROM SHA e task_ids dos
pedidos; nunca anexar aprovação diagnóstica de outra ROM/projeto. Vídeo de
gesto é capturado durante a timeline de input, não só depois da liberação.
Input/RAM/imagem podem ter latência; incluir cauda neutra explícita para
consequência/recuperação exigidas pelo roteiro. Coleta interrompida preserva
sessão parcial encerrada e evidências com feedback `blocked` válido; falta de
bundle completo impede `passed`.

## 95. Integridade histórica usa snapshots; elegibilidade atual é outra decisão

Aplicação de L036/L057/L065 e §94. Novos pedidos QA usam
`sms_subagent_session_v2`: `session_qa.py prepare` copia ROM e contexto para
inputs próprios, registra papel único, origem e SHA, e confere alterações
durante a preparação. `origin` é proveniência; o auditor confere os snapshots,
não os arquivos ativos que continuarão evoluindo. Snapshot adulterado, alias
por symlink/hardlink ao input ativo ou papel ausente reprova.

Copiar arquivos sequencialmente e comparar hashes não cria uma transação do
filesystem inteiro. Coordenador prepara com build/contexto estáveis; revisão
dos inputs detecta mistura de épocas que hashes individuais não explicam.
Nunca relaxar hash, restaurar ROM antiga sobre a ativa ou reescrever pedido
histórico para fazer a auditoria passar. V1 continua auditável conforme seu
contrato antigo, mas `collect` exige novo V2. Derivar novo pedido, mantendo o
anterior e sua limitação intactos.

`audit_subagent_session.py --current-rom ROM` compara separadamente a
elegibilidade por SHA da ROM atual. Integridade histórica não aprova outra
build nem design que mudou: GDD/contexto atual exigem reconciliação do
coordenador, e checkpoints continuam vinculados ao projeto/ROM/tasks.

## 96. Sessão nova e baseline observada definem independência do caso

Aplicação de L035/L036/L057/L065; gate `audit_subagent_session.py`.
V2 declara `case_relation`. `independent` permite exatamente um caso aplicável
em sessão nova; prepare um pedido por caso independente. `chained` executa
uma timeline cumulativa: o endpoint de um gesto pode conter efeitos dos
gestos anteriores. Não chamar ACK de reset ou contador da ponte de prova de
reset da ROM. N/A só com booleano e justificativa do coordenador.

O coletor registra framebuffer anterior ao gesto. Quando a hipótese exige
estado interno específico, forneça `precondition` com endereço, tamanho e
`equals_hex` de probe real; ele lê e compara antes dos comandos. Divergência
preserva sessão parcial/evidências e produz feedback bloqueado, sem gesto.
O auditor não aceita caso aprovado sem a precondição vinculada e satisfeita.
Sessão nova não garante que boot chegou ao idle/tela desejada; baseline visual
e ROM precisam sustentar a expectativa. Endereços de fixture não são lei SMS.

## 97. Fronteira observada, duração e identidade temporal são provas distintas

Aplicação de L037/L056/L061/L071/L082/L091, gates
`audit_stage_attribution.py`, `capture_video.py` e `audit_import_semantics.py`.
Máscara OR e histograma de fase em interrupção localizam exposição, não ciclos
gastos nem primeiro estágio causador em cada quadro. Para atribuição agregada,
use baseline antes do trabalho e contagens monotônicas da mesma janela selada,
uma observação booleana por frame/fronteira, SHA/sessão iguais e contador final
coerente com vovf. Contagens invertidas ou sem baseline reprovam consistência.
Contadores que continuam mudando após o selo não sustentam atribuição: o gate
confere a janela declarada e os números, não a implementação do congelamento.
O coordenador revisa fonte/probe e vínculo da observação com a janela selada.
O gate aprova consistência do perfil mesmo quando budget reprova: delta maior
que zero não vira PASS de VBlank. Não inferir taxa segura universal de upload.

Duração requer timestamps coerentes e tratamento da sequência/voltas do
VCounter ou contador ROM; localizar a primeira fronteira não prova duração
exclusiva ou causa única. Perfil de outro renderer/ROM/região não é transferido.

Movimento usa toda a timeline decodificada, mantendo endpoints como métrica
separada. Voltar ao idle não é freeze. Variação de HUD/contador também muda
pixels: o gate de vídeo não identifica ação do ator. Quadros RGB idênticos
podem ser elementos AIR distintos. Para timing AIR, use índices/fronteiras
gravadas pela ROM e compare com a fonte; amostra DAP pode perder elementos
curtos. Vídeo e telemetria se complementam; nenhum substitui throughput real.
O perfil AIR de `audit_import_semantics.py` confere durações finitas entre
fronteiras, não IDs/ordem dos elementos. Para identidade/ordem, associe índices
fonte e ROM a cada fronteira; intervalos iguais podem ocultar permutação.

## 98. Importação preserva unidades; cache lógico exige validade no contato

Aplicação de L036/L037/L052/L061/L083/L088; receita MUGEN e disciplina de
dados, sem transformar um piloto em lei geral do hardware. Gates
`audit_import_semantics.py`, `mugen2sms/analysis/bg_normal_phase_probe.py`,
`audit_symbol_size_sync.py` e QA nativa do §94.

Declare domínio das coordenadas, razão de escala, pivôs/facing e caixas da
fonte antes de converter uma condição. P2BodyDist de um par em pé/frente a
frente não é distância entre eixos. O perfil limitado do auditor calcula a
comparação racional com frentes fonte e verifica casos de fronteira; outras
poses/Width/escalas exigem outro contrato e medição, não copiar 45/46 ou 72/107.

Prefetch de imagem é separado de precomputar colisão. Overlap preparado com
P2 parado só é válido enquanto posição, facing, hurtbox e estado permanecem
válidos no contato. Registre revisões e prazo, invalide/recompute se mudarem;
o gate reprova registros stale. Ele não prova que o runtime realmente mantém
essas revisões: exija casos nativos com defensor móvel, guarda/troca de estado
e facing antes de promover cache como solução dinâmica. Essa implementação
no jogo permanece pendente enquanto só houver prova estacionária.

Dados de comando/metadata compartilham armazenamento apenas por igualdade
exata no namespace compatível, preservando símbolos e SIZE. Confirme payload
emitido, alias/size e mapa pós-link. Economia observada em um mirror não
autoriza fundir streams diferentes nem anunciar capacidade para features
futuras. Reúso e comparação de payloads em
`mugen2sms/generators/versus_scene_cut.py` ampliam a disciplina do §73.

## 99. Contexto legível precede QA; diagnóstico não substitui produção

Aplicação de L036/L057/L065/L071: `session_qa.py prepare` e
`audit_subagent_session.py` exigem `readable_project_context_v1` nos novos
pedidos. Produção lê e congela memory bank, GDD, spec de cenas e TDD, todos
UTF-8 não vazios. Falta de documento aborta antes de abrir o emulador.
Diagnóstico usa `--context-mode diagnostic --diagnostic-reason ...`, registra
cada ausência real (ENOENT) e limita o claim ao teste atribuído. EIO, EACCES,
diretório, link quebrado, texto vazio ou inválido nunca viram ausência
aceitável, documento substituto nem downgrade automático. O coordenador
registra o bloqueio de leitura, preserva arquivos e avança somente em ramos
independentes seguros; recuperação de armazenamento exige outra intervenção.

`audit_doc_sync.py` lê diretamente os documentos da hierarquia: distingue
ENOENT de EIO/EACCES e texto vazio/inválido; erro continua reprovando o gate.
Não interpretar erro de acesso como autorização para criar um substituto.

Snapshots históricos íntegros continuam auditáveis quando a origem ativa
muda ou fica ilegível; isso não aprova a saúde/elegibilidade do projeto atual.
O auditor recusa snapshots symlink/hardlink; origem é proveniência, não input.
Pedidos V2 anteriores sem contrato permanecem históricos e são recusados
pela coleta atual. Prepare outro pedido; não reescreva o histórico.
O gate verifica cobertura/bytes, não qualidade ou completude semântica dos
documentos. Hashes por arquivo não constituem snapshot transacional do projeto.

## 100. Identidade AIR exige elementos vinculados a todas as fronteiras

Aplicação de L037/L056/L071/L083/L091: `audit_import_semantics.py` oferece
`air_identity_timing`; use `--require-air-identity` para claims de ordem e
identidade. `air_timing` mantém apenas prova de duração (§97). O modo completo
exige export fonte hasheado (`source_air`: `durations`, `boundary_element_ids`)
e trace ROM hasheado (`air_boundary_stamps`, `air_boundary_element_ids`).
Para N intervalos finitos, ambos os vetores de IDs têm N+1 entradas, inclusive
o destino terminal, associado à mesma fronteira. IDs são elementos da ação,
nunca identidade de pixels RGB; declare namespace e significado terminal.
Valores/tipos e ordem devem coincidir. Permutar elementos com duração igual,
omitir terminal ou usar booleano como índice reprova. Timestamps ROM de 16 bits
admitem rollover; intervalos devem estar entre 1 e 32767 frames. Loops e
elementos infinitos exigem outro contrato.

O PASS mede consistência dos registros declarados. Revisão independente da
fonte/export e da instrumentação ROM deve confirmar de onde vieram IDs e
stamps. Listar índices vistos em amostras DAP não os associa a cada fronteira;
não converter essa lista em trace completo. Fixtures offline validam o gate,
não importação rodando, throughput, combate, FPS, ausência de flicker ou AAA.
Conserve registros antigos como duração apenas até existir prova ROM nova.

## 101. Lições de QA precisam chegar às skills e ao workflow de entrega

Aplicação de L036/L038/L056/L057/L065/L071/L083/L097, sem novos IDs.
`audit_learning_capture.py` verifica instruções explícitas supersedidas nas
skills/workflows: desktop como canal padrão, encerramento global por nome,
sleep como regra de gesto, endpoints como freeze e delta RGB universal.
Self-check tem exemplos válidos/inválidos; a varredura de frases não é análise
semântica completa e não autentica uso correto da ferramenta. Menções ao
legado têm alcance histórico explícito; comandos globais de encerramento
copiáveis são removidos dos runbooks, mesmo rotulados como corrigidos.

Skills de input/evidência/luta/vídeo/áudio ensinam sessão privada, ID/SHA,
sequência em frames, baseline e consequências observadas pela ROM. Throughput
usa execução contínua; vídeo stepped não inclui prova de FPS/áudio. Workers
nativos mantêm cobertura/cleanup; ACK não aprova gameplay. Review independente
confere semântica e artefatos, além do gate de texto (§§93–100).

Receita MUGEN em `skills/sms-mugen-source-semantics.md` aplica §§68/98/100:
papel declarado/emitido difere de consumidor e execução. Extração próxima/
distante mantém ordem, predicados do perfil e grupos não compilados; estados,
ações, loop local, velset/physics e HitDef aproximados ficam explícitos.
Testes do importador e `audit_import_semantics.py` medem registros/perfis,
nunca compatibilidade CNS geral, orçamento dinâmico ou combate em ROM.
Falha de leitura bloqueia QA production; não reconstruir contexto para passar.


## 102. Arte autoral começa por catálogo e produção incremental (L108)

Quando o usuário pedir arte autoral para um projeto, consulte o catálogo
`doc/curation/2026-10-07_catalogo_inicial_estilos_visuais.json`, identifique o
estilo e os invariantes do asset e siga `workflows/original-artwork.md`. O padrão
é um concept/model sheet individual por ciclo, com o formulário aprovado e
revisão antes da próxima variação; gerar dezenas de estilos de uma vez não é o
padrão, pois o custo aumenta e a revisão perde viabilidade. O catálogo pode
crescer por entradas com ID estável, índice estável, fonte identificável/hash,
artista/estúdio de referência com papel e fonte, assinatura visual distinta,
descritores completos e estado de validação; crédito individual não confirmado
deve permanecer declarado como tal, sem suposição. Se o usuário não definiu a
direção, informe que há 49 referências atuais e que pode escolher fora do
catálogo; explicite mídia/traço, obra/era e artista/estúdio como critérios
mínimos. O model sheet deve exibir índice, referência artística e assinatura de
estilo. Faça revisão anatômica traçando ombro→braço→cotovelo→antebraço→punho→mão
e revisão de coesão/distinção da assinatura visual. Compare artistas específicos
separadamente (por exemplo, Eisuke Ogura e Toshiaki Mori/Shinkiro); não os
reduza a uma etiqueta genérica. Texto de estilo não prova fidelidade nem
validação visual. Guarde prompts, originais, composições, metadados, lineage e
validações versionados em `data/source_art/` do jogo. Concept candidato não
entra em `res/` nem prova conversão SMS, integração, ROM ou aprovação. Use
`art-review.md` e `audit_art_review_checklist.py`; o gate mede cobertura,
status e hashes desses eixos, não a verdade artística. O dono aprova promoção.
O prompt da arte-fonte não deve incluir título, rótulos, régua, baseline ou
fichas; o compositor os adiciona uma vez. Na revisão final, confira duplicatas,
alinhamento, sobreposição com silhuetas/equipamentos e texto cortado nos cartões.

## 103. Delta modular não é incidência exata de otimização

Aplicação de L013/L037/L061/L082/L089/L097, gate `audit_counter_window.py`.
Em contadores monotônicos com wrap, diferença entre extremos é módulo 2^bits.
Declare largura, limite máximo de eventos, units/owners, início/fim da janela e
ausência de reset. Use `--require-exact` antes de publicar contagem/hit rate.
Sem limite ou quando outra volta cabe nele, não há contagem única. Byte155→184
admite29 e285 numa janela de até358 eventos; zero delta também pode esconder
uma volta inteira. Limite incompatível com o delta reprova consistência.
O gate mede aritmética declarada e hashes; não prova o limite/reset/janela ou
instrumentação ROM. VCounter não é contador linear de duração CPU (§97).

Cache/preflight/dirty-bit não vira ganho sem comparar trabalho equivalente,
FPS contínuo e custo de fallback na ROM. Counter de boot não paga incidência
na fase ativa. Regressão observada bloqueia aquele candidato; motivo interno
permanece hipótese enquanto faltam amostras/instrumentação. Os trials Ryo/Terry
de2026-10-08 estão rejeitados; não generalizar que cache é ruim no SMS nem que
slots fixos estão aprovados. `skills/sms-runtime-optimization.md` conserva
baseline, incidência, invalidadores, comportamento/render e próxima rota medida.

## 104. Revisão de concept cobre a composição final

Aplicação de L106/L108 e §102: `audit_art_review_checklist.py` exige
`document_and_layout` em `character_concept_model_sheet`, junto de atribuição,
assinatura, cadeia anatômica e coesão. Arte-fonte correta não aprova cartão
composto: revisar título/índice/ficha, clipping, sobreposição, régua/baseline e
alinhamento após composição. Workflow `art-review.md` e skill visual ensinam
essa etapa; metadata copiada de canvas diferente não prova encaixe.
O gate confere cobertura/status/hash, nunca geometria artística ou verdade do
parecer. Reports históricos permanecem arquivados; revisão atual com eixo
ausente precisa novo checklist/parecer, sem reescrever PASS antigo. Aprovação
do dono e conversão/integracão/ROM permanecem gates separados.
O eixo de layout da model sheet não aceita `not_applicable`: mesmo sem ficha,
vistas e recortes têm composição que precisa de parecer concreto.

## 105. Prova de asset separa pixels-fonte, mapa de tiles e animação (L109)

Após concept aprovado, a prova de conversão contém uma pose idle e uma pose de
ação, separadas; não é folha de animação e não fixa quantidade de frames.
Nenhuma grade, régua, baseline, label ou caixa pode cruzar o preview do sprite.
Mapa 8×8 fica em painel próprio. `audit_asset_proof_sheet.py` reconstrói cada
preview desde a fonte indexed e compara pixels exatos; diferença, reamostragem,
alpha antialias ou overlay reprova. Também confere duas poses distintas,
índice transparente, alpha binário, paleta de até 15 cores úteis na grade SMS,
contagem 8×8 e cobertura declarada dos 12 princípios. O gate mede reprodução e
estrutura; não julga anatomia, appeal, fidelidade de concept ou qualidade AAA.
`audit_sprite_cutout.py` também precisa fechar pixels órfãos e regiões de cor por
material. Um perfil `components_only` pode detectar ilhas, mas fica pending e
bloqueia promoção até as regiões materiais e o review visual estarem completos.

Toda animação precisa de análise com critério/evidência para os 12 princípios:
squash/stretch, anticipation, staging, straight ahead/pose to pose, follow
through/overlap, slow in/out, arcs, secondary action, timing, exaggeration,
solid drawing e appeal. Dois stills não validam movimento ou timing e não
substituem a folha animada. A folha completa espera orçamento coerente no GDD,
TDD e spec de cena.

Master System tem VRAM 16 KB (512 padrões 8×8 de 32 B), janela de 256 padrões
por seleção da base de sprite, SAT de 64 objetos, teto de 8 sprites por linha,
objetos de 8 px de largura por 8/16 px de altura, duas subpaletas de 16
(BG índice 0 visível; sprite índice 0 transparente), RAM 8 KB, ROM linear
48 KB e sem DMA. O hardware não
estabelece máximo universal de quadros por folha: `max_frames_per_sprite_sheet`
fica indefinido até medir compartilhamento, pools VRAM/RAM, ROM/banking,
residência e upload por VBlank no TDD/scene budget. Inventário de padrões não
prova SAT/scanline, nem residência. Review independente e aprovação humana
continuam gates distintos.

## 106. Prova de pose exige arma inteira e escala de tela fundamentada (L110)

Aplicação de L101/L102/L104/L105/L109. Não considere um proof sheet válido só
porque seu preview reproduz um recorte: conteúdo opaco encostado na borda pode
ser arma/equipamento truncado. O canvas de prova tem dimensões múltiplas de 8
e ao menos 1 px transparente nos quatro lados; a exceção exige decisão de
contrato explícita e não se aplica a poses apresentadas como completas.

Se a resolução do personagem for convertida, declarar origem, dimensão de
entrada, saída e razão uniforme nearest-neighbor. `audit_asset_proof_sheet.py`
reconstitui o frame convertido a partir da folha indexada, verifica tile
alignment, mede clearance do bbox opaco e compara o preview 1×/ampliado com o
PNG convertido. Transform diferente, canvas que não é múltiplo de 8, borda
opaca ou diferença de pixels falha. A arte-fonte externa ou o concept ainda
precisam de revisão humana para confirmar que arma, cabo, ponta e acessórios
estão completos e ligados corretamente; clearance não prova semântica visual.

Escala vem do GDD/TDD e é medida de composição, não limite de hardware. Para
Master of Fighters, Fatal Fury Special Game Gear fornece régua visual em
viewport 160×144; projetar aproximadamente 53 px em pé para SMS 256×192 dá
71 px. O alvo atual 66–72 px tem centro 70 e pode variar por papel, pose ou
profundidade com justificativa. Não confundir altura corporal com extensão de
arma/capa, nem canvas com tamanho visível. A referência é estimativa visual,
não frame-data extraído. Nenhum desses checks prova anatomia, identidade da
arma, aprovação humana, orçamento VRAM/SAT/VBlank, ROM ou qualidade AAA.

## 107. Terminais de equipamento e paleta compartilhada exigem dupla verificação (L111)

Uma silhueta de arma pode estar totalmente dentro do canvas, sem pixels soltos,
e ainda assim estar semanticamente errada: uma ponta ou terminal achatado pode
ser lido como martelo, pomo ou outra peça. Na revisão, compare a forma esperada
com o concept/referência, em pixel nativo e nearest-neighbor ampliado; registre
um eixo explícito `equipment_terminal_shape` no contrato. Se a forma falhar,
selecione/repare uma fonte adequada e repita a inspeção visual integral depois
da alteração. `audit_asset_proof_sheet.py` pode exigir eixo, identidade
esperada, evidência e hash, mas não pode decidir sozinho que a imagem parece
uma bengala. Pixels limpos não substituem revisão semântica.

Altura da pose não é altura anatômica quando o bbox inclui bengala, arma, capa
ou cabelo solto. Compare a faixa do GDD à medida coroa–sola do corpo sem
equipamento e registre o eixo separadamente; postura de ação pode mudar o bbox
vertical e não substitui a pose em pé. Contratos de proof sheet usam o eixo
`standing_body_height_vs_gdd` para impedir que altura total com equipamento seja
declarada como altura anatômica aprovada.

Não confunda a paleta indexada de cada personagem com alocação de runtime. SMS
tem P0 e P1, ambas com 16 entradas; sprites compartilham P1, cujo índice 0 é
transparente, e P0 índice 0 é visível no BG. HUD e cenário dividem P0 conforme
papéis do jogo; tiles BG podem selecionar P1 para reutilizar cores. O GDD/TDD
e o contrato machine-readable devem dizer quais slots são fixos, como as
paletas individuais mapeiam para o conjunto comum e o que permanece pendente.
Nunca promover o roster com a suposição de uma CRAM independente por lutador.
Em Master of Fighters, 14 perfis de autoria somam 43 RGBs; o mapeamento para
uma única P1 de até 15 cores úteis está pendente. O proof v4 escolhe o frame
06-fonte para preservar a ponta arredondada da bengala; sua avaliação humana
ainda bloqueia promoção.


## 108. Emuladores complementares: identidade, relógios e representações SMS (L112)

Emulicious privado permanece a rota principal de produção e dos sete eixos de
QA. BlastEm SMS entra para uma hipótese concreta Z80/VDP/mapper e comparação
independente da mesma SHA e precondição; não é gate obrigatório por build nem
substituto automático. A aceitação MD do SGDK não qualifica SMS.

- `blastem_sms.py` fixa arquivo/binário oficial 1.0.0, força máquina SMS e modelo
  sms1/sms2, conserva `.sms`, gera config/SRAM/Xvfb/PTY/sandbox privados e fecha
  somente processos próprios. Sem foco, teclado host ou joystick físico. Input
  lógico SMS1/2 usa bindings B/C; A/B era port incorreto de nomes MD.
- Baseline/dumps completos precedem input. Predicados são contados; ausência
  declara diagnóstico genérico, não aplicabilidade de caso. Fonte da ferramenta
  é congelada por sessão; módulo importado anterior à edição não pode registrar
  o hash da fonte nova como código executado. Revisão exige ROM/tool atuais
  quando o claim for sobre a versão atual, sem apagar a integridade histórica.
- Frames VDP, SDL presentations, contador da ROM e atualização de estado não
  são iguais. Snapshot pode interromper a iteração; consumo/ação vêm do probe
  ou gravador da ROM. Compare estado lógico equivalente; cauda neutra documenta
  conclusão da iteração, não autoriza alterar comando para ocultar defeito.
- CRAM interna em words e contador de ciclos rebaseado são representações do
  emulador. Não ler CRAM interna como SMS6bit, ciclos internos como duração CPU
  ou texto genérico do debugger VDP como suporte SMS a DMA/planos MD.
- Screenshot GL por software foi calibrado 256×192; SDL perdeu linhas no host
  e fallback é rejeitado. Imagem é um frame após último snapshot com input
  solto: não prova estado transitório anterior. Imagem uniforme é registrada
  sem claim de boot visual. Áudio nasce dummy; não paga música/FPS.
- Backend limitado a NTSC Mode4 192 linhas. PAL, áudio e FPS BlastEm não estão
  qualificados como eixos de entrega; §110 acrescenta capturas APNG/WAVE/VGM
  diagnósticas, sem promover esses eixos. Consistência/concordância não prova compatibilidade universal
  ou hardware real. `session_qa.py` continua qualificado para Emulicious;
  review BlastEm usa worker nativo real e auditor de bundle próprio.

Gate: `audit_blastem_sms.py` verifica SHA/arquivos, dimensões e tamanhos, fonte,
limites de perfil/claim, snapshots/log e baseline/cleanup registrados.
`--current-rom` e `--require-current-tool` impedem reutilizar histórico para a
versão atual. O auditor mede consistência; não autentica semântica, isolamento
contra agente malicioso, eficiência, som, arte ou verdade física.
Workflow: `blastem-sms-diagnostics.md`; skill: `sms-emulator-diagnostics.md`.

## 109. Contrato de animação separa desenho, estado e custo VDP (L113)

Antes de produzir uma sprite sheet, cada ação/estado registra trigger,
loop/transição, pose inicial/final, IDs e contagem de poses-fonte, duração por
pose, e track próprio do personagem e de todo objeto/efeito animado. Objetos
com lifetime próprio (projétil/efeito) declaram evento de entrada/saída e
timeline/duração independente, mesmo que a animação do ator já termine. Avaliar
os
12 princípios Disney por sequência; pelo menos sete precisam de aplicação
contextual planejada ligada a IDs de quadro. Cada princípio restante recebe
razão explícita. Pista planejada não é evidência visual: após desenhar os PNGs,
revisão temporal comprova o efeito real.

`source_pose_count` não é número de objetos de hardware. Cada entidade declara
separadamente objetos SMS 8×8/8×16 por quadro; tiles únicos/compartilhados,
residência VRAM, RAM/ROM/banking, SAT/scanline e pior VBlank exigem medição. O
Master System não fixa teto universal de quadros por folha. Contagens não
medidas ficam pending/null, e aprovação do contrato não valida pixels,
anatomia, física, balanceamento, integração ou ROM.

Para locomoção/golpes, declarar apoio, trajetória, velocidade/aceleração,
startup/active/recovery, hitbox, hitstop, consequência e contrajogo conforme o
GDD. Alcance de hitbox segue a arma e o corpo visíveis; objetos não teleportam
nem atravessam mão/corpo/cenário. Runtime Z80 usa inteiros/Q8.8, sem float.
Números de balanceamento são hipóteses até medir a ROM e testar hit/block/whiff.

`audit_animation_contract.py` verifica cobertura, endpoints, tracks, poses,
revisão dos 12 princípios e mínimo de sete aplicados; `--self-check` testa o
gate. Ele não lê pixels nem autentica física/arte. `audit_animation_semantics.py`
permanece necessário depois que houver PNGs reais. Para o primeiro exercício,
`doc/dr_social_animation_contract_v1.json` registra 20 estados comuns e quatro
golpes autorais candidatos, todos ainda pendentes; pesquisa do jogo original e
propostas de luta têm campos/fonte separados. O guide pesquisado tem divergência
de nomes de armas primárias, portanto manual/ROM devem confirmar esses detalhes
antes de convertê-los em cânone.

## 110. BlastEm avançado: qualificar recurso por CPU, captura e versão (L114–L120)

Aplicar `sms-emulator-diagnostics.md` e a matriz de decisão de
`blastem-sms-diagnostics.md` para escolher o recurso pelo sintoma. Emulicious
permanece a rota de produção, FPS real, PAL, áudio final e QA `session_qa.py`.
BlastEm é complementar, sem transformar uma aquisição diagnóstica em entrega.

1. **L114 — Manutenção sem promoção implícita.** `blastem_maintenance.py`
   consulta a página oficial, registra fonte/hash/data e instala candidato em
   paralelo a partir de manifesto com versão/URL/SHA do arquivo e executável.
   Confere também arquivos e links internos. Divergência bloqueia; descoberta
   não altera o pin qualificado, e hash declarado não equivale a assinatura.
2. **L115 — GDB exige domínio de CPU/protocolo.** No source 1.0.0, Z2/z2
   implementam watchpoint de escrita M68K apesar do README; Z3/Z4 não estão
   implementados. Nem esse stub nem `vdpregbreak` Genesis são suporte Z80.
   O wrapper SMS não aceita comandos GDB/MD brutos; matriz/source inspection
   delimitam a capacidade. O teste GDB MD informado pelo usuário não é teste SMS.
3. **L116 — Watchpoint nativo não é rastreamento completo de bus.** Z80
   WRITE_8 pode ignorar valor inalterado. Endereço/tamanho RAM são limitados;
   listas nativas contam/logam/continuam e o auditor coteja contagens. O valor
   no trap e `observed_pc` (stale em casos observados) não identificam sozinhos
   o writer nem o commit. Exigir o caminho real e estado/probe posterior.
4. **L117 — VDP por OUT precisa de opcode e contexto vivos.** Breakpoint CPU
   é distinto de watchpoint VDP. Sites cabem em 0000–03FE, com bytes na ROM
   congelada e conferência viva em cada hit; mudança reprova a sessão. No mapper
   Sega 0400–3FFF é bankável. OUT(C),r exige BE/BF e registrador correto; não
   cobre aliases/OUTI/OTIR/outros sites/bancos. Mesmo opcode em outro mapeamento
   não prova identidade de rotina. VCounter/hslot/address/CD são campos internos
   tipados, sem prova de sincronia com bus ou cumprimento de VBlank.
5. **L118 — Corrigir um derivado, preservar o bruto.** APNG 1.0.0 observado
   atualiza a contagem acTL sem seu CRC. `blastem_diagnostics.py` preserva o
   original e corrige somente o checksum que corresponde ao payload antigo
   de zero frames; valida todos os chunks, CRCs, terminador e contagens. Outra
   corrupção reprova. Auditor compara a derivação e cobertura VDP ativa.
6. **L119 — Mix e log têm relógios/limites próprios.** WAVE nativo precisa de
   RIFF/data/bytes PCM efetivos coerentes, formato, duração e pico; VGM precisa
   de header/offset/EOF, comandos PSG e soma de waits válidos. WAVE assíncrono
   não é sample-accurate com o APNG; VGM pode omitir silêncio final. Cadência
   APNG nominal e sinal de áudio não provam FPS real nem fidelidade musical.
7. **L120 — Visor derivado não é framebuffer.** Getter VRAM já retorna os
   endereços SMS lógicos; CRAM interna usa encoding do pin, invertido com
   teste dos 64 códigos. Visores de paleta/tiles/name table têm vínculo aos
   dumps, papéis e dimensões próprios; name table não aplica scroll/sprites/
   raster. RGB digital não modela DAC. Não promover esses PNGs a arte final,
   screenshot do jogo ou comparação física de cor. Janelas nativas Mode4
   existem na fonte, mas sua captura automatizada ainda não foi qualificada.
   `blastem_dump_diff.py` compara duas fronteiras auditadas e labels da mesma
   ROM; delta líquido não mede escrituras/restaurações intermediárias, tempo
   ou causalidade. Blocos VRAM de32bytes incluem dados não gráficos, não são
   tiles únicos nem volume transferido. Diff fica fora da sessão imutável.

Gates: `blastem_sms.py`, `blastem_diagnostics.py`, `blastem_maintenance.py`,
`blastem_dump_diff.py` e
`audit_blastem_sms.py`, com `--self-check`/selftest e casos nativos independentes.
O auditor mede consistência de registros e formatos; não autentica origem de
chat, isolamento contra atacante, semântica da ROM, precisão temporal ou arte.
Atualização do helper também invalida elegibilidade da ferramenta atual;
histórico permanece íntegro. Nenhum reviewer é simulado em JSON.

## 111. Conversão de asset termina em framebuffer comparado à fonte (L121)

Concept/model sheet aprovado define identidade, mas cada PNG convertido é um
estágio próprio. Preserve os índices, a paleta e a transparência ao normalizar
um PNG indexado de 4 bits para o contrato de recurso 8-bit; não redimensione
nem reamostre para corrigir apenas o formato. Use `audit_validate_resources.py`
com `--kind sheet` para uma folha alinhada em múltiplos de 8, e declare
explicitamente o personagem. O build roteia 8×8, 8×16 e 16×16 como sprites
físicos e canvas de pose maior, como 80×80, como folha; `build_inner.py
--self-check` cobre sprites, folha válida e dimensão fora do grid.

`pack_sms_metasprite.py` recebe PNGs indexados 8-bit que já passaram por esses
gates. Exige índice 0 transparente, cores SMS 6-bit, paleta idêntica entre
poses, dimensões múltiplas de 8 e offsets representáveis. Empacota os padrões
8×8 em quatro planos/32 bytes, deduplica padrões e emite mapas/metasprites
terminados por `METASPRITE_END`. Declara tile base e reserva de tile vazio;
confere 256 índices lógicos, 64 objetos SAT, até 8 por scanline e terminador Y.
A capacidade segura de padrões residentes depende também do layout físico da
VRAM e da posição da name table (§112). `--self-check` cobre deduplicação,
tile vazio, divergência de paleta e excesso por scanline. Esta ferramenta não
escolhe nem reindexa a P1 comum do jogo: cada asset deve mapear sua paleta de
autoria para a tabela compartilhada de runtime.

Antes de ligar o display, inicialize todas as entradas visíveis da name table
com o mapa de fundo válido daquela cena. Em uma prova com fundo uniforme,
reserve um padrão vazio para tile 0 e limpe a name table 32×24 enquanto o
display está desligado. Pixels transparentes do sprite revelam o BG; tile 0 do
BG é cor visível, não alpha. VRAM de reset nunca é conteúdo visual definido.

Depois de gerar metasprites, rode `audit_sprite_mode.py`,
`audit_sprite_line_sim.py` com a geometria real e `audit_provenance.py`; compile
com `build_inner.py`, gere `doc/rom_asset_binding.json` com SHA de fonte,
recurso, símbolo/header e ROM, e exija `audit_rom_asset_binding.py --require`.
O modo `audit_render_fidelity.py --exact-indexed --at X,Y` compara cada pixel
opaco do PNG indexado com o RGB da captura 1:1. Para uma prova de fundo
uniforme, `--transparent-rgb RRGGBB` também confere pixels de índice 0 e
detecta sujeira sob transparência. Use a comparação estrutural padrão para
cenas com BG variável; ela não prova cor pixel-exata.

Capture pelo Emulicious privado com ROM e sessão identificadas. Para poses
distintas, aplique input por sequência de frames e observe a pose resultante;
ACK de input não prova transição visível. O publicador de captura por sessão
aceita uma imagem selada, então use uma sessão isolada por captura de pose e
feche cada sessão; para movimento contínuo, use captura de framebuffer por
frame. Binding e captura devem apontar para o mesmo SHA. Uma captura exata de
duas poses prova somente esses pixels/cores no framebuffer daquela ROM: não
prova animação, gameplay, FPS estável, áudio, PAL, hardware físico, P1 global,
coexistência do roster ou budget VBlank.

Na prova Dr. Social v3, 89 padrões de personagem + 1 padrão vazio ocuparam
2.880 B de tile 4bpp; idle usou 43 objetos/pico 6 por scanline e ação 49/pico
7. A ROM diagnóstica de 16 KiB passou pela comparação indexada exata nas duas
poses (0 divergências opacas e 0 no fundo transparente) e binding por SHA.
Ela fica fora de `res/`; a P1 do roster, revisão humana de pixels e orçamento
de runtime continuam pendentes. Evidência: `SMS_projects/master_of_fighters/
data/source_art/asset_conversion_proofs/dr_social/
dr_social_sms_conversion_verification_v3.json`.

## 112. Fonte aprovada e janela física de patterns são contratos distintos (L122)

Antes de converter uma sequência, selecione a origem pelo papel e SHA: concept
sheet define identidade; prova técnica idle+ação valida o procedimento de
conversão; a fonte de animação aprovada pelo dono fornece os quadros de
produção. Não substitua uma folha aprovada de sequência pela prova de duas
poses. Prenda IDs e contagem da origem ao contrato de animação. Aprovação da
imagem-fonte não aprova automaticamente quantização, timing ou integração.

O limite de 256 descrito pelo registrador/base do sprite é uma janela de
índices lógicos, não um orçamento residente independente do cenário. Calcule
antes do pack: `min(256 - tile_base,
(name_table_base - (sprite_pattern_base + tile_base*32)) // 32)`. Use a base de
sprite selecionada e o endereço real da name table da cena. Com base de sprite
0x2000, name table em 0x3800 e tile base 257, cabem 191 padrões de 32 bytes;
escrever o padrão seguinte invade a PNT. Pool compartilhado acima do limite
reprova ou precisa ser dividido em carregamento por pose/streaming com orçamento
explícito. Nunca conte o tilemap ou SAT como espaço de arte. O `--self-check`
de `pack_sms_metasprite.py` prova o limite 191/192; a ferramenta calcula a
capacidade quando recebe `--sprite-pattern-base` e `--name-table-base`.

L122 nasceu no viewer Dr. Social: a fonte aprovada contém 61 poses em nove
sequências; a prova técnica anterior tinha somente duas. Um pool compartilhado
de 200/246 padrões foi tratado como se coubesse no índice lógico e corrompeu
rótulos da name table. Com o limite físico declarado, idle (169) e defesa (182)
permanecem compartilhados; sete sequências excedentes carregam uma pose por
vez. A regra mede a consistência do inventário/layout, não pixels, timing,
throughput VBlank, gameplay, FPS, áudio, paleta P1 do roster ou qualidade AAA.

## 113. Estados de arte até ROM são promoções independentes (L123)

Use `workflows/artwork-to-rom-lifecycle.md` para criar ou modificar arte
autoral. O intake define escopo, plataforma e direção visual; referências
registram papel/hash e não substituem identidade do jogo. Model sheet e revisão
independente/hash-bound precedem aceite explícito do dono. Se houver elenco,
comparar frontalmente com baseline comum, máximo de cinco por prancha e escala
declarada no GDD; métricas de bbox não aprovam morfologia ou estilo.

Antes da folha animada, contrato por ação declara estados inicial/final, IDs,
quantidade/duração de poses, trilhas separadas de personagem/objetos e os 12
princípios com ao menos sete aplicações contextuais (L113). A prova técnica de
duas poses valida conversão, não é a fonte de animação. A fonte completa deve
ser aprovada para seu papel e ligada por caminho/SHA ao contrato (L122).
Concept aprovado, fonte aprovada, pixels convertidos, ROM diagnóstica e ROM de
produção são decisões distintas.

Para SMS, medir recursos, procedência, recorte, geometria, SAT/scanline e
patterns residentes pelo layout real até a name table. P1 de sprites é
compartilhada; P0/uso de BG, RAM/ROM, banking e pior VBlank são decisões por
cena que precisam de medição. Uma ROM diagnóstica com binding SHA e framebuffer
comparado à fonte prova apenas o render daquela ROM; não prova estilo, timing,
gameplay, FPS, áudio ou entrega. Revisão independente/humana da conversão,
paleta e budgets precede promoção a `res/`; entrega exige evidência fresca do
binário atual.

Estados mínimos: documentado, candidato, fonte aprovada, recurso aprovado,
ROM diagnóstica comparada, review humano aprovado, produção integrada,
testado em emulador, budget validado e delivery. Não transportar PASS entre
eixos, versões ou hashes. Os gates existentes medem transições específicas:
`audit_art_review_checklist.py`, `audit_roster_harmony.py`,
`audit_animation_contract.py`, `audit_animation_semantics.py`,
`audit_asset_proof_sheet.py`, `audit_validate_resources.py`,
`audit_reference_boundary.py`, `audit_provenance.py`,
`audit_sprite_cutout.py`, `audit_sprite_mode.py`, `audit_sprite_line_sim.py`,
`pack_sms_metasprite.py --self-check`, `audit_rom_asset_binding.py`,
`audit_render_fidelity.py`, `audit_visual_delivery.py` e `audit_claims.py`.
Cobertura de gate não substitui parecer artístico independente nem aprovação
do dono.

## 114. Revisar fluxo espacial de sombra por material, além da paleta (L124)

Pertencer à paleta do personagem prova somente que os valores RGB são
permitidos; não prova que roupa, pele ou metal tenham volume e luz coerentes.
Para todo pixel sprite, declare e revise sombra/base/luz por material, direção
da luz e continuidade espacial dos clusters em cada pose. Em tecido, a sombra
deve acompanhar a mesma face e as dobras; manchas azuis claras isoladas dentro
de uma região sombreada reprovam `material_shadow_flow_coherence` até serem
visualmente justificadas. Sombras, bases e luzes devem formar blocos contíguos
com bordas nítidas, sem dithering decorativo ou confete de cor.

Declare o papel semântico de branco, amarelo e demais acentos. Eles ficam
restritos às regiões autorizadas do design (por exemplo, olho, luva, gola,
insígnia, pomo ou peça metálica); vazamento para roupa, cabelo e contorno é
reprovação. Verifique `semantic_palette_role_confinement` junto com o eixo de
fluxo de sombra no checklist `audit_art_review_checklist.py`. Esses eixos medem
presença/cobertura, não verdade visual: automação não substitui inspeção
artística independente nem aprovação do dono.

Um detector que só procura acentos totalmente cercados pelo material não prova
ausência de vazamento: ele perde pixels que tocam a borda de outra região. Use
máscaras e âncoras semânticas estáveis quando possível; por exemplo, cabelo/face
para localizar óculos e a junção entre luva e haste para localizar o pomo da
bengala. Remapeie pontos fora dos papéis autorizados com cores vizinhas já
existentes, preservando a silhueta; depois faça dupla inspeção de cada pose em
1× e nearest-neighbor 4×. Confirme visualmente cada acento mantido, alterado ou
removido, pois uma máscara também pode classificar pixels de modo errado.

Na redução de arte colorizada, quando houver máscara explícita de material, a
conversão pode medir a cobertura do footprint dentro daquela região e escolher
entre os tons existentes pela luminância. Preserve contorno/silhueta por
nearest-neighbor; não amostre através de alpha, contorno ou outro material; não
crie cores, blur ou dithering. Verifique o framebuffer da ROM separadamente:
fidelidade exata prova que os pixels candidatos foram exibidos, não que luz,
anatomia ou papel semântico estejam artisticamente corretos.

No caso Dr. Social (L124), v7 foi rejeitada pelo dono. V8 reagrupou 927 pixels
em 61 poses (438 ilhas de tecido e 489 marcas navy internas), mas sua regra de
contenção não identificou acentos amarelos na borda. V9 reclassificou 249 pixels
amarelos, mas a dupla inspeção encontrou depois 70 brancos isolados/pares fora
de luvas e bengala. A candidata v10 removeu esses 70 pontos usando cores
vizinhas, preservou clusters maiores para análise humana e passou build/render
exato 61/61. Todos os eixos artísticos, a revisão independente e a aprovação
do dono continuam pendentes.

No mesmo ciclo, v6 reclassificou 6.145 pixels por média de área dentro da
máscara do tecido; v7 reordenou a rampa por luminância e mudou 15.690 pixels,
mas a ROM só foi comparada exatamente em três poses. Esse delta não bastou para
aprovar o visual nem para declarar cobertura completa. V8 foi o primeiro ciclo
com comparação exata dos 61 quadros. Em futuras correções, congele a fonte
aprovada e seu SHA, trate uma classe de defeito por versão, mantenha cada
transformação isolada e mensure o delta por pose. Uma mudança posterior invalida
preview, ROM e captura anteriores: reconstrua em diretório versionado novo e
repita a comparação exata de todos os quadros antes da revisão humana. Os limites
geométricos usados para encontrar a bengala em v10 são heurísticas específicas
daquela arte, não presets universais.

## 115. Registro único de artefatos e aplicação das lições (L125)

Harness de produção visual usa `workflows/artifact-organization.md` e
`artifact_registry.py`: um registro por projeto, local ou apontado pelo catálogo
central, com IDs por asset/papel/variante, uma candidata e uma aprovada distintas.
Paths são relativos ao projeto; raízes de projeto/pedido são explícitas. A
ferramenta bloqueia prefixo do workspace repetido dentro do projeto, destinos
concorrentes, aliases de symlink/hardlink, ownership duplicado, SHA stale,
ciclos e revisão sem vínculo de continuidade. Fonte animada, concept, model
sheet, planilha de planejamento, prova, conversão e ROM têm papéis separados.

O coordenador reserva arquivos antes da escrita e sela hashes após cada
tentativa. `harness_orchestration.py` recusa arquivos visuais/planilhas explícitos
sem reserva, mesmo quando o task foi classificado como review/inventário.
QA nativa mantém pedido, diretório privado e manifests próprios; não transformar
esse destino em uma raiz alternativa de produção. Preflight não é sandbox nem
lock de filesystem. Tipos novos registram finalidade, necessidade, procedimento
e destino no mesmo índice. Experimentos criativos são versões/variantes explícitas;
histórico fica preservado, sem duplicar autoridade ou escolher por maior vNN.

Adoção pode selar `legacy_inventory` sem classificação/aprovação. `--scan`
cobre áreas managed; áreas legacy são declaradamente parciais. PASS do registro
mede consistência de organização e declarações, não validade artística, conteúdo
futuro de diretórios, autenticidade humana, contexto/GDD ou entrega. Aprovação
nova precisa de decisão real ligada ao papel/ID/paths/SHA. O adaptador existente
de fonte animada conserva personagem/hash/escopo literal, sem aprovar conversão.

Toda lição emitida possui rota atual em `doc/agent_learning/lesson_routes.json`:
curadoria única e skill/workflow concreto por SHA. Refutações apontam para o
procedimento corrigido, mantendo seus limites históricos. `audit_learning_capture.py`
reprova rota ausente, duplicada, stale ou alias da lei como se fosse skill.
O mapa mede cobertura/frescor, não compreensão; revisão independente testa a
decisão do agente. Não criar outro ID para uma lição já aplicada.

## 116. Preflight do raster salvo antes da conversão de sprite sheet (L126)

Prompt, preview e extensão PNG não garantem grid, slots, IDs, alpha ou keycolor.
Antes de converter uma folha preparada para exportação, confronte o arquivo
salvo com contrato hash-bound usando `audit_source_raster.py`. Declare dimensão,
slots/retângulos/IDs/contagem e grade quando aplicável. Alpha binário aceita
somente 0/255 e exige transparência; opaque_key exige imagem opaca e presença
da chave RGB declarada. Limite cromático da fonte é opcional e explícito;
não impor automaticamente 15 cores ou paleta SMS ao concept/arte bruta.

Uma folha livre pode permanecer como referência preservada, mas não herda o
status de fonte pronta para conversão. Conserto é outra revisão, com delta,
review e novo hash. O gate não verifica quantas poses diferentes foram desenhadas,
halo, uniformidade do fundo, anatomia, identidade, luz ou recorte semântico.
Presença de preto não prova fundo limpo. Gates de pixels SMS, revisão artística
e framebuffer continuam separados (L102/L109–L124).

No exercício de jab, v4 tinha 83.402 RGB e passou apenas o contrato mínimo de
chave presente; isso não removeu os blockers visuais. V5 tinha 600.866 pixels
com alpha parcial e nenhum totalmente opaco, reprovando o contrato de alpha.
Os arquivos foram medidos sem alteração; nenhuma candidata foi promovida.

## 117. Revisão disciplinada e promoção de concept/model sheet (L127)

Antes de revisar uma matriz, congele o SHA da identidade aprovada e registre
cada apontamento como defeito, delta visual e evidência de fechamento. Liste
os invariantes que não podem regredir: rosto, idade, biotipo, escala, paleta,
estilo, roupa, equipamento e vistas preservadas. Gere nova revisão sem
sobrescrever a fonte; após a correção, faça uma segunda passagem completa pelos
encaixes anatômicos, mãos/pegadas, terminais de objetos, silhueta, composição,
legibilidade e continuidade entre vistas. Fonte de jogo divergente fica marcada
como questão aberta, sem virar canon de equipamento ou moveset.

A promoção exige checklist completo/hash-bound, revisão independente sem
blockers e aprovação explícita do proprietário. Registre decisão
`sms_artifact_decision_v1` para o papel `model_sheet`, incluindo todos os
arquivos e SHA, atualize o head aprovado e marque a matriz ativa anterior como
`superseded`. O escopo de aprovação permanece conceitual; não se estende a
sprites, animação, conversão SMS, integração ou ROM.

Depois da promoção, mantenha a matriz aprovada ativa e seus sidecars canonizados
na raiz do diretório do personagem. Arquive folhas aprovadas substituídas em
`historical_approved/`, exercícios/candidatas em `review_drafts/` e aprovações
de papel distinto em `approved_records/`. Preserve a entrada e saída com SHA em
mapa reversível, atualize registros e referências path-bound e não altere os
pixels durante a organização. Preserve relatórios independentes como evidência
da revisão original; igualdade de hash demonstra continuidade dos bytes, não
renova julgamento artístico. `audit_art_review_checklist.py`,
`quality_review_router.py`, `artifact_registry.py --scan` e
`audit_learning_capture.py` cobrem estados, escopos, hashes e organização, mas
não substituem a leitura visual independente nem autenticam a aprovação humana.

## 118. Terminador 0xD0 da SAT existe só no modo 192 linhas (L128)

O Y armazenado 0xD0 encerra o parsing da SAT apenas no modo de 192 linhas. Nos
modos de 224 e 240 linhas (`VDPFEATURE_224LINES` / `VDPFEATURE_240LINES`, que o
header marca como SMS II only) 0xD0 é um Y comum: o VDP percorre as 64 entradas
e o sprite conta nas scanlines que cobre. Fonte: corpus hasheado
`out/smspower_corpus_2026-10-12/Sprites.txt` ("This only works in the 192-line
display mode").

Consequências:

- em 224/240, truncar a SAT com 0xD0 não esconde os sprites seguintes nem vale
  como otimização; entrada não usada precisa de outro Y fora da área visível;
- manifesto de cena declara `screen_h` ∈ {192, 224, 240}; qualquer outro valor
  reprova;
- manifesto em 224/240 com `sat_terminated: true` reprova.

Adenda aplicada 2026-10-13 (aprovada junto ao item A1; fonte vendorizada, não
esteira): `SMS_copySpritestoSAT` **escreve 0xD0 sozinho** — quando há menos de
64 sprites ativos, o primeiro slot livre recebe Y=`0xD0` (`cp #64 / jr z / ld
a,#0xD0 / out (c),a`), e quando não há sprite nenhum o slot 0 recebe o mesmo
`0xD0` (ramo `_no_sprites`). Lastro: `sdk/devkitSMS-upstream/SMSlib/src/SMSlib_sprite.c:184,191-195,209-211`; o X dessa entrada não é reescrito — é resíduo do quadro anterior. Em 192 linhas isso é o terminador inofensivo; em **224/240 a entrada de padding é um sprite comum com Y=0xD0**, contável no buffer de parsing (§119) e desenhado na scanline ~209 — um fantasma sem autor. Consequência operacional: em 224/240 o truncamento/`sat_terminated` não é apenas inútil, é **automático contra você** — o padding vem da própria biblioteca, e o manifesto precisa declarar o que a ROM faz com essa entrada (ou justificar a linha 209 vazia), não assumir SAT "cortada".

Gate: `audit_sprite_line_sim.py` (`--self-check` cobre 0xD0 reprovado em 192,
aprovado em 224, truncamento declarado em 224 e `screen_h` inválido).

Limites: a regra vem do corpus e não foi medida em emulador nem em console. O
comportamento em silício dos modos 224/240 fica `hardware_pass` pendente e não
é gate de emulador. A convenção de offset do Y armazenado foi fechada na §119.

## 119. Overflow de sprites é do buffer de parsing; Y armazenado é y − 1 (L129)

A cada scanline o VDP percorre a SAT em ordem e põe num buffer de 8 entradas
os sprites cujo Y e altura caem na linha seguinte. O parsing para quando as 64
entradas foram vistas, quando o buffer enche ou, em 192 linhas, no terminador
(§118). Se o buffer encheu e ainda há sprite na linha, o bit 6 do status é
setado e fica assim até a leitura da porta de controle. A contagem ignora X e
padrão: oito sprites transparentes ou fora da tela enchem o buffer e derrubam
o nono, mesmo sendo o único visível. Fonte: corpus hasheado
`out/smspower_corpus_2026-10-12/Sprites.txt`, seção "Table parsing".

Consequências:

- quem decide o que some é a **ordem da SAT**, não a posição na tela; sprite
  que não pode sumir entra antes na SAT;
- "esconder" sprite deixando-o na SAT com tile vazio não libera orçamento de
  scanline; para liberar, a entrada sai da linha (outro Y) ou da SAT;
- o manifesto de cena lista `sprites` em ordem de SAT e declara com
  `hidden: true` toda entrada sem pixel visível que a ROM mantém na SAT.
  Entrada que a ROM emite e o manifesto omite deixa o gate cego.

Offset de Y: o VDP desenha o sprite em `stored + 1`. `SMS_addSprite` grava
`y − 1`, então o `y` passado à SMSlib é a primeira linha desenhada, e o valor
que colide com o terminador é `y = 0xD1` (a variante com checagem devolve −2).
Lastro: os bytes de `SMSlib_sprite` em `sdk/devkitSMS/SMSlib/SMSlib.lib`
(`cp #0xD1`, `dec a` antes da escrita em `SpriteTableY`), lidos com apoio da
fonte upstream, mais o corpus. O simulador usava `y + 1` e reprovava y = 207
(que grava 0xCE) enquanto aprovava y = 209.

Gate: `audit_sprite_line_sim.py` reporta por linha o buffer, os descartados e
os descartados visíveis, e reprova qualquer linha com overflow. `--self-check`
tem o caso de 8 `hidden` + 1 visível, que reprova, e o de y = 207, que aprova.

Limites: o gate mede o manifesto, não a SAT que a ROM escreve; o flag de
overflow em runtime não foi lido em emulador nem em console. Bordas de Y
(valores armazenados perto de 0xFF) não estão modeladas.

## 120. Qualidade conjunta e taxa regional: aplicar os gates ao jogo real (L013/L035/L078–L081/L123)

Antes de ampliar slice/RC, usar `workflows/product-quality-checkpoint.md`: público
e critérios no GDD, input→ação→feedback→consequência, imagem no tamanho nativo,
música+SFX+restauração de canais, IA/HUD/FX simultâneos e pior frame da cena.
Parecer de agente não é playtest com público nem valida aceitação comercial.
Mais efeitos/tamanho ou nomes AAA não provam qualidade; técnica avançada precisa
de ganho observável, budget medido e fallback dentro do escopo.

`measure_runtime_probe.py --session` exige NTSC60/PAL50 em pelo menos duas
janelas completas, tolerância explícita até1FPS e dispersão até1FPS. Janelas
NTSC55 ouNTSC50 reprovam alvo60. `emulicious_dap.fps_constant` não descarta
amostra ausente nem aceita janela única. Taxa média regional não prova deadline
por frame, reação da lógica ou pose apresentada: contador ISR pode avançar sem
gameplay completo. Medir worst-frame/pacing e latência separadamente, em ROM
completa/SHA atual. Metas de controle pertencem ao GDD; não inventar limiar
universal de diversão. Resultado histórico50..60 não é aprovação target60.

L003/L006/L128/L129 aplicam também ao schema e packer: modo físico8x8/8x16,
Ystored=(y−1)&255, ordemSAT incluihidden. `audit_sprite_line_sim.py` rejeita
coerçãofloat/string/bool e perfil negativo/wrap não modelado. Manifesto não
observaSATreal; quirkszoomSMS1 continuam sem qualificação.

L124/L127: emendas de edição por revisão, máscara/franja, deltas deownership e
contorno separados dealpha; sólido2x2 não é área/bbox. Convergência não aprova
sombra/anatomia. Decisão de fonte emres/approved_art não comprova ROMbuildada
ourodando; conflito com memória/registry precisa reconciliação explícita.

`audit_claims.py` requer identificadores/escopo/autor/data e teto textual
não vazios. O gate lexical não autentica aprovação nem julga a semântica do
escopo; `reconcile_claims.py` histórico também não é checklist dequalidade
comercial. Nenhum PASS desses gates substitui evidência fresca, review nativo
e todos os eixos da entrega.

## 121. Espelhamento de tilemap no SMS1: reg2 com bit0=0 força bit10 do endereço VRAM a 0 (L130)

No VDP do SMS1, se o bit 0 do registrador 2 (base da name table) for 0, o bit
10 do endereço VRAM usado na consulta da name table é forçado a 0. As 12 linhas
inferiores da tela virtual passam a referenciar as mesmas entradas das 12
primeiras; com Y-scroll zero em modo 192, as 8 primeiras linhas preenchem o
terço de cima **e** o de baixo. Fonte: corpus hasheado
`out/smspower_corpus_2026-10-12/TilemapMirroring.txt`
("If bit 0 of VDP register 2 is 0, then bit 10 of the VRAM address for name
table lookups will be forced to 0"), e o veredito do próprio corpus:
"a common bug in homebrew software, however, which may assume the presence of
an SMS2 VDP. This behavior also does not function as intended on the
Genesis/Mega Drive VDP."

Consequências:

- o defeito é **invisível no emulador-alvo SMS2/PC**: o tilemap espelhado só
  aparece em SMS1; em Genesis não funciona como pretendido. "Rodou no
  emulador" não absolve a escrita;
- a inicialização padrão da SMSlib escreve reg2 = `0xFF` (bit0=1;
  `VDPReg_init[]` em `sdk/devkitSMS-upstream/SMSlib/src/SMSlib.c`, com o
  comentário "reg2: PNT is at address 0x3800"). O caminho padrão é seguro; a
  classe de defeito são escritas custom ao registrador 2 com valor par;
- `SMS_VDPturnOnFeature/turnOffFeature` não tocam o reg2 (os defines do header
  mapeiam registradores 0 e 1) — a escrita custom exige motivo explícito no
  código do projeto;
- exceção deliberada existe e é única no corpus: "Only one game relies on this
  behaviour: the Japanese version of Ys." Imitar *Ys* JP exige
  `--allow-sms1-mirror "<motivo>"` com o motivo registrado no memory bank/GDD;
  o gate então emite `excecao_declarada`, nunca `aprovado` silencioso.

Gate: `audit_tilemap_mirror.py` em três modos — `--source` (escritas literais
ao reg2: `outp(0xBF, vv); outp(0xBF, 0x82)`; `VDPControlPort` e a forma
prefixada `SMS_VDPControlPort` — o único sfr que a SMSlib vendorada expõe;
uma correção de 2026-10-14 fecha o bypass em que o padrão de adjacência exigia
o identificador nu e a forma `SMS_` escapava; `SMS_write_to_VDPRegister(2, vv)`;
valor não-literal reportado como não
provado, nunca aprovado), `--rom` (assinatura Z80 `3E vv D3 BF 3E 82 D3 BF`;
ausência é `nao_provado_estatico` porque o init da SMSlib usa tabela) e
`--snapshots` (modo autoritativo: `vdp_regs.bin` de 11 bytes produzido por
`blastem_sms.py`, byte[2] com bit0=1). `--self-check` cobre os três modos, a
exceção declarada, dump truncado, a recusa de variável como literal e as duas
formas do porta-objeto (nu e `SMS_`).

Limites: a lei é Tier 1 do corpus, não medida em console — o efeito em
silício SMS1 fica `hardware_pass` pendente e pertence à matriz de
compatibilidade (item A5 do dossiê, não aplicado). A varredura estática só
decide literais; runtime real exige a sessão `blastem_sms.py` com dumps.
**Campanha 2026-10-14 (probe `reg2_bit0_mirror`, ROM sha `364b7edc…`):**
com reg2=`0xFE` vivo em `vdp_regs.bin` (modo `--rom` também pega, offset
728), o BlastEm 1.0.0 **não espelha em nenhum dos modelos** (`sms1` e
`sms2` renderizam as linhas 16..23 próprias) — cenário C pré-registrado:
o emulador não modela o quirk; a lei permanece sem reprodução em simulador
deste host e o status de L130 continua `documentado`. Veredito:
`out/campaign_tier1_2026-10-14/reg2_bit0_mirror/verdict.json`.

## 122. Assimetria dos registros de scroll: Y lido uma vez por frame e wrapa ≥224 no modo 192; X ao vivo em HBlank (L131)

O registrador de scroll vertical (reg9) **é lido uma única vez por frame,
antes da tilemap ser desenhada**: "so it cannot be updated as the screen is
drawn for special effects". O horizontal (reg8) pode: "the horizontal scroll
register is updated during the HBlank interrupt". Logo, raster de scroll só
existe em X; split **vertical** por reg9 é impossível — o efeito de banda
vertical fixa (status bar sobre mundo rolando) é técnica de troca de name
table via reg2 em HBlank, não de scroll: é assim que *Sylvan Tale* faz
(`VRAMMemoryMap.txt`). O header materializa a assimetria: `SMSlib.h:386-387`
oferece `INLINE_SMS_setBGScrollX` "to be used in the line interrupt handler
for raster effects" e não existe contraparte para Y. Atenção cruzada com
§121: trocar reg2 em HBlank só é seguro com bit0=1; no SMS1 com bit0=0 a
própria tabela trocada espelha.

Wrap do scroll Y — a constante é o **tamanho da tilemap**, não a tela: em modo
192 linhas a tilemap tem 28×8 = **224 px** (32×28), e valores >223 escritos no
reg9 "wrap around, treated as if between 0 and 31 — setting the vertical
scroll register to 240 is equivalent to setting it to 16"; a variável do jogo
precisa dar wrap em 224, senão cada volta produz descontinuidade silenciosa
("to avoid discontinuities in the scrolling"). Em 224/240 linhas a tilemap tem
32×32 = 256 px e "there is no such wrapping — values from 0 to 255 are all
valid", e o truncamento natural da API (`unsigned char`) já é o módulo 256.
Geometria relacionada (mesma página): base da tilemap `$3800` em 192 e `$3700`
em 224/240, para não colidir com a SAT em `$3F00`.

Consequências:

- split horizontal com line interrupt continua válido (§6); promessa de
  "parallax vertical por reg9" no GDD é defeito de design, não de código —
  ou se troca a name table, ou se paga em tiles;
- cena com scroll Y em modo 192 declara no spec de cenas a constante de wrap
  224; o acumulador da ROM deve implementá-la;
- reescrita de reg2 em HBlank (técnica Sylvan Tale) entra no contrato do
  `audit_tilemap_mirror.py` — bit0=1 obrigatório.

Gate: `audit_vscroll_wrap.py --screen-h {192|224|240} --source <src>` —
literal de `SMS_setBGScrollY` decidido contra o modo declarado; acumulador com
mutação no arquivo sem token de wrap em 224 (modo 192) reprova; função,
expressão ou variável sem mutação reportam **não provado, nunca aprovado**.
`--self-check` cobre os 8 casos (reprovação 192 sem wrap, aprovação com wrap,
240≡16 em 192, 240 válido em 224, >255, chamada, extern, arquivo sem call).

Limites: o gate detecta **presença de token de wrap no arquivo**, não fluxo de
dados — presença não prova correção quadro a quadro, e o caminho entre a
mutação e a chamada pode ter ramos. Lei Tier 1 do corpus; o wrap ≥224 e a
leitura única não foram medidos em console: telemetria de reg9 em
`measure_runtime_probe.py` fica como verificação futura.
**Campanha 2026-10-14 (probe `vscroll_wrap224`, ROM sha `866f5cc8…`):** o
wrap ≥224 em modo 192 está **confirmado no BlastEm** — renders pixel-idênticos
240≡16, 224≡0, 255≡31, controle 240≠192, com o valor cru provivo por
`vdp_regs.bin[9]` e marcador RAM em cada fronteira. A **leitura única por
frame** (ausência de raster vertical) segue não medida — exige sonda por
linha. Engine única; console é LOTE F. Veredito:
`out/campaign_tier1_2026-10-14/vscroll_wrap224/verdict.json`. A técnica
Sylvan Tale está registrada como `documentado`, não como receita implementada.

## 123. Bits 13–15 da entrada de tilemap: o VDP ignora, o canon veda por padrão, engine declara para usar (L132)

A entrada de name table é uma palavra de 16 bits. O VDP só consome os bits
0–12: índice (0–8), flip H (9, `$200`), flip V (10, `$400`), subpaleta de
sprite (11, `$800`) e prioridade (12, `$1000`). Os **bits 13–15 são "Unused"**
para o hardware — a tabela do SMSPower anota que *"Some games use these bits as
flags for collision and damage zones"* (`Tilemap.txt`, sha256 `2168bc88…`;
geometria da tile em `Tiles.txt`, sha256 `ae995fd6…`). Isso confirma §6 por
autoridade externa citável (o selo Tier-1) e abre um gancho de engine: três bits
por tile, grátis, que um motor de luta pode usar como máscara de solo/dano/zona.

**Política (vedado por padrão).** Como o hardware descarta os bits e nenhuma
ferramenta do framework os lê hoje, um valor com bit 13–15 armado é ou um bug
(tile index estourado, flag canônica somada errado) ou um uso próprio do projeto
não declarado. O canon trata ambos como suspeitos: a entrada escrita via
`SMS_setTileatXY` deve manter `0x1FFF` como teto dos bits usados. **Flags
canônicos dos bits 9–12 não são "flags custom"** — flip/subpaleta/prioridade
continuam lícitos e o gate não os toca.

**Gancho de engine (declarado, não implantado).** O motor MUGEN
(`mugen_fighting_v1`) pode promover os bits 13–15 a camadas de colisão/dano do
stage, mas isso é decisão de design com consequence em runtime (o mesmo bit vira
semântica que a SMSlib e o VDP ignoram; só o interpretador do jogo a lê). Antes
de qualquer projeto fazer isso, a convenção bit-a-bit precisa estar no TDD/spec
de cenas e o gate precisa rodar com `--allow-tilemap-flags "<motivo>"`. Sem
declaracao, a escrita reprova. Registrar em `mugen-source-semantics` §"Camada de
chão por tile".

Gate: `audit_tilemap_bounds.py` ganhou o segundo eixo — **valor** da entrada,
não só coordenada. Literal com bits 13–15 armados reprova; o mesmo achado sob
`--allow-tilemap-flags` com motivo não-vazio vira `excecao declarada`
(aprovação com lastro, nunca silencio); expressão/variável é `nao provado`.
Flags canonicos 9–12 passam limpos. `--self-check` cobre os quatro casos novos
(reprova `$2000`, excecao declarada, `0x1E41` canonico passa, tile nao literal
indecidivel).

Limites: lei Tier 1 do corpus (o "unused" e o uso em jogos), não medida em
console. **Campanha 2026-10-14 (probe `tilemap_bits1315`, ROM sha
`1b167890…`):** no BlastEm a VRAM **preserva** os bits escritos (palavras
`$203C/$403C/$803C/$E03C` exatas no dump `vram.bin`) e a renderização os
**ignora** (seis células pixel-idênticas à control sem flags) — veredito
confirmado em nível de emulador, engine única; a preservação no silício
SMS1/SMS2 real continua `hardware_pass` pendente, questão de LOTE F. O gate só decide
literal em `SMS_setTileatXY`; `SMS_setTile` posicional e arrays de
`SMS_loadTileMap*` ficam fora — a tile index vindo de memória não é decidível
estaticamente e o projeto declara seu próprio contrato de mapa.

## 124. Mapa de VRAM: janela de sprites pelo reg6 ($FB 256 tiles / $FF 192), sobras legais com guarda e tilemap extra por reg2 (L133)

O layout corrente de VRAM (16 KB) é tabela do corpus: `$0000-$1FFF` graphics
dos tiles 0-255, `$2000-$37FF` dos tiles 256-447, `$3800-$3EFF` tilemap,
`$3F00-$3FFF` SAT, com reg2 e reg5 em `$FF` (`VRAMMemoryMap.txt`, sha
`ab4c480d…`). Dado novo para o orçamento (§9, §27): a SAT alocar **1 byte**
ao índice do sprite significa que o sprite só alcança a janela de 256 tiles
escolhida pelo **reg6** — `$FB` = base `$0000` (256 tiles únicos), `$FF` =
base `$2000` (192 únicos). A SMSlib liga em `$FF` (`VDPReg_init` reg6 =
`0xFF`, "Sprite tiles begins at address 0x2000", `SMSlib.c:29-31`; confirmado
como valor vivo nos dumps `vdp_regs.bin` das sessões BlastEm de 2026-10-14) e
expõe a troca por API: `SMS_useFirstHalfTilesforSprites`
(`SMSlib.h:53` → `SMS_write_to_VDPRegister(0x06, usefirsthalf?0xFB:0xFF)`).
O BG não sofre a janela: a entrada de tilemap guarda 9 bits de índice e
"the background can use any tile" (0-511).

Sobras legais de VRAM existem — cada uma com **condição de guarda do próprio
corpus**, não como espaço gratuito genérico:

- `$3F40-$3F7F` — stretch de 64 bytes não usados pela SAT quando o software
  ocupa 32 entradas = 2 tiles (índice de sprite 250/`$FA`, de tilemap
  506/`$1FA` quando reg6=`$FF`);
- `$3E00-$3EFF` — as 4 linhas inferiores do tilemap em modo 192 = 8 tiles
  (índices 240/`$F0` e 496/`$1F0`), **só se o jogo não rola verticalmente** —
  rolou, as linhas são dados do mapa (§122: a tilemap de 192 linhas tem 224 px);
- `$3F20-$3F3F` + `$3FC0-$3FFF` — 3 tiles quando o software se limita a ≤31
  sprites e grava `$D0` no Y da 32ª entrada (`$3F1F`): o terminador `$D0` **só
  vale em modo 192** (§118/L128) — em 224/240 a entrada seria lida como sprite
  na linha 208 e o "espaço livre" passa a desenhar lixo;
- **name table extra** trocada instantaneamente via reg2: duplo buffer de
  animação (atualizar uma enquanto a outra é exibida), menu, e split em
  mid-HBlank estilo Sylvan Tale (§122: o status bar fixo é troca de reg2, não
  scroll vertical; §121: no SMS1 a troca segura exige bit0=1, senão o mapa
  trocado espelha).

Consequências:

- o contrato de cena (`13-spec-cenas.md`) declara o mapa de VRAM por escrita:
  regiões de tiles BG/sprite, janela do reg6 pretendida e sobras reclamadas
  com a guarda satisfeita — "cou porque sobrou byte" sem guarda declarada é
  a classe de bug que este registro documenta (o `$D0` em 224 linhas é
  refutável pela própria lei de L128);
- trocar reg6 é decisão de pool, não de economia: `$FB` libera os 256 tiles
  inferiores para sprites, mas o BG perde o acesso exclusivo a `$0000-$1FFF`
  como zona segura — e o caminho §27 (`SMS_addSprite` citando tile <256 sem
  declarar base) continua gateado por `audit_sprite_mode.py`;
- tilemap extra consome região de tiles: o orçamento de tiles únicos da cena
  encolhe exatamente `linhas×64` bytes por mapa adicional.

Gate: `measure_vram_map.py` — `--plan` (schema `sms_vram_plan_v1`) julga
colisões entre regiões/blocos (tiles×PNT×SAT×extras), exige motivo para toda
name table extra, bloqueia tile de sprite fora da janela do reg6 e recusa
sobra reclamada com guarda violada (`sobria_sem_guarda`); `--snapshots` lê os
`vdp_regs.bin` de `blastem_sms.py` e confere reg5/reg6 vivos contra o plano
(divergência reprova; reg2 com bit0=0 gera alerta de mirror §121).
`--self-check` cobre janelas `$FB`/`$FF`, as três guardas de sobra, colisão
BG×PNT, tilemap extra sem motivo, modo 240 com base `$3800` (invasão de SAT),
cross-check de snapshot (conforme/divergente/alerta) e dump truncado.

Limites: as geometrias são Tier 1 do corpus; a janela de 256×1 byte do índice
de sprite é física da SAT, mas o que o VDP faz com reg6 fora de `$FB`/`$FF`
não é decidido aqui (a ferramenta aceita só os dois valores). O cross-check
mede o registrador no **emulador** — engine única BlastEm, console fica
LOTE F. A ferramenta julga o **plano declarado**: quem escreve VRAM fora do
plano (DMA inexistente, stagers à mão) escapa — o par estático do código é
`audit_tilemap_bounds.py`/`audit_sprite_mode.py`, o dinâmico é a sessão com
dumps.

## 125. Decisão por varredura não se conta em runtime: pré-computar na emissão (L134)

O laço do SDCC que recarrega locais via IX custa ~115–150 ciclos por iteração
(medido no piloto openbor_sms_rev1). Consequência de orçamento: contar ou
decidir centenas de células por quadro derruba o ritmo — no O2, o corte de
inimigos contado a cada quadro consumia ~2.07 quadros na pior pose e derrubava
o loop abaixo de 1.0; a decisão pré-computada na **emissão** (bit a bit; no O2,
máscara por pose+profundidade, 3 B/entrada, política conservadora) devolveu
**1.0 loop/frame** em idle e caminhada, com o runtime só consultando o bit.
Medição: `measure_runtime_probe.py` (ritmo do loop da ROM) e
`audit_sprite_line_sim.py` (orçamento de sprites/linha do lado da emissão).

Limites: os ciclos/iteração são ordem de grandeza **deste** projeto (SDCC sem
otimização; loops IX-relative) — não constante universal do Z80 nem promessa
para código otimizado. A máscara de 3 B/entrada é do elenco do piloto (poses e
profundidades do GAL); outro elenco recalcula. A ferramenta de ritmo mede o
efeito no loop, não atribui causalidade sozinha; a evidência do defeito
original é o registro `decided+measured` do escopo rev2 do O2
(`doc/artifacts/o2_vdp_pilot_scope_20261016.json`). Console segue LOTE F.

## 126. Sinal e anel do h-scroll de PNT parcial (L135)

Com a janela PNT declarada da câmera, o registrador de scroll X recebe
`N = (-cam) & 0xFF` — o valor anda ao contrário da câmera; a tela x≥8 mostra a
coluna PNT `cam_col + (x>>3)`. O anel mod-32 de colunas
(`[cam_col..cam_col+31]`) precisa ser reescrito a cada passo de 8 px,
**inclusive andando para trás** — anel reescrito só no avanço deixa colunas
velhas na janela (tearing na volta). Fecha junto com L043/§6: `LEFTCOLBLANK`
para x0..7, `LOCKHSCROLL` para HUD fixo e backdrop explícito (preto no O2).
Evidência do O2: `cam = clamp(px-120,0,376) & ~7`;
`SMS_setBGScrollX((unsigned char)(0u - cam))`; comparação framebuffer↔dados
emitidos com 0 divergências fora dos retângulos de sprite em cam_col
45/41/3/8/0 (inclui caminhada de volta); vídeos walk6/back6 gravados sem
compositor (bundle selado, ROM `b0eb624f…`).

Limites: **não há gate estático** para sinal/anel — a verificação da campanha é
comparação framebuffer↔dados emitidos (procedimento, não ferramenta canônica) e
os vídeos são evidência de comportamento, não oráculo. Candidatos ainda não
aplicados: expected-dir para `audit_render_glitch.py` (declarado N/A no O2 por
falta dele) ou comparador framebuffer↔colunas emitidas (natural no O4/terreno).
A técnica do anel é do engine deste piloto; o sinal é convenção da janela
declarada. Console segue LOTE F.

## 127. Escrita fora da janela do VBlank: integridade medida (L136)

Bytes escritos na VRAM fora da janela do VBlank **chegam**: um bloco bancado de
1856 B copiado para a VRAM 0x0000 logo após `SMS_waitForVBlank` atravessa ~230
linhas de varredura (janela declarada ~70 linhas / ~4,5 ms NTSC; ~8,1 B/linha
medidos) e chega íntegro em dois emuladores (dump de VRAM == fonte, zero
mismatches; fronteira visível exata em 1856 B), com o loop a 60 Hz no BlastEm.
A janela do VBlank governa **quando** transferir — qualidade visual de quadro e
orçamento de bytes/frame medidos —, não a integridade do dado. Não invocar
"escrita se perde" como motivo de desenho sem medir o caso; não simplificar
cronograma de upload sem medida cruzada e revisão de escopo.

Limites: medido em emulador (BlastEm sms2/NTSC + Emulicious); acesso do CPU à
VRAM durante display ativo no silício segue LOTE F. O custo por instrução
(OUTI vs laço) não é universal. Corrige o mecanismo invocado em L047: o resíduo
visual de redesenho a meio quadro permanece e a receita display-off de §9 segue
válida — o que se refuta é a perda de dado. Ferramentas: `capture_evidence.py`
(Emulicious com self-check) e `blastem_diagnostics.py` (views de decode
planar); o caso é reproduzido pelo harness do probe de laboratório
`mapper_vblank_copy` (campanha própria), não por ferramenta do wrapper.

## 128. Asserts observados, apresentação e preservação dos relatórios

Aplicação de L001/L013/L035/L036/L064/L086/L090/L091/L097–L099/L123/L125/L133/L136;
sem novo ID. O ganho esperado é controle, leitura e continuidade do jogo, não
um catálogo de técnicas ou uma promessa de qualidade comercial.

Separe passos solicitados, ACK frame VDP, tick da lógica e elemento de
animação. Média regional, prazo do commit VDP, resposta da ação e integridade
dos pixels são eixos diferentes. Completar ticks por espera crescente não
aprova latência. Frames absolutos não são deltas. Current/residente não prova
submissão SAT/PNT nem apresentação no framebuffer; uma pose pode estar legal
e aparecer na hora errada. Um vídeo que termina antes do retorno não fecha a
duração completa da ação. Referência operacional: `sms-observed-case-evidence.md`.

`audit_observed_cases.py --record RECORD` rederiva asserts dos reads primários
e intervalos observados de ACKs, com ROM/sessão/journal/layout por SHA.
O perfil `journal_ram_v1` valida identidade/ordem, pontos de reads sem execução
intercalada, igualdade/delta de RAM e deadline observado ancorado em input.
Reprova resumo de whiff quando os bytes mostram dano. Não autentica layout,
instrumentação ou journal, não mede pixels apresentados, primeira ocorrência,
FPS, voltas de contador nem cleanup; combina com `audit_subagent_session.py`,
`audit_counter_window.py` e revisão nativa. Relato agregado sem primários pede
coleta nova; não fabricar histórico. O selo de uma lista não prova que a lista
inclui o controle negativo e o terminal previstos no pedido.

L098/L099: medir pares/bytes realmente novos e prazo/idade/serviço por ator.
Current+next de um ator não fecha residência do par/FX/HUD. “Desacoplar hit de
arte” na lista histórica de §84 não autoriza dano invisível: a reorganização
precisa manter contato/perigo legíveis e uma política coerente de apresentação.
Legalidade da SAT após corte não prova integridade da arte; omissão permanente
não recebe aprovação de qualidade por ter zero flicker. Híbrido BG/sprites
continua candidato até medir atualização, overlap e restauração em ROM.
Patterns, PNT e SAT são regiões simultâneas, não o mesmo orçamento reutilizado.
L136 distingue integridade dos bytes e prazo visual; toda a lógica do jogo
não precisa ocorrer no VBlank.

Relatórios usam saída nova por run. `report_output.py` cria exclusivamente;
`audit_learning_capture.py`, `audit_hardware_constants.py`,
`audit_header_claims.py` e `audit_debug_markers.py` aceitam `--report-out`
(alias histórico `--json`) e recusam destino existente, inclusive aliases por
symlink/hardlink. A migração não abrange todas as outras ferramentas. Não
apagar JSON de entrada para contornar a recusa; `selftest.py` cobre criação
nova e preservação de fonte. O gate de constantes inclui a forma errada
“índice 0 transparente nas duas paletas”; não infere o total de cores de uma cena.
