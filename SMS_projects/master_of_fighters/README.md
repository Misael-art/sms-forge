# Master of Fighters

> **Dr. Social in-game congelado pelo proprietário em 04/11/2026.**
> Leia [o registro vigente](doc/dr_social_ingame_freeze_20261104.md) antes de atuar.
> Model sheet/referências de tamanho e cena experimental preservados; J.J. e
> Hayato/Kenseiden seguem validados no recorte já realizado.

Jogo de luta autoral em desenvolvimento. O manifesto padrão compila o
esqueleto. Os manifestos de viewer são diagnósticos de arte e animação.

## Jogar na pista com o novo horizonte de Palma

Abra [a ROM do Espaçoporto com o guarda e as nuvens](out/candidates/alis_palma_horizonte_r3/rom/master_of_fighters.sms). No título, pressione **1** e escolha **História de Alis** ou **Versus local**. Na pista, deixe os controles em repouso para ver o vento nas nuvens. Caminhe com os dois lutadores para o mesmo lado para ver o deslocamento relativo do céu, das naves e do piso.

A pista foi conferida no Emulicious. As duas cargas de 3.000 apresentações encerraram com zero estouros de VBlank. A janela mais lenta dos especiais ficou em 33,46 FPS, abaixo do piso de 58. [Ver a pista em movimento](out/qa/alis_palma_horizonte_r3/cenario/nuvens.mp4) · [Medições da ROM](doc/decisions/2026-11-27_palma_horizonte.json)

## Jogar a apresentação Alis × Alis no Espaçoporto de Palma

Abra [a ROM do Versus com câmera e áudio FM](out/candidates/alis_versus_barlow_fm/rom/master_of_fighters.sms). Na abertura, o botão **1** entra no menu. Escolha **Versus local** para ver a apresentação antes da luta. **1** também permite avançá-la. Com Alis como P2 e a música ligada, toca *Battle*, do primeiro *Phantasy Star*. No Emulicious, habilite a unidade FM em **Options → Emulation → Master System** para ouvir o arranjo do YM2413. O hardware PSG toca a versão do mesmo tema para esse chip.

```sh
SMS_projects/master_of_fighters/run.sh SMS_projects/master_of_fighters/out/candidates/alis_versus_barlow_fm/rom/master_of_fighters.sms
```

A câmera, as duas paletas e o áudio foram conferidos no Emulicious. A menor janela de especiais foi de 34,455577 FPS, abaixo do piso de 58. [Ver o cartão em movimento](out/qa/alis_versus_barlow_fm/fm/versus.gif) · [Ouvir Battle em FM](out/qa/alis_versus_barlow_fm/fm/battle.wav) · [Medições da candidata](doc/decisions/2026-11-27_versus_palma_fm.json)

## Jogar os especiais de Alis e os Guardiões de Algol

Abra diretamente [Alis — Guardiões de Algol, candidata G6e](out/candidates/alis_guardioes_g6e/rom/master_of_fighters.sms) no **Emulicious (SMSForge)**. A ROM reúne os especiais na História e no Versus do Espaçoporto de Palma. Na opção **Vitórias por duelo → Uma**, o primeiro round já decide o confronto. Um teste rápido do arquivo é pressionar duas vezes para baixo, apertar **1** no segundo toque e soltar. Alis lança Fire.

No teclado, P1 usa as setas, **A** para o botão 1 e **S** para o botão 2. Para iniciar a candidata a partir da raiz do SMSForge, use o caminho explícito.

```sh
SMS_projects/master_of_fighters/run.sh SMS_projects/master_of_fighters/out/candidates/alis_guardioes_g6e/rom/master_of_fighters.sms
```

A G6e registrou zero estouros de VBlank nas duas cargas de 3.000 apresentações. A pior janela de especiais mediu 35,45 FPS, abaixo do piso de 58. [Medições por revisão](doc/decisions/2026-11-26_cadencia_g6.json)

[Comandos e custos](doc/padrao_moveset_especiais.md) · [Curadoria das peças e verificações](doc/curadoria_guardioes_de_algol.md).

## Jogar no Espaçoporto de Palma

Abra [Espacoporto_de_Palma.sms](out/candidates/espacoporto_de_palma_e2/Espacoporto_de_Palma.sms). No título, aperte **1**. Escolha **História de Alis** para enfrentar a CPU ou **Versus local** para dois controles. Na História, **1** avança cada fala e **2** pula a introdução. Os dois modos chegam à pista com as naves vermelhas e a torre azul. Esta é a candidata E2, com desempenho abaixo do piso de 58 FPS. [Captura da História](out/qa/alis_20261125/espacoporto_de_palma_e2/story/arena.png) · [Captura do Versus](out/qa/alis_20261125/espacoporto_de_palma_e2/port-versus/pista_oeste.png)

## Jogar o capítulo de Alis em Camineet

A [candidata com as casas e lojas redesenhadas](out/candidates/alis_capitulo_01_c5r/rom/master_of_fighters.sms) inicia no título. Use o direcional e o botão 1 para entrar. Nos diálogos, 1 avança e 2 pula. No menu, Opções ajusta a música e a quantidade de vitórias por duelo. História coloca a segunda Alis sob controle da CPU. Versus local usa as duas portas do Master System.

Na raiz do SMSForge, abra a candidata no Emulicious com o comando abaixo.

```sh
tools/sms_wrapper/run_host.sh rtk proxy SMS_projects/master_of_fighters/run.sh \
  SMS_projects/master_of_fighters/out/candidates/alis_capitulo_01_c5r/rom/master_of_fighters.sms
```

A candidata C5r tem 1 MiB e SHA-256 `2112971df3eb08339e93a2892a43fc38fd144b2df7c4a6134ec13640e20af9ea`. A história, o versus e os dois resultados foram exercitados. O desempenho ainda reprova o aceite de 58 FPS. [Troca de golpes](out/qa/alis_20261125/c5r-story/troca.mp4) · [Tema do título](out/qa/alis_20261125/c5r-story/tema_titulo.wav) · [PSG durante o combate](out/qa/alis_20261125/c5r-story/musica_e_golpes.wav)

P1 usa as setas e as teclas **A** e **S**. O botão 1 usa espada ou escudo, e o 2 usa chutes. Toque e segure produzem golpes diferentes. Para o especial, pressione baixo, depois frente + 1. Para a resposta de escudo, pressione baixo, depois trás + 1. Com a carga completa, pressione baixo, frente, baixo, frente + 1 para o Super. Frente e trás acompanham o lado do adversário. [Comandos dos dois jogadores](doc/scene02-comandos.md#perfil-alis--alis) · [Memória e evidências](doc/10-memory-bank.md)

## Jogar Alis × Alis

Abra a [candidata b53 do espelho](out/candidates/scene02_alis_mirror_b53/rom/master_of_fighters.sms)
com **Emulicious (SMSForge)**. A ROM abre no duelo local com dois controles. P1 veste
rosa e P2 veste verde. Cada lado tem os mesmos comandos para os doze
normais, as guardas e a Puxada com Escudo.
[Comandos dos dois controles](doc/scene02-comandos.md#perfil-alis--alis) ·
[Matriz e estado de aceite](doc/scene02_alis_espelho_qa.md).

Para jogar com o controle integrado do Steam Deck, abra a ROM pelo
lançador do projeto. **A** usa escudo e espada. **B** usa chutes. A intensidade
depende de tocar e soltar ou sustentar o botão. No teclado do P1, use
as setas, **A** para escudo e espada e **S** para chutes.

```sh
rtk proxy SMS_projects/master_of_fighters/run.sh \
  SMS_projects/master_of_fighters/out/candidates/scene02_alis_mirror_b53/rom/master_of_fighters.sms
```

## Comparação histórica com Hayato

Abra a [candidata b32](out/candidates/scene02_alis_jump_mix_b32/rom/master_of_fighters.sms)
no **Emulicious (SMSForge)**. No Steam Deck, o controle integrado usa P1.
Alis começa à esquerda e Hayato usa P2. Mova o direcional à esquerda para
recuar e à direita para avançar. Toque e solte **1** para o soco de guarda,
ou sustente **1** para a espadada. Alis transfere o peso a cada passo em
avanço e recuo. O escudo responde ao apoio e a espada gira em torno da mão.
Os dois golpes do botão 1 têm sons próprios de preparação e impacto.
Para Alis, **↓** abaixa, **↑** salta e **↑ + esquerda/direita** salta na
diagonal. **↑ + frente** perto de Hayato permite atravessar por cima e
pousar do outro lado. **Trás** defende em pé ou no ar e **↓ + trás** defende abaixada.
[Comandos do duelo](doc/scene02-comandos.md)

Também é possível abrir a candidata da raiz do SMSForge:

```sh
rtk proxy SMS_projects/master_of_fighters/run.sh \
  SMS_projects/master_of_fighters/out/candidates/scene02_alis_jump_mix_b32/rom/master_of_fighters.sms
```

## Reproduzir o viewer da provocação de Dr. Social

Execute da raiz do SMSForge com o ambiente do [guia de continuidade](../../doc/continuity/20261024-start-here.md).
Os scripts v2/v3 conferem os JPEGs locais pelos recibos de registro e só
recolocam derivados ausentes após verificar a reprodução. Se faltar um
original, recupere pelo Git o arquivo indicado pela receita.

```sh
project="$PWD/SMS_projects/master_of_fighters"
art="$project/data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1"
host=tools/sms_wrapper/run_host.sh
wrapper=tools/sms_wrapper
rtk proxy "$host" python "$art/register_taunt_cycle_v2.py"
rtk proxy "$host" python "$art/register_taunt_cycle_v3.py"

converted="$project/out/diagnostics/social_taunt01_cycle_v3_20261101/converted"
# Em uma restauração, gere somente se este destino estiver ausente.
rtk proxy "$host" python "$wrapper/prepare_authored_sprite_sample.py" \
  --config "$art/proposals/TA01_cycle_v3_adapter_config.json" --out "$converted"
rtk proxy sha256sum "$converted/sample_data.h"
```

O SHA-256 esperado do header é
`2613029ccaff5ef12ad578988660e42f35950134a7581465ecc11819eabaa008`.
Com o header conferido, escolha um destino novo para o build e abra a sessão.

```sh
candidate="$project/out/candidates/rebuild_social_taunt_v3"
rtk proxy "$host" python "$wrapper/build_inner.py" --project "$project" \
  --manifest "$project/.mddev/dr_social_taunt01_cycle_v3_build.json" --build-dir "$candidate"
rtk proxy "$host" python "$wrapper/emulator_session.py" isolated start "$candidate/rom/master_of_fighters.sms"
```

Use o [workflow de sessão privada](../../tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md)
para input, captura, conciliação pelo recibo e fechamento por ID. `./run.sh`
abre manualmente uma ROM nominal quando ela existe. O viewer v3 histórico está
em `out/candidates/dr_social_taunt01_cycle_v3_src`, SHA-256
`47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`.
Suas medidas cobrem o viewer com Ken de construção. A integração do duelo,
os comandos competitivos e o aceite do pacote Social seguem no
[memory bank](doc/10-memory-bank.md).
