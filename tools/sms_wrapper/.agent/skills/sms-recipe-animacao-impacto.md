# Receita — Animação de poses e leitura de impacto (L075)

Skill-receita do SMSForge. Molde vivo: **MSSF2T** (ROM `efd7162f…`) para poses
de luta + flip runtime; **kage_matsuri** (ROM `f02dfd3c…`) para ciclo de
slash com frames de fonte selecionada. É a camada visual da receita
`sms-recipe-combate-1v1.md`: o golpe conecta por lógica; aqui ele **é visto**.

Complementa (não substitui) `sms-sprite-animation.md` e
`sms-sprites-metasprite.md`.

**Alcance histórico:** demonstra ligação estado→pose→consequência. Os golpes
de um quadro deste molde não ensinam atuação corporal, aceleração ou fluidez;
para novas ações usar o procedimento gestual/temporal de `sms-sprite-animation.md`
e o checkpoint de `workflows/art-review.md`. Os números, orientação e código
abaixo são do molde, não defaults da fábrica ou evidência da build atual.

## 1. Contrato

- **Toda ação do GDD precisa de representação coerente.** No molde: 8 poses distintas
  (idle, walk, punch, special, hit, KO, crouch, jump). Nesse caso, `ST_JUMP`
  com folha de andar não representava a ação contratada; foi defeito corrigido
  (`poses.json` re-medido, JUMP com menor y=67). Igualdade de imagens por si
  só não classifica a semântica de outro contrato.
- **Convenção do molde:** folhas olham para a **esquerda**; o
  flip é **runtime** (bitrev + dx-mirror em `want_flip`/`apply_pose`). Folha
  autorizada na orientação contrária quebra a convenção e renderiza de
  costas (pago na v086: as 8 folhas do Guile espelhadas, tamanhos idênticos).
- **Upload de pose dentro do orçamento de VBlank:** stream de 96 B/frame, um
  lutador por vez (`STREAM_BYTES`; não mexer sem remedir fps). Troca de pose
  é o pico de custo — worst-frame **medido**, não afirmado.
- **Impacto do molde tem consequência visível:** `g_hitstop` (6 cheio / 3 chip)
  congela o tick, `g_shake` treme, pose `POSE_HIT`/`POSE_KO` assume a
  silhueta de dano. Escolher feedback conforme ação/GDD; shake e esses tempos
  não são obrigatórios nem prova de impacto convincente.
- **Física não depende de estado:** gravidade roda em qualquer estado
  (`airborne()` é altura, não `ST_JUMP` — L050); `separate()` ignora quem
  está no ar — por isso o pulo por cima cruza e o facing vira ao aterrissar
  (L053).

## 2. Exemplo mínimo

Mapeamento estado→pose→folha, reduzido (de `fight.c:431-462`):

```c
static void set_state(unsigned char who, unsigned int st) {
    unsigned char pose = POSE_IDLE;
    if (P[who].state == st && st != ST_HIT) return;  /* HIT re-dispara */
    P[who].state = st;
    P[who].hit_used = 0;
    switch (st) {
    case ST_WALK_F: case ST_WALK_B: pose = POSE_WALK; break;
    case ST_JUMP:   pose = POSE_JUMP; break;
    case ST_PUNCH:  pose = POSE_PUNCH; P[who].startup=4; P[who].active=4; ...
    case ST_HIT:    pose = POSE_HIT;  P[who].recovery = 12; break;
    case ST_KO:     pose = POSE_KO;   P[who].recovery = 60; break;
    ...
    }
    apply_pose(who);   /* request_pose(who, pose, want_flip(who)) */
}
```

Geração de variantes sem arte nova (molde): `tools/author_pose_variants.py`
remodela a **silhueta a partir das folhas próprias** do lutador — custo
medido: 2560 B. No kage, slash2/jump vieram de **fontes selecionadas do
acervo** (`anim_kage_slash2/f015.png`, `anim_kage_combo/f025.png`), com proof
16×32 gerado — zero tile novo de cena.

Esse registro é histórico: transformação mecânica não autoriza autoria de
pixels finais por código, nem substitui fonte/poses autorais aprovadas. Holds
e repetição da mesma imagem em elementos semânticos diferentes podem ser
intencionais; não impor uma imagem única por estado sem examinar o contrato.

## 3. Comando de reprodução

```bash
# poses: provar cada estado do GDD por memória (probe_pose) e medir frames
python3 SMS_projects/MSSF2T/tools/prove_poses.py \
    --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms

# pico de custo (troca de pose): worst-frame com contador WORD canônico (L061/L071)
python3 tools/sms_wrapper/measure_worst_frame.py \
    --project SMS_projects/MSSF2T --seconds 20

# vídeo nativo das poses em combate (atração CPU-vs-CPU)
python3 tools/sms_wrapper/capture_video.py --project SMS_projects/MSSF2T \
    --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms --seconds 45 \
    --out recipe_combate --frames 6

# gate de semântica da animação (frames reordenados/ação clonada/pivot oscilando)
# — o manifest é explícito (o --project sozinho não basta; validado a frio:
#    no hamoopig o gate pegou 'musgo_punch' clonando ordem de ryo_punch/idle/walk)
python3 tools/sms_wrapper/audit_animation_semantics.py \
    --manifest SMS_projects/<p>/doc/animation_semantics.json
```

## 4. Caso válido / caso inválido

**Válido:** pose lida em RAM durante o golpe (`probe_pose` 0x82 =
`POSE_PUNCH|facing`), queda de hp do alvo no mesmo intervalo, hitstop visto
em `probe_hitstop`, facing virando após troca de lado no ar (kage/MSSF2T:
`cruzou_no_ar=true`, `min_py` lido). No kage: combo→2 derrotas→torii em
`full_cycle_memory.json` — ciclo animado com consequência.

**Inválido** (cada um já foi defeito pago, com fixture/gate):
- `ST_JUMP` desenhando folha de andar / `ST_CROUCH` a de parado — pose
  mentirosa (o que esta receita existe para impedir).
- Chute reusando a folha do soco, soco ≈ idle — movimento não lê como golpe.
  **Caso observado a frio (25/09)**: no hamoopig o gate pegou `musgo_punch`
  clonando a ordem de frames de `ryo_punch`, `musgo_idle` e `musgo_walk`
  (`duplicate_action_under_new_name` ×3) — violação real, não fixture.
  **Dívida aberta no molde**: hoje cada golpe é UM frame estático
  (blocker 6 do memory bank MSSF2T); a receita cobre poses de estado, e a
  animação 2–4 frames/golho depende de banking — não claimar animação por
  movimento onde ela não existe.
- `probe_vovf` de 8 bits saturando em 255 — contagem perdida (L071, §56);
  contador é WORD e zera só no boot.
- Flip assado em folha duplicada no lugar do flip runtime — paga VRAM/ROM a
  mais e diverge da convenção.
- Gate de animação com frames reordenados ou ação clonada com outro nome —
  `audit_animation_semantics.py` reprova (L037, §42).

### Comparar os contatos de duas gravações

Para os recibos MFD1 do gravador de round e de seu replay contínuo, execute
da raiz da fábrica, com o SHA do binário ensaiado. O exemplo usa a b11-r2
preservada no acervo do Master of Fighters.

```sh
base=SMS_projects/master_of_fighters/out/diagnostics/repertoire_20261119
tool=tools/sms_wrapper/audit_duel_contacts.py
rtk proxy tools/sms_wrapper/run_host.sh python "$tool" --self-check
rtk proxy tools/sms_wrapper/run_host.sh python "$tool" \
  --rom-sha256 f76fe86f5b3d874a7317c7727f350aa8e750af7a1dba9d85b8d71722c3a126b7 \
  --stepped "$base/scene02-actions-qa6-b11-r2/6-round/round-completo.json" \
  --continuous "$base/scene02-actions-continuous6-b11-r2-v2/6-continuous/round-continuo.json"
```

O controle é o primeiro soco, pose 8 e vida de Alis 100→94. A reprodução
completa deve sair com código 1. No nono contato a ordem e o dano conferem,
mas no VDP 674 o probe indica pose pedida 46 e publicada 45. No contínuo,
consulte a imagem 552, tick 472, que registra 46/46. Use os hashes dos
recibos para cotejar a auditoria. A ferramenta lê identificadores publicados
e compara contatos com dano relatados por duas sessões ligadas à mesma ROM.
Guarda, whiff, integridade dos pixels de P0/P1, duração do hitstop, FPS e
determinismo por tick exigem observações próprias. Para hitstop, fixe o
evento inicial, o avanço dos relógios de input, lógica, apresentação e som,
e o primeiro comando que volta a produzir ação.

Confira ainda de onde o gravador tira cada ID. No Saque desta build,
`pose_used_for_contact=2` é a segunda exposição do golpe. O primeiro
desenho no repertório é 45, logo a exposição corresponde a 45 + 2 − 1 = 46.
Comparar diretamente 2 com 46 criaria um segundo defeito fictício. Há também
um perfil da Cena 02 sem repertório que copia o mesmo valor para pedida,
residente e apresentada. Para esse perfil, verificar a publicação exige
observar SAT/PNT e o framebuffer. Antes de reutilizar a receita em outra
build, conferir o produtor da sonda, o perfil compilado e a unidade do ID.

## 5. Vídeo nativo

`SMS_projects/MSSF2T/out/evidence/recipe_combate.mp4` (mesma captura da
receita de combate): f02 mostra os dois lutadores em poses de locomoção/
guarda distintas; f05 mostra `POSE_KO` (Guile caído) com banner — a silhueta
de dano existe na tela, não só no enum. Frames-chave:
`recipe_combate_f00..f05.png`.

`SMS_projects/kage_matsuri/out/evidence/recipe_combate.mp4`: Kage em pose de
caminhada (f02) e a cena com inimigos em poses idle/próximas (f05) — folhas
próprias por estado visíveis na captura nativa.

## 6. SHA da ROM

- MSSF2T: `efd7162f8c9f829b4826047d24ac2cfed5ab163e094520ee4ca1d00521892122`
- kage_matsuri: `f02dfd3c749ed546d4303e1938ebb41cbc08837e8c7bbd96fae08251772419f9`

Worst-frame selado contra `efd7162f…`: `worst_frame_m03.json` derramou com
honestidade (vovf_delta=181, vline_max=235) — a receita exige o **número**,
não a promessa. W06-kage: `worst_frame_cycle.json` vovf_delta=67,
vline_max=245.
