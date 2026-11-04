# Prompt — pose budget da cena, não de um lutador

Você implementa um lote fechado no `luta_mugem_rev2`. O default `pose_budget` já existe e compilou. Este lote corrige o critério de tamanho para dois lutadores em sprite puro, faz os rótulos dizerem a fração que rodou, e só então mede a ROM nova no emulador. Não redesenha golpe, não troca o renderer para híbrido BG e não promove lei da fábrica.

Comece com `[Contexto SMS Carregado]`. Leia o `AGENTS.md` da raiz, `/home/misael/.codex/RTK.md`, `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` e os workflows `emulator-isolated-session.md` e `subagent-emulator-qa.md`. Prefixe comandos de shell com `rtk`. Não sobrescreva `.agent` local. Não faça commit nem push.

## Fontes, nesta ordem

Workspace: `/mnt/sdcard/Projects/SMSForge`.
Projeto: `SMS_projects/luta_mugem_rev2`.
Motor: `tools/sms_wrapper/mugen2sms`.

1. `doc/10-memory-bank.md`, seção `2026-10-23 — pose_budget`.
2. `doc/11-gdd.md`, primeiro parágrafo. `doc/13-spec-cenas.md`. `doc/15-tdd.md`.
3. `doc/28-pose-budget-8.md`.
4. `doc/curation/2026-10-23_pose_budget_aguardando_curador.md` na raiz do SMSForge, pontos PB-08, PB-09 e PB-11.
5. `doc/display_profile.json` e `doc/continuity/config/ken_pose_budget.json`, `ryu_pose_budget.json`.
6. `tools/sms_wrapper/mugen2sms/converters/display_fit.py`.
7. `generators/scene_cut.py` (`_prepare_pose_budget`) e `generators/smsdev.py` (`_worst_scene`).
8. `analysis/fidelity.py`, motivo `downscale1:4`.
9. `converters/sms_scale.py`, `needs_scale`.

Reconfira SHA e tamanho dos dois binários antes de editar. Se divergirem do bloco abaixo, pare e registre o valor lido. Não apague nem substitua a ROM anterior.

```text
ROM anterior, intacta:
  SMS_projects/luta_mugem_rev2/out/rom/luta_mugem_rev2.sms
  851968 bytes
  SHA-256 087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65
  data de arquivo 2026-10-20
  escala 40/49, 49 banks

Piloto pose_budget já compilado, não é entrega:
  SMS_projects/luta_mugem_rev2/out/rom/pose_budget_20261023.sms
  458752 bytes
  SHA-256 9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba
  24 banks
  captura de janela saiu preta; status = buildado
```

`src/main.c` e `.mddev/project.json` vivos apontam o corte antigo de 49 banks. Não os edite para apontar o piloto. Build do piloto continua em cópia temporária, com ROM de saída nova. Compilar o projeto vivo recria a ROM `087df676…`; não faça isso no lugar dela.

Configs `ken_pilot_diag.json` e `ryu_pilot_diag.json` ficam como estão. `framebuffer`, `fighter_scale` (72–88 px) e `legacy_quarter` (1:4) continuam selecionáveis.

## O que este lote corrige

O piloto atual leva a pose de corpo mais larga a 64 px, 8 colunas. Isso é o teto de um lutador. A cena tem dois. Idle contra idle fica em 4+4 e cabe justo. O KO do Ken no corte chega a 64×32 e, nessa linha, o outro lutador fica com zero sprites. O GDD pede composição sem omissão. O lote v043 só passou a silhueta com cota 5+3.

A altura de idle deste piloto (cerca de 32×56 a 32×64) já está na faixa do Masters of Combat. Não encolha o corpo de novo para caber o golpe largo. O golpe que não cabe no par sai da escala uniforme e fica na lista caso a caso.

## Ordem de trabalho

### 1. Ver o piloto que já existe, antes de mudar a fração

Abra `pose_budget_20261023.sms` numa sessão privada de emulador, uma janela, cleanup no fim. A captura tem de ser o framebuffer 256×192, não a janela do desktop por nome. `audit_deterministic_boot` com frame preto e `Update=0` não é boot.

Se os dois idles aparecerem, guarde PNG, SHA da ROM e da imagem, e siga. Se o miolo continuar preto, ache a causa no log da sessão e no init da cópia que linkou os 24 banks. Só altere runtime se a ROM em si não emite sprite. Não chame essa captura de entrega.

### 2. Trocar a unidade do orçamento

Em `display_fit.py`, o default continua `pose_budget`, com origem obrigatória. A decisão deixa de ser “cerca de 70% das ações soltas já têm 8 colunas, então a mais larga vai a 64 px”.

A decisão passa a ser o par na scanline:

- Pose neutra de cada lado: no máximo 4 colunas de 8 px (32 px de célula emitida). Dois idles fecham em 8.
- Golpe largo contra uma pose neutra: no máximo 5 colunas de um lado e 3 do outro.
- Pose de corpo acima disso não puxa a fração do elenco. Entra em `case_by_case` para corte ou redesenho posterior. Este lote não reautora pixel.
- A escala extra, quando existir, é uma fração única para o corpo inteiro, escolhida para o idle emitido cair em 4 colunas sem reduzir quem já está dentro. Se o idle já está em 4, a extra do corpo fica 1/1 e só a lista caso a caso registra os largos.
- Apague o uso de `POSE_NEAR = 0.69` como porta. Esse número existe para 107/154 do Ryu passar. Não é lei de hardware. Pode permanecer como medida informativa no relatório, com o nome `within_8_ratio`, sem abrir nem fechar escala.

Conte a célula que a SAT realmente recebe. `measure_body_poses` hoje usa a largura padded do canvas. Célula 8×16 toda transparente, omitida por `omit_blank_cells`, não entra. O pico é por scanline, no modo tall 8×16, nos dois lutadores no mesmo Y de combate. Rode `audit_sprite_line_sim.py` com `--self-check` antes de ler o resultado. Canvas/8 sozinho não aprova.

Grupo 9000 continua fora da referência. Não emita esse retrato (120×140) como sprite de luta.

### 3. Efeitos

Mantenha `fx_groups` explícito no `display_profile.json`. Não infira FX por “grupo ≥ 8000”: os FX 1001 e 1002 do Ken se perdem, e o 9010 do Ryu é misto.

Depois da fração do corpo, efeito que passe de 3 colunas não entra no corte da ROM piloto. O `g8400` do Ryu, 112×24 e 14 colunas no piloto atual, fica de fora com motivo registrado. Não o desenhe no plano de fundo neste lote. Não deixe um FX largo escolher a escala do lutador.

### 4. Rótulos que hoje mentem

Quando `size_policy` é `pose_budget` e o personagem já veio `pre_scaled`:

- `analysis/fidelity.py` não grava motivo `downscale1:4`. O motivo nomeia as frações reais: framebuffer `x=2/3 y=6/7` e a extra do corpo, ou `1/1` se não houve extra.
- `smsdev._worst_scene` não divide de novo por 4. O pico usa o tamanho já convertido.
- No manifesto do corte, `ratio.numerator/denominator` não fica sozinho como se fosse a escala 40/49. `framebuffer_x`, `framebuffer_y` e `pose_extra` seguem ao lado, e o texto do relatório diz qual fração gerou o pixel.

Atualize o teste que hoje exige `motivo == "downscale1:4"` só no caminho `legacy_quarter` / `needs_scale` histórico. O caminho `pose_budget` ganha asserção própria.

### 5. Eixo e caixas

A contagem de CLSN preservada não prova posição. Num idle e num golpe de cada lutador, meça eixo contra a sola opaca e a caixa hurt contra o corpo, antes e depois do padding duplo de 8 px. Se o deslocamento passar de 1 px, corrija o padding para não andar o eixo em relação ao pixel. Não invente hitbox nova.

### 6. ROM nova e medidas

Gere outra ROM, `out/rom/pose_budget_pair_20261023.sms`. Não sobrescreva `luta_mugem_rev2.sms` nem `pose_budget_20261023.sms`.

No fechamento, nesta ordem, cada ferramenta com `--self-check` quando ela tiver:

1. Testes `test_display_fit.py`, `test_sms_scale.py`, `test_scene_cut_scale_order.py`, `test_cli_sms.py`, mais o teste novo do motivo de fidelidade.
2. `audit_sprite_line_sim.py` no par idle/idle, idle/golpe e golpe/golpe das poses incluídas. Registre pico e quem estoura 8. Estouro nas poses incluídas reprova o lote.
3. Framebuffer 256×192 da ROM nova, sessão privada, dois idles visíveis. PNG com SHA da ROM no relatório.
4. Só se o passo 3 mostrar os dois lutadores: `measure_worst_frame.py` sem DAP, dois atores, fundo sólido. Menos banks não é FPS. Se o passo 3 falhar, o pior frame não roda e o relatório diz isso.

## Fora deste lote

- `SMS_GLOBAL.md`, `learning_ledger.json`, `id_registry.json`, `lesson_routes.json`. Nenhum ID de lição.
- Híbrido corpo-no-BG. Cota 5/3 desenhada à mão no `main.c`. Flicker como política.
- Reautoria das poses em `case_by_case`.
- Substituir a ROM `087df676…` ou apontar o `project.json` vivo para o piloto.
- Claim de 60 fps, áudio, gameplay ou entrega visual.
- Apagar a faixa 72–88 ou o perfil 1:4.

## Definição de pronto

Entregue um relatório curto com: SHA e bytes das três ROMs, fração aplicada, pico do simulador de linha nos três pares, delta de eixo/caixa nos quatro quadros medidos, caminho do PNG 256×192, e o que ficou em `case_by_case` e fora do corte por ser FX. Atualize `doc/10-memory-bank.md`, `doc/11-gdd.md` e `doc/28-pose-budget-8.md` para a regra do par. Status permitido: `buildado` se a tela não mostrou os dois; `testado_em_emulador` só com o PNG do framebuffer. `validado_budget` fica proibido neste lote.
