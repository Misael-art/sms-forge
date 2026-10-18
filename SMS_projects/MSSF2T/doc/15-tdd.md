# 15-tdd — MSSF2T

> Autoridade #7. API = `SMSlib.h` / `PSGlib.h`.

## Restrições
Sem float, sem malloc, sem DMA, ≤8 sprites/scanline, SAT 64, 8 KB RAM.

## Arquitetura (HAMOOPIG-like, Z80)
Dois `Fighter` estáticos. FSM numérica herdada da tabela HAMOOPIG (subset).
Hit/hurt/push boxes em pixels. Startup/active/recovery em frames.
Projétil: um por lutador.

## Poses
8 folhas por lutador: idle, walk, punch, special, hit, KO, crouch, jump.
`crouch`/`jump` vêm de `tools/author_pose_variants.py`, que remodela por faixa
a silhueta já presente em `inc/*_tiles.h`. **Não** usar
`author_native_fighters.py` para arte nova: ele recorta de `art_src_base/`
(`reference_only`).

Gravidade (`apply_gravity`) roda em QUALQUER estado e `airborne()` é altura,
não estado (L050) — levar golpe no ar tirava o lutador de `ST_JUMP` e ele
ficava pendurado. `separate()` ignora quem está no ar, senão não há pulo por
cima.

`fight_gfx.h` é GERADO (`tools/gen_fight_gfx.py`, L052): escrever os tamanhos
à mão já fez o header dizer 1024 para uma folha de 832 B, e o streamer leu
fora dos limites. Rodar `--check` depois de mexer em folha. Gate de fábrica:
`audit_symbol_size_sync.py`.

## Mapa de memória (RAM)
| Faixa | Conteúdo |
|-------|----------|
| 0xC000+ | BSS SDCC (fighters, round, timer, input buffer) |
| 0xC7F0 | probe runtime SMRT (schema 1) — `volatile` |
| 0xC7F9 | `probe_pose` = pose do 1P; bit 7 leva o `facing` de carona (L054: estado curto não se prova por screenshot) |
| 0xC7FC | `probe_p2x` = x do oponente (troca de lado é posição RELATIVA) |

## Pools
| Pool | Máx | Bytes |
|------|-----|-------|
| Fighter | 2 | ~32 |
| Projectile | 2 | ~8 |
| Input history | 2×8 | 16 |

## VRAM
| Tiles | Uso |
|-------|-----|
| 18–60 | fonte 8×8 + tiles de barra (só BG) |
| 96–127 / 128–159 | Ken — **dois** bancos de pose |
| 160–191 / 192–223 | Guile — **dois** bancos de pose |
| 224–231 | Hadouken (direita / espelhado) |
| 232–239 | Sonic Boom (direita / espelhado) |
| 256–348 | palco (93 tiles) — região **só de BG** |

O palco mora em 256+ porque o name table indexa 0..511 e os sprites só
enxergam 0..255: 93 tiles de cais não disputam espaço com lutador nenhum.
`stage_ken_map` guarda índices relativos (byte) e o offset entra em runtime.

`SMS_useFirstHalfTilesforSprites(1)`. Metasprite: dx comparado a 0x80; tile unsigned pode ser ≥128.

**Banco duplo por lutador.** O stream escreve no banco ocioso e só troca o
banco exibido quando a pose inteira chegou. Com um banco só, a pose levava
~5 frames para subir enquanto o soco tem startup de 4: todo golpe aparecia
meio velho, meio novo. O custo é VRAM, não CPU.

## Orçamento de VBlank
~70 linhas (~16k ciclos) por frame. A SAT já consome ~256 B. Restam ~96 B de
tiles por frame, **de um lutador por vez** (`STREAM_BYTES`). Medido no gate
`measure_runtime_probe.py`: 32B→59.5 · 64B→58.3 · 96B→57.5 · 128B→55.5 ·
256B→40 fps. Alterar `STREAM_BYTES` sem remedir o fps não é permitido.

### Worst-frame medido na ROM (2026-09-08, L061)
Instrumento no probe SMRT (aditivo, schema 1): `probe_vline` (0xC7EA) =
VCounter lido NO FIM do trabalho do frame, antes do wait; `probe_vovf`
(0xC7EB) = contador saturante de frames com vline ≥ 0xC0. Leitura pelo
gate `measure_worst_frame.py` (wrapper) no pior caso real — modo atração
(trocas de pose de ~1 KB + HUD + projéteis):
- **247 de ~2.700 frames derramam no VBlank** (vovf_delta; pior linha 251/262
  NTSC) — ~9% dos frames;
- **fps segue 60**: derrame espreme o streaming de VRAM, não o frame;
- degrau seguinte: reduzir o stream de troca de pose (ou DMA, que o MVP
  exclui). Número em mãos; folga zero.

## Banking
48 KB linear (B01). Se estourar: mapper Sega — ainda não. (Spec de migração:
`doc/spec-banking.md`, preparada 2026-09-08, exige cerimônia de curadoria no
`build_inner.py`.)

## Áudio
**Cada SFX no canal para o qual foi AUTORADO.** `make_psg_assets.py` gera
`sfx_shot` para `SFX_CHANNEL2` e `sfx_hit` para `SFX_CHANNELS2AND3`, mas os
dois eram tocados em `SFX_CHANNEL3`: o fluxo PSGlib não batia com os canais
que recebia e o mix caía de 92% para 86% ativo (piso do gate: 90%). Cooldown
não resolvia — 14, 30 e 60 frames davam os mesmos 86%, prova de que a causa
era o canal e não a frequência. Hoje: `sfx_shot`→canal 2 (fireball),
`sfx_hurt`→canal 3 (impacto), `sfx_down`→canal 3 (KO), os dois últimos já
autorados para o canal 3 e antes sem uso na ROM. Resultado: **94% ativo**.
O `SFX_COOLDOWN` ficou só pelo ouvido (evita metralhadora num flurry); não é
ele que sustenta o gate.

### Base
PSGlib. `music_battle` é ostinato na nota 0x0A0 (uníssono 3 tone + noise).
A versão de 240 frames era **240 cópias do mesmo frame** (L051); PSGlib
já faz loop no `PSGEnd`. Stream atual: 49 B. Arpejo grave media 84% e
reprovava o piso 90%. `PSGPlay` + `PSGFrame` após o VBlank. Sem YM2413 no MVP.
Gate de fábrica: `audit_psg_redundancy.py`.
(A frase antiga "SFX hit/shot só no canal 3" descrevia justamente o defeito
corrigido acima — ficou aqui só para não parecer que a decisão sumiu sozinha.)

## Input
PORT_A = 1P, PORT_B = 2P — **uma leitura de `SMS_getKeysStatus()` cobre os
dois portes** (PORT_B_KEY_* são os bits altos). Passar 0 para o jogador 2
tornava o modo 2P impossível. Buffer de 8 direções para QCF; o laço varre do
mais ANTIGO para o mais recente (a versão anterior varria ao contrário e
reconhecia frente→baixo, disparando especial de graça na diagonal).

### Troca de lado: observada (L053 fechada no ciclo 2026-09-08)
O conserto (`apply_pose` quando o facing muda) está no código e o caminho é
exercido e OBSERVADO por pulo por cima: `input_memory.json` registra
`sideswap_provado=true` com `cruzou_no_ar=true` e o facing virando para o
novo lado após aterrissar (runs de 08/09). A frase antiga "correto por
leitura, não observado" descrevia o estado anterior à prova.

### Prova de input: memória, não pixels
`tools/prove_input_memory.py` lê `probe_px` (P[0].x) com a emulação pausada e
exige deslocamento **≥8 px na direção comandada, nos dois sentidos**.

Existe porque o detector de pixels é ambíguo aqui: Ken e Guile geram blobs
idênticos (309 px) e o gi do Ken funde com o deck. A fábrica (L038–L040) já
exige direção, identidade e escala nativa em `interaction_verdict`; bundles
anteriores a essa curadoria fechavam com `abs(dx)>=8` sozinho. Neste projeto
o canal certo continua sendo memória (`probe_px`).

**Canal neste host (L039 fechada 2026-09-07):** KDE/Wayland. xdotool/XTEST
não atravessa o KWin. Canal real: **kdotool + ydotool** (`emulator_input.py`).
Canário: Ctrl+BackSpace zera `probe_frame`. Prova selada:
`out/evidence/input_memory.json` (dx=+74/−90, `probe_keys` 0x08/0x04,
SHA `2990757f…`). `reconcile_claims` aceita esse JSON como lastro do eixo
gameplay. Botão 1 = tecla A (lido em `probe_state` no título).

### Escala da janela é entrada do gate, não detalhe de UI
A fábrica (L040) normaliza limiares de forma para a canvas 256×192. Bundles
velhos com Scale=2.25 no `.ini` inverteram o veredito (32×64 → 72×144) porque
os limiares eram absolutos. A escala entra no bundle; não tratar FAIL de
gameplay sem olhar `capture_scale`.

## Flip
`res/fighters/` olha para a esquerda. Facing direito é espelhado **em runtime**:
bitrev por byte (tabela de 256 B) para os tiles + dx-mirror na SAT em torno da
própria caixa da pose.

Isto REVERTE a decisão anterior ("sem bitrev no Z80 e sem dx-mirror na SAT",
que usava folhas `*_l` pré-espelhadas na ROM). Motivo: a ROM estava em
**100% de 32 KB** (código terminava em 0x7F70, header em 0x7FF0 — zero bytes
livres) e nada mais cabia, nem a fonte que o próprio GDD pedia. As dez folhas
`*_l` eram, byte a byte, o bit-reverse das folhas base — 9,7 KB de duplicata.

O preço é CPU: o espelhamento custa fps e foi ele que forçou `STREAM_BYTES`
de 256 para 96. Equivalência verificada pixel a pixel contra as folhas `*_l`
nas 12 poses antes da remoção.

Folhas `inc/*_l_tiles.h` continuam no disco mas **não são compiladas** e estão
defasadas (ainda têm o placeholder). Não reintroduzir sem regerar.

## Fonte e HUD
`tools/make_font.py` gera 41 glifos 8×8 (4bpp, cor 1) + 2 tiles de barra.
O `stage_ken_tiles` já trazia um alfabeto embutido (tiles 1..7 = K,E,N,G,U,I,L)
usado por `stage_ken_map` nas colunas 1 e 25 — por isso `hud_static()` escreve
os nomes NESSAS colunas, sobrepondo, em vez de encostar uma segunda cópia ao
lado. Texto é escrito com um único latch de endereço + auto-incremento
(`put_run`), não com `SMS_setTileatXY` por caractere.

## Palco — cais do Ken
`tools/author_stage_ken.py` desenha 256×192 e recorta em 93 tiles (2976 B).
**Pixel art autoral.** A sheet `art_src_base/.../stage_ken_arcade_v1.png` é
`reference_only` (Capcom) e foi usada como RÉGUA — horizonte, proporção
céu/mar/deck, iate atracado à direita, tábuas em perspectiva — nunca como
fonte de pixel. `make_stage()` do `translate_ssf2t.py`, que reamostrava o rip
direto para dentro da ROM, foi desativado: era código morto e uma armadilha.

Padrões periódicos não são estética, são orçamento: cristas e tábuas em
posição livre davam **323 tiles únicos** (nem cabia no mapa de bytes). Com
período de 32/64/128 px e elementos repetidos em x múltiplo de 8 — as nuvens
e os dois barris compartilham tiles — o palco cabe em 93.

### Barras de vida
Tiles com **moldura escura** (cor 15), não bloco chapado. Chapada, a barra
virava o retângulo mais saturado da tela e o detector de gameplay travava
NELA em vez do lutador — eixo reprovando com deslocamento zero mesmo com o
input funcionando. Regra geral: nada de BG ou HUD pode ser o objeto mais
saturado com forma de sprite.

## Parallax por raster
Uma camada de BG só, cortada em bandas pela interrupção de linha
(`stage_raster` em `src/fight.c`, armado por `stage_scroll_frame` no VBlank):

| Linhas | Banda | Scroll |
|--------|-------|--------|
| 0–15 | HUD | **travado** no VDP (`VDPFEATURE_LOCKHSCROLL`) |
| 16–63 | céu / nuvens | 1 px a cada 8 frames |
| 64–111 | horizonte + iate | 0 — o barco está *atracado* |
| 112–127 | mar perto | 1 px a cada 2 frames |
| 128–191 | deck | 0 — é onde os lutadores pisam |

`LEFTCOLBLANK` também é obrigatório: com H-scroll ligado o VDP mostra lixo nos
8 px da esquerda (o tile que entra ainda não foi buscado) — aparecia um talho
vertical com pedaço da barra de vida e um bloco cinza cortando céu, mar e
deck. `STAGE_X_MIN` é 8, então nem o lutador encurralado entra na faixa.

Sem o `LOCKHSCROLL` o placar andaria junto com as nuvens. O horizonte fica
parado de propósito: se o iate deslizasse junto com o mar, denunciaria que
céu e mar são a mesma camada. Custo medido: ~0,5–1 fps.

Verificação: entre duas capturas, as linhas 88 (iate) e 185 (deck) dão
**0 pixels de diferença** e as bandas de céu e mar dão diferença — bandas
independentes, confirmado. A taxa exata não é mensurável assim porque
`capture_evidence.py` não é exato em contagem de frames.

## Arte
`tools/fix_sprite_transparency.py` — as folhas do Ken saíram do translate com
um placeholder desenhado por baixo (retângulo cor 12 + moldura cor 1), que o
VDP renderizava como uma caixa azul opaca em volta do lutador.
`tools/repack_sheets.py` — descarta sprites 8×16 totalmente transparentes e
deduplica pares de tiles; valida o canvas antes/depois pixel a pixel.
