# workflow: first-playable-slice

Use depois de GDD/TDD e antes de produzir um elenco, conjunto de fases ou arte
final completo. Vale para qualquer gênero SMS; `mugen-engine-quality.md` é a
especialização de conversão MUGEN. O slice é uma prova pequena do jogo real,
não uma tela de boot que imita uma entrega.

## 1. Travar a interação

- Ler GDD, spec de cena, TDD e memory bank; listar o que entra e o que foi
  explicitamente excluído. Não inventar cenário, modo, personagem ou efeito.
- Descrever um ciclo jogável curto: entrada → estado/ação → feedback visível →
  consequência → retorno, derrota ou reinício, conforme o gênero.
- Escolher a menor fatia que usa o runtime pretendido. Plataforma: mover/saltar
  e pousar; combate: dois atores, controle, defesa, um golpe, impacto e dano;
  puzzle: selecionar, executar e atualizar o tabuleiro. São exemplos, não
  conteúdo imposto ao GDD.

### Do beat ao caso observável

Parta dos beats identificados no roteiro. Para projetos novos, confira a
cobertura com `audit_specialization.py --project PROJETO --slice-plan`.
Leve o mesmo ID ao storyboard, à coreografia e ao caso de QA. Na captura,
anote ROM, sessão, entrada consumida, tick da consequência, quadro visível
e primeiro controle aceito. Uma variação negativa deve distinguir sucesso
de falha. A aprovação do plano indica que os casos foram escritos.

| Família prevista no GDD | Ensaio no primeiro trecho em que aparece |
|---|---|
| Repouso (idle) | Observar a pose neutra e a primeira ação após ficar parado. Se houver ciclo, filmar a volta ao primeiro desenho, com silhueta, apoios, equipamento e pivô legíveis a 1×. Para repouso estático, observar estabilidade e saída. Soltar a direção e verificar ausência de deslocamento involuntário. |
| Locomoção | Em plataforma, acompanhar partida, frenagem, virada, salto, ápice e pouso previstos. Comparar pé visível com o chão e a caixa usada pela física. Ensaiar a última posição de apoio e a primeira fora da borda, nas condições de câmera do trecho. |
| Projétil | No tick da emissão, alinhar a origem física ao ponto visível da mão, arma ou nave. Acompanhar trajetória, contato, erro e remoção enquanto o emissor volta a agir. Exercitar limite do pool, saída de tela e limpeza na troca de cena. |
| Golpe | Observar preparação, primeira/última caixa ativa, pose no contato, reação e recuperação. Repetir no limite de alcance e imediatamente além. No duelo, aplicar [lutador jogável](playable-fighter.md) para guarda, prioridades e contrajogo. |
| Efeito | Ligar início e fim ao evento que o gera. Repetir sem o evento e no pior cruzamento com ator, cenário, HUD e áudio. Verificar se os pixels comunicam a consequência e se o efeito libera os recursos e canais ao terminar. |
| Troca de cenário | Reproduzir a saída e a primeira ação no destino, inclusive mantendo o botão pressionado. Conferir câmera, posição, paleta, HUD, música e objetos que persistem ou são limpos. Repetir saída/reentrada quando a rota permitir. |
| Cutscene | Para cada passagem, identificar quem tem o controle, pose, enquadramento, deixa visual/sonora e condição de término. Testar reprodução completa e skip quando autorizado, inclusive no limite da troca. Comparar estado e primeiro comando jogável no destino das duas rotas. |

Para puzzle, o ciclo pode ser selecionar, aplicar uma jogada válida,
recusar uma inválida e devolver o cursor. Outras famílias específicas podem
ganhar linhas no roteiro. Para plataforma, o acervo de Kage Matsuri oferece
movimento, corte e chegada ao torii em uma única rua. Projétil e cutscene
recebem casos próprios quando outro GDD os inclui.

Por exemplo, numa plataforma que autoriza disparo e vinheta de saída, B01
pode ser o pouso seguido do tiro e B02 a passagem pela porta. O tiro que
passa ao lado deve desaparecer sem dano. Entrar pela porta com o botão
ainda pressionado permite verificar se a vinheta entrega o controle sem
emitir um segundo tiro. O mesmo teste pode cobrir projétil, efeito e troca
de cenário quando cada consequência tem um ponto de observação identificado.

Conforme o GDD, acrescentar linhas para HUD, recursos, som, IA ou lógica de
tabuleiro. A barra deve comunicar a menor mudança relevante; dois sons que
disputam o PSG devem permitir a retomada do canal. Para CPU que reage ao que
vê, variar a entrada oculta mantendo o mesmo estímulo visível. Para replay
determinístico, repetir a entrada por tick e identificar o primeiro estado
divergente. As escolhas de guarda, prioridade de golpes e punição do duelo
pertencem à especialização de luta.

Para animação consulte [poses e atuação](../skills/sms-sprite-animation.md);
para mudanças de controle use o [contrato de transição](../skills/sms-state-transitions.md).
Use o framebuffer em velocidade normal para julgar leitura e ritmo. Analise
o primeiro quadro divergente por stepping e repita o caso em execução
contínua com a carga real antes de expandir personagens, fases ou efeitos.

## 2. Pagar a conta antes da arte cara

Registrar para as telas do slice: recursos que coexistem, RAM/ROM/bancos,
residência de padrões, bytes por pose/transição, upload por VBlank, custo de
CPU, pior frame, SAT e pico por scanline. Somar HUD, projéteis e efeitos ao
mesmo quadro quando aparecem juntos. Análise estática define uma hipótese; o
budget de runtime só fecha na ROM medida.

Para sprites, validar arte e coreografia com `audit_sprite_line_sim.py` antes
do runtime. Para animações, medir geometria/pivô por quadro e poses únicas
quando exigidas (`audit_animation_semantics.py`). Conteúdo de placeholder fica
quarentenado e nunca vira personagem ou tela final.

## 3. Implementar uma fatia completa

Implementar somente o caminho escolhido, mantendo o estado inicial
determinístico. Instrumentar, conforme o jogo, entrada aceita, estado, quadro
de animação, colisão/evento, valor de HUD e resultado. Em ação de combate,
deixar explícito quando a pose sinaliza o impacto e quando a regra causa dano;
uma atualização lógica rápida com arte atrasada continua sendo uma falha de
feedback.

Instrumentar desejado/residente/submetido separadamente quando existir cache;
um probe com nome `disp` pode registrar current sem que o ator seja desenhado.
Para conferir asserts dos reads e prazos VDP observados, consultar
`skills/sms-observed-case-evidence.md` / `audit_observed_cases.py`. A imagem
apresentada continua dependendo de captura alinhada. Não exigir que um baseline
diagnóstico já passe: preservar suas falhas e produzir candidato com identidade
própria; não reescrever o baseline para parecer pronto.

Compilar pelo wrapper e rodar no emulador com uma sequência de entrada
reproduzível (`emulator_input.py`). Capturar vídeo de framebuffer para provar
movimento e transições (`capture_video.py`); usar probe de RAM para estado, não
como substituto da captura visual. A leitura DAP pausa o jogo e não é uma
amostra de cada frame. Quando uma trilha temporal for necessária, a ROM de
diagnóstico registra os estados durante o próprio loop e sela a captura depois.

## 4. Gates de decisão

- `measure_fps.py` mede velocidade de emulação; `measure_frame_advance.py`
  mede o relógio da ROM. Não trocar um pelo outro.
  Probe privado exige objetivo60/piso58FPS em todas as janelas (SMS_GLOBAL §133);
  PAL50 e a faixa histórica50–60 não aprovam. Taxa das janelas não prova pacing ou
  reação da lógica; aplicar `product-quality-checkpoint.md`.
- Medir resposta da entrada, tempo até feedback/pose e consequência da mecânica
  com instrumentação adequada ao projeto. Para combate, conferir pose, hitbox,
  evento de dano e atualização de vida na mesma linha temporal.
- Medir `measure_worst_frame.py`, SAT/scanline e uploads para o caso mais caro
  do slice. Limites: no máximo 64 sprites na SAT, 8 por linha e transferências
  em massa dentro do VBlank.
- Gravar os eixos não aplicáveis como fora de escopo, não como PASS. PAL,
  áudio, menus e modos só sobem de status quando a fatia incluir e medir esses
  recursos.

Avançar para o próximo personagem/ação/tela quando a ROM observada completa o
ciclo escolhido, responde a input, apresenta feedback coerente, mantém o frame
counter regular e passa o budget medido aplicável. Atualizar memory bank com
SHA da ROM, vídeo/traces, números, limites e próximo bloqueio causal. Se falhar,
atribuir a causa por medição e mudar o menor contrato que a resolve; não
mascarar o atraso congelando a simulação, escondendo o hit ou promovendo uma
captura de boot.
