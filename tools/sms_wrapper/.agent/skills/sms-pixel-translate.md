# skill: sms-pixel-translate

Use quando uma foto, conceito ou arte de outro console precisar **entrar**
no contrato visual do Master System. Porta o MÉTODO da skill Hermes
pixel-art v2.0.0 (MIT: downscale NEAREST → Floyd-Steinberg no grid),
**nunca** a paleta NES/SNES/PICO-8/C64/Game Boy (§32/L001/L055).

Ferramenta: `prepare_sms_pixel_art.py`.

## O que entra

- Foto ou PNG truecolor em `rascunho/` (sha256 no manifesto).
- Pixel art de outro hardware usada como **régua** (escala, silhueta,
  densidade). Pixels só reentram com licença/proveniência.

## O que sai

PNG indexado, grid 8×8, índice 0 transparente, ≤15 úteis, RGB no
contrato canal×85. Ainda **não** é personagem/palco final: é tradução.
Gates: `audit_validate_resources.py`, `audit_luma_floor.py`,
`audit_provenance.py`. Entrega visual: `sms-visual-excellence.md`.

Para personagem de um projeto, use a paleta exata declarada em
`doc/palettes_manifest.json` como conjunto permitido. Depois da conversão,
valide a folha com `audit_validate_resources.py` e os argumentos
`--kind sheet --project <projeto> --character <id> <png>`; o gate confere grid,
transparência, limite de cores, valores SMS 6-bit e se cada cor usada pertence
à paleta daquele personagem (L100). Se a paleta do personagem mudar, atualize
a fonte geradora e regenere o manifesto. Prompt e aprovação visual não
substituem essa medição.

Em folhas de sprite com halos ou granulação de fundo, prefira
`prepare_sms_pixel_art.py` com `--dither none`, `--speckle-cleanup`,
`--project <projeto>`, `--character <id>` e `--cell-size WxH`. Confira a saída
na escala nativa. A limpeza remove componentes pequenos por quadro; revise se
um detalhe legítimo foi removido (L101). Floyd–Steinberg continua disponível
para outros tipos de conceito.

Em um roster, paleta correta não significa imagem equalizada: confira a
distribuição de cor por material, mantenha clusters de sombra/base/luz coesos e
elimine halo ou pontilhado que polua o contorno. Compare com o conceito
aprovado e uma referência de acabamento, sem emprestar suas cores. Revise o PNG
transparente no tamanho nativo e em nearest-neighbor 4×; registre esse parecer
separado da conformidade de paleta (L100/L101/L105).

Em cada material, declare a ordem dos tons (sombra → base → luz), sua região e
a direção da luz. A aprovação da paleta só prova que os RGB pertencem ao
contrato; não prova que sombras e luzes formam volumes coerentes. Revise
`material_shadow_flow_coherence` e `semantic_palette_role_confinement` em todas
as poses: os clusters de sombra devem
seguir a mesma face/dobra do tecido e não podem alternar manchas claras e
escuras sem justificativa espacial. Ao reduzir uma arte já colorizada, se a
quantização espalhar tons da mesma rampa dentro do tecido, pode-se amostrar a
cobertura média da região-fonte por footprint e escolher um tom já existente
pela luminância. A máscara de material deve vir da classificação mais próxima;
nunca misture amostras através de contorno, transparência ou outro material.
Preserve a geometria por nearest-neighbor, não crie cores, não aplique blur nem
dithering, e confirme que alpha e materiais alheios à rampa ficaram idênticos.
Confine branco, amarelo e demais acentos às regiões semânticas autorizadas; não
deixe pixels isolados em roupa, cabelo ou contorno. Limpe apenas vazamentos
comprovados e preserve agrupamentos legítimos de olho, luva, gola e equipamento.
`audit_art_review_checklist.py` exige os dois eixos no registro, mas a decisão
sobre fluxo e papel das cores continua visual e independente.

### Correção iterativa de sprite por material — L124

1. Congele a fonte aprovada (papel, caminho, SHA e IDs de quadro) e gere cada
   candidata em diretório versionado próprio. Não reutilize ROM, preview,
   checklist ou captura de uma imagem anterior.
2. Anote defeito por material/região/quadro e corrija uma família por passe. Para
   reduzir arte colorida, classifique primeiro a máscara pelo nearest-neighbor;
   só faça média de área dentro da máscara, sem amostrar através de contorno,
   transparência ou material adjacente.
3. Trate conectividade e geometria como detector de candidatos. Pixels que tocam
   a borda escapam de filtros limitados a componentes totalmente internos;
   use âncoras semânticas estáveis quando existirem. Preserve agrupamentos
   ambíguos maiores para revisão humana em vez de os apagar automaticamente.
4. Recolora vazamentos comprovados com tons locais já presentes na paleta. Emita
   deltas por pose e confira IDs, alpha, geometria, cores novas e pixels alterados
   fora da região-alvo. Revise todas as poses a 1× e nearest-neighbor 4×.
5. Depois de qualquer alteração de pixel, reconstrua a ROM e compare todos os
   framebuffers com os PNGs indexados. Render exato prova a conversão; fluxo de
   luz, semântica, anatomia e aprovação continuam como eixos visuais separados.

Os limiares geométricos da v10 do Dr. Social (área, comprimento, razão linear e
margem da haste) pertencem àquele canvas/arte; não os copie para outro desenho
sem recalibrar e revisar falsos positivos/negativos. Veja L124/§114.

```
prepare_sms_pixel_art.py rascunho/foto.png rascunho/foto_sms.png --block 8 --size 256x192
prepare_sms_pixel_art.py rascunho/sprite.png rascunho/sprite_sms.png --block 1 --size 32x64
```

`--block 1` = já é pixel (só quantiza). `--block 8` = foto chunky no tile.

## Proibido (contaminacao de outro hardware)

- Preset `nes` / `snes` / `pico8` / `gameboy` / `arcade` 32 cores / `neon`.
- Paleta adaptativa de 32 cores (SNES). SMS = 15 úteis + idx0 por subpaleta.
- Dither que invente cor fora de {0,85,170,255}.
- MP4/GIF com chuva, neon, fireflies, snow como evidência de ROM ou como
  asset em `res/`. Cena `night/urban/snow` no máximo informa o GDD
  (atmosfera); o VDP não tem essas partículas de graça.
- Promover a saída desta ferramenta a lutador/boss/palco `delivery`
  sem model sheet e sem `audit_visual_delivery.py`.
- `tool:"code"` no manifesto para personagem — esta ferramenta **traduz**
  um original; o original precisa de proveniência.

## Relação com animação

Ciclos de sprite: `sms-sprite-animation.md` + `audit_animation_semantics.py`.
Não use `pixel_art_video.py` para fabricar walk/punch. Vídeo de mood não
substitui strip no grid 8×8.

## Atribuição

Método (quantizar DEPOIS do downscale para o dither cair no pixel final)
e a ideia de presets de época vêm da skill pixel-art v2 (dodo-reach / MIT,
paletas de Synero/pixel-art-studio). A paleta mestra é só a do SMS.
# Refinamento autorizado e material (L124)

Máscaras heurísticas são candidatas: conferir regiões e franja, não só ausência
de cor proibida no interior. Preservar alpha não preserva automaticamente
separações materiais ou contorno interno. Declare deltas de ownership, cores e
contorno acrescentado, com autorização por revisão. Critério 2×2 sólido precisa
testar o quadrado, não somente área/bbox; detalhes 1px autorizados são exceções
semânticas registradas. Use `art-review.md`; não portar heurísticas específicas
do Dr. Social como preset universal, nem inferir qualidade de uma convergência.
