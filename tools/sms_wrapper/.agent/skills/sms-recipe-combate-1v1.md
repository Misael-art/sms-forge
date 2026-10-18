# Receita — Combate 1v1 com resolução determinística (L074)

Skill-receita do SMSForge. Molde vivo: **MSSF2T** (`src/fight.c`, 1149 linhas,
ROM `efd7162f…`). Segunda validação: **kage_matsuri** (combo→derrotas→torii,
ROM `f02dfd3c…`). Validação a frio (passo 4, 25/09): **hamoopig** — engine
1v1 escrita independente do molde; as seis cláusulas mapearam a código próprio
sem ajuda (`MoveDef` soco 4/4/8 dano 7, chute 6/4/10 dano 10, projétil
10/4/18 dano 12 em `src/fighter.c:5-9`; fila de eventos com trade em
`combat.c`). É a receita que fecha o contrato de um laço de golpe que
conecta, faz dano atribuível e decide round sem depender de ordem P0/P1.

Ela **não** substitui `sms-fight-input-proof.md` (prova de golpe contra IA,
L060) — ela é o motor que aquela prova mede.

## 1. Contrato

Dado um lutador em `ST_PUNCH`/`ST_KICK`/`ST_SPECIAL`, a engine deve:

- **Janela de frame explícita** por golpe: `startup`, `active`, `recovery`
  (no molde: soco 4/4/8, chute 7/5/13, especial 8/4/12 — `set_state`,
  fight.c:445-457). O golpe só tem hitbox entre `[startup, startup+active)`.
- **Um golpe, um acerto**: `hit_used` trava o contato após conectar
  (fight.c:758) — sem multi-hit involuntário por frame.
- **Dano atribuível por movimento**: soco 7, chute 10, projétil 12, chip de
  guarda 2 (fight.c:708-712, 677). A prova lê a queda exata de `hp`.
- **Guarda posicional**: só vale se o defensor segura trás **e** o golpe vem
  da frente **e** ele não está no ar (fight.c:673-676). Bloqueio pelas costas
  é defeito, não recurso.
- **Snapshot antes do veredito**: todos os contatos são coletados em
  `contact_mask` e resolvidos de uma vez (fight.c:703-724) — trade e dupla
  KO não dependem da ordem de iteração P0/P1.
- **Impacto sentido**: `g_hitstop` 6 (cheio) / 3 (chip) congela o tick
  (fight.c:1041) e `g_shake` treme a tela — o golpe precisa *parecer* golpe.

Pré-condições: probe SMRT canônico na RAM (`probe_gap` 0xC7E?, `probe_pose`,
`probe_keys`, `probe_hp`) — sem ele a prova é pixel, e pixel não sobrevive a
este host (L035/L038).

## 2. Exemplo mínimo

A caixa de colisão melee, reduzida ao osso (de `fight.c:741-760`):

```c
if (P[a].state != ST_PUNCH && P[a].state != ST_KICK) continue;
if (P[a].hit_used) continue;                       /* um golpe, um acerto */
if (P[a].timer < P[a].startup) continue;           /* ainda em startup    */
if (P[a].timer >= P[a].startup + P[a].active) continue;  /* janela passou */
/* soco = caixa alta, chute = caixa baixa: dá sentido a agachar */
if (P[a].state == ST_PUNCH) { ay0 = P[a].y + 18; ay1 = P[a].y + 32; }
else                        { ay0 = P[a].y + 40; ay1 = P[a].y + 58; }
ax = P[a].facing ? P[a].x + 20 : P[a].x - 4;        /* borda frontal */
bx = P[b].x + 8; by0 = P[b].y + hurt_top(b); by1 = P[b].y + 60;
if (ax < bx + 16 && ax + 12 > bx && ay0 < by1 && ay1 > by0) {
    P[a].hit_used = 1;
    record_contact(a);                              /* só coleta; aplica depois */
}
```

E a resolução com guarda (de `fight.c:669-693`): `from_front` + `guard` +
`!airborne` ⇒ chip 2 e hitstop 3; senão dano cheio, hitstop 6, shake,
`set_state(def, ST_HIT)`.

## 3. Comando de reprodução

```bash
# build canônico (roda os pré-gates; nunca --skip-pre-gates em entrega)
python3 tools/sms_wrapper/build_inner.py --project SMS_projects/MSSF2T

# prova de golpe por RAM: aproxima, B1, lê queda exata de guile_hp
python3 SMS_projects/MSSF2T/tools/prove_input_memory.py \
    --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms

# vídeo nativo do laço (atração CPU-vs-CPU mostra hits/hitstop/KO sem canal de input)
python3 tools/sms_wrapper/capture_video.py \
    --project SMS_projects/MSSF2T \
    --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms \
    --seconds 45 --out recipe_combate --frames 6
```

## 4. Caso válido / caso inválido

**Válido** (o que a ROM `efd7162f…` entrega, selado em `input_memory.json`):
canal vivo + `gap < 24` lido antes do golpe + `guile_hp 64→57` (delta 7 =
soco cheio sem guarda) + pose 0x82 (`POSE_PUNCH|facing`) + `hit_used=1`.
Whiff-honesto na 1ª tentativa (B1 não chegou no 1º toque) é **válido** — o
retry é do instrumento, e a falha fica no log (L060).

**Inválido** (reprovado pelos gates, fixtures no `--self-check`):
- `probe_keys` nunca latches 0x10 → canal morto (L039) — `emulator_input.py` reprove.
- `guile_hp 64→64` com pose de punch vista → **whiff**, não conexão; a
  atribuição exige queda de hp.
- Bloqueio com `hp` caindo dano cheio → guarda não estava `from_front`.
- `dx` do blob andou para o lado oposto ao comandado e o gate deu PASS por
  `abs(dx)` → regressão L038, o critério é dx **na direção** comandada.
- Trade/duplo-KO decidido por ordem de iteração → snapshot ausente.

## 5. Vídeo nativo

`SMS_projects/MSSF2T/out/evidence/recipe_combate.mp4` — 256×192 h264, 46,3 s,
movimento 76,4%, 6/6 frames informativos. Frame f02: Ken vs Guile em combate
(HUD, timer 90, ambos de pé). Frame f05: banner **"KEN WINS"** com Guile
caído (pose `POSE_KO`) — laço completo golpe→dano→KO observado no framebuffer
do emulador, sem screenshot estático. Bundle: `recipe_combate.json`.

Segundo projeto (validação da receita fora do molde):
`SMS_projects/kage_matsuri/out/evidence/recipe_combate.mp4` — cena viva com
roteiro de input (`Right/a/Left/Up`), Kage anda, samurais convergem, pips de
vida mudam. O **golpe** no kage é provado por RAM em
`full_cycle_memory.json` (`ciclo_provado`, `attack_attempts`), não por pixel.

## 6. SHA da ROM

- MSSF2T: `efd7162f8c9f829b4826047d24ac2cfed5ab163e094520ee4ca1d00521892122`
  (32768 B) — vídeo e `input_memory.json` selados contra esta SHA.
- kage_matsuri: `f02dfd3c749ed546d4303e1938ebb41cbc08837e8c7bbd96fae08251772419f9`
  (16384 B) — `full_cycle_memory.json` e vídeo contra esta SHA.

A SHA é invariante de fonte (SDSC pinado, L065): rebuild não derruba o selo.
Qualquer evidência desta receita produzida contra outra SHA é inferência de
outro binário — não vale (memória: "Quais evidências valem para esta SHA").
