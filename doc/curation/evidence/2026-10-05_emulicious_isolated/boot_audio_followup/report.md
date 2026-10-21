# Fechamento do boot de áudio privado — 2026-10-05

Estado: implementado e testado em emulador no host atual, com JAR fixado.

## Resultado

- Boot inicia com `-muted` antes de carregar/executar a ROM; a linha recebe zeros.
- O supervisor confirma sink e PID reais antes de liberar PCM; buffers do boot são descartados.
- A linha permanece aberta e recebe keepalive silencioso durante mute/pausa. Apenas impedir stop/start/flush reprovou numa repetição.
- Recusar avanço quando o contrato de sink divergir da associação real. A fixture negativa altera o contrato, não o monitor do desktop.
- Captura limitada por prazo, duração mínima de 95%, pausa no final e remoção do sink após saída da JVM.
- Correção adicional: esperar a linha completa de displayfd do Xvfb antes de fechar o pipe. Falhas anteriores preservadas em `failures/`.

## Provas finais

- 8 verificações de áudio: `final/audio/audio_acceptance.json`.
- MSSF2T: 8,173 s para 8 s pedidos, pico 6012. Controle silencioso simultâneo: 8,173 s, pico 0.
- ROM sonora executando em mute: 2,229 s, pico 0 no monitor privado.
- 17 verificações de controles: `final/controls/acceptance.json`; comandos durante exatamente 17/29 frames, SRAM, vídeo, protocolo e limpeza.
- FPS diagnosticado sob carga concorrente: 58,85/58,70; pertence à fixture, não ao jogo. Não é prova de 60 FPS constantes.
- Fábrica: 71/71 selftest e 51/51 instrumentos; doc sync, learning capture e self-check de áudio aprovados.
- `inventory.json` vincula artefatos e versão das ferramentas. ROMs e pontes das sessões de áudio foram preservadas, assim como o estado final encerrado.

## Limites

A prova usa somente monitores privados; não gravou áudio pessoal nem demonstrou ausência audível em todo o desktop. O mecanismo bloqueia PCM de ROM durante o boot e a aceitação confirma roteamento/sinal no JAR/backend atuais. Políticas futuras ou mudanças de backend exigem nova aceitação.

Fidelidade musical com trechos alinhados, joystick físico/hotplug, adoção pelos scripts antigos e integração Mugen (RAM sobreposta em 0xC800) seguem abertos. Nenhuma aprovação de gameplay, qualidade AAA ou 60 FPS do jogo. Nenhum commit criado.
