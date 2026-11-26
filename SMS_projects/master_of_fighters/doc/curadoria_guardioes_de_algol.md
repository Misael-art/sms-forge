# Guardiões de Algol · caderno de curadoria

## O tiro de Odin · conferência com o primeiro Phantasy Star

**Decisão de direção.** Manter Odin com a Laser Gun no segundo plano. Na ficha de equipamento do primeiro jogo, a própria Sega associa a Laser Gun a タイロン, o guerreiro chamado Odin na versão em inglês. O manual americano registra que ele começa com o Iron Axe, que só ele pode usar a Needle Gun e que a Laser Gun continua útil no fim da aventura. As duas armas contam a mesma história de personagem. [Armas no guia oficial da Sega](https://www.sega.jp/fb/album/07_ps/play.html) · [Manual americano do Master System, seção Weapons](https://www.smstributes.co.uk/images/db/manual_phantasystarusa.pdf)

No roteiro do fan game, Odin ergue a arma, o clarão nasce na boca do cano e o feixe parte dela. Noah responde com Thunder, Myau come a Noz de Laerma e mergulha alado, e Alis fecha com a Espada Laconiana. A montagem dos quatro ataques e o uso ofensivo do mergulho são coreografia de *Master of Fighters*. A pose, a cor do laser e sua cadência são decisões da nossa direção de arte. O clarão, o feixe e a reação do defensor continuam editáveis separadamente.

A ficha de Alis também identifica duas adaptações. A provocação inspirada em Chat recupera Reiki no duelo. O Mirror Counter de Alis homenageia o Mirror Shield, que o manual original descreve como escudo de Odin. Assim a lista de comandos preserva essas propostas com atribuição explícita. [Manual americano, seções Shields e Magic](https://www.smstributes.co.uk/images/db/manual_phantasystarusa.pdf)

## Integração com a camada de elenco

1. Conferi o repasse com os fontes da branch. A R2 tinha a ficha de regras e os tempos de impacto. O checkout já continha também a conversão do aparo, dos comandos físicos e dos materiais de som em dados. A versão G4 ainda aplicava dano e Reiki por um caminho próprio para projéteis.
2. Na G5, liguei os gestos às fichas e o contato dos projéteis à reação do motor. A coleta por atacante eliminou dano duplicado quando duas chamas ocupavam a mesma caixa no mesmo passo. Dois tiros fortes simultâneos deixaram ambas as lutadoras com 90 PV e duas unidades de Reiki. A amostragem encontrou um registro parcial durante o congelamento. O replay passou a medir o intervalo entre os contadores de apresentação do acerto e da retomada, preservando também cada amostra íntegra. [Troca no emulador G5](../out/qa/alis_guardioes_g5/trade/observations.json)
3. Medi a G5 antes de mexer no vídeo. Na carga mista, 27 de 3.000 apresentações terminaram fora do VBlank. O primeiro caso registrou oito tiles de upload e 133 bytes da tabela de sprites. Na carga de magias, foram 74 ocorrências. Usei esses dois testes como referência para a revisão seguinte. [Carga mista G5](../out/qa/alis_guardioes_g5/worst/observations.json) · [Magias G5](../out/qa/alis_guardioes_g5/spell-budget/observations.json)
4. Preparei relógio, Reiki, placas, aves e efeitos antes do VBlank. A fila reúne endereços e tiles prontos para o VDP. O motor atualiza os registros de quais poses foram publicadas depois da última escrita de vídeo. Os testes de sobreposição exercitam tanto a chegada de uma camada inferior quanto a saída da superior. Os testes do elenco exercitam outro vínculo entre gesto e ação, uma ficha sem o comando de Alis e uma ficha ambígua que deve ser rejeitada.

## Parecer de arte, 26 de novembro de 2026

O proprietário reconheceu o estilo de Phantasy Star na prancha de seis ilustrações. Identificou dois problemas para o jogo de luta. O quadro final reunia atacante, espada e vítima no mesmo desenho, o que obrigaria a ilustrar cada confronto. Os outros planos dependiam de uma troca de telas inteiras para produzir movimento. A prancha original fica identificada como referência de direção. A reação da vítima, o corte e as exposições locais são recursos independentes do cartucho.

Com N personagens e um final por atacante, uma ilustração por par exigiria até N² composições, incluindo espelhos. A solução tem uma sequência por atacante e uma reação reutilizável por defensor. O custo real depende da quantidade de tiles, mapas, efeitos e alinhamento dos bancos. Os 90% citados na proposta são uma expectativa para um elenco maior. A medida desta construção fica no relatório de empacotamento.

## Ordem de produção reproduzível

1. Registrar a solicitação, a imagem original, sua função e seu SHA-256. Fixar identidade, cor, orientação, silhueta, objeto em uso e intenção de cada pose. A referência de luta determina as condições do F. Anime. Phantasy Star determina equipamento e elenco.
2. Aprovar a leitura do confronto no papel. O corte de entrada de Alis confirma o acerto no duelo. O close de Alis introduz o ataque. Odin dispara, Noah invoca Thunder, Myau come a noz, o Myau alado mergulha e Alis termina com a Espada Laconiana. A vítima ocupa um plano próprio depois do corte da atacante.
3. Produzir a folha de peças separadas com transparência e margem. Guardar o original, o recorte por peça e a origem. Para o capítulo espelhado, os dois trajes de Alis usam uma reação. O registro de Hayato usa outra silhueta, que só entra quando o alvo tem a identidade dele. Um novo lutador exige sua própria reação.
4. Fixar âncoras na resolução de trabalho. Entregar uma base limpa e duas sobreposições RGBA registradas nos planos de atuação. Comparar a recomposição com cada exposição pixel a pixel. A reação precisa de uma única pose por identidade. A sobreposição de corte e o deslocamento produzem o impacto nessa pose.
5. Separar as microações. No close de Alis, mexer a boca, duas mechas e o brilho da lâmina. No laser de Odin, alternar o clarão do cano e a luz do feixe. Em Noah, animar boca e reservar três índices só para os raios. Em Myau, deslocar a mordida na noz e alternar entre asas abertas e semiflexionadas no voo. Reservar três índices para as linhas azuis. O torso e os olhos devem continuar legíveis a 256×192.
6. Converter para a paleta SMS. Cores visualmente iguais podem ter índices diferentes para o personagem e para o efeito. Registrar os índices e inspecionar o ciclo sobre cada material. Enquadrar cada arte em letterbox. Medir os padrões únicos dos dois quadros juntos e o espaço de cada página na ROM.
7. Pré-carregar os padrões do plano com o display apagado. Durante a atuação, publicar apenas as entradas modificadas da tabela de fundo. Dividir uma diferença extensa entre VBlanks. No impacto final, usar a reação escolhida por identidade e o corte com padrões de sprite independentes. Contar os sprites por linha do efeito. Medir também o comportamento real.
8. Integrar os gestos aos dois controles. Registrar versão curta e forte, custo, recuperação, interrupção, alcance, reflexão e limite de vida. A finalização só pode consumir Reiki quando elegível e a sequência só começa se o corte atingir o rival ainda tonto.
9. Testar o caminho público em sessão privada, começando no título. Ligar evidência à ROM exata pelo SHA-256. Conservar as entradas, amostras de vida e Reiki, poses, contador e captura em movimento. Registrar cronologia, pior quadro, intervalo de FPS, som, retorno ao resultado e encerramento da sessão. Separar as observações dos valores de projeto.
10. Para o próximo personagem, reutilizar os contratos de controle, leitor de reação e sobreposição. Avaliar identidade artística e contrajogo por confronto. Registrar pendências sem promover um candidato ao elenco aprovado.

## Fontes de reprodução

- [Prancha, recortes e linhagem](../data/source_art/scenes/alis_guardioes/lineage.json)
- [Preparação de camadas e deltas de animação](../tools/alis_guardians_panels.py)
- [Empacotamento de páginas e dos efeitos da arena](../tools/pack_alis_magic.py)
- [Ficha de repertório e equilíbrio](padrao_moveset_especiais.md)
- [Planos, ocupação e pico do corte](../out/diagnostics/alis_guardioes_a/camadas/contrato.json)

## Diário técnico do lote

| Ordem | Observação | Decisão e verificação |
|---|---|---|
| 1 | A primeira prancha continha os dois combatentes no último quadro. | Conservar o original e excluí-lo como composição completa do cartucho. Isolar o gesto de Alis e gerar separadamente as vítimas e o corte. |
| 2 | A primeira conversão dispunha seis páginas inteiras e alternava somente paleta. | Passar a bases registradas, sobreposições RGBA, índices exclusivos e diferenças de mapa por exposição. O empacotador testa a recomposição de cada PNG. |
| 3 | As duas posições grandes das asas excederam a região antes da tabela de fundo, com 479 padrões para um limite de 448. | Enquadrar o voo de Myau a 192×96. Medir de novo com as duas posições presentes e corrigir o recorte das penas sobre o peito e a orelha. |
| 4 | O primeiro link ultrapassou o limite do banco fixo. O conversor recusou a ROM. | Compartilhar os 25 padrões do corte e os oito padrões da barra crítica no espaço livre da página de reação. Conferir no mapa o fim da área fixa e repetir a compilação. |
| 5 | O capítulo aceita dois trajes para a mesma identidade de lutadora. | O despachante recebe o ID do lutador que sofreu o golpe. Alis rosa e verde usam a mesma pose. O corte desenhado pelo VDP tem 25 sprites e pico calculado de quatro na mesma linha. |
| 6 | Na G2, a guarda contra a CPU apresentou 31,35–32,84 quadros de luta por segundo nas três janelas. A G2 também fazia o teste das espadas e da cor de vida já dentro do VBlank. | A G3 reaproveitou a leitura do direcional mantido e deixou de planejar magias quando nenhuma estava ativa. A mesma guarda subiu para 36,62–39,76. A G4 passou a calcular as prioridades de fundo antes do VBlank e a escrever a vida crítica pelo mesmo pacote do HUD. |
| 7 | A captura de um plano logo depois da troca de banco ainda podia conter o apagamento do quadro anterior. | Conservar esses quadros no vídeo e capturar cada foto depois da varredura da nova exposição. Repetir a entrada completa até a vitória e a revanche. Conferir o resultado com a ROM atual em cada tentativa. |

## Peças para editar

O [pacote editável com todos os planos](../out/candidates/alis_guardioes_g4/Camadas_Guardioes_de_Algol.zip) reúne 85 arquivos. Na pasta de cada plano, `base.png` recebe `camada-0.png` ou `camada-1.png` com a origem em (0, 0). Os arquivos `sms-0.png` e `sms-1.png` mostram a equivalência já quantizada. Cada plano com luz animada também tem uma placa `sem-efeito` e um PNG transparente `efeito-3-cores` por exposição. A integração de outro final recebe o ID do alvo, a duração e duas funções do próprio atacante para preparar e desenhar o efeito. [Raios de Noah](../out/diagnostics/alis_guardioes_a/camadas/noah/efeito-3-cores-0.png) · [Linhas de voo de Myau](../out/diagnostics/alis_guardioes_a/camadas/myau/efeito-3-cores-0.png) · [Corte separado](../out/diagnostics/alis_guardioes_a/camadas/corte.png)

## Receita para o próximo curador

Use os diretórios do capítulo indicados no README e o Python de `tools/sms_wrapper/run_host.sh rtk proxy python3`. O empacotador usa Pillow, eSpeak e FFmpeg do ambiente existente. A voz curta **“Algol!”** parte de síntese em português com eSpeak e passa a níveis de volume do PSG. As falas do jogo original e gravações comerciais não são insumos desse som.

Com a pasta de painéis E2 preparada, as entradas para reproduzir a candidata a partir da raiz do workspace são as seguintes. Execute o empacotamento, a compilação e as sessões oficiais em sequência sob o launcher de capacidade do host.

```sh
p=SMS_projects/master_of_fighters
h=tools/sms_wrapper/run_host.sh
d="$p/out/diagnostics/alis_guardioes_g6"
base="$p/out/diagnostics/alis_espacoporto_e2/panels"
c="$p/out/candidates/alis_guardioes_g6e_rebuild"
"$h" rtk proxy python3 "$p/tools/pack_alis_magic.py" "$base" "$d"
"$h" rtk proxy python3 tools/sms_wrapper/build_inner.py --project "$p" --manifest "$d/chapter.json" --build-dir "$c"
```

Para repetir uma observação, forneça um novo diretório de evidência ao `tools/replay_alis_magic.py`, após o diretório de build. O modo padrão prepara o final de P1 pelos controles. `--story` exercita Fire contra a CPU. `--story-move myau` reproduz o chamado de Myau na campanha. O argumento aceita também os demais especiais, incluindo `tontura` e `guardioes`. `--p2-final` exercita o lado oposto. `--range` testa as trajetórias até a borda. `--spell-budget` carrega o quadro com comandos dos dois jogadores. `--sound` grava a saída do próprio emulador pelo monitor privado. O replay preserva as entradas reais e fecha cada sessão.

A curadoria pode reproduzir também o verificador de exposições. Execute `tools/verify_alis_guardians.py --self-check` e depois o mesmo script com o diretório de empacotamento, o diretório de evidência do replay padrão e a sessão privada correspondente. Ele compara o framebuffer RGB inteiro com as exposições e as rotações possíveis de paleta. No impacto, acompanha a posição da cor do corte sobre a vítima.

A silhueta adicional de Hayato está em estudo. A seleção jogável do Espaçoporto oferece Alis em dois trajes. A revisão de Hayato no confronto e a homologação artística da silhueta continuam abertas para a incorporação dele ao capítulo.

Para reproduzir o teste de regras no host, a bancada abaixo liga as mesmas funções de gesto, movimento e caixa vulnerável do perfil do capítulo. Ela verifica os limites 24/25/26 dos dois lados, a falta de uma unidade de Reiki, o round inelegível, a ausência de tontura, a cura interrompida, o intervalo de Chat e a propriedade do tiro refletido. O alcance máximo também é isolado com uma vítima aérea fora das duas curvas.

```sh
cc -std=c99 -fpack-struct=1 -O1 -DMOF_DUEL_HOST_TEST -DMOF_ALIS_MAGIC -DMOF_ALIS_CHAPTER \
   -DMOF_ALIS_RIPOSTE -DMOF_DUEL_SCENE_POSTURES -DMOF_DUEL_SCENE_CROSSOVER \
   -DMOF_DUEL_SCENE_MIRROR -DMOF_DUEL_SCENE_SPECIALS -I"$d" \
   "$p/tools/test_alis_magic.c" "$p/src/alis_magic.c" "$p/src/duel_rules.c" \
   "$p/src/duel_motion.c" "$p/src/duel_commands.c" -o "$c/test_alis_magic"
"$c/test_alis_magic"
```

## Resultado da candidata G4 no Emulicious

O cartucho de 1 MiB tem SHA-256 `21c43ff6fdb5f9241e33fb76f0ee6a624316d5078cf03b48cd292a2ed93ea9c0`. No Versus, P1 iniciou o final com 16 PV e 8 Reiki contra uma P2 tonta com 20 PV. O corte consumiu a barra, os sete planos apareceram, a vitória foi atribuída a P1 e a revanche repôs 100 PV em cada lado. Em outra partida, P2 iniciou o golpe pelo lado direito com 20 PV e venceu com o comando espelhado. Na História, o jogo aceitou Fire durante o combate com a CPU. [Versus](../out/qa/alis_guardioes_g4/versus2/observations.json) · [Final de P2](../out/qa/alis_guardioes_g4/p2-final/observations.json) · [História](../out/qa/alis_guardioes_g4/historia/observations.json)

A inspeção dos 344 quadros nativos encontrou correspondência RGB exata com as duas exposições completas de cada um dos seis planos de atuação. Encontrou as três fases de paleta no laser, nos raios e nas linhas de voo. Sobre a reação de Alis, o corte passou por 36 posições observadas. A captura contínua com som usa outra sessão do mesmo SHA. Tem 437 quadros de 256×192 e 7,30 s de sinal do monitor privado do emulador. [Contagem de exposições](../out/qa/alis_guardioes_g4/versus2/prova_camadas.json) · [Vídeo com PSG](../out/qa/alis_guardioes_g4/som/guardioes_com_som.mp4)

O piso de 58 FPS reprovou. As três janelas de guarda na História mediram 36,626440, 39,759629 e 37,254583 FPS. No Versus com normais e contato, as janelas por publicação deram 37,951071, 40,447852 e 37,951071 FPS. No exercício dos dois jogadores lançando magias, 35 janelas mediram de 21,472316 a 48,936907 FPS. O contador selado aos 3.000 quadros marcou 27 saídas do VBlank na carga normal e 104 na carga de magia. Na G3 a carga normal havia registrado 84. O orçamento gráfico continua aberto para integração ao trabalho do motor. [Sonda em tempo real](../out/evidence/sessions/bdc072a6491a46e2a14e7ce20f067d32/runtime/fps.json) · [Pior quadro de contato](../out/qa/alis_guardioes_g4/worst/observations.json) · [Carga de magias](../out/qa/alis_guardioes_g4/spell-budget/observations.json)

No host Jupiter o lote usou um job por vez, reserva participante para 760 MiB de RAM e 170 MiB em disco, heap do emulador de 256 MiB e temporários privados em disco. O launcher adiou a compilação enquanto outro projeto ocupava o host. A bancada C passou a usar alinhamento de um byte para reproduzir o layout Z80 dos 492 bytes do estado. O mapa confirmou o símbolo em `C900` e a auditoria encontrou 103 bytes livres antes do corredor das sondas. Os estados, inputs e mídias de cada sessão permanecem associados à ROM que os produziu.

No teste de alcance, os pivôs ficaram nos limites da arena, x=43 e x=212. A rival saltou sobre as chamas. As duas saíram pela borda da tela, com 18 e 17 alturas distintas durante a amostragem. A primeira tentativa de QA havia exigido uma distância maior que a possível entre os pivôs. O replay passou a ler o limite real do cabeçalho da arena. [Trajetórias e entradas](../out/qa/alis_guardioes_g4/alcance/observations.json) · [Recibo consolidado do lote](decisions/2026-11-26_alis_guardioes_g4.json).
