# Padrão de prova técnica de conversão e modelo de sprite — v1 (histórico)

**Estado:** REJEITADO como prancha de inspeção em 2026-10-09. A grade 8×8 foi desenhada sobre a ampliação do personagem e alterou visualmente os pixels apresentados. A fonte não tinha as linhas, mas a prova tornou-se inadequada para revisão. Consulte `asset_conversion_proof_standard_v3.md`; não reutilize o compositor v1 para novas entregas.  
**Escopo:** contrato visual e inventário de pixels/tile para assets do Master System  
**Não substitui:** contrato de runtime, orçamento de VRAM/RAM, metasprite, ROM binding ou validação em emulador

## Objetivo

Cada personagem ou item que sair de uma arte aprovada recebe um contrato próprio e uma prancha de prova. A prancha liga a identidade aprovada ao arquivo pixelado no tamanho nativo e torna observáveis a escala, a paleta, o recorte e a ocupação em tiles 8×8.

O arquivo de saída é uma prova técnica de arte em data/source_art/. Ele não é promovido automaticamente para res/. A contagem do arquivo de imagem também não afirma quanto da VRAM ficará residente: isso depende do formato de runtime, pools, banking e política de troca de quadros do projeto.

## Entradas obrigatórias por asset

1. Referência de concept/model sheet aprovada, caminho e SHA-256.
2. Fonte do sprite/objeto que será avaliada, caminho, SHA-256 e proveniência.
3. Tipo (character, item, prop, stage_piece), papel no jogo, estilo/identidade e personagem ou objeto.
   Registrar o estilo/referência da concept e separar essa referência do acabamento técnico de pixel art SMS.
4. Contrato de escala do GDD ou do roster: alvo/faixa, baseline e pivô. Se não estiver definido, declarar pending; não inventar um alvo.
5. Contrato de paleta do personagem/item e a paleta efetivamente usada pelo PNG.
6. Geometria da folha: largura/altura nativa de quadro, quantidade de linhas/colunas, ordem de leitura e estados/ações.

## Conteúdo obrigatório da prancha

- Mesmo vocabulário visual de documento do concept model sheet: título, identificação do asset, estado, régua relativa, cartões informativos e alinhamento limpo.
- Nome/índice do estilo da concept e descrição da tradução para pixel art SMS, sem sugerir que a paleta SMS por si só prova fidelidade estética.
- Sprite sem reescala artística, mostrado em 1× e ampliado apenas por nearest-neighbor. A ampliação deve ser rotulada.
- Um quadro escolhido com grade alinhada a blocos de 8×8, mapa de células ocupadas, baseline/pivô e caixa opaca. Informar se a caixa inclui arma, cabelo, capa, efeito ou outro equipamento.
- Folha completa de quadros em ordem de leitura, quando o asset for animado. Mostrar canvas e baseline comuns.
- Dimensão nativa do canvas/quadro, bbox visível, faixa-alvo do projeto, diferença numérica e estado da revisão de escala.
- Tabela da paleta realmente usada: índice, função/material quando declarada, RGB e validação da grade RGB de 6 bits. Índice 0 é transparência e não conta como cor útil; teto: 15 cores úteis.
- Um fundo de inspeção puro, escolhido entre magenta #FF00FF, verde #00FF00 ou azul #0000FF, conforme contraste e colisões com a paleta. O relatório registra a escolha e deixa explícito que o fundo não pertence ao PNG do asset nem à paleta do jogo.
- Inventário de tiles com o método de contagem definido abaixo.
- Referências, hashes, status e gates seguintes. O status deve distinguir arte candidata, aprovação visual, integração e validação de ROM.

## Regra de contagem de tiles

O padrão de contagem usa tiles gráficos de 8×8 pixels:

- canvas_tile_slots_per_frame: (frame_width / 8) × (frame_height / 8), incluindo células transparentes.
- occupied_tile_cells_per_frame: células 8×8 com pelo menos um pixel opaco.
- unique_tile_patterns_per_frame: padrões 8×8 opacos distintos dentro daquele quadro, comparados pelos índices de pixel; células totalmente transparentes são omitidas.
- occupied_tile_placements_all_frames: soma das células ocupadas nos quadros.
- unique_tile_patterns_all_frames: padrões 8×8 opacos distintos em toda a folha, comparados exatamente pelos índices. A contagem não presume reaproveitamento por espelhamento.
- raw_4bpp_bytes_per_pattern: 32 bytes por padrão 8×8 em 4bpp; informar bytes por quadro e para padrões únicos da folha.

Esses números são inventário da arte. Não são quantidade de objetos da SAT, custo de metasprite, uso total de VRAM, custo de upload por VBlank, custo de ROM comprimida ou aprovação do limite por scanline. Esses eixos precisam de contratos e gates de runtime próprios.

## Fundo de inspeção e leitura

O compositor escolhe uma das três cores-key permitidas que não esteja na paleta opaca e maximize a distância média para as cores usadas. O revisor ainda confirma visualmente que o fundo distingue contornos e materiais. Se nenhuma cor-key der contraste adequado, registrar o bloqueio e pedir uma decisão; não trocar por cinza/checkerboard silenciosamente.

O fundo é somente de inspeção. Os PNGs-fonte continuam com transparência real. A prancha final deve ser vista no tamanho nativo e em nearest-neighbor 4× ou maior; linhas da grade são sobreposição de leitura e nunca alteram a imagem-fonte.

## Reprodução

O compositor reutilizável é tools/compose_sms_asset_conversion_proof.py. Ele lê a folha indexada e o manifesto de paleta, calcula a bbox e os padrões exatos 8×8, escolhe o fundo-key e produz a prancha e o relatório JSON. A folha ampliada é apresentação; os dados vêm da fonte nativa.

Para novos assets, passar caminhos de concept, fonte pixelada, contrato de origem, paleta e saída. Registrar também tamanho de quadro, grade de quadros, quadro de destaque e faixa de escala do GDD. O compositor não altera a fonte e não aprova a arte.

## Revisão e promoção

Antes de chamar a arte de aprovada, preencher e conferir:

- os micro-eixos obrigatórios de pixel art: pixel_clusters, face_detail_readability, outline_and_cutout, material_shading, hand_weapon_attachment, equipment_geometry, frame_pose_integrity e native_size_readability;
- fidelidade à referência aprovada e aos papéis de cor;
- proporção relativa, cabeça/torso/pernas, massa dos membros e baseline;
- rosto/olhos, mãos/orientação, juntas e cadeia mão → pegada → arma;
- fixação e perspectiva dos acessórios;
- clusters por material, contorno/recorte, pixels soltos e leitura em 1×;
- consistência de todos os quadros, pivô e integridade da ação;
- exatidão dos campos, dimensões, paleta e contagens da prancha;
- revisão independente hash-bound e decisão do dono.

Qualquer eixo fail reprova a candidata; pending impede promoção. O autor não aprova o próprio trabalho. A aprovação desta prancha não valida carregamento no jogo, runtime, orçamento, FPS, áudio ou ROM.

## Piloto Dr. Social

O primeiro ensaio usa dr_social_idle_guard_12f_sms_96px_v9_clean.png, estado registrado no contrato de origem: candidato com revisão visual do dono pendente. O quadro 09/12 foi escolhido por ter bbox opaco de 65×82 px, próxima da faixa GDD de 78–82 px; a bbox inclui equipamento e não é uma medida isolada do corpo.

Resultados derivados da fonte: canvas 96×96 (12×12 posições 8×8), 62 células ocupadas e 62 padrões únicos no quadro escolhido; sequência 12 quadros com 706 colocações ocupadas e 690 padrões únicos exatos. O PNG usa 12 cores úteis mais índice 0 transparente; os canais RGB estão na grade {0, 85, 170, 255}. O fundo de inspeção escolhido é verde puro #00FF00.

A sequência completa de 690 padrões é contagem de arte, não declaração de que todos serão residentes ao mesmo tempo. O contrato de runtime do projeto ainda não define o consumidor das tabelas de mugen2sms, os pools VRAM/RAM ou a política de banking/carregamento. Por isso o piloto permanece em data/source_art/asset_conversion_proofs/ e não entra em res/.
