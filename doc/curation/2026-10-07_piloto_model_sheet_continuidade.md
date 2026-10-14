# Piloto: model sheet para continuidade visual

**Status:** promovida em 2026-10-08 ao workflow canônico `original-artwork.md`;
o registro do piloto abaixo permanece como evidência histórica do padrão.

**Objetivo:** verificar se uma folha de referência fixa a identidade visual do
personagem com detalhe suficiente para orientar imagens derivadas sem deriva de
anatomia, figurino, marcas, símbolos ou equipamentos.

## Composição da folha

1. **Frente, corpo inteiro:** vista neutra e legível do traje e da anatomia.
2. **Lado, corpo inteiro:** perfil que esclareça volume, camadas e posição dos
   equipamentos.
3. **Costas, corpo inteiro:** vista que fixe o desenho posterior do traje,
   cabelo, marcas e acessórios.
4. **Close do rosto:** detalhe ampliado para fixar formato facial, olhos,
   cabelo, expressão-base, marcas e acessórios da cabeça.
5. **Pose de identidade:** pose expressiva que comunique a personalidade e a
   silhueta do personagem sem alterar o desenho estabelecido nas vistas.

## Inventário de invariantes

Antes da geração, listar os detalhes que precisam sobreviver em todas as
imagens derivadas:

- proporções, idade aparente e características anatômicas;
- estrutura do rosto, olhos, cabelo e marcas distintivas;
- peças de roupa, sobreposições, materiais, cores e símbolos;
- armas e acessórios, incluindo forma, escala, orientação e pontos de fixação;
- diferenças entre frente, perfil e costas que precisam permanecer coerentes.

O inventário deve separar fatos definidos pelo usuário ou pelas referências
autorizadas de decisões ainda abertas. Uma imagem derivada não deve preencher
lacunas com detalhes apresentados como fatos.

## Formulário padrão candidato

Cada folha deve trazer, dentro da própria imagem, os campos abaixo em texto
legível:

- **Tipo de documento:** `character lineup model sheet`, `concept art sheet`;
  explicitar que é uma prancha de personagem com vistas, não uma cena.
- **Estilo:** identificador do catálogo, franquia de referência, plataforma e
  era, seguidos da descrição aplicada ao desenho.
- **Traço / lineart:** espessura, cor, acabamento e comportamento das linhas.
- **Morfologia:** proporção corporal e silhueta do estilo, separadas do biotipo
  específico do personagem.
- **Sombreamento:** número de tons por material, contraste, luz e uso ou não de
  dithering.
- **Biotipo:** registrar as opções do formulário — ectomorfo, mesomorfo,
  endomorfo, musculoso, petite; slim, atlético, curvilíneo, muito musculoso,
  baixo — e marcar qual combinação foi selecionada para este personagem.
- **Régua relativa:** declarar uma unidade visual (por exemplo, `H` = altura da
  cabeça), altura de referência e linha de base comum para as vistas ortográficas.
- **Fundo e alinhamento:** fundo branco, creme ou cinza claro, sem cenário; vistas
  organizadas horizontalmente, na mesma escala e com baseline comum.
- **Paleta e iluminação:** descrever a direção do estilo e preservar os papéis de
  cor já estabelecidos para o personagem.

Para personagem único, o campo de biotipo documenta o conjunto de opções e
destaca apenas o biotipo escolhido; não pede uma versão de cada corpo na mesma
folha. O layout pode reservar uma pose de identidade além das vistas ortográficas
e do close facial. O primeiro teste registrado usa `CPS2-Alpha-Cel` e Dr. Social.

## Teste de continuidade

1. Congelar a folha-base e o inventário de invariantes depois da aprovação do
   usuário.
2. Gerar uma imagem derivada usando a folha-base como referência de identidade.
3. Comparar cada invariante entre a folha e a imagem derivada: preservar,
   alterar, omitir ou introduzir sem suporte.
4. Registrar cada divergência por elemento; corrigir uma causa por iteração e
   repetir a comparação.
5. Só avaliar a eficácia do método após revisar a imagem derivada inteira,
   incluindo rosto, roupa, marcas, anatomia, símbolos, armas e acessórios.

## Critério de avaliação do piloto

O piloto será considerado promissor se a imagem derivada mantiver os detalhes
aprovados e se qualquer divergência puder ser localizada e corrigida usando a
folha e o inventário. A prancha, por si só, não prova consistência entre
gerações; essa conclusão depende da comparação com pelo menos uma imagem
derivada.

## Limite da promoção

O formulário e o processo incremental foram promovidos ao workflow compartilhado
em 2026-10-08. Isso oficializa o procedimento de trabalho, não as descrições das
49 referências do catálogo nem qualquer folha candidata individual. Cada estilo
e cada concept continuam sujeitos a curadoria e aprovação próprias. O fluxo
canônico está em `tools/sms_wrapper/.agent/workflows/original-artwork.md`; a
regra correspondente é SMS_GLOBAL §102 / L108.

