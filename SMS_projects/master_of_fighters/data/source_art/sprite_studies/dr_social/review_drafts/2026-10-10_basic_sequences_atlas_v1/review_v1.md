# Dr. Social — atlas básico de animações — pré-revisão

**Status:** rascunho visual, reprovado na checagem de contorno/paleta, não promovido.

A imagem proposta agrupa nove sequências básicas do contrato: idle, avanço,
recuo, pulo/aterrissagem, abaixar, dash, queda, rolagem/levantada e defesa.
As contagens planejadas somam 61 poses-fonte. A imagem sugere a ordem das linhas,
mas não comprova uma grade exata de células nem a identidade de cada pose.

## Pré-revisão observada

- A identidade e o figurino geral permanecem reconhecíveis.
- Persistem halos azul/ciano em torno dos sprites, contrariando a regra de
  contorno limpo e sem ruído.
- A imagem tem 256 níveis de alpha, 716.811 pixels parcialmente transparentes
  e 1.390 cores RGB totalmente opacas. Portanto, não cumpre a paleta declarada
  de 12 cores nem o recorte binário exigido para pixels de sprite.
- Canvas 1323×1189 não comprova células 80×80. A grade, pivôs, contagens reais
  por quadro e recorte de cada pose continuam sem verificação.

Foram feitas duas revisões da imagem para corrigir halo, suavização e paleta;
elas não resolveram os defeitos. O PNG permanece apenas neste diretório de
rascunhos, fora da linhagem canônica de sprites e de `res/`.

O registro machine-readable está em [`review_v1.json`](review_v1.json). A
referência de identidade usada foi o model sheet aprovado #01. Não houve revisão
independente, promoção, vínculo asset→ROM nem validação em emulador.
