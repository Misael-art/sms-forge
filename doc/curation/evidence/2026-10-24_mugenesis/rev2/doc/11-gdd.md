# GDD — luta_mugem_rev2

## Pedido e produto
MotorSMS reutilizável MUGEN→dados/config→runtime, com Ken e Ryu dos pacotes
MUGEN do consumidorSGDK como pilotos. Jogo1v1 em256×192; metaNTSC60/PAL50,
comandos responsivos e zeroomissões/flicker visível nas composições aprovadas.
São objetivos de aceitação, não resultados. Fundo sólido em TODAS as telas;
semcenário/backdrop nesta revisão. Escala default desde 2026-10-23:
encaixe CPS2→SMS (largura 2/3, altura 6/7) e pose neutra de cada lado em no
máximo 4 colunas de 8 px. Dois idles fecham em 8. Golpe largo contra pose
neutra fica em 5 e 3. O que passa disso entra em caso a caso, sem reautoria.
`POSE_NEAR` 0,69 não abre nem fecha a escala. A faixa histórica 72–88 px e o
quarto 1:4 permanecem opções (`doc/28-pose-budget-8.md`). Não é promessa de
viabilidade.

## Combate
Walk/crouch/jump/landing/guard/hitstun/blockstun/knockdown/getup/KO/win,
normais/proximidade/cancel/combos definidos na fonte, magias/projéteis, especiais
e supers/power, spark/efeitos fonte-orientados. Guard/facing/colisão dinâmicos,
recursos/vulnerabilidade/lifetime dos objetos, rounds/timeout/empate e retorno
consistentes. Hitstop/slowdown/shake moderados e finitos, medidos em frames,
sem confundir pausa intencional com stall por upload. Cada movimento fonte
precisa classificação exact/approximate/blocked/dropped_decision antes de aceitação.

## Apresentação e fluxo
Título identificador provisório +PressStart piscante; menuArcade/Versus/Treino/
Options; seleçãoKen/Ryu com retratos derivados de fonte rastreada; VS; início
round/fight, HUDvida/power/timer/rounds/hits; resultado/continue/final; pause.
Options: dificuldade, rounds, timer, controlesP1/P2, música/SFX, soundtest e
musicplayer. Treino: inputhistory/commandlist, reset, dummyparado/defesa/IA,
powerinfinito. Persistência inicial emRAM da sessão; save não solicitado.
Arcade elenco2 com CPU; Versus dois pads; treino perfisdooponente.

## Controles e áudio
PadSMS2botões+direções; Start/Pause do console separado. Perfil por personagem
extraídoCMD e adaptado por famílias/pressão/contexto; limiar candidato6ticks
precisa latência/ergonomia medidas. Combinações/botões inacessíveis explícitos,
sem descartar especiais silenciosamente; remapeamento limitado pelohardware.
SND é referência de semântica/identidade: saídaPSG autorada/adaptada e rastreada,
sem converterPCMMD/XGM2 em capacidadeSMS. VozFight opcional se viável/validada
no trecho deabertura; cuePSG ou alternativa previamente declarada se não couber.
Música de fonte/autoria registrada e reviewauditivo; importarSND não criaBGM.

## Aceitação e exclusões
MesmoCcore serveKen/Ken,Ryu/Ryu,Ken/Ryu eRyu/Ken, paletaP2 distinguível,
IAxIA/humanoxIA/humanoxhumano; trocar.def sem editar núcleo. Entrega requer
fontes→dados→símbolo→ROM/SHA, gameplay/vídeo/inputtrace, alvoFPSregional,
piorframe/RAM/VRAM/SAT medidos, áudio e revisão independente.
Sem personagens adicionais, cenário, online, MUGENcompatirre­strita, FMobrigatório
ou promessaAAA. Tradeoffs de fidelidade/arte precisam decisão explícita.
