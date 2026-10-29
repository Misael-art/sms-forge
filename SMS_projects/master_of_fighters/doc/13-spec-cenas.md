# 13-spec-cenas — master_of_fighters

## Par diagnóstico Hayato + Dr. Social — 2026-10-29

GuardaHayato v2,source0b72e603…,materialmap2,registrobaseline3. Quatro pares:
guardas em ambos os lados e Socialjab contra guardaHayato nos dois sentidos.
Canvas porPNG80×80;pivôSMS(32,72);origens(32,72)/(144,72),trocadas noespelho;
solasvisíveisy143,boundary144. P1comum15códigos doSocialv8, P0fundo0x15.
Arma não entra na altura anatômica; source144×144 não é canvas obrigatório
para futuros movimentos. Mesma transformação de elenco; não normalizar altura
por bbox de equipamento. CorposSMS~58–60px no diagnóstico, sem claim de fechar
faixa absoluta68–72px da produção.

Guardas66patterns/2112B,32SAT,pico8; Social6poses contra guardaHayato
222patterns/7104B,35SAT máximo,pico8. Todasresidentes; baseSATsomenteVBlank.
Baseline3 inclui faseSocialJ04espelhado[5,9], medida após corrigir1px nos pés.
0derrame em3000frames,mínimo207; degrau+128B0derrame,mínimo218. FPSmédioNTSC
59,67/59,81 em8s. Não há prazo/streaming/dano/hitbox/açãoHayato aprovados.
Controle, revisão, SHAs, sessões privadas encerradas e índices no memorybank
atual e out/diagnostics/hayato_cps2_sample_v1/result.json. É checkpoint estático,
não cena de combate/entrega; ação própria depende da escolha já solicitada.

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Paletas CRAM | 2 × 16: P0 para BG/HUD, P1 para todos os sprites; índice 0 transparente só para pixels de sprite; BG índice 0 sempre visível; P0 índice 0 é backdrop |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |
| Padrão gráfico 4bpp | 8×8 px; 32 B; 512 padrões no total da VRAM |
| Janela de padrões para sprites | 256 padrões, selecionados pela base do reg. 6 |
| Objeto sprite | 8 px de largura; 8 ou 16 px de altura |
| CRAM | 32 entradas; até 15 cores comuns de sprite em P1; P0 usa 16 slots de BG/HUD, com índice 0 visível e reservado como backdrop no projeto |

Não existe limite físico universal de quadros por folha. O máximo por asset é
decisão de projeto, derivada de padrões residentes, compartilhamento, pools,
ROM/banking e upload por VBlank. O valor fica pendente no TDD até haver layout,
alocação e medição reais. Contagem de patterns da imagem não substitui
metasprite, SAT, sprites/scanline ou orçamento por cena.

### Prova de duas poses — Dr. Social (inventário, não orçamento de cena)
O padrão de escala está no GDD/TDD: *Fatal Fury Special* Game Gear, altura
proporcional ao viewport SMS e faixa-alvo do roster 66–72 px; canvas por pose
fica tile-alinhado e é dimensionado pelo conteúdo, não fixado em 96×96.

O candidato atual é
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json`.
Registra duas imagens 80×80 (10×10 tiles): idle com 42 padrões únicos; ação
com 47; união do par 89 (2.848 B brutos 4bpp). A v3 foi superada porque a
reamostragem achatava a terminação da bengala; a v4 usa o frame-fonte 06, em
que a ponta arredondada permanece legível. As duas são poses estáticas, não
quadros de animação, e mantêm pelo menos 1 px transparente em cada borda. A
contagem de padrões é inventário da arte, não alocação residente nem contagem
de objetos SAT. Metasprite, pico de scanline, pool VRAM/RAM, banking e carga
VBlank permanecem pendentes; não usar esses números para fechar o budget de
uma cena. O scan não encontrou ilhas opacas menores que 2 px; regiões por
material, anatomia, identidade visual do terminal da bengala e review artístico
seguem pendentes. A alocação de paleta runtime está em
`doc/palette_runtime_contract_v1.json`; não há 14 paletas de sprite separadas.

## Trecho diagnóstico CPS2 idle/jab — 2026-10-28

Owner e fonte: `dr_social_cps2_sample_v1.md`. ROM base SHA `f5d54b15…`,
32.768 B. Medição do pool e dos sete manifestos `scene_*.json` pelo pipeline
tall e `audit_sprite_line_sim.py`: 212 padrões/6.784 B residentes, 31 SAT e
pico8 por scanline em idle e J01–J06, zero overflow. Uma P1 comum de15 cores
úteis com o Ken autorizado. Sprites na janela0x0000..0x1FFF; tile0 vazio
compartilhado com fundo diagnóstico, PNT0x3800, SAT0x3F00. Não há cenário,
HUD, projéteis ou áudio neste inventário.

No setup, padrões/CRAM são carregados com display desligado. Em cada tick de
animação, somente SAT é copiada ao VDP; os desenhos ficam todos residentes.
Selo autônomo3.000frames no Emulicious: `vovf_delta=0`, `vline_min=207`.
Degrau medido de+128B de padrões corretos por VBlank: também zero derrames,
`vline_min=217`, em outra ROM/sessão identificada no relatório do lote.
Não há conversão desses valores em milissegundos CPU ou teto máximo.

SMRT em duas janelas8s:59,43/59,56fps; alvo NTSC passou no instrumento.
Janelas curtas anteriores falharam e permanecem registradas. Sem qualificação
PAL. Todos os números vêm de JSONs em `out/diagnostics/dr_social_cps2_sample_v1/`
e `out/evidence/sessions/`, com quatro sessões encerradas e QA visual nativa
independente1/1. Não se transporta o resultado para produção, gameplay ou
outros conteúdos. O orçamento integrado da Cena01 abaixo continua aberto.

## Trecho diagnóstico facial v5 — 2026-10-29

ROM `fc46d77b…`,32.768B: fonte v5 e receita SMS identificadas no handoff.
216 padrões/6.912B;31SAT em idle/J01/J02/J03/J05/J06 e32SAT em J04, pico8 em
todos os sete pares pelo conversor tall/simulador. Fonte larga v6 reprovou
J04/pico9 e não foi buildada. Layout/CRAM/transferências iguais à baseline,
com os novos patterns residentes. FPS8s59,62/59,79NTSC; selo3000frames,
zero derrames/mínimo207. Degrau128B medido em outra ROM SHA `a5c013a8…`,
zero derrames/mínimo217. Arte/contato/produção permanecem abertos; esses
números não pagam a Cena01 abaixo, cenário/HUD ou gameplay.

## Trecho diagnóstico contato v8 — 2026-10-29

Fonte/receita no handoff, ROM452cd565…/32.768B. Pelo conversor e sete manifestos
SAT:220padrões/7.040B,31SAT nas poses exceto J04=34, pico8 emtodos os pares.
GradeJ04(3,9)px compensada: controle idêntico nos oito PNGs mediu33SAT/pico9 e
foi reprovado sem build. O custo maior de SAT/patterns está incluído.
Performance: duas janelas8s59,62/59,74fpsNTSC; selo3000frames0derrame/mínimo207;
degrau128B,outra ROM7ce342bc…,0derrame/mínimo217. Quatro sessões encerradas;
120framebuffers independentes e21da linha temporal exatos. Esses números pagam
somente o diagnóstico residente; cenário/HUD/gameplay, PAL e produção da Cena01
continuam abertos. Não inferir orçamento pelo screenshot nem milissegundosCPU.

## Cena 01 — _(nome)_
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | — | — | — |
| patterns sprite | — | — | — |
| name table | — | — | — |
| SAT | — | — | — |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| — | — | — |

- **Total worst-frame**: _(medido)_ bytes
- **Headroom**: _(medido)_ %
- **Método**: _(como foi contado — contagem instrumentada, não estimativa)_
- **Degrau seguinte medido**: _(§18: qual o próximo incremento e ele cabe?)_

### Sprites por scanline (pico)
_(rodar `audit_sprite_line_sim.py` sobre o manifesto da cena e citar o pico real)_

### fps observado
_(rodar `measure_fps.py`; ≥5 amostras, todas 50–60. Citar o JSON.)_
