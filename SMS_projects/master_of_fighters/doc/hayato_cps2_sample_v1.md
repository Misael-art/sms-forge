# Hayato — repetição da amostra CPS2

Pedido de 2026-10-29: novo personagem no mesmo consumidor, somente guarda e
ação curta, comparação com Social, conversão e ROM diagnóstica. Não amplia
elenco, movimentos de produção, atlas, cenário ou sistemas.

## Autoridades e limite de aceite

Hayato concept v2, `a8dc147836a8c703ecdda0a4bce87d2cd41efa6abaff6f55340a04bb3fccdf95`,
tem decisão owner em `decisions/hayato-concept-v02_owner_approval.json`.
Jovem adulto esguio/atlético, cabelo escuro preso com laço vermelho, quimono
branco, faixa vermelha, hakama laranja-vermelho, faixas brancas nas canelas,
sandálias, katana e bainha. A classe de combate não define massa/altura.
Os estudos SMS antigos são referência histórica, não resultado deste lote.

O dono expressou que gostou das artes do Social e autorizou este teste de
repetibilidade. Isso não fabrica decisão hash-bound de aprovação de cada
estágio. A amostra Social corrente é fonte v8, SHA
`877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41`;
idle é J01/v5 byte-idêntico ao J01/v8. A fonte61poses v08.2 aprovada permanece
separada, intacta. Não há aprovação automática de Hayato.

## Receita recuperada antes de gerar

Social partiu do model CPS2 v4, geração nativa registrada, extração nearest
com paleta-fonte explícita, `prepare_authored_sprite_sample.py` e funções
canônicas de display_fit/sms_tiles/runtime_format/scene_cut. Referências Ken
e Ryu e parâmetros estão em `dr_social_cps2_sample_v1.md`.
V4 não resolveu o rosto; v5 resolveu óculos. V6 deu contato reto, mas a grade
tall regular excedeu scanline. V7 continuou sem contato convincente.
V8 juntou cinco desenhos v5 com J04/v6 e a grade compensada(3,9): mesmos
pixels/escala/pivô, pico9→8, custoSAT33→34, pool218→220. A revisão independente
passou os eixos estáticos,120framebuffers conferiram, holds foram observados
na ROM e o trecho teve FPS/VBlank medidos. Isso não certifica AAA nem percepção.

Reutilizável: congelar referências/papéis, gerar uma candidata, inspecionar
matriz real, converter cedo, mapear P1 dos dois originais, medir ambos os lados,
revisar fonte/derivada separadamente, comparar framebuffer com PNG e ler prazo
real na ROM. Não reutilizar automaticamente corpo104px, canvas128px,
paleta30cores, seis poses, durações2/1/1/1/1/3, óculos/bengala ou fase(3,9).

## Proposta de ação — decisão pendente

GDD autoriza katana e pergaminhos, mas não há contrato de ação curta de Hayato
com IDs/poses/durações aprovados. Proposta enviada ao dono: corte curto de
katana (alternativa: desembainhar e voltar à guarda), exclusivamente amostra
artística diagnóstica, sem dano/hitboxes/frame-data competitiva. A produção
da guarda e a verificação do par são independentes dessa decisão.

## Tentativas observadas

1. Guarda v1: uma geração Imagegen, usando concept v2 para identidade e J01
   Social para construção/densidade. Ferramenta retornou1254×1254 em vez do
  1152×1152 pedido. Extração declarada1/10nearest e32cores-fonte, alpha128,
   sem pintar pixels. Fonte144×144, bbox(26,26)..(122,129),103px incluindo
   cabelo, pivô observado(68,129). Não se normalizou corpo à altura do Social.
   Mesma transformação global x2/3,y6/7 e extra2/3 nos dois atores. Guarda
   diagonal ocupa5sprites tall por linha; Social4; par9. Busca128fases em cada
   orientação não reduziu o pico. Relatórios preservados em
   `out/diagnostics/hayato_cps2_sample_v1/idle_pair_v1/` e `idle_grid_phases.json`.
2. Guarda v2: delta solicitado somente no ângulo de katana e rotação mínima
   da pega, para guarda mais vertical. Preservar comprimento, corpo, rosto,
   roupa, pés e bainha. Encerra o ponto apenas se fonte passar revisão e par
   ficar legal, sem corte, omissão, redução de corpo/arma ou normalização.

## Adaptação técnica autorizada

O adaptador existente v1 codificava IDs/tempos exclusivos do jab do Social.
V2 aditiva permite IDs/durações explícitos, extra_scale obrigatório para
preservar escala comum de elenco, canvas/pivô registrados e orientação/posição
do par. Encoder, mapper e packer canônicos são os mesmos. V1 mantém contrato
e bytes de header. Não há novo conversor ou consumidor. A extração aceita
colunas/nome de folha explícitos; defaults históricos preservados.

Quinze testes focados passaram, incluindo regressões v1, todas as fases,
reflexão de índices com pivô compensado e contrato de ação genérico inválido.
Self-check do adaptador passou. Auditoria global do registro continua falhando
pelo mesmo relatório histórico v5 ausente do Social; não foi fabricado.

## Repetibilidade — julgamento ainda aberto

Funcionou diretamente: identidade já aprovada, árvore/registro existentes,
extração registrada, mesmas funções oficiais, comparação de escala comum,
teste físico antes de animar. Adaptação Hayato: comprimento/orientação da
katana e hakama, além de parâmetros próprios. O teste precoce evitou desenhar
uma sequência inteira sobre guarda fisicamente incompatível. Não há medição
comparável de tempo histórico para afirmar economia percentual. Fonte/SMS,
movimento, ROM e orçamento finais continuam pendentes neste registro inicial.
