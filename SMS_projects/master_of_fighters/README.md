# Master of Fighters

> **Dr. Social in-game congelado pelo proprietário em 04/11/2026.**
> Leia [o registro vigente](doc/dr_social_ingame_freeze_20261104.md) antes de atuar.
> Model sheet/referências de tamanho e cena experimental preservados; J.J. e
> Hayato/Kenseiden seguem validados no recorte já realizado.

Jogo de luta autoral em desenvolvimento. O manifesto padrão compila o
esqueleto. Os manifestos de viewer são diagnósticos de arte e animação.

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
