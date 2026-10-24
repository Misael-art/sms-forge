# Prompt — pose residente, composição legal, célula emitida

Você fecha o parecer registrado em 2026-10-23. O orçamento do par já está no GDD e em `decide_pose_scale`. A ROM do par já mostrou tinta dos dois lados. Este lote descobre por que o Ken não fecha, impede a ROM de exibir um par acima de 8 sprites na linha, e corrige a amostragem da sola do Ryu. Não redesenha golpe, não abre outra paleta, não troca o renderer para híbrido e não promove lei da fábrica.

Comece com `[Contexto SMS Carregado]`. Leia o `AGENTS.md` da raiz, `/home/misael/.codex/RTK.md`, `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` e os workflows `emulator-isolated-session.md` e `subagent-emulator-qa.md`. Prefixe comandos de shell com `rtk`. Não sobrescreva `.agent` local. Não faça commit nem push.

## Fontes, nesta ordem

Workspace: `/mnt/sdcard/Projects/SMSForge`.
Projeto: `SMS_projects/luta_mugem_rev2`.
Motor: `tools/sms_wrapper/mugen2sms`.

1. `doc/10-memory-bank.md`, seção `2026-10-23 — parecer da captura do par`.
2. `doc/11-gdd.md`, primeiro parágrafo. A condição viva é o par, não a porta de 70%.
3. `doc/28-pose-budget-8.md`. O bloco «Resultado medido» é o piloto da manhã. Não use a ação 440 como referência deste lote.
4. `doc/curation/2026-10-23_pose_budget_aguardando_curador.md`, pontos PB-13 a PB-18. O JSON de mesmo nome. Sem ID de lição.
5. `doc/29-prompt-pose-budget-cena-20261023.md`. Esse lote já rodou. Não o repita.
6. `src/main.c`, `sprites_build`, por volta da linha 996. Os dois ramos estão no fonte.
7. `out/logs/pose_budget_pair_20261023/line_summary.json`.
8. As duas capturas em `out/evidence/`.

Reconfira SHA e tamanho antes de editar. Se um binário divergir do bloco abaixo, pare e registre o valor lido. Não apague nem substitua nenhum deles.

```text
Produção, intacta, data 2026-10-20:
  out/rom/luta_mugem_rev2.sms
  851968 bytes
  SHA-256 087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65
  49 banks, escala 40/49

Piloto da manhã:
  out/rom/pose_budget_20261023.sms
  458752 bytes
  SHA-256 9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba

Paleta reservada, recusada pelo dono, sem captura:
  out/rom/palette_reserve_20261023.sms
  458752 bytes
  SHA-256 f9ef0e27eef5e29d530b0fa4e5c8325bd8df84a1ab6e7d93e77873f40a2b76cb

Par e paleta de brilho, os mesmos bytes:
  out/rom/pose_budget_pair_20261023.sms
  out/rom/palette_luma_20261023.sms
  458752 bytes
  SHA-256 6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873
  24 banks
  corte out/generated/pose_budget_pair_20261023/
```

`src/main.c` e `.mddev/project.json` vivos apontam `out/generated/ryu_ken_cross`. Não os aponte para o piloto. Compilar o projeto vivo recria a ROM `087df676…`. Não faça isso no lugar dela. Build de prova continua em cópia temporária dos 24 banks, com ROM de saída nova só se os bytes mudarem.

A chave `p1_ken` é o corte do Ryu. A chave `p2_ryu` é o corte do Ken. Na captura, o Ryu legível está à esquerda e o Ken partido à direita.

## O que já está decidido

Idle de boot: 32×56, 4 colunas, 16 células. Maior célula neutra: 32×64. Fração do par: framebuffer 2/3 × 6/7, extra 2/3, porta `idle_to_4`. Não aplique outra escala. Não encolha o idle para fabricar 5+3.

As duas capturas 256×192 têm a mesma ocupação. Diff de 14 pixels, todos no Ken, de `(170,0,0)` para `(170,85,85)`.

| Lado | Ocupação |
|---|---|
| Ryu | x 70–99, 30 px, y 108–160, idle legível |
| Ken | x 118–121 (4 px), vão, x 126–141 (16 px), vão, x 146–149 (4 px). Vão total 32 px |

Livro de cor: as 7 mais frequentes. Preto opaco fica de fora. Não abra uma terceira paleta. `palette_reserve` permanece recusada.

FX acima de 3 colunas já saiu do corte e não vai para o fundo. Não o traga de volta.

`POSE_NEAR` 0,69 não abre nem fecha escala. `framebuffer`, `fighter_scale` (72–88) e `legacy_quarter` (1:4) continuam selecionáveis.

## Ordem de trabalho

### 1. Quadro com as duas poses residentes

Abra `pose_budget_pair_20261023.sms` numa sessão privada, uma janela, cleanup no fim. A captura é o framebuffer 256×192. `audit_deterministic_boot` com frame preto e `Update=0` não é boot.

Antes de interpretar a listra, leia com qual ramo esta ROM foi ligada. Em `sprites_build`:

- `LUTA_PROFILE` emite a pose residente mesmo quando a pedida ainda é outra. A espera fica nas sondas.
- O ramo de diagnóstico só chama `emit_frame` quando `pose_global == poses_req`. Enquanto diferem, o ator inteiro sai.

Uma listra não é o ramo de diagnóstico: esse ramo omite o ator, não desenha metade. Registre o ramo que o binário `6fb424a3…` realmente usou. Não troque o perfil de produção para o gate de diagnóstico.

O quadro vale quando as duas poses pedidas já estão residentes, ou quando a sessão já passou frames suficientes para um idle de 16 células terminar o upload e a pose não foi trocada no meio. Grave o número do frame. Se a ROM não tem sonda de residente/pedida, ou se `measure_worst_frame.py` em `0xC800` continuar `sem_lastro` (`done` 0), não invente o schema. Diga isso e use o frame longo da sessão.

No quadro válido, conte as entradas da SAT de cada lado e compare com as 16 células do idle.

- Menos células do que o idle declara: o que está na tela é submissão ou upload incompleto. A prova é a contagem, não a aparência.
- As 16 células presentes e o Ken ainda partido: o defeito é conteúdo ou ordem do tile do P2. Aí, e só aí, corrija essa ordem no corte do piloto. Não mude o livro de cor.

Se o Ken fechar nesse quadro, a captura anterior era pose incompleta. Guarde o PNG novo. Não altere tile nem paleta para “melhorar” um corpo que já fechou.

Não chame o resultado de entrega visual.

### 2. Medir as composições que a ROM pode mostrar

Rode `audit_sprite_line_sim.py --self-check` antes de ler qualquer número. Conte célula emitida, com transparente omitido, modo tall, os dois lutadores no mesmo Y. Canvas/8 não aprova. Lutador contra ele mesmo não é luta.

Meça estes pares e grave pico e violações:

- idle de cada um contra idle do outro. Referência já medida: pico 8, 32 sprites.
- Ken punch 250, hp 450, kick 200, hk 220, special 1000 e ko 5080, cada um contra o idle do Ryu.
- Ryu punch 260, hp 280, kick 200 e hk 240, cada um contra o idle do Ken.

Pico acima de 8 reprova essa composição. `included_pair: false` no JSON antigo não é aprovação. O special 1000 do Ryu e o ko 170 do Ryu já cabem em 4 colunas; não os use no lugar dos golpes largos do Ken.

### 3. A composição exibida tem de ser legal

O idle permanece em 4 colunas. Um golpe de 5 a 8 contra esse idle soma 9 a 12. A regra 5+3 só existe quando um lado emite no máximo 5 e o outro no máximo 3 nas linhas compartilhadas, os dois sendo lutadores diferentes, com o simulador dizendo pico ≤ 8.

Para cada papel que o link ainda exige:

- Se o par com o parceiro que a cena mostra fica em pico ≤ 8, ele pode ser exibido.
- Se passa de 8, a cena de prova não o submete junto do outro lutador. Os dados do papel podem permanecer para o link. O relatório marca `dropped_from_composition` com o pico medido.
- Não encolha o idle. Não reautora pixel. Não desenhe cota 5/3 à mão em `main.c`. Não omita coluna no chute para forçar a soma: omissão de coluna é outro desenho e fica fora deste lote.

`case_by_case` num relatório, com o sprite ainda submetido, não cumpre este passo.

### 4. Sola do Ryu

No idle do Ryu a hurtbox passa 2 px da sola porque a linha de baixo não foi amostrada. O padding duplo não foi a causa: Ken idle e Ken punch estão em delta 0, e o soco do Ryu move 1 px pelo pad.

Corrija a amostragem para a linha da sola entrar. Meça de novo idle e soco dos dois, eixo contra a sola opaca e hurt contra o corpo. Se a correção mover a sola do Ken mais de 1 px, pare e registre. Não invente hitbox nova. Não altere o sampler se a nova medida não trouxer a hurt do Ryu de volta à sola.

### 5. Pior quadro, só com o Ken fechado

`measure_worst_frame.py` roda somente depois do passo 1 mostrar o Ken com o corpo fechado. Se ele continuar partido, o pior quadro não roda e o relatório diz isso. Se a sonda não casar com o schema da ferramenta, o resultado continua `sem_lastro`. `validado_budget` fica proibido. 24 banks não são FPS.

## ROM de saída

Se o passo 1 não mudar bytes e a cena de prova ainda for `6fb424a3…`, não crie ROM duplicada. O artefato novo é o PNG do quadro residente, com o número do frame.

Se o corte, o agendamento ou o sampler mudarem bytes, grave `out/rom/pose_budget_settled_20261023.sms`. Não sobrescreva as quatro ROMs do bloco. Não aponte `project.json` para ela.

## Fora deste lote

- `SMS_GLOBAL.md`, `learning_ledger.json`, `id_registry.json`, `lesson_routes.json`. Nenhum ID de lição.
- Terceira paleta. Reserva de preto e branco. Preencher os 26 e 44 pixels transparentes da amostragem.
- Híbrido corpo-no-BG. Flicker como política. Cota 5/3 escrita à mão.
- Reautoria de pose. Segunda escala extra. Trazer o FX de volta ao corte ou desenhá-lo no fundo.
- Substituir `087df676…`.
- Claim de 60 fps, áudio, gameplay ou entrega visual.
- Apagar a faixa 72–88 ou o 1:4.

## Definição de pronto

Relatório curto com: SHA das ROMs lidas e, se houver, da ROM nova; ramo de `sprites_build` que o binário `6fb424a3…` usa; frame e caminho do PNG residente; contagem de SAT contra as 16 células; veredito do Ken separado por essa contagem; tabela dos dez pares golpe-contra-idle com pico; lista `dropped_from_composition`; delta de sola e hurt nos quatro quadros; resultado do pior quadro ou o motivo de não ter rodado.

Atualize `doc/10-memory-bank.md` com esses números. Status permitido: `testado_em_emulador` só com o PNG do quadro residente. Entrega visual continua fechada enquanto o Ken não for um corpo legível. `validado_budget` continua proibido.
