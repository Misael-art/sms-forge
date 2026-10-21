# Dr. Social — diretriz de reconstrução da sprite sheet v08

**Estado:** diretriz ativa para reconstrução; a arte v07 está rejeitada pelo dono.
**Escopo:** sprite sheet de movimentos básicos, 61 poses, Master System.
**Matriz única de identidade:** `data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`.

## Decisão e causa

A v07 não deve ser usada como arte aprovada nem como referência cromática. O dono
observou perda da hierarquia do figurino, cabelo cinza com variação avermelhada,
casaco convertido em massa ciano/verde-azulada e sombra granulada sem direção.
As correções por média, luminância, proximidade espacial ou substituição pela cor
mais próxima não resolveram a leitura visual; em alguns casos, apagaram diferenças
entre materiais. A v07 fica preservada apenas como evidência rejeitada.

## Invariantes de forma e sequência

- Preservar os 61 IDs, a ordem, o conteúdo semântico e a quantidade por sequência:
  `4/8/8/8/5/8/8/8/4`.
- Preservar o canvas de 80×80 por pose e a grade 8×9 enquanto a revisão for de cor.
  Qualquer correção anatômica ou de pose deve ser registrada como delta separado.
- Usar exclusivamente a model sheet CPS2-Alpha-Cel v4 para identidade, figurino,
  bengala e anatomia. A v07/v06 pode ser consultada apenas como dado histórico,
  não como autoridade de cor, luz ou desenho.

## Paleta mestre fechada

Usar uma única paleta indexada em todos os 61 quadros, com os papéis abaixo e sem
adicionar cores. Índice 0 é transparência; a cor magenta de preview não é tinta.

| Índice | RGB | Papel permitido |
|---:|---|---|
| 0 | transparente | fundo/recorte; preview em magenta puro `#FF00FF` |
| 1 | `#000055` | contorno geral e separações estruturais |
| 2 | `#FFAAAA` | pele iluminada |
| 3 | `#AA5555` | sombra rosada da pele; proibido no cabelo e no tecido |
| 4 | `#55AAFF` | luz do casaco/sobretudo |
| 5 | `#00AAAA` | base do casaco/sobretudo |
| 6 | `#005555` | sombra do casaco/sobretudo |
| 7 | `#FFFFFF` | luvas, camisa/gola e haste da bengala, dentro dos contornos |
| 8 | `#AAAAAA` | cabelo grisalho claro e dobra cinza autorizada |
| 9 | `#555555` | segundo tom do cabelo grisalho e sombra cinza autorizada |
| 10 | `#550000` | couro/castanho escuro, principalmente botas e acessórios de couro |
| 11 | `#AA0055` | gravata/lenço bordô e detalhes de bota aprovados |
| 12 | `#FFFF00` | pomo/empunhadura dourada da bengala; fita de cabelo somente se a matriz a confirmar |

O cabelo deve usar os tons 8 e 9, com contorno 1. Nenhum pixel 3, 10 ou 11 pode
ser classificado como cabelo. A roupa usa os tons 4, 5 e 6 em planos contíguos.
Bordô não é permitido em punhos, casaco ou bengala. Branco e amarelo ficam
confinados às regiões declaradas; uma coincidência de RGB fora da região é falha.

## Sombreamento e edição

- Cel shading de borda dura: luz, base e sombra são massas contíguas por material;
  a transição do casaco é direta entre planos, sem dithering, ruído ou pixels
  alternados para simular textura.
- Cada marca de sombra deve seguir volume, dobra e direção da pose. Não uniformizar
  o casaco nem substituir uma cor por outra apenas porque está mais próxima no RGB.
- Componentes coloridos de 1×1 ou 1×2 são alertas para decisão humana. Não os
  remapear automaticamente: registrar quadro, coordenada, cor, material esperado,
  decisão e delta. O contorno e detalhes faciais também precisam de revisão visual.
- Permanecem proibidos: blur, antialias, média global/de vizinhança, distância
  espacial/cromática para escolher cor, filtro de luminância e quantização por
  aproximação RGB. Não usar ImageGen nem difusão.
- **Emenda aprovada pelo dono em 2026-10-12:** autorizar reconstrução determinística
  por máscaras explícitas de material/região aplicadas à geometria v07 (grade
  fixa 8×9, células 80×80, 61 poses). Cada máscara deve ser exportada, nomeada e
  auditável por pose; regiões sobrepostas ou sem classificação não podem receber
  pintura automática.
- Algoritmos de cluster/Cel Shading podem agrupar ou substituir tons **somente
  dentro da máscara explícita correspondente**, usando exclusivamente os índices
  da rampa daquele material. Não atravessar contornos, transparência, fronteiras
  entre materiais ou os 80×80 de cada quadro. Empates e pixels sem máscara devem
  ser registrados como pendência, não resolvidos por cor mais próxima.
- Preservar fonte congelada/SHA, canvas, índices transparentes, silhueta e ordem
  dos quadros. Guardar máscaras por material, log dos pixels alterados, prancha
  1×/4× e relatório reproduzível de conformidade.

## Revisão obrigatória antes de pedir aprovação

1. Entregar preview 4× nearest-neighbor de idle quadro 1, avanço quadro 1 e queda
   quadro 2, mais a prancha completa. Exibir as mesmas regiões em 1× para confirmar
   leitura no tamanho real.
2. Conferir manualmente o cabelo em 61/61 quadros: somente cinzas 8/9 e contorno 1;
   nenhuma variação avermelhada/castanha. Reportar cobertura e exceções por quadro.
3. Conferir manualmente todos os pixels brancos e amarelos em 61/61 quadros. O
   relatório deve mostrar zero fora das zonas permitidas: branco em luvas,
   camisa/gola ou haste da bengala; amarelo no pomo/empunhadura e, se confirmado
   pela matriz, fita do cabelo.
4. Revisar continuidade dos blocos do casaco, rosto, mãos, pega/terminal da bengala,
   recorte, contorno, anatomia e sequência em todos os quadros. Nenhum achado
   estatístico substitui a inspeção visual.
5. Rodar o checklist hash-bound e pedir revisão independente. A arte permanece
   candidata até decisão explícita do dono; não copiar para `res/` nem ROM antes.

## Delta de revisão solicitado pelo dono

| Observação | Correção exigida | Evidência de fechamento |
|---|---|---|
| Casaco virou massa ciano e salpicada | Reconstruir planos de luz/base/sombra do figurino, sem filtros | Amostras 1×/4× e inspeção de todas as poses |
| Cabelo varia entre cinza e avermelhado | Fixar dois cinzas e contorno em todos os quadros | Auditoria manual de cabelo 61/61 e zero cores proibidas |
| Sombra granulada e sem direção | Pintar blocos contíguos por dobra/material | Review de clusters, direção e continuidade 61/61 |
| Paleta branca/amarela/bordô vaza de seu papel | Restringir cada acento à zona permitida | Relatório por cor/região com zero ocorrências fora da zona |

**Não alegar:** edição manual concluída, qualidade AAA, arte aprovada, orçamento
de hardware, integração `res/` ou ROM. Neste registro foi iniciada a diretriz;
a nova pintura v08 ainda não foi produzida. A tentativa exploratória de
12/10/2026 com geração de imagem foi rejeitada tecnicamente: saiu em 1182×1330,
com fundo opaco e 287.407 valores RGBA distintos; não preservou a grade 8×9
auditável. Ela está arquivada em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_imagegen_rejected/`.
Não criar previews 1×/4× nem declarar conformidade sem uma fonte que preserve
os limites dos quadros e as cores exatas. Relatório: `doc/curation_candidates/2026-10-12_dr_social_v08_imagegen_trial_rejection.json`.

## Emenda de execução por máscaras (2026-10-12)

O dono autorizou substituir a rota de tentativa generativa por máscaras explícitas
e processamento determinístico, sem ImageGen/difusão. A matriz de geometria é a
folha v07 congelada; a edição fica restrita aos pixels opacos pertencentes às
máscaras. O agrupamento de tons é permitido dentro das máscaras e deve preservar
os papéis da paleta. Cada máscara e cada delta precisam ser arquivados junto à
candidata. Zonas amarelas que conflitem com a identidade aprovada (óculos de
latão) permanecem sob confirmação do dono; a tabela v08 ainda limita amarelo ao
pomo/empunhadura da bengala e à fita somente se confirmada pela referência.
