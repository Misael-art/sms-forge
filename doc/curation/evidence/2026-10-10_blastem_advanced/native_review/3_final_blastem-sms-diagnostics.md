# workflow: blastem-sms-diagnostics

## Escolha do emulador

| Necessidade | Rota |
|---|---|
| Produção diária, input exato da ponte, vídeo em frames VDP, áudio isolado, QA `session_qa.py`, probe SMRT, throughput e worst-frame | Emulicious privado: `emulator-isolated-session.md` e `subagent-emulator-qa.md` |
| Segunda implementação para investigar divergência Z80, RAM, mapper, padrões/atributos VDP, CRAM ou estado PSG | BlastEm SMS privado via `blastem_sms.py`; aprovação de consistência via `audit_blastem_sms.py` |
| PAL, gravação de áudio ou gameplay de entrega no BlastEm | Rota não qualificada; use Emulicious para esses eixos |
| Causa atribuída exclusivamente a um emulador | Reproduza a mesma ROM e precondição nos dois; divergência abre investigação, não decide automaticamente qual está certo |

Emulicious permanece o gate principal. BlastEm não é substituto automático nem
gate obrigatório em cada build. Use-o quando uma segunda implementação puder
resolver uma hipótese concreta, após alterar código de VDP/mapper/timing ou ao
investigar comportamento específico do emulador. Registrar o caso e sua SHA.
Concordância entre dois emuladores aumenta evidência; hardware real exige teste
próprio. Não extrapolar esta fixture para compatibilidade de todos os jogos.

## Ambiente e execução

Esta integração usa o pacote **oficial Linux x86_64 BlastEm 1.0.0**, com arquivo
e executável fixados por SHA-256. Não instala/atualiza Flatpak, não depende do
workspace SGDK e conserva os arquivos de licença/distribuição. Instale uma vez:

```bash
rtk proxy python3 tools/sms_wrapper/blastem_sms.py install
rtk proxy python3 tools/sms_wrapper/blastem_sms.py status
rtk proxy python3 tools/sms_wrapper/blastem_sms.py --self-check
rtk proxy python3 tools/sms_wrapper/audit_blastem_sms.py --self-check
```

`run` é limitado e síncrono; cada chamada cria ID, Xvfb com cookie, configuração,
ROM `.sms`, SRAM, PTY e sandbox próprios, e encerra os processos no `finally`.
Falta de isolamento aborta. Input é `binddown`/`bindup` no debugger nativo;
não passa pelo teclado do host, foco ou joystick físico. `/dev/input`,
`/dev/uinput` e `/dev/snd` ficam ocultos. Áudio SDL `dummy` desde o boot.
Não usar `-n`: no BlastEm significa desabilitar Z80. Não usar `-D` como se o
debugger GDB 68000/ELF SGDK fosse um debugger Z80/SDCC homologado.

Roteiro JSON: `schema: sms_blastem_sequence_v1`, `model: sms1|sms2`, `region:
ntsc`, `warmup_frames` de 1–600, `steps` com `frames` positivos e máscaras
P1/P2 (up/down/left/right/1/2 = 1/2/4/8/16/32), `pause: true` para um evento
da tecla Pause da unidade. Botões SMS **1/2 usam nomes BlastEm B/C**, não A/B.
O próprio `help` tem erro de grafia na descrição; o comando é `binddown`.
Não adicionar comandos debugger brutos ao roteiro.

```json
{
  "schema": "sms_blastem_sequence_v1",
  "model": "sms2",
  "region": "ntsc",
  "warmup_frames": 120,
  "preconditions": [{"address": 50944, "equals_hex": "534d493101"}],
  "steps": [
    {"frames": 7, "p1": 8},
    {"frames": 3},
    {"frames": 9, "p2": 16},
    {"frames": 3}
  ]
}
```

O endereço `50944` (`0xC700`) e a magic SMI1 são **exclusivos da fixture**;
substituir pelo contrato real da ROM. Baseline e todos os dumps são verificados
antes de aplicar input. Predicados ausentes não provam aplicabilidade de caso.
Para uso em projeto, carregue memory/GDD/spec/TDD legíveis antes de montar o
caso; erro EIO/EACCES não vira contexto diagnóstico inventado para o jogo.

```bash
rtk proxy python3 tools/sms_wrapper/blastem_sms.py run \
  --rom /caminho/absoluto/rom.sms --script /caminho/absoluto/roteiro.json \
  --output /caminho/absoluto/evidencias
rtk proxy python3 tools/sms_wrapper/audit_blastem_sms.py \
  --session /caminho/absoluto/evidencias/blastem-sms-ID \
  --current-rom /caminho/absoluto/rom.sms --require-current-tool
```

## Ler telemetria corretamente

- Snapshots: RAM Z80 `0xC000..0xDFFF` (8192 bytes), VRAM Mode4 (16384),
  registradores VDP 0–10, CRAM **interna** e frequência/volume PSG, mais PC/SP,
  AF/BC/DE/HL/IX/IY/IFF1 e contador de ciclos interno do emulador.
- `frame` do debugger é VDP. O contador da ROM é outro relógio. O debugger pode
  parar entre instruções que incrementam frame e held counters; comparar
  estados/precondições da ROM, não exigir igualdade dos PCs ou do boot frame
  entre emuladores. Na fixture, uma cauda neutra permite completar a iteração;
  no jogo use marcador/gravador atômico documentado. Não ajustar gesto para
  esconder falha ou trocar consumo observado por ACK da ponte.
- Ciclos internos são rebaseados pelo emulador. Não dividir seu delta pelo
  tempo do host para declarar FPS, budget CPU ou duração exclusiva de etapa.
- `cram_internal.bin` contém words little-endian da representação interna do
  BlastEm. `0x00EE` representa branco nesta implementação, não um código CRAM
  SMS de 6 bits. Traduzir segundo a fonte fixada antes de comparar códigos;
  comparação visual deve usar paleta SMS real e respeitar P1 compartilhada.
- A saída textual genérica do VDP pode listar campos de Mega Drive/DMA.
  Interprete os **11 registradores SMS brutos** conforme hardware SMS; nenhuma
  capacidade DMA, planos MD ou limite de sprites MD é ensinada por esse texto.
- Screenshot nativo OpenGL por software, overscan NTSC27/24/13/14 calibrado em
  256×192. A captura via SDL observada perdeu linhas; fallback é recusado.
  Screenshot ocorre **um frame depois** do último snapshot, com input solto.
  Não usá-la como imagem do exato estado transitório do snapshot anterior.
- Run concluído significa aquisição de estados. Captura uniforme é registrada
  como não informativa e não prova boot visual. Não prova música/FPS/AAA.

## Review nativo

Workers independentes executam `run` próprios e leem imagens/dumps reais.
Feedback inclui ID nativo, sessão/SHA, versão da ferramenta, cobertura,
observados, falhas preservadas e cleanup. O coordenador coteja IDs de verdade.
O coletor `session_qa.py` permanece qualificado para Emulicious; não fabricar
registro Emulicious ou parecer compatível com esse coletor para BlastEm.
Esta integração possui auditor de bundle próprio, não promoção automática
dos sete eixos do game. Hash histórico válido não paga build/ferramenta atual.

Fontes: [distribuição oficial](https://www.retrodev.com/blastem/downloads.html),
[fonte 1.0.0](https://www.retrodev.com/repos/blastem/archive/2b2a182f4522.tar.gz)
(`sms.c`, `debug.c`, `paths.c`, `bindings.c`, `io.c`, `render_sdl.c`).
