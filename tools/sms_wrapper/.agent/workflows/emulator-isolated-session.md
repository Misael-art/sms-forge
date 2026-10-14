# workflow: emulator-isolated-session

Emulicious é a rota principal de produção/QA. Para segunda observação de
Z80/VDP/mapper, veja `blastem-sms-diagnostics.md` e §108: BlastEm tem backend
diagnóstico próprio, áudio dummy e sem qualificação PAL/FPS. Não passar seu ID
às ferramentas `--session` de Emulicious nem simular coleta `session_qa.py`.

Aplicação de L057/L039/L065, SMS_GLOBAL §93. Teste automatizado deve tolerar
outros emuladores e o uso normal do host pelo dono.
Para QA com subagentes nativos em qualquer projeto: `subagent-emulator-qa.md`
e §94. Cada revisor possui sessão própria e devolve cobertura/evidência.

## Janela visível solicitada pelo dono

Build e QA continuam em sessões privadas e ocultas por padrão. Se o dono pedir
explicitamente para ver a ROM, pode-se abrir uma instância visível apenas para
essa inspeção manual: confira o caminho e SHA da ROM, indique se ela é candidata
ou aprovada e evite reutilizar/alterar a configuração pessoal do emulador.
Essa janela não substitui as sessões privadas, capturas ligadas à sessão/SHA,
nem os gates. “Abriu”, título/FPS exibido ou o dono validar o lançamento não
significa aprovação artística ou prova de gameplay.

1. Ler `doc/plano-sessoes-emulicious-isoladas.md`; conferir dependências locais.
   Sem Xvfb/ponte/sandbox, falhar com diagnóstico. Nenhum fallback ao desktop.
2. Iniciar com `emulator_session.py isolated start ROM.sms`. Guardar ID, SHA
   da ROM e caminho retornados. Configuração/SRAM ficam dentro da sessão.
3. Usar `emulator_input.py --session ID --script roteiro.json` ou a API
   `run_session_sequence`. O roteiro declara P1/P2, console e frames inteiros.
   Nunca converter um golpe em sleep ou fazer refoco entre partes do gesto.
4. Ler o probe/gravador da ROM para provar comandos e consequência. ACK da
   ponte e leitura da porta não provam o golpe nem que o oponente foi atingido.
5. Capturar com `capture_evidence.py --session` e `capture_video.py --session`.
   Vídeo por stepping prova quadros/ordem, não throughput em tempo real.
6. Para FPS, usar `measure_runtime_probe.py --session` e probe SMRT real. A
   reserva global serializa medições cooperativas; registrar a carga do host.
7. Publicar bundle exclusivo por sessão, verificar com
   `emulator_session.py isolated check-bundle DIRETORIO`. Consumers recebem ID
   e SHA explícitos; nunca buscam primeira janela ou última pasta por nome.
8. Fechar por `isolated close ID`, inclusive na saída de erro. Nunca usar
   pkill, kill por descoberta global ou capturar exclusivamente controle físico.
9. Áudio: boot com `-muted` obrigatório na ponte, stream primado com zeros e
   fluxo do PID exato movido e confirmado antes de liberar som. A linha fica
   aberta nas pausas: neste host, stop/start/flush recriam o stream e perdem a
   rota. Um keepalive mantém zeros durante mute/pausa; a linha aberta sozinha
   reprovou em repetição. Buffers do boot são descartados antes do unmute. `capture_audio.py
   --session` mede duração efetiva ≥95%, recusa mute/rota ausente ou divergente
   e pausa ao terminar. `session_bridge/audio_acceptance.py` testa mute de ROM
   sonora, rota estável, duração e controle silencioso em paralelo. Comparação
   musical exige trechos alinhados; sinal não comprova fidelidade.

`session_bridge/acceptance.py` é a prova de integração com duas ROMs. O
selftest cobre vínculos válidos, ROM trocada e captura preta. Fixtures offline
não substituem a prova em emulador nem sustentam gameplay/AAA.
