# skill: sms-video-evidence

Use para transição, animação, latência visual, KO ou golpe. Screenshot mede
estado estático, não duração ou consequência (§36/L054). Leia os workflows
centrais `emulator-isolated-session.md` e `subagent-emulator-qa.md` antes do QA.

## Sessão, input e captura (§§93–100)

- Inicie sessão própria com `emulator_session.py isolated start ROM.sms`;
  mantenha ID/SHA explícitos. Display/config/SRAM/controles são privados.
- `emulator_input.py --session ID --script roteiro.json` usa frames VDP e
  masks P1/P2/console. Nunca buscar janela/foco nem usar teclado do host.
- Para vídeo durante os comandos, use caso `proof: video` com `sequence` em
  `session_qa.py`: ele captura cada quadro enquanto o input atribuído está
  ativo. Declare cauda neutra para recuperação. `input` seguido de gravação
  após liberar o gesto perde a ação e não sustenta sua hipótese.
- Para animação sem gesto simultâneo:

```sh
rtk proxy python3 tools/sms_wrapper/capture_video.py \
  --session ID --ticks 120 --out video_idle
```

A saída pertence à sessão; consulte o path/metadata retornados. É framebuffer
256×192, sem compositor, um quadro por frame VDP. `--press` em milissegundos
não é compatível com a rota privada. Stepping prova ordem/quadros, não FPS
real nem áudio. FPS exige execução contínua/probe; áudio tem captura separada.

## O que medir

| Dado | Alcance |
|---|---|
| Dimensão, hashes, SHA/sessão | Canvas e vínculo desta captura; não qualidade |
| Cobertura da timeline | Quadros previstos, inclusive transição e recuperação |
| `motion_timeline.motion_fraction` | Pico de variação luma ao longo de toda a sequência |
| `endpoint_fraction` | Diferença dos extremos; extremos iguais podem formar ciclo válido |
| Probe/trilha de estado | Identidade do ator, ação, facing, contato/dano com schema revisado |

O gate da rota histórica `capture_video.py` exige ≥60 frames, ≥1s, conteúdo
informativo e movimento ≥1% na timeline. Esses limiares não são um contrato
universal de combate nem o mínimo de cada caso privado. Caso privado mede
cobertura/identidade; o worker revê a hipótese atribuída. Variação de contador
ou HUD não comprova que o lutador executou a ação. Os caminhos de coleta têm
regras distintas: sucesso da gravação privada não é aprovação perceptiva.

Para AIR, IDs fonte/ROM por N+1 fronteiras (terminal incluso) e duração finita
seguem §100. RGB idêntico não funde elementos. Amostra DAP isolada pode perder
frames curtos; não fabricar índice/stamp ausente. Vídeo e trace se complementam.

## Selar, revisar, encerrar

`session_qa.py` captura baseline, executa precondição ROM quando declarada,
sela bundle e encerra a sessão própria em finally. Draft começa needs_review.
Worker nativo inspeciona quadros/dados e registra cobertura; coordenador
valida `audit_subagent_session.py`, IDs nativos, frescor e teto do claim.
Na coleta direta, publique/check-bundle e feche com `isolated close ID`, também
na falha. Nunca encerrar processos por nome ou manipular sessões alheias.

## Legado e áudio

A rota histórica de atalhos F7/F8 e `.ini` compartilhado é supersedida para QA
automatizada. Suas falhas documentadas continuam históricas: atalho ausente,
F10 ativando menu Swing e MP4 movido antes de finalizar o atom moov. Não mexer
no ini compartilhado nem limpar instâncias para tornar esse caminho viável.

Vídeo privado não anexa áudio; `capture_audio.py --session ID` prova sinal
isolado do PID. No legado, `attach_audio()` corrige o tamanho RIFF declarado
maior que o payload real e mantém contagem de frames; silêncio não vira sinal.
Nenhum desses caminhos prova música certa: ouvir/comparar trechos alinhados.
Vídeo de arte/concept não é framebuffer de ROM, mesmo que tenha movimento.
