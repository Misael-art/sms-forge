# Dr. Social — diretriz v08.2 de consolidação determinística

**Estado:** candidata; gate quantitativo passou, revisão visual do dono pendente.
**Base geométrica:** v07 congelada, 61 poses, grade 8×9, células 80×80.
**Identidade:** model sheet aprovado CPS2-Alpha-Cel v4.
**Contrato:** `doc/dr_social_sprite_mask_contract_v08_2.json`.

## Delta autorizado

- Reclassificar pixels opacos entre materiais e através do contorno para remover clusters sem um bloco sólido 2×2. A geometria alfa, a grade e a transparência binária permanecem idênticas.
- Para cada componente abaixo do mínimo, contar somente os pixels opacos do anel 8-conectado imediato. Remapear para a cor dominante; transferir a propriedade da máscara quando a cor pertence a outro material. Reavaliar após cada componente até ponto fixo.
- Casaco limitado a duas cores: índice 5, ciano base `#00AAAA`; índice 6, sombra azul escura `#005555`.
- Cabelo limitado aos índices cinza 8/9. A pele usa tons 2/3. O branco, amarelo e bordô ancorados continuam protegidos de novos vazamentos.
- Óculos de latão permanecem autorizados: preservar os 85 pixels da máscara facial. A haste branca contínua de 1 px é exceção semântica ao tamanho mínimo.
- ImageGen/difusão, blur, média, antialias, filtros de luminância e remapeamento por distância de cor permanecem proibidos.

## Execução observada

A ferramenta `tools/build_dr_social_61f_v08_2_masks.py` gerou a candidata em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_2_final_candidate/`.
PNG: `dr_social_basic_sequences_61f_cps2_alpha_cel_v08_2_candidate.png`.

- 61/61 poses; PNG indexado 640×720; grade 8×9 de células 80×80; 11 cores úteis.
- Alpha e geometria preservados; nenhum pixel alterado fora das máscaras auditadas.
- Zero singletons e zero clusters sem bloco 2×2 em cabelo, casaco e pele, verificados novamente por célula fora do relatório gerador.
- Casaco contém somente índices 5/6; cabelo sem tons não cinza dentro da máscara em 61/61 poses.
- Vazamentos branco/amarelo/bordô/cinza: zero. Óculos: 85 pixels autorizados preservados. Haste da bengala: 1.245 pixels brancos, zero não brancos.
- A reclassificação de fronteira acrescentou 863 pixels ao contorno; nenhum pixel do contorno original foi removido.
- A consolidação de clusters reassociou 225 pixels de cabelo, 1.949 do casaco e 1.631 da pele. Total de mudanças de cor na candidata: 23.236, incluindo a repintura determinística das máscaras de material.
- Amostras 1×/4×: `dr_social_v08_2_keypose_samples_1x_4x.png`. Relatório: `dr_social_v08_2_mask_compliance_report.json`.

## Aprendizado técnico desta execução

Uma tentativa intermediária aplicou todas as decisões sobre uma fotografia imutável. Componentes adjacentes podiam então trocar tons de pele em sentidos opostos e oscilar entre passagens. A rota estável é processar um componente por vez, recalcular as conectividades depois de cada remapeamento e exigir ponto fixo. O relatório de conformidade deve diferenciar contorno original preservado de novos pixels que receberam o índice de contorno por autorização explícita.

O zero quantitativo de clusters comprova somente os critérios medidos. Não aprova anatomia, leitura da pose, identidade, acabamento visual, custos de tiles/SAT/scanline/VBlank nem integração. Esta candidata não foi promovida para `res/` nem compilada em ROM; aguarda validação visual do dono.
