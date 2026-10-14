# Workflow: arte autoral até ROM

Use para personagem, item ou outra arte autoral integrada a um jogo Master
System. Este runbook coordena `original-artwork.md`, `art-review.md`,
`new-visual-asset.md`, `sms-sprite-animation.md` e `sms-asset-to-rom.md`; não
substitui os contratos técnicos ou os documentos do projeto.
Organização/retomada segue `artifact-organization.md`: um registro por projeto,
heads por papel e revisão, decisões ligadas ao hash e reservas antes da escrita.

## Estados de promoção

```text
pedido definido
→ referências, identidade e estilo registrados
→ concept model sheet revisado
→ concept aprovado pelo dono para o hash exato
→ harmonia do elenco aprovada, quando aplicável
→ contrato de animação aprovado
→ prova técnica de conversão aprovada
→ fonte completa de animação aprovada por papel/caminho/SHA
→ pixels convertidos e gates SMS aprovados
→ ROM diagnóstica ligada ao asset e comparada no framebuffer
→ revisão artística da conversão aprovada
→ asset integrado à cena/produção e budgets aprovados
→ evidência atual de gameplay e entrega
```

`documentado`, `candidate`, `owner_approved_source`, `resource_pass`,
`diagnostic_rom_pixel_pass`, `owner_review_pass`, `production_integrated`,
`tested_emulator`, `validado_budget` e `delivery` são estados diferentes. Todo
status identifica artefato, papel, versão/hash e eixo comprovado. Não herde
aprovação de um estágio para outro nem de um hash para outro.

## Passos e gates

1. **Receber o pedido.** Registrar jogo/franquia, asset, personagem, objetivo,
   plataforma, mídia, alterações permitidas e identidade invariável. Se a
   direção visual não estiver definida, consultar os estilos vigentes no
   catálogo, com liberdade para propor outro; identificar traço/mídia,
   obra/era e artista/estúdio quando confirmados. Não inventar créditos.
2. **Fixar referências e identidade.** Separar identidade do personagem de
   acabamento artístico. Registrar papel, limite e hash de cada fonte; congelar
   idade, biotipo, rosto, silhueta, cabelo, roupa, marcas, armas, paleta e
   acessórios. Mudanças fora do pedido exigem decisão do dono.
3. **Criar o concept sheet aprovado.** Por padrão, um ciclo/estilo por vez.
   Incluir frente, perfil estrito, costas, detalhe do rosto, pose-assinatura,
   escala/régua, baseline, fundo neutro e ficha legível. Arte bruta sem título,
   rótulo ou régua; o compositor acrescenta cada elemento uma vez. Versionar
   bruto, prompt, composição, metadata, lineage e validação em
   `data/source_art/`, fora de `res/`.
4. **Revisar e aprovar o concept.** Revisor independente vincula o parecer ao
   SHA; o produtor não se autoaprova. Fazer dupla passagem de anatomia e
   assinatura visual. Traçar ombro→braço→cotovelo→antebraço→punho→mão;
   verificar orientação e pega→guarda→lâmina/cano; fixação/perspectiva e
   terminais de equipamento; rosto, proporção, paleta, clusters, recorte,
   contorno e layout. Reinspecionar todo defeito reportado após a correção e
   repetir os eixos afetados. Checklist verifica cobertura/hash, não verdade
   artística. `fail`, `pending` ou ausência de aceite do dono bloqueiam avanço.
5. **Harmonizar elenco, se houver mais de um personagem.** Pranchas frontais
   com baseline/régua comuns, até cinco personagens cada. Medir as relações do
   GDD e revisar visualmente altura corporal sem cabelo/arma/capa, proporção
   cabeça-torso-pernas, massa de membros, acabamento, contorno, paletas e
   clusters. Preservar identidade e evitar chibi, engrossamento, dithering,
   ruído e pixels órfãos. `audit_roster_harmony.py` mede relações, não
   morfologia/estilo; parecer visual e aprovação do dono continuam necessários.
6. **Contratar animação antes de desenhar.** Para cada ação: trigger/finalidade,
   loop/transição, estados inicial/final, IDs/quantidade/duração de poses,
   trilha separada do personagem e de cada arma/projétil/efeito, lifetime,
   física e hitbox quando aplicável. Rever os 12 princípios; ao menos sete
   aplicações contextuais ligadas a quadros e razão para cada princípio
   restante. `source_pose_count` é desenho, não objeto VDP. Valores não medidos
   ficam `pending`/proposta. Rodar `audit_animation_contract.py`; após PNGs,
   `audit_animation_semantics.py` e revisão do movimento.
7. **Produzir a prova técnica conforme o padrão do projeto.** Duas poses
   distintas (idle e ação), paleta, escala, canvas tile-alinhado, equipamento
   inteiro e mapa de tiles em painel separado. Essa prova valida a rota de
   conversão; não é sprite sheet animada nem origem dos quadros finais. Conferir
   terminais e anatomia visualmente além da igualdade de pixels.
   `audit_asset_proof_sheet.py` mede reprodução/estrutura, não verdade artística.
8. **Selecionar a fonte animada pelo papel e SHA.** Converter a folha completa
   aprovada, com IDs e contagens ligados ao contrato/lineage. A prova de duas
   poses nunca substitui a fonte de animação. Normalizar PNG indexado sem mudar
   matriz de índices, PLTE, dimensão ou transparência (L121/L122).
   Antes de converter um sprite sheet, verificar o arquivo salvo com
   `audit_source_raster.py` e contrato explícito de dimensões, slots/IDs e
   alpha/keycolor. Promessa no prompt não comprova essas propriedades. O gate
   não conta poses semanticamente distintas nem certifica recorte/halo.
9. **Passar gates de pixels e hardware.** Validar índice 0 transparente, no
   máximo 15 cores úteis, valores SMS, grid, cores por material, recorte,
   contorno, pivôs e legibilidade em 1×/nearest-neighbor ampliado. O parecer
   artístico inclui o eixo obrigatório `material_shadow_flow_coherence`:
   revisar a progressão espacial sombra/base/luz e a continuidade de cada rampa
   por dobra/plano em todas as poses, separado do simples teste de pertencimento
   à paleta. Rodar gates
   de recursos, proveniência, cutout, geometria, SAT/scanline e patterns
   residentes. Calcular a janela real até a name table; índices lógicos não
   equivalem a padrões residentes. P1 de sprites, P0/uso de BG, RAM/ROM,
   banking e pior VBlank devem ser definidos e medidos por cena.
10. **Construir e inspecionar ROM diagnóstica.** Ligar fonte→PNG→símbolo→ROM
    pelo SHA. Construir com devkitSMS e abrir sessão privada Emulicious ligada
    ao binário. Comparar poses no framebuffer com a fonte por
    `audit_render_fidelity.py --exact-indexed`; ciclos precisam de captura
    frame-paced e revisão da timeline. ACK ou screenshot estático não provam
    movimento. Igualdade pixel a pixel prova renderização daquela ROM, não
    anatomia, estilo, timing, gameplay ou qualidade AAA.
11. **Integrar somente após a aprovação da conversão.** Obter revisão
    independente e humana do que aparece no ROM. Mapear paleta por material
    para P1 compartilhada; medir coexistência de elenco, cenário/HUD, VRAM,
    RAM, ROM/banking, SAT/scanline e pior VBlank da cena real. ROM diagnóstica
    fica fora de `res/` e não é entrega.
12. **Fechar produção com evidência atual.** Validar gameplay/interação,
    animação, FPS apropriado (50/60), áudio, memória e budgets conforme
    GDD/TDD/spec. Mudança/relink da ROM exige evidência fresca. Declarar apenas
    eixos pagos e dentro do teto de claims aprovado.

## Curadoria

Preservar fontes aprovadas e tentativas rejeitadas. Registrar falha observada,
causa ainda hipotética, artefato/hash, ferramenta, alcance e próximo gate.
Deduplicar lições existentes, ligar a doutrina ao workflow/skill e usar
`curation-learning.md` mais `audit_learning_capture.py`. Cada projeto mantém
status e decisões no memory bank, GDD/TDD e lineage. Nenhum PASS de checklist,
conversão ou ROM substitui outro eixo.

## Gates usados

`audit_art_review_checklist.py`, `audit_roster_harmony.py`,
`audit_animation_contract.py`, `audit_animation_semantics.py`,
`audit_asset_proof_sheet.py`, `audit_validate_resources.py`,
`audit_reference_boundary.py`, `audit_provenance.py`, `audit_sprite_cutout.py`,
`audit_sprite_mode.py`, `audit_sprite_line_sim.py`,
`pack_sms_metasprite.py --self-check`, `audit_rom_asset_binding.py --require`,
`audit_render_fidelity.py --exact-indexed`, `audit_visual_delivery.py`,
`audit_claims.py` e `audit_learning_capture.py`. Cada ferramenta mede somente
sua alegação; review independente e aprovação humana permanecem necessários.
