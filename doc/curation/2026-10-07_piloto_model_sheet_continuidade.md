# Piloto: model sheet para continuidade visual

**Status:** proposta experimental para teste; ainda não promovida ao skill ou
workflow canônico.

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

## Limite de promoção

Este registro descreve o método candidato para um teste. Não altera regras,
ferramentas, skills ou workflows compartilhados do SMSForge. A promoção futura
depende de um piloto com personagem e estilo definidos, revisão do resultado e
curadoria posterior.
