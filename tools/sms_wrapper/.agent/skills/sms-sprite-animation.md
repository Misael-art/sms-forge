# skill: sms-sprite-animation

Use quando houver idle, walk, golpe, hit, KO ou qualquer ciclo de frames.
Metasprite e SAT: `sms-sprites-metasprite.md`. Esta skill é **semântica**.

## Atuação antes do acabamento

Intenção do golpe → estudo curto de referências autorizadas → coreografia
corporal → poses gestuais → teste temporal preliminar → revisão do movimento
→ acabamento → conversão e ROM. Referência tem papel e SHA: não extrair
identidade, equipamento ou moveset de uma fonte autorizada apenas para ritmo.

No brief, definir função, personalidade, alvo e contrajogo; desenhar linha de
ação e silhueta de preparação, execução, acompanhamento e recuperação. Traçar
apoio/transferência de peso, quadril–tronco–ombros, cadeias dos membros,
empunhadura e arco da arma. Corpo apoiado pode girar, comprimir e inclinar;
preservar comprimentos e identidade não significa fixar cabeça, quadril, pés
e roupa no mesmo pixel. Arma rígida não exige corpo rígido. Cabelo, tecido e
acessórios respondem à ação com atraso coerente, sem movimento ornamental
obrigatório. Diagrama de juntas é estudo esquemático, nunca pixel final.

Antes de acabamento, reproduzir o gesto na duração proposta. Comparar
deslocamento entre poses (espaçamento) e tempo de exposição (timing)
separadamente: holds diferentes não demonstram aceleração. Acrescentar desenho
somente para fechar uma lacuna identificada de trajetória, leitura ou retorno.
Mais desenhos e sete princípios declarados não são pontuação de qualidade.
Registrar por princípio efeito planejado, efeito observado e pendência; a
contagem exigida pelo contrato continua uma verificação de cobertura.

Testar cedo a sobrevivência de rosto/mãos/arma na escala SMS e a composição do
par, antes de expandir atlas. A amostra é definida pela ação e pelo projeto;
seis poses de Hayato ou Social não são mínimo/preset universal. Converter não
autoriza redesenhar atuação ou reduzir individualmente a pose larga.

## Decisão temporal

Aplicar o checkpoint de `workflows/art-review.md`: imagens, análise quadro a
quadro, ordem/exposição, percepção contínua, apresentação ROM e aceite do dono
são eixos separados. Uma interface que só entrega stills deixa percepção em
`needs_evidence`. Preparar mídias exatas normal/lenta e intervalos a observar,
preservar controle e encerrar a repetição de revisões equivalentes. Não gerar
ou buildar para preencher uma limitação de percepção. Após observação real,
decidir manter, ajustar exposições ou corrigir a pose responsável.

## Princípios (ênfase SMS)

Considere os 12: squash/stretch, anticipation, staging, straight ahead/pose to
pose, follow-through/overlap, slow in/slow out, arcs, secondary action, timing,
exaggeration, solid drawing e appeal. Marque quais serão aplicados com pista
planejada e IDs de quadro, e justifique os não aplicados. Cada animação precisa
aplicar pelo menos sete princípios de forma contextual; enumerar sete nomes sem
efeito visível planejado não satisfaz a regra. Pista de planejamento não prova
o resultado desenhado.

## Contrato obrigatório antes de gerar a folha

Para cada ação, registrar em manifest versionado:

- ID/nome, gatilho e finalidade; `loop` ou transição;
- pose/estado inicial e pose/estado final;
- IDs das poses-fonte, contagem de imagens distintas e duração provisória por
  pose, em ticks lógicos definidos;
- trilha frame a frame do personagem e de cada objeto/efeito animado, com estado
  inicial/final e contagem de poses da entidade;
- lifetime próprio de projétil/efeito: evento de lançamento, retorno/colisão ou
  remoção e timeline independente quando ultrapassar a sequência do ator;
- os 12 princípios, no mínimo sete aplicados e ligados a IDs de quadro; motivos
  contextuais para os demais;
- trajetória/velocidade/apoios, hitbox e fases startup/active/recovery quando
  houver locomoção ou golpe;
- contagens de hardware em campos próprios: objetos 8×8/8×16 por quadro,
  padrões únicos/compartilhados, RAM/ROM, residência, SAT/scanline e VBlank.

`source_pose_count` conta desenhos de pose. Não chamar cada pose de “um sprite
VDP”: um quadro pode exigir vários objetos físicos e várias poses podem
compartilhar tiles. Se os pixels ou medição ainda não existem, declarar
contagem hardware `pending`/`null`, sem estimativa tratada como fato.

Para SMS, declarar definição de tick em NTSC/PAL e manter movimento discreto em
inteiros/Q8.8; não usar `float`/`double` no runtime Z80. Cada golpe registra
resposta/contrajogo e hipótese de balanceamento. Maior alcance, dano e cobertura
precisam de custo coerente em startup, recovery, recurso ou vulnerabilidade.
Alcance da hitbox segue silhueta e arma desenhadas; trajetória de personagem,
arma e projétil é contínua e não atravessa mãos, corpo ou cenário.

Gate de contrato: `audit_animation_contract.py --manifest <json>` e
`audit_animation_contract.py --self-check`. Depois que os PNGs existirem,
executar também `audit_animation_semantics.py`; os dois gates medem coisas
diferentes.

## Moveset mínimo (quando o GDD for fighting / action)

idle, walk/advance, retreat, crouch, jump, landing, guard, hit, knockdown,
get-up, light, medium, heavy, special, throw, victory, defeat — mais ações
específicas do GDD. Não invente frame fora do GDD.

Não colapse estados que têm gatilhos/leituras diferentes (ex.: derrota por
tempo e empate; queda e recuperação; retratos versus neutro/vitória/derrota).
Para o primeiro exercício Dr. Social, preservar a lista completa de
`required_sequence_ids` em `doc/dr_social_animation_contract_v1.json`; ela é o
caso de validação desta skill, não aprovação de moveset ou de pixel art.

## Reprovação permanente

- frames apenas reordenados
- ações semanticamente iguais com nomes diferentes
- fragmentos da célula vizinha
- fundo incorporado / contato transparente
- pivot inconsistente
- preview diferente do strip
- vista frontal usada como corrida lateral
- silhueta preenchida chamada de lineart
- derivação mecânica chamada de autoria nativa
- smear que parece sujeira ou ilha

## Medição

Estados devem preservar a ação e o timing contratados, sem clone/rename.
Elementos AIR distintos podem usar a mesma imagem; não exigir mudança RGB
em cada elemento nem fundir holds para satisfazer um gate. Idle periódico pode
terminar no mesmo RGB inicial. Medir a timeline completa e rever a ação do
ator: variação de HUD não prova animação (§97).
Hitstop/recovery são frames, não adjetivos. Scanline: `audit_sprite_line_sim.py`
antes de animar um elenco inteiro na mesma linha.
Gate: `audit_animation_semantics.py` (permutação, clone, ciclo idêntico, pivot, roster).

Importação AIR usa `air_identity_timing`/`--require-air-identity` (§100): IDs
fonte/ROM por N+1 fronteiras, incluindo terminal. O produtor fonte
`mugen2sms/analysis/air_source_identity.py` registra IDs `ação:elemento`, SHA
do pacote/AIR, offsets, flips e CLSN; é source-only, não trace da ROM. Rejeita
LoopStart explícito e duração infinita/ambígua no perfil de passagem finita.
Não converter automaticamente guard hold `-1`, GUARDEND ou fases de salto
em loop local e chamar isso de fidelidade. Declare a política no manifest,
os papéis consumidos e as limitações; veja `sms-mugen-source-semantics.md`.

Review independente: `quality_review_router.py` domínio `animation`.
Não simule aprovação humana da incumbente.
