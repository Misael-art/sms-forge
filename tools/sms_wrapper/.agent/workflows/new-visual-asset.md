# workflow: new-visual-asset

Antes da escrita, use `artifact-organization.md`: localizar origem por papel,
reservar versão e destinos no registro único e manter fonte/candidata/aprovada
distintas. Para fonte sprite sheet preparada para conversão, executar
`audit_source_raster.py` sobre o arquivo salvo e contrato hash-bound; alpha,
keycolor, dimensão e slots declarados não são garantidos pelo prompt.

Para pedidos de criação de imagem/arte autoral, iniciar por
`workflows/original-artwork.md`: escolher estilo no catálogo ativo, limitar o
ciclo, compor e revisar o concept/model sheet e guardar fonte, prompt,
metadados, lineage e validação em `data/source_art/`. Não gerar em massa todo o
catálogo por padrão. Este workflow cobre a conversão e integração posterior.

Orquestre as transições conforme `workflows/artwork-to-rom-lifecycle.md`:
cada saída preserva papel, versão/hash e aprovação própria; não promova por
herança de uma etapa anterior.

1. Fonte aprovada entra em `rascunho/` (ou é criada lá); registrar proveniência
   e SHA-256. Se houver versões em mídias diferentes, o jogo SMS de origem
   continua definindo identidade, paleta e comportamento. Referência suplementar
   só preenche a lacuna autorizada pelo dono (por exemplo, construção do traje);
   declare os papéis, limites, URL e hash no contrato/lineage e rode
   `audit_reference_boundary.py` (L103). O gate não julga fidelidade visual.
   Uma imagem de referência não aprova automaticamente seu uso como pixel final.
2. Definir o contrato de cor a partir da paleta mestra SMS e da paleta do
   personagem; confrontar os papéis cromáticos com a referência autorizada.
   Conformidade 6-bit não garante fidelidade semântica (L100). Para foto ou
   conceito truecolor, usar `prepare_sms_pixel_art.py` e a skill
   `sms-pixel-translate.md`; paleta de outro console é régua, não fonte (L055).
3. Definir `asset_contract_v1`: grid, tipo, escala, origem/pivô e paleta.
   Em folha de animação, declarar geometria por quadro (canvas, bbox visível,
   baseline e pivô), comparando cada ação com a escala do model sheet aprovado;
   uma célula igual não prova tamanho ou pés alinhados (L102).
   Em Master of Fighters, derivar escala corporal do GDD: Fatal Fury Special
   (Game Gear) é projetado de 160×144 para SMS 256×192; a faixa de trabalho é
   66–72 px, alvo 70 px. É direção visual, não limite físico. Canvas é escolhido
   por pose, múltiplo de 8, com ao menos 1 px transparente em cada borda;
   arma/equipamento cortados reprovam a prova (L110).
   Antes da folha animada, produzir somente duas poses-chave separadas (idle e
   ação), conforme o GDD e o padrão de prova técnica v4 do projeto. Isso não é
   uma animação de dois quadros; não exibir a sequência completa nessa prova.
   Depois da aprovação da prova e antes de desenhar a folha, selar um contrato
   de sequência por ação com estado inicial/final, loop/transição, IDs e
   contagem de poses-fonte, duração por pose, trilha do personagem e de cada
   objeto/efeito animado, física/hitbox quando aplicável e revisão dos 12
   princípios (pelo menos sete aplicados com pistas ligadas a quadros; razão
   para os restantes). Projétil/efeito com lifetime próprio declara lançamento,
   retorno/colisão/remoção e duração independente se ultrapassar a sequência do
   ator. Gate: `audit_animation_contract.py`. Separar essa
   contagem de poses do número de objetos físicos 8×8/8×16, tiles, SAT e VBlank;
   contagens hardware não medidas ficam `pending`.
   Em elenco de jogo, consultar também o contrato de harmonia do roster:
   confrontar a pose-fonte com concepts aceitas em uma prancha com baseline
   comum, medir altura/largura e relações declaradas com
   `audit_roster_harmony.py`, e revisar manualmente cabeça/torso/pernas,
   silhueta, densidade de clusters e acabamento de todos os personagens juntos
   (L105). Para Alis e J.J., registrar explicitamente a leitura anti-chibi; altura
   total não prova proporção corporal. Bbox de largura pode incluir cabelo, capa,
   espada ou escudo: comparar ocupação sem chamar isso de largura do tronco. A
   classe de peso do jogo não escolhe a altura visual. Declare também as
   referências por papel: uma pode servir de biotipo e outra de acabamento.
   Não herde defeitos de recorte da referência de morfologia. A revisão deve
   registrar pass/fail/pending para anatomia humana, cabeça/rosto, massa dos
   membros, recorte, agrupamento cromático, acabamento comum e leitura em 1×.
   Uma falha estética continua reprovação mesmo quando bbox e relações passam.
   Em concepts/model sheets e na primeira prancha do elenco, complete também
   `art-review.md`: olhos, ambas as mãos e sua orientação, articulações,
   continuidade da empunhadura até lâmina/cano, fixação e perspectiva de cada
   acessório, botas/linha de chão, contorno e consistência de luz. Registre
   todos os eixos por personagem e rode `audit_art_review_checklist.py`; `fail`,
   `pending`, eixo ausente ou SHA divergente impede promoção. O autor não aprova
   o próprio asset; use o review independente no checkpoint e aprovação humana.
4. Criar model sheet para personagem/inimigo/cenário final e revisar no tamanho
   SMS de destino, sobre fundo que revele transparência, contorno e ruído.
   Limpeza sem dithering por célula é correção condicional para granulação em
   folha de sprite; não substituir a conversão geral de fotos/conceitos (L101).
   Inspecione cada quadro também no tamanho nativo e com nearest-neighbor 4× ou
   maior. Pixels ligados por diagonal ainda podem ter cor de material errada:
   declare regiões/cores no contrato e rode `audit_sprite_cutout.py` (L104).
   Ao remover checkerboard, trabalhe pela conectividade ao exterior e não use
   chave global que apague tons iguais da roupa. Paleta correta não garante
   distribuição correta: agrupe os tons declarados por material, sem dithering,
   halos ou pixels cromáticos soltos; confira o PNG transparente no tamanho
   nativo e em nearest-neighbor 4× sobre fundo contrastante (L101/L104/L105).
   Se o preto puro for a chave de transparência, pixels destinados a contorno
   opaco usam um tom escuro não-zero declarado na paleta; conferir a folha sobre
   fundo não preto. Na prova técnica, cada pose aparece em 1× e nearest-neighbor
   sem linha, grid, baseline, caixa ou rótulo sobre os pixels. O mapa de tiles
   fica em painel separado. A transformação de escala precisa ser declarada e
   reproduzível em nearest-neighbor uniforme; o preview continua pixel a pixel
   igual ao PNG convertido. Rode `audit_asset_proof_sheet.py`, que refaz o
   transform, mede margem vazia e reprova corte de borda ou divergência pixel a
   pixel (L109/L110). A checagem não aprova anatomia, estilo ou fidelidade.
5. Converter tecnicamente antes de integrar em `res/`: preserve sem perda os
   índices/paleta/transparência/dimensões do PNG aprovado; para cada pose
   composta, gere metasprite com `pack_sms_metasprite.py`, rode gates de
   recurso/proveniência/geometria/SAT-scanline e construa uma ROM diagnóstica.
   Capture cada pose em sessão isolada e compare pixels visíveis e fundo
   transparente com `audit_render_fidelity.py --exact-indexed`. O runbook é
   `sms-asset-to-rom.md` (L121). Um passe estático não aprova movimento,
   gameplay, FPS, áudio, integração de produção ou budgets da cena.
6. Após prova técnica e aprovação dos gates humanos/hardware, exportar PNG
   indexado 8-bit para `res/` (índice 0 transparente, ≤15 úteis).
7. Rodar gates:
   - `audit_validate_resources.py`
   - `audit_luma_floor.py`
   - `audit_provenance.py`
8. Atualizar `doc/asset_provenance_manifest.json`.
9. Se for personagem/palco/HUD de entrega: skill `sms-visual-excellence.md`,
   contrato de escala no GDD, `audit_visual_delivery.py` e entrada no
   `doc/rom_asset_binding.json`. Sintaxe P/4bpp não fecha este passo.
10. Headroom de ROM menor que o custo do asset novo: **compor** com paleta,
   pose e fonte já carregadas antes de gerar (L049). Não inventar logo
   de 2 KB quando cabem 518 B de composição.
11. Falhou? Lição → workflow curation-learning. Persistência:
    `causal-persistence-loop.md` — não encerrar no diagnóstico.

## Doze princípios da animação

Toda animação revisa os 12 princípios: squash and stretch, anticipation,
staging, straight ahead/pose to pose, follow through/overlap, slow in/slow out,
arcs, secondary action, timing, exaggeration, solid drawing e appeal. Aplicar
no mínimo sete com efeito planejado observável e IDs de quadro; os demais têm
motivo contextual explícito. Declaração de intenção não é evidência do desenho:
após gerar pixels, revisão temporal confere o efeito real. Dois stills não
provam ciclo, intervalos, aceleração, holds ou follow-through. Rodar
`audit_animation_contract.py` no contrato e `audit_animation_semantics.py` nos
PNGs reais. Não promover folha com contrato incompleto, falha visual ou
orçamento de hardware sem medição.
