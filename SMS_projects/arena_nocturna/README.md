# arena_nocturna

Vertical slice jogável do SMSForge: uma arena Dark Deco para Master System,
criada para demonstrar o hero VANTA-9, um guardião inimigo grande, metasprites,
tilemap, tiro, contra-ataque e ritmo de frame.

## Controles

- D-pad: mover VANTA-9
- Botão 2: disparar
- Botão 1: reiniciar após vitória ou `CORE BREACH`

## Reproduzir

```sh
./build.sh
./run.sh
```

Assets visuais: `rascunho/` → derivados auditados em `res/` → headers 4bpp em
`inc/`. O ROM atual é `out/rom/arena_nocturna.sms` (SHA-256
`f86c4fae3826699c39a231f4ff33761f7d54adf5e08bc20ec3d341d04504d7d8`).

Estado observado no Emulicious: title BG-only, atração determinística, hero em
quatro poses autorais com pose de ataque ligada ao disparo, boss 4× maior com
telegraph/hurt/dead, tiro horizontal ciano/branco, contra-ataque diagonal
magenta/violeta com núcleo quente, colisão swept e impacto em três frames sem
flicker. O controle humano continua pendente porque o teclado
do harness não fechou o caminho de input; a atração não é usada como prova de
agência.

Bundle de evidências atual: `out/evidence/sealed_bundle_final_v6.json`.
