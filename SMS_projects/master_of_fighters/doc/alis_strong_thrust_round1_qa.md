# Rodada 1 — roteiro de QA pendente

Este roteiro prepara testes; nenhum resultado de ROM foi observado. A condição
`MOF_ALIS_STRONG_HOLD` no visualizador existente seleciona o limiar
**provisório de 12 leituras consecutivas** do botão 1. A liberação zera a
contagem e rearma. Ao atingir o limiar fora da guarda, a pressão é consumida
sem enfileirar uma ação; outra tentativa requer soltura. O ramo normal do
visualizador continua selecionado sem essa definição. O visualizador atual
não liga um normal fraco: não inferir que o toque aciona soco nesta amostra.

Os endereços abaixo são provisórios e precisam passar no gate de corredor e
no `.map` da candidata antes da coleta. Valores são amostras da ROM, não ACK
da ponte: `C7F6` pose (zero é guarda), `C7F8` teclas, `C7F9` tempo
decorrido da pose, `C7FA` latch, `C7FB` contador de disparos módulo 256 e
`C7FC` contagem saturada da pressão. O contador
deve ser inicializado em zero na sessão; o incremento só acontece se a pose
estiver em guarda no limiar. Comparar deltas módulo 256 e limitar a janela
de modo a excluir múltiplas voltas, conforme `audit_counter_window.py`.

## Ramo experimental preparado nesta retomada

O seletor `MOF_ALIS_ROUND1` com `MOF_ALIS_STRONG_HOLD` está preparado em
`src/main.c`; manifesto `.mddev/alis_strong_round1_diagnostic_build.json`.
**Não foi compilado, executado ou validado no emulador.** O cabeçalho
gerado `out/diagnostics/alis_strong_thrust_round1/grounded_faces_assets_probe/both_faces_assets.h`
tem SHA-256 `c93fc4ebcd4a11b86e521758058394796aa76b6e46a9f35520ad346dc0e17a46`.
A fonte é a sequência exploratória, não as chaves corrigidas finais; escala
corporal de 68 px, qualidade artística e continuidade do gesto permanecem
pendentes. O ataque fraco não está ligado neste visualizador.

Controles planejados na guarda: botão 1 segurado aciona; botão 2 alterna face;
cima/baixo escolhem perto, limite e fora, ciclicamente. O indicador na linha
superior usa as três primeiras posições para distância, posição 5 para face
esquerda, 7 para janela ativa e 9 para interseção geométrica. A leitura de
alcance só aparece na extensão e não resolve bloqueio, acerto ou dano.
`C7FD` deve expor flags ativo/interseção/face nos bits 0/1/2 e `C7FE` a
distância 0/1/2; comprovar valores na ROM e auditar corredor após link.

A divisão de partes da lâmina para BG usa P0 igual a P1, 246 padrões SAT,
14 padrões BG mais um tile de HUD (480 bytes). As 24 cenas estáticas de
quatro poses, três distâncias e duas faces passaram no simulador oficial,
com máximo de 53 objetos na SAT e oito por linha. A reconstrução independente
dos dez metasprites e quatro conjuntos BG passou pixel a pixel em índices.
Isso não verifica as escritas dinâmicas da PNT nem o comportamento do VDP.
O resultado reproduzível está em
`out/diagnostics/alis_strong_thrust_round1/grounded_faces_assets_probe/static_check.json`;
o self-check do verificador inclui dados de sprites e de BG inválidos.
No estudo estático, os fragmentos BG se sobrepõem ao oponente em 25/2/0
pixels nas distâncias perto/limite/fora, em cada face: a prioridade efetiva
e a legibilidade precisam de comparação do framebuffer, sem presumir que
equivalem à composição com todos os elementos em sprite.

Em Y=108 da tela, a geometria do PNG convertido produz deltas visíveis de
8/0/−8 px entre ponta e borda frontal para as três posições. Os valores são
provisórios, sem calibração neutra aprovada ou colisão. A versão atual grava
esses resultados na lógica de alcance geométrico; qualquer ajuste de arte
deve atualizar e retestar as medidas e o diagnóstico. A checagem de
`audit_tilemap_bounds.py` deixou 14 coordenadas/entradas dinâmicas não
provadas; `alis_round1_data_check.py --grounded` verifica os dados gerados,
mas não comprova que o Z80 escreve os mesmos valores em tempo de execução.

## Entrada: executar no SHA exato da candidata

Preparar scripts em frames VDP, com baseline em guarda confirmado pela RAM e
framebuffer. Reconciliar latência da ponte e amostrar em fronteiras, em vez
de assumir que duração injetada equivale automaticamente a leituras da ROM.
Os roteiros iniciais em `.mddev/alis_strong_round1_input_scripts/` cobrem toque,
11/12/13 frames da ponte e pressão longa com soltura e segunda pressão. São
entradas preparadas, não resultados nem garantia de 11/12/13 leituras da ROM;
iniciar cada caso em guarda e medir as sondas. O caso da última leitura da
recuperação precisa ser sincronizado com o estado observado, não inferido do
tempo nominal de um desses roteiros.

O coletor `tools/alis_input_trace.py` prepara amostras de RAM por frame VDP
em sessão privada já aberta, checa o SHA informado e requer guarda solta como
baseline. `--mode press --hold-frames 11` (ou 12, 13, 90) coleta pressão e
soltura; `--mode last_recovery` tenta alinhar a segunda pressão pela sonda de
pose/tempo. `--capture-frames` acrescenta framebuffers selados. É um coletor
experimental: o self-check de offsets e o teste com respostas simuladas da
ponte passaram, inclusive a soltura após interrupção. Não foi ligado ao
Emulicious. Conferir os limites de cada amostra, a fronteira real da
recuperação e o corredor antes de tirar conclusões. Stepping não mede FPS.

| Caso | Sequência de leituras pretendidas | Estado/resultado esperado |
|---|---|---|
| Toque | 1 pressionada, soltar | Contagem retorna a zero; contador de disparos inalterado. |
| Limiar − 1 | 11 pressionadas, soltar | Contagem 11 antes da soltura, sem disparo; depois zero e latch zero. |
| Limiar | 12 pressionadas | Contagem 12, latch 1, contador +1 e entrada na ação. |
| Limiar + 1 | 13 pressionadas | Contagem saturada 12, contador +1; nenhuma segunda entrada. |
| Pressão longa | Segurar além de toda a recuperação | Uma execução; guarda restaurada, latch 1 e contador inalterado após a primeira. |
| Soltura e segunda execução | Soltar após a volta; pressionar 12 leituras | Contagem/latch zeram na soltura; contador +1 na segunda pressão. |
| Limiar durante recuperação | Soltar e voltar a segurar cedo, atingindo 12 com pose não zero | Sem disparo enfileirado ao retornar à guarda; soltar novamente rearma. |
| Última leitura da recuperação | Atingir 12 exatamente na leitura em que a última pose termina | A ordem atual consome a pressão antes de retornar à guarda; observar se exige soltura, e avaliar a resposta no alvo. |

Medir os frames de aperto → disparo → primeira pose apresentada → extensão,
separando o estado amostrado após a SAT da imagem que o VDP efetivamente
apresenta. Não substituir essas latências por duração declarada.

Fazer casos independentes em sessões novas ou declarar timeline encadeada,
com precondição explícita. Ler pose, contagem e contador por frame em torno
do limiar e da volta; capturar framebuffer para comprovar a apresentação.
Registros e vídeo devem ter ROM SHA e ID da sessão. O seletor de piloto
precisa estar definido na configuração de build e usar a arte correta;
ativar somente a flag com o par histórico não é candidata Alis/Hayato.

## Alcance e hardware

Depois das chaves calibradas, registrar por pose pivô inicial e atual,
apoios, mão, base e ponta, altura e borda de Hayato na mesma altura. Derivar
distâncias próxima, limite e fora a partir da pose ativa convertida; não
reutilizar os 36 px rejeitados. Para cada distância testar as duas faces,
recolher framebuffer e estado de janela ativa e alcance. Projeção geométrica
é distinta de acerto/bloqueio: só declarar colisão se a resolução existente
for efetivamente integrada e observada. Seletores de distância, face e
indicadores foram preparados no ramo experimental acima, mas ainda não foram
compilados nem observados na ROM.

Antes da execução, ler os workflows centrais de sessão privada. Verificar
os self-checks dos instrumentos e o SHA da ROM; medir P1, SAT, scanline,
VRAM e pior frame com ambos atores, incluindo degrau seguinte. O FPS real
precisa de pelo menos duas janelas válidas, cada uma ≥58 sem arredondar,
alvo 60, dispersão conforme §133; confirmar cleanup da sessão. Não
confundir vídeo por stepping com ritmo medido em tempo real.
