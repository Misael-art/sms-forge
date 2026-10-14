# Sessões privadas de Emulicious para SMSForge

Autorização: pedido do dono em 2026-10-05, aplicando ao SMSForge o plano de
isolamento de testes do SGDKForge. Escopo de escrita: fábrica e documentação.

## Decisão técnica

O método do plano do SGDK é aplicável: display privado, controles dentro do
processo, identidade da sessão e evidência ligada ao binário. A ponte SDL2 do
BlastEm não se aplica ao Emulicious Java. A adaptação conecta dois `SMSJoypad`
virtuais às portas emuladas e um provider separado dos controles de console.
O JAR original permanece byte a byte intacto e seu SHA é verificado antes de
iniciar. A integração usa APIs do emulador e reflexão para parar/iniciar seu
runner; uma mudança de JAR bloqueia a rota até nova prova de compatibilidade.

Xvfb fornece um servidor gráfico exclusivo, com cookie Xauthority e sem TCP.
Bubblewrap esconde `/dev/input`, `/dev/uinput` e os outros sockets X do caminho
de arquivos da JVM. O launcher desativa JInput e conecta somente seus próprios
providers à ROM. Não há joystick global, captura de teclado físico nem mudança
de foco do desktop. Referências: [manual Xvfb](https://xorg.freedesktop.org/archive/X11R7.0/doc/html/Xvfb.1.html),
[JInput](https://github.com/jinput/jinput) e [Emulicious](https://emulicious.net/downloads/).

## Implementação disponível

- `emulator_session.py isolated`: preparar runtime, iniciar, consultar,
  pausar, rodar em tempo real, input, sequências, leitura de RAM, screenshot,
  vídeo, publicar, verificar bundle e encerrar por sessão.
- `session_bridge/ForgeSMS.java`: controles P1/P2 locais ao processo e callback
  `frameFinished` do dispositivo emulado. Polls de input e sleeps não contam
  frames. Sequências são uma transação e soltam todos os botões ao concluir ou
  falhar. A ponte só lê RAM; não injeta comandos escrevendo no jogo.
- `session_bridge/isolated.py`: supervisor, TTL, display autenticado, socket
  Unix com sessão/token/seq, PID acompanhado de start ticks, configuração,
  ROM, cache e evidência privados. O supervisor encerra apenas seus filhos.
- `capture_evidence.py --session`: screenshot nativo, sem moldura/compositor,
  com hash de ROM, JAR, ponte, fonte da ponte e configurações.
- `capture_video.py --session --ticks N`: um framebuffer nativo por frame do
  VDP. A reprodução usa a frequência nominal do sistema; não prova performance
  em tempo real e não contém áudio.
- `measure_runtime_probe.py --session`: lê o probe canônico SMRT da ROM,
  usa o runner original em tempo real e uma reserva global para medições
  cooperativas. Registra carga do host; não transforma FPS do título em FPS
  de gameplay. Os testes funcionais podem coexistir.
- `emulator_input.py --session --script`: roteiro JSON em frames, sem foco.
- `capture_audio.py --session`: monitor privado do PID exato, duração efetiva
  ≥95% da solicitada, pausa ao terminar e falha se a rota mudar. Boot começa
  com `-muted`; a ponte envia somente zeros até a confirmação da rota. A linha
  permanece aberta nas pausas para o backend não recriar um fluxo no sink
  padrão. Um keepalive envia zeros durante mute/pausa, pois manter a linha
  aberta sozinho não foi suficiente nos testes repetidos. Buffers do boot são
  descartados antes de liberar as amostras da ROM. Mudança da rota recusa avanço.
- `luta_mugen_trace_dap.py`: o produtor de trilha passa a abrir uma sessão
  privada e ler blocos de RAM por ela. O nome histórico da função é preservado;
  não abre mais uma porta DAP fixa nem exige matar outros emuladores.
  A migração está implementada, mas a ROM de trilha atual não passou na prova:
  `trace_buf` em 0xC800 sobrepõe `tl_snap`, `frame_cache_storage` e
  `pose_runtime_cache`. O produtor agora exige o gate de RAM antes de iniciar;
  o mapa do fixture deve ser corrigido antes de promover a integração.

O SMS usa direções e botões **1/2** em cada controle. Pause é um botão do console
que gera NMI; Reset também pertence ao console. Start do Game Gear e controles
Mega Drive de seis botões precisam de perfis e provas próprios. Não se importam
os masks A/B/C/X/Y/Z do SGDK.

## Preparação e uso

Java 17+, Bubblewrap, Pillow e FFmpeg são necessários. Áudio real também exige
`pactl` e `parec`; sem rota privada confirmada, a sessão permanece em mute.
A compilação da ponte
aceita javac ou Eclipse ECJ. Neste host, Xvfb e ECJ foram materializados apenas
em `out/session_bridge/runtime/`; nenhum pacote global foi instalado.
Proveniência e hashes ficam em `out/session_bridge/runtime/provenance.json`.
Se o runtime privado for removido, preparar novamente com os pacotes locais:

```sh
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated prepare-runtime \
  --xvfb-package /caminho/xorg-server-xvfb.pkg.tar.zst --ecj /caminho/ecj.jar
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated start /caminho/jogo.sms
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated status ID
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated input ID --p1 16 --p2 8
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated step ID 17
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated input ID
rtk proxy python3 tools/sms_wrapper/capture_evidence.py --session ID --project /caminho/projeto --frames 1
rtk proxy python3 tools/sms_wrapper/emulator_session.py isolated close ID
```

`input` substitui os masks completos e pausa a execução; sem masks ele solta
todos. `run` mantém os masks no runner real até a próxima operação que pausa.
Para gestos com prazo exato, usar uma sequência atômica. Exemplo de arquivo:

```json
[{"p1":2,"frames":4},{"p1":10,"frames":4},{"p1":24,"frames":3}]
```

```sh
rtk proxy python3 tools/sms_wrapper/emulator_input.py --session ID --script roteiro.json
rtk proxy python3 tools/sms_wrapper/capture_video.py --session ID --ticks 120 --out movimento
rtk proxy python3 tools/sms_wrapper/measure_runtime_probe.py --session ID \
  --project /caminho/projeto --seconds 8 --janelas 2
```

O ACK de `input` confirma recebimento e estado das portas do emulador. Um claim
de controle/golpe ainda exige ler o probe/gravador da ROM e o estado do oponente.
O fixture `controls_probe.c` faz essa leitura via SMSlib, conta frames de cada
botão e escreve identificadores diferentes na SRAM. Não é arte de jogo.

Publicações têm diretório exclusivo por sessão, lock por destino e rename
atômico. O verificador recusa hashes/configuração/ROM divergentes ou uma captura
sem informação. Não escolher a última pasta por data para determinar a ROM;
consumir o ID e o SHA retornados pela operação.

## Aceitação reproduzível

```sh
rtk proxy python3 tools/sms_wrapper/session_bridge/acceptance.py \
  --out out/local_study/sms_isolated_session/aceitacao \
  --xvfb out/session_bridge/runtime/xvfb/usr/bin/Xvfb
rtk proxy python3 tools/sms_wrapper/session_bridge/audio_acceptance.py \
  --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms \
  --out out/local_study/sms_isolated_session/audio_acceptance
```

A bateria usa duas ROMs simultâneas, testa os seis controles de cada porta,
17/29 frames exatos em paralelo, Pause/NMI, SRAM, mensagens inválidas/atrasadas,
teclado enviado somente ao display de teste, vídeo nativo, probe SMRT e morte
restrita à sessão. Verifica `/dev/input` e `/dev/uinput` no namespace de cada
JVM. Não digita no desktop do dono. Os resultados pagos e os limites estão em
`doc/curation/2026-10-05_l057_sessoes_privadas_emulicious.json`.

## Continuação do plano: gates ainda abertos

1. **Fidelidade de áudio.** Boot em mute, rota privada, captura de sinal/duração
   e encerramento têm prova em emulador. Comparar trechos alinhados da ROM alvo
   e da referência conhecida antes de afirmar equivalência musical. O teste
   de mute mede somente o monitor privado e não grava o áudio pessoal do host.
2. **Joystick físico/hotplug.** A negação de acesso aos dispositivos foi
   observada na JVM; uso/conexão de um controle físico real ainda precisa de
   uma rodada acompanhada. Registrar input observado antes/durante/depois.
3. **Compatibilidade com referência.** O núcleo binário não foi modificado;
   comparar renders, trilhas e áudio das ROMs alvo com a rota histórica em
   fixture controlado. Não anunciar equivalência total com base no boot.
4. **Adoção pelos consumidores.** A trilha Mugen e os capturadores centrais já
   têm a rota. Migrar os scripts locais conforme cada projeto adotar o contrato,
   sem sobrescrever `.agent` existente. Não foi localizado consumidor OpenBOR
   neste wrapper; quando existir, ele deve usar o mesmo ID/ROM SHA.
5. **Medição sob concorrência.** A reserva serializa medições cooperativas;
   outras aplicações do host ainda disputam CPU. Registrar sessões concorrentes
   e carga, repetir janelas e não atribuir degradação do host à ROM sem controle.

## Prompt de continuidade para um agente

Leia AGENTS, RTK, SMS_GLOBAL §93, este plano e a curadoria L057 vinculada.
Trabalhe na fábrica, preservando projetos e emuladores alheios. Use a sessão
privada existente; não substitua a ponte por teclado do host. Preserve o JAR
original e sua licença, valide o SHA e mantenha tokens fora dos artefatos
publicados. Separe ACK recebido, input aplicado no emulador e observação na
ROM. Duração de golpe vem de frame do VDP e contador da ROM. Cada implementação
nova precisa de self-check, caso válido/inválido e ROM diagnóstica real.
Execute os cinco gates abertos acima conforme o escopo autorizado. Preserve
os gates de isolamento já pagos e avance na comparação alinhada de referência.
Não feche áudio por silêncio, FPS por título ou gameplay por
diferença de screenshot. Atualize evidência, memory e ledger apenas com fatos
reproduzidos; mantenha limitações explícitas. Reuse L057/L039/L065, sem emitir
IDs duplicados. Não solicite novamente autorização para este escopo já pedido.
