# Prompt de execução contínua — 48 concept model sheets do Dr. Social

## Missão

Trabalhe como agente de produção de arte conceitual do projeto **Master of Fighters**. Produza e registre **uma concept model sheet individual para cada um dos 48 estilos candidatos** do catálogo visual do projeto, usando exatamente a forma aprovada nas folhas de referência do Dr. Ferdinand Social. Continue em sequência, sem pedir autorização a cada estilo, até todos os estilos do catálogo terem uma folha própria íntegra e uma prancha comparativa vertical composta a partir dessas folhas.

Não gere uma colagem para substituir as folhas individuais. Cada estilo precisa de uma imagem própria, gerada com tratamento visual reconhecível e diferente dos demais, e com a mesma identidade fixa do Dr. Social.

## Estado inicial e fontes de verdade

Antes de produzir:

1. Leia `/mnt/sdcard/Projects/SMSForge/AGENTS.md`, `/home/misael/.codex/RTK.md`, as instruções locais aplicáveis em `SMS_projects/master_of_fighters/.agent/`, `doc/10-memory-bank.md`, `doc/08-bible-artistica.md` e o manifesto `doc/dr_social_style_series_manifest_v1.json`.
2. Resolva `catalog.path` do manifesto a partir da raiz do workspace. Confirme o SHA-256 catalogado e conte as entradas. O estado esperado é **49 entradas**: item 1 é a âncora CPS2-Alpha-Cel; itens 2–49 são **48 estilos candidatos**.
3. Confira os artefatos, hashes, registros e commits existentes antes de gerar. Os exemplos de referência são:
   - `8052763` — piloto Dr. Social, CPS2-Alpha-Cel (âncora de identidade e formato);
   - `1afaeb0` — Dark-Gothic-Pop;
   - `2b858ff` — Late-SNK-Realism.
   O estilo 04, CPS3-Fluid-Mastery, também já tem folha e registros (`b6c6082`); preserve-o se a integridade confirmar. Não presuma que status `candidate_pending_owner_review` significa aprovado.
4. A entrada `selection_atlas` legado pode representar apenas um índice tipográfico, não uma seleção visual. Não trate esse atlas como as 48 folhas nem o use como fonte de arte. A saída final precisa ser composta das imagens individuais verificadas.
5. Calcule o conjunto de trabalho pelo manifesto e pelos arquivos/linhagens válidos. Preserve candidatos válidos. Corrija os incompletos ou inválidos em uma nova versão, sem sobrescrever a arte histórica. Não regenere folhas válidas só para mudar nomes ou repetir trabalho.

## Identidade fixa do personagem

Use a folha aprovada CPS2 como referência primária de identidade, anatomia e roupa. Em todas as imagens, mantenha:

- Dr. Ferdinand Social: adulto, rosto inteligente e determinado, cabelo grisalho penteado para trás e óculos redondos de aro de latão;
- biotipo ectomorfo alto e esguio, membros longos, ombros estreitos a médios; anatomia adulta coerente;
- sobretudo vitoriano azul/ciano, camisa branca, gravata/cravat e detalhes burgundy, calça escura e sapatos marrons;
- bengala, rapieira e bumerangue de aço ocultista;
- aparência totalmente humana: sem presas, asas, garras, transformação, traços de monstro ou redesign não aprovado.

A paleta material estabelecida em Master of Darkness é invariável. O estilo pode mudar linha, construção de sombra, acabamento, contraste e iluminação, mas não trocar as cores de identidade das peças. Violeta aparece somente no efeito do bumerangue. Não converter a imagem em paleta de outro console/jogo.

Se a descrição de um estilo sugerir chibi, corpo musculoso, monstro ou figurino alheio, adapte apenas o tratamento gráfico ao Dr. Social. A morfologia, identidade, roupa, armas e paleta fixas acima prevalecem.

## Folha oficial obrigatória para cada estilo

Cada imagem individual deve seguir a composição do piloto aprovado:

- cabeçalho com nome do personagem, sequência/ID do estilo, franquia e plataforma/era;
- selo `CANDIDATO` até revisão do proprietário;
- fundo limpo branco, creme ou cinza claro, sem cenário ou textura;
- alinhamento horizontal: frente corpo inteiro, perfil lateral estrito corpo inteiro e costas, com escala e linha de base comuns;
- close-up legível do rosto e uma pose de assinatura que comunique o personagem;
- régua relativa `H`, definida como altura da cabeça do topo do crânio ao queixo, alvo aproximado de 7,5H;
- fichas legíveis para: tipo de documento, estilo/ID, franquia, plataforma/era, lineart, morfologia, sombreamento, biotipo e opções, escala relativa, paleta/iluminação, fundo/alinhamento e detalhes fixos do personagem.

Mantenha canvas, hierarquia tipográfica, margem, escala das vistas e posição das fichas compatíveis entre folhas. Use `tools/compose_concept_model_sheet.py` e os metadados existentes quando apropriado. Texto exato deve ser aplicado por composição tipográfica, não confiado à geração de imagem.

## Regra de geração: um estilo por imagem

Para cada sequência 2–49:

1. Leia o registro completo do estilo no catálogo/manifesta: estilo base, franquia, era, lineart, morfologia e paleta/iluminação.
2. Escreva um prompt específico para aquele estilo. A folha CPS2 aprovada serve para identidade e estrutura; use folhas 02/03/04 como referências de acabamento e disciplina de layout. Não deixe uma referência de estilo sobrepor a identidade ou dominar todas as variações.
3. Gere **uma imagem dedicada para esse único estilo** usando o gerador de imagem disponível. Não peça ao modelo uma grade de dezenas de estilos e não recicle a mesma arte em vários painéis.
4. Faça o estilo ficar visualmente identificável no desenho: linguagem de linha, formas de sombra, nível de simplificação/detalhe e contraste precisam refletir o catálogo. Ainda assim, preserve rosto, cabelo, óculos, silhueta esguia, roupa, armas e funções de cor.
5. Revise o resultado em tamanho normal e ampliado antes de compor. Se ele parecer cópia de outro estilo, descaracterizar o personagem, alterar cores, inventar equipamento, apresentar anatomia/mãos/olhos defeituosos, ruído/granulação, texto ilegível, sujeira de recorte ou vistas inconsistentes, corrija o prompt e gere novamente.
6. Não pare o ciclo depois de uma folha. Registre a folha, atualize o estado e avance imediatamente para o próximo estilo pendente.

## Arquivos e proveniência

Para cada estilo novo, guardar em `data/source_art/concept_art/dr_social/`:

- PNG final composto, por exemplo `dr_social_model_sheet_05_urban_seinen_kof_v1.png`;
- arte raster original gerada, preservada sem substituição;
- prompt exato usado;
- metadados tipográficos/layout e campos do estilo;
- linhagem com SHA-256 da fonte gerada, PNG final, prompt, metadados, âncora de identidade e registro catalogado.

Em `doc/`, manter checklist de revisão artística por folha, relatório de auditoria, pedido/plano de revisão independente e estado de revisão do proprietário. Use os padrões já existentes para as folhas 02–04. Atualize o manifesto da série, a contagem de progresso e `doc/10-memory-bank.md` após cada lote concluído. Toda referência externa precisa de papel declarado e hash quando aplicável. Não declarar que conceito está convertido para SMS, pixel-quantized, integrado ao jogo, testado em ROM ou aprovado pelo proprietário sem evidência específica.

## Revisão de qualidade por folha

Antes de marcar uma folha como candidata íntegra, revisar explicitamente:

1. identidade/rosto, idade aparente e óculos;
2. anatomia adulta esguia e proporções;
3. mãos, dedos, empunhaduras e articulações;
4. rapieira, guarda/cabo, bengala e bumerangue;
5. roupa e silhueta nas vistas frente/perfil/costas;
6. cores fixas por material e efeito violeta restrito;
7. contorno contínuo, limpo, sem pixels órfãos, grão ou halo;
8. leitura dos olhos e detalhes do rosto;
9. sombras e iluminação coerentes com o estilo e com a folha;
10. alinhamento, escala 7.5H, linha de base e cinco vistas;
11. texto, labels e metadados corretos;
12. diferença visual real em relação aos outros estilos;
13. hashes, linhagem e estado do registro.

Execute as ferramentas focadas disponíveis, em especial `audit_art_review_checklist.py`, e os validadores de linhagem/proveniência existentes. Um status `pending` de revisão independente ou do proprietário deve permanecer pending; não preencha essa revisão em nome deles e não se autoaprove. Corrija falhas próprias antes de seguir. A auditoria registra cobertura e integridade, não prova verdade artística.

## Loop de execução contínua

Trabalhe pela ordem do catálogo e mantenha uma lista persistente `done / pending / blocked`:

```text
while houver estilo candidato sem folha íntegra:
    escolher a menor sequência ainda pendente
    conferir se já existe arte e linhagem válidas
    se válidas: registrar como preservada e avançar
    se ausentes/inválidas: gerar a folha individual, revisar, corrigir e registrar
    atualizar manifesto, memory bank e log do lote
    fazer commit escopado dos arquivos deste projeto/lote
    avançar sem esperar aprovação individual do proprietário
```

Se a geração falhar, tente até três revisões direcionadas para aquele estilo; nunca aceite uma duplicata só para avançar. Se persistir um bloqueio técnico, registre exatamente evidência, tentativa e causa, passe aos outros estilos independentes e retorne à fila de bloqueados antes de concluir. Não invente uma folha nem declare sucesso para satisfazer contagem.

Não faça polling de CI nem rode gates gerais em cada item. Use verificações focadas no lote e, ao final, faça uma única auditoria integral da série. Faça commits pequenos e escopados; não inclua mudanças não relacionadas nem altere trabalho sujo pré-existente.

## Entregas finais

Só conclua quando todos os 48 estilos candidatos (sequências 2–49) tiverem uma folha individual com arquivo, metadados, prompt, linhagem e revisão registrados, e a conferência final confirmar nenhuma falta, duplicação ou divergência de estilo/ID.

Além das folhas individuais, componha **uma prancha vertical única a partir dos 48 PNGs finais reais**, pela ordem do catálogo. Preserve os painéis completos; não substitua ilustrações por nomes, silhuetas genéricas, cópias ou fichas textuais. Se a dimensão do PNG exceder limites práticos do visualizador, preserve a prancha master em resolução integral e crie também uma versão de contato para navegação, identificando-a como reduzida. A prancha comparativa não substitui os 48 arquivos-fonte.

A série deve terminar como `candidate_pending_owner_review`, salvo estilos que o proprietário já tenha aprovado explicitamente. Informe número total, quais folhas foram preservadas, quais foram geradas/reparadas, hashes/commits finais e qualquer bloqueio remanescente. Nunca declarar aprovação final ou qualidade AAA sem revisão humana e evidências apropriadas.
