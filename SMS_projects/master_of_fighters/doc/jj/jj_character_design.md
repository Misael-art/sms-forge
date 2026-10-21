# J.J. — ficha de personagem

**Estado:** concept art v4 aprovada visualmente pelo dono em 2026-10-04; folha idle v5 refinada em 12 quadros é estudo candidato, aguardando revisão própria.  
**Origem escolhida:** *Zillion II: The Tri Formation* (Sega Master System).  
**Fronteira de fontes:** o jogo Master System ancora identidade, cores e mecânicas. Por pedido do dono em 2026-10-04, o model sheet e uma arte colorida do anime foram consultados apenas para corrigir o figurino; não definem paleta SMS, movimentos, poses copiadas ou lore do fan game.

## Identidade

- **Nome no jogo:** J.J. (também apresentado como J.J. na página de sprites).
- **Equipe:** o nome White Knights pertence à continuidade do anime; não é requisito de jogo adotado para o projeto.
- **Função no fan game:** lutador móvel de alcance médio/curto com arma laser. Esta é uma leitura de design, ainda não validada em combate.
- **Classe proposta:** leve, com alvo de 72–76 px de altura idle segundo a janela do GDD. A classe descreve mobilidade de jogo; escala e dano continuam abertos.
- **Idade:** não fixada nesta ficha. Os materiais consultados não sustentam aqui uma idade canônica.

## Concept art aprovada como referência visual

A folha `data/source_art/concept_art/jj_zillion_ii/jj_concept_sheet_v4.png` apresenta duas poses completas: guarda móvel com a pistola baixa e avanço lateral com disparo. O dono aprovou a concept art v4 em 2026-10-04. Ela usa o pool de cores SMS do jogo e tem fundo transparente; as referências do anime só ajudaram na construção do figurino, conforme pedido do dono, sem cópia de pixels, poses ou composição.

## Leitura visual do jogo

O estudo parte do sprite `J.J - Standing` de *Zillion II*, com 13×40 px, sete cores opacas e índice transparente no arquivo arquivado. Sua leitura de cor é curta e forte: blocos azul-violeta, magenta-vermelho, laranja, pele clara e branco. Como o sprite é muito pequeno, o model sheet do anime foi consultado a pedido do dono para resolver o corte do traje e dos equipamentos, sem determinar mecânicas ou cores.

Direção da concept art:

- corpo jovem, esguio e ágil, sem volume de armadura ou proporções de tanque;
- cabelo e família cromática azul-violeta continuam ancorados no sprite SMS; detalhes do corte permanecem sujeitos à revisão do dono;
- uniforme White Knights vermelho-magenta justo, gola protetora alta, ombreiras arredondadas claras, arnês diagonal com dispositivo octogonal no peito, cinto, coldre na coxa, proteções nos antebraços/joelhos e botas altas;
- azul-violeta fica concentrado no cabelo, arnês, detalhes de equipamento e sombras das proteções; os acentos laranja da paleta do jogo são pequenos, nunca placas grandes nos joelhos;
- pistola laser compacta ligada à arma Zillion do jogo;
- duas poses humanas de corpo inteiro: guarda pronta com a pistola baixa e avanço lateral com disparo controlado;
- sem moto, veículo ou armadura transformada no model sheet. Tri-Formation/Armorater fica documentado como referência mecânica separada, não como peça permanente da roupa;
- arte original de luta anos 90, contorno limpo, cel shading duro e três tons por material, sem ruído ou dithering.

## Paleta SMS

A paleta individual `jj_zillion_ii` foi acrescentada a `doc/build_palettes_manifest.py` e gerada em `doc/palettes_manifest.json` antes da arte. Ela contém 13 cores úteis em RGB canal×85, deixando índice 0 transparente. Os tons base vêm do sprite do jogo; as cores intermediárias próximas completam rampas de cel shading. O preto original foi substituído por navy `#000055` no contorno opaco para não confundir contorno com transparência.

Papéis e códigos:

| Papel | Código RGB SMS |
|---|---|
| contorno navy | `#000055` |
| cabelo azul profundo / médio / claro | `#0000AA`, `#5555FF`, `#AAAAFF` |
| uniforme magenta profundo / médio / claro | `#AA0055`, `#FF0055`, `#FF55AA` |
| acento laranja profundo / médio / claro | `#AA5500`, `#FF5500`, `#FFAA55` |
| pele profunda / média / clara | `#AA5555`, `#FFAAAA`, `#FFFFFF` |
| índice 0 | transparente |

## Ideia de combate — ainda não aprovada

J.J. pressiona a média distância com disparos únicos e busca ângulo com passos laterais curtos. A arma deve ter recuperação legível e espaço para contra-ataque. Dois especiais candidatos constam em `doc/jj/jj_moveset_concept_v1.json`:

1. **Zillion Laser:** disparo reto, uma instância por ação até decisão sobre multi-hit. A animação, hitbox, alcance e frame data não foram definidos.
2. **Armorater Shift:** evasão vertical curta inspirada na transformação do veículo Tri-Formation em Armorater descrita na embalagem japonesa. A aparição do veículo/armadura é apenas proposta; precisa de contrato de coreografia, hitbox e orçamento antes de virar asset.

Não há startup/active/recovery, dano ou hitstop fechados. O arquivo é uma proposta para revisão do dono, não FSM nem contrato de asset.

## Documentos e gates

- Fontes visuais, limites de uso, dimensões e hashes: `data/source_art/concept_art/jj_zillion_ii/review_drafts/reference_notes/jj_reference_notes_v2.md`.
- Prompts de revisão: `data/source_art/concept_art/jj_zillion_ii/review_drafts/prompts/jj_concept_prompt_v3.txt` e `data/source_art/concept_art/jj_zillion_ii/review_drafts/prompts/jj_concept_cleanup_prompt_v4.txt`.
- Contrato visual ativo: `data/source_art/concept_art/jj_zillion_ii/approved_records/jj_concept_asset_contract_v4.json`.
- Lineage e hashes de saída: `data/source_art/concept_art/jj_zillion_ii/approved_records/jj_concept_lineage_v4.json`.
- Contrato e lineage da folha idle candidata v5: `data/source_art/sprite_studies/jj_zillion_ii/jj_idle_asset_contract_v5.json` e `data/source_art/sprite_studies/jj_zillion_ii/jj_idle_lineage_v5.json`.
- Perfil de cores por região e recorte: `audit_sprite_cutout.py`, executado pelo contrato v5; a fidelidade visual completa ainda requer revisão humana.
- Moveset de conceito: este diretório `doc/jj/`.

Esta arte é material de origem. A folha idle `data/source_art/sprite_studies/jj_zillion_ii/jj_idle_12f_sms_96px_v5.png` tem 12 quadros distintos, 13 cores úteis, transparência no índice 0, altura visível de 72–76 px, largura de 61–66 px e baseline comum y=95. A revisão v5 removeu 13 pixels castanho-avermelhados ligados ao limite superior do cabelo, sem mudar outras cores, poses ou escala; passaram os gates de recursos, semântica/geometria e regiões de material. O perfil de cor do cabelo está declarado no contrato para impedir que o erro se repita. A folha aguarda revisão visual própria, está fora de `res/`, não tem vínculo com ROM e não foi vista no emulador. A busca por qualidade AAA é um objetivo de trabalho, não uma certificação; a aprovação do conceito não aprova a folha, orçamento ou integração.
