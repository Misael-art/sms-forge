# Contrato de animação — Dr. Ferdinand Social

Atualização operacional de 2026-10-28: a fonte artística v08.2 de 61 poses
possui decisão explícita aprovada pelo SHA `4e557095…`; os trechos abaixo
sobre v02 bloqueada e canvas 80×80 são históricos. O pedido atual autoriza
uma candidata CPS2 separada (idle e J01–J06), fonte 128×128 por célula, antes
da conversão SMS. Identidade v4, cabelo cinza, óculos de latão e tempos
2/1/1/1/1/3 permanecem. Detalhes: `dr_social_cps2_sample_v1.md`. Nenhuma
aprovação artística ou de runtime foi transportada entre essas fontes.

**Versão:** 2  
**Estado:** direção do moveset aprovada pelo dono (2026-10-10); arte dos golpes,
balanceamento e hardware ainda pendentes.  
**Contrato machine-readable:**
[`dr_social_animation_contract_v2.json`](dr_social_animation_contract_v2.json)  
**Histórico:** [v1](dr_social_animation_contract_v1.md) preserva a proposta
anterior sem as decisões aprovadas.

## Decisão aprovada

Dr. Social é um duelista investigativo de alcance médio que controla espaço e
pune erros. O elenco usa duas especiais por personagem: para Social, estocada
de rapieira e arremesso de bumerangue. Jab e chute baixo são normais de apoio;
toque de bengala é o normal de assinatura. O contragolpe de bengala está dentro
do Super **Laudo Final**, não é uma terceira especial. O Super consome uma barra
cheia do medidor comum do jogo, com carga independente por lutador. Esta
decisão não aprova frame data, valor de dano, economia numérica, hitbox ou
implementação do medidor.

Laudo Final é uma leitura curta contra ataques físicos altos/médios. Perde para
ataque baixo, agarrão, projétil, atraso ou finta; não concede invulnerabilidade
universal e não transforma Social. Os números de startup/active/recovery,
alcance, dano e janela continuam `proposal_unmeasured`.

## Fonte de identidade e limites de referência — atualização 2026-10-11

- Fonte visual aprovada de identidade:
  `data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`,
  SHA-256 `ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644`.
- A fonte v1 de 61 poses está arquivada em
  `data/source_art/sprite_studies/dr_social/historical_approved/basic_sequences_61f_owner_source_v1/`.
  Sua aprovação anterior é histórica; não usar como referência visual para a
  nova folha básica.
- A candidata v2 para as nove sequências básicas foi produzida somente a partir
  do model sheet v4 como referência visual e dos documentos GDD/TDD como
  especificação. Nenhuma sprite sheet anterior ou preview convertido entrou
  como referência visual. O arquivo atual permanece bloqueado por alpha parcial,
  franja ciano, paleta extensa e grade sem alinhamento exato; não iniciar
  conversão SMS antes da correção e revisão.
- A conversão v10 em `out/diagnostics/` é evidência histórica de uma rota de
  conversão, não referência de identidade, movimento ou paleta para a nova
  fonte.
- Dr. Social continua humano e esguio. Não aumentar largura de tronco/membros,
  não chibificar e não acrescentar presas, asas, aura ou transformação.

## Conteúdo do contrato v2

O JSON mantém as 20 ações comuns do contrato anterior e registra oito
sequências ativas de combate:

| Sequência | Quadros | Função | Estado |
|---|---|---|---|
| `social_light_jab` | J01–J06 | Jab curto de luva; primeiro sheet a desenhar | Candidata v2; preflight bloqueia alpha/paleta; review pendente |
| `basic_cane_tap` | BC01–BC08 | Normal médio de assinatura | Design aprovado; arte pendente |
| `social_low_boot_check` | K01–K07 | Interrupção baixa de alcance curto | Design aprovado; arte pendente |
| `rapier_lunge` | RL01–RL12 | Especial linear, sem invulnerabilidade | Design aprovado; arte pendente |
| `boomerang_throw` | BT01–BT14 + objeto | Especial de espaço com ida/retorno | Design aprovado; arte pendente |
| `social_read_super_attempt` | LC01–LC06 | Abre e anuncia a janela de leitura | Design aprovado; arte pendente |
| `social_read_super_hit` | LCH01–LCH08 | Aparo, saque contínuo e estocada | Bloqueado até definir bainha/ancoragem visual |
| `social_read_super_whiff` | LCW01–LCW06 | Falha visível e recuperação punível | Design aprovado; arte pendente |

O antigo `cane_riposte` é mantido no JSON só para rastreabilidade e marcado
como superado; não se conta como golpe ativo. O bumerangue e o rastro têm
tracks próprios no contrato. O rastro violeta é breve e exclusivo do
bumerangue; não é aura do personagem.

## Primeira folha: jab

`social_light_jab` é a primeira candidata visual desta etapa. O quadro tem seis
poses distintas, sempre em canvas/célula alinhada de 80×80 px, comparável à
fonte básica atual. J01 guarda; J02 carrega ombro/cotovelo; J03 inicia a
extensão; J04 é o único contato; J05 recolhe enquanto manga/aba do casaco
terminam o movimento; J06 retorna à guarda original. A bengala permanece inteira
na mão de apoio e acompanha a articulação sem mudar de mão, sumir, ser cortada
ou ter a ponta achatada.

A candidata visual v1 foi mantida em
`data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v1/`.
A v2, gerada usando só referências pixeladas aprovadas, está em
`data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v2/`.
Ela mostra as seis posições na ordem 3×2, mas o preflight do arquivo v2 mediu
1536×1024 RGBA, 184.429 cores RGBA, nenhum pixel com alpha 255 e 601.980 pixels
com alpha parcial; o halo semitransparente impede recorte limpo. Ainda não há
export dos seis quadros em 80×80 nem paleta indexada. As duas versões são
rascunhos para leitura de movimento, não pixel art aprovada, prova técnica nem
fonte pronta para conversão. Hash, medidas e checklist da v2 ficam junto à
imagem. Revisão artística independente e decisão do dono permanecem pendentes;
os bloqueios objetivos impedem promoção.

Antes de gerar pixels, o contrato distingue pose, track de corpo, track de
bengala, contato, startup/active/recovery e contrajogo. Os tempos atuais são
rascunho, não valores fechados. Os 12 princípios são revisados; pelo menos sete
estão mapeados a IDs no JSON com efeito visual planejado e justificativa
contextual para os demais. Depois da geração, esses vínculos só contam como
evidência se o movimento real mostrar o efeito.

## Rota de arte e revisão

1. Produzir uma folha de cada vez, em arquivo versionado dentro de
   `data/source_art/`; nunca escrever arte candidata em `res/`.
2. Preservar face, cabelo cinza, óculos redondos, cravat burgundy, casaco teal/
   cyan, luvas claras, botas marrons, bengala dourada/prateada e proporção
   esguia. A paleta tem papéis fixos; sombras do tecido formam blocos contíguos
   e nítidos, sem dithering, blur ou pixels-confete.
3. Inspecionar cada quadro em tamanho nativo e nearest-neighbor 4×, em fundos
   claro e escuro. Conferir ombro→cotovelo→punho→luva, pegada→haste→pomo
   arredondado, rosto/óculos, silhueta, baseline, recorte e alinhamento de
   células. Uma folha montada também é revisada; uma intenção textual não prova
   que a imagem obedeceu ao grid.
4. Congelar hash, dimensões, fonte, prompt/lineage e checklist por candidato.
   Review independente é read-only e a aprovação final é do dono. Qualquer
   falha ou eixo pendente bloqueia promoção.
5. Só depois da arte aprovada converter a paleta, mapear tiles/metasprites,
   medir SAT/scanline, VRAM/RAM/ROM/banking e VBlank, rodar os gates aplicáveis
   e construir ROM diagnóstica. Esses custos não são inferidos do concept nem
   da contagem de poses-fonte.

Falhas que barram a folha: quadro repetido ou fora de ordem; braço sem junção
anatômica; mão/punho sem leitura; bengala ou corpo cortados; ponta deformada;
halo/ruído/contorno sujo; sombra azul interrompida ou espalhada; branco/amarelo
vazando para materiais errados; ou diferença de morfologia em relação à fonte.

## Limite de promoção

O aceite do moveset autoriza a **produção das folhas candidatas**, não aceita
automaticamente sua arte. A folha de jab ainda precisa de review independente
e validação do dono. PNG aprovado também não equivale a paleta SMS, recurso
integrado, gameplay equilibrado, ROM ou entrega visual. Os limites de 15 cores
úteis em P1, 64 entradas SAT, oito objetos por scanline e orçamento por cena
continuam gates de conversão/runtime; `source_pose_count` não representa
objetos VDP, tiles nem um limite físico universal de quadros por sheet.
