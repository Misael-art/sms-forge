# Prova técnica de conversão de asset para Sega Master System — v3

**Status do padrão:** piloto documentado; revisão humana do asset Dr. Social pendente.  
**Escopo:** provar a conversão visual e inventariar recursos gráficos do candidato antes de planejar a folha de animação.  
**Não é:** sprite sheet final, contrato de runtime completo, aprovação para `res/`, ROM ou certificação automática de qualidade AAA.

Use o modelo `doc/asset_conversion_contract_template_v3.json`. Esta revisão
conserva duas poses e mapa de tiles separado; acrescenta transform indexado
nearest-neighbor reprodutível, canvas tile-alinhado e margem transparente
mensurada para impedir que previews incompletos sejam aceitos.

## Objetivo e ordem

Depois que o concept/model sheet for aprovado, cada personagem ou item recebe
um contrato técnico próprio. Nesta etapa a prancha mostra **exatamente duas
poses-chave**: uma idle e uma ação que expressem a identidade do personagem.
Elas são amostras de referência independentes, não dois quadros de uma
animação e não autorizam a produção da folha completa. A folha animada virá
depois que GDD, semântica de movimentos, limites do SMS e orçamento do TDD
estiverem fechados.

```text
concept aprovado → contrato do asset → duas poses-chave em pixels SMS
→ revisão exata de pixels e de arte → orçamento de hardware no GDD/TDD
→ aprovação humana → folha de animação → integração → ROM/emulador
```

Qualidade AAA é a meta artística do projeto, não um veredito que um script
possa emitir. Nenhum gate técnico substitui revisão visual independente e
aprovação do dono.

## Prancha obrigatória

Cada cartão apresenta a mesma personagem, sem alterar proporção entre as
poses:

- uma pose idle e uma pose de ação alinhadas ao concept aprovado e à identidade
  do jogo de origem;
- canvas nativo declarado por pose, régua relativa e baseline/pivô derivados
  do contrato de escala do GDD;
- visualização em 1× e ampliação nearest-neighbor claramente rotulada;
- paleta indexada efetivamente usada, RGB da grade de 6 bits e transparência;
- caixa opaca, contagem exata de células 8×8 ocupadas, padrões únicos e bytes
  brutos 4bpp por pose e para o par;
- mapa de ocupação 8×8 em painel independente;
- limites físicos SMS e cada orçamento de runtime com estado explícito;
- fonte, hash, concept de referência, hash do contrato, pareceres e próximos
  gates.

### Regra inviolável de composição

**Nenhuma grade, linha, régua, baseline, rótulo, caixa ou anotação pode cruzar
o retângulo que contém os pixels do sprite.** O PNG de pose convertido e a
renderização da prancha precisam ser idênticos pixel a pixel após composição
da transparência e do fundo de inspeção. Se a fonte usa uma transformação de
escala, ela deve ser declarada e reproduzível a partir do frame indexado; a
prova permite nearest-neighbor uniforme e rejeita interpolação, antialias ou
transform não declarado. A grade de tiles aparece somente em mapa separado.
`audit_asset_proof_sheet.py` refaz o transform declarado e compara a prancha
com o PNG convertido; qualquer overlay ou diferença reprova a prova.

Inspecionar cada fonte em tamanho nativo e em nearest-neighbor 4× ou maior,
sobre fundo contrastante. Fundo de prova pode ser somente magenta puro
`#FF00FF`, verde `#00FF00` ou azul `#0000FF`, escolhido sem colisão com pixels
opacos do asset. O fundo é de visualização, não integra o arquivo do personagem
nem sua paleta.

## Contrato de pixel e medição

- PNG indexado, índice 0 transparente, alpha binário, no máximo 15 cores úteis
  na subpaleta de sprites e RGB com canais em `{0, 85, 170, 255}`.
- Resolver escala a partir do GDD e do padrão visual do jogo. Redução para o
  tamanho-alvo é permitida como conversão uniforme nearest-neighbor
  determinística, sem filtro; nunca deformar eixo ou remover detalhe sem
  revisão. Bbox opaca inclui armas/equipamentos: registrar a altura corporal
  separadamente quando comparar o elenco.
- A pose convertida deve manter pelo menos 1 px transparente em cada borda;
  nenhum pixel de personagem/arma pode encostar ou ser cortado pelo canvas.
  Canvas tem largura e altura múltiplas de 8. A margem é integridade da prova,
  não limite físico do VDP.
- Tile: 8×8 px, 32 bytes em 4bpp. Contagem de célula ocupada, padrão único,
  colocação e bytes são inventário exato de índices da arte; não deduplicar
  flips sem declarar e provar a otimização.
- O mapa 8×8 **não** é contagem de objetos SAT. Hardware sprites, geometria de
  metasprite, pico por scanline, alocação e tempo de carga são gates próprios.
- Registrar separadamente pixels-fonte, preview composto, PNG indexado,
  arquivo em `res/`, dados de runtime e SHA da ROM. Um estágio não herda a
  aprovação do anterior.
- Rodar `audit_sprite_cutout.py` sobre a fonte. O modo `components_only` detecta
  ilhas opacas menores que o mínimo declarado, mas termina como **pending**
  enquanto regiões de cor por material não estiverem descritas. Esse resultado
  não aprova recorte/cor nem libera promoção.

## Limites físicos de Master System

| Recurso | Limite ou valor físico | O que a prancha pode afirmar |
|---|---:|---|
| Canvas visível | 256×192 px | Resolução da tela; não define a escala artística do personagem |
| VRAM | 16 KB | Total compartilhado por padrões, name table, SAT e demais estruturas |
| Padrão gráfico | 8×8 px, 32 B em 4bpp | `16 KB / 32 B = 512` posições de padrão no total |
| Padrões endereçáveis por sprites | 256 na metade selecionada pela base de sprites | Não é orçamento livre: BG, HUD e outros assets também consomem VRAM |
| SAT | até 64 objetos | Exige geometria real de metasprite para ser auditada |
| Carga por scanline | até 8 objetos de hardware | Exige simulação das coordenadas/alturas de cada objeto; o mapa de tiles não prova |
| Dimensão de cada objeto sprite | 8 px de largura; altura 8 ou 16 px | Arte maior é composta como metasprite; não existe modo de objeto 16×16 |
| CRAM | 2 subpaletas × 16 entradas; índice 0 transparente | Até 15 cores úteis na paleta de sprite; total de 30 úteis nas duas tabelas |
| RAM / ROM sem mapper | 8 KB / 48 KB | A quantidade de estados residentes precisa de contrato de runtime e banco |
| Transferência | sem DMA; upload em massa no VBlank | Medir o pior frame e a rotina; não estimar a folga |

**Não existe um limite físico universal de quadros por sprite sheet.** O máximo
permitido pelo projeto depende do formato dos quadros, compartilhamento de
padrões, pools estáticos de VRAM/RAM, armazenamento e banking de ROM, estados
residentes e orçamento medido de upload por VBlank. O campo
`max_frames_per_sprite_sheet` fica `null` até que o TDD e `13-spec-cenas.md`
registrem esses valores e o degrau seguinte seja medido. Não tratar duas poses
de prova como uma folha de dois quadros.

Cada prova registra `pending/pass/fail` para: residência VRAM, SAT/scanline,
VBlank, banking/ROM e limite de quadros. `pending` bloqueia a promoção da
folha animada. A contagem de padrões de um ou dois quadros não prova que todos
os demais assets cabem simultaneamente.

## Doze princípios da animação — regra obrigatória

Toda animação produzida para o projeto deve considerar e documentar os doze
princípios. Uma folha completa deve vincular cada princípio a poses, quadros,
timing ou decisão artística verificável:

| Princípio | Verificação no asset |
|---|---|
| Squash and Stretch | volume e massa preservados; deformação apenas quando a ação justificar |
| Anticipation | pose prepara e anuncia a ação principal |
| Staging | silhueta, foco e trajetória deixam a ação legível |
| Straight Ahead / Pose to Pose | método de construção declarado; poses-chave e intervalos coerentes |
| Follow Through / Overlapping Action | cabelo, cravat, casaco e arma acompanham o movimento principal |
| Slow In / Slow Out | espaçamento e holds aceleram/desaceleram com intenção |
| Arcs | membros e arma seguem arcos plausíveis, com juntas contínuas |
| Secondary Action | gesto/roupa reforça sem competir com a ação principal |
| Timing | duração de cada quadro/hold registrada em frames |
| Exaggeration | ação clara e expressiva sem quebrar anatomia nem identidade |
| Solid Drawing | volume, perspectiva, equilíbrio e encaixes permanecem sólidos |
| Appeal | pose/expression preserva personalidade e apelo do personagem |

O contrato usa `pass`, `fail`, `pending` ou `not_applicable`, sempre com
evidência e justificativa. Dois stills podem orientar encenação e forma, mas não
validam ciclo, aceleração, timing, intervalos, follow-through ou leitura em
movimento; esses eixos ficam `pending` até a folha animada e seu review.

## Revisão de arte e promoção

Registrar um parecer independente ligado por SHA ao conceito, às duas poses,
ao contrato e à prancha. A revisão humana avalia, para cada pose:

- fidelidade ao concept e à referência original, biotipo, silhueta e proporção;
- grupos de pixels, rosto/olhos a 1×, contorno e ausência de pixels soltos;
- luz e tons por material, sem blur, dithering decorativo ou cores extras;
- ombros, cotovelos, punhos e mãos; cadeia mão→empunhadura→guarda→arma;
- fixação, perspectiva e recorte de cane/arma/acessórios;
- baseline, scale, legibilidade nativa, encenação e contraste;
- composição final e correspondência exata entre preview e fonte.

Use `audit_art_review_checklist.py` para cobertura/status/hash; ele não julga a
verdade visual. Use `audit_asset_proof_sheet.py` para reprodução de pixels,
paleta, dois papéis de pose, inventário 8×8 e completude das declarações
técnicas. Qualquer diferença pixel a pixel falha. Qualquer eixo visual `fail`,
`pending`, divergência de concept, paleta inválida, auditoria de tile/recorte
falha ou orçamento runtime sem medida impede promoção. O autor não aprova sua
própria arte.

Depois desta prova aprovada pelo dono, definir animação e orçamento no GDD/TDD;
somente então produzir a folha completa e validar semântica, recursos,
metasprite, scanline, VBlank, ROM e emulador. Esta prova não entra em `res/` e
não afirma integração, FPS, gameplay, validade em ROM ou AAA.

## Referência de escala e piloto Dr. Social v3

*Fatal Fury Special* para Game Gear é a referência visual de composição. Uma
figura em pé ocupa aproximadamente 53 px na captura consultada; sua proporção
na tela 160×144 projetada à tela SMS 256×192 dá `53 × 192 / 144 ≈ 71 px`. O
GDD/TDD fixam uma faixa de trabalho de 66–72 px, centro 70 px. É uma estimativa
visual e uma tolerância de projeto, não propriedade física de tile ou VDP. Veja
[capturas originais Game Gear](https://www.mobygames.com/game/10591/fatal-fury-special/screenshots/game-gear/66969/)
e a [galeria de gameplay](https://www.gamestar.de/galerien/fatal_fury_special_game_gear,46053.html).

A v2 está preservada, mas não serve como proposta atual: arma encostada no
limite direito e canvas 96×96 maior que o novo padrão visual. A amostra v3 em
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v3.png`
tem JSON/hash homônimo. Usa canvas 80×80 (10×10 tiles), nearest-neighbor 5/6,
frame-fonte 01 como idle e frame-fonte 08 como ação. A bbox opaca mede 37×67 px
no idle e 68×70 px na ação; margens transparentes L/T/R/B são 20/7/23/6 e
7/4/5/6 px. A arma da ação está inteira dentro do canvas. Contagem exata:
43/52 células ocupadas, 42/52 padrões únicos e união de 94 padrões (3.008 B
brutos em 4bpp).

A amostra segue candidata. Regiões de material, revisão de anatomia/arma/concept,
review independente, decisão do dono e budgets de runtime permanecem pendentes.
Ela não entrou em `res/` e não foi validada em ROM/emulador.
