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

Compilar pelo wrapper e rodar no emulador com uma sequência de entrada
reproduzível (`emulator_input.py`). Capturar vídeo de framebuffer para provar
movimento e transições (`capture_video.py`); usar probe de RAM para estado, não
como substituto da captura visual. A leitura DAP pausa o jogo e não é uma
amostra de cada frame. Quando uma trilha temporal for necessária, a ROM de
diagnóstico registra os estados durante o próprio loop e sela a captura depois.

## 4. Gates de decisão

- `measure_fps.py` mede velocidade de emulação; `measure_frame_advance.py`
  mede o relógio da ROM. Não trocar um pelo outro.
  Probe privado exige o alvo regional NTSC60/PAL50; 55FPS em NTSC não passam
  só por pertencer à faixa 50–60. Taxa média das janelas não prova pacing ou
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
