# skill: sms-visual-excellence

Use quando a tarefa pedir julgamento estético, época visual, escala, palco,
HUD ou promoção para `res/` / ROM. Complementa `sms-pixel-strict-rules`
(sintaxe) — esta skill trata **semântica**. PNG 4bpp válido não é qualidade.

Canvas: **256×192** (224 só com `VDPFEATURE_224LINES` medido). Não copie
320×224, 4 subpaletas, DMA ou Shadow/Highlight do Mega Drive.

## Teto honesto

```
runtime_probe_passed ≠ visual_epoch_passed ≠ ready_for_aaa
```

Captura que prova boot/rota Linux classifica no máximo
`runtime_probe_passed_visual_epoch_failed` até `audit_visual_delivery.py`
passar em modo `--delivery`.

## Época visual

Somente `visual_epoch=delivery` promove personagem, inimigo, boss, palco ou HUD.
Reprovar promoção de: `probe`, `technical_d1`, `technical_candidate`,
`visual_lab_control`, `reference_only`, `negative_case_evidence`, `placeholder`.

Benchmark (engine de referência, outro console, outro jogo) é **régua**:
escala, densidade, timing, silhueta, ocupação de tela. Pixels só reentram
com licença/proveniência explícita.

## Personagem

1. Model sheet limpo: sem sombra no chão, poeira, glow, FX ou checkerboard assado.
2. Must-preserve: rosto, cabelo, traje, proporção, mãos/pés, arma, identidade.
3. Até três rotas de tradução; nenhuma rota mecânica vira final sozinha.
4. Triagem em 1×, 2×/3×, NEAREST 8×, silhueta, fundos claro/escuro, composição 256×192.
5. Limpeza nativa: olhar legível, contorno consistente, ≤15 úteis + idx0,
   RGB no grid 6-bit, sem halo.
6. Escala vem do GDD. Para Master of Fighters, use a referência de composição
   *Fatal Fury Special* Game Gear: alvo de corpo 66–72 px na tela SMS, centro
   70 px. O valor é faixa visual de projeto, não hardware. Reduzir para caber
   numa pose ou economizar tiles continua proibido; a conversão nearest-neighbor
   declarada só pode aplicar a escala-alvo do GDD.
   `scale_density_mismatch` com escala `locked` → reautor no grid, não probe maior.
7. Em jogo com roster, compare todos os personagens em prancha comum antes de
   aprovar uma nova folha: fontes conceituais aceitas, sprite-fonte em tamanho
   nativo, baseline comum e escala não normalizada. Verifique cabeça/torso/pernas,
   volume aparente, contorno e densidade de clusters. Peso de gameplay não define
   altura de tela. Use `audit_roster_harmony.py` para medir os limites registrados
   no contrato; a ferramenta não substitui a revisão humana de estilo ou morfologia
   (L105). Bbox de largura inclui cabelo e equipamento; use relações de largura
   específicas para escala percebida e não trate esse valor como largura do tronco.
   Um frame 00 pode comparar escala, mas não promove animação. Se Alis ou J.J.
   parecerem chibi, mantenha a revisão pendente até conferir cabeça, torso e pernas
   em 1× e 4× nearest-neighbor.
8. Separe os papéis das referências. No roster de Master of Fighters, Hayato é
   régua de acabamento/cluster; Joe Musashi é régua de biotipo humano esguio e
   massa dos membros. Não herde do Joe halo ou pixel solto, nem empreste paleta,
   roupa ou identidade entre jogos. Registre os dois papéis no contrato da prancha.
9. Paleta exata não basta: avalie como os tons estão agrupados. Preserve os
   valores SMS permitidos e organize sombra/base/luz por material em clusters
   simples, sem dithering, halo ou pontos de cor que poluam a silhueta. Inspecione
   cada sprite com transparência real, a 1× e 4× nearest-neighbor, sobre fundos
   claro e escuro. Marque separadamente `identity_palette`,
   `head_torso_leg_proportion`, `limb_mass`, `cutout_cleanliness`,
   `palette_cluster_harmony`, `material_shadow_flow_coherence`,
   `semantic_palette_role_confinement`,
   `rendering_harmony` e `native_size_readability`. Para cada peça de roupa,
   verifique que sombra, base e luz acompanham a mesma face/dobra em todas as
   poses; uma cor válida porém isolada numa região de sombra reprova esse eixo.
   Confine brancos/amarelos a usos semânticos definidos no design; procure
   vazamentos na roupa, cabelo e contorno sem apagar olhos, luvas ou acessórios
   legítimos. Os dois micro-eixos são obrigatórios no checklist, que verifica
   cobertura; o resultado artístico ainda exige revisão humana.
   Qualquer `fail` reprova a proposta mesmo quando as medidas de escala passam
   (L101/L104/L105/L124).
10. Use o fluxo `art-review.md` para o pente-fino estrutural antes de aprovar
    conceito ou sprite. Confira rosto/olhos, as duas mãos e o polegar, orientação
    de mão esquerda/direita, punho/cotovelo/joelho, cadeia mão→grip→guarda→arma,
    tiras e pontos de fixação, perspectiva do equipamento, pés no baseline,
    contorno e pixels soltos. Para cada arma e acessório, compare também a
    identidade da ponta/terminal/pomo com o concept: item inteiro ainda pode
    estar semanticamente deformado (uma ponta achatada pode parecer martelo).
    Faça uma segunda passagem de todos os eixos depois da correção, em nativo
    e nearest-neighbor ampliado. No roster, repita a revisão quadro a quadro e na
    prancha completa. Preencha todos os eixos do checklist e rode
    `audit_art_review_checklist.py`; esse gate confirma que a revisão foi
    registrada e que o hash ainda corresponde, mas a decisão visual depende de
    um revisor independente e do dono. O produtor nunca escreve `pass` em seu
    próprio nome nem converte seu parecer em aprovação.
11. Para `pixel_sprite_sheet` e `pixel_sprite_roster_board`, o checklist precisa
    dos micro-eixos `pixel_clusters`, `face_detail_readability`,
    `outline_and_cutout`, `material_shading`, `hand_weapon_attachment`,
    `equipment_geometry`, `frame_pose_integrity` e `native_size_readability`.
    Confira o sprite em 1× e 4× sem suavização; metal, tecido e pele devem usar
    clusters deliberados da paleta do personagem, sem dithering decorativo,
    blur ou halo. Se um gerador alterar uma folha inteira, valide cada pose e
    os gates de paleta, recorte e animação antes de usar a saída como candidata.
    O prompt não prova que a pose, o grid ou os pixels foram preservados (L107).
12. Antes da animação, a prova técnica mostra somente duas poses-chave
    independentes: idle e ação. No preview, nenhum grid, régua, baseline ou
    texto cruza os pixels; o mapa 8×8 fica em painel separado. Canvas deve ser
    tile-alinhado e guardar ao menos um pixel transparente em cada borda.
    Arma/equipamento tocando o limite é fail; revise imagem em 1× e nearest
    antes de gerar o board. Exija `audit_asset_proof_sheet.py`: o gate refaz o
    transform nearest-neighbor declarado desde o PNG indexado e reprova corte
    na borda, diferença de pixel, alpha não binário, paleta fora da grade SMS ou
    contrato incompleto. Ele não julga anatomia, identidade da arma, fidelidade
    do concept ou acabamento. Exija os eixos humanos `equipment_terminal_shape`
    e `standing_body_height_vs_gdd`: a altura GDD é coroa–sola, sem bengala,
    arma ou capa, não bbox opaco total (L110/L111).
13. Registre limites físicos SMS junto aos budgets GDD/TDD: VRAM 16 KB; 512
    padrões 8×8 de 32 B no total; janela de 256 padrões para sprites; SAT de 64;
    8 objetos/scanline; objeto 8 px de largura × 8 ou 16 px de altura. CRAM:
    P0 para BG e P1 compartilhada por todos os sprites; índice 0 só é transparente
    para pixels de sprite; BG índice 0 sempre exibe a cor da tabela escolhida,
    e P0 índice 0 é backdrop visível. BG pode reutilizar P1 por
    tile. Inventário de padrões não é contagem SAT. O hardware não fixa máximo universal de
    quadros por folha: medir pools, ROM/banking, residência e upload VBlank
    antes de decidir o teto do projeto.
14. Para cada animação, liste e avalie os 12 princípios Disney com evidência.
    Timing, slow-in/out, follow-through, arcos e ciclo precisam de quadros e
    review temporal; dois stills não aprovam esses eixos. Nenhum script
    certifica AAA: gates cobrem invariantes declarados; revisão independente e
    aprovação do dono continuam obrigatórias (L109).
15. Paletas por personagem são estudos de autoria. Antes de promover uma luta,
    declare P0 (BG/HUD) e P1 (uma tabela comum de sprites), papéis de HUD
    estáveis, cores de cenário livres e mapeamento de todas as cores do roster;
    tiles BG podem selecionar P1 sem criar outra tabela CRAM. Em Master of
    Fighters, o mapa comum de até 15 cores úteis ainda está pending (L111).

## Palco e HUD

Concept/model sheet segue `original-artwork.md` (L108): produção incremental,
estilo/identidade separados, raw sem fichas/guias e compositor versionado.
Revisar a folha final no eixo obrigatório `document_and_layout` (§104): índice,
título, texto, silhuetas/equipamentos, régua/baseline, clipping e alinhamento.
Parecer anatômico da raw não aprova layout novo nem aprovação do dono.

- BG_A/B coerentes; sem splash de engine, logo de toolkit ou tela de referência.
- Lutador/jogador é o pico de leitura; BG_B respira; BG_A estrutura.
  BG/HUD não podem ser o objeto mais saturado com forma de sprite —
  sequestram o detector de gameplay (L042).
- HUD autoral sem overlap/clipping; nomes, barras, timer quando o GDD pedir.
- ROM cheia: composição (paleta, pose, fonte já carregada) **antes** de
  gerar asset novo (L049).
- Contraste medido (`audit_luma_floor.py`); CRT-aware: se só funciona ampliado, não existe.

## Gates

- `audit_visual_delivery.py --delivery`
- `audit_rom_asset_binding.py --require`
- `audit_placeholder_quarantine.py --check-release`
- `audit_render_fidelity.py` + `screenshot_semantic_gate.py`

## Nunca faça

- Confundir conformidade P/4bpp com qualidade artística.
- Reusar o mesmo PNG para dois personagens.
- Promover probe 8×8/16×16/32×40 como lutador final.
- Usar tela de branding como stage.
- Declarar `ready_for_aaa` com epoch ≠ delivery.
