# Estocada forte de Alis — estudos não aprovados

Estudos exploratórios gerados em 2026-11-15 com a ferramenta integrada de
geração de imagens. Não são sprites nativos, não foram convertidos e não
representam uma animação aprovada ou uma ROM. Ambos medem 2172 × 724 pixels,
RGBA, com 256 valores de alpha; o adaptador existente exige fontes indexadas
com índice 0 transparente. A extração, quantização, escala, pivôs, máscara e
paleta SMS ainda exigem trabalho e revisão. A conversão não corrige desenho.

Referências: concept v4 de Alis SHA-256
`b7b01f18ae71b5538404935f4ce2e1cf6b10991dde6522c6697c0b52ab6ede95` e
prancha `doc/duel_reach_reference_v2.png` SHA-256
`80d8e8a3ef99c4d49999e600a1062ba2149c77bf2ddffc332bd5e95292a04dec`.

## Primeira tentativa

`study_01.png`, SHA-256
`aaae93f8bf5b14425329c99115f3c9c4385cd86398a723d0ffc273236d4bb755`.
Cinco poses geradas em sequência, com linha de chão desenhada e resíduos
vermelhos e azuis junto às figuras. A posição do escudo e comprimento da
espada não foram validados. Não há correspondência demonstrada com os
68 px corporais; não usar para medir alcance.

Prompt: “Create original game animation source art, a clean pixel-art character animation sheet for Alis Landale. Reference image 1 is the approved identity, costume, sword and shield; reference image 2 gives body proportion and Hayato scale. Draw only Alis in strict side view facing right, consistent anatomy and costume, five separate full-body poses ordered guard, preparation, extended sword thrust, recoil, settled guard. Ground line and planted feet coherent across frames; shield fixed to forearm and turns naturally; short sword remains continuous from hand to tip, with consistent length. Show clear weight transfer and readable silhouette, SNK fighting-game expressive timing, no motion blur. Same scale across poses, reference standing body height equivalent to 68 pixels. Clean discrete hard-edged pixel clusters, no text, no grid, no other character, generous space around each pose. Transparent background.”

## Segunda tentativa

`study_02.png`, SHA-256
`ab889dac61fca9a5da3bb52977d133cb622e1f35cc47ea4056f3fa06328d02a3`.
Pediu-se a remoção dos resíduos e da linha, mantendo a ação. A linha visível
de chão deixou de aparecer, mas resíduos vermelhos e azuis permanecem, em
particular perto da espada e dos apoios. O ajuste **não resolveu** o recorte;
escudo, mão, arma, escala e animação seguem sem validação. Não promover.

Prompt: “Revise this fighting-game animation study: keep Alis's identity, costume, five positions and overall action. Remove every red halo, stray pixel, ground line and background artifact. Five isolated full-body side-view character poses, facing right, transparent background. Consistent anatomy and proportions, same short sword length across poses, one continuous grip and sword, shield physically attached to forearm in every pose. Make the motion a clear sequential weight shift guard, windup, thrust, recovery, guard, with planted feet and no duplicated limbs. Clean pixel art with hard edges; no antialias, no text or graphics. This is an unapproved production study.”

## Retomada — chaves e sequência exploratórias

Três imagens adicionais geradas com a ferramenta integrada em 2026-11-15:

- `keyposes_01.png`, SHA-256 `fb1ddcaf94154bcd9a01a1807d6b07c21ae989187ab37e3ad6979162277cf28b`: guarda e extensão; a fixação do escudo na extensão ficou encoberta.
- `keyposes_02_shield.png`, SHA-256 `d9a3fcafe3fbd03f05e4722704b3944b5581062efd956557087cb595757f91cc`: edição da anterior que revela mão, tira e interior do escudo. O desenho do escudo difere da guarda e sua continuidade permanece sem revisão. Não prova recorte ou escala.
- `sequence_01.png`, SHA-256 `afddbb42ac9358606d46780032a997e15e392182aa71e675fe6967029e782eb2`: cinco poses baseadas na primeira chave. Não incorpora a segunda versão do escudo; arma e trajetória ainda precisam de revisão e o timing não foi testado.
- `sequence_02_shield.png`, SHA-256 `c70ef27f35d682e652d9d2e2db6a8fb9810bbfc1713560843db054d3efa54df3`: nova tentativa de incorporar a pega na sequência. A extensão mostra a pega, mas a parte interna aparece marrom, contrariando a solicitação de manter o desenho, e permanecem resíduos vermelhos e azuis. Não é fonte limpa.

Referência gestual: `study_02.png`; referência de economia visual: guarda
convertida de Hayato em `out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_left/idle.png`.
As duas chaves medem 1774 × 887 e a sequência 2172 × 724. Não são fontes
indexadas nativas, nem foram comparadas a Hayato na mesma escala; não derivar
alcance delas. Um ajuste de escudo isolado não estabelece continuidade.

Prompt das chaves: “Make original production source art for a side-view fighting-game character, using first image for Alis's design and thrust gesture and second image only for desired pixel-art visual economy. Exactly two separate full-body poses facing right: guard and maximum horizontal thrust. Strict side profile torso, consistent body scale and proportions; boots planted at same ground level; clear hand holding short straight sword, same blade length both poses; shield strapped to visible opposite forearm, mounting readable especially during thrust. Preserve magenta, indigo, ivory armor and brown-gold hair. Crisp deliberately drawn chunky pixel-art silhouette, limited flat colors, no antialiasing, no red halos, no stray pixels, no text, no grid, no outlines around the whole image, transparent background. Ample space between figures; no ground line. Source for later 68-pixel game sprite.”

Prompt da edição do escudo: “Edit the image, concentrating on the right-hand thrust pose. Make the opposite forearm and hand clearly visible behind the shield, with an obvious strap wrapping the forearm so the shield is physically attached. Turn the shield slightly toward the viewer while keeping the torso in strict side profile. Preserve the pose, character identity, body, leg positions, short sword, colors, scale, left guard pose, and transparent background. Remove any red and cyan fringing around the silhouette; hard pixel-art edges. No text or floor.”

Prompt da sequência: “Produce an original side-view game sprite animation source strip, matching the Alis character and exact costume in reference image 1, using image 2 for the five-beat gesture. Five fully separated complete poses facing right, consistent scale and shape: guard, low preparation, horizontal thrust, recoil, returned guard. Short sword stays same physical length and has a clearly gripped hilt; the intermediate blade direction follows hand and tip naturally from low backward to horizontal. Shield straps visibly onto opposite forearm, face discernible in the thrust. Show the hips, knees and planted feet transfer weight. End pose matches guard, no floor or text, transparent background, crisp limited-color pixel art with discrete edges and no colored halos or loose pixels. Leave generous transparent separation between poses.”

Prompt da segunda sequência: “Create a five-pose full-body side-view fighting game animation sprite source using reference image 1 as the definitive guard and thrust, and reference image 2 only as the low preparation/recovery gesture. Retain the EXACT same shield design as in the guard: ivory and magenta outer face, gold rim, visibly held on Alis's left forearm throughout all poses. In the thrust pose show a narrow portion of its inner side and the hand/strap, but keep the same outline and construction, no new wooden shield. Keep the blue short sword the same length in every pose; clear base, hilt, hand and tip. Left to right: guard, preparation, thrust, recovery, same guard. One character per pose facing right, same body scale and ground plane, clear planted feet, clean crisp pixel art, no red/cyan halos, no labels, true transparent background.”

## Retomada — edição por região e estudo de construção

Foi reaproveitado `keyposes_01.png` como base. A primeira tentativa desta
retomada, `keyposes_local_cleanup_01.png`, SHA-256
`837facb1246620c1f1632370913abc17d6eab3dff7ffdacb93cbd5c35877caca`,
pediu remoção da franja cinza e halos, preservando todo o resto. A ferramenta
gerou uma imagem de mesmo canvas, mas alterou extensamente o interior das
duas figuras. Em composição RGB sobre `#a6a6a6` e sem alinhamento de pivô,
46.399 pixels da metade de guarda e 44.991 da extensão diferem em mais de
16 num canal. Recortes internos `(220,250,430,650)` e
`(1020,300,1250,600)` contêm respectivamente 16.175 e 14.820 pixels
divergentes pelo mesmo critério. Esses recortes não são máscaras artísticas;
servem como evidência negativa de preservação, não como avaliação de alcance.
**Nenhuma correção foi fechada.** Não expandir esta imagem como fonte final.

Prompt da tentativa: “Edit this existing image locally. Remove ONLY the gray fringe between the face and blue sword of the left guard pose, and remove ONLY colored halo pixels outside the two figures. Preserve every other pixel and exact location, geometry, colors, shield material and occlusion, both complete poses, both weapons and the canvas. The right-hand shield may naturally conceal the hand. No new straps or visible wood. Genuine transparent background. Do not redraw the figures.”

`shield_construction_study.png`, SHA-256
`385a888b5c54f1b91ef2e166893f88f7a53b2587814671139ee324f14e8e8ec0`,
é uma proposta de face, borda e fixação, gerada a partir de `keyposes_01` e
concept v4. A face tenta preservar o motivo conhecido; a tira e a superfície
interna são hipóteses de construção geradas, sem comprovação de material ou
aprovação do proprietário. Não são uma correção das poses existentes.

Prompt: “Create a construction reference study of Alis Landale's existing small shield only, based on the supplied reference. Show three small views of the exact same ivory and magenta shield with gold rim: outside face, narrow side, and inner side with forearm attachment indicated clearly. Keep the established outer contour and materials; do not invent brown wood, iron hardware or change the outer design. The forearm may naturally be hidden behind the shield in the action view. Plain background and no captions; this is a separate construction study, not a replacement for the action sprite.”

O comando anterior que exigia fixação legível permitiu interpretar que mão e
tira precisavam aparecer durante o golpe, o que levou à edição com interior
marrom. A direção atual aceita oclusão e pede construção separada. A nova
tentativa de remoção de franja repetiu a alteração fora da região; é preciso
mudar de método, não repetir uma edição global e chamá-la localizada.

### Esboço temporal diagnóstico

`out/diagnostics/alis_strong_thrust_round1/sequence_01_sketch_normal.mp4`
(SHA-256 `8c55c866dba820b052adb3c62b096d4353049c297e845bf1efb4c30d4b8127f0`)
reproduz quatro ciclos a 60 fps: guarda 8, preparação 7, extensão 3,
recolha 6, guarda 12 quadros. A versão `sequence_01_sketch_slow.mp4`
(SHA-256 `b453a39b38c297007edd5eeac55db9ea846c8c8f01f88589fb71d14a3c5efc3e`)
é a mesma sequência quatro vezes mais lenta. Foi usado o PNG exploratório
`sequence_01` com recortes horizontais `[0,367,758,1360,1761,2172]`,
centralizados em canvas de 602 × 724 e reduzidos por nearest-neighbor a
150 × 180. A centralização não registra pivôs: o vídeo pode introduzir
deslocamentos aparentes. Não é framebuffer, teste de input ou animação
aprovada; uma imagem do quadro 16 foi inspecionada, mas a reprodução contínua
ainda não foi avaliada. As exposições são hipótese, não frame data selado.

## Retomada — máscara e registro de apoios

Na primeira tentativa desta retomada, `tools/alis_mask_cleanup.py` reutiliza
`keyposes_01.png` e altera apenas alpha 1..24 na caixa `[455,190,515,290)`
entre rosto e espada. `keyposes_guard_masked_01.png` tem SHA-256
`2d358b12a0956f5b4f7e05ede25c9babe1a1a6116ccc1798b2f915d1404d0ef4`;
a máscara e o recibo têm nomes `keyposes_guard_mask_01.png/.json`. Um
segundo cálculo independente de bytes RGBA confirmou 2.224 pixels alterados
e **zero fora da máscara**. A extensão é preservada byte a byte. O tratamento
não corrige contaminação opaca, nem demonstra que a franja desapareceu no
recorte nativo: revisão artística continua pendente. O método anterior, que
gerava a folha inteira e mudou regiões fora do pedido, foi abandonado.

`tools/alis_duel_preview.py` cria `duel_keyposes_provisional_1x.png` e
`duel_keyposes_provisional_4x.png` em `out/diagnostics/alis_strong_thrust_round1/`.
Hayato é o `idle.png` convertido v7 esquerdo, SHA-256
`b34e97ea6585939ebe5f867098b69163dc62a2c26c5b33ef7e2d011231a6e1ee`,
espelhado para a composição. Chão comum Y144, âncora traseira rosa de Alis,
apoio dianteiro amarelo e pivô verde de Hayato; os pontos de Alis são
estimativas visuais. Alis é reduzida por nearest-neighbor com fator 1/10
experimental, o mesmo nas duas poses, e Hayato mantém pixels de saída.
O desenho não fornece uma pose neutra calibrada: **isto não demonstra a
relação corporal aprovada de 68 px nem serve para fechar alcance**. As
pranchas são diagnósticas, não fontes nativas convertidas nem prova de ROM.
SHA 1× `ff91fea0a341c957d74dae87b13b43782c2e204ec629b11f6ea993089f7be35e`,
4× `67e1926b81640f9400d9f0b67ff33ade0779edd3abbbecbede37146e3424a8b3`.

Os vídeos `sequence_01_pivot_sketch_normal.mp4` e
`sequence_01_pivot_sketch_slow.mp4`, no mesmo `out`, foram remontados pelo
script `tools/alis_pivot_sketch.sh`. Exposições permanecem 8/7/3/6/12 a
60 Hz; a última guarda usa exatamente a mesma fonte da primeira. As âncoras
visuais no centro aproximado do apoio traseiro na fonte são X=76,449,836,1404
para guarda/preparação/extensão/recolha; Y do chão é comum e o avanço
adicional declarado é zero em todas. Isso estabiliza uma referência de pé,
não autentica o pivô anatômico, o contato nem o avanço do jogo.

No vídeo decodificado, com o mesmo critério do parecer (limites nos 9 pixels
inferiores, máximo RGB ≥64), guarda/preparação/extensão/recolha/guarda têm
X esquerdo/direito `16/89`, `17/93`, `16/105`, `16/90`, `16/89`, Y=153.
O recuo aparente do apoio traseiro na transição preparação→extensão caiu de
27 para 1 px; a diferença remanescente inclui discretização/compressão. O
apoio dianteiro avança na imagem. Isso não comprova animação boa ou pés
fisicamente plantados. Sequência contínua ainda precisa de revisão humana;
foram inspecionados quadros individuais. Não é framebuffer da ROM.
SHA vídeo normal `75c1a78e945a516840ad4beeba3f6531366e02501faf18ec356cf2cee4b179dd`;
lento `5eb6dc28b48806fba3ea0d742e351d7f187bc792d06764fa5ba169d2bcc319ad`.

## Retomada — conversão, orçamento estático e preparação do piloto

O adaptador oficial passou no self-check. As receitas
`.mddev/alis_strong_keyposes_extract_{before,masked}.json` extraíram as duas
chaves com limiar de alpha 128. Os arquivos indexados foram idênticos antes
e depois da máscara: guarda SHA-256 `ffd17ab7aeb901f2896fbe29def1daf18cf249dbf46aaa62acb1d317d1611542`,
extensão `052265e55bb29e6b98c174b13ae961ce2ac92113bfb045db988f702f8ae47672`.
Resultado: a máscara anterior **não corrigiu** a saída usada nesta extração.
Os recibos e fontes indexadas estão em `out/diagnostics/alis_strong_thrust_round1/keypose_{before,masked}/`.

A quantização automática sacrificou o azul da espada e o magenta da roupa.
O perfil `alis_strong_keyposes_material_extract.json` reservou três cores
de lâmina a partir da fonte autoral; `alis_strong_keyposes_hayato_exact_probe.json`
fixou uma paleta P1 de 15 cores e mapeamentos materiais. Na comparação da
guarda (`palette_guard_three_comparison_4x.png` no `out`), azul e magenta
voltam a aparecer. A primeira paleta explícita tornou cabelo de Alis muito
magenta; uma troca de cor recuperou a leitura castanha. A guarda de Hayato
com a paleta comum foi comparada à v7, nas duas faces, com **zero diferenças
RGBA após registro**. Revisão de material por região permanece pendente;
um índice compartilhado pode aparecer em mais de um material.

O adaptador aplica `2/3` em X e `6/7` em Y. O estudo inicial, sem ajuste,
ficou 22,2% mais estreito em relação à altura. O script
`tools/alis_precondition_aspect.py` registra uma pré-compensação horizontal
nearest-neighbor de `9/7` (canvas real 257/200, com arredondamento) antes do
adaptador. Isso aproxima fatores geométricos iguais, mas não calibra a altura
neutra nem comprova a identidade do corpo. Em `keypose_pair_aspect_probe`, a
extensão inteira em sprites chegou a 10 por linha. Uma busca diagnóstica das
64 × 64 fases de empacotamento não encontrou pico ≤8. O teste 8×16 chegou a
11 na guarda e 12 na extensão. Esses perfis reprovados foram preservados.

A tentativa `keyposes_lower_thrust_generated.png`, SHA-256
`332044291cdb4539d325fb84470b2f46b5bec2b38b7caa58ff0af153d9f39e27`,
partiu da extensão e abaixou a arma. O script `alis_lower_thrust_region.py`
limitou a substituição à caixa `[1090,270,1650,490)`; 77.784 pixels mudaram
dentro e zero fora da máscara. O resultado tem SHA-256
`232e54df6a79c21a6154189245e098fc6515d520092589a13dcd62d0c05ab78c`.
Ele preserva a guarda fora da máscara, mas costura, anatomia e equipamento não
foram aprovados. A conversão `keypose_pair_lower_probe` chegou a 11 por linha
com a fase inicial; a busca de fases encontrou mínimo 10. A alteração, portanto,
**não resolveu** o orçamento e não foi integrada ao piloto.

Prompt da tentativa: “Edit only the RIGHT-HAND thrust pose of this existing two-pose pixel art image. Keep the left guard entirely unchanged. Preserve Alis's costume, head, hair, torso, shield silhouette, legs and feet in their original locations. On the right pose only, lower the sword arm and the straight blue blade together by approximately one forearm thickness, so the sword thrust is horizontal at lower-chest height instead of shoulder height. The shoulder, elbow, wrist, clenched hand, crossguard and blade must remain anatomically connected. Keep the sword same length and shape, keep shield in natural occlusion, no added effects. Preserve the exact canvas and a transparent background, no text, no floor, no halos. This is a draft for a resource-constrained 8-bit fighting game.”

Para investigar sem diminuir a arte, `tools/alis_blade_bg_probe.py` separou
fragmentos da lâmina em BG, preservando os índices ao recompor. As quatro
poses da sequência `sequence_01` foram extraídas e registradas por apoio;
duas tentativas de correção de chão falharam, e a terceira usou margem
transparente explícita, canvas 128×96 e verificação de sola em Y=80 para
todas as poses e Hayato. Em cada face, 32 pixels de preparação e 38 da
extensão foram separados. `grounded_faces_assets_probe/split_probe.json`
registra 24 cenas, 246 padrões SAT, 14 BG e um de HUD. O simulador passou
nos 24 manifestos, com até 53 sprites e oito por linha; o checker independente
reconstruiu os dez metasprites e quatro mapas BG de volta aos índices fonte.
Isso é **somente dado estático**. Com rival próximo, 25 pixels da parte em
BG se sobrepõem ao sprite de Hayato (dois no limite); prioridade, coerência
visual, escrita e limpeza da PNT e custo de VBlank exigem teste no emulador.

Pranchas e esboço da sequência convertida estão em
`out/diagnostics/alis_strong_thrust_round1/converted_grounded_preview/`;
`keyposes_1x.png`, `keyposes_4x.png`, `keyposes_light_1x.png`,
`distances_1x.png`, `right_limit_normal.mp4` e `right_limit_slow.mp4` são
**composições offline**, não framebuffer. A sequência usa 8/7/3/6/12 e a
mesma guarda no fim; não houve revisão contínua de atuação nesta execução.
As poses intermediárias usam `sequence_01`, não a estocada baixa acima.

Reprodução: extrair `.mddev/alis_strong_sequence_material_extract.json` com
`prepare_authored_sprite_sample.py --extract-config`, executar
`tools/alis_precondition_aspect.py --sequence`, converter as duas receitas
`.mddev/alis_strong_sequence_grounded96_{right,left}_probe.json` em saídas
novas e preservar suas reprovações de composição inteira; executar
`tools/alis_blade_bg_probe.py --both-faces --grounded` e
`tools/alis_round1_data_check.py --self-check` seguido de `--grounded`.
Os caminhos esperados e hashes são explícitos nos scripts. O wrapper detectou
a rota de áudio existente ao executar com `XDG_RUNTIME_DIR=/run/user/1000`;
nenhum servidor foi reiniciado. Antes de compilar, medir de novo o host: uma
VM de outro trabalho reapareceu com outro PID e cerca de 2 GiB de RSS.
Não houve build, ROM, sessão Emulicious ou FPS nesta retomada.

### Tentativa adicional de limpeza da franja

`keyposes_gray_fringe_generated_01.png`, SHA-256
`05590f7bfdb8b53671ae18c0509f314a5a5947826f2f9b72822dd9648ecd927d`,
foi gerada a partir de `keyposes_01.png` para limpar a região entre o rosto
e a lâmina, pedindo preservação do restante. Sob comparação RGBA direta,
324.014 pixels mudaram, dos quais 317.719 fora do retângulo diagnóstico
`[450,175,510,290)`. O detalhe lado a lado está em
`out/diagnostics/alis_strong_thrust_round1/fringe_attempt_01_detail.png`.
O pedido global falhou na preservação e o detalhe não demonstrou melhora
visual; o resultado não foi aplicado nem convertido. A fonte usa alpha baixo
em grande parte do espaço examinado, e a comparação anterior já mostrou que
o limiar 128 elimina as diferenças da máscara antiga. As poses utilizadas
no piloto continuam pertencendo a `sequence_01`, não a esta tentativa.

Prompt: “Edit this exact existing game sprite source sheet, preserving its original canvas dimensions and both poses. ONLY clean the unwanted gray opaque fringe in the LEFT figure's small gap between the face and raised blue blade: make the empty background there transparent, preserve the exact blue blade edge and exact face silhouette, and keep every other feature and pixel unchanged. Keep the armor, hair, shield, sword, hands, legs and the entire right pose unchanged. Crisp discrete pixel art, no new colors, no halo, no text. This is a local cleanup draft for comparison; do not redraw or recompose.”

**Teste por máscara da mesma tentativa:** `tools/alis_fringe_region.py` copiou
o estudo gerado apenas no retângulo `[460,195,505,260)`. A fonte resultante
`keyposes_gray_fringe_masked_01.png` tem SHA-256
`af805e564a2b2259d22c552399e94c98baf6803df829e19653da31661a895c57`;
2.517 pixels RGBA mudaram dentro e zero fora, conforme recibo e máscara
homônimos. Com a paleta automática, a quantização mudou também cores da
extensão não editada: o efeito ficou confundido. As receitas
`alis_strong_keyposes_fringe_fixed_{baseline,masked}.json` fixam a paleta de
32 cores da extração original. Nelas a guarda nativa mudou 15 pixels na
região e zero fora; a extensão ficou igual. Em seguida, as receitas de
material fixo e conversão P1 compartilhada produziram um único delta na
guarda convertida: em `(56,34)` do canvas, cinza opaco `#555555` tornou-se
transparente; extensão e Hayato têm zero diferenças RGBA. Os dois pares
estáticos converteram com pico sete/oito sprites por linha.

Antes/depois em `out/diagnostics/alis_strong_thrust_round1/fringe_converted_comparison_01/`:
`dark_1x.png`, `dark_4x.png`, `light_1x.png`, `light_4x.png`, detalhe
`detail_before_after_12x.png` e `comparison.json`. Colunas antes/depois;
linhas guarda/extensão; pontos indicam pivôs declarados e barras indicam
intervalos opacos dos pés. A remoção do pequeno ponto cinza ficou visível no
detalhe claro/escuro. Isso não aprova identidade, escala corporal, escudo ou
animação. A conversão usa as chaves `keyposes_01`, enquanto o ramo de runtime
segue ligado a `sequence_01`; não se deve atribuir esse resultado à ROM.

Na comparação convertida, `tools/alis_support_marks.py` acrescenta marcas
sem tocar nos sprites. Gera `converted_grounded_preview/keyposes_supports_1x.png`
e `keyposes_supports_4x.png`, com recibo homônimo; pontos rosa/ciano são os
pivôs declarados, barras amarela/ciano os intervalos de pixels opacos nas
três linhas inferiores, agrupados por pé. Na face direita, a guarda tem
intervalos de Alis 61–67 e 83–92; a extensão, 60–66 e 90–100 no canvas.
O avanço adicional do pivô é zero como hipótese. Essas medições não provam
apoio físico nem movimento, e a escala neutra continua sem demonstração.

### Estudo preliminar de segmentos

`tools/alis_scale_landmarks.py` marca, por estimativa visual, ombro, quadril,
joelho e tornozelo no perfil neutro e em duas poses de `sequence_01`. Insumos,
pontos, fatores e medidas estão em
`out/diagnostics/alis_strong_thrust_round1/scale_landmarks_01/measurements.json`,
com as três fontes anotadas. Projetando o turnaround com 68/924 e a sequência
com fator nominal 4/35, os comprimentos estimados em pixels são:

| Segmento | Referência neutra | Guarda | Extensão |
|---|---:|---:|---:|
| Ombro–quadril | 18,76 | 18,34 | 16,73 |
| Quadril–joelho | 13,47 | 8,71 | 7,84 |
| Joelho–tornozelo | 15,45 | 10,77 | 11,54 |

Estes pontos são hipóteses manuais: quadril e ombro estão cobertos, armadura
não garante centro articular, e os desenhos são independentes. Ainda assim,
a divergência entre as razões sugere que aumentar a pose inteira para ajustar
as pernas pode aumentar demais o tronco. Revisar os marcos e redesenhar ou
reconstruir a anatomia se a diferença se confirmar. Não usar esses números
como calibração aprovada, alcance ou prova da ROM.

`tools/alis_weapon_landmarks.py` registra também pontos estimados de mão,
base e ponta nas quatro poses de `sequence_01`. No fator nominal atual, as
lâminas projetam aproximadamente 18,0 / 12,7 / 14,7 / 14,3 px de guarda
a recolha; a referência neutra lateral da régua v2 projeta 27,3 px.
As imagens e `measurements.json` estão em `weapon_landmarks_01/`. O contraste
entre poses sugere encurtamento e reforça a necessidade de redesenhar ou
registrar melhor as extremidades antes da animação final. São medidas manuais,
com perspectivas e poses diferentes: não equivalem a uma comparação da
katana no mesmo ângulo, não aprovam comprimentos e não definem alcance.

### Redesenho de chaves após medição

`keyposes_redraw_proportions_01.png`, SHA-256
`14b4d3d029ebf3d6b21da27d4497c284d938907f854c29b65e3209a5176f5dac`,
é uma tentativa nova de guarda e extensão com base em `sequence_01`, no
turnaround e na concept v4. A extração `.mddev/alis_strong_keyposes_redraw_extract_01.json`
usa a paleta de materiais, fator 1/9 para ambas as poses e pivôs estimados
no apoio traseiro; `alis_precondition_aspect.py --redraw` compensa o aspecto.
A conversão inicial deixou a sola da guarda um pixel abaixo de Hayato; a
receita `alis_strong_keyposes_redraw_ground_probe_01.json` ajusta seu registro
e as duas poses mais o rival terminam na mesma linha opaca Y=79. Escala e
proporção continuam experimentais. A fonte possui apenas duas poses e não foi
aplicada à sequência ou ao runtime.

Na composição estática alinhada, o conversor oficial aceita a guarda com 52
objetos e pico 8, mas rejeita a extensão com 51 e pico 9. A busca geométrica
das 64 fases de cada ator, preservando a mesma fase do rival nas duas poses,
não encontrou solução para esse par na posição e orientação testadas;
`redraw_shared_phase_probe_01.json` não é gate nem prova de outras cenas.
Pranchas de diagnóstico em `redraw_comparison_01/` mostram guarda e extensão
com Hayato, 1×/4×, fundos claro/escuro, pivôs e faixas opacas dos apoios.

Em `redraw_blade_bg_probe_01/`, 12 pixels da ponta foram separados em BG,
com reconstrução de índices exata. O simulador oficial obteve guarda 52/pico 8
e extensão 50/pico 8 nessa única posição e face. A tentativa **não é
implementação pronta**: prioridade da lâmina sobre o rival, as outras posições,
orientação oposta, poses intermediárias, palette P0, escritas da PNT, VBlank
e imagem real ainda precisam ser provados. A solução não aprova a arte nem
substitui o gate da conversão original reprovada.
Reprodução em diretório novo com `alis_blade_bg_probe.py --redraw --out ...`
gerou imagens do split, manifestos de cena e recibo byte a byte idênticos;
isso verifica reprodutibilidade dos dados estáticos, não o VDP.

A projeção offline `redraw_reach_preview_01/` usa a extensão convertida no
Y=109 da tela. À direita, pivô da Alis no chão X=64, ponta X=115 e borda do
alvo em `origem_alvo + 35`; origens do alvo 72/80/88 produzem deltas
8/0/−8 px. A linha inferior da prancha é espelho da composição offline,
não uma conversão de sprites para a face oposta. Dos 12 pixels no BG, 11/2/0
se sobrepõem ao alvo nas três posições; com BG atrás do sprite, a ponta pode
ficar encoberta. Isso precisa de decisão visual e teste em framebuffer, não
é colisão ou alcance aprovado. PNGs 1×/4× e números estão no mesmo diretório.

Prompt do redesenho: “Create original two-pose source art for an 8-bit fighting game, as a new clean drawing informed by these references. Image 1 is the acting direction, image 2 the neutral standing body and equipment proportions, image 3 Alis's approved identity and costume. Show exactly TWO separate full-body side-view poses of the SAME Alis facing right: (left) ready guard and (right) maximum horizontal sword thrust. Both planted feet on a common imagined ground, long leg segments matching image 2's anatomy, not short legs under an enlarged torso. The same neutral body scale in both poses; the thrust lowers the body by bending the knees and shifting weight forward. Retain her long brown hair, pink-and-yellow outfit, blue breastplate, gold boots and distinctive purple pink cream pointed shield. Shield stays attached to forearm with natural occlusion, same material and contour; do not invent inner brown face or expose straps. A straight blue short sword with gold hilt is continuously gripped. Keep its visible blade length the SAME in both poses, about 40 percent of standing body height, including when turned horizontal. Crisp handcrafted pixel-art clusters, bold silhouette, readable at 68-pixel standing body height, no gradients, no colored fringes. Avoid touching each other; generous transparent gap around each full figure and the sword. Real transparent background, no text, no ground line, no grid, no motion streak.”

Próximo passo: criar e revisar fontes limpas com poses e apoios registrados;
comparar as armas em mesma orientação e escala, extrair com receita e hashes,
revisar em 1× e 4× e testar timing. O consumidor já recebeu um ramo
experimental ligado à sequência exploratória; substituir pela arte corrigida,
compilar e medir com Hayato nas posições e faces exigidas. Preservar estas tentativas para
curadoria; não usar a linha de chão gerada como referência de pivô.
