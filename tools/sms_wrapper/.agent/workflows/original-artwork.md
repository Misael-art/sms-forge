# Workflow: arte autoral original para projetos

## Gatilho e escopo

Use este workflow quando o usuário pedir a criação de personagem, cenário, objeto,
concept art, model sheet, sprite ou outro visual autoral para um projeto. Este
fluxo organiza a arte-fonte e sua revisão; não substitui os contratos/gates de
conversão, integração ou validação em ROM.

Para acompanhar os estados e impedir promoção implícita entre concept, sprite
e ROM, consulte também `workflows/artwork-to-rom-lifecycle.md`.
Antes da geração, aplique `workflows/artifact-organization.md`: localizar a
fonte pelo papel/ID, reservar a revisão no registro único e conferir destinos.

## 1. Identificar intenção e limitar o primeiro lote

1. Leia `AGENTS.md`, `SMS_GLOBAL.md`, o memory bank/GDD do projeto, a skill visual
   aplicável e `workflows/art-review.md`. Identifique o diretório real do projeto
   e sua estrutura existente antes de gravar arquivos.
2. Determine o asset, personagem, identidade aprovada, plataforma-alvo, mídia,
   estilo escolhido e objetivo da imagem. Use referências já aceitas para fixar
   identidade; não deduza mudanças de traje, anatomia, paleta ou equipamento.
3. Consulte o catálogo canônico `doc/curation/2026-10-07_catalogo_inicial_estilos_visuais.json`.
   Escolha o estilo indicado pelo usuário ou a direção já aprovada no projeto.
   Se a escolha for necessária e não estiver clara, apresente opções do catálogo
   de forma concisa. Não gere o catálogo inteiro para responder a um pedido de
   arte individual.
   Se o usuário ainda não especificou a direção visual, consulte a quantidade
   vigente no catálogo; o catálogo não limita a escolha.
   Apresente os critérios mínimos para orientar a decisão: mídia/tipo de traço,
   obra/franquia e era de referência, e artista ou estúdio (ou ausência de
   crédito individual confirmado). Se a intenção já estiver clara, siga sem
   interromper o pedido com uma pergunta redundante.
4. O padrão é **um concept/model sheet por ciclo**, com checkpoint para o usuário
   revisar antes de gerar a próxima variação. Um lote maior só começa quando o
   usuário pedir comparação/ampliação explicitamente; então proponha um lote
   pequeno e identifique o custo de geração antes de iniciá-lo. Não execute
   automaticamente dezenas de gerações porque há dezenas de estilos listados.

## 2. Manter o catálogo rigoroso e expansível

O catálogo é um índice de direções visuais, não um conjunto de presets validados.
Para cada estilo, preserve ID único, `catalog_index` estável, obra/franquia de
referência, edição quando conhecida, plataforma/era, medium, linguagem de
lineart, morfologia, luz/paleta, artista/estúdio de referência e papel,
assinatura visual distinta, referências autorizadas e seu papel,
proveniência/hash, estado de validação e observações de adaptação ao projeto.
Se não houver atribuição individual confiável, registre isso explicitamente;
não preencha o campo com uma suposição. Diferencie o autor de uma ilustração
promocional do autor dos sprites ou da equipe do jogo.

Ao propor estilo novo:

- procure duplicatas e use IDs estáveis;
- obtenha fonte identificável e registre URL/arquivo, edição/plataforma/era,
  hash e quais propriedades a fonte pode esclarecer;
- separe fatos da fonte de inferências e decisões autorais;
- registre a nova entrada como candidata não validada; não marque como estilo
  validado só por ter uma descrição textual;
- inclua-a no catálogo canônico após curadoria e aprovação do proprietário,
  sem apagar ou renumerar entradas históricas.

A descrição do catálogo nunca autoriza copiar personagens, logos, cenários ou
assets de terceiros. Ela orienta características gerais de acabamento e desenho.

## 3. Congelar identidade e preencher o contrato visual

Antes da geração, escreva um inventário curto de invariantes do asset: idade,
rosto, biotipo, silhueta, cabelo, roupa, marcas, símbolos, equipamentos, paleta
por material, escala e itens ainda abertos. Separe a identidade do personagem
do estilo de renderização.

Para personagem, use como padrão aprovado o concept/model sheet com:

- vista de frente, perfil estrito e costas em corpo inteiro;
- close detalhado do rosto;
- uma pose de assinatura que revele personalidade/silhueta;
- vistas ortográficas alinhadas em baseline e escala comum;
- régua relativa documentada (`H` = coroa do crânio ao queixo, se aplicável);
- fundo neutro limpo;
- campos legíveis de tipo de documento, índice/nome do estilo, franquia e era,
  medium/lineart, artista e escopo da referência, assinatura visual,
  morfologia, sombreamento, biotipo, escala e paleta/iluminação.

Use o formulário que o proprietário aprovou para o projeto. Se não houver um,
proponha o padrão acima e congele sua versão após aprovação. Não deixe textos
críticos para a imagem generativa: aplique rótulos e fichas com o compositor do
projeto para evitar texto inventado ou ilegível.

O prompt da arte-fonte deve pedir somente a ilustração: sem título, rótulo,
régua, linha de base, moldura ou ficha. Esses elementos são responsabilidade
do compositor e devem aparecer uma única vez. Após compor, confira a prancha
inteira e os detalhes em escala nativa: vistas, armas e pés não podem cruzar
rótulos; régua e baseline não podem duplicar guias que tenham escapado para a
arte-fonte; texto deve caber em cada cartão sem tocar a borda.

## 4. Gerar incrementalmente e preservar proveniência

Para fonte de sprite em linguagem CPS2, separar quatro representações:
concept/model sheet (identidade), fonte autoral (desenho/atuação), saída SMS
(tradução limitada) e framebuffer (apresentação). CPS2 descreve a direção
visual escolhida; não certifica anatomia, resolução ou paleta do arquivo.
Definir simplificações intencionais de olhos/rosto, dedos/pega, dobras e
equipamento antes da geração. Contorno, clusters e planos sombra/base/luz têm
papéis por material; preservar o preto opaco quando outra entrada é transparente.

Comparar a amostra com referências aprovadas em escala comum, sem normalizar
cada personagem pela própria bbox. Medir corpo sem cabelo/arma e equipamento
separadamente. Registrar escala, canvas, pivôs, paleta e duração como parâmetros
do personagem/cena; conferir os valores atuais no GDD/decisões, não em receitas
históricas. Converter uma amostra cedo e revisar quais detalhes sobrevivem.
Para golpes, seguir `skills/sms-sprite-animation.md` antes do acabamento.

Uma iteração registra causa observada, delta pretendido e invariantes; depois
confere delta real e reinspeciona a pose inteira. Edição de lâmina pode alterar
braço/rosto fora do pedido. Se o contrato limita ROI, comparar pixels fora da
região contra a fonte congelada, além da revisão visual. Não atribuir economia
ao método sem contagem de tentativas/custo comparável e mais de um caso completo.

1. Gere uma imagem para o estilo escolhido e revise antes de seguir. Para cada
   estilo, use prompt próprio, com a referência aprovada para identidade e as
   características de estilo separadas. Declare qual obra/peça e qual papel do
   artista estão servindo de referência; traduza a referência em traços
   observáveis que diferenciem a direção escolhida. O nome do artista é
   atribuição e contexto, não instrução para copiar uma assinatura exata. Não
   transforme uma única imagem em dezenas de variações repetidas nem apresente
   um painel com lacunas como se contivesse folhas completas.
2. Faça duas passagens: (a) pose/anatomia, seguindo cada membro da inserção no
   torso/ombro até braço, cotovelo, antebraço, punho e mão; confirme articulações,
   lado, perspectiva, apoio e encaixe das armas; (b) coesão visual, verificando
   se a assinatura artística declarada está legível, distinta das referências
   próximas e consistente entre as vistas. Depois revise rosto/olhos, roupa,
   paleta material, contorno, textura acidental, alinhamento, escala, recorte e
   legibilidade. Corrija uma causa por iteração e retenha versões rejeitadas.
3. Quando o usuário pedir uma revisão, congele o SHA da matriz aceita e
   transforme cada apontamento em um delta explícito: defeito observado,
   alteração pretendida e evidência que fechará o ponto. Liste também os
   invariantes que não podem mudar (identidade, face, biotipo, paleta, escala,
   estilo, armas, vistas preservadas). Gere uma nova revisão, sem sobrescrever
   a matriz, e faça a segunda passagem completa após a alteração. Se fontes do
   jogo discordarem sobre itens, mantenha a divergência aberta e identifique
   visualmente o que é equipamento autoral e o que é referência de inventário;
   não transforme uma imagem em decisão de moveset.
3. Guarde o material sob o diretório-fonte do jogo, seguindo sua convenção. Para
   projetos novos, use:

   ```text
   SMS_projects/<project>/data/source_art/concept_art/<asset_id>/<style_id>/vNN/
     references/       # fontes autorizadas ou registros/links e hashes
     prompt.txt        # prompt exato e limites de cada referência
     generated_raw.png # geração original intacta
     model_sheet.png   # versão composta candidata
     metadata.json     # estilo, layout, paleta, escala e versão
     lineage.json      # origens, papéis e SHA-256 dos arquivos
     validation/       # checklist, relatório, review request/plan, decisão
   ```

   Adapte somente se o projeto já tiver estrutura equivalente; preserve arquivos
   existentes e não faça migrações em massa. Não grave concepts candidatos em
   `res/`. Atualize `doc/asset_provenance_manifest.json` quando a arte passar a
   ser asset de jogo integrado, não apenas por existir uma imagem-fonte.

## 5. Revisar e marcar status com precisão

Use `workflows/art-review.md` para cada concept/model sheet. Inclua e verifique
os eixos de escopo/atribuição artística, assinatura visual distinta,
continuidade anatômica das articulações, coesão visual e `document_and_layout`
da folha composta (§104; não dispensável por N/A). Vincule checklist e
relatórios ao SHA-256 da imagem revisada. O autor não aprova a própria arte. Uma
folha pode ser registrada como `candidate_pending_owner_review`, mas não como
aprovada até decisão explícita do proprietário. Revisão do concept não aprova
pixel art, animação, integração, paleta SMS, build, ROM, emulador ou qualidade
AAA.

Quando houver aprovação, preserve o registro da decisão e só então planeje a
etapa seguinte (revisão de sprites/conversão/integracão) pelo workflow de asset
apropriado. Mantenha as versões candidatas e aprovadas distintas.

Para promover uma folha revisada: exija checklist completo, revisão independente
hash-bound sem blockers e decisão explícita do proprietário. Registre a decisão
`sms_artifact_decision_v1` no escopo exato `model_sheet`, com todos os arquivos
e SHA da revisão. Atualize o registro único: nova revisão `approved`, ponteiro
aprovado para ela, candidata nula quando não houver outra candidata e matriz
anterior `superseded`. A aprovação cobre somente a folha conceitual; não aprova
sprites, moveset, animação, conversão SMS, integração ou ROM.

Depois da promoção, mantenha na raiz do diretório do personagem somente a folha
ativa e seus sidecars canonizados (metadata, lineage e prompt). Mova matrizes
aprovadas substituídas para `historical_approved/` e exercícios/candidatas para
`review_drafts/`, sem apagar evidências. Mantenha conceitos aprovados de outro
papel em `approved_records/<papel-ou-revisao>/`. Atualize os caminhos no registro
e nos manifestos afetados; registre cada mudança em mapa reversível com SHA de
origem/destino. Não altere o conteúdo artístico durante uma simples organização.

## 6. Memória e retomada

Sele a revisão e atualize os heads candidata/aprovada do registro antes de
gravar o checkpoint na memória. Não inferir qual arquivo está vigente por uma
busca de `vNN`; preserve os rascunhos como histórico com origem e motivo.

Após cada ciclo, atualize o memory bank do projeto com o caminho, estilo, SHA,
status, decisão do usuário e próximo passo. Se houver aprendizado reutilizável,
faça curadoria via `workflows/curation-learning.md`: atualize JSON canônico,
regra numerada, ledger e este workflow/skill. Em caso de interrupção, retome do
manifesto e continue somente o escopo autorizado, sem re-gerar material íntegro.
