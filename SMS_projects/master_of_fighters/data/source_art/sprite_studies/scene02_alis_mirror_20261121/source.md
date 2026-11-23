# Pranchas do espelho de Alis

As pranchas novas foram produzidas com ImageGen nesta sessão a partir do
concept v4 autorizado e do estudo de posturas de 21/11. Cada desenho
permanece isolado com transparência. Os pacotes históricos de combate em
pé, marcha e salto vêm da prancha construída para a b32.

| Fonte | Uso | SHA-256 |
|---|---|---|
| low.png | Quatro linhas de preparação, contato e recuperação abaixada | f2a10fdbd8526f87287017089589efa8200f28fc34b43f1e32cc539966920271 |
| air.png | Quatro linhas de preparação, contato e recuperação no ar | 3d0ac225d4116d6ea3afa64e01686cc614e71581cdcc353cd4f69bee3255ac2b |
| air-shield.png | Revisão do contato de soco aéreo. Braço e escudo lideram o movimento e a lâmina recolhe. | d8b573ee096a047b2bc2a0826631a1330ec3bf34312bb74f10048059b4928459 |
| reactions.png | Cabeça, abdômen, base baixa, três impactos de escudo, queda, chão e levantada | 03b47fe4bdce921cb7a5ff90786f73df7a5854b86af5180cfb79cc90c240611d |
| turn.png | Trilha de apoio e giro da atacante e trilha de desequilíbrio da vítima | 657d02f43f43b8158c45474f90b3d0521c7b07e20b1c27dba45c55e25c5c4f18 |

A conversão usa recorte por alfa, redução nearest-neighbor, paleta SMS
compartilhada e pivôs em pixels da arena. Na montagem nativa,
o chute aéreo curto, o início de queda e as poses da vítima presa
são ajustados uniformemente para caber na faixa de quatro sprites
por atriz. A pose deitada usa 52 px de comprimento. As medidas
do material convertido continuam em revisão de proporção e encaixe.
O resultado de cada pacote e o hash das fontes ficam no recibo de
montagem da ROM. As pistas de espada e escudo reaproveitam a composição
PSG original do projeto registrada na matriz de Hayato × Alis.

[Concept autorizado](../../concept_art/alis_landale/alis_concept_sheet_v4.png) ·
[Estudo de posturas](../scene02_alis_postures_20261121/source.md).

## Reexposição aérea e queda

As novas poses de Alis usam o concept v4 como referência no ImageGen.
Preservam a paleta compartilhada e o ponto de apoio, com redução uniforme
e empacotamento de quatro sprites por linha por atriz em voo.

| Fonte | Uso | SHA-256 |
|---|---|---|
| air-b40.png | Preparação e recuperação no ar, contatos dos dois chutes | 5aaaf46a5288448fe66286147b745233e04a59ff46d4d77ef3284b417ad9dcb3 |
| air-contact-b40.png | Escudo projetado no contato, célula esquerda | 873c4c06b7f588e8b2cfe04d517d4ee6a3d68db34f915bbde0278d5121fc9786 |
| air-sword-b40.png | Lâmina em descida à frente do corpo | 0093cb019144e6a4f6f50aca66e01f4a6279091f995d6df16450181f701a0ff3 |
| floor-b40.png | Corpo deitado, cabeça apoiada na altura do chão | 799f98238217be0049986aadf86d0c0842fbcd0041723a1c4b370ee65863e5d7 |

A pose de cabeça erguida da prancha `reactions.png` passa a ser o
primeiro quadro da levantada. A figura deitada é espelhada na conversão
para manter o lado da cabeça nesse corte e usa o mesmo plano do chão.

## Revisão de punho, tecido e contorno

O ImageGen retocou as poses autorais de contato em voo e a pose de
repouso. A montagem usa os dois contatos da primeira prancha e o
primeiro desenho da segunda, com a cabeça apoiada. A pose de elevação da
cabeça segue ancorada ao mesmo piso.

| Fonte | Uso | SHA-256 |
|---|---|---|
| air-grips-b48.png | Contato com escudo à esquerda e espada à direita, com punho e empunhadura mais definidos | 91961cd4232030b96eeabfb7a56bb11967cd43523584df7511dc8ead37b13b50 |
| floor-material-b48.png | Corpo estendido com túnica saturada e contorno legível no primeiro desenho | ad0aeeb1225acb59520cc9f0914a158af39d2d0056bca060fef0662b229741e8 |

A conversão encaminha amostras rosadas à rampa de tecido antes de
quantizar e usa traços escuros existentes na fonte para recuperar a
borda quando a amostra mais próxima cai num brilho. O ajuste de
contorno trabalha dentro da máscara opaca. No soco de guarda em pé,
seis pixels do bracelete herdado recebem os dourados da guarda.

## Escala de cinco poses

A b49 reusa as fontes das poses de contato aéreo, queda, repouso e
primeira levantada. A redução uniforme dos dois contatos resulta em
53 px de altura. A queda usa a silhueta em diagonal com 42 × 36 px
e mantém toda a figura em sprites. O repouso mede 63 × 11 px. Na
primeira levantada, a fase de amostragem de 0,4 px conserva a leitura
do contorno e o orçamento do fundo em 56 × 18 px. O repouso e a
levantada terminam na mesma linha Y=143.

## Revisão de 22/11 · lâmina, chute aéreo e puxada com escudo

O [concept v4](../../concept_art/alis_landale/alis_concept_sheet_v4.png)
é a referência de identidade para todos os quadros revistos. A tentativa
b50 usou uma prancha intermediária que reinterpretava a lâmina ciano
como faixa diagonal. Suas fontes ficam no lote de diagnóstico. A nova
trilha preserva o peitoral índigo, as ombreiras prateadas, a túnica rosa
com friso dourado, as meias brancas, o escudo pontudo e a espada na mão.

| Fonte | Uso | SHA-256 |
|---|---|---|
| shield-grip-concept.png | Alcance, puxada, apoio e empurrão. Lâmina baixa na mão e escudo à frente. | 093939636afb25df93a6fb691d54b6af05a6ea3408bebbce7dc74ecffae5d163 |
| shield-stagger-concept.png | Captura, aproximação e perda de equilíbrio. O primeiro quadro também serve de retomada da guarda. | 337f72e9cc6221c93ee919b524426ecab04b07ce504c2954315496d9cd4666c1 |
| air-kicks-concept.png | Preparações, contato em descida e recuperações. | 9cb3bced1df77a927a88097ba07aa858fcbd4c335fb2664441396500324ebf8f |

As pranchas foram produzidas com ImageGen a partir do concept v4.
O roteiro de edição definiu alcance, puxada, apoio e empurrão com
a espada baixa. Para a rival, definiu aproximação, flexão e dois
passos de desequilíbrio para trás. Para o chute, definiu joelho armado,
extensão da bota e recolhimento. O contato curto retém a décima célula de
`air-b40.png`, convertida em 50 px com a classificação de material
revista. A extensão da bota dessa célula cabe em quatro sprites por
linha. A conversão mantém a rampa física da túnica de cada traje e
distingue a lâmina ciano, o índigo da armadura e a pele iluminada.

## b53 · Recolhimento do escudo e correções locais

[shield-recovery-b53.png](shield-recovery-b53.png) foi produzida com
ImageGen a partir do concept v4 e da pose de empurrão desta prancha.
O pedido visual usa a mesma armadura e o mesmo tamanho de cabeça, com
a perna da frente ainda apoiada, o peso voltando ao centro, o escudo
recolhido e a espada baixa e separada. SHA-256
`0063a9bcf929d4b2b2f97d84521ef1547f983b2ad18bb3877b86870a6b745f02`.

Os chutes fortes e a preparação aérea comum conservam os desenhos e
recebem uma correção por região no tecido, na pele e nos braceletes.
O metal das ombreiras conserva a rampa cinza. O agachamento e a guarda
baixa usam suas células da prancha de posturas com redução uniforme
e a sola na linha 143.
