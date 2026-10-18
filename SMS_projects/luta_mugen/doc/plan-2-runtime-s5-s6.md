# Plano histórico — Runtime S5–S6 / perfil legacy_probe_quarter (luta_mugen)

> **Revisão vigente 2026-09-26:** `engine_quality_contract.json` e
> `16-engine-review-2026-09-26.md` supersedem a escala 1:4/48 px como limite do
> motor. Números e tarefas T10 abaixo são histórico do perfil
> `legacy_probe_quarter`, sem aceite no novo piso. Próxima cena precisa medir
> corpo idle 45–55% da área útil (perfil inicial: 72–88 px), custos simultâneos
> e capacidade expansível. Técnicas opcionais exigem A/B; não estão implementadas
> por constarem no contrato.
>
> **Uso:** este arquivo registra a execução original de T10. Não executar os
> checkboxes de escala como padrão de produção atual. S4.5a/b e os limites
> 1:4/32×48 são o perfil `legacy_probe_quarter`; a rota vigente está em
> `tools/sms_wrapper/.agent/workflows/mugen-engine-quality.md` e
> `doc/05_technical/mugen_engine_standard.md`.


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal histórico:** Fechar o furo medido do S4 do perfil T10 (gate
`audit_sprite_line_sim` = FAIL, pico 32/linha, SAT 256) com a escala 1:4 então
escolhida e construir o runtime Z80. O resultado permanece útil como baseline
comparativa; o padrão de escala foi atualizado em 2026-09-26.

**Arquitetura histórica:** O motor (Python, `tools/sms_wrapper/mugen2sms/`) ganhou uma etapa S4.5:
downscale 1:4 fixo + emissão de arte no formato de runtime provado pelo MSSF2T (metasprite
de 3 bytes `{dx, dy, tile}` + `METASPRITE_END`; espelhamento horneteado como tile extra,
porque **o SAT do SMS não tem flip de sprite** — precedente: MSSF2T `src/fight.c:1108-1129`
usa `TILE_FB1L`, um tile espelhado separado). O consumidor (`SMS_projects/luta_mugen/src/`)
é um interpretador de tabelas compiladas: FSM por dados, física Q8.8, colisão clsn em
software, streaming de VRAM só no VBlank, banking Sega mapper.

**Tech stack:** Python 3 (conversor, testes pytest), SDCC + devkitSMS (`sdk/devkitSMS`,
headers = autoridade #8), gates do harness `tools/sms_wrapper/` (mesmo harness que deu
FAIL — ele é o veredito, não opinião minha).

**Referência vigente:** `SMS_projects/luta_mugen/doc/11-gdd.md` §"Padrão de entrega vigente",
`doc/05_technical/mugen_engine_standard.md`, o workflow atual e
`doc/10-memory-bank.md`. A especificação 1:4 nas tarefas abaixo é histórico T10.

## Global Constraints

- Escala histórica de T10 (GDD 2026-09-25; supersedida 2026-09-26): `SPRITEMODE_TALL` 8×16; alvo de
  no máximo metade do orçamento físico por linha para cada lutador (~32 px) × **≤3
  de altura** (~48 px); downscale
  **1:4 fixo** no conversor; pose que ainda estourar vira `manual` e **não entra no
  build**; flicker/rotação de prioridade para mascarar overflow é proibido.
- Cena versus: 2 lutadores = pico 8/scanline **exato** (teto físico), SAT ≤ 64.
- ❌ float/double em runtime; ❌ malloc/free; ❌ API inventada — só o que está citado
  em `sdk/devkitSMS/SMSlib/SMSlib.h` / `PSGlib/PSGlib.h` (linhas citadas por tarefa);
  ❌ VRAM fora do VBlank; ❌ lógica de build fora de `tools/sms_wrapper/`.
- Ken/arte real **nunca** no Git: derivativos só em `out/local_study/` (gitignored);
  o repo comita apenas fixtures sintéticos e o runtime.
- Paridade de doação: todo arquivo novo do fork é registrado em
  `doc/doacao_md_mugen2sms.json` como `origin: "local_original"` com
  `local_sha256_after_deviation`; editar arquivo pinado exige **re-pin** no mesmo commit.
- Gate final = ROM vista rodando no emulador com evidência selada ao SHA da ROM
  (`seal_fresh_evidence_bundle.py`). `documentado ≠ implementado ≠ buildado ≠
  testado_em_emulador`.
- APIs verificadas (usar EXATAMENTE estas; header é a fonte):
  - `SMS_setSpriteMode(SPRITEMODE_TALL)` — SMSlib.h:54-57
  - `SMS_addMetaSprite(x, y, metasprite)` / `METASPRITE_END 0x80` — SMSlib.h:214-216
  - `SMS_initSprites()` SMSlib.h:188 · `SMS_copySpritestoSAT()` SMSlib.h:211
  - `SMS_loadTiles(src, tilefrom, size)` = 4bpp/32B por tile — SMSlib.h:130
  - `SMS_setBGPaletteColor/SMS_setSpritePaletteColor(entry,color6bit)` — SMSlib.h:249-250
  - `SMS_getKeysHeld()/SMS_getKeysPressed()` + `PORT_A_KEY_*` (UP 0x0001, DOWN 0x0002,
    LEFT 0x0004, RIGHT 0x0008, **1** 0x0010, **2** 0x0020, START=1) — SMSlib.h:287-303
  - `SMS_setTileatXY(x,y,tile)` — SMSlib.h:117 · `SMS_useFirstHalfTilesforSprites(1)`
    (lei L006; já em uso no esqueleto `src/main.c`)
  - `SMS_mapROMBank(n)` / `SMS_saveROMBank()` / `SMS_restoreROMBank()` — SMSlib.h:70-83
  - `PSGPlay(song)` / `PSGFrame()` por VBlank / `PSGSFXPlay(sfx, SFX_CHANNELS2AND3)` —
    PSGlib.h:37-43, 56-57, 8-11 (SFX só nos canais 2+3; música nos 0+1)

**Blocker herdado (documentado no memory bank):** o round Ken do S4 gerou cena com pico
32/scanline e SAT 256 → `veredito: FAIL`. As Tasks 1–2 invertem esse número com o MESMO
gate.

---

### Task 1: S4.5a — downscale 1:4 e reclassificação no conversor

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_scale.py`
- Modify: `tools/sms_wrapper/mugen2sms/analysis/fidelity.py` (poses usam escala de runtime p/ classe)
- Modify: `tools/sms_wrapper/mugen2sms/generators/smsdev.py:77` (`generate` aplica escala antes de `to_sms_pose`)
- Test: `tools/sms_wrapper/mugen2sms/tests/test_sms_scale.py`
- Modify: `SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json` (registrar novo + re-pin dos editados)

**Interfaces:**
- Consumes: `Pose/placements` de `converters/sms_tiles.to_sms_pose`; `classify_character(ch, limits)` de `analysis/fidelity`.
- Produz: `sms_scale.MAX_COLS = 4`, `sms_scale.MAX_TALL_ROWS = 3`, `sms_scale.SCALE = 4`,
  `sms_scale.downscale_indexed(sp, k=4) -> SimpleNamespace(width,height,pixels,palette,group,image)`
  (nearest topo-esquerda, mesmo método de `prepare_sms_pixel_art.py`; o input é o sprite
  IR — `.width/.height/.pixels flat/.palette RGB tuples),
  `sms_scale.pose_runtime_size(w_px, h_px) -> tuple[int,int]` (pós-1:4, por excesso),
  `sms_scale.needs_scale(w,h) -> bool` (não cabe 4 col × 3 TALL em 1:1),
  `sms_scale.exceeds_budget(w,h) -> bool` (nem 1:4 salva → `manual`).

- [x] **Step 1: Teste falho** — `tests/test_sms_scale.py`:

```python
from converters import sms_scale as sc

def test_downscale_nearest_mantem_indices():
    img = {"w": 16, "h": 16, "palette": [(0,0,0),(255,0,0),(0,255,0)],
           "pixels": [bytes([1]*16) if y < 8 else bytes([2]*16) for y in range(16)]}
    out = sc.downscale_indexed(img, 4)
    assert (out["w"], out["h"]) == (4, 4)
    assert all(row == bytes([1,1,1,1]) for row in out["pixels"][:1])
    assert all(row == bytes([2,2,2,2]) for row in out["pixels"][1:])

def test_orcamento_pose_poca_escala():
    # 128x112 nativo -> 32x28 -> 4 colunas de 8px; 28px = 2 linhas TALL + sobra p/ 3a
    assert sc.pose_runtime_size(128, 112) == (4, 2)   # (colunas, linhas TALL) ceil
    assert not sc.exceeds_budget(128, 112)
    # 48 px de largura pós-escala = 192 nativo -> 6 colunas > 4 -> manual
    assert sc.exceeds_budget(192, 48)
```

- [x] **Step 2:** `pytest tests/test_sms_scale.py -v` → FAIL (`No module named ... sms_scale`).

- [x] **Step 3: Implementar `sms_scale.py`** — `downscale_indexed` amostra nearest
  (`px[y*k//h][x*k//w]`), preserva `palette` intacta (cores já são do contrato — a
  paleta não muda ao reduzir; só a contagem de pixels). `pose_runtime_size`:
  `cols = -(-w8 // 8)` com `w8 = -(-w_px // SCALE)`; idem linhas TALL (16 px).
  `exceeds_budget = cols > MAX_COLS or rows > MAX_TALL_ROWS`. Sem dependências novas.

- [x] **Step 4: Ligar no fluxo.** Em `generators/smsdev.generate`, antes de
  `to_sms_pose(sp)`, aplicar `downscale_indexed(sp_img, sc.SCALE)`; se
  `sc.exceeds_budget(w,h)` da pose resultante → adicionar `Element("pose:<n>.<i>",
  "manual", "estourou-apos-escala")` ao relatório e **pular** a arte (linha no
  `s4_generation_report.json` `excluded_by_classe.manual`). Em
  `analysis/fidelity.classify_character`, a regra `scanline>8` passa a usar o
  orçamento **pós-escala** (`pose_runtime_size` da bounding box da pose × 2 lutadores).

- [x] **Step 5: Testes verdes + round Ken local** (arte fora do Git):

```bash
cd tools/sms_wrapper/mugen2sms && python3 -m pytest tests/ -q           # esperado: tudo verde
python3 -m generators.smsdev "/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip" \
    --out ../../SMS_projects/luta_mugen/out/local_study/generated
```
  (o CLI real é `smsdev <pacote> --out <dir>` — generators/smsdev.py:169-170; rodada
  local a partir de `tools/sms_wrapper/mugen2sms`, ~3 min em background)
  Esperado: `s4_generation_report.json` sem traceback e com `estourou-apos-escala`
  em `excluded_by_classe.manual`. O `gate_scanline` pode **virar PASS já aqui**
  (worst-scene agora conta a pose pós-escala) — reportar o número medido, sem
  assumir veredito.

- [x] **Step 6: Re-pin do manifest + commit** (rode o script que recalcula
  `local_sha256_after_deviation` dos 3 arquivos editados + registra `sms_scale.py`):

```bash
git add tools/sms_wrapper/mugen2sms/converters/sms_scale.py \
        tools/sms_wrapper/mugen2sms/analysis/fidelity.py \
        tools/sms_wrapper/mugen2sms/generators/smsdev.py \
        tools/sms_wrapper/mugen2sms/tests/test_sms_scale.py \
        SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json
git commit -m "feat(mugen2sms): S4.5a downscale 1:4 travado pelo GDD no conversor"
```

---

### Task 2: S4.5b — formato de runtime (metasprite 3B, tiles TALL pareados, flip horneteado, P2 por shift de índice)

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/generators/runtime_format.py`
- Modify: `tools/sms_wrapper/mugen2sms/generators/smsdev.py` (gera também `<slug>_runtime.h/.c` no formato do runtime)
- Test: `tools/sms_wrapper/mugen2sms/tests/test_runtime_format.py`
- Modify: manifest (registro + re-pin)

**Interfaces:**
- Consumes: `Pose(width,height,tiles,placements,...)` de `converters/sms_tiles`.
- Produz:
  - `runtime_format.build_frames(pose, tile_base: int) -> bytes` — sequências de
    3 bytes **`dx, dy, tile`** terminadas por `dx=0x80` (`METASPRITE_END`), formato
    provado em ROM por MSSF2T (`SMS_projects/MSSF2T/src/fight.c:1095-1129`).
  - `runtime_format.pack_tiles_tall(pose) -> (blob, map_flip)` — blob = concatenção de
    pares verticais (topo 8×8, base 8×8) **por construção da fonte**: o conversor já
    sabe que uma pose tem alturas 16; índice local sempre par. `map_flip[(tx,ty)]` →
    índice do tile espelhado horizontalmente (bytes invertidos pixel a pixel; SMS não
    tem flip de sprite — espelho é outro padrão, custo medido de VRAM).
  - `runtime_format.shift_palette_indices(blob, offset)` — cópia com `idx+offset`
    (P2 = mesmos padrões em faixa de índices distinta do MESMO sprite palette; a
    restrição medida é `|pal(P1) ∪ pal(P2)| ≤ 15` — sprite palette única do SMS,
    SMSlib.h:249-250).

- [x] **Step 1: Teste falho** — `tests/test_runtime_format.py`:

```python
from generators import runtime_format as rf
from converters.sms_tiles import Pose, Placement

def _mini_pose():
    tiles = [bytes(32), bytes(range(32))]                      # 2 tiles 4bpp
    return Pose(width=8, height=16, tiles=tiles,
                placements=[[Placement(0, False, False, 0, 0),
                             Placement(1, True,  False, 0, 8)]],
                palette=(), unique_tiles=2, flips_used={1})

def test_metasprite_triples_e_fim():
    b = rf.build_frames(_mini_pose(), tile_base=0x20)
    assert b[0:3] == bytes([0, 0, 0x20])                  # dx,dy,tile
    assert b[3:6] == bytes([0, -8 & 0xFF, 0x21])          # segundo sprite
    assert b[6] == 0x80 and len(b) == 7

def test_flip_vira_tile_espelhado_distinto():
    pose = _mini_pose()
    blob, mirrors = rf.pack_tiles_tall(pose)
    mirrored = mirrors[1]                      # tile 1 tinha hflip
    # linha 0 da fonte = planos (0x00,0x01,0x02,0x03): espelhar inverte bits de cada plano
    assert blob[mirrored*32 : mirrored*32 + 4] == bytes([0x00, 0x80, 0x40, 0xC0])
    assert blob[mirrored*32 : (mirrored+1)*32] != pose.tiles[1]  # espelho é OUTRO padrão
```

- [x] **Step 2:** `pytest tests/test_runtime_format.py -v` → FAIL (`No module named`).

- [x] **Step 3: Implementar `runtime_format.py`** conforme interfaces acima. Regras
  duras: `dx = tx*8`, `dy = -(altura - (ty*16+16))` (origem do metasprite = pés,
  como MSSF2T espera); tile espelhado é alocado depois dos normais (dedup por
  conteúdo do blob). `shift_palette_indices` soma `offset` só a índices `!=0`.

- [x] **Step 4: Emitir runtime no `smsdev.generate`** — por personagem:
  `<slug>_runtime.c` com tabelas nomeadas:

```c
const unsigned char pose_meta_<anim>_<frame>[] = { /* rf.build_frames */ 0x80 };
const struct { unsigned char dur_frames; const unsigned char *meta; } frames_<slug>[] = {...};
const unsigned char tiles_<slug>[];  unsigned int tiles_<slug>_len;  /* base 0 = tile par */
const unsigned char pal_<slug>_bg[16], pal_<slug>_spr[16];           /* bytes 6-bit */
const signed int clsn_<slug>[];                                      /* int16, já do S4 */
const unsigned char patt_<slug>[];                                   /* StepCodes do sms_cmd */
```

- [x] **Step 5: Gate do harness tem que virar verde.** Rodar o round Ken local; o
  worst-scene do `s4_generation_report.json` agora conta **por formato de runtime**:
  2 lutadores, cada um limitado a metade do teto físico por linha; entradas de espelho não contam na scanline.

```bash
python3 -m generators.smsdev "/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip" \
    --out ../../SMS_projects/luta_mugen/out/local_study/generated
python3 -c 'import json;g=json.load(open("../../SMS_projects/luta_mugen/out/local_study/generated/s4_generation_report.json"))["gate_scanline"];print(g["veredito"],g["peak_per_line"],g["sat_entries"])'
```
  Esperado: `PASS 8 ≤64` (pico ≤8, SAT ≤64). **Se não virar PASS, parar e reportar o
  número — não há terceiro caminho** (a escala é contrato do GDD).

- [x] **Step 6:** suíte completa + re-pin + commit
  `feat(mugen2sms): S4.5b formato de runtime SMS; gate worst-scene do Ken vira <veredito>`.

---

### Task 3: Cena 01 `probe_import` — runtime esqueleto lê tabela gerada e ROM boot

**Files:**
- Create: `SMS_projects/luta_mugen/inc/luta.h` (contrato das tabelas)
- Modify: `SMS_projects/luta_mugen/src/main.c` (substitui esqueleto)
- Create: `SMS_projects/luta_mugen/tests_c/scene01.c` — NÃO: o teste da cena 01 é a
  ROM no emulador (harness). Fixtures sintéticos committáveis vivem em
  `SMS_projects/luta_mugen/inc/gen/` (gerados do char sintético dos testes, sem Ken).
- Modify: `doc/13-spec-cenas.md` (preencher cena 01 com números MEDIDOS)

**Interfaces:**
- Consumes: `<slug>_runtime.c` da Task 2 compilado ao projeto (`inc/gen/` para o
  sintético; `out/local_study/gen/` para Ken, via flag de build local).
- Produz: `luta.h` com os structs que as Tasks 4–7 compartilham:

```c
typedef struct { unsigned char dur; const unsigned char *meta; } Frame;
typedef struct { signed char x, y; unsigned short w, h; } Box;   /* clsn flat */
typedef struct {
    unsigned char id;             /* pose id (estados referenciam por id) */
    unsigned char n_frames; const Frame *frames;
} Anim;
typedef struct { unsigned char facing; signed int x; signed int y; /* Q8.8 */
                 unsigned char anim, frame, tick; unsigned short life; } Fighter;
#define FIGHTER_TILE_BASE 0x00    /* sprites no 1º half (SMSlib.h:53, L006) */
```

- [x] **Step 1:** Escrever `main.c` da cena 01: `SMS_displayOff();
  SMS_useFirstHalfTilesforSprites(1); SMS_setSpriteMode(SPRITEMODE_TALL);` carregar
  `tiles_`, paletas (`SMS_setBGPaletteColor`/`SMS_setSpritePaletteColor` por entrada),
  nome table com rodapé de tiles sólidos (`SMS_setTileatXY`), desenhar a frame 0 de
  cada anim em pose estática alternando a cada 30 frames (`SMS_addMetaSprite`),
  `SMS_initSprites(); ... SMS_copySpritestoSAT(); SMS_displayOn();` dentro do loop
  `SMS_waitForVBlank()`. **Verificação de hardware (não assumir):** pares TALL
  topo/base — renderizar um tile-teste 0=branco/1=preto na cena 01 e conferir na
  captura; se o VDP inverter o par, corrigir `pack_tiles_tall` (ordem topo↔base) com
  teste novo na Task 2 — não remendar no runtime.
- [x] **Step 2: Build gate:** `bash SMS_projects/luta_mugen/build.sh` → ROM; erro de
  link >48 KB já antecipa a Task 6 (banco) — neste ponto o sintético cabe linear.
- [x] **Step 3:** `python3 tools/sms_wrapper/emulator_session.py --project SMS_projects/luta_mugen --rom <rom>`
  e `capture_evidence.py` → screenshot não-branca; `audit_deterministic_boot.py --rom`
  → PASS; `audit_render_fidelity.py` (estrutura da fonte vs captura — sprite presente).
- [x] **Step 4: Preencher `doc/13-spec-cenas.md` cena 01** com VRAM/picos da MEDIDA
  (não estimativa). Commit: `feat(luta_mugen): cena 01 probe — tabela gerada vira ROM no emulador`.

---

### Task 4: Interpretador FSM + física Q8.8 + colisão clsn (motor `fight.c`)

**Files:**
- Create: `SMS_projects/luta_mugen/src/fight.c`, `inc/fight.h`
- Test: evidência = cena 02 (não existe unit-test de Z80 aqui); cada decisão de
  frame budget vira linha no memory bank.

**Interfaces:**
- Consumes: `Anim/Frame/Box/Fighter` (Task 3) + tabelas do runtime (Task 2).
- Produz:

```c
void fight_reset(Fighter *p, unsigned char slot);
void fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys); /* 1 frame */
void fight_draw(void);              /* precedentes MSSF2T: projéteis antes, SAT */
extern volatile unsigned char dbg_frame;  /* __at() só com volatile (L009) */
```

- [x] **Step 1:** Máquina por dados: `states_<slug>[]` destilados no S2/S4 (anim,
  flags `physics|hitcheck|blockable`, janela startup/active/recovery vinda de
  `clsn` por frame). Tick: `if (++p->tick >= frames[...].dur) {p->tick=0; próxima
  frame;}`. Física: `vx, vy` em Q8.8 (tabelas `const signed int grav_tbl[]`;
  NUNCA `int16 * 8.5`). Colisão: AABB em colunas inteiras (`box_overlap`), hit →
  `hitstop=8`, knockback da tabela do estado, dano constante por golpe (sem
  multiplicador — fora do corte, TDD).
- [x] **Step 2:** Idle/walk/jump/crouch/punch1/punch2/block para o sintético;
  animação avança sem input (ver Task 5 para input vivo).
- [x] **Step 3:** Build + boot; `measure_frame_advance.py` (contador `dbg_frame`)
  → 50–60; commit `feat(luta_mugen): FSM interpretado por tabelas + clsn em software`.
  Medido: 59.6 fps constante (célula período 128, 60 s, 23× sobreamostragem);
  boot determinístico PASS 2 runs; ROM `145a0433…fb16`.

---

### Task 5: Input vivo (o eixo que reprovou MSSF2T) — gate primeiro, código depois

**Files:**
- Create: `SMS_projects/luta_mugen/src/input.c`, `inc/input.h`
- Consumes: `patt_<slug>[]` (StepCode de `converters/sms_cmd`: byte de dir/keys +
  janela), `SMS_getKeysHeld()/Pressed()`.

**Interfaces:**
- Produz: `unsigned int input_read(void);` → bits já na convenção
  `{U,D,B,F}=DIR_BITS, {A,S}=KEY_BITS do sms_cmd;`
  `input_pattern_hit(const unsigned char *steps) -> unsigned char;`

- [x] **Step 1: Provar o canal ANTES da ROM reagir:**
  `python3 tools/sms_wrapper/emulator_input.py --self-check` (canal = uinput
  kdotool/ydotool; NUNCA XTEST em Wayland/KWin — L039), depois enviar uma tecla e
  ver `dbg_keys` no probe de memória (`measure_runtime_probe.py` lê RAM via DAP sem
  depender de pixels — precedentes L035/§37).
  MEDIDO: self-check PASS antes de tocar a ROM; mapa SMRT na ROM (magic/schema
  0xC7E0..E4, snapshot 0xC7F2..0xC7FD); canario frame 508→63 por reset.
- [x] **Step 2:** Buffer de 16 amostras + match de padrão (janela de frames vinda do
  StepCode `rel_time`); botões: 1=fraco, 2=forte (remape QCB+1 etc. do GDD);
  start = pause (NMI existente do crt0).
  MEDIDO: `src/input.c` com matcher no formato do CMD blob; latch de padrão
  0x03 (punch e hold-F casam). K_GUARD fica bit sintético — 2 botões não o
  alcançam; remap "recuar = guard" declarado para a cena 02 (`inc/input.h`).
- [x] **Step 3:** Cena de teste: pad → Ken anda/salta/socor **ao vivo**; evidência
  com `capture_video.py` (transição não vive em screenshot — §45). Commit:
  `feat(luta_mugen): input vivo provado no emulador via canal uinput`.
  MEDIDO (ROM `fe66394c…dc9`): Right +70 px / Left −88 px com keys vistos sob
  tecla, pulo 94 px + estado JUMP, soco B1 a gap −9 → boss 237→232 score 3,
  crouch estado 4 — `t5_input_memory.json` 5/5; `t5_live.mp4` movimento 1.1%
  PASS; `t5_probe.json` fps 59.19/58.79; boot determinístico PASS. A caçada do
  vídeo expôs bug real de CRAM (entry do chão nunca inicializada — cor variava
  entre runs; corrigida e travada em 0x15).

---

### Task 6: Banking + streaming de VRAM (paga a dívida medida do S3: 1,16 MB de tiles/lutador)

**Estado medido (2026-09-26): Task 6 concluída para a arena de fixture sintético.**
L082 invalidou as leituras antigas: `t6_phase_profile_verified.json` (`3d08c5fd…`)
marcava 2.968/3.000 derramamentos porque o predicado de VCounter estava
invertido. As leituras corrigidas em builds posteriores encontraram derrames
reais e conduziram a duas mudanças: upload direto do bank e separação de CPU do
bloco VBlank. A primeira captura após a separação revelou outro defeito visual:
`SMS_VRAMmemcpy_brief` recebe destino em **bytes**; o stream passava índice de
tile. Ambos os caminhos agora convertem `base_tile * 32 + offset_bytes`.

ROM validada: SHA `b5d5db7b6295e8c6947b0125f0d4ef468fc179fb4e4d72215b5b5573227fafc5`
(65.536 B). Evidências da mesma build em `out/evidence/t6_vblank_cpu_split_byte_addr*`:

- `measure_worst_frame.py`: PASS, 3.000 frames selados, `vovf_delta=0`,
  `vline_min=200 (0xC8)`. O perfil por etapa é inválido porque só guarda um
  frame com derrame; a medição não alega uma distribuição sem amostras.
- `measure_frame_advance.py`: PASS em 60 s, 27 estados completos, 59,9 fps,
  zero durações fora da tolerância; `measure_fps.py`: 6/6 a 59,9 quadros/s.
- `measure_runtime_probe.py`: PASS em duas janelas de 8 s (59,29 e 59,43 fps);
  input vivo: cinco eixos PASS na RAM, incluindo hit B1 e padrões.
- Captura do boot e `screenshot_semantic_gate.py`: PASS; paleta 100%, sem
  assinatura de lixo de VRAM. `audit_deterministic_boot.py`: 2/2 idênticos.

O recorte provado continua sendo fixture sintético de bancada. Isso fecha o
budget do loop atual, mas não declara entrega visual do Ken real nem áudio.

**Atualização do checkpoint citado no resumo colado:** aquele estado foi
superado pela instrumentação ROM-sealed e pelas medições posteriores. Na build
atual Ken, o próprio `measure_worst_frame.py` selou 3.000 frames e PASS (`vovf_delta=0`,
`vline_min=201`; `out/evidence/t9_current_worst_frame.json`). Portanto as
opções (a/b/c) daquele checkpoint ficaram obsoletas; nenhum limiar ou ferramenta
central foi alterado.

**Files:**
- Modify: `SMS_projects/luta_mugen/src/stream.c`, `src/main.c`, `src/fight.c`
- Consumes: `SMS_VRAMmemcpy_brief` (SMSlib.h:394; endereço e tamanho em bytes),
  `SMS_mapROMBank`/`save/restore`
  (SMSlib.h:70-83), arte > 48 KB só com header SDSC/mapper correto (padrão
  MSSF2T spec-banking; verificar `sdk/README.md` antes).

- [x] **Step 1:** ROM bancária de 65.536 B, dados no slot 2 e código fixo; mapa
  de bank trocado no bloco VBlank depois de `SMS_waitForVBlank()`. Upload lê
  diretamente da janela ROM e restaura o bank no mesmo escopo.
- [x] **Step 2:** buffers duplos por lutador e até 96 B/lutador por VBlank.
  Pedido em N → upload a partir de N+1 → buffer completo alternado; metasprite
  preparado em CPU e apresentado pela SAT no próximo VBlank. Se uma pose exigir
  mais de um chunk, a apresentação espera a carga completa.
- [x] **Step 3:** `measure_worst_frame.py` PASS sem derrame na ROM SHA acima;
  frame advance, fps, runtime probe, input vivo e boot determinístico também
  medidos. A captura inicial com unidade de destino errada foi renomeada como
  rejeitada e não sustenta nenhum claim.

O commit sugerido no plano não foi criado: o workspace já contém outras
alterações locais extensas e a sessão não autorizou stage/commit.

---

### Task 7: Cena 02 `ken_vs_dummy` — base implementada; estado atual em T10

**Estado medido (2026-09-26): T10 integra os cortes Ken e Ryu; fechamento parcial.**
A ROM SHA `af9eb127…dc97` contém Ken P1 e Ryu P2 em bancos distintos. Input,
cadência do loop, FPS do emulador, pior quadro, áudio, semântica e vínculo dos
assets têm evidência PASS ou parcial específica da SHA atual. O DAP 2×120 s
passou (58,10/59,78 FPS, spread 1,68); a execução 2×240 s quebrou o canal DAP
antes da segunda janela e ficou como diagnóstico.
A captura continua época `probe`; KO/reset,
partida longa e promoção visual permanecem abertos.

**Files:**
- Create: `SMS_projects/luta_mugen/src/hud.c`, `src/sfx.c` + reautoría de áudio em
  `SMS_projects/luta_mugen/res/audio/*.psg` (6 SFX + 1 BGM — zero PCM; manifest de
  áudio com sha256 → `audit_audio_provenance.py`)
- Modify: `main.c` (loop da cena 02)

- [x] **Step 1 (parcial de escopo):** P2 usa perfil/corte Ryu (32 poses, banks
  5–6) com dummy determinístico simples, sem IA avançada (GDD). A ROM inclui Ken
  P1 (44 poses, banks 2–4). O PASS range-synced de input/dano está em
  `out/evidence/t10_input_memory_range_sync_pass.json`: gap 16 medido com o jogo
  pausado antes do B1, vida 152→102. O whiff anterior após B1 chegar permanece
  em `out/evidence/t10_input_memory_idle_wait_retry_whiff.json` como diagnóstico;
  helper agora reamostra o alcance após IDLE. As combinações de poses atingíveis passaram o simulador em
  `out/evidence/t10_ken_ryu_line_sim.json`.
- [ ] **Step 2 (implementado; KO/reset sem prova dedicada):** Vida = barra de tiles na BG (24×2, `SMS_setTileatXY` no VBlank);
  KO por vida 0 → pose KO (hitstop final), round reinicia; `PSGPlay(bgm)` +
  `PSGFrame()` no loop, `PSGSFXPlay(sfx, SFX_CHANNELS2AND3)` nos golpes.
  O screenshot confirma o HUD e a captura isolada/audits confirmam sinal PSG;
  falta observar KO, reinício do round e partida mais longa.
- [x] **Step 3 (parcial):** Gates da cena: boot determinístico, input, fps (`measure_fps.py`
  ≥5 amostras 50–60) E frame advance, `audit_psg_channel_binding`, `audit_psg_quality`,
  `reconcile_claims.py`, `audit_claims.py`, doc-sync, learning capture e gates estáticos têm resultados T10.
  DAP 2×120 s PASS (58,10/59,78 FPS,
  spread 1,68); 2×240 s falhou como rota diagnóstica. Só os resultados T9
  pertencem ao relatório antigo. Bundle T10 com 38 artefatos está selado.
  KO/round reset e
  gameplay longo continuam sem prova dedicada. Commit não criado por
  escopo/autorização; memory bank atualizado.

---

### Task 8: Cena 03 `golden_slice` + PROVA DO CONTRATO + fechamento de claims

T10 integra Ken e Ryu simultaneamente em `out/rom/luta_mugen.sms`: Ken ocupa
banks 2–4 e Ryu banks 5–6, com perfis de animação, CLSN e física próprios.
P2 continua dummy. A prova antiga `out/evidence/t9_ryu_def_switch.json` só
documenta substituição no build; a composição T10 não prova ainda a troca de
`.def` sem alterar C do núcleo.

Preparação de dados (2026-09-26): cortes regenerados em
`out/local_study/generated/versus_cut/`; Ken 44 poses nos banks 2–4 e Ryu 32
poses nos banks 5–6. Os arquivos derivados estão fora do Git; o manifesto
`.mddev/project.json` aponta para os cinco banks.

- [ ] **Step 1 (parcial):** completar melhor-de-3 com timer em tiles, 1 especial por lutador
  (QCB+1 remapeado, Task 5); segundo lutador trocado **apenas por `.def`** no build
  local (prova do contrato do GDD: nenhum `.c` do núcleo muda — documentar os dois
  builds e os SHAs). Ken QCF+B1 está provado; especial de Ryu, ciclo de rounds e
  substituição data-only na composição atual ainda não.
- [ ] **Step 2:** Rodar TODOS os gates do AGENTS.md aplicáveis na cena pesada COM
  áudio; `reconcile_claims.py`, `audit_claims.py`, `audit_rom_asset_binding.py`;
  teto de claims: `protótipo jogável de engine de luta MUGEN→SMS dirigida por dados`.
- [ ] **Step 3:** `doc/10-memory-bank.md` com os 7 eixos e provas; `doc/13-spec-cenas.md`
  fechado; então superpowers:finishing-a-development-branch (perguntar antes de push).

---

## Requisitos de honestidade deste plano

1. Tasks 1–2 **não podem** declarar sucesso sem o `s4_generation_report.json` com
   `veredito: PASS` medido pelo gate do harness — o mesmo artefato que deu FAIL.
2. Nenhum claim de qualidade visual acima de `probe` até a Task 7; Ken só existe em
   round local gitignored.
3. Cada número novo em doc vem com o comando que o mediu (regra do spec-cenas).
4. Se a escala travada (~32×48 px) produzir silhueta ruim na cena 01 (Lição aberta 2
   do memory bank), isso é **achado medido reportado ao humano**, não ajuste
   silencioso de escala.
