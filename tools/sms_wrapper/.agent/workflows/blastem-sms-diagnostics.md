# workflow: blastem-sms-diagnostics

## Escolha do emulador

| Necessidade | Rota |
|---|---|
| Produção diária, input exato da ponte, vídeo em frames VDP, áudio isolado, QA `session_qa.py`, probe SMRT, throughput e worst-frame | Emulicious privado: `emulator-isolated-session.md` e `subagent-emulator-qa.md` |
| Segunda implementação para investigar divergência Z80, RAM, mapper, padrões/atributos VDP, CRAM ou estado PSG | BlastEm SMS privado via `blastem_sms.py`; aprovação de consistência via `audit_blastem_sms.py` |
| APNG/WAVE/VGM nativos para uma hipótese visual/sonora | BlastEm diagnóstico: `diagnostics.record_av` / `vgm`; medir conteúdo/duração, sem aprovar FPS ou fidelidade musical |
| PAL, áudio final ou gameplay de entrega no BlastEm | Rota não qualificada; use Emulicious para esses eixos |
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

## Recursos avançados e momento de uso — §110

| Sintoma / objetivo | Recurso e prova necessária |
|---|---|
| Quem mudou um byte de life, FSM, cache ou canário? | `cpu_watches`: escrita que muda RAM, com endereço do mapa atual; observar evento e estado antes/depois. Testar também o caminho de instrução usado pela ROM. |
| Qual rotina está enviando dados/endereços ao VDP? | `vdp_io_breakpoints`: PC de `OUT` na ROM congelada, opcode esperado e porta BE/BF; log antes de OUT, estado VDP interno e dumps posteriores. |
| Tile errado, paleta trocada, flip ou mapa corrompido? | Dumps + `palette_sms.png`, `tiles_palette_0/1.png`, `name_table_unscrolled.png`; conferir com captura nativa do jogo. |
| O que mudou entre duas fronteiras? | `blastem_dump_diff.py`: RAM/VRAM/CRAM/regs/PSG e faixas nomeadas vinculadas à ROM; delta líquido não mede escrita/transferência nem causa. |
| Flicker/omissão/transição transitória? | APNG multiquadro durante o roteiro; verificar cada quadro, cobertura e SHA. Tempo de contêiner não é throughput. Para gate do jogo, vídeo Emulicious e `audit_render_glitch.py`. |
| SFX ausente ou mudança PSG indevida? | WAVE sinal/duração + VGM de registradores, mesma ROM/trecho. Para música certa, comparar referência alinhada na rota de áudio Emulicious. |
| Custo CPU/VBlank, fluidez real ou PAL? | Emulicious com probes/tempo real e ferramentas correspondentes; não usar stepping BlastEm para fechar budget. |
| Nova release ou suspeita de instalação alterada? | `blastem_maintenance.py`: consultar, instalar candidato em paralelo e verificar; qualificação explícita antes de mudar pin. |

Acrescentar ao roteiro apenas o necessário:

```json
"diagnostics": {
  "cpu_watches": [{"address": 51192, "size": 1}],
  "vdp_io_breakpoints": [
    {"pc": 11, "opcode_hex": "ed69"},
    {"pc": 25, "opcode_hex": "d3be"}
  ],
  "record_av": true,
  "vgm": true
}
```

Esses endereços são **da fixture SMI1**, não receitas de jogos. CPU watches
aceitam RAM C000–DFFF e tamanho 1/2; endereços/PCs vêm do mapa e da disassembly
da SHA atual. Sites OUT ficam em 0000–03FE, com dois bytes dentro do primeiro KiB.
No mapper Sega, 0400–3FFF já pode ser paginado. Cada hit também confere os
dois bytes vivos: mudança de opcode reprova a sessão. Isso protege outras
configurações/mapper, sem provar identidade da rotina se o opcode coincidir.
`OUT (C),r` é condicionado a C=BE/BF; o registrador de saída é lido conforme
opcode. Não cobre outros aliases de porta, bancos paginados, OUTI/OTIR nem
escritas que não passem pelo site escolhido. Máximo oito sites por tipo, prazo
limitado e log de até 16MiB; reduzir o escopo se houver excesso.

O debugger roda listas `commands` com contador, log e `continue`; enviar o
bloco completo, terminando em `end`, antes do ACK. Native watchpoint Z80
instrumenta WRITE_8 e pode ignorar escrita de valor inalterado: não mede toda
operação de bus nem leitura/I/O. Verificar sua eficácia no caminho real.
`observed_pc` é `context->pc`, que ficou stale nos traps observados; o site
de breakpoint declarado está em `event_definitions.address`. Não atribuir
writer pelo `observed_pc` sozinho. O valor RAM no trap não substitui prova de
commit; snapshots posteriores e probe completam a cadeia causal.

Os campos `vdp_internal_vcounter`, `vdp_internal_hslot`, `address` e `cd` são
estado interno observado. `hcounter` do debugger é **hslot**, não leitura do
contador H de hardware; sem sincronização adicional com CPU, não aprovam
instante de bus ou violação de VBlank. `vdpregbreak` pertence ao contexto
Genesis/M68K: o wrapper SMS usa breakpoints CPU de OUT, sem chamar isso de
watchpoint nativo de VRAM/registrador VDP.

### GDB: separar CPU, protocolo e versão

Na fonte 1.0.0 `gdb_remote.c` implementa Z2/z2 de escrita via
`m68k_add_watchpoint`/`m68k_remove_watchpoint`; o README ainda diz que
watchpoints não são suportados. Z3/Z4 (leitura/acesso) retornam vazio.
O teste MD informado pelo usuário confirma ganho naquele contexto; não foi
repetido como teste SMS. `sms.c` não integra esse stub Z80. Não afirmar
"GDB sem watchpoints" universalmente, nem oferecer GDB 68000/ELF SGDK para
SDCC Z80. SMS nesta integração usa debugger **nativo**, identificado nos
metadados; compatibilidade de protocolo exige sua própria prova.

### APNG, WAVE, VGM e visores

`record_av` aciona `ui.record_video` depois do baseline e encerra antes do
frame extra de screenshot. Produz `media/native.apng` e `native.wav`.
No pin 1.0.0, `png.c:end_apng` atualiza a contagem acTL sem refazer seu CRC.
`blastem_diagnostics.py` preserva o bruto e gera `decoded.apng`, corrigindo
somente esse CRC quando o checksum antigo corresponde ao payload de zero
frames; qualquer outra corrupção reprova. Contagem de fcTL precisa coincidir
com acTL; auditor exige tantos quadros quanto frames ativos do roteiro.
Registrar a derivação e usar o derivado para leitura em viewers estritos.

APNG usa cadência nominal de 60 Hz. WAVE é mix nativo 16-bit estéreo,
assíncrono, gravado diretamente em arquivo com SDL dummy: nenhum sink do host
é capturado. Medir sample frames, duração e pico; silêncio não reprova quando
esperado. Duração WAVE e APNG podem diferir por buffers e por pausas no
debugger; não afirmar alinhamento exato ou fidelidade musical pelo pico.
`vgm` grava comandos PSG, não áudio audível. Avaliar duração/trecho por caso.

Os visores derivados são diagnóstico, não screenshot nem assets de jogo:
VRAM do getter debugger já usa endereços SMS lógicos (não reembaralhar);
CRAM é invertida pelo encoding SMS da fonte fixada, com teste dos 64 códigos.
RGB 0/85/170/255 é referência digital, não modelo de DAC. Name table 256×224
não aplica scroll/sprites/raster/backdrop; paletas de tile mostram ambas as
seleções. O console continua renderizando 256×192 no perfil homologado.
Visores nativos de plano/sprites, VRAM, CRAM e composição têm implementação
Mode4 no source; seleção de modos pode depender da janela auxiliar ativa.
Captura automatizada dessas janelas ainda não foi qualificada. Usar os dumps
e visores derivados quando precisar de evidência reproduzível sem foco.

### Manutenção reproduzível

Para comparar o baseline `000` e o snapshot `001`, sem alterar o pacote:

```bash
rtk proxy python3 tools/sms_wrapper/blastem_dump_diff.py \
  --session /caminho/blastem-sms-ID --first 0 --last 1 \
  --current-rom /caminho/rom.sms --json /caminho/fora-da-sessao/diff.json
```

O diff audita o pacote e exige ferramentas de aquisição atuais; `--historical`
declara auditoria histórica sem elegibilidade atual. Índices precisam ser
ordenados e existir na timeline. A saída inclui hashes dos dumps e manifesto,
mudanças contíguas, offsets e contagem de blocos VRAM de32bytes que mudaram.
Blocos incluem SAT/name table/dados; não são tiles únicos gráficos ou bytes
transferidos. Escrita/alteração/restauração dentro da janela pode ter delta
zero. Comparação é estado final, não custo, causa ou ausência de atividade.

`--labels` aceita `sms_blastem_memory_labels_v1` com `rom_sha256` e `ranges`,
cada entrada `{name,space:ram|vram,address,length}`. Endereços são absolutos
RAM C000–DFFF ou VRAM0000–3FFF. Nomes são faixas declaradas pelo chamador,
vinculadas à SHA; não se apresentam como símbolos SDCC autenticados. Sobreposição
é permitida e as contagens não se somam. Labels stale ou fora do espaço
reprovam. O arquivo de diff fica fora da sessão imutável; destinos symlink/hardlink e
overwrites dos inputs são recusados. A gravação usa arquivo novo e substituição
atômica, preservando os inodes dos dumps.

```bash
rtk proxy python3 tools/sms_wrapper/blastem_maintenance.py releases
rtk proxy python3 tools/sms_wrapper/blastem_maintenance.py status
rtk proxy python3 tools/sms_wrapper/blastem_maintenance.py install-candidate --manifest /caminho/pin.json
rtk proxy python3 tools/sms_wrapper/blastem_maintenance.py verify --installation /caminho/candidato
```

Manifest contém `version`, URL oficial Linux64, `archive_sha256` e
`binary_sha256` explícitos. A consulta não aprende hashes nem troca o pin.
Candidatos ficam em `out/host_tools/blastem/candidates/<versão>-<hash>/`, com
arquivo, licenças, arquivos/hashes e links internos conferidos; divergência
aborta. Hash esperado tem origem declarada pelo curador, não é assinatura
upstream. Instalação em paralelo não é qualificação nem muda o executável
usado pelo wrapper; nova versão exige repetir os casos e revisar limites.

Fontes: [distribuição oficial](https://www.retrodev.com/blastem/downloads.html),
[fonte 1.0.0](https://www.retrodev.com/repos/blastem/archive/2b2a182f4522.tar.gz)
(`sms.c`, `debug.c`, `paths.c`, `bindings.c`, `io.c`, `render_sdl.c`).
